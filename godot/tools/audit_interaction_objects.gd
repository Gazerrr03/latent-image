extends SceneTree
## 在真实关卡中逐热区找有地面、容得下角色、看得见目标的站位。
## 不任意移动关卡对象、不关闭遮挡；容器通过正常开门动作后检查内部物品。
const Targeting := preload("res://world/interaction_targeting.gd")
var results: Array = []
var host: Node
var camera: Camera3D

func _initialize() -> void:
	call_deferred("run")

func run() -> void:
	root.get_node("GameState").persist = false
	var main: Node = load("res://main.tscn").instantiate()
	root.add_child(main)
	await process_frame
	root.get_node("GameState").reset()
	var director := root.get_node("Director")
	var content := root.get_node("ContentDB")
	director.ui.menus.hide()
	host = director.world
	camera = Camera3D.new()
	main.add_child(camera)
	var rooms: Array = []
	for h in content.hotspots.values():
		if not rooms.has(h["scene"]):
			rooms.append(h["scene"])
	for room_id in rooms:
		if room_id == "ded_corridor":
			continue # 特殊回廊按层创建，需要专门的层状态审查。
		host.show_scene(room_id)
		var shot: String = {"guest_room": "C6-02", "darkroom": "C1-05", "archive": "C2-03", "con_room": "C2-04", "child_room": "C3-04", "greenhouse": "C4-03", "seance": "C5-03"}.get(room_id, "C1-05")
		root.get_node("GameState").shot = shot
		host.apply_room_states(shot)
		host.set_mode("walk", "")
		host.player.frozen = true
		await physics_frame
		await physics_frame
		var candidates: Array = []
		for h in content.hotspots.values():
			if h["scene"] == room_id and host.hotspot_nodes.has(h["id"]):
				candidates.append(host.hotspot_nodes[h["id"]])
		for body in host.doors:
			if not candidates.has(body):
				candidates.append(body)
		for body in get_nodes_in_group("light_switch"):
			if not candidates.has(body):
				candidates.append(body)
		for h in content.hotspots.values():
			if h["scene"] != room_id:
				continue
			var target: Node3D = host.hotspot_nodes.get(h["id"])
			var result := {"id": h["id"], "room": room_id, "name": h["label"], "status": "missing", "samples": 0}
			if target:
				result["status"] = "blocked"
				if h["id"] == "hs_gh_latch":
					for door in host.doors:
						if String(host.doors[door]["leaf"].name) == "暗房·温室侧门" and not host.door_is_open(door):
							host.toggle_door(door, host.doors[door]["leaf"].global_position + Vector3(1, 0, 0))
							await create_timer(0.9).timeout
							result["side_door_opened"] = host.door_is_open(door)
				var leaf: Node3D = target.get_meta("container_leaf") if target.has_meta("container_leaf") else null
				if is_instance_valid(leaf):
					for door in host.doors:
						if host.doors[door]["leaf"] == leaf:
							host.toggle_door(door, leaf.global_position - Vector3(1.0, 0, 0))
							await create_timer(0.9).timeout
							result["container_opened"] = host.door_is_open(door)
				var floor_y: float = host.spawn[0].y
				if host._room_spawn.has(room_id):
					floor_y = host._room_spawn[room_id][0].y
				for radius in [1.2, 1.65, 0.8, 2.0]:
					for step in 24:
						var angle := TAU * step / 24.0
						var position: Vector3 = target.global_position + Vector3(sin(angle), 0, cos(angle)) * float(radius)
						var floor_query := PhysicsRayQueryParameters3D.create(Vector3(position.x, floor_y + 0.35, position.z), Vector3(position.x, floor_y - 0.65, position.z), 1)
						floor_query.exclude = [host.player.get_rid()]
						var floor_hit := camera.get_world_3d().direct_space_state.intersect_ray(floor_query)
						if floor_hit.is_empty() or floor_hit.normal.y < 0.8:
							continue
						var feet: Vector3 = floor_hit.position + Vector3.UP * 0.03
						if not can_stand(feet):
							continue
						result["samples"] += 1
						camera.global_position = feet + Vector3.UP * 1.6
						camera.look_at(target.global_position, Vector3.UP)
						if Targeting.pick(camera, candidates, null, [host.player.get_rid()]) == target:
							result["status"] = "selectable"
							result["feet"] = [feet.x, feet.y, feet.z]
							result["distance"] = camera.global_position.distance_to(target.global_position)
							break
					if result["status"] == "selectable":
						break
			if result["status"] == "selectable":
				result["edge_checks"] = check_edges(target, candidates)
			results.append(result)
			print("OBJECT ", JSON.stringify(result))
	var file := FileAccess.open("/tmp/dm-interaction-objects.json", FileAccess.WRITE)
	file.store_string(JSON.stringify(results, "\t"))
	var bad := results.filter(func(row): return row["status"] != "selectable").size()
	print("OBJECT_AUDIT total=", results.size(), " incomplete=", bad)
	quit(0 if bad == 0 else 1)

