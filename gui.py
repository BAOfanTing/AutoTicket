import sys
from PyQt5.QtWidgets import (QApplication, QWidget, QLabel, QLineEdit, QPushButton,
                             QTextEdit, QVBoxLayout, QHBoxLayout, QGroupBox, QFormLayout,
                             QMessageBox)
<<<<<<< HEAD
from PyQt5.QtCore import QThread, pyqtSignal, QDateTime, Qt
=======
from PyQt5.QtCore import QThread, pyqtSignal, QDateTime, QTimer, Qt
>>>>>>> c1f27e830a6e600b6fde59ce2e969e5c8de75d25
from PyQt5.QtGui import QIcon
import AutoTicket
import time
import json
import os
import updater

APP_STYLESHEET = """
QWidget {
    color: #1d1d1f;
    background: #ffffff;
    font-size: 15px;
}
QWidget#mainWindow {
    background: #ffffff;
}
QLabel {
    background: transparent;
    color: #3a3a3c;
    font-weight: 600;
}
QGroupBox {
    background: #fbfbfd;
    border: 1px solid #e5e5ea;
    border-radius: 18px;
    margin-top: 14px;
    color: #1d1d1f;
    font-weight: 600;
}
QGroupBox::title {
    subcontrol-origin: margin;
    left: 16px;
    padding: 0 6px;
    background: #fbfbfd;
    color: #6e6e73;
}
QLineEdit,
QTextEdit {
    background: #ffffff;
    border: 1px solid #d2d2d7;
    border-radius: 12px;
    padding: 8px 12px;
    selection-background-color: #0a84ff;
    selection-color: #ffffff;
}
QLineEdit:focus,
QTextEdit:focus {
    border: 1px solid #0a84ff;
}
QTextEdit#logPanel {
    color: #1d1d1f;
}
QPushButton {
    background: #f5f5f7;
    border: 1px solid #d2d2d7;
    border-radius: 12px;
    padding: 8px 18px;
    color: #1d1d1f;
    font-weight: 600;
}
QPushButton:hover {
    background: #ededf0;
}
QPushButton:pressed {
    background: #e4e4e8;
}
QPushButton:disabled {
    background: #f7f7f8;
    border: 1px solid #e5e5ea;
    color: #a1a1aa;
}
QPushButton#primaryButton {
    background: #007aff;
    border: 1px solid #007aff;
    color: #ffffff;
    font-weight: 600;
}
QPushButton#primaryButton:hover {
    background: #0a84ff;
    border-color: #0a84ff;
}
QPushButton#primaryButton:pressed {
    background: #0063ce;
    border-color: #0063ce;
}
QPushButton#primaryButton:disabled {
    background: #bcdcff;
    border-color: #bcdcff;
    color: #ffffff;
}
QPushButton#stopButton {
    background: #fff5f4;
    border: 1px solid #ffd5d2;
    color: #ff3b30;
    font-weight: 600;
}
QPushButton#stopButton:hover {
    background: #ffeceb;
}
QPushButton#stopButton:pressed {
    background: #ffe1df;
}
"""

# pyinstaller --onefile --windowed --icon=./icon.ico -n AutoTicket gui.py
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

    def run(self):
        try:
            from datetime import datetime

            AutoTicket.set_log_callback(self.log_signal.emit)
            AutoTicket.LOGIN_NAME_PLAINTEXT = self.login_name
            AutoTicket.USER_ID_PLAINTEXT = self.login_name
            AutoTicket.SES_ID = self.ses_id
            AutoTicket.EXCHANGE_ID_PLAINTEXT = self.exchange_id

            run_time = datetime.strptime(self.run_time_str, "%Y-%m-%d %H:%M:%S")
            AutoTicket.RUN_TIME = run_time
            AutoTicket.RUN_COUNT = self.run_count
            AutoTicket.timeSleep = self.time_sleep

            self.log_signal.emit(f"程序已启动，将在 {run_time} 执行兑换任务，共执行 {self.run_count} 次。")

            self.wait_until_target(run_time)
            if self.running:
                AutoTicket.job()
        except Exception as e:
            self.log_signal.emit(f"任务执行出错: {str(e)}")
        finally:
            AutoTicket.set_log_callback(None)
            self.finished_signal.emit()

    def wait_until_target(self, run_time):
        from datetime import datetime

        while self.running:
            now = datetime.now()
            if now >= run_time:
                return

            diff = (run_time - now).total_seconds()
            if diff > 3600:
                sleep_time = min(300, diff)
            elif diff > 600:
                sleep_time = min(60, diff)
            elif diff > 60:
                sleep_time = min(30, diff)
            elif diff > 1:
                sleep_time = min(0.5, diff)
            else:
                sleep_time = min(0.05, diff)

            time.sleep(max(sleep_time, 0.01))

    def stop(self):
        self.running = False

