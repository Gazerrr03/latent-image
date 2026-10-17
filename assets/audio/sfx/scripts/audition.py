"""把音效表里的声音按顺序排成一盘试听带，附时间表。

    python3 assets/audio/sfx/scripts/audition.py              # 全部
    python3 assets/audio/sfx/scripts/audition.py id1 id2 ...  # 只排指定的

循环声截取前 6 秒。输出 assets/audio/sfx/preview/试听带.wav 与 试听带.txt（不进 git）。
"""
import csv
import subprocess
import sys
import wave
from pathlib import Path

import numpy as np

REPO = Path(__file__).resolve().parents[4]
OUT = Path(__file__).resolve().parents[1] / "preview"
SR = 44100

rows = list(csv.DictReader(open(REPO / "godot/content/audio/sounds.csv", newline="")))
want = sys.argv[1:]
parts, index, t = [], [], 0.0
for r in rows:
    if not r["file"] or (want and r["id"] not in want):
        continue
    raw = subprocess.run(["ffmpeg", "-loglevel", "error", "-i", str(REPO / "godot/audio" / r["file"]),
                          "-f", "f32le", "-ac", "2", "-ar", str(SR), "-"], capture_output=True).stdout
    a = np.frombuffer(raw, np.float32).reshape(-1, 2)
    if r["loop"] == "是":
        a = a[: 6 * SR].copy()
        a[-int(0.3 * SR):] *= np.linspace(1, 0, int(0.3 * SR))[:, None]
    gain = 10 ** (float(r["volume_db"] or 0) / 20)  # 按表里的音量，听到的就是游戏里的相对响度
    index.append(f"{int(t // 60)}:{t % 60:05.2f}  {r['id']:20s} {r['name']}")
    parts += [a * gain, np.zeros((int(0.9 * SR), 2), np.float32)]
    t += len(a) / SR + 0.9
mix = np.concatenate(parts)
mix *= 0.9 / max(np.abs(mix).max(), 1e-9)
OUT.mkdir(exist_ok=True)
with wave.open(str(OUT / "试听带.wav"), "wb") as w:
    w.setnchannels(2), w.setsampwidth(2), w.setframerate(SR)
    w.writeframes((mix * 32767).astype(np.int16).tobytes())
(OUT / "试听带.txt").write_text("\n".join(index) + "\n")
print(f"{len(index)} 个声音，共 {t / 60:.1f} 分钟 → {OUT}")
