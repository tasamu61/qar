import os
import json
import random
import requests
import time

BASE_URL = "http://127.0.0.1:5001"

OKEY = os.environ.get("OKEY")
GKEY = os.environ.get("GKEY")
GROQKEY = os.environ.get("GROQKEY")

WAIT_TIME = 5
TEST_COUNT = 9

session = requests.Session()


SAMPLES = [
    {
        "theme": "ペット",
        "question_instruction":
            "家で飼うペットについてです。家の種類は５種、"
            "ペットに臨むことは20種複数選択、"
            "好みについてテキストで入力可能で作成してください。",
        "result_instruction":
            "不明、無理な場合はその理由を返してください。"
    },
    {
        "theme": "恋",
        "question_instruction":
            "職場に好きな人がいますが、話したこともなく"
            "告白もできません、仲良くなる方法を教えてください。",
        "result_instruction":
            "最初にどのようにして接触すればいいでしょう？"
    },
    {
        "theme": "自治体へのＡＩ導入",
        "question_instruction":
            "自治体の業務システムで導入しやすく、"
            "効果が得やすいＡＩを提案するための質問は？",
        "result_instruction":
            "試行的なため、一般市民に開放ではなく、"
            "職員が使うシステムがよい。"
    }
]


AIS = [
    "openai",
    "google",
    "groq"
]


AI_NAMES = {
    "openai": "OpenAI",
    "google": "Google",
    "groq": "Groq"
}


#
# テスト結果
#

history = []

stats = {
    ai: {
        "question": {
            "ok": 0,
            "ng": 0
        },
        "answer": {
            "ok": 0,
            "ng": 0
        },
        "result": {
            "ok": 0,
            "ng": 0
        }
    }
    for ai in AIS
}


def record(
    ai,
    process,
    ok
):

    if ok:

        stats[ai][process]["ok"] += 1

    else:

        stats[ai][process]["ng"] += 1


#
# QARを利用して質問生成
#

def get_questions(
    ai,
    sample
):

    data = {
        "title": "some",
        "theme":
            sample["theme"],
        "instruction":
            sample["question_instruction"],
        "sendInstruction":
            sample["question_instruction"],
        "userAdvice": "",
        "aillm": ai
    }

    start = time.time()

    try:

        response = session.post(
            BASE_URL + "/get_questions",
            json=data,
            timeout=120
        )

    except Exception as e:

        print(
            "質問生成通信エラー:",
            e
        )

        return None

    elapsed = time.time() - start

    print(
        f"{AI_NAMES[ai]} 質問生成: "
        f"{response.status_code} "
        f"{elapsed:.2f}秒"
    )

    if response.status_code != 200:

        print_error(
            response
        )

        return None

    try:

        result = response.json()

    except Exception:

        print(
            "質問JSON形式違反"
        )

        return None

    questions = result.get(
        "questions"
    )

    if not questions:

        print(
            "questions がありません"
        )

        return None

    return questions


#
# 回答用プロンプト
#

def make_answer_prompt(
    theme,
    questions
):

    return f"""
あなたはQARシステムのテスト回答者です。

テーマは「{theme}」です。

以下の質問すべてに、
一人の人物として矛盾しない自然な回答をしてください。

ルール：

・single は choices の中から1つ選ぶ
・multiple は choices の中から1つ以上選ぶ
・text は質問内容に合った短い回答
・text1 は質問内容に合った自然な文章
・選択肢がある場合は必ずその選択肢を使用する
・質問の意味に対応した回答をする
・回答間で人物像が矛盾しないようにする

回答はJSON配列だけを返してください。

形式：

[
  {{
    "id": 質問ID,
    "question": "質問文",
    "answer": 回答
  }}
]

質問：

""" + json.dumps(
        questions,
        ensure_ascii=False,
        indent=2
    )


#
# AIへ直接問い合わせ
#

def call_answer_ai(
    ai,
    theme,
    questions
):

    prompt = make_answer_prompt(
        theme,
        questions
    )

    if ai == "openai":

        url = (
            "https://api.openai.com/"
            "v1/chat/completions"
        )

        key = OKEY

        model = "gpt-4o-mini"

    elif ai == "groq":

        url = (
            "https://api.groq.com/openai/"
            "v1/chat/completions"
        )

        key = GROQKEY

        model = "openai/gpt-oss-20b"

    elif ai == "google":

        return call_google_answer(
            theme,
            questions
        )

    else:

        return None

    headers = {
        "Authorization":
            f"Bearer {key}",
        "Content-Type":
            "application/json"
    }

    data = {
        "model": model,
        "messages": [
            {
                "role": "user",
                "content": prompt
            }
        ],
        "temperature": 0.5
    }

    start = time.time()

    try:

        response = requests.post(
            url,
            headers=headers,
            json=data,
            timeout=120
        )

    except Exception as e:

        print(
            f"{AI_NAMES[ai]} "
            f"回答通信エラー:",
            e
        )

        return None

    elapsed = time.time() - start

    print(
        f"{AI_NAMES[ai]} 回答生成: "
        f"{response.status_code} "
        f"{elapsed:.2f}秒"
    )

    if response.status_code != 200:

        print(
            response.text[:500]
        )

        return None

    try:

        content = (
            response.json()
            ["choices"][0]
            ["message"]
            ["content"]
        )

    except Exception as e:

        print(
            "回答取得エラー:",
            e
        )

        return None

    return parse_answers(
        ai,
        content
    )


