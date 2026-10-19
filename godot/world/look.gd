extends RefCounted
## 庄园的“天光”：天空、日光 / 月光、远处的雾、室内灯的强弱，所有房间共用一套（视觉基准与做法见 docs/06 第 9 节）。
## 预设来自 content/visual/look.csv：按当前章日记里的“天气”一行找第一条 match 命中的预设（入夜 → 夜，雾 → 雾……）。
## 每个房间仍保留自己机位环境里的环境光强度、SSAO 等设置，只换天空、雾与色调；
## 机位环境的 metadata/own_look = true 时（暗房、火车）原样使用，不套天光。

const LOOK_TABLE := "res://content/visual/look.csv"
const PANORAMA := "res://art/look/stuttgart_hillside_2k.hdr"
const SKY_SHADER := "res://shaders/sky_panorama.gdshader"
## 调色查找表：暗部偏冷、亮部偏暖、轻微 S 曲线（tools/make_lut.py 生成）。截图对比可加 --lut=off / --lut=neutral
const LUT := "res://art/look/grade_lut.png"

## 灯具发光（按 glTF 材质名认）：灯泡亮、奶白灯罩透光、灯笼玻璃微亮；数字是自发光强度
const PRACTICAL_GLOW := {"manor_室内_灯泡": 4.0, "manor_室内_奶白灯罩": 0.8, "manor_灯笼玻璃": 0.6}
## 灯具附近 0.7 米内没有真灯时补的小灯：暖色、不投影、照亮一小团
const PRACTICAL_COLOR := Color(1.0, 0.76, 0.5)
const PRACTICAL_ENERGY := 0.6
const PRACTICAL_RANGE := 2.6

static var _glow_mats := {}
static var _rows: Array = []
static var _sky_mat: ShaderMaterial
static var _sky: Sky
static var _derived := {}
static var _preset := ""


static func reload() -> void:
	_rows = ContentDB.load_table(LOOK_TABLE)
	_derived.clear()
	_preset = ""


## 当前章的天气 → 预设那一行
static func current() -> Dictionary:
	if _rows.is_empty():
		reload()
	var w := weather()
	for row in _rows:
		var m := String(row.get("match", ""))
		if m != "" and w.contains(m):
			return row
	for row in _rows:
		if String(row.get("match", "")) == "":
			return row
	return {}


## 当前章日记里“天气”那一行（例如“天气：晴。入夜，远处打雷”）
static func weather() -> String:
	var row: Dictionary = ContentDB.shots.get(GameState.shot, {})
	var chapter := String(row.get("node", ""))
	for line in ContentDB.lines.get("diary" + chapter.trim_prefix("C"), []):
		if String(line.get("speaker", "")) == "天气":
			return String(line.get("text", ""))
	return ""


## 预设换了没有（换章时调用方据此重新套一遍）
static func preset_changed() -> bool:
	var name := String(current().get("preset", ""))
	if name == _preset:
		return false
	_preset = name
	_update_sky()
	return true


## 这个环境自己管自己的样子（暗房、火车），不套天光
static func owns(base: Environment) -> bool:
	return base != null and base.get_meta("own_look", false)


## 一个房间的画面环境：以房间自己的环境为底，换上共用的天空与雾
static func env(base: Environment) -> Environment:
	if owns(base):
		return base
	var row := current()
	var key := "%d/%s" % [base.get_instance_id() if base else 0, row.get("preset", "")]
	if _derived.has(key):
		return _derived[key]
	_update_sky()
	var e: Environment = base.duplicate() if base else _template()
	e.background_mode = Environment.BG_SKY
	e.sky = _sky
	var amb := e.ambient_light_energy if e.ambient_light_source != Environment.AMBIENT_SOURCE_DISABLED else 0.3
	e.ambient_light_source = Environment.AMBIENT_SOURCE_SKY
	e.ambient_light_sky_contribution = 1.0
	e.ambient_light_energy = amb * _f(row, "ambient", 1.0)
	e.reflected_light_source = Environment.REFLECTION_SOURCE_SKY
	e.tonemap_mode = Environment.TONE_MAPPER_AGX
	# 远处发灰（空气透视）：雾取天空的颜色，天空本身不被雾盖住
	e.fog_enabled = true
	e.fog_mode = Environment.FOG_MODE_EXPONENTIAL
	e.fog_density = _f(row, "fog_density", 0.008)
	e.fog_aerial_perspective = 0.85
	e.fog_sky_affect = 0.0
	e.fog_light_color = fog_color()
	# 晴天才开体积雾：太阳从窗口斜照进来，空气里看得见光柱（开销较大，只给晴天）
	var vol := _f(row, "vol_fog", 0.0)
	e.volumetric_fog_enabled = vol > 0.0
	e.volumetric_fog_density = vol
	e.volumetric_fog_albedo = Color(0.9, 0.88, 0.84)
	e.volumetric_fog_anisotropy = 0.6
	e.volumetric_fog_length = 16.0
	var lut := _lut()
	e.adjustment_enabled = lut != null
	e.adjustment_color_correction = lut
	e.set_meta("look", true)
	_derived[key] = e
	return e


