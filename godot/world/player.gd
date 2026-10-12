extends CharacterBody3D
## 第一人称行走：慢速、无跑步（P.T. 准则）。看向热区时提示，按 E 或左键检查。
## 步幅计数沿用 three.js 原型的做法，之后用于“脚步声循环”等渗漏表现。

const SPEED := 1.4
const STRIDE := 0.72
const EYE := 1.6
const SENS := 0.0025
const REACH := 2.2

var cam := Camera3D.new()
var ray := RayCast3D.new()
var active := false
var frozen := false
var needs_spawn := true
var steps := 0
var _stride := 0.0
var _hover := ""
var _pitch := 0.0


func _ready() -> void:
	_ensure_input()
	var cs := CollisionShape3D.new()
	var cap := CapsuleShape3D.new()
	cap.radius = 0.3
	cap.height = 1.75
	cs.shape = cap
	cs.position.y = 0.875
	add_child(cs)
	cam.position.y = EYE
	cam.fov = 70
	cam.near = 0.05
	add_child(cam)
	ray.target_position = Vector3(0, 0, -REACH)
	ray.collide_with_areas = true
	ray.collision_mask = 1 | 2
	cam.add_child(ray)
	visible = false
	set_physics_process(false)


static func _ensure_input() -> void:
	var keys := {
		"move_forward": [KEY_W, KEY_UP], "move_back": [KEY_S, KEY_DOWN],
		"move_left": [KEY_A, KEY_LEFT], "move_right": [KEY_D, KEY_RIGHT],
		"interact": [KEY_E],
	}
	for action in keys:
		if InputMap.has_action(action):
			continue
		InputMap.add_action(action)
		for k in keys[action]:
			var ev := InputEventKey.new()
			ev.physical_keycode = k
			InputMap.action_add_event(action, ev)


func place(pos: Vector3, yaw_deg: float) -> void:
	global_position = pos
	rotation = Vector3(0, deg_to_rad(yaw_deg), 0)
	_pitch = 0.0
	cam.rotation = Vector3.ZERO
	velocity = Vector3.ZERO
	needs_spawn = false


func activate() -> void:
	active = true
	visible = true
	cam.current = true
	set_physics_process(true)
	if not Director.autoplay:
		Input.mouse_mode = Input.MOUSE_MODE_CAPTURED


func deactivate() -> void:
	if not active:
		return
	active = false
	set_physics_process(false)
	Director.ui.set_hint("")
	Input.mouse_mode = Input.MOUSE_MODE_VISIBLE


func _unhandled_input(event: InputEvent) -> void:
	if not active or frozen:
		return
	if event is InputEventMouseMotion and Input.mouse_mode == Input.MOUSE_MODE_CAPTURED:
		rotate_y(-event.relative.x * SENS)
		_pitch = clampf(_pitch - event.relative.y * SENS, -1.3, 1.3)
		cam.rotation.x = _pitch
	elif event.is_action_pressed("ui_cancel"):
		Input.mouse_mode = Input.MOUSE_MODE_VISIBLE
	elif event is InputEventMouseButton and event.pressed and Input.mouse_mode != Input.MOUSE_MODE_CAPTURED:
		Input.mouse_mode = Input.MOUSE_MODE_CAPTURED
	elif event.is_action_pressed("interact") or (event is InputEventMouseButton and event.pressed and event.button_index == MOUSE_BUTTON_LEFT):
		if _hover != "":
			Director.inspected.emit(_hover)


func _physics_process(dt: float) -> void:
	if frozen:
		return
	var input := Input.get_vector("move_left", "move_right", "move_forward", "move_back")
	var dir := (transform.basis * Vector3(input.x, 0, input.y)).normalized()
	velocity.x = dir.x * SPEED
	velocity.z = dir.z * SPEED
	velocity.y = 0.0 if is_on_floor() else velocity.y - 9.8 * dt
	var before := global_position
	move_and_slide()
	_stride += Vector2(global_position.x - before.x, global_position.z - before.z).length()
	if _stride >= STRIDE:
		_stride -= STRIDE
		steps += 1
		Director.world.play_sound("footstep_wood")
	_update_hover()


func _update_hover() -> void:
	var id := ""
	if ray.is_colliding():
		var c := ray.get_collider()
		if c and c.has_meta("hotspot_id"):
			id = c.get_meta("hotspot_id")
	if id == _hover:
		return
	_hover = id
	var label: String = ContentDB.hotspots.get(id, {}).get("label", id)
	Director.ui.set_hint("" if id == "" else "E　检查：" + label)
