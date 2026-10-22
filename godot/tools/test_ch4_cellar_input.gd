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

func run() -> void:
	create_timer(90).timeout.connect(func(): printerr("CH4_INPUT timeout"); quit(2))
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
	for entry in [
		["hs_cellar_book", Vector3(0.82, 0.03, 0.65)],
		["hs_cellar_notes", Vector3(-0.4, 0.03, 0.65)],
		["hs_cellar_relics", Vector3(-3.25, 0.03, -1.9)],
		["hs_cellar_portraits", Vector3(0, 0.03, -2.9)],
		["hs_cellar_camera", Vector3(0.36, 0.03, 0.65)]
	]:
		if not await inspect(entry[0], entry[1]):
			quit(1)
			return
	var cellar: Node = host.room
	check("正常E拿到相机", cellar.has_camera)
	var overlay_id: int = cellar.camera_overlay.get_instance_id()
	var previous_fov: float = host.player.cam.fov
	key(KEY_F)
	await process_frame
	check("F举镜", cellar.camera_raised)
	await aim(Vector3(-1.82, 0.03, -2.2), Vector3(-1.82, 1.95, -3.92))
	for i in 12:
		mouse(MOUSE_BUTTON_WHEEL_UP)
	await process_frame
	check("滚轮对焦并瞄准1920", cellar.focus >= 0.82 and cellar.current_aim_year == 1920)
	if OS.get_cmdline_user_args().has("--capture-a1"):
		await create_timer(0.5).timeout
		await RenderingServer.frame_post_draw
		root.get_texture().get_image().save_png("/tmp/ch4-a1-raised.png")

	key(KEY_ESCAPE)
	await process_frame
	check("举镜时Esc打开暂停", ui.menus.visible and host.player.frozen)
	await process_frame
	check("暂停时取景器隐藏", not cellar.camera_overlay.visible)
	var focus: float = cellar.focus
	key(KEY_F)
	key(KEY_R)
	mouse(MOUSE_BUTTON_WHEEL_DOWN)
	mouse(MOUSE_BUTTON_LEFT)
	await process_frame
	check("暂停不响应摄影操作", cellar.camera_raised and cellar.focus == focus and cellar.plate_state == "NONE")
	key(KEY_ESCAPE)
	await process_frame
	mouse(MOUSE_BUTTON_LEFT)
	await process_frame
	check("正常左键首曝", cellar.plate_state == "EXPOSED" and not ui.inspector.active)
	check("首曝后显影盘是实际交互目标", host.active_hotspots.has("hs_cellar_tray"))
	if not host.active_hotspots.has("hs_cellar_tray"):
		print("CH4_INPUT failures=", failures)
		quit(1)
		return
	key(KEY_F)
	await aim(Vector3(-3.35, 0.03, -0.9), host.hotspot_nodes["hs_cellar_tray"].global_position)
	check("显影盘可选中", host.player._hover == "hs_cellar_tray")
	key(KEY_E)
	await process_frame
	check("E第一次显影且不打开无关检视", cellar.plate_state == "DEVELOPED" and not ui.inspector.active)
	key(KEY_R)
	await process_frame
	check("放下相机后R可拨杆", cellar.plate_state == "ARMED")
	key(KEY_F)
	await aim(Vector3(-1.82, 0.03, -2.2), Vector3(-0.55, 1.95, -3.92))
	mouse(MOUSE_BUTTON_LEFT)
	await process_frame
	check("错误年份二曝不推进", cellar.plate_state == "ARMED")
	await aim(Vector3(-1.82, 0.03, -2.2), Vector3(-1.82, 1.95, -3.92))
	mouse(MOUSE_BUTTON_LEFT)
	await process_frame
	check("同年份二曝", cellar.plate_state == "EXPOSED2")
	key(KEY_F)
	await aim(Vector3(-3.35, 0.03, -0.9), host.hotspot_nodes["hs_cellar_tray"].global_position)
	key(KEY_E)
	await process_frame
	check("E二次显影并交接梯子目标", cellar.cleared_years.has(1920) and host.active_hotspots.has("hs_cellar_ladder"))
	key(KEY_F)
	await process_frame
	check("带举镜状态走向出口", cellar.camera_raised)
	if not await inspect("hs_cellar_ladder", Vector3(3.1, 0.03, 1.5)):
		quit(1)
		return
	await until(func(): return finished, "镜头调查与返回结束")
	await process_frame
	check("返回庄园且FOV恢复", host.current_id == "manor" and is_equal_approx(host.player.cam.fov, previous_fov))
	check("离场清理手持相机与取景器", host.player.cam.get_node_or_null("CameraViewmodel") == null and not is_instance_id_valid(overlay_id))
	print("CH4_INPUT failures=", failures)
	main.queue_free()
	await process_frame
	quit(0 if failures == 0 else 1)
