#!/usr/bin/env node
/**
 * 工作流版本：3次签到 → 1次评论 → 1次查询积分
 * 每次执行都推送到钉钉
 * JavaScript版本，避免语言差距带来的性能差异
 */

const https = require('https');
const { exec } = require('child_process');
const { promisify } = require('util');
const execAsync = promisify(exec);
const fs = require('fs');
const path = require('path');
const crypto = require('crypto');
const { encryptRequest } = require('./encrypt_rsa.js');
const DINGTALK_CONFIG = require('./dingtalk_config.js');
const WORKFLOW_CONFIG = require('./workflow_config.js');

/**
 * 构建请求参数
 * @param {string} functionName - 功能名称 (login, signin, comment, query)
 * @param {Object} extraParams - 额外参数
 * @returns {Object} 完整的请求参数
 */
function buildRequestParams(functionName, extraParams = {}) {
    const params = {
        ...WORKFLOW_CONFIG.commonFields,
        timestamp: Date.now().toString(),
        ...WORKFLOW_CONFIG.functions[functionName],
        ...extraParams
    };
    return params;
}

/**
 * 构建完整URL
 * @param {string} functionName - 功能名称
 * @returns {string} 完整URL
 */
function buildUrl(functionName) {
    return `${WORKFLOW_CONFIG.baseUrl}${WORKFLOW_CONFIG.endpoints[functionName]}`;
}

/**
 * 通用执行函数
 * @param {string} functionName - 功能名称
 * @param {string} displayName - 显示名称
 * @param {Object} extraParams - 额外参数
 * @returns {Promise<boolean>} 执行结果
 */
async function executeFunction(functionName, displayName, extraParams = {}) {
    console.log(`\n${'='.repeat(60)}`);
    console.log(`🚀 ${displayName}`);
    console.log(`⏰ 开始时间: ${new Date().toLocaleString()}`);
    
    const params = buildRequestParams(functionName, extraParams);
    const url = buildUrl(functionName);
    
    try {
        // 生成加密请求
        const encryptedData = encryptRequest(params, url);
        console.log('🔐 加密请求体:', JSON.stringify(JSON.parse(encryptedData), null, 2));
        console.log('-'.repeat(50));
        
        // 发送请求
        const response = await sendRequestFast(url, encryptedData);
        
        console.log(`✅ 请求成功! 状态码: ${response.statusCode}`);
        console.log(`📄 原始响应: ${response.data}`);
        console.log('-'.repeat(50));
        
        // 解析响应
        try {
            const responseJson = JSON.parse(response.data);
            
            if (responseJson.data2) {
                console.log('🔍 发现data2字段，调用解密...');
                const decryptedResponse = await callDecryptScript(responseJson);
                
                if (decryptedResponse && decryptedResponse.data2) {
                    try {
                        const data2Json = JSON.parse(decryptedResponse.data2);
                        const msg = JSON.stringify(data2Json, null, 2);
                        console.log(`📋 解密结果: ${msg}`);
                        
                        // 发送到钉钉
                        const dingtalkMessage = `🚀 杭工e家${displayName}执行完成

⏰ 执行时间: ${new Date().toLocaleString()}
📋 结果: ${data2Json.msg || '未知'}

详细信息:
${msg}`;
                        
                        console.log('📤 发送钉钉通知...');
                        await sendDingTalkMessage(dingtalkMessage);
                        
                        return true;
                    } catch (parseError) {
                        console.log(`⚠️ data2内容解析失败: ${parseError.message}`);
                        return false;
                    }
                } else {
                    console.log('❌ 解密失败');
                    return false;
                }
            } else {
                console.log('⚠️ 响应中没有data2字段');
                return false;
            }
        } catch (jsonError) {
            console.log('响应不是JSON格式');
            return false;
        }
    } catch (error) {
        console.log(`❌ 请求失败: ${error.message}`);
        return false;
    }
}

/**
 * 快速发送HTTP请求
 */
function sendRequestFast(url, data) {
    return new Promise((resolve, reject) => {
        const urlObj = new URL(url);
        const options = {
            hostname: urlObj.hostname,
            port: urlObj.port || 443,
            path: urlObj.pathname,
            method: 'POST',
            headers: {
                ...WORKFLOW_CONFIG.headers,
                'Content-Length': Buffer.byteLength(data)
            },
            rejectUnauthorized: false,
            timeout: WORKFLOW_CONFIG.request.timeout
        };

        console.log('发送请求到:', url);

        const req = https.request(options, (res) => {
            let responseData = '';
            res.on('data', (chunk) => {
                responseData += chunk;
            });
            res.on('end', () => {
                resolve({
                    statusCode: res.statusCode,
                    data: responseData
                });
            });
        });

        req.on('error', (error) => {
            console.error('请求错误:', error);
            reject(error);
        });
        req.on('timeout', () => {
            console.error('请求超时');
            req.destroy();
            reject(new Error('Request timeout'));
        });

        req.write(data);
        req.end();
    });
}

/**
 * 调用decrypt.js脚本解密响应
 */
