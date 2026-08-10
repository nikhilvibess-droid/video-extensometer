import cv2
import numpy as np
from PyQt5 import QtWidgets, QtGui, QtCore


class MarkerSelectionGuideDialog(QtWidgets.QDialog):
    """
    Popup dialog that displays selection instructions and tips to the user
    before marker selection begins.
    """
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Select Gauge Markers")
        self.setModal(True)
        self.resize(450, 420)
        
        # Stylesheet matching modern industrial dark theme
        self.setStyleSheet("""
            QDialog {
                background-color: #0f172a;
            }
            QWidget {
                color: #f8fafc;
                font-family: 'Segoe UI', -apple-system, sans-serif;
            }
            QFrame#contentCard {
                background-color: #1e293b;
                border: 1px solid #334155;
                border-radius: 8px;
                padding: 20px;
            }
            QLabel#mainTitle {
                font-size: 18px;
                font-weight: bold;
                color: #3b82f6;
            }
            QLabel#stepTitle {
                font-size: 12px;
                font-weight: bold;
                color: #fbbf24;
                text-transform: uppercase;
                margin-top: 10px;
            }
            QLabel#stepDesc {
                font-size: 13px;
                color: #cbd5e1;
                margin-left: 12px;
                margin-bottom: 6px;
            }
            QLabel#tipText {
                font-size: 12px;
                color: #94a3b8;
                font-style: italic;
            }
            QPushButton#startBtn {
                background-color: #3b82f6;
                color: white;
                border: none;
                border-radius: 6px;
                padding: 10px 20px;
                font-weight: bold;
                font-size: 13px;
            }
            QPushButton#startBtn:hover {
                background-color: #2563eb;
            }
            QPushButton#cancelBtn {
                background-color: #334155;
                color: #f8fafc;
                border: 1px solid #475569;
                border-radius: 6px;
                padding: 10px 20px;
                font-weight: bold;
                font-size: 13px;
            }
            QPushButton#cancelBtn:hover {
                background-color: #475569;
            }
        """)
        
        layout = QtWidgets.QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(16)
        
        card = QtWidgets.QFrame()
        card.setObjectName("contentCard")
        card_layout = QtWidgets.QVBoxLayout(card)
        card_layout.setSpacing(6)
        
        title_label = QtWidgets.QLabel("Select Gauge Markers")
        title_label.setObjectName("mainTitle")
        card_layout.addWidget(title_label)
        
        sub_label = QtWidgets.QLabel("Please select two gauge points.")
        sub_label.setStyleSheet("font-size: 14px; color: #f8fafc; margin-bottom: 12px;")
        card_layout.addWidget(sub_label)
        
        # Step 1
        s1_title = QtWidgets.QLabel("Step 1")
        s1_title.setObjectName("stepTitle")
        s1_desc = QtWidgets.QLabel("Click the center of the upper gauge point.")
        s1_desc.setObjectName("stepDesc")
        card_layout.addWidget(s1_title)
        card_layout.addWidget(s1_desc)
        
        # Step 2
        s2_title = QtWidgets.QLabel("Step 2")
        s2_title.setObjectName("stepTitle")
        s2_desc = QtWidgets.QLabel("Click the center of the lower gauge point.")
        s2_desc.setObjectName("stepDesc")
        card_layout.addWidget(s2_title)
        card_layout.addWidget(s2_desc)
        
        # Tips
        tips_title = QtWidgets.QLabel("Tips")
        tips_title.setObjectName("stepTitle")
        tips_title.setStyleSheet("color: #94a3b8; font-size: 12px; margin-top: 14px;")
        card_layout.addWidget(tips_title)
        
        tip1 = QtWidgets.QLabel("• Use the zoom window for precise positioning.")
        tip1.setObjectName("tipText")
        tip2 = QtWidgets.QLabel("• Press Enter to confirm.")
        tip2.setObjectName("tipText")
        tip3 = QtWidgets.QLabel("• Press Esc to cancel.")
        tip3.setObjectName("tipText")
        card_layout.addWidget(tip1)
        card_layout.addWidget(tip2)
        card_layout.addWidget(tip3)
        
        layout.addWidget(card)
        
        # Buttons layout
        btn_layout = QtWidgets.QHBoxLayout()
        btn_layout.setSpacing(12)
        
        self.cancel_button = QtWidgets.QPushButton("Cancel")
        self.cancel_button.setObjectName("cancelBtn")
        self.cancel_button.clicked.connect(self.reject)
        
        self.start_button = QtWidgets.QPushButton("Start Selection")
        self.start_button.setObjectName("startBtn")
        self.start_button.clicked.connect(self.accept)
        
        btn_layout.addWidget(self.cancel_button)
        btn_layout.addStretch()
        btn_layout.addWidget(self.start_button)
        
        layout.addLayout(btn_layout)


