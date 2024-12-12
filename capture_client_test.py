import tkinter as tk
from tkinter import scrolledtext
import threading
import sounddevice as sd
import numpy as np
from scipy.io.wavfile import write
from google.cloud import speech
import openai
import socketio
import base64
import cv2
from PIL import Image, ImageTk
import os
import settings

# OpenAI APIキーとGoogle Cloud認証ファイルパス
openai.api_key = settings.AP
json_file_path = settings.GP
os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = json_file_path

# Socket.IOクライアント設定
sio = socketio.Client()

# Google Speech-to-Text設定
speech_client = speech.SpeechClient()
language_code = "ja-JP"

# 音声録音設定
sample_rate = 16000
recording = False
audio_data = []
recognized_text = ""
audio_filename = "recorded_audio.wav"
received_image_filename = "received_image.jpg"

# Tkinter GUI設定
root = tk.Tk()
root.title("クライアント側：音声・画像認識")
root.geometry("800x600")

button_font = ("Arial", 14)
label_font = ("Arial", 14)

message_label = tk.Label(root, text="サーバーに接続してください", font=label_font)
message_label.pack(pady=10)

# 写真表示用のラベル
image_label = tk.Label(root)
image_label.pack(pady=10)

history_text = scrolledtext.ScrolledText(root, wrap=tk.WORD, width=50, height=10, state='disabled', font=label_font)
history_text.pack(pady=10)

# サーバーから写真を受信したときの処理
@sio.on('send_image')
def handle_send_image(data):
    image_data = data['image']
    # 画像をデコードして保存
    image = decode_image(image_data)
    cv2.imwrite(received_image_filename, image)
    display_received_image(image)
    print("サーバーから写真を受信しました")

# 画像をデコードする関数
def decode_image(image_data):
    image_bytes = base64.b64decode(image_data)
    np_arr = np.frombuffer(image_bytes, np.uint8)
    return cv2.imdecode(np_arr, cv2.IMREAD_COLOR)

# 受信した画像をGUIに表示する関数
def display_received_image(cv2_image):
    cv2image = cv2.cvtColor(cv2_image, cv2.COLOR_BGR2RGB)
    img = Image.fromarray(cv2image).resize((400, 300))
    imgtk = ImageTk.PhotoImage(image=img)
    image_label.imgtk = imgtk
    image_label.config(image=imgtk)

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
    with open(received_image_filename, "rb") as image_file:
        base64_image = base64.b64encode(image_file.read()).decode("utf-8")
    try:
        response = openai.ChatCompletion.create(
            model="gpt-4-turbo",
            messages=[
                {
                    "role": "system",
                    "content": "あなたは明るい雰囲気の人です。話を盛り上げるように話します。"
                },
                {
                    "role": "user",
                    "content": [
                        {"type": "text", "text": f"録音された会話の内容: {recognized_text}\nこの会話内容から現在の会話を予測して、画像を考慮しながら会話の流れに沿った質問をしてください。\
                            質問は、画像を見た高齢者にすることを想定しているので、高齢者に対する質問を1つ生成してください。\
                                返答は、そのまま読み上げてもらうことを想定しているので、「GPTからの応答」など、質問以外の文字は含めず、質問文のみ返答してください。"},
                        {
                            "type": "image_url",
                            "image_url": {"url": f"data:image/jpeg;base64,{base64_image}"}
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

# 発話履歴に追加
def add_to_history(text):
    history_text.configure(state='normal')
    history_text.insert(tk.END, text + "\n\n")
    history_text.configure(state='disabled')
    history_text.yview(tk.END)

# メッセージ更新
def update_message(new_message):
    message_label.config(text=new_message)

# サーバーに接続
sio.connect('http://192.168.0.19:5000')  # server_pc_ipをサーバーPCのIPアドレスに置き換えてください
update_message("サーバーに接続しました")

# 録音開始・停止ボタンの設定
start_button = tk.Button(root, text="録音開始", command=start_recording, font=button_font)
start_button.pack(pady=10)

stop_button = tk.Button(root, text="録音停止", command=stop_recording, font=button_font)
stop_button.pack(pady=10)

# Tkinterメインループ開始
root.mainloop()
