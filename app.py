import os
from flask import Flask, render_template, request, redirect, session
from werkzeug.security import generate_password_hash, check_password_hash

app = Flask(__name__)
app.secret_key = os.environ.get("SECRET_KEY", os.urandom(24).hex())

# 用户数据库 - 密码使用哈希存储
USERS = {
    "admin": {
        "username": "admin",
        "password": generate_password_hash("admin123"),
        "role": "admin",
        "email": "admin@example.com",
        "phone": "13800138000",
        "balance": 99999
    },
    "alice": {
        "username": "alice",
        "password": generate_password_hash("alice2025"),
        "role": "user",
        "email": "alice@example.com",
        "phone": "13900139001",
        "balance": 100
    }
}


def get_safe_user_info(username):
    """返回不包含密码的用户信息"""
    if username in USERS:
        user = USERS[username]
        return {k: v for k, v in user.items() if k != "password"}
    return None


@app.route("/")
def index():
    username = session.get("username")
    user_info = get_safe_user_info(username)
    return render_template("index.html", username=username, user=user_info)


@app.route("/login", methods=["GET", "POST"])
def login():
    error = None

    if request.method == "POST":
        username = request.form.get("username", "")
        password = request.form.get("password", "")

        if username in USERS and check_password_hash(USERS[username]["password"], password):
            session["username"] = username
            session.permanent = True
            user_info = get_safe_user_info(username)
            return render_template("index.html", username=username, user=user_info)
        else:
            error = "用户名或密码错误，请重试"

    return render_template("login.html", error=error)


@app.route("/logout")
def logout():
    session.clear()
    return redirect("/")


if __name__ == "__main__":
    debug_mode = os.environ.get("FLASK_DEBUG", "0") == "1"
    app.run(debug=debug_mode, host="127.0.0.1", port=5000)
