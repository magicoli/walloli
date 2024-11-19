import os
import subprocess
import re
import argparse
import tkinter as tk
from tkinter import ttk
from ffpyplayer.player import MediaPlayer
from PIL import Image, ImageTk
import psutil
import time
from math import ceil, sqrt
import random

# Fonction de journalisation
def log(message):
    if verbose:
        script_name = os.path.basename(__file__)
        print(f"{script_name}: {message}")

class VideoPlayer:
    def __init__(self, root, video_path, x, y, width, height):
        self.root = root
        self.video_path = video_path
        self.canvas = tk.Canvas(root, width=width, height=height)
        self.canvas.place(x=x, y=y)
        self.frame_image = None
        self.running = True

        # Initialize MediaPlayer
        self.player = MediaPlayer(video_path, ff_opts={'sync': 'audio'})
        self.start_time = None  # To track playback start time
        self.update_frame()

    def update_frame(self):
        if not self.running:
            return
        
        if self.start_time is None:
            self.start_time = time.time()  # Initialize playback start time

        # Get the next video frame and timestamp
        frame, val = self.player.get_frame()

        if val == 'eof':  # End of file
            self.running = False
            return

        if frame is not None:
            img, t = frame  # Frame and its timestamp
            elapsed_time = time.time() - self.start_time

            # Define a tolerance (buffer) for synchronization
            tolerance = 0.05  # 50 ms

            if t < elapsed_time - tolerance:
                # Frame is too late, skip it
                print(f"Frame {t:.2f}s is too late, skipping.")
                self.update_frame()  # Fetch the next frame immediately
                return
            elif t > elapsed_time + tolerance:
                # Frame is too early, delay but ensure recalibration
                delay = int((t - elapsed_time) * 1000)
                print(f"Frame {t:.2f}s is early, delaying by {delay}ms.")
                self.root.after(delay, self.update_frame)
                return

            # Frame is within the tolerance, display it
            img = Image.frombytes("RGB", img.get_size(), bytes(img.to_bytearray()[0]))
            self.frame_image = ImageTk.PhotoImage(img)
            self.canvas.create_image(0, 0, anchor="nw", image=self.frame_image)

        # Continue updating frames
        self.root.after(10, self.update_frame)

    def stop(self):
        self.running = False
        self.player.close_player()

def toggle_fullscreen(event, window):
    window.attributes("-fullscreen", not window.attributes("-fullscreen"))

def exit_fullscreen(event, window):
    window.attributes("-fullscreen", False)

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

    slots = []
    slot_index = 0
    ignore_slots = set()  # Table to note the blocks to ignore
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
                    # Check if there is a slot below
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

                # DO NOT UNCOMMENT PLAYER INITIALIZATION, we do'nt give a shit until the slots are properly defined
                # player = MediaPlayer(video_paths[slot_index % len(video_paths)])
                # player.set_size(slot_default_width, slot_height)
                # players.append(player)
                # log(f"Initialized player for video {slot_index % len(video_paths)} at screen {screen} with size {slot_default_width}x{slot_height}")
        screen_index +=1

    return slots

def create_windows_and_players(screens, slots, video_paths):
    windows = []
    for screen_index, screen in enumerate(screens):
        # Créer une fenêtre pour chaque écran
        window = tk.Tk()
        window.title("Videowall")  # Définir le titre de la fenêtre
        res, x, y = screen
        width, height = map(int, res.split('x'))
        window.geometry(f"{width}x{height}+{x}+{y}")
        window.attributes("-fullscreen", True)  # Ouvrir en plein écran par défaut
        windows.append(window)

        # Assigner les touches pour quitter et réactiver le plein écran
        window.bind("<Escape>", lambda event, win=window: exit_fullscreen(event, win))
        if os.name == 'posix' and 'darwin' in os.uname().sysname.lower():
            window.bind("<Command-f>", lambda event, win=window: toggle_fullscreen(event, win))
        else:
            window.bind("<F11>", lambda event, win=window: toggle_fullscreen(event, win))

        # Positionner les players dans chaque slot correspondant à cet écran
        for slot in slots:
            slot_screen_index, slot_x, slot_y, slot_width, slot_height = slot
            if slot_screen_index == screen_index:
                # Mélanger les vidéos pour chaque player
                playlist = video_paths[:]
                random.shuffle(playlist)

                # Créer un player pour chaque slot
                VideoPlayer(window, playlist[0], slot_x - x, slot_y - y, slot_width, slot_height)

    return windows

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

    if not video_paths:
        print("No videos found")
        return

    screens = get_screens(args.screen)
    log("Screens: " + str(screens))

    slots = get_slots(video_paths, screens, args)
    log("slots: " + str(slots))

    windows = create_windows_and_players(screens, slots, video_paths)
    log("Windows: " + str(windows))

    # Lancer la boucle principale de Tkinter
    for window in windows:
        window.mainloop()

if __name__ == "__main__":
    main()
