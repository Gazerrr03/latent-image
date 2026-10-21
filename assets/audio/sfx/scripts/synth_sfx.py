"""全部音效的合成配方。读 / 写 godot/content/audio/sounds.csv，文件输出到 godot/audio/sfx/。

    python3 assets/audio/sfx/scripts/synth_sfx.py              # 合成全部
    python3 assets/audio/sfx/scripts/synth_sfx.py glass_break  # 只合成指定的
    python3 assets/audio/sfx/scripts/synth_sfx.py --list       # 列出配方

每个配方登记：编号、描述、分类、是否循环、建议音量。音效表里没有的编号会自动加一行；
已有的行只更新 file 和 note，不动别人填的描述与音量。
默认由代码合成；雨声已按用户 10-19 要求换成实录，recordings/rain/sources.json 中的编号不再覆盖。
"""

import csv
import json
import subprocess
import sys
import wave
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).parent))
from dsp import *  # noqa: E402,F401,F403

REPO = Path(__file__).resolve().parents[4]
TABLE = REPO / "godot/content/audio/sounds.csv"
OUT = REPO / "godot/audio/sfx"
PREVIEW = Path(__file__).resolve().parents[1] / "preview"
NOTE = "脚本合成：assets/audio/sfx/scripts/synth_sfx.py"

RECIPES = {}


def sfx(sid, name, category, loop=False, vol=0):
    def deco(fn):
        RECIPES[sid] = dict(fn=fn, name=name, category=category, loop=loop, vol=vol)
        return fn
    return deco


def midi_hz(m):
    return 440 * 2 ** ((m - 69) / 12)


# 儿歌：一张底片多一个，红灯底下数一数；数到明年少一个，谁也没有见过他。
# 每句七个字，前六个字各半拍、最后一个字一拍，再空半拍；最后一句落在升 F 上（与《潜影》的升 F 呼应）
RHYME = [
    [64, 64, 67, 64, 62, 60, 62],
    [64, 64, 67, 69, 67, 64, 62],
    [64, 67, 69, 71, 69, 67, 64],
    [62, 64, 62, 60, 59, 60, 54],
]


def rhyme_notes(lines, beat=0.42, transpose=0):
    out, t = [], 0.0
    for line in lines:
        for i, m in enumerate(line):
            d = beat * (2 if i == 6 else 1)
            out.append((t, d, m + transpose))
            t += d
        t += beat
    return out, t


# ======================= 序章 =======================

@sfx("projector", "放映机（片头家庭电影）", "器物", loop=True, vol=-8)
def projector():
    d = 2.0
    n = int(d * SR)
    t = secs(d)
    motor = 0.25 * np.sin(2 * np.pi * 120 * t) + 0.12 * np.sin(2 * np.pi * 240 * t)
    motor += 0.15 * bandpass(white(n, 1), 300, 1200)
    clat = grains(d, 0, lambda i, r: impact(0.03, [(1900, 0.006, 1), (3400, 0.004, 0.5)], 0.6, 0.002, seed=i),
                  times=np.arange(36) / 18.0)
    whirr = 0.1 * bandpass(white(n, 2), 2000, 6000) * (1 + 0.5 * np.sin(2 * np.pi * 18 * t))
    x = motor * 0.5 + clat * 0.8 + whirr
    x = np.concatenate([x, x[: int(0.3 * SR)]])  # 多算一点，交叉淡化后正好 2 秒
    x = loopify(x, 0.3)
    return stereo(x, np.roll(x, 300))


@sfx("train_rattle", "火车车轮声", "环境", loop=True, vol=-4)
def train_rattle():
    d = 8.0
    n = int(d * SR)
    t = secs(d)
    rumble = lowpass(colored(n, 2, 3), 380) * (0.8 + 0.2 * np.sin(2 * np.pi * 2.5 * t))
    def clack(i, r):
        return lowpass(impact(0.25, [(140, 0.06, 1), (420, 0.03, 0.6), (960, 0.015, 0.3)], 0.8, 0.008, seed=i), 3000)
    times = []
    for k in range(5):  # 每 1.6 秒一个轨缝，前后两个转向架“哒—哒，哒—哒”
        b = k * 1.6
        times += [b, b + 0.11, b + 0.62, b + 0.73]
    clacks = grains(d, 0, clack, times=times)
    rattle = 0.05 * bandpass(white(n, 5), 2000, 6000) * (0.6 + 0.4 * smooth_noise(n, 3, 5))
    x = rumble * 0.9 + clacks * 0.7 + rattle
    xl = x + 0.15 * lowpass(colored(n, 2, 8), 300)
    return stereo(loopify(xl, 0.5), loopify(x, 0.5))


@sfx("train_whistle", "火车汽笛（远）", "环境", vol=-6)
def train_whistle():
    d = 2.6
    n = int(d * SR)
    e = env_shape(n, [(0, 0), (0.15, 1), (1.9, 0.9), (2.3, 0)])
    bend = env_shape(n, [(0, 0.94), (0.25, 1.0), (2.6, 0.995)])
    x = np.zeros(n)
    for f, a in ((466, 1), (587, 0.7), (698, 0.5)):
        ph = np.cumsum(f * bend) / SR
        x += a * (np.sin(2 * np.pi * ph) + 0.3 * np.sin(4 * np.pi * ph))
        x += a * 0.4 * resonant(white(n, int(f)), [(f, 30, 1)])
    return distant(x * e, 3000, 2.2, 0.6)


@sfx("train_brake", "火车减速进站：刹车尖声与放汽", "环境", vol=-8)
def train_brake():
    d = 3.2
    n = int(d * SR)
    f = env_shape(n, [(0, 3100), (2.2, 2400), (2.4, 2300)]) * (1 + 0.01 * smooth_noise(n, 8, 1))
    squeal = np.sin(2 * np.pi * np.cumsum(f) / SR) * env_shape(n, [(0, 0), (0.3, 0.5), (1.8, 0.4), (2.4, 0)])
    hiss = highpass(white(n, 2), 2500) * env_shape(n, [(0, 0), (2.2, 0), (2.35, 0.6), (3.2, 0)])
    rumble = lowpass(colored(n, 2, 3), 250) * env_shape(n, [(0, 1), (2.4, 0.4), (3.2, 0)])
    return distant(0.35 * squeal + 0.5 * hiss + rumble, 6000, 1.4, 0.35)


