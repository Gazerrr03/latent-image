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
print "第四章 · 地下暗房直通试玩（已整合最新交互与桌体对齐修复）"
print "直通地下室密室（C4-09）：复测桌体摆件贴合、大画幅相机取景、R 键二次曝光动态引导、记录本与物证调查通过。完成后顺木梯返回温室。"
exec "$GODOT_BIN" --path "$TRIAL_ROOT/godot" --resolution 1280x720 -- --trial-cellar "$@"
