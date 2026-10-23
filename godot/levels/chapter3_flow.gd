extends Node
## 第三章正常流程：绘画检视与小屋往返。独立试玩入口仍在 tools。
signal returned

var in_house := false
var _returning := false
var _saved := {}
var gallery: Node

func inspect_drawings() -> void:
	gallery = preload("res://levels/chapter3_drawings.gd").new()
	add_child(gallery)
	await gallery.run(self)
	gallery.queue_free()
	gallery = null

func enter_house() -> void:
	if in_house:
		return
	var host: Node = Director.world
	_saved = {"targets": host.active_hotspots.duplicate(), "exploring": host.exploring,
		"objective": GameState.objective, "music": host._music_id, "focus": host._focus,
		"conversation": Director.conversation, "leak": GameState.leak_level,
		"pitch": host.player._pitch, "pose": host.player.global_transform}
	Director.conversation = ""
	host.player.conversing = false
	host.exploring = false
	host.stop_music(0.0)
	host.show_scene("ded_house")
	GameState.set_leak(0)
	host.set_mode("walk", "")
	host.set_frozen(false)
	host.player.needs_spawn = false
	Director.ui.set_cinematic(false)
	Director.ui.set_checklist([])
	GameState.objective = "沿小路进入小屋，探索迷宫，寻找北侧出口。"
	in_house = true
	_returning = false
	print("CHAPTER3_TRIAL house ready: scene=", host.current_id, " doors=", host.doors.size(), " spawn=", host.player.global_position, " persist=", GameState.persist)
	await returned

func leave_house() -> void:
	if not in_house or _returning:
		return
	_returning = true
	in_house = false
	var host: Node = Director.world
	GameState.objective = _saved.get("objective", "")
	GameState.set_leak(int(_saved.get("leak", 1)))
	host.show_scene(String(_saved.get("focus", "child_room")))
	host.exploring = _saved.get("exploring", false)
	host.highlight_hotspots(_saved.get("targets", []))
	host.set_mode("walk", "")
	Director.conversation = _saved.get("conversation", "")
	host.player.conversing = Director.conversation != ""
	host.player.global_transform = _saved.get("pose", host.player.global_transform)
	host.player._pitch = float(_saved.get("pitch", 0.0))
	host.player.cam.rotation.x = host.player._pitch
	host.play_music(String(_saved.get("music", "")), 0.0)
	returned.emit()

func _process(_dt: float) -> void:
	if not in_house or _returning:
		return
	var p: Vector3 = Director.world.player.global_position
	# 既有玩法完成条件：穿过北侧出口。
	if p.z < -20.5 and p.x > 0.05 and p.x < 0.95:
		leave_house()
	if p.y < -3.0:
		_restart_house()

func _restart_house() -> void:
	var host: Node = Director.world
	host.player.place(host.spawn[0], host.spawn[1])
	host.set_frozen(false)

func cancel() -> void:
	if in_house:
		leave_house()
	if is_instance_valid(gallery):
		gallery.cancel()
