import sys
from PyQt5.QtWidgets import (QApplication, QWidget, QLabel, QLineEdit, QPushButton,
                             QTextEdit, QVBoxLayout, QHBoxLayout, QGroupBox, QFormLayout,
                             QMessageBox, QDialog, QDialogButtonBox, QFrame)
from PyQt5.QtCore import QThread, pyqtSignal, QDateTime, QTimer, Qt
from PyQt5.QtGui import QIcon, QPixmap, QImage
import AutoTicket
import Login
import time
import json
import os
import updater
import qrcode
from PIL import Image
import io
# pyinstaller --onefile --windowed --icon=./icon.ico -n AutoTicket gui.py
APP_STYLESHEET = """
QWidget {
    color: #1d1d1f;
    background: #ffffff;
    font-size: 17px;
    font-family: "SF Pro Display", "SF Pro Text", "PingFang SC", "Hiragino Sans GB", "Helvetica Neue", "Microsoft YaHei UI", "Microsoft YaHei", sans-serif;
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
QPushButton#qrButton {
    background: #1f9d55;
    border: 1px solid #1f9d55;
    color: #ffffff;
    font-weight: 600;
}
QPushButton#qrButton:hover {
    background: #28a85e;
    border-color: #28a85e;
}
QPushButton#qrButton:pressed {
    background: #198a49;
    border-color: #198a49;
}
QPushButton#qrButton:disabled {
    background: #b8e0c5;
    border-color: #b8e0c5;
    color: #ffffff;
}
"""

