"""
AutoTicket.py - 杭州工会 App 自动化核心模块
提供优惠券兑换、每日任务（登录+签到+评论+查询积分）等自动化操作接口。
"""

import requests
import time
import random
import string
import base64
import json
from datetime import datetime, timedelta
from email.utils import parsedate_to_datetime
import threading
from Crypto.PublicKey import RSA
from Crypto.Signature import pkcs1_15
from Cryptodome.Hash import SHA256
from Crypto.Cipher import DES3, PKCS1_v1_5
from Crypto.Util.Padding import pad, unpad
import urllib3
import concurrent.futures
# 禁用 SSL 警告（自签名证书兼容）
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# ================= 配置区域 =================
# 以下为 App 服务端通信所需的参数、密钥和运行时配置
CHANNEL = "02"
APP_VER_NO = "3.1.7"

# ============ 线程本地运行态（支持多账号并发任务） ============
# 每个 Worker 线程在运行时通过 set_thread_context() 写入自己的凭证与日志回调，
# build_payload / 日志输出等读取时优先取线程本地值，取不到再回退到模块全局值，
# 从而避免多账号同时跑任务时凭证、日志互相覆盖串号。
import threading as _threading
_thread_ctx = _threading.local()

def set_thread_context(login_name=None, user_id=None, ses_id=None, exchange_id=None, log_cb=None):
    """在当前线程内设置账号上下文（不影响其他线程）。"""
    if login_name is not None: _thread_ctx.login_name = login_name
    if user_id is not None: _thread_ctx.user_id = user_id
    if ses_id is not None: _thread_ctx.ses_id = ses_id
    if exchange_id is not None: _thread_ctx.exchange_id = exchange_id
    if log_cb is not None: _thread_ctx.log_cb = log_cb

def clear_thread_context():
    """清除当前线程的账号上下文。"""
    for attr in ('login_name', 'user_id', 'ses_id', 'exchange_id', 'log_cb'):
        if hasattr(_thread_ctx, attr):
            delattr(_thread_ctx, attr)

def _ctx(name, default):
    """读取线程本地值，没有则回退到模块全局默认值。"""
    return getattr(_thread_ctx, name, default)

SES_ID = ""
LOGIN_NAME_PLAINTEXT = ""
USER_ID_PLAINTEXT = ""
EXCHANGE_ID_PLAINTEXT = "10"   #9是2块,10是4块,11是6块
RUN_TIME = datetime(2025, 9, 9, 17, 00, 0, 300000)  # 2025-08-16 06:59:59.900
RUN_COUNT = 10   # 运行次数
timeSleep = 0.2  # 请求间隔   0.2 = 0.2秒发送一次

# API 端点配置（从 constants.py 导入）
from constants import BASE_URL, ENDPOINTS

# 统计数据上报（在线人数 / 抢票数），未配置服务端地址时自动静默关闭
import stats_client
# ============================================================

# 【密钥1】用于 3DES 密钥传输加密的 RSA 公钥
ENCRYPTION_PUBLIC_KEY_PEM = """-----BEGIN PUBLIC KEY-----
MIGfMA0GCSqGSIb3DQEBAQUAA4GNADCBiQKBgQC7yWoQaojBBqKI2H0j4e8ZeX/n1yip6hxrxSVth5F5n1JJ/B3liPMdz6K1chNLFTAcbI7hTL9KkphP9yQ+bPYD68Ajrt/DFrW679Zi1CoeetHVrM4sF68lYarGXwnSlKloaPWnI4Ch9cSqIvIOInlpeJqYPlJ8ZJvGCmbQoM6bewIDAQAB
-----END PUBLIC KEY-----"""

# 【密钥2】用于请求数据 RSA 签名的私钥（从 JS 源码提取）
SIGNING_PRIVATE_KEY_PEM = """-----BEGIN PRIVATE KEY-----
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
-----END PRIVATE KEY-----"""

# 【密钥3】签名密钥，拼接在待签名内容末尾参与签名计算
SIGN_KEY_NEW = "zSw3MLRV7VuwT!*G"

# 在 JS 代码中定义的字段配置：需要 3DES 加密的字段和不参与签名的字段
ENCRYPT_KEYS = ["login_name", "user_id"]
NO_SIGN_KEYS = [
    "answerContent", "surveyId", "content", "preContent", "img", "img1",
    "img2", "package", "codeUrl", "belong", "verCode"
]

