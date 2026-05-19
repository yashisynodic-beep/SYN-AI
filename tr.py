
import math
from PyQt5 import QtCore, QtGui, QtWidgets
import sys, os
from serial_manager import SerialManager
from ics_rc import *
from stl_view import STLView
import numpy as np
from stl_view import resource_path




class MotionWidget(QtWidgets.QWidget):
    
    def __init__(self, serial_manager, stl_view):
        super().__init__()
        self.serial_manager = serial_manager 
        self.stl_view = stl_view
        self.serial_manager.data_received.connect(self.on_serial_data)
        #self.serial_manager.start()
        self.trajectory = []
        self.lat0 = None
        self.lon0 = None

       # self.serial_manager.data_received.connect(self.on_serial_data)
        
        # -------- Telemetry Fields (filtered from ESP32) --------
        # Only fields needed for motion display
        self.telemetry_fields = [
            "Flight Uptime",   
            "Altitude",
            "Euler X",          # maps to 'roll'
            "Euler Y",          # maps to 'pitch'
            "Euler Z",          # maps to 'yaw'
            "SystemMode"        # maps to 'phase'
        ]
        
        # -------- Media Player State --------
        self.data_buffer = []       
        self.current_index = 0     
        self.is_playing = True      
        self.last_data_time = QtCore.QTime.currentTime()

 
        self.setupUi(self)
        
        #self.update_timer = QtCore.QTimer(self)
        #self.update_timer.timeout.connect(self.poll_serial)
        #QtCore.QTimer.singleShot(500, lambda: self.update_timer.start(100))

        
    def setupUi(self, mainWidget):
        mainWidget.setObjectName("mainWidget")
        mainWidget.setMinimumSize(0, 0)
        mainWidget.setStyleSheet("""

/* ================= GLOBAL ================= */
QWidget {
    background: transparent;
    color: #ecfdff;
    
    
}

/* ================= MAIN BACKDROP ================= */
QWidget#MainWindow {
    background: qlineargradient(
        x1:0, y1:0, x2:1, y2:1,
        stop:0 #0a4d66,
        stop:0.5 #0f6f8f,
        stop:1 #06384d
    );
}

/* ================= GLASS BASE ================= */
QFrame, QWidget {
    background: rgba(40, 160, 200, 90);
    border-radius: 20px;
    border: 1.2px solid rgba(0, 229, 255, 140);
}

/* ================= RIGHT PANEL ================= */
QFrame#frame_3 {
    background: qlineargradient(
        x1:0, y1:0, x2:0, y2:1,
        stop:0 rgba(120, 220, 255, 160),
        stop:1 rgba(30, 110, 150, 200)
    );
    border-radius: 24px;
    border: 1.6px solid rgba(0, 240, 255, 190);
}

/* ================= STL / MAP VIEW ================= */
QFrame#frame_4 {
    background: qlineargradient(
        x1:0, y1:0, x2:1, y2:1,
        stop:0 rgba(140, 230, 255, 150),
        stop:1 rgba(40, 130, 170, 210)
    );
    border-radius: 20px;
    border: 1.4px solid rgba(0, 229, 255, 170);
}

/* ================= PLAY BUTTON BAR ================= */
QFrame#playBtnFrame {
    background: rgba(120, 220, 255, 140);
    border-radius: 18px;
    border: 1.5px solid rgba(0, 229, 255, 180);
}

/* ================= LEFT DATA PANEL ================= */
QFrame#frame_2 {
    background: rgba(100, 200, 240, 120);
    border-radius: 22px;
    border: 1.5px solid rgba(0, 229, 255, 160);
}

/* ================= GROUP BOX ================= */
QGroupBox {
    background: rgba(120, 220, 255, 120);
    border-radius: 22px;
    border: 1.6px solid rgba(0, 229, 255, 180);
    margin-top: 28px;
    padding: 14px;
}

/* ================= GROUP TITLE ================= */
QGroupBox::title {
    background: qlineargradient(
        x1:0, y1:0, x2:1, y2:0,
        stop:0 #7ff7ff,
        stop:1 #00cfe8
    );
    color: #01313d;
    padding: 6px 18px;
    border-radius: 14px;
    margin-left: 14px;
    font-weight: 600;
}

/* ================= LABEL ================= */
QLabel {
    background: rgba(0, 0, 0, 70);
    border-radius: 10px;
    padding: 6px 12px;
    color: white;
    font-size: 14px;
    font-weight: 500;
}

/* Flight data values (right column) */
QLabel#label_2,
QLabel#label_6,
QLabel#label_8,
QLabel#label_10,
QLabel#label_12,
QLabel#label_13 {
    color: #00E5FF;
    font-size: 15px;
    font-weight: 600;
}

/* Status values */
QLabel#label_20,
QLabel#label_33,
QLabel#label_31,
QLabel#label_30 {
    font-weight: bold;
}

/* ================= GLASS BUTTONS ================= */
QPushButton {
    background: qlineargradient(
        x1:0, y1:0, x2:0, y2:1,
        stop:0 rgba(200, 250, 255, 220),
        stop:1 rgba(80, 190, 220, 220)
    );
    color: #023846;
    border-radius: 12px;
    border: 1.6px solid rgba(0, 229, 255, 200);
    padding: 8px 22px;
    font-weight: 600;
}

/* Hover glow */
QPushButton:hover {
    background: qlineargradient(
        x1:0, y1:0, x2:0, y2:1,
        stop:0 #ffffff,
        stop:1 #9ff6ff
    );
    border: 1.8px solid #e6feff;
}


/* Pressed glass */
QPushButton:pressed {
    background: qlineargradient(
        x1:0, y1:0, x2:0, y2:1,
        stop:0 #5fdbe8,
        stop:1 #2ba7bd
    );
    border: 1.8px solid #00e5ff;
}

/* Disabled */
QPushButton:disabled {
    background: rgba(160, 200, 210, 120);
    color: rgba(0, 60, 80, 120);
    border: 1px solid rgba(0, 229, 255, 80);
}


""")
        self.verticalLayout = QtWidgets.QVBoxLayout(mainWidget)
        self.verticalLayout.setContentsMargins(5, 5, 5, 5)
        self.verticalLayout.setSpacing(6)
        self.verticalLayout.setObjectName("verticalLayout")
        self.frame = QtWidgets.QFrame(mainWidget)
        self.frame.setSizePolicy(
             QtWidgets.QSizePolicy.Expanding,
             QtWidgets.QSizePolicy.Expanding
)
        self.frame.setFrameShape(QtWidgets.QFrame.Box)
        self.frame.setFrameShadow(QtWidgets.QFrame.Sunken)
        self.frame.setObjectName("frame")
        self.horizontalLayout = QtWidgets.QHBoxLayout(self.frame)
        self.horizontalLayout.setStretch(0, 1)   # left panel
        self.horizontalLayout.setStretch(1, 3)   # right panel
        self.horizontalLayout.setObjectName("horizontalLayout")
        self.frame_2 = QtWidgets.QFrame(self.frame)
        self.frame_2.setMinimumWidth(180)
        self.frame_2.setMaximumWidth(300)
        self.frame_2.setSizePolicy(
    QtWidgets.QSizePolicy.Preferred,
    QtWidgets.QSizePolicy.Expanding
)
        self.frame_2.setFrameShape(QtWidgets.QFrame.Box)
        self.frame_2.setFrameShadow(QtWidgets.QFrame.Sunken)
        self.frame_2.setObjectName("frame_2")
        self.verticalLayout_5 = QtWidgets.QVBoxLayout(self.frame_2)
        self.verticalLayout_5.setObjectName("verticalLayout_5")
        self.groupBox_2 = QtWidgets.QGroupBox(self.frame_2)
        self.groupBox_2.setMinimumSize(QtCore.QSize(0, 0))
        font = QtGui.QFont()
        font.setFamily("Monotype Corsiva")
        font.setPointSize(12)
        font.setBold(True)
        font.setItalic(False)
        font.setUnderline(True)
        font.setWeight(75)
        self.groupBox_2.setFont(font)
        self.groupBox_2.setStyleSheet("")
        self.groupBox_2.setObjectName("groupBox_2")
        self.verticalLayout_4 = QtWidgets.QVBoxLayout(self.groupBox_2)
        self.verticalLayout_4.setObjectName("verticalLayout_4")
        self.gridLayout = QtWidgets.QGridLayout()
        self.gridLayout.setContentsMargins(0, -1, -1, -1)
        self.gridLayout.setSpacing(9)
        self.gridLayout.setObjectName("gridLayout")
        self.label_11 = QtWidgets.QLabel(self.groupBox_2)
        self.label_11.setAlignment(QtCore.Qt.AlignCenter)
        self.label_11.setObjectName("label_11")
        self.gridLayout.addWidget(self.label_11, 4, 0, 1, 1)
        self.label = QtWidgets.QLabel(self.groupBox_2)
        self.label.setAlignment(QtCore.Qt.AlignCenter)
        self.label.setObjectName("label")
        self.gridLayout.addWidget(self.label, 0, 0, 1, 1)
        self.label_2 = QtWidgets.QLabel(self.groupBox_2)
        self.label_2.setText("")
        self.label_2.setObjectName("label_2")
        self.gridLayout.addWidget(self.label_2, 0, 1, 1, 1)
        self.label_5 = QtWidgets.QLabel(self.groupBox_2)
        self.label_5.setAlignment(QtCore.Qt.AlignCenter)
        self.label_5.setObjectName("label_5")
        self.gridLayout.addWidget(self.label_5, 1, 0, 1, 1)
        self.label_6 = QtWidgets.QLabel(self.groupBox_2)
        self.label_6.setText("")
        self.label_6.setObjectName("label_6")
        self.gridLayout.addWidget(self.label_6, 1, 1, 1, 1)
        self.label_7 = QtWidgets.QLabel(self.groupBox_2)
        self.label_7.setAlignment(QtCore.Qt.AlignCenter)
        self.label_7.setObjectName("label_7")
        self.gridLayout.addWidget(self.label_7, 2, 0, 1, 1)
        self.label_10 = QtWidgets.QLabel(self.groupBox_2)
        self.label_10.setText("")
        self.label_10.setObjectName("label_10")
        self.gridLayout.addWidget(self.label_10, 3, 1, 1, 1)
        self.label_8 = QtWidgets.QLabel(self.groupBox_2)
        self.label_8.setText("")
        self.label_8.setObjectName("label_8")
        self.gridLayout.addWidget(self.label_8, 2, 1, 1, 1)
        self.label_14 = QtWidgets.QLabel(self.groupBox_2)
        self.label_14.setAlignment(QtCore.Qt.AlignCenter)
        self.label_14.setObjectName("label_14")
        self.gridLayout.addWidget(self.label_14, 5, 0, 1, 1)
        self.label_13 = QtWidgets.QLabel(self.groupBox_2)
        self.label_13.setText("")
        self.label_13.setObjectName("label_13")
        self.gridLayout.addWidget(self.label_13, 5, 1, 1, 1)
        self.label_9 = QtWidgets.QLabel(self.groupBox_2)
        self.label_9.setAlignment(QtCore.Qt.AlignCenter)
        self.label_9.setObjectName("label_9")
        self.gridLayout.addWidget(self.label_9, 3, 0, 1, 1)
        self.label_12 = QtWidgets.QLabel(self.groupBox_2)
        self.label_12.setText("")
        self.label_12.setObjectName("label_12")
        self.gridLayout.addWidget(self.label_12, 4, 1, 1, 1)
        self.verticalLayout_4.addLayout(self.gridLayout)
        self.verticalLayout_5.addWidget(self.groupBox_2)
        self.groupBox_3 = QtWidgets.QGroupBox(self.frame_2)
        font = QtGui.QFont()
        #font.setFamily("Monotype Corsiva")
        font.setPointSize(12)
        font.setBold(True)
        font.setUnderline(True)
        font.setWeight(75)
        self.groupBox_3.setFont(font)
        self.groupBox_3.setObjectName("groupBox_3")
        self.verticalLayout_3 = QtWidgets.QVBoxLayout(self.groupBox_3)
        self.verticalLayout_3.setObjectName("verticalLayout_3")
        self.gridLayout_2 = QtWidgets.QGridLayout()
        self.gridLayout_2.setContentsMargins(0, 10, -1, -1)
        self.gridLayout_2.setSpacing(9)
        self.gridLayout_2.setObjectName("gridLayout_2")
        self.label_20 = QtWidgets.QLabel(self.groupBox_3)
        self.label_20.setAlignment(QtCore.Qt.AlignCenter)
        self.label_20.setObjectName("label_20")
        self.gridLayout_2.addWidget(self.label_20, 0, 1, 1, 1)
        self.label_19 = QtWidgets.QLabel(self.groupBox_3)
        self.label_19.setAlignment(QtCore.Qt.AlignCenter)
        self.label_19.setObjectName("label_19")
        self.gridLayout_2.addWidget(self.label_19, 0, 0, 1, 1)
        self.label_34 = QtWidgets.QLabel(self.groupBox_3)
        self.label_34.setAlignment(QtCore.Qt.AlignCenter)
        self.label_34.setObjectName("label_34")
        self.gridLayout_2.addWidget(self.label_34, 1, 0, 1, 1)
        self.label_33 = QtWidgets.QLabel(self.groupBox_3)
        self.label_33.setAlignment(QtCore.Qt.AlignCenter)
        self.label_33.setObjectName("label_33")
        self.gridLayout_2.addWidget(self.label_33, 1, 1, 1, 1)
        self.label_31 = QtWidgets.QLabel(self.groupBox_3)
        self.label_31.setAlignment(QtCore.Qt.AlignCenter)
        self.label_31.setObjectName("label_31")
        self.gridLayout_2.addWidget(self.label_31, 2, 1, 1, 1)
        self.label_29 = QtWidgets.QLabel(self.groupBox_3)
        self.label_29.setAlignment(QtCore.Qt.AlignCenter)
        self.label_29.setObjectName("label_29")
        self.gridLayout_2.addWidget(self.label_29, 2, 0, 1, 1)
        self.label_30 = QtWidgets.QLabel(self.groupBox_3)
        self.label_30.setAlignment(QtCore.Qt.AlignCenter)
        self.label_30.setObjectName("label_30")
        self.gridLayout_2.addWidget(self.label_30, 3, 1, 1, 1)
        self.label_27 = QtWidgets.QLabel(self.groupBox_3)
        self.label_27.setAlignment(QtCore.Qt.AlignCenter)
        self.label_27.setObjectName("label_27")
        self.gridLayout_2.addWidget(self.label_27, 3, 0, 1, 1)
        self.verticalLayout_3.addLayout(self.gridLayout_2)
        self.verticalLayout_5.addWidget(self.groupBox_3)
        self.horizontalLayout.addWidget(self.frame_2)
        self.frame_3 = QtWidgets.QFrame(self.frame)
        #SizePolicy of frame_3
        self.frame_3.setSizePolicy(
              QtWidgets.QSizePolicy.Expanding,
              QtWidgets.QSizePolicy.Expanding
)
        self.frame_3.setFrameShape(QtWidgets.QFrame.Box)
        self.frame_3.setFrameShadow(QtWidgets.QFrame.Sunken)
        self.frame_3.setObjectName("frame_3")
        self.verticalLayout_2 = QtWidgets.QVBoxLayout(self.frame_3)
        self.verticalLayout_2.setObjectName("verticalLayout_2")
        self.frame_4 = QtWidgets.QFrame(self.frame_3)
        #SizePolicy of frame_4
        self.frame_4.setSizePolicy(
    QtWidgets.QSizePolicy.Expanding,
    QtWidgets.QSizePolicy.Expanding
)

        layout = QtWidgets.QVBoxLayout(self.frame_4)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addWidget(self.stl_view)

        self.frame_4.setFrameShape(QtWidgets.QFrame.Box)
        self.frame_4.setFrameShadow(QtWidgets.QFrame.Sunken)
        self.frame_4.setObjectName("frame_4")
        self.verticalLayout_2.addWidget(self.frame_4)
        self.playBtnFrame = QtWidgets.QFrame(self.frame_3)
        self.playBtnFrame.setFrameShape(QtWidgets.QFrame.Box)
        self.playBtnFrame.setFrameShadow(QtWidgets.QFrame.Raised)
        self.playBtnFrame.setObjectName("playBtnFrame")
        self.playBtnFrame.setSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Fixed)
        self.playBtnFrame.setMaximumHeight(80)
        self.playBtnFrame.setMinimumHeight(50)
        self.horizontalLayout_3 = QtWidgets.QHBoxLayout(self.playBtnFrame)
        self.horizontalLayout_3.setSpacing(12)
        self.horizontalLayout_3.setContentsMargins(12, 8, 12, 8)

        self.horizontalLayout_3.setStretch(0, 0)
        self.horizontalLayout_3.setStretch(1, 0)
        self.horizontalLayout_3.setStretch(2, 0)
        self.horizontalLayout_3.setStretch(3, 0)
        self.horizontalLayout_3.setStretch(4, 1)  # ONLY progress bar expands
        self.horizontalLayout_3.setStretch(5, 0)
        self.horizontalLayout_3.setStretch(6, 0)
        self.horizontalLayout_3.setStretch(7, 0)
        self.horizontalLayout_3.setStretch(0, 0)  # Reset
        self.horizontalLayout_3.setStretch(1, 0)  # Top View
        self.horizontalLayout_3.setStretch(2, 0)  # Side View
        self.horizontalLayout_3.setStretch(3, 0)  # Play button
        self.horizontalLayout_3.setStretch(4, 1)  # Progress bar (only this expands)
        self.horizontalLayout_3.setStretch(5, 0)  # rewind
        self.horizontalLayout_3.setStretch(6, 0)  # forward
        self.horizontalLayout_3.setStretch(7, 0)  # combo
        self.horizontalLayout_3.setObjectName("horizontalLayout_3")
        self.pushButton = QtWidgets.QPushButton(self.playBtnFrame)
        self.pushButton.setEnabled(True)
        sizePolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Minimum, QtWidgets.QSizePolicy.Fixed)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.pushButton.sizePolicy().hasHeightForWidth())
        self.pushButton.setSizePolicy(sizePolicy)
        self.pushButton.setMinimumWidth(100)
        font = QtGui.QFont()
        font.setPointSize(10)
        font.setBold(True)
        font.setWeight(62)
        self.pushButton.setFont(font)
        self.pushButton.setObjectName("pushButton")
        self.horizontalLayout_3.addWidget(self.pushButton)
        self.pushButton_2 = QtWidgets.QPushButton(self.playBtnFrame)
        self.pushButton_2.setEnabled(True)
        sizePolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Minimum, QtWidgets.QSizePolicy.Fixed)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.pushButton_2.sizePolicy().hasHeightForWidth())
        self.pushButton_2.setSizePolicy(sizePolicy)
        self.pushButton_2.setMinimumWidth(100)
        self.pushButton_2.setObjectName("pushButton_2")
        self.horizontalLayout_3.addWidget(self.pushButton_2)
        self.pushButton_3 = QtWidgets.QPushButton(self.playBtnFrame)
        self.pushButton_3.setEnabled(True)
        sizePolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Minimum, QtWidgets.QSizePolicy.Fixed)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.pushButton_3.sizePolicy().hasHeightForWidth())
        self.pushButton_3.setSizePolicy(sizePolicy)
        self.pushButton_3.setMinimumWidth(100)
        self.pushButton_3.setObjectName("pushButton_3")
        self.horizontalLayout_3.addWidget(self.pushButton_3)
        self.horizontalLayout_3.addSpacing(15)   # after view buttons
        self.pushButton_4 = QtWidgets.QPushButton(self.playBtnFrame)
        self.pushButton_4.setEnabled(True)
        #self.pushButton_4.setFixedSize(40, 40)
        self.pushButton_4.setStyleSheet("")
        self.pushButton_4.setText("")
        icon = QtGui.QIcon()
        icon.addPixmap(QtGui.QPixmap(":/icons/pause-play.png"), QtGui.QIcon.Normal, QtGui.QIcon.Off)
        self.pushButton_4.setIcon(icon)
        self.pushButton_4.setIconSize(QtCore.QSize(32, 32))
        self.pushButton_4.setCheckable(True)
        self.pushButton_4.setObjectName("pushButton_4")
        #sizePolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Minimum, QtWidgets.QSizePolicy.Fixed)
        self.horizontalLayout_3.addWidget(self.pushButton_4)
        self.progressBar = QtWidgets.QProgressBar(self.playBtnFrame)
        self.progressBar.setFixedHeight(18)
        self.progressBar.setTextVisible(False)
        self.progressBar.setSizePolicy(
             QtWidgets.QSizePolicy.Expanding,
             QtWidgets.QSizePolicy.Fixed
)
        self.progressBar.setValue(0)
        

        self.progressBar.setObjectName("progressBar")
        self.progressBar.setStyleSheet("""
QProgressBar {
    background: rgba(0, 0, 0, 80);
    border-radius: 9px;
    border: 1px solid rgba(0,255,255,120);
}
QProgressBar::chunk {
    border-radius: 9px;
    background: qlineargradient(
        x1:0, y1:0, x2:1, y2:0,
        stop:0 #00e5ff,
        stop:1 #00ffaa
    );
    
  
QPushButton #pushButton_4 {
    background: qlineargradient(
        x1:0, y1:0, x2:0, y2:1,
        stop:0 #00e5ff,
        stop:1 #00bcd4
    );
    border-radius: 24px;
    border: 2px solid #e6feff;
}
QPushButton:hover {
    background: #00ffff;
}
QPushButton:pressed {
    background: #0097a7;
}

}
""")
        self.horizontalLayout_3.addWidget(self.progressBar)
        self.pushButton_5 = QtWidgets.QPushButton(self.playBtnFrame)
        self.pushButton_5.setEnabled(True)
        #self.pushButton_5.setFixedSize(40, 40)
        self.pushButton_5.setStyleSheet("")
        self.pushButton_5.setText("")
        icon1 = QtGui.QIcon()
        icon1.addPixmap(QtGui.QPixmap(":/icons/rewind.png"), QtGui.QIcon.Normal, QtGui.QIcon.Off)
        self.pushButton_5.setIcon(icon1)
        self.pushButton_5.setIconSize(QtCore.QSize(32, 32))
        self.pushButton_5.setCheckable(True)
        self.pushButton_5.setObjectName("pushButton_5")
        self.horizontalLayout_3.addWidget(self.pushButton_5)
        self.pushButton_6 = QtWidgets.QPushButton(self.playBtnFrame)
        self.pushButton_6.setEnabled(True)
        #self.pushButton_6.setFixedSize(40, 40)
        self.pushButton_6.setText("")
        icon2 = QtGui.QIcon()
        icon2.addPixmap(QtGui.QPixmap(":/icons/fast-forward.png"), QtGui.QIcon.Normal, QtGui.QIcon.Off)
        self.pushButton_6.setIcon(icon2)
        self.pushButton_6.setIconSize(QtCore.QSize(32, 32))
        self.pushButton_6.setCheckable(True)
        self.pushButton_6.setObjectName("pushButton_6")
        for btn in [self.pushButton_4, self.pushButton_5, self.pushButton_6]:
            btn.setSizePolicy(QtWidgets.QSizePolicy.Fixed, QtWidgets.QSizePolicy.Fixed)
            btn.setMinimumSize(40, 40)
            
        self.horizontalLayout_3.addWidget(self.pushButton_6)
        self.horizontalLayout_3.addSpacing(15)
        self.comboBox = QtWidgets.QComboBox(self.playBtnFrame)
        self.comboBox.setMinimumWidth(90)
        self.comboBox.setSizePolicy(
    QtWidgets.QSizePolicy.Preferred,
    QtWidgets.QSizePolicy.Fixed
)
        self.comboBox.setObjectName("comboBox")
        self.horizontalLayout_3.addWidget(self.comboBox)
        self.comboBox.setMaximumWidth(120)
        # Normalize button sizes
        for btn in [self.pushButton, self.pushButton_2, self.pushButton_3]:
                btn.setFixedHeight(32)
                btn.setMinimumWidth(90)
                btn.setMaximumWidth(120)

        #for btn in [self.pushButton_4, self.pushButton_5, self.pushButton_6]:
            #btn.setFixedSize(40, 40)
        self.verticalLayout_2.addWidget(self.playBtnFrame)
        self.horizontalLayout.addWidget(self.frame_3)
        self.verticalLayout.addWidget(self.frame)

        self.retranslateUi(mainWidget)
        
