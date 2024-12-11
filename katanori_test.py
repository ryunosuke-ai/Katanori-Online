import socket
import numpy as np
import time
import threading

# 肩乗りのIPアドレス, ポート
IP = '127.0.0.1'  # ローカルホストでテスト
PORT = 9210

# 肩乗りにパラメータを送る間隔
INTERVAL = 5.0  # 2秒ごとに方向を変更

default_posture = np.array([0, 0, -50, 0, 0, 30])

limit_min = np.array([-35, -25, -55, -40, -90, -90])
limit_max = np.array([35, 25, 15, 20, 20, 90])

current_posture = default_posture.copy()
last_sent_posture = None  # 最後に送信されたポーズを保存する変数

def robot_posture():
    global current_posture
    return current_posture

def params_to_message(posture):
    return ','.join(map(str, posture))

def adjust_posture(pos):
    pos = np.maximum(pos, limit_min)
    pos = np.minimum(pos, limit_max)
    return pos

def auto_update_posture():
    global current_posture
    next_yaw = -current_posture[5]  # 現在のyaw値を反転させる
    current_posture[5] = next_yaw
    print("Automatically updated yaw to:", next_yaw)

if __name__ == '__main__':
    # UDP通信の設定
    serv_address = (IP, PORT)
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

    # 肩乗りを初期位置へ
    message = params_to_message(default_posture)
    sock.sendto(message.encode("utf-8"), serv_address)
    last_sent_posture = default_posture.copy()
    print('Sending initial parameter:', last_sent_posture)

    while True:
        # 自動更新ループ
        time.sleep(INTERVAL)

        # yawを自動更新
        auto_update_posture()

        # robot_posture()で得られるパラメータを肩乗りに送信
        pos = robot_posture()
        pos = adjust_posture(pos)
        if not np.array_equal(pos, last_sent_posture):
            message = params_to_message(pos)
            sock.sendto(message.encode("utf-8"), serv_address)
            last_sent_posture = pos.copy()
            print('Sending parameter:', pos)
