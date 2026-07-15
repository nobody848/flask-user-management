import os
import re
import sqlite3
import secrets
import time
import urllib.request
import urllib.error
import socket
from functools import wraps
from flask import Flask, render_template, request, redirect, session, abort, url_for
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
    MAX_CONTENT_LENGTH=16 * 1024 * 1024,  # 最大上传 16MB
)

# ── 登录频率限制 ──
LOGIN_ATTEMPTS = {}  # IP -> [count, first_attempt_time]
REGISTER_ATTEMPTS = {}  # IP -> [count, first_attempt_time]
PAGE_ATTEMPTS = {}  # IP -> [count, first_attempt_time]
RECHARGE_ATTEMPTS = {}  # IP -> [count, first_attempt_time]
MAX_LOGIN_ATTEMPTS = 5
MAX_REGISTER_ATTEMPTS = 3
MAX_PAGE_ATTEMPTS = 30
MAX_RECHARGE_ATTEMPTS = 5
LOGIN_LOCKOUT_TIME = 300  # 5 分钟
REGISTER_LOCKOUT_TIME = 600  # 10 分钟
PAGE_LOCKOUT_TIME = 60  # 1 分钟
RECHARGE_LOCKOUT_TIME = 60  # 1 分钟


def check_login_rate_limit():
    """检查登录频率，防止暴力破解"""
    return _check_rate_limit(LOGIN_ATTEMPTS, MAX_LOGIN_ATTEMPTS, LOGIN_LOCKOUT_TIME, "login")


def check_register_rate_limit():
    """检查注册频率，防止批量注册"""
    return _check_rate_limit(REGISTER_ATTEMPTS, MAX_REGISTER_ATTEMPTS, REGISTER_LOCKOUT_TIME, "register")


def check_page_rate_limit():
    """检查页面加载频率"""
    return _check_rate_limit(PAGE_ATTEMPTS, MAX_PAGE_ATTEMPTS, PAGE_LOCKOUT_TIME, "page")


def check_recharge_rate_limit():
    """检查充值频率"""
    return _check_rate_limit(RECHARGE_ATTEMPTS, MAX_RECHARGE_ATTEMPTS, RECHARGE_LOCKOUT_TIME, "recharge")


def _check_rate_limit(attempts_dict, max_attempts, lockout_time, label):
    """通用频率检查"""
    ip = request.remote_addr or "unknown"
    now = time.time()
    if ip in attempts_dict:
        count, first_attempt = attempts_dict[ip]
        if now - first_attempt > lockout_time:
            attempts_dict[ip] = [1, now]
            return True
        if count >= max_attempts:
            return False
        attempts_dict[ip][0] += 1
    else:
        attempts_dict[ip] = [1, now]
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
    conn = None
    try:
        conn = sqlite3.connect("data/users.db")
        cursor = conn.cursor()
        cursor.execute("SELECT username, password, email, phone, role, balance FROM users WHERE username = ?", (username,))
        row = cursor.fetchone()
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
    finally:
        if conn:
            conn.close()


def get_safe_user_info(username):
    """返回不包含密码的用户信息（先查数据库，再查内存兼容）"""
    user = get_user_from_db(username)
    if user:
        return {k: v for k, v in user.items() if k != "password"}
    return None


def get_user_by_id(user_id):
    """根据 user_id 获取用户信息（不含密码）"""
    try:
        user_id = int(user_id)
    except (ValueError, TypeError):
        return None
    conn = None
    try:
        conn = sqlite3.connect("data/users.db")
        cursor = conn.cursor()
        cursor.execute("SELECT id, username, email, phone, role, balance FROM users WHERE id = ?", (user_id,))
        row = cursor.fetchone()
        if row:
            return {
                "id": row[0],
                "username": row[1],
                "email": row[2],
                "phone": row[3],
                "role": row[4],
                "balance": row[5],
            }
        return None
    finally:
        if conn:
            conn.close()


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
    return render_template("index.html", username=username, user=user_info, search_results=None, search_keyword="", page_content=None, fetch_result=None, fetch_url="")


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

        # CSRF 校验
        form_token = request.form.get("csrf_token", "")
        if not form_token or form_token != session.get("csrf_token"):
            error = "表单验证失败，请重试"
            return render_template("login.html", error=error, msg=msg)

        username = request.form.get("username", "").strip()
        password = request.form.get("password", "")

        if not username or not password:
            error = "用户名和密码不能为空"
        else:
            # 从数据库查询用户（支持哈希密码验证）
            user = get_user_from_db(username)
            if user and check_password_hash(user["password"], password):
                # 重置 session 防止会话固定攻击
                session.clear()
                session["username"] = username
                session.permanent = True
                session["csrf_token"] = secrets.token_hex(32)
                reset_login_rate_limit()
                user_info = get_safe_user_info(username)
                return render_template("index.html", username=username, user=user_info, search_results=None, search_keyword="", page_content=None, fetch_result=None, fetch_url="")
            else:
                error = "用户名或密码错误，请重试"

    return render_template("login.html", error=error, msg=msg)


