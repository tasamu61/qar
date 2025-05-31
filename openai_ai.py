import google.generativeai as genai
import json, os, requests


def get_prompt_q(theme, instruction):
    instruction = instruction.replace("{", "{{").replace("}", "}}")

    function_call_payload = {
        "model": "gpt-4o-mini",
        "messages": [
            {
                "role": "user",
                "content": f"""{instruction}
必ず ["choices"][0]["message"]["function_call"]["arguments"] で当該jsonを取得できる電文にしてください。
出力はJSON形式のみ。余計な解説文・前置き・マークダウンは含めないでください。
返信は、コードはUTF-8でおねがいします。"""
            }
        ],
        "functions": [
            {
                "name": "get_questions",
                "description": f"{theme}に関する質問を生成します。",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "questions": {
                            "type": "array",
                            "description": "質問の配列",
                            "items": {
                                "questions": {
                                    "type": "array",
                                    "items": {
                                        "type": "object",
                                        "properties": {
                                            "id": {"type": "integer"},
                                            "text": {"type": "string", "maxLength": 50},
                                            "type": {"type": "string", "enum": ["single", "multiple", "word", "text"]},
                                            "choices": {
                                                "type": "array",
                                                "items": {
                                                    "type": "string",
                                                    "maxLength": 20
                                                }
                                            }
                                        },
                                        "required": ["id", "text", "type", "choices"]
                                    }
                                }
                            }
                        }
                    },
                    "required": ["questions"]
                }
            }
        ],
        "function_call": {
            "name": "get_questions"
        }
    }
    
 
    return function_call_payload

                        
                



def get_prompt_r(title, answers):

# プロンプトの作成
    function_call_payload = {
    "model": "gpt-4o-mini",
    "messages": [
        {
            "role": "user",
            "content": f"""
あなたは{title}に関するアドバイザー
以下は{title}に関するアンケート結果です：
{json.dumps(answers, ensure_ascii=False, indent=2)}
この情報をもとに、以下の形式でおすすめの{title}を3つ提案してください。
候補提示が無理なら、同じフォーマットでdescriptionにその理由を返してください。
日程、予算が未入力なら、それについても案を提示してアドバイスもしてください。
必ず
かならず n["choices"][0]["message"]["function_call"]["arguments"]
で当該jsonを取得できる電文にしてください。
出力はJSON形式のみ。余計な解説文・前置き・マークダウンは含めないでください。
返信は、コードはUTF-8でおねがいします。
"""
        }
    ],
    "functions": [
        {
            "name": "get_result",
            "description": f"{title}に関するアンケート結果から候補を生成します。",
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
    # APIキーを設定   
    okey = os.getenv("OKEY") 
    ai_response = requests.post(
        "https://api.openai.com/v1/chat/completions",
        headers={
            "Authorization": f"Bearer {okey}",
            "Content-Type": "application/json"
        },
        json=function_call_payload,  # 事前に作成された Function Calling 用ペイロード
        timeout=10
    )
    print(ai_response.text)
# レスポンスを JSON（辞書）として取得
    response_json = ai_response.json()

# arguments を文字列として取り出す
    raw_json = response_json["choices"][0]["message"]["function_call"]["arguments"]

# 文字列を Python の辞書に変換
    parsed_arguments = json.loads(raw_json)
    return parsed_arguments
