import sounddevice as sd
import numpy as np
import wave
import time
import requests
import os
from google.cloud import speech
import threading
import settings
from flask import Flask, request, jsonify

app = Flask(__name__)

silence_duration = 0  # 無音時間を管理するグローバル変数

@app.route('/reset_silence', methods=['POST'])
def reset_silence():
    """PC1からのリセットリクエストを受信し、無音時間をリセット"""
    global silence_duration
    silence_duration = 0
    print("PC1からのリクエストで無音時間をリセットしました")
    return jsonify({"status": "reset successful"})

# Google Cloud認証ファイルパス
os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = settings.GP
# 設定
SILENCE_THRESHOLD = 800  # 無音判定の閾値
SILENCE_DURATION = 3     # 無音の継続時間（秒）
RESTART_DELAY = 1        # 録音再開の遅延秒数
RATE = 44100             # サンプルレート
CHANNELS = 1             # チャンネル数
CLIENT_URL_TEXT = "http://192.168.1.125:5000/receive_text"  # PC1の文字起こしデータ送信先
CLIENT_URL_SILENCE = "http://192.168.1.125:5000/receive_silence"  # PC1の無音状態送信先

# Google Speech-to-Text クライアント
speech_client = speech.SpeechClient()

# 音声処理用のヘルパー関数
def moving_average(data, window_size=5):
    return np.convolve(data, np.ones(window_size) / window_size, mode='valid')

def is_silent(data, threshold=SILENCE_THRESHOLD):
    rms_value = np.sqrt(np.mean(np.square(data)))
    return rms_value < threshold

def transcribe_audio(data):
    """録音データをGoogle Speech-to-Textに送信し、文字起こし結果を返す"""
    audio = speech.RecognitionAudio(content=data)
    config = speech.RecognitionConfig(
        encoding=speech.RecognitionConfig.AudioEncoding.LINEAR16,
        sample_rate_hertz=RATE,
        language_code="ja-JP"
    )
    response = speech_client.recognize(config=config, audio=audio)
    return " ".join(result.alternatives[0].transcript for result in response.results)

def send_text_to_client(text):
    """PC1の文字起こしデータ送信エンドポイントに文字起こし結果を送信"""
    try:
        response = requests.post(CLIENT_URL_TEXT, json={"text": text})
        print("PC1にテキストを送信しました:", response.status_code)
    except requests.exceptions.RequestException as e:
        print("PC1への送信に失敗しました:", e)

def send_silence_status():
    """無音状態の継続時間を定期的にPC1に送信"""
    global silence_duration
    while True:
        with sd.InputStream(samplerate=RATE, channels=CHANNELS, dtype='int16') as stream:
            try:
                data, _ = stream.read(int(RATE * 0.5))
                data_flat = data.flatten()
                smoothed_data = moving_average(data_flat)

                # 無音状態を判定
                if is_silent(smoothed_data):
                    silence_duration += 0.5  # 無音の場合カウントを増やす
                else:
                    silence_duration = 0  # 音声がある場合リセット

                # PC1に無音状態を送信
                response = requests.post(CLIENT_URL_SILENCE, json={"silent_duration": silence_duration})
                print(f"PC1に無音状態を送信しました: {silence_duration}")
            except Exception as e:
                print("無音状態送信中にエラーが発生しました:", e)

            time.sleep(0.5)  # 送信間隔


def continuous_transcription():
    """音声認識を継続的に行い、文字起こしデータをPC1に送信"""
    while True:
        print("音声認識を開始します...話してください！")
        buffer = []
        recording_silence_duration = 0  # この関数専用の無音カウント
        recording_started = False

        with sd.InputStream(samplerate=RATE, channels=CHANNELS, dtype='int16') as stream:
            while True:
                try:
                    data, _ = stream.read(int(RATE * 0.5))
                    buffer.append(data)
                    data_flat = data.flatten()
                    smoothed_data = moving_average(data_flat)

                    # 録音の開始判定
                    if not recording_started and not is_silent(smoothed_data):
                        recording_started = True
                        print("録音中...")

                    # 録音中の無音判定
                    if recording_started and is_silent(smoothed_data):
                        recording_silence_duration += 0.5
                        if recording_silence_duration >= SILENCE_DURATION:
                            print("無音が続いたため録音を停止します...")
                            break
                    else:
                        recording_silence_duration = 0  # 無音カウントのリセット

                except Exception as e:
                    print("音声認識中にエラーが発生しました:", e)
                    break

            # バッファ内の録音データを結合し、文字起こし
            try:
                data_bytes = np.concatenate(buffer).tobytes()
                if recording_started:
                    transcribed_text = transcribe_audio(data_bytes)
                    print("文字起こし結果:", transcribed_text)
                    send_text_to_client(transcribed_text)
            except Exception as e:
                print("文字起こし中にエラーが発生しました:", e)

            print("次の音声認識を準備中...")
            time.sleep(RESTART_DELAY)

if __name__ == "__main__":
    # 無音状態送信スレッドを開始
    threading.Thread(target=send_silence_status, daemon=True).start()
    # Flaskサーバーを開始
    threading.Thread(target=lambda: app.run(host='0.0.0.0', port=5002, threaded=True), daemon=True).start()

    # 継続的に音声認識を実行
    continuous_transcription()
