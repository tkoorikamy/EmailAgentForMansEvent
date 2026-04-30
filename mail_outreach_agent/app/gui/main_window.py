from PySide6.QtWidgets import QMainWindow, QTabWidget
from app.gui.tabs_database import DatabaseTab
from app.gui.tabs_mailbox import MailboxTab
from app.gui.tabs_template import TemplateTab
from app.gui.tabs_preview import PreviewTab
from app.gui.tabs_sending import SendingTab


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Mail Outreach Agent")
        self.resize(1100, 700)
        state = {"recipients": [], "emails": [], "attachment": None}

        tabs = QTabWidget()
        tabs.addTab(DatabaseTab(state), "База")
        tabs.addTab(MailboxTab(), "Почтовый ящик")
        tabs.addTab(TemplateTab(state), "КП и шаблон")
        tabs.addTab(PreviewTab(state), "Предпросмотр")
        tabs.addTab(SendingTab(state), "Отправка и логи")
        self.setCentralWidget(tabs)
