extends Node3D
## 场景宿主：按场景 id 搭建房间，管理机位、热区、渗漏材质与声音。
## 房间以人工在 Godot 里搭的关卡场景 res://levels/<房间id>.tscn 为准；还没搭的房间暂用灰盒（房间布局表）。
## 关卡场景的命名约定见 docs/09-团队协作与任务派发.md 第 5 节：
##   spawn 出生点；cam_<机位> 机位（Camera3D）；hs_<id> 可检查物件；chr_<人名> 人物站位；prop_<id> 小物件占位

const HOTSPOT_LAYER := 2
const Actions := preload("res://core/actions.gd")
const PAD := Vector3(0.04, 0.04, 0.04)

var player: Node3D
var shot_cam: Camera3D
var current_id := ""
var room: Node3D
var markers := {}
## 有名字的东西：名称 -> 节点（reveal / conceal 用）
var named := {}
## 人物名 -> 模型里的 AnimationPlayer（方盒子人物自带 idle / walk / talk / tap / sit）
var figures := {}
var hotspot_nodes := {}
## 当前这一轮自由检查的目标；只有它们能被准星选中
var active_hotspots: Array = []
var spawn := [Vector3.ZERO, 0.0]
var _surfaces: Array = []
var _orig_mats := {}
var _leak_mat: ShaderMaterial
var _env: WorldEnvironment
var _cam_key := ""
var _camera_tween: Tween
var _missing_sounds := {}
## 能开关的门：门扇上导入时生成的 StaticBody3D -> {leaf, closed}（closed = 关着时的朝向，第一次开门时找）
var doors := {}
var _loops := {}
var _music: AudioStreamPlayer
var _music_id := ""


func _ready() -> void:
	shot_cam = Camera3D.new()
	shot_cam.fov = 45
	add_child(shot_cam)
	_env = WorldEnvironment.new()
	_env.environment = _make_env()
	add_child(_env)
	_leak_mat = ShaderMaterial.new()
	_leak_mat.shader = load("res://shaders/leak_white.gdshader")


func _make_env() -> Environment:
	var e := Environment.new()
	e.background_mode = Environment.BG_COLOR
	e.background_color = Color("#07070a")
	e.ambient_light_source = Environment.AMBIENT_SOURCE_COLOR
	e.ambient_light_color = Color("#40404c")
	e.ambient_light_energy = 0.35
	e.tonemap_mode = Environment.TONE_MAPPER_ACES
	e.fog_enabled = true
	e.fog_light_color = Color("#0b0b10")
	e.fog_density = 0.02
	return e


# ───────────── 场景 ─────────────

func show_scene(id: String) -> void:
	if id == current_id:
		return
	if _camera_tween:
		_camera_tween.kill()
	current_id = id
	_cam_key = ""
	stop_loops()
	if room:
		remove_child(room)
		room.queue_free()
	markers.clear()
	doors.clear()
	named.clear()
	figures.clear()
	hotspot_nodes.clear()
	_surfaces.clear()
	_orig_mats.clear()
	spawn = [Vector3.ZERO, 0.0]
	var level := ContentDB.level_path(id)
	if ResourceLoader.exists(level):
		room = (load(level) as PackedScene).instantiate()
		add_child(room)
		_adopt_level(room)
	else:
		room = _build_greybox(id)
		add_child(room)
	# 行走模式的画面环境：关卡里机位带了环境（天空、色调）就用它，否则用默认的暗环境
	var level_env: Environment = null
	for m in markers.values():
		if m.size() > 3 and m[3] != null:
			level_env = m[3]
			break
	_env.environment = level_env if level_env else _make_env()
	apply_leak(GameState.leak_level)
	if player:
		player.needs_spawn = true


