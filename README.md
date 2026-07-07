# Flask 用户信息管理平台

> 🔐 简易用户管理系统 — 包含**故意引入的安全漏洞**及其**完整修复过程**的安全演示项目

## 项目概述

使用 Python Flask 框架实现的用户登录管理系统，支持用户登录、登出和个人信息展示。

**项目用途**：安全教学演示 — 展示了 7 个常见 Web 安全漏洞，并逐一修复对比。

---

## 目录结构

```
flask-user-management/
├── app.py                  # Flask 主应用（修复版）
├── app_vulnerable.py       # Flask 主应用（原始漏洞版）
├── static/
│   └── css/
│       └── style.css       # 样式文件
├── templates/
│   ├── base.html           # 基础模板（导航栏）
│   ├── index.html          # 首页（用户信息展示）
│   └── login.html          # 登录页面
└── README.md
```

---

## 快速启动

```bash
pip install flask
python app.py
# 访问 http://127.0.0.1:5000
```

### 测试账号

| 用户名 | 密码 | 角色 | 邮箱 | 余额 |
|--------|------|------|------|------|
| admin | admin123 | admin | admin@example.com | 99999 |
| alice | alice2025 | user | alice@example.com | 100 |

---

## 🔍 安全漏洞检测与修复

共检测并修复 **7 个安全漏洞**，按严重程度排列如下：

### 🔴 漏洞 1：登录页 HTML 注释泄露管理员账号密码

| 项目 | 内容 |
|------|------|
| **文件** | `templates/login.html` |
| **描述** | 登录页面 HTML 源代码中含有一行泄露默认账号的注释：`<!-- 调试信息 - 默认管理员账号 用户名: admin 密码: admin123 -->` |
| **攻击方式** | 任何访客打开登录页后，右键 → 查看页面源代码，即可直接获取管理员账号密码 |
| **严重程度** | 🔴 严重 |
| **修复** | 删除该注释行 |

```diff
- <!-- 调试信息 - 默认管理员账号 用户名: admin 密码: admin123 -->
  {% extends "base.html" %}
```

---

### 🔴 漏洞 2：密码明文展示在首页

| 项目 | 内容 |
|------|------|
| **文件** | `templates/index.html` 第 10 行 |
| **描述** | 用户登录成功后，首页直接渲染 `{{ user.password }}`，将密码明文显示在浏览器页面中 |
| **攻击方式** | 他人经过看到屏幕、屏幕截图，即可获取当前用户的明文密码 |
| **严重程度** | 🔴 严重 |
| **修复** | 将密码展示替换为掩码显示 `••••••••` |

```diff
- <li><span class="info-label">密码：</span>{{ user.password }}</li>
+ <li><span class="info-label">密码：</span>••••••••</li>
```

---

### 🔴 漏洞 3：明文密码存储

| 项目 | 内容 |
|------|------|
| **文件** | `app.py` USERS 字典 |
| **描述** | 用户密码以明文形式直接存储在 `USERS` 字典中，未做任何哈希处理。若数据库泄露或代码被查看，所有用户的密码直接暴露 |
| **攻击方式** | 代码泄露 / 数据库泄露 → 密码全量被获取 |
| **严重程度** | 🔴 严重 |
| **修复** | 使用 `werkzeug.security.generate_password_hash()` 进行密码哈希存储，登录时使用 `check_password_hash()` 比对 |

```python
from werkzeug.security import generate_password_hash, check_password_hash

# 存储（哈希化）
"password": generate_password_hash("admin123")

# 验证（安全比对）
check_password_hash(USERS[username]["password"], password)
```

---

### 🔴 漏洞 4：弱 Secret Key 可导致 Session 伪造

