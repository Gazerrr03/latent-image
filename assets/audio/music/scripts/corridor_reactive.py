"""回廊的响应式音乐（10-20 用户定，取代“整张唱片跟着唱针”的做法）。

三层：
  底色 BGM   低音提琴、镲片、弱音小号。按时间一直在放，每圈一段 8 小节无缝循环；
             玩家往回走时倒放；停下时压低一点、变闷（像唱针抬起了一点）
  脚步层     鼓点 + 钢琴。按距离触发：沿走廊每走过一步（0.7 m）一下，**对齐到底色的下一个十六分音符**，
             所以玩家怎么走，出来的都在拍子上。左脚落地鼓（闷），右脚鼓边（嗒）；钢琴叠在第 1、3、5、7 步，
             第 8 步换成往下一个全音的回答。往回走用倒放音样（短促地“吸”一下）
  唱片人声   每圈的剧情人声与字幕（godot/audio/voice/corridor_l*.ogg）照旧跟着唱针：位置决定播放点，停下就停

底色每圈一段（越往里乐队越少）：
  1 低音提琴走路 + 镲片      2 加弱音小号（第一句是《潜影》动机 F A C B）
  3 整体升高半音，小号长音往下走调      4 只剩低音提琴      5 只剩走了音的钢琴回答
  （第 6 圈：底色停下，小号吹动机开头、在第四个音之前断掉 → corridor_ending，见 compose_corridor.py）

    python3 assets/audio/music/scripts/corridor_reactive.py          # 渲染 + 走走停停的试听 preview/corridor_reactive.ogg
    python3 assets/audio/music/scripts/corridor_reactive.py --game   # 另导出底色循环与脚步音样到 godot/audio/music/
"""

import argparse
import subprocess
import sys
import zlib
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).parent))
import compose_corridor as cc  # noqa: E402
import compose_latent_image as lat  # noqa: E402

ROOT = Path(__file__).resolve().parents[1]
PREV = ROOT / "preview"
GAME = ROOT.parents[2] / "godot" / "audio" / "music"
VOICE = ROOT.parents[2] / "godot" / "audio" / "voice"
SR = 44100
BPM = 120
BARS = 8
LOOP_SEC = BARS * 4 * 60 / BPM          # 16 秒
GRID = 60 / BPM / 4                     # 十六分音符 = 0.125 秒
STEP = 0.7
SEG_LEN = [cc.SEG_A + s for s in cc.SEG_B]

# 脚步层：每一步一下鼓（左右交替），钢琴按八步的格子叠上去
PIANO_PAT = ["root", "", "quartal", "", "fifth", "", "quartal", "answer"]
PHRASES = [  # 弱音小号（拍数相对循环开头），与 compose_corridor.py 同一组句子
    (1.5, 0.5, 65, 80), (2.0, 0.5, 69, 84), (2.5, 1.5, 72, 90), (4.0, 2.5, 71, 82),
    (9.0, 0.5, 74, 84), (9.5, 0.5, 72, 80), (10.0, 1.0, 69, 86), (11.0, 0.5, 67, 76), (11.5, 2.0, 65, 78),
    (17.0, 0.5, 64, 70), (17.5, 0.5, 65, 74), (18.0, 2.0, 69, 72),
]


def bed_tracks(lap):
    """第 lap 圈（0 起）的底色：8 小节，循环。"""
    up = 1 if lap == 2 else 0
    bass = lat.Track("低音提琴", 0, 32)
    drums = lat.Track("套鼓", 9, 32)
    piano = lat.Track("钢琴", 1, 0)
    horn = lat.Track("弱音小号", 2, 59)
    for t, pan, vol in ((bass, 64, 96), (drums, 64, 104), (piano, 50, 90), (horn, 72, 122)):
        t.cc(0, 10, pan)
        t.cc(0, 7, vol)
        t.cc(0, 91, 34)
    for b in range(BARS):
        o = b * 4
        if lap <= 3:
            for k, rel in enumerate(cc.WALK[b % len(cc.WALK)]):
                bass.note(o + k, 0.92, 38 + rel + up, (74 if lap < 3 else 84) + (6 if k == 0 else 0))
        if lap <= 2:
            for k in range(4):
                drums.note(o + k, 0.25, 51, 48 if k % 2 == 0 else 42, jitter=False)
                if k in (1, 3):
                    drums.note(o + k, 0.2, 44, 44, jitter=False)
        if lap == 4 and b % 2 == 1:  # 第 5 圈：只剩钢琴的回答，走了音
            for beat, chord, vel in ((o + 3.5, cc.QUARTAL, 48), (o + 4, cc.ANSWER, 42)):
                for j, p in enumerate(chord):
                    piano.note((beat + j * 0.012) % (BARS * 4), 0.8, p, vel)
    if lap == 4:
        piano.bend(0, -1230)
    if lap in (1, 2):
        for beat, dur, p, v in PHRASES:
            horn.note(beat, dur + (2.0 if lap == 2 and beat == 4.0 else 0), p + up, v - (6 if lap == 2 else 0))
        if lap == 2:
            for i in range(1, 9):
                horn.bend(4.6 + i * 0.35, -int(2400 * i / 8))
            horn.bend(14.0, 0)
    horn.cc(BARS * 4 + 4, 110, 0)
    return [t for t in (bass, drums, piano, horn) if len(t.events) > 5]