## 灰盒（过渡用）：还没有关卡场景的房间，按房间登记表（尺寸）与房间布局表搭出来。
## 12 个房间都有关卡场景后，灰盒、房间布局表与这段代码一起删除。
func _build_greybox(id: String) -> Node3D:
	var r := Node3D.new()
	r.name = "Greybox"
	var info: Dictionary = ContentDB.scenes.get(id, {})
	var s := Vector3(_num(info, "width", 4), _num(info, "height", 3), _num(info, "depth", 4))
	var t := 0.1
	_box(r, "地面", Vector3(0, -t / 2, 0), Vector3(s.x, t, s.z), Color("#3a2c22"))
	_box(r, "天花", Vector3(0, s.y + t / 2, 0), Vector3(s.x, t, s.z), Color("#2a2826"))
	_box(r, "前墙", Vector3(0, s.y / 2, -s.z / 2 - t / 2), Vector3(s.x, s.y, t), Color("#3b3430"))
	_box(r, "后墙", Vector3(0, s.y / 2, s.z / 2 + t / 2), Vector3(s.x, s.y, t), Color("#3b3430"))
	_box(r, "左墙", Vector3(-s.x / 2 - t / 2, s.y / 2, 0), Vector3(t, s.y, s.z), Color("#3b3430"))
	_box(r, "右墙", Vector3(s.x / 2 + t / 2, s.y / 2, 0), Vector3(t, s.y, s.z), Color("#3b3430"))
	spawn = [Vector3(0, 0, s.z / 2 - 0.6), 0.0]
	_apply_layout(r, id)
	return r


## 布局表的各行（家具、人物、可检查物件、机位、灯光、出生点）
func _apply_layout(r: Node3D, id: String) -> void:
	for row in ContentDB.layout.get(id, []):
		var p := _vec(row, "x", "y", "z")
		var size := _vec(row, "w", "h", "d")
		var look := _vec(row, "look_x", "look_y", "look_z")
		var before := r.get_child_count()
		match row.get("type", ""):
			"家具":
				# y 是底部离地高度
				var mi := _box(r, row["id"], p + Vector3(0, size.y / 2, 0), size, _color(row, "#5b3f2a"))
				if "镜" in row["id"]:
					# 镜面不随渗漏变白：终局时镜中的白色人形才看得出来
					_surfaces.erase(mi)
					var glass := StandardMaterial3D.new()
					glass.albedo_color = Color("#1d2328")
					glass.metallic = 0.6
					glass.roughness = 0.15
					mi.material_override = glass
			"人物":
				# 人物在这个房间的站位（同一画面里只放一个人，docs/02 第 7 节）
				_figure(r, row["id"], p)
			"可检查物件":
				_hotspot(r, row["id"], p, size if size != Vector3.ZERO else Vector3(0.3, 0.3, 0.3))
			"机位":
				markers[row["id"]] = [p, look]
			"灯光":
				var o := OmniLight3D.new()
				o.position = p
				o.light_color = _color(row, "#ffc98a")
				o.light_energy = _num(row, "energy", 2.0)
				o.omni_range = 6.0
				o.shadow_enabled = true
				if row.get("id", "") != "":
					o.name = row["id"]
				r.add_child(o)
			"出生点":
				var dir := look - p
				spawn = [p, rad_to_deg(atan2(-dir.x, -dir.z)) if dir.length() > 0.01 else 0.0]
			_:
				push_warning("房间布局表：未知类型 %s（%s）" % [row.get("type", ""), id])
		# hidden = 是：开始时隐藏，由镜头表的 reveal(名称) 显示
		if r.get_child_count() > before:
			var node := r.get_child(r.get_child_count() - 1)
			if row.get("id", "") != "":
				named[row["id"]] = node
			if row.get("hidden", "") == "是":
				node.visible = false
	# 人物：人物表里所在房间为本房间、且尚未被指认的人
	for c in ContentDB.characters:
		if c.get("room", "") != id or named.has(c["name"]):
			continue
		named[c["name"]] = _figure(r, c["name"], _vec(c, "x", "y", "z"))


