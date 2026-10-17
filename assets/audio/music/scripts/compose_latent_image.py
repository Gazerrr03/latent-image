"""《潜影》（Latent Image）：探索曲。日常的松弛爵士，里面藏着几处不对劲。

曲名取自摄影术语“潜影”：底片已经曝光、影像已经在上面，但还没显影，看不见。

生成多轨 MIDI（可直接拖进库乐队，每件乐器一条轨），并可选用 FluidSynth 渲染成无缝循环。

    python3 assets/audio/music/scripts/compose_latent_image.py            # 只写 MIDI
    python3 assets/audio/music/scripts/compose_latent_image.py --render   # 另渲染 wav/ogg

音色：乐队（低音提琴、套鼓、钢琴）用 FluidSynth 渲染；两条合成器轨由本脚本直接算波形——
  旋律    模拟合成器：两条略微走调的锯齿波，削掉高频，慢起音、长收尾
  固定音型 特雷门琴（1920 年发明）式：正弦为主，音与音之间滑过去，带颤音，低音区
不用八音盒、颤音琴、钢片琴一类“敲铃”的音色（用户 10-17：太像儿童游戏），也不用鼓刷（“沙子”声）。

方向（用户 10-17）：像《宝可梦》紫苑镇那样靠一段简单、重复、略微走调的旋律让人发毛，
但更轻；不靠紧张和起伏，而是“看起来很日常，其实有很多怪异现象”。爵士负责松弛感。

C 大调，84 BPM（用户 10-17：104 太快、显得欢快），摇摆八分，16 小节一个循环（约 45.7 秒）。
和声是最日常的 I–vi–ii–V（Cmaj7–Am7–Dm7–G7），中段转 Em7–A7。
  1—4   合成器的固定音型 + 低音提琴二分音符 + 轻轻的叮叮镲
  5—16  加钢琴（查尔斯顿节奏）和合成器旋律
怪异之处（都很小，玩家未必说得出哪里不对）：
  a. 合成器的音型永远不变，也不随和弦走，两小节一轮、每拍一个音，不跟着乐队摇摆
  b. 音型里有一个升 F：在 C 大调里它是爵士常用的 ♯11，听着合理；碰到 Dm7、G7 时就和 F 相擦
  c. 第 11 小节后两拍乐队整体消失，只剩合成器照常走
  d. 第 12 小节旋律停在升 F 上，不回主音
  e. 第 14 小节合成器漏掉一个音
  f. 第 15 小节合成器旋律的长音慢慢往下走调
"""

import argparse
import random
import struct
import subprocess
import wave
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
NAME = "latent_image"
BPM = 84
TPB = 480  # 每拍 tick 数
BARS = 16
SWING = 0.17  # 反拍八分往后推的拍数（0.5 → 0.67，三连音式摇摆）
SF2 = Path.home() / ".local/share/soundfonts/GeneralUser-GS.sf2"

rng = random.Random(1926)

# ---------- 和声 ----------
PROG = ["C", "Am", "Dm", "G", "C", "Am", "Dm", "G", "Em", "A", "Dm", "G", "C", "Am", "Dm", "G"]
ROOT_NOTE = {"C": 36, "Am": 33, "Dm": 38, "G": 31, "Em": 40, "A": 33}
FIFTH = {k: v + 7 for k, v in ROOT_NOTE.items()}
VOICING = {  # 钢琴无根音位，柔和
    "C": [64, 67, 71, 74],   # Cmaj9：E G B D
    "Am": [60, 64, 67, 71],  # Am9：C E G B
    "Dm": [60, 64, 65, 69],  # Dm9：C E F A
    "G": [59, 64, 65, 69],   # G13：B E F A
    "Em": [62, 66, 67, 71],  # Em9：D F♯ G B
    "A": [61, 66, 67, 71],   # A13：C♯ F♯ G B
}
DROPOUT = (10, 2)  # 第 11 小节第 3 拍起乐队消失


