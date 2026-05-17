import md5 from 'crypto-js/md5'
import { APP_VER_NO, CHANNEL, ENDPOINTS } from './constants'
import { buildEncryptedPayload, decryptData2 } from './cryptoService'
import { postJson } from './http'

function nowTs() {
  return String(Date.now())
}

// 获取验证码（对应 Login.py:get_captcha_u067）
export async function getCaptchaU067() {
  const payload = buildEncryptedPayload({
    channel: CHANNEL,
    app_ver_no: APP_VER_NO,
    timestamp: nowTs(),
    term_sys_ver: '12',
    root: '0',
    term_sys: '2',
    model: '24031PN0DC',
    term_id: '42e85afdd7e346e5',
    trcode: 'U/U067'
  })

  const response = await postJson(ENDPOINTS.captcha, payload)
  if (!response || !response.data2) {
    throw new Error('验证码接口返回缺少 data2')
  }

  try {
    const plain = decryptData2(response.data2)
    const parsed = JSON.parse(plain)
    if (parsed.result !== '0') {
      throw new Error(parsed.msg || '验证码接口返回失败')
    }
    if (!parsed.imgUniCode) {
      throw new Error('验证码响应缺少 imgUniCode')
    }
    if (!parsed.img) {
      throw new Error('验证码响应缺少 img')
    }
    return parsed
  } catch (error) {
    throw new Error(`验证码响应解密失败: ${error.message || error}`)
  }
}

function normalizeBase64(raw) {
  if (!raw) return '';

  // 1. 提取内容
  let content = raw.includes(',') ? raw.split(',', 2)[1] : raw;

  // 2. 深度清洗：必须去除反斜杠 \ 和 所有空白符
  // 很多时候解密出来的字符串会带 "\/9j\/..." 这种转义
  let normalized = String(content)
    .replace(/\\/g, '')     // 关键：去掉所有反斜杠
    .replace(/\s/g, '')     // 去掉换行、空格
    .replace(/-/g, '+')
    .replace(/_/g, '/');

  // 3. 补齐长度
  const mod = normalized.length % 4;
  if (mod !== 0) {
    normalized += '='.repeat(4 - mod);
  }

  return normalized;
}

