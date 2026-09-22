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
        theme_str = theme.get("theme", "ペット")
        inst_str = theme.get("instruction", "")
        advice_str = theme.get("userAdvice", "")
    else:
        theme_str = theme

        if isinstance(instruction, dict):
            inst_str = instruction.get("instruction", "")
            advice_str = instruction.get("userAdvice", "")
        else:
            inst_str = instruction or ""
            advice_str = ""

    user_content = f"""
あなたはペットに関するアドバイザーです。
利用者に質問してその回答より利用者に最適なペットをアドバイスするための質問を考えてください。

テーマ: {theme_str}
詳細指示: {inst_str}
補足: {advice_str}

不明、無理な場合はその理由を返してください。
この要求は単独で他の要求とは関係ありません。また他の要求の参考にしないでください。

以下形式で7つの質問を生成してください。

- single: 単選択
  choices に選択肢の文字列配列を入れてください。

- multiple: 複数選択
  choices に選択肢の文字列配列を入れてください。

- text: 20文字以内の単語入力
  choices は空配列 [] にしてください。

- text1: 50文字以内のテキスト入力
  choices は空配列 [] にしてください。
"""

    function_call_payload = {
        "model": MODEL_NAME,
        "messages": [
            {
                "role": "user",
                "content": user_content
            }
        ],
        "tools": [
            {
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
                                        "id": {
                                            "type": "integer"
                                        },
                                        "text": {
                                            "type": "string",
                                            "maxLength": 100
                                        },
                                        "type": {
                                            "type": "string",
                                            "enum": [
                                                "single",
                                                "multiple",
                                                "text",
                                                "text1"
                                            ]
                                        },
                                        "choices": {
                                            "type": "array",
                                            "description":
                                                "single/multipleの場合は選択肢。"
                                                "text/text1の場合は空配列[]",
                                            "items": {
                                                "type": "string",
                                                "maxLength": 50
                                            }
                                        },
                                        "maxLength": {
                                            "type": "integer"
                                        }
                                    },
                                    "required": [
                                        "id",
                                        "text",
                                        "type"
                                    ]
                                }
                            }
                        },
                        "required": [
                            "questions"
                        ]
                    }
                }
            }
        ],
        "tool_choice": "auto"
    }

    return headers, function_call_payload


def get_prompt_r(theme, answers, send_instruction=None):
    """
    Vueアプリが期待する
    {"result": [...]}
    形式で提案を生成する。
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
利用者の回答を元に、おすすめの提案を3パターン生成してください。

テーマ: {theme}

回答データ:
{json.dumps(answers, ensure_ascii=False, indent=2)}

補足指示:
{send_instruction or ''}

不明、無理な場合はその理由を返してください。
"""

    function_call_payload = {
        "model": MODEL_NAME,
        "messages": [
            {
                "role": "user",
                "content": user_content
            }
        ],
        "tools": [
            {
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
                                            "description":
                                                "おすすめの名称・名前"
                                        },
                                        "description": {
                                            "type": "string",
                                            "description":
                                                "提案理由や詳細アドバイス"
                                        }
                                    },
                                    "required": [
                                        "destination",
                                        "description"
                                    ]
                                }
                            }
                        },
                        "required": [
                            "result"
                        ]
                    }
                }
            }
        ],
        "tool_choice": "auto"
    }

    return headers, function_call_payload


def get_result(prompt, answers=None, send_instruction=None):
    """
    get_prompt_q() / get_prompt_r() が作成した
    (headers, payload) をGroq APIへ送信する。

    Tool Callingで返る場合と、
    通常contentでJSONが返る場合の両方に対応する。
    """

    import re

    headers, payload = prompt

    # 質問生成か結果生成かを判定するため保存
    tool_name = payload["tools"][0]["function"]["name"]

    response = requests.post(
        GROQ_API_URL,
        headers=headers,
        json=payload
    )

    if response.status_code != 200:
        raise Exception(
            f"Groq API Error: {response.status_code}, {response.text}"
        )

    response_json = response.json()
    message = response_json["choices"][0]["message"]

    # Tool Callingで返ってきた場合
    if message.get("tool_calls"):
        raw_data = (
            message["tool_calls"][0]
            ["function"]
            ["arguments"]
        )

    # 通常contentで返ってきた場合
    else:
        raw_data = message.get("content", "")

    if isinstance(raw_data, str):

        cleaned = re.sub(
            r"^```(?:json)?\s*",
            "",
            raw_data.strip(),
            flags=re.IGNORECASE
        )

        cleaned = re.sub(
            r"\s*```$",
            "",
            cleaned
        )

        try:
            parsed = json.loads(cleaned)

        except json.JSONDecodeError as e:

            # Groqが
            # {...}
            # {...}
            # {...}
            # のように複数JSONを連続して返す場合に対応
            if tool_name == "get_questions":
                try:
                    decoder = json.JSONDecoder()
                    pos = 0
                    items = []

                    while pos < len(cleaned):

                        # JSON間の空白・改行を読み飛ばす
                        while pos < len(cleaned) and cleaned[pos].isspace():
                            pos += 1

                        if pos >= len(cleaned):
                            break

                        item, pos = decoder.raw_decode(cleaned, pos)
                        items.append(item)

                    parsed = items

                except json.JSONDecodeError:
                    raise Exception(
                        f"Groq JSON parse error: {e}\n"
                        f"raw_data={cleaned}"
                    )

            else:
                raise Exception(
                    f"Groq JSON parse error: {e}\n"
                    f"raw_data={cleaned}"
                )

    else:
        parsed = raw_data

    # -----------------------------
    # 質問生成
    # -----------------------------

    if tool_name == "get_questions":

        # Tool Callingで
        # {"questions": [...]} が返った場合
        if isinstance(parsed, dict) and "questions" in parsed:
            return parsed

        # contentに質問配列だけ返った場合
        if isinstance(parsed, list):
            return {
                "questions": parsed
            }

    # -----------------------------
    # 結果生成
    # -----------------------------

    if tool_name == "get_result_list":

        # Tool Callingで
        # {"result": [...]} が返った場合
        if isinstance(parsed, dict) and "result" in parsed:
            return parsed

        # contentに結果配列だけ返った場合
        if isinstance(parsed, list):
            return {
                "result": parsed
            }

    # -----------------------------
    # 想定外レスポンス
    # -----------------------------

    raise Exception(
        "Groq response format error: "
        + json.dumps(parsed, ensure_ascii=False)
    )
