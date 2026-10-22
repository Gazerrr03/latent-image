"""Generate item-specific, readable paper surfaces from approved story excerpts.

No body copy is invented here. Each physical sheet has independent front/back
textures and dimensions; books, carbon copies, clippings and tickets retain their
own paper treatment. Re-run from the repository root with Python 3 and Pillow.
"""
from pathlib import Path
import argparse
import csv
import hashlib
import json
import random
import shutil
from PIL import Image, ImageDraw, ImageFont, ImageOps
from handwriting import draw_line, font_at, line_width

ROOT = Path(__file__).resolve().parents[4]
OUT = ROOT / "godot/art/props/inspection"
TABLE = ROOT / "godot/content/visual/inspection_pages.csv"
FONT = "/System/Library/Fonts/Supplemental/Songti.ttc"


def wrapped(text, font, width, handwritten=False):
    lines = []
    for paragraph in text.split("\n"):
        if handwritten:
            line = ""
            for word in paragraph.split():
                candidate = (line + " " + word).strip()
                if line and line_width(candidate, font) > width:
                    lines.append(line)
                    line = word
                else:
                    line = candidate
            lines.append(line)
            continue
        line = ""
        for character in paragraph:
            length = line_width(line + character, font) if handwritten else font.getlength(line + character)
            if length > width and line:
                lines.append(line)
                line = ""
            line += character
        lines.append(line)
    return lines


