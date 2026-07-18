#!/usr/bin/env bash

set -euo pipefail

PROJECT_DIR="$HOME/downloads_cleanup"
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
