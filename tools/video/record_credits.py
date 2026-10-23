#!/usr/bin/env python3
"""录制庄园实景片尾制作名单与致谢动画为 MP4 视频。
1. 使用 Godot Movie Maker 逐帧录制 1920x1080 @ 30fps 完整音画为未压缩 AVI；
2. 调用 ffmpeg 压缩为高画质标准 H.264 / AAC MP4 文件，存放在 output/。
"""

import os
import subprocess
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
GODOT_DIR = ROOT / "godot"
OUTPUT_DIR = ROOT / "output"
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

RAW_AVI = Path("/tmp/credits_raw.avi")
OUT_MP4 = OUTPUT_DIR / "潜影_庄园实景片尾制作名单.mp4"
OUT_MP4_EN = OUTPUT_DIR / "credits_manor_ending.mp4"


def main():
    print("=" * 60)
    print("正在启动《潜影》庄园实景片尾动画录制管线...")
    print(f"输出目录: {OUTPUT_DIR}")
    print("=" * 60)

    if RAW_AVI.exists():
        RAW_AVI.unlink()

    # 1. 运行 Godot Movie Writer
    godot_cmd = [
        "godot",
        "--path",
        str(GODOT_DIR),
        "--resolution",
        "1920x1080",
        "--fixed-fps",
        "30",
        "--write-movie",
        str(RAW_AVI),
        "--script",
        "res://tools/record_credits.gd",
    ]

    print("\n[Step 1/2] 运行 Godot 逐帧渲染与音频录制 (1080p @ 30fps)...")
    start_t = time.time()
    res = subprocess.run(godot_cmd)
    if res.returncode != 0:
        print(f"Godot 渲染失败，退出码: {res.returncode}")
        sys.exit(res.returncode)

    render_t = time.time() - start_t
    print(f"Godot 渲染完成！耗时: {render_t:.1f}s")

    if not RAW_AVI.exists() or RAW_AVI.stat().st_size == 0:
        print(f"错误: 原始视频文件不存在或为空: {RAW_AVI}")
        sys.exit(1)

    raw_mb = RAW_AVI.stat().st_size / (1024 * 1024)
    print(f"原始 AVI 文件大小: {raw_mb:.1f} MB")

    # 2. ffmpeg 转码为高质量 MP4
    print("\n[Step 2/2] 调用 ffmpeg 压制为 H.264 / AAC MP4...")
    ffmpeg_cmd = [
        "ffmpeg",
        "-y",
        "-i",
        str(RAW_AVI),
        "-c:v",
        "libx264",
        "-preset",
        "medium",
        "-crf",
        "18",
        "-pix_fmt",
        "yuv420p",
        "-c:a",
        "aac",
        "-b:a",
        "192k",
        "-movflags",
        "+faststart",
        str(OUT_MP4),
    ]

    ff_res = subprocess.run(ffmpeg_cmd)
    if ff_res.returncode != 0:
        print(f"ffmpeg 编码失败，退出码: {ff_res.returncode}")
        sys.exit(ff_res.returncode)

    # 复制/硬链接一份英文名便于双语查看
    if OUT_MP4.exists():
        import shutil
        shutil.copyfile(OUT_MP4, OUT_MP4_EN)

    # 删除中间 AVI 释放临时磁盘
    if RAW_AVI.exists():
        RAW_AVI.unlink()

    mp4_mb = OUT_MP4.stat().st_size / (1024 * 1024)
    print("=" * 60)
    print("录制与压制完成！")
    print(f"成片路径: {OUT_MP4}")
    print(f"备份路径: {OUT_MP4_EN}")
    print(f"文件大小: {mp4_mb:.1f} MB")
    print("=" * 60)


if __name__ == "__main__":
    main()