class ImageWidget(QtWidgets.QWidget):
    """
    Custom widget designed for displaying the camera image and rendering
    visual guides, cursor crosshairs, selected markers, and dashed connections.
    """
    mouse_moved = QtCore.pyqtSignal(object)
    point_selected = QtCore.pyqtSignal(list)

    def __init__(self, frame, parent=None):
        super().__init__(parent)
        self.frame = frame  # BGR Numpy Array
        self.points = []
        self.mouse_pos = None  # Position mapped to image coordinate space
        
        # Convert frame to QPixmap
        rgb = cv2.cvtColor(self.frame, cv2.COLOR_BGR2RGB)
        h, w, ch = rgb.shape
        qimg = QtGui.QImage(rgb.data, w, h, ch * w, QtGui.QImage.Format_RGB888)
        self.pixmap = QtGui.QPixmap.fromImage(qimg)
        
        self.setMouseTracking(True)
        self.setSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Expanding)

    def get_image_rect(self):
        """Calculate coordinates of the image displayed centered keeping aspect ratio."""
        if self.pixmap.isNull():
            return QtCore.QRect()
            
        w_widget = self.width()
        h_widget = self.height()
        w_img = self.pixmap.width()
        h_img = self.pixmap.height()
        
        scale = min(w_widget / w_img, h_widget / h_img)
        w_disp = int(w_img * scale)
        h_disp = int(h_img * scale)
        
        x_offset = (w_widget - w_disp) // 2
        y_offset = (h_widget - h_disp) // 2
        
        return QtCore.QRect(x_offset, y_offset, w_disp, h_disp)

    def map_to_image(self, pos):
        """Map widget coordinate to image pixel coordinate."""
        rect = self.get_image_rect()
        if rect.width() == 0 or rect.height() == 0 or self.pixmap.isNull():
            return None
            
        if not rect.contains(pos):
            return None
            
        x_img = (pos.x() - rect.x()) * self.pixmap.width() / rect.width()
        y_img = (pos.y() - rect.y()) * self.pixmap.height() / rect.height()
        return QtCore.QPoint(int(x_img), int(y_img))

    def map_to_widget(self, pos):
        """Map image pixel coordinate to widget coordinate."""
        rect = self.get_image_rect()
        if rect.width() == 0 or rect.height() == 0 or self.pixmap.isNull():
            return QtCore.QPoint()
            
        x_widget = rect.x() + pos.x() * rect.width() / self.pixmap.width()
        y_widget = rect.y() + pos.y() * rect.height() / self.pixmap.height()
        return QtCore.QPoint(int(x_widget), int(y_widget))

    def mouseMoveEvent(self, event):
        img_pos = self.map_to_image(event.pos())
        if img_pos is not None:
            self.mouse_pos = img_pos
            self.mouse_moved.emit(img_pos)
        else:
            self.mouse_pos = None
            self.mouse_moved.emit(None)
        self.update()

    def leaveEvent(self, event):
        self.mouse_pos = None
        self.mouse_moved.emit(None)
        self.update()

    def mousePressEvent(self, event):
        if event.button() == QtCore.Qt.LeftButton:
            img_pos = self.map_to_image(event.pos())
            if img_pos is not None and len(self.points) < 2:
                pt_tuple = (img_pos.x(), img_pos.y())
                # Avoid selecting the exact same point twice
                if pt_tuple not in self.points:
                    self.points.append(pt_tuple)
                    self.point_selected.emit(self.points)
                    self.update()

    def paintEvent(self, event):
        painter = QtGui.QPainter(self)
        painter.setRenderHint(QtGui.QPainter.Antialiasing)
        
        # Draw background canvas color
        painter.fillRect(self.rect(), QtGui.QColor("#0f172a"))
        
        if self.pixmap.isNull():
            painter.end()
            return
            
        # Draw camera image centered
        rect = self.get_image_rect()
        painter.drawPixmap(rect, self.pixmap)
        
        # Draw dynamic yellow crosshairs on hover
        if self.mouse_pos is not None:
            w_pos = self.map_to_widget(self.mouse_pos)
            
            # Semi-transparent yellow guide lines spanning entire image area
            pen_guide = QtGui.QPen(QtGui.QColor(234, 179, 8, 160), 1, QtCore.Qt.SolidLine)
            painter.setPen(pen_guide)
            
            painter.drawLine(rect.left(), w_pos.y(), rect.right(), w_pos.y())
            painter.drawLine(w_pos.x(), rect.top(), w_pos.x(), rect.bottom())
            
            # Precise central marker guide at cursor
            pen_cursor = QtGui.QPen(QtGui.QColor(234, 179, 8), 2)
            painter.setPen(pen_cursor)
            painter.drawEllipse(w_pos, 4, 4)
            
        # Draw permanently selected markers (yellow crosshair + label)
        pen_marker = QtGui.QPen(QtGui.QColor(234, 179, 8), 2)
        brush_marker = QtGui.QBrush(QtGui.QColor(234, 179, 8, 80))  # Translucent yellow
        
        for idx, pt in enumerate(self.points):
            w_pt = self.map_to_widget(QtCore.QPoint(pt[0], pt[1]))
            
            painter.setPen(pen_marker)
            painter.setBrush(brush_marker)
            painter.drawEllipse(w_pt, 8, 8)
            
            # Inner crosshair coordinates
            painter.drawLine(w_pt.x() - 15, w_pt.y(), w_pt.x() + 15, w_pt.y())
            painter.drawLine(w_pt.x(), w_pt.y() - 15, w_pt.x(), w_pt.y() + 15)
            
            # Render label banner next to the point
            label_text = f"Marker {idx + 1}"
            label_pos = QtCore.QPoint(w_pt.x() + 20, w_pt.y() - 10)
            
            # Measure text size
            font = painter.font()
            font.setPointSize(10)
            font.setBold(True)
            painter.setFont(font)
            metrics = QtGui.QFontMetrics(font)
            text_rect = metrics.boundingRect(label_text)
            
            # Draw label border box
            bg_rect = QtCore.QRect(
                label_pos.x() - 4,
                label_pos.y() - metrics.ascent() - 2,
                text_rect.width() + 8,
                metrics.height() + 4
            )
            
            painter.setPen(QtGui.QPen(QtGui.QColor(234, 179, 8), 1))
            painter.setBrush(QtGui.QBrush(QtGui.QColor(15, 23, 42)))  # Dark background
            painter.drawRoundedRect(bg_rect, 4, 4)
            
            # Render text
            painter.setPen(QtGui.QPen(QtGui.QColor(234, 179, 8)))
            painter.drawText(label_pos, label_text)
            
        # Draw dashed yellow gauge alignment line
        if len(self.points) == 2:
            w_pt1 = self.map_to_widget(QtCore.QPoint(self.points[0][0], self.points[0][1]))
            w_pt2 = self.map_to_widget(QtCore.QPoint(self.points[1][0], self.points[1][1]))
            
            pen_dash = QtGui.QPen(QtGui.QColor(234, 179, 8), 2, QtCore.Qt.DashLine)
            painter.setPen(pen_dash)
            painter.drawLine(w_pt1, w_pt2)
            
        painter.end()


