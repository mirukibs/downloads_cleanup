#!/usr/bin/env bash

set -euo pipefail

# Resolve the project root dynamically based on the script's location
PROJECT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
CONFIG="$PROJECT_DIR/config/config.json"
ENGINE="$PROJECT_DIR/src/main.py"

# Activate conda environment
# I source conda.sh to ensure 'conda activate' works in a script
if [ -f "$HOME/miniconda3/etc/profile.d/conda.sh" ]; then
    source "$HOME/miniconda3/etc/profile.d/conda.sh"
elif [ -f "$HOME/anaconda3/etc/profile.d/conda.sh" ]; then
    source "$HOME/anaconda3/etc/profile.d/conda.sh"
elif [ -f "/opt/conda/etc/profile.d/conda.sh" ]; then
    source "/opt/conda/etc/profile.d/conda.sh"
else
    # Fallback if standard paths don't work
    eval "$(conda shell.bash hook)"
fi

#Auto Installer for flock command
install_flock_macos() {
    echo "flock is missing. Attempting to install via Homebrew..." >&2

    # 1. Ensure Homebrew is installed first
    if ! command -v brew >/dev/null 2>&1; then
        echo "Error: Homebrew is not installed. Cannot auto-install flock." >&2
        echo "Please install Homebrew first from https://brew.sh" >&2
        exit 1
    fi

    # 2. Update Homebrew and install flock
    brew install flock

    # 3. Final verification check
    if ! command -v flock >/dev/null 2>&1; then
        echo "Error: Homebrew installation failed or 'flock' is not in your PATH." >&2
        exit 1
    fi
    echo "flock successfully installed via Homebrew!" >&2
}


#Checking of flock command exist
if command -v flock >/dev/null 2>&1; then
    echo "flock is installed."
else
    install_flock_macos
fi

conda activate downloads_cleanup || {
    echo "ERROR: Conda environment 'downloads_cleanup' not found. Please run 'conda env create -f environment.yml'." >&2
    exit 2
}

if [ ! -f "$ENGINE" ]; then
	echo "ERROR: Engine not found at $ENGINE" >&2
	exit 2
fi

if [ ! -f "$CONFIG" ]; then
  echo "ERROR: config.json not found at $CONFIG" >&2
  exit 2
fi

export PYTHONPATH="$PROJECT_DIR"

LOCKFILE="/tmp/downloads_cleanup.lock"
exec 200>"$LOCKFILE"
flock -n 200 || {
  echo "Another run is in progress; exiting." >&2
  exit 0
}

python3 "$ENGINE" --config "$CONFIG" "$@"
EXIT_CODE=$?

exit $EXIT_CODE
