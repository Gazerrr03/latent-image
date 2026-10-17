"""Build the v3 room-reference gallery and verify copies without modifying images."""
from pathlib import Path
import hashlib
import html
import json
import os
import struct

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / 'assets/production/2026-10-16-room-previews-v3'
NOTES = {
    'hall_hall_mid-v3': '已修正钟面为七点；门厅无窗、无楼梯。正门四心拱曲线与侧门面板分格仍需按 v1 / 四面板规范建模。',
    'hall_north-v3': '北门外可见横走廊与左侧楼梯脚；钟面七点。侧门面板分格仍有生成偏差。',
    'hall_stair-v3': '修订后为左侧上行、右侧返回的平行折返楼梯，背墙无窗。图中踏步数不等于规定的两跑各 10 级，建模以 v1 为准。',
    'hall_landing_darkroom-v3': '已把暗房红光门从正前方端墙移到远端左墙；中段左侧留过道。精确长度与门洞宽度以 v1 为准。',
    'archive_archive_mid-v3b': '凸窗、窗座、大书桌、东西柜架与西侧合影墙可见。凸窗各扇的窗格细分仍需按六上六下规范校正；纸面细纹不可作为可读文字使用。',
    'archive_doorframe-v3': '修订去掉多余壁炉与钟；四面板北门、左框刻痕、底片柜、手册和朝下照片可见。旧刻痕的剧情辨识仍需在游戏近景中验证。',
    'dining_dining_mid-v3': '南墙三扇推拉窗；左侧东墙壁炉与厨房门、右侧门厅门。椅数与侧门面板细分需按物件清单和四面板规范建模。',
    'dining_snug-v3': '无窗、北侧实墙、木梁、小圆桌与瓷器柜；前景开口边有较厚饰边，不能据此新增隔墙或门。',
    'dining_table_close-v3': '末端空椅子前有完整餐具；两侧餐具衬托。该图表达状态，不能替代房间反向空间参考；额外一副的叙事识别仍需结合章节验证。',
    'child_room_child_mid-v3': '北侧唯一推拉窗、窗下书桌、左侧西墙壁炉、铜床、窗外温室屋顶可见。',
    'child_room_child_wall-v3': '南门偏左、门右七张乱线画、柜上音乐盒。门扇生成成六面板，应按共同规范改为四面板；个别家具位置不能视为精确坐标。',
    'iris_drawing_black_cloth-v3': '修订加重遮堵线团，仅露出少量网格眼；旧纸、黑乱线与被堵开口均可见。',
    'iris_drawing_family_portrait-v3': '六个重复网格脸、连成一体的身体、多手与名字处黑线条；黑白乱线。',
    'iris_drawing_hat_man-v3': '礼帽、无五官网格圆脸、放大的左手新月疤可见；黑白乱线。',
    'iris_drawing_red_light_asleep-v3': '门下闭眼与尖刺睫毛、上方网格圆灯；全图黑色线条，不使用红颜料。',
    'seance_seance_mid-v3': '南墙三窗、西墙壁炉及北段一窗、北墙门可见；侧门生成分格需改为四面板。',
    'seance_table_candle-v3': '修订为围桌五椅加一把远椅；全拉帘、壁炉熄灭、仅烛光，手铃与扣卡可见。与平日图共用空间；侧门分格需改为四面板。',
}


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    items = json.loads((OUT / 'generation-log.json').read_text())
    cards, rows = [], []
    for x in items:
        x['selected_source'] = x['revision_source'] or x['source']
        path = Path(x['destination'])
        data = path.read_bytes()
        assert data[:8] == b'\x89PNG\r\n\x1a\n', path
        width, height = struct.unpack('>II', data[16:24])
        digest = sha(path)
        assert digest == sha(Path(x['selected_source'])), path
        assert width > 0 and height > 0
        x.update(file=str(path.relative_to(ROOT)), width=width, height=height,
                 sha256=digest, format='PNG', copy_verified=True,
                 review_note=NOTES[x['name']], status='参考预览，待用户审查')
        url = html.escape(os.path.relpath(path, OUT))
        label = html.escape(x['name'])
        note = html.escape(x['review_note'])
        cards.append(f'<article><a href="{url}"><img src="{url}" loading="lazy" alt="{label}"></a>'
                     f'<div><h2>{label}</h2><p>{path.parent.name} · {width} × {height} · PNG</p>'
                     f'<p>{note}</p><a href="{url}">打开原图</a></div></article>')
        rows.append(f"| {x['name']} | [预览]({os.path.relpath(path, OUT)}) | {width} × {height} | {x['review_note']} |")
    assert len(items) == 17 and len({x['sha256'] for x in items}) == 17
    (OUT / 'manifest.json').write_text(json.dumps(items, ensure_ascii=False, indent=2) + '\n')
    (OUT / 'index.html').write_text('''<!doctype html><html lang="zh-CN"><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1"><title>补图 v3 · 17 张参考预览</title>
<style>body{margin:0;background:#f3f0e8;color:#263732;font:16px/1.7 system-ui,sans-serif}main{max-width:1400px;margin:auto;padding:40px 24px}h1{font-size:30px}header{max-width:1000px;margin-bottom:32px}section{display:grid;grid-template-columns:repeat(auto-fit,minmax(min(100%,540px),1fr));gap:24px}article{background:#fff;border:1px solid #d4d9cf}article img{display:block;width:100%;height:auto}article div{padding:18px 22px}h2{font-size:18px;overflow-wrap:anywhere;margin:0}a{color:#35675e}p{margin:8px 0}.notice{border-left:3px solid #a77943;padding-left:16px}</style>
<main><header><p>奥瑞尔庄园 / 2026-10-16</p><h1>补图 v3 · 17 张参考预览</h1>
<p>13 张空间 / 状态图 + 4 张艾瑞斯的画。使用 Codex 内置 image 工具生成，原图保存到对应设计包根目录。点击图片查看原图。</p>
<p class="notice">本页确认缺失文件已补齐；未代表全部通过建模验收。楼梯级数、门板和窗格细分等偏差逐图列出。尺寸和洞口以 T-039 v1 平面及共同规范为准。餐桌近景和降灵会状态图不增加新的观察朝向，不能据此声称所有房间已满足 SOP 的三朝向条件。</p>
</header><section>''' + ''.join(cards) + '</section></main></html>')
    (OUT / '审查说明.md').write_text('''# 补图需求 v3：生成与审查记录

日期：2026-10-16。17/17 缺失参考预览已补齐；工具：Codex 内置 image_gen。没有覆盖旧 v2 图。

- 房间图原生输出 1672 × 941；画作原生输出 1448 × 1086。未放大冒充原生 1080p。
- 所选文件均已检查 PNG 签名、尺寸、SHA-256；项目副本与生成原图字节一致。机器检查见 `manifest.json`。
- 原始需求提示词留在各包 `prompts/*-v3*.txt`；本轮最终调用与修订提示词见 `generation-log.json`，六张定向修订另存 `prompts/*-r1.txt`。
- 六张被修订的首轮图保留在各包 `review/v3-iterations/`；工具生成原件保持原位。
- 图片是概念参考预览。没有把本轮登记为最终美术验收、3D 完成或 Godot 接入。
- 已逐图目视检查主体、主要布局与剧情物件。无场景人物或人的倒影；档案室画框里的历史合影是需求指定的道具。未见有意排版的可读文字，书页 / 盒签仍有微小生成纹理。
- 尚不能把房间 SOP 的“≥3 张不同朝向”全部打勾：本清单包含近景 / 状态图，同向状态变化不等于新朝向。档案室、儿童房、客厅每组本轮仅两张空间视角；餐厅的第三张是桌面近景。旧版仅作氛围参照，开建仍需按 v1 补定布置。

## 逐图记录

| 文件 | 图片 | 原生尺寸 | 目视检查与剩余偏差 |
| --- | --- | --- | --- |
''' + '\n'.join(rows) + '\n')
    print(json.dumps({'count': len(items), 'copy_hashes_match': True,
                      'dimensions': sorted({f"{x['width']}x{x['height']}" for x in items}),
                      'gallery': str(OUT / 'index.html')}, ensure_ascii=False))


if __name__ == '__main__':
    main()
