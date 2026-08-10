from PyQt5 import QtCore, QtGui, QtWidgets


def apply_enterprise_table_style(table, object_name="enterpriseTable", row_height=40):
    """Apply seamless dark industrial styling to a QTableWidget."""
    table.setObjectName(object_name)
    table.setShowGrid(True)
    table.setFrameShape(QtWidgets.QFrame.NoFrame)
    table.setAttribute(QtCore.Qt.WA_StyledBackground, True)

    viewport = table.viewport()
    viewport.setAttribute(QtCore.Qt.WA_StyledBackground, True)
    viewport.setAutoFillBackground(True)

    palette = table.palette()
    palette.setColor(QtGui.QPalette.Base, QtGui.QColor("#1E293B"))
    palette.setColor(QtGui.QPalette.AlternateBase, QtGui.QColor("#0F172A"))
    palette.setColor(QtGui.QPalette.Window, QtGui.QColor("#1E293B"))
    palette.setColor(QtGui.QPalette.Button, QtGui.QColor("#0F172A"))
    palette.setColor(QtGui.QPalette.Text, QtGui.QColor("#FFFFFF"))
    palette.setColor(QtGui.QPalette.Highlight, QtGui.QColor("#3B82F6"))
    palette.setColor(QtGui.QPalette.HighlightedText, QtGui.QColor("#FFFFFF"))
    table.setPalette(palette)
    viewport.setPalette(palette)

    header_palette = QtGui.QPalette(palette)
    header_palette.setColor(QtGui.QPalette.Window, QtGui.QColor("#0F172A"))
    header_palette.setColor(QtGui.QPalette.Button, QtGui.QColor("#0F172A"))
    header_palette.setColor(QtGui.QPalette.Base, QtGui.QColor("#0F172A"))

    vertical_header = table.verticalHeader()
    horizontal_header = table.horizontalHeader()

    for header in (horizontal_header, vertical_header):
        header.setAttribute(QtCore.Qt.WA_StyledBackground, True)
        header.setAutoFillBackground(True)
        header.setPalette(header_palette)
        header.setHighlightSections(False)

    vertical_header.setVisible(True)
    vertical_header.setDefaultSectionSize(row_height)
    vertical_header.setSectionResizeMode(QtWidgets.QHeaderView.Fixed)

    vertical_header.setStyleSheet("""
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

    horizontal_header.setStyleSheet("""
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
            font-size: 12px;
            font-weight: bold;
        }
    """)

    viewport.setStyleSheet("background-color: #1E293B;")

    table.setStyleSheet(f"""
        QTableWidget#{object_name} {{
            background-color: #1E293B;
            alternate-background-color: #0F172A;
            gridline-color: #334155;
            color: #FFFFFF;
            border: 1px solid #334155;
            border-radius: 8px;
            outline: none;
        }}
        QTableWidget#{object_name} QAbstractScrollArea {{
            background-color: #1E293B;
            border: none;
        }}
        QTableWidget#{object_name} QAbstractScrollArea::viewport {{
            background-color: #1E293B;
        }}
        QTableWidget#{object_name} QAbstractScrollArea::corner {{
            background-color: #0F172A;
            border: none;
        }}
        QTableWidget#{object_name} QTableCornerButton::section {{
            background-color: #0F172A;
            border: none;
            border-right: 1px solid #334155;
            border-bottom: 1px solid #334155;
        }}
        QTableWidget#{object_name}::item {{
            padding: 8px 12px;
            border: none;
        }}
        QTableWidget#{object_name}::item:alternate {{
            background-color: #0F172A;
        }}
        QTableWidget#{object_name}::item:hover {{
            background-color: #2563EB;
            color: #FFFFFF;
        }}
        QTableWidget#{object_name}::item:selected {{
            background-color: #3B82F6;
            color: #FFFFFF;
        }}
        QTableWidget#{object_name} QScrollBar:vertical {{
            background: #0F172A;
            width: 10px;
            margin: 0;
            border: none;
        }}
        QTableWidget#{object_name} QScrollBar::handle:vertical {{
            background: #334155;
            min-height: 24px;
            border-radius: 5px;
        }}
        QTableWidget#{object_name} QScrollBar::add-line:vertical,
        QTableWidget#{object_name} QScrollBar::sub-line:vertical {{
            height: 0;
            border: none;
            background: none;
        }}
        QTableWidget#{object_name} QScrollBar:horizontal {{
            background: #0F172A;
            height: 10px;
            margin: 0;
            border: none;
        }}
        QTableWidget#{object_name} QScrollBar::handle:horizontal {{
            background: #334155;
            min-width: 24px;
            border-radius: 5px;
        }}
        QTableWidget#{object_name} QScrollBar::add-line:horizontal,
        QTableWidget#{object_name} QScrollBar::sub-line:horizontal {{
            width: 0;
            border: none;
            background: none;
        }}
    """)


def apply_dark_panel_style(widget, background="#1E293B"):
    """Ensure stacked/placeholder panels use the dark theme background."""
    widget.setAttribute(QtCore.Qt.WA_StyledBackground, True)
    widget.setAutoFillBackground(True)
    palette = widget.palette()
    palette.setColor(QtGui.QPalette.Window, QtGui.QColor(background))
    widget.setPalette(palette)
    widget.setStyleSheet(f"background-color: {background};")
