extends Node
## 全局游戏状态与存档。字段含义见 docs/06-技术方案.md 第 3 节。

signal changed

const SAVE_PATH := "user://save.json"
const TELEGRAMS := 7

var shot := ""
var telegrams_left := TELEGRAMS
var line := ""
## 指认顺序：[X, Y]
var accused: Array = []
var evidence: Array = []
var inspected: Array = []
var links_done: Array = []
## 连对的证据对 [[a, b], ...]，证据板上画红线用
var link_pairs: Array = []
var leak_level := 0
## 人格属性计数：好奇 / 记忆 / 共情 / 欲望（docs/01 第 4.1 节）
var tendency := {}
## 玩家的全部批注与选择，终局自述的输入
var journal: Array = []
var objective := ""
## 终局视角 = 结束时的主导属性
var ending := ""
## 本局的容器编号，N7-05 的文件上显示；每局随机，暗示还有很多个“我”
var container := ""
## 截图、自动测试时为 false：开发测试永远不写玩家的存档
var persist := true


func reset() -> void:
	shot = ""
	telegrams_left = TELEGRAMS
	line = ""
	accused = []
	evidence = []
	inspected = []
	links_done = []
	link_pairs = []
	leak_level = 0
	tendency = {}
	journal = []
	objective = ""
	ending = ""
	container = "%04d" % randi_range(1, 9999)
	changed.emit()


## 主导属性：计数最高者；平局取“好奇”（侦探本来就是好奇）。
## 命令行 --view=记忆 可强制指定，用于截图和测试四种视角
func dominant() -> String:
	for a in OS.get_cmdline_user_args():
		if a.begins_with("--view="):
			return a.trim_prefix("--view=")
	var best := "好奇"
	for t in ["好奇", "记忆", "共情", "欲望"]:
		if int(tendency.get(t, 0)) > int(tendency.get(best, 0)):
			best = t
	return best


## 嫌疑人名单与分支线来自人物表（content/story/characters.csv）
func remaining_suspects() -> Array:
	return ContentDB.suspects().filter(func(s): return not accused.has(s))


## 用于 lines.csv 的条件匹配：X、Y、Z、line、ending、view（当前主导属性）
func vars() -> Dictionary:
	var v := {"line": line, "ending": ending, "view": dominant()}
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
		line = ContentDB.line_of(name)
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
		"links_done": links_done, "link_pairs": link_pairs, "leak_level": leak_level, "tendency": tendency,
		"journal": journal, "objective": objective, "ending": ending, "container": container,
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
	link_pairs = d.get("link_pairs", [])
	leak_level = int(d.get("leak_level", 0))
	tendency = d.get("tendency", {})
	journal = d.get("journal", [])
	objective = d.get("objective", "")
	ending = d.get("ending", "")
	container = d.get("container", container)
	changed.emit()


func save() -> void:
	if not persist:
		return
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
