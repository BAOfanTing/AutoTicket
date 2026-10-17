/**
 * statsService.js - 在线人数 / 抢票数统计服务
 *
 * 与 Python 版 stats_client.py 对应，使用 uni.request 实现。
 * 所有请求均为 fire-and-forget，超时短、异常全部吞掉，不影响主流程。
 * 未配置服务端地址时，所有函数静默返回。
 */

// ================= 配置 =================
const DEFAULT_API_BASE = ''
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

/** 上报上线 / 下线 */
export async function reportOnline(action = 'open') {
  _ensureReady()
  const data = await _request('POST', PATH_ONLINE, {
    client_id: getClientId(),
    action
  })
  return data ? data.online : null
}

/** 上报下线（短超时） */
export async function reportOffline() {
  _ensureReady()
  await _request('POST', PATH_ONLINE, {
    client_id: getClientId(),
    action: 'close'
  })
}

/** 上报抢到票 */
export async function reportGrab(exchangeId) {
  _ensureReady()
  if (!_apiBase) return
  _request('POST', PATH_GRAB, {
    client_id: getClientId(),
    exchange_id: String(exchangeId)
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
    }
  }
}
