extends Node3D
## 第 5 章“回廊”：降灵会之后的神游空间。
## 玩法“你就是唱针”：留声机的声音只在玩家走动时才响，停下就停，往回走就倒放；
## 走过尽头的门回到起点，进入下一层。设计见 docs/关卡/ded_corridor.md。
##
## Blender 模型由 ded_corridor.tscn 实例化；本脚本只负责状态、声音与交互。
## 显隐与实体碰撞同步切换，避免隐藏墙补片继续堵住房门。

const SEG_A := 8.0          # 第一段：从起点沿 -z
const SEG_B := 6.0          # 左转后沿 -x（最长；每圈按表里的 seg_b 截短，唱片越放越靠里）
const PATH_LEN := SEG_A + SEG_B
const LANE := 1.6
const STEP := 0.7
const SPEED := 1.4
const DOORS := [6.0, 3.6, 1.2]   # 左墙三扇门的中心离起点的距离（第一段）

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
var _chase_d := 0.0          # 上一帧走到哪里（判断是不是在往前走）

var rows: Array = []
var layer := 0
var running := false
var player: Node3D

var _audio_fwd: AudioStreamPlayer
var _audio_rev: AudioStreamPlayer
## 响应式音乐（10-20）分三层：
##   底色 BGM（低音提琴、镲片、弱音小号）：按时间一直在放，每圈一段 16 秒循环（表 music 列）；
##     往回走时倒放，停下时压低、不停
##   脚步层（鼓 + 钢琴）：沿走廊每走过一步（0.7 m）一下，对齐到底色的下一个十六分音符；
##     左脚落地鼓、右脚鼓边（表 drums 列），钢琴按八步的格子叠上去（表 steps 列）；往回走用倒放音样
##   唱片人声：每圈的剧情人声与字幕，仍跟着唱针（_audio_fwd / _audio_rev）
const GRID := 0.125               # 120 BPM 的十六分音符
var _bed_fwd: AudioStreamPlayer
var _bed_rev: AudioStreamPlayer
var _bed_back := false
var _bed_gain := 0.0
var _ending: AudioStreamPlayer     # 最后一圈：小号吹《潜影》动机的开头，在第四个音之前断掉
var _drum: AudioStreamPlayer
var _steps: AudioStreamPlayer      # 钢琴
var _step_pat := PackedStringArray()
var _drums_on := false
var steps_played := 0      # 自查用：这一局弹了多少下
var _step_cell := 0
var _gains := {}
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
var _model: Node3D
var _nodes := {}
var _door_yaws := {}
var _room_seen := {}
var _room_entered := false
var _room_left := false
var _in_photo := false
var _touching := false
var _resetting := false
var _figure_start := Vector3.ZERO
var _photo_spawn := Vector3(30, 0.04, 0.8)
const ROOM_NOTES := ["ev_corridor_hook", "ev_corridor_circle", "ev_corridor_window"]
var _room_observations := [
	"空着的那个挂钩还在晃。下面一摊水。",
	"有人在这里绕着圈走，走了很久。",
	"从上面看，那条走廊没有出口。",
]
var _sitting := false
## 屏幕上固定的提示（玩家脚本每帧读它）
var current_hint := ""
var sub_label: Label = null
var _beats: Array = []   # [[比例, 文字], ...]

signal done


func _ready() -> void:
	_build_env()
	_bind_model()
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