class Track:
    def __init__(self, name, ch, program, swing=True, synth=""):  # synth：本脚本合成的音色名
        self.name, self.ch, self.swing, self.synth = name, ch, swing, synth
        self.events = [(0, 0, bytes([0xC0 | ch, program]))]

    def _t(self, beat):
        if self.swing and abs(beat % 1 - 0.5) < 1e-6:
            beat += SWING
        return int(beat * TPB)

    def note(self, beat, dur, pitch, vel, jitter=True):
        t = max(self._t(beat) + (rng.randint(-6, 6) if jitter else 0), 0)
        v = max(1, min(127, vel + rng.randint(-5, 5)))
        self.events.append((t, 2, bytes([0x90 | self.ch, pitch, v])))
        self.events.append((t + max(int(dur * TPB) - 10, 20), 1, bytes([0x80 | self.ch, pitch, 0])))

    def cc(self, beat, num, val):
        self.events.append((int(beat * TPB), 0, bytes([0xB0 | self.ch, num, val])))

    def bend(self, beat, value):  # value：-8192..8191，默认弯音范围 ±2 半音
        v = value + 8192
        self.events.append((int(beat * TPB), 0, bytes([0xE0 | self.ch, v & 0x7F, v >> 7])))


def bar(b):
    return b * 4


def silenced(b, beat):
    return b == DROPOUT[0] and beat >= DROPOUT[1]


def compose():
    bass = Track("低音提琴", 0, 32)
    drums = Track("套鼓", 9, 32)  # GS 鼓组 32 = Jazz
    piano = Track("钢琴", 1, 0)
    # v6（用户 10-17）：颤音琴和高音区的特雷门琴都像八音盒，太像儿童游戏。
    # 旋律改由模拟合成器“唱”（慢起音、长收尾），特雷门琴降一个八度、去掉起音重音。
    # 两条合成器轨在 MIDI 里挂 GM 音色占位，库乐队里换成自己的合成器；试听版由本脚本合成
    vibes = Track("合成器旋律", 3, 81, synth="analog")  # 沿用变量名 vibes，旋律与弯音都在这条轨上
    lead = Track("特雷门琴", 4, 80, swing=False, synth="theremin")

    for t, pan, vol in ((bass, 64, 72), (drums, 64, 127), (piano, 46, 84),
                        (vibes, 84, 110), (lead, 70, 112)):
        t.cc(0, 10, pan)
        t.cc(0, 7, vol)
        t.cc(0, 91, 50)

    for b, ch in enumerate(PROG):
        o = bar(b)
        nxt = PROG[(b + 1) % BARS]
        # 低音提琴：二分音符的“两拍子”，松，不走步；偶尔在 4 拍反拍带一个半音进入下一小节
        for beat, dur, p, v in ((0, 1.9, ROOT_NOTE[ch], 80), (2, 1.4, FIFTH[ch] - 12, 70)):
            if not silenced(b, beat):
                bass.note(o + beat, dur, p, v)
        if b % 2 == 1 and not silenced(b, 3.5):
            bass.note(o + 3.5, 0.45, ROOT_NOTE[nxt] + 1, 56)

        # 套鼓：叮叮镲（1、2、2&、3、4、4&），2、4 拍踩镲，4 拍轻轻边击
        for beat, v in ((0, 74), (1, 66), (1.5, 52), (2, 72), (3, 66), (3.5, 52)):
            if not silenced(b, beat):
                drums.note(o + beat, 0.3, 51, v, jitter=False)
        for beat in (1, 3):
            if not silenced(b, beat):
                drums.note(o + beat, 0.2, 44, 58, jitter=False)
        if b >= 4 and not silenced(b, 3):
            drums.note(o + 3, 0.2, 37, 54, jitter=False)

        # 钢琴：5 小节起，查尔斯顿节奏（1 拍、2 拍反拍）
        if b >= 4:
            for beat, dur, v in ((0, 1.2, 46), (1.5, 0.9, 40)):
                if not silenced(b, beat):
                    for k, p in enumerate(VOICING[ch]):
                        piano.note(o + beat + k * 0.015, dur, p, v)

        # 合成器：同一个音型从头到尾不变，不随和弦。
        # v5（用户 10-17：音型太密）：八个音从一小节拉宽到两小节，每拍一个音，连着滑过去
        pattern = [64, 59, 55, 59, 64, 59, 54, 59]  # E B G B E B F♯ B（v6 降一个八度）
        if b % 2 == 0:
            for k, p in enumerate(pattern):
                if b == 12 and k == 6:  # e. 第 14 小节漏掉一个音
                    continue
                lead.note(o + k, 0.95, p, 52 if k % 2 else 60, jitter=False)

    # 合成器旋律（小节从 0 计）
    melody = [
        (4, 1, 0.5, 76), (4, 1.5, 0.5, 79), (4, 2, 1.5, 83), (4, 3.5, 0.5, 81),
        (5, 0, 2, 79), (5, 2, 0.5, 76), (5, 2.5, 1.5, 72),
        (6, 0.5, 0.5, 77), (6, 1, 0.5, 81), (6, 1.5, 0.5, 84), (6, 2, 2, 83),
        (7, 0, 1, 81), (7, 1, 2.5, 79),
        (8, 1, 0.5, 79), (8, 1.5, 0.5, 83), (8, 2, 1.5, 86), (8, 3.5, 0.5, 85),
        (9, 0, 2, 85), (9, 2, 1, 83), (9, 3, 1, 81),
        (10, 0, 1, 77), (10, 1, 1, 81),            # 第 3 拍起乐队消失，旋律也断
        (11, 0.5, 0.5, 76), (11, 1, 0.5, 79), (11, 1.5, 2.5, 78),  # d. 停在升 F 上
        (13, 2, 0.5, 81), (13, 2.5, 0.5, 79), (13, 3, 1, 77),
        (14, 0, 4, 76),                            # f. 这个长音会慢慢走调
    ]
    for b, beat, dur, p in melody:
        vibes.note(bar(b) + beat, dur, p - 12, 72)  # v6 降一个八度
    for i in range(1, 9):  # f. 半拍一步，往下弯约 40 音分
        vibes.bend(bar(14) + 0.5 + i * 0.4, -int(1640 * i / 8))
    vibes.bend(bar(15) + 3.9, 0)

    # 循环结束后再留 4 拍空事件，保证渲染时混响尾巴不被截断
    vibes.cc(bar(BARS) + 4, 110, 0)
    return [bass, drums, piano, vibes, lead]


