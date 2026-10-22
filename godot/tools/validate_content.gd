extends SceneTree
## 内容检查：核对所有表格与文件是否互相对得上，生成一份中文检查报告。
## 用法：godot --headless --path godot --script res://tools/validate_content.gd
## 报告写到仓库根目录的“检查报告.md”。退出码：0 = 没有错误（可能有提醒），1 = 有错误。
## 队友可以直接双击仓库根目录的“检查内容.command”。

const DB := preload("res://core/content_db.gd")
const Actions := preload("res://core/actions.gd")
const STORY := "res://content/story/"
const SPACE := "res://content/space/"
const AUDIO := "res://content/audio/"
const AI := "res://content/ai/"
const VISUAL := "res://content/visual/"
## 每一章允许的渗漏等级（docs/02 第 9.2 节；EP = 尾声）
const NODE_LEAK := {"C0": 0, "C1": 0, "C2": 0, "C3": 1, "C4": 1, "C5": 2, "C6": 3, "C7": 4, "EP": 4}
## 禁用词在这些章节解禁（终局与尾声明确揭示世界观）
const REVEAL_NODES := ["C7", "EP"]
const LAYOUT_TYPES := ["家具", "可检查物件", "机位", "灯光", "出生点", "人物"]

## 每条问题：{level: 错误/提醒, table, where, what, fix}
var issues: Array = []
var fx_presets := {}
var footage := {}
var music := {}
## 任务表：组 -> 行数组
var quests := {}
## 关卡进度（纵切面），写进检查报告
var level_rows: Array = []
## 人工搭的关卡场景：房间 id -> 从场景里读出的名字（机位、物件、人物、小物件占位）
var levels := {}
## 小物件规格（从关卡占位方块读出），写进检查报告给美术
var prop_specs: Array = []


func err(table: String, where: String, what: String, fix := "") -> void:
	issues.append({"level": "错误", "table": table, "where": where, "what": what, "fix": fix})


func warn(table: String, where: String, what: String, fix := "") -> void:
	issues.append({"level": "提醒", "table": table, "where": where, "what": what, "fix": fix})


