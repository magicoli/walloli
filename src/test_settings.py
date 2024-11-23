# main.py

import sys
from PyQt5 import QtWidgets, QtGui

def log(message):
    print(f"[DEBUG] {message}")

def open_settings():
    log("Preferences clicked")
    dialog = QtWidgets.QMessageBox()
    dialog.setWindowTitle("Settings")
    dialog.setText("Settings dialog would open here.")
    dialog.exec_()

class SettingsController(QtWidgets.QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("WallOli")
        self.setGeometry(100, 100, 800, 600)  # Position et taille de la fenêtre
        log("Main window initialized")
        self.setup_menu()

    def setup_menu(self):
        # Créer la barre de menus
        menu_bar = self.menuBar()
        
        # Ajouter le menu "Settings"
        settings_menu = menu_bar.addMenu("Settings")
        
        # Créer l'action "Preferences..." avec le rôle PreferencesRole
        preferences_action = QtWidgets.QAction("Preferences…", self)  # Utiliser l'ellipsis correct
        preferences_action.setMenuRole(QtWidgets.QAction.PreferencesRole)
        preferences_action.triggered.connect(open_settings)
        
        # Ajouter l'action au menu "Settings"
        settings_menu.addAction(preferences_action)
        log("Added 'Preferences...' action to 'Settings' menu")

def main():
    app = QtWidgets.QApplication(sys.argv)
    
    # Définir le nom de l'application (important pour le menu d'application sur macOS)
    app.setApplicationName("WallOli")
    app.setWindowIcon(QtGui.QIcon('assets/icons/app_icon.icns'))
    
    setting_controller = SettingsController()
    log("Main window shown")
    
    sys.exit(app.exec_())

if __name__ == "__main__":
    main()
