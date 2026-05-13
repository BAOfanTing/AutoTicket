// 与 Python 版本保持一致的基础配置
export const BASE_URL = 'https://app.hzgh.org.cn'
export const CHANNEL = '02'
export const APP_VER_NO = '3.1.7'

export const ENDPOINTS = {
  captcha: '/unionApp/interf/front/U/U067',
  login: '/unionApp/interf/front/U/U004',
  signin: '/unionApp/interf/front/U/U042',
  comment: '/unionApp/interf/front/AC/AC08',
  query: '/unionApp/interf/front/U/U005',
  exchange: '/unionApp/interf/front/OL/OL41'
}

// 小程序端请求头（不能手动设置 User-Agent / Host / Connection）
export const REQUEST_HEADERS = {
  Accept: 'application/json, text/plain, */*',
  'Content-Type': 'application/json;charset=UTF-8'
}
