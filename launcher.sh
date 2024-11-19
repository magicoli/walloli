#!/bin/bash

basedir=$(dirname "$0")
PGM=$(basename "$0")
venv_dir=./venv

for arg in "$@"; do
    case "$arg" in
        -v|--verbose) DEBUG=true ;;
    esac
done

log() {
    [ "$DEBUG" = "true" ] || return
    echo "$PGM: $*" >&2
}

end() {
    # if first parameter is a number, use it as exit code
    if [ "$1" -eq "$1" ] 2>/dev/null; then
        exit_code=$1
        [ $exit_code -eq 0 ] || DEBUG=true
        shift
    else
        exit_code=0
    fi

    # if virtual  environment is active, deactivate it
    [ -n "$VIRTUAL_ENV" ] && log "Deactivating virtual environment" && deactivate

    # user remaining parameters as error message if any, or error # if message is empty
    if [ -n "$1" ]; then
        log "Error $exit_code: $*"
    else
        log "Error $exit_code"
    fi

    # Désactiver l'environnement virtuel

    exit $exit_code
}

log "Activating virtual environment"
# make sure ven_dir is an absolute path
venv_dir="$(cd "$(dirname "$venv_dir")" && pwd)/$(basename "$venv_dir")" || exit $?
timestamp_file="$venv_dir/.last_checked"

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
    # if [ "$OS" = "Mac" ]; then
    #     python3 -m venv "$venv_dir" --system-site-packages
    # else
        python3 -m venv "$venv_dir"
    # fi
fi

# Activer l'environnement virtuel
source "$venv_dir/bin/activate" || end $? "Failed to activate virtual environment in $venv_dir"
if [[ "$(which python)" != "$venv_dir/bin/python" ]]; then
  end 1 "Virtual environement is active but Python binary $(which python)
  is not within virtual environment $venv_dir.
Delete the venv directory and run the script again."
fi

# Vérifier les dépendances si elles n'ont pas été vérifiées depuis plus de 6 heures
if [ ! -f "$timestamp_file" ] || [ $(find "$timestamp_file" -mmin +360) ]; then
    log "Check dependencies"
    
    # Vérifier si Tkinter est installé en premier
    python -c "import tkinter" 2>/dev/null || end $? "Tkinter is required to run this script.

    - macos:    brew install python-tk
    - linux:    sudo apt-get update && sudo apt-get install python3-tk -y
    - windows:  idk&idc

    After installing it, delete the directory $venv_dir before running the script again"

    # Si Tkinter est OK, procéder aux installations pip
    pip install --upgrade pip || end $? "Failed to upgrade pip"
    
    pip install python-mpv \
    || end $? "Failed to install $_"

    touch "$timestamp_file"
else
    log "Skip dependency check"
fi

# Exécuter le script Python
log "Launch main script"
python "$basedir/videowall.py" "$@"
