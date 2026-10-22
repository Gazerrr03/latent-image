extends SceneTree
## 单独运行的实机检视性能抽样。保持项目画质和滤镜，不与其它 Godot 测试并行。
## 每种状态预热 2 秒，实测 5 秒；不把它当作所有场景达标的证据。
var director: Node
var ui: Node
var host: Node

func _initialize() -> void:
	call_deferred("run")

func run() -> void:
	if DisplayServer.get_name() == "headless":
		quit(2)
		return
	root.get_node("GameState").persist = false
	var main: Node = load("res://main.tscn").instantiate()
	root.add_child(main)
	await process_frame
	root.get_node("GameState").reset()
	director = root.get_node("Director")
	ui = director.ui
	host = director.world
	ui.menus.hide()
<<<<<<< HEAD
	if OS.get_cmdline_user_args().has("--corridor-reviews"):
		var below: int = await corridor_reviews()
		quit(0 if below == 0 else 1)
		return
=======
>>>>>>> codex/snapshot-source-20261022-1
	if OS.get_cmdline_user_args().has("--new-assets"):
		var below: int = await new_assets()
		quit(0 if below == 0 else 1)
		return
	if OS.get_cmdline_user_args().has("--darkroom"):
		var below: int = await darkroom()
		quit(0 if below == 0 else 1)
		return
	if OS.get_cmdline_user_args().has("--extended"):
		var below: int = await extended()
		quit(0 if below == 0 else 1)
		return
	host.show_scene("guest_room")
	host.set_mode("walk", "")
	ui.set_cinematic(false)
	ui.eyelids_set(1.0)
	var target: Node3D = host.hotspot_nodes["hs_notebook"]
	host.player.place(Vector3(2.8, 3.6, -4.7), 0)
	host.player.cam.look_at(target.global_position, Vector3.UP)
	print("INSPECTION_PERF_META ", JSON.stringify({"gpu": RenderingServer.get_video_adapter_name(), "viewport": str(root.size), "vsync": DisplayServer.window_get_vsync_mode()}))
	var bad := 0
	for mode in ["walk", "paper", "fixed", "notebook"]:
		if mode == "paper":
			ui.inspect_hotspot("hs_coat")
		elif mode == "fixed":
			ui.inspect_hotspot("hs_drawer")
		elif mode == "notebook":
			root.get_node("GameState").add_evidence("ev_letter_p2")
			ui.browse_board()
			ui.board.examine("ev_letter_p2")
		if not await sample("guest_room", mode):
			bad += 1
		if ui.inspector.active:
			ui.inspector.close(true)
		if ui.board.visible:
			ui.board.close()
	print("INSPECTION_PERF below_45=", bad)
	quit(0 if bad == 0 else 1)


func sample(room: String, mode: String) -> bool:
	await create_timer(2.0).timeout
	var frames: Array[float] = []
	var start := Time.get_ticks_usec()
	var last := start
	while Time.get_ticks_usec() - start < 5000000:
		await process_frame
		var now := Time.get_ticks_usec()
		frames.append((now - last) / 1000.0)
		last = now
	var fps := frames.size() * 1000000.0 / (last - start)
	frames.sort()
	print("INSPECTION_PERF ", JSON.stringify({"room": room, "mode": mode, "fps": fps, "p95_ms": frames[int(frames.size() * 0.95)], "p99_ms": frames[int(frames.size() * 0.99)], "samples": frames.size()}))
	return fps >= 45.0


func extended() -> int:
	var rows: Array = JSON.parse_string(FileAccess.get_file_as_string("res://../docs/验证/2026-10-20-物品检视/逐对象判定.json"))
	var positions := {}
	for row in rows:
		positions[row["id"]] = row["feet"]
	var groups := {
		"child_room": ["C3-04", "hs_draw_path", ["hs_draw_path", "hs_draw_wall", "hs_draw_family", "hs_draw_boxes", "hs_draw_train"]],
		"greenhouse": ["C4-03", "hs_gh_photos", ["hs_gh_latch", "hs_gh_photos"]],
		"seance": ["C5-03", "hs_se_cards", ["hs_se_cards", "hs_se_photo", "hs_se_gloves"]],
	}
	var bad := 0
	ui.set_cinematic(false)
	ui.eyelids_set(1.0)
	print("INSPECTION_PERF_META ", JSON.stringify({"gpu": RenderingServer.get_video_adapter_name(), "viewport": str(root.size), "vsync": DisplayServer.window_get_vsync_mode(), "scope": "three investigation rooms"}))
	for room in groups:
		var shot: String = groups[room][0]
		var id: String = groups[room][1]
		root.get_node("GameState").shot = shot
		host.show_scene(room)
		host.apply_room_states(shot)
		host.set_mode("walk", "")
		host.highlight_hotspots(groups[room][2])
		var feet: Array = positions[id]
		host.player.place(Vector3(feet[0], feet[1], feet[2]), 0)
		var direction: Vector3 = host.hotspot_nodes[id].global_position - host.player.cam.global_position
		host.player.rotation.y = atan2(-direction.x, -direction.z)
		host.player._pitch = atan2(direction.y, Vector2(direction.x, direction.z).length())
		for mode in ["walk", "inspection"]:
			if mode == "inspection":
				ui.inspect_hotspot(id)
			if not await sample(room, mode):
				bad += 1
			if ui.inspector.active:
				ui.inspector.close(true)
		if room == "greenhouse":
			var detail: Array = positions["hs_gh_latch"]
			host.player.place(Vector3(detail[0], detail[1], detail[2]), 0)
			ui.inspect_hotspot("hs_gh_latch")
			if not await sample(room, "latch_detail_light"):
				bad += 1
			ui.inspector.close(true)
	print("INSPECTION_PERF below_45=", bad)
	return bad


