extends SceneTree
## 1926 实体底片：从片夹装片，举镜拍两次，走到 shoot 结局。

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


func _run() -> void:
	level = (load("res://levels/gh_cellar.tscn") as PackedScene).instantiate()
	root.add_child(level)
	await process_frame
	await physics_frame
	player = level.get_node("Player")

	# shortcut to the physical final state
	var s = level.state
	s.has_camera = true
	player.set_has_camera(true)
	s.cleared["1920"] = true
	s.has_key = true
	s.key_seen = true
	s.box_open = true
	s.owner_seen = true
	s.plate_1926_taken = true
	s.plate_state = "NONE"
	level._on_state_changed()

	await _aim(Vector3(0.86, 0, 0.55), Vector3(0.86, 1.08, -0.52))
	_check(player.get_target_area() != null, "holder is targetable")
	player.interact_pressed.emit()
	_check(level.state.final_loaded, "1926 plate loads at holder")
	_check(level.state.plate_state == "FINAL", "plate state FINAL")

	await _aim(Vector3(2.02, 0, -2.2), Vector3(2.02, 1.95, -3.92))
	player.camera_toggle_requested.emit()
	level._process(0.016)
	_check(level.state.camera_raised, "camera raised for 1926")
	_check(level.state.owner_seen, "owner remains seen")
	player.shutter_pressed.emit()
	_check(level.state.final_shots == 1, "final first shutter")
	player.shutter_pressed.emit()
	_check(level.state.final_shots == 2, "final second shutter")
	_check(level.state.final_choice == "shoot", "shoot ending state")
	_check(level.ui.is_overlay_open(), "shoot ending overlay shown")

	print("TEST_SCENE_SHOOT ", "PASS" if ok else "FAIL")
	for t in get_processed_tweens():
		t.kill()
	for p in level.find_children("*", "AudioStreamPlayer", true, false):
		p.stop()
		p.stream = null
	level.free()
	await process_frame
	quit(0 if ok else 1)
