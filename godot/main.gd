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
	if not OS.get_cmdline_user_args().has("--trial-table"):
		add_child(DebugPanel.new())
	if OS.get_cmdline_user_args().has("--chapter3-trial") or OS.get_cmdline_user_args().has("--chapter3-house-trial") or OS.get_cmdline_user_args().has("--chapter3-drawings-trial"):
		var trial := preload("res://tools/chapter3_trial.gd").new()
		trial.name = "Chapter3Trial"
		add_child(trial)
		trial.begin(OS.get_cmdline_user_args().has("--chapter3-house-trial"))
		return
	if not Director.autoplay and _arg("--capture=") == "":
		Director.finished.connect(_on_finished)

	if Director.autoplay or _arg("--capture=") != "":
		GameState.persist = false
	if _arg("--showcase=") != "":
		await preload("res://tools/showcase/showcase.gd").run(self, _arg("--showcase="))
		return
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
	if OS.get_cmdline_user_args().has("--trial-table"):
		DisplayServer.window_set_title("PR33 第二章餐桌 · 独立试玩 · 不写存档")
		GameState.persist = false
		GameState.reset()
		if OS.get_cmdline_user_args().has("--chapter"):
			Director.start("C2-00")
		else:
			_trial_table()
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


## 截图：Godot --path godot -- --capture=C1-02 [--leak=3] [--grant-all] [--examine=ev_id] [--fx=纪录片片头] [--clean [--keep-fx]] [--play=片头_怪谈] [--view=取代] [--at=x,y,z,朝向[,俯仰]] [--switch=红灯] [--menu=标题|暂停|设置|操作|确认] [--out=/tmp/x.png]
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
	if _arg("--back=") != "":
		# 再往回走 N 米（验证倒放：底色换到倒放那一条，脚步放倒放音样）
		var d0: float = c._dist
		var b := float(_arg("--back="))
		var t := 0.0
		while t < b / 1.1:
			await get_tree().process_frame
			t += get_process_delta_time()
			var k := maxf(d0 - b, d0 - t * 1.1)
			Director.world.player.place(c.global_position + c._at(k), 0.0 if k < 8.0 else 90.0)
		print("回廊：往回走时 底色倒放=%s · 倒放那一条在放=%s" % [c._bed_back, c._bed_rev.playing])
	await get_tree().create_timer(float(_arg("--wait=")) if _arg("--wait=") != "" else 3.0).timeout
	# 回廊自查：这一圈第二段多长、那个人在哪里（追逐）
	print("回廊：第 %d 圈 · 第二段 %.1f m · 走到 %.2f m · 那个人在前方 %.2f m（%s）· 脚步响了 %d 下 · 底色 %s" % [c.layer + 1, c._seg_b, c._dist, c._gap, "合上了" if c._merged else ("没有他" if c._gap < 0.0 else "追着"), c.steps_played, c._bed_fwd.stream.resource_path.get_file() if c._bed_fwd.stream else "无"])
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
		await get_tree().create_timer(float(_arg("--at-after=")) if _arg("--at-after=") != "" else 1.5).timeout
		var f := _arg("--at=").split(",")
		var pl: Node = Director.world.player
		pl.place(Vector3(float(f[0]), float(f[1]), float(f[2])), float(f[3]) if f.size() > 3 else 0.0)
		if f.size() > 4:
			pl._pitch = deg_to_rad(float(f[4]))
			pl.cam.rotation.x = pl._pitch
	if _arg("--switch=") != "":
		# 截图自查：按一下墙上的电灯开关（--switch=红灯）
		await get_tree().create_timer(1.5).timeout
		for b in get_tree().get_nodes_in_group("light_switch"):
			if String(b.get_meta("switch_name", "")) == _arg("--switch="):
				Director.world.toggle_switch(b)
	if _arg("--press=") != "":
		# 截图自查：对着某个目标按了 E（客房的一站 hs_bed、任务目标 talk:…），之后再等 --wait 秒
		await get_tree().create_timer(float(_arg("--press-after=")) if _arg("--press-after=") != "" else 1.5).timeout
		Director.inspected.emit(_arg("--press="))
	if OS.get_cmdline_user_args().has("--recall"):
		# 截图自查：按一下 Q（回想），地面浮现指引
		await get_tree().create_timer(float(_arg("--recall-after=")) if _arg("--recall-after=") != "" else 1.0).timeout
		Director.ui.recall()
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


## PR33 人工试玩入口，不读取或写入玩家存档。
func _trial_table() -> void:
	Director.running = true
	GameState.shot = "C2-02a"
	GameState.add_evidence("ev_extra_plate")
	GameState.quests_done.append("c2_constance")
	var old_skip: bool = Director.skip_text
	Director.skip_text = true
	var smoke := OS.get_cmdline_user_args().has("--trial-smoke")
	if smoke:
		_trial_table_smoke()
	await Director._play(ContentDB.shots["C2-02a"])
	Director.skip_text = old_skip
	if Director._interrupted():
		_trial_interrupted()
		return
	if smoke:
		var host = Director.world
		var ok: bool = host._sublevel == null and host.room.visible and host.player.interaction_owner == null and host.player.active and Director.ui.visible and not GameState.persist and not GameState.evidence.has("ev_table_diagram")
		print("PR33_EXIT_RESTORE ", ok)
		get_tree().quit(0 if ok else 1)
		return
	await Director._explore("c2")
	if Director._interrupted():
		_trial_interrupted()
		return
	Director.running = false
	Director.start("C2-05")


## 只检查资源、椅子隔离与控制交接；不代替人工解谜验收。
func _trial_table_smoke() -> void:
	await get_tree().create_timer(2.0).timeout
	var host = Director.world
	var lvl = host._sublevel
	var chairs: Array = []
	var normal_chairs: Array = []
	if is_instance_valid(lvl):
		for n in host._walk(lvl.get_node("结构/1924临时端椅")):
			if n is MeshInstance3D:
				chairs.append(str(n.name))
	for n in host._walk(host.room):
		if str(n.name).begins_with("餐厅·餐椅7") or str(n.name).begins_with("餐厅·餐椅8"):
			normal_chairs.append(str(n.name))
	var ok: bool = is_instance_valid(lvl) and chairs.size() == 2 and normal_chairs.is_empty() and host.player.interaction_owner == lvl and not host.room.visible and Director.ui.visible
	if DisplayServer.get_name() != "headless":
		ok = ok and lvl.player == host.player and host.player.cam.current
		await RenderingServer.frame_post_draw
		get_viewport().get_texture().get_image().save_png("/tmp/pr33-trial-entry.png")
	print("PR33_ENTRY ", ok, " temporary_chairs=", chairs, " regular_chairs=", normal_chairs)
	if not ok:
		get_tree().quit(1)
		return
	lvl._show_chat("餐桌提示：复用现行阅读界面。")
	await get_tree().process_frame
	Director.ui.cancel()
	await get_tree().process_frame
	print("PR33_SHARED_UI ", not lvl.chat_open)
	lvl._finish()


func _trial_interrupted() -> void:
	var target: String = Director._jump_to
	Director._jump_to = ""
	Director.running = false
	if target != "END":
		Director.start(target)
