extends Node
## Branch-only manual trial. No save writes or new canonical evidence/rules.
signal returned

var in_house := false
var standalone := false
var _returning := false
var _saved := {}
var _label: Label

func enable_snapshot() -> void:
	_label = Label.new()
	_label.visible = false
	add_child(_label)

func begin(house_only: bool) -> void:
	GameState.persist = false
	GameState.reset()
	GameState.shot = "C3-01"
	standalone = house_only
	# Supply earlier clues for the chapter's existing show-clue interaction.
	for id in ContentDB.evidence:
		var group: String = ContentDB.evidence[id].get("conclusion", "")
		if group in ["D1", "D2"] or id in ["ev_letter_p1", "ev_amb_words"]:
			GameState.add_evidence(id)
	var layer := CanvasLayer.new()
	layer.layer = 40
	add_child(layer)
	_label = Label.new()
	_label.position = Vector2(18, 12)
	_label.add_theme_font_size_override("font_size", 18)
	_label.add_theme_color_override("font_shadow_color", Color.BLACK)
	_label.add_theme_constant_override("shadow_outline_size", 5)
	_label.mouse_filter = Control.MOUSE_FILTER_IGNORE
	layer.add_child(_label)
	DisplayServer.window_set_title("第三章试验 · PR35 · 不写正式存档")
	_update_label()
	if house_only:
		enter_house()
	else:
		var first := "C3-04" if OS.get_cmdline_user_args().has("--chapter3-drawings-trial") else "C3-01"
		if first == "C3-04":
			for id in ["ev_drawing_red", "ev_rhyme"]:
				GameState.add_evidence(id)
		print("CHAPTER3_TRIAL chapter ready: start=", first, " persist=", GameState.persist)
		Director.start(first)

func inspect_drawings() -> void:
	var gallery := preload("res://tools/chapter3_drawings.gd").new()
	add_child(gallery)
	await gallery.run(self)
	gallery.queue_free()

func enter_house() -> void:
	if in_house:
		return
	var host: Node = Director.world
	_saved = {"targets": host.active_hotspots.duplicate(), "exploring": host.exploring,
		"objective": GameState.objective, "music": host._music_id, "focus": host._focus,
		"conversation": Director.conversation, "leak": GameState.leak_level,
		"pitch": host.player._pitch}
	Director.conversation = ""
	host.player.conversing = false
	host.exploring = false
	host.stop_music(0.0)
	host.show_scene("ded_house")
	GameState.set_leak(0)
	host.set_mode("walk", "")
	host.set_frozen(false)
	host.player.needs_spawn = false
	Director.ui.set_cinematic(false)
	Director.ui.set_checklist([])
	GameState.objective = "试验：沿小路进入小屋，探索迷宫，寻找北侧出口。"
	in_house = true
	_returning = false
	_update_label()
	print("CHAPTER3_TRIAL house ready: scene=", host.current_id, " doors=", host.doors.size(), " spawn=", host.player.global_position, " persist=", GameState.persist)
	await returned

func leave_house() -> void:
	if not in_house or _returning:
		return
	_returning = true
	in_house = false
	var host: Node = Director.world
	GameState.objective = _saved.get("objective", "")
	GameState.set_leak(int(_saved.get("leak", 1)))
	if standalone:
		for id in ["ev_drawing_red", "ev_rhyme"]:
			GameState.add_evidence(id)
		host.show_scene("child_room")
		host.set_mode("walk", "")
		host.set_frozen(false)
		standalone = false
	else:
		host.show_scene(String(_saved.get("focus", "child_room")))
		host.exploring = _saved.get("exploring", false)
		host.highlight_hotspots(_saved.get("targets", []))
		host.set_mode("walk", "")
		Director.conversation = _saved.get("conversation", "")
		host.player.conversing = Director.conversation != ""
		host.player._pitch = float(_saved.get("pitch", 0.0))
		host.player.cam.rotation.x = host.player._pitch
	host.play_music(String(_saved.get("music", "")), 0.0)
	_update_label()
	returned.emit()
	if not Director.running:
		Director.start("C3-04")

func _process(_dt: float) -> void:
	if not in_house or _returning:
		return
	var p: Vector3 = Director.world.player.global_position
	# Test completion only: reach the authored north porch beyond the exit door.
	if p.z < -20.5 and p.x > 0.05 and p.x < 0.95:
		leave_house()
	if p.y < -3.0:
		_restart_house()

func _input(event: InputEvent) -> void:
	if not in_house or Director.ui._busy():
		return
	if event is InputEventKey and event.pressed and not event.echo:
		if event.physical_keycode == KEY_F7:
			get_viewport().set_input_as_handled()
			leave_house()
		elif event.physical_keycode == KEY_F6:
			get_viewport().set_input_as_handled()
			_restart_house()

func _restart_house() -> void:
	var host: Node = Director.world
	host.player.place(host.spawn[0], host.spawn[1])
	host.set_frozen(false)

func _update_label() -> void:
	if in_house:
		_label.text = "第三章试验｜小屋空间与往返测试（尚无三次碰壁规则）\nWASD 行走 · 鼠标转头 · E/左键开门｜F6 回起点 · F7 返回调查\n穿过北侧出口自动返回；不写正式存档"
	else:
		_label.text = "第三章试验｜按原流程调查艾瑞斯的画\n查看墙上绘画集 → 正面选择五幅画 → 最后选择小屋画，走进画中｜不写正式存档"