function normalizeLocalImagePath(filePath) {
  if (!filePath) return ''
    // 统一转换：无论 http://usr/ 还是直接的 /usr/，都转为 wxfile://usr/
    return filePath.replace('http://usr/', 'wxfile://usr/').replace(/^\/?usr\//, 'wxfile://usr/')
}

// 将 base64 图片数据写入临时文件，返回可被 image 组件加载的路径
function base64ToFilePath(base64Data) {
  return new Promise((resolve, reject) => {
    // 尝试提取 data:image/xxx;base64, 前缀；没有则当作纯 base64 处理
    const match = /data:image\/(\w+);base64,(.*)/.exec(base64Data);
    let format, body;
    if (match) {
      format = match[1];
      body = match[2];
    } else {
      // 纯 base64，默认 jpg
      format = 'jpg';
      body = base64Data;
    }

    const filePath = `${wx.env.USER_DATA_PATH}/captcha_${Date.now()}.${format}`;
    const fsm = wx.getFileSystemManager();
    fsm.writeFile({
      filePath,
      data: body,
      encoding: 'base64',
      success() { resolve(filePath); },
      fail(err) { reject(new Error('写入验证码图片失败: ' + (err.errMsg || JSON.stringify(err)))); }
    });
  });
}

// 解析验证码图片，优先返回小程序可直接加载的本地临时路径
export async function decodeCaptchaImage(captchaData) {
  const raw = (captchaData && captchaData.img) || ''
  if (!raw) {
    throw new Error('验证码图片为空')
  }

  // 先归一化 base64（处理反斜杠、空白、URL-safe 编码等）
  const pureBase64 = normalizeBase64(raw)
  if (!pureBase64) {
    throw new Error('验证码图片数据无效')
  }

  // 补上 data URL 前缀
  const dataUrl = `data:image/jpeg;base64,${pureBase64}`

  // 优先写入临时文件（性能更好）
  try {
    const rawPath = await base64ToFilePath(dataUrl)
    console.log('[captcha] write success:', rawPath)
    return rawPath
  } catch (err) {
    console.error('[captcha] base64ToFilePath failed:', err.message)
  }

  // fallback：直接返回 data URL
  return dataUrl
}

// 发送短信验证码（对应 Login.py:send_sms）
export async function sendSms(captchaData, phone, imgAuthCode) {
  if (!captchaData || !captchaData.imgUniCode) {
    throw new Error('验证码标识 imgUniCode 缺失')
  }
  if (!phone || !imgAuthCode) {
    throw new Error('手机号和图形验证码均不能为空')
  }

  console.log('[sendSms] 构建请求 payload...')
  const payload = buildEncryptedPayload({
    channel: CHANNEL,
    app_ver_no: APP_VER_NO,
    timestamp: nowTs(),
    term_sys_ver: '12',
    root: '0',
    term_sys: '2',
    model: '24031PN0DC',
    login_name: phone,
    mobile: phone,
    imgUniCode: captchaData.imgUniCode,
    imgAuthCode: imgAuthCode.trim(),
    sms_type: '10'
  })
  console.log('[sendSms] payload key 顺序:', payload.key)
  console.log('[sendSms] 请求 URL:', ENDPOINTS.smsSend)

  const response = await postJson(ENDPOINTS.smsSend, payload)
  console.log('[sendSms] 响应:', response ? (response.data2 ? '有 data2' : '无 data2') : '空响应')

  if (!response || !response.data2) {
    throw new Error('短信发送接口返回缺少 data2')
  }

  try {
    const plain = decryptData2(response.data2)
    console.log('[sendSms] 解密成功:', plain)
    return JSON.parse(plain)
  } catch (error) {
    throw new Error(`短信发送响应解密失败: ${error.message || error}`)
  }
}

// 短信验证码登录（对应 Login.py:login_u065）
export async function loginU065(phone, authCode) {
  if (!phone || !authCode) {
    throw new Error('手机号和短信验证码均不能为空')
  }

  const payload = buildEncryptedPayload({
    channel: CHANNEL,
    app_ver_no: APP_VER_NO,
    timestamp: nowTs(),
    term_sys_ver: '12',
    root: '0',
    term_sys: '2',
    model: '24031PN0DC',
    term_id: '42e85afdd7e346e5',
    login_name: phone,
    auth_code: authCode.trim()
  })

  const response = await postJson(ENDPOINTS.smsLogin, payload)
  if (!response || !response.data2) {
    throw new Error('短信登录接口返回缺少 data2')
  }

  try {
    const plain = decryptData2(response.data2)
    return JSON.parse(plain)
  } catch (error) {
    throw new Error(`短信登录响应解密失败: ${error.message || error}`)
  }
}

// 提交登录（对应 Login.py:login_u004_with_code）
export async function loginU004WithCode(captchaData, phone, password, imgAuthCode) {
  if (!captchaData || !captchaData.imgUniCode) {
    throw new Error('验证码标识 imgUniCode 缺失')
  }
  if (!phone || !password || !imgAuthCode) {
    throw new Error('手机号、密码、验证码均不能为空')
  }

  const payload = buildEncryptedPayload({
    channel: CHANNEL,
    app_ver_no: APP_VER_NO,
    timestamp: nowTs(),
    term_sys_ver: '12',
    root: '0',
    term_sys: '2',
    model: '24031PN0DC',
    term_id: '42e85afdd7e346e5',
    login_name: phone,
    pwd: md5(password).toString(),
    imgUniCode: captchaData.imgUniCode,
    imgAuthCode: imgAuthCode.trim()
  })

  const response = await postJson(ENDPOINTS.login, payload)
  if (!response || !response.data2) {
    throw new Error('登录接口返回缺少 data2')
  }

  try {
    const plain = decryptData2(response.data2)
    return JSON.parse(plain)
  } catch (error) {
    throw new Error(`登录响应解密失败: ${error.message || error}`)
  }
}
