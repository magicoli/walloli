import os
import subprocess
import argparse
import tkinter as tk
from tkinter import ttk
import cv2
from PIL import Image, ImageTk
import psutil
import time

def log(message):
    if os.getenv('DEBUG') == 'true':
        print(f"DEBUG: {message}")

class VideoWall:
    def __init__(self, root, video_paths, rows, cols):
        self.root = root
        self.video_paths = video_paths
        self.rows = rows
        self.cols = cols
        self.frames = []
        self.caps = [cv2.VideoCapture(video) for video in video_paths]
        self.setup_ui()
        self.update_frames()

    def setup_ui(self):
        self.root.title("Video Wall")
        self.root.geometry("800x600")
        self.canvas = tk.Canvas(self.root)
        self.canvas.pack(fill=tk.BOTH, expand=True)
        self.root.bind("<F11>", self.toggle_fullscreen)
        self.root.bind("<Escape>", self.exit_fullscreen)
        self.fullscreen = False

    def update_frames(self):
        for i, cap in enumerate(self.caps):
            ret, frame = cap.read()
            if ret:
                frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                img = Image.fromarray(frame)
                img = ImageTk.PhotoImage(img)
                if len(self.frames) > i:
                    self.canvas.itemconfig(self.frames[i], image=img)
                else:
                    x = (i % self.cols) * (self.root.winfo_width() // self.cols)
                    y = (i // self.cols) * (self.root.winfo_height() // self.rows)
                    self.frames.append(self.canvas.create_image(x, y, anchor=tk.NW, image=img))
                self.root.after(30, self.update_frames)

    def toggle_fullscreen(self, event=None):
        self.fullscreen = not self.fullscreen
        self.root.attributes("-fullscreen", self.fullscreen)

    def exit_fullscreen(self, event=None):
        self.fullscreen = False
        self.root.attributes("-fullscreen", False)

def find_videos(directory, days=None):
    log("Finding videos in directory " + os.path.abspath(directory))

    directory = os.path.abspath(directory)

    # regex = r'^[^\.].*\.\(avi|mp4|webm|m4v|mkv|wmv|mov|mpe?g\)\(.part\)?$'
    regex = r'.*\.(mp4|avi|webm|m4v|mkv|wmv|mov|mpe?g)(\.part)?$'

    command = ['find', directory, '(', '-type', 'f', '-o', '-type', 'l', ')']
    if days:
        # add [ 'mtime', f'-{days}' ] to command
        command.extend([ '-mtime', f'-{days}' ])

    log("Running command: " + ' '.join(command))
    result = subprocess.run(command, capture_output=True, text=True)
    log("Command output: " + result.stdout)
    
    ## Exit for now, for debug purpose
    exit(0)

    return result.stdout.splitlines()

def main():
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

    if args.verbose:
        print("Verbose mode enabled")

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