## 导入器会去掉 -col 后缀；名字统一在这里索引，玩法不依赖导入后的深层路径。
func _bind_model() -> void:
	_model = get_node("模型")
	for n in _model.find_children("*", "", true, false):
		_nodes[String(n.name)] = n
		if n is CollisionObject3D:
			n.set_meta("solid_layer", n.collision_layer)
	for i in range(1, 4):
		_door_yaws[i] = _part("door_%d" % i).rotation.y
		var doorway := _hotspot(self, "hs_corridor_door_%d" % i, Vector3(-0.72, 1.05, -DOORS[i-1]), Vector3(0.12, 1.9, 0.80))
		doorway.set_meta("hotspot_id", String(doorway.name))
	var end := _part("segB_end")
	var exit_target := _hotspot(end, "hs_doorway", Vector3(0.13, 1.05, 0), Vector3(0.12, 1.9, 0.80))
	exit_target.set_meta("hotspot_id", "hs_doorway")
	exit_target.set_meta("interaction_normal", Vector3.RIGHT)
	var dark := _hotspot(self, "hs_darkroom_door", Vector3(0, 1.05, -8.76), Vector3(0.85, 1.9, 0.12))
	dark.set_meta("hotspot_id", "hs_darkroom_door")
	dark.set_meta("interaction_normal", Vector3.BACK)
	var chair := _hotspot(end, "hs_chair4", Vector3(0.46, 0.65, 0), Vector3(0.40, 1.05, 0.50))
	chair.set_meta("hotspot_id", "hs_chair4")
	var targets := [Vector3(-4.02, 1.62, -6.025), Vector3(-2.6, 0.06, -3.4), Vector3(0, 2.42, 0.57)]
	for i in range(3):
		var target := _hotspot(self, "hs_room_%d" % (i+1), targets[i], Vector3(0.25, 0.25, 0.3) if i != 1 else Vector3(0.8, 0.06, 0.8))
		target.set_meta("hotspot_id", String(target.name))
	var touch := _hotspot(self, "hs_corridor_figure", Vector3.ZERO, Vector3(0.5, 1.5, 0.4))
	touch.set_meta("hotspot_id", "hs_corridor_figure")
	for i in range(1, 5):
		_chairs.append(_part("prop_chair_%d" % i))
	for i in range(1, 13):
		_prints.append(_part("prop_print_%02d" % i))
	_figure_start = _part("gh_figure").position
	_build_lights()


func _part(id: String) -> Node3D:
	return _nodes.get(id)


## 只切换这组节点的物理层，不修改共享的 GLB 碰撞资源。
func _show_part(node: Node3D, show: bool) -> void:
	node.visible = show
	var solids: Array = node.find_children("*", "CollisionObject3D", true, false)
	if node is CollisionObject3D:
		solids.append(node)
	for solid in solids:
		solid.collision_layer = int(solid.get_meta("solid_layer", 1)) if show else 0


func _build_lights() -> void:
	for i in range(1, 6):
		_light("壁灯%d" % i, Vector3(0.60, 2.15, -[0.5, 2.4, 4.3, 6.2, 8.1][i-1]), 1.6)
	for i in range(1, 4):
		_light("壁灯B%d" % i, Vector3([-1.45, -3.35, -5.25][i-1], 2.15, -8.60), 1.6)
	for i in range(1, 4):
		_light("房间灯%d" % i, Vector3(-2.6, 2.35, -[5.8, 3.4, 1.2][i-1]) if i < 3 else Vector3(-1.5, 2.35, -1.2), 1.5)
	_light("楼梯平台灯", Vector3(-0.9, 2.5, 1.38), 1.2)
	_light("门缝红光", Vector3(0, 0.22, -8.62), 0.0, Color("#e52b13"))
	_light("照片烛光", Vector3(0.55, 0.5, 0), 0.8, Color("#ffbf72"), _part("segB_end"))
	_light("温室月光", Vector3(30, 2.8, -1.7), 1.3, Color("#8b9dbb"))
	_light("温室门光", Vector3(28.9, 1.9, -3.35), 1.8)


func _light(id: String, pos: Vector3, energy: float, color := Color("#ffcf92"), parent: Node3D = self) -> void:
	var light := OmniLight3D.new()
	light.name = id
	light.position = pos
	light.light_color = color
	light.light_energy = energy
	light.omni_range = 4.0
	# 灯罩网格不应把点光源封在里面；模型本身保留遮挡。
	light.shadow_enabled = false
	parent.add_child(light)


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
	_bed_fwd = _player("底色正", MUSIC_DB)
	_bed_rev = _player("底色反", MUSIC_DB)
	_ending = _player("唱片尾", MUSIC_DB)
	_steps = _player("钢琴", STEPS_DB)
	_steps.max_polyphony = 4
	_drum = _player("鼓", DRUM_DB)
	_drum.max_polyphony = 4
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


