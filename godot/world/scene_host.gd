extends Node3D
## 场景宿主：按场景 id 搭建房间，管理机位、热区、渗漏材质与声音。
## 房间以人工在 Godot 里搭的关卡场景 res://levels/<房间id>.tscn 为准；还没搭的房间暂用灰盒（房间布局表）。
## 关卡场景的命名约定见 docs/09-团队协作与任务派发.md 第 5 节：
##   spawn 出生点；cam_<机位> 机位（Camera3D）；hs_<id> 可检查物件；chr_<人名> 人物站位；prop_<id> 小物件占位

const HOTSPOT_LAYER := 2
const Actions := preload("res://core/actions.gd")
const Look := preload("res://world/look.gd")
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
## 当前单独加载的关卡（不在大地图里）自带的画面环境
var _level_env: Environment = null
var _cam_key := ""
var _camera_tween: Tween
var _missing_sounds := {}
## 能开关的门：门扇上导入时生成的 StaticBody3D -> {leaf, closed}（closed = 关着时的朝向，第一次开门时找）
var doors := {}
var _switch_lit := false       # 开关现在描不描边（玩家自由行走时描）
var _loops := {}
var _music: AudioStreamPlayer
var _music_id := ""
var _hovered := ""
var _outline_mat := _make_outline(Color(1.0, 0.82, 0.5, 0.55), 0.008)
var _outline_hover := _make_outline(Color(1.0, 0.9, 0.7, 1.0), 0.014)
var _outline_box := _make_outline(Color(0, 0, 0, 0), 0.0)


func _ready() -> void:
	shot_cam = Camera3D.new()
	shot_cam.fov = 45
	add_child(shot_cam)
	_env = WorldEnvironment.new()
	_env.environment = _make_env()
	add_child(_env)
	_leak_mat = ShaderMaterial.new()
	_leak_mat.shader = load("res://shaders/leak_white.gdshader")
	var rain := preload("res://world/rain.gd").new()      # 雨声按天气与离窗远近自己放（world/rain.gd）
	rain.name = "雨声"
	rain.host = self
	add_child(rain)
	var amb := preload("res://world/ambience.gd").new()  # 灰尘、炉火的火星、室外的雨丝（world/ambience.gd）
	amb.name = "氛围粒子"
	amb.host = self
	amb.rain = rain
	add_child(amb)
	GameState.changed.connect(_on_state_changed)


## 换章时天气可能变了（入夜、下雨、起雾）：重新套一遍天光
func _on_state_changed() -> void:
	if not Look.preset_changed():
		return
	if current_id == MAP_ID:
		_apply_look(_focus)
	elif room:
		_env.environment = Look.env(_level_env) if _level_env else _make_env()
		if not Look.owns(_level_env):
			for n in _walk(room):
				if n is Light3D:
					Look.light(n)
		apply_leak(GameState.leak_level)


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
	# 庄园里有关卡场景的房间都在同一张大地图里：换房间只换“镜头所在的房间”，不重新加载
	if is_map_room(id):
		if current_id != MAP_ID:
			_enter_map()
		focus_room(id)
		return
	if id == current_id:
		return
	if _camera_tween:
		_camera_tween.kill()
	_cam_key = ""
	stop_loops()
	if current_id == MAP_ID:
		_stash_map()
	elif room:
		remove_child(room)
		room.queue_free()
	current_id = id
	_reset_state()
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
	# 庄园里的房间套共用的天光（world/look.gd）；灰盒仍用默认的暗环境
	_level_env = level_env
	Look.preset_changed()
	_env.environment = Look.env(level_env) if level_env else _make_env()
	if not Look.owns(level_env):
		for n in _walk(room):
			if n is Light3D:
				Look.light(n)
	apply_leak(GameState.leak_level)
	if player:
		player.needs_spawn = true


func _reset_state() -> void:
	markers.clear()
	doors.clear()
	named.clear()
	figures.clear()
	hotspot_nodes.clear()
	active_hotspots = []
	_surfaces.clear()
	_orig_mats.clear()
	_chr_nodes.clear()
	spawn = [Vector3.ZERO, 0.0]


# ───────────── 大地图 ─────────────
## 第 1 章起，白天在整座庄园里自由走动（《01》、《12》H17）。大地图 = 庄园外景 levels/manor.tscn
## + 每个房间的关卡场景里属于这个房间的部分（房间本身、状态层、灯光、接口）。房间都按原位摆，坐标通用，
## 所以空间仍然只以各关卡场景为准；关卡场景里为了构图放的庄园外壳和邻房（“庄园”“邻·*”）不进大地图。

const MAP_ID := "manor"
const MAP_ROOMS := ["hall", "dining", "seance", "archive", "child_room", "guest_room", "darkroom", "greenhouse", "garden"]

## 镜头所在的房间（机位、reveal、人物动作先在这里找）
var _focus := ""
## 玩家现在站在哪个房间（走动时按位置算；进了新房间发出 enter:<房间>）
var _player_room := ""
## 第 5 章回廊：当前的回廊节点（不在 current_id 里，单独挂）
var corridor: Node3D = null
var _room_box := {}
var _room_env := {}
var _room_spawn := {}
var _room_lights := {}
var _chr_nodes: Array = []
## 离开大地图（灰盒房间、火车）时把整张地图和它的索引收起来，回来时原样放回
var _map_stash := {}
## 自由探索时，哪些人站在哪里：["dining/康斯坦斯·塔尔博特", ...]；空数组 = 不在探索，按镜头所在房间显示
var _present: Array = []
var exploring := false


func _exit_tree() -> void:
	# 收起来的大地图不在场景树里，退出时要自己释放
	if _map_stash.has("room") and is_instance_valid(_map_stash["room"]):
		_map_stash["room"].free()
	_map_stash.clear()


static func is_map_room(id: String) -> bool:
	return id == MAP_ID or MAP_ROOMS.has(id)


func _enter_map() -> void:
	if room and current_id != MAP_ID:
		remove_child(room)
		room.queue_free()
	current_id = MAP_ID
	if not _map_stash.is_empty():
		room = _map_stash["room"]
		for k in ["markers", "doors", "named", "figures", "hotspot_nodes", "_surfaces", "_orig_mats", "_chr_nodes"]:
			set(k, _map_stash[k])
		add_child(room)
		var pos = _map_stash.get("player")
		_map_stash.clear()
		_player_room = ""
		if player and pos != null:
			player.global_transform = pos
			player.needs_spawn = false
		apply_leak(GameState.leak_level)
		return
	_reset_state()
	room = Node3D.new()
	room.name = "庄园大地图"
	add_child(room)
	var ext: Node3D = (load(ContentDB.level_path(MAP_ID)) as PackedScene).instantiate()
	var dup := ext.get_node_or_null("结构/房间")
	if dup:
		dup.get_parent().remove_child(dup)
		dup.free()
	room.add_child(ext)
	_adopt_level(ext, MAP_ID)
	_collect_room(MAP_ID, ext)
	for rid in MAP_ROOMS:
		var path := ContentDB.level_path(rid)
		if not ResourceLoader.exists(path):
			continue
		var lv: Node3D = (load(path) as PackedScene).instantiate()
		lv.name = rid
		var own: Node3D = null
		var st := lv.get_node_or_null("结构")
		if st:
			for c in st.get_children():
				var keep := String(c.name).begins_with("层·") or String(c.scene_file_path).ends_with("/room_%s.gltf" % rid)
				if keep and String(c.scene_file_path).ends_with("/room_%s.gltf" % rid):
					own = c
				if not keep:
					st.remove_child(c)
					c.free()
		room.add_child(lv)
		_adopt_level(lv, rid)
		_collect_room(rid, lv, own)
	apply_leak(GameState.leak_level)
	if player:
		player.needs_spawn = true
	# 室外的房间（花园百叶外侧）模型只有墙根一小块：范围扩到出生点周围，走到那里就算到了
	for rid in _room_box:
		var sp: Array = _room_spawn.get(rid, [])
		if not sp.is_empty() and not _room_box[rid].grow(0.05).has_point(sp[0] + Vector3(0, 0.9, 0)):
			_room_box[rid] = _room_box[rid].merge(AABB(sp[0] - Vector3(1.5, 0, 1.5), Vector3(3, 2.5, 3)))
	_add_practicals()
	_add_shafts()
	_add_room_probes()
	# 自查：每个房间的出生点要落在这个房间的范围里，否则“走进房间”的任务永远触发不了
	for rid in _room_spawn:
		if rid != MAP_ID and room_at(_room_spawn[rid][0]) != rid:
			push_warning("大地图：%s 的出生点被认成了 %s" % [rid, room_at(_room_spawn[rid][0])])


