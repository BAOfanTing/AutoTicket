# 快速开始指南

## 🚀 5分钟快速上手

### 1. 环境准备
```bash
# 安装依赖
npm install node-rsa
npm install crypt
```

### 2. 配置钉钉机器人
编辑 `dingtalk_config.js`:
```javascript
module.exports = {
    webhook: 'https://oapi.dingtalk.com/robot/send?access_token=你的token',
    secret: '你的加签密钥',
    enabled: true
};
```

### 3. 配置用户信息
编辑 `workflow_config.js` 中的 `commonFields`:
```javascript
commonFields: {
    channel: "02",
    app_ver_no: "3.1.4",
    login_name: "你的加密用户名",  // 需要替换
    ses_id: "你的会话ID"         // 需要替换
}
```

### 4. 运行脚本

#### 完整工作流 (推荐)
```bash
node workflow_sigin.js
```
**功能**: 3次签到 → 1次评论 → 1次查询积分

#### 持续请求脚本
```bash
node AutoTicket.js
```
**功能**: 持续请求直到出现"手慢了"响应，固定100ms延迟

## 📁 文件说明

| 文件 | 作用 | 是否需要修改 |
|------|------|-------------|
| `workflow_config.js` | 统一配置文件 | ✅ 需要配置用户信息 |
| `dingtalk_config.js` | 钉钉通知配置 | ✅ 需要配置机器人信息 |
| `workflow_sigin.js` | 主工作流脚本 | ❌ 直接运行 |
| `AutoTicket.js` | 持续请求脚本 | ❌ 直接运行 |
| `encrypt_rsa.js` | 加密模块 | ❌ 无需修改 |
| `decrypt.js` | 解密模块 | ❌ 无需修改 |

## ⚡ 常用命令

```bash
# 运行完整工作流
node workflow_sigin.js

# 运行持续请求脚本
node AutoTicket.js

# 测试解密功能
echo '{"data2":"加密数据"}' | node --security-revert=CVE-2023-46809 decrypt.js
```

## 🔧 故障排除

### 问题1: 解密失败
**错误**: `解密过程中发生错误`
**解决**: 检查输入的JSON数据格式是否正确，确保包含data2字段

### 问题2: 签名错误
**错误**: `数字签名错误`
**解决**: 检查 `workflow_config.js` 中的参数是否正确

### 问题3: 钉钉通知失败
**错误**: `钉钉通知发送失败`
**解决**: 检查 `dingtalk_config.js` 中的webhook和secret

### 问题4: 请求超时
**错误**: `Request timeout`
**解决**: 检查网络连接，或增加 `timeout` 配置

## 📊 监控和日志

- **控制台输出**: 查看详细的执行日志
- **钉钉通知**: 接收成功/失败通知
- **性能统计**: 查看请求耗时和重试次数

## 🎯 使用建议

1. **首次使用**: 先运行 `workflow_sigin.js` 测试基础功能
2. **持续请求**: 使用 `AutoTicket.js` 进行持续请求直到出现"手慢了"
3. **定时任务**: 可以设置定时任务自动执行
4. **监控告警**: 关注钉钉通知，及时处理异常

---

**需要帮助?** 查看 `README_项目总览.md` 获取详细文档。
