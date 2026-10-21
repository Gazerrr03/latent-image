# gh_cellar：密室相机链路技术说明

更新：2026-10-21  
工程：`D:\千人千面blender\新建游戏项目`（Godot 4.7.2，Forward+）  
源场景：`D:\千人千面blender\新建文件夹\Darkroom_1926.blend`

## 1. 本版范围

在第一版可走空间上，完成：

- 拿相机、举镜、滚轮对焦、左键快门
- 第一次曝光 → 显影 → 翻记录本第 4 页 → 装回干版 → `R` 二次曝光 → 再显影 → 空框
- 8 个年份相框（1919—1926）的双视觉
- 实体记录本：单页翻页、第 4 页装片门槛、第 7 页钥匙
- 钥匙虚影、底片盒、1926 实体底片
- 1926 两个物理结局：底片放回盒子 / 装片拍两次
- 1600×900 截图、状态测试、场景串联测试

没有做：存档、显影动画、主工程 Director 接入、独立的 1922/1924 结局。

## 2. 运行时结构

```text
GHCellar (Node3D, levels/gh_cellar.gd)
├── WorldEnvironment
├── Art/CellarModel (GLB)
├── Collision (StaticBody3D，12 个盒)
├── Lighting (7 盏灯)
├── Interactables (17 个 Area3D，layer 2)
├── CameraOnly (只举镜可见的 3D 痕迹)
├── FrameLabels (8 个 Label3D)
├── CameraTag (纸签)
├── KeyProp (第 7 页后出现)
├── Plate1926 (盒内实体底片)
├── Player (cellar_player.tscn)
│   └── Camera3D
│       ├── InteractRay (2.6 m，mask 1|2)
│       └── CameraViewmodel
└── CellarUI (cellar_ui.tscn)
```

`CellarState` 不依赖节点，单独做状态与规则；`gh_cellar.gd` 只负责把状态、射线、相框材质、UI、音效接起来。

## 3. 状态机

`systems/cellar_state.gd` 的 `plate_state`：

| 状态 | 含义 | 下一步 |
|---|---|---|
| `NONE` | 没有干版 | 到片夹换新 / 结束 |
| `LOADED` | 已装干版 | 举镜第一次快门 |
| `EXPOSED` | 第一次曝光 | 放下相机，显影盘 |
| `DEVELOPED` | 第一次显影 | 翻第 4 页 → 片夹装回 |
| `LOADED2` | 已装回 | `R` |
| `ARMED` | 二次曝光待拍 | 举镜、同一年、快门 |
| `EXPOSED2` | 第二次曝光 | 显影盘 |
| `FINAL` | 1926 实体底片已装 | 举镜 1926，左键两次 |
| `NONE` + cleared | 收走 | 相框 state=1（空框） |

关键规则：

- 第一次快门：必须举镜、对焦 ≥ 0.88、有干版、该年 haunted、不是 1926。
- 第二次快门：必须 `ARMED`，且目标年份等于第一次曝光年份。
- **第 4 页门槛**：`DEVELOPED` 后片夹先卡住；`page4_read` 为真才能 `reload_plate` / `arm_second`。
- **第 7 页钥匙**：看到钥匙虚影只设置 `key_seen` 并解锁第 7 页；`mark_page_read("key")` 才设置 `key_taken` / `has_key`。
- 1926：普通快门返回 `final_locked`；开盒、举镜触发 owner，解锁最后一页；拿到底片后才能放回/装片。
- `FINAL`：装片后左键两次，第一次旁白，第二次 `choose_final("shoot")`。
- `return_1926_plate()`：放回盒子 → `choose_final("keep")`。

## 4. 相框双视觉

`shaders/frame_view.gdshader`：

```glsl
col = mix(normal, mix(lens_blur, lens_sharp, focus), camera_mix);
col = mix(col, empty, state);
```

每个年份一组：

```text
art/levels/gh_cellar/textures/frames/
  1920_normal.png
  1920_lens_blur.png
  1920_lens_sharp.png
  1920_empty.png
```

- `camera_mix`：0 = 肉眼，1 = 举镜。
- `focus`：0 = 模糊，1 = 清晰。
- `state`：0 = 有人，1 = 空框。
- 只有 1920/1922/1924/1926 的 lens 图多出一个人；1919/1921/1923/1925 的 lens 与 normal 相同。

## 5. 记录本

`ui/cellar_ui.gd` 的记录本从“一次列出全部页面”改为**单页**：

- `open_notebook(pages, start_index)`；
- `A` / `D` / 方向键 / 滚轮翻页；
- 每次显示页面发 `notebook_page_shown(page_id)`；
- `gh_cellar.gd` 收到后调用 `state.mark_page_read(id)`。

页面门槛：

| 页 | 解锁 | 作用 |
|---|---|---|
| 第 1 页 | 开局 | 建立悬念 |
| 第 2 页 | 第一次举镜 1920 | 确认取景框 |
| 第 3 页 | 第一次显影 | 第一次不是收 |
| 第 4 页 | 第一次显影 | **卡流程**：装片 + R |
| 第 5 页 | 收走 1920 | 空框/记得 |
| 第 6 页 | 举镜看片夹 | 隔年规律 |
| 第 7 页 | 钥匙虚影 | **卡流程**：钥匙从本子滑出 |
| 第 8 页 | 开底片盒 | 只有我记得 |
| 第 9 页 | 1926 主人 | 最终情绪 |

第一次必须走到桌上 `E` 翻；`Tab` 只在 `notebook_opened_once` 后作为快捷查看。
读取第 7 页时，`KeyProp` 在桌上出现，HUD 显示“钥匙：已取得”。

## 6. 1926 实体底片

- 开盒后，`Plate1926` 在柜前出现，但只有 `owner_seen` 后 `plate_1926` Area 才启用。
- `E` 拿取 → `plate_1926_taken`。
- 回柜 `E` → `return_1926_plate()` → keep 结局。
- 回片夹 `E` → `load_1926_plate()` → `FINAL`。
- 举镜 1926，左键两次：
  - 第一次：`final_shots=1`；
  - 第二次：`choose_final("shoot")` → 黑场结局。

不再使用二选一弹窗；`ui.show_choice` 仍保留但未被调用。

## 7. 验证

见根目录 `README.md`。当前：

- `test_import.gd` PASS
- `test_collision.gd` PASS
- `test_flow.gd` PASS：第 4 页门槛、第 7 页钥匙、双结局
- `test_scene_flow.gd` PASS：真实射线 + 记录本翻页 + 钥匙 + 放回结局
- `test_scene_shoot.gd` PASS：实体 1926 底片装片 + 两次快门
- `test_fps.gd`：1600×900 约 147 FPS / 54 draw calls

## 8. 下一阶段

1. 给显影、装片、二次曝光、放回底片加 2—3 秒演出。
2. 烘焙砖/木/石贴图。
3. 存档：`cleared_years`、记录本、钥匙、结局。
4. 把 `CellarState` 接到主工程 Director / SceneHost。
