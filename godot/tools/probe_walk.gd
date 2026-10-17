extends SceneTree
## 行走体检：用玩家本身（world/player.gd 的胶囊、脚下射线与 walk()）从起点向各个方向走，打印终点与最低点。
## 用法：godot --headless --path godot --script res://tools/probe_walk.gd -- --level=hall [--from=x,y,z] [--dirs=16] [--yaw=度] [--secs=6]
## 不给 --from 时从关卡的 spawn 出发；“← 掉落”= 比起点低了 0.5 m 以上（下楼梯也会这样标，看终点高度判断）
func _initialize() -> void:
	var args := {}
	for a in OS.get_cmdline_user_args():
		var kv := a.trim_prefix("--").split("=")
		args[kv[0]] = kv[1] if kv.size() > 1 else ""
	var scene: Node3D = load("res://levels/%s.tscn" % args.get("level", "greenhouse")).instantiate()
	root.add_child(scene)
	await process_frame
	var start := Vector3.ZERO
	if args.has("from"):
		var f: PackedStringArray = args["from"].split(",")
		start = Vector3(float(f[0]), float(f[1]), float(f[2]))
	else:
		start = scene.find_child("spawn", true, false).global_position
	var n := int(args.get("dirs", "16"))
	var secs := float(args.get("secs", "6"))
	var only := float(args.get("yaw", "-1"))
	var Walker = load("res://world/player.gd")
	for i in n:
		var yaw := TAU * i / n if only < 0 else deg_to_rad(only)
		var b: CharacterBody3D = Walker.new()
		scene.add_child(b)
		b.global_position = start
		await physics_frame
		var dir := Vector3(sin(yaw), 0, cos(yaw))
		var miny := start.y
		var maxy := start.y
		var t := 0.0
		while t < secs:
			b.walk(dir, 1.0 / 60.0)
			await physics_frame
			miny = minf(miny, b.global_position.y)
			maxy = maxf(maxy, b.global_position.y)
			t += 1.0 / 60.0
		print("dir %5.0f°  end %s  miny %.2f maxy %.2f%s" % [rad_to_deg(yaw), b.global_position.snapped(Vector3.ONE * 0.01), miny, maxy, "  ← 掉落" if miny < start.y - 0.5 else ""])
		b.queue_free()
		if only >= 0:
			break
	quit()
