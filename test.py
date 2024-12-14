import openai
import settings

openai.api_key = settings.AP

prompt = """
以前の会話のログ：
AI:好きな色はなんですか？
私：赤色です
AI:好きな食べ物はなんですか？
私:カレーライスです

以前の会話ログから、まだ私と会話する必要があると判断した場合は、yes、そうでない場合は、noと答えてください。

"""

response = openai.ChatCompletion.create(
    model="gpt-4o-mini",
    messages=[{"role": "system", "content": "結果のみ返答してください。"},
              {"role": "user", "content": prompt}],
    temperature=0  # 応答の一貫性を高める
)

print(response["choices"][0]["message"]["content"])
