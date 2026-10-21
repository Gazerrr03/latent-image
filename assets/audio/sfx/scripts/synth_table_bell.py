"""合成餐桌铃：一只黄铜台铃的“叮——”。

项目里的其他音效用 synth_sfx.py 配方生成；这台机器没有 ffmpeg，所以这个脚本
直接写 16-bit 立体声 WAV，Godot 4 可以直接导入（sound.csv 里写 .wav）。

设计思路：台铃不是教堂钟，也不是手摇铃。它由三部分组成：
  1. 8 ms 的金属触点噪声（锤子打上去的那一下）；
  2. 一组非谐波模态：基频 + 2.4x / 4.2x / 6.8x，越高衰减越快；
  3. 很短的木质/黄铜底座低频，给“台”一点重量。
再加小餐厅的早期反射和 2.2 s 混响。默认生成三个候选：
  - table_bell.wav        银铃，紧凑起音 + 5.8 s 长尾；正片用；
  - table_bell_brass.wav  黄铜台铃，明亮、干净；备选；
  - table_bell_old.wav    旧铜铃，更低、更闷，带一点年代感。

用法：
  python3 assets/audio/sfx/scripts/synth_table_bell.py
  python3 assets/audio/sfx/scripts/synth_table_bell.py --variant all
"""

from __future__ import annotations

import argparse
import math
import wave
from pathlib import Path

import numpy as np

SR = 44100
REPO = Path(__file__).resolve().parents[4]
OUT = REPO / "godot/audio/sfx"
PREVIEW = REPO / "assets/audio/sfx/preview"


def t_axis(duration: float) -> np.ndarray:
    return np.arange(int(duration * SR), dtype=np.float64) / SR


def exp_env(t: np.ndarray, tau: float) -> np.ndarray:
    return np.exp(-np.maximum(t, 0.0) / max(tau, 1e-5))


def modal(
    duration: float,
    base: float,
    ratios: tuple[float, ...],
    amps: tuple[float, ...],
    taus: tuple[float, ...],
    *,
    detune: float = 0.0,
    pitch_drop: float = 0.0,
    drop_tau: float = 0.028,
    phase_seed: int = 0,
) -> np.ndarray:
    """一组带轻微失谐和起音下滑的钟体模态。"""
    t = t_axis(duration)
    out = np.zeros_like(t)
    rng = np.random.default_rng(phase_seed)
    for i, (ratio, amp, tau) in enumerate(zip(ratios, amps, taus)):
        f = base * ratio
        if f >= SR * 0.48:
            continue
        # 起音瞬间频率略高，20~30 ms 内落到额定音高：金属被敲击后的“紧”
        phase = 2.0 * math.pi * f * (t + pitch_drop * drop_tau * (1.0 - np.exp(-t / drop_tau)))
        # 两条极近的模态，产生缓慢拍频，听起来像真的钟体在晃
        det = f * detune
        p1 = np.cos(phase)
        p2 = np.sin(2 * math.pi * det * t + rng.uniform(0, 2 * math.pi)) * 0.10
        out += amp * (p1 + p2) * exp_env(t, tau)
    return out


def strike(duration: float, seed: int, strength: float = 1.0) -> np.ndarray:
    """锤头触点：极短的高频噪声 + 一点低频底座。"""
    t = t_axis(duration)
    rng = np.random.default_rng(seed)
    n = len(t)
    noise = rng.normal(0.0, 1.0, n)
    # 一阶差分当高通，去掉低频轰隆，只留“嗒”的金属接触
    hp = np.diff(noise, prepend=0.0)
    contact = hp * exp_env(t, 0.0022) * 0.55
    body = (
        0.30 * np.sin(2 * math.pi * 318.0 * t) * exp_env(t, 0.055)
        + 0.16 * np.sin(2 * math.pi * 742.0 * t) * exp_env(t, 0.032)
        + 0.08 * np.sin(2 * math.pi * 1290.0 * t) * exp_env(t, 0.020)
    )
    # 第二次轻触：锤子回弹，约 7 ms 后
    t2 = np.maximum(t - 0.007, 0.0)
    bounce = (
        0.22 * np.sin(2 * math.pi * 2450.0 * t2) * exp_env(t2, 0.0045)
        + 0.12 * np.sin(2 * math.pi * 3870.0 * t2) * exp_env(t2, 0.0028)
    )
    return (contact + body + bounce) * strength


