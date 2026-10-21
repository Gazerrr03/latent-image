extends Node
## 雨天的室内雨声只在窗边响；近于 0.8 m 为设定音量，远于 3.5 m 静音。下雨时窗玻璃上挂雨滴。
## 天气来自当前章日记；听音点沿用当前相机，探索时即玩家眼睛。

const NEAR := 0.8
const FAR := 3.5
const INDOOR_GLASS_DB := -8.0       # 玻璃上的近处雨滴收轻，避免盖住窗外雨和配乐。
const INDOOR_OUTSIDE_DB := -6.0     # 窗外小雨作为室内混合的底声。
const GLASS_NAMES := ["门窗_glass", "温室_玻璃", "温室_补玻璃"]
const OUTDOOR_ROOMS := ["manor", "garden"]
const RATE := 1.5

var host: Node
var _glass: Array = []
var _glass_root_id := 0
var _players := {}
var _amp := {"rain_night": 0.0, "rain_glass": 0.0}
var _weather_cache := {}
var _indoor_gain := 0.0
var _glass_meshes: Array = []
var _wet := false
var _drops: ShaderMaterial
var _outdoor_gain := 0.0


func _process(dt: float) -> void:
	_paint_glass(host != null and raining())
	var indoor := 0.0
	var outdoor := 0.0
	if host and raining():
		var cam := get_viewport().get_camera_3d()
		if cam:
			var p := cam.global_position
			if _outdoors(p):
				outdoor = 1.0
			else:
				indoor = _closeness(p)
	# 两条实录共享同一个距离淡入淡出，走近、走远时混合比例不变。
	_indoor_gain = move_toward(_indoor_gain, indoor, RATE * dt)
	_outdoor_gain = move_toward(_outdoor_gain, outdoor, RATE * dt)
	_amp["rain_glass"] = _indoor_gain * db_to_linear(INDOOR_GLASS_DB)
	_amp["rain_night"] = _outdoor_gain + _indoor_gain * db_to_linear(INDOOR_OUTSIDE_DB)
	for id in _amp:
		_apply(id, _amp[id])


func raining() -> bool:
	var row: Dictionary = ContentDB.shots.get(GameState.shot, {})
	var chapter := String(row.get("node", ""))
	if chapter == "":
		return false
	if not _weather_cache.has(chapter):
		var wet := false
		for line in ContentDB.lines.get("diary" + chapter.trim_prefix("C"), []):
			if String(line.get("speaker", "")) == "天气" and String(line.get("text", "")).contains("雨"):
				wet = true
		_weather_cache[chapter] = wet
	return _weather_cache[chapter]


func _outdoors(p: Vector3) -> bool:
	# 已提交版本按房间加载；大地图版本则按玩家实际所在房间判断。
	if not host.has_method("room_at"):
		return OUTDOOR_ROOMS.has(host.current_id)
	if host.current_id != "manor":
		return false
	# room_at 要脚下坐标，内部会再抬高 0.9 m；传眼睛位置会误判室外。
	var feet: Vector3 = host.player.global_position if host.player and host.player.active else p - Vector3(0, 1.6, 0)
	return OUTDOOR_ROOMS.has(host.room_at(feet))


func _closeness(p: Vector3) -> float:
	_refresh_glass()
	var distance := INF
	for box in _glass:
		distance = minf(distance, _aabb_dist(box, p))
	return 0.0 if distance == INF else 1.0 - smoothstep(NEAR, FAR, distance)


static func _aabb_dist(box: AABB, p: Vector3) -> float:
	return p.clamp(box.position, box.end).distance_to(p)


func _refresh_glass() -> void:
	var room: Node = host.room
	var rid := room.get_instance_id() if room else 0
	if rid == _glass_root_id:
		return
	_glass_root_id = rid
	_glass.clear()
	_glass_meshes.clear()
	_wet = false
	if room == null:
		return
	var stack: Array = [room]
	while not stack.is_empty():
		var node: Node = stack.pop_back()
		stack.append_array(node.get_children())
		if node is MeshInstance3D and GLASS_NAMES.has(String(node.name)) and node.mesh:
			_glass.append_array(_panes(node))
			_glass_meshes.append(node)


## 雨天给窗玻璃挂上雨滴（shaders/rain_glass.gdshader），不下雨时摘掉
func _paint_glass(wet: bool) -> void:
	if host == null:
		return
	_refresh_glass()
	if wet == _wet:
		return
	_wet = wet
	if not _drops:
		_drops = ShaderMaterial.new()
		_drops.shader = load("res://shaders/rain_glass.gdshader")
	for m in _glass_meshes:
		if is_instance_valid(m):
			m.material_overlay = _drops if wet else null


## 同一网格可能含有多扇窗，按相交的三角形包围盒分开，避免整面墙都被算成窗。
static func _panes(mesh_instance: MeshInstance3D) -> Array:
	var boxes: Array = []
	var xf := mesh_instance.global_transform
	for surface in mesh_instance.mesh.get_surface_count():
		var arrays := mesh_instance.mesh.surface_get_arrays(surface)
		var vertices: PackedVector3Array = arrays[Mesh.ARRAY_VERTEX]
		var indices: PackedInt32Array = arrays[Mesh.ARRAY_INDEX]
		var count := indices.size() if not indices.is_empty() else vertices.size()
		for triangle in range(0, count, 3):
			var first := xf * vertices[indices[triangle] if not indices.is_empty() else triangle]
			var box := AABB(first, Vector3.ZERO)
			for k in [1, 2]:
				box = box.expand(xf * vertices[indices[triangle + k] if not indices.is_empty() else triangle + k])
			boxes.append(box.grow(0.02))
	var merged := true
	while merged:
		merged = false
		var result: Array = []
		for box in boxes:
			var hit := false
			for i in result.size():
				if result[i].intersects(box):
					result[i] = result[i].merge(box)
					hit = true
					merged = true
					break
			if not hit:
				result.append(box)
		boxes = result
	return boxes


func _apply(id: String, amp: float) -> void:
	var player: AudioStreamPlayer = _players.get(id)
	if amp <= 0.001:
		if player:
			player.stop()
			player.queue_free()
			_players.erase(id)
		return
	if player == null:
		var row: Dictionary = ContentDB.sounds.get(id, {})
		var path := "res://audio/" + String(row.get("file", ""))
		if row.is_empty() or not ResourceLoader.exists(path):
			return
		var stream: AudioStream = load(path)
		if stream is AudioStreamOggVorbis or stream is AudioStreamMP3:
			stream.loop = true
		elif stream is AudioStreamWAV:
			stream.loop_mode = AudioStreamWAV.LOOP_FORWARD
		player = AudioStreamPlayer.new()
		player.stream = stream
		player.bus = "SFX" if AudioServer.get_bus_index("SFX") >= 0 else "Master"
		# 淡入音量必须在 play 之前设置，避免初次开播突然以默认音量响一下。
		player.volume_db = _base_volume(id) + linear_to_db(amp)
		add_child(player)
		player.play(randf() * maxf(stream.get_length() - 1.0, 0.0))
		_players[id] = player
	player.volume_db = _base_volume(id) + linear_to_db(amp)


func _base_volume(id: String) -> float:
	var value := str(ContentDB.sounds.get(id, {}).get("volume_db", ""))
	return float(value) if value.is_valid_float() else 0.0