def render_bed(lap):
    lat.NAME, lat.BPM, lat.BARS = f"_bed{lap + 1}", BPM, BARS
    lat.render(bed_tracks(lap), PREV, loop=True)
    _, x = cc.read_wav(PREV / f"_bed{lap + 1}.wav")
    for suf in (".wav", ".ogg", "_x2.wav"):
        p = PREV / f"_bed{lap + 1}{suf}"
        if p.exists():
            p.unlink()
    n = len(x)
    # 留声机处理做在三遍连放上，取中间一遍：滤波与混响在接缝处是连续的
    rec = cc.gramophone(np.concatenate([x, x, x]), SR, seed=11 + lap)[n:2 * n]
    return rec[:, 0]


def render_shots():
    """脚步音样：鼓（左、右）与钢琴（四种 × 是否升半音）。返回 {名称: 单声道数组}。"""
    t_d = lat.Track("鼓", 9, 32, swing=False)
    t_p = lat.Track("钢琴", 0, 0, swing=False)
    t_d.cc(0, 7, 120)
    t_p.cc(0, 7, 112)
    for t in (t_d, t_p):
        t.cc(0, 91, 26)
    names = []

    def slot():
        return len(names) * 4  # 120 BPM：4 拍 = 2 秒

    t_d.note(slot(), 0.3, 41, 74, jitter=False)          # 左脚：落地鼓，闷
    names.append("drum_l")
    t_d.note(slot(), 0.3, 37, 70, jitter=False)          # 右脚：鼓边，“嗒”
    names.append("drum_r")
    for up in (0, 1):
        for name, notes in (("root", [38, 45]), ("fifth", [45]), ("quartal", cc.QUARTAL), ("answer", cc.ANSWER)):
            for j, p in enumerate(notes):
                t_p.note(slot() + j * 0.01, 0.5, p - (0 if name in ("root", "fifth") else 12) + up, 50, jitter=False)
            names.append(name + ("_up" if up else ""))
    t_p.cc(slot() + 2, 110, 0)
    lat.BPM = BPM
    mid, raw = PREV / "_shots.mid", PREV / "_shots.wav"
    lat.write_midi([t_d, t_p], mid)
    subprocess.run(["fluidsynth", "-ni", "-g", "0.7", "-r", str(SR), "-F", str(raw), str(lat.SF2), str(mid)],
                   check=True, capture_output=True)
    _, x = cc.read_wav(raw)
    mid.unlink()
    raw.unlink()
    out = {}
    for i, name in enumerate(names):
        seg = x[i * 2 * SR:(i * 2 + 2) * SR].mean(axis=1)
        a = np.abs(seg)
        last = np.nonzero(a > 1e-3 * max(a.max(), 1e-9))[0]
        seg = seg[: (last[-1] + int(0.02 * SR)) if len(last) else SR].copy()
        seg[-int(0.02 * SR):] *= np.linspace(1, 0, int(0.02 * SR))
        # 脚步是玩家的，不在唱片上：只轻轻收窄一点频带，不加炸豆声
        m = 1 << int(np.ceil(np.log2(len(seg) + 1)))
        f = np.fft.rfftfreq(m, 1 / SR)
        seg = np.fft.irfft(np.fft.rfft(seg, m) / (1 + (f / 6000) ** 4) / (1 + (90 / np.maximum(f, 1)) ** 2), m)[: len(seg)]
        out[name] = (seg / max(np.abs(seg).max(), 1e-9) * 0.89).astype(np.float32)
    return out


def reverse_shot(s, keep=0.35):
    r = s[: int(keep * SR)][::-1].copy()
    f = int(0.03 * SR)
    r[:f] *= np.linspace(0, 1, f)
    return r


def step_sounds(k, lap):
    """第 k 步（这一圈从 0 数）要响的音样名。"""
    up = "_up" if lap == 2 else ""
    names = ["drum_l" if k % 2 == 0 else "drum_r"]
    if lap <= 3:
        p = PIANO_PAT[k % len(PIANO_PAT)]
        if p:
            names.append(p + up)
    return names


MOVES = [(3.0, 1.4), (1.6, 0.0), (1.5, 0.7), (2.0, 1.9), (1.2, 0.0), (2.0, -1.1), (0.8, 0.0),
         (5.5, 1.4), (4.0, 1.4), (1.0, 0.0), (3.0, 1.4)]


def load_voice(lap):
    raw = PREV / "_voice.wav"
    subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-i", str(VOICE / f"corridor_l{lap + 1}.ogg"),
                    "-ac", "1", "-ar", str(SR), str(raw)], check=True)
    _, x = cc.read_wav(raw) if False else (None, None)
    import wave
    with wave.open(str(raw)) as w:
        x = np.frombuffer(w.readframes(w.getnframes()), dtype=np.int16).astype(np.float32) / 32768
    raw.unlink()
    return x


