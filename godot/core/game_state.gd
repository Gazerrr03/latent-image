extends Node
## 全局游戏状态与存档。字段含义见 docs/06-技术方案.md 第 3 节。

signal changed

const SAVE_PATH := "user://save.json"
const TELEGRAMS := 7
## 指认后决定分支线：第一次指认谁，就走哪条线
const LINE_OF := {"巴洛": "A", "韦恩小姐": "B", "朗斯": "C"}
const SUSPECTS := ["巴洛", "韦恩小姐", "朗斯"]

var shot := ""
var telegrams_left := TELEGRAMS
var line := ""
## 指认顺序：[X, Y]
var accused: Array = []
var evidence: Array = []
var inspected: Array = []
var links_done: Array = []
var leak_level := 0
var tendency := {}
## 玩家的全部批注与选择，终局自述的输入
var journal: Array = []
var objective := ""
var ending := ""


func reset() -> void:
	shot = ""
	telegrams_left = TELEGRAMS
	line = ""
	accused = []
	evidence = []
	inspected = []
	links_done = []
	leak_level = 0
	tendency = {}
	journal = []
	objective = ""
	ending = ""
	changed.emit()


func remaining_suspects() -> Array:
	return SUSPECTS.filter(func(s): return not accused.has(s))


## 用于 lines.csv 的条件匹配：X、Y、Z、line、ending
func vars() -> Dictionary:
	var v := {"line": line, "ending": ending}
	if accused.size() > 0:
		v["X"] = accused[0]
	if accused.size() > 1:
		v["Y"] = accused[1]
		var rest := remaining_suspects()
		if rest.size() == 1:
			v["Z"] = rest[0]
	return v


func accuse(name: String) -> void:
	accused.append(name)
	if line == "":
		line = LINE_OF.get(name, "")
	changed.emit()


func add_evidence(id: String) -> void:
	if id != "" and not evidence.has(id):
		evidence.append(id)
		changed.emit()


func add_tendency(t: String) -> void:
	if t == "":
		return
	tendency[t] = int(tendency.get(t, 0)) + 1


func record(kind: String, text: String, extra := {}) -> void:
	var entry := {"kind": kind, "text": text, "shot": shot}
	entry.merge(extra)
	journal.append(entry)


func use_telegram() -> void:
	telegrams_left = max(0, telegrams_left - 1)
	changed.emit()


func set_leak(level: int) -> void:
	leak_level = clampi(level, 0, 4)
	changed.emit()


func to_dict() -> Dictionary:
	return {
		"version": 1, "shot": shot, "telegrams_left": telegrams_left, "line": line,
		"accused": accused, "evidence": evidence, "inspected": inspected,
		"links_done": links_done, "leak_level": leak_level, "tendency": tendency,
		"journal": journal, "objective": objective, "ending": ending,
	}


func from_dict(d: Dictionary) -> void:
	reset()
	shot = d.get("shot", "")
	telegrams_left = int(d.get("telegrams_left", TELEGRAMS))
	line = d.get("line", "")
	accused = d.get("accused", [])
	evidence = d.get("evidence", [])
	inspected = d.get("inspected", [])
	links_done = d.get("links_done", [])
	leak_level = int(d.get("leak_level", 0))
	tendency = d.get("tendency", {})
	journal = d.get("journal", [])
	objective = d.get("objective", "")
	ending = d.get("ending", "")
	changed.emit()


func save() -> void:
	var f := FileAccess.open(SAVE_PATH, FileAccess.WRITE)
	if f:
		f.store_string(JSON.stringify(to_dict(), "\t"))


func has_save() -> bool:
	return FileAccess.file_exists(SAVE_PATH)


func load_save() -> bool:
	if not has_save():
		return false
	var data = JSON.parse_string(FileAccess.get_file_as_string(SAVE_PATH))
	if typeof(data) != TYPE_DICTIONARY:
		return false
	from_dict(data)
	return true


func delete_save() -> void:
	if has_save():
		DirAccess.remove_absolute(ProjectSettings.globalize_path(SAVE_PATH))
