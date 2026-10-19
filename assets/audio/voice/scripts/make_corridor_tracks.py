#!/usr/bin/env python3
"""第 5 章回廊的六层录音：语声用 macOS 的 say 合成，加重留声机滤镜（窄带、底噪、轻度失真、黑胶噪声），
再与已有的音效（雨、钟、玻璃碎响、敲门、脚步、门闩）按时间线拼成每一层的 10 秒音轨；每层再生成一份倒放。

走廊按玩家的步速 1.4 m/s、路径 14 米设计，所以一层 = 14 / 1.4 = 10 秒。

    python3 assets/audio/voice/scripts/make_corridor_tracks.py

输出：godot/audio/voice/corridor_l1..l6[_rev].ogg，以及第 5 层的三个孤立声源 corridor_s1..s3.ogg。
"""

import subprocess
import tempfile
import wave
from pathlib import Path

import numpy as np

REPO = Path(__file__).resolve().parents[4]
OUT = REPO / "godot/audio/voice"
SFX = REPO / "godot/audio/sfx"
SR = 44100
LEN = 10.0  # 一层走完的时间

SAY = "/usr/bin/say"


def say_to_wav(text, voice, rate, path: Path, pitch=1.0):
    """只有 Tingting 这一个中文嗓音可用（其余几个在这台机器上只有 0.01 秒的空文件），
    男声靠降调区分：pitch < 1 变低变慢，再用 atempo 把语速拉回来。"""
    subprocess.run([SAY, "-v", voice, "-r", str(rate), "-o", str(path.with_suffix(".aiff")), text], check=True)
    af = "aresample=%d" % SR
    if abs(pitch - 1.0) > 0.01:
        af = "asetrate=%d,atempo=%f,aresample=%d" % (int(SR * pitch), 1.0 / pitch, SR)
    subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-i", str(path.with_suffix(".aiff")),
                    "-af", af, "-ar", str(SR), "-ac", "1", str(path)], check=True)


def load(path: Path) -> np.ndarray:
    with wave.open(str(path)) as w:
        data = np.frombuffer(w.readframes(w.getnframes()), dtype=np.int16).astype(np.float32) / 32768
        if w.getnchannels() == 2:
            data = data.reshape(-1, 2).mean(axis=1)
        if w.getframerate() != SR:
            raise SystemExit("采样率不对：" + str(path))
        return data


def phonograph(x: np.ndarray) -> np.ndarray:
    """留声机：窄带、轻微饱和、黑胶噪声、结尾一顿。"""
    n = len(x)
    # 一阶高通 + 一阶低通（近似 300—3400 Hz）
    x = np.concatenate([[0], np.diff(x)]) * 0.6 + x * 0.4
    k = int(SR / 3000)
    x = np.convolve(x, np.ones(k) / k, "same")
    x = np.tanh(x * 2.2) * 0.55
    rng = np.random.default_rng(7)
    crackle = np.zeros(n)
    for _ in range(int(n / SR * 9)):
        i = rng.integers(0, n)
        crackle[i] = rng.uniform(-0.35, 0.35)
    hiss = rng.normal(0, 0.006, n)
    x = x + crackle + hiss
    # 留声机放出来的声音有轻微的转速抖动
    wob = 1 + 0.004 * np.sin(2 * np.pi * 2.3 * np.arange(n) / SR)
    idx = np.clip(np.cumsum(wob), 0, n - 1).astype(int)
    return x[idx]


def at(buf: np.ndarray, x: np.ndarray, t: float, gain=1.0):
    i = int(t * SR)
    j = min(len(buf), i + len(x))
    if i < len(buf):
        buf[i:j] += x[: j - i] * gain


def place_sfx(buf, name, t, gain=1.0):
    p = SFX / (name + ".ogg")
    if not p.exists():
        print("  缺少音效", name)
        return
    with tempfile.NamedTemporaryFile(suffix=".wav") as f:
        subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-i", str(p), "-ar", str(SR), "-ac", "1", f.name], check=True)
        at(buf, load(Path(f.name)), t, gain)


def norm(x):
    m = np.abs(x).max()
    return x * (0.9 / m) if m > 0 else x


