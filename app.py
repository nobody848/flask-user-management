import os
import re
import sqlite3
import secrets
import time
from functools import wraps
from flask import Flask, render_template, request, redirect, session, abort
from werkzeug.security import generate_password_hash, check_password_hash

app = Flask(__name__)

# ── 安全配置 ──
app.secret_key = os.environ.get("SECRET_KEY", secrets.token_hex(32))
app.config.update(
    SESSION_COOKIE_HTTPONLY=True,
    SESSION_COOKIE_SAMESITE="Lax",
    SESSION_COOKIE_SECURE=False,          # 本地开发用 False，生产应改为 True (HTTPS)
    PERMANENT_SESSION_LIFETIME=1800,      # 30 分钟过期
    SESSION_REFRESH_EACH_REQUEST=True,
)

# ── 登录频率限制 ──
LOGIN_ATTEMPTS = {}  # IP -> [count, first_attempt_time]
MAX_LOGIN_ATTEMPTS = 5
LOGIN_LOCKOUT_TIME = 300  # 5 分钟


def check_login_rate_limit():
    """检查登录频率，防止暴力破解"""
    ip = request.remote_addr or "unknown"
    now = time.time()
    if ip in LOGIN_ATTEMPTS:
        count, first_attempt = LOGIN_ATTEMPTS[ip]
        if now - first_attempt > LOGIN_LOCKOUT_TIME:
            # 超过锁定时间，重置
            LOGIN_ATTEMPTS[ip] = [1, now]
            return True
        if count >= MAX_LOGIN_ATTEMPTS:
            return False
        LOGIN_ATTEMPTS[ip][0] += 1
    else:
        LOGIN_ATTEMPTS[ip] = [1, now]
    return True


def reset_login_rate_limit():
    """登录成功后重置频率计数"""
    ip = request.remote_addr or "unknown"
    LOGIN_ATTEMPTS.pop(ip, None)


# ── 需要登录的装饰器 ──
def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if "username" not in session:
            return redirect("/login")
        return f(*args, **kwargs)
    return decorated_function


# ── 数据库初始化 ──
def init_db():
    os.makedirs("data", exist_ok=True)
    conn = sqlite3.connect("data/users.db")
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            password TEXT NOT NULL,
            email TEXT,
            phone TEXT,
            role TEXT DEFAULT 'user',
            balance REAL DEFAULT 0,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    # 插入默认用户，密码使用哈希存储
    admin_pw = generate_password_hash("Admin@123!")  # 增强默认密码
    alice_pw = generate_password_hash("alice2025")
    cursor.execute(
        "INSERT OR IGNORE INTO users (username, password, email, phone, role, balance) VALUES (?, ?, ?, ?, ?, ?)",
        ("admin", admin_pw, "admin@example.com", "13800138000", "admin", 99999)
    )
    cursor.execute(
        "INSERT OR IGNORE INTO users (username, password, email, phone, role, balance) VALUES (?, ?, ?, ?, ?, ?)",
        ("alice", alice_pw, "alice@example.com", "13900139001", "user", 100)
    )
    conn.commit()
    conn.close()
    print("[DB] 数据库初始化完成（密码已哈希存储）")


init_db()


def get_user_from_db(username):
    """从数据库获取用户信息"""
    conn = sqlite3.connect("data/users.db")
    cursor = conn.cursor()
    cursor.execute("SELECT username, password, email, phone, role, balance FROM users WHERE username = ?", (username,))
    row = cursor.fetchone()
    conn.close()
    if row:
        return {
            "username": row[0],
            "password": row[1],
            "email": row[2],
            "phone": row[3],
            "role": row[4],
            "balance": row[5],
        }
    return None


def get_safe_user_info(username):
    """返回不包含密码的用户信息（先查数据库，再查内存兼容）"""
    user = get_user_from_db(username)
    if user:
        return {k: v for k, v in user.items() if k != "password"}
    return None


def validate_username(username):
    """用户名验证：只允许字母、数字、下划线，长度 3-32"""
    if not username or len(username) < 3 or len(username) > 32:
        return False
    return bool(re.match(r'^[a-zA-Z0-9_一-龥]{3,32}$', username))


def validate_password(password):
    """密码强度验证：至少8位，包含字母和数字"""
    if not password or len(password) < 8:
        return False
    if not re.search(r'[A-Za-z]', password):
        return False
    if not re.search(r'[0-9]', password):
        return False
    return True