@sfx("footstep_gravel", "脚步（碎石路）", "人声", vol=-6)
def footstep_gravel():
    def g(i, r):
        return click(0.003, 800, 6000, seed=i) * r.uniform(0.2, 1)
    x = grains(0.22, 260, g, seed=1, amp_env=lambda t: np.exp(-t / 0.06))
    place(x, lowpass(impact(0.15, [(110, 0.03, 1)], 0.2, seed=3), 400), 0, 0.4)
    return x


@sfx("iron_gate", "铁门吱呀", "器物", vol=-4)
def iron_gate():
    d = 2.4
    n = int(d * SR)
    rate = env_shape(n, [(0, 30), (0.6, 90), (1.4, 60), (1.9, 120)])
    cr = friction(d, rate, [(520, 14, 1), (1250, 18, 0.7), (2750, 22, 0.4)], seed=4)
    cr *= env_shape(n, [(0, 0), (0.1, 1), (1.9, 1), (2.0, 0)])
    clank = impact(1.5, [(180, 0.4, 1), (530, 0.3, 0.6), (1380, 0.15, 0.4), (2950, 0.08, 0.2)], 0.6, seed=5)
    x = place(np.concatenate([cr, silence(1.0)]), clank, 2.0, 1.2)
    return distant(x, 5000, 1.8, 0.3)


@sfx("thunder_far", "远处雷声", "环境", vol=-4)
def thunder_far():
    d = 7.0
    n = int(d * SR)
    t = secs(d)
    env = np.zeros(n)
    for c, w, a in ((0.4, 0.25, 0.6), (1.1, 0.6, 1.0), (2.2, 0.8, 0.8), (3.4, 1.0, 0.5), (4.8, 1.2, 0.3)):
        env += a * np.exp(-((t - c) / w) ** 2)
    x = lowpass(colored(n, 2, 6), 220) * env + 0.3 * lowpass(colored(n, 1, 7), 600) * env ** 2
    return stereo(x, np.roll(x, 900))


@sfx("rain_night", "夜雨（室外与窗外）", "环境", loop=True, vol=-6)
def rain_night():
    d = 12.0
    n = int(d * SR)
    def ch(seed):
        bed = bandpass(colored(n, 1, seed), 250, 5000) * 0.5
        drops = grains(d, 160, lambda i, r: click(0.004, r.uniform(800, 2500), r.uniform(3000, 7000), seed=seed * 1000 + i) * r.uniform(0.1, 0.6), seed=seed)
        def drip(i, r):
            dd = 0.08
            f = np.linspace(r.uniform(900, 1400), r.uniform(500, 700), int(dd * SR))
            return np.sin(2 * np.pi * np.cumsum(f) / SR) * env_exp(len(f), 0.02)
        drips = grains(d, 1.2, drip, seed=seed + 50) * 0.3
        return loopify(bed + drops + drips, 0.6)
    return stereo(ch(21), ch(22))


@sfx("door_front", "推开庄园的前门：门锁、沉重的吱呀", "器物", vol=-4)
def door_front():
    latch = impact(0.2, [(1600, 0.03, 1), (3300, 0.02, 0.5)], 0.6, seed=2)
    d = 1.6
    n = int(d * SR)
    cr = friction(d, env_shape(n, [(0, 18), (0.8, 40), (1.6, 25)]), [(220, 10, 1), (560, 12, 0.6), (1300, 14, 0.3)], seed=6)
    cr *= env_shape(n, [(0, 0), (0.2, 1), (1.4, 0.8), (1.6, 0)])
    air = lowpass(white(n, 7), 500) * env_shape(n, [(0, 0), (0.5, 0.4), (1.6, 0)])
    x = place(silence(2.2), latch, 0.0)
    place(x, cr * 0.8 + air * 0.3, 0.25)
    return reverb(x, 1.5, 0.3)


@sfx("clock_chime", "座钟报时（一声）", "环境", vol=-6)
def clock_chime():
    f = 196.0
    modes = [(f * 0.5, 4.0, 0.5), (f, 3.5, 1.0), (f * 1.2, 2.5, 0.6), (f * 1.5, 2.0, 0.5),
             (f * 2.0, 1.8, 0.6), (f * 2.5, 1.2, 0.3), (f * 3.0, 0.9, 0.25), (f * 4.2, 0.6, 0.15)]
    x = impact(4.5, modes, 0.3, 0.003, 300, 5000, seed=3, detune=0.004)
    return reverb(x, 2.0, 0.25)


@sfx("clock_tick", "座钟走时声（其实停着，只在画面外响）", "环境", loop=True, vol=-14)
def clock_tick():
    x = silence(2.0)
    place(x, impact(0.12, [(2800, 0.008, 1), (4100, 0.006, 0.6), (900, 0.012, 0.4)], 0.5, 0.002, seed=1), 0.0)
    place(x, impact(0.12, [(2300, 0.009, 1), (3350, 0.007, 0.6), (760, 0.014, 0.4)], 0.5, 0.002, seed=2), 1.0, 0.85)
    return x


@sfx("bolt_slide", "插上门闩（金属滑动，咔）", "器物", vol=-4)
def bolt_slide():
    d = 0.3
    n = int(d * SR)
    slide = bandpass(white(n, 3), 1800, 6000) * env_shape(n, [(0, 0), (0.03, 0.6), (0.25, 0.8), (0.3, 0)])
    slide *= 1 + 0.6 * smooth_noise(n, 60, 3)
    clack = impact(0.4, [(1450, 0.05, 1), (3200, 0.03, 0.6), (5100, 0.02, 0.3)], 0.8, seed=4)
    x = place(silence(0.8), slide * 0.4, 0)
    place(x, clack, 0.28)
    return reverb(x, 0.9, 0.2)


@sfx("child_steps", "小女孩跑上楼梯的碎步，渐远", "人声", vol=-6)
def child_steps():
    x = silence(2.0)
    for k in range(9):
        st = impact(0.15, [(160 + 8 * k, 0.025, 1), (620, 0.012, 0.4)], 0.4, 0.003, seed=k)
        st = lowpass(st, 4000 - 300 * k)
        place(x, st, 0.12 + k * 0.17, 0.9 * 0.86 ** k)
    return reverb(x, 1.2, 0.35)


@sfx("luggage", "放下行李箱", "器物", vol=-6)
def luggage():
    x = silence(1.0)
    place(x, lowpass(impact(0.4, [(95, 0.08, 1), (240, 0.05, 0.5)], 0.5, 0.01, seed=1), 2000), 0.0)
    for k in range(3):
        place(x, impact(0.08, [(2400 + 300 * k, 0.015, 1)], 0.5, seed=10 + k), 0.06 + 0.05 * k, 0.25)
    return reverb(x, 0.8, 0.2)


