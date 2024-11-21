import sys
import os
import subprocess
import re
import argparse
import ctypes  # Pour Windows
from math import ceil, sqrt
import random
import time
from itertools import cycle
import threading  # Pour gérer les threads si nécessaire

"""
This application is intended to display multiple videos on multiple screens in a single window.
It uses VLC to play the videos and PyQt5 for the GUI.

The application is designed to be cross-platform, but some features may not work on all platforms.
"""

# Reminder for devs and AI: do not remove developer's comments

def log(message, *args):
    """
    Log a message to the console with optional arguments.

    Args:
        message: The message to log.
        *args: Optional arguments to format the message.

    Returns:
        None
    """
    if verbose:
        script_name = os.path.basename(__file__)
        if args:
            message += " " + " ".join(str(arg) for arg in args).rstrip()
        print(f"{script_name}: {message}")

def find_vlc_lib():
    """
    Find the path to the libvlccore library based on the operating system.
    Returns the full path if found, otherwise None.

    Returns:
        str: The path to the libvlcc if found, otherwise None.

    Raises:
        SystemExit: If VLC is not installed or libvlccore is not found.
    """
    if sys.platform.startswith('darwin'):
        # Chemins courants pour VLC sur macOS
        vlc_paths = [
            "/Applications/VLC.app/Contents/MacOS/lib/libvlccore.dylib",
            "/Applications/VLC.app/Contents/MacOS/lib/libvlccore.9.dylib",  # Adapter selon la version
        ]
    elif sys.platform.startswith('linux'):
        # Chemins courants pour VLC sur Linux
        vlc_paths = [
            "/usr/lib/libvlccore.so",
            "/usr/local/lib/libvlccore.so",
            "/snap/vlc/current/lib/libvlccore.so",  # Pour les installations via snap
        ]
    elif sys.platform == "win32":
        # Chemins courants pour VLC sur Windows
        vlc_paths = [
            "C:\\Program Files\\VideoLAN\\VLC\\libvlccore.dll",
            "C:\\Program Files (x86)\\VideoLAN\\VLC\\libvlccore.dll",
        ]
    else:
        vlc_paths = []
    
    for path in vlc_paths:
        if os.path.exists(path):
            return path

    log("VLC n'est pas installé ou libvlccore n'a pas été trouvé.")
    log("Veuillez installer VLC depuis https://www.videolan.org/vlc/download-macosx.html")
    sys.exit(1)

# Import VLC and PyQt5 modules
vlc_lib_path = find_vlc_lib()
import vlc
from PyQt5 import QtWidgets, QtCore, QtGui
from PyQt5.QtCore import pyqtSignal

