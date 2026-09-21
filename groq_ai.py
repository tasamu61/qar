import json
import os
import requests

GROQ_API_URL = "https://api.groq.com/openai/v1/chat/completions"
MODEL_NAME = "openai/gpt-oss-20b"

def get_prompt_q(theme, instruction=None):
    api_key = os.environ.get("GROQKEY")
    if not api_key:
        raise ValueError("環境変数 'GROQKEY' が設定されていません。")

    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    }

    if isinstance(theme, dict):
        theme_str = theme.get('theme', 'ペット')
        inst_str = theme.get('instruction', '')
        advice_str = theme.get('userAdvice', '')
    else:
        theme_str = theme
        if isinstance(instruction, dict):
            inst_str = instruction.get('instruction', '')
            advice_str = instruction.get('userAdvice', '')
        else:
            inst_str = instruction or ''
            advice_str = ''

    user_content = f"""
あなたはペットに関するアドバイザーです。
利用者に質問してその回答より利用者に最適なペットをアドバイスするための質問を考えてください。

テーマ: {theme_str}
詳細指示: {inst_str}
補足: {advice_str}
不明、無理な場合はその理由を返してください。
この要求は単独で他の要求とは関係ありません。また他の要求の参考にしないでください。

以下形式で7つの質問を生成してください。
- single: 単選択 (※必ず choices に選択肢の文字列配列を入れてください)
- multiple: 複数選択 (※必ず choices に選択肢の文字列配列を入れてください)
- word: 20文字以内の単語 (※ choices は [] 空配列にしてください)
- text: 50文字以内のテキスト (※ choices は [] 空配列にしてください)
"""

    function_call_payload = {
        "model": MODEL_NAME,
        "messages": [
            {"role": "user", "content": user_content}
        ],
        "tools": [{
            "type": "function",
            "function": {
                "name": "get_questions",
                "description": "ペットに関する質問を生成します。",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "questions": {
                            "type": "array",
                            "description": "質問の配列",
                            "items": {
                                "type": "object",
                                "properties": {
                                    "id": {"type": "integer"},
                                    "text": {"type": "string", "maxLength": 50},
                                    "type": {"type": "string", "enum": ["single", "multiple", "word", "text"]},
                                    "choices": {
                                        "type": "array",
                                        "description": "single/multipleの場合は選択肢の配列。word/textの場合は空配列[]",
                                        "items": {"type": "string", "maxLength": 20}
                                    }
                                },
                                "required": ["id", "text", "type"]
                            }
                        }
                    },
                    "required": ["questions"]
                }
            }
        }],
        "tool_choice": "auto"
    }

    return headers, function_call_payload


def get_prompt_r(theme, answers, send_instruction=None):
    """
    Vueアプリ(vue_app.js)が期待する result 配列形式(destinationを含むオブジェクトの配列)で出力するように定義
    """
    api_key = os.environ.get("GROQKEY")
    if not api_key:
        raise ValueError("環境変数 'GROQKEY' が設定されていません。")

    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    }

    data = {
        "theme": theme,
        "answers": answers,
        "sendInstruction": send_instruction
    }

    user_content = f"""
利用者の回答を元に、おすすめの提案（ペットや旅行先・選択肢等）を3パターン生成してください。

回答データ: {json.dumps(data, ensure_ascii=False)}
補足指示: {send_instruction or ''}
"""

    function_call_payload = {
        "model": MODEL_NAME,
        "messages": [
            {"role": "user", "content": user_content}
        ],
        "tools": [{
            "type": "function",
            "function": {
                "name": "get_result_list",
                "description": "回答に応じた提案リストを生成します。",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "result": {
                            "type": "array",
                            "description": "提案の配列",
                            "items": {
                                "type": "object",
                                "properties": {
                                    "destination": {
                                        "type": "string", 
                                        "description": "おすすめの名称・名前（検索キーワードのメイン部分）"
                                    },
                                    "description": {
                                        "type": "string", 
                                        "description": "提案理由や詳細アドバイス"
                                    }
                                },
                                "required": ["destination", "description"]
                            }
                        }
                    },
                    "required": ["result"]
                }
            }
        }],
        "tool_choice": "auto"
    }

    return headers, function_call_payload


def get_result(prompt, answers=None, send_instruction=None):
    """
    web_serv.py 側からの呼び出しに対応し、回答結果のアドバイス(get_prompt_r)を正しく生成します。
    """
    import re

    # 1. パラメータの判定と get_prompt_r の呼び出し
    # answers が渡されているか、prompt (第一引数) が辞書型で answers キーを持つ場合はアドバイス取得
    if answers is not None:
        headers, payload = get_prompt_r(prompt, answers, send_instruction)
    elif isinstance(prompt, dict) and "answers" in prompt:
        headers, payload = get_prompt_r(
            prompt.get("theme"), 
            prompt.get("answers"), 
            prompt.get("sendInstruction")
        )
    else:
        # prompt が文字列等で answers が渡されない場合（回答データ全体が prompt に入っている場合）
        headers, payload = get_prompt_r(prompt, [], send_instruction)

    # 2. Groq API 呼び出し
    response = requests.post(GROQ_API_URL, headers=headers, json=payload)

    if response.status_code != 200:
        raise Exception(f"Groq API Error: {response.status_code}, {response.text}")

    response_json = response.json()
    message = response_json["choices"][0]["message"]

    # 3. レスポンスからのデータ抽出
    raw_data = None
    if "tool_calls" in message and len(message["tool_calls"]) > 0:
        raw_data = message["tool_calls"][0]["function"]["arguments"]
    else:
        raw_data = message.get("content", "")

    # 4. 文字列の場合は JSON パース（```json などのクリーニング処理含む）
    if isinstance(raw_data, str):
        # Markdownのコードブロックタグ(```json ... ```)を解除
        cleaned = re.sub(r"^```(?:json)?\s*", "", raw_data.strip(), flags=re.IGNORECASE)
        cleaned = re.sub(r"\s*```$", "", cleaned)
        
        try:
            parsed = json.loads(cleaned)
            # Vue側が期待する { "result": [...] } 形式で補正
            if isinstance(parsed, list):
                return {"result": parsed}
            elif isinstance(parsed, dict):
                if "result" in parsed:
                    return parsed
                elif "questions" in parsed:
                    # 万が一 LLM が質問形式で返してしまった場合のフォールバック
                    return {
                        "result": [{
                            "destination": "回答結果",
                            "description": "ご回答ありがとうございました。最適なペットの条件を分析しました。"
                        }]
                    }
                else:
                    return {"result": [parsed]}
            return {"result": [{"destination": "アドバイス", "description": str(parsed)}]}
        except json.JSONDecodeError:
            return {
                "result": [{
                    "destination": "おすすめのペット",
                    "description": cleaned
                }]
            }

    # すでに dict の場合
    if isinstance(raw_data, dict) and "result" not in raw_data:
        return {"result": [raw_data]}

    return raw_data