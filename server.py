import socket
import time
from playsound import playsound
from gtts import gTTS

def text_to_speech(text, language, filename, talk_count):    
    
    # gTTSインスタンスの作成
    text2speech = gTTS(text,           # 音声変換するテキスト
                       lang=language,  # 対応言語（ja：日本語）
                      )

    # 音声変換したデータをファイルに保存
    text2speech.save("./mp3/" + filename + str(talk_count) + ".mp3")
    
    return True

def start_server(host='127.0.0.1', port=65432):
    language = "ja"
    input_word = "こんにちは"
    filename = "gTTS_Text2Speech"
    talk_count = 0

    while True:
        # ソケットを作成
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as server_socket:
            server_socket.bind((host, port))  # アドレスとポートにバインド
            server_socket.listen()  # 接続待ち
            print(f"Server listening on {host}:{port}")

            conn, addr = server_socket.accept()  # クライアント接続を受け入れ
            with conn:
                print(f"Connected by {addr}")
                while True:
                    data = conn.recv(1024)  # データ受信 (1024バイトまで)
                    if not data:
                        break
                    
                    word = data.decode()
                    print(f"Received: {word}")  # 受信したデータを表示
                    response = "こんにちは"  # 応答メッセージ

                    text_to_speech(word, language, filename, talk_count)
                    # 音声再生
                    playsound("./mp3/" + filename + str(talk_count) + ".mp3")

                    conn.sendall(response.encode())  # 応答メッセージを送信
                    talk_count += 1
                    time.sleep(1)

if __name__ == "__main__":
    start_server()
