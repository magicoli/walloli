# modules/appcontroller.py

# All code comments, user outputs and debugs must be in English. Do not remove this line.
# Some commands are commented out for further development. Do not remove them.

from PyQt5 import QtWidgets
from PyQt5.QtCore import Qt  # Ensure Qt is imported

import modules.config as config
import modules.utils as utils   # all functions accessible with utils.function()
from modules.utils import *     # main functions accessible as function() for ease of use, e.g. log(), error(), exit_with_error()
from modules.settings import SettingsDialog

class AppController(QtWidgets.QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle(config.app_name)
        self.setup_menu()

    def setup_menu(self):
        # Create the menu bar
        menu_bar = self.menuBar()
        
        # Add the "Settings" menu
        settings_menu = menu_bar.addMenu("Settings")
        
        # Create the "Preferences..." action with PreferencesRole
        settings_action = QtWidgets.QAction("Preferences…", self)
        settings_action.setMenuRole(QtWidgets.QAction.PreferencesRole)
        settings_action.triggered.connect(self.open_settings_dialog)
        
        # Add the action to the "Settings" menu
        settings_menu.addAction(settings_action)
        log("Added 'Preferences...' action to 'Settings' menu")

    def open_settings_dialog(self):
        """
        Centers the dialog on the application's main screen, on top of any other application windows.
        """
        active_window = QtWidgets.QApplication.activeWindow()
        
        if active_window:
            # Get the screen of the active window
            active_screen = active_window.screen()
        else:
            # Fallback to the primary screen if no active window is found
            active_screen = QtWidgets.QApplication.primaryScreen()
        
        # Create the SettingsDialog with the active window as parent
        dialog = SettingsDialog(active_window)
        dialog.setWindowModality(Qt.ApplicationModal)
        dialog.setWindowFlags(dialog.windowFlags() | Qt.WindowStaysOnTopHint)

        # self.center_dialog_on_screen(dialog, active_screen)
        screen_geometry = active_screen.geometry()
        dialog_geometry = dialog.frameGeometry()
        center_point = screen_geometry.center()
        dialog_geometry.moveCenter(center_point)
        dialog.move(dialog_geometry.topLeft())
        
        # Execute the dialog modally
        dialog.exec_()
        log("Settings dialog opened and closed")
