"""回廊的唱片（第 5 章演绎“回廊”）：降灵会里放出来的一张唱片，玩家是唱针。

10-20 起游戏里改用响应式音乐（corridor_reactive.py：底色循环 + 按步触发的鼓与钢琴）。
本脚本保留作整张唱片的连放试听，以及第 6 圈的结尾 corridor_ending（--game 只导出它）。

    python3 assets/audio/music/scripts/compose_corridor.py           # 写 MIDI + 渲染试听
    python3 assets/audio/music/scripts/compose_corridor.py --game    # 另把每圈的切片（正放 + 倒放）放进 godot/audio/music/

方向（用户 10-20）：喜欢 Miles Davis《So What》那种调式爵士的调子，但不照抄；
小号加弱音器；爵士不要太松弛，太松弛会破坏氛围。10-17 被否的“紧绷的小调悬疑爵士”也不要。
所以：比《潜影》直、往前推，但力度一直很轻，不靠加速和不协和音块制造紧张。

  调式  D 多利亚，没有和弦进行、不“回家”，能一直转下去；第 3 圈整体升高半音（降 E 多利亚），
        同一首曲子转回来就不对了
  拍速  120 BPM = 正常步速每分钟 120 步（1.4 m/s、一步 0.7 m）。低音提琴一拍一个音，落在玩家的步子上
  摇摆  0.08（《潜影》的一半），镲片每拍一下，像钟在走
  乐器  低音提琴（走路）、爵士套鼓（叮叮镲 + 踩镲，不用鼓刷）、钢琴（四度叠置的两个和弦，回答低音提琴）、
        加弱音器的小号。不用八音盒、颤音琴、钢片琴
  唱片  整段做成 1920 年代声学录音：单声道、窄频、号筒共鸣、轻微变速、炸豆声与底噪

唱片越放越靠里，每圈放下一段（切片长度 = 这一圈路径长 ÷ 1.4 m/s，所以正常步速时正好放完）：
  第 1 圈  只有低音提琴走路、镲片和钢琴的回答
  第 2 圈  一记镲片，小号进来，零星几句；第一句就是《潜影》的动机（3、5、7、6 级），停在多利亚的 6 级上
  第 3 圈  整体升高半音；小号重复上一句，最后一个长音往下走调
  第 4 圈  小号走了，只剩低音提琴（那个人）；最后一小节低音提琴停在半句
  第 5 圈  只剩钢琴那两个和弦，走了音，像从墙后传来
  结尾    小号独自吹《潜影》动机的开头三个音，在第四个音之前断掉（完整的旋律留给第 6 章“显影”）
"""

import argparse
import subprocess
import sys
import wave
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).parent))
import compose_latent_image as lat  # noqa: E402

ROOT = Path(__file__).resolve().parents[1]
GAME = ROOT.parents[2] / "godot" / "audio" / "music"
BPM = 120
SPEED = 1.4
SEG_A = 8.0
SEG_B = [6, 5, 4, 3, 2]            # 每圈第二段的长度（与 content/story/corridor.csv 的 seg_b 一致）
LAP_SEC = [(SEG_A + s) / SPEED for s in SEG_B]
LAP_BEAT = [sum(LAP_SEC[:i]) * BPM / 60 for i in range(6)]  # 每圈从第几拍开始


def lap_of(beat):
    for i in range(5):
        if beat < LAP_BEAT[i + 1]:
            return i
    return 5


# D 多利亚：D E F G A B C；第 3 圈整体 +1
def shift(beat):
    return 1 if lap_of(beat) == 2 else 0


WALK = [  # 低音提琴每小节四个音（相对 D2=38 的半音数），最后一拍是进入下一小节的经过音
    [0, 3, 7, 11], [12, 10, 9, 5], [0, 2, 3, 7], [9, 10, 9, -1],
    [0, 7, 5, 3], [2, 3, 5, 6], [7, 9, 10, 9], [7, 5, 3, 1],
]
QUARTAL = [52, 57, 62, 67, 72]      # E A D G C：全部四度叠置
ANSWER = [50, 55, 60, 65, 71]       # 往下一个全音：D G C F B（F 与 B 相差三全音，轻轻地擦）


