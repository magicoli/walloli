# slots.py - This module contains functions to calculate the slots needed based on the number of screens and videos.
# """
# Calculate the slots needed based on the number of screens and videos.
# """

import os
import re
import subprocess
from math import ceil, sqrt

import _config as config
import modules.utils as utils   # all functions accessible with utils.function()
from modules.utils import *     # main functions accessible as function() for ease of use, e.g. log(), error(), exit_with_error()

def get_screens(screen_number=None):
    """
    Get the available screens and their resolutions.
    
    Args:
        screen_number (int, optional): The screen number to return, user-friendly (starting from 1). If None, all screens are returned.
    
    Returns:
        list of tuples: A list of screens where each screen is represented as (resolution, x, y).
    
    Raises:
        SystemExit: If the provided screen_number is invalid.
    """
    screens = []
    if config.is_mac:
        # macOS

        # if not shutil.which('displayplacer'):
        #     log("Error: 'displayplacer' is not installed on this system.")
        #     exit(1)
        result = subprocess.run(['displayplacer', 'list'], capture_output=True, text=True)
        for line in result.stdout.splitlines():
            if 'Resolution:' in line:
                res = line.split(': ')[1]
            if 'Origin' in line:
                origin = line.split(': ')[1].replace('(', '').replace(')', '').split(' ')[0]
                x, y = origin.split(',')
                screens.append((res, int(x), int(y)))
    elif config.is_linux:
        # Linux
        # if not shutil.which('xrandr'):
        #     log("Erreur: 'xrandr' n'est pas installé sur ce système.")
        #     exit(1)
        result = subprocess.run(['xrandr', '--query'], capture_output=True, text=True)
        for line in result.stdout.splitlines():
            if ' connected' in line:
                parts = line.split()
                res = parts[2]
                x, y = map(int, res.split('+')[1:])
                screens.append((res.split('+')[0], x, y))
    elif config.is_windows:
        # Windows
        result = subprocess.run(['wmic', 'path', 'Win32_VideoController', 'get', 'VideoModeDescription'], capture_output=True, text=True)
        for line in result.stdout.splitlines():
            if 'x' in line:
                res = line.strip()
                screens.append((res, 0, 0))
    
    screens.sort(key=lambda screen: (screen[1], screen[2]))
    if screen_number is not None:
        if 1 <= screen_number <= len(screens):
            screens = [screens[screen_number - 1]]
        else:
            log(f"Invalid screen number: {screen_number}")
            exit(1)  # Exit with error if the screen number is invalid

    return screens

def get_slots(video_paths, screens, args):
    """
    Calculate the slots needed based on the number of screens and videos.
    
    Args:
        video_paths (list of str): A list of video paths to play.
        screens (list of tuples): A list of screen resolutions and positions.
        args (argparse.Namespace): The command-line arguments.
    
    Returns:
        list of tuples: A list of slots where each slot is represented as (screen_index, slot_x, slot_y, slot_width, slot_height).
    """
    log("Initializing windows and players")

    log(f"Total screens: {screens}")

    videos_count = len(video_paths)

    if args.singleloop:
        log(f"Single loop: {args.singleloop}")
        # single loop shows a player for each video in the list
        min_players = len(video_paths)
    elif args.total_number:
        args.total_number = min(args.total_number, videos_count)
        log(f"Requested total number of players: {args.total_number}")
        min_players = args.total_number
    elif args.number:
        log(f"Requested videos per screen: {args.number}")
        min_players = min(len(screens) * args.number, videos_count)
    else:
        min_players = len(screens)  # one player per screen by default

    min_players = min(min_players, videos_count)

    if args.max:
        # set total players to minimum value between args.max, args.number and len(video_paths)
        min_players = min(args.max, args.number if args.number else min_players, len(video_paths))

        # TODO: shuffle if needed, then truncate the list
        # video_paths = video_paths[:args.max]
    else:
        args.max = args.number if args.number else min_players
    
    # Calculate actual best fit for slots. Divide each screen into slots by x,y
    min_slots_per_screen = ceil(min_players / len(screens))
    optimized_slots_per_screen = ceil(sqrt(min_slots_per_screen)) ** 2

    best_fit = None
    if args.bestfit:
        min_diff = float('inf')
        for rows in range(1, min_slots_per_screen + 1):
            cols = ceil(min_slots_per_screen / rows)
            diff = abs(rows - cols)
            if diff < min_diff:
                min_diff = diff
                best_fit = (rows, cols)
        slots_grid = best_fit
    else:
        slots_per_side = ceil(sqrt(optimized_slots_per_screen))
        slots_grid = (slots_per_side, slots_per_side)
    
    slots_per_screen = slots_grid[0] * slots_grid[1]
    log(f"Slots per screen: {slots_per_screen}")

    total_slots = slots_per_screen * len(screens)
    log(f"Total slots: {total_slots}")

    slots = []
    slot_index = 0
    screen_index = 0

    empty_slots = 0
    if args.total_number is not None:
        empty_slots = max(total_slots - args.total_number, 0)
        log(f"Total number of players requested: {args.total_number}, empty slots: {empty_slots}")
    else:
        log(f"No total number of players requested, empty slots: {empty_slots}")
        empty_slots = max(total_slots - min_players, 0)

    for screen in screens:
        ignore_slots = set()  # Initialiser pour chaque écran
        res, x, y = screen
        log("Screen resolution " + res + " at position " + str((x, y)))
        width, height = map(int, res.split('x'))
        rows, cols = slots_grid
        log(f"  Rows: {rows}, Cols: {cols}")
        slot_default_width = width // cols
        slot_default_height = height // rows
        log(f"  Slots dimensions: {slot_default_width}x{slot_default_height}")

        # Calculer les empty_slots pour cet écran
        if args.total_number:
            empty_slots_screen = empty_slots
        elif args.number:  # if number is set, manage per screen to distribute evenly
            empty_slots_screen = slots_per_screen - min(args.number, videos_count)
        else:
            empty_slots_screen = 0  # Par défaut 0 slot vide

        log(f"  Empty slots for this screen: {empty_slots_screen}")

        for row in range(rows):
            for col in range(cols):
                log("Checking slot " + str((row, col)))
                if (row, col) in ignore_slots:
                    log("slot " + str((row, col)) + " is in ignore list, skipping")
                    continue

                slot_x = x + col * slot_default_width
                slot_y = y + row * slot_default_height
                current_slot_height = slot_default_height
                current_slot_width = slot_default_width

                if empty_slots_screen >= 1 and row < rows - 1:
                    log(f"slot {row},{col}: {empty_slots_screen} empty slots left and a slot is available below")
                    ignore_slots.add((row + 1, col))
                    current_slot_height *= 2
                    empty_slots_screen -= 1
                    empty_slots = max(empty_slots - 1, 0)
                    if empty_slots_screen >= 2 and col < cols - 1:
                        log(f"{empty_slots_screen} empty slots left and two slots are available aside")
                        ignore_slots.add((row, col + 1))
                        ignore_slots.add((row + 1, col + 1))
                        current_slot_width *= 2
                        empty_slots_screen -= 2
                        empty_slots = max(empty_slots - 2, 0)

                # Assigner le slot
                slots.append((screen_index, slot_x, slot_y, current_slot_width, current_slot_height))

                log(f"  Slot {slot_index} {current_slot_width}x{current_slot_height} at ({slot_x}, {slot_y})")
                slot_index += 1
        screen_index +=1

    log("Slots: " + str(slots))
    return slots
