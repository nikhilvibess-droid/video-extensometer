import csv
from PyQt5 import QtWidgets, QtCore

from database.report_manager import ReportManager


class ReportsPage(QtWidgets.QWidget):

    def __init__(self):
        super().__init__()

        self.report_manager = ReportManager()

        layout = QtWidgets.QVBoxLayout()

        # =====================
        # REPORTS TABLE
        # =====================
        self.table = QtWidgets.QTableWidget()
        self.table.setColumnCount(7)
        self.table.setHorizontalHeaderLabels(
            [
                "ID",
                "User",
                "Gauge Length",
                "Initial Distance",
                "Final Distance",
                "Strain",
                "Date"
            ]
        )
        self.table.horizontalHeader().setSectionResizeMode(
            QtWidgets.QHeaderView.Stretch
        )
        layout.addWidget(self.table)

        # =====================
        # BUTTONS
        # =====================
        self.refresh_btn = QtWidgets.QPushButton(
            "Refresh Reports"
        )
        layout.addWidget(self.refresh_btn)

        self.export_btn = QtWidgets.QPushButton(
            "Export to CSV"
        )
        layout.addWidget(self.export_btn)

        # =====================
        # LAYOUT
        # =====================
        self.setLayout(layout)

        # =====================
        # SIGNALS
        # =====================
        self.refresh_btn.clicked.connect(
            self.load_reports
        )

        self.export_btn.clicked.connect(
            self.export_csv
        )

        # =====================
        # INITIAL LOAD
        # =====================
        self.load_reports()

    def load_reports(self):
        try:
            reports = self.report_manager.get_reports()
            self.table.setRowCount(len(reports))

            for row, report in enumerate(reports):
                for col, val in enumerate(report):
                    if isinstance(val, float):
                        if col == 5:
                            text = f"{val:+.6f}"
                        else:
                            text = f"{val:.2f}"
                    else:
                        text = str(val)

                    item = QtWidgets.QTableWidgetItem(text)
                    item.setFlags(
                        item.flags() & ~QtCore.Qt.ItemIsEditable
                    )
                    self.table.setItem(row, col, item)

        except Exception as e:
            QtWidgets.QMessageBox.warning(
                self,
                "Error",
                f"Failed to load reports: {e}"
            )

    def export_csv(self):
        try:
            options = QtWidgets.QFileDialog.Options()
            fileName, _ = QtWidgets.QFileDialog.getSaveFileName(
                self,
                "Save Reports CSV",
                "",
                "CSV Files (*.csv);;All Files (*)",
                options=options
            )
            if fileName:
                if not fileName.endswith(".csv"):
                    fileName += ".csv"

                reports = self.report_manager.get_reports()
                with open(fileName, "w", newline="", encoding="utf-8") as f:
                    writer = csv.writer(f)
                    writer.writerow(
                        [
                            "ID",
                            "User",
                            "Gauge Length (mm)",
                            "Initial Distance (mm)",
                            "Final Distance (mm)",
                            "Strain",
                            "Date"
                        ]
                    )
                    for r in reports:
                        writer.writerow(r)

                QtWidgets.QMessageBox.information(
                    self,
                    "Success",
                    f"Reports exported successfully to:\n{fileName}"
                )

        except Exception as e:
            QtWidgets.QMessageBox.warning(
                self,
                "Error",
                f"Failed to export CSV: {e}"
            )
