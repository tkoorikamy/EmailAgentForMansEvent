import csv
import logging
from pathlib import Path

import keyring
from PySide6.QtCore import QObject, QThread, Signal
from PySide6.QtWidgets import QWidget, QVBoxLayout, QPushButton, QTextEdit, QLabel, QMessageBox, QFileDialog

from app.core.email_sender import build_message, send_message
from app.core.queue_manager import QueueManager
from app.core.settings import load_settings

SERVICE = "MailOutreachAgent"
logger = logging.getLogger(__name__)


class SendingWorker(QObject):
    row_updated = Signal(dict)
    finished = Signal()
    failed = Signal(str)

    def __init__(self, queue: QueueManager, rows: list[dict], delay_seconds: int, max_per_run: int, send_fn):
        super().__init__()
        self.queue = queue
        self.rows = rows
        self.delay_seconds = delay_seconds
        self.max_per_run = max_per_run
        self.send_fn = send_fn

    def run(self):
        try:
            self.queue.run(self.rows, self.delay_seconds, self.max_per_run, self.send_fn, self.row_updated.emit)
        except Exception as exc:  # noqa: BLE001
            logger.exception("Unhandled sending worker error")
            self.failed.emit(str(exc))
        finally:
            self.finished.emit()


class SendingTab(QWidget):
    def __init__(self, app_state):
        super().__init__()
        self.app_state = app_state
        self.queue = QueueManager()
        self.worker_thread = None
        self.worker = None

        lay = QVBoxLayout(self)
        self.progress = QLabel("Ожидание")
        self.log = QTextEdit()
        self.log.setReadOnly(True)
        self.start = QPushButton("Старт")
        self.send_test = QPushButton("Отправить тестовое письмо")
        self.pause = QPushButton("Пауза")
        self.resume = QPushButton("Продолжить")
        self.stop = QPushButton("Остановить")
        self.export = QPushButton("Экспорт отчета")

        self.start.clicked.connect(self.start_sending)
        self.send_test.clicked.connect(self.send_test_email)
        self.pause.clicked.connect(self.queue.pause)
        self.resume.clicked.connect(self.queue.resume)
        self.stop.clicked.connect(self.queue.stop)
        self.export.clicked.connect(self.export_report)

        for w in [self.progress, self.log, self.start, self.send_test, self.pause, self.resume, self.stop, self.export]:
            lay.addWidget(w)

    def _build_send_fn(self, settings: dict, pwd: str, attachment: str):
        def send_fn(row):
            msg = build_message(settings["smtp_login"], settings["sender_name"], row["email"], row["subject"], row["body"], attachment)
            send_message(settings, pwd, msg)

        return send_fn

    def start_sending(self):
        if self.worker_thread and self.worker_thread.isRunning():
            QMessageBox.warning(self, "Отправка", "Отправка уже выполняется.")
            return

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

        self.queue.reset()
        send_fn = self._build_send_fn(settings, pwd, attachment)

        self.worker_thread = QThread(self)
        self.worker = SendingWorker(self.queue, rows, int(settings["delay_seconds"]), int(settings["max_per_run"]), send_fn)
        self.worker.moveToThread(self.worker_thread)
        self.worker_thread.started.connect(self.worker.run)
        self.worker.row_updated.connect(self.on_update)
        self.worker.failed.connect(lambda err: QMessageBox.critical(self, "Ошибка отправки", err))
        self.worker.finished.connect(self.on_finished)
        self.worker.finished.connect(self.worker_thread.quit)
        self.worker.finished.connect(self.worker.deleteLater)
        self.worker_thread.finished.connect(self.worker_thread.deleteLater)

        self.start.setEnabled(False)
        self.progress.setText("Запуск отправки...")
        self.log.append("[INFO] Старт отправки")
        logger.info("Start sending requested from GUI")
        self.worker_thread.start()

    def on_update(self, row: dict):
        self.progress.setText(f"{row['email']}: {row.get('send_status')}")
        self.log.append(f"{row['email']} -> {row.get('send_status')} {row.get('error_message', '')}")

    def on_finished(self):
        self.start.setEnabled(True)
        self.progress.setText("Отправка завершена")
        self.log.append("[INFO] Отправка завершена")
        logger.info("Sending finished")
        self.worker_thread = None
        self.worker = None

    def send_test_email(self):
        settings = load_settings()
        attachment = self.app_state.get("attachment", {}).get("path")
        if not attachment:
            QMessageBox.warning(self, "Ошибка", "Выберите файл КП")
            return

        pwd = keyring.get_password(SERVICE, settings["smtp_login"])
        if not pwd:
            QMessageBox.warning(self, "Ошибка", "Пароль не найден в Credential Manager")
            return

        recipient = settings["smtp_login"]
        test_row = {
            "email": recipient,
            "subject": "Тестовое письмо MailOutreachAgent",
            "body": "Это тестовое письмо для проверки SMTP-настроек.",
        }
        try:
            send_fn = self._build_send_fn(settings, pwd, attachment)
            send_fn(test_row)
            self.log.append(f"[INFO] Тестовое письмо отправлено на {recipient}")
            QMessageBox.information(self, "OK", f"Тестовое письмо отправлено на {recipient}")
        except Exception as exc:  # noqa: BLE001
            logger.exception("Test email failed")
            self.log.append(f"[ERROR] Ошибка тестовой отправки: {exc}")
            QMessageBox.critical(self, "Ошибка", str(exc))

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