## 灰盒人形：身体 + 头 + 眼部处理（docs/02 第 5 节：除侦探外，所有人的眼睛都被遮住）。
## 人形面朝 +z（玩家通常从 +z 方向看过来）。“镜中人形”是终局镜子里没有脸的白色人形。
func _figure(parent: Node3D, who: String, foot: Vector3) -> Node3D:
	var c: Dictionary = {}
	for row in ContentDB.characters:
		if row["name"] == who:
			c = row
	var root := StaticBody3D.new()
	root.name = who
	root.position = foot
	parent.add_child(root)
	var hgt := _num(c, "height", 1.75)
	# 人物表 model 列：方盒子人物模型（T-025）。有模型就用模型，没有就画灰盒人形
	var model: String = c.get("model", "")
	if model != "" and not model.begins_with("res://"):
		model = "res://" + model
	if model != "" and ResourceLoader.exists(model):
		var inst: Node3D = (load(model) as PackedScene).instantiate()
		inst.name = "模型"
		root.add_child(inst)
		for n in _walk(inst):
			if n is GeometryInstance3D:
				_surfaces.append(n)
				_orig_mats[n] = n.material_override
				# 镜中的人是镜像，不在墙上投影
				if who.begins_with("镜中"):
					n.cast_shadow = GeometryInstance3D.SHADOW_CASTING_SETTING_OFF
			elif n is AnimationPlayer:
				for a in ["idle", "walk", "talk", "sit"]:
					if n.has_animation(a):
						n.get_animation(a).loop_mode = Animation.LOOP_LINEAR
				figures[who] = n
				if n.has_animation("idle"):
					n.play("idle")
					n.seek(randf() * n.current_animation_length)
		var mcs := CollisionShape3D.new()
		var msh := BoxShape3D.new()
		msh.size = Vector3(0.44, hgt, 0.3)
		mcs.shape = msh
		mcs.position.y = hgt / 2
		root.add_child(mcs)
		return root
	var col := _color(c, "#2b2420")
	var head := 0.24
	var body_h := hgt - head - 0.04
	var mirror := who == "镜中人形"
	var body := _mesh(root, Vector3(0, body_h / 2, 0), Vector3(0.44, body_h, 0.28), col)
	var face := _mesh(root, Vector3(0, body_h + 0.04 + head / 2, 0), Vector3(head * 0.85, head, head * 0.9), Color("#c9b9a3"))
	if mirror:
		# 没有脸的白色网格人形
		body.material_override = _leak_mat
		face.material_override = _leak_mat
		return root
	var eye_y := body_h + 0.04 + head * 0.58
	var ec := Color.from_string(c.get("eye_color", ""), Color("#111111")) if c.get("eye_color", "") != "" else Color("#111111")
	match c.get("eye", ""):
		"缎带":
			_mesh(root, Vector3(0, eye_y, 0), Vector3(head * 0.92, 0.05, head * 0.96), ec)
		"布条":
			_mesh(root, Vector3(0, eye_y, 0), Vector3(head * 0.95, 0.075, head * 1.0), ec)
			_mesh(root, Vector3(head * 0.32, eye_y - 0.05, -head * 0.5), Vector3(0.06, 0.12, 0.03), ec)
		"帽檐":
			_mesh(root, Vector3(0, eye_y + 0.035, head * 0.38), Vector3(head * 1.05, 0.025, head * 0.75), ec)
			_mesh(root, Vector3(0, eye_y + 0.07, 0), Vector3(head * 0.9, 0.03, head * 0.92), ec)
		"面纱":
			_mesh(root, Vector3(0, eye_y - 0.02, head * 0.47), Vector3(head * 0.9, head * 0.55, 0.01), ec)
			_mesh(root, Vector3(0, eye_y + 0.11, 0), Vector3(head * 1.2, 0.02, head * 1.2), ec)
		"涂白":
			_mesh(root, Vector3(0, eye_y, head * 0.46), Vector3(head * 0.6, 0.05, 0.01), Color.WHITE)
	var cs := CollisionShape3D.new()
	var sh := BoxShape3D.new()
	sh.size = Vector3(0.44, hgt, 0.3)
	cs.shape = sh
	cs.position.y = hgt / 2
	root.add_child(cs)
	return root


func _mesh(parent: Node3D, pos: Vector3, size: Vector3, color: Color) -> MeshInstance3D:
	var mi := MeshInstance3D.new()
	var bm := BoxMesh.new()
	bm.size = size
	mi.mesh = bm
	mi.position = pos
	var m := StandardMaterial3D.new()
	m.albedo_color = color
	m.roughness = 0.85
	mi.material_override = m
	parent.add_child(mi)
	_surfaces.append(mi)
	_orig_mats[mi] = m
	return mi


