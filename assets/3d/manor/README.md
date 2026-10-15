# manor：奥瑞尔庄园大地图 · 3D 源

源文件 `manor.blend`（本机，不进 git）。依据**只用** `assets/2d/T-039-奥瑞尔庄园全貌/v1/`（10-14 用户验收的现行布局）；上级目录是另一套布局，不要混用。

## 阶段 1 目标：墙体结构，区分房间与周边环境（10-14）

**目标**：按 v1 平面图在 Blender 里搭出可以在 Godot 里走的整栋庄园白模，让每个房间、两层地面和周边地形都清楚可辨。

**验收（已达到）**

- [x] 一楼、二楼全部墙体，门窗洞口按 SVG 切出（门 / 窗 / 无隔墙洞口 / 凸窗 / 低位百叶）；未匹配洞口只剩温室北门（单独建）
- [x] 房间尺寸对上 `manor_设计坐标-v1.json`：25 块房间地面全部按 json 命名，颜色区分 可进入 / 只能走过 / 不可进入
- [x] 楼板（二楼留楼梯井）、两跑楼梯（各 10 级，0.18 / 0.28，平台 +1.80）、凸窗、四根烟囱、双坡屋顶（檐口 +6.80、屋脊 +9.10，默认隐藏）
- [x] 环境：前院 ±0.00、西侧坡地 ±0.00→+3.60、后花园台地 +3.60、东侧低位服务院与挡土墙、厨房翼、温室（6×6，+3.60，北门）、泥地、道路、北侧树篱、前院围墙与大门缺口
- [x] 导出 `godot/art/levels/manor/manor_shell.glb`：40 个物体，`-col` 结尾的 12 组自动生成碰撞
- [x] Godot 关卡场景 `godot/levels/manor.tscn`：结构 / 灯光 / 接口（`spawn` 在正门外，`cam_c1_gate`—`cam_c4_vent` 对应总平面 C1—C4）
- [x] 审查图：`review/` 下顶视（一楼、二楼）、东南鸟瞰（有无屋顶）、C1—C4，以及 Godot 实机一帧 `godot_C1_南门外.jpg`

**不在本阶段**：家具与物件、`hs_` 可检查物件、人物站位、材质与光、门扇、楼梯扶手、西侧小路的台阶细化、温室内部、镜头表接入（`manor` 还不是房间登记表里的房间，游戏流程仍走旧的分房间灰盒）。

## 阶段 2 目标：立面细节与造景，与参考图逐项对应（10-14）

**目标**：先把东侧低位服务院旁的陡坎改成坡道（用户要求），再让立面与造景和 T-039 v1 的六张效果图逐项对应。房间内饰放到最后一步。

**验收**：按六张效果图的视角各渲染一张，与参考图左右并排（`review/compare/对照_*.jpg`），逐项列出对应关系与差异。

**地形改动**：东侧 X 25.2—33 改为坡道，N −2.0 处 ±0.00 坡到 N 11.40 处 +3.60（约 27%）；坡道西侧加翼墙挡住低位服务院；挡土墙只保留在服务院与温室之间（X 19.2—25.5）。这条坡道让前院可以从东侧上到后花园，成了一条新的前后通道，叙事上的封闭（序章 0B）要连同西侧绕屋路一起考虑。

### 参考图元素 → 模型

