# modules/wall.py - Module to build the wall and windows.

import sys
import random
from PyQt5 import QtWidgets, QtCore, QtGui

import _config as config
from modules.videoplayer import VideoPlayer
from modules.utils import log

class Wall:
    """
    A class to manage the video wall by creating and managing multiple WallWindow instances.
    """

    def __init__(self, screens, slots, video_paths, volume=config.volume):
        """
        Initialize the Wall with the necessary parameters.

        Parameters:
            screens (list of tuples): List of screen resolutions and positions. Each tuple contains (resolution, x, y).
            slots (list of tuples): List of slots with position and size for each player. Each tuple contains (screen_index, slot_x, slot_y, slot_width, slot_height).
            video_paths (list of str): List of video paths to play.
            volume (int, optional): The volume level for the players. Defaults to 40.
        """
        self.screens = screens
        self.slots = slots
        self.video_paths = video_paths
        self.volume = volume
        self.windows = []

        self.create_windows_and_players()

    def create_windows_and_players(self):
        """
        Create required windows and build the video players grid.
        
        Returns:
            list of WallWindow: A list of created window instances.
        """
        total_slots = len(self.slots)
        slot_index = 0

        # Shuffle the video paths to distribute them randomly
        random.shuffle(self.video_paths)

        # Distribute the videos to the players without duplicates
        players_playlists = [[] for _ in range(total_slots)]
        for i, video in enumerate(self.video_paths):
            players_playlists[i % total_slots].append(video)

        for screen_index, screen in enumerate(self.screens):
            # Create a window for each screen
            window = WallWindow()
            window.setWindowTitle("Videowall")  # Set the window title
            res, x, y = screen
            try:
                width, height = map(int, res.split('x'))
            except ValueError:
                log(f"Invalid resolution for screen {screen_index}: {res}")
                continue
            window.setGeometry(x, y, width, height)
            window.showFullScreen()  # Open in fullscreen by default
            self.windows.append(window)

            # Build slots for current screen
            screen_slots = [slot for slot in self.slots if slot[0] == screen_index]
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
                    playlist = self.video_paths  # Fallback if insufficient

                # Color for the player background
                color = QtGui.QColor("black")

                # Build and configure the player
                log(f"Adding player {slot_index} on screen {screen_index} slot at ({relative_x}, {relative_y}) {slot_width}x{slot_height} with color {color.name()}")
                try:
                    player = VideoPlayer(playlist, window, slot_width, slot_height, color, volume=self.volume)
                    player.setGeometry(relative_x, relative_y, slot_width, slot_height)
                    player.show()
                except Exception as e:
                    log(f"Error creating VideoPlayer: {e}")

                slot_index += 1

        return self.windows

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
        exit_fullscreen: Exit fullscreen mode if active.
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

        self.setup_shortcuts()

    def setup_shortcuts(self):
        """
        Setup keyboard shortcuts for the window.
        """
        toggle_fs_seq = QtGui.QKeySequence("Ctrl+F")
        toggle_fs = QtWidgets.QShortcut(toggle_fs_seq, self)
        toggle_fs.activated.connect(self.toggle_fullscreen)

        exit_fs_seq = QtGui.QKeySequence("Esc")
        exit_fs = QtWidgets.QShortcut(exit_fs_seq, self)
        exit_fs.activated.connect(self.exit_fullscreen)

        close_seq = QtGui.QKeySequence("Ctrl+W")
        close_shortcut = QtWidgets.QShortcut(close_seq, self)
        close_shortcut.activated.connect(self.close)

        if not config.is_mac:
            # We don't want to interfere with Mission Control on macOS
            # F11 is standard for fullscreen on Windows and Linux
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
