"""把 art/look/materials/ 里的材质接到庄园模型上（按材质名替换，模型本身不动）。

用法：python3 godot/tools/apply_material_overrides.py
- art/look/materials/<材质名>.tres 的文件名 = glTF 里的材质名（例如 manor_室内_灰泥墙漆）。
- 给 art/levels/manor/ 下每个用到这些材质的 .gltf，在它的 .gltf.import 里写上外部材质覆盖；
  Blender 重新导出 .gltf 时 .import 不会被改写，覆盖一直有效。
- 改完后让 Godot 重新导入：godot --headless --path godot --import
"""
import json
import pathlib

ROOT = pathlib.Path(__file__).resolve().parent.parent
MATS = ROOT / "art/look/materials"
MODELS = ROOT / "art/levels/manor"

overrides = {p.stem for p in MATS.glob("*.tres")}
changed = 0
for gltf in sorted(MODELS.glob("*.gltf")):
    imp = gltf.with_suffix(".gltf.import")
    if not imp.exists():
        continue
    used = {m.get("name") for m in json.loads(gltf.read_text()).get("materials", [])} & overrides
    text = imp.read_text()
    start = text.find("\n_subresources=")
    sub, end = {}, -1
    if start >= 0:
        depth = 0
        i = text.index("{", start)
        for j in range(i, len(text)):
            depth += {"{": 1, "}": -1}.get(text[j], 0)
            if depth == 0:
                end = j + 1
                break
        sub = json.loads(text[i:end])
    mats = {k: v for k, v in sub.get("materials", {}).items() if k not in overrides}
    for name in sorted(used):
        mats[name] = {"use_external/enabled": True, "use_external/path": f"res://art/look/materials/{name}.tres"}
    if mats:
        sub["materials"] = mats
    else:
        sub.pop("materials", None)
    block = "_subresources=" + json.dumps(sub, ensure_ascii=False, indent=0).replace("\n\n", "\n") + "\n"
    if start >= 0:
        new = text[: start + 1] + block + text[end + 1:]
    else:
        new = text.replace("\ngltf/", "\n" + block + "gltf/", 1)
    if new != text:
        imp.write_text(new)
        changed += 1
        print(f"{gltf.name}: {', '.join(sorted(used)) or '（清除）'}")
print(f"改了 {changed} 个 .import")
