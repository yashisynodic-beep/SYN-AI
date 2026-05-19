from PyQt5 import QtWidgets, QtCore
import csv
from datetime import datetime
import os


class NotificationWindow(QtWidgets.QWidget):
    def __init__(self, username, parent=None):
        super().__init__(parent)
        self.username = username
        self.setWindowTitle(f"Logs - {username}")
        self.resize(540, 470)

        # ---------------- STYLE ----------------
        self.setStyleSheet("""
            QWidget { background-color:#1e1e2f; color:white; font-size:13px; }
            QTextEdit { background:#12121c; border:1px solid #3a3a55; border-radius:6px; padding:6px; }
            QPushButton { background:#4a6cf7; border-radius:8px; padding:7px; font-weight:bold; }
            QPushButton:hover { background:#6f8cff; }
        """)

        # ---------------- DATA ----------------
        self.log_data = []
        self.pinned_logs = []

        # folder path
        base = os.path.join(os.getenv("APPDATA"), "GCSLogs")
        self.user_folder = os.path.join(base, self.username)
        os.makedirs(self.user_folder, exist_ok=True)

        self.csv_file = os.path.join(self.user_folder, "log_data.csv")
        self.pinned_file = os.path.join(self.user_folder, "pinned_logs.csv")

        # ---------------- LAYOUT ----------------
        layout = QtWidgets.QVBoxLayout(self)

        title = QtWidgets.QLabel("Mission Logs")
        title.setAlignment(QtCore.Qt.AlignCenter)
        title.setStyleSheet("font-size:18px;font-weight:bold;margin:6px;")
        layout.addWidget(title)

        self.log_text = QtWidgets.QTextEdit()
        self.log_text.setReadOnly(True)
        layout.addWidget(self.log_text)

        btn_layout = QtWidgets.QHBoxLayout()

        self.save_btn = QtWidgets.QPushButton("💾 Save Data")
        self.save_btn.clicked.connect(self.save_data)

        self.pin_btn = QtWidgets.QPushButton("📌 Pin Selected")
        self.pin_btn.clicked.connect(self.pin_selected)

        self.stats_btn = QtWidgets.QPushButton("📊 Stats")
        self.stats_btn.clicked.connect(self.show_stats)

        self.clear_btn = QtWidgets.QPushButton("🗑 Clear Logs")
        self.clear_btn.clicked.connect(self.clear_logs)

        btn_layout.addWidget(self.save_btn)
        btn_layout.addWidget(self.pin_btn)
        btn_layout.addWidget(self.stats_btn)
        btn_layout.addWidget(self.clear_btn)
        layout.addLayout(btn_layout)

        # load previous logs
        self.load_existing_logs()

    # ---------------- LOAD OLD LOGS ----------------
    def load_existing_logs(self):
        if os.path.exists(self.csv_file):
            with open(self.csv_file, newline="") as f:
                reader = csv.reader(f)
                for row in reader:
                    if row:
                        self.log_data.append(row)
                        self.log_text.append(f"{row[0]} → {row[1]}")

    # ---------------- ADD LOG ----------------
    def add_serial_data(self, data):
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        entry = [timestamp, data]
        self.log_data.append(entry)

        if self.is_corrupt_packet(data):
            self.log_text.append(
                f'<span style="color:#ff4d4d;">⚠ {timestamp} → {data}</span>'
            )
            self.pinned_logs.append(f"{timestamp} → {data}")
        else:
            self.log_text.append(f"{timestamp} → {data}")

    # ---------------- SAVE ----------------
    def save_data(self):
        if not self.log_data:
            QtWidgets.QMessageBox.warning(self, "Empty", "No data to save.")
            return

        # overwrite file with full session
        with open(self.csv_file, "w", newline="") as f:
            writer = csv.writer(f)
            writer.writerows(self.log_data)

        # save pinned
        if self.pinned_logs:
            with open(self.pinned_file, "w", newline="") as f:
                writer = csv.writer(f)
                for log in self.pinned_logs:
                    writer.writerow([log])

        QtWidgets.QMessageBox.information(self, "Saved", "Full log saved successfully!")

    # ---------------- PIN SELECTED ----------------
    def pin_selected(self):
        cursor = self.log_text.textCursor()
        selected = cursor.selectedText()

        if not selected:
            QtWidgets.QMessageBox.warning(self, "No Selection", "Select a log line first.")
            return

        self.pinned_logs.append(selected)
        self.log_text.append(f"📌 PINNED → {selected}")

    # ---------------- CLEAR ----------------
    def clear_logs(self):
        confirm = QtWidgets.QMessageBox.question(
            self,
            "Confirm",
            "Clear current session logs?",
            QtWidgets.QMessageBox.Yes | QtWidgets.QMessageBox.No
        )

        if confirm == QtWidgets.QMessageBox.Yes:
            self.log_data.clear()
            self.log_text.clear()

    # ---------------- STATS ----------------
    def show_stats(self):
        total = len(self.log_data)
        pinned = len(self.pinned_logs)

        msg = f"""
User: {self.username}

Total Logs: {total}
Pinned Logs: {pinned}

Session Active: {"Yes" if total else "No"}
        """

        QtWidgets.QMessageBox.information(self, "Session Statistics", msg)

    # ---------------- CORRUPT CHECK ----------------
    def is_corrupt_packet(self, data):
        if "ERROR" in data:
            return True
        if "CORRUPT" in data:
            return True
        if "CHK_FAIL" in data:
            return True
        return False