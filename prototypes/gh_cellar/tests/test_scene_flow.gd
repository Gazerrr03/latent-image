extends SceneTree
## 场景层测试：真实射线 + 记录本翻页 + 第4/7页门槛 + 实体 1926 底片。

var ok := true
var level: Node3D
var player: CharacterBody3D


func _initialize() -> void:
	_run.call_deferred()


func _check(cond: bool, label: String) -> void:
	print(("PASS  " if cond else "FAIL  ") + label)
	if not cond:
		ok = false


func _aim(stand: Vector3, target: Vector3) -> void:
	player.place(stand, 0.0)
	await physics_frame
	player.camera.look_at(target, Vector3.UP)
	await physics_frame
	await physics_frame


func _target_id() -> String:
	var a: Area3D = player.get_target_area()
	return String(a.get_meta("id", "")) if a else ""


func _goto_page(target_id: String) -> bool:
	for i in 20:
		if level.ui.notebook_current_page_id() == target_id:
			return true
		level.ui.notebook_next()
	return false


func _close_notebook() -> void:
	var tab := InputEventKey.new()
	tab.keycode = KEY_TAB
	tab.pressed = true
	level._input(tab)


func _run() -> void:
	level = (load("res://levels/gh_cellar.tscn") as PackedScene).instantiate()
	root.add_child(level)
	await process_frame
	await physics_frame
	player = level.get_node("Player")
	_check(level.frame_views.size() == 8, "8 frame shader views")
	_check(level.interactables.size() == 17, "17 interactables")
	_check(level.ui != null, "CellarUI exists")

	await _aim(Vector3(0.36, 0, 0.55), Vector3(0.36, 1.15, -0.64))
	_check(_target_id() == "pickup", "ray hits pickup (%s)" % _target_id())
	player.interact_pressed.emit()
	_check(level.state.has_camera, "E picks up camera")
	_check(player.camera.fov == 70.0, "camera lowered by default")
	_check(not level.tag_prop.visible, "paper tag hidden after pickup")

	player.notebook_requested.emit()
	_check(not level.ui.notebook_is_open(), "Tab refuses before first physical read")

	await _aim(Vector3(0.82, 0, 0.55), Vector3(0.82, 0.92, -0.32))
	_check(_target_id() == "notebook", "ray hits notebook (%s)" % _target_id())
	player.interact_pressed.emit()
	_check(level.ui.notebook_is_open(), "E opens physical notebook")
	_check(level.ui.notebook_current_page_id() == "intro", "opens on first page")
	_close_notebook()
	_check(not level.ui.notebook_is_open(), "Tab closes notebook")

	await _aim(Vector3(-1.82, 0, -2.2), Vector3(-1.82, 1.95, -3.92))
	_check(_target_id() == "frame_1920", "ray hits 1920 frame (%s)" % _target_id())
	player.camera_toggle_requested.emit()
	_check(level.state.camera_raised, "F raises camera")
	_check(player.camera.fov == 48.0, "camera FOV 48")
	_check(player.viewmodel.visible, "camera viewmodel visible")
	_check(level.ui._camera_overlay.visible, "viewfinder visible")
	level._process(0.016)
	level.state.focus = 1.0
	level._update_camera_materials()
	player.shutter_pressed.emit()
	_check(level.state.plate_state == "EXPOSED", "left click exposes plate")

	player.camera_toggle_requested.emit()
	_check(not level.state.camera_raised, "F lowers camera")
	await _aim(Vector3(-3.35, 0, -0.9), Vector3(-4.5, 1.0, -0.9))
	_check(_target_id() == "tray", "ray hits developing tray (%s)" % _target_id())
	player.interact_pressed.emit()
	_check(level.state.plate_state == "DEVELOPED", "tray develops first plate")

	await _aim(Vector3(0.86, 0, 0.55), Vector3(0.86, 1.08, -0.52))
	_check(_target_id() == "holder", "ray hits film holder (%s)" % _target_id())
	player.interact_pressed.emit()
	_check(level.state.plate_state == "DEVELOPED", "holder stays stuck before page 4")
	_check(not level.state.page4_read, "page 4 still unread")

	await _aim(Vector3(0.82, 0, 0.55), Vector3(0.82, 0.92, -0.32))
	player.interact_pressed.emit()
	_check(level.ui.notebook_is_open(), "notebook opens for page 4")
	_check(_goto_page("second"), "reaches page 4")
	_check(level.state.page4_read, "reading page 4 sets flag")
	_close_notebook()

	await _aim(Vector3(0.86, 0, 0.55), Vector3(0.86, 1.08, -0.52))
	player.interact_pressed.emit()
	_check(level.state.plate_state == "LOADED2", "holder reloads after page 4")
	player.second_exposure_requested.emit()
	_check(level.state.plate_state == "ARMED", "R arms second exposure")

	await _aim(Vector3(-1.82, 0, -2.2), Vector3(-1.82, 1.95, -3.92))
	player.camera_toggle_requested.emit()
	level._process(0.016)
	level.state.focus = 1.0
	level._update_camera_materials()
	player.shutter_pressed.emit()
	_check(level.state.plate_state == "EXPOSED2", "second shutter exposes again")
	player.camera_toggle_requested.emit()
	await _aim(Vector3(-3.35, 0, -0.9), Vector3(-4.5, 1.0, -0.9))
	player.interact_pressed.emit()
	_check(level.state.plate_state == "NONE", "second development clears plate")
	_check(level.state.cleared.has("1920"), "1920 frame cleared")

	# key ghost -> page 7 -> key -> box
	await _aim(Vector3(-3.4, 0, 2.95), Vector3(-4.55, 0.85, 2.95))
	_check(_target_id() == "cabinet", "ray hits film cabinet (%s)" % _target_id())
	player.camera_toggle_requested.emit()
	level._process(0.016)
	player.interact_pressed.emit()
	_check(level.state.key_seen, "camera sees key ghost")
	_check(not level.state.has_key, "ghost does not give key")
	player.camera_toggle_requested.emit()

	await _aim(Vector3(0.82, 0, 0.55), Vector3(0.82, 0.92, -0.32))
	player.interact_pressed.emit()
	_check(_goto_page("key"), "reaches page 7")
	_check(level.state.has_key, "reading page 7 gives key")
	_close_notebook()

	await _aim(Vector3(-3.4, 0, 2.95), Vector3(-4.55, 0.85, 2.95))
	player.interact_pressed.emit()
	_check(level.state.box_open, "key opens film box")

	await _aim(Vector3(2.02, 0, -2.2), Vector3(2.02, 1.95, -3.92))
	_check(_target_id() == "frame_1926", "ray hits 1926 frame (%s)" % _target_id())
	player.camera_toggle_requested.emit()
	level._process(0.016)
	_check(level.state.owner_seen, "owner reflection triggers at 1926")
	player.camera_toggle_requested.emit()

	await _aim(Vector3(-3.2, 0, 2.85), Vector3(-4.15, 1.02, 2.85))
	_check(_target_id() == "plate_1926", "ray hits 1926 plate (%s)" % _target_id())
	player.interact_pressed.emit()
	_check(level.state.plate_1926_taken, "1926 plate taken")
	_check(level.plate_1926_prop != null and not level.plate_1926_prop.visible, "plate prop hidden")

	# physical "put it back" ending
	await _aim(Vector3(-3.4, 0, 2.95), Vector3(-4.55, 0.85, 2.95))
	player.interact_pressed.emit()
	_check(level.state.final_choice == "keep", "returning plate reaches keep ending")
	_check(level.ui.is_overlay_open(), "keep ending overlay shown")

	print("TEST_SCENE ", "PASS" if ok else "FAIL")
	for t in get_processed_tweens():
		t.kill()
	for p in level.find_children("*", "AudioStreamPlayer", true, false):
		p.stop()
		p.stream = null
	level.free()
	await process_frame
	quit(0 if ok else 1)