@sfx("glass_break", "玻璃碎响（走廊那头，一只量杯摔碎）", "器物", vol=-2)
def glass_break():
    d = 2.0
    hit = impact(0.6, [(2200, 0.04, 1), (3900, 0.03, 0.8), (6100, 0.02, 0.6)], 1.2, 0.004, 1500, 12000, seed=1)
    def shard(i, r):
        return modal(0.15, [(r.uniform(2500, 9000), r.uniform(0.01, 0.06), 1),
                            (r.uniform(4000, 11000), r.uniform(0.008, 0.04), 0.5)], seed=i)
    shards = grains(d, 0, shard, times=np.sort(np.random.default_rng(3).exponential(0.25, 70)),
                    amp_env=lambda t: 0.5 * np.exp(-t / 0.5))
    x = place(silence(d), hit, 0)
    x += shards[: len(x)]
    return distant(x, 7000, 1.4, 0.35)  # 走廊那头，隔着一段距离


@sfx("body_thud", "人倒在地板上的闷响", "人声", vol=-4)
def body_thud():
    x = silence(1.2)
    place(x, lowpass(impact(0.5, [(62, 0.12, 1), (130, 0.07, 0.6), (300, 0.03, 0.3)], 0.4, 0.01, seed=1), 900), 0)
    place(x, lowpass(impact(0.3, [(140, 0.05, 1), (420, 0.02, 0.4)], 0.4, seed=2), 1500), 0.17, 0.5)
    return distant(x, 1800, 1.0, 0.3)


@sfx("door_knock", "敲门：三下，停一停，再三下", "器物", vol=-4)
def door_knock():
    x = silence(2.6)
    k = 0
    for t0, a in ((0, 0.7), (0.24, 0.7), (0.48, 0.75), (1.3, 1.0), (1.52, 1.0), (1.74, 1.0)):
        kn = impact(0.25, [(210, 0.05, 1), (470, 0.03, 0.6), (1150, 0.012, 0.3)], 0.5, 0.002, seed=k)
        place(x, kn, t0, a)
        k += 1
    return reverb(x, 1.0, 0.25)


@sfx("door_bang", "撞门声", "器物", vol=-2)
def door_bang():
    x = silence(2.0)
    thud = impact(0.8, [(70, 0.15, 1), (145, 0.1, 0.7), (330, 0.05, 0.4)], 1.0, 0.02, 100, 3000, seed=1)
    splinter = grains(0.4, 120, lambda i, r: click(0.005, 600, 5000, seed=i) * r.uniform(0.2, 1), seed=2,
                      amp_env=lambda t: np.exp(-t / 0.12))
    bolt = modal(0.8, [(2250, 0.3, 1), (3600, 0.2, 0.5)], seed=3)
    place(x, thud, 0)
    place(x, splinter, 0.01, 0.6)
    place(x, bolt, 0.02, 0.25)
    place(x, impact(0.5, [(110, 0.08, 1), (260, 0.05, 0.5)], 0.5, seed=4), 0.38, 0.5)  # 门撞到墙
    return reverb(x, 1.1, 0.3)


@sfx("scream_constance", "女主人一声短促的惊叫，很快被捂住", "人声", vol=-4)
def scream_constance():
    d = 1.15
    n = int(d * SR)
    f0 = env_shape(n, [(0, 520), (0.12, 930), (0.55, 880), (0.75, 820), (1.15, 600)])
    f0 *= 1 + 0.03 * np.sin(2 * np.pi * 7 * secs(d))
    v = voice(f0, "ae", breath=0.12, rough=0.25, seed=1)
    muffled = lowpass(v, 600)
    mix = env_shape(n, [(0, 0), (0.68, 0), (0.78, 1), (1.15, 1)])  # 0.7 秒时被手捂住
    x = (1 - mix) * v + mix * muffled * 0.6
    x *= env_shape(n, [(0, 0), (0.04, 1), (0.7, 0.9), (0.8, 0.35), (1.0, 0.15), (1.15, 0)])
    return reverb(lowpass(x, 6000), 1.3, 0.35)


@sfx("typewriter", "打字机声", "器物", vol=-6)
def typewriter():
    d = 3.2
    r = np.random.default_rng(5)
    times = np.cumsum(r.uniform(0.09, 0.22, 20))
    times = times[times < 3.0]
    def key(i, r):
        return impact(0.12, [(1800 + r.uniform(-150, 150), 0.02, 1), (3200, 0.015, 0.6), (4700, 0.01, 0.3),
                             (180, 0.02, 0.5)], 0.9, 0.002, seed=i)
    return reverb(grains(d, 0, key, times=times), 0.6, 0.15)


@sfx("typewriter_return", "打字机回车（叮一声，滑回去）", "器物", vol=-6)
def typewriter_return():
    x = silence(1.6)
    place(x, modal(1.2, [(2620, 0.5, 1), (3480, 0.3, 0.4), (5200, 0.15, 0.2)], seed=1), 0, 0.5)
    for k, t0 in enumerate(np.cumsum(np.linspace(0.06, 0.02, 14)) + 0.15):
        place(x, click(0.006, 2000, 7000, seed=k), t0, 0.5)
    slide = bandpass(white(int(0.4 * SR), 3), 400, 3000) * env_shape(int(0.4 * SR), [(0, 0), (0.05, 0.4), (0.4, 0.2)])
    place(x, slide, 0.15)
    place(x, impact(0.2, [(320, 0.04, 1), (1100, 0.02, 0.5)], 0.6, seed=9), 0.6)
    return reverb(x, 0.6, 0.15)


# ======================= 第 1—2 章 =======================

@sfx("rain_glass", "雨打温室玻璃", "环境", loop=True, vol=-6)
def rain_glass():
    d = 12.0
    n = int(d * SR)
    def ch(seed):
        bed = bandpass(colored(n, 1, seed), 400, 6000) * 0.35
        drops = grains(d, 120, lambda i, r: click(0.003, 2000, 9000, seed=seed * 1000 + i) * r.uniform(0.1, 0.5), seed=seed)
        tinks = grains(d, 5, lambda i, r: modal(0.08, [(r.uniform(4000, 7000), 0.025, 1)], seed=seed * 7 + i) * 0.25, seed=seed + 9)
        return loopify(bed + drops + tinks, 0.6)
    return stereo(ch(31), ch(32))


