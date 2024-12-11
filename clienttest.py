import socketio
import cv2
import base64
import time

# サーバーのURL
sio = socketio.Client()
sio.connect('http://192.168.0.12:5001')  # elderly_pc_ipはサーバーPCのIPアドレス

# Webカメラ映像の送信
cap = cv2.VideoCapture(0)
capture_interval = 5  # 写真を送信する間隔（秒）
last_capture_time = time.time()

try:
    while cap.isOpened():
        ret, frame = cap.read()
        if ret:
            # フレームをJPEGにエンコードしてBase64に変換
            _, buffer = cv2.imencode('.jpg', frame)
            frame_data = base64.b64encode(buffer).decode('utf-8')
            sio.emit('stream_frame', {'image': frame_data})
            print("リアルタイムフレームを送信しました")

            # 一定間隔でキャプチャを保存・送信
            if time.time() - last_capture_time >= capture_interval:
                sio.emit('send_image', {'image': frame_data})
                print("写真を送信しました")
                last_capture_time = time.time()
        
        # 少し待機して次のフレーム送信
        time.sleep(0.1)

except KeyboardInterrupt:
    pass

finally:
    cap.release()
    sio.disconnect()