## 让灯具亮起来（docs/06 第 9 节）：壁灯、台灯、吊灯这些模型原来只是摆设，灯泡与灯罩不发光、身边也没有光。
## 按材质名（Look.PRACTICAL_GLOW）认出灯具，灯泡、灯罩换成发光的材质；附近 0.7 米内没有真灯的，补一盏不投影的暖色小灯，
## 挂在灯具模型下面（灯具在状态层里时跟着显隐），记进所在房间的灯（随天光表的 lamps 倍数变）。
## 自己管样子的房间（暗房、火车）不动。
func _add_practicals() -> void:
	var lights: Array = []
	for n in _walk(room):
		if n is Light3D:
			lights.append(n.global_position)
	for n in _walk(room):
		if not n is MeshInstance3D or n.mesh == null:
			continue
		var glow := AABB()
		var found := false
		for i in n.mesh.get_surface_count():
			var mat: Material = n.get_active_material(i)
			if mat == null or not Look.PRACTICAL_GLOW.has(mat.resource_name):
				continue
			var b := _surface_box(n.mesh, i)
			glow = b if not found else glow.merge(b)
			found = true
		if not found:
			continue
		var at: Vector3 = n.global_transform * glow.get_center()
		var rid := room_at(at - Vector3(0, 0.9, 0))   # room_at 按脚下算，灯在头顶：减回去，免得一楼吊灯算进二楼
		if Look.owns(_room_env.get(rid)):
			continue
		for i in n.mesh.get_surface_count():
			var mat: Material = n.get_active_material(i)
			if mat and Look.PRACTICAL_GLOW.has(mat.resource_name):
				n.set_surface_override_material(i, Look.glow_material(mat))
		n.cast_shadow = GeometryInstance3D.SHADOW_CASTING_SETTING_OFF
		var near := false
		for p in lights:
			if p.distance_to(at) < 0.7:
				near = true
				break
		if near:
			continue
		var l := OmniLight3D.new()
		l.name = "补光·" + String(n.name)
		l.light_color = Look.PRACTICAL_COLOR
		l.light_energy = Look.PRACTICAL_ENERGY
		l.omni_range = Look.PRACTICAL_RANGE
		l.shadow_enabled = false
		n.add_child(l)
		l.global_position = at
		l.set_meta("shadow_default", false)
		lights.append(at)
		if not _room_lights.has(rid):
			_room_lights[rid] = []
		_room_lights[rid].append(l)


## 灯的影子按离镜头的远近淡出（8 米起、4 米淡完），不再按“在不在这个房间”开关：跨门时影子不会突然出现、消失
static func _fade_lamp_shadows(l: Light3D) -> void:
	l.distance_fade_enabled = true
	l.distance_fade_begin = 40.0
	l.distance_fade_shadow = 8.0
	l.distance_fade_length = 4.0


## 房间的局部补光（docs/06 第 9 节）：引擎的环境光是全局的、墙挡不住，以前每个房间换一套环境来调明暗，跨门就跳。
## 实测（10-20）：只用共用环境，客房、门厅、餐厅、客厅的亮度和原来差不到几个百分点（屋里亮不亮主要看灯），
## 只有原来特意压暗的房间（房间机位环境的环境光 ÷ 共用值 0.5 小于 0.35，目前只有暗房 0.1）会变亮。
## 所以只给这种房间按自己的范围自动放一个 ReflectionProbe 压暗环境光；盒子比房间大一圈（过渡带落在墙里和门口），
## 门口 0.6 米内和外面平滑过渡。
## 房间环境开了体积雾的（暗房），换成只在这个房间里的 FogVolume。只在载入时拍一次，换天光时补拍。
const OUTDOOR_LOOK := ["garden", "greenhouse"]
var _probes: Array = []

func _add_room_probes() -> void:
	_probes.clear()
	var base := 0.5
	for rid in _room_box:
		if rid == MAP_ID or OUTDOOR_LOOK.has(rid):
			continue
		var e: Environment = _room_env.get(rid)
		var factor: float = (e.ambient_light_energy / base) if e else 1.0
		if factor >= 0.35:
			continue
		var box: AABB = _room_box[rid].grow(0.6)
		var p := ReflectionProbe.new()
		p.name = "局部补光·" + rid
		p.size = box.size
		p.interior = true
		p.box_projection = true
		p.blend_distance = 0.6
		p.update_mode = ReflectionProbe.UPDATE_ONCE
		p.ambient_mode = ReflectionProbe.AMBIENT_COLOR
		p.set_meta("factor", factor)
		if e and e.ambient_light_source == Environment.AMBIENT_SOURCE_COLOR:
			p.set_meta("tint", e.ambient_light_color)   # 房间环境自己写了环境光颜色的（暗房），沿用这个颜色
		room.add_child(p)
		p.global_position = box.get_center()
		_probes.append(p)
		if e and e.volumetric_fog_enabled:
			var fog := FogVolume.new()
			fog.name = "局部雾·" + rid
			fog.size = _room_box[rid].size - Vector3(0.2, 0.2, 0.2)
			var fm := FogMaterial.new()
			fm.density = e.volumetric_fog_density
			fm.albedo = e.volumetric_fog_albedo
			fm.edge_fade = 0.3
			fog.material = fm
			room.add_child(fog)
			fog.global_position = box.get_center()
	_update_room_probes()


func _update_room_probes() -> void:
	for p in _probes:
		if not is_instance_valid(p):
			continue
		var amb: Array = Look.probe_ambient(float(p.get_meta("factor")))
		p.ambient_color = p.get_meta("tint", amb[0])
		p.ambient_color_energy = amb[1]