| 参考图里的元素 | 出现在 | 模型里的物体 |
| --- | --- | --- |
| 蜂蜜色石灰岩墙面 | 全部 | 材质 `manor_外墙石` |
| 双坡石板瓦屋顶、屋脊瓦 | 全部 | `屋顶_slate`、`屋顶_dress` |
| 东西两端山墙压顶、檐角托石与尖饰、山尖尖饰 | 人视角 1、2，鸟瞰前、后 | `屋顶_stone`、`屋顶_dress` |
| 正面中央山墙、山尖尖饰、竖向小窗、交叉屋面 | 人视角 1、2，鸟瞰前 | `屋顶_*` |
| 二楼中央凸窗：石质竖棂、横棂、逐层收进的托石 | 人视角 1、2，鸟瞰前 | `立面_dress`、`立面_glass` |
| 六上六下推拉窗：白框 6+6 格、石窗套、窗台 | 人视角 1、2，鸟瞰前 | `立面_paint`、`立面_dress`、`立面_glass` |
| 正门：双扇橡木门、石门套与门楣、门前台阶 | 人视角 1、2，鸟瞰前 | `立面_oak`、`立面_dress` |
| 正门两侧壁灯 | 人视角 1、2 | `立面_lamp`、`立面_iron` |
| 正门两侧石花钵与黄杨球 | 人视角 1、2 | `立面_stone`、`立面_box` |
| 四根烟囱、帽檐、每根两只陶土烟囱帽 | 全部 | `屋顶_stone`、`屋顶_clay` |
| 檐口线脚、勒脚、檐沟、落水管 | 人视角 2、4 | `立面_dress`、`立面_iron` |
| 窗间墙上的攀援植物、一二层之间的横向藤蔓 | 人视角 1、2，鸟瞰前 | `造景_ivy` |
| 墙根花境（绣球等）与花境前的矮黄杨篱 | 人视角 1、2，鸟瞰前 | `造景_soil`、`造景_hyd`、`造景_box-col` |
| 碎石前庭与车道 | 人视角 1，鸟瞰前 | `造景_gravel` |
| 两块草坪、黄杨矮篱围边、四角黄杨球 | 人视角 1，鸟瞰前 | `造景_lawn`、`造景_box-col` |
| 干砌石围墙与压顶、两根门柱与石球、铸铁双扇大门 | 人视角 1，鸟瞰前 | `前院围墙-col`、`造景_stone-col`、`造景_dress-col`、`造景_iron-col` |
| 东侧低位厨房翼：南山墙、石板屋顶、窗 | 人视角 1、2，鸟瞰前、后 | `厨房翼墙体-col`、`屋顶_*` |
| 温室：铸铁玻璃、石砌矮墙、屋脊花饰与端头尖饰、北门 | 人视角 1、2、4，鸟瞰前、后 | `温室玻璃-col`、`温室框架-col`、`屋顶_iron`、`屋顶_stone` |
| 西侧坡地小路、靠房一侧的随坡石砌矮墙、沿路矮灯 | 人视角 3，鸟瞰前 | `道路`、`造景_stone-col`、`造景_lamp` |
| 西侧台地边的石栏与石瓮 | 人视角 2，鸟瞰前 | `造景_stone-col`、`造景_dress-col` |
| 后立面：后门、两扇窗、低位百叶与石质托边 | 鸟瞰后、人视角 4 | `立面_olive`、`立面_*`、百叶为 `立面_iron` |
| 后墙下的裸露泥地（不种植物） | 鸟瞰后、人视角 4 | `泥地` |
| 后花园：长方形草坪、环形碎石路、花境 | 鸟瞰后 | `造景_lawn`、`造景_gravel`、`道路` |
| 后花园北侧矮石墙、柱墩与石瓮，墙外树篱 | 鸟瞰后 | `造景_stone-col`、`造景_dress-col`、`树篱-col` |
| 低位服务院挡土墙顶的石栏与柱墩 | 鸟瞰后，人视角 2 | `造景_stone-col`、`造景_dress-col` |
| 四周秋色阔叶树与针叶树 | 全部 | `造景_amber`、`造景_rust`、`造景_olivef`、`造景_pine`、`造景_trunk` |

### 与参考图仍有的差异（有意保留或留到后面）

- **屋脊 +10.0**：按效果图把屋顶做陡；剖面图是 +9.10。屋顶不影响行走，以效果图为准。
- **人视角 3**：参考图里西立面有三个山墙和成排窗户，与 v1 平面（西墙每层一扇窗）不符。来源说明里这张只作“坡道氛围参考”，模型以平面为准。
- **正门门洞**：参考图是都铎式尖拱，模型是方门洞加门楣。
- **材质与光**：现在是纯色材质，没有石材纹理、雨水反光、窗帘与室内灯光；窗玻璃和灯笼的夜间自发光只在对照渲染里打开（05 脚本）。
- **植物**：藤蔓、灌木和树是低面数占位，体量与位置对得上，形态还很粗。
- 远景（山谷、天空）与雨，不在模型范围内。

### 阶段 2 文件

| 文件 | 内容 |
| --- | --- |
| `scripts/04_facade_landscape.py` | 立面细节、屋顶、造景；读 01 写出的 `review/build_report.json` 里的外墙门窗；可重复运行 |
| `scripts/05_compare_refs.py` | 按六张效果图的视角渲染（EEVEE，白天 / 夜景） |
| `scripts/06_stitch_compare.py` | 拼“参考 | 模型”对照图（系统 Python + PIL） |
| `review/compare/` | 对照图与模型渲染 |

## 阶段 3 目标：精修，几何干净、材质真实、Godot 里不出显示问题（10-14—10-15）

**目标**：用户检查阶段 2 后指出凸窗西侧缺面、厨房翼与主楼交接处闪斜纹，且整体太粗糙。本阶段把庄园外观做到“游戏美术一眼看得出用心”的精度，同时保证导入 Godot 不出任何显示问题。