func darkroom() -> int:
	var rows: Array = JSON.parse_string(FileAccess.get_file_as_string("res://../docs/验证/2026-10-20-物品检视/逐对象判定.json"))
	var positions := {}
	for row in rows:positions[row["id"]]=row["feet"]
	root.get_node("GameState").shot="C1-05"
	host.show_scene("darkroom");host.apply_room_states("C1-05");host.set_mode("walk", "")
	ui.set_cinematic(false);ui.eyelids_set(1.0)
	print("INSPECTION_PERF_META ", JSON.stringify({"gpu": RenderingServer.get_video_adapter_name(), "viewport": str(root.size), "vsync": DisplayServer.window_get_vsync_mode(), "scope": "darkroom native residue and bottle"}))
	var bad := 0
	for id in ["hs_tray", "hs_bottles"]:
		var feet: Array=positions[id]
		host.player.place(Vector3(feet[0],feet[1],feet[2]),0)
		host.player.cam.look_at(host.hotspot_nodes[id].global_position)
		ui.inspect_hotspot(id)
		if not await sample("darkroom", id):bad+=1
		ui.inspector.close(true)
	print("INSPECTION_PERF below_45=",bad)
	return bad


func new_assets() -> int:
	var rows: Array = JSON.parse_string(FileAccess.get_file_as_string("res://../docs/验证/2026-10-20-物品检视/逐对象判定.json"))
	var positions := {}
	for row in rows:positions[row["id"]]=row["feet"]
	ui.set_cinematic(false);ui.eyelids_set(1.0)
	print("INSPECTION_PERF_META ", JSON.stringify({"gpu":RenderingServer.get_video_adapter_name(),"viewport":str(root.size),"vsync":DisplayServer.window_get_vsync_mode(),"scope":"native shoes, sweater, cloth and five-source handwriting"}))
	var bad := 0
	var cases := [["guest_room","C0-11","hs_shoes"],["con_room","C2-04","hs_con_sweater"],["garden","C4-06","hs_vent_louver"],["guest_room","C5-08","hs_handwriting"]]
	if OS.get_cmdline_user_args().has("--handwriting-only"):
		cases = [["guest_room","C5-08","hs_handwriting"]]
<<<<<<< HEAD
	if OS.get_cmdline_user_args().has("--final-photo"):
		cases = [["seance","C5-03","hs_se_photo"]]
	if OS.get_cmdline_user_args().has("--ringbox"):
		cases = [["con_room","C2-04","hs_con_ringbox"]]
=======
>>>>>>> codex/snapshot-source-20261022-1
	if OS.get_cmdline_user_args().has("--frame-latch"):
		cases = [["archive","C2-05","hs_doorframe"],["greenhouse","C4-03","hs_gh_latch"]]
	for item in cases:
		var room: String=item[0];var shot: String=item[1];var id: String=item[2]
		root.get_node("GameState").shot=shot
		host.show_scene(room);host.apply_room_states(shot);host.set_mode("walk","")
		var feet: Array=positions[id]
		host.player.place(Vector3(feet[0],feet[1],feet[2]),0)
		host.player.cam.look_at(host.hotspot_nodes[id].global_position)
		ui.inspect_hotspot(id)
<<<<<<< HEAD
		if OS.get_cmdline_user_args().has("--final-photo"):
			await create_timer(.3).timeout
			ui.inspector.flip()
=======
>>>>>>> codex/snapshot-source-20261022-1
		if not await sample(room,id):bad+=1
		ui.inspector.close(true)
		if id in ["hs_handwriting","hs_doorframe","hs_gh_latch"]:
			var evidence: String = root.get_node("ContentDB").hotspots[id]["evidence"]
			root.get_node("GameState").add_evidence(evidence)
			ui.browse_board();ui.board.examine(evidence)
			if not await sample(room,id+"_notebook"):bad+=1
			ui.inspector.close(true);ui.board.close()
	print("INSPECTION_PERF below_45=",bad)
	return bad
<<<<<<< HEAD


func corridor_reviews() -> int:
	host.show_scene("guest_room");host.set_mode("walk","")
	ui.set_cinematic(false);ui.eyelids_set(1.0)
	print("CORRIDOR_REVIEW_PERF_META ",JSON.stringify({"gpu":RenderingServer.get_video_adapter_name(),"window":str(root.size),"logical_viewport":str(root.get_visible_rect().size),"vsync":DisplayServer.window_get_vsync_mode()}))
	var bad:=0
	ui.browse_board();await process_frame
	for id in ["ev_corridor_hook","ev_corridor_circle","ev_corridor_window"]:
		root.get_node("GameState").add_evidence(id);ui.board.examine(id)
		if not await sample("guest_room",id+"_notebook"):bad+=1
		ui.inspector.close(true)
	ui.board.close()
	print("CORRIDOR_REVIEW_PERF below_45=",bad)
	return bad
=======
>>>>>>> codex/snapshot-source-20261022-1
