extends Node3D
## 第 5 章“回廊”：降灵会之后的神游空间。
## 玩法“你就是唱针”：留声机的声音只在玩家走动时才响，停下就停，往回走就倒放；
## 走过尽头的门回到起点，进入下一层。设计见 docs/关卡/ded_corridor.md。
##
## 空间在代码里搭（用户还没在编辑器里搭正式场景）。以后换成 levels/ded_corridor.tscn，
## 只要节点名保持不变：spawn / door_end / path_0..path_2 / layer_<n>。
## 每层的内容在 content/story/corridor.csv，代码不写死。

const SEG_A := 8.0          # 第一段：从起点沿 -z
const SEG_B := 6.0          # 左转后沿 -x（最长；每圈按表里的 seg_b 截短，唱片越放越靠里）
const PATH_LEN := SEG_A + SEG_B
const LANE := 2.2
const STEP := 0.7
const SPEED := 1.4

## 这一圈第二段的长度与路径总长（表 corridor.csv 的 seg_b 列）
var _seg_b := SEG_B
var _path_len := PATH_LEN

## 追逐：唱片里那个人的脚步。他在玩家前方 _gap 米处，跟着唱针走、停、倒退
var _man: AudioStreamPlayer3D
var _step_fwd: AudioStream
var _step_rev: AudioStream
var _door_far: AudioStreamPlayer3D
var _gap := -1.0            # < 0 = 这一圈没有他
var _gap_base := -1.0
var _man_prev := 0.0
var _man_acc := 0.0
var _man_arrived := false
var _merged := false

var rows: Array = []
var layer := 0
var running := false
var player: Node3D

var _audio_fwd: AudioStreamPlayer
var _audio_rev: AudioStreamPlayer
var _scratch: AudioStreamPlayer
var _amb: AudioStreamPlayer
var _bell: AudioStreamPlayer
var _knock: AudioStreamPlayer

var _dist := 0.0
var _speed := 0.0
var _last_pos := Vector2.ZERO
var _layer_t := 0.0
var _bell_t := 0.0
var _bell_done := false
var _silence_t := -1.0
var _knocks_left := 0
var _knocked := false
var _answered := false
var _sources: Array = []
var _chairs: Array = []
var _prints: Array = []
var _fade: ColorRect
var _finished := false
var _sitting := false
## 屏幕上固定的提示（玩家脚本每帧读它）
var current_hint := ""
var sub_label: Label = null
var _beats: Array = []   # [[比例, 文字], ...]

signal done


func _ready() -> void:
	_build_env()
	_build_hall()
	_build_audio()
	_build_fx()
	rows = ContentDB.corridor
	set_process(false)


# ───────────── 建空间 ─────────────

## 回廊的空气：几乎无光的暗，带一点雾，壁灯是唯一的光源
func _build_env() -> void:
	var we := WorldEnvironment.new()
	we.name = "回廊环境"
	var e := Environment.new()
	e.background_mode = Environment.BG_COLOR
	e.background_color = Color("#050506")
	e.ambient_light_source = Environment.AMBIENT_SOURCE_COLOR
	e.ambient_light_color = Color("#2a2622")
	e.ambient_light_energy = 0.12
	e.tonemap_mode = Environment.TONE_MAPPER_ACES
	e.fog_enabled = true
	e.fog_light_color = Color("#141016")
	e.fog_density = 0.055
	we.environment = e
	_env_res = e
	add_child(we)


var _env_res: Environment


func environment() -> Environment:
	return _env_res


func _mat(c: Color) -> StandardMaterial3D:
	var m := StandardMaterial3D.new()
	m.albedo_color = c
	m.roughness = 0.95
	return m


func _box(n: String, pos: Vector3, size: Vector3, m: Material, collide := true) -> Node3D:
	var mi := MeshInstance3D.new()
	mi.name = n
	var bm := BoxMesh.new()
	bm.size = size
	mi.mesh = bm
	mi.material_override = m
	mi.position = pos
	add_child(mi)
	if collide:
		var body := StaticBody3D.new()
		var cs := CollisionShape3D.new()
		var bs := BoxShape3D.new()
		bs.size = size
		cs.shape = bs
		body.add_child(cs)
		mi.add_child(body)
	return mi


