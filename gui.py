import sys
from PyQt5.QtWidgets import (QApplication, QWidget, QLabel, QLineEdit, QPushButton, 
                             QTextEdit, QVBoxLayout, QHBoxLayout, QGroupBox, QFormLayout,
                             QMessageBox)
from PyQt5.QtCore import QThread, pyqtSignal, QDateTime, QTimer
import AutoTicket
import time
import threading
import json
import os
import updater

class Worker(QThread):
    log_signal = pyqtSignal(str)
    finished_signal = pyqtSignal()

    def __init__(self, login_name, ses_id, exchange_id, run_time_str, run_count, time_sleep):
        super().__init__()
        self.login_name = login_name
        self.user_id = login_name  # user_id与login_name相同
        self.ses_id = ses_id
        self.exchange_id = exchange_id
        self.run_time_str = run_time_str
        self.run_count = int(run_count)
        self.time_sleep = float(time_sleep)
        self.running = True
        self.timer = None

    # 在Worker类的run方法中添加日志重定向
    def run(self):
        try:
            # 设置日志回调
            AutoTicket.set_log_callback(self.log_signal.emit)
            
            # 更新AutoTicket模块中的全局变量
            AutoTicket.LOGIN_NAME_PLAINTEXT = self.login_name
            AutoTicket.USER_ID_PLAINTEXT = self.login_name
            AutoTicket.SES_ID = self.ses_id
            AutoTicket.EXCHANGE_ID_PLAINTEXT = self.exchange_id
            
            # 解析运行时间字符串
            from datetime import datetime
            run_time = datetime.strptime(self.run_time_str, "%Y-%m-%d %H:%M:%S")
            AutoTicket.RUN_TIME = run_time
            AutoTicket.RUN_COUNT = self.run_count
            AutoTicket.timeSleep = self.time_sleep

            self.log_signal.emit(f"程序已启动，将在 {run_time} 执行兑换任务，共执行 {self.run_count} 次。")
            
            # 在单独的线程中运行任务
            self.task_thread = threading.Thread(target=self.run_task)
            self.task_thread.start()
            
        except Exception as e:
            self.log_signal.emit(f"发生错误: {str(e)}")
            self.finished_signal.emit()

    def run_task(self):
        try:
            # 确保日志回调设置正确
            AutoTicket.set_log_callback(self.log_signal.emit)
            AutoTicket.wait_until_target()
            if self.running:
                AutoTicket.job()
        except Exception as e:
            self.log_signal.emit(f"任务执行出错: {str(e)}")
        finally:
            # 清除日志回调
            AutoTicket.set_log_callback(None)
            self.finished_signal.emit()

    def stop(self):
        self.running = False
        if self.timer:
            self.timer.cancel()
        self.quit()
        self.wait()

