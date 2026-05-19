from dataclasses import field

from PyQt5 import QtCore, QtGui, QtWidgets
import matplotlib
from ics_rc import *
#from PyQt5.QtGui import QMovie
from PyQt5.QtWidgets import QWidget
#from PyQt5.QtGui import QFontDatabase
from stl_view import STLView
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure
import os
import sys
from serial_manager import SerialManager
from stl_view import STLView


def resource_path(relative_path):
        if hasattr(sys, '_MEIPASS'):
            base_path = sys._MEIPASS
        else:
            base_path = os.path.dirname(os.path.abspath(__file__))
        return os.path.join(base_path, relative_path)
    
class DbWindow(QtWidgets.QWidget):
   
    def __init__(self, serial_manager, stl_view):
        super().__init__()
        self.serial_manager = serial_manager
        self.stl_view = stl_view   

        self.setupUi(self)
        self.stl_view.setMinimumSize(0, 0)
        self.stl_view.setMaximumSize(QtCore.QSize(16777215, 16777215))
        #self.stl_view.setSizePolicy(QtWidgets.QSizePolicy.Ignored, QtWidgets.QSizePolicy.Ignored)
        self.stl_view.setSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Expanding)
        if self.serial_manager is not None:
           self.serial_manager.data_received.connect(self.update_data)
           self.serial_manager.data_received.connect(lambda data: self.update_stl_from_serial(data))
        
        self.progressBar_10.setMaximum(100)
        self.progressBar_11.setMaximum(100)
        self.progressBar_12.setMaximum(100)
        self.progressBar_13.setMaximum(100)
        self.progressBar_14.setMaximum(100)


        self.last_update_time = 0
        self.update_interval_ms = 200
        self.last_energy_time = QtCore.QDateTime.currentMSecsSinceEpoch()
        self.total_energy_Wh = 0.0

        # Set your battery capacity here (example: 2200mAh 3S Li-ion)
        self.battery_capacity_Wh = 11.1 * 2.2   # 11.1V × 2.2Ah = 24.42Wh

        self.telemetry_fields = [
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
            "Gyro Z", 
            "Mag X", "Mag Y", "Mag Z",
            "Euler X", "Euler Y", "Euler Z",
            "State", "Battery"
        ]

        # Core telemetry
        self.field_widgets = {
            # Rocket Info
            "Rocket_ID": self.label_59,
            "Mission Time": self.label_61,
            "Packet Count": self.label_17,

            # Core Telemetry
            "Altitude": self.label_19,
            "Pressure": self.label_21,
            "Load Voltage": self.label_23,
            "Load Current": self.label_25,

            # GPS
            "GPS Latitude": self.label_27,
            "GPS Longitude": self.label_141,

            # Accelerometer
            "Accel X": self.label_88,
            "Accel Y": self.label_91,
            "Accel Z": self.label_89,

            # Gyroscope
            "Gyro X": self.label_99,
            "Gyro Y": self.label_101,
            "Gyro Z": self.label_103,

            # Magnetometer
            "Mag X": self.label_93,
            "Mag Y": self.label_95,
            "Mag Z": self.label_97,

            # Euler Angles
            "Euler X": self.label_105,
            "Euler Y": self.label_107,
            "Euler Z": self.label_109,

            # State
            "State": self.label_62,

            # Battery 
            "Battery": self.progressBar_10,
        }
        self.state_map = {
            "0": "Boot",
            "1": "Testing",
            "2": "Launch",
            "3": "Ascent",
            "4": "Apogee",
            "5": "Aero Release",
            "6": "Descent",
            "7": "Impact",
            "8": "Recovery"
        }
        
    def setupUi(self, Form):
        Form.setObjectName("Form")
        Form.resize(900, 600)
        sizePolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Expanding)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(Form.sizePolicy().hasHeightForWidth())
        Form.setSizePolicy(sizePolicy)
        Form.setStyleSheet("""
/* ===== GLOBAL BACKGROUND (DARK HUD) ===== */
QWidget {
    background: qlineargradient(
        x1:0, y1:0, x2:1, y2:1,
        stop:0 #071B2E,
        stop:0.5 #0A2A47,
        stop:1 #031521
    );
    font-family: Electrolize;
}

/* ===== MAIN PANEL ===== */
QFrame#frame_2 {
    background: rgba(0, 180, 255, 0.08);
    border-radius: 18px;
    border: 1px solid rgba(0, 230, 255, 0.45);
}

/* ===== GLASS PANELS ===== */
QFrame#frame_30, QFrame#frame_31, QFrame#frame_16,
QFrame#frame_17, QFrame#frame_18, QFrame#frame_19,
QFrame#frame_20, QFrame#frame_21, QFrame#frame_12,
QFrame#frame_14, QFrame#frame_15,
QFrame#frame_22, QFrame#frame_23, QFrame#frame_32,
QFrame#frame_25, QFrame#frame_26, QFrame#frame_27,
QFrame#frame_28, QFrame#frame_29, QFrame#frame_40 {

    background: rgba(0, 200, 255, 0.06);
    border-radius: 14px;
    border: 1px solid rgba(0, 180, 255, 0.35);
}

/* ===== TRANSPARENT FRAMES ===== */
QFrame#frame_3,
QFrame#frame,
QFrame#frame_13,
QFrame#frame_24 {
    background: transparent;
    border: none;
}

/* ===== LABELS  ===== */
        QLabel {
            background: rgba(0, 80, 140, 0.95);   /* almost solid */
            color: #E6FBFF;                       /* very bright text */
            
            font-weight: 600;

            padding: 6px 10px;
            border-radius: 8px;

            border: 1px solid rgba(0, 220, 255, 0.85);
}

QLabel#valueLabel {
    background: rgba(0, 120, 200, 1);     /* FULL solid */
    color: #FFFFFF;

    
    font-weight: 700;

    border: 1px solid rgba(0, 255, 255, 1);
}
/* HOVER */
QLabel:hover {
    border: 1px solid rgba(0, 180, 255, 0.7);
    color: #A8E6FF;
}

/* HOVER (subtle glow, not neon) */
QLabel:hover {
    border: 1px solid rgba(0, 180, 255, 0.7);
    color: #A8E6FF;
}

/* HOVER EFFECT */
QLabel:hover {
    border: 1px solid rgba(0, 230, 255, 0.8);
}

/* ===== PROGRESS BAR ===== */
QProgressBar {
    background: rgba(5, 25, 45, 0.9);
    border-radius: 8px;
    border: 1px solid rgba(0, 180, 255, 0.4);
    height: 14px;
    text-align: center;
    color: #CFFAFF;
}

/* FIXED SYNTAX HERE */
QProgressBar::chunk {
    border-radius: 8px;
    background: qlineargradient(
        x1:0, y1:0, x2:1, y2:0,
        stop:0 #00E6FF,
        stop:0.5 #009DFF,
        stop:1 #66F7FF
    );
}
""")
        self.verticalLayout = QtWidgets.QVBoxLayout(Form)
        self.verticalLayout.setObjectName("verticalLayout")
        self.frame_2 = QtWidgets.QFrame(Form)
        sizePolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Expanding)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.frame_2.sizePolicy().hasHeightForWidth())
        self.frame_2.setSizePolicy(sizePolicy)
        self.frame_2.setMinimumSize(QtCore.QSize(0, 0))
        self.frame_2.setMaximumSize(QtCore.QSize(16777215, 1677215))
        self.frame_2.setFrameShape(QtWidgets.QFrame.Box)
        self.frame_2.setFrameShadow(QtWidgets.QFrame.Plain)
        self.frame_2.setObjectName("frame_2")
        self.horizontalLayout = QtWidgets.QHBoxLayout(self.frame_2)
        self.horizontalLayout.setSpacing(10)
        self.horizontalLayout.setContentsMargins(5, 0, 0, 0)
        self.horizontalLayout.setObjectName("horizontalLayout")
        self.frame_3 = QtWidgets.QFrame(self.frame_2)
        self.frame_3.setMinimumWidth(250)
        self.frame_3.setMaximumWidth(16777215)
        self.frame_3.setSizePolicy(QtWidgets.QSizePolicy.Preferred, QtWidgets.QSizePolicy.Expanding)
        self.frame_3.setFrameShape(QtWidgets.QFrame.Box)
        self.frame_3.setFrameShadow(QtWidgets.QFrame.Plain)
        self.frame_3.setObjectName("frame_3")
        self.gridLayout = QtWidgets.QGridLayout(self.frame_3)
        self.gridLayout.setHorizontalSpacing(0)
        self.gridLayout.setContentsMargins(0, 10, 5, 5)
        self.gridLayout.setObjectName("gridLayout")
        self.frame_30 = QtWidgets.QFrame(self.frame_3)
        sizePolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Expanding)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.frame_30.sizePolicy().hasHeightForWidth())
        self.frame_30.setSizePolicy(sizePolicy)
        self.frame_30.setMinimumWidth(120)
        self.frame_30.setSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Expanding)
        
        self.frame_30.setFrameShape(QtWidgets.QFrame.Box)
        self.frame_30.setFrameShadow(QtWidgets.QFrame.Plain)
        self.frame_30.setObjectName("frame_30")
        self.verticalLayout_21 = QtWidgets.QVBoxLayout(self.frame_30)
        self.verticalLayout_21.setContentsMargins(5, -1, -1, -1)
        self.verticalLayout_21.setObjectName("verticalLayout_21")
        self.label_58 = QtWidgets.QLabel(self.frame_30)
        sizePolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Fixed)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.label_58.sizePolicy().hasHeightForWidth())
        self.label_58.setSizePolicy(sizePolicy)
        self.label_58.setMinimumHeight(30)
        self.label_58.setSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Preferred)
        self.label_58.setFrameShape(QtWidgets.QFrame.Box)
        self.label_58.setAlignment(QtCore.Qt.AlignCenter)
        self.label_58.setObjectName("label_58")
        self.verticalLayout_21.addWidget(self.label_58)
        self.label_59 = QtWidgets.QLabel(self.frame_30)
        sizePolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Expanding)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.label_59.sizePolicy().hasHeightForWidth())
        self.label_59.setSizePolicy(sizePolicy)
        self.label_59.setMinimumHeight(30)
        self.label_59.setSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Preferred)
        font = QtGui.QFont()
        font.setFamily("Digital-7")
        font.setPointSize(max(8, 12))
        self.label_59.setFont(font)
        
        self.label_59.setFrameShape(QtWidgets.QFrame.Box)
        self.label_59.setAlignment(QtCore.Qt.AlignCenter)
        self.label_59.setText("TRI-100M")
        self.label_59.setIndent(1)
        self.label_59.setObjectName("label_59")
        self.verticalLayout_21.addWidget(self.label_59)
        self.gridLayout.addWidget(self.frame_30, 0, 0, 1, 1)
        self.frame_31 = QtWidgets.QFrame(self.frame_3)
        sizePolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Expanding)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.frame_31.sizePolicy().hasHeightForWidth())
        self.frame_31.setSizePolicy(sizePolicy)
        self.frame_31.setMinimumWidth(120)
        self.frame_31.setSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Expanding)
        self.frame_31.setFrameShape(QtWidgets.QFrame.Box)
        self.frame_31.setFrameShadow(QtWidgets.QFrame.Plain)
        self.frame_31.setObjectName("frame_31")
        self.verticalLayout_22 = QtWidgets.QVBoxLayout(self.frame_31)
        self.verticalLayout_22.setContentsMargins(5, -1, -1, -1)
        self.verticalLayout_22.setObjectName("verticalLayout_22")
        self.label_60 = QtWidgets.QLabel(self.frame_31)
        sizePolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Fixed)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.label_60.sizePolicy().hasHeightForWidth())
        self.label_60.setSizePolicy(sizePolicy)
        self.label_60.setMinimumHeight(30)
        self.label_60.setSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Preferred)
        self.label_60.setFrameShape(QtWidgets.QFrame.Box)
        self.label_60.setAlignment(QtCore.Qt.AlignCenter)
        self.label_60.setObjectName("label_60")
        self.verticalLayout_22.addWidget(self.label_60)
        self.label_61 = QtWidgets.QLabel(self.frame_31)
        sizePolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Expanding)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.label_61.sizePolicy().hasHeightForWidth())
        self.label_61.setSizePolicy(sizePolicy)
        self.label_61.setMinimumHeight(30)
        self.label_61.setSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Preferred)
        font = QtGui.QFont()
        font.setPointSize(max(8, 12))
        self.label_61.setFont(font)
        self.label_61.setFrameShape(QtWidgets.QFrame.Box)
        self.label_61.setAlignment(QtCore.Qt.AlignCenter)
        self.label_61.setText("")
        self.label_61.setIndent(1)
        self.label_61.setObjectName("label_61")
        self.verticalLayout_22.addWidget(self.label_61)
        self.gridLayout.addWidget(self.frame_31, 0, 1, 1, 1)
        self.frame_16 = QtWidgets.QFrame(self.frame_3)
        sizePolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Expanding)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.frame_16.sizePolicy().hasHeightForWidth())
        
        self.frame_16.setSizePolicy(sizePolicy)
        self.frame_16.setMinimumWidth(120)
        self.frame_16.setSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Expanding)
        self.frame_16.setFrameShape(QtWidgets.QFrame.Box)
        self.frame_16.setFrameShadow(QtWidgets.QFrame.Plain)
        self.frame_16.setObjectName("frame_16")
        self.verticalLayout_9 = QtWidgets.QVBoxLayout(self.frame_16)
        self.verticalLayout_9.setContentsMargins(5, -1, -1, -1)
        self.verticalLayout_9.setObjectName("verticalLayout_9")
        self.label_16 = QtWidgets.QLabel(self.frame_16)
        sizePolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Fixed)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.label_16.sizePolicy().hasHeightForWidth())
        self.label_16.setSizePolicy(sizePolicy)
        self.label_16.setMinimumHeight(30)
        self.label_16.setSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Preferred)
        self.label_16.setFrameShape(QtWidgets.QFrame.Box)
        self.label_16.setAlignment(QtCore.Qt.AlignCenter)
        self.label_16.setObjectName("label_16")
        self.verticalLayout_9.addWidget(self.label_16)
        self.label_17 = QtWidgets.QLabel(self.frame_16)
        sizePolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Expanding)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.label_17.sizePolicy().hasHeightForWidth())
        self.label_17.setSizePolicy(sizePolicy)
        self.label_17.setMinimumHeight(30)
        self.label_17.setSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Preferred)
        font = QtGui.QFont()
        font.setFamily("Digital-7")
        font.setPointSize(max(8, 12))
        self.label_17.setFont(font)
        self.label_17.setFrameShape(QtWidgets.QFrame.Box)
        self.label_17.setAlignment(QtCore.Qt.AlignCenter)
        self.label_17.setText("")
        self.label_17.setIndent(1)
        self.label_17.setObjectName("label_17")
        self.verticalLayout_9.addWidget(self.label_17)
        self.gridLayout.addWidget(self.frame_16, 1, 0, 1, 1)
        self.frame_17 = QtWidgets.QFrame(self.frame_3)
        sizePolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Preferred, QtWidgets.QSizePolicy.Expanding)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.frame_17.sizePolicy().hasHeightForWidth())
        self.frame_17.setSizePolicy(sizePolicy)
        self.frame_17.setMinimumWidth(120)
        self.frame_17.setSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Expanding)
        self.frame_17.setFrameShape(QtWidgets.QFrame.Box)
        self.frame_17.setFrameShadow(QtWidgets.QFrame.Plain)
        self.frame_17.setObjectName("frame_17")
        self.verticalLayout_10 = QtWidgets.QVBoxLayout(self.frame_17)
        self.verticalLayout_10.setContentsMargins(5, -1, -1, -1)
        self.verticalLayout_10.setObjectName("verticalLayout_10")
        self.label_18 = QtWidgets.QLabel(self.frame_17)
        sizePolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Fixed)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.label_18.sizePolicy().hasHeightForWidth())
        self.label_18.setSizePolicy(sizePolicy)
        self.label_18.setMinimumHeight(30)
        self.label_18.setSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Preferred)
        self.label_18.setFrameShape(QtWidgets.QFrame.Box)
        self.label_18.setAlignment(QtCore.Qt.AlignCenter)
        self.label_18.setObjectName("label_18")
        self.verticalLayout_10.addWidget(self.label_18)
        self.label_19 = QtWidgets.QLabel(self.frame_17)
        sizePolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Expanding)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.label_19.sizePolicy().hasHeightForWidth())
        self.label_19.setSizePolicy(sizePolicy)
        self.label_19.setMinimumHeight(30)
        self.label_19.setSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Preferred)
        font = QtGui.QFont()
        font.setFamily("Digital-7")
        font.setPointSize(max(8, 12))
        self.label_19.setFont(font)
        self.label_19.setFrameShape(QtWidgets.QFrame.Box)
        self.label_19.setAlignment(QtCore.Qt.AlignCenter)
        self.label_19.setText("")
        self.label_19.setIndent(1)
        self.label_19.setObjectName("label_19")
        self.verticalLayout_10.addWidget(self.label_19)
        self.gridLayout.addWidget(self.frame_17, 1, 1, 1, 1)
        self.frame_18 = QtWidgets.QFrame(self.frame_3)
        sizePolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Preferred, QtWidgets.QSizePolicy.Expanding)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.frame_18.sizePolicy().hasHeightForWidth())
        self.frame_18.setSizePolicy(sizePolicy)
        self.frame_18.setMinimumWidth(120)
        self.frame_18.setSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Expanding)
        self.frame_18.setFrameShape(QtWidgets.QFrame.Box)
        self.frame_18.setFrameShadow(QtWidgets.QFrame.Plain)
        self.frame_18.setObjectName("frame_18")
        self.verticalLayout_11 = QtWidgets.QVBoxLayout(self.frame_18)
        self.verticalLayout_11.setContentsMargins(5, -1, -1, -1)
        self.verticalLayout_11.setObjectName("verticalLayout_11")
        self.label_20 = QtWidgets.QLabel(self.frame_18)
        sizePolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Fixed)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.label_20.sizePolicy().hasHeightForWidth())
        self.label_20.setSizePolicy(sizePolicy)
        self.label_20.setMinimumHeight(30)
        self.label_20.setSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Preferred)
        self.label_20.setFrameShape(QtWidgets.QFrame.Box)
        self.label_20.setAlignment(QtCore.Qt.AlignCenter)
        self.label_20.setObjectName("label_20")
        self.verticalLayout_11.addWidget(self.label_20)
        self.label_21 = QtWidgets.QLabel(self.frame_18)
        sizePolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Expanding)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.label_21.sizePolicy().hasHeightForWidth())
        self.label_21.setSizePolicy(sizePolicy)
        self.label_21.setMinimumHeight(30)
        self.label_21.setSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Preferred)
        font = QtGui.QFont()
        font.setFamily("Digital-7")
        font.setPointSize(max(8, 12))
        self.label_21.setFont(font)
        
        self.label_21.setFrameShape(QtWidgets.QFrame.Box)
        self.label_21.setAlignment(QtCore.Qt.AlignCenter)
        self.label_21.setText("")
        self.label_21.setIndent(1)
        self.label_21.setObjectName("label_21")
        self.verticalLayout_11.addWidget(self.label_21)
        self.gridLayout.addWidget(self.frame_18, 2, 0, 1, 1)
        self.frame_19 = QtWidgets.QFrame(self.frame_3)
        sizePolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Preferred, QtWidgets.QSizePolicy.Expanding)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.frame_19.sizePolicy().hasHeightForWidth())
        self.frame_19.setSizePolicy(sizePolicy)
        self.frame_19.setMinimumWidth(120)
        self.frame_19.setSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Expanding)
        self.frame_19.setFrameShape(QtWidgets.QFrame.Box)
        self.frame_19.setFrameShadow(QtWidgets.QFrame.Plain)
        self.frame_19.setObjectName("frame_19")
        self.verticalLayout_12 = QtWidgets.QVBoxLayout(self.frame_19)
        self.verticalLayout_12.setContentsMargins(5, -1, -1, -1)
        self.verticalLayout_12.setObjectName("verticalLayout_12")
        self.label_22 = QtWidgets.QLabel(self.frame_19)
        sizePolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Fixed)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.label_22.sizePolicy().hasHeightForWidth())
        self.label_22.setSizePolicy(sizePolicy)
        self.label_22.setMinimumHeight(30)
        self.label_22.setSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Preferred)
        self.label_22.setFrameShape(QtWidgets.QFrame.Box)
        self.label_22.setAlignment(QtCore.Qt.AlignCenter)
        self.label_22.setObjectName("label_22")
        self.verticalLayout_12.addWidget(self.label_22)
        self.label_23 = QtWidgets.QLabel(self.frame_19)
        sizePolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Expanding)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.label_23.sizePolicy().hasHeightForWidth())
        self.label_23.setSizePolicy(sizePolicy)
        self.label_23.setMinimumHeight(30)
        self.label_23.setSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Preferred)
        font = QtGui.QFont()
        font.setFamily("Digital-7")
        font.setPointSize(max(8, 12))
        self.label_23.setFont(font)
        self.label_23.setFrameShape(QtWidgets.QFrame.Box)
        self.label_23.setAlignment(QtCore.Qt.AlignCenter)
        self.label_23.setText("")
        self.label_23.setIndent(1)
        self.label_23.setObjectName("label_23")
        self.verticalLayout_12.addWidget(self.label_23)
        self.gridLayout.addWidget(self.frame_19, 2, 1, 1, 1)
        self.frame_20 = QtWidgets.QFrame(self.frame_3)
        sizePolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Preferred, QtWidgets.QSizePolicy.Expanding)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.frame_20.sizePolicy().hasHeightForWidth())
        self.frame_20.setSizePolicy(sizePolicy)
        self.frame_20.setMinimumWidth(120)
        self.frame_20.setSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Expanding)
        self.frame_20.setFrameShape(QtWidgets.QFrame.Box)
        self.frame_20.setFrameShadow(QtWidgets.QFrame.Plain)
        self.frame_20.setObjectName("frame_20")
        self.verticalLayout_13 = QtWidgets.QVBoxLayout(self.frame_20)
        self.verticalLayout_13.setContentsMargins(5, -1, -1, -1)
        self.verticalLayout_13.setObjectName("verticalLayout_13")
        self.label_24 = QtWidgets.QLabel(self.frame_20)
        sizePolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Fixed)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.label_24.sizePolicy().hasHeightForWidth())
        self.label_24.setSizePolicy(sizePolicy)
        self.label_24.setMinimumHeight(30)
        self.label_24.setSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Preferred)
        self.label_24.setFrameShape(QtWidgets.QFrame.Box)
        self.label_24.setAlignment(QtCore.Qt.AlignCenter)
        self.label_24.setObjectName("label_24")
        self.verticalLayout_13.addWidget(self.label_24)
        self.label_25 = QtWidgets.QLabel(self.frame_20)
        sizePolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Expanding)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.label_25.sizePolicy().hasHeightForWidth())
        self.label_25.setSizePolicy(sizePolicy)
        self.label_25.setMinimumHeight(30)
        self.label_25.setSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Preferred)
        font = QtGui.QFont()
        font.setFamily("Digital-7")
        font.setPointSize(max(8, 12))
        self.label_25.setFont(font)
        self.label_25.setFrameShape(QtWidgets.QFrame.Box)
        self.label_25.setAlignment(QtCore.Qt.AlignCenter)
        self.label_25.setText("")
        self.label_25.setIndent(1)
        self.label_25.setObjectName("label_25")
        self.verticalLayout_13.addWidget(self.label_25)
        self.gridLayout.addWidget(self.frame_20, 3, 0, 1, 1)
        self.frame_21 = QtWidgets.QFrame(self.frame_3)
        sizePolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Preferred, QtWidgets.QSizePolicy.Expanding)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.frame_21.sizePolicy().hasHeightForWidth())
        self.frame_21.setSizePolicy(sizePolicy)
        self.frame_21.setMinimumWidth(120)
        self.frame_21.setSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Expanding)
        self.frame_21.setFrameShape(QtWidgets.QFrame.Box)
        self.frame_21.setFrameShadow(QtWidgets.QFrame.Plain)
        self.frame_21.setObjectName("frame_21")
        self.verticalLayout_14 = QtWidgets.QVBoxLayout(self.frame_21)
        self.verticalLayout_14.setContentsMargins(5, -1, -1, -1)
        self.verticalLayout_14.setObjectName("verticalLayout_14")
        self.label_26 = QtWidgets.QLabel(self.frame_21)
        sizePolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Fixed)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.label_26.sizePolicy().hasHeightForWidth())
        self.label_26.setSizePolicy(sizePolicy)
        self.label_26.setMinimumHeight(30)
        self.label_26.setSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Preferred)
        self.label_26.setFrameShape(QtWidgets.QFrame.Box)
        self.label_26.setAlignment(QtCore.Qt.AlignLeft | QtCore.Qt.AlignVCenter)
        self.label_26.setObjectName("label_26")
        self.verticalLayout_14.addWidget(self.label_26)
        self.label_27 = QtWidgets.QLabel(self.frame_21)
        sizePolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Expanding)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.label_27.sizePolicy().hasHeightForWidth())
        self.label_27.setSizePolicy(sizePolicy)
        self.label_27.setMinimumHeight(30)
        self.label_27.setSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Preferred)
        font = QtGui.QFont()
        font.setFamily("Digital-7")
        font.setPointSize(max(8, 12))
        self.label_27.setFont(font)
        
        self.label_27.setFrameShape(QtWidgets.QFrame.Box)
        self.label_27.setAlignment(QtCore.Qt.AlignLeft | QtCore.Qt.AlignVCenter)
        self.label_27.setText("")
        self.label_27.setIndent(1)
        self.label_27.setObjectName("label_27")
        self.verticalLayout_14.addWidget(self.label_27)
        self.gridLayout.addWidget(self.frame_21, 3, 1, 1, 1)
        #########################################################3
        self.frame_40 = QtWidgets.QFrame(self.frame_3)
        sizePolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Preferred, QtWidgets.QSizePolicy.Expanding)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.frame_40.sizePolicy().hasHeightForWidth())
        self.frame_40.setSizePolicy(sizePolicy)
        self.frame_40.setMinimumWidth(120)
        self.frame_40.setSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Expanding)
        self.frame_40.setFrameShape(QtWidgets.QFrame.Box)
        self.frame_40.setFrameShadow(QtWidgets.QFrame.Plain)
        self.frame_40.setObjectName("frame_40")
        self.verticalLayout_40 = QtWidgets.QVBoxLayout(self.frame_40)
        self.verticalLayout_40.setContentsMargins(5, 5, 5, 5)
        self.verticalLayout_40.setObjectName("verticalLayout_14")
        self.label_140 = QtWidgets.QLabel(self.frame_40)
        sizePolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Fixed)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.label_140.sizePolicy().hasHeightForWidth())
        self.label_140.setSizePolicy(sizePolicy)
        self.label_140.setMinimumHeight(30)
        self.label_140.setSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Preferred)
        self.label_140.setFrameShape(QtWidgets.QFrame.Box)
        self.label_140.setAlignment(QtCore.Qt.AlignLeft | QtCore.Qt.AlignVCenter)
        self.label_140.setObjectName("label_140")
        self.verticalLayout_40.addWidget(self.label_140)
        self.label_141 = QtWidgets.QLabel(self.frame_40)
        sizePolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Expanding)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.label_141.sizePolicy().hasHeightForWidth())
        self.label_141.setSizePolicy(sizePolicy)
        self.label_141.setMinimumHeight(30)
        self.label_141.setSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Preferred)
        font = QtGui.QFont()
        font.setFamily("Digital-7")
        font.setPointSize(max(8, 12))
        self.label_141.setFont(font)
        
        self.label_141.setFrameShape(QtWidgets.QFrame.Box)
        self.label_141.setAlignment(QtCore.Qt.AlignLeft | QtCore.Qt.AlignVCenter)
        self.label_141.setText("")
        self.label_141.setIndent(1)
        self.label_141.setObjectName("label_141")
        self.verticalLayout_40.addWidget(self.label_141)
        self.gridLayout.addWidget(self.frame_40, 4, 0, 1, 1)
        
        
        self.horizontalLayout.addWidget(self.frame_3)
        self.frame = QtWidgets.QFrame(self.frame_2)
        sizePolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Expanding)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.frame.sizePolicy().hasHeightForWidth())
        self.frame.setSizePolicy(sizePolicy)
        self.frame.setMinimumWidth(300)
        self.frame.setMaximumWidth(16777215)
        self.frame.setSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Expanding)
        self.frame.setFrameShape(QtWidgets.QFrame.Box)
        self.frame.setFrameShadow(QtWidgets.QFrame.Plain)
        self.frame.setObjectName("frame")
        self.verticalLayout_15 = QtWidgets.QVBoxLayout(self.frame)
        self.verticalLayout_15.setObjectName("verticalLayout_15")

        self.frame_12 = QtWidgets.QFrame(self.frame)
        sizePolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Preferred, QtWidgets.QSizePolicy.Preferred)
        self.frame_12.setSizePolicy(sizePolicy)
        self.frame_12.setMinimumHeight(200)
        self.frame_12.setFrameShape(QtWidgets.QFrame.Box)
        self.frame_12.setFrameShadow(QtWidgets.QFrame.Plain)
        self.frame_12.setObjectName("frame_12")
        self.stl_layout = QtWidgets.QVBoxLayout(self.frame_12)
        #self.stl_layout.setSizePolicy(QtWidgets.QSizePolicy.Fixed, QtWidgets.QSizePolicy.Fixed)
        self.stl_layout.setContentsMargins(0, 0, 0, 0)
        self.stl_layout.setSpacing(0)
        self.stl_layout.addWidget(self.stl_view)

        self.verticalLayout_15.addWidget(self.frame_12)
        
        self.frame_13 = QtWidgets.QFrame(self.frame)
        sizePolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Preferred)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.frame_13.sizePolicy().hasHeightForWidth())
        self.frame_13.setSizePolicy(sizePolicy)
        self.frame_13.setMinimumSize(QtCore.QSize(0, 10))
        self.frame_13.setMaximumSize(QtCore.QSize(16777215, 16777215))
        self.frame_13.setFrameShape(QtWidgets.QFrame.Box)
        self.frame_13.setFrameShadow(QtWidgets.QFrame.Plain)
        self.frame_13.setObjectName("frame_13")
        self.widget = QtWidgets.QWidget(self.frame_13)
        self.frame_13_layout = QtWidgets.QVBoxLayout(self.frame_13)
        self.frame_13_layout.setContentsMargins(0, 0, 0, 0)
        self.frame_13_layout.setSpacing(0)
        self.frame_13_layout.addWidget(self.widget)
        #self.widget.setGeometry(QtCore.QRect(10, 10, 521, 312))
        self.widget.setObjectName("widget")
        self.gridLayout_14 = QtWidgets.QGridLayout(self.widget)
        self.gridLayout_14.setContentsMargins(10, 10, 10, 20)
        self.gridLayout_14.setVerticalSpacing(6)
        self.gridLayout_14.setHorizontalSpacing(6)
        self.gridLayout_14.setObjectName("gridLayout_14")
        self.gridLayout_14.setRowStretch(0, 1)
        self.gridLayout_14.setRowStretch(1, 1)
        self.gridLayout_14.setColumnStretch(0, 1)
        self.gridLayout_14.setColumnStretch(1, 1)
        self.frame_14 = QtWidgets.QFrame(self.widget)
        sizePolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Expanding)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.frame_14.sizePolicy().hasHeightForWidth())
        self.frame_14.setSizePolicy(sizePolicy)
        self.frame_14.setMinimumSize(QtCore.QSize(200, 150))
        self.frame_14.setMaximumSize(QtCore.QSize(16777215, 16777215))
        self.frame_14.setFrameShape(QtWidgets.QFrame.Box)
        self.frame_14.setFrameShadow(QtWidgets.QFrame.Plain)
        self.frame_14.setObjectName("frame_14")
        self.horizontalLayout_10 = QtWidgets.QHBoxLayout(self.frame_14)
        self.horizontalLayout_10.setContentsMargins(4, 4, 4, 4)
        self.horizontalLayout_10.setObjectName("horizontalLayout_10")
        self.gridLayout_10 = QtWidgets.QGridLayout()
        self.gridLayout_10.setContentsMargins(8, 9, 9, 9)
        self.gridLayout_10.setSpacing(9)
        self.gridLayout_10.setObjectName("gridLayout_10")
        self.label_86 = QtWidgets.QLabel(self.frame_14)
        self.label_86.setFrameShape(QtWidgets.QFrame.Box)
        self.label_86.setAlignment(QtCore.Qt.AlignCenter)
        self.label_86.setObjectName("label_86")
        self.gridLayout_10.addWidget(self.label_86, 0, 0, 1, 1)
        self.label_87 = QtWidgets.QLabel(self.frame_14)
        self.label_87.setFrameShape(QtWidgets.QFrame.Box)
        self.label_87.setAlignment(QtCore.Qt.AlignCenter)
        self.label_87.setObjectName("label_87")
        self.gridLayout_10.addWidget(self.label_87, 1, 0, 1, 1)
        self.label_88 = QtWidgets.QLabel(self.frame_14)
        self.label_88.setFrameShape(QtWidgets.QFrame.Box)
        self.label_88.setAlignment(QtCore.Qt.AlignCenter)
        self.label_88.setText("")
        self.label_88.setObjectName("label_88")
        self.gridLayout_10.addWidget(self.label_88, 0, 1, 1, 1)
        self.label_89 = QtWidgets.QLabel(self.frame_14)
        self.label_89.setFrameShape(QtWidgets.QFrame.Box)
        self.label_89.setAlignment(QtCore.Qt.AlignCenter)
        self.label_89.setText("")
        self.label_89.setObjectName("label_89")
        self.gridLayout_10.addWidget(self.label_89, 2, 1, 1, 1)
        self.label_90 = QtWidgets.QLabel(self.frame_14)
        self.label_90.setFrameShape(QtWidgets.QFrame.Box)
        self.label_90.setAlignment(QtCore.Qt.AlignCenter)
        self.label_90.setObjectName("label_90")
        self.gridLayout_10.addWidget(self.label_90, 2, 0, 1, 1)
        self.label_91 = QtWidgets.QLabel(self.frame_14)
        self.label_91.setFrameShape(QtWidgets.QFrame.Box)
        self.label_91.setAlignment(QtCore.Qt.AlignCenter)
        self.label_91.setText("")
        self.label_91.setObjectName("label_91")
        self.gridLayout_10.addWidget(self.label_91, 1, 1, 1, 1)
        self.horizontalLayout_10.addLayout(self.gridLayout_10)
        self.gridLayout_14.addWidget(self.frame_14, 0, 0, 1, 1)
        self.frame_22 = QtWidgets.QFrame(self.widget)
        sizePolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Expanding)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.frame_22.sizePolicy().hasHeightForWidth())
        self.frame_22.setSizePolicy(sizePolicy)
        self.frame_22.setMinimumSize(QtCore.QSize(200, 150))
        self.frame_22.setMaximumSize(QtCore.QSize(16777215, 16777215))
        self.frame_22.setFrameShape(QtWidgets.QFrame.Box)
        self.frame_22.setFrameShadow(QtWidgets.QFrame.Plain)
        self.frame_22.setObjectName("frame_22")
        self.horizontalLayout_12 = QtWidgets.QHBoxLayout(self.frame_22)
        self.horizontalLayout_12.setContentsMargins(8, -1, -1, -1)
        self.horizontalLayout_12.setObjectName("horizontalLayout_12")
        self.gridLayout_12 = QtWidgets.QGridLayout()
        self.gridLayout_12.setContentsMargins(9, 9, 9, 9)
        self.gridLayout_12.setSpacing(9)
        self.gridLayout_12.setObjectName("gridLayout_12")
        self.label_98 = QtWidgets.QLabel(self.frame_22)
        self.label_98.setFrameShape(QtWidgets.QFrame.Box)
        self.label_98.setAlignment(QtCore.Qt.AlignCenter)
        self.label_98.setObjectName("label_98")
        self.gridLayout_12.addWidget(self.label_98, 0, 0, 1, 1)
        self.label_99 = QtWidgets.QLabel(self.frame_22)
        self.label_99.setFrameShape(QtWidgets.QFrame.Box)
        self.label_99.setAlignment(QtCore.Qt.AlignCenter)
        self.label_99.setText("")
        self.label_99.setObjectName("label_99")
        self.gridLayout_12.addWidget(self.label_99, 0, 1, 1, 1)
        self.label_100 = QtWidgets.QLabel(self.frame_22)
        self.label_100.setFrameShape(QtWidgets.QFrame.Box)
        self.label_100.setAlignment(QtCore.Qt.AlignCenter)
        self.label_100.setObjectName("label_100")
        self.gridLayout_12.addWidget(self.label_100, 1, 0, 1, 1)
        self.label_101 = QtWidgets.QLabel(self.frame_22)
        self.label_101.setFrameShape(QtWidgets.QFrame.Box)
        self.label_101.setAlignment(QtCore.Qt.AlignCenter)
        self.label_101.setText("")
        self.label_101.setObjectName("label_101")
        self.gridLayout_12.addWidget(self.label_101, 1, 1, 1, 1)
        self.label_102 = QtWidgets.QLabel(self.frame_22)
        self.label_102.setFrameShape(QtWidgets.QFrame.Box)
        self.label_102.setAlignment(QtCore.Qt.AlignCenter)
        #self.label_102.setAlignment(QtCore.Qt.AlignCenter)
        self.label_102.setObjectName("label_102")
        self.gridLayout_12.addWidget(self.label_102, 2, 0, 1, 1)
        self.label_103 = QtWidgets.QLabel(self.frame_22)
        self.label_103.setFrameShape(QtWidgets.QFrame.Box)
        self.label_103.setAlignment(QtCore.Qt.AlignCenter)
        self.label_103.setText("")
        self.label_103.setObjectName("label_103")
        self.gridLayout_12.addWidget(self.label_103, 2, 1, 1, 1)
        self.horizontalLayout_12.addLayout(self.gridLayout_12)
        self.gridLayout_14.addWidget(self.frame_22, 0, 1, 1, 1)
        self.frame_15 = QtWidgets.QFrame(self.widget)
        sizePolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Expanding)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.frame_15.sizePolicy().hasHeightForWidth())
        self.frame_15.setSizePolicy(sizePolicy)
        self.frame_15.setMinimumSize(QtCore.QSize(200, 140))
        self.frame_15.setMaximumSize(QtCore.QSize(16777215, 16777215))
        self.frame_15.setFrameShape(QtWidgets.QFrame.Box)
        self.frame_15.setFrameShadow(QtWidgets.QFrame.Plain)
        self.frame_15.setObjectName("frame_15")
        self.horizontalLayout_11 = QtWidgets.QHBoxLayout(self.frame_15)
        self.horizontalLayout_11.setObjectName("horizontalLayout_11")
        self.gridLayout_11 = QtWidgets.QGridLayout()
        self.gridLayout_11.setContentsMargins(9, 9, 9, 9)
        self.gridLayout_11.setSpacing(9)
        self.gridLayout_11.setObjectName("gridLayout_11")
        self.label_92 = QtWidgets.QLabel(self.frame_15)
        self.label_92.setFrameShape(QtWidgets.QFrame.Box)
        self.label_92.setAlignment(QtCore.Qt.AlignCenter)
        self.label_92.setObjectName("label_92")
        self.gridLayout_11.addWidget(self.label_92, 0, 0, 1, 1)
        self.label_93 = QtWidgets.QLabel(self.frame_15)
        self.label_93.setFrameShape(QtWidgets.QFrame.Box)
        self.label_93.setAlignment(QtCore.Qt.AlignCenter)
        self.label_93.setText("")
        self.label_93.setObjectName("label_93")
        self.gridLayout_11.addWidget(self.label_93, 0, 1, 1, 1)
        self.label_94 = QtWidgets.QLabel(self.frame_15)
        self.label_94.setFrameShape(QtWidgets.QFrame.Box)
        self.label_94.setAlignment(QtCore.Qt.AlignCenter)
        self.label_94.setObjectName("label_94")
        self.gridLayout_11.addWidget(self.label_94, 1, 0, 1, 1)
        self.label_95 = QtWidgets.QLabel(self.frame_15)
        self.label_95.setFrameShape(QtWidgets.QFrame.Box)
        self.label_95.setAlignment(QtCore.Qt.AlignCenter)
        self.label_95.setText("")
        self.label_95.setObjectName("label_95")
        self.gridLayout_11.addWidget(self.label_95, 1, 1, 1, 1)
        self.label_96 = QtWidgets.QLabel(self.frame_15)
        self.label_96.setFrameShape(QtWidgets.QFrame.Box)
        self.label_96.setAlignment(QtCore.Qt.AlignCenter)
        self.label_96.setObjectName("label_96")
        self.gridLayout_11.addWidget(self.label_96, 2, 0, 1, 1)
        self.label_97 = QtWidgets.QLabel(self.frame_15)
        self.label_97.setFrameShape(QtWidgets.QFrame.Box)
        self.label_97.setAlignment(QtCore.Qt.AlignCenter)
        self.label_97.setText("")
        self.label_97.setObjectName("label_97")
        self.gridLayout_11.addWidget(self.label_97, 2, 1, 1, 1)
        self.horizontalLayout_11.addLayout(self.gridLayout_11)
        self.gridLayout_14.addWidget(self.frame_15, 1, 0, 1, 1)
        self.frame_23 = QtWidgets.QFrame(self.widget)
        sizePolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Expanding)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.frame_23.sizePolicy().hasHeightForWidth())
        self.frame_23.setSizePolicy(sizePolicy)
        self.frame_23.setMinimumSize(QtCore.QSize(200, 140))
        self.frame_23.setMaximumSize(QtCore.QSize(16777215, 16777215))
        self.frame_23.setFrameShape(QtWidgets.QFrame.Box)
        self.frame_23.setFrameShadow(QtWidgets.QFrame.Plain)
        self.frame_23.setObjectName("frame_23")
        self.horizontalLayout_13 = QtWidgets.QHBoxLayout(self.frame_23)
        self.horizontalLayout_13.setContentsMargins(8, -1, -1, -1)
        self.horizontalLayout_13.setSpacing(9)
        self.horizontalLayout_13.setObjectName("horizontalLayout_13")
        self.gridLayout_13 = QtWidgets.QGridLayout()
        self.gridLayout_13.setContentsMargins(9, 9, 9, 9)
        self.gridLayout_13.setSpacing(9)
        self.gridLayout_13.setObjectName("gridLayout_13")
        self.label_104 = QtWidgets.QLabel(self.frame_23)
        self.label_104.setFrameShape(QtWidgets.QFrame.Box)
        self.label_104.setAlignment(QtCore.Qt.AlignCenter)
        self.label_104.setObjectName("label_104")
        self.gridLayout_13.addWidget(self.label_104, 0, 0, 1, 1)
        self.label_105 = QtWidgets.QLabel(self.frame_23)
        self.label_105.setFrameShape(QtWidgets.QFrame.Box)
        self.label_105.setAlignment(QtCore.Qt.AlignCenter)
        self.label_105.setText("")
        self.label_105.setObjectName("label_105")
        self.gridLayout_13.addWidget(self.label_105, 0, 1, 1, 1)
        self.label_106 = QtWidgets.QLabel(self.frame_23)
        self.label_106.setFrameShape(QtWidgets.QFrame.Box)
        self.label_106.setAlignment(QtCore.Qt.AlignCenter)
        self.label_106.setObjectName("label_106")
        self.gridLayout_13.addWidget(self.label_106, 1, 0, 1, 1)
        self.label_107 = QtWidgets.QLabel(self.frame_23)
        self.label_107.setFrameShape(QtWidgets.QFrame.Box)
        self.label_107.setAlignment(QtCore.Qt.AlignCenter)
        self.label_107.setText("")
        self.label_107.setObjectName("label_107")
        self.gridLayout_13.addWidget(self.label_107, 1, 1, 1, 1)
        self.label_108 = QtWidgets.QLabel(self.frame_23)
        self.label_108.setFrameShape(QtWidgets.QFrame.Box)
        self.label_108.setAlignment(QtCore.Qt.AlignCenter)
        self.label_108.setAlignment(QtCore.Qt.AlignCenter)
        self.label_108.setObjectName("label_108")
        self.gridLayout_13.addWidget(self.label_108, 2, 0, 1, 1)
        self.label_109 = QtWidgets.QLabel(self.frame_23)
        self.label_109.setFrameShape(QtWidgets.QFrame.Box)
        self.label_109.setAlignment(QtCore.Qt.AlignCenter)
        self.label_109.setText("")
        self.label_109.setObjectName("label_109")
        self.gridLayout_13.addWidget(self.label_109, 2, 1, 1, 1)
        self.horizontalLayout_13.addLayout(self.gridLayout_13)
        self.gridLayout_14.addWidget(self.frame_23, 1, 1, 1, 1)
        self.verticalLayout_15.addWidget(self.frame_13)
        self.verticalLayout_15.setStretch(0, 4)  # STL gets 30%
        self.verticalLayout_15.setStretch(1, 6)  # sensors get 70%
        self.horizontalLayout.addWidget(self.frame)
        self.frame_24 = QtWidgets.QFrame(self.frame_2)
        sizePolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Preferred, QtWidgets.QSizePolicy.MinimumExpanding)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.frame_24.sizePolicy().hasHeightForWidth())
        self.frame_24.setSizePolicy(sizePolicy)
        self.frame_24.setMinimumSize(QtCore.QSize(250, 300))
        self.frame_24.setMaximumHeight(16777215)
        self.frame_24.setSizePolicy(QtWidgets.QSizePolicy.Preferred, QtWidgets.QSizePolicy.Expanding)        
        self.frame_24.setFrameShape(QtWidgets.QFrame.Box)
        self.frame_24.setFrameShadow(QtWidgets.QFrame.Plain)
        self.frame_24.setObjectName("frame_24")
        self.verticalLayout_8 = QtWidgets.QVBoxLayout(self.frame_24)
        self.verticalLayout_8.setAlignment(QtCore.Qt.AlignTop)
        self.verticalLayout_8.setSizeConstraint(QtWidgets.QLayout.SetMaximumSize)
        self.verticalLayout_8.setContentsMargins(5, 5, 5, 5)
        self.verticalLayout_8.setSpacing(10)
        self.verticalLayout_8.setObjectName("verticalLayout_8")
        self.frame_32 = QtWidgets.QFrame(self.frame_24)
        sizePolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Preferred, QtWidgets.QSizePolicy.Fixed)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.frame_32.sizePolicy().hasHeightForWidth())
        self.frame_32.setSizePolicy(sizePolicy)
        self.frame_32.setFrameShape(QtWidgets.QFrame.Box)
        self.frame_32.setFrameShadow(QtWidgets.QFrame.Plain)
        self.frame_32.setObjectName("frame_32")
        self.verticalLayout_7 = QtWidgets.QVBoxLayout(self.frame_32)
        self.verticalLayout_7.setObjectName("verticalLayout_7")
        self.label_62 = QtWidgets.QLabel(self.frame_32)
        sizePolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Preferred, QtWidgets.QSizePolicy.Fixed)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.label_62.sizePolicy().hasHeightForWidth())
        self.label_62.setSizePolicy(sizePolicy)
        self.label_62.setMinimumSize(QtCore.QSize(0, 40))
        self.label_62.setFrameShape(QtWidgets.QFrame.Box)
        self.label_62.setAlignment(QtCore.Qt.AlignLeading|QtCore.Qt.AlignLeft|QtCore.Qt.AlignVCenter)
        self.label_62.setObjectName("label_62")
        self.verticalLayout_7.addWidget(self.label_62)
        self.verticalLayout_8.addWidget(self.frame_32)
        self.frame_25 = QtWidgets.QFrame(self.frame_24)
        sizePolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Preferred, QtWidgets.QSizePolicy.Fixed)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.frame_25.sizePolicy().hasHeightForWidth())
        self.frame_25.setSizePolicy(sizePolicy)
        self.frame_25.setFrameShape(QtWidgets.QFrame.Box)
        self.frame_25.setFrameShadow(QtWidgets.QFrame.Plain)
        self.frame_25.setObjectName("frame_25")
        self.verticalLayout_2 = QtWidgets.QVBoxLayout(self.frame_25)
        self.verticalLayout_2.setObjectName("verticalLayout_2")
        self.label_63 = QtWidgets.QLabel(self.frame_25)
        sizePolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Preferred, QtWidgets.QSizePolicy.Fixed)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.label_63.sizePolicy().hasHeightForWidth())
        self.label_63.setSizePolicy(sizePolicy)
        self.label_63.setMinimumSize(QtCore.QSize(0, 40))
        self.label_63.setFrameShape(QtWidgets.QFrame.Box)
        self.label_63.setAlignment(QtCore.Qt.AlignCenter)
        self.label_63.setObjectName("label_63")
        self.verticalLayout_2.addWidget(self.label_63)
        self.progressBar_10 = QtWidgets.QProgressBar(self.frame_25)
        sizePolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Preferred, QtWidgets.QSizePolicy.Fixed)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.progressBar_10.sizePolicy().hasHeightForWidth())
        self.progressBar_10.setSizePolicy(sizePolicy)
        self.progressBar_10.setMinimumSize(QtCore.QSize(110, 15))
        self.progressBar_10.setStyleSheet("")
        self.progressBar_10.setMaximum(100)
        self.progressBar_10.setProperty("value", 24)
        self.progressBar_10.setObjectName("progressBar_10")
        self.verticalLayout_2.addWidget(self.progressBar_10)
        self.verticalLayout_8.addWidget(self.frame_25)
        self.frame_26 = QtWidgets.QFrame(self.frame_24)
        sizePolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Preferred, QtWidgets.QSizePolicy.Fixed)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.frame_26.sizePolicy().hasHeightForWidth())
        self.frame_26.setSizePolicy(sizePolicy)
        self.frame_26.setFrameShape(QtWidgets.QFrame.Box)
        self.frame_26.setFrameShadow(QtWidgets.QFrame.Plain)
        self.frame_26.setObjectName("frame_26")
        self.verticalLayout_3 = QtWidgets.QVBoxLayout(self.frame_26)
        self.verticalLayout_3.setObjectName("verticalLayout_3")
        self.label_64 = QtWidgets.QLabel(self.frame_26)
        sizePolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Preferred, QtWidgets.QSizePolicy.Fixed)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.label_64.sizePolicy().hasHeightForWidth())
        self.label_64.setSizePolicy(sizePolicy)
        self.label_64.setMinimumSize(QtCore.QSize(0, 40))
        self.label_64.setFrameShape(QtWidgets.QFrame.Box)
        self.label_64.setAlignment(QtCore.Qt.AlignCenter)
        self.label_64.setObjectName("label_64")
        self.verticalLayout_3.addWidget(self.label_64)
        self.progressBar_11 = QtWidgets.QProgressBar(self.frame_26)
        sizePolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Preferred, QtWidgets.QSizePolicy.Fixed)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.progressBar_11.sizePolicy().hasHeightForWidth())
        self.progressBar_11.setSizePolicy(sizePolicy)
        self.progressBar_11.setMinimumSize(QtCore.QSize(110, 15))
        self.progressBar_11.setStyleSheet("")
        self.progressBar_11.setMaximum(100)
        self.progressBar_11.setProperty("value", 24)
        self.progressBar_11.setObjectName("progressBar_11")
        self.verticalLayout_3.addWidget(self.progressBar_11)
        self.verticalLayout_8.addWidget(self.frame_26)
        self.frame_27 = QtWidgets.QFrame(self.frame_24)
        sizePolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Preferred, QtWidgets.QSizePolicy.Fixed)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.frame_27.sizePolicy().hasHeightForWidth())
        self.frame_27.setSizePolicy(sizePolicy)
        self.frame_27.setFrameShape(QtWidgets.QFrame.Box)
        self.frame_27.setFrameShadow(QtWidgets.QFrame.Plain)
        self.frame_27.setObjectName("frame_27")
        self.verticalLayout_4 = QtWidgets.QVBoxLayout(self.frame_27)
        self.verticalLayout_4.setObjectName("verticalLayout_4")
        self.label_65 = QtWidgets.QLabel(self.frame_27)
        sizePolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Preferred, QtWidgets.QSizePolicy.Fixed)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.label_65.sizePolicy().hasHeightForWidth())
        self.label_65.setSizePolicy(sizePolicy)
        self.label_65.setMinimumSize(QtCore.QSize(0, 40))
        self.label_65.setFrameShape(QtWidgets.QFrame.Box)
        self.label_65.setAlignment(QtCore.Qt.AlignCenter)
        self.label_65.setObjectName("label_65")
        self.verticalLayout_4.addWidget(self.label_65)
        self.progressBar_12 = QtWidgets.QProgressBar(self.frame_27)
        sizePolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Preferred, QtWidgets.QSizePolicy.Fixed)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.progressBar_12.sizePolicy().hasHeightForWidth())
        self.progressBar_12.setSizePolicy(sizePolicy)
        self.progressBar_12.setMinimumSize(QtCore.QSize(110, 15))
        self.progressBar_12.setStyleSheet("")
        self.progressBar_12.setMaximum(100)
        self.progressBar_12.setProperty("value", 24)
        self.progressBar_12.setObjectName("progressBar_12")
        self.verticalLayout_4.addWidget(self.progressBar_12)
        self.verticalLayout_8.addWidget(self.frame_27)
        self.frame_28 = QtWidgets.QFrame(self.frame_24)
        sizePolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Preferred, QtWidgets.QSizePolicy.Fixed)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.frame_28.sizePolicy().hasHeightForWidth())
        self.frame_28.setSizePolicy(sizePolicy)
        self.frame_28.setFrameShape(QtWidgets.QFrame.Box)
        self.frame_28.setFrameShadow(QtWidgets.QFrame.Plain)
        self.frame_28.setObjectName("frame_28")
        self.verticalLayout_5 = QtWidgets.QVBoxLayout(self.frame_28)
        self.verticalLayout_5.setObjectName("verticalLayout_5")
        self.label_66 = QtWidgets.QLabel(self.frame_28)
        sizePolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Preferred, QtWidgets.QSizePolicy.Fixed)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.label_66.sizePolicy().hasHeightForWidth())
        self.label_66.setSizePolicy(sizePolicy)
        self.label_66.setMinimumSize(QtCore.QSize(0, 40))
        self.label_66.setFrameShape(QtWidgets.QFrame.Box)
        self.label_66.setAlignment(QtCore.Qt.AlignCenter)
        self.label_66.setObjectName("label_66")
        self.verticalLayout_5.addWidget(self.label_66)
        self.progressBar_13 = QtWidgets.QProgressBar(self.frame_28)
        sizePolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Preferred, QtWidgets.QSizePolicy.Fixed)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.progressBar_13.sizePolicy().hasHeightForWidth())
        self.progressBar_13.setSizePolicy(sizePolicy)
        self.progressBar_13.setMinimumSize(QtCore.QSize(110, 15))
        self.progressBar_13.setStyleSheet("")
        self.progressBar_13.setMaximum(100)
        self.progressBar_13.setProperty("value", 24)
        self.progressBar_13.setObjectName("progressBar_13")
        self.verticalLayout_5.addWidget(self.progressBar_13)
        self.verticalLayout_8.addWidget(self.frame_28)
        self.frame_29 = QtWidgets.QFrame(self.frame_24)
        sizePolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Preferred, QtWidgets.QSizePolicy.Fixed)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.frame_29.sizePolicy().hasHeightForWidth())
        self.frame_29.setSizePolicy(sizePolicy)
        self.frame_29.setFrameShape(QtWidgets.QFrame.Box)
        self.frame_29.setFrameShadow(QtWidgets.QFrame.Plain)
        self.frame_29.setObjectName("frame_29")
        self.verticalLayout_6 = QtWidgets.QVBoxLayout(self.frame_29)
        self.verticalLayout_6.setObjectName("verticalLayout_6")
        self.label_67 = QtWidgets.QLabel(self.frame_29)
        sizePolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Preferred, QtWidgets.QSizePolicy.Fixed)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.label_67.sizePolicy().hasHeightForWidth())
        self.label_67.setSizePolicy(sizePolicy)
        self.label_67.setMinimumSize(QtCore.QSize(0, 40))
        self.label_67.setFrameShape(QtWidgets.QFrame.Box)
        self.label_67.setAlignment(QtCore.Qt.AlignCenter)
        self.label_67.setObjectName("label_67")
        self.verticalLayout_6.addWidget(self.label_67)
        self.progressBar_14 = QtWidgets.QProgressBar(self.frame_29)
        sizePolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Preferred, QtWidgets.QSizePolicy.Fixed)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.progressBar_14.sizePolicy().hasHeightForWidth())
        self.progressBar_14.setSizePolicy(sizePolicy)
        self.progressBar_14.setMinimumSize(QtCore.QSize(110, 15))
        self.progressBar_14.setStyleSheet("")
        self.progressBar_14.setMaximum(100)
        self.progressBar_14.setProperty("value", 24)
        self.progressBar_14.setObjectName("progressBar_14")
        self.verticalLayout_6.addWidget(self.progressBar_14)
        self.verticalLayout_8.addWidget(self.frame_29)
        self.horizontalLayout.addWidget(self.frame_24)
        self.horizontalLayout.setStretch(0, 2)  # left panel
        self.horizontalLayout.setStretch(1, 4)  # center panel
        self.horizontalLayout.setStretch(2, 2)  # right panel
        self.verticalLayout.addWidget(self.frame_2)

        
        QtCore.QMetaObject.connectSlotsByName(Form)
        self.retranslateUi(Form)

    def retranslateUi(self, Form):
        _translate = QtCore.QCoreApplication.translate
        Form.setWindowTitle(_translate("Form", "Form"))

        self.label_58.setText(_translate("Form", "Rocket_ID"))
        self.label_60.setText(_translate("Form", "Mission Time"))
        self.label_16.setText(_translate("Form", "Packet Count"))
        self.label_18.setText(_translate("Form", "Altitude"))
        self.label_20.setText(_translate("Form", "Pressure"))
        self.label_22.setText(_translate("Form", "Load Voltage"))
        self.label_24.setText(_translate("Form", "Load Current"))
        self.label_26.setText(_translate("Form", "GPS Latitude"))
        
        self.label_86.setText(_translate("Form", "Accel  X"))
        self.label_87.setText(_translate("Form", "Accel Y"))
        self.label_90.setText(_translate("Form", "Accel  Z"))
        self.label_98.setText(_translate("Form", "Gyro  X"))
        self.label_100.setText(_translate("Form", "Gyro  Y"))
        self.label_102.setText(_translate("Form", "Gyro  Z"))
        self.label_92.setText(_translate("Form", "Mag X"))
        self.label_94.setText(_translate("Form", "Mag  Y"))
        self.label_96.setText(_translate("Form", "Mag Z"))
        self.label_104.setText(_translate("Form", "Euler X"))
        self.label_106.setText(_translate("Form", "Euler Y"))
        self.label_108.setText(_translate("Form", "Euler  Z"))
        self.label_62.setText(_translate("Form", "  STATUS:"))
        self.label_63.setText(_translate("Form", "Battery"))
        self.label_64.setText(_translate("Form", "Altitude"))
        self.label_65.setText(_translate("Form", "Power Consumption"))
        self.label_66.setText(_translate("Form", "Load Voltage"))
        self.label_67.setText(_translate("Form", "Pressure"))
        self.label_140.setText(_translate("Form", "GPS Longitude"))

    
    
    @QtCore.pyqtSlot(str)
    @QtCore.pyqtSlot(object)
    def update_data(self, data):

        current_time = QtCore.QDateTime.currentMSecsSinceEpoch()
        self.last_update_time = current_time

        try:
            
            values = data.strip().split(",")
            expected_len = len(self.telemetry_fields) - 1
            if len(values) < expected_len:
                return
            telemetry = dict(zip(self.telemetry_fields[1:], values))

            # ---------------- Update Labels ----------------
            for field, widget in self.field_widgets.items():
                if field in telemetry and isinstance(widget, QtWidgets.QLabel):

                    if field == "Rocket_ID":
                        widget.setText("TRI-100M")

                    elif field == "State":
                        state_value = telemetry.get("State", "").strip()
                        state_text = self.state_map.get(state_value, "Unknown")
                        widget.setText(f"  STATUS: {state_text}")

                    else:
                        widget.setText(str(telemetry.get(field, "")))
                    
            # ---------------- Convert Telemetry ----------------
            altitude = float(telemetry.get("Altitude", 0))
            pressure = float(telemetry.get("Pressure", 0))
            voltage = float(telemetry.get("Load Voltage", 0))
            current = float(telemetry.get("Load Current", 0))

            # ---------------- Power Calculation ----------------
            power = voltage * current

            # ---------------- Battery Calculation ----------------
            now = QtCore.QDateTime.currentMSecsSinceEpoch()
            dt = (now - self.last_energy_time) / 3600000.0
            self.last_energy_time = now

            self.total_energy_Wh += power * dt

            remaining_energy = max(0, self.battery_capacity_Wh - self.total_energy_Wh)
            battery_percent = int((remaining_energy / self.battery_capacity_Wh) * 100)

            # ---------------- Percent Calculations ----------------
            altitude_percent = int((altitude / 1000) * 100)
            pressure_percent = int((pressure / 1100) * 100)
            power_percent = int((power / 50) * 100)

            # Clamp values
            altitude_percent = max(0, min(100, altitude_percent))
            pressure_percent = max(0, min(100, pressure_percent))
            power_percent = max(0, min(100, power_percent))
            battery_percent = int((voltage * 100) - 700)
            battery_percent = max(0, min(100, battery_percent))
            voltage_percent = int((voltage / 12) * 100)
            voltage_percent = max(0, min(100, voltage_percent))

            # ---------------- Update Progress Bars ----------------

            # Battery
            self.progressBar_10.setRange(0,100)
            self.progressBar_10.setValue(battery_percent)

            # Altitude
            self.progressBar_11.setRange(0,100)
            self.progressBar_11.setValue(altitude_percent)
            
            self.progressBar_13.setRange(0,100)
            self.progressBar_13.setValue(voltage_percent)

            # Pressure
            self.progressBar_14.setRange(0,100)
            self.progressBar_14.setValue(pressure_percent)

            # Power
            self.progressBar_12.setRange(0,100)
            self.progressBar_12.setValue(power_percent)
            
            self.update_stl_from_serial(data)

        except Exception as e:
            print("Telemetry parse error:", e)


    def parse(self, line):
        try:
            return dict(item.split(":") for item in line.split(","))
        except:
            return None

    def on_serial_data(self, data):
        try:
            # Split multiple fields
            parts = data.split(",")
            for part in parts:
                if ":" not in part:
                    continue

                key, value = part.split(":", 1)
                key = key.strip()
                value = value.strip()

                if key in self.field_widgets:
                    widgets = self.field_widgets[key]

                    # -----------------
                    # Update Label
                    # -----------------
                    if "label" in widgets:
                        widgets["label"].setText(value)

                    # -----------------
                    # Update ProgressBar
                    # -----------------
                    if "progress" in widgets:
                        try:
                            numeric_value = int(float(value))
                            # Optional: clamp within range
                            progress = widgets["progress"]
                            min_val = progress.minimum()
                            max_val = progress.maximum()
                            numeric_value = max(min_val, min(numeric_value, max_val))
                            progress.setValue(numeric_value)
                        except ValueError:
                            pass  # ignore if not numeric
        except Exception as e:
            print("Serial update error:", e)


    def update_stl_from_serial(self, data):
        try:
            if isinstance(data, dict):
                roll = float(data.get("roll", 0))
                pitch = float(data.get("pitch", 0))
                yaw = float(data.get("yaw", 0))
            else:
                parts = data.strip().split(",")
                if len(parts) < 21:
                    return
                roll = float(parts[17])
                pitch = float(parts[18])
                yaw = float(parts[19])

            self.stl_view.update_orientation({
                "roll": roll,
                "pitch": pitch,
                "yaw": yaw
            })
        except Exception as e:
            print("DB STL error:", e)


'''if __name__ == "__main__":
    
    app = QtWidgets.QApplication(sys.argv)

    serial_manager = SerialManager()
    stl_view = STLView()

    ui = DbWindow(serial_manager, stl_view)

    ui.show()

    sys.exit(app.exec_())'''