func _build_hall() -> void:
	var floor_m := _mat(Color("#241b16"))
	var wall_m := _mat(Color("#2b2622"))
	var ceil_m := _mat(Color("#121010"))
	# 地面 / 天花
	_box("地面A", Vector3(0, -0.05, -SEG_A / 2), Vector3(LANE, 0.1, SEG_A + 1.2), floor_m)
	_box("地面B", Vector3(-SEG_B / 2, -0.05, -SEG_A), Vector3(SEG_B + 0.2, 0.1, LANE), floor_m)
	_box("天花A", Vector3(0, 2.6, -SEG_A / 2), Vector3(LANE, 0.1, SEG_A + 1.2), ceil_m, false)
	_box("天花B", Vector3(-SEG_B / 2, 2.6, -SEG_A), Vector3(SEG_B + 0.2, 0.1, LANE), ceil_m, false)
	# 墙（把路封成一条）
	_box("墙A左", Vector3(-LANE / 2 - 0.05, 1.3, -SEG_A / 2), Vector3(0.1, 2.6, SEG_A + 1.2), wall_m)
	_box("墙A右", Vector3(LANE / 2 + 0.05, 1.3, -SEG_A / 2), Vector3(0.1, 2.6, SEG_A + 1.2), wall_m)
	_box("墙B后", Vector3(-SEG_B / 2, 1.3, -SEG_A - LANE / 2 - 0.05), Vector3(SEG_B + 0.2, 2.6, 0.1), wall_m)
	_box("墙B前", Vector3(-SEG_B / 2, 1.3, -SEG_A + LANE / 2 + 0.05), Vector3(SEG_B + 0.2, 2.6, 0.1), wall_m)
	_box("墙起点", Vector3(0, 1.3, 0.6), Vector3(LANE, 2.6, 0.1), wall_m)
	# 地毯
	_box("地毯A", Vector3(0, 0.004, -SEG_A / 2), Vector3(1.1, 0.008, SEG_A), _mat(Color("#3a2622")), false)
	_box("地毯B", Vector3(-SEG_B / 2, 0.004, -SEG_A), Vector3(SEG_B, 0.008, 1.1), _mat(Color("#3a2622")), false)
	# 护墙板竖条：给走廊一点可读的透视
	var trim := _mat(Color("#171310"))
	for i in range(1, 6):
		for side in [-1.0, 1.0]:
			_box("板A%d_%d" % [i, int(side)], Vector3(side * (LANE / 2 - 0.02), 0.9, -i * 1.45), Vector3(0.05, 1.8, 0.04), trim, false)
	for i in range(1, 5):
		for side in [-1.0, 1.0]:
			_box("板B%d_%d" % [i, int(side)], Vector3(-i * 1.45, 0.9, -SEG_A + side * (LANE / 2 - 0.02)), Vector3(0.04, 1.8, 0.05), trim, false)
	# 尽头：端墙 + 门洞 + 一扇关着的门，走过它就进入下一层。整组是 segB_end，每圈沿 -x 挪到第二段的尽头
	var end := Node3D.new()
	end.name = "segB_end"
	end.position = Vector3(-SEG_B, 0, -SEG_A)
	add_child(end)
	var endwall := _box_child(end, "端墙", Vector3(-0.12, 1.3, 0), Vector3(0.1, 2.6, LANE), wall_m)
	var ew_body := StaticBody3D.new()
	var ew_cs := CollisionShape3D.new()
	var ew_bs := BoxShape3D.new()
	ew_bs.size = Vector3(0.1, 2.6, LANE)
	ew_cs.shape = ew_bs
	ew_body.add_child(ew_cs)
	endwall.add_child(ew_body)
	_box_child(end, "门框B", Vector3(-0.02, 1.05, 0), Vector3(0.1, 2.1, 1.05), _mat(Color("#1e1712")))
	var leaf := _box_child(end, "end_leaf", Vector3(0.05, 1.03, 0), Vector3(0.06, 2.06, 0.95), _mat(Color("#3a2a1d")))
	leaf.set_meta("corridor_gate", true)
	# 门缝下的一道暖光，每一层都是“出口”的提示
	var glow := OmniLight3D.new()
	glow.name = "门缝光"
	glow.position = Vector3(0.35, 0.12, 0)
	glow.light_color = Color("#d8a868")
	glow.light_energy = 1.4
	glow.omni_range = 3.4
	end.add_child(glow)
	# 走廊的灯
	for i in range(1, 5):
		var l := OmniLight3D.new()
		l.name = "壁灯%d" % i
		l.position = Vector3(LANE / 2 - 0.25, 2.15, -i * 1.9)
		l.light_color = Color("#ffcf92")
		l.light_energy = 0.0
		l.omni_range = 6.0
		l.shadow_enabled = true
		add_child(l)
	for i in range(1, 5):
		var l := OmniLight3D.new()
		l.name = "壁灯B%d" % i
		l.position = Vector3(-i * 1.9, 2.15, -SEG_A + LANE / 2 - 0.25)
		l.light_color = Color("#ffcf92")
		l.light_energy = 0.0
		l.omni_range = 6.0
		add_child(l)
	# 转角：暗房的门（第 2 层门缝红光，第 4 层熄灭）
	var turn := Node3D.new()
	turn.name = "转角"
	turn.position = Vector3(-LANE / 2 + 0.02, 0, -SEG_A + 0.9)
	turn.rotation.y = PI / 2
	add_child(turn)
	_box_pair(turn, "暗房门框", Vector3(0, 1.05, 0), Vector3(0.1, 2.1, 1.15), _mat(Color("#20170f")))
	var red := OmniLight3D.new()
	red.name = "门缝红光"
	red.position = Vector3(0.3, 0.3, 0)
	red.light_color = Color("#c0200e")
	red.light_energy = 0.0
	red.omni_range = 2.6
	turn.add_child(red)
	var hs := _hotspot(turn, "hs_darkroom_door", Vector3(0.35, 1.1, 0), Vector3(0.9, 2.0, 1.3))
	hs.set_meta("hotspot_id", "hs_darkroom_door")
	# 历年合影：一排相框（玻璃不反光）
	var photos := Node3D.new()
	photos.name = "合影墙"
	add_child(photos)
	for i in range(6):
		var z := -1.6 - i * 1.15
		_box_child(photos, "相框%d" % i, Vector3(-LANE / 2 + 0.03, 1.5, z), Vector3(0.04, 0.5, 0.38), _mat(Color("#241a12")))
		_box_child(photos, "相纸%d" % i, Vector3(-LANE / 2 + 0.055, 1.5, z), Vector3(0.02, 0.4, 0.28), _mat(Color("#4a4238")))
	photos.visible = false
	_prints_layer(photos)


