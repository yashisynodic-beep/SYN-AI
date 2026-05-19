
import os
from PyQt5 import QtCore, QtGui, QtWidgets
from PyQt5 import QtCore
from PyQt5 import QtCore, QtGui, QtWidgets
from PyQt5.QtWidgets import QMessageBox, QFileDialog
from PyQt5.QtGui import QPixmap
from PyQt5.QtGui import QMovie
from PyQt5.QtWidgets import QSplitter
import sqlite3
from PyQt5.QtWidgets import QApplication, QToolTip
from PyQt5.QtGui import QColor
from PyQt5.QtWidgets import QGraphicsDropShadowEffect
from PyQt5.QtCore import QPropertyAnimation, QEasingCurve, QSequentialAnimationGroup
from datetime import datetime
from PyQt5.QtCore import QSize


# integrated pages
from db import DbWindow as DashboardPage
from gp import GraphsWindow as GraphPage
from map import MapWindow as MapPage
from cs import ConsoleWindow as ConsolePage
from tr import MotionWidget as MotionPage
from serial_manager import SerialManager
from stl_view import STLView
from db_manager import NotificationWindow

from ics_rc import *#import ics_rc
import sys

import os
import csv
from pathlib import Path
from datetime import datetime
import serial.tools.list_ports

def resource_path(relative_path):
    if hasattr(sys, '_MEIPASS'):
        base_path = sys._MEIPASS
    else:
        base_path = os.path.dirname(os.path.abspath(__file__))
    return os.path.join(base_path, relative_path)

class SidePanel(QtWidgets.QFrame):
    def __init__(self, parent=None):
        super().__init__(parent)

        self.setAttribute(QtCore.Qt.WA_TranslucentBackground)
        self.setAutoFillBackground(False)
        self.setStyleSheet("background: transparent;")

    # =============================
    # Updated Mask With More Cuts
    # =============================
    def resizeEvent(self, event):
        self.updateMask()
        super().resizeEvent(event)

    def updateMask(self):
        w = self.width()
        h = self.height()

        cut_big = 40
        cut_small = 20
        notch = 14

        path = QtGui.QPainterPath()

        path.moveTo(0, 0)

        # top edge with extra notch
        path.lineTo(w - cut_big, 0)
        path.lineTo(w - cut_small, notch)
        path.lineTo(w, cut_big)

        # right side with mechanical notch
        path.lineTo(w, h - cut_big)
        path.lineTo(w - cut_small, h - notch)
        path.lineTo(w - cut_big, h)

        # bottom edge
        path.lineTo(notch, h)
        path.lineTo(0, h - notch)

        # left straight edge
        path.lineTo(0, 0)
        

        path.closeSubpath()

        polygon = path.toFillPolygon()
        region = QtGui.QRegion(polygon.toPolygon())
        self.setMask(region.translated(1, 1))
        


    # =============================
    # Paint Event
    # =============================
    def paintEvent(self, event):
        painter = QtGui.QPainter(self)
        painter.setRenderHint(QtGui.QPainter.Antialiasing)

        w = self.width()
        h = self.height()

        cut_big = 40
        cut_small = 20
        notch = 14

        # ----- Complex Multi-Cut Shape -----
        path = QtGui.QPainterPath()
        path.moveTo(1, 1)
        path.lineTo(w - cut_big - 1, 1)
        path.lineTo(w - cut_small, notch)
        path.lineTo(w - 1, cut_big)

        path.lineTo(w - 1, h - cut_big)
        path.lineTo(w - cut_small, h - notch)
        path.lineTo(w - cut_big - 1, h - 1)

        path.lineTo(notch, h - 1)
        path.lineTo(0, h - notch)
        path.lineTo(0, 0)
        path.closeSubpath()

        # ----- Dark Deep Sci-Fi Gradient -----
        gradient = QtGui.QLinearGradient(0, 0, 0, h)
        gradient.setColorAt(0, QtGui.QColor(10, 25, 60, 230))
        gradient.setColorAt(1, QtGui.QColor(2, 8, 20, 230))
        painter.setPen(QtCore.Qt.NoPen)
        painter.fillPath(path, gradient)

        # ----- Outer Glow -----
        painter.setPen(QtGui.QPen(QtGui.QColor(0, 200, 255, 60), 3))
        painter.drawPath(path)

        # ----- Main Sharp Border -----
        painter.setPen(QtGui.QPen(QtGui.QColor(0, 220, 255), 1.8))
        painter.drawPath(path)

        # ----- Inner Mechanical Line -----
        inner = path.translated(2, 2)
        painter.setPen(QtGui.QPen(QtGui.QColor(120, 200, 255, 100), 1))
        painter.drawPath(inner)

        # ----- Extra Tech Accent Lines -----
        painter.setPen(QtGui.QPen(QtGui.QColor(0, 255, 255, 180), 2))
        painter.drawLine(30, 18, w - 90, 18)  # top accent
        painter.drawLine(30, h - 18, w - 90, h - 18)  # bottom accent

        # small corner detail
        painter.setPen(QtGui.QPen(QtGui.QColor(0, 255, 255, 150), 2))
        painter.drawLine(w - cut_big + 8, 8, w - 8, cut_big - 8)
        painter.drawLine(w - cut_big + 8, h - 8, w - 8, h - cut_big + 8)

        self.setContentsMargins(12, 12, 12, 12)
        
class BodyFrame(QtWidgets.QFrame):
    def __init__(self, parent=None):
        super().__init__(parent)

        self.setAttribute(QtCore.Qt.WA_TranslucentBackground)
        self.setAutoFillBackground(False)
        self.setStyleSheet("background: transparent;")

    def resizeEvent(self, event):
        path = QtGui.QPainterPath()
        path.addRoundedRect(QtCore.QRectF(self.rect()), 18, 18)
        
        super().resizeEvent(event)

    def paintEvent(self, event):
        painter = QtGui.QPainter(self)
        painter.setRenderHint(QtGui.QPainter.Antialiasing)

        w = self.width()
        h = self.height()
        radius = 14  # smaller radius like image

        path = QtGui.QPainterPath()
        path.addRoundedRect(1, 1, w-2, h-2, radius, radius)

    # Dark glass look
        gradient = QtGui.QLinearGradient(0, 0, 0, h)
        gradient.setColorAt(0, QtGui.QColor(15, 35, 80, 220))
        gradient.setColorAt(1, QtGui.QColor(5, 15, 35, 220))

        painter.fillPath(path, gradient)

    # Subtle outer edge
        painter.setPen(QtGui.QPen(QtGui.QColor(0, 200, 255, 40), 2))
        painter.drawPath(path)

    # Sharp main border
        painter.setPen(QtGui.QPen(QtGui.QColor(0, 220, 255), 1.5))
        painter.drawPath(path)

    # Inner highlight
        inner = QtGui.QPainterPath()
        inner.addRoundedRect(2, 2, w-4, h-4, radius-2, radius-2)

        painter.setPen(QtGui.QPen(QtGui.QColor(170, 200, 255, 100), 1))
        painter.drawPath(inner)
        
        self.setContentsMargins(10, 10, 10, 10)             


class ModeRatio:
    WIDTH = 1
    HEIGHT = 2
    BOTH = WIDTH | HEIGHT
    
class SizeManager(QtCore.QObject):
    def __init__(self, widget, mode):
        super().__init__(widget)
        self.widget = widget
        self.mode = mode

        self.window = self.widget.window()

        # Store initial ratios ONCE
        self.width_ratio = self.widget.width() / self.window.width()
        self.height_ratio = self.widget.height() / self.window.height()

        self.window.installEventFilter(self)

    def eventFilter(self, obj, event):
        if obj is self.window and event.type() == QtCore.QEvent.Resize:
            self.apply_resize()
        return super().eventFilter(obj, event)

    def apply_resize(self):
        new_width = self.widget.width()
        new_height = self.widget.height()

        if self.mode & ModeRatio.WIDTH:
            new_width = self.window.width() * self.width_ratio

        if self.mode & ModeRatio.HEIGHT:
            new_height = self.window.height() * self.height_ratio

        self.widget.resize(int(new_width), int(new_height))

class AutoFontScaler(QtCore.QObject):
    def __init__(self, window):
        super().__init__(window)

        self.window = window
        self.base_width = window.width()

        self.widgets = []
        self.base_fonts = {}

        self.collect_widgets(window)

        self.window.installEventFilter(self)

    def collect_widgets(self, parent):
        for child in parent.findChildren(QtWidgets.QWidget):

            # skip widgets without text relevance
            if not hasattr(child, "font"):
                continue

            font = child.font()
            size = font.pointSize()

            # skip invalid font sizes
            if size <= 0:
                continue

            self.widgets.append(child)
            self.base_fonts[child] = size

    def eventFilter(self, obj, event):
        if obj is self.window and event.type() == QtCore.QEvent.Resize:
            self.apply_scaling()
        return super().eventFilter(obj, event)

    def apply_scaling(self):
        scale = self.window.width() / self.base_width

        for w in self.widgets:
            base_size = self.base_fonts.get(w, 10)

            new_size = max(8, min(int(base_size * scale), 28))

            font = w.font()

            if font.pointSize() != -1:
                font.setPointSize(new_size)
            else:
                font.setPixelSize(new_size)

            w.setFont(font)
            
