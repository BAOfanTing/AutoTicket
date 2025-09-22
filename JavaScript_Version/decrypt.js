// decrypt.js

const crypto = require('crypto');

// RSA 私钥 (直接嵌入代码中)
const RSA_PRIVATE_KEY_PEM = `-----BEGIN PRIVATE KEY-----
MIICdQIBADANBgkqhkiG9w0BAQEFAASCAl8wggJbAgEAAoGBAIOBMtf2AIYQlrNy/lVPHx4R/LKI+Vtk3bKmzID8vdVnh/4WA3lczqfejM10Xfy3sNe4l5EeQTvnDgUHbIFK8FyJRpvypAmS9oyW6uwGTjZEu5Y6hsSxiGAOG5ZOlH8vOSfuaAkZ+iUlqifPE3ZOmHkqGzmukg4wCRaPLx5ioq8zAgMBAAECgYAgLOVmx677HmXxBCrMbq57agU9HZx9SyGfS4Zv7Ob5pvo0Jei1sgpyMlabEmTIp50iOu0CubdWU8MvYdCfldlXQLW7cjk8N1NyGQLFd2fJ03a7gGWnwwEdPoNTpSHnB+mDL9l7MVjion5fLojzq9Pz1gMKL01I2TfZBDL4m6EbgQJBAMfgrMKtj7f40GA3qp/y/9/eBCAu8PbtFmtATLMQRf4tGhjvn349x1b6FZj8RiaRBSrq0Owjrdo5TUxgfS7dz3MCQQCobdWk2SQhRlqEHfFEro/8ab6gn3GhBDzzKvNjhKr2MO6JWqs+Vr+/P9uYpA+G+rv74uVIGWhjuNtI5+/69DFBAkAJOQS/tuJ6yrBSwD7PQpcr7UKjeYcE3cu7ByyC1q1kHRCnNedWG+Omz8NPW9Sg0vA6GrupKbxL5Xj7nTgpgXKhAkBIVlvioAvfaqrngUClAd//RZ9EtxYDVKGkwnaj8E/Iyr04KsPPU0ypJBD5XsT4cOmZxho5PAhUhAlSJ6MvAf/BAkA64ieVhtQA1KV0pSSEJMnbPlZe+yBYGTWLMaG2zL0kKEhIs2fIHbVhLFQ8TkO5oH+mhxuuXI5+nVU2G0dqUl6D
-----END PRIVATE KEY-----`;

// 固定的 DESede 密钥前缀
const DESEDE_KEY_PREFIX = Buffer.from("HTt0Hzsu", 'utf-8');

// 从标准输入获取JSON响应
function getStdin() {
    return new Promise((resolve, reject) => {
        let data = '';
        process.stdin.on('data', chunk => {
            data += chunk;
        });
        process.stdin.on('end', () => {
            resolve(data);
        });
        process.stdin.on('error', err => {
            reject(err);
        });
    });
}

async function decryptData2FromStdin() {
    let responseData;
    try {
        const responseText = (await getStdin()).trim();
        if (!responseText) {
            console.error("错误：未输入响应数据，解密终止。");
            process.exit(1);
        }
        
        responseData = JSON.parse(responseText);
        const data2 = responseData.data2;

        if (!data2) {
            console.error("错误：响应中没有data2字段，解密终止。");
            process.exit(1);
        }

        const finalDecryptedContent = decryptData2(data2);
        
        // 创建包含解密后data2的完整响应
        responseData.data2 = finalDecryptedContent;
        
        // 输出完整的JSON响应
        console.log(JSON.stringify(responseData, null, 2)); // null, 2 用于格式化输出
        
    } catch (e) {
        console.error(`解密过程中发生错误: ${e.message}`);
        if (responseData) {
            console.error("原始响应数据:");
            console.error(JSON.stringify(responseData, null, 2));
        } else {
            console.error("请检查输入的JSON数据是否有效。");
        }
        process.exit(1);
    }
}

function decryptData2(data2_full_base64) {
    if (data2_full_base64.length < 172) {
        throw new Error("data2 字符串长度不足 172，无法提取密钥材料。");
    }

    // --- 第一步：RSA 解密密钥材料 ---
    // 1. 提取 data2 的前 172 个字符作为 RSA 加密数据 (Base64 编码)
    const rsa_encrypted_material_b64 = data2_full_base64.substring(0, 172);

    // 2. Base64 解码得到原始 RSA 密文
    const rsa_encrypted_buffer = Buffer.from(rsa_encrypted_material_b64, 'base64');
    

    // 3. RSA 解密 (使用 PKCS #1 v1.5 填充)
    // Node.js crypto.privateDecrypt 支持 PKCS#1_OAEP 和 PKCS#1_V1_5 填充
    // 对应 Java 的 "RSA/ECB/PKCS1Padding"
    const rsa_decrypted_buffer = crypto.privateDecrypt(
        {
            key: RSA_PRIVATE_KEY_PEM,
            padding: crypto.constants.RSA_PKCS1_PADDING, // 对应 PKCS1_v1_5 填充
        },
        rsa_encrypted_buffer
    );
    const rsa_decrypted_str = rsa_decrypted_buffer.toString('utf-8');
    

    // --- 第二步：DESede 解密实际数据 ---
    // 1. 提取 data2 的后半部分作为 DESede 密文 (Base64 编码)
    const desede_encrypted_data_b64 = data2_full_base64.substring(172);

    // 2. 生成 DESede 密钥 (K1K2K3 模式，取前 24 字节)
    // Java: ("HTt0Hzsu" + str2).getBytes()
    // 这里的 str2 就是 rsa_decrypted_str
    const full_desede_key_buffer = Buffer.concat([
        DESEDE_KEY_PREFIX, 
        Buffer.from(rsa_decrypted_str, 'utf-8')
    ]);
    const desede_key = full_desede_key_buffer.subarray(0, 24); // 使用 subarray 兼容旧 Node.js (slice 也行)

    if (desede_key.length !== 24) {
        throw new Error(`生成的 DESede 密钥长度 ${desede_key.length} 不足 24 字节，无法用于三重 DES。`);
    }
   

    // 3. 生成 IV (Initialization Vector)
    // Java: str2.substring(0, 8).getBytes()
    // 这里的 str2 还是 rsa_decrypted_str
    const iv_str = rsa_decrypted_str.substring(0, 8);
    const iv = Buffer.from(iv_str, 'utf-8');

    if (iv.length !== 8) {
        throw new Error(`生成的 IV 长度 ${iv.length} 不符合 8 字节要求。`);
    }
    

    // 4. Base64 解码 DESede 密文
    const desede_encrypted_buffer = Buffer.from(desede_encrypted_data_b64, 'base64');
    

    // 5. 创建 DES3 Cipher 对象并解密
    // 对应 Java 的 "DESede/CBC/PKCS5Padding"
    const decipher = crypto.createDecipheriv('des-ede3-cbc', desede_key, iv);

    // 6. 解密并移除 PKCS7 填充 (Node.js 的 PKCS7 填充就是 PKCS5Padding)
    decipher.setAutoPadding(true); // 默认启用 PKCS7/PKCS5 padding

    let decrypted = decipher.update(desede_encrypted_buffer);
    decrypted = Buffer.concat([decrypted, decipher.final()]);

    // 7. 返回 UTF-8 编码的明文字符串
    return decrypted.toString('utf-8');
}


// 如果脚本被直接执行，则从标准输入读取数据并执行解密
if (require.main === module) {
    decryptData2FromStdin();
}

// 可选：如果需要其他 JS 脚本导入这个功能
module.exports = {
    decryptData2
};
