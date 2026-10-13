# 项目约定（给 coding agent）

1926 年庄园悬案游戏，Godot 4.7。参赛截止 2026-10-23。

## 信息来源

- 设计文档：`docs/`（入口 `docs/README.md`）。改动设计后，同步更新对应文档，并在 `docs/08-决策与更新记录.md` 记一笔。
- 剧情的唯一依据：`docs/归档/故事分支分镜（MVP 预设分支）.pdf` 与 `docs/归档/2026-10-对话记录-剧情讨论.md`。**不要参考 Codex 生成的《第七间》。**
- 10-13 起，世界观、人物（每个人物都是同一病人的一种人格）、怪谈“签收人”、结局视角以 `docs/11-叙事层级与世界观.md` 为准，玩家看到的内容以 `docs/剧本-玩家视角.md` 为准；镜头级细节仍以分镜 PDF 为准，两者冲突时按 `docs/11`。
- 事实锚点 F1—F3（`docs/02` 第 3 节）任何内容都不得违反。叙述者不说谎，只省略。
- `game/`（three.js）与 `docs/归档/v0-ERRATA/` 是旧方向，仅作参考，不要在其上继续开发。

## Godot 工程（`godot/`）

- 分镜即数据：剧情内容全部在 `godot/content/story/*.csv`，代码不写死内容。表头与列含义见 `docs/06-技术方案.md` 第 2 节。
- 镜头表的 `actions` 列只能使用 `godot/core/actions.gd` 中的白名单；新增动作要同时改 `actions.gd`、`director.gd` 的 `_do`，并更新 `docs/06` 2.2 节。
- 每个 `.csv` 旁必须有 `importer="keep"` 的 `.csv.import`（校验工具会自动补）。
- 美术模型放 `godot/art/rooms/`，在 `scenes.csv` 的 `model` 列登记；命名约定见 `docs/09` 第 5 节（`hs_`、`spawn`、`exit`、`cam_`、`guide_`、`-col`）。没有模型时按 `godot/content/space/`（房间登记表、房间布局表）搭灰盒。
- 内容表分四个文件夹：`content/story/`（镜头、台词、预设、人物、证据、物件、连线）、`content/space/`（房间、布局）、`content/audio/`（音效表）、`content/ai/`（词表、自述兜底）、`content/visual/`（滤镜表、影像片段表）；影像素材放 `godot/art/footage/`。填表说明在 `docs/填表说明/`。
- 结构：`core/`（状态、内容、播放器、动作）、`world/`（场景宿主、玩家）、`ui/`（临时界面、调试面板）、`shaders/`、`tools/`。

## 验证命令（改动后必须跑）

```bash
G=godot   # ~/.local/bin/godot → /Applications/Godot.app/Contents/MacOS/Godot
# 1. 内容校验：表格互相对得上（退出码 0 = 通过），报告写到根目录“检查报告.md”；队友可双击“检查内容.command”
$G --headless --path godot --script res://tools/validate_content.gd
# 2. 自动通关：无界面走完整条路径（退出码 0 = 到达终局且三组连线完成）
$G --headless --path godot -- --autoplay --line=A   # 三条线 A / B / C 都要跑
# 3. 截图自查：跳到镜号截图后退出（会短暂弹出窗口）
$G --path godot --resolution 1280x720 -- --capture=N1-07 --leak=0 --out=/tmp/x.png
# 可加 --grant-all（发放全部证据）、--telegrams=4、--fx=纪录片片头、--play=示例_录像带（播放影像片段）、--wait=秒、--clean（不显示界面，用于截素材）、--view=记忆（强制终局视角：好奇 / 记忆 / 共情 / 欲望）
```

macOS 没有 `timeout` 命令，长时间运行时用 `perl -e 'alarm(120); exec(@ARGV)' <命令>` 防止卡住。

Godot MCP 已在 `.mcp.json` 配置（Coding-Solo/godot-mcp）：可启动编辑器、运行项目、读取调试输出；没有截图功能，截图用上面的 `--capture`。

游戏内按 F1 打开调试面板：跳镜号、切分支线、切渗漏等级、重载表格、从头开始。

## Git

- 远端：`github.com/Gazerrr03/acknowledged`（private），主分支 `main`。
- 本机 git 未配置 GitHub 凭据，推送时用：`git -c credential.helper= -c 'credential.helper=!gh auth git-credential' push`（或由用户运行一次 `gh auth setup-git`）。

## 协作

- 用户是项目负责人，代码只由用户和 agent 修改；队友只交表格和文件。
- 给队友派任务用 `/task-card`（`.claude/skills/task-card/`），任务卡存 `docs/任务/`。
- 每项计划都要有“只有用户 + agent 也能完成”的兜底。
