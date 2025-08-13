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

SIGN_KEY = "qwerqaz.-*"   # b775 里用的固定 signkey
ENCRYPT_KEYS = ["login_name", "user_id"]  # 需要 3DES 加密的字段
SES_ID = "be59660b6f1541bdb1a95d22c9eb1188" # 登录后再退出,登录会发生变化
LOGIN_NAME_PLAINTEXT = "HFbSkQ7f/BeguGThXNyVwQ=="
USER_ID_PLAINTEXT = "HFbSkQ7f/BeguGThXNyVwQ=="

URL = "https://app.hzgh.org.cn/unionApp/interf/front/OL/OL41"

# 指定运行时间 (HH:MM)
RUN_TIME = "11:30"
# ============================================


def random_str(length):
    """生成随机字符串"""
    chars = string.ascii_letters + string.digits
    return ''.join(random.choice(chars) for _ in range(length))


def rsa_encrypt(pub_key_pem, plaintext):
    """RSA 公钥加密"""
    rsakey = RSA.importKey(pub_key_pem)
    cipher = PKCS1_v1_5.new(rsakey)
    return base64.b64encode(cipher.encrypt(plaintext.encode())).decode()


def triple_des_encrypt(key, plaintext):
    """3DES ECB PKCS7 加密"""
    # 3DES 要求 key 长度是 24 字节
    key_bytes = key.encode()
    cipher = DES3.new(key_bytes, DES3.MODE_ECB)
    pad_len = 8 - len(plaintext) % 8
    padded = plaintext + chr(pad_len) * pad_len
    return base64.b64encode(cipher.encrypt(padded.encode())).decode()


def build_payload():
    # 1. 生成随机 24 位 m
    m = random_str(24)

    # 2. RSA 加密得到 dec_key
    dec_key = rsa_encrypt(PUBLIC_KEY_PEM, m)

    # 3. 构建数据字典
    data = {
        "channel": "02",
        "app_ver_no": "3.1.4",
        "timestamp": int(time.time() * 1000),
        "login_name": LOGIN_NAME_PLAINTEXT,
        "user_id": USER_ID_PLAINTEXT,
        "ses_id": SES_ID,
        "exchange_id": "10",
        "dec_key": dec_key
    }

    # 4. 对 encryptKeys 列表内的字段用 3DES 加密
    for k in ENCRYPT_KEYS:
        if data.get(k):
            data[k] = triple_des_encrypt(m, data[k])

    # 5. 生成 key 字段
    data["key"] = ",".join(data.keys())

    # 6. 生成 sign
    sign_str = "".join(str(data[k]) for k in data if k != "sign") + SIGN_KEY
    md5_val = hashlib.md5(sign_str.encode()).hexdigest().upper()
    sha256_val = hashlib.sha256(md5_val.encode()).hexdigest().upper()
    data["sign"] = sha256_val

    return data


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
