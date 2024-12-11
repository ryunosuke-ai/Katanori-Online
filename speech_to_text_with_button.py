import pyaudio
import wave
import os
import threading
from google.cloud import speech
import io
import tkinter as tk

# Google Cloudの認証ファイルへのパスを設定
os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = "\\Users\Ryunosuke\Desktop\my-project-test-436808-4ac407ed29b1.json"

# 録音設定
FORMAT = pyaudio.paInt16
CHANNELS = 1
RATE = 16000  # サンプルレート（Google Speech-to-Textのデフォルト）
CHUNK = 1024
WAVE_OUTPUT_FILENAME = "recorded.wav"

# グローバル変数
is_recording = False
audio = pyaudio.PyAudio()
stream = None

def start_recording():
    global is_recording, stream
    is_recording = True
    frames = []

    # 録音の開始
    stream = audio.open(format=FORMAT,
                        channels=CHANNELS,
                        rate=RATE,
                        input=True,
                        frames_per_buffer=CHUNK)

    print("録音中...")

    # 別スレッドで録音処理を実行
    def record():
        while is_recording:
            data = stream.read(CHUNK)
            frames.append(data)

        # 録音データをWAV形式で保存
        with wave.open(WAVE_OUTPUT_FILENAME, 'wb') as wf:
            wf.setnchannels(CHANNELS)
            wf.setsampwidth(audio.get_sample_size(FORMAT))
            wf.setframerate(RATE)
            wf.writeframes(b''.join(frames))

        print("録音終了")

    # 録音スレッドを開始
    threading.Thread(target=record).start()

def stop_recording():
    global is_recording, stream
    is_recording = False
    if stream is not None:
        stream.stop_stream()
        stream.close()

    # 文字起こしを実行
    transcribe_audio(WAVE_OUTPUT_FILENAME)

def transcribe_audio(file_path):
    client = speech.SpeechClient()

    with io.open(file_path, "rb") as audio_file:
        content = audio_file.read()

    audio = speech.RecognitionAudio(content=content)
    config = speech.RecognitionConfig(
        encoding=speech.RecognitionConfig.AudioEncoding.LINEAR16,
        sample_rate_hertz=16000,
        language_code="ja-JP"  # 日本語の場合
    )

    response = client.recognize(config=config, audio=audio)

    # 文字起こしの結果を出力
    for result in response.results:
        print("Transcript: {}".format(result.alternatives[0].transcript))

# GUIのセットアップ
root = tk.Tk()
root.title("音声認識アプリ")

start_button = tk.Button(root, text="録音開始", command=start_recording)
start_button.pack(pady=10)

stop_button = tk.Button(root, text="録音停止", command=stop_recording)
stop_button.pack(pady=10)

root.mainloop()

# 終了時にリソースを解放
audio.terminate()