class VideoPlayer(QtWidgets.QFrame):
    """
    A class to represent a video player widget using VLC.

    Attributes:
        playlist: A cycle iterator for the video playlist.
        current_media: The current media being played.
        video_path: The path to the current video file.

    Methods:
        play_next_video: Play the next video in the playlist.
        on_end_reached: Handle the end of the video playback.
        mousePressEvent: Handle mouse press events on the video player.
        keyPressEvent: Capture specific key events and send related commands to the video player.
    """

    # Define a signal for when the video has finished playing
    video_finished = pyqtSignal()

    def __init__(self, playlist, parent=None, width=300, height=200, color=None, volume=40):
        """
        Initialize the video player with a playlist of video paths.

        Args:
            playlist: A list of video paths to play.
            parent: The parent widget for the video player.
            width: The width of the video player.
            height: The height of the video player.
            color: The background color of the video player.
            volume: The volume level for the video player.

        Raises:
            Exception: If VLC fails to initialize.
        """
        # TODO: fix exception not raised in some cases (e.g. invalid video file)

        super(VideoPlayer, self).__init__(parent)
        self.playlist = cycle(playlist)  # Cycle infini sur la playlist
        self.current_media = None
        self.video_path = None

        self.setStyleSheet("background-color: black;")
        self.setGeometry(0, 0, width, height)  # Définir la taille selon le slot

        if color is not None:        
            self.setStyleSheet(f"background-color: {color.name()}; border: solid 5px {color.name()};")
        
        # Autoriser le focus
        self.setFocusPolicy(QtCore.Qt.StrongFocus)

        # Créer un widget pour le rendu vidéo
        self.video_widget = QtWidgets.QFrame(self)
        self.video_widget.setGeometry(0, 0, width, height)
        self.video_widget.setStyleSheet("background-color: black;")

        # Préparer les arguments pour VLC en fonction du mode verbose
        vlc_args = []
        if not verbose:
            vlc_args.append('--quiet')  # Suppression des messages VLC

        # Instance VLC avec les arguments appropriés
        try:
            self.instance = vlc.Instance(*vlc_args)
            self.player = self.instance.media_player_new()
        except Exception as e:
            log(f"Erreur lors de l'initialisation de VLC: {e}")
            return

        # Configuration du rendu vidéo selon le système d'exploitation
        if sys.platform.startswith('linux'):  # pour Linux
            self.player.set_xwindow(self.video_widget.winId())
        elif sys.platform == "win32":  # pour Windows
            self.player.set_hwnd(self.video_widget.winId())
        elif sys.platform == "darwin":  # pour macOS
            self.player.set_nsobject(int(self.video_widget.winId()))
        
        # Connecter l'événement de fin de lecture à la méthode on_end_reached
        events = self.player.event_manager()
        events.event_attach(vlc.EventType.MediaPlayerEndReached, self.on_end_reached)

        # Connecter le signal video_finished au slot play_next_video
        self.video_finished.connect(self.play_next_video)

        # Définir le volume
        self.player.audio_set_volume(volume)

        # Démarrer la première vidéo
        self.play_next_video()

    def play_next_video(self):
        """
        Play the next video in the playlist.

        Raises:
            StopIteration: If the playlist is exhausted.
        """
        try:
            self.video_path = next(self.playlist)
            if not os.path.exists(self.video_path):
                log(f"File not found, skipping {self.video_path}")
                self.play_next_video()  # Passer à la vidéo suivante
                return

            log(f"Playing next video: {self.video_path}")

            # Arrêter le lecteur avant de charger une nouvelle vidéo
            self.player.stop()
            log("Lecteur VLC arrêté.")

            # Charger le nouveau média
            media = self.instance.media_new(self.video_path)
            self.player.set_media(media)
            log(f"Média chargé: {self.video_path}")

            # Configurer les entrées vidéo
            self.player.video_set_key_input(True)
            self.player.video_set_mouse_input(True)

            # Définir le volume à chaque chargement
            self.player.audio_set_volume(self.player.audio_get_volume())

            # Démarrer la lecture
            self.player.play()
            log(f"Lecture de {self.video_path} en cours...")

            # Vérifier si la lecture a commencé
            state = self.player.get_state()
            log(f"État du lecteur après play(): {state}")
            if state == vlc.State.Error:
                log(f"Erreur de lecture pour {self.video_path}")
                self.play_next_video()  # Passer à la vidéo suivante en cas d'erreur

        except StopIteration:
            log("Fin de la playlist.")
        except Exception as e:
            log(f"Exception dans play_next_video: {e}")

    def on_end_reached(self, event):
        """
        Handle the end of the video playback.
        Emmit the video_finished signal to play the next video.

        Args:
            event: The event object.
        """
        log(f"Vidéo terminée: {self.video_path}")
        self.video_finished.emit()
    
    def mousePressEvent(self, event):
        """
        Handle mouse press events on the video player.

        Args:
            event: The mouse press event.
        """
        self.setFocus()
        super(VideoPlayer, self).mousePressEvent(event)
    
    def keyPressEvent(self, event):
        """
        Capture specific key events and send related commands to the video player.

        Args:
            event: The key press event.
        """
        # Gérer les événements clavier spécifiques
        if event.key() == QtCore.Qt.Key_Space:
            if self.player.is_playing():
                self.player.pause()
                log(f"Pause de {self.video_path}")
            else:
                self.player.play()
                log(f"Lecture de {self.video_path}")
        elif event.key() == QtCore.Qt.Key_S:
            self.player.stop()
            log(f"Arrêt de {self.video_path}")
        else:
            super(VideoPlayer, self).keyPressEvent(event)

