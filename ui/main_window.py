from PyQt5 import QtWidgets, QtGui, QtCore
import cv2
import numpy as np

from camera import FLIRCamera
from tracking import MarkerTracker
from ui.marker_selection import MarkerSelector
from database.report_manager import ReportManager


class MainWindow(QtWidgets.QWidget):

    def __init__(
        self,
        user=None
    ):
        super().__init__()

        self.user = user

        self.report_manager = ReportManager()

        self.current_strain = 0.0

        self.current_distance_mm = 0.0

        self.setWindowTitle(
            "Video Extensometer - FLIR Blackfly S"
        )

        self.resize(
            1400,
            900
        )

        # ==================
        # UI LAYOUT
        # ==================

        layout = QtWidgets.QVBoxLayout()

        # Video display
        self.video_label = QtWidgets.QLabel()
        self.video_label.setMinimumSize(1200, 800)
        self.video_label.setStyleSheet(
            "border: 2px solid #cccccc; background-color: #000000;"
        )
        layout.addWidget(self.video_label)

        # Control panel
        control_layout = QtWidgets.QHBoxLayout()

        # Gauge length input
        self.gauge_input = QtWidgets.QLineEdit()
        self.gauge_input.setPlaceholderText("Gauge Length (mm)")
        self.gauge_input.setMaximumWidth(200)
        control_layout.addWidget(QtWidgets.QLabel("Gauge Length (mm):"))
        control_layout.addWidget(self.gauge_input)

        # Capture button
        self.capture_btn = QtWidgets.QPushButton("Capture & Select Markers")
        self.capture_btn.setMaximumWidth(200)
        control_layout.addWidget(self.capture_btn)

        # Start tracking button
        self.start_btn = QtWidgets.QPushButton("Start Tracking")
        self.start_btn.setMaximumWidth(150)
        self.start_btn.setEnabled(False)
        control_layout.addWidget(self.start_btn)

        # Stop tracking button
        self.stop_btn = QtWidgets.QPushButton("Stop Tracking")
        self.stop_btn.setMaximumWidth(150)
        self.stop_btn.setEnabled(False)
        control_layout.addWidget(self.stop_btn)

        layout.addLayout(control_layout)

        # Results display — three high-contrast HUD labels
        results_panel = QtWidgets.QFrame()
        results_panel.setStyleSheet(
            "background-color: #0f172a;"
            "border: 1px solid #334155;"
            "border-radius: 6px;"
            "padding: 6px;"
        )
        results_layout = QtWidgets.QHBoxLayout(results_panel)
        results_layout.setContentsMargins(16, 10, 16, 10)
        results_layout.setSpacing(40)

        self.strain_label = QtWidgets.QLabel("Strain\n+0.000000")
        self.strain_label.setStyleSheet(
            "font-size: 15px; font-weight: bold; color: #fbbf24;"
            "letter-spacing: 0.5px;"
        )
        self.strain_label.setAlignment(QtCore.Qt.AlignCenter)

        self.dist_label = QtWidgets.QLabel("Distance\n0.00 mm")
        self.dist_label.setStyleSheet(
            "font-size: 15px; font-weight: bold; color: #38bdf8;"
            "letter-spacing: 0.5px;"
        )
        self.dist_label.setAlignment(QtCore.Qt.AlignCenter)

        self.status_label = QtWidgets.QLabel("Status\nIdle")
        self.status_label.setStyleSheet(
            "font-size: 15px; font-weight: bold; color: #94a3b8;"
            "letter-spacing: 0.5px;"
        )
        self.status_label.setAlignment(QtCore.Qt.AlignCenter)

        results_layout.addWidget(self.strain_label)
        results_layout.addWidget(self.dist_label)
        results_layout.addWidget(self.status_label)

        layout.addWidget(results_panel)

        self.setLayout(layout)

        # ==================
        # CAMERA & TRACKER
        # ==================

        self.camera = FLIRCamera()
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
        self.start_btn.clicked.connect(self.start_tracking)
        self.stop_btn.clicked.connect(self.stop_tracking)

    # ==================
    # CAPTURE & SELECTION
    # ==================

    def capture_image(self):
        """
        Capture current frame, freeze it, and let user select markers with confirmation.
        
        PROFESSIONAL WORKFLOW:
        1. Capture frame from camera
        2. Resize to 40% for comfortable marker selection window
        3. Display marker selection interface with real-time visual feedback
        4. User clicks P1 location → Green circle appears (P1)
        5. User clicks P2 location → Green circle appears (P2)
        6. Blue gauge line drawn between markers
        7. Pixel distance and coordinates displayed
        8. User presses ENTER to confirm (or ESC to re-select)
        9. Points scaled back to original camera resolution
        10. Tracking initialization with confirmed markers
        
        Returns: None (updates self.current_markers and self.markers_selected)
        """
        ok, frame = self.camera.read()

        if not ok:
            QtWidgets.QMessageBox.warning(
                self,
                "Camera Error",
                "Failed to capture frame from FLIR camera"
            )
            return

        # Store frozen frame (already writable from camera.read())
        self.frozen_frame = frame.copy()
        
        # Get original resolution for coordinate scaling
        original_height, original_width = self.frozen_frame.shape[:2]

        # Resize for comfortable marker selection window (40% scale)
        # This allows easier clicking while reducing window size
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

        # Display marker selection interface
        # User clicks to place P1 and P2, sees real-time visual feedback
        points_scaled = self.selector.select(display)

        # Handle cancellation (empty list returned when user presses ESC)
        if len(points_scaled) == 0:
            print("[MARKER SELECTION] User cancelled - returning to live feed")
            QtWidgets.QMessageBox.information(
                self,
                "Selection Cancelled",
                "Marker selection cancelled.\n\n"
                "Live feed will resume.\n"
                "Click 'Capture & Select Markers' again to try again."
            )
            return

        # Verify we have exactly 2 points
        if len(points_scaled) != 2:
            QtWidgets.QMessageBox.warning(
                self,
                "Selection Error",
                f"Invalid selection: {len(points_scaled)} markers selected.\n\n"
                "Please select exactly 2 markers and press ENTER."
            )
            return

        # ===== CRITICAL: Scale points back to original camera resolution =====
        # Points were clicked on 40% scaled image
        # Must scale back by 1/0.4 = 2.5 to match original frame resolution
        scale_factor = 1.0 / 0.4  # = 2.5
        
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

        # Verify coordinates are within image bounds
        for i, (x, y) in enumerate(points):
            if not (0 <= x < original_width and 0 <= y < original_height):
                QtWidgets.QMessageBox.warning(
                    self,
                    "Out of Bounds",
                    f"Marker P{i+1} is outside image bounds after scaling.\n\n"
                    f"P{i+1}: ({x}, {y})\n"
                    f"Image size: {original_width}x{original_height}\n\n"
                    "Please re-select markers within the visible frame."
                )
                return

        # Initialize tracker with confirmed marker points (at original resolution)
        self.tracker.initialize(points)
        self.current_markers = points

        # Calculate initial pixel distance for calibration
        # This distance in pixels will be converted to mm based on gauge length
        self.initial_pixel_distance = self.tracker.distance(
            points[0],
            points[1]
        )

        # Mark as ready for tracking
        self.markers_selected = True

        # Enable start button for tracking
        self.start_btn.setEnabled(True)

        # Console output for verification
        print(f"\n[MARKER CONFIRMATION] ✓ Successfully confirmed 2 markers")
        print(f"[MARKER POSITIONS] P1 (original res): {points[0]}")
        print(f"[MARKER POSITIONS] P2 (original res): {points[1]}")
        print(f"[INITIAL CALIBRATION] Pixel distance: {self.initial_pixel_distance:.2f} px\n")

        # Show confirmation dialog with exact coordinates and distance
        QtWidgets.QMessageBox.information(
            self,
            "✓ Markers Successfully Confirmed",
            f"Professional marker selection complete.\n\n"
            f"━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
            f"Marker P1 (gauge point 1): {points[0]}\n"
            f"Marker P2 (gauge point 2): {points[1]}\n"
            f"━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
            f"Pixel Distance: {self.initial_pixel_distance:.2f} px\n"
            f"━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n\n"
            f"Next Steps:\n"
            f"1. Enter gauge length (mm) in the input field\n"
            f"2. Click 'Start Tracking' to begin measurement\n"
            f"3. System will calculate strain in real-time"
        )

    # ==================
    # TRACKING CONTROL
    # ==================

    def start_tracking(self):
        """
        Start real-time marker tracking with strain calculation.
        """
        try:
            self.initial_mm = float(
                self.gauge_input.text()
            )

        except ValueError:
            QtWidgets.QMessageBox.warning(
                self,
                "Input Error",
                "Gauge length must be a valid number (mm)"
            )
            return

        if self.initial_pixel_distance is None:
            QtWidgets.QMessageBox.warning(
                self,
                "Error",
                "Please select markers first"
            )
            return

        if self.initial_mm <= 0:
            QtWidgets.QMessageBox.warning(
                self,
                "Input Error",
                "Gauge length must be positive"
            )
            return

        # Calculate calibration factor
        self.pixel_to_mm = (
            self.initial_mm /
            self.initial_pixel_distance
        )

        self.tracking = True
        self.capture_btn.setEnabled(False)
        self.start_btn.setEnabled(False)
        self.stop_btn.setEnabled(True)

        print(f"[TRACKING START] Calibration: {self.pixel_to_mm:.6f} mm/px")

    def stop_tracking(self):
        """
        Stop real-time tracking.
        """
        print("[STOP TRACKING CALLED]")
        if self.tracking:
            try:
                username = "Unknown"
                if self.user:
                    if isinstance(self.user, dict):
                        username = self.user.get("username", "Unknown")
                    elif hasattr(self.user, "username"):
                        username = self.user.username

                gauge_length = self.initial_mm if self.initial_mm is not None else 0.0
                initial_distance = (self.initial_pixel_distance * self.pixel_to_mm) if (self.initial_pixel_distance is not None and self.pixel_to_mm is not None) else 0.0
                final_distance = self.current_distance_mm
                strain = self.current_strain

                self.report_manager.save_report(
                    username=username,
                    gauge_length=gauge_length,
                    initial_distance=initial_distance,
                    final_distance=final_distance,
                    strain=strain
                )
            except Exception as e:
                print(f"[ERROR] Failed to automatically save report: {e}")

        self.tracking = False

        self.capture_btn.setEnabled(True)

        self.start_btn.setEnabled(
            self.markers_selected
        )

        self.stop_btn.setEnabled(False)

        print(
            "[TRACKING STOP] Tracking halted by user"
        )

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
        
        CRITICAL: Frame from camera.read() is already writable (copied in camera.py)
        """
        ok, frame = self.camera.read()

        if not ok:
            return

        # Ensure frame is writable (defensive programming)
        # This should always pass due to copy in camera.read(), but safety first
        if not frame.flags.writeable:
            frame = frame.copy()

        # Convert to grayscale for tracking
        gray = cv2.cvtColor(
            frame,
            cv2.COLOR_BGR2GRAY
        )

        # ==================
        # TRACKING PIPELINE
        # ==================

        if self.tracking and self.old_gray is not None:
            # Run optical flow tracking
            points = self.tracker.track(
                self.old_gray,
                gray
            )

            if points is not None and len(points) == 2:
                pt1 = tuple(points[0].astype(int))
                pt2 = tuple(points[1].astype(int))

                # Update marker positions
                self.current_markers = [pt1, pt2]

                # Calculate distances and strain
                pixel_dist = self.tracker.distance(
                    pt1,
                    pt2
                )

                mm_dist = pixel_dist * self.pixel_to_mm

                strain = (mm_dist - self.initial_mm) / self.initial_mm

                self.current_pixel_distance = pixel_dist

                self.current_distance_mm = mm_dist

                self.current_strain = strain

                # Update results display
                self.strain_label.setText(f"Strain\n{strain:+.6f}")
                self.dist_label.setText(f"Distance\n{mm_dist:.2f} mm")
                self.status_label.setText("Status\nTracking")
                self.status_label.setStyleSheet(
                    "font-size: 15px; font-weight: bold; color: #22c55e;"
                    "letter-spacing: 0.5px;"
                )

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
                self.strain_label.setText("Strain\n+0.000000")
                self.status_label.setText("Status\nTracking Loss")
                self.status_label.setStyleSheet(
                    "font-size: 15px; font-weight: bold; color: #ef4444;"
                    "letter-spacing: 0.5px;"
                )

        elif self.markers_selected and not self.tracking:
            # Display selected markers visually (waiting for tracking to start)
            if self.current_markers and len(self.current_markers) == 2:
                pt1, pt2 = self.current_markers

                # Draw filled green circles for markers
                cv2.circle(
                    frame,
                    pt1,
                    15,
                    (0, 255, 0),  # Green
                    -1
                )
                
                cv2.circle(
                    frame,
                    pt2,
                    15,
                    (0, 255, 0),  # Green
                    -1
                )

                # Draw white contours for emphasis
                cv2.circle(
                    frame,
                    pt1,
                    15,
                    (255, 255, 255),  # White border
                    2
                )
                
                cv2.circle(
                    frame,
                    pt2,
                    15,
                    (255, 255, 255),  # White border
                    2
                )

                # Draw gauge line
                cv2.line(
                    frame,
                    pt1,
                    pt2,
                    (255, 0, 0),  # Blue
                    3
                )

                # Draw marker labels
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

                # Display ready status
                cv2.putText(
                    frame,
                    "READY - Enter Gauge Length to Start",
                    (20, 40),
                    cv2.FONT_HERSHEY_SIMPLEX,
                    0.9,
                    (0, 255, 0),
                    2
                )

        # Store current gray frame for next iteration
        self.old_gray = gray.copy()

        # ==================
        # DISPLAY FRAME
        # ==================

        # Convert BGR to RGB for PyQt5
        rgb = cv2.cvtColor(
            frame,
            cv2.COLOR_BGR2RGB
        )

        h, w, ch = rgb.shape

        # Create QImage with proper byte order
        # CRITICAL: Pass rgb.data directly (it's already writable)
        img = QtGui.QImage(
            rgb.data,
            w,
            h,
            ch * w,
            QtGui.QImage.Format_RGB888
        )

        # Convert to QPixmap and scale to label size
        pixmap = QtGui.QPixmap.fromImage(img)

        self.video_label.setPixmap(
            pixmap.scaled(
                self.video_label.size(),
                QtCore.Qt.KeepAspectRatio,
                QtCore.Qt.SmoothTransformation
            )
        )

    # ==================
    # CLEANUP
    # ==================

    def closeEvent(self, event):
        """
        Proper cleanup on window close:
        1. Stop timer
        2. Stop tracking
        3. Stop camera acquisition
        4. Release all resources
        
        CRITICAL: Ensures camera references are properly cleared
        to prevent "reference still held" exceptions.
        """
        try:
            print("[SHUTDOWN] Initiating graceful shutdown...")
            
            # Stop the main timer
            if hasattr(self, 'timer') and self.timer:
                self.timer.stop()
                print("[SHUTDOWN] Timer stopped")
            
            # Stop tracking
            if hasattr(self, 'tracking'):
                self.tracking = False
                print("[SHUTDOWN] Tracking stopped")
            
            # Release camera resources
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