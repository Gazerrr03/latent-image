extends SceneTree

## 雨声音量回归：真实庄园窗玻璃、房间判定、天气、淡入淡出及 BGM。
## godot --headless --path godot --script res://tools/probe_rain.gd

var bad := 0

func check(ok: bool, label: String) -> void:
	print("PASS " if ok else "FAIL ", label)
	if not ok:
		bad += 1


func _check_recordings() -> void:
	# 验证实际加载的素材已替换为长录音，不能误用旧的约 12 秒合成音。
	for sid in ["rain_glass", "rain_night"]:
		var stream: AudioStream = load("res://audio/sfx/%s.ogg" % sid)
		check(stream != null and stream.get_length() > 20.0, "recorded rain asset loaded: " + sid)

func _initialize() -> void:
	call_deferred("run")

func run() -> void:
	# 启动依赖丢失或解析失败时直接失败，不能让无人值守检查一直挂着。
	if not FileAccess.file_exists("res://world/rain.gd"):
		printerr("FAIL missing res://world/rain.gd")
		quit(1)
		return
	var host_script: GDScript = load("res://world/scene_host.gd")
	if host_script == null or not host_script.can_instantiate():
		printerr("FAIL scene_host cannot load")
		quit(1)
		return
	var state = root.get_node("GameState")
	state.persist = false
	_check_recordings()
	var host = host_script.new()
	root.add_child(host)
	var player = load("res://world/player.gd").new()
	root.add_child(player)
	host.player = player
	if not host.has_method("room_at"):
		await _check_room_loading(host, player, state)
		return
	host.show_scene("guest_room")
	host.apply_room_states("C1-02")
	var rain = host.get_node("雨声")
	rain.set_process(false)
	state.shot = "C1-02"
	check(rain.raining(), "C1 wet weather")
	rain._refresh_glass()
	print("PANES ", rain._glass.size())
	check(rain._glass.size() > 0, "real manor window geometry found")
	for rid in host._room_spawn:
		var feet: Vector3 = host._room_spawn[rid][0]
		player.place(feet, 0)
		player.active = true
		var ear := feet + Vector3(0, 1.6, 0)
		var outside: bool = rain._outdoors(ear)
		print("ROOM ", rid, " outside=", outside, " gain=", rain._closeness(ear))
		check(outside == (rid in ["manor", "garden"]), "outdoor classification " + rid)
	player.active = false
	var pane: AABB = rain._glass[0]
	check(rain._closeness(pane.get_center()) > 0.99, "near glass audible")
	check(is_zero_approx(rain._closeness(Vector3(1000, 1000, 1000))), "far from glass silent")
	var cam := Camera3D.new()
	host.add_child(cam)
	cam.make_current()
	cam.global_position = pane.get_center()
	# 在实际玻璃内侧、屋外和远处移动听音点，验证整条更新链。
	var near_point := Vector3.ZERO
	var found := false
	for b: AABB in rain._glass:
		for offset in [Vector3(0.4, 0, 0), Vector3(-0.4, 0, 0), Vector3(0, 0, 0.4), Vector3(0, 0, -0.4)]:
			var ear: Vector3 = b.get_center() + offset
			if not rain._outdoors(ear) and rain._closeness(ear) > 0.99:
				near_point = ear
				found = true
				break
		if found:
			break
	check(found, "indoor listening point near real window found")
	cam.global_position = near_point
	rain._process(1.0 / 60.0)
	check(rain._amp["rain_glass"] > 0 and rain._amp["rain_glass"] < 0.1, "approaching window fades in")
	for i in 60:
		rain._process(1.0 / 60.0)
	check(is_equal_approx(rain._amp["rain_glass"], db_to_linear(-8.0)), "near window glass layer reduced by 8 dB")
	check(is_equal_approx(rain._amp["rain_night"], db_to_linear(-6.0)), "near window includes outdoor rain bed")
	check(rain._players.has("rain_glass") and rain._players.has("rain_night"), "both recordings play together near window")
	# 在室内移动时，两层声音应共享相同的距离变化，不能分别提前淡出。
	cam.global_position = host._room_spawn["dining"][0] + Vector3(0, 1.6, 0)
	rain._process(0.1)
	check(is_equal_approx(rain._amp["rain_glass"] / rain._amp["rain_night"], db_to_linear(-2.0)), "indoor fade preserves layer balance")
	cam.global_position = Vector3(1000, 1.6, 1000)
	for i in 60:
		rain._process(1.0 / 60.0)
	check(is_zero_approx(rain._amp["rain_glass"]), "leaving window fades glass rain out")
	check(is_equal_approx(rain._amp["rain_night"], 1.0), "outdoor rain remains audible")
	cam.global_position = host._room_spawn["dining"][0] + Vector3(0, 1.6, 0)
	for i in 60:
		rain._process(1.0 / 60.0)
	check(rain._players.is_empty(), "indoor far from windows stops both layers")
	# 验证播放器第一次开播就有衰减，以及归零时释放。
	rain._apply("rain_glass", 0.1)
	check(rain._players.has("rain_glass"), "rain audio starts")
	check(is_equal_approx(rain._players["rain_glass"].volume_db, -26.0), "first playback already attenuated")
	rain._apply("rain_glass", 0.0)
	check(not rain._players.has("rain_glass"), "zero gain releases audio")
	host.play_sound("rain_glass")
	check(not host._loops.has("rain_glass"), "shot sound cannot start duplicate rain loop")
	host.play_music("explore", 0)
	var music = host._music
	state.shot = "C2-01"
	check(not rain.raining(), "C2 dry weather")
	for i in 120:
		rain._process(1.0 / 60.0)
	check(rain._players.is_empty(), "dry weather stops both rain layers")
	check(is_instance_valid(music) and host._music == music and music.playing, "BGM continues through rain changes")
	# 也走引擎的真实帧更新，避免只手动调用 _process 掩盖未启用脚本的问题。
	state.shot = "C1-02"
	cam.global_position = near_point
	rain.set_process(true)
	await create_timer(0.8).timeout
	check(rain._players.has("rain_glass") and rain._players["rain_glass"].playing, "engine frames start rain near window")
	if rain._players.has("rain_glass"):
		check(rain._players["rain_glass"].bus == "SFX", "rain follows SFX volume setting")
	cam.global_position = host._room_spawn["dining"][0] + Vector3(0, 1.6, 0)
	await create_timer(0.8).timeout
	check(rain._players.is_empty(), "engine frames stop rain far from window")
	check(is_instance_valid(music) and music.playing, "BGM still plays after moving away")
	rain.set_process(false)
	host.show_scene("ded_corridor")
	state.shot = "C6-01"
	rain._refresh_glass()
	check(rain._glass.is_empty(), "window cache cleared in windowless scene")
	print("RAIN PROBE failures=", bad)
	# show_scene 会缓存并移出庄园；探针结束时一并释放。
	if host._map_stash.has("room"):
		host._map_stash["room"].queue_free()
		host._map_stash.clear()
	host.queue_free()
	player.queue_free()
	await process_frame
	# 在 run 返回后退出。
	call_deferred("quit", 1 if bad else 0)


