extends SceneTree
func _initialize():
	call_deferred("run")
func run():
	var main = load("res://main.tscn").instantiate()
	root.add_child(main)
	await create_timer(7.0).timeout
	var host = root.get_node("Director").world
	print("SHOT ", root.get_node("GameState").shot, " cur=", host.current_id, " explore=", host.exploring)
	var guide = load("res://world/guide.gd").new()
	guide.host = host
	host.add_child(guide)
	host.player.place(Vector3(9.6, 0.02, -1.1), 0)
	await create_timer(0.5).timeout
	await guide._ensure_mesh()
	var start = guide._poly_at(host.player.global_position)
	for t in [Vector3(22.85, 3.63, -12.25), Vector3(21.4, 3.63, -9.0), Vector3(16.4, 3.6, -14.0), Vector3(12.5, 3.62, -9.4), Vector3(9.6, 3.62, -4.25)]:
		var goal = guide._poly_at(t)
		var path = guide._astar(start, goal, host.player.global_position, t) if goal >= 0 else PackedVector3Array()
		print("PATH to ", t, " goal_poly=", goal, " len=", path.size())
	# 后门：从后门过道往北打射线
	var space = host.get_world_3d().direct_space_state
	for x in [11.5, 12.0, 12.5, 13.0, 13.5]:
		var q = PhysicsRayQueryParameters3D.create(Vector3(x, 4.6, -9.4), Vector3(x, 4.6, -14.0))
		var h = space.intersect_ray(q)
		print("RAY x=", x, " hit=", h.get("position"), " by=", (h.get("collider").get_parent().name if h else ""))
	for n in host.doors:
		print("DOOR ", host.doors[n]["leaf"].name, " ", host.doors[n]["leaf"].global_position.snapped(Vector3.ONE*0.01))
	quit()
