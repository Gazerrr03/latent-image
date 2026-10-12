extends Node3D
## 场景宿主：按场景 id 搭建房间（美术模型优先，否则用灰盒），管理机位、热区、渗漏材质与声音。
## 美术模型的命名约定见 docs/09-团队协作与任务派发.md 第 5 节：
##   hs_<id> 可检查物件；spawn 出生点；exit 出口；cam_<名称> 机位；guide_ 指引光；-col 碰撞（Godot 导入时处理）

const HOTSPOT_LAYER := 2
const GreyboxSpecs := preload("res://world/greybox_specs.gd")

var player: Node3D
var shot_cam: Camera3D
var current_id := ""
var room: Node3D
var markers := {}
var hotspot_nodes := {}
var spawn := [Vector3.ZERO, 0.0]
var _surfaces: Array = []
var _orig_mats := {}
var _leak_mat: ShaderMaterial
var _env: WorldEnvironment
var _cam_key := ""
var _missing_sounds := {}
var _audio := AudioStreamPlayer.new()


func _ready() -> void:
	shot_cam = Camera3D.new()
	shot_cam.fov = 45
	add_child(shot_cam)
	_env = WorldEnvironment.new()
	_env.environment = _make_env()
	add_child(_env)
	_leak_mat = ShaderMaterial.new()
	_leak_mat.shader = load("res://shaders/leak_white.gdshader")
	add_child(_audio)


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
	if room:
		remove_child(room)
		room.queue_free()
	markers.clear()
	hotspot_nodes.clear()
	_surfaces.clear()
	_orig_mats.clear()
	var model: String = ContentDB.scenes.get(id, {}).get("model", "")
	if model != "" and ResourceLoader.exists(model):
		room = (load(model) as PackedScene).instantiate()
		_adopt_model(room)
	else:
		room = _build_greybox(GreyboxSpecs.get_spec(id))
	add_child(room)
	apply_leak(GameState.leak_level)
	if player:
		player.needs_spawn = true


func _build_greybox(spec: Dictionary) -> Node3D:
	var r := Node3D.new()
	r.name = "Greybox"
	if spec.is_empty():
		push_warning("没有灰盒规格：" + current_id)
		spec = {"size": Vector3(4, 3, 4)}
	var s: Vector3 = spec["size"]
	var t := 0.1
	_box(r, "地面", Vector3(0, -t / 2, 0), Vector3(s.x, t, s.z), Color("#3a2c22"))
	_box(r, "天花", Vector3(0, s.y + t / 2, 0), Vector3(s.x, t, s.z), Color("#2a2826"))
	_box(r, "前墙", Vector3(0, s.y / 2, -s.z / 2 - t / 2), Vector3(s.x, s.y, t), Color("#3b3430"))
	_box(r, "后墙", Vector3(0, s.y / 2, s.z / 2 + t / 2), Vector3(s.x, s.y, t), Color("#3b3430"))
	_box(r, "左墙", Vector3(-s.x / 2 - t / 2, s.y / 2, 0), Vector3(t, s.y, s.z), Color("#3b3430"))
	_box(r, "右墙", Vector3(s.x / 2 + t / 2, s.y / 2, 0), Vector3(t, s.y, s.z), Color("#3b3430"))
	for p in spec.get("props", []):
		# 已被指认的人不再出现在场景里
		if GameState.accused.has(p["name"]):
			continue
		_box(r, p["name"], p["pos"], p["size"], p["color"])
	for id in spec.get("hotspots", {}):
		_hotspot(r, id, spec["hotspots"][id], Vector3(0.3, 0.3, 0.3))
	for l in spec.get("lights", []):
		var o := OmniLight3D.new()
		o.position = l[0]
		o.light_color = l[1]
		o.light_energy = l[2]
		o.omni_range = 6.0
		o.shadow_enabled = true
		r.add_child(o)
	markers = spec.get("markers", {}).duplicate()
	spawn = spec.get("spawn", [Vector3.ZERO, 0.0])
	return r


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


func _hotspot(parent: Node3D, id: String, pos: Vector3, size: Vector3) -> void:
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
	mi.material_override = m
	a.add_child(mi)
	parent.add_child(a)
	hotspot_nodes[id] = a


## 美术模型：按命名约定识别热区、出生点、机位
func _adopt_model(r: Node) -> void:
	for n in _walk(r):
		if not n is Node3D:
			continue
		var nm: String = n.name
		if nm.begins_with("hs_") and n is MeshInstance3D:
			var aabb: AABB = n.get_aabb()
			_hotspot(n, nm.trim_suffix("-col"), aabb.get_center(), aabb.size.max(Vector3(0.2, 0.2, 0.2)))
		elif nm == "spawn":
			spawn = [n.global_position, n.global_rotation_degrees.y]
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


func play_sound(id: String) -> void:
	if id == "":
		return
	for ext in [".ogg", ".wav", ".mp3"]:
		var p: String = "res://audio/" + id + ext
		if ResourceLoader.exists(p):
			_audio.stream = load(p)
			_audio.play()
			return
	_missing_sounds[id] = true


## 被指认者：变成白模后消失（N5-03 的表现；N2 时同样适用）
func on_accused(who: String) -> void:
	if room == null:
		return
	var body := room.find_child(who, true, false)
	if body == null:
		return
	var mi: MeshInstance3D = body.get_child(0)
	mi.material_override = _leak_mat
	if Director.autoplay:
		body.queue_free()
		return
	var t := create_tween()
	t.tween_interval(1.0)
	t.tween_callback(body.queue_free)
