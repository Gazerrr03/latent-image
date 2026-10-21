extends Node3D
## 回想（Q）：地面上浮现一段通往目标的路，几秒后淡去（docs/01 第 4 节，10-20）。
## 寻路网格在第一次按 Q 时按大地图的碰撞体烘焙（门全当开着、隐藏的状态层不算），房间状态变了再重烘。
## 画法是贴花（Decal），投在地面和楼梯上，不会浮在台阶外面。样式 STYLE：prints = 脚印，dots = 点状线。

const STYLE := "prints"
## 只画前方这么长的一段
const SHOW_LEN := 14.0
const STEP := 0.55
const HOLD := 4.5

var host: Node3D
## 烘好的网格：顶点、多边形、中心、邻接（[邻居, 共用边的中点]）。寻路服务器在这里问不到路，
## 所以和 tools/probe_map.gd 一样自己算：多边形之间按共用边做 A*，路点取共用边的中点再拉直
var _verts: PackedVector3Array
var _polys: Array = []
var _centers: Array = []
var _adj: Array = []
var _baked_key := ""
var _baking := false
var _marks: Array = []
var _tween: Tween
var _tex_print: ImageTexture
var _tex_dot: ImageTexture


func _ready() -> void:
	_tex_print = _make_print()
	_tex_dot = _make_dot()


## 按一下 Q：找最近的一个目标，画出前方一段路。返回 false = 没有可指的（图标是灰的）
func show_path(targets: Array) -> bool:
	if targets.is_empty() or host.player == null:
		return false
	await _ensure_mesh()
	if _polys.is_empty():
		return false
	var start := _poly_at(host.player.global_position)
	if start < 0:
		return false
	var best: PackedVector3Array = PackedVector3Array()
	var best_len := INF
	for t in targets:
		var goal := _poly_at(t)
		if goal < 0:
			continue
		var path := _astar(start, goal, host.player.global_position, t)
		if path.size() < 2:
			continue
		var l := _length(path)
		if l < best_len:
			best_len = l
			best = path
	if best.size() < 2:
		return false
	_draw(best)
	return true


func _length(p: PackedVector3Array) -> float:
	var l := 0.0
	for i in range(1, p.size()):
		l += p[i - 1].distance_to(p[i])
	return l


func clear() -> void:
	if _tween:
		_tween.kill()
	for m in _marks:
		if is_instance_valid(m):
			m.queue_free()
	_marks.clear()


## 沿路每 STEP 米放一个贴花，从近到远依次浮现，停一会儿，再从近到远淡去
func _draw(path: PackedVector3Array) -> void:
	clear()
	var dist := 0.6   # 脚下那一步不画
	var seg := 0
	var acc := 0.0
	var i := 0
	while dist < SHOW_LEN:
		while seg < path.size() - 1 and acc + path[seg].distance_to(path[seg + 1]) < dist:
			acc += path[seg].distance_to(path[seg + 1])
			seg += 1
		if seg >= path.size() - 1:
			break
		var a := path[seg]
		var b := path[seg + 1]
		var t := (dist - acc) / maxf(a.distance_to(b), 0.001)
		var p := a.lerp(b, t)
		var dir := Vector3(b.x - a.x, 0, b.z - a.z).normalized()
		if dir.length() < 0.1:
			dist += STEP
			continue
		var d := Decal.new()
		var side := Vector3(-dir.z, 0, dir.x) * (0.09 if i % 2 == 0 else -0.09)
		d.size = Vector3(0.11, 0.45, 0.27) if STYLE == "prints" else Vector3(0.1, 0.45, 0.1)
		d.texture_albedo = _tex_print if STYLE == "prints" else _tex_dot
		d.texture_emission = _glow(d.texture_albedo)
		d.emission_energy = 0.35
		d.modulate = Color(0.95, 0.78, 0.52, 0.0)
		d.albedo_mix = 1.0
		d.upper_fade = 0.2
		d.lower_fade = 0.2
		d.normal_fade = 0.6   # 只印在朝上的面上，不印在地毯边、台阶立面上
		d.cull_mask = 1
		add_child(d)
		d.global_position = p + Vector3.UP * 0.1 + (side if STYLE == "prints" else Vector3.ZERO)
		# 贴花沿自己的 -Y 投影；+Z 朝向前进方向的反面，脚尖朝前
		d.global_basis = Basis.looking_at(-dir, Vector3.UP)
		_marks.append(d)
		dist += STEP
		i += 1
	if _marks.is_empty():
		return
	_tween = create_tween()
	var gap := 0.07
	_tween.set_parallel()
	for k in _marks.size():
		_tween.tween_property(_marks[k], "modulate:a", 0.6, 0.35).set_delay(k * gap)
	_tween.set_parallel(false)
	_tween.tween_interval(HOLD)
	_tween.set_parallel()
	for k in _marks.size():
		_tween.tween_property(_marks[k], "modulate:a", 0.0, 0.8).set_delay(k * gap)
	_tween.set_parallel(false)
	_tween.tween_callback(clear)


