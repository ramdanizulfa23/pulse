#!/usr/bin/env bash
set -euo pipefail
cd /home/ram/Apps/Notch

# System python3 has pygobject/GTK4 (venv does not).
export PYTHONPATH="$PWD/src"
export GDK_BACKEND=x11
export DISPLAY="${DISPLAY:-:0}"

exec /usr/bin/python3 src/main.py --no-tray "$@"