#
# Googleによる回答
#

def call_google_answer(
    theme,
    questions
):

    prompt = make_answer_prompt(
        theme,
        questions
    )

    url = (
        "https://generativelanguage.googleapis.com/"
        "v1beta/models/gemini-3.6-flash:"
        "generateContent"
        f"?key={GKEY}"
    )

    data = {
        "contents": [
            {
                "parts": [
                    {
                        "text": prompt
                    }
                ]
            }
        ]
    }

    start = time.time()

    try:

        response = requests.post(
            url,
            json=data,
            timeout=120
        )

    except Exception as e:

        print(
            "Google 回答通信エラー:",
            e
        )

        return None

    elapsed = time.time() - start

    print(
        f"Google 回答生成: "
        f"{response.status_code} "
        f"{elapsed:.2f}秒"
    )

    if response.status_code != 200:

        print(
            response.text[:500]
        )

        return None

    try:

        content = (
            response.json()
            ["candidates"][0]
            ["content"]
            ["parts"][0]
            ["text"]
        )

    except Exception as e:

        print(
            "Google 回答取得エラー:",
            e
        )

        return None

    return parse_answers(
        "google",
        content
    )


#
# 回答JSON解析
#

def parse_answers(
    ai,
    content
):

    if not content:

        return None

    content = content.strip()

    if content.startswith(
        "```"
    ):

        content = content.replace(
            "```json",
            ""
        )

        content = content.replace(
            "```",
            ""
        )

        content = content.strip()

    try:

        answers = json.loads(
            content
        )

    except json.JSONDecodeError as e:

        print(
            f"{AI_NAMES[ai]} "
            f"回答JSON形式違反:",
            e
        )

        print(
            content[:500]
        )

        return None

    if not isinstance(
        answers,
        list
    ):

        print(
            "回答がJSON配列ではありません"
        )

        return None

    return answers


#
# QARを利用して提案生成
#

def get_result(
    ai,
    sample,
    answers
):

    data = {
        "title": "some",
        "answer": {
            "theme":
                sample["theme"],
            "answers":
                answers,
            "sendInstruction":
                sample["result_instruction"],
            "aillm":
                ai
        }
    }

    start = time.time()

    try:

        response = session.post(
            BASE_URL + "/get_result",
            json=data,
            timeout=120
        )

    except Exception as e:

        print(
            "提案生成通信エラー:",
            e
        )

        return False

    elapsed = time.time() - start

    print(
        f"{AI_NAMES[ai]} 提案生成: "
        f"{response.status_code} "
        f"{elapsed:.2f}秒"
    )

    if response.status_code != 200:

        print_error(
            response
        )

        return False

    try:

        result = response.json()

    except Exception:

        print(
            "提案JSON形式違反"
        )

        return False

    if "result" not in result:

        print(
            "result がありません"
        )

        return False

    print()

    for item in result["result"]:

        print(
            "提案:",
            item.get(
                "destination"
            )
        )

        print(
            item.get(
                "description",
                ""
            )
        )

        print()

    return True


#
# エラー表示
#

def print_error(
    response
):

    text = response.text

    print(
        "HTTP:",
        response.status_code
    )

    if (
        "Failed to parse tool call arguments as JSON"
        in text
    ):

        print(
            "AI返信のJSON形式違反"
        )

    elif (
        "Too Many Requests" in text
        or "429" in text
    ):

        print(
            "Too Many Requests"
        )

    else:

        print(
            text[:500]
        )


#
# 1回のランダムテスト
#

