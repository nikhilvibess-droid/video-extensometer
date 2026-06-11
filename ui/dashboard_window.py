from PyQt5 import QtWidgets

from ui.main_window import MainWindow
from ui.users_page import UsersPage
from ui.audit_logs_page import AuditLogsPage
from ui.reports_page import ReportsPage


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

        self.setCentralWidget(
            central
        )

        layout = QtWidgets.QHBoxLayout()

        central.setLayout(
            layout
        )

        # =====================
        # SIDEBAR
        # =====================

        sidebar = QtWidgets.QVBoxLayout()

        self.user_label = QtWidgets.QLabel(
            f"User: {user['username'] if user else 'Unknown'}"
        )

        self.role_label = QtWidgets.QLabel(
            f"Role: {self.role}"
        )

        sidebar.addWidget(
            self.user_label
        )

        sidebar.addWidget(
            self.role_label
        )

        self.tracking_btn = QtWidgets.QPushButton(
            "Tracking"
        )

        self.reports_btn = QtWidgets.QPushButton(
            "Reports"
        )

        self.users_btn = QtWidgets.QPushButton(
            "Users"
        )

        self.audit_btn = QtWidgets.QPushButton(
            "Audit Logs"
        )

        sidebar.addWidget(
            self.tracking_btn
        )

        sidebar.addWidget(
            self.reports_btn
        )

        sidebar.addWidget(
            self.users_btn
        )

        sidebar.addWidget(
            self.audit_btn
        )

        # RBAC

        if self.role not in [
            "superadmin",
            "admin"
        ]:
            self.users_btn.hide()
            self.audit_btn.hide()

        if self.role not in [
            "superadmin",
            "admin",
            "engineer"
        ]:
            self.reports_btn.hide()

        sidebar.addStretch()

        layout.addLayout(
            sidebar,
            1
        )

        # =====================
        # PAGES
        # =====================

        self.pages = QtWidgets.QStackedWidget()

        self.tracking_page = MainWindow(
            self.user
        )

        self.reports_page = ReportsPage()

        self.users_page = UsersPage()

        self.audit_page = AuditLogsPage()

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

        layout.addWidget(
            self.pages,
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