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
	var state: Node = root.get_node("GameState")
	state.evidence.assign(["ev_inf_d1"])
	await button(JOY_BUTTON_Y)
	check("旧版证据卡获得焦点",root.gui_get_focus_owner()!=null and root.gui_get_focus_owner() in ui.board.cards.values())
	await button(JOY_BUTTON_A)
	check("A打开旧版证据详情",ui.board._exam.visible)
	await button(JOY_BUTTON_B)
	check("B先返回证据板",not ui.board._exam.visible and ui.board.visible)
	await button(JOY_BUTTON_B)
	check("B合上证据板恢复行动",not ui.board.visible and not pl.frozen)
	print("STABLE_INPUT failures=",failures)
	main.queue_free()
	await process_frame
	quit(0 if failures==0 else 1)
