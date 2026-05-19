// ════════════════════════════════════════════════════════════════
// 小程序环境 polyfill：jsencrypt 依赖 crypto.getRandomValues 生成
// RSA PKCS1 填充随机数，但微信小程序没有这个 API。
// 这里用 Math.random() 做 fallback（PKCS1 填充不要求密码学级随机）
// ════════════════════════════════════════════════════════════════
if (typeof globalThis !== 'undefined' && (!globalThis.crypto || !globalThis.crypto.getRandomValues)) {
  if (!globalThis.crypto) globalThis.crypto = {}
  globalThis.crypto.getRandomValues = function (array) {
    for (let i = 0; i < array.length; i++) {
      array[i] = Math.floor(Math.random() * 256)
    }
    return array
  }
}

import CryptoJS from 'crypto-js'
import JSEncrypt from 'jsencrypt'
import { KJUR } from 'jsrsasign'

// 签名密钥（拼接到待签名字符串末尾，与 Python 端一致）
const SIGN_KEY_NEW = 'zSw3MLRV7VuwT!*G'

// 需要进行 3DES 加密的敏感字段集合（包含密码、手机号、金额、验证码等）
const ENCRYPT_KEYS = new Set([
  'login_name',
  'login_auth_code',
  'auth_code',
  'pwd',
  'password',
  'newpwd',
  'amt',
  'tr_amt',
  'sms_code',
  'total_amount',
  'account_no',
  'mob_data',
  'order_amt',
  'before_amt',
  'txn_amt',
  'tel',
  'mobile',
  'new_mobile',
  'code',
  'cert_no',
  'card_no',
  'reserve_mobile',
  'reply_tel',
  'card_bal',
  'bank_card_no',
  'car_no',
  'user_id',
  'invite_code',
  'imgAuthCode',
  'imgUniCode'
])

// 不参与签名计算的字段集合（大体积或二进制数据，签名前需排除）
const NO_SIGN_KEYS = new Set([
  'answerContent',
  'surveyId',
  'content',
  'preContent',
  'img',
  'img1',
  'img2',
  'package',
  'codeUrl',
  'belong',
  'verCode'
])

// RSA 公钥（用于加密 sessionKey，与 Login.py / AutoTicket.py 保持一致）
const ENCRYPTION_PUBLIC_KEY_PEM = `-----BEGIN PUBLIC KEY-----
MIGfMA0GCSqGSIb3DQEBAQUAA4GNADCBiQKBgQC7yWoQaojBBqKI2H0j4e8ZeX/n1yip6hxrxSVth5F5n1JJ/B3liPMdz6K1chNLFTAcbI7hTL9KkphP9yQ+bPYD68Ajrt/DFrW679Zi1CoeetHVrM4sF68lYarGXwnSlKloaPWnI4Ch9cSqIvIOInlpeJqYPlJ8ZJvGCmbQoM6bewIDAQAB
-----END PUBLIC KEY-----`

// RSA 私钥（用于请求签名 RSA-SHA256，与 Login.py / AutoTicket.py 保持一致）
const SIGNING_PRIVATE_KEY_PEM = `-----BEGIN PRIVATE KEY-----
MIICeAIBADANBgkqhkiG9w0BAQEFAASCAmIwggJeAgEAAoGBAJ+C8Z9awsGU8DeB
pq47p+pVBgIxWr9epYE5lTrVwoTvOv7dOBTsNgYPgDqFLbU8eZsV26DOvgd4TC5t
ZUWF7WbAleOcxvwA143XTBpZEeDx6who8KiW1WBKUwkeEfXZvOWhN2d+8GlCjvJu
2J4yNGEXScQEIWb+ofE4Pd4yPkkzAgMBAAECgYB0Tzu18a0vEFX0c1JBm3g98w81
jB1aiz3tMzqwMuvqmLIQ4uegwfhGhQkAItoIW/dj8RU7dWS096+87sG4ZwaKCv/S
mT1CibqmSATrX6YNIFU4uXsZzMREJxmZi+V5AllT9DWBG5YjKgrGfWjL0Rq10Zvx
YMTdjO+SbqDIjVoc+QJBAOrMXRO6G349NpLvo1QPevxIykKNKhr5Qkjv4oVydoVo
HW6iMU30PhrBqBYla+K8W+xyeqrjd9ucDQFW/Z2+hD8CQQCt6jz4o7qadQM0giko
BsgWwp7teyZI/8ZH5htrKZwDJzUe6LuM9xjDeXAqqjNjQrDL7M+6T7ZwMmK3UN3b
oe4NAkEA6ioGabYh1TSXSNNVwG/v58twbA78/wm34aXb89rD+Shssflv0p7TkTuxt
uR7RBU2WAmT7PoOfyaSkdN/++IVYQJBAJ/klCvQc/YfkFPNO0N2gK0UP4N8zmUc
6tIdh6XNeocXm+oP9KaUYusMkghXtKkUnnDOBul28fdTC5kYOvD7fl0CQQDLIYfo
8MSMgcFkBH1wRUbhjVv31bk8+4G9a+h7UkLdLtch5qPsS7bsFCyszqEYjhYtQ278
Q20lSzaIsom0Q3ai
-----END PRIVATE KEY-----`

