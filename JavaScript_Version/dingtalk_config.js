/**
 * 钉钉机器人配置文件
 * 请根据您的钉钉机器人信息修改以下配置
 */

module.exports = {
    // 钉钉机器人webhook地址
    // 获取方式：在钉钉群中添加自定义机器人，复制webhook地址
    webhook: 'https://oapi.dingtalk.com/robot/send?access_token=此处填写你的webhook地址token',
    
    // 钉钉机器人加签密钥
    // 获取方式：在创建机器人时选择"加签"安全设置，复制密钥
    secret: 'SEC此处填写你的加签密钥',
    
    // 不再使用重试配置
    // maxRetries: 10,       // 最大重试次数（增加重试次数应对网络错误）
    // retryDelay: 500,      // 重试间隔(毫秒)（稍微增加间隔）
    
    // 是否启用钉钉推送（设为false可禁用推送进行测试）
    enabled: true
};