# ── 登出 ──
@app.route("/logout")
def logout():
    session.clear()
    # 生成新 CSRF Token 防止会话重用
    session["csrf_token"] = secrets.token_hex(32)
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


# ── 安全响应头 ──
@app.after_request
def add_security_headers(response):
    """添加安全响应头"""
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "DENY"
    response.headers["X-XSS-Protection"] = "1; mode=block"
    csp = (
        "default-src 'self'; "
        "script-src 'self' 'unsafe-inline'; "
        "style-src 'self' 'unsafe-inline'; "
        "img-src 'self' data:; "
        "font-src 'self'; "
        "form-action 'self'"
    )
    response.headers["Content-Security-Policy"] = csp
    return response


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

        # 检查注册频率限制
        if not check_register_rate_limit():
            error = "注册尝试过于频繁，请稍后再试"
            return render_template("register.html", error=error)

        username = request.form.get("username", "").strip()[:32]
        password = request.form.get("password", "")[:128]
        email = request.form.get("email", "").strip()[:254]
        phone = request.form.get("phone", "").strip()[:20]

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
            conn = None
            try:
                conn = sqlite3.connect("data/users.db")
                cursor = conn.cursor()
                cursor.execute(
                    "INSERT INTO users (username, password, email, phone) VALUES (?, ?, ?, ?)",
                    (username, password_hash, email, phone)
                )
                conn.commit()
                # 刷新 CSRF Token
                session["csrf_token"] = secrets.token_hex(32)
                return redirect("/login?msg=注册成功，请登录")
            except sqlite3.IntegrityError:
                error = "注册失败，用户名可能已存在，请尝试其他用户名"
            except Exception as e:
                app.logger.error(f"注册失败: {e}")
                error = "注册失败，请稍后重试"
            finally:
                if conn:
                    conn.close()

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
        conn = None
        try:
            conn = sqlite3.connect("data/users.db")
            cursor = conn.cursor()
            cursor.execute(
                "SELECT id, username, email, phone FROM users WHERE username LIKE ? OR email LIKE ?",
                (like_pattern, like_pattern)
            )
            results = cursor.fetchall()
        except Exception as e:
            app.logger.error(f"搜索错误: {e}")
        finally:
            if conn:
                conn.close()

    return render_template("index.html", username=username, user=user_info, search_results=results, search_keyword=keyword, page_content=None, fetch_result=None, fetch_url="")


# ── 上传头像（需要登录）──
UPLOAD_FOLDER = os.path.join("static", "uploads")


def safe_filename(filename):
    """移除路径遍历字符，保留原始文件名"""
    # 只保留文件名部分，去除目录路径
    filename = os.path.basename(filename)
    # 移除空字符和路径分隔符
    filename = filename.replace("\x00", "").replace("\x00", "")
    if not filename:
        filename = "unnamed"
    return filename


@app.route("/upload", methods=["GET", "POST"])
@login_required
def upload():
    error = None
    success = None
    file_url = None
    filename = None

    if request.method == "POST":
        # CSRF 校验
        form_token = request.form.get("csrf_token", "")
        if not form_token or form_token != session.get("csrf_token"):
            error = "表单验证失败，请重试"
            return render_template("upload.html", error=error, success=success, file_url=file_url, filename=filename)

        if "upload_file" not in request.files:
            error = "没有选择文件"
        else:
            file = request.files["upload_file"]
            if file.filename == "":
                error = "没有选择文件"
            else:
                # 使用用户子目录隔离不同用户的上传文件
                username = session.get("username", "anonymous")
                user_upload_dir = os.path.join(UPLOAD_FOLDER, username)
                os.makedirs(user_upload_dir, exist_ok=True)
                # 移除路径遍历字符，保留原始文件名
                original_name = safe_filename(file.filename)
                save_path = os.path.join(user_upload_dir, original_name)
                file.save(save_path)
                file_url = url_for("static", filename=f"uploads/{username}/{original_name}")
                filename = original_name
                success = "文件上传成功！"

    return render_template("upload.html", error=error, success=success, file_url=file_url, filename=filename)


# ── 个人中心（需要登录）──
@app.route("/profile")
@login_required
def profile():
    user_id = request.args.get("user_id", "")
    user_info = get_user_by_id(user_id)

    if user_info is None:
        return render_template("profile.html", user=None, error="未找到该用户")

    return render_template("profile.html", user=user_info, error=None)


# ── 充值（需要登录）──
@app.route("/recharge", methods=["POST"])
@login_required
def recharge():
    # CSRF 校验
    form_token = request.form.get("csrf_token", "")
    if not form_token or form_token != session.get("csrf_token"):
        return redirect("/profile?user_id=1")

    # 检查充值频率
    if not check_recharge_rate_limit():
        return redirect("/profile?user_id=1")

    user_id = request.form.get("user_id", "")
    amount = request.form.get("amount", "0")

    try:
        amount = float(amount)
        user_id_int = int(user_id)
    except (ValueError, TypeError):
        return redirect(f"/profile?user_id={user_id}")

    conn = None
    try:
        conn = sqlite3.connect("data/users.db")
        cursor = conn.cursor()
        cursor.execute("UPDATE users SET balance = balance + ? WHERE id = ?", (amount, user_id_int))
        conn.commit()
    finally:
        if conn:
            conn.close()

    return redirect(f"/profile?user_id={user_id}")


