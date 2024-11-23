# modules/appcontroller.py

# All code comments, user outputs and debugs must be in English. Do not remove this line.
# Some commands are commented out for further development. Do not remove them.

import sys
import os
from PyQt5 import QtWidgets, QtGui
from PyQt5.QtCore import Qt  # Ensure Qt is imported

from modules.utils import log
from modules.settings import SettingsDialog

class AppController(QtWidgets.QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("WallOli")
        self.setup_menu()
        self.set_app_icon()

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
        Opens the settings dialog on the screen where the active window is located.
        """
        active_window = QtWidgets.QApplication.activeWindow()
        
        # if active_window:
        #     # Get the screen of the active window
        #     active_screen = active_window.screen()
        # else:
        #     # Fallback to the primary screen if no active window is found
        #     active_screen = QtWidgets.QApplication.primaryScreen()
        active_screen = QtWidgets.QApplication.primaryScreen()
        
        # Create the SettingsDialog with the active window as parent
        dialog = SettingsDialog(active_window)
        
        # Set the dialog modality to Application Modal
        dialog.setWindowModality(Qt.ApplicationModal)
        
        # Optional: Ensure the dialog stays on top
        # dialog.setWindowFlags(dialog.windowFlags() | Qt.WindowStaysOnTopHint)
        
        # Center the dialog on the active screen
        self.center_dialog_on_screen(dialog, active_screen)
        
        # Execute the dialog modally
        dialog.exec_()
        log("Settings dialog opened and closed")

    def center_dialog_on_screen(self, dialog, screen):
        """
        Centers the dialog on the specified screen.
        """
        # Get the geometry of the screen
        screen_geometry = screen.geometry()
        
        # Get the geometry of the dialog
        dialog_geometry = dialog.frameGeometry()
        
        # Calculate the center point of the screen
        center_point = screen_geometry.center()
        
        # Move the center of the dialog to the center of the screen
        dialog_geometry.moveCenter(center_point)
        
        # Apply the new top-left position to the dialog
        dialog.move(dialog_geometry.topLeft())

    def set_app_icon(self):
        """
        Sets the application icon using a relative path.
        """
        # Determine the directory of the current script
        script_dir = os.path.dirname(os.path.abspath(__file__))
        
        # Construct the path to the icon
        icon_path = os.path.join(script_dir, 'assets/icons/app_icon.icns')
        
        # Set the window icon
        self.setWindowIcon(QtGui.QIcon(icon_path))
        log(f"Application icon set to {icon_path}")