func _init() -> void:
	var shots := DB.load_table(STORY + "shots.csv")
	var hotspots := DB.index_by(DB.load_table(STORY + "hotspots.csv"), "id")
	var evidence := DB.index_by(DB.load_table(STORY + "evidence.csv"), "id")
	var links := DB.group_by(DB.load_table(STORY + "links.csv"), "group")
	var ann := DB.group_by(DB.load_table(STORY + "annotations.csv"), "set_id")
	var lines := DB.group_by(DB.load_table(STORY + "lines.csv"), "set_id")
	var chars := DB.load_table(STORY + "characters.csv")
	var rooms := DB.index_by(DB.load_table(SPACE + "rooms.csv"), "id")
	var layout_rows := DB.load_table(SPACE + "layout.csv")
	var layout := DB.group_by(layout_rows, "room")
	var sounds := DB.index_by(DB.load_table(AUDIO + "sounds.csv"), "id")
	music = DB.index_by(DB.load_table(AUDIO + "music.csv"), "id")
	quests = DB.group_by(DB.load_table(STORY + "quests.csv"), "group")
	var props := DB.index_by(DB.load_table(VISUAL + "props.csv"), "id")
	_check_inspection_assets(hotspots, evidence)
	for rid in rooms:
		var lv := _scan_level(rid)
		if not lv.is_empty():
			levels[rid] = lv
	var words := DB.load_table(AI + "wordlists.csv")
	fx_presets = DB.index_by(DB.load_table(VISUAL + "fx.csv"), "preset")
	footage = DB.group_by(DB.load_table(VISUAL + "footage.csv"), "clip")
	for clip in footage:
		for row in footage[clip]:
			var where := "%s / 第 %s 行" % [clip, row.get("seq", "?")]
			if not row.get("mode", "") in ["警告卡", "档案卡", "摄像机", "雪花"]:
				err("影像片段表", where, "样式只能是 警告卡 / 档案卡 / 摄像机 / 雪花，现在是“%s”" % row.get("mode", ""))
			var img: String = row.get("image", "")
			if img != "" and not FileAccess.file_exists("res://art/footage/" + img):
				warn("影像片段表", where, "图片 art/footage/%s 还没交付，播放时显示占位文字" % img)
			if row.get("fx", "") != "" and not fx_presets.has(row["fx"]):
				err("影像片段表", where, "滤镜预设“%s”不在滤镜表里" % row["fx"])
			if not str(row.get("duration", "3")).is_valid_float():
				err("影像片段表", where, "停留时间不是数字")
	for lv in 5:
		if not fx_presets.has("L%d" % lv):
			err("滤镜表", "L%d" % lv, "缺少渗漏等级 L%d 的默认滤镜" % lv, "滤镜表必须有 L0—L4 五行")
	for pr in fx_presets.values():
		for k in pr:
			if k in ["preset", "tint", "note"]:
				continue
			if pr[k] != "" and not str(pr[k]).is_valid_float():
				err("滤镜表", pr["preset"], "%s 不是数字" % k)

	_check_import_files()

	# ── 镜头表 ──
	var ids := {}
	for r in shots:
		var id: String = r.get("shot_id", "")
		if id == "":
			err("镜头表", "某一行", "没有填镜号", "每行第一列必须填镜号，例如 C3-02")
		elif ids.has(id):
			err("镜头表", id, "镜号重复", "改成一个没用过的镜号")
		ids[id] = r
	var cur_room := ""
	for i in shots.size():
		var r: Dictionary = shots[i]
		var id: String = r["shot_id"]
		var room: String = r.get("scene", "")
		if room != "":
			cur_room = room
		var mode: String = r.get("mode", "")
		if room != "" and not rooms.has(room):
			err("镜头表", id, "房间“%s”不在房间登记表里" % room, "先在房间登记表加这个房间，或改成已有的房间编号")
		if not mode in ["", "camera", "walk"]:
			err("镜头表", id, "模式只能填 camera（镜头）或 walk（行走），现在是“%s”" % mode)
		var cam: String = r.get("camera", "")
		if cam != "" and levels.has(room):
			if not levels[room]["cams"].has(cam):
				warn("镜头表", id, "关卡场景 levels/%s.tscn 里没有机位 cam_%s，会用默认机位" % [room, cam], "在关卡场景里加一个 Camera3D，命名为 cam_%s" % cam)
		elif cam != "" and room != "" and not _has_layout(layout, room, "机位", cam):
			warn("镜头表", id, "机位“%s”在房间布局表的 %s 里找不到，会用默认机位" % [cam, room], "在房间布局表给这个房间加一行“机位”")
		_check_sound_spec("镜头表", id, str(r.get("sound", "")), sounds)
		_check_next(r, i, shots, ids)
		for a in Actions.parse(r.get("actions", "")):
			_check_action(id, a, mode, cur_room, hotspots, evidence, links, ann, lines, layout)

	# ── 线索 ──
	for h in hotspots.values():
		_check_sound_spec("可检查物件表", h["id"], str(h.get("sound", "")), sounds)
		var fc: String = h.get("footage", "")
		if fc != "" and not footage.has(fc):
			err("可检查物件表", h["id"], "影像片段“%s”不在影像片段表里" % fc)
		var e: String = h.get("evidence", "")
		if e != "" and not evidence.has(e):
			err("可检查物件表", h["id"], "给出的证据“%s”不在证据表里" % e, "在证据表加这张卡片")
	for g in links:
		for p in links[g]:
			if p.get("result", "") != "" and not evidence.has(p["result"]):
				err("连线规则表", "连线组 " + g, "连对后得到的推论“%s”不在证据表里" % p["result"])
			for k in ["a", "b"]:
				if not evidence.has(p.get(k, "")):
					err("连线规则表", "连线组 " + g, "证据“%s”不在证据表里" % p.get(k, ""))

	# ── 人物 ──
	for c in chars:
		var n: String = c.get("name", "")
		var st: String = c.get("status", "")
		if not st in ["侦探", "人物", "死者", "其他"]:
			err("人物表", n, "状态只能填 侦探 / 人物 / 死者 / 其他，现在是“%s”" % st)
		var cm: String = c.get("model", "")
		if cm != "" and not FileAccess.file_exists(cm if cm.begins_with("res://") else "res://" + cm):
			err("人物表", n, "模型文件 %s 不存在" % cm, "检查路径，例如 res://art/characters/char_grey.glb")
		if c.get("room", "") != "" and not rooms.has(c["room"]):
			err("人物表", n, "所在房间“%s”不在房间登记表里" % c["room"])
		elif levels.has(c.get("room", "")) and not levels[c["room"]]["chr"].has(n):
			warn("人物表", n, "所在房间 %s 已有关卡场景，但场景里没有 chr_%s，这个人不会出现" % [c["room"], n], "在关卡场景里放一个空节点（Marker3D），命名为 chr_%s" % n)
	for room in levels:
		var people: Array = levels[room]["chr"].keys().filter(func(p): return p != "镜中人形")
		if people.size() > 1:
			warn("关卡场景", room, "这个房间放了 %d 个人物；同一画面里只应有一个人" % people.size(), "把其他人移到别的房间，或先隐藏、再用 reveal 轮流出现")
	# 同一个房间里最多放一个人：这些人物从不同时出现在同一画面里（docs/02 第 7 节）
	for room in layout:
		if levels.has(room):
			continue
		var people: Array = layout[room].filter(func(row): return row.get("type", "") == "人物" and row.get("id", "") != "镜中人形")
		if people.size() > 1:
			warn("房间布局表", room, "这个房间放了 %d 个人物；同一画面里只应有一个人" % people.size(), "把其他人移到别的房间，或用 hidden + reveal 轮流出现")

	# ── 空间：有关卡场景的房间以场景为准；其余房间暂用灰盒（房间布局表） ──
	for room in levels:
		var lv: Dictionary = levels[room]
		if layout.has(room):
			warn("房间布局表", room, "这个房间已有关卡场景 levels/%s.tscn，布局表里的 %d 行不再生效" % [room, layout[room].size()], "确认场景搭好后，删掉布局表里这个房间的行")
		if not lv["spawn"]:
			warn("关卡场景", room, "场景里没有 spawn，玩家会出生在原点", "放一个空节点（Marker3D），命名为 spawn，朝向 -z 是玩家面朝的方向")
		for h in lv["hs"]:
			if not hotspots.has(h):
				warn("关卡场景", "%s / %s" % [room, h], "这个可检查物件在可检查物件表里没有描述", "在可检查物件表补一行，写玩家看到什么")
		for pid in lv["props"]:
			var size = lv["props"][pid]
			var row: Dictionary = props.get(pid, {})
			var file: String = row.get("model", "")
			var state := "未登记" if row.is_empty() else ("待交付" if file == "" or not FileAccess.file_exists(file) else "已替换")
			prop_specs.append({"id": pid, "name": row.get("name", ""), "room": room, "size": size, "state": state})
			if row.is_empty():
				warn("模型资产表", pid, "关卡 %s 里有这个小物件占位，但模型资产表还没登记" % room, "在模型资产表加一行，id 写 %s" % pid)
	for pid in props:
		var file: String = props[pid].get("model", "")
		if not pid.begins_with("prop_"):
			err("模型资产表", pid, "id 必须以 prop_ 开头，和关卡里的占位节点同名")
		if file != "" and not FileAccess.file_exists(file):
			err("模型资产表", pid, "模型文件 %s 不存在" % file, "检查路径，例如 res://art/props/teacup.glb")
		if not prop_specs.any(func(p): return p["id"] == pid):
			warn("模型资产表", pid, "还没有哪个关卡放了这个物件的占位", "在关卡场景里放一个 CSGBox3D，命名为 %s" % pid)
	for row in layout_rows:
		var room: String = row.get("room", "")
		var where := "%s / %s" % [room, row.get("id", row.get("type", ""))]
		if not rooms.has(room):
			err("房间布局表", where, "房间“%s”不在房间登记表里" % room)
		var t: String = row.get("type", "")
		if not t in LAYOUT_TYPES:
			err("房间布局表", where, "类型只能是 %s，现在是“%s”" % ["、".join(PackedStringArray(LAYOUT_TYPES)), t])
		for k in ["x", "y", "z"]:
			if not str(row.get(k, "")).is_valid_float():
				err("房间布局表", where, "%s 坐标不是数字" % k)
		if t == "可检查物件" and not hotspots.has(row.get("id", "")):
			warn("房间布局表", where, "这个可检查物件在可检查物件表里没有描述", "在可检查物件表补一行，写玩家看到什么")
	for id in rooms:
		if not levels.has(id) and not layout.has(id):
			err("房间登记表", id, "既没有关卡场景，也没有灰盒布局", "在 Godot 里搭 levels/%s.tscn" % id)
	# ── 门的说法表：话不空，起止镜号存在且先后正确（门名对不对要进游戏看：准星对着门有没有“推门”提示）──
	for row in DB.load_table(STORY + "doors.csv"):
		var where := String(row.get("door", ""))
		if where == "" or String(row.get("text", "")) == "":
			err("门的说法表", where, "door 和 text 都不能空")
		for k in ["from", "until"]:
			var v: String = row.get(k, "")
			if v != "" and not shots.map(func(r): return r.get("shot_id", "")).has(v):
				err("门的说法表", where, "%s 写的镜号 %s 不在镜头表里" % [k, v], "写成镜头表 shot_id 列里的镜号，或留空")
	# ── 房间状态表：房间在登记表里、类型合法、起止镜号存在且先后正确 ──
	var shot_ids := shots.map(func(r): return r.get("shot_id", ""))
	for row in DB.load_table(SPACE + "room_states.csv"):
		var where := "%s / %s" % [row.get("room", ""), row.get("layer", "")]
		if not rooms.has(row.get("room", "")):
			err("房间状态表", where, "房间“%s”不在房间登记表里" % row.get("room", ""))
		if not row.get("kind", "") in ["状态层", "开关"]:
			err("房间状态表", where, "kind 只能是 状态层 或 开关，现在是“%s”" % row.get("kind", ""))
		if row.get("layer", "") == "":
			err("房间状态表", where, "layer 不能空")
		for k in ["from", "until"]:
			var v: String = row.get(k, "")
			if v != "" and not shot_ids.has(v):
				err("房间状态表", where, "%s 写的镜号 %s 不在镜头表里" % [k, v], "写成镜头表 shot_id 列里的镜号，或留空")
		var lvs: Dictionary = levels.get(row.get("room", ""), {})
		if not lvs.is_empty() and not lvs["names"].has("层·" + String(row.get("layer", ""))):
			warn("房间状态表", where, "关卡场景 levels/%s.tscn 里没有节点“层·%s”" % [row.get("room", ""), row.get("layer", "")], "在关卡场景里加一个名为 层·%s 的节点（状态层的 glTF 实例或一组灯）" % row.get("layer", ""))
		var a_: String = row.get("from", ""); var b_: String = row.get("until", "")
		if a_ != "" and b_ != "" and shot_ids.find(a_) >= shot_ids.find(b_):
			err("房间状态表", where, "from（%s）不在 until（%s）之前" % [a_, b_])

	# ── 任务表（自由探索） ──
	var shot_set := {}
	for r in shots:
		shot_set[r.get("shot_id", "")] = true
	var quest_ids := {}
	for g in quests:
		for q in quests[g]:
			quest_ids[q.get("id", "")] = true
	var map_rooms := ["hall", "dining", "seance", "archive", "child_room", "guest_room", "darkroom", "greenhouse", "garden", "manor"]
	for g in quests:
		var exits := 0
		for q in quests[g]:
			var qid: String = q.get("id", "")
			var t: String = q.get("trigger", "")
			if t.begins_with("talk:"):
				var who := t.trim_prefix("talk:").get_slice("@", 0)
				var rid := t.get_slice("@", 1)
				if not t.contains("@") or not map_rooms.has(rid):
					err("任务表", qid, "talk 要写成 talk:人名@房间，房间是庄园大地图里的房间（%s）" % "、".join(PackedStringArray(map_rooms)))
				elif levels.has(rid) and not levels[rid]["names"].has("chr_" + who):
					err("任务表", qid, "关卡场景 levels/%s.tscn 里没有 chr_%s，玩家找不到这个人" % [rid, who], "在关卡场景里放一个站位节点 chr_%s" % who)
			elif t.begins_with("enter:"):
				if not map_rooms.has(t.trim_prefix("enter:")):
					err("任务表", qid, "enter 的房间“%s”不在庄园大地图里" % t.trim_prefix("enter:"))
			elif t.begins_with("door:"):
				pass  # 门是模型里的节点，运行时找不到会提醒
			elif not hotspots.has(t):
				err("任务表", qid, "trigger“%s”看不懂" % t, "写 talk:人名@房间、enter:房间、door:门的节点名，或可检查物件表里的 hs_ 编号")
			for k in ["shot", "until"]:
				var v: String = q.get(k, "")
				if v != "" and not shot_set.has(v):
					err("任务表", qid, "%s 写的镜号 %s 不在镜头表里" % [k, v])
			var req: String = q.get("require", "")
			if req != "":
				exits += 1
			for part in req.split("|", false):
				if part.strip_edges() == "全部":
					continue  # 这一组能拿到线索的任务都做完（线索收齐，docs/01 第 4 节）
				var ids_ := part.get_slice(":", 1) if part.contains(":") else part
				for x in ids_.split(",", false):
					if not quest_ids.has(x.strip_edges()):
						err("任务表", qid, "require 里的任务 %s 不存在" % x.strip_edges())
		if exits == 0:
			err("任务表", g, "这一组没有写 require 的任务，探索永远结束不了", "加一行“回客房”之类的收尾任务，require 写要先完成的任务")

	# ── 声音 ──
	for set_id in lines:
		for row in lines[set_id]:
			_check_sound_spec("台词表", set_id, str(row.get("sound", "")), sounds)
	var steps := DB.index_by(DB.load_table(AUDIO + "footsteps.csv"), "room")
	for room_id in steps:
		if not rooms.has(room_id):
			err("脚步表", room_id, "房间“%s”不在房间登记表里" % room_id)
		if not sounds.has(String(steps[room_id].get("sound", ""))):
			err("脚步表", room_id, "脚步声“%s”不在音效表里" % steps[room_id].get("sound", ""))
	var missing_files := 0
	for s in sounds.values():
		var f: String = s.get("file", "")
		if s["id"] == "silence":
			continue
		if f == "":
			missing_files += 1
		elif not FileAccess.file_exists("res://audio/" + f):
			err("音效表", s["id"], "文件 audio/%s 不存在" % f, "检查文件名是否一致，包括扩展名")
	for m in music.values():
		if not FileAccess.file_exists("res://audio/music/" + String(m.get("file", ""))):
			err("配乐表", m["id"], "文件 audio/music/%s 不存在" % m.get("file", ""), "把 .ogg 放进 godot/audio/music/，文件名与表里一致")
	if missing_files > 0:
		warn("音效表", "全表", "%d / %d 个声音还没有文件（游戏里会静音）" % [missing_files, sounds.size()])

	# ── 词表：玩家看到的文字里，穿帮词是否出现得太早 ──
	_check_words(words, shots, hotspots, links, ann, lines, evidence)

	_level_report(shots, rooms, sounds, ann, lines, footage)
	_report(shots.size(), hotspots.size(), evidence.size(), chars.size(), rooms.size(), layout_rows.size(), sounds.size(), words.size())


