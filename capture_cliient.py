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
capture_interval = 5  # 写真撮影の間隔（秒）
last_capture_time = time.time()
recognized_text = ""
photo_data = ""
openai.api_key = settings.AP  # OpenAI APIキーを設定

# Google Speech-to-Textの設定
os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = settings.G_AP  # Google Cloud認証情報のパス
speech_client = speech.SpeechClient()
language_code = "ja-JP"  # 日本語設定

# カメラの初期化
cap = cv2.VideoCapture(0)
if not cap.isOpened():
    print("カメラにアクセスできません")
    exit()

# 音声処理用のヘルパー関数
def moving_average(data, window_size=5):
    return np.convolve(data, np.ones(window_size) / window_size, mode='valid')

def is_silent(data, threshold=SILENCE_THRESHOLD):
    rms_value = np.sqrt(np.mean(np.square(data)))
    return rms_value < threshold

def record_audio():
    global recognized_text
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
                        print("無音が続いたため録音を停止します...")
                        break
                else:
                    silent_duration = 0

    # 音声をテキストに変換
    transcribe_audio(OUTPUT_FILENAME)

def transcribe_audio(filename):
    global recognized_text
    with open(filename, "rb") as audio_file:
        audio_content = audio_file.read()
        audio = speech.RecognitionAudio(content=audio_content)
        config = speech.RecognitionConfig(
            encoding=speech.RecognitionConfig.AudioEncoding.LINEAR16,
            sample_rate_hertz=RATE,
            language_code=language_code
        )
        response = speech_client.recognize(config=config, audio=audio)

        # 文字起こしの結果を保存
        recognized_text = "".join(result.alternatives[0].transcript for result in response.results)
        print("認識されたテキスト:", recognized_text)

def capture_image():
    global photo_data
    ret, frame = cap.read()
    if ret:
        _, buffer = cv2.imencode('.jpg', frame)
        photo_data = base64.b64encode(buffer).decode("utf-8")
        print("画像をキャプチャしました")

def send_to_gpt(text_data):
    try:
        # GPT-4に全データを送信し応答を取得
        response = openai.ChatCompletion.create(
            model="gpt-4o",
            messages=[
                {
                    "role": "system",
                    "content": "あなたは会話の内容を引き出すような質問をするプロの司会です。\
                        若者には高齢者と楽しく会話できるような質問を、高齢者には昔の思い出などを思い出させるような質問をするように心がけてください。"
                },
                {
                    "role": "user",
                    "content": [
                        {"type": "text", "text": f"若者と高齢者が会話をしていて、現在の若者の発言は{recognized_text}で、高齢者の発言は{text_data}です。\n \
                         この発言内容から現在の会話を予測して、画像を考慮しながら会話の流れに沿った質問をしてください。\
                         質問は、若者と高齢者に対する質問を1つずつ生成し、必ず最初に高齢者に対する質問、次に若者に対する質問の順番で生成してください。\
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
        gpt_response = response.choices[0].message.content
        print("GPT-4からの応答:", gpt_response)
        return gpt_response
    except Exception as e:
        print("GPT-4との通信エラー:", e)
        return "GPT-4との通信に失敗しました。"

@app.route('/receive_text', methods=['POST'])
def receive_text():
    data = request.get_json()
    text = data.get("text", "")
    print("サーバーから受信したテキスト:", text)

    # 録音（無音検知）
    record_audio()

    # 画像をキャプチャ
    global last_capture_time
    if time.time() - last_capture_time >= capture_interval:
        capture_image()
        last_capture_time = time.time()

    # 全入力をGPT-4に送信
    response_text = send_to_gpt(text)

    return jsonify({"status": "received", "gpt_response": response_text}), 200

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
