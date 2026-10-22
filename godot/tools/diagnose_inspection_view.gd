extends SceneTree
## 检查门闩真实站位到细节之间的可见三角面；用于发现缺少碰撞的渲染遮挡。
func _initialize(): call_deferred("run")
func run():
	root.get_node("GameState").persist = false
	var main = load("res://main.tscn").instantiate()
	root.add_child(main)
	await process_frame
	var h = root.get_node("Director").world
	h.show_scene("greenhouse")
	h.set_mode("walk", "")
	await physics_frame
	var origin = Vector3(17.80977,5.23,-9.595)
	var target = Vector3(18.849,4.958,-10.195)
	var hits = []
	for node in h._walk(h.room):
		if not node is MeshInstance3D or not node.is_visible_in_tree(): continue
		var inv = node.global_transform.affine_inverse()
		var start = inv * origin
		var end = inv * target
		if node.mesh.get_aabb().intersects_segment(start,end) == null: continue
		var faces = node.mesh.get_faces()
		for i in range(0,faces.size(),3):
			var point = Geometry3D.segment_intersects_triangle(start,end,faces[i],faces[i+1],faces[i+2])
			if point != null:
				hits.append([origin.distance_to(node.global_transform * point),String(node.name)])
	hits.sort_custom(func(a,b):return a[0]<b[0])
	for hit in hits.slice(0,16): print("VISIBLE_RAY ",hit)
	quit()
