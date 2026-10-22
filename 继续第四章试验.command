#!/bin/zsh
set -eu
TRIAL_ROOT="${0:A:h}"
exec /Applications/Godot.app/Contents/MacOS/Godot --path "$TRIAL_ROOT/godot" -- --trial-chapter4 --resume-trial
