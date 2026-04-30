from PySide6.QtWidgets import QWidget, QVBoxLayout, QPushButton, QFileDialog, QLabel, QTableWidget, QTableWidgetItem
from app.core.importer import load_recipients
from app.core.validator import assign_statuses


class DatabaseTab(QWidget):
    def __init__(self, app_state):
        super().__init__()
        self.app_state = app_state
        layout = QVBoxLayout(self)
        self.btn = QPushButton("Загрузить XLSX/CSV")
        self.btn.clicked.connect(self.load_file)
        self.stats = QLabel("Готово: 0 | Ошибки: 0 | Дубли: 0")
        self.table = QTableWidget()
        layout.addWidget(self.btn)
        layout.addWidget(self.stats)
        layout.addWidget(self.table)

    def load_file(self):
        path, _ = QFileDialog.getOpenFileName(self, "Выберите базу", "", "Tables (*.xlsx *.csv)")
        if not path:
            return
        df = load_recipients(path)
        statuses = assign_statuses(df["email"].tolist())
        df["status"] = statuses
        if "ai_comment" not in df.columns:
            df["ai_comment"] = ""
        self.app_state["recipients"] = df.to_dict(orient="records")
        self.render(df)

    def render(self, df):
        self.table.setColumnCount(len(df.columns))
        self.table.setRowCount(len(df))
        self.table.setHorizontalHeaderLabels(df.columns.tolist())
        for r in range(len(df)):
            for c, col in enumerate(df.columns):
                self.table.setItem(r, c, QTableWidgetItem(str(df.iloc[r][col])))
        ready = (df["status"] == "ready").sum()
        bad = (df["status"] == "invalid_email").sum()
        dup = (df["status"] == "duplicate").sum()
        self.stats.setText(f"Готово: {ready} | Ошибки: {bad} | Дубли: {dup}")
