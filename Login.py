"""
Login.py - 杭州工会 App 登录与绿色出行码模块
提供图形验证码获取、短信验证码发送、密码/短信登录、绿色出行码获取等功能的接口封装。
"""

import requests
import time
import random
import string
import base64
import json
import urllib3
from Crypto.PublicKey import RSA
from Crypto.Signature import pkcs1_15
from Cryptodome.Hash import SHA256
from Crypto.Cipher import DES3, PKCS1_v1_5
from Crypto.Util.Padding import pad
import hashlib

# 清除 HTTPS 警告，避免自签名证书报错
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# ================= 1. 密钥配置区域 =================
# 以下为与 App 服务端通信所需的加密密钥、签名密钥及应用配置参数
CHANNEL = "02"
APP_VER_NO = "3.1.7"
BASE_URL = 'https://app.hzgh.org.cn'

ENCRYPTION_PUBLIC_KEY_PEM = """-----BEGIN PUBLIC KEY-----
MIGfMA0GCSqGSIb3DQEBAQUAA4GNADCBiQKBgQC7yWoQaojBBqKI2H0j4e8ZeX/n1yip6hxrxSVth5F5n1JJ/B3liPMdz6K1chNLFTAcbI7hTL9KkphP9yQ+bPYD68Ajrt/DFrW679Zi1CoeetHVrM4sF68lYarGXwnSlKloaPWnI4Ch9cSqIvIOInlpeJqYPlJ8ZJvGCmbQoM6bewIDAQAB
-----END PUBLIC KEY-----"""

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

SIGN_KEY_NEW = "zSw3MLRV7VuwT!*G"

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

# ================= 2. 核心加解密工具 =================
def rand_str(n):
    """生成长度为 n 的随机字母数字字符串，用于作为临时 3DES 密钥"""
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
    """使用 RSA 私钥对数据进行 SHA256withRSA 签名，返回 Base64 签名结果"""
    key = RSA.import_key(private_key_pem)
    h = SHA256.new(data_string.encode('utf-8'))
    signature = pkcs1_15.new(key).sign(h)
    return base64.b64encode(signature).decode('utf-8')

def pkcs7_unpad(data):
    """去除 PKCS7 填充字节（末字节即为填充长度）"""
    pad_len = data[-1]
    return data[:-pad_len]

def decrypt_data2(data2):
    """
    解密服务端返回的 data2 字段。
    流程：RSA 解密前 172 字节得到 3DES 密钥和 IV → 用该密钥 3DES CBC 解密剩余数据 → 去填充 → 返回 JSON 字符串。
    """
    # 拆分 RSA 密文部分和 3DES 密文部分
    rsa_enc = data2[:172]
    des_enc = data2[172:]
    rsa_enc_bytes = base64.b64decode(rsa_enc)
    des_enc_bytes = base64.b64decode(des_enc)

    # RSA 私钥解密，得到明文字符串 a
    rsakey = RSA.importKey(PRIVATE_KEY_PEM)
    cipher_rsa = PKCS1_v1_5.new(rsakey)
    a_bytes = cipher_rsa.decrypt(rsa_enc_bytes, None)
    a = a_bytes.decode()

    # 按约定构造 3DES 密钥和 IV，进行 CBC 解密
    key = ("HTt0Hzsu" + a).encode()
    iv = a[:8].encode()
    cipher_des3 = DES3.new(key, DES3.MODE_CBC, iv)
    decrypted = cipher_des3.decrypt(des_enc_bytes)
    return pkcs7_unpad(decrypted).decode()

# ================= 3. 网络请求 Session 初始化 =================
# 复用 Session 连接，减少 TCP 握手开销
session = requests.Session()
headers = {
    "Host": "app.hzgh.org.cn",
    "Connection": "keep-alive",
    "Accept": "application/json, text/plain, */*",
    "User-Agent": "okhttp/3.4.2",
    "Content-Type": "application/json;charset=UTF-8",
    "Accept-Encoding": "gzip, deflate"
}
session.headers.update(headers)