async function callDecryptScript(responseJson) {
    try {
        console.log('开始解密响应...');
        
        // 使用临时文件传递数据，避免shell转义问题
        const tempFile = path.join(__dirname, 'temp_response.json');
        
        // 写入临时文件
        fs.writeFileSync(tempFile, JSON.stringify(responseJson), 'utf8');
        
        try {
            // 使用临时文件进行解密
            const command = `node --security-revert=CVE-2023-46809 decrypt.js < "${tempFile}"`;
            const { stdout, stderr } = await execAsync(command, {
                timeout: 5000,
                shell: true
            });
            
            if (stderr && !stderr.includes('SECURITY WARNING')) {
                console.error('解密错误:', stderr);
                return null;
            }
            
            if (!stdout) {
                console.error('解密返回空结果');
                return null;
            }
            
            // 过滤掉安全警告信息，提取JSON部分
            const lines = stdout.split('\n');
            let jsonContent = '';
            let inJson = false;
            
            for (const line of lines) {
                const trimmedLine = line.trim();
                if (trimmedLine.startsWith('{')) {
                    inJson = true;
                    jsonContent = trimmedLine;
                } else if (inJson) {
                    jsonContent += ' ' + trimmedLine;
                    if (trimmedLine.endsWith('}')) {
                        break;
                    }
                }
            }
            
            if (!jsonContent) {
                console.error('解密输出中未找到有效JSON');
                return null;
            }
            
            console.log('解密成功，解析JSON...');
            return JSON.parse(jsonContent);
        } finally {
            // 清理临时文件
            try {
                fs.unlinkSync(tempFile);
            } catch (e) {
                // 忽略清理错误
            }
        }
    } catch (error) {
        console.error('解密失败:', error.message);
        return null;
    }
}

/**
 * 发送钉钉通知
 */
function sendDingTalkMessage(message) {
    return new Promise((resolve, reject) => {
        // 检查是否启用钉钉推送
        if (!DINGTALK_CONFIG.enabled) {
            console.log('📱 钉钉推送已禁用，跳过发送');
            resolve(true);
            return;
        }
        
        // 检查配置是否完整
        if (DINGTALK_CONFIG.webhook.includes('YOUR_ACCESS_TOKEN') || 
            DINGTALK_CONFIG.secret === 'YOUR_SECRET') {
            console.log('⚠️  钉钉配置未完成，请先配置 dingtalk_config.js 文件');
            resolve(false);
            return;
        }
        
        const timestamp = Date.now();
        const sign = crypto
            .createHmac('sha256', DINGTALK_CONFIG.secret)
            .update(`${timestamp}\n${DINGTALK_CONFIG.secret}`)
            .digest('base64');
        
        const webhook = `${DINGTALK_CONFIG.webhook}&timestamp=${timestamp}&sign=${encodeURIComponent(sign)}`;
        
        const data = JSON.stringify({
            msgtype: 'text',
            text: {
                content: message
            }
        });
        
        const options = {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'Content-Length': Buffer.byteLength(data)
            }
        };
        
        const req = https.request(webhook, options, (res) => {
            let responseData = '';
            res.on('data', (chunk) => {
                responseData += chunk;
            });
            res.on('end', () => {
                if (res.statusCode === 200) {
                    console.log('✅ 钉钉通知发送成功');
                    resolve(true);
                } else {
                    console.error('❌ 钉钉通知发送失败:', res.statusCode, responseData);
                    resolve(false);
                }
            });
        });
        
        req.on('error', (error) => {
            console.error('❌ 钉钉通知发送错误:', error.message);
            resolve(false);
        });
        
        req.write(data);
        req.end();
    });
}

/**
 * 执行登录签到功能
 */
async function loginFirst() {
    return await executeFunction('login', '执行登录签到功能');
}

/**
 * 执行签到功能
 */
async function executeSignin(attempt) {
    return await executeFunction('signin', `第 ${attempt} 次签到`);
}

/**
 * 执行评论功能
 */
async function executeComment() {
    return await executeFunction('comment', '执行评论功能');
}

/**
 * 执行查询积分功能
 */
async function executeQuery() {
    return await executeFunction('query', '执行查询积分功能');
}

/**
 * 主工作流函数
 */
async function main() {
    console.log('🎯 杭工e家工作流脚本 (JavaScript版本)');
    console.log('='.repeat(60));
    console.log('工作流: 3次签到 → 1次评论 → 1次查询积分');
    console.log('每次执行都推送到钉钉');
    console.log('='.repeat(60));
    
    const startTime = Date.now();
    
    try {
        // 执行登录签到
        console.log('\n🔄 开始执行登录签到...');
        await loginFirst();
        
        // 执行3次签到
        console.log('\n🔄 开始执行3次签到...');
        for (let i = 1; i <= 3; i++) {
            console.log(`\n第 ${i} 次签到:`);
            await executeSignin(i);
            await new Promise(resolve => setTimeout(resolve, WORKFLOW_CONFIG.request.retryDelay)); // 等待配置的延迟时间
        }
        
        // 执行1次评论
        console.log('\n🔄 开始执行评论...');
        await executeComment();
        
        // 执行1次查询积分
        console.log('\n🔄 开始查询积分...');
        await executeQuery();
        
        const totalTime = Date.now() - startTime;
        console.log('\n🎉 工作流执行完成!');
        console.log(`⏱️  总耗时: ${totalTime}ms`);
        console.log('='.repeat(60));
        
    } catch (error) {
        console.error('❌ 工作流执行失败:', error.message);
    }
}

// 运行工作流
if (require.main === module) {
    main().catch(console.error);
}

module.exports = { main, loginFirst, executeSignin, executeComment, executeQuery };
