import os
import sys
import ctypes
from PyQt5.QtWidgets import QApplication
from PyQt5.QtGui import QIcon
from ui.main_activity import MainWindow

def main():
    # Weird way to set icon in Windows
    if sys.platform == 'win32':
        myappid = 'me.thenano.image2gcode'
        ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID(myappid)
    
    app = QApplication(sys.argv)
    # Set the application icon for taskbar and window
    icon_path = os.path.join(os.path.dirname(__file__), 'attachments', 'favicon.ico')
    app.setWindowIcon(QIcon(icon_path))
    window = MainWindow()
    window.setWindowIcon(QIcon(icon_path))
    window.show()
    sys.exit(app.exec_())

if __name__ == "__main__":
    main()