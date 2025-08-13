import base64
from Crypto.Cipher import PKCS1_v1_5, DES3
from Crypto.PublicKey import RSA
import json

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

# 示例
data2_str = "Gx6vn2AcOSx0OgNWgVBnF6pE2WPUdl4PBl5BfT/Lv5tq3Yf7MsDMXGlvHwySfIvMnFMl6dwvtyjyAmuaQbqo+yB3lAgJ7sQb1kkhmpNZXrWGn31b1iYxqoZyRIOrGMDAoK5CNUjgF/VTaPxY9a5ypNUSWNVWUg7GtzAa+O7FHa4=xpg4u/l6MffuKk8aHF8fv90LdtzYt/oaqQon2qekZfqCmKpuJkQt/eyhO5g0OPID8pphMpu+qhDWGicQdkh5q3foqwrh3IgRy5kH1mulC7s="
print(decrypt_data2(data2_str))