def write(name: str, x: np.ndarray):
    x = norm(x)
    tmp = OUT / (name + ".wav")
    with wave.open(str(tmp), "wb") as w:
        w.setnchannels(1)
        w.setsampwidth(2)
        w.setframerate(SR)
        w.writeframes((np.clip(x, -1, 1) * 32767).astype("<i2").tobytes())
    subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-i", str(tmp), "-c:a", "vorbis", "-strict", "-2", "-b:a", "128k", "-ac", "2",
                    str(OUT / (name + ".ogg"))], check=True)
    tmp.unlink()
    print("  ", name, "%.2f 秒" % (len(x) / SR))


def blank():
    return np.zeros(int(LEN * SR), dtype=np.float32)


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    tmpdir = Path(tempfile.mkdtemp())

    def voice(text, pitch=1.0, rate=180):
        p = tmpdir / ("v%s" % abs(hash(text)))
        say_to_wav(text, "Tingting", rate, p.with_suffix(".wav"), pitch)
        x = load(p.with_suffix(".wav"))
        if len(x) < 1000:
            print("  !! 合成失败：", text)
        return phonograph(x)

    # ── 第 1 层：雨声、钟声 ──
    b = blank()
    place_sfx(b, "rain_night", 0.0, 0.55)
    for i in range(9):
        place_sfx(b, "clock_tick", 0.6 + i * 1.05, 0.35)
    write("corridor_l1", b)

    # ── 第 2 层：玻璃碎响，然后敲门；门里回敲两下 ──
    b = blank()
    place_sfx(b, "room_hum", 0.0, 0.4)
    place_sfx(b, "glass_break", 4.2, 0.75)
    place_sfx(b, "door_knock", 5.4, 0.5)
    write("corridor_l2", b)

    # ── 第 3 层：门厅。主人两句，格雷一句（另一个嗓子） ──
    b = blank()
    place_sfx(b, "rain_night", 0.0, 0.25)
    place_sfx(b, "thunder_far", 0.9, 0.5)
    place_sfx(b, "cloth_rustle", 1.6, 0.4)
    at(b, voice("格雷。你来了。", 0.62), 1.9, 0.75)
    at(b, voice("信的第二页，你看了吗？", 0.62), 3.3, 0.75)
    at(b, voice("我手里只有信的第一页。", 0.92), 5.0, 0.6)
    write("corridor_l3", b)

    # ── 第 4 层：泥地，皮鞋，门闩；暗房里一句“你来了”，然后是沉默 ──
    b = blank()
    place_sfx(b, "rain_night", 0.0, 0.2)
    for i in range(9):
        place_sfx(b, "footstep_shoe", 0.5 + i * 0.62, 0.5)
    place_sfx(b, "latch_greenhouse", 3.2, 0.7)
    place_sfx(b, "candle", 4.0, 0.2)
    at(b, voice("你来了。", 0.6), 4.6, 0.7)
    # 之后留白：只有唱针空转的沙沙声（底噪本身就在）
    write("corridor_l4", b)

    # ── 第 5 层：三个孤立的声源（3D），主线轨只有空转的底噪 ──
    b = blank()
    place_sfx(b, "room_hum", 0.0, 0.5)
    write("corridor_l5", b)
    write("corridor_s1", voice("跟我念：la，ti，num。", 0.88))
    write("corridor_s2", voice("炉子太旺了，这锅汤要溢出来。", 1.12))
    write("corridor_s3", voice("妈妈，我又长高了。你量量看。", 1.3, 200))

    # ── 第 6 层：静 ──
    write("corridor_l6", np.zeros(int(6.0 * SR), dtype=np.float32))

    # ── 倒放版本 ──
    for i in range(1, 7):
        x = load_wav_ogg(OUT / ("corridor_l%d.ogg" % i))
        write("corridor_l%d_rev" % i, x[::-1])


def load_wav_ogg(path: Path) -> np.ndarray:
    with tempfile.NamedTemporaryFile(suffix=".wav") as f:
        subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-i", str(path), "-ar", str(SR), "-ac", "1", f.name], check=True)
        return load(Path(f.name))


if __name__ == "__main__":
    main()
