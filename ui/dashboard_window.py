from PyQt5 import QtWidgets, QtCore, QtGui

from ui.main_window import MainWindow
from ui.users_page import UsersPage
from ui.audit_logs_page import AuditLogsPage
from ui.reports_page import ReportsPage
from ui.settings_page import SettingsPage
from database.db_manager import DatabaseManager
from database.audit_manager import AuditManager
from database.company_manager import CompanyManager
from datetime import datetime

ROLE_LABELS = {
    "superadmin": "Super Administrator",
    "admin": "Administrator",
    "engineer": "Engineer",
    "operator": "Operator",
    "viewer": "Viewer",
}

STATUS_STYLES = {
    "Idle": ("#94a3b8", "#334155", "#1e293b"),
    "Ready": ("#60a5fa", "#2563eb", "#172554"),
    "Selecting Markers": ("#fbbf24", "#d97706", "#422006"),
    "Tracking": ("#4ade80", "#16a34a", "#14532d"),
    "Paused": ("#fb923c", "#ea580c", "#431407"),
    "Completed": ("#c084fc", "#9333ea", "#3b0764"),
    "Error": ("#f87171", "#dc2626", "#450a0a"),
}


class DashboardWindow(QtWidgets.QMainWindow):

    def __init__(self, user=None):
        super().__init__()

        self.user = user

        self.audit = AuditManager.get_instance()
        self.company = CompanyManager.get_instance()

        self.role = "superadmin"

        if user:
            self.role = user["role"]

        self.setWindowTitle(
            "Video Extensometer"
        )

        self.resize(
            1600,
            900
        )

        central = QtWidgets.QWidget()
        self.setCentralWidget(central)

        layout = QtWidgets.QHBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        central.setLayout(layout)

        # Global Dark Theme stylesheet
        self.setStyleSheet("""
            QMainWindow {
                background-color: #0f172a;
            }
            QWidget {
                color: #f8fafc;
                font-family: 'Segoe UI', -apple-system, sans-serif;
            }
            QLabel {
                color: #f8fafc;
            }
            QLineEdit {
                background-color: #1e293b;
                border: 1px solid #334155;
                border-radius: 6px;
                padding: 8px 12px;
                color: #f8fafc;
            }
            QLineEdit:focus {
                border-color: #3b82f6;
            }
            QComboBox {
                background-color: #1e293b;
                border: 1px solid #334155;
                border-radius: 6px;
                padding: 6px 12px;
                color: #f8fafc;
            }
            QComboBox:focus {
                border-color: #3b82f6;
            }
            QTableWidget {
                background-color: #1e293b;
                alternate-background-color: #0f172a;
                gridline-color: #334155;
                border: 1px solid #334155;
                border-radius: 8px;
                color: #f8fafc;
            }
            QHeaderView::section {
                background-color: #0f172a;
                color: #94a3b8;
                padding: 6px;
                font-weight: bold;
                border: none;
                border-bottom: 1px solid #334155;
            }
            QTableCornerButton::section {
                background-color: #0f172a;
                border: none;
            }
            QPushButton {
                background-color: #3b82f6;
                color: white;
                border: none;
                border-radius: 6px;
                padding: 8px 16px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #2563eb;
            }
            QPushButton:pressed {
                background-color: #1d4ed8;
            }
            QScrollBar:vertical {
                border: none;
                background: #0f172a;
                width: 10px;
                margin: 0px;
            }
            QScrollBar::handle:vertical {
                background: #334155;
                min-height: 20px;
                border-radius: 5px;
            }
            QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {
                border: none;
                background: none;
            }
        """)

        # =====================
        # SIDEBAR CONTAINER
        # =====================
        sidebar_container = QtWidgets.QFrame()
        sidebar_container.setObjectName("sidebarContainer")
        sidebar_container.setFixedWidth(260)
        sidebar_container.setStyleSheet("""
            QFrame#sidebarContainer {
                background-color: #1e293b;
                border-right: 1px solid #334155;
            }
        """)

        sidebar_layout = QtWidgets.QVBoxLayout()
        sidebar_layout.setContentsMargins(16, 24, 16, 24)
        sidebar_layout.setSpacing(10)
        sidebar_container.setLayout(sidebar_layout)

        # Logo / Company Branding
        brand_widget = QtWidgets.QWidget()
        brand_layout = QtWidgets.QVBoxLayout(brand_widget)
        brand_layout.setContentsMargins(0, 0, 0, 0)
        brand_layout.setSpacing(6)

        self.brand_logo_label = QtWidgets.QLabel()
        self.brand_logo_label.setAlignment(QtCore.Qt.AlignLeft | QtCore.Qt.AlignVCenter)
        self.brand_logo_label.setFixedHeight(52)

        self.brand_name_label = QtWidgets.QLabel()
        self.brand_name_label.setStyleSheet(
            "font-size: 14px; font-weight: bold; color: #f8fafc; letter-spacing: 0.5px;"
        )
        self.brand_name_label.setWordWrap(True)

        brand_layout.addWidget(self.brand_logo_label)
        brand_layout.addWidget(self.brand_name_label)
        sidebar_layout.addWidget(brand_widget)
        self.apply_company_branding()
        self.company.profile_updated.connect(self.apply_company_branding)

        # Buttons
        self.tracking_btn = QtWidgets.QPushButton("Tracking")
        self.reports_btn = QtWidgets.QPushButton("Reports")
        self.users_btn = QtWidgets.QPushButton("Users")
        self.audit_btn = QtWidgets.QPushButton("Audit Logs")
        self.settings_btn = QtWidgets.QPushButton("Settings")

        button_style = """
            QPushButton {
                background-color: transparent;
                color: #94a3b8;
                border: none;
                border-radius: 6px;
                padding: 10px 14px;
                text-align: left;
                font-size: 13px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #334155;
                color: #f8fafc;
            }
            QPushButton:checked {
                background-color: #2563eb;
                color: #ffffff;
            }
        """

        self.nav_group = QtWidgets.QButtonGroup(self)
        self.nav_group.setExclusive(True)

        for btn in [self.tracking_btn, self.reports_btn, self.users_btn, self.audit_btn, self.settings_btn]:
            btn.setCheckable(True)
            btn.setStyleSheet(button_style)
            self.nav_group.addButton(btn)
            sidebar_layout.addWidget(btn)

        self.tracking_btn.setChecked(True)

        # RBAC visibility rules
        if self.role not in ["superadmin", "admin"]:
            self.users_btn.hide()
            self.audit_btn.hide()

        if self.role not in ["superadmin", "admin", "engineer"]:
            self.reports_btn.hide()

        sidebar_layout.addStretch()

        # =====================
        # STATUS INDICATORS
        # =====================
        status_card = QtWidgets.QFrame()
        status_card.setObjectName("statusCard")
        status_card.setStyleSheet("""
            QFrame#statusCard {
                background-color: #0f172a;
                border: 1px solid #334155;
                border-radius: 8px;
            }
        """)
        status_layout = QtWidgets.QVBoxLayout()
        status_layout.setContentsMargins(12, 12, 12, 12)
        status_layout.setSpacing(8)
        status_card.setLayout(status_layout)

        # Camera status
        camera_layout = QtWidgets.QHBoxLayout()
        camera_label = QtWidgets.QLabel("Camera:")
        camera_label.setStyleSheet("color: #94a3b8; font-size: 11px; font-weight: bold;")
        self.camera_status_dot = QtWidgets.QLabel("●")
        self.camera_status_dot.setStyleSheet("color: #ef4444; font-size: 14px;")
        self.camera_status_text = QtWidgets.QLabel("Disconnected")
        self.camera_status_text.setStyleSheet("color: #f8fafc; font-size: 11px; font-weight: bold;")
        camera_layout.addWidget(camera_label)
        camera_layout.addWidget(self.camera_status_dot)
        camera_layout.addWidget(self.camera_status_text)
        camera_layout.addStretch()
        status_layout.addLayout(camera_layout)

        # Logged User status
        user_layout = QtWidgets.QHBoxLayout()
        user_title = QtWidgets.QLabel("User:")
        user_title.setStyleSheet("color: #94a3b8; font-size: 11px; font-weight: bold;")
        self.user_status_val = QtWidgets.QLabel(user["username"] if user else "Unknown")
        self.user_status_val.setStyleSheet("color: #f8fafc; font-size: 11px; font-weight: bold;")
        user_layout.addWidget(user_title)
        user_layout.addWidget(self.user_status_val)
        user_layout.addStretch()
        status_layout.addLayout(user_layout)

        # Current Role status
        role_layout = QtWidgets.QHBoxLayout()
        role_title = QtWidgets.QLabel("Role:")
        role_title.setStyleSheet("color: #94a3b8; font-size: 11px; font-weight: bold;")
        self.role_status_val = QtWidgets.QLabel(self.role)
        self.role_status_val.setStyleSheet("color: #3b82f6; font-size: 11px; font-weight: bold;")
        role_layout.addWidget(role_title)
        role_layout.addWidget(self.role_status_val)
        role_layout.addStretch()
        status_layout.addLayout(role_layout)

        sidebar_layout.addWidget(status_card)

        layout.addWidget(sidebar_container)

        # =====================
        # PAGES & STATS PANELS
        # =====================

        right_panel = QtWidgets.QVBoxLayout()
        right_panel.setContentsMargins(24, 24, 24, 24)
        right_panel.setSpacing(20)

        stats_layout = QtWidgets.QHBoxLayout()
        stats_layout.setSpacing(16)

        self.test_time_card, self.test_time_val = self._create_live_card(
            "TEST TIME", "00:00:00", value_size=32
        )
        self.extension_card, self.extension_val = self._create_live_card(
            "EXTENSION", "0.000 mm", value_size=32, value_color="#38bdf8"
        )
        self.status_reports_card, self.status_badge, self.reports_today_val = (
            self._create_status_and_reports_card()
        )
        self.user_card, self.user_name_val, self.user_role_val = self._create_user_card()

        stats_layout.addWidget(self.test_time_card, 3)
        stats_layout.addWidget(self.extension_card, 3)
        stats_layout.addWidget(self.status_reports_card, 3)
        stats_layout.addWidget(self.user_card, 2)

        right_panel.addLayout(stats_layout)

        self.pages = QtWidgets.QStackedWidget()

        self.tracking_page = MainWindow(
            self.user
        )
        self.tracking_page.live_dashboard_signal.connect(
            self.update_live_dashboard
        )

        self.reports_page = ReportsPage(self.user)

        self.users_page = UsersPage(self.user)

        self.audit_page = AuditLogsPage(self.user)

        self.settings_page = SettingsPage(self.user)

        self.pages.addWidget(
            self.tracking_page
        )

        self.pages.addWidget(
            self.reports_page
        )

        self.pages.addWidget(
            self.users_page
        )

        self.pages.addWidget(
            self.audit_page
        )

        self.pages.addWidget(
            self.settings_page
        )

        right_panel.addWidget(self.pages)

        layout.addLayout(
            right_panel,
            5
        )

        # =====================
        # SIGNALS
        # =====================

        self.tracking_btn.clicked.connect(
            lambda:
            self.pages.setCurrentWidget(
                self.tracking_page
            )
        )

        self.reports_btn.clicked.connect(
            lambda:
            self.pages.setCurrentWidget(
                self.reports_page
            )
        )

        self.users_btn.clicked.connect(
            lambda:
            self.pages.setCurrentWidget(
                self.users_page
            )
        )

        self.audit_btn.clicked.connect(
            lambda:
            self.pages.setCurrentWidget(
                self.audit_page
            )
        )

        self.settings_btn.clicked.connect(
            lambda:
            self.pages.setCurrentWidget(
                self.settings_page
            )
        )

        self.pages.currentChanged.connect(
            self.on_page_changed
        )

        # =====================
        # INITIAL LOAD
        # =====================
        self.update_live_dashboard({
            "test_time": "00:00:00",
            "extension_mm": 0.0,
            "status": "Idle",
        })
        self.refresh_auxiliary_stats()

    def _create_live_card(self, title, initial_value, value_size=28, value_color="#f8fafc"):
        card = QtWidgets.QFrame()
        card.setObjectName("liveStatCard")
        card.setMinimumHeight(118)
        card.setStyleSheet("""
            QFrame#liveStatCard {
                background-color: #1e293b;
                border: 1px solid #334155;
                border-radius: 10px;
            }
        """)

        layout = QtWidgets.QVBoxLayout()
        layout.setContentsMargins(18, 16, 18, 16)
        layout.setSpacing(6)

        title_label = QtWidgets.QLabel(title)
        title_label.setStyleSheet(
            "font-size: 10px; color: #94a3b8; font-weight: bold; letter-spacing: 1px;"
        )

        value_label = QtWidgets.QLabel(initial_value)
        value_label.setStyleSheet(
            f"font-size: {value_size}px; font-weight: bold; color: {value_color};"
        )
        value_label.setAlignment(QtCore.Qt.AlignLeft | QtCore.Qt.AlignVCenter)

        layout.addWidget(title_label)
        layout.addStretch()
        layout.addWidget(value_label)
        layout.addStretch()
        card.setLayout(layout)
        return card, value_label

    def _create_status_and_reports_card(self):
        card = QtWidgets.QFrame()
        card.setObjectName("liveStatCard")
        card.setMinimumHeight(118)
        card.setStyleSheet("""
            QFrame#liveStatCard {
                background-color: #1e293b;
                border: 1px solid #334155;
                border-radius: 10px;
            }
        """)

        outer = QtWidgets.QHBoxLayout()
        outer.setContentsMargins(0, 0, 0, 0)
        outer.setSpacing(0)

        status_panel = QtWidgets.QWidget()
        status_layout = QtWidgets.QVBoxLayout()
        status_layout.setContentsMargins(14, 14, 10, 14)
        status_layout.setSpacing(6)

        status_title = QtWidgets.QLabel("STATUS")
        status_title.setStyleSheet(
            "font-size: 9px; color: #94a3b8; font-weight: bold; letter-spacing: 1px;"
        )

        badge = QtWidgets.QLabel("Idle")
        badge.setAlignment(QtCore.Qt.AlignCenter)
        badge.setMinimumHeight(30)
        badge.setStyleSheet(self._status_badge_style("Idle", compact=True))

        status_layout.addWidget(status_title)
        status_layout.addStretch()
        status_layout.addWidget(badge)
        status_layout.addStretch()
        status_panel.setLayout(status_layout)

        divider = QtWidgets.QFrame()
        divider.setFrameShape(QtWidgets.QFrame.VLine)
        divider.setFixedWidth(1)
        divider.setStyleSheet("background-color: #334155; border: none;")

        reports_panel = QtWidgets.QWidget()
        reports_layout = QtWidgets.QVBoxLayout()
        reports_layout.setContentsMargins(14, 14, 14, 14)
        reports_layout.setSpacing(6)

        reports_title = QtWidgets.QLabel("TODAY'S REPORTS")
        reports_title.setStyleSheet(
            "font-size: 9px; color: #94a3b8; font-weight: bold; letter-spacing: 1px;"
        )

        reports_val = QtWidgets.QLabel("0")
        reports_val.setStyleSheet(
            "font-size: 32px; font-weight: bold; color: #f8fafc;"
        )
        reports_val.setAlignment(QtCore.Qt.AlignLeft | QtCore.Qt.AlignVCenter)

        reports_layout.addWidget(reports_title)
        reports_layout.addStretch()
        reports_layout.addWidget(reports_val)
        reports_layout.addStretch()
        reports_panel.setLayout(reports_layout)

        outer.addWidget(status_panel, 1)
        outer.addWidget(divider)
        outer.addWidget(reports_panel, 1)
        card.setLayout(outer)
        return card, badge, reports_val

    def _create_user_card(self):
        card = QtWidgets.QFrame()
        card.setObjectName("userStatCard")
        card.setMinimumHeight(118)
        card.setStyleSheet("""
            QFrame#userStatCard {
                background-color: #1e293b;
                border: 1px solid #334155;
                border-radius: 10px;
            }
        """)

        layout = QtWidgets.QVBoxLayout()
        layout.setContentsMargins(14, 14, 14, 14)
        layout.setSpacing(4)

        title_label = QtWidgets.QLabel("CURRENT USER")
        title_label.setStyleSheet(
            "font-size: 9px; color: #64748b; font-weight: bold; letter-spacing: 1px;"
        )

        row = QtWidgets.QHBoxLayout()
        row.setSpacing(8)

        icon = QtWidgets.QLabel("👤")
        icon.setStyleSheet("font-size: 14px;")

        text_col = QtWidgets.QVBoxLayout()
        text_col.setSpacing(2)

        username = self.user["username"] if self.user else "Unknown"
        role_key = self.role if self.user else ""
        role_label = ROLE_LABELS.get(role_key, role_key.title() if role_key else "—")

        name_val = QtWidgets.QLabel(username)
        name_val.setStyleSheet("font-size: 13px; font-weight: 600; color: #e2e8f0;")

        role_val = QtWidgets.QLabel(role_label)
        role_val.setStyleSheet("font-size: 11px; color: #94a3b8;")

        text_col.addWidget(name_val)
        text_col.addWidget(role_val)
        row.addWidget(icon)
        row.addLayout(text_col)
        row.addStretch()

        layout.addWidget(title_label)
        layout.addStretch()
        layout.addLayout(row)
        layout.addStretch()
        card.setLayout(layout)
        return card, name_val, role_val

    def _status_badge_style(self, status, compact=False):
        text_color, border_color, bg_color = STATUS_STYLES.get(
            status, STATUS_STYLES["Idle"]
        )
        font_size = "11px" if compact else "13px"
        padding = "4px 8px" if compact else "6px 12px"
        return (
            f"font-size: {font_size}; font-weight: bold; color: {text_color}; "
            f"background-color: {bg_color}; border: 1px solid {border_color}; "
            f"border-radius: 6px; padding: {padding};"
        )

    def _animate_label(self, label):
        effect = QtWidgets.QGraphicsOpacityEffect(label)
        label.setGraphicsEffect(effect)
        anim = QtCore.QPropertyAnimation(effect, b"opacity", label)
        anim.setDuration(180)
        anim.setStartValue(0.55)
        anim.setEndValue(1.0)
        anim.start(QtCore.QAbstractAnimation.DeleteWhenStopped)

    def update_live_dashboard(self, payload):
        test_time = payload.get("test_time", "00:00:00")
        if self.test_time_val.text() != test_time:
            self.test_time_val.setText(test_time)
            self._animate_label(self.test_time_val)

        extension = payload.get("extension_mm", 0.0)
        extension_text = f"{extension:.3f} mm"
        if self.extension_val.text() != extension_text:
            self.extension_val.setText(extension_text)
            self._animate_label(self.extension_val)

        status = payload.get("status", "Idle")
        if self.status_badge.text() != status:
            self.status_badge.setText(status)
            self.status_badge.setStyleSheet(
                self._status_badge_style(status, compact=True)
            )
            self._animate_label(self.status_badge)

    def _fetch_reports_today(self):
        db = DatabaseManager()
        cur = db.conn.cursor()
        today_str = datetime.now().strftime("%Y-%m-%d")
        cur.execute(
            "SELECT COUNT(*) FROM reports WHERE date(created_at) = ?",
            (today_str,),
        )
        count = cur.fetchone()[0]
        cur.close()
        return count

    def refresh_reports_today(self):
        try:
            count = self._fetch_reports_today()
            text = str(count)
            if self.reports_today_val.text() != text:
                self.reports_today_val.setText(text)
                self._animate_label(self.reports_today_val)
        except Exception as e:
            print(f"[ERROR] Failed to refresh today's reports: {e}")

    def on_page_changed(self):
        self.refresh_auxiliary_stats()

    def apply_company_branding(self):
        profile = self.company.get_profile()
        self.brand_name_label.setText(profile.get("company_name", ""))
        pixmap = self.company.get_logo_pixmap(180, 48)
        if pixmap and not pixmap.isNull():
            self.brand_logo_label.setPixmap(pixmap)
            self.brand_logo_label.setText("")
        else:
            self.brand_logo_label.setPixmap(QtGui.QPixmap())
            self.brand_logo_label.setText("")

    def refresh_auxiliary_stats(self):
        try:
            self.refresh_reports_today()

            if hasattr(self, 'settings_page'):
                self.settings_page.update_db_info()

            self.update_camera_status()
            if hasattr(self, 'tracking_page') and self.tracking_page:
                self.tracking_page._emit_dashboard_update(force=True)
        except Exception as e:
            print(f"[ERROR] Failed to refresh dashboard: {e}")

    def update_stats(self):
        """Backward-compatible hook used by reports and settings pages."""
        self.refresh_auxiliary_stats()

    def refresh_data_views(self):
        """Reload database-backed pages after backup restore."""
        try:
            if hasattr(self, "reports_page"):
                self.reports_page.load_reports()
            if hasattr(self, "users_page"):
                self.users_page.load_users()
            if hasattr(self, "audit_page"):
                self.audit_page.load_logs()
            if hasattr(self, "settings_page"):
                self.settings_page.company_profile_page.load_profile()
            self.apply_company_branding()
            self.refresh_auxiliary_stats()
        except Exception as e:
            print(f"[ERROR] Failed to refresh data views after restore: {e}")

    def update_camera_status(self):
        connected = False
        try:
            if hasattr(self, 'tracking_page') and self.tracking_page:
                if hasattr(self.tracking_page, 'camera') and self.tracking_page.camera:
                    if self.tracking_page.camera.cam is not None:
                        connected = True
        except Exception:
            pass

        if connected:
            self.camera_status_dot.setStyleSheet("color: #22c55e; font-size: 14px;")
            self.camera_status_text.setText("Connected")
        else:
            self.camera_status_dot.setStyleSheet("color: #ef4444; font-size: 14px;")
            self.camera_status_text.setText("Disconnected")

    def showEvent(self, event):
        super().showEvent(event)
        self.refresh_auxiliary_stats()

    def closeEvent(self, event):
        try:
            if self.user:
                self.audit.log_logout(
                    username=self.user.get("username"),
                    role=self.user.get("role"),
                )
        except Exception as exc:
            print(f"[AUDIT] Logout record failed: {exc}")
        super().closeEvent(event)