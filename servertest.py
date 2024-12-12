from flask import Flask
import socketio
import base64
import cv2
import numpy as np
import tkinter as tk
from PIL import Image, ImageTk

# FlaskアプリとSocket.IOサーバーをセットアップ
app = Flask(__name__)
sio = socketio.Server()
app.wsgi_app = socketio.WSGIApp(sio, app.wsgi_app)

# GUIセットアップ
root = tk.Tk()
root.title("リアルタイム映像")

# ラベルウィジェット（映像表示用）
video_label = tk.Label(root)
video_label.pack()

# 画像デコード関数
def decode_image(image_data):
    image = base64.b64decode(image_data)
    np_arr = np.frombuffer(image, np.uint8)
    return cv2.imdecode(np_arr, cv2.IMREAD_COLOR)

# フレームを受信したときの処理（映像）
@sio.on('stream_frame')
def handle_stream_frame(sid, data):
    frame_data = data['image']
    frame = decode_image(frame_data)

    # OpenCVの画像からPILに変換し、Tkinterで表示
    cv2image = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
    img = Image.fromarray(cv2image).resize((400, 300))
    imgtk = ImageTk.PhotoImage(image=img)
    video_label.imgtk = imgtk
    video_label.config(image=imgtk)
    root.update_idletasks()  # GUIの更新

# 写真を受信したときの処理（上書き保存のみ）
@sio.on('send_image')
def handle_send_image(sid, data):
    image_data = data['image']
    image = decode_image(image_data)
    filename = "latest_received_image.jpg"  # ファイル名を固定
    cv2.imwrite(filename, image)  # 上書き保存
    print(f"写真を上書き保存しました: {filename}")

# Flaskサーバー起動
if __name__ == '__main__':
    import threading
    # Socket.IOサーバーを別スレッドで実行
    threading.Thread(target=lambda: app.run(host='0.0.0.0', port=5001)).start()
    # Tkinterのメインループ
    root.mainloop()
