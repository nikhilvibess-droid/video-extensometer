from datetime import datetime
from PyQt5 import QtWidgets

from ui.main_window import MainWindow
from ui.users_page import UsersPage
from ui.audit_logs_page import AuditLogsPage
from ui.reports_page import ReportsPage
from ui.settings_page import SettingsPage
from database.db_manager import DatabaseManager


class DashboardWindow(QtWidgets.QMainWindow):

    def __init__(self, user=None):
        super().__init__()

        self.user = user

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
            QMessageBox {
                background-color: #ffffff;
                color: #0f172a;
            }
            QMessageBox QLabel {
                color: #0f172a;
                font-size: 13px;
            }
            QMessageBox QPushButton {
                background-color: #3b82f6;
                color: #ffffff;
                border: none;
                border-radius: 4px;
                padding: 6px 18px;
                font-weight: bold;
                min-width: 80px;
            }
            QMessageBox QPushButton:hover {
                background-color: #2563eb;
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

        # Logo / Title
        logo_label = QtWidgets.QLabel("VEX CONTROL")
        logo_label.setStyleSheet("font-size: 18px; font-weight: bold; color: #f8fafc; letter-spacing: 1px; margin-bottom: 20px;")
        sidebar_layout.addWidget(logo_label)

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

        self.reports_card, self.reports_val = self.create_stat_card("TOTAL REPORTS", "0")
        self.users_card, self.users_val = self.create_stat_card("TOTAL USERS", "0")
        self.today_card, self.today_val = self.create_stat_card("REPORTS TODAY", "0")
        self.user_card, self.user_val = self.create_stat_card(
            "CURRENT USER",
            self.user["username"] if self.user else "Unknown"
        )

        stats_layout.addWidget(self.reports_card)
        stats_layout.addWidget(self.users_card)
        stats_layout.addWidget(self.today_card)
        stats_layout.addWidget(self.user_card)

        right_panel.addLayout(stats_layout)

        self.pages = QtWidgets.QStackedWidget()

        self.tracking_page = MainWindow(
            self.user
        )

        self.reports_page = ReportsPage()

        self.users_page = UsersPage()

        self.audit_page = AuditLogsPage()

        self.settings_page = SettingsPage()

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
            self.update_stats
        )

        # =====================
        # INITIAL LOAD
        # =====================
        self.update_stats()

    def create_stat_card(self, title, initial_value):
        card = QtWidgets.QFrame()
        card.setObjectName("statCard")
        card.setFrameShape(QtWidgets.QFrame.StyledPanel)
        card.setStyleSheet("""
            QFrame#statCard {
                background-color: #1e293b;
                border: 1px solid #334155;
                border-radius: 8px;
            }
        """)

        card_layout = QtWidgets.QVBoxLayout()
        card_layout.setContentsMargins(16, 16, 16, 16)
        card_layout.setSpacing(8)

        title_label = QtWidgets.QLabel(title)
        title_label.setStyleSheet("font-size: 11px; color: #94a3b8; font-weight: bold; text-transform: uppercase;")
        card_layout.addWidget(title_label)

        value_label = QtWidgets.QLabel(initial_value)
        value_label.setStyleSheet("font-size: 28px; font-weight: bold; color: #f8fafc;")
        card_layout.addWidget(value_label)

        card.setLayout(card_layout)
        return card, value_label

    def update_stats(self):
        try:
            db = DatabaseManager()
            cur = db.conn.cursor()

            # Total Reports
            cur.execute("SELECT COUNT(*) FROM reports")
            total_reports = cur.fetchone()[0]
            self.reports_val.setText(str(total_reports))

            # Total Users
            cur.execute("SELECT COUNT(*) FROM users")
            total_users = cur.fetchone()[0]
            self.users_val.setText(str(total_users))

            # Reports Today
            today_str = datetime.now().strftime("%Y-%m-%d")
            cur.execute(
                "SELECT COUNT(*) FROM reports WHERE date(created_at) = ?",
                (today_str,)
            )
            reports_today = cur.fetchone()[0]
            self.today_val.setText(str(reports_today))

            cur.close()

            if hasattr(self, 'settings_page'):
                self.settings_page.update_db_info()

            self.update_camera_status()
        except Exception as e:
            print(f"[ERROR] Failed to update dashboard stats: {e}")

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
        self.update_stats()