@sfx("light_switch", "旋钮电灯开关“咔哒”，灯丝轻轻嗡起来", "器物", vol=-8)
def light_switch():
    x = silence(0.8)
    place(x, impact(0.12, [(2100, 0.015, 1), (4300, 0.01, 0.5), (700, 0.02, 0.4)], 0.7, seed=1), 0)
    t = secs(0.6)
    hum = (np.sin(2 * np.pi * 100 * t) + 0.4 * np.sin(2 * np.pi * 200 * t)) * env_shape(len(t), [(0, 0), (0.1, 0.06), (0.6, 0)])
    place(x, hum, 0.05)
    return reverb(x, 0.5, 0.15)


@sfx("bottles_clink", "药柜里的瓶子相碰", "器物", vol=-6)
def bottles_clink():
    x = silence(1.2)
    for k, t0 in enumerate((0, 0.21, 0.29)):
        place(x, impact(0.6, [(1700 + 200 * k, 0.3, 1), (2950, 0.2, 0.5), (4800, 0.1, 0.3)], 0.3, seed=k), t0, 1 - 0.25 * k)
    return reverb(x, 0.7, 0.2)


@sfx("drawer", "拉开木抽屉", "器物", vol=-6)
def drawer():
    d = 0.55
    n = int(d * SR)
    slide = bandpass(white(n, 1), 200, 1500) * (0.7 + 0.3 * np.abs(smooth_noise(n, 40, 1)))
    slide *= env_shape(n, [(0, 0), (0.05, 0.6), (0.5, 0.5), (0.55, 0)])
    x = place(silence(0.9), slide, 0)
    place(x, impact(0.3, [(180, 0.05, 1), (520, 0.03, 0.5)], 0.6, seed=2), 0.52, 0.8)
    place(x, impact(0.2, [(2600, 0.04, 1)], 0.3, seed=3), 0.55, 0.2)  # 里面的东西晃一下
    return reverb(x, 0.6, 0.15)


@sfx("liquid", "药液晃动", "器物", vol=-8)
def liquid():
    d = 2.6
    n = int(d * SR)
    t = secs(d)
    slosh = lowpass(white(n, 1), 1200) * (0.5 + 0.5 * np.sin(2 * np.pi * 1.4 * t)) ** 2
    def bub(i, r):
        dd = r.uniform(0.02, 0.05)
        f = np.linspace(r.uniform(400, 900), r.uniform(900, 1600), int(dd * SR))
        return np.sin(2 * np.pi * np.cumsum(f) / SR) * env_exp(len(f), dd / 3)
    x = slosh * 0.6 + grains(d, 12, bub, seed=2) * 0.3
    return reverb(x * env_shape(n, [(0, 0), (0.2, 1), (2.2, 1), (2.6, 0)]), 0.6, 0.15)


@sfx("cutlery", "刀叉轻碰", "器物", vol=-8)
def cutlery():
    x = silence(1.0)
    for k, t0 in enumerate((0, 0.18, 0.42)):
        place(x, impact(0.5, [(2950, 0.2, 1), (4420, 0.15, 0.6), (6900, 0.08, 0.3), (8300, 0.05, 0.2)], 0.3, seed=k, detune=0.05),
              t0, 0.8 - 0.2 * k)
    return reverb(x, 0.8, 0.2)


@sfx("page_turn", "翻页声", "器物", vol=-8)
def page_turn():
    d = 0.5
    n = int(d * SR)
    sw = bandpass(white(n, 1), 800, 7000) * env_shape(n, [(0, 0), (0.15, 0.6), (0.3, 1), (0.42, 0.2), (0.5, 0)])
    x = place(silence(0.7), sw, 0)
    place(x, click(0.006, 1000, 5000, seed=2), 0.33, 0.6)
    return reverb(x, 0.4, 0.1)


@sfx("paper_rustle", "纸张摩擦", "器物", vol=-8)
def paper_rustle():
    d = 1.2
    n = int(d * SR)
    crk = grains(d, 90, lambda i, r: click(0.004, 1200, 8000, seed=i) * r.uniform(0.1, 0.8), seed=3)
    sw = bandpass(white(n, 4), 1000, 6000) * 0.3 * (0.5 + 0.5 * smooth_noise(n, 6, 4))
    return reverb((crk + sw) * env_shape(n, [(0, 0), (0.1, 1), (1.0, 0.8), (1.2, 0)]), 0.4, 0.1)


@sfx("wardrobe_open", "打开衣柜：柜门吱呀，衣架轻碰", "器物", vol=-6)
def wardrobe_open():
    d = 1.2
    n = int(d * SR)
    cr = friction(d, env_shape(n, [(0, 25), (0.6, 55), (1.2, 35)]), [(300, 10, 1), (780, 12, 0.6), (1700, 14, 0.3)], seed=3)
    cr *= env_shape(n, [(0, 0), (0.1, 1), (1.0, 0.7), (1.2, 0)])
    hang = grains(0.8, 10, lambda i, r: modal(0.2, [(r.uniform(2500, 4500), 0.06, 1)], seed=i) * 0.4, seed=4)
    x = place(silence(2.0), cr * 0.7, 0)
    place(x, hang, 0.7)
    return reverb(x, 0.7, 0.2)


@sfx("ring_box", "合上首饰盒", "器物", vol=-8)
def ring_box():
    return reverb(impact(0.3, [(900, 0.03, 1), (2100, 0.02, 0.5), (240, 0.03, 0.6)], 0.5, seed=1), 0.5, 0.15)


@sfx("flash_powder", "镁粉闪光灯“砰”的一声", "器物", vol=-4)
def flash_powder():
    d = 1.2
    n = int(d * SR)
    whump = lowpass(white(n, 1), 2500) * env_exp(n, 0.12, 0.004)
    low = modal(d, [(60, 0.1, 1)], seed=2)
    sizzle = grains(0.6, 80, lambda i, r: click(0.003, 2000, 9000, seed=i) * r.uniform(0.1, 0.5), seed=3,
                    amp_env=lambda t: np.exp(-t / 0.2))
    x = whump + 0.6 * low
    place(x, sizzle, 0.05, 0.4)
    return reverb(x, 1.6, 0.3)


@sfx("shutter_old", "老相机的快门", "器物", vol=-6)
def shutter_old():
    x = silence(0.5)
    place(x, impact(0.08, [(2400, 0.01, 1), (5200, 0.006, 0.4)], 0.6, seed=1), 0)
    place(x, impact(0.1, [(1900, 0.012, 1), (4100, 0.008, 0.4)], 0.6, seed=2), 0.09, 0.8)
    return reverb(x, 0.4, 0.1)


