#!/bin/zsh
set -eu
TRIAL_ROOT="${0:A:h}"
GODOT_BIN="/Applications/Godot.app/Contents/MacOS/Godot"
if [[ ! -x "$GODOT_BIN" ]]; then
  print "未找到 Godot：$GODOT_BIN"
  exit 1
fi
print "第四章试验 · M00 当前本地基线"
print "目前没有接入 PR34 地下室补丁。人工试玩从 C4-01 开始。"
exec "$GODOT_BIN" --path "$TRIAL_ROOT/godot" -- --trial-chapter4
