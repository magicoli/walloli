import os
import subprocess
import re
import argparse
import tkinter as tk
from tkinter import ttk
from ffpyplayer.player import MediaPlayer
import psutil
import time

# Fonction de journalisation
def log(message):
    if verbose:
        script_name = os.path.basename(__file__)
        print(f"{script_name}: {message}")

class VideoWall:
    def __init__(self, root, video_paths, rows, cols):
        self.root = root
        self.video_paths = video_paths
        self.rows = rows
        self.cols = cols
        self.players = [MediaPlayer(video) for video in video_paths]
        log(f"Initialized VideoWall with {len(video_paths)} videos, {rows} rows, {cols} cols")
        self.setup_ui()
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

    def play_videos(self):
        for player in self.players:
            player.set_size(self.root.winfo_width(), self.root.winfo_height())
            player.toggle_pause()
        log("Started playing videos")

    def enter_fullscreen(self, event=None):
        self.fullscreen = True
        self.root.attributes("-fullscreen", self.fullscreen)
        log("Entered fullscreen")

    def toggle_fullscreen(self, event=None):
        self.fullscreen = not self.fullscreen
        self.root.attributes("-fullscreen", self.fullscreen)
        log(f"Toggled fullscreen to {self.fullscreen}")

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

def main():
    global verbose
    verbose = False

    parser = argparse.ArgumentParser(description="Video Wall")
    parser.add_argument('-d', '--days', type=int, help='Number of days to look back for videos')
    parser.add_argument('-m', '--max', type=int, help='Maximum number of videos to play')
    parser.add_argument('-p', '--panscan', type=float, default=0, help='Panscan value')
    parser.add_argument('-s', '--screen', type=int, help='Screen number')
    parser.add_argument('-V', '--volume', type=int, default=40, help='Volume level')
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

    if args.max:
        video_paths = video_paths[:args.max]

    if not video_paths:
        print("No videos found")
        return

    root = tk.Tk()
    player = VideoWall(root, video_paths, 2, 2)
    root.mainloop()

if __name__ == "__main__":
    main()
