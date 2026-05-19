// 本地存储键名：用户业务配置（如兑换编号等）
const CONFIG_KEY = 'auto_ticket_config'
// 本地存储键名：登录认证信息
const AUTH_KEY = 'auto_ticket_auth'

// 将业务配置保存到本地存储
export function saveConfig(config) {
  uni.setStorageSync(CONFIG_KEY, config)
}

// 从本地存储读取业务配置，无数据时返回空对象
export function loadConfig() {
  return uni.getStorageSync(CONFIG_KEY) || {}
}

// 将登录认证信息保存到本地存储
export function saveAuth(auth) {
  uni.setStorageSync(AUTH_KEY, auth)
}

// 从本地存储读取登录认证信息，无数据时返回空对象
export function loadAuth() {
  return uni.getStorageSync(AUTH_KEY) || {}
}

// 清除本地存储中的登录认证信息（注销时调用）
export function clearAuth() {
  uni.removeStorageSync(AUTH_KEY)
}
