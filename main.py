# main.py
import sys
import os
import argparse
from PyQt5 import QtWidgets

import _config as config
from modules.wallwindow import WallWindow, create_windows_and_players
from modules.slots import get_screens, get_slots
from modules.videoplayer import VideoPlayer
from modules.utils import log, prevent_sleep, valid_volume, find_videos

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
    # Prévenir la mise en veille de l'ordinateur
    prevent_sleep()

    # Initialiser QApplication avant de créer des widgets
    app = QtWidgets.QApplication(sys.argv)

    parser = argparse.ArgumentParser(description="Video Wall")
    parser.add_argument('-n', '--number', type=int, default=1, help='Number of players per screen')
    parser.add_argument('-N', '--total-number', type=int, default=None, help='Total number of players, overrides -n')
    parser.add_argument('-d', '--days', type=int, help='Number of days to look back for videos')
    parser.add_argument('-m', '--max', type=int, help='Maximum number of videos to play')
    parser.add_argument('-p', '--panscan', type=float, default=0, help='Panscan value')
    parser.add_argument('-s', '--screen', type=int, help='Screen number')
    parser.add_argument('-V', '--volume', type=valid_volume, default=20, help='Volume level (0-100)')
    parser.add_argument('-b', '--bestfit', action='store_true', help='Try to fit the best number of players on the screens')
    parser.add_argument('-k', '--kill', action='store_true', help='Kill existing video players')
    parser.add_argument('-l', '--singleloop', action='store_true', help='Single loop mode')
    parser.add_argument('-q', '--quiet', action='store_true', help='Quiet mode')
    parser.add_argument('-v', '--verbose', action='store_true', help='Verbose mode')
    parser.add_argument('directories', nargs='+', help='Directories to search for videos')
    args = parser.parse_args()

    if os.getenv('DEBUG') == 'true' or args.verbose:
        # set global variable verbose to true
        config.verbose = True

    video_paths = []
    for directory in args.directories:
        video_paths.extend(find_videos(directory, args.days))

    if not video_paths:
        print("No videos found")
        return

    screens = get_screens(args.screen)
    log("Screens: " + str(screens))

    slots = get_slots(video_paths, screens, args)
    log("slots: " + str(slots))

    windows = create_windows_and_players(screens, slots, video_paths, volume=args.volume)
    log("Windows: " + str(windows))

    # Lancer la boucle principale de PyQt
    sys.exit(app.exec_())

if __name__ == "__main__":
    main()
