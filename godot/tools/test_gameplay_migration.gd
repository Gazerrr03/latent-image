extends SceneTree
## 验证迁移后的进入/退出、取消、证据与存档边界；不代替人工解谜。
var failures := 0
func _initialize() -> void: call_deferred("run")
func check(label: String, ok: bool) -> void:
	print("PASS " if ok else "FAIL ", label)
	if not ok: failures += 1
func frames(n := 3) -> void:
	for i in n: await process_frame
func same_pose(actual: Transform3D, expected: Transform3D) -> bool:
	print("RESTORE actual=", actual.origin, " expected=", expected.origin)
	# 物理落地会调整脚下高度；检查水平位置和朝向，没有误传送。
	return Vector2(actual.origin.x, actual.origin.z).distance_to(Vector2(expected.origin.x, expected.origin.z)) < 0.15 and actual.basis.is_equal_approx(expected.basis)
func run() -> void:
	create_timer(90).timeout.connect(func(): quit(2))
	var state = root.get_node("GameState")
	var director = root.get_node("Director")
	var db = root.get_node("ContentDB")
	state.persist = false
	state.reset()
	var main = load("res://main.tscn").instantiate()
	root.add_child(main)
	await frames()
	director.ui.menus.hide()
	var host = director.world
	check("第一章保留新增问询", db.shots["C1-02"].actions.contains("inquire(c1_ask_constance)"))
	check("第五章保留主目录不眠衔接", not db.shots["C5-12"].actions.contains("sleep"))
	check("第二章任务包含餐桌", db.quests.c2[0].until == "C2-02a")
	host.show_scene("dining")
	host.set_mode("walk", "")
	state.shot = "C2-02a"
	var pose: Transform3D = host.player.global_transform
	director._do("level", ["ded_table", "ev_table_diagram"], "walk")
	await frames()
	var table = host._sublevel
	check("餐桌接管操作", is_instance_valid(table) and host.player.interaction_owner == table)
	table.solved = true
	table._finish()
	await frames()
	check("完成餐桌取得图纸证据", state.evidence.has("ev_table_diagram"))
	check("退出餐桌恢复位置和控制", host._sublevel == null and host.player.interaction_owner == null and same_pose(host.player.global_transform, pose))
	var restored: Dictionary = state.to_dict().duplicate(true)
	state.reset()
	state.from_dict(restored)
	check("图纸证据存档往返保留", state.evidence.has("ev_table_diagram"))
	state.evidence.erase("ev_table_diagram")
	director._do("level", ["ded_table", "ev_table_diagram"], "walk")
	await frames()
	host.cancel_level()
	await frames()
	check("取消餐桌不发放证据并归还控制", not state.evidence.has("ev_table_diagram") and host._sublevel == null and host.player.interaction_owner == null)
	host.show_scene("child_room")
	host.set_mode("walk", "")
	state.shot = "C3-04"
	state.set_leak(1)
	pose = host.player.global_transform
	var flow = main.get_node("Chapter3Trial")
	flow.enter_house()
	await frames()
	check("小屋正常入口不重置章节或禁用存档", flow.in_house and state.shot == "C3-04" and not state.persist)
	host.player.global_position = Vector3(0.5, 0, -21)
	await frames()
	check("穿过出口恢复调查位置和渗漏", not flow.in_house and state.leak_level == 1 and same_pose(host.player.global_transform, pose))
	flow.enter_house()
	await frames()
	host.cancel_level()
	await frames()
	check("中断小屋可返回且不残留运行状态", not flow.in_house and same_pose(host.player.global_transform, pose))
	flow.inspect_drawings()
	await frames()
	check("绘画集正常挂接", is_instance_valid(flow.gallery) and host.hotspot_nodes.has("hs_trial_drawing_collection"))
	director.inspected.emit("hs_trial_drawing_collection")
	await create_timer(0.7).timeout
	host.cancel_level()
	director.inspected.emit(director.CANCEL)
	await create_timer(0.6).timeout
	check("绘画选择界面中断可清理", not is_instance_valid(flow.gallery) and not db.hotspots.has("hs_trial_drawing_collection"))
	flow.inspect_drawings()
	await frames()
	director.inspected.emit("hs_trial_drawing_collection")
	await create_timer(0.1).timeout
	host.cancel_level()
	director.inspected.emit(director.CANCEL)
	await create_timer(1.1).timeout
	check("开画墙运镜中中断也能清理", not is_instance_valid(flow.gallery))
	flow.inspect_drawings()
	await frames()
	director.inspected.emit("hs_trial_drawing_collection")
	await create_timer(0.7).timeout
	var gallery = flow.gallery
	check("未看完五幅画时小屋锁定", gallery._house.disabled)
	if DisplayServer.get_name() != "headless":
		await RenderingServer.frame_post_draw
		root.get_texture().get_image().save_png("/tmp/gameplay-migration-drawings.png")
	for id in gallery.DRAWINGS:
		gallery._buttons[id].pressed.emit()
		await create_timer(0.4).timeout
		var inspector = director.ui.inspector
		check("绘画检视打开 " + id, inspector.active)
		await inspector.close()
		await create_timer(0.1).timeout
		check("绘画真实收集证据 " + id, gallery.reviewed.has(id) and state.evidence.has(db.hotspots[id].evidence))
		check("五幅看完前不能进入小屋 " + id, gallery._house.disabled == (gallery.reviewed.size() < 5))
	gallery.selected.emit(gallery.HOUSE)
	await create_timer(0.9).timeout
	check("绘画选择实际接入小屋", flow.in_house)
	host.player.global_position = Vector3(0.5, 0, -21)
	await frames(6)
	check("小屋完成后整个绘画流程结束", not flow.in_house and not is_instance_valid(flow.gallery) and not db.hotspots.has("hs_trial_drawing_collection"))
	print("GAMEPLAY_MIGRATION failures=", failures)
	quit(1 if failures else 0)
