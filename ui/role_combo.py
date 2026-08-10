from PyQt5 import QtCore, QtGui, QtWidgets

ROLE_DISPLAY = {
    "superadmin": "Super Admin",
    "admin": "Admin",
    "engineer": "Engineer",
    "operator": "Operator",
    "viewer": "Viewer",
}

# Roles assignable when creating a new user (Super Admin is system-managed).
CREATE_ROLE_VALUES = ["admin", "engineer", "operator", "viewer"]

COMBO_HEIGHT = 44
ITEM_HEIGHT = 38
PADDING_LEFT = 12
BORDER_RADIUS = 8

COLOR_BG = QtGui.QColor("#1E293B")
COLOR_BORDER = QtGui.QColor("#334155")
COLOR_HOVER = QtGui.QColor("#2563EB")
COLOR_SELECTED = QtGui.QColor("#3B82F6")
COLOR_TEXT = QtGui.QColor("#FFFFFF")


def role_display_name(role_value):
    return ROLE_DISPLAY.get(role_value, str(role_value).replace("_", " ").title())


class RoleComboDelegate(QtWidgets.QStyledItemDelegate):
    """Enterprise-style list item rendering with animated hover."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self._hover_row = -1
        self._hover_progress = 0.0
        self._anim = QtCore.QVariantAnimation(self)
        self._anim.setDuration(140)
        self._anim.setEasingCurve(QtCore.QEasingCurve.OutCubic)
        self._anim.valueChanged.connect(self._on_anim_value)

    def _on_anim_value(self, value):
        self._hover_progress = float(value)
        view = self.parent()
        if isinstance(view, QtWidgets.QAbstractItemView):
            view.viewport().update()

    def set_hover_row(self, row):
        if row == self._hover_row:
            return
        self._hover_row = row
        self._anim.stop()
        if row >= 0:
            self._anim.setStartValue(0.0)
            self._anim.setEndValue(1.0)
        else:
            self._anim.setStartValue(self._hover_progress)
            self._anim.setEndValue(0.0)
        self._anim.start()

    @staticmethod
    def _blend(base, overlay, factor):
        factor = max(0.0, min(1.0, factor))
        return QtGui.QColor(
            int(base.red() + (overlay.red() - base.red()) * factor),
            int(base.green() + (overlay.green() - base.green()) * factor),
            int(base.blue() + (overlay.blue() - base.blue()) * factor),
        )

    def sizeHint(self, option, index):
        return QtCore.QSize(option.rect.width(), ITEM_HEIGHT)

    def paint(self, painter, option, index):
        painter.save()
        painter.setRenderHint(QtGui.QPainter.Antialiasing)

        rect = option.rect.adjusted(6, 3, -6, -3)
        selected = bool(option.state & QtWidgets.QStyle.State_Selected)
        keyboard_focus = bool(option.state & QtWidgets.QStyle.State_HasFocus)
        is_active = selected or keyboard_focus
        is_hover = index.row() == self._hover_row and not is_active

        if is_active:
            bg = COLOR_SELECTED
        elif is_hover:
            bg = self._blend(COLOR_BG, COLOR_HOVER, self._hover_progress)
        else:
            bg = COLOR_BG

        painter.setPen(QtCore.Qt.NoPen)
        painter.setBrush(bg)
        painter.drawRoundedRect(rect, 6, 6)

        font = QtGui.QFont("Segoe UI", 10)
        font.setWeight(QtGui.QFont.Medium)
        if is_active:
            font.setWeight(QtGui.QFont.DemiBold)
        painter.setFont(font)
        painter.setPen(COLOR_TEXT)

        text_rect = rect.adjusted(PADDING_LEFT, 0, -PADDING_LEFT, 0)
        painter.drawText(
            text_rect,
            QtCore.Qt.AlignVCenter | QtCore.Qt.AlignLeft,
            index.data(QtCore.Qt.DisplayRole) or "",
        )
        painter.restore()


class RoleComboBox(QtWidgets.QComboBox):
    """Dark-theme role selector with consistent popup sizing and keyboard support."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("roleCombo")
        self.setMinimumHeight(COMBO_HEIGHT)
        self.setMaximumHeight(COMBO_HEIGHT)
        self.setCursor(QtCore.Qt.PointingHandCursor)
        self.setFocusPolicy(QtCore.Qt.StrongFocus)
        self.setSizeAdjustPolicy(QtWidgets.QComboBox.AdjustToContents)

        font = QtGui.QFont("Segoe UI", 10)
        font.setWeight(QtGui.QFont.Medium)
        self.setFont(font)

        for value in CREATE_ROLE_VALUES:
            self.addItem(role_display_name(value), value)

        self._delegate = RoleComboDelegate(self)
        self._popup_open = False
        self._setup_popup_view()
        self._apply_stylesheet()

    def _setup_popup_view(self):
        view = QtWidgets.QListView(self)
        view.setObjectName("roleComboList")
        view.setFrameShape(QtWidgets.QFrame.NoFrame)
        view.setUniformItemSizes(True)
        view.setSpacing(2)
        view.setHorizontalScrollBarPolicy(QtCore.Qt.ScrollBarAlwaysOff)
        view.setVerticalScrollMode(QtWidgets.QAbstractItemView.ScrollPerPixel)
        view.setMouseTracking(True)
        view.setAttribute(QtCore.Qt.WA_StyledBackground, True)
        view.setItemDelegate(self._delegate)
        view.setMinimumWidth(self.width())

        palette = view.palette()
        palette.setColor(QtGui.QPalette.Base, COLOR_BG)
        palette.setColor(QtGui.QPalette.Text, COLOR_TEXT)
        palette.setColor(QtGui.QPalette.Highlight, COLOR_SELECTED)
        palette.setColor(QtGui.QPalette.HighlightedText, COLOR_TEXT)
        view.setPalette(palette)

        view.entered.connect(self._on_item_entered)
        view.viewport().installEventFilter(self)
        self.setView(view)

    def _on_item_entered(self, index):
        self._delegate.set_hover_row(index.row() if index.isValid() else -1)

    def eventFilter(self, obj, event):
        if obj is self.view().viewport():
            if event.type() == QtCore.QEvent.Leave:
                self._delegate.set_hover_row(-1)
        return super().eventFilter(obj, event)

    def showPopup(self):
        self._popup_open = True
        super().showPopup()
        popup = self.view().window()
        if popup is not None:
            popup.setFixedWidth(self.width())
        list_view = self.view()
        if list_view is not None:
            list_view.setMinimumWidth(self.width())

    def hidePopup(self):
        self._popup_open = False
        self._delegate.set_hover_row(-1)
        super().hidePopup()

    def selected_role_value(self):
        value = self.currentData()
        if value:
            return value
        text = self.currentText().strip().lower().replace(" ", "")
        if text == "superadmin":
            return "superadmin"
        return text

    def _apply_stylesheet(self):
        self.setStyleSheet(f"""
            QComboBox#roleCombo {{
                background-color: #1E293B;
                border: 1px solid #334155;
                border-radius: {BORDER_RADIUS}px;
                padding: 0 44px 0 {PADDING_LEFT}px;
                color: #FFFFFF;
                font-family: 'Segoe UI', -apple-system, sans-serif;
                font-size: 14px;
                font-weight: 500;
                min-height: {COMBO_HEIGHT}px;
                max-height: {COMBO_HEIGHT}px;
            }}
            QComboBox#roleCombo:hover {{
                border-color: #475569;
            }}
            QComboBox#roleCombo:focus,
            QComboBox#roleCombo:on {{
                border: 1px solid #3B82F6;
            }}
            QComboBox#roleCombo::drop-down {{
                subcontrol-origin: padding;
                subcontrol-position: center right;
                width: 44px;
                border: none;
                border-left: 1px solid #334155;
                border-top-right-radius: {BORDER_RADIUS}px;
                border-bottom-right-radius: {BORDER_RADIUS}px;
                background: transparent;
                padding-right: 12px;
            }}
            QComboBox#roleCombo::down-arrow {{
                width: 0;
                height: 0;
                border: none;
                image: none;
            }}
            QComboBox#roleCombo:on::drop-down {{
                border-left-color: #3B82F6;
            }}
            QListView#roleComboList {{
                background-color: #1E293B;
                color: #FFFFFF;
                border: 1px solid #334155;
                border-radius: {BORDER_RADIUS}px;
                padding: 4px;
                outline: none;
            }}
        """)

    def paintEvent(self, event):
        super().paintEvent(event)
        opt = QtWidgets.QStyleOptionComboBox()
        self.initStyleOption(opt)
        arrow_rect = self.style().subControlRect(
            QtWidgets.QStyle.CC_ComboBox,
            opt,
            QtWidgets.QStyle.SC_ComboBoxArrow,
            self,
        )
        if not arrow_rect.isValid():
            return
        painter = QtGui.QPainter(self)
        painter.setRenderHint(QtGui.QPainter.Antialiasing)
        color = QtGui.QColor("#94A3B8")
        if self.hasFocus() or self._popup_open:
            color = QtGui.QColor("#FFFFFF")
        self._paint_chevron(painter, arrow_rect, color)
        painter.end()

    @staticmethod
    def _paint_chevron(painter, rect, color):
        cx = rect.center().x()
        cy = rect.center().y() + 1
        path = QtGui.QPainterPath()
        path.moveTo(cx - 5, cy - 2)
        path.lineTo(cx + 5, cy - 2)
        path.lineTo(cx, cy + 4)
        path.closeSubpath()
        painter.setPen(QtCore.Qt.NoPen)
        painter.setBrush(color)
        painter.drawPath(path)
