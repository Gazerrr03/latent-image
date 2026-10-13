#!/bin/bash
# 双击运行：检查所有表格与文件是否对得上，然后打开中文检查报告。
# 需要本机安装 Godot 4.7（放在“应用程序”文件夹）。
cd "$(dirname "$0")"
GODOT="$(command -v godot || echo /Applications/Godot.app/Contents/MacOS/Godot)"
if [ ! -x "$GODOT" ]; then
  echo "没有找到 Godot。请先把 Godot 4.7 安装到“应用程序”文件夹。"
  read -n 1 -p "按任意键关闭……"
  exit 1
fi
"$GODOT" --headless --path godot --script res://tools/validate_content.gd 2>/dev/null | grep -v "^Godot Engine"
open "检查报告.md"
