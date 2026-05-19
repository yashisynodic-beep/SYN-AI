import sys
from PyQt5.QtWidgets import QApplication, QMainWindow
from PyQt5.QtCore import QTimer

from ss import SplashScreen
from MAIN import Ui_MainWindow


class MainApp(QMainWindow, Ui_MainWindow):
    def __init__(self):
        super().__init__()
        self.setupUi(self)


if __name__ == "__main__":
    app = QApplication(sys.argv)

    splash = SplashScreen()
    splash.show()

    app.processEvents()  # IMPORTANT

    # 👇 make it global
    global main_window
    main_window = None

    def load_main():
        global main_window  # ✅ FIX

        main_window = MainApp()
        splash.set_app_ready()
        main_window.show()

    QTimer.singleShot(100, load_main)

    sys.exit(app.exec_())