def smooth_gate(g, sec):
    k = np.exp(-np.arange(int(sec * SR)) / (sec / 3 * SR))
    return np.convolve(g, k / k.sum())[: len(g)]


def simulate(beds, shots):
    ctl = 200
    v = np.concatenate([np.full(int(d * ctl), s) for d, s in MOVES])
    k = np.exp(-np.arange(int(0.12 * ctl)) / (0.04 * ctl))
    v = np.convolve(v, k / k.sum())[: len(v)]
    pos = np.cumsum(v) / ctl
    lap = np.zeros(len(pos), int)
    p_lap = pos.copy()
    over = pos >= SEG_LEN[0] - 0.35
    if over.any():
        i0 = int(np.argmax(over))
        lap[i0:] = 1
        p_lap[i0:] = pos[i0:] - pos[i0] + 0.15
    n = int(len(pos) / ctl * SR)
    tc = np.arange(len(pos)) / ctl
    ta = np.arange(n) / SR
    pa = np.interp(ta, tc, p_lap)
    la = np.interp(ta, tc, lap).round().astype(int)
    va = np.interp(ta, tc, v)

    # 底色：按时间走，往回走时倒着读；停下时压低 5 dB、削掉高频
    back = va < -0.12
    direction = np.where(back, -1.0, 1.0)
    bpos = np.cumsum(direction) % (LOOP_SEC * SR)
    bed = np.zeros(n)
    for L in np.unique(la):
        sel = la == L
        src = beds[L]
        bed[sel] = np.interp(bpos[sel], np.arange(len(src)), src)
    moving = (np.abs(va) > 0.12).astype(float)
    duck = smooth_gate(0.56 + 0.44 * moving, 0.25)
    bed *= duck

    # 唱片人声：跟着唱针（位置），停下淡出
    voice = np.zeros(n)
    for L in np.unique(la):
        sel = la == L
        vx = load_voice(L)
        src = np.clip(pa[sel] / SEG_LEN[L], 0, 1) * (len(vx) - 1)
        voice[sel] = np.interp(src, np.arange(len(vx)), vx)
    voice *= smooth_gate(moving, 0.06)

    # 脚步：越过 0.7 m 的格子 → 等到下一个十六分音符再响；往回走用倒放
    steps = np.zeros(n)
    cell = np.floor(p_lap / STEP).astype(int)
    hits = 0
    for i in range(1, len(cell)):
        if cell[i] == cell[i - 1] or lap[i] != lap[i - 1]:
            continue
        fwd = cell[i] > cell[i - 1]
        kstep = cell[i] if fwd else cell[i - 1]
        t_hit = np.ceil((i / ctl) / GRID - 1e-6) * GRID
        at = int(t_hit * SR)
        for name in step_sounds(kstep, lap[i]):
            s = shots[name] if fwd else reverse_shot(shots[name])
            e = min(n, at + len(s))
            if at < n:
                steps[at:e] += s[: e - at] * (0.8 if name.startswith("drum") else 0.55)
        hits += 1

    rms = lambda x: float(np.sqrt((x[np.abs(x) > 1e-4] ** 2).mean())) if (np.abs(x) > 1e-4).any() else 1.0
    bed *= 0.30 / rms(bed)
    voice *= 0.22 / rms(voice)
    steps *= 0.30 / rms(steps)
    mix = bed + voice + steps
    mix *= 0.89 / np.abs(mix).max()
    return np.stack([mix, mix], axis=1).astype(np.float32), hits, (bed, voice, steps, moving, back)


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--game", action="store_true")
    args = ap.parse_args()
    lat.SWING = 0.08
    beds = [render_bed(L) for L in range(5)]
    shots = render_shots()
    out, hits, _ = simulate(beds, shots)
    cc.write(out, SR, PREV / "corridor_reactive")
    (PREV / "corridor_reactive.wav").unlink()
    print(f"试听 {len(out) / SR:.1f} 秒 → preview/corridor_reactive.ogg（脚步 {hits} 下）")
    if args.game:
        for L, bed in enumerate(beds):
            st = np.stack([bed, bed], axis=1)
            cc.write(st, SR, GAME / f"corridor_bed{L + 1}")
            cc.write(st[::-1].copy(), SR, GAME / f"corridor_bed{L + 1}_rev")
            (GAME / f"corridor_bed{L + 1}.wav").unlink()
            (GAME / f"corridor_bed{L + 1}_rev.wav").unlink()
        d = GAME / "steps"
        d.mkdir(parents=True, exist_ok=True)
        for name, s in shots.items():
            st = np.stack([s, s], axis=1)
            r = reverse_shot(s)
            cc.write(st, SR, d / name)
            cc.write(np.stack([r, r], axis=1), SR, d / f"{name}_rev")
            (d / f"{name}.wav").unlink()
            (d / f"{name}_rev.wav").unlink()
        print("底色循环 →", GAME, "；脚步音样 →", d)
