import os
import subprocess
import re
import argparse
import tkinter as tk
from tkinter import ttk
from ffpyplayer.player import MediaPlayer
import psutil
import time
from math import ceil, sqrt

# Fonction de journalisation
def log(message):
    if verbose:
        script_name = os.path.basename(__file__)
        print(f"{script_name}: {message}")

class VideoWall:
    def __init__(self, root, video_paths, rows, cols, screen_info):
        self.root = root
        self.video_paths = video_paths
        self.rows = rows
        self.cols = cols
        self.screen_info = screen_info
        self.players = [MediaPlayer(video) for video in video_paths]
        log(f"Initialized VideoWall with {len(video_paths)} videos, {rows} rows, {cols} cols")
        self.setup_ui()
        self.calculate_layout()
        self.play_videos()

    def setup_ui(self):
        self.root.title("Video Wall")
        self.root.geometry("800x600")
        self.canvas = tk.Canvas(self.root)
        self.canvas.pack(fill=tk.BOTH, expand=True)
        self.root.bind("<Escape>", self.exit_fullscreen)
        self.fullscreen = False

        # Détecter le système d'exploitation
        if os.name == 'posix' and 'darwin' in os.uname().sysname.lower():
            # macOS
            self.root.bind("<Command-f>", self.enter_fullscreen)
        else:
            # Autres systèmes d'exploitation
            self.root.bind("<F11>", self.toggle_fullscreen)

        log("UI setup complete")

    def calculate_layout(self):
        screen_width = self.root.winfo_screenwidth()
        screen_height = self.root.winfo_screenheight()
        log(f"Screen dimensions: {screen_width}x{screen_height}")

        self.slot_default_width = screen_width // self.cols
        self.slot_height = screen_height // self.rows
        log(f"Slot dimensions: {self.slot_default_width}x{self.slot_height}")

    def play_videos(self):
        for i, player in enumerate(self.players):
            x = (i % self.cols) * self.slot_default_width
            y = (i // self.cols) * self.slot_height
            player.set_size(self.slot_default_width, self.slot_height)
            player.toggle_pause()
            log(f"Started playing video {i} at position ({x}, {y})")
        log("Started playing videos")

    def toggle_fullscreen(self, event=None):
        self.fullscreen = not self.fullscreen
        self.root.attributes("-fullscreen", self.fullscreen)
        log(f"Toggled fullscreen to {self.fullscreen}")

    def enter_fullscreen(self, event=None):
        self.fullscreen = True
        self.root.attributes("-fullscreen", self.fullscreen)
        log("Entered fullscreen")

    def exit_fullscreen(self, event=None):
        self.fullscreen = False
        self.root.attributes("-fullscreen", False)
        log("Exited fullscreen")

def find_videos(directory, days=None):
    log("Finding videos in directory " + os.path.abspath(directory))

    directory = os.path.abspath(directory)

    command = ['find', directory, '(', '-type', 'f', '-o', '-type', 'l', ')']
    if days:
        command.extend(['-mtime', f'-{days}'])

    log("Running command: " + ' '.join(command))
    result = subprocess.run(command, capture_output=True, text=True)
    # log("Command output: " + result.stdout)

    files = result.stdout.splitlines()

    # Utiliser grep pour filtrer les fichiers vidéo et exclure ceux dont le nom commence par un point
    video_extensions = re.compile(r'.*\.(avi|mp4|webm|m4v|mkv|wmv|mov|mpe?g)(\.part)?$', re.IGNORECASE)
    videos = [file for file in files if video_extensions.match(os.path.basename(file)) and not os.path.basename(file).startswith('.')]

    log("Found videos:\n" + "\n".join(videos))

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
    log("Screens: " + str(screens))

    return screens

def init_windows_and_players(video_paths, screens, args):
    log("Initializing windows and players")
    #  (one per screen aka monitor aka display) and players (one or more players per window)")

    log(f"Total screens: {screens}")

    videos_count = len(video_paths)

    if args.singleloop:
        log(f"Single loop: {args.singleloop}")
        # single loop shows a player for each video in the list
        min_players = len(video_paths)
    elif args.number:
        log(f"Requested videos per screen: {args.number}")
        min_players = len(screens) * args.number
    else:
        min_players = len(screens) # one player per screen by default

    if args.max:
        # set total players to minimum value between args.max, args.number and len(video_paths
        min_players = min(args.max, args.number, len(video_paths))

        # TODO: shuffle if needed, then truncate the list
        # video_paths = video_paths[:args.max]
    else:
        args.max = args.number

    log(f"Min players: {min_players}")
    # Calculate actual best fit for slots. Divide each screen in slots by x,y
    min_slots_per_screen = ceil(min_players / len(screens))
    # log(f"Min slots per screen: {min_slots_per_screen}")
    optimized_slots_per_screen = ceil(sqrt(min_slots_per_screen)) ** 2
    # log(f"Optimized slots per screen: {optimized_slots_per_screen}")

    best_fit = None
    if args.bestfit:
        min_diff = float('inf')
        for rows in range(1, min_slots_per_screen + 1):
            cols = ceil(min_slots_per_screen / rows)
            diff = abs(rows - cols)
            if diff < min_diff:
                min_diff = diff
                best_fit = (rows, cols)
        # log(f"Best fit: {best_fit}")
        slots_grid = best_fit
    else:
        slots_per_side = ceil(sqrt(optimized_slots_per_screen))
        slots_grid = (slots_per_side, slots_per_side)
    # log(f"Slots grid: {slots_grid}")

    slots_per_screen = slots_grid[0] * slots_grid[1]
    log(f"Slots per screen: {slots_per_screen}")

    total_slots = slots_per_screen * len(screens)
    log(f"Total slots: {total_slots}")

    empty_slots = total_slots - min_players
    log(f"Empty slots: {empty_slots}")

    players = []
    slot_index = 0
    ignore_slots = set()  # Table to note the blocks to ignore

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

                slot_index += 1
                slot_x = x + col * slot_default_width
                slot_y = y + row * slot_default_height
                current_slot_height = slot_default_height
                current_slot_width = slot_default_width

                if empty_slots >= 1 and row < rows - 1:
                    # Check if there is a slot below
                    ignore_slots.add((row + 1, col))
                    current_slot_height *= 2
                    empty_slots -= 1
                    if empty_slots >= 2 and col < cols - 1:
                        ignore_slots.add((row, col + 1))
                        ignore_slots.add((row + 1, col + 1))
                        current_slot_width *= 2
                        empty_slots -= 2

                log(f"  Slot {slot_index} {current_slot_width}x{current_slot_height} at ({slot_x}, {slot_y})")

                # DO NOT UNCOMMENT PLAYER INITIALIZATION, we do'nt give a shit until the slots are properly defined
                # player = MediaPlayer(video_paths[slot_index % len(video_paths)])
                # player.set_size(slot_default_width, slot_height)
                # players.append(player)
                # log(f"Initialized player for video {slot_index % len(video_paths)} at screen {screen} with size {slot_default_width}x{slot_height}")

    exit() # DEBUG
    log("players: " + str(players))
    return players

def main():
    global verbose
    verbose = False

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

    # Wrong to do this that early, the list will be truncated later, after deciding the ordering
    # if args.max:
    #     video_paths = video_paths[:args.max]
    # total_videos = args.max if args.max else len(video_paths)

    if not video_paths:
        print("No videos found")
        return

    screens = get_screens(args.screen)

    players = init_windows_and_players(video_paths, screens, args)

    # root = tk.Tk()
    # player = VideoWall(root, video_paths, 2, 2, screens)
    # root.mainloop()

if __name__ == "__main__":
    main()
