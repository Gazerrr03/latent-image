# 项目约定（给 coding agent）

1926 年庄园悬案游戏，Godot 4.7。参赛截止 2026-10-23。

## 信息来源

- 设计文档：`docs/`（入口 `docs/README.md`）。改动设计后，同步更新对应文档，并在 `docs/08-决策与更新记录.md` 记一笔。
- 剧情的唯一依据：`docs/02-剧情设计.md`（10-13 晚起的“暗房主线”）；玩法以 `docs/01-玩法设计.md` 为准；预期的演变与已作废的设定见 `docs/14-最新预期（收敛版）.md`。
- 固定事实 T1—T5（`docs/02` 第 2 节）任何内容都不得违反。叙述者不说谎，只省略。
- 旧剧情（罗伊德庄园、签收人、访客簿、事务所与电报、四种结局视角）已归档到 `docs/归档/v1-签收人/`，**不再作为依据**；`godot/content/` 的内容表已于 10-13 迁移到暗房主线（#3）。**不要参考 Codex 生成的《第七间》。**
- `game/`（three.js）、`docs/归档/v0-ERRATA/` 与 `docs/归档/v1-签收人/` 是旧方向，仅作参考，不要在其上继续开发。

## Godot 工程（`godot/`）

- 分镜即数据：剧情内容全部在 `godot/content/story/*.csv`，代码不写死内容。表头与列含义见 `docs/06-技术方案.md` 第 2 节。
- 镜头表的 `actions` 列只能使用 `godot/core/actions.gd` 中的白名单；新增动作要同时改 `actions.gd`、`director.gd` 的 `_do`，并更新 `docs/06` 2.2 节。
- 每个 `.csv` 旁必须有 `importer="keep"` 的 `.csv.import`（校验工具会自动补）。
- **空间不进表（10-14）**：关卡空间与机位构图由用户在 Godot 编辑器里搭成 `godot/levels/<房间id>.tscn`，是空间的唯一依据；不要用代码或表格生成、改写关卡空间。表格只放靠名字就能接上的内容（线索、小物件用哪个模型等）。节点命名见 `docs/填表说明/1.4`（`spawn`、`cam_<机位>`、`hs_<编号>`、`chr_<人名>`、`prop_<编号>`）；小物件模型放 `godot/art/props/`，在 `content/visual/props.csv` 登记。还没有关卡场景的房间暂按 `content/space/`（rooms.csv、layout.csv）搭灰盒，全部搭完后删除。镜头的节奏与运镜优先由 agent 完成。每个关卡的需求写在 `docs/关卡/<关卡id>.md`（一个关卡一篇，索引 `docs/关卡/README.md`），新增或改动关卡时同步。关卡的开发流程、中间产物与最终产物放哪里，按 `docs/关卡/关卡开发规范.md`（基准案例 `train`）。
- 人物资产（设定依据、三视图、模型、管线现状）的总入口是 `docs/人物/README.md`；只以现行六个人物为准，旧剧情的人物资产已于 10-14 删除。
- 项目按两套视角管理：横切面（模块 H1—H16）与纵切面（关卡 0—7），见 `docs/12-关卡拆解.md`；关卡表 `godot/content/levels.csv`，检查报告会按关卡统计进度。现阶段先纵向贯通。
- 内容表分四个文件夹：`content/story/`（镜头、台词、预设、人物、证据、物件、连线）、`content/space/`（房间、布局）、`content/audio/`（音效表）、`content/ai/`（词表、自述兜底）、`content/visual/`（滤镜表、影像片段表）；影像素材放 `godot/art/footage/`。填表说明在 `docs/填表说明/`。
- 结构：`core/`（状态、内容、播放器、动作）、`world/`（场景宿主、玩家）、`ui/`（临时界面、调试面板）、`shaders/`、`tools/`。

## 验证命令（改动后必须跑）

```bash
G=godot   # ~/.local/bin/godot → /Applications/Godot.app/Contents/MacOS/Godot
# 1. 内容校验：表格互相对得上（退出码 0 = 通过），报告写到根目录“检查报告.md”；队友可双击“检查内容.command”
$G --headless --path godot --script res://tools/validate_content.gd
# 2. 自动通关：无界面走完整条主线（退出码 0 = 选定了一种讲法且六组推论 d1—d6 全部成立）
$G --headless --path godot -- --autoplay                # 两种讲法都要跑：
$G --headless --path godot -- --autoplay --view=取代
# 3. 截图自查：跳到镜号截图后退出（会短暂弹出窗口）
$G --path godot --resolution 1280x720 -- --capture=C2-05 --wait=4 --out=/tmp/x.png
# 可加 --leak=0..4、--grant-all（发放全部证据）、--fx=纪录片片头、--play=片头_怪谈（播放影像片段）、--wait=秒、--clean（不显示界面，用于截素材）、--skip-text（文字不等点击；截带文字的镜头时不要加，否则会跑过头）、--hint-test=1..3（看连错提示）、--examine=ev_xxx（打开证据板检视一张证据）、--view=保护|取代（强制终局倾向）
# 4. 关卡碰撞体检（改了关卡场景或模型后跑）：用玩家本身从出生点向各方向走，看会不会掉下去
$G --headless --path godot --script res://tools/probe_walk.gd -- --level=hall --dirs=8
```

macOS 没有 `timeout` 命令，长时间运行时用 `perl -e 'alarm(120); exec(@ARGV)' <命令>` 防止卡住。

Godot MCP 已在 `.mcp.json` 配置（Coding-Solo/godot-mcp）：可启动编辑器、运行项目、读取调试输出；没有截图功能，截图用上面的 `--capture`。

游戏内按 F1 打开调试面板：跳镜号、按章跳转、切终局倾向、切渗漏等级、重载表格、从头开始。按 Tab 翻开证据板，点卡片检视。

## Git

- 远端：`github.com/Gazerrr03/acknowledged`（private），主分支 `main`。
- 本机 git 未配置 GitHub 凭据，推送时用：`git -c credential.helper= -c 'credential.helper=!gh auth git-credential' push`（或由用户运行一次 `gh auth setup-git`）。

## 协作

- 用户是项目负责人，代码只由用户和 agent 修改；队友只交表格和文件。贡献规则（派任务、生产、接入、验证）见根目录 `CONTRIBUTING.md`。
- 生成可直接发给队友的 PDF 派发单：`python3 tools/dispatch/make_dispatch.py docs/任务/T-xxx.md`（需要 `pip3 install --user markdown` 与本机 Chrome）。
- 给队友派任务用 `/task-card`（`.claude/skills/task-card/`），任务卡存 `docs/任务/`。
- 每项计划都要有“只有用户 + agent 也能完成”的兜底。
