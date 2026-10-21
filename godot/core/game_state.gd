extends Node
## 全局游戏状态与存档。字段含义见 docs/06-技术方案.md 第 3 节。

signal changed

const SAVE_PATH := "user://save.json"
## 两种讲法（docs/02 第 9.3 节）；平局时先出现“保护”
const LEANS := ["保护", "取代"]

var shot := ""
var evidence: Array = []
## 每条证据是在哪一镜收进来的：章末复盘按章列出“今天找到的”
var found_at := {}
var inspected: Array = []
var links_done: Array = []
## 完成了的任务（任务表 id）
var quests_done: Array = []
## 连对的证据对 [[a, b], ...]，证据板上画红线用
var link_pairs: Array = []
var leak_level := 0
## 玩家记录的倾向计数：保护 / 取代（决定终局哪一种讲法先出现在纸上）
var tendency := {}
## 玩家的全部批注与选择，终局自述的输入
var journal: Array = []
var objective := ""
## 终局选定的讲法（保护 / 取代）与那句话本身
var ending := ""
var statement := ""
## 本局的容器编号 01—12：第 5 章合影背面与尾声记录卡上显示
var container := ""
## 截图、自动测试时为 false：开发测试永远不写玩家的存档
var persist := true


func reset() -> void:
	shot = ""
	evidence = []
	found_at = {}
	inspected = []
	links_done = []
	quests_done = []
	link_pairs = []
	leak_level = 0
	tendency = {}
	journal = []
	objective = ""
	ending = ""
	statement = ""
	container = "%02d" % randi_range(1, 12)
	changed.emit()


## 倾向：计数较高的讲法；平局取“保护”。
## 命令行 --view=取代 可强制指定，用于截图和测试
func dominant() -> String:
	for a in OS.get_cmdline_user_args():
		if a.begins_with("--view="):
			return a.trim_prefix("--view=")
	var best: String = LEANS[0]
	for t in LEANS:
		if int(tendency.get(t, 0)) > int(tendency.get(best, 0)):
			best = t
	return best


## 用于 lines.csv 与 next 列的条件匹配：ending（已选定的讲法）、view（当前倾向）
func vars() -> Dictionary:
	return {"ending": ending, "view": dominant()}


func add_evidence(id: String) -> void:
	if id != "" and not evidence.has(id):
		evidence.append(id)
		found_at[id] = shot
		changed.emit()


func add_tendency(t: String) -> void:
	if t == "":
		return
	tendency[t] = int(tendency.get(t, 0)) + 1


func record(kind: String, text: String, extra := {}) -> void:
	var entry := {"kind": kind, "text": text, "shot": shot}
	entry.merge(extra)
	journal.append(entry)


func set_leak(level: int) -> void:
	leak_level = clampi(level, 0, 4)
	changed.emit()


func to_dict() -> Dictionary:
	return {
		"version": 2, "shot": shot, "evidence": evidence, "found_at": found_at, "inspected": inspected,
		"links_done": links_done, "quests_done": quests_done, "link_pairs": link_pairs, "leak_level": leak_level, "tendency": tendency,
		"journal": journal, "objective": objective, "ending": ending, "statement": statement, "container": container,
	}


func from_dict(d: Dictionary) -> void:
	reset()
	shot = d.get("shot", "")
	evidence = d.get("evidence", [])
	found_at = d.get("found_at", {})
	inspected = d.get("inspected", [])
	links_done = d.get("links_done", [])
	quests_done = d.get("quests_done", [])
	link_pairs = d.get("link_pairs", [])
	leak_level = int(d.get("leak_level", 0))
	tendency = d.get("tendency", {})
	journal = d.get("journal", [])
	objective = d.get("objective", "")
	ending = d.get("ending", "")
	statement = d.get("statement", "")
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
	# 旧剧情（版本 1）的存档不再可用
	if typeof(data) != TYPE_DICTIONARY or int(data.get("version", 1)) < 2:
		return false
	from_dict(data)
	return true


func delete_save() -> void:
	if has_save():
		DirAccess.remove_absolute(ProjectSettings.globalize_path(SAVE_PATH))
