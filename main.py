# main.py

# All code comments, user outputs and debugs must be in English. Do not remove this line.
# Some commands are commented out for further development. Do not remove them.

import sys
import os
from PyQt5 import QtWidgets, QtGui

import _config as config
import modules.utils as utils   # all functions accessible with utils.function()
from modules.utils import *     # main functions accessible as function() for ease of use, e.g. log(), error(), exit_with_error()
from modules.appcontroller import AppController
from modules.settings import Settings, SettingsDialog
from modules.wall import Wall, WallWindow
from modules.slots import get_screens, get_slots
from modules.videoplayer import VideoPlayer

def main():
    """
    Main function to run the video wall application.
    
    Performs the following steps:
        1. Prevents the computer from going to sleep.
        2. Initializes the QApplication.
        3. Parses command-line arguments.
        4. Searches for video files in the specified directories.
        5. Retrieves available screens.
        6. Calculates slots based on screens and videos.
        7. Creates windows and video players.
        8. Starts the Qt event loop.
    
    Returns:
        None
    """

    # Check OS and die if not supported
    utils.validate_os()
    utils.validate_vlc_lib()

    # Prevent computer from going to sleep
    utils.prevent_sleep()

    # Initialize the QApplication before creating any widgets
    app = QtWidgets.QApplication(sys.argv)
    config.app_name = "WallOli"
    app.setApplicationName(config.app_name)  # Correction : utiliser config.app_name sans guillemets
    app.setWindowIcon(QtGui.QIcon('assets/icons/app_icon.icns'))

    app_controller = AppController()

    # Initialiser les paramètres en utilisant la classe Settings
    settings = Settings()

    # Appeler setup_logging
    utils.setup_logging()

    # Process directories and find videos
    if not config.directories:
        exit_with_error("No directories specified")
    video_paths = []
    for directory in settings.args.directories:
        video_paths.extend(utils.find_videos(directory, settings.args.days))

    if not video_paths:
        print("No videos found")
        return

    screens = get_screens(settings.args.screen)
    log("Screens: " + str(screens))

    slots = get_slots(video_paths, screens, settings.args)
    log("slots: " + str(slots))

    wall = Wall(screens, slots, video_paths, volume=settings.args.volume)
    log("Wall: " + str(wall))
    
    # Lancer la boucle principale de PyQt
    sys.exit(app.exec_())

if __name__ == "__main__":
    main()
