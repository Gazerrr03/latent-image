# train：固定坐姿过场模型

源文件：`train.blend`。几何与材质在 `TRAIN_MODEL`；构图相机、检查灯光在 `REVIEW_ONLY`。模型由 computer use 在用户 Blender 的 Python 控制台中执行 `scripts/` 里的步骤创建并保存。原客厅未保存现场备份在 `backups/pre-train-session.blend`。

**以 `train.blend` 为准**（10-14 用户确定）。游戏模型：`../../../godot/art/levels/train/train-baked.glb`（由 `baked/train-baked.blend` 烘焙导出）；Godot 场景：`../../../godot/levels/train.tscn`。

`.blend` 与 `backups/` 只留在本机，不进 git。旧版 `train.glb` 及其贴图已不再引用，移到 `backups/godot-unused-10-14/`。

## 当前有效版本

- 用户确认固定坐姿，只转头与读信，不建完整车厢/走廊，不制作行走碰撞。
- 用户三张氛围参考在 `references/`；取方向光、深阴影、哑光旧木与褪色布料。
- **Godot 窗外已经改成黑白手绘线稿。** 材质在 `res://art/levels/train/window_lineart.tres`，图像在 `textures/window-lineart.png`（Godot 资产目录）。Blender 源文件仍保留之前的写实背景，不再追加渲染测试。
- `review/*reviewed.png` 是改为线稿前的真实 Blender 渲染，仅供结构参考，不能代表当前 Godot 输出。
- `review/cameras.json` 为 Blender 相机参数；Godot 已换算坐标轴与竖向 FOV。
- 源文件贴图已打包；GLB 包含贴图、不包含灯光与相机。
- 窗外循环、火车实际音效文件、信纸正文仍待后续制作；当前信件文字来自已有分镜字幕。

## 维护

在 Blender 修改模型后导出到相同 GLB 路径，保留对象名 `窗外画面`，这样 Godot 的线稿材质覆盖可继续使用。不要导出 REVIEW_ONLY。导出应转换曲线的临时副本，保持源文件可编辑。

详细 Godot 调整入口与验收边界见 `docs/关卡/train.md`。这轮在用户要求下停止视觉测试；Godot 已导入并打开编辑器，现场视觉和玩法体验未验收。


## 最新：烘焙与滚动窗景

Godot 当前引用 `train-baked.glb`。`baked/train-lighting-source.blend` 保存烘焙布光；`baked/train-baked.blend` 保存合并 UV 和烘焙结果，原 `train.blend` 保留可编辑结构。复现脚本为 `scripts/06_bake_window_light.py`。

窗光来自矩形面光的离线直接/间接照明，不来自手绘图的发光。Godot 用无光照材质显示已经包含照明的 4096×4096 atlas，避免重复照明；不含动态树影或视角相关高光。

当前长图 `godot/art/levels/train/textures/window-panorama-lineart.png` 为 2172×724。默认 6 秒、203.625 纹理像素/秒；根节点的 Travel Seconds 可调 5—7 秒。一次滚动到末端停留，不是无缝循环。详细公式和限制见关卡文档第 8 节。
