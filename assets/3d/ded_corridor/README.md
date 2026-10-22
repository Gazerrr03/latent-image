# ded_corridor：回廊关卡 3D 源

第 5 章演绎关卡“回廊”（需求 [`docs/关卡/ded_corridor.md`](../../../docs/关卡/ded_corridor.md)）。独立维护，不放进 `manor.blend`（10-20 用户）。墙、门、线脚、家具复用 `assets/3d/manor/scripts/room_lib.py` 与 `room_props.py`，和庄园同一种手艺；温室小景借 `21_room_greenhouse.py` 的花架、工作台、陶盆、植物卡片、水槽泵。

| 文件 | 说明 |
| --- | --- |
| `ded_corridor.blend` | 唯一的工作文件（不进 git，只在本机）；集合 `CORRIDOR_MODEL`（导出）/ `REVIEW_ONLY`（审查相机与灯） |
| `scripts/layout.py` | 布置数据（尺寸、门、灯、相框、房间、楼梯），平面图与建模共用；改尺寸只改这里 |
| `scripts/00_plan.py` | B1 平面图与楼梯剖面（→ `assets/2d/T-043-回廊/corridor_平面图-v2.*`、`corridor_剖面_楼梯-v2.*`） |
| `scripts/00b_textures.py` | 本关卡贴图（长条波斯地毯 1 m 一循环、湿脚印、水渍、磨亮的圆圈）→ `textures/`；`photo_wall_night.jpg` 是夜拍照片 `drafts/night_photo-v1.png` 的 JPEG |
| `scripts/_common.py` | 各脚本开头 exec：载入 room_lib / room_props、回廊材质、地毯 / 相框 / 留声机 / 打褶壁灯 / 墙补片线脚等部件 |
| `scripts/01—10` | 建模：01 走廊固定部分 + 暗房门（C2、C3）；02 segB_end 与地毯分节（C4）；03 左墙三扇门与墙补片（C5）；04 支线房间外壳；05 衣帽间（C6）；06 空房间（C7）；07 窄楼梯 + 内窗那侧（C8）；08 照片墙（C9）；09 温室小路小景（C10）；10 椅子与湿脚印（C11）。碰撞（C12）在各脚本里按命名做 |
| `scripts/run_all.py` | 在当前 Blender 文件里清空并按顺序执行 01—19（用户的 Blender 窗口用） |
| `scripts/build_all.py` | 后台重建到 `/tmp`（迭代用） |
| `scripts/20_review.py` | 审查渲染：参考相机 `REF_cam_<机位>` 的白模（clay）或夜景（night）→ `review/` |
| `scripts/21_compare.py` | 设计稿 \| 渲染 对照图 → `review/对照_<机位>.jpg` |
| `scripts/22_check_geometry.py` | 几何体检（manor 09 的回廊版）→ `review/geometry_check.json` |
| `scripts/23_layout_audit.py` | 排布体检（manor 23 的回廊版）→ `review/排布体检.json`、`review/排布俯视.png` |
| `scripts/24_save_archive.py` | 保存 `ded_corridor.blend` 并在 `archive/版本记录.md` 追加一行 |
| `scripts/25_export_glb.py` | 导出 `godot/art/levels/ded_corridor/ded_corridor.glb`（不含相机与灯光，贴图嵌入） |

## 命令

```bash
B=/Applications/Blender.app/Contents/MacOS/Blender; cd assets/3d/ded_corridor
$B -b --factory-startup --python scripts/build_all.py -- /tmp/dc.blend          # 后台重建
$B -b /tmp/dc.blend --python scripts/22_check_geometry.py                      # 几何体检
$B -b /tmp/dc.blend --python scripts/23_layout_audit.py                        # 排布体检
DC_OPEN=123 $B -b /tmp/dc.blend --python scripts/20_review.py -- night cloakroom # 审查渲染（DC_SEGB=2 DC_PHOTO=1 DC_WALLS=1 DC_CHAIRS=1 DC_PRINTS=1 摆状态）
python3 scripts/21_compare.py
$B -b ded_corridor.blend --python scripts/25_export_glb.py                     # 导出
```

用户 Blender 的 Python 控制台（新建空文件或打开 `ded_corridor.blend` 后）：

```python
exec(open('/Users/qizhi_dong/Projects/DigitalMedia/assets/3d/ded_corridor/scripts/run_all.py', encoding='utf-8').read())
NOTE='回廊模型：在用户 Blender 中执行 run_all'; exec(open('/Users/qizhi_dong/Projects/DigitalMedia/assets/3d/ded_corridor/scripts/24_save_archive.py', encoding='utf-8').read())
```

## 坐标与给 Godot 的接口（glb 里的物体名）

Blender x 东 / y 北 / z 高，原点 = spawn 脚下；Godot = (x, z, -y)。尺寸见 `layout.py` 与平面图 v2。

