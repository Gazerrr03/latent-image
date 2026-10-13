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
## 每个节点允许的渗漏等级（docs/02 第 4 节）
const NODE_LEAK := {"N1": 0, "N2": 1, "N3": 1, "N4": 2, "N5": 3, "N6": 4, "N7": 4}
const LAYOUT_TYPES := ["家具", "可检查物件", "机位", "灯光", "出生点"]

## 每条问题：{level: 错误/提醒, table, where, what, fix}
var issues: Array = []
var fx_presets := {}
var footage := {}


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
			err("镜头表", "某一行", "没有填镜号", "每行第一列必须填镜号，例如 N3-A-01")
		elif ids.has(id):
			err("镜头表", id, "镜号重复", "改成一个没用过的镜号")
		ids[id] = r
	for i in shots.size():
		var r: Dictionary = shots[i]
		var id: String = r["shot_id"]
		var room: String = r.get("scene", "")
		var mode: String = r.get("mode", "")
		if room != "" and not rooms.has(room):
			err("镜头表", id, "房间“%s”不在房间登记表里" % room, "先在房间登记表加这个房间，或改成已有的房间编号")
		if not mode in ["", "camera", "walk"]:
			err("镜头表", id, "模式只能填 camera（镜头）或 walk（行走），现在是“%s”" % mode)
		var cam: String = r.get("camera", "")
		if cam != "" and room != "" and not _has_layout(layout, room, "机位", cam) and rooms.get(room, {}).get("model", "") == "":
			warn("镜头表", id, "机位“%s”在房间布局表的 %s 里找不到，会用默认机位" % [cam, room], "在房间布局表给这个房间加一行“机位”")
		for snd in str(r.get("sound", "")).split(";", false):
			if not sounds.has(snd.strip_edges()):
				err("镜头表", id, "声音“%s”不在音效表里" % snd.strip_edges(), "在音效表加这一行，或改成已有的声音编号")
		_check_next(r, i, shots, ids)
		for a in Actions.parse(r.get("actions", "")):
			_check_action(id, a, mode, room, hotspots, evidence, links, ann, lines, layout)

	# ── 线索 ──
	for h in hotspots.values():
		var fc: String = h.get("footage", "")
		if fc != "" and not footage.has(fc):
			err("可检查物件表", h["id"], "影像片段“%s”不在影像片段表里" % fc)
		var e: String = h.get("evidence", "")
		if e != "" and not evidence.has(e):
			err("可检查物件表", h["id"], "给出的证据“%s”不在证据表里" % e, "在证据表加这张卡片")
	for g in links:
		for p in links[g]:
			for k in ["a", "b"]:
				if not evidence.has(p.get(k, "")):
					err("连线规则表", "连线组 " + g, "证据“%s”不在证据表里" % p.get(k, ""))

	# ── 人物 ──
	var lines_seen := {}
	for c in chars:
		var n: String = c.get("name", "")
		var st: String = c.get("status", "")
		if not st in ["嫌疑人", "已除名", "其他"]:
			err("人物表", n, "状态只能填 嫌疑人 / 已除名 / 其他，现在是“%s”" % st)
		if st == "嫌疑人":
			var ln: String = c.get("line", "")
			if not ln in ["A", "B", "C"]:
				err("人物表", n, "嫌疑人必须填分支线 A / B / C")
			elif lines_seen.has(ln):
				err("人物表", n, "分支线 %s 和 %s 重复" % [ln, lines_seen[ln]])
			lines_seen[ln] = n
			if c.get("room", "") != "" and not rooms.has(c["room"]):
				err("人物表", n, "所在房间“%s”不在房间登记表里" % c["room"])

	# ── 空间 ──
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
		var m: String = rooms[id].get("model", "")
		if m != "" and not FileAccess.file_exists(m):
			warn("房间登记表", id, "美术模型 %s 还没交付，暂时用灰盒" % m.get_file())
		if not FileAccess.file_exists(m) and not layout.has(id):
			err("房间登记表", id, "既没有美术模型，也没有房间布局", "在房间布局表给它加家具、出生点等")

	# ── 声音 ──
	var missing_files := 0
	for s in sounds.values():
		var f: String = s.get("file", "")
		if f == "":
			missing_files += 1
		elif not FileAccess.file_exists("res://audio/" + f):
			err("音效表", s["id"], "文件 audio/%s 不存在" % f, "检查文件名是否一致，包括扩展名")
	if missing_files > 0:
		warn("音效表", "全表", "%d / %d 个声音还没有文件（游戏里会静音）" % [missing_files, sounds.size()])

	# ── 词表：玩家看到的文字里，穿帮词是否出现得太早 ──
	_check_words(words, shots, hotspots, links, ann, lines, evidence)

	_report(shots.size(), hotspots.size(), evidence.size(), chars.size(), rooms.size(), layout_rows.size(), sounds.size(), words.size())


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
				elif mode == "walk" and not _has_layout(layout, room, "可检查物件", h):
					err("镜头表", id, "行走镜头要检查 %s，但房间布局表的 %s 里没有放它，玩家找不到" % [h, room], "在房间布局表给 %s 加一行“可检查物件”" % room)
		"collect":
			for e in args:
				if not evidence.has(e):
					err("镜头表", id, "证据 %s 不在证据表里" % e)
		"annotate", "inquire", "accuse":
			if args.size() > 0 and args[0] != "" and not ann.has(args[0]):
				err("镜头表", id, "预设组 %s 不在预设表里" % args[0])
		"link":
			if args.is_empty() or not links.has(args[0]):
				err("镜头表", id, "连线组 %s 不在连线规则表里" % str(args))
		"say", "ending":
			if args.is_empty() or not lines.has(args[0]):
				err("镜头表", id, "台词组 %s 不在台词表里" % str(args))
		"footage":
			if args.is_empty() or not footage.has(args[0]):
				err("镜头表", id, "影像片段“%s”不在影像片段表里" % str(args))
		"osd":
			if args.size() > 0 and args[0] != "" and not args[0] in ["档案卡", "摄像机"]:
				err("镜头表", id, "osd 的样式只能是 档案卡 或 摄像机")
		"fx":
			if args.size() > 0 and not args[0] in ["", "自动"] and not fx_presets.has(args[0]):
				err("镜头表", id, "滤镜预设“%s”不在滤镜表里" % args[0])
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
		var text: String = r.get("text", "")
		for w in graded:
			if int(w["level"]) > lv and text.contains(w["word"]):
				warn("镜头表", r["shot_id"], "出现了“%s”（渗漏 L%s 才该出现），而 %s 只到 L%d" % [w["word"], w["level"], node, lv], "确认是否故意提前；否则换成本时代的说法")
		if node != "N7":
			for b in banned:
				if text.contains(b):
					err("镜头表", r["shot_id"], "出现禁用词“%s”（终局前不得出现）" % b)
	# 其他玩家看得到的文字：禁用词一律不得出现
	var others := {}
	for h in hotspots.values():
		others["可检查物件表 / " + h["id"]] = h.get("text", "") + h.get("label", "")
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
		others["证据表 / " + e["id"]] = e.get("name", "") + e.get("note", "")
	for where in others:
		for b in banned:
			if str(others[where]).contains(b):
				var parts: PackedStringArray = where.split(" / ")
				err(parts[0], parts[1], "出现禁用词“%s”" % b)


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