# ================= 4. 业务逻辑：获取验证码 (U067) =================
def get_captcha_u067():
    """
    请求 U067 接口，获取图形验证码及唯一标识 (imgUniCode)。

    返回:
        dict: 包含 img（Base64 图片）、imgUniCode（验证码标识）等字段的字典，
              失败返回 None。
    """
    # 构造请求参数，包含设备信息、时间戳等
    payload = {
        "channel": CHANNEL,
        "app_ver_no": APP_VER_NO,
        "timestamp": str(int(time.time() * 1000)),
        "term_sys_ver": "12",
        "root": "0",
        "term_sys": "2",
        "model": "24031PN0DC",
        "term_id": "42e85afdd7e346e5",
        "trcode": "U/U067"
    }

    # 生成随机 3DES 密钥并用 RSA 公钥加密后放入 payload
    m = rand_str(24).upper()
    payload["dec_key"] = rsa_encrypt(ENCRYPTION_PUBLIC_KEY_PEM, m)

    # 将所有字段按字典序组合，拼接签名密钥后进行 RSA 签名
    keys_for_sign = list(payload.keys())
    values_for_sign = [str(v) for v in payload.values()]
    values_concat = "".join(values_for_sign)
    string_to_sign = values_concat + SIGN_KEY_NEW
    payload["key"] = ",".join(keys_for_sign)
    payload["sign"] = rsa_sha256_sign(SIGNING_PRIVATE_KEY_PEM, string_to_sign)

    url = BASE_URL + "/unionApp/interf/front/U/U067"
    print(f"[*] 正在请求 U067 获取验证码...")
    resp = session.post(url, json=payload, verify=False)

    try:
        resp_json = resp.json()
        if "data2" in resp_json:
            decrypted_json_str = decrypt_data2(resp_json["data2"])
            data_dict = json.loads(decrypted_json_str)
            print("[+] U067 解密成功，获取到以下数据：")

            # 截断 Base64 图片字段显示，避免控制台刷屏
            display_dict = data_dict.copy()
            if 'img' in display_dict:
                display_dict['img'] = display_dict['img'][:30] + "...(已省略长字符串)"
            print(json.dumps(display_dict, indent=2, ensure_ascii=False))

            return data_dict
        else:
            print("[-] U067 响应中没有 data2 字段:", resp.text)
            return None
    except Exception as e:
        print(f"[-] U067 请求解密失败: {e}")
        return None



# ================= 5. 业务逻辑：发送短信验证码 (SMS/SMS1) =================
def send_sms(captcha_data, phone, img_auth_code, sms_type="10"):
    """
    请求 SMS/SMS1 接口，发送短信验证码到指定手机号。

    参数:
        captcha_data (dict): 包含 imgUniCode 的验证码数据字典
        phone (str): 目标手机号
        img_auth_code (str): 图形验证码字符
        sms_type (str): 短信类型，"10" 为登录验证码

    返回:
        dict: 响应数据字典，失败返回 None

    异常:
        ValueError: 参数校验失败时抛出
    """
    if not captcha_data or not captcha_data.get("imgUniCode"):
        raise ValueError("验证码数据异常，缺少 imgUniCode。")
    if not phone or not img_auth_code:
        raise ValueError("手机号和图形验证码都必须填写。")

    payload = {
        "channel": CHANNEL,
        "app_ver_no": APP_VER_NO,
        "timestamp": str(int(time.time() * 1000)),
        "term_sys_ver": "12",
        "root": "0",
        "term_sys": "2",
        "model": "24031PN0DC",
        "login_name": phone,
        "mobile": phone,
        "imgUniCode": captcha_data["imgUniCode"],
        "imgAuthCode": img_auth_code.strip(),
        "sms_type": sms_type
    }

    m = rand_str(24).upper()
    payload["dec_key"] = rsa_encrypt(ENCRYPTION_PUBLIC_KEY_PEM, m)

    # 对敏感字段使用 3DES 加密
    encrypt_keys = ["login_name", "mobile", "imgUniCode", "imgAuthCode"]
    for k in encrypt_keys:
        if k in payload:
            payload[k] = des3_ecb_pkcs7_encrypt(m, payload[k])

    keys_for_sign = list(payload.keys())
    values_for_sign = [str(v) for v in payload.values()]

    values_concat = "".join(values_for_sign)
    string_to_sign = values_concat + SIGN_KEY_NEW
    payload["key"] = ",".join(keys_for_sign)
    payload["sign"] = rsa_sha256_sign(SIGNING_PRIVATE_KEY_PEM, string_to_sign)

    url = BASE_URL + "/unionApp/interf/front/SMS/SMS1"
    print(f"\n[*] 正在请求 SMS/SMS1 发送短信验证码...")
    resp = session.post(url, json=payload, verify=False)

    try:
        resp_json = resp.json()
        if "data2" in resp_json:
            decrypted_json_str = decrypt_data2(resp_json["data2"])
            data_dict = json.loads(decrypted_json_str)
            print("[+] SMS/SMS1 响应解密成功：")
            print(json.dumps(data_dict, indent=2, ensure_ascii=False))
            return data_dict
        print("[-] SMS/SMS1 响应中没有 data2 字段:", resp.text)
        return None
    except Exception as e:
        print(f"[-] SMS/SMS1 请求解密失败: {e}")
        return None