# ---------- 写 MIDI（Type 1） ----------
def vlq(n):
    out = [n & 0x7F]
    n >>= 7
    while n:
        out.append(0x80 | (n & 0x7F))
        n >>= 7
    return bytes(reversed(out))


def chunk(events):
    data, last = b"", 0
    for t, _, ev in sorted(events, key=lambda e: (e[0], e[1])):
        data += vlq(t - last) + ev
        last = t
    data += b"\x00\xff\x2f\x00"
    return b"MTrk" + struct.pack(">I", len(data)) + data


def meta_name(name):
    raw = name.encode("utf-8")
    return (0, -1, b"\xff\x03" + vlq(len(raw)) + raw)


def write_midi(tracks, path):
    us = int(60_000_000 / BPM)
    tempo = [
        meta_name(NAME),
        (0, 0, b"\xff\x51\x03" + us.to_bytes(3, "big")),
        (0, 0, b"\xff\x58\x04\x04\x02\x18\x08"),
    ]
    body = chunk(tempo) + b"".join(chunk([meta_name(t.name)] + t.events) for t in tracks)
    head = b"MThd" + struct.pack(">IHHH", 6, 1, len(tracks) + 1, TPB)
    path.write_bytes(head + body)


# ---------- 小合成器 ----------
def synth_notes(track):
    """把合成器轨的事件换算成音符 (起, 止, 音高, 力度) 与弯音 (时刻, 半音)，单位秒。"""
    sec = 60 / BPM / TPB
    on, notes, bends = {}, [], []
    for t, _, ev in sorted(track.events, key=lambda e: (e[0], e[1])):
        kind = ev[0] & 0xF0
        if kind == 0x90:
            on[ev[1]] = (t, ev[2])
        elif kind == 0x80 and ev[1] in on:
            t0, v = on.pop(ev[1])
            notes.append((t0 * sec, t * sec, ev[1], v))
        elif kind == 0xE0:
            bends.append((t * sec, ((ev[2] << 7 | ev[1]) - 8192) / 8192 * 2))
    return notes, bends


