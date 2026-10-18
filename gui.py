"""
gui.py - AutoTicket 图形界面主模块
基于 PyQt5 实现，提供登录、配置、定时兑换、每日任务、绿色出行码等功能操作界面。
"""

import sys
from PyQt5.QtWidgets import (QApplication, QWidget, QLabel, QLineEdit, QComboBox, QPushButton,
                             QTextEdit, QVBoxLayout, QHBoxLayout, QGroupBox, QFormLayout,
                             QMessageBox, QDialog, QDialogButtonBox, QFrame, QSizePolicy,
                             QScrollArea)
from PyQt5.QtCore import QThread, pyqtSignal, QDateTime, QTimer, Qt
from PyQt5.QtGui import QIcon, QPixmap, QImage
import AutoTicket
import Login
import time
import json
import html
from datetime import date
import os
import threading
import updater
import stats_client
import qrcode
from PIL import Image
import io


def safe_int(value, default=0):
    """把接口返回的积分等字段安全转成 int。

    接口可能返回字符串、空串、带小数点的字符串甚至 None，
    直接 int() 会抛 ValueError/TypeError 导致界面崩掉，这里统一兜底。
    """
    if value is None:
        return default
    try:
        return int(float(str(value).strip() or default))
    except (ValueError, TypeError):
        return default
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
""".replace("__DOWN_ARROW_ICON__", DOWN_ARROW_ICON)

class LoginDialog(QDialog):
    """登录对话框，支持密码登录和短信验证码登录两种模式"""

    def __init__(self, captcha_data, parent=None):
        super().__init__(parent)
        self.setWindowTitle("账号登录")
        self.setModal(True)
        # 去掉标题栏的问号按钮
        self.setWindowFlags(self.windowFlags() & ~Qt.WindowContextHelpButtonHint)
        self.setMinimumWidth(420)
        self.setStyleSheet("QDialog { background: #ffffff; }")
        self.captcha_data = captcha_data
        self.sms_countdown_sec = 0
        self.sms_timer = QTimer(self)
        self.sms_timer.timeout.connect(self._on_sms_timer)

        # 保存"密码/短信"相关控件，供 _switch_mode 显隐（不再靠遍历表单项找文字）
        self._password_widgets = []
        self._sms_widgets = []

        layout = QVBoxLayout()
        layout.setContentsMargins(28, 24, 28, 20)
        layout.setSpacing(16)

        # ---------- 顶部标题 ----------
        title = QLabel("账号登录")
        title.setStyleSheet("font-size: 20px; font-weight: 700; color: #1f1f1f;")
        subtitle = QLabel("请使用手机号完成登录")
        subtitle.setStyleSheet("font-size: 12px; color: #5f6368;")
        layout.addWidget(title)
        layout.addWidget(subtitle)

        # ---------- 登录方式切换（分段按钮）----------
        mode_layout = QHBoxLayout()
        mode_layout.setSpacing(0)
        self.btn_password_mode = QPushButton("密码登录")
        self.btn_sms_mode = QPushButton("短信验证码登录")
        for btn in [self.btn_password_mode, self.btn_sms_mode]:
            btn.setCheckable(True)
            btn.setMinimumHeight(38)
            btn.setCursor(Qt.PointingHandCursor)
            btn.setStyleSheet(
                "QPushButton { border: none; background: transparent; color: #444746;"
                " font-weight: 600; font-size: 13px; border-radius: 17px; }"
                "QPushButton:checked { background: #ffffff; color: #1a73e8;"
                " border: 1px solid #dadce0; }"
            )
        self.btn_password_mode.setChecked(True)
        mode_layout.addWidget(self.btn_password_mode)
        mode_layout.addWidget(self.btn_sms_mode)

        mode_frame = QFrame()
        mode_frame.setObjectName("modeFrame")
        mode_frame.setLayout(mode_layout)
        mode_frame.setStyleSheet(
            "QFrame#modeFrame { background: #f1f3f4; border-radius: 19px; padding: 4px; }"
        )
        layout.addWidget(mode_frame)

        # ---------- 表单 ----------
        form = QVBoxLayout()
        form.setSpacing(12)

        # 手机号
        form.addWidget(self._make_label("手机号"))
        self.phone_edit = QLineEdit()
        self.phone_edit.setPlaceholderText("请输入手机号")
        form.addWidget(self.phone_edit)

        # 密码（密码模式）
        self.password_label = self._make_label("密码")
        self.password_edit = QLineEdit()
        self.password_edit.setPlaceholderText("请输入密码")
        self.password_edit.setEchoMode(QLineEdit.Password)
        form.addWidget(self.password_label)
        form.addWidget(self.password_edit)
        self._password_widgets = [self.password_label, self.password_edit]

        # 图形验证码：图片和输入框并排，图片保持清晰
        form.addWidget(self._make_label("验证码"))
        captcha_row = QHBoxLayout()
        captcha_row.setSpacing(12)

        self.captcha_label = QLabel()
        self.captcha_label.setAlignment(Qt.AlignCenter)
        self.captcha_label.setFixedSize(150, 62)
        self.captcha_label.setStyleSheet(
            "border: 1px solid #dadce0; border-radius: 8px; background: #f8f9fa;"
        )
        captcha_bytes = Login.decode_captcha_image(captcha_data)
        pixmap = QPixmap()
        pixmap.loadFromData(captcha_bytes)
        if not pixmap.isNull():
            # 按比例缩放，避免拉伸导致模糊
            self.captcha_label.setPixmap(
                pixmap.scaled(148, 60, Qt.KeepAspectRatio, Qt.SmoothTransformation)
            )
        captcha_row.addWidget(self.captcha_label)

        self.captcha_edit = QLineEdit()
        self.captcha_edit.setPlaceholderText("请输入图形验证码")
        captcha_row.addWidget(self.captcha_edit, 1)
        form.addLayout(captcha_row)

        # 短信验证码（短信模式）
        self.sms_label = self._make_label("短信验证码")
        self.sms_code_edit = QLineEdit()
        self.sms_code_edit.setPlaceholderText("请输入短信验证码")
        self.btn_send_sms = QPushButton("获取验证码")
        self.btn_send_sms.setMinimumHeight(42)
        self.btn_send_sms.setMinimumWidth(120)
        self.btn_send_sms.setCursor(Qt.PointingHandCursor)
        self.btn_send_sms.setStyleSheet(
            "QPushButton { background: #1a73e8; color: #fff; border: 1px solid #1a73e8;"
            " border-radius: 8px; font-weight: 600; font-size: 13px; }"
            "QPushButton:hover { background: #1765cc; }"
            "QPushButton:disabled { background: #bcdcff; border: 1px solid #bcdcff; color: #ffffff; }"
        )

        sms_row = QHBoxLayout()
        sms_row.setSpacing(12)
        sms_row.addWidget(self.sms_code_edit, 1)
        sms_row.addWidget(self.btn_send_sms)
        sms_row_frame = QFrame()
        sms_row_frame.setLayout(sms_row)
        sms_row_frame.setStyleSheet("QFrame { border: none; }")

        form.addWidget(self.sms_label)
        form.addWidget(sms_row_frame)
        self._sms_widgets = [self.sms_label, sms_row_frame]

        for line_edit in [self.phone_edit, self.password_edit, self.captcha_edit, self.sms_code_edit]:
            line_edit.setMinimumHeight(42)
            line_edit.setStyleSheet(
                "QLineEdit { background: #ffffff; border: 1px solid #dadce0; border-radius: 8px;"
                " padding: 8px 12px; font-size: 13px; color: #1f1f1f; }"
                "QLineEdit:focus { border: 1px solid #1a73e8; }"
            )

        layout.addLayout(form)
        layout.addSpacing(4)

        # ---------- 底部按钮 ----------
        button_box = QDialogButtonBox()
        ok_btn = button_box.addButton("登录", QDialogButtonBox.AcceptRole)
        cancel_btn = button_box.addButton("取消", QDialogButtonBox.RejectRole)
        ok_btn.setObjectName("loginOkBtn")
        ok_btn.setMinimumHeight(40)
        ok_btn.setMinimumWidth(110)
        ok_btn.setCursor(Qt.PointingHandCursor)
        ok_btn.setStyleSheet(
            "QPushButton { background: #1a73e8; color: #fff; border: 1px solid #1a73e8;"
            " border-radius: 8px; font-weight: 600; font-size: 13px; }"
            "QPushButton:hover { background: #1765cc; }"
            "QPushButton:pressed { background: #1456a8; }"
        )
        cancel_btn.setMinimumHeight(40)
        cancel_btn.setMinimumWidth(90)
        cancel_btn.setCursor(Qt.PointingHandCursor)
        cancel_btn.setStyleSheet(
            "QPushButton { background: transparent; color: #5f6368; border: 1px solid #dadce0;"
            " border-radius: 8px; font-weight: 600; font-size: 13px; }"
            "QPushButton:hover { background: #f1f3f4; }"
        )
        button_box.accepted.connect(self.accept)
        button_box.rejected.connect(self.reject)
        layout.addWidget(button_box)
        self.setLayout(layout)

        # 信号连接
        self.btn_password_mode.clicked.connect(lambda: self._switch_mode("password"))
        self.btn_sms_mode.clicked.connect(lambda: self._switch_mode("sms"))
        self.btn_send_sms.clicked.connect(self._on_send_sms)

        # 初始状态（默认密码模式）
        self._switch_mode("password")

    @staticmethod
    def _make_label(text):
        """表单小标题"""
        label = QLabel(text)
        label.setStyleSheet("font-size: 12px; color: #444746; font-weight: 600;")
        return label

    def _switch_mode(self, mode):
        """切换密码登录/短信验证码登录模式，控制对应输入控件的显隐"""
        self.login_mode = mode
        self.btn_password_mode.setChecked(mode == "password")
        self.btn_sms_mode.setChecked(mode == "sms")
        for w in self._password_widgets:
            w.setVisible(mode == "password")
        for w in self._sms_widgets:
            w.setVisible(mode == "sms")

    def _on_send_sms(self):
        """点击"获取验证码"按钮：校验输入、调用 SMS 接口、启动倒计时"""
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
        # 不设 AlignCenter：垂直居中会把各区块挤压在一起，
        # 改为自上而下自然排列，末尾补弹性空间
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(14)

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
        info_frame.setStyleSheet("QFrame { background: #f1f3f4; border-radius: 12px; }")
        info_layout = QVBoxLayout(info_frame)
        info_layout.setContentsMargins(16, 16, 16, 16)
        info_layout.setSpacing(10)

        money_label = QLabel(f"余额: {money} 元")
        money_label.setStyleSheet("font-size: 28px; font-weight: 700; color: #f9ab00;")
        money_label.setAlignment(Qt.AlignCenter)
        money_label.setMinimumHeight(44)
        money_label.setWordWrap(False)

        card_label = QLabel(f"交通卡号: {card_no}") if card_no else QLabel("")
        card_label.setAlignment(Qt.AlignCenter)
        card_label.setStyleSheet("font-size: 14px; color: #5f6368;")

        # deadline 来自接口，可能是字符串或非数字，转换失败时降级为不显示
        try:
            deadline_text = (f"有效期至: "
                             f"{time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(int(deadline)))}"
                             ) if deadline else ""
        except (ValueError, TypeError, OSError, OverflowError):
            deadline_text = f"有效期至: {deadline}" if deadline else ""
        deadline_label = QLabel(deadline_text)
        deadline_label.setAlignment(Qt.AlignCenter)
        deadline_label.setStyleSheet("font-size: 14px; color: #5f6368;")

        info_layout.addWidget(money_label)
        info_layout.addWidget(card_label)
        info_layout.addWidget(deadline_label)

        coupon_frame = QFrame()
        coupon_frame.setStyleSheet("QFrame { background: #f1f3f4; border-radius: 12px; }")
        coupon_layout = QVBoxLayout(coupon_frame)
        coupon_layout.setContentsMargins(16, 16, 16, 16)
        coupon_layout.setSpacing(10)

        coupon_title = QLabel("地铁优惠券")
        coupon_title.setAlignment(Qt.AlignCenter)
        coupon_title.setStyleSheet("font-size: 16px; font-weight: 600; color: #1f1f1f;")
        coupon_title.setMinimumHeight(28)
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
        self.coupon_content_layout.setContentsMargins(0, 0, 0, 0)

        # 优惠券列表可能很多条，放进滚动区，避免把窗口撑爆或被挤压截断
        coupon_scroll = QScrollArea()
        coupon_scroll.setWidgetResizable(True)
        coupon_scroll.setFrameShape(QFrame.NoFrame)
        coupon_scroll.setMinimumHeight(150)
        coupon_scroll.setStyleSheet(
            "QScrollArea { background: transparent; border: none; }"
            "QScrollBar:vertical { background: transparent; width: 8px; margin: 0; }"
            "QScrollBar::handle:vertical { background: #dadce0; border-radius: 4px; min-height: 24px; }"
            "QScrollBar::handle:vertical:hover { background: #bdc1c6; }"
            "QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical { height: 0; }"
        )
        coupon_scroll.setWidget(self.coupon_content_frame)
        coupon_layout.addWidget(coupon_scroll)

        close_btn = QPushButton("关闭")
        close_btn.setMinimumHeight(44)
        close_btn.setStyleSheet(
            "QPushButton { background: #1a73e8; color: #fff; border: none; border-radius: 22px; font-weight: 600; font-size: 15px; }"
            "QPushButton:hover { background: #1765cc; border-radius: 22px; }"
            "QPushButton:pressed { background: #185abc; border-radius: 22px; }"
        )
        close_btn.clicked.connect(self.accept)

        # 剩余空间给优惠券区
        layout.addWidget(qr_label)
        layout.addWidget(info_frame)
        layout.addWidget(coupon_frame, 1)
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
        # 配置值理论上已校验过，这里再兜一层，避免脏数据让任务线程启动即崩
        self.run_count = safe_int(run_count, 10)
        try:
            self.time_sleep = float(time_sleep)
        except (ValueError, TypeError):
            self.time_sleep = 0.2
        self.running = True

    def run(self):
        """线程入口：设置线程本地参数 → 等待目标时间 → 执行兑换任务"""
        try:
            from datetime import datetime

            # 使用线程本地上下文，多账号并发时互不干扰
            AutoTicket.set_thread_context(
                login_name=self.login_name,
                user_id=self.user_id,
                ses_id=self.ses_id,
                exchange_id=self.exchange_id,
                log_cb=self.log_signal.emit,
            )

            run_time = datetime.strptime(self.run_time_str, "%Y-%m-%d %H:%M:%S")

            self.log_signal.emit(f"程序已启动，将在 {run_time} 执行兑换任务，共执行 {self.run_count} 次。")
            self.log_signal.emit("正在同步服务器时间...")

            # 与小程序版一致：同步服务器时间并计算本地偏移，避免本地时钟偏差错过抢票时机
            offset = AutoTicket.sync_time_offset()
            self.wait_until_target(run_time, offset)
            if self.running:
                # 显式传入 run_count / time_sleep，避免并发时全局变量被其他账号覆盖
                AutoTicket.job(run_count=self.run_count, time_sleep=self.time_sleep)
        except Exception as e:
            self.log_signal.emit(f"任务执行出错: {str(e)}")
        finally:
            AutoTicket.clear_thread_context()
            self.finished_signal.emit()

    def wait_until_target(self, run_time, offset=0.0):
        """等待直到目标时间（按服务器时间偏移校正）。

        远距离时每 1 秒醒一次检查停止标志（保证停止/退出程序能及时响应），
        接近目标时逐步加密到 50 毫秒，保证抢票时机精度。
        """
        from datetime import datetime, timedelta

        while self.running:
            now = datetime.now() + timedelta(seconds=offset)
            if now >= run_time:
                return

            diff = (run_time - now).total_seconds()
            if diff > 60:
                sleep_time = 1.0
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
    # 携带本次任务是否真正成功（当天已签到也算成功）
    result_signal = pyqtSignal(bool)

    def __init__(self, login_name, user_id, ses_id, exchange_id):
        super().__init__()
        self.login_name = login_name
        self.user_id = user_id or login_name
        self.ses_id = ses_id
        self.exchange_id = exchange_id
        self.success = False

    def run(self):
        """线程入口：设置线程本地参数并执行每日任务工作流"""
        try:
            AutoTicket.set_thread_context(
                login_name=self.login_name,
                user_id=self.user_id,
                ses_id=self.ses_id,
                exchange_id=self.exchange_id,
                log_cb=self.log_signal.emit,
            )
            self.success = bool(AutoTicket.daily_task_workflow())
        except Exception as e:
            self.success = False
            self.log_signal.emit(f"执行每日任务时出错: {str(e)}")
        finally:
            AutoTicket.clear_thread_context()
            try:
                self.result_signal.emit(self.success)
            except Exception:
                pass
            self.finished_signal.emit()

class StatsPoller(QThread):
    """统计数据轮询线程：定时拉取在线人数与抢票数，纯展示用，失败静默忽略

    服务端在线数是滑动窗口（2 分钟内有心跳才算在线），所以每轮
    先给所有已登录账号发一次 open 刷新心跳，再拉取统计，
    否则自己会掉出在线列表。多账号各自一条在线记录。
    """

    stats_signal = pyqtSignal(dict)
    # 拉取失败时发出，用于隐藏统计面板（显示全 0 比不显示更误导）
    stats_failed_signal = pyqtSignal()

    def __init__(self, interval=60, account_keys_provider=None):
        super().__init__()
        self.interval = interval
        self.running = True
        # 回调：返回当前所有已登录账号的统计标识
        self.account_keys_provider = account_keys_provider

    def run(self):
        """线程入口：立即拉取一次，之后每隔 interval 秒拉取一次"""
        while self.running:
            try:
                keys = []
                if self.account_keys_provider:
                    try:
                        keys = self.account_keys_provider() or []
                    except Exception:
                        keys = []
                if keys:
                    for key in keys:
                        if not self.running:
                            return
                        stats_client.report_online("open", key)
                else:
                    # 尚未登录任何账号：用设备级标识占位
                    stats_client.report_online("open")
            except Exception:
                pass
            data = stats_client.fetch_stats()
            if data:
                self.stats_signal.emit(data)
            else:
                # 连不上服务端：通知界面隐藏面板
                try:
                    self.stats_failed_signal.emit()
                except Exception:
                    pass
            # 分片休眠，便于关闭软件时快速退出
            for _ in range(int(self.interval * 2)):
                if not self.running:
                    return
                time.sleep(0.5)

    def stop(self):
        """请求线程停止"""
        self.running = False


class AccountSlotWidget(QFrame):
    """单个账号槽位：圆形头像 + 右侧信息面板 + 悬停红叉退出"""
    slot_clicked = pyqtSignal(int)
    slot_closed = pyqtSignal(int)

    def __init__(self, index, parent=None):
        super().__init__(parent)
        self.index = index
        self.is_logged_in = False
        self.setFixedSize(218, 76)
        self.setCursor(Qt.PointingHandCursor)

        outer = QHBoxLayout(self)
        outer.setContentsMargins(10, 6, 10, 6)
        outer.setSpacing(10)

        # 头像容器（用于绝对定位红叉）
        avatar_box = QFrame()
        avatar_box.setFixedSize(64, 64)

        self.avatar_btn = QPushButton()
        self.avatar_btn.setParent(avatar_box)
        self.avatar_btn.setFixedSize(64, 64)
        self.avatar_btn.setGeometry(0, 0, 64, 64)
        self.avatar_btn.setCursor(Qt.PointingHandCursor)
        self.avatar_btn.clicked.connect(lambda: self.slot_clicked.emit(self.index))

        # 红叉退出按钮（默认隐藏）
        self.close_btn = QPushButton("\u00d7")
        self.close_btn.setParent(avatar_box)
        self.close_btn.setFixedSize(20, 20)
        self.close_btn.setGeometry(42, 0, 20, 20)
        self.close_btn.setCursor(Qt.PointingHandCursor)
        self.close_btn.setStyleSheet(
            "background-color: #F56C6C; color: #ffffff; "
            "border-radius: 10px; border: 2px solid #ffffff; "
            "font-size: 13px; font-weight: bold; padding: 0;"
        )
        self.close_btn.setVisible(False)
        self.close_btn.clicked.connect(lambda: self.slot_closed.emit(self.index))

        # 右侧信息面板
        info = QVBoxLayout()
        info.setSpacing(4)
        info.setContentsMargins(0, 0, 0, 0)

        self.name_label = QLabel("")
        self.name_label.setStyleSheet("font-size: 14px; font-weight: 600; color: #1f1f1f;")

        self.task_label = QLabel("")
        self.task_label.setStyleSheet("font-size: 12px; color: #5f6368;")

        self.status_label = QLabel("")
        self.status_label.setStyleSheet("font-size: 11px; font-weight: 600;")

        info.addWidget(self.name_label)
        info.addWidget(self.task_label)
        info.addWidget(self.status_label)

        outer.addWidget(avatar_box)
        outer.addLayout(info)
        outer.addStretch(1)

    def enterEvent(self, event):
        if self.is_logged_in:
            self.close_btn.setVisible(True)
        super().enterEvent(event)

    def set_active_style(self, active):
        """选中态：给整个槽位加蓝色描边 + 浅蓝背景，让人一眼看出当前操作哪个账号"""
        if active:
            self.setStyleSheet(
                "AccountSlotWidget {"
                " background: rgba(26, 115, 232, 0.08);"
                " border: 2px solid #1a73e8;"
                " border-radius: 12px;"
                "}"
            )
        else:
            self.setStyleSheet(
                "AccountSlotWidget {"
                " background: transparent;"
                " border: 2px solid transparent;"
                " border-radius: 12px;"
                "}"
            )

    def leaveEvent(self, event):
        self.close_btn.setVisible(False)
        super().leaveEvent(event)

    def mousePressEvent(self, event):
        # 点击信息面板区域也触发切换/登录（头像和红叉各自处理自己的点击，不会冒泡到这里）
        if event.button() == Qt.LeftButton:
            self.slot_clicked.emit(self.index)
        super().mousePressEvent(event)


class MainWindow(QWidget):
    """主窗口，包含登录、配置参数、启动/停止任务、日志展示及绿色出行码等功能"""

    def __init__(self):
        super().__init__()
        self.workers = {}              # profile_id -> Worker（多账号并发任务）
        self.daily_task_workers = {}   # profile_id -> DailyTaskWorker
        self._stopped_pids = set()     # 被手动停止的 profile_id（用于区分"执行完成"和"已停止"）
        self.stats_poller = None
        self.stats_group = None
        self.config_file = "./config.json"
        self.loading_config = False

        # 多开 Profile 管理
        self.max_profiles = 3
        self.profiles = []           # Profile 列表
        self.active_profile_index = 0  # 当前选中的 Profile 索引
        self.profile_slots = []      # 3个固定槽位（init_ui 中创建）

        # 兼容旧版的单账号字段（会被 Profile 数据覆盖）
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

    # ==================== Profile 属性访问 ====================
    @property
    def current_profile(self):
        """获取当前选中的 Profile，无则返回 None"""
        if 0 <= self.active_profile_index < len(self.profiles):
            return self.profiles[self.active_profile_index]
        return None

    def _get_profile_auth(self, profile=None):
        """获取指定 Profile 的 auth 字典，默认当前 Profile"""
        p = profile or self.current_profile
        return p.get('auth', {}) if p else {}

    def _get_profile_config(self, profile=None):
        """获取指定 Profile 的 config 字典，默认当前 Profile"""
        p = profile or self.current_profile
        return p.get('config', {}) if p else {}

    def _get_profile_state(self, profile=None):
        """获取指定 Profile 的 state 字典，默认当前 Profile"""
        p = profile or self.current_profile
        return p.get('state', {}) if p else {}

    def init_ui(self):
        """初始化界面：创建登录区域、配置参数区域、按钮区域和日志展示区域"""
        self.setObjectName("mainWindow")
        self.setWindowTitle(f'AutoTicket {updater.CURRENT_VERSION} - 免费开源使用')
        self.setWindowIcon(QIcon(os.path.join(os.path.dirname(__file__), "icon.ico")))
        self.setGeometry(100, 100, 780, 980)
        self.setMinimumSize(760, 940)

        # 创建顶部登录状态区域（账号槽位 + 圆头像 + 用户名 + 状态标签）
        auth_group = QGroupBox("登录")
        auth_outer_layout = QVBoxLayout()
        auth_outer_layout.setContentsMargins(20, 20, 20, 20)
        auth_outer_layout.setSpacing(12)

        # 小程序宣传提示
        mini_program_label = QLabel("小程序 e家AutoTicket 已上线，手机端即可使用")
        mini_program_label.setStyleSheet("font-size: 13px; color: #5f6368;")
        auth_outer_layout.addWidget(mini_program_label)

        # 3个账号槽位（水平排列）
        accounts_row = QHBoxLayout()
        accounts_row.setSpacing(10)
        self.profile_slots = []
        for i in range(self.max_profiles):
            widget = AccountSlotWidget(i, self)
            widget.slot_clicked.connect(self._on_slot_clicked)
            widget.slot_closed.connect(self._on_slot_closed)
            accounts_row.addWidget(widget)
            self.profile_slots.append(widget)

        auth_outer_layout.addLayout(accounts_row)
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

        # 创建日志显示区域
        log_group = QGroupBox("运行日志")
        log_layout = QVBoxLayout()
        log_layout.setContentsMargins(20, 26, 20, 20)
        log_layout.setSpacing(12)
        self.log_display = QTextEdit()
        self.log_display.setObjectName("logPanel")
        self.log_display.setReadOnly(True)
        # 日志区可伸缩：窗口变大时优先给日志，避免内容被截断
        self.log_display.setMinimumHeight(180)
        self.log_display.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
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
        # 日志区占据剩余空间（拉伸因子 1），其他控件固定高度
        main_layout.addWidget(log_group, 1)
        self.setLayout(main_layout)

        # 连接信号和槽
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
        """判断当前 Profile 是否处于有效登录状态"""
        auth = self._get_profile_auth()
        return auth.get('is_logged_in', False) and bool(auth.get('login_name')) and bool(auth.get('ses_id'))

    def get_logged_in_account_keys(self):
        """收集所有已登录账号的统计标识（用于在线人数按账号计数）。

        服务端按 client_id 去重，同一台机器跑多个账号时若共用一个标识，
        在线人数永远只有 1。这里给每个账号返回独立标识。
        """
        keys = []
        for profile in self.profiles:
            auth = profile.get('auth') or {}
            if not (auth.get('is_logged_in') and auth.get('login_name') and auth.get('ses_id')):
                continue
            # 优先 user_id（稳定），回退 login_name
            key = (auth.get('user_id') or auth.get('login_name') or '').strip()
            if key and key not in keys:
                keys.append(key)
        return keys

    def verify_session(self):
        """调用 U005 验证当前 Profile 的 ses_id 是否仍有效，若失效则清除登录状态。"""
        auth = self._get_profile_auth()
        login_name = auth.get('login_name', '').strip()
        ses_id = auth.get('ses_id', '').strip()
        if not login_name or not ses_id:
            return False

        try:
            user_info = Login.query_user_info(login_name, ses_id)
            if user_info and user_info.get("result") == "0":
                name = user_info.get("name") or user_info.get("sensitive_name", "")
                if name:
                    auth['display_name'] = name  # 更新显示名称
                    self.user_name = name
                self.remain_integral = safe_int(user_info.get("remain_integral", 0))
                self.save_config()  # 保存更新后的 Profile
                self.update_profile_tabs()  # 刷新槽位：显示最新积分/姓名
                self.refresh_login_state()
                return True
            else:
                self.update_log("登录会话已失效，请重新登录")
                self._clear_login_state()
                self.save_config()
                self.refresh_login_state()
                QMessageBox.warning(self, "登录已失效", "登录会话已失效，请重新登录。")
                return False
        except Exception as e:
            self.update_log(f"验证登录状态时出错: {e}")
            self._clear_login_state()
            self.save_config()
            self.refresh_login_state()
            QMessageBox.warning(self, "登录已失效", "验证登录状态时出错，请重新登录。")
            return False

    def _clear_login_state(self):
        """清除当前 Profile 的登录状态并刷新槽位显示"""
        auth = self._get_profile_auth()
        auth['is_logged_in'] = False
        auth['user_id'] = ''
        auth['login_name'] = ''
        auth['ses_id'] = ''
        auth['display_name'] = ''
        auth['remain_integral'] = 0
        self.is_logged_in = False
        self.user_id = ""
        self.user_name = ""
        self.remain_integral = 0
        AutoTicket.LOGIN_NAME_PLAINTEXT = ""
        AutoTicket.USER_ID_PLAINTEXT = ""
        AutoTicket.SES_ID = ""
        # 刷新槽位：登录态清除后该槽位显示"点击登录"
        if self.profile_slots:
            self.update_profile_tabs()

    def refresh_login_state(self):
        """根据登录状态刷新按钮，并把焦点交还主窗口"""
        logged_in = self.has_valid_login()
        self.qr_code_button.setEnabled(logged_in)
        self._refresh_task_buttons()
        # 登录/退出对话框关闭后焦点会残留在已销毁的窗口上，
        # 这里主动把焦点抢回来，避免之后快捷键、输入都失效
        try:
            if self.isVisible():
                self.activateWindow()
                self.raise_()
                self.setFocus()
        except Exception:
            pass

    # ==================== 多开 Profile 管理 ====================
    def add_profile(self):
        """新建账号 Profile"""
        if len(self.profiles) >= self.max_profiles:
            QMessageBox.information(self, "提示", f"最多只能创建 {self.max_profiles} 个账号")
            return

        new_profile = {
            'id': f'profile_{len(self.profiles) + 1}_{int(time.time())}',
            'name': f'账号{len(self.profiles) + 1}',
            'auth': {'login_name': '', 'user_id': '', 'ses_id': '', 'is_logged_in': False, 'display_name': '', 'remain_integral': 0},
            'config': {
                'exchange_id': '10',
                'run_time': self.get_next_run_time(),
                'run_count': '10',
                'time_sleep': '0.2'
            },
            'state': {'running': False, 'daily_task_done': False, 'daily_task_done_date': ''}
        }
        self.profiles.append(new_profile)
        self.active_profile_index = len(self.profiles) - 1
        self.update_profile_tabs()
        self.sync_ui_from_profile()
        self.save_config()
        self.update_log(f"已创建 {new_profile['name']}，请登录")

    def delete_profile(self, index):
        """删除指定 Profile"""
        if index < 0 or index >= len(self.profiles):
            return
        if index == self.active_profile_index:
            QMessageBox.warning(self, "无法删除", "不能删除当前选中的账号")
            return

        profile = self.profiles[index]
        reply = QMessageBox.question(
            self, "删除账号",
            f"确定删除 {profile['name']} 吗？此操作不可恢复。",
            QMessageBox.Yes | QMessageBox.No
        )
        if reply != QMessageBox.Yes:
            return

        # 该账号有任务在跑则不能删除
        pid = profile.get('id')
        if pid in self.workers or pid in self.daily_task_workers:
            QMessageBox.warning(self, "无法删除", "该账号有任务正在运行，请先停止后再删除。")
            return

        self.profiles.pop(index)
        if self.active_profile_index >= len(self.profiles):
            self.active_profile_index = max(0, len(self.profiles) - 1)
        self.update_profile_tabs()
        self.sync_ui_from_profile()
        self.save_config()
        self.update_log(f"已删除 {profile['name']}")

    def switch_profile(self, index):
        """切换到指定 Profile"""
        if index < 0 or index >= len(self.profiles):
            return
        if index == self.active_profile_index:
            return

        self.active_profile_index = index
        self.update_profile_tabs()
        self.sync_ui_from_profile()
        self._refresh_task_buttons()
        self.update_log(f"已切换到 {self.profiles[index]['name']}")

        # 切换后若该账号已登录，后台验证会话并刷新积分/姓名
        auth = self._get_profile_auth()
        if auth.get('is_logged_in') and auth.get('login_name') and auth.get('ses_id'):
            QTimer.singleShot(100, self.verify_session)

    def update_profile_tabs(self):
        """更新3个账号槽位：已登录显示头像+信息+状态，未登录显示+号"""
        from datetime import date

        for i, widget in enumerate(self.profile_slots):
            has_profile = i < len(self.profiles)
            is_active = has_profile and i == self.active_profile_index
            auth = self._get_profile_auth(self.profiles[i]) if has_profile else {}
            is_logged_in = auth.get('is_logged_in', False)
            widget.is_logged_in = is_logged_in
            # 选中态：整块加蓝色描边 + 浅蓝底，明确当前操作的是哪个账号
            widget.set_active_style(is_active)

            if is_logged_in:
                profile = self.profiles[i]
                state = self._get_profile_state(profile)
                name = auth.get('display_name') or auth.get('login_name') or profile.get('name', f'账号{i+1}')
                first = name[0] if name else '用'
                integral = safe_int(auth.get('remain_integral', 0))

                # 头像样式
                if is_active:
                    widget.avatar_btn.setStyleSheet(
                        "background: #1a73e8; color: #ffffff; "
                        "border: 2px solid #1a73e8; border-radius: 32px; "
                        "font-size: 22px; font-weight: 700; padding: 0;"
                    )
                else:
                    widget.avatar_btn.setStyleSheet(
                        "background: rgba(26, 115, 232, 0.10); color: #1a73e8; "
                        "border: 2px solid #1a73e8; border-radius: 32px; "
                        "font-size: 22px; font-weight: 700; padding: 0;"
                    )
                widget.avatar_btn.setText(first)

                # 第一行：名称 | 积分（积分绿色）
                if integral > 0:
                    widget.name_label.setText(f'{name} <span style="color:#67C23A;">| {integral}分</span>')
                else:
                    widget.name_label.setText(name)
                widget.name_label.setStyleSheet("font-size: 13px; font-weight: 600; color: #1f1f1f;")

                # 第二行：每日任务完成情况
                today = date.today().isoformat()
                daily_done = state.get('daily_task_done_date', '') == today
                if daily_done:
                    widget.task_label.setText("✅ 任务完成")
                    widget.task_label.setStyleSheet("font-size: 11px; color: #1e8e3e;")
                else:
                    widget.task_label.setText("❌ 任务未完成")
                    widget.task_label.setStyleSheet("font-size: 11px; color: #9aa0a6;")

                # 第三行：运行状态（该账号有存活的工作线程即显示运行中，与是否选中无关）
                profile_running = self.profiles[i].get('id') in self.workers
                if profile_running:
                    widget.status_label.setText("● 运行中")
                    widget.status_label.setStyleSheet("font-size: 10px; font-weight: 600; color: #67C23A;")
                else:
                    widget.status_label.setText("● 未运行")
                    widget.status_label.setStyleSheet("font-size: 10px; font-weight: 600; color: #E6A23C;")
            else:
                # 未登录或空槽位
                widget.avatar_btn.setText("+")
                widget.avatar_btn.setStyleSheet(
                    "background: #ffffff; color: #9aa0a6; "
                    "border: 2px dashed #dadce0; border-radius: 32px; "
                    "font-size: 22px; font-weight: 400; padding: 0;"
                    "\nQPushButton:hover {"
                    "background: rgba(26, 115, 232, 0.04); color: #1a73e8; "
                    "border-color: #1a73e8;"
                    "}"
                )
                widget.name_label.setText(f"账号{i+1}")
                widget.name_label.setStyleSheet("font-size: 13px; color: #9aa0a6;")
                widget.task_label.setText("")
                widget.status_label.setText("")

    def _on_slot_clicked(self, index):
        """点击槽位：已登录则切换；未登录/空槽位则切换(或新建)后直接弹登录框"""
        if index < len(self.profiles):
            if index != self.active_profile_index:
                self.switch_profile(index)
        else:
            self.add_profile()

        # 当前槽位未登录 → 直接弹出登录框
        if not self.has_valid_login():
            self.login()

    def _on_slot_closed(self, index):
        """点击头像红叉：切换到该账号并退出登录"""
        if index < len(self.profiles):
            if index != self.active_profile_index:
                self.switch_profile(index)
            self.logout()

    def _show_profile_context_menu(self, index, pos):
        """显示槽位右键菜单（仅对有账号且非当前的槽位提供删除）"""
        if index >= len(self.profiles):
            return
        if index == self.active_profile_index:
            return  # 当前选中的不能删除

        from PyQt5.QtWidgets import QMenu
        menu = QMenu(self)
        delete_action = menu.addAction("删除此账号")
        action = menu.exec_(self.profile_slots[index].mapToGlobal(pos))
        if action == delete_action:
            self.delete_profile(index)

    def sync_ui_from_profile(self):
        """从当前 Profile 加载数据到 UI（阻止表单信号触发反向同步）"""
        p = self.current_profile
        if not p:
            return

        auth = self._get_profile_auth(p)
        config = self._get_profile_config(p)
        state = self._get_profile_state(p)

        # 阻止表单信号触发（避免 setText 触发 textChanged → save_config）
        self.loading_config = True

        try:
            # 更新内部状态
            self.is_logged_in = auth.get('is_logged_in', False)
            self.user_id = auth.get('user_id', '')
            self.user_name = auth.get('display_name', '') or auth.get('login_name', '')
            self.remain_integral = safe_int(auth.get('remain_integral', 0))
            self.daily_task_done_date = state.get('daily_task_done_date', '')

            # 同步到 AutoTicket 全局变量（供任务使用）
            AutoTicket.LOGIN_NAME_PLAINTEXT = auth.get('login_name', '')
            AutoTicket.USER_ID_PLAINTEXT = auth.get('user_id', '')
            AutoTicket.SES_ID = auth.get('ses_id', '')

            # 更新表单
            self.login_name_edit.setText(auth.get('login_name', ''))
            self.ses_id_edit.setText(auth.get('ses_id', ''))

            # 更新下拉框
            exchange_id = config.get('exchange_id', '10')
            idx = self.exchange_id_edit.findData(exchange_id)
            if idx >= 0:
                self.exchange_id_edit.setCurrentIndex(idx)

            self.run_count_edit.setText(config.get('run_count', '10'))
            self.time_sleep_edit.setText(config.get('time_sleep', '0.2'))
        finally:
            self.loading_config = False

        # 刷新登录状态显示
        self.refresh_login_state()

    def sync_profile_from_ui(self):
        """将 UI 数据保存回当前 Profile"""
        p = self.current_profile
        if not p:
            return

        auth = self._get_profile_auth(p)
        config = self._get_profile_config(p)
        state = self._get_profile_state(p)

        # 更新 auth
        auth['login_name'] = self.login_name_edit.text().strip()
        auth['ses_id'] = self.ses_id_edit.text().strip()
        auth['user_id'] = self.user_id
        auth['is_logged_in'] = self.is_logged_in
        auth['remain_integral'] = self.remain_integral

        # 更新 config
        config['exchange_id'] = self.exchange_id_edit.currentData()
        config['run_count'] = self.run_count_edit.text()
        config['time_sleep'] = self.time_sleep_edit.text()

        # 更新 state
        state['daily_task_done_date'] = self.daily_task_done_date

        # 如果用户名是默认的"账号N"，更新为登录名
        if p['name'].startswith('账号') and auth.get('login_name'):
            new_name = auth['login_name'][:1] + '**'  # 脱敏
            if p['name'] != new_name:
                p['name'] = new_name
                self.update_profile_tabs()  # 名称变了才刷新 Tab

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
        """统计服务已配置时显示统计面板，启动轮询（轮询里自带各账号心跳）

        面板是否可见由服务端的 stats_enabled 开关决定，
        首次轮询拿到结果后会自动校正（见 update_stats_display）。
        """
        if not stats_client.is_enabled():
            self.stats_group.setVisible(False)
            return

        # 先隐藏：等第一次轮询拿到服务端开关再决定，避免启动时闪出全 0 面板
        self.stats_group.setVisible(False)
        self.stats_poller = StatsPoller(60, account_keys_provider=self.get_logged_in_account_keys)
        self.stats_poller.stats_signal.connect(self.update_stats_display)
        self.stats_poller.stats_failed_signal.connect(self.hide_stats_panel)
        self.stats_poller.start()

    def hide_stats_panel(self):
        """拉取统计失败时隐藏面板：全 0 的统计比不显示更误导"""
        try:
            self.stats_group.setVisible(False)
        except Exception:
            pass

    def update_stats_display(self, data):
        """把拉取到的统计数据刷新到卡片上，并按服务端开关控制面板显隐"""
        try:
            # 服务端开关：False 时隐藏整个实时统计模块
            enabled = data.get("stats_enabled", True) is not False
            if self.stats_group.isVisible() != enabled:
                self.stats_group.setVisible(enabled)

            if not enabled:
                return

            self.stat_labels["online"].setText(str(data.get("online", 0)))
            by_type = data.get("by_type") or {}
            for key in ("9", "10", "11"):
                self.stat_labels[key].setText(str(by_type.get(key, 0)))
        except Exception:
            pass

    def closeEvent(self, event):
        """关闭窗口：停止后台线程、等待退出、保存配置并上报下线"""
        try:
            self.save_config()
        except Exception:
            pass
        try:
            # 1. 停止所有可停止的线程
            if self.stats_poller:
                self.stats_poller.stop()
            for w in list(self.workers.values()):
                w.stop()

            # 2. 等待抢票线程退出（休眠粒度 ≤1s，stop 后 ≤1s 退出）
            for w in list(self.workers.values()):
                w.wait(3000)

            # 3. 等待每日任务线程（工作流含多次网络调用+间隔，最长约 10s）
            for w in list(self.daily_task_workers.values()):
                w.wait(10000)

            # 4. 等待统计轮询线程退出（fetch_stats 是网络请求）
            if self.stats_poller:
                self.stats_poller.wait(5000)

            # 5. 等待更新检查线程退出（requests.get timeout=10s）
            if hasattr(self, 'updater') and self.updater:
                self.updater.wait(15000)
        except Exception:
            pass

        # 上报下线（超时 1 秒，失败不影响退出）
        try:
            if stats_client.is_enabled():
                keys = self.get_logged_in_account_keys()
                if keys:
                    for key in keys:
                        stats_client.report_offline(key)
                else:
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

            # 更新当前 Profile 的 auth
            auth = self._get_profile_auth()
            auth['login_name'] = login_name
            auth['user_id'] = login_result.get("user_id") or login_name
            auth['ses_id'] = ses_id
            auth['is_logged_in'] = True

            # 更新内部状态
            self.user_id = auth['user_id']
            self.is_logged_in = True

            # 更新 AutoTicket 全局变量
            AutoTicket.LOGIN_NAME_PLAINTEXT = login_name
            AutoTicket.USER_ID_PLAINTEXT = auth['user_id']
            AutoTicket.SES_ID = ses_id

            # 更新表单（阻止 textChanged 触发 save_config）
            self.loading_config = True
            try:
                self.login_name_edit.setText(login_name)
                self.ses_id_edit.setText(ses_id)
            finally:
                self.loading_config = False

            # 登录成功后立即查询用户信息，获取真实姓名
            try:
                user_info = Login.query_user_info(login_name, ses_id)
                if user_info and user_info.get("result") == "0":
                    self.user_name = user_info.get("name") or user_info.get("sensitive_name", "")
                    auth['display_name'] = self.user_name  # 更新显示名称
                    self.remain_integral = safe_int(user_info.get("remain_integral", 0))
                    self.update_log(f"欢迎, {self.user_name}  当前积分: {self.remain_integral}")
                else:
                    self.user_name = ""
                    self.remain_integral = 0
            except Exception:
                self.user_name = ""
                self.remain_integral = 0

            self.save_config()
            self.update_profile_tabs()  # 更新 Tab 显示
            self.refresh_login_state()   # 内部会把焦点交还主窗口
            self.update_log("登录成功，已自动填入 login_name 和 ses_id")
            QMessageBox.information(self, "登录成功", "登录成功，已自动填入 login_name 和 ses_id。")
        except Exception as e:
            QMessageBox.warning(self, "登录失败", str(e))
            self.update_log(f"登录失败: {str(e)}")
            self.refresh_login_state()

    def logout(self):
        """退出登录：清空当前 Profile 的登录信息并重置状态"""
        pid = self.current_profile.get('id') if self.current_profile else None
        if pid in self.workers or pid in self.daily_task_workers:
            QMessageBox.warning(self, "无法退出登录", "请先停止当前账号的任务后再退出登录。")
            return

        # 只清除当前 Profile 的登录态
        auth = self._get_profile_auth()
        auth['is_logged_in'] = False
        auth['user_id'] = ''
        auth['login_name'] = ''
        auth['ses_id'] = ''
        auth['display_name'] = ''
        auth['remain_integral'] = 0

        state = self._get_profile_state()
        state['daily_task_done'] = False
        state['daily_task_done_date'] = ''

        # 重置内部状态
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
        self.update_profile_tabs()  # 刷新槽位：退出后显示"点击登录"
        self.refresh_login_state()
        self.update_log("已退出登录")
        QMessageBox.information(self, "退出登录", "已清除当前账号的登录状态。")

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
        """启动当前账号的定时兑换任务（各账号独立运行，互不干扰）"""
        p = self.current_profile
        if not p:
            return
        profile_id = p.get('id')
        if profile_id in self.workers:
            QMessageBox.information(self, "提示", "该账号任务已在运行中。")
            return

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

        # 更新当前 Profile 状态
        state = self._get_profile_state()
        state['running'] = True

        # 绑定当前账号名，任务期间即使切换账号，该任务的日志仍归属原账号
        auth = self._get_profile_auth()
        task_owner = auth.get('display_name') or auth.get('login_name') or '未知'
        worker_logger = lambda msg: self.update_log(msg, prefix_name=task_owner)

        worker = Worker(login_name, user_id, ses_id, exchange_id, run_time_str, run_count, time_sleep)
        worker.log_signal.connect(worker_logger)
        # 回调中携带 profile_id，任务结束时清理对应槽位
        worker.finished_signal.connect(lambda pid=profile_id: self.program_finished(pid))
        self.workers[profile_id] = worker
        worker.start()

        self.update_profile_tabs()
        self._refresh_task_buttons()
        self.update_log("程序启动中...")

    def stop_program(self):
        """停止当前账号的兑换任务（不影响其他账号）

        注意：只置停止标志，不从 self.workers 移除——工作线程可能还在休眠循环中，
        提前丢弃引用会导致 "QThread: Destroyed while thread is still running" 崩溃。
        线程退出后由 program_finished 统一清理。
        """
        p = self.current_profile
        if not p:
            return
        profile_id = p.get('id')
        worker = self.workers.get(profile_id)
        if worker:
            self._stopped_pids.add(profile_id)
            worker.stop()

        state = self._get_profile_state()
        state['running'] = False
        self.update_profile_tabs()
        self._refresh_task_buttons()
        self.update_log("程序已停止")

    def execute_daily_task(self):
        """执行当前账号的每日任务完整工作流：登录→3次签到→评论→查询积分"""
        p = self.current_profile
        if not p:
            return
        profile_id = p.get('id')
        if profile_id in self.daily_task_workers:
            QMessageBox.information(self, "提示", "该账号每日任务正在执行中。")
            return

        login_name = self.login_name_edit.text()
        ses_id = self.ses_id_edit.text()
        exchange_id = self.exchange_id_edit.currentData()
        user_id = self.get_current_user_id(login_name)

        if not all([login_name, ses_id]):
            QMessageBox.warning(self, "输入错误", "LOGIN_NAME和SES_ID字段必须填写！")
            return

        # 绑定当前账号名，任务期间即使切换账号，日志仍归属原账号
        auth = self._get_profile_auth()
        task_owner = auth.get('display_name') or auth.get('login_name') or '未知'
        daily_logger = lambda msg: self.update_log(msg, prefix_name=task_owner)
        worker = DailyTaskWorker(login_name, user_id, ses_id, exchange_id)
        worker.log_signal.connect(daily_logger)
        worker.finished_signal.connect(lambda pid=profile_id: self.daily_task_finished(pid))
        self.daily_task_workers[profile_id] = worker
        worker.start()
        self._refresh_task_buttons()

    def daily_task_finished(self, profile_id=None):
        """每日任务完成后的回调：等待线程退出后清理并更新对应 Profile"""
        if profile_id is None:
            profile_id = self.current_profile.get('id') if self.current_profile else None
        worker = self.daily_task_workers.pop(profile_id, None)
        if worker:
            # 等待线程真正退出，避免 QThread 销毁时仍在运行导致崩溃
            worker.wait(5000)

        # 找到对应 profile 更新状态（可能不是当前选中的）
        target = None
        for p in self.profiles:
            if p.get('id') == profile_id:
                target = p
                break
        # 只有真正成功才标记完成（当天已签到的情况在 workflow 里已算成功）
        ok = bool(getattr(worker, 'success', False)) if worker else False
        if target:
            state = self._get_profile_state(target)
            state['daily_task_done'] = ok
            if ok:
                state['daily_task_done_date'] = date.today().isoformat()
                if target is self.current_profile:
                    self.daily_task_done_date = state['daily_task_done_date']
            elif target is self.current_profile:
                self.daily_task_done_date = ''

        self.save_config()
        self.update_profile_tabs()  # 刷新槽位：显示"✅ 任务完成"
        owner = (self._get_profile_auth(target).get('display_name') or target.get('name')) if target else None
        self.update_log(
            "每日任务执行完成" if ok else "每日任务未全部成功，请查看上方日志",
            prefix_name=owner,
        )
        self._refresh_task_buttons()

    def update_log(self, message, prefix_name=None):
        """向日志显示区域追加一条带时间戳和账号名的消息

        prefix_name: 可选，指定账号名（用于后台任务日志归属原账号）；
                     缺省时使用当前选中账号的显示名/登录名/账号名。
        抢到票的消息加粗高亮显示。
        """
        timestamp = QDateTime.currentDateTime().toString("yyyy-MM-dd hh:mm:ss")
        if prefix_name:
            name = prefix_name
        else:
            auth = self._get_profile_auth()
            p = self.current_profile
            name = auth.get('display_name') or auth.get('login_name') or (p.get('name', '未登录') if p else '未登录')
        line = f"[{timestamp}] [{name}] {message}"
        if '抢到' in str(message):
            self.log_display.append(f'<b style="color:#67C23A;">{html.escape(line)}</b>')
        else:
            self.log_display.append(line)

    def program_finished(self, profile_id=None):
        """兑换任务完成后的回调：等待线程退出后清理对应账号的线程并刷新显示"""
        if profile_id is None:
            profile_id = self.current_profile.get('id') if self.current_profile else None
        worker = self.workers.pop(profile_id, None)
        if worker:
            # 等待线程真正退出，避免 QThread 销毁时仍在运行导致崩溃
            worker.wait(5000)

        # 找到对应 profile 更新状态
        target = None
        for p in self.profiles:
            if p.get('id') == profile_id:
                target = p
                break
        if target:
            self._get_profile_state(target)['running'] = False

        was_stopped = profile_id in self._stopped_pids
        self._stopped_pids.discard(profile_id)

        self.update_profile_tabs()
        self._refresh_task_buttons()
        if not was_stopped:
            name = (self._get_profile_auth(target).get('display_name') or target.get('name')) if target else None
            self.update_log("程序执行完成", prefix_name=name)

    def _refresh_task_buttons(self):
        """根据当前账号的登录态与任务运行状态刷新按钮"""
        p = self.current_profile
        pid = p.get('id') if p else None
        has_worker = pid in self.workers
        has_daily = pid in self.daily_task_workers
        busy = has_worker or has_daily
        # 未登录就不允许启动，避免点了才弹"所有字段都必须填写"
        logged_in = self.has_valid_login()

        self.start_button.setEnabled(not busy and logged_in)
        self.stop_button.setEnabled(has_worker)
        self.daily_task_button.setEnabled(not busy and logged_in)

    def _apply_active_profile(self):
        """确保总有一个账号被选中：优先已登录的，其次第一个 profile

        程序启动或删除账号后调用，避免出现"没有选中任何账号"导致无法抢票。
        """
        if not self.profiles:
            self.active_profile_index = 0
            return

        if 0 <= self.active_profile_index < len(self.profiles):
            # 当前索引有效，但若该账号未登录、而别的账号已登录，则切到已登录的
            cur_auth = self._get_profile_auth(self.profiles[self.active_profile_index])
            if cur_auth.get('is_logged_in'):
                return
            for i, prof in enumerate(self.profiles):
                auth = prof.get('auth') or {}
                if auth.get('is_logged_in') and auth.get('login_name') and auth.get('ses_id'):
                    self.active_profile_index = i
                    return
            return  # 没有任何已登录账号，保持当前索引

        # 索引越界，回退到第一个
        self.active_profile_index = 0

    def save_config(self):
        """将当前配置保存到本地 config.json 文件（包含所有 Profile）"""
        if self.loading_config:
            return

        # 先同步当前 UI 到 Profile
        self.sync_profile_from_ui()

        config = {
            # 多开 Profile 数据
            "profiles": self.profiles,
            "active_profile_index": self.active_profile_index,
            # 统计相关：匿名标识与服务端地址，避免被本次写入覆盖
            "client_id": stats_client.get_client_id(),
            "stats_api_base": stats_client.get_api_base(),
        }
        # 写盘失败（磁盘满、文件被占用、权限不足）不能闪退，只提示
        try:
            with open(self.config_file, 'w', encoding='utf-8') as f:
                json.dump(config, f, indent=4, ensure_ascii=False)
        except Exception as e:
            try:
                self.update_log(f"保存配置失败：{e}")
            except Exception:
                pass
        self.refresh_login_state()

    def load_config(self):
        """从本地 config.json 加载保存的配置（支持多 Profile 和旧版单账号迁移）

        配置文件损坏（断电、磁盘满、手动编辑出错）时必须能兜底，
        否则 JSONDecodeError 会直接让程序启动即闪退。
        """
        if os.path.exists(self.config_file):
            self.loading_config = True
            try:
                with open(self.config_file, encoding='utf-8') as f:
                    config = json.load(f)
                if not isinstance(config, dict):
                    raise ValueError("配置文件格式不正确（顶层不是对象）")

                # 加载 Profile 列表
                self.profiles = config.get("profiles", [])
                if not isinstance(self.profiles, list):
                    self.profiles = []
                self.active_profile_index = config.get("active_profile_index", 0)
                try:
                    self.active_profile_index = int(self.active_profile_index)
                except (ValueError, TypeError):
                    self.active_profile_index = 0

                # 兼容旧版：如果没有 profiles 但有 login_name，迁移为第一个 Profile
                if not self.profiles and config.get("login_name"):
                    migrated_profile = {
                        'id': 'profile_1',
                        'name': '账号1',
                        'auth': {
                            'login_name': config.get("login_name", ""),
                            'user_id': config.get("user_id", ""),
                            'ses_id': config.get("ses_id", ""),
                            'is_logged_in': config.get("is_logged_in", False),
                            'display_name': config.get("user_name", ""),
                            'remain_integral': config.get("remain_integral", 0)
                        },
                        'config': {
                            'exchange_id': config.get("exchange_id", "10"),
                            'run_time': self.get_next_run_time(),
                            'run_count': config.get("run_count", "10"),
                            'time_sleep': config.get("time_sleep", "0.2")
                        },
                        'state': {
                            'running': False,
                            'daily_task_done': config.get("daily_task_done_date", "") == date.today().isoformat(),
                            'daily_task_done_date': config.get("daily_task_done_date", "")
                        }
                    }
                    self.profiles = [migrated_profile]
                    self.active_profile_index = 0

                # 确保索引有效
                if self.active_profile_index >= len(self.profiles):
                    self.active_profile_index = 0

                # 程序刚启动，任何账号都不可能在运行任务 → 清除残留的运行状态标记
                for p in self.profiles:
                    p.setdefault('state', {})['running'] = False

            except Exception as e:
                # 配置文件损坏：备份原文件后用默认配置继续启动，不闪退
                self.profiles = []
                self.active_profile_index = 0
                try:
                    backup = self.config_file + ".corrupt"
                    if os.path.exists(self.config_file):
                        os.replace(self.config_file, backup)
                except Exception:
                    pass
                try:
                    self.update_log(f"配置文件读取失败，已重置为默认配置：{e}")
                except Exception:
                    pass
            finally:
                self.loading_config = False

        # 如果没有 Profile，创建一个空的
        if not self.profiles:
            self.add_profile()
        else:
            # 默认选中一个已登录账号，避免"没选用户就运行不了"
            self._apply_active_profile()
            # 更新 UI
            self.update_profile_tabs()
            self.sync_ui_from_profile()

        # 如果标记已登录，启动后验证 ses_id 是否仍有效
        auth = self._get_profile_auth()
        if auth.get('is_logged_in') and auth.get('login_name') and auth.get('ses_id'):
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