**验收结果**

| 验收项 | 结果 |
| --- | --- |
| 几何体检（`09_check_geometry.py`）：共面重叠（z-fighting）、实体缺面 | 阶段 2：共面重叠 90 处 / 944 m²，缺面 42 条 → 阶段 3：**缺面 0 条；共面重叠只剩 1 处 0.001 m²**（窗套斜接线上的采样噪声，埋在墙里，看不见） |
| 用户指出的两处 | 凸窗六面闭合（石竖棂 + 玻璃）；厨房翼与主楼东墙交接无斜纹。对比图 `review/beauty/检查1_凸窗西侧.jpg`、`检查2_厨房翼交接.jpg` |
| 真实贴图 | `10_textures.py` 程序生成、可无缝平铺：方石、细石、干砌毛石、石板瓦、碎石、草坪、泥地、花坛土、橡木、树皮、窗帘；叶片与花卉为带透明通道的图集（秋叶、黄杨、常春藤、针叶、绣球、草丛及四种叶团） |
| 精度 | 线脚与窗套按截面扫掠、尖饰与烟囱帽用旋转体、铁艺用管体；推拉窗（窗樘、上下扇、羊角、3×2 窗格条、玻璃、窗帘）、四心拱正门（拱肩、门套、滴水线、装饰钉与铁环）、马车灯、凸窗托石、转角隅石、勒脚、檐口、S 形檐沟与落水管、逐层石板瓦、脊瓦、山墙压顶与尖饰、温室铸铁框与屋脊花饰、手压泵、干砌石墙“公母”压顶、铸铁大门 |
| 植物 | `12_vegetation.py`：30 棵近景树（阔叶递归分枝 + 针叶树）、远景山丘与成片树林、绿篱与黄杨球（芯体 + 贴面叶团）、绕开门窗生长的常春藤、绣球花境、草丛、落叶、温室盆栽；约 3 万张叶片卡片 |
| 参考图对照 | `review/compare/对照_*.jpg`（六张，`13_beauty.py` 渲染：白天 / 阴天 / 雨夜） |
| 近景细节 | `review/beauty/`：正门、凸窗与山墙、推拉窗与藤蔓、屋顶与烟囱、铁门与门柱、温室、后墙通风口与泥地、东南鸟瞰 |
| Godot | 导入 47 个网格、9 组碰撞；`godot/tools/capture_level.gd` 加临时天空与阳光后截图，见 `review/godot/`；内容校验通过，两种讲法自动通关通过 |
| 在用户 Blender 中执行 | **完成**（10-15 01:00）：computer use 在用户的 Blender 里依次执行 11、12、14；材质预览下用 `REF_检查1_凸窗西侧`、`REF_检查2_厨房翼交接` 两个机位复查了用户指出的两处；工作文件已保存，并留档快照 |

**规模**：建筑与地形约 14.5 万三角面，植物约 15.8 万三角面；贴图约 45 MB（JPEG 颜色 / 法线 + PNG 透明图集），glTF 几何 19.6 MB。

### 保存、维护与留档

| 文件 | 位置 | 进 git | 用途 |
| --- | --- | --- | --- |
| 工作文件 | `assets/3d/manor/manor.blend` | 否 | 日常在 Blender 里打开、修改的就是它；贴图引用 `godot/art/levels/manor/textures/`，与游戏共用一套 |
| 留档快照 | `assets/3d/manor/archive/manor-<日期时间>.blend` | 否 | 每次重要修改后用 14 存一份，贴图已打包，单独拷走也能打开 |
| 版本记录 | `assets/3d/manor/archive/版本记录.md` | 是 | 每个快照一行：时间、物体数、三角面、几何体检、说明 |
| 会话备份 | `assets/3d/manor/backups/pre-manor-session-*.blend` | 否 | 11 执行前自动另存的上一个未保存会话 |

**手工修改之后怎么维护**：在 Blender 里改完 → Python 控制台执行 `NOTE = '改了什么'`、再执行 `exec(open('/Users/qizhi_dong/Projects/DigitalMedia/assets/3d/manor/scripts/14_save_archive.py').read())`（保存工作文件 + 快照 + 记录）→ 后台跑 09 体检与 03 导出。**手工改过之后不要再跑 11、12**：它们会从图纸重新生成、覆盖手工修改（11 会新建 manor.blend，12 会重建“植物”集合）。要改生成规则（尺寸、构件、植物分布），改 11 / 12 脚本再整体重跑，然后用 14 留档。

### 阶段 3 的流水线（取代 01、04、05）