def synth(notes, bends, n, sr, voice):
    import numpy as np

    out = np.zeros((n, 2), np.float32)
    hz = lambda p: 440 * 2 ** ((p - 69) / 12)
    if voice in ("analog", "pad"):
        # 两条略微走调的锯齿波，削掉高频；慢起音、长收尾，像在“唱”而不是“敲”
        bt = np.array([b[0] for b in bends] or [0.0])
        bv = np.array([b[1] for b in bends] or [0.0])
        for t0, t1, p, v in notes:
            a, b = int(t0 * sr), min(int((t1 + 0.4) * sr), n)
            t = np.arange(b - a) / sr
            dur = t1 - t0
            env = np.minimum(t / 0.07, 1) * (0.82 + 0.18 * np.exp(-t / 0.3))
            env *= np.clip((dur + 0.4 - t) / 0.4, 0, 1) ** 2
            k_ = np.clip(np.searchsorted(bt, t0 + t, side="right") - 1, 0, None)
            semis = np.where(t0 + t >= bt[0], bv[k_], 0.0)
            vib = (7 / 1200) * np.sin(2 * np.pi * 4.6 * t) * np.clip((t - 0.35) / 0.5, 0, 1)
            f_inst = hz(p) * 2 ** (semis / 12 + vib)
            phase = 2 * np.pi * np.cumsum(f_inst) / sr
            for ch, cents in ((0, -6), (1, 6)):
                ph = phase * 2 ** (cents / 1200)
                wave_ = np.zeros_like(t)
                for k in range(1, int(5000 / hz(p)) + 1):
                    wave_ += np.sin(k * ph) / k / (1 + (k * hz(p) / 1100) ** 2)
                out[a:b, ch] += wave_ * env * v / 127
    else:  # theremin：一条连续的音高曲线，音与音之间滑过去，没有起音重音
        logf = np.full(n, np.nan, np.float32)
        amp = np.zeros(n, np.float32)
        for t0, t1, p, v in notes:
            a, b = int(t0 * sr), min(int(t1 * sr), n)
            logf[a:b] = np.log2(hz(p))
            amp[a:b] = np.maximum(amp[a:b], v / 127)
        idx = np.where(~np.isnan(logf), np.arange(n), 0)  # 空隙里保持上一个音高
        np.maximum.accumulate(idx, out=idx)
        logf = logf[idx]
        logf[np.isnan(logf)] = np.nanmean(logf)

        def smooth(x, tau):
            k = np.exp(-np.arange(int(tau * sr * 5)) / (tau * sr))
            k /= k.sum()
            m = len(x) + len(k)
            y = np.fft.irfft(np.fft.rfft(x - x[0], m) * np.fft.rfft(k, m), m)[: len(x)]
            return (y + x[0]).astype(np.float32)

        logf = smooth(logf, 0.06)  # 滑音
        amp = smooth(amp, 0.05)
        tt = np.arange(n) / sr
        logf += (18 / 1200) * np.sin(2 * np.pi * 5.0 * tt) * np.clip(amp * 1.5, 0, 1)  # 颤音
        phase = 2 * np.pi * np.cumsum(2 ** logf) / sr
        tone = np.sin(phase) + 0.25 * np.sin(2 * phase) + 0.08 * np.sin(3 * phase)
        out[:, 0] = out[:, 1] = tone * amp
    # 简单的混响：指数衰减的噪声做冲激响应，左右各一条
    rng_np = np.random.default_rng(7)
    L = int(1.6 * sr)
    m = n + L
    for ch in range(2):
        ir = rng_np.standard_normal(L) * np.exp(-np.arange(L) / (0.38 * sr))
        ir *= 0.22 / np.sqrt((ir ** 2).sum())
        wet = np.fft.irfft(np.fft.rfft(out[:, ch], m) * np.fft.rfft(ir, m), m)[:n]
        out[:, ch] += wet.astype(np.float32)
    return out


