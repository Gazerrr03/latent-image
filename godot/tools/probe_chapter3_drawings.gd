extends SceneTree
## UI fixture only: checks overview composition/return, without walking the chapter or maze.
func _initialize() -> void:
	call_deferred("run")

func run() -> void:
	create_timer(60.0).timeout.connect(func(): printerr("DRAWINGS_UI_FIXTURE TIMEOUT"); quit(2))
	root.add_child(load("res://main.tscn").instantiate())
	for i in 4:
		await process_frame
	var trial: Node = current_scene
	trial = root.get_child(root.get_child_count() - 1).get_node("Chapter3Trial")
	var gallery: Node = trial.get_child(trial.get_child_count() - 1)
	var player: Node = root.get_node("Director").world.player
	var before: Transform3D = player.global_transform
	root.get_node("Director").inspected.emit(gallery.GROUP)
	await create_timer(0.8).timeout
	assert(gallery.overview and not gallery.transitioning)
	assert(gallery.camera.projection == Camera3D.PROJECTION_ORTHOGONAL)
	assert(gallery._house.disabled)
	assert(player.frozen and not player.active)
	var viewport: Rect2 = root.get_visible_rect()
	print("VIEWPORT ", viewport, " wall=", gallery._wall_bounds(), " camera=", gallery.camera.global_position, " size=", gallery.camera.size, " aspect=", gallery.camera.keep_aspect)
	for id in gallery._buttons:
		var button: Button = gallery._buttons[id]
		if not viewport.encloses(button.get_global_rect()):
			printerr("DRAWING_OUTSIDE_VIEWPORT ", id)
			quit(1)
			return
		print("DRAWING_RECT ", id, " ", button.get_global_rect())
	if DisplayServer.get_name() != "headless":
		await RenderingServer.frame_post_draw
		root.get_texture().get_image().save_png("res://../output/chapter3-trial/drawings-overview.png")
	if OS.get_cmdline_user_args().has("--check-drawing-flow"):
		for id in gallery.DRAWINGS:
			print("CHECK_DRAWING_OPEN ", id)
			gallery._buttons[id].pressed.emit()
			await create_timer(0.4).timeout
			var inspector: Node = root.get_node("Director").ui.inspector
			assert(inspector.active, "drawing did not open inspector: " + id)
			await inspector.close()
			print("CHECK_DRAWING_CLOSED ", id)
			await create_timer(0.1).timeout
			assert(gallery.reviewed.has(id), "drawing not marked reviewed: " + id)
			assert(root.get_node("GameState").evidence.has(root.get_node("ContentDB").hotspots[id].evidence))
			assert(not trial.in_house, "house entered before explicit choice")
			assert(gallery._house.disabled == (gallery.reviewed.size() < 5))
		print("DRAWINGS_FLOW PASS: all five use real inspector; collect evidence; unlock house only last; no automatic entry")
		var group_id: String = gallery.GROUP
		gallery._house.pressed.emit()
		await create_timer(1.0).timeout
		assert(trial.in_house)
		assert(root.get_node("Director").world.current_id == "ded_house")
		trial.leave_house()
		await create_timer(0.4).timeout
		assert(not trial.in_house)
		assert(not root.get_node("Director").world.hotspot_nodes.has(group_id))
		print("DRAWINGS_RETURN PASS: explicit final action enters house; return clears collection and resumes chapter")
		quit()
		return
	gallery.selected.emit("close")
	await create_timer(0.6).timeout
	assert(not gallery.overview and player.active and not player.frozen)
	assert(player.global_transform.is_equal_approx(before))
	print("DRAWINGS_UI_FIXTURE PASS: orthographic; five click regions in viewport; house locked; exit restores player")
	quit()
