# TASK-12：不眠夜与定影音效

新增 `heartbeat_low`（8 秒循环，-12 dB）、`storm_window`（23 秒循环，-10 dB）、`shutter_lock`（0.65 秒单次，-6 dB）。均为项目内可复现合成，不使用新增外部录音；现有实录雨声继续按窗边距离播放，storm_window 是叠加的窗框拍击、风与闷雷。

资源配方：`assets/audio/sfx/scripts/synth_sfx.py`，可用 `python3 assets/audio/sfx/scripts/synth_sfx.py heartbeat_low storm_window shutter_lock` 重建。

镜前死寂由运行时保障：C7-03 进入时停止循环音效与配乐；C7-03/04 拦截除 shutter_lock 以外的新音效（含上一镜头延迟声音与灯丝嗡鸣）。rain.gd 同步将天气实录静音，保持窗上的雨迹。C7-05 起恢复通常规则。

镜头表接线由主执行者负责：C6 自查/暗房/返回各段恢复 heartbeat_low 与 storm_window；C7-01 雨停仅保留心跳；C7-03 全静音；C7-04 shutter_lock。

已验证：Godot 4.7.2 无界面导入完成，无脚本错误；三份 OGG 经 ffprobe 验证为 44.1kHz 双声道、时长分别为 8.0007/23.0008/0.6502 秒；内容检查通过（0 错误，10 条已有场景/布局提醒）。本记录不代表主观听感验收，整体双终局由主执行者统一回归。

最终接线补充：第七章整章 `raining()` 返回 false，确保 C7-01 黎明前雨停与文档一致；不是只在镜前压低音量。`storm_window` 配方 `loop=True`、sounds.csv 登记“是”，scene_host 根据表设置 AudioStreamOggVorbis.loop，循环注册链完整。
