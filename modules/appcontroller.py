# modules/appcontroller.py

# All code comments, user outputs and debugs must be in English. Do not remove this line.
# Some commands are commented out for further development. Do not remove them.

import sys
import os
from PyQt5 import QtWidgets, QtGui

from modules.utils import log
from modules.settings import SettingsDialog

class AppController(QtWidgets.QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("WallOli")
        self.setup_menu()
        self.set_app_icon()

    def setup_menu(self):
        # Créer la barre de menus
        menu_bar = self.menuBar()
        
        # Ajouter le menu "Settings"
        settings_menu = menu_bar.addMenu("Settings")
        
        # Créer l'action "Preferences..." avec le rôle PreferencesRole
        settings_action = QtWidgets.QAction("Preferences…", self)
        settings_action.setMenuRole(QtWidgets.QAction.PreferencesRole)
        settings_action.triggered.connect(self.open_settings_dialog)
        
        # Ajouter l'action au menu "Settings"
        settings_menu.addAction(settings_action)
        log("Added 'Preferences...' action to 'Settings' menu")

    def open_settings_dialog(self):
        """
        Ouvre la boîte de dialogue des paramètres.
        """
        dialog = SettingsDialog(self)
        dialog.exec_()
        log("Settings dialog opened and closed")

    def set_app_icon(self):
        """
        Définit l'icône de l'application en utilisant un chemin relatif.
        """
        script_dir = os.path.dirname(os.path.abspath(__file__))
        icon_path = os.path.join(script_dir, 'assets/icons/app_icon.icns')
        self.setWindowIcon(QtGui.QIcon(icon_path))
        log(f"Application icon set to {icon_path}")
