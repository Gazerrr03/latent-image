# -*- coding: utf-8 -*-
"""Copy verified runtime evidence and build the local inspection review index."""
from pathlib import Path
import csv
import html
import json
import shutil
from PIL import Image

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "docs/验证/2026-10-20-物品检视"
COPIES = {
    "门框门闩性能-采样上下文.txt": "/tmp/dm-frame-latch-perf-context.txt",
    "门框门闩档案室行走.log": "/tmp/dm-frame-latch-walk.log",
    "门框门闩实际E与几何.log": "/tmp/dm-frame-latch-inspection.log",
    "门框门闩性能-并行干扰.log": "/tmp/dm-frame-latch-performance.log",
    "门框门闩内容检查.log": "/tmp/dm-frame-latch-content.log",
    "门框门闩通关-保护.log": "/tmp/dm-frame-latch-protect.log",
    "门框门闩通关-取代.log": "/tmp/dm-frame-latch-replace.log",
    "门框门闩大地图.log": "/tmp/dm-frame-latch-map.log",
    "门框刻痕现场.png": "/tmp/dm-frame-latch-hs_doorframe.png",
    "门闩线头现场.png": "/tmp/dm-frame-latch-hs_gh_latch.png",
    "笔记本门框刻痕.png": "/tmp/dm-notebook-ev_doorframe_l.png",
    "笔记本门闩线头.png": "/tmp/dm-notebook-ev_latch_thread.png",
    "新物件性能-独立采样.log": "/tmp/dm-inspection-perf-new-assets-independent.log",
    "字迹复查性能-复测.log": "/tmp/dm-inspection-perf-handwriting-repeat.log",
    "手写字形分离检查.log": "/tmp/dm-handwriting-glyph-check.log",
    "摊字接入-共用检视回归.log": "/tmp/dm-inspector-handwriting-regression.log",
    "摊字接入-内容检查.log": "/tmp/dm-spread-content.log",
    "摊字接入-通关保护.log": "/tmp/dm-spread-protect.log",
    "摊字接入-通关取代.log": "/tmp/dm-spread-replace.log",
    "摊字接入-大地图.log": "/tmp/dm-spread-map.log",
    "摊字接入-客房行走.log": "/tmp/dm-spread-walk.log",
    "五源字迹笔记本放大.png": "/tmp/dm-handwriting-spread-notebook-zoom.png",
    "五源字迹实物专项.log": "/tmp/dm-handwriting-spread.log",
    "五源字迹现场.png": "/tmp/dm-handwriting-spread-onsite.png",
    "五源字迹放大.png": "/tmp/dm-handwriting-spread-onsite-zoom.png",
    "五源字迹笔记本.png": "/tmp/dm-handwriting-spread-notebook.png",
    "暗房特写性能-独立采样.log": "/tmp/dm-inspection-perf-darkroom-independent.log",
    "授权补定-纸面检视.log": "/tmp/dm-handwriting-inspection.log",
    "授权补定-药柜检视.log": "/tmp/dm-authorized-cabinet.log",
    "授权补定-内容检查.log": "/tmp/dm-authorized-content.log",
    "授权补定-通关保护.log": "/tmp/dm-authorized-protect.log",
    "授权补定-通关取代.log": "/tmp/dm-authorized-replace.log",
    "签收单实物笔迹.png": "/tmp/dm-handwriting-ev_receipt.png",
    "账簿实物笔迹.png": "/tmp/dm-handwriting-ev_con_ledger.png",
    "降灵卡片实物笔迹.png": "/tmp/dm-handwriting-ev_seance_cards.png",
    "安布罗斯笔记实物笔迹.png": "/tmp/dm-handwriting-ev_amb_notes.png",
    "皮鞋实尺-修正前.log": "/tmp/dm-shoe-footprint-before.log",
    "皮鞋实尺-修正后.log": "/tmp/dm-shoe-footprint-after.log",
    "实尺修正-衣物回归.log": "/tmp/dm-native-scale-regression.log",
    "实尺修正-共用检视回归.log": "/tmp/dm-inspector-native-size.log",
    "花园固定痕迹E.log": "/tmp/dm-garden-inspection.log",
    "花园遮光布现场.png": "/tmp/dm-garden-hs_vent_louver.png",
    "花园鞋印现场.png": "/tmp/dm-garden-hs_vent_print.png",
    "笔记本遮光布.png": "/tmp/dm-notebook-ev_vent_cloth.png",
    "笔记本皮鞋印.png": "/tmp/dm-notebook-ev_vent_print.png",
    "花园行走.log": "/tmp/dm-inspection-walk-garden.log",
    "固定痕迹笔记本复查.log": "/tmp/dm-fixed-notebook-six.log",
    "固定复查共用检视回归.log": "/tmp/dm-inspector-fixed-replay.log",
    "笔记本盘底结晶.png": "/tmp/dm-notebook-ev_tray_crystal.png",
    "笔记本药柜灰圈.png": "/tmp/dm-notebook-ev_bottle_moved.png",
    "回廊E专项.log": "/tmp/dm-corridor-interaction.log",
    "回廊出口E.png": "/tmp/dm-corridor-hs_doorway.png",
    "回廊暗房门E.png": "/tmp/dm-corridor-hs_darkroom_door.png",
    "回廊第四椅E.png": "/tmp/dm-corridor-hs_chair4.png",
    "停显盘实物特写.log": "/tmp/dm-tray-inspection.log",
    "停显盘实物特写.png": "/tmp/dm-tray-inspection.png",
    "暗房行走.log": "/tmp/dm-inspection-walk-darkroom.log",
    "档案室照片检视.log": "/tmp/dm-archive-photo-inspection.log",
    "档案室手写08.png": "/tmp/dm-archive-photo-back.png",
    "药柜实物特写.log": "/tmp/dm-authorized-cabinet.log",
    "药柜实物特写.png": "/tmp/dm-cabinet-inspection.png",
    "检视-年度照片回归.log": "/tmp/dm-inspector-archive-regression.log",
    "衣物-年度照片回归.log": "/tmp/dm-native-archive-regression.log",
    "档案室行走.log": "/tmp/dm-inspection-walk-archive.log",
    "判定测试.log": "/tmp/dm-targeting-art.log",
    "检视运行测试.log": "/tmp/dm-inspector-page-test.log",
    "内容检查.log": "/tmp/dm-inspect-content-art.log",
    "通关-保护.log": "/tmp/dm-inspect-autoplay-protect-art.log",
    "通关-取代.log": "/tmp/dm-inspect-autoplay-replace-art.log",
    "动态照片检视.log": "/tmp/dm-photo-inspection.log",
    "合影小样背面.png": "/tmp/dm-photo-back.png",
    "合影小样正面-待替换.png": "/tmp/dm-photo-front.png",
    "独立物件复测.log": "/tmp/dm-native-repeat.log",
    "原家具实物拆分.log": "/tmp/dm-native-parts.log",
    "新物件性能-并行干扰.log": "/tmp/dm-native-perf-concurrent.log",
    "皮鞋正面检视.png": "/tmp/dm-native-shoes-front.png",
    "皮鞋鞋底检视.png": "/tmp/dm-native-shoes-sole.png",
    "少年毛衣检视.png": "/tmp/dm-native-sweater.png",
    "实际E键检视.log": "/tmp/dm-inspection-world.log",
    "衣柜开闭验证.log": "/tmp/dm-container-interaction.log",
    "细节照明性能.log": "/tmp/dm-inspection-perf-detail.log",
    "扩展场景性能.log": "/tmp/dm-inspection-perf-extended.log",
    "衣柜房行走.log": "/tmp/dm-inspection-walk-con.log",
    "温室行走.log": "/tmp/dm-inspection-walk-green.log",
    "大地图检查.log": "/tmp/dm-inspection-map.log",
    "逐对象判定.json": "/tmp/dm-interaction-objects.json",
    "逐对象判定.log": "/tmp/dm-interaction-objects.log",
    "检视性能-独立采样.log": "/tmp/dm-inspection-perf.log",
    "房间切换释放对照.log": "/tmp/dm-inspection-teardown-baseline.log",
    "真实记事本检视.png": "/tmp/dm-inspector-portable.png",
    "固定现场特写.png": "/tmp/dm-inspector-fixed.png",
    "信件正面.png": "/tmp/dm-inspector-letter-front.png",
    "信件背面.png": "/tmp/dm-inspector-letter-back.png",
}
for object_id, name in [("ev_ticket", "车票"), ("ev_clipping", "剪报"),
                        ("ev_con_ledger", "家用账簿"), ("ev_seance_cards", "降灵卡片")]:
    COPIES[name + "检视.png"] = f"/tmp/dm-inspector-{object_id}.png"

