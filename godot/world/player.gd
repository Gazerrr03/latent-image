extends CharacterBody3D
## 第一人称行走：慢速、无跑步（P.T. 准则）。看向热区时提示，按 E 或左键检查。
## 步幅计数沿用 three.js 原型的做法，之后用于“脚步声循环”等渗漏表现。

const SPEED := 1.4
const STRIDE := 0.72
const EYE := 1.6
const SENS := 0.0025
const REACH := 2.2
## 能直接迈上去的台阶高度（主楼梯踢面 18 cm）。胶囊体圆底爬不上竖直的踢面，
## 所以胶囊抬高这么多，脚下用一根向下的分离射线站在地上：射线扫到更高的台面，身体就被托上去
const STEP_UP := 0.32
## 上下台阶时视线不跟着一级一级跳，而是平滑地跟上去
const EYE_EASE := 10.0

var cam := Camera3D.new()
var ray := RayCast3D.new()
var active := false
var frozen := false
var needs_spawn := true
var steps := 0
var _stride := 0.0
var _hover := ""
## 准星对着的门（门扇的碰撞体）
var _door: Node = null
var _pitch := 0.0


func _ready() -> void:
	_ensure_input()
	var cs := CollisionShape3D.new()
	var cap := CapsuleShape3D.new()
	cap.radius = 0.3
	cap.height = 1.75 - STEP_UP
	cs.shape = cap
	cs.position.y = STEP_UP + cap.height / 2
	add_child(cs)
	var feet := CollisionShape3D.new()
	var ray_shape := SeparationRayShape3D.new()
	ray_shape.length = STEP_UP + 0.3
	ray_shape.slide_on_slope = false
	feet.shape = ray_shape
	# 射线默认沿本地 +z，转成朝下；起点在胶囊底部的球心
	feet.rotation.x = PI / 2
	feet.position.y = STEP_UP + 0.3
	add_child(feet)
	cam.position.y = EYE
	cam.fov = 70
	cam.near = 0.05
	add_child(cam)
	floor_snap_length = STEP_UP
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
		# 灵敏度与 Y 轴反转来自设置（core/settings.gd）；Esc 由界面层打开暂停页
		var k := SENS * Settings.mouse_scale()
		rotate_y(-event.relative.x * k)
		_pitch = clampf(_pitch - event.relative.y * k * (-1.0 if Settings.invert_y else 1.0), -1.3, 1.3)
		cam.rotation.x = _pitch
	elif event is InputEventMouseButton and event.pressed and Input.mouse_mode != Input.MOUSE_MODE_CAPTURED:
		Input.mouse_mode = Input.MOUSE_MODE_CAPTURED
	elif event.is_action_pressed("interact") or (event is InputEventMouseButton and event.pressed and event.button_index == MOUSE_BUTTON_LEFT):
		if _hover != "":
			Director.inspected.emit(_hover)
		elif _door:
			Director.world.toggle_door(_door, global_position)
			_door = null


func _physics_process(dt: float) -> void:
	if frozen:
		return
	var input := Input.get_vector("move_left", "move_right", "move_forward", "move_back")
	var dir := (transform.basis * Vector3(input.x, 0, input.y)).normalized()
	var before := global_position
	walk(dir, dt)
	_stride += Vector2(global_position.x - before.x, global_position.z - before.z).length()
	if _stride >= STRIDE:
		_stride -= STRIDE
		steps += 1
		Director.world.play_sound(Director.world.footstep_sound())
	_update_hover()


## 走一帧（tools/probe_walk.gd 也直接调用它，用来体检关卡碰撞）
func walk(dir: Vector3, dt: float) -> void:
	velocity.x = dir.x * SPEED
	velocity.z = dir.z * SPEED
	velocity.y = 0.0 if is_on_floor() else velocity.y - 9.8 * dt
	var y0 := global_position.y
	move_and_slide()
	var dy := global_position.y - y0
	if is_on_floor() and absf(dy) > 0.004 and absf(dy) < STEP_UP + 0.05:
		cam.position.y -= dy
	cam.position.y = lerpf(cam.position.y, EYE, clampf(EYE_EASE * dt, 0.0, 1.0))


func _update_hover() -> void:
	var id := ""
	var door: Node = null
	if ray.is_colliding():
		var c := ray.get_collider()
		if c and c.has_meta("hotspot_id") and Director.world.active_hotspots.has(c.get_meta("hotspot_id")):
			id = c.get_meta("hotspot_id")
		elif c and c.has_meta("door"):
			door = c
	if id == _hover and door == _door:
		return
	_hover = id
	_door = door
	if id != "":
		Director.ui.set_hint("E　检查：" + ContentDB.hotspots.get(id, {}).get("label", id))
	elif door:
		Director.ui.set_hint("E　关门" if Director.world.door_is_open(door) else "E　开门")
	else:
		Director.ui.set_hint("")
