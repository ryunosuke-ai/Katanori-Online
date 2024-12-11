import openai
import base64
import cv2
import time

# GPT APIキーの設定
openai.api_key = "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"

def encode_image(image_path):
    """画像をBase64エンコードする"""
    with open(image_path, "rb") as image_file:
        return base64.b64encode(image_file.read()).decode('utf-8')

def capture_image(output_path):
    """カメラから画像をキャプチャして保存する"""
    cap = cv2.VideoCapture(0)
    if not cap.isOpened():
        raise Exception("カメラを開けませんでした")

    ret, frame = cap.read()
    if ret:
        cv2.imwrite(output_path, frame)
    else:
        raise Exception("画像をキャプチャできませんでした")
    cap.release()

def send_image_to_gpt(base64_image):
    """画像をGPTに送信して説明を生成する"""
    response = openai.ChatCompletion.create(
        model="gpt-4o",
        messages=[
            {
                "role": "system",
                "content": "明るい雰囲気で答えてください．"
            },
            {
                "role": "user",
                "content": [
                    {"type": "text", "text": "提供された画像について説明してください。"},
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
    return response.choices[0].message.content

def main():
    image_path = "captured_image.jpg"
    interval_seconds = 10  # 撮影間隔（秒）

    while True:
        try:
            print("画像を撮影中...")
            capture_image(image_path)

            print("画像をエンコード中...")
            base64_image = encode_image(image_path)

            print("画像をGPTに送信中...")
            description = send_image_to_gpt(base64_image)

            print("GPTの応答:")
            print(description)
        except Exception as e:
            print(f"エラーが発生しました: {e}")

        print(f"{interval_seconds}秒後に再実行します...\n")
        time.sleep(interval_seconds)

if __name__ == "__main__":
    main()
