"""回廊的“按步触发”节奏层（10-20 方案 A）与走走停停的试听模拟。

玩家不会一直按着 W：会停、会慢、会快、会往回走。所以节奏层不随唱针拉伸，而是**按距离触发**：
沿走廊每走过 0.7 米（一步）弹一下；往回走过一步，放这一下的倒放（先轻后重、“吸”回去）。
唱片那层（低音提琴、镲片、弱音小号）照旧跟着唱针：位置决定播放点，速度决定快慢和音高，倒走就倒放，停下就停。

    python3 assets/audio/music/scripts/corridor_steps.py            # 渲染单步音样 + 两版试听（班卓琴 / 钢琴）
    python3 assets/audio/music/scripts/corridor_steps.py --game     # 另把选定乐器的单步音样放进 godot/audio/music/steps/

输出（preview/）：
  corridor_steps_<乐器>.ogg   模拟一段真实操作：走 → 停下环顾 → 慢走 → 快走 → 停 → 往回走 → 再走，穿过尽头的门进第 2 圈
"""

import argparse
import subprocess
import sys
import wave
import zlib
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).parent))
import compose_corridor as cc  # noqa: E402
import compose_latent_image as lat  # noqa: E402

ROOT = Path(__file__).resolve().parents[1]
PREV = ROOT / "preview"
STEP = 0.7
SR = 44100

# 每一步弹什么：四步一小节。1 低音区根音 + 五音，2 四度和弦，3 低音区五音，4 四度和弦；第 8 步换成往下一个全音的回答
LOW_ROOT = [38, 45]          # D2 + A2
LOW_FIFTH = [45]             # A2
SHOTS = {
    "root": LOW_ROOT,
    "fifth": LOW_FIFTH,
    "quartal": cc.QUARTAL,
    "answer": cc.ANSWER,
}
PATTERN = ["root", "quartal", "fifth", "quartal", "root", "quartal", "fifth", "answer"]
INSTR = {  # 名称：(GM 音色, 时值拍, 力度, 移八度)
    "banjo": (105, 0.35, 58, 0),
    "piano": (0, 0.5, 50, -12),
}


def shot_name(k, lap):
    return PATTERN[k % len(PATTERN)] + ("_up" if lap == 2 else "")  # 第 3 圈整体升高半音


def render_shots(instr):
    """每种音样隔 2 秒放一个，一次渲染完再切开。返回 {名称: 数组}。"""
    prog, dur, vel, octave = INSTR[instr]
    t = lat.Track(instr, 0, prog, swing=False)
    t.cc(0, 7, 110)
    t.cc(0, 91, 30)
    names = []
    for up in (0, 1):
        for name, notes in SHOTS.items():
            beat = len(names) * 4  # 120 BPM：4 拍 = 2 秒
            for j, p in enumerate(notes):
                t.note(beat + j * 0.01, dur, p + octave + up, vel + (6 if name in ("root", "fifth") else 0), jitter=False)
            names.append(name + ("_up" if up else ""))
    t.cc(len(names) * 4 + 2, 110, 0)
    lat.BPM = cc.BPM
    mid = PREV / f"_shots_{instr}.mid"
    raw = PREV / f"_shots_{instr}.wav"
    lat.write_midi([t], mid)
    subprocess.run(["fluidsynth", "-ni", "-g", "0.7", "-r", str(SR), "-F", str(raw), str(lat.SF2), str(mid)],
                   check=True, capture_output=True)
    _, x = cc.read_wav(raw)
    mid.unlink()
    raw.unlink()
    out = {}
    for i, name in enumerate(names):
        seg = x[i * 2 * SR:(i * 2 + 2) * SR].copy()
        a = np.abs(seg).max(axis=1)
        last = np.nonzero(a > 1e-3 * max(a.max(), 1e-9))[0]
        seg = seg[: (last[-1] + int(0.02 * SR)) if len(last) else SR]
        seg[-int(0.02 * SR):] *= np.linspace(1, 0, int(0.02 * SR))[:, None]
        out[name] = seg
    return out


def reverse_shot(s, sr=SR, keep=0.35):
    """倒放：只取起音最前面的 0.35 秒再反过来，先轻后重、短促地“吸”一下，不拖尾巴。"""
    r = s[: int(keep * sr)][::-1].copy()
    f = int(0.03 * sr)
    r[:f] *= np.linspace(0, 1, f) if r.ndim == 1 else np.linspace(0, 1, f)[:, None]
    return r


