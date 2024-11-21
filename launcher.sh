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

    exit $exit_code
}

cd $(dirname "$0")

log "Activating virtual environment"
# make sure ven_dir is an absolute path
venv_dir="$(cd "$(dirname "$venv_dir")" && pwd)/$(basename "$venv_dir")" || exit $?
timestamp_file="$venv_dir/.last_checked"

# Detect the operating system
OS="$(uname -s)"
case "$OS" in
    Linux*)     OS=Linux;;
    Darwin*)    OS=Mac;;
    CYGWIN*|MINGW*|MSYS*) OS=Windows;;
    *)          OS="UNKNOWN"
esac

# Create the virtual environment if it does not exist
if [ ! -d "$venv_dir" ]; then
    python3 -m venv "$venv_dir"
fi

# Activate the virtual environment
source "$venv_dir/bin/activate" || end $? "Failed to activate virtual environment in $venv_dir"
if [[ "$(which python)" != "$venv_dir/bin/python" ]]; then
  end 1 "Virtual environement is active but Python binary $(which python)
  is not within virtual environment $venv_dir.
Delete the venv directory and run the script again."
fi

# Check dependencies if not checked in the last 7 days
if [ ! -f "$timestamp_file" ] || [ $(find "$timestamp_file" -mmin +10080) ]; then
    old_debug=$DEBUG
    DEBUG=true
    log "Check dependencies"

    pip install --upgrade pip || end $? "Failed to upgrade pip"
    
    pip install python-vlc \
    && pip install PyQt5 \
    || end $? "Failed to install $_"

    touch "$timestamp_file"
    DEBUG=$old_debug
else
    log "Skip dependency check"
fi

# Launch the main script
log "Launch main script"
python "$basedir/main.py" "$@"
