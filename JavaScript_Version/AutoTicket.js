#!/usr/bin/env node
/**
 * 测试快速脚本 - 调试版本
 */

const https = require('https');
const { spawn } = require('child_process');
const { encryptRequest, isSlowResponse } = require('./encrypt_rsa.js');
const DINGTALK_CONFIG = require('./dingtalk_config.js');
const WORKFLOW_CONFIG = require('./workflow_config.js');

// 构建请求参数
function buildExchangeParams() {
    return {
        ...WORKFLOW_CONFIG.commonFields,
        timestamp: Date.now().toString(),
        ...WORKFLOW_CONFIG.functions.exchange
    };
}

// 构建完整URL
function buildExchangeUrl() {
    return `${WORKFLOW_CONFIG.baseUrl}${WORKFLOW_CONFIG.endpoints.exchange}`;
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
                'Host': 'app.hzgh.org.cn',
                'Content-Type': 'application/json;charset=UTF-8',
                'User-Agent': 'Mozilla/5.0 (Linux; Android 15; SM-9210 Build/AP2A.240905.003.F1; wv) AppleWebKit/537.36 (KHTML, like Gecko) Version/4.0 Chrome/139.0.7258.158 Mobile Safari/537.36;unionApp;HZGH',
                'Accept': 'application/json, text/plain, */*',
                'Sec-Ch-Ua': '"Not;A=Brand";v="99", "Android WebView";v="139", "Chromium";v="139"',
                'Sec-Ch-Ua-Mobile': '?1',
                'Sec-Ch-Ua-Platform': '"Android"',
                'Origin': 'https://app.hzgh.org.cn:8123',
                'X-Requested-With': 'com.zjte.hanggongefamily',
                'Sec-Fetch-Site': 'same-site',
                'Sec-Fetch-Mode': 'cors',
                'Sec-Fetch-Dest': 'empty',
                'Referer': 'https://app.hzgh.org.cn:8123/',
                'Accept-Encoding': 'gzip, deflate, br',
                'Accept-Language': 'zh-CN,zh;q=0.9,en-US;q=0.8,en;q=0.7',
                'Priority': 'u=1, i',
                'Pragma': 'no-cache',
                'Cache-Control': 'no-cache',
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
        const sign = require('crypto')
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
 * 快速解密响应（使用子进程调用带参数的decrypt.js）
 */
function decryptResponseFast(responseData) {
    return new Promise((resolve, reject) => {
        try {
            console.log('开始解密响应...');
            
            // 解析响应数据
            const parsedData = JSON.parse(responseData);
            
            // 构造完整的响应格式用于解密
            const fullResponse = {
                result: "000000",
                msg: "处理中",
                data2: parsedData.data2
            };
            
            // 使用子进程调用带参数的decrypt.js
            const child = spawn('node', ['--security-revert=CVE-2023-46809', 'decrypt.js'], {
                stdio: ['pipe', 'pipe', 'pipe']
            });
            
            let stdout = '';
            let stderr = '';
            
            child.stdout.on('data', (data) => {
                stdout += data.toString();
            });
            
            child.stderr.on('data', (data) => {
                stderr += data.toString();
            });
            
            child.on('close', (code) => {
                if (code !== 0) {
                    console.error('解密进程退出码:', code);
                    console.error('解密错误:', stderr);
                    resolve(null);
                    return;
                }
                
                if (stderr && !stderr.includes('SECURITY WARNING')) {
                    console.error('解密错误:', stderr);
                    resolve(null);
                    return;
                }
                
                if (!stdout) {
                    console.error('解密返回空结果');
                    resolve(null);
                    return;
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
                    resolve(null);
                    return;
                }
                
                try {
                    console.log('解密成功，解析JSON...');
                    const result = JSON.parse(jsonContent);
                    resolve(result);
                } catch (parseError) {
                    console.error('解析解密结果失败:', parseError.message);
                    resolve(null);
                }
            });
            
            child.on('error', (error) => {
                console.error('解密进程错误:', error.message);
                resolve(null);
            });
            
            // 向子进程发送数据
            child.stdin.write(JSON.stringify(fullResponse));
            child.stdin.end();
            
        } catch (error) {
            console.error('解密失败:', error.message);
            resolve(null);
        }
    });
}

/**
 * 执行单次请求
 */
async function executeRequest(params, attempt = 1) {
    const url = buildExchangeUrl();
    const startTime = Date.now();
    
    try {
        console.log(`\n🚀 第 ${attempt} 次尝试...`);
        
        // 生成加密请求
        const encryptStartTime = Date.now();
        const encryptedData = encryptRequest(params, WORKFLOW_CONFIG.baseUrl);
        const encryptTime = Date.now() - encryptStartTime;
        console.log(`🔐 加密完成，耗时: ${encryptTime}ms，数据长度: ${encryptedData.length}`);
        
        // 发送请求
        const requestStartTime = Date.now();
        const response = await sendRequestFast(url, encryptedData);
        const requestTime = Date.now() - requestStartTime;
        
        if (response.statusCode !== 200) {
            console.log(`⚠️  HTTP状态码: ${response.statusCode}，继续重试...`);
            
            // 忽略所有HTTP错误，继续重试
            const totalTime = Date.now() - startTime;
            return {
                isSlow: false,
                isError: true,
                isHttpError: true,
                error: `HTTP ${response.statusCode}`,
                errorType: 'HTTP_ERROR',
                data: {
                    result: "ERROR",
                    msg: `HTTP错误: ${response.statusCode}`,
                    trcode: "HTTP_ERROR"
                },
                timing: {
                    encryptTime: 0,
                    requestTime: totalTime,
                    decryptTime: 0,
                    totalTime: totalTime
                }
            };
        }
        
        console.log(`📡 请求完成，耗时: ${requestTime}ms`);
        
        // 解密响应
        const decryptStartTime = Date.now();
        console.log('🔓 开始解密响应...');
        
        // 解析响应
        const responseJson = JSON.parse(response.data);
        
        if (responseJson.data2) {
            const decryptedResponse = await decryptResponseFast(response.data);
            const decryptTime = Date.now() - decryptStartTime;
            
            if (decryptedResponse && decryptedResponse.data2) {
                const data2Json = JSON.parse(decryptedResponse.data2);
                const totalTime = Date.now() - startTime;
                
                console.log(`🔓 解密完成，耗时: ${decryptTime}ms`);
                console.log(`⏱️  总耗时: ${totalTime}ms`);
                console.log('📦 解密结果:', JSON.stringify(data2Json, null, 2));
                
                // 检查是否是"手慢"响应
                if (isSlowResponse(data2Json)) {
                    console.log('⚠️  检测到"手慢"响应，准备重试...');
                    return { 
                        isSlow: true, 
                        data: data2Json,
                        timing: {
                            encryptTime,
                            requestTime,
                            decryptTime,
                            totalTime
                        }
                    };
                } else {
                    console.log('🎉 成功！非"手慢"响应');
                    return { 
                        isSlow: false, 
                        data: data2Json,
                        timing: {
                            encryptTime,
                            requestTime,
                            decryptTime,
                            totalTime
                        }
                    };
                }
            } else {
                console.log('❌ 解密失败');
                return null;
            }
        } else {
            console.log('❌ 响应中没有data2字段');
            return null;
        }
    } catch (error) {
        const totalTime = Date.now() - startTime;
        console.log(`⚠️  网络错误: ${error.message}，继续重试...`);
        
        // 返回错误信息而不是null，这样主循环可以继续
        return {
            isSlow: false,
            isError: true,
            error: error.message,
            data: {
                result: "ERROR",
                msg: `请求失败: ${error.message}`,
                trcode: "NETWORK_ERROR"
            },
            timing: {
                encryptTime: 0,
                requestTime: totalTime,
                decryptTime: 0,
                totalTime: totalTime
            }
        };
    }
}

/**
 * 计算性能统计
 */
function calculatePerformanceStats(timings) {
    if (timings.length === 0) return null;
    
    const encryptTimes = timings.map(t => t.encryptTime);
    const requestTimes = timings.map(t => t.requestTime);
    const decryptTimes = timings.map(t => t.decryptTime);
    const totalTimes = timings.map(t => t.totalTime);
    
    const stats = {
        attempts: timings.length,
        encrypt: {
            min: Math.min(...encryptTimes),
            max: Math.max(...encryptTimes),
            avg: Math.round(encryptTimes.reduce((a, b) => a + b, 0) / encryptTimes.length)
        },
        request: {
            min: Math.min(...requestTimes),
            max: Math.max(...requestTimes),
            avg: Math.round(requestTimes.reduce((a, b) => a + b, 0) / requestTimes.length)
        },
        decrypt: {
            min: Math.min(...decryptTimes),
            max: Math.max(...decryptTimes),
            avg: Math.round(decryptTimes.reduce((a, b) => a + b, 0) / decryptTimes.length)
        },
        total: {
            min: Math.min(...totalTimes),
            max: Math.max(...totalTimes),
            avg: Math.round(totalTimes.reduce((a, b) => a + b, 0) / totalTimes.length)
        }
    };
    
    return stats;
}

/**
 * 生成请求耗时详情
 */
function generateRequestTimingDetails(requestDetails) {
    if (requestDetails.length === 0) return '';
    
    let details = '\n📊 每次请求耗时:\n';
    details += '┌─────────┬─────┬─────────────┐\n';
    details += '│ 尝试     │ 请求耗时 │ 结果       │\n';
    details += '├─────────┼─────┼─────────────┤\n';
    
    requestDetails.forEach(detail => {
        const timing = detail.timing;
        const result = detail.result;
        const msg = detail.msg.length > 8 ? detail.msg.substring(0, 8) + '...' : detail.msg;
        
        details += `│ 第${detail.attempt}次  │ ${timing.requestTime.toString().padStart(3)}ms │  ${msg.substring(0, 3)} │\n`;
    });
    
    details += '└─────────┴─────┴─────────────┘';
    return details;
}

/**
 * 显示性能统计
 */
function displayPerformanceStats(stats) {
    if (!stats) return;
    
    console.log('\n📊 性能统计报告');
    console.log('='.repeat(50));
    console.log(`🔄 总尝试次数: ${stats.attempts}`);
    console.log('\n⏱️  各阶段耗时统计 (毫秒):');
    console.log('┌─────────┬─────┬─────┬─────┐');
    console.log('│ 阶段   │ 最小 │ 最大 │ 平均 │');
    console.log('├─────────┼─────┼─────┼─────┤');
    console.log(`│ 加密   │ ${stats.encrypt.min.toString().padStart(3)} │ ${stats.encrypt.max.toString().padStart(3)} │ ${stats.encrypt.avg.toString().padStart(3)} │`);
    console.log(`│ 请求   │ ${stats.request.min.toString().padStart(3)} │ ${stats.request.max.toString().padStart(3)} │ ${stats.request.avg.toString().padStart(3)} │`);
    console.log(`│ 解密   │ ${stats.decrypt.min.toString().padStart(3)} │ ${stats.decrypt.max.toString().padStart(3)} │ ${stats.decrypt.avg.toString().padStart(3)} │`);
    console.log(`│ 总计   │ ${stats.total.min.toString().padStart(3)} │ ${stats.total.max.toString().padStart(3)} │ ${stats.total.avg.toString().padStart(3)} │`);
    console.log('└─────────┴─────┴─────┴─────┘');
}

/**
 * 主测试函数 - 持续请求直到出现"兑换成功"或"手慢了"
 */
async function main() {
    const scriptStartTime = Date.now();
    console.log('🚀 持续请求脚本 - 直到出现"兑换成功"或"手慢了"');
    console.log('='.repeat(60));
    console.log('⚡ 固定延迟: 100ms');
    console.log('🔄 将持续请求直到返回包中出现"兑换成功"或"手慢了"');
    console.log('⚠️  忽略404、502等HTTP错误，继续重试');
    console.log('='.repeat(60));
    
    // 构建请求参数
    const params = buildExchangeParams();
    
    let attempt = 1;
    let lastResult = null;
    const allTimings = []; // 收集所有请求的耗时信息
    const requestDetails = []; // 收集每次请求的详细信息
    let foundFinalResponse = false; // 是否找到最终响应（兑换成功或手慢了）
    
    // 持续请求直到出现"兑换成功"或"手慢了"
    while (!foundFinalResponse) {
        lastResult = await executeRequest(params, attempt);
        
        // 收集耗时信息和请求详情
        if (lastResult && lastResult.timing) {
            allTimings.push(lastResult.timing);
            requestDetails.push({
                attempt: attempt,
                timing: lastResult.timing,
                result: lastResult.data ? lastResult.data.result : 'ERROR',
                msg: lastResult.data ? lastResult.data.msg : '无响应'
            });
        }
        
        // 检查是否出现最终响应（兑换成功或手慢了）
        if (lastResult && !lastResult.isError && lastResult.data) {
            const msg = lastResult.data.msg;
            if (msg === "兑换成功") {
                console.log('🎉 检测到"兑换成功"响应，停止请求！');
                foundFinalResponse = true;
                break;
            } else if (msg === "手慢啦，优惠券被抢光了") {
                console.log('😞 检测到"手慢了"响应，停止请求！');
                foundFinalResponse = true;
                break;
            } else {
                console.log(`📝 第${attempt}次请求完成，响应: "${msg}"，继续请求...`);
            }
        }
        
        // 无论什么错误都继续重试，固定延迟100ms
        if (!foundFinalResponse) {
            console.log(`⏳ 第${attempt}次请求完成，等待100ms后继续...`);
            await new Promise(resolve => setTimeout(resolve, 100));
        }
        
        // 重新构建参数以更新时间戳
        Object.assign(params, buildExchangeParams());
        attempt++;
    }
    
    // 发送最终结果通知
    if (lastResult) {
        if (lastResult.data && lastResult.data.msg === "兑换成功") {
            console.log('🎉 兑换成功！');
            
            // 生成请求耗时详情
            const timingDetails = generateRequestTimingDetails(requestDetails);
            
            // 发送成功通知到钉钉
            const successMessage = `🎉 积分兑换成功！\n\n` +
                `📊 响应内容：\n${JSON.stringify(lastResult.data, null, 2)}\n\n` +
                `⏰ 时间：${new Date().toLocaleString()}\n` +
                `🔄 总尝试次数：${attempt}\n` +
                `⏱️  最后耗时：${lastResult.timing ? lastResult.timing.totalTime : 0}ms` +
                timingDetails;
            
            await sendDingTalkMessage(successMessage);
        } else if (lastResult.data && lastResult.data.msg === "手慢啦，优惠券被抢光了") {
            console.log('😞 手慢啦！');
            
            // 生成请求耗时详情
            const timingDetails = generateRequestTimingDetails(requestDetails);
            
            const failMessage = `😞 积分兑换失败 - 手慢啦！\n\n` +
                `📊 响应内容：\n${JSON.stringify(lastResult.data, null, 2)}\n\n` +
                `⏰ 时间：${new Date().toLocaleString()}\n` +
                `🔄 总尝试次数：${attempt}\n` +
                `⏱️  最后耗时：${lastResult.timing ? lastResult.timing.totalTime : 0}ms` +
                timingDetails;
            
            await sendDingTalkMessage(failMessage);
        } else if (!lastResult.isError) {
            console.log('😞 请求完成但未检测到最终响应');
            
            // 生成请求耗时详情
            const timingDetails = generateRequestTimingDetails(requestDetails);
            
            const failMessage = `😞 积分兑换失败 - 未检测到最终响应！\n\n` +
                `📊 最后响应内容：\n${JSON.stringify(lastResult.data, null, 2)}\n\n` +
                `⏰ 时间：${new Date().toLocaleString()}\n` +
                `🔄 总尝试次数：${attempt}\n` +
                `⏱️  最后耗时：${lastResult.timing ? lastResult.timing.totalTime : 0}ms` +
                timingDetails;
            
            await sendDingTalkMessage(failMessage);
        }
    } else {
        console.log('😞 无响应数据');
        
        // 生成请求耗时详情
        const timingDetails = generateRequestTimingDetails(requestDetails);
        
        const failMessage = `😞 积分兑换失败 - 无响应！\n\n` +
            `⏰ 时间：${new Date().toLocaleString()}\n` +
            `🔄 总尝试次数：${attempt}` +
            timingDetails;
        
        await sendDingTalkMessage(failMessage);
    }
    
    // 显示性能统计
    const performanceStats = calculatePerformanceStats(allTimings);
    displayPerformanceStats(performanceStats);
    
    const totalScriptTime = Date.now() - scriptStartTime;
    console.log(`\n🏁 脚本执行完成，总耗时: ${totalScriptTime}ms`);
}

// 运行测试
if (require.main === module) {
    main().catch(console.error);
}

module.exports = { main };
