"""拼“参考 | 模型”对照图（系统 Python + PIL；Blender 自带的 Python 没有 PIL）。

    python3 assets/3d/manor/scripts/19_room_compare.py 客房
读 review/rooms/<房间>/<视角>-白天|夜晚.jpg，与 T-0xx 效果图并排，输出 对照-<视角>.jpg（参考 | 白天 | 夜晚）。
"""
import sys, os
from PIL import Image
ROOT = '/Users/qizhi_dong/Projects/DigitalMedia'
REFS = {'客房': {'全景': 'T-026-客房/guest_room_透视_establish-v3.png', '书桌': 'T-026-客房/guest_room_透视_board-v2.png',
                 '床与壁炉': 'T-026-客房/guest_room_透视_bed-v2.png', '打字机近景': 'T-026-客房/guest_room_透视_typewriter_close-v2.png',
                 '镜子': 'T-026-客房/guest_room_透视_mirror-v2.png'},
        '暗房': {'全景': 'T-027-暗房/darkroom_透视_wide-v3.png', '推门': 'T-027-暗房/darkroom_透视_door_push-v2.png', '显影盘': 'T-027-暗房/darkroom_透视_tray-v2.png'},
        '花园百叶外侧': {'全景': 'T-032-花园·通风口外侧/garden_透视_garden_wide-v2.png'},
        '门厅': {'门厅朝南': 'T-034-门厅/hall_hall_mid-v3.png', '门厅朝北': 'T-034-门厅/hall_north-v3.png', '楼梯': 'T-034-门厅/hall_stair-v3.png',
                 '二楼楼梯口': 'T-034-门厅/hall_landing_darkroom-v3.png'},
        '餐厅': {'餐厅朝南': 'T-029-餐厅/dining_dining_mid-v3.png', '餐叙区': 'T-029-餐厅/dining_snug-v3.png', '多一副餐具': 'T-029-餐厅/dining_table_close-v3.png'},
        '客厅': {'客厅朝西': 'T-033-客厅·降灵会/seance_seance_mid-v3.png', '降灵会布置': 'T-033-客厅·降灵会/seance_table_candle-v3.png'},
        '照片档案室': {'朝南凸窗': 'T-028-照片档案室/archive_archive_mid-v3b.png', '门框': 'T-028-照片档案室/archive_doorframe-v3.png'},
        '艾瑞斯的房间': {'朝北看窗': 'T-031-艾瑞斯的房间/child_room_child_mid-v3.png', '贴画的墙': 'T-031-艾瑞斯的房间/child_room_child_wall-v3.png'},
        '温室': {'全景': 'T-030-温室/greenhouse_透视_green_mid-v2.png', '手压泵': 'T-030-温室/greenhouse_透视_pump_detail-v2.png', '侧门': 'T-030-温室/greenhouse_透视_side_door-v2.png'}}
room = sys.argv[1] if len(sys.argv) > 1 else '客房'
D = f'{ROOT}/assets/3d/manor/review/rooms/{room}'
for key, ref in REFS.get(room, {}).items():
    ims = [Image.open(f'{ROOT}/assets/2d/{ref}').convert('RGB')]
    ims += [Image.open(p).convert('RGB') for p in (f'{D}/{key}-白天.jpg', f'{D}/{key}-夜晚.jpg') if os.path.exists(p)]
    if len(ims) < 2: continue
    h = 432; ims = [i.resize((int(i.width * h / i.height), h)) for i in ims]
    S = Image.new('RGB', (sum(i.width for i in ims) + 10 * (len(ims) - 1), h), 'white'); x = 0
    for i in ims: S.paste(i, (x, 0)); x += i.width + 10
    S.save(f'{D}/对照-{key}.jpg', quality=88); print('对照', key)