# 兑换接口完整 URL
URL = BASE_URL + ENDPOINTS['exchange']

# ============================================================

def rand_str(n):
    """生成长度为 n 的随机字母数字字符串，用作临时 3DES 密钥"""
    return ''.join(random.choice(string.ascii_letters + string.digits) for _ in range(n))

def rsa_encrypt(pub_pem, s):
    """使用 RSA 公钥加密字符串，返回 Base64 编码的密文"""
    rsakey = RSA.importKey(pub_pem)
    cipher = PKCS1_v1_5.new(rsakey)
    return base64.b64encode(cipher.encrypt(s.encode('utf-8'))).decode('utf-8')

def des3_ecb_pkcs7_encrypt(key24, plaintext):
    """使用 24 字节密钥进行 3DES ECB 模式加密，PKCS7 填充，返回 Base64 结果"""
    key_bytes = key24.encode('utf-8')
    cipher = DES3.new(key_bytes, DES3.MODE_ECB)
    padded_data = pad(plaintext.encode('utf-8'), DES3.block_size, style='pkcs7')
    encrypted = cipher.encrypt(padded_data)
    return base64.b64encode(encrypted).decode('utf-8')

def rsa_sha256_sign(private_key_pem, data_string):
    """使用 RSA 私钥对数据进行 SHA256withRSA 签名，返回 Base64 编码的签名结果"""
    key = RSA.import_key(private_key_pem)
    h = SHA256.new(data_string.encode('utf-8'))
    signature = pkcs1_15.new(key).sign(h)
    return base64.b64encode(signature).decode('utf-8')

def build_payload():
    """
    构造兑换请求的加密载荷，完全模拟 JS 端的加签流程。

    流程:
        准备通用参数 → 过滤空值 → RSA 加密 3DES 密钥 → 3DES 加密敏感字段
        → 移除不参与签名的字段 → 拼接签名 → RSA 签名

    返回:
        dict: 包含 key、sign 等字段的完整请求体
    """
    # 1. 准备所有参数（优先取线程本地上下文，支持多账号并发）
    _login_name = _ctx('login_name', LOGIN_NAME_PLAINTEXT)
    _user_id = _ctx('user_id', USER_ID_PLAINTEXT)
    _ses_id = _ctx('ses_id', SES_ID)
    _exchange_id = _ctx('exchange_id', EXCHANGE_ID_PLAINTEXT)

    payload = {
        "channel": CHANNEL,
        "app_ver_no": APP_VER_NO,
        "timestamp": int(time.time() * 1000)
    }
    if _login_name: payload["login_name"] = _login_name
    if _user_id: payload["user_id"] = _user_id
    if _ses_id: payload["ses_id"] = _ses_id
    payload["exchange_id"] = _exchange_id

    # 2. 过滤空值 (模拟JS的M()函数)
    filtered_payload = {}
    for key, value in payload.items():
        if value is not None and value != "":
            filtered_payload[key] = value
        elif isinstance(value, (int, float)) and value == 0:
            filtered_payload[key] = value
    payload = filtered_payload

    # 3. 生成并加密3DES密钥
    m = rand_str(24).upper()
    dec_key = rsa_encrypt(ENCRYPTION_PUBLIC_KEY_PEM, m)
    payload["dec_key"] = dec_key

    # 4. 加密指定字段
    for key in ENCRYPT_KEYS:
        if key in payload:
            payload[key] = des3_ecb_pkcs7_encrypt(m, str(payload[key]))

    # 5. 准备签名字段 (移除不参与签名的key)
    payload_for_signing = payload.copy()
    for key in NO_SIGN_KEYS:
        if key in payload_for_signing:
            del payload_for_signing[key]

    # Python 3.7+ 字典保持插入顺序，这与JS的Object.keys()行为一致
    keys_for_sign = list(payload_for_signing.keys())
    values_for_sign = [str(v) for v in payload_for_signing.values()]

    # 6. 【核心】计算正确的RSA签名
    values_concat = "".join(values_for_sign)
    string_to_sign = values_concat + SIGN_KEY_NEW
    sign = rsa_sha256_sign(SIGNING_PRIVATE_KEY_PEM, string_to_sign)

    # 7. 组装最终请求体
    payload["key"] = ",".join(keys_for_sign)
    payload["sign"] = sign

    return payload

# ================== 解密过程 ==================
PRIVATE_KEY_PEM = """-----BEGIN RSA PRIVATE KEY-----
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
-----END RSA PRIVATE KEY-----"""