## 检视资源也纳入内容检查，不能只验证旧剧情表而漏掉物品正反面和分页。
func _check_inspection_assets(hotspots: Dictionary, evidence: Dictionary) -> void:
	var seen := {}
	var inspected_objects := {}
	var label_ids := {}
	for label in DB.load_table(VISUAL + "inspection_labels.csv"):
		var id: String = label.get("id", "")
		if not hotspots.has(id) or label_ids.has(id):
			err("物品标签表", id, "热区不存在或标签重复")
		label_ids[id] = true
		var expected: String = label.get("expected_liquid_colour", "")
		if expected == "" or not label.get("text", "").contains(expected):
			err("物品标签表", id, "实物标签必须显示登记的应有液色")
		if label.get("source", "") == "":
			err("物品标签表", id, "标签缺少内容依据")
	for row in DB.load_table(VISUAL + "inspections.csv"):
		var id: String = row.get("hotspot", "")
		if seen.has(id) or not hotspots.has(id):
			err("物品检视表", id, "热区重复或不存在")
		seen[id] = true
		if row.get("object", "") != "":
			inspected_objects[row["object"]] = true
		var replacement: String = row.get("replacement_asset", "")
		if replacement != "" and (not ResourceLoader.exists(replacement) or not load(replacement) is PackedScene):
			err("物品检视表", id, "局部替换资源不存在或无法加载：" + replacement)
		if not row.get("mode", "") in ["portable", "fixed"]:
			err("物品检视表", id, "mode 必须是 portable 或 fixed")
		if row.get("asset_fit", "") not in ["", "native"]:
			err("物品检视表", id, "asset_fit 必须为空或 native")
		if row.get("occlusion", "") not in ["", "solid"]:
			err("物品检视表", id, "occlusion 必须为空或 solid")
		for flag in ["start_back", "world_document"]:
			if row.get(flag, "") not in ["", "1"]:
				err("物品检视表", id, flag + " 必须为空或 1")
		if row.get("world_document", "") == "1" and (row.get("mesh", "") == "" or row.get("asset", "") == "" or row.get("world_rotation", "").split(",").size() != 3):
			err("物品检视表", id, "原位文稿需要原网格、实物场景与三个旋转角")
		var notebook_asset: String = row.get("notebook_asset", "")
		if notebook_asset != "":
			if not ResourceLoader.exists(notebook_asset) or not load(notebook_asset) is PackedScene:
				err("物品检视表", id, "现场复查实物场景无法加载：" + notebook_asset)
			else:
				# 组合实物可以包含不单独收集的原文页，例如格雷自己的笔记。
				# 只有场景确实引用的纸张才能成为合法对象，避免白名单放过孤立资源。
				var assembly: Node = load(notebook_asset).instantiate()
				var pending: Array[Node] = [assembly]
				while not pending.is_empty():
					var part: Node = pending.pop_back()
					if part.get_script() == preload("res://world/inspection_document.gd"):
						inspected_objects[part.object_id] = true
					pending.append_array(part.get_children())
				assembly.free()
			if not row.get("notebook_span", "").is_valid_float() or float(row.get("notebook_span", "0")) <= 0:
				err("物品检视表", id, "现场复查构图范围必须为正数")
			for key in ["notebook_center", "notebook_rotation"]:
				var parts: PackedStringArray = row.get(key, "").split(",")
				if parts.size() != 3 or not Array(parts).all(func(value): return value.is_valid_float()):
					err("物品检视表", id, key + " 必须是三个数字")
		var asset: String = row.get("asset", "")
		if asset != "" and (not ResourceLoader.exists(asset) or not load(asset) is PackedScene):
			err("物品检视表", id, "独立实物场景不存在或无法加载：" + asset)
		if row.get("mode", "") == "portable" and asset == "" and row.get("mesh", "") == "":
			err("物品检视表", id, "便携物品没有实物场景或原网格")
	for id in hotspots:
		if not seen.has(id):
			err("物品检视表", id, "缺少该物件的检视类型登记")
	var documents := DB.group_by(DB.load_table(VISUAL + "inspection_pages.csv"), "object")
	for id in documents:
		if not evidence.has(id) and not inspected_objects.has(id):
			err("物品原文页表", id, "原物件未对应证据或检视对象")
		var rows: Array = documents[id]
		var pages := {}
		for row in rows:
			if row.get("handwriting", "") not in ["", "detached_t"]:
				err("物品原文页表", id, "handwriting 必须为空或 detached_t")
			if row.get("handwriting", "") != "" and row.get("surface_front", "") == "":
				err("物品原文页表", id, "笔迹物件须提供可核对的实物原文 surface_front")
			if row.get("dynamic_back", "") not in ["", "1"]:
				err("物品原文页表", id, "dynamic_back 必须为空或 1")
			if row.get("dynamic_back", "") == "1" and (not row.get("back", "").contains("{容器号}") or row.get("back_image", "") != ""):
				err("物品原文页表", id, "动态背面必须用容器号模板且不能混入静态背图")
			var index: String = row.get("page", "")
			if not index.is_valid_int() or pages.has(index) or int(index) < 0:
				err("物品原文页表", id, "页码须从 0 开始、不重复")
			pages[index] = true
			if float(row.get("width", "0")) <= 0 or float(row.get("height", "0")) <= 0:
				err("物品原文页表", id, "实物尺寸必须大于 0")
			for side in ["front", "back"]:
				var texture := "res://art/props/inspection/%s_%s_%s.png" % [id, index, side]
				if not ResourceLoader.exists(texture):
					err("物品原文页表", id, "缺少纸张纹理：" + texture)
		for i in rows.size():
			if not pages.has(str(i)):
				err("物品原文页表", id, "页码不连续")
		var asset := "res://art/props/inspection/%s.tscn" % id
		if not ResourceLoader.exists(asset) or not load(asset) is PackedScene:
			err("物品原文页表", id, "缺少对应实物场景：" + asset)