class MainWindow(QWidget):
    def __init__(self):
        super().__init__()
        self.worker = None
        self.init_ui()
        self.config_file = "./config.json"  # 配置文件路径
        self.load_config()  # 加载配置文件

        # 检查更新
        self.check_update()

    def init_ui(self):
        self.setWindowTitle(f'AutoTicket {updater.CURRENT_VERSION} --by bft')
        self.setGeometry(100, 100, 600, 500)

        # 创建配置区域
        config_group = QGroupBox("配置参数")
        config_layout = QFormLayout()
        
        self.login_name_edit = QLineEdit(AutoTicket.LOGIN_NAME_PLAINTEXT)
        self.ses_id_edit = QLineEdit(AutoTicket.SES_ID)
        self.exchange_id_edit = QLineEdit(AutoTicket.EXCHANGE_ID_PLAINTEXT)
        self.run_time_edit = QLineEdit(QDateTime.currentDateTime().toString("yyyy-MM-dd hh:mm:ss"))
        self.run_count_edit = QLineEdit(str(AutoTicket.RUN_COUNT))
        self.time_sleep_edit = QLineEdit(str(AutoTicket.timeSleep))
        
        config_layout.addRow(QLabel("LOGIN_NAME/USER_ID:"), self.login_name_edit)
        config_layout.addRow(QLabel("SES_ID:"), self.ses_id_edit)
        config_layout.addRow(QLabel("EXCHANGE_ID:#9是2块,10是4块,11是6块"), self.exchange_id_edit)
        config_layout.addRow(QLabel("抢票时间"), self.run_time_edit)
        config_layout.addRow(QLabel("运行次数:"), self.run_count_edit)
        config_layout.addRow(QLabel("运行间隔:"), self.time_sleep_edit)
        
        config_group.setLayout(config_layout)

        # 创建按钮区域
        button_layout = QHBoxLayout()
        self.start_button = QPushButton("启动")
        self.stop_button = QPushButton("停止")
        self.stop_button.setEnabled(False)
        button_layout.addWidget(self.start_button)
        button_layout.addWidget(self.stop_button)

        # 创建日志显示区域
        self.log_display = QTextEdit()
        self.log_display.setReadOnly(True)

        # 主布局
        main_layout = QVBoxLayout()
        main_layout.addWidget(config_group)
        main_layout.addLayout(button_layout)
        main_layout.addWidget(QLabel("运行日志:"))
        main_layout.addWidget(self.log_display)
        self.setLayout(main_layout)

        # 连接信号和槽
        self.start_button.clicked.connect(self.start_program)
        self.stop_button.clicked.connect(self.stop_program)

        #输入后保存ses_id和login_name
        self.login_name_edit.textChanged.connect(self.save_config)
        self.ses_id_edit.textChanged.connect(self.save_config)

    def start_program(self):
        login_name = self.login_name_edit.text()
        ses_id = self.ses_id_edit.text()
        exchange_id = self.exchange_id_edit.text()
        run_time_str = self.run_time_edit.text()
        run_count = self.run_count_edit.text()
        time_sleep = self.time_sleep_edit.text()
        
        # 验证输入
        if not all([login_name, ses_id, exchange_id, run_time_str, run_count, time_sleep]):
            QMessageBox.warning(self, "输入错误", "所有字段都必须填写！")
            return
            
        try:
            int(run_count)
            float(time_sleep)
            from datetime import datetime
            datetime.strptime(run_time_str, "%Y-%m-%d %H:%M:%S")
        except ValueError:
            QMessageBox.warning(self, "输入错误", "RUN_COUNT 和 timeSleep 必须是数字，RUN_TIME 格式必须正确！")
            return
        
        self.worker = Worker(login_name, ses_id, exchange_id, run_time_str, run_count, time_sleep)      
        self.worker.log_signal.connect(self.update_log)
        self.worker.finished_signal.connect(self.program_finished)
        self.worker.start()
        
        self.start_button.setEnabled(False)
        self.stop_button.setEnabled(True)
        self.update_log("程序启动中...")
        
    def stop_program(self):
        if self.worker:
            self.worker.stop()
            self.worker = None
        self.start_button.setEnabled(True)
        self.stop_button.setEnabled(False)
        self.update_log("程序已停止")
        
    def update_log(self, message):
        timestamp = QDateTime.currentDateTime().toString("yyyy-MM-dd hh:mm:ss")
        self.log_display.append(f"[{timestamp}] {message}")
        
    def program_finished(self):
        self.start_button.setEnabled(True)
        self.stop_button.setEnabled(False)
        self.update_log("程序执行完成")

    def save_config(self):
        #保存配置文件
        config = {
            "login_name":self.login_name_edit.text(),
            "ses_id":self.ses_id_edit.text()
        }
        with open(self.config_file, 'w') as f:
            json.dump(config, f, indent=4)
    
    def load_config(self):
        "从文件中加载"
        if os.path.exists(self.config_file):
            with open(self.config_file,encoding='utf-8') as f:
                config = json.load(f)
                # 更新界面中的值
                if "login_name" in config:
                    self.login_name_edit.setText(config["login_name"])
                if "ses_id" in config:
                    self.ses_id_edit.setText(config["ses_id"])

    def check_update(self):
        """
        检查更新
        :return: None
        """
        server_url = "https://gitee.com/baofanting/auto-ticket/raw/master/AutoTicket_update_info.json"
        def update_callback(has_update, latest_version, download_url, message):
            if has_update:
                self.update_log(f"发现新版本 {latest_version}")
                # 显示更新提示对话框
                reply = QMessageBox.information(
                    self, 
                    "发现新版本", 
                    f"发现新版本 {latest_version}\n\n是否前往下载？",
                    QMessageBox.Yes | QMessageBox.No
                )
                if reply == QMessageBox.Yes:
                    # 这里可以打开浏览器下载新版本
                    import webbrowser
                    webbrowser.open(download_url)
            else:
                self.update_log("当前已是最新版本")
        
        
        self.update_log("正在检查更新...")
        # 创建更新检查线程
        self.updater = updater.UpdateChecker(server_url)
        self.updater.sig_update.connect(update_callback)
        self.updater.start()


if __name__ == '__main__':
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec_())