def pan(x: np.ndarray, p: float) -> tuple[np.ndarray, np.ndarray]:
    """等功率声像；p=-1 左，+1 右。"""
    a = (p + 1.0) * math.pi * 0.25
    return x * math.cos(a), x * math.sin(a)


def early_reflections(x: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
    """小餐厅的 4 条早期反射，左右交错，给铃一个空间。"""
    left = x.copy()
    right = x.copy()
    taps = ((0.011, 0.30, -0.65), (0.019, 0.22, 0.55), (0.031, 0.15, -0.35), (0.047, 0.10, 0.30))
    for delay, gain, p in taps:
        d = int(delay * SR)
        if d >= len(x):
            continue
        shifted = np.zeros_like(x)
        shifted[d:] = x[:-d]
        l, r = pan(shifted * gain, p)
        left += l
        right += r
    return left, right


def reverb(x: np.ndarray, duration: float = 1.35, decay: float = 0.38, wet: float = 0.20) -> np.ndarray:
    """用指数衰减噪声当 IR，FFT 卷积；比反馈延迟自然，也不会拖得太长。"""
    rng = np.random.default_rng(7)
    n = int(duration * SR)
    t = np.arange(n) / SR
    ir = rng.normal(0.0, 1.0, n) * np.exp(-t / decay)
    # 简易低通：频域乘一个平滑衰减，去掉刺耳的高频尾
    spec = np.fft.rfft(ir)
    freqs = np.fft.rfftfreq(n, 1.0 / SR)
    spec *= np.exp(-freqs / 4200.0)
    ir = np.fft.irfft(spec, n=n)
    ir /= np.max(np.abs(ir)) + 1e-9
    ir *= np.exp(-t / decay)
    # 补零后循环卷积
    m = len(x) + n - 1
    size = 1 << (m - 1).bit_length()
    y = np.fft.irfft(np.fft.rfft(x, size) * np.fft.rfft(ir, size), size)[: len(x)]
    # 湿声按 RMS 对齐干声：不然长 IR 的卷积增益会把起音压没，只剩一片混响
    y *= np.sqrt(np.mean(x ** 2)) / (np.sqrt(np.mean(y ** 2)) + 1e-9)
    return x + wet * y


def highpass(x: np.ndarray, cutoff: float = 150.0) -> np.ndarray:
    """零相位高通，去掉包络/混响带来的 2~3 Hz 隆隆声；台铃不需要 150 Hz 以下。"""
    n = len(x)
    spec = np.fft.rfft(x)
    freqs = np.fft.rfftfreq(n, 1.0 / SR)
    h = 1.0 / (1.0 + (cutoff / np.maximum(freqs, 1e-6)) ** 4)
    return np.fft.irfft(spec * h, n=n)


def make_bell(variant: dict) -> np.ndarray:
    duration = variant["duration"]
    t = t_axis(duration)
    # 主模态 + 第二组轻微错开的模态，让尾音有“晃”的感觉
    body = modal(
        duration,
        variant["base"],
        variant["ratios"],
        variant["amps"],
        variant["taus"],
        detune=variant["detune"],
        pitch_drop=variant["pitch_drop"],
        phase_seed=variant["seed"],
    )
    shimmer = modal(
        duration,
        variant["base"] * 1.0012,
        variant["ratios"],
        [a * variant.get("shimmer", 0.18) for a in variant["amps"]],
        [tau * 0.88 for tau in variant["taus"]],
        detune=variant["detune"] * 1.7,
        pitch_drop=variant["pitch_drop"] * 0.6,
        phase_seed=variant["seed"] + 11,
    )
    x = body + shimmer + strike(duration, variant["seed"] + 3, variant["strike"])
    # 收尾淡出，避免 WAV 末尾的直流/爆音
    fade = np.clip((duration - t) / 0.25, 0.0, 1.0)
    x *= fade
    x = np.tanh(x * variant["drive"]) / np.tanh(variant["drive"])
    x *= exp_env(t, variant["tail"])
    left, right = early_reflections(x)
    room = float(variant.get("room", 1.35))
    left = reverb(left, duration=room, wet=variant["wet"])
    right = reverb(np.roll(x, 17), duration=room, wet=variant["wet"])
    # 立体声轻微不同，避免单声道叠加太干
    left = highpass(left - np.mean(left), 150.0)
    right = highpass(right - np.mean(right), 150.0)
    stereo = np.stack([left, right], axis=1)
    stereo = stereo / (np.max(np.abs(stereo)) + 1e-9) * 0.72
    return stereo


def write_wav(path: Path, stereo: np.ndarray) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    pcm = np.clip(stereo, -1.0, 1.0)
    pcm = (pcm * 32767.0).astype(np.int16)
    with wave.open(str(path), "wb") as w:
        w.setnchannels(2)
        w.setsampwidth(2)
        w.setframerate(SR)
        w.writeframes(pcm.tobytes())


VARIANTS = {
    "table_bell": {
        "duration": 5.80,
        "base": 3136.0,
        "ratios": (1.0, 2.52, 4.65, 7.10),
        "amps": (0.72, 0.38, 0.16, 0.06),
        "taus": (4.20, 2.20, 1.10, 0.50),
        "detune": 0.0004,
        "pitch_drop": 0.008,
        "strike": 0.82,
        "drive": 1.15,
        "tail": 3.80,
        "wet": 0.16,
        "room": 2.20,
        "shimmer": 0.13,
        "seed": 1914,
        "desc": "银铃，紧凑起音 + 5.8 s 长尾；正片",
    },
    "table_bell_brass": {
        "duration": 2.65,
        "base": 2349.0,
        "ratios": (1.0, 2.40, 4.23, 6.81),
        "amps": (0.78, 0.42, 0.19, 0.08),
        "taus": (1.55, 0.78, 0.38, 0.18),
        "detune": 0.0005,
        "pitch_drop": 0.012,
        "strike": 0.95,
        "drive": 1.25,
        "tail": 1.35,
        "wet": 0.20,
        "seed": 1924,
        "desc": "黄铜台铃，明亮干净；备选",
    },
    "table_bell_old": {
        "duration": 2.35,
        "base": 1568.0,
        "ratios": (1.0, 2.18, 3.72, 5.90),
        "amps": (0.82, 0.50, 0.22, 0.10),
        "taus": (1.25, 0.62, 0.30, 0.14),
        "detune": 0.0018,
        "pitch_drop": 0.016,
        "strike": 1.05,
        "drive": 1.35,
        "tail": 1.15,
        "wet": 0.14,
        "seed": 1901,
        "desc": "旧铜铃，更低更闷；备选",
    },
}


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--variant", default="table_bell", choices=sorted(VARIANTS) + ["all"])
    args = ap.parse_args()

    PREVIEW.mkdir(parents=True, exist_ok=True)
    names = sorted(VARIANTS) if args.variant == "all" else [args.variant]
    for name in names:
        v = VARIANTS[name]
        audio = make_bell(v)
        if name == "table_bell":
            path = OUT / "table_bell.wav"
        else:
            path = PREVIEW / f"{name}.wav"
        write_wav(path, audio)
        peak = float(np.max(np.abs(audio)))
        rms = float(np.sqrt(np.mean(audio**2)))
        print(f"{name}: {path}  {v['desc']}  peak={peak:.3f} rms={rms:.4f}  {v['duration']:.2f}s")


if __name__ == "__main__":
    main()
