import { APP_VER_NO, CHANNEL, ENDPOINTS } from './constants'
import { buildEncryptedPayload, decryptData2 } from './cryptoService'
import { postJson } from './http'

// 获取当前时间戳字符串（毫秒级）
function nowTs() {
  return String(Date.now())
}

// 解密并解析服务端加密响应 data2 字段，返回 JSON 对象
// 若 JSON 解析失败则返回 { raw: plaintext }
function parseData2Response(response) {
  if (!response || !response.data2) {
    throw new Error('接口返回缺少 data2')
  }
  const plain = decryptData2(response.data2)
  try {
    return JSON.parse(plain)
  } catch {
    return { raw: plain }
  }
}

// 将每日任务解密响应格式化为人类可读的结果文本（非 JSON）
function formatResultText(parsed, action = '操作') {
  if (!parsed || typeof parsed !== 'object') {
    return `${action}: 响应格式异常`
  }
  const result = String(parsed.result || '')
  const msg = String(parsed.msg || '')
  if (result === '0') {
    const parts = [`${action}: 成功`]
    if (msg) parts.push(`(${msg})`)
    if (parsed.remain_integral !== undefined && parsed.remain_integral !== null) {
      parts.push(`剩余积分: ${parsed.remain_integral}`)
      if (parsed.total_integral !== undefined && parsed.total_integral !== null) {
        parts.push(`总积分: ${parsed.total_integral}`)
      }
    }
    return parts.join('  ')
  } else {
    return `${action}: 失败${msg ? ` - ${msg}` : ''}`
  }
}

// 统一记录日志并返回结果；formatter 默认 JSON.stringify，每日任务传入 formatResultText 输出可读文本
async function executeTask(path, payload, log, formatter = JSON.stringify) {
  const encryptedPayload = buildEncryptedPayload(payload)
  const response = await postJson(path, encryptedPayload)
  const parsed = parseData2Response(response)
  log(formatter(parsed))
  return parsed
}

// 对应 AutoTicket.py 的 build_payload + run_exchange
export async function runExchangeOnce({ loginName, userId, sesId, exchangeId, log }) {
  return executeTask(
    ENDPOINTS.exchange,
    {
      channel: CHANNEL,
      app_ver_no: APP_VER_NO,
      timestamp: nowTs(),
      login_name: loginName,
      user_id: userId,
      ses_id: sesId,
      exchange_id: String(exchangeId)
    },
    log
  )
}

// 对应 AutoTicket.py 的每日任务链路
export async function runDailyTaskWorkflow({ loginName, sesId, log }) {
  const common = {
    channel: CHANNEL,
    app_ver_no: '3.1.4',
    timestamp: nowTs(),
    login_name: loginName,
    ses_id: sesId
  }

  log('开始执行每日任务：登录 -> 3次签到 -> 评论 -> 查询积分')

  await executeTask(ENDPOINTS.signin, { ...common, type: '1' }, log, (p) => formatResultText(p, '登录'))

  for (let i = 1; i <= 3; i += 1) {
    await executeTask(ENDPOINTS.signin, { ...common, timestamp: nowTs(), type: '5' }, log, (p) => formatResultText(p, `第${i}次签到`))
  }

  await executeTask(
    ENDPOINTS.comment,
    {
      ...common,
      timestamp: nowTs(),
      related_id: '1232',
      content_type: '1',
      oper_type: '0',
      suffix: 'png',
      content: '好'
    },
    log,
    (p) => formatResultText(p, '评论')
  )

  await executeTask(ENDPOINTS.query, { ...common, timestamp: nowTs() }, log, (p) => formatResultText(p, '查询积分'))
}