@sfx("wind", "花园里的风", "环境", loop=True, vol=-8)
def wind():
    d = 14.0
    n = int(d * SR)
    def ch(seed):
        x = np.zeros(n)
        for k, (lo, hi) in enumerate(((150, 350), (300, 600), (550, 1000), (900, 1700))):
            band = bandpass(colored(n, 1, seed + k), lo, hi)
            band /= np.abs(band).max() + 1e-9
            x += band * (0.4 + 0.6 * (0.5 + 0.5 * smooth_noise(n, 0.4, seed + 10 + k))) ** 2
        whistle = resonant(white(n, seed + 20), [(760, 40, 1)]) * (0.5 + 0.5 * smooth_noise(n, 0.3, seed + 30)) ** 3
        x += 0.15 * whistle / (np.abs(whistle).max() + 1e-9)
        return loopify(x, 1.0)
    return stereo(ch(41), ch(51))


# ======================= 第 3 章 =======================

@sfx("paper_slide", "深夜，一张纸从门缝里塞进来", "器物", vol=-8)
def paper_slide():
    d = 0.9
    n = int(d * SR)
    x = bandpass(white(n, 1), 1200, 4500) * env_shape(n, [(0, 0), (0.15, 0.5), (0.6, 0.8), (0.9, 0)])
    x *= 1 + 0.4 * smooth_noise(n, 30, 1)
    return reverb(x, 0.6, 0.2)


@sfx("crayon", "蜡笔在纸上补一笔", "器物", vol=-8)
def crayon():
    x = silence(1.4)
    for k in range(3):
        d = 0.3
        n = int(d * SR)
        s = bandpass(white(n, k), 1500, 5000) * (0.5 + 0.5 * np.abs(smooth_noise(n, 120, k)))
        place(x, s * env_shape(n, [(0, 0), (0.03, 1), (0.25, 0.8), (0.3, 0)]), 0.1 + 0.42 * k, 0.6)
    return reverb(x, 0.4, 0.1)


@sfx("cloth_rustle", "布料摩擦（黑布、大衣）", "器物", vol=-8)
def cloth_rustle():
    d = 1.2
    n = int(d * SR)
    x = lowpass(white(n, 1), 2500) * (0.3 + 0.7 * np.abs(smooth_noise(n, 5, 1)))
    return reverb(x * env_shape(n, [(0, 0), (0.15, 1), (1.0, 0.6), (1.2, 0)]), 0.4, 0.1)


@sfx("music_box", "八音盒：儿歌（发条快走完，有点慢、有点走音）", "器物", loop=True, vol=-12)
def music_box():
    notes, total = rhyme_notes(RHYME, beat=0.5, transpose=12)
    d = total + 1.0
    x = silence(d)
    for i, (t0, dur, m) in enumerate(notes):
        f = midi_hz(m) * (1 - 0.004 * (i % 3))  # 梳齿有点走音
        tine = modal(1.6, [(f, 0.7, 1), (f * 3.01, 0.25, 0.25), (f * 5.4, 0.1, 0.1)], seed=i)
        place(x, tine, t0 * (1 + 0.002 * i), 0.6)  # 越走越慢一点
    x = reverb(x, 1.0, 0.3)[: int(d * SR)]
    return loopify(np.concatenate([x, silence(1.0)]), 0.8)


def _hum(lines):
    notes, total = rhyme_notes(lines, beat=0.46, transpose=-12)
    d = total + 0.6
    n = int(d * SR)
    f0 = np.full(n, midi_hz(notes[0][2]))
    amp = np.zeros(n)
    for t0, dur, m in notes:
        a, b = int(t0 * SR), int((t0 + dur) * SR)
        f0[a:] = midi_hz(m)
        amp[a:b] = 1
    k = int(0.04 * SR)
    kern = np.ones(k) / k
    f0 = np.convolve(f0, kern, "same")
    amp = np.convolve(amp, np.ones(int(0.06 * SR)) / int(0.06 * SR), "same")
    f0 *= 1 + 0.015 * np.sin(2 * np.pi * 5.5 * secs(d))
    v = voice(f0, "m", breath=0.03, seed=3, tilt=1.8)
    return reverb(lowpass(v * amp, 2500), 1.2, 0.35)


@sfx("hum_rhyme", "小女孩哼儿歌（整首）", "人声", vol=-8)
def hum_rhyme():
    return _hum(RHYME)


@sfx("hum_rhyme_line", "小女孩哼一句儿歌就跑开", "人声", vol=-8)
def hum_rhyme_line():
    return _hum(RHYME[:1])


@sfx("gasp_iris", "小女孩一声被压住的抽气", "人声", vol=-6)
def gasp_iris():
    d = 0.45
    n = int(d * SR)
    air = resonant(white(n, 1), VOWELS["h"]) * env_shape(n, [(0, 0), (0.05, 1), (0.25, 0.7), (0.45, 0)])
    sq = voice(np.full(n, 620.0) * env_shape(n, [(0, 1), (0.45, 1.15)]), "ae", breath=0.2, seed=2)
    sq *= env_shape(n, [(0, 0), (0.06, 0.25), (0.15, 0)])
    return reverb(air * 0.7 + sq, 1.0, 0.3)


# ======================= 第 4 章 =======================

@sfx("paper_slap", "签收单“啪”地拍在桌上", "器物", vol=-4)
def paper_slap():
    x = impact(0.4, [(150, 0.05, 1), (420, 0.03, 0.5)], 1.2, 0.012, 300, 6000, seed=1)
    return reverb(x, 0.7, 0.2)


@sfx("latch_greenhouse", "温室侧门的门闩", "器物", vol=-6)
def latch_greenhouse():
    x = silence(0.8)
    place(x, impact(0.5, [(1400, 0.12, 1), (3600, 0.06, 0.5), (5900, 0.03, 0.2)], 0.5, seed=1), 0)
    place(x, impact(0.3, [(1250, 0.08, 1), (3100, 0.04, 0.4)], 0.4, seed=2), 0.16, 0.5)
    return reverb(x, 1.2, 0.3)


@sfx("footstep_boot", "园丁的靴子（重、闷）", "人声", vol=-4)
def footstep_boot():
    x = lowpass(impact(0.35, [(85, 0.06, 1), (190, 0.04, 0.6), (430, 0.02, 0.3)], 0.6, 0.01, seed=1), 1500)
    place(x, friction(0.2, 60, [(800, 8, 1)], seed=2), 0.03, 0.15)  # 皮靴的一点吱声
    return x


