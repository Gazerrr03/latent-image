"""《潜影》之外的几段配乐，与《潜影》同一套乐器、同一个母题。

    python3 assets/audio/music/scripts/compose_cues.py            # 全部
    python3 assets/audio/music/scripts/compose_cues.py think      # 只做一段

  think    推理：证据板连线时循环。只有低音提琴和特雷门琴，66 BPM，很空
  develop  显影：第 6 章亲手冲洗底片（只放一遍）。去掉鼓，《潜影》一直“潜”着的旋律
           第一次被慢慢、清楚地奏出来，最后停在升 F 上
  ending   尾声：十二块屏幕（只放一遍）。乐队全部消失，只剩合成器——1926 年的外壳脱落

合成器与渲染沿用 compose_latent_image.py。
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
import compose_latent_image as lat  # noqa: E402

ROOT = Path(__file__).resolve().parents[1]
PATTERN = [64, 59, 55, 59, 64, 59, 54, 59]  # 特雷门琴音型 E B G B E B F♯ B（与《潜影》相同）
# 《潜影》的旋律（小节从 0 计；音高已是合成器旋律实际的八度）
MELODY = [
    (4, 1, 0.5, 64), (4, 1.5, 0.5, 67), (4, 2, 1.5, 71), (4, 3.5, 0.5, 69),
    (5, 0, 2, 67), (5, 2, 0.5, 64), (5, 2.5, 1.5, 60),
    (6, 0.5, 0.5, 65), (6, 1, 0.5, 69), (6, 1.5, 0.5, 72), (6, 2, 2, 71),
    (7, 0, 1, 69), (7, 1, 2.5, 67),
    (8, 1, 0.5, 67), (8, 1.5, 0.5, 71), (8, 2, 1.5, 74), (8, 3.5, 0.5, 73),
    (9, 0, 2, 73), (9, 2, 1, 71), (9, 3, 1, 69),
    (10, 0, 1, 65), (10, 1, 1, 69),
    (11, 0.5, 0.5, 64), (11, 1, 0.5, 67), (11, 1.5, 2.5, 66),
]


def setup(name, bpm, bars):
    lat.NAME, lat.BPM, lat.BARS = name, bpm, bars


def theremin_track(bars, vel=56, fade_from=None):
    t = lat.Track("特雷门琴", 4, 80, swing=False, synth="theremin")
    for b in range(0, bars, 2):
        for k, p in enumerate(PATTERN):
            v = vel
            if fade_from is not None and b >= fade_from:
                v = max(12, int(vel * (1 - (b - fade_from + k / 8) / (bars - fade_from + 1))))
            t.note(lat.bar(b) + k, 0.95, p, v, jitter=False)
    return t


def bass_track(bars, prog):
    t = lat.Track("低音提琴", 0, 32)
    t.cc(0, 7, 70)
    t.cc(0, 91, 60)
    for b in range(bars):
        t.note(lat.bar(b), 3.8, lat.ROOT_NOTE[prog[b % len(prog)]], 74)
    return t


def piano_track(bars, prog, start, vel=40):
    t = lat.Track("钢琴", 1, 0)
    t.cc(0, 7, 80)
    t.cc(0, 91, 70)
    for b in range(start, bars):
        for k, p in enumerate(lat.VOICING[prog[b % len(prog)]]):
            t.note(lat.bar(b) + k * 0.04, 3.6, p, vel)  # 整小节的长和弦，不再是查尔斯顿节奏
    return t


def melody_track(offset, vel=74, name="合成器旋律"):
    t = lat.Track(name, 3, 81, synth="analog")
    for b, beat, dur, p in MELODY:
        t.note(lat.bar(b + offset) + beat, dur, p, vel)
    return t


def think():
    setup("think", 66, 8)
    tracks = [bass_track(8, lat.PROG[:8]), theremin_track(8)]
    tracks[0].cc(lat.bar(8) + 4, 110, 0)
    lat.render(tracks, ROOT / "preview", loop=True)
    return tracks


def develop():
    setup("develop", 72, 13)
    prog = lat.PROG[:12] + ["C"]
    mel = melody_track(0, 80)
    mel.note(lat.bar(12), 4, 66, 60)  # 最后一小节，升 F 再响一次，不回主音
    tracks = [bass_track(13, prog), piano_track(13, prog, 4), theremin_track(13, 50), mel]
    lat.render(tracks, ROOT / "preview", loop=False)
    return tracks


def ending():
    setup("ending", 76, 18)
    pad = lat.Track("合成器和弦", 5, 89, synth="pad")
    for b in range(4, 16):
        for p in lat.VOICING[lat.PROG[b % 16]]:
            pad.note(lat.bar(b), 3.9, p - 12, 40)
    tracks = [theremin_track(18, 56, fade_from=14), melody_track(0, 76), pad]
    lat.render(tracks, ROOT / "preview", loop=False)
    return tracks


CUES = {"think": think, "develop": develop, "ending": ending}

if __name__ == "__main__":
    for name in sys.argv[1:] or CUES:
        tracks = CUES[name]()
        lat.write_midi(tracks, ROOT / "midi" / f"{name}.mid")
