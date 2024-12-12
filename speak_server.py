import sounddevice as sd
import numpy as np
import wave
import time
import requests
import os
from google.cloud import speech
import settings

# Google Cloud認証ファイルパス
os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = settings.GP

# 設定
SILENCE_THRESHOLD = 800  # 無音判定の閾値
SILENCE_DURATION = 3     # 無音の継続時間（秒）
RESTART_DELAY = 1        # 録音再開の遅延秒数
RATE = 44100             # サンプルレート
CHANNELS = 1             # チャンネル数
CLIENT_URL = "http://192.168.0.19:5000/receive_text"  # PC1のFlaskエンドポイント

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
    """PC1のFlaskエンドポイントに文字起こしデータを送信"""
    try:
        response = requests.post(CLIENT_URL, json={"text": text})
        print("PC1にテキストを送信しました:", response.status_code)
    except requests.exceptions.RequestException as e:
        print("PC1への送信に失敗しました:", e)

def continuous_transcription():
    """音声認識を継続的に行い、文字起こしデータをPC1に送信"""
    print("音声認識を開始します...")
    while True:
        # 一時的な音声データを保存するバッファ
        buffer = []

        # 録音を開始し、無音判定または一定時間経過で再度録音
        with sd.InputStream(samplerate=RATE, channels=CHANNELS, dtype='int16') as stream:
            silent_duration = 0
            start_time = time.time()
            recording_started = False

            while True:
                # 0.5秒間の音声データを取得
                data, _ = stream.read(int(RATE * 0.5))
                buffer.append(data)

                # データを平滑化して無音判定
                data_flat = data.flatten()
                smoothed_data = moving_average(data_flat)

                # 録音の開始判定
                if not recording_started and not is_silent(smoothed_data):
                    print("録音中...")
                    recording_started = True
                    start_time = time.time()

                # 録音中の無音判定
                if recording_started and is_silent(smoothed_data):
                    silent_duration += 0.5
                    if silent_duration >= SILENCE_DURATION:
                        print("無音が続いたため録音を停止します...")
                        break
                else:
                    silent_duration = 0  # 無音カウントのリセット

                # 一定の録音時間が経過した場合
                if time.time() - start_time > 15:  # 最大録音時間の例として15秒
                    print("録音時間が上限に達しました")
                    break

            # バッファ内の録音データを結合し、文字起こし
            data_bytes = np.concatenate(buffer).tobytes()
            transcribed_text = transcribe_audio(data_bytes)
            print("文字起こし結果:", transcribed_text)

            # PC1に文字起こしを送信
            send_text_to_client(transcribed_text)
            time.sleep(RESTART_DELAY)  # 録音再開の遅延

# 継続的に音声認識を実行
continuous_transcription()
