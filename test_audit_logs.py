import sys

from PyQt5.QtWidgets import QApplication

from ui.audit_logs_page import AuditLogsPage

app = QApplication(sys.argv)

window = AuditLogsPage()

window.show()

sys.exit(app.exec_())