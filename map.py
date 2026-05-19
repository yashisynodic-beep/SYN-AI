import os
import time
from PyQt5.QtWidgets import QApplication
import sys
import math
import time
from PyQt5 import QtWidgets, QtCore
from PyQt5.QtCore import pyqtSlot
from PyQt5.QtWebEngineWidgets import QWebEngineView
from serial_manager import SerialManager


# ================= HTML MAP =================
HTML_TEMPLATE = """
<!DOCTYPE html>
<html>
<head>
<meta charset="utf-8"/>
<title>Rocket GPS Tracker</title>
<meta name="viewport" content="width=device-width, initial-scale=1.0">

<link rel="stylesheet" href="https://unpkg.com/leaflet/dist/leaflet.css"/>
<script src="https://unpkg.com/leaflet/dist/leaflet.js"></script>

<style>
html, body, #map {
    height: 100%;
    margin: 0;
    padding: 0;
}
</style>
</head>

<body>
<div id="map"></div>

<script>
var map = L.map('map').setView([23.0225, 72.5714], 15);
// 🌍 world view

L.tileLayer(
  'https://services.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}',
  { maxZoom: 19 }
).addTo(map);
var marker = null;
var path = L.polyline([], { color: 'cyan', weight: 3 }).addTo(map);
var lastPoint = null;

function updatePosition(lat, lon) {

    var newPoint = L.latLng(lat, lon);

    if (!marker) {
        marker = L.marker(newPoint).addTo(map);
        map.setView(newPoint, 18);

        path.addLatLng(newPoint);
        lastPoint = newPoint;
        return;
    }

    marker.setLatLng(newPoint);

    // ---- FILTER SMALL GPS NOISE ----
    if (lastPoint) {
        var dist = newPoint.distanceTo(lastPoint);

        // Ignore jitter (< 2 meters)
        if (dist < 2) return;

        // Ignore unrealistic jumps (> 300 meters)
        if (dist > 300) return;
    }

    path.addLatLng(newPoint);
    lastPoint = newPoint;
}
</script>
</body>
</html>
"""



# ================= DISTANCE =================
def haversine(lat1, lon1, lat2, lon2):
    R = 6371000.0
    p1 = math.radians(lat1)
    p2 = math.radians(lat2)
    dp = math.radians(lat2 - lat1)
    dl = math.radians(lon2 - lon1)
    a = math.sin(dp/2)**2 + math.cos(p1)*math.cos(p2)*math.sin(dl/2)**2
    return 2 * R * math.atan2(math.sqrt(a), math.sqrt(1 - a))


# ================= MAP WINDOW =================
class MapWindow(QtWidgets.QWidget):
    def __init__(self, serial_manager=None):
        super().__init__()

        self.serial_manager = serial_manager or SerialManager()
        self.serial_manager.data_received.connect(self.on_telemetry_received)

        self.lat = None
        self.lon = None
        self.altitude = 0.0
        self.speed = 0.0

        self.last_lat = None
        self.last_lon = None
        self.last_time = None

        self.page_ready = False
        self.map_saved = False

        self.setWindowTitle("Satellite GPS Tracker")
        self.resize(1280, 750)

        layout = QtWidgets.QVBoxLayout(self)

        self.map_view = QWebEngineView()
        self.map_view.setHtml(HTML_TEMPLATE)
        self.map_view.loadFinished.connect(self.on_map_loaded)
        layout.addWidget(self.map_view)

        # ---------- INFO PANEL ----------
        self.info_frame = QtWidgets.QFrame(self)
        self.info_frame.setGeometry(20, 20, 260, 120)
        self.info_frame.raise_()

        info_layout = QtWidgets.QVBoxLayout(self.info_frame)
        info_layout.setContentsMargins(12, 12, 12, 12)

        self.speed_card = QtWidgets.QLabel("Speed: 0.00 m/s")
        self.altitude_card = QtWidgets.QLabel("Altitude: 0.0 m")

        info_layout.addWidget(self.speed_card)
        info_layout.addWidget(self.altitude_card)

        self.setStyleSheet("""
        QWidget { background: #1b1b2f; }
        QFrame {
            background: rgba(20,20,40,0.85);
            border-radius: 14px;
            border: 1px solid rgba(255,255,255,0.4);
        }
        QLabel {
            color: white;
            font: 12pt "Segoe UI";
        }
        """)

    # ================= MAP READY =================
    def on_map_loaded(self):
        self.page_ready = True
        

        self.map_view.page().runJavaScript("""
            if (typeof marker !== 'undefined' && marker !== null) {
                map.removeLayer(marker);
                marker = null;
            }
            path.setLatLngs([]);
            lastPoint = null;
            map.setView([23.0225, 72.5714], 15);
        """)

        #  IMPORTANT: restore last known position
        if self.lat is not None and self.lon is not None:
            self.map_view.page().runJavaScript(
                f"updatePosition({self.lat}, {self.lon});"
            )

        print("[MapWindow] Map reset & loaded")
    # ================= CSV TELEMETRY PARSER =================
    @pyqtSlot(str)
    def on_telemetry_received(self, line):
        try:
            parts = line.strip().split(",")

            if len(parts) < 9:
                return

            try:
                altitude = float(parts[2].strip())
                new_lat = float(parts[6].strip())
                new_lon = float(parts[7].strip())
            except ValueError:
                return

            # ignore invalid GPS
            if new_lat == 0.0 or new_lon == 0.0:
                return

            # ignore out-of-range values
            if not (-90 <= new_lat <= 90 and -180 <= new_lon <= 180):
                return

                        # Ignore invalid GPS
            if new_lat == 0.0 or new_lon == 0.0:
                return

            now = time.time()

            # -------- SPEED CALCULATION --------
            if self.last_lat is None:
                self.speed = 0.0
            else:
                dt = now - self.last_time
                if dt > 0:
                    dist = haversine(self.last_lat, self.last_lon, new_lat, new_lon)

                    # Ignore unrealistic jumps (> 200 m in 1s)
                    if dist < 200:
                        self.speed = dist / dt

            self.last_lat = new_lat
            self.last_lon = new_lon
            self.last_time = now

            self.altitude = altitude
            self.lat = new_lat
            self.lon = new_lon

            # -------- UI UPDATE --------
            self.speed_card.setText(f"Speed: {self.speed:.2f} m/s")
            self.altitude_card.setText(f"Altitude: {self.altitude:.1f} m")

            # -------- MAP UPDATE --------
            if self.page_ready:
                self.map_view.page().runJavaScript(
                    f"updatePosition({self.lat}, {self.lon});"
                )
                
            # -------- AUTO SAVE AFTER MAP UPDATE --------
            if self.page_ready and not self.map_saved:
                self.map_saved = True
                QtCore.QTimer.singleShot(1500, self.save_map_screenshot)

        except Exception as e:
            print("[MapWindow] Parse error:", e)
            print("Raw line:", line)
            
    def save_map_screenshot(self):
        screen = QApplication.primaryScreen()
        pixmap = screen.grabWindow(self.map_view.winId())

        download_path = os.path.join(os.path.expanduser("~"), "Downloads")
        filename = f"map_capture_{int(time.time())}.png"
        filepath = os.path.join(download_path, filename)

        pixmap.save(filepath, "png")

        print(f"[Map] Screenshot saved: {filepath}")
# ================= MAIN =================
'''if __name__ == "__main__":
    app = QtWidgets.QApplication(sys.argv)
    window = MapWindow()
    window.show()
    sys.exit(app.exec_())'''                