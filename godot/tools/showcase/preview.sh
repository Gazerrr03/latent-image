#!/bin/bash
# 低分辨率试录并拼图：tools/showcase/preview.sh S06 [S07 ...] → /tmp/sc/<镜号>.png
# 默认 4 帧（2x2）；环境变量 FRAMES=12 出 12 帧（4x3），看玩法录屏的节奏用
cd "$(dirname "$0")/../.."
mkdir -p /tmp/sc
N=${FRAMES:-4}
for id in "$@"; do
  perl -e 'alarm(240); exec(@ARGV)' godot --path . --write-movie /tmp/sc/$id.avi --fixed-fps 30 --resolution 640x360 -- --showcase=$id >/tmp/sc/$id.log 2>&1
  n=$(ffprobe -v error -select_streams v:0 -count_frames -show_entries stream=nb_read_frames -of csv=p=0 /tmp/sc/$id.avi)
  m=$(grep -o 'SHOWCASE_FRAMES [0-9]*' /tmp/sc/$id.log | awk '{print $2}')
  s0=$(( n - m ))
  sel=""
  for k in $(seq 0 $((N-1))); do
    f=$(( s0 + (m-1)*k/(N-1) ))
    sel="$sel+eq(n\\,$f)"
  done
  cols=2; [ $N -gt 4 ] && cols=4
  rows=$(( (N+cols-1)/cols ))
  ffmpeg -y -loglevel error -i /tmp/sc/$id.avi -vf "select='${sel#+}',scale=800:-1,tile=${cols}x${rows}:padding=4" -frames:v 1 /tmp/sc/$id.png
  rm -f /tmp/sc/$id.avi            # AVI 每条上 GB，用完就删
done
