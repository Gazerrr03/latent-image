# 音效

大部分由代码合成。雨声按用户 10-19 要求换成真实录音：`rain_night` 是室外小雨，`rain_glass` 是室内听到的雨打天窗。清单与分类见《04-美术与声音风格》第 7 节，逐条登记在 `godot/content/audio/sounds.csv`。

雨声作者、来源页、CC0 授权及源文件 SHA-256 见 [sources.json](recordings/rain/sources.json)。保存的是 Freesound 公开 HQ MP3，并非原始 WAV／AIFF。游戏版只做 60 Hz 高通、1 秒等功率交叠循环、响度对齐及 Ogg 转码；未叠加合成雨滴或共振。使用 `python3 assets/audio/sfx/scripts/import_recorded_rain.py` 重建。10-19 用户已认可窗边混合试听，采用此比例。

窗边两条实录同时混合：玻璃雨声在音效表基准上再降低 8 dB，窗外小雨降低 6 dB。两层共用距离淡入淡出，离窗 3.5 m 外静音，0.8 m 内达到混合设定音量。参数在 `godot/world/rain.gd`，室外仍单独播放小雨。`recordings/rain/试听-窗边混合.mp3` 是按游戏窗边音量导出的 20 秒混合，不含 BGM 或用户的总音量设置。

```bash
python3 assets/audio/sfx/scripts/synth_sfx.py              # 合成全部，写进 godot/audio/sfx/，并更新音效表的 file 列
python3 assets/audio/sfx/scripts/synth_sfx.py glass_break  # 只重做一个
python3 assets/audio/sfx/scripts/synth_sfx.py --list       # 列出全部配方
python3 assets/audio/sfx/scripts/audition.py               # 排成一盘试听带（preview/试听带.wav + 时间表，不进 git）
```

- `scripts/dsp.py`：合成工具箱（噪声、滤波、模态共振、摩擦吱呀、拨弦、颗粒、声门脉冲 + 共振峰的人声、混响、无缝循环）。
- `scripts/synth_sfx.py`：每个声音一个函数。新声音写一个带 `@sfx(编号, 描述, 分类, loop, 建议音量)` 的函数，跑一遍就会自动加进音效表。
- 单次音效统一到峰值 -3 dBFS，循环声统一到约 -20 dBFS，游戏里的相对响度由音效表的 `volume_db` 决定。
- 雨声来源清单中的编号会被合成脚本自动跳过，避免全量合成时重新覆盖为旧素材。
