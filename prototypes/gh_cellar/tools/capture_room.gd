extends SceneTree
## 密室空间截图：入口、工作台、西侧水槽。窗口模式运行。
## godot --path . --resolution 1600x900 --script res://tools/capture_room.gd

func _initialize() -> void:
	_run.call_deferred()


func _run() -> void:
	var level: Node3D = (load("res://levels/gh_cellar.tscn") as PackedScene).instantiate()
	root.add_child(level)
	await process_frame
	await physics_frame

	var hud := level.get_node_or_null("CellarUI")
	if hud:
		hud.visible = false
	var player := level.get_node_or_null("Player")
	if player:
		var pcam := player.get_node_or_null("Camera3D")
		if pcam:
			pcam.current = false

	var out_dir := ProjectSettings.globalize_path("res://review/gh_cellar")
	DirAccess.make_dir_recursive_absolute(out_dir)

	# (position, target)
	var shots := [
		["01_entry", Vector3(2.15, 1.62, -3.35), Vector3(-0.2, 1.15, -0.2)],
		["02_table", Vector3(-2.55, 1.62, -2.35), Vector3(0.35, 1.05, -0.55)],
		["03_sink", Vector3(-2.25, 1.62, 0.95), Vector3(-4.55, 1.05, -1.85)],
		["04_north_wall", Vector3(0.0, 1.65, -1.55), Vector3(0.0, 1.75, -4.0)],
	]
	for shot in shots:
		var cam := Camera3D.new()
		cam.fov = 68.0
		cam.near = 0.04
		cam.far = 80.0
		level.add_child(cam)
		cam.look_at_from_position(shot[1], shot[2], Vector3.UP)
		cam.current = true
		for i in 40:
			await process_frame
		var img := get_root().get_texture().get_image()
		var path := out_dir + "/" + String(shot[0]) + ".png"
		img.save_png(path)
		print("CAPTURED ", path)
		cam.queue_free()
		await process_frame
	quit(0)
