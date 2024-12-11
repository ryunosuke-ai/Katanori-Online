from flask import Flask, request, jsonify
import sounddevice as sd
import numpy as np
import wave
import time
import base64
import openai
import cv2
import os
from google.cloud import speech
import socketio
import threading
import settings

app = Flask(__name__)

# 定数と設定
DURATION = 10  # 最大録音時間（秒）
SILENCE_THRESHOLD = 800  # 無音判定の閾値
SILENCE_DURATION = 3  # 無音が続いた場合の停止判定時間
RESTART_DELAY = 5  # 録音再開の遅延秒数
RATE = 44100
CHANNELS = 1
OUTPUT_FILENAME = "recorded_audio.wav"
capture_interval = 10  # 写真撮影の間隔（秒）
last_capture_time = time.time()
recognized_text = ""  # PC1の文字起こし結果
pc2_transcription = ""  # PC2からの文字起こし結果
photo_data = ""
latest_gpt_response = ""  # 最新のGPT応答
openai.api_key = settings.AP  # OpenAI APIキーを設定
PC3_SOCKET_URL = "http://192.168.1.67:5001"  # PC3のSocketIOサーバーURLを設定

# Google Speech-to-Textの設定
os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = settings.G_AP
speech_client = speech.SpeechClient()
language_code = "ja-JP"

# カメラの初期化
cap = cv2.VideoCapture(0)
if not cap.isOpened():
    print("カメラにアクセスできません")
    exit()

# Socket.IOクライアントの設定
sio = socketio.Client()
sio.connect(PC3_SOCKET_URL)  # PC3のSocketIOサーバーに接続

# 音声処理用のヘルパー関数
def moving_average(data, window_size=5):
    return np.convolve(data, np.ones(window_size) / window_size, mode='valid')

def is_silent(data, threshold=SILENCE_THRESHOLD):
    rms_value = np.sqrt(np.mean(np.square(data)))
    return rms_value < threshold

def record_audio():
    """PC1で音声を録音し、無音を検出して停止し、文字起こしを実行。これを繰り返す。"""
    global recognized_text
    while True:
        print("録音を開始します... 話してください")
        recording_started = False
        start_time = None

        # WAVファイルに録音データを保存
        with wave.open(OUTPUT_FILENAME, 'wb') as wf:
            wf.setnchannels(CHANNELS)
            wf.setsampwidth(2)
            wf.setframerate(RATE)

            with sd.InputStream(samplerate=RATE, channels=CHANNELS, dtype='int16') as stream:
                silent_duration = 0
                while True:
                    data = stream.read(int(RATE * 0.5))[0].flatten()
                    smoothed_data = moving_average(data)

                    # 話し始めを待つ
                    if not recording_started:
                        if not is_silent(smoothed_data):
                            print("録音中...")
                            recording_started = True
                            start_time = time.time()
                        else:
                            continue

                    # WAVファイルに録音データを書き込む
                    wf.writeframes(data.tobytes())

                    # 最大録音時間に達した場合、録音停止
                    if recording_started and (time.time() - start_time > DURATION):
                        print("録音時間が上限に達しました")
                        break

                    # 無音が続く場合、録音停止
                    if recording_started and is_silent(smoothed_data):
                        silent_duration += 0.5
                        if silent_duration >= SILENCE_DURATION:
                            print("無音が続いたため、録音を停止します...")
                            break
                    else:
                        silent_duration = 0

        # 音声をテキストに変換
        recognized_text = transcribe_audio(OUTPUT_FILENAME)
        print(f"PC1の文字起こし: {recognized_text}")

def transcribe_audio(filename):
    """録音ファイルをGoogle Speech-to-Textで文字起こし"""
    with open(filename, "rb") as audio_file:
        audio_content = audio_file.read()
        audio = speech.RecognitionAudio(content=audio_content)
        config = speech.RecognitionConfig(
            encoding=speech.RecognitionConfig.AudioEncoding.LINEAR16,
            sample_rate_hertz=RATE,
            language_code=language_code
        )
        response = speech_client.recognize(config=config, audio=audio)
        return " ".join(result.alternatives[0].transcript for result in response.results)

def capture_image():
    """一定間隔で画像をキャプチャし、Base64にエンコードして固定ファイル名で保存"""
    global photo_data, last_capture_time
    if time.time() - last_capture_time >= capture_interval:
        ret, frame = cap.read()
        if ret:
            # 固定ファイル名で画像を保存
            filename = "captured_image.jpg"
            cv2.imwrite(filename, frame)
            print(f"画像を保存しました: {filename}")

            # Base64にエンコード
            _, buffer = cv2.imencode('.jpg', frame)
            photo_data = base64.b64encode(buffer).decode("utf-8")
            print("画像をキャプチャし、エンコードしました")
            last_capture_time = time.time()


