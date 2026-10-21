extends SceneTree
## 1926 装片拍两次的 shoot 结局截图。

func _initialize() -> void:
	_run.call_deferred()


func _wait(n: int) -> void:
	for i in n:
		await process_frame


func _look(player: CharacterBody3D, stand: Vector3, target: Vector3) -> void:
	player.place(stand, 0.0)
	await physics_frame
	player.camera.look_at(target, Vector3.UP)
	await physics_frame
	await physics_frame


func _run() -> void:
	var level: Node3D = (load("res://levels/gh_cellar.tscn") as PackedScene).instantiate()
	root.add_child(level)
	await process_frame
	await physics_frame
	var player: CharacterBody3D = level.get_node("Player")
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

	await _look(player, Vector3(0.86, 0, 0.55), Vector3(0.86, 1.08, -0.52))
	player.interact_pressed.emit()
	await _look(player, Vector3(2.02, 0, -2.2), Vector3(2.02, 1.95, -3.92))
	player.camera_toggle_requested.emit()
	level._process(0.016)
	player.shutter_pressed.emit()
	player.shutter_pressed.emit()
	await _wait(10)
	var out_dir := ProjectSettings.globalize_path("res://review/gh_cellar")
	var img := get_root().get_texture().get_image()
	img.save_png(out_dir + "/26_ending_shoot.png")
	print("CAPTURED 26_ending_shoot")
	quit(0)
