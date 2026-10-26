extends RefCounted
## 展示视频机位：用游戏自己的灯光与滤镜，隐藏界面，沿表里的路径运镜。
## 用法（逐帧录制，PNG 序列）：
##   godot --path godot --write-movie /tmp/showcase/S06/f.png --fixed-fps 30 --resolution 1920x1080 -- --showcase=S06
## 表：tools/showcase/shots.csv，坐标沿用设计坐标 (X, N, 标高)，同 tools/capture_level.gd。只动相机，不改任何关卡场景。
## shot_id 也可写 room:<关卡 id>，直接加载独立关卡再按表里的自有机位运镜。

const TABLE := "res://tools/showcase/shots.csv"


## "x N h"（设计坐标）或 "cam:机位名 [dx dN dh]"（取关卡场景里 cam_<机位名> 的位置，再加偏移；look 列写 "cam:机位名" 取它的朝向点）
static func _v(s: String, look := false) -> Vector3:
	var p := s.strip_edges().split(" ", false)
	if p[0].begins_with("cam:"):
		var m: Array = Director.world.markers[p[0].trim_prefix("cam:")]
		var base: Vector3 = m[1] if look else m[0]
		if p.size() >= 4:
			base += Vector3(float(p[1]), float(p[3]), -float(p[2]))
		return base
	return Vector3(float(p[0]), float(p[2]), -float(p[1]))     # 设计坐标 → Godot


static func _row(id: String) -> Dictionary:
	var f := FileAccess.open(TABLE, FileAccess.READ)
	var head := f.get_csv_line()
	while not f.eof_reached():
		var c := f.get_csv_line()
		if c.size() < head.size() or c[0] != id:
			continue
		var d := {}
		for i in head.size():
			d[head[i]] = c[i]
		return d
	return {}


static func _f(r: Dictionary, k: String, d: String) -> String:
	return r[k] if r.has(k) and r[k] != "" else d


## 三种拍法：
##   1. 自己的相机：pos_a 有内容时，相机沿 pos_a→pos_b / look_a→look_b 运镜（设计坐标或 cam:机位）
##   2. 镜头自带机位：pos_a 留空，等 seconds 秒，用这一镜原本的运镜与动作（显影、镜子、白色的房间）。ui 列：show 保留界面，skip 文字不等点击
##   3. 回廊：shot_id 写 corridor:N（第 N 圈），玩家沿中线往前走 seconds 秒
## drive 列：玩法自动驾驶剧本（见 driver.gd）；grant 列：先发放的证据
## press 列：空格分隔的秒数，到点替玩家点一下当前选项
## clip 列写影像片段名（如 片头_怪谈）：播放这个片段，seconds 为拍摄时长
static func run(main: Node, id: String) -> void:
	var tree := main.get_tree()
	var r := _row(id)
	if r.is_empty():
		push_error("展示机位表里没有：" + id)
		tree.quit(1)
		return
	GameState.reset()
	GameState.persist = false
	GameState.set_leak(int(r["leak"]))
	if r["fx"] != "":
		Director.ui.fx.set_override(r["fx"])
	if "skip" in _f(r, "ui", ""):
		Director.skip_text = true             # 文字不等点击（显影这类要往下走的镜头）
	var sid: String = r["shot_id"]
	var corridor_layer := 0
	if sid.begins_with("corridor:"):
		corridor_layer = int(sid.get_slice(":", 1))
		Director.world.start_corridor()
		await tree.create_timer(0.6).timeout
		var c0: Node = Director.world.corridor
		c0.running = true
		c0._enter(clampf(corridor_layer - 1, 0, 5))
	elif sid.begins_with("room:"):
		var room_id := sid.trim_prefix("room:")
		if not ResourceLoader.exists(ContentDB.level_path(room_id)):
			push_error("展示镜头找不到关卡：" + room_id)
			tree.quit(1)
			return
		Director.world.show_scene(room_id)
		Director.world.set_mode("walk", "")
	else:
		Director.start(sid)
	var lead := int(_f(r, "lead", "90"))
	for i in lead:
		await tree.process_frame               # 等场景、灯光、阴影收敛
	if r["switch"] != "":
		for b in tree.get_nodes_in_group("light_switch"):
			if String(b.get_meta("switch_name", "")) == r["switch"]:
				Director.world.toggle_switch(b)
		for i in 30:
			await tree.process_frame
	if _f(r, "clip", "") != "":
		Director.ui.footage.play_clip(r["clip"])
	var show_ui: bool = "show" in _f(r, "ui", "") or _f(r, "clip", "") != ""
	if not show_ui:
		Director.ui.visible = false
		Director.ui.footage.visible = false
	var total := int(float(r["seconds"]) * 30.0)
	print("SHOWCASE_FRAMES ", total + 1)          # 录像开头还有加载与等待的帧，剪辑时按总帧数减去这个数裁掉
	print("SHOWCASE_MARKERS ", Director.world.markers.keys())
	if corridor_layer > 0:
		var c: Node = Director.world.corridor
		var t := 0.0
		for i in total + 1:
			t += 1.0 / 30.0
			var k := minf(float(c._seg_b + 8.0), t * 1.4)
			Director.world.player.place(c.global_position + c._at(k), 0.0 if k < 8.0 else 90.0)
			await tree.process_frame
		tree.quit(0)
		return
	if _f(r, "grant", "") != "":
		for ev in _f(r, "grant", "").split(" ", false):
			GameState.add_evidence(ev)           # 提前给齐这一镜用得到的证据
	var drive := _f(r, "drive", "")
	if drive != "":
		preload("res://tools/showcase/driver.gd").run(tree, drive)   # 不 await：与录制同时跑
	var presses: Array = []
	for t in _f(r, "press", "").split(" ", false):
		presses.append(int(float(t) * 30.0))
	if r["pos_a"] == "":
		for i in total + 1:
			if presses.has(i):
				Director.ui._resolved.emit(0)    # 替玩家点一下选项（把底片放进显影液、放进定影液）
			await tree.process_frame
		tree.quit(0)
		return
	var cam := Camera3D.new()
	cam.near = 0.05
	cam.far = 600.0
	Director.world.add_child(cam)
	var a_pos := _v(r["pos_a"])
	var b_pos := _v(r["pos_b"])
	var a_look := _v(r["look_a"], true)
	var b_look := _v(r["look_b"], true)
	var ease_on := int(r["ease"]) == 1
	var fov_a := float(r["fov_a"])
	var fov_b := float(r["fov_b"])
	var rig: Node = preload("res://tools/showcase/rig.gd").new()
	rig.cam = cam
	if not show_ui:
		rig.hide_nodes = [Director.ui, Director.ui.footage]
	rig.pose = func(f: int) -> void:
		var u := float(f) / float(total)
		if ease_on:
			u = u * u * (3.0 - 2.0 * u)
		cam.global_transform = Transform3D(Basis(), a_pos.lerp(b_pos, u)).looking_at(a_look.lerp(b_look, u), Vector3.UP)
		cam.fov = lerpf(fov_a, fov_b, u)
	main.add_child(rig)
	for i in total + 1:
		if presses.has(i):
			Director.ui._resolved.emit(0)
		rig.frame = i
		await tree.process_frame
	tree.quit(0)
