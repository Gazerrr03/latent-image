"""音效合成用的小工具箱：噪声、滤波、模态共振、摩擦、人声共振峰、混响、循环拼接。

全部是离线计算（numpy 的 FFT），不追求实时，只追求能复现。
"""

import numpy as np

SR = 44100


def secs(d):
    return np.arange(int(d * SR)) / SR


def rng(seed):
    return np.random.default_rng(seed)


# ---------- 噪声 ----------
def white(n, seed=0):
    return rng(seed).standard_normal(n)


def colored(n, power, seed=0):
    """power=1 粉红噪声，power=2 褐噪声。"""
    x = np.fft.rfft(white(n, seed))
    f = np.fft.rfftfreq(n, 1 / SR)
    f[0] = f[1]
    y = np.fft.irfft(x / f ** (power / 2), n)
    return y / (np.abs(y).max() + 1e-12)


# ---------- 滤波（频域掩膜） ----------
def _apply(x, H):
    n = len(x)
    return np.fft.irfft(np.fft.rfft(x) * H, n)


def _f(n):
    f = np.fft.rfftfreq(n, 1 / SR)
    f[0] = 1e-3
    return f


def lowpass(x, fc, order=2):
    f = _f(len(x))
    return _apply(x, 1 / np.sqrt(1 + (f / fc) ** (2 * order)))


def highpass(x, fc, order=2):
    f = _f(len(x))
    return _apply(x, 1 / np.sqrt(1 + (fc / f) ** (2 * order)))


def bandpass(x, lo, hi, order=2):
    return highpass(lowpass(x, hi, order), lo, order)


def resonant(x, peaks):
    """peaks：[(中心频率, Q, 增益)]，并联的共振峰。"""
    f = _f(len(x))
    H = np.zeros_like(f)
    for c, q, g in peaks:
        H += g / np.sqrt(1 + q * q * (f / c - c / f) ** 2)
    return _apply(x, H)


# ---------- 包络 ----------
def env_exp(n, tau, attack=0.002):
    t = np.arange(n) / SR
    return np.minimum(t / max(attack, 1e-5), 1) * np.exp(-t / tau)


def env_shape(n, points):
    """points：[(秒, 值)]，线性插值。"""
    t = np.arange(n) / SR
    ts, vs = zip(*points)
    return np.interp(t, ts, vs)


def smooth_noise(n, rate, seed=0):
    """每秒约 rate 个随机点的平滑起伏，范围约 -1..1。"""
    k = max(int(n / SR * rate) + 2, 2)
    pts = rng(seed).uniform(-1, 1, k)
    return np.interp(np.linspace(0, k - 1, n), np.arange(k), pts)


# ---------- 合成积木 ----------
def modal(dur, modes, seed=0, detune=0.0):
    """modes：[(频率, 衰减秒, 振幅)]。敲击类声音（玻璃、金属、木头）的核心。"""
    t = secs(dur)
    r = rng(seed)
    out = np.zeros_like(t)
    for f, tau, a in modes:
        f2 = f * (1 + r.uniform(-detune, detune))
        out += a * np.sin(2 * np.pi * f2 * t + r.uniform(0, 6.28)) * np.exp(-t / tau)
    return out


def click(dur=0.004, lo=1500, hi=9000, seed=0):
    n = int(dur * SR)
    return bandpass(white(n + 256, seed), lo, hi)[:n] * env_exp(n, dur / 3, 0.0003)


def impact(dur, modes, noise_amt=0.5, noise_tau=0.006, noise_lo=200, noise_hi=8000, seed=0, detune=0.01):
    x = modal(dur, modes, seed, detune)
    n = len(x)
    burst = bandpass(white(n, seed + 1), noise_lo, noise_hi) * env_exp(n, noise_tau, 0.0005)
    return x + noise_amt * burst / (np.abs(burst).max() + 1e-9)


def friction(dur, rate, resonances, seed=0, jitter=0.25, noise=0.15):
    """摩擦吱呀：粘—滑脉冲串经过共振体。rate：每秒脉冲数，可为数组（随时间变）。"""
    n = int(dur * SR)
    r = rng(seed)
    rate = np.broadcast_to(np.asarray(rate, float), (n,)).copy()
    rate *= 1 + jitter * smooth_noise(n, 30, seed)
    phase = np.cumsum(rate) / SR
    idx = np.nonzero(np.diff(np.floor(phase)) > 0)[0]
    src = np.zeros(n)
    src[idx] = r.uniform(0.5, 1.0, len(idx))
    src += noise * white(n, seed + 3) * 0.05
    return resonant(src, resonances)


