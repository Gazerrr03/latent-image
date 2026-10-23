extends SceneTree
func _initialize():
	call_deferred("run")
func run():
	var main = load("res://main.tscn").instantiate()
	root.add_child(main)
	await create_timer(7.0).timeout
	var host = root.get_node("Director").world
	var pl = host.player
	var guide = load("res://world/guide.gd").new()
	guide.host = host
	host.add_child(guide)
	pl.place(Vector3(11.8, 3.62, -10.2), 0)
	await create_timer(0.5).timeout
	await guide._ensure_mesh()
	var t := Vector3(22.85, 3.63, -12.25)
	var path: PackedVector3Array = guide._astar(guide._poly_at(pl.global_position), guide._poly_at(t), pl.global_position, t)
	print("WAYPOINTS ", path)
	# 按路点走，遇到门按 E
	var doors_opened := []
	for wp in path:
		var tries := 0
		while Vector2(pl.global_position.x - wp.x, pl.global_position.z - wp.z).length() > 0.25 and tries < 600:
			var d: Vector3 = wp - pl.global_position
			d.y = 0
			pl.look_at(pl.global_position + d.normalized(), Vector3.UP)
			await physics_frame
			pl.walk(d.normalized(), 1.0 / 60.0)
			tries += 1
			pl._update_hover()
			if pl._door and not host.door_is_open(pl._door) and not doors_opened.has(pl._door):
				doors_opened.append(pl._door)
				print("OPEN ", host.doors[pl._door]["leaf"].name, " at ", pl.global_position.snapped(Vector3.ONE * 0.01))
				host.toggle_door(pl._door, pl.global_position)
				await create_timer(0.9).timeout
		if tries >= 600:
			print("STUCK at ", pl.global_position.snapped(Vector3.ONE * 0.01), " heading to ", wp.snapped(Vector3.ONE * 0.01))
			break
	print("END ", pl.global_position.snapped(Vector3.ONE * 0.01), " room=", host.room_at(pl.global_position))
	quit()
