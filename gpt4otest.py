import openai
import base64
import cv2
import os

openai.api_key="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"

def encode_image(image_path):
  with open(image_path, "rb") as image_file:
    return base64.b64encode(image_file.read()).decode('utf-8')
  
def capture_image(filename="captured_image.png"):
    # カメラを初期化
    cap = cv2.VideoCapture(0)

    if not cap.isOpened():
        print("カメラを開くことができませんでした")
        return

    # 画像をキャプチャ
    ret, frame = cap.read()

    if ret:
        # 画像の保存パスを決定（現在のディレクトリ）
        current_dir = os.path.dirname(os.path.abspath(__file__))
        save_path = os.path.join(current_dir, filename)
        
        # 画像を保存
        cv2.imwrite(save_path, frame)
        print(f"画像が保存されました: {save_path}")
    else:
        print("画像をキャプチャできませんでした")

    # カメラを解放
    cap.release()

# 画像を撮影して保存
capture_image()

base64_image = encode_image("captured_image.png")

response = openai.ChatCompletion.create(
  model="gpt-4o",
  messages=[
    {
      "role": "system",
      "content": "あなたは明るい雰囲気の人です。話を盛り上げるように話します。"
    },
    {
      "role": "user",
      "content": [
        {"type": "text", "text": "提供された画像について説明し、話を盛り上げるようなその画像の内容に関する質問をしてください。\
         質問は、画像を見た若者と高齢者の二人にすることを想定しているので、それぞれに対する2つの質問を生成してください。"},
        {
          "type": "image_url",
          "image_url": {
            "url": f"data:image/jpeg;base64,{base64_image}"
          }
        }
      ]
    }
  ],
  max_tokens=300
)
print(response.choices[0].message.content)

"""
response = openai.ChatCompletion.create(
            model="gpt-4o",
            messages=[
            {
                "role": "system",
                "content": "あなたは明るい雰囲気の人です。話を盛り上げるように話します。"
            },
            {
                "role": "user",
                "content": [
                {"type": "text", "text": "過去の会話の流れ:\n{past_conversation}\n\
                 現在の発言: {current_text}\n\
                 提供された画像について説明し、話を盛り上げるようなその画像の内容に関する質問をしてください。\
                 質問は、画像を見た若者と高齢者の二人にすることを想定しているので、それぞれに対する2つの質問を生成してください。"},
                {
                "type": "image_url",
                "image_url": {
                    "url": f"data:image/jpeg;base64,{base64_image}"
                }
                }
                ]
            }
            ],
            max_tokens=300
            )
        print(response.choices[0].message.content)
"""

"""
openai.api_key = "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"

# JSONファイルのパスを指定（ユーザーの環境に合わせてパスを設定してください）
json_file_path = "my-project-test-436808-4ac407ed29b1.json"

# 環境変数を設定
os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = json_file_path"""