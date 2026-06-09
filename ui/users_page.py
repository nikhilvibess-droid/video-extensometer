from PyQt5 import QtWidgets

from auth.user_manager import UserManager


class UsersPage(QtWidgets.QWidget):

    def __init__(self):
        super().__init__()

        self.manager = UserManager()

        layout = QtWidgets.QVBoxLayout()

        # =====================
        # USERS TABLE
        # =====================

        self.table = QtWidgets.QTableWidget()

        self.table.setColumnCount(2)

        self.table.setHorizontalHeaderLabels(
            [
                "Username",
                "Role"
            ]
        )

        layout.addWidget(
            self.table
        )

        # =====================
        # USERNAME
        # =====================

        self.username_input = QtWidgets.QLineEdit()

        self.username_input.setPlaceholderText(
            "Username"
        )

        layout.addWidget(
            self.username_input
        )

        # =====================
        # PASSWORD
        # =====================

        self.password_input = QtWidgets.QLineEdit()

        self.password_input.setPlaceholderText(
            "Password"
        )

        layout.addWidget(
            self.password_input
        )

        # =====================
        # ROLE
        # =====================

        self.role_combo = QtWidgets.QComboBox()

        self.role_combo.addItems(
            [
                "admin",
                "engineer",
                "operator",
                "viewer"
            ]
        )

        layout.addWidget(
            self.role_combo
        )

        # =====================
        # BUTTONS
        # =====================

        self.create_btn = QtWidgets.QPushButton(
            "Create User"
        )
        self.delete_btn = QtWidgets.QPushButton(
            "Delete Selected User"
        )

        layout.addWidget(
           self.delete_btn
        )

        layout.addWidget(
            self.create_btn
        )

        self.refresh_btn = QtWidgets.QPushButton(
            "Refresh Users"
        )

        layout.addWidget(
            self.refresh_btn
        )

        # =====================
        # LAYOUT
        # =====================

        self.setLayout(
            layout
        )

        # =====================
        # SIGNALS
        # =====================

        self.refresh_btn.clicked.connect(
            self.load_users
        )

        self.create_btn.clicked.connect(
            self.create_user
        )

        self.delete_btn.clicked.connect(
            self.delete_user
        )

        # =====================
        # INITIAL LOAD
        # =====================

        self.load_users()

    def load_users(self):

        users = self.manager.get_users()

        self.table.setRowCount(
            len(users)
        )

        for row, user in enumerate(users):

            self.table.setItem(
                row,
                0,
                QtWidgets.QTableWidgetItem(
                    user[0]
                )
            )

            self.table.setItem(
                row,
                1,
                QtWidgets.QTableWidgetItem(
                    user[1]
                )
            )

    def create_user(self):

        username = (
            self.username_input.text()
        )

        password = (
            self.password_input.text()
        )

        role = (
            self.role_combo.currentText()
        )

        if not username or not password:

            QtWidgets.QMessageBox.warning(
                self,
                "Error",
                "Username and Password required"
            )

            return

        try:

            self.manager.create_user(
                username,
                password,
                role
            )

            self.load_users()

            self.username_input.clear()

            self.password_input.clear()

            QtWidgets.QMessageBox.information(
                self,
                "Success",
                "User Created Successfully"
            )

        except Exception as e:

            QtWidgets.QMessageBox.warning(
                self,
                "Error",
                str(e)
            )
    def delete_user(self):

        row = self.table.currentRow()

        if row < 0:

            QtWidgets.QMessageBox.warning(
                self,
                "Error",
                "Select a user first"
            )

            return

        username = self.table.item(
            row,
            0
        ).text()

        if username == "superadmin":

            QtWidgets.QMessageBox.warning(
                self,
                "Protected",
                "Cannot delete Super Admin"
            )

            return

        self.manager.delete_user(
            username
        )

        self.load_users()

        QtWidgets.QMessageBox.information(
            self,
            "Success",
            "User Deleted"
        )