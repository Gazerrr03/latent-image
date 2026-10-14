extends Node3D
## 场景宿主：按场景 id 搭建房间，管理机位、热区、渗漏材质与声音。
## 房间以人工在 Godot 里搭的关卡场景 res://levels/<房间id>.tscn 为准；还没搭的房间暂用灰盒（房间布局表）。
## 关卡场景的命名约定见 docs/09-团队协作与任务派发.md 第 5 节：
##   spawn 出生点；cam_<机位> 机位（Camera3D）；hs_<id> 可检查物件；chr_<人名> 人物站位；prop_<id> 小物件占位

const HOTSPOT_LAYER := 2
const PAD := Vector3(0.04, 0.04, 0.04)

var player: Node3D
var shot_cam: Camera3D
var current_id := ""
var room: Node3D
var markers := {}
## 有名字的东西：名称 -> 节点（reveal / conceal 用）
var named := {}
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
var _loops := {}


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
	named.clear()
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


## 镜头表 reveal(名称) / conceal(名称)：显示或隐藏关卡里的某个节点（如终局的镜中人形）
func set_shown(id: String, on: bool) -> void:
	if named.has(id) and is_instance_valid(named[id]):
		named[id].visible = on
	else:
		push_warning("当前房间里没有：" + id)


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
	for n in _walk(r):
		if not n is Node3D or n == r:
			continue
		var nm := String(n.name)
		named[nm] = n
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


## hs_<id>：网格或方块本身就是物件的样子，热区比它略大一圈（准星先碰到热区）；空节点就放一个默认大小的高亮方块
func _hotspot_on(n: Node3D, nm: String) -> void:
	if n is MeshInstance3D and n.mesh:
		var aabb: AABB = n.mesh.get_aabb()
		_hotspot(n, nm, aabb.get_center(), aabb.size.max(Vector3(0.05, 0.05, 0.05)) + PAD, true)
	elif n is CSGBox3D:
		_hotspot(n, nm, Vector3.ZERO, n.size + PAD, true)
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
	add_child(p)
	p.play()
	if loop:
		_loops[id] = p
	else:
		p.finished.connect(p.queue_free)


## 换房间时停掉上一个房间的循环声
func stop_loops() -> void:
	for p in _loops.values():
		if is_instance_valid(p):
			p.queue_free()
	_loops.clear()
