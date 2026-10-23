#!/bin/zsh
cd -- "${0:A:h}" || exit 1
if [[ -x /Applications/Godot.app/Contents/MacOS/Godot ]]; then
  exec /Applications/Godot.app/Contents/MacOS/Godot --path "$PWD/godot"
fi
exec godot --path "$PWD/godot"
