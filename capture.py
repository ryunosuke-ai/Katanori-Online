import cv2
import openai
from google.cloud import vision, texttospeech
from google.oauth2 import service_account
from PIL import Image
import io
from pydub import AudioSegment
from pydub.playback import play
import threading

# OpenAI APIキーを設定します（自分のAPIキーを入力してください）
openai.api_key = "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"

# サービスアカウントキーのJSONファイルのパスを指定します
credentials_path = 'my-project-test-436808-4ac407ed29b1.json'  # 自分のファイルパスに置き換えてください

# 認証情報を読み込み、Google Cloud Vision APIクライアントを初期化します
credentials = service_account.Credentials.from_service_account_file(credentials_path)
vision_client = vision.ImageAnnotatorClient(credentials=credentials)

# Google Cloud Text-to-Speech APIクライアントを初期化します
tts_client = texttospeech.TextToSpeechClient(credentials=credentials)

# カメラを初期化して画像をキャプチャします
cap = cv2.VideoCapture(0)

# カメラが開けない場合はエラーを表示します
if not cap.isOpened():
    print("カメラが開けませんでした")
    exit()

# 画像をキャプチャします
ret, frame = cap.read()
if not ret:
    print("画像をキャプチャできませんでした")
    cap.release()
    exit()

# カメラを解放します
cap.release()

# 画像をPIL形式に変換します
image = Image.fromarray(cv2.cvtColor(frame, cv2.COLOR_BGR2RGB))

# キャプチャした画像を保存します
image_save_path = "captured_image.png"  # 保存する画像のパスを指定します
image.save(image_save_path, format='PNG')
print(f"画像を保存しました: {image_save_path}")

# 画像をバイトに変換します
img_byte_arr = io.BytesIO()
image.save(img_byte_arr, format='PNG')
img_byte_arr = img_byte_arr.getvalue()

# Vision APIに画像を送信してラベルを取得します
image_vision = vision.Image(content=img_byte_arr)
response = vision_client.label_detection(image=image_vision)

# Vision APIのレスポンスを解析します
labels = response.label_annotations
label_descriptions = [label.description for label in labels]

# 認識されたラベルをOpenAI APIに送信して説明を生成します
prompt_description = f"この画像には、{', '.join(label_descriptions)}があります。この画像について日本語で説明してください。"
description_response = openai.ChatCompletion.create(
    model="gpt-3.5-turbo",
    messages=[
        {"role": "system", "content": "あなたは画像の内容について日本語で説明を行うアシスタントです。"},
        {"role": "user", "content": prompt_description}
    ]
)

# 説明文を取得します
description = description_response['choices'][0]['message']['content']

# 画像に関する質問文を生成します
prompt_question = f"この画像には、{', '.join(label_descriptions)}があります。この画像に関連する質問を一つ日本語で生成してください。"
question_response = openai.ChatCompletion.create(
    model="gpt-3.5-turbo",
    messages=[
        {"role": "system", "content": "あなたは画像に関連する質問を日本語で生成するアシスタントです。"},
        {"role": "user", "content": prompt_question}
    ]
)

# 質問文を取得します
question = question_response['choices'][0]['message']['content']

# 結果を表示します
print(f"画像の説明: {description}")
print(f"画像に関する質問: {question}")

# 音声を再生する関数
def play_audio(file_path):
    audio = AudioSegment.from_mp3(file_path)
    play(audio)

# Google Cloud Text-to-Speech APIを使用して説明文を音声に変換します
def synthesize_speech(text):
    synthesis_input = texttospeech.SynthesisInput(text=text)
    voice = texttospeech.VoiceSelectionParams(
        language_code="ja-JP",
        ssml_gender=texttospeech.SsmlVoiceGender.NEUTRAL
    )
    audio_config = texttospeech.AudioConfig(
        audio_encoding=texttospeech.AudioEncoding.MP3
    )
    response = tts_client.synthesize_speech(
        input=synthesis_input,
        voice=voice,
        audio_config=audio_config
    )
    # 音声ファイルを保存
    audio_file_path = "output.mp3"
    with open(audio_file_path, "wb") as out:
        out.write(response.audio_content)
        print("音声ファイルを保存しました: output.mp3")

    # 画像を表示しながら音声を再生
    img = cv2.imread(image_save_path)
    cv2.imshow("Captured Image", img)

    # 音声を再生するスレッドを開始
    audio_thread = threading.Thread(target=play_audio, args=(audio_file_path,))
    audio_thread.start()

    # 音声再生中に画像を表示するため、キー入力を待つ
    cv2.waitKey(0)

    # ウィンドウを閉じる
    cv2.destroyAllWindows()

# 生成された説明文を読み上げ
synthesize_speech(description)
# 生成された質問文を読み上げ
synthesize_speech(question)
