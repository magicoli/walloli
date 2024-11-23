# main.py

# All code comments, user outputs and debugs must be in English. Do not remove this line.
# Some commands are commented out for further development. Do not remove them.

import sys
import os
import argparse
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

    # Check os and die if not supported
    utils.validate_os()
    utils.validate_vlc_lib()

    # Prevent computer from going to sleep
    utils.prevent_sleep()

    # Initialize the QApplication before creating any widgets
    app = QtWidgets.QApplication(sys.argv)
    config.app_name = "WallOli"
    app.setApplicationName("config.app_name")
    app.setWindowIcon(QtGui.QIcon('assets/icons/app_icon.icns'))

    app_controller = AppController()

    # Parse command-line arguments
    parser = argparse.ArgumentParser(description="Video Wall")
    parser.add_argument('-s', '--screen', type=int, help='Screen number')
    parser.add_argument('-n', '--number', type=int, default=1, help='Number of players per screen')
    parser.add_argument('-N', '--total-number', type=int, default=None, help='Total number of players, overrides -n')
    parser.add_argument('-b', '--bestfit', action='store_true', help='Try to fit the best number of players on the screens')
    parser.add_argument('-d', '--days', type=int, help='Number of days to look back for videos')
    parser.add_argument('-p', '--panscan', type=float, default=0, help='Panscan value')
    parser.add_argument('-V', '--volume', type=utils.valid_volume, default=config.volume, help='Volume level (0-100)')
    parser.add_argument('-v', '--verbose', action='count', default=0, help='Verbose mode (can be used multiple times)')
    # parser.add_argument('-m', '--monitor', action='store_true', help='Monitor changes in the directories and refresh video list (not implemented)')
    parser.add_argument('-l', '--singleloop', action='store_true', help='Single loop mode (partially implemented)')
    parser.add_argument('-m', '--max', type=int, help='Maximum number of videos in single-loop mode (partially implemented)')
    # parser.add_argument('-k', '--kill', action='store_true', help='Kill other video players (not implemented)')
    parser.add_argument('-q', '--quiet', action='store_true', help='Quiet mode (not implemented)')
    parser.add_argument('directories', nargs='+', help='Directories to search for videos')

    args = parser.parse_args()

    # Define list of arguments to map to config variables
    config_args_mapping = {
        'verbose': 'verbose',
        'volume': 'volume',
        'panscan': 'panscan',
    }

    # Map command-line arguments to config variables
    for arg_key, config_key in config_args_mapping.items():
        arg_value = getattr(args, arg_key, None)
        if arg_value is not None:
            setattr(config, config_key, arg_value)

    if os.getenv('DEBUG') == 'true':
        # Surcharger si la variable d'environnement DEBUG est définie
        config.verbose = 2
        args.quiet = False # overrides quiet mode

    # Store procesed command-line arguments in config for reference
    config.args = args
 
    utils.setup_logging()

    # # Keep test portion for debugging
    # log("message with log()")
    # error("message with error(message)")
    # error("message with error(message, error_code=1)", error_code=1)
    # error("message with error(message, 1)", 1)
    # exit_with_error("message with exit_with_error()")
    # exit_with_error("message with exit_with_error()", 14)
    # exit(0) # DEBUG

    # Process directories and find videos
    video_paths = []
    for directory in args.directories:
        video_paths.extend(utils.find_videos(directory, args.days))

    if not video_paths:
        print("No videos found")
        return

    screens = get_screens(args.screen)
    log("Screens: " + str(screens))

    slots = get_slots(video_paths, screens, args)
    log("slots: " + str(slots))

    # windows = create_windows_and_players(screens, slots, video_paths, volume=args.volume)
    # log("Windows: " + str(windows))

    wall = Wall(screens, slots, video_paths, volume=args.volume)
    log("Wall: " + str(wall))
    
    # Lancer la boucle principale de PyQt
    sys.exit(app.exec_())

if __name__ == "__main__":
    main()
