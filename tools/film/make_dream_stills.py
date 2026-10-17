"""章间梦境片段（影像片段表 梦_r0—梦_r6）用的静帧：从游戏里按镜号截图，转成梦里的样子。

做法：Godot --capture=<镜号> --clean 截一张 1280x720 → 转灰度、拉开对比、稍微提亮
（冷蓝的颜色由滤镜表的“梦境”预设加上）；第 6 章那一夜“不是梦”，红灯保留原色。
输出到 godot/art/footage/dream_<章>_<名>.png。分镜见 docs/02 第 9.1 节“梦境分镜”。

用法：python3 tools/film/make_dream_stills.py [名字 ...]   （不写名字 = 全部重截）
"""
import subprocess, sys, tempfile
from pathlib import Path
from PIL import Image, ImageOps, ImageEnhance

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "godot/art/footage"

# 输出名 -> (镜号, 是否保留颜色[, 裁切框（按 1280x720 的坐标），用 2 倍分辨率截图再裁])
STILLS = {
    "dream_r3_drawings": ("C3-04", False, (590, 172, 910, 352)),
    "dream_r0_train": ("C0-02", False),
    "dream_r0_hall": ("C0-05", False),
    "dream_r2_table": ("C2-01", False),
    "dream_r2_archive": ("C2-03", False),
    "dream_r4_greenhouse": ("C4-03", False),
    "dream_r4_wall": ("C4-04", False),
    "dream_r5_seance": ("C5-04", False),
    "dream_r6_trays": ("C6-05", True),
}


def capture(shot: str, out: Path, scale: int = 1) -> None:
    cmd = ["perl", "-e", "alarm(90);exec(@ARGV)", "godot", "--path", str(ROOT / "godot"),
           "--resolution", f"{1280 * scale}x{720 * scale}", "--", f"--capture={shot}", "--clean", "--wait=3", f"--out={out}"]
    subprocess.run(cmd, check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)


def dreamify(src: Path, keep_color: bool, box=None) -> Image.Image:
    im = Image.open(src).convert("RGB")
    if box:
        k = im.width / 1280
        im = im.crop(tuple(int(v * k) for v in box))
    im = im.resize((1280, 720), Image.LANCZOS)
    if keep_color:
        return ImageEnhance.Brightness(im).enhance(1.1)
    g = ImageOps.grayscale(im)
    g = ImageOps.autocontrast(g, cutoff=1)
    g = ImageEnhance.Brightness(g).enhance(1.12)
    return g.convert("RGB")


def main(names: list[str]) -> None:
    todo = names or list(STILLS)
    with tempfile.TemporaryDirectory() as tmp:
        for name in todo:
            shot, keep, *box = STILLS[name]
            raw = Path(tmp) / f"{name}.png"
            capture(shot, raw, 2 if box else 1)
            dreamify(raw, keep, box[0] if box else None).save(OUT / f"{name}.png")
            print(f"{name}.png  ← {shot}")


if __name__ == "__main__":
    main(sys.argv[1:])
