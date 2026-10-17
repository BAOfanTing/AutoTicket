"""
gui.py - AutoTicket 图形界面主模块
基于 PyQt5 实现，提供登录、配置、定时兑换、每日任务、绿色出行码等功能操作界面。
"""

import sys
from PyQt5.QtWidgets import (QApplication, QWidget, QLabel, QLineEdit, QComboBox, QPushButton,
                             QTextEdit, QVBoxLayout, QHBoxLayout, QGroupBox, QFormLayout,
                             QMessageBox, QDialog, QDialogButtonBox, QFrame)
from PyQt5.QtCore import QThread, pyqtSignal, QDateTime, QTimer, Qt
from PyQt5.QtGui import QIcon, QPixmap, QImage
import AutoTicket
import Login
import time
import json
from datetime import date
import os
import threading
import updater
import stats_client
import qrcode
from PIL import Image
import io
import base64
# pyinstaller --onefile --windowed --icon=./icon.ico -n AutoTicket gui.py

# 下拉框箭头图标路径（打包为 exe 后 __file__ 指向解压目录，均可生效）
DOWN_ARROW_ICON = os.path.join(os.path.dirname(os.path.abspath(__file__)), "icons", "down-arrow.png").replace("\\", "/")

# 全局样式表：Google Material Design 3 UI（品牌蓝 #1a73e8 主题）
# 定义各控件的颜色、圆角、字体与 elevation 分层，逻辑不受影响。
APP_STYLESHEET = """
QWidget {
    color: #1f1f1f;
    font-size: 15px;
    font-family: "Google Sans", "Roboto", "PingFang SC", "Hiragino Sans GB", "Microsoft YaHei UI", "Microsoft YaHei", sans-serif;
}
QWidget#mainWindow {
    background: #f8f9fa;
}
QLabel {
    background: transparent;
    color: #444746;
    font-weight: 500;
}
QGroupBox {
    background: #ffffff;
    border: 1px solid #dadce0;
    border-radius: 16px;
    margin-top: 14px;
    padding-top: 4px;
    color: #1f1f1f;
    font-weight: 500;
}
QGroupBox::title {
    subcontrol-origin: margin;
    left: 16px;
    padding: 0 10px;
    background: #f8f9fa;
    color: #1a73e8;
}
QLineEdit,
QTextEdit {
    background: #ffffff;
    border: 1px solid #dadce0;
    border-radius: 8px;
    padding: 8px 12px;
    color: #1f1f1f;
    selection-background-color: #1a73e8;
    selection-color: #ffffff;
}
QLineEdit:focus,
QTextEdit:focus {
    border: 2px solid #1a73e8;
}
QComboBox {
    background: #ffffff;
    border: 1px solid #dadce0;
    border-radius: 8px;
    padding: 8px 12px;
    color: #1f1f1f;
    selection-background-color: #1a73e8;
    selection-color: #ffffff;
}
QComboBox:focus {
    border: 2px solid #1a73e8;
}
QComboBox::drop-down {
    border: none;
    width: 32px;
}
QComboBox::down-arrow {
    image: url(__DOWN_ARROW_ICON__);
    width: 12px;
    height: 8px;
}
QComboBox QAbstractItemView {
    background: #ffffff;
    border: 1px solid #dadce0;
    border-radius: 8px;
    padding: 4px;
    outline: none;
}
QComboBox QAbstractItemView::item {
    padding: 8px 12px;
    border-radius: 6px;
}
QComboBox QAbstractItemView::item:hover {
    background: #e8f0fe;
}
QComboBox QAbstractItemView::item:selected {
    background: #1a73e8;
    color: #ffffff;
}
QTextEdit#logPanel {
    color: #1f1f1f;
    background: #f8f9fa;
    font-family: "Roboto Mono", "Menlo", "Consolas", monospace;
    font-size: 12px;
}
QPushButton {
    background: #ffffff;
    border: 1px solid #dadce0;
    border-radius: 20px;
    padding: 8px 22px;
    color: #1a73e8;
    font-weight: 600;
}
QPushButton:hover {
    background: #e8f0fe;
}
QPushButton:pressed {
    background: #d2e3fc;
}
QPushButton:disabled {
    background: #f1f3f4;
    border: 1px solid #dadce0;
    border-radius: 20px;
    color: #9aa0a6;
}
QPushButton#primaryButton {
    background: #1a73e8;
    border: 1px solid #1a73e8;
    border-radius: 20px;
    color: #ffffff;
    font-weight: 600;
}
QPushButton#primaryButton:hover {
    background: #1765cc;
    border: 1px solid #1765cc;
    border-radius: 20px;
}
QPushButton#primaryButton:pressed {
    background: #185abc;
    border: 1px solid #185abc;
    border-radius: 20px;
}
QPushButton#primaryButton:disabled {
    background: #bcdcff;
    border: 1px solid #bcdcff;
    border-radius: 20px;
    color: #ffffff;
}
QPushButton#stopButton {
    background: #ffffff;
    border: 1px solid #dadce0;
    border-radius: 20px;
    color: #d93025;
    font-weight: 600;
}
QPushButton#stopButton:hover {
    background: #fce8e6;
    border: 1px solid #fad2cf;
    border-radius: 20px;
}
QPushButton#stopButton:pressed {
    background: #fad2cf;
    border: 1px solid #f28b82;
    border-radius: 20px;
}
QPushButton#qrButton {
    background: #1e8e3e;
    border: 1px solid #1e8e3e;
    border-radius: 20px;
    color: #ffffff;
    font-weight: 600;
}
QPushButton#qrButton:hover {
    background: #188038;
    border: 1px solid #188038;
    border-radius: 20px;
}
QPushButton#qrButton:pressed {
    background: #13732f;
    border: 1px solid #13732f;
    border-radius: 20px;
}
QPushButton#qrButton:disabled {
    background: #b8e0c5;
    border: 1px solid #b8e0c5;
    border-radius: 20px;
    color: #ffffff;
}
QFrame#statCard {
    background: #ffffff;
    border: 1px solid #dadce0;
    border-radius: 8px;
}
QLabel#statTitle {
    color: #5f6368;
    font-size: 10px;
    font-weight: 500;
}
QFrame#avatarFrame {
    background: qlineargradient(x1:0, y1:0, x2:1, y2:1, stop:0 #1a73e8, stop:1 #174ea6);
    border-radius: 28px;
}
QLabel#avatarLabel {
    color: #ffffff;
    font-size: 24px;
    font-weight: 700;
    background: transparent;
}
QLabel#userNameLabel {
    color: #1f1f1f;
    font-size: 15px;
    font-weight: 600;
}
QLabel#integralLabel {
    color: #1e8e3e;
    font-size: 12px;
    font-weight: 600;
    background: rgba(30, 142, 62, 0.08);
    border-radius: 10px;
    padding: 2px 10px;
}
QPushButton#logoutButton {
    background: #ffffff;
    border: 1px solid #d93025;
    color: #d93025;
    border-radius: 20px;
    font-weight: 600;
    padding: 6px 20px;
}
QPushButton#logoutButton:hover {
    background: #fce8e6;
    border: 1px solid #d93025;
    border-radius: 20px;
}
QPushButton#logoutButton:disabled {
    background: #ffffff;
    border: 1px solid #dadce0;
    color: #9aa0a6;
    border-radius: 20px;
}
QLabel#dailyTaskDoneLabel {
    color: #1e8e3e;
    background: #e6f4ea;
    border: 1px solid #a8dab5;
    border-radius: 16px;
    padding: 8px 24px;
    font-size: 13px;
    font-weight: 600;
}
""".replace("__DOWN_ARROW_ICON__", DOWN_ARROW_ICON)

