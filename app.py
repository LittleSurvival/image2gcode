import sys
from PyQt5.QtWidgets import QApplication
from ui.main_activity import MainWindow

def main():
    app = QApplication(sys.argv)
    #Main GUI(Desktop App)
    window = MainWindow()
    window.show()
    sys.exit(app.exec_())

if __name__ == "__main__":
    main()