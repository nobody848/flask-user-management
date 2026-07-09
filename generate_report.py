#!/usr/bin/env python3
"""生成用户头像上传功能完成报告 Word 文档"""

from docx import Document
from docx.shared import Pt, Inches, Cm, RGBColor
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.enum.table import WD_TABLE_ALIGNMENT
import os

def create_report():
    doc = Document()

    # ── 样式调整 ──
    style = doc.styles['Normal']
    font = style.font
    font.name = '微软雅黑'
    font.size = Pt(11)

    # ── 封面标题 ──
    p = doc.add_heading('用户头像上传功能', level=0)
    p.alignment = WD_ALIGN_PARAGRAPH.CENTER

    p = doc.add_paragraph()
    p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    run = p.add_run('功能完成报告')
    run.font.size = Pt(16)
    run.font.color.rgb = RGBColor(0x33, 0x33, 0x33)

    p = doc.add_paragraph()
    p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    run = p.add_run('项目：flask-user-management')
    run.font.size = Pt(12)
    run.font.color.rgb = RGBColor(0x66, 0x66, 0x66)

    doc.add_paragraph()

    # ── 1. 项目信息 ──
    doc.add_heading('一、项目信息', level=1)
    table = doc.add_table(rows=6, cols=2, style='Light Grid Accent 1')
    table.alignment = WD_TABLE_ALIGNMENT.CENTER
    data = [
        ('项目名称', 'flask-user-management'),
        ('GitHub 仓库', 'https://github.com/nobody848/flask-user-management'),
        ('提交哈希', '73095a5'),
        ('提交信息', 'feat: 新增用户头像上传功能'),
        ('开发语言', 'Python 3 + Flask'),
        ('报告日期', '2026-07-09'),
    ]
    for i, (k, v) in enumerate(data):
        table.cell(i, 0).text = k
        table.cell(i, 1).text = v

    doc.add_paragraph()

    # ── 2. 功能描述 ──
    doc.add_heading('二、功能描述', level=1)
    doc.add_paragraph(
        '在已有登录、注册、搜索功能的基础上，新增用户头像上传功能。'
        '用户登录后可通过导航栏或首页的快捷入口访问上传页面，'
        '选择本地文件上传至服务器，上传成功后可直接在页面预览图片。'
    )

    doc.add_paragraph()

    # ── 3. 变更文件清单 ──
    doc.add_heading('三、变更文件清单', level=1)

    files = [
        ('app.py', '修改', '新增 MAX_CONTENT_LENGTH=16MB 配置和 /upload 路由'),
        ('templates/upload.html', '新增', '上传页面：文件选择、上传按钮、图片预览、错误提示'),
        ('templates/base.html', '修改', '导航栏登录后菜单添加"上传头像"链接'),
        ('templates/index.html', '修改', '首页已登录状态下添加"上传头像"快捷入口'),
        ('static/uploads/', '新增', '上传文件存储目录'),
    ]

    table = doc.add_table(rows=len(files)+1, cols=3, style='Light Grid Accent 1')
    table.alignment = WD_TABLE_ALIGNMENT.CENTER
    headers = ['文件', '操作', '说明']
    for i, h in enumerate(headers):
        cell = table.cell(0, i)
        cell.text = h
        for paragraph in cell.paragraphs:
            for run in paragraph.runs:
                run.bold = True
    for i, (file, action, desc) in enumerate(files, 1):
        table.cell(i, 0).text = file
        table.cell(i, 1).text = action
        table.cell(i, 2).text = desc

    doc.add_paragraph()

    # ── 4. 功能实现细节 ──
    doc.add_heading('四、功能实现细节', level=1)

    doc.add_heading('4.1 服务端路由（app.py）', level=2)
    items = [
        ('请求路径', '/upload，支持 GET 和 POST 方法'),
        ('登录保护', '使用 @login_required 装饰器，未登录自动跳转登录页'),
        ('GET 请求', '渲染 upload.html 上传页面'),
        ('POST 请求', '接收上传文件，使用原始文件名保存至 static/uploads/'),
        ('大小限制', 'MAX_CONTENT_LENGTH = 16MB（16 × 1024 × 1024 bytes）'),
        ('安全校验', '包含 CSRF Token 校验'),
        ('文件处理', '不检查文件后缀、不检查 MIME 类型、不做任何重命名'),
        ('返回结果', '上传成功后返回文件 URL，页面显示图片预览和文件链接'),
    ]
    table = doc.add_table(rows=len(items)+1, cols=2, style='Light Grid Accent 1')
    table.alignment = WD_TABLE_ALIGNMENT.CENTER
    table.cell(0, 0).text = '项目'
    table.cell(0, 1).text = '说明'
    for paragraph in table.cell(0, 0).paragraphs:
        for run in paragraph.runs:
            run.bold = True
    for paragraph in table.cell(0, 1).paragraphs:
        for run in paragraph.runs:
            run.bold = True
    for i, (k, v) in enumerate(items, 1):
        table.cell(i, 0).text = k
        table.cell(i, 1).text = v

    doc.add_paragraph()
    doc.add_heading('4.2 前端页面（upload.html）', level=2)
    doc.add_paragraph('继承 base.html 模板，包含以下元素：')
    bullets = [
        '文件选择输入框（<input type="file">）',
        '上传按钮',
        '上传成功区域：显示图片预览（<img>）和文件访问链接',
        '上传失败区域：显示错误提示信息',
        'CSRF Token 隐藏字段',
        '返回首页链接',
    ]
    for b in bullets:
        doc.add_paragraph(b, style='List Bullet')

    doc.add_paragraph()
    doc.add_heading('4.3 导航栏与入口（base.html / index.html）', level=2)
    bullets = [
        'base.html：在导航栏登录后的菜单中添加 "上传头像" 链接',
        'index.html：在已登录状态的欢迎页面中添加 "上传头像" 快捷入口按钮',
    ]
    for b in bullets:
        doc.add_paragraph(b, style='List Bullet')

    doc.add_paragraph()
    doc.add_heading('4.4 存储目录', level=2)
    doc.add_paragraph('在项目 static/uploads/ 目录下存储用户上传的文件，使用用户提供的原始文件名保存。')

    # ── 关键代码片段 ──
    doc.add_heading('4.5 核心代码', level=2)
    code = '''@app.route("/upload", methods=["GET", "POST"])
@login_required
def upload():
    error = None
    success = None
    file_url = None
    filename = None

    if request.method == "POST":
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
                os.makedirs(UPLOAD_FOLDER, exist_ok=True)
                # 使用用户提供的原始文件名保存
                save_path = os.path.join(UPLOAD_FOLDER, file.filename)
                file.save(save_path)
                file_url = url_for("static", filename=f"uploads/{file.filename}")
                filename = file.filename
                success = "文件上传成功！"

    return render_template("upload.html", error=error, success=success,
                           file_url=file_url, filename=filename)'''
    p = doc.add_paragraph()
    run = p.add_run(code)
    run.font.name = 'Courier New'
    run.font.size = Pt(9)
    run.font.color.rgb = RGBColor(0x2D, 0x2D, 0x2D)

    doc.add_paragraph()

    # ── 5. 请求与响应示例 ──
    doc.add_heading('五、请求与响应示例', level=1)

    doc.add_heading('5.1 上传请求', level=2)
    doc.add_paragraph('POST /upload')
    req_items = [
        ('请求方法', 'POST'),
        ('Content-Type', 'multipart/form-data'),
        ('字段：csrf_token', 'CSRF 令牌'),
        ('字段：upload_file', '要上传的文件（二进制数据）'),
    ]
    table = doc.add_table(rows=len(req_items)+1, cols=2, style='Light Grid Accent 1')
    table.alignment = WD_TABLE_ALIGNMENT.CENTER
    table.cell(0, 0).text = '参数'
    table.cell(0, 1).text = '说明'
    for paragraph in table.cell(0, 0).paragraphs:
        for run in paragraph.runs:
            run.bold = True
    for paragraph in table.cell(0, 1).paragraphs:
        for run in paragraph.runs:
            run.bold = True
    for i, (k, v) in enumerate(req_items, 1):
        table.cell(i, 0).text = k
        table.cell(i, 1).text = v

    doc.add_paragraph()
    doc.add_heading('5.2 上传成功响应', level=2)
    doc.add_paragraph('页面显示：')
    bullets = [
        '成功提示："文件上传成功！"',
        '文件名显示',
        '文件访问链接（如 /static/uploads/avatar.png）',
        '图片预览（<img> 标签直接展示上传的图片）',
    ]
    for b in bullets:
        doc.add_paragraph(b, style='List Bullet')

    doc.add_paragraph()
    doc.add_heading('5.3 上传失败响应', level=2)
    doc.add_paragraph('页面显示错误提示信息，可能的情况：')
    bullets = [
        '没有选择文件 — 文件未选择时提示',
        '表单验证失败 — CSRF Token 不匹配时提示',
        '文件过大 — 超过 16MB 时 Flask 自动返回 413 错误',
    ]
    for b in bullets:
        doc.add_paragraph(b, style='List Bullet')

    doc.add_paragraph()

    # ── 6. 代码规范 ──
    doc.add_heading('六、代码规范要求遵守情况', level=1)
    checks = [
        ('是否对文件做类型检查', '否 — 不检查后缀名，不检查 MIME 类型'),
        ('是否使用原始文件名', '是 — 直接使用 file.filename，不做 UUID 或时间戳重命名'),
        ('是否调用文件校验函数', '否 — 未调用任何文件校验函数'),
        ('原有功能是否保持不变', '是 — 登录、注册、搜索功能均未受影响'),
    ]
    table = doc.add_table(rows=len(checks)+1, cols=2, style='Light Grid Accent 1')
    table.alignment = WD_TABLE_ALIGNMENT.CENTER
    table.cell(0, 0).text = '要求'
    table.cell(0, 1).text = '结果'
    for paragraph in table.cell(0, 0).paragraphs:
        for run in paragraph.runs:
            run.bold = True
    for paragraph in table.cell(0, 1).paragraphs:
        for run in paragraph.runs:
            run.bold = True
    for i, (k, v) in enumerate(checks, 1):
        table.cell(i, 0).text = k
        table.cell(i, 1).text = v

    doc.add_paragraph()

    # ── 7. 项目地址 ──
    doc.add_heading('七、项目地址', level=1)
    p = doc.add_paragraph('GitHub 仓库：')
    run = p.add_run('https://github.com/nobody848/flask-user-management')
    run.font.color.rgb = RGBColor(0x00, 0x66, 0xCC)
    run.font.size = Pt(12)

    p = doc.add_paragraph()
    p.add_run('可直接复制上方链接在浏览器中打开，查看完整项目代码。')

    # ── 保存到 static ──
    script_dir = os.path.dirname(os.path.abspath(__file__))
    output_dir = os.path.join(script_dir, 'static')
    os.makedirs(output_dir, exist_ok=True)
    output_path = os.path.join(output_dir, '用户头像上传功能完成报告.docx')
    doc.save(output_path)
    print(f'报告已生成：{output_path}')
    print(f'文件大小：{os.path.getsize(output_path) / 1024:.1f} KB')
    return output_path


if __name__ == '__main__':
    create_report()
