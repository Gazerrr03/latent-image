"""Raster handwriting for T5: a detached crossbar on each lowercase t.

The system font is used only to rasterize ordinary glyphs, never distributed.
The diagnostic t is drawn as two independent ink strokes in font coordinates.
"""
from PIL import ImageFont

FONT = "/System/Library/Fonts/Supplemental/Bradley Hand Bold.ttf"


def font_at(size):
    return ImageFont.truetype(FONT, size)


def draw_line(draw, position, text, font, fill):
    x, y = position
    size = font.size
    stroke = max(3, round(size * .075))
    for char in text:
        advance = font.getlength(char)
        if char == "t":
            # Curved downstroke ends in a small hook. The crossbar floats on
            # its left, matching the current in-game observation wording.
            points = [(x + size * a, y + size * b) for a, b in
                      [(.39, .29), (.37, .49), (.35, .74), (.37, .85), (.43, .87), (.48, .82)]]
            draw.line(points, fill=fill, width=stroke, joint="curve")
            draw.line((x + size * .03, y + size * .54,
                       x + size * .19, y + size * .52), fill=fill, width=stroke)
            advance = max(advance, size * .54)
        else:
            draw.text((x, y), char, font=font, fill=fill,
                      stroke_width=max(1, round(size * .012)), stroke_fill=fill)
        x += advance
    return x


def line_width(text, font):
    return sum(max(font.getlength(c), font.size * .54) if c == "t"
               else font.getlength(c) for c in text)
