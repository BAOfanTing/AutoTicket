/**
 * 工作流配置文件
 * 包含所有请求的公共字段和配置
 */

// 获取用户ID（与login_name相同）
function getUserId() {
    return "此处填写加密后的用户名";
}
//  获取会话ID 
function getSesId() {
    return "此处填写会话ID";
}
module.exports = {
    // 基础配置
    baseUrl: 'https://app.hzgh.org.cn',
    
    // 公共请求字段
    commonFields: {
        channel: "02",
        app_ver_no: "3.1.4",
        login_name: getUserId(),
        ses_id: getSesId()
    },
    
    // Cookie配置
    cookies: {
        'JSESSIONID': '406CD683439BDFEC843C6C3A5C928504',
        'SERVERID': '12240fdeb12bd990da3bbf786eeeee2f|1758383252|1758382894'
    },
    
    // HTTP请求头配置
    headers: {
        'Host': 'app.hzgh.org.cn',
        'Content-Type': 'text/plain;charset=utf-8',
        'Connection': 'Keep-Alive',
        'User-Agent': 'okhttp/3.4.2'
    },
    
    // API端点配置
    endpoints: {
        login: '/unionApp/interf/front/U/U042',
        signin: '/unionApp/interf/front/U/U042',
        comment: '/unionApp/interf/front/AC/AC08',
        query: '/unionApp/interf/front/U/U005',
        exchange: '/unionApp/interf/front/OL/OL41'  // 兑换优惠券接口
    },
    
    // 功能特定参数
    functions: {
        // 登录签到参数
        login: {
            type: "1"
        },
        
        // 日常签到参数
        signin: {
            type: "5"
        },
        
        // 评论参数，默认评论是"好"，如需修改，请修改content字段
        comment: {
            related_id: "1232",
            content_type: "1",
            oper_type: "0",
            suffix: "png",
            content: "好"
        },
        
        // 查询积分参数（无额外参数）
        query: {},
        
        // 兑换优惠券参数，默认兑换4块的优惠券，如需修改，请修改exchange_id字段，9是2块，10是4块，11是6块
        exchange: {
            user_id: getUserId(),
            exchange_id: "10"
        }
    },
    
    // 请求配置
    request: {
        timeout: 5000,
        retryDelay: 1000
    },
    
    // 导出工具函数
    getUserId: getUserId,
    getSesId: getSesId
};