## 假光柱（docs/06 第 9 节）：Look.SHAFT_ROOMS 里每扇窗前拉一束斜向屋里、向下的光，几乎不耗性能，
## 不受太阳方向和窗外树木影响。窗玻璃按 rain.gd 认的名字找，一扇窗一束；光到地面为止。
func _add_shafts() -> void:
	var rain_script: GDScript = load("res://world/rain.gd")
	var tilt := deg_to_rad(Look.SHAFT_TILT)
	for n in _walk(room):
		if not n is MeshInstance3D or not rain_script.GLASS_NAMES.has(String(n.name)) or n.mesh == null:
			continue
		for b: AABB in rain_script._panes(n):
			var c: Vector3 = b.get_center()
			var thin_x: bool = b.size.x < b.size.z
			var ax := Vector3.RIGHT if thin_x else Vector3.BACK
			var rid := ""
			var inward := Vector3.ZERO
			for sgn in [1.0, -1.0]:
				var r := room_at(c + ax * sgn * 0.4 - Vector3(0, 1.2, 0))
				if Look.SHAFT_ROOMS.has(r) and _room_box.has(r) and absf(_room_box[r].position.y - (c.y - b.size.y * 0.5)) < 1.6:
					rid = r
					inward = ax * sgn
			if rid == "":
				continue
			var half: Vector3 = b.size * 0.5
			var side := Vector3.BACK if thin_x else Vector3.RIGHT
			var w: float = half.z if thin_x else half.x
			var dir := (inward * cos(tilt) + Vector3.DOWN * sin(tilt)).normalized()
			var floor_y: float = _room_box[rid].position.y
			var length: float = (c.y + half.y - floor_y) / sin(tilt)
			var mi := MeshInstance3D.new()
			mi.name = "光柱·" + rid
			mi.mesh = Look.shaft_mesh(c + inward * 0.05, side, w, half.y, dir, length)
			mi.material_override = Look.shaft_material()
			mi.cast_shadow = GeometryInstance3D.SHADOW_CASTING_SETTING_OFF
			mi.add_to_group("no_leak")
			room.add_child(mi)


static func _surface_box(mesh: Mesh, i: int) -> AABB:
	var v: PackedVector3Array = mesh.surface_get_arrays(i)[Mesh.ARRAY_VERTEX]
	var b := AABB(v[0], Vector3.ZERO) if v.size() > 0 else AABB()
	for p in v:
		b = b.expand(p)
	return b


## 记下一个房间的范围（判断玩家在哪）、画面环境（机位带的环境）、灯
func _collect_room(rid: String, lv: Node, own: Node = null) -> void:
	if own:
		var first := true
		var box := AABB()
		for n in _walk(own):
			if n is MeshInstance3D:
				var b: AABB = n.global_transform * n.get_aabb()
				box = b if first else box.merge(b)
				first = false
		if not first:
			_room_box[rid] = box
	for n in _walk(lv):
		if n is Camera3D and n.environment and not _room_env.has(rid):
			_room_env[rid] = n.environment
		elif n is Light3D:
			n.set_meta("shadow_default", n.shadow_enabled)
			if n is DirectionalLight3D:
				n.set_meta("basis_default", n.global_basis)
				if rid != MAP_ID and not has_meta("room_sun_basis"):
					set_meta("room_sun_basis", n.global_basis)   # 房间里的太阳都朝同一个方向，按房间布的窗光
			else:
				_fade_lamp_shadows(n)
			if not _room_lights.has(rid):
				_room_lights[rid] = []
			_room_lights[rid].append(n)


func _stash_map() -> void:
	_map_stash = {"room": room, "markers": markers, "doors": doors, "named": named, "figures": figures,
		"hotspot_nodes": hotspot_nodes, "_surfaces": _surfaces, "_orig_mats": _orig_mats, "_chr_nodes": _chr_nodes,
		"player": player.global_transform if player else null}
	remove_child(room)
	room = null
	markers = {}
	doors = {}
	named = {}
	figures = {}
	hotspot_nodes = {}
	_surfaces = []
	_orig_mats = {}
	_chr_nodes = []
	active_hotspots = []


## 镜头切到大地图里的某个房间：机位、出生点、画面环境都按这个房间
func focus_room(rid: String) -> void:
	_focus = rid
	spawn = _room_spawn.get(rid, _room_spawn.get("guest_room", [Vector3.ZERO, 0.0]))
	_apply_look(rid)
	_apply_presence()
	_sync_switch_hums()


## 画面的样子。大地图里全庄园只有一套：一个共用环境、一个太阳（庄园外景的那盏，夜里用月光的方向，白天用房间里太阳的方向）、
## 所有灯都投影（离远了影子自己淡掉，见 _fade_lamp_shadows）；房间之间的明暗差别交给房间里的局部补光（_add_room_probes），
## 所以走过门口只有渐变，不会整屏跳。不在大地图里（火车、灰盒）时仍按那个房间的环境。
func _apply_look(rid: String) -> void:
	Look.preset_changed()
	if current_id != MAP_ID:
		var look := rid if _room_lights.has(rid) or _room_env.has(rid) else MAP_ID
		for r in _room_lights:
			for l in _room_lights[r]:
				if is_instance_valid(l) and not Look.owns(_room_env.get(r)):
					Look.light(l)
		_env.environment = Look.env(_room_env.get(look, _room_env.get(MAP_ID)))
		apply_leak(GameState.leak_level)
		return
	for r in _room_lights:
		for l in _room_lights[r]:
			if not is_instance_valid(l):
				continue
			Look.light(l)
			if l is DirectionalLight3D:
				l.visible = r == MAP_ID
				if r == MAP_ID:
					var night := String(Look.current().get("preset", "")) == "夜"
					l.global_basis = l.get_meta("basis_default") if night or not has_meta("room_sun_basis") else get_meta("room_sun_basis")
			else:
				l.shadow_enabled = l.get_meta("shadow_default", false)
	_env.environment = Look.shared_env()
	_update_room_probes()
	apply_leak(GameState.leak_level)


## 谁在画面里：探索时按当天的任务摆人；看镜头时只有镜头所在房间的人在
func _apply_presence() -> void:
	for c in _chr_nodes:
		if not is_instance_valid(c["node"]) or not c["default"]:
			continue
		var on: bool
		if exploring:
			on = _present.has(c["room"] + "/" + c["who"])
		else:
			on = c["room"] == _focus
		_set_present(c["node"], on)


## 玩家在哪个房间：包住玩家的房间里最小的那个；都不在 = 庄园外面
func room_at(p: Vector3) -> String:
	var best := MAP_ID
	var best_vol := INF
	for rid in _room_box:
		var b: AABB = _room_box[rid]
		if b.grow(0.05).has_point(p + Vector3(0, 0.9, 0)) and b.get_volume() < best_vol:
			best = rid
			best_vol = b.get_volume()
	return best


func _process(_dt: float) -> void:
	var walking: bool = player != null and player.active
	_keep_inside()
	if walking != _switch_lit:
		_switch_lit = walking
		paint_switches()
	if current_id != MAP_ID or not walking:
		return
	var r := room_at(player.global_position)
	if r == _player_room:
		return
	_player_room = r
	_focus = r
	_apply_look(r)
	_sync_switch_hums()
	Director.inspected.emit("enter:" + r)


# ───────────── 自由探索的目标 ─────────────

## 探索开始或回到探索：摆好当天的人，标出能交谈的人、能推的门，再加上要检查的物件
## targets：talk:人名@房间 / door:门的节点名 / hs_<id>；enter:<房间> 不用标，走进去就算
func set_explore(targets: Array, present: Array) -> void:
	exploring = true
	_present = present
	_apply_presence()
	var ids: Array = []
	for t in targets:
		var id := String(t)
		if id.begins_with("talk:"):
			var who := id.trim_prefix("talk:").get_slice("@", 0)
			var rid := id.get_slice("@", 1)
			var n: Node = named.get(rid + "/chr_" + who)
			if n and n.get_child_count() > 0:
				_register_target(id, n.get_child(0))
				ids.append(id)
			else:
				push_warning("任务目标找不到人：%s（%s 的关卡场景里要有 chr_%s）" % [id, rid, who])
		elif id.begins_with("door:"):
			var leaf: Node = named.get(id.trim_prefix("door:"))
			if leaf:
				var body: Node = null
				for c in leaf.get_children():
					if c is StaticBody3D:
						body = c
				if body:
					_register_target(id, body, [leaf])
					ids.append(id)
				else:
					push_warning("任务目标的门没有碰撞体：" + id)
			else:
				push_warning("任务目标找不到门：" + id)
		elif not id.begins_with("enter:"):
			ids.append(id)
	highlight_hotspots(ids)


