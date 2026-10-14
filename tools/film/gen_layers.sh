#!/bin/bash
# 按生图清单逐张生成（Codex 内置图像生成，一次一张，避免并发出错）：bash tools/film/gen_layers.sh assets/2d/T-038-片头家庭电影
set -u
D="$1"; T="${D#assets/}"
tail -n +2 "$D/分层/生图清单.csv" | while IFS=, read -r id name prompt ref style; do
  ls "$D/drafts/${id}"-v*.png >/dev/null 2>&1 && { echo "跳过 $id（已有草稿）"; continue; }
  args=(gen "$T" "$id" "$D/$prompt" --title "$name")
  [ -n "$ref" ] && args+=(--ref "$D/$ref")
  echo "生成 $id"; python3 tools/art/art.py "${args[@]}" || echo "失败 $id"
done
