"""合成倒茶声：细流 + 杯底回响，给 ded_table 记忆演出的特写。

没有 ffmpeg，直接写 16-bit 立体声 WAV；Godot 4 直接导入。
"""

from pathlib import Path
import wave

import numpy as np

SR = 44100
REPO = Path(__file__).resolve().parents[4]
OUT = REPO / "godot/audio/sfx/tea_pour.wav"


def envelope(t: np.ndarray, duration: float) -> np.ndarray:
    attack = np.clip(t / 0.12, 0.0, 1.0)
    release = np.clip((duration - t) / 0.35, 0.0, 1.0)
    body = 0.75 + 0.25 * np.sin(2 * np.pi * 1.7 * t) ** 2
    return attack * release * body


def main() -> None:
    duration = 2.35
    t = np.arange(int(duration * SR)) / SR
    rng = np.random.default_rng(1924)
    n = len(t)

    # 细流：带通噪声（250–4200 Hz），像水柱落在杯底
    noise = rng.normal(0, 1, n)
    spec = np.fft.rfft(noise)
    freqs = np.fft.rfftfreq(n, 1 / SR)
    band = np.exp(-((freqs - 1400) / 1200) ** 4)
    band *= np.clip((freqs - 220) / 500, 0, 1)
    stream = np.fft.irfft(spec * band, n=n)
    stream /= np.max(np.abs(stream)) + 1e-9

    # 杯底的低频回响 + 不规则的“咕”
    low = np.fft.irfft(np.fft.rfft(rng.normal(0, 1, n)) * np.exp(-((freqs - 280) / 260) ** 4), n=n)
    low /= np.max(np.abs(low)) + 1e-9
    gurgle = np.zeros(n)
    for _ in range(9):
        at = rng.uniform(0.15, duration - 0.25)
        f = rng.uniform(420, 900)
        i = int(at * SR)
        ln = int(rng.uniform(0.035, 0.09) * SR)
        tt = np.arange(ln) / SR
        gurgle[i:i + ln] += np.sin(2 * np.pi * f * tt) * np.exp(-tt / 0.025) * rng.uniform(0.12, 0.3)

    x = 0.8 * stream + 0.35 * low + gurgle
    x *= envelope(t, duration)
    # 小房间湿声：4 条早期反射
    left = x.copy()
    right = x.copy()
    for delay, gain, pan in ((0.013, 0.35, -0.6), (0.021, 0.25, 0.5), (0.037, 0.16, -0.2)):
        d = int(delay * SR)
        shifted = np.zeros(n)
        shifted[d:] = x[:-d]
        left += shifted * gain * (1 - pan) * 0.5
        right += shifted * gain * (1 + pan) * 0.5
    stereo = np.stack([left, right], axis=1)
    # 温和低通，去掉刺耳的高频
    for ch in range(2):
        s = np.fft.rfft(stereo[:, ch])
        s *= np.exp(-freqs / 5200.0)
        stereo[:, ch] = np.fft.irfft(s, n=n)
    stereo -= stereo.mean(axis=0, keepdims=True)
    stereo = stereo / (np.max(np.abs(stereo)) + 1e-9) * 0.62
    pcm = np.clip(stereo, -1, 1)
    pcm = (pcm * 32767).astype(np.int16)
    OUT.parent.mkdir(parents=True, exist_ok=True)
    with wave.open(str(OUT), "wb") as w:
        w.setnchannels(2)
        w.setsampwidth(2)
        w.setframerate(SR)
        w.writeframes(pcm.tobytes())
    print("tea_pour:", OUT, "dur", duration, "peak", float(np.max(np.abs(stereo))))


if __name__ == "__main__":
    main()