class DailyTaskWorker(QThread):
    log_signal = pyqtSignal(str)
    finished_signal = pyqtSignal()

    def __init__(self, login_name, ses_id, exchange_id):
        super().__init__()
        self.login_name = login_name
        self.ses_id = ses_id
        self.exchange_id = exchange_id

    def run(self):
        try:
            AutoTicket.LOGIN_NAME_PLAINTEXT = self.login_name
            AutoTicket.USER_ID_PLAINTEXT = self.login_name
            AutoTicket.SES_ID = self.ses_id
            AutoTicket.EXCHANGE_ID_PLAINTEXT = self.exchange_id
            AutoTicket.set_log_callback(self.log_signal.emit)
            AutoTicket.daily_task_workflow()
        except Exception as e:
            self.log_signal.emit(f"执行每日任务时出错: {str(e)}")
        finally:
            AutoTicket.set_log_callback(None)
            self.finished_signal.emit()

class MainWindow(QWidget):
    def __init__(self):
        super().__init__()
        self.worker = None
        self.daily_task_worker = None
        self.stop_requested = False
        self.init_ui()
        self.config_file = "./config.json"  # 配置文件路径
        self.load_config()  # 加载配置文件

        # 检查更新
        self.check_update()

    def init_ui(self):
        self.setObjectName("mainWindow")
        self.setWindowTitle(f'AutoTicket {updater.CURRENT_VERSION} - 免费开源使用')
        self.setWindowIcon(QIcon(os.path.join(os.path.dirname(__file__), "icon.ico")))
        self.setGeometry(100, 100, 820, 720)
        self.setMinimumSize(760, 660)

        # 创建配置区域
        config_group = QGroupBox("配置参数")
        config_layout = QFormLayout()
        config_layout.setHorizontalSpacing(18)
        config_layout.setVerticalSpacing(14)
        config_layout.setContentsMargins(20, 26, 20, 20)
        config_layout.setLabelAlignment(Qt.AlignRight | Qt.AlignVCenter)

        self.login_name_edit = QLineEdit(AutoTicket.LOGIN_NAME_PLAINTEXT)
        self.ses_id_edit = QLineEdit(AutoTicket.SES_ID)
        self.exchange_id_edit = QLineEdit(AutoTicket.EXCHANGE_ID_PLAINTEXT)

        # 设置默认时间，但允许用户手动修改
        default_time = self.get_next_run_time()
        self.run_time_edit = QLineEdit(default_time)
        self.run_count_edit = QLineEdit(str(AutoTicket.RUN_COUNT))
        self.time_sleep_edit = QLineEdit(str(AutoTicket.timeSleep))

        self.login_name_edit.setPlaceholderText("请输入 LOGIN_NAME / USER_ID")
        self.ses_id_edit.setPlaceholderText("请输入 SES_ID")
        self.exchange_id_edit.setPlaceholderText("例如 9 / 10 / 11")
        self.run_time_edit.setPlaceholderText("YYYY-MM-DD HH:MM:SS")
        self.run_count_edit.setPlaceholderText("请输入运行次数")
        self.time_sleep_edit.setPlaceholderText("请输入运行间隔")

        for line_edit in [
            self.login_name_edit,
            self.ses_id_edit,
            self.exchange_id_edit,
            self.run_time_edit,
            self.run_count_edit,
            self.time_sleep_edit,
        ]:
            line_edit.setMinimumHeight(46)

        config_layout.addRow(QLabel("LOGIN_NAME / USER_ID"), self.login_name_edit)
        config_layout.addRow(QLabel("SES_ID"), self.ses_id_edit)
        config_layout.addRow(QLabel("EXCHANGE_ID（9=2块 / 10=4块 / 11=6块）"), self.exchange_id_edit)
        config_layout.addRow(QLabel("抢票时间"), self.run_time_edit)
        config_layout.addRow(QLabel("运行次数"), self.run_count_edit)
        config_layout.addRow(QLabel("运行间隔"), self.time_sleep_edit)

        config_group.setLayout(config_layout)

        # 创建按钮区域
        button_layout = QHBoxLayout()
        button_layout.setSpacing(12)
        self.start_button = QPushButton("启动")
        self.stop_button = QPushButton("停止")
        self.daily_task_button = QPushButton("执行每日任务")
        self.github_button = QPushButton("GitHub")
        self.start_button.setObjectName("primaryButton")
        self.stop_button.setObjectName("stopButton")
        self.stop_button.setEnabled(False)

        for button in [self.start_button, self.stop_button, self.daily_task_button, self.github_button]:
            button.setMinimumHeight(48)

        button_layout.addWidget(self.start_button)
        button_layout.addWidget(self.stop_button)
        button_layout.addWidget(self.daily_task_button)
        button_layout.addWidget(self.github_button)

        # 创建日志显示区域
        log_group = QGroupBox("运行日志")
        log_layout = QVBoxLayout()
        log_layout.setContentsMargins(20, 26, 20, 20)
        log_layout.setSpacing(12)
        self.log_display = QTextEdit()
        self.log_display.setObjectName("logPanel")
        self.log_display.setReadOnly(True)
        self.log_display.setMinimumHeight(220)
        log_layout.addWidget(self.log_display)
        log_group.setLayout(log_layout)

        # 主布局
        main_layout = QVBoxLayout()
        main_layout.setContentsMargins(24, 24, 24, 24)
        main_layout.setSpacing(16)
        main_layout.addWidget(config_group)
        main_layout.addLayout(button_layout)
        main_layout.addWidget(log_group)
        self.setLayout(main_layout)

        # 连接信号和槽
        self.start_button.clicked.connect(self.start_program)
        self.stop_button.clicked.connect(self.stop_program)
        self.daily_task_button.clicked.connect(self.execute_daily_task)
        self.github_button.clicked.connect(self.open_github)

        #输入后保存ses_id和login_name
        self.login_name_edit.textChanged.connect(self.save_config)
        self.ses_id_edit.textChanged.connect(self.save_config)
        self.exchange_id_edit.textChanged.connect(self.save_config)
        self.run_count_edit.textChanged.connect(self.save_config)
        self.time_sleep_edit.textChanged.connect(self.save_config)

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
        
        self.stop_requested = False
        self.worker = Worker(login_name, ses_id, exchange_id, run_time_str, run_count, time_sleep)
        self.worker.log_signal.connect(self.update_log)
        self.worker.finished_signal.connect(self.program_finished)
        self.worker.start()
        
        self.start_button.setEnabled(False)
        self.stop_button.setEnabled(True)
        self.update_log("程序启动中...")
        
    def stop_program(self):
        if self.worker:
            self.stop_requested = True
            self.worker.stop()
            self.worker = None
        self.start_button.setEnabled(True)
        self.stop_button.setEnabled(False)
        self.update_log("程序已停止")
        
    def execute_daily_task(self):
        """执行每日任务：登录→3次签到→评论→查询积分"""
        login_name = self.login_name_edit.text()
        ses_id = self.ses_id_edit.text()
        exchange_id = self.exchange_id_edit.text()

        if not all([login_name, ses_id]):
            QMessageBox.warning(self, "输入错误", "LOGIN_NAME和SES_ID字段必须填写！")
            return

        self.start_button.setEnabled(False)
        self.stop_button.setEnabled(False)
        self.daily_task_button.setEnabled(False)

        self.daily_task_worker = DailyTaskWorker(login_name, ses_id, exchange_id)
        self.daily_task_worker.log_signal.connect(self.update_log)
        self.daily_task_worker.finished_signal.connect(self.daily_task_finished)
        self.daily_task_worker.start()

    def daily_task_finished(self):
        self.start_button.setEnabled(True)
        self.stop_button.setEnabled(False)
        self.daily_task_button.setEnabled(True)
        self.update_log("每日任务执行完成")
        self.daily_task_worker = None
        
    def update_log(self, message):
        timestamp = QDateTime.currentDateTime().toString("yyyy-MM-dd hh:mm:ss")
        self.log_display.append(f"[{timestamp}] {message}")
        
    def program_finished(self):
        self.start_button.setEnabled(True)
        self.stop_button.setEnabled(False)
        if not self.stop_requested:
            self.update_log("程序执行完成")
        self.stop_requested = False
        self.worker = None

    def save_config(self):
        #保存配置文件
        config = {
            "login_name":self.login_name_edit.text(),
            "ses_id":self.ses_id_edit.text(),
            "exchange_id":self.exchange_id_edit.text(),
            "run_count":self.run_count_edit.text(),
            "time_sleep":self.time_sleep_edit.text(),
        }
        with open(self.config_file, 'w') as f:
            json.dump(config, f, indent=4)
    
    def open_github(self):
        import webbrowser
        # 打开项目的GitHub页面
        github_url = "https://github.com/BAOfanTing/AutoTicket"
        webbrowser.open(github_url)
    
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
                if "exchange_id" in config:
                    self.exchange_id_edit.setText(config["exchange_id"])
                if "run_count" in config:
                    self.run_count_edit.setText(config["run_count"])
                if "time_sleep" in config:
                    self.time_sleep_edit.setText(config["time_sleep"])

    def get_next_run_time(self):
        """
        获取下一个运行时间点
        规则：
        1. 如果当前时间在7:00之前，选择当天的7:00
        2. 如果当前时间在7:00到11:30之间，选择11:30
        3. 如果当前时间在11:30到17:00之间，选择17:00
        4. 如果当前时间超过17:00，选择第二天的7:00
        """
        from datetime import datetime, timedelta
        
        now = datetime.now()
        today = now.date()
        
        # 定义时间点
        time_07_00 = datetime.combine(today, datetime.strptime("07:00", "%H:%M").time())
        time_11_30 = datetime.combine(today, datetime.strptime("11:30", "%H:%M").time())
        time_17_00 = datetime.combine(today, datetime.strptime("17:00", "%H:%M").time())
        time_07_00_tomorrow = datetime.combine(today + timedelta(days=1), datetime.strptime("07:00", "%H:%M").time())
        
        # 根据当前时间选择最近的时间点
        if now < time_07_00:
            next_time = time_07_00
        elif now < time_11_30:
            next_time = time_11_30
        elif now < time_17_00:
            next_time = time_17_00
        else:
            next_time = time_07_00_tomorrow
            
        return next_time.strftime("%Y-%m-%d %H:%M:%S")

    def check_update(self):
        """
        检查更新
        :return: None
        """
        try:
            server_url = "https://gitee.com/baofanting/auto-ticket/raw/master/AutoTicket_update_info.json"
            def update_callback(has_update, latest_version, download_url, message):
                try:
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
                except Exception as e:
                    self.update_log(f"处理更新结果时出错: {str(e)}")
            
            self.update_log("正在检查更新...")
            # 创建更新检查线程
            self.updater = updater.UpdateChecker(server_url)
            self.updater.sig_update.connect(update_callback)
            self.updater.start()
        except Exception as e:
            self.update_log(f"检查更新时出错: {str(e)}")


if __name__ == '__main__':
    app = QApplication(sys.argv)
    app.setStyle("Fusion")
    app.setStyleSheet(APP_STYLESHEET)
    window = MainWindow()
    window.show()
    sys.exit(app.exec_())