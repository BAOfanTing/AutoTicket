# 杭工e家自动化脚本项目总览

## 项目简介

这是一个用于杭工e家APP的自动化脚本项目，支持多种功能包括签到、评论、查询积分、兑换优惠券等。项目采用JavaScript实现，具有完整的加密解密、错误处理、重试机制和钉钉通知功能。

## 文件结构说明

```
frida_demo/
├── README_项目总览.md          # 本文档 - 项目总览和使用指南
├── workflow_sigin.js           # 主工作流脚本 - 3次签到→1次评论→1次查询
├── AutoTicket.js               # 兑换优惠券脚本 - 带重试和钉钉通知
├── workflow_config.js          # 统一配置文件 - 所有请求参数和API端点
├── dingtalk_config.js          # 钉钉机器人配置 - 通知推送设置
├── encrypt_rsa.js              # 加密模块 - RSA签名和DESede加密
└── decrypt.js                  # 解密模块 - 响应数据解密
```

## 核心文件功能详解

### 1. 📋 workflow_config.js - 统一配置文件
**作用**: 集中管理所有请求参数、API端点和配置信息

**主要配置**:
- `baseUrl`: 基础URL (https://app.hzgh.org.cn)
- `commonFields`: 公共请求字段 (channel, app_ver_no, login_name, ses_id)
- `endpoints`: API端点配置 (login, signin, comment, query, exchange)
- `functions`: 功能特定参数 (每个功能的独有参数)
- `request`: 请求配置 (超时时间、重试延迟)

**使用场景**: 所有脚本都引用此文件，避免硬编码参数

### 2. 🔐 encrypt_rsa.js - 加密模块
**作用**: 实现与服务器端一致的加密和签名算法

**核心功能**:
- **RSA加密**: 加密会话密钥 (dec_key)
- **DESede加密**: 加密敏感字段 (login_name, user_id等)
- **RSA签名**: 生成请求签名 (sign字段)
- **双重分支**: 支持zhgh和else两种加密模式

**技术细节**:
- 使用PKCS#1 v1.5填充的RSA加密
- DESede-ECB模式的三重DES加密
- SHA256WithRSA签名算法

### 3. 🔓 decrypt.js - 解密模块
**作用**: 解密服务器返回的加密响应数据

**核心功能**:
- **RSA解密**: 解密密钥材料 (前172字符)
- **DESede解密**: 解密实际数据内容
- **标准输入**: 通过管道接收JSON数据
- **完整输出**: 返回包含解密data2的完整JSON

**使用方式**:
```bash
echo '{"data2":"加密数据"}' | node --security-revert=CVE-2023-46809 decrypt.js
```

### 4. 📱 dingtalk_config.js - 钉钉配置
**作用**: 配置钉钉机器人通知功能

**配置项**:
- `webhook`: 钉钉机器人webhook地址
- `secret`: 加签密钥
- `maxRetries`: 最大重试次数
- `retryDelay`: 重试间隔
- `enabled`: 是否启用通知

### 5. 🚀 workflow_sigin.js - 主工作流脚本
**作用**: 执行完整的工作流程 (3次签到→1次评论→1次查询积分)

**工作流程**:
1. 执行登录签到
2. 执行3次日常签到 (每次间隔1秒)
3. 执行1次评论
4. 执行1次积分查询
5. 每次执行都推送钉钉通知

**特点**:
- 使用通用执行函数 `executeFunction()`
- 自动加密请求和解密响应
- 完整的错误处理和日志输出

### 6. ⚡ AutoTicket.js.js - 兑换优惠券脚本
**作用**: 专门用于兑换优惠券，具有智能重试机制

**核心功能**:
- **智能重试**: 检测"手慢"响应自动重试
- **错误处理**: 处理网络错误和HTTP状态码
- **动态延迟**: 根据错误类型调整重试间隔
- **性能监控**: 记录每次请求的耗时
- **钉钉通知**: 成功/失败都推送通知

**重试策略**:
- 最大重试10次
- 手慢响应: 500ms延迟
- HTTP 5xx错误: 3秒延迟
- HTTP 404错误: 2秒延迟
- 网络错误: 指数退避延迟

## 快速开始指南

### 第一步: 环境准备
1. **安装Node.js**: 确保已安装Node.js (建议v14+)
2. **安装依赖**: 
   ```bash
   npm install node-rsa
   ```

### 第二步: 配置钉钉机器人
1. 在钉钉群中添加自定义机器人
2. 选择"加签"安全设置
3. 复制webhook地址和密钥
4. 编辑 `dingtalk_config.js`:
   ```javascript
   module.exports = {
       webhook: '你的webhook地址',
       secret: '你的加签密钥',
       enabled: true
   };
   ```

### 第三步: 配置请求参数
编辑 `workflow_config.js` 中的关键参数:
```javascript
commonFields: {
    channel: "02",
    app_ver_no: "3.1.4", 
    login_name: "你的加密用户名",
    ses_id: "你的会话ID"
}
```

### 第四步: 运行脚本

#### 运行完整工作流
```bash
node workflow_sigin.js
```

#### 运行兑换优惠券
```bash
node AutoTicket.js.js
```

## 使用场景

### 场景1: 日常签到自动化
使用 `workflow_sigin.js` 实现每日自动签到、评论和查询积分

### 场景2: 优惠券抢购
使用 `AutoTicket.js.js` 实现优惠券的快速抢购，自动重试直到成功

### 场景3: 批量操作
可以同时运行多个脚本实例，实现并发操作

## 技术架构

### 加密流程
```
原始参数 → RSA加密会话密钥 → DESede加密敏感字段 → RSA签名 → 发送请求
```

### 解密流程
```
加密响应 → RSA解密密钥材料 → DESede解密数据内容 → 返回明文JSON
```

### 错误处理
```
请求失败 → 判断错误类型 → 计算重试延迟 → 等待重试 → 记录日志 → 钉钉通知
```

## 注意事项

### 安全提醒
1. **私钥安全**: RSA私钥已嵌入代码中，请妥善保管代码文件
2. **配置安全**: 不要将包含真实配置的文件提交到公共仓库
3. **频率控制**: 避免过于频繁的请求，遵守服务器限制

### 使用建议
1. **测试环境**: 先在测试环境验证脚本功能
2. **监控日志**: 关注控制台输出和钉钉通知
3. **参数更新**: 定期检查并更新配置参数
4. **错误处理**: 遇到问题查看详细错误日志

### 常见问题
1. **解密失败**: 检查输入的JSON数据格式，确保包含data2字段
2. **签名错误**: 确认加密模块配置正确
3. **网络超时**: 调整 `timeout` 配置
4. **钉钉通知失败**: 检查webhook配置

## 扩展开发

### 添加新功能
1. 在 `workflow_config.js` 中添加新的端点和参数
2. 在相应脚本中添加新的执行函数
3. 测试加密解密流程

### 自定义重试策略
修改 `AutoTicket.js.js` 中的重试逻辑:
```javascript
// 自定义重试延迟
const customDelay = calculateCustomDelay(errorType, attemptCount);
```

### 添加新的通知方式
扩展 `dingtalk_config.js` 支持其他通知方式:
```javascript
// 添加邮件通知
email: {
    enabled: true,
    smtp: 'smtp.example.com',
    // ...
}
```

## 版本历史

- **v1.0**: 基础Python版本
- **v2.0**: JavaScript重写，性能优化
- **v3.0**: 配置文件统一，代码重构
- **v4.0**: 智能重试机制，错误处理增强

## 技术支持

如有问题或建议，请查看:
1. 控制台错误日志
2. 钉钉通知中的错误信息
3. 各配置文件的参数设置

---

**免责声明**: 本项目仅供学习和研究使用，请遵守相关法律法规和网站使用条款。