## 房间状态表（content/space/room_states.csv）：这一镜打开哪些层。关卡里的层节点命名为“层·<层名>”，
## 状态层是一份 glTF 的实例，开关是一组灯 / 发光件；表里没写的层不动。
func apply_room_states(shot_id: String) -> void:
	var rows: Array = ContentDB.room_states.get(current_id, [])
	if rows.is_empty() or shot_id == "":
		return
	var on: Array = ContentDB.room_layers(current_id, shot_id)
	for r in rows:
		var n = named.get("层·" + String(r.get("layer", "")))
		if n is Node3D:
			_set_present(n, on.has(r["layer"]))


## 镜头表 reveal(名称) / conceal(名称)：显示或隐藏关卡里的某个节点（如终局的镜中人形）
## 让人物播放一个动作（idle / walk / talk / tap / sit）。who 可以写全名或台词里的简称（“吉迪恩”）。
## 不循环的动作（tap）播完自动回到 idle。找不到人物或动作时返回 false。
func figure_anim(who: String, anim: String) -> bool:
	var ap: AnimationPlayer = null
	for k in figures:
		if k == who or String(k).begins_with(who):
			ap = figures[k]
			break
	if ap == null or not is_instance_valid(ap) or not ap.has_animation(anim):
		return false
	if ap.current_animation == anim:
		return true
	ap.play(anim, 0.25)
	if ap.get_animation(anim).loop_mode == Animation.LOOP_NONE and ap.has_animation("idle"):
		ap.queue("idle")
	return true


func set_shown(id: String, on: bool) -> void:
	if named.has(id) and is_instance_valid(named[id]):
		_set_present(named[id], on)
	else:
		push_warning("当前房间里没有：" + id)


## 隐藏的东西也不留碰撞（例如“门完好”层关掉后，那扇关着的门不能还挡在门洞里）
func _set_present(n: Node, on: bool) -> void:
	n.visible = on
	n.process_mode = Node.PROCESS_MODE_INHERIT if on else Node.PROCESS_MODE_DISABLED


static func _num(row: Dictionary, key: String, default: float) -> float:
	var v: String = row.get(key, "")
	return float(v) if v.is_valid_float() else default


static func _vec(row: Dictionary, kx: String, ky: String, kz: String) -> Vector3:
	return Vector3(_num(row, kx, 0), _num(row, ky, 0), _num(row, kz, 0))


static func _color(row: Dictionary, default: String) -> Color:
	var v: String = row.get("color", "")
	return Color.from_string(v, Color(default)) if v != "" else Color(default)


func _box(parent: Node3D, n: String, pos: Vector3, size: Vector3, color: Color) -> MeshInstance3D:
	var body := StaticBody3D.new()
	body.name = n
	body.position = pos
	var mi := MeshInstance3D.new()
	var bm := BoxMesh.new()
	bm.size = size
	mi.mesh = bm
	var m := StandardMaterial3D.new()
	m.albedo_color = color
	m.roughness = 0.85
	mi.material_override = m
	body.add_child(mi)
	var cs := CollisionShape3D.new()
	var sh := BoxShape3D.new()
	sh.size = size
	cs.shape = sh
	body.add_child(cs)
	parent.add_child(body)
	_surfaces.append(mi)
	_orig_mats[mi] = m
	return mi


