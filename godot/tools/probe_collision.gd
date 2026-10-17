extends SceneTree
## 碰撞体检：加载关卡场景，在一片网格上向下打射线，打印每一点的地面高度（---- = 下面什么都没有，会掉下去）。
## 用法：godot --headless --path godot --script res://tools/probe_collision.gd -- --level=greenhouse --x=18,27 --z=-15,-5 --step=0.5

func _initialize() -> void:
	var args := {}
	for a in OS.get_cmdline_user_args():
		var kv := a.trim_prefix("--").split("=")
		args[kv[0]] = kv[1] if kv.size() > 1 else ""
	var scene: Node3D = load("res://levels/%s.tscn" % args.get("level", "greenhouse")).instantiate()
	root.add_child(scene)
	await physics_frame
	await physics_frame
	var xs: PackedStringArray = args.get("x", "18,27").split(",")
	var zs: PackedStringArray = args.get("z", "-15,-5").split(",")
	var st := float(args.get("step", "0.5"))
	var top := float(args.get("top", "12"))
	var space := scene.get_world_3d().direct_space_state
	var z := float(zs[0])
	while z <= float(zs[1]) + 0.001:
		var line := "z=%6.2f " % z
		var x := float(xs[0])
		while x <= float(xs[1]) + 0.001:
			var q := PhysicsRayQueryParameters3D.create(Vector3(x, top, z), Vector3(x, -5, z))
			var hit := space.intersect_ray(q)
			line += (" %5.2f" % hit.position.y) if hit else "  ----"
			x += st
		print(line)
		z += st
	quit()