func end_explore() -> void:
	exploring = false
	_present = []
	highlight_hotspots([])
	_apply_presence()


## 人和门不是热区，但用同一套：准星对着它、按 E 发出它的 id，描边也一样
func _register_target(id: String, body: Node, meshes: Array = []) -> void:
	body.set_meta("hotspot_id", id)
	if meshes.is_empty():
		for n in _walk(body):
			if n is GeometryInstance3D:
				meshes.append(n)
	body.set_meta("outline", meshes)
	hotspot_nodes[id] = body


## 准星提示的文字
func target_label(id: String) -> String:
	if id.begins_with("talk:"):
		return "交谈：" + id.trim_prefix("talk:").get_slice("@", 0)
	if id.begins_with("door:"):
		return "推门：" + id.trim_prefix("door:").get_slice("（", 0).get_slice("·", 1)
	var h: Dictionary = ContentDB.hotspots.get(id, {})
	var verb: String = h.get("verb", "")
	return (verb if verb != "" else "检查") + "：" + String(h.get("label", id))


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
func _figure(parent: Node3D, who: String, foot: Vector3, rid := "") -> Node3D:
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
				figures[(rid + "/" + who) if rid != "" else who] = n
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
	if shot_id == "":
		return
	var rooms: Array = MAP_ROOMS if current_id == MAP_ID else [current_id]
	for rid in rooms:
		var rows: Array = ContentDB.room_states.get(rid, [])
		var on: Array = ContentDB.room_layers(rid, shot_id)
		for r in rows:
			var nm := "层·" + String(r.get("layer", ""))
			var n = named.get(rid + "/" + nm, named.get(nm) if current_id != MAP_ID else null)
			if n is Node3D:
				_set_present(n, on.has(r["layer"]))


## 镜头表 reveal(名称) / conceal(名称)：显示或隐藏关卡里的某个节点（如终局的镜中人形）
## 让人物播放一个动作（idle / walk / talk / tap / sit）。who 可以写全名或台词里的简称（“吉迪恩”）。
## 不循环的动作（tap）播完自动回到 idle。找不到人物或动作时返回 false。
func figure_anim(who: String, anim: String) -> bool:
	var ap: AnimationPlayer = null
	# 大地图里人物的键是“房间/人名”：先找镜头所在房间里的那一个
	for pass_room in [_focus + "/", ""]:
		for k in figures:
			var bare := String(k).get_slice("/", 1) if String(k).contains("/") else String(k)
			if (pass_room == "" or String(k).begins_with(pass_room)) and (bare == who or bare.begins_with(who)):
				ap = figures[k]
				break
		if ap:
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
	var key := _focus + "/" + id
	if named.has(key) and is_instance_valid(named[key]):
		_set_present(named[key], on)
	elif named.has(id) and is_instance_valid(named[id]):
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
	for key in ["interaction_normal", "interaction_min_dot", "interaction_reach", "inspection_focus", "inspect_fov", "inspect_light"]:
		if parent.has_meta(key):
			a.set_meta(key, parent.get_meta(key))
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
func _adopt_level(r: Node, rid := "") -> void:
	var declared_hotspot := RegEx.new()
	declared_hotspot.compile("\\bhs_[a-z0-9_]+\\b")
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
			# 衣柜右门已按合页单独建模，但导入资源未生成碰撞。
			# 碰撞直接来自真实门板，既能按 E 开门，也会挡住柜内物品。
			if String(n.name).ends_with("衣柜右门"):
				var has_body: bool = n.get_children().any(func(child): return child is StaticBody3D)
				if not has_body:
					var body := StaticBody3D.new()
					body.name = "门板碰撞"
					var collision := CollisionShape3D.new()
					collision.shape = n.mesh.create_trimesh_shape()
					body.add_child(collision)
					n.add_child(body)
			for c in n.get_children():
				if c is StaticBody3D:
					c.set_meta("door", true)
					doors[c] = {"leaf": n}
					if String(n.name).ends_with("衣柜右门"):
						doors[c]["closed"] = n.rotation.y
						doors[c]["container"] = true
						n.set_meta("closed_yaw", n.rotation.y)
					# 能开的门在某几镜里也可以闩着（暗房温室侧门：序章当晚从里面闩上，T1）：门的说法表这一镜有话就推不开
					if ContentDB.door_lines.has(String(n.name)):
						c.set_meta("door_line", String(n.name))
						c.add_to_group("door_line")
		elif n is MeshInstance3D and ContentDB.door_lines.has(String(n.name)):
			# 打不开、但推了有一句话的门（门的说法表 doors.csv）：正门、序章里闩着的暗房门
			for c in n.get_children():
				if c is StaticBody3D:
					c.set_meta("door_line", String(n.name))
					c.add_to_group("door_line")
	for n in _walk(r):
		if not n is Node3D or n == r:
			continue
		var nm := String(n.name)
		if rid == "" or not named.has(nm):
			named[nm] = n
		if rid != "":
			named[rid + "/" + nm] = n
		if not n.visible:
			_set_present(n, false)
		if nm == "spawn":
			if rid == "":
				spawn = [n.global_position, n.global_rotation_degrees.y]
			else:
				_room_spawn[rid] = [n.global_position, n.global_rotation_degrees.y]
		elif nm.begins_with("cam_"):
			var fwd: Vector3 = -n.global_transform.basis.z
			var fov: float = n.fov if n is Camera3D else 45.0
			if n is Camera3D:
				n.current = false
			markers[nm.trim_prefix("cam_")] = [n.global_position, n.global_position + fwd, fov,
				n.environment if n is Camera3D else null, n.near if n is Camera3D else 0.05]
		elif nm.begins_with("hs_"):
			_hotspot_on(n, nm)
		elif nm.begins_with("sw_"):
			_bind_switch(n, nm.trim_prefix("sw_"), rid)
		elif nm.begins_with("chr_"):
			# 人形挂在站位节点下，面朝站位节点的 +z；reveal / conceal 用人名或 chr_人名都行
			var who := nm.trim_prefix("chr_")
			_figure(n, who, Vector3.ZERO, rid)
			if rid == "" or not named.has(who):
				named[who] = n
			if rid != "":
				named[rid + "/" + who] = n
				# 大地图里同一个人可能在几个房间都有站位：平时都不出现，由镜头所在的房间或当天的任务决定谁在哪里
				_chr_nodes.append({"room": rid, "who": who, "node": n, "default": n.visible})
	# 原模型已明确标注编号时，直接绑定真实网格；不重建空间或猜测摆放位置。
	# 多编号组合家具仍以关卡里的独立 Marker 为准，不能用整件家具替代两条线索。
	for n in _walk(r):
		if not n is MeshInstance3D:
			continue
		var matches := declared_hotspot.search_all(String(n.name))
		if matches.size() != 1:
			continue
		var id: String = matches[0].get_string()
		if hotspot_nodes.has(id) or not ContentDB.hotspots.has(id):
			continue
		if rid != "" and ContentDB.hotspots[id].get("scene", "") != rid:
			continue
		_hotspot_on(n, id)
	# 回廊这种自己搭空间、自带热区的关卡：挂在 r 下面、带 hotspot_id 的 Area3D 也要能选
	_bind_meta_hotspots(r)
	_bind_inspection_assets(r, rid)
	if hotspot_nodes.has("hs_con_sweater"):
		for body in doors:
			if doors[body].get("container", false):
				hotspot_nodes["hs_con_sweater"].set_meta("container_leaf", doors[body]["leaf"])
	_bind_outlines(r)


