# main.py

import sys
import os
import argparse
from PyQt5 import QtWidgets, QtCore, QtGui  # Ajout de QtGui si nécessaire

import _config as config
from modules.main_controller import MainController  # Nouveau contrôleur
from modules.slots import get_screens, get_slots
from modules.utils import log, prevent_sleep, valid_volume, find_videos, validate_os, validate_vlc_lib

# All code comments, user outputs and debugs must be in English. Do not remove this line.
# Some commands are commented out for further development. Do not remove them.

def main():
    """
    Main function to run the video wall application.
    
    Steps:
        1. Prevent computer from sleeping.
        2. Initialize QApplication.
        3. Parse command-line arguments.
        4. Search for video files in specified directories.
        5. Retrieve available screens.
        6. Calculate slots based on screens and videos.
        7. Create windows and video players.
        8. Start the Qt event loop.
    """

    # Validate OS and dependencies or die
    validate_os()
    validate_vlc_lib()

    # Prevent sleep
    prevent_sleep()

    # Initialize QApplication before any widgets
    app = QtWidgets.QApplication(sys.argv)
    # app.setQuitOnLastWindowClosed(False)  # Commented, it prevents quitting app when last window is closed. It's a display app, it makes absolutely no sense to keep it open without window.

    # Define application icon
    icon_path = os.path.join(os.path.dirname(__file__), 'modules', 'icons', 'app_icon.png')
    if os.path.exists(icon_path):
        app.setWindowIcon(QtGui.QIcon(icon_path))
    else:
        app.setWindowIcon(QtWidgets.QApplication.style().standardIcon(QtWidgets.QStyle.SP_ComputerIcon))

    # Parse command-line arguments
    parser = argparse.ArgumentParser(description="Video Wall")
    parser.add_argument('-s', '--screen', type=int, help='Screen number')
    parser.add_argument('-n', '--number', type=int, default=1, help='Number of players per screen')
    parser.add_argument('-N', '--total-number', type=int, default=None, help='Total number of players, overrides -n')
    parser.add_argument('-b', '--bestfit', action='store_true', help='Try to fit the best number of players on the screens')
    parser.add_argument('-d', '--days', type=int, help='Number of days to look back for videos')
    parser.add_argument('-p', '--panscan', type=float, default=0, help='Panscan value')
    parser.add_argument('-V', '--volume', type=valid_volume, default=config.volume, help='Volume level (0-100)')
    parser.add_argument('-v', '--verbose', action='store_true', help='Verbose mode')
    # parser.add_argument('-m', '--monitor', action='store_true', help='Monitor changes in the directories and refresh video list (not implemented)')
    parser.add_argument('-l', '--singleloop', action='store_true', help='Single loop mode (partially implemented)')
    parser.add_argument('-m', '--max', type=int, help='Maximum number of videos in single-loop mode (partially implemented)')
    # parser.add_argument('-k', '--kill', action='store_true', help='Kill other video players (not implemented)')
    # parser.add_argument('-q', '--quiet', action='store_true', help='Quiet mode (not implemented)')
    parser.add_argument('directories', nargs='+', help='Directories to search for videos')

    args = parser.parse_args()

    # Map command-line args to config
    config_args_mapping = {
        'verbose': 'verbose',
        'volume': 'volume',
        'panscan': 'panscan',
    }
    for arg_key, config_key in config_args_mapping.items():
        arg_value = getattr(args, arg_key, None)
        if arg_value is not None:
            setattr(config, config_key, arg_value)

    # ENV var override
    if os.getenv('DEBUG') == 'true':
        config.verbose = True

    # Load saved settings
    settings = QtCore.QSettings('Magiiic WallOli', 'VideoWallApp')  # Replace with your organization and app name
    config.volume = int(settings.value('volume', config.volume))
    config.panscan = bool(settings.value('panscan', config.panscan))
    config.verbose = bool(settings.value('verbose', config.verbose))
    # Command line directories override saved settings
    if args.directories:
        directories = args.directories
    else:
        directories = settings.value('directories', args.directories)

    # Find videos
    video_paths = []
    for directory in directories:
        video_paths.extend(find_videos(directory, args.days))

    if not video_paths:
        print("No videos found")
        return

    screens = get_screens(args.screen)
    log("Screens: " + str(screens))

    slots = get_slots(video_paths, screens, args)
    log("slots: " + str(slots))

    # Initialize and configure MainController
    main_controller = MainController(screens, slots, video_paths, volume=config.volume)
    app.main_controller = main_controller  # Maintain reference to MainController

    # Run Qt loop
    sys.exit(app.exec_())

if __name__ == "__main__":
    main()
