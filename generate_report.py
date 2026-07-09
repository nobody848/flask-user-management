#!/usr/bin/env python3
"""生成安全漏洞发现与修复过程报告 Word 文档"""

from docx import Document
from docx.shared import Pt, Cm, RGBColor
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.enum.table import WD_TABLE_ALIGNMENT
from docx.oxml.ns import qn, nsdecls
from docx.oxml import parse_xml
import os


def add_code(doc, code_text):
    """添加代码块"""
    p = doc.add_paragraph()
    p.paragraph_format.left_indent = Cm(0.5)
    p.paragraph_format.space_before = Pt(4)
    p.paragraph_format.space_after = Pt(4)
    run = p.add_run(code_text)
    run.font.name = 'Courier New'
    run.font.size = Pt(9)
    run.font.color.rgb = RGBColor(0x2D, 0x2D, 0x2D)
    shading = parse_xml(f'<w:shd {nsdecls("w")} w:fill="0xF5F5F5"/>')
    p._p.get_or_add_pPr().append(shading)
    return p


def add_table(doc, headers, rows, col_widths=None):
    """添加表格"""
    table = doc.add_table(rows=1 + len(rows), cols=len(headers), style='Light Grid Accent 1')
    table.alignment = WD_TABLE_ALIGNMENT.CENTER
    for i, h in enumerate(headers):
        cell = table.cell(0, i)
        cell.text = h
        for para in cell.paragraphs:
            para.alignment = WD_ALIGN_PARAGRAPH.CENTER
            for run in para.runs:
                run.bold = True
    for ri, row in enumerate(rows):
        for ci, val in enumerate(row):
            table.cell(ri + 1, ci).text = str(val)
    if col_widths:
        for i, w in enumerate(col_widths):
            for row in table.rows:
                row.cells[i].width = Cm(w)
    return table


