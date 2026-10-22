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
<<<<<<< HEAD
    "最终合影小样.png": "/tmp/dm-photo-front.png",
    "最终合影档案室.log": "/tmp/dm-final-archive-photo.log",
    "最终合影小样.log": "/tmp/dm-final-seance-photo.log",
    "最终合影性能.log": "/tmp/dm-final-photo-performance.log",
    "隔离交付导入.log": "/tmp/dm-staged-import3.log",
    "隔离交付内容检查.log": "/tmp/dm-staged-content.log",
    "隔离交付通关保护.log": "/tmp/dm-staged-protect.log",
    "隔离交付通关取代.log": "/tmp/dm-staged-replace.log",
    "隔离交付完整输入.log": "/tmp/dm-staged-inputs.log",
    "隔离交付回廊.log": "/tmp/dm-staged-corridor.log",
    "隔离交付笔记本.log": "/tmp/dm-staged-notebook.log",
    "隔离交付共用检视.log": "/tmp/dm-staged-inspector.log",
    "隔离交付大地图.log": "/tmp/dm-staged-map.log",
    "隔离交付行走.log": "/tmp/dm-staged-walk.log",
    "当前未打开检视退出对照.log": "/tmp/dm-inspection-teardown-current-baseline.log",
    "回廊挂钩笔记本.png": "/tmp/dm-notebook-ev_corridor_hook.png",
    "回廊圆圈笔记本.png": "/tmp/dm-notebook-ev_corridor_circle.png",
    "回廊内窗笔记本.png": "/tmp/dm-notebook-ev_corridor_window.png",
    "九处笔记本实物复查.log": "/tmp/dm-fixed-notebook-nine.log",
    "回廊复查性能.log": "/tmp/dm-corridor-review-performance.log",
    "回廊复查内容检查.log": "/tmp/dm-corridor-review-content.log",
    "回廊复查通关保护.log": "/tmp/dm-corridor-review-protect.log",
    "回廊复查通关取代.log": "/tmp/dm-corridor-review-replace.log",
    "回廊原位动作复测.log": "/tmp/dm-corridor-review-actions.log",
    "反复检视生命周期.log": "/tmp/dm-inspection-lifetime.log",
    "门开关逐状态.json": "/tmp/dm-door-switch-inputs.json",
    "门开关逐状态.log": "/tmp/dm-door-switch-inputs.log",
    "戒指盒实物检视.png": "/tmp/dm-ringbox-inspection.png",
    "戒指盒专项.log": "/tmp/dm-ringbox-inspection.log",
    "戒指盒实机专项.log": "/tmp/dm-ringbox-visible.log",
    "戒指盒性能.log": "/tmp/dm-ringbox-performance.log",
    "戒指盒共用检视回归.log": "/tmp/dm-ringbox-common-visible.log",
    "戒指盒单材质回归.log": "/tmp/dm-ringbox-native.log",
    "戒指盒内容检查.log": "/tmp/dm-ringbox-content.log",
    "戒指盒通关保护.log": "/tmp/dm-ringbox-protect.log",
    "戒指盒通关取代.log": "/tmp/dm-ringbox-replace.log",
    "账簿连续走近实机.png": "/tmp/dm-walk-con-room-visible-hs_con_ledger.png",
    "卧室连续走近实机.log": "/tmp/dm-walk-con-room-visible.log",
    "连续走近检视.json": "/tmp/dm-walk-to-hotspots-final.json",
    "连续走近检视.log": "/tmp/dm-walk-to-hotspots-final.log",
    "检视环境声.log": "/tmp/dm-inspection-ambient.log",
    "逐物件距离判定.log": "/tmp/dm-targeting-object-reach.log",
    "距离调整内容检查.log": "/tmp/dm-reach-content.log",
    "距离调整通关保护.log": "/tmp/dm-reach-protect.log",
    "距离调整通关取代.log": "/tmp/dm-reach-replace.log",
    "距离调整大地图.log": "/tmp/dm-reach-map.log",
    "距离调整卧室行走.log": "/tmp/dm-reach-walk.log",
    "逐物件E完整流程.json": "/tmp/dm-all-hotspot-inputs.json",
    "逐物件E完整流程.log": "/tmp/dm-ringbox-all-inputs.log",
    "相机抢门闩-修正前.log": "/tmp/dm-camera-latch-before.log",
    "相机门闩可视回归.log": "/tmp/dm-camera-latch-visual.log",
    "相机特写-判定修正.png": "/tmp/dm-all-input-hs_camera.png",
    "门闩特写-判定修正.png": "/tmp/dm-all-input-hs_gh_latch.png",
    "判定改动大地图.log": "/tmp/dm-dense-map.log",
    "判定改动暗房行走.log": "/tmp/dm-dense-walk.log",
    "密集候选判定.json": "/tmp/dm-dense-interaction.json",
    "密集候选判定.log": "/tmp/dm-reach-dense.log",