from Crypto.Cipher import DES3 as _DES3   # 避免名称冲突
DES3 = _DES3
DES_IV = b"12345678"

def pkcs7_unpad(data):
    """去除 PKCS7 填充字节"""
    pad_len = data[-1]
    return data[:-pad_len]

def decrypt_data2(data2):
    """
    解密服务端返回的 data2 字段。

    流程：RSA 私钥解密前 172 字符得到 3DES 密钥 → 3DES CBC 解密剩余数据 → 去填充 → 返回 JSON 字符串。
    """
    # 拆分 RSA 密文部分和 3DES 密文部分
    rsa_enc = data2[:172]
    des_enc = data2[172:]

    rsa_enc_bytes = base64.b64decode(rsa_enc)
    des_enc_bytes = base64.b64decode(des_enc)

    # RSA 私钥解密，得到临时密钥 a
    rsakey = RSA.importKey(PRIVATE_KEY_PEM)
    cipher_rsa = PKCS1_v1_5.new(rsakey)
    a_bytes = cipher_rsa.decrypt(rsa_enc_bytes, None)
    a = a_bytes.decode()

    # 按约定构造 3DES 密钥和 IV
    key = ("HTt0Hzsu" + a).encode()
    iv = a[:8].encode()

    # 3DES CBC 解密并去除 PKCS7 填充
    cipher_des3 = DES3.new(key, DES3.MODE_CBC, iv)
    decrypted = cipher_des3.decrypt(des_enc_bytes)
    decrypted = pkcs7_unpad(decrypted)
    return decrypted.decode()

# 请求头模板
_DEFAULT_HEADERS = {
        "Host": "app.hzgh.org.cn",
        "Connection": "keep-alive",
        "Accept": "application/json, text/plain, */*",
        "User-Agent": "Mozilla/5.0 (Linux; Android 9; SKW-A0 Build/PQ3A.190705.08061357; wv) AppleWebKit/537.36 (KHTML, like Gecko) Version/4.0 Chrome/91.0.4472.114 Mobile Safari/537.36;unionApp;HZGH",
        "Content-Type": "application/json;charset=UTF-8",
        "Origin": "https://app.hzgh.org.cn:8123",
        "X-Requested-With": "com.zjte.hanggongefamily",
        "Referer": "https://app.hzgh.org.cn:8123/",
        "Accept-Encoding": "gzip, deflate",
        "Accept-Language": "zh-CN,zh;q=0.9,en-US;q=0.8,en;q=0.7"
    }

# Session 按线程隔离（requests.Session 非线程安全），每个线程首次使用时创建
_session_local = _threading.local()

def _get_session():
    """获取当前线程的 requests.Session，没有则创建。"""
    s = getattr(_session_local, 'session', None)
    if s is None:
        s = requests.Session()
        s.headers.update(_DEFAULT_HEADERS)
        _session_local.session = s
    return s

# 兼容旧代码里的全局 session 引用（主线程使用）
session = _get_session()

# ================== 日志系统 ==================
# 支持通过回调将日志输出到 GUI 界面
import sys
import io
from contextlib import redirect_stdout

# 全局日志回调函数，由 GUI 注册
log_callback = None

def set_log_callback(callback):
    """注册日志回调函数，将控制台重定向到 GUI 日志面板"""
    global log_callback
    log_callback = callback

def log_print(*args, **kwargs):
    """自定义日志输出函数：优先发送到当前线程注册的回调（多账号并发时各自归属），
    否则发送到全局回调，最后回退到控制台打印"""
    cb = _ctx('log_cb', None) or log_callback
    if cb:
        message = ' '.join(str(arg) for arg in args)
        cb(message)
    else:
        print(*args, **kwargs)

# 虽然 result 非 0，但业务上等同「已完成」的提示语。
# 典型场景：当天已签到过，或被其他设备/上次运行完成了签到，
# 接口返回「该积分规则当日已到积分上限次数」——这不是失败，是任务本来就已经做完了。
ALREADY_DONE_KEYWORDS = (
    "已到积分上限",
    "已达积分上限",
    "已签到",
    "重复签到",
    "已经签到",
    "今日已完成",
    "已经完成",
    "已评论",
)


def is_already_done_msg(msg):
    """判断一段提示语是否表示「本操作此前已完成」"""
    text = str(msg or "")
    if not text:
        return False
    return any(k in text for k in ALREADY_DONE_KEYWORDS)