# 一段真实操作：(持续秒, 沿走廊的速度 m/s)。负数 = 往回走
MOVES = [(3.0, 1.4), (1.6, 0.0), (1.5, 0.7), (2.0, 1.9), (1.2, 0.0), (2.0, -1.1), (0.8, 0.0),
         (5.5, 1.4), (4.0, 1.4), (1.0, 0.0), (3.0, 1.4)]


def simulate(shots, record_clean, sr=SR):
    ctl = 200  # 控制频率
    # 位置曲线（带一点加减速，像真人松开、按下 W）
    v = np.concatenate([np.full(int(d * ctl), s) for d, s in MOVES])
    k = np.exp(-np.arange(int(0.12 * ctl)) / (0.04 * ctl))
    v = np.convolve(v, k / k.sum())[: len(v)]
    pos = np.cumsum(v) / ctl
    lens = [cc.SEG_A + s for s in cc.SEG_B]
    # 进第 2 圈：走过第 1 圈尽头（14 m）就回到起点
    lap = np.zeros(len(pos), int)
    p_lap = pos.copy()
    over = pos >= lens[0] - 0.35
    if over.any():
        i0 = np.argmax(over)
        lap[i0:] = 1
        p_lap[i0:] = pos[i0:] - pos[i0] + 0.15
    n = int(len(pos) / ctl * sr)
    tt = np.arange(n) / sr
    pa = np.interp(tt, np.arange(len(pos)) / ctl, p_lap)
    la = np.interp(tt, np.arange(len(pos)) / ctl, lap).round().astype(int)
    va = np.interp(tt, np.arange(len(pos)) / ctl, v)
    # 唱片层：每圈一段切片，播放点 = 位置 / 路径长 × 切片长；停下时淡出
    starts = np.concatenate([[0], np.cumsum(cc.LAP_SEC)])
    src = (starts[la] + np.clip(pa / np.array(lens)[la], 0, 1) * np.array(cc.LAP_SEC)[la]) * sr
    mono = record_clean.mean(axis=1)
    rec = np.interp(src, np.arange(len(mono)), mono)
    gate = (np.abs(va) > 0.12).astype(float)
    kg = np.exp(-np.arange(int(0.1 * sr)) / (0.03 * sr))
    gate = np.convolve(gate, kg / kg.sum())[:n]
    rec *= gate
    # 节奏层：每越过一个 0.7 m 的格子弹一下；往回越过就放倒放
    steps = np.zeros(n)
    cell = np.floor(p_lap / STEP).astype(int)
    for i in range(1, len(cell)):
        if cell[i] == cell[i - 1] and lap[i] == lap[i - 1]:
            continue
        if lap[i] != lap[i - 1]:
            continue  # 推门回到起点，不算一步
        fwd = cell[i] > cell[i - 1]
        kstep = cell[i] if fwd else cell[i - 1]
        s = shots[shot_name(kstep, lap[i])].mean(axis=1)
        if not fwd:
            s = reverse_shot(s, sr)
        at = int(i / ctl * sr)
        at = max(at, 0)
        e = min(n, at + len(s))
        steps[at:e] += s[: e - at] * (0.9 if fwd else 0.75)
    r = lambda x: np.sqrt((x[np.abs(x) > 1e-4] ** 2).mean()) if (np.abs(x) > 1e-4).any() else 1
    steps *= 0.55 * r(rec) / r(steps)
    mix = np.stack([rec + steps] * 2, axis=1)
    return cc.gramophone(mix, sr, seed=7), pos, v


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--game", metavar="乐器", help="把这种乐器的单步音样放进 godot/audio/music/steps/")
    args = ap.parse_args()
    _, record = cc.read_wav(PREV / "corridor_record.wav")
    for instr in INSTR:
        shots = render_shots(instr)
        out, pos, v = simulate(shots, record)
        cc.write(out, SR, PREV / f"corridor_steps_{instr}")
        (PREV / f"corridor_steps_{instr}.wav").unlink()
        print(f"{instr}：{len(out) / SR:.1f} 秒 → preview/corridor_steps_{instr}.ogg（共走 {int(np.abs(np.diff(np.floor(np.clip(pos, 0, None) / STEP))).sum())} 格）")
        if args.game == instr:
            d = ROOT.parents[2] / "godot" / "audio" / "music" / "steps"
            d.mkdir(parents=True, exist_ok=True)
            for name, s in shots.items():
                g = cc.gramophone(s, SR, seed=zlib.crc32(name.encode()) % 1000)[: len(s)]
                cc.write(g, SR, d / name)
                cc.write(reverse_shot(g), SR, d / f"{name}_rev")
                (d / f"{name}.wav").unlink()
                (d / f"{name}_rev.wav").unlink()
            print("单步音样 →", d)