## 换这一圈的底色：从头正放，循环
func _set_music(id: String) -> void:
	_bed_fwd.stop()
	_bed_rev.stop()
	_bed_fwd.stream = null
	_bed_rev.stream = null
	_bed_back = false
	if id == "" or id == "ending":
		return
	_bed_fwd.stream = _loop_stream("res://audio/music/corridor_%s.ogg" % id)
	_bed_rev.stream = _loop_stream("res://audio/music/corridor_%s_rev.ogg" % id)
	if _bed_fwd.stream:
		_bed_fwd.play()


func _loop_stream(path: String) -> AudioStream:
	if not ResourceLoader.exists(path):
		return null
	var st: AudioStream = load(path)
	if "loop" in st:
		st.loop = true
	return st


## 底色：按时间走。往回走时换到倒放那一条（从镜像位置接上），停下时压低、不停
func _bed() -> void:
	if _bed_fwd.stream == null or _bed_rev.stream == null:
		return
	var back := _speed < -0.12 and not _sitting
	if back != _bed_back:
		var len := _bed_fwd.stream.get_length()
		var from: AudioStreamPlayer = _bed_rev if _bed_back else _bed_fwd
		var to: AudioStreamPlayer = _bed_fwd if _bed_back else _bed_rev
		var p := len - from.get_playback_position() if from.playing else 0.0
		from.stop()
		to.play(fposmod(p, len))
		_bed_back = back
	var moving := absf(_speed) >= 0.12
	_bed_gain = move_toward(_bed_gain, 1.0 if moving else 0.56, get_process_delta_time() / 0.25)
	var db := MUSIC_DB + linear_to_db(maxf(_bed_gain, 0.0001))
	_bed_fwd.volume_db = db
	_bed_rev.volume_db = db


## 离底色的下一个十六分音符还有多久（底色正放、倒放都对得上：循环长是十六分音符的整数倍）
func _grid_delay() -> float:
	var pl: AudioStreamPlayer = _bed_rev if _bed_back else _bed_fwd
	if not pl.playing:
		return 0.0
	var t := pl.get_playback_position() + AudioServer.get_time_since_last_mix()
	var d := GRID - fposmod(t, GRID)
	return 0.0 if d > GRID - 0.012 else d


## 脚步层：每越过一个 0.7 m 的格子响一下（鼓左右交替 + 钢琴按格子），等到下一个十六分音符再出声；
## 往回越过就放倒放（短促地“吸”回去）
func _step_layer(dd: float) -> void:
	var cell := int(floor(_dist / STEP))
	if cell == _step_cell:
		return
	var back := cell < _step_cell
	var k := _step_cell if back else cell
	_step_cell = cell
	if _sitting or absf(dd) > 1.0:
		return
	var names: Array = []
	if _drums_on:
		names.append(["drum_l" if k % 2 == 0 else "drum_r", _drum])
	if not _step_pat.is_empty():
		var p := String(_step_pat[posmod(k, _step_pat.size())]).strip_edges()
		if p != "":
			names.append([p, _steps])
	if names.is_empty():
		return
	steps_played += 1
	_fire_step(names, back)


func _fire_step(names: Array, back: bool) -> void:
	var d := _grid_delay()
	if d > 0.0:
		await get_tree().create_timer(d).timeout
	if not running:
		return
	for pair in names:
		var path := "res://audio/music/steps/%s%s.ogg" % [pair[0], "_rev" if back else ""]
		if ResourceLoader.exists(path):
			var pl: AudioStreamPlayer = pair[1]
			pl.stream = load(path)
			pl.play()


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
	_room_seen.clear()
	layer = 0
	player.silent_steps = true
	Director.world.highlight_hotspots([])
	_enter(0)
	set_process(true)


