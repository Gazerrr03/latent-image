extends SceneTree
var failures := 0
var director: Node
var controls: Node
var choice_result := -1

func _initialize() -> void:
	call_deferred("run")

func check(label: String, ok: bool) -> void:
	print("PASS " if ok else "FAIL ", label)
	if not ok: failures += 1

func button(code: JoyButton) -> void:
	var ev := InputEventJoypadButton.new()
	ev.button_index = code
	ev.pressed = true
	Input.parse_input_event(ev)
	await process_frame
	ev = ev.duplicate()
	ev.pressed = false
	Input.parse_input_event(ev)
	await process_frame

func hold_button(code: JoyButton, pressed: bool) -> void:
	var ev := InputEventJoypadButton.new()
	ev.button_index = code
	ev.pressed = pressed
	Input.parse_input_event(ev)
	await process_frame

func axis(code: JoyAxis, value: float) -> void:
	var ev := InputEventJoypadMotion.new()
	ev.axis = code
	ev.axis_value = value
	Input.parse_input_event(ev)
	await process_frame

func run() -> void:
	director = root.get_node("Director")
	controls = root.get_node("Controls")
	print("Connected physical controllers: ", Input.get_connected_joypads())
	root.get_node("GameState").persist = false
	var main: Node = load("res://main.tscn").instantiate()
	root.add_child(main)
	await process_frame
	var ui: Node = director.ui
	await button(JOY_BUTTON_DPAD_DOWN)
	check("标题菜单方向键获得焦点", root.gui_get_focus_owner() != null)
	ui.menus.hide()
	director.world.show_scene("guest_room")
	director.world.set_mode("walk", "")
	ui.set_cinematic(false)
	var pl: Node3D = director.world.player
	await create_timer(0.1).timeout
	await axis(JOY_AXIS_LEFT_Y, -0.1)
	check("左摇杆死区不移动", Input.get_vector("move_left", "move_right", "move_forward", "move_back").is_zero_approx())
	await axis(JOY_AXIS_LEFT_Y, -0.6)
	check("半推保留模拟力度", Input.get_vector("move_left", "move_right", "move_forward", "move_back").length() > 0.0 and Input.get_vector("move_left", "move_right", "move_forward", "move_back").length() < 0.8)
	# 暂离家具碰撞范围，检查控制力度本身；随后回到出生点。
	var spawn: Vector3 = pl.global_position
	pl.global_position.y += 4.0
	await create_timer(0.08).timeout
	check("角色按摇杆力度慢走", Vector2(pl.velocity.x, pl.velocity.z).length() > 0.0 and Vector2(pl.velocity.x, pl.velocity.z).length() < pl.SPEED)
	await axis(JOY_AXIS_LEFT_Y, 0.0)
	await create_timer(0.05).timeout

	# 疾跑测试：手柄按住 R1 / 键盘按住 Shift
	await hold_button(JOY_BUTTON_RIGHT_SHOULDER, true)
	await create_timer(0.04).timeout
	check("原地静止时长按 R1 不触发疾跑", not pl.sprinting)
	await hold_button(JOY_BUTTON_RIGHT_SHOULDER, false)

	await axis(JOY_AXIS_LEFT_Y, -1.0)
	await create_timer(0.08).timeout
	var walk_spd: float = Vector2(pl.velocity.x, pl.velocity.z).length()
	check("推满左摇杆为常速走", absf(walk_spd - pl.SPEED) < 0.2)

	await hold_button(JOY_BUTTON_RIGHT_SHOULDER, true)
	await create_timer(0.08).timeout
	var sprint_spd_pad: float = Vector2(pl.velocity.x, pl.velocity.z).length()
	check("手柄长按 R1 移动中加速为疾跑", pl.sprinting and sprint_spd_pad > walk_spd + 0.5)
	await hold_button(JOY_BUTTON_RIGHT_SHOULDER, false)
	await create_timer(0.08).timeout
	check("手柄松开 R1 恢复常速", not pl.sprinting)

	Input.action_press("sprint")
	await create_timer(0.08).timeout
	var sprint_spd_key: float = Vector2(pl.velocity.x, pl.velocity.z).length()
	check("键盘长按 Shift 移动中加速为疾跑", pl.sprinting and sprint_spd_key > walk_spd + 0.5)
	Input.action_release("sprint")
	await create_timer(0.08).timeout
	check("键盘松开 Shift 恢复常速", not pl.sprinting)

	await axis(JOY_AXIS_LEFT_Y, 0.0)
	pl.global_position = spawn
	var yaw: float = pl.rotation.y
	await axis(JOY_AXIS_RIGHT_X, 1.0)
	await create_timer(0.1).timeout
	check("右摇杆转动镜头", absf(pl.rotation.y - yaw) > 0.01)
	await axis(JOY_AXIS_RIGHT_X, 0.0)
	await button(JOY_BUTTON_START)
	check("Menu 暂停并冻结角色", ui.menus.visible and pl.frozen)
	yaw = pl.rotation.y
	await axis(JOY_AXIS_RIGHT_X, 1.0)
	await create_timer(0.1).timeout
	check("暂停时镜头不动", is_equal_approx(pl.rotation.y, yaw))
	await axis(JOY_AXIS_RIGHT_X, 0.0)
	await button(JOY_BUTTON_B)
	check("B 返回探索", not ui.menus.visible and not pl.frozen)
	ui._resolved.connect(func(value): choice_result = value, CONNECT_ONE_SHOT)
	ui.choose("手柄选项测试", ["第一项", "第二项"])
	await process_frame
	await button(JOY_BUTTON_DPAD_DOWN)
	await button(JOY_BUTTON_A)
	check("方向键选项后 A 确认", choice_result == 1 and not ui.choice_panel.visible)
	await button(JOY_BUTTON_Y)
	check("Y 打开笔记本", ui.board.visible and pl.frozen)
	await button(JOY_BUTTON_B)
	check("B 合上笔记本", not ui.board.visible and not pl.frozen)
	# 真实证据卡、焦点和检视返回；仅修改内存，不写存档。
	var state: Node = root.get_node("GameState")
	state.evidence.assign(["ev_inf_d1"])
	await button(JOY_BUTTON_Y)
	check("证据板卡片获得焦点", root.gui_get_focus_owner() != null and root.gui_get_focus_owner() in ui.board.cards.values())
	await button(JOY_BUTTON_A)
	await create_timer(0.35).timeout
	check("A 检视卡片且保留笔记本", ui.inspector.active and ui.board.visible)
	await button(JOY_BUTTON_B)
	await create_timer(0.25).timeout
	check("B 退出记录检视且不误关笔记本", not ui.inspector.active and ui.board.visible)
	await button(JOY_BUTTON_B)
	var inspector: Node = ui.inspector
	ui.inspect_evidence("ev_letter_p1", "", "")
	await create_timer(0.3).timeout
	check("真实信纸资源可用手柄检视", inspector.active and inspector._portable and inspector._model != null)
	await button(JOY_BUTTON_B)
	await create_timer(0.25).timeout
	check("真实信纸放下恢复探索", not inspector.active and not pl.frozen)
	var prop := MeshInstance3D.new()
	prop.mesh = BoxMesh.new()
	root.add_child(prop)
	inspector.open({"title": "手柄测试", "mode": "portable", "pages": ["第一页", "第二页"], "can_flip": true, "notes": "观察记录"}, [prop], Vector3.ZERO, [])
	await create_timer(0.4).timeout
	await button(JOY_BUTTON_A)
	check("A 阅读且不会穿透关闭", inspector.active and inspector.reading)
	await button(JOY_BUTTON_RIGHT_SHOULDER)
	check("RB 翻页", inspector.page == 1)
	await button(JOY_BUTTON_B)
	check("B 返回物品", inspector.active and not inspector.reading)
	await axis(JOY_AXIS_TRIGGER_RIGHT, 1.0)
	await create_timer(0.1).timeout
	check("RT 放大物品", inspector._zoom > 1.0)
	await axis(JOY_AXIS_TRIGGER_RIGHT, 0.0)
	await axis(JOY_AXIS_RIGHT_X, 0.7)
	await create_timer(0.08).timeout
	check("右摇杆旋转检视物", not inspector._spin.is_zero_approx())
	await axis(JOY_AXIS_RIGHT_X, 0.0)
	await button(JOY_BUTTON_RIGHT_STICK)
	check("按下右摇杆翻面", inspector._flipped)
	await button(JOY_BUTTON_Y)
	check("Y 查看观察记录", inspector.reading and inspector._notes_mode)
	await button(JOY_BUTTON_B)
	await button(JOY_BUTTON_X)
	check("X 复位", is_equal_approx(inspector._zoom, 1.0))
	await button(JOY_BUTTON_B)
	await create_timer(0.25).timeout
	check("B 放下恢复探索", not inspector.active and not pl.frozen)
	check("动作注册可重复且不丢键鼠", InputMap.action_get_events("interact").size() == 2)
	controls.ensure_actions()
	check("重复注册没有多重绑定", InputMap.action_get_events("interact").size() == 2)
	ui.menus.open_pause()
	ui.menus._page_controls(func(): ui.menus._page_pause(), 1)
	await create_timer(0.15).timeout
	var rect: Rect2 = ui.menus._card.get_global_rect()
	check("手柄说明完整位于画面内", rect.position.y >= 0 and rect.end.y <= root.get_visible_rect().size.y)
	if DisplayServer.get_name() != "headless":
		await RenderingServer.frame_post_draw
		root.get_texture().get_image().save_png("res://../docs/验证/2026-10-20-手柄适配/controls.png")
	ui.menus._page_settings(func(): ui.menus._page_pause())
	await create_timer(0.15).timeout
	rect = ui.menus._card.get_global_rect()
	check("设置新增灵敏度后完整位于画面内", rect.position.y >= 0 and rect.end.y <= root.get_visible_rect().size.y)
	if DisplayServer.get_name() != "headless":
		await RenderingServer.frame_post_draw
		root.get_texture().get_image().save_png("res://../docs/验证/2026-10-20-手柄适配/settings.png")
	print("GAMEPAD failures=", failures)
	quit(0 if failures == 0 else 1)
