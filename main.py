import sys
from PyQt5 import QtWidgets
from ui.main_window import MainWindow

if __name__ == "__main__":

    app = QtWidgets.QApplication(sys.argv)

    try:
        window = MainWindow()
        window.show()
        sys.exit(app.exec_())
        
    except Exception as e:
        print(f"[FATAL ERROR] Application crashed: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)