# ---------- 渲染与无缝循环 ----------
def render(tracks, out_dir, loop=True):
    """loop=False：只放一遍的曲子（冲洗、尾声），保留自然收尾，不叠回开头。
    没有乐队轨时只渲染合成器（尾声）。其他曲目 compose_cues.py 也复用这个函数。"""
    import numpy as np

    sr = 44100
    loop_n = round(BARS * 4 * 60 / BPM * sr)
    band_tracks = [t for t in tracks if not t.synth]
    if band_tracks:
        band_mid = out_dir / f"{NAME}_band.mid"
        raw = out_dir / f"{NAME}_raw.wav"
        write_midi(band_tracks, band_mid)
        subprocess.run(["fluidsynth", "-ni", "-g", "0.7", "-r", "44100", "-F", str(raw), str(SF2), str(band_mid)],
                       check=True, capture_output=True)
        with wave.open(str(raw)) as w:
            sr, n = w.getframerate(), w.getnframes()
            band = np.frombuffer(w.readframes(n), dtype=np.int16).reshape(-1, 2).astype(np.float32) / 32768
        raw.unlink()
        band_mid.unlink()
    else:
        n = loop_n + 6 * sr
        band = np.zeros((n, 2), np.float32)
    rms = lambda x: float(np.sqrt((x ** 2).mean()))
    ref = rms(band[:loop_n]) if band_tracks else 0.08  # 合成器按乐队电平对齐；没有乐队时用固定电平

    def save(arr, path):
        with wave.open(str(path), "wb") as w:
            w.setnchannels(2), w.setsampwidth(2), w.setframerate(sr)
            w.writeframes(arr.tobytes())

    # 合成器轨相对乐队（低音提琴、套鼓、钢琴）的音量：旋律最突出，特雷门琴垫在下面
    level = {"analog": 0.9, "theremin": 0.5, "pad": 0.45}
    mix = band.copy()
    for t in tracks:
        if t.synth:
            notes, bends = synth_notes(t)
            x = synth(notes, bends, n, sr, t.synth)
            # 按发声部分的电平对齐，避免长时间静默拉低平均
            active = np.abs(x[:loop_n]).max(axis=1) > 1e-3
            x *= level[t.synth] * ref / max(rms(x[:loop_n][active]), 1e-9)
            mix += x
    if loop:
        out = mix[:loop_n].copy()
        tail = mix[loop_n:]
        out[: len(tail)] += tail[: loop_n]  # 尾巴叠回开头，接缝处不断
    else:
        a = np.abs(mix).max(axis=1)
        last = np.nonzero(a > 1e-4 * a.max())[0][-1]
        out = mix[: last + int(0.05 * sr)].copy()
        out[-int(0.05 * sr):] *= np.linspace(1, 0, int(0.05 * sr))[:, None]
    out *= 0.89 / max(np.abs(out).max(), 1e-9)
    pcm = (out * 32767).astype(np.int16)
    stem = out_dir / NAME
    save(pcm, stem.with_suffix(".wav"))
    if loop:
        save(np.concatenate([pcm, pcm]), Path(f"{stem}_x2.wav"))  # 连放两遍，听接缝
    subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-i", str(stem.with_suffix(".wav")),
                    "-c:a", "vorbis", "-strict", "-2", "-ac", "2", "-b:a", "192k",
                    str(stem.with_suffix(".ogg"))], check=True)
    print(f"{'循环' if loop else '全长'} {len(out) / sr:.2f} 秒 → {stem}.ogg")


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--render", action="store_true")
    ap.add_argument("--bpm", type=int, help="换拍速试听，例如 --bpm 76")
    ap.add_argument("--name", help="输出文件名（默认 %s）" % NAME)
    args = ap.parse_args()
    if args.bpm:
        BPM = args.bpm
    if args.name:
        NAME = args.name
    mid_dir, prev_dir = ROOT / "midi", ROOT / "preview"
    mid_dir.mkdir(exist_ok=True)
    prev_dir.mkdir(exist_ok=True)
    mid = mid_dir / f"{NAME}.mid"
    tracks = compose()
    write_midi(tracks, mid)
    print(f"MIDI → {mid}")
    if args.render:
        render(tracks, prev_dir)
