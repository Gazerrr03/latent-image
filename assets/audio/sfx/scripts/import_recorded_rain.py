"""将 CC0 雨声实录的公开 HQ 预览制成游戏循环；不增加合成雨滴或共振。

python3 assets/audio/sfx/scripts/import_recorded_rain.py
来源文件、授权和校验值见 recordings/rain/sources.json。
"""

import hashlib
import json
import subprocess
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[4]
SOURCES = ROOT / "assets/audio/sfx/recordings/rain"
OUT = ROOT / "godot/audio/sfx"
RATE = 48000


def run():
    records = json.loads((SOURCES / "sources.json").read_text())
    for sid, entry in records.items():
        source = SOURCES / entry["file"]
        if hashlib.sha256(source.read_bytes()).hexdigest() != entry["sha256"]:
            raise ValueError(f"Source checksum mismatch: {source}")
        raw = subprocess.check_output([
            "ffmpeg", "-v", "error", "-i", str(source), "-af", "highpass=f=60",
            "-ar", str(RATE), "-ac", "2", "-f", "f32le", "-",
        ])
        x = np.frombuffer(raw, dtype="<f4").reshape(-1, 2).copy()
        # 尾部一秒与开头一秒交叠；播放接缝回到第 1 秒处，保留自然雨滴的随机变化。
        n = RATE
        t = np.linspace(0.0, np.pi / 2, n, endpoint=True)[:, None]
        seam = x[-n:] * np.cos(t) + x[:n] * np.sin(t)
        loop = np.concatenate([x[n:-n], seam])
        loop *= 0.1 / max(float(np.sqrt(np.mean(loop ** 2))), 1e-9)
        peak = float(np.max(np.abs(loop)))
        if peak > 0.9:
            loop *= 0.9 / peak
        target = OUT / f"{sid}.ogg"
        temporary = OUT / f"{sid}.recorded.tmp.ogg"
        subprocess.run([
            "ffmpeg", "-y", "-v", "error", "-f", "f32le", "-ar", str(RATE),
            "-ac", "2", "-i", "-", "-c:a", "vorbis", "-strict", "-2", "-b:a", "160k", str(temporary),
        ], input=loop.astype("<f4").tobytes(), check=True)
        subprocess.run(["ffmpeg", "-v", "error", "-i", str(temporary), "-f", "null", "-"], check=True)
        temporary.replace(target)
        print(f"{sid}: {len(loop) / RATE:.2f}s, peak {20 * np.log10(np.max(np.abs(loop))):.1f} dBFS, RMS {20 * np.log10(np.sqrt(np.mean(loop ** 2))):.1f} dBFS")


if __name__ == "__main__":
    run()