def _parse_result_obj(decrypted_json_str):
    """把解密后的响应解析成 dict，失败返回 None"""
    try:
        data = json.loads(decrypted_json_str)
    except Exception:
        return None
    return data if isinstance(data, dict) else None


def is_step_ok(step):
    """判断单步结果是否等效成功：result == '0'，或提示语表示「此前已完成」"""
    if not isinstance(step, dict):
        return False
    if str(step.get("result", "")) == "0":
        return True
    return is_already_done_msg(step.get("msg"))


def format_result_text(decrypted_json_str, action="操作"):
    """
    将每日任务解密响应格式化为人类可读的结果文本（非 JSON）。

    提取 result / msg / remain_integral / total_integral 等关键字段，
    以「操作: 成功 (消息)  剩余积分: N  总积分: N」形式输出。
    """
    try:
        data = json.loads(decrypted_json_str)
    except Exception:
        return f"{action}: 响应解析失败"

    if not isinstance(data, dict):
        return f"{action}: 响应格式异常"

    result = str(data.get("result", ""))
    msg = str(data.get("msg", ""))

    if result == "0":
        parts = [f"{action}: 成功"]
        if msg:
            parts.append(f"({msg})")
        remain = data.get("remain_integral")
        if remain is not None:
            parts.append(f"剩余积分: {remain}")
            if data.get("total_integral") is not None:
                parts.append(f"总积分: {data['total_integral']}")
        return "  ".join(parts)
    # 当天已签到/已到上限这类，业务上等同于已完成，不显示"失败"以免误导
    if is_already_done_msg(msg):
        return f"{action}: 已完成（{msg}）"
    return f"{action}: 失败" + (f" - {msg}" if msg else "")

# ================== 兑换任务 ==================

def extract_response_msg(decrypted_json):
    """
    从解密后的响应中提取 msg 字段。

    服务端返回结构存在嵌套：msg 可能在外层，也可能在内层 data2 字符串里，
    两种结构都做兼容。解析失败返回空字符串。
    """
    try:
        data = json.loads(decrypted_json)
    except Exception:
        return ""

    if not isinstance(data, dict):
        return ""
    if data.get("msg"):
        return str(data["msg"])

    inner = data.get("data2")
    if isinstance(inner, str):
        try:
            inner_data = json.loads(inner)
            if isinstance(inner_data, dict) and inner_data.get("msg"):
                return str(inner_data["msg"])
        except Exception:
            return ""
    return ""


def is_exchange_success(decrypted_json):
    """判断本次兑换是否成功（与 JS 版一致：响应 msg 为"兑换成功"）"""
    return extract_response_msg(decrypted_json) == "兑换成功"


def run_exchange():
    """执行一次兑换操作：构造加密请求 → 发起 POST → 解密 → 判断是否抢到并上报统计"""
    payload = build_payload()
    resp = _get_session().post(URL, json=payload, verify=False)

    try:
        resp_json = resp.json()
        if "data2" in resp_json:
            decrypted_json = decrypt_data2(resp_json["data2"])
            log_print(decrypted_json)  # 替换原来的print

            # 抢到票就上报，每张票都算。
            # 一轮任务开 12 个并发线程、间隔 0.15 秒，2 秒内抢到 2 张同面额的券
            # 是完全可能的，因此这里不做"一轮只报一次"的合并，否则会少算。
            # 重试导致重复计数的问题由 request_id 幂等键在服务端解决。
            if is_exchange_success(decrypted_json):
                log_print("🎉 抢到票了！正在上报统计...")
                # 带上账号标识，与在线统计的 client_id 计算方式保持一致
                _account_key = (_ctx('user_id', '') or _ctx('login_name', LOGIN_NAME_PLAINTEXT) or '')
                stats_client.report_grab(_ctx('exchange_id', EXCHANGE_ID_PLAINTEXT), _account_key)
        else:
            log_print("返回中没有 data2 字段")  # 替换原来的print
    except Exception as e:
        log_print("解密失败:", e)  # 替换原来的print

