# Flask 用户管理系统 — 安全审计报告

---

## 一、项目概述

| 项目 | 内容 |
|------|------|
| **项目名称** | flask-user-management |
| **技术栈** | Python Flask + Jinja2 + HTML/CSS |
| **审计目的** | 检测并修复 Web 应用常见安全漏洞 |
| **仓库地址** | https://github.com/nobody848/flask-user-management |
| **审计日期** | 2026-07-07 |

---

## 二、检测范围

审计覆盖全部 5 个源文件：

| 文件 | 行数 | 功能 |
|------|------|------|
| `app.py` | 62 行 | Flask 主应用逻辑 |
| `templates/base.html` | 25 行 | 基础布局模板 |
| `templates/index.html` | 23 行 | 首页/用户信息展示 |
| `templates/login.html` | 20 行 | 登录页面 |
| `static/css/style.css` | 202 行 | 全局样式 |

---

## 三、漏洞汇总

| 编号 | 漏洞名称 | 文件 | 行号 | 严重程度 | CVSS 类比 |
|------|----------|------|------|----------|-----------|
| V-01 | HTML 注释泄露默认账号密码 | `templates/login.html` | 第 1 行 | 🔴 严重 | 7.5 |
| V-02 | 密码明文展示在首页页面 | `templates/index.html` | 第 10 行 | 🔴 严重 | 7.5 |
| V-03 | 明文密码存储（无哈希） | `app.py` | 第 10-23 行 | 🔴 严重 | 9.1 |
| V-04 | 弱 Secret Key 可伪造 Session | `app.py` | 第 4 行 | 🔴 严重 | 8.6 |
| V-05 | Debug 模式开启导致 RCE 风险 | `app.py` | 第 62 行 | 🟠 高 | 7.8 |
| V-06 | 监听 0.0.0.0 扩大攻击面 | `app.py` | 第 62 行 | 🟠 中 | 5.1 |
| V-07 | 密码字段从后端传递到前端模板 | `app.py` | 第 32/47 行 | 🟡 中 | 4.3 |

---

## 四、漏洞详细分析

### V-01：HTML 注释泄露默认账号密码

**文件位置**：`templates/login.html` 第 1 行

**漏洞代码**：
```html
<!-- 调试信息 - 默认管理员账号 用户名: admin 密码: admin123 -->
```

**攻击路径**：
```
访客打开登录页 → 右键查看页面源代码 → 直接获取管理员账号 admin/admin123 → 登录系统
```

**修复方案**：删除该注释行。

**安全原则**：永远不要在 HTML 注释、JavaScript 代码、API 响应等任何客户端可达的位置放置敏感凭据信息。

---

### V-02：密码明文展示在首页页面

**文件位置**：`templates/index.html` 第 10 行

**漏洞代码**：
```html
<li><span class="info-label">密码：</span>{{ user.password }}</li>
```

**攻击路径**：
```
用户登录成功 → 首页直接显示密码明文 → 旁人路过看到/屏幕截图 → 密码泄露
```

**修复方案**：替换为掩码显示 `••••••••`。

**安全原则**：密码在任何情况下都不应以明文形式展示在用户界面上。

---

### V-03：明文密码存储

**文件位置**：`app.py` 第 10-23 行

**漏洞代码**：
```python
"password": "admin123",   # 明文
"password": "alice2025",  # 明文
```

**攻击路径**：
```
攻击者获得代码读取权限/数据库泄露 → 直接获取所有用户的明文密码 → 可能用于撞库攻击其他平台
```

**修复方案**：使用 `werkzeug.security.generate_password_hash()` 进行密码哈希存储。

```python
from werkzeug.security import generate_password_hash, check_password_hash

# 存储
"password": generate_password_hash("admin123")

# 验证
check_password_hash(stored_hash, input_password)
```

**原理说明**：
- `generate_password_hash()` 使用 PBKDF2-SHA256 算法，自动加盐
- 每次生成的哈希值都不同（因为随机盐值），即使相同密码哈希结果也不同
- `check_password_hash()` 使用恒定时间比较，防止时序攻击

