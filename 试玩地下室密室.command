#!/bin/zsh
set -eu
TRIAL_ROOT="${0:A:h}"
GODOT_BIN="/Applications/Godot.app/Contents/MacOS/Godot"
if [[ ! -x "$GODOT_BIN" ]]; then
  print "未找到 Godot：$GODOT_BIN"
  exit 1
fi
print "第四章试验 · A1 摄影流程复测"
print "直接进入地下室；复测调查、拿相机、两次曝光与显影、木梯返回。返回后停在温室供你反馈。"
exec "$GODOT_BIN" --path "$TRIAL_ROOT/godot" -- --trial-cellar