# 修改job函数中的print语句
def job(run_count=None, time_sleep=None):
    """使用线程池并发执行多次兑换任务，每次请求之间间隔 time_sleep 秒

    run_count / time_sleep 为 None 时回退到模块全局值（兼容 CLI 入口）。
    多账号并发时必须显式传入，避免全局变量被其他线程覆盖。
    """
    _run_count = run_count if run_count is not None else RUN_COUNT
    _time_sleep = time_sleep if time_sleep is not None else timeSleep

    # 捕获当前线程的账号上下文，传播给线程池中的工作线程
    _snapshot = {
        'login_name': _ctx('login_name', LOGIN_NAME_PLAINTEXT),
        'user_id': _ctx('user_id', USER_ID_PLAINTEXT),
        'ses_id': _ctx('ses_id', SES_ID),
        'exchange_id': _ctx('exchange_id', EXCHANGE_ID_PLAINTEXT),
        'log_cb': _ctx('log_cb', None),
    }

    def _run_exchange_with_ctx():
        """在线程池线程内恢复账号上下文后执行兑换"""
        set_thread_context(**_snapshot)
        try:
            run_exchange()
        finally:
            clear_thread_context()

    with concurrent.futures.ThreadPoolExecutor(max_workers=12) as executor:
        log_print(_snapshot['user_id'])
        log_print(_snapshot['login_name'])
        log_print(_snapshot['ses_id'])
        for i in range(_run_count):
            log_print(f"准备启动第{i+1}个线程，时间：{datetime.now()}")  # 替换原来的print
            executor.submit(_run_exchange_with_ctx)
            time.sleep(_time_sleep)

# 模拟JavaScript版本的每日任务功能
def daily_task_login():
    """每日任务之登录：构造登录请求并发送到 U042 端点"""
    payload = {
        "channel": CHANNEL,
        "app_ver_no": "3.1.4",  # 使用与JavaScript版本相同的版本号
        "timestamp": int(time.time() * 1000),
        "login_name": _ctx('login_name', LOGIN_NAME_PLAINTEXT),
        "ses_id": _ctx('ses_id', SES_ID)
    }
    # 添加登录特定参数（参考JavaScript版本的functions.login）
    payload.update({
        "type": "1"  # 登录类型
    })
    
    # 过滤空值
    filtered_payload = {}
    for key, value in payload.items():
        if value is not None and value != "":
            filtered_payload[key] = value
        elif isinstance(value, (int, float)) and value == 0:
            filtered_payload[key] = value
    payload = filtered_payload

    # 生成并加密3DES密钥
    m = rand_str(24).upper()
    dec_key = rsa_encrypt(ENCRYPTION_PUBLIC_KEY_PEM, m)
    payload["dec_key"] = dec_key

    # 加密指定字段
    for key in ENCRYPT_KEYS:
        if key in payload:
            payload[key] = des3_ecb_pkcs7_encrypt(m, str(payload[key]))

    # 准备签名字段
    payload_for_signing = payload.copy()
    for key in NO_SIGN_KEYS:
        if key in payload_for_signing:
            del payload_for_signing[key]

    keys_for_sign = list(payload_for_signing.keys())
    values_for_sign = [str(v) for v in payload_for_signing.values()]

    # 计算RSA签名
    values_concat = "".join(values_for_sign)
    string_to_sign = values_concat + SIGN_KEY_NEW
    sign = rsa_sha256_sign(SIGNING_PRIVATE_KEY_PEM, string_to_sign)

    # 组装最终请求体
    payload["key"] = ",".join(keys_for_sign)
    payload["sign"] = sign

    # 使用登录端点URL
    login_url = BASE_URL + ENDPOINTS['dailyLogin']
    resp = _get_session().post(login_url, json=payload, verify=False)
    try:
        resp_json = resp.json()
        if "data2" in resp_json:
            decrypted_json = decrypt_data2(resp_json["data2"])
            log_print(format_result_text(decrypted_json, "登录"))
            return _parse_result_obj(decrypted_json)
        log_print("登录响应中没有 data2 字段")
    except Exception as e:
        log_print(f"登录请求失败: {e}")
    return None