func _box_pair(parent: Node3D, n: String, pos: Vector3, size: Vector3, m: Material) -> void:
	_box_child(parent, n, pos, size, m)


func _box_child(parent: Node3D, n: String, pos: Vector3, size: Vector3, m: Material) -> Node3D:
	var mi := MeshInstance3D.new()
	mi.name = n
	var bm := BoxMesh.new()
	bm.size = size
	mi.mesh = bm
	mi.material_override = m
	mi.position = pos
	parent.add_child(mi)
	return mi


func _hotspot(parent: Node3D, n: String, pos: Vector3, size: Vector3) -> Area3D:
	var a := Area3D.new()
	a.name = n
	a.position = pos
	var cs := CollisionShape3D.new()
	var bs := BoxShape3D.new()
	bs.size = size
	cs.shape = bs
	a.add_child(cs)
	parent.add_child(a)
	return a


## 第 4 层的湿脚印：沿中线，一次只亮出前面几个
func _prints_layer(parent: Node3D) -> void:
	var m := _mat(Color("#0e0b0a"))
	var n := int(PATH_LEN / STEP)
	for i in n:
		var p := _at(float(i) * STEP)
		var side := 0.09 if i % 2 == 0 else -0.09
		var off := Vector3(side, 0, 0) if p.x > -SEG_A * 0 else Vector3(0, 0, side)
		var f := _box_child(parent, "脚印%d" % i, Vector3(p.x, 0.012, p.z) + off, Vector3(0.1, 0.006, 0.27), m)
		f.visible = false
		_prints.append(f)


# ───────────── 声音 ─────────────

func _build_audio() -> void:
	_audio_fwd = _player("唱针正", -2.0)
	_audio_rev = _player("唱针反", -2.0)
	_scratch = _player("跳针", -4.0, "needle_scratch")
	_bell = _player("铃", -6.0, "seance_bell")
	_knock = _player("敲", -6.0, "door_knock")
	_amb = _player("底噪", -14.0, "room_hum")
	if _amb.stream:
		_amb.stream.loop = true
	# 那个人：一个会动的定位声源，一步一响；倒着走用倒放的步声
	_man = AudioStreamPlayer3D.new()
	_man.name = "那个人"
	_man.unit_size = 3.0
	_man.max_distance = 22.0
	_man.volume_db = -3.0
	_man.max_polyphony = 3
	add_child(_man)
	_step_fwd = _sfx("footstep_shoe")
	_step_rev = _sfx("footstep_shoe_rev")
	_door_far = AudioStreamPlayer3D.new()
	_door_far.name = "尽头的门声"
	_door_far.unit_size = 3.0
	_door_far.max_distance = 30.0
	_door_far.volume_db = -4.0
	_door_far.stream = _sfx("door_creak")
	add_child(_door_far)


