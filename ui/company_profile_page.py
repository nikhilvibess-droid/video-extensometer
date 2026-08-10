from PyQt5 import QtWidgets, QtCore, QtGui

from database.company_manager import CompanyManager, DEFAULT_PROFILE
from database.audit_manager import AuditManager
from ui.custom_dialog import CustomDialog


class CompanyProfilePage(QtWidgets.QWidget):

    def __init__(self, current_user=None, parent=None):
        super().__init__(parent)
        self.current_user = current_user or {}
        self.company = CompanyManager.get_instance()
        self.audit = AuditManager.get_instance()
        self._pending_logo_path = None
        self._remove_logo = False
        self._build_ui()
        self._apply_styles()
        self.load_profile()

    def _build_ui(self):
        outer = QtWidgets.QVBoxLayout(self)
        outer.setContentsMargins(0, 0, 0, 0)
        outer.setSpacing(0)

        scroll = QtWidgets.QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QtWidgets.QFrame.NoFrame)
        scroll.setHorizontalScrollBarPolicy(QtCore.Qt.ScrollBarAlwaysOff)

        content = QtWidgets.QWidget()
        layout = QtWidgets.QVBoxLayout(content)
        layout.setContentsMargins(0, 0, 8, 0)
        layout.setSpacing(16)

        layout.addWidget(self._build_branding_card())
        layout.addWidget(self._build_info_card())
        layout.addWidget(self._build_pdf_card())
        layout.addWidget(self._build_action_row())
        layout.addStretch()

        scroll.setWidget(content)
        outer.addWidget(scroll)

    def _card(self, title):
        card = QtWidgets.QFrame()
        card.setObjectName("companyCard")
        card_layout = QtWidgets.QVBoxLayout(card)
        card_layout.setContentsMargins(20, 18, 20, 18)
        card_layout.setSpacing(14)
        header = QtWidgets.QLabel(title)
        header.setObjectName("companyCardTitle")
        card_layout.addWidget(header)
        return card, card_layout

    def _build_branding_card(self):
        card, card_layout = self._card("1. Company Branding")

        logo_row = QtWidgets.QHBoxLayout()
        self.logo_preview = QtWidgets.QLabel()
        self.logo_preview.setObjectName("logoPreview")
        self.logo_preview.setFixedSize(220, 88)
        self.logo_preview.setAlignment(QtCore.Qt.AlignCenter)
        self.logo_preview.setText("Logo Preview")

        logo_btns = QtWidgets.QVBoxLayout()
        self.upload_logo_btn = QtWidgets.QPushButton("Upload Logo")
        self.remove_logo_btn = QtWidgets.QPushButton("Remove Logo")
        self.remove_logo_btn.setObjectName("secondaryBtn")
        logo_btns.addWidget(self.upload_logo_btn)
        logo_btns.addWidget(self.remove_logo_btn)
        logo_btns.addStretch()

        logo_row.addWidget(self.logo_preview)
        logo_row.addLayout(logo_btns)
        logo_row.addStretch()
        card_layout.addLayout(logo_row)

        hint = QtWidgets.QLabel("Supported: PNG, JPG, SVG  |  Maximum: 5 MB")
        hint.setObjectName("hintLabel")
        card_layout.addWidget(hint)
        return card

    def _build_info_card(self):
        card, card_layout = self._card("2. Company Information")
        form = QtWidgets.QFormLayout()
        form.setSpacing(10)
        form.setLabelAlignment(QtCore.Qt.AlignLeft)

        self.company_name_input = QtWidgets.QLineEdit()
        self.address_input = QtWidgets.QLineEdit()
        self.city_input = QtWidgets.QLineEdit()
        self.state_input = QtWidgets.QLineEdit()
        self.country_input = QtWidgets.QLineEdit()
        self.postal_code_input = QtWidgets.QLineEdit()
        self.phone_input = QtWidgets.QLineEdit()
        self.email_input = QtWidgets.QLineEdit()
        self.website_input = QtWidgets.QLineEdit()
        self.authorized_by_input = QtWidgets.QLineEdit()
        self.gst_number_input = QtWidgets.QLineEdit()

        for label, widget in (
            ("Company Name *", self.company_name_input),
            ("Address", self.address_input),
            ("City", self.city_input),
            ("State", self.state_input),
            ("Country", self.country_input),
            ("Postal Code", self.postal_code_input),
            ("Phone", self.phone_input),
            ("Email", self.email_input),
            ("Website", self.website_input),
            ("Authorized By", self.authorized_by_input),
            ("GST Number", self.gst_number_input),
        ):
            form.addRow(self._form_label(label), widget)

        card_layout.addLayout(form)
        return card

    def _build_pdf_card(self):
        card, card_layout = self._card("3. PDF Settings")
        form = QtWidgets.QFormLayout()
        form.setSpacing(10)
        self.report_title_input = QtWidgets.QLineEdit()
        self.footer_text_input = QtWidgets.QPlainTextEdit()
        self.footer_text_input.setFixedHeight(80)
        form.addRow(self._form_label("Report Title"), self.report_title_input)
        form.addRow(self._form_label("Footer Text"), self.footer_text_input)
        card_layout.addLayout(form)
        return card

    def _build_action_row(self):
        row = QtWidgets.QHBoxLayout()
        row.setSpacing(12)
        self.save_btn = QtWidgets.QPushButton("Save")
        self.reset_btn = QtWidgets.QPushButton("Reset")
        self.reset_btn.setObjectName("secondaryBtn")
        self.restore_btn = QtWidgets.QPushButton("Restore Default")
        self.restore_btn.setObjectName("secondaryBtn")
        self.preview_btn = QtWidgets.QPushButton("Preview PDF Header")
        self.preview_btn.setObjectName("secondaryBtn")

        row.addWidget(self.save_btn)
        row.addWidget(self.reset_btn)
        row.addWidget(self.restore_btn)
        row.addStretch()
        row.addWidget(self.preview_btn)
        return self._wrap_layout(row)

    def _wrap_layout(self, layout):
        wrapper = QtWidgets.QWidget()
        wrapper.setLayout(layout)
        return wrapper

    def _form_label(self, text):
        label = QtWidgets.QLabel(text)
        label.setObjectName("formLabel")
        return label

    def _apply_styles(self):
        self.setStyleSheet("""
            QFrame#companyCard {
                background-color: #1e293b;
                border: 1px solid #334155;
                border-radius: 10px;
            }
            QLabel#companyCardTitle {
                font-size: 14px;
                font-weight: bold;
                color: #38bdf8;
                letter-spacing: 0.4px;
            }
            QLabel#formLabel {
                font-size: 12px;
                color: #94a3b8;
                font-weight: bold;
            }
            QLabel#hintLabel {
                font-size: 11px;
                color: #64748b;
            }
            QLabel#logoPreview {
                background-color: #0f172a;
                border: 1px dashed #475569;
                border-radius: 8px;
                color: #64748b;
            }
            QLineEdit, QPlainTextEdit {
                background-color: #0f172a;
                border: 1px solid #334155;
                border-radius: 6px;
                padding: 8px 10px;
                color: #f8fafc;
                font-size: 13px;
            }
            QLineEdit:focus, QPlainTextEdit:focus {
                border-color: #3b82f6;
            }
            QPushButton {
                background-color: #3b82f6;
                color: white;
                border: none;
                border-radius: 6px;
                padding: 10px 18px;
                font-weight: bold;
                font-size: 13px;
            }
            QPushButton:hover { background-color: #2563eb; }
            QPushButton#secondaryBtn {
                background-color: #334155;
                border: 1px solid #475569;
            }
            QPushButton#secondaryBtn:hover { background-color: #475569; }
        """)

        self.upload_logo_btn.clicked.connect(self._upload_logo)
        self.remove_logo_btn.clicked.connect(self._remove_logo_clicked)
        self.save_btn.clicked.connect(self.save_profile)
        self.reset_btn.clicked.connect(self.load_profile)
        self.restore_btn.clicked.connect(self.restore_defaults)
        self.preview_btn.clicked.connect(self.preview_pdf_header)

    def _set_logo_preview(self, animate=False):
        pixmap = self.company.get_logo_pixmap(210, 78)
        if pixmap and not pixmap.isNull():
            self.logo_preview.setPixmap(pixmap)
            self.logo_preview.setText("")
        else:
            self.logo_preview.setPixmap(QtGui.QPixmap())
            self.logo_preview.setText("Logo Preview")

        if animate:
            effect = QtWidgets.QGraphicsOpacityEffect(self.logo_preview)
            self.logo_preview.setGraphicsEffect(effect)
            anim = QtCore.QPropertyAnimation(effect, b"opacity")
            anim.setDuration(250)
            anim.setStartValue(0.2)
            anim.setEndValue(1.0)
            anim.start(QtCore.QAbstractAnimation.DeleteWhenStopped)
            self._logo_anim = anim

    def _upload_logo(self):
        file_path, _ = QtWidgets.QFileDialog.getOpenFileName(
            self,
            "Upload Company Logo",
            "",
            "Images (*.png *.jpg *.jpeg *.svg);;All Files (*)",
        )
        if not file_path:
            return
        error = self.company.validate_logo_file(file_path)
        if error:
            CustomDialog.warning(self, "Invalid Logo", error, buttons=["OK"])
            return
        self._pending_logo_path = file_path
        self._remove_logo = False
        preview = self.company.get_logo_pixmap(210, 78)
        if file_path.lower().endswith(".svg"):
            from PyQt5.QtSvg import QSvgRenderer
            renderer = QSvgRenderer(file_path)
            if renderer.isValid():
                pixmap = QtGui.QPixmap(210, 78)
                pixmap.fill(QtCore.Qt.transparent)
                painter = QtGui.QPainter(pixmap)
                renderer.render(painter)
                painter.end()
                preview = pixmap
        else:
            preview = QtGui.QPixmap(file_path).scaled(
                210, 78, QtCore.Qt.KeepAspectRatio, QtCore.Qt.SmoothTransformation
            )
        if preview and not preview.isNull():
            self.logo_preview.setPixmap(preview)
            self.logo_preview.setText("")
        self._set_logo_preview(animate=True)

    def _remove_logo_clicked(self):
        self._pending_logo_path = None
        self._remove_logo = True
        self._set_logo_preview(animate=True)

    def _collect_form_data(self):
        return {
            "company_name": self.company_name_input.text().strip(),
            "address": self.address_input.text().strip(),
            "city": self.city_input.text().strip(),
            "state": self.state_input.text().strip(),
            "country": self.country_input.text().strip(),
            "postal_code": self.postal_code_input.text().strip(),
            "phone": self.phone_input.text().strip(),
            "email": self.email_input.text().strip(),
            "website": self.website_input.text().strip(),
            "authorized_by": self.authorized_by_input.text().strip(),
            "gst_number": self.gst_number_input.text().strip(),
            "report_title": self.report_title_input.text().strip(),
            "footer_text": self.footer_text_input.toPlainText().strip(),
            "company_logo": self.company.get_profile().get("company_logo", ""),
        }

    def load_profile(self):
        profile = self.company.get_profile()
        self.company_name_input.setText(profile.get("company_name", ""))
        self.address_input.setText(profile.get("address", ""))
        self.city_input.setText(profile.get("city", ""))
        self.state_input.setText(profile.get("state", ""))
        self.country_input.setText(profile.get("country", ""))
        self.postal_code_input.setText(profile.get("postal_code", ""))
        self.phone_input.setText(profile.get("phone", ""))
        self.email_input.setText(profile.get("email", ""))
        self.website_input.setText(profile.get("website", ""))
        self.authorized_by_input.setText(profile.get("authorized_by", ""))
        self.gst_number_input.setText(profile.get("gst_number", ""))
        self.report_title_input.setText(profile.get("report_title", ""))
        self.footer_text_input.setPlainText(profile.get("footer_text", ""))
        self._pending_logo_path = None
        self._remove_logo = False
        self._set_logo_preview()

    def save_profile(self):
        data = self._collect_form_data()
        try:
            self.company.save_profile(
                data,
                logo_source_path=self._pending_logo_path,
                remove_logo=self._remove_logo,
            )
            actor = self.current_user.get("username", "system")
            actor_role = self.current_user.get("role", "")
            self.audit.log_event(
                action="Company Profile Updated",
                username=actor,
                role=actor_role,
                result="Success",
            )
            self._pending_logo_path = None
            self._remove_logo = False
            self.load_profile()
            CustomDialog.success(
                self,
                "Company Profile Saved",
                "Branding has been updated across the application.",
                buttons=["OK"],
            )
        except ValueError as exc:
            CustomDialog.warning(self, "Validation Error", str(exc), buttons=["OK"])
        except Exception as exc:
            CustomDialog.critical(
                self,
                "Save Failed",
                "Could not save Company Profile. No changes were applied.",
                details=str(exc),
                buttons=["OK"],
            )

    def restore_defaults(self):
        reply = CustomDialog.question(
            self,
            "Restore Default Branding",
            "Restore the default VEX branding profile?",
            description="This will remove custom company information and uploaded logos.",
            buttons=["Restore Default", "Cancel"],
            default_button="Cancel",
        )
        if reply != CustomDialog.Yes:
            return
        try:
            self.company.restore_defaults()
            actor = self.current_user.get("username", "system")
            actor_role = self.current_user.get("role", "")
            self.audit.log_event(
                action="Company Profile Updated",
                username=actor,
                role=actor_role,
                result="Success",
                details="Restored default VEX branding",
            )
            self.load_profile()
            CustomDialog.success(
                self,
                "Defaults Restored",
                "Default VEX branding has been restored.",
                buttons=["OK"],
            )
        except Exception as exc:
            CustomDialog.critical(
                self,
                "Restore Failed",
                "Could not restore default branding.",
                details=str(exc),
                buttons=["OK"],
            )

    def preview_pdf_header(self):
        profile = self._collect_form_data()
        if self._pending_logo_path:
            profile["company_logo"] = self._pending_logo_path

        dialog = QtWidgets.QDialog(self)
        dialog.setWindowTitle("PDF Header Preview")
        dialog.resize(640, 280)
        layout = QtWidgets.QVBoxLayout(dialog)

        header = QtWidgets.QFrame()
        header.setStyleSheet(
            "background-color: #1e3a8a; border-radius: 8px; padding: 16px;"
        )
        header_layout = QtWidgets.QHBoxLayout(header)

        left = QtWidgets.QVBoxLayout()
        logo = QtWidgets.QLabel()
        pixmap = self.company.get_logo_pixmap(180, 60)
        if self._pending_logo_path and self._pending_logo_path.lower().endswith(".svg"):
            from PyQt5.QtSvg import QSvgRenderer
            renderer = QSvgRenderer(self._pending_logo_path)
            if renderer.isValid():
                pm = QtGui.QPixmap(180, 60)
                pm.fill(QtCore.Qt.transparent)
                p = QtGui.QPainter(pm)
                renderer.render(p)
                p.end()
                pixmap = pm
        elif self._pending_logo_path:
            pixmap = QtGui.QPixmap(self._pending_logo_path).scaled(
                180, 60, QtCore.Qt.KeepAspectRatio, QtCore.Qt.SmoothTransformation
            )
        if pixmap and not pixmap.isNull():
            logo.setPixmap(pixmap)
        left.addWidget(logo)

        info = QtWidgets.QLabel(
            f"<b style='color:white;font-size:14px;'>{profile.get('company_name', '')}</b><br>"
            f"<span style='color:#cbd5e1;font-size:10px;'>{self.company.format_address_block(profile).replace(chr(10), '<br>')}</span><br>"
            f"<span style='color:#93c5fd;font-size:10px;'>{self.company.format_contact_line(profile)}</span>"
        )
        info.setWordWrap(True)
        left.addWidget(info)
        header_layout.addLayout(left, 1)

        title = QtWidgets.QLabel(
            f"<div style='color:white;font-size:15px;font-weight:bold;text-align:right;'>"
            f"{profile.get('report_title', DEFAULT_PROFILE['report_title'])}</div>"
        )
        title.setAlignment(QtCore.Qt.AlignRight | QtCore.Qt.AlignVCenter)
        header_layout.addWidget(title, 1)

        layout.addWidget(header)
        footer = QtWidgets.QLabel(
            f"<span style='color:#94a3b8;font-size:11px;'>{profile.get('footer_text', '').replace(chr(10), '<br>')}</span>"
        )
        layout.addWidget(footer)
        close_btn = QtWidgets.QPushButton("Close")
        close_btn.clicked.connect(dialog.accept)
        layout.addWidget(close_btn, alignment=QtCore.Qt.AlignRight)
        dialog.exec_()