func can_stand(feet: Vector3) -> bool:
	var capsule := CapsuleShape3D.new()
	capsule.radius = 0.3
	capsule.height = 1.75
	var query := PhysicsShapeQueryParameters3D.new()
	query.shape = capsule
	query.transform = Transform3D(Basis.IDENTITY, feet + Vector3.UP * 0.875)
	query.collision_mask = 1
	query.exclude = [host.player.get_rid()]
	return camera.get_world_3d().direct_space_state.intersect_shape(query, 1).is_empty()


## 从已验证站位，沿四个屏幕方向找到真实形状边界，再偏出6px。
## 记录其它目标优先与遮挡结果，不把合理竞争强行算成目标丢失。
func check_edges(target: CollisionObject3D, candidates: Array) -> Array:
	var original := camera.global_transform
	var center := camera.get_viewport().get_visible_rect().size*.5
	var edges: Array=[]
	for direction in [Vector2.LEFT,Vector2.RIGHT,Vector2.UP,Vector2.DOWN]:
		camera.global_transform=original
		var edge := -1.0
		var available: int = int(center.x if direction.x!=0 else center.y)-8
		for offset in range(2,available,2):
			var ray := camera.project_ray_normal(center+direction*float(offset))
			var direct := false
			for child in target.get_children():
				if child is CollisionShape3D and not child.disabled:
					var inv: Transform3D = child.global_transform.affine_inverse()
					if Targeting._bounds(child.shape).intersects_segment(inv*camera.global_position,inv*(camera.global_position+ray*2.54))!=null:direct=true
			if not direct:
				edge=float(offset);break
		if edge<0:
			edges.append({"direction":str(direction),"status":"offscreen_edge"});continue
		var ray := camera.project_ray_normal(center+direction*(edge+6))
		camera.look_at(camera.global_position+ray,Vector3.UP)
		var picked := Targeting.pick(camera,candidates,null,[host.player.get_rid()])
		var kept := Targeting.pick(camera,candidates,target,[host.player.get_rid()])
		var status := "tolerated" if picked==target else "competing" if picked!=null else "not_selected"
		edges.append({"direction":str(direction),"edge_px":edge,"outside_px":6,"status":status,"picked":String(picked.name) if picked else "","sticky_kept":kept==target,"alone_selected":Targeting.pick(camera,[target],null,[host.player.get_rid()])==target,"diagnostics":edge_obstructions(target) if picked==null else []})
	camera.global_transform=original
	return edges

func edge_obstructions(target: CollisionObject3D) -> Array:
	var details: Array=[]
	var origin := camera.global_position
	var forward := -camera.global_basis.z
	for child in target.get_children():
		if not child is CollisionShape3D or child.disabled:continue
		var bounds := Targeting._bounds(child.shape)
		var inv: Transform3D=child.global_transform.affine_inverse()
		var depth: float=maxf(.1,(child.global_transform*bounds.get_center()-origin).dot(forward))
		var margin: float=minf(.14,22.0*2*tan(deg_to_rad(camera.fov)*.5)*depth/720.0)
		var scale: Vector3=child.global_basis.get_scale().abs().max(Vector3.ONE*.001)
		var expanded:=AABB(bounds.position-Vector3.ONE*margin/scale,bounds.size+Vector3.ONE*2*margin/scale)
		var hit=expanded.intersects_segment(inv*origin,inv*(origin+forward*2.54))
		if hit==null:details.append({"reason":"outside_margin"});continue
		var point: Vector3=child.global_transform*Vector3(hit).clamp(bounds.position,bounds.end)
		var query:=PhysicsRayQueryParameters3D.create(origin,point,1|4)
		query.exclude=[host.player.get_rid()];query.hit_back_faces=true
		var obstruction:=camera.get_world_3d().direct_space_state.intersect_ray(query)
		details.append({"distance":origin.distance_to(point),"obstruction":String(obstruction.collider.name) if not obstruction.is_empty() else "","obstruction_before_surface_m":origin.distance_to(point)-origin.distance_to(obstruction.position) if not obstruction.is_empty() else 0.0})
	return details
