import socket
import time
import speech_recognition as sr
 
def text_to_speech(text, language, filename, talk_count):    
    
    # gTTSインスタンスの作成
    text2speech = gTTS(text,           # 音声変換するテキスト
                       lang=language,  # 対応言語（ja：日本語）
                      )

    # 音声変換したデータをファイルに保存
    text2speech.save("./mp3/" + filename + str(talk_count) + ".mp3")
    
    return True


def start_client(host='127.0.0.1', port=65432):
    # ソケットを作成
    recognizer = sr.Recognizer()
    while True:
        try:
            with sr.Microphone() as source:
                print("話してください")
                # playsound(filename_play_demo)
                ## 録音開始
                # audio = recognizer.listen(source)
                ## 文字起こし
                #input_word = recognizer.recognize_google(audio, language="ja-JP")
                input_word = "こんにちは"
                print(input_word)
        except Exception as e:
            print(e)

        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as client_socket:
            client_socket.connect((host, port))  # サーバーに接続
            message = input_word  # 送信するメッセージを入力
            if not message:
                break
            client_socket.sendall(message.encode())  # メッセージを送信

            data = client_socket.recv(1024)  # サーバーからの応答を受信
            print(f"Received: {data.decode()}")  # 受信した応答を表示
            time.sleep(1)

if __name__ == "__main__":
    start_client()
