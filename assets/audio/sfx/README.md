# 音效

全部由代码合成，不用外部素材（用户 10-17）。清单与分类见《04-美术与声音风格》第 7 节，逐条登记在 `godot/content/audio/sounds.csv`。

```bash
python3 assets/audio/sfx/scripts/synth_sfx.py              # 合成全部，写进 godot/audio/sfx/，并更新音效表的 file 列
python3 assets/audio/sfx/scripts/synth_sfx.py glass_break  # 只重做一个
python3 assets/audio/sfx/scripts/synth_sfx.py --list       # 列出全部配方
python3 assets/audio/sfx/scripts/audition.py               # 排成一盘试听带（preview/试听带.wav + 时间表，不进 git）
```

- `scripts/dsp.py`：合成工具箱（噪声、滤波、模态共振、摩擦吱呀、拨弦、颗粒、声门脉冲 + 共振峰的人声、混响、无缝循环）。
- `scripts/synth_sfx.py`：每个声音一个函数。新声音写一个带 `@sfx(编号, 描述, 分类, loop, 建议音量)` 的函数，跑一遍就会自动加进音效表。
- 单次音效统一到峰值 -3 dBFS，循环声统一到约 -20 dBFS，游戏里的相对响度由音效表的 `volume_db` 决定。
- 有更好的录音时，直接替换 `godot/audio/sfx/<编号>.ogg`，并把音效表 note 改成来源。之后不要再对这个编号跑合成脚本。
