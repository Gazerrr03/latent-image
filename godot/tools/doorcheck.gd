extends SceneTree
func _initialize() -> void:
	var s: Node3D = load("res://levels/ded_house.tscn").instantiate()
	root.add_child(s)
	await process_frame
	for nm in ["门入口", "门出口"]:
		var leaf: MeshInstance3D = s.find_child(nm, true, false)
		if leaf == null:
			print(nm, " MISSING"); continue
		var body: StaticBody3D = null
		for c in leaf.get_children():
			if c is StaticBody3D: body = c
		if body == null:
			print(nm, " NO BODY"); continue
		var cs: CollisionShape3D = body.get_child(0)
		var start_hit: Vector3 = cs.global_position
		var hinge := leaf.global_transform.origin
		leaf.rotation.y = deg_to_rad(90.0)
		await process_frame
		var end_hit: Vector3 = cs.global_position
		print(nm, " ok body=%s shape=%s hinge_drift=%.4f collider_moved=%.2f" % [
			body.name, cs.shape.get_class(), hinge.distance_to(leaf.global_transform.origin),
			start_hit.distance_to(end_hit)])
		leaf.rotation.y = 0.0
	quit()