def compose():
    bass = lat.Track("低音提琴", 0, 32)
    drums = lat.Track("套鼓", 9, 32)
    piano = lat.Track("钢琴", 1, 0)
    horn = lat.Track("弱音小号", 2, 59)
    for t, pan, vol in ((bass, 64, 96), (drums, 64, 110), (piano, 50, 82), (horn, 72, 122)):
        t.cc(0, 10, pan)
        t.cc(0, 7, vol)
        t.cc(0, 91, 34)

    total = LAP_BEAT[5]
    bars = int(np.ceil(total / 4))
    stop_bass = LAP_BEAT[4] - 2.0     # 第 4 圈最后：低音提琴停在半句

    for b in range(bars):
        o = b * 4
        line = WALK[b % len(WALK)]
        for k, rel in enumerate(line):
            beat = o + k
            lap = lap_of(beat)
            if beat >= total or beat >= stop_bass or lap >= 4:
                continue
            vel = 74 if lap < 3 else 84  # 第 4 圈只剩他，走得更清楚
            bass.note(beat, 0.92, 38 + rel + shift(beat), vel + (6 if k == 0 else 0))

        for k in range(4):  # 叮叮镲每拍一下（像钟），2、4 拍踩镲；第 1 小节先不进
            beat = o + k
            lap = lap_of(beat)
            if b == 0 or beat >= total or lap >= 4:
                continue
            drums.note(beat, 0.25, 51, 50 if k % 2 == 0 else 44, jitter=False)
            if k in (1, 3):
                drums.note(beat, 0.2, 44, 46, jitter=False)

        if b % 2 == 1:  # 钢琴每两小节回答一次：4 拍反拍一个和弦，下一小节第 1 拍往下一个全音
            for beat, chord, vel in ((o + 3.5, QUARTAL, 44), (o + 4, ANSWER, 38)):
                lap = lap_of(beat)
                if beat >= total:
                    continue
                if lap < 4:  # 前四圈的钢琴改由“按步触发”的节奏层弹（10-20 方案 A），唱片里只在第 5 圈留下
                    continue
                v = vel + (4 if lap == 4 else 0)
                for j, p in enumerate(chord):
                    piano.note(beat + j * 0.012, 0.8, p + shift(beat), v)

    # 第 5 圈：钢琴整体走音（往下约 30 音分）
    piano.bend(LAP_BEAT[4] - 0.2, -1230)

    drums.note(LAP_BEAT[1], 1.5, 49, 58, jitter=False)  # 第 2 圈：一记镲片，小号进来

    # 弱音小号（拍数相对第 2 圈开头）。动机 = 《潜影》的 3、5、7、6 级 → D 小调里是 F A C B（B 是多利亚的 6 级）
    s2 = LAP_BEAT[1]
    phrases = [
        (1.5, 0.5, 65, 70), (2.0, 0.5, 69, 74), (2.5, 1.5, 72, 80), (4.0, 2.5, 71, 72),
        (9.0, 0.5, 74, 74), (9.5, 0.5, 72, 70), (10.0, 1.0, 69, 76), (11.0, 0.5, 67, 66), (11.5, 2.0, 65, 68),
        (15.0, 0.5, 64, 60), (15.5, 0.5, 65, 64), (16.0, 2.0, 69, 62),
    ]
    for beat, dur, p, v in phrases:
        horn.note(s2 + beat, dur, p, v + 10)
    s3 = LAP_BEAT[2]  # 第 3 圈：升高半音重复第一句，最后的长音往下走调
    for beat, dur, p, v in phrases[:4]:
        horn.note(s3 + beat, dur + (2.0 if beat == 4.0 else 0), p + 1, v - 6)
    for i in range(1, 9):
        horn.bend(s3 + 4.6 + i * 0.35, -int(2400 * i / 8))
    horn.bend(LAP_BEAT[3] - 0.1, 0)
    horn.cc(total + 4, 110, 0)  # 留 4 拍空事件，混响尾巴不被截断
    return [bass, drums, piano, horn]


def compose_ending():
    horn = lat.Track("弱音小号", 2, 59)
    horn.cc(0, 7, 104)
    horn.cc(0, 91, 70)
    for beat, dur, p, v in ((0.5, 0.5, 65, 66), (1.0, 0.5, 69, 70), (1.5, 2.2, 72, 76)):  # F A C……不到 B
        horn.note(beat, dur, p, v)
    horn.cc(8, 110, 0)
    return [horn]