def surface(row, side):
    style = row["style"]
    width = 1200
    height = round(width * float(row["height"]) / float(row["width"]))
    rng = random.Random(row["object"] + side)
    base = (215, 203, 171) if style == "newspaper" else (234, 224, 198)
    if style == "carbon":
        base = (62, 63, 75)
    # Subtle fiber, fold and edge wear; the original content remains dominant.
    image = Image.new("RGB", (width, height), base)
    pixels = image.load()
    for y in range(height):
        for x in range(width):
            edge = min(x, y, width - 1 - x, height - 1 - y)
            wear = max(0, 1 - edge / 45) * 10
            noise = rng.choice([-2, -1, 0, 0, 0, 1, 2])
            pixels[x, y] = tuple(max(0, min(255, round(c + noise - wear))) for c in base)
    draw = ImageDraw.Draw(image)
    margin = 115 if style not in ["ticket", "card"] else 75
    color = (46, 39, 30) if style != "carbon" else (172, 166, 176)
    if style in ["ledger", "journal"]:
        for y in range(170, height - 70, 65):
            draw.line((65, y, width - 65, y), fill=(193, 183, 164), width=1)
        draw.line((150, 70, 150, height - 70), fill=(171, 122, 110), width=2)
        margin = 190
    elif style == "ticket":
        draw.rectangle((30, 30, width - 30, height - 30), outline=color, width=4)
        draw.rectangle((43, 43, width - 43, height - 43), outline=color, width=1)
        for y in range(20, height, 25):
            draw.ellipse((width - 58, y, width - 51, y + 7), fill=(170, 154, 124))
    elif style == "card":
        draw.rectangle((48, 48, width - 48, height - 48), outline=(151, 130, 96), width=2)
    elif style == "newspaper":
        draw.line((60, 120, width - 60, 120), fill=color, width=3)
        draw.line((60, height - 55, width - 60, height - 55), fill=color, width=2)
    physical = row.get("surface_" + side, "") or row[side]
    text = "" if side == "back" and row.get("dynamic_back", "") == "1" else physical.replace("\\n", "\n")
    handwritten = row.get("handwriting", "") == "detached_t"
    if style == "photo" and side == "back" and text:
        font = ImageFont.truetype("/System/Library/Fonts/Supplemental/Bradley Hand Bold.ttf", 120)
        ink = Image.new("RGBA", (width, height))
        ImageDraw.Draw(ink).text((width * .68, height * .64), text, font=font, fill=(65, 59, 49, 230))
        image = Image.alpha_composite(image.convert("RGBA"), ink.rotate(-7, resample=Image.Resampling.BICUBIC))
        return image
    size = 46 if style != "card" else 88
    if handwritten:
        size = 160 if style == "card" else 84
    if style == "ticket":
        size = 54
    while True:
        font = font_at(size) if handwritten else ImageFont.truetype(FONT, size)
        lines = wrapped(text, font, width - margin * 2, handwritten)
        if len(lines) * size * 1.65 < height - margin * 2 or size <= 28:
            break
        size -= 2
    y = margin if style != "card" else (height - len(lines) * size * 1.65) / 2
    for line in lines:
        length = line_width(line, font) if handwritten else font.getlength(line)
        x = margin if style != "card" else (width - length) / 2
        if handwritten:
            draw_line(draw, (x, y), line, font, color)
        else:
            draw.text((x, y), line, font=font, fill=color)
        y += size * 1.65
    if style == "letter":
        draw.line((70, height // 2, width - 70, height // 2), fill=(222, 211, 186), width=2)
    if style == "carbon":
        image = ImageOps.mirror(image)
    if style == "torn":
        rgba = image.convert("RGBA")
        polygon = [(0, height), (0, 0)] + [(x, rng.randint(2, 20)) for x in range(0, width, 11)] + [(width, 0), (width, height)]
        mask = Image.new("L", image.size)
        ImageDraw.Draw(mask).polygon(polygon, fill=255)
        rgba.putalpha(mask)
        image = rgba
    return image


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--scenes-only", action="store_true")
    parser.add_argument("--objects", nargs="*")
    args = parser.parse_args()
    OUT.mkdir(parents=True, exist_ok=True)
    records = list(csv.DictReader(TABLE.open()))
    if args.objects:
        records = [row for row in records if row["object"] in args.objects]
    manifest = []
    for row in records:
        for side in [] if args.scenes_only else ["front", "back"]:
            path = OUT / f'{row["object"]}_{row["page"]}_{side}.png'
            external = row.get(side + "_image", "")
            if external:
                original = ROOT / external
                image = Image.open(original)
                if image.format == "PNG":
                    if original.resolve() != path.resolve():
                        shutil.copy2(original, path)
                else:
                    # Preserve decoded native pixels while using the texture's actual PNG format.
                    image.save(path, format="PNG")
                image = Image.open(path)
            else:
                image = surface(row, side)
                image.save(path)
            manifest.append({"path": str(path.relative_to(ROOT)), "size": image.size,
                             "sha256": hashlib.sha256(path.read_bytes()).hexdigest(),
                             "source": row["source"], "text": row[side],
                             "surface_text": row.get("surface_" + side, "") or row[side],
                             "handwriting": row.get("handwriting", ""),
                             "dynamic": side == "back" and row.get("dynamic_back", "") == "1"})
        if row["page"] != "0":
            continue
        bound = row["style"] in ["ledger", "journal", "manual"]
        scene = f'''[gd_scene load_steps=2 format=3]

[ext_resource type="Script" path="res://world/inspection_document.gd" id="1"]

[node name="{row['object']}" type="Node3D"]
script = ExtResource("1")
object_id = "{row['object']}"
paper_size = Vector2({float(row['width'])}, {float(row['height'])})
binding = {str(bound).lower()}
'''
        (OUT / f'{row["object"]}.tscn').write_text(scene)
    if not args.scenes_only:
        manifest_path = ROOT / "assets/3d/inspection/document-manifest.json"
        if args.objects and manifest_path.exists():
            updated = {item["path"] for item in manifest}
            manifest = [item for item in json.loads(manifest_path.read_text()) if item["path"] not in updated] + manifest
        manifest_path.write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + "\n")
    print(f"Generated {len(manifest)} paper surfaces for {len(set(r['object'] for r in records))} objects")


if __name__ == "__main__":
    main()
