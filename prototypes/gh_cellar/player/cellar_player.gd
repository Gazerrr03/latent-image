extends CharacterBody3D
## 第一人称：WASD、鼠标视角、E 检查、F 举镜、滚轮对焦、左键快门、
## R 二次曝光、Tab 记录本。相机模式只改手感与取景，规则在 CellarState。

signal camera_toggle_requested
signal interact_pressed
signal shutter_pressed
signal focus_step_requested(direction: float)
signal second_exposure_requested
signal notebook_requested

const SPEED := 2.2
const CAMERA_SPEED := 1.05
const EYE := 1.6
const SENS := 0.0022
const PITCH_LIMIT := 1.35
const REACH := 2.6

var camera: Camera3D
var ray: RayCast3D
var viewmodel: Node3D
var camera_raised := false
var ui_locked := false
var has_camera := false
var _pitch := 0.0
var _captured := true
var _fov := 70.0


func _ready() -> void:
	_ensure_input()
	camera = $Camera3D
	camera.position.y = EYE
	camera.near = 0.04
	camera.far = 80.0
	camera.fov = _fov
	floor_snap_length = 0.35
	floor_max_angle = deg_to_rad(50.0)

	ray = RayCast3D.new()
	ray.name = "InteractRay"
	ray.target_position = Vector3(0.0, 0.0, -REACH)
	ray.collide_with_areas = true
	ray.collide_with_bodies = true
	ray.collision_mask = 1 | 2
	ray.enabled = true
	camera.add_child(ray)

	_build_viewmodel()
	Input.mouse_mode = Input.MOUSE_MODE_CAPTURED
	_captured = true


static func _ensure_input() -> void:
	var keys := {
		"move_forward": [KEY_W, KEY_UP],
		"move_back": [KEY_S, KEY_DOWN],
		"move_left": [KEY_A, KEY_LEFT],
		"move_right": [KEY_D, KEY_RIGHT],
	}
	for action in keys:
		if InputMap.has_action(action):
			continue
		InputMap.add_action(action)
		for k in keys[action]:
			var ev := InputEventKey.new()
			ev.physical_keycode = k
			InputMap.action_add_event(action, ev)


func _build_viewmodel() -> void:
	viewmodel = Node3D.new()
	viewmodel.name = "CameraViewmodel"
	viewmodel.position = Vector3(0.29, -0.215, -0.62)
	viewmodel.rotation_degrees = Vector3(-3, -18, 0)
	viewmodel.visible = false
	camera.add_child(viewmodel)
	var wood := StandardMaterial3D.new()
	wood.albedo_color = Color(0.20, 0.10, 0.048)
	wood.roughness = 0.5
	wood.metallic = 0.02
	wood.emission_enabled = true
	wood.emission = Color(0.05, 0.022, 0.008)
	wood.emission_energy_multiplier = 0.8
	var leather := StandardMaterial3D.new()
	leather.albedo_color = Color(0.045, 0.028, 0.018)
	leather.roughness = 0.8
	var brass := StandardMaterial3D.new()
	brass.albedo_color = Color(0.55, 0.36, 0.11)
	brass.metallic = 0.85
	brass.roughness = 0.32
	brass.emission_enabled = true
	brass.emission = Color(0.08, 0.045, 0.01)
	brass.emission_energy_multiplier = 0.5
	var body := MeshInstance3D.new()
	var bm := BoxMesh.new()
	bm.size = Vector3(0.155, 0.092, 0.115)
	body.mesh = bm
	body.material_override = wood
	viewmodel.add_child(body)
	var bellows := MeshInstance3D.new()
	var bm2 := BoxMesh.new()
	bm2.size = Vector3(0.09, 0.074, 0.075)
	bellows.mesh = bm2
	bellows.position = Vector3(-0.028, 0, 0.063)
	bellows.material_override = leather
	viewmodel.add_child(bellows)
	var lens := MeshInstance3D.new()
	var cm := CylinderMesh.new()
	cm.top_radius = 0.035
	cm.bottom_radius = 0.044
	cm.height = 0.085
	lens.mesh = cm
	lens.rotation_degrees.x = 90.0
	lens.position = Vector3(-0.015, 0.0, -0.105)
	lens.material_override = brass
	viewmodel.add_child(lens)
	var glass := MeshInstance3D.new()
	var gm := CylinderMesh.new()
	gm.top_radius = 0.029
	gm.bottom_radius = 0.029
	gm.height = 0.007
	glass.mesh = gm
	glass.rotation_degrees.x = 90.0
	glass.position = Vector3(-0.015, 0.0, -0.151)
	var gm2 := StandardMaterial3D.new()
	gm2.albedo_color = Color(0.015, 0.075, 0.078)
	gm2.metallic = 0.0
	gm2.roughness = 0.05
	glass.material_override = gm2
	viewmodel.add_child(glass)
	# top winding knob and the small red frame counter
	var knob := MeshInstance3D.new()
	var km := CylinderMesh.new()
	km.top_radius = 0.013
	km.bottom_radius = 0.015
	km.height = 0.025
	knob.mesh = km
	knob.position = Vector3(0.038, 0.058, 0.012)
	knob.material_override = brass
	viewmodel.add_child(knob)
	var window := MeshInstance3D.new()
	var wm := BoxMesh.new()
	wm.size = Vector3(0.022, 0.010, 0.005)
	window.mesh = wm
	window.position = Vector3(0.03, 0.05, -0.045)
	var wmat := StandardMaterial3D.new()
	wmat.albedo_color = Color(0.35, 0.012, 0.006)
	wmat.emission_enabled = true
	wmat.emission = Color(0.75, 0.03, 0.01)
	wmat.emission_energy_multiplier = 2.5
	window.material_override = wmat
	viewmodel.add_child(window)
	# rear eyepiece, visible from the player's side
	var eye := MeshInstance3D.new()
	var em := CylinderMesh.new()
	em.top_radius = 0.018
	em.bottom_radius = 0.021
	em.height = 0.028
	eye.mesh = em
	eye.rotation_degrees.x = 90.0
	eye.position = Vector3(-0.025, 0.005, 0.072)
	eye.material_override = brass
	viewmodel.add_child(eye)
	var eyeglass := MeshInstance3D.new()
	var egm := CylinderMesh.new()
	egm.top_radius = 0.014
	egm.bottom_radius = 0.014
	egm.height = 0.004
	eyeglass.mesh = egm
	eyeglass.rotation_degrees.x = 90.0
	eyeglass.position = Vector3(-0.025, 0.005, 0.088)
	var egmat := StandardMaterial3D.new()
	egmat.albedo_color = Color(0.01, 0.02, 0.025)
	egmat.roughness = 0.05
	eyeglass.material_override = egmat
	viewmodel.add_child(eyeglass)


