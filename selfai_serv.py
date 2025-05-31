from flask import Flask, request, jsonify, json, Response

app = Flask(__name__)

@app.route("/get_questions", methods=["POST"])
def get_questions():
    # 受信したJSONを確認（任意）
    req_json = request.get_json()
    # print("Received JSON:", json.dumps(req_json, ensure_ascii=False, indent=2))
    print(json.dumps(req_json, indent=2, ensure_ascii=False))  #

    # 固定の質問リストを返す
    response_json = {
        "questions": [
            {
                "id": 1,
                "text": "出発地はどちらですか？",
                "type": "text",
                "choices": []
            },
            {
                "id": 2,
                "text": "誰と行きますか？",
                "type": "single",
                "choices": ["一人", "二人", "5人以下", "10人以下"]
            },
            {
                "id": 3,
                "text": "日程は？",
                "type": "single",
                "choices": ["日帰り", "３日ぐらい", "５日ぐらい", "１週間ぐらい"]
            },
            {
                "id": 4,
                "text": "予算は？（一人あたり）",
                "type": "single",
                "choices": ["２万以下", "５万以下", "１０万以下", "２０万以下"]
            },
            {
                "id": 5,
                "text": "希望・好み（複数選択可）",
                "type": "multiple",
                "choices": ["国内旅行", "海外旅行", "自然", "温泉", "グルメ", "歴史・文化", "アクティビティ", "のんびり", "買い物", "子連れ向け"]
            }
        ]
    }
    json_str = json.dumps(response_json, ensure_ascii=False, indent=2)
    return Response(json_str, content_type="application/json; charset=utf-8")


@app.route('/get_result', methods=['POST'])
def get_result():
    req_json = request.get_json()
    # print("Received JSON:", json.dumps(req_json, ensure_ascii=False, indent=2))
    print(json.dumps(req_json, indent=2, ensure_ascii=False))  #

        
    response_json = {
        "result": [
            {
                "destination": "京都",
                "score": 95,
                "description": "伝統と歴史が息づく町並み。寺社や和の文化に触れたい方に最適です。",
                "url": "https://www.kyoto.travel/"
            },
            {
                "destination": "沖縄",
                "score": 88,
                "description": "透明な海と亜熱帯の自然、独自の食文化が魅力。リゾート気分を満喫したい方に。",
                "url": "https://www.okinawastory.jp/"
            },
            {
                "destination": "北海道",
                "score": 82,
                "description": "四季折々の美しい風景と海の幸。広大な自然とグルメを楽しみたい方におすすめ。",
                "url": "https://www.visit-hokkaido.jp/"
            }
        ]
    }

    json_str = json.dumps(response_json, ensure_ascii=False, indent=2)
    print(json_str)  #
    return Response(json_str, content_type="application/json; charset=utf-8")



if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8000, debug=True)