class LoginDialog(QDialog):
    """登录对话框，支持密码登录和短信验证码登录两种模式"""

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
                "QPushButton { border: 1px solid #dadce0; border-radius: 20px; background: #ffffff; color: #5f6368; font-weight: 600; }"
                "QPushButton:checked { background: #1a73e8; color: #fff; border: 1px solid #1a73e8; border-radius: 20px; }"
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
        self.captcha_label.setStyleSheet("border: 1px solid #dadce0; border-radius: 8px; background: #f8f9fa;")
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
            "QPushButton { background: #1a73e8; color: #fff; border: 1px solid #1a73e8; border-radius: 20px; font-weight: 600; }"
            "QPushButton:disabled { background: #bcdcff; border: 1px solid #bcdcff; border-radius: 20px; }"
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
        """切换密码登录/短信验证码登录模式，控制对应输入行的显隐"""
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
        """点击"获取验证码"按钮：校验输入、调用 SMS 接口、启动倒计时"""
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
        """短信验证码倒计时更新，每秒触发一次，倒计时结束后恢复按钮"""
        if self.sms_countdown_sec <= 0:
            self.sms_timer.stop()
            self.btn_send_sms.setEnabled(True)
            self.btn_send_sms.setText("获取验证码")
        else:
            self.btn_send_sms.setText(f"重新发送({self.sms_countdown_sec}s)")

    def get_login_input(self):
        """获取对话框中的用户输入：登录模式、手机号、密码、验证码、短信验证码"""
        return {
            "mode": self.login_mode,
            "phone": self.phone_edit.text().strip(),
            "password": self.password_edit.text(),
            "captcha": self.captcha_edit.text().strip(),
            "sms_code": self.sms_code_edit.text().strip(),
        }


