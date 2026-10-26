extends SceneTree
## Records the live chapter-two table level with Godot MovieWriter.
## Run: godot --path godot --write-movie OUTPUT.avi --fixed-fps 30 --resolution 960x540 --script res://tools/record_table_gameplay.gd

func _initialize() -> void:
	call_deferred("record")

func frames(n: int) -> void:
	for i in n:
		await process_frame

func look(player: Node, target: Vector3) -> void:
	var d: Vector3 = target - player.cam.global_position
	player.rotation.y = atan2(-d.x, -d.z)
	player._pitch = clampf(atan2(d.y, Vector2(d.x, d.z).length()), -1.2, 1.2)
	player.cam.rotation.x = player._pitch

func record() -> void:
	root.get_node("GameState").persist = false
	var main: Node = load("res://main.tscn").instantiate()
	root.add_child(main)
	await frames(8)
	root.get_node("Director").ui.menus.hide()
	root.get_node("Director").world.show_scene("dining")
	root.get_node("Director").world.set_mode("walk", "")
	root.get_node("Director").world.enter_level("ded_table")
	await frames(45)
	var level = root.get_node("Director").world._sublevel
	var player = root.get_node("Director").world.player
	if level == null or player == null:
		push_error("Table level did not load")
		quit(1)
		return
	# The player remains the actual gameplay camera. Stage it beside each interaction
	# and pass through the level's normal interaction dispatcher.
	player.place(Vector3(14.35, 0.02, -1.1), 90.0)
	look(player, Vector3(13.4, 0.95, -1.1))
	await frames(55)
	level.hover = {"kind": "drawer", "id": ""}
	level._interact()
	await frames(25)
	level.hover = {"kind": "diagram", "id": ""}
	level._interact()
	await frames(90)
	level._plan_viewer.close()
	await frames(15)
	var order := ["ambrose", "constance", "iris", "gideon", "lucien", "toast_rack", "fruit_bowl", "sugar_bowl", "small_bowl"]
	var slots := ["slot_north", "slot_east_1", "slot_east_2", "slot_west", "slot_south", "slot_toast", "slot_fruit", "slot_sugar", "slot_small"]
	for i in order.size():
		var id: String = order[i]
		var slot: String = slots[i]
		player.place(Vector3(14.3, 0.02, -1.3), 90.0)
		look(player, level.items[id].global_position)
		await frames(12)
		level.hover = {"kind": "item", "id": id}
		level._interact()
		await frames(17)
		var destination: Vector3 = level.SLOT_POS[slot]
		player.place(Vector3(14.7, 0.02, destination.z), 90.0)
		look(player, destination)
		await frames(14)
		level.hover = {"kind": "slot", "id": slot}
		level._interact()
		await frames(19)
		print("TABLE_RECORD placed ", id, " at ", slot)
	for beat in 8:
		await frames(90)
		root.get_node("Director").ui._resolved.emit(0)
		if level.solved:
			break
	await frames(45)
	print("TABLE_RECORD solved=", level.solved, " bell=", level.bell_seq, " slots=", level.slot_items.size())
	quit(0 if level.solved or level.bell_seq else 1)
