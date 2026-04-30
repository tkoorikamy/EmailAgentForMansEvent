from PySide6.QtWidgets import QWidget, QVBoxLayout, QPushButton, QTableWidget, QTableWidgetItem, QMessageBox, QDialog, QTextEdit


class EditDialog(QDialog):
    def __init__(self, row):
        super().__init__()
        self.row = row
        lay = QVBoxLayout(self)
        self.edit = QTextEdit(row.get("body", ""))
        btn = QPushButton("Сохранить")
        btn.clicked.connect(self.save)
        lay.addWidget(self.edit)
        lay.addWidget(btn)

    def save(self):
        self.row["body"] = self.edit.toPlainText()
        self.row["previewed"] = True
        self.accept()


class PreviewTab(QWidget):
    def __init__(self, app_state):
        super().__init__()
        self.app_state = app_state
        lay = QVBoxLayout(self)
        self.table = QTableWidget()
        self.refresh_btn = QPushButton("Обновить список")
        self.edit_btn = QPushButton("Просмотр/редактировать выбранное")
        self.send_btn = QPushButton("Отправить выбранные")
        self.refresh_btn.clicked.connect(self.refresh)
        self.edit_btn.clicked.connect(self.edit_selected)
        self.send_btn.clicked.connect(self.mark_selected)
        lay.addWidget(self.table)
        lay.addWidget(self.refresh_btn)
        lay.addWidget(self.edit_btn)
        lay.addWidget(self.send_btn)

    def refresh(self):
        rows = self.app_state.get("emails", [])
        self.table.setColumnCount(6)
        self.table.setHorizontalHeaderLabels(["send", "company", "email", "subject", "ai_comment", "status"])
        self.table.setRowCount(len(rows))
        for i, r in enumerate(rows):
            self.table.setItem(i, 0, QTableWidgetItem("1" if r.get("selected", True) else "0"))
            self.table.setItem(i, 1, QTableWidgetItem(r.get("company", "")))
            self.table.setItem(i, 2, QTableWidgetItem(r.get("email", "")))
            self.table.setItem(i, 3, QTableWidgetItem(r.get("subject", "")))
            self.table.setItem(i, 4, QTableWidgetItem(r.get("ai_comment", "")))
            self.table.setItem(i, 5, QTableWidgetItem(r.get("send_status", r.get("status", ""))))

    def edit_selected(self):
        row_idx = self.table.currentRow()
        if row_idx < 0:
            QMessageBox.warning(self, "Ошибка", "Выберите строку")
            return
        row = self.app_state.get("emails", [])[row_idx]
        EditDialog(row).exec()
        self.refresh()

    def mark_selected(self):
        rows = self.app_state.get("emails", [])
        count = 0
        for i, r in enumerate(rows):
            selected = self.table.item(i, 0).text() == "1"
            r["selected"] = selected
            if selected:
                count += 1
        info = self.app_state.get("attachment")
        if not info:
            QMessageBox.warning(self, "Ошибка", "Файл КП не выбран")
            return
        ai_needs_review = [r for r in rows if r.get("selected") and r.get("requires_preview") and not r.get("previewed")]
        if ai_needs_review:
            QMessageBox.warning(self, "Требуется предпросмотр", "Для AI-писем откройте карточку и подтвердите текст перед отправкой.")
            return
        self.app_state["send_ready"] = True
        QMessageBox.information(self, "Подтверждение", f"Будет отправлено {count} писем с вложением {info['name']}. Перейдите во вкладку Отправка и логи и нажмите Старт.")