```bash
python3 assets/3d/manor/scripts/10_textures.py                                        # 贴图（系统 Python）
blender -b --factory-startup --python assets/3d/manor/scripts/11_build_manor.py          # 建筑、立面、屋顶、地形、硬质景观（会新建 manor.blend）
blender -b --factory-startup assets/3d/manor/manor.blend --python assets/3d/manor/scripts/12_vegetation.py   # 植物与远景
blender -b --factory-startup assets/3d/manor/manor.blend --python assets/3d/manor/scripts/09_check_geometry.py # 几何体检
blender -b --factory-startup assets/3d/manor/manor.blend --python assets/3d/manor/scripts/13_beauty.py        # 美术渲染与参考对照
python3 assets/3d/manor/scripts/06_stitch_compare.py                                   # 拼对照图
blender -b --factory-startup assets/3d/manor/manor.blend --python assets/3d/manor/scripts/03_export_glb.py     # 导出 godot/art/levels/manor/manor.gltf
godot --path godot --resolution 1600x900 --script res://tools/capture_level.gd -- --level=manor --out=/tmp/manor_godot   # Godot 实机截图
```

在用户的 Blender 里：Python 控制台依次 `exec(open('…/11_build_manor.py').read())`、`exec(open('…/12_vegetation.py').read())`。

**几何原则**（写进了 11 的文件头）：墙、楼板、山墙、烟囱身、凸窗实体先拼成一个结构，做精确布尔并集（没有内部面、没有共面重叠）；所有装饰构件嵌入墙体几厘米，不与墙面共面；地形是一张连续网格，草坪 / 碎石 / 泥地 / 花坛土是同一网格上的不同面；朝向室内的墙面自动换成灰泥。

**其他取舍**：西墙外加了 0.8 m 宽的采光井（地面 ±0.00），否则西侧坡道会埋掉一楼客厅西窗；玻璃为半透明（看得见窗帘），Godot 里是透明材质；夜景的地灯、室内灯只在 13 的渲染里，关卡里的灯光以后在 Godot 里布。01、04、05 保留作历史，不要再用（01 会覆盖 manor.blend）。

## 房间模块（10-15 起）：每个房间一份空间，按原位嵌回庄园

划分与状态见 `docs/关卡/manor.md`“房间划分与状态”。做法：

- **原位建模**：房间直接建在 manor 坐标上，嵌回庄园不需要对位；Godot 里 `manor.tscn` 也是原位放置。
- **分工以墙的内表面为界**：结构墙、洞口、楼板、天花、窗框玻璃归 manor（11）；墙面饰面、踢脚 / 墙裙 / 天花线脚、门扇门套、窗台板与窗帘、壁炉、家具、物件归房间。饰面离 manor 墙面 1.2 cm，构件嵌入不共面。manor 里被房间接管的窗帘由房间脚本删掉，11 的 `ROOM_OWNED` 保证重建时也不再生成。
- **集合**：`ROOMS / 房间_<名> / {房间_<名>_空间, 房间_<名>_状态_<状态>…}`。一个房间只有一份空间；版本是状态子集合，视图层里默认只开第一个状态。
- **陈列区**（`REVIEW_ONLY / 陈列区`，庄园东侧 X 42 起）：每格是“空间 + 一个状态”的集合实例，改原件陈列区同步变化；只看不导出。
- **导出**：空间一份 `godot/art/levels/manor/room_<id>.gltf`，每个状态一份 `room_<id>__<状态>.gltf`，贴图共用 `textures/`。

| 脚本 | 作用 |
| --- | --- |
| `room_lib.py` | 公用：材质（`室内_` 开头的每次重建）、多材质家具物体、墙面饰面留洞口、沿轮廓扫掠线脚、门窗套、贴脸板、四块面板门扇（原点在合页轴）、陈列区、审查相机 |
| `room_props.py` | 公用的家具与小物件：抽屉拉手、书、挂钟、油画、吊灯、篮子、地毯 |
| `16_room_guest.py` | 客房 + 前室（状态：夹层未发现 / 夹层已打开） |
| `17_room_darkroom.py` | 暗房（状态：门完好 / 门撞坏 / 冲洗布置；开关：暗房·红灯、暗房·白灯） |
| `21_room_greenhouse.py` | 温室（无状态；植物卡片：蕨叶、阔叶、白花、粉花、常春藤） |
| `09b_overlap_detail.py` | 体检的补充：逐对打印某个物体里重叠的三角形 |
| `18_room_review.py` | 房间审查渲染：白天（西南阳光 + 窗口天光）与夜晚（台灯、吊灯、炉火），输出 `review/rooms/<房间>/` |
| `19_room_compare.py` | 系统 Python：拼“参考 | 白天 | 夜晚”对照图 |
| `20_room_export.py` | 导出房间到 Godot（空间 + 各状态） |

