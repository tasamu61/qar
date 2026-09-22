import functools, logging, datetime, threading, time
from flask import Flask, render_template, request, jsonify, json, Response, session, redirect, send_from_directory
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
import uuid, os, importlib
from framework.aop_session import SessionManager
from texts.pharse import response_json, get_prompt_q

app = Flask(__name__)
app.secret_key = os.getenv("SEED", "3301")

# Session Manager と AOP デコレータ初期化
session_mgr = SessionManager(app=app)
aop = session_mgr.aop_()

@app.route("/")
@session_mgr.limiter.limit("60 per minute", key_func=get_remote_address)
@aop
def index():
    sid = str(uuid.uuid4())
    session["session_id"] = sid
    session_mgr.add_session(sid)
    return render_template("index.html", session_id=sid)

@app.route("/some")
@session_mgr.limiter.limit("60 per minute", key_func=get_remote_address)
@aop
def some():
    sid = str(uuid.uuid4())
    session["session_id"] = sid
    session_mgr.add_session(sid)
    return render_template("some.html", session_id=sid)

@app.route("/get_questions", methods=["POST"])
@session_mgr.limiter.limit("5 per minute")
@aop
def get_questions():
    req_json = request.get_json()
    if not req_json:
        return jsonify({"error": "JSONデータがありません。"}), 400

    # answer オブジェクトがある場合はそこから取得し、なければ直下を見る（後方互換対応）
    answer_data = req_json.get("answer", req_json)

    theme = answer_data.get("theme", "")
    instruction = answer_data.get("sendInstruction", answer_data.get("instruction", ""))
    llm = answer_data.get("aillm", "openai")

    if llm == "self":
        json_str = json.dumps(response_json, ensure_ascii=False, indent=2)
        return Response(json_str, content_type="application/json; charset=utf-8")

    mod = importlib.import_module(f"{llm}_ai")
    prompt = mod.get_prompt_q(theme, get_prompt_q(theme, instruction))
    result = mod.get_result(prompt)
    return jsonify(result)

@app.route("/get_questions_travel", methods=["POST"])
@session_mgr.limiter.limit("5 per minute")
@aop
def get_questions_travel():
    req_json = request.get_json()
    if not req_json:
        return jsonify({"error": "JSONデータがありません。"}), 400

    return Response(json.dumps(response_json, ensure_ascii=False, indent=2),
                    content_type="application/json; charset=utf-8")

@app.route("/get_result", methods=["POST"])
@session_mgr.limiter.limit("5 per minute")
@aop
def get_result():
    data = request.get_json()
    answers = data["answer"]["answers"]
    theme = data["answer"]["theme"]
    sendInstruction = data["answer"]["sendInstruction"]
    title = data.get("title", "")
    if title == "travel":
        theme = "旅行"
        sendInstruction = "回答がない部分について、その点についてもアドバイスしてください"

    llm = data["answer"]["aillm"]
    mod = importlib.import_module(f"{llm}_ai")
    prompt = mod.get_prompt_r(theme, answers, sendInstruction)
    return jsonify(mod.get_result(prompt))

@app.route("/static/doc/2002/<path:filename>")
def serve_2002_file(filename):
    directory = os.path.join(app.root_path, "static/doc/2002")

    # HTML以外（txt, gif, jpg等）は加工せず、そのまま配信する。
    # text/plain なら改行・空白がブラウザ上でも保持され、
    # 画像も正しいContent-Typeで返される。
    if not filename.lower().endswith((".html", ".htm")):
        return send_from_directory(directory, filename)

    filepath = os.path.join(directory, filename)
    with open(filepath, mode='r', encoding='utf-8') as f:
        html = f.read()

    # 2002年版の注記を、元のHTML文書を壊さずbody先頭へ追加する
    notice = "<div style='font-weight:bold; margin:10px 0;'>2002年の過去のシステムの資料です</div>"
    lower_html = html.lower()
    body_pos = lower_html.find('<body')
    if body_pos != -1:
        body_end = html.find('>', body_pos)
        if body_end != -1:
            html = html[:body_end + 1] + notice + html[body_end + 1:]
    else:
        html = notice + html

    return Response(html, content_type="text/html; charset=utf-8")

@app.after_request
def add_image_to_html(response: Response) -> Response:
    if 'text/html' in response.headers.get('Content-Type', '').lower() and response.status_code == 200:
        if request.path.startswith('/static/'):  # static配下は除外
            return response
        try:
            html_content = response.get_data(as_text=True)
            image_tag = """<div style='font-size:smaller;margin:5px 0;'>このシステムの結果は参考程度に、、</div>
            <img src='/static/img/mail.png' style='position: fixed; bottom: 0; right: 0; width: 140px; height: auto; z-index: 1000;'>"""
            if image_tag not in html_content:
                insert_index = html_content.lower().rfind('</body>')
                if insert_index != -1:
                    html_content = html_content[:insert_index] + image_tag + html_content[insert_index:]
                    response.set_data(html_content)
                    response.headers['Content-Length'] = len(response.get_data())
        except UnicodeDecodeError:
            pass  # Shift_JISなどの非UTF-8エンコーディング対応
    return response

if __name__ == '__main__':
    app.run(host="0.0.0.0", port=5001, debug=True, use_reloader=False)
