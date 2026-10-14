@tool
extends Node3D
## 一次完整的窗景平移。只改变贴图采样，不移动模型或改变烘焙光照。
## C0-02 开始，默认 6 秒到末端并停留；不将非无缝长图强行循环。

@export_range(5.0, 7.0, 0.1) var travel_seconds := 6.0
@export var window_opening_ratio := 1.3125
@export var panorama: Texture2D = preload("res://art/levels/train/textures/window-panorama-lineart.png")
@export var window_surface: NodePath = ^"结构/车厢模型/窗外画面"

var _material: ShaderMaterial
var _elapsed := 0.0
var _playing := false


func _ready() -> void:
	var surface := get_node_or_null(window_surface) as MeshInstance3D
	if surface == null or not surface.material_override is ShaderMaterial:
		return
	# 每个场景实例拥有自己的进度，避免重进关卡继承上一次滚动位置。
	_material = surface.material_override.duplicate() as ShaderMaterial
	surface.material_override = _material
	_material.set_shader_parameter("panorama", panorama)
	_material.set_shader_parameter("visible_fraction", _visible_fraction())
	_material.set_shader_parameter("scroll_progress", 0.0)
	if Engine.is_editor_hint():
		set_process(false)
		return
	var director := get_node_or_null("/root/Director")
	var state := get_node_or_null("/root/GameState")
	if director:
		director.shot_started.connect(_on_shot_started)
	if (state and state.shot == "C0-02") or get_tree().current_scene == self:
		start_panorama()


func _visible_fraction() -> float:
	if panorama == null or panorama.get_width() <= 0:
		return 1.0
	return clampf(window_opening_ratio * panorama.get_height() / panorama.get_width(), 0.01, 1.0)


func texture_pixels_per_second() -> float:
	if panorama == null:
		return 0.0
	return panorama.get_width() * (1.0 - _visible_fraction()) / maxf(travel_seconds, 0.01)


func start_panorama() -> void:
	_elapsed = 0.0
	_playing = true
	if _material:
		_material.set_shader_parameter("scroll_progress", 0.0)


func _on_shot_started(row: Dictionary) -> void:
	if row.get("shot_id", "") == "C0-02":
		start_panorama()
	elif row.get("scene", "") != "train":
		_playing = false


func _process(delta: float) -> void:
	if Engine.is_editor_hint() or not _playing or _material == null:
		return
	_elapsed = minf(_elapsed + delta, travel_seconds)
	_material.set_shader_parameter("scroll_progress", _elapsed / maxf(travel_seconds, 0.01))
	if _elapsed >= travel_seconds:
		_playing = false