func _sfx(id: String) -> AudioStream:
	var path := "res://audio/sfx/%s.ogg" % id
	return load(path) if ResourceLoader.exists(path) else null


func _player(n: String, db: float, id := "") -> AudioStreamPlayer:
	var a := AudioStreamPlayer.new()
	a.name = n
	a.volume_db = db
	var path := "res://audio/sfx/%s.ogg" % id if id != "" else ""
	if path != "" and ResourceLoader.exists(path):
		a.stream = load(path)
	add_child(a)
	return a


func _set_track(fwd: String, rev: String) -> void:
	_audio_fwd.stop()
	_audio_rev.stop()
	var p := "res://audio/voice/corridor_%s.ogg" % fwd
	var q := "res://audio/voice/corridor_%s_rev.ogg" % rev
	_audio_fwd.stream = load(p) if ResourceLoader.exists(p) else null
	_audio_rev.stream = load(q) if ResourceLoader.exists(q) else null


# ───────────── 每层的推进 ─────────────

func start(p: Node3D) -> void:
	player = p
	running = true
	_finished = false
	layer = 0
	player.silent_steps = true
	Director.world.highlight_hotspots([])
	_enter(0)
	set_process(true)


func _enter(i: int) -> void:
	layer = i
	_layer_t = 0.0
	_dist = 0.0
	_speed = 0.0
	_bell_t = 0.0
	_bell_done = false
	_silence_t = -1.0
	_knocked = false
	_answered = false
	_sitting = false
	_last_pos = Vector2(global_position.x, global_position.z)
	var r := _row()
	_set_seg_b(float(r.get("seg_b", "")) if String(r.get("seg_b", "")).is_valid_float() else SEG_B)
	var g := String(r.get("chase_gap", ""))
	_gap_base = float(g) if g.is_valid_float() else -1.0
	_gap = _gap_base
	_man_prev = _gap
	_man_acc = 0.0
	_man_arrived = false
	_merged = false
	_place()
	_set_lights()
	_set_track(String(r.get("track", "")), String(r.get("track", "")))
	_parse_beats(String(r.get("beats", "")))
	_stage_layer(i, r)
	if _amb.stream and not _amb.playing:
		_amb.play()
	current_hint = ""
	Director.ui.set_checklist([])
	if i == 0:
		Director.ui.toast("走，声音才会有。")


## beats 列："0.12:走，声音才会有。|0.55:停下来，声音也停了。"
func _parse_beats(spec: String) -> void:
	_beats = []
	for part in spec.split("|", false):
		var t := part.split(":", true, 1)
		if t.size() == 2 and t[0].strip_edges().is_valid_float():
			_beats.append([float(t[0].strip_edges()), t[1].strip_edges()])
	if sub_label:
		sub_label.text = ""


## 第二段截到 seg 米：挪尽头那一组，地毯跟着短，尽头以外的壁灯关掉
func _set_seg_b(seg: float) -> void:
	_seg_b = clampf(seg, 1.5, SEG_B)
	_path_len = SEG_A + _seg_b
	var end := get_node_or_null("segB_end")
	if end:
		end.position = Vector3(-_seg_b, 0, -SEG_A)
	var rug := get_node_or_null("地毯B") as Node3D
	if rug:
		rug.scale.x = _seg_b / SEG_B
		rug.position.x = -_seg_b / 2
	for i in range(1, 5):
		var l := get_node_or_null("壁灯B%d" % i) as Node3D
		if l:
			l.visible = l.position.x > -_seg_b + 0.2


func _row() -> Dictionary:
	return rows[int(clampf(layer, 0, rows.size() - 1))]


func _place() -> void:
	player.place(global_position + Vector3(0, 0, -0.15), 0.0)
	player.needs_spawn = false
	player.frozen = false