## from_model = true：物件来自美术模型，模型本身就是物件的样子，
## 所以高亮方块平时隐藏，只在指引时显示成一层半透明的暖光
func _hotspot(parent: Node3D, id: String, pos: Vector3, size: Vector3, from_model := false) -> void:
	var a := Area3D.new()
	a.name = id
	a.position = pos
	a.collision_layer = 1 << (HOTSPOT_LAYER - 1)
	a.collision_mask = 0
	a.set_meta("hotspot_id", id)
	var cs := CollisionShape3D.new()
	var sh := BoxShape3D.new()
	sh.size = size
	cs.shape = sh
	a.add_child(cs)
	var mi := MeshInstance3D.new()
	var bm := BoxMesh.new()
	bm.size = size * 0.6
	mi.mesh = bm
	var m := StandardMaterial3D.new()
	m.albedo_color = Color("#d8cdb4")
	m.emission_enabled = true
	m.emission = Color("#ffcf8a")
	m.emission_energy_multiplier = 0.0
	if from_model:
		bm.size = size + Vector3(0.02, 0.02, 0.02)
		m.transparency = BaseMaterial3D.TRANSPARENCY_ALPHA
		m.albedo_color = Color(1.0, 0.85, 0.6, 0.18)
		m.shading_mode = BaseMaterial3D.SHADING_MODE_UNSHADED
		mi.visible = false
		a.set_meta("from_model", true)
	mi.material_override = m
	a.add_child(mi)
	parent.add_child(a)
	hotspot_nodes[id] = a


## 关卡场景：空间、灯光、构图全部以场景为准，这里只按名字认出需要接上剧情的节点
func _adopt_level(r: Node) -> void:
	# 先换小物件模型，再记下房间表面（渗漏变白用），最后接上出生点、机位、热区、人物
	for n in _walk(r):
		if n is Node3D and String(n.name).begins_with("prop_"):
			_swap_prop(n, String(n.name))
	for n in _walk(r):
		if n is GeometryInstance3D and not n.is_in_group("no_leak"):
			_surfaces.append(n)
			_orig_mats[n] = n.material_override
	_unshadow_lamp_housings(r)
	for n in _walk(r):
		if n is MeshInstance3D and _is_door(String(n.name)):
			for c in n.get_children():
				if c is StaticBody3D:
					c.set_meta("door", true)
					doors[c] = {"leaf": n}
	for n in _walk(r):
		if not n is Node3D or n == r:
			continue
		var nm := String(n.name)
		named[nm] = n
		if not n.visible:
			_set_present(n, false)
		if nm == "spawn":
			spawn = [n.global_position, n.global_rotation_degrees.y]
		elif nm.begins_with("cam_"):
			var fwd: Vector3 = -n.global_transform.basis.z
			var fov: float = n.fov if n is Camera3D else 45.0
			if n is Camera3D:
				n.current = false
			markers[nm.trim_prefix("cam_")] = [n.global_position, n.global_position + fwd, fov,
				n.environment if n is Camera3D else null, n.near if n is Camera3D else 0.05]
		elif nm.begins_with("hs_"):
			_hotspot_on(n, nm)
		elif nm.begins_with("chr_"):
			# 人形挂在站位节点下，面朝站位节点的 +z；reveal / conceal 用人名或 chr_人名都行
			var who := nm.trim_prefix("chr_")
			_figure(n, who, Vector3.ZERO)
			named[who] = n


# ───────────── 门 ─────────────

## 能开关的门扇：名字以“门”结尾、不带括号说明（“（锁着）”“（关着、插上）”“（撞开）”都开不了）。
## 门扇的原点在合页轴上（房间模块 SOP），碰撞在导入设置里生成（见《房间模块SOP》）。
static func _is_door(nm: String) -> bool:
	return nm.ends_with("门") and not nm.contains("（") and not nm.begins_with("门窗_")


func door_is_open(body: Node) -> bool:
	if not doors.has(body):
		return false
	var d: Dictionary = doors[body]
	var leaf: Node3D = d["leaf"]
	if not d.has("closed"):
		d["closed"] = _find_closed(leaf, body)
	return absf(angle_difference(leaf.rotation.y, d["closed"])) > 0.2


## 开门往离开玩家的一侧推开（推不开就换一边、开小一点）；关门转回关着的朝向
func toggle_door(body: Node, from: Vector3) -> void:
	if not doors.has(body):
		return
	var d: Dictionary = doors[body]
	var leaf: Node3D = d["leaf"]
	var target: float = d.get("closed", 0.0)
	if not door_is_open(body):
		target = d["closed"]
		var side := (from - leaf.global_position).dot(leaf.global_basis.z)
		var first := 1.0 if side > 0 else -1.0
		var found := false
		for sgn in [first, -first]:
			for deg in [90.0, 75.0, 60.0, 45.0]:
				if _swing_free(leaf, body, d["closed"] + sgn * deg_to_rad(deg)):
					target = d["closed"] + sgn * deg_to_rad(deg)
					found = true
					break
			if found:
				break
		if not found:
			return
	play_sound("door_creak")
	var t := create_tween().set_trans(Tween.TRANS_SINE).set_ease(Tween.EASE_OUT)
	t.tween_property(leaf, "rotation:y", leaf.rotation.y + angle_difference(leaf.rotation.y, target), 0.7)


