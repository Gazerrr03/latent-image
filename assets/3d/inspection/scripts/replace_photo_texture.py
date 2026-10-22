"""Package the approved photo into existing native texture references, preserving geometry."""
from pathlib import Path
import json, struct
from PIL import Image
ROOT = Path(__file__).resolve().parents[4]
source = ROOT / 'assets/2d/inspection/generated/photo1926-redesign-v1.png'
target = ROOT / 'godot/art/levels/manor/textures/photo_1926.jpg'
Image.open(source).convert('RGB').save(target, quality=96, subsampling=0)
copy = ROOT / 'godot/art/levels/ded_corridor/ded_corridor_photo_1926.jpg'
copy.write_bytes(target.read_bytes())
path = ROOT / 'godot/art/levels/ded_corridor/ded_corridor.glb'
raw = path.read_bytes()
size, kind = struct.unpack_from('<II', raw, 12)
doc = json.loads(raw[20:20+size])
offset = 20+size
length, kind = struct.unpack_from('<II', raw, offset)
binary = raw[offset+8:offset+8+length]
for image in doc['images']:
    if image.get('name') != 'photo_1926':
        continue
    binary += b'\0' * (-len(binary) % 4)
    payload = target.read_bytes()
    view = {'buffer': 0, 'byteOffset': len(binary), 'byteLength': len(payload)}
    doc['bufferViews'].append(view)
    image['bufferView'] = len(doc['bufferViews'])-1
    image['mimeType'] = 'image/jpeg'
    binary += payload
doc['buffers'][0]['byteLength'] = len(binary)
binary += b'\0' * (-len(binary) % 4)
js = json.dumps(doc, ensure_ascii=False, separators=(',', ':')).encode()
js += b' ' * (-len(js) % 4)
output = struct.pack('<III', 0x46546c67, 2, 28+len(js)+len(binary))
output += struct.pack('<II', len(js), 0x4e4f534a)+js
output += struct.pack('<II', len(binary), 0x004e4942)+binary
path.write_bytes(output)
