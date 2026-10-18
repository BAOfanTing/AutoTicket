/**
 * statsService.js - 在线人数 / 抢票数统计服务
 *
 * 与 Python 版 stats_client.py 对应，使用 uni.request 实现。
 * 所有请求均为 fire-and-forget，超时短、异常全部吞掉，不影响主流程。
 * 未配置服务端地址时，所有函数静默返回。
 */

// ================= 配置 =================
// 统计服务端地址。小程序必须是小程序管理后台白名单内的域名，不能用裸 IP。
// 需要在小程序后台把 https://www.relx5th.space 加入 request 合法域名。
const DEFAULT_API_BASE = 'https://www.relx5th.space'
const PATH_ONLINE = '/api/v1/online'
const PATH_GRAB = '/api/v1/grab'
const PATH_STATS = '/api/v1/stats'
const TIMEOUT = 3000 // ms

let _apiBase = DEFAULT_API_BASE
let _clientId = ''
let _loaded = false

// ================= 本地配置 =================
function _ensureReady() {
  if (_loaded) return
  try {
    const config = uni.getStorageSync('auto_ticket_config') || {}
    // 本地存储未配置时回退到内嵌地址，否则每次安装后统计都是静默关闭的
    _apiBase = (config.statsApiBase || DEFAULT_API_BASE || '').trim()
    _clientId = (config.clientId || '').trim()
    if (!_clientId) {
      _clientId = _generateId()
      config.clientId = _clientId
      uni.setStorageSync('auto_ticket_config', config)
    }
    _loaded = true
  } catch {
    _loaded = true
  }
}

function _generateId() {
  return 'xxxxxxxx-xxxx-4xxx-yxxx-xxxxxxxxxxxx'.replace(/[xy]/g, (c) => {
    const r = (Math.random() * 16) | 0
    const v = c === 'x' ? r : (r & 0x3) | 0x8
    return v.toString(16)
  })
}

// ================= 对外接口 =================
export function isStatsEnabled() {
  _ensureReady()
  return !!_apiBase
}

export function getClientId() {
  _ensureReady()
  return _clientId
}

/**
 * 按账号生成的客户端标识。
 *
 * 在线人数按 client_id 去重，同一台手机跑多个账号时如果都用同一个标识，
 * 服务端只会算一个人。这里拼上账号标识，让每个账号占独立的一条在线记录。
 *
 * @param {string} accountKey 账号唯一标识（优先 userId，其次 loginName）
 */
export function getScopedClientId(accountKey) {
  _ensureReady()
  const raw = String(accountKey || '').trim()
  if (!raw) return _clientId
  // 只保留服务端 client_id 允许的字符（A-Za-z0-9_-），长度截断
  const safe = raw.replace(/[^A-Za-z0-9_-]/g, '').slice(0, 24)
  if (!safe) return _clientId
  return `${_clientId.slice(0, 32)}-${safe}`.slice(0, 64)
}

function _url(path) {
  return _apiBase.replace(/\/$/, '') + path
}

function _request(method, path, payload) {
  if (!_apiBase) return Promise.resolve(null)
  return new Promise((resolve) => {
    uni.request({
      url: _url(path),
      method,
      timeout: TIMEOUT,
      data: method === 'GET' ? undefined : payload,
      header: { 'Content-Type': 'application/json;charset=UTF-8' },
      success: (res) => {
        try {
          const body = res.data
          if (body && body.code === 0) {
            resolve(body.data || null)
          } else {
            resolve(null)
          }
        } catch {
          resolve(null)
        }
      },
      fail: () => resolve(null)
    })
  })
}

/** 上报上线 / 下线（accountKey 用于让多个账号各占一条在线记录） */
export async function reportOnline(action = 'open', accountKey = '') {
  _ensureReady()
  const data = await _request('POST', PATH_ONLINE, {
    client_id: getScopedClientId(accountKey),
    action
  })
  return data ? data.online : null
}

/** 上报下线（短超时） */
export async function reportOffline(accountKey = '') {
  _ensureReady()
  await _request('POST', PATH_ONLINE, {
    client_id: getScopedClientId(accountKey),
    action: 'close'
  })
}

/**
 * 上报抢到票。
 *
 * 每张票生成独立的 requestId，服务端据此幂等去重：
 * 同一张票的网络重试复用同一个 requestId（只算 1 张），
 * 真实抢到多张票时 requestId 各不相同（正确计多张）。
 */
export async function reportGrab(exchangeId, accountKey = '') {
  _ensureReady()
  if (!_apiBase) return
  const requestId = `g-${Date.now()}-${Math.random().toString(36).slice(2, 18)}`
  _request('POST', PATH_GRAB, {
    client_id: getScopedClientId(accountKey),
    exchange_id: String(exchangeId),
    request_id: requestId
  })
}

/** 拉取统计数据 */
export async function fetchStats() {
  _ensureReady()
  const data = await _request('GET', PATH_STATS)
  if (!data || typeof data !== 'object') return null
  const byType = (data.by_type && typeof data.by_type === 'object') ? data.by_type : {}
  return {
    online: parseInt(data.online) || 0,
    total: parseInt(data.total) || 0,
    by_type: {
      '9': parseInt(byType['9']) || 0,
      '10': parseInt(byType['10']) || 0,
      '11': parseInt(byType['11']) || 0
    },
    // 服务端开关：false 表示服务端已关闭统计，界面应隐藏实时统计模块。
    // 老版本服务端没有该字段时按 true 处理。
    stats_enabled: data.stats_enabled !== false
  }
}
