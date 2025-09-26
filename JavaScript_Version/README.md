# 杭工e家自动化脚本项目

## 📚 文档导航

### 🚀 快速开始
- **[README_快速开始.md](./README_快速开始.md)** - 5分钟快速上手指南
- **[README_项目总览.md](./README_项目总览.md)** - 完整项目文档和使用说明

### 🔧 技术文档
- **[README_技术架构.md](./README_技术架构.md)** - 系统架构和技术实现

### 📁 核心文件
| 文件 | 作用 | 文档说明 |
|------|------|----------|
| `workflow_sigin.js` | 主工作流脚本 | 3次签到→1次评论→1次查询积分 |
| `AutoTicket.js` | 持续请求脚本 | 持续请求直到出现"手慢了"响应 |
| `workflow_config.js` | 统一配置文件 | 所有请求参数和API端点 |
| `dingtalk_config.js` | 钉钉配置 | 通知推送设置 |
| `encrypt_rsa.js` | 加密模块 | RSA签名和DESede加密 |
| `decrypt.js` | 解密模块 | 响应数据解密 |

## 🎯 快速开始

### 1. 环境准备
```bash
# 安装依赖
npm install node-rsa
npm install crypto

# 私钥已嵌入代码中，无需额外文件
```

### 2. 配置钉钉机器人
编辑 `dingtalk_config.js` 配置你的钉钉机器人信息

### 3. 配置用户信息
编辑 `workflow_config.js` 中的 `getUserId` `getSesId` 函数配置你的用户信息

### 4. 运行脚本
```bash
# 完整工作流
node workflow_sigin.js

# 持续请求脚本
node AutoTicket.js
```

## 📋 功能特性

- ✅ **完整工作流**: 自动执行签到、评论、查询积分
- ✅ **持续请求**: 持续请求直到出现"手慢了"响应，固定100ms延迟
- ✅ **加密安全**: 完整的RSA+DESede加密解密
- ✅ **钉钉通知**: 实时推送执行结果
- ✅ **性能监控**: 详细的执行时间和重试统计
- ✅ **配置统一**: 集中管理所有配置参数
- ✅ **错误处理**: 完善的错误处理和日志记录

## 🔧 技术栈

- **Node.js**: 运行时环境
- **crypto**: 加密解密模块
- **node-rsa**: RSA加密库
- **https**: HTTP请求模块
- **child_process**: 子进程管理

## 📞 支持

- 查看 [README_快速开始.md](./README_快速开始.md) 获取快速上手指南
- 查看 [README_项目总览.md](./README_项目总览.md) 获取详细文档
- 查看 [README_技术架构.md](./README_技术架构.md) 了解技术实现

## ⚠️ 免责声明

本项目仅供学习和研究使用，请遵守相关法律法规和网站使用条款。

---

**最后更新**: 2025年9月