| 物体 | 用途 |
| --- | --- |
| `segB_end`（空物体，x = -6） | 第二段尽头：子物体 `segB_end·端墙-col`、`segB_end·端墙饰面与门套`、`door_end-col`（假门，原点在合页）、`segB_end·地毯末端`、`prop_chair_4`、`photo_wall`。第 n 圈 s = 6,5,4,3,2：`position.x = -s` |
| `segB_sec_1—4` | 第二段地毯每 1 m 一节（x -1→-5）；显示条件 k ≤ s - 2 |
| `doorway_1—3`（门套，原点在洞口中心）下挂 `door_1—3-col`（门扇，原点在合页轴，合页在北侧） | 与 `wall_1—3-col`（墙补片：饰面 + 踢脚 + 压条 + 填洞实体，踢脚上两道浅痕）二选一显示。开缝 = 门扇绕竖轴转负角（向房间里）。门中心 y：1 = 6.0（衣帽间）、2 = 3.6（空房间）、3 = 1.2（窄楼梯） |
| `room_1—3`（空物体） | 三间支线房间（衣帽间、空房间、窄楼梯）；`room_1·空挂钩` 原点在钩座（可摆）；`room_2·磨亮的圆圈` 圆心是 `hs_room_2` 的位置 |
| `darkroom_door-col`、`glow_darkroom` | 暗房门（关死）与门缝红光网格（发光材质 `回廊_暗房门缝红光`） |
| `photo_wall`（空物体）→ `photo_wall·照片` | 照片单独网格，UV 0—1（夜拍照片） |
| `frame_1—8·合影` | 相框（相片材质 `回廊_合影相片`、玻璃 `回廊_相框玻璃` 可换：第 3 圈蒙灰、第 5 圈只剩轮廓） |
| `回廊·壁灯_东1—5`、`回廊·壁灯_第二段1—3` | 壁灯模型（灯泡在原点上方 0.16 m）；光源在 Godot 的 `layer_<n>` 里放 |
| `prop_chair_1—3`、`prop_chair_4`、`prop_print_01—12` | 第 5 圈椅子、第 4 圈湿脚印（默认由程序藏） |
| `gh_*`（x = 30 一带） | 温室小路小景：`gh_figure`（半透明黑影，原点在脚下）、`gh_door-col`（侧门，开着 70°）、`gh_地面-col`… |
| 名字带 `-col` / `-colonly` | Godot 导入时生成碰撞 / 只有碰撞 |

## 现状（10-21）

- 111 个网格、约 6.9 万三角面；glb 16.9 MB。
- 几何体检：缺面 0，共面重叠 0.004 m²（目标 < 0.01）；排布体检：穿进固定结构 0、物件互相穿插 0、卡片穿墙 0（二选一的状态之间不比，见脚本说明）。
- 与 T-043 v2 九张效果图同机位对照：`review/对照_*.jpg`。走廊、暗房门、转角、第二段、衣帽间、空房间、楼梯内窗、照片墙对得上；**温室小路观感还差**（常春藤卡片偏平、偏花，近景偏亮），待修。
- 10-21 已在用户的 Blender 窗口里执行 `run_all` 与 `24` 并保存（版本记录第 3 行），glb 由这份文件导出。
- **建模交付时的边界**：Godot 正式场景与玩法未接入；后续导入、行走与正式接入状态见下方更新。
- 2026-10-21：glb 导进 Godot，无报错；嵌入贴图被 Godot 抽到 `godot/art/levels/ded_corridor/` 下，目录共 29 MB。临时验收场景 `godot/art/levels/ded_corridor/ded_corridor_walktest.tscn`（只有模型 + spawn，不是正式关卡场景）。`probe_walk` 实走：起点 8 个方向都不掉落，墙、暗房门、尽头门、背墙都挡得住；第二段走到尽头门前停（x -5.74）；衣帽间、空房间四面都挡住（长凳也挡得住）；第一跑上到平台 +0.90；温室小路走到北端挡墙。**发现**：第二跑只能上两级（脚下 +1.26）就被天花板顶住（楼梯间净高 2.90，平台以上只剩 2.0 m），比“走到顶才到头”早；要走得更高，得把第二跑上方的天花抬高，待定。实机截图（`walktest_capture.gd`，临时在壁灯处布了点光）存 `assets/3d/ded_corridor/review/godot/`：模型、材质、门缝红光、楼梯小窗看走廊都正常；天花上的斑驳暗影是临时点光被灯罩投影造成的（正式场景里灯具不投影）。
- 2026-10-21（续）：按用户要求把楼梯第二跑上方的天花抬到 4.00（`layout.py` 的 `STAIR_HIGH`；平台上方仍是 2.90，交界处一道挡板），最后一段斜天花从 x 1.90 压到 3.30。Godot 实走：第二跑能上 5 级（脚下 +1.98），顶上两级被斜天花挡住，走到顶附近才到头。已在用户 Blender 里执行 run_all + 24 保存（版本记录 09:43），体检不变（缺面 0、共面重叠 0.004 m²、穿插 0），glb 重新导出并在 Godot 重新导入。

- 2026-10-21（正式接入）：正式场景为 `godot/levels/ded_corridor.tscn`，章节入口已加载本 GLB，旧代码方块空间已移除。三间支线、逐圈门/墙碰撞切换、声源椅子与照片结尾可实际完成；验收截图、逐项判定和可复跑命令见 `docs/验证/2026-10-21-回廊接入/`。模型几何本次未修改。

## 独立 PR 验证（2026-10-22）

本次提交以 `main` 为基线，不包含物品检视、手柄、对话字幕和整篇文案精修。回廊复用主线既有的目标选择器，只有回廊模式使用容错与遮挡检测；其他房间保持原有射线交互。支线观察通过主线既有的笔记本卡片阅读。已在全新 `.godot` 导入缓存下复跑完整流程和交互测试，证据见 `docs/验证/2026-10-21-回廊接入/` 的 10-22 更新。

游戏运行只需要 `godot/` 里的导出模型、贴图和音频，不要求安装 Blender。建模脚本保留既有的本机绝对路径约定；在其他目录重新建模前，需按目录调整脚本路径。设计稿迭代、审查渲染与 `.blend` 工作文件不在本次提交中。