class WallWindow(QtWidgets.QWidget):
    """
    A custom window class to display the video wall.

    Attributes:
        toggle_fs (QtWidgets.QShortcut): Shortcut for toggling fullscreen mode (Ctrl+F).
        exit_fs (QtWidgets.QShortcut): Shortcut for exiting fullscreen mode (Esc).
        close_shortcut (QtWidgets.QShortcut): Shortcut for closing the window (Ctrl+W).
        toggle_fs2 (QtWidgets.QShortcut): Additional shortcut for toggling fullscreen on Windows/Linux (F11).

    Methods:
        toggle_fullscreen: Toggle the window between fullscreen and normal size.
        exit_fullscreen: Exit fullscreen mode if active
    """

    def __init__(self, *args, **kwargs):
        """
        Initialize the WallWindow with the specified arguments and keyword arguments.
        
        Parameters:
            *args: Command-line arguments.
            **kwargs: Additional keyword arguments.
        """
        super(WallWindow, self).__init__(*args, **kwargs)
        self.setFocusPolicy(QtCore.Qt.StrongFocus)

        # Définir les raccourcis clavier
        toggle_fs_seq = QtGui.QKeySequence("Ctrl+F")
        toggle_fs = QtWidgets.QShortcut(toggle_fs_seq, self)
        toggle_fs.activated.connect(self.toggle_fullscreen)

        exit_fs_seq = QtGui.QKeySequence("Esc")
        exit_fs = QtWidgets.QShortcut(exit_fs_seq, self)
        exit_fs.activated.connect(self.exit_fullscreen)

        close_seq = QtGui.QKeySequence("Ctrl+W")
        close_shortcut = QtWidgets.QShortcut(close_seq, self)
        close_shortcut.activated.connect(self.close)

        if sys.platform != 'darwin':
            # Windows/Linux
            toggle_fs_seq2 = QtGui.QKeySequence("F11")
            toggle_fs2 = QtWidgets.QShortcut(toggle_fs_seq2, self)
            toggle_fs2.activated.connect(self.toggle_fullscreen)

    def toggle_fullscreen(self):
        """
        Toggle the window between fullscreen and normal size.
        """
        if self.isFullScreen():
            self.showNormal()
        else:
            self.showFullScreen()

    def exit_fullscreen(self):
        """
        Exit fullscreen mode if active.
        """
        if self.isFullScreen():
            self.showNormal()

def prevent_sleep():
    """
    Prevent the computer from going to sleep while the application is running.
    
    Implements OS-specific methods to inhibit sleep:
        - macOS: Uses 'caffeinate' in the background.
        - Windows: Utilizes SetThreadExecutionState API via ctypes.
        - Linux: Employs 'systemd-inhibit' to block idle/sleep modes.
    
    Returns:
        None
    """
    if sys.platform == 'darwin':
        # macOS : utiliser 'caffeinate' en arrière-plan
        def run_caffeinate():
            subprocess.call(['caffeinate', '-dimsu'])
        threading.Thread(target=run_caffeinate, daemon=True).start()
        log("Prévention de la mise en veille sur macOS avec 'caffeinate'")
    elif sys.platform == 'win32':
        # Windows : utiliser SetThreadExecutionState
        import ctypes
        ES_CONTINUOUS = 0x80000000
        ES_SYSTEM_REQUIRED = 0x00000001
        ES_DISPLAY_REQUIRED = 0x00000002
        ctypes.windll.kernel32.SetThreadExecutionState(
            ES_CONTINUOUS | ES_SYSTEM_REQUIRED | ES_DISPLAY_REQUIRED)
        log("Prévention de la mise en veille sur Windows avec SetThreadExecutionState")
    elif sys.platform.startswith('linux'):
        # Linux : utiliser 'systemd-inhibit' en arrière-plan
        def inhibit_sleep():
            try:
                subprocess.call([
                    'systemd-inhibit',
                    '--what=idle:sleep',
                    '--why=WallOli Running',
                    '--mode=block',
                    'bash', '-c', 'while true; do sleep 60; done'
                ])
            except Exception as e:
                log(f"Erreur lors de l'appel à systemd-inhibit : {e}")
        threading.Thread(target=inhibit_sleep, daemon=True).start()
        log("Prévention de la mise en veille sur Linux avec 'systemd-inhibit'")
    else:
        log("Prévention de la mise en veille non prise en charge sur ce système.")

