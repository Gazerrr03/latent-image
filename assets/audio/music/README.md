# 配乐

风格与分段见《04-美术与声音风格》第 14 节。

## 流程

1. **agent 写谱**：`scripts/compose_<曲名>.py` 用代码写出多轨 MIDI（每件乐器一条轨），存到 `midi/`。
2. **原型渲染**：加 `--render`，乐队用 FluidSynth + GeneralUser GS 音色库渲染，标了 `synth` 的轨由脚本里的小合成器直接算波形，混成无缝循环，存到 `preview/`：
   - `<曲名>.ogg`：游戏可用的循环（Godot 里勾 loop 即可）
   - `<曲名>.wav`：同一段的无损版（不进 git）
   - `<曲名>_x2.wav`：连放两遍，专门听接缝（不进 git）
3. **用户在库乐队里细化**：把 `midi/<曲名>.mid` 拖进库乐队，会按乐器自动分轨，速度一起带进去。在每条轨上换成库乐队的音色，推荐：
   - 低音提琴 → 贝斯 › Upright Studio Bass（原声贝斯）
   - 套鼓 → 选干净的爵士套鼓（Jazz Kit），不要用 Brushes（用户 10-17：鼓刷的“沙子”声不对味）
   - 钢琴 → Steinway Grand Piano
   - 合成器旋律 → 温暖的模拟合成器：Retro Synth › 锯齿波，两个振荡器略微走调，滤波器关到 1 kHz 左右，起音慢一点、释放长一点
   - 特雷门琴 → Alchemy 里搜 Theremin，或 Retro Synth 正弦波 + 滑音（Glide）+ 颤音。这条轨不跟乐队摇摆，不要对它开量化摇摆
   - 不要用八音盒、颤音琴、钢片琴一类“敲铃”的音色（用户 10-17：太像儿童游戏）
4. **定稿导出**：库乐队「共享 › 导出歌曲到磁盘」，选 WAV，范围正好 16 小节（从第 1 小节开头到第 17 小节开头），不要带混响尾巴，否则循环会多出一截空白。导出后交给 agent 转成 `.ogg`，替换 `godot/audio/music/` 里的同名文件。

本机依赖：`brew install fluid-synth`；音色库在 `~/.local/share/soundfonts/GeneralUser-GS.sf2`（来自 github.com/mrbumpy409/GeneralUser-GS，可免费用于商业作品）。

## 曲目

| 曲名 | 文件 | 用途 | 状态 |
| --- | --- | --- | --- |
| 《潜影》Latent Image | 脚本 `scripts/compose_latent_image.py`，MIDI `midi/latent_image.mid`，循环 `preview/latent_image.ogg` | 探索曲：白天走访与调查（配乐表 `explore`） | **定稿，已接入游戏**（`godot/audio/music/latent_image.ogg`） |
| 推理 think | `scripts/compose_cues.py think` | 证据板连线时循环（配乐表 `think`） | 已接入 |
| 显影 develop | `scripts/compose_cues.py develop` | 第 6 章亲手冲洗底片，只放一遍 | 已接入 |
| 尾声 ending | `scripts/compose_cues.py ending` | 尾声十二块屏幕，只放一遍 | 已接入 |

**《潜影》**：曲名取自摄影术语——底片已经曝光、影像已经在上面，只是还没显影，看不见。C 大调，84 BPM 摇摆，16 小节一个循环（45.7 秒），Cmaj7–Am7–Dm7–G7，中段转 Em7–A7。低音提琴二分音符、叮叮镲、钢琴查尔斯顿节奏垫底；模拟合成器唱旋律；低音区的特雷门琴两小节一轮，反复同一个音型 E B G B E B F♯ B。怪异细节见脚本开头的 a—f。在库乐队里改动时，别把这些“错”修掉。

**推理、显影、尾声**与《潜影》同一套乐器和母题（`compose_cues.py` 复用《潜影》脚本里的合成器与渲染）：推理只有低音提琴和特雷门琴，66 BPM；显影去掉鼓，《潜影》的旋律第一次被慢慢、清楚地奏出来，最后停在升 F 上；尾声乐队全部消失，只剩合成器。

试听过、已删除的草稿（10-17）：v1—v2 紧绷的小调悬疑爵士（被否：太紧张，鼓刷有“沙子”声）；v3 大调日常爵士 + 钢片琴八音盒（方向对，八音盒音色被否）；v4 合成器音型（选了特雷门琴）；v5 放慢到 84 BPM、音型拉宽到两小节。
