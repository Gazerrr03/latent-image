extends Node3D
## 场景宿主：按场景 id 搭建房间（美术模型优先，否则用灰盒），管理机位、热区、渗漏材质与声音。
## 美术模型的命名约定见 docs/09-团队协作与任务派发.md 第 5 节：
##   hs_<id> 可检查物件；spawn 出生点；exit 出口；cam_<名称> 机位；guide_ 指引光；-col 碰撞（Godot 导入时处理）

const HOTSPOT_LAYER := 2

var player: Node3D
var shot_cam: Camera3D
var current_id := ""
var room: Node3D
var markers := {}
## 布局表里有名字的东西：名称 -> 节点（reveal / conceal 用）
var named := {}
var hotspot_nodes := {}
var spawn := [Vector3.ZERO, 0.0]
var _surfaces: Array = []
var _orig_mats := {}
var _leak_mat: ShaderMaterial
var _env: WorldEnvironment
var _cam_key := ""
## 当前美术模型里有没有 spawn（没有就用布局表的出生点）
var _model_spawn := false
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
	var model: String = ContentDB.scenes.get(id, {}).get("model", "")
	if model != "" and ResourceLoader.exists(model):
		room = (load(model) as PackedScene).instantiate()
		_adopt_model(room)
		# 美术模型只提供房间本身；人物、灯光，以及模型里没有的机位、物件、出生点仍按布局表补上
		_apply_layout(room, id, true)
	else:
		room = _build_greybox(id)
	add_child(room)
	apply_leak(GameState.leak_level)
	if player:
		player.needs_spawn = true


## 灰盒：按房间登记表（尺寸）与房间布局表（家具、可检查物件、机位、灯光、出生点）搭出房间。
## 填表说明见 docs/填表说明/1.4-空间与地图.md
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
	_apply_layout(r, id, false)
	return r


## 布局表的各行（家具、人物、可检查物件、机位、灯光、出生点）。
## model_mode = true 时房间来自美术模型：跳过家具，模型里已有的机位、物件、出生点以模型为准
func _apply_layout(r: Node3D, id: String, model_mode: bool) -> void:
	for row in ContentDB.layout.get(id, []):
		var p := _vec(row, "x", "y", "z")
		var size := _vec(row, "w", "h", "d")
		var look := _vec(row, "look_x", "look_y", "look_z")
		var before := r.get_child_count()
		match row.get("type", ""):
			"家具":
				if model_mode:
					continue
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
				# 人物在这个房间的站位；被指认过的人不再出现
				if not GameState.accused.has(row["id"]):
					_figure(r, row["id"], p)
			"可检查物件":
				if model_mode and hotspot_nodes.has(row["id"]):
					continue
				_hotspot(r, row["id"], p, size if size != Vector3.ZERO else Vector3(0.3, 0.3, 0.3))
			"机位":
				if model_mode and markers.has(row["id"]):
					continue
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
				if model_mode and _model_spawn:
					continue
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
		if c.get("room", "") != id or GameState.accused.has(c["name"]) or named.has(c["name"]):
			continue
		named[c["name"]] = _figure(r, c["name"], _vec(c, "x", "y", "z"))


## 灰盒人形：身体 + 头 + 眼部处理（《04》第 11 节：除侦探外，所有人的眼睛都被遮住）。
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
		"丝巾":
			_mesh(root, Vector3(0, eye_y, 0), Vector3(head * 0.95, 0.075, head * 1.0), ec)
			_mesh(root, Vector3(head * 0.32, eye_y - 0.05, -head * 0.5), Vector3(0.06, 0.12, 0.03), ec)
		"遮光帽":
			_mesh(root, Vector3(0, eye_y + 0.035, head * 0.38), Vector3(head * 1.05, 0.025, head * 0.75), ec)
			_mesh(root, Vector3(0, eye_y + 0.07, 0), Vector3(head * 0.9, 0.03, head * 0.92), ec)
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


## 镜头表 reveal(名称) / conceal(名称)：显示或隐藏布局表里的某样东西（如终局的镜中人形）
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


## 美术模型：按命名约定识别热区、出生点、机位
func _adopt_model(r: Node) -> void:
	_model_spawn = false
	for n in _walk(r):
		if not n is Node3D:
			continue
		var nm: String = n.name
		if nm.begins_with("hs_") and n is MeshInstance3D:
			var aabb: AABB = n.get_aabb()
			_hotspot(n, nm.trim_suffix("-col"), aabb.get_center(), aabb.size.max(Vector3(0.05, 0.05, 0.05)), true)
		elif nm == "spawn":
			spawn = [n.global_position, n.global_rotation_degrees.y]
			_model_spawn = true
		elif nm.begins_with("cam_"):
			var fwd: Vector3 = -n.global_transform.basis.z
			markers[nm.trim_prefix("cam_")] = [n.global_position, n.global_position + fwd]
		if n is MeshInstance3D:
			_surfaces.append(n)
			_orig_mats[n] = n.material_override


func _walk(n: Node) -> Array:
	var out: Array = [n]
	for c in n.get_children():
		out.append_array(_walk(c))
	return out


# ───────────── 模式与机位 ─────────────

func set_mode(mode: String, cam: String) -> void:
	if mode == "walk":
		if player.needs_spawn or not player.active:
			player.place(spawn[0], spawn[1])
		player.activate()
		return
	player.deactivate()
	shot_cam.current = true
	var key := cam if markers.has(cam) else ""
	if key == "" and not markers.is_empty():
		key = markers.keys()[0]
	if key == "":
		shot_cam.position = Vector3(0, 1.6, 1.5)
		shot_cam.look_at(Vector3(0, 1.0, 0))
		return
	var m: Array = markers[key]
	var target := Transform3D(Basis(), m[0]).looking_at(m[1])
	if _cam_key != "" and _cam_key != key and not Director.autoplay:
		create_tween().tween_property(shot_cam, "global_transform", target, 1.2).set_trans(Tween.TRANS_SINE)
	else:
		shot_cam.global_transform = target
	_cam_key = key


func highlight_hotspots(ids: Array) -> void:
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


## 被指认者：变成白模后消失（N5-03 的表现；N2 时同样适用）
func on_accused(who: String) -> void:
	if room == null:
		return
	var body := room.find_child(who, true, false)
	if body == null:
		return
	# 先变成白色网格人形，片刻后消失（N5-03）
	for n in _walk(body):
		if n is MeshInstance3D:
			n.material_override = _leak_mat
	if Director.autoplay:
		body.queue_free()
		return
	var t := create_tween()
	t.tween_interval(1.0)
	t.tween_callback(body.queue_free)