## 门扇宽度（本地 +x 方向，从合页量起）与把手高度
func _leaf_span(leaf: MeshInstance3D) -> Vector2:
	var a := leaf.mesh.get_aabb()
	return Vector2(a.end.x, a.position.y + a.size.y * 0.45)


## 关着的门：门扇末端再往外一点就碰到门洞的墙。从当前朝向起左右逐步转，找最近的那个朝向
func _find_closed(leaf: MeshInstance3D, body: Node) -> float:
	var base := leaf.rotation.y
	for k in range(0, 37):
		for sgn in ([1.0] if k == 0 else [1.0, -1.0]):
			var yaw: float = base + sgn * deg_to_rad(5.0 * k)
			if _tip_in_wall(leaf, body, yaw):
				return yaw
	return base


func _tip_in_wall(leaf: MeshInstance3D, body: Node, yaw: float) -> bool:
	var span := _leaf_span(leaf)
	var dir := _leaf_dir(leaf, yaw)
	var start := leaf.global_position + Vector3(0, span.y, 0) + dir * (span.x - 0.03)
	return _ray_hits(start, start + dir * 0.15, body)


func _swing_free(leaf: MeshInstance3D, body: Node, yaw: float) -> bool:
	var span := _leaf_span(leaf)
	var dir := _leaf_dir(leaf, yaw)
	var origin := leaf.global_position + Vector3(0, span.y, 0)
	# 合页一侧留出门套的厚度，末端多留几厘米
	return not _ray_hits(origin + dir * 0.12, origin + dir * (span.x + 0.05), body)


## 门扇在世界里的朝向（本地 +x 绕父节点的竖轴转到 yaw）
func _leaf_dir(leaf: Node3D, yaw: float) -> Vector3:
	var parent_basis: Basis = leaf.get_parent().global_basis if leaf.get_parent() is Node3D else Basis()
	return (parent_basis * Basis(Vector3.UP, yaw) * Vector3.RIGHT).normalized()


func _ray_hits(a: Vector3, b: Vector3, body: Node) -> bool:
	var q := PhysicsRayQueryParameters3D.create(a, b)
	q.exclude = [body.get_rid(), player.get_rid()] if player else [body.get_rid()]
	q.hit_back_faces = true
	return not get_world_3d().direct_space_state.intersect_ray(q).is_empty()


## hs_<id>：网格或方块本身就是物件的样子，热区比它略大一圈（准星先碰到热区）；空节点就放一个默认大小的高亮方块
func _hotspot_on(n: Node3D, nm: String) -> void:
	if n is MeshInstance3D and n.mesh:
		var aabb: AABB = n.mesh.get_aabb()
		_hotspot(n, nm, aabb.get_center(), aabb.size.max(Vector3(0.05, 0.05, 0.05)) + PAD, true)
	elif n is CSGBox3D:
		_hotspot(n, nm, Vector3.ZERO, n.size + PAD, true)
	elif n is Marker3D:
		# 不可见的热区：物件本身已经在美术模型里（房间模块），热区大小写在节点的 size 元数据里
		_hotspot(n, nm, Vector3.ZERO, n.get_meta("size", Vector3(0.3, 0.3, 0.3)), true)
	else:
		_hotspot(n, nm, Vector3.ZERO, Vector3(0.3, 0.3, 0.3))