## 寻路网格：和 tools/probe_map.gd 同样的参数；门全当开着，隐藏的状态层（如“门完好”）不挡路
func _ensure_mesh() -> void:
	var key := _state_key()
	if not _polys.is_empty() and key == _baked_key:
		return
	if _baking:
		while _baking:
			await get_tree().process_frame
		return
	_baking = true
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
	var off: Array = []
	for body in host.doors:
		if is_instance_valid(body):
			off.append([body, body.collision_layer])
			body.collision_layer = 0
	for n in host._walk(host.room):
		if n is CollisionObject3D and not n.is_visible_in_tree() and n.collision_layer != 0:
			off.append([n, n.collision_layer])
			n.collision_layer = 0
	var src := NavigationMeshSourceGeometryData3D.new()
	NavigationServer3D.parse_source_geometry_data(nm, src, host.room)
	for o in off:
		if is_instance_valid(o[0]):
			o[0].collision_layer = o[1]
	# 同步烘焙（约半秒，只在第一次按 Q、或房间状态变了以后发生一次）
	NavigationServer3D.bake_from_source_geometry_data(nm, src)
	_index(nm)
	_baked_key = key
	_baking = false


func _index(nm: NavigationMesh) -> void:
	_verts = nm.get_vertices()
	_polys.clear()
	_centers.clear()
	_adj.clear()
	var owner := {}
	for i in nm.get_polygon_count():
		var p: PackedInt32Array = nm.get_polygon(i)
		_polys.append(p)
		var c := Vector3.ZERO
		for k in p:
			c += _verts[k]
		_centers.append(c / p.size())
		_adj.append([])
		for k in p.size():
			var a := p[k]
			var b := p[(k + 1) % p.size()]
			var e := Vector2i(mini(a, b), maxi(a, b))
			if owner.has(e):
				var o: int = owner[e]
				var mid := (_verts[a] + _verts[b]) * 0.5
				_adj[i].append([o, mid])
				_adj[o].append([i, mid])
			else:
				owner[e] = i


## 包住这个点的多边形（水平投影在多边形里、高度差 0.6 m 内）；都不包住就取最近的中心（1.5 m 内）
func _poly_at(p: Vector3) -> int:
	var best := -1
	var bd := 1.5
	for i in _polys.size():
		var c: Vector3 = _centers[i]
		if absf(c.y - p.y) > 0.6:
			continue
		var pts := PackedVector2Array()
		for k in _polys[i]:
			pts.append(Vector2(_verts[k].x, _verts[k].z))
		if Geometry2D.is_point_in_polygon(Vector2(p.x, p.z), pts):
			return i
		var d := Vector2(c.x - p.x, c.z - p.z).length()
		if d < bd:
			bd = d
			best = i
	return best