func _enter(i: int) -> void:
	layer = i
	_layer_t = 0.0
	_dist = 0.0
	_prev_dist = 0.0
	_speed = 0.0
	_bell_t = 0.0
	_bell_done = false
	_silence_t = -1.0
	_knocked = false
	_answered = false
	_sitting = false
	_in_photo = false
	_touching = false
	_resetting = false
	_room_entered = false
	_room_left = false
	_last_pos = Vector2(global_position.x, global_position.z)
	var r := _row()
	_set_seg_b(float(r.get("seg_b", "")) if String(r.get("seg_b", "")).is_valid_float() else SEG_B)
	var g := String(r.get("chase_gap", ""))
	_gap_base = float(g) if g.is_valid_float() else -1.0
	_gap = _gap_base
	_man_prev = _gap
	_chase_d = 0.0
	_man_acc = 0.0
	_man_arrived = false
	_merged = false
	_place()
	_set_lights()
	_set_track(String(r.get("track", "")), String(r.get("track", "")))
	_set_music(String(r.get("music", "")))
	_step_pat = String(r.get("steps", "")).split(",", true) if String(r.get("steps", "")) != "" else PackedStringArray()
	_drums_on = String(r.get("drums", "")) == "是"
	_step_cell = 0
	sub_label.show()
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
	var end := _part("segB_end")
	if end:
		end.position = Vector3(-_seg_b, 0, -SEG_A)
	for k in range(1, 5):
		_show_part(_part("segB_sec_%d" % k), k <= _seg_b - 2)
	for i in range(1, 5):
		var l := get_node_or_null("壁灯B%d" % i) as Node3D
		if l:
			l.visible = l.position.x > -_seg_b + 0.2


func _row() -> Dictionary:
	return rows[int(clampf(layer, 0, rows.size() - 1))]


func _place() -> void:
	player.place(global_position + Vector3(0, 0.03, -0.15), 0.0)
	player.needs_spawn = false
	player.frozen = false


func _set_lights() -> void:
	var e := [2.6, 3.2, 2.0, 2.4, 1.4, 1.1]
	var k: float = e[int(clampf(layer, 0, 5))]
	for i in range(1, 6):
		var l := get_node_or_null("壁灯%d" % i)
		if l:
			l.light_energy = k * 0.55 if not (layer == 3 and i == 3) else 0.0
	for i in range(1, 5):
		var l := get_node_or_null("壁灯B%d" % i)
		if l:
			l.light_energy = k * 0.85


## 每层多出 / 换掉的东西
func _stage_layer(i: int, _r: Dictionary) -> void:
	for n in range(1, 4):
		var forgotten := i > n
		_show_part(_part("doorway_%d" % n), not forgotten)
		_show_part(_part("wall_%d" % n), forgotten)
		_part("door_%d" % n).rotation.y = _door_yaws[n] - deg_to_rad(12.0 if i == n else 0.0)
		get_node("房间灯%d" % n).visible = i == n
	get_node("楼梯平台灯").visible = i == 3
	get_node("门缝红光").light_energy = 1.7 if i == 1 else 0.0
	_show_part(_part("glow_darkroom"), i == 1)
	_show_part(_part("door_end"), i != 5)
	_show_part(_part("photo_wall"), i == 5)
	for f in _prints:
		f.visible = false
	for c in _chairs:
		c.visible = false
	for source in _sources:
		source.player.stop()
	if i == 4:
		_build_chairs()
		for source in _sources:
			source.found = false
			if source.player.stream:
				source.player.play()
	_part("gh_figure").position = _figure_start
	_part("gh_figure").visible = i == 5
	_sync_interaction_targets()


func _build_chairs() -> void:
	if not _sources.is_empty():
		return
	for i in range(3):
		var pos := Vector3(-1.4, 1.2, -DOORS[i])
		var sp := AudioStreamPlayer3D.new()
		sp.position = pos
		sp.unit_size = 2.4
		sp.max_distance = 12.0
		sp.volume_db = -2.0
		var path := "res://audio/voice/corridor_s%d.ogg" % (i+1)
		if ResourceLoader.exists(path):
			sp.stream = load(path)
		add_child(sp)
		_sources.append({"pos": pos, "player": sp, "found": false, "id": i+1, "chair": _chairs[i].position})


