import tkinter as tk
from tkinter import scrolledtext
import threading
import cv2
import base64
import time
from flask import Flask
import socketio
import sounddevice as sd
import numpy as np
from scipy.io.wavfile import write
from google.cloud import speech
import openai
from PIL import Image, ImageTk
import os
import settings

# OpenAI APIキーとGoogle Cloud認証ファイルパス
openai.api_key = settings.AP
json_file_path = settings.G_AP
os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = json_file_path

# FlaskアプリとSocket.IOサーバー設定
sio = socketio.Server()
app = Flask(__name__)
app.wsgi_app = socketio.WSGIApp(sio, app.wsgi_app)

# Google Speech-to-Text設定
speech_client = speech.SpeechClient()
language_code = "ja-JP"

# 音声録音設定
sample_rate = 16000
recording = False
audio_data = []
recognized_text = ""
audio_filename = "recorded_audio.wav"
captured_image_filename = "captured_image.jpg"

# GUI設定
root = tk.Tk()
root.title("サーバー側：音声・画像認識")
root.geometry("800x600")

button_font = ("Arial", 14)
label_font = ("Arial", 14)

# メッセージ表示用のラベル
message_label = tk.Label(root, text="サーバーが起動しました", font=label_font)
message_label.pack(pady=10)

# 写真表示用のラベル
image_label = tk.Label(root)
image_label.pack(pady=10)

# 発話履歴の表示
history_text = scrolledtext.ScrolledText(root, wrap=tk.WORD, width=50, height=10, state='disabled', font=label_font)
history_text.pack(pady=10)

# 一定間隔で写真を撮影してクライアントに送信する関数
def send_image_to_client():
    cap = cv2.VideoCapture(0)
    capture_interval = 5  # 写真の送信間隔（秒）
    while True:
        ret, frame = cap.read()
        if ret:
            # 写真を保存
            cv2.imwrite(captured_image_filename, frame)
            # フレームをJPEGにエンコードしてBase64に変換
            _, buffer = cv2.imencode('.jpg', frame)
            image_data = base64.b64encode(buffer).decode('utf-8')
            # クライアントに写真を送信
            sio.emit('send_image', {'image': image_data})
            update_message("写真をクライアントに送信しました")
            display_image(frame)  # GUIに表示
        time.sleep(capture_interval)

# クライアントが接続したときの処理
@sio.event
def connect(sid, environ):
    update_message("クライアントが接続しました")

# 画像をTkinter GUIに表示
def display_image(cv2_image):
    cv2image = cv2.cvtColor(cv2_image, cv2.COLOR_BGR2RGB)
    img = Image.fromarray(cv2image).resize((400, 300))
    imgtk = ImageTk.PhotoImage(image=img)
    image_label.imgtk = imgtk
    image_label.config(image=imgtk)

# メッセージを履歴とメッセージラベルに追加
def add_to_history(text):
    history_text.configure(state='normal')
    history_text.insert(tk.END, text + "\n\n")
    history_text.configure(state='disabled')
    history_text.yview(tk.END)

def update_message(new_message):
    message_label.config(text=new_message)
    add_to_history(new_message)

# 音声録音開始
def start_recording():
    global recording, audio_data
    if not recording:
        recording = True
        audio_data = []
        update_message("発話が終了したら録音停止ボタンを押してください")
        threading.Thread(target=record_audio).start()

# 音声録音停止
def stop_recording():
    global recording
    if recording:
        recording = False
        update_message("録音開始ボタンを押してください")

# 音声録音処理
def record_audio():
    global audio_data
    while recording:
        chunk = sd.rec(int(0.5 * sample_rate), samplerate=sample_rate, channels=1, dtype='int16')
        sd.wait()
        audio_data.append(chunk)

    if audio_data:
        complete_audio = np.concatenate(audio_data, axis=0)
        write(audio_filename, sample_rate, complete_audio)
        transcribe_audio(audio_filename)

# 音声テキスト変換
def transcribe_audio(filename):
    global recognized_text
    with open(filename, "rb") as audio_file:
        audio_content = audio_file.read()
        audio = speech.RecognitionAudio(content=audio_content)
        config = speech.RecognitionConfig(
            encoding=speech.RecognitionConfig.AudioEncoding.LINEAR16,
            sample_rate_hertz=sample_rate,
            language_code=language_code
        )
        response = speech_client.recognize(config=config, audio=audio)
        recognized_text = "".join(result.alternatives[0].transcript for result in response.results)
        add_to_history("ユーザー: " + recognized_text)
        send_to_gpt_with_image_and_text()

# GPT-4に画像とテキストを送信
def send_to_gpt_with_image_and_text():
    with open(captured_image_filename, "rb") as image_file:
        base64_image = base64.b64encode(image_file.read()).decode("utf-8")
    try:
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
                        {"type": "text", "text": f"録音された会話の内容: {recognized_text}\n \
                         この会話内容から現在の会話を予測して、画像を考慮しながら会話の流れに沿った質問をしてください。\
                         質問は、画像を見た高齢者にすることを想定しているので、高齢者に対する質問を1つ生成してください。\
                         返答は、そのまま読み上げてもらうことを想定しているので、「GPTからの応答」など、質問以外の文字は含めず、質問文のみ返答してください。"},
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
        gpt_response = response.choices[0].message.content
        add_to_history("GPT-4の返答: " + gpt_response)
    except Exception as e:
        print("APIリクエストに失敗しました:", e)
        add_to_history("APIリクエストに失敗しました。")

# Flaskサーバーの別スレッドで起動
def start_flask_server():
    app.run(host='0.0.0.0', port=5000, debug=True)

# 写真送信を別スレッドで開始
threading.Thread(target=send_image_to_client).start()

# 録音開始・停止ボタンの設定
start_button = tk.Button(root, text="録音開始", command=start_recording, font=button_font)
start_button.pack(pady=10)

stop_button = tk.Button(root, text="録音停止", command=stop_recording, font=button_font)
stop_button.pack(pady=10)

# Flaskサーバーを別スレッドで起動
threading.Thread(target=start_flask_server).start()

# Tkinterメインループ開始
root.mainloop()
