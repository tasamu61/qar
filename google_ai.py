import google.generativeai as genai
import json, os, logging


def get_prompt_q(theme, instruction):
    prompt = f"""
{instruction}
出力はJSON形式のみ。余計な解説文・前置き・マークダウンは含めないでください。
返信は、コードはUTF-8でおねがいします。以下形式でお願いします。

{{
  "questions": [
    {{
      "id": 1,
      "text": "質問文",
      "type": "single",         // 単選択
      "choices": ["選択肢A", "選択肢B"] // 単選択・複数選択の場合のみ
    }},
    {{
      "id": 2,
      "text": "質問文",
      "type": "multiple",       // 複数選択
      "choices": ["選択肢A", "選択肢B"]
    }},
    {{
      "id": 3,
      "text": "質問文",
      "type": "text",           // 20文字以内の単語
      "maxLength": 40
    }},
    {{
      "id": 4,
      "text": "質問文",
      "type": "text1",           // 50文字以内のテキスト
      "maxLength": 100
    }}
  ]
}}
"""
    return prompt


def get_prompt_r(theme, answers ,sendInstruction):
    # プロンプトの作成
    prompt = f"""
あなたは{theme}に関するアドバイザー
 {sendInstruction}
以下は{theme}に関する質問結果です。
{json.dumps(answers, ensure_ascii=False, indent=2)}
この情報をもとに、以下の形式でおすすめの{theme}を3つ提案してください。
候補提示が無理なら、同じフォーマットでdescriptionにその理由を返してください。
必ず
response.candidates[0].content.parts[0].text.strip().removeprefix("```json").removesuffix("```").strip()
で当該jsonを取得できる電文にしてください。
出力はJSON形式のみ。余計な解説文・前置き・マークダウンは含めないでください。
この要求は単独で他の要求とは関係ありません。
返信は、コードはUTF-8でおねがいします。
**【重要】**
**レスポンスは以下のJSONスキーマと構造に厳密に従ってください。**
**特に、最上位のキーは**`"result"`** としてください。**
**余計な解説文・前置き・マークダウン（```json```）は一切含めないでください。**
**返信はUTF-8でお願いします。**
  "result": [ <-- トップレベルのキーは必ず「result」にしてください
    {{
      "destination": "候補名",
      "score": 数値（0-100）,
      "description": "説明（100～200文字）",
      "url": "参考URL"
    }},
    ...
  ]
}}
"""


    return prompt



def get_result(prompt):
    # APIキーを設定   
    gkey = os.getenv("GKEY") 
    genai.configure(api_key= gkey)
    model = genai.GenerativeModel("models/gemini-1.5-pro-latest")# モデルに問い合わせ
    logging.debug(f"P {prompt}")
    response = model.generate_content(prompt)
    logging.debug(f"R {response}")
    # JSONとしてパースできるか試す（念のため）
    try:

        json_str = response.candidates[0].content.parts[0].text.strip().removeprefix("```json").removesuffix("```").strip()
        result = json.loads(json_str);
        logging.debug(f"R {result}")
        return result
    except Exception as e:
        print("⚠️ JSONパースエラー:", e)
        return response