func _update_room() -> void:
	if layer not in [1, 2, 3]:
		return
	var p := player.global_position - global_position
	# 只在穿过本圈支线门洞时记为进房；第二段主走廊也在 x < -1.15。
	if p.x < -1.15 and absf(p.z + DOORS[layer - 1]) < 0.5 and p.y < 0.4:
		_room_entered = true
	elif _room_entered and p.x > -0.4 and p.z < -0.6 and p.z > -7.2 and p.y < 0.4 and not _room_left:
		_room_left = true
		_part("door_%d" % layer).rotation.y = _door_yaws[layer]
		_sync_interaction_targets()


func _update_photo() -> void:
	if layer != 5 or _touching:
		return
	if not _in_photo:
		if _dist >= _path_len - 1.0:
			_in_photo = true
			player.place(global_position + _photo_spawn, 0)
			Director.ui.toast("脚下变成了湿泥地。脚步声从照片里面传来。")
	else:
		var p := player.global_position - global_position
		# 人影与玩家同步，靠近侧门后停住，留下可以伸手的距离。
		var progress := clampf(_photo_spawn.z - p.z, 0.0, 1.15)
		_part("gh_figure").position = _figure_start + Vector3(0, 0, -progress)
		get_node("hs_corridor_figure").position = _part("gh_figure").position + Vector3(0, 0.9, 0.15)
		_sync_interaction_targets()


# ───────────── 每帧 ─────────────

func _process(dt: float) -> void:
	if not running or player == null or _resetting:
		return
	_layer_t += dt
	var pos: Vector2 = Vector2(player.global_position.x, player.global_position.z)
	_dist = _project(player.global_position - global_position)
	# 唱针的速度 = 沿走廊前进了多少（带正负）。侧着走、原地转身都不算；推门回到起点那一下也不算
	var dd := _dist - _prev_dist
	var v := 0.0 if absf(dd) > 1.0 else dd / maxf(dt, 0.0001)
	_prev_dist = _dist
	_last_pos = pos
	_speed = lerpf(_speed, clampf(v, -2.5, 2.5), 0.18)
	_step_layer(dd)
	_bed()
	_needle()
	_chase(dt)
	_subtitles()
	_update_room()
	_update_photo()
	_rules(dt)


var _prev_dist := 0.0
const NEEDLE_DB := -2.0   # 人声
const MUSIC_DB := -7.0    # 底色 BGM
const STEPS_DB := -12.0   # 脚步层的钢琴
const DRUM_DB := -9.0     # 脚步层的鼓


func _project(p: Vector3) -> float:  # p 是相对本节点的本地坐标
	var za := clampf(-p.z, 0.0, SEG_A)
	if p.z > -7.2 or p.x > -0.2:
		return za
	return SEG_A + clampf(-p.x, 0.0, _seg_b)


func _at(d: float) -> Vector3:
	var k := clampf(d, 0.0, _path_len)
	if k <= SEG_A:
		return Vector3(0, 0, -k)
	return Vector3(-(k - SEG_A), 0, -SEG_A)


## 唱针：声音的位置跟着玩家在走廊里的位置；停就停，退就倒放。人声和唱片（BGM）两对都这样放
func _needle() -> void:
	_needle_pair(_audio_fwd, _audio_rev, NEEDLE_DB)


func _needle_pair(a_fwd: AudioStreamPlayer, a_rev: AudioStreamPlayer, db: float) -> void:
	var ratio := clampf(_dist / _path_len, 0.0, 1.0)
	var going_forward: bool = _speed > 0.0
	var fwd: AudioStreamPlayer = a_fwd if going_forward else a_rev
	var other: AudioStreamPlayer = a_rev if going_forward else a_fwd
	if fwd.stream == null:
		return
	var len := fwd.stream.get_length()
	# 停下时不硬切（会“啪”一声）：60 毫秒左右淡掉再停
	var moving := absf(_speed) >= 0.12 and not _sitting
	var g: float = _gains.get(a_fwd.name, 0.0)
	g = move_toward(g, 1.0 if moving else 0.0, get_process_delta_time() / 0.06)
	_gains[a_fwd.name] = g
	fwd.volume_db = db + linear_to_db(maxf(g, 0.0001))
	if not moving and g <= 0.0:
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
	# 正常步速走完一圈正好放完一条录音：第二段越短，放得越快（越往里，节奏越急）
	var base := len / _path_len * SPEED
	fwd.pitch_scale = clampf(base * (1.0 + (absf(_speed) - SPEED) * 0.18), 0.6, 1.8)