class Ui_MainWindow(object):
    
    
    def apply_glow(self, widget):

        glow = QGraphicsDropShadowEffect(widget)  # attach to widget
        glow.setOffset(0, 0)

        # --- Sci-fi purple glow ---
        glow.setBlurRadius(50)  
        glow.setColor(QColor(170, 0, 255, 200))  

        widget.setGraphicsEffect(glow)

        # store reference (IMPORTANT)
        widget._glow = glow
        
        
    def load_stl_file(self):

        file_path, _ = QFileDialog.getOpenFileName(
            None,
            "Select STL File",
            "",
            "STL Files (*.stl *.STL)"
        )

        if not file_path:
            return

        try:
            self.stlView_dashboard.load_new_stl(file_path)
            self.stlView_motion.load_new_stl(file_path)

            QMessageBox.information(
                None,
                "Success",
                "STL Loaded Successfully"
            )

        except Exception as e:
            QMessageBox.critical(
                None,
                "Error",
                str(e)
            )
            
    def setupUi(self, MainWindow):
        MainWindow.setObjectName("SYNODIC GCS")
        self.window_width, self.window_height = 1200, 800
        MainWindow.setMinimumSize(self.window_width, self.window_height)
        screen = QtWidgets.QApplication.primaryScreen()
        size = screen.availableGeometry()

        MainWindow.resize(int(size.width() * 0.85), int(size.height() * 0.85))
        self.centralwidget = QtWidgets.QWidget(MainWindow)
        # Initialize serial manager for communication
        self.serial_manager = SerialManager()
        self.notify_window = None

        
        self.serial_manager.data_received.connect(self.route_serial_data)
        self.serial_manager.status_text.connect(self.show_notification)
        #self.serial_manager.start()

        # -------- USER DATA LOGGING --------
        self.current_user = None
        self.log_file = None
        self.log_writer = None
        self.logging_enabled = False
        self.mission_start = None
        self.mission_user = None
        self.current_mission_id = None

        self.centralwidget.setStyleSheet("""
        /* ================= BACKGROUND ================= */
        QWidget#centralwidget {
            border-image: url(:/icons/bg_3.jpeg) 0 0 0 0 stretch stretch;
            background-position: center;
            background-repeat: no-repeat;
        }

        /* ================= BUTTONS ================= */
        QPushButton {
            background: rgba(0,0,0,0.4);
            border: 1px solid rgba(255,255,255,0.15);
            border-radius: 32px;
            color: #C77DFF;
        }

        QPushButton:hover {
            background-color: rgba(170, 0, 255, 0.15);
            border: 1px solid rgba(200, 120, 255, 0.9);
        }

        QPushButton:pressed {
            background-color: rgba(140,77,255,0.25);
        }

        /* Small round buttons */
        QPushButton#notifyBtn,
        QPushButton#lightBtn,
        QPushButton#darkBtn {
            border-radius: 17px;
        }

        QPushButton#notifyBtn:hover,
        QPushButton#lightBtn:hover,
        QPushButton#darkBtn:hover {
            background-color: rgba(255,255,255,0.10);
            border: 1px solid #00F5FF;
        }

        /* ================= MAIN PANEL ================= */
        QFrame#frame_2 {
            background: qradialgradient(
                cx: 0.5, cy: 0.5, radius: 2.0,
                stop:0 #000000,
                stop:0.3 #140022,
                stop:0.5 #2F004A,
                stop:0.7 #000000,
                stop:1 #000000
            );
            border-radius: 15px;
            border: 1px solid rgba(170, 0, 255, 0.6);        }

        /* ================= SENSOR PANELS ================= */
        QFrame#frame_4,
        QFrame#frame_12 {
            background: qradialgradient(
                cx:0.4, cy:0.4, radius:1.5,
                stop:0 #0C0C0F,
                stop:0.3 #1B0035,
                stop:0.5 #26004A,
                stop:1 #0B0B0E
            );
            border-radius: 15px;
            border: 1px solid rgba(0,255,255,0.25);
        }

        /* Transparent Frames */
        QFrame#frame_13,
        QFrame#frame_14,
        QFrame#frame_15,
        QFrame#frame_16,
        QFrame#frame_17 {
            background: transparent;
            border: none;
        }

        /* ================= RIGHT PANEL CARDS ================= */
        QFrame#frame_18,
        QFrame#frame_19,
        QFrame#frame_20,
        QFrame#frame_21,
        QFrame#frame_22 {
            background-color: #050A14;
            border-radius: 10px;
            border: 1px solid rgba(0,255,255,0.2);
        }

        /* ================= GLOBAL NEON BORDER ================= */
        QFrame {
            border: 1px solid rgba(0,255,255,0.15);
            border-radius: 12px;
        }

        
        QToolTip {
            background-color: rgba(20, 40, 120, 230);
            color: #7DF9FF;
            font-weight: 600;
            border: 1px solid rgba(0, 255, 255, 180);
            border-radius: 3px;
            padding: 8px;

            background-image: qlineargradient(
                x1:0, y1:0, x2:1, y2:1,
                stop:0 rgba(0, 255, 255, 180),
                stop:0.5 rgba(0, 120, 200, 180),
                stop:1 rgba(0, 20, 35, 230)
            );
}
        /* ================= LABELS ================= */
        QLabel {
            color: #9FEFFF;
            background: rgba(0, 230, 255, 0.05);
            border-radius: 6px;
            padding: 5px;
            border: 1px solid rgba(0,200,255,0.2);
        }

        /* ================= PROGRESS BAR ================= */
        QProgressBar {
            background: rgba(10, 30, 50, 0.8);
            border-radius: 8px;
            border: 1px solid rgba(0,255,255,0.3);
            text-align: center;
        }

        QProgressBar::chunk {
        border-radius: 8px;
        background: qlineargradient(
        x1:0, y1:0, x2:1, y2:0,
        stop:0 #00F0FF,
        stop:0.3 #00FFFF,
        stop:0.6 #00BFFF,
        stop:1 #7DF9FF
    );
    
    
}
     """)
        self.centralwidget.setObjectName("centralwidget")
        self.horizontalLayout_5 = QtWidgets.QHBoxLayout(self.centralwidget)
        self.horizontalLayout_5.setContentsMargins(0, 0, 0, 0)
        self.horizontalLayout_5.setSpacing(0)
        self.horizontalLayout_5.setObjectName("horizontalLayout_5")
        self.frame = QtWidgets.QFrame(self.centralwidget)
        self.frame.setStyleSheet("QFrame#frame{\n"
"background-color: transparent;\n"
"border: none;\n"
"}")
        self.frame.setFrameShape(QtWidgets.QFrame.StyledPanel)
        self.frame.setFrameShadow(QtWidgets.QFrame.Raised)
        self.frame.setObjectName("frame")
        self.horizontalLayout_2 = QtWidgets.QHBoxLayout(self.frame)
        self.horizontalLayout_2.setContentsMargins(0,0,0,0)
        self.horizontalLayout_2.setSpacing(0)
        self.horizontalLayout_2.setObjectName("horizontalLayout_2")
        self.sideFrame = SidePanel(self.frame)

        sizePolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Preferred, QtWidgets.QSizePolicy.Expanding)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.sideFrame.sizePolicy().hasHeightForWidth())
        self.sideFrame.setSizePolicy(sizePolicy)
    
        self.sideFrame.setMaximumWidth(180) 
        #self.sideFrame.setMaximumWidth(200)
        #self.sideFrame.setFrameShape(QtWidgets.QFrame.Box)
        self.sideFrame.setFrameShadow(QtWidgets.QFrame.Raised)
        self.sideFrame.setObjectName("sideFrame")
        self.verticalLayout_2 = QtWidgets.QVBoxLayout(self.sideFrame)
        self.verticalLayout_2.setContentsMargins(13,23,8,9)
        self.verticalLayout_2.setSpacing(0)
        #self.verticalLayout_2.setContentsMargins(15, 9, 15, 0)
        #self.verticalLayout_2.setSpacing(0)
        self.verticalLayout_2.setObjectName("verticalLayout_2")
        
        self.logoFrame = QtWidgets.QFrame(self.sideFrame)
        self.logoFrame.setSizePolicy(
            QtWidgets.QSizePolicy.Fixed,
            QtWidgets.QSizePolicy.Fixed
        )
        self.logoFrame.setMinimumHeight(90)       
        self.logoFrame.setStyleSheet("QFrame{\n"
"background-color: transparent;\n"
"border: none;\n"
"}")
        self.logoFrame.setFrameShape(QtWidgets.QFrame.StyledPanel)
        self.logoFrame.setFrameShadow(QtWidgets.QFrame.Raised)
        self.logoFrame.setObjectName("logoFrame")
        self.horizontalLayout_9 = QtWidgets.QHBoxLayout(self.logoFrame)
        self.horizontalLayout_9.setContentsMargins(0, 0, 0, 0)
        self.horizontalLayout_9.setSpacing(0)
        self.horizontalLayout_9.setObjectName("horizontalLayout_9")
        self.label_2 = QtWidgets.QLabel(self.logoFrame)
        self.label_2.setSizePolicy(
            QtWidgets.QSizePolicy.Fixed,
            QtWidgets.QSizePolicy.Fixed
        )
        self.label_2.setFixedSize(120, 70)
        font = QtGui.QFont()
        #font.setPointSize(14)
        font.setPointSize(max(8, 14))
        self.label_2.setFont(font)
        self.label_2.setAutoFillBackground(False)
        self.label_2.setText("")
        self.label_2.setPixmap(QtGui.QPixmap(":/icons/WhatsApp_Image_2025-11-28_at_14.29.41_8941b3a5-removebg-preview.png"))
        self.label_2.setScaledContents(True)
        self.label_2.setObjectName("label_2")
        self.horizontalLayout_9.addWidget(self.label_2)
        self.verticalLayout_2.addWidget(self.logoFrame, 0, QtCore.Qt.AlignTop)
        self.frame_11 = QtWidgets.QFrame(self.sideFrame)
        self.frame_11.setMinimumHeight(350)
        self.frame_11.setSizePolicy(
            QtWidgets.QSizePolicy.Expanding,
            QtWidgets.QSizePolicy.Preferred
        )
        self.frame_11.setStyleSheet("QFrame{\n"
"background-color: transparent;\n"
"border: none;\n"
"}")
        self.frame_11.setFrameShape(QtWidgets.QFrame.StyledPanel)
        self.frame_11.setFrameShadow(QtWidgets.QFrame.Raised)
        self.frame_11.setObjectName("frame_11")
        self.verticalLayout_4 = QtWidgets.QVBoxLayout(self.frame_11)
        self.verticalLayout_4.setContentsMargins(5, 5, 5, 5)
        self.verticalLayout_4.setSpacing(10)
        self.verticalLayout_4.setObjectName("verticalLayout_4")
        self.frame_13 = QtWidgets.QFrame(self.frame_11)
        self.frame_13.setFrameShape(QtWidgets.QFrame.Box)
        self.frame_13.setFrameShadow(QtWidgets.QFrame.Raised)
        self.frame_13.setMinimumSize(80, 80)

        self.frame_13.setObjectName("frame_13")
        self.horizontalLayout_10 = QtWidgets.QHBoxLayout(self.frame_13)
        self.horizontalLayout_10.setContentsMargins(2, 2, 2, 9)
        self.horizontalLayout_10.setObjectName("horizontalLayout_10")
        self.dbBtn = QtWidgets.QPushButton(self.frame_13)
        #self.dbBtn.setMinimumSize(QtCore.QSize(50, 50))
        self.dbBtn.setMaximumSize(QtCore.QSize(70, 70))
        font = QtGui.QFont()
        font.setFamily("Segoe Print")
        #font.setPointSize(15)
        font.setPointSize(max(8, 14))
        font.setBold(True)
        font.setWeight(75)
        self.dbBtn.setFont(font)
        self.dbBtn.setToolTipDuration(0)
        self.dbBtn.setText("")
        icon = QtGui.QIcon()
        icon.addPixmap(QtGui.QPixmap(":/icons/db-removebg-preview.png"), QtGui.QIcon.Normal, QtGui.QIcon.Off)
        #icon.addPixmap(QtGui.QPixmap(":/icons2/icons/db.jpeg"), QtGui.QIcon.Normal, QtGui.QIcon.Off)
        #self.dbBtn.setIcon(QtGui.QIcon(":/icons/icons/db.jpeg"))
        self.dbBtn.setIcon(icon)
        self.dbBtn.setIconSize(QtCore.QSize(65, 65))

        #self.dbBtn.setIcon(icon)
        #self.dbBtn.setIconSize(QtCore.QSize(40, 40))
        self.dbBtn.setCheckable(True)
        self.dbBtn.setAutoExclusive(True)
        self.dbBtn.setObjectName("dbBtn")
        self.horizontalLayout_10.addWidget(self.dbBtn, 0, QtCore.Qt.AlignHCenter|QtCore.Qt.AlignVCenter)
        self.verticalLayout_4.addWidget(self.frame_13, 0, QtCore.Qt.AlignHCenter)
        self.frame_16 = QtWidgets.QFrame(self.frame_11)
        self.frame_16.setFrameShape(QtWidgets.QFrame.Box)
        self.frame_16.setFrameShadow(QtWidgets.QFrame.Raised)
        self.frame_16.setObjectName("frame_16")
        self.horizontalLayout_14 = QtWidgets.QHBoxLayout(self.frame_16)
        self.horizontalLayout_14.setContentsMargins(2, 2, 2, 2)
        self.horizontalLayout_14.setObjectName("horizontalLayout_14")
        self.csBtn = QtWidgets.QPushButton(self.frame_16)
        #self.csBtn.setMinimumSize(QtCore.QSize(50, 50))
        self.csBtn.setMaximumSize(QtCore.QSize(70, 70))
        font = QtGui.QFont()
        font.setFamily("Segoe Print")
        #font.setPointSize(14)
        font.setPointSize(max(8, 14))
        font.setBold(True)
        font.setWeight(75)
        self.csBtn.setFont(font)
        self.csBtn.setToolTipDuration(0)
        self.csBtn.setText("")
        icon1 = QtGui.QIcon()
        self.csBtn.setIcon(QtGui.QIcon(":/icons/3-removebg-preview.png"))
        self.csBtn.setIconSize(QtCore.QSize(65, 65))
        '''icon1.addPixmap(QtGui.QPixmap(":/icons2/icons/ae611c1f902e7b91204fde7c659d4a36_X-Design.png"), QtGui.QIcon.Normal, QtGui.QIcon.Off)
        self.csBtn.setIcon(icon1)
        self.csBtn.setIconSize(QtCore.QSize(40, 40))'''
        self.csBtn.setCheckable(True)
        self.csBtn.setAutoExclusive(True)
        self.csBtn.setObjectName("csBtn")
        self.horizontalLayout_14.addWidget(self.csBtn)
        self.verticalLayout_4.addWidget(self.frame_16)
        self.frame_14 = QtWidgets.QFrame(self.frame_11)
        self.frame_14.setMinimumSize(QtCore.QSize(70, 70))
        self.frame_14.setFrameShape(QtWidgets.QFrame.Box)
        self.frame_14.setFrameShadow(QtWidgets.QFrame.Raised)
        self.frame_14.setObjectName("frame_14")
        self.horizontalLayout_11 = QtWidgets.QHBoxLayout(self.frame_14)
        self.horizontalLayout_11.setContentsMargins(2, 2, 2, 2)
        self.horizontalLayout_11.setSpacing(6)
        self.horizontalLayout_11.setObjectName("horizontalLayout_11")
        self.gpBtn = QtWidgets.QPushButton(self.frame_14)
        #self.gpBtn.setMinimumSize(QtCore.QSize(50, 50))
        self.gpBtn.setMaximumSize(QtCore.QSize(70, 70))
        font = QtGui.QFont()
        font.setFamily("Segoe Print")
        font.setPointSize(max(8, 14))
        font.setBold(True)
        font.setWeight(75)
        self.gpBtn.setFont(font)
        self.gpBtn.setToolTipDuration(0)
        self.gpBtn.setText("")
        icon2 = QtGui.QIcon()
        self.gpBtn.setIcon(QtGui.QIcon(":/icons/7-removebg-preview.png"))
        self.gpBtn.setIconSize(QtCore.QSize(65, 65))
        '''icon2.addPixmap(QtGui.QPixmap(":/icons2/icons/f3c1651032969d16b8416aa423dae5ec_X-Design.png"), QtGui.QIcon.Normal, QtGui.QIcon.Off)
        self.gpBtn.setIcon(icon2)
        self.gpBtn.setIconSize(QtCore.QSize(40, 40))'''
        self.gpBtn.setCheckable(True)
        self.gpBtn.setAutoExclusive(True)
        self.gpBtn.setObjectName("gpBtn")
        self.horizontalLayout_11.addWidget(self.gpBtn)
        self.verticalLayout_4.addWidget(self.frame_14)
        self.frame_17 = QtWidgets.QFrame(self.frame_11)
        self.frame_17.setFrameShape(QtWidgets.QFrame.Box)
        self.frame_17.setFrameShadow(QtWidgets.QFrame.Raised)
        self.frame_17.setObjectName("frame_17")
        self.horizontalLayout_13 = QtWidgets.QHBoxLayout(self.frame_17)
        self.horizontalLayout_13.setContentsMargins(2, 2, 2, 2)
        self.horizontalLayout_13.setSpacing(6)
        self.horizontalLayout_13.setObjectName("horizontalLayout_13")
        self.mBtn = QtWidgets.QPushButton(self.frame_17)
        #self.mBtn.setMinimumSize(QtCore.QSize(50, 50))
        self.mBtn.setMaximumSize(QtCore.QSize(70, 70))
        font = QtGui.QFont()
        font.setFamily("Segoe Print")
        font.setPointSize(max(8, 14))
        font.setBold(True)
        font.setWeight(75)
        self.mBtn.setFont(font)
        self.mBtn.setToolTipDuration(0)
        self.mBtn.setText("")
        icon3 = QtGui.QIcon()
        self.mBtn.setIcon(QtGui.QIcon(":/icons/5-removebg-preview.png"))
        self.mBtn.setIconSize(QtCore.QSize(65, 65))
        '''icon3.addPixmap(QtGui.QPixmap(":/icons2/icons/image (1).png"), QtGui.QIcon.Normal, QtGui.QIcon.Off)
        self.mBtn.setIcon(icon3)
        self.mBtn.setIconSize(QtCore.QSize(40, 40))'''
        self.mBtn.setCheckable(True)
        self.mBtn.setAutoExclusive(True)
        self.mBtn.setObjectName("mBtn")
        self.horizontalLayout_13.addWidget(self.mBtn)
        self.verticalLayout_4.addWidget(self.frame_17)
        self.frame_15 = QtWidgets.QFrame(self.frame_11)
        self.frame_15.setFrameShape(QtWidgets.QFrame.Box)
        self.frame_15.setFrameShadow(QtWidgets.QFrame.Raised)
        self.frame_15.setObjectName("frame_15")
        self.horizontalLayout_12 = QtWidgets.QHBoxLayout(self.frame_15)
        self.horizontalLayout_12.setContentsMargins(2, 2, 2, 2)
        self.horizontalLayout_12.setSpacing(6)
        self.horizontalLayout_12.setObjectName("horizontalLayout_12")
        self.trBtn = QtWidgets.QPushButton(self.frame_15)
        #self.trBtn.setMinimumSize(QtCore.QSize(50, 50))
        self.trBtn.setMaximumSize(QtCore.QSize(70, 70))
        font = QtGui.QFont()
        font.setFamily("Segoe Print")
        font.setPointSize(max(8, 14))
        font.setBold(True)
        font.setWeight(75)
        self.trBtn.setFont(font)
        self.trBtn.setToolTipDuration(-1)
        self.trBtn.setText("")
        icon4 = QtGui.QIcon()
        self.trBtn.setIcon(QtGui.QIcon(":/icons/1-removebg-preview.png"))
        self.trBtn.setIconSize(QtCore.QSize(65, 65))
        '''icon4.addPixmap(QtGui.QPixmap(":/icons2/icons/3d-view.svg"), QtGui.QIcon.Normal, QtGui.QIcon.Off)
        self.trBtn.setIcon(icon4)
        self.trBtn.setIconSize(QtCore.QSize(40, 40))'''
        self.trBtn.setCheckable(True)
        self.trBtn.setAutoExclusive(True)
        self.trBtn.setObjectName("trBtn")
        self.horizontalLayout_12.addWidget(self.trBtn)
        self.verticalLayout_4.addWidget(self.frame_15)
        '''self.verticalLayout_2.setStretch(0, 0)  # logo
        self.verticalLayout_2.setStretch(1, 1)  # buttons
        self.verticalLayout_2.setStretch(2, 0)  # gif expands ONLY'''
        self.verticalLayout_2.addWidget(self.logoFrame, 0)
        self.verticalLayout_2.addWidget(self.frame_11, 0, QtCore.Qt.AlignHCenter)  # buttons grow
        #self.verticalLayout_2.addWidget(self.iconFrame, 0)
        self.iconFrame = QtWidgets.QFrame(self.sideFrame)
        
        self.iconFrame.setStyleSheet("QFrame{\n"
"background-color: transparent;\n"
"border: none;\n"
"}")
        
        self.iconFrame.setSizePolicy(
             QtWidgets.QSizePolicy.Expanding,
             QtWidgets.QSizePolicy.Fixed   #  stops vertical stretching
)

        self.iconFrame.setMinimumHeight(80) 
        self.iconFrame.setFrameShape(QtWidgets.QFrame.StyledPanel)
        self.iconFrame.setFrameShadow(QtWidgets.QFrame.Raised)
        self.iconFrame.setObjectName("iconFrame")
        self.horizontalLayout_8 = QtWidgets.QHBoxLayout(self.iconFrame)
        self.horizontalLayout_8.setContentsMargins(0, 0, 0, 0)
        self.horizontalLayout_8.setSpacing(0)
        self.horizontalLayout_8.setObjectName("horizontalLayout_8")
        self.label_3 = QtWidgets.QLabel(self.iconFrame)
        self.label_3.setMinimumSize(80, 80)
        self.label_3.setSizePolicy(
             QtWidgets.QSizePolicy.Expanding,
             QtWidgets.QSizePolicy.Expanding
)

        self.label_3.setMaximumSize(100, 100)  # prevents overflow
        self.label_3.setScaledContents(True)
        self.label_3.setFrameShape(QtWidgets.QFrame.StyledPanel)
        self.label_3.setFrameShadow(QtWidgets.QFrame.Raised)
        self.label_3.setText("")
        self.label_3.setPixmap(QtGui.QPixmap(":/icons/Untitled design (2).gif"))
        self.label_3.setScaledContents(True)
        self.label_3.setAlignment(QtCore.Qt.AlignCenter)
        self.horizontalLayout_8.addWidget(self.label_3, alignment=QtCore.Qt.AlignCenter)
        self.label_3.setObjectName("label_3")
        self.movie = QMovie(":/icons/Untitled design (2).gif")  
        self.label_3.setMovie(self.movie)
        self.movie.start()
        
        self.verticalLayout_2.addWidget(self.iconFrame)
        #self.horizontalLayout_2.addWidget(self.sideFrame)
        self.mainSplitter = QtWidgets.QSplitter(QtCore.Qt.Horizontal)
        self.mainSplitter.addWidget(self.sideFrame)
        self.frame_3 = QtWidgets.QFrame(self.frame)
        self.frame_3.setStyleSheet("")
        self.frame_3.setFrameShape(QtWidgets.QFrame.NoFrame)
        self.frame_3.setFrameShadow(QtWidgets.QFrame.Raised)
        self.frame_3.setObjectName("frame_3")
        self.frame_3.setSizePolicy(
             QtWidgets.QSizePolicy.Expanding,
             QtWidgets.QSizePolicy.Expanding
)
        self.verticalLayout = QtWidgets.QVBoxLayout(self.frame_3)
        self.verticalLayout.setSpacing(0)
        self.verticalLayout.setContentsMargins(0,0,0,10)
        self.verticalLayout.setObjectName("verticalLayout")
        self.bodnFrame = QtWidgets.QFrame(self.frame_3)
        #self.bodnFrame.setFrameShape(QtWidgets.QFrame.Box)
        #self.bodnFrame.setFrameShadow(QtWidgets.QFrame.Raised)
        self.bodnFrame.setObjectName("bodnFrame")
        self.bodnFrame.setSizePolicy(
             QtWidgets.QSizePolicy.Expanding,
             QtWidgets.QSizePolicy.Preferred
)
        self.bodnFrame.setMinimumHeight(70)  
        self.verticalLayout_3 = QtWidgets.QVBoxLayout(self.bodnFrame)
        self.verticalLayout_3.setContentsMargins(0, 0, 0, 0)
        self.verticalLayout_3.setSpacing(0)
        self.verticalLayout_3.setObjectName("verticalLayout_3")
        self.frame_6 = BodyFrame(self.bodnFrame)
        self.frame_6.setMinimumSize(QtCore.QSize(0, 50))
        self.frame_6.setMinimumHeight(50)
        self.frame_6.setSizePolicy(
             QtWidgets.QSizePolicy.Expanding,
             QtWidgets.QSizePolicy.Expanding
        )
        self.frame_6.setStyleSheet("QFrame{\n"
        "background-color: transparent;\n"
        "border: none;\n"
        "}")
        #self.frame_6.setFrameShape(QtWidgets.QFrame.StyledPanel)
        #self.frame_6.setFrameShadow(QtWidgets.QFrame.Raised)
        self.frame_6.setObjectName("frame_6")
        self.horizontalLayout_7 = QtWidgets.QHBoxLayout(self.frame_6)
        self.horizontalLayout_7.setContentsMargins(8, 4, 8, 4)
        self.horizontalLayout_7.setSpacing(8)       
        self.horizontalLayout_7.setObjectName("horizontalLayout_7")
        self.label = QtWidgets.QLabel(self.frame_6)
        self.label.setStyleSheet("color: white;")

        font = QtGui.QFont()
        font.setFamily("Futura")
        font.setPointSize(max(8, 14))
        self.label.setFont(font)
        self.label.setSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Preferred)
        
        self.label.setObjectName("label")
        self.horizontalLayout_7.addWidget(self.label)
        self.verticalLayout_2.addStretch()
        self.unFrame = QtWidgets.QFrame(self.frame_6)
        sizePolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Expanding)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.unFrame.sizePolicy().hasHeightForWidth())
        self.unFrame.setSizePolicy(sizePolicy)
        self.unFrame.setMinimumSize(QtCore.QSize(0, 40))
        self.unFrame.setFrameShape(QtWidgets.QFrame.StyledPanel)
        self.unFrame.setFrameShadow(QtWidgets.QFrame.Raised)
        self.unFrame.setObjectName("unFrame")
        self.verticalLayout_11 = QtWidgets.QVBoxLayout(self.unFrame)
        self.verticalLayout_11.setContentsMargins(15, 0, 0, 0)
        self.verticalLayout_11.setSpacing(0)
        self.verticalLayout_11.setObjectName("verticalLayout_11")
        self.lineEdit = QtWidgets.QLineEdit(self.unFrame)
        self.lineEdit.setMaximumWidth(180)
        self.lineEdit.setSizePolicy(QtWidgets.QSizePolicy.Preferred, QtWidgets.QSizePolicy.Expanding)
        self.lineEdit.setObjectName("lineEdit")
        self.lineEdit.setPlaceholderText("enter name to create file")
        self.verticalLayout_11.addWidget(self.lineEdit)
        #  for user input field and connect Enter key to create user file
        self.userLineEdit = self.lineEdit
        self.userLineEdit.returnPressed.connect(self.create_user_file)
        self.horizontalLayout_7.addWidget(self.unFrame, 0, QtCore.Qt.AlignBottom)
        self.frame_8 = QtWidgets.QFrame(self.frame_6)
        self.frame_8.setFrameShape(QtWidgets.QFrame.StyledPanel)
        self.frame_8.setFrameShadow(QtWidgets.QFrame.Plain)
        self.frame_8.setObjectName("frame_8")
        self.horizontalLayout_6 = QtWidgets.QHBoxLayout(self.frame_8)
        self.horizontalLayout_6.setContentsMargins(0, 0, 0, 0)
        self.horizontalLayout_6.setSpacing(0)
        self.horizontalLayout_6.setObjectName("horizontalLayout_6")
        self.frame_9 = QtWidgets.QFrame(self.frame_8)
        self.frame_9.setMinimumSize(QtCore.QSize(150, 0))
        self.frame_9.setSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Expanding)
        self.frame_9.setFrameShape(QtWidgets.QFrame.Box)
        self.frame_9.setFrameShadow(QtWidgets.QFrame.Raised)
        self.frame_9.setObjectName("frame_9")
        self.horizontalLayout_3 = QtWidgets.QHBoxLayout(self.frame_9)
        self.horizontalLayout_3.setContentsMargins(0, 0, 0, 0)
        self.horizontalLayout_3.setSpacing(5)
        self.horizontalLayout_3.setObjectName("horizontalLayout_3")
        self.portBtn = QtWidgets.QPushButton(self.frame_9)
        self.portBtn.setMinimumSize(40, 40)
        self.portBtn.setSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Expanding)
        self.portBtn.setText("")
        icon5 = QtGui.QIcon()
        icon5.addPixmap(QtGui.QPixmap(":/icons/8848ee68ea738abadd3f2740df920522_X-Design.png"), QtGui.QIcon.Normal, QtGui.QIcon.Off)
        self.portBtn.setIcon(icon5)
        self.portBtn.setIconSize(QtCore.QSize(34, 34))
        self.portBtn.setObjectName("portBtn")
        #self.portBtn.setToolTip("click to refresh port")
        self.horizontalLayout_3.addWidget(self.portBtn, 0, QtCore.Qt.AlignVCenter)
        self.portCombo = QtWidgets.QComboBox(self.frame_9)
        self.portCombo.setMinimumSize(QtCore.QSize(80, 20))
        self.portCombo.setObjectName("portCombo")
        self.horizontalLayout_3.addWidget(self.portCombo)
        self.horizontalLayout_6.addWidget(self.frame_9)
        self.baudFrame = QtWidgets.QFrame(self.frame_8)
        self.baudFrame.setMinimumSize(QtCore.QSize(150, 0))
        self.baudFrame.setSizePolicy(QtWidgets.QSizePolicy.Minimum, QtWidgets.QSizePolicy.Minimum)
        self.baudFrame.setFrameShape(QtWidgets.QFrame.Box)
        self.baudFrame.setFrameShadow(QtWidgets.QFrame.Raised)
        self.baudFrame.setObjectName("baudFrame")
        self.horizontalLayout_4 = QtWidgets.QHBoxLayout(self.baudFrame)
        self.horizontalLayout_4.setContentsMargins(0, 0, 0, 0)
        self.horizontalLayout_4.setSpacing(5)
        self.horizontalLayout_4.setObjectName("horizontalLayout_4")
        self.rateBtn = QtWidgets.QPushButton(self.baudFrame)
        self.rateBtn.setMinimumSize(40, 40)
        self.rateBtn.setSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Expanding)
        self.rateBtn.setText("")
        icon6 = QtGui.QIcon()
        icon6.addPixmap(QtGui.QPixmap(":/icons/ae611c1f902e7b91204fde7c659d4a36_X-Design.png"), QtGui.QIcon.Normal, QtGui.QIcon.Off)
        self.rateBtn.setIcon(icon6)
        self.rateBtn.setIconSize(QtCore.QSize(34, 34))
        self.rateBtn.setObjectName("rateBtn")
        self.horizontalLayout_4.addWidget(self.rateBtn)
        self.baudCombo = QtWidgets.QComboBox(self.baudFrame)
        self.baudCombo.setMinimumSize(QtCore.QSize(100, 0))
        self.baudCombo.setSizePolicy(QtWidgets.QSizePolicy.Minimum, QtWidgets.QSizePolicy.Minimum)
        self.baudCombo.setObjectName("baudCombo")
        # Add standard baudrate options
        self.baudCombo.addItems([
            
            "115200",
            "9600",
            "14400",
            "19200",
            
        ])
        self.baudCombo.setCurrentText("115200")  # Set default
        self.horizontalLayout_4.addWidget(self.baudCombo)
        self.horizontalLayout_6.addWidget(self.baudFrame)
        self.horizontalLayout_7.addWidget(self.frame_8)
        self.notifyBtn = QtWidgets.QPushButton(self.frame_6)
        self.notifyBtn.setMinimumSize(40, 40)
        self.notifyBtn.setSizePolicy(QtWidgets.QSizePolicy.Minimum, QtWidgets.QSizePolicy.Minimum)
        self.notifyBtn.setText("")
        icon7 = QtGui.QIcon()
        icon7.addPixmap(QtGui.QPixmap(":/icons/message.png"), QtGui.QIcon.Normal, QtGui.QIcon.Off)
        self.notifyBtn.setIcon(icon7)
        self.notifyBtn.setIconSize(QtCore.QSize(36, 36))
        self.notifyBtn.setCheckable(True)
        self.notifyBtn.setAutoExclusive(True)
        self.notifyBtn.setObjectName("notifyBtn")
        self.notifyBtn.clicked.connect(self.load_stl_file)
        self.horizontalLayout_7.addWidget(self.notifyBtn, 0, QtCore.Qt.AlignVCenter)
        self.themeframe = QtWidgets.QFrame(self.frame_6)
        self.themeframe.setMinimumSize(QtCore.QSize(100, 0))
        self.themeframe.setSizePolicy(QtWidgets.QSizePolicy.Fixed, QtWidgets.QSizePolicy.Fixed)
        self.themeframe.setFrameShape(QtWidgets.QFrame.StyledPanel)
        self.themeframe.setFrameShadow(QtWidgets.QFrame.Raised)
        self.themeframe.setObjectName("themeframe")
        self.horizontalLayout = QtWidgets.QHBoxLayout(self.themeframe)
        self.horizontalLayout.setContentsMargins(0, 0, 0, 0)
        self.horizontalLayout.setSpacing(0)
        self.horizontalLayout.setObjectName("horizontalLayout")
        self.lightBtn = QtWidgets.QPushButton(self.themeframe)
        self.lightBtn.setMinimumSize(40, 40)
        self.lightBtn.setSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Expanding)
        self.lightBtn.setText("START MISSION")
        icon8 = QtGui.QIcon()
        icon8.addPixmap(QtGui.QPixmap(":/icons/power-button.png"), QtGui.QIcon.Normal, QtGui.QIcon.Off)
        self.lightBtn.setIcon(icon8)
        self.lightBtn.setIconSize(QtCore.QSize(32, 32))
        self.lightBtn.setCheckable(True)
        self.lightBtn.setAutoExclusive(True)
        self.lightBtn.setObjectName("lightBtn")
        self.lightBtn.setStyleSheet("QPushButton { border-radius: 17px; }")
        self.horizontalLayout.addWidget(self.lightBtn)
        
         # ===== MISSION CONTROL SETUP =====
        self.mission_active = False
        self.lightBtn.setCheckable(True)
        self.lightBtn.setChecked(False)
        self.lightBtn.setText("START MISSION")
        self.lightBtn.clicked.connect(self.toggle_mission)
        
