#!/usr/bin/env python3
"""Import the generated T-024 boards without overwriting prior art."""
from __future__ import annotations

import csv
import hashlib
from datetime import date
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont, ImageOps

ROOT = Path(__file__).resolve().parents[2]
BASE = ROOT / "assets" / "2d" / "T-024-人物三视图"
GEN = Path("/Users/qizhi_dong/.mirasim/agent-homes/codex-relay/generated_images/01a136a2-90bf-7892-bc8f-cc33a08fb44c")

SHEETS = {
    "grey": GEN / "exec-1320bbeb-15b7-499d-91b3-8a91d1179257.png",
    "constance": GEN / "exec-d5485e05-f0bc-48bc-8083-1c6a52e22262.png",
    "ambrose": GEN / "exec-00fb05f5-da0f-42bc-8c0a-ef34cb407a9c.png",
    "gideon": GEN / "exec-dcb57fa7-ecba-4c4e-a242-58f327de194c.png",
    "latente": GEN / "exec-8c8ec05d-ccbb-47f5-bd14-759b043e99e2.png",
}

META = {
    "grey": ("伊波利特·格雷", "解释者；唯一露出眼睛；左手不遮疤"),
    "ambrose": ("安布罗斯·塔尔博特", "记录者；照片与尸体；眼部以白色曝光遮挡"),
    "constance": ("康斯坦斯·塔尔博特", "照护者；黑色缎带；保留无名指宽戒指，拇指合拢遮虎口疤"),
    "iris": ("艾瑞斯·塔尔博特", "儿童人格；布条蒙眼；创可贴遮虎口疤"),
    "gideon": ("吉迪恩·沃登", "保护者；低帽檐遮眼；帆布手套遮虎口疤"),
    "latente": ("拉坦特夫人", "新生人格；黑色面纱；黑色蕾丝手套遮虎口疤"),
}


def fnt(size: int, bold=False):
    for p in ["/System/Library/Fonts/STHeiti Medium.ttc" if bold else "/System/Library/Fonts/STHeiti Light.ttc", "/System/Library/Fonts/Supplemental/Arial Unicode.ttf"]:
        try:
            return ImageFont.truetype(p, size)
        except OSError:
            pass
    return ImageFont.load_default()


