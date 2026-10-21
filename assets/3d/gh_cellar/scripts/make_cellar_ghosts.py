from PIL import Image, ImageDraw, ImageFilter
import random, os

OUT = r"D:\千人千面blender\新建游戏项目\art\ui"
os.makedirs(OUT, exist_ok=True)
rng = random.Random(19261021)

def soft_glow(im, radius=8):
    a = im.filter(ImageFilter.GaussianBlur(radius))
    return Image.alpha_composite(a, im)

# tall owner silhouette, to be overlaid on the right of the viewfinder
W, H = 360, 720
im = Image.new("RGBA", (W, H), (0, 0, 0, 0))
d = ImageDraw.Draw(im, "RGBA")
body = (204, 195, 176, 155)
# coat
d.polygon([(130, 250), (230, 250), (300, 650), (60, 650)], fill=body)
# shoulders
d.ellipse([70, 205, 290, 360], fill=body)
# neck
d.rectangle([160, 190, 200, 270], fill=(226, 214, 190, 165))
# head
d.ellipse([130, 80, 230, 220], fill=(218, 206, 182, 175))
# hat
d.rectangle([120, 45, 240, 92], fill=(24, 20, 16, 210))
d.ellipse([95, 72, 265, 105], fill=(24, 20, 16, 210))
# faint face
d.ellipse([158, 126, 202, 196], fill=(244, 226, 194, 150))
# arms
d.line([(95, 280), (35, 480)], fill=body, width=40)
d.line([(265, 280), (325, 480)], fill=body, width=40)
im = im.filter(ImageFilter.GaussianBlur(2.4))
im.save(os.path.join(OUT, "owner_reflection.png"))

# generic standing silhouette for the relics
W, H = 240, 500
im = Image.new("RGBA", (W, H), (0, 0, 0, 0))
d = ImageDraw.Draw(im, "RGBA")
c = (180, 172, 146, 95)
d.ellipse([82, 40, 158, 132], fill=c)
d.ellipse([58, 126, 182, 250], fill=c)
d.polygon([(70, 210), (170, 210), (205, 480), (35, 480)], fill=c)
im = im.filter(ImageFilter.GaussianBlur(7))
im = soft_glow(im, 5)
im.save(os.path.join(OUT, "silhouette.png"))

# footprint
W, H = 180, 260
im = Image.new("RGBA", (W, H), (0, 0, 0, 0))
d = ImageDraw.Draw(im, "RGBA")
d.ellipse([48, 24, 132, 138], fill=(190, 172, 140, 125))
d.ellipse([62, 135, 122, 215], fill=(190, 172, 140, 100))
for i in range(5):
    d.ellipse([72+i*10, 145+i*8, 80+i*10, 157+i*8], fill=(190, 172, 140, 70))
im = im.filter(ImageFilter.GaussianBlur(5))
im.save(os.path.join(OUT, "footprint.png"))

# old key
W, H = 256, 160
im = Image.new("RGBA", (W, H), (0, 0, 0, 0))
d = ImageDraw.Draw(im, "RGBA")
c = (220, 188, 116, 150)
d.ellipse([20, 36, 90, 106], outline=c, width=12)
d.rectangle([88, 62, 215, 80], fill=c)
d.rectangle([168, 78, 185, 116], fill=c)
d.rectangle([196, 78, 213, 105], fill=c)
im = im.filter(ImageFilter.GaussianBlur(2.4))
im.save(os.path.join(OUT, "key_ghost.png"))
print("WROTE", os.listdir(OUT))
