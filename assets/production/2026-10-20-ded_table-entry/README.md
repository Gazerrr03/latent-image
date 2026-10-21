# 2026-10-20 · 餐桌关卡接进主线（第一人称 MVP）的验收截图

相机：`--resolution 1280x720`，Godot 4.7.2 mono。

| 文件 | 截的是 | 命令 |
| --- | --- | --- |
| `entry_in_main.png` | 从 `C2-02a` 进入小关卡 `ded_table`：主界面隐藏，玩家第一人称站在长桌西北角，餐边柜抽屉没关严；看到长桌、九个金色圆环（五套餐具 + 四件公用件）与固定茶壶、右手边的餐边柜和关卡自己的 HUD（目标、准星、操作提示） | `-- --capture=C2-02a --skip-text --wait=7` |
| `after_return_C2-03.png` | 关卡自动通关（`--auto-solve` 走完就收起成功卡）后回到主线：C2-03 书房资料室，主 HUD、观察清单、日期角标都恢复 | `-- --capture=C2-02a --skip-text --auto-solve --wait=7` |

`--auto-solve` 是 `ded_table.gd` 的自查开关；正式流程里玩家自己走到餐边柜、拿五套、摆五处、走到桌边摇铃，再收起成功卡。
