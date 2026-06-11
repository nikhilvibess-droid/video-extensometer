import csv
from datetime import datetime
from PyQt5 import QtWidgets, QtCore

from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib import colors

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
            "Export CSV"
        )
        layout.addWidget(self.export_btn)

        self.pdf_btn = QtWidgets.QPushButton(
            "Generate PDF"
        )
        layout.addWidget(self.pdf_btn)

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

        self.pdf_btn.clicked.connect(
            self.generate_pdf
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
            default_name = datetime.now().strftime(
                "reports_%Y%m%d_%H%M%S.csv"
            )

            options = QtWidgets.QFileDialog.Options()
            fileName, _ = QtWidgets.QFileDialog.getSaveFileName(
                self,
                "Save Reports CSV",
                default_name,
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
                            "Gauge Length",
                            "Initial Distance",
                            "Final Distance",
                            "Strain",
                            "Created At"
                        ]
                    )
                    for r in reports:
                        writer.writerow(r)

                print("[CSV EXPORTED]")

                QtWidgets.QMessageBox.information(
                    self,
                    "Success",
                    f"CSV exported successfully\n\n{fileName}"
                )

        except Exception as e:
            print(f"[ERROR] Failed to export CSV: {e}")
            QtWidgets.QMessageBox.warning(
                self,
                "Error",
                f"Failed to export CSV: {e}"
            )

    def generate_pdf(self):
        try:
            row = self.table.currentRow()
            if row < 0:
                QtWidgets.QMessageBox.warning(
                    self,
                    "Selection Required",
                    "Please select a report row first."
                )
                return

            report_id = self.table.item(row, 0).text()
            username = self.table.item(row, 1).text()
            gauge_length = self.table.item(row, 2).text()
            initial_distance = self.table.item(row, 3).text()
            final_distance = self.table.item(row, 4).text()
            strain = self.table.item(row, 5).text()
            date_str = self.table.item(row, 6).text()

            default_name = f"report_{report_id}.pdf"
            options = QtWidgets.QFileDialog.Options()
            file_path, _ = QtWidgets.QFileDialog.getSaveFileName(
                self,
                "Save PDF Report",
                default_name,
                "PDF Files (*.pdf);;All Files (*)",
                options=options
            )

            if file_path:
                if not file_path.endswith(".pdf"):
                    file_path += ".pdf"

                doc = SimpleDocTemplate(
                    file_path,
                    pagesize=letter,
                    rightMargin=54,
                    leftMargin=54,
                    topMargin=54,
                    bottomMargin=54
                )
                story = []
                styles = getSampleStyleSheet()

                title_style = ParagraphStyle(
                    name='ReportTitle',
                    parent=styles['Normal'],
                    fontName='Helvetica-Bold',
                    fontSize=24,
                    leading=28,
                    textColor=colors.HexColor('#0f172a'),
                    spaceAfter=20
                )

                label_style = ParagraphStyle(
                    name='ReportLabel',
                    parent=styles['Normal'],
                    fontName='Helvetica-Bold',
                    fontSize=11,
                    leading=14,
                    textColor=colors.HexColor('#64748b')
                )

                value_style = ParagraphStyle(
                    name='ReportValue',
                    parent=styles['Normal'],
                    fontName='Helvetica',
                    fontSize=11,
                    leading=14,
                    textColor=colors.HexColor('#0f172a')
                )

                story.append(Paragraph("Video Extensometer Test Report", title_style))
                story.append(Spacer(1, 15))

                data = [
                    [Paragraph("Report ID", label_style), Paragraph(report_id, value_style)],
                    [Paragraph("Username", label_style), Paragraph(username, value_style)],
                    [Paragraph("Date & Time", label_style), Paragraph(date_str, value_style)],
                    [Paragraph("Gauge Length", label_style), Paragraph(f"{gauge_length} mm" if not gauge_length.endswith("mm") else gauge_length, value_style)],
                    [Paragraph("Initial Distance", label_style), Paragraph(f"{initial_distance} mm" if not initial_distance.endswith("mm") else initial_distance, value_style)],
                    [Paragraph("Final Distance", label_style), Paragraph(f"{final_distance} mm" if not final_distance.endswith("mm") else final_distance, value_style)],
                    [Paragraph("Strain", label_style), Paragraph(strain, value_style)]
                ]

                t = Table(data, colWidths=[150, 350])
                t.setStyle(TableStyle([
                    ('BACKGROUND', (0,0), (-1,-1), colors.HexColor('#f8fafc')),
                    ('ALIGN', (0,0), (-1,-1), 'LEFT'),
                    ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
                    ('TOPPADDING', (0,0), (-1,-1), 12),
                    ('BOTTOMPADDING', (0,0), (-1,-1), 12),
                    ('LEFTPADDING', (0,0), (-1,-1), 15),
                    ('RIGHTPADDING', (0,0), (-1,-1), 15),
                    ('LINEBELOW', (0,0), (-1,-2), 0.5, colors.HexColor('#e2e8f0')),
                    ('BOX', (0,0), (-1,-1), 1, colors.HexColor('#e2e8f0')),
                ]))

                story.append(t)
                doc.build(story)

                print("[PDF GENERATED]")

                QtWidgets.QMessageBox.information(
                    self,
                    "Success",
                    f"PDF report generated successfully.\n\nFile: {file_path}"
                )

        except Exception as e:
            print(f"[ERROR] Failed to generate PDF: {e}")
            QtWidgets.QMessageBox.warning(
                self,
                "Error",
                f"Failed to generate PDF: {e}"
            )