# ================= 6. 业务逻辑：短信验证码登录 (U065) =================
def login_u065(phone, auth_code):
    """
    提交 U065 接口，使用短信验证码登录。

    参数:
        phone (str): 手机号
        auth_code (str): 短信验证码

    返回:
        dict: 登录响应数据，包含 user_id、ses_id、login_name 等字段；
              失败返回 None。

    异常:
        ValueError: 参数校验失败时抛出
    """
    if not phone or not auth_code:
        raise ValueError("手机号和短信验证码都必须填写。")

    payload = {
        "channel": CHANNEL,
        "app_ver_no": APP_VER_NO,
        "timestamp": str(int(time.time() * 1000)),
        "term_sys_ver": "12",
        "root": "0",
        "term_sys": "2",
        "model": "24031PN0DC",
        "term_id": "42e85afdd7e346e5",
        "login_name": phone,
        "auth_code": auth_code.strip()
    }

    m = rand_str(24).upper()
    payload["dec_key"] = rsa_encrypt(ENCRYPTION_PUBLIC_KEY_PEM, m)

    # 对登录名和验证码进行 3DES 加密
    encrypt_keys = ["login_name", "auth_code"]
    for k in encrypt_keys:
        if k in payload:
            payload[k] = des3_ecb_pkcs7_encrypt(m, payload[k])

    keys_for_sign = list(payload.keys())
    values_for_sign = [str(v) for v in payload.values()]

    values_concat = "".join(values_for_sign)
    string_to_sign = values_concat + SIGN_KEY_NEW
    payload["key"] = ",".join(keys_for_sign)
    payload["sign"] = rsa_sha256_sign(SIGNING_PRIVATE_KEY_PEM, string_to_sign)

    url = BASE_URL + "/unionApp/interf/front/U/U065"
    print(f"\n[*] 正在提交 U065 短信验证码登录...")
    resp = session.post(url, json=payload, verify=False)

    try:
        resp_json = resp.json()
        if "data2" in resp_json:
            decrypted_json_str = decrypt_data2(resp_json["data2"])
            data_dict = json.loads(decrypted_json_str)
            print("[+] U065 登录响应解密成功：")
            print(json.dumps(data_dict, indent=2, ensure_ascii=False))
            return data_dict
        print("[-] U065 响应中没有 data2 字段:", resp.text)
        return None
    except Exception as e:
        print(f"[-] U065 请求解密失败: {e}")
        return None