@sfx("footstep_shoe", "男式皮鞋（脆、硬）", "人声", vol=-4)
def footstep_shoe():
    x = silence(0.3)
    place(x, impact(0.2, [(2100, 0.012, 1), (3400, 0.008, 0.6), (1200, 0.02, 0.4), (150, 0.02, 0.5)], 0.7, 0.002, seed=1), 0)
    place(x, impact(0.15, [(1600, 0.01, 1), (120, 0.02, 0.5)], 0.5, seed=2), 0.07, 0.5)  # 脚掌落下
    return x


# ======================= 第 5 章 =======================

@sfx("candle", "烛火", "环境", loop=True, vol=-12)
def candle():
    d = 8.0
    n = int(d * SR)
    flame = lowpass(colored(n, 2, 1), 300) * (0.6 + 0.4 * smooth_noise(n, 6, 1))
    pops = grains(d, 1.5, lambda i, r: click(0.004, 1500, 6000, seed=i) * r.uniform(0.2, 0.6), seed=2)
    return loopify(flame + 0.5 * pops, 0.5)


@sfx("seance_bell", "降灵会的手摇铃", "器物", vol=-6)
def seance_bell():
    x = silence(2.4)
    f = 1760.0
    for k, t0 in enumerate((0, 0.17, 0.33, 0.52, 0.7)):
        place(x, modal(1.6, [(f, 0.7, 1), (f * 2.32, 0.45, 0.5), (f * 4.1, 0.2, 0.25), (f * 5.4, 0.1, 0.12)], seed=k, detune=0.002),
              t0, 0.9 - 0.12 * k)
    return reverb(x, 1.5, 0.3)


@sfx("planchette", "写板在桌面上慢慢划过", "器物", vol=-8)
def planchette():
    d = 2.2
    n = int(d * SR)
    x = friction(d, env_shape(n, [(0, 35), (1.1, 70), (2.2, 40)]), [(380, 6, 1), (900, 8, 0.6), (2100, 10, 0.3)], seed=1, noise=1.0)
    x += 0.3 * bandpass(white(n, 2), 300, 2000)
    return reverb(x * env_shape(n, [(0, 0), (0.2, 1), (2.0, 0.8), (2.2, 0)]), 0.8, 0.2)


@sfx("chair_drag", "椅子在木地板上拖动（桌边多了一把空椅子）", "器物", vol=-4)
def chair_drag():
    d = 1.1
    n = int(d * SR)
    x = friction(d, env_shape(n, [(0, 22), (0.5, 48), (1.1, 30)]), [(150, 6, 1), (430, 8, 0.7), (1050, 10, 0.4)], seed=2, jitter=0.4)
    x *= env_shape(n, [(0, 0), (0.05, 1), (1.0, 0.8), (1.1, 0)])
    y = place(silence(1.6), x, 0)
    place(y, impact(0.3, [(120, 0.05, 1), (380, 0.03, 0.4)], 0.5, seed=3), 1.12, 0.6)
    return reverb(y, 1.0, 0.3)


@sfx("glove_burn", "烛火烧破蕾丝手套的嘶声", "器物", vol=-6)
def glove_burn():
    d = 1.3
    n = int(d * SR)
    hiss = highpass(white(n, 1), 3000) * (0.4 + 0.6 * np.abs(smooth_noise(n, 25, 1))) * env_shape(n, [(0, 0), (0.05, 1), (1.3, 0)])
    crk = grains(d, 50, lambda i, r: click(0.003, 2000, 9000, seed=i) * r.uniform(0.2, 1), seed=2, amp_env=lambda t: np.exp(-t / 0.5))
    whoosh = lowpass(white(n, 3), 800) * env_shape(n, [(0, 0), (0.08, 0.6), (0.4, 0)])
    return reverb(0.4 * hiss + 0.5 * crk + whoosh, 0.7, 0.2)


@sfx("cry_latente", "灵媒被烫到的一声痛呼", "人声", vol=-4)
def cry_latente():
    d = 0.75
    n = int(d * SR)
    f0 = env_shape(n, [(0, 380), (0.07, 640), (0.3, 520), (0.75, 300)])
    v = voice(f0, "a", breath=0.18, rough=0.15, seed=4)
    v *= env_shape(n, [(0, 0), (0.03, 1), (0.35, 0.7), (0.75, 0)])
    x = place(silence(1.4), v, 0)
    gasp = resonant(white(int(0.35 * SR), 5), VOWELS["h"]) * env_shape(int(0.35 * SR), [(0, 0), (0.05, 0.5), (0.35, 0)])
    place(x, gasp, 0.85, 0.5)
    return reverb(lowpass(x, 6500), 1.3, 0.3)


@sfx("chime_modern", "一声极轻的提示音，不属于这个时代", "渗漏", vol=-14)
def chime_modern():
    x = silence(0.6)
    for f, t0 in ((1568, 0), (2093, 0.12)):
        t = secs(0.35)
        place(x, np.sin(2 * np.pi * f * t) * env_exp(len(t), 0.1, 0.003), t0)
    return x  # 不加混响：干净得不像这个房间里的声音


# ======================= 第 6 章 =======================

@sfx("camera_case", "从三脚架取下相机，打开皮套", "器物", vol=-6)
def camera_case():
    x = silence(1.4)
    place(x, impact(0.2, [(1500, 0.03, 1), (3300, 0.02, 0.5)], 0.6, seed=1), 0)
    leather = friction(0.6, 45, [(500, 5, 1), (1300, 6, 0.5)], seed=2, noise=0.6)
    place(x, leather * env_shape(len(leather), [(0, 0), (0.1, 1), (0.6, 0)]), 0.3, 0.6)
    place(x, impact(0.2, [(2200, 0.02, 1)], 0.5, seed=3), 1.0, 0.6)  # 按扣
    return reverb(x, 0.7, 0.2)


@sfx("timer_tick", "暗房定时器走完，“叮”", "器物", vol=-8)
def timer_tick():
    x = silence(4.6)
    for k in range(16):
        place(x, impact(0.05, [(3100, 0.006, 1), (5200, 0.004, 0.4)], 0.4, seed=k), k * 0.25, 0.5)
    place(x, modal(1.0, [(2350, 0.4, 1), (3700, 0.2, 0.3)], seed=99), 4.0, 0.8)
    return reverb(x, 0.6, 0.2)


@sfx("red_hum", "暗房红灯的嗡鸣", "环境", loop=True, vol=-16)
def red_hum():
    d = 4.0  # 4 秒里 100 Hz 正好整数个周期，首尾自然接上
    t = secs(d)
    x = np.sin(2 * np.pi * 100 * t) + 0.5 * np.sin(2 * np.pi * 200 * t) + 0.25 * np.sin(2 * np.pi * 300 * t)
    buzz = np.sign(np.sin(2 * np.pi * 100 * t)) * 0.05
    return x * 0.5 + lowpass(buzz, 2000)


