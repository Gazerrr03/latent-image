#!/bin/zsh
set -e
TRIAL_ROOT="${0:A:h}"
GODOT_BIN="${commands[godot]:-$HOME/.local/bin/godot}"
if [[ ! -x "$GODOT_BIN" ]]; then
  GODOT_BIN="/Applications/Godot.app/Contents/MacOS/Godot"
fi
mkdir -p "$TRIAL_ROOT/output/chapter3-trial"
exec "$GODOT_BIN" --path "$TRIAL_ROOT/godot" --resolution 1600x900 --log-file "$TRIAL_ROOT/output/chapter3-trial/latest.log" -- --chapter3-house-trial
