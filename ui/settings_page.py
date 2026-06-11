import os
import shutil
from datetime import datetime
from PyQt5 import QtWidgets, QtCore

from database.db_manager import DatabaseManager


class SettingsPage(QtWidgets.QWidget):

    def __init__(self):
        super().__init__()

        layout = QtWidgets.QVBoxLayout()
        layout.setContentsMargins(24, 24, 24, 24)
        layout.setSpacing(20)

        # Page Title
        title = QtWidgets.QLabel("Settings & Database Administration")
        title.setStyleSheet("font-size: 20px; font-weight: bold; color: #1e293b;")
        layout.addWidget(title)

        # Info Section Card
        info_card = QtWidgets.QFrame()
        info_card.setObjectName("infoCard")
        info_card.setStyleSheet("""
            QFrame#infoCard {
                background-color: #ffffff;
                border: 1px solid #e2e8f0;
                border-radius: 8px;
            }
        """)

        info_layout = QtWidgets.QFormLayout()
        info_layout.setContentsMargins(20, 20, 20, 20)
        info_layout.setSpacing(12)
        info_layout.setLabelAlignment(QtCore.Qt.AlignLeft)

        # Section Header
        sec_header = QtWidgets.QLabel("Database Information")
        sec_header.setStyleSheet("font-size: 14px; font-weight: bold; color: #475569; margin-bottom: 8px;")
        info_layout.addRow(sec_header)

        self.path_val = QtWidgets.QLabel("-")
        self.path_val.setStyleSheet("font-size: 13px; color: #0f172a;")
        self.path_val.setTextInteractionFlags(QtCore.Qt.TextSelectableByMouse)

        self.size_val = QtWidgets.QLabel("-")
        self.size_val.setStyleSheet("font-size: 13px; color: #0f172a;")

        self.users_val = QtWidgets.QLabel("-")
        self.users_val.setStyleSheet("font-size: 13px; color: #0f172a;")

        self.reports_val = QtWidgets.QLabel("-")
        self.reports_val.setStyleSheet("font-size: 13px; color: #0f172a;")

        def create_form_label(text):
            label = QtWidgets.QLabel(text)
            label.setStyleSheet("font-size: 13px; color: #64748b; font-weight: bold;")
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
                background-color: #ffffff;
                border: 1px solid #e2e8f0;
                border-radius: 8px;
            }
        """)

        actions_layout = QtWidgets.QVBoxLayout()
        actions_layout.setContentsMargins(20, 20, 20, 20)
        actions_layout.setSpacing(16)

        actions_header = QtWidgets.QLabel("Database Backup & Restore")
        actions_header.setStyleSheet("font-size: 14px; font-weight: bold; color: #475569;")
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

        layout.addStretch()
        self.setLayout(layout)

        # Signal Connections
        self.backup_btn.clicked.connect(self.backup_database)
        self.restore_btn.clicked.connect(self.restore_database)

        # Load database details
        self.update_db_info()

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
                db_path = "database/extensometer.db"
                if not os.path.exists(db_path):
                    QtWidgets.QMessageBox.warning(
                        self,
                        "Backup Failed",
                        "Source database file 'database/extensometer.db' does not exist."
                    )
                    return

                shutil.copy2(db_path, file_path)
                print("[DATABASE BACKUP]")

                QtWidgets.QMessageBox.information(
                    self,
                    "Backup Successful",
                    f"Database backup created successfully.\n\nFile: {file_path}"
                )
                self.update_db_info()
        except Exception as e:
            print(f"[ERROR] Database backup failed: {e}")
            QtWidgets.QMessageBox.critical(
                self,
                "Backup Error",
                f"Failed to backup database:\n{e}"
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
                reply = QtWidgets.QMessageBox.question(
                    self,
                    "Confirm Database Restore",
                    "Are you sure you want to restore the database?\n\n"
                    "This action will completely overwrite the current database and ALL its data. "
                    "This cannot be undone.",
                    QtWidgets.QMessageBox.Yes | QtWidgets.QMessageBox.No,
                    QtWidgets.QMessageBox.No
                )

                if reply == QtWidgets.QMessageBox.Yes:
                    db_path = "database/extensometer.db"
                    if not os.path.exists(file_path):
                        QtWidgets.QMessageBox.warning(
                            self,
                            "Restore Failed",
                            "Selected backup file does not exist."
                        )
                        return

                    shutil.copy2(file_path, db_path)
                    print("[DATABASE RESTORE]")

                    QtWidgets.QMessageBox.information(
                        self,
                        "Restore Successful",
                        "Database has been successfully restored."
                    )
                    self.update_db_info()

                    # Trigger a refresh of the dashboard KPI stats
                    parent_win = self.window()
                    if parent_win and hasattr(parent_win, 'update_stats'):
                        parent_win.update_stats()
        except Exception as e:
            print(f"[ERROR] Database restore failed: {e}")
            QtWidgets.QMessageBox.critical(
                self,
                "Restore Error",
                f"Failed to restore database:\n{e}"
            )

    def showEvent(self, event):
        super().showEvent(event)
        self.update_db_info()
