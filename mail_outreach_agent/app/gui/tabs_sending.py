import csv
from pathlib import Path
import keyring
from PySide6.QtWidgets import QWidget, QVBoxLayout, QPushButton, QTextEdit, QLabel, QMessageBox, QFileDialog
from app.core.settings import load_settings
from app.core.email_sender import build_message, send_message
from app.core.queue_manager import QueueManager

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
        self.export = QPushButton("Экспорт отчета")
        self.start.clicked.connect(self.start_sending)
        self.pause.clicked.connect(self.queue.pause)
        self.resume.clicked.connect(self.queue.resume)
        self.stop.clicked.connect(self.queue.stop)
        self.export.clicked.connect(self.export_report)
        for w in [self.progress, self.log, self.start, self.pause, self.resume, self.stop, self.export]:
            lay.addWidget(w)

    def start_sending(self):
        settings = load_settings()
        rows = [r for r in self.app_state.get("emails", []) if r.get("selected", True)]
        attachment = self.app_state.get("attachment", {}).get("path")
        not_previewed_ai = [r for r in rows if r.get("requires_preview") and not r.get("previewed")]
        if not_previewed_ai:
            QMessageBox.warning(self, "Ошибка", "Есть AI-письма без обязательного предпросмотра.")
            return
        if not attachment:
            QMessageBox.warning(self, "Ошибка", "Выберите файл КП")
            return
        pwd = keyring.get_password(SERVICE, settings["smtp_login"])
        if not pwd:
            QMessageBox.warning(self, "Ошибка", "Пароль не найден в Credential Manager")
            return

        def send_fn(row):
            msg = build_message(settings["smtp_login"], settings["sender_name"], row["email"], row["subject"], row["body"], attachment)
            send_message(settings, pwd, msg)

        def on_update(row):
            self.progress.setText(f"{row['email']}: {row.get('send_status')}")
            self.log.append(f"{row['email']} -> {row.get('send_status')} {row.get('error_message', '')}")

        self.queue.run(rows, int(settings["delay_seconds"]), int(settings["max_per_run"]), send_fn, on_update)

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
