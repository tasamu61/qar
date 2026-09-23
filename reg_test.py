import requests
import sys
import time

BASE_URL = "http://127.0.0.1:5001"

LLMS = [
    "openai",
    "google",
    "groq"
]

WAIT_TIME = 5

session = requests.Session()


def post_with_retry(url, data):

    for retry in range(3):

        response = session.post(
            url,
            json=data,
            timeout=120
        )

        # 通常の応答なら終了
        if response.status_code != 429:
            time.sleep(WAIT_TIME)
            return response

        # 429の場合は待って再試行
        wait = 10 * (retry + 1)

        print(
            f"Too Many Requests - {wait}秒待機して再試行"
        )

        time.sleep(wait)

    return response


def get_questions(llm):

    data = {
        "title": "some",
        "theme": "旅行",
        "instruction": "自分に合った旅行先を提案するための質問",
        "sendInstruction": "",
        "userAdvice": "",
        "aillm": llm
    }

    start = time.time()

    response = post_with_retry(
        BASE_URL + "/get_questions",
        data
    )

    elapsed = time.time() - start

    print(
        f"get_questions: {response.status_code} "
        f"{elapsed:.2f}秒"
    )

    if response.status_code != 200:

        print_error(response)

        return None

    try:
        result = response.json()

    except Exception:
        print("形式違反: JSONとして解析できません")
        return None

    questions = result.get("questions")

    if not questions:
        print("形式違反: questions がありません")
        print(result)
        return None

    print("質問数:", len(questions))

    for q in questions:

        print(
            q.get("id"),
            q.get("type"),
            q.get("text")
        )

    return questions


def make_answers(questions, pattern):

    answers = []

    for q in questions:

        qid = q.get("id")
        text = q.get("text")
        qtype = q.get("type")
        choices = q.get("choices", [])

        if qtype == "single":

            if not choices:
                print(
                    "形式違反: singleなのにchoicesがありません"
                )
                return None

            index = min(
                pattern,
                len(choices) - 1
            )

            answer = choices[index]

        elif qtype == "multiple":

            if not choices:
                print(
                    "形式違反: multipleなのにchoicesがありません"
                )
                return None

            if pattern == 0:
                answer = choices[:1]

            elif pattern == 1:
                answer = choices[:2]

            else:
                answer = choices[-2:]

        elif qtype in [
            "text",
            "text1"
        ]:

            # 質問内容によって回答を変える
            if (
                "出発" in text
                or "住んで" in text
                or "居住" in text
            ):

                text_answers = [
                    "横浜",
                    "大阪",
                    "札幌"
                ]

            elif (
                "予算" in text
                or "費用" in text
            ):

                text_answers = [
                    "5万円",
                    "10万円",
                    "20万円"
                ]

            elif (
                "日数" in text
                or "期間" in text
            ):

                text_answers = [
                    "3日",
                    "5日",
                    "7日"
                ]

            elif (
                "時期" in text
                or "季節" in text
            ):

                text_answers = [
                    "春",
                    "夏",
                    "秋"
                ]

            else:

                text_answers = [
                    "自然を楽しみたい",
                    "温泉と食事を楽しみたい",
                    "海でのんびり過ごしたい"
                ]

            answer = text_answers[pattern]

        else:

            print(
                "形式違反: 不明なtype:",
                qtype
            )

            return None

        answers.append({
            "id": qid,
            "question": text,
            "answer": answer
        })

    return answers


def print_error(response):

    print(
        f"形式違反またはAPIエラー: "
        f"HTTP {response.status_code}"
    )

    text = response.text

    if (
        "Failed to parse tool call arguments as JSON"
        in text
    ):

        print(
            "内容: AI返信のTool Call JSON形式違反"
        )

    elif (
        "Too Many Requests" in text
        or "429" in text
    ):

        print(
            "内容: Too Many Requests"
        )

    else:

        # Werkzeugの巨大なHTMLなどを
        # 全部コンソールへ出さない
        text = text.replace(
            "\n",
            " "
        )

        print(
            "内容:",
            text[:300]
        )


def test_result(llm, answers):

    data = {
        "title": "some",
        "answer": {
            "theme": "旅行",
            "answers": answers,
            "sendInstruction": "",
            "aillm": llm
        }
    }

    start = time.time()

    response = post_with_retry(
        BASE_URL + "/get_result",
        data
    )

    elapsed = time.time() - start

    print(
        f"get_result: {response.status_code} "
        f"{elapsed:.2f}秒"
    )

    if response.status_code != 200:

        print_error(response)

        return False

    try:
        result = response.json()

    except Exception:

        print(
            "形式違反: JSONとして解析できません"
        )

        return False

    if "result" not in result:

        print(
            "形式違反: result がありません"
        )

        print(result)

        return False

    print(
        "提案数:",
        len(result["result"])
    )

    for r in result["result"]:

        print(
            "-",
            r.get("destination"),
            r.get(
                "description",
                ""
            )[:60]
        )

    return True


def test_llm(llm):

    print()
    print(
        "========================================"
    )
    print(
        "LLM:",
        llm
    )
    print(
        "========================================"
    )

    try:

        questions = get_questions(llm)

    except Exception as e:

        print(
            "質問生成でエラー:",
            e
        )

        print(
            "RESULT:",
            llm,
            "NG"
        )

        return False

    if not questions:

        print(
            "RESULT:",
            llm,
            "NG"
        )

        return False

    all_ok = True

    for pattern in range(3):

        print()
        print(
            "----------------------------------------"
        )
        print(
            "回答パターン:",
            pattern + 1
        )
        print(
            "----------------------------------------"
        )

        try:

            answers = make_answers(
                questions,
                pattern
            )

            if not answers:

                print(
                    "回答生成: NG"
                )

                all_ok = False

                continue

            for a in answers:

                print(
                    "Q:",
                    a["question"]
                )

                print(
                    "A:",
                    a["answer"]
                )

            print()

            if not test_result(
                llm,
                answers
            ):

                all_ok = False

                # エラーでも次のパターンへ進む
                continue

        except Exception as e:

            print(
                "このパターンでエラー:",
                e
            )

            all_ok = False

            # エラーでも次のパターンへ進む
            continue

    print()

    print(
        "RESULT:",
        llm,
        "OK" if all_ok else "NG"
    )

    return all_ok


def main():

    print(
        "=== QAR Regression Test ==="
    )

    # トップページへアクセスして
    # セッションCookieを取得
    response = session.get(
        BASE_URL + "/",
        timeout=30
    )

    print(
        "トップページ:",
        response.status_code
    )

    if response.status_code != 200:

        print(
            "NG: トップページにアクセスできません"
        )

        print(
            response.text
        )

        sys.exit(1)

    total_ok = True

    for llm in LLMS:

        try:

            if not test_llm(llm):
                total_ok = False

        except Exception as e:

            print()
            print(
                "LLM全体でエラー:",
                llm
            )

            print(e)

            total_ok = False

            # 次のAIへ進む
            continue

    print()
    print(
        "========================================"
    )

    if total_ok:

        print(
            "ALL RESULT: OK"
        )

    else:

        print(
            "ALL RESULT: NG"
        )

    print(
        "========================================"
    )

    if not total_ok:
        sys.exit(1)


if __name__ == "__main__":
    main()
	