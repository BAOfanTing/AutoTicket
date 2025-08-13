import requests
import time
import random
import string
import base64
import hashlib
import schedule
from Crypto.Cipher import DES3, PKCS1_v1_5
from Crypto.PublicKey import RSA

# ================= 配置区域 =================
PUBLIC_KEY_PEM = """-----BEGIN PUBLIC KEY-----
MIGfMA0GCSqGSIb3DQEBAQUAA4GNADCBiQKBgQCVXsxrrMcxNwFNYt0wMTdqc5WMa4gr7nMbWbcQCpJ2XNBMTQetknYNzCr8MMRdHBKFKjdCJE40u6UDBXQx13z7OSKyvQBwtLj5n8eIQXRtpMIjvqfR1xRuNBi5147ZXJDbKxWGRm0kjLN5UuqnDe6zu8v6MKU7KNDzHUrWqsj2LwIDAQAB
-----END PUBLIC KEY-----"""

SIGN_KEY = "qwerqaz.-*"
ENCRYPT_KEYS = ["login_name", "user_id"]   # 这俩需要 3DES(m) 加密
URL = "https://app.hzgh.org.cn/unionApp/interf/front/OL/OL41"

# ！！！把下面三项替换成 localStorage["login"] 明文里的真实值
CHANNEL = "02"                 # Android=02
APP_VER_NO = "3.1.4"          # 你 App 里看到的 version

SIGN_KEY = "qwerqaz.-*"   # b775 里用的固定 signkey
ENCRYPT_KEYS = ["login_name", "user_id"]  # 需要 3DES 加密的字段
SES_ID = "be59660b6f1541bdb1a95d22c9eb1188"
LOGIN_NAME_PLAINTEXT = "HFbSkQ7f/BeguGThXNyVwQ=="
USER_ID_PLAINTEXT = "HFbSkQ7f/BeguGThXNyVwQ=="

URL = "https://app.hzgh.org.cn/unionApp/interf/front/OL/OL41"

# 指定运行时间 (HH:MM)
RUN_TIME = "11:30"
# ============================================


def rand_str(n):
    return ''.join(random.choice(string.ascii_letters + string.digits) for _ in range(n))

def rsa_encrypt(pub_pem, s):
    rsakey = RSA.importKey(pub_pem)
    cipher = PKCS1_v1_5.new(rsakey)
    return base64.b64encode(cipher.encrypt(s.encode())).decode()

def des3_ecb_pkcs7_encrypt(key24, plaintext):
    # PyCryptodome 对 24 字节 key 可能要求 parity；失败时用 adjust_key_parity
    key_bytes = key24.encode()
    try:
        cipher = DES3.new(key_bytes, DES3.MODE_ECB)
    except ValueError:
        from Crypto.Cipher.DES3 import adjust_key_parity
        key_bytes = adjust_key_parity(key_bytes)
        cipher = DES3.new(key_bytes, DES3.MODE_ECB)
    pad_len = 8 - (len(plaintext) % 8)
    padded = plaintext + chr(pad_len) * pad_len
    return base64.b64encode(cipher.encrypt(padded.encode())).decode()


def build_payload():
    # 1. b + c 合并（顺序严格保持）
    l = {
        "channel": CHANNEL,
        "app_ver_no": APP_VER_NO,
        "timestamp": int(time.time() * 1000),
        "login_name": LOGIN_NAME_PLAINTEXT,
        "user_id": USER_ID_PLAINTEXT,
        "ses_id": SES_ID,
        "exchange_id": "10"
    }

    # 2. 生成 m
    m = rand_str(24).upper()

    # 3. 加 dec_key
    l["dec_key"] = rsa_encrypt(PUBLIC_KEY_PEM, m)

    # 4. 对 ENCRYPT_KEYS 做 3DES 加密
    for k in ENCRYPT_KEYS:
        l[k] = des3_ecb_pkcs7_encrypt(m, l[k])

    # 5. 计算 sign（不含 sign、不含 key）
    values_concat = "".join(str(v) for v in l.values())
    md5_hex = hashlib.md5((values_concat + SIGN_KEY).encode()).hexdigest().upper()
    sign = hashlib.sha256(md5_hex.encode()).hexdigest().upper()

    # 6. 生成 key（必须在 sign 之后加）
    key_csv = ",".join(l.keys())

    # 7. 最终加上 key 和 sign
    l["key"] = key_csv
    l["sign"] = sign

    return l


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

DES_IV = b"12345678"

# ================== 解密函数 ==================
def pkcs7_unpad(data):
    pad_len = data[-1]
    return data[:-pad_len]

def decrypt_data2(data2):
    # 1. 提取前 172 字节（Base64解码前是字符串长度172，解码后是RSA块）
    rsa_enc = data2[:172]
    des_enc = data2[172:]

    # Base64 decode
    rsa_enc_bytes = base64.b64decode(rsa_enc)
    des_enc_bytes = base64.b64decode(des_enc)

    # 2. RSA 私钥解密，得到 a
    rsakey = RSA.importKey(PRIVATE_KEY_PEM)
    cipher_rsa = PKCS1_v1_5.new(rsakey)
    a_bytes = cipher_rsa.decrypt(rsa_enc_bytes, None)
    a = a_bytes.decode()

    # 3. 构造 3DES key 和 iv
    key = ("HTt0Hzsu" + a).encode()
    iv = a[:8].encode()

    # 4. 3DES CBC PKCS7 解密
    cipher_des3 = DES3.new(key, DES3.MODE_CBC, iv)
    decrypted = cipher_des3.decrypt(des_enc_bytes)
    decrypted = pkcs7_unpad(decrypted)

    # 5. 转成 JSON
    return decrypted.decode()

# def job():
def main():
    headers = {
        "Host": "app.hzgh.org.cn",
        "Connection": "keep-alive",
        "Accept": "application/json, text/plain, */*",
        "User-Agent": "Mozilla/5.0 (Linux; Android 9; SKW-A0 Build/PQ3A.190705.08061357; wv) "
                      "AppleWebKit/537.36 (KHTML, like Gecko) Version/4.0 Chrome/91.0.4472.114 "
                      "Safari/537.36;unionApp;HZGH",
        "Content-Type": "application/json;charset=UTF-8",
        "Origin": "https://app.hzgh.org.cn:8123",
        "X-Requested-With": "com.zjte.hanggongefamily",
        "Referer": "https://app.hzgh.org.cn:8123/",
        "Accept-Encoding": "gzip, deflate",
        "Accept-Language": "zh-CN,zh;q=0.9,en-US;q=0.8,en;q=0.7"
    }

    #让python通过fiddler走手机的通道发起请求
    proxies = {
        "http": "http://127.0.0.1:8888",
        "https": "http://127.0.0.1:8888"
    }

    payload = build_payload()
    print("请求数据:", payload)

    resp = requests.post(URL, headers=headers, json=payload, verify=False, proxies=proxies)
    print("状态码:", resp.status_code)
    print("响应:", resp.text)
    try:
        resp_json = resp.json()
        if "data2" in resp_json:
            decrypted_json = decrypt_data2(resp_json["data2"])
            print("解密响应:", decrypted_json)
        else:
            print("返回中没有 data2 字段")
    except Exception as e:
        print("解密失败:", e)

# def main():

#     schedule.every().day.at(RUN_TIME).do(run_twice_with_delay)
    
#     while True:
#         schedule.run_pending()
#         time.sleep(1)


# def run_twice_with_delay():
#     # 在指定时间运行第一次
#     job()
#     # 等待0.5秒
#     time.sleep(0.5)
#     # 运行第二次
#     job()


if __name__ == "__main__":
    main()