## 只在现有物件上接内容、原画位材质与热区；不生成或移动房间布局。
func _bind_inspection_assets(r: Node, rid: String) -> void:
	var nodes := {}
	for n in _walk(r):
		if n is MeshInstance3D:
			nodes[String(n.name)] = n
	for row in ContentDB.load_table("res://content/visual/inspections.csv"):
		var id: String = row.get("hotspot", "")
		var h: Dictionary = ContentDB.hotspots.get(id, {})
		if rid != "" and h.get("scene", "") != rid:
			continue
		var source: MeshInstance3D = nodes.get(row.get("mesh", ""))
		if not is_instance_valid(source):
			continue
		if row.get("replacement_asset", "") != "":
			preload("res://world/inspection_mesh.gd").replace(source, row["replacement_asset"])
		if row.get("part_material", "") != "":
			source = preload("res://world/inspection_mesh.gd").part(source, row["part_material"], "" if row.get("world_document", "") == "1" else row.get("asset", ""), row.get("asset_fit", "") == "native")
			if not is_instance_valid(source):
				continue
		# 部分原模型只有渲染网格。实体道具仍须挡住视线，不能选中它背后的线索。
		# 独立交互遮挡层不改变行走碰撞，形状来自该道具的真实三角面。
		if row.get("occlusion", "") == "solid" and not source.has_node("交互遮挡"):
			var occluder := StaticBody3D.new()
			occluder.name = "交互遮挡"
			occluder.collision_layer = 4
			occluder.collision_mask = 0
			occluder.set_meta("inspection_surface_for", id)
			var shape := CollisionShape3D.new()
			shape.shape = source.mesh.create_trimesh_shape()
			occluder.add_child(shape)
			source.add_child(occluder)
		if not hotspot_nodes.has(id):
			_hotspot_on(source, id)
		if row.get("world_document", "") == "1" and not source.has_meta("inspection_document"):
			var document: Node3D = load(row["asset"]).instantiate()
			document.position = source.mesh.get_aabb().get_center()
			var angles: PackedStringArray = row.get("world_rotation", "0,0,0").split(",")
			document.rotation_degrees = Vector3(float(angles[0]), float(angles[1]), float(angles[2]))
			source.add_child(document)
			# 原薄片仅保留已有热区与状态层；真实双面纸张接在同一个原位。
			source.layers = 0
			source.set_meta("inspection_document", document)
		var image: String = row.get("image", "")
		if image != "" and ResourceLoader.exists(image):
			for i in source.mesh.get_surface_count():
				var original := source.get_active_material(i)
				if original is StandardMaterial3D and original.resource_name.contains(row.get("material", "")):
					var material: StandardMaterial3D = original.duplicate()
					material.albedo_texture = load(image)
					source.set_surface_override_material(i, material)
		var layer: String = row.get("layer", "")
		if layer != "":
			named[(rid + "/" if rid != "" else "") + "层·" + layer] = source


## 关卡里手工放的 Area3D（名字 hs_、set_meta("hotspot_id")）：直接当热区用，不做描边
func _bind_meta_hotspots(r: Node) -> void:
	for n in _walk(r):
		if n is Area3D and n.has_meta("hotspot_id"):
			var id: String = n.get_meta("hotspot_id")
			hotspot_nodes[id] = n
			n.collision_layer = 1 << (HOTSPOT_LAYER - 1)
			n.collision_mask = 0


# ───────────── 灯的开关 ─────────────

## sw_<层名>：墙上的电灯开关，玩家按 E 打开 / 关上同一房间的“层·<层名>”（例如暗房的 sw_红灯 → 层·红灯）。
## 开关节点上可写 metadata/hum = 音效编号：灯亮着、玩家在这个房间时一直响（红灯的嗡鸣）。
## 换镜头时房间状态表照样会把层设回表里的样子。
func _bind_switch(n: Node3D, layer: String, rid: String) -> void:
	var body := StaticBody3D.new()
	body.collision_layer = 1 << (HOTSPOT_LAYER - 1)
	body.collision_mask = 0
	var shape := CollisionShape3D.new()
	var box := BoxShape3D.new()
	box.size = n.get_meta("size", Vector3(0.2, 0.24, 0.12))   # 比开关面板大一圈，好瞄
	shape.shape = box
	body.add_child(shape)
	n.add_child(body)
	body.set_meta("switch", (rid + "/" if rid != "" else "") + "层·" + layer)
	body.set_meta("switch_name", layer)
	body.set_meta("switch_room", rid)
	body.set_meta("hum", n.get_meta("hum", ""))
	body.add_to_group("light_switch")


## 玩家自由行走时，开关和要检查的物件一样描一圈边（暗房进门是黑的，不描边找不到）；准星对着时加粗
func paint_switches(hovered: Node = null) -> void:
	for b in get_tree().get_nodes_in_group("light_switch"):
		var g = b.get_parent()
		if g is GeometryInstance3D:
			g.material_overlay = (_outline_hover if b == hovered else _outline_mat) if _switch_lit else null


func switch_is_on(body: Node) -> bool:
	var n = named.get(String(body.get_meta("switch", "")))
	return n is Node3D and n.visible


## 准星对着开关时的提示：“开灯：红灯” / “关灯：红灯”
func switch_label(body: Node) -> String:
	return ("关灯：" if switch_is_on(body) else "开灯：") + String(body.get_meta("switch_name", ""))


func toggle_switch(body: Node) -> void:
	var n = named.get(String(body.get_meta("switch", "")))
	if not n is Node3D:
		return
	_set_present(n, not n.visible)
	play_sound("light_switch")
	_sync_switch_hums()


## 开着的灯在玩家所在的房间里嗡嗡响，离开房间或关灯就停
func _sync_switch_hums() -> void:
	for b in get_tree().get_nodes_in_group("light_switch"):
		var hum := String(b.get_meta("hum", ""))
		if hum == "":
			continue
		var here: bool = String(b.get_meta("switch_room", "")) in ["", _focus]
		if here and switch_is_on(b):
			if not _loops.has(hum):
				play_sound(hum)
		else:
			stop_loop(hum)


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


## 推打不开的门：这一镜有话说就返回那句话，没有就是空的（准星不提示）
func door_line(body: Node) -> String:
	return ContentDB.door_line(String(body.get_meta("door_line", "")), GameState.shot) if is_instance_valid(body) and body.is_visible_in_tree() else ""


func door_line_label(body: Node) -> String:
	return "推门：" + String(body.get_meta("door_line", "")).get_slice("（", 0).get_slice("·", 1)


