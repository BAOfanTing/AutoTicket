

免责声明：详见MIT License，此仓库仅用于个人参考学习，但如他人用本仓库代码用于商业用途，侵犯到杭工e家等，本人不承担任何责任。

# 运行流程

打开模拟器按下边操作,得到自己的`SES_ID`,`LOGIN_NAME_PLAINTEXT`   ,下载软件打开填入,修改时间运行

# 1 模拟器配置

下载雷电模拟器https://www.ldmnq.com/#page2,打开雷电模拟器设置--其他设置--开启root权限

![image-20250909151940755](https://gitee.com/baofanting/image/raw/master/image/20250909153108151.png)

安装杭工e家app和Mt管理器

![image-20250909151957442](https://gitee.com/baofanting/image/raw/master/image/20250909153108152.png)

# 2 `login_name`,`ses_id`获取

在模拟器上登录杭工e家,登录后点开积分优享,且界面加载

![image-20250909151841700](https://gitee.com/baofanting/image/raw/master/image/20250909153108153.png)

`mt管理器`打开路径 `/data/data/com.zjte.hanggongefamily/app_webview/Default/Local Storage/leveldb/`能够看到有个log文件,他就是我们需要的

![image-20250909152040902](https://gitee.com/baofanting/image/raw/master/image/20250909153108155.png)

打开滑动到最下边,复制最后的 `login_name`,`ses_id`,填入程序

![image-20250909152355655](https://gitee.com/baofanting/image/raw/master/image/20250909153108156.png)



双击运行软件,填入信息,修改时间运行,出现手慢优惠券没了,说明正确.  修改为抢票时间点击启动等待即可

![image-20250909152433677](https://gitee.com/baofanting/image/raw/master/image/20250909153108157.png)

## 注意事项

你在手机登录杭工e家后,模拟器就会退出登录,需要重新登录,点击积分兑换界面,这样本地才能更新ses_id,此时再打开log获取

**## Star History**

[![Star History Chart](./image/AutoTicket&type=Date.svg+xml)
