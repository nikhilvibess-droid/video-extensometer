from PyQt5 import QtWidgets
from database.db_manager import DatabaseManager


class AuditLogsPage(QtWidgets.QWidget):

    def __init__(self):
        super().__init__()

        self.db = DatabaseManager()

        layout = QtWidgets.QVBoxLayout()

        self.table = QtWidgets.QTableWidget()

        self.table.setColumnCount(3)

        self.table.setHorizontalHeaderLabels(
            [
                "Timestamp",
                "Username",
                "Action"
            ]
        )

        layout.addWidget(
            self.table
        )

        self.refresh_btn = QtWidgets.QPushButton(
            "Refresh Logs"
        )

        layout.addWidget(
            self.refresh_btn
        )

        self.setLayout(layout)

        self.refresh_btn.clicked.connect(
            self.load_logs
        )

        self.load_logs()

    def load_logs(self):

        cur = self.db.conn.cursor()

        cur.execute(
            """
            SELECT timestamp,
                   username,
                   action
            FROM audit_logs
            ORDER BY id DESC
            """
        )

        logs = cur.fetchall()

        self.table.setRowCount(
            len(logs)
        )

        for row, log in enumerate(logs):

            self.table.setItem(
                row,
                0,
                QtWidgets.QTableWidgetItem(
                    str(log[0])
                )
            )

            self.table.setItem(
                row,
                1,
                QtWidgets.QTableWidgetItem(
                    str(log[1])
                )
            )

            self.table.setItem(
                row,
                2,
                QtWidgets.QTableWidgetItem(
                    str(log[2])
                )
            )