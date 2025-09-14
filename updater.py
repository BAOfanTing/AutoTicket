import requests
import json
from PyQt5.QtCore import QThread, pyqtSignal
import sys
import os

# 当前版本号
CURRENT_VERSION = "1.0.3"

class UpdateChecker(QThread):
    #定义信号,用于向主线程发送检查结果
    sig_update = pyqtSignal(bool,str,str,str)  #(是否有更新,最新版本号,更新日志)
    def __init__(self,server_url):
        super().__init__()
        self.server_url = server_url

    def run(self):
        response = requests.get(self.server_url)
        response.raise_for_status()  # 检查请求是否成功
        # 解析服务器响应
        data = response.json()
        print(data)
        latest_version = data.get("version")
        download_url = data.get("download_url")
        if self.is_newer_version(latest_version,CURRENT_VERSION):
            self.sig_update.emit(True,latest_version,download_url,"有最新版本!")
        else:
            self.sig_update.emit(False,latest_version,"","无更新")

    def is_newer_version(self,latest_version,current_version):
        """
        比较版本号,判断是否有更新
        :param latest_verision: 最新版本号
        :param current_verision: 当前版本号
        :return: 如果有更新,返回True;否则返回False
        """
        latest_parts = latest_version.split(".")
        current_parts = current_version.split(".")
        for i in range(len(latest_parts)):
            if int(latest_parts[i]) > int(current_parts[i]):
                return True
            elif int(latest_parts[i]) < int(current_parts[i]):
                return False
        return False

def check_for_updates(server_url, callback):
    """
    检查更新的便捷函数
    
    Args:
        server_url (str): 服务器更新信息地址
        callback (function): 回调函数，接收四个参数：
            - has_update (bool): 是否有更新
            - latest_version (str): 最新版本号
            - download_url (str): 下载链接
            - message (str): 更新信息
    """
    def handle_result(has_update, latest_version, download_url, message):
        callback(has_update, latest_version, download_url, message)
    
    # 创建更新检查线程
    updater = UpdateChecker(server_url)
    updater.sig_update.connect(handle_result)
    updater.start()
    
    # 返回线程对象，以便调用者可以管理它
    return updater


# 示例用法（如果直接运行此脚本）
if __name__ == "__main__":
    # 示例：如何使用更新检查功能
    def update_callback(has_update, latest_version, download_url, message):
        if has_update:
            print(f"发现新版本: {latest_version}")
            print(f"更新内容: {message}")
            print(f"下载地址: {download_url}")
        else:
            print("当前已是最新版本")
    
    # 请替换为您的服务器地址
    server_url = "https://gitee.com/baofanting/auto-ticket/blob/master/AutoTicket_update_info.json"
    checker = check_for_updates(server_url, update_callback)