static func fog_color() -> Color:
	var row := current()
	return Color.from_string(String(row.get("sky_tint", "#c9cdd1")), Color.GRAY) * _f(row, "sky_energy", 0.75) * 0.5


## 日光 / 月光、室内灯：按预设换颜色与强度（原值存在 meta 里，换预设时从原值算）
static func light(l: Light3D) -> void:
	var row := current()
	if not l.has_meta("energy_default"):
		l.set_meta("energy_default", l.light_energy)
	if l is DirectionalLight3D:
		l.light_color = Color.from_string(String(row.get("sun_color", "#dedcd6")), Color.WHITE)
		l.light_energy = _f(row, "sun_energy", 0.45)
		# 太阳阴影是最贵的一项（每帧把整座庄园再画几遍）：室内只要窗口投进来的光斑，两层、24 米够用
		l.directional_shadow_mode = DirectionalLight3D.SHADOW_PARALLEL_2_SPLITS
		l.directional_shadow_max_distance = 24.0
	else:
		l.light_energy = float(l.get_meta("energy_default")) * _f(row, "lamps", 1.0)
		if l is OmniLight3D:
			# 立方体阴影要把房间画 6 遍，双抛物面只画 2 遍；吊灯、灯笼的软影看不出差别
			l.omni_shadow_mode = OmniLight3D.SHADOW_DUAL_PARABOLOID


## 灯具发光的材质（同一种材质共用一份）
static func glow_material(base: Material) -> Material:
	var key := base.resource_name
	if _glow_mats.has(key):
		return _glow_mats[key]
	var m: Material = base
	if base is StandardMaterial3D:
		m = base.duplicate()
		m.emission_enabled = true
		m.emission = PRACTICAL_COLOR.lerp(Color.WHITE, 0.15)
		m.emission_energy_multiplier = float(PRACTICAL_GLOW.get(key, 1.0))
	_glow_mats[key] = m
	return m


## 室内灯的倍数（夜里灯更显眼）
static func lamps() -> float:
	return _f(current(), "lamps", 1.0)


static func _update_sky() -> void:
	var row := current()
	if not _sky_mat:
		_sky_mat = ShaderMaterial.new()
		_sky_mat.shader = load(SKY_SHADER)
		_sky_mat.set_shader_parameter("panorama", load(PANORAMA))
		_sky = Sky.new()
		_sky.sky_material = _sky_mat
		_sky.radiance_size = Sky.RADIANCE_SIZE_128
	var tint := Color.from_string(String(row.get("sky_tint", "#ffffff")), Color.WHITE)
	_sky_mat.set_shader_parameter("tint", Vector3(tint.r, tint.g, tint.b))
	_sky_mat.set_shader_parameter("energy", _f(row, "sky_energy", 0.75))


static func _lut() -> Texture:
	var args := OS.get_cmdline_user_args()
	if args.has("--lut=off"):
		return null
	return load(LUT.replace(".png", "_neutral.png") if args.has("--lut=neutral") else LUT)


## 没有机位环境的地方（庄园外景）用的底子
static func _template() -> Environment:
	var e := Environment.new()
	e.ambient_light_energy = 0.5
	e.ssao_enabled = true
	e.ssao_radius = 0.8
	e.ssil_enabled = true
	e.glow_enabled = true
	e.glow_intensity = 0.35
	return e


static func _f(row: Dictionary, key: String, fallback: float) -> float:
	var v := String(row.get(key, ""))
	return float(v) if v.is_valid_float() else fallback
