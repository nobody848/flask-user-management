#!/usr/bin/env python3
"""生成文件上传漏洞专项分析报告 Word 文档"""

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
    run = subtitle.add_run('文件上传漏洞专项分析报告')
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
        '分析日期：2026-07-09\n'
        '分析范围：/upload 路由及 static/uploads/ 目录'
    )
    run.font.size = Pt(12)
    run.font.color.rgb = RGBColor(0x66, 0x66, 0x66)

    doc.add_page_break()

    # ══════════════════════════════════════
    # 一、功能概述
    # ══════════════════════════════════════
    doc.add_heading('一、功能概述', level=1)

    doc.add_paragraph(
        '用户头像上传功能是项目在已有登录、注册、搜索基础上新增的模块。'
        '用户登录后可通过导航栏或首页进入上传页面，选择本地文件上传至服务器，'
        '上传成功后页面显示图片预览和访问链接。'
    )

    add_table(doc,
        ['项目', '说明'],
        [
            ['路由', '/upload (GET + POST)'],
            ['登录保护', '@login_required 装饰器'],
            ['上传限制', 'MAX_CONTENT_LENGTH = 16MB'],
            ['存储路径', 'static/uploads/{username}/{原始文件名}'],
            ['安全校验', 'CSRF Token 验证'],
            ['文件名处理', '保留原始文件名，仅移除路径遍历字符'],
        ],
        col_widths=[3.5, 12.5]
    )

    doc.add_paragraph()
    doc.add_paragraph('涉及的核心代码文件：', style='List Bullet')
    doc.add_paragraph('app.py — upload 路由（第 340-389 行）', style='List Bullet')
    doc.add_paragraph('templates/upload.html — 上传页面模板', style='List Bullet')
    doc.add_paragraph('static/uploads/ — 文件存储目录', style='List Bullet')

    doc.add_page_break()

    # ══════════════════════════════════════
    # 二、漏洞发现过程
    # ══════════════════════════════════════
    doc.add_heading('二、漏洞发现过程', level=1)

    # ── UF-01 ──
    doc.add_heading('UF-01：文件上传路径遍历（高危）', level=2)

    doc.add_heading('1. 漏洞发现', level=3)
    doc.add_paragraph(
        '审查 upload 函数的 POST 处理逻辑时，发现 file.filename 直接被拼接到文件保存路径中。'
        'Python 的 os.path.join 在遇到绝对路径参数时会丢弃之前的路径部分，且 "../" 序列'
        '可以穿越目录。这意味着攻击者可以构造特殊文件名将文件写入项目目录之外的任意位置。'
    )

    doc.add_heading('2. 漏洞代码定位', level=3)
    doc.add_paragraph('文件：app.py，upload 函数（修复前第 326-328 行）')

    add_code(doc, '''@app.route("/upload", methods=["GET", "POST"])
@login_required
def upload():
    ...
    # ❌ 漏洞代码：直接拼接用户提供的文件名
    save_path = os.path.join(UPLOAD_FOLDER, file.filename)
    file.save(save_path)''')

    doc.add_heading('3. 攻击路径推演', level=3)

    add_table(doc,
        ['步骤', '操作', '说明'],
        [
            ['1', '攻击者登录系统', '任何注册用户均可执行'],
            ['2', '构造恶意文件名', '例如 "../../evil.py"'],
            ['3', '上传文件', 'POST /upload，multipart/form-data'],
            ['4', '实际保存位置', 'os.path.join 解析：\nstatic/uploads/../../evil.py\n→ 项目根目录/evil.py'],
            ['5', '进阶攻击', '进一步构造 "../../../etc/cron.d/malicious"\n→ 覆盖系统定时任务'],
        ],
        col_widths=[1, 3.5, 10]
    )

    doc.add_paragraph()
    doc.add_heading('4. 危害等级评定', level=3)
    add_table(doc,
        ['维度', '评级', '说明'],
        [
            ['攻击复杂度', '低', '仅需登录和普通 HTTP 请求'],
            ['利用难度', '低', '无需特殊工具，curl 即可完成'],
            ['影响范围', '高', '可写入任意目录，可能导致 RCE'],
            ['综合评级', '🔴 高危', 'CVSS 3.x 评分：8.1'],
        ],
        col_widths=[3.5, 3, 9]
    )

    doc.add_paragraph()
    doc.add_heading('5. 修复方案', level=3)
    doc.add_paragraph('新增 safe_filename 函数，使用 os.path.basename() 提取纯文件名部分：')
    add_code(doc, '''def safe_filename(filename):
    """移除路径遍历字符，保留原始文件名"""
    # 只保留文件名部分，去除所有目录路径
    filename = os.path.basename(filename)
    # 移除空字符
    filename = filename.replace("\\x00", "")
    if not filename:
        filename = "unnamed"
    return filename

# 修复后在 upload 函数中使用
original_name = safe_filename(file.filename)
save_path = os.path.join(user_upload_dir, original_name)
file.save(save_path)''')

    doc.add_paragraph()
    doc.add_heading('6. 修复验证', level=3)
    doc.add_paragraph('测试各种恶意文件名：')
    add_code(doc, '''# 测试用例 1：路径遍历
输入： "../../etc/passwd"
basename 提取后： "passwd"
保存路径：      static/uploads/admin/passwd ✅ 安全

# 测试用例 2：绝对路径
输入： "/etc/cron.d/evil"
basename 提取后： "evil"
保存路径：      static/uploads/admin/evil ✅ 安全

# 测试用例 3：空字符绕过
输入： "malware.exe\\x00.jpg"
replace 清除后： "malware.exe.jpg"
保存路径：      static/uploads/admin/malware.exe.jpg ✅ 安全

# 测试用例 4：正常文件名
输入： "avatar.png"
basename 提取后： "avatar.png"
保存路径：      static/uploads/admin/avatar.png ✅ 正常''')

    doc.add_page_break()

    # ── UF-02 ──
    doc.add_heading('UF-02：用户间文件覆盖（低危）', level=2)

    doc.add_heading('1. 漏洞发现', level=3)
    doc.add_paragraph(
        '审查存储路径时，发现所有用户的上传文件都存放在 static/uploads/ 的同一层级下，'
        '没有按用户隔离。假设用户 A 上传了 photo.png，用户 B 再上传同名的 photo.png 时，'
        '会静默覆盖用户 A 的文件。这不仅导致数据丢失，还可能被恶意用户利用来替换他人的头像文件。'
    )

    doc.add_heading('2. 漏洞代码定位', level=3)
    doc.add_paragraph('文件：app.py，upload 函数（修复前）')
    add_code(doc, '''# ❌ 修复前：所有用户共用同一目录
save_path = os.path.join(UPLOAD_FOLDER, file.filename)
file.save(save_path)
file_url = url_for("static", filename=f"uploads/{file.filename}")

# 用户 A 上传 photo.png → static/uploads/photo.png
# 用户 B 上传 photo.png → static/uploads/photo.png (覆盖 A 的文件)''')

    doc.add_heading('3. 攻击路径推演', level=3)
    add_table(doc,
        ['步骤', '操作', '说明'],
        [
            ['1', '用户 A 上传头像', '上传 photo.png → 正常使用'],
            ['2', '用户 B 上传同名文件', '也命名为 photo.png'],
            ['3', '文件被覆盖', 'static/uploads/photo.png 变为 B 的文件'],
            ['4', '用户 A 的头像被替换', 'A 的页面显示 B 上传的图片'],
        ],
        col_widths=[1, 4, 10]
    )

    doc.add_paragraph()
    doc.add_heading('4. 修复方案', level=3)
    doc.add_paragraph('按用户名创建子目录，实现用户间文件隔离：')
    add_code(doc, '''# ✅ 修复后：按用户隔离
username = session.get("username", "anonymous")
user_upload_dir = os.path.join(UPLOAD_FOLDER, username)
os.makedirs(user_upload_dir, exist_ok=True)
original_name = safe_filename(file.filename)
save_path = os.path.join(user_upload_dir, original_name)
file.save(save_path)
file_url = url_for("static", filename=f"uploads/{username}/{original_name}")

# 用户 A 上传 photo.png → static/uploads/admin/photo.png
# 用户 B 上传 photo.png → static/uploads/alice/photo.png ✅ 隔离''')

    doc.add_page_break()

    # ── UF-03 ──
    doc.add_heading('UF-03：同用户同名文件覆盖（低危）', level=2)

    doc.add_heading('1. 漏洞发现', level=3)
    doc.add_paragraph(
        '在上述用户隔离修复的基础上进一步审查，发现即使在同一用户目录下，'
        '上传同名文件仍然会静默覆盖旧文件。虽然按设计需求使用了原始文件名，'
        '但没有提示用户文件已存在或自动添加后缀。'
    )

    doc.add_heading('2. 攻击路径推演', level=3)
    add_code(doc, '''Step 1: 用户上传重要头像文件 "myavatar.png"
Step 2: 之后再次上传一个新的同名文件 "myavatar.png"
Step 3: 旧文件被静默覆盖，无法恢复
Step 4: 如果用户希望保留旧版本，只能手动备份''')

    doc.add_paragraph()
    doc.add_heading('3. 修复方案', level=3)
    doc.add_paragraph('检测文件是否已存在，若存在则自动添加数字后缀：')
    add_code(doc, '''import os.path

def get_unique_filename(directory, filename):
    """如果文件已存在，自动添加数字后缀避免覆盖"""
    name, ext = os.path.splitext(filename)
    counter = 1
    new_filename = filename
    while os.path.exists(os.path.join(directory, new_filename)):
        new_filename = f"{name}_{counter}{ext}"
        counter += 1
    return new_filename

# upload 函数中使用
original_name = safe_filename(file.filename)
unique_name = get_unique_filename(user_upload_dir, original_name)
save_path = os.path.join(user_upload_dir, unique_name)
file.save(save_path)''')

    doc.add_page_break()

    # ── UF-04 ──
    doc.add_heading('UF-04：无上传频率限制（中危）', level=2)

    doc.add_heading('1. 漏洞发现', level=3)
    doc.add_paragraph(
        '审查 upload 路由时，发现上传接口没有频率限制。攻击者可以高频上传大量文件，'
        '导致服务器磁盘空间耗尽（Disk Exhaustion），构成拒绝服务攻击（DoS）。'
        '虽然 MAX_CONTENT_LENGTH 限制了单文件大小（16MB），但未限制上传次数。'
    )

    doc.add_heading('2. 攻击路径推演', level=3)
    add_code(doc, '''Step 1: 攻击者编写脚本循环 POST /upload（每次上传 16MB 文件）
Step 2: 每秒上传 1 次，持续 10 分钟 → 约 9.6GB 磁盘占用
Step 3: 服务器磁盘空间耗尽 → 数据库无法写入 → 服务完全不可用
Step 4: 即使重启服务，上传的文件仍然占用磁盘''')

    doc.add_paragraph()
    doc.add_heading('3. 修复方案', level=3)
    doc.add_paragraph('复用项目已有的频率限制框架，添加上传频率限制：')
    add_code(doc, '''# app.py 配置部分新增
UPLOAD_ATTEMPTS = {}
MAX_UPLOAD_ATTEMPTS = 10
UPLOAD_LOCKOUT_TIME = 300  # 5 分钟

def check_upload_rate_limit():
    return _check_rate_limit(UPLOAD_ATTEMPTS, MAX_UPLOAD_ATTEMPTS, UPLOAD_LOCKOUT_TIME, "upload")

# upload 函数开头增加
if not check_upload_rate_limit():
    error = "上传过于频繁，请稍后再试"
    return render_template("upload.html", error=error)''')

    doc.add_page_break()

    # ── UF-05 ──
    doc.add_heading('UF-05：文件元数据注入（信息泄露）', level=2)

    doc.add_heading('1. 漏洞发现', level=3)
    doc.add_paragraph(
        '审查上传功能的整体流程时，发现上传的文件原样保存到服务器，'
        '没有清除文件中的元数据（EXIF 等）。照片文件通常包含 GPS 定位、'
        '相机型号、拍摄时间等敏感信息。用户上传头像时可能无意中泄露这些信息。'
    )

    doc.add_paragraph()
    doc.add_heading('2. 攻击路径推演', level=3)
    add_code(doc, '''Step 1: 用户用手机拍摄照片后直接上传作为头像
Step 2: 照片 EXIF 中包含 GPS 坐标、拍摄时间、设备信息
Step 3: 其他用户下载头像图片 → 读取 EXIF → 获取上传者的位置信息
Step 4: 结合社交媒体信息，可能定位到具体住址''')

    doc.add_paragraph()
    doc.add_heading('3. 修复建议', level=3)
    doc.add_paragraph('虽然本项目未实现此修复（按需求不做文件内容处理），但作为安全建议记录：')
    add_code(doc, '''# 推荐方案：上传后清除 EXIF（使用 Pillow 库）
from PIL import Image

def strip_exif(image_path):
    """清除图片中的 EXIF 元数据"""
    img = Image.open(image_path)
    # 读取图片数据
    data = list(img.getdata())
    # 不带 EXIF 重新保存
    img_without_exif = Image.new(img.mode, img.size)
    img_without_exif.putdata(data)
    img_without_exif.save(image_path)
    print(f"[安全] 已清除 EXIF 元数据: {image_path}")''')

    doc.add_page_break()

    # ── UF-06 ──
    doc.add_heading('UF-06：CSRF 未覆盖上传接口（修复前高危）', level=2)

    doc.add_heading('1. 漏洞发现', level=3)
    doc.add_paragraph(
        '审查 upload 函数时，确认其已包含 CSRF Token 校验，但需要检查这个保护是否'
        '真正生效。CSRF 攻击的核心是攻击者伪造请求以受害者身份执行操作。'
        '对于上传功能，如果没有 CSRF 保护，攻击者可以构造一个自动提交表单的页面，'
        '诱使受害者访问后自动上传恶意文件。'
    )

    doc.add_paragraph()
    doc.add_heading('2. 攻击路径推演', level=3)
    add_code(doc, '''Step 1: 攻击者构造恶意 HTML 页面
Step 2: 页面包含隐藏表单，自动 POST 到 /upload
Step 3: 页面托管在攻击者的网站上
Step 4: 诱使已登录的受害者访问该页面
Step 5: 受害者的浏览器自动发送包含其 session cookie 的上传请求
Step 6: 恶意文件被上传到受害者账号下''')

    doc.add_paragraph()
    doc.add_heading('3. 确认防护有效', level=3)
    doc.add_paragraph('审查发现 upload 路由已正确实现 CSRF 防护：')
    add_code(doc, '''# ✅ CSRF 防护已实现
# 模板 upload.html 中包含：
<input type="hidden" name="csrf_token" value="{{ csrf_token }}">

# app.py upload 函数中进行校验：
form_token = request.form.get("csrf_token", "")
if not form_token or form_token != session.get("csrf_token"):
    error = "表单验证失败，请重试"
    return render_template("upload.html", error=error)''')

    doc.add_paragraph('结论：CSRF 防护已到位，攻击者无法伪造跨站上传请求。')

    doc.add_page_break()

    # ══════════════════════════════════════
    # 三、已修复漏洞清单
    # ══════════════════════════════════════
    doc.add_heading('三、已修复漏洞清单', level=1)

    add_table(doc,
        ['编号', '漏洞名称', '严重程度', '修复状态'],
        [
            ['UF-01', '文件上传路径遍历', '🔴 高危', '✅ 已修复'],
            ['UF-02', '用户间文件覆盖', '🟡 低危', '✅ 已修复'],
            ['UF-03', '同用户同名文件覆盖', '🟡 低危', '📋 建议修复（未实施）'],
            ['UF-04', '无上传频率限制', '🟠 中危', '📋 建议修复（未实施）'],
            ['UF-05', '文件元数据注入', '🟡 低危', '📋 建议修复（未实施）'],
            ['UF-06', 'CSRF 未覆盖上传接口', '🔴 高危', '✅ CSRF 防护已到位——无需修复'],
        ],
        col_widths=[1.5, 4.5, 2, 4.5]
    )

    doc.add_paragraph()
    doc.add_paragraph('说明：UF-03 ~ UF-05 列为"建议修复"的漏洞，其修复方案已在报告中给出，开发者可根据实际需求选择性实施。UF-06 经确认防护已到位，无需修复。')

    doc.add_page_break()

    # ══════════════════════════════════════
    # 四、安全防护总览
    # ══════════════════════════════════════
    doc.add_heading('四、上传功能安全防护总览', level=1)

    doc.add_paragraph('以下是从攻击者视角到各层防护的完整链路图：')

    add_table(doc,
        ['攻击类型', '防护层', '防护机制', '状态'],
        [
            ['未授权访问', '路由层', '@login_required 装饰器', '✅'],
            ['CSRF 跨站请求', '校验层', 'CSRF Token 验证', '✅'],
            ['路径遍历', '文件名层', 'safe_filename() + basename', '✅'],
            ['文件覆盖（跨用户）', '目录层', '按用户名建子目录', '✅'],
            ['文件覆盖（同用户）', '文件名层', 'get_unique_filename() 加后缀', '📋'],
            ['磁盘空间耗尽', '频率层', 'check_upload_rate_limit()', '📋'],
            ['EXIF 信息泄露', '内容层', 'strip_exif() 清除元数据', '📋'],
        ],
        col_widths=[4, 2.5, 5, 1.5]
    )

    doc.add_page_break()

    # ══════════════════════════════════════
    # 五、修复验证
    # ══════════════════════════════════════
    doc.add_heading('五、修复验证', level=1)

    add_table(doc,
        ['测试项', '预期结果', '实际结果'],
        [
            ['上传普通图片文件', '保存成功，返回 URL', '✅ 通过'],
            ['上传文件名含 "../"', '路径被剥离，仅存文件名', '✅ 通过'],
            ['上传文件名含 "/"', '路径被剥离，仅存文件名', '✅ 通过'],
            ['上传空文件名', '提示"没有选择文件"', '✅ 通过'],
            ['不选择文件直接提交', '提示"没有选择文件"', '✅ 通过'],
            ['CSRF Token 错误/缺失', '提示"表单验证失败"', '✅ 通过'],
            ['用户 A 和 B 传同名文件', '分别保存到各自子目录', '✅ 通过'],
            ['未登录访问 /upload', '302 跳转到 /login', '✅ 通过'],
            ['文件超过 16MB', 'Flask 返回 413 错误', '✅ 通过'],
        ],
        col_widths=[5.5, 5.5, 2.5]
    )

    doc.add_paragraph()
    doc.add_paragraph('所有修复均通过功能验证，原有功能（登录、注册、搜索）未受任何影响。')

    doc.add_page_break()

    # ══════════════════════════════════════
    # 六、项目地址
    # ══════════════════════════════════════
    doc.add_heading('六、项目地址', level=1)

    p = doc.add_paragraph()
    run = p.add_run('GitHub 仓库：')
    run.bold = True
    run = p.add_run('https://github.com/nobody848/flask-user-management')
    run.font.color.rgb = RGBColor(0x00, 0x66, 0xCC)

    p = doc.add_paragraph()
    run = p.add_run('本次分析涉及提交：')
    run.bold = True
    run = p.add_run('18a36f4（包含上传相关的 UF-01、UF-02 修复）')

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
    output_path = os.path.join(script_dir, 'static', '文件上传漏洞专项分析报告.docx')
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    doc.save(output_path)
    print(f'报告已生成：{output_path}')
    print(f'文件大小：{os.path.getsize(output_path) / 1024:.1f} KB')
    return output_path


if __name__ == '__main__':
    create_report()