def run_test(
    number
):

    sample = random.choice(
        SAMPLES
    )

    question_ai = random.choice(
        AIS
    )

    answer_ai = random.choice(
        AIS
    )

    result_ai = random.choice(
        AIS
    )

    print()
    print(
        "========================================"
    )

    print(
        f"TEST {number}"
    )

    print(
        "テーマ:",
        sample["theme"]
    )

    print(
        "質問:",
        AI_NAMES[question_ai]
    )

    print(
        "回答:",
        AI_NAMES[answer_ai]
    )

    print(
        "提案:",
        AI_NAMES[result_ai]
    )

    print(
        "========================================"
    )

    test_history = {
        "number":
            number,

        "theme":
            sample["theme"],

        "question_ai":
            question_ai,

        "question_ok":
            False,

        "answer_ai":
            answer_ai,

        "answer_ok":
            False,

        "result_ai":
            result_ai,

        "result_ok":
            False
    }

    #
    # 質問
    #

    questions = get_questions(
        question_ai,
        sample
    )

    question_ok = (
        questions is not None
    )

    test_history[
        "question_ok"
    ] = question_ok

    record(
        question_ai,
        "question",
        question_ok
    )

    if not question_ok:

        history.append(
            test_history
        )

        return

    print()

    for q in questions:

        print(
            "Q:",
            q.get("text")
        )

    time.sleep(
        WAIT_TIME
    )

    #
    # 回答
    #

    answers = call_answer_ai(
        answer_ai,
        sample["theme"],
        questions
    )

    answer_ok = (
        answers is not None
    )

    test_history[
        "answer_ok"
    ] = answer_ok

    record(
        answer_ai,
        "answer",
        answer_ok
    )

    if not answer_ok:

        history.append(
            test_history
        )

        return

    print()

    for answer in answers:

        print(
            "Q:",
            answer.get(
                "question"
            )
        )

        print(
            "A:",
            answer.get(
                "answer"
            )
        )

    time.sleep(
        WAIT_TIME
    )

    #
    # 提案
    #

    result_ok = get_result(
        result_ai,
        sample,
        answers
    )

    test_history[
        "result_ok"
    ] = result_ok

    record(
        result_ai,
        "result",
        result_ok
    )

    history.append(
        test_history
    )


#
# 最終リファレンス
#

def print_reference():

    print()
    print()
    print(
        "========================================"
    )

    print(
        "REFERENCE"
    )

    print(
        "========================================"
    )

    print()

    print(
        f"{'AI':<10}"
        f"{'質問作成':<15}"
        f"{'回答':<15}"
        f"{'提案':<15}"
    )

    print(
        "-" * 55
    )

    for ai in AIS:

        values = []

        for process in [
            "question",
            "answer",
            "result"
        ]:

            ok = (
                stats[ai]
                [process]
                ["ok"]
            )

            ng = (
                stats[ai]
                [process]
                ["ng"]
            )

            total = ok + ng

            if total == 0:

                value = "-"

            else:

                value = (
                    f"{ok}/{total} OK"
                )

            values.append(
                value
            )

        print(
            f"{AI_NAMES[ai]:<10}"
            f"{values[0]:<15}"
            f"{values[1]:<15}"
            f"{values[2]:<15}"
        )

    print()
    print(
        "---------- 実行履歴 ----------"
    )

    for item in history:

        print()

        print(
            f"No.{item['number']} "
            f"{item['theme']}"
        )

        print(
            "  質問:",
            f"{AI_NAMES[item['question_ai']]:<8}",
            "OK"
            if item["question_ok"]
            else "NG"
        )

        print(
            "  回答:",
            f"{AI_NAMES[item['answer_ai']]:<8}",
            "OK"
            if item["answer_ok"]
            else "NG"
        )

        #
        # 質問または回答で止まった場合は
        # 提案は未実行
        #

        if (
            not item["question_ok"]
            or not item["answer_ok"]
        ):

            result_text = "未実行"

        else:

            result_text = (
                "OK"
                if item["result_ok"]
                else "NG"
            )

        print(
            "  提案:",
            f"{AI_NAMES[item['result_ai']]:<8}",
            result_text
        )


def main():

    print(
        "=== QAR Random AI Test ==="
    )

    #
    # APIキー確認
    #

    if not OKEY:

        print(
            "OKEY がありません"
        )

        return

    if not GKEY:

        print(
            "GKEY がありません"
        )

        return

    if not GROQKEY:

        print(
            "GROQKEY がありません"
        )

        return

    #
    # QARセッション取得
    #

    try:

        response = session.get(
            BASE_URL + "/",
            timeout=30
        )

    except Exception as e:

        print(
            "QAR接続エラー:",
            e
        )

        return

    if response.status_code != 200:

        print(
            "QARに接続できません:",
            response.status_code
        )

        return

    #
    # 9回実行
    #

    for number in range(
        1,
        TEST_COUNT + 1
    ):

        try:

            run_test(
                number
            )

        except Exception as e:

            print(
                "テスト実行エラー:",
                e
            )

        time.sleep(
            WAIT_TIME
        )

    #
    # 最終結果
    #

    print_reference()


if __name__ == "__main__":
    main()
