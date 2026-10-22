#!/bin/bash
# 全分辨率录制并裁掉开头的加载帧：tools/showcase/render.sh S06 [S07 ...] → ~/Movies/潜影展示/<镜号>.mp4（游戏内录制是 1600x900，Movie Maker 忽略 --resolution；这里用 lanczos 放大到 1920x1080，30fps）
cd "$(dirname "$0")/../.."
out="${SHOWCASE_OUT:-$HOME/Movies/潜影展示}"; mkdir -p "$out" /tmp/sc
for id in "$@"; do
  perl -e 'alarm(300); exec(@ARGV)' godot --path . --write-movie /tmp/sc/$id.full.avi --fixed-fps 30 -- --showcase=$id >/tmp/sc/$id.full.log 2>&1
  n=$(ffprobe -v error -select_streams v:0 -count_frames -show_entries stream=nb_read_frames -of csv=p=0 /tmp/sc/$id.full.avi)
  m=$(grep -o 'SHOWCASE_FRAMES [0-9]*' /tmp/sc/$id.full.log | awk '{print $2}')
  ffmpeg -y -loglevel error -i /tmp/sc/$id.full.avi -vf "select=gte(n\,$((n-m))),setpts=N/30/TB,scale=1920:1080:flags=lanczos" -an -c:v libx264 -crf 14 -pix_fmt yuv420p -r 30 "$out/$id.mp4"
  rm -f /tmp/sc/$id.full.avi
  echo "$id → $out/$id.mp4"
done
