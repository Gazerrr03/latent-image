extends Node3D
## 1924 年餐桌记忆：格雷摆对九件、自动摇铃后的推演。
## 这一段只放“他摆出来的那顿饭”：四个大人 + 南端少年剪影，不出现脸，不出现卢西恩的名字。
## 机位与人物站位先集中在这里，方便整段调整；空间本身仍是 ded_table.tscn。

signal finished

const CAM_WIDE_POS := Vector3(13.95, 2.05, -0.45)
const CAM_WIDE_TARGET := Vector3(15.75, 0.85, -2.40)
const CAM_WIDE_FOV := 54.0
const CAM_CLOSE_POS := Vector3(15.95, 1.02, -1.65)
const CAM_CLOSE_TARGET := Vector3(15.615, 0.86, -1.48)
const CAM_CLOSE_FOV := 30.0
const CUP_POS := Vector3(15.615, 0.862, -1.49)

const FIGURES := {
	"ambrose": {"pos": Vector3(15.75, 0.0, -4.05), "target": Vector3(15.75, 0.0, -2.55)},
	"constance": {"pos": Vector3(16.75, 0.0, -2.55), "target": Vector3(15.75, 0.0, -2.55)},
	"iris": {"pos": Vector3(16.75, 0.0, -3.20), "target": Vector3(15.75, 0.0, -2.55)},
	"gideon": {"pos": Vector3(14.75, 0.0, -2.55), "target": Vector3(15.75, 0.0, -2.55)},
}

var level: Node
var player: Node
var pcam: Camera3D
var cam: Camera3D
var cam_close: Camera3D
var stream: MeshInstance3D
var tea_surface: MeshInstance3D
var steam: Array[MeshInstance3D] = []
var child_root: Node3D
var stage: Node3D
var figures: Array[Node] = []
var saved_lights: Dictionary = {}
var key_light: SpotLight3D
var rim_light: OmniLight3D
var skip_requested := false
var _finished := false
var _active_timer: Timer
var clock_audio: AudioStreamPlayer
var pour_audio: AudioStreamPlayer


func play(level_ref: Node, player_ref: Node) -> void:
	level = level_ref
	player = player_ref
	pcam = player.get("cam") if player else null
	if not (pcam is Camera3D):
		finished.emit()
		return
	if player:
		player.frozen = true
	await Director.ui.eyelids_to(0.0, 0.2)
	_build_stage()
	await _run()
	_restore()
	finished.emit()


func _build_stage() -> void:
	stage = Node3D.new()
	stage.name = "memory_stage"
	add_child(stage)
	# 压暗现在的餐厅
	var lights_root := level.get_node_or_null("灯光")
	if lights_root:
		for n in lights_root.get_children():
			if n is Light3D:
				saved_lights[n] = n.light_energy
				n.light_energy *= 0.18
	key_light = SpotLight3D.new()
	key_light.name = "memory_key"
	key_light.light_color = Color("#ffd0a0")
	key_light.light_energy = 4.0
	key_light.spot_range = 5.0
	key_light.spot_angle = 42.0
	key_light.shadow_enabled = true
	key_light.position = Vector3(14.05, 2.20, 0.20)
	stage.add_child(key_light)
	key_light.look_at(Vector3(15.75, 0.75, -2.55), Vector3.UP)
	rim_light = OmniLight3D.new()
	rim_light.name = "memory_rim"
	rim_light.light_color = Color("#a8bdd8")
	rim_light.light_energy = 1.5
	rim_light.omni_range = 4.0
	rim_light.position = Vector3(16.55, 1.65, -3.55)
	stage.add_child(rim_light)
	var back_light := OmniLight3D.new()
	back_light.name = "memory_back"
	back_light.light_color = Color("#ffd6a6")
	back_light.light_energy = 1.3
	back_light.omni_range = 2.6
	back_light.position = Vector3(15.35, 1.75, 0.05)
	stage.add_child(back_light)
	var fill := OmniLight3D.new()
	fill.name = "memory_fill"
	fill.light_color = Color("#ffe2c0")
	fill.light_energy = 0.55
	fill.omni_range = 3.5
	fill.position = Vector3(15.75, 2.25, -2.50)
	stage.add_child(fill)
	_build_figures()
	cam = Camera3D.new()
	cam.name = "cam_memory_wide"
	cam.fov = CAM_WIDE_FOV
	cam.near = 0.03
	cam.environment = pcam.environment
	stage.add_child(cam)
	cam.global_position = CAM_WIDE_POS
	cam.look_at(CAM_WIDE_TARGET, Vector3.UP)
	cam.current = true
	cam_close = Camera3D.new()
	cam_close.name = "cam_memory_close"
	cam_close.fov = CAM_CLOSE_FOV
	cam_close.near = 0.02
	cam_close.environment = pcam.environment
	stage.add_child(cam_close)
	cam_close.global_position = CAM_CLOSE_POS
	cam_close.look_at(CAM_CLOSE_TARGET, Vector3.UP)
	_build_pour()
	clock_audio = AudioStreamPlayer.new()
	clock_audio.stream = load("res://audio/sfx/clock_tick.ogg")
	clock_audio.volume_db = -14.0
	stage.add_child(clock_audio)
	pour_audio = AudioStreamPlayer.new()
	pour_audio.stream = load("res://audio/sfx/tea_pour.wav")
	pour_audio.volume_db = -12.0
	stage.add_child(pour_audio)


