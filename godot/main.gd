extends Node3D
## 入口：搭起世界、玩家、界面，然后交给 Director 播放分镜。
## 无界面回归测试：Godot --headless --path godot -- --autoplay

const SceneHost := preload("res://world/scene_host.gd")
const Player := preload("res://world/player.gd")
const UiRoot := preload("res://ui/ui_root.gd")
const DebugPanel := preload("res://ui/debug_panel.gd")
const MediaFx := preload("res://ui/media_fx.gd")


func _ready() -> void:
	var host := SceneHost.new()
	add_child(host)
	var player := Player.new()
	add_child(player)
	host.player = player
	var fx := MediaFx.new()
	add_child(fx)
	var ui := UiRoot.new()
	ui.fx = fx
	add_child(ui)
	Director.ui = ui
	Director.world = host
	add_child(DebugPanel.new())

	if Director.autoplay or _arg("--capture=") != "":
		GameState.persist = false
	if Director.autoplay:
		_autoplay()
		return
	var cap := _arg("--capture=")
	if cap != "":
		_capture(cap)
		return
	if GameState.load_save() and GameState.shot != "":
		var k: int = await ui.choose("罗伊德庄园", ["继续调查", "从头开始"])
		if k == 0:
			Director.start(GameState.shot)
			return
	GameState.reset()
	Director.start()


## 自动选第一个选项走完整条路径，检查是否到达终局
func _autoplay() -> void:
	GameState.reset()
	var watchdog := get_tree().create_timer(120.0)
	watchdog.timeout.connect(func():
		printerr("AUTOPLAY 超时，停在镜号 ", GameState.shot)
		get_tree().quit(2))
	Director.finished.connect(func():
		var ok := GameState.ending != "" and GameState.telegrams_left == 0 \
			and GameState.links_done.has("c1") and GameState.links_done.has("c2") and GameState.links_done.has("c3")
		print("\n── AUTOPLAY 结束 ──")
		print("最后镜号 %s ｜ 分支线 %s ｜ 指认 %s ｜ 剩余电报纸 %d ｜ 连线 %s ｜ 终局 %s ｜ 证据 %d 件" % [
			GameState.shot, GameState.line, GameState.accused, GameState.telegrams_left,
			GameState.links_done, GameState.ending, GameState.evidence.size()])
		print("结果：", "通过" if ok else "未通过")
		get_tree().quit(0 if ok else 1))
	Director.shot_started.connect(func(r): print("▶ ", r["shot_id"]))
	Director.start()


func _arg(prefix: String) -> String:
	for a in OS.get_cmdline_user_args():
		if a.begins_with(prefix):
			return a.trim_prefix(prefix)
	return ""


## 截图：Godot --path godot -- --capture=N1-07 [--leak=3] [--grant-all] [--telegrams=4] [--fx=纪录片片头] [--out=/tmp/x.png]
## 跳到指定镜号，等画面稳定后截图并退出。供 agent 自查画面用。
func _capture(shot_id: String) -> void:
	GameState.reset()
	if _arg("--leak=") != "":
		GameState.set_leak(int(_arg("--leak=")))
	if _arg("--fx=") != "":
		Director.ui.fx.set_override(_arg("--fx="))
	if OS.get_cmdline_user_args().has("--grant-all"):
		for id in ContentDB.evidence:
			GameState.add_evidence(id)
	if _arg("--telegrams=") != "":
		GameState.telegrams_left = int(_arg("--telegrams="))
		GameState.changed.emit()
	Director.start(shot_id)
	if _arg("--fx=") != "":
		await get_tree().process_frame
		Director.ui.fx.set_override(_arg("--fx="))
	await get_tree().create_timer(float(_arg("--wait=")) if _arg("--wait=") != "" else 2.5).timeout
	var out := _arg("--out=")
	if out == "":
		out = "/tmp/godot_capture_%s.png" % shot_id
	if OS.get_cmdline_user_args().has("--debug-ui"):
		print("board ", Director.ui.board.size, " register ", Director.ui.register.size, " anchors ", Director.ui.register.anchor_right, " page ", Director.ui.register.page.size)
	get_viewport().get_texture().get_image().save_png(out)
	print("截图已保存：", out)
	get_tree().quit()
