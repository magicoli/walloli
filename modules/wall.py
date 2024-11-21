# modules/wall.py - Module to create custom windows and build the wall.

import sys
import random
from PyQt5 import QtWidgets, QtCore, QtGui

import _config as config
from modules.videoplayer import VideoPlayer
from modules.utils import log

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

def create_windows_and_players(screens, slots, video_paths, volume=config.volume):
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
    #   Previously using itertools.cycle, replaced by random.shuffle)
    #   but using itertools.cycle might allow to choose dynamically the next video
    #   without the need to split the list in advance
    players_playlists = [[] for _ in range(total_slots)]
    for i, video in enumerate(video_paths):
        players_playlists[i % total_slots].append(video)

    for screen_index, screen in enumerate(screens):
        # Create a window for each screen
        window = WallWindow()
        window.setWindowTitle("Videowall")  # Définir le titre de la fenêtre
        res, x, y = screen
        width, height = map(int, res.split('x'))
        window.setGeometry(x, y, width, height)
        window.showFullScreen()  # Ouvrir en plein écran par défaut
        windows.append(window)

        # Build slots for current screen
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
            color = QtGui.QColor("black")

            # Build and configure the player
            log(f"Adding player {slot_index} in screen {screen_index} slot at ({relative_x}, {relative_y}) {slot_width}x{slot_height} with color {color.name()}")
            try:
                player = VideoPlayer(playlist, window, slot_width, slot_height, color, volume=volume)
                player.setGeometry(relative_x, relative_y, slot_width, slot_height)
                player.show()
            except Exception as e:
                log(f"Erreur lors de la création du VideoPlayer: {e}")

            slot_index += 1

    return windows
