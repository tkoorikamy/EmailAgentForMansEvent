from PySide6.QtWidgets import QWidget, QVBoxLayout, QPushButton, QFileDialog, QLabel, QLineEdit, QTextEdit, QMessageBox, QComboBox
from app.core.template_engine import DEFAULT_SUBJECT, DEFAULT_BODY, generate_email
from app.core.attachment_manager import attachment_info
from app.core.ai_personalizer import ai_available, generate_ai_comment
from app.core.database import replace_emails


class TemplateTab(QWidget):
    def __init__(self, app_state):
        super().__init__()
        self.app_state = app_state
        layout = QVBoxLayout(self)
        self.attach_btn = QPushButton("Загрузить файл КП")
        self.attach_info = QLabel("Файл не выбран")
        self.mode = QComboBox()
        self.mode.addItems(["Обычный шаблон", "AI-персонализация"])
        self.mode_hint = QLabel("AI использует переменную окружения MAIL_OUTREACH_AI_API_KEY")
        self.subject = QLineEdit(DEFAULT_SUBJECT)
        self.body = QTextEdit(DEFAULT_BODY)
        self.gen_btn = QPushButton("Сгенерировать письма")
        self.attach_btn.clicked.connect(self.pick_attachment)
        self.gen_btn.clicked.connect(self.generate)
        for w in [self.attach_btn, self.attach_info, self.mode, self.mode_hint, self.subject, self.body, self.gen_btn]:
            layout.addWidget(w)

    def pick_attachment(self):
        path, _ = QFileDialog.getOpenFileName(self, "Выберите КП", "", "Docs (*.pdf *.docx *.xlsx)")
        if not path:
            return
        info = attachment_info(path)
        self.app_state["attachment"] = info
        self.attach_info.setText(f"{info['name']} | {info['size']} bytes | {info['path']}")

    def generate(self):
        if not self.app_state.get("recipients"):
            QMessageBox.warning(self, "Ошибка", "Сначала загрузите базу")
            return
        use_ai = self.mode.currentText() == "AI-персонализация"
        ai_ok = ai_available()
        if use_ai and not ai_ok:
            QMessageBox.warning(self, "AI недоступен", "API key не найден. Будет использован обычный шаблон.")

        emails = []
        for row in self.app_state["recipients"]:
            if use_ai and ai_ok:
                row["ai_comment"] = generate_ai_comment(row)
                row["requires_preview"] = True
            else:
                row["ai_comment"] = row.get("ai_comment", "")
                row["requires_preview"] = False
            subject, body = generate_email(row, self.subject.text(), self.body.toPlainText())
            row["subject"] = subject
            row["body"] = body
            row["send_status"] = "pending"
            emails.append(row)
        self.app_state["emails"] = emails
        self.app_state["send_ready"] = False
        replace_emails(emails)
        self.app_state["generation_mode"] = "ai" if use_ai and ai_ok else "normal"
        QMessageBox.information(self, "OK", f"Сгенерировано: {len(emails)}")