def create_windows_and_players(screens, slots, video_paths, volume=40):
    """
    Create required windows and build the video players grid.
    
    Args:
        screens (list of tuples): List of screen resolutions and positions. Each tuple contains (resolution, x, y).
        slots (list of tuples): List of slots with position and size for each player. Each tuple contains (screen_index, slot_x, slot_y, slot_width, slot_height).
        video_paths (list of str): List of video paths to play.
        volume (int, optional): The volume level for the players. Defaults to 40.
    
    Returns:
        list of WallWindow: A list of created window instances.
    """
    windows = []
    total_slots = len(slots)
    slot_index = 0

    # Shuffle the video paths to distribute them randomly
    random.shuffle(video_paths)

    # Distribute the videos to the players without duplicates
    # Players will use itertools.cycle to repeat videos if necessary
    players_playlists = [[] for _ in range(total_slots)]
    for i, video in enumerate(video_paths):
        players_playlists[i % total_slots].append(video)

    for screen_index, screen in enumerate(screens):
        # Create a window for each screen
        # Créer une fenêtre personnalisée pour chaque écran
        window = WallWindow()
        window.setWindowTitle("Videowall")  # Définir le titre de la fenêtre
        res, x, y = screen
        width, height = map(int, res.split('x'))
        window.setGeometry(x, y, width, height)
        window.showFullScreen()  # Ouvrir en plein écran par défaut
        windows.append(window)

        # Build slots
        screen_slots = [slot for slot in slots if slot[0] == screen_index]
        log(f"Screen {screen_index} slots: {screen_slots}")
        for slot in screen_slots:
            _, slot_x, slot_y, slot_width, slot_height = slot

            # Calculate the relative position within the window
            relative_x = slot_x - x
            relative_y = slot_y - y

            # Assign a playlist to the player based on the slot index
            if slot_index < total_slots:
                playlist = players_playlists[slot_index]
            else:
                playlist = video_paths  # Fallback si insuffisance

            # Color for the player background
            color = color = QtGui.QColor("black")

            # Build the player
            log(f"Adding player {slot_index} in screen {screen_index} slot at ({relative_x}, {relative_y}) {slot_width}x{slot_height} with color {color.name()}")
            player = VideoPlayer(playlist, window, slot_width, slot_height, color, volume=volume)
            player.setGeometry(relative_x, relative_y, slot_width, slot_height)  # Positionnement correct
            player.show()

            slot_index += 1

    return windows

def find_videos(directory, days=None):
    """
    Find video files in the specified directory.
    
    Args:
        directory (str): The directory to search for video files.
        days (int, optional): The number of days to look back for videos. If None, all videos are considered.
    
    Returns:
        list of str: A list of paths to found video files.
    """
    log("Finding videos in directory " + os.path.abspath(directory))

    directory = os.path.abspath(directory)

    command = ['find', directory, '(', '-type', 'f', '-o', '-type', 'l', ')']
    if days:
        command.extend(['-mtime', f'-{days}'])

    log("Running command: " + ' '.join(command))
    try:
        result = subprocess.run(command, capture_output=True, text=True, check=True)
    except subprocess.CalledProcessError as e:
        log(f"Erreur lors de l'exécution de la commande find: {e}")
        sys.exit(1)

    # log("Command output: " + result.stdout)

    files = result.stdout.splitlines()

    # Utiliser grep pour filtrer les fichiers vidéo et exclure ceux dont le nom commence par un point
    video_extensions = re.compile(r'.*\.(avi|mp4|webm|m4v|mkv|wmv|mov|mpe?g)(\.part)?$', re.IGNORECASE)
    videos = [file for file in files if video_extensions.match(os.path.basename(file)) and not os.path.basename(file).startswith('.')]

    log(f"Found {len(videos)} video(s)")

    return videos

