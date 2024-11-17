#!/bin/bash

basedir=$(dirname "$0")
venv_dir="$basedir/venv"
timestamp_file="$venv_dir/.last_checked"
PGM=$(basename "$0")
DEBUG=true

log() {
    if ! $DEBUG; then
        return
    fi
    echo "$PGM: $*" >&2
}

log "Activate virtual environment"
# Détecter le système d'exploitation
OS="$(uname -s)"
case "$OS" in
    Linux*)     OS=Linux;;
    Darwin*)    OS=Mac;;
    CYGWIN*|MINGW*|MSYS*) OS=Windows;;
    *)          OS="UNKNOWN"
esac

# Créer un environnement virtuel s'il n'existe pas
if [ ! -d "$venv_dir" ]; then
    if [ "$OS" = "Mac" ]; then
        python3 -m venv "$venv_dir" --system-site-packages
    else
        python3 -m venv "$venv_dir"
    fi
fi

end() {
    # if first parameter is a number, use it as exit code
    if [ "$1" -eq "$1" ] 2>/dev/null; then
        exit_code=$1
        shift
    else
        exit_code=0
    fi
    # user remaining parameters as error message if any, or error # if message is empty
    if [ -n "$1" ]; then
        log "Error $exit_code: $*"
    else
        log "Error $exit_code"
    fi

    log "Deactivating virtual environment"
    # Désactiver l'environnement virtuel
    deactivate

    exit $exit_code
}

# Activer l'environnement virtuel
source "$venv_dir/bin/activate"

# Vérifier les dépendances si elles n'ont pas été vérifiées depuis plus de 6 heures
if [ ! -f "$timestamp_file" ] || [ $(find "$timestamp_file" -mmin +360) ]; then
    log "Check dependencies"

    # Vérifier si Tkinter est installé
    python -c "import tkinter" 2>/dev/null
    if [ $? -ne 0 ]; then
        log "Tkinter not found, installing"
        if [ "$OS" = "Mac" ]; then
            brew install python-tk || end $? "Failed to install Tkinter"
        elif [ "$OS" = "Linux" ]; then
            sudo apt-get update && sudo apt-get install python3-tk -y || end $? "Failed to install Tkinter"
        elif [ "$OS" = "Windows" ]; then
            log "Please install Tkinter manually on Windows"
            end 1 "Tkinter installation required"
        else
            end 1 "Unsupported OS"
        fi
    else
        log "Tkinter is already installed"
    fi

    pip install --upgrade pip || end $? "Failed to upgrade pip"

    pip install opencv-python-headless \
    && pip install psutil \
    && pip install pillow \
    && pip install argparse \
    || end $? "Failed to install $_"

    touch "$timestamp_file"
else
    log "Skip dependency check"
fi

log "Launch main script"
# Exécuter le script Python
python "$basedir/videowall.py" "$@"
