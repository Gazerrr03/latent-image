extends SceneTree
## 真实输入检查：正常镜头调查、拿相机、快门、显影与返回；不代替人工走动验收。
var failures := 0
var director: Node
var host: Node
var ui: Node
var main: Node
var finished := false

func _initialize() -> void:
	call_deferred("run")

func check(label: String, ok: bool) -> void:
	print("PASS " if ok else "FAIL ", label)
	if not ok:
		failures += 1

func until(predicate: Callable, label: String) -> bool:
	for i in 80:
		if predicate.call():
			return true
		await create_timer(0.05).timeout
	check(label, false)
	return false

func key(code: Key) -> void:
	var event := InputEventKey.new()
	event.keycode = code
	event.physical_keycode = code
	event.pressed = true
	root.push_input(event, true)
	event = event.duplicate()
	event.pressed = false
	root.push_input(event, true)

func mouse(button: MouseButton) -> void:
	var event := InputEventMouseButton.new()
	event.button_index = button
	event.position = Vector2(10, 10)
	event.pressed = true
	root.push_input(event, true)
	event = event.duplicate()
	event.pressed = false
	root.push_input(event, true)

func aim(feet: Vector3, point: Vector3) -> void:
	host.player.place(feet, 0)
	await physics_frame
	await physics_frame
	var delta: Vector3 = point - host.player.cam.global_position
	host.player.rotation.y = atan2(-delta.x, -delta.z)
	host.player._pitch = atan2(delta.y, Vector2(delta.x, delta.z).length())
	host.player.cam.rotation.x = host.player._pitch
	host.player._update_hover()
	await process_frame

func inspect(id: String, feet: Vector3) -> bool:
	var target: Node3D = host.hotspot_nodes[id]
	await aim(feet, target.global_position)
	check(id + " 室内站位可选中", host.player._hover == id)
	key(KEY_E)
	if not await until(func(): return ui.inspector.active, id + " E打开检视"):
		return false
	await create_timer(0.3).timeout
	var cellar: Node = host.room
	var raised: bool = cellar.camera_raised
	var is_ladder: bool = id == "hs_cellar_ladder"
	key(KEY_F)
	await process_frame
	check(id + " 阅读F不误举镜", (is_ladder or cellar.camera_raised == raised) and ui.inspector.reading)
	key(KEY_ESCAPE)
	await process_frame
	key(KEY_ESCAPE)
	return await until(func(): return not ui.inspector.active and not host.player.frozen, id + " 退出检视")

func play_range() -> void:
	await director._play_range("C4-09", "C4-09")
	finished = true

func interact(id: String, feet: Vector3) -> void:
	await aim(feet, host.hotspot_nodes[id].global_position)
	check(id + " 站位可选中", host.player._hover == id)
	key(KEY_E)
	await process_frame

func read_book() -> void:
	await interact("hs_cellar_book", Vector3(0.82, 0.03, 0.65))
	if not await until(func(): return ui.inspector.active, "记录本打开"): return
	await create_timer(0.3).timeout
	key(KEY_F)
	await process_frame
	for i in ui.inspector.pages.size() - 1:
		key(KEY_D)
		await process_frame
	key(KEY_ESCAPE)
	await process_frame
	key(KEY_ESCAPE)
	await until(func(): return not ui.inspector.active and not host.player.frozen, "记录本退出")

func shot(year: int) -> void:
	var x: float = {1920: -1.82, 1926: 2.02}[year]
	await aim(Vector3(x, 0.03, -2.2), Vector3(x, 1.95, -3.92))
	mouse(MOUSE_BUTTON_LEFT)
	await process_frame

