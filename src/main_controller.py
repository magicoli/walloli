# modules/main_controller.py

from PyQt5 import QtWidgets, QtCore, QtGui
from modules.settings import SettingsDialog
from modules.wall import Wall
from modules.utils import log
from modules.videoplayer import VideoPlayer
import _config as config
import os

# All code comments, user outputs and debugs must be in English. Do not remove this line.
# Some commands are commented out for further development. Do not remove them.

class MainController(QtCore.QObject):
    """
    Main controller of the application managing the system tray and settings.
    """

    def __init__(self, screens, slots, video_paths, volume, parent=None):
        super(MainController, self).__init__(parent)
        log("Initializing MainController")
        self.init_tray()
        self.wall = Wall(screens, slots, video_paths, volume=volume)
        # self.wall.all_windows_closed.connect(self.quit_application)  # Connect the signal

    def init_tray(self):
        """
        Initialize the system tray icon and context menu.
        """
        log("Initializing system tray")
        icon_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'assets', 'icons', 'tray_icon.png')
        if os.path.exists(icon_path):
        #     log(f"Icon path {icon_path} does not exist. Using standard icon.")
        #     icon = QtWidgets.QApplication.style().standardIcon(QtWidgets.QStyle.SP_ComputerIcon)
        # else:
            icon = QtGui.QIcon(icon_path)
            log(f"Using custom tray icon from {icon_path}")

        self.tray_icon = QtWidgets.QSystemTrayIcon(icon, self)
        
        tray_menu = QtWidgets.QMenu()

        # Action "Settings"
        settings_action = tray_menu.addAction("Settings")
        settings_action.triggered.connect(self.open_settings_dialog)
        log("Added 'Settings' action to tray menu")

        # Action "Exit"
        exit_action = tray_menu.addAction("Exit")
        exit_action.triggered.connect(QtWidgets.qApp.quit)
        log("Added 'Exit' action to tray menu")

        self.tray_icon.setContextMenu(tray_menu)
        self.tray_icon.show()
        log("System tray initialized and shown")

    def open_settings_dialog(self):
        """
        Open the settings dialog.
        """
        log("Opening settings dialog")
        dialog = SettingsDialog()
        dialog.settings_changed.connect(self.apply_settings)
        if dialog.exec_() == QtWidgets.QDialog.Accepted:
            log("Settings dialog accepted")
            self.apply_settings()
        else:
            log("Settings dialog cancelled")

    def apply_settings(self):
        """
        Apply updated settings to the application.
        """
        log("Applying settings")
        settings = QtCore.QSettings('YourCompany', 'VideoWallApp')  # Replace with your organization and app name
        config.volume = int(settings.value('volume', config.volume))
        config.panscan = bool(settings.value('panscan', config.panscan))
        config.verbose = bool(settings.value('verbose', config.verbose))
        directories = settings.value('directories', self.wall.video_paths)

        # Update VideoPlayer instances with the new volume
        for window in self.wall.windows:
            for player in window.findChildren(VideoPlayer):
                player.set_volume(config.volume)

        log("Settings applied")

    def quit_application(self):
        """
        Quit the application gracefully.
        """
        log("All WallWindows are closed. Quitting application.")
        QtWidgets.qApp.quit()
