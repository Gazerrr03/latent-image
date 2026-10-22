#!/bin/zsh
cd -- "${0:A:h}"
exec /Users/qizhi_dong/.local/bin/godot --path "$PWD/godot"
