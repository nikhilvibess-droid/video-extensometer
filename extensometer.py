import os
import sys
import cv2
import numpy as np
from math import sqrt

# =========================
# FLIR SPINNAKER SETUP
# =========================
dll_path = r"C:\Program Files\Teledyne\Spinnaker\bin64"
legacy_path = r"C:\Program Files\Point Grey Research\Spinnaker\bin64"

if os.path.exists(dll_path):
    os.add_dll_directory(dll_path)
elif os.path.exists(legacy_path):
    os.add_dll_directory(legacy_path)

import PySpin

# =========================
# FLIR CAMERA WRAPPER
# =========================
class FLIRCamera:
    def __init__(self):
        self.system = PySpin.System.GetInstance()
        self.cam_list = self.system.GetCameras()
        self.cam = None

        if self.cam_list.GetSize() == 0:
            raise RuntimeError("No FLIR camera detected")

        self.cam = self.cam_list.GetByIndex(0)
        self.cam.Init()

        # Reduce lag / buffer overflow
        nodemap = self.cam.GetTLStreamNodeMap()
        handling_mode = PySpin.CEnumerationPtr(nodemap.GetNode('StreamBufferHandlingMode'))
        if PySpin.IsReadable(handling_mode) and PySpin.IsWritable(handling_mode):
            entry = handling_mode.GetEntryByName('NewestOnly')
            handling_mode.SetIntValue(entry.GetValue())

        self.converter = PySpin.ImageProcessor()
        self.converter.SetColorProcessing(
            PySpin.SPINNAKER_COLOR_PROCESSING_ALGORITHM_HQ_LINEAR
        )

        self.timeout_ms = 2000
        self.cam.BeginAcquisition()

    def read(self):
        try:
            image = self.cam.GetNextImage(self.timeout_ms)
        except PySpin.SpinnakerException as e:
            print(f"Camera read error: {e}")
            return False, None

        if image.IsIncomplete():
            image.Release()
            return False, None

        frame = self.converter.Convert(image, PySpin.PixelFormat_BGR8).GetNDArray()
        image.Release()
        return True, frame

    def release(self):
        try:
            self.cam.EndAcquisition()
            self.cam.DeInit()
        except:
            pass

        del self.cam
        self.cam_list.Clear()
        self.system.ReleaseInstance()


# =========================
# PYQT5 UI
# =========================
from PyQt5 import QtWidgets, QtGui, QtCore


class ExtensometerApp(QtWidgets.QWidget):
    def __init__(self):
        super().__init__()

        self.setWindowTitle("FLIR Video Extensometer")
        self.setGeometry(100, 100, 1000, 700)

        # UI
        layout = QtWidgets.QVBoxLayout()

        self.video_label = QtWidgets.QLabel()
        layout.addWidget(self.video_label)

        self.input_box = QtWidgets.QLineEdit()
        self.input_box.setPlaceholderText("Enter Gauge Length (mm)")
        layout.addWidget(self.input_box)

        self.start_btn = QtWidgets.QPushButton("Start")
        self.stop_btn = QtWidgets.QPushButton("Stop")
        layout.addWidget(self.start_btn)
        layout.addWidget(self.stop_btn)

        self.result_label = QtWidgets.QLabel("Strain: 0.000000")
        layout.addWidget(self.result_label)

        self.setLayout(layout)

        # CAMERA (FLIR ONLY)
        try:
            self.cap = FLIRCamera()
            print("FLIR camera connected")
        except Exception as e:
            self.cap = None
            self.result_label.setText(f"Camera error: {e}")
            self.start_btn.setEnabled(False)

        # TIMER
        self.timer = QtCore.QTimer()
        self.timer.timeout.connect(self.update_frame)

        # STATE
        self.running = False
        self.prev_gray = None
        self.p0 = None
        self.initial_mm = None
        self.pixel_to_mm = None

        # Optical flow
        self.lk_params = dict(
            winSize=(21, 21),
            maxLevel=3,
            criteria=(cv2.TERM_CRITERIA_EPS | cv2.TERM_CRITERIA_COUNT, 30, 0.01)
        )

        self.start_btn.clicked.connect(self.start)
        self.stop_btn.clicked.connect(self.stop)

    # -------------------------
    def distance(self, a, b):
        return sqrt((a[0]-b[0])**2 + (a[1]-b[1])**2)

    # -------------------------
    def start(self):
        if self.cap is None:
            return

        try:
            self.initial_mm = float(self.input_box.text())
        except:
            self.result_label.setText("Invalid gauge length")
            return

        self.running = True
        self.timer.start(30)

    # -------------------------
    def stop(self):
        self.running = False
        self.timer.stop()

    # -------------------------
    def update_frame(self):
        if not self.running:
            return

        ret, frame = self.cap.read()
        if not ret:
            self.result_label.setText("Frame read failed")
            return

        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)

        # -------------------------
        # INITIAL POINT DETECTION
        # -------------------------
        if self.p0 is None:
            corners = cv2.goodFeaturesToTrack(gray, 2, 0.01, 50)

            if corners is not None and len(corners) == 2:
                self.p0 = corners

                d = self.distance(self.p0[0][0], self.p0[1][0])
                if d > 1e-6:
                    self.pixel_to_mm = self.initial_mm / d
                else:
                    self.p0 = None

        # -------------------------
        # TRACKING
        # -------------------------
        elif self.prev_gray is not None:

            p1, st, err = cv2.calcOpticalFlowPyrLK(
                self.prev_gray, gray, self.p0, None, **self.lk_params
            )

            if p1 is not None and st is not None:
                good = p1[st.flatten() == 1]

                if len(good) == 2 and self.pixel_to_mm is not None:
                    pt1, pt2 = good

                    pixel_dist = self.distance(pt1, pt2)
                    mm_dist = pixel_dist * self.pixel_to_mm

                    strain = (mm_dist - self.initial_mm) / self.initial_mm
                    self.result_label.setText(f"Strain: {strain:.6f}")

                    # update points
                    self.p0 = good.reshape(-1, 1, 2)

                    # draw
                    cv2.circle(frame, tuple(pt1.astype(int)), 5, (0,255,0), -1)
                    cv2.circle(frame, tuple(pt2.astype(int)), 5, (0,255,0), -1)
                    cv2.line(frame, tuple(pt1.astype(int)), tuple(pt2.astype(int)), (255,0,0), 2)
            else:
                self.p0 = None

        self.prev_gray = gray.copy()

        # -------------------------
        # DISPLAY
        # -------------------------
        rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        h, w, ch = rgb.shape
        qimg = QtGui.QImage(rgb.data, w, h, ch*w, QtGui.QImage.Format_RGB888)
        self.video_label.setPixmap(QtGui.QPixmap.fromImage(qimg))

    # -------------------------
    def closeEvent(self, event):
        if self.cap:
            self.cap.release()
        event.accept()


# =========================
# MAIN
# =========================
if __name__ == "__main__":
    app = QtWidgets.QApplication(sys.argv)
    win = ExtensometerApp()
    win.show()
    sys.exit(app.exec_())