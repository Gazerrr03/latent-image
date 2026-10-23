extends SceneTree
## 独立诊断入口，不加载主场景、不读写玩家存档。
var _last_axes := {}
var _heartbeat := 0.0

func _initialize() -> void:
	Input.joy_connection_changed.connect(func(_id, _connected): _devices())
	call_deferred("_devices")

func emit_record(kind: String, data: Dictionary) -> void:
	data["kind"] = kind
	print("PADWATCH ", JSON.stringify(data))

func _devices() -> void:
	var devices: Array = []
	for id in Input.get_connected_joypads():
		devices.append({"id": id, "name": Input.get_joy_name(id), "mapped": Input.is_joy_known(id)})
	emit_record("gamepads", {"devices": devices})

func _process(dt: float) -> bool:
	_heartbeat += dt
	if _heartbeat >= 2.0:
		_heartbeat = 0.0
		_devices()
	for id in Input.get_connected_joypads():
		for axis in range(JOY_AXIS_MAX):
			var value := Input.get_joy_axis(id, axis)
			var key := "%s:%s" % [id, axis]
			var previous := float(_last_axes.get(key, 0.0))
			if absf(value - previous) >= 0.12 or (absf(value) < 0.05 and absf(previous) >= 0.05):
				_last_axes[key] = value
				emit_record("axis", {"id": id, "axis": axis, "value": snappedf(value, 0.01)})
		for button in range(JOY_BUTTON_MAX):
			var key := "b:%s:%s" % [id, button]
			var pressed := Input.is_joy_button_pressed(id, button)
			if pressed != bool(_last_axes.get(key, false)):
				_last_axes[key] = pressed
				emit_record("button", {"id": id, "button": button, "pressed": pressed})
	return false
