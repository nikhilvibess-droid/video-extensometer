from PyQt5 import QtWidgets

from ui.main_window import MainWindow
from ui.users_page import UsersPage
from ui.audit_logs_page import AuditLogsPage
from ui.reports_page import ReportsPage
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
        # PAGES & STATS PANELS
        # =====================

        right_panel = QtWidgets.QVBoxLayout()

        stats_layout = QtWidgets.QHBoxLayout()

        self.tests_card, self.tests_val = self.create_stat_card("TOTAL TESTS", "0")
        self.users_card, self.users_val = self.create_stat_card("TOTAL USERS", "0")
        self.today_card, self.today_val = self.create_stat_card("REPORTS TODAY", "0")
        self.user_card, self.user_val = self.create_stat_card(
            "CURRENT LOGGED USER",
            self.user["username"] if self.user else "Unknown"
        )

        stats_layout.addWidget(self.tests_card)
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

        self.pages.currentChanged.connect(
            self.update_stats
        )

        # =====================
        # INITIAL LOAD
        # =====================
        self.update_stats()

    def create_stat_card(self, title, initial_value):
        card = QtWidgets.QFrame()
        card.setFrameShape(QtWidgets.QFrame.StyledPanel)
        card.setStyleSheet("""
            QFrame {
                background-color: #f8f9fa;
                border: 1px solid #dee2e6;
                border-radius: 6px;
                padding: 10px;
            }
        """)

        card_layout = QtWidgets.QVBoxLayout()

        title_label = QtWidgets.QLabel(title)
        title_label.setStyleSheet("font-size: 11px; color: #6c757d; font-weight: bold;")
        card_layout.addWidget(title_label)

        value_label = QtWidgets.QLabel(initial_value)
        value_label.setStyleSheet("font-size: 18px; font-weight: bold; color: #212529;")
        card_layout.addWidget(value_label)

        card.setLayout(card_layout)
        return card, value_label

    def update_stats(self):
        try:
            db = DatabaseManager()
            cur = db.conn.cursor()

            # Total Tests
            cur.execute("SELECT COUNT(*) FROM reports")
            total_tests = cur.fetchone()[0]
            self.tests_val.setText(str(total_tests))

            # Total Users
            cur.execute("SELECT COUNT(*) FROM users")
            total_users = cur.fetchone()[0]
            self.users_val.setText(str(total_users))

            # Reports Today
            cur.execute(
                "SELECT COUNT(*) FROM reports WHERE date(created_at, 'localtime') = date('now', 'localtime')"
            )
            reports_today = cur.fetchone()[0]
            self.today_val.setText(str(reports_today))

            cur.close()
        except Exception as e:
            print(f"[ERROR] Failed to update dashboard stats: {e}")