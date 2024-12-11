from IPython.display import display, Image, Audio
import cv2  # We're using OpenCV to read video, to install !pip install opencv-python
import base64
import time
from openai import OpenAI
import os
import requests

def videocap(videoname):
    client = OpenAI()

    video = cv2.VideoCapture(videoname)

    base64Frames = []
    while video.isOpened():
        
        success, frame = video.read()
        if not success:
            break
        _, buffer = cv2.imencode(".jpg", frame)
        base64Frames.append(base64.b64encode(buffer).decode("utf-8"))

    video.release()#これを最後に持ってくる？
    print(len(base64Frames), "frames read.")

    """display_handle = display(None, display_id=True)
    for img in base64Frames:
        display_handle.update(Image(data=base64.b64decode(img.encode("utf-8"))))
        time.sleep(0.025)"""

    PROMPT_MESSAGES = [
        {
            "role": "user",
            "content": [
                #"These are frames from a video that I want to upload. Generate a compelling description that I can upload along with the video.",
                "アップロードしたい画像のフレームです。この動画の内容について簡単に説明してください。",
                *map(lambda x: {"image": x, "resize": 768}, base64Frames[0::50]),
            ],
        },
    ]
    params = {
        "model": "gpt-4-vision-preview",
        "messages": PROMPT_MESSAGES,
        "max_tokens": 200,
    }

    result = client.chat.completions.create(**params)
    text = result.choices[0].message.content
    print(text)
    return text

videoname = "jpg1.jpg"
print(videocap(videoname))
