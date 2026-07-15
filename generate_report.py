#!/usr/bin/env python3
"""生成SSRF漏洞测试与修复报告"""

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
    run = subtitle.add_run('SSRF 漏洞测试与修复报告')
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
        '报告日期：2026-07-13\n'
        '测试范围：/fetch-url 路由 SSRF 漏洞检测与修复\n'
        '提交哈希：b504f9e'
    )
    run.font.size = Pt(12)
    run.font.color.rgb = RGBColor(0x66, 0x66, 0x66)
    doc.add_page_break()

    # ══════════════════════════════════════
    # 一、SSRF 漏洞原理
    # ══════════════════════════════════════
    doc.add_heading('一、SSRF 漏洞原理', level=1)

    doc.add_paragraph(
        'SSRF（Server-Side Request Forgery，服务器端请求伪造）是一种 Web 安全漏洞，'
        '攻击者可以诱使服务器向攻击者指定的任意 URL 发起请求。由于请求是从服务器内部发出的，'
        '攻击者可以利用此漏洞访问内网服务、读取本地文件或进行端口扫描。'
    )

    doc.add_paragraph('SSRF 攻击的常见危害：')
    conds = [
        '内网服务探测：扫描内网 IP 和端口，发现未授权的内部服务',
        '云元数据窃取：访问云厂商元数据接口（如 169.254.169.254）获取临时凭证',
        '本地文件读取：使用 file:// 协议读取服务器上的敏感文件',
        '内网攻击：利用 SSRF 攻击内网的 Redis、Memcached 等未授权服务',
    ]
    for c in conds:
        doc.add_paragraph(c, style='List Bullet')

    doc.add_paragraph('本次测试针对的路由：')
    add_code(doc, '''POST /fetch-url
需要登录
接收 url 参数
使用 urllib.request.urlopen() 直接访问''')

    doc.add_page_break()

    # ══════════════════════════════════════
    # 二、漏洞发现
    # ══════════════════════════════════════
    doc.add_heading('二、漏洞发现', level=1)

    doc.add_heading('2.1 漏洞代码定位', level=2)
    doc.add_paragraph('审查 /fetch-url 路由时发现以下问题：')

    doc.add_heading('SSRF-01：未限制 URL 协议（高危）', level=3)
    doc.add_paragraph(
        'urlopen() 直接接收用户输入的 URL，未对协议做任何限制。'
        '攻击者可以使用 file://、gopher://、dict:// 等非 HTTP 协议绕过正常访问限制。'
    )
    add_code(doc, '''# ❌ 修复前：协议完全开放
req = urllib.request.Request(url)
with urllib.request.urlopen(req, timeout=10) as response:
    ...

# 攻击者可传入：
#   file:///etc/passwd      → 读取本地文件
#   gopher://localhost:6379 → Redis 攻击
#   dict://localhost:11211  → Memcached 攻击''')

    doc.add_heading('SSRF-02：未屏蔽内网地址（高危）', level=3)
    doc.add_paragraph(
        'urlopen() 可以访问内网 IP 地址，攻击者可以利用此功能探测内网服务、'
        '访问云元数据接口获取云服务临时凭证。'
    )
    add_code(doc, '''# ❌ 修复前：可访问任意地址
# 攻击者可传入：
#   http://127.0.0.1:5000/           → 自身服务
#   http://169.254.169.254/          → AWS/GCP/Azure 云元数据
#   http://10.0.0.1:6379/            → 内网 Redis
#   http://192.168.1.1:8080/         → 内网其他服务''')

    doc.add_page_break()

    # ══════════════════════════════════════
    # 三、攻击路径推演
    # ══════════════════════════════════════
    doc.add_heading('三、攻击路径推演', level=1)

    doc.add_heading('3.1 云元数据窃取攻击', level=2)
    add_table(doc,
        ['步骤', '操作', '说明'],
        [
            ['1', '攻击者登录系统', '获取合法 session'],
            ['2', '构造恶意 URL', 'http://169.254.169.254/latest/meta-data/'],
            ['3', '提交 POST /fetch-url', '服务器从内部请求云元数据接口'],
            ['4', '获取临时凭证', '返回结果中包含云服务访问密钥'],
            ['5', '利用凭证', '使用密钥访问云资源，造成数据泄露'],
        ],
        col_widths=[1, 4.5, 8.5]
    )

    doc.add_heading('3.2 内网 Redis 攻击', level=2)
    add_table(doc,
        ['步骤', '操作', '说明'],
        [
            ['1', '攻击者登录系统', '获取合法 session'],
            ['2', '探测内网 Redis', 'http://10.0.0.2:6379/'],
            ['3', '使用 gopher://', 'gopher://10.0.0.2:6379/_*1$8...'],
            ['4', '写入 SSH 密钥', '通过 Redis 未授权访问写入 SSH 公钥'],
            ['5', '远程登录服务器', '直接获得服务器 shell 权限'],
        ],
        col_widths=[1, 4.5, 8.5]
    )

    doc.add_heading('3.3 本地文件读取攻击', level=2)
    add_table(doc,
        ['步骤', '操作', '说明'],
        [
            ['1', '攻击者登录系统', '获取合法 session'],
            ['2', '构造恶意 URL', 'file:///etc/passwd'],
            ['3', '提交 POST /fetch-url', '服务器读取本地文件'],
            ['4', '返回文件内容', '攻击者获取系统用户列表'],
            ['5', '进一步攻击', '读取配置文件获取数据库密码等敏感信息'],
        ],
        col_widths=[1, 4.5, 8.5]
    )

    doc.add_page_break()

    # ══════════════════════════════════════
    # 四、修复方案
    # ══════════════════════════════════════
    doc.add_heading('四、修复方案', level=1)

    doc.add_paragraph(
        '针对两个 SSRF 漏洞分别新增 validate_url_protocol() 和 is_internal_ip() '
        '两个安全函数，在发起请求前对 URL 进行两次检查。'
    )

    doc.add_heading('4.1 修复 SSRF-01：协议校验', level=2)
    add_code(doc, '''def validate_url_protocol(url):
    """验证 URL 协议只允许 http/https"""
    if not url.startswith("http://") and not url.startswith("https://"):
        return False
    if url.startswith("http://localhost") or url.startswith("https://localhost"):
        return False
    return True''')

    doc.add_paragraph('该函数拦截以下协议：')
    doc.add_paragraph('file:// — 本地文件读取', style='List Bullet')
    doc.add_paragraph('gopher:// — 协议走私攻击', style='List Bullet')
    doc.add_paragraph('dict:// — Memcached/Redis 攻击', style='List Bullet')
    doc.add_paragraph('ftp:// — FTP 请求', style='List Bullet')
    doc.add_paragraph('http://localhost / https://localhost — localhost 绕过', style='List Bullet')

    doc.add_heading('4.2 修复 SSRF-02：内网 IP 屏蔽', level=2)
    add_code(doc, '''def is_internal_ip(host):
    """检查目标 IP 是否为内网地址"""
    try:
        ip = socket.gethostbyname(host)
        parts = ip.split(".")
        if parts[0] == "127":                 # 127.0.0.0/8
            return True
        if parts[0] == "10":                   # 10.0.0.0/8
            return True
        if parts[0] == "0":                    # 0.0.0.0/8
            return True
        if parts[0] == "169" and parts[1] == "254":  # 169.254.0.0/16
            return True
        if parts[0] == "192" and parts[1] == "168":  # 192.168.0.0/16
            return True
        if parts[0] == "172" and 16 <= int(parts[1]) <= 31:  # 172.16.0.0/12
            return True
        if host.lower() == "localhost":
            return True
        return False
    except Exception:
        return True''')

    doc.add_paragraph('该函数屏蔽的地址段：')
    doc.add_paragraph('127.0.0.0/8 — 回环地址（自身服务）', style='List Bullet')
    doc.add_paragraph('10.0.0.0/8 — A 类私有地址', style='List Bullet')
    doc.add_paragraph('172.16.0.0/12 — B 类私有地址', style='List Bullet')
    doc.add_paragraph('192.168.0.0/16 — C 类私有地址', style='List Bullet')
    doc.add_paragraph('169.254.0.0/16 — 链路本地地址（云元数据）', style='List Bullet')
    doc.add_paragraph('localhost — 主机名绕过', style='List Bullet')

    doc.add_heading('4.3 修复后的请求流程', level=2)
    add_code(doc, '''用户提交 URL
    │
    ├── validate_url_protocol()
    │   ├── 非 http/https → BLOCKED
    │   ├── localhost → BLOCKED
    │   └── 通过 → 继续
    │
    ├── is_internal_ip(urlparse(url).hostname)
    │   ├── 解析 host 到 IP
    │   ├── 内网 IP → BLOCKED
    │   └── 外网 IP → 继续
    │
    └── urllib.request.urlopen()
        └── 返回结果''')

    doc.add_page_break()

    # ══════════════════════════════════════
    # 五、测试验证
    # ══════════════════════════════════════
    doc.add_heading('五、测试验证', level=1)

    add_table(doc,
        ['编号', '测试用例', '输入 URL', '预期结果', '实际结果'],
        [
            ['T-01', 'file:// 协议', 'file:///etc/passwd', '协议拦截', '✅ 通过'],
            ['T-02', 'gopher:// 协议', 'gopher://internal:6379/', '协议拦截', '✅ 通过'],
            ['T-03', 'dict:// 协议', 'dict://localhost:11211/', '协议拦截', '✅ 通过'],
            ['T-04', '回环地址', 'http://127.0.0.1:5000/', '内网拦截', '✅ 通过'],
            ['T-05', 'localhost', 'http://localhost:5000/', '协议拦截', '✅ 通过'],
            ['T-06', 'A类私有', 'http://10.0.0.1/', '内网拦截', '✅ 通过'],
            ['T-07', 'B类私有', 'http://172.16.0.1/', '内网拦截', '✅ 通过'],
            ['T-08', 'C类私有', 'http://192.168.1.1/', '内网拦截', '✅ 通过'],
            ['T-09', '链路本地', 'http://169.254.169.254/', '内网拦截', '✅ 通过'],
            ['T-10', '正常外网', 'https://example.com', '正常抓取', '✅ 通过'],
            ['T-11', '未登录访问', '—', '302 跳转', '✅ 通过'],
        ],
        col_widths=[1.5, 3, 4.5, 2.5, 2.5]
    )

    doc.add_paragraph()

    # ══════════════════════════════════════
    # 六、安全防护对比
    # ══════════════════════════════════════
    doc.add_heading('六、安全防护对比', level=1)

    add_table(doc,
        ['攻击向量', '修复前', '修复后'],
        [
            ['file:// 读取本地文件', '❌ 可读取', '✅ 协议拦截'],
            ['gopher:// Redis 攻击', '❌ 可攻击', '✅ 协议拦截'],
            ['dict:// Memcached 攻击', '❌ 可攻击', '✅ 协议拦截'],
            ['127.0.0.1 自身服务', '❌ 可访问', '✅ 内网拦截'],
            ['localhost 绕过', '❌ 可访问', '✅ 协议拦截'],
            ['10.x.x.x 内网服务', '❌ 可扫描', '✅ 内网拦截'],
            ['172.16-31.x.x 内网服务', '❌ 可扫描', '✅ 内网拦截'],
            ['192.168.x.x 内网服务', '❌ 可扫描', '✅ 内网拦截'],
            ['169.254.169.254 云元数据', '❌ 可窃取', '✅ 内网拦截'],
            ['正常外网 URL', '✅ 可访问', '✅ 可访问'],
        ],
        col_widths=[5.5, 2.5, 2.5]
    )

    doc.add_page_break()

    # ══════════════════════════════════════
    # 七、漏洞汇总
    # ══════════════════════════════════════
    doc.add_heading('七、漏洞汇总', level=1)

    add_table(doc,
        ['编号', '漏洞名称', '严重', '发现位置', '状态'],
        [
            ['SSRF-01', 'URL 协议未限制', '🔴 高危', '/fetch-url 第534行', '✅ 已修复'],
            ['SSRF-02', '内网地址未屏蔽', '🔴 高危', '/fetch-url 第535行', '✅ 已修复'],
        ],
        col_widths=[2, 4, 2, 3.5, 3]
    )

    doc.add_paragraph()

    # ══════════════════════════════════════
    # 八、Git 提交记录
    # ══════════════════════════════════════
    doc.add_heading('八、Git 提交记录', level=1)

    add_table(doc,
        ['提交哈希', '提交信息', '涉及文件'],
        [
            ['b504f9e', 'fix: 修复SSRF漏洞（URL抓取功能）', 'app.py'],
        ],
        col_widths=[3, 7, 4]
    )

    doc.add_paragraph()

    p = doc.add_paragraph()
    p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    run = p.add_run('━' * 40)
    run.font.color.rgb = RGBColor(0xCC, 0xCC, 0xCC)

    p = doc.add_paragraph()
    p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    run = p.add_run('报告生成日期：2026-07-13')
    run.font.size = Pt(10)
    run.font.color.rgb = RGBColor(0x99, 0x99, 0x99)

    # ── 保存 ──
    script_dir = os.path.dirname(os.path.abspath(__file__))
    output_path = os.path.join(script_dir, 'static', 'SSRF漏洞测试与修复报告.docx')
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    doc.save(output_path)
    print(f'报告已生成：{output_path}')
    print(f'文件大小：{os.path.getsize(output_path) / 1024:.1f} KB')
    return output_path


if __name__ == '__main__':
    create_report()