# ----------------- STL View Button Connections -----------------
        self.pushButton.clicked.connect(self.stl_view.reset_view)       # Reset view
        self.pushButton_2.clicked.connect(self.stl_view.set_top_view)    # Top view
        self.pushButton_3.clicked.connect(self.stl_view.set_side_view)   # Side view
        self.pushButton_4.toggled.connect(self.toggle_playback)          # Pause/Play toggle button
        self.pushButton_5.clicked.connect(self.previous_frame)  # Previous/Next frame buttons
        self.pushButton_6.clicked.connect(self.next_frame)
        QtCore.QMetaObject.connectSlotsByName(mainWidget)

    def retranslateUi(self, mainWidget):
        _translate = QtCore.QCoreApplication.translate
        mainWidget.setWindowTitle(_translate("motionWidget", "Form"))
        self.groupBox_2.setTitle(_translate("motionWidget", "Flight Data"))
        self.label_11.setText(_translate("motionWidget", "Time"))
        self.label.setText(_translate("motionWidget", "Yaw"))
        self.label_5.setText(_translate("motionWidget", "Pitch"))
        self.label_7.setText(_translate("motionWidget", "Roll"))
        self.label_14.setText(_translate("motionWidget", "Flight Phase"))
        self.label_9.setText(_translate("motionWidget", "Altitude"))
        self.groupBox_3.setTitle(_translate("motionWidget", "Status"))
        self.label_20.setText(_translate("motionWidget", "GREEN"))
        self.label_19.setText(_translate("motionWidget", "Telemetry"))
        self.label_34.setText(_translate("motionWidget", "GPS"))
        self.label_33.setText(_translate("motionWidget", "GREEN"))
        self.label_31.setText(_translate("motionWidget", "GREEN"))
        self.label_29.setText(_translate("motionWidget", "IMU"))
        self.label_30.setText(_translate("motionWidget", "GREEN"))
        self.label_27.setText(_translate("motionWidget", "Link"))
        self.pushButton.setText(_translate("motionWidget", "Reset view"))
        self.pushButton_2.setText(_translate("motionWidget", "Top View"))
        self.pushButton_3.setText(_translate("motionWidget", "Side View"))
        import ics_rc


    def update_flight_data(self, data):
        try:
            self.label_2.setText(f"{data.get('yaw', 0):.2f}")
            self.label_6.setText(f"{data.get('pitch', 0):.2f}")
            self.label_8.setText(f"{data.get('roll', 0):.2f}")
            self.label_10.setText(f"{data.get('altitude', 0):.2f}")
            self.label_12.setText(str(data.get('time', '0')))
            self.label_13.setText(str(data.get('phase', 'IDLE')))  # FIXED

        except Exception as e:
            print("Flight data UI update error:", e)
       
       
    def update_status_ui(self, status):

        def set_status(label, ok):
            if ok:
                label.setText("GREEN")
                label.setStyleSheet("color: #00ff00;")
            else:
                label.setText("RED")
                label.setStyleSheet("color: #ff0000;")

        try:
        
           set_status(self.label_20, status.get('telemetry', False))
           set_status(self.label_33, status.get('gps', False))
           set_status(self.label_31, status.get('imu', False))
           set_status(self.label_30, status.get('link', False))

        except Exception as e:
            print("Status UI update error:", e)


    def on_serial_data(self, data):
        try:
            if isinstance(data, str):
               data = self.parse_serial_data(data)

            if not isinstance(data, dict):
               return

            self.data_buffer.append(data)
            self.last_data_time = QtCore.QTime.currentTime()
            # -------- Trajectory System --------
           

            status_data = {
            "telemetry": True,
            "gps": bool(data.get("gpsLat")),
            "imu": True,
            "link": True
        }

            self.update_status_ui(status_data)

           
            self.current_index = len(self.data_buffer) - 1

            # -------- ADD THIS BLOCK --------


            lat = data.get("gpsLat")
            lon = data.get("gpsLon")
            alt = data.get("altitude", 0)

            if lat is not None and lon is not None:

                if self.lat0 is None:
                    self.lat0 = lat
                    self.lon0 = lon

                x = (lon - self.lon0) * 111320 * math.cos(math.radians(self.lat0))
                y = (lat - self.lat0) * 110540
                z = alt

                self.trajectory.append((x, y, z))

                try:
                    self.stl_view.update_position((x, y, z))
                except Exception as e:
                    print("STL position error:", e)

            # Only auto-render if playing
            if self.is_playing:
                self.render_frame(self.current_index)

        except Exception as e:
            print("❌ Serial handling error:", e)


    def poll_serial(self):
        # No longer needed; data comes via data_received signal
        pass

    def parse_serial_data(self, line):
        try:
            parts = line.strip().split(",")
            if len(parts) < 21:
               return None

            return {
            
            "time": parts[0],
            "altitude": float(parts[2]),
            "roll":  float(parts[17]),
            "pitch": float(parts[18]),
            "yaw":   float(parts[19]),
            "phase": parts[20],
            "gpsLat": float(parts[6]),
            "gpsLon": float(parts[7]),
                        
        }

        except Exception as e:
             print("❌ Serial parsing error:", e)
             return None
        
    def render_frame(self, index):
        if 0 <= index < len(self.data_buffer):
            data = self.data_buffer[index]
            self.update_flight_data(data)

            try:
                self.stl_view.update_orientation({
                    "roll": float(data.get("roll", 0)),
                    "pitch": float(data.get("pitch", 0)),
                    "yaw": float(data.get("yaw", 0)),
                })
            except Exception as e:
                print("❌ STL error:", e)
            # -------- ADD POSITION FOR REPLAY --------
            if self.lat0 is not None:
                import math

                x = (data.get("gpsLon", 0) - self.lon0) * 111320 * math.cos(math.radians(self.lat0))
                y = (data.get("gpsLat", 0) - self.lat0) * 110540
                z = data.get("altitude", 0)

                try:
                    self.stl_view.update_position((x, y, z))
                except Exception as e:
                    print("Replay STL error:", e)
            
            self.progressBar.setMaximum(len(self.data_buffer))
            self.progressBar.setValue(index + 1)
    def toggle_playback(self, checked):
        # checked = True → paused
        self.is_playing = not checked

        if self.is_playing:
            # Resume → show latest frame
            if self.data_buffer:
                self.current_index = len(self.data_buffer) - 1
                #self.render_frame(self.current_index)
               
         
    def previous_frame(self):
        if self.current_index > 0:
            self.current_index -= 1
            self.render_frame(self.current_index)
           
    def next_frame(self):
        if self.current_index < len(self.data_buffer) - 1:
            self.current_index += 1
            self.render_frame(self.current_index)


'''if __name__ == "__main__":
    import sys

    app = QtWidgets.QApplication(sys.argv)

    # create serial manager
    serial_manager = SerialManager()

    # create main widget
    mainWidget = MotionWidget(serial_manager)
    mainWidget.show()

    sys.exit(app.exec_())'''
