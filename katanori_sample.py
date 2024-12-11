import socket
import numpy as np
import time
import random

# 肩乗りのIPアドレス, ポート
IP = '127.0.0.1' # '192.168.1.19'
PORT = 9210

# 肩乗りにパラメータを送る間隔
INTERVAL = 0.3 # 念のため0.3秒以上推奨

default_posture = np.array([0, # 目の上下 -35（下）～35（上）
                            0, # 目の左右 -25（左）～25（右）
                            -50, # まぶたの開閉 -50（開く）～13（閉じる）
                            0, # 胴体のroll -40（左）～20（右）
                            0, # 胴体のpitch -90（前）～20（後ろ）
                            30]) # 胴体のyaw -90（右）～90（左）

limit_min = np.array([-35, -25, -55, -40, -90, -90])
limit_max = np.array([35, 25, 15, 20, 20, 90])

def robot_posture(): 
    # 引数や処理の内容を編集して好きな動きをさせよう
    # 以下は簡易的にまばたきさせる例
    posture = default_posture.copy()

    # まばたき
    if random.random() > 0.9:
        posture[2] = -15
    
    return posture

def params_to_message(posture):
    return ','.join(map(str, posture))

def adjust_posture(pos):
    # 肩乗りに限界以上の値を送信しないように調整
    pos = np.stack([pos, limit_min]).max(axis=0)
    pos = np.stack([pos, limit_max]).min(axis=0)
    return pos

if __name__ == '__main__':
    #udp通信の設定
    serv_address = (IP, PORT)
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

    #肩乗りを初期位置へ
    message = params_to_message(default_posture)
    sock.sendto(message.encode("utf-8"), serv_address)

    while True:
        # 肩乗りが動き終わるのを待つ
        time.sleep(INTERVAL)

        # robot_posture()で得られるパラメータを肩乗りに送信
        pos = robot_posture()
        pos = adjust_posture(pos)
        
        print('parameter:', pos)
        sock.sendto(message.encode("utf-8"), serv_address)