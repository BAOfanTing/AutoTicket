import requests
import json
from PyQt5.QtCore import QThread, pyqtSignal
import sys
import os

# 当前版本号
CURRENT_VERSION = "1.0.3"

class UpdateChecker(QThread):
    #定义信号,用于向主线程发送检查结果
    # (是否有更新,最新版本号,下载链接,更新信息)
    sig_update = pyqtSignal(bool, str, str, str)
    
    def __init__(self, server_url):
        super().__init__()
        self.server_url = server_url

    def run(self):
        try:
            # 首先尝试HTTPS连接
            response = requests.get(self.server_url, timeout=10)
            response.raise_for_status()  # 检查请求是否成功
            # 解析服务器响应
            data = response.json()
            print(data)
            latest_version = data.get("version")
            download_url = data.get("download_url")
            if self.is_newer_version(latest_version, CURRENT_VERSION):
                self.sig_update.emit(True, latest_version, download_url, "有最新版本!")
            else:
                self.sig_update.emit(False, latest_version, "", "无更新")
        except requests.exceptions.SSLError as e:
            # SSL错误处理
            print(f"SSL连接失败: {e}")
            self.sig_update.emit(False, "", "", f"SSL连接失败: {str(e)}")
        except requests.exceptions.RequestException as e:
            # 其他网络请求错误
            print(f"网络请求失败: {e}")
            self.sig_update.emit(False, "", "", f"网络请求失败: {str(e)}")
        except json.JSONDecodeError as e:
            # JSON解析错误
            print(f"JSON解析失败: {e}")
            self.sig_update.emit(False, "", "", f"JSON解析失败: {str(e)}")
        except Exception as e:
            # 其他未知错误
            print(f"检查更新时发生未知错误: {e}")
            self.sig_update.emit(False, "", "", f"检查更新时发生未知错误: {str(e)}")

    def is_newer_version(self, latest_version, current_version):
        """
        比较版本号,判断是否有更新
        :param latest_version: 最新版本号
        :param current_version: 当前版本号
        :return: 如果有更新,返回True;否则返回False
        """
        try:
            # 处理版本号段数不一致的情况
            latest_parts = [int(x) for x in latest_version.split(".")]
            current_parts = [int(x) for x in current_version.split(".")]
            
            # 补齐版本号长度
            while len(latest_parts) < len(current_parts):
                latest_parts.append(0)
            while len(current_parts) < len(latest_parts):
                current_parts.append(0)
                
            for i in range(len(latest_parts)):
                if latest_parts[i] > current_parts[i]:
                    return True
                elif latest_parts[i] < current_parts[i]:
                    return False
            return False
        except Exception:
            # 版本号格式错误时，返回False
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
    server_url = "https://gitee.com/baofanting/auto-ticket/raw/master/AutoTicket_update_info.json"
    checker = check_for_updates(server_url, update_callback)

