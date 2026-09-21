import functools, logging, datetime, threading, time
from flask import request, Response, redirect, session, jsonify
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address

class SessionManager:
    def __init__(self, app=None, timeout=3600):
        self.timeout = timeout
        self.issued_sessions = {}
        self.valid_sessions = set()
        self._start_cleanup_thread()

        self.get_session_id = lambda: session.get("session_id", get_remote_address())
        if app:
            self.limiter = Limiter(self.get_session_id, app=app, default_limits=["400 per day", "10 per minute"])
        else:
            self.limiter = None

        logging.basicConfig(level=logging.DEBUG, format="%(asctime)s - %(levelname)s - %(message)s")

    def _start_cleanup_thread(self):
        thread = threading.Thread(target=self._cleanup_sessions, daemon=True)
        thread.start()

    def _cleanup_sessions(self):
        while True:
            now = time.time()
            expired = [sid for sid, ts in self.issued_sessions.items() if now - ts > self.timeout]
            for sid in expired:
                del self.issued_sessions[sid]
                self.valid_sessions.discard(sid)
                logging.info(f"セッション {sid} が削除されました。")
            time.sleep(60)

    def add_session(self, sid):
        self.valid_sessions.add(sid)
        self.issued_sessions[sid] = time.time()

    def get_valid_sessions(self):
        return self.valid_sessions

    def get_issued_sessions(self):
        return self.issued_sessions

    def is_valid(self, session_id):
        return 0 if session_id and session_id != "invalid" and session_id in self.valid_sessions else 1

    def aop_(self):
        def decorator(func):
            @functools.wraps(func)
            def wrapper(*args, **kwargs):
                timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S.%f")[:-3]
                remote_ip = request.remote_addr
                remote_port = request.environ.get("REMOTE_PORT", "-")
                session_id = session.get("session_id", "0")
                session_validation = self.is_valid(session_id)
                request_content = request.get_json() if request.is_json else request.url
                logging.info(f"B {remote_ip} {remote_port} {session_id} {session_validation} {request_content}")
                if request.is_json and session_validation == 1:
                    return jsonify({
                        "error": "セッションが無効です。トップページから再度アクセスしてください。",
                        "retry_after": 10
                    }), 403
                response = func(*args, **kwargs)
                status_code = response.status_code if isinstance(response, Response) else "-"
                response_size = len(response.data) if isinstance(response, Response) else "-"
                timestamp_after = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S.%f")[:-3]
                logging.info(f"A {remote_ip} {remote_port} {status_code} {response_size}")
                return response
            return wrapper
        return decorator
