extends Node3D
## 入口：搭起世界、玩家、界面，然后交给 Director 播放分镜。
## 无界面回归测试：Godot --headless --path godot -- --autoplay

const SceneHost := preload("res://world/scene_host.gd")
const Player := preload("res://world/player.gd")
const UiRoot := preload("res://ui/ui_root.gd")
const DebugPanel := preload("res://ui/debug_panel.gd")
const MediaFx := preload("res://ui/media_fx.gd")
const FootagePlayer := preload("res://ui/footage_player.gd")


func _ready() -> void:
	var host := SceneHost.new()
	add_child(host)
	var player := Player.new()
	add_child(player)
	host.player = player
	var fx := MediaFx.new()
	add_child(fx)
	var footage := FootagePlayer.new()
	footage.fx = fx
	add_child(footage)
	var ui := UiRoot.new()
	ui.fx = fx
	ui.footage = footage
	add_child(ui)
	Director.ui = ui
	Director.world = host
	add_child(DebugPanel.new())
	if not Director.autoplay and _arg("--capture=") == "":
		Director.finished.connect(_on_finished)

	if Director.autoplay or _arg("--capture=") != "":
		GameState.persist = false
	if _arg("--corridor=") != "":
		_corridor_capture(int(_arg("--corridor=")))
		return
	if OS.get_cmdline_user_args().has("--probe-map"):
		var g := _arg("--group=")
		var code: int = await preload("res://tools/probe_map.gd").run(host, g if g != "" else "c1")
		get_tree().quit(code)
		return
	if Director.autoplay:
		_autoplay()
		return
	var cap := _arg("--capture=")
	if cap != "":
		_capture(cap)
		return
	# 标题页：有存档时“继续调查”（ui/menus.gd）
	if not GameState.load_save():
		GameState.reset()
	ui.menus.show_title()


## 走到结尾（尾声之后）：▸ 再读一遍
func _on_finished() -> void:
	var k: int = await Director.ui.choose("", ["再读一遍"])
	if k == 0:
		GameState.reset()
		GameState.delete_save()
		Director.start()


## 自动选第一个选项走完整条路径，检查是否到达终局
func _autoplay() -> void:
	GameState.reset()
	var watchdog := get_tree().create_timer(120.0)
	watchdog.timeout.connect(func():
		printerr("AUTOPLAY 超时，停在镜号 ", GameState.shot)
		get_tree().quit(2))
	Director.finished.connect(func():
		# 通过 = 选定了一种讲法，且连线规则表里的每一组推论都已成立
		var missing: Array = ContentDB.links.keys().filter(func(g): return not GameState.links_done.has(g))
		var ok := GameState.ending != "" and missing.is_empty()
		print("\n── AUTOPLAY 结束 ──")
		print("最后镜号 %s ｜ 推论 %s ｜ 未成立 %s ｜ 讲法 %s ｜ 容器 %s ｜ 证据 %d 件" % [
			GameState.shot, GameState.links_done, missing, GameState.ending,
			GameState.container, GameState.evidence.size()])
		print("结果：", "通过" if ok else "未通过")
		get_tree().quit(0 if ok else 1))
	Director.shot_started.connect(func(r): print("▶ ", r["shot_id"]))
	Director.start()


func _arg(prefix: String) -> String:
	for a in OS.get_cmdline_user_args():
		if a.begins_with(prefix):
			return a.trim_prefix(prefix)
	return ""


