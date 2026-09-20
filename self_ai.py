import google.generativeai as genai
import json, os, requests
from flask import Response



def get_prompt_r(title, answers):
    

# プロンプトの作成
    function_call_payload = {
    "model": "gpt-4o-mini",
    "messages": [
        {
            "role": "user",
            "content": f"""
あなたは{title}に関するアドバイザー
以下は{title}に関する質問結果です：

{json.dumps(answers, ensure_ascii=False, indent=2)}

この情報をもとに、以下の形式でおすすめの{title}を3つ提案してください。
参考URLは1件だけです。
かならず n["choices"][0]["message"]["function_call"]["arguments"]
で当該jsonを取得できる電文にしてください。
出力はJSON形式のみ。余計な解説文・前置き・マークダウンは含めないでください。
条件を満たす候補提示が困難な場合、同じフォーマットでdescriptionにその理由を返してください。
返信は、コードはUTF-8でおねがいします。

"""
        }
    ],
    "functions": [
        {
            "name": "get_result",
            "description": f"{title}に関する質問結果から候補を生成します。",
            "parameters": {
                "type": "object",
                "properties": {
                    "result": {
                        "type": "array",
                        "description": "おすすめ候補の配列",
                        "items": {
                            "type": "object",
                            "properties": {
                                "destination": {
                                    "type": "string",
                                    "description": "候補の名前"
                                },
                                "score": {
                                    "type": "integer",
                                    "description": "おすすめ度（0〜100）"
                                },
                                "description": {
                                    "type": "string",
                                    "description": "候補の説明（100〜200文字）"
                                },
                                "url": {
                                    "type": "string",
                                    "description": "参考URL"
                                }
                            },
                            "required": ["destination", "score", "description", "url"]
                        }
                    }
                },
                "required": ["result"]
            }
        }
    ],
    "function_call": {
        "name": "get_result"
    }
}
    
    print(function_call_payload)
    return function_call_payload



def get_result(function_call_payload):
    ai_response = requests.post(
        "http://localhost:8000/get_result",
        json=function_call_payload,
        timeout=10
    )

    # AIサーバからのJSON応答をパースして返す
    try:
        result = json.loads(ai_response.text);

        return result
    except Exception as e:
        # 何か問題あれば生レスポンス文字列で返す
        return Response(ai_response.text, content_type="application/json; charset=utf-8")

# resp = get_response(istr)
     
