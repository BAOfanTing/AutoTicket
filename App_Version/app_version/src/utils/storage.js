// 本地存储键名：用户业务配置（如兑换编号等）
const CONFIG_KEY = 'auto_ticket_config'
// 本地存储键名：登录认证信息
const AUTH_KEY = 'auto_ticket_auth'
// 本地存储键名：多开 Profile 列表
const PROFILES_KEY = 'auto_ticket_profiles'
// 本地存储键名：当前选中的 Profile 索引
const ACTIVE_PROFILE_KEY = 'auto_ticket_active_profile'

// ==================== 配置 ====================
// 将业务配置保存到本地存储
export function saveConfig(config) {
  uni.setStorageSync(CONFIG_KEY, config)
}

// 从本地存储读取业务配置，无数据时返回空对象
export function loadConfig() {
  return uni.getStorageSync(CONFIG_KEY) || {}
}

// ==================== 认证 ====================
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

// ==================== 多开 Profile ====================
// 保存 Profile 列表
export function saveProfiles(profiles) {
  uni.setStorageSync(PROFILES_KEY, profiles)
}

// 读取 Profile 列表，无数据时返回空数组
export function loadProfiles() {
  return uni.getStorageSync(PROFILES_KEY) || []
}

// 保存当前选中的 Profile 索引
export function saveActiveProfileIndex(index) {
  uni.setStorageSync(ACTIVE_PROFILE_KEY, index)
}

// 读取当前选中的 Profile 索引，无数据时返回 0
export function loadActiveProfileIndex() {
  return uni.getStorageSync(ACTIVE_PROFILE_KEY) || 0
}

// 清除所有 Profile 数据
export function clearProfiles() {
  uni.removeStorageSync(PROFILES_KEY)
  uni.removeStorageSync(ACTIVE_PROFILE_KEY)
}
