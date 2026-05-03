import smtplib

import keyring
from PySide6.QtWidgets import QWidget, QFormLayout, QLineEdit, QPushButton, QCheckBox, QMessageBox, QSpinBox

from app.core.settings import load_settings, save_settings

SERVICE = "MailOutreachAgent"


class MailboxTab(QWidget):
    def __init__(self):
        super().__init__()
        self.settings = load_settings()
        layout = QFormLayout(self)
        self.host = QLineEdit(self.settings["smtp_host"])
        self.port = QLineEdit(str(self.settings["smtp_port"]))
        self.ssl = QCheckBox("SSL")
        self.ssl.setChecked(self.settings["smtp_ssl"])
        self.login = QLineEdit(self.settings["smtp_login"])
        self.password = QLineEdit()
        self.password.setEchoMode(QLineEdit.Password)
        self.sender_name = QLineEdit(self.settings["sender_name"])

        self.delay_seconds = QSpinBox()
        self.delay_seconds.setRange(1, 3600)
        self.delay_seconds.setValue(int(self.settings.get("delay_seconds", 20)))

        self.max_per_run = QSpinBox()
        self.max_per_run.setRange(1, 500)
        self.max_per_run.setValue(int(self.settings.get("max_per_run", 500)))

        self.test_btn = QPushButton("Проверить подключение")
        self.save_btn = QPushButton("Сохранить")
        self.test_btn.clicked.connect(self.test_connection)
        self.save_btn.clicked.connect(self.save)

        for k, w in [
            ("SMTP host", self.host),
            ("SMTP port", self.port),
            ("SSL/TLS", self.ssl),
            ("Email/Login", self.login),
            ("Password/App password", self.password),
            ("Имя отправителя", self.sender_name),
            ("Задержка между письмами (сек)", self.delay_seconds),
            ("Максимум писем за запуск", self.max_per_run),
            ("", self.test_btn),
            ("", self.save_btn),
        ]:
            layout.addRow(k, w)

    def snapshot(self):
        return {
            "smtp_host": self.host.text(),
            "smtp_port": int(self.port.text()),
            "smtp_ssl": self.ssl.isChecked(),
            "smtp_starttls": not self.ssl.isChecked(),
            "smtp_login": self.login.text(),
            "sender_name": self.sender_name.text(),
            "delay_seconds": self.delay_seconds.value(),
            "max_per_run": self.max_per_run.value(),
        }

    def test_connection(self):
        s = self.snapshot()
        try:
            with smtplib.SMTP_SSL(s["smtp_host"], s["smtp_port"], timeout=10) as server:
                server.login(s["smtp_login"], self.password.text())
            QMessageBox.information(self, "OK", "Подключение успешно")
        except Exception as exc:  # noqa: BLE001
            QMessageBox.critical(self, "Ошибка", str(exc))

    def save(self):
        s = self.snapshot()
        save_settings(s)
        if self.password.text():
            keyring.set_password(SERVICE, s["smtp_login"], self.password.text())
        QMessageBox.information(self, "OK", "Настройки сохранены. Для Gmail/Yandex/Mail.ru может понадобиться пароль приложения.")
