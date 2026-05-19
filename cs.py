import sys
from datetime import datetime
from PyQt5 import QtCore
from PyQt5.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QLineEdit, QListWidget, QCheckBox, QGroupBox, QGridLayout, QTextEdit, QSizePolicy
)
from PyQt5.QtGui import QFont, QColor, QPalette, QTextCursor
from PyQt5.QtWidgets import QScrollArea
from cv2 import line
from serial_manager import SerialManager

class ConsoleWindow(QWidget):
    def __init__(self, serial_manager, parent=None):
        super().__init__(parent)
        self.serial_manager = serial_manager

        self.setWindowTitle("Console")
        self.resize(900, 600)

        self.total_packets = 0
        self.missing_packets = 0
        self.corrupt_packets = 0
        self.last_packet_id = -1
        self.last_packet_time = "N/A"

        self.headers = [
            "Rocket_ID",
            "Mission Time",
            "Packet Count",
            "Altitude",
            "Pressure",
            "Load Voltage",
            "Load Current",
            "GPS Latitude",
            "GPS Longitude",
            "Accel X",
            "Accel Y",
            "Accel Z",
            "Gyro X",
            "Gyro Y",
            "Gyro Z", "Mag X", "Mag Y", "Mag Z",
            "Euler X", "Euler Y", "Euler Z",
            "State"
        ]

        self.value_labels = {}
        self.packet_labels = {}

        # Connect SerialManager signal
        self.serial_manager.data_received.connect(self.update_data)

        # Build UI
        self.initUI()
        self.apply_modern_theme()

    def initUI(self):
        main_layout = QHBoxLayout(self)

        # Console Group
        console_group = QGroupBox("Console")
        console_group.setObjectName("card")
        console_layout = QVBoxLayout(console_group)

        # Command layout
        command_layout = QHBoxLayout()
        self.command_input = QLineEdit()
        self.command_input.setPlaceholderText("Enter Command")

        self.send_button = QPushButton("Send")
        self.clear_button = QPushButton("Clear")
        self.timestamp_checkbox = QCheckBox("Timestamp")
        self.timestamp_checkbox.setChecked(True)

        for btn in [self.send_button, self.clear_button]:
            btn.setMinimumWidth(100)

        command_layout.addWidget(self.command_input)
        command_layout.addWidget(self.send_button)
        command_layout.addWidget(self.clear_button)
        command_layout.addWidget(self.timestamp_checkbox)

        # Console output and raw telemetry
        split_layout = QHBoxLayout()
        self.console_output = QTextEdit()
        self.console_output.setReadOnly(True)
        split_layout.addWidget(self.console_output, 7)
        #split_layout.addWidget(self.raw_telemetry_display, 3)

        # Right-side layout
        right_side_layout = QVBoxLayout()

        # Command History
        self.command_history_list = QListWidget()
        command_history_group = QGroupBox("Command History")
        command_history_group.setObjectName("card")
        ch_layout = QVBoxLayout(command_history_group)
        ch_layout.addWidget(self.command_history_list)

        # Packet Info
        packet_info_group = QGroupBox("Packet Info")
        packet_info_group.setObjectName("card")
        packet_info_layout = QGridLayout(packet_info_group)
        packet_headers = [
            "Total Packets", "Missing Packets", "Packet Loss %",
            "Corrupt Packets", "Last Packet ID", "Last Packet Time"
        ]
        for row, name in enumerate(packet_headers):
            label = QLabel(f"{name}:")
            label.setFont(QFont("Poppins", 10, QFont.Bold))
            value_label = QLabel("-")
            value_label.setFont(QFont("Poppins", 11))
            self.packet_labels[name] = value_label
            packet_info_layout.addWidget(label, row, 0)
            packet_info_layout.addWidget(value_label, row, 1)
        packet_info_group.setFixedHeight(300)

        right_side_layout.addWidget(command_history_group)
        right_side_layout.addWidget(packet_info_group)
        split_layout.addLayout(right_side_layout, 3)

        console_layout.addLayout(command_layout)
        console_layout.addLayout(split_layout)
        main_layout.addWidget(console_group, 2)

        # Telemetry group
        telemetry_group = QGroupBox("Raw Telemetry")
        telemetry_group.setObjectName("card")
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)

        scroll_content = QWidget()
        telemetry_layout = QVBoxLayout(scroll_content)

        scroll_area.setWidget(scroll_content)

        telemetry_group_layout = QVBoxLayout(telemetry_group)
        telemetry_group_layout.addWidget(scroll_area)
        telemetry_values_layout = QGridLayout()
        for i, header in enumerate(self.headers):
                label = QLabel(f"{header}:")
                label.setFont(QFont("Poppins", 10, QFont.Bold))
                label.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Preferred)  # prevents shrinking
                label.setMinimumWidth(135)   # keeps label width stable

                value_label = QLabel("-")
                value_label.setFont(QFont("Poppins", 11))
                value_label.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Preferred)  # value expands
                value_label.setMinimumWidth(80)

                self.value_labels[header] = value_label
                telemetry_values_layout.addWidget(label, i, 0)
                telemetry_values_layout.addWidget(value_label, i, 1)
        telemetry_layout.addLayout(telemetry_values_layout)
        main_layout.addWidget(telemetry_group, 1)

        # Connect signals
        self.send_button.clicked.connect(self.send_command)
        self.clear_button.clicked.connect(self.clear_console)
        self.command_input.returnPressed.connect(self.send_command)
        self.command_history_list.itemClicked.connect(
            lambda item: self.command_input.setText(item.text())
        )

    def apply_modern_theme(self):
        palette = QPalette()
        palette.setColor(QPalette.Window, QColor("#F5F7FA"))
        palette.setColor(QPalette.WindowText, QColor("#111111"))
        self.setPalette(palette)

        self.setStyleSheet("""
            QWidget {
                background-color: qlineargradient(x1:0 y1:0, x2:1 y2:1,
                    stop:0 #F5F7FA, stop:1 #E8ECF1);
                color: #111111;
                font-family: "Poppins", "Segoe UI";
                
            }
            QGroupBox#card {
    border-radius: 14px;
    background: rgba(15, 45, 70, 0.55);
    border: 1px solid rgba(0, 229, 255, 0.4);
    margin-top: 10px;
    padding: 14px;
}

     QGroupBox#card::title {
    color: white;
    background: transparent;
    subcontrol-origin: margin;
    subcontrol-position: top left;
    padding-left: 10px;
    padding-top: -6px;
}


            QPushButton {
                background: qlineargradient(x1:0 y1:0, x2:1 y2:1,
                    stop:0 #0078D7, stop:1 #00B7C2);
                color: white;
                border: none;
                border-radius: 8px;
                padding: 8px 16px;
                font-family: "Poppins";
                
            }
            QPushButton:hover {
                background: qlineargradient(x1:0 y1:0, x2:1 y2:1,
                    stop:0 #0094FF, stop:1 #00D7E6);
            }
            QLineEdit, QListWidget, QTextEdit {
                background: rgba(255,255,255,0.9);
                border-radius: 8px;
                padding: 8px;
                border: 1px solid rgba(0,0,0,0.15);
                color: #111111;
                
            }
            
            /* ===== VERTICAL SCROLLBAR ===== */
QScrollBar:vertical {
    background: transparent;
    width: 8px;
    margin: 2px;
}

/* Handle */
QScrollBar::handle:vertical {
    background: rgba(120, 120, 120, 0.4);
    border-radius: 4px;
    min-height: 30px;
}

/* Hover effect */
QScrollBar::handle:vertical:hover {
    background: rgba(160, 160, 160, 0.7);
}

/* Pressed */
QScrollBar::handle:vertical:pressed {
    background: rgba(200, 200, 200, 0.9);
}

/* Remove arrows */
QScrollBar::add-line:vertical,
QScrollBar::sub-line:vertical {
    height: 0px;
}

/* Remove page background */
QScrollBar::add-page:vertical,
QScrollBar::sub-page:vertical {
    background: transparent;
}


/* ===== HORIZONTAL SCROLLBAR ===== */
QScrollBar:horizontal {
    background: transparent;
    height: 8px;
    margin: 2px;
}

/* Handle */
QScrollBar::handle:horizontal {
    background: rgba(120, 120, 120, 0.4);
    border-radius: 4px;
    min-width: 30px;
}

/* Hover */
QScrollBar::handle:horizontal:hover {
    background: rgba(160, 160, 160, 0.7);
}

/* Pressed */
QScrollBar::handle:horizontal:pressed {
    background: rgba(200, 200, 200, 0.9);
}

/* Remove arrows */
QScrollBar::add-line:horizontal,
QScrollBar::sub-line:horizontal {
    width: 0px;
}

/* Track */
QScrollBar::add-page:horizontal,
QScrollBar::sub-page:horizontal {
    background: transparent;
}
        """)

    # Send command through connected serial port
    def send_command(self):
        """Send a typed command to the transmitter via USB port."""
        command = self.command_input.text().strip()
        if not command:
            return

        timestamp = datetime.now().strftime("[%H:%M:%S] ") if self.timestamp_checkbox.isChecked() else ""
        self.console_output.append(f"{timestamp}> {command}")
        self.command_history_list.addItem(command)

        try:
            data_to_send = (command + "\r\n").encode('utf-8')
            self.serial_manager.send_data(data_to_send)
            self.console_output.append("[Command sent to transmitter]")
        except Exception as e:
            self.console_output.append(f"[Error sending command: {e}]")

        self.console_output.moveCursor(QTextCursor.End)
        self.command_input.clear()

    def clear_console(self):
        self.console_output.clear()
        
        
        for label in self.packet_labels.values():
            label.setText("-")
        for label in self.value_labels.values():
            label.setText("-")

    def update_data(self, data: str):
        
            self.console_output.append(data)
            self.console_output.moveCursor(QTextCursor.End)
            #self.raw_telemetry_display.append(data)
            self.parse_telemetry(data)
            self.update_packet_info(data)
            print("RX:", repr(data))
       

    def parse_telemetry(self, line: str):
        parts = [p.strip() for p in line.split(',')]

        for header, value in zip(self.headers[1:], parts):
            self.value_labels[header].setText(value)

        self.value_labels["Rocket_ID"].setText("TRI-100M")
    def extract_packet_id(self, parts):
        try:
            return int(parts[2])
        except Exception:
            return self.last_packet_id + 1

    def update_packet_info(self, line: str):
        parts = line.strip().split(',')
        if len(parts) < 3:
            self.corrupt_packets += 1
        else:
            try:
                packet_id = self.extract_packet_id(parts)
                if self.last_packet_id != -1 and packet_id > self.last_packet_id + 1:
                    self.missing_packets += packet_id - (self.last_packet_id + 1)
                self.last_packet_id = packet_id
                self.total_packets += 1
                self.last_packet_time = datetime.now().strftime("%H:%M:%S")
            except Exception:
                self.corrupt_packets += 1

        total_expected = self.total_packets + self.missing_packets
        packet_loss = (self.missing_packets / total_expected) * 100 if total_expected else 0

        self.packet_labels["Total Packets"].setText(str(self.total_packets))
        self.packet_labels["Missing Packets"].setText(str(self.missing_packets))
        self.packet_labels["Packet Loss %"].setText(f"{packet_loss:.2f}")
        self.packet_labels["Corrupt Packets"].setText(str(self.corrupt_packets))
        self.packet_labels["Last Packet ID"].setText(str(self.last_packet_id))
        self.packet_labels["Last Packet Time"].setText(self.last_packet_time)


'''if __name__ == "__main__":
    app = QApplication(sys.argv)
    serial_manager = SerialManager()
   
    window = ConsoleWindow(serial_manager)
    window.show()
    sys.exit(app.exec_())'''
