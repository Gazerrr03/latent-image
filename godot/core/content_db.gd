extends Node
## 读取 res://content/ 下的表格。所有剧情内容都在表里，代码不写死内容。
## 表头与列含义见 docs/06-技术方案.md 第 2 节。

const STORY := "res://content/story/"
const SPACE := "res://content/space/"
const AUDIO := "res://content/audio/"
const AI := "res://content/ai/"

## 按表格顺序排列的镜头，以及 shot_id -> 行
var shot_order: Array = []
var shots := {}
var hotspots := {}
var evidence := {}
## group -> 行数组
var links := {}
## set_id -> 行数组
var annotations := {}
## set_id -> 行数组
var lines := {}
## 房间登记表（id -> 行）
var scenes := {}
## 房间布局表：room -> 行数组
var layout := {}
## 人物表，按表格顺序
var characters: Array = []
## 音效表：id -> 行
var sounds := {}
var wordlists: Array = []
var confession_fallback := ""


func _ready() -> void:
	reload()


func reload() -> void:
	shot_order = load_table(STORY + "shots.csv")
	shots = index_by(shot_order, "shot_id")
	hotspots = index_by(load_table(STORY + "hotspots.csv"), "id")
	evidence = index_by(load_table(STORY + "evidence.csv"), "id")
	links = group_by(load_table(STORY + "links.csv"), "group")
	annotations = group_by(load_table(STORY + "annotations.csv"), "set_id")
	lines = group_by(load_table(STORY + "lines.csv"), "set_id")
	scenes = index_by(load_table(SPACE + "rooms.csv"), "id")
	layout = group_by(load_table(SPACE + "layout.csv"), "room")
	characters = load_table(STORY + "characters.csv")
	sounds = index_by(load_table(AUDIO + "sounds.csv"), "id")
	wordlists = load_table(AI + "wordlists.csv")
	if FileAccess.file_exists(AI + "confession_fallback.txt"):
		confession_fallback = FileAccess.get_file_as_string(AI + "confession_fallback.txt")


## 读 CSV：第一行是表头；以 # 开头的行是注释；文本中的 \n 转为换行
static func load_table(path: String) -> Array:
	var rows: Array = []
	var f := FileAccess.open(path, FileAccess.READ)
	if f == null:
		push_warning("内容表不存在：" + path)
		return rows
	var header := f.get_csv_line()
	if header.size() > 0:
		# Excel 另存的 UTF-8 CSV 开头会带一个看不见的标记（BOM）
		header[0] = header[0].trim_prefix("\ufeff")
	while not f.eof_reached():
		var cells := f.get_csv_line()
		if cells.size() == 0 or (cells.size() == 1 and cells[0].strip_edges() == ""):
			continue
		if cells[0].begins_with("#"):
			continue
		var row := {}
		for i in header.size():
			var key := header[i].strip_edges()
			row[key] = cells[i].strip_edges().replace("\\n", "\n") if i < cells.size() else ""
		rows.append(row)
	return rows


static func index_by(rows: Array, key: String) -> Dictionary:
	var d := {}
	for r in rows:
		d[r.get(key, "")] = r
	return d


static func group_by(rows: Array, key: String) -> Dictionary:
	var d := {}
	for r in rows:
		var k: String = r.get(key, "")
		if not d.has(k):
			d[k] = []
		d[k].append(r)
	return d


## 人物表中状态为“嫌疑人”的人，按表格顺序
func suspects() -> Array:
	return characters.filter(func(c): return c.get("status", "") == "嫌疑人").map(func(c): return c["name"])


## 第一次指认此人时进入的分支线（A / B / C）
func line_of(name: String) -> String:
	for c in characters:
		if c["name"] == name:
			return c.get("line", "")
	return ""


## 访客簿上列出的名字：已除名与嫌疑人，按表格顺序
func register_names() -> Array:
	return characters.filter(func(c): return c.get("status", "") in ["已除名", "嫌疑人"]).map(func(c): return c["name"])


## 表格中下一行的镜号（用于 next 列留空时）
func next_in_order(shot_id: String) -> String:
	for i in shot_order.size():
		if shot_order[i]["shot_id"] == shot_id and i + 1 < shot_order.size():
			return shot_order[i + 1]["shot_id"]
	return "END"


## lines.csv 的 condition 形如 "X=巴洛;Y=韦恩小姐"，空表示无条件
static func condition_matches(cond: String, vars: Dictionary) -> bool:
	if cond.strip_edges() == "":
		return true
	for part in cond.split(";", false):
		var kv := part.split("=")
		if kv.size() != 2:
			return false
		if str(vars.get(kv[0].strip_edges(), "")) != kv[1].strip_edges():
			return false
	return true
