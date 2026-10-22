extends SceneTree
## 可试玩：godot --path godot --script res://tools/demo_dialogue.gd
## 轻量冒烟与截图：追加 -- --smoke。独立运行，不读写正式存档。
var failures := 0
var main: Node
var director: Node
var host: Node
var ui: Node
var smoke := false
var phase := 0

func _initialize() -> void:
	call_deferred("run")

func key(code: Key) -> void:
	var event := InputEventKey.new()
	event.keycode = code
	event.physical_keycode = code
	event.pressed = true
	root.push_input(event, true)
	event = event.duplicate()
	event.pressed = false
	root.push_input(event, true)

func check(label: String, ok: bool) -> void:
	print("PASS " if ok else "FAIL ", label)
	if not ok:
		failures += 1

func capture(label: String) -> void:
	if DisplayServer.get_name() == "headless":
		return
	await RenderingServer.frame_post_draw
	root.get_texture().get_image().save_png("/tmp/dm-dialogue-" + label + ".png")

func run() -> void:
	smoke = OS.get_cmdline_user_args().has("--smoke")
	root.get_node("GameState").persist = false
	main = load("res://main.tscn").instantiate()
	root.add_child(main)
	await process_frame
	director = root.get_node("Director")
	host = director.world
	ui = director.ui
	ui.menus.hide()
	root.get_node("GameState").reset()
	root.get_node("GameState").shot = "C0-07"
	ui.set_cinematic(false)
	ui.eyelids_set(1.0)
	host.show_scene("seance")
	host.set_mode("walk", "")
	director._explore("c0")
	await physics_frame
	await physics_frame
	var npc: Node3D = host.named["seance/chr_拉坦特夫人"]
	# 真实人物面前的试玩起点；之后通过 E 触发真实探索任务。
	var feet: Vector3 = npc.global_position + npc.global_basis.z.normalized() * 2.0
	feet.y += 0.03
	# 只选真实地面且胶囊放得下的位置，避免出生在椅子上。
	var capsule := CapsuleShape3D.new()
	capsule.height = 1.65
	capsule.radius = 0.3
	for i in 64:
		var offset: Vector3 = npc.global_basis * Vector3(sin((i % 16) * TAU / 16), 0, cos((i % 16) * TAU / 16)) * (1.0 + floori(i / 16.0) * 0.3)
		var at: Vector3 = npc.global_position + offset
		var floor_query := PhysicsRayQueryParameters3D.create(at + Vector3.UP * 1.3, at - Vector3.UP * 0.4, 1)
		floor_query.exclude = [host.player.get_rid()]
		var floor_hit: Dictionary = host.player.get_world_3d().direct_space_state.intersect_ray(floor_query)
		if floor_hit.is_empty() or host.room_at(floor_hit.position) != "seance" or absf(floor_hit.position.y - npc.global_position.y) > 0.2:
			continue
		var shape_query := PhysicsShapeQueryParameters3D.new()
		shape_query.shape = capsule
		shape_query.collision_mask = 1
		shape_query.exclude = [host.player.get_rid()]
		shape_query.transform = Transform3D(Basis.IDENTITY, floor_hit.position + Vector3.UP * 0.95)
		var face: Vector3 = npc.global_position + Vector3.UP * 1.5
		var sight := PhysicsRayQueryParameters3D.create(floor_hit.position + Vector3.UP * 1.6, face, 1 | 4)
		sight.exclude = [host.player.get_rid()]
		var obstacle: Dictionary = host.player.get_world_3d().direct_space_state.intersect_ray(sight)
		if not obstacle.is_empty() and obstacle.collider != npc.get_child(0) and obstacle.position.distance_to(face) > 0.1:
			continue
		if host.player.get_world_3d().direct_space_state.intersect_shape(shape_query, 1).is_empty():
			feet = floor_hit.position + Vector3.UP * 0.03
			break
	host.player.place(feet, 0)
	await create_timer(0.4).timeout
	var eye: Vector3 = npc.global_position + Vector3.UP * 1.55
	var direction: Vector3 = eye - host.player.cam.global_position
	host.player.rotation.y = atan2(-direction.x, -direction.z)
	host.player._pitch = atan2(direction.y, Vector2(direction.x, direction.z).length())
	host.player.cam.rotation.x = host.player._pitch
	await create_timer(1.0).timeout
	host.player._update_hover()
	print("DEMO NPC target=", host.player._hover, " feet=", host.player.global_position, " npc=", npc.global_position, " room=", host.room_at(host.player.global_position))
	print("按 E 与拉坦特夫人交谈，鼠标转头，空格/点击继续。交谈后按 F8 看火车过场，F9 返回探索。")
	if not smoke:
		return
	create_timer(40).timeout.connect(func(): printerr("DIALOGUE_DEMO timeout"); quit(2))
	root.get_node("Settings").text_instant = true
	check("真实 NPC 可被交互瞄准", host.player._hover == "talk:拉坦特夫人@seance")
	var before: Transform3D = host.player.cam.global_transform
	var feet_before: Vector3 = host.player.global_position
	key(KEY_E)
	await create_timer(0.2).timeout
	check("E 接入原地 NPC 交谈且无黑边", director.conversation != "" and host.player.conversing and host.player.active and not ui._cinematic)
	check("交互不切相机不改视角", root.get_camera_3d() == host.player.cam and before.is_equal_approx(host.player.cam.global_transform))
	check("气泡可见且无底部重复字幕", ui.bubble.visible and not ui.text_panel.visible)
	await capture("npc")
	var motion := InputEventMouseMotion.new()
	motion.relative = Vector2(32, 6)
	root.push_input(motion, true)
	Input.action_press("move_forward")
	await create_timer(0.15).timeout
	Input.action_release("move_forward")
	check("交谈能转头但站位不变", not before.basis.is_equal_approx(host.player.cam.global_basis) and feet_before.is_equal_approx(host.player.global_position))
	# 转身后再回来；没有在屏幕边缘保留一个穿墙气泡。
	var yaw: float = host.player.rotation.y
	host.player.rotation.y += PI
	await process_frame
	await process_frame
	check("转身离开视野气泡收起", not ui.bubble.visible)
	host.player.rotation.y = yaw
	await create_timer(0.1).timeout
	var count := 0
	while director.conversation != "" and count < 40:
		key(KEY_SPACE)
		count += 1
		await create_timer(0.06).timeout
	check("真实台词分页推进后恢复探索", director.conversation == "" and not host.player.conversing and host.player.active and not ui.bubble.visible)
	check("长台词生成多个页面", ui.subtitle_pages("这是一段用于检查阅读体验的长台词。".repeat(10), 480, 24).size() > 1)
	# 同一入口切到真实火车镜头，展示长旁白分页与黑边。
	show_cutscene()
	await create_timer(1.0).timeout
	check("真实过场黑边伸出且字幕位于下黑边", ui._cinematic and ui.bar_bottom.size.y > 100 and ui.text_panel.position.y >= ui.bar_bottom.position.y)
	check("演出隐藏非必要 HUD", not ui.crosshair.visible and not ui.day_label.visible and not ui.keys.visible)
	await capture("cutscene")
	ui.cancel()
	await process_frame
	ui.set_cinematic(false)
	await create_timer(0.7).timeout
	check("黑边可收回且恢复 HUD", ui.bar_bottom.size.y < 1 and ui.crosshair.visible)
	# 再触发一次真实 NPC 台词并取消，检查跨页等待能退出。
	director.conversation = "talk:拉坦特夫人@seance"
	host.show_scene("seance")
	host.player.conversing = true
	director._say("c0_latente")
	await process_frame
	ui.cancel()
	await process_frame
	check("取消不会继续挂起下一句气泡", not ui._waiting and not ui.bubble.visible)
	director.conversation = ""
	host.player.conversing = false
	# 真实任务里交谈后会接实地检查，不能继续锁住玩家。
	director.conversation = "talk:拉坦特夫人@seance"
	host.player.conversing = true
	var walk_fixture: Dictionary = root.get_node("ContentDB").shots["C5-03"].duplicate()
	walk_fixture["mode"] = "walk" # 独立检查交谈后恢复行走；不接入尚未提交的实物热区。
	director._play(walk_fixture)
	await create_timer(1.0).timeout
	check("交谈后进入实地检查会解除移动限制", director.conversation == "" and not host.player.conversing and host.player.active and not ui._cinematic)
	director.inspected.emit(director.CANCEL)
	await process_frame
	ui.show_text("不必把视线交给镜头。站在这里，也能继续听她说话。")
	await create_timer(0.15).timeout
	await capture("plain")
	ui.cancel()
	await process_frame
	ui.footage.set_live("档案卡", "DEMO", "001/001", "1926/10/16 21:00")
	ui.show_text("档案字幕沿用自己的媒介外观，文字同样无需大面积底板。")
	await create_timer(0.15).timeout
	check("档案字幕保留独立播放入口", ui.footage._subtitle.visible and not ui.text_panel.visible)
	ui.cancel()
	await process_frame
	print("DIALOGUE_DEMO failures=", failures)
	main.queue_free()
	await process_frame
	quit(0 if failures == 0 else 1)

func show_cutscene() -> void:
	director.inspected.emit(director.CANCEL)
	ui.cancel()
	director._play(root.get_node("ContentDB").shots["C0-02"])
	phase = 1

func _process(_dt: float) -> bool:
	if smoke or ui == null:
		return false
	if Input.is_physical_key_pressed(KEY_F8) and phase == 0 and director.conversation == "":
		show_cutscene()
	if Input.is_physical_key_pressed(KEY_F9) and phase == 1:
		ui.cancel()
		host.show_scene("seance")
		host.set_mode("walk", "")
		ui.set_cinematic(false)
		director._explore("c0")
		phase = 0
	return false
