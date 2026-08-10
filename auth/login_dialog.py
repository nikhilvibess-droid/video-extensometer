from PyQt5 import QtWidgets, QtCore, QtGui

from auth.auth_manager import AuthManager
from database.company_manager import CompanyManager
from ui.custom_dialog import CustomDialog


class LoginDialog(QtWidgets.QDialog):

    def __init__(self):
        super().__init__()

        self.auth = AuthManager()
        self.company = CompanyManager.get_instance()

        self.logged_user = None
        self._login_in_progress = False

        self.setWindowTitle("Login")
        self.setFixedWidth(420)
        self.setStyleSheet("""
            QDialog {
                background-color: #0f172a;
            }
            QWidget {
                color: #f8fafc;
                font-family: 'Segoe UI', -apple-system, sans-serif;
            }
            QLineEdit {
                background-color: #1e293b;
                border: 1px solid #334155;
                border-radius: 8px;
                padding: 10px 12px;
                color: #f8fafc;
                font-size: 13px;
            }
            QLineEdit:focus {
                border-color: #3b82f6;
            }
            QPushButton {
                background-color: #3b82f6;
                color: white;
                border: none;
                border-radius: 8px;
                padding: 10px 16px;
                font-weight: bold;
                font-size: 13px;
            }
            QPushButton:hover {
                background-color: #2563eb;
            }
            QLabel#companyNameLabel {
                font-size: 18px;
                font-weight: bold;
                color: #f8fafc;
            }
            QLabel#subtitleLabel {
                font-size: 11px;
                color: #94a3b8;
            }
            QLabel#logoLabel {
                background-color: #1e293b;
                border: 1px solid #334155;
                border-radius: 8px;
            }
        """)

        layout = QtWidgets.QVBoxLayout()
        layout.setContentsMargins(28, 28, 28, 28)
        layout.setSpacing(14)

        self.logo_label = QtWidgets.QLabel()
        self.logo_label.setObjectName("logoLabel")
        self.logo_label.setAlignment(QtCore.Qt.AlignCenter)
        self.logo_label.setFixedHeight(88)

        self.company_name_label = QtWidgets.QLabel()
        self.company_name_label.setObjectName("companyNameLabel")
        self.company_name_label.setAlignment(QtCore.Qt.AlignCenter)

        subtitle = QtWidgets.QLabel("Video Extensometer Control System")
        subtitle.setObjectName("subtitleLabel")
        subtitle.setAlignment(QtCore.Qt.AlignCenter)

        layout.addWidget(self.logo_label)
        layout.addWidget(self.company_name_label)
        layout.addWidget(subtitle)
        layout.addSpacing(8)

        self.username = QtWidgets.QLineEdit()
        self.username.setPlaceholderText("Username")

        self.password = QtWidgets.QLineEdit()
        self.password.setPlaceholderText("Password")
        self.password.setEchoMode(QtWidgets.QLineEdit.Password)

        self.login_btn = QtWidgets.QPushButton("Login")

        layout.addWidget(self.username)
        layout.addWidget(self.password)
        layout.addWidget(self.login_btn)
        self.setLayout(layout)

        self.login_btn.clicked.connect(self.try_login)
        self.password.returnPressed.connect(self.try_login)
        self.apply_branding()

    def apply_branding(self):
        profile = self.company.get_profile()
        self.company_name_label.setText(profile.get("company_name", ""))
        pixmap = self.company.get_logo_pixmap(220, 72)
        if pixmap and not pixmap.isNull():
            self.logo_label.setPixmap(pixmap)
            self.logo_label.setText("")
        else:
            self.logo_label.setText("Company Logo")

    def try_login(self):

        if self._login_in_progress:
            return

        username = self.username.text()
        password = self.password.text()

        self._login_in_progress = True
        self.login_btn.setEnabled(False)

        try:
            if self.auth.login(username, password):
                self.logged_user = self.auth.current_user
                self.accept()
            else:
                CustomDialog.warning(
                    self,
                    "Login Failed",
                    "Invalid username or password",
                )
        finally:
            self._login_in_progress = False
            if not self.logged_user:
                self.login_btn.setEnabled(True)