class LoginDialog(QDialog):
    def __init__(self, captcha_data, parent=None):
        super().__init__(parent)
        self.setWindowTitle("账号登录")
        self.setModal(True)
        self.setMinimumWidth(400)
        self.captcha_data = captcha_data
        self.sms_countdown_sec = 0
        self.sms_timer = QTimer(self)
        self.sms_timer.timeout.connect(self._on_sms_timer)

        layout = QVBoxLayout()
        layout.setSpacing(12)

        # 登录方式切换
        mode_layout = QHBoxLayout()
        self.btn_password_mode = QPushButton("密码登录")
        self.btn_sms_mode = QPushButton("短信验证码登录")
        for btn in [self.btn_password_mode, self.btn_sms_mode]:
            btn.setCheckable(True)
            btn.setMinimumHeight(38)
            btn.setStyleSheet(
                "QPushButton { border: 1px solid #d2d2d7; border-radius: 8px; background: #f5f5f7; color: #6e6e73; font-weight: 600; }"
                "QPushButton:checked { background: #007aff; color: #fff; border-color: #007aff; }"
            )
        self.btn_password_mode.setChecked(True)
        mode_layout.addWidget(self.btn_password_mode)
        mode_layout.addWidget(self.btn_sms_mode)
        layout.addLayout(mode_layout)

        form_layout = QFormLayout()
        self.form_layout = form_layout  # 供 _switch_mode 使用
        form_layout.setHorizontalSpacing(18)
        form_layout.setVerticalSpacing(14)

        # 手机号（共用）
        self.phone_edit = QLineEdit()
        self.phone_edit.setPlaceholderText("请输入手机号")

        # 密码（密码模式）
        self.password_edit = QLineEdit()
        self.password_edit.setPlaceholderText("请输入密码")
        self.password_edit.setEchoMode(QLineEdit.Password)

        # 图形验证码
        self.captcha_label = QLabel()
        self.captcha_label.setAlignment(Qt.AlignCenter)
        self.captcha_label.setMinimumHeight(100)
        self.captcha_label.setStyleSheet("border: 1px solid #d2d2d7; border-radius: 12px; background: #ffffff;")
        captcha_bytes = Login.decode_captcha_image(captcha_data)
        pixmap = QPixmap()
        pixmap.loadFromData(captcha_bytes)
        self.captcha_label.setPixmap(pixmap)

        self.captcha_edit = QLineEdit()
        self.captcha_edit.setPlaceholderText("请输入图形验证码")

        # 短信验证码（短信模式）
        self.sms_code_edit = QLineEdit()
        self.sms_code_edit.setPlaceholderText("请输入短信验证码")
        self.btn_send_sms = QPushButton("获取验证码")
        self.btn_send_sms.setMinimumHeight(42)
        self.btn_send_sms.setStyleSheet(
            "QPushButton { background: #007aff; color: #fff; border: 1px solid #007aff; border-radius: 8px; font-weight: 600; }"
            "QPushButton:disabled { background: #bcdcff; border-color: #bcdcff; }"
        )

        sms_row = QHBoxLayout()
        sms_row.addWidget(self.sms_code_edit, 1)
        sms_row.addWidget(self.btn_send_sms)

        for line_edit in [self.phone_edit, self.password_edit, self.captcha_edit, self.sms_code_edit]:
            line_edit.setMinimumHeight(42)

        form_layout.addRow(QLabel("手机号"), self.phone_edit)
        form_layout.addRow(QLabel("密码"), self.password_edit)
        form_layout.addRow(QLabel("验证码"), self.captcha_label)
        form_layout.addRow(QLabel("输入验证码"), self.captcha_edit)
        form_layout.addRow(QLabel("短信验证码"), sms_row)

        button_box = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        button_box.accepted.connect(self.accept)
        button_box.rejected.connect(self.reject)

        layout.addLayout(form_layout)
        layout.addWidget(button_box)
        self.setLayout(layout)

        # 信号连接
        self.btn_password_mode.clicked.connect(lambda: self._switch_mode("password"))
        self.btn_sms_mode.clicked.connect(lambda: self._switch_mode("sms"))
        self.btn_send_sms.clicked.connect(self._on_send_sms)

        # 初始状态（默认密码模式）
        self._switch_mode("password")

    def _switch_mode(self, mode):
        self.login_mode = mode
        self.btn_password_mode.setChecked(mode == "password")
        self.btn_sms_mode.setChecked(mode == "sms")
        # 密码行显隐
        for i in range(self.form_layout.rowCount()):
            label_item = self.form_layout.itemAt(i, QFormLayout.LabelRole)
            if label_item and label_item.widget() and label_item.widget().text() == "密码":
                label_item.widget().setVisible(mode == "password")
                field_item = self.form_layout.itemAt(i, QFormLayout.FieldRole)
                if field_item:
                    w = field_item.widget()
                    if w:
                        w.setVisible(mode == "password")
                break
        # 短信验证码行显隐
        for i in range(self.form_layout.rowCount()):
            label_item = self.form_layout.itemAt(i, QFormLayout.LabelRole)
            if label_item and label_item.widget() and label_item.widget().text() == "短信验证码":
                label_item.widget().setVisible(mode == "sms")
                field_item = self.form_layout.itemAt(i, QFormLayout.FieldRole)
                if field_item:
                    w = field_item.widget()
                    if w:
                        w.setVisible(mode == "sms")
                    else:
                        for j in range(field_item.layout().count()):
                            field_item.layout().itemAt(j).widget().setVisible(mode == "sms")
                break

    def _on_send_sms(self):
        phone = self.phone_edit.text().strip()
        captcha = self.captcha_edit.text().strip()
        if not phone:
            QMessageBox.warning(self, "输入错误", "请先输入手机号")
            return
        if not captcha:
            QMessageBox.warning(self, "输入错误", "请先输入图形验证码")
            return

        self.btn_send_sms.setEnabled(False)
        self.btn_send_sms.setText("发送中...")
        QApplication.processEvents()

        try:
            result = Login.send_sms(self.captcha_data, phone, captcha)
            if result and result.get("result") == "0":
                self.sms_countdown_sec = 60
                self.btn_send_sms.setText(f"重新发送({self.sms_countdown_sec}s)")
                self.sms_timer.start(1000)
                QMessageBox.information(self, "发送成功", "短信验证码已发送，请注意查收")
            else:
                msg = (result and result.get("msg")) or "发送失败"
                QMessageBox.warning(self, "发送失败", msg)
                self.btn_send_sms.setEnabled(True)
                self.btn_send_sms.setText("获取验证码")
        except Exception as e:
            QMessageBox.warning(self, "发送失败", str(e))
            self.btn_send_sms.setEnabled(True)
            self.btn_send_sms.setText("获取验证码")

    def _on_sms_timer(self):
        self.sms_countdown_sec -= 1
        if self.sms_countdown_sec <= 0:
            self.sms_timer.stop()
            self.btn_send_sms.setEnabled(True)
            self.btn_send_sms.setText("获取验证码")
        else:
            self.btn_send_sms.setText(f"重新发送({self.sms_countdown_sec}s)")

    def get_login_input(self):
        return {
            "mode": self.login_mode,
            "phone": self.phone_edit.text().strip(),
            "password": self.password_edit.text(),
            "captcha": self.captcha_edit.text().strip(),
            "sms_code": self.sms_code_edit.text().strip(),
        }


