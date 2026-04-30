import csv
from pathlib import Path
import keyring
from PySide6.QtWidgets import QWidget, QVBoxLayout, QPushButton, QTextEdit, QLabel, QMessageBox, QFileDialog
from app.core.settings import load_settings
from app.core.email_sender import build_message, send_email
from app.core.queue_manager import QueueManager
from app.core.database import update_email_status, add_send_log

SERVICE = "MailOutreachAgent"


class SendingTab(QWidget):
    def __init__(self, app_state):
        super().__init__()
        self.app_state = app_state
        self.queue = QueueManager()
        lay = QVBoxLayout(self)
        self.progress = QLabel("Ожидание")
        self.log = QTextEdit()
        self.log.setReadOnly(True)
        self.start = QPushButton("Старт")
        self.pause = QPushButton("Пауза")
        self.resume = QPushButton("Продолжить")
        self.stop = QPushButton("Остановить")
        self.test_send = QPushButton("Отправить тестовое письмо")
        self.export = QPushButton("Экспорт отчета")
        self.start.clicked.connect(self.start_sending)
        self.pause.clicked.connect(self.queue.pause)
        self.resume.clicked.connect(self.queue.resume)
        self.stop.clicked.connect(self.queue.stop)
        self.test_send.clicked.connect(self.send_test_email)
        self.export.clicked.connect(self.export_report)
        for w in [self.progress, self.log, self.start, self.pause, self.resume, self.stop, self.test_send, self.export]:
            lay.addWidget(w)

    def _log(self, message: str):
        self.log.append(message)
        add_send_log("INFO", message)

    def _get_settings_password(self):
        settings = load_settings()
        pwd = keyring.get_password(SERVICE, settings["smtp_login"])
        return settings, pwd

    def start_sending(self):
        if not self.app_state.get("send_ready"):
            QMessageBox.warning(self, "Ошибка", "Нет выбранных писем для отправки. Вернитесь во вкладку Предпросмотр и выберите получателей.")
            return

        settings, pwd = self._get_settings_password()
        if not pwd:
            QMessageBox.warning(self, "Ошибка", "Пароль не найден в Credential Manager")
            return

        rows = [r for r in self.app_state.get("emails", []) if r.get("selected", True) and r.get("send_status", "pending") == "pending"]
        if not rows:
            QMessageBox.warning(self, "Ошибка", "Нет выбранных писем для отправки. Вернитесь во вкладку Предпросмотр и выберите получателей.")
            return

        attachment = self.app_state.get("attachment", {}).get("path")
        if not attachment:
            QMessageBox.warning(self, "Ошибка", "Выберите файл КП")
            return

        self._log("Старт отправки")

        def send_fn(row):
            msg = build_message(settings["smtp_login"], settings["sender_name"], row["email"], row["subject"], row["body"], attachment)
            return send_email(settings, pwd, msg)

        def on_update(row):
            self.progress.setText(f"Текущий получатель: {row['company']} / {row['email']} -> {row.get('send_status')}")
            update_email_status(row["email"], row.get("send_status", "pending"), row.get("error_message", ""), row.get("sent_at", ""))

        self.queue.run(rows, int(settings["delay_seconds"]), int(settings["max_per_run"]), send_fn, on_update, self._log)

    def send_test_email(self):
        settings, pwd = self._get_settings_password()
        if not pwd:
            QMessageBox.warning(self, "Ошибка", "Пароль не найден в Credential Manager")
            return
        to_addr = settings["smtp_login"]
        msg = build_message(settings["smtp_login"], settings["sender_name"], to_addr, "Тест SMTP - Mail Outreach Agent", "Это тестовое письмо для проверки SMTP.")
        ok, err = send_email(settings, pwd, msg)
        if ok:
            QMessageBox.information(self, "OK", f"Тестовое письмо отправлено на {to_addr}")
            self._log(f"Успешно отправлено тестовое письмо на {to_addr}")
        else:
            QMessageBox.critical(self, "Ошибка", err)
            self._log(f"Ошибка отправки: {err}")

    def export_report(self):
        path, _ = QFileDialog.getSaveFileName(self, "Экспорт", "report.csv", "CSV (*.csv)")
        if not path:
            return
        rows = self.app_state.get("emails", [])
        with Path(path).open("w", encoding="utf-8", newline="") as f:
            writer = csv.DictWriter(f, fieldnames=["company", "email", "subject", "send_status", "sent_at", "error_message"])
            writer.writeheader()
            for r in rows:
                writer.writerow({k: r.get(k, "") for k in writer.fieldnames})
        QMessageBox.information(self, "OK", "Отчет экспортирован")
