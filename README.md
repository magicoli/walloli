# WallOli

![Version](https://img.shields.io/github/v/release/magicoli/walloli)
![License](https://img.shields.io/github/license/magicoli/walloli)
![Last Commit](https://img.shields.io/github/last-commit/magicoli/walloli)
![Contributors](https://img.shields.io/github/contributors/magicoli/walloli)

Cross-platform video wall player, play multiple videos across one or multiple screens

## Description

**WallOli** is a cross-platform tool designed to display a grid of videos across one or multiple screens. Leveraging **VLC** for video playback, this application ensures smooth and synchronized video presentations.
## Features

- **Multiple Video Playback**: Simultaneously play multiple videos.
- **Multi-screen support** Can be set to play on a single screen or across different screens.
- **Wide Format Support**: Compatible with common video formats such as AVI, MP4, MKV, and more.
- **Sleep Prevention**: Prevents the computer from sleeping while the application is running.
- **Flexible Configuration**: Choose the number of players per screen or total, screen split method, single-loop mode...

## Installation

### Prerequisites

- **Python 3.13+**
- **VLC Media Player** installed on your system
- **Python modules** VLC and PyQt5 libraries will be installed by the launcher script

### Setup and Install Dependencies

The `launcher.sh` script handles the creation of a virtual environment and the installation of necessary dependencies.

Ensure that the `launcher.sh` script has execute permissions. If not, make it executable:

```bash
chmod +x launcher.sh
```

### Install VLC

Download and install VLC from the [official website](https://www.videolan.org/vlc/download-macosx.html).

## Usage

### Launch the Application

Use the provided launch script, which automatically checks for dependencies and starts the application.

```bash
./launcher.sh /path/to/videos/
```

### Command-Line Options

The application supports various command-line arguments to customize its behavior:

**Usage**:
```bash
./launcher.sh [OPTIONS] <video_directory> [<video_directory> ...]
```
- `directories`: Directories to search for videos
- `-n`, `--number`: Number of players per screen (default: 1)
- `-N`, `--total-number`: Total number of players, overrides `-n`
- `-s`, `--screen`: Screen number to use _(use all monitors if not set)_
- `-b`, `--bestfit`: Adjust to fit the best number of players on the screens
    - with bestfit: try to get the most neutral ratio (closer to square), _best for videos with various orientations and ratios_
    - without bestfit, try to get most of the slots at the same ratio as the screen, _best for videos with same ratio and orientation as the screens_
- `-d`, `--days`: Number of days to look back for recent videos
- `-V`, `--volume`: Volume level (0-100) (default: 20)
- `-v`, `--verbose`: Chatty output on terminal (for developers)

**Not yet implemented** those features are in the original Linux player but are not yet ported for this multi-platform project:
- `-p`, `--panscan`: Panscan crop value (decimal from 0 to 1, default 0)
    - 0 fits video in available space
    - 1 crops video to fill available space
    - any intermediate value to adjust the cropping, e.g. 0.5 to balance between cropping and fillin space
- `-k`, `--kill`: Terminate already running instances
- `-l`, `--singleloop`: Enable single-loop mode, number of players adjusted to display all videos simultaneously
- `-m`, `--max`: Truncate the video list to limit the number of players _(in single-loop mode only)_
- `-q`, `--quiet`: Enable quiet mode

**Example:**

```bash
./launcher.sh --verbose -n 2 -V 50 /path/to/videos/
```

## Files

- **`launcher.sh`**
  - the only script to use, launches the application in the proper environment and install dendendencies

- **`main.py`**
  - main python script, should not be used directly, unless the proper environment is manually set and dependencies are manually installed

- **`generate-test-videos.sh`**:
  - Tool to generate simple videos with variable lengths and dimensions for testing purpose.
  - **Usage**:
    ```bash
    ./generate-test-videos.sh [<number_of_test_videos>]
    ```
- **`_config.py`**
    - Application's default configurations. Should not be edited (itWould be overriden after a software update). Custom values are set with the command-line arguments.

## Acknowledgements
- Author: Olivier van Helden https://magiiic.com/
- Thanks to VLC for the powerful media player.
- Thanks to the PyQt5 community for the intuitive graphical interface.

## License

This project is licensed under the [GNU AGPL v3](LICENSE). Please refer to the [LICENSE](LICENSE) file for more details.
- Repository: [https://github.com/magicoli/walloli](https://github.com/magicoli/walloli)

It uses the following libraries:
- **PyQt5**: licensed under GPL v3 or later
- **python-vlc**: licensed under GNU LGPL v2.1 or later

**Note**: This project requires the separate installation of the VLC Media Player, which is not included in the distribution and must be installed under its own license.