def daily_task_signin(signin_number=1):
    """每日任务之签到：发送签到请求到 U042 端点（与登录同端点，type 不同）"""
    payload = {
        "channel": CHANNEL,
        "app_ver_no": "3.1.4",  # 使用与JavaScript版本相同的版本号
        "timestamp": int(time.time() * 1000),
        "login_name": _ctx('login_name', LOGIN_NAME_PLAINTEXT),
        "ses_id": _ctx('ses_id', SES_ID)
    }
    # 添加签到特定参数（参考JavaScript版本的functions.signin）
    payload.update({
        "type": "5"  # 签到类型
    })
    
    # 过滤空值
    filtered_payload = {}
    for key, value in payload.items():
        if value is not None and value != "":
            filtered_payload[key] = value
        elif isinstance(value, (int, float)) and value == 0:
            filtered_payload[key] = value
    payload = filtered_payload

    # 生成并加密3DES密钥
    m = rand_str(24).upper()
    dec_key = rsa_encrypt(ENCRYPTION_PUBLIC_KEY_PEM, m)
    payload["dec_key"] = dec_key

    # 加密指定字段
    for key in ENCRYPT_KEYS:
        if key in payload:
            payload[key] = des3_ecb_pkcs7_encrypt(m, str(payload[key]))

    # 准备签名字段
    payload_for_signing = payload.copy()
    for key in NO_SIGN_KEYS:
        if key in payload_for_signing:
            del payload_for_signing[key]

    keys_for_sign = list(payload_for_signing.keys())
    values_for_sign = [str(v) for v in payload_for_signing.values()]

    # 计算RSA签名
    values_concat = "".join(values_for_sign)
    string_to_sign = values_concat + SIGN_KEY_NEW
    sign = rsa_sha256_sign(SIGNING_PRIVATE_KEY_PEM, string_to_sign)

    # 组装最终请求体
    payload["key"] = ",".join(keys_for_sign)
    payload["sign"] = sign

    # 使用签到端点URL
    signin_url = BASE_URL + ENDPOINTS['signin']
    resp = _get_session().post(signin_url, json=payload, verify=False)
    try:
        resp_json = resp.json()
        if "data2" in resp_json:
            decrypted_json = decrypt_data2(resp_json["data2"])
            log_print(format_result_text(decrypted_json, f"第{signin_number}次签到"))
            return _parse_result_obj(decrypted_json)
        log_print("签到响应中没有 data2 字段")
    except Exception as e:
        log_print(f"签到请求失败: {e}")
    return None

def daily_task_comment():
    """每日任务之评论：发送评论请求到 AC08 端点"""
    payload = {
        "channel": CHANNEL,
        "app_ver_no": "3.1.4",  # 使用与JavaScript版本相同的版本号
        "timestamp": int(time.time() * 1000),
        "login_name": _ctx('login_name', LOGIN_NAME_PLAINTEXT),
        "ses_id": _ctx('ses_id', SES_ID)
    }
    # 添加评论特定参数（参考JavaScript版本的functions.comment）
    payload.update({
        "related_id": "1232",
        "content_type": "1",
        "oper_type": "0",
        "suffix": "png",
        "content": "好"  # 默认评论内容
    })
    
    # 过滤空值
    filtered_payload = {}
    for key, value in payload.items():
        if value is not None and value != "":
            filtered_payload[key] = value
        elif isinstance(value, (int, float)) and value == 0:
            filtered_payload[key] = value
    payload = filtered_payload

    # 生成并加密3DES密钥
    m = rand_str(24).upper()
    dec_key = rsa_encrypt(ENCRYPTION_PUBLIC_KEY_PEM, m)
    payload["dec_key"] = dec_key

    # 加密指定字段
    for key in ENCRYPT_KEYS:
        if key in payload:
            payload[key] = des3_ecb_pkcs7_encrypt(m, str(payload[key]))

    # 准备签名字段
    payload_for_signing = payload.copy()
    for key in NO_SIGN_KEYS:
        if key in payload_for_signing:
            del payload_for_signing[key]

    keys_for_sign = list(payload_for_signing.keys())
    values_for_sign = [str(v) for v in payload_for_signing.values()]

    # 计算RSA签名
    values_concat = "".join(values_for_sign)
    string_to_sign = values_concat + SIGN_KEY_NEW
    sign = rsa_sha256_sign(SIGNING_PRIVATE_KEY_PEM, string_to_sign)

    # 组装最终请求体
    payload["key"] = ",".join(keys_for_sign)
    payload["sign"] = sign

    # 使用评论端点URL
    comment_url = BASE_URL + ENDPOINTS['comment']
    resp = _get_session().post(comment_url, json=payload, verify=False)
    try:
        resp_json = resp.json()
        if "data2" in resp_json:
            decrypted_json = decrypt_data2(resp_json["data2"])
            log_print(format_result_text(decrypted_json, "评论"))
            return _parse_result_obj(decrypted_json)
        log_print("评论响应中没有 data2 字段")
    except Exception as e:
        log_print(f"评论请求失败: {e}")
    return None