# ================= 7. 业务逻辑：绿色出行码 (OL82 / OP80 / QR) =================
def get_qr_token(user_id_plain, ses_id):
    """
    请求 OL82 接口，获取市民卡交通码 token。

    参数:
        user_id_plain (str): 明文 user_id（登录响应中获取）
        ses_id (str): 明文 ses_id（登录响应中获取）

    返回:
        str: token 字符串（如 "HZCODEGONGHUI..."），失败返回 None

    异常:
        ValueError: 参数校验失败时抛出
    """
    if not user_id_plain or not ses_id:
        raise ValueError("user_id 和 ses_id 都必须填写。")

    payload = {
        "channel": CHANNEL,
        "app_ver_no": APP_VER_NO,
        "timestamp": str(int(time.time() * 1000)),
        "user_id": user_id_plain,
        "ses_id": ses_id
    }

    m = rand_str(24).upper()
    payload["dec_key"] = rsa_encrypt(ENCRYPTION_PUBLIC_KEY_PEM, m)

    # 对 user_id 进行 3DES 加密
    encrypt_keys = ["user_id"]
    for k in encrypt_keys:
        if k in payload:
            payload[k] = des3_ecb_pkcs7_encrypt(m, payload[k])

    keys_for_sign = list(payload.keys())
    values_for_sign = [str(v) for v in payload.values()]

    values_concat = "".join(values_for_sign)
    string_to_sign = values_concat + SIGN_KEY_NEW
    payload["key"] = ",".join(keys_for_sign)
    payload["sign"] = rsa_sha256_sign(SIGNING_PRIVATE_KEY_PEM, string_to_sign)

    url = BASE_URL + "/unionApp/interf/front/OL/OL82"
    print(f"\n[*] 正在请求 OL82 获取绿色出行码 token...")
    resp = session.post(url, json=payload, verify=False)

    try:
        resp_json = resp.json()
        if "data2" in resp_json:
            decrypted_json_str = decrypt_data2(resp_json["data2"])
            data_dict = json.loads(decrypted_json_str)
            print("[+] OL82 响应解密成功：")
            print(json.dumps(data_dict, indent=2, ensure_ascii=False))
            if data_dict.get("result") == "0" and "data" in data_dict:
                return data_dict["data"].get("token", "")
            return None
        print("[-] OL82 响应中没有 data2 字段:", resp.text)
        return None
    except Exception as e:
        print(f"[-] OL82 请求解密失败: {e}")
        return None


def record_qr_visit(user_id_plain):
    """
    请求 OP80 接口，记录用户点击量（绿色出行码入口点击统计）。

    参数:
        user_id_plain (str): 明文 user_id

    返回:
        bool: True 表示记录成功，False 表示失败
    """
    if not user_id_plain:
        raise ValueError("user_id 不能为空。")

    payload = {
        "channel": CHANNEL,
        "app_ver_no": APP_VER_NO,
        "timestamp": str(int(time.time() * 1000)),
        "user_id": user_id_plain,
        "icon_id": "92",
        "type": "2"
    }

    m = rand_str(24).upper()
    payload["dec_key"] = rsa_encrypt(ENCRYPTION_PUBLIC_KEY_PEM, m)

    encrypt_keys = ["user_id"]
    for k in encrypt_keys:
        if k in payload:
            payload[k] = des3_ecb_pkcs7_encrypt(m, payload[k])

    keys_for_sign = list(payload.keys())
    values_for_sign = [str(v) for v in payload.values()]

    values_concat = "".join(values_for_sign)
    string_to_sign = values_concat + SIGN_KEY_NEW
    payload["key"] = ",".join(keys_for_sign)
    payload["sign"] = rsa_sha256_sign(SIGNING_PRIVATE_KEY_PEM, string_to_sign)

    url = BASE_URL + "/unionApp/interf/front/OP/OP80"
    print(f"\n[*] 正在请求 OP80 记录访问...")
    resp = session.post(url, json=payload, verify=False)

    try:
        resp_json = resp.json()
        print(f"[+] OP80 响应: {resp_json}")
        return resp_json.get("result") == "0"
    except Exception as e:
        print(f"[-] OP80 请求失败: {e}")
        return False


def get_qr_code(token):
    """
    使用 OL82 获取的 token，调用第三方接口获取乘车码二维码数据。

    参数:
        token (str): OL82 接口获取的认证 token

    返回:
        dict: 包含 qrcode（二维码数据十六进制字符串）、deadTime（有效期）、
              money（余额）、trafficCardNo（交通卡号）等字段，失败返回 None
    """
    if not token:
        raise ValueError("token 不能为空。")

    ts = str(int(time.time() * 1000))
    global_seq = "2500" + ''.join(random.choices('0123456789abcdef', k=14))

    payload = {
        "latitude": None,
        "longitude": None,
        "version": "1.0.0",
        "isImage": "1",
        "timestamp": ts,
        "globalSeq": global_seq
    }

    # 调用第三方乘车码引擎接口，token 放在请求头中
    url = "https://hzcode.96225.com/hzcitizencodeengine/codeEngine/apply"
    headers = {
        "Host": "hzcode.96225.com",
        "Connection": "keep-alive",
        "Accept": "application/json, text/plain, */*",
        "User-Agent": "Mozilla/5.0 (Linux; Android 12; 23113RKC6C Build/V417IR; wv) AppleWebKit/537.36 (KHTML, like Gecko) Version/4.0 Chrome/110.0.5481.154 Mobile Safari/537.36;unionApp;HZGH",
        "Content-Type": "application/json;charset=UTF-8",
        "Origin": "https://hzcode.96225.com",
        "X-Requested-With": "com.zjte.hanggongefamily",
        "Referer": "https://hzcode.96225.com/hzcitizencodeh5/",
        "token": token
    }

    print(f"\n[*] 正在请求乘车码接口...")
    resp = requests.post(url, json=payload, headers=headers, verify=False)

    try:
        resp_json = resp.json()
        print("[+] 乘车码响应:")
        print(json.dumps(resp_json, indent=2, ensure_ascii=False))
        return resp_json
    except Exception as e:
        print(f"[-] 乘车码请求失败: {e}")
        return None