## 截图：Godot --path godot -- --capture=C1-02 [--leak=3] [--grant-all] [--examine=ev_id] [--fx=纪录片片头] [--clean [--keep-fx]] [--play=片头_怪谈] [--view=取代] [--at=x,y,z,朝向[,俯仰]] [--menu=标题|暂停|设置|操作|确认] [--out=/tmp/x.png]
## 跳到指定镜号，等画面稳定后截图并退出。供 agent 自查画面用。
## 截图自查：直接进回廊的第 N 层（1—6），走几步后截图
func _corridor_capture(which: int) -> void:
	GameState.reset()
	GameState.set_leak(2)
	if _arg("--fx=") != "":
		Director.ui.fx.set_override(_arg("--fx="))
	Director.world.start_corridor()
	await get_tree().create_timer(0.6).timeout
	var c: Node = Director.world.corridor
	c.running = true
	c._enter(clampf(which - 1, 0, 5))
	if _arg("--at=") != "":
		var at := _arg("--at=").split(",")
		Director.world.player.place(c.global_position + Vector3(float(at[0]), float(at[1]), float(at[2])), float(at[3]))
	if _arg("--walk=") != "":
		# 模拟往前走 N 米（验证字幕、脚印、转身），每帧把玩家沿中线前推
		var d := float(_arg("--walk="))
		var t := 0.0
		while t < d / 1.4:
			await get_tree().process_frame
			t += get_process_delta_time()
			var k := minf(d, t * 1.4)
			var p: Vector3 = c._at(k)
			Director.world.player.place(c.global_position + p, 0.0 if k < 8.0 else 90.0)
	await get_tree().create_timer(float(_arg("--wait=")) if _arg("--wait=") != "" else 3.0).timeout
	var vp := get_viewport()
	var img := vp.get_texture().get_image()
	img.save_png(_arg("--out=") if _arg("--out=") != "" else "/tmp/corridor.png")
	print("截图已保存：", _arg("--out="))
	get_tree().quit(0)


func _capture(shot_id: String) -> void:
	GameState.reset()
	if _arg("--leak=") != "":
		GameState.set_leak(int(_arg("--leak=")))
	if _arg("--fx=") != "":
		Director.ui.fx.set_override(_arg("--fx="))
	if OS.get_cmdline_user_args().has("--grant-all"):
		for id in ContentDB.evidence:
			GameState.add_evidence(id)
	Director.start(shot_id)
	if _arg("--fx=") != "":
		await get_tree().process_frame
		Director.ui.fx.set_override(_arg("--fx="))
	if _arg("--hint-test=") != "":
		# 截图自查：模拟在当前连线组连错 N 次后的提示
		await get_tree().create_timer(1.0).timeout
		var pairs: Array = ContentDB.links.get("d1", [])
		var usable := pairs.filter(func(p): return GameState.evidence.has(p["a"]) and GameState.evidence.has(p["b"]))
		Director.ui.footage.cancel()
		Director._link_hint("d1", ["ev_letter_p1", "ev_vent_print"], usable, int(_arg("--hint-test=")))
	if _arg("--examine=") != "":
		# 截图自查：打开证据板，把一张证据拿起来看
		await get_tree().create_timer(1.0).timeout
		if not Director.ui.board.visible:
			Director.ui.board.open("证据板")
		Director.ui.board.examine(_arg("--examine="))
	if _arg("--play=") != "":
		await get_tree().process_frame
		Director.ui.footage.play_clip(_arg("--play="))
	if _arg("--at=") != "":
		# 截图自查：自由探索时把玩家放到某处、朝某个方向看（--at=x,y,z,朝向度[,俯仰度]）
		await get_tree().create_timer(1.5).timeout
		var f := _arg("--at=").split(",")
		var pl: Node = Director.world.player
		pl.place(Vector3(float(f[0]), float(f[1]), float(f[2])), float(f[3]) if f.size() > 3 else 0.0)
		if f.size() > 4:
			pl._pitch = deg_to_rad(float(f[4]))
			pl.cam.rotation.x = pl._pitch
	await get_tree().create_timer(float(_arg("--wait=")) if _arg("--wait=") != "" else 2.5).timeout
	if OS.get_cmdline_user_args().has("--clean"):
		# 不显示界面与滤镜，用来截取素材
		Director.ui.visible = false
		# --keep-fx：去掉界面文字，但保留滤镜（用于滤镜对比图）
		Director.ui.fx.visible = OS.get_cmdline_user_args().has("--keep-fx")
		Director.ui.footage.visible = false
		await get_tree().process_frame
		await get_tree().process_frame
	var out := _arg("--out=")
	if out == "":
		out = "/tmp/godot_capture_%s.png" % shot_id
	if OS.get_cmdline_user_args().has("--debug-ui"):
		print("board ", Director.ui.board.size)
	if _arg("--menu=") != "":
		# 截图自查：--menu=标题|确认|暂停|设置|操作
		Director.ui.menus.open_for_capture(_arg("--menu="))
		await get_tree().create_timer(0.6).timeout
	get_viewport().get_texture().get_image().save_png(out)
	print("截图已保存：", out)
	get_tree().quit()