class MarkerSelectionDialog(QtWidgets.QDialog):
    """
    Main marker selection dialog consisting of the left-panel image canvas
    and the right-panel configuration stats (live zoom view, instructions, and marker points).
    """
    def __init__(self, frame, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Marker Selection")
        self.setModal(True)
        self.resize(1400, 900)
        
        self.frame = frame  # Display resolution frame (numpy array)
        self.zoom_level = 300  # Default zoom level (300%)
        self.points = []
        
        self.setup_ui()
        self.setup_stylesheet()

    def setup_stylesheet(self):
        self.setStyleSheet("""
            QDialog {
                background-color: #0f172a;
            }
            QWidget {
                color: #f8fafc;
                font-family: 'Segoe UI', -apple-system, sans-serif;
            }
            QFrame#card {
                background-color: #1e293b;
                border: 1px solid #334155;
                border-radius: 8px;
                padding: 14px;
            }
            QLabel#title {
                font-size: 13px;
                font-weight: bold;
                color: #38bdf8;
                text-transform: uppercase;
                letter-spacing: 0.5px;
            }
            QPushButton {
                background-color: #3b82f6;
                color: white;
                border: none;
                border-radius: 6px;
                padding: 8px 16px;
                font-weight: bold;
                font-size: 13px;
            }
            QPushButton:hover {
                background-color: #2563eb;
            }
            QPushButton:disabled {
                background-color: #1e293b;
                color: #64748b;
                border: 1px solid #334155;
            }
            QPushButton#secondary {
                background-color: #334155;
                color: #f8fafc;
                border: 1px solid #475569;
            }
            QPushButton#secondary:hover {
                background-color: #475569;
            }
            QPushButton#cancel {
                background-color: #ef4444;
                color: white;
            }
            QPushButton#cancel:hover {
                background-color: #dc2626;
            }
        """)

    def setup_ui(self):
        main_layout = QtWidgets.QVBoxLayout(self)
        main_layout.setContentsMargins(16, 16, 16, 16)
        main_layout.setSpacing(16)
        
        # Central Panels (Left: 70%, Right: 30%)
        panels_layout = QtWidgets.QHBoxLayout()
        panels_layout.setSpacing(16)
        
        # Left Panel (Image canvas)
        self.image_widget = ImageWidget(self.frame, self)
        panels_layout.addWidget(self.image_widget, 70)
        
        # Right Panel (Zoom, instructions, point indicators)
        right_container = QtWidgets.QWidget()
        right_layout = QtWidgets.QVBoxLayout(right_container)
        right_layout.setContentsMargins(0, 0, 0, 0)
        right_layout.setSpacing(16)
        
        # 1. Zoom View Card
        zoom_card = QtWidgets.QFrame()
        zoom_card.setObjectName("card")
        zoom_card_layout = QtWidgets.QVBoxLayout(zoom_card)
        zoom_card_layout.setSpacing(10)
        
        zoom_title = QtWidgets.QLabel("Zoom View")
        zoom_title.setObjectName("title")
        zoom_card_layout.addWidget(zoom_title)
        
        self.zoom_label = QtWidgets.QLabel()
        self.zoom_label.setFixedSize(240, 240)
        self.zoom_label.setText("Move cursor over\ncamera feed to zoom")
        self.zoom_label.setAlignment(QtCore.Qt.AlignCenter)
        self.zoom_label.setStyleSheet("color: #64748b; font-size: 12px; font-weight: bold; background-color: #090d16; border: 1px solid #334155; border-radius: 6px;")
        
        # Center the zoom view label
        zoom_lbl_box = QtWidgets.QHBoxLayout()
        zoom_lbl_box.addStretch()
        zoom_lbl_box.addWidget(self.zoom_label)
        zoom_lbl_box.addStretch()
        zoom_card_layout.addLayout(zoom_lbl_box)
        
        self.zoom_level_label = QtWidgets.QLabel(f"Zoom Level: {self.zoom_level}%")
        self.zoom_level_label.setAlignment(QtCore.Qt.AlignCenter)
        self.zoom_level_label.setStyleSheet("font-size: 13px; font-weight: bold; color: #94a3b8;")
        zoom_card_layout.addWidget(self.zoom_level_label)
        
        # Zoom controls
        zoom_btns = QtWidgets.QHBoxLayout()
        self.zoom_in_btn = QtWidgets.QPushButton("Zoom In")
        self.zoom_in_btn.setObjectName("secondary")
        self.zoom_in_btn.clicked.connect(self.zoom_in)
        
        self.zoom_out_btn = QtWidgets.QPushButton("Zoom Out")
        self.zoom_out_btn.setObjectName("secondary")
        self.zoom_out_btn.clicked.connect(self.zoom_out)
        
        self.zoom_reset_btn = QtWidgets.QPushButton("Reset Zoom")
        self.zoom_reset_btn.setObjectName("secondary")
        self.zoom_reset_btn.clicked.connect(self.reset_zoom)
        
        zoom_btns.addWidget(self.zoom_in_btn)
        zoom_btns.addWidget(self.zoom_out_btn)
        zoom_btns.addWidget(self.zoom_reset_btn)
        zoom_card_layout.addLayout(zoom_btns)
        
        right_layout.addWidget(zoom_card)
        
        # 2. Instructions Card
        instr_card = QtWidgets.QFrame()
        instr_card.setObjectName("card")
        instr_card_layout = QtWidgets.QVBoxLayout(instr_card)
        instr_card_layout.setSpacing(8)
        
        instr_title = QtWidgets.QLabel("Instructions")
        instr_title.setObjectName("title")
        instr_card_layout.addWidget(instr_title)
        
        step1_lbl = QtWidgets.QLabel("Step 1: Click Marker 1")
        step1_lbl.setStyleSheet("font-weight: bold; color: #fbbf24; font-size: 12px;")
        step1_desc = QtWidgets.QLabel("Click the exact center of the upper gauge point.")
        step1_desc.setWordWrap(True)
        step1_desc.setStyleSheet("color: #cbd5e1; font-size: 11px; margin-left: 8px;")
        
        step2_lbl = QtWidgets.QLabel("Step 2: Click Marker 2")
        step2_lbl.setStyleSheet("font-weight: bold; color: #fbbf24; font-size: 12px;")
        step2_desc = QtWidgets.QLabel("Click the exact center of the lower gauge point.")
        step2_desc.setWordWrap(True)
        step2_desc.setStyleSheet("color: #cbd5e1; font-size: 11px; margin-left: 8px;")
        
        step3_lbl = QtWidgets.QLabel("Step 3: Confirm")
        step3_lbl.setStyleSheet("font-weight: bold; color: #fbbf24; font-size: 12px;")
        step3_desc = QtWidgets.QLabel("Press Enter to confirm. Press Esc to cancel.")
        step3_desc.setStyleSheet("color: #cbd5e1; font-size: 11px; margin-left: 8px;")
        
        instr_card_layout.addWidget(step1_lbl)
        instr_card_layout.addWidget(step1_desc)
        instr_card_layout.addWidget(step2_lbl)
        instr_card_layout.addWidget(step2_desc)
        instr_card_layout.addWidget(step3_lbl)
        instr_card_layout.addWidget(step3_desc)
        
        right_layout.addWidget(instr_card)
        
        # 3. Selected Points Card
        points_card = QtWidgets.QFrame()
        points_card.setObjectName("card")
        points_card_layout = QtWidgets.QVBoxLayout(points_card)
        points_card_layout.setSpacing(10)
        
        points_title = QtWidgets.QLabel("Selected Points")
        points_title.setObjectName("title")
        points_card_layout.addWidget(points_title)
        
        m1_box = QtWidgets.QHBoxLayout()
        m1_lbl = QtWidgets.QLabel("Marker 1")
        m1_lbl.setStyleSheet("font-weight: bold; color: #94a3b8; font-size: 12px;")
        self.m1_val = QtWidgets.QLabel("Not Selected")
        self.m1_val.setStyleSheet("color: #64748b; font-size: 12px; font-weight: bold;")
        m1_box.addWidget(m1_lbl)
        m1_box.addStretch()
        m1_box.addWidget(self.m1_val)
        
        m2_box = QtWidgets.QHBoxLayout()
        m2_lbl = QtWidgets.QLabel("Marker 2")
        m2_lbl.setStyleSheet("font-weight: bold; color: #94a3b8; font-size: 12px;")
        self.m2_val = QtWidgets.QLabel("Not Selected")
        self.m2_val.setStyleSheet("color: #64748b; font-size: 12px; font-weight: bold;")
        m2_box.addWidget(m2_lbl)
        m2_box.addStretch()
        m2_box.addWidget(self.m2_val)
        
        points_card_layout.addLayout(m1_box)
        points_card_layout.addLayout(m2_box)
        
        right_layout.addWidget(points_card)
        right_layout.addStretch()
        
        panels_layout.addWidget(right_container, 30)
        main_layout.addLayout(panels_layout)
        
        # Bottom Status Area & Buttons
        footer_layout = QtWidgets.QHBoxLayout()
        footer_layout.setSpacing(16)
        
        self.cancel_btn = QtWidgets.QPushButton("Cancel")
        self.cancel_btn.setObjectName("cancel")
        self.cancel_btn.clicked.connect(self.reject)
        
        self.status_label = QtWidgets.QLabel("Waiting for Marker 1...")
        self.status_label.setAlignment(QtCore.Qt.AlignCenter)
        self.status_label.setStyleSheet("font-size: 14px; font-weight: bold; color: #fbbf24;")
        
        self.confirm_btn = QtWidgets.QPushButton("Confirm Markers")
        self.confirm_btn.setEnabled(False)
        self.confirm_btn.clicked.connect(self.accept)
        
        footer_layout.addWidget(self.cancel_btn)
        footer_layout.addWidget(self.status_label, 1)
        footer_layout.addWidget(self.confirm_btn)
        
        main_layout.addLayout(footer_layout)
        
        # Bind signals
        self.image_widget.mouse_moved.connect(self.update_zoom_view)
        self.image_widget.point_selected.connect(self.on_point_selected)

    def extract_crop(self, frame, x, y, size):
        """Extract a crop centered at image pixel coordinates (x, y) with safety boundaries."""
        h, w = frame.shape[:2]
        half = size // 2
        
        x0 = x - half
        y0 = y - half
        x1 = x0 + size
        y1 = y0 + size
        
        crop_x0 = max(0, x0)
        crop_y0 = max(0, y0)
        crop_x1 = min(w, x1)
        crop_y1 = min(h, y1)
        
        crop = frame[crop_y0:crop_y1, crop_x0:crop_x1]
        
        # Pad bounds with black pixels if near borders
        pad_top = crop_y0 - y0
        pad_bottom = y1 - crop_y1
        pad_left = crop_x0 - x0
        pad_right = x1 - crop_x1
        
        if pad_top > 0 or pad_bottom > 0 or pad_left > 0 or pad_right > 0:
            crop = cv2.copyMakeBorder(crop, pad_top, pad_bottom, pad_left, pad_right, cv2.BORDER_CONSTANT, value=[0, 0, 0])
            
        return crop

    def update_zoom_view(self, img_pos):
        """Draw live 200%-500% zoom crop with centered target alignment crosshair."""
        if img_pos is None:
            self.zoom_label.clear()
            self.zoom_label.setText("Move cursor over\ncamera feed to zoom")
            self.zoom_label.setAlignment(QtCore.Qt.AlignCenter)
            self.zoom_label.setStyleSheet("color: #64748b; font-size: 12px; font-weight: bold; background-color: #090d16; border: 1px solid #334155; border-radius: 6px;")
            return
            
        x_img = img_pos.x()
        y_img = img_pos.y()
        
        # Bounding box crop size
        crop_size = 60
        crop = self.extract_crop(self.frame, x_img, y_img, crop_size)
        
        # Resize crop according to magnification factor
        zoom_factor = self.zoom_level / 100.0
        zoom_w = int(crop_size * zoom_factor)
        zoom_h = int(crop_size * zoom_factor)
        zoomed = cv2.resize(crop, (zoom_w, zoom_h), interpolation=cv2.INTER_LINEAR)
        
        # Convert BGR Numpy crop to QPixmap
        rgb = cv2.cvtColor(zoomed, cv2.COLOR_BGR2RGB)
        h, w, ch = rgb.shape
        qimg = QtGui.QImage(rgb.data, w, h, ch * w, QtGui.QImage.Format_RGB888)
        pixmap = QtGui.QPixmap.fromImage(qimg)
        
        # Align pixmap inside zoom container
        pixmap = pixmap.scaled(self.zoom_label.size(), QtCore.Qt.KeepAspectRatio, QtCore.Qt.SmoothTransformation)
        
        # Paint centered crosshair over crop using QPainter
        result_pixmap = QtGui.QPixmap(pixmap.size())
        result_pixmap.fill(QtCore.Qt.transparent)
        
        painter = QtGui.QPainter(result_pixmap)
        painter.drawPixmap(0, 0, pixmap)
        
        cx = result_pixmap.width() // 2
        cy = result_pixmap.height() // 2
        
        # Draw high contrast alignment guide crosshair in red
        pen = QtGui.QPen(QtGui.QColor(239, 68, 68), 2)
        painter.setPen(pen)
        
        # Draw reticle cross lines
        painter.drawLine(cx - 12, cy, cx - 2, cy)
        painter.drawLine(cx + 2, cy, cx + 12, cy)
        painter.drawLine(cx, cy - 12, cx, cy - 2)
        painter.drawLine(cx, cy + 2, cx, cy + 12)
        
        # Center indicator dot
        painter.drawEllipse(QtCore.QPoint(cx, cy), 2, 2)
        painter.end()
        
        self.zoom_label.setPixmap(result_pixmap)

    def on_point_selected(self, points):
        """Update indicators, coordinates, status bar, and enable/disable confirm navigation."""
        self.points = points
        
        # Render Marker 1 status
        if len(points) >= 1:
            self.m1_val.setText(f"({points[0][0]}, {points[0][1]})")
            self.m1_val.setStyleSheet("color: #38bdf8; font-size: 12px; font-weight: bold;")
        else:
            self.m1_val.setText("Not Selected")
            self.m1_val.setStyleSheet("color: #64748b; font-size: 12px; font-weight: bold;")
            
        # Render Marker 2 status
        if len(points) >= 2:
            self.m2_val.setText(f"({points[1][0]}, {points[1][1]})")
            self.m2_val.setStyleSheet("color: #38bdf8; font-size: 12px; font-weight: bold;")
        else:
            self.m2_val.setText("Not Selected")
            self.m2_val.setStyleSheet("color: #64748b; font-size: 12px; font-weight: bold;")
            
        # Update professional bottom status bar and button navigation
        if len(points) == 0:
            self.status_label.setText("Waiting for Marker 1...")
            self.status_label.setStyleSheet("font-size: 14px; font-weight: bold; color: #fbbf24;")
            self.confirm_btn.setEnabled(False)
        elif len(points) == 1:
            self.status_label.setText("Marker 1 Selected. Waiting for Marker 2...")
            self.status_label.setStyleSheet("font-size: 14px; font-weight: bold; color: #fbbf24;")
            self.confirm_btn.setEnabled(False)
        elif len(points) == 2:
            self.status_label.setText("Marker 2 Selected. Press Enter to Confirm.")
            self.status_label.setStyleSheet("font-size: 14px; font-weight: bold; color: #22c55e;")
            self.confirm_btn.setEnabled(True)

    def zoom_in(self):
        """Magnify crop view up to 500%."""
        if self.zoom_level < 500:
            self.zoom_level = min(500, self.zoom_level + 50)
            self.zoom_level_label.setText(f"Zoom Level: {self.zoom_level}%")
            if self.image_widget.mouse_pos is not None:
                self.update_zoom_view(self.image_widget.mouse_pos)

    def zoom_out(self):
        """Demagnify crop view down to 200%."""
        if self.zoom_level > 200:
            self.zoom_level = max(200, self.zoom_level - 50)
            self.zoom_level_label.setText(f"Zoom Level: {self.zoom_level}%")
            if self.image_widget.mouse_pos is not None:
                self.update_zoom_view(self.image_widget.mouse_pos)

    def reset_zoom(self):
        """Reset crop view to 300%."""
        self.zoom_level = 300
        self.zoom_level_label.setText(f"Zoom Level: {self.zoom_level}%")
        if self.image_widget.mouse_pos is not None:
            self.update_zoom_view(self.image_widget.mouse_pos)

    def keyPressEvent(self, event):
        """Keyboard shortcut support (Enter/Return to accept selection, Esc to reject)."""
        if event.key() in (QtCore.Qt.Key_Return, QtCore.Qt.Key_Enter):
            if len(self.points) == 2:
                self.accept()
        elif event.key() == QtCore.Qt.Key_Escape:
            self.reject()
        else:
            super().keyPressEvent(event)


class MarkerSelector:
    """
    Interface class keeping compatibility with main_window.py's calling signature.
    """
    def __init__(self):
        self.points = []
        self.confirmed = False

    def select(self, frame):
        """
        Launches the pre-selection guidance dialog and main Marker Selection window.
        Returns scaled point coordinates [(x1,y1), (x2,y2)] if confirmed, else [].
        """
        self.points = []
        self.confirmed = False
        
        # 1. Show pre-selection instruction pop-up guide
        guide_dialog = MarkerSelectionGuideDialog()
        if guide_dialog.exec_() != QtWidgets.QDialog.Accepted:
            print("[MARKER SELECTION] Selection guide cancelled by operator.")
            return []
            
        # 2. Show main selection dialog
        selection_dialog = MarkerSelectionDialog(frame)
        if selection_dialog.exec_() == QtWidgets.QDialog.Accepted:
            self.points = selection_dialog.points
            self.confirmed = True
            print(f"[MARKER SELECTION] ✓ Marker selection confirmed: {self.points}")
            return self.points
        else:
            self.points = []
            self.confirmed = False
            print("[MARKER SELECTION] Selection cancelled by operator.")
            return []
