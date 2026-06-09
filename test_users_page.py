import sys

from PyQt5.QtWidgets import QApplication

from ui.users_page import UsersPage


app = QApplication(sys.argv)

window = UsersPage()

window.show()

sys.exit(app.exec_())