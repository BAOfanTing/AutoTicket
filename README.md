<div align="center">
  <img src="https://socialify.git.ci/BAOfanTing/AutoTicket/image?description=1&font=Inter&forks=1&language=1&name=1&owner=1&pattern=Plus&stargazers=1&theme=Dark" alt="AutoTicket" />
  <p>
    <strong>杭工e家 APP 自动化脚本</strong>
    <br />
    支持签到 · 评论 · 积分查询 · 优惠券定时兑换
  </p>
  <p>
    <a href="#-python-版本"><img src="https://img.shields.io/badge/Python-3.x-blue?logo=python" /></a>
    <a href="#-javascript-版本"><img src="https://img.shields.io/badge/Node.js-14%2B-green?logo=nodedotjs" /></a>
    <a href="#-微信小程序"><img src="https://img.shields.io/badge/WeChat-%E5%B0%8F%E7%A8%8B%E5%BA%8F-07c160?logo=wechat" /></a>
    <a href="./LICENSE"><img src="https://img.shields.io/badge/license-MIT-yellow" /></a>
  </p>
</div>

---

## 📋 目录

- [项目简介](#-项目简介)
- [功能特性](#-功能特性)
- [版本对比](#-版本对比)
- [快速开始](#-快速开始)
  - [Python 版本](#python-版本)
  - [JavaScript 版本](#javascript-版本)
  - [微信小程序](#微信小程序)
- [项目结构](#-项目结构)
- [技术栈](#-技术栈)
- [更新日志](#-更新日志)
- [免责声明](#-免责声明)

---

## 📖 项目简介

AutoTicket 是一个针对 **杭工e家 APP** 的自动化脚本集合。通过对 APP 接口的逆向分析，实现了**登录**、**每日签到**、**评论**、**积分查询**和**优惠券定时兑换**等功能的自动化。

项目提供 **Python**（图形界面）、**JavaScript**（命令行）和**微信小程序**三种形态，满足不同使用场景。

---

## 🎯 功能特性

| 功能 | Python | JavaScript | 小程序 | 说明 |
|------|--------|------------|--------|------|
| ✅ 密码登录 | ✓ | ✗ | ✓ | 手机号 + 密码 + 图形验证码 |
| ✅ 短信验证码登录 | ✓ | ✗ | ✓ | 手机号 + 短信验证码 |
| ✅ 获取图形验证码 | ✓ | ✗ | ✓ | U067 接口 |
| ✅ 每日签到 | ✓ | ✓ | ✓ | 自动 3 次签到 |
| ✅ 发表评论 | ✓ | ✓ | ✓ | 自动评论 |
| ✅ 积分查询 | ✓ | ✓ | ✓ | 查询当前积分 |
| ✅ 定时兑换 | ✓ | ✓ | ✓ | 指定时间并发抢券 |
| ✅ 图形界面 | ✓ | ✗ | ✓ | PyQt5 / 小程序 UI |
| ✅ 钉钉通知 | ✗ | ✓ | ✗ | 执行结果推送 |
| ✅ 自动更新 | ✓ | ✗ | ✗ | 检查 GitHub 新版本 |

---

## 🔄 版本对比

| 特性 | Python 版 | JavaScript 版 | 微信小程序 |
|------|-----------|---------------|------------|
| **界面** | PyQt5 桌面 GUI | 命令行 | 移动端 UI |
| **操作难度** | ⭐ 简单 | ⭐⭐⭐ 中等 | ⭐⭐ 较简单 |
| **适用场景** | 个人电脑使用 | 服务器定时任务 | 手机端操作 |
| **登录方式** | 密码 / 短信 | 手动填 token | 密码 / 短信 |
| **定时兑换** | ✓ 支持 | ✓ 支持 | ✓ 支持 |
| **依赖环境** | Python 3.x + PyQt5 | Node.js 14+ | 微信开发者工具 |

---

## 🚀 快速开始

### Python 版本

支持密码登录和短信验证码登录两种方式。

#### 安装依赖

```bash
pip install -r requirements.txt
```

`requirements.txt` 内容：
```
requests
pycryptodome
pycryptodomex
```

#### 方式一：下载 Release 可执行文件（推荐）

从 [GitHub Releases](https://github.com/BAOfanTing/AutoTicket/releases) 下载最新的 `AutoTicket.exe`，双击运行即可，无需安装 Python 环境。

#### 方式二：源码运行

```bash
pip install -r requirements.txt
python gui.py
```

1. 点击 **登录** 按钮
2. 选择 **密码登录** 或 **短信验证码登录**
3. 输入手机号、图形验证码，完成登录
4. 登录成功后自动回填 `login_name` 和 `ses_id`
5. 设置兑换参数（抢票时间、运行次数、间隔）
6. 点击 **启动** 等待定时执行

#### 方式三：命令行

```bash
python Login.py
```

1. 输入手机号，选择登录方式
2. 密码登录：输入密码 + 图形验证码
3. 短信登录：输入图形验证码 → 接收短信 → 输入验证码
4. 自动完成登录流程

#### 自行打包为 exe

```bash
pip install pyinstaller
pyinstaller AutoTicket.spec
```

---

### JavaScript 版本

适用于服务器部署和定时任务。

```bash
cd JavaScript_Version
npm install
```

编辑 `workflow_config.js` 配置 `login_name` 和 `ses_id`，然后运行：

```bash
# 完整工作流（签到→评论→查询积分）
node workflow_sigin.js

# 持续兑换脚本
node AutoTicket.js
```

钉钉通知配置请编辑 `dingtalk_config.js`。

---

### 微信小程序

使用 HBuilderX 打开 `App_Version/app_version` 目录，运行到微信开发者工具即可。

支持密码登录和短信验证码登录，登录完成后可执行每日任务（签到、评论、积分查询）。

---

## 📁 项目结构

```
AutoTicket/
├── README.md                    # 本文档
├── LICENSE                      # MIT 许可证
│
├── AutoTicket.py                # Python 主程序 - 定时兑换逻辑
├── Login.py                     # Python 登录模块 - U067/U004/U065/SMS
├── Decoder.py                   # Python 解密模块 - data2 解密
├── gui.py                       # Python 图形界面（PyQt5）
├── updater.py                   # Python 自动更新模块
├── requirements.txt             # Python 依赖
├── AutoTicket.spec              # PyInstaller 打包配置
│
├── JavaScript_Version/          # JS 命令行版本
│   ├── README.md
│   ├── AutoTicket.js            # 持续兑换脚本
│   ├── workflow_sigin.js        # 每日工作流脚本
│   ├── workflow_config.js       # 配置文件
│   ├── dingtalk_config.js       # 钉钉通知配置
│   ├── encrypt_rsa.js           # RSA + DESede 加密
│   └── decrypt.js               # 响应解密
│
├── App_Version/                 # 微信小程序版本
│   └── app_version/
│       ├── pages/
│       │   ├── login/login.vue  # 登录页面
│       │   └── main/main.vue    # 主页面
│       └── src/
│           ├── services/
│           │   ├── authService.js    # 登录相关 API
│           │   ├── taskService.js    # 任务相关 API
│           │   ├── cryptoService.js  # 加解密服务
│           │   ├── constants.js      # 常量 & 端点
│           │   └── http.js           # HTTP 请求封装
│           └── utils/
│               ├── storage.js        # 本地存储
│               └── time.js           # 时间工具
│
├── image/                       # 文档图片
├── icon.ico                     # 程序图标
└── config.json                  # 本地配置文件（自动生成）
```

---

## 🧱 技术栈

### 加密体系

所有版本共用同一套加密体系（通过逆向 APP 获取）：

| 算法 | 用途 |
|------|------|
| RSA (PKCS1_v1_5) | 加密 3DES 会话密钥 |
| 3DES (ECB/PKCS7) | 加密敏感字段（手机号、密码等） |
| SHA256withRSA | 请求体签名 |
| 3DES (CBC/PKCS7) | 解密响应 data2 |

### Python 版

- **Python 3.x** — 主开发语言
- **PyQt5** — 图形界面框架
- **requests** — HTTP 客户端
- **pycryptodome / pycryptodomex** — 加密库

### JavaScript 版

- **Node.js 14+** — 运行环境
- **node-rsa / crypto** — 加密库

### 微信小程序

- **Vue 3** — 前端框架
- **uni-app** — 跨端框架
- **crypto-js / jsencrypt / jsrsasign** — 加密库

---

## 📜 更新日志

### v1.0.7 (2026-05-17)
- 新增 **短信验证码登录**（Python GUI / CLI / 小程序）
- 新增 `SMS/SMS1` 短信发送接口
- 新增 `U/U065` 短信验证码登录接口
- 登录页面增加密码 / 短信切换

### v1.0.6 (2026-02-13)
- Python 版本增加每日任务一键运行

### v1.0.5 (2026-02-03)
- 实测抢票功能正常
- 优化请求间隔参数

### v1.0.5 (2025-12-23)
- 调整抢票间隔为 0.5~1 秒
- 提高抢票成功率

---

## ⚠️ 免责声明

1. **学习用途**：本项目仅供学习和研究 API 逆向技术使用
2. **合规使用**：请遵守相关法律法规和杭工e家 APP 的使用条款
3. **使用风险**：因使用本软件造成的任何直接或间接后果，开发者不承担责任
4. **商业用途**：如他人将本项目用于商业用途或不当用途，由使用者自行承担责任
5. **开源协议**：本项目基于 **MIT License** 开源

---

<div align="center">
  <sub>Built with ❤️ by BAOfanTing</sub>
  <br />
  <a href="https://github.com/BAOfanTing/AutoTicket">GitHub</a>
  ·
  <a href="https://github.com/BAOfanTing/AutoTicket/issues">Issue</a>
</div>
