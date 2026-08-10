import os
import sys
from PyQt5 import QtWidgets, QtGui, QtCore


class CustomDialog(QtWidgets.QDialog):
    """
    A premium dark-themed custom dialog designed to replace QMessageBox.
    Features:
    - Frameless window with custom border, rounded corners, and shadow.
    - Drag-to-move support.
    - Smooth fade-in window transition.
    - Standard drawn vector icons (Success, Warning, Error, Info, Question).
    - Dedicated quick action handlers (Open PDF, Open CSV, Open Folder).
    - Expandable technical details box for errors/tracebacks.
    """
    
    # Button roles compatible with QMessageBox returns
    Ok = 1024
    Cancel = 4194304
    Yes = 16384
    No = 65536
    
    def __init__(
        self,
        parent=None,
        title="Notification",
        message="",
        description="",
        details="",
        icon_type="info",
        buttons=None,
        default_button=None,
        file_path=None
    ):
        super().__init__(parent)
        self.setWindowTitle(title)
        self.setModal(True)
        self.setWindowFlags(QtCore.Qt.FramelessWindowHint | QtCore.Qt.Dialog)
        self.setAttribute(QtCore.Qt.WA_TranslucentBackground, True)
        
        self.message = message
        self.description = description
        self.details = details
        self.icon_type = icon_type
        self.buttons_list = buttons or ["OK"]
        self.default_button = default_button
        self.file_path = file_path
        self.drag_position = QtCore.QPoint()
        
        self.result_value = self.Ok
        
        self.setup_ui()
        self.setup_styles()
        
        # Apply drop shadow
        shadow = QtWidgets.QGraphicsDropShadowEffect(self)
        shadow.setBlurRadius(18)
        shadow.setColor(QtGui.QColor(0, 0, 0, 180))
        shadow.setOffset(0, 4)
        self.main_frame.setGraphicsEffect(shadow)
        
        # Fade-in animation
        self.setWindowOpacity(0.0)
        self.anim = QtCore.QPropertyAnimation(self, b"windowOpacity")
        self.anim.setDuration(150)
        self.anim.setStartValue(0.0)
        self.anim.setEndValue(1.0)
        self.anim.start()

    def mousePressEvent(self, event):
        if event.button() == QtCore.Qt.LeftButton:
            self.drag_position = event.globalPos() - self.frameGeometry().topLeft()
            event.accept()

    def mouseMoveEvent(self, event):
        if event.buttons() == QtCore.Qt.LeftButton:
            self.move(event.globalPos() - self.drag_position)
            event.accept()

    def setup_ui(self):
        # Master container layout
        master_layout = QtWidgets.QVBoxLayout(self)
        master_layout.setContentsMargins(12, 12, 12, 12)
        
        # Rounded main card frame
        self.main_frame = QtWidgets.QFrame()
        self.main_frame.setObjectName("mainFrame")
        
        self.card_layout = QtWidgets.QVBoxLayout(self.main_frame)
        self.card_layout.setContentsMargins(18, 18, 18, 18)
        self.card_layout.setSpacing(14)
        
        # ------------------------------------
        # TOP SECTION: Header Layout
        # ------------------------------------
        header_layout = QtWidgets.QHBoxLayout()
        header_layout.setSpacing(12)
        
        # Header Icon Label
        self.icon_lbl = QtWidgets.QLabel()
        self.icon_lbl.setFixedSize(32, 32)
        self.icon_lbl.setScaledContents(True)
        self.set_icon_pixmap()
        header_layout.addWidget(self.icon_lbl)
        
        # Header Title
        self.title_lbl = QtWidgets.QLabel(self.windowTitle())
        self.title_lbl.setObjectName("titleLabel")
        header_layout.addWidget(self.title_lbl, 1)
        
        # Header Close Button
        self.close_btn = QtWidgets.QPushButton("✕")
        self.close_btn.setObjectName("closeBtn")
        self.close_btn.setFixedSize(22, 22)
        self.close_btn.clicked.connect(self.reject)
        header_layout.addWidget(self.close_btn)
        
        self.card_layout.addLayout(header_layout)
        
        # Thin Divider
        divider = QtWidgets.QFrame()
        divider.setFrameShape(QtWidgets.QFrame.HLine)
        divider.setStyleSheet("background-color: #334155; max-height: 1px; border: none;")
        self.card_layout.addWidget(divider)
        
        # ------------------------------------
        # MIDDLE SECTION: Contents
        # ------------------------------------
        content_layout = QtWidgets.QVBoxLayout()
        content_layout.setSpacing(8)
        
        # Main Message
        if self.message:
            self.msg_lbl = QtWidgets.QLabel(self.message)
            self.msg_lbl.setObjectName("messageLabel")
            self.msg_lbl.setWordWrap(True)
            content_layout.addWidget(self.msg_lbl)
            
        # Description Text
        if self.description:
            self.desc_lbl = QtWidgets.QLabel(self.description)
            self.desc_lbl.setObjectName("descriptionLabel")
            self.desc_lbl.setWordWrap(True)
            content_layout.addWidget(self.desc_lbl)
            
        # File Path Container Card
        if self.file_path:
            self.path_card = QtWidgets.QFrame()
            self.path_card.setObjectName("pathCard")
            path_layout = QtWidgets.QVBoxLayout(self.path_card)
            path_layout.setContentsMargins(10, 8, 10, 8)
            
            path_title = QtWidgets.QLabel("FILE PATH LOCATION:")
            path_title.setStyleSheet("font-size: 9px; font-weight: bold; color: #94a3b8; text-transform: uppercase;")
            path_layout.addWidget(path_title)
            
            self.path_lbl = QtWidgets.QLabel(self.file_path)
            self.path_lbl.setObjectName("pathLabel")
            self.path_lbl.setWordWrap(True)
            path_layout.addWidget(self.path_lbl)
            
            content_layout.addWidget(self.path_card)
            
        # Technical Details Container (Expandable)
        if self.details:
            self.details_toggle = QtWidgets.QPushButton("▶ Show Technical Details")
            self.details_toggle.setObjectName("toggleBtn")
            self.details_toggle.setCheckable(True)
            self.details_toggle.clicked.connect(self.toggle_details)
            content_layout.addWidget(self.details_toggle)
            
            self.details_box = QtWidgets.QPlainTextEdit()
            self.details_box.setObjectName("detailsBox")
            self.details_box.setReadOnly(True)
            self.details_box.setPlainText(self.details)
            self.details_box.hide()
            content_layout.addWidget(self.details_box)
            
        self.card_layout.addLayout(content_layout)
        
        # ------------------------------------
        # BOTTOM SECTION: Buttons Layout
        # ------------------------------------
        self.btns_layout = QtWidgets.QHBoxLayout()
        self.btns_layout.setSpacing(10)
        self.btns_layout.addStretch()
        
        # Generate Action Buttons
        for btn_text in self.buttons_list:
            btn = QtWidgets.QPushButton(btn_text)
            self.style_action_button(btn, btn_text)
            
            # Map clicks
            btn.clicked.connect(lambda checked, t=btn_text: self.handle_button_clicked(t))
            self.btns_layout.addWidget(btn)
            
            if btn_text == self.default_button:
                btn.setDefault(True)
                
        self.card_layout.addLayout(self.btns_layout)
        master_layout.addWidget(self.main_frame)
        self.setLayout(master_layout)

    def set_icon_pixmap(self):
        # Get drawn icons programmatically
        if self.icon_type == "success":
            px = self.draw_success_icon()
        elif self.icon_type == "error":
            px = self.draw_error_icon()
        elif self.icon_type == "warning":
            px = self.draw_warning_icon()
        elif self.icon_type == "pdf":
            px = self.draw_pdf_icon()
        elif self.icon_type == "csv":
            px = self.draw_csv_icon()
        elif self.icon_type == "backup":
            px = self.draw_backup_icon()
        elif self.icon_type == "question":
            px = self.draw_question_icon()
        else:
            px = self.draw_info_icon()
            
        self.icon_lbl.setPixmap(px)

    def draw_success_icon(self):
        pixmap = QtGui.QPixmap(48, 48)
        pixmap.fill(QtCore.Qt.transparent)
        painter = QtGui.QPainter(pixmap)
        painter.setRenderHint(QtGui.QPainter.Antialiasing)
        painter.setPen(QtCore.Qt.NoPen)
        painter.setBrush(QtGui.QBrush(QtGui.QColor("#22C55E")))
        painter.drawEllipse(2, 2, 44, 44)
        
        pen = QtGui.QPen(QtGui.QColor("white"), 4)
        pen.setCapStyle(QtCore.Qt.RoundCap)
        pen.setJoinStyle(QtCore.Qt.RoundJoin)
        painter.setPen(pen)
        
        path = QtGui.QPainterPath()
        path.moveTo(14, 24)
        path.lineTo(21, 31)
        path.lineTo(34, 17)
        painter.drawPath(path)
        painter.end()
        return pixmap

    def draw_error_icon(self):
        pixmap = QtGui.QPixmap(48, 48)
        pixmap.fill(QtCore.Qt.transparent)
        painter = QtGui.QPainter(pixmap)
        painter.setRenderHint(QtGui.QPainter.Antialiasing)
        painter.setPen(QtCore.Qt.NoPen)
        painter.setBrush(QtGui.QBrush(QtGui.QColor("#EF4444")))
        painter.drawEllipse(2, 2, 44, 44)
        
        pen = QtGui.QPen(QtGui.QColor("white"), 4)
        pen.setCapStyle(QtCore.Qt.RoundCap)
        painter.setPen(pen)
        painter.drawLine(16, 16, 32, 32)
        painter.drawLine(32, 16, 16, 32)
        painter.end()
        return pixmap

    def draw_warning_icon(self):
        pixmap = QtGui.QPixmap(48, 48)
        pixmap.fill(QtCore.Qt.transparent)
        painter = QtGui.QPainter(pixmap)
        painter.setRenderHint(QtGui.QPainter.Antialiasing)
        painter.setPen(QtCore.Qt.NoPen)
        painter.setBrush(QtGui.QBrush(QtGui.QColor("#F59E0B")))
        
        points = QtGui.QPolygonF([
            QtCore.QPointF(24, 2),
            QtCore.QPointF(46, 42),
            QtCore.QPointF(2, 42)
        ])
        painter.drawPolygon(points)
        
        painter.setBrush(QtGui.QBrush(QtGui.QColor("white")))
        painter.drawRoundedRect(QtCore.QRectF(22, 16, 4, 13), 2, 2)
        painter.drawEllipse(QtCore.QPointF(24, 34), 2.5, 2.5)
        painter.end()
        return pixmap

    def draw_info_icon(self):
        pixmap = QtGui.QPixmap(48, 48)
        pixmap.fill(QtCore.Qt.transparent)
        painter = QtGui.QPainter(pixmap)
        painter.setRenderHint(QtGui.QPainter.Antialiasing)
        painter.setPen(QtCore.Qt.NoPen)
        painter.setBrush(QtGui.QBrush(QtGui.QColor("#3B82F6")))
        painter.drawEllipse(2, 2, 44, 44)
        
        painter.setBrush(QtGui.QBrush(QtGui.QColor("white")))
        painter.drawEllipse(QtCore.QPointF(24, 14), 2.5, 2.5)
        painter.drawRoundedRect(QtCore.QRectF(22, 20, 4, 13), 2, 2)
        painter.end()
        return pixmap

    def draw_question_icon(self):
        pixmap = QtGui.QPixmap(48, 48)
        pixmap.fill(QtCore.Qt.transparent)
        painter = QtGui.QPainter(pixmap)
        painter.setRenderHint(QtGui.QPainter.Antialiasing)
        painter.setPen(QtCore.Qt.NoPen)
        painter.setBrush(QtGui.QBrush(QtGui.QColor("#3B82F6")))
        painter.drawEllipse(2, 2, 44, 44)
        
        painter.setPen(QtCore.Qt.white)
        font = QtGui.QFont("Segoe UI", 22, QtGui.QFont.Bold)
        painter.setFont(font)
        painter.drawText(QtCore.QRect(0, 0, 48, 44), QtCore.Qt.AlignCenter, "?")
        painter.end()
        return pixmap

    def draw_pdf_icon(self):
        pixmap = QtGui.QPixmap(48, 48)
        pixmap.fill(QtCore.Qt.transparent)
        painter = QtGui.QPainter(pixmap)
        painter.setRenderHint(QtGui.QPainter.Antialiasing)
        painter.setPen(QtCore.Qt.NoPen)
        
        painter.setBrush(QtGui.QBrush(QtGui.QColor("#EF4444")))
        painter.drawRoundedRect(QtCore.QRectF(10, 4, 28, 40), 4, 4)
        
        painter.setBrush(QtGui.QBrush(QtGui.QColor("#B91C1C")))
        corner = QtGui.QPolygonF([
            QtCore.QPointF(28, 4),
            QtCore.QPointF(38, 14),
            QtCore.QPointF(28, 14)
        ])
        painter.drawPolygon(corner)
        
        painter.setPen(QtCore.Qt.white)
        font = QtGui.QFont("Segoe UI", 9, QtGui.QFont.Bold)
        painter.setFont(font)
        painter.drawText(QtCore.QRect(10, 22, 28, 20), QtCore.Qt.AlignCenter, "PDF")
        painter.end()
        return pixmap

    def draw_csv_icon(self):
        pixmap = QtGui.QPixmap(48, 48)
        pixmap.fill(QtCore.Qt.transparent)
        painter = QtGui.QPainter(pixmap)
        painter.setRenderHint(QtGui.QPainter.Antialiasing)
        painter.setPen(QtCore.Qt.NoPen)
        
        painter.setBrush(QtGui.QBrush(QtGui.QColor("#22C55E")))
        painter.drawRoundedRect(QtCore.QRectF(10, 4, 28, 40), 4, 4)
        
        painter.setBrush(QtGui.QBrush(QtGui.QColor("#15803D")))
        corner = QtGui.QPolygonF([
            QtCore.QPointF(28, 4),
            QtCore.QPointF(38, 14),
            QtCore.QPointF(28, 14)
        ])
        painter.drawPolygon(corner)
        
        painter.setPen(QtCore.Qt.white)
        font = QtGui.QFont("Segoe UI", 9, QtGui.QFont.Bold)
        painter.setFont(font)
        painter.drawText(QtCore.QRect(10, 22, 28, 20), QtCore.Qt.AlignCenter, "CSV")
        painter.end()
        return pixmap

    def draw_backup_icon(self):
        pixmap = QtGui.QPixmap(48, 48)
        pixmap.fill(QtCore.Qt.transparent)
        painter = QtGui.QPainter(pixmap)
        painter.setRenderHint(QtGui.QPainter.Antialiasing)
        painter.setPen(QtCore.Qt.NoPen)
        
        painter.setBrush(QtGui.QBrush(QtGui.QColor("#F59E0B")))
        painter.drawRoundedRect(QtCore.QRectF(6, 14, 36, 26), 4, 4)
        painter.drawRoundedRect(QtCore.QRectF(6, 8, 16, 10), 3, 3)
        
        painter.setPen(QtGui.QPen(QtCore.Qt.white, 3, QtCore.Qt.SolidLine, QtCore.Qt.RoundCap))
        painter.drawLine(24, 18, 24, 30)
        painter.drawLine(20, 26, 24, 30)
        painter.drawLine(28, 26, 24, 30)
        painter.end()
        return pixmap

    def style_action_button(self, btn, text):
        btn.setCursor(QtGui.QCursor(QtCore.Qt.PointingHandCursor))
        
        # Color coding buttons depending on role/text
        lowered = text.lower()
        if lowered in ["ok", "yes", "save", "continue", "open pdf", "open csv", "open backup folder"]:
            # Success/Primary Blue/Green color
            bg_color = "#3B82F6"
            hover_color = "#2563EB"
            pressed_color = "#1D4ED8"
            if "open" in lowered or lowered == "yes" or lowered == "continue":
                if "pdf" in lowered or "backup" in lowered:
                    bg_color = "#22C55E"
                    hover_color = "#16A34A"
                    pressed_color = "#15803D"
        elif lowered in ["restart", "reset"]:
            # Orange warning style
            bg_color = "#F97316"
            hover_color = "#EA580C"
            pressed_color = "#C2410C"
        elif lowered in ["delete", "delete report", "delete user", "remove", "discard", "discard measurements", "clear all reports", "clear all audit logs", "vacuum database", "restore default"]:
            # Red warning style
            bg_color = "#EF4444"
            hover_color = "#DC2626"
            pressed_color = "#B91C1C"
        else:
            # Secondary gray style
            bg_color = "#334155"
            hover_color = "#475569"
            pressed_color = "#1E293B"
            
        btn.setStyleSheet(f"""
            QPushButton {{
                background-color: {bg_color};
                color: white;
                border: none;
                border-radius: 6px;
                padding: 8px 16px;
                font-weight: bold;
                font-size: 12px;
                min-width: 80px;
                min-height: 28px;
            }}
            QPushButton:hover {{
                background-color: {hover_color};
            }}
            QPushButton:pressed {{
                background-color: {pressed_color};
            }}
        """)

    def setup_styles(self):
        self.setStyleSheet("""
            QDialog {
                background-color: transparent;
            }
            QFrame#mainFrame {
                background-color: #0F172A;
                border: 1px solid #334155;
                border-radius: 10px;
            }
            QLabel#titleLabel {
                font-size: 15px;
                font-weight: bold;
                color: #FFFFFF;
                font-family: 'Segoe UI', sans-serif;
            }
            QPushButton#closeBtn {
                background-color: transparent;
                color: #94A3B8;
                border: none;
                font-size: 14px;
                font-weight: bold;
            }
            QPushButton#closeBtn:hover {
                color: #EF4444;
            }
            QLabel#messageLabel {
                font-size: 13px;
                font-weight: bold;
                color: #FFFFFF;
                font-family: 'Segoe UI', sans-serif;
            }
            QLabel#descriptionLabel {
                font-size: 12px;
                color: #CBD5E1;
                font-family: 'Segoe UI', sans-serif;
            }
            QFrame#pathCard {
                background-color: #1E293B;
                border: 1px solid #334155;
                border-radius: 6px;
            }
            QLabel#pathLabel {
                font-size: 11px;
                color: #38BDF8;
                font-family: 'Consolas', monospace;
            }
            QPushButton#toggleBtn {
                background-color: transparent;
                color: #38BDF8;
                border: none;
                text-align: left;
                font-size: 11px;
                font-weight: bold;
                padding: 2px 0px;
            }
            QPushButton#toggleBtn:hover {
                color: #7DD3FC;
            }
            QPlainTextEdit#detailsBox {
                background-color: #090D16;
                border: 1px solid #334155;
                border-radius: 4px;
                color: #EF4444;
                font-family: 'Consolas', monospace;
                font-size: 11px;
                min-height: 100px;
                max-height: 180px;
            }
        """)

    def toggle_details(self, checked):
        if checked:
            self.details_toggle.setText("▼ Hide Technical Details")
            self.details_box.show()
            self.resize(self.width(), self.height() + 120)
        else:
            self.details_toggle.setText("▶ Show Technical Details")
            self.details_box.hide()
            self.resize(self.width(), self.height() - 120)

    def handle_button_clicked(self, text):
        lowered = text.lower()
        
        # Execute direct file opening actions if clicked
        if self.file_path:
            if "open pdf" in lowered or "open csv" in lowered or "open file" in lowered:
                try:
                    os.startfile(self.file_path)
                except Exception as e:
                    print(f"[CustomDialog ERROR] Failed to startfile: {e}")
            elif "open folder" in lowered or "open backup folder" in lowered:
                try:
                    target_dir = self.file_path if os.path.isdir(self.file_path) else os.path.dirname(self.file_path)
                    os.startfile(target_dir)
                except Exception as e:
                    print(f"[CustomDialog ERROR] Failed to startfolder: {e}")
                    
        # Map output returns compatible with QDialog.exec_() & QMessageBox
        if lowered in ["ok", "yes", "save", "continue", "open pdf", "open csv", "open backup folder", "restart", "delete", "delete report", "delete user", "clear all reports", "clear all audit logs", "vacuum database", "restore default"]:
            if lowered in ["yes", "restart", "delete", "delete report", "delete user", "clear all reports", "clear all audit logs", "vacuum database", "restore default"]:
                self.result_value = self.Yes
            else:
                self.result_value = self.Ok
            self.accept()
        else:
            if lowered == "no":
                self.result_value = self.No
            else:
                self.result_value = self.Cancel
            self.reject()

    def exec_(self):
        super().exec_()
        return self.result_value

    # ------------------------------------
    # STATIC HELPER APIs
    # ------------------------------------
    @classmethod
    def information(cls, parent, title, message, description="", buttons=None):
        dlg = cls(
            parent=parent,
            title=title,
            message=message,
            description=description,
            icon_type="info",
            buttons=buttons or ["OK"]
        )
        return dlg.exec_()

    @classmethod
    def success(cls, parent, title, message, description="", buttons=None):
        dlg = cls(
            parent=parent,
            title=title,
            message=message,
            description=description,
            icon_type="success",
            buttons=buttons or ["OK"]
        )
        return dlg.exec_()

    @classmethod
    def warning(cls, parent, title, message, description="", buttons=None):
        dlg = cls(
            parent=parent,
            title=title,
            message=message,
            description=description,
            icon_type="warning",
            buttons=buttons or ["OK"]
        )
        return dlg.exec_()

    @classmethod
    def critical(cls, parent, title, message, description="", details="", buttons=None):
        dlg = cls(
            parent=parent,
            title=title,
            message=message,
            description=description,
            details=details,
            icon_type="error",
            buttons=buttons or ["OK"]
        )
        return dlg.exec_()

    @classmethod
    def question(cls, parent, title, message, description="", buttons=None, default_button="No"):
        dlg = cls(
            parent=parent,
            title=title,
            message=message,
            description=description,
            icon_type="question",
            buttons=buttons or ["Yes", "No"],
            default_button=default_button
        )
        return dlg.exec_()

    @classmethod
    def pdf_success(cls, parent, file_path):
        dlg = cls(
            parent=parent,
            title="Report Exported",
            message="Professional PDF report exported successfully.",
            description="The metrology analysis details have been compiled and generated.",
            file_path=file_path,
            icon_type="pdf",
            buttons=["Open PDF", "Open Folder", "OK"],
            default_button="OK"
        )
        return dlg.exec_()

    @classmethod
    def csv_success(cls, parent, file_path):
        dlg = cls(
            parent=parent,
            title="Report Exported",
            message="CSV report successfully exported.",
            description="The complete metric history has been compiled into CSV structure.",
            file_path=file_path,
            icon_type="csv",
            buttons=["Open CSV", "Open Folder", "OK"],
            default_button="OK"
        )
        return dlg.exec_()

    @classmethod
    def backup_success(cls, parent, folder_path):
        dlg = cls(
            parent=parent,
            title="Backup Completed",
            message="System database backup completed successfully.",
            description="A copy of the local database and settings has been archived.",
            file_path=folder_path,
            icon_type="backup",
            buttons=["Open Backup Folder", "Close"],
            default_button="Close"
        )
        return dlg.exec_()
