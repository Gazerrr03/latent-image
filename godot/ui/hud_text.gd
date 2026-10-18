extends RefCounted
## 界面上要从表格拼出来的几行字：界面文字表、日期角标、房间名、准星提示。
## 内容都从表里取（界面文字表 content/visual/ui.csv、镜头表的 diary(...)、台词表的日记页、关卡表、房间表），代码不写死。

const Actions := preload("res://core/actions.gd")
const UI_TABLE := "res://content/visual/ui.csv"
const LEVELS_TABLE := "res://content/levels.csv"

static var _ui := {}
static var _levels: Array = []


static func reload() -> void:
	_ui = ContentDB.index_by(ContentDB.load_table(UI_TABLE), "id")
	_levels = ContentDB.load_table(LEVELS_TABLE)


## 界面文字表的一项；表里没有时用 id 本身，好在画面上一眼看出缺了什么
static func t(id: String) -> String:
	if _ui.is_empty():
		reload()
	return String(_ui.get(id, {}).get("text", id))


## 这一镜属于哪一章：关卡表 name 的前半（“第二章·女主人” → “第二章”，“序·鱼头” → “序”）
static func chapter(shot_id: String) -> String:
	if _levels.is_empty():
		reload()
	var node: String = ContentDB.shots.get(shot_id, {}).get("node", "")
	for lv in _levels:
		if node != "" and String(lv.get("nodes", "")).split(";", false).has(node):
			return String(lv.get("name", "")).get_slice("·", 0)
	return ""


## 这一镜是哪一天：镜头表里这一镜之前最近一次 diary(...) 写下的那一页。
## 返回 {date: “十月十八日 星期一”, countdown: “离开庭还有五天”}（日记页标题下的第一行小字）
static func day(shot_id: String) -> Dictionary:
	var set_id := ""
	for r in ContentDB.shot_order:
		if r.get("shot_id", "") == shot_id:
			# 这一镜之前还没有写过日记（第一镜）：用这一镜自己的
			if set_id == "":
				set_id = _diary_of(r)
			break
		var d := _diary_of(r)
		if d != "":
			set_id = d
	var out := {"date": "", "countdown": ""}
	var v := GameState.vars()
	for r in ContentDB.lines.get(set_id, []):
		if not ContentDB.condition_matches(r.get("condition", ""), v):
			continue
		var text: String = String(r.get("text", "")).replace("　", " ").strip_edges()
		match r.get("speaker", ""):
			"日期": out["date"] = text
			"": if out["countdown"] == "": out["countdown"] = text.trim_suffix("。")
	return out


static func _diary_of(row: Dictionary) -> String:
	var found := ""
	for a in Actions.parse(row.get("actions", "")):
		if a["name"] == "diary" and a["args"].size() > 0:
			found = a["args"][0]
	return found


## 日期角标：“十月十八日 星期一 · 第二章 · 离开庭还有五天”；chapter_first 时章在最前（标题页“继续调查”下面那行）
static func day_line(shot_id: String, chapter_first := false) -> String:
	var d := day(shot_id)
	var ch := chapter(shot_id)
	var parts: Array = [ch, d["date"], d["countdown"]] if chapter_first else [d["date"], ch, d["countdown"]]
	return " · ".join(PackedStringArray(parts.filter(func(s): return s != "")))


## 房间名：房间表的 label，没写用 name，去掉括号里的注
static func room_name(rid: String) -> String:
	var row: Dictionary = ContentDB.scenes.get(rid, {})
	var n: String = row.get("label", "")
	if n == "":
		n = String(row.get("name", "")).get_slice("（", 0)
	return n.strip_edges()


## 准星提示统一成“动作 · 对象”：“检查：药柜” → “检查 · 药柜”；交谈只写名字（“康斯坦斯·塔尔博特” → “康斯坦斯”）
static func hint_parts(text: String) -> Array:
	var s := text.strip_edges()
	# 玩家脚本传来的文字前面带着按键（“E　检查：药柜”）
	var sp := s.find("　")
	if sp > 0 and sp <= 3:
		s = s.substr(sp + 1).strip_edges()
	var verb := s.get_slice("：", 0).strip_edges()
	var obj := s.get_slice("：", 1).strip_edges() if s.contains("：") else ""
	if verb == "交谈":
		obj = obj.get_slice("·", 0)
	return [verb, obj]
