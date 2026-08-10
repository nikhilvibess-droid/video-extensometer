import csv
from datetime import datetime

from PyQt5 import QtWidgets, QtCore

from database.audit_manager import AuditManager
from database.audit_archive_service import (
    AuditArchiveService,
    AuditClearPermissionError,
    MAX_ACTIVE_RECORDS,
)
from ui.custom_dialog import CustomDialog
from ui.table_style import apply_enterprise_table_style

PAGE_SIZE = 100

TABLE_HEADERS = [
    "Timestamp",
    "Username",
    "Role",
    "Action",
    "Result",
    "Reason",
    "Machine",
    "OS User",
    "Session",
    "Version",
]

DATE_RANGE_OPTIONS = [
    "All",
    "Today",
    "Last 7 Days",
    "Last 30 Days",
    "Last 90 Days",
    "Last Year",
]

SORT_OPTIONS = [
    "Newest First",
    "Oldest First",
    "Username A-Z",
    "Action A-Z",
]


class AuditLogsPage(QtWidgets.QWidget):

    def __init__(self, current_user=None):
        super().__init__()

        self.current_user = current_user or {}
        self.audit = AuditManager.get_instance()
        self.archive_service = AuditArchiveService.get_instance()
        self.viewing_active = True
        self.current_page = 0
        self.total_records = 0
        self.active_total = 0
        self.archived_total = 0

        self._build_ui()
        self._apply_styles()
        self._wire_signals()
        self.load_logs()

    def _build_ui(self):
        layout = QtWidgets.QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(12)

        title = QtWidgets.QLabel("Audit Logs")
        title.setObjectName("auditPageTitle")
        layout.addWidget(title)

        source_row = QtWidgets.QHBoxLayout()
        source_label = QtWidgets.QLabel("Log Source")
        source_label.setObjectName("auditSectionLabel")
        self.source_group = QtWidgets.QButtonGroup(self)
        self.active_btn = QtWidgets.QPushButton("Active Logs")
        self.active_btn.setCheckable(True)
        self.active_btn.setChecked(True)
        self.archived_btn = QtWidgets.QPushButton("Archived Logs")
        self.archived_btn.setCheckable(True)
        self.source_group.addButton(self.active_btn)
        self.source_group.addButton(self.archived_btn)
        self.active_btn.setObjectName("sourceToggleActive")
        self.archived_btn.setObjectName("sourceToggleArchived")
        source_row.addWidget(source_label)
        source_row.addWidget(self.active_btn)
        source_row.addWidget(self.archived_btn)
        source_row.addStretch()
        layout.addLayout(source_row)

        filter_card = QtWidgets.QFrame()
        filter_card.setObjectName("auditFilterCard")
        filter_outer = QtWidgets.QVBoxLayout(filter_card)
        filter_outer.setContentsMargins(12, 12, 12, 12)
        filter_outer.setSpacing(8)

        row1 = QtWidgets.QHBoxLayout()
        row1.setSpacing(8)
        self.username_filter = self._filter_input(row1, "Username")
        self.role_filter = self._filter_input(row1, "Role")
        self.action_filter = self._filter_input(row1, "Action")
        self.result_filter = QtWidgets.QComboBox()
        self.result_filter.addItems(["All Results", "Success", "Failed"])
        row1.addWidget(self.result_filter)
        self.machine_filter = self._filter_input(row1, "Machine")
        filter_outer.addLayout(row1)

        row2 = QtWidgets.QHBoxLayout()
        row2.setSpacing(8)
        self.session_filter = self._filter_input(row2, "Session")
        self.os_user_filter = self._filter_input(row2, "OS User")
        self.date_filter = self._filter_input(row2, "Date (YYYY-MM-DD)")
        self.timestamp_filter = self._filter_input(row2, "Timestamp")
        self.range_filter = QtWidgets.QComboBox()
        self.range_filter.addItems(DATE_RANGE_OPTIONS)
        row2.addWidget(self.range_filter)
        self.sort_filter = QtWidgets.QComboBox()
        self.sort_filter.addItems(SORT_OPTIONS)
        row2.addWidget(self.sort_filter)
        filter_outer.addLayout(row2)

        action_row = QtWidgets.QHBoxLayout()
        self.search_btn = QtWidgets.QPushButton("Search")
        self.clear_btn = QtWidgets.QPushButton("Clear")
        self.clear_btn.setObjectName("secondaryBtn")
        action_row.addWidget(self.search_btn)
        action_row.addWidget(self.clear_btn)
        action_row.addStretch()
        filter_outer.addLayout(action_row)
        layout.addWidget(filter_card)

        self.stats_label = QtWidgets.QLabel()
        self.stats_label.setObjectName("auditStatsLabel")
        layout.addWidget(self.stats_label)

        self.table = QtWidgets.QTableWidget()
        self.table.setColumnCount(len(TABLE_HEADERS))
        self.table.setHorizontalHeaderLabels(TABLE_HEADERS)
        self.table.setAlternatingRowColors(True)
        self.table.setSelectionBehavior(QtWidgets.QAbstractItemView.SelectRows)
        self.table.setEditTriggers(QtWidgets.QAbstractItemView.NoEditTriggers)
        self.table.setSortingEnabled(False)
        self.table.horizontalHeader().setStretchLastSection(True)
        self.table.horizontalHeader().setSectionResizeMode(
            QtWidgets.QHeaderView.ResizeToContents
        )
        self.table.setSizePolicy(
            QtWidgets.QSizePolicy.Expanding,
            QtWidgets.QSizePolicy.Expanding,
        )
        apply_enterprise_table_style(self.table, "auditLogsTable", row_height=36)
        layout.addWidget(self.table, 1)

        pager_layout = QtWidgets.QHBoxLayout()
        self.total_label = QtWidgets.QLabel("0 records")
        self.total_label.setObjectName("auditStatsLabel")
        self.prev_btn = QtWidgets.QPushButton("Previous")
        self.prev_btn.setObjectName("secondaryBtn")
        self.next_btn = QtWidgets.QPushButton("Next")
        self.next_btn.setObjectName("secondaryBtn")
        self.page_label = QtWidgets.QLabel("Page 1 of 1")
        self.page_label.setAlignment(QtCore.Qt.AlignCenter)
        self.page_spin = QtWidgets.QSpinBox()
        self.page_spin.setMinimum(1)
        self.page_spin.setMaximum(1)
        self.page_spin.setPrefix("Page ")
        self.jump_btn = QtWidgets.QPushButton("Go")
        self.jump_btn.setObjectName("secondaryBtn")

        pager_layout.addWidget(self.total_label)
        pager_layout.addStretch()
        pager_layout.addWidget(self.prev_btn)
        pager_layout.addWidget(self.page_label)
        pager_layout.addWidget(self.next_btn)
        pager_layout.addWidget(self.page_spin)
        pager_layout.addWidget(self.jump_btn)
        pager_layout.addStretch()

        self.export_csv_btn = QtWidgets.QPushButton("Export CSV")
        self.export_csv_btn.setObjectName("secondaryBtn")
        self.export_pdf_btn = QtWidgets.QPushButton("Export PDF")
        self.export_pdf_btn.setObjectName("secondaryBtn")
        self.refresh_btn = QtWidgets.QPushButton("Refresh")
        pager_layout.addWidget(self.export_csv_btn)
        pager_layout.addWidget(self.export_pdf_btn)
        pager_layout.addWidget(self.refresh_btn)

        if self._is_superadmin():
            self.clear_all_btn = QtWidgets.QPushButton("Clear All Audit Logs")
            self.clear_all_btn.setObjectName("dangerBtn")
            pager_layout.addWidget(self.clear_all_btn)
        else:
            self.clear_all_btn = None

        layout.addLayout(pager_layout)

    def _filter_input(self, layout, placeholder):
        field = QtWidgets.QLineEdit()
        field.setPlaceholderText(placeholder)
        layout.addWidget(field)
        return field

    def _apply_styles(self):
        self.setStyleSheet("""
            QWidget {
                color: #f8fafc;
                font-family: 'Segoe UI', -apple-system, sans-serif;
            }
            QLabel#auditPageTitle {
                font-size: 20px;
                font-weight: bold;
                color: #f8fafc;
            }
            QLabel#auditSectionLabel {
                font-size: 11px;
                font-weight: bold;
                color: #94a3b8;
                letter-spacing: 0.5px;
            }
            QLabel#auditStatsLabel {
                color: #94a3b8;
                font-size: 12px;
            }
            QFrame#auditFilterCard {
                background-color: #1e293b;
                border: 1px solid #334155;
                border-radius: 8px;
            }
            QLineEdit, QComboBox, QSpinBox {
                background-color: #0f172a;
                border: 1px solid #334155;
                border-radius: 6px;
                padding: 6px 10px;
                color: #f8fafc;
                font-size: 12px;
                min-height: 18px;
            }
            QLineEdit:focus, QComboBox:focus, QSpinBox:focus {
                border-color: #3b82f6;
            }
            QPushButton {
                background-color: #3b82f6;
                color: white;
                border: none;
                border-radius: 6px;
                padding: 8px 16px;
                font-weight: bold;
                font-size: 12px;
            }
            QPushButton:hover {
                background-color: #2563eb;
            }
            QPushButton#secondaryBtn {
                background-color: #334155;
                border: 1px solid #475569;
            }
            QPushButton#secondaryBtn:hover {
                background-color: #475569;
            }
            QPushButton#sourceToggleActive:checked,
            QPushButton#sourceToggleArchived:checked {
                background-color: #2563eb;
                border: 1px solid #3b82f6;
            }
            QPushButton#sourceToggleActive,
            QPushButton#sourceToggleArchived {
                background-color: #1e293b;
                border: 1px solid #334155;
                min-width: 120px;
            }
            QPushButton#dangerBtn {
                background-color: #ef4444;
                border: 1px solid #dc2626;
            }
            QPushButton#dangerBtn:hover {
                background-color: #dc2626;
            }
        """)

    def _wire_signals(self):
        self.search_btn.clicked.connect(self._reset_and_load)
        self.clear_btn.clicked.connect(self._clear_filters)
        self.refresh_btn.clicked.connect(self.load_logs)
        self.prev_btn.clicked.connect(self._prev_page)
        self.next_btn.clicked.connect(self._next_page)
        self.jump_btn.clicked.connect(self._jump_to_page)
        self.export_csv_btn.clicked.connect(self.export_csv)
        self.export_pdf_btn.clicked.connect(self.export_pdf)
        if self.clear_all_btn is not None:
            self.clear_all_btn.clicked.connect(self.clear_all_audit_logs)
        self.active_btn.clicked.connect(lambda: self._switch_source(True))
        self.archived_btn.clicked.connect(lambda: self._switch_source(False))
        self.result_filter.currentIndexChanged.connect(self._reset_and_load)
        self.range_filter.currentIndexChanged.connect(self._reset_and_load)
        self.sort_filter.currentIndexChanged.connect(self._reset_and_load)

        for field in (
            self.username_filter,
            self.role_filter,
            self.action_filter,
            self.date_filter,
            self.timestamp_filter,
            self.machine_filter,
            self.session_filter,
            self.os_user_filter,
        ):
            field.returnPressed.connect(self._reset_and_load)

        self.audit.audit_record_created.connect(self.load_logs)

    def _is_superadmin(self):
        return (self.current_user or {}).get("role", "").lower() == "superadmin"

    def clear_all_audit_logs(self):
        if not self._is_superadmin():
            CustomDialog.warning(
                self,
                "Access Denied",
                "You do not have permission to clear audit logs.",
                description="Only Super Admin users may perform this action.",
            )
            return

        reply = CustomDialog.question(
            self,
            "Clear All Audit Logs",
            "You are about to permanently delete every audit log record.",
            description=(
                "This action cannot be undone.\n\n"
                "This operation should only be performed for database maintenance "
                "or system reset."
            ),
            buttons=["Clear All Audit Logs", "Cancel"],
            default_button="Cancel",
        )
        if reply != CustomDialog.Yes:
            return

        username = self.current_user.get("username", "system")
        role = self.current_user.get("role", "")

        try:
            self.archive_service.clear_all_audit_logs(
                username=username,
                role=role,
                reason="Manual Maintenance",
            )
            self.current_page = 0
            self.load_logs()
            CustomDialog.success(
                self,
                "Audit Logs Cleared",
                "All audit log records have been permanently deleted.",
                description=(
                    "Active and archived audit tables are now empty. "
                    "New audit records will start from ID 1."
                ),
            )
        except AuditClearPermissionError:
            CustomDialog.warning(
                self,
                "Access Denied",
                "You do not have permission to clear audit logs.",
                description="Only Super Admin users may perform this action.",
            )
        except Exception as exc:
            CustomDialog.critical(
                self,
                "Clear Failed",
                "Could not clear audit logs. No records were deleted.",
                details=str(exc),
            )

    def _switch_source(self, active):
        self.viewing_active = active
        self.active_btn.setChecked(active)
        self.archived_btn.setChecked(not active)
        self._reset_and_load()

    def _clear_filters(self):
        self.username_filter.clear()
        self.role_filter.clear()
        self.action_filter.clear()
        self.date_filter.clear()
        self.timestamp_filter.clear()
        self.machine_filter.clear()
        self.session_filter.clear()
        self.os_user_filter.clear()
        self.result_filter.setCurrentIndex(0)
        self.range_filter.setCurrentIndex(0)
        self.sort_filter.setCurrentIndex(0)
        self._reset_and_load()

    def _reset_and_load(self):
        self.current_page = 0
        self.load_logs()

    def _prev_page(self):
        if self.current_page > 0:
            self.current_page -= 1
            self.load_logs()

    def _next_page(self):
        max_page = max(0, (self.total_records - 1) // PAGE_SIZE)
        if self.current_page < max_page:
            self.current_page += 1
            self.load_logs()

    def _jump_to_page(self):
        target = self.page_spin.value() - 1
        max_page = max(0, (self.total_records - 1) // PAGE_SIZE)
        self.current_page = max(0, min(target, max_page))
        self.load_logs()

    def _current_filters(self):
        return {
            "username": self.username_filter.text(),
            "role": self.role_filter.text(),
            "action": self.action_filter.text(),
            "result": self.result_filter.currentText(),
            "machine": self.machine_filter.text(),
            "session": self.session_filter.text(),
            "os_user": self.os_user_filter.text(),
            "date": self.date_filter.text(),
            "timestamp": self.timestamp_filter.text(),
            "date_range": self.range_filter.currentText(),
        }

    def load_logs(self):
        filters = self._current_filters()
        order_by = AuditArchiveService.order_clause(self.sort_filter.currentText())

        stats = self.archive_service.get_stats()
        self.active_total = stats["active_count"]
        self.archived_total = stats["archived_count"]
        self.stats_label.setText(
            f"Total Active Records: {self.active_total:,}  |  "
            f"Total Archived Records: {self.archived_total:,}  |  "
            f"Maximum Active Records: {MAX_ACTIVE_RECORDS:,}"
        )

        self.total_records = self.archive_service.count_records(
            active=self.viewing_active,
            filters=filters,
        )

        rows = self.archive_service.fetch_page(
            active=self.viewing_active,
            filters=filters,
            page=self.current_page,
            page_size=PAGE_SIZE,
            order_by=order_by,
        )

        self.table.setRowCount(len(rows))
        for row_idx, record in enumerate(rows):
            display_values = [
                record[1],
                record[2],
                record[3],
                record[4],
                record[5],
                record[6],
                record[7],
                record[8],
                record[9],
                record[10],
            ]
            for col, value in enumerate(display_values):
                text = str(value) if value is not None else ""
                if col == 8 and text:
                    text = text[:8] + "..."
                self.table.setItem(
                    row_idx,
                    col,
                    QtWidgets.QTableWidgetItem(text),
                )

        total_pages = max(1, (self.total_records + PAGE_SIZE - 1) // PAGE_SIZE)
        source_name = "Active" if self.viewing_active else "Archived"
        self.page_label.setText(
            f"Page {self.current_page + 1} of {total_pages}"
        )
        self.total_label.setText(
            f"{self.total_records:,} {source_name.lower()} records"
        )
        self.page_spin.setMaximum(total_pages)
        self.page_spin.setValue(self.current_page + 1)
        self.prev_btn.setEnabled(self.current_page > 0)
        self.next_btn.setEnabled(self.current_page < total_pages - 1)

    def export_csv(self):
        filters = self._current_filters()
        order_by = AuditArchiveService.order_clause(self.sort_filter.currentText())
        source = "active" if self.viewing_active else "archived"
        rows = self.archive_service.fetch_all_for_export(
            active=self.viewing_active,
            filters=filters,
            order_by=order_by,
        )
        if not rows:
            CustomDialog.information(
                self,
                "Export CSV",
                "No audit records match the current filters.",
            )
            return

        default_name = f"audit_{source}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
        file_path, _ = QtWidgets.QFileDialog.getSaveFileName(
            self,
            "Export Audit Logs CSV",
            default_name,
            "CSV Files (*.csv);;All Files (*)",
        )
        if not file_path:
            return

        try:
            with open(file_path, "w", newline="", encoding="utf-8") as handle:
                writer = csv.writer(handle)
                writer.writerow(
                    ["ID"] + TABLE_HEADERS + ["Session Duration", "Details"]
                )
                for record in rows:
                    writer.writerow(record)
            CustomDialog.success(
                self,
                "Export Complete",
                f"Exported {len(rows)} audit records to CSV.",
                description=file_path,
            )
        except Exception as exc:
            CustomDialog.critical(
                self,
                "Export Failed",
                "Could not export audit logs to CSV.",
                details=str(exc),
            )

    def export_pdf(self):
        try:
            from reportlab.lib import colors
            from reportlab.lib.pagesizes import landscape, letter
            from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
            from reportlab.lib.styles import getSampleStyleSheet
        except ImportError as exc:
            CustomDialog.critical(
                self,
                "Export Failed",
                "ReportLab is required for PDF export.",
                details=str(exc),
            )
            return

        filters = self._current_filters()
        order_by = AuditArchiveService.order_clause(self.sort_filter.currentText())
        source = "active" if self.viewing_active else "archived"
        rows = self.archive_service.fetch_all_for_export(
            active=self.viewing_active,
            filters=filters,
            order_by=order_by,
        )
        if not rows:
            CustomDialog.information(
                self,
                "Export PDF",
                "No audit records match the current filters.",
            )
            return

        default_name = f"audit_{source}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf"
        file_path, _ = QtWidgets.QFileDialog.getSaveFileName(
            self,
            "Export Audit Logs PDF",
            default_name,
            "PDF Files (*.pdf);;All Files (*)",
        )
        if not file_path:
            return

        try:
            doc = SimpleDocTemplate(file_path, pagesize=landscape(letter))
            styles = getSampleStyleSheet()
            elements = [
                Paragraph(
                    f"Audit Logs Export ({source.title()})",
                    styles["Title"],
                ),
                Paragraph(
                    f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}  |  "
                    f"Records: {len(rows)}",
                    styles["Normal"],
                ),
                Spacer(1, 12),
            ]

            table_data = [["ID"] + TABLE_HEADERS]
            for record in rows:
                table_data.append(
                    [str(value) if value is not None else "" for value in record[:11]]
                )

            table = Table(table_data, repeatRows=1)
            table.setStyle(
                TableStyle(
                    [
                        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#3e403f")),
                        ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
                        ("GRID", (0, 0), (-1, -1), 0.25, colors.HexColor("#272829")),
                        ("FONTSIZE", (0, 0), (-1, -1), 7),
                        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [
                            colors.HexColor("#aab2bf"),
                            colors.HexColor("#cad2e6"),
                        ]),
                    ]
                )
            )
            elements.append(table)
            doc.build(elements)

            CustomDialog.success(
                self,
                "Export Complete",
                f"Exported {len(rows)} audit records to PDF.",
                description=file_path,
            )
        except Exception as exc:
            CustomDialog.critical(
                self,
                "Export Failed",
                "Could not export audit logs to PDF.",
                details=str(exc),
            )
