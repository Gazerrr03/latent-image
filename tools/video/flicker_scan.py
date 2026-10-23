#!/usr/bin/env python3
"""扫描镜头里的闪屏帧：整帧亮度（YAVG）突然偏离前后帧又回来的那几帧。
用法：python3 tools/video/flicker_scan.py [目录] [--thr 6]   （只报告，不改文件）"""
import re, subprocess, sys
from pathlib import Path


def yavg(path):
    r = subprocess.run(["ffmpeg", "-v", "error", "-i", str(path), "-vf", "signalstats,metadata=print:key=lavfi.signalstats.YAVG:file=-", "-f", "null", "-"],
                       capture_output=True, text=True)
    return [float(m) for m in re.findall(r"YAVG=([0-9.]+)", r.stdout)]


def spikes(y, thr, span=3):
    """返回 [(起帧, 止帧)]：这一段（≤span 帧）的亮度同时偏离前一帧与后一帧达 thr 以上，而前后两帧彼此接近"""
    out, n, i = [], len(y), 1
    while i < n - 1:
        for k in range(1, span + 1):
            a, b = i - 1, i + k
            if b >= n:
                break
            seg = y[i:b]
            before, after = y[a], y[b]
            if abs(before - after) < thr / 2 and all(abs(v - (before + after) / 2) >= thr for v in seg):
                out.append((i, b - 1))
                i = b
                break
        i += 1
    return out


if __name__ == "__main__":
    args = [a for a in sys.argv[1:] if not a.startswith("--")]
    thr = float(sys.argv[sys.argv.index("--thr") + 1]) if "--thr" in sys.argv else 6.0
    if "--thr" in sys.argv:
        args = [a for a in args if a != str(thr) and a != sys.argv[sys.argv.index("--thr") + 1]]
    d = Path(args[0] if args else "~/Movies/潜影展示").expanduser()
    for f in sorted(d.glob("*.mp4")):
        y = yavg(f)
        sp = spikes(y, thr)
        print(f"{f.name:12s} {len(y):4d} 帧  闪屏 {len(sp)} 处 {sp[:8]}")
