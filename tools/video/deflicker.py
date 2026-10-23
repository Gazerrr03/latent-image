#!/usr/bin/env python3
"""去闪屏：找出整帧亮度突然偏离前后帧又回来的帧（≤3 帧），用前一帧顶替，重新编码覆盖原文件。
用法：python3 tools/video/deflicker.py [目录] [--rel 0.03] [--skip S31,S32] [--dry]
  --rel  相对阈值：偏离量 / 前后帧平均亮度（默认 3%）
  --skip 逗号分隔的镜号，不处理（影像片段与对话里的亮度变化是内容，不是闪屏）
  --dry  只报告，不改文件
闪屏的来源：滤镜里的胶片闪烁（每个镜头在同样的帧序号上出现，例如第 38—39 帧、第 116 帧整屏变暗）。"""
import re, subprocess, sys
from pathlib import Path


def yavg(path):
    r = subprocess.run(["ffmpeg", "-v", "error", "-i", str(path), "-vf", "signalstats,metadata=print:key=lavfi.signalstats.YAVG:file=-", "-f", "null", "-"],
                       capture_output=True, text=True)
    return [float(m) for m in re.findall(r"YAVG=([0-9.]+)", r.stdout)]


def spikes(y, rel, span=3):
    out, n, i = [], len(y), 1
    while i < n - 1:
        hit = False
        for k in range(1, span + 1):
            a, b = i - 1, i + k
            if b >= n:
                break
            before, after = y[a], y[b]
            mid = (before + after) / 2
            thr = max(1.0, rel * mid)
            if abs(before - after) < thr / 2 and all(abs(v - mid) >= thr for v in y[i:b]):
                out.append((i, b - 1))
                i, hit = b, True
                break
        if not hit:
            i += 1
    return out


def fix(path, spans):
    """逐帧解码，闪屏帧换成它前面最近的一张好帧，再编码（freezeframes 滤镜要两路输入，不好用）"""
    probe = subprocess.run(["ffprobe", "-v", "error", "-select_streams", "v:0", "-show_entries", "stream=width,height,r_frame_rate", "-of", "csv=p=0", str(path)],
                           capture_output=True, text=True).stdout.strip().split(",")
    w, h, fps = int(probe[0]), int(probe[1]), probe[2]
    size = w * h * 3 // 2
    bad = set()
    for a, b in spans:
        bad.update(range(a, b + 1))
    tmp = path.with_suffix(".fix.mp4")
    dec = subprocess.Popen(["ffmpeg", "-v", "error", "-i", str(path), "-f", "rawvideo", "-pix_fmt", "yuv420p", "-"], stdout=subprocess.PIPE)
    enc = subprocess.Popen(["ffmpeg", "-y", "-v", "error", "-f", "rawvideo", "-pix_fmt", "yuv420p", "-s", f"{w}x{h}", "-r", fps, "-i", "-",
                            "-c:v", "libx264", "-crf", "14", "-preset", "medium", "-pix_fmt", "yuv420p", str(tmp)], stdin=subprocess.PIPE)
    good, i = None, 0
    while True:
        buf = dec.stdout.read(size)
        if len(buf) < size:
            break
        if i in bad and good is not None:
            buf = good
        else:
            good = buf
        enc.stdin.write(buf)
        i += 1
    enc.stdin.close()
    dec.wait()
    if enc.wait() != 0:
        tmp.unlink(missing_ok=True)
        return False
    tmp.replace(path)
    return True


if __name__ == "__main__":
    argv = sys.argv[1:]
    rel = float(argv[argv.index("--rel") + 1]) if "--rel" in argv else 0.03
    dry = "--dry" in argv
    skip = set(argv[argv.index("--skip") + 1].split(",")) if "--skip" in argv else set()
    rest = [a for i, a in enumerate(argv) if not a.startswith("--") and (i == 0 or argv[i - 1] not in ("--rel", "--skip"))]
    d = Path(rest[0] if rest else "~/Movies/潜影展示").expanduser()
    total = 0
    for f in sorted(d.glob("*.mp4")):
        if f.stem in skip:
            continue
        y = yavg(f)
        sp = spikes(y, rel)
        if not sp:
            continue
        frames = sum(b - a + 1 for a, b in sp)
        total += frames
        print(f"{f.name:10s} {len(sp):2d} 处 {frames:2d} 帧 {sp[:10]}", flush=True)
        if not dry:
            fix(f, sp)
    print(f"共 {total} 帧" + ("（未改文件）" if dry else "，已替换"))