## 读关卡场景里按约定命名的节点；没有场景返回空字典
func _scan_level(id: String) -> Dictionary:
	var path := DB.level_path(id)
	if not ResourceLoader.exists(path):
		return {}
	var ps := load(path) as PackedScene
	if ps == null:
		err("关卡场景", id, "levels/%s.tscn 打不开" % id, "在 Godot 编辑器里打开它，看报什么错")
		return {}
	var root := ps.instantiate()
	var d := {"cams": {}, "hs": {}, "chr": {}, "props": {}, "names": {}, "spawn": false}
	var part_materials := {}
	var stack: Array = [root]
	var hotspot_pattern := RegEx.new()
	hotspot_pattern.compile("\\bhs_[a-z0-9_]+\\b")
	while not stack.is_empty():
		var n: Node = stack.pop_back()
		stack.append_array(n.get_children())
		var nm := String(n.name)
		d["names"][nm] = true
		if nm == "spawn":
			d["spawn"] = true
		elif nm.begins_with("cam_"):
			d["cams"][nm.trim_prefix("cam_")] = true
		elif nm.begins_with("hs_"):
			d["hs"][nm] = true
		elif nm.begins_with("chr_"):
			d["chr"][nm.trim_prefix("chr_")] = true
			d["names"][nm.trim_prefix("chr_")] = true
		elif nm.begins_with("prop_"):
			d["props"][nm] = n.size if n is CSGBox3D else (n.mesh.get_aabb().size if n is MeshInstance3D and n.mesh else null)
		if n is MeshInstance3D:
			part_materials[nm] = []
			for surface in n.mesh.get_surface_count():
				var material: Material = n.mesh.surface_get_material(surface)
				if material != null:
					part_materials[nm].append(material.resource_name)
			var matches := hotspot_pattern.search_all(nm)
			if matches.size() == 1:
				d["hs"][matches[0].get_string()] = true
	for row in DB.load_table(VISUAL + "inspections.csv"):
		if row.get("mesh", "") != "" and d["names"].has(row["mesh"]):
			d["hs"][row["hotspot"]] = true
			for material_name in row.get("part_material", "").split("|", false):
				if not material_name in part_materials.get(row["mesh"], []):
					err("物品检视表", row["hotspot"], "原网格中不存在该物件材质面：" + material_name)
			if row.get("layer", "") != "":
				d["names"]["层·" + row["layer"]] = true
	root.free()
	return d


