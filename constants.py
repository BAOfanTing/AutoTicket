"""
constants.py - 接口端点与通用常量定义
统一管理所有后端 API 端点地址，Python 各模块统一从此文件引用。
"""

# 后端服务基础地址
BASE_URL = 'https://app.hzgh.org.cn'

# 接口端点映射（与小程序 constants.js 完全对齐）
ENDPOINTS = {
    'captcha': '/unionApp/interf/front/U/U067',
    'login': '/unionApp/interf/front/U/U004',
    'smsSend': '/unionApp/interf/front/SMS/SMS1',
    'smsLogin': '/unionApp/interf/front/U/U065',
    'dailyLogin': '/unionApp/interf/front/U/U042',
    'signin': '/unionApp/interf/front/U/U042',
    'comment': '/unionApp/interf/front/AC/AC08',
    'query': '/unionApp/interf/front/U/U005',
    'exchange': '/unionApp/interf/front/OL/OL41',
    'qrToken': '/unionApp/interf/front/OL/OL82',
    'qrVisit': '/unionApp/interf/front/OP/OP80',
    'subwayTickets': '/unionApp/interf/front/OL/OL83',
}