# ── 修改密码（需要登录）──
@app.route("/change-password", methods=["POST"])
@login_required
def change_password():
    username = request.form.get("username", "")
    new_password = request.form.get("new_password", "")

    if username and new_password:
        password_hash = generate_password_hash(new_password)
        conn = None
        try:
            conn = sqlite3.connect("data/users.db")
            cursor = conn.cursor()
            cursor.execute("UPDATE users SET password = ? WHERE username = ?", (password_hash, username))
            conn.commit()
        finally:
            if conn:
                conn.close()

    return redirect("/profile")


# ── URL 抓取（需要登录）──
def is_internal_ip(host):
    """检查目标 IP 是否为内网地址"""
    try:
        ip = socket.gethostbyname(host)
        parts = ip.split(".")
        if parts[0] == "127":
            return True
        if parts[0] == "10":
            return True
        if parts[0] == "0":
            return True
        if parts[0] == "169" and parts[1] == "254":
            return True
        if parts[0] == "192" and parts[1] == "168":
            return True
        if parts[0] == "172" and 16 <= int(parts[1]) <= 31:
            return True
        if host.lower() == "localhost":
            return True
        return False
    except Exception:
        return True


def validate_url_protocol(url):
    """验证 URL 协议只允许 http/https"""
    if not url.startswith("http://") and not url.startswith("https://"):
        return False
    if url.startswith("http://localhost") or url.startswith("https://localhost"):
        return False
    return True


@app.route("/fetch-url", methods=["POST"])
@login_required
def fetch_url():
    url = request.form.get("url", "")
    fetch_result = None
    username = session.get("username")
    user_info = get_safe_user_info(username)

    if url:
        # SSRF 防护：检查协议
        if not validate_url_protocol(url):
            fetch_result = {
                "url": url,
                "status_code": "BLOCKED",
                "content": "不允许的协议，仅支持 http:// 和 https://"
            }
            return render_template("index.html", username=username, user=user_info, search_results=None, search_keyword="", page_content=None, fetch_result=fetch_result, fetch_url=url)

        # SSRF 防护：提取 host 并检查是否为内网地址
        try:
            from urllib.parse import urlparse
            parsed = urlparse(url)
            host = parsed.hostname
            if host and is_internal_ip(host):
                fetch_result = {
                    "url": url,
                    "status_code": "BLOCKED",
                    "content": "不允许访问内网地址"
                }
                return render_template("index.html", username=username, user=user_info, search_results=None, search_keyword="", page_content=None, fetch_result=fetch_result, fetch_url=url)
        except Exception:
            pass

        try:
            req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
            with urllib.request.urlopen(req, timeout=10) as response:
                status_code = response.status
                content = response.read().decode("utf-8", errors="replace")
                fetch_result = {
                    "url": url,
                    "status_code": status_code,
                    "content": content[:5000]
                }
        except urllib.error.HTTPError as e:
            fetch_result = {
                "url": url,
                "status_code": e.code,
                "content": str(e.reason)[:5000]
            }
        except Exception as e:
            fetch_result = {
                "url": url,
                "status_code": "ERROR",
                "content": f"抓取失败: {str(e)}"[:5000]
            }

    return render_template("index.html", username=username, user=user_info, search_results=None, search_keyword="", page_content=None, fetch_result=fetch_result, fetch_url=url)


# ── 动态页面加载 ──
@app.route("/page")
def dynamic_page():
    name = request.args.get("name", "")
    page_content = None

    # 检查页面加载频率
    if not check_page_rate_limit():
        page_content = "请求过于频繁，请稍后再试"
    elif name:
        # 拼接文件路径（不做任何安全过滤）
        page_path = os.path.join("pages", name)
        if os.path.exists(page_path):
            with open(page_path, "r", encoding="utf-8") as f:
                page_content = f.read()
        else:
            # 尝试加上 .html 后缀
            page_path_html = page_path + ".html"
            if os.path.exists(page_path_html):
                with open(page_path_html, "r", encoding="utf-8") as f:
                    page_content = f.read()
            else:
                page_content = "页面不存在"

    username = session.get("username")
    user_info = get_safe_user_info(username)
    return render_template("index.html", username=username, user=user_info, search_results=None, search_keyword="", page_content=page_content, fetch_result=None, fetch_url="")


# ── 错误处理 ──
@app.errorhandler(404)
def not_found(e):
    return render_template("base.html"), 404


@app.errorhandler(413)
def request_entity_too_large(e):
    return render_template("base.html"), 413


if __name__ == "__main__":
    debug_mode = os.environ.get("FLASK_DEBUG", "0") == "1"
    app.run(debug=debug_mode, host="127.0.0.1", port=5000)
