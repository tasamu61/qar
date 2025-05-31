import openai, time, importlib
from flask import Flask, render_template, request, jsonify, json, Response, session, redirect
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
import uuid, time, threading
import requests, os
import openai_ai, google_ai


app = Flask(__name__)

### 運用関連処理
# シード
seed = os.getenv("SEED", "3301") 
app.secret_key = seed
# セッションごとの制限
def get_session_id():
    return session.get("session_id", get_remote_address())

# 1日400回　分10回のリクエスト制限を設定
limiter = Limiter(get_session_id, app=app, default_limits=["400 per day", "10 per minute"])

# セッションIDリストとタイムスタンプ
issued_sessions = {}
SESSION_TIMEOUT = 600  # 秒（10分）

response_json = {
        "questions": [
            {
                "id": 1,
                "text": "出発地はどちらですか？（日程にあった細かさで）",
                "type": "text",
                "choices": []
            },
            {
                "id": 2,
                "text": "人数は？",
                "type": "single",
                "choices": [
                    "1人", "2人", "3人", "5人", "10人", "10人以上"
                ]
            },
            {
                "id": 3,
                "text": "日程は？",
                "type": "single",
                "choices": ["日帰り", "2日", "3日", "5日", "1週間", "10日", "2週間","3週間", "1月", "数か月", "1年", "1年以上"]
            },
            {
                "id": 4,
                "text": "予算は？（一人あたり）",
                "type": "single",
                "choices": ["1万", "2万", "3万", "5万", "10万", "20万", "30万", "50万", "70万", "100万", "200万", "200万以上"]
            },
            {
                "id": 5,
                "text": "希望・好み（複数選択可）",
                "type": "multiple",
                "choices": ["国内旅行", "海外旅行", "温泉","グルメ","自然体験","アクティビティ","歴史・文化探訪","リラックス・癒し","ショッピング","インスタ映えスポット巡り","ビーチリゾート","山岳観光・登山","都市観光・街歩き","美術館・博物館巡り","世界遺産巡り","テーマパーク・アミューズメント","クルーズ旅行","ドライブ・ロードトリップ","鉄道の旅","パワースポット巡り"]
            },
            {
                "id": 6,
                "text": "希望する内容、国、地域、関連するキーワード（テキスト）",
                "type": "text1",
                "choices": []
            },
                        {
                "id": 7,
                "text": "避けたい事柄",
                "type": "text1",
                "choices": []
            }
        ]
}

# 定期的に古いセッションを削除する関数
def cleanup_sessions():
    while True:
        now = time.time()
        expired = [sid for sid, ts in issued_sessions.items() if now - ts > SESSION_TIMEOUT]
        for sid in expired:
            del issued_sessions[sid]
        time.sleep(60)  # 1分おきにチェック

# バックグラウンドスレッドでクリーンアップ起動
threading.Thread(target=cleanup_sessions, daemon=True).start()

# 初期画面、セッション付与
@app.route("/")
@limiter.limit("100 per minute", key_func=get_remote_address)
def index():
    sid = str(uuid.uuid4())
    session["session_id"] = sid
    issued_sessions[sid] = time.time()
    return render_template("index.html", time=int(time.time()), session_id=sid)

@app.route("/some")
@limiter.limit("100 per minute", key_func=get_remote_address)
def some():
    sid = str(uuid.uuid4())
    session["session_id"] = sid
    issued_sessions[sid] = time.time()
    return render_template("some.html", time=int(time.time()), session_id=sid)



@app.route('/get_questions', methods=['POST'])
@limiter.limit("5 per minute", key_func=get_session_id)
def get_questions():
    req_json = request.get_json()
    if not req_json:
       return jsonify({"error": "JSONデータがありません。"}), 400
    
    theme = req_json.get("theme", "")
    instruction = req_json.get("instruction", "")
    prom = get_prompt_q(theme, instruction)
    
    data = request.get_json()
    llm = req_json.get("aillm", "openai")  # デフォルトはOpenAI
    
    if llm == "self":
        json_str = json.dumps(response_json, ensure_ascii=False, indent=2)
        return Response(json_str, content_type="application/json; charset=utf-8")

    # 他のAIモジュールを動的にインポート
    module_name = llm + "_ai"
    mod = importlib.import_module(module_name)
    
    prom = mod.get_prompt_q(theme, prom)
    result = mod.get_result(prom)
    ret = jsonify(result)

    return ret


@app.route('/get_questions_travel', methods=['POST'])
@limiter.limit("5 per minute", key_func=get_session_id)
def get_questions_travel():
    # sid = session.get("session_id")
    # if not sid or sid not in issued_sessions:
    #    return redirect("/")
    
    req_json = request.get_json()
    if not req_json:
       return jsonify({"error": "JSONデータがありません。"}), 400
    
    title = req_json.get("title", "")
    questions_input = req_json.get("questions", [])

    json_str = json.dumps(response_json, ensure_ascii=False, indent=2)
    return Response(json_str, content_type="application/json; charset=utf-8")



@app.route("/get_result", methods=["POST"])
@limiter.limit("5 per minute", key_func=get_session_id)
def get_result():
    # sid = session.get("session_id")
    # if not sid or sid not in issued_sessions:
    #     return redirect("/")
    data = request.get_json()
    answers = data["answer"]["answers"]
    theme =data["answer"]["theme"]
    llm = data["answer"]["aillm"]
    
    module_name = llm + "_ai"
    mod = importlib.import_module(module_name)

    # 関数を呼び出す
    prompt = mod.get_prompt_r( theme, answers)
    answer = mod.get_result(prompt)

    print(f"[{module_name}] prompt =>", prompt)
    print(f"[{module_name}] getAnswer =>", answer)

    ret = jsonify(answer)

    return ret

@app.errorhandler(429)
@limiter.limit("5 per minute")
def ratelimit_handler(e):
    return jsonify({"error": "リクエストが多すぎます。しばらく待ってから再試行してください。"}), 429

def get_prompt_q( theme, instructions):
    """
    質問のプロンプトを生成する関数
    """
    prompt = f"""
        あなたは{theme}に関するアドバイザーです。
        利用者に質問してその回答より利用者に最適な{theme}をアドバイスするための
        質問を考えてください。
        {instructions}
        出力はJSON形式のみで機械処理するので、余計な解説文・前置き・マークダウンは
        含めないでください。
        以下形式で７つの質問を生成してください。
        質問は下記の形式で作成してください。

        {{
  "id": 1,
  "text": "質問文",
  "type": "single",         // 単選択
  "choices": ["選択肢A", "選択肢B"] // 単選択・複数選択の場合のみ
}}
{{
  "id": 2,
  "text": "質問文",
  "type": "multiple",       // 複数選択
  "choices": ["選択肢A", "選択肢B"]
}}
{{
  "id": 3,
  "text": "質問文",
  "type": "text",           // 20文字以内の単語
  "maxLength": 40
}}
{{
  "id": 4,
  "text": "質問文",
  "type": "text1",           // 50文字以内のテキスト
  "maxLength": 100
}}
        返信は、コードはUTF-8でおねがいします。"""
    
    return prompt

if __name__ == '__main__':
    app.run(host="0.0.0.0", port=5001, debug=True)