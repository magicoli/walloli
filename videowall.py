import sys
import os
import subprocess
import re
import argparse
from math import ceil, sqrt
import random
import time
from itertools import cycle

# This test script is intended to find a way to display several videos in a single window
#
# This script is supposed to be multiplatform, even if it's developed on macOS
# Do not suggest solutions for macOS only, unless it's a macOS-specific issue
# Do not remove developer's comments

# La fonction de log fonctionne parfaitement, ne la changez pas, ne la supprimez pas.
def log(message, *args):
    if verbose:
        script_name = os.path.basename(__file__)
        if args:
            message += " " + " ".join(str(arg) for arg in args).rstrip()
        print(f"{script_name}: {message}")

def find_vlc_lib():
    """
    Recherche le chemin de la bibliothèque libvlccore en fonction du système d'exploitation.
    Retourne le chemin complet si trouvé, sinon None.
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
    return None

# Vérifier la présence de VLC
vlc_lib_path = find_vlc_lib()

if not vlc_lib_path:
    log("VLC n'est pas installé ou libvlccore n'a pas été trouvé.")
    log("Veuillez installer VLC depuis https://www.videolan.org/vlc/download-macosx.html")
    sys.exit(1)
# else:
#     # Optionnel : Ajouter le chemin de la bibliothèque VLC aux variables d'environnement
#     vlc_lib_dir = os.path.dirname(vlc_lib_path)
#     os.environ['PATH'] = vlc_lib_dir + os.pathsep + os.environ.get('PATH', '')
#     os.environ['PYTHON_VLC_LIB_PATH'] = vlc_lib_dir

# Maintenant que VLC est vérifié, importer le module vlc
import vlc
from PyQt5 import QtWidgets, QtCore, QtGui
from PyQt5.QtCore import pyqtSignal

class VideoPlayer(QtWidgets.QFrame):
    # Définir un signal PyQt pour indiquer que la vidéo est terminée
    video_finished = pyqtSignal()

    def __init__(self, playlist, parent=None, width=300, height=200, color=None, volume=40):
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

        # Instance VLC
        try:
            self.instance = vlc.Instance()
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
        log(f"Vidéo terminée: {self.video_path}")
        # Émettre le signal pour appeler play_next_video dans le thread principal
        self.video_finished.emit()
    
    def mousePressEvent(self, event):
        # Lorsque le player est cliqué, il reçoit le focus
        self.setFocus()
        super(VideoPlayer, self).mousePressEvent(event)
    
    def keyPressEvent(self, event):
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

class MainWindow(QtWidgets.QWidget):
    def __init__(self, *args, **kwargs):
        super(MainWindow, self).__init__(*args, **kwargs)
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
        if self.isFullScreen():
            self.showNormal()
        else:
            self.showFullScreen()

    def exit_fullscreen(self):
        if self.isFullScreen():
            self.showNormal()

def create_windows_and_players(screens, slots, video_paths, volume=40):
    windows = []
    total_slots = len(slots)
    slot_index = 0

    # Mélanger globalement les vidéos
    random.shuffle(video_paths)

    # Distribuer les vidéos aux players sans duplication
    players_playlists = [[] for _ in range(total_slots)]
    for i, video in enumerate(video_paths):
        players_playlists[i % total_slots].append(video)
    
    # Si les vidéos sont insuffisantes, certains players auront des listes plus courtes
    # Les VideoPlayers utiliseront itertools.cycle pour répéter les vidéos si nécessaire

    for screen_index, screen in enumerate(screens):
        # Créer une fenêtre personnalisée pour chaque écran
        window = MainWindow()
        window.setWindowTitle("Videowall")  # Définir le titre de la fenêtre
        res, x, y = screen
        width, height = map(int, res.split('x'))
        window.setGeometry(x, y, width, height)
        window.showFullScreen()  # Ouvrir en plein écran par défaut
        windows.append(window)

        # Liste des slots pour cet écran
        screen_slots = [slot for slot in slots if slot[0] == screen_index]
        log(f"Screen {screen_index} slots: {screen_slots}")
        for slot in screen_slots:
            _, slot_x, slot_y, slot_width, slot_height = slot

            # Calculer la position relative au sein de la fenêtre
            relative_x = slot_x - x
            relative_y = slot_y - y

            # Assigner la playlist au player
            if slot_index < total_slots:
                playlist = players_playlists[slot_index]
            else:
                playlist = video_paths  # Fallback si insuffisance

            # Calculate a color, with hue based on the slot index and saturation/value fixed
            color = QtGui.QColor.fromHsvF(0, 0, 0)

            # Créer un player pour chaque slot avec taille dynamique
            log(f"Adding player {slot_index} in screen {screen_index} slot at ({relative_x}, {relative_y}) {slot_width}x{slot_height} with color {color.name()}")
            player = VideoPlayer(playlist, window, slot_width, slot_height, color, volume=volume)
            player.setGeometry(relative_x, relative_y, slot_width, slot_height)  # Positionnement correct
            player.show()

            slot_index += 1

    return windows

def find_videos(directory, days=None):
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
    # result: [('1920x1080', 0, 0), ('1920x1080', 1920, 0), ('1920x1080', -1920, 0)]
    # They should be sorted by position
    # Then if args.screen is specified, return only that screen, otherwise return all screens
    if screen_number is not None:
        if 1 <= screen_number <= len(screens):
            screens = [screens[screen_number - 1]]
        else:
            log(f"Invalid screen number: {screen_number}")
            exit(1)  # Exit with error if the screen number is invalid

    return screens

def get_slots(video_paths, screens, args):
    log("Initializing windows and players")
    #  (one per screen aka monitor aka display) and players (one or more players per window)")

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
    try:
        ivalue = int(value)
    except ValueError:
        raise argparse.ArgumentTypeError(f"Volume must be an integer, received {value}.")

    if ivalue < 0 or ivalue > 200:
        raise argparse.ArgumentTypeError(f"Volume must be between 0 and 200 (less than 100 recommended), received {ivalue}.")
    return ivalue

def main():
    global verbose
    verbose = False

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