class QRCodeDialog(QDialog):
    def __init__(self, qrcode_hex, money, card_no, deadline, parent=None):
        super().__init__(parent)
        self.setWindowTitle("绿色出行码")
        self.setModal(True)
        self.setMinimumWidth(380)
        self.setMinimumHeight(520)

        layout = QVBoxLayout()
        layout.setAlignment(Qt.AlignCenter)

        qr_img = qrcode.make(qrcode_hex)
        qr_img = qr_img.convert("RGBA")
        data = qr_img.tobytes("raw", "RGBA")
        qimage = QImage(data, qr_img.width, qr_img.height, QImage.Format_RGBA8888)
        pixmap = QPixmap.fromImage(qimage)

        qr_label = QLabel()
        qr_label.setPixmap(pixmap.scaled(280, 280, Qt.KeepAspectRatio, Qt.SmoothTransformation))
        qr_label.setAlignment(Qt.AlignCenter)
        qr_label.setStyleSheet("padding: 16px;")

        info_frame = QFrame()
        info_frame.setStyleSheet("QFrame { background: #f5f5f7; border-radius: 12px; padding: 12px; }")
        info_layout = QVBoxLayout(info_frame)
        info_layout.setSpacing(8)

        money_label = QLabel(f"余额: {money} 元")
        money_label.setStyleSheet("font-size: 28px; font-weight: 700; color: #1d1d1f;")
        money_label.setAlignment(Qt.AlignCenter)

        card_label = QLabel(f"交通卡号: {card_no}") if card_no else QLabel("")
        card_label.setAlignment(Qt.AlignCenter)
        card_label.setStyleSheet("font-size: 14px; color: #6e6e73;")

        deadline_label = QLabel(
            f"有效期至: {time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(int(deadline)))}"
        ) if deadline else QLabel("")
        deadline_label.setAlignment(Qt.AlignCenter)
        deadline_label.setStyleSheet("font-size: 14px; color: #6e6e73;")

        info_layout.addWidget(money_label)
        info_layout.addWidget(card_label)
        info_layout.addWidget(deadline_label)

        close_btn = QPushButton("关闭")
        close_btn.setMinimumHeight(44)
        close_btn.setStyleSheet(
            "QPushButton { background: #007aff; color: #fff; border: none; border-radius: 10px; font-weight: 600; font-size: 16px; }"
            "QPushButton:hover { background: #0a84ff; }"
        )
        close_btn.clicked.connect(self.accept)

        layout.addWidget(qr_label)
        layout.addWidget(info_frame)
        layout.addWidget(close_btn)
        self.setLayout(layout)