def daily_task_query():
    """每日任务之查询积分：发送查询请求到 U005 端点"""
    payload = {
        "channel": CHANNEL,
        "app_ver_no": "3.1.4",  # 使用与JavaScript版本相同的版本号
        "timestamp": int(time.time() * 1000),
        "login_name": _ctx('login_name', LOGIN_NAME_PLAINTEXT),
        "ses_id": _ctx('ses_id', SES_ID)
    }
    # 添加查询特定参数（参考JavaScript版本的functions.query）
    # 查询功能不需要额外参数
    
    # 过滤空值
    filtered_payload = {}
    for key, value in payload.items():
        if value is not None and value != "":
            filtered_payload[key] = value
        elif isinstance(value, (int, float)) and value == 0:
            filtered_payload[key] = value
    payload = filtered_payload

    # 生成并加密3DES密钥
    m = rand_str(24).upper()
    dec_key = rsa_encrypt(ENCRYPTION_PUBLIC_KEY_PEM, m)
    payload["dec_key"] = dec_key

    # 加密指定字段
    for key in ENCRYPT_KEYS:
        if key in payload:
            payload[key] = des3_ecb_pkcs7_encrypt(m, str(payload[key]))

    # 准备签名字段
    payload_for_signing = payload.copy()
    for key in NO_SIGN_KEYS:
        if key in payload_for_signing:
            del payload_for_signing[key]

    keys_for_sign = list(payload_for_signing.keys())
    values_for_sign = [str(v) for v in payload_for_signing.values()]

    # 计算RSA签名
    values_concat = "".join(values_for_sign)
    string_to_sign = values_concat + SIGN_KEY_NEW
    sign = rsa_sha256_sign(SIGNING_PRIVATE_KEY_PEM, string_to_sign)

    # 组装最终请求体
    payload["key"] = ",".join(keys_for_sign)
    payload["sign"] = sign

    # 使用查询端点URL
    query_url = BASE_URL + ENDPOINTS['query']
    resp = _get_session().post(query_url, json=payload, verify=False)
    try:
        resp_json = resp.json()
        if "data2" in resp_json:
            decrypted_json = decrypt_data2(resp_json["data2"])
            log_print(format_result_text(decrypted_json, "查询积分"))
            return _parse_result_obj(decrypted_json)
        log_print("查询积分响应中没有 data2 字段")
    except Exception as e:
        log_print(f"查询积分请求失败: {e}")
    return None

def daily_task_workflow():
    """
    执行完整的每日任务工作流。

    流程: 登录 → 3 次签到 → 评论 → 查询积分
    每个步骤之间间隔 1 秒，避免请求过快被限流。

    返回:
        bool: 所有步骤是否都等效成功。当天已签到（返回"已到积分上限"）
              也算成功，避免重复执行时被误判为失败。
    """
    log_print("🎯 开始执行每日任务工作流")
    log_print("=" * 40)
    log_print("工作流: 登录 → 3次签到 → 评论 → 查询积分")
    log_print("=" * 40)

    steps = []

    try:
        # 执行登录
        log_print("\n🔄 开始执行登录...")
        steps.append(daily_task_login())
        time.sleep(1)  # 等待1秒

        # 执行3次签到
        log_print("\n🔄 开始执行3次签到...")
        for i in range(1, 4):
            log_print(f"\n第 {i} 次签到:")
            steps.append(daily_task_signin(i))
            time.sleep(1)  # 等待1秒

        # 执行评论
        log_print("\n🔄 开始执行评论...")
        steps.append(daily_task_comment())
        time.sleep(1)  # 等待1秒

        # 执行查询积分
        log_print("\n🔄 开始查询积分...")
        steps.append(daily_task_query())

        all_ok = bool(steps) and all(is_step_ok(s) for s in steps)
        if all_ok:
            log_print("\n🎉 每日任务工作流执行完成!")
        else:
            log_print("\n⚠️ 每日任务有步骤未成功，请查看上方日志")
        log_print("=" * 40)
        return all_ok

    except Exception as e:
        log_print(f"❌ 每日任务执行失败: {e}")
        return False
        log_print("=" * 40)
        return all_ok

    except Exception as e:
        log_print(f"❌ 每日任务执行失败: {e}")
        return False

