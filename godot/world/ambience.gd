extends Node3D
## 氛围粒子：室内光里飘的灰尘、壁炉的火星和火光跳动、室外的雨丝（docs/06 第 9 节）。
## 都跟着当前相机走，数量很少；灰尘用受光材质，只在有光的地方看得见。

const DUST_BOX := Vector3(3.0, 1.4, 3.0)
const RAIN_BOX := Vector3(14.0, 6.0, 14.0)
const FIRE_NAMES := ["炉火", "烛光"]
const Look := preload("res://world/look.gd")

var host: Node
var rain: Node
var _dust: GPUParticles3D
var _rain: GPUParticles3D
var _fires: Array = []
var _room_id := 0
var _t := 0.0


func _ready() -> void:
	_dust = _particles(90, 9.0, _dust_material(), _dust_process(), 0.006)
	_rain = _particles(900, 0.7, _rain_material(), _rain_process(), 0.0)
	add_child(_dust)
	add_child(_rain)
	_rain.draw_pass_1 = _streak_mesh()
	_rain.emitting = false


func _process(dt: float) -> void:
	_t += dt
	var cam := get_viewport().get_camera_3d()
	if cam == null:
		return
	var p := cam.global_position
	var outdoors: bool = rain.has_method("_outdoors") and host and host.room and rain._outdoors(p)
	_dust.global_position = p
	_dust.emitting = not outdoors and GameState.leak_level < 3
	var wet: bool = outdoors and rain.raining()
	_rain.global_position = p + Vector3(0, 2.5, 0)
	if _rain.emitting != wet:
		_rain.emitting = wet
	_refresh_fires()
	for f in _fires:
		var l: Light3D = f["light"]
		if not is_instance_valid(l):
			continue
		# 火光：两个频率叠起来的轻微跳动
		var base := float(l.get_meta("energy_default", l.light_energy)) * Look.lamps()
		var k := 1.0 + 0.12 * sin(_t * 9.0 + f["phase"]) + 0.08 * sin(_t * 23.0 + f["phase"] * 2.0)
		l.light_energy = base * k


## 换了房间（或大地图）时，重新找壁炉、蜡烛的灯，给壁炉加火星
func _refresh_fires() -> void:
	var r: Node = host.room if host else null
	var id := r.get_instance_id() if r else 0
	if id == _room_id:
		return
	_room_id = id
	for f in _fires:
		if is_instance_valid(f["sparks"]):
			f["sparks"].queue_free()
	_fires.clear()
	if r == null:
		return
	var stack: Array = [r]
	while not stack.is_empty():
		var n: Node = stack.pop_back()
		stack.append_array(n.get_children())
		if n is OmniLight3D and FIRE_NAMES.has(String(n.name)):
			if not n.has_meta("energy_default"):
				n.set_meta("energy_default", n.light_energy)
			var sparks: GPUParticles3D = null
			if String(n.name) == "炉火":
				sparks = _particles(10, 1.6, _ember_material(), _ember_process(), 0.012)
				n.add_child(sparks)
			_fires.append({"light": n, "sparks": sparks, "phase": randf() * TAU})


func _particles(amount: int, life: float, mat: Material, proc: ParticleProcessMaterial, size: float) -> GPUParticles3D:
	var g := GPUParticles3D.new()
	g.amount = amount
	g.lifetime = life
	g.preprocess = life
	g.local_coords = false
	g.process_material = proc
	g.cast_shadow = GeometryInstance3D.SHADOW_CASTING_SETTING_OFF
	g.visibility_aabb = AABB(-RAIN_BOX, RAIN_BOX * 2.0)
	if size > 0.0:
		var q := QuadMesh.new()
		q.size = Vector2(size, size)
		q.material = mat
		g.draw_pass_1 = q
	else:
		g.material_override = mat
	return g


