from openai import OpenAI
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

    """display_handle = display(None, display_id=True)
    for img in base64Frames:
        display_handle.update(Image(data=base64.b64decode(img.encode("utf-8"))))
        time.sleep(0.025)"""

    PROMPT_MESSAGES = [
        {
            "role": "user",
            "content": [
                #"These are frames from a video that I want to upload. Generate a compelling description that I can upload along with the video.",
                "アップロードしたい画像のフレームです。この画像の内容を、100文字で簡単に説明してください。",
                *map(lambda x: {"image": x, "resize": 768}, base64Frames[0::50]),
            ],
        },
    ]
    params = {
        "model": "gpt-4o",
        "messages": PROMPT_MESSAGES,
        "max_tokens": 200,
        "temperature": 0,
    }

    result = client.chat.completions.create(**params)
    text = result.choices[0].message.content
    # print(text)

    return text

def no_word(caption, db):

  client = OpenAI()

  text=f"""以下は、ある人物がいる場所について説明した文です。

  「{caption}」

  そして以下は、ある人物がいる場所の音量（デシベル）を示しています。

  「{db}」

  あなたはある人物の方に乗るテレプレゼンスロボットです。ある人物に話しかける際にタッチをする必要がありますか？
  タッチをする必要がある周囲の音量は10dbです。

  <出力例1>
  Yes
  <出力例2>
  No

  <答え>"""

  """completion = openai.Completion.create(
      model="gpt-4o",
      prompt= text,
      max_tokens=2048,
      n=1,
      temperature=0
  )"""


  completion = client.chat.completions.create(
    model="gpt-4o",
    messages=[
      {"role": "system", "content": "You are a helpful assistant."},
      {"role": "user", "content": text}
    ],
    temperature=0
  )

  no_word_answer = completion.choices[0].message.content
  print(no_word_answer)

  return no_word_answer



def word(caption, speak_word):

  client = OpenAI()

  text=f"""あなたは人の肩に乗るテレプレゼンスロボットです。あなたを操作する人が以下の言葉を話しました。

  「{speak_word}」

  以下は、ある人物がいる場所について説明した文です。

  「{caption}」

  遠隔操作者の発言は乗っている人の周囲の環境・状況において、言っていい言葉ですか？以下3つの条件に従って文章を出力してください。

  1. 言っていい場合
    出力：「{speak_word}」

  2. 一部分がふさわしくない場合
    出力：「{speak_word}」のふさわしくない部分を妥当な言葉に変えて出力

  3. 言ってはいけない言葉の場合
    出力：タッチ

  """

  """completion = openai.Completion.create(
      model="gpt-4o",
      prompt= text,
      max_tokens=2048,
      n=1,
      temperature=0
  )"""


  completion = client.chat.completions.create(
    model="gpt-4o",
    messages=[
      {"role": "system", "content": "You are a helpful assistant."},
      {"role": "user", "content": text}
    ],
    temperature=0
  )

  word_answer = completion.choices[0].message.content
  print(word_answer)

  return word_answer