extends SceneTree
## 实际加载游戏、真实物件和检视输入，保存渲染截图；不写玩家存档。
var failures := 0
var ui: Node
var player: Node3D
var inspector: CanvasLayer
var Director: Node
var GameState: Node

func _initialize() -> void:
	call_deferred("run")

func check(label: String, ok: bool) -> void:
	print("PASS " if ok else "FAIL ", label)
	if not ok:
		failures += 1

func key(code: Key) -> void:
	var ev := InputEventKey.new()
	ev.physical_keycode = code
	ev.keycode = code
	ev.pressed = true
	Input.parse_input_event(ev)
	ev = ev.duplicate()
	ev.pressed = false
	Input.parse_input_event(ev)

func wait_closed() -> void:
	for i in 90:
		if not inspector.active:
			return
		await process_frame

func click(control: Control) -> void:
	var ev := InputEventMouseButton.new()
	ev.position = control.get_global_rect().get_center()
	ev.button_index = MOUSE_BUTTON_LEFT
	ev.pressed = true
	# 按逻辑视口坐标注入，避免 1280 窗口 / 1600 设计视口再次缩放坐标。
	root.push_input(ev, true)
	ev = ev.duplicate()
	ev.pressed = false
	root.push_input(ev, true)

func run() -> void:
	Director = root.get_node("Director")
	GameState = root.get_node("GameState")
	GameState.persist = false
	var main: Node = load("res://main.tscn").instantiate()
	root.add_child(main)
	await process_frame
	GameState.persist = false
	ui = Director.ui
	GameState.reset()
	ui.menus.hide()
	Director.world.show_scene("guest_room")
	Director.world.set_mode("walk", "")
	ui.set_cinematic(false)
	ui.eyelids_set(1.0)
	player = Director.world.player
	inspector = ui.inspector
	await create_timer(0.3).timeout
	var camera: Camera3D = root.get_camera_3d()
	var before := camera.global_transform
	var fov := camera.fov
	var mouse := Input.mouse_mode
	var body: Node3D = Director.world.hotspot_nodes.get("hs_notebook")
	check("场景真实热区存在", body != null)
	var meshes: Array = []
	for n in Director.world._walk(Director.world.room):
		if n is MeshInstance3D and String(n.name) == "客房·记事本":
			meshes.append(n)
	check("真实记事本网格存在", not meshes.is_empty())
	Director.world.highlight_hotspots(["hs_notebook"])
	var overlay_before: Material = meshes[0].material_overlay
	var data := {"title": "记事本", "mode": "portable", "pages": ["第一页\n十月十六日，九点，我到达。", "第二页\n检视输入验证"]}
	inspector.open(data, meshes, body.global_position, [ui.crosshair, ui.checklist_box])
	await create_timer(0.4).timeout
	check("检视冻结角色、释放鼠标并隐藏准星", player.frozen and Input.mouse_mode == Input.MOUSE_MODE_VISIBLE and not ui.crosshair.visible)
	check("检视隐藏现场真实高亮描边", overlay_before != null and meshes[0].material_overlay == null)
	check("便携检视使用真实网格且隐藏原件", inspector._portable and inspector._pivot.get_child_count() > 0 and not meshes[0].visible)
	var press := InputEventMouseButton.new()
	press.button_index = MOUSE_BUTTON_LEFT
	press.pressed = true
	Input.parse_input_event(press)
	var motion := InputEventMouseMotion.new()
	motion.relative = Vector2(70, -30)
	Input.parse_input_event(motion)
	await process_frame
	check("拖动能旋转实物", not inspector._pivot.basis.is_equal_approx(Basis.IDENTITY))
	var basis_before: Basis = inspector._pivot.basis
	key(KEY_F)
	await process_frame
	check("F 进入阅读", inspector.reading and inspector._read_panel.visible)
	key(KEY_D)
	await process_frame
	check("D 翻页并更新正文", inspector.page == 1 and inspector._text.text.contains("第二页"))
	key(KEY_ESCAPE)
	await process_frame
	check("Esc 从阅读返回且保留观察角度", inspector.active and not inspector.reading and inspector._pivot.basis.is_equal_approx(basis_before) and not ui.menus.visible)
	await RenderingServer.frame_post_draw
	root.get_texture().get_image().save_png("/tmp/dm-inspector-portable.png")
	key(KEY_R)
	await process_frame
	check("R 复位", inspector._pivot.basis.is_equal_approx(inspector._home_basis))
	for i in 30:
		var wheel := InputEventMouseButton.new()
		wheel.button_index = MOUSE_BUTTON_WHEEL_UP
		wheel.pressed = true
		root.push_input(wheel, true)
	check("滚轮可放大且缩放有固定上限", inspector._zoom > 1.0 and inspector._zoom <= 1.75)
	var zoom_before_read: float = inspector._zoom
	click(inspector._read_button)
	await process_frame
	check("真实阅读按钮不启动拖动", inspector.reading and not inspector._dragging)
	key(KEY_ESCAPE)
	await process_frame
	check("阅读返回保留缩放", is_equal_approx(inspector._zoom, zoom_before_read))
	var restored := {}
	inspector.closed.connect(func():
		restored["transform"] = camera.global_transform
		restored["fov"] = camera.fov
		restored["frozen"] = player.frozen
		restored["mouse"] = Input.mouse_mode
		restored["source"] = meshes[0].visible
		restored["crosshair"] = ui.crosshair.visible, CONNECT_ONE_SHOT)
	key(KEY_ESCAPE)
	await wait_closed()
	# 在 closed 信号交还控制的同一时刻核对；其后正常输入和眼高平滑可以继续改变相机。
	check("退出恢复原件、角色、准星、鼠标与相机", not inspector.active and restored.get("source", false) and not restored.get("frozen", true) and restored.get("crosshair", false) and restored.get("mouse", -1) == mouse and restored.get("transform", Transform3D()).is_equal_approx(before) and is_equal_approx(restored.get("fov", 0.0), fov))
	check("放下恢复原先描边材质", meshes[0].material_overlay == overlay_before)
	inspector.open(data, meshes, body.global_position)
	await create_timer(0.3).timeout
	check("重复检视物件不会透明", is_equal_approx(inspector._stage.modulate.a, 1.0))
	inspector.close(true)
	check("中断立即恢复", not inspector.active and meshes[0].visible and not player.frozen)
	before = camera.global_transform
	inspector.open({"title": "桌面现场", "mode": "fixed", "text": "现场观察记录"}, [], body.global_position)
	await create_timer(0.3).timeout
	check("现场特写不复制或拿走物品", not inspector._portable and meshes[0].visible and camera.fov < fov)
	await RenderingServer.frame_post_draw
	root.get_texture().get_image().save_png("/tmp/dm-inspector-fixed.png")
	inspector.close()
	await process_frame
	inspector.close(true)
	check("退出过渡中也可立即中断", not inspector.active and camera.global_transform.is_equal_approx(before) and not player.frozen)
	player.frozen = true
	inspector.open(data, meshes, body.global_position)
	inspector.close(true)
	check("保留进入前已有的冻结状态", player.frozen)
	player.frozen = false
	# 完整 Director 路径：第一次收入、任务结束后仍可回看，重复不增证据。
	Director.world.show_scene("darkroom")
	Director.world.set_mode("walk", "")
	Director.world.highlight_hotspots([])
	await process_frame
	Director._show_hotspot("hs_tray")
	await create_timer(0.3).timeout
	check("场景入口已进入检视", inspector.active)
	inspector.close(true)
	await process_frame
	check("首次检视后收入证据", GameState.evidence.has("ev_tray_crystal"))
	var count: int = GameState.evidence.size()
	Director.reinspect("hs_tray")
	await create_timer(0.3).timeout
	check("不在当前任务列表的已见线索仍可检视", inspector.active)
	inspector.close(true)
	await process_frame
	check("重复检视不重复收集且恢复角色", GameState.evidence.size() == count and not player.frozen and GameState.inspected.count("hs_tray") == 1)
	GameState.evidence.erase("ev_tray_crystal")
	Director._show_hotspot("hs_tray")
	await process_frame
	Director._jump_to = "C0-11"
	ui.cancel()
	await process_frame
	check("剧情中断立即恢复且不发放未完成线索", not inspector.active and not player.frozen and not GameState.evidence.has("ev_tray_crystal"))
	Director._jump_to = ""
	# 笔记本通过真实卡片点击进入同一个实物检视器。
	GameState.add_evidence("ev_letter_p2")
	GameState.add_evidence("ev_amb_words")
	GameState.add_evidence("ev_ledger_last")
	ui.browse_board()
	await process_frame
	click(ui.board.cards["ev_letter_p2"])
	await create_timer(0.4).timeout
	check("笔记本真实卡片打开实物信件", inspector.active and inspector._portable and inspector._model != null and not inspector.reading)
	if inspector._model == null:
		quit(1)
		return
	await RenderingServer.frame_post_draw
	root.get_texture().get_image().save_png("/tmp/dm-inspector-letter-front.png")
	check("信件正面纹理为该信原文", inspector._model.front.material_override.albedo_texture.resource_path.contains("ev_letter_p2_0_front"))
	key(KEY_V)
	await create_timer(0.3).timeout
	check("V 翻到真实背面", inspector._flipped and inspector._object_yaw > 3.0)
	await RenderingServer.frame_post_draw
	root.get_texture().get_image().save_png("/tmp/dm-inspector-letter-back.png")
	key(KEY_F)
	await process_frame
	check("阅读对应当前背面而不是泄露正面", inspector.reading and inspector._text.text == "背面没有文字。")
	key(KEY_ESCAPE)
	await process_frame
	check("Esc 从信件阅读回到同一背面", inspector.active and not inspector.reading and inspector._flipped)
	key(KEY_ESCAPE)
	await wait_closed()
	check("退出实物后笔记本仍打开且角色仍冻结", ui.board.visible and player.frozen)
	click(ui.board.cards["ev_ledger_last"])
	await create_timer(0.3).timeout
	var texture_before: Texture2D = inspector._model.front.material_override.albedo_texture
	key(KEY_D)
	await process_frame
	await create_timer(0.28).timeout
	check("实际翻页同时更换纸面和阅读原文", inspector._model.front.material_override.albedo_texture != texture_before and inspector.page == 1 and inspector.pages[1].contains("十月十五日"))
	var observed_basis: Basis = inspector._pivot.basis
	inspector.turn_page(-1)
	await create_timer(0.06).timeout
	check("翻页途中纸面实际转动", absf(inspector._page_turn) > 0.05)
	key(KEY_F)
	await process_frame
	check("翻页中进入阅读恢复平面且保留观察姿态", inspector.reading and is_zero_approx(inspector._page_turn) and inspector._pivot.basis.is_equal_approx(observed_basis) and inspector.page == 0 and inspector._model.front.material_override.albedo_texture == texture_before)
	inspector.close(true)
	click(ui.board.cards["ev_amb_words"])
	await create_timer(0.3).timeout
	check("证词作为可读记录进入同一检视器", inspector.active and inspector.reading and inspector._record and inspector._text.text.contains("信的第二页"))
	key(KEY_ESCAPE)
	await wait_closed()
	check("证词 Esc 直接返回笔记本", ui.board.visible and player.frozen)
	key(KEY_ESCAPE)
	await process_frame
	check("再按 Esc 合上笔记本并恢复行走", not ui.board.visible and not player.frozen)
	# 每种正式文档资源都实际实例化并翻遍所有纸面，避免只有测试信件可用。
	var documents: Array = []
	for row in root.get_node("ContentDB").load_table("res://content/visual/inspection_pages.csv"):
		if not documents.has(row["object"]):
			documents.append(row["object"])
	for id in documents:
		ui.inspect_evidence(id, "", "")
		await process_frame
		var valid: bool = inspector.active and inspector._model != null
		if valid:
			for index in inspector.pages.size():
				valid = valid and inspector._model.front.material_override.albedo_texture.resource_path.ends_with("%s_%d_front.png" % [id, index])
				valid = valid and inspector._model.back.material_override.albedo_texture.resource_path.ends_with("%s_%d_back.png" % [id, index])
				if index < inspector.pages.size() - 1:
					inspector.turn_page(1)
					await create_timer(0.27).timeout
		check("文档全部纸面资源可用：" + id, valid)
		if id in ["ev_ticket", "ev_clipping", "ev_con_ledger", "ev_seance_cards"]:
			inspector.reset_view()
			await create_timer(0.3).timeout
			await RenderingServer.frame_post_draw
			root.get_texture().get_image().save_png("/tmp/dm-inspector-%s.png" % id)
		inspector.close(true)
	print("INSPECTOR failures=", failures)
	main.queue_free()
	await process_frame
	await process_frame
	await RenderingServer.frame_post_draw
	quit(0 if failures == 0 else 1)
