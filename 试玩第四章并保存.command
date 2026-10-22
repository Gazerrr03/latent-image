#!/bin/zsh
set -eu
TRIAL_ROOT="${0:A:h}"
print "使用试验专属存档；首次从第四章开始，以后继续上次进度。"
exec /Applications/Godot.app/Contents/MacOS/Godot --path "$TRIAL_ROOT/godot" -- --trial-chapter4 --resume-trial
