#!/bin/zsh
set -eu
TRIAL_ROOT="${0:A:h}"
GODOT_BIN="/Applications/Godot.app/Contents/MacOS/Godot"
if [[ ! -x "$GODOT_BIN" ]]; then
  print "未找到 Godot：$GODOT_BIN"
  exit 1
fi
print "第四章试验 · M01 地下室密室直通试玩"
print "直接进入 gh_cellar 场景（C4-09），测试密室自由移动、物证检视与木梯返回。"
exec "$GODOT_BIN" --path "$TRIAL_ROOT/godot" -- --trial-cellar
