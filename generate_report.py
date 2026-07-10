#!/usr/bin/env python3
"""生成业务逻辑及越权漏洞分析报告"""

from docx import Document
from docx.shared import Pt, Cm, RGBColor
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.enum.table import WD_TABLE_ALIGNMENT
from docx.oxml.ns import qn, nsdecls
from docx.oxml import parse_xml
import os


def add_code(doc, code_text):
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


def add_table(doc, headers, rows, col_widths=None):
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

    # ═══════ 封面 ═══════
    for _ in range(6):
        doc.add_paragraph()
    title = doc.add_paragraph()
    title.alignment = WD_ALIGN_PARAGRAPH.CENTER
    run = title.add_run('Flask 用户管理系统')
    run.bold = True; run.font.size = Pt(28)
    run.font.color.rgb = RGBColor(0x1a, 0x1a, 0x2e)

    subtitle = doc.add_paragraph()
    subtitle.alignment = WD_ALIGN_PARAGRAPH.CENTER
    run = subtitle.add_run('业务逻辑及越权漏洞分析报告')
    run.bold = True; run.font.size = Pt(20)
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
        '分析日期：2026-07-09\n'
        '分析范围：/profile 路由、/recharge 路由、profile.html 模板'
    )
    run.font.size = Pt(12)
    run.font.color.rgb = RGBColor(0x66, 0x66, 0x66)
    doc.add_page_break()

    # ═══════ 一、分析范围 ═══════
    doc.add_heading('一、分析范围', level=1)
    doc.add_paragraph(
        '本次分析聚焦于今日新增的两个业务功能：个人中心（/profile）和充值（/recharge）。'
        '分析维度包括业务逻辑缺陷和越权漏洞，不涉及其他已有功能模块。'
    )

    add_table(doc,
        ['功能', '路由', '方法', '描述'],
        [
            ['个人中心', '/profile', 'GET', '根据 URL 参数 user_id 展示用户资料'],
            ['充值', '/recharge', 'POST', '根据表单 user_id 和 amount 修改用户余额'],
        ],
        col_widths=[3, 3, 2, 8]
    )

    doc.add_paragraph()
    doc.add_heading('1.1 核心代码定位', level=2)
    doc.add_paragraph('个人中心路由（app.py 第 415-425 行）：')
    add_code(doc, '''@app.route("/profile")
@login_required
def profile():
    user_id = request.args.get("user_id", "")
    user_info = get_user_by_id(user_id)
    if user_info is None:
        return render_template("profile.html", user=None, error="未找到该用户")
    return render_template("profile.html", user=user_info, error=None)''')

    doc.add_paragraph('充值路由（app.py 第 428-447 行）：')
    add_code(doc, '''@app.route("/recharge", methods=["POST"])
@login_required
def recharge():
    user_id = request.form.get("user_id", "")
    amount = request.form.get("amount", "0")
    try:
        amount = float(amount)
        user_id_int = int(user_id)
    except (ValueError, TypeError):
        return redirect(f"/profile?user_id={user_id}")
    conn = sqlite3.connect("data/users.db")
    cursor = conn.cursor()
    cursor.execute("UPDATE users SET balance = balance + ? WHERE id = ?", (amount, user_id_int))
    conn.commit()
    conn.close()
    return redirect(f"/profile?user_id={user_id}")''')

    doc.add_paragraph('充值表单（profile.html 第 22-29 行）：')
    add_code(doc, '''<form action="/recharge" method="POST" class="recharge-form">
    <input type="hidden" name="csrf_token" value="{{ csrf_token }}">
    <input type="hidden" name="user_id" value="{{ user.id }}">
    <div class="form-group">
        <label for="amount">充值金额</label>
        <input type="number" id="amount" name="amount" step="0.01"
               placeholder="请输入充值金额" class="recharge-input">
    </div>
    <button type="submit" class="btn btn-primary">确认充值</button>
</form>''')

    doc.add_page_break()

    # ═══════ 二、漏洞发现过程 ═══════
    doc.add_heading('二、漏洞发现过程', level=1)
    doc.add_paragraph('以下按严重程度从高到低逐一描述每个漏洞的发现过程、攻击路径和修复方案。')

    # ── BL-01 ──
    doc.add_heading('BL-01：水平越权 — 任意用户资料可被越权查看（高危）', level=2)

    doc.add_heading('1. 漏洞发现', level=3)
    doc.add_paragraph(
        '审查 /profile 路由时发现，user_id 参数完全来自 URL 查询字符串（request.args.get），'
        '后端没有将当前登录用户与请求查询的 user_id 做任何比对。'
        '这意味着用户 alice 登录后，只需将 URL 中的 user_id=2 改为 user_id=1，'
        '即可查看管理员 admin 的完整资料，包括邮箱、手机号和余额。'
    )

    doc.add_heading('2. 漏洞代码定位', level=3)
    add_code(doc, '''# ❌ 问题代码：user_id 来源与当前用户无关
user_id = request.args.get("user_id", "")     # 从 URL 获取，与 session 无关
user_info = get_user_by_id(user_id)           # 直接查询，无视所有权

# 缺少的关键校验：
# if str(user_id) != str(session.get("user_id")):
#     return abort(403)''')

    doc.add_heading('3. 攻击路径推演', level=3)
    add_table(doc,
        ['步骤', '操作', '说明'],
        [
            ['1', 'alice 登录系统', '以普通用户 alice 身份登录'],
            ['2', '访问个人中心', '正常 URL：/profile?user_id=2（alice 自己的资料）'],
            ['3', '修改 URL 参数', '将 URL 改为 /profile?user_id=1'],
            ['4', '越权查看', 'admin 的邮箱、手机、余额全部展示在页面上'],
            ['5', '遍历全部用户', '继续修改 user_id=3,4,5... 可枚举所有注册用户信息'],
        ],
        col_widths=[1, 3.5, 10]
    )

    doc.add_heading('4. 危害评级', level=3)
    add_table(doc,
        ['维度', '评级', '说明'],
        [
            ['攻击复杂度', '极低', '仅需修改浏览器 URL 参数'],
            ['利用难度', '极低', '无需任何工具，在地址栏操作即可'],
            ['影响范围', '高', '所有注册用户的个人隐私数据均可被窃取'],
            ['综合评级', '🔴 高危', 'CVSS 3.x 评分：7.5'],
        ],
        col_widths=[3.5, 2, 10]
    )

    doc.add_heading('5. 修复方案', level=3)
    doc.add_paragraph('在 /profile 路由中增加身份校验，确保只能查看当前登录用户本人的资料：')
    add_code(doc, '''@app.route("/profile")
@login_required
def profile():
    user_id = request.args.get("user_id", "")
    # 获取当前登录用户 ID
    current_username = session.get("username")
    current_user = get_user_from_db(current_username)
    current_user_id = get_user_id_by_username(current_username)  # 需新增此函数

    # 权限校验：只能查看自己的资料
    if str(user_id) != str(current_user_id):
        return abort(403)

    user_info = get_user_by_id(user_id)
    ...''')

    doc.add_paragraph()

    # ── BL-02 ──
    doc.add_heading('BL-02：水平越权 — 任意用户余额可被他人篡改（高危）', level=2)

    doc.add_heading('1. 漏洞发现', level=3)
    doc.add_paragraph(
        '审查 /recharge 路由时发现，user_id 参数来自表单 POST 数据（request.form.get），'
        '且充值表单中的 user_id 是一个隐藏的 input 字段。后端既没有验证当前登录用户 '
        '与充值目标的 user_id 是否匹配，也没有在服务端重新确认 user_id 的真实性。'
        '攻击者只需修改 HTML 中的隐藏字段值，或直接用 curl 构造 POST 请求，'
        '即可为任意用户充值或扣减余额。'
    )

    doc.add_heading('2. 漏洞代码定位', level=3)
    add_code(doc, '''# ❌ 问题代码：user_id 来自前端隐藏字段，完全不可信
user_id = request.form.get("user_id", "")   # 隐藏字段容易被篡改
amount = request.form.get("amount", "0")
...
cursor.execute("UPDATE users SET balance = balance + ? WHERE id = ?", (amount, user_id_int))

# 缺少的关键校验：
# 1. 未校验当前用户 == 充值目标用户
# 2. 未在服务端重新获取 user_id（不应信赖前端传入）''')

    doc.add_heading('3. 攻击路径推演', level=3)
    add_table(doc,
        ['步骤', '操作', '说明'],
        [
            ['1', 'alice 登录系统', '以普通用户 alice 身份登录'],
            ['2', '打开个人中心', '正常页面，充值表单的隐藏 user_id=2'],
            ['3', '修改隐藏字段', '浏览器 DevTools 将 user_id 改为 1（admin 的 ID）'],
            ['4', '输入金额提交', '充值 -99999 → admin 余额从 99999 变为 0'],
            ['5', '直接构造请求', 'curl -X POST /recharge -d "user_id=1&amount=-99999"'],
        ],
        col_widths=[1, 4, 10]
    )

    doc.add_heading('4. 危害评级', level=3)
    add_table(doc,
        ['维度', '评级', '说明'],
        [
            ['攻击复杂度', '极低', '浏览器 DevTools 或 curl 即可完成'],
            ['利用难度', '极低', '无需任何特殊权限'],
            ['影响范围', '高', '任意用户的余额可被任意增减，直接造成经济损失'],
            ['综合评级', '🔴 高危', 'CVSS 3.x 评分：8.1'],
        ],
        col_widths=[3.5, 2, 10]
    )

    doc.add_heading('5. 修复方案', level=3)
    doc.add_paragraph('充值时应从 session 获取当前用户，并强制只能操作自己的账户：')
    add_code(doc, '''@app.route("/recharge", methods=["POST"])
@login_required
def recharge():
    amount = request.form.get("amount", "0")
    # 从 session 获取当前登录用户身份（不信任前端传入的 user_id）
    current_username = session.get("username")
    current_user = get_user_from_db(current_username)
    current_user_id = get_user_id_by_username(current_username)

    try:
        amount = float(amount)
    except (ValueError, TypeError):
        return redirect(f"/profile?user_id={current_user_id}")

    # 只能给自己充值
    conn = sqlite3.connect("data/users.db")
    cursor = conn.cursor()
    cursor.execute("UPDATE users SET balance = balance + ? WHERE id = ?",
                   (amount, current_user_id))
    conn.commit()
    conn.close()

    return redirect(f"/profile?user_id={current_user_id}")''')

    doc.add_paragraph()

    # ── BL-03 ──
    doc.add_heading('BL-03：业务逻辑缺陷 — 充值金额可正可负（中危）', level=2)

    doc.add_heading('1. 漏洞发现', level=3)
    doc.add_paragraph(
        '审查 /recharge 路由时发现，amount 参数直接从表单获取后转为 float，'
        '直接执行 SQL 的 balance = balance + amount。代码没有对 amount 做任何正负校验，'
        '这意味着用户可以提交负数金额来实现"反向充值"——实际是从账户中扣减余额。'
        '更严重的是，由于 BL-02 的越权漏洞，攻击者可以用负数给任意用户扣款。'
    )

    doc.add_heading('2. 漏洞代码定位', level=3)
    add_code(doc, '''# ❌ 问题代码：amount 未做范围校验
amount = float(amount)    # 用户可传入 -9999999.99
...
cursor.execute("UPDATE users SET balance = balance + ? WHERE id = ?", (amount, user_id_int))
# balance = balance + (-9999999.99) → 余额瞬间变负数''')

    doc.add_heading('3. 攻击路径推演', level=3)
    add_table(doc,
        ['步骤', '操作', '效果'],
        [
            ['1', '登录任意账户', '获取合法 session'],
            ['2', '提交 amount=-99999', '余额被扣减 99999'],
            ['3', '反复提交', '余额可被扣到负数甚至 -∞'],
            ['4', '越权组合利用', '将他人余额扣为负数，实现"抢劫"'],
        ],
        col_widths=[1, 4.5, 8.5]
    )

    doc.add_heading('4. 修复方案', level=3)
    add_code(doc, '''# ✅ 修复：增加金额正负校验
try:
    amount = float(amount)
    if amount <= 0:
        return redirect(f"/profile?user_id={user_id}?error=充值金额必须为正数")
except (ValueError, TypeError):
    return redirect(f"/profile?user_id={user_id}")''')

    doc.add_paragraph()

    # ── BL-04 ──
    doc.add_heading('BL-04：信息泄露 — 用户 ID 可被枚举遍历（中危）', level=2)

    doc.add_heading('1. 漏洞发现', level=3)
    doc.add_paragraph(
        '审查 /profile 路由的查询逻辑时发现，user_id 参数使用连续的整数自增 ID，'
        '且未登录用户无法访问（有 @login_required 保护），但任何已登录用户'
        '可以通过遍历 user_id 参数来发现系统中有多少注册用户以及他们的详细信息。'
        '这构成了用户枚举攻击（User Enumeration）。'
    )

    doc.add_heading('2. 攻击路径推演', level=3)
    add_code(doc, '''# 使用 curl 脚本遍历所有用户
for i in $(seq 1 100); do
  curl -b "session=..." "http://localhost:5000/profile?user_id=$i"
  # 根据返回内容判断用户是否存在
done
# 结果：系统中有哪些用户、各用户的邮箱、手机、余额全部暴露''')

    doc.add_heading('3. 修复方案', level=3)
    doc.add_paragraph('将连续的整数 ID 替换为 UUID 或随机的用户标识符，或在已修复 BL-01 的基础上，'
                       '用户只能看到自己的资料，枚举将无法获取他人信息。')

    doc.add_paragraph()

    # ── BL-05 ──
    doc.add_heading('BL-05：业务逻辑缺陷 — 充值操作无频率限制（低危）', level=2)

    doc.add_heading('1. 漏洞发现', level=3)
    doc.add_paragraph(
        '审查 /recharge 路由时发现，该接口没有任何频率限制。'
        '虽然登录接口有 check_login_rate_limit()、注册接口有 check_register_rate_limit()，'
        '但充值接口完全没有任何速率控制。攻击者可以在短时间内发送大量充值请求，'
        '如果结合 BL-03（负数金额），可以极快地破坏账户余额数据。'
    )

    doc.add_heading('2. 漏洞代码定位', level=3)
    add_code(doc, '''# ❌ 问题代码：充值接口完全无频率限制
@app.route("/recharge", methods=["POST"])
@login_required
def recharge():
    user_id = request.form.get("user_id", "")
    amount = request.form.get("amount", "0")
    # ... 缺少频率校验
    cursor.execute("UPDATE users SET balance = balance + ? WHERE id = ?", ...)''')

    doc.add_heading('3. 攻击路径推演', level=3)
    add_code(doc, '''# 每秒发送 100 次扣款请求，5 秒内将余额扣到负数
for i in $(seq 1 500); do
  curl -X POST -b "session=..." \\
    -d "user_id=2&amount=-99999" \\
    "http://localhost:5000/recharge" &
done
wait''')

    doc.add_heading('4. 修复方案', level=3)
    add_code(doc, '''# ✅ 复用项目已有的频率限制框架
RECHARGE_ATTEMPTS = {}
MAX_RECHARGE_ATTEMPTS = 5
RECHARGE_LOCKOUT_TIME = 60  # 1 分钟

def check_recharge_rate_limit():
    return _check_rate_limit(RECHARGE_ATTEMPTS, MAX_RECHARGE_ATTEMPTS,
                             RECHARGE_LOCKOUT_TIME, "recharge")

@app.route("/recharge", methods=["POST"])
@login_required
def recharge():
    if not check_recharge_rate_limit():
        return redirect("/profile?user_id=当前用户ID&error=操作过于频繁")
    ...''')

    doc.add_paragraph()

    # ── BL-06 ──
    doc.add_heading('BL-06：业务逻辑缺陷 — CSRF 防护依赖于前端隐藏字段（低危）', level=2)

    doc.add_heading('1. 漏洞发现', level=3)
    doc.add_paragraph(
        '审查 profile.html 中的充值表单发现，user_id 通过隐藏的 input 字段传递。'
        '虽然项目已经实现了 CSRF Token 防护，但 user_id 放在隐藏字段中意味着：'
        '攻击者可以通过浏览器的"查看页面源代码"或 DevTools 轻易获取当前页面的 user_id。'
        '结合 BL-02 和 BL-03，如果攻击者能诱使用户点击一个构造好的表单，'
        '就可以利用 CSRF + 越权 + 负金额的组合实现跨站扣款攻击。'
    )

    doc.add_heading('2. 漏洞代码定位', level=3)
    add_code(doc, '''<!-- ❌ 问题：user_id 暴露在前端，且未经服务端二次确认 -->
<input type="hidden" name="user_id" value="{{ user.id }}">
<!-- 攻击者只需查看页面源代码即可获得此值 -->''')

    doc.add_heading('3. 修复方案', level=3)
    doc.add_paragraph('user_id 不应依赖前端传入，而应从服务端 session 中获取：')
    add_code(doc, '''# ✅ 修复：充值表单移除 user_id 隐藏字段
<form action="/recharge" method="POST" class="recharge-form">
    <input type="hidden" name="csrf_token" value="{{ csrf_token }}">
    <div class="form-group">
        <label for="amount">充值金额</label>
        <input type="number" id="amount" name="amount" step="0.01"
               placeholder="请输入充值金额" class="recharge-input">
    </div>
    <button type="submit" class="btn btn-primary">确认充值</button>
</form>

# 服务端直接从 session 获取充值目标
current_user_id = session.get("user_id")   # 服务端可靠来源
cursor.execute("UPDATE users SET balance = balance + ? WHERE id = ?",
               (amount, current_user_id))''')

    doc.add_page_break()

    # ═══════ 三、漏洞汇总 ═══════
    doc.add_heading('三、漏洞汇总', level=1)

    add_table(doc,
        ['编号', '漏洞名称', '类型', '严重', '涉及功能'],
        [
            ['BL-01', '水平越权 — 任意用户资料可被查看', '越权漏洞', '🔴 高危', '/profile'],
            ['BL-02', '水平越权 — 任意用户余额可被篡改', '越权漏洞', '🔴 高危', '/recharge'],
            ['BL-03', '充值金额可正可负（反向扣款）', '业务逻辑', '🟠 中危', '/recharge'],
            ['BL-04', '用户 ID 可被枚举遍历', '信息泄露', '🟠 中危', '/profile'],
            ['BL-05', '充值操作无频率限制', '业务逻辑', '🟡 低危', '/recharge'],
            ['BL-06', 'user_id 暴露在前端隐藏字段', '业务逻辑', '🟡 低危', 'profile.html'],
        ],
        col_widths=[1.5, 6, 2.5, 2, 2.5]
    )

    doc.add_page_break()

    # ═══════ 四、越权攻击路径全景 ═══════
    doc.add_heading('四、越权攻击路径全景', level=1)

    doc.add_paragraph('以下展示从攻击者视角出发，各漏洞之间如何串联形成完整的攻击链：')

    doc.add_heading('攻击链 1：越权窃取信息', level=2)
    add_table(doc,
        ['步骤', '操作', '利用漏洞'],
        [
            ['1', '登录系统获取合法 session', '正常登录功能'],
            ['2', '遍历 /profile?user_id=1,2,3...', 'BL-01 水平越权 + BL-04 ID枚举'],
            ['3', '获取所有用户资料', '邮箱、手机号可用于钓鱼或撞库'],
        ],
        col_widths=[1, 8, 6]
    )

    doc.add_heading('攻击链 2：越权篡改余额', level=2)
    add_table(doc,
        ['步骤', '操作', '利用漏洞'],
        [
            ['1', '登录系统获取合法 session', '正常登录功能'],
            ['2', '提交 POST /recharge', '无频率限制 BL-05'],
            ['3', '修改隐藏字段 user_id=目标用户ID', 'BL-02 越权充值'],
            ['4', '填入负数 amount=-99999', 'BL-03 负金额扣款'],
            ['5', '目标用户余额被清空或变为负数', '直接经济损失'],
        ],
        col_widths=[1, 8, 6]
    )

    doc.add_heading('攻击链 3：组合攻击 — 全面破坏', level=2)
    add_table(doc,
        ['步骤', '操作', '利用漏洞'],
        [
            ['1', '编写自动化脚本', 'BL-04 枚举获得全部 user_id'],
            ['2', '遍历所有用户扣款', 'BL-02 + BL-03 + BL-05 叠加利用'],
            ['3', '系统所有用户余额归零', '业务完全瘫痪'],
            ['4', '数据库余额出现负数', '后续业务逻辑混乱'],
        ],
        col_widths=[1, 8, 6]
    )

    doc.add_page_break()

    # ═══════ 五、漏洞成因分析 ═══════
    doc.add_heading('五、漏洞成因分析', level=1)

    doc.add_heading('5.1 根因：信赖客户端传入的用户标识', level=2)
    doc.add_paragraph(
        '所有越权漏洞的根源在于：系统使用客户端传入的 user_id 作为用户身份标识，'
        '而没有与服务端 session 中保存的用户身份进行比对。'
        '在 Web 安全中，任何来自客户端的数据（URL 参数、表单字段、Cookie、HTTP 头）'
        '都是不可信的，必须经过服务端验证后方可使用。'
    )

    doc.add_heading('5.2 数据流对比', level=2)
    doc.add_paragraph('信任链分析（修复前 vs 修复后）：')
    add_table(doc,
        ['环节', '修复前（不安全）', '修复后（安全）'],
        [
            ['user_id 来源', 'URL 参数 / 表单隐藏字段（客户端可控）', 'Session（服务端存储，客户端不可篡改）'],
            ['身份校验', '无', '比对 session 中的用户身份与操作目标'],
            ['amount 校验', '无（正负均可）', '校验 amount > 0'],
            ['频率限制', '无', '复用 _check_rate_limit 框架'],
        ],
        col_widths=[3, 6, 6]
    )

    doc.add_heading('5.3 OWASP 分类映射', level=2)
    add_table(doc,
        ['OWASP 类别', '对应漏洞', '说明'],
        [
            ['A01:2024-Broken Access Control', 'BL-01, BL-02', '未对用户操作进行权限校验'],
            ['A04:2024-Insecure Design', 'BL-03, BL-05, BL-06', '业务逻辑设计缺陷'],
            ['A05:2024-Security Misconfiguration', 'BL-04', '使用可枚举的连续整数 ID'],
        ],
        col_widths=[6, 3.5, 5.5]
    )

    doc.add_page_break()

    # ═══════ 六、修复建议总结 ═══════
    doc.add_heading('六、修复建议总结', level=1)

    add_table(doc,
        ['#', '修复项', '对应漏洞', '优先级'],
        [
            ['1', 'profile 路由增加身份校验：只能查看自己的资料', 'BL-01', '🔴 立即'],
            ['2', 'recharge 路由从 session 获取用户身份，不信任前端 user_id', 'BL-02', '🔴 立即'],
            ['3', 'amount 仅接受正数，拒绝 <=0 的充值请求', 'BL-03', '🟠 尽快'],
            ['4', '使用 UUID 替代自增 ID 或配合身份校验防止枚举', 'BL-04', '🟠 尽快'],
            ['5', '添加上限频率限制（如 5 次/分钟）', 'BL-05', '🟡 建议'],
            ['6', '充值表单移除 user_id 隐藏字段', 'BL-06', '🟡 建议'],
        ],
        col_widths=[1, 10, 3, 2]
    )

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
    run = p.add_run('分析方式：Manual Code Review + Attack Path Simulation')
    run.font.size = Pt(10)
    run.font.color.rgb = RGBColor(0x99, 0x99, 0x99)

    # ── 保存 ──
    script_dir = os.path.dirname(os.path.abspath(__file__))
    output_path = os.path.join(script_dir, 'static', '业务逻辑及越权漏洞分析报告.docx')
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    doc.save(output_path)
    print(f'报告已生成：{output_path}')
    print(f'文件大小：{os.path.getsize(output_path) / 1024:.1f} KB')
    return output_path


if __name__ == '__main__':
    create_report()