func run() -> void:
	create_timer(100).timeout.connect(func(): printerr("CH4_INPUT timeout"); quit(2))
	var state := root.get_node("GameState")
	state.persist = false
	main = load("res://main.tscn").instantiate()
	root.add_child(main)
	await process_frame
	director = root.get_node("Director")
	host = director.world
	ui = director.ui
	ui.menus.hide()
	state.reset()
	director.skip_text = true
	play_range()
	await process_frame
	await interact("hs_cellar_camera", Vector3(0.36, 0.03, 0.65))
	var cellar: Node = host.room
	check("Q下一步指向1920肖像", director.guide_targets() == ["hs_cellar_portraits"])
	check("地下室Q实际生成路径", await host.show_guide(director.guide_targets()))
	check("E拿到相机", cellar.has_camera)
	var previous_fov: float = host.player.cam.fov
	key(KEY_F)
	await process_frame
	for i in 12: mouse(MOUSE_BUTTON_WHEEL_UP)
	await shot(1920)
	check("正常输入首曝", cellar.plate_state == "EXPOSED")
	key(KEY_F)
	await interact("hs_cellar_tray", Vector3(-3.35, 0.03, -0.9))
	check("显影不直接可二曝", cellar.plate_state == "DEVELOPED")
	check("Q引导返回记录本", director.guide_targets() == ["hs_cellar_book"])
	await read_book()
	check("翻页阅读解锁装回", cellar.rules.data.pages_read.has("reload"))
	await interact("hs_cellar_holder", Vector3(1.25, 0.03, 0.15))
	check("E实体片夹装回", cellar.plate_state == "LOADED2")
	key(KEY_R)
	await process_frame
	check("R拨杆", cellar.plate_state == "ARMED")
	key(KEY_F)
	await shot(1920)
	key(KEY_F)
	await interact("hs_cellar_tray", Vector3(-3.35, 0.03, -0.9))
	check("1920完成后仍未调查完成", cellar.rules.data.cleared.has("1920") and not cellar.rules.data.complete)
	# 提前离开，重新进入：相机/干版/页面仍在。
	await interact("hs_cellar_ladder", Vector3(3.1, 0.03, 1.5))
	await until(func(): return finished, "提前返回温室")
	check("提前离开不完成地下室任务", not state.quests_done.has("c4_cellar") and not state.cellar.complete)
	finished = false
	play_range()
	await process_frame
	cellar = host.room
	await process_frame
	check("重入恢复1920与相机", cellar.has_camera and cellar.rules.data.cleared.has("1920"))
	key(KEY_F)
	await interact("hs_cellar_cabinet", Vector3(-3.5, 0.03, 2.6))
	check("举镜发现钥匙但未拿到", cellar.rules.data.key_seen and not cellar.rules.data.has_key)
	key(KEY_F)
	await read_book()
	check("读夹层拿到钥匙", cellar.rules.data.has_key)
	await interact("hs_cellar_cabinet", Vector3(-3.5, 0.03, 2.6))
	check("柜子开锁", cellar.rules.data.box_open)
	key(KEY_F)
	await aim(Vector3(2.02, 0.03, -2.2), Vector3(2.02, 1.95, -3.92))
	key(KEY_E)
	await process_frame
	check("E观察1926", cellar.rules.data.final_seen)
	key(KEY_F)
	await interact("hs_cellar_plate", Vector3(-3.35, 0.03, 2.85))
	check("E拿实体1926底片", cellar.rules.data.final_taken)
	if OS.get_cmdline_user_args().has("--observe"):
		await interact("hs_cellar_holder", Vector3(1.25, 0.03, 0.15))
		key(KEY_F)
		for i in 12: mouse(MOUSE_BUTTON_WHEEL_UP)
		await shot(1926)
		await shot(1926)
		key(KEY_F)
		check("1926装片观察路径", cellar.rules.data.final_choice == "observe")
	else:
		await interact("hs_cellar_cabinet", Vector3(-3.5, 0.03, 2.6))
		check("1926放回路径", cellar.rules.data.final_choice == "keep")
	for entry in [["hs_cellar_notes", Vector3(-0.4, 0.03, 0.65)], ["hs_cellar_clip", Vector3(-0.9, 0.03, 0.65)], ["hs_cellar_relics", Vector3(-3.25, 0.03, -1.9)]]:
		await inspect(entry[0], entry[1])
	check("核心资料阅读后完成", cellar.rules.data.complete)
	if OS.get_cmdline_user_args().has("--capture-a6"):
		await aim(Vector3(3.1, 0.03, 1.4), Vector3(0, 1.4, -0.5))
		await create_timer(0.5).timeout
		await RenderingServer.frame_post_draw
		root.get_texture().get_image().save_png("/tmp/ch4-a6-investigation.png")
	await interact("hs_cellar_ladder", Vector3(3.1, 0.03, 1.5))
	await until(func(): return finished, "完成后返回温室")
	check("返回恢复FOV", is_equal_approx(host.player.cam.fov, previous_fov))
	check("独立地下室已卸载", host.current_id == "manor")
	print("CH4_INPUT failures=", failures)
	quit(0 if failures == 0 else 1)
