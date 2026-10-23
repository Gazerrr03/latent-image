# 物品检视资源

来源：`godot/content/story/evidence.csv` 与当前物件表。纸面原文、正反面、页码、纸张类型和真实尺寸登记在 `godot/content/visual/inspection_pages.csv`。不以缺失的完整原文为由编造新剧情。

- `scripts/build_documents.py`：从内容表生成独立原生纹理和 `.tscn`；`--scenes-only` 只更新资源场景。
- `document-manifest.json`：36 个纸面文件，包含来源、文字、原生尺寸和 SHA-256。
- 运行资源：`godot/art/props/inspection/`；实际纸张由 `godot/world/inspection_document.gd` 构成，正反面各自贴图，账簿/手册保留装订边与纸页厚度。
- 当前范围：12 种文稿、18 张纸、36 个正反面。已接入待用户验收；不代表所有线索实物完成。药瓶、照片、织物、鞋底与 t 字笔迹等仍需对应内容，不用通用证据卡替代。
- 实际运行审查：`docs/验证/2026-10-20-物品检视/检视审查.html`。

复现：在仓库根目录运行 `python3 assets/3d/inspection/scripts/build_documents.py`，然后让 Godot 导入资源。需要 Pillow 与 macOS 的宋体字体；跨平台应显式提供同款中文字体，不能默默改成缺字字体。