def ks_string(dur, f0, decay=0.996, seed=0, bend=None):
    """Karplus-Strong 拨弦。bend：结束时相对音高（如 0.9）。"""
    n = int(dur * SR)
    out = np.zeros(n)
    period = SR / f0
    buf = rng(seed).uniform(-1, 1, int(period) + 2)
    pos = 0.0
    p = period
    for i in range(n):
        if bend is not None:
            p = period / (1 + (bend - 1) * i / n)
        L = len(buf)
        j = int(pos) % L
        k = (j + 1) % L
        out[i] = buf[j]
        buf[j] = decay * 0.5 * (buf[j] + buf[k])
        pos += L / p
    return out


def grains(dur, rate, maker, seed=0, amp_env=None, times=None):
    """把很多短声音撒在一段时间里：雨滴、碎玻璃、砂石。maker(i, r) 返回一段短声音。"""
    n = int(dur * SR)
    out = np.zeros(n)
    r = rng(seed)
    if times is None:
        times = np.sort(r.uniform(0, dur, int(rate * dur)))
    for i, t0 in enumerate(times):
        g = maker(i, r)
        a = int(t0 * SR)
        b = min(a + len(g), n)
        amp = amp_env(t0) if amp_env else 1.0
        out[a:b] += amp * g[: b - a]
    return out


# ---------- 人声：声门脉冲 + 共振峰 ----------
VOWELS = {
    "a": [(850, 6, 1.0), (1600, 8, 0.5), (2900, 10, 0.25), (4100, 12, 0.12)],
    "ae": [(1000, 6, 1.0), (1800, 8, 0.6), (3000, 10, 0.3), (4300, 12, 0.15)],
    "m": [(260, 5, 1.0), (1000, 10, 0.08), (2600, 12, 0.03)],
    "h": [(700, 3, 0.6), (1800, 4, 0.5), (3000, 5, 0.4)],
}


def voice(f0, vowel, breath=0.08, rough=0.0, seed=0, tilt=1.3):
    """f0：每个采样点的基频数组。返回一段干声。"""
    n = len(f0)
    r = rng(seed)
    f = f0 * (1 + 0.012 * smooth_noise(n, 40, seed))  # 微抖动
    phase = np.cumsum(f) / SR
    src = np.zeros(n)
    for k in range(1, 40):
        mask = (k * f) < 9000
        if not mask.any():
            break
        src += mask * np.sin(2 * np.pi * k * phase) / k ** tilt
    if rough:
        src *= 1 + rough * np.sin(np.pi * phase + r.uniform(0, 6))  # 半频调制，嘶哑
    src += breath * white(n, seed + 7)
    return resonant(src, VOWELS[vowel])


# ---------- 空间 ----------
def reverb(x, t60=1.2, wet=0.25, seed=11, damp=4000, predelay=0.012):
    n = len(x)
    L = int(t60 * SR)
    ir = white(L, seed) * np.exp(-6.9 * np.arange(L) / L)
    ir = lowpass(ir, damp)
    ir /= np.sqrt((ir ** 2).sum()) + 1e-12
    pd = int(predelay * SR)
    m = n + L + pd
    y = np.fft.irfft(np.fft.rfft(x, m) * np.fft.rfft(np.concatenate([np.zeros(pd), ir]), m), m)
    out = np.zeros(m)
    out[:n] += x
    out += wet * y / (np.abs(y).max() + 1e-12) * (np.abs(x).max() + 1e-12)
    return out


def distant(x, cutoff=2500, t60=1.6, wet=0.5):
    """放远：削高频、多混响。"""
    return reverb(lowpass(x, cutoff), t60, wet)


# ---------- 拼接与输出 ----------
def place(buf, x, at, gain=1.0):
    a = int(at * SR)
    b = min(a + len(x), len(buf))
    if b > a:
        buf[a:b] += gain * x[: b - a]
    return buf


def silence(d):
    return np.zeros(int(d * SR))


def loopify(x, xfade=0.5):
    """把结尾叠回开头，做成无缝循环（等功率交叉淡化）。"""
    k = int(xfade * SR)
    body = x[:-k].copy()
    t = np.linspace(0, np.pi / 2, k)
    body[:k] = body[:k] * np.sin(t) + x[-k:] * np.cos(t)
    return body


def stereo(left, right=None):
    if right is None:
        right = left
    n = min(len(left), len(right))
    return np.stack([left[:n], right[:n]], axis=1)


def trim_tail(x, thresh=1e-4):
    a = np.abs(x if x.ndim == 1 else x.max(axis=1))
    idx = np.nonzero(a > thresh * a.max())[0]
    return x[: idx[-1] + int(0.02 * SR)] if len(idx) else x