class Worker(QThread):
    log_signal = pyqtSignal(str)
    finished_signal = pyqtSignal()

    def __init__(self, login_name, user_id, ses_id, exchange_id, run_time_str, run_count, time_sleep):
        super().__init__()
        self.login_name = login_name
        self.user_id = user_id or login_name
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
            AutoTicket.USER_ID_PLAINTEXT = self.user_id
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

    def __init__(self, login_name, user_id, ses_id, exchange_id):
        super().__init__()
        self.login_name = login_name
        self.user_id = user_id or login_name
        self.ses_id = ses_id
        self.exchange_id = exchange_id

    def run(self):
        try:
            AutoTicket.LOGIN_NAME_PLAINTEXT = self.login_name
            AutoTicket.USER_ID_PLAINTEXT = self.user_id
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
        self.config_file = "./config.json"
        self.loading_config = False
        self.is_logged_in = False
        self.user_id = ""
        self.init_ui()
        self.load_config()

        # 检查更新
        self.check_update()

    def init_ui(self):
        self.setObjectName("mainWindow")
        self.setWindowTitle(f'AutoTicket {updater.CURRENT_VERSION} - 免费开源使用')
        self.setWindowIcon(QIcon(os.path.join(os.path.dirname(__file__), "icon.ico")))
        self.setGeometry(100, 100, 750, 900)
        self.setMinimumSize(750, 900)

        # 创建顶部登录状态区域
        auth_group = QGroupBox("登录")
        auth_layout = QHBoxLayout()
        auth_layout.setContentsMargins(20, 20, 20, 20)
        auth_layout.setSpacing(12)
        self.login_status_label = QLabel()
        self.login_button = QPushButton("登录")
        self.logout_button = QPushButton("退出登录")
        self.login_button.setObjectName("primaryButton")
        self.logout_button.setEnabled(False)
        self.login_button.setMinimumHeight(48)
        self.logout_button.setMinimumHeight(48)
        auth_layout.addWidget(QLabel("登录状态"))
        auth_layout.addWidget(self.login_status_label, 1)
        auth_layout.addWidget(self.login_button)
        auth_layout.addWidget(self.logout_button)
        auth_group.setLayout(auth_layout)

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
        self.qr_code_button = QPushButton("绿色出行码")
        self.about_button = QPushButton("说明")
        self.github_button = QPushButton("GitHub")
        self.start_button.setObjectName("primaryButton")
        self.stop_button.setObjectName("stopButton")
        self.qr_code_button.setObjectName("qrButton")
        self.stop_button.setEnabled(False)

        for button in [self.start_button, self.stop_button, self.daily_task_button, self.qr_code_button, self.about_button, self.github_button]:
            button.setMinimumHeight(48)

        button_layout.addWidget(self.start_button)
        button_layout.addWidget(self.stop_button)
        button_layout.addWidget(self.daily_task_button)
        button_layout.addWidget(self.qr_code_button)
        button_layout.addWidget(self.about_button)
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
        main_layout.addWidget(auth_group)
        main_layout.addWidget(config_group)
        main_layout.addLayout(button_layout)
        main_layout.addWidget(log_group)
        self.setLayout(main_layout)

        # 连接信号和槽
        self.login_button.clicked.connect(self.login)
        self.logout_button.clicked.connect(self.logout)
        self.start_button.clicked.connect(self.start_program)
        self.stop_button.clicked.connect(self.stop_program)
        self.daily_task_button.clicked.connect(self.execute_daily_task)
        self.qr_code_button.clicked.connect(self.show_qr_code)
        self.about_button.clicked.connect(self.show_about)
        self.github_button.clicked.connect(self.open_github)

        #输入后保存ses_id和login_name
        self.login_name_edit.textChanged.connect(self.save_config)
        self.ses_id_edit.textChanged.connect(self.save_config)
        self.exchange_id_edit.textChanged.connect(self.save_config)
        self.run_count_edit.textChanged.connect(self.save_config)
        self.time_sleep_edit.textChanged.connect(self.save_config)

        self.refresh_login_state()

    def get_current_user_id(self, login_name):
        return self.user_id or login_name

    def has_valid_login(self):
        return self.is_logged_in and bool(self.login_name_edit.text().strip()) and bool(self.ses_id_edit.text().strip())

    def refresh_login_state(self):
        if self.has_valid_login():
            self.login_status_label.setText("已登录")
            self.login_status_label.setStyleSheet("color: #1f9d55; font-weight: 700;")
            self.logout_button.setEnabled(True)
            self.start_button.setEnabled(True)
            self.qr_code_button.setEnabled(True)
        else:
            self.login_status_label.setText("未登录")
            self.login_status_label.setStyleSheet("color: #d93025; font-weight: 700;")
            self.logout_button.setEnabled(False)
            self.start_button.setEnabled(False)
            self.qr_code_button.setEnabled(False)

    def login(self):
        try:
            self.update_log("正在获取验证码...")
            captcha_data = Login.get_captcha_u067()
            if not captcha_data or captcha_data.get("result") != "0":
                QMessageBox.warning(self, "登录失败", "获取验证码失败，请稍后重试。")
                self.update_log("获取验证码失败")
                return

            dialog = LoginDialog(captcha_data, self)
            if dialog.exec_() != QDialog.Accepted:
                self.update_log("已取消登录")
                return

            login_input = dialog.get_login_input()
            if login_input["mode"] == "sms":
                # 短信验证码登录
                if not login_input["phone"] or not login_input["sms_code"]:
                    QMessageBox.warning(self, "输入错误", "手机号和短信验证码都必须填写！")
                    return

                self.update_log("正在提交短信验证码登录...")
                login_result = Login.login_u065(
                    login_input["phone"],
                    login_input["sms_code"],
                )
            else:
                # 密码登录
                if not all([login_input["phone"], login_input["password"], login_input["captcha"]]):
                    QMessageBox.warning(self, "输入错误", "手机号、密码和验证码都必须填写！")
                    return

                self.update_log("正在提交登录请求...")
                login_result = Login.login_u004_with_code(
                    captcha_data,
                    login_input["phone"],
                    login_input["password"],
                    login_input["captcha"],
                )

            if not login_result or login_result.get("result") != "0":
                message = "登录失败"
                if login_result and login_result.get("msg"):
                    message = login_result["msg"]
                QMessageBox.warning(self, "登录失败", message)
                self.update_log(f"登录失败: {message}")
                return

            login_name = login_result.get("login_name") or login_result.get("user_id") or ""
            ses_id = login_result.get("ses_id") or ""
            if not login_name or not ses_id:
                QMessageBox.warning(self, "登录失败", "登录响应缺少 login_name 或 ses_id。")
                self.update_log("登录响应缺少 login_name 或 ses_id")
                return

            self.user_id = login_result.get("user_id") or login_name
            self.is_logged_in = True
            self.login_name_edit.setText(login_name)
            self.ses_id_edit.setText(ses_id)
            self.save_config()
            self.refresh_login_state()
            self.update_log("登录成功，已自动填入 login_name 和 ses_id")
            QMessageBox.information(self, "登录成功", "登录成功，已自动填入 login_name 和 ses_id。")
        except Exception as e:
            QMessageBox.warning(self, "登录失败", str(e))
            self.update_log(f"登录失败: {str(e)}")

    def logout(self):
        if self.worker or self.daily_task_worker:
            QMessageBox.warning(self, "无法退出登录", "请先停止当前任务后再退出登录。")
            return

        self.is_logged_in = False
        self.user_id = ""
        self.login_name_edit.clear()
        self.ses_id_edit.clear()
        AutoTicket.LOGIN_NAME_PLAINTEXT = ""
        AutoTicket.USER_ID_PLAINTEXT = ""
        AutoTicket.SES_ID = ""
        self.save_config()
        self.refresh_login_state()
        self.update_log("已退出登录")
        QMessageBox.information(self, "退出登录", "已清除本地登录状态。")

    def show_qr_code(self):
        try:
            login_name = self.login_name_edit.text().strip()
            ses_id = self.ses_id_edit.text().strip()
            if not login_name or not ses_id:
                QMessageBox.warning(self, "错误", "请先登录获取 login_name 和 ses_id")
                return

            self.update_log("正在获取绿色出行码 token...")
            token = Login.get_qr_token(login_name, ses_id)
            if not token:
                QMessageBox.warning(self, "获取失败", "获取 token 失败，请检查登录状态")
                self.update_log("获取 token 失败")
                return
            self.update_log(f"token 获取成功: {token[:20]}...")

            self.update_log("正在获取乘车码数据...")
            result = Login.get_qr_code(token)
            if not result or result.get("respCode") != "00":
                QMessageBox.warning(self, "获取失败", "获取乘车码数据失败")
                self.update_log("获取乘车码数据失败")
                return

            data = result.get("data", {})
            qrcode_hex = data.get("qrcode", "")
            money = data.get("money", "0")
            card_no = data.get("trafficCardNo", "")
            deadline = data.get("deadTime", "")

            if not qrcode_hex:
                QMessageBox.warning(self, "数据错误", "乘车码数据为空")
                return

            dialog = QRCodeDialog(qrcode_hex, money, card_no, deadline, self)
            dialog.exec_()
            self.update_log("绿色出行码展示完成")

            # 后台记录访问量 (OP80)
            try:
                Login.record_qr_visit(login_name)
            except:
                pass

        except Exception as e:
            QMessageBox.warning(self, "错误", str(e))
            self.update_log(f"绿色出行码出错: {str(e)}")

    def start_program(self):
        login_name = self.login_name_edit.text()
        ses_id = self.ses_id_edit.text()
        exchange_id = self.exchange_id_edit.text()
        run_time_str = self.run_time_edit.text()
        run_count = self.run_count_edit.text()
        time_sleep = self.time_sleep_edit.text()
        user_id = self.get_current_user_id(login_name)

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
        self.worker = Worker(login_name, user_id, ses_id, exchange_id, run_time_str, run_count, time_sleep)
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
        user_id = self.get_current_user_id(login_name)

        if not all([login_name, ses_id]):
            QMessageBox.warning(self, "输入错误", "LOGIN_NAME和SES_ID字段必须填写！")
            return

        self.start_button.setEnabled(False)
        self.stop_button.setEnabled(False)
        self.daily_task_button.setEnabled(False)

        self.daily_task_worker = DailyTaskWorker(login_name, user_id, ses_id, exchange_id)
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
        if self.loading_config:
            return

        config = {
            "login_name": self.login_name_edit.text(),
            "ses_id": self.ses_id_edit.text(),
            "user_id": self.user_id,
            "is_logged_in": self.is_logged_in,
            "exchange_id": self.exchange_id_edit.text(),
            "run_count": self.run_count_edit.text(),
            "time_sleep": self.time_sleep_edit.text(),
        }
        with open(self.config_file, 'w', encoding='utf-8') as f:
            json.dump(config, f, indent=4, ensure_ascii=False)
        self.refresh_login_state()
    
    def show_about(self):
        QMessageBox.information(
            self,
            "作者: BAOfanTing 软件说明",
            "AutoTicket 是一个用于辅助填写登录信息、定时执行兑换任务与每日任务的开源工具。\n\n"
            "用途说明：\n"
            "- 支持保存 login_name、ses_id 等本地配置\n"
            "- 支持账号登录后自动回填会话信息\n"
            "- 支持定时启动兑换任务与执行每日任务\n\n"
            "开源协议：\n"
            "- 本项目基于 MIT License 开源，详见仓库中的 LICENSE 文件\n\n"
            "使用说明：\n"
            "- 本软件仅供学习、研究与技术交流使用\n"
            "- 请在遵守相关法律法规、平台规则和服务条款的前提下使用\n\n"
            "免责声明：\n"
            "- 软件按“原样”提供，不附带任何明示或暗示担保\n"
            "- 因使用本软件造成的任何直接或间接后果，开发者不承担责任\n"
            "- 如他人将本项目代码用于商业用途或不当用途，由使用者自行承担责任"
        )

    def open_github(self):
        import webbrowser
        # 打开项目的GitHub页面
        github_url = "https://github.com/BAOfanTing/AutoTicket"
        webbrowser.open(github_url)
    
    def load_config(self):
        if os.path.exists(self.config_file):
            self.loading_config = True
            try:
                with open(self.config_file, encoding='utf-8') as f:
                    config = json.load(f)
                self.user_id = config.get("user_id", "")
                self.is_logged_in = bool(config.get("is_logged_in"))
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
            finally:
                self.loading_config = False

        if not self.login_name_edit.text().strip() or not self.ses_id_edit.text().strip():
            self.is_logged_in = False
            self.user_id = ""
        self.refresh_login_state()

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