---

### V-04：弱 Secret Key 可导致 Session 伪造

**文件位置**：`app.py` 第 4 行

**漏洞代码**：
```python
app.secret_key = "dev-key-2025"
```

**攻击路径**：
```
攻击者获取合法 session cookie → 使用 flask-unsign 工具破解 secret key
→ flask-unsign --unsign --cookie <session_cookie> → 得到密钥 "dev-key-2025"
→ flask-unsign --sign --cookie '{"username":"admin"}' --secret "dev-key-2025"
→ 伪造 admin 的 session cookie → 以管理员身份登录系统
```

**修复方案**：使用 `os.urandom(24).hex()` 生成 48 字符随机密钥，并支持环境变量覆盖。

```python
import os
app.secret_key = os.environ.get("SECRET_KEY", os.urandom(24).hex())
```

**安全原则**：Flask 使用 `itsdangerous` 库对 session cookie 进行签名（HMAC-SHA1），secret_key 就是这个签名的密钥。弱密钥意味着攻击者可以伪造任意 session 数据。应始终使用密码学安全的随机密钥。

---

### V-05：Debug 模式开启导致 RCE 风险

**文件位置**：`app.py` 第 62 行

**漏洞代码**：
```python
app.run(debug=True, host="0.0.0.0", port=5000)
```

**攻击路径**：
```
访问 http://<server_ip>:5000/console → 进入 Flask Debugger PIN 控制台
→ 利用 PIN 生成算法（获取机器信息）计算 PIN → 获得 Python shell → 执行任意系统命令
```

**修复方案**：通过环境变量控制 debug 模式。

```python
debug_mode = os.environ.get("FLASK_DEBUG", "0") == "1"
app.run(debug=debug_mode, ...)
```

**安全原则**：Flask 的 Werkzeug Debugger 提供了交互式 Python shell 功能一旦开启且可访问，攻击者可以：
- 查看完整的调用栈和本地变量
- 通过 debugger PIN 进入 Python 交互式控制台
- 执行任意 Python 代码和系统命令

---

### V-06：监听所有网卡扩大攻击面

**文件位置**：`app.py` 第 62 行

**漏洞代码**：
```python
app.run(debug=True, host="0.0.0.0", port=5000)
```

**攻击路径**：
```
攻击者扫描内网 → 发现 192.168.x.x:5000 开放 → 直接访问服务
→ 结合 Debug 模式开启 → 执行远程代码
```

**修复方案**：改为仅监听本地地址。

```python
app.run(..., host="127.0.0.1", port=5000)
```

**安全原则**：开发服务器应仅绑定到 `127.0.0.1`（localhost），避免暴露在局域网中。生产环境应使用反向代理（Nginx/Caddy）配合 WSGI 服务器（Gunicorn/uWSGI）。

---

### V-07：密码字段从后端传递到前端模板

**文件位置**：`app.py` 第 32 行和第 47 行

**漏洞代码**：
```python
user_info = USERS[username]  # 直接取出包含 password 的完整字典
return render_template("index.html", username=username, user=user_info)
```

**攻击路径**：
```
登录成功 → 密码字段被传入模板上下文 → 浏览器开发者工具可查看模板变量
→ 或模板将来被修改为显示 {{ user.password }} → 密码泄露
```

**修复方案**：新增过滤函数，在传给模板前主动移除 `password` 字段。

```python
def get_safe_user_info(username):
    """返回不包含密码的用户信息"""
    if username in USERS:
        user = USERS[username]
        return {k: v for k, v in user.items() if k != "password"}
    return None
```

**安全原则**：最小权限原则——只传递模板真正需要的数据，不应将敏感字段（密码、密钥等）传入模板上下文，即使当前模板没有渲染该字段。

---

## 五、修复前后功能验证

所有修复均不影响核心功能：