func _has_layout(layout: Dictionary, room: String, type: String, id: String) -> bool:
	for row in layout.get(room, []):
		if row.get("type", "") == type and row.get("id", "") == id:
			return true
	return false


func _check_next(r: Dictionary, i: int, shots: Array, ids: Dictionary) -> void:
	var id: String = r["shot_id"]
	var n: String = r.get("next", "").strip_edges()
	var targets: Array = []
	if n == "":
		if i + 1 < shots.size():
			var nxt: Dictionary = shots[i + 1]
			if r.get("line", "*") not in ["", "*"] and nxt.get("line", "*") != r.get("line", "*"):
				warn("镜头表", id, "“下一镜”留空，表格下一行 %s 属于另一条线，可能走错" % nxt["shot_id"], "在“下一镜”一栏写明要接哪个镜头")
	elif n.contains(">"):
		for opt in n.split("|", false):
			targets.append(opt.split(">")[-1].strip_edges())
	else:
		targets.append(n)
	for t in targets:
		if t != "END" and not ids.has(t):
			err("镜头表", id, "“下一镜”指向的 %s 不存在" % t)


## 声音列：编号必须在音效表里；延迟写成 编号@秒；-编号 只能停循环声
func _check_sound_spec(table: String, id: String, spec: String, sounds: Dictionary) -> void:
	for s in Actions.parse_sounds(spec):
		if not sounds.has(s["id"]):
			err(table, id, "声音“%s”不在音效表里" % s["id"], "在音效表加这一行，或改成已有的声音编号")
		elif s["delay"] < 0:
			err(table, id, "声音“%s”的延迟写法不对" % s["id"], "写成 编号@秒，例如 door_bang@3.2")
		elif s["stop"] and sounds[s["id"]].get("loop", "否") != "是":
			warn(table, id, "“-%s”要停的不是循环声，不会有效果" % s["id"])


