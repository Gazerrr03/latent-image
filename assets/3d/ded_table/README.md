# ded_table · 1924 年餐桌（3D 素材说明）

更新日期：2026-10-20

这一关的餐具、干扰物和服务铃是**程序化生成**的：没有 `.blend`、没有 `.glb`、没有外部贴图文件。运行时由 GDScript 车削网格、在引擎里做材质（釉面、锡的划痕、餐巾绣字、纸卡），所以「源文件」就是脚本本身，改形状与材质都改那里。

| 层 | 位置 |
| --- | --- |
| 源（唯一依据） | [`godot/levels/ded_table_props.gd`](../../../godot/levels/ded_table_props.gd) · `build_item(id)` / `build_bell()` |
| 场景 | [`godot/levels/ded_table.tscn`](../../../godot/levels/ded_table.tscn)（餐厅模型 + 开放餐边柜 + 槽位） |
| 玩法与判定 | [`godot/levels/ded_table.gd`](../../../godot/levels/ded_table.gd) |
| 检查截图 | 本目录 [`review/`](review/)（1600×900） |
| 登记 | `assets/登记表.csv` 的 `ded_table_*` 行；2D 图纸另有一行 |
| 需求文档 | [`docs/关卡/ded_table.md`](../../../docs/关卡/ded_table.md) 第 4、10、14 节 |

## 清单

| id | 内容 | 识别特征 | 生成 |
| --- | --- | --- | --- |
| `ambrose` | 安布罗斯：深蓝边大盘、切面水晶玻璃杯、银刀叉、白餐巾、`A.` 卡片 | 蓝边 + 两道蓝线、杯身竖棱、刀叉最正式 | `build_item("ambrose")` |
| `constance` | 康斯坦斯：金边大盘、金边花纹茶杯 + 金边茶碟、银刀叉、白餐巾、`C.` 卡片 | 盘/杯/碟三道金边、杯身花纹 | `build_item("constance")` |
| `iris` | 艾瑞斯：碎花小盘（散落粉点）、小杯 + 茶碟、短叉、绣 `I.` 的餐巾、`I.` 卡片 | 盘面粉点、尺寸小、有茶碟 | `build_item("iris")` |
| `gideon` | 吉迪恩：棕边厚盘、带把手锡制啤酒杯、餐刀、素色餐巾、`G.` 卡片 | 盘沿厚 + 两道棕线、杯有把手和凹痕 | `build_item("gideon")` |
| `lucien` | 卢西恩：棕边旧盘（裂纹 + 金属修补夹）、缺角锡杯、短叉、绣 `L.` 的餐巾、`L.` 卡片 | 折线裂纹、修补夹、锡杯缺口、立体 `L.` | `build_item("lucien")` |
| `toast_rack` | 公用件：烤面包架 | 银座 + 拱架 + 两片带皮吐司 | `build_shared("toast_rack")` |
| `fruit_bowl` | 公用件：水果盘 | 金边浅盘 + 五种带梗叶水果 | `build_shared("fruit_bowl")` |
| `sugar_bowl` | 公用件：糖罐 | 花带盖碗、双耳、金钮、银勺 | `build_shared("sugar_bowl")` |
| `small_bowl` | 公用件：小碗 | 最小的白碗 | `build_shared("small_bowl")` |
| `teapot` | 公用件：茶壶（固定，不拿） | 圈足、弯嘴、C 形把手、青花花带、金盖钮 | `build_shared("teapot")` |
| `decoy_guest` | 客人备用套 | 蓝边更细、多一只面包碟、无首字母 | `build_item("decoy_guest")` |
| `decoy_plate` | 普通小盘 | 没有碎花、没有描边 | `build_item("decoy_plate")` |
| `decoy_cup` | 错锡杯 | 缺口在左前方、杯底无 `L.` | `build_item("decoy_cup")` |
| `decoy_napkin_i` | 绣 `I.` 的餐巾 | 首字母是 `I.` | `build_item("decoy_napkin_i")` |
| `decoy_card_penrose` | 彭罗斯旧地点卡 | 年代错、只能读不能摆 | `build_item("decoy_card_penrose")` |
| `bell` | 桌上服务铃 | 黄铜；九件全对时格雷自动拿起摇铃 | `build_bell()` |
| `ded_table_blueprint` | 1924 年 2D 餐桌图 | 五个位置、南端 `L.` | 2D 图直接复制件 |

## 怎么玩（第一人称）

关内是走动 + 准星交互：`WASD` 走、鼠标看、`E`（或左键）拿起/摆放/翻看/继续格雷聊天框、`Q` 在镜头前展开/收起 1924 年图纸（3D 纸片，不是全屏 UI；展开时滚轮缩放）、`R` 把手里的餐具放回柜子。一次只拿一件，拿起的物件端在画面右下角。屏幕下方不再有 2D 物品栏。

