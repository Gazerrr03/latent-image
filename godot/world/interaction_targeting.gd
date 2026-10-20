extends RefCounted
## 每个目标使用自身碰撞形状；容错只用于选择，不扩大实体碰撞。
## 先找直接命中，再在准星周围找候选；遮挡、距离、可见性每次重新检查。
const REACH := 2.4
const EDGE_PIXELS := 22.0 # 按 720p 折算，避免分辨率改变手感
const MAX_MARGIN := 0.14
const KEEP_BONUS := 0.18

static func pick(camera: Camera3D, candidates: Array, previous: Node = null, exclude: Array[RID] = []) -> Node:
	var origin := camera.global_position
	var forward := -camera.global_basis.z
	var best: Node = null
	var best_score := INF
	var direct_best: Node = null
	var direct_distance := INF
	var pixels_per_radian := camera.get_viewport().get_visible_rect().size.y / (2.0 * tan(deg_to_rad(camera.fov) * 0.5))
	var radius_pixels := EDGE_PIXELS * camera.get_viewport().get_visible_rect().size.y / 720.0
	for body in candidates:
		if not is_instance_valid(body) or not body is CollisionObject3D or not body.is_visible_in_tree():
			continue
		for child in body.get_children():
			if not child is CollisionShape3D or child.disabled or child.shape == null:
				continue
			var bounds := _bounds(child.shape)
			var inverse: Transform3D = child.global_transform.affine_inverse()
			var local_origin: Vector3 = inverse * origin
			var local_end: Vector3 = inverse * (origin + forward * (REACH + MAX_MARGIN))
			var hit = bounds.intersects_segment(local_origin, local_end)
			var direct: bool = hit != null
			var depth := maxf(0.1, (child.global_transform * bounds.get_center() - origin).dot(forward))
			var margin := minf(MAX_MARGIN, radius_pixels * depth / pixels_per_radian)
			# 转成本地长度：带缩放的模型不能得到更大的世界容错。
			var scale: Vector3 = child.global_basis.get_scale().abs().max(Vector3.ONE * 0.001)
			var local_margin := Vector3.ONE * margin / scale
			if not direct:
				var expanded := AABB(bounds.position - local_margin, bounds.size + local_margin * 2.0)
				hit = expanded.intersects_segment(local_origin, local_end)
				if hit == null:
					continue
			var surface: Vector3 = child.global_transform * Vector3(hit).clamp(bounds.position, bounds.end)
			var delta := surface - origin
			var distance := delta.length()
			if distance > REACH or delta.dot(forward) <= 0.0:
				continue
			if not _visible(camera, origin, surface, body, exclude):
				continue
			if direct:
				if distance < direct_distance:
					direct_best = body
					direct_distance = distance
				continue
			var lateral := (delta - forward * delta.dot(forward)).length()
			var score := lateral / maxf(0.001, margin) + distance * 0.025
			if body == previous:
				score -= KEEP_BONUS
			if score < best_score:
				best = body
				best_score = score
	return direct_best if direct_best != null else best


static func _bounds(shape: Shape3D) -> AABB:
	if shape is BoxShape3D:
		return AABB(-shape.size * 0.5, shape.size)
	if shape is SphereShape3D:
		return AABB(Vector3.ONE * -shape.radius, Vector3.ONE * shape.radius * 2.0)
	if shape is CapsuleShape3D or shape is CylinderShape3D:
		var size := Vector3(shape.radius * 2.0, shape.height, shape.radius * 2.0)
		return AABB(-size * 0.5, size)
	return shape.get_debug_mesh().get_aabb()


static func _visible(camera: Camera3D, origin: Vector3, surface: Vector3, body: Node, exclude: Array[RID]) -> bool:
	# 只测实体遮挡，热区彼此不遮挡。终点前的墙、桌面、关着的柜门都会阻止选中。
	var query := PhysicsRayQueryParameters3D.create(origin, surface, 1)
	query.exclude = exclude
	query.hit_back_faces = true
	var obstruction := camera.get_world_3d().direct_space_state.intersect_ray(query)
	return obstruction.is_empty() or obstruction.collider == body or origin.distance_to(obstruction.position) >= origin.distance_to(surface) - 0.025
