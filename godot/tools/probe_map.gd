extends RefCounted
## 大地图体检：搭起庄园大地图，门全部打开，按碰撞体烘一张寻路网格，
## 从客房出生点到每个房间的出生点、每个任务目标问一条路。走不通的打“✗”。
## 用法：godot --headless --path godot -- --probe-map [--group=c1]（由 main.gd 调用，需要自动加载）


static func run(host: Node3D, group: String) -> int:
	var tree := host.get_tree()
	var cdb := ContentDB
	host.show_scene("guest_room")
	host.apply_room_states("C1-02")
	await tree.physics_frame
	await tree.physics_frame
	var start: Vector3 = host._room_spawn["guest_room"][0]
	var targets := {}
	for rid in host._room_spawn:
		targets["出生点 " + rid] = host._room_spawn[rid][0]
	for q in cdb.quests.get(group, []):
		var t: String = q["trigger"]
		if t.begins_with("talk:"):
			var n: Node3D = host.named.get(t.get_slice("@", 1) + "/chr_" + t.trim_prefix("talk:").get_slice("@", 0))
			if n:
				targets[t] = n.global_position
		elif t.begins_with("door:"):
			var d: Node3D = host.named.get(t.trim_prefix("door:"))
			if d:
				targets[t] = d.global_position
		elif t.begins_with("enter:"):
			targets[t] = host._room_spawn.get(t.trim_prefix("enter:"), [Vector3.ZERO])[0]
	# 隐藏的状态层在游戏里没有碰撞，烘焙时也去掉
	for n in host._walk(host.room):
		if n is Node3D and not n.visible and n.get_parent():
			n.get_parent().remove_child(n)
			n.queue_free()
	# 门都打开：门扇的碰撞体不参与烘焙
	for body in host.doors:
		(body as CollisionObject3D).collision_layer = 0
	var nm := NavigationMesh.new()
	nm.agent_radius = 0.3
	nm.agent_height = 1.6
	nm.agent_max_climb = 0.3
	nm.agent_max_slope = 40.0
	nm.cell_size = 0.1
	nm.cell_height = 0.05
	nm.geometry_parsed_geometry_type = NavigationMesh.PARSED_GEOMETRY_STATIC_COLLIDERS
	nm.geometry_collision_mask = 1
	nm.filter_baking_aabb = AABB(Vector3(-6, -1, -22), Vector3(36, 10, 34))
	var src := NavigationMeshSourceGeometryData3D.new()
	NavigationServer3D.parse_source_geometry_data(nm, src, host.room)
	NavigationServer3D.bake_from_source_geometry_data(nm, src)
	var vs := nm.get_vertices()
	var vb := AABB(vs[0], Vector3.ZERO) if vs.size() > 0 else AABB()
	for v in vs:
		vb = vb.expand(v)
	print("寻路网格：源几何 %d 个顶点，网格 %d 个多边形，范围 %s" % [src.get_vertices().size() / 3, nm.get_polygon_count(), vb])
	# 无界面模式下寻路服务器是空壳，所以自己算：共用一条边（两个顶点）的多边形连成一片，看起点和目标是不是同一片
	var polys: Array = []
	for i in nm.get_polygon_count():
		polys.append(nm.get_polygon(i))
	var parent := range(polys.size())
	var edge_owner := {}
	for i in polys.size():
		var p: PackedInt32Array = polys[i]
		for k in p.size():
			var a := p[k]
			var b := p[(k + 1) % p.size()]
			var key := Vector2i(mini(a, b), maxi(a, b))
			if edge_owner.has(key):
				_union(parent, i, edge_owner[key])
			else:
				edge_owner[key] = i
	var bad := 0
	var home := _poly_at(nm, polys, start)
	var home_set: int = _find(parent, home) if home >= 0 else -1
	for k in targets:
		var to: Vector3 = targets[k]
		# 人和门本身挡在那里：在它周围一圈 0.9 m 找一块能站的地方
		var pi := _poly_at(nm, polys, to)
		var ok := pi >= 0 and home_set >= 0 and _find(parent, pi) == home_set
		if not ok and not String(k).begins_with("出生点"):
			for d in 8:
				var a := TAU * d / 8
				var q := _poly_at(nm, polys, to + Vector3(sin(a), 0, cos(a)) * 0.9)
				if q >= 0 and _find(parent, q) == home_set:
					ok = true
					pi = q
					break
		if not ok:
			bad += 1
		print("%s %s  %s%s" % ["✓" if ok else "✗", k, to.snapped(Vector3.ONE * 0.01), "  （脚下没有可走的地面）" if pi < 0 else ""])
	print("走不通：%d" % bad)
	return 1 if bad > 0 else 0


static func _find(parent: Array, i: int) -> int:
	while parent[i] != i:
		parent[i] = parent[parent[i]]
		i = parent[i]
	return i


static func _union(parent: Array, a: int, b: int) -> void:
	parent[_find(parent, a)] = _find(parent, b)


## 离这个点最近、高度相差不到 0.6 m 的多边形（按多边形中心，水平 1.2 m 以内）
static func _poly_at(nm: NavigationMesh, polys: Array, p: Vector3) -> int:
	var vs := nm.get_vertices()
	var best := -1
	var bd := 1.2
	for i in polys.size():
		var c := Vector3.ZERO
		for idx in polys[i]:
			c += vs[idx]
		c /= polys[i].size()
		if absf(c.y - p.y) > 0.6:
			continue
		var d := Vector2(c.x - p.x, c.z - p.z).length()
		if d < bd:
			bd = d
			best = i
	return best
