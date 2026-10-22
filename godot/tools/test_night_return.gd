extends SceneTree
## 回客房天光回归：不写玩家存档。
var failures := 0
func _initialize() -> void: call_deferred("run")
func check(label: String, ok: bool) -> void:
	print("PASS " if ok else "FAIL ", label)
	if not ok: failures += 1
func run() -> void:
	var Look = load("res://world/look.gd")
	var state = root.get_node("GameState")
	var db = root.get_node("ContentDB")
	var director = root.get_node("Director")
	state.persist = false
	state.reset()
	for group in ["c1", "c2", "c3", "c4", "c6"]:
		state.quests_done.clear()
		state.shot = "C2-03"
		director._explore_group = group
		check(group + " 未收齐保持日间", not Look.is_night())
		for q in db.quests[group]:
			if not director.quest_ends(q): state.quests_done.append(q.id)
		check(group + " 返程启用夜预设", Look.is_night() and Look.current().preset == "夜")
		director._explore_group = ""
	for sid in ["C1-07", "C2-05", "C3-06", "C4-05", "C5-08", "C6-08", "C6-10"]:
		state.shot = sid
		check(sid + " 收尾夜间", Look.current().preset == "夜")
	for sid in ["C1-01", "C2-01", "C3-01", "C4-01"]:
		state.shot = sid
		check(sid + " 恢复日间", Look.current().preset != "夜")
	quit(0 if failures == 0 else 1)
