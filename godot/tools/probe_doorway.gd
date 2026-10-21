extends SceneTree
## 跨门体检：进出房间时画面会不会整屏跳（10-20 起全庄园共用一套画面设置，应该不跳）。
## godot --path godot --resolution 1280x720 --script res://tools/probe_doorway.gd -- --capture=C0-11 --wait=1000 [--day] [--out=/tmp/dir]
## 对每一道隔开两个房间的门（能开的门自动找，另加 EXTRA 里打不开的门洞）：站在门这边、隔着门看过去，
## 先按门这边的房间套画面设置截一帧，再按门那边的房间套一次截一帧，比两帧的平均亮度。
## 只量“换房间时画面设置变了多少”，不受走路时视野变化影响；测时关掉胶片滤镜（颗粒、闪烁每帧随机）。
## 两帧差在 ±3% 以内算不跳；退出码 1 = 有门超过。--out=目录：存每道门的两帧。
const EXTRA := [
	# 名字, 门这边（脚下）, 门那边（脚下）
	["暗房的门（撞开）", Vector3(17.25, 3.62, -6.7), Vector3(17.25, 3.62, -8.6)],
]
const LIMIT := 0.03

func _initialize():
	call_deferred("run")

func run():
	var main = load("res://main.tscn").instantiate()
	root.add_child(main)
	await create_timer(6.0).timeout
	var host = root.get_node("Director").world
	var player = host.player
	Input.mouse_mode = Input.MOUSE_MODE_VISIBLE
	var args := OS.get_cmdline_user_args()
	var out := ""
	for a in args:
		if a.begins_with("--out="):
			out = a.trim_prefix("--out=")
	if args.has("--day"):
		root.get_node("GameState").shot = "C2-03"
		host._on_state_changed()
	var pairs: Array = EXTRA.duplicate()
	for door in host.doors:
		var leaf: MeshInstance3D = host.doors[door]["leaf"]
		var box: AABB = leaf.global_transform * leaf.get_aabb()
		var c := box.get_center()
		var n: Vector3 = leaf.global_basis.z.normalized()
		var foot := Vector3(c.x, box.position.y + 0.02, c.z)
		var a := foot + n * 0.9
		var b := foot - n * 0.9
		if host.room_at(a) != host.room_at(b):
			pairs.append([String(leaf.name), a, b])
		if not host.door_is_open(door):
			host.toggle_door(door, a)
	root.get_node("Director").ui.fx.visible = false
	await create_timer(1.5).timeout
	var bad := 0
	for w in pairs:
		var from: Vector3 = w[1]
		var to: Vector3 = w[2]
		var dir := (to - from).normalized()
		player.place(from, rad_to_deg(atan2(-dir.x, -dir.z)))
		player._pitch = deg_to_rad(-8)
		player.cam.rotation.x = player._pitch
		await create_timer(0.8).timeout
		var rooms := [host.room_at(from), host.room_at(to)]
		var lum: Array[float] = []
		for r in rooms:
			host._apply_look(r)
			for i in 4:
				await process_frame
			var img: Image = root.get_viewport().get_texture().get_image()
			if out != "":
				img.save_png("%s/%s_%s.png" % [out, w[0], r])
			lum.append(_lum(img))
		var d := (lum[1] - lum[0]) / maxf(lum[0], 0.01)
		if absf(d) > LIMIT:
			bad += 1
		print("DOORSWAP %s %s %s→%s 亮度 %.3f → %.3f（%+.1f%%）" % ["✗" if absf(d) > LIMIT else "✓", w[0], rooms[0], rooms[1], lum[0], lum[1], d * 100.0])
	print("DOORSWAP 共 %d 道门，%d 道跳" % [pairs.size(), bad])
	quit(1 if bad > 0 else 0)


static func _lum(img: Image) -> float:
	img.resize(64, 36, Image.INTERPOLATE_BILINEAR)
	var s := 0.0
	for y in 36:
		for x in 64:
			s += img.get_pixel(x, y).get_luminance()
	return s / (64 * 36)
