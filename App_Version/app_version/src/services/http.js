import { BASE_URL, REQUEST_HEADERS } from './constants'

const UNSAFE_HEADERS = new Set(['user-agent', 'host', 'connection', 'content-length'])

function sanitizeHeaders(headers = {}) {
  const safe = {}
  Object.keys(headers).forEach((key) => {
    if (!UNSAFE_HEADERS.has(key.toLowerCase())) {
      safe[key] = headers[key]
    }
  })
  return safe
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