func door_label(body: Node) -> String:
	var container: bool = doors.get(body, {}).get("container", false)
	var name_text := String(doors.get(body, {}).get("leaf", body).name)
	var label := name_text.get_slice("·", 1) if name_text.contains("·") else name_text
	return ("关门：" if door_is_open(body) else "开门：") + ("衣柜" if container else label)


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
	return Vector2(maxf(absf(a.position.x), absf(a.end.x)), a.position.y + a.size.y * 0.45)


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
	var box: AABB = leaf.mesh.get_aabb() if leaf is MeshInstance3D else AABB()
	var side := Vector3.LEFT if absf(box.position.x) > absf(box.end.x) else Vector3.RIGHT
	return (parent_basis * Basis(Vector3.UP, yaw) * side).normalized()


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
## 光源常挂在灯罩下沿一点（餐叙区吊灯低于灯罩 9 cm，把灯罩投成天花板上一大块黑影），所以盒子放宽 0.3 米。
## 名字带“灯”的小模型（壁灯、台灯、吊灯）本身是发光的东西，也不投影（餐厅壁灯的灯罩被吊灯投到墙上，像一团黑影）。
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
		if String(n.name).contains("灯"):
			n.cast_shadow = GeometryInstance3D.SHADOW_CASTING_SETTING_OFF
			continue
		for p in lights:
			if box.grow(0.3).has_point(p):
				n.cast_shadow = GeometryInstance3D.SHADOW_CASTING_SETTING_OFF
				break


func _walk(n: Node) -> Array:
	var out: Array = [n]
	for c in n.get_children():
		out.append_array(_walk(c))
	return out


# ───────────── 模式与机位 ─────────────

## 第 5 章：进入回廊（降灵会之后）。回廊自己是空间，走完发 done 给 Director。
func start_corridor() -> void:
	if corridor == null:
		corridor = preload("res://levels/ded_corridor.tscn").instantiate()
		corridor.name = "回廊"
		# 回廊是独立空间，挪到远离庄园的一张空地上，免得和大地图叠在一起
		corridor.position = Vector3(500, 0, 500)
		add_child(corridor)
	corridor.done.connect(_on_corridor_done, CONNECT_ONE_SHOT)
	await get_tree().process_frame
	# 回廊自带一套环境（暗、雾），换掉庄园的那一套
	if corridor.has_method("environment"):
		_env.environment = corridor.environment()
	# 切第一人称：镜头相机让位给玩家自己的相机
	player.activate()
	player.frozen = false
	active_hotspots = []
	hotspot_nodes.clear()
	_bind_meta_hotspots(corridor)
	Director.ui.set_cinematic(false)
	corridor.start(player)
	exploring = false


func _on_corridor_done() -> void:
	hotspot_nodes.clear()
	active_hotspots = []
	Director.corridor_done.emit()


## 玩家按 E 时先问回廊：它自己处理（敲门、坐第四把椅子）
func corridor_interact(id: String) -> bool:
	return corridor != null and corridor.running and corridor.interact(id)


func corridor_running() -> bool:
	return corridor != null and corridor.running


func corridor_hint() -> String:
	return corridor.current_hint if corridor != null and corridor.running else ""


func corridor_answer() -> void:
	if corridor != null and corridor.running:
		corridor.answer()


func corridor_answering() -> bool:
	return corridor != null and corridor.running and corridor.answering()


func set_mode(mode: String, cam: String) -> void:
	if _camera_tween:
		_camera_tween.kill()
	if mode == "walk":
		# 大地图里：自由探索时玩家从哪里来就站在哪里；按镜头走的行走镜头，玩家不在这个房间就送到房间的出生点
		var respawn: bool = player.needs_spawn or not player.active
		if current_id == MAP_ID and not player.needs_spawn:
			respawn = not exploring and _locked == "" and room_at(player.global_position) != _focus
		if respawn:
			player.place(spawn[0], spawn[1])
		# 从剧情机位回到玩家眼里：镜头平滑地回到玩家的视线，而不是一刀切回去（10-20）
		if not player.active and shot_cam.current and not respawn and not Director.autoplay \
				and shot_cam.global_position.distance_to(player.cam.global_position) < GLIDE_RANGE:
			_glide(shot_cam.global_transform, player.cam.global_transform, shot_cam.fov, player.cam.fov, 0.8)
			_camera_tween.tween_callback(player.activate)
			_cam_key = ""
			return
		player.activate()
		return
	# 从玩家眼里进剧情机位（交谈、坐到桌前）：从玩家的视线滑过去
	var from_eye: bool = player.active and not Director.autoplay
	var eye: Transform3D = player.cam.global_transform
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
	# 大地图里剧情机位也用共用环境（不切环境，镜头前后不跳）；火车这类单独的关卡仍用机位自己的环境
	shot_cam.environment = null if current_id == MAP_ID else (Look.env(m[3]) if m.size() > 3 and m[3] else null)
	shot_cam.near = m[4] if m.size() > 4 else 0.05
	if from_eye and eye.origin.distance_to(target.origin) < GLIDE_RANGE:
		_glide(eye, target, player.cam.fov, fov, 1.0)
	elif _cam_key != "" and _cam_key != key and not Director.autoplay:
		_camera_tween = create_tween().set_parallel().set_trans(Tween.TRANS_SINE).set_ease(Tween.EASE_IN_OUT)
		_camera_tween.tween_property(shot_cam, "global_transform", target, 1.2)
		_camera_tween.tween_property(shot_cam, "fov", fov, 1.2)
	else:
		shot_cam.global_transform = target
		shot_cam.fov = fov
	_focus_dof(target)
	_cam_key = key


## 玩家眼睛与剧情机位之间平滑过渡的最远距离：再远（换了房间）就直接切
const GLIDE_RANGE := 9.0

func _glide(from: Transform3D, to: Transform3D, fov_from: float, fov_to: float, sec: float) -> void:
	shot_cam.current = true
	shot_cam.global_transform = from
	shot_cam.fov = fov_from
	_camera_tween = create_tween().set_trans(Tween.TRANS_SINE).set_ease(Tween.EASE_IN_OUT)
	_camera_tween.set_parallel()
	_camera_tween.tween_property(shot_cam, "global_transform", to, sec)
	_camera_tween.tween_property(shot_cam, "fov", fov_to, sec)
	_camera_tween.set_parallel(false)


# ───────────── 回想：地面指引（docs/01 第 4 节） ─────────────

const Guide := preload("res://world/guide.gd")
var guide: Node3D

## 把任务的触发（talk:/enter:/door:/hs_）换成地面上的一个点，画出通往最近那个的路；没有可指的返回 false
func show_guide(ids: Array) -> bool:
	if current_id != MAP_ID or player == null or not player.active:
		return false
	if guide == null:
		guide = Guide.new()
		guide.name = "回想"
		guide.host = self
		add_child(guide)
	var pts: Array = []
	for id in ids:
		var p = target_position(String(id))
		if p != null:
			pts.append(p)
	return await guide.show_path(pts)


func target_position(id: String) -> Variant:
	if id.begins_with("talk:"):
		var n: Node3D = named.get(id.get_slice("@", 1) + "/chr_" + id.trim_prefix("talk:").get_slice("@", 0))
		return n.global_position if n else null
	if id.begins_with("door:"):
		var d: Node3D = named.get(id.trim_prefix("door:"))
		return d.global_position if d else null
	if id.begins_with("enter:"):
		var sp: Array = _room_spawn.get(id.trim_prefix("enter:"), [])
		return sp[0] if not sp.is_empty() else null
	var h: Node3D = hotspot_nodes.get(id)
	if h and is_instance_valid(h) and h.is_inside_tree():
		var g := h.global_position
		var q := PhysicsRayQueryParameters3D.create(g, g + Vector3.DOWN * 3.0, 1)
		var hit := get_world_3d().direct_space_state.intersect_ray(q)
		return hit["position"] if not hit.is_empty() else g
	return null


# ───────────── 客房：收尾、躺下、醒来（docs/01 第 4 节） ─────────────

