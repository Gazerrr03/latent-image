extends SceneTree
## 有图形窗口的探索性能抽样；不要使用 --headless 或 --fixed-fps。
## godot --path godot --script res://tools/probe_fps.gd -- --capture=C0-11 --wait=1000
## 每处预热 2 秒、转一圈采样 8 秒；保留默认垂直同步，比较原滤镜与关闭滤镜。
## 不代表加载耗时、连续走动或完整剧情的性能。截图入口会关闭存档写入。
## --off=dust,fog,sky,shadows,sun,ssil：关掉某一项看开销。
## --shots=/tmp/dir：每个房间采样前截一张图。
## 可加 --no-vsync（关掉垂直同步，看真实余量）、--day（换成第 2 章阴天的天光；默认是序章夜里）、--shot=C3-01（按那一镜的天气）。
func _initialize():
	call_deferred("run")
func run():
	if DisplayServer.get_name() == "headless" or not OS.get_cmdline_user_args().has("--capture=C0-11") or not OS.get_cmdline_user_args().has("--wait=1000"):
		printerr("Use a graphical window with -- --capture=C0-11 --wait=1000")
		quit(1)
		return
	var main = load("res://main.tscn").instantiate()
	root.add_child(main)
	await create_timer(6.0).timeout
	var director = root.get_node("Director")
	var host = director.world
	var player = host.player
	if not player.active or not player.cam.current:
		printerr("FPS probe requires the active exploration camera")
		quit(1)
		return
	Input.mouse_mode = Input.MOUSE_MODE_VISIBLE
	var args := OS.get_cmdline_user_args()
	if args.has("--no-vsync"):
		DisplayServer.window_set_vsync_mode(DisplayServer.VSYNC_DISABLED)
	var vp := root.get_viewport().get_viewport_rid()
	RenderingServer.viewport_set_measure_render_time(vp, true)
	# --off=dust,fog,sky：关掉某一项，看它花了多少（排查用）
	var offs := ""
	for a in args:
		if a.begins_with("--off="):
			offs = a.trim_prefix("--off=")
	for off in offs.split(",", false):
		if off == "dust":
			var amb: Node = host.find_child("氛围粒子", true, false)
			amb.process_mode = Node.PROCESS_MODE_DISABLED
			amb.visible = false
		elif off == "shadows" or off == "sun":
			for l in root.find_children("*", "Light3D", true, false):
				if off == "shadows" or l is DirectionalLight3D:
					l.shadow_enabled = false
		elif off == "ssil":
			root.get_viewport().get_camera_3d().get_world_3d().environment.ssil_enabled = false
		elif off == "fog":
			root.get_viewport().get_camera_3d().get_world_3d().environment.fog_enabled = false
		elif off == "sky":
			RenderingServer.environment_set_sky(root.get_viewport().get_camera_3d().get_world_3d().environment.get_rid(), RID())
	var at_shot := "C2-03" if args.has("--day") else ""
	for a in args:
		if a.begins_with("--shot="):
			at_shot = a.trim_prefix("--shot=")   # 例如 --shot=C3-01：第 3 章晴天
	if at_shot != "":
		root.get_node("GameState").shot = at_shot
		host._on_state_changed()
	print("PERF_META ", JSON.stringify({"viewport":str(root.get_visible_rect().size),"window":str(DisplayServer.window_get_size()),"gpu":RenderingServer.get_video_adapter_name(),"vsync":DisplayServer.window_get_vsync_mode()}))
	var shots := ""
	for a in args:
		if a.begins_with("--shots="):
			shots = a.trim_prefix("--shots=")
	for room_id in ["guest_room", "hall", "dining", "seance", "garden", "darkroom"]:
		if not host._room_spawn.has(room_id):
			continue
		host.focus_room(room_id)
		player.place(host._room_spawn[room_id][0], 0)
		for mode in ["baseline", "no_filter"]:
			director.ui.fx.visible = mode == "baseline"
			player.rotation.y = 0
			await create_timer(2.0).timeout
			if shots != "" and mode == "baseline":
				# --shots=/tmp/dir：采样前在出生点截一张，看改动有没有坏画面
				root.get_viewport().get_texture().get_image().save_png("%s/%s.png" % [shots, room_id])
			var gpu: Array[float] = []
			var samples: Array[float] = []
			var start = Time.get_ticks_usec()
			var last = start
			while Time.get_ticks_usec() - start < 8000000:
				await process_frame
				var now = Time.get_ticks_usec()
				samples.append((now-last)/1000.0)
				gpu.append(RenderingServer.viewport_get_measured_render_time_gpu(vp))
				last = now
				player.rotation.y = float(now-start)/8000000.0 * TAU
			var elapsed = (last-start)/1000000.0
			samples.sort()
			print("PERF_RESULT ", JSON.stringify({"room":room_id,"mode":mode,"fps":samples.size()/elapsed,"gpu_ms":gpu.reduce(func(a, b): return a + b, 0.0) / maxf(gpu.size(), 1),"p95_ms":samples[int(samples.size()*0.95)],"p99_ms":samples[int(samples.size()*0.99)],"draw_calls":Performance.get_monitor(Performance.RENDER_TOTAL_DRAW_CALLS_IN_FRAME),"primitives":Performance.get_monitor(Performance.RENDER_TOTAL_PRIMITIVES_IN_FRAME)}))
	quit()