| 项目 | 内容 |
|------|------|
| **文件** | `app.py` 第 4 行 |
| **描述** | `secret_key = "dev-key-2025"` 是一个硬编码的弱密钥，攻击者可以用 `flask-unsign` 等工具暴力破解，然后伪造任意用户的 session cookie |
| **攻击方式** | 使用 `flask-unsign --unsign --cookie <session>` 破解密钥 → 伪造 `{"username": "admin"}` 的 session cookie → 以管理员身份登录 |
| **严重程度** | 🔴 严重 |
| **修复** | 使用 `os.urandom(24).hex()` 生成随机密钥，并支持通过环境变量 `SECRET_KEY` 覆盖 |

```python
import os
app.secret_key = os.environ.get("SECRET_KEY", os.urandom(24).hex())
```

---

### 🟠 漏洞 5：Debug 模式在生产环境开启

| 项目 | 内容 |
|------|------|
| **文件** | `app.py` 第 62 行 |
| **描述** | `debug=True` 强制开启，且在 `0.0.0.0` 监听，导致 Debugger PIN 暴露在网络上，存在远程代码执行（RCE）风险 |
| **攻击方式** | 访问 `http://<ip>:5000/console` 进入 Flask Debugger 控制台，暴力破解 Debugger PIN 后执行任意 Python 代码 |
| **严重程度** | 🟠 高 |
| **修复** | 通过环境变量 `FLASK_DEBUG` 控制 debug 模式，生产环境默认为关闭 |

```python
debug_mode = os.environ.get("FLASK_DEBUG", "0") == "1"
app.run(debug=debug_mode, host="127.0.0.1", port=5000)
```

---

### 🟠 漏洞 6：监听所有网卡扩大攻击面

| 项目 | 内容 |
|------|------|
| **文件** | `app.py` 第 62 行 |
| **描述** | `host="0.0.0.0"` 使得服务监听在所有网络接口上，局域网内任何设备均可访问该服务 |
| **攻击方式** | 内网扫描发现 `192.168.x.x:5000` 即可直接访问，增加被攻击面 |
| **严重程度** | 🟠 中 |
| **修复** | 改为 `host="127.0.0.1"`，仅允许本地访问 |

```diff
- app.run(debug=True, host="0.0.0.0", port=5000)
+ app.run(debug=debug_mode, host="127.0.0.1", port=5000)
```

---

### 🟡 漏洞 7：密码字段从后端传递到模板

| 项目 | 内容 |
|------|------|
| **文件** | `app.py` 第 47 行 |
| **描述** | 从 `USERS[username]` 获取的完整用户信息字典直接传给模板渲染，其中包含 `password` 字段。即使模板不显示，数据已经在前端上下文中 |
| **攻击方式** | 浏览器开发者工具可查看模板变量，或模板将来被修改显示密码 |
| **严重程度** | 🟡 中 |
| **修复** | 新增 `get_safe_user_info()` 函数，在传给模板前主动过滤掉 `password` 字段 |

```python
def get_safe_user_info(username):
    """返回不包含密码的用户信息"""
    if username in USERS:
        user = USERS[username]
        return {k: v for k, v in user.items() if k != "password"}
    return None
```

---

## 修复前后对比

### 文件变更对照

| 文件 | 变更内容 |
|------|----------|
| `app.py` | 密码哈希存储、随机 Secret Key、环境变量控制 Debug 模式、host 改为 127.0.0.1、新增 `get_safe_user_info()` 过滤密码字段 |
| `templates/index.html` | 密码展示改为掩码 `••••••••` |
| `templates/login.html` | 删除泄露账号的 HTML 注释 |
| `templates/base.html` | 未变更 |
| `static/css/style.css` | 未变更 |

### 新增文件

| 文件 | 说明 |
|------|------|
| `app_vulnerable.py` | 原始的、包含全部漏洞的版本，供对比学习使用 |

---

## 运行

```bash
# 运行修复版本
python app.py

# 运行漏洞版本（仅用于学习对比）
python app_vulnerable.py
```

打开 `http://127.0.0.1:5000` 即可访问。