func _build_figures() -> void:
	for id in FIGURES:
		var data: Dictionary = FIGURES[id]
		var n := _make_adult(id, data["pos"], data["target"])
		if n:
			figures.append(n)
	figures.append(_make_child())


func _make_adult(id: String, pos: Vector3, target: Vector3) -> Node3D:
	var ps: PackedScene = load("res://art/characters/char_%s.glb" % id)
	if ps == null:
		return null
	var n := ps.instantiate()
	stage.add_child(n)
	n.global_position = pos
	# 方盒子模型的正面是 +Z：北 0°，东 -90°，西 +90°
	var yaw := 0.0
	match id:
		"constance", "iris":
			yaw = -90.0
		"gideon":
			yaw = 90.0
	n.rotation = Vector3(0, deg_to_rad(yaw), 0)
	var aps := n.find_children("*", "AnimationPlayer", true, false)
	for ap in aps:
		if ap.has_animation("sit"):
			ap.play("sit")
			ap.seek(maxf(ap.current_animation_length - 0.02, 0.0), true)
			ap.pause()
	return n


func _make_child() -> Node3D:
	var root := Node3D.new()
	child_root = root
	root.name = "memory_child"
	root.position = Vector3(15.55, 0.0, -1.08)
	root.rotation.y = PI
	stage.add_child(root)
	var mat := _dark_material()
	# 坐姿：髋、躯干、头、腿、臂；不做脸
	_add_box(root, Vector3(0.24, 0.16, 0.18), Vector3(0, 0.48, 0), mat)
	_add_box(root, Vector3(0.26, 0.30, 0.15), Vector3(0, 0.68, 0), mat)
	var head := SphereMesh.new()
	head.radius = 0.085
	head.height = 0.17
	_add_mesh(root, head, mat, Vector3(0, 0.91, 0))
	for sx in [-1.0, 1.0]:
		_add_box(root, Vector3(0.08, 0.08, 0.22), Vector3(sx * 0.10, 0.47, 0.10), mat)
		_add_box(root, Vector3(0.07, 0.30, 0.07), Vector3(sx * 0.10, 0.30, 0.20), mat)
		_add_box(root, Vector3(0.07, 0.26, 0.07), Vector3(sx * 0.17, 0.66, 0.02), mat)
	return root


func _darken(root: Node) -> void:
	var mat := _dark_material()
	for n in root.find_children("*", "MeshInstance3D", true, false):
		n.material_override = mat
		n.cast_shadow = GeometryInstance3D.SHADOW_CASTING_SETTING_ON


func _dark_material() -> StandardMaterial3D:
	var m := StandardMaterial3D.new()
	m.albedo_color = Color("#221a15")
	m.roughness = 0.95
	m.metallic = 0.0
	return m


func _add_box(parent: Node3D, size: Vector3, pos: Vector3, mat: Material) -> void:
	var mesh := BoxMesh.new()
	mesh.size = size
	_add_mesh(parent, mesh, mat, pos)


func _add_mesh(parent: Node3D, mesh: Mesh, mat: Material, pos: Vector3) -> void:
	var mi := MeshInstance3D.new()
	mi.mesh = mesh
	mi.material_override = mat
	mi.position = pos
	parent.add_child(mi)


