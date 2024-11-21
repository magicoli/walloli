# utils.py - This module contains utility functions for logging, argument validation, and system-specific operations.

import _config as config
import sys
import os
import subprocess
import re
import argparse
import threading

def log(message, *args):
    """
    Log a message to the console with optional arguments.

    Args:
        message: The message to log.
        *args: Optional arguments to format the message.

    Returns:
        None
    """
    if config.verbose:
        script_name = os.path.basename(__file__)
        if args:
            message += " " + " ".join(str(arg) for arg in args).rstrip()
        print(f"{script_name}: {message}")

def valid_volume(value):
    """
    Validate the volume argument as an integer between 0 and 200.
    
    Args:
        value (str): The volume value to validate.
    
    Returns:
        int: The validated volume level.
    
    Raises:
        argparse.ArgumentTypeError: If the volume is not an integer or not within the valid range.
    """
    try:
        ivalue = int(value)
    except ValueError:
        raise argparse.ArgumentTypeError(f"Volume must be an integer, received {value}.")

    if ivalue < 0 or ivalue > 200:
        raise argparse.ArgumentTypeError(f"Volume must be between 0 and 200 (less than 100 recommended), received {ivalue}.")
    return ivalue

def find_videos(directory, days=None):
    """
    Find video files in the specified directory.
    
    Args:
        directory (str): The directory to search for video files.
        days (int, optional): The number of days to look back for videos. If None, all videos are considered.
    
    Returns:
        list of str: A list of paths to found video files.
    """
    log("Finding videos in directory " + os.path.abspath(directory))

    directory = os.path.abspath(directory)

    # TODO: handle alternative to find for Windows
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

def prevent_sleep():
    """
    Prevent the computer from going to sleep while the application is running.
    
    Implements OS-specific methods to inhibit sleep:
        - macOS: Uses 'caffeinate' in the background.
        - Windows: Utilizes SetThreadExecutionState API via ctypes.
        - Linux: Employs 'systemd-inhibit' to block idle/sleep modes.
    
    Returns:
        None
    """

    if sys.platform == 'darwin':
        # macOS : use 'caffeinate' in the background
        # TODO: make sure caffeinate is a standard command on macOS, try to use a standard alternative otherwise
        def run_caffeinate():
            subprocess.call(['caffeinate', '-dimsu'])
        threading.Thread(target=run_caffeinate, daemon=True).start()
        log("Prévention de la mise en veille sur macOS avec 'caffeinate'")
    elif sys.platform == 'win32':
        # Windows : utiliser SetThreadExecutionState
        import ctypes
        ES_CONTINUOUS = 0x80000000
        ES_SYSTEM_REQUIRED = 0x00000001
        ES_DISPLAY_REQUIRED = 0x00000002
        ctypes.windll.kernel32.SetThreadExecutionState(
            ES_CONTINUOUS | ES_SYSTEM_REQUIRED | ES_DISPLAY_REQUIRED)
        log("Prévention de la mise en veille sur Windows avec SetThreadExecutionState")
    elif sys.platform.startswith('linux'):
        # Linux : use 'systemd-inhibit' in the background
        # TODO: make sure systemd-inhibit is available on the system
        def inhibit_sleep():
            try:
                subprocess.call([
                    'systemd-inhibit',
                    '--what=idle:sleep',
                    '--why=WallOli Running',
                    '--mode=block',
                    'bash', '-c', 'while true; do sleep 60; done'
                ])
            except Exception as e:
                log(f"Erreur lors de l'appel à systemd-inhibit : {e}")
        threading.Thread(target=inhibit_sleep, daemon=True).start()
        log("Prévention de la mise en veille sur Linux avec 'systemd-inhibit'")
    else:
        log("Prévention de la mise en veille non prise en charge sur ce système.")

def find_vlc_lib():
    """
    Find the path to the libvlccore library based on the operating system.
    Returns the full path if found, otherwise None.

    Returns:
        str: The path to the libvlcc if found, otherwise None.

    Raises:
        SystemExit: If VLC is not installed or libvlccore is not found.
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

    log("VLC n'est pas installé ou libvlccore n'a pas été trouvé.")
    log("Veuillez installer VLC depuis https://www.videolan.org/vlc/download-macosx.html")
    sys.exit(1)
