import { BASE_URL, REQUEST_HEADERS } from './constants'

// 不允许手动设置的请求头（uni-app 运行环境自动管理这些字段）
const UNSAFE_HEADERS = new Set(['user-agent', 'host', 'connection', 'content-length'])

// 过滤掉会被 uni-app 运行时自动覆盖的请求头
function sanitizeHeaders(headers = {}) {
  const safe = {}
  Object.keys(headers).forEach((key) => {
    if (!UNSAFE_HEADERS.has(key.toLowerCase())) {
      safe[key] = headers[key]
    }
  })
  return safe
}

// 发起请求并解析响应头中的 Date 字段，返回服务器时间戳（毫秒）
export function fetchServerTime(path, data) {
  return new Promise((resolve, reject) => {
    uni.request({
      url: `${BASE_URL}${path}`,
      method: 'POST',
      header: sanitizeHeaders(REQUEST_HEADERS),
      data: typeof data === 'string' ? data : JSON.stringify(data),
      success: (res) => {
        if (res.statusCode < 200 || res.statusCode >= 300) {
          reject(new Error(`请求失败，状态码: ${res.statusCode}`))
          return
        }
        const header = res.header || {}
        const dateHeader = header.Date || header.date || header['date'] || header['Date']
        if (!dateHeader) {
          reject(new Error('响应头缺少 Date 字段'))
          return
        }
        const serverTime = new Date(dateHeader).getTime()
        if (Number.isNaN(serverTime)) {
          reject(new Error('服务器时间格式无效'))
          return
        }
        resolve(serverTime)
      },
      fail: (err) => reject(new Error((err && err.errMsg) || '网络请求失败'))
    })
  })
}

// uni.request Promise 包装，统一错误处理
export function postJson(path, data) {
  return new Promise((resolve, reject) => {
    uni.request({
      url: `${BASE_URL}${path}`,
      method: 'POST',
      header: sanitizeHeaders(REQUEST_HEADERS),
      data: typeof data === 'string' ? data : JSON.stringify(data),
      success: (res) => {
        if (res.statusCode >= 200 && res.statusCode < 300) {
          resolve(res.data)
        } else {
          reject(new Error(`请求失败，状态码: ${res.statusCode}`))
        }
      },
      fail: (err) => reject(new Error((err && err.errMsg) || '网络请求失败'))
    })
  })
}
