# 技术架构说明

## 系统架构图

```
┌─────────────────────────────────────────────────────────────────┐
│                        用户操作层                                │
├─────────────────────────────────────────────────────────────────┤
│  workflow_sigin.js     │    AutoTicket.js.js                 │
│  (完整工作流)          │    (兑换优惠券)                        │
└─────────────────────┬───────────────────────────────────────────┘
                      │
┌─────────────────────▼───────────────────────────────────────────┐
│                      配置管理层                                  │
├─────────────────────────────────────────────────────────────────┤
│  workflow_config.js   │    dingtalk_config.js                  │
│  (统一配置)          │    (钉钉配置)                           │
└─────────────────────┬───────────────────────────────────────────┘
                      │
┌─────────────────────▼───────────────────────────────────────────┐
│                      加密解密层                                  │
├─────────────────────────────────────────────────────────────────┤
│  encrypt_rsa.js      │    decrypt.js                           │
│  (请求加密)          │    (响应解密)                            │
└─────────────────────┬───────────────────────────────────────────┘
                      │
┌─────────────────────▼───────────────────────────────────────────┐
│                      网络通信层                                  │
├─────────────────────────────────────────────────────────────────┤
│  HTTPS请求          │    服务器响应                             │
│  (杭工e家API)       │    (加密数据)                             │
└─────────────────────────────────────────────────────────────────┘
```

## 数据流程图

### 请求流程
```
1. 用户参数 → workflow_config.js → 构建请求参数
2. 请求参数 → encrypt_rsa.js → RSA加密 + DESede加密 + 签名
3. 加密数据 → HTTPS请求 → 杭工e家服务器
4. 服务器响应 → decrypt.js → RSA解密 + DESede解密
5. 解密结果 → 钉钉通知 → 用户
```

### 加密流程详解
```
原始参数
    ↓
生成随机会话密钥 (strC)
    ↓
RSA加密会话密钥 → dec_key
    ↓
DESede加密敏感字段 (login_name, user_id等)
    ↓
生成签名 (RSA-SHA256)
    ↓
构建最终JSON请求
```

### 解密流程详解
```
加密响应
    ↓
提取data2字段
    ↓
RSA解密前172字符 → 获取密钥材料
    ↓
生成DESede密钥 (HTt0Hzsu + 密钥材料)
    ↓
DESede解密剩余数据
    ↓
返回明文JSON
```

## 核心模块说明

### 1. 配置管理模块
```javascript
// workflow_config.js
module.exports = {
    baseUrl: 'https://app.hzgh.org.cn',
    commonFields: { /* 公共字段 */ },
    endpoints: { /* API端点 */ },
    functions: { /* 功能参数 */ },
    request: { /* 请求配置 */ }
};
```

**职责**:
- 集中管理所有配置参数
- 避免硬编码和重复配置
- 提供统一的配置接口

### 2. 加密模块
```javascript
// encrypt_rsa.js
function encryptRequest(params, baseUrl) {
    // 1. 生成会话密钥
    // 2. RSA加密会话密钥
    // 3. DESede加密敏感字段
    // 4. 生成RSA签名
    // 5. 返回加密JSON
}
```

**职责**:
- 实现与服务器一致的加密算法
- 支持多种加密模式 (zhgh/else)
- 提供完整的签名验证

### 3. 解密模块
```javascript
// decrypt.js
function decryptData2(data2_full_base64) {
    // 1. RSA解密密钥材料
    // 2. 生成DESede密钥
    // 3. DESede解密数据
    // 4. 返回明文内容
}
```

**职责**:
- 解密服务器返回的加密数据
- 支持标准输入/输出接口
- 处理安全警告和错误

### 4. 工作流模块
```javascript
// workflow_sigin.js
async function executeFunction(functionName, displayName, extraParams) {
    // 1. 构建请求参数
    // 2. 加密请求
    // 3. 发送请求
    // 4. 解密响应
    // 5. 发送通知
}
```

**职责**:
- 执行完整的工作流程
- 处理各种业务逻辑
- 提供统一的执行接口

### 5. 重试模块
```javascript
// AutoTicket.js.js
async function executeRequest(params, attempt) {
    // 1. 发送请求
    // 2. 检查响应类型
    // 3. 决定是否重试
    // 4. 计算重试延迟
    // 5. 记录性能统计
}
```

**职责**:
- 实现智能重试机制
- 处理各种错误类型
- 提供性能监控

## 安全机制

### 1. 加密安全
- **RSA加密**: 使用2048位RSA密钥
- **DESede加密**: 三重DES加密敏感数据
- **签名验证**: RSA-SHA256签名防止篡改

### 2. 传输安全
- **HTTPS**: 所有请求使用HTTPS加密传输
- **证书验证**: 支持自签名证书
- **超时控制**: 防止长时间等待

### 3. 配置安全
- **私钥保护**: RSA私钥文件本地存储
- **配置分离**: 敏感配置独立文件
- **环境隔离**: 支持不同环境配置

## 错误处理机制

### 1. 网络错误
```javascript
// 指数退避重试
const delay = Math.min(baseDelay * Math.pow(1.5, attempt), maxDelay);
```

### 2. HTTP错误
```javascript
// 根据状态码分类处理
if (statusCode >= 500) {
    // 服务器错误，延迟重试
} else if (statusCode === 404) {
    // 资源未找到，中等延迟
} else if (statusCode === 429) {
    // 请求过多，长时间延迟
}
```

### 3. 业务错误
```javascript
// 手慢响应检测
if (data2Json.result === '999992' && 
    data2Json.msg.includes('手慢')) {
    // 立即重试
}
```

## 性能优化

### 1. 加密优化
- **密钥预加载**: 启动时预加载RSA密钥
- **算法优化**: 使用原生crypto模块
- **内存管理**: 及时释放加密对象

### 2. 网络优化
- **连接复用**: 保持HTTP连接
- **超时控制**: 合理的超时设置
- **并发控制**: 避免过多并发请求

### 3. 重试优化
- **智能延迟**: 根据错误类型调整延迟
- **指数退避**: 避免雪崩效应
- **最大重试**: 防止无限重试

## 监控和日志

### 1. 性能监控
```javascript
const timing = {
    encryptTime: encryptEnd - encryptStart,
    requestTime: requestEnd - requestStart,
    decryptTime: decryptEnd - decryptStart,
    totalTime: totalEnd - totalStart
};
```

### 2. 错误日志
```javascript
console.error('请求失败:', error.message);
console.error('解密失败:', decryptError.message);
console.error('钉钉通知失败:', dingtalkError.message);
```

### 3. 钉钉通知
```javascript
const message = `🚀 执行结果
⏰ 时间: ${new Date().toLocaleString()}
📊 结果: ${result.msg}
⏱️ 耗时: ${timing.totalTime}ms`;
```

## 扩展性设计

### 1. 模块化设计
- 每个模块职责单一
- 模块间松耦合
- 易于测试和维护

### 2. 配置驱动
- 所有参数可配置
- 支持多环境配置
- 动态参数调整

### 3. 插件化架构
- 支持自定义加密算法
- 支持多种通知方式
- 支持自定义重试策略

---

这个技术架构确保了系统的安全性、可靠性和可扩展性，同时提供了良好的用户体验和开发体验。