# Initial state
        self.lightBtn.setEnabled(True)   # START enabled
        #self.darkBtn.setEnabled(False)  # END disabled

        self.horizontalLayout_7.addWidget(self.themeframe)
        
        
        self.verticalLayout_3.addWidget(self.frame_6)
        #self.verticalLayout.addWidget(self.bodnFrame)
        self.verticalSplitter = QtWidgets.QSplitter(QtCore.Qt.Vertical)
        self.verticalSplitter.addWidget(self.bodnFrame) 
        self.verticalSplitter.setHandleWidth(0)
        self.verticalSplitter.setStyleSheet("""
        QSplitter::handle {
           background: transparent;
             border: none;
             }
""")
        self.frame_5 = QtWidgets.QFrame(self.frame_3)
        sizePolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Expanding)
        sizePolicy.setHeightForWidth(self.frame_5.sizePolicy().hasHeightForWidth())
        self.frame_5.setSizePolicy(sizePolicy)
        self.frame_5.setStyleSheet("QFrame#frame_5{\n"
"background-color: transparent;\n"
"border: none;\n"
"}")
        self.frame_5.setFrameShape(QtWidgets.QFrame.StyledPanel)
        self.frame_5.setFrameShadow(QtWidgets.QFrame.Raised)
        self.frame_5.setObjectName("frame_5")
        self.verticalLayout_5 = QtWidgets.QVBoxLayout(self.frame_5)
        self.stackedWidget = QtWidgets.QStackedWidget(self.frame_5)
        self.verticalLayout_5.setContentsMargins(0,0,0,0)
        self.verticalLayout_5.setSpacing(0)
        self.verticalLayout_5.setObjectName("verticalLayout_5")
        self.stackedWidget.setContentsMargins(0,0,0,0)

        self.stackedWidget.setStyleSheet("QFrame{\n"
"background-color: transparent;\n"
"border: none;\n"
"}")
        self.stackedWidget.setObjectName("stackedWidget")
        #self.stackedWidget.setMinimumSize(QtCore.QSize(0, 380))      
        self.stackedWidget.setSizePolicy(
            QtWidgets.QSizePolicy.Expanding,
            QtWidgets.QSizePolicy.Expanding
)
        self.db = QtWidgets.QWidget()
        self.db.setObjectName("db")
        self.verticalLayout_6 = QtWidgets.QVBoxLayout(self.db)
        self.verticalLayout_6.setObjectName("verticalLayout_6")
        self.frame_18 = QtWidgets.QFrame(self.db)
        self.frame_18.setFrameShape(QtWidgets.QFrame.StyledPanel)
        self.frame_18.setFrameShadow(QtWidgets.QFrame.Raised)
        self.frame_18.setObjectName("frame_18")
        self.verticalLayout_6.addWidget(self.frame_18)
        self.stackedWidget.addWidget(self.db)
        self.cs = QtWidgets.QWidget()
        self.cs.setObjectName("cs")
        self.verticalLayout_7 = QtWidgets.QVBoxLayout(self.cs)
        self.verticalLayout_7.setObjectName("verticalLayout_7")
        self.frame_19 = QtWidgets.QFrame(self.cs)
        self.frame_19.setFrameShape(QtWidgets.QFrame.StyledPanel)
        self.frame_19.setFrameShadow(QtWidgets.QFrame.Raised)
        self.frame_19.setObjectName("frame_19")
        self.verticalLayout_7.addWidget(self.frame_19)
        self.stackedWidget.addWidget(self.cs)
        self.gp = QtWidgets.QWidget()
        self.gp.setObjectName("gp")
        self.verticalLayout_8 = QtWidgets.QVBoxLayout(self.gp)
        self.verticalLayout_8.setObjectName("verticalLayout_8")
        self.frame_20 = QtWidgets.QFrame(self.gp)
        self.frame_20.setFrameShape(QtWidgets.QFrame.StyledPanel)
        self.frame_20.setFrameShadow(QtWidgets.QFrame.Raised)
        self.frame_20.setObjectName("frame_20")
        self.verticalLayout_8.addWidget(self.frame_20)
        self.stackedWidget.addWidget(self.gp)
        self.map = QtWidgets.QWidget()
        self.map.setObjectName("map")
        self.verticalLayout_9 = QtWidgets.QVBoxLayout(self.map)
        self.verticalLayout_9.setObjectName("verticalLayout_9")
        self.frame_21 = QtWidgets.QFrame(self.map)
        self.frame_21.setFrameShape(QtWidgets.QFrame.StyledPanel)
        self.frame_21.setFrameShadow(QtWidgets.QFrame.Raised)
        self.frame_21.setObjectName("frame_21")
        self.label_12 = QtWidgets.QLabel(self.frame_21)
        self.label_12.setGeometry(QtCore.QRect(200, 110, 331, 91))
        font = QtGui.QFont()
        font.setFamily("Segoe Print")
        font.setBold(True)
        font.setWeight(75)
        self.label_12.setFont(font)
        self.label_12.setObjectName("label_12")
        self.verticalLayout_9.addWidget(self.frame_21)
        self.stackedWidget.addWidget(self.map)
        self.motion = QtWidgets.QWidget()
        self.motion.setObjectName("motion")
        self.verticalLayout_10 = QtWidgets.QVBoxLayout(self.motion)
        self.verticalLayout_10.setObjectName("verticalLayout_10")
        self.frame_22 = QtWidgets.QFrame(self.motion)
        self.frame_22.setFrameShape(QtWidgets.QFrame.StyledPanel)
        self.frame_22.setFrameShadow(QtWidgets.QFrame.Raised)
        self.frame_22.setObjectName("frame_22")
        self.verticalLayout_10.addWidget(self.frame_22)
        self.stackedWidget.addWidget(self.motion)
        # --- replace placeholder pages with real pages ---
        # --- create TWO separate STL views ---
        self.stlView_dashboard = STLView(
            resource_path("gcs_rocket.STL"),
            self.serial_manager
)

        self.stlView_motion = STLView(
            resource_path("gcs_rocket.STL"),
            self.serial_manager
)
     