## prop_<id>：关卡里的占位方块。模型资产表给了模型文件，就换成模型，底面中心对齐方块底面中心
func _swap_prop(n: Node3D, nm: String) -> void:
	var file: String = ContentDB.props.get(nm, {}).get("model", "")
	if file == "" or not ResourceLoader.exists(file):
		return
	var m: Node3D = (load(file) as PackedScene).instantiate()
	m.transform = n.transform
	if n is CSGBox3D:
		m.transform = n.transform * Transform3D(Basis(), Vector3(0, -n.size.y / 2, 0))
	m.visible = n.visible
	var parent := n.get_parent()
	parent.add_child(m)
	parent.move_child(m, n.get_index())
	for c in n.get_children():
		c.reparent(m, true)
	parent.remove_child(n)
	n.queue_free()
	m.name = nm
	named[nm] = m


## 光源放在灯具模型里（灯笼、壁灯）时，灯罩和框架会把整面墙切成几道通顶的黑影。
## 包住投影光源的小模型（水平不到 1 米，即灯具本身）不投影；房间墙体等大模型不受影响。
func _unshadow_lamp_housings(r: Node) -> void:
	var lights: Array = []
	for n in _walk(r):
		if n is Light3D and n.shadow_enabled:
			lights.append(n.global_position)
	if lights.is_empty():
		return
	for n in _walk(r):
		if not n is GeometryInstance3D or n.cast_shadow == GeometryInstance3D.SHADOW_CASTING_SETTING_OFF:
			continue
		var box: AABB = n.global_transform * n.get_aabb()
		if box.size.x > 1.0 or box.size.z > 1.0:
			continue
		for p in lights:
			if box.grow(0.05).has_point(p):
				n.cast_shadow = GeometryInstance3D.SHADOW_CASTING_SETTING_OFF
				break


func _walk(n: Node) -> Array:
	var out: Array = [n]
	for c in n.get_children():
		out.append_array(_walk(c))
	return out


# ───────────── 模式与机位 ─────────────

func set_mode(mode: String, cam: String) -> void:
	if _camera_tween:
		_camera_tween.kill()
	if mode == "walk":
		if player.needs_spawn or not player.active:
			player.place(spawn[0], spawn[1])
		player.activate()
		return
	player.deactivate()
	shot_cam.current = true
	shot_cam.environment = null
	shot_cam.near = 0.05
	var key := cam if markers.has(cam) else ""
	if key == "" and not markers.is_empty():
		key = markers.keys()[0]
	if key == "":
		shot_cam.position = Vector3(0, 1.6, 1.5)
		shot_cam.look_at(Vector3(0, 1.0, 0))
		return
	var m: Array = markers[key]
	var target := Transform3D(Basis(), m[0]).looking_at(m[1])
	var fov: float = m[2] if m.size() > 2 else 45.0
	shot_cam.environment = m[3] if m.size() > 3 else null
	shot_cam.near = m[4] if m.size() > 4 else 0.05
	if _cam_key != "" and _cam_key != key and not Director.autoplay:
		_camera_tween = create_tween().set_parallel().set_trans(Tween.TRANS_SINE).set_ease(Tween.EASE_IN_OUT)
		_camera_tween.tween_property(shot_cam, "global_transform", target, 1.2)
		_camera_tween.tween_property(shot_cam, "fov", fov, 1.2)
	else:
		shot_cam.global_transform = target
		shot_cam.fov = fov
	_cam_key = key


func highlight_hotspots(ids: Array) -> void:
	active_hotspots = ids.duplicate()
	for id in hotspot_nodes:
		var mi: MeshInstance3D = hotspot_nodes[id].get_child(1)
		(mi.material_override as StandardMaterial3D).emission_energy_multiplier = 0.6 if ids.has(id) else 0.0
		if hotspot_nodes[id].has_meta("from_model"):
			mi.visible = ids.has(id)


func set_frozen(b: bool) -> void:
	if player:
		player.frozen = b


# ───────────── 渗漏、声音、事件 ─────────────

## L3 起，房间表面换成白模网格材质（docs/02 第 4 节）
func apply_leak(level: int) -> void:
	for mi in _surfaces:
		if not is_instance_valid(mi):
			continue
		mi.material_override = _leak_mat if level >= 3 else _orig_mats.get(mi)
	_env.environment.fog_light_color = Color("#d8d6d0") if level >= 3 else Color("#0b0b10")


