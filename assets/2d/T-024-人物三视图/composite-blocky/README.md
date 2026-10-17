# 第 6 章叠印 · 方盒子版（10-17）

人物改为方盒子风格后，叠印也随之改做。取代 `../composite-v1/`（拟真肖像版，保留作历史）。

- `portraits/<英文名>.png`：`assets/3d/T-025-人物模型/scripts/build_portraits.py` 渲染。肖像模式去掉缎带、帽檐、面纱、布条与格雷的脸部暗影，六人画上同一套五官位置（对应设定里的“同一张底脸”），按各自头高缩放，所以五官完全重合。
- `composite.png`：`tools/art/composite_blocky.py` 加权叠加（格雷 40%，其余各 12%），黑白冷调、颗粒、暗角。脸是清晰的格雷，帽子、发型、衣领留下重影。同一张交到 `godot/art/footage/composite.png`，第 6 章 `develop(composite.png)` 显影。
- `review.png`：六张原图与叠印并排。

重做：先跑 `build_portraits.py`，再跑 `python3 tools/art/composite_blocky.py`。