func _set_lights() -> void:
	var e := [2.6, 3.2, 2.0, 2.4, 1.4, 1.1]
	var k: float = e[int(clampf(layer, 0, 5))]
	for i in range(1, 5):
		var l := get_node_or_null("壁灯%d" % i)
		if l:
			l.light_energy = k
	for i in range(1, 5):
		var l := get_node_or_null("壁灯B%d" % i)
		if l:
			l.light_energy = k * 0.85


## 每层多出 / 换掉的东西
func _stage_layer(i: int, _r: Dictionary) -> void:
	var photos := get_node_or_null("合影墙")
	if photos:
		photos.visible = i >= 2
	var red := get_node_or_null("转角/门缝红光")
	if red:
		red.light_energy = 1.7 if i == 1 else 0.0
	# 脚印：第 4 层
	for f in _prints:
		f.visible = false
	# 椅子：第 5 层
	for c in _chairs:
		c.visible = false
	# 第 5 层：把三处声源与椅子摆出来
	if i == 4:
		_build_chairs()
		if Director.world.has_method("_bind_meta_hotspots"):
			Director.world._bind_meta_hotspots(self)
		for s in _sources:
			s["found"] = false
			if s["player"].stream:
				s["player"].play()
	# 第 6 层：坐在第四把椅子上
	if i == 5:
		_build_chairs()
		for c in _chairs:
			c.visible = true
		_sitting = true
		player.frozen = true
		player.place(global_position + Vector3(-SEG_B + 0.75, 0, -SEG_A + 0.05), 90.0)


func _build_chairs() -> void:
	if not _chairs.is_empty():
		for c in _chairs:
			c.visible = layer >= 4
		return
	var spots := [
		Vector3(LANE / 2 - 0.62, 0, -2.6),
		Vector3(-LANE / 2 + 0.62, 0, -5.4),
		Vector3(-2.2, 0, -SEG_A + LANE / 2 - 0.55),
		Vector3(-SEG_B + 1.0, 0, -SEG_A),
	]
	for i in spots.size():
		var c := Node3D.new()
		c.name = "椅子%d" % (i + 1)
		c.position = spots[i]
		add_child(c)
		var m := _mat(Color("#1f1510"))
		_box_child(c, "座", Vector3(0, 0.44, 0), Vector3(0.44, 0.05, 0.42), m)
		_box_child(c, "靠背", Vector3(0, 0.74, 0.2), Vector3(0.44, 0.58, 0.05), m)
		for k in 4:
			_box_child(c, "腿%d" % k, Vector3(0.17 if k % 2 == 0 else -0.17, 0.22, 0.17 if k < 2 else -0.17), Vector3(0.04, 0.44, 0.04), m)
		c.visible = false
		_chairs.append(c)
	var old := get_node_or_null("hs_chair4")
	if old:
		old.queue_free()
	var a := _hotspot(self, "hs_chair4", Vector3(-SEG_B + 1.0, 0.6, -SEG_A), Vector3(1.2, 1.4, 1.2))
	a.set_meta("hotspot_id", "hs_chair4")
	a.set_meta("corridor_new", true)
	# 三处声源
	var src := [
		Vector3(LANE / 2 - 0.62, 1.2, -2.6),
		Vector3(-LANE / 2 + 0.62, 1.2, -5.4),
		Vector3(-2.2, 1.2, -SEG_A + LANE / 2 - 0.55),
	]
	_sources.clear()
	for i in src.size():
		var sp := AudioStreamPlayer3D.new()
		sp.name = "声源%d" % (i + 1)
		sp.position = src[i]
		sp.unit_size = 2.4
		sp.max_distance = 12.0
		sp.volume_db = -2.0
		var f := "res://audio/voice/corridor_s%d.ogg" % (i + 1)
		if ResourceLoader.exists(f):
			sp.stream = load(f)
		add_child(sp)
		_sources.append({"pos": src[i], "player": sp, "found": false, "id": i + 1, "chair": spots[i]})


# ───────────── 每帧 ─────────────

func _process(dt: float) -> void:
	if not running or player == null:
		return
	_layer_t += dt
	var pos: Vector2 = Vector2(player.global_position.x, player.global_position.z)
	_dist = _project(player.global_position - global_position)
	var v := (pos - _last_pos).length() / maxf(dt, 0.0001)
	_prev_dist = _dist
	_last_pos = pos
	_speed = lerpf(_speed, clampf(v, -2.5, 2.5), 0.18)
	_needle()
	_subtitles()
	_rules(dt)