## 按声音列播放一串声音（写法见 actions.gd 的 parse_sounds）：立刻、延迟、停掉循环
func play_sounds(spec: String) -> void:
	for s in Actions.parse_sounds(spec):
		if s["stop"]:
			stop_loop(s["id"])
		elif s["delay"] > 0:
			get_tree().create_timer(s["delay"]).timeout.connect(play_sound.bind(s["id"]))
		else:
			play_sound(s["id"])


## 当前房间的脚步声（脚步表 content/audio/footsteps.csv；没写的房间用木地板）
func footstep_sound() -> String:
	return String(ContentDB.footsteps.get(current_id, {}).get("sound", "footstep_wood"))


## 按音效表播放：文件放在 res://audio/，音量与是否循环由表决定；还没有文件的声音保持静音
func play_sound(id: String) -> void:
	if id == "" or id == "silence":
		return
	var row: Dictionary = ContentDB.sounds.get(id, {})
	var file: String = row.get("file", "")
	var path := "res://audio/" + file
	if file == "" or not ResourceLoader.exists(path):
		_missing_sounds[id] = true
		return
	var stream: AudioStream = load(path)
	var loop: bool = row.get("loop", "否") == "是"
	if loop:
		if _loops.has(id):
			return
		if stream is AudioStreamOggVorbis or stream is AudioStreamMP3:
			stream.loop = true
		elif stream is AudioStreamWAV:
			stream.loop_mode = AudioStreamWAV.LOOP_FORWARD
	var p := AudioStreamPlayer.new()
	p.stream = stream
	p.volume_db = float(row.get("volume_db", "0")) if str(row.get("volume_db", "")).is_valid_float() else 0.0
	if id.begins_with("footstep_"):
		p.pitch_scale = randf_range(0.92, 1.08)  # 每一步略有不同，不像复读
	add_child(p)
	p.play()
	if loop:
		_loops[id] = p
	else:
		p.finished.connect(p.queue_free)


## 配乐：跨镜头、跨房间一直放，直到 music(关闭) 或换成另一首；换房间不停
func play_music(id: String, fade := 1.5) -> void:
	if id == "" or id == "关闭":
		stop_music(fade)
		return
	if id == _music_id and is_instance_valid(_music):
		return
	stop_music(fade)
	var row: Dictionary = ContentDB.music.get(id, {})
	var path := "res://audio/music/" + String(row.get("file", ""))
	if row.is_empty() or not ResourceLoader.exists(path):
		push_warning("配乐“%s”没有文件，静音" % id)
		return
	var stream: AudioStream = load(path)
	if stream is AudioStreamOggVorbis or stream is AudioStreamMP3:
		stream.loop = row.get("loop", "是") != "否"  # 配乐表 loop 列：否 = 只放一遍（冲洗、尾声）
	var target := float(row.get("volume_db", "0")) if str(row.get("volume_db", "")).is_valid_float() else 0.0
	var p := AudioStreamPlayer.new()
	p.stream = stream
	p.volume_db = -60.0 if fade > 0 else target
	add_child(p)
	p.play()
	if fade > 0:
		create_tween().tween_property(p, "volume_db", target, fade)
	_music = p
	_music_id = id


func stop_music(fade := 1.5) -> void:
	if is_instance_valid(_music):
		var p := _music
		if fade > 0:
			var tw := create_tween()
			tw.tween_property(p, "volume_db", -60.0, fade)
			tw.tween_callback(p.queue_free)
		else:
			p.queue_free()
	_music = null
	_music_id = ""


func stop_loop(id: String) -> void:
	if _loops.has(id):
		if is_instance_valid(_loops[id]):
			_loops[id].queue_free()
		_loops.erase(id)


## 循环声渐弱后停掉
func fade_loop(id: String, sec: float) -> void:
	if not _loops.has(id) or not is_instance_valid(_loops[id]):
		return
	var p: AudioStreamPlayer = _loops[id]
	_loops.erase(id)
	var tw := create_tween()
	tw.tween_property(p, "volume_db", -60.0, sec)
	tw.tween_callback(p.queue_free)


## 换房间时停掉上一个房间的循环声
func stop_loops() -> void:
	for p in _loops.values():
		if is_instance_valid(p):
			p.queue_free()
	_loops.clear()