主线里复用 `SceneHost.player`；单独运行时 `ded_table.gd` 自己建一个玩家。进关时主房间的碰撞会临时静音，交接在 `scene_host.enter_level()`。

## 检查截图

| 文件 | 内容 | 拍法 |
| --- | --- | --- |
| `review/ded_table_wide.jpg` | 固定机位宽景：九个金环（五套餐具 + 四件公用件）、铃、固定茶壶 | `godot --path godot res://levels/ded_table.tscn -- --capture-ded` |
| `review/ded_table_wide_v0.jpg` | 上一版宽景（保留对照） | 同上，旧版本 |
| `review/ded_table_cabinet.jpg` | 餐边柜：中层五套餐具、下层四件公用件、柜顶干扰物、左门图纸 | 同上，第二张 |
| `review/ded_table_solved.jpg` | 摆好九件后的宽景：四个公用件沿桌中线一排 | 同上，第三张 |
| `review/ded_table_rings.jpg` | 端着餐具时的细黄铜嵌线圆环（空手隐藏） | `-- --ring-capture` |
| `review/ded_table_close.jpg` | 南端摆好后的近景 | 同上，第四张 |
| `review/ded_table_macro.jpg` | 卢西恩那套的微距：旧盘、锡杯、绣 `L.` 的餐巾 | 同上，第四张 |
| `review/ded_table_crop.jpg` | 餐边柜局部裁切（检查素材用） | 由 `ded_table_cabinet` 裁切 |
| `review/ded_table_hud.jpg` | 第一人称出生点：目标、准星、操作提示 | `-- --capture-hud` |
| `review/ded_table_hud_drawer.jpg` | 拉开餐边柜抽屉：折起的 1924 年餐桌图 | `-- --self-test` |
| `review/ded_table_hud_prompt.jpg` | 准星对着柜里的餐具：`E 拿起：蓝边大盘` | `-- --self-test` |
| `review/ded_table_hud_held.jpg` | 拿起以后：手上提示与右下角端着的盘子 | `-- --self-test` |
| `review/ded_table_hud_blueprint.jpg` | 按 Q 时镜头前展开的 3D 图纸（纸背 + unshaded 画面，不是全屏 UI） | `-- --self-test` |
| `review/ded_table_hud_chat.jpg` | 摆错时格雷的聊天框：署名、最多两行、`E 继续` | `-- --chat-test` |
| `review/ded_table_hud_bell.jpg` | 九件全对：镜头右下的铃复制体 | `-- --bell-test` |
| `review/ded_table_hud_memory.jpg` | 记忆转场旧版（黑场独白占位） | `-- --bell-test` |
| `review/ded_table_memory_wide.jpg` | 1924 记忆宽景：四大人 + 南端少年剪影 | `-- --memory-capture` |
| `review/ded_table_memory_pour.jpg` | 倒茶特写：旧盘、缺角锡杯、茶流、热气 | `-- --memory-close-capture` |
| `review/ded_table_memory_line2.jpg` | 第二句独白：“南边那个位置，是卢西恩的。” | `-- --memory-line2-capture` |

同名 `.png` 是本机原图（`.gitignore` 只把 review 下的 PNG 留在本机）；入库的是 `.jpg`。
`--capture-ded` / `--capture-hud` 默认写到本目录（`ded_table.gd` 的 `_capture_dir()`），也可用 `--capture-dir=<绝对路径>` 指定。
`-- --self-test` 会用真实准星射线走完“拿九件 → 摆九处 → 看图”，最后一件摆对后自动进成功流程，输出 PASS/FAIL；主线里也可以加这个参数。另有 `--chat-test` / `--idle-test` / `--bell-test` 三个专项自查。

## 已知问题（近景）

微距那张暴露的：锡杯口有一圈锯齿、餐巾看起来像白盒子、叉子像梳子。第 6.3 节要求玩家「近看盘沿、杯底、餐巾角」认特征，这三件近看还认不出来，下次做记忆演出时一起修。宽景和柜内视角不受影响。

灯光：`_capture_lights()` 的两盏补光只在截图时加，实际游玩时桌面近景比截图暗；这属于关卡灯光，不属于素材。

## 为什么没进 `content/visual/props.csv`

`props.csv` 只登记场景里的 `prop_<编号>` 占位方块要换成哪个 `.glb`（`scene_host._swap_prop`）。这一关没有占位节点，餐具是运行时建的，没有可替换的模型文件，所以登记在 `assets/登记表.csv`；`props.csv` 仍为空表。