var _prev_dist := 0.0


func _project(p: Vector3) -> float:  # p 是相对本节点的本地坐标
	var za := clampf(-p.z, 0.0, SEG_A)
	if za < SEG_A - 0.001:
		return za
	return SEG_A + clampf(-p.x, 0.0, SEG_B)


func _at(d: float) -> Vector3:
	var k := clampf(d, 0.0, PATH_LEN)
	if k <= SEG_A:
		return Vector3(0, 0, -k)
	return Vector3(-(k - SEG_A), 0, -SEG_A)


## 唱针：声音的位置跟着玩家在走廊里的位置；停就停，退就倒放
func _needle() -> void:
	var ratio := clampf(_dist / PATH_LEN, 0.0, 1.0)
	var going_forward: bool = _speed > 0.0
	if player.has_method("get") and player.forward == false:
		going_forward = false
	var fwd: AudioStreamPlayer = _audio_fwd if going_forward else _audio_rev
	var other: AudioStreamPlayer = _audio_rev if going_forward else _audio_fwd
	if fwd.stream == null:
		return
	var len := fwd.stream.get_length()
	if absf(_speed) < 0.12 or _sitting:
		fwd.stop()
		other.stop()
		return
	if other.playing:
		other.stop()
	if not fwd.playing:
		fwd.play()
	var t := ratio * len if going_forward else (1.0 - ratio) * len
	if absf(fwd.get_playback_position() - t) > 0.08:
		fwd.seek(t)
	fwd.pitch_scale = clampf(1.0 + (_speed - SPEED) * 0.18, 0.72, 1.5)


## 字幕跟着唱针走：念到的句子才出现，字一个一个浮出来；往回走，字一个一个退回去
func _subtitles() -> void:
	if sub_label == null:
		return
	if _beats.is_empty() or _sitting:
		sub_label.text = ""
		return
	var ratio := clampf(_dist / PATH_LEN, 0.0, 1.0)
	var idx := -1
	for i in _beats.size():
		if ratio >= float(_beats[i][0]):
			idx = i
	if idx < 0:
		sub_label.text = ""
		return
	var text: String = _beats[idx][1]
	var start := float(_beats[idx][0])
	var end := float(_beats[idx + 1][0]) if idx + 1 < _beats.size() else 1.0
	var k := clampf((ratio - start) / maxf(end - start, 0.0001), 0.0, 1.0)
	var n := int(ceil(float(text.length()) * k))
	sub_label.text = text.substr(0, n)


## 每层的规则
func _rules(dt: float) -> void:
	match layer:
		1:  # 案发夜：铃响不能回头
			if _dist / PATH_LEN > 0.45 and not _bell_done and _bell_t <= 0.0:
				_bell_t = 4.0
				if _bell.stream:
					_bell.play()
			if _bell_t > 0.0:
				_bell_t -= dt
				# 走廊方向是 -z，转到背后就是 yaw 偏离 0 超过 100 度
				if absf(angle_difference(player.rotation.y, 0.0)) > deg_to_rad(100.0):
					_bust("铃响的时候，不要回头。")
				if _bell_t <= 0.0:
					_bell_done = true
		2:  # 序章门厅：那句话从身后响起，回答就重来
			if _dist / PATH_LEN > 0.35 and not _answered and _layer_t > 2.0:
				current_hint = "E　我手里只有信的第一页。"
		3:  # 星期四夜：脚印；到暗房门口有一段沉默，听完才走得过去
			_stage_prints()
			var near := absf(_dist - (SEG_A - 0.7)) < 0.55
			if near and _silence_t < 0.0 and not _knocked:
				_silence_t = 5.0
				_knocked = true
				Director.ui.toast("暗房里有人说：你来了。")
			if _silence_t > 0.0:
				_silence_t -= dt
				if _dist > SEG_A - 0.35:
					_dist = SEG_A - 0.35
					player.place(global_position + _at(SEG_A - 0.35), 0.0)
		4:  # 怪谈：走近三处声源（只能靠听觉找：走近了，椅子就在那里）
			for s in _sources:
				var d: float = Vector2(s["chair"].x, s["chair"].z).distance_to(Vector2(player.global_position.x - global_position.x, player.global_position.z - global_position.z))
				if not s["found"]:
					s["player"].volume_db = lerpf(-3.0, -26.0, clampf((d - 0.9) / 7.0, 0.0, 1.0))
					if d < 1.15:
						s["found"] = true
						s["player"].stop()
						var ch: Node3D = _chairs[s["id"] - 1]
						ch.visible = true
						if _knock.stream:
							_knock.play()
						Director.ui.toast("椅背是温的。")
	# 走到尽头：进入下一层（第 5 层要先找齐三把）
	if _dist >= PATH_LEN - 0.35 and _silence_t <= 0.0 and not _sitting:
		if layer == 4 and _sources.filter(func(s): return s["found"]).size() < 3:
			if _dist > PATH_LEN - 0.3:
				player.place(global_position + _at(PATH_LEN - 0.45), 0.0)
			return
		_next()