=======
    "密集候选判定.json": "/tmp/dm-dense-interaction.json",
    "密集候选判定.log": "/tmp/dm-dense-interaction.log",
>>>>>>> codex/snapshot-source-20261022-1
    "同分抢选-修正前.log": "/tmp/dm-targeting-ties-before.log",
    "薄墙穿透-修正前.log": "/tmp/dm-targeting-thin-wall-before.log",
    "判定-修正后.log": "/tmp/dm-targeting-thin-wall-after.log",
    "E键提示执行路由.log": "/tmp/dm-interaction-routing.log",
    "移动门扇遮挡路由.log": "/tmp/dm-moving-door-targeting.log",
    "当前衣柜判定回归.log": "/tmp/dm-dense-container.log",
<<<<<<< HEAD
    "当前回廊判定回归.log": "/tmp/dm-ringbox-corridor.log",
=======
    "当前回廊判定回归.log": "/tmp/dm-dense-corridor.log",
>>>>>>> codex/snapshot-source-20261022-1
    "判定改动内容检查.log": "/tmp/dm-dense-content.log",
    "判定改动通关-保护.log": "/tmp/dm-dense-protect.log",
    "判定改动通关-取代.log": "/tmp/dm-dense-replace.log",
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
    "逐对象判定.log": "/tmp/dm-dense-object-audit.log",
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
<<<<<<< HEAD
        if hotspot["scene"] == "ded_corridor":
            resource = "回廊专用原位动作 / 当前原生场景"
            log = OUT / "当前回廊判定回归.log"
            status = "按层E专项通过" if log.exists() and "CORRIDOR_INTERACTION failures=0" in log.read_text() else "按层E专项待通过"
            todo = "现场保留原位观察；笔记本同源实物复查已接入，待观感终验" if hotspot["id"] in ["hs_room_1", "hs_room_2", "hs_room_3"] else "逐层连续行走与最终场景观感；不把接口测试算作全关终验"
=======
        if hotspot["id"] in ["hs_doorway", "hs_darkroom_door", "hs_chair4"]:
            resource = "回廊原位动作入口 / 当前灰盒"
            log = OUT / "回廊E专项.log"
            status = "按层E专项通过" if log.exists() and "CORRIDOR_INTERACTION failures=0" in log.read_text() else "按层E专项待通过"
            todo = "逐层连续行走、边缘遮挡与最终场景观感；不把接口测试算作全关终验"
>>>>>>> codex/snapshot-source-20261022-1
        if hotspot["id"] == "hs_handwriting":
            resource = "原位五份真实纸张 / 笔记本复用同一组合"
            todo = "各站位字迹可读性、放大范围与用户视觉终验"
        if hotspot["id"] in ["hs_photo_back", "hs_se_photo"]:
<<<<<<< HEAD
            todo += "；四人侧后方新合影已接入，待用户观感终验"
=======
            todo += "；正面旧合影必须替换为最终美术"
>>>>>>> codex/snapshot-source-20261022-1
        if status in ["missing", "blocked"]:
            todo += "；修复接口或容器交互"
        rows.append(f'| {hotspot["id"]} | {hotspot["label"]} | {resource} | {status} | {todo} |')
    (OUT / "物品资源清单.md").write_text("\n".join(rows) + "\n")

    manifest = json.loads((ROOT / "assets/3d/inspection/document-manifest.json").read_text())