class QRCodeDialog(QDialog):
    """绿色出行码展示对话框，显示服务端渲染的二维码图片及余额、卡号、有效期和优惠券信息"""

    def __init__(self, qrcode_image, money, card_no, deadline, login_name, ses_id, subway_info=None, parent=None):
        super().__init__(parent)
        self.setWindowTitle("绿色出行码")
        self.setModal(True)
        self.setMinimumWidth(420)
        self.setMinimumHeight(640)

        self.login_name = login_name
        self.ses_id = ses_id
        self.current_award_type = "1"
        self.subway_info = subway_info or {}
        self.coupon_buttons = {}

        layout = QVBoxLayout()
        layout.setAlignment(Qt.AlignCenter)

        if qrcode_image.startswith('data:image'):
            qrcode_image = qrcode_image.split(',', 1)[1]
        img_bytes = base64.b64decode(qrcode_image)
        pixmap = QPixmap()
        pixmap.loadFromData(img_bytes)

        qr_label = QLabel()
        qr_label.setPixmap(pixmap.scaled(280, 280, Qt.KeepAspectRatio, Qt.SmoothTransformation))
        qr_label.setAlignment(Qt.AlignCenter)
        qr_label.setStyleSheet("padding: 16px;")

        info_frame = QFrame()
        info_frame.setStyleSheet("QFrame { background: #f1f3f4; border-radius: 12px; padding: 12px; }")
        info_layout = QVBoxLayout(info_frame)
        info_layout.setSpacing(8)

        money_label = QLabel(f"余额: {money} 元")
        money_label.setStyleSheet("font-size: 28px; font-weight: 700; color: #f9ab00;")
        money_label.setAlignment(Qt.AlignCenter)

        card_label = QLabel(f"交通卡号: {card_no}") if card_no else QLabel("")
        card_label.setAlignment(Qt.AlignCenter)
        card_label.setStyleSheet("font-size: 14px; color: #5f6368;")

        deadline_label = QLabel(
            f"有效期至: {time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(int(deadline)))}"
        ) if deadline else QLabel("")
        deadline_label.setAlignment(Qt.AlignCenter)
        deadline_label.setStyleSheet("font-size: 14px; color: #5f6368;")

        info_layout.addWidget(money_label)
        info_layout.addWidget(card_label)
        info_layout.addWidget(deadline_label)

        coupon_frame = QFrame()
        coupon_frame.setStyleSheet("QFrame { background: #f1f3f4; border-radius: 12px; padding: 12px; }")
        coupon_layout = QVBoxLayout(coupon_frame)
        coupon_layout.setSpacing(6)

        coupon_title = QLabel("地铁优惠券")
        coupon_title.setAlignment(Qt.AlignCenter)
        coupon_title.setStyleSheet("font-size: 16px; font-weight: 600; color: #1f1f1f; margin-bottom: 8px;")
        coupon_layout.addWidget(coupon_title)

        switch_layout = QHBoxLayout()
        switch_layout.setSpacing(8)
        button_configs = [
            ("1", "2元券"),
            ("2", "4元券"),
            ("3", "6元券")
        ]
        for award_type, button_text in button_configs:
            button = QPushButton(button_text + "\n0")
            button.setCheckable(True)
            button.setMinimumHeight(56)
            button.clicked.connect(lambda checked, t=award_type: self.switch_award_type(t))
            self.coupon_buttons[award_type] = button
            switch_layout.addWidget(button)
        coupon_layout.addLayout(switch_layout)

        self.coupon_content_frame = QFrame()
        self.coupon_content_frame.setStyleSheet("QFrame { background: transparent; }")
        self.coupon_content_layout = QVBoxLayout(self.coupon_content_frame)
        self.coupon_content_layout.setSpacing(6)
        coupon_layout.addWidget(self.coupon_content_frame)

        close_btn = QPushButton("关闭")
        close_btn.setMinimumHeight(44)
        close_btn.setStyleSheet(
            "QPushButton { background: #1a73e8; color: #fff; border: none; border-radius: 22px; font-weight: 600; font-size: 15px; }"
            "QPushButton:hover { background: #1765cc; border-radius: 22px; }"
            "QPushButton:pressed { background: #185abc; border-radius: 22px; }"
        )
        close_btn.clicked.connect(self.accept)

        layout.addWidget(qr_label)
        layout.addWidget(info_frame)
        layout.addWidget(coupon_frame)
        layout.addWidget(close_btn)
        self.setLayout(layout)

        self.refresh_coupon_area()
        self.update_coupon_button_styles()

    def update_coupon_button_styles(self):
        name_map = {"1": "2元券", "2": "4元券", "3": "6元券"}
        num_map = {
            "1": self.subway_info.get("num_2", "0"),
            "2": self.subway_info.get("num_4", "0"),
            "3": self.subway_info.get("num_6", "0"),
        }
        for award_type, button in self.coupon_buttons.items():
            is_active = award_type == self.current_award_type
            button.setChecked(is_active)
            button.setText(f"{name_map[award_type]}\n{num_map[award_type]}")
            if is_active:
                button.setStyleSheet(
                    "QPushButton { background: rgba(26,115,232,0.08); color: #1a73e8; border: 1px solid #1a73e8; border-radius: 8px; font-weight: 600; font-size: 13px; padding: 4px; }"
                )
            else:
                button.setStyleSheet(
                    "QPushButton { background: #ffffff; color: #444746; border: 1px solid #dadce0; border-radius: 8px; font-weight: 600; font-size: 13px; padding: 4px; }"
                )

    def clear_coupon_content(self):
        while self.coupon_content_layout.count():
            item = self.coupon_content_layout.takeAt(0)
            widget = item.widget()
            if widget:
                widget.deleteLater()

    def refresh_coupon_area(self):
        self.clear_coupon_content()
        self.update_coupon_button_styles()

        coupon_list = self.subway_info.get("list") if isinstance(self.subway_info.get("list"), list) else []
        if coupon_list:
            for item in coupon_list:
                exchange_name = item.get("exchange_name") or item.get("award_name") or item.get("award_type") or "-"
                create_time = item.get("create_time") or item.get("createTime") or "-"
                expire_time = item.get("expire_time") or item.get("expireTime") or "-"
                self.coupon_content_layout.addWidget(self._build_coupon_detail(exchange_name, create_time, expire_time))
        else:
            empty_label = QLabel("暂无优惠券记录")
            empty_label.setAlignment(Qt.AlignCenter)
            empty_label.setStyleSheet("font-size: 14px; color: #5f6368; padding: 8px;")
            self.coupon_content_layout.addWidget(empty_label)

    def switch_award_type(self, award_type):
        if self.current_award_type == award_type:
            return

        self.current_award_type = award_type
        try:
            result = Login.get_subway_ticket_records(self.login_name, self.ses_id, award_type)
            if result and result.get("result") == "0":
                self.subway_info = result
            else:
                self.subway_info = {"list": []}
        except Exception:
            self.subway_info = {"list": []}

        self.refresh_coupon_area()
        self.update_coupon_button_styles()

    def _build_coupon_detail(self, exchange_name, create_time, expire_time):
        detail_frame = QFrame()
        detail_frame.setStyleSheet("QFrame { background: transparent; }")
        detail_layout = QVBoxLayout(detail_frame)
        detail_layout.setSpacing(6)

        rows = [
            ("券名称", exchange_name),
            ("领取时间", create_time),
            ("过期时间", expire_time),
        ]
        for label_text, value_text in rows:
            row_layout = QHBoxLayout()
            row_layout.setSpacing(8)
            row_layout.setContentsMargins(0, 0, 0, 0)

            lbl = QLabel(label_text)
            lbl.setStyleSheet("font-size: 13px; color: #5f6368;")

            val = QLabel(value_text)
            val.setStyleSheet("font-size: 13px; color: #1f1f1f; font-weight: 500;")

            row_layout.addWidget(lbl)
            row_layout.addWidget(val, 1)
            detail_layout.addLayout(row_layout)

        return detail_frame


