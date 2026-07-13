#!/usr/bin/env python3
"""生成文件上传漏洞修复与测试报告"""

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
    run = subtitle.add_run('文件上传漏洞修复与测试报告')
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
        '分析范围：/upload 路由 · safe_filename 函数 · static/uploads/ 目录\n'
        '提交哈希：352b3b6'
    )
    run.font.size = Pt(12)
    run.font.color.rgb = RGBColor(0x66, 0x66, 0x66)
    doc.add_page_break()

    # ══════════════════════════════════════
    # 一、文件上传功能概述
    # ══════════════════════════════════════
    doc.add_heading('一、文件上传功能概述', level=1)

    doc.add_paragraph(
        '用户头像上传功能是在已有登录、注册、搜索功能基础上新增的模块。'
        '用户登录后可通过导航栏或首页进入上传页面，选择本地文件上传至服务器，'
        '上传成功后页面显示图片预览和访问链接。'
    )

    add_table(doc,
        ['项目', '说明'],
        [
            ['路由', '/upload (GET + POST)'],
            ['登录保护', '@login_required 装饰器，未登录跳转 /login'],
            ['文件大小限制', 'MAX_CONTENT_LENGTH = 16MB'],
            ['存储路径', 'static/uploads/{username}/{原始文件名}'],
            ['安全校验', 'CSRF Token 验证'],
            ['文件名处理', 'safe_filename() 移除路径遍历字符'],
        ],
        col_widths=[4, 12]
    )

    doc.add_paragraph()
    doc.add_paragraph('相关源代码文件：', style='List Bullet')
    doc.add_paragraph('app.py — upload 路由（第 393-442 行）及 safe_filename 函数（第 397-405 行）', style='List Bullet')
    doc.add_paragraph('templates/upload.html — 上传页面模板', style='List Bullet')
    doc.add_paragraph('static/uploads/ — 文件存储根目录', style='List Bullet')
    doc.add_paragraph('static/css/style.css — 上传页面样式（第 269-308 行）', style='List Bullet')

    doc.add_page_break()

    # ══════════════════════════════════════
    # 二、上传功能代码详解
    # ══════════════════════════════════════
    doc.add_heading('二、上传功能代码详解', level=1)

    doc.add_heading('2.1 safe_filename 安全函数', level=2)
    doc.add_paragraph('该函数负责处理用户上传文件的文件名，移除可能的安全风险：')
    add_code(doc, '''def safe_filename(filename):
    """移除路径遍历字符，保留原始文件名"""
    # 只保留文件名部分，去除目录路径
    filename = os.path.basename(filename)
    # 移除空字符
    filename = filename.replace("\\x00", "")
    if not filename:
        filename = "unnamed"
    return filename''')
    doc.add_paragraph('处理逻辑说明：')
    doc.add_paragraph('① os.path.basename() 提取纯文件名，去除所有目录路径成分', style='List Bullet')
    doc.add_paragraph('② 替换空字符 \\x00 防止空字符截断攻击', style='List Bullet')
    doc.add_paragraph('③ 空文件名兜底为 "unnamed"', style='List Bullet')

    doc.add_paragraph()
    doc.add_heading('2.2 upload 路由完整代码', level=2)
    add_code(doc, '''@app.route("/upload", methods=["GET", "POST"])
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
            return render_template("upload.html", error=error, ...)

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
                file_url = url_for("static",
                    filename=f"uploads/{username}/{original_name}")
                filename = original_name
                success = "文件上传成功！"

    return render_template("upload.html", error=error, success=success,
                           file_url=file_url, filename=filename)''')

    doc.add_paragraph('路由处理流程：')
    doc.add_paragraph('① GET 请求直接渲染 upload.html 上传页面', style='List Bullet')
    doc.add_paragraph('② POST 请求先进行 CSRF Token 校验', style='List Bullet')
    doc.add_paragraph('③ 检查是否有文件被提交，文件名是否为空', style='List Bullet')
    doc.add_paragraph('④ 按用户名创建子目录实现用户间隔离', style='List Bullet')
    doc.add_paragraph('⑤ 调用 safe_filename 处理文件名', style='List Bullet')
    doc.add_paragraph('⑥ 保存文件并生成访问 URL', style='List Bullet')

    doc.add_page_break()

    # ══════════════════════════════════════
    # 三、漏洞发现与修复
    # ══════════════════════════════════════
    doc.add_heading('三、漏洞发现与修复', level=1)

    # ── UF-01 路径遍历 ──
    doc.add_heading('UF-01：文件上传路径遍历漏洞（高危）', level=2)

    doc.add_heading('3.1 漏洞发现', level=3)
    doc.add_paragraph(
        '审查 upload 函数的 POST 处理逻辑时，发现 file.filename 直接被拼接到文件保存路径中。'
        'Python 的 os.path.join 在处理绝对路径参数时会丢弃之前的路径部分，'
        '且 "../" 序列可以穿越目录。'
        '攻击者可以构造恶意文件名将文件写入项目目录之外的任意位置。'
    )

    doc.add_heading('3.2 漏洞代码（修复前）', level=3)
    add_code(doc, '''# ❌ 修复前：直接拼接用户提供的文件名
save_path = os.path.join(UPLOAD_FOLDER, file.filename)
file.save(save_path)

# 攻击者可提交 filename="../../../etc/cronjob.sh"
# os.path.join 解析后 → 项目根目录/../etc/cronjob.sh → /etc/cronjob.sh''')

    doc.add_heading('3.3 攻击路径推演', level=3)
    add_table(doc,
        ['步骤', '操作', '说明'],
        [
            ['1', '攻击者登录系统', '任何注册用户均可执行'],
            ['2', '构造恶意文件名', '例如 "../../etc/cronjob.sh"'],
            ['3', '上传文件', 'POST /upload，multipart/form-data'],
            ['4', '文件写入任意目录', 'os.path.join 解析静态路径 + ../ 穿越到系统目录'],
            ['5', '进阶攻击', '覆盖系统定时任务或启动脚本，实现远程代码执行'],
        ],
        col_widths=[1.2, 3.5, 10]
    )

    doc.add_heading('3.4 修复方案', level=3)
    doc.add_paragraph('新增 safe_filename 函数，使用 os.path.basename() 提取纯文件名部分，'
                       '从源头阻断目录穿越：')
    add_code(doc, '''def safe_filename(filename):
    """移除路径遍历字符，保留原始文件名"""
    filename = os.path.basename(filename)  # 只保留文件名
    filename = filename.replace("\\x00", "")  # 移除空字符
    if not filename:
        filename = "unnamed"
    return filename

# 修复后在 upload 函数中使用
original_name = safe_filename(file.filename)
save_path = os.path.join(user_upload_dir, original_name)
file.save(save_path)''')

    doc.add_paragraph()
    # ── UF-02 用户隔离 ──
    doc.add_heading('UF-02：跨用户文件覆盖漏洞（低危）', level=2)

    doc.add_heading('3.5 漏洞发现', level=3)
    doc.add_paragraph(
        '审查存储路径时，发现所有用户的上传文件都存放在 static/uploads/ 的同一层级下，'
        '没有按用户隔离。用户 A 上传 photo.png 后，用户 B 再上传同名的 photo.png 时，'
        '会静默覆盖用户 A 的文件。'
    )

    doc.add_heading('3.6 漏洞代码（修复前）', level=3)
    add_code(doc, '''# ❌ 修复前：所有用户共用同一目录
save_path = os.path.join(UPLOAD_FOLDER, file.filename)
file_url = url_for("static", filename=f"uploads/{file.filename}")

# 用户 A 上传 photo.png → static/uploads/photo.png
# 用户 B 上传 photo.png → static/uploads/photo.png (覆盖 A 的文件)''')

    doc.add_heading('3.7 修复方案', level=3)
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
# 用户 B 上传 photo.png → static/uploads/alice/photo.png ✅''')


    doc.add_paragraph()
    # ── UF-03 CSRF ──
    doc.add_heading('UF-03：CSRF 跨站请求伪造防护（高危）', level=2)

    doc.add_heading('3.8 防护确认', level=3)
    doc.add_paragraph(
        '审查 upload 函数时，确认其已包含 CSRF Token 校验。'
        'CSRF 攻击的核心是攻击者伪造请求以受害者身份执行操作。'
        '对于上传功能，如果没有 CSRF 保护，攻击者可以构造一个自动提交表单的页面，'
        '诱使受害者访问后自动上传恶意文件。'
    )
    doc.add_paragraph('经审查，CSRF 防护已正确实现，无需修复：')
    add_code(doc, '''# 模板 upload.html 中包含 CSRF Token：
<input type="hidden" name="csrf_token" value="{{ csrf_token }}">

# app.py upload 函数中进行校验：
form_token = request.form.get("csrf_token", "")
if not form_token or form_token != session.get("csrf_token"):
    error = "表单验证失败，请重试"
    return render_template("upload.html", error=error, ...)''')

    doc.add_page_break()

    # ══════════════════════════════════════
    # 四、修复验证测试
    # ══════════════════════════════════════
    doc.add_heading('四、修复验证测试', level=1)

    doc.add_heading('4.1 路径遍历防护测试', level=2)
    add_table(doc,
        ['测试用例', '输入文件名', '处理后文件名', '保存路径', '结果'],
        [
            ['正常文件', 'avatar.png', 'avatar.png', 'static/uploads/admin/avatar.png', '✅ 正常'],
            ['相对路径', '../../etc/passwd', 'passwd', 'static/uploads/admin/passwd', '✅ 安全'],
            ['绝对路径', '/etc/cron.d/evil', 'evil', 'static/uploads/admin/evil', '✅ 安全'],
            ['多层穿越', '../../../../a.txt', 'a.txt', 'static/uploads/admin/a.txt', '✅ 安全'],
            ['空字符绕过', 'malware.exe\\x00.jpg', 'malware.exe.jpg', 'static/uploads/admin/malware.exe.jpg', '✅ 安全'],
            ['空文件名', '', 'unnamed', 'static/uploads/admin/unnamed', '✅ 兜底'],
        ],
        col_widths=[2.5, 3.5, 3.5, 4.5, 2]
    )

    doc.add_paragraph()
    doc.add_heading('4.2 用户隔离测试', level=2)
    add_table(doc,
        ['场景', '操作', '预期', '结果'],
        [
            ['admin 上传 photo.png', 'POST /upload → photo.png', 'admin 目录保存', '✅ 通过'],
            ['alice 上传同名 photo.png', 'POST /upload → photo.png', 'alice 目录保存', '✅ 通过'],
            ['admin 的文件是否被覆盖', '检查 admin 目录文件', 'admin/photo.png 仍在', '✅ 未覆盖'],
        ],
        col_widths=[4, 4.5, 4, 2]
    )

    doc.add_paragraph()
    doc.add_heading('4.3 安全校验测试', level=2)
    add_table(doc,
        ['测试项', '操作', '预期', '结果'],
        [
            ['未登录访问上传页', 'GET /upload', '302 跳转 /login', '✅ 通过'],
            ['无 CSRF Token 上传', 'POST /upload (无 csrf_token)', '提示"表单验证失败"', '✅ 通过'],
            ['CSRF Token 错误', 'POST /upload (错误 token)', '提示"表单验证失败"', '✅ 通过'],
            ['不选文件直接提交', 'POST /upload (无文件)', '提示"没有选择文件"', '✅ 通过'],
            ['空文件名提交', 'POST /upload (文件名空)', '提示"没有选择文件"', '✅ 通过'],
            ['文件超过 16MB', '上传 >16MB 文件', 'Flask 413 错误', '✅ 通过'],
        ],
        col_widths=[4, 4.5, 4.5, 2]
    )

    doc.add_paragraph()
    doc.add_heading('4.4 功能完整性测试', level=2)
    add_table(doc,
        ['测试项', '操作', '预期', '结果'],
        [
            ['正常上传图片', '选择图片文件 → 点击上传', '显示预览和链接', '✅ 通过'],
            ['上传后文件可访问', '点击返回的 URL', '图片正常显示', '✅ 通过'],
            ['上传页返回首页', '点击"返回首页"', '跳转到首页', '✅ 通过'],
        ],
        col_widths=[4, 5, 4.5, 2]
    )

    doc.add_page_break()

    # ══════════════════════════════════════
    # 五、安全防护总览
    # ══════════════════════════════════════
    doc.add_heading('五、安全防护总览', level=1)

    add_table(doc,
        ['攻击类型', '防护层', '防护机制', '状态'],
        [
            ['未授权上传', '路由层', '@login_required 装饰器', '✅ 已防护'],
            ['CSRF 跨站上传', '校验层', 'CSRF Token 匹配验证', '✅ 已防护'],
            ['路径遍历', '文件名层', 'safe_filename() + basename', '✅ 已修复'],
            ['文件覆盖（跨用户）', '目录层', '按用户名建子目录', '✅ 已修复'],
            ['文件过大', '配置层', 'MAX_CONTENT_LENGTH = 16MB', '✅ 已防护'],
            ['文件类型绕过', '需求设计', '不检查后缀和 MIME', '📋 设计如此'],
        ],
        col_widths=[3.5, 2.5, 5.5, 2.5]
    )

    doc.add_paragraph()

    # ══════════════════════════════════════
    # 六、Git 提交记录
    # ══════════════════════════════════════
    doc.add_heading('六、Git 提交记录', level=1)

    add_table(doc,
        ['提交哈希', '提交信息', '涉及文件'],
        [
            ['73095a5', 'feat: 新增用户头像上传功能', 'app.py, upload.html, base.html, index.html'],
            ['18a36f4', 'fix: 修复8项安全漏洞（含UF-01, UF-02）', 'app.py'],
            ['352b3b6', 'fix: 修复4项安全漏洞（VS-01~04）', 'app.py'],
        ],
        col_widths=[3, 6, 6]
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
    output_path = os.path.join(script_dir, 'static', '文件上传漏洞修复与测试报告.docx')
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    doc.save(output_path)
    print(f'报告已生成：{output_path}')
    print(f'文件大小：{os.path.getsize(output_path) / 1024:.1f} KB')
    return output_path


if __name__ == '__main__':
    create_report()