def generate_gpt_response():
    """GPT-4にPC1とPC2の文字起こしおよび画像データを送信し、応答を保存"""
    global latest_gpt_response
    try:
        response = openai.ChatCompletion.create(
            model="gpt-4o",
            messages=[
                {
                    "role": "system",
                    "content": "あなたは会話の内容を引き出すような質問をするプロの司会者です。\
                        若者には高齢者と楽しく会話できるような質問を、高齢者には昔の思い出などを思い出させるような質問をするように心がけてください。"
                },
                {
                    "role": "user",
                    "content": [
                        {"type": "text", "text": f"若者と高齢者が会話をしていて、現在の若者の発言は{recognized_text}で、高齢者の発言は{pc2_transcription}です。\n \
                         この発言内容から現在の会話を予測して、入力画像を考慮しながら会話の流れに沿った質問をしてください。\
                         質問は、若者と高齢者に対する質問を1つずつ生成し、必ず最初に高齢者に対する質問、次に若者に対する質問の順番で生成してください。\
                         高齢者に対する質問を生成する際には、「高齢者さん、○○（質問内容）」という風に、高齢者に対して質問していることが分かるように声掛けをし、\
                         同様に、若者に対して質問を生成するときも「若者さん、○○（質問内容）」という風に、若者に対して質問していることが分かるように声掛けをしてください。\
                         返答は、そのまま読み上げてもらうことを想定しているので、「GPTからの応答」など、質問以外の文字は含めず、質問文のみ返答してください。\
                         "},
                        {
                            "type": "image_url",
                            "image_url": {
                                "url": f"data:image/jpeg;base64,{photo_data}"
                            }
                        }
                    ]
                }
            ],
            max_tokens=300
        )
        latest_gpt_response = response.choices[0].message.content
        print("GPT-4からの応答:", latest_gpt_response)
    except Exception as e:
        print("GPT-4との通信エラー:", e)

def send_to_pc3_if_silent():
    """無音状態が続いた場合に最新のGPT応答をPC3に送信"""
    silent_duration = 0
    while True:
        # 音声を確認
        with sd.InputStream(samplerate=RATE, channels=CHANNELS, dtype='int16') as stream:
            data, _ = stream.read(int(RATE * 0.5))
            data_flat = data.flatten()
            smoothed_data = moving_average(data_flat)

            if is_silent(smoothed_data):
                silent_duration += 0.5
                if silent_duration >= SILENCE_DURATION:
                    # 無音状態が続いた場合にPC3にGPTの応答を送信
                    print("無音状態のため、PC3にGPT応答を送信します...")
                    sio.emit('text_to_speech', {'text': latest_gpt_response})
                    silent_duration = 0  # リセット
            else:
                silent_duration = 0  # 無音カウントのリセット

            time.sleep(RESTART_DELAY)

@app.route('/receive_text', methods=['POST'])
def receive_text():
    """PC2からの文字起こしデータを非同期で受信し、ログとして表示"""
    global pc2_transcription
    data = request.get_json()
    text = data.get("text", "")
    print("PC2からの文字起こしを受信:", text)
    pc2_transcription = text  # PC2のテキストを更新
    print(f"PC2の文字起こし: {pc2_transcription}")
    return jsonify({"status": "received"})

def continuous_gpt_generation():
    """定期的にGPTの応答を生成"""
    while True:
        capture_image()       # 画像をキャプチャ
        generate_gpt_response()  # GPT-4に送信して応答を生成
        time.sleep(5)  # 一定間隔で応答を生成

if __name__ == '__main__':
    # Flaskサーバーを非同期で開始
    threading.Thread(target=lambda: app.run(host='0.0.0.0', port=5000, threaded=True), daemon=True).start() #Threadで並列で実行する場合は、daemon=Trueを全てのスレッドにつける。
    # 音声認識、GPT応答生成、および無音判定を別スレッドで実行
    threading.Thread(target=record_audio, daemon=True).start()          # 音声認識のスレッド
    threading.Thread(target=continuous_gpt_generation, daemon=True).start()  # GPT応答生成のスレッド
    send_to_pc3_if_silent()  # 無音検出およびPC3への送信