func _check_action(id: String, a: Dictionary, mode: String, room: String, hotspots: Dictionary, evidence: Dictionary, links: Dictionary, ann: Dictionary, lines: Dictionary, layout: Dictionary) -> void:
	var nm: String = a["name"]
	var args: Array = a["args"]
	if not Actions.ACTIONS.has(nm):
		err("镜头表", id, "动作“%s”不存在" % nm, "可用动作：" + "、".join(PackedStringArray(Actions.ACTIONS)))
		return
	match nm:
		"inspect":
			for h in args:
				if not hotspots.has(h):
					err("镜头表", id, "要检查的物件 %s 不在可检查物件表里" % h)
				elif mode == "walk" and levels.has(room):
					if not levels[room]["hs"].has(h):
						err("镜头表", id, "行走镜头要检查 %s，但关卡场景 levels/%s.tscn 里没有这个节点，玩家找不到" % [h, room], "在关卡场景里放一个节点，命名为 %s" % h)
				elif mode == "walk" and not _has_layout(layout, room, "可检查物件", h):
					err("镜头表", id, "行走镜头要检查 %s，但房间布局表的 %s 里没有放它，玩家找不到" % [h, room], "在房间布局表给 %s 加一行“可检查物件”" % room)
		"collect":
			for e in args:
				if not evidence.has(e):
					err("镜头表", id, "证据 %s 不在证据表里" % e)
		"annotate", "inquire", "telling":
			if args.size() > 0 and args[0] != "" and not ann.has(args[0]):
				err("镜头表", id, "预设组 %s 不在预设表里" % args[0])
			if nm == "telling":
				var leans := {}
				for row in ann.get(args[0], []):
					leans[row.get("tendency", "")] = true
				if not (leans.has("保护") and leans.has("取代")):
					err("预设表", args[0], "终局讲法必须同时有“保护”和“取代”两种倾向")
		"develop":
			if args.is_empty() or args[0] == "":
				err("镜头表", id, "develop 需要一张图片（art/footage/ 下的文件名）")
			elif not FileAccess.file_exists("res://art/footage/" + args[0]):
				warn("镜头表", id, "冲洗用的图片 art/footage/%s 还没交付，显示占位文字" % args[0])
		"link":
			if args.is_empty() or not links.has(args[0]):
				err("镜头表", id, "连线组 %s 不在连线规则表里" % str(args))
		"say", "recap", "diary":
			if args.is_empty() or not lines.has(args[0]):
				err("镜头表", id, "台词组 %s 不在台词表里" % str(args))
		"reveal", "conceal":
			for x in args:
				var found: bool = levels.has(room) and levels[room]["names"].has(x)
				if levels.has(room) and not found:
					err("镜头表", id, "%s 要显示 / 隐藏的“%s”在关卡场景 levels/%s.tscn 里没有同名节点" % [nm, x, room])
					continue
				for row in layout.get(room, []):
					if row.get("id", "") == x:
						found = true
				if not found:
					err("镜头表", id, "%s 要显示 / 隐藏的“%s”不在房间布局表的 %s 里" % [nm, x, room])
		"footage":
			if args.is_empty() or not footage.has(args[0]):
				err("镜头表", id, "影像片段“%s”不在影像片段表里" % str(args))
		"osd":
			if args.size() > 0 and args[0] != "" and not args[0] in ["档案卡", "摄像机"]:
				err("镜头表", id, "osd 的样式只能是 档案卡 或 摄像机")
		"fx":
			if args.size() > 0 and not args[0] in ["", "自动"] and not fx_presets.has(args[0]):
				err("镜头表", id, "滤镜预设“%s”不在滤镜表里" % args[0])
		"music":
			if args.is_empty() or (args[0] != "关闭" and not music.has(args[0])):
				err("镜头表", id, "配乐“%s”不在配乐表里" % str(args), "写配乐表里的曲名，或 music(关闭) 停止")
			if args.size() > 1 and not args[1].is_valid_float():
				err("镜头表", id, "music 的第二个参数是淡入 / 淡出秒数，现在是“%s”" % args[1])
		"station":
			# 客房的一站：桌面 / 打字机 / 床（docs/01 第 4 节）
			if args.size() != 1 or not ["hs_desk_board", "hs_typewriter", "hs_bed"].has(args[0]):
				err("镜头表", id, "station 只能写客房的三站：hs_desk_board、hs_typewriter、hs_bed")
			elif room != "guest_room":
				err("镜头表", id, "station 只用在客房（scene 写 guest_room）")
		"wake", "sleep":
			if room != "guest_room" and room != "":
				err("镜头表", id, "%s 只用在客房（scene 写 guest_room）" % nm)
		"explore":
			if args.is_empty() or not quests.has(args[0]):
				err("镜头表", id, "explore 的任务组“%s”不在任务表里" % str(args), "在 content/story/quests.csv 的 group 列写这个组名")
		"leak":
			if args.is_empty() or not args[0].is_valid_int() or int(args[0]) < 0 or int(args[0]) > 4:
				err("镜头表", id, "渗漏等级必须是 0—4")


func _check_words(words: Array, shots: Array, hotspots: Dictionary, links: Dictionary, ann: Dictionary, lines: Dictionary, evidence: Dictionary) -> void:
	var banned: Array = words.filter(func(w): return w.get("level", "") == "禁用").map(func(w): return w["word"])
	var graded: Array = words.filter(func(w): return str(w.get("level", "")).is_valid_int())
	# 镜头文字：按节点检查等级
	for r in shots:
		var node: String = r.get("node", "")
		var lv: int = NODE_LEAK.get(node, 4)
		var text: String = _strip_placeholders(r.get("text", ""))
		for w in graded:
			if int(w["level"]) > lv and text.contains(w["word"]):
				warn("镜头表", r["shot_id"], "出现了“%s”（渗漏 L%s 才该出现），而 %s 只到 L%d" % [w["word"], w["level"], node, lv], "确认是否故意提前；否则换成本时代的说法")
		if not node in REVEAL_NODES:
			for b in banned:
				if text.contains(b):
					err("镜头表", r["shot_id"], "出现禁用词“%s”（终局前不得出现）" % b)
	# 其他玩家看得到的文字：禁用词一律不得出现
	var others := {}
	for h in hotspots.values():
		others["可检查物件表 / " + h["id"]] = h.get("text", "") + h.get("label", "") + h.get("hint", "")
	for g in links:
		for p in links[g]:
			others["连线规则表 / " + g] = str(others.get("连线规则表 / " + g, "")) + p.get("response", "")
	for k in ann:
		for p in ann[k]:
			others["预设表 / " + k] = str(others.get("预设表 / " + k, "")) + p.get("text", "") + p.get("response", "")
	for k in lines:
		for p in lines[k]:
			others["台词表 / " + k] = str(others.get("台词表 / " + k, "")) + p.get("text", "")
	for e in evidence.values():
		others["证据表 / " + e["id"]] = e.get("name", "") + e.get("note", "") + e.get("detail", "") + e.get("hint", "")
	for where in others:
		for b in banned:
			if _strip_placeholders(str(others[where])).contains(b):
				var parts: PackedStringArray = where.split(" / ")
				err(parts[0], parts[1], "出现禁用词“%s”" % b)


