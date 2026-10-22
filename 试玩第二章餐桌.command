#!/bin/zsh
set -eu
TRIAL_DIR="${0:A:h}"
GODOT_BIN="${HOME}/.local/bin/godot"
if [[ ! -x "$GODOT_BIN" ]]; then
  GODOT_BIN="/Applications/Godot.app/Contents/MacOS/Godot"
fi
cd "$TRIAL_DIR"
exec "$GODOT_BIN" --path "$TRIAL_DIR/godot" --resolution 1280x720 -- --trial-table
