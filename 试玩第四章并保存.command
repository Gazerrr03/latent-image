#!/bin/zsh
set -eu
TRIAL_ROOT="${0:A:h}"
GODOT_BIN="${commands[godot]:-$HOME/.local/bin/godot}"
if [[ ! -x "$GODOT_BIN" ]]; then
  GODOT_BIN="/Applications/Godot.app/Contents/MacOS/Godot"
fi
if [[ ! -x "$GODOT_BIN" ]]; then
  print "未找到 Godot 4.7 可执行文件，请确认安装在 /Applications/Godot.app 或 ~/.local/bin/godot"
  exit 1
fi
print "第四章试验 · 保存进度试玩"
print "使用试验专属存档；首次从第四章开始，以后继续上次进度。"
exec "$GODOT_BIN" --path "$TRIAL_ROOT/godot" --resolution 1280x720 -- --trial-chapter4 --resume-trial "$@"
