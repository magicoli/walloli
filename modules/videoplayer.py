# videoplayer.py

import os
import sys
from itertools import cycle
from PyQt5 import QtWidgets, QtCore, QtGui
from PyQt5.QtCore import pyqtSignal, QTimer
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
        """
        super(VideoPlayer, self).__init__(parent)
        self.playlist = cycle(playlist)  # Infinite cycle over the playlist
        self.current_media = None
        self.video_path = None

        self.setStyleSheet("background-color: black;")
        self.setGeometry(0, 0, width, height)  # Set size according to the slot

        if color is not None:        
            self.setStyleSheet(f"background-color: {color.name()}; border: solid 5px {color.name()};")
        
        # Enable focus
        self.setFocusPolicy(QtCore.Qt.StrongFocus)

        # Create a widget for video rendering
        self.video_widget = QtWidgets.QFrame(self)
        self.video_widget.setGeometry(0, 0, width, height)
        self.video_widget.setStyleSheet("background-color: black;")

        # Prepare VLC arguments based on verbose mode and panscan
        vlc_args = []
        if not config.verbose:
            vlc_args.append('--quiet')  # Suppress VLC messages

        try:
            self.instance = vlc.Instance(*vlc_args)
            self.player = self.instance.media_player_new()
        except Exception as e:
            log(f"Error initializing VLC: {e}")
            return

        # Configure video output based on the operating system
        if config.is_mac:
            self.player.set_nsobject(int(self.video_widget.winId()))
        elif config.is_linux:
            self.player.set_xwindow(self.video_widget.winId())
        elif config.is_windows:
            self.player.set_hwnd(self.video_widget.winId())
        
        # Connect the end of media event to the handler
        events = self.player.event_manager()
        events.event_attach(vlc.EventType.MediaPlayerEndReached, self.on_end_reached)
        
        # Connect the playing event to apply_panscan
        events.event_attach(vlc.EventType.MediaPlayerPlaying, self.on_playing)

        # Connect the video_finished signal to play_next_video slot
        self.video_finished.connect(self.play_next_video)

        # Set the volume
        self.player.audio_set_volume(volume)

        # Start the first video
        self.play_next_video()

    def on_playing(self, event):
        """
        Handle the MediaPlayerPlaying event.
        Apply panscan once the video starts playing.
        
        Args:
            event: The event object.
        """
        self.apply_panscan()

    def play_next_video(self):
        """
        Play the next video in the playlist.
        """
        try:
            self.video_path = next(self.playlist)
        except StopIteration:
            log("Playlist is exhausted")
            return

        if not os.path.exists(self.video_path):
            log(f"File not found, skipping {self.video_path}")
            self.play_next_video()  # Skip to the next video
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
        except Exception as e:
            log(f"Error playing {self.video_path}: {e}")
            self.play_next_video()  # Skip to the next video in case of error

    def on_end_reached(self, event):
        """
        Handle the end of the video playback.
        Emit the video_finished signal to play the next video.

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
        # Handle specific key events
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

    def apply_panscan(self):
        """
        Adjust the video scale based on the panscan value from config.

        Panscan Values:
            - 0 : Fit (scale video to fit the entire widget)
            - 1 : Fill (scale video to fill the widget, cropping excess)
            - 0 < panscan < 1 : Partial cropping

        Returns:
            None
        """
        panscan = getattr(config, 'panscan', 0)
        panscan = max(0, min(1, panscan))  # Clamp between 0 and 1

        video_width = self.player.video_get_width()
        video_height = self.player.video_get_height()

        if video_width == 0 or video_height == 0:
            log("Unable to retrieve video dimensions.")
            return  # Cannot proceed without video dimensions

        PAD_PIXELS = 2  # Extra pixels to avoid rounding issues
        widget_width = self.video_widget.width() + PAD_PIXELS
        widget_height = self.video_widget.height() + PAD_PIXELS

        # Calculate scale factors
        scale_fit = min(widget_width / video_width, widget_height / video_height)
        scale_fill = max(widget_width / video_width, widget_height / video_height)

        # Calculate the final scale based on panscan
        if panscan == 0:
            # Utiliser 0.0 pour laisser VLC gérer l'échelle automatiquement (fit)
            scale_factor = 0.0
        elif panscan == 1:
            scale_factor = scale_fill
        else:
            scale_factor = (scale_fill - scale_fit) * panscan + scale_fit

        # Appliquer le facteur d'échelle
        self.player.video_set_scale(scale_factor)

        log(f"Panscan applied: panscan={panscan}, scale_factor={scale_factor}")

    def resizeEvent(self, event):
        """
        Handle the resize event to reapply panscan.

        Args:
            event: The resize event.
        """
        super(VideoPlayer, self).resizeEvent(event)
        self.apply_panscan()
