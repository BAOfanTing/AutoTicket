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
    pad_len = data[-1]
    if pad_len > len(data) - 1:
        raise ValueError("Invalid padding length for PKCS7 padding")
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
data2_str = "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"
print(decrypt_data2(data2_str))