func _dust_process() -> ParticleProcessMaterial:
	var m := ParticleProcessMaterial.new()
	m.emission_shape = ParticleProcessMaterial.EMISSION_SHAPE_BOX
	m.emission_box_extents = DUST_BOX
	m.direction = Vector3(0, 1, 0)
	m.spread = 180.0
	m.initial_velocity_min = 0.005
	m.initial_velocity_max = 0.03
	m.gravity = Vector3(0, -0.004, 0)
	m.turbulence_enabled = true
	m.turbulence_noise_strength = 0.3
	m.turbulence_noise_speed_random = 0.2
	m.scale_min = 0.6
	m.scale_max = 1.4
	var fade := Curve.new()
	fade.add_point(Vector2(0.0, 0.0))
	fade.add_point(Vector2(0.2, 1.0))
	fade.add_point(Vector2(0.8, 1.0))
	fade.add_point(Vector2(1.0, 0.0))
	var ct := CurveTexture.new()
	ct.curve = fade
	m.alpha_curve = ct
	return m


func _dust_material() -> StandardMaterial3D:
	# 受光：暗处看不见，窗边和灯下才亮
	var m := StandardMaterial3D.new()
	m.transparency = BaseMaterial3D.TRANSPARENCY_ALPHA
	m.billboard_mode = BaseMaterial3D.BILLBOARD_PARTICLES
	m.albedo_color = Color(1.0, 0.97, 0.9, 0.55)
	m.vertex_color_use_as_albedo = true
	m.roughness = 1.0
	m.disable_receive_shadows = true
	return m


func _ember_process() -> ParticleProcessMaterial:
	var m := ParticleProcessMaterial.new()
	m.emission_shape = ParticleProcessMaterial.EMISSION_SHAPE_BOX
	m.emission_box_extents = Vector3(0.18, 0.05, 0.08)
	m.direction = Vector3(0, 1, 0)
	m.spread = 20.0
	m.initial_velocity_min = 0.25
	m.initial_velocity_max = 0.55
	m.gravity = Vector3(0, 0.1, 0)
	m.turbulence_enabled = true
	m.turbulence_noise_strength = 0.6
	var fade := Curve.new()
	fade.add_point(Vector2(0.0, 1.0))
	fade.add_point(Vector2(1.0, 0.0))
	var ct := CurveTexture.new()
	ct.curve = fade
	m.scale_curve = ct
	return m


func _ember_material() -> StandardMaterial3D:
	var m := StandardMaterial3D.new()
	m.shading_mode = BaseMaterial3D.SHADING_MODE_UNSHADED
	m.billboard_mode = BaseMaterial3D.BILLBOARD_PARTICLES
	m.transparency = BaseMaterial3D.TRANSPARENCY_ALPHA
	m.blend_mode = BaseMaterial3D.BLEND_MODE_ADD
	m.albedo_color = Color(1.0, 0.55, 0.2, 0.9)
	return m


func _rain_process() -> ParticleProcessMaterial:
	var m := ParticleProcessMaterial.new()
	m.emission_shape = ParticleProcessMaterial.EMISSION_SHAPE_BOX
	m.emission_box_extents = RAIN_BOX * 0.5
	m.direction = Vector3(0.08, -1, 0.04)
	m.spread = 2.0
	m.initial_velocity_min = 9.0
	m.initial_velocity_max = 11.0
	m.gravity = Vector3.ZERO
	m.particle_flag_align_y = true
	return m


func _rain_material() -> StandardMaterial3D:
	var m := StandardMaterial3D.new()
	m.shading_mode = BaseMaterial3D.SHADING_MODE_UNSHADED
	m.transparency = BaseMaterial3D.TRANSPARENCY_ALPHA
	m.billboard_mode = BaseMaterial3D.BILLBOARD_FIXED_Y
	m.billboard_keep_scale = true
	m.albedo_color = Color(0.75, 0.8, 0.85, 0.18)
	m.disable_receive_shadows = true
	return m


func _streak_mesh() -> QuadMesh:
	var q := QuadMesh.new()
	q.size = Vector2(0.008, 0.45)
	return q
