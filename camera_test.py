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
# CAMERA WRAPPER
# =========================
class FLIRCamera:
    def __init__(self):
        self.system = PySpin.System.GetInstance()
        self.cam_list = self.system.GetCameras()

        if self.cam_list.GetSize() == 0:
            raise RuntimeError("No FLIR camera detected")

        self.cam = self.cam_list.GetByIndex(0)
        self.cam.Init()

        nodemap = self.cam.GetTLStreamNodeMap()
        handling_mode = PySpin.CEnumerationPtr(
            nodemap.GetNode('StreamBufferHandlingMode'))
        if PySpin.IsReadable(handling_mode) and PySpin.IsWritable(handling_mode):
            entry = handling_mode.GetEntryByName('NewestOnly')
            handling_mode.SetIntValue(entry.GetValue())

        self.converter = PySpin.ImageProcessor()
        self.converter.SetColorProcessing(
            PySpin.SPINNAKER_COLOR_PROCESSING_ALGORITHM_HQ_LINEAR
        )

        self.cam.BeginAcquisition()

    def read(self):
        try:
            image = self.cam.GetNextImage(2000)
        except PySpin.SpinnakerException:
            return False, None

        if image.IsIncomplete():
            image.Release()
            return False, None

        frame = self.converter.Convert(
            image, PySpin.PixelFormat_BGR8).GetNDArray()

        image.Release()
        return True, frame

    def release(self):
        try:
            self.cam.EndAcquisition()
            self.cam.DeInit()
        except:
            pass

        self.cam_list.Clear()
        self.system.ReleaseInstance()


# =========================
# PYQT5 UI
# =========================
from PyQt5 import QtWidgets, QtGui, QtCore


class App(QtWidgets.QWidget):
    def __init__(self):
        super().__init__()

        self.setWindowTitle("FLIR Extensometer")
        self.setGeometry(200, 200, 900, 700)

        layout = QtWidgets.QVBoxLayout()

        self.video = QtWidgets.QLabel()
        layout.addWidget(self.video)

        self.input = QtWidgets.QLineEdit()
        self.input.setPlaceholderText("Gauge Length (mm)")
        layout.addWidget(self.input)

        self.btn = QtWidgets.QPushButton("Start")
        layout.addWidget(self.btn)

        self.label = QtWidgets.QLabel("Strain: 0.000000")
        layout.addWidget(self.label)

        self.setLayout(layout)

        # CAMERA
        self.cam = None
        try:
            self.cam = FLIRCamera()
            print("FLIR camera connected")
        except Exception as e:
            self.label.setText(str(e))

        # TIMER
        self.timer = QtCore.QTimer()
        self.timer.timeout.connect(self.update)

        self.running = False
        self.prev = None
        self.p0 = None
        self.scale = None
        self.init_mm = None

        self.btn.clicked.connect(self.start)

        self.lk = dict(
            winSize=(21, 21),
            maxLevel=3,
            criteria=(cv2.TERM_CRITERIA_EPS |
                      cv2.TERM_CRITERIA_COUNT, 30, 0.01)
        )

    # =========================
    # SAFE DISTANCE
    # =========================
    def dist(self, a, b):
        a = np.ravel(a)
        b = np.ravel(b)
        return sqrt((a[0] - b[0])**2 + (a[1] - b[1])**2)

    def start(self):
        try:
            self.init_mm = float(self.input.text())
        except:
            return

        self.running = True
        self.timer.start(30)

    def update(self):
        if not self.running:
            return

        ok, frame = self.cam.read()
        if not ok:
            return

        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)

        # =========================
        # INITIALIZE FEATURES
        # =========================
        if self.p0 is None:
            pts = cv2.goodFeaturesToTrack(gray, 20, 0.01, 10)

            if pts is None or len(pts) < 5:
                return

            self.p0 = pts

            # Compute initial average distance
            dists = []
            for i in range(len(self.p0) - 1):
                d = self.dist(self.p0[i][0], self.p0[i+1][0])
                dists.append(d)

            avg_dist = np.mean(dists)

            if avg_dist > 1e-6:
                self.scale = self.init_mm / avg_dist
            else:
                self.p0 = None
                return

        # =========================
        # TRACK FEATURES
        # =========================
        elif self.prev is not None:

            p1, st, _ = cv2.calcOpticalFlowPyrLK(
                self.prev, gray, self.p0, None, **self.lk)

            if p1 is None or st is None:
                self.p0 = None
                return

            good_new = p1[st.flatten() == 1]

            if len(good_new) < 5:
                self.p0 = None
                return

            good_new = good_new.reshape(-1, 2)

            # Compute average distance
            dists = []
            for i in range(len(good_new) - 1):
                d = self.dist(good_new[i], good_new[i+1])
                dists.append(d)

            avg_pixel_dist = np.mean(dists)
            mm = avg_pixel_dist * self.scale

            strain = (mm - self.init_mm) / self.init_mm
            self.label.setText(f"Strain: {strain:.6f}")

            self.p0 = good_new.reshape(-1, 1, 2)

        self.prev = gray.copy()

        # =========================
        # DISPLAY
        # =========================
        rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        h, w, ch = rgb.shape

        img = QtGui.QImage(
            rgb.data, w, h, ch * w, QtGui.QImage.Format_RGB888)
        self.video.setPixmap(QtGui.QPixmap.fromImage(img))

    def closeEvent(self, e):
        if self.cam:
            self.cam.release()
        e.accept()


# =========================
# RUN APP
# =========================
if __name__ == "__main__":
    app = QtWidgets.QApplication(sys.argv)
    w = App()
    w.show()
    sys.exit(app.exec_())