extends Node
## 统一动作注册；按物理位置映射，兼容 Godot 识别的 Xbox / PS / Switch 手柄。
signal device_changed
var gamepad := false

func _ready() -> void:
	ensure_actions()
	Input.joy_connection_changed.connect(func(_id, connected):
		if not connected and Input.get_connected_joypads().is_empty():
			_set_gamepad(false))

static func ensure_actions() -> void:
	var keys := {"move_forward": [KEY_W, KEY_UP], "move_back": [KEY_S, KEY_DOWN],
		"move_left": [KEY_A, KEY_LEFT], "move_right": [KEY_D, KEY_RIGHT],
		"interact": [KEY_E], "notebook": [KEY_TAB], "recall": [KEY_Q], "pause": [KEY_ESCAPE]}
	for action in keys:
		if not InputMap.has_action(action): InputMap.add_action(action, 0.2)
		for code in keys[action]:
			var ev := InputEventKey.new()
			ev.physical_keycode = code
			_add(action, ev)
	var buttons := {"interact": JOY_BUTTON_A, "ui_accept": JOY_BUTTON_A,
		"ui_cancel": JOY_BUTTON_B, "notebook": JOY_BUTTON_Y, "recall": JOY_BUTTON_X,
		"pause": JOY_BUTTON_START, "inspect_flip": JOY_BUTTON_RIGHT_STICK, "inspect_read": JOY_BUTTON_A, "inspect_reset": JOY_BUTTON_X,
		"page_prev": JOY_BUTTON_LEFT_SHOULDER, "page_next": JOY_BUTTON_RIGHT_SHOULDER}
	for action in buttons:
		if not InputMap.has_action(action): InputMap.add_action(action, 0.2)
		var ev := InputEventJoypadButton.new()
		ev.device = -1
		ev.button_index = buttons[action]
		_add(action, ev)
	var axes := {"move_left": [JOY_AXIS_LEFT_X, -1.0], "move_right": [JOY_AXIS_LEFT_X, 1.0],
		"move_forward": [JOY_AXIS_LEFT_Y, -1.0], "move_back": [JOY_AXIS_LEFT_Y, 1.0],
		"look_left": [JOY_AXIS_RIGHT_X, -1.0], "look_right": [JOY_AXIS_RIGHT_X, 1.0],
		"look_up": [JOY_AXIS_RIGHT_Y, -1.0], "look_down": [JOY_AXIS_RIGHT_Y, 1.0],
		"inspect_zoom_out": [JOY_AXIS_TRIGGER_LEFT, 1.0], "inspect_zoom_in": [JOY_AXIS_TRIGGER_RIGHT, 1.0]}
	for action in axes:
		if not InputMap.has_action(action): InputMap.add_action(action, 0.2)
		var ev := InputEventJoypadMotion.new()
		ev.device = -1
		ev.axis = axes[action][0]
		ev.axis_value = axes[action][1]
		_add(action, ev)

static func _add(action: String, event: InputEvent) -> void:
	if not InputMap.action_has_event(action, event): InputMap.action_add_event(action, event)

func _input(event: InputEvent) -> void:
	note_event(event)

func note_event(event: InputEvent) -> void:
	if event is InputEventJoypadButton and event.pressed or event is InputEventJoypadMotion and absf(event.axis_value) > 0.25:
		_set_gamepad(true)
	elif event is InputEventKey and event.pressed or event is InputEventMouseButton and event.pressed or event is InputEventMouseMotion and event.relative.length() > 2.0:
		_set_gamepad(false)

func _set_gamepad(value: bool) -> void:
	if gamepad != value:
		gamepad = value
		device_changed.emit()

func look_vector() -> Vector2:
	var v := Input.get_vector("look_left", "look_right", "look_up", "look_down", 0.2)
	return v * v.length()
