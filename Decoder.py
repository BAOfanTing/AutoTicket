"""
Decoder.py - 响应数据解密模块
提供对服务端返回的 data2 字段进行 RSA + 3DES 双层解密的工具函数。
"""

import base64
from Crypto.Cipher import PKCS1_v1_5, DES3
from Crypto.PublicKey import RSA
import json

# RSA 私钥，用于解密 data2 中的 3DES 密钥
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
    """去除 PKCS7 填充（末字节表示填充长度）"""
    return data[:-pad_len]

def decrypt_data2(data2):
    """
    解密服务端返回的 data2 字段。

    解密流程：
    1. 提取前 172 字符（RSA 密文的 Base64），剩余部分为 3DES 密文的 Base64
    2. 用 RSA 私钥解密得到临时密钥字符串 a
    3. 以 "HTt0Hzsu" + a 作为 3DES 密钥、a 前 8 字节为 IV，进行 CBC 解密
    4. 去除 PKCS7 填充后得到 JSON 字符串

    参数:
        data2 (str): 服务端返回的 data2 字符串

    返回:
        str: 解密后的 JSON 字符串
    """
    # 拆分 RSA 密文部分（前 172 字符）和 3DES 密文部分
    rsa_enc = data2[:172]
    des_enc = data2[172:]

    # Base64 解码
    rsa_enc_bytes = base64.b64decode(rsa_enc)
    des_enc_bytes = base64.b64decode(des_enc)

    # 用 RSA 私钥解密，得到临时密钥 a
    rsakey = RSA.importKey(PRIVATE_KEY_PEM)
    cipher_rsa = PKCS1_v1_5.new(rsakey)
    a_bytes = cipher_rsa.decrypt(rsa_enc_bytes, None)
    a = a_bytes.decode()

    # 按约定构造 3DES 密钥和 IV
    key = ("HTt0Hzsu" + a).encode()
    iv = a[:8].encode()

    # 3DES CBC 模式解密并去除 PKCS7 填充
    cipher_des3 = DES3.new(key, DES3.MODE_CBC, iv)
    decrypted = cipher_des3.decrypt(des_enc_bytes)
    decrypted = pkcs7_unpad(decrypted)

    return decrypted.decode()

# 示例
data2_str = "ERM+FNAM5Ld/stmSVHZZhleCCIMbI/qszUwuQxScROi1hILgVpQBVJG0dB3u3xz2/WT3yIMiy7PagPfl1DTLL656w70wG3FzrcaTkoT5omrShfu4iWnaXW+E68rAuSemKj11pm72XhlMacJTtVoJdmcG8ILKIbyp4zCwHMfo/Po=VdQiXJJh4ETkwuyNqQXT+gCzXatZDFNu3Giyub0FkMY9bMaJDNhWw/7nB4XAzZNZtTnYPr1FsxGRzYgg1tsbrE9mWum2c08D"
print(decrypt_data2(data2_str))