# ======================= 第 7 章与尾声 =======================

@sfx("footstep_white", "脚步（白色走廊：发空，没有回响）", "人声", vol=-6)
def footstep_white():
    x = silence(0.15)
    t = secs(0.15)
    x += np.sin(2 * np.pi * 110 * t) * env_exp(len(t), 0.03, 0.002)
    place(x, click(0.003, 3000, 9000, seed=1), 0, 0.3)
    return x  # 不加混响：这条走廊不该有回声


@sfx("room_tone_white", "白色房间的底噪（无菌、几乎听不见）", "渗漏", loop=True, vol=-18)
def room_tone_white():
    d = 8.0
    n = int(d * SR)
    t = secs(d)
    x = loopify(lowpass(colored(n, 1, 61), 2500) * 0.4, 0.5)
    t = secs(len(x) / SR)
    return x + 0.08 * np.sin(2 * np.pi * 1000 * t)  # 1 kHz 测试音，极轻；7.5 秒里正好整数周期


@sfx("click_clean", "一声很干净的“咔”", "渗漏", vol=-6)
def click_clean():
    x = silence(0.3)
    place(x, click(0.002, 2000, 12000, seed=1), 0)
    t = secs(0.06)
    place(x, 0.3 * np.sin(2 * np.pi * 3000 * t) * env_exp(len(t), 0.01), 0.001)
    return x


@sfx("monitor_hum", "很多块屏幕的低鸣", "渗漏", loop=True, vol=-12)
def monitor_hum():
    d = 8.0
    t = secs(d)
    x = np.zeros_like(t)
    for k, f in enumerate((60.0, 60.125, 59.875, 120.0, 120.25, 180.0)):  # 8 秒里都是整数周期
        x += (1 / (1 + k)) * np.sin(2 * np.pi * f * t)
    whine = 0.03 * np.sin(2 * np.pi * 7812.5 * t)
    return stereo(x * 0.4 + whine, x * 0.4 + np.roll(whine, 37))


@sfx("dot_print", "记录卡打出来：针式打印", "渗漏", vol=-8)
def dot_print():
    x = silence(1.6)
    for k in range(5):
        d = 0.22
        t = secs(d)
        burst = np.sign(np.sin(2 * np.pi * 1450 * t)) * 0.3 + bandpass(white(len(t), k), 2000, 6000) * 0.3
        burst *= (np.sin(2 * np.pi * 90 * t) > 0)
        place(x, burst * env_shape(len(t), [(0, 0), (0.01, 1), (0.2, 1), (0.22, 0)]), 0.05 + k * 0.28, 0.6)
    return reverb(x, 0.3, 0.1)


@sfx("water_pump", "井边压水", "器物", vol=-6)
def water_pump():
    x = silence(2.4)
    for k in range(2):
        sq = friction(0.35, env_shape(int(0.35 * SR), [(0, 80), (0.35, 160)]), [(900, 12, 1), (2300, 16, 0.5)], seed=k)
        place(x, sq * 0.5, k * 1.0)
        gush = bandpass(white(int(0.7 * SR), 10 + k), 300, 2500) * env_shape(int(0.7 * SR), [(0, 0), (0.1, 1), (0.7, 0)])
        place(x, gush * 0.7, k * 1.0 + 0.3)
    return reverb(x, 1.0, 0.25)


@sfx("birds_morning", "早晨的鸟叫", "环境", vol=-10)
def birds_morning():
    d = 6.0
    def chirp(i, r):
        dd = r.uniform(0.05, 0.12)
        n = int(dd * SR)
        f = np.linspace(r.uniform(3000, 4500), r.uniform(4500, 6500), n) * (1 + 0.08 * np.sin(2 * np.pi * r.uniform(30, 60) * np.arange(n) / SR))
        return np.sin(2 * np.pi * np.cumsum(f) / SR) * np.sin(np.pi * np.arange(n) / n) ** 2
    def phrase(i, r):
        k = r.integers(2, 6)
        out = silence(1.0)
        for j in range(k):
            place(out, chirp(i * 10 + j, r), j * r.uniform(0.09, 0.15), r.uniform(0.5, 1))
        return out
    x = grains(d, 1.6, phrase, seed=7)
    return distant(x, 9000, 1.5, 0.4)


# ======================= 脚步与界面 =======================

@sfx("footstep_wood", "玩家脚步（木地板）", "人声", vol=-8)
def footstep_wood():
    x = silence(0.35)
    place(x, lowpass(impact(0.3, [(95, 0.04, 1), (210, 0.03, 0.6), (620, 0.015, 0.4)], 0.6, 0.004, seed=1), 3500), 0)
    return reverb(x, 0.5, 0.12)


@sfx("footstep_carpet", "脚步（地毯）", "人声", vol=-10)
def footstep_carpet():
    x = lowpass(impact(0.25, [(80, 0.03, 1), (180, 0.02, 0.4)], 0.8, 0.02, seed=2), 900)
    return reverb(x, 0.4, 0.1)


@sfx("footstep_stone", "脚步（温室地砖）", "人声", vol=-8)
def footstep_stone():
    x = impact(0.25, [(1700, 0.01, 1), (2900, 0.008, 0.5), (140, 0.02, 0.6)], 0.6, 0.002, seed=3)
    return reverb(x, 0.9, 0.25)


@sfx("door_creak", "开门 / 关门（木门合页吱呀一声）", "器物", vol=-6)
def door_creak():
    d = 0.9
    n = int(d * SR)
    cr = friction(d, env_shape(n, [(0, 40), (0.5, 90), (0.9, 60)]), [(420, 12, 1), (1050, 14, 0.6), (2300, 18, 0.3)], seed=8)
    cr *= env_shape(n, [(0, 0), (0.08, 1), (0.8, 0.7), (0.9, 0)])
    x = place(silence(1.2), impact(0.15, [(1700, 0.02, 1)], 0.5, seed=9), 0, 0.5)
    place(x, cr * 0.7, 0.05)
    return reverb(x, 0.8, 0.2)


@sfx("pin", "图钉轻响", "器物", vol=-8)
def pin():
    x = impact(0.15, [(4200, 0.015, 1), (6800, 0.01, 0.4), (300, 0.02, 0.5)], 0.6, 0.002, seed=1)
    return reverb(x, 0.3, 0.1)


