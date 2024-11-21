# Import VLC and PyQt5 modules

import os
import sys
from itertools import cycle
from PyQt5 import QtWidgets, QtCore
from PyQt5.QtCore import pyqtSignal
import vlc

import _config as config
from modules.utils import log

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
        if not config.verbose:
            vlc_args.append('--quiet')  # Suppression des messages VLC

        # Instance VLC avec les arguments appropriés
        try:
            self.instance = vlc.Instance(*vlc_args)
            self.player = self.instance.media_player_new()
        except Exception as e:
            log(f"Error initializing VLC: {e}")
            return

        # Configuration du rendu vidéo selon le système d'exploitation
        if config.is_mac:  # pour macOS  
            self.player.set_nsobject(int(self.video_widget.winId()))
        elif config.is_linux:  # pour Linux
            self.player.set_xwindow(self.video_widget.winId())
        elif config.is_windows:  # pour Windows
            self.player.set_hwnd(self.video_widget.winId())
        
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
        self.video_path = next(self.playlist)
        if not os.path.exists(self.video_path):
            log(f"File not found, skipping {self.video_path}")
            self.play_next_video()  # Passer à la vidéo suivante
            return

        log(f"Playing next video: {self.video_path}")

        try:
            self.player.stop()
            media = self.instance.media_new(self.video_path)
            self.player.set_media(media)
            self.player.video_set_key_input(True)
            self.player.video_set_mouse_input(True)
            self.player.audio_set_volume(self.player.audio_get_volume())
            self.player.play()
            log(f"Playing video: {self.video_path}")
        except StopIteration:
            log("Playlist is exhausted")
        except Exception as e:
            log(f"Error playing {self.video_path}: {e}")

        # Vérifier si la lecture a commencé
        state = self.player.get_state()
        log(f"Player state: {state}")
        if state == vlc.State.Error:
            log(f"Error playing {self.video_path}")
            self.play_next_video()  # Skip to the next video


    def on_end_reached(self, event):
        """
        Handle the end of the video playback.
        Emmit the video_finished signal to play the next video.

        Args:
            event: The event object.
        """
        log(f"Video finished: {self.video_path}")
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
                log(f"Video paused {self.video_path}")
            else:
                self.player.play()
                log(f"Video resumed {self.video_path}")
        elif event.key() == QtCore.Qt.Key_S:
            self.player.stop()
            log(f"Video stopped {self.video_path}")
        else:
            super(VideoPlayer, self).keyPressEvent(event)
