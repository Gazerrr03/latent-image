extends SceneTree
## 从真实玩家相机截一张举镜画面，确认取景框与相机模型都接上了。

func _initialize() -> void:
	_run.call_deferred()


func _run() -> void:
	var level: Node3D = (load("res://levels/gh_cellar.tscn") as PackedScene).instantiate()
	root.add_child(level)
	await process_frame
	await physics_frame
	var player: CharacterBody3D = level.get_node("Player")
	player.place(Vector3(-1.82, 0.0, -2.05), 0.0)
	player.camera.look_at(Vector3(-1.82, 1.95, -3.922), Vector3.UP)
	level.state.pickup_camera()
	level.state.raise_camera()
	player.set_camera_mode(true)
	level.ui.set_camera_mode(true)
	level._set_camera_world(true)
	await physics_frame
	level._process(0.016)
	level.state.focus = 1.0
	level._update_camera_materials()
	level._update_target_ui()
	level._update_prompt()
	level.set_process(false)
	for i in 25:
		await process_frame
	var dir := ProjectSettings.globalize_path("res://review/gh_cellar")
	var img := get_root().get_texture().get_image()
	img.save_png(dir + "/17_player_camera.png")
	print("CAPTURED 17_player_camera")
	quit(0)