def qr_code_workflow(user_id_plain, ses_id):
    """
    完整绿色出行码流程：OL82 获取 token → OP80 记录访问 → 获取乘车码

    参数:
        user_id_plain (str): 明文 user_id
        ses_id (str): 明文 ses_id

    返回:
        dict: 乘车码响应数据，失败返回 None
    """
    print("\n" + "="*50)
    print("  绿色出行码流程")
    print("="*50)

    # 第一步：通过 OL82 获取认证 token
    print("\n--- 第一步：获取 token (OL82) ---")
    token = get_qr_token(user_id_plain, ses_id)
    if not token:
        print("[-] 获取 token 失败")
        return None
    print(f"[+] token: {token}")

    # 第二步：通过 OP80 记录入口点击统计
    print("\n--- 第二步：记录访问 (OP80) ---")
    record_qr_visit(user_id_plain)

    # 第三步：使用 token 向第三方引擎请求乘车码二维码数据
    print("\n--- 第三步：获取乘车码 ---")
    result = get_qr_code(token)
    return result


# ================= 8. 业务逻辑：执行登录 (U004) =================
def decode_captcha_image(captcha_data):
    """
    将图形验证码的 Base64 字符串解码为图片二进制数据。

    参数:
        captcha_data (dict): 包含 img 字段的验证码数据字典

    返回:
        bytes: 图片的原始二进制数据
    """
    img_base64 = captcha_data.get("img", "")
    if not img_base64:
        raise ValueError("验证码数据异常，没有找到图片数据。")

    # 移除可能的 data:image/...;base64, 前缀
    if "," in img_base64:
        img_base64 = img_base64.split(",", 1)[1]

    return base64.b64decode(img_base64)


def login_u004_with_code(captcha_data, phone, password, img_auth_code):
    """
    提交 U004 登录接口（密码登录），验证码由调用方传入而非从图片文件读取。

    参数:
        captcha_data (dict): 包含 imgUniCode 的验证码数据字典
        phone (str): 手机号
        password (str): 明文密码
        img_auth_code (str): 图形验证码字符

    返回:
        dict: 登录响应数据，包含 user_id、ses_id、login_name 等字段；
              失败返回 None。
    """
    if not captcha_data or not captcha_data.get("imgUniCode"):
        raise ValueError("验证码数据异常，缺少 imgUniCode。")
    if not phone or not password or not img_auth_code:
        raise ValueError("手机号、密码和验证码都必须填写。")

    # 密码经 MD5 哈希后再传输
    password_md5 = hashlib.md5(password.encode('utf-8')).hexdigest()

    payload = {
        "channel": CHANNEL,
        "app_ver_no": APP_VER_NO,
        "timestamp": str(int(time.time() * 1000)),
        "term_sys_ver": "12",
        "root": "0",
        "term_sys": "2",
        "model": "24031PN0DC",
        "term_id": "42e85afdd7e346e5",
        "login_name": phone,
        "pwd": password_md5,
        "imgUniCode": captcha_data["imgUniCode"],
        "imgAuthCode": img_auth_code.strip()
    }

    m = rand_str(24).upper()
    payload["dec_key"] = rsa_encrypt(ENCRYPTION_PUBLIC_KEY_PEM, m)

    # 对登录敏感字段进行 3DES 加密
    encrypt_keys_u004 = ["login_name", "pwd", "imgUniCode", "imgAuthCode"]
    for k in encrypt_keys_u004:
        if k in payload:
            payload[k] = des3_ecb_pkcs7_encrypt(m, payload[k])

    keys_for_sign = list(payload.keys())
    values_for_sign = [str(v) for v in payload.values()]

    values_concat = "".join(values_for_sign)
    string_to_sign = values_concat + SIGN_KEY_NEW
    payload["key"] = ",".join(keys_for_sign)
    payload["sign"] = rsa_sha256_sign(SIGNING_PRIVATE_KEY_PEM, string_to_sign)

    url = BASE_URL + "/unionApp/interf/front/U/U004"
    print(f"\n[*] 正在提交 U004 登录请求...")
    resp = session.post(url, json=payload, verify=False)

    try:
        resp_json = resp.json()
        if "data2" in resp_json:
            decrypted_json_str = decrypt_data2(resp_json["data2"])
            data_dict = json.loads(decrypted_json_str)
            print("[+] U004 登录响应解密成功：")
            print(json.dumps(data_dict, indent=2, ensure_ascii=False))
            return data_dict
        print("[-] U004 响应中没有 data2 字段:", resp.text)
        return None
    except Exception as e:
        print(f"[-] U004 请求解密失败: {e}")
        return None