def get_screens(screen_number=None):
    """
    Get the available screens and their resolutions.
    
    Args:
        screen_number (int, optional): The screen number to return, user-friendly (starting from 1). If None, all screens are returned.
    
    Returns:
        list of tuples: A list of screens where each screen is represented as (resolution, x, y).
    
    Raises:
        SystemExit: If the provided screen_number is invalid.
    """
    screens = []
    if os.name == 'posix' and 'darwin' in os.uname().sysname.lower():
        # macOS
        result = subprocess.run(['displayplacer', 'list'], capture_output=True, text=True)
        for line in result.stdout.splitlines():
            if 'Resolution:' in line:
                res = line.split(': ')[1]
            if 'Origin' in line:
                origin = line.split(': ')[1].replace('(', '').replace(')', '').split(' ')[0]
                x, y = origin.split(',')
                screens.append((res, int(x), int(y)))
    elif os.name == 'nt':
        # Windows
        result = subprocess.run(['wmic', 'path', 'Win32_VideoController', 'get', 'VideoModeDescription'], capture_output=True, text=True)
        for line in result.stdout.splitlines():
            if 'x' in line:
                res = line.strip()
                screens.append((res, 0, 0))
    else:
        # Linux
        result = subprocess.run(['xrandr', '--query'], capture_output=True, text=True)
        for line in result.stdout.splitlines():
            if ' connected' in line:
                parts = line.split()
                res = parts[2]
                x, y = map(int, res.split('+')[1:])
                screens.append((res.split('+')[0], x, y))
    
    screens.sort(key=lambda screen: (screen[1], screen[2]))
    if screen_number is not None:
        if 1 <= screen_number <= len(screens):
            screens = [screens[screen_number - 1]]
        else:
            log(f"Invalid screen number: {screen_number}")
            exit(1)  # Exit with error if the screen number is invalid

    return screens

