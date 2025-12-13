#!/usr/bin/env bash

set -euo pipefail


PROJECT_DIR="$HOME/downloads_cleanup"
CONFIG="$PROJECT_DIR/config/config.json"
ENGINE="$PROJECT_DIR/engine/cleanup_engine.py"


if ! command -v python3 >/dev/null 2>&1; then
	echo "ERROR: python3 is required. Install it and try again." >&2
	exit 2
fi

if [ ! -f "$ENGINE" ]; then
	echo "ERROR: Engine not found at $ENGINE" >&2
	exit 2
fi

if [ ! -f "$CONFIG" ]; then
  echo "ERROR: config.json not found at $CONFIG" >&2
  exit 2
fi


LOCKFILE="/tmp/downloads_cleanup.lock"
exec 200>"$LOCKFILE"
flock -n 200 || {
  echo "Another run is in progress; exiting." >&2
  exit 0
}


python3 "$ENGINE" --config "$CONFIG" "$@"
EXIT_CODE=$?

# release lock by exiting (flock closes when script exits)
exit $EXIT_CODE