def pad_16_9(src: Image.Image, size=(3840, 2160)):
    src = src.convert("RGB")
    fitted = ImageOps.contain(src, size, method=Image.Resampling.LANCZOS)
    canvas = Image.new("RGB", size, "#E5E0D7")
    canvas.paste(fitted, ((size[0] - fitted.width) // 2, (size[1] - fitted.height) // 2))
    return canvas


def make_iris_fallback():
    """A safe, fully dressed paper/mannequin concept until a human draws Iris."""
    W, H = 1536, 1024
    im = Image.new("RGB", (W, H), "#E9E3D7")
    d = ImageDraw.Draw(im)
    # faint paper grid / wash
    for x in range(0, W, 48): d.line((x, 0, x, H), fill="#D8D0C2", width=1)
    for y in range(0, H, 48): d.line((0, y, W, y), fill="#D8D0C2", width=1)
    def figure(cx, back=False, side=False):
        scale = 1.0 if not side else .8
        top, foot = 90, 900
        head_w = 120 * scale
        d.ellipse((cx-head_w/2, top, cx+head_w/2, top+125), fill="#C9B49B", outline="#806B5D", width=4)
        # short bob hair / blindfold
        d.pieslice((cx-head_w/2-8, top-8, cx+head_w/2+8, top+70), 180, 360, fill="#5A4A43", outline="#3B302D")
        d.rectangle((cx-head_w/2-2, top+51, cx+head_w/2+2, top+70), fill="#D2D0C9")
        d.rectangle((cx-head_w/2-5, top+44, cx+head_w/2+5, top+70), fill="#A69A8A")
        # sailor dress
        body_top = top+115
        d.polygon([(cx-62*scale,body_top),(cx+62*scale,body_top),(cx+120*scale,foot-65),(cx-120*scale,foot-65)], fill="#4E6370", outline="#2E3F49")
        d.polygon([(cx-58*scale,body_top+4),(cx+58*scale,body_top+4),(cx+18*scale,body_top+72),(cx-18*scale,body_top+72)], fill="#E2D8C4", outline="#786A5B")
        # arms
        d.line((cx-55*scale,body_top+20,cx-120*scale,body_top+260), fill="#C9B49B", width=int(28*scale))
        d.line((cx+55*scale,body_top+20,cx+120*scale,body_top+260), fill="#C9B49B", width=int(28*scale))
        # socks / shoes
        d.rectangle((cx-76*scale,foot-65,cx-32*scale,foot), fill="#E5E0D2")
        d.rectangle((cx+32*scale,foot-65,cx+76*scale,foot), fill="#E5E0D2")
        d.ellipse((cx-88*scale,foot-12,cx-18*scale,foot+18), fill="#493A36")
        d.ellipse((cx+18*scale,foot-12,cx+88*scale,foot+18), fill="#493A36")
        if back:
            d.line((cx,body_top+20,cx,foot-70), fill="#3A4C56", width=5)
    figure(250); figure(580, side=True); figure(900, back=True)
    # face and hand studies: intentionally non-photographic, no readable text
    cx, cy = 1270, 210
    d.ellipse((cx-150,cy-130,cx+150,cy+130), fill="#C9B49B", outline="#806B5D", width=6)
    d.rectangle((cx-150,cy-12,cx+150,cy+48), fill="#AAA093")
    d.pieslice((cx-160,cy-150,cx+160,cy+10),180,360,fill="#5A4A43")
    d.ellipse((1140,590,1280,890), fill="#C9B49B", outline="#806B5D", width=6)
    d.rectangle((1143,650,1277,705), fill="#D9CDBA")
    d.ellipse((1320,590,1460,890), fill="#C9B49B", outline="#806B5D", width=6)
    d.arc((1347,730,1410,800), 200, 340, fill="#9C3D39", width=8)
    d.rectangle((1324,650,1456,705), fill="#E1D8C9")
    return im


def write_sources(name, folder, status, extra=""):
    person, role = META[name]
    text = f"""# {person}（T-024）\n\n状态：{status}，待用户验收。\n\n- 角色 / 造型：{role}\n- 共同底脸：`../foundation/底脸-v1.png`。鼻形、颧骨、下颌和唇形作为跨人物一致性参考。\n- 工具：Codex 内置 imagegen；艾瑞斯本轮使用本地程序绘制的完整服装纸模候选，原因是图像模型连续误判学校年龄人物全身设定图，故不把未生成结果冒充成 AI 产物。\n- 生成日期：2026-10-13。\n- 画面不含现代物品、血、伤口或可读的游戏文字。\n{extra}\n"""
    (folder / "来源.md").write_text(text, encoding="utf-8")


def main():
    raise SystemExit("该 v1 导入器已停用：不得把放大裁切当作原生细节；艾瑞斯纸模不计交付。保留原件供审查。")
    BASE.mkdir(parents=True, exist_ok=True)
    # shared foundation at task root
    foundation = BASE / "底脸.png"
    if not foundation.exists():
        foundation.write_bytes((BASE / "foundation" / "底脸-v1.png").read_bytes())
    outputs = []
    for name, source in SHEETS.items():
        if not source.exists():
            continue
        folder = BASE / name
        folder.mkdir(parents=True, exist_ok=True)
        src = Image.open(source).convert("RGB")
        draft = folder / f"{name}_sheet-v1.png"
        src.save(draft)
        board = pad_16_9(src)
        board_path = folder / f"{name}_三视图.png"
        board.save(board_path, optimize=True)
        # The generated layout is stable: three figures occupy the left 76%; face and hand studies occupy the right.
        face = src.crop((1080, 0, 1536, 570))
        hand = src.crop((1030, 520, 1536, 1024))
        ImageOps.fit(face, (2048, 2048), method=Image.Resampling.LANCZOS).save(folder / f"{name}_脸.png")
        ImageOps.fit(hand, (2048, 2048), method=Image.Resampling.LANCZOS).save(folder / f"{name}_左手.png")
        extra = ""
        if name == "constance":
            extra = "- 交互修正：保留无名指宽戒指；合拇指的手势遮虎口，展开手部特写展示疤痕。"
        write_sources(name, folder, "候选", extra)
        outputs.extend([board_path, folder / f"{name}_脸.png", folder / f"{name}_左手.png"])
    # Iris is deliberately safe and conservative: a fully dressed paper/mannequin board, not a claim of final character art.
    folder = BASE / "iris"
    folder.mkdir(parents=True, exist_ok=True)
    iris = make_iris_fallback()
    iris.save(folder / "iris_sheet-v1.png")
    pad_16_9(iris).save(folder / "iris_三视图.png")
    ImageOps.fit(iris.crop((1080, 0, 1536, 420)), (2048, 2048), method=Image.Resampling.LANCZOS).save(folder / "iris_脸.png")
    ImageOps.fit(iris.crop((1080, 540, 1536, 1024)), (2048, 2048), method=Image.Resampling.LANCZOS).save(folder / "iris_左手.png")
    write_sources("iris", folder, "候选（程序绘制安全占位，需人工重绘）", "- 这张图锁定服装色、蒙眼布条、三视图基线与手部疤痕位置；不进入 T-025 作为最终脸部参考。")
    outputs.extend([folder / "iris_三视图.png", folder / "iris_脸.png", folder / "iris_左手.png"])
    # Add a compact manifest for reviewers.
    manifest = {"task": "T-024", "status": "候选", "shared_face": str(foundation.relative_to(ROOT)), "characters": {n: {"folder": str((BASE / n).relative_to(ROOT)), "files": [str(p.relative_to(ROOT)) for p in outputs if p.parent.name == n]} for n in META}}
    (BASE / "asset-manifest.json").write_text(__import__("json").dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"imported {len(outputs)} files to {BASE}")


if __name__ == "__main__":
    main()
