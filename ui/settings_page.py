import os
from datetime import datetime
from PyQt5 import QtWidgets, QtCore
from ui.custom_dialog import CustomDialog

from database.db_manager import DatabaseManager
from database.audit_manager import AuditManager
from database.audit_archive_service import AuditArchiveService, MAX_ACTIVE_RECORDS
from ui.company_profile_page import CompanyProfilePage


class SettingsPage(QtWidgets.QWidget):

    def __init__(self, current_user=None):
        super().__init__()

        self.current_user = current_user or {}
        self.audit = AuditManager.get_instance()
        self.archive_service = AuditArchiveService.get_instance()

        layout = QtWidgets.QVBoxLayout()
        layout.setContentsMargins(24, 24, 24, 24)
        layout.setSpacing(20)

        title = QtWidgets.QLabel("Settings")
        title.setStyleSheet("font-size: 20px; font-weight: bold; color: #f8fafc;")
        layout.addWidget(title)

        nav_row = QtWidgets.QHBoxLayout()
        nav_row.setSpacing(10)
        self.db_nav_btn = QtWidgets.QPushButton("Database Administration")
        self.company_nav_btn = QtWidgets.QPushButton("Company Profile")
        for btn in (self.db_nav_btn, self.company_nav_btn):
            btn.setCheckable(True)
            btn.setObjectName("settingsNavBtn")
        self.db_nav_btn.setChecked(True)
        nav_row.addWidget(self.db_nav_btn)
        nav_row.addWidget(self.company_nav_btn)
        nav_row.addStretch()
        layout.addLayout(nav_row)

        self.settings_stack = QtWidgets.QStackedWidget()
        self.database_page = self._build_database_page()
        self.company_profile_page = CompanyProfilePage(self.current_user)
        self.settings_stack.addWidget(self.database_page)
        self.settings_stack.addWidget(self.company_profile_page)
        layout.addWidget(self.settings_stack, 1)

        self.setLayout(layout)

        self.db_nav_btn.clicked.connect(lambda: self._switch_settings_page(0))
        self.company_nav_btn.clicked.connect(lambda: self._switch_settings_page(1))

        self.update_db_info()

        self.setStyleSheet("""
            QPushButton#settingsNavBtn {
                background-color: #1e293b;
                color: #94a3b8;
                border: 1px solid #334155;
                border-radius: 6px;
                padding: 8px 16px;
                font-weight: bold;
            }
            QPushButton#settingsNavBtn:checked {
                background-color: #2563eb;
                color: #ffffff;
                border-color: #3b82f6;
            }
            QPushButton#settingsNavBtn:hover {
                background-color: #334155;
                color: #f8fafc;
            }
        """)

    def _switch_settings_page(self, index):
        self.settings_stack.setCurrentIndex(index)
        self.db_nav_btn.setChecked(index == 0)
        self.company_nav_btn.setChecked(index == 1)
        if index == 0:
            self.update_db_info()
        elif index == 1:
            self.company_profile_page.load_profile()

    def _build_database_page(self):
        page = QtWidgets.QWidget()
        layout = QtWidgets.QVBoxLayout(page)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(20)

        page_title = QtWidgets.QLabel("Database Administration")
        page_title.setStyleSheet("font-size: 16px; font-weight: bold; color: #94a3b8;")
        layout.addWidget(page_title)

        # Info Section Card
        info_card = QtWidgets.QFrame()
        info_card.setObjectName("infoCard")
        info_card.setStyleSheet("""
            QFrame#infoCard {
                background-color: #1e293b;
                border: 1px solid #334155;
                border-radius: 8px;
            }
        """)

        info_layout = QtWidgets.QFormLayout()
        info_layout.setContentsMargins(20, 20, 20, 20)
        info_layout.setSpacing(12)
        info_layout.setLabelAlignment(QtCore.Qt.AlignLeft)

        # Section Header
        sec_header = QtWidgets.QLabel("Database Information")
        sec_header.setStyleSheet("font-size: 14px; font-weight: bold; color: #94a3b8; margin-bottom: 8px;")
        info_layout.addRow(sec_header)

        self.path_val = QtWidgets.QLabel("-")
        self.path_val.setStyleSheet("font-size: 13px; color: #f8fafc;")
        self.path_val.setTextInteractionFlags(QtCore.Qt.TextSelectableByMouse)

        self.size_val = QtWidgets.QLabel("-")
        self.size_val.setStyleSheet("font-size: 13px; color: #f8fafc;")

        self.users_val = QtWidgets.QLabel("-")
        self.users_val.setStyleSheet("font-size: 13px; color: #f8fafc;")

        self.reports_val = QtWidgets.QLabel("-")
        self.reports_val.setStyleSheet("font-size: 13px; color: #f8fafc;")

        def create_form_label(text):
            label = QtWidgets.QLabel(text)
            label.setStyleSheet("font-size: 13px; color: #94a3b8; font-weight: bold;")
            return label

        info_layout.addRow(create_form_label("Database Path:"), self.path_val)
        info_layout.addRow(create_form_label("Database Size:"), self.size_val)
        info_layout.addRow(create_form_label("Total Registered Users:"), self.users_val)
        info_layout.addRow(create_form_label("Total Generated Reports:"), self.reports_val)

        info_card.setLayout(info_layout)
        layout.addWidget(info_card)

        # Actions Section Card
        actions_card = QtWidgets.QFrame()
        actions_card.setObjectName("actionsCard")
        actions_card.setStyleSheet("""
            QFrame#actionsCard {
                background-color: #1e293b;
                border: 1px solid #334155;
                border-radius: 8px;
            }
        """)

        actions_layout = QtWidgets.QVBoxLayout()
        actions_layout.setContentsMargins(20, 20, 20, 20)
        actions_layout.setSpacing(16)

        actions_header = QtWidgets.QLabel("Database Backup & Restore")
        actions_header.setStyleSheet("font-size: 14px; font-weight: bold; color: #94a3b8;")
        actions_layout.addWidget(actions_header)

        btn_layout = QtWidgets.QHBoxLayout()
        btn_layout.setSpacing(16)

        self.backup_btn = QtWidgets.QPushButton("Backup Database")
        self.backup_btn.setStyleSheet("""
            QPushButton {
                background-color: #3b82f6;
                color: white;
                border: none;
                border-radius: 6px;
                padding: 10px 20px;
                font-size: 13px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #2563eb;
            }
            QPushButton:pressed {
                background-color: #1d4ed8;
            }
        """)

        self.restore_btn = QtWidgets.QPushButton("Restore Database")
        self.restore_btn.setStyleSheet("""
            QPushButton {
                background-color: #ef4444;
                color: white;
                border: none;
                border-radius: 6px;
                padding: 10px 20px;
                font-size: 13px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #dc2626;
            }
            QPushButton:pressed {
                background-color: #b91c1c;
            }
        """)

        btn_layout.addWidget(self.backup_btn)
        btn_layout.addWidget(self.restore_btn)
        btn_layout.addStretch()

        actions_layout.addLayout(btn_layout)
        actions_card.setLayout(actions_layout)
        layout.addWidget(actions_card)

        self.backup_btn.clicked.connect(self.backup_database)
        self.restore_btn.clicked.connect(self.restore_database)

        if self._can_manage_audit_logs():
            layout.addWidget(self._build_audit_management_card())

        layout.addStretch()
        return page

    def _can_manage_audit_logs(self):
        role = (self.current_user or {}).get("role", "")
        return role in ("admin", "superadmin")

    def _build_audit_management_card(self):
        card = QtWidgets.QFrame()
        card.setObjectName("auditMgmtCard")
        card.setStyleSheet("""
            QFrame#auditMgmtCard {
                background-color: #1e293b;
                border: 1px solid #334155;
                border-radius: 8px;
            }
        """)

        card_layout = QtWidgets.QVBoxLayout(card)
        card_layout.setContentsMargins(20, 20, 20, 20)
        card_layout.setSpacing(16)

        header = QtWidgets.QLabel("Audit Log Management")
        header.setStyleSheet("font-size: 14px; font-weight: bold; color: #94a3b8;")
        card_layout.addWidget(header)

        form = QtWidgets.QFormLayout()
        form.setSpacing(10)

        def metric_label():
            label = QtWidgets.QLabel("-")
            label.setStyleSheet("font-size: 13px; color: #f8fafc;")
            return label

        def metric_title(text):
            label = QtWidgets.QLabel(text)
            label.setStyleSheet("font-size: 13px; color: #94a3b8; font-weight: bold;")
            return label

        self.audit_active_val = metric_label()
        self.audit_archived_val = metric_label()
        self.audit_max_val = metric_label()
        self.audit_db_size_val = metric_label()
        self.audit_last_archive_val = metric_label()

        form.addRow(metric_title("Active Records:"), self.audit_active_val)
        form.addRow(metric_title("Archived Records:"), self.audit_archived_val)
        form.addRow(metric_title("Maximum Active Records:"), self.audit_max_val)
        form.addRow(metric_title("Current Database Size:"), self.audit_db_size_val)
        form.addRow(metric_title("Last Archive Date:"), self.audit_last_archive_val)
        card_layout.addLayout(form)

        btn_row = QtWidgets.QHBoxLayout()
        btn_row.setSpacing(12)

        self.archive_now_btn = QtWidgets.QPushButton("Archive Now")
        self.optimize_db_btn = QtWidgets.QPushButton("Optimize Database")
        self.vacuum_db_btn = QtWidgets.QPushButton("Vacuum Database")

        for btn in (self.archive_now_btn, self.optimize_db_btn, self.vacuum_db_btn):
            btn.setStyleSheet("""
                QPushButton {
                    background-color: #334155;
                    color: #f8fafc;
                    border: 1px solid #475569;
                    border-radius: 6px;
                    padding: 10px 16px;
                    font-size: 13px;
                    font-weight: bold;
                }
                QPushButton:hover {
                    background-color: #475569;
                }
            """)

        self.archive_now_btn.clicked.connect(self.archive_audit_logs_now)
        self.optimize_db_btn.clicked.connect(self.optimize_audit_database)
        self.vacuum_db_btn.clicked.connect(self.vacuum_audit_database)

        btn_row.addWidget(self.archive_now_btn)
        btn_row.addWidget(self.optimize_db_btn)
        btn_row.addWidget(self.vacuum_db_btn)
        btn_row.addStretch()
        card_layout.addLayout(btn_row)

        self.audit_max_val.setText(f"{MAX_ACTIVE_RECORDS:,}")
        return card

    def update_audit_info(self):
        if not self._can_manage_audit_logs():
            return
        try:
            stats = self.archive_service.get_stats()
            self.audit_active_val.setText(f"{stats['active_count']:,}")
            self.audit_archived_val.setText(f"{stats['archived_count']:,}")
            self.audit_db_size_val.setText(stats["database_size"])
            self.audit_last_archive_val.setText(stats["last_archive_date"])
        except Exception as exc:
            print(f"[ERROR] Failed to update audit info: {exc}")

    def archive_audit_logs_now(self):
        try:
            actor = self.current_user.get("username", "system")
            actor_role = self.current_user.get("role", "")
            moved = self.archive_service.archive_now(
                username=actor,
                role=actor_role,
            )
            self.update_audit_info()
            self.update_db_info()
            CustomDialog.success(
                self,
                "Archive Complete",
                "Audit archive operation finished successfully.",
                description=f"Moved Records: {moved}",
            )
        except Exception as exc:
            CustomDialog.critical(
                self,
                "Archive Failed",
                "Audit archive operation failed. No records were changed.",
                details=str(exc),
            )

    def optimize_audit_database(self):
        try:
            self.archive_service.optimize_database()
            self.update_audit_info()
            CustomDialog.success(
                self,
                "Database Optimized",
                "SQLite ANALYZE completed successfully.",
            )
        except Exception as exc:
            CustomDialog.critical(
                self,
                "Optimization Failed",
                "Database optimization failed.",
                details=str(exc),
            )

    def vacuum_audit_database(self):
        reply = CustomDialog.question(
            self,
            "Vacuum Database",
            "Run SQLite VACUUM to reclaim unused database space?",
            description="This operation may take a moment on large databases.",
            buttons=["Vacuum Database", "Cancel"],
            default_button="Cancel",
        )
        if reply != CustomDialog.Yes:
            return

        app = QtWidgets.QApplication.instance()
        progress = QtWidgets.QProgressDialog(
            "Optimizing database storage...",
            None,
            0,
            0,
            self,
        )
        progress.setWindowTitle("Vacuum Database")
        progress.setWindowModality(QtCore.Qt.WindowModal)
        progress.setMinimumDuration(0)
        progress.show()
        if app:
            app.processEvents()

        try:
            self.archive_service.vacuum_database()
            progress.close()
            self.update_audit_info()
            self.update_db_info()
            CustomDialog.success(
                self,
                "Vacuum Complete",
                "Database vacuum completed successfully.",
            )
        except Exception as exc:
            progress.close()
            CustomDialog.critical(
                self,
                "Vacuum Failed",
                "Database vacuum failed.",
                details=str(exc),
            )

    def update_db_info(self):
        db_path = "database/extensometer.db"
        abs_path = os.path.abspath(db_path)
        self.path_val.setText(abs_path)

        if os.path.exists(db_path):
            size_bytes = os.path.getsize(db_path)
            if size_bytes < 1024:
                size_str = f"{size_bytes} B"
            elif size_bytes < 1024 * 1024:
                size_str = f"{size_bytes / 1024:.2f} KB"
            else:
                size_str = f"{size_bytes / (1024 * 1024):.2f} MB"
        else:
            size_str = "0 B"
        self.size_val.setText(size_str)

        try:
            db = DatabaseManager()
            cur = db.conn.cursor()

            cur.execute("SELECT COUNT(*) FROM users")
            total_users = cur.fetchone()[0]
            self.users_val.setText(str(total_users))

            cur.execute("SELECT COUNT(*) FROM reports")
            total_reports = cur.fetchone()[0]
            self.reports_val.setText(str(total_reports))

            cur.close()
        except Exception as e:
            print(f"[ERROR] Failed to fetch database info: {e}")

        self.update_audit_info()

    def backup_database(self):
        try:
            default_name = datetime.now().strftime("backup_%Y%m%d_%H%M%S.db")
            options = QtWidgets.QFileDialog.Options()
            file_path, _ = QtWidgets.QFileDialog.getSaveFileName(
                self,
                "Backup Database",
                default_name,
                "SQLite Database (*.db);;All Files (*)",
                options=options
            )

            if file_path:
                if not file_path.lower().endswith(".db"):
                    file_path += ".db"

                db = DatabaseManager()
                if not os.path.exists(DatabaseManager.DB_PATH):
                    CustomDialog.warning(
                        self,
                        "Backup Failed",
                        f"Source database file '{DatabaseManager.DB_PATH}' does not exist."
                    )
                    return

                db.backup_to(file_path)
                print("[DATABASE BACKUP]")

                actor = self.current_user.get("username", "system")
                actor_role = self.current_user.get("role", "")
                self.audit.log_event(
                    action="Database Backup",
                    username=actor,
                    role=actor_role,
                    result="Success",
                    details=file_path,
                )

                CustomDialog.backup_success(self, file_path)
                self.update_db_info()
        except Exception as e:
            print(f"[ERROR] Database backup failed: {e}")
            CustomDialog.critical(
                self,
                "Backup Error",
                "Failed to backup database.",
                details=str(e)
            )

    def restore_database(self):
        try:
            options = QtWidgets.QFileDialog.Options()
            file_path, _ = QtWidgets.QFileDialog.getOpenFileName(
                self,
                "Select Backup Database to Restore",
                "",
                "SQLite Database (*.db);;All Files (*)",
                options=options
            )

            if file_path:
                reply = CustomDialog.question(
                    self,
                    "Confirm Database Restore",
                    "Are you sure you want to restore the database?",
                    description="This action will completely overwrite the current database and ALL its data. This cannot be undone.",
                    buttons=["Yes", "No"],
                    default_button="No"
                )

                if reply == CustomDialog.Yes:
                    if not os.path.exists(file_path):
                        CustomDialog.warning(
                            self,
                            "Restore Failed",
                            "Selected backup file does not exist."
                        )
                        return

                    db = DatabaseManager()
                    db.restore_from(file_path)
                    print("[DATABASE RESTORE]")

                    actor = self.current_user.get("username", "system")
                    actor_role = self.current_user.get("role", "")
                    self.audit.log_event(
                        action="Database Restore",
                        username=actor,
                        role=actor_role,
                        result="Success",
                        details=file_path,
                    )

                    CustomDialog.success(
                        self,
                        "Restore Successful",
                        "Database has been successfully restored.",
                        description=(
                            "All tables, users, and reports have been overwritten from the backup file. "
                            "Open pages such as Reports and Users will refresh automatically."
                        )
                    )
                    self.update_db_info()

                    parent_win = self.window()
                    if parent_win and hasattr(parent_win, 'update_stats'):
                        parent_win.update_stats()
                    if parent_win and hasattr(parent_win, 'refresh_data_views'):
                        parent_win.refresh_data_views()
        except Exception as e:
            print(f"[ERROR] Database restore failed: {e}")
            CustomDialog.critical(
                self,
                "Restore Error",
                "Failed to restore database.",
                details=str(e)
            )

    def showEvent(self, event):
        super().showEvent(event)
        self.update_db_info()
