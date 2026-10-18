extends CanvasLayer
## 媒介滤镜层：盖在 3D 画面之上、纸质界面之下（文字保持清晰）。
## 预设来自 content/visual/fx.csv：L0—L4 五行跟随渗漏等级自动切换；其余命名预设由镜头表的 fx(名称) 调用。
## fx() 或 fx(自动) 回到跟随渗漏等级。

const FX_TABLE := "res://content/visual/fx.csv"
const PARAMS := [
	"sepia", "desat", "grain", "flicker", "vignette", "scratches", "dust", "weave", "fps",
	"chroma", "scanlines", "tracking", "jitter", "bleed", "glitch",
]

var presets := {}
var current := ""
var _override := ""
var _rect: ColorRect
var _mat: ShaderMaterial
var _tween: Tween


func _ready() -> void:
	layer = 5
	_rect = ColorRect.new()
	_rect.set_anchors_and_offsets_preset(Control.PRESET_FULL_RECT)
	_rect.mouse_filter = Control.MOUSE_FILTER_IGNORE
	_mat = ShaderMaterial.new()
	_mat.shader = load("res://shaders/media_fx.gdshader")
	_rect.material = _mat
	add_child(_rect)
	reload()
	GameState.changed.connect(_follow_leak)
	_follow_leak()
	# 设置里的亮度：画面的 gamma（只作用于 3D 画面，纸质界面不变）
	Settings.changed.connect(func(): _mat.set_shader_parameter("brightness", Settings.gamma()))
	_mat.set_shader_parameter("brightness", Settings.gamma())


func reload() -> void:
	presets.clear()
	for row in ContentDB.load_table(FX_TABLE):
		presets[row["preset"]] = row
	current = ""
	apply(_override if _override != "" else "L%d" % GameState.leak_level, 0.0)


## 由镜头表调用：fx(纪录片片头)；fx() / fx(自动) 回到跟随渗漏
func set_override(name: String) -> void:
	_override = "" if name in ["", "自动"] else name
	apply(_override if _override != "" else "L%d" % GameState.leak_level, 1.2)


func get_override() -> String:
	return _override


func _follow_leak() -> void:
	if _override == "":
		apply("L%d" % GameState.leak_level, 1.5)


## 切换到某个预设，duration 秒内渐变过去
func apply(name: String, duration := 1.0) -> void:
	if name == current:
		return
	if not presets.has(name):
		push_warning("滤镜表里没有预设：" + name)
		return
	current = name
	var row: Dictionary = presets[name]
	if _tween:
		_tween.kill()
	var instant := duration <= 0.0 or Director.autoplay
	if not instant:
		_tween = create_tween().set_parallel()
	for p in PARAMS:
		var v: String = row.get(p, "0")
		var target := float(v) if v.is_valid_float() else 0.0
		if p == "fps":
			_mat.set_shader_parameter(p, target if target > 0 else 18.0)
		elif instant:
			_mat.set_shader_parameter(p, target)
		else:
			_tween.tween_method(func(x): _mat.set_shader_parameter(p, x), float(_mat.get_shader_parameter(p)), target, duration)
	var tint: String = row.get("tint", "")
	if tint != "":
		_mat.set_shader_parameter("tint", Color.from_string(tint, Color("#ffe6bd")))


func set_enabled(on: bool) -> void:
	_rect.visible = on