<<<<<<< HEAD
    images = [("最终合影小样.png", "新合影 · 四人、主位空隙与边缘面纱女人"), ("回廊挂钩笔记本.png", "回廊复查 · 原空挂钩、大衣与下方水渍"), ("回廊圆圈笔记本.png", "回廊复查 · 原地板磨痕"), ("回廊内窗笔记本.png", "回廊复查 · 原内窗与窗外走廊"), ("戒指盒实物检视.png", "戒指盒 · 原盒体与白缎内衬独立拿起"), ("相机特写-判定修正.png", "相机 · 贴合机身朝向的判定与局部照明"), ("门闩特写-判定修正.png", "门闩 · 检查相机后仍选中正确物件"), ("门框刻痕现场.png", "储物间门框 · 原位八道刻痕与 L"), ("笔记本门框刻痕.png", "门框复查 · 原木框、墙面和刻痕位置"), ("门闩线头现场.png", "门闩内侧 · 同源呢子线头"), ("笔记本门闩线头.png", "门闩复查 · 裁切原硬件与共享线头几何"), ("五源字迹现场.png", "第五章 · 原书桌上的五份真实字迹"), ("五源字迹放大.png", "现场滚轮放大 · 笔迹可读性审查"), ("五源字迹笔记本.png", "异地笔记本 · 相同实物复查"), ("五源字迹笔记本放大.png", "复查滚轮放大 · 原始字迹直接比较"), ("签收单实物笔迹.png", "药房签收单 · 用户授权品名与瓶数"), ("账簿实物笔迹.png", "账簿 · 断开的小写 t"), ("降灵卡片实物笔迹.png", "Salter 卡片 · 实物英文与中文阅读分离"), ("安布罗斯笔记实物笔迹.png", "安布罗斯笔记 · 既有文字的英文手写"), ("花园遮光布现场.png", "通风口 · 现场原位特写"), ("花园鞋印现场.png", "泥地 · 原位残缺鞋印"), ("笔记本遮光布.png", "笔记本 · 真实墙体、百叶与派生布面"), ("笔记本皮鞋印.png", "笔记本 · 原地形和鞋印裁切复查"), ("笔记本盘底结晶.png", "笔记本 · 原位三盘关系与盘底结晶复查"), ("笔记本药柜灰圈.png", "笔记本 · 同一药柜网格，标签与错位灰圈"), ("回廊出口E.png", "运行版回廊 · E推门入口，非最终场景美术"), ("回廊暗房门E.png", "运行版回廊 · E敲门入口"), ("回廊第四椅E.png", "运行版回廊 · 三声源找到后E坐下"), ("停显盘实物特写.png", "急停液盘 · 中间原盘的盘底结晶，C1-05状态"), ("档案室手写08.png", "档案室合影背面 · 固定年度序号08"), ("药柜实物特写.png", "药柜 · 挪开的瓶与原灰圈，标签继续调整"), ("合影小样背面.png", "小样背面 · 本局动态现代印字"), ("合影小样正面-待替换.png", "小样正面 · 四人侧后方新构图"), ("皮鞋正面检视.png", "皮鞋 · 实际 E 键拿起"), ("皮鞋鞋底检视.png", "翻转观察实际干泥鞋底"), ("少年毛衣检视.png", "少年毛衣 · 实际开柜与 E 键拿起"), ("信件正面.png", "笔记本中的实物信件"), ("信件背面.png", "信件独立背面"),
=======
    images = [("门框刻痕现场.png", "储物间门框 · 原位八道刻痕与 L"), ("笔记本门框刻痕.png", "门框复查 · 原木框、墙面和刻痕位置"), ("门闩线头现场.png", "门闩内侧 · 同源呢子线头"), ("笔记本门闩线头.png", "门闩复查 · 裁切原硬件与共享线头几何"), ("五源字迹现场.png", "第五章 · 原书桌上的五份真实字迹"), ("五源字迹放大.png", "现场滚轮放大 · 笔迹可读性审查"), ("五源字迹笔记本.png", "异地笔记本 · 相同实物复查"), ("五源字迹笔记本放大.png", "复查滚轮放大 · 原始字迹直接比较"), ("签收单实物笔迹.png", "药房签收单 · 用户授权品名与瓶数"), ("账簿实物笔迹.png", "账簿 · 断开的小写 t"), ("降灵卡片实物笔迹.png", "Salter 卡片 · 实物英文与中文阅读分离"), ("安布罗斯笔记实物笔迹.png", "安布罗斯笔记 · 既有文字的英文手写"), ("花园遮光布现场.png", "通风口 · 现场原位特写"), ("花园鞋印现场.png", "泥地 · 原位残缺鞋印"), ("笔记本遮光布.png", "笔记本 · 真实墙体、百叶与派生布面"), ("笔记本皮鞋印.png", "笔记本 · 原地形和鞋印裁切复查"), ("笔记本盘底结晶.png", "笔记本 · 原位三盘关系与盘底结晶复查"), ("笔记本药柜灰圈.png", "笔记本 · 同一药柜网格，标签与错位灰圈"), ("回廊出口E.png", "运行版回廊 · E推门入口，非最终场景美术"), ("回廊暗房门E.png", "运行版回廊 · E敲门入口"), ("回廊第四椅E.png", "运行版回廊 · 三声源找到后E坐下"), ("停显盘实物特写.png", "急停液盘 · 中间原盘的盘底结晶，C1-05状态"), ("档案室手写08.png", "档案室合影背面 · 固定年度序号08"), ("药柜实物特写.png", "药柜 · 挪开的瓶与原灰圈，标签继续调整"), ("合影小样背面.png", "小样背面 · 本局动态现代印字"), ("合影小样正面-待替换.png", "小样正面 · 当前来源待替换，非最终美术"), ("皮鞋正面检视.png", "皮鞋 · 实际 E 键拿起"), ("皮鞋鞋底检视.png", "翻转观察实际干泥鞋底"), ("少年毛衣检视.png", "少年毛衣 · 实际开柜与 E 键拿起"), ("信件正面.png", "笔记本中的实物信件"), ("信件背面.png", "信件独立背面"),
>>>>>>> codex/snapshot-source-20261022-1
              ("车票检视.png", "车票"), ("剪报检视.png", "剪报"),
              ("家用账簿检视.png", "账簿正反面"), ("降灵卡片检视.png", "降灵卡片"),
              ("真实记事本检视.png", "原场景独立网格"), ("固定现场特写.png", "保留现场关系的特写")]
    images += [(hotspot + "现场检视.png", hotspot + " · 实际 E 键入口") for hotspot in ["hs_draw_path", "hs_draw_boxes", "hs_draw_train", "hs_draw_family", "hs_draw_wall", "hs_gh_photos", "hs_gh_latch", "hs_se_cards", "hs_se_photo", "hs_se_gloves"]]
    markup = '''<!doctype html><meta charset="utf-8"><title>物品检视 · 运行审查</title>
<style>body{margin:40px auto;max-width:1180px;padding:0 24px;background:#191816;color:#eee7dc;font:16px/1.7 system-ui}h1{font-weight:550}p{color:#c5bbab}main{display:grid;grid-template-columns:1fr 1fr;gap:24px}figure{margin:0;background:#24221f;padding:12px;border:1px solid #474137}img{width:100%;height:auto;display:block}figcaption{padding:10px 0}a{color:#d6b67e}.meta{font-size:13px;color:#b4aa9a}details{margin:18px 0;border-top:1px solid #474137;padding-top:12px}.papers{display:grid;grid-template-columns:repeat(4,1fr);gap:12px}.papers img{max-height:320px;object-fit:contain}@media(max-width:700px){main{grid-template-columns:1fr}.papers{grid-template-columns:1fr 1fr}}</style>
<<<<<<< HEAD
<h1>物品检视 · 实际运行审查</h1><p><a href="完成核对.md">最终需求与证据逐项核对</a></p><p><a href="密集判定审查.html">E键密集候选、分辨率与遮挡审查</a></p><p>状态：实现及自动验证完成，等待用户观感验收。历史进度中的缺口以最新完成核对为准。下面是 Godot 实际渲染，不是设计效果图。阅读内容来自现有剧情表；原文、资源和验证边界见 <a href="进度与验收.md">进度与验收</a>。</p><main>'''
=======
<h1>物品检视 · 实际运行审查</h1><p><a href="密集判定审查.html">E键密集候选、分辨率与遮挡审查</a></p><p>状态：实施中，待逐物品和用户最终验收。下面是 Godot 实际渲染，不是设计效果图。阅读内容来自现有剧情表；原文、资源和验证边界见 <a href="进度与验收.md">进度与验收</a>。</p><main>'''
>>>>>>> codex/snapshot-source-20261022-1
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

    dense_path = OUT / "密集候选判定.json"
    if dense_path.exists():
        grouped = {}
        for record in json.loads(dense_path.read_text()):
            grouped.setdefault(record["id"], []).append(record)
        labels = {r["id"]: r["label"] for r in hotspots}
        dense_html = '<!doctype html><meta charset="utf-8"><title>E键判定审查</title><style>body{max-width:1160px;margin:36px auto;padding:0 24px;background:#191816;color:#eee7dc;font:16px/1.7 system-ui}a{color:#d6b67e}table{border-collapse:collapse;width:100%;font-size:14px}td,th{padding:10px;text-align:left;border-bottom:1px solid #474137}code{color:#c5bbab}</style><h1>E键密集候选与遮挡审查</h1>'
        dense_html += '<p>范围：46个普通目标，两个实际逻辑视口1280×720与1920×1080。每目标横向/纵向各17个瞄准点，合计3128点。使用真实关卡碰撞与当前候选物件；候选反序、旧目标资格与分辨率对应关系逐点检查。此为Godot无界面物理/输入自动验证，不是逐条人工试玩或全部连续路线证明。</p>'
        dense_html += '<p>修正了同分随列表换序抢选，以及2.5厘米余量使紧贴薄墙后的物品可被选中的漏洞。仅物件自身明确绑定的表面保留装配余量，其他遮挡保留0.1毫米数值误差。<a href="同分抢选-修正前.log">同分失败记录</a> · <a href="薄墙穿透-修正前.log">薄墙失败记录</a> · <a href="判定-修正后.log">修正后26项</a></p>'
        dense_html += '<p>另有三房间21项E输入路由、6项移动侧门遮挡、当前衣柜与回廊专项。<a href="E键提示执行路由.log">输入路由</a> · <a href="移动门扇遮挡路由.log">移动侧门</a> · <a href="当前衣柜判定回归.log">衣柜</a> · <a href="当前回廊判定回归.log">回廊</a> · <a href="密集候选判定.json">逐点原始数据</a></p>'
        dense_html += '<table><tr><th>物件</th><th>目标ID</th><th>两个视口中心命中</th><th>候选顺序稳定</th><th>仍有选择资格</th><th>分辨率选择一致</th></tr>'
        for id, pair in grouped.items():
            samples = [sample for r in pair for sample in r["samples"]]
            center = len(pair) == 2 and all(r["center_matches"] for r in pair)
            stable = all(sample["order_stable"] for sample in samples)
            eligible = all(sample["still_eligible"] for sample in samples)
            same = len(pair) == 2 and all(a["picked"] == b["picked"] for a,b in zip(pair[0]["samples"],pair[1]["samples"]))
            cells = [labels.get(id,id), id] + ["通过" if v else "未通过" for v in [center, stable, eligible, same]]
            dense_html += '<tr>' + ''.join('<td>'+html.escape(v)+'</td>' for v in cells) + '</tr>'
        dense_html += '</table><p>实际边界另采184点：138个容错选中、33个邻物优先、10个被真实实体遮挡、3个边界在视口外。未把后面三类强行计作容错成功，也未通过扩大实体碰撞来绕过墙或门。</p><p><a href="检视审查.html">返回实物与操作截图</a></p>'
<<<<<<< HEAD
        inputs_path = OUT / "逐物件E完整流程.json"
        if inputs_path.exists():
            flows = json.loads(inputs_path.read_text())
            dense_html += '<h2>逐物件完整输入流程</h2><p>按已验证站位放置角色，46个普通目标逐个注入E/F/Esc，再走Director与Inspector真实入口。打开对象ID、阅读、分层退出、关闭瞬间恢复相机/FOV、解冻、重复检视与单次记录均检查。角色退出后继续自然落地/视点平滑不算恢复失败；这仍不是从出生点连续走完路线的证明。<a href="逐物件E完整流程.log">逐项日志</a> · <a href="逐物件E完整流程.json">结果数据</a> · <a href="相机抢门闩-修正前.log">相机判定框抢选失败记录</a> · <a href="相机门闩可视回归.log">两物件实际渲染回归</a></p><table><tr><th>物件</th><th>实际对象打开</th><th>登记形态</th><th>恢复</th><th>再检视</th><th>单次记录</th></tr>'
            for flow in flows:
                values = [labels.get(flow["id"],flow["id"])] + ["通过" if flow[key] else "未通过" for key in ["opened","form","restored","reopened","evidence_once"]]
                dense_html += '<tr>'+''.join('<td>'+html.escape(value)+'</td>' for value in values)+'</tr>'
            dense_html += '</table><p>相机旧判定框未跟随机身−60°朝向，会在已检视资格集中抢选门闩；现按原机身尺寸与朝向加每侧2厘米余量，保留通用边缘容错。两件实际渲染仍需用户观感终验，普通物件新合影及生成来源见主审查页。</p>'
        walking_path = OUT / "连续走近检视.json"
        if walking_path.exists():
            walking = json.loads(walking_path.read_text())
            passed = sum(bool(r["ok"]) for r in walking["objects"])
            dense_html += f'<h2>从房间出生点连续走近</h2><p>{passed}/{len(walking["objects"])}项通过。每个房间只在出生点放置一次角色，之后使用原角色移动输入和碰撞走近，按真实E打开对应物件；门通过E开关。路线规划只读取碰撞，不禁用或移动家具。这是各房间内的自动行走，仍不等同人工手感验收或整条主线连续通关。<a href="连续走近检视.log">日志</a> · <a href="连续走近检视.json">原始结果</a></p>'
            dense_html += '<table><tr><th>物件</th><th>房间</th><th>走近并打开</th><th>实际行走米数</th><th>结果说明</th></tr>'
            for item in walking["objects"]:
                cells = [labels.get(item["id"], item["id"]), item["room"], "通过" if item["ok"] else "未通过", f'{item["walked_m"]:.2f}', item["reason"] or "正常"]
                dense_html += '<tr>' + ''.join('<td>'+html.escape(v)+'</td>' for v in cells) + '</tr>'
            dense_html += '</table><p>账簿单独采用2.65米表面距离，解决现有家具下从入口侧略超统一2.4米的问题；其他物件保持默认距离，遮挡仍有效。角色尺寸、家具与实体碰撞不变。<a href="账簿连续走近实机.png">账簿真实渲染</a> · <a href="卧室连续走近实机.log">卧室有界面复测</a></p>'
        dense_html += '<p>环境声专项：便携与固定检视、文字阅读、退出均保留同一循环播放器，播放位置继续前进，音量/总线静音不被改写。此为引擎播放状态验证，不代替扬声器听感。<a href="检视环境声.log">原始日志</a> · <a href="逐物件距离判定.log">距离规则回归</a></p>'
        controls_path = OUT / "门开关逐状态.json"
        if controls_path.exists():
            controls = json.loads(controls_path.read_text())
            passed = sum(bool(r["ok"]) for r in controls["controls"])
            dense_html += f'<h2>门、灯开关与序章闩门</h2><p>{passed}/{len(controls["controls"])}个状态通过，覆盖15个独立操作点。采用房间地面附近、容得下全高角色的无遮挡站位；按真实E，再按真实E恢复。检查提示对象、状态改变、按键回声和其他门/灯未被误操作。C0-11/C0-13的闩门必须显示对应原剧情提示并保持关闭。此为逐点输入验证，未声称所有门之间的连续步行路线。<a href="门开关逐状态.log">日志</a> · <a href="门开关逐状态.json">原始数据</a></p><table><tr><th>操作点</th><th>镜号</th><th>站位</th><th>E动作</th><th>不误操作其他点</th><th>恢复</th></tr>'
            for control in controls["controls"]:
                cells = [control["name"], control["shot"]] + ["通过" if control[k] else "未通过" for k in ["stand","action","isolated","restored"]]
                dense_html += '<tr>' + ''.join('<td>'+html.escape(v)+'</td>' for v in cells) + '</tr>'
            dense_html += '</table>'
=======
>>>>>>> codex/snapshot-source-20261022-1
        (OUT / "密集判定审查.html").write_text(dense_html)



if __name__ == "__main__":
    main()
