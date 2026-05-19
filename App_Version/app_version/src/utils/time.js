// 计算默认执行时间，规则与 gui.py:get_next_run_time 一致
export function getNextRunTime() {
  const now = new Date()
  const today = new Date(now.getFullYear(), now.getMonth(), now.getDate())

  const t0700 = new Date(today)
  t0700.setHours(7, 0, 0, 0)

  const t1130 = new Date(today)
  t1130.setHours(11, 30, 0, 0)

  const t1700 = new Date(today)
  t1700.setHours(17, 0, 0, 0)

  const next0700 = new Date(today)
  next0700.setDate(next0700.getDate() + 1)
  next0700.setHours(7, 0, 0, 0)

  let target
  if (now < t0700) target = t0700
  else if (now < t1130) target = t1130
  else if (now < t1700) target = t1700
  else target = next0700

  return formatDateTime(target)
}

// 将 Date 对象格式化为 "YYYY-MM-DD HH:MM:SS" 字符串
export function formatDateTime(date) {
  const yyyy = date.getFullYear()
  const mm = String(date.getMonth() + 1).padStart(2, '0')
  const dd = String(date.getDate()).padStart(2, '0')
  const hh = String(date.getHours()).padStart(2, '0')
  const mi = String(date.getMinutes()).padStart(2, '0')
  const ss = String(date.getSeconds()).padStart(2, '0')
  return `${yyyy}-${mm}-${dd} ${hh}:${mi}:${ss}`
}

// 将 "YYYY-MM-DD HH:MM:SS" 格式的字符串解析为 Date 对象
// @param {string} text - 日期时间字符串
// @returns {Date} 解析后的 Date 对象
// @throws {Error} 格式不合法时抛出异常
export function parseDateTime(text) {
  const normalized = text.replace(/-/g, '/')
  const date = new Date(normalized)
  if (Number.isNaN(date.getTime())) {
    throw new Error('时间格式必须为 YYYY-MM-DD HH:MM:SS')
  }
  return date
}
