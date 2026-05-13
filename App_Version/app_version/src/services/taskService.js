import { APP_VER_NO, CHANNEL, ENDPOINTS } from './constants'
import { buildEncryptedPayload, decryptData2 } from './cryptoService'
import { postJson } from './http'

function nowTs() {
  return String(Date.now())
}

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

// 统一记录日志并返回结果
async function executeTask(path, payload, log) {
  const encryptedPayload = buildEncryptedPayload(payload)
  const response = await postJson(path, encryptedPayload)
  const parsed = parseData2Response(response)
  log(JSON.stringify(parsed))
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

  await executeTask(ENDPOINTS.signin, { ...common, type: '1' }, (m) => log(`登录结果: ${m}`))

  for (let i = 1; i <= 3; i += 1) {
    await executeTask(ENDPOINTS.signin, { ...common, timestamp: nowTs(), type: '5' }, (m) => log(`第${i}次签到: ${m}`))
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
    (m) => log(`评论结果: ${m}`)
  )

  await executeTask(ENDPOINTS.query, { ...common, timestamp: nowTs() }, (m) => log(`积分查询: ${m}`))
}