| 功能 | 修复前 | 修复后 |
|------|--------|--------|
| admin 登录 | ✅ 成功 | ✅ 成功 |
| alice 登录 | ✅ 成功 | ✅ 成功 |
| 错误密码登录 | ✅ 拒绝 | ✅ 拒绝 |
| 退出登录 | ✅ 正常 | ✅ 正常 |
| 未登录访问首页 | ✅ 提示登录 | ✅ 提示登录 |

---

## 六、安全建议总结

### 针对本项目的修复清单

| # | 修复项 | 优先级 |
|---|--------|--------|
| 1 | 删除 HTML 中的凭据注释 | 🔴 立即 |
| 2 | 前端不展示密码字段 | 🔴 立即 |
| 3 | 密码加盐哈希存储 | 🔴 立即 |
| 4 | 替换为随机 Secret Key | 🔴 立即 |
| 5 | 关闭 Debug 模式 | 🟠 尽快 |
| 6 | 仅绑定 127.0.0.1 | 🟠 尽快 |
| 7 | 后端过滤敏感字段再传模板 | 🟡 建议 |

### 通用 Web 安全最佳实践

1. **密码策略**：使用 bcrypt/PBKDF2/Argon2 等加盐哈希算法，永远不存储明文
2. **密钥管理**：敏感配置（secret key、数据库密码、API token）从环境变量或密钥管理服务读取
3. **最小暴露**：服务不绑定 0.0.0.0，使用反向代理，仅暴露必要端口
4. **安全头**：启用 CSP、X-Frame-Options、HSTS 等 HTTP 安全头
5. **CSRF 保护**：Flask-WTF 或自定义 CSRF token
6. **HTTPS**：生产环境强制启用 HTTPS
7. **输入验证**：对所有用户输入进行验证和清洗
8. **开发/生产分离**：Debug 模式、热重载、详细错误信息仅限开发环境

---

## 七、文件变更清单

```
创建: .gitignore
创建: README.md
修改: app.py          (密码哈希、Secret Key、Debug控制、127.0.0.1、过滤函数)
创建: app_vulnerable.py (原始漏洞版，供学习对比)
不变: static/css/style.css
不变: templates/base.html
修改: templates/index.html   (密码展示改为掩码)
修改: templates/login.html   (删除注释行)
```

---

## 八、参考文献

- [OWASP Top 10 - 2021](https://owasp.org/www-project-top-ten/)
- [OWASP - Password Storage Cheat Sheet](https://cheatsheetseries.owasp.org/cheatsheets/Password_Storage_Cheat_Sheet.html)
- [Flask Documentation - Sessions](https://flask.palletsprojects.com/en/stable/quickstart/#sessions)
- [Flask Documentation - Security Considerations](https://flask.palletsprojects.com/en/stable/security/)
- [CWE-259: Use of Hard-coded Password](https://cwe.mitre.org/data/definitions/259.html)
- [CWE-521: Weak Password Requirements](https://cwe.mitre.org/data/definitions/521.html)
- [CWE-312: Cleartext Storage of Sensitive Information](https://cwe.mitre.org/data/definitions/312.html)
- [CWE-798: Use of Hard-coded Credentials](https://cwe.mitre.org/data/definitions/798.html)

---

## 九、附录：攻击复现工具

以下工具可用于验证本报告中的漏洞：

| 工具 | 用途 | 安装 |
|------|------|------|
| `flask-unsign` | Session 伪造/破解 | `pip install flask-unsign` |
| `curl` | 查看页面源码 | 系统自带 |
| Browser DevTools | 调试模板变量 | 浏览器内置 |

### Session 伪造演示

```bash
# 1. 获取合法 session cookie（通过浏览器 DevTools）
# 2. 破解 secret key
flask-unsign --unsign --cookie "eyJ1c2VybmFtZSI6ImFsaWNlIn0.Z6dYwQ.xxx"

# 3. 伪造 admin session
flask-unsign --sign --cookie '{"username":"admin"}' --secret "dev-key-2025"
```

---

*报告生成日期：2026-07-07*
*审计工具：Manuel Code Review + Adversarial Verification*