// RSA 私钥（用于解密服务端返回的 data2 字段）
const PRIVATE_KEY_PEM = `-----BEGIN RSA PRIVATE KEY-----
MIICdQIBADANBgkqhkiG9w0BAQEFAASCAl8wggJbAgEAAoGBAIOBMtf2AIYQlrNy
/lVPHx4R/LKI+Vtk3bKmzID8vdVnh/4WA3lczqfejM10Xfy3sNe4l5EeQTvnDgUH
bIFK8FyJRpvypAmS9oyW6uwGTjZEu5Y6hsSxiGAOG5ZOlH8vOSfuaAkZ+iUlqifP
E3ZOmHkqGzmukg4wCRaPLx5ioq8zAgMBAAECgYAgLOVmx677HmXxBCrMbq57agU9
HZx9SyGfS4Zv7Ob5pvo0Jei1sgpyMlabEmTIp50iOu0CubdWU8MvYdCfldlXQLW7
cjk8N1NyGQLFd2fJ03a7gGWnwwEdPoNTpSHnB+mDL9l7MVjion5fLojzq9Pz1gMK
L01I2TfZBDL4m6EbgQJBAMfgrMKtj7f40GA3qp/y/9/eBCAu8PbtFmtATLMQRf4t
Ghjvn349x1b6FZj8RiaRBSrq0Owjrdo5TUxgfS7dz3MCQQCobdWk2SQhRlqEHfFE
ro/8ab6gn3GhBDzzKvNjhKr2MO6JWqs+Vr+/P9uYpA+G+rv74uVIGWhjuNtI5+/6
9DFBAkAJOQS/tuJ6yrBSwD7PQpcr7UKjeYcE3cu7ByyC1q1kHRCnNedWG+Omz8NP
W9Sg0vA6GrupKbxL5Xj7nTgpgXKhAkBIVlvioAvfaqrngUClAd//RZ9EtxYDVKGk
wnaj8E/Iyr04KsPPU0ypJBD5XsT4cOmZxho5PAhUhAlSJ6MvAf/BAkA64ieVhtQA
1KV0pSSEJMnbPlZe+yBYGTWLMaG2zL0kKEhIs2fIHbVhLFQ8TkO5oH+mhxuuXI5+
nVU2G0dqUl6D
-----END RSA PRIVATE KEY-----`

// 生成与 Python rand_str 一致的随机字符串
export function randStr(length = 24) {
  const chars = 'abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789'
  let result = ''
  for (let i = 0; i < length; i += 1) {
    result += chars[Math.floor(Math.random() * chars.length)]
  }
  return result.toUpperCase()
}

// RSA 公钥加密
export function rsaEncrypt(publicKeyPem, plaintext) {
  const encryptor = new JSEncrypt()
  encryptor.setPublicKey(publicKeyPem)
  const encrypted = encryptor.encrypt(plaintext)
  if (!encrypted) {
    throw new Error('RSA 加密失败')
  }
  return encrypted
}

// 3DES ECB PKCS7 加密
export function des3EcbPkcs7Encrypt(key24, plaintext) {
  const keyWordArray = CryptoJS.enc.Utf8.parse(key24)
  const encrypted = CryptoJS.TripleDES.encrypt(plaintext, keyWordArray, {
    mode: CryptoJS.mode.ECB,
    padding: CryptoJS.pad.Pkcs7
  })
  return encrypted.toString()
}

// RSA-SHA256 签名
export function rsaSha256Sign(privateKeyPem, dataString) {
  const signature = new KJUR.crypto.Signature({ alg: 'SHA256withRSA' })
  signature.init(privateKeyPem)
  signature.updateString(dataString)
  return CryptoJS.enc.Base64.stringify(CryptoJS.enc.Hex.parse(signature.sign()))
}

// data2 解密，等价于 Python decrypt_data2
export function decryptData2(data2) {
  const rsaEnc = data2.slice(0, 172)
  const desEnc = data2.slice(172)

  const decryptor = new JSEncrypt()
  decryptor.setPrivateKey(PRIVATE_KEY_PEM)
  const rsaPlain = decryptor.decrypt(rsaEnc)
  if (!rsaPlain) {
    throw new Error('RSA 解密失败')
  }

  const keyStr = `HTt0Hzsu${rsaPlain}`
  const keyWordArray = CryptoJS.enc.Utf8.parse(keyStr.slice(0, 24))
  const ivWordArray = CryptoJS.enc.Utf8.parse(rsaPlain.slice(0, 8))

  const decrypted = CryptoJS.TripleDES.decrypt(
    { ciphertext: CryptoJS.enc.Base64.parse(desEnc) },
    keyWordArray,
    {
      iv: ivWordArray,
      mode: CryptoJS.mode.CBC,
      padding: CryptoJS.pad.Pkcs7
    }
  )

  return CryptoJS.enc.Utf8.stringify(decrypted)
}

// 构建通用加密请求体，复用 AutoTicket.py 的字段规则
export function buildEncryptedPayload(rawPayload) {
  const payload = { ...rawPayload }
  const filtered = {}
  Object.keys(payload).forEach((key) => {
    const value = payload[key]
    if (value === 0 || (value !== undefined && value !== null && value !== '')) {
      filtered[key] = value
    }
  })

  const sessionKey = randStr(24)
  filtered.dec_key = rsaEncrypt(ENCRYPTION_PUBLIC_KEY_PEM, sessionKey)

  Object.keys(filtered).forEach((key) => {
    if (ENCRYPT_KEYS.has(key)) {
      filtered[key] = des3EcbPkcs7Encrypt(sessionKey, String(filtered[key]))
    }
  })

  const keysForSign = []
  const valuesForSign = []
  Object.keys(filtered).forEach((key) => {
    if (!NO_SIGN_KEYS.has(key)) {
      keysForSign.push(key)
      valuesForSign.push(String(filtered[key]))
    }
  })

  const signText = `${valuesForSign.join('')}${SIGN_KEY_NEW}`
  filtered.key = keysForSign.join(',')
  filtered.sign = rsaSha256Sign(SIGNING_PRIVATE_KEY_PEM, signText)

  return filtered
}
