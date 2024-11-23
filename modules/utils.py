# utils.py - This module contains utility functions for logging, argument validation, and system-specific operations.

# All code comments, user outputs and debugs must be in English. Do not remove this line.
# Some commands are commented out for further development. Do not remove them.

__all__ = [
    'log',
    'error',
    'exit_with_error',
]

import sys
import os
import subprocess
import re
import argparse
import threading
import logging

import _config as config

# Get the logger for the module
logger = logging.getLogger(__name__)

def setup_logging(log_level=logging.WARNING):
    """
    Configure logging for the application.

    Args:
        app (QApplication): The application object.
        log_level (int): The logging level to set.

    Returns:
        None
    """
    app_name = config.app_name
    if not app_name:
        app_name = os.path.basename(sys.argv[0])

    args = config.args

    # Define logging level -- this should move into utils.setup_logging function
    if args.quiet:
        log_level = logging.CRITICAL
    elif args.verbose >= 2:
        log_level = logging.DEBUG
    elif args.verbose == 1:
        log_level = logging.INFO
    else:
        log_level = logging.WARNING

    config.log_level = log_level

    logging.basicConfig(
        level=log_level,
        format=f'{app_name} [%(levelname)s] %(name)s: %(message)s',
        handlers=[
            logging.StreamHandler(sys.stdout),        # Affiche les logs dans la console
            # logging.FileHandler("app.log")            # Écrit les logs dans un fichier
        ]
    )

def log(message, *args):
    """
    Log a message with the appropriate log level if specified, otherwise use the 'info' level.

    Args:
        message (str): message to log. If the message is a key in the levels dictionary, it will be used as the log level.
        *args: Additional message parts

    Returns:
        None
    """
    levels = {
        'debug': logging.DEBUG,
        'info': logging.INFO,
        'warning': logging.WARNING,
        'error': logging.ERROR,
        'critical': logging.CRITICAL
    }
    if message in levels:
        level = message
        if not args:
            return # Pas de message à logger
        message = " ".join(str(arg) for arg in args).rstrip()
    else:
        level = 'info'
        if args:
            message += " " + " ".join(str(arg) for arg in args).rstrip()

    logger.log(levels[level], message)

def error(message, *args, error_code=1):
    """
    Log an error message et quitter le script.

    Args:
        message (str): Le message d'erreur à logger.
        *args: Arguments supplémentaires pour formater le message.
        exit_code (int): Code de sortie du script.

    Returns:
        None
    """
    log("error", message, *args)

def exit_with_error(message, *args, error_code=1):
    """
    Log une erreur et quitter le script avec un code d'erreur.

    Args:
        message (str): Le message d'erreur à logger.
        *args: Arguments supplémentaires pour formater le message.
        exit_code (int): Code de sortie du script.

    Returns:
        None
    """
    log("critical", message, *args)
    sys.exit(error_code)

def validate_os():
    """
    Validate the operating system and set the platform variable in the config module.

    Returns:
        None

    Raises:
        SystemExit: If the operating system is not supported.
    """
    if sys.platform == 'darwin':
        config.platform = 'macOS'
        config.is_mac = True
    elif sys.platform == 'win32':
        config.platform = 'Windows'
        config.is_windows = True
    elif sys.platform.startswith('linux'):
        config.platform = 'Linux'
        config.is_linux = True
    else:
        # Exit if platform is not supported
        print(f"Your platform {sys.platform} is not supported or could not be detected.")
        sys.exit(1)

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
        log(f"Error running find command: {e}")
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

    if config.is_mac:
        # macOS : use 'caffeinate' in the background and make sure it exits when the script ends
        log("Prevent sleep on macOS with 'caffeinate'")
        subprocess.Popen(['caffeinate', '-dimsu', '-w', str(os.getpid())])
    elif config.is_windows:
        # Windows : utiliser SetThreadExecutionState
        log("Prevent sleep on Windows with SetThreadExecutionState")
        import ctypes
        ES_CONTINUOUS = 0x80000000
        ES_SYSTEM_REQUIRED = 0x00000001
        ES_DISPLAY_REQUIRED = 0x00000002
        ctypes.windll.kernel32.SetThreadExecutionState(
            ES_CONTINUOUS | ES_SYSTEM_REQUIRED | ES_DISPLAY_REQUIRED)
    elif config.is_linux:
        # Linux : use 'systemd-inhibit' in the background
        # TODO: make sure systemd-inhibit is available on the system
        log("Prevent sleep on Linux with 'systemd-inhibit'")
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
                log(f"Error running systemd-inhibit: {e}")
        threading.Thread(target=inhibit_sleep, daemon=True).start()

def validate_vlc_lib():
    """
    Find the path to the libvlccore library based on the operating system.
    Returns the full path if found, otherwise None.

    Returns:
        str: The path to the libvlcc if found, otherwise None.

    Raises:
        SystemExit: If VLC is not installed or libvlccore is not found.
    """
    if config.is_mac:
        # Chemins courants pour VLC sur macOS
        vlc_paths = [
            "/Applications/VLC.app/Contents/MacOS/lib/libvlccore.dylib",
            "/Applications/VLC.app/Contents/MacOS/lib/libvlccore.9.dylib",  # Adapter selon la version
        ]
    elif config.is_windows:
        # Chemins courants pour VLC sur Windows
        vlc_paths = [
            "C:\\Program Files\\VideoLAN\\VLC\\libvlccore.dll",
            "C:\\Program Files (x86)\\VideoLAN\\VLC\\libvlccore.dll",
        ]
    # elif config.is_linux:
    else:
        # Chemins courants pour VLC sur Linux
        vlc_paths = [
            "/usr/lib/libvlccore.so",
            "/usr/local/lib/libvlccore.so",
            "/snap/vlc/current/lib/libvlccore.so",  # Pour les installations via snap
        ]
    # else:
    #     vlc_paths = []
    
    for path in vlc_paths:
        if os.path.exists(path):
            config.vlc_lib_path = path
            return

    log("VLC n'est pas installé ou libvlccore n'a pas été trouvé.")
    log("Veuillez installer VLC depuis https://www.videolan.org/vlc/download-macosx.html")
    sys.exit(1)
