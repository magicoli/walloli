import sys
import os
import subprocess
import re
import argparse
from math import ceil, sqrt
import random

# This test script is intended to find a way to display several videos in a single window
#
# This script is supposed to be multiplatform, even if it's developed on macOS
# Do not suggest solutions for macOS only, unless it's a macOS-specific issue
# Do not remove developer's comments

# La fonction de log fonctionne parfaitement, ne la changez pas, ne la supprimez pas.
def log(message, *args):
    # if verbose:
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

class VideoPlayer(QtWidgets.QFrame):
    def __init__(self, video_path, parent=None, width=300, height=200):
        super(VideoPlayer, self).__init__(parent)
        self.video_path = video_path
        self.setStyleSheet("background-color: black;")
        self.setGeometry(0, 0, width, height)  # Définir la taille selon le slot
        
        # Vérifiez si le fichier vidéo existe
        if not os.path.exists(self.video_path):
            log(f"Fichier vidéo non trouvé: {self.video_path}")
            return

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

        # Charger et jouer le média
        media = self.instance.media_new(self.video_path)
        self.player.set_media(media)
        self.player.play()

class MainWindow(QtWidgets.QMainWindow):
    def __init__(self, *args, **kwargs):
        super(MainWindow, self).__init__(*args, **kwargs)
        self.setFocusPolicy(QtCore.Qt.StrongFocus)
        self.is_fullscreen = False  # État du plein écran

        # Créer le widget central
        self.central_widget = QtWidgets.QWidget()
        self.setCentralWidget(self.central_widget)

        # Créer la mise en page
        self.layout = QtWidgets.QVBoxLayout(self.central_widget)

        # Créer les actions
        self.create_actions()
        # Créer le menu "View"
        self.create_menu()

    def create_actions(self):
        log("Plateforme: " + sys.platform)

        if sys.platform == 'darwin':
            # macOS
            self.toggle_fullscreen_action = QtWidgets.QAction("Basculer en Plein Écran", self)
            self.toggle_fullscreen_action.setShortcut(QtGui.QKeySequence("Ctrl+F"))
            self.toggle_fullscreen_action.triggered.connect(self.toggle_fullscreen)

            self.close_action = QtWidgets.QAction("Fermer la Fenêtre", self)
            self.close_action.setShortcut(QtGui.QKeySequence("Ctrl+W"))
            self.close_action.triggered.connect(self.close)
        else:
            # Windows/Linux
            self.toggle_fullscreen_action = QtWidgets.QAction("Basculer en Plein Écran", self)
            self.toggle_fullscreen_action.setShortcut(QtGui.QKeySequence("F11"))
            self.toggle_fullscreen_action.triggered.connect(self.toggle_fullscreen)

            self.toggle_fullscreen_alt_action = QtWidgets.QAction("Basculer en Plein Écran (Ctrl+F)", self)
            self.toggle_fullscreen_alt_action.setShortcut(QtGui.QKeySequence("Ctrl+F"))
            self.toggle_fullscreen_alt_action.triggered.connect(self.toggle_fullscreen)

            self.exit_fullscreen_action = QtWidgets.QAction("Quitter le Plein Écran", self)
            self.exit_fullscreen_action.setShortcut(QtGui.QKeySequence("Escape"))
            self.exit_fullscreen_action.triggered.connect(self.exit_fullscreen)

            self.close_action = QtWidgets.QAction("Fermer la Fenêtre", self)
            self.close_action.setShortcut(QtGui.QKeySequence("Ctrl+W"))
            self.close_action.triggered.connect(self.close)

        # Ajouter les actions à la fenêtre
        self.addAction(self.toggle_fullscreen_action)
        if not sys.platform == 'darwin':
            self.addAction(self.toggle_fullscreen_alt_action)
            self.addAction(self.exit_fullscreen_action)
        self.addAction(self.close_action)

    def create_menu(self):
        # Créer un menu "View"
        menubar = self.menuBar()
        view_menu = menubar.addMenu("View")
        view_menu.addAction(self.toggle_fullscreen_action)
        if not sys.platform == 'darwin':
            view_menu.addAction(self.toggle_fullscreen_alt_action)
            view_menu.addAction(self.exit_fullscreen_action)
        view_menu.addAction(self.close_action)

    def toggle_fullscreen(self):
        if self.isFullScreen():
            self.showNormal()
            self.is_fullscreen = False
        else:
            self.showFullScreen()
            self.is_fullscreen = True
        log(f"Plein écran {'activé' if self.is_fullscreen else 'désactivé'}")

    def exit_fullscreen(self):
        if self.is_fullscreen:
            self.showNormal()
            self.is_fullscreen = False
            log("Plein écran désactivé")

def create_windows_and_players(screens, slots, video_paths):
    windows = []
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

            # Sélectionner une vidéo aléatoire ou séquentielle
            video_path = random.choice(video_paths)

            # Créer un player pour chaque slot avec taille dynamique
            player = VideoPlayer(video_path, window, slot_width, slot_height)
            player.setGeometry(relative_x, relative_y, slot_width, slot_height)  # Positionnement correct
            player.show()

    return windows