def create_report():
    doc = Document()

    # 全局样式
    style = doc.styles['Normal']
    style.font.name = '微软雅黑'
    style.font.size = Pt(11)
    style.element.rPr.rFonts.set(qn('w:eastAsia'), '微软雅黑')
    for level in range(1, 5):
        hs = doc.styles[f'Heading {level}']
        hs.font.color.rgb = RGBColor(0x1a, 0x1a, 0x2e)
        hs.element.rPr.rFonts.set(qn('w:eastAsia'), '微软雅黑')

    section = doc.sections[0]
    section.top_margin = Cm(2.5)
    section.bottom_margin = Cm(2.5)
    section.left_margin = Cm(2.5)
    section.right_margin = Cm(2.5)

    # ══════════════════════════════════════
    # 封面
    # ══════════════════════════════════════
    for _ in range(6):
        doc.add_paragraph()

    title = doc.add_paragraph()
    title.alignment = WD_ALIGN_PARAGRAPH.CENTER
    run = title.add_run('Flask 用户管理系统')
    run.bold = True
    run.font.size = Pt(28)
    run.font.color.rgb = RGBColor(0x1a, 0x1a, 0x2e)

    subtitle = doc.add_paragraph()
    subtitle.alignment = WD_ALIGN_PARAGRAPH.CENTER
    run = subtitle.add_run('安全漏洞发现与修复过程报告')
    run.bold = True
    run.font.size = Pt(20)
    run.font.color.rgb = RGBColor(0x66, 0x7e, 0xea)

    doc.add_paragraph()
    line = doc.add_paragraph()
    line.alignment = WD_ALIGN_PARAGRAPH.CENTER
    run = line.add_run('━' * 40)
    run.font.color.rgb = RGBColor(0x66, 0x7e, 0xea)

    doc.add_paragraph()
    info = doc.add_paragraph()
    info.alignment = WD_ALIGN_PARAGRAPH.CENTER
    run = info.add_run(
        '项目地址：github.com/nobody848/flask-user-management\n'
        '审计日期：2026-07-09\n'
        '技术栈：Python Flask + SQLite + Jinja2'
    )
    run.font.size = Pt(12)
    run.font.color.rgb = RGBColor(0x66, 0x66, 0x66)

    doc.add_page_break()

    # ══════════════════════════════════════
    # 一、审计概述
    # ══════════════════════════════════════
    doc.add_heading('一、审计概述', level=1)

    doc.add_heading('1.1 审计范围', level=2)
    doc.add_paragraph(
        '本次安全审计覆盖项目全部源代码，包括 app.py 主应用逻辑及所有 Jinja2 模板文件。'
        '审计以手动代码审查（Manual Code Review）方式逐行检查，发现安全漏洞后逐一修复并验证。'
    )

    add_table(doc,
        ['文件', '行数', '功能'],
        [
            ['app.py', '约 400 行', 'Flask 主应用逻辑（路由、Session、数据库）'],
            ['templates/base.html', '27 行', '基础布局模板'],
            ['templates/index.html', '62 行', '首页 / 用户信息 / 搜索'],
            ['templates/login.html', '24 行', '登录页面'],
            ['templates/register.html', '35 行', '注册页面'],
            ['templates/upload.html', '31 行', '上传头像页面'],
            ['static/css/style.css', '308 行', '全局样式'],
        ],
        col_widths=[4, 2, 10]
    )

    doc.add_paragraph()

    doc.add_heading('1.2 审计方法', level=2)
    doc.add_paragraph('漏洞发现采用以下方法：')
    methods = [
        '静态代码审查 — 逐行检查源代码中的安全缺陷',
        '攻击路径推演 — 对每个潜在漏洞推演完整的攻击链',
        '漏洞分类分级 — 按 OWASP Top 10 框架分类，按严重程度分级',
        '修复验证 — 修复后通过功能测试确认修复有效且不影响原有功能',
    ]
    for m in methods:
        doc.add_paragraph(m, style='List Bullet')

    doc.add_page_break()

    # ══════════════════════════════════════
    # 二、漏洞发现过程
    # ══════════════════════════════════════
    doc.add_heading('二、漏洞发现过程', level=1)

    doc.add_paragraph(
        '以下按照代码从上到下的阅读顺序，逐一描述每个漏洞的发现过程、'
        '漏洞代码定位、攻击路径推演和修复方案。'
    )

    # ── V-01 ──
    doc.add_heading('V-01：会话固定攻击（Session Fixation）', level=2)

    doc.add_heading('🔍 发现过程', level=3)
    doc.add_paragraph(
        '审查登录路由（login 函数）时，发现用户登录成功后仅简单地设置 session["username"]，'
        '没有重置 Session ID。Flask 的客户端 Session 机制中，Session 数据被签名后存储在 Cookie 中，'
        '如果攻击者事先让受害者使用一个已知的 Session Cookie 登录，攻击者就可以冒用受害者的身份。'
    )

    doc.add_heading('📌 漏洞代码定位', level=3)
    doc.add_paragraph('文件：app.py，原 login 函数（约第 198-206 行）')
    add_code(doc, '''# ❌ 修复前：直接设置 session，不重置
if user and check_password_hash(user["password"], password):
    session["username"] = username          # 旧 session ID 继续使用
    session.permanent = True
    reset_login_rate_limit()
    ...''')

    doc.add_heading('🔗 攻击路径推演', level=3)
    add_code(doc, '''Step 1: 攻击者获取一个空白 session cookie（访问任意页面即可获得）
Step 2: 攻击者将 cookie 通过 URL 参数 /login?session=xxx 发给受害者
Step 3: 受害者使用该 cookie 登录成功
Step 4: 攻击者使用同一 cookie → 直接以受害者身份登录''')

    doc.add_heading('🛠️ 修复方案', level=3)
    doc.add_paragraph('登录成功后重置 session 并生成新 CSRF Token：')
    add_code(doc, '''# ✅ 修复后：重置 session 防止会话固定攻击
if user and check_password_hash(user["password"], password):
    session.clear()                          # 清除旧 session
    session["username"] = username
    session.permanent = True
    session["csrf_token"] = secrets.token_hex(32)  # 新 token
    reset_login_rate_limit()
    ...''')

    doc.add_paragraph()

    # ── V-02 ──
    doc.add_heading('V-02：注册用户名枚举（User Enumeration）', level=2)

    doc.add_heading('🔍 发现过程', level=3)
    doc.add_paragraph(
        '审查注册路由（register 函数）时，发现数据库 UNIQUE 约束冲突时返回的具体错误信息'
        '"用户名已存在，请选择其他用户名"。这个错误信息精确地告诉攻击者某个用户名是否已注册，'
        '攻击者可以利用此信息批量验证用户名是否有效，为后续的暴力破解或钓鱼攻击提供目标清单。'
    )

    doc.add_heading('📌 漏洞代码定位', level=3)
    doc.add_paragraph('文件：app.py，原 register 函数异常处理部分')
    add_code(doc, '''# ❌ 修复前：泄露用户名是否存在
except sqlite3.IntegrityError:
    error = "用户名已存在，请选择其他用户名"''')

    doc.add_heading('🔗 攻击路径推演', level=3)
    add_code(doc, '''Step 1: 攻击者编写脚本批量注册常见用户名（admin, root, test, user...）
Step 2: 对每个用户名，根据错误信息判断是否已注册
Step 3: 收集有效用户名清单
Step 4: 对有效用户名发起暴力破解或定向钓鱼攻击''')

    doc.add_heading('🛠️ 修复方案', level=3)
    doc.add_paragraph('使用模糊的错误信息，不透露用户名是否已存在：')
    add_code(doc, '''# ✅ 修复后：统一使用模糊错误信息
except sqlite3.IntegrityError:
    error = "注册失败，用户名可能已存在，请尝试其他用户名"''')

    doc.add_paragraph()

    # ── V-03 ──
    doc.add_heading('V-03：注册接口缺少频率限制（无 Rate Limiting）', level=2)

    doc.add_heading('🔍 发现过程', level=3)
    doc.add_paragraph(
        '审查代码时发现登录接口有频率限制（check_login_rate_limit），但注册接口完全没有限制。'
        '攻击者可以通过注册接口批量创建恶意账号，或批量探测用户名是否已注册（即使修复了 V-02，'
        '没有频率限制仍然允许大量请求）。'
    )

    doc.add_heading('📌 漏洞代码定位', level=3)
    doc.add_paragraph('文件：app.py，register 函数 — 缺少频率检查')
    add_code(doc, '''# ❌ 修复前：注册接口无频率限制
@app.route("/register", methods=["GET", "POST"])
def register():
    error = None
    if request.method == "POST":
        # CSRF 校验...
        username = request.form.get("username", "").strip()
        # ... 无频率限制检查''')

    doc.add_heading('🔗 攻击路径推演', level=3)
    add_code(doc, '''Step 1: 攻击者编写脚本高速发送注册请求（每秒数十次）
Step 2: 短时间内注册数百个垃圾账号
Step 3: 消耗服务器资源 (SQLite写入)
Step 4: 利用这些账号进行垃圾内容发布或其他恶意行为''')

    doc.add_heading('🛠️ 修复方案', level=3)
    doc.add_paragraph('复用已有的频率限制框架，添加注册频率限制（3次/10分钟）：')
    add_code(doc, '''# app.py 配置部分新增
REGISTER_ATTEMPTS = {}
MAX_REGISTER_ATTEMPTS = 3
REGISTER_LOCKOUT_TIME = 600  # 10 分钟

# 通用频率检查函数
def _check_rate_limit(attempts_dict, max_attempts, lockout_time, label):
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

# register 函数开头增加
if not check_register_rate_limit():
    error = "注册尝试过于频繁，请稍后再试"
    return render_template("register.html", error=error)''')

    doc.add_paragraph()

    # ── V-04 ──
    doc.add_heading('V-04：文件上传路径遍历漏洞（Path Traversal）', level=2)

    doc.add_heading('🔍 发现过程', level=3)
    doc.add_paragraph(
        '审查上传路由（upload 函数）时，发现 file.filename 直接被拼接到文件保存路径中，'
        '没有任何过滤。攻击者可以通过构造包含 "../" 的文件名，将文件写入到项目目录外的任意位置，'
        '甚至覆盖系统关键文件。'
    )

    doc.add_heading('📌 漏洞代码定位', level=3)
    doc.add_paragraph('文件：app.py，原 upload 函数（约第 326-328 行）')
    add_code(doc, '''# ❌ 修复前：直接使用用户提供的文件名
save_path = os.path.join(UPLOAD_FOLDER, file.filename)
file.save(save_path)

# 攻击者可提交 filename="../../etc/cronjob.sh"
# 实际保存到 static/uploads/../../etc/cronjob.sh → /etc/cronjob.sh''')

    doc.add_heading('🔗 攻击路径推演', level=3)
    add_code(doc, '''Step 1: 攻击者登录后构造恶意文件名 "../../evil.py"
Step 2: POST /upload 上传一个恶意 Python 文件
Step 3: 文件实际保存到项目外部的任意目录
Step 4: 结合其他漏洞触发恶意代码执行''')

    doc.add_heading('🛠️ 修复方案', level=3)
    doc.add_paragraph('使用 os.path.basename() 提取纯文件名，去除所有目录路径部分：')
    add_code(doc, '''# 新增安全文件名函数
def safe_filename(filename):
    """移除路径遍历字符，保留原始文件名"""
    filename = os.path.basename(filename)
    filename = filename.replace("\\x00", "")
    if not filename:
        filename = "unnamed"
    return filename

# 上传时使用
original_name = safe_filename(file.filename)
save_path = os.path.join(user_upload_dir, original_name)
file.save(save_path)''')

    doc.add_paragraph()

    # ── V-05 ──
    doc.add_heading('V-05：文件上传缺少用户隔离（用户间文件覆盖）', level=2)

    doc.add_heading('🔍 发现过程', level=3)
    doc.add_paragraph(
        '审查上传路由时，发现所有用户的上传文件都保存在同一个 static/uploads/ 目录下，'
        '没有按用户隔离。用户 A 上传 photo.png 后，用户 B 再上传同名 photo.png 会静默覆盖用户 A 的文件。'
        '这可能导致数据丢失和拒绝服务。'
    )

    doc.add_heading('📌 漏洞代码定位', level=3)
    doc.add_paragraph('文件：app.py，原 upload 函数 — 所有用户共用同一目录')
    add_code(doc, '''# ❌ 修复前：所有用户共用上传目录
save_path = os.path.join(UPLOAD_FOLDER, file.filename)
file.save(save_path)
file_url = url_for("static", filename=f"uploads/{file.filename}")''')

    doc.add_heading('🛠️ 修复方案', level=3)
    doc.add_paragraph('按用户名创建子目录，每个用户拥有独立的上传空间：')
    add_code(doc, '''# ✅ 修复后：按用户隔离
username = session.get("username", "anonymous")
user_upload_dir = os.path.join(UPLOAD_FOLDER, username)
os.makedirs(user_upload_dir, exist_ok=True)
original_name = safe_filename(file.filename)
save_path = os.path.join(user_upload_dir, original_name)
file.save(save_path)
file_url = url_for("static", filename=f"uploads/{username}/{original_name}")''')

    doc.add_paragraph()

    # ── V-06 ──
    doc.add_heading('V-06：缺少安全响应头（Security Headers）', level=2)

    doc.add_heading('🔍 发现过程', level=3)
    doc.add_paragraph(
        '审查响应头配置时，发现应用没有设置任何安全相关的 HTTP 响应头。'
        '这会使应用面临点击劫持（Clickjacking）、MIME 类型嗅探攻击、'
        '以及 XSS 在部分浏览器中更容易被利用的风险。'
    )

    doc.add_heading('📌 漏洞代码定位', level=3)
    doc.add_paragraph('文件：app.py — 缺少 after_request 安全头中间件')
    add_code(doc, '''# ❌ 修复前：没有任何安全响应头
# 浏览器会默认允许：
# - 页面被嵌入 iframe（点击劫持）
# - MIME 类型嗅探（上传欺骗性文件时）
# - 加载任意外部资源（缺少 CSP）''')

    doc.add_heading('🛠️ 修复方案', level=3)
    doc.add_paragraph('添加 after_request 钩子，注入安全响应头：')
    add_code(doc, '''@app.after_request
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
    return response''')

    doc.add_paragraph()

    # ── V-07 ──
    doc.add_heading('V-07：注册输入字段缺少长度限制', level=2)

    doc.add_heading('🔍 发现过程', level=3)
    doc.add_paragraph(
        '审查注册路由时，发现 email 和 phone 字段直接从 request.form 获取后没有做任何长度截断。'
        '攻击者可以提交超长字符串，导致数据库存储异常、内存消耗增加，甚至触发 SQLite 限制错误。'
    )

    doc.add_heading('📌 漏洞代码定位', level=3)
    doc.add_paragraph('文件：app.py，register 函数 — 输入获取部分')
    add_code(doc, '''# ❌ 修复前：无长度限制
username = request.form.get("username", "").strip()
password = request.form.get("password", "")
email = request.form.get("email", "").strip()
phone = request.form.get("phone", "").strip()''')

    doc.add_heading('🛠️ 修复方案', level=3)
    doc.add_paragraph('对每个输入字段做切片截断：')
    add_code(doc, '''# ✅ 修复后：增加长度截断
username = request.form.get("username", "").strip()[:32]
password = request.form.get("password", "")[:128]
email = request.form.get("email", "").strip()[:254]
phone = request.form.get("phone", "").strip()[:20]''')

    doc.add_paragraph()

    # ── V-08 ──
    doc.add_heading('V-08：登出后 CSRF Token 未更新', level=2)

    doc.add_heading('🔍 发现过程', level=3)
    doc.add_paragraph(
        '审查登出路由（logout 函数）时，发现登出后 session 被清除但未生成新的 CSRF Token。'
        '这使得浏览器历史记录中的旧页面如果包含表单，仍可能被重放利用。'
        '虽然程度较低，但作为纵深防御措施应该修复。'
    )

    doc.add_heading('📌 漏洞代码定位', level=3)
    doc.add_paragraph('文件：app.py，原 logout 函数')
    add_code(doc, '''# ❌ 修复前：清除 session 后没有生成新 token
@app.route("/logout")
def logout():
    session.clear()
    return redirect("/")''')

    doc.add_heading('🛠️ 修复方案', level=3)
    add_code(doc, '''# ✅ 修复后：生成新 CSRF Token
@app.route("/logout")
def logout():
    session.clear()
    session["csrf_token"] = secrets.token_hex(32)
    return redirect("/")''')

    doc.add_page_break()

    # ══════════════════════════════════════
    # 三、漏洞汇总
    # ══════════════════════════════════════
    doc.add_heading('三、漏洞汇总', level=1)

    add_table(doc,
        ['编号', '漏洞名称', '严重程度', '发现方式', '修复方式'],
        [
            ['V-01', '会话固定攻击 (Session Fixation)', '🔴 高危', '代码审查', '登录后 session.clear()'],
            ['V-02', '注册用户名枚举', '🟠 中危', '代码审查', '模糊错误信息'],
            ['V-03', '注册接口缺少频率限制', '🟠 中危', '代码审查', '新增 Rate Limiting'],
            ['V-04', '文件上传路径遍历', '🔴 高危', '代码审查', 'basename 过滤'],
            ['V-05', '上传缺少用户隔离', '🟡 低危', '代码审查', '按用户建子目录'],
            ['V-06', '缺少安全响应头', '🟠 中危', '代码审查', 'after_request 头注入'],
            ['V-07', '注册输入缺少长度限制', '🟡 低危', '代码审查', '字段切片截断'],
            ['V-08', '登出后 CSRF Token 未更新', '🟡 低危', '代码审查', '登出时生成新 Token'],
        ],
        col_widths=[1.5, 5.5, 2, 2.5, 4.5]
    )

    doc.add_page_break()

    # ══════════════════════════════════════
    # 四、修复验证
    # ══════════════════════════════════════
    doc.add_heading('四、修复验证', level=1)

    doc.add_heading('4.1 功能测试', level=2)
    add_table(doc,
        ['测试项', '结果'],
        [
            ['GET / 首页', '✅ 200 OK'],
            ['GET /login 登录页', '✅ 200 OK'],
            ['GET /register 注册页', '✅ 200 OK'],
            ['GET /upload (未登录)', '✅ 302 跳转到 /login'],
            ['GET /search (未登录)', '✅ 302 跳转到 /login'],
            ['POST /login admin 登录', '✅ 200 OK'],
            ['GET /upload (已登录)', '✅ 200 OK'],
            ['X-Content-Type-Options 头', '✅ nosniff'],
            ['X-Frame-Options 头', '✅ DENY'],
            ['Content-Security-Policy 头', '✅ 已设置'],
        ],
        col_widths=[8, 4]
    )

    doc.add_paragraph()

    doc.add_heading('4.2 安全验证', level=2)
    doc.add_paragraph('每个漏洞修复后均进行了以下验证：')
    verifications = [
        'V-01 会话固定：登录后 session.clear() 使旧 cookie 失效，新 cookie 包含新签名',
        'V-02 用户枚举：注册重复用户名返回模糊提示，攻击者无法区分"用户名已存在"和"其他错误"',
        'V-03 注册频率：同一 IP 10 分钟内最多注册 3 次，超过返回限制提示',
        'V-04 路径遍历：上传 filename="../../a.txt" → os.path.basename 提取为 "a.txt"',
        'V-05 用户隔离：admin 上传 photo.png → static/uploads/admin/photo.png',
        'V-06 安全头：curl 响应中包含 X-Content-Type-Options、X-Frame-Options、CSP',
        'V-07 长度限制：提交超长字段 → 自动截断至最大允许长度',
        'V-08 CSRF 更新：登出后 session 中 csrf_token 为新生成的随机值',
    ]
    for v in verifications:
        doc.add_paragraph(v, style='List Bullet')

    doc.add_page_break()

    # ══════════════════════════════════════
    # 五、项目地址
    # ══════════════════════════════════════
    doc.add_heading('五、项目地址', level=1)

    p = doc.add_paragraph()
    run = p.add_run('GitHub 仓库：')
    run.bold = True
    run = p.add_run('https://github.com/nobody848/flask-user-management')
    run.font.color.rgb = RGBColor(0x00, 0x66, 0xCC)

    p = doc.add_paragraph()
    run = p.add_run('本次修复提交：')
    run.bold = True
    run = p.add_run('（见 GitHub 仓库 commit 记录）')

    doc.add_paragraph()

    p = doc.add_paragraph()
    p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    run = p.add_run('━' * 40)
    run.font.color.rgb = RGBColor(0xCC, 0xCC, 0xCC)

    p = doc.add_paragraph()
    p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    run = p.add_run('报告生成日期：2026-07-09')
    run.font.size = Pt(10)
    run.font.color.rgb = RGBColor(0x99, 0x99, 0x99)

    p = doc.add_paragraph()
    p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    run = p.add_run('审计方式：Manual Code Review')
    run.font.size = Pt(10)
    run.font.color.rgb = RGBColor(0x99, 0x99, 0x99)

    # ── 保存 ──
    script_dir = os.path.dirname(os.path.abspath(__file__))
    output_path = os.path.join(script_dir, 'static', '安全漏洞发现与修复过程报告.docx')
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    doc.save(output_path)
    print(f'报告已生成：{output_path}')
    print(f'文件大小：{os.path.getsize(output_path) / 1024:.1f} KB')
    return output_path


if __name__ == '__main__':
    create_report()
