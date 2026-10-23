extends SceneTree
## 从真实站位发送 E 键，走完三组调查；验证世界资源、章节可见性、收集和回看。
var director: Node
var host: Node
var ui: Node
var state: Node
var content: Node
var failures := 0
var group_finished := false
const GROUPS := {
	"child_room": ["C3-04", ["hs_draw_path", "hs_draw_wall", "hs_draw_family", "hs_draw_boxes", "hs_draw_train"]],
	"greenhouse": ["C4-03", ["hs_gh_latch", "hs_gh_photos"]],
	"seance": ["C5-03", ["hs_se_cards", "hs_se_photo", "hs_se_gloves"]],
}
func _initialize() -> void:
	call_deferred("run")
func check(label: String, ok: bool) -> void:
	print("PASS " if ok else "FAIL ", label)
	if not ok:
		failures += 1
func start_group(ids: Array) -> void:
	group_finished = false
	await director._inspect(ids, "walk")
	group_finished = true
func press_e() -> void:
	var ev := InputEventKey.new()
	ev.keycode = KEY_E
	ev.physical_keycode = KEY_E
	ev.pressed = true
	root.push_input(ev, true)
	ev = ev.duplicate()
	ev.pressed = false
	root.push_input(ev, true)
func pose(id: String, samples: Dictionary) -> void:
	var feet: Array = samples[id]["feet"]
	host.player.frozen = true
	host.player.place(Vector3(feet[0], feet[1], feet[2]), 0)
	var target: Node3D = host.hotspot_nodes[id]
	host.player.cam.look_at(target.global_position, Vector3.UP)
	host.player.frozen = false
	host.player._update_hover()
func run() -> void:
	state = root.get_node("GameState")
	state.persist = false
	var main: Node = load("res://main.tscn").instantiate()
	root.add_child(main)
	await process_frame
	state.reset()
	director = root.get_node("Director")
	content = root.get_node("ContentDB")
	host = director.world
	ui = director.ui
	ui.menus.hide()
	ui.eyelids_set(1.0)
	create_timer(180.0).timeout.connect(func():
		printerr("WORLD_INSPECTION timeout")
		quit(2))
	var rows: Array = JSON.parse_string(FileAccess.get_file_as_string("res://../docs/验证/2026-10-20-物品检视/逐对象判定.json"))
	var samples := {}
	for row in rows:
		samples[row["id"]] = row
	for room in GROUPS:
		var shot: String = GROUPS[room][0]
		var ids: Array = GROUPS[room][1]
		state.shot = shot
		host.show_scene(room)
		host.apply_room_states(shot)
		host.set_mode("walk", "")
		ui.set_cinematic(false)
		await physics_frame
		await physics_frame
		check("调查由 E 键现场操作：" + shot, content.shots[shot]["mode"] == "walk")
		if room == "child_room":
			host.apply_room_states("C2-03")
			check("新线索画在第三章之前不出现", ids.all(func(id): return not host.hotspot_nodes[id].is_visible_in_tree()))
			host.apply_room_states(shot)
		start_group(ids)
		for id in ids:
			pose(id, samples)
			if id == "hs_gh_latch" and host.player._door != null:
				var door: Node = host.player._door
				press_e()
				await create_timer(0.9).timeout
				check("门闩先打开挡在前面的真实侧门", host.door_is_open(door) and not ui.inspector.active)
				pose(id, samples)
			check("目标提示与对象一致：" + id, host.player._hover == id)
			press_e()
			await create_timer(0.35).timeout
			var valid: bool = ui.inspector.active
			check("E 进入目标检视：" + id, valid)
			if not valid:
				continue
			if room == "child_room" or id in ["hs_gh_photos", "hs_se_cards"]:
				check("实物资源不是观察卡片：" + id, ui.inspector._portable and ui.inspector._model != null)
			elif id == "hs_se_gloves":
				check("手套使用原场景网格", ui.inspector._portable and ui.inspector._pivot.get_child_count() > 0)
			check("检视期间现场描边已隐藏：" + id, host._walk(host.room).all(func(node): return not node is MeshInstance3D or node.material_overlay == null))
			if id == "hs_gh_latch":
				check("门闩内侧细节用局部照明且保持真实站位", is_instance_valid(ui.inspector._inspection_light) and host.player.global_position.x < host.hotspot_nodes[id].global_position.x and is_equal_approx(host.player.cam.fov, 18.0))
			await RenderingServer.frame_post_draw
			root.get_texture().get_image().save_png("/tmp/dm-world-" + id + ".png")
			ui.inspector.close(true)
			var evidence: String = content.hotspots[id].get("evidence", "")
			check("关闭后恢复行走并记录线索：" + id, not host.player.frozen and (evidence == "" or state.evidence.has(evidence)))
		check("整组调查完成：" + shot, group_finished and host.active_hotspots.is_empty())
		var count: int = state.evidence.size()
		pose(ids[0], samples)
		press_e()
		await create_timer(0.3).timeout
		check("任务结束后 E 可再次检视：" + shot, ui.inspector.active)
		ui.inspector.close(true)
		check("重复检视不增加证据：" + shot, state.evidence.size() == count)
	print("WORLD_INSPECTION failures=", failures)
	quit(0 if failures == 0 else 1)
