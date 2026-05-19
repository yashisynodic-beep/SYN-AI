import serial
import serial.tools.list_ports
from PyQt5.QtCore import QThread, pyqtSignal
import time


class SerialManager(QThread):
    data_received = pyqtSignal(str)
    connection_status = pyqtSignal(bool)
    status_text = pyqtSignal(str)


    def __init__(self, port_name=None, baud_rate=115200):
        super().__init__()
        self.serial = None
        self.port_name = port_name
        self.baud_rate = baud_rate
        self.running = False

    def connect_port(self, port_name=None, baud_rate=None):
        """Connect to selected serial port."""
        if port_name:
            self.port_name = port_name
        if baud_rate:
            self.baud_rate = baud_rate

        try:
             self.serial = serial.Serial(self.port_name, self.baud_rate, timeout=1)
             self.running = True
             self.connection_status.emit(True)
             self.status_text.emit(
                  f"✅ Connected to {self.port_name} @ {self.baud_rate}"
              )
             self.start()
             print(f"[SerialManager] ✅ Connected to {self.port_name} at {self.baud_rate}")
        except Exception as e:
             print(f"[SerialManager] ❌ Connection error: {e}")
             self.connection_status.emit(False)

    def disconnect_port(self):
        """Disconnect from serial port."""
        self.running = False
        if self.serial and self.serial.is_open:
            self.serial.close()
            self.connection_status.emit(False)
            self.status_text.emit("🔌 Disconnected")
            print("[SerialManager] 🔌 Disconnected")

    def stop(self):
        """Stop the serial manager thread and disconnect."""
        self.running = False
        if self.serial and self.serial.is_open:
            self.serial.close()
        self.connection_status.emit(False)


    def run(self):
   

        while self.running:

        # ---------- NOT CONNECTED ----------
            if not self.serial or not self.serial.is_open:
              time.sleep(1)
              continue

        # ---------- READ DATA ----------
            try:
                if self.serial.in_waiting > 0:
                   line = self.serial.readline().decode("utf-8", errors="ignore").strip()
                   if line:
                       self.data_received.emit(line)
                        
                else:
                     time.sleep(0.05)

        # ---------- DISCONNECT DETECTED ----------
            except Exception as e:
                self.status_text.emit(f"Disconnected: {e}")
                print("[SerialManager] Disconnected:", e)

                try:
                   self.serial.close()
                except:
                    pass

                self.serial = None
                time.sleep(1)

    def send_data(self, data_bytes):
        """Send bytes safely to serial port."""
        try:
            if self.serial and self.serial.is_open:
                self.serial.write(data_bytes)
                print(f"[SerialManager] 🚀 Sent: {data_bytes}")
            else:
                print("[SerialManager] ❌ Port not open, cannot send data")
        except Exception as e:
            print(f"[SerialManager] ⚠️ Send error: {e}")

    @staticmethod
    def list_ports():
        """Return list of available COM ports."""
        return [port.device for port in serial.tools.list_ports.comports()]
