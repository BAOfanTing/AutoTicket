import { APP_VER_NO, CHANNEL, ENDPOINTS } from './constants'
import { buildEncryptedPayload, decryptData2 } from './cryptoService'
import { postJson } from './http'

// 获取当前时间戳字符串（毫秒级）
function nowTs() {
  return String(Date.now())
}

/**
 * 「虽然 result 非 0，但业务上等同已完成」的提示语。
 *
 * 典型场景：当天已签到过，或被其他设备/上次运行完成了签到，
 * 接口会返回「该积分规则当日已到积分上限次数」——这不是失败，
 * 而是任务本来就已经做完了，不能算未完成。
 */
const ALREADY_DONE_KEYWORDS = [
  '已到积分上限',
  '已达积分上限',
  '已签到',
  '重复签到',
  '已经签到',
  '今日已完成',
  '已经完成',
  '已评论'
]

/** 判断一段提示语是否表示"本操作此前已完成" */
function isAlreadyDoneMsg(msg) {
  const text = String(msg || '')
  if (!text) return false
  return ALREADY_DONE_KEYWORDS.some((k) => text.includes(k))
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
  }
  // 当天已签到/已到上限这类，业务上等同于已完成，不显示"失败"以免误导
  if (isAlreadyDoneMsg(msg)) {
    return `${action}: 已完成（${msg}）`
  }
  return `${action}: 失败${msg ? ` - ${msg}` : ''}`
}

// 统一记录日志并返回结果；formatter 默认 JSON.stringify，每日任务传入 formatResultText 输出可读文本
async function executeTask(path, payload, log, formatter = JSON.stringify) {
  const encryptedPayload = buildEncryptedPayload(payload)
  const response = await postJson(path, encryptedPayload)
  const parsed = parseData2Response(response)
  log(formatter(parsed))
  return parsed
}

/** 判断本次兑换是否成功（与 Python 版 is_exchange_success 一致：响应 msg 为"兑换成功"） */
export function isExchangeSuccess(parsed) {
  if (!parsed || typeof parsed !== 'object') return false
  return String(parsed.msg || '').trim() === '兑换成功'
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

  // 逐步收集结果，供调用方判断每日任务是否真的完成
  const steps = []

  steps.push(await executeTask(ENDPOINTS.signin, { ...common, type: '1' }, log, (p) => formatResultText(p, '登录')))

  for (let i = 1; i <= 3; i += 1) {
    steps.push(await executeTask(ENDPOINTS.signin, { ...common, timestamp: nowTs(), type: '5' }, log, (p) => formatResultText(p, `第${i}次签到`)))
  }

  steps.push(await executeTask(
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
  ))

  steps.push(await executeTask(ENDPOINTS.query, { ...common, timestamp: nowTs() }, log, (p) => formatResultText(p, '查询积分')))

  return steps
}

/**
 * 判断单步结果是否等效成功（result === '0' 或命中"已完成"提示）
 */
export function isStepOk(step) {
  if (!step || typeof step !== 'object') return false
  if (String(step.result) === '0') return true
  return isAlreadyDoneMsg(step.msg)
}

/**
 * 判断每日任务各步是否全部成功。
 *
 * 除 result === '0' 外，把「已到上限 / 已签到」这类"本来就完成了"的
 * 提示也算成功，否则当天重复执行会一直被标记为未完成。
 */
export function isDailyTaskComplete(steps) {
  if (!Array.isArray(steps) || steps.length === 0) return false
  return steps.every(isStepOk)
}
