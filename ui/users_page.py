from PyQt5 import QtWidgets, QtCore, QtGui
from ui.custom_dialog import CustomDialog
from ui.role_combo import RoleComboBox, role_display_name

from auth.user_manager import UserManager
from database.audit_manager import AuditManager


class UsersPage(QtWidgets.QWidget):

    def __init__(self, current_user=None):
        super().__init__()

        self.current_user = current_user or {}
        self.manager = UserManager()
        self.audit = AuditManager.get_instance()

        layout = QtWidgets.QVBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(16)

        title = QtWidgets.QLabel("User Management")
        title.setObjectName("pageTitle")
        layout.addWidget(title)

        # =====================
        # USERS TABLE
        # =====================

        self.table = QtWidgets.QTableWidget()
        self.table.setObjectName("usersTable")
        self.table.setColumnCount(2)
        self.table.setHorizontalHeaderLabels(["Username", "Role"])
        self.table.setAlternatingRowColors(True)
        self.table.setSelectionBehavior(QtWidgets.QAbstractItemView.SelectRows)
        self.table.setSelectionMode(QtWidgets.QAbstractItemView.SingleSelection)
        self.table.setEditTriggers(QtWidgets.QAbstractItemView.NoEditTriggers)
        self.table.setShowGrid(True)
        self.table.setFrameShape(QtWidgets.QFrame.NoFrame)
        self.table.setSizePolicy(
            QtWidgets.QSizePolicy.Expanding,
            QtWidgets.QSizePolicy.Expanding,
        )
        self.table.horizontalHeader().setStretchLastSection(True)
        self.table.horizontalHeader().setSectionResizeMode(
            QtWidgets.QHeaderView.Stretch
        )
        self.table.horizontalHeader().setHighlightSections(False)
        self.table.horizontalHeader().setDefaultAlignment(QtCore.Qt.AlignLeft | QtCore.Qt.AlignVCenter)
        self.table.verticalHeader().setVisible(True)
        self.table.verticalHeader().setHighlightSections(False)
        self.table.verticalHeader().setDefaultSectionSize(40)
        self.table.verticalHeader().setSectionResizeMode(
            QtWidgets.QHeaderView.Fixed
        )
        self._style_users_table()
        layout.addWidget(self.table, 1)

        # =====================
        # USERNAME
        # =====================

        self.username_input = QtWidgets.QLineEdit()
        self.username_input.setPlaceholderText("Username")
        layout.addWidget(self.username_input)

        self.password_input = QtWidgets.QLineEdit()
        self.password_input.setPlaceholderText("Password")
        self.password_input.setEchoMode(QtWidgets.QLineEdit.Password)
        layout.addWidget(self.password_input)

        self.role_combo = RoleComboBox()
        layout.addWidget(self.role_combo)

        # =====================
        # BUTTONS
        # =====================

        self.delete_btn = QtWidgets.QPushButton(
            "Delete Selected User"
        )
        self.delete_btn.setObjectName("dangerBtn")
        self.create_btn = QtWidgets.QPushButton(
            "Create User"
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
        self.refresh_btn.setObjectName("secondaryBtn")

        layout.addWidget(
            self.refresh_btn
        )

        # =====================
        # LAYOUT
        # =====================

        self.setLayout(
            layout
        )

        self.setup_stylesheet()

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

    def _style_users_table(self):
        self.table.setAttribute(QtCore.Qt.WA_StyledBackground, True)
        viewport = self.table.viewport()
        viewport.setAttribute(QtCore.Qt.WA_StyledBackground, True)
        viewport.setAutoFillBackground(True)

        palette = self.table.palette()
        palette.setColor(QtGui.QPalette.Base, QtGui.QColor("#1E293B"))
        palette.setColor(QtGui.QPalette.AlternateBase, QtGui.QColor("#0F172A"))
        palette.setColor(QtGui.QPalette.Window, QtGui.QColor("#1E293B"))
        palette.setColor(QtGui.QPalette.Button, QtGui.QColor("#0F172A"))
        palette.setColor(QtGui.QPalette.Text, QtGui.QColor("#FFFFFF"))
        palette.setColor(QtGui.QPalette.Highlight, QtGui.QColor("#3B82F6"))
        palette.setColor(QtGui.QPalette.HighlightedText, QtGui.QColor("#FFFFFF"))
        self.table.setPalette(palette)
        viewport.setPalette(palette)

        header_palette = QtGui.QPalette(palette)
        header_palette.setColor(QtGui.QPalette.Window, QtGui.QColor("#0F172A"))
        header_palette.setColor(QtGui.QPalette.Button, QtGui.QColor("#0F172A"))
        header_palette.setColor(QtGui.QPalette.Base, QtGui.QColor("#0F172A"))

        for header in (self.table.horizontalHeader(), self.table.verticalHeader()):
            header.setAttribute(QtCore.Qt.WA_StyledBackground, True)
            header.setAutoFillBackground(True)
            header.setPalette(header_palette)

        self.table.verticalHeader().setStyleSheet("""
            QHeaderView:vertical {
                background-color: #0F172A;
                border: none;
            }
            QHeaderView {
                background-color: #0F172A;
                border: none;
            }
            QHeaderView::section {
                background-color: #0F172A;
                color: #FFFFFF;
                border: none;
                border-right: 1px solid #334155;
                border-bottom: 1px solid #334155;
                padding: 6px 8px;
                font-size: 12px;
                font-weight: 600;
            }
        """)

        self.table.horizontalHeader().setStyleSheet("""
            QHeaderView {
                background-color: #0F172A;
                border: none;
            }
            QHeaderView::section {
                background-color: #0F172A;
                color: #FFFFFF;
                border: none;
                border-bottom: 1px solid #334155;
                border-right: 1px solid #334155;
                padding: 8px 12px;
                font-size: 13px;
                font-weight: bold;
            }
        """)

        viewport.setStyleSheet("background-color: #1E293B;")

        self.table.setStyleSheet("""
            QTableWidget#usersTable {
                background-color: #1E293B;
                alternate-background-color: #0F172A;
                gridline-color: #334155;
                color: #FFFFFF;
                border: 1px solid #334155;
                border-radius: 8px;
                outline: none;
            }
            QTableWidget#usersTable QAbstractScrollArea {
                background-color: #1E293B;
                border: none;
            }
            QTableWidget#usersTable QAbstractScrollArea::viewport {
                background-color: #1E293B;
            }
            QTableWidget#usersTable QAbstractScrollArea::corner {
                background-color: #0F172A;
                border: none;
            }
            QTableWidget#usersTable QTableCornerButton::section {
                background-color: #0F172A;
                border: none;
                border-right: 1px solid #334155;
                border-bottom: 1px solid #334155;
            }
            QTableWidget#usersTable::item {
                padding: 8px 12px;
                border: none;
            }
            QTableWidget#usersTable::item:alternate {
                background-color: #0F172A;
            }
            QTableWidget#usersTable::item:hover {
                background-color: #2563EB;
                color: #FFFFFF;
            }
            QTableWidget#usersTable::item:selected {
                background-color: #3B82F6;
                color: #FFFFFF;
            }
            QTableWidget#usersTable QScrollBar:vertical {
                background: #0F172A;
                width: 10px;
                margin: 0;
                border: none;
            }
            QTableWidget#usersTable QScrollBar::handle:vertical {
                background: #334155;
                min-height: 24px;
                border-radius: 5px;
            }
            QTableWidget#usersTable QScrollBar::add-line:vertical,
            QTableWidget#usersTable QScrollBar::sub-line:vertical {
                height: 0;
                border: none;
                background: none;
            }
            QTableWidget#usersTable QScrollBar:horizontal {
                background: #0F172A;
                height: 10px;
                margin: 0;
                border: none;
            }
            QTableWidget#usersTable QScrollBar::handle:horizontal {
                background: #334155;
                min-width: 24px;
                border-radius: 5px;
            }
            QTableWidget#usersTable QScrollBar::add-line:horizontal,
            QTableWidget#usersTable QScrollBar::sub-line:horizontal {
                width: 0;
                border: none;
                background: none;
            }
        """)

    def setup_stylesheet(self):
        self.setAttribute(QtCore.Qt.WA_StyledBackground, True)
        self.setStyleSheet("""
            QWidget {
                color: #f8fafc;
                font-family: 'Segoe UI', -apple-system, sans-serif;
            }
            QLabel#pageTitle {
                font-size: 20px;
                font-weight: bold;
                color: #f8fafc;
            }
            QLineEdit {
                background-color: #1e293b;
                border: 1px solid #334155;
                border-radius: 6px;
                padding: 8px 12px;
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
                border-radius: 6px;
                padding: 10px 16px;
                font-weight: bold;
                font-size: 13px;
            }
            QPushButton:hover {
                background-color: #2563eb;
            }
            QPushButton#dangerBtn {
                background-color: #7f1d1d;
                color: #fecaca;
            }
            QPushButton#dangerBtn:hover {
                background-color: #991b1b;
            }
            QPushButton#secondaryBtn {
                background-color: #334155;
                color: #f8fafc;
                border: 1px solid #475569;
            }
            QPushButton#secondaryBtn:hover {
                background-color: #475569;
            }
        """)

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

            role_item = QtWidgets.QTableWidgetItem(
                role_display_name(user[1])
            )
            role_item.setData(QtCore.Qt.UserRole, user[1])
            self.table.setItem(row, 1, role_item)

    def _current_actor(self):
        return (
            self.current_user.get("username", "system"),
            self.current_user.get("role", ""),
        )

    def _refresh_dashboard_stats(self):
        parent = self.window()
        if parent and hasattr(parent, "update_stats"):
            parent.update_stats()

    def _log_delete_blocked(self, target_username, reason):
        actor, actor_role = self._current_actor()
        self.audit.log_event(
            action="Delete User",
            username=actor,
            role=actor_role,
            result="Blocked",
            reason=reason,
            details=f"Target user: '{target_username}'",
        )

    def delete_user(self):

        row = self.table.currentRow()

        if row < 0:
            CustomDialog.warning(
                self,
                "Error",
                "Select a user first",
            )
            return

        username = self.table.item(row, 0).text()
        role_item = self.table.item(row, 1)
        role_value = (
            role_item.data(QtCore.Qt.UserRole)
            if role_item
            else self.manager.get_user_role(username)
        )
        if not role_value:
            role_value = self.manager.get_user_role(username) or ""

        role_label = role_display_name(role_value)
        current_username = self.current_user.get("username", "")

        if username == current_username:
            self._log_delete_blocked(
                username,
                "Attempted self-deletion",
            )
            CustomDialog.warning(
                self,
                "Cannot Delete Current User",
                "You cannot delete the account that is currently logged in.",
                description=(
                    "Please log in with another Administrator account if this "
                    "account needs to be removed."
                ),
                buttons=["OK"],
            )
            return

        if username == "superadmin":
            CustomDialog.warning(
                self,
                "Protected",
                "Cannot delete Super Admin",
            )
            return

        if role_value in ("admin", "superadmin"):
            admin_count = self.manager.count_administrators()
            if admin_count <= 1:
                self._log_delete_blocked(
                    username,
                    "Attempted to delete the last Administrator",
                )
                CustomDialog.warning(
                    self,
                    "Cannot Delete Last Administrator",
                    "The system must always contain at least one Administrator account.",
                    description=(
                        "Create another Administrator before deleting this account."
                    ),
                    buttons=["OK"],
                )
                return

        description_text = (
            f"Username: {username}\n"
            f"Role: {role_label}\n\n"
            f"Warning: This action cannot be undone."
        )

        reply = CustomDialog.question(
            self,
            "Delete User",
            "Are you sure you want to permanently delete this user account?",
            description=description_text,
            buttons=["Delete User", "Cancel"],
            default_button="Cancel",
        )

        if reply != CustomDialog.Yes:
            return

        try:
            self.manager.delete_user(username)

            actor, actor_role = self._current_actor()
            self.audit.log_event(
                action="User Deleted",
                username=actor,
                role=actor_role,
                result="Success",
                details=(
                    f"Performed By: {actor} | Deleted User: {username}"
                ),
            )

            self.load_users()
            self._refresh_dashboard_stats()

            CustomDialog.success(
                self,
                "User Deleted",
                "The selected user has been permanently removed.",
                buttons=["OK"],
            )
        except Exception as exc:
            CustomDialog.critical(
                self,
                "Delete Failed",
                "Failed to delete user.",
                details=str(exc),
                buttons=["OK"],
            )

    def create_user(self):

        username = (
            self.username_input.text()
        )

        password = (
            self.password_input.text()
        )

        role = self.role_combo.selected_role_value()

        if not username or not password:

            CustomDialog.warning(
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

            actor = self.current_user.get("username", "system")
            actor_role = self.current_user.get("role", "")
            self.audit.log_event(
                action="User Created",
                username=actor,
                role=actor_role,
                result="Success",
                details=f"Created user '{username}' with role '{role}'",
            )

            self.load_users()

            self.username_input.clear()

            self.password_input.clear()

            CustomDialog.success(
                self,
                "Success",
                "User Created Successfully"
            )

        except Exception as e:

            CustomDialog.warning(
                self,
                "Error",
                str(e)
            )
