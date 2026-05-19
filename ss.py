import sys
from PyQt5.QtWidgets import QApplication, QWidget, QLabel
from PyQt5.QtGui import QFont, QPainter, QColor
from PyQt5.QtCore import Qt, QTimer


# ================= CUSTOM TECH LOGO =================
class TechLogo(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFixedSize(120, 120)

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)

        center = self.rect().center()

        # Outer ring
        pen = painter.pen()
        pen.setWidth(3)
        pen.setColor(QColor(0, 200, 255))
        painter.setPen(pen)
        painter.drawEllipse(center, 45, 45)

        # Inner core
        painter.setBrush(QColor(0, 200, 255, 120))
        painter.setPen(Qt.NoPen)
        painter.drawEllipse(center, 10, 10)

        # Signal arcs
        pen.setColor(QColor(0, 255, 255))
        pen.setWidth(2)
        painter.setPen(pen)
        painter.drawArc(20, 20, 80, 80, 30 * 16, 120 * 16)
        painter.drawArc(30, 30, 60, 60, 30 * 16, 120 * 16)

        # Orbit
        pen.setColor(QColor(255, 180, 0))
        pen.setWidth(2)
        painter.setPen(pen)
        painter.drawEllipse(center, 30, 30)


# ================= SPLASH SCREEN =================
class SplashScreen(QWidget):
    def __init__(self):
        super().__init__()

        # Window settings
        self.setFixedSize(700, 420)
        self.setWindowFlags(Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint)
        self.setAttribute(Qt.WA_TranslucentBackground)

        # Main container (rounded)
        self.container = QWidget(self)
        self.container.setGeometry(0, 0, 700, 420)
        self.container.setStyleSheet("""
            background-color: #0A192F;
            border-radius: 20px;
        """)

        # -------- LOGO --------
        self.logo = TechLogo(self.container)
        self.logo.move(60, 140)

        # -------- COMPANY --------
        self.company = QLabel("SYNODIC SPACE PVT. LTD.", self.container)
        self.company.setFont(QFont("Segoe UI", 9))
        self.company.setStyleSheet("color: rgba(255,255,255,0.6);")
        self.company.move(25, 20)

        # -------- TITLE --------
        self.title = QLabel("TESS GCS", self.container)
        self.title.setFont(QFont("Segoe UI", 26, QFont.Bold))
        self.title.setStyleSheet("color: #EAF6FF;")
        self.title.adjustSize()
        self.title.move(320, 150)

        # -------- VERSION --------
        self.version = QLabel("v1.0", self.container)
        self.version.setFont(QFont("Segoe UI", 10))
        self.version.setStyleSheet("color: #00C6FF;")
        self.version.move(480, 160)

        # -------- STATUS --------
        self.status = QLabel("Initializing systems...", self.container)
        self.status.setFont(QFont("Segoe UI", 10))
        self.status.setStyleSheet("color: #AFCBFF;")
        self.status.adjustSize()
        self.status.move(320, 200)

        # -------- PROGRESS BAR --------
        self.progress_bg = QLabel(self.container)
        self.progress_bg.setGeometry(150, 340, 400, 6)
        self.progress_bg.setStyleSheet("""
            background-color: rgba(255,255,255,0.15);
            border-radius: 3px;
        """)

        self.progress_fill = QLabel(self.progress_bg)
        self.progress_fill.setGeometry(0, 0, 0, 6)
        self.progress_fill.setStyleSheet("""
            background-color: #00C6FF;
            border-radius: 3px;
        """)

        # -------- TIMER --------
        self.progress = 0
        self.app_ready = False

        self.timer = QTimer()
        self.timer.timeout.connect(self.update_progress)

        # Faster loading
        self.timer.start(30)

    # -------- BACKGROUND (transparent outer) --------
    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        painter.setBrush(Qt.transparent)
        painter.setPen(Qt.NoPen)
        painter.drawRect(self.rect())

    # -------- PROGRESS --------
    def update_progress(self):
        if self.progress < 85:
            self.progress += 2
        elif self.progress < 95:
            self.progress += 1
        elif self.app_ready:
            self.progress += 3

        width = int((self.progress / 100) * 400)
        self.progress_fill.setFixedWidth(width)

        steps = [
            "Initializing systems...",
            "Loading modules...",
            "Connecting telemetry...",
            "Establishing link...",
            "Launching interface..."
        ]

        index = min(int(self.progress) // 20, len(steps) - 1)
        self.status.setText(steps[index])

        if self.progress >= 100:
            self.timer.stop()
            self.close()

    def set_app_ready(self):
        self.app_ready = True


# ================= TEST RUN =================
'''if __name__ == "__main__":
    app = QApplication(sys.argv)

    splash = SplashScreen()
    splash.show()

    # simulate fast app load
    def finish():
        splash.set_app_ready()

    QTimer.singleShot(1000, finish)

    sys.exit(app.exec_())'''