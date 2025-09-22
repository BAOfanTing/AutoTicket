/**
 * 钉钉机器人配置文件
 * 请根据您的钉钉机器人信息修改以下配置
 */

module.exports = {
    // 钉钉机器人webhook地址
    // 获取方式：在钉钉群中添加自定义机器人，复制webhook地址
    webhook: 'https://oapi.dingtalk.com/robot/send?access_token=3b3e502e26ddfe0069af0ace7cb39cae686c162191e6dd87bee9a96b6f8c6564',
    
    // 钉钉机器人加签密钥
    // 获取方式：在创建机器人时选择"加签"安全设置，复制密钥
    secret: 'SEC3e1c2e70ab06c2368f3791b8b6df3071919a933ba8ae72524297c7111a28c98b',
    
    // 重试配置
    maxRetries: 10,       // 最大重试次数（增加重试次数应对网络错误）
    retryDelay: 500,      // 重试间隔(毫秒)（稍微增加间隔）
    
    // 是否启用钉钉推送（设为false可禁用推送进行测试）
    enabled: true
};