func _stage_prints() -> void:
	if layer != 3:
		return
	for i in _prints.size():
		_prints[i].visible = _dist > float(i) * STEP - 1.6


func _bust(reason: String) -> void:
	if _bell_t < 0.0:
		return
	_bell_t = -1.0
	if _scratch.stream:
		_scratch.play()
	Director.ui.toast(reason)
	await get_tree().create_timer(0.7).timeout
	_enter(layer)


func _next() -> void:
	if layer >= rows.size() - 1:
		_finish()
		return
	_enter(layer + 1)


func _finish() -> void:
	if _finished:
		return
	_finished = true
	running = false
	set_process(false)
	for s in _sources:
		s["player"].stop()
	_audio_fwd.stop()
	_audio_rev.stop()
	if _amb.stream:
		_amb.stop()
	Director.ui.set_hint("")
	player.silent_steps = false
	Director.world.highlight_hotspots([])
	done.emit()


## 玩家按 E：回廊里只有三件事
func interact(id: String) -> bool:
	if not running:
		return false
	if id == "hs_darkroom_door":
		if layer == 1 and not _knocked:
			_knocked = true
			if _knock.stream:
				_knock.play()
			Director.ui.toast("门里有人敲回来两下。很轻，像一个人思考的时候，用指节敲两下桌面。")
			current_hint = ""
		elif layer == 3:
			Director.ui.toast("门里没有声音。来的人没有回答。")
		return true
	if id == "hs_chair4" and layer == 4:
		if _sources.filter(func(s): return s["found"]).size() < 3:
			Director.ui.toast("还有声音没有找到。")
			return true
		_enter(5)
		await get_tree().create_timer(5.0).timeout
		if not running:
			return true
		Director.ui.show_text("有人在看着我们。稳定率已经很低了。")
		await get_tree().create_timer(1.2).timeout
		_finish()
		return true
	return false


## 第 3 层：玩家选了“回答”。规矩是不要回答
func answer() -> void:
	if layer != 2 or _answered:
		return
	_answered = true
	current_hint = ""
	if _scratch.stream:
		_scratch.play()
	Director.ui.toast("有人问你话，不要回答。")
	await get_tree().create_timer(0.7).timeout
	_enter(2)


## 玩家按 E 时如果屏幕上有“回答”，就是回答了（第 3 层的陷阱）
func answering() -> bool:
	return layer == 2 and _dist / PATH_LEN > 0.35


func _build_fx() -> void:
	var layer_node := CanvasLayer.new()
	layer_node.layer = 8
	add_child(layer_node)
	sub_label = Label.new()
	sub_label.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER
	sub_label.anchor_left = 0.12
	sub_label.anchor_right = 0.88
	sub_label.anchor_top = 0.80
	sub_label.anchor_bottom = 0.92
	sub_label.vertical_alignment = VERTICAL_ALIGNMENT_CENTER
	sub_label.autowrap_mode = TextServer.AUTOWRAP_WORD_SMART
	sub_label.add_theme_font_size_override("font_size", 26)
	sub_label.add_theme_color_override("font_color", Color("#efe3c6"))
	sub_label.add_theme_color_override("font_shadow_color", Color(0, 0, 0, 0.85))
	sub_label.add_theme_constant_override("shadow_offset_x", 1)
	sub_label.add_theme_constant_override("shadow_offset_y", 2)
	sub_label.text = ""
	layer_node.add_child(sub_label)
	_fade = ColorRect.new()
	_fade.set_anchors_preset(Control.PRESET_FULL_RECT)
	_fade.color = Color(0, 0, 0, 0)
	_fade.mouse_filter = Control.MOUSE_FILTER_IGNORE
	layer_node.add_child(_fade)
