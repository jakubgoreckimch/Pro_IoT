import sys
from PyQt5.QtWidgets import QApplication  # type: ignore
from gui_app import TempHumidityApp

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = TempHumidityApp()
    window.show()
    sys.exit(app.exec_())