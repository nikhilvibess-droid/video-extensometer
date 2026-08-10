from PyQt5 import QtWidgets, QtGui, QtCore
import cv2
import numpy as np
import time
from camera import FLIRCamera
from tracking import MarkerTracker
from ui.marker_selection import MarkerSelector
from database.report_manager import ReportManager
from database.sample_manager import SampleManager
from database.audit_manager import AuditManager
from ui.graph_widget import GraphContainer
from ui.custom_dialog import CustomDialog
from datetime import datetime


class MainWindow(QtWidgets.QWidget):
    graph_update_signal = QtCore.pyqtSignal(float, float, float, float, int, str)
    live_dashboard_signal = QtCore.pyqtSignal(dict)

    def __init__(
        self,
        user=None
    ):
        super().__init__()

        self.user = user

        self.report_manager = ReportManager()
        self.sample_manager = SampleManager()
        self.audit = AuditManager.get_instance()

        self.current_strain = 0.0

        self.current_distance_mm = 0.0

        self._selecting_markers = False
        self._test_completed = False
        self._frozen_test_seconds = None
        self._last_dashboard_emit = 0.0

        self.setWindowTitle(
            "Video Extensometer - FLIR Blackfly S"
        )

        self.resize(
            1600,
            900
        )

        # ==================
        # UI LAYOUT
        # ==================

        main_layout = QtWidgets.QVBoxLayout()
        main_layout.setContentsMargins(12, 12, 12, 12)
        main_layout.setSpacing(12)

        # Upper Area: Live Camera Feed (60% width) and Live Graphs (40% width)
        top_layout = QtWidgets.QHBoxLayout()
        top_layout.setSpacing(12)

        # Left Column: Video display
        self.video_label = QtWidgets.QLabel()
        self.video_label.setSizePolicy(
            QtWidgets.QSizePolicy.Expanding,
            QtWidgets.QSizePolicy.Expanding
        )
        self.video_label.setMinimumSize(480, 320)
        self.video_label.setStyleSheet(
            "border: 2px solid #334155; background-color: #0f172a; border-radius: 8px;"
        )
        self.video_label.setAlignment(QtCore.Qt.AlignCenter)
        top_layout.addWidget(self.video_label, 60)

        # Right Column: Live Graphs (stacked vertically)
        right_panel = QtWidgets.QWidget()
        right_panel_layout = QtWidgets.QVBoxLayout(right_panel)
        right_panel_layout.setContentsMargins(0, 0, 0, 0)
        right_panel_layout.setSpacing(10)

        self.strain_graph = GraphContainer(
            "Strain vs Time", "Strain (%)", "#fbbf24", is_strain_y=True, parent=self
        )
        self.dist_graph = GraphContainer(
            "Distance vs Time", "Distance (mm)", "#38bdf8", is_strain_y=False, parent=self
        )
        self.strain_graph.setMinimumHeight(220)
        self.dist_graph.setMinimumHeight(220)

        right_panel_layout.addWidget(self.strain_graph, 1)
        right_panel_layout.addWidget(self.dist_graph, 1)
        top_layout.addWidget(right_panel, 40)

        main_layout.addLayout(top_layout, 3)

        # Bottom Area: Controls & Live HUD Dashboard Panel
        bottom_panel = QtWidgets.QFrame()
        bottom_panel.setObjectName("bottomPanel")
        bottom_panel.setStyleSheet("""
            QFrame#bottomPanel {
                background-color: #1e293b;
                border: 1px solid #334155;
                border-radius: 8px;
            }
        """)
        bottom_layout = QtWidgets.QHBoxLayout(bottom_panel)
        bottom_layout.setContentsMargins(16, 12, 16, 12)
        bottom_layout.setSpacing(24)

        # Bottom Left: Controls Panel Card
        controls_card = QtWidgets.QFrame()
        controls_card.setObjectName("controlsCard")
        controls_card.setStyleSheet("""
            QFrame#controlsCard {
                background-color: #0f172a;
                border: 1px solid #334155;
                border-radius: 6px;
            }
        """)
        controls_layout = QtWidgets.QVBoxLayout(controls_card)
        controls_layout.setContentsMargins(12, 8, 12, 8)
        controls_layout.setSpacing(8)

        # Form layout for inputs
        inputs_layout = QtWidgets.QFormLayout()
        inputs_layout.setSpacing(6)

        self.material_input = QtWidgets.QLineEdit("Steel")
        self.material_input.setPlaceholderText("e.g. Steel, Aluminum")
        self.material_input.textChanged.connect(self.sync_material_value)

        self.sample_name_input = QtWidgets.QLineEdit()
        self.sample_name_input.setPlaceholderText("Specimen Name (e.g. Specimen A01)")

        self.test_name_input = QtWidgets.QLineEdit("Tensile Test")
        self.test_name_input.setPlaceholderText("e.g. Tensile Test")

        self.remarks_input = QtWidgets.QLineEdit()
        self.remarks_input.setPlaceholderText("Optional remarks")

        self.gauge_input = QtWidgets.QLineEdit()
        self.gauge_input.setPlaceholderText("Gauge Length (mm)")
        self.gauge_input.textChanged.connect(self.sync_gauge_value)

        def make_form_label(text):
            lbl = QtWidgets.QLabel(text)
            lbl.setStyleSheet("font-size: 11px; font-weight: bold; color: #94a3b8; text-transform: uppercase;")
            return lbl

        inputs_layout.addRow(make_form_label("Material *:"), self.material_input)
        inputs_layout.addRow(make_form_label("Sample Name *:"), self.sample_name_input)
        inputs_layout.addRow(make_form_label("Test Name:"), self.test_name_input)
        inputs_layout.addRow(make_form_label("Remarks:"), self.remarks_input)
        inputs_layout.addRow(make_form_label("Gauge Length (mm) *:"), self.gauge_input)
        controls_layout.addLayout(inputs_layout)

        # Buttons
        btn_layout = QtWidgets.QHBoxLayout()
        btn_layout.setSpacing(8)

        self.capture_btn = QtWidgets.QPushButton("Capture")
        self.restart_btn = QtWidgets.QPushButton("Restart Test")
        self.start_btn = QtWidgets.QPushButton("Start Tracking")
        self.stop_save_btn = QtWidgets.QPushButton("Stop & Save")

        # Generate custom scalable high-contrast vector icons
        self.capture_btn.setIcon(self.create_camera_icon())
        self.restart_btn.setIcon(self.create_refresh_icon())
        self.start_btn.setIcon(self.create_play_icon())
        self.stop_save_btn.setIcon(self.create_stop_icon())

        icon_size = QtCore.QSize(16, 16)
        self.capture_btn.setIconSize(icon_size)
        self.restart_btn.setIconSize(icon_size)
        self.start_btn.setIconSize(icon_size)
        self.stop_save_btn.setIconSize(icon_size)

        self.start_btn.setEnabled(False)
        self.stop_save_btn.setEnabled(False)

        # Style buttons with modern theme colors and professional hover animations
        self.capture_btn.setStyleSheet("""
            QPushButton {
                background-color: #3b82f6; color: white; border: none; border-radius: 6px; padding: 8px 16px; font-weight: bold; font-size: 12px; min-height: 28px;
            }
            QPushButton:hover { background-color: #2563eb; }
            QPushButton:pressed { background-color: #1d4ed8; }
            QPushButton:disabled { background-color: #1e293b; color: #64748b; border: 1px solid #334155; }
        """)
        self.restart_btn.setStyleSheet("""
            QPushButton {
                background-color: #f97316; color: white; border: none; border-radius: 6px; padding: 8px 16px; font-weight: bold; font-size: 12px; min-height: 28px;
            }
            QPushButton:hover { background-color: #ea580c; }
            QPushButton:pressed { background-color: #c2410c; }
            QPushButton:disabled { background-color: #1e293b; color: #64748b; border: 1px solid #334155; }
        """)
        self.start_btn.setStyleSheet("""
            QPushButton {
                background-color: #22c55e; color: white; border: none; border-radius: 6px; padding: 8px 16px; font-weight: bold; font-size: 12px; min-height: 28px;
            }
            QPushButton:hover { background-color: #16a34a; }
            QPushButton:pressed { background-color: #15803d; }
            QPushButton:disabled { background-color: #1e293b; color: #64748b; border: 1px solid #334155; }
        """)
        self.stop_save_btn.setStyleSheet("""
            QPushButton {
                background-color: #ef4444; color: white; border: none; border-radius: 6px; padding: 8px 16px; font-weight: bold; font-size: 12px; min-height: 28px;
            }
            QPushButton:hover { background-color: #dc2626; }
            QPushButton:pressed { background-color: #b91c1c; }
            QPushButton:disabled { background-color: #1e293b; color: #64748b; border: 1px solid #334155; }
        """)

        btn_layout.addWidget(self.capture_btn)
        btn_layout.addWidget(self.restart_btn)
        btn_layout.addWidget(self.start_btn)
        btn_layout.addWidget(self.stop_save_btn)
        controls_layout.addLayout(btn_layout)

        bottom_layout.addWidget(controls_card, 40)

        # Bottom Right: Info Grid Card (Live HUD Dashboard)
        info_card = QtWidgets.QFrame()
        info_card.setObjectName("infoCard")
        info_card.setStyleSheet("""
            QFrame#infoCard {
                background-color: #0f172a;
                border: 1px solid #334155;
                border-radius: 6px;
            }
        """)
        info_layout = QtWidgets.QVBoxLayout(info_card)
        info_layout.setContentsMargins(12, 8, 12, 8)
        info_layout.setSpacing(6)

        info_title = QtWidgets.QLabel("CURRENT TEST INFORMATION")
        info_title.setStyleSheet("font-size: 11px; font-weight: bold; color: #38bdf8; letter-spacing: 0.5px;")
        info_layout.addWidget(info_title)

        grid = QtWidgets.QGridLayout()
        grid.setSpacing(8)

        def add_hud_field(grid, label_text, row, col, val_color="#f8fafc", val_size="14px"):
            lbl = QtWidgets.QLabel(label_text)
            lbl.setStyleSheet("font-size: 10px; font-weight: bold; color: #64748b; text-transform: uppercase;")
            
            val = QtWidgets.QLabel("—")
            val.setStyleSheet(f"font-size: {val_size}; font-weight: bold; color: {val_color};")
            
            grid.addWidget(lbl, row * 2, col)
            grid.addWidget(val, row * 2 + 1, col)
            return val

        # Grid column layouts
        self.hud_material = add_hud_field(grid, "Material", 0, 0)
        self.hud_gauge = add_hud_field(grid, "Gauge Length", 0, 1)
        self.hud_user = add_hud_field(grid, "Current User", 0, 2)

        self.hud_init_dist = add_hud_field(grid, "Initial Distance", 1, 0, val_color="#38bdf8")
        self.hud_curr_dist = add_hud_field(grid, "Current Distance", 1, 1, val_color="#38bdf8")
        self.hud_extension = add_hud_field(grid, "Extension", 1, 2, val_color="#38bdf8")

        self.hud_strain = add_hud_field(grid, "Current Strain", 2, 0, val_color="#fbbf24", val_size="15px")
        self.hud_fps = add_hud_field(grid, "Camera FPS", 2, 1, val_color="#fbbf24")
        self.hud_status = add_hud_field(grid, "Tracking Status", 2, 2, val_color="#94a3b8")

        info_layout.addLayout(grid)
        bottom_layout.addWidget(info_card, 60)

        main_layout.addWidget(bottom_panel, 1)
        self.setLayout(main_layout)

        # ==================
        # CAMERA & TRACKER
        # ==================

        self.camera = None
        try:
            self.camera = FLIRCamera()
        except Exception as exc:
            print(f"[CAMERA] Initialization failed: {exc}")
            CustomDialog.warning(
                self,
                "Camera Unavailable",
                "FLIR camera could not be started.",
                description=(
                    "The application will open without live video. "
                    "Reconnect the camera, then restart the application."
                ),
            )
        self.tracker = MarkerTracker()
        self.selector = MarkerSelector()

        # ==================
        # STATE VARIABLES
        # ==================

        self.frozen_frame = None  # Captured and frozen frame
        self.old_gray = None      # Previous grayscale for tracking
        
        self.pixel_to_mm = None                 # Calibration factor
        self.initial_mm = None                  # Initial gauge length (mm)
        self.initial_pixel_distance = None      # Initial pixel distance
        self.current_pixel_distance = None      # Current pixel distance
        
        self.tracking = False                   # Tracking state
        self.markers_selected = False           # Markers selected state
        self.current_markers = None             # Current marker positions

        # FPS and Real-time Plotting state
        self.fps_last_time = None
        self.fps_smoothed = 0.0
        self.start_time = None
        self.time_data = []
        self.strain_data = []
        self.distance_data = []
        self.frame_count = 0

        # ==================
        # INITIALIZE HUD VALUES
        # ==================
        username = "Unknown"
        if self.user:
            if isinstance(self.user, dict):
                username = self.user.get("username", "Unknown")
            elif hasattr(self.user, "username"):
                username = self.user.username
        self.hud_user.setText(username)
        self.hud_material.setText(self.material_input.text())
        self.hud_status.setText("Idle")

        # ==================
        # TIMER
        # ==================

        self.timer = QtCore.QTimer()
        self.timer.timeout.connect(self.update_frame)
        self.timer.start(30)  # ~33 FPS

        # ==================
        # SIGNAL CONNECTIONS
        # ==================

        self.capture_btn.clicked.connect(self.capture_image)
        self.restart_btn.clicked.connect(self.restart_test)
        self.start_btn.clicked.connect(self.start_tracking)
        self.stop_save_btn.clicked.connect(self.stop_and_save)
        self.graph_update_signal.connect(self.handle_graph_update)

        self._emit_dashboard_update()

    # ==================
    # INPUT VALUE SYNC
    # ==================

    def sync_material_value(self, text):
        if text.strip():
            self.hud_material.setText(text.strip())
        else:
            self.hud_material.setText("—")

    def sync_gauge_value(self, text):
        if text.strip():
            self.hud_gauge.setText(f"{text.strip()} mm")
        else:
            self.hud_gauge.setText("—")

    # ==================
    # CAPTURE & SELECTION
    # ==================

    def capture_image(self):
        """
        Capture current frame, freeze it, and let user select markers with confirmation.
        """
        ok, frame = self.camera.read() if self.camera else (False, None)

        if not ok:
            CustomDialog.critical(
                self,
                "Camera Error",
                "Failed to capture frame from FLIR camera.",
                description="Ensure the FLIR Blackfly S camera is connected and powered on."
            )
            return

        self.frozen_frame = frame.copy()
        original_height, original_width = self.frozen_frame.shape[:2]

        display = cv2.resize(
            self.frozen_frame,
            None,
            fx=0.4,
            fy=0.4,
            interpolation=cv2.INTER_LINEAR
        )
        
        display_height, display_width = display.shape[:2]

        print(f"\n[CAPTURE] Original resolution: {original_width}x{original_height}")
        print(f"[CAPTURE] Display resolution: {display_width}x{display_height} (40% scale)")
        print(f"[CAPTURE] Starting professional marker selection...\n")

        self._selecting_markers = True
        self._emit_dashboard_update()

        try:
            points_scaled = self.selector.select(display)
        finally:
            self._selecting_markers = False

        if len(points_scaled) == 0:
            print("[MARKER SELECTION] User cancelled - returning to live feed")
            CustomDialog.information(
                self,
                "Selection Cancelled",
                "Marker selection cancelled.",
                description="Live feed will resume. Click 'Capture' again to try again."
            )
            self._emit_dashboard_update()
            return

        if len(points_scaled) != 2:
            CustomDialog.warning(
                self,
                "Selection Error",
                f"Invalid selection: {len(points_scaled)} markers selected.",
                description="Please select exactly 2 markers and press ENTER."
            )
            return

        scale_factor = 1.0 / 0.4
        
        points = [
            (
                int(round(p[0] * scale_factor)),
                int(round(p[1] * scale_factor))
            )
            for p in points_scaled
        ]

        print(f"[COORDINATE SCALING] Scale factor: {scale_factor}")
        print(f"[COORDINATE SCALING] P1 (40%): {points_scaled[0]} → P1 (original): {points[0]}")
        print(f"[COORDINATE SCALING] P2 (40%): {points_scaled[1]} → P2 (original): {points[1]}")

        for i, (x, y) in enumerate(points):
            if not (0 <= x < original_width and 0 <= y < original_height):
                CustomDialog.warning(
                    self,
                    "Out of Bounds",
                    f"Marker P{i+1} is outside image bounds after scaling.",
                    description=f"P{i+1}: ({x}, {y})\nImage size: {original_width}x{original_height}\n\nPlease re-select markers within the visible frame."
                )
                return

        self.tracker.initialize(points)
        self.current_markers = points

        self.initial_pixel_distance = self.tracker.distance(
            points[0],
            points[1]
        )

        self.markers_selected = True
        self.start_btn.setEnabled(True)

        # Update HUD to state visual details
        self.hud_init_dist.setText(f"{self.initial_pixel_distance:.1f} px")
        self.hud_status.setText("Ready")
        self.hud_status.setStyleSheet("font-size: 15px; font-weight: bold; color: #3b82f6;")

        print(f"\n[MARKER CONFIRMATION] ✓ Successfully confirmed 2 markers")
        print(f"[MARKER POSITIONS] P1 (original res): {points[0]}")
        print(f"[MARKER POSITIONS] P2 (original res): {points[1]}")
        print(f"[INITIAL CALIBRATION] Pixel distance: {self.initial_pixel_distance:.2f} px\n")

        CustomDialog.success(
            self,
            "Markers Successfully Confirmed",
            "Professional marker selection complete.",
            description=f"Marker P1: {points[0]}\nMarker P2: {points[1]}\nPixel Distance: {self.initial_pixel_distance:.2f} px\n\nNext Steps:\n1. Enter gauge length (mm)\n2. Click 'Start Tracking' to begin measurement"
        )
        self._emit_dashboard_update()

    # ==================
    # TRACKING CONTROL
    # ==================

    def start_tracking(self):
        """
        Start real-time marker tracking with strain calculation.
        """
        material = self.material_input.text().strip()
        sample_name = self.sample_name_input.text().strip()

        if not material:
            CustomDialog.warning(
                self,
                "Input Error",
                "Material is a required field."
            )
            return

        if not sample_name:
            CustomDialog.warning(
                self,
                "Input Error",
                "Sample Name is a required field."
            )
            return

        try:
            self.initial_mm = float(
                self.gauge_input.text()
            )

        except ValueError:
            CustomDialog.warning(
                self,
                "Input Error",
                "Gauge length must be a valid number (mm)"
            )
            return

        if self.initial_pixel_distance is None:
            CustomDialog.warning(
                self,
                "Error",
                "Please select markers first"
            )
            return

        if self.initial_mm <= 0:
            CustomDialog.warning(
                self,
                "Input Error",
                "Gauge length must be positive"
            )
            return

        self.pixel_to_mm = (
            self.initial_mm /
            self.initial_pixel_distance
        )

        # Reset plots and lists for a fresh test run
        self.time_data = []
        self.strain_data = []
        self.distance_data = []
        self.frame_count = 0
        self.strain_graph.clear()
        self.dist_graph.clear()
        self.start_time = time.time()
        self._test_completed = False
        self._frozen_test_seconds = None
        self.sample_manager.start_session()

        self.tracking = True
        self.capture_btn.setEnabled(False)
        self.start_btn.setEnabled(False)
        self.stop_save_btn.setEnabled(True)

        self.hud_init_dist.setText(f"{self.initial_mm:.2f} mm")
        self.hud_status.setText("Tracking")
        self.hud_status.setStyleSheet("font-size: 15px; font-weight: bold; color: #22c55e;")

        print(f"[TRACKING START] Calibration: {self.pixel_to_mm:.6f} mm/px")

        actor = ""
        actor_role = ""
        if self.user and isinstance(self.user, dict):
            actor = self.user.get("username", "")
            actor_role = self.user.get("role", "")
        self.audit.log_event(
            action="Tracking Started",
            username=actor,
            role=actor_role,
            result="Success",
        )
        self._emit_dashboard_update(force=True)

    def stop_and_save(self):
        """
        Stop real-time tracking, save the report details to the database,
        refresh dashboard/reports widgets, and prompt for immediate PDF generation.
        """
        print("[STOP & SAVE CALLED]")
        report_id = None
        username = "Unknown"
        gauge_length = 0.0
        initial_distance = 0.0
        final_distance = 0.0
        strain = 0.0
        material = ""
        sample_name = ""
        test_name = ""
        remarks = ""
        camera_res = "Unknown"
        software_version = "v2.5.0-industrial"
        operator = "Unknown"

        if self.tracking:
            if self.start_time is not None:
                self._frozen_test_seconds = time.time() - self.start_time
            try:
                if self.user:
                    if isinstance(self.user, dict):
                        username = self.user.get("username", "Unknown")
                    elif hasattr(self.user, "username"):
                        username = self.user.username

                gauge_length = self.initial_mm if self.initial_mm is not None else 0.0
                initial_distance = (self.initial_pixel_distance * self.pixel_to_mm) if (self.initial_pixel_distance is not None and self.pixel_to_mm is not None) else 0.0
                final_distance = self.current_distance_mm
                strain = self.current_strain

                material = self.material_input.text().strip()
                sample_name = self.sample_name_input.text().strip()
                test_name = self.test_name_input.text().strip() or "Tensile Test"
                remarks = self.remarks_input.text().strip()
                
                # Determine camera resolution
                if self.frozen_frame is not None:
                    h_f, w_f = self.frozen_frame.shape[:2]
                    camera_res = f"{w_f}x{h_f}"
                
                operator = username  # default to current logged-in user

                report_id = self.report_manager.save_report(
                    username=username,
                    gauge_length=gauge_length,
                    initial_distance=initial_distance,
                    final_distance=final_distance,
                    strain=strain,
                    material=material,
                    sample_name=sample_name,
                    test_name=test_name,
                    operator=operator,
                    remarks=remarks,
                    camera_resolution=camera_res,
                    software_version=software_version
                )
                if report_id:
                    self.sample_manager.flush_to_report(report_id)
            except Exception as e:
                self.sample_manager.discard_session()
                print(f"[ERROR] Failed to save report: {e}")
                CustomDialog.critical(self, "Save Error", "Failed to save test report.", details=str(e))
        else:
            self.sample_manager.discard_session()

        self.tracking = False
        self._test_completed = True
        self.capture_btn.setEnabled(True)
        self.restart_btn.setEnabled(True)
        self.start_btn.setEnabled(False) # Force re-capture for the next test
        self.stop_save_btn.setEnabled(False)

        # Clear marker select flags so user must select new markers for a new test
        self.markers_selected = False
        self.current_markers = None

        self.hud_status.setText("Stopped")
        self.hud_status.setStyleSheet("font-size: 15px; font-weight: bold; color: #ef4444;")

        print("[TRACKING STOP] Tracking halted and report successfully saved")

        actor = ""
        actor_role = ""
        if self.user and isinstance(self.user, dict):
            actor = self.user.get("username", "")
            actor_role = self.user.get("role", "")
        if report_id:
            self.audit.log_event(
                action="Report Generated",
                username=actor,
                role=actor_role,
                result="Success",
                details=f"Report ID {report_id}",
            )
        self.audit.log_event(
            action="Tracking Stopped",
            username=actor,
            role=actor_role,
            result="Success",
        )

        # Refresh Reports page & Dashboard statistics
        parent = self.window()
        if hasattr(parent, "update_stats"):
            parent.update_stats()
        if hasattr(parent, "reports_page") and parent.reports_page:
            if hasattr(parent.reports_page, "load_reports"):
                parent.reports_page.load_reports()

        # Prompt user to generate PDF if saved successfully
        if report_id:
            reply = CustomDialog.question(
                self,
                "Generate PDF Report",
                "Test completed and report saved successfully.",
                description="Would you like to export the PDF Metrology Analysis Report now?",
                buttons=["Yes", "No"],
                default_button="Yes"
            )
            if reply == CustomDialog.Yes:
                if hasattr(parent, "reports_page") and parent.reports_page:
                    report_data = {
                        'id': report_id,
                        'username': username,
                        'gauge_length': gauge_length,
                        'initial_distance': initial_distance,
                        'final_distance': final_distance,
                        'strain': strain,
                        'created_at': datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                        'material': material,
                        'sample_name': sample_name,
                        'test_name': test_name,
                        'operator': operator,
                        'remarks': remarks,
                        'camera_resolution': camera_res,
                        'software_version': software_version
                    }
                    parent.reports_page.render_report_pdf(report_data)

        self._emit_dashboard_update(force=True)

    def _format_test_time(self, seconds):
        total = max(0, int(seconds or 0))
        hours = total // 3600
        minutes = (total % 3600) // 60
        secs = total % 60
        return f"{hours:02d}:{minutes:02d}:{secs:02d}"

    def _get_test_time_seconds(self):
        if self.tracking and self.start_time is not None:
            return time.time() - self.start_time
        if self._frozen_test_seconds is not None:
            return self._frozen_test_seconds
        return 0.0

    def _get_extension_mm(self):
        if self.initial_mm is None:
            return 0.0
        return self.current_distance_mm - self.initial_mm

    def _resolve_tracking_status(self):
        if self._selecting_markers:
            return "Selecting Markers"
        if self.tracking:
            if self.hud_status.text() == "Tracking Loss":
                return "Error"
            return "Tracking"
        if self._test_completed:
            return "Completed"
        if self.markers_selected:
            return "Ready"
        if self.camera is not None:
            return "Ready"
        return "Idle"

    def _emit_dashboard_update(self, force=False):
        now = time.time()
        extension = self._get_extension_mm()
        if not force and self.tracking:
            ext_changed = abs(
                extension - getattr(self, "_last_ext_emit", -999.0)
            ) > 0.0005
            sec = int(self._get_test_time_seconds())
            sec_changed = sec != getattr(self, "_last_sec_emit", -1)
            if (
                not ext_changed
                and not sec_changed
                and (now - self._last_dashboard_emit) < 0.5
            ):
                return
            self._last_ext_emit = extension
            self._last_sec_emit = sec

        self._last_dashboard_emit = now
        self.live_dashboard_signal.emit({
            "test_time": self._format_test_time(self._get_test_time_seconds()),
            "extension_mm": extension,
            "status": self._resolve_tracking_status(),
        })

    # ==================
    # FRAME UPDATE (Main Loop)
    # ==================

    def update_frame(self):
        """
        Main real-time loop:
        1. Capture frame from FLIR camera
        2. If tracking: run optical flow on markers
        3. Draw overlays (markers, gauge line, strain)
        4. Display in PyQt5 label
        """
        # Smooth actual rolling FPS calculation
        now = time.time()
        if self.fps_last_time is not None:
            dt = now - self.fps_last_time
            if dt > 0:
                fps = 1.0 / dt
                self.fps_smoothed = 0.9 * self.fps_smoothed + 0.1 * fps
        else:
            self.fps_smoothed = 33.3
        self.fps_last_time = now
        self.hud_fps.setText(f"{self.fps_smoothed:.1f} FPS")

        ok, frame = self.camera.read() if self.camera else (False, None)

        if not ok:
            return

        if not frame.flags.writeable:
            frame = frame.copy()

        gray = cv2.cvtColor(
            frame,
            cv2.COLOR_BGR2GRAY
        )

        # ==================
        # TRACKING PIPELINE
        # ==================

        if self.tracking and self.old_gray is not None:
            points = self.tracker.track(
                self.old_gray,
                gray
            )

            if points is not None and len(points) == 2:
                pt1 = tuple(points[0].astype(int))
                pt2 = tuple(points[1].astype(int))

                self.current_markers = [pt1, pt2]

                pixel_dist = self.tracker.distance(
                    pt1,
                    pt2
                )

                mm_dist = pixel_dist * self.pixel_to_mm
                strain = (mm_dist - self.initial_mm) / self.initial_mm
                ext = mm_dist - self.initial_mm

                self.current_pixel_distance = pixel_dist
                self.current_distance_mm = mm_dist
                self.current_strain = strain

                # Update HUD variables
                self.hud_curr_dist.setText(f"{mm_dist:.2f} mm")
                self.hud_extension.setText(f"{ext:+.2f} mm")
                self.hud_strain.setText(f"{strain:+.6f}")
                self.hud_status.setText("Tracking")
                self.hud_status.setStyleSheet("font-size: 15px; font-weight: bold; color: #22c55e;")

                # Emit Graph Update Signal directly from tracking frame
                if self.start_time is not None:
                    self.frame_count += 1
                    timestamp = time.time()
                    elapsed = timestamp - self.start_time
                    self.graph_update_signal.emit(timestamp, elapsed, mm_dist, strain, self.frame_count, "Tracking")

                self._emit_dashboard_update()

                # Draw markers (green circles)
                cv2.circle(
                    frame,
                    pt1,
                    12,
                    (0, 255, 0),
                    -1
                )

                cv2.circle(
                    frame,
                    pt2,
                    12,
                    (0, 255, 0),
                    -1
                )

                # Draw gauge line (blue)
                cv2.line(
                    frame,
                    pt1,
                    pt2,
                    (255, 0, 0),
                    3
                )

                # Draw marker labels
                cv2.putText(
                    frame,
                    "M1",
                    (pt1[0] - 20, pt1[1] - 20),
                    cv2.FONT_HERSHEY_SIMPLEX,
                    0.8,
                    (0, 255, 0),
                    2
                )

                cv2.putText(
                    frame,
                    "M2",
                    (pt2[0] + 10, pt2[1] - 20),
                    cv2.FONT_HERSHEY_SIMPLEX,
                    0.8,
                    (0, 255, 0),
                    2
                )

            else:
                self.hud_strain.setText("+0.000000")
                self.hud_status.setText("Tracking Loss")
                self.hud_status.setStyleSheet(
                    "font-size: 15px; font-weight: bold; color: #ef4444;"
                )
                self._emit_dashboard_update(force=True)

        elif self.markers_selected and not self.tracking:
            if self.current_markers and len(self.current_markers) == 2:
                pt1, pt2 = self.current_markers

                cv2.circle(
                    frame,
                    pt1,
                    15,
                    (0, 255, 0),
                    -1
                )
                
                cv2.circle(
                    frame,
                    pt2,
                    15,
                    (0, 255, 0),
                    -1
                )

                cv2.circle(
                    frame,
                    pt1,
                    15,
                    (255, 255, 255),
                    2
                )
                
                cv2.circle(
                    frame,
                    pt2,
                    15,
                    (255, 255, 255),
                    2
                )

                cv2.line(
                    frame,
                    pt1,
                    pt2,
                    (255, 0, 0),
                    3
                )

                cv2.putText(
                    frame,
                    "P1",
                    (pt1[0] - 20, pt1[1] - 25),
                    cv2.FONT_HERSHEY_SIMPLEX,
                    1.0,
                    (0, 255, 0),
                    2
                )
                
                cv2.putText(
                    frame,
                    "P2",
                    (pt2[0] - 20, pt2[1] - 25),
                    cv2.FONT_HERSHEY_SIMPLEX,
                    1.0,
                    (0, 255, 0),
                    2
                )

                cv2.putText(
                    frame,
                    "READY - Enter Gauge Length to Start",
                    (20, 40),
                    cv2.FONT_HERSHEY_SIMPLEX,
                    0.9,
                    (0, 255, 0),
                    2
                )

        self.old_gray = gray.copy()

        # ==================
        # DISPLAY FRAME
        # ==================

        rgb = cv2.cvtColor(
            frame,
            cv2.COLOR_BGR2RGB
        )

        h, w, ch = rgb.shape

        img = QtGui.QImage(
            rgb.data,
            w,
            h,
            ch * w,
            QtGui.QImage.Format_RGB888
        )

        pixmap = QtGui.QPixmap.fromImage(img)

        self.video_label.setPixmap(
            pixmap.scaled(
                self.video_label.size(),
                QtCore.Qt.KeepAspectRatio,
                QtCore.Qt.SmoothTransformation
            )
        )

    def handle_graph_update(self, timestamp, elapsed_time, distance_mm, strain, frame_number, status):
        """
        Slot to handle live graph updates when a successful tracking frame is processed.
        Updates internal data buffers, appends to graphs, and logs debug output.
        """
        self.time_data.append(elapsed_time)
        self.strain_data.append(strain)
        self.distance_data.append(distance_mm)

        if len(self.time_data) > 10000:
            self.time_data = self.time_data[-10000:]
            self.strain_data = self.strain_data[-10000:]
            self.distance_data = self.distance_data[-10000:]

        self.strain_graph.append_point(elapsed_time, strain)
        self.strain_graph.update_live_metrics(elapsed=elapsed_time, fps=self.fps_smoothed, current_strain=strain, current_distance=distance_mm)

        self.dist_graph.append_point(elapsed_time, distance_mm)
        self.dist_graph.update_live_metrics(elapsed=elapsed_time, fps=self.fps_smoothed, current_strain=strain, current_distance=distance_mm)

        extension_mm = self._get_extension_mm()
        self.sample_manager.maybe_record(
            elapsed_time,
            distance_mm,
            extension_mm,
            strain,
        )

        # Print debug log in the requested format
        # [GRAPH UPDATE]
        # Frame: 125
        # Time: 4.18 s
        # Distance: 63.42 mm
        # Strain: 2.184 %
        strain_percent = strain * 100.0
        print(f"[GRAPH UPDATE]\nFrame: {frame_number}\nTime: {elapsed_time:.2f} s\nDistance: {distance_mm:.2f} mm\nStrain: {strain_percent:.3f} %")

    def restart_test(self):
        """
        Restart the current test after operator confirmation.
        Discards current measurements without saving any report.
        """
        result = CustomDialog.question(
            self,
            "Restart Current Test?",
            "Current measurements will be discarded.",
            description="No report will be saved.",
            buttons=["Restart", "Cancel"],
            default_button="Cancel"
        )
        
        if result == CustomDialog.Yes:
            print("[RESTART TEST] Operator confirmed restart. Clearing test state...")
            self.sample_manager.discard_session()
            # 1. Stop tracking immediately
            self.tracking = False
            
            # 2. Clear selected markers and calibration
            self.markers_selected = False
            self.current_markers = None
            self.frozen_frame = None
            self.old_gray = None
            self.pixel_to_mm = None
            self.initial_mm = None
            self.initial_pixel_distance = None
            self.current_pixel_distance = None
            self._test_completed = False
            self._frozen_test_seconds = None
            
            # 3. Clear strain and distance measurements
            self.current_strain = 0.0
            self.current_distance_mm = 0.0
            
            # 4. Clear graphs
            self.strain_graph.clear()
            self.dist_graph.clear()
            
            # 5. Clear timers & frame counter
            self.start_time = None
            self.time_data = []
            self.strain_data = []
            self.distance_data = []
            self.frame_count = 0
            
            # 6. Reset inputs to defaults/empty
            self.material_input.setText("Steel")
            self.sample_name_input.clear()
            self.test_name_input.setText("Tensile Test")
            self.remarks_input.clear()
            self.gauge_input.clear()
            
            # 7. Reset HUD labels
            self.hud_material.setText(self.material_input.text())
            self.hud_gauge.setText("—")
            self.hud_init_dist.setText("—")
            self.hud_curr_dist.setText("—")
            self.hud_extension.setText("—")
            self.hud_strain.setText("—")
            self.hud_status.setText("Idle")
            self.hud_status.setStyleSheet("font-size: 14px; font-weight: bold; color: #94a3b8;")
            
            # 8. Reset button states
            self.capture_btn.setEnabled(True)
            self.restart_btn.setEnabled(True)
            self.start_btn.setEnabled(False)
            self.stop_save_btn.setEnabled(False)
            
            self._emit_dashboard_update(force=True)
            print("[RESTART TEST] ✓ Test state successfully reset")

    def create_camera_icon(self):
        pixmap = QtGui.QPixmap(32, 32)
        pixmap.fill(QtCore.Qt.transparent)
        painter = QtGui.QPainter(pixmap)
        painter.setRenderHint(QtGui.QPainter.Antialiasing)
        painter.setPen(QtCore.Qt.NoPen)
        painter.setBrush(QtGui.QBrush(QtGui.QColor("white")))
        # Camera top bump
        painter.drawRoundedRect(QtCore.QRectF(10, 6, 12, 5), 2, 2)
        # Camera main body
        painter.drawRoundedRect(QtCore.QRectF(4, 11, 24, 15), 3, 3)
        # Punch a hole for the lens ring using DestinationOut
        painter.setCompositionMode(QtGui.QPainter.CompositionMode_DestinationOut)
        painter.drawEllipse(QtCore.QPointF(16, 18), 6, 6)
        # Restore composition mode to draw white lens center
        painter.setCompositionMode(QtGui.QPainter.CompositionMode_SourceOver)
        painter.setBrush(QtGui.QBrush(QtGui.QColor("white")))
        painter.drawEllipse(QtCore.QPointF(16, 18), 3, 3)
        painter.end()
        return QtGui.QIcon(pixmap)

    def create_refresh_icon(self):
        pixmap = QtGui.QPixmap(32, 32)
        pixmap.fill(QtCore.Qt.transparent)
        painter = QtGui.QPainter(pixmap)
        painter.setRenderHint(QtGui.QPainter.Antialiasing)
        
        pen = QtGui.QPen(QtGui.QColor("white"), 3)
        pen.setCapStyle(QtCore.Qt.RoundCap)
        painter.setPen(pen)
        
        # Circular reloading arrow path
        painter.drawArc(QtCore.QRect(6, 6, 20, 20), 45 * 16, 270 * 16)
        
        # Arrow head pointing clockwise reload
        painter.setPen(QtCore.Qt.NoPen)
        painter.setBrush(QtGui.QBrush(QtGui.QColor("white")))
        arrow = QtGui.QPolygonF([
            QtCore.QPointF(20, 4),
            QtCore.QPointF(27, 10),
            QtCore.QPointF(20, 16)
        ])
        painter.drawPolygon(arrow)
        painter.end()
        return QtGui.QIcon(pixmap)

    def create_play_icon(self):
        pixmap = QtGui.QPixmap(32, 32)
        pixmap.fill(QtCore.Qt.transparent)
        painter = QtGui.QPainter(pixmap)
        painter.setRenderHint(QtGui.QPainter.Antialiasing)
        painter.setPen(QtCore.Qt.NoPen)
        painter.setBrush(QtGui.QBrush(QtGui.QColor("white")))
        # Rightward triangle play arrow
        triangle = QtGui.QPolygonF([
            QtCore.QPointF(9, 6),
            QtCore.QPointF(25, 16),
            QtCore.QPointF(9, 26)
        ])
        painter.drawPolygon(triangle)
        painter.end()
        return QtGui.QIcon(pixmap)

    def create_stop_icon(self):
        pixmap = QtGui.QPixmap(32, 32)
        pixmap.fill(QtCore.Qt.transparent)
        painter = QtGui.QPainter(pixmap)
        painter.setRenderHint(QtGui.QPainter.Antialiasing)
        painter.setPen(QtCore.Qt.NoPen)
        painter.setBrush(QtGui.QBrush(QtGui.QColor("white")))
        # Stop block square
        painter.drawRoundedRect(QtCore.QRectF(7, 7, 18, 18), 3, 3)
        painter.end()
        return QtGui.QIcon(pixmap)

    # ==================
    # CLEANUP
    # ==================

    def closeEvent(self, event):
        """
        Proper cleanup on window close.
        """
        try:
            print("[SHUTDOWN] Initiating graceful shutdown...")
            
            if hasattr(self, 'timer') and self.timer:
                self.timer.stop()
                print("[SHUTDOWN] Timer stopped")
            
            if hasattr(self, 'tracking'):
                self.tracking = False
                print("[SHUTDOWN] Tracking stopped")
            
            if hasattr(self, 'camera') and self.camera:
                self.camera.release()
                print("[SHUTDOWN] Camera released")
            
            print("[SHUTDOWN] Application closed gracefully")
            event.accept()
            
        except Exception as e:
            print(f"[SHUTDOWN ERROR] Error during cleanup: {e}")
            import traceback
            traceback.print_exc()
            event.accept()