## 回客房收尾时锁住这个房间：走出房间范围就被送回来，侦探说一句话
var _locked := ""
var _last_inside := Vector3.ZERO
var _lock_said := 0.0
## 床的朝向（床头在哪一头、从哪一边上下床），第一次用到时按床的模型算出来
var _bed := {}

func lock_room(rid: String) -> void:
	if _locked != rid and player:
		_last_inside = player.global_position
	_locked = rid


func unlock_room() -> void:
	_locked = ""


func room_locked() -> String:
	return _locked


func _keep_inside() -> void:
	if _locked == "" or not player or not player.active or player.frozen:
		return
	if room_at(player.global_position) == _locked:
		_last_inside = player.global_position
		return
	player.global_position = _last_inside
	player.velocity = Vector3.ZERO
	var now := Time.get_ticks_msec() / 1000.0
	if now - _lock_said > 4.0:
		_lock_said = now
		Director.ui.toast("今天就到这里。该把今天的东西理一理了。")


## 床：像人一样躺下去（10-20，用户：原来的动作不符合人体）——
## 走到床边、面朝床 → 转过身背对床 → 坐到床沿（视线降到坐高）→ 侧身仰躺，头落在床头的枕头上，看见天花板
func lie_down() -> void:
	var f := _bed_frame()
	if f.is_empty() or player == null:
		return
	var eye: Transform3D = player.cam.global_transform
	player.deactivate()
	_cam_free(eye)
	await _cam_path([
		[_bed_pose(f, "face_bed"), 1.1],
		[_bed_pose(f, "stand_out"), 0.7],
		[_bed_pose(f, "sit"), 0.9],
		[_bed_pose(f, "lean"), 0.8],
		[_bed_pose(f, "lie"), 1.1],
	])


## 醒来：眼睑闭着，仰躺在枕头上睁眼 → 撑起上身、把腿放下床，坐在床沿 → 站起来，交给玩家
func wake_up() -> void:
	show_scene("guest_room")
	var f := _bed_frame()
	if f.is_empty() or player == null:
		Director.ui.eyelids_set(1.0)
		return
	player.deactivate()
	var stand: Transform3D = _bed_pose(f, "stand_out")
	var fwd: Vector3 = -stand.basis.z
	player.place(stand.origin - Vector3.UP * player.EYE, rad_to_deg(atan2(-fwd.x, -fwd.z)))
	focus_room("guest_room")
	Director.ui.eyelids_set(0.0)
	_cam_free(_bed_pose(f, "lie"))
	await Director.ui.eyelids_open()
	await _cam_path([
		[_bed_pose(f, "lean"), 1.2],
		[_bed_pose(f, "sit"), 1.0],
		[_bed_pose(f, "sit_look"), 0.6],
		[player.cam.global_transform, 1.1],
	])
	_cam_key = ""
	player.activate()


func _cam_free(from: Transform3D) -> void:
	if _camera_tween:
		_camera_tween.kill()
	shot_cam.current = true
	shot_cam.environment = null
	shot_cam.near = 0.05
	shot_cam.attributes = null
	shot_cam.global_transform = from
	shot_cam.fov = player.cam.fov
	_cam_key = ""


## 一段接一段地移动镜头：位置直线过去、朝向平滑转过去（四元数插值，不会绕着视线打滚）
func _cam_path(steps: Array) -> void:
	var prev := shot_cam.global_transform
	_camera_tween = create_tween()
	for st in steps:
		var a := prev
		var b: Transform3D = st[0]
		_camera_tween.tween_method(func(k: float): shot_cam.global_transform = a.interpolate_with(b, k), 0.0, 1.0, st[1]) \
			.set_trans(Tween.TRANS_SINE).set_ease(Tween.EASE_IN_OUT)
		prev = b
	await _camera_tween.finished


## 床的框架：中心、床面高度、床头方向（沿床长）、上下床的那一边、半长、半宽、地面高度。
## 床的模型是“客房·床”开头的节点；模型原点在床头（Blender 里床头靠墙），所以原点在中心的哪一头，哪一头就是床头。
## 上下床的那一边：两边各往外打一条射线，空出来的那一边
func _bed_frame() -> Dictionary:
	if not _bed.is_empty():
		return _bed
	var hs: Node3D = hotspot_nodes.get("hs_bed")
	if hs == null:
		return {}
	var model: Node3D = null
	for k in named:
		var n = named[k]
		if String(k).begins_with("客房·床") and not String(k).begins_with("客房·床头") and n is Node3D and is_instance_valid(n):
			model = n
			break
	var box := AABB(hs.global_position - Vector3(1.0, 0.3, 0.45), Vector3(2.0, 0.6, 0.9))
	var origin := hs.global_position
	if model:
		var first := true
		for m in _walk(model):
			if m is MeshInstance3D:
				var bb: AABB = m.global_transform * m.get_aabb()
				box = bb if first else box.merge(bb)
				first = false
		origin = model.global_position
	var c := box.get_center()
	var along_x: bool = box.size.x >= box.size.z
	var axis := Vector3.RIGHT if along_x else Vector3.BACK
	var head := axis if (origin - c).dot(axis) >= 0.0 else -axis
	var side := Vector3.BACK if along_x else Vector3.RIGHT
	var half_len: float = (box.size.x if along_x else box.size.z) * 0.5
	var half_wid: float = (box.size.z if along_x else box.size.x) * 0.5
	var top := _bed_top(Vector3(c.x, box.end.y, c.z) + head * half_len * 0.2)
	var floor_y: float = player.global_position.y if player else box.position.y
	# 哪一边空着：从床面往两边各量 1.2 米
	var space := get_world_3d().direct_space_state
	var room_on := {}
	for sgn in [1.0, -1.0]:
		var from: Vector3 = Vector3(c.x, floor_y + 0.9, c.z) + side * sgn * (half_wid + 0.05)
		var q := PhysicsRayQueryParameters3D.create(from, from + side * sgn * 1.2, 1)
		if player:
			q.exclude = [player.get_rid()]
		var hit := space.intersect_ray(q)
		room_on[sgn] = from.distance_to(hit["position"]) if not hit.is_empty() else 1.2
	var out := side if room_on[1.0] >= room_on[-1.0] else -side
	# 地面：床边往下打一条射线（醒来时玩家还不在客房，不能用玩家的高度）
	var down := PhysicsRayQueryParameters3D.create(Vector3(c.x, top, c.z) + out * (half_wid + 0.4), Vector3(c.x, top - 3.0, c.z) + out * (half_wid + 0.4), 1)
	if player:
		down.exclude = [player.get_rid()]
	var fh := space.intersect_ray(down)
	if not fh.is_empty():
		floor_y = fh["position"].y
	_bed = {"c": Vector3(c.x, top, c.z), "head": head, "out": out, "len": half_len, "wid": half_wid, "floor": floor_y}
	return _bed


