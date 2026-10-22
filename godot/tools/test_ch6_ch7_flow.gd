extends SceneTree
## --headless --path godot --script res://tools/test_ch6_ch7_flow.gd
const Actions = preload("res://core/actions.gd")
var failures := 0
func _initialize() -> void: call_deferred("run")
func check(label: String, ok: bool) -> void:
	print("PASS " if ok else "FAIL ", label)
	if not ok: failures += 1
func run() -> void:
	var state = root.get_node("GameState")
	var db = root.get_node("ContentDB")
	var director = root.get_node("Director")
	state.persist = false
	state.reset()
	var tasks: Array = db.quests.c6
	var back: Dictionary = tasks.filter(func(q): return q.id == "c6_return")[0]
	var darkroom: Dictionary = tasks.filter(func(q): return q.id == "c6_darkroom")[0]
	check("暗房任务不会提前结束探索", not director.quest_ends(darkroom))
	check("未完成暗房不能返回收尾", not director.quest_ready(back))
	# 已收齐证据不等于已经经历显影/对质：不能用证据持有替代任务完成。
	for evidence in db.evidence: state.evidence.append(evidence)
	check("仅持有证据不能跳过暗房演出", not director.quest_ready(back))
	state.quests_done.append("c6_darkroom")
	check("暗房完成后可返回客房并结束探索", director.quest_ready(back) and director.quest_ends(back))
	check("暗房播放包含完整显影对质范围", darkroom.shot == "C6-03" and darkroom.until == "C6-07")
	for id in ["C5-12", "C6-01", "C6-10", "C7-01"]:
		var names: Array = Actions.parse(db.shots[id].actions).map(func(a): return a.name)
		check(id + "保持不眠连续性", not names.any(func(n): return n in ["sleep", "wake", "recap", "diary"]))
	check("客房自查包含镜子", db.shots["C6-02"].actions.contains("hs_mirror_guest"))
	check("自查后从暗房任务回到证据板", director.resolve_next(db.shots["C6-02"]) == "C6-08")
	check("无眠段固定在打字机", db.shots["C6-10"].camera == "typewriter_close")
	quit(0 if failures == 0 else 1)
