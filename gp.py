import sys
import random
from PyQt5.QtWidgets import QApplication, QWidget, QVBoxLayout, QGridLayout, QPushButton, QHBoxLayout
from PyQt5.QtCore import Qt, QTimer
import pyqtgraph as pg
from serial_manager import SerialManager  # your serial manager

class ClickablePlot(pg.PlotWidget):
    def mouseDoubleClickEvent(self, event):
        if hasattr(self, "expand_callback"):
            self.expand_callback(self)
        super().mouseDoubleClickEvent(event)


class GraphsWindow(QWidget):
    def __init__(self, serial_manager=None):
        super().__init__()
        self.serial_manager = serial_manager or SerialManager()
        self.paused = False
        self.interval = 40  
        self.glow_state = False
# update interval in ms

        # ---------------- Window ----------------
        self.setWindowTitle("Telemetry Dashboard")
        self.resize(1280, 750)
        self.setStyleSheet("""
GraphsWindow {
    background: qlineargradient(
        x1:0, y1:0, x2:1, y2:1,
        stop:0   #041821,
        stop:0.5 #063b52,
        stop:1   #0a6c85
    );
    color: #e8fcff;
    font-family: "Segoe UI";
   
}


QWidget#GraphFrame {
    background: qlineargradient(
        x1:0, y1:0, x2:0, y2:1,
        stop:0 rgba(20, 120, 160, 160),
        stop:1 rgba(5, 30, 50, 230)
    );
    border-radius: 18px;
    border: 1.5px solid rgba(0, 229, 255, 160);
}


PlotWidget {
    background: rgba(10, 35, 60, 210);
    border: 1.5px solid rgba(0, 229, 255, 100);
    border-radius: 12px;
}


QPushButton {
    background: qlineargradient(
        x1:0, y1:0, x2:0, y2:1,
        stop:0 #00f5ff,
        stop:1 #0096a8
    );
    color: #002b36;
    border: 1.5px solid rgba(0, 255, 255, 190);
    border-radius: 10px;
    padding: 6px 18px;
    font-weight: 600;
}


QPushButton:hover {
    background: qlineargradient(
        x1:0, y1:0, x2:0, y2:1,
        stop:0 #6ffcff,
        stop:1 #00cdd6
    );
    border: 1.5px solid #e0ffff;
}


QPushButton:pressed {
    background: qlineargradient(
        x1:0, y1:0, x2:0, y2:1,
        stop:0 #007c88,
        stop:1 #004f57
    );
    border: 1.5px solid #00e5ff;
}


QPushButton:disabled {
    background: rgba(80, 120, 130, 120);
    color: rgba(220, 255, 255, 120);
    border: 1px solid rgba(0, 255, 255, 60);
}
""")


        # ---------------- Layout ----------------
        main_layout = QVBoxLayout(self)
        self.setLayout(main_layout)
        
        self.expand_container = QWidget(self)
        self.expand_container_layout = QVBoxLayout(self.expand_container)
        self.expand_container.hide()
        main_layout.insertWidget(0, self.expand_container)
        
        self.grid_container = QWidget(self)
        self.grid_layout = QGridLayout(self.grid_container)
        main_layout.addWidget(self.grid_container)


        # ---------------- Graphs ----------------
        self.curves = {}
        self.data = {}
        self.graph_info = {}      
        self.expanded = None
        self.close_btn = None

        # List of graphs to create
        graph_items = [
            ("Altitude (m)", False, ["alt"]),
            ("Pressure (Pa)", False, ["press"]),
            ("Acceleration (X,Y,Z)", True, ["acc_x","acc_y","acc_z"]),
            ("Gyroscope (X,Y,Z)", True, ["gyr_x","gyr_y","gyr_z"]),
            ("Magnetometer (X,Y,Z)", True, ["mag_x","mag_y","mag_z"]),
            ("Current (mA)", False, ["curr"]),
        ]

        color_map = {
            "acc_x": "red", "acc_y": "green", "acc_z": "blue",
            "gyr_x": "orange", "gyr_y": "magenta", "gyr_z": "cyan",
            "mag_x": "red", "mag_y": "green", "mag_z": "blue",
            "alt": "cyan", "press": "yellow", "speed": "red",
             "curr": "cyan",
        }

        row, col = 0, 0
        for title, three_axis, keys in graph_items:
            frame, plot = self.graph(title, three_axis=three_axis)
            for key in keys:
                pen_color = color_map.get(key, "cyan")
                self.curves[key] = plot.plot(pen=pg.mkPen(color=pen_color, width=2), name=key)
                self.data[key] = {"x": [], "y": []}

            self.grid_layout.addWidget(frame, row, col)
            self.graph_info[plot] = (frame, row, col)
            col += 1
            if col >= 3:  # 4 graphs per row
                col = 0
                row += 1
                
            

        # ---------------- Buttons ----------------
        btn_layout = QHBoxLayout()
        main_layout.addLayout(btn_layout)

        self.pause_btn = QPushButton("Pause")
        self.resume_btn = QPushButton("Resume")
        self.speed_up_btn = QPushButton("Speed x2")
        self.refresh_btn = QPushButton("Refresh Graphs")
        btn_layout.addWidget(self.pause_btn)
        btn_layout.addWidget(self.resume_btn)
        btn_layout.addWidget(self.speed_up_btn)
        btn_layout.addWidget(self.refresh_btn)

        self.pause_btn.clicked.connect(lambda: setattr(self, 'paused', True))
        self.resume_btn.clicked.connect(lambda: setattr(self, 'paused', False))
        self.speed_up_btn.clicked.connect(self.speed_up)
        self.refresh_btn.clicked.connect(self.refresh_graphs)

        # ---------------- Timer ----------------
        self.timer = QTimer()
        self.timer.timeout.connect(self.update_plots)
        self.timer.start(self.interval)

        # ---------------- Serial signal ----------------
        if self.serial_manager:
            self.serial_manager.data_received.connect(self.on_serial_data)

    # ---------------- Graph creation ----------------
    def graph(self, title, three_axis=False):
        frame = QWidget()
        frame.setObjectName("GraphFrame")
        layout = QVBoxLayout(frame)
        layout.setContentsMargins(12,12,12,12)

        plot = ClickablePlot()
        plot.expand_callback = self.expand_graph

        plot.setStyleSheet("""
    border: 2px solid rgba(0, 229, 255, 120);
    border-radius: 12px;
""")
        plot.setTitle(title, color="w", size="12pt")
        plot.showGrid(x=True, y=True, alpha=0.3)
        plot.setLabel("bottom", "Time (s)")
        plot.setLabel("left", title)
        plot.setBackground((10, 35, 60, 220))
        plot.enableAutoRange(axis='y', enable=True)
 

        if three_axis:
            plot.addLegend()
        plot.setMouseEnabled(x=True, y=True)
        layout.addWidget(plot)
        return frame, plot

    # ---------------- Plot update ----------------
    def update_plots(self):
        if self.paused:
           return

        self.glow_state = not self.glow_state
        glow_alpha = 200 if self.glow_state else 90
        for key, curve in self.curves.items():
            if self.data[key]["x"]:
                curve.setData(self.data[key]["x"], self.data[key]["y"])

                y = self.data[key]["y"]
                if y:
                    min_y, max_y = min(y), max(y)
                    if min_y == max_y:
                        max_y += 1  # avoid flat line crash
                    curve.getViewBox().setYRange(min_y, max_y, padding=0.3)
                

    # ---------------- Serial data ----------------
    def on_serial_data(self, line: str):
        if self.paused:
            return
        parts = line.strip().split(",")
        if len(parts) < 5:
            return
        try:
            # Time in seconds
            try:
                h,m,s = map(int, parts[1].split(":"))
                t = h*3600 + m*60 + s
            except:
                t = len(self.data["alt"]["x"]) if "alt" in self.data else 0

                mapping = {
            "alt": 2,
            "press": 3,
            "acc_x": 8, "acc_y": 9, "acc_z": 10,
            "gyr_x": 11, "gyr_y": 12, "gyr_z": 13,
            "mag_x": 14, "mag_y": 15, "mag_z": 16,
            "batt": 21,
            "curr": 5
        }

            for key, idx in mapping.items():
                try:
                    val = float(parts[idx])
                    if key not in self.data:
                        continue
                    self.data[key]["x"].append(t)
                    self.data[key]["y"].append(val)
                except:
                    continue

        except Exception as e:
            print(f"Error parsing line: {line} ({e})")

    # ---------------- Speed control ----------------
    def speed_up(self):
        self.interval = max(5, self.interval // 2)
        self.timer.start(self.interval)

    
        
    def expand_graph(self, plot):
        if self.expanded:
            return

        frame, row, col = self.graph_info[plot]
        self.expanded = plot

        self.grid_layout.removeWidget(frame)
        frame.setParent(None)

        # hide grid
        self.grid_container.hide()


        # clear container
        while self.expand_container_layout.count():
            item = self.expand_container_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

        self.close_btn = QPushButton("✕ Close Graph")
        self.close_btn.clicked.connect(self.restore_graph)

        self.expand_container_layout.addWidget(self.close_btn)
        self.expand_container_layout.addWidget(frame)

        self.expand_container.show()

        
        
    def restore_graph(self): 
        plot = self.expanded 
        frame, row, col = self.graph_info[plot] 
        frame._orig_size_policy = frame.sizePolicy()
        frame._orig_min = frame.minimumSize() 
        frame._orig_max = frame.maximumSize() 
        self.expand_container_layout.removeWidget(frame) 
        frame.setParent(None) 
        if hasattr(frame, "_orig_size_policy"): 
            frame.setSizePolicy(frame._orig_size_policy) 
            if hasattr(frame, "_orig_min"): 
                frame.setMinimumSize(frame._orig_min) 
                if hasattr(frame, "_orig_max"): 
                    frame.setMaximumSize(frame._orig_max) 
                    self.grid_layout.addWidget(frame, row, col) 
                    for r in range(self.grid_layout.rowCount()): 
                        self.grid_layout.setRowStretch(r, 1) 
                        for c in range(self.grid_layout.columnCount()): 
                            self.grid_layout.setColumnStretch(c, 1)
                            #Force layout refresh 
                        self.grid_container.updateGeometry() 
                        self.grid_layout.invalidate() 
                        self.grid_container.update() 
                        self.expand_container.hide() 
                        self.grid_container.show() 
                        if self.close_btn: 
                            self.close_btn.deleteLater() 
                            self.close_btn = None 
                        self.expanded = None
        
    def refresh_graphs(self):
    
        self.paused = True

        # Clear all stored data
        for key in self.data:
            self.data[key]["x"].clear()
            self.data[key]["y"].clear()

        # Clear curves visually
        for curve in self.curves.values():
            curve.setData([], [])

        # Reset expansion if any graph is maximized
        if self.expanded:
            self.restore_graph()

        # Resume plotting
        self.paused = False

        print("Graphs refreshed")




# ---------------- Main ----------------
'''if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = GraphsWindow()
    window.show()
    sys.exit(app.exec_())'''