# ================== 服务器时间同步 ==================
# 与小程序版一致：通过查询接口响应头 Date 字段获取服务器时间，
# 用请求往返时间的一半补偿网络延迟，避免本地时钟偏差导致错过抢票时机
def sync_server_time():
    """
    同步服务器时间：向查询接口发送请求，从响应头 Date 字段获取服务器时间。

    返回:
        float: 服务器时间戳（毫秒，已补偿网络延迟）
    """
    payload = {
        "channel": CHANNEL,
        "app_ver_no": "3.1.4",  # 使用与JavaScript版本相同的版本号
        "timestamp": int(time.time() * 1000),
        "login_name": _ctx('login_name', LOGIN_NAME_PLAINTEXT),
        "ses_id": _ctx('ses_id', SES_ID)
    }

    # 过滤空值
    filtered_payload = {}
    for key, value in payload.items():
        if value is not None and value != "":
            filtered_payload[key] = value
        elif isinstance(value, (int, float)) and value == 0:
            filtered_payload[key] = value
    payload = filtered_payload

    # 生成并加密3DES密钥
    m = rand_str(24).upper()
    dec_key = rsa_encrypt(ENCRYPTION_PUBLIC_KEY_PEM, m)
    payload["dec_key"] = dec_key

    # 加密指定字段
    for key in ENCRYPT_KEYS:
        if key in payload:
            payload[key] = des3_ecb_pkcs7_encrypt(m, str(payload[key]))

    # 准备签名字段
    payload_for_signing = payload.copy()
    for key in NO_SIGN_KEYS:
        if key in payload_for_signing:
            del payload_for_signing[key]

    keys_for_sign = list(payload_for_signing.keys())
    values_for_sign = [str(v) for v in payload_for_signing.values()]

    # 计算RSA签名
    values_concat = "".join(values_for_sign)
    string_to_sign = values_concat + SIGN_KEY_NEW
    sign = rsa_sha256_sign(SIGNING_PRIVATE_KEY_PEM, string_to_sign)

    payload["key"] = ",".join(keys_for_sign)
    payload["sign"] = sign

    # 发送查询请求并读取响应头 Date 字段
    query_url = BASE_URL + ENDPOINTS['query']
    local_start = int(time.time() * 1000)
    resp = _get_session().post(query_url, json=payload, verify=False)
    local_end = int(time.time() * 1000)

    date_header = resp.headers.get("Date")
    if not date_header:
        raise ValueError("响应头缺少 Date 字段")
    # parsedate_to_datetime 解析 HTTP 日期，不受本地语言环境影响
    server_time = parsedate_to_datetime(date_header).timestamp() * 1000
    # 用请求往返时间的一半作为网络延迟补偿
    latency = (local_end - local_start) // 2
    return server_time + latency

def sync_time_offset():
    """
    同步服务器时间并计算本地时钟偏移（秒）。

    失败时回退到本地时间（偏移为 0），与小程序版行为一致。
    """
    try:
        server_ms = sync_server_time()
        offset = (server_ms - int(time.time() * 1000)) / 1000.0
        log_print(f"服务器时间同步完成，本地偏移: {offset * 1000:+.0f}ms")
        return offset
    except Exception as e:
        log_print(f"服务器时间同步失败，使用本地时间: {e}")
        return 0.0

# 修改main函数中的print语句
def main():
    """主入口：同步服务器时间，等待目标执行时间，然后启动多线程兑换任务"""
    log_print(f"程序已启动，将在每天{RUN_TIME}执行兑换任务，共执行{RUN_COUNT}次。")
    log_print("正在同步服务器时间...")
    offset = sync_time_offset()
    wait_until_target(offset)
    job()

def wait_until_target(offset=0.0):
    """阻塞等待直到 RUN_TIME（按服务器时间偏移校正），按剩余时间动态调整检查频率（5 分钟 → 1 分钟 → 30 秒 → 0.5 秒 → 50 毫秒）"""
    while True:
        now = datetime.now() + timedelta(seconds=offset)
        if now >= RUN_TIME:
            break
        # 控制检查频率到毫秒
        diff = (RUN_TIME - now).total_seconds()

        # 距离超过 1 小时
        if diff > 3600:
            time.sleep(300)    # 5分钟
        # 距离超过 10 分钟
        elif diff > 600:
            time.sleep(60)     # 1分钟
        # 距离超过 1 分钟
        if diff > 60:
            time.sleep(30)
            
        # 情况 B: 距离较远 (> 1秒)
        elif diff > 1:
            time.sleep(0.5)
            
        # 情况 C: 临近了 (0.1秒 ~ 1秒)
        else:
            time.sleep(0.05)  # 50ms, 留出足够余量给系统调度


if __name__ == "__main__":
    main()