def validate_email(email):
    """邮箱格式验证"""
    if not email:
        return True  # 邮箱可选
    return bool(re.match(r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$', email))


def validate_phone(phone):
    """手机号格式验证"""
    if not phone:
        return True  # 手机号可选
    return bool(re.match(r'^1[3-9]\d{9}$', phone))


# ── 首页 ──
@app.route("/")
def index():
    username = session.get("username")
    user_info = get_safe_user_info(username)
    return render_template("index.html", username=username, user=user_info, search_results=None, search_keyword="")


# ── 登录 ──
@app.route("/login", methods=["GET", "POST"])
def login():
    error = None
    msg = request.args.get("msg", "")

    if request.method == "POST":
        # 检查登录频率限制
        if not check_login_rate_limit():
            error = "登录尝试过于频繁，请5分钟后再试"
            return render_template("login.html", error=error, msg=msg)

        username = request.form.get("username", "").strip()
        password = request.form.get("password", "")

        if not username or not password:
            error = "用户名和密码不能为空"
        else:
            # 从数据库查询用户（支持哈希密码验证）
            user = get_user_from_db(username)
            if user and check_password_hash(user["password"], password):
                session["username"] = username
                session.permanent = True
                reset_login_rate_limit()
                user_info = get_safe_user_info(username)
                return render_template("index.html", username=username, user=user_info, search_results=None, search_keyword="")
            else:
                error = "用户名或密码错误，请重试"

    return render_template("login.html", error=error, msg=msg)


# ── 登出 ──
@app.route("/logout")
def logout():
    session.clear()
    return redirect("/")


# ── CSRF Token 生成 ──
@app.before_request
def generate_csrf_token():
    if "csrf_token" not in session:
        session["csrf_token"] = secrets.token_hex(32)


def get_csrf_token():
    return session.get("csrf_token", "")


@app.context_processor
def inject_csrf_token():
    return dict(csrf_token=get_csrf_token())


# ── 注册 ──
@app.route("/register", methods=["GET", "POST"])
def register():
    error = None

    if request.method == "POST":
        # CSRF 校验
        form_token = request.form.get("csrf_token", "")
        if not form_token or form_token != session.get("csrf_token"):
            error = "表单验证失败，请重试"
            return render_template("register.html", error=error)

        username = request.form.get("username", "").strip()
        password = request.form.get("password", "")
        email = request.form.get("email", "").strip()
        phone = request.form.get("phone", "").strip()

        # 输入验证
        if not validate_username(username):
            error = "用户名格式不正确（3-32位字母、数字、中文或下划线）"
        elif not validate_password(password):
            error = "密码强度不足（至少8位，包含字母和数字）"
        elif not validate_email(email):
            error = "邮箱格式不正确"
        elif not validate_phone(phone):
            error = "手机号格式不正确（11位中国大陆手机号）"
        else:
            # 使用参数化查询防止 SQL 注入，密码哈希存储
            password_hash = generate_password_hash(password)
            try:
                conn = sqlite3.connect("data/users.db")
                cursor = conn.cursor()
                cursor.execute(
                    "INSERT INTO users (username, password, email, phone) VALUES (?, ?, ?, ?)",
                    (username, password_hash, email, phone)
                )
                conn.commit()
                conn.close()
                # 刷新 CSRF Token
                session["csrf_token"] = secrets.token_hex(32)
                return redirect("/login?msg=注册成功，请登录")
            except sqlite3.IntegrityError:
                error = "用户名已存在，请选择其他用户名"
            except Exception as e:
                app.logger.error(f"注册失败: {e}")
                error = "注册失败，请稍后重试"

    return render_template("register.html", error=error)


# ── 搜索（需要登录） ──
@app.route("/search")
@login_required
def search():
    keyword = request.args.get("keyword", "").strip()
    username = session.get("username")
    user_info = get_safe_user_info(username)
    results = []

    if keyword:
        # 使用参数化查询防止 SQL 注入
        like_pattern = f"%{keyword}%"
        print(f"[SQL] SELECT id, username, email, phone FROM users WHERE username LIKE ? OR email LIKE ?  [参数: '{like_pattern}']")
        conn = sqlite3.connect("data/users.db")
        cursor = conn.cursor()
        try:
            cursor.execute(
                "SELECT id, username, email, phone FROM users WHERE username LIKE ? OR email LIKE ?",
                (like_pattern, like_pattern)
            )
            results = cursor.fetchall()
        except Exception as e:
            app.logger.error(f"搜索错误: {e}")
        conn.close()

    return render_template("index.html", username=username, user=user_info, search_results=results, search_keyword=keyword)


# ── 错误处理 ──
@app.errorhandler(404)
def not_found(e):
    return render_template("base.html"), 404


if __name__ == "__main__":
    debug_mode = os.environ.get("FLASK_DEBUG", "0") == "1"
    app.run(debug=debug_mode, host="127.0.0.1", port=5000)