流程：后台迭代 `Blender -b manor.blend --python scripts/16_room_guest.py -- /tmp/room_guest.blend` → `18` 渲染 → `19` 对照 → `09` 体检（房间单面件不查缺面；同一房间不同状态之间的重叠不算）→ 在用户 Blender 的 Python 控制台执行 16 → `14_save_archive.py` 留档 → 后台 `03`、`20` 导出 → Godot `capture_level.gd --only=客房`。

**暗房与温室（10-15）**：暗房 24 个物体约 1.0 万面，温室 15 个物体约 1.6 万面；manor 里归它们的东西（温室侧门外门扇、百叶背板、温室简化台架 / 手压泵 / 盆栽）由脚本删除，`11` 的 `ROOM_OWNED` / `GH_BY_ROOM` 保证重建时也不生成。新贴图：蕨叶、阔叶、白花图集。留档 `archive/manor-2026-10-15_0603.blend`。

**客房（10-15）**：31 个物体、约 2.5 万面。壁炉在西墙南段（西南烟囱下）、书桌在西窗下、床头靠东墙、衣柜与五斗柜靠北墙、穿衣镜在前室东墙正对房门；挂钟停在七点；炉栅里有一角没烧尽的相纸。新贴图：条形地板、奶油色灰泥、波斯地毯、桃花心木、芥末黄针织、提花窗帘、亚麻、两幅油画（`10_textures.py`）。对照图 `review/rooms/客房/`，Godot 截图在其 `godot/` 子目录。体检：庄园 + 客房共面重叠 0.009 m²（都在构件交接内部），缺面 0。留档 `archive/manor-2026-10-15_0442.blend`。

## 坐标

原点在主楼西南外墙角。Blender x = 东（X），y = 北（N），z = 标高；导出 glTF 后即 Godot `(X, 标高, -N)`，与尺寸表一致。

## 文件

| 文件 | 内容 |
| --- | --- |
| `scripts/01_build_shell.py` | 读 v1 的一楼、二楼平面 SVG 与设计坐标 json，搭整个模型；会先把当前未保存的会话另存到 `backups/`，再新建空文件，最后存为 `manor.blend` |
| `scripts/02_render_review.py` | Workbench 审查渲染到 `review/` |
| `scripts/03_export_glb.py` | 按 `MANOR_MODEL` 集合导出 glb（不靠选择，后台模式下选择不可靠） |
| `review/build_report.json` | 墙段数、洞口数、未匹配洞口、每个房间的位置与尺寸 |

`manor.blend` 里分两组：`MANOR_MODEL`（导出：一楼墙体、二楼墙体、楼板、楼梯、房间地面、厨房翼、温室、地形、屋顶）和 `REVIEW_ONLY`（不导出：房间名文字、三张图纸叠图（默认隐藏，可打开对位）、审查相机 `REF_*`）。

## 重建

```bash
# 在用户的 Blender 里（Python 控制台）
exec(open('/Users/qizhi_dong/Projects/DigitalMedia/assets/3d/manor/scripts/01_build_shell.py').read())
exec(open('/Users/qizhi_dong/Projects/DigitalMedia/assets/3d/manor/scripts/04_facade_landscape.py').read())
# 或后台
blender -b --factory-startup --python assets/3d/manor/scripts/01_build_shell.py
blender -b assets/3d/manor/manor.blend --python assets/3d/manor/scripts/04_facade_landscape.py
blender -b assets/3d/manor/manor.blend --python assets/3d/manor/scripts/05_compare_refs.py && python3 assets/3d/manor/scripts/06_stitch_compare.py
blender -b assets/3d/manor/manor.blend --python assets/3d/manor/scripts/02_render_review.py
blender -b assets/3d/manor/manor.blend --python assets/3d/manor/scripts/03_export_glb.py
```

**注意**：01 会整体重建 `manor.blend`，之后要再跑 04 补上立面与造景。阶段 2 起如果在 Blender 里手工改了模型，就不要再跑 01，改为在 Blender 里直接编辑、再跑 03 导出。

## 已知取舍

- 门高：一楼 2.40（正门 2.70），二楼 2.20，厨房 2.10；窗台 0.90，窗楣一楼 2.70、二楼 2.50。图纸没写，阶段 2 可改。
- 西侧小路只是坡面上的一条路面，坡度均匀（约 32%），没有做台阶，实际可走性要在 Godot 里试。
- 墙按图纸中线 ±0.15 m 生成，房间相交处有重叠的墙块（不影响外观与碰撞）。
