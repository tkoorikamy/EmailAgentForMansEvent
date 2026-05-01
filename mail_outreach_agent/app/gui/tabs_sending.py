import csv
from datetime import datetime
from pathlib import Path
import keyring
from PySide6.QtCore import QObject, QThread, Signal
from PySide6.QtWidgets import QWidget, QVBoxLayout, QPushButton, QTextEdit, QLabel, QMessageBox, QFileDialog, QProgressBar

from app.core.settings import load_settings
from app.core.email_sender import build_message, send_email
from app.core.database import update_email_status, add_send_log

SERVICE = "MailOutreachAgent"


class SendingWorker(QObject):
    log_message = Signal(str)
    progress_changed = Signal(int, int)
    current_recipient_changed = Signal(str, str)
    email_sent = Signal(int)
    email_failed = Signal(int, str)
    finished = Signal()

    def __init__(self, jobs, delay_seconds, max_per_run, smtp_settings, password, attachment):
        super().__init__()
        self.jobs = jobs[: max(0, int(max_per_run))]
        self.delay_seconds = max(0, int(delay_seconds))
        self.smtp_settings = smtp_settings
        self.password = password
        self.attachment = attachment
        self.stop_requested = False
        self.pause_requested = False

    def run(self):
        total = len(self.jobs)
        self.log_message.emit("Пробую подключиться к SMTP")
        self.log_message.emit(f"SMTP host: {self.smtp_settings.get('smtp_host')} port: {self.smtp_settings.get('smtp_port')} login: {self.smtp_settings.get('smtp_login')}")
        self.log_message.emit("SMTP подключение успешно")
        self.log_message.emit(f"Выбрано {total} писем")
        for i, row in enumerate(self.jobs, start=1):
            if self.stop_requested:
                break
            while self.pause_requested and not self.stop_requested:
                QThread.msleep(200)
            if self.stop_requested:
                break

            self.current_recipient_changed.emit(row.get("company", ""), row.get("email", ""))
            self.log_message.emit(f"Отправляю: {row.get('company', '')} / {row.get('email', '')}")
            self.log_message.emit(f"Пробую отправить письмо: {row.get('email', '')}")
            msg = build_message(self.smtp_settings["smtp_login"], self.smtp_settings["sender_name"], row["email"], row["subject"], row["body"], self.attachment)
            ok, err = send_email(self.smtp_settings, self.password, msg)
            if ok:
                self.email_sent.emit(row["_row_id"])
                self.log_message.emit("send_message выполнен")
                self.log_message.emit("Письмо отправлено")
            else:
                self.email_failed.emit(row["_row_id"], err)
                self.log_message.emit(f"Ошибка отправки: {err}")
            self.progress_changed.emit(i, total)

            if i < total and self.delay_seconds > 0:
                self.log_message.emit(f"Пауза {self.delay_seconds} секунд")
                for _ in range(self.delay_seconds * 5):
                    if self.stop_requested:
                        break
                    while self.pause_requested and not self.stop_requested:
                        QThread.msleep(200)
                    QThread.msleep(200)

        self.log_message.emit("Очередь завершена")
        self.finished.emit()


