import sys
import os

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from PyQt6.QtWidgets import QApplication
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QIcon
from gui.main_window import MainWindow


def main():
    if sys.platform == 'win32':
        import ctypes
        ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID('schemacrafter.gui.v1')
    
    app = QApplication(sys.argv)
    app.setStyle('Fusion')
    
    icon_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'SchemCraft.png')
    if os.path.exists(icon_path):
        app.setWindowIcon(QIcon(icon_path))
    
    window = MainWindow()
    if os.path.exists(icon_path):
        window.setWindowIcon(QIcon(icon_path))
    window.show()
    
    sys.exit(app.exec())


if __name__ == '__main__':
    main()
