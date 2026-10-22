#!/bin/zsh
set -eu
TRIAL_ROOT="${0:A:h}"
GODOT_BIN="/Applications/Godot.app/Contents/MacOS/Godot"
if [[ ! -x "$GODOT_BIN" ]]; then
  print "未找到 Godot：$GODOT_BIN"
  exit 1
fi
print "第四章 · 完整主线连续试玩"
print "从 C4-01 客房起跑：温室与园丁交涉 -> 发现角落活板门 -> 进入地下暗房调查物证与肖像 -> 拿起大画幅相机举镜收人 -> 顺木梯返回温室 -> 调查花园风口 -> 回客房完成 D4 推论与晚间收尾。"
exec "$GODOT_BIN" --path "$TRIAL_ROOT/godot" -- --trial-chapter4
