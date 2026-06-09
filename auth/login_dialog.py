from PyQt5 import QtWidgets

from auth.auth_manager import AuthManager


class LoginDialog(QtWidgets.QDialog):

    def __init__(self):
        super().__init__()

        self.auth = AuthManager()

        self.setWindowTitle("Login")
        self.resize(350, 180)

        layout = QtWidgets.QVBoxLayout()

        self.username = QtWidgets.QLineEdit()
        self.username.setPlaceholderText("Username")

        self.password = QtWidgets.QLineEdit()
        self.password.setPlaceholderText("Password")
        self.password.setEchoMode(
            QtWidgets.QLineEdit.Password
        )

        self.login_btn = QtWidgets.QPushButton(
            "Login"
        )

        layout.addWidget(self.username)
        layout.addWidget(self.password)
        layout.addWidget(self.login_btn)

        self.setLayout(layout)

        self.login_btn.clicked.connect(
            self.try_login
        )

    def try_login(self):

        username = self.username.text()

        password = self.password.text()

        if self.auth.login(
            username,
            password
        ):

            self.accept()

        else:

            QtWidgets.QMessageBox.warning(
                self,
                "Login Failed",
                "Invalid username or password"
            )