func place(pos: Vector3, yaw_deg := 0.0) -> void:
	global_position = pos
	rotation = Vector3(0.0, deg_to_rad(yaw_deg), 0.0)
	_pitch = 0.0
	if camera:
		camera.rotation = Vector3.ZERO
	velocity = Vector3.ZERO


func set_camera_mode(on: bool) -> void:
	camera_raised = on
	_camera_mode_visual(on)


func _camera_mode_visual(on: bool) -> void:
	if camera:
		camera.fov = 48.0 if on else _fov
	if viewmodel:
		viewmodel.visible = on


func set_has_camera(value: bool) -> void:
	has_camera = value


func set_ui_locked(value: bool) -> void:
	ui_locked = value
	if value:
		velocity = Vector3.ZERO
		Input.mouse_mode = Input.MOUSE_MODE_VISIBLE
	elif _captured:
		Input.mouse_mode = Input.MOUSE_MODE_CAPTURED


func get_target_area() -> Area3D:
	if ray and ray.is_colliding():
		var c := ray.get_collider()
		if c is Area3D:
			return c
	return null


func _unhandled_input(event: InputEvent) -> void:
	if event is InputEventKey and event.pressed and not event.echo:
		if event.keycode == KEY_ESCAPE:
			_set_captured(false)
			return
		if ui_locked:
			return
		match event.keycode:
			KEY_E:
				interact_pressed.emit()
			KEY_F:
				camera_toggle_requested.emit()
			KEY_R:
				second_exposure_requested.emit()
			KEY_TAB:
				notebook_requested.emit()
		return

	if ui_locked:
		return

	if event is InputEventMouseMotion and _captured:
		var scale := 0.8 if camera_raised else 1.0
		rotate_y(-event.relative.x * SENS * scale)
		_pitch = clampf(_pitch - event.relative.y * SENS * scale, -PITCH_LIMIT, PITCH_LIMIT)
		camera.rotation.x = _pitch
	elif event is InputEventMouseButton and event.pressed:
		match event.button_index:
			MOUSE_BUTTON_LEFT:
				if _captured and camera_raised:
					shutter_pressed.emit()
				elif not _captured:
					_set_captured(true)
			MOUSE_BUTTON_WHEEL_UP:
				if camera_raised:
					focus_step_requested.emit(1.0)
			MOUSE_BUTTON_WHEEL_DOWN:
				if camera_raised:
					focus_step_requested.emit(-1.0)
			_:
				if not _captured:
					_set_captured(true)


func _set_captured(value: bool) -> void:
	_captured = value
	if ui_locked:
		Input.mouse_mode = Input.MOUSE_MODE_VISIBLE
	else:
		Input.mouse_mode = Input.MOUSE_MODE_CAPTURED if value else Input.MOUSE_MODE_VISIBLE


func walk(dir: Vector3, dt: float) -> void:
	if not is_on_floor():
		velocity.y -= 9.8 * dt
	else:
		velocity.y = 0.0
	var speed := CAMERA_SPEED if camera_raised else SPEED
	velocity.x = dir.x * speed
	velocity.z = dir.z * speed
	move_and_slide()


func _physics_process(dt: float) -> void:
	if ui_locked:
		velocity = Vector3.ZERO
		return
	var input := Input.get_vector("move_left", "move_right", "move_forward", "move_back")
	var dir := (transform.basis * Vector3(input.x, 0.0, input.y)).normalized()
	walk(dir, dt)