def find_videos(directory, days=None):
    log("Finding videos in directory " + os.path.abspath(directory))

    directory = os.path.abspath(directory)

    command = ['find', directory, '(', '-type', 'f', '-o', '-type', 'l', ')']
    if days:
        command.extend(['-mtime', f'-{days}'])

    log("Running command: " + ' '.join(command))
    result = subprocess.run(command, capture_output=True, text=True)

    files = result.stdout.splitlines()

    # Utiliser regex pour filtrer les fichiers vidéo et exclure ceux dont le nom commence par un point
    video_extensions = re.compile(r'.*\.(avi|mp4|webm|m4v|mkv|wmv|mov|mpe?g)(\.part)?$', re.IGNORECASE)
    videos = [file for file in files if video_extensions.match(os.path.basename(file)) and not os.path.basename(file).startswith('.')]

    log("Found videos:\n" + "\n".join(videos))

    return videos

def get_screens(screen_number=None):
    screens = []
    if os.name == 'posix' and 'darwin' in os.uname().sysname.lower():
        # macOS
        result = subprocess.run(['displayplacer', 'list'], capture_output=True, text=True)
        res = None
        origin = None
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
    # Exemple : [('1920x1080', 0, 0), ('1920x1080', 1920, 0), ('1920x1080', -1920, 0)]
    # Ils doivent être triés par position
    # Ensuite, si args.screen est spécifié, retourner uniquement cet écran, sinon tous les écrans
    if screen_number is not None:
        if 1 <= screen_number <= len(screens):
            screens = [screens[screen_number - 1]]
        else:
            log(f"Invalid screen number: {screen_number}")
            exit(1)  # Quitter avec une erreur si le numéro d'écran est invalide

    return screens

def get_slots(video_paths, screens, args):
    log("Initializing windows and players")
    # (un par écran aka moniteur aka display) et players (un ou plusieurs players par fenêtre)

    log(f"Total screens: {screens}")

    videos_count = len(video_paths)

    if args.singleloop:
        log(f"Single loop: {args.singleloop}")
        # single loop affiche un player pour chaque vidéo dans la liste
        min_players = len(video_paths)
    elif args.number:
        log(f"Requested videos per screen: {args.number}")
        min_players = len(screens) * args.number
    else:
        min_players = len(screens) # un player par écran par défaut

    if args.max:
        # définir le nombre total de players au minimum entre args.max, args.number et len(video_paths)
        min_players = min(args.max, args.number if args.number else min_players, len(video_paths))
        # TODO: mélanger si nécessaire, puis tronquer la liste
        # video_paths = video_paths[:args.max]
    else:
        args.max = args.number if args.number else min_players

    log(f"Min players: {min_players}")
    # Calculer le meilleur ajustement réel pour les slots. Diviser chaque écran en slots par x,y
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

    empty_slots = total_slots - min_players
    log(f"Empty slots: {empty_slots}")

    slots = []
    slot_index = 0
    ignore_slots = set()  # Tableau pour noter les blocs à ignorer
    screen_index = 0
    for screen in screens:
        res, x, y = screen
        log("Screen resolution " + res + " at position " + str((x, y)))
        width, height = map(int, res.split('x'))
        rows, cols = slots_grid
        log(f"  Rows: {rows}, Cols: {cols}")
        slot_default_width = width // cols
        slot_default_height = height // rows
        log(f"  Slots dimensions: {slot_default_width}x{slot_default_height}")

        for row in range(rows):
            for col in range(cols):
                if (row, col) in ignore_slots:
                    continue

                slot_x = x + col * slot_default_width
                slot_y = y + row * slot_default_height
                current_slot_height = slot_default_height
                current_slot_width = slot_default_width

                if empty_slots >= 1 and row < rows - 1:
                    # Vérifier s'il y a un slot en dessous
                    ignore_slots.add((row + 1, col))
                    current_slot_height *= 2
                    empty_slots -= 1
                    if empty_slots >= 2 and col < cols - 1:
                        ignore_slots.add((row, col + 1))
                        ignore_slots.add((row + 1, col + 1))
                        current_slot_width *= 2
                        empty_slots -= 2

                slots.append((screen_index, slot_x, slot_y, current_slot_width, current_slot_height))

                log(f"  Slot {slot_index} {current_slot_width}x{current_slot_height} at ({slot_x}, {slot_y})")
                slot_index += 1
        screen_index +=1

    return slots

def main():
    global verbose
    verbose = False

    # Initialiser QApplication avant de créer des widgets
    app = QtWidgets.QApplication(sys.argv)

    parser = argparse.ArgumentParser(description="Video Wall")
    parser.add_argument('-n', '--number', type=int, default=1, help='Number of players to display')
    parser.add_argument('-d', '--days', type=int, help='Number of days to look back for videos')
    parser.add_argument('-m', '--max', type=int, help='Maximum number of videos to play')
    parser.add_argument('-p', '--panscan', type=float, default=0, help='Panscan value')
    parser.add_argument('-s', '--screen', type=int, help='Screen number')
    parser.add_argument('-V', '--volume', type=int, default=40, help='Volume level')
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

    windows = create_windows_and_players(screens, slots, video_paths)
    log("Windows: " + str(windows))

    # Lancer la boucle principale de PyQt
    sys.exit(app.exec_())

if __name__ == "__main__":
    main()