class SendingTab(QWidget):
    def __init__(self, app_state):
        super().__init__()
        self.app_state = app_state
        self.worker = None
        self.thread = None
        self.row_index = {}

        lay = QVBoxLayout(self)
        self.progress = QLabel("Ожидание")
        self.progress_bar = QProgressBar()
        self.log = QTextEdit()
        self.log.setReadOnly(True)
        self.start = QPushButton("Старт")
        self.pause = QPushButton("Пауза")
        self.resume = QPushButton("Продолжить")
        self.stop = QPushButton("Остановить")
        self.test_send = QPushButton("Отправить тестовое письмо")
        self.export = QPushButton("Экспорт отчета")

        self.start.clicked.connect(self.start_sending)
        self.pause.clicked.connect(self.pause_sending)
        self.resume.clicked.connect(self.resume_sending)
        self.stop.clicked.connect(self.stop_sending)
        self.test_send.clicked.connect(self.send_test_email)
        self.export.clicked.connect(self.export_report)

        for w in [self.progress, self.progress_bar, self.log, self.start, self.pause, self.resume, self.stop, self.test_send, self.export]:
            lay.addWidget(w)

    def _log(self, message: str):
        self.log.append(message)
        add_send_log("INFO", message)

    def _get_settings_password(self):
        settings = load_settings()
        pwd = keyring.get_password(SERVICE, settings["smtp_login"])
        return settings, pwd

    def _set_running(self, running: bool):
        self.start.setEnabled(not running)
        self.test_send.setEnabled(not running)
        self.pause.setEnabled(running)
        self.resume.setEnabled(running)
        self.stop.setEnabled(running)

    def start_sending(self):
        if self.thread and self.thread.isRunning():
            return

        self._log("Нажата кнопка Старт")
        settings, pwd = self._get_settings_password()
        if not pwd:
            QMessageBox.warning(self, "Ошибка", "Пароль не найден в Credential Manager")
            return

        all_rows = self.app_state.get("emails", [])
        self._log(f"Загружено {len(all_rows)} писем из БД")
        rows = []
        self.row_index = {}
        for idx, r in enumerate(self.app_state.get("emails", [])):
            if r.get("selected", True) and r.get("send_status", "pending") == "pending":
                job = dict(r)
                job["_row_id"] = idx
                rows.append(job)
                self.row_index[idx] = r

        self._log(f"Выбрано {len(rows)} писем для отправки")
        if not rows:
            QMessageBox.warning(self, "Ошибка", "Нет выбранных писем для отправки. Вернитесь во вкладку Предпросмотр и выберите получателей.")
            return

        attachment = self.app_state.get("attachment", {}).get("path")
        if not attachment:
            QMessageBox.warning(self, "Ошибка", "Выберите файл КП")
            return

        self._log("Старт отправки")
        self.progress_bar.setMaximum(len(rows))
        self.progress_bar.setValue(0)
        self._set_running(True)

        self.thread = QThread(self)
        self.worker = SendingWorker(rows, settings.get("delay_seconds", 20), settings.get("max_per_run", 50), settings, pwd, attachment)
        self.worker.moveToThread(self.thread)

        self.thread.started.connect(self.worker.run)
        self.worker.log_message.connect(self._log)
        self.worker.progress_changed.connect(self.on_progress)
        self.worker.current_recipient_changed.connect(self.on_current_recipient)
        self.worker.email_sent.connect(self.on_email_sent)
        self.worker.email_failed.connect(self.on_email_failed)
        self.worker.finished.connect(self.on_finished)
        self.worker.finished.connect(self.thread.quit)
        self.thread.finished.connect(self.thread.deleteLater)
        self.thread.start()

    def on_progress(self, current, total):
        self.progress_bar.setMaximum(total)
        self.progress_bar.setValue(current)

    def on_current_recipient(self, company, email):
        self.progress.setText(f"Текущий получатель: {company} / {email}")

    def on_email_sent(self, email_id):
        row = self.row_index.get(email_id)
        if row is None:
            return
        row["send_status"] = "sent"
        row["error_message"] = ""
        row["sent_at"] = datetime.utcnow().isoformat()
        update_email_status(row.get("email", ""), "sent", "", row["sent_at"])
        self._log("Статус обновлен на sent")

    def on_email_failed(self, email_id, error):
        row = self.row_index.get(email_id)
        if row is None:
            return
        row["send_status"] = "failed"
        row["error_message"] = error
        update_email_status(row.get("email", ""), "failed", error, "")

    def on_finished(self):
        self._set_running(False)
        self.progress.setText("Очередь завершена")

    def pause_sending(self):
        if self.worker:
            self.worker.pause_requested = True

    def resume_sending(self):
        if self.worker:
            self.worker.pause_requested = False

    def stop_sending(self):
        if self.worker:
            self.worker.stop_requested = True

    def send_test_email(self):
        self._log("Нажата кнопка Старт")
        settings, pwd = self._get_settings_password()
        if not pwd:
            QMessageBox.warning(self, "Ошибка", "Пароль не найден в Credential Manager")
            return
        to_addr = settings["smtp_login"]
        attachment = self.app_state.get("attachment", {}).get("path")
        self._log(f"SMTP host: {settings.get('smtp_host')} port: {settings.get('smtp_port')} login: {settings.get('smtp_login')}")
        self._log("Пробую подключиться к SMTP")
        self._log(f"Отправляю: TEST / {to_addr}")
        msg = build_message(settings["smtp_login"], settings["sender_name"], to_addr, "Тест SMTP - Mail Outreach Agent", "Это тестовое письмо для проверки SMTP.", attachment)
        ok, err = send_email(settings, pwd, msg)
        if ok:
            self._log("SMTP подключение успешно")
            self._log("send_message выполнен")
            self._log("Письмо отправлено")
        else:
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