func _astar(a: int, b: int, from: Vector3, to: Vector3) -> PackedVector3Array:
	var g := {a: 0.0}
	var came := {}
	var at := {a: from}
	var open := [a]
	var closed := {}
	while not open.is_empty():
		var cur: int = open[0]
		var cf: float = g[cur] + Vector3(at[cur]).distance_to(to)
		for n in open:
			var f: float = g[n] + Vector3(at[n]).distance_to(to)
			if f < cf:
				cf = f
				cur = n
		if cur == b:
			break
		open.erase(cur)
		closed[cur] = true
		for e in _adj[cur]:
			var n: int = e[0]
			if closed.has(n):
				continue
			var ng: float = g[cur] + Vector3(at[cur]).distance_to(e[1])
			if not g.has(n) or ng < g[n]:
				g[n] = ng
				at[n] = e[1]
				came[n] = cur
				if not open.has(n):
					open.append(n)
	if not came.has(b) and a != b:
		return PackedVector3Array()
	var pts: Array = [to]
	var c := b
	while c != a:
		pts.push_front(at[c])
		c = came[c]
	pts.push_front(from)
	return _straighten(pts)


## 拉直：能直接看见（同一高度、中间不隔墙）的路点之间跳过中间的点
func _straighten(pts: Array) -> PackedVector3Array:
	var out := PackedVector3Array([pts[0]])
	var i := 0
	var space := get_world_3d().direct_space_state
	while i < pts.size() - 1:
		var j := pts.size() - 1
		while j > i + 1:
			var p: Vector3 = pts[i]
			var q: Vector3 = pts[j]
			if absf(p.y - q.y) < 0.05:
				var ray := PhysicsRayQueryParameters3D.create(p + Vector3.UP * 0.5, q + Vector3.UP * 0.5, 1)
				ray.exclude = [host.player.get_rid()]
				if space.intersect_ray(ray).is_empty():
					break
			j -= 1
		out.append(pts[j])
		i = j
	return out


## 房间状态变了（门撞开、家具挪动）就要重烘：按大地图里每个状态层的显隐拼一个键
func _state_key() -> String:
	var parts: PackedStringArray = []
	for k in host.named:
		var n = host.named[k]
		if String(k).contains("层·") and is_instance_valid(n) and n is Node3D:
			parts.append("%s=%d" % [k, int(n.visible)])
	parts.sort()
	return str(host.room.get_instance_id()) + "|" + ",".join(parts)


## 发光贴图：颜色 = 透明度（形状外面是黑的，不发光；否则整块方形都会亮）
var _glows := {}
func _glow(t: ImageTexture) -> ImageTexture:
	if _glows.has(t):
		return _glows[t]
	var img := t.get_image()
	img.convert(Image.FORMAT_RGBA8)
	for y in img.get_height():
		for x in img.get_width():
			var a := img.get_pixel(x, y).a
			img.set_pixel(x, y, Color(a, a, a, a))
	var g := ImageTexture.create_from_image(img)
	_glows[t] = g
	return g


## 脚印：鞋底 + 鞋跟两块椭圆（白色，颜色由 modulate 给）
static func _make_print() -> ImageTexture:
	var w := 48
	var h := 96
	var img := Image.create(w, h, false, Image.FORMAT_RGBA8)
	for y in h:
		for x in w:
			var a := 0.0
			var u := (x + 0.5) / w
			var v := (y + 0.5) / h
			# 前掌（上 60%）
			var e1 := pow((u - 0.5) / 0.36, 2) + pow((v - 0.3) / 0.27, 2)
			# 鞋跟（下 30%）
			var e2 := pow((u - 0.5) / 0.3, 2) + pow((v - 0.8) / 0.15, 2)
			a = maxf(clampf((1.0 - e1) * 4.0, 0, 1), clampf((1.0 - e2) * 4.0, 0, 1))
			img.set_pixel(x, y, Color(1, 1, 1, a))
	return ImageTexture.create_from_image(img)


static func _make_dot() -> ImageTexture:
	var n := 32
	var img := Image.create(n, n, false, Image.FORMAT_RGBA8)
	for y in n:
		for x in n:
			var r := Vector2(x + 0.5 - n / 2.0, y + 0.5 - n / 2.0).length() / (n / 2.0)
			img.set_pixel(x, y, Color(1, 1, 1, clampf((1.0 - r) * 3.0, 0, 1)))
	return ImageTexture.create_from_image(img)