## 远端的逐房间加载版本也必须可以独立运行这份修复。
func _check_room_loading(host: Node3D, player: Node3D, state: Node) -> void:
	var rain = host.get_node("雨声")
	rain.set_process(false)
	state.shot = "C1-01"
	check(rain.raining(), "C1 wet weather")
	host.show_scene("guest_room")
	rain._refresh_glass()
	check(not rain._glass.is_empty(), "room window geometry found")
	check(not rain._outdoors(Vector3.ZERO), "guest room is indoors")
	if rain._glass.is_empty():
		host.queue_free()
		player.queue_free()
		call_deferred("quit", 1)
		return
	var cam := Camera3D.new()
	host.add_child(cam)
	cam.make_current()
	cam.global_position = rain._glass[0].get_center()
	host.play_music("explore", 0)
	var music = host._music
	rain.set_process(true)
	await create_timer(0.8).timeout
	check(rain._players.has("rain_glass") and rain._players["rain_glass"].playing, "engine frames start rain near window")
	check(rain._players.has("rain_night") and rain._players["rain_night"].playing, "engine frames also play outdoor layer near window")
	check(is_equal_approx(rain._players["rain_glass"].volume_db, -14.0), "glass layer matches approved mix volume")
	check(is_equal_approx(rain._players["rain_night"].volume_db, -12.0), "outdoor layer matches approved mix volume")
	cam.global_position = Vector3(1000, 1.6, 1000)
	await create_timer(0.8).timeout
	check(rain._players.is_empty(), "far from windows stops both rain layers")
	host.play_sound("rain_glass")
	check(not host._loops.has("rain_glass"), "shot cannot start duplicate rain loop")
	host.show_scene("garden")
	check(rain._outdoors(cam.global_position), "garden is outdoors")
	await create_timer(0.8).timeout
	check(rain._players.has("rain_night"), "outdoor rain starts")
	state.shot = "C2-01"
	await create_timer(0.8).timeout
	check(not rain.raining() and rain._players.is_empty(), "dry weather stops rain")
	check(is_instance_valid(music) and music.playing, "BGM continues through rain changes")
	host.show_scene("white_hall")
	rain._refresh_glass()
	check(rain._glass.is_empty(), "window cache cleared in windowless scene")
	print("RAIN PROBE failures=", bad)
	host.queue_free()
	player.queue_free()
	await process_frame
	call_deferred("quit", 1 if bad else 0)