class Worker(QThread):
    """定时兑换任务工作线程：等待指定时间后启动兑换循环"""

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
        """线程入口：设置全局参数 → 等待目标时间 → 执行兑换任务"""
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
            self.log_signal.emit("正在同步服务器时间...")

            # 与小程序版一致：同步服务器时间并计算本地偏移，避免本地时钟偏差错过抢票时机
            offset = AutoTicket.sync_time_offset()
            self.wait_until_target(run_time, offset)
            if self.running:
                AutoTicket.job()
        except Exception as e:
            self.log_signal.emit(f"任务执行出错: {str(e)}")
        finally:
            AutoTicket.set_log_callback(None)
            self.finished_signal.emit()

    def wait_until_target(self, run_time, offset=0.0):
        """等待直到目标时间（按服务器时间偏移校正），按距离远近动态调整休眠粒度（最远 5 分钟，最近 50 毫秒）"""
        from datetime import datetime, timedelta

        while self.running:
            now = datetime.now() + timedelta(seconds=offset)
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
        """请求线程停止（设置 running 标志为 False，wait_until_target 将退出循环）"""
        self.running = False

class DailyTaskWorker(QThread):
    """每日任务工作线程：封装签到、评论、查询积分等日常操作"""

    log_signal = pyqtSignal(str)
    finished_signal = pyqtSignal()

    def __init__(self, login_name, user_id, ses_id, exchange_id):
        super().__init__()
        self.login_name = login_name
        self.user_id = user_id or login_name
        self.ses_id = ses_id
        self.exchange_id = exchange_id

    def run(self):
        """线程入口：设置全局参数并执行每日任务工作流"""
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

class StatsPoller(QThread):
    """统计数据轮询线程：定时拉取在线人数与抢票数，纯展示用，失败静默忽略"""

    stats_signal = pyqtSignal(dict)

    def __init__(self, interval=60):
        super().__init__()
        self.interval = interval
        self.running = True

    def run(self):
        """线程入口：立即拉取一次，之后每隔 interval 秒拉取一次"""
        while self.running:
            data = stats_client.fetch_stats()
            if data:
                self.stats_signal.emit(data)
            # 分片休眠，便于关闭软件时快速退出
            for _ in range(int(self.interval * 2)):
                if not self.running:
                    return
                time.sleep(0.5)

    def stop(self):
        """请求线程停止"""
        self.running = False


