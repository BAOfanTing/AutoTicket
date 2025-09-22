#!/usr/bin/env node
/**
 * 完整RSA签名加密模块
 * 基于encrypto.py重写，包含正确的RSA签名
 */

const crypto = require('crypto');
const NodeRSA = require('node-rsa');

// 常量定义
const F38860A = "0123456789abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ";
const F38813C_PUB_KEY_BASE64 = "MIGfMA0GCSqGSIb3DQEBAQUAA4GNADCBiQKBgQCVXsxrrMcxNwFNYt0wMTdqc5WMa4gr7nMbWbcQCpJ2XNBMTQetknYNzCr8MMRdHBKFKjdCJE40u6UDBXQx13z7OSKyvQBwtLj5n8eIQXRtpMIjvqfR1xRuNBi5147ZXJDbKxWGRm0kjLN5UuqnDe6zu8v6MKU7KNDzHUrWqsj2LwIDAQAB";
const F38814D_PUB_KEY_B_BASE64 = "MIGfMA0GCSqGSIb3DQEBAQUAA4GNADCBiQKBgQC7yWoQaojBBqKI2H0j4e8ZeX/n1yip6hxrxSVth5F5n1JJ/B3liPMdz6K1chNLFTAcbI7hTL9KkphP9yQ+bPYD68Ajrt/DFrW679Zi1CoeetHVrM4sF68lYarGXwnSlKloaPWnI4Ch9cSqIvIOInlpeJqYPlJ8ZJvGCmbQoM6bewIDAQAB";
const F27605N_PRIV_KEY_BASE64 = "MIICeAIBADANBgkqhkiG9w0BAQEFAASCAmIwggJeAgEAAoGBAJ+C8Z9awsGU8DeBpq47p+pVBgIxWr9epYE5lTrVwoTvOv7dOBTsNgYPgDqFLbU8eZsV26DOvgd4TC5tZUWF7WbAleOcxvwA143XTBpZEeDx6who8KiW1WBKUwkeEfXZvOWhN2d+8GlCjvJu2J4yNGEXScQEIWb+ofE4Pd4yPkkzAgMBAAECgYB0Tzu18a0vEFX0c1JBm3g98w81jB1aiz3tMzqwMuvqmLIQ4uegwfhGhQkAItoIW/dj8RU7dWS096+87sG4ZwaKCv/SmT1CibqmSATrX6YNIFU4uXsZzMREJxmZi+V5AllT9DWBG5YjKgrGfWjL0Rq10ZvxYMTdjO+SbqDIjVoc+QJBAOrMXRO6G349NpLvo1QPevxIykKNKhr5Qkjv4oVydoVoHW6iMU30PhrBqBYla+K8W+xyeqrjd9ucDQFW/Z2+hD8CQQCt6jz4o7qadQM0gikoBsgWwp7teyZI/8ZH5htrKZwDJzUe6LuM9xjDeXAqqjNjQrDL7M+6T7ZwMmK3UN3boe4NAkEA6ioGabYh1TSXSNNVwG/v58twbA78/wm34aXb89rD+Shssflv0p7TkTuxtuR7RBU2WAmT7PoOfyaSkdN/++IVYQJBAJ/klCvQc/YfkFPNO0N2gK0UP4N8zmUc6tIdh6XNeocXm+oP9KaUYusMkghXtKkUnnDOBul28fdTC5kYOvD7fl0CQQDLIYfo8MSMgcFkBH1wRUbhjVv31bk8+4G9a+h7UkLdLtch5qPsS7bsFCyszqEYjhYtQ278Q20lSzaIsom0Q3ai"
const F5734B = new Set(["login_name", "login_auth_code", "auth_code", "pwd", "password", "newpwd", "amt", "tr_amt", "sms_code", "total_amount", "account_no", "mob_data", "order_amt", "before_amt", "txn_amt", "tel", "mobile", "new_mobile", "code", "cert_no", "card_no", "reserve_mobile", "reply_tel", "card_bal", "bank_card_no", "car_no", "user_id", "invite_code", "auth_code", "imgAuthCode", "imgUniCode"]);
const F27603M = "qwerqaz.-*";
const F27579A = "https://zhgh.hzgh.org/";
const EXCLUDE_SIGN_FIELDS = new Set(["content", "link_url", "url", "pic_cont", "advice_img1", "advice_img2", "advice_img3", "photo_one", "photo_two", "photo_three", "book_img", "pimge"]);
const SIGN_SALT_FOR_ELSE_BRANCH = "zSw3MLRV7VuwT!*G";

// 预加载RSA密钥
let rsaKeys = {
    f38813c: null,
    f38814d: null,
    f27605n: null
};