## 占位符（如 {容器号}）在游戏里会被替换掉，玩家看不到，不参与词表检查
static func _strip_placeholders(t: String) -> String:
	var re := RegEx.create_from_string("\\{[^}]*\\}")
	return re.sub(t, "", true)


func _report(n_shots: int, n_hot: int, n_ev: int, n_ch: int, n_rooms: int, n_layout: int, n_snd: int, n_words: int) -> void:
	var errors: Array = issues.filter(func(i): return i["level"] == "错误")
	var notes: Array = issues.filter(func(i): return i["level"] == "提醒")
	var ok := errors.is_empty()
	var md := PackedStringArray()
	md.append("# 内容检查报告")
	md.append("")
	md.append("生成时间：%s" % Time.get_datetime_string_from_system(false, true))
	md.append("")
	md.append("## 结果：%s" % ("✅ 通过（没有错误）" if ok else "❌ 有 %d 个错误需要修改" % errors.size()))
	md.append("")
	md.append("共检查：镜头 %d · 可检查物件 %d · 证据 %d · 人物 %d · 房间 %d · 房间布局 %d 行 · 声音 %d · 词表 %d 个词" % [n_shots, n_hot, n_ev, n_ch, n_rooms, n_layout, n_snd, n_words])
	for group in [["❌ 错误（必须改，否则游戏里会出问题）", errors], ["⚠️ 提醒（不影响运行，建议看一眼）", notes]]:
		md.append("")
		md.append("## " + group[0])
		md.append("")
		if group[1].is_empty():
			md.append("无")
			continue
		md.append("| 表格 | 位置 | 问题 | 怎么改 |")
		md.append("| --- | --- | --- | --- |")
		for i in group[1]:
			md.append("| %s | %s | %s | %s |" % [i["table"], i["where"], i["what"], i["fix"]])
	md.append("")
	md.append("## 🧱 关卡场景与小物件规格")
	md.append("")
	md.append("已搭关卡场景：%d / %d 个房间（%s）" % [levels.size(), n_rooms, "、".join(PackedStringArray(levels.keys())) if not levels.is_empty() else "无"])
	if not prop_specs.is_empty():
		md.append("")
		md.append("小物件的尺寸从关卡里的占位方块读出，就是建模规格（单位：米；模型原点放在底面中心）。")
		md.append("")
		md.append("| 物件 | 名称 | 房间 | 宽 × 高 × 深 | 状态 |")
		md.append("| --- | --- | --- | --- | --- |")
		for p in prop_specs:
			var sz: String = "（不是方块，没有尺寸）" if p["size"] == null else "%.2f × %.2f × %.2f" % [p["size"].x, p["size"].y, p["size"].z]
			md.append("| %s | %s | %s | %s | %s |" % [p["id"], p["name"], p["room"], sz, p["state"]])
	if not level_rows.is_empty():
		md.append("")
		md.append("## 🎬 关卡进度（纵切面，按关卡表自动统计）")
		md.append("")
		md.append("| 关卡 | 镜头 | 房间（可走动的） | 用到的模块 | 渗漏与影像 | AI 位置 | 自动发现的缺口 | 状态 | 备注 |")
		md.append("| --- | --- | --- | --- | --- | --- | --- | --- | --- |")
		for r in level_rows:
			md.append("| %s %s | %d | %s（%s） | %s | %s | %s | %s | %s | %s |" % [r["level"], r["name"], r["shots"], r["rooms"], r["walk"] if r["walk"] != "" else "无", r["modules"], r["look"], r["ai"] if r["ai"] != "" else "—", r["gaps"], r["status"], r["note"]])
	md.append("")
	md.append("填表说明见 docs/填表说明/。")
	var path := ProjectSettings.globalize_path("res://").path_join("../检查报告.md").simplify_path()
	var f := FileAccess.open(path, FileAccess.WRITE)
	if f:
		f.store_string("\n".join(md) + "\n")
	print("内容检查：%s（%d 个错误，%d 个提醒）" % ["通过" if ok else "未通过", errors.size(), notes.size()])
	for i in errors:
		print("  错误  [%s] %s：%s" % [i["table"], i["where"], i["what"]])
	for i in notes:
		print("  提醒  [%s] %s：%s" % [i["table"], i["where"], i["what"]])
	for r in level_rows:
		print("  关卡 %s %s：%d 个镜头 · 缺口：%s" % [r["level"], r["name"], r["shots"], r["gaps"]])
	print("报告：", path)
	quit(0 if ok else 1)


## 每个 CSV 都要有 importer="keep" 的 .import 文件，否则 Godot 会把它当成翻译表导入
func _check_import_files() -> void:
	for path in _list("res://content"):
		if path.ends_with(".csv"):
			var imp: String = path + ".import"
			if not FileAccess.file_exists(imp) or not FileAccess.get_file_as_string(imp).contains("\"keep\""):
				var f := FileAccess.open(imp, FileAccess.WRITE)
				f.store_string("[remap]\n\nimporter=\"keep\"\n")
				warn("（自动修复）", path.get_file(), "已补上导入设置文件")


