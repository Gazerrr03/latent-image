extends SceneTree
func _initialize() -> void:
	var args := {}
	for a in OS.get_cmdline_user_args():
		var kv := a.trim_prefix("--").split("=")
		args[kv[0]] = kv[1] if kv.size() > 1 else ""
	var scene: Node3D = load("res://levels/%s.tscn" % args.get("level", "ded_house")).instantiate()
	root.add_child(scene)
	var we := WorldEnvironment.new()
	var e := Environment.new()
	e.background_mode = Environment.BG_COLOR
	e.background_color = Color("#07070a")
	e.ambient_light_source = Environment.AMBIENT_SOURCE_COLOR
	e.ambient_light_color = Color("#40404c")
	e.ambient_light_energy = float(args.get("amb", "0.35"))
	e.tonemap_mode = Environment.TONE_MAPPER_ACES
	e.fog_enabled = args.get("fog", "1") == "1"
	e.fog_light_color = Color("#0b0b10")
	e.fog_density = 0.02
	we.environment = e
	root.add_child(we)
	if args.get("nolight", "0") == "1":
		for l in scene.find_children("*", "Light3D", true, false):
			l.visible = false
	var cam := Camera3D.new()
	cam.fov = 70
	cam.near = 0.05
	root.add_child(cam)
	var f: PackedStringArray = args.get("at", "0,1.6,0,0,0").split(",")
	cam.global_position = Vector3(float(f[0]), float(f[1]), float(f[2]))
	cam.rotation.y = deg_to_rad(float(f[3]) if f.size() > 3 else 0.0)
	cam.rotation.x = deg_to_rad(float(f[4]) if f.size() > 4 else 0.0)
	cam.current = true
	await process_frame
	await process_frame
	await RenderingServer.frame_post_draw
	var img := root.get_viewport().get_texture().get_image()
	img.save_png(args.get("out", "user://shot.png"))
	print("截图已保存：", args.get("out", "user://shot.png"))
	quit()
