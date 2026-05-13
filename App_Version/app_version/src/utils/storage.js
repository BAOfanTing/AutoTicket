const CONFIG_KEY = 'auto_ticket_config'
const AUTH_KEY = 'auto_ticket_auth'

// 保存业务配置
export function saveConfig(config) {
  uni.setStorageSync(CONFIG_KEY, config)
}

// 读取业务配置
export function loadConfig() {
  return uni.getStorageSync(CONFIG_KEY) || {}
}

// 保存登录态
export function saveAuth(auth) {
  uni.setStorageSync(AUTH_KEY, auth)
}

// 读取登录态
export function loadAuth() {
  return uni.getStorageSync(AUTH_KEY) || {}
}

// 清空登录态
export function clearAuth() {
  uni.removeStorageSync(AUTH_KEY)
}