def get_slots(video_paths, screens, args):
    """
    Calculate the slots needed based on the number of screens and videos.
    
    Args:
        video_paths (list of str): A list of video paths to play.
        screens (list of tuples): A list of screen resolutions and positions.
        args (argparse.Namespace): The command-line arguments.
    
    Returns:
        list of tuples: A list of slots where each slot is represented as (screen_index, slot_x, slot_y, slot_width, slot_height).
    """
    log("Initializing windows and players")

    log(f"Total screens: {screens}")

    videos_count = len(video_paths)

    if args.singleloop:
        log(f"Single loop: {args.singleloop}")
        # single loop shows a player for each video in the list
        min_players = len(video_paths)
    elif args.total_number:
        log(f"Requested total number of players: {args.total_number}")
        min_players = args.total_number
    elif args.number:
        log(f"Requested videos per screen: {args.number}")
        min_players = min(len(screens) * args.number, videos_count)
    else:
        min_players = len(screens)  # one player per screen by default

    min_players = min(min_players, videos_count)

    if args.max:
        # set total players to minimum value between args.max, args.number and len(video_paths)
        min_players = min(args.max, args.number if args.number else min_players, len(video_paths))

        # TODO: shuffle if needed, then truncate the list
        # video_paths = video_paths[:args.max]
    else:
        args.max = args.number if args.number else min_players

    # Calculate actual best fit for slots. Divide each screen into slots by x,y
    min_slots_per_screen = ceil(min_players / len(screens))
    optimized_slots_per_screen = ceil(sqrt(min_slots_per_screen)) ** 2

    best_fit = None
    if args.bestfit:
        min_diff = float('inf')
        for rows in range(1, min_slots_per_screen + 1):
            cols = ceil(min_slots_per_screen / rows)
            diff = abs(rows - cols)
            if diff < min_diff:
                min_diff = diff
                best_fit = (rows, cols)
        slots_grid = best_fit
    else:
        slots_per_side = ceil(sqrt(optimized_slots_per_screen))
        slots_grid = (slots_per_side, slots_per_side)
    
    slots_per_screen = slots_grid[0] * slots_grid[1]
    log(f"Slots per screen: {slots_per_screen}")

    total_slots = slots_per_screen * len(screens)
    log(f"Total slots: {total_slots}")

    slots = []
    slot_index = 0
    screen_index = 0

    empty_slots = 0
    if args.total_number is not None:
        empty_slots = max(total_slots - args.total_number, 0)
        log(f"Total number of players requested: {args.total_number}, empty slots: {empty_slots}")
    else:
        log(f"No total number of players requested, empty slots: {empty_slots}")
        empty_slots = max(total_slots - min_players, 0)

    for screen in screens:
        ignore_slots = set()  # Initialiser pour chaque écran
        res, x, y = screen
        log("Screen resolution " + res + " at position " + str((x, y)))
        width, height = map(int, res.split('x'))
        rows, cols = slots_grid
        log(f"  Rows: {rows}, Cols: {cols}")
        slot_default_width = width // cols
        slot_default_height = height // rows
        log(f"  Slots dimensions: {slot_default_width}x{slot_default_height}")

        # Calculer les empty_slots pour cet écran
        if args.total_number:
            empty_slots_screen = empty_slots
        elif args.number:  # if number is set, manage per screen to distribute evenly
            empty_slots_screen = slots_per_screen - min(args.number, videos_count)
        else:
            empty_slots_screen = 0  # Par défaut 0 slot vide

        log(f"  Empty slots for this screen: {empty_slots_screen}")

        for row in range(rows):
            for col in range(cols):
                log("Checking slot " + str((row, col)))
                if (row, col) in ignore_slots:
                    log("slot " + str((row, col)) + " is in ignore list, skipping")
                    continue

                slot_x = x + col * slot_default_width
                slot_y = y + row * slot_default_height
                current_slot_height = slot_default_height
                current_slot_width = slot_default_width

                if empty_slots_screen >= 1 and row < rows - 1:
                    log(f"slot {row},{col}: {empty_slots_screen} empty slots left and a slot is available below")
                    ignore_slots.add((row + 1, col))
                    current_slot_height *= 2
                    empty_slots_screen -= 1
                    empty_slots = max(empty_slots - 1, 0)
                    if empty_slots_screen >= 2 and col < cols - 1:
                        log(f"{empty_slots_screen} empty slots left and two slots are available aside")
                        ignore_slots.add((row, col + 1))
                        ignore_slots.add((row + 1, col + 1))
                        current_slot_width *= 2
                        empty_slots_screen -= 2
                        empty_slots = max(empty_slots - 2, 0)

                # Assigner le slot
                slots.append((screen_index, slot_x, slot_y, current_slot_width, current_slot_height))

                log(f"  Slot {slot_index} {current_slot_width}x{current_slot_height} at ({slot_x}, {slot_y})")
                slot_index += 1
        screen_index +=1

    log("Slots: " + str(slots))
    return slots

def valid_volume(value):
    """
    Validate the volume argument as an integer between 0 and 200.
    
    Args:
        value (str): The volume value to validate.
    
    Returns:
        int: The validated volume level.
    
    Raises:
        argparse.ArgumentTypeError: If the volume is not an integer or not within the valid range.
    """
    try:
        ivalue = int(value)
    except ValueError:
        raise argparse.ArgumentTypeError(f"Volume must be an integer, received {value}.")

    if ivalue < 0 or ivalue > 200:
        raise argparse.ArgumentTypeError(f"Volume must be between 0 and 200 (less than 100 recommended), received {ivalue}.")
    return ivalue

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
    global verbose
    verbose = False

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
        verbose = True

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