for hotspot in ["hs_draw_path", "hs_draw_boxes", "hs_draw_train", "hs_draw_family", "hs_draw_wall", "hs_gh_photos", "hs_gh_latch", "hs_se_cards", "hs_se_photo", "hs_se_gloves"]:
    COPIES[hotspot + "现场检视.png"] = f"/tmp/dm-world-{hotspot}.png"


def table(path):
    with (ROOT / path).open() as source:
        return list(csv.DictReader(source))


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    for name, source in COPIES.items():
        if Path(source).exists():
            shutil.copy2(source, OUT / name)
    hotspots = table("godot/content/story/hotspots.csv")
    entries = {row["hotspot"]: row for row in table("godot/content/visual/inspections.csv")}
    sheets = table("godot/content/visual/inspection_pages.csv")
    documents = {row["object"] for row in sheets}
    styles = {row["object"]: row["style"] for row in sheets}
    audit = {row["id"]: row for row in json.loads((OUT / "逐对象判定.json").read_text())}
    rows = ["# 物品资源与交互逐项清单", "",
            "本表区分实际资源、站位采样和最终验收。selectable 只证明找到有地面、角色站得下且无遮挡的选中位置，不等于已从出生点完整走到，也不证明每个边缘角度通过。", "",
            "| 热区 | 对象 | 当前资源 | 站位检查 | 仍需处理 |",
            "| --- | --- | --- | --- | --- |"]
    for hotspot in hotspots:
        entry = entries[hotspot["id"]]
        object_id = entry.get("object") or hotspot["evidence"]
        is_document = object_id in documents
        status = audit.get(hotspot["id"], {}).get("status", "回廊按层另查")
        edges = audit.get(hotspot["id"], {}).get("edge_checks", [])
        if edges:
            status += "；边界外6px可选 %d/4" % sum(e["status"] == "tolerated" for e in edges)
        resource = ("实物画作 / 正反面" if styles.get(object_id) == "drawing" else "实物照片 / 正反面" if styles.get(object_id) == "photo" else "独立文稿纸张 / 正反面") if is_document else (
            "真实独立网格" if entry["mode"] == "portable" else "现场特写 / 观察记录")
        todo = "实物观感终验" if is_document else (
            "默认角度与完整内容终验" if entry["mode"] == "portable" else "核对固定痕迹或便携物；便携物须补齐资源")
        if entry.get("notebook_asset", ""):
            resource += " / 笔记本实物现场复查"
        if hotspot["id"] in ["hs_doorway", "hs_darkroom_door", "hs_chair4"]:
            resource = "回廊原位动作入口 / 当前灰盒"
            log = OUT / "回廊E专项.log"
            status = "按层E专项通过" if log.exists() and "CORRIDOR_INTERACTION failures=0" in log.read_text() else "按层E专项待通过"
            todo = "逐层连续行走、边缘遮挡与最终场景观感；不把接口测试算作全关终验"
        if hotspot["id"] == "hs_handwriting":
            resource = "原位五份真实纸张 / 笔记本复用同一组合"
            todo = "各站位字迹可读性、放大范围与用户视觉终验"
        if hotspot["id"] in ["hs_photo_back", "hs_se_photo"]:
            todo += "；正面旧合影必须替换为最终美术"
        if status in ["missing", "blocked"]:
            todo += "；修复接口或容器交互"
        rows.append(f'| {hotspot["id"]} | {hotspot["label"]} | {resource} | {status} | {todo} |')
    (OUT / "物品资源清单.md").write_text("\n".join(rows) + "\n")

    manifest = json.loads((ROOT / "assets/3d/inspection/document-manifest.json").read_text())
    images = [("门框刻痕现场.png", "储物间门框 · 原位八道刻痕与 L"), ("笔记本门框刻痕.png", "门框复查 · 原木框、墙面和刻痕位置"), ("门闩线头现场.png", "门闩内侧 · 同源呢子线头"), ("笔记本门闩线头.png", "门闩复查 · 裁切原硬件与共享线头几何"), ("五源字迹现场.png", "第五章 · 原书桌上的五份真实字迹"), ("五源字迹放大.png", "现场滚轮放大 · 笔迹可读性审查"), ("五源字迹笔记本.png", "异地笔记本 · 相同实物复查"), ("五源字迹笔记本放大.png", "复查滚轮放大 · 原始字迹直接比较"), ("签收单实物笔迹.png", "药房签收单 · 用户授权品名与瓶数"), ("账簿实物笔迹.png", "账簿 · 断开的小写 t"), ("降灵卡片实物笔迹.png", "Salter 卡片 · 实物英文与中文阅读分离"), ("安布罗斯笔记实物笔迹.png", "安布罗斯笔记 · 既有文字的英文手写"), ("花园遮光布现场.png", "通风口 · 现场原位特写"), ("花园鞋印现场.png", "泥地 · 原位残缺鞋印"), ("笔记本遮光布.png", "笔记本 · 真实墙体、百叶与派生布面"), ("笔记本皮鞋印.png", "笔记本 · 原地形和鞋印裁切复查"), ("笔记本盘底结晶.png", "笔记本 · 原位三盘关系与盘底结晶复查"), ("笔记本药柜灰圈.png", "笔记本 · 同一药柜网格，标签与错位灰圈"), ("回廊出口E.png", "运行版回廊 · E推门入口，非最终场景美术"), ("回廊暗房门E.png", "运行版回廊 · E敲门入口"), ("回廊第四椅E.png", "运行版回廊 · 三声源找到后E坐下"), ("停显盘实物特写.png", "急停液盘 · 中间原盘的盘底结晶，C1-05状态"), ("档案室手写08.png", "档案室合影背面 · 固定年度序号08"), ("药柜实物特写.png", "药柜 · 挪开的瓶与原灰圈，标签继续调整"), ("合影小样背面.png", "小样背面 · 本局动态现代印字"), ("合影小样正面-待替换.png", "小样正面 · 当前来源待替换，非最终美术"), ("皮鞋正面检视.png", "皮鞋 · 实际 E 键拿起"), ("皮鞋鞋底检视.png", "翻转观察实际干泥鞋底"), ("少年毛衣检视.png", "少年毛衣 · 实际开柜与 E 键拿起"), ("信件正面.png", "笔记本中的实物信件"), ("信件背面.png", "信件独立背面"),
              ("车票检视.png", "车票"), ("剪报检视.png", "剪报"),
              ("家用账簿检视.png", "账簿正反面"), ("降灵卡片检视.png", "降灵卡片"),
              ("真实记事本检视.png", "原场景独立网格"), ("固定现场特写.png", "保留现场关系的特写")]
    images += [(hotspot + "现场检视.png", hotspot + " · 实际 E 键入口") for hotspot in ["hs_draw_path", "hs_draw_boxes", "hs_draw_train", "hs_draw_family", "hs_draw_wall", "hs_gh_photos", "hs_gh_latch", "hs_se_cards", "hs_se_photo", "hs_se_gloves"]]
    markup = '''<!doctype html><meta charset="utf-8"><title>物品检视 · 运行审查</title>
<style>body{margin:40px auto;max-width:1180px;padding:0 24px;background:#191816;color:#eee7dc;font:16px/1.7 system-ui}h1{font-weight:550}p{color:#c5bbab}main{display:grid;grid-template-columns:1fr 1fr;gap:24px}figure{margin:0;background:#24221f;padding:12px;border:1px solid #474137}img{width:100%;height:auto;display:block}figcaption{padding:10px 0}a{color:#d6b67e}.meta{font-size:13px;color:#b4aa9a}details{margin:18px 0;border-top:1px solid #474137;padding-top:12px}.papers{display:grid;grid-template-columns:repeat(4,1fr);gap:12px}.papers img{max-height:320px;object-fit:contain}@media(max-width:700px){main{grid-template-columns:1fr}.papers{grid-template-columns:1fr 1fr}}</style>
<h1>物品检视 · 实际运行审查</h1><p>状态：实施中，待逐物品和用户最终验收。下面是 Godot 实际渲染，不是设计效果图。阅读内容来自现有剧情表；原文、资源和验证边界见 <a href="进度与验收.md">进度与验收</a>。</p><main>'''
    for filename, label in images:
        dimensions = Image.open(OUT / filename).size if (OUT / filename).exists() else (0, 0)
        markup += f'<figure><a href="{filename}"><img src="{filename}" loading="lazy"></a><figcaption>{label}</figcaption><div class="meta">Godot 实际渲染 · {dimensions[0]} × {dimensions[1]} · 点击查看原图</div></figure>'
    markup += f'''</main><p>档案室与灵媒小样正面沿用当前照片，艾瑞斯仍为缩小成人的旧替代图；本轮编辑生成被服务拦截，没有可用输出。此项只验证原位照片和动态背面，不计为最终美术完成。</p><h2>逐物件的纸面资源</h2><p>{len(documents)} 种物件 / {len(sheets)} 张纸 / {len(manifest)} 个正反面（含文稿、画作与照片）。每张纸都有对应原文与原生像素尺寸，完整 SHA-256 见 <a href="../../../assets/3d/inspection/document-manifest.json">资源清单</a>。这些纸面物件已接入，尚不代表其余照片、药瓶、织物等线索完成。五张画使用内置 imagegen 编辑生成，原生 1448 × 1086；原图、逐图准确提示词、SHA-256 和候选状态见 <a href="../../../assets/2d/inspection/generated/manifest-v1.json">生成来源清单</a>。</p>'''
    for object_id in sorted(documents):
        markup += "<details><summary>" + html.escape(object_id) + '</summary><div class="papers">'
        for record in manifest:
            if Path(record["path"]).name.startswith(object_id + "_"):
                path = "../../../" + record["path"]
                markup += f'<figure><a href="{path}"><img src="{path}" loading="lazy"></a><figcaption>{html.escape(Path(path).name)}{" · 编号在运行时印于背面" if record.get("dynamic") else ""}</figcaption><div class="meta">{record["size"][0]} × {record["size"][1]} 原生像素</div></figure>'
        markup += "</div></details>"
    (OUT / "检视审查.html").write_text(markup)


if __name__ == "__main__":
    main()
