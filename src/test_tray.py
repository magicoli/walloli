# test_tray.py

import sys
from PyQt5 import QtWidgets, QtCore, QtGui
import os

# All code comments, user outputs and debugs must be in English. Do not remove this line.
# Some commands are commented out for further development. Do not remove them.

# Définir une fonction de log simple
def log(message):
    print(message)

def main():
    app = QtWidgets.QApplication(sys.argv)
    # app.setQuitOnLastWindowClosed(False)  


    icon_path = os.path.join(os.path.dirname(__file__), 'assets', 'icons', 'tray_icon.png')
    if not os.path.exists(icon_path):
        log(f"Icon path {icon_path} does not exist. Using standard icon.")
        icon = QtWidgets.QApplication.style().standardIcon(QtWidgets.QStyle.SP_ComputerIcon)
    else:
        icon = QtGui.QIcon(icon_path)
        log(f"Using custom tray icon from {icon_path}")

    tray_icon = QtWidgets.QSystemTrayIcon(icon, app)
    tray_menu = QtWidgets.QMenu()

    # Dummy window
    dummy_window = QtWidgets.QWidget()
    dummy_window.setWindowTitle("Dummy Window")
    # dummy_window.setGeometry(0, 0, 0, 0)
    dummy_window.show()

    # Initialiser la barre système
    log("Initializing system tray")

    # Ajouter l'action "Settings"
    settings_action = tray_menu.addAction("Settings")
    def open_settings():
        log("Settings clicked")
        dialog = QtWidgets.QMessageBox()
        dialog.setWindowTitle("Settings")
        dialog.setText("Settings dialog would open here.")
        dialog.exec_()
    settings_action.triggered.connect(open_settings)
    log("Added 'Settings' action to tray menu")

    # Ajouter l'action "Exit"
    exit_action = tray_menu.addAction("Exit")
    exit_action.triggered.connect(app.quit)  # Connexion complète
    log("Added 'Exit' action to tray menu")

    tray_icon.setContextMenu(tray_menu)
    tray_icon.show()
    log("System tray initialized and should be shown but nothing is less certain")

    # **Maintenir une référence à l'icône de la barre système**
    app.tray_icon = tray_icon

    sys.exit(app.exec_())

if __name__ == "__main__":
        main()