## 床边的几个姿势（镜头 = 眼睛）。坐高：床面上 0.72 米；躺下：头在枕头上，眼睛离床面 0.2 米
func _bed_pose(f: Dictionary, which: String) -> Transform3D:
	var c: Vector3 = f["c"]
	var head: Vector3 = f["head"]
	var out: Vector3 = f["out"]
	var edge: Vector3 = c + out * f["wid"] + head * f["len"] * 0.25   # 坐的地方：床沿，偏床头一点
	var eye_y: float = f["floor"] + player.EYE
	match which:
		"face_bed":
			var p: Vector3 = Vector3(edge.x, eye_y, edge.z) + out * 0.5
			return Transform3D(Basis.looking_at(-out - Vector3.UP * 0.45, Vector3.UP), p)
		"stand_out":
			var p: Vector3 = Vector3(edge.x, eye_y, edge.z) + out * 0.45
			return Transform3D(Basis.looking_at(out - Vector3.UP * 0.1, Vector3.UP), p)
		"sit":
			var p: Vector3 = edge - out * 0.12 + Vector3.UP * 0.72
			return Transform3D(Basis.looking_at(out - Vector3.UP * 0.3, Vector3.UP), p)
		"sit_look":
			var p: Vector3 = edge - out * 0.05 + Vector3.UP * 0.74
			return Transform3D(Basis.looking_at(out - Vector3.UP * 0.05, Vector3.UP), p)
		"lean":
			# 先往后仰、撑在手肘上（仍朝着屋里，视线抬向天花板）；转到枕头上是下一步
			var p: Vector3 = edge - out * 0.35 + Vector3.UP * 0.4
			return Transform3D(Basis.looking_at((Vector3.UP + out * 0.5).normalized(), Vector3.UP), p)
		"lie":
			# 仰躺：头在枕头上（离床头 0.32 米），视线朝上、略朝脚那头；画面的上方是床头
			var p: Vector3 = c + head * (f["len"] - 0.32) + Vector3.UP * 0.2
			return Transform3D(Basis.looking_at((Vector3.UP - head * 0.3).normalized(), head), p)
	return Transform3D()


## 床面的高度：从床的热区上方往下打一条射线
func _bed_top(p: Vector3) -> float:
	var q := PhysicsRayQueryParameters3D.create(p + Vector3.UP * 1.2, p + Vector3.DOWN * 1.5, 1)
	if player:
		q.exclude = [player.get_rid()]
	var hit := get_world_3d().direct_space_state.intersect_ray(q)
	return hit["position"].y if not hit.is_empty() else p.y + 0.1


## 剧情机位的景深：只给近景（镜头中线 2 米内碰到东西，如显影盘、桌面）加，焦点后面轻轻虚掉；
## 全景不加，免得站在后面的人被虚掉。自由行走的相机不加
func _focus_dof(t: Transform3D) -> void:
	if not shot_cam.attributes:
		shot_cam.attributes = CameraAttributesPractical.new()
	var a: CameraAttributesPractical = shot_cam.attributes
	var from := t.origin
	var q := PhysicsRayQueryParameters3D.create(from, from - t.basis.z * 30.0, 1)
	if player:
		q.exclude = [player.get_rid()]
	var hit := get_world_3d().direct_space_state.intersect_ray(q)
	var d: float = from.distance_to(hit["position"]) if not hit.is_empty() else 8.0
	a.dof_blur_far_enabled = d < 2.0
	a.dof_blur_far_distance = d + 0.4
	a.dof_blur_far_transition = 1.0
	a.dof_blur_amount = 0.08


func highlight_hotspots(ids: Array) -> void:
	active_hotspots = ids.duplicate()
	_hovered = ""
	for id in hotspot_nodes:
		_paint_hotspot(id)


## 准星对着的目标：描边加粗、变亮（player 调用；id 为空 = 没有对着任何目标）
func hover_hotspot(id: String) -> void:
	if id == _hovered:
		return
	var was := _hovered
	_hovered = id
	if hotspot_nodes.has(was):
		_paint_hotspot(was)
	if hotspot_nodes.has(id):
		_paint_hotspot(id)


## 指引时，物件模型本身描一圈暖色的边（模板描边，模型的共用材质不动）；找不到模型的热区才显示方块
func _paint_hotspot(id: String) -> void:
	var a: Node3D = hotspot_nodes[id]
	var on := active_hotspots.has(id)
	var meshes: Array = a.get_meta("outline", [])
	if not meshes.is_empty():
		for g in meshes:
			if is_instance_valid(g):
				g.material_overlay = (_outline_hover if id == _hovered else _outline_mat) if on else null
		return
	if a.get_child_count() < 2:
		# 回廊这种自己搭的热区：只有碰撞体，没有占位方块，不描边
		return
	var mi: MeshInstance3D = a.get_child(1)
	if mi == null or not mi is MeshInstance3D or mi.material_override == null:
		return
	if a.has_meta("from_model"):
		# 物件长在墙面这类大网格里（百叶）：只描出热区盒子的轮廓
		mi.material_override = _outline_box
		mi.material_overlay = (_outline_hover if id == _hovered else _outline_mat) if on else null
		mi.visible = on
		return
	(mi.material_override as StandardMaterial3D).emission_energy_multiplier = (1.0 if id == _hovered else 0.6) if on else 0.0


static func _make_outline(color: Color, thickness: float) -> StandardMaterial3D:
	var m := StandardMaterial3D.new()
	m.transparency = BaseMaterial3D.TRANSPARENCY_ALPHA
	m.albedo_color = Color(0, 0, 0, 0)
	m.shading_mode = BaseMaterial3D.SHADING_MODE_UNSHADED
	m.no_depth_test = false
	m.stencil_mode = BaseMaterial3D.STENCIL_MODE_OUTLINE
	m.stencil_color = color
	m.stencil_outline_thickness = thickness
	return m


## 热区（来自美术模型的）对应哪些网格：大半落在热区盒子里的小网格，或者占满热区盒子、又不比它大太多的网格（药品柜、显影盘）。
## 房间模块里每件家具是单独的网格，所以按位置就能认出来，不需要在表里登记。
func _bind_outlines(r: Node) -> void:
	var cands: Array = []
	for n in _walk(r):
		if n is GeometryInstance3D and not n is Label3D and n.is_visible_in_tree():
			var b: AABB = n.global_transform * n.get_aabb()
			if b.size.x < 3.0 and b.size.z < 3.0 and b.size.y < 3.0:
				cands.append([n, b])
	for id in hotspot_nodes:
		var a: Node3D = hotspot_nodes[id]
		if not a.has_meta("from_model") or not a.is_inside_tree():
			continue
		var cs: CollisionShape3D = a.get_child(0)
		var half: Vector3 = (cs.shape as BoxShape3D).size / 2
		var box: AABB = a.global_transform * AABB(-half, half * 2)
		box = box.grow(0.03)
		var hits: Array = []
		for c in cands:
			if c[0] == a.get_child(1) or a.is_ancestor_of(c[0]):
				continue
			var b: AABB = c[1]
			var inter := box.intersection(b)
			var vol := maxf(b.get_volume(), 1e-6)
			if inter.has_volume() and (inter.get_volume() / vol >= 0.5 or (inter.get_volume() / box.get_volume() >= 0.4 and vol <= box.get_volume() * 30.0)):
				hits.append(c[0])
			elif b.size.y < 0.02 and box.has_point(b.get_center()):
				hits.append(c[0])  # 纸、照片这类扁平的东西
		if not hits.is_empty():
			a.set_meta("outline", hits)


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
	Look.update_shafts()
	var calm := Look.fog_color() if _env.environment.has_meta("look") else Color("#0b0b10")
	_env.environment.fog_light_color = Color("#d8d6d0") if level >= 3 else calm


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
	var rid := _player_room if current_id == MAP_ID else current_id
	return String(ContentDB.footsteps.get(rid, {}).get("sound", "footstep_wood"))


## 按音效表播放：文件放在 res://audio/，音量与是否循环由表决定；还没有文件的声音保持静音
func play_sound(id: String) -> void:
	if id == "" or id == "silence":
		return
	if id.begins_with("rain_"):                           # 雨声由 world/rain.gd 按天气与离窗远近放，镜头表里写了也不重复放
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