## 沿路径 d 米处的位置；超过尽头时沿 -x 继续延伸（那个人穿过尽头的门以后）
func _at_ext(d: float) -> Vector3:
	if d <= SEG_A:
		return Vector3(0, 0, -maxf(d, 0.0))
	return Vector3(-(d - SEG_A), 0, -SEG_A)


## 追逐：唱片里那个人的脚步在玩家前方 _gap 米处。玩家走他就走，停他就停，倒走他就倒着走回来。
## 第 1 圈他远远地穿过尽头的门；第 2 圈停在暗房门前；第 4 圈走得合拍，他就越来越近，最后和玩家的步子合上
func _chase(dt: float) -> void:
	if _gap < 0.0 or _man == null or _sitting:
		return
	var moving_on := _dist > _chase_d + 0.0005
	_chase_d = _dist
	if layer == 3 and not _merged:
		var p := player.global_position - global_position
		var lateral: float = absf(p.x) if _dist < SEG_A - 0.6 else absf(p.z + SEG_A)
		var in_step: bool = absf(_speed - SPEED) <= SPEED * 0.15 and lateral <= 0.25 and moving_on
		if in_step:
			_gap = maxf(0.0, _gap - dt * 0.3)
		elif absf(_speed) > 0.12:
			_gap = minf(_gap_base, _gap + dt * 0.12)
		if _gap <= 0.15:
			_merged = true
			_man.stop()
			Director.ui.toast("前面的脚步声，和我的步子合上了。")
			return
	if _merged:
		return
	var cap := _path_len + 0.8           # 穿过尽头的门
	if layer == 1:
		cap = SEG_A - 0.6                # 案发夜：停在转角的暗房门前
	var m := minf(_dist + _gap, cap)
	if m >= cap and not _man_arrived:
		_man_arrived = true
		if layer == 0 and _door_far.stream:
			_door_far.position = _at_ext(_path_len)
			_door_far.play()
	var delta := m - _man_prev
	_man_prev = m
	_man.position = _at_ext(m) + Vector3(0, 0.05, 0)
	if m >= cap:
		return
	_man_acc += absf(delta)
	if _man_acc >= STEP:
		_man_acc -= STEP
		_man.stream = _step_fwd if delta >= 0.0 else _step_rev
		if _man.stream:
			_man.pitch_scale = clampf(0.92 + absf(_speed - SPEED) * 0.2 * signf(_speed - SPEED), 0.75, 1.3)
			_man.play()


## 字幕跟着唱针走：念到的句子才出现，字一个一个浮出来；往回走，字一个一个退回去
func _subtitles() -> void:
	if sub_label == null:
		return
	if _beats.is_empty() or _sitting:
		sub_label.text = ""
		return
	var ratio := clampf(_dist / _path_len, 0.0, 1.0)
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
			if _knocked and not _bell_done and _bell_t <= 0.0:
				_bell_t = 4.0
				if _bell.stream:
					_bell.play()
			if _bell_t > 0.0:
				_bell_t -= dt
				# 走廊方向是 -z，转到背后就是 yaw 偏离 0 超过 100 度
				var facing := PI / 2 if player.global_position.x - global_position.x < -0.2 else 0.0
				if absf(angle_difference(player.rotation.y, facing)) > deg_to_rad(100.0):
					_bust("铃响的时候，不要回头。")
				if _bell_t <= 0.0:
					_bell_done = true
		2:  # 序章门厅：那句话从身后响起，回答就重来
			if _dist / _path_len > 0.35 and not _answered and _layer_t > 2.0:
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
	if layer == 4:
		_sync_interaction_targets()
	# 换圈只由尽头门的真实 E 入口触发，接近墙面不能跳过交互。


func _stage_prints() -> void:
	if layer != 3:
		return
	for i in _prints.size():
		_prints[i].visible = _dist > float(i) * STEP - 1.6