#         self.stlView.setSizePolicy(
#             QtWidgets.QSizePolicy.Expanding,
#             QtWidgets.QSizePolicy.Expanding
# )

        try:
            # Dashboard (index 0)
            self.dashboardPage = DashboardPage(
                self.serial_manager,
                self.stlView_dashboard
)
            self.stackedWidget.removeWidget(self.db)
            self.stackedWidget.insertWidget(0, self.dashboardPage)
            self.dashboard_resizer = SizeManager(
                widget=self.dashboardPage,
                mode=ModeRatio.BOTH
            )


            # Console (index 1)
            self.consolePage = ConsolePage(self.serial_manager)
            self.stackedWidget.removeWidget(self.cs)
            self.stackedWidget.insertWidget(1, self.consolePage)

            # Graphs (index 2)
            self.graphPage = GraphPage(self.serial_manager)
            self.stackedWidget.removeWidget(self.gp)
            self.stackedWidget.insertWidget(2, self.graphPage)
            self.graph_resizer = SizeManager(
                self.graphPage,
                ModeRatio.BOTH
            )

            # Map (index 3)
            self.mapPage = MapPage(self.serial_manager)
            self.stackedWidget.removeWidget(self.map)
            self.stackedWidget.insertWidget(3, self.mapPage)
            self.map_resizer = SizeManager(
                self.mapPage,
                ModeRatio.BOTH
            )
            
            self.motionPage = MotionPage(
                self.serial_manager,
                self.stlView_motion
)
            self.stackedWidget.removeWidget(self.motion)
            self.stackedWidget.insertWidget(4, self.motionPage)
            self.motion_resizer = SizeManager(
                self.motionPage,
                ModeRatio.BOTH
            )

            '''self.surfacePlotPage = SurfacePlotPage()
            self.stackedWidget.removeWidget(self.nag)
            self.stackedWidget.insertWidget(4, self.surfacePlotPage)'''

        except Exception as e:
            print("Page load error:", e)

        self.verticalLayout_5.addWidget(self.stackedWidget)
        #self.verticalLayout.addWidget(self.frame_5)
        #self.verticalLayout.setStretch(0, 0)  # bodnFrame (header)
        #self.verticalLayout.setStretch(1, 1)  # frame_5 (stackedWidget)
        self.verticalSplitter.addWidget(self.frame_5)     # stacked widget
        self.verticalSplitter.setStretchFactor(0, 1)
        self.verticalSplitter.setStretchFactor(1, 9)
        self.verticalSplitter.setChildrenCollapsible(False)
        self.verticalLayout.addWidget(self.verticalSplitter)
        self.frame_5.raise_()
        self.bodnFrame.raise_()
        #self.horizontalLayout_2.addWidget(self.frame_3)
        #self.horizontalLayout_2.setStretch(0, 0)
        #self.horizontalLayout_2.setStretch(1, 1)  
        self.mainSplitter.addWidget(self.frame_3)

        self.mainSplitter.setStretchFactor(0, 2) 
        self.mainSplitter.setStretchFactor(1, 8) 

        self.mainSplitter.setChildrenCollapsible(False)
        self.mainSplitter.setHandleWidth(0)
        self.mainSplitter.setSizes([200, 800])
        self.mainSplitter.setStyleSheet("""
         QSplitter::handle {
          background: transparent;
          border: none;}
""")
        
        self.horizontalLayout_2.addWidget(self.mainSplitter)
        self.horizontalLayout_5.addWidget(self.frame)
        MainWindow.setCentralWidget(self.centralwidget)
        
        for frame in [self.frame_18, self.frame_19, self.frame_21, self.frame_22]:
            effect = QtWidgets.QGraphicsDropShadowEffect(frame)
            effect.setBlurRadius(40)
            effect.setColor(QtGui.QColor(170, 0, 255, 180))  
            effect.setOffset(0, 0)
            frame.setGraphicsEffect(effect)

        center_effect = QtWidgets.QGraphicsDropShadowEffect(self.frame_20)
        center_effect.setBlurRadius(70)
        center_effect.setColor(QtGui.QColor(170, 0, 255, 220))  
        center_effect.setOffset(0, 0)

        self.frame_20.setGraphicsEffect(center_effect)


        
        self.retranslateUi(MainWindow)
        # Set default page to Dashboard (index 0)
        self.dbBtn.setChecked(True)
        self.stackedWidget.setCurrentIndex(0)
        QtCore.QMetaObject.connectSlotsByName(MainWindow)
        self.auto_font_scaler = AutoFontScaler(MainWindow)
        self.main_window = MainWindow
        MainWindow.installEventFilter(self.main_window)
        
        # ===== APPLY JARVIS GLOW TO BUTTONS =====
        self.apply_glow(self.dbBtn)
        self.apply_glow(self.csBtn)
        self.apply_glow(self.gpBtn)
        self.apply_glow(self.mBtn)
        self.apply_glow(self.trBtn)
        self.apply_glow(self.lightBtn)
        #self.apply_glow(self.darkBtn)
        self.apply_glow(self.label_2)
        self.apply_glow(self.label)
        
        #-----------Page Animations-----------#
        self.dbBtn.clicked.connect(lambda: self.switch_page_animated(0))
        self.csBtn.clicked.connect(lambda: self.switch_page_animated(1))
        self.gpBtn.clicked.connect(lambda: self.switch_page_animated(2))
        self.mBtn.clicked.connect(lambda: self.switch_page_animated(3))
        self.trBtn.clicked.connect(lambda: self.switch_page_animated(4))
        
        self.portCombo.currentIndexChanged.connect(self.auto_connect_port)
        self.portBtn.clicked.connect(self.load_serial_ports)
        self.notifyBtn.clicked.connect(self.open_notify_window)
        self.load_serial_ports()
        
        
        
       

    def load_serial_ports(self):
        # ----- STOP LOGGING -----
        if self.log_file:
           print("LOG STOPPED")
           self.log_file.close()

           self.log_file = None
        self.log_writer = None
        self.logging_enabled = False
        self.current_user = None
        self.lineEdit.clear()

    # ----- REFRESH PORTS -----
        self.portCombo.clear()
        ports = serial.tools.list_ports.comports()

        for port in ports:
            self.portCombo.addItem(port.device)
            
    def set_active_button(self, clicked_btn):
        for btn in self.frame_11.findChildren(QtWidgets.QPushButton):
            btn.setGraphicsEffect(None)
        self.apply_breathing_glow(clicked_btn)

    
    def switch_page_animated(self, index):
        current_index = self.stackedWidget.currentIndex()
        if current_index == index:
            return

        current_widget = self.stackedWidget.currentWidget()
        next_widget = self.stackedWidget.widget(index)

        width = self.stackedWidget.frameRect().width()

        # Direction
        direction = 1 if index > current_index else -1

        next_widget.setGeometry(
            direction * width,
            0,
            width,
            self.stackedWidget.height()
        )
        next_widget.show()

        self.anim_current = QtCore.QPropertyAnimation(current_widget, b"pos")
        self.anim_current.setDuration(300)
        self.anim_current.setStartValue(QtCore.QPoint(0, 0))
        self.anim_current.setEndValue(QtCore.QPoint(-direction * width, 0))
        self.anim_current.setEasingCurve(QtCore.QEasingCurve.OutCubic)

        self.anim_next = QtCore.QPropertyAnimation(next_widget, b"pos")
        self.anim_next.setDuration(300)
        self.anim_next.setStartValue(QtCore.QPoint(direction * width, 0))
        self.anim_next.setEndValue(QtCore.QPoint(0, 0))
        self.anim_next.setEasingCurve(QtCore.QEasingCurve.OutCubic)

        self.anim_group = QtCore.QParallelAnimationGroup()
        self.anim_group.addAnimation(self.anim_current)
        self.anim_group.addAnimation(self.anim_next)

        def on_finished():
            self.stackedWidget.setCurrentIndex(index)
            current_widget.move(0, 0)

        self.anim_group.finished.connect(on_finished)
        self.anim_group.start()
        
    def retranslateUi(self, MainWindow):
        _translate = QtCore.QCoreApplication.translate
        MainWindow.setWindowTitle(_translate("MainWindow", "MainWindow"))
        self.dbBtn.setToolTip(_translate("MainWindow", "DashBoard"))
        self.csBtn.setToolTip(_translate("MainWindow", "Console"))
        self.gpBtn.setToolTip(_translate("MainWindow", "Graphs"))
        self.mBtn.setToolTip(_translate("MainWindow", "Map"))
        self.trBtn.setToolTip(_translate("MainWindow", "3D Motion"))
        self.label.setText(_translate("MainWindow", "Back on Deck,Navigator!"))
        self.portBtn.setToolTip(_translate("MainWindow", "Port: Click to refresh and detect connected devices"))
        self.rateBtn.setToolTip(_translate("MainWindow", "Baudrate"))
        self.notifyBtn.setToolTip(_translate("MainWindow", "Messages"))
        self.label_12.setText(_translate("MainWindow", "TextLabel 4"))
        self.csBtn.setToolTip(_translate("MainWindow", "Console"))
        self.gpBtn.setToolTip(_translate("MainWindow", "Graphs"))
        self.mBtn.setToolTip(_translate("MainWindow", "Map"))
        self.trBtn.setToolTip(_translate("MainWindow", "3D Motion"))
        self.label.setText(_translate("MainWindow", "Back on Deck,Navigator!"))
        self.portBtn.setToolTip(_translate("MainWindow", "Port: Click to refresh and detect connected devices"))
        self.rateBtn.setToolTip(_translate("MainWindow", "Baudrate: Click to select data transmission speed"))
        self.notifyBtn.setToolTip(_translate("MainWindow", "Select STL file to load and display"))
        self.label_12.setText(_translate("MainWindow", "TextLabel 4"))
        
        
    def eventFilter(self, obj, event):
        if event.type() == QtCore.QEvent.Resize:
            if hasattr(self, "stlView_dashboard"):
                self.stlView_dashboard.update()

            if hasattr(self, "stlView_motion"):
                self.stlView_motion.update()

        return super().eventFilter(obj, event)
    
    def start_mission(self):
        if self.mission_active:
           return

        # Get port and baud rate from UI
        port = self.portCombo.currentText()
        baud = int(self.baudCombo.currentText())
        
        if not port:
            QMessageBox.warning(None, "Error", "Please select a serial port first")
            return

        self.mission_active = True
        print("MISSION STARTED")
        self.mission_start = datetime.now().strftime("%d-%m-%Y %H:%M:%S")
        self.serial_start_time = QtCore.QDateTime.currentDateTime()

        # Connect to port and start serial manager
        self.serial_manager.connect_port(port, baud)

    
    def end_mission(self):
        if not self.mission_active:
            return

        self.mission_active = False
        print("MISSION ENDED")
        self.mission_end = datetime.now().strftime("%d-%m-%Y %H:%M:%S")

        # -------- STOP CSV LOGGING --------
        if hasattr(self, "logging_enabled") and self.logging_enabled:
            self.stop_logging()

        # -------- STOP TELEMETRY PROPERLY --------
        try:
            self.serial_manager.data_received.disconnect()
        except:
            pass

        self.serial_manager.stop()
        self.serial_manager.disconnect_port()

        # Wait for thread to finish
        if self.serial_manager.isRunning():
            self.serial_manager.quit()
            self.serial_manager.wait()

    
    def auto_connect_port(self):
   
     port = self.portCombo.currentText()
     baud = int(self.baudCombo.currentText())

     if port:
        self.serial_manager.connect_port(port, baud)
        self.serial_manager.data_received.connect(self.on_serial_data)

     print("AUTO CONNECT:", port)

    def get_downloads_folder(self):
        return str(Path.home() / "Downloads")
  
    def route_serial_data(self, data):
        if hasattr(self, "logging_enabled") and self.logging_enabled:
            try:
               data_list = data.strip().split(",")
               self.log_data(data_list)
            except Exception as e:
                print("CSV Parse Error:", e)
                
        if hasattr(self, 'notify_window') and self.notify_window and self.notify_window.isVisible():
           self.notify_window.add_serial_data(data)
    
    # Dashboard
        if hasattr(self, "dashboardPage"):
           self.dashboardPage.update_data(data)

    # Console
        if hasattr(self, "consolePage"):
           self.consolePage.append_text(data)

    # Graph
        if hasattr(self, "graphPage"):
           self.graphPage.update_data(data)

    # Map
        if hasattr(self, "mapPage"):
           self.mapPage.update_gps(data)

    # Motion
        if hasattr(self, "motionPage"):
           self.motionPage.on_serial_data(data)
           
           
    def on_new_serial_data(self, data):
        if self.mission_active:
            self.resume_logging(data)

    def show_notification(self, text):
        
        # ---- AUTO STOP MISSION WHEN SERIAL STOPS ----
        if any(word in text.lower() for word in ["disconnected", "stopped", "closed"]):
           if self.mission_start:
              mission_end = datetime.now().strftime("%d-%m-%Y %H:%M:%S")

              self.cursor.execute(
            "INSERT INTO missions (user, start_time, end_time) VALUES (?, ?, ?)",
                  (self.mission_user, self.mission_start, mission_end)
              )
              self.db.commit()
              self.mission_start = None

        login_str = self.login_time.toString("dd-MM-yyyy hh:mm:ss")

        if self.serial_start_time:
           serial_str = self.serial_start_time.toString("dd-MM-yyyy hh:mm:ss")
        else:
            serial_str = "Not started"
        if self.logging_enabled:
           self.stop_logging()


        msg = f"""
 Login Time: {login_str}
 Serial Started: {serial_str}

🛰 Status:
{text}
"""
        QMessageBox.information(None, "Notifications", msg)
        # ------ END MISSION ON DISCONNECT -------#
        if any(word in text.lower() for word in ["disconnected", "stopped", "closed"]):
           if self.mission_start and self.current_mission_id:

              mission_end = datetime.now().strftime("%d-%m-%Y %H:%M:%S")

              self.cursor.execute(
            "UPDATE missions SET end_time=? WHERE id=?",
             (mission_end, self.current_mission_id)
        )

              self.db.commit()

              print("MISSION SAVED:", self.current_mission_id)

              self.mission_start = None
              self.current_mission_id = None
        
    def create_user_file(self):
        username = self.userLineEdit.text().strip()
        if not username:
            QMessageBox.warning(None, "Error", "Enter username first")
            return

        

        downloads = Path.home() / "Downloads"
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        file_path = downloads / f"{username}_{timestamp}.csv"

        self.log_file = open(file_path, "a", newline="", encoding="utf-8")
        self.log_writer = csv.writer(self.log_file)

        # ✅ FIXED ROCKET ID (GLOBAL FOR FILE)
        self.rocket_id = "TRI-100M"

        # ===============================
        #  FILE HEADER SECTION
        # ===============================
        self.log_writer.writerow(["=============================================="])
        self.log_writer.writerow([" SYNODIC GCS FLIGHT LOG"])
        self.log_writer.writerow(["=============================================="])
        self.log_writer.writerow(["Username:", username])
        self.log_writer.writerow(["Rocket ID:", self.rocket_id])   # ✅ ADDED
        self.log_writer.writerow(["Log Start Time:", datetime.now().strftime("%d-%m-%Y %H:%M:%S")])
        self.log_writer.writerow(["Mission Status:", "ACTIVE"])
        self.log_writer.writerow([])

        # ===============================
        #  DATA HEADER SECTION
        # ===============================
        self.log_writer.writerow([
                              
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
        "Mag X",
        "Mag Y",
        "Mag Z",
        "Euler X",
        "Euler Y",
        "Euler Z",
        "State",
        "Battery"
    ])
        self.logging_enabled = True
        self.current_user = username

        QMessageBox.information(
            None,
            "Logging Started",
            f"Structured CSV logging started:\n{file_path}"
        )

        self.label_12.setText(f"Logging: {username}")

    def log_data(self, data_list):
        if not hasattr(self, "log_file") or not self.log_file:
            return

        try:
            self.log_writer.writerow(data_list)
            self.log_file.flush()

            # Store last logged data
            self.last_logged_data = data_list

        except Exception as e:
            print("Logging failed:", e)
            
    def resume_logging(self, new_data):
        """
        Resume logging after reconnection.
        Prevents duplicate data and ensures continuity.
        """
        if not hasattr(self, "last_logged_data"):
            self.log_data(new_data)
            return

        try:
            # Example logic: skip duplicate row
            if new_data != self.last_logged_data:
                self.log_data(new_data)
            else:
                # Duplicate detected → skip
                pass

        except Exception as e:
            print("Resume logging failed:", e)
            
    def stop_logging(self):
        if hasattr(self, "log_file") and self.log_file:

        # Write footer
            self.log_writer.writerow([])
            self.log_writer.writerow(["Mission Status:", "ENDED"])
            end_time = datetime.now().strftime("%d-%m-%Y %H:%M:%S")
            end_time = datetime.now().strftime("%d-%m-%Y %H:%M:%S")
            -self.log_writer.writerow(["Log End Time:", end_time])

            self.log_file.flush()
            self.log_file.close()

            self.log_file = None
            self.logging_enabled = False

            print("CSV LOGGING STOPPED")
            self.label_12.setText("Logging: OFF")

            
    def show_mission_history(self):

        dialog = QtWidgets.QDialog()
        dialog.setWindowTitle("📌 Mission History")
        dialog.resize(650, 400)

        layout = QtWidgets.QVBoxLayout(dialog)

        table = QtWidgets.QTableWidget()
        layout.addWidget(table)

    #  Load missions from DatabaseManager
        rows = self.db_manager.get_missions()

        table.setRowCount(len(rows))
        table.setColumnCount(3)
        table.setHorizontalHeaderLabels(["Mission ID", "User", "Start Time"])

        for r, (mid, user, start_time) in enumerate(rows):
            table.setItem(r, 0, QtWidgets.QTableWidgetItem(str(mid)))
            table.setItem(r, 1, QtWidgets.QTableWidgetItem(user))
            table.setItem(r, 2, QtWidgets.QTableWidgetItem(start_time))

    # Double click → open telemetry packets
            table.cellDoubleClicked.connect(
            lambda r, c: self.show_mission_data(rows[r][0])
    )

        dialog.exec_()

    def show_mission_data(self, mission_id):

        dialog = QtWidgets.QDialog()
        dialog.setWindowTitle(f"Telemetry Data - Mission {mission_id}")
        dialog.resize(900, 500)

        layout = QtWidgets.QVBoxLayout(dialog)

        table = QtWidgets.QTableWidget()
        layout.addWidget(table)

    #  Fetch telemetry rows
        telemetry_rows = self.db_manager.get_telemetry_for_mission(mission_id)

        if not telemetry_rows:
            QMessageBox.information(None, "No Data", "No telemetry found for this mission.")
            return

        headers = [
        "Uptime", "Altitude", "Pressure", "Temp",
        "Voltage", "Battery", "Current",
        "Lat", "Lon", "Mode"
    ]

        table.setColumnCount(len(headers))
        table.setHorizontalHeaderLabels(headers)
        table.setRowCount(len(telemetry_rows))

        for r, row in enumerate(telemetry_rows):

            uptime   = row[2]
            altitude = row[3]
            pressure = row[4]
            temp     = row[5]
            volt     = row[6]
            batt     = row[7]
            current  = row[8]
            lat      = row[9]
            lon      = row[10]
            mode     = row[-1]

            values = [uptime, altitude, pressure, temp,
                  volt, batt, current,
                  lat, lon, mode]

            for c, val in enumerate(values):
                table.setItem(r, c, QtWidgets.QTableWidgetItem(str(val)))
  
            dialog.exec_()
        
    def resource_path(relative_path):
        try:
            base_path = sys._MEIPASS  # used by PyInstaller
        except Exception:
            base_path = os.path.abspath(".")
        return os.path.join(base_path, relative_path)
    def open_notify_window(self):
        username = self.userLineEdit.text().strip()
        if not username:
           QtWidgets.QMessageBox.warning(self, "Error", "Please enter a username first!")
           return

    # Ensure attribute exists
        if not hasattr(self, "notify_window") or self.notify_window is None:
            self.notify_window = NotificationWindow(username=username)

        self.notify_window.show()
        self.notify_window.raise_()
        self.notify_window.activateWindow()
        
    def toggle_mission(self):
        if self.lightBtn.isChecked():
            self.lightBtn.setText("END MISSION")
            self.lightBtn.setIcon(QtGui.QIcon(":/icons/play.png"))
            self.lightBtn.setStyleSheet("background-color: #8B0000; border-radius: 17px; color: white;")
            self.start_mission()
        else:
            self.lightBtn.setText("START MISSION")
            self.lightBtn.setIcon(QtGui.QIcon(":/icons/power-button.png"))
            self.lightBtn.setStyleSheet("background-color: #1e3a5f; border-radius: 17px; color: white;")
            self.end_mission()

        self.lightBtn.repaint()  
        
    def load_stl_file(self):

        file_path, _ = QtWidgets.QFileDialog.getOpenFileName(
            None,
            "Select STL File",
            "",
            "STL Files (*.stl *.STL)"
        )

        # User cancelled → keep default rocket
        if not file_path:
            return

        try:
            # Replace only after user selects STL
            self.stlView_dashboard.load_new_stl(
                file_path
            )

            self.stlView_motion.load_new_stl(
                file_path
            )

            QMessageBox.information(
                None,
                "Success",
                "New STL Loaded"
            )

        except Exception as e:
            print("STL Upload Error:", e)
        
    

if __name__ == "__main__":
    import sys
    QtCore.QCoreApplication.setAttribute(QtCore.Qt.AA_EnableHighDpiScaling)
    QtCore.QCoreApplication.setAttribute(QtCore.Qt.AA_UseHighDpiPixmaps)
    app = QtWidgets.QApplication(sys.argv)
    app.setFont(QtGui.QFont("Futura", 10))
    MainWindow = QtWidgets.QMainWindow()
    ui = Ui_MainWindow()
    ui.setupUi(MainWindow)
    
    MainWindow.show()
    sys.exit(app.exec_())