func _build_pour() -> void:
	tea_surface = MeshInstance3D.new()
	var disc := CylinderMesh.new()
	disc.top_radius = 0.025
	disc.bottom_radius = 0.025
	disc.height = 0.001
	tea_surface.mesh = disc
	var tea_mat := StandardMaterial3D.new()
	tea_mat.albedo_color = Color("#3a2114")
	tea_mat.roughness = 0.18
	tea_surface.material_override = tea_mat
	tea_surface.position = CUP_POS + Vector3(0, 0.001, 0)
	tea_surface.visible = false
	stage.add_child(tea_surface)
	stream = MeshInstance3D.new()
	var cyl := CylinderMesh.new()
	cyl.top_radius = 0.0014
	cyl.bottom_radius = 0.0020
	cyl.height = 0.17
	stream.mesh = cyl
	var stream_mat := StandardMaterial3D.new()
	stream_mat.albedo_color = Color(0.36, 0.20, 0.08, 0.38)
	stream_mat.transparency = BaseMaterial3D.TRANSPARENCY_ALPHA
	stream_mat.emission_enabled = true
	stream_mat.emission = Color("#3a1c08")
	stream_mat.emission_energy_multiplier = 0.35
	stream.material_override = stream_mat
	stream.position = CUP_POS + Vector3(0, 0.085, 0.012)
	stream.scale = Vector3(1, 0.03, 1)
	stream.visible = false
	stage.add_child(stream)
	var steam_mat := StandardMaterial3D.new()
	steam_mat.albedo_color = Color(0.9, 0.86, 0.8, 0.07)
	steam_mat.transparency = BaseMaterial3D.TRANSPARENCY_ALPHA
	steam_mat.shading_mode = BaseMaterial3D.SHADING_MODE_UNSHADED
	for i in 4:
		var p := SphereMesh.new()
		p.radius = 0.008
		p.height = 0.016
		var s := MeshInstance3D.new()
		s.mesh = p
		s.material_override = steam_mat
		s.position = CUP_POS + Vector3((i - 1.5) * 0.016, 0.045 + i * 0.014, 0.012)
		s.visible = false
		stage.add_child(s)
		steam.append(s)
	var close_light := OmniLight3D.new()
	close_light.light_color = Color("#ffd3a3")
	close_light.light_energy = 1.4
	close_light.omni_range = 1.8
	close_light.position = Vector3(16.0, 1.35, -1.25)
	stage.add_child(close_light)


func _pour_shot() -> void:
	cam.current = false
	cam_close.current = true
	if child_root:
		child_root.visible = false
	tea_surface.visible = true
	stream.visible = true
	if pour_audio: pour_audio.play()
	var tw := create_tween()
	tw.tween_property(stream, "scale:y", 1.0, 0.22)
	await tw.finished
	for s in steam:
		s.visible = true
		var st := create_tween().set_parallel(true)
		st.tween_property(s, "position:y", s.position.y + 0.13, 2.2)
		st.tween_property(s, "scale", Vector3(0.25, 0.25, 0.25), 2.2)
	await _wait(2.0)
	stream.visible = false
	tea_surface.visible = false
	for s in steam:
		s.visible = false
	cam_close.current = false
	if child_root:
		child_root.visible = true
	cam.current = true


func _run() -> void:
	await _fade(1.0, 0.0, 0.8)
	await _wait(0.5)
	if clock_audio: clock_audio.play()
	await _say("1924 年，这张桌子上有五个人。", 2.8)
	if skip_requested:
		return
	await _wait(0.3)
	await _pour_shot()
	if skip_requested:
		return
	await _wait(0.3)
	if clock_audio: clock_audio.play()
	await _say("南边那个位置，是卢西恩的。", 2.8)
	await _wait(0.5)
	await get_tree().create_timer(0.1).timeout


func _say(text: String, _hold: float) -> void:
	await Director.ui.show_text(text)


func _fade(_from_a: float, to_a: float, duration: float) -> void:
	await Director.ui.eyelids_to(1.0 - to_a, duration)


func _wait(seconds: float) -> void:
	var timer := Timer.new()
	timer.one_shot = true
	timer.wait_time = seconds
	add_child(timer)
	_active_timer = timer
	timer.start()
	await timer.timeout
	_active_timer = null
	timer.queue_free()


func _unhandled_input(event: InputEvent) -> void:
	if skip_requested:
		return
	if event is InputEventKey and event.pressed and not event.echo and event.physical_keycode == KEY_E:
		skip_requested = true
		if _active_timer:
			_active_timer.stop()
			_active_timer.timeout.emit()
	elif event is InputEventMouseButton and event.pressed and event.button_index == MOUSE_BUTTON_LEFT:
		skip_requested = true
		if _active_timer:
			_active_timer.stop()
			_active_timer.timeout.emit()


func _restore() -> void:
	if _finished:
		return
	_finished = true
	if pcam:
		pcam.current = true
	for n in saved_lights:
		if is_instance_valid(n):
			n.light_energy = saved_lights[n]
	Director.ui.eyelids_set(1.0)
	stage.queue_free()