// 初始化RSA密钥
function initRSAKeys() {
    if (!rsaKeys.f38813c) {
        try {
            rsaKeys.f38813c = new NodeRSA();
            rsaKeys.f38813c.importKey(Buffer.from(F38813C_PUB_KEY_BASE64, 'base64'), 'public-der');
        } catch (error) {
            console.error('Failed to load f38813c key:', error.message);
        }
    }
    if (!rsaKeys.f38814d) {
        try {
            rsaKeys.f38814d = new NodeRSA();
            rsaKeys.f38814d.importKey(Buffer.from(F38814D_PUB_KEY_B_BASE64, 'base64'), 'public-der');
        } catch (error) {
            console.error('Failed to load f38814d key:', error.message);
        }
    }
    if (!rsaKeys.f27605n) {
        try {
            // 尝试PKCS#1格式
            const privateKeyPem = `-----BEGIN RSA PRIVATE KEY-----\n${F27605N_PRIV_KEY_BASE64}\n-----END RSA PRIVATE KEY-----`;
            rsaKeys.f27605n = new NodeRSA();
            rsaKeys.f27605n.importKey(privateKeyPem, 'private-pem');
        } catch (error) {
            try {
                // 尝试PKCS#8格式
                const privateKeyPem = `-----BEGIN PRIVATE KEY-----\n${F27605N_PRIV_KEY_BASE64}\n-----END PRIVATE KEY-----`;
                rsaKeys.f27605n = new NodeRSA();
                rsaKeys.f27605n.importKey(privateKeyPem, 'private-pem');
            } catch (error2) {
                try {
                    // 尝试直接导入Base64
                    rsaKeys.f27605n = new NodeRSA();
                    rsaKeys.f27605n.importKey(Buffer.from(F27605N_PRIV_KEY_BASE64, 'base64'), 'private-der');
                } catch (error3) {
                    // 静默处理错误，else分支不需要私钥
                    // console.error('Failed to load f27605n key:', error3.message);
                }
            }
        }
    }
}

// 快速生成随机字符串
function generateRandomStrC(length = 24) {
    let result = '';
    for (let i = 0; i < length; i++) {
        result += F38860A[Math.floor(Math.random() * F38860A.length)];
    }
    return result.toUpperCase();
}

// 快速DESede加密
function desedeEncrypt(data, key) {
    try {
        const keyBuffer = Buffer.from(key, 'utf8');
        if (keyBuffer.length !== 24) {
            throw new Error("DESede key must be 24 bytes");
        }
        
        // 使用ECB模式，手动PKCS7填充
        const cipher = crypto.createCipheriv('des-ede3-ecb', keyBuffer, null);
        cipher.setAutoPadding(false);
        
        // 手动PKCS7填充
        const blockSize = 8;
        const dataBuffer = Buffer.from(data, 'utf8');
        const padding = blockSize - (dataBuffer.length % blockSize);
        const paddedData = Buffer.concat([dataBuffer, Buffer.alloc(padding, padding)]);
        
        const encrypted = Buffer.concat([cipher.update(paddedData), cipher.final()]);
        return encrypted.toString('base64');
    } catch (error) {
        console.error('DESede encryption error:', error);
        return null;
    }
}

// 快速MD5哈希
function md5Hash(text) {
    return crypto.createHash('md5').update(text, 'utf8').digest('hex');
}

// 快速SHA1哈希
function sha1Hash(text) {
    return crypto.createHash('sha1').update(text, 'utf8').digest('hex');
}

// 快速RSA加密 - 使用Node.js原生crypto模块匹配Python版本
function rsaEncryptStrC(strCKey, useZhghKey = false) {
    try {
        const keyBase64 = useZhghKey ? F38813C_PUB_KEY_BASE64 : F38814D_PUB_KEY_B_BASE64;
        
        // 将base64密钥转换为PEM格式
        const publicKeyPem = `-----BEGIN PUBLIC KEY-----\n${keyBase64}\n-----END PUBLIC KEY-----`;
        
        // 使用RSA公钥加密
        const encrypted = crypto.publicEncrypt({
            key: publicKeyPem,
            padding: crypto.constants.RSA_PKCS1_PADDING
        }, Buffer.from(strCKey, 'utf8'));
        
        return encrypted.toString('base64');
    } catch (error) {
        console.error('RSA encryption error:', error);
        return null;
    }
}

