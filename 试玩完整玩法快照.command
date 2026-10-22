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
print "庄园悬案 · 完整玩法快照试玩（2026-10-22）"
print "从序幕开始连续体验完整主线与各章关卡交互。"
exec "$GODOT_BIN" --path "$TRIAL_ROOT/godot" --resolution 1280x720 "$@"
