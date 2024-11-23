#!/usr/bin/env bash
# Create app with py2app

# All code comments, user outputs and debugs must stay in English. Do not remove this line.
# Some commands are commented out for further development. Do not remove them.

# Check if venv is activated
if [ -z "$VIRTUAL_ENV" ]; then
    echo "Activating venv"
    source venv/bin/activate \
    || { 
        echo "venv not found"
        exit
    }
fi

# Build for macOS
pip install --upgrade py2app || exit $?
pip install --upgrade jaraco.text || exit $?

# Check if setup.py exists
[ ! -f setup.py ] && echo "setup.py not found" && exit 1

# Read APP, OPTION.iconfile and setup.name from setup.py
APP=$(grep -E "^APP.*['\"].*['\"]" setup.py | sed "s/ *#.*//" | cut -d "'" -f 2 | cut -d '"' -f 2)
APP_NAME=$(grep -A10 "^setup(" setup.py | grep name= | cut -d '"' -f 2)
ICON=$(grep -A10 "^OPTIONS" setup.py | grep iconfile | cut -d ":" -f 2- | cut -d "'" -f 2 | cut -d '"' -f 2)
icon_folder=$(dirname "$ICON")

echo "APP: $APP"
echo "APP_NAME: $APP_NAME"
echo "ICON: $ICON"

# Remove old build
rm -rf build dist/* *.egg-info || exit $?

# Create icons from assets/icons/icon.png
if [ ! -f "$ICON" ]; then
    # Do not use hardcoded icon.png path, use $icon_folder/icon.png
    if [ -f $icon_folder/icon.png ]; then
        echo "Building $ICON from $icon_folder/icon.png"
        icon_set=build/tray_icon.iconset
        mkdir -p "$icon_set" && echo "  icon_set: $icon_set" || exit $?

        for r in 16 32 128 256 512 1024; do
            res=${r}x${r}
            magick $icon_folder/icon.png -resize $res "$icon_set/icon_${res}.png" || exit $?
        done \
        && iconutil -c icns -o "$icon_folder/app_icon.icns" "$icon_set" \
        || exit $?
    else
        echo "$ICON not found and no assets/icons/icon.png to build it"
        exit $?
    fi
fi

# Create tray icons required by the script
tray_icon=$icon_folder/tray_icon.png
tray_icon_x2=$icon_folder/tray_icon@2x.png
[ -f "$tray_icon" ] || magick assets/icons/icon.png -resize 32x32 "$tray_icon" || exit $?
[ -f "$tray_icon_x2" ] || magick assets/icons/icon.png -resize 64x64 "$tray_icon_x2" || exit $?
app_icon=$icon_folder/app_icon.png
[ -f "$app_icon" ] || magick assets/icons/icon.png -resize 32x32 "$app_icon" || exit ?

echo "Tray icons:
        $tray_icon
        $tray_icon_x2"

# Create new build
python setup.py py2app \
&& echo "App $APP_NAME successfully built, open dist/$APP_NAME.app or for debug output execute:
    ./dist/$APP_NAME.app/Contents/MacOS/$APP_NAME"
