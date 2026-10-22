extends SceneTree
const Rules = preload("res://levels/cellar_state.gd")
var failures := 0
var d: Node
var state: Node
var main: Node
func _initialize() -> void: call_deferred("run")
func check(label: String, ok: bool) -> void:
	print("PASS " if ok else "FAIL ", label)
	if not ok: failures += 1
func until(test: Callable, label: String) -> void:
	for i in 150:
		if test.call(): return
		await create_timer(0.03).timeout
	check(label, false)
func task() -> Dictionary:
	return root.get_node("ContentDB").quests.c4.filter(func(q): return q.id == "c4_return")[0]
func explore() -> void: await d._explore("c4")
func run() -> void:
	create_timer(30).timeout.connect(func(): quit(2))
	state = root.get_node("GameState")
	state.persist = false
	main = load("res://main.tscn").instantiate()
	root.add_child(main)
	await process_frame
	d = root.get_node("Director")
	d.ui.menus.hide()
	d.skip_text = true
	state.reset()
	state.shot = "C4-01"
	state.quests_done = ["c4_gideon", "c4_vent"]
	check("线索前置不结束探索", not d.quest_ends(root.get_node("ContentDB").quests.c4.filter(func(q): return q.id == "c4_cellar")[0]))
	check("地下室未完成不能回客房收尾", not d.quest_ready(task()))
	explore()
	await process_frame
	d.inspected.emit("hs_gh_trapdoor")
	await until(func(): return d.world.current_id == "gh_cellar" and d.world.room._gameplay_active, "进入地下室")
	check("进入不等于完成", not state.quests_done.has("c4_cellar") and state.active_quest == "c4_cellar")
	d.inspected.emit("hs_cellar_camera")
	d.world.room.rules.shutter(1920, true)
	d.world.room.rules.develop()
	d.world.room._save_progress()
	# 真实文件保存/读回，备份和还原试验数据；不触及主项目数据目录。
	var path: String = state.SAVE_PATH
	var had: bool = FileAccess.file_exists(path)
	var backup: String = FileAccess.get_file_as_string(path) if had else ""
	state.persist = true
	state.save()
	state.reset()
	check("实际文件可载入", state.load_save())
	state.persist = false
	if had:
		var file := FileAccess.open(path, FileAccess.WRITE)
		file.store_string(backup)
		file.close()
	else: DirAccess.remove_absolute(ProjectSettings.globalize_path(path))
	check("首次显影与任务返回点读回", state.cellar.plate == "DEVELOPED" and state.active_quest == "c4_cellar" and state.explore_shot == "C4-01")
	d.inspected.emit("hs_cellar_ladder")
	await until(func(): return d.world.current_id == "manor" and state.active_quest == "", "提前返回")
	check("提前返回仍不能收尾", not state.quests_done.has("c4_cellar") and not d.quest_ready(task()))
	d.inspected.emit("hs_gh_trapdoor")
	await until(func(): return d.world.current_id == "gh_cellar" and d.world.room._gameplay_active, "再次进入")
	check("重入恢复显影状态", d.world.room.plate_state == "DEVELOPED")
	var checkpoint: Dictionary = state.to_dict().duplicate(true)
	# 中断探索，然后按正常继续调查入口恢复。
	d._jump_to = "END"
	d.inspected.emit(d.CANCEL)
	await process_frame
	d._jump_to = ""
	state.from_dict(checkpoint)
	d.start(state.shot)
	await until(func(): return d.world.current_id == "gh_cellar" and d.world.room._gameplay_active and d.running, "继续调查恢复地下室")
	check("继续从父探索恢复任务", state.active_quest == "c4_cellar" and not state.quests_done.has("c4_cellar"))
	# 使用同一规则完成玩法；输入层另有两条全流程测试。
	d.world.room.autoplay_cellar()
	d.inspected.emit("hs_cellar_ladder")
	await until(func(): return state.quests_done.has("c4_cellar"), "调查完再标记任务完成")
	check("完整调查后才开放章节收尾", d.quest_ready(task()) and state.cellar.complete)
	await d.stop()
	print("CH4_RESUME failures=", failures)
	quit(0 if failures == 0 else 1)
