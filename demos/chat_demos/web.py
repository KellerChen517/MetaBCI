import json
import multiprocessing as mp
import os
import urllib.error
import urllib.request

from flask import Flask, flash, jsonify, redirect, render_template, request, session, url_for
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import check_password_hash, generate_password_hash

from collector import collecting_all_info


def _extract_zhipu_reply(body):
    """Best-effort parse for multiple Zhipu response schemas."""
    if isinstance(body, dict):
        if body.get("choices"):
            content = body["choices"][0].get("message", {}).get("content")
            if content:
                return content.strip()

        if isinstance(body.get("output"), dict):
            out = body["output"]
            if out.get("text"):
                return str(out["text"]).strip()

        if body.get("reply"):
            return str(body["reply"]).strip()

        if body.get("data") and isinstance(body["data"], dict):
            data = body["data"]
            if data.get("reply"):
                return str(data["reply"]).strip()

    raise RuntimeError(f"智谱接口返回格式异常: {body}")


def call_ai_model(messages):
    """Call Zhipu assistant API (not OpenAI mode).

    Configure with env vars:
    - ZHIPU_API_KEY
    - ZHIPU_ASSISTANT_ID
    - ZHIPU_API_BASE (default: https://open.bigmodel.cn/api/paas/v4)
    """
    api_base = os.getenv("ZHIPU_API_BASE", "https://open.bigmodel.cn/api/paas/v4").rstrip("/")
    api_key = os.getenv("ZHIPU_API_KEY", "")
    assistant_id = os.getenv("ZHIPU_ASSISTANT_ID", "")

    latest_user = next((m["content"] for m in reversed(messages) if m.get("role") == "user"), "")
    system_text = next((m["content"] for m in messages if m.get("role") == "system"), "")
    merged_user_text = f"{system_text}\n\n用户提问：{latest_user}".strip()
    if not api_key or not assistant_id:
        return (
            "[本地演示模式] 我收到了你的消息："
            f"{latest_user}。\n请配置 ZHIPU_API_KEY 和 ZHIPU_ASSISTANT_ID 以启用智谱智能体对话。"
        )

    payload = {
        "assistant_id": assistant_id,
        "messages": [{"role": "user", "content": merged_user_text}],
    }
    data = json.dumps(payload).encode("utf-8")
    req = urllib.request.Request(
        f"{api_base}/assistant",
        data=data,
        headers={
            "Content-Type": "application/json",
            "Authorization": f"Bearer {api_key}",
        },
        method="POST",
    )

    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            body = json.loads(resp.read().decode("utf-8"))
    except urllib.error.HTTPError as e:
        detail = e.read().decode("utf-8", errors="ignore")
        raise RuntimeError(f"AI接口错误: {e.code} {detail}") from e
    except urllib.error.URLError as e:
        raise RuntimeError(f"无法连接AI接口: {e}") from e

    return _extract_zhipu_reply(body)


def web_server():
    app = Flask(__name__)
    app.secret_key = os.getenv("FLASK_SECRET_KEY", "your_secret_key")
    app.config["SECRET_KEY"] = app.secret_key
    app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///users.db"
    app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
    db = SQLAlchemy(app)

    class User(db.Model):
        id = db.Column(db.Integer, primary_key=True)
        username = db.Column(db.String(80), unique=True, nullable=False)
        password = db.Column(db.String(120), nullable=False)
        user_hobby = db.Column(db.String(200))

    class Current(db.Model):
        id = db.Column(db.Integer, primary_key=True)
        name = db.Column(db.String(80), unique=False, nullable=False)
        info = db.Column(db.String(200), unique=False, nullable=False)

    with app.app_context():
        db.create_all()

    def get_current_profile():
        row = Current.query.first()
        if row:
            return row.name, row.info
        return session.get("username", "user"), ""

    @app.route('/register', methods=['GET', 'POST'])
    def register():
        if request.method == 'POST':
            username = request.form['username']
            password = request.form['password']
            info = request.form['info']
            hashed_password = generate_password_hash(password, method="scrypt")
            try:
                new_user = User(username=username, password=hashed_password, user_hobby=info)
                db.session.add(new_user)
                if Current.query.first() is None:
                    db.session.add(Current(name="dummy", info="dummy info"))
                db.session.commit()
            except Exception as e:
                print("create user failed", e)
                flash('username occupied!', 'error')
                return render_template('register.html')

            flash('Registration successful. Please login.', 'success')
            return redirect(url_for('login'))
        return render_template('register.html')

    @app.route('/login', methods=['GET', 'POST'])
    def login():
        if request.method == 'POST':
            username = request.form['username']
            password = request.form['password']

            user = User.query.filter_by(username=username).first()
            if user and check_password_hash(user.password, password):
                flash('Login successful.', 'success')
                session['username'] = username

                first_row = Current.query.first()
                if first_row is None:
                    first_row = Current(name=user.username, info=user.user_hobby or "")
                    db.session.add(first_row)
                else:
                    first_row.name = user.username
                    first_row.info = user.user_hobby or ""
                db.session.commit()

                if os.getenv("ENABLE_EMOTION_COLLECTOR", "1") == "1":
                    process = mp.Process(target=collecting_all_info, args=(username, user.user_hobby or ""))
                    process.daemon = True
                    process.start()

                return redirect(url_for('chat'))
            flash('Invalid username or password.', 'danger')
        return render_template('login.html')

    @app.route('/')
    def index():
        if 'username' in session:
            return redirect(url_for('chat'))
        return redirect(url_for('login'))

    @app.route('/chat')
    def chat():
        if 'username' not in session:
            return redirect(url_for('login'))
        return render_template('chat.html', username=session['username'])

    @app.route('/api/profile')
    def api_profile():
        if 'username' not in session:
            return jsonify({"error": "unauthorized"}), 401
        name, info = get_current_profile()
        return jsonify({"name": name, "info": info})

    @app.route('/api/chat', methods=['POST'])
    def api_chat():
        if 'username' not in session:
            return jsonify({"error": "unauthorized"}), 401

        content = (request.json or {}).get("message", "").strip()
        if not content:
            return jsonify({"error": "message is required"}), 400

        _, info = get_current_profile()
        system_prompt = (
            "你是一个温和、简洁的心理支持聊天助手。"
            "请根据用户当前信息提供支持性对话，不要输出医学诊断。"
            f"用户画像（可能含情绪）: {info}"
        )
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": content},
        ]

        try:
            answer = call_ai_model(messages)
        except Exception as e:
            return jsonify({"error": str(e)}), 500

        return jsonify({"reply": answer})

    @app.route('/logout')
    def logout():
        session.pop('username', None)
        return redirect(url_for('login'))

    app.run(host="0.0.0.0", port=5000)


if __name__ == '__main__':
    web_server()
