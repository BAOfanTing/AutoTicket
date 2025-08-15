import requests
import time
import random
import string
import base64
import time
from datetime import datetime

from Crypto.PublicKey import RSA
from Crypto.Signature import pkcs1_15
from Cryptodome.Hash import SHA256
from Crypto.Cipher import DES3, PKCS1_v1_5
from Crypto.Util.Padding import pad, unpad

# ================= 配置区域 =================

# =========================参数配置======= = ==========================
CHANNEL = "02"
APP_VER_NO = "3.1.4"
SES_ID = "44f451f1dad24fc18f7ebfa076128314" # 重新登录后会变
LOGIN_NAME_PLAINTEXT = "HFbSkQ7f/BeguGThXNyVwQ=="
USER_ID_PLAINTEXT = "HFbSkQ7f/BeguGThXNyVwQ=="
EXCHANGE_ID_PLAINTEXT = "10"   #9是2块,10是4块,11是6块
RUN_TIME = datetime(2025, 8, 15, 10, 20, 59, 000000)  # 2025-08-16 06:59:59.900
RUN_COUNT = 10                 # 运行次数

# ======================================= = ==========================

# 【密钥1】用于加密3DES密钥的【公钥】
ENCRYPTION_PUBLIC_KEY_PEM = """-----BEGIN PUBLIC KEY-----
MIGfMA0GCSqGSIb3DQEBAQUAA4GNADCBiQKBgQC7yWoQaojBBqKI2H0j4e8ZeX/n1yip6hxrxSVth5F5n1JJ/B3liPMdz6K1chNLFTAcbI7hTL9KkphP9yQ+bPYD68Ajrt/DFrW679Zi1CoeetHVrM4sF68lYarGXwnSlKloaPWnI4Ch9cSqIvIOInlpeJqYPlJ8ZJvGCmbQoM6bewIDAQAB
-----END PUBLIC KEY-----"""

# 【密钥2】用于RSA签名的【签名私钥】(从JS的B函数中提取)
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

# 【密钥3】用于拼接在签名数据末尾的【签名字符串】
SIGN_KEY_NEW = "zSw3MLRV7VuwT!*G"

# JS代码中定义的需要加密的字段和不需要签名的字段
ENCRYPT_KEYS = ["login_name", "user_id"]
NO_SIGN_KEYS = [
    "answerContent", "surveyId", "content", "preContent", "img", "img1",
    "img2", "package", "codeUrl", "belong", "verCode"
]

URL = "https://app.hzgh.org.cn/unionApp/interf/front/OL/OL41"

# ======================================= = ==========================

def rand_str(n):
    return ''.join(random.choice(string.ascii_letters + string.digits) for _ in range(n))

def rsa_encrypt(pub_pem, s):
    rsakey = RSA.importKey(pub_pem)
    cipher = PKCS1_v1_5.new(rsakey)
    return base64.b64encode(cipher.encrypt(s.encode('utf-8'))).decode('utf-8')

def des3_ecb_pkcs7_encrypt(key24, plaintext):
    key_bytes = key24.encode('utf-8')
    cipher = DES3.new(key_bytes, DES3.MODE_ECB)
    # 使用pycryptodome自带的pad函数进行PKCS7填充
    padded_data = pad(plaintext.encode('utf-8'), DES3.block_size, style='pkcs7')
    encrypted = cipher.encrypt(padded_data)
    return base64.b64encode(encrypted).decode('utf-8')

def rsa_sha256_sign(private_key_pem, data_string):
    """使用私钥对数据进行SHA256withRSA签名，并返回Base64结果"""
    key = RSA.import_key(private_key_pem)
    h = SHA256.new(data_string.encode('utf-8'))
    signature = pkcs1_15.new(key).sign(h)
    return base64.b64encode(signature).decode('utf-8')

def build_payload():
    """
    完全模拟JS端的加密和签名逻辑
    流程: 准备数据 -> 过滤空值 -> 加密 -> 过滤不签名字段 -> RSA签名
    """
    # 1. 准备所有参数
    payload = {
        "channel": CHANNEL,
        "app_ver_no": APP_VER_NO,
        "timestamp": int(time.time() * 1000)
    }
    if LOGIN_NAME_PLAINTEXT: payload["login_name"] = LOGIN_NAME_PLAINTEXT
    if USER_ID_PLAINTEXT: payload["user_id"] = USER_ID_PLAINTEXT
    if SES_ID: payload["ses_id"] = SES_ID
    payload["exchange_id"] = EXCHANGE_ID_PLAINTEXT

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
    pad_len = data[-1]
    return data[:-pad_len]

def decrypt_data2(data2):
    rsa_enc = data2[:172]
    des_enc = data2[172:]

    rsa_enc_bytes = base64.b64decode(rsa_enc)
    des_enc_bytes = base64.b64decode(des_enc)

    rsakey = RSA.importKey(PRIVATE_KEY_PEM)
    cipher_rsa = PKCS1_v1_5.new(rsakey)
    a_bytes = cipher_rsa.decrypt(rsa_enc_bytes, None)
    a = a_bytes.decode()

    key = ("HTt0Hzsu" + a).encode()
    iv = a[:8].encode()

    cipher_des3 = DES3.new(key, DES3.MODE_CBC, iv)
    decrypted = cipher_des3.decrypt(des_enc_bytes)
    decrypted = pkcs7_unpad(decrypted)
    return decrypted.decode()

def run_exchange():
    """执行一次兑换操作"""
    headers = {
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

    proxies = {
        "http": "http://127.0.0.1:8888",
        "https": "http://127.0.0.1:8888"
    }

    payload = build_payload()
    # print("请求数据:", payload)
    # # 自检：签名长度应为 172
    # print("sign 长度:", len(payload.get("sign","")))

    resp = requests.post(URL, headers=headers, json=payload, verify=False, proxies=proxies)
    print("状态码:", resp.status_code)
    # print("响应:", resp.text)
    try:
        resp_json = resp.json()
        if "data2" in resp_json:
            decrypted_json = decrypt_data2(resp_json["data2"])
            print("解密响应:", decrypted_json)
        else:
            print("返回中没有 data2 字段")
    except Exception as e:
        print("解密失败:", e)

count = 0
def job():
    """定时任务执行的函数"""
    global count
    for i in range(RUN_COUNT):
        print(f"第{i + 1}次执行兑换任务，当前时间：{datetime.now()}")
        run_exchange()
        count += 1

def wait_until_target():
    while True:
        now = datetime.now()
        if now >= RUN_TIME:
            break
        # 控制检查频率到毫秒
        time.sleep(0.0005)  # 0.5 毫秒检查一次

def main():
    """主函数，设置定时任务并运行"""
    # 设置每天7:00执行任务
    
    print(f"程序已启动，将在每天{RUN_TIME}执行兑换任务，共执行{RUN_COUNT}次。")
    wait_until_target()
    # 保持程序运行
    job()


if __name__ == "__main__":
    main()
