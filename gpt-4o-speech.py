import openai
import base64
import cv2
import os
import threading
import time
import tkinter as tk
from google.cloud import speech
import sounddevice as sd
import numpy as np
from six.moves import queue
from tkinter import messagebox
import settings

openai.api_key = settings.AP

# JSONファイルのパスを指定（ユーザーの環境に合わせてパスを設定してください）
json_file_path = settings.GP

# 環境変数を設定
os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = json_file_path

RATE = 16000
CHUNK = int(RATE / 10)  # 100msに設定
recording = threading.Event()
transcript_list = []  # 音声認識結果を保持するリスト
capture_interval = 5  # サンプリング間隔（秒）
speech_thread = None  # 音声認識用のスレッド

class MicrophoneStream(object):
    def __init__(self, rate, chunk):
        self._rate = rate
        self._chunk = chunk
        self.closed = True

    def __enter__(self):
        self.closed = False
        return self

    def __exit__(self, type, value, traceback):
        self.closed = True

    def generator(self):
        # sounddeviceでマイク入力を取得し、chunkごとにデータを生成
        with sd.InputStream(samplerate=self._rate, channels=1, dtype='int16') as stream:
            while not self.closed and recording.is_set():
                audio_chunk, _ = stream.read(self._chunk)
                yield audio_chunk.tobytes()

def save_frame(frame, filename="captured_image.png"):
    current_dir = os.path.dirname(os.path.abspath(__file__))
    save_path = os.path.join(current_dir, filename)
    cv2.imwrite(save_path, frame)
    print(f"画像が保存されました: {save_path}")
    return save_path

def encode_image(image_path):
    with open(image_path, "rb") as image_file:
        return base64.b64encode(image_file.read()).decode('utf-8')

def recognize_speech():
    global transcript_list
    transcript_list = []  # 録音が開始されたらリストをクリア
    client = speech.SpeechClient()
    config = speech.RecognitionConfig(
        encoding=speech.RecognitionConfig.AudioEncoding.LINEAR16,
        sample_rate_hertz=RATE,
        language_code="ja-JP",
        enable_automatic_punctuation=True,
    )
    streaming_config = speech.StreamingRecognitionConfig(
        config=config,
        interim_results=True,
    )

    with MicrophoneStream(RATE, CHUNK) as stream:
        audio_generator = stream.generator()
        requests = (speech.StreamingRecognizeRequest(audio_content=content) for content in audio_generator)

        try:
            responses = client.streaming_recognize(streaming_config, requests)
            listen_print_loop(responses)
        except Exception as e:
            if recording.is_set():
                print(f"エラーが発生しました: {e}")

def listen_print_loop(responses):
    global transcript_list
    for response in responses:
        if not response.results:
            continue
        result = response.results[0]
        if not result.alternatives:
            continue

        transcript = result.alternatives[0].transcript
        print(f"認識した音声: {transcript}")

        # 音声認識結果をリストに追加
        transcript_list.append(transcript)

        # 録音が停止されたらループを終了
        if not recording.is_set():
            break

def process_conversation():
    # 音声認識結果を結合して一つのテキストにする
    combined_transcript = " ".join(transcript_list)
    if not combined_transcript:
        print("録音データがありません")
        return

    image_path = "captured_image.png"  # 常に最新の画像を使用
    base64_image = encode_image(image_path)

    response = openai.ChatCompletion.create(
            model="gpt-4o",
            messages=[
            {
                "role": "system",
                "content": "あなたは明るい雰囲気の人です。話を盛り上げるように話します。"
            },
            {
                "role": "user",
                "content": [
                {"type": "text", "text": "録音された会話の内容: {combined_transcript}\n\
                 提供された画像について説明し、話を盛り上げるようなその画像の内容に関する質問をしてください。\
                 質問は、画像を見た若者と高齢者の二人にすることを想定しているので、それぞれに対する2つの質問を生成してください。"},
                {
                "type": "image_url",
                "image_url": {
                    "url": f"data:image/jpeg;base64,{base64_image}"
                }
                }
                ]
            }
            ],
            max_tokens=300
            )
    print(response.choices[0].message.content)

def start_recording():
    global speech_thread
    if recording.is_set():
        messagebox.showinfo("録音", "既に録音中です")
        return

    recording.set()
    speech_thread = threading.Thread(target=recognize_speech, daemon=True)
    speech_thread.start()

def stop_recording():
    if not recording.is_set():
        messagebox.showinfo("録音", "録音は開始されていません")
        return

    recording.clear()
    if speech_thread:
        speech_thread.join()  # スレッドが終了するのを待機
    print("録音停止")
    process_conversation()  # 録音が停止されたらAPIに送信

def display_video():
    cap = cv2.VideoCapture(0)
    if not cap.isOpened():
        messagebox.showerror("エラー", "カメラを開くことができませんでした")
        return

    last_capture_time = time.time()

    while True:
        ret, frame = cap.read()
        if not ret:
            print("フレームをキャプチャできませんでした")
            break

        cv2.imshow('Webカメラ映像', frame)

        # 一定周期でフレームをキャプチャして保存
        current_time = time.time()
        if current_time - last_capture_time >= capture_interval:
            save_frame(frame)
            last_capture_time = current_time

        # 'q'キーでカメラ映像を終了
        if cv2.waitKey(1) & 0xFF == ord('q'):
            break

    cap.release()
    cv2.destroyAllWindows()

def create_gui():
    root = tk.Tk()
    root.title("録音コントローラー")

    start_button = tk.Button(root, text="録音開始", command=start_recording, width=20)
    start_button.pack(pady=10)

    stop_button = tk.Button(root, text="録音停止", command=stop_recording, width=20)
    stop_button.pack(pady=10)

    video_thread = threading.Thread(target=display_video, daemon=True)
    video_thread.start()

    root.mainloop()

# GUIを表示
create_gui()
