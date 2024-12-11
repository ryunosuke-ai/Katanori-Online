from threading import Thread
import socket
from playsound import playsound
from gtts import gTTS
import time
import pyaudio
import wave
from db import get_db
import cv2
from answer import no_word
from answer import videocap
from answer import word

loop = True  # 無限ループを制御するフラグ
db = 0
videocaption = ""
speak_word = ""

def text_to_speech(text, language, filename, talk_count):    
    
    # gTTSインスタンスの作成
    text2speech = gTTS(text,           # 音声変換するテキスト
                       lang=language,  # 対応言語（ja：日本語）
                      )

    # 音声変換したデータをファイルに保存
    text2speech.save("./mp3/" + filename + str(talk_count) + ".mp3")
    
    return True

#db
def worker_db():
    global loop
    global db
    chunk = 1024
    FORMAT = pyaudio.paInt16
    CHANNELS = 1
    
    #サンプリングレート
    RATE = 44100
    
    #録音時間を入力
    RECORD_SECONDS = 1
    loop_number = 1

    while loop:

        p = pyaudio.PyAudio()
        
        stream = p.open(
            format = FORMAT,
            channels = CHANNELS,
            rate = RATE,
            input = True,
            frames_per_buffer = chunk
        )
        
        all = []
        for i in range(0, int(RATE / chunk * RECORD_SECONDS)):
            data = stream.read(chunk)
            all.append(data)
        
        stream.close()   
        p.terminate()
        
        data = b''.join(all)
        wav_filename = 'data/wav/wav'+ str(loop_number) +'.wav'

        
        #保存するファイル名、wは書き込みモード
        out = wave.open(wav_filename,'w')
        out.setnchannels(1)
        out.setsampwidth(2)
        out.setframerate(RATE)
        out.writeframes(data)
        out.close()

        loop_number += 1

        #get db
        db = get_db(wav_filename)
        
            
# picture
def worker_video():
    global loop
    global manner_flag
    global videocaption

    photo_count = 1
    #カメラの設定　デバイスIDは0, カメラIDは1
    cap = cv2.VideoCapture(0)
    
    while loop:
        #カメラからの画像取得
        ret, frame = cap.read()
        
        jpg_filename = 'data/jpg/jpg' + str(photo_count) + ".jpg"
        cv2.imwrite(jpg_filename,frame)

        videocaption = videocap(jpg_filename)

        photo_count += 1
        time.sleep(1)
    
    cap.release()
    cv2.destroyAllWindows()



def main():
    global loop

    global db
    global videocap
    global speak_word
    
    thread = Thread(target=worker_db)  # スレッドの作成
    thread.start()  # スレッドの開始
    thread2 = Thread(target=worker_video)  # スレッドの作成
    thread2.start()  # スレッドの開始

    speak_word = "研究頑張ってください"
    language = "ja"
    input_word = "こんにちは"
    filename = "gTTS_Text2Speech"
    talk_count = 0
    host='127.0.0.1'
    port=65432

    while loop:

        # ソケットを作成
        try:
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as server_socket:
                server_socket.bind((host, port))  # アドレスとポートにバインド
                server_socket.listen()  # 接続待ち
                print(f"Server listening on {host}:{port}")

                conn, addr = server_socket.accept()  # クライアント接続を受け入れ
                with conn:
                    print(f"Connected by {addr}")
                    while loop:
                        data = conn.recv(1024)  # データ受信 (1024バイトまで)
                        if not data:
                            break
                        
                        speak_word = data.decode()
                        print(f"Received: {speak_word}")  # 受信したデータを表示

                        """
                        no_word_answer = no_word(videocap, db)

                        if no_word_answer == "Yes":
                            print("touch")
                        else:
                            print("speak")
                        time.sleep(1)
                        """

                        word_answer = word(videocap, speak_word)

                        if word_answer == "タッチ":
                            print("touch")
                        else:
                            print("speak")

                        response = "こんにちは"  # 応答メッセージ

                        text_to_speech(speak_word, language, filename, talk_count)
                        # 音声再生
                        playsound("./mp3/" + filename + str(talk_count) + ".mp3")

                        conn.sendall(response.encode())  # 応答メッセージを送信
                        talk_count += 1
                        time.sleep(1)
                        # flagが立ったらタッチデバイス動作
                        # print(db)


        except KeyboardInterrupt:
            # Ctrl + Cなどが発生したらフラグを折って無限ループを中断する
            loop = False

    thread.join()  # スレッドの終了を待つ
    thread2.join()  # スレッドの終了を待つ

main()