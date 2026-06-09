from PyQt5 import QtWidgets

from ui.main_window import MainWindow
from ui.users_page import UsersPage


class DashboardWindow(QtWidgets.QMainWindow):

    def __init__(self):
        super().__init__()

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

        self.tracking_btn = (
            QtWidgets.QPushButton(
                "Tracking"
            )
        )

        self.users_btn = (
            QtWidgets.QPushButton(
                "Users"
            )
        )

        sidebar.addWidget(
            self.tracking_btn
        )

        sidebar.addWidget(
            self.users_btn
        )

        sidebar.addStretch()

        layout.addLayout(
            sidebar,
            1
        )

        # =====================
        # PAGES
        # =====================

        self.pages = (
            QtWidgets.QStackedWidget()
        )

        self.tracking_page = (
            MainWindow()
        )

        self.users_page = (
            UsersPage()
        )

        self.pages.addWidget(
            self.tracking_page
        )

        self.pages.addWidget(
            self.users_page
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

        self.users_btn.clicked.connect(
            lambda:
            self.pages.setCurrentWidget(
                self.users_page
            )
        )