def login_u004(captcha_data, phone, password):
    """
    密码登录流程：将验证码图片保存到本地，提示用户手动输入验证码，然后提交 U004 登录。

    参数:
        captcha_data (dict): 包含 img（Base64 图片）和 imgUniCode 的验证码数据
        phone (str): 手机号
        password (str): 明文密码

    返回:
        dict: 登录响应数据，失败返回 None
    """
    # 将 Base64 验证码图片解码并保存为本地文件，供用户查看
    try:
        with open("captcha.jpg", "wb") as f:
            f.write(decode_captcha_image(captcha_data))
        print("\n[*] 验证码图片已保存为当前目录下的 captcha.jpg")
    except Exception as e:
        print(f"[-] 保存验证码图片失败: {e}")
        return None

    # 等待用户手动输入验证码
    img_auth_code = input("[?] 请打开 captcha.jpg，输入验证码字符: ").strip()
    return login_u004_with_code(captcha_data, phone, password, img_auth_code)



# ================= 9. 命令行入口（测试/调试用） =================
if __name__ == "__main__":
    TEST_PHONE = input("请输入登录手机号: ")

    print("\n请选择登录方式:")
    print("  1. 密码登录")
    print("  2. 短信验证码登录")
    login_mode = input("请选择 (1/2，默认 1): ").strip() or "1"

    print("\n--- 第一步：获取验证码 ---")
    captcha_data = get_captcha_u067()

    if not captcha_data or captcha_data.get("result") != "0":
        print("[-] 获取验证码失败，程序退出。")
        exit(1)

    if login_mode == "2":
        # 短信验证码登录路径
        try:
            with open("captcha.jpg", "wb") as f:
                f.write(decode_captcha_image(captcha_data))
            print("\n[*] 验证码图片已保存为当前目录下的 captcha.jpg")
        except Exception as e:
            print(f"[-] 保存验证码图片失败: {e}")
            exit(1)

        img_auth_code = input("[?] 请打开 captcha.jpg，输入图形验证码: ").strip()

        print("\n--- 第二步：发送短信验证码 ---")
        sms_result = send_sms(captcha_data, TEST_PHONE, img_auth_code)

        if sms_result and sms_result.get("result") == "0":
            print("\n--- 第三步：提交短信验证码登录 ---")
            sms_code = input("[?] 请输入手机收到的短信验证码: ").strip()
            login_result = login_u065(TEST_PHONE, sms_code)
        else:
            print(f"[-] 短信发送失败: {(sms_result and sms_result.get('msg')) or '未知错误'}")
    else:
        # 密码登录路径
        TEST_PWD = input("请输入登录密码: ")
        login_result = login_u004(captcha_data, TEST_PHONE, TEST_PWD)

    # 登录成功后，可选测试绿色出行码
    if login_result and login_result.get("result") == "0":
        user_id = login_result.get("user_id") or login_result.get("login_name") or ""
        ses_id = login_result.get("ses_id") or ""
        if user_id and ses_id:
            print(f"\n[+] 登录成功！user_id={user_id}, ses_id={ses_id}")
            choice = input("\n是否测试绿色出行码？(y/n，默认 n): ").strip().lower()
            if choice == "y":
                qr_code_workflow(user_id, ses_id)