// RSA SHA256签名 - 使用Node.js crypto模块，与Python版本一致
function rsaSha256Sign(message, privateKeyBase64) {
    try {
        // 使用正确的私钥
        const privateKeyPem = `-----BEGIN PRIVATE KEY-----\n${F27605N_PRIV_KEY_BASE64}\n-----END PRIVATE KEY-----`;
        
        // 使用crypto.createSign，这与Python的PKCS1_v1_5.new()等效
        const sign = crypto.createSign('RSA-SHA256');
        sign.update(message, 'utf8');
        const signature = sign.sign(privateKeyPem, 'base64');
        
        return signature;
    } catch (error) {
        console.error('RSA SHA256 signing error:', error);
        return null;
    }
}

// zhgh分支加密
function encryptRequestZhghBranch(originalParams) {
    const finalJsonObj = { ...originalParams };
    
    // 1. 生成会话密钥
    const strC = generateRandomStrC();
    
    // 2. 加密会话密钥
    const decKey = rsaEncryptStrC(strC, true);
    if (!decKey) {
        throw new Error("Failed to encrypt strC to dec_key.");
    }
    finalJsonObj["dec_key"] = decKey;
    
    // 3. 加密敏感字段
    for (const field of F5734B) {
        if (field in finalJsonObj && typeof finalJsonObj[field] === 'string') {
            const encryptedValue = desedeEncrypt(finalJsonObj[field], strC);
            if (encryptedValue) {
                finalJsonObj[field] = encryptedValue;
            }
        }
    }
    
    // 4. 生成签名
    const sortedKeys = Object.keys(finalJsonObj).sort();
    const str2Parts = [];
    const keyParts = [];
    
    for (const k of sortedKeys) {
        const v = finalJsonObj[k];
        if (Array.isArray(v)) continue; // 跳过JSONArray
        
        keyParts.push(k);
        str2Parts.push(String(v));
    }
    
    const str2 = str2Parts.join('');
    const keyStr = keyParts.join(',');
    
    // 双重哈希签名
    const signMessage = str2 + F27603M;
    const md5Result = md5Hash(signMessage.toUpperCase());
    const sha1Result = sha1Hash(md5Result.toUpperCase());
    const sign = sha1Result.toUpperCase();
    
    finalJsonObj["key"] = keyStr;
    finalJsonObj["sign"] = sign;
    
    return JSON.stringify(finalJsonObj);
}

// else分支加密
function encryptRequestElseBranch(originalParams) {
    const finalJsonObj = { ...originalParams };
    
    // 1. 生成会话密钥
    const strC = generateRandomStrC();
    
    // 2. 加密会话密钥
    const decKey = rsaEncryptStrC(strC, false);
    if (!decKey) {
        throw new Error("Failed to encrypt strC to dec_key.");
    }
    finalJsonObj["dec_key"] = decKey;
    
    // 3. 加密敏感字段
    for (const field of F5734B) {
        if (field in finalJsonObj && typeof finalJsonObj[field] === 'string') {
            const encryptedValue = desedeEncrypt(finalJsonObj[field], strC);
            if (encryptedValue) {
                finalJsonObj[field] = encryptedValue;
            }
        }
    }
    
    // 4. 生成签名
    const sortedKeys = Object.keys(finalJsonObj).sort();
    const str3Parts = [];
    const keyParts = [];
    
    for (const k of sortedKeys) {
        const v = finalJsonObj[k];
        
        if (EXCLUDE_SIGN_FIELDS.has(k)) continue;
        if (Array.isArray(v)) continue; // 跳过JSONArray
        
        keyParts.push(k);
        str3Parts.push(String(v));
    }
    
    const str3 = str3Parts.join('');
    const keyStr = keyParts.join(',');
    
    // RSA签名
    const signMessage = str3 + SIGN_SALT_FOR_ELSE_BRANCH;
    const sign = rsaSha256Sign(signMessage, F27605N_PRIV_KEY_BASE64);
    if (!sign) {
        throw new Error("Failed to generate signature.");
    }
    
    finalJsonObj["key"] = keyStr;
    finalJsonObj["sign"] = sign;
    
    return JSON.stringify(finalJsonObj);
}

// 主加密函数
function encryptRequest(originalParams, baseUrl = "") {
    // 预加载密钥
    initRSAKeys();
    
    if (baseUrl.startsWith(F27579A)) {
        return encryptRequestZhghBranch(originalParams);
    } else {
        return encryptRequestElseBranch(originalParams);
    }
}

// 检查是否为手慢响应
function isSlowResponse(data2Json) {
    return (data2Json.result === '999992' && 
            data2Json.msg && data2Json.msg.includes('手慢') && 
            data2Json.trcode === 'OL41');
}

module.exports = {
    encryptRequest,
    isSlowResponse,
    desedeEncrypt,
    rsaEncryptStrC,
    rsaSha256Sign,
    md5Hash,
    sha1Hash
};