# ---------- 1920 年代声学录音 ----------
def gramophone(x, sr, seed=1926):
    rng = np.random.default_rng(seed)
    mono = x.mean(axis=1).astype(np.float64)
    n = len(mono)
    # 轻微变速（78 转唱片偏心）：0.55 Hz、约 ±0.25%
    t = np.arange(n) / sr
    drift = 0.0025 * np.sin(2 * np.pi * 0.55 * t) + 0.0008 * np.sin(2 * np.pi * 1.3 * t + 1.0)
    pos = np.cumsum(1 + drift) - 1
    mono = np.interp(np.clip(pos, 0, n - 1), np.arange(n), mono)
    # 窄频 + 号筒共鸣（FFT 域）
    m = 1 << int(np.ceil(np.log2(n)))
    f = np.fft.rfftfreq(m, 1 / sr)
    hp = 1 / (1 + (280 / np.maximum(f, 1)) ** 4)
    lp = 1 / (1 + (f / 3000) ** 6)
    horn_res = 1 + 0.9 * np.exp(-((np.log2(np.maximum(f, 1) / 1150)) ** 2) / 0.18)
    mono = np.fft.irfft(np.fft.rfft(mono, m) * hp * lp * horn_res, m)[:n]
    mono /= max(np.abs(mono).max(), 1e-9)
    mono = np.tanh(1.7 * mono) / np.tanh(1.7)
    # 底噪：带限的沙沙声 + 炸豆声 + 每转一圈的轻微“噗”
    hiss = rng.standard_normal(n)
    hiss = np.fft.irfft(np.fft.rfft(hiss, m) * (1 / (1 + (f / 2600) ** 4)) * (1 / (1 + (500 / np.maximum(f, 1)) ** 2)), m)[:n]
    hiss *= 0.035 / max(np.sqrt((hiss ** 2).mean()), 1e-9)
    crackle = np.zeros(n)
    for i in rng.choice(n, size=int(n / sr * 7), replace=False):
        L = int(rng.uniform(0.0004, 0.002) * sr)
        crackle[i:i + L] += rng.uniform(0.08, 0.35) * rng.choice([-1, 1]) * np.exp(-np.arange(min(L, n - i)) / (L / 4))
    thump = 0.012 * np.sin(2 * np.pi * 1.3 * t) ** 16
    out = mono * 0.82 + hiss + crackle + thump
    out /= max(np.abs(out).max(), 1e-9)
    return (np.stack([out, out], axis=1) * 0.89).astype(np.float32)


def read_wav(path):
    with wave.open(str(path)) as w:
        sr, n = w.getframerate(), w.getnframes()
        return sr, np.frombuffer(w.readframes(n), dtype=np.int16).reshape(-1, 2).astype(np.float32) / 32768


def write(arr, sr, stem):
    pcm = (np.clip(arr, -1, 1) * 32767).astype(np.int16)
    with wave.open(str(stem.with_suffix(".wav")), "wb") as w:
        w.setnchannels(2), w.setsampwidth(2), w.setframerate(sr)
        w.writeframes(pcm.tobytes())
    subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-i", str(stem.with_suffix(".wav")),
                    "-c:a", "vorbis", "-strict", "-2", "-ac", "2", "-b:a", "160k", str(stem.with_suffix(".ogg"))],
                   check=True)


def render_record(tracks, name, prev):
    lat.NAME, lat.BPM = name, BPM
    lat.render(tracks, prev, loop=False)       # 干净的乐队混音：preview/<name>.wav
    sr, clean = read_wav(prev / f"{name}.wav")
    rec = gramophone(clean, sr)
    write(rec, sr, prev / f"{name}_78")
    return sr, rec


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--game", action="store_true", help="把每圈切片放进 godot/audio/music/")
    args = ap.parse_args()
    lat.SWING = 0.08
    prev = ROOT / "preview"
    prev.mkdir(exist_ok=True)

    tracks = compose()
    lat.BPM = BPM
    lat.write_midi(tracks, ROOT / "midi" / "corridor_record.mid")
    sr, rec = render_record(tracks, "corridor_record", prev)
    ending = compose_ending()
    lat.write_midi(ending, ROOT / "midi" / "corridor_ending.mid")
    sr_e, rec_e = render_record(ending, "corridor_ending", prev)
    print("每圈切片（秒）：", " | ".join(f"{a:.2f}–{b:.2f}" for a, b in zip(np.cumsum([0] + LAP_SEC[:-1]), np.cumsum(LAP_SEC))))

    if args.game:
        # 10-20 起回廊改用响应式音乐（corridor_reactive.py）：整张唱片按圈切片的做法作废，这里只导出结尾
        GAME.mkdir(parents=True, exist_ok=True)
        write(rec_e, sr_e, GAME / "corridor_ending")
        (GAME / "corridor_ending.wav").unlink()
        print("已放进", GAME)
