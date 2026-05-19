import os
os.environ["QT_OPENGL"] = "software"
from PyQt5 import QtWidgets, QtCore
import pyvista as pv
from pyvistaqt import QtInteractor
import os
import sys

# =====================================================
# RESOURCE PATH FIX (FOR PYINSTALLER)
# =====================================================
def resource_path(relative_path):
    """
    Get absolute path to resource,
    works for both development and PyInstaller EXE
    """
    if hasattr(sys, "_MEIPASS"):
        # Running from EXE
        base_path = sys._MEIPASS
    else:
        # Running from normal python: use script directory, not current working dir
        base_path = os.path.dirname(os.path.abspath(__file__))
    return os.path.join(base_path, relative_path)


class STLView(QtWidgets.QFrame):
    def __init__(self, stl_path=None, serial_manager=None, parent=None):
        super().__init__(parent)

        self.setMinimumSize(200, 200)
        self.setSizePolicy(
            QtWidgets.QSizePolicy.Expanding,
            QtWidgets.QSizePolicy.Expanding
        )

        self.setFrameShape(QtWidgets.QFrame.NoFrame)

        # ---------- rotation values ----------
        self.manual_roll = 0.0
        self.manual_pitch = 0.0
        self.manual_yaw = 0.0

        self.telemetry_roll = 0.0
        self.telemetry_pitch = 0.0
        self.telemetry_yaw = 0.0
        
        # ===== AUTO RESET TIMER =====
        self.reset_timer = QtCore.QTimer(self)
        self.reset_timer.setInterval(20000)  # 20 sec
        self.reset_timer.setSingleShot(True)
        self.reset_timer.timeout.connect(self.reset_view)

        self.last_mouse_pos = None
        self.setMouseTracking(True)

        # ---------- Layout ----------
        layout = QtWidgets.QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)

        # ---------- 3D Plotter ----------
        self.plotter = QtInteractor(self)
        layout.addWidget(self.plotter.interactor)

        self.plotter.enable_anti_aliasing()
        self.plotter.renderer.SetUseFXAA(True)
        self.plotter.set_background("#061A357F")

        # ---------- GRID INIT ----------
        self.grid_actor = None
        self.update_grid_size()

        # ---------- LOAD ROCKET ----------
        if stl_path is None:
            stl_path = resource_path("gcs_rocket.STL")
        elif not os.path.isabs(stl_path):
            # allow relative path from code location
            stl_path = resource_path(stl_path)

        print(f"STL Path resolved to: {stl_path}")
        print(f"STL File exists: {os.path.exists(stl_path)}")

        if not os.path.exists(stl_path):
            QtWidgets.QMessageBox.critical(self, "Error", f"STL not found:\n{stl_path}")
            missing_label = QtWidgets.QLabel(f"STL not found:\n{stl_path}", self)
            missing_label.setAlignment(QtCore.Qt.AlignCenter)
            layout.addWidget(missing_label)
            return

            print("Loading STL mesh...")
            self.load_new_stl(stl_path)
            print("STL loaded successfully")

        # ---------- Camera ----------
        self.plotter.add_axes()
        
        self.plotter.view_isometric()
        self.plotter.reset_camera()
        self.plotter.render()
        print("STL View initialized successfully!")

    # =====================================================
    # GRID CREATION
    # =====================================================
    def create_grid(self, size, divisions):

        grid = pv.Plane(
            center=(0, 0, 0),
            direction=(0, 0, 1),
            i_size=size,
            j_size=size,
            i_resolution=divisions,
            j_resolution=divisions
        )

        if self.grid_actor:
            self.plotter.remove_actor(self.grid_actor)

        self.grid_actor = self.plotter.add_mesh(
            grid,
            style="wireframe",
            color="#888888",
            line_width=1
        )

        self.grid_actor.SetPickable(False)

    # =====================================================
    # AUTO GRID RESIZE
    # =====================================================
    def update_grid_size(self):
   
        w = max(self.width(), 800)
        h = max(self.height(), 800)
        size = max(w, h) * 2
        divisions = max(40, int(size / 30))   # slightly denser grid
        self.create_grid(size, divisions)

    def resizeEvent(self, event):
        super().resizeEvent(event)

        self.update_grid_size()

        if hasattr(self, "plotter"):
            QtCore.QTimer.singleShot(50, self.safe_render)
    # =====================================================
    # CAMERA CONTROLS
    # =====================================================
    def reset_view(self):
        try:
            self.plotter.view_isometric()
            self.plotter.reset_camera()
            self.plotter.disable_parallel_projection()  # optional
            self.plotter.render()
            print("Auto reset done")
        except Exception as e:
            print("Reset error:", e)

    def set_top_view(self):
        self.plotter.view_xy()

    def set_side_view(self):
        self.plotter.view_xz()

    # =====================================================
    # MOUSE ROTATION
    # =====================================================
    def mousePressEvent(self, event):
        self.reset_timer.start()   

        if event.buttons() & QtCore.Qt.LeftButton:          # need to modify
            self.last_mouse_pos = event.pos()

    def mouseMoveEvent(self, event):
        self.reset_timer.start() 
        if self.last_mouse_pos is None:
            return

        dx = event.x() - self.last_mouse_pos.x()
        dy = event.y() - self.last_mouse_pos.y()

        sensitivity = 0.4
        self.manual_yaw += dx * sensitivity
        self.manual_pitch += dy * sensitivity

        self.last_mouse_pos = event.pos()
        self.update_combined_rotation()

    def mouseReleaseEvent(self, event):
        self.last_mouse_pos = None
        # -------- TRAJECTORY --------
        self.position = (0, 0, 0)
        self.path_points = []
        self.path_actor = None

    # =====================================================
    # ROTATION SYSTEM
    # =====================================================
    def set_attitude_absolute(self, roll, pitch, yaw):
        self.telemetry_roll = roll
        self.telemetry_pitch = pitch
        self.telemetry_yaw = yaw
        self.update_combined_rotation()

    def update_combined_rotation(self):
        roll = self.telemetry_roll + self.manual_roll
        pitch = self.telemetry_pitch + self.manual_pitch
        yaw = self.telemetry_yaw + self.manual_yaw
        self.set_rotation(roll, pitch, yaw)

    
    def set_rotation(self, roll, pitch, yaw):
        if not hasattr(self, "stl_actor"):
            return

        self.stl_actor.SetOrientation(
            pitch,
            roll,
            yaw
        )

        self.plotter.render()

        
        
    def move_object(self, x=0, y=0, z=0):
        if hasattr(self, "stl_actor"):
            self.stl_actor.SetPosition(x, y, z)

        self.plotter.render()
    
    def update_orientation(self, data):
        try:
            self.telemetry_roll = -float(data.get("roll", 0))
            self.telemetry_pitch = float(data.get("pitch", 0))
            self.telemetry_yaw = -float(data.get("yaw", 0))
            self.update_combined_rotation()
        except Exception as e:
            print("STL update error:", e)

    def showEvent(self, event):
        super().showEvent(event)

        QtCore.QTimer.singleShot(100, self.delayed_show_render)

    def delayed_show_render(self):
        try:
            self.plotter.reset_camera()
            self.plotter.render()
        except Exception as e:
            print("STL show event error:", e)
                
              
    def update_position(self, pos):
        self.position = pos
        self.path_points.append(pos)

        # limit memory
        if len(self.path_points) > 1000:
            self.path_points.pop(0)

        # move rocket
        self.move_object(*pos)

        # update trajectory line
        try:
            import numpy as np

            if len(self.path_points) > 1:
                points = np.array(self.path_points)

                if self.path_actor:
                
                   self.plotter.remove_actor(self.path_actor, reset_camera=False)

                self.path_actor = self.plotter.add_lines(
                    points,
                    color="red",
                    width=3
                )

        except Exception as e:
            print("Trajectory error:", e)
            
            
    def wheelEvent(self, event):
        self.reset_timer.start()  
        super().wheelEvent(event)
        
    def safe_render(self):
        try:
            self.plotter.render()
        except Exception as e:
            print("Render error:", e)
            
    def open_stl_file(self):
        file_path, _ = QtWidgets.QFileDialog.getOpenFileName(
            self,
            "Select STL File",
            "",
            "STL Files (*.stl)"
        )

        if file_path:

            # remove old STL
            if hasattr(self, "stl_actor"):
                self.plotter.remove_actor(
                    self.stl_actor,
                    reset_camera=False
                )

            self.load_new_stl(file_path)
            
    def load_new_stl(self, stl_path):

        try:
            # remove previous STL
            if hasattr(self, "stl_actor"):
                self.plotter.remove_actor(
                    self.stl_actor,
                    reset_camera=False
                )

            # ==========================
            # READ STL
            # ==========================
            self.stl_mesh = pv.read(stl_path)

            bounds = self.stl_mesh.bounds

            x_size = bounds[1] - bounds[0]
            y_size = bounds[3] - bounds[2]
            z_size = bounds[5] - bounds[4]

            # ==========================
            # CENTER STL
            # ==========================
            x_center = (bounds[0] + bounds[1]) / 2
            y_center = (bounds[2] + bounds[3]) / 2
            z_center = (bounds[4] + bounds[5]) / 2

            self.stl_mesh.translate(
                (-x_center, -y_center, -z_center),
                inplace=True
            )

            # ==========================
            # AUTO SCALE
            # ==========================
            largest_dimension = max(
                x_size,
                y_size,
                z_size
            )

            # IMPORTANT: Bigger size
            target_size = 400

            scale_factor = (
                target_size /
                largest_dimension
            )

            self.stl_mesh.scale(
                [scale_factor] * 3,
                inplace=True
            )

            # ==========================
            # ADD STL
            # ==========================
            self.stl_actor = self.plotter.add_mesh(
                self.stl_mesh,
                color="#E8E8E8",
                smooth_shading=True
            )

            self.stl_actor.SetPosition(
                0, 0, 0
            )

            self.plotter.reset_camera()
            self.plotter.render()

            print("Loaded:", stl_path)

        except Exception as e:
            print("STL Load Error:", e)