func _bust(reason: String) -> void:
	if _resetting:
		return
	_resetting = true
	player.frozen = true
	if _scratch.stream:
		_scratch.play()
	Director.ui.toast(reason)
	await get_tree().create_timer(0.7).timeout
	if running:
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
	_bed_fwd.stop()
	_bed_rev.stop()
	if _amb.stream:
		_amb.stop()
	Director.ui.set_hint("")
	sub_label.text = ""
	sub_label.hide()
	player.silent_steps = false
	# 伸手演出由回廊冻结玩家，结束时必须归还移动控制。
	player.frozen = false
	Director.world.highlight_hotspots([])
	done.emit()


## 玩家按 E：回廊里只有三件事
func interact(id: String) -> bool:
	if not running:
		return false
	if id.begins_with("hs_corridor_door_"):
		var n := int(id.get_slice("_", 3))
		if n == layer and not _room_left:
			_part("door_%d" % n).rotation.y = _door_yaws[n] - deg_to_rad(95)
			Director.ui.toast("门开了。脚步声像是拐了进去。")
		return true
	if id.begins_with("hs_room_"):
		var n := int(id.get_slice("_", 2))
		if n == layer:
			if not _room_seen.has(n):
				_room_seen[n] = true
				GameState.record("observation", _room_observations[n-1])
				GameState.add_evidence(ROOM_NOTES[n-1])
				Director.ui.notebook_ping()
				GameState.changed.emit()
			Director.ui.toast(_room_observations[n-1])
		return true
	if id == "hs_corridor_figure" and layer == 5 and _in_photo:
		_touch_figure()
		return true
	if id == "hs_doorway" and layer < 4:
		if _silence_t <= 0.0:
			_next()
		return true
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
		_sit_fourth()
		return true
	return false


## 第四把椅子把玩家送到唱片中心；第六圈继续可走，走近照片进入小路。
func _sit_fourth() -> void:
	_enter(5)
	Director.ui.toast("留声机还在转。尽头的门变成了一张照片。")


func _touch_figure() -> void:
	if _touching:
		return
	_touching = true
	player.frozen = true
	var at := _part("gh_figure").position
	_part("gh_figure").visible = false
	get_node("hs_corridor_figure").visible = false
	Director.world.active_hotspots = []
	player.place(global_position + at, 90.0)
	var e := "res://audio/music/corridor_ending.ogg"
	if ResourceLoader.exists(e):
		_ending.stream = load(e)
		_ending.play()
	await get_tree().create_timer(0.6).timeout
	if not running:
		return
	_fade.color = Color.WHITE
	_fade.modulate.a = 1.0
	var flash := create_tween()
	flash.tween_property(_fade, "modulate:a", 0.0, 1.2)
	await Director.ui.show_text("有人在看着我们。稳定率已经很低了。")
	if running:
		_finish()


## 所有入口统一按当前圈同步，隐藏物体不留下可选热区。
func _sync_interaction_targets() -> void:
	var enabled := []
	if layer in [1, 3]:
		enabled.append("hs_darkroom_door")
	if layer < 4:
		enabled.append("hs_doorway")
	if layer in [1, 2, 3]:
		if not _room_left:
			enabled.append("hs_corridor_door_%d" % layer)
		enabled.append("hs_room_%d" % layer)
	var ready_chair := layer == 4 and _sources.size() == 3 and _sources.all(func(source): return source.found)
	if ready_chair:
		enabled.append("hs_chair4")
	_chairs[3].visible = ready_chair
	if layer == 5 and _in_photo and not _touching:
		enabled.append("hs_corridor_figure")
	for n in find_children("hs_*", "Area3D", true, false):
		n.visible = enabled.has(String(n.name))
	Director.world.active_hotspots = enabled


## 第 3 层：玩家选了“回答”。规矩是不要回答
func answer() -> void:
	if layer != 2 or _answered or _resetting:
		return
	_answered = true
	current_hint = ""
	_bust("有人问你话，不要回答。")


## 玩家按 E 时如果屏幕上有“回答”，就是回答了（第 3 层的陷阱）
func answering() -> bool:
	return layer == 2 and _dist / _path_len > 0.35


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