func _list(root: String) -> Array:
	var out: Array = []
	var d := DirAccess.open(root)
	if d == null:
		return out
	for f in d.get_files():
		out.append(root.path_join(f))
	for sub in d.get_directories():
		out.append_array(_list(root.path_join(sub)))
	return out

## 动作 → 横切面模块（docs/12 第 2 节）
const ACTION_MODULE := {
	"osd": "影像档案", "footage": "影像档案", "fx": "媒介滤镜", "leak": "媒介滤镜",
	"inquire": "问话与台词", "say": "问话与台词",
	"link": "证据板", "annotate": "打字机与手记", "develop": "暗房冲洗",
	"telling": "终局讲法", "reveal": "场景事件", "conceal": "场景事件",
	"collect": "证据板",
}


## 纵切面：按关卡表把镜头归到各关，统计每关用到的模块、滤镜、房间与缺口
func _level_report(shots: Array, rooms: Dictionary, sounds: Dictionary, ann: Dictionary, lines: Dictionary, footage: Dictionary) -> void:
	var levels := DB.load_table("res://content/levels.csv")
	if levels.is_empty():
		return
	var owner := {}
	for lv in levels:
		for sid in str(lv.get("shots", "")).split(";", false):
			owner[sid.strip_edges()] = lv["level"]
	var data := {}
	for lv in levels:
		data[lv["level"]] = {"shots": 0, "rooms": [], "walk": [], "modules": [], "leak": [], "clips": [], "ai": [], "todo": 0, "img": 0, "snd_missing": 0, "snd": [], "models": 0, "errors": 0}
	var cur_room := ""
	var cur_leak := "0"
	for s in shots:
		var id: String = s["shot_id"]
		var lvid := ""
		if owner.has(id):
			lvid = owner[id]
		else:
			for lv in levels:
				if s.get("node", "") in str(lv.get("nodes", "")).split(";", false):
					lvid = lv["level"]
		if s.get("scene", "") != "":
			cur_room = s["scene"]
		if lvid == "" or not data.has(lvid):
			if not owner.has(id):
				warn("关卡表", id, "这个镜头不属于任何关卡", "在关卡表的 nodes 或 shots 列里认领它")
			continue
		var d: Dictionary = data[lvid]
		d["shots"] += 1
		var rname: String = rooms.get(cur_room, {}).get("name", cur_room)
		if not d["rooms"].has(rname):
			d["rooms"].append(rname)
		var walk: bool = s.get("mode", "") == "walk"
		if walk and not d["walk"].has(rname):
			d["walk"].append(rname)
		if s.get("text", "") != "" and not d["modules"].has("文字与字幕"):
			d["modules"].append("文字与字幕")
		if s.get("ai_slot", "") != "" and not d["ai"].has(s["ai_slot"]):
			d["ai"].append(s["ai_slot"])
		if "待补" in str(s.get("text", "")):
			d["todo"] += 1
		for snd in Actions.parse_sounds(str(s.get("sound", ""))):
			var sid2: String = snd["id"]
			if snd["stop"] or sid2 == "silence":
				continue
			if not d["snd"].has(sid2):
				d["snd"].append(sid2)
				if sounds.get(sid2, {}).get("file", "") == "":
					d["snd_missing"] += 1
		for a in Actions.parse(s.get("actions", "")):
			var nm: String = a["name"]
			var args: Array = a["args"]
			var mod: String = ACTION_MODULE.get(nm, "")
			if nm == "inspect":
				mod = "行走与检查" if walk else "观察"
			if mod != "" and not d["modules"].has(mod):
				d["modules"].append(mod)
			if nm == "leak" and args.size() > 0:
				cur_leak = args[0]
				if int(cur_leak) >= 3 and not d["modules"].has("渗漏材质"):
					d["modules"].append("渗漏材质")
			if nm in ["footage"] and args.size() > 0 and not d["clips"].has(args[0]):
				d["clips"].append(args[0])
				for row in footage.get(args[0], []):
					var img: String = row.get("image", "")
					if img != "" and not FileAccess.file_exists("res://art/footage/" + img):
						d["img"] += 1
			if nm in ["inquire", "annotate", "telling"] and args.size() > 0:
				for row in ann.get(args[0], []):
					if "待补" in str(row.get("response", "")):
						d["todo"] += 1
		var leak_tag := "L%d" % NODE_LEAK.get(s.get("node", ""), 0)
		if not d["leak"].has(leak_tag):
			d["leak"].append(leak_tag)
		for i in issues:
			if i["level"] == "错误" and i["where"] == id:
				d["errors"] += 1
	for lv in levels:
		var d: Dictionary = data[lv["level"]]
		for rn in d["rooms"]:
			for rid in rooms:
				if rooms[rid].get("name", "") == rn and not levels.has(rid):
					d["models"] += 1
		var gaps := PackedStringArray()
		if d["errors"] > 0:
			gaps.append("%d 个错误" % d["errors"])
		if d["todo"] > 0:
			gaps.append("%d 处文字待补" % d["todo"])
		if d["img"] > 0:
			gaps.append("%d 张影像图片待交付" % d["img"])
		if d["models"] > 0:
			gaps.append("%d 个房间还没有关卡场景（仍是灰盒）" % d["models"])
		if d["snd_missing"] > 0:
			gaps.append("%d / %d 个声音无文件" % [d["snd_missing"], d["snd"].size()])
		level_rows.append({
			"level": lv["level"], "name": lv.get("name", ""), "shots": d["shots"],
			"rooms": "、".join(PackedStringArray(d["rooms"])),
			"walk": "、".join(PackedStringArray(d["walk"])),
			"modules": "、".join(PackedStringArray(d["modules"])),
			"look": "、".join(PackedStringArray(d["leak"])) + ("；影像：" + "、".join(PackedStringArray(d["clips"])) if not d["clips"].is_empty() else ""),
			"ai": "、".join(PackedStringArray(d["ai"])),
			"gaps": "；".join(gaps) if not gaps.is_empty() else "无",
			"status": lv.get("status", ""),
			"note": lv.get("note", ""),
		})
