import sys
from PySide6.QtWidgets import QApplication
from app.core.database import init_db
from app.gui.main_window import MainWindow


def main():
    init_db()
    app = QApplication(sys.argv)
    w = MainWindow()
    w.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
