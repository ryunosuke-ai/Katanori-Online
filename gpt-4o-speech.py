import tkinter as tk
from tkinter import scrolledtext
import threading
import sounddevice as sd
import numpy as np
from scipy.io.wavfile import write
from google.cloud import speech
import openai
import cv2
import base64
import os
from PIL import Image, ImageTk
import settings

openai.api_key = settings.AP

# JSONファイルのパスを指定（ユーザーの環境に合わせてパスを設定してください）
json_file_path = "\\Users\Ryunosuke\Desktop\my-project-test-436808-4ac407ed29b1.json"

# 環境変数を設定
os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = json_file_path

# Google Speech-to-Textクライアントの設定
speech_client = speech.SpeechClient()
language_code = "ja-JP"  # 日本語設定

# 録音設定
sample_rate = 16000
recording = False  # 録音状態の管理
audio_data = []    # 録音された音声データ
recognized_text = ""  # 認識されたテキスト

# 録音ファイル名
audio_filename = "recorded_audio.wav"

# PC内蔵カメラのデバイス番号
camera_device_number = 0  # 必要に応じて番号を変更
cap = cv2.VideoCapture(camera_device_number)

if not cap.isOpened():
    print("カメラにアクセスできません")
    exit()

# 録音を開始する関数
def start_recording():
    global recording, audio_data
    if not recording:
        print("録音を開始します...")
        recording = True
        audio_data = []
        update_message("発話が終了したら録音停止ボタンを押してください")
        threading.Thread(target=record_audio).start()  # 別スレッドで録音を開始

# 録音を停止する関数
def stop_recording():
    global recording
    if recording:
        print("録音を停止します...")
        recording = False
        update_message("録音開始ボタンを押してください")

# 録音処理を行う関数
def record_audio():
    global audio_data
    while recording:
        # 一定時間の音声を録音（0.5秒ごと）
        chunk = sd.rec(int(0.5 * sample_rate), samplerate=sample_rate, channels=1, dtype='int16')
        sd.wait()  # チャンクの録音が完了するまで待機
        audio_data.append(chunk)

    # 録音が停止したら音声をファイルに上書き保存し、テキスト変換を行う
    if audio_data:
        complete_audio = np.concatenate(audio_data, axis=0)
        write(audio_filename, sample_rate, complete_audio)  # 上書き保存
        print(f"録音された音声ファイルが保存されました: {audio_filename}")
        transcribe_audio(audio_filename)

# 音声ファイルをテキストに変換する関数
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
        
        # 認識結果を保存
        recognized_text = "".join(result.alternatives[0].transcript for result in response.results)
        print("認識されたテキスト:", recognized_text)
        add_to_history("ユーザー: " + recognized_text)

        # 音声認識が終わったら画像をキャプチャしてGPT-4へ送信
        capture_image_and_ask_gpt()

# 画像をキャプチャして表示し、GPT-4 APIに送信する関数
def capture_image_and_ask_gpt():
    ret, frame = cap.read()
    if not ret:
        print("画像のキャプチャに失敗しました")
        return

    # 画像をファイルに保存
    filename = "captured_image.png"
    cv2.imwrite(filename, frame)
    print(f"{filename} を保存しました")

    # 画像をBase64エンコード
    with open(filename, "rb") as image_file:
        base64_image = base64.b64encode(image_file.read()).decode("utf-8")

    # GPT-4 APIに送信
    send_to_gpt(base64_image, recognized_text)

# GPT-4 APIに画像とテキストを送信し、応答を取得する関数
def send_to_gpt(image_data, text_data):
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
                        {"type": "text", "text": f"録音された会話の内容: {text_data}\n \
                         この会話内容から現在の会話を予測して、画像を考慮しながら会話の流れに沿った質問をしてください。\
                         質問は、画像を見た高齢者にすることを想定しているので、高齢者に対する質問を1つ生成してください。\
                         返答は、そのまま読み上げてもらうことを想定しているので、「GPTからの応答」など、質問以外の文字は含めず、質問文のみ返答してください。"},
                        {
                            "type": "image_url",
                            "image_url": {
                                "url": f"data:image/jpeg;base64,{image_data}"
                            }
                        }
                    ]
                }
            ],
            max_tokens=300
        )
        gpt_response = response.choices[0].message.content
        print("GPT-4からの応答:", gpt_response)
        add_to_history("GPT-4の返答: " + gpt_response)

    except Exception as e:
        print("APIリクエストに失敗しました:", e)
        add_to_history("APIリクエストに失敗しました。")

# 映像をTkinterウィンドウに表示する関数
def show_video_feed():
    ret, frame = cap.read()
    if ret:
        # OpenCVからPILに変換し、サイズを縮小
        cv2image = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        img = Image.fromarray(cv2image).resize((400, 300))
        imgtk = ImageTk.PhotoImage(image=img)
        video_label.imgtk = imgtk
        video_label.config(image=imgtk)
    video_label.after(10, show_video_feed)

# 発話履歴に追加する関数
def add_to_history(text):
    history_text.configure(state='normal')
    history_text.insert(tk.END, text + "\n\n")
    history_text.configure(state='disabled')
    history_text.yview(tk.END)  # 自動スクロール

# メッセージラベルの内容を更新する関数
def update_message(new_message):
    message_label.config(text=new_message)

# GUIのセットアップ
root = tk.Tk()
root.title("音声・画像認識アプリ")
root.geometry("800x600")  # ウィンドウサイズを設定

# フォント設定
button_font = ("Arial", 14)
label_font = ("Arial", 14)

# 録音ガイドメッセージ
message_label = tk.Label(root, text="録音開始ボタンを押してください", font=label_font)
message_label.pack(pady=10)

start_button = tk.Button(root, text="録音開始", command=start_recording, font=button_font)
start_button.pack(pady=10)

stop_button = tk.Button(root, text="録音停止", command=stop_recording, font=button_font)
stop_button.pack(pady=10)

# 大きくした映像表示用のラベル
video_label = tk.Label(root)
video_label.pack(pady=10)

# GPT-4の返答とユーザー発話の履歴表示
history_text = scrolledtext.ScrolledText(root, wrap=tk.WORD, width=50, height=10, state='disabled', font=label_font)
history_text.pack(pady=10)

# GUIの映像表示を開始
show_video_feed()

# GUIの表示開始
root.mainloop()

# ウィンドウが閉じたらカメラを解放
cap.release()
cv2.destroyAllWindows()