class MainWindow(QWidget):
    """主窗口，包含登录、配置参数、启动/停止任务、日志展示及绿色出行码等功能"""

    def __init__(self):
        super().__init__()
        self.worker = None
        self.daily_task_worker = None
        self.stats_poller = None
        self.stats_group = None
        self.stop_requested = False
        self.config_file = "./config.json"
        self.loading_config = False
        self.is_logged_in = False
        self.user_id = ""
        self.user_name = ""
        self.remain_integral = 0
        self.daily_task_done_date = ""
        self.init_ui()
        self.load_config()
        self.setup_stats()

        # 启动时检查版本更新
        self.check_update()

    def init_ui(self):
        """初始化界面：创建登录区域、配置参数区域、按钮区域和日志展示区域"""
        self.setObjectName("mainWindow")
        self.setWindowTitle(f'AutoTicket {updater.CURRENT_VERSION} - 免费开源使用')
        self.setWindowIcon(QIcon(os.path.join(os.path.dirname(__file__), "icon.ico")))
        self.setGeometry(100, 100, 780, 980)
        self.setMinimumSize(760, 940)

        # 创建顶部登录状态区域（圆头像 + 用户名 + 状态标签）
        auth_group = QGroupBox("登录")
        auth_outer_layout = QVBoxLayout()
        auth_outer_layout.setContentsMargins(20, 20, 20, 20)
        auth_outer_layout.setSpacing(12)

        # 小程序宣传提示
        mini_program_label = QLabel("小程序 e家AutoTicket 已上线，手机端即可使用")
        mini_program_label.setStyleSheet("font-size: 13px; color: #5f6368;")
        auth_outer_layout.addWidget(mini_program_label)

        # 头像 + 用户信息行
        status_row = QHBoxLayout()
        status_row.setSpacing(16)

        # 圆形头像
        avatar_frame = QFrame()
        avatar_frame.setObjectName("avatarFrame")
        avatar_frame.setFixedSize(56, 56)
        avatar_inner = QVBoxLayout(avatar_frame)
        avatar_inner.setContentsMargins(0, 0, 0, 0)
        self.avatar_label = QLabel("用")
        self.avatar_label.setObjectName("avatarLabel")
        self.avatar_label.setAlignment(Qt.AlignCenter)
        avatar_inner.addWidget(self.avatar_label)

        # 用户信息
        status_meta = QVBoxLayout()
        status_meta.setSpacing(4)

        # 用户名 + 状态 chip
        user_row = QHBoxLayout()
        user_row.setSpacing(8)
        self.user_name_label = QLabel("未登录")
        self.user_name_label.setObjectName("userNameLabel")
        self.status_chip = QLabel("未登录")
        user_row.addWidget(self.user_name_label)
        user_row.addWidget(self.status_chip)

        # 积分
        self.integral_label = QLabel("")
        self.integral_label.setObjectName("integralLabel")
        self.integral_label.setVisible(False)

        status_meta.addLayout(user_row)
        status_meta.addWidget(self.integral_label)

        status_row.addWidget(avatar_frame)
        status_row.addLayout(status_meta)
        status_row.addStretch(1)

        # 按钮行
        buttons_row = QHBoxLayout()
        buttons_row.setSpacing(8)
        self.login_button = QPushButton("登录")
        self.logout_button = QPushButton("退出登录")
        self.login_button.setObjectName("primaryButton")
        self.logout_button.setObjectName("logoutButton")
        self.logout_button.setEnabled(False)
        self.login_button.setMinimumHeight(40)
        self.logout_button.setMinimumHeight(40)
        buttons_row.addWidget(self.login_button)
        buttons_row.addWidget(self.logout_button)

        auth_outer_layout.addLayout(status_row)
        auth_outer_layout.addLayout(buttons_row)
        auth_group.setLayout(auth_outer_layout)

        # 创建配置区域
        config_group = QGroupBox("配置参数")
        config_layout = QFormLayout()
        config_layout.setHorizontalSpacing(18)
        config_layout.setVerticalSpacing(14)
        config_layout.setContentsMargins(20, 26, 20, 20)
        config_layout.setLabelAlignment(Qt.AlignRight | Qt.AlignVCenter)

        self.login_name_edit = QLineEdit(AutoTicket.LOGIN_NAME_PLAINTEXT)
        self.ses_id_edit = QLineEdit(AutoTicket.SES_ID)
        self.exchange_id_edit = QComboBox()
        self.exchange_id_edit.addItem("2元优惠券", "9")
        self.exchange_id_edit.addItem("4元优惠券", "10")
        self.exchange_id_edit.addItem("6元优惠券", "11")
        self.exchange_id_edit.setCurrentIndex(1)  # 默认4元

        # 登录凭证输入框不在界面上展示，仅用于内部数据回填
        self.login_name_edit.setVisible(False)
        self.ses_id_edit.setVisible(False)

        # 设置默认时间，但允许用户手动修改
        default_time = self.get_next_run_time()
        self.run_time_edit = QLineEdit(default_time)
        self.run_count_edit = QLineEdit(str(AutoTicket.RUN_COUNT))
        self.time_sleep_edit = QLineEdit(str(AutoTicket.timeSleep))

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

        config_layout.addRow(QLabel("优惠券面额"), self.exchange_id_edit)
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
        self.start_button.setObjectName("primaryButton")
        self.stop_button.setObjectName("stopButton")
        self.qr_code_button.setObjectName("qrButton")
        self.stop_button.setEnabled(False)

        for button in [self.start_button, self.stop_button, self.daily_task_button, self.qr_code_button]:
            button.setMinimumHeight(48)

        button_layout.addWidget(self.start_button)
        button_layout.addWidget(self.stop_button)
        button_layout.addWidget(self.daily_task_button)
        button_layout.addWidget(self.qr_code_button)

        # 每日任务完成状态标签
        self.daily_task_done_label = QLabel("✓ 每日任务已完成")
        self.daily_task_done_label.setObjectName("dailyTaskDoneLabel")
        self.daily_task_done_label.setAlignment(Qt.AlignCenter)
        self.daily_task_done_label.setVisible(False)

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

        # 实时统计区域（未配置统计服务时整体隐藏）
        self.stats_group = self.build_stats_group()
        self.stats_group.setVisible(False)

        # 主布局
        main_layout = QVBoxLayout()
        main_layout.setContentsMargins(24, 24, 24, 24)
        main_layout.setSpacing(16)
        main_layout.addWidget(auth_group)
        main_layout.addWidget(self.stats_group)
        main_layout.addWidget(config_group)
        main_layout.addLayout(button_layout)
        main_layout.addWidget(self.daily_task_done_label)
        main_layout.addWidget(log_group)
        self.setLayout(main_layout)

        # 连接信号和槽
        self.login_button.clicked.connect(self.login)
        self.logout_button.clicked.connect(self.logout)
        self.start_button.clicked.connect(self.start_program)
        self.stop_button.clicked.connect(self.stop_program)
        self.daily_task_button.clicked.connect(self.execute_daily_task)
        self.qr_code_button.clicked.connect(self.show_qr_code)

        #输入后保存ses_id和login_name
        self.login_name_edit.textChanged.connect(self.save_config)
        self.ses_id_edit.textChanged.connect(self.save_config)
        self.exchange_id_edit.currentIndexChanged.connect(self.save_config)
        self.run_count_edit.textChanged.connect(self.save_config)
        self.time_sleep_edit.textChanged.connect(self.save_config)

        self.refresh_login_state()

    def get_current_user_id(self, login_name):
        """获取当前有效的 user_id，优先使用已登录的 user_id，否则回退到 login_name"""
        return self.user_id or login_name

    def has_valid_login(self):
        """判断当前是否处于有效登录状态（已登录且表单中有 login_name 和 ses_id）"""
        return self.is_logged_in and bool(self.login_name_edit.text().strip()) and bool(self.ses_id_edit.text().strip())

    def verify_session(self):
        """调用 U005 验证当前 ses_id 是否仍有效，若失效则清除登录状态。"""
        login_name = self.login_name_edit.text().strip()
        ses_id = self.ses_id_edit.text().strip()
        if not login_name or not ses_id:
            return False

        try:
            user_info = Login.query_user_info(login_name, ses_id)
            if user_info and user_info.get("result") == "0":
                name = user_info.get("name") or user_info.get("sensitive_name", "")
                if name:
                    self.user_name = name
                self.remain_integral = int(user_info.get("remain_integral", 0))
                self.refresh_login_state()
                return True
            else:
                self.update_log("登录会话已失效，请重新登录")
                self._clear_login_state()
                self.refresh_login_state()
                QMessageBox.warning(self, "登录已失效", "登录会话已失效，请重新登录。")
                return False
        except Exception as e:
            self.update_log(f"验证登录状态时出错: {e}")
            self._clear_login_state()
            self.refresh_login_state()
            QMessageBox.warning(self, "登录已失效", "验证登录状态时出错，请重新登录。")
            return False

    def _clear_login_state(self):
        """清除内部登录状态但不触发界面刷新，供内部调用"""
        self.is_logged_in = False
        self.user_id = ""
        self.user_name = ""
        self.remain_integral = 0
        AutoTicket.LOGIN_NAME_PLAINTEXT = ""
        AutoTicket.USER_ID_PLAINTEXT = ""
        AutoTicket.SES_ID = ""

    def refresh_login_state(self):
        """根据登录状态更新界面 UI：头像、用户名、状态 chip、积分显示"""
        chip_ok_style = "color: #1e8e3e; background: rgba(30, 142, 62, 0.12); border-radius: 10px; padding: 2px 10px; font-size: 11px; font-weight: 600;"
        chip_bad_style = "color: #d93025; background: rgba(217, 48, 37, 0.12); border-radius: 10px; padding: 2px 10px; font-size: 11px; font-weight: 600;"

        if self.has_valid_login():
            # 头像：用户名首字符
            name = self.user_name or "用"
            self.avatar_label.setText(name[0])
            self.user_name_label.setText(self.user_name or "已登录")
            self.status_chip.setText("已登录")
            self.status_chip.setStyleSheet(chip_ok_style)
            # 积分
            if self.remain_integral > 0:
                self.integral_label.setText(f"积分 · {self.remain_integral}")
                self.integral_label.setVisible(True)
            else:
                self.integral_label.setVisible(False)
            # 按钮
            self.logout_button.setEnabled(True)
            self.start_button.setEnabled(True)
            self.qr_code_button.setEnabled(True)
        else:
            # 未登录
            self.avatar_label.setText("用")
            self.user_name_label.setText("未登录")
            self.status_chip.setText("未登录")
            self.status_chip.setStyleSheet(chip_bad_style)
            self.integral_label.setVisible(False)
            # 按钮
            self.logout_button.setEnabled(False)
            self.start_button.setEnabled(False)
            self.qr_code_button.setEnabled(False)

    # ================= 实时统计 =================
    def build_stats_group(self):
        """构建实时统计卡片区域：在线人数 + 各面额抢到数（紧凑版）"""
        stats_group = QGroupBox("实时统计")
        stats_outer = QVBoxLayout()
        stats_outer.setContentsMargins(16, 10, 16, 10)
        stats_outer.setSpacing(0)

        cards_layout = QHBoxLayout()
        cards_layout.setSpacing(8)

        self.stat_labels = {}
        card_defs = [
            ("online", "在线人数", "#1e8e3e"),
            ("9", "2元券", "#1f1f1f"),
            ("10", "4元券", "#1f1f1f"),
            ("11", "6元券", "#1f1f1f"),
        ]
        for key, title, color in card_defs:
            card = QFrame()
            card.setObjectName("statCard")
            card_layout = QVBoxLayout(card)
            card_layout.setContentsMargins(6, 8, 6, 8)
            card_layout.setSpacing(2)

            title_label = QLabel(title)
            title_label.setObjectName("statTitle")
            title_label.setAlignment(Qt.AlignCenter)

            value_label = QLabel("--")
            value_label.setAlignment(Qt.AlignCenter)
            value_label.setStyleSheet(f"font-size: 18px; font-weight: 700; color: {color};")

            card_layout.addWidget(title_label)
            card_layout.addWidget(value_label)
            self.stat_labels[key] = value_label
            cards_layout.addWidget(card, 1)

        stats_outer.addLayout(cards_layout)
        stats_group.setLayout(stats_outer)
        return stats_group

    def setup_stats(self):
        """统计服务已配置时显示统计面板、上报上线并启动轮询"""
        if not stats_client.is_enabled():
            self.stats_group.setVisible(False)
            return

        self.stats_group.setVisible(True)
        # 上报上线放到后台线程，避免网络请求拖慢软件启动
        threading.Thread(target=stats_client.report_online, args=("open",), daemon=True).start()

        self.stats_poller = StatsPoller(60)
        self.stats_poller.stats_signal.connect(self.update_stats_display)
        self.stats_poller.start()

    def update_stats_display(self, data):
        """把拉取到的统计数据刷新到卡片上"""
        try:
            self.stat_labels["online"].setText(str(data.get("online", 0)))
            by_type = data.get("by_type") or {}
            for key in ("9", "10", "11"):
                self.stat_labels[key].setText(str(by_type.get(key, 0)))
        except Exception:
            pass

    def closeEvent(self, event):
        """关闭窗口：停止后台线程并上报下线"""
        try:
            if self.stats_poller:
                self.stats_poller.stop()
            if self.worker:
                self.worker.stop()
        except Exception:
            pass

        # 上报下线（超时 1 秒，失败不影响退出）
        try:
            if stats_client.is_enabled():
                stats_client.report_offline()
        except Exception:
            pass

        event.accept()

    def login(self):
        """弹出登录对话框，完成验证码获取→用户输入→登录提交→自动回填信息的完整流程"""
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

            # 登录成功后立即查询用户信息，获取真实姓名
            try:
                user_info = Login.query_user_info(login_name, ses_id)
                if user_info and user_info.get("result") == "0":
                    self.user_name = user_info.get("name") or user_info.get("sensitive_name", "")
                    self.remain_integral = int(user_info.get("remain_integral", 0))
                    self.update_log(f"欢迎, {self.user_name}  当前积分: {self.remain_integral}")
                else:
                    self.user_name = ""
                    self.remain_integral = 0
            except Exception:
                self.user_name = ""
                self.remain_integral = 0

            self.refresh_login_state()
            self.update_log("登录成功，已自动填入 login_name 和 ses_id")
            QMessageBox.information(self, "登录成功", "登录成功，已自动填入 login_name 和 ses_id。")
        except Exception as e:
            QMessageBox.warning(self, "登录失败", str(e))
            self.update_log(f"登录失败: {str(e)}")

    def logout(self):
        """退出登录：清空表单中的登录信息并重置状态"""
        if self.worker or self.daily_task_worker:
            QMessageBox.warning(self, "无法退出登录", "请先停止当前任务后再退出登录。")
            return

        self.is_logged_in = False
        self.user_id = ""
        self.user_name = ""
        self.remain_integral = 0
        self.daily_task_done_date = ""
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
        """获取并展示绿色出行码（token → 乘车码 → QR 码弹窗），同时查询优惠券统计并在后台记录访问量"""
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
            qrcode_image = data.get("qrcodeImage", "")
            money = data.get("money", "0")
            card_no = data.get("trafficCardNo", "")
            deadline = data.get("deadTime", "")

            if not qrcode_image:
                QMessageBox.warning(self, "数据错误", "服务端未返回图片，请确认接口参数")
                return

            subway_info = {}
            try:
                self.update_log("正在查询地铁优惠券统计...")
                subway_result = Login.get_subway_ticket_records(login_name, ses_id)
                if subway_result and subway_result.get("result") == "0":
                    subway_info = subway_result
                else:
                    self.update_log("地铁优惠券统计查询失败，已跳过展示")
            except Exception as subway_error:
                self.update_log(f"地铁优惠券统计查询失败: {str(subway_error)}")

            dialog = QRCodeDialog(qrcode_image, money, card_no, deadline, login_name, ses_id, subway_info, self)
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
        """启动定时兑换任务：校验输入后创建工作线程 Worker 并启动"""
        login_name = self.login_name_edit.text()
        ses_id = self.ses_id_edit.text()
        exchange_id = self.exchange_id_edit.currentData()
        run_time_str = self.run_time_edit.text()
        run_count = self.run_count_edit.text()
        time_sleep = self.time_sleep_edit.text()
        user_id = self.get_current_user_id(login_name)

        # 验证输入
        if not all([login_name, ses_id, exchange_id, run_time_str, run_count, time_sleep]):
            QMessageBox.warning(self, "输入错误", "所有字段都必须填写！")
            return

        try:
            count_val = int(run_count)
            sleep_val = float(time_sleep)
            from datetime import datetime
            datetime.strptime(run_time_str, "%Y-%m-%d %H:%M:%S")
            if count_val <= 0 or count_val > 20:
                raise ValueError("运行次数必须是 1~20 之间的正整数")
            if sleep_val < 0.15:
                raise ValueError("运行间隔不能小于 0.15 秒")
        except ValueError as e:
            msg = str(e) if "运行" in str(e) else "RUN_COUNT 和 timeSleep 必须是数字，RUN_TIME 格式必须正确！"
            QMessageBox.warning(self, "输入错误", msg)
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
        """停止正在运行的兑换任务"""
        if self.worker:
            self.stop_requested = True
            self.worker.stop()
            self.worker = None
        self.start_button.setEnabled(True)
        self.stop_button.setEnabled(False)
        self.update_log("程序已停止")
        
    def execute_daily_task(self):
        """执行每日任务完整工作流：登录→3次签到→评论→查询积分"""
        login_name = self.login_name_edit.text()
        ses_id = self.ses_id_edit.text()
        exchange_id = self.exchange_id_edit.currentData()
        user_id = self.get_current_user_id(login_name)

        if not all([login_name, ses_id]):
            QMessageBox.warning(self, "输入错误", "LOGIN_NAME和SES_ID字段必须填写！")
            return

        self.start_button.setEnabled(False)
        self.stop_button.setEnabled(False)
        self.daily_task_button.setEnabled(False)

        self.daily_task_done_label.setVisible(False)
        self.daily_task_worker = DailyTaskWorker(login_name, user_id, ses_id, exchange_id)
        self.daily_task_worker.log_signal.connect(self.update_log)
        self.daily_task_worker.finished_signal.connect(self.daily_task_finished)
        self.daily_task_worker.start()

    def daily_task_finished(self):
        """每日任务完成后的回调：恢复按钮状态"""
        self.start_button.setEnabled(True)
        self.stop_button.setEnabled(False)
        self.daily_task_button.setEnabled(True)
        self.daily_task_done_date = date.today().isoformat()
        self.save_config()
        self.daily_task_done_label.setVisible(True)
        self.update_log("每日任务执行完成")
        self.daily_task_worker = None
        
    def update_log(self, message):
        """向日志显示区域追加一条带时间戳的消息"""
        timestamp = QDateTime.currentDateTime().toString("yyyy-MM-dd hh:mm:ss")
        self.log_display.append(f"[{timestamp}] {message}")
        
    def program_finished(self):
        """兑换任务完成后的回调：恢复按钮状态"""
        self.start_button.setEnabled(True)
        self.stop_button.setEnabled(False)
        if not self.stop_requested:
            self.update_log("程序执行完成")
        self.stop_requested = False
        self.worker = None

    def save_config(self):
        """将当前表单配置保存到本地 config.json 文件（loading_config 为 True 时跳过）"""
        if self.loading_config:
            return

        config = {
            "login_name": self.login_name_edit.text(),
            "ses_id": self.ses_id_edit.text(),
            "user_id": self.user_id,
            "user_name": self.user_name,
            "is_logged_in": self.is_logged_in,
            "exchange_id": self.exchange_id_edit.currentData(),
            "run_count": self.run_count_edit.text(),
            "time_sleep": self.time_sleep_edit.text(),
            # 统计相关：匿名标识与服务端地址，避免被本次写入覆盖
            "client_id": stats_client.get_client_id(),
            "stats_api_base": stats_client.get_api_base(),
            # 每日任务完成日期（当天有效）
            "daily_task_done_date": self.daily_task_done_date,
        }
        with open(self.config_file, 'w', encoding='utf-8') as f:
            json.dump(config, f, indent=4, ensure_ascii=False)
        self.refresh_login_state()
    
    def load_config(self):
        """从本地 config.json 加载保存的配置（login_name、ses_id、exchange_id 等）"""
        if os.path.exists(self.config_file):
            self.loading_config = True
            try:
                with open(self.config_file, encoding='utf-8') as f:
                    config = json.load(f)
                self.user_id = config.get("user_id", "")
                self.is_logged_in = bool(config.get("is_logged_in"))
                self.user_name = config.get("user_name", "")
                if "login_name" in config:
                    self.login_name_edit.setText(config["login_name"])
                if "ses_id" in config:
                    self.ses_id_edit.setText(config["ses_id"])
                if "exchange_id" in config:
                    value = config["exchange_id"]
                    index = self.exchange_id_edit.findData(value)
                    if index >= 0:
                        self.exchange_id_edit.setCurrentIndex(index)
                if "run_count" in config:
                    self.run_count_edit.setText(config["run_count"])
                if "time_sleep" in config:
                    self.time_sleep_edit.setText(config["time_sleep"])
                self.daily_task_done_date = config.get("daily_task_done_date", "")
            finally:
                self.loading_config = False

        if not self.login_name_edit.text().strip() or not self.ses_id_edit.text().strip():
            self.is_logged_in = False
            self.user_id = ""
            self.user_name = ""
            self.daily_task_done_date = ""
        self.refresh_login_state()

        # 如果当天已完成每日任务，恢复显示标签
        if self.daily_task_done_date == date.today().isoformat():
            self.daily_task_done_label.setVisible(True)

        # 如果标记已登录，启动后验证 ses_id 是否仍有效
        if self.is_logged_in and self.login_name_edit.text().strip() and self.ses_id_edit.text().strip():
            QTimer.singleShot(100, self.verify_session)

    def get_next_run_time(self):
        """
        根据当前时间自动推算下一个合理的运行时间点。

        规则：
        1. 当前在 7:00 之前 → 当天 7:00
        2. 当前在 7:00 ~ 11:30 → 当天 11:30
        3. 当前在 11:30 ~ 17:00 → 当天 17:00
        4. 当前已过 17:00 → 次日 7:00
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
        """在后台线程中检查是否有新版本发布，若有则提示用户下载"""
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