@sfx("ui_board_open", "翻开证据板：纸页与软木", "界面", vol=-10)
def ui_board_open():
    d = 0.35
    n = int(d * SR)
    sw = bandpass(white(n, 1), 600, 5000) * env_shape(n, [(0, 0), (0.12, 0.8), (0.35, 0)])
    x = place(silence(0.5), sw, 0)
    place(x, lowpass(impact(0.15, [(160, 0.03, 1)], 0.5, seed=2), 1500), 0.22, 0.6)
    return x


@sfx("ui_collect", "收进证据板：铅笔记了一笔", "界面", vol=-10)
def ui_collect():
    d = 0.22
    n = int(d * SR)
    s = bandpass(white(n, 3), 2000, 7000) * (0.5 + 0.5 * np.abs(smooth_noise(n, 150, 3))) * env_shape(n, [(0, 0), (0.02, 1), (0.2, 0.6), (0.22, 0)])
    x = place(silence(0.4), s * 0.6, 0)
    place(x, click(0.003, 2000, 6000, seed=4), 0.22, 0.5)
    return x


@sfx("ui_link_ok", "连线连上：红线绷紧", "界面", vol=-8)
def ui_link_ok():
    x = place(silence(1.2), ks_string(1.0, 196, 0.994, seed=1), 0, 0.8)
    place(x, impact(0.1, [(4200, 0.01, 1)], 0.5, seed=2), 0, 0.4)
    return x


@sfx("ui_link_wrong", "连错：红线松掉，弹回去", "界面", vol=-8)
def ui_link_wrong():
    return place(silence(1.0), ks_string(0.8, 150, 0.99, seed=3, bend=0.82), 0, 0.8)


# ======================= 输出 =======================

# ======================= 第 5 章：回廊 =======================

@sfx("needle_scratch", "唱针跳了：一声刮擦", "器物", vol=-4)
def needle_scratch():
    d = 0.45
    n = int(d * SR)
    # 一段被猛地拖回沟槽的摩擦：窄带噪声 + 频率快速下滑的叫声
    hiss = bandpass(white(n, 7), 1800, 7000) * env_shape(n, [(0, 0), (0.01, 1), (0.12, 0.7), (0.45, 0)])
    sweep = modal(d, [(1700, 0.12, 0.9)], seed=8)
    t = secs(d)
    glide = np.sin(2 * np.pi * np.cumsum(1600 * np.exp(-t * 6) + 200) / SR) * np.exp(-t * 9) * 0.5
    x = hiss + 0.5 * sweep + glide
    return reverb(x, 0.5, 0.15)


@sfx("room_hum", "回廊底噪：空房间的低鸣", "环境", loop=True, vol=-16)
def room_hum():
    d = 8.0
    n = int(d * SR)
    base = (np.sin(2 * np.pi * 48 * secs(d)) * 0.3
            + np.sin(2 * np.pi * 97 * secs(d)) * 0.12
            + np.sin(2 * np.pi * 151 * secs(d)) * 0.05)
    air = lowpass(white(n, 11), 420) * 0.35
    x = base + air
    x *= 0.8 + 0.2 * smooth_noise(n, 0.2, 12)
    return loopify(x, 1.2)


def normalize(x, loop):
    if x.ndim == 1:
        x = stereo(x)
    x = np.stack([highpass(x[:, c], 20, 2) for c in range(2)], axis=1)  # 切掉直流和次声
    if loop:
        r = np.sqrt((x ** 2).mean())
        x = x * (0.1 / max(r, 1e-9))  # 循环底噪按响度对齐（约 -20 dBFS），音量再交给表格
        p = np.abs(x).max()
        if p > 0.9:
            x *= 0.9 / p
    else:
        x = x * (0.7 / max(np.abs(x).max(), 1e-9))  # 单次音效按峰值对齐（-3 dBFS）
    return x


def write(sid, x):
    OUT.mkdir(parents=True, exist_ok=True)
    tmp = OUT / f"{sid}.tmp.wav"
    pcm = (np.clip(x, -1, 1) * 32767).astype(np.int16)
    with wave.open(str(tmp), "wb") as w:
        w.setnchannels(2), w.setsampwidth(2), w.setframerate(SR)
        w.writeframes(pcm.tobytes())
    subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-i", str(tmp), "-c:a", "vorbis", "-strict", "-2",
                    "-ac", "2", "-b:a", "160k", str(OUT / f"{sid}.ogg")], check=True)
    tmp.unlink()


def update_table(done):
    rows = list(csv.DictReader(open(TABLE, newline="")))
    fields = list(rows[0].keys())
    have = {r["id"] for r in rows}
    for sid in done:
        meta = RECIPES[sid]
        if sid not in have:
            rows.append({"id": sid, "name": meta["name"], "category": meta["category"], "file": "",
                         "volume_db": str(meta["vol"]), "loop": "是" if meta["loop"] else "否", "note": ""})
        for r in rows:
            if r["id"] == sid:
                r["file"] = f"sfx/{sid}.ogg"
                if NOTE not in r["note"]:
                    r["note"] = (r["note"] + "；" if r["note"] else "") + NOTE
                if r["volume_db"] in ("", "0"):
                    r["volume_db"] = str(meta["vol"])
    with open(TABLE, "w", newline="") as f:
        w = csv.DictWriter(f, fields, lineterminator="\n")
        w.writeheader()
        w.writerows(rows)


if __name__ == "__main__":
    args = sys.argv[1:]
    if "--list" in args:
        for sid, m in RECIPES.items():
            print(f"{sid:22s} {m['category']}  {'循环' if m['loop'] else '单次'}  {m['name']}")
        sys.exit()
    recorded_manifest = Path(__file__).resolve().parents[1] / "recordings/rain/sources.json"
    recorded = json.loads(recorded_manifest.read_text()) if recorded_manifest.exists() else {}
    requested = args or list(RECIPES)
    ids = [sid for sid in requested if sid not in recorded]
    for sid in requested:
        if sid in recorded:
            print(f"  {sid}: 保留实录，不合成覆盖（重建请用 import_recorded_rain.py）")
    if not ids:
        sys.exit()
    for sid in ids:
        meta = RECIPES[sid]
        x = normalize(np.asarray(meta["fn"](), float), meta["loop"])
        if not meta["loop"]:
            x = trim_tail(x)
        write(sid, x)
        print(f"  {sid:22s} {len(x) / SR:5.2f} 秒")
    update_table(ids)
    print(f"共 {len(ids)} 个 → {OUT}")
