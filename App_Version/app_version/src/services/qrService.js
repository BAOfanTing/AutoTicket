import { APP_VER_NO, CHANNEL, ENDPOINTS } from './constants'
import { buildEncryptedPayload, decryptData2 } from './cryptoService'
import { postJson } from './http'

// 获取当前时间戳字符串（毫秒级）
function nowTs() {
  return String(Date.now())
}

// OL82 - 获取绿色出行码 token
// @param {string} userId - 用户 ID
// @param {string} sesId - 会话 ID
// @returns {Promise<string>} 返回 QR token
export async function getQrToken(userId, sesId) {
  if (!userId || !sesId) {
    throw new Error('user_id 和 ses_id 不能为空')
  }

  const payload = buildEncryptedPayload({
    channel: CHANNEL,
    app_ver_no: APP_VER_NO,
    timestamp: nowTs(),
    user_id: userId,
    ses_id: sesId
  })

  const response = await postJson(ENDPOINTS.qrToken, payload)
  if (!response || !response.data2) {
    throw new Error('OL82 接口返回缺少 data2')
  }

  try {
    const plain = decryptData2(response.data2)
    const data = JSON.parse(plain)
    if (data.result !== '0' || !data.data) {
      throw new Error(data.msg || '获取 token 失败')
    }
    return data.data.token
  } catch (error) {
    throw new Error(`OL82 响应解密失败: ${error.message || error}`)
  }
}

// OP80 - 记录用户访问量（统计接口，静默上传不抛错）
// @param {string} userId - 用户 ID
export async function recordQrVisit(userId) {
  if (!userId) return

  const payload = buildEncryptedPayload({
    channel: CHANNEL,
    app_ver_no: APP_VER_NO,
    timestamp: nowTs(),
    user_id: userId,
    icon_id: '92',
    type: '2'
  })

  try {
    await postJson(ENDPOINTS.qrVisit, payload)
  } catch {
    // 忽略，只是统计数据
  }
}

// 获取乘车码二维码数据（第三方接口，请求杭州公交码引擎 /hzcitizencodeengine/codeEngine/apply）
// @param {string} token - QR 认证 token
// @returns {Promise<Object>} 返回包含二维码数据的响应对象
export async function getQrCode(token) {
  if (!token) {
    throw new Error('token 不能为空')
  }

  const ts = String(Date.now())
  const globalSeq = '2500' + Array.from({ length: 14 }, () =>
    Math.floor(Math.random() * 16).toString(16)
  ).join('')

  const payload = {
    latitude: null,
    longitude: null,
    version: '1.0.0',
    isImage: '1',
    timestamp: ts,
    globalSeq
  }

  return new Promise((resolve, reject) => {
    uni.request({
      url: 'https://hzcode.96225.com/hzcitizencodeengine/codeEngine/apply',
      method: 'POST',
      header: {
        'Content-Type': 'application/json;charset=UTF-8',
        token
      },
      data: JSON.stringify(payload),
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

// 完整流程：获取并展示绿色出行码
export async function getGreenTravelCode(userId, sesId) {
  // 1. 获取 token
  const token = await getQrToken(userId, sesId)
  if (!token) {
    throw new Error('获取 token 失败')
  }

  // 2. 获取乘车码
  const result = await getQrCode(token)
  if (!result || result.respCode !== '00') {
    throw new Error(result.respDesc || '获取乘车码失败')
  }

  // 3. 后台记录访问
  recordQrVisit(userId)

  return result.data
}
