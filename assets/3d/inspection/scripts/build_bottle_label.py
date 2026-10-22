from pathlib import Path
import csv,re
from PIL import Image,ImageDraw,ImageFont
ROOT=Path(__file__).resolve().parents[4]
row=next(r for r in csv.DictReader((ROOT/'godot/content/visual/inspection_labels.csv').open())if r['id']=='hs_bottles')
text=row['text'].replace('\\n','\n')
image=Image.new('RGB',(1024,512),(217,206,177));draw=ImageDraw.Draw(image)
font_path=next(Path('/System/Library/AssetsV2').glob('com_apple_MobileAsset_Font*/*/AssetData/Kaiti.ttc'))
font=ImageFont.truetype(str(font_path),135)
for line,y in zip(text.splitlines(),[28,190,350]):
 box=draw.textbbox((0,0),line,font=font);draw.text(((1024-(box[2]-box[0]))/2,y),line,font=font,fill=(38,33,28),anchor='lt')
out=ROOT/'assets/3d/inspection/generated/bottle-label-v1.png';out.parent.mkdir(parents=True,exist_ok=True);image.save(out)
print(out)
