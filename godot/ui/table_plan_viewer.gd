extends CanvasLayer
## Persistent, front-on plan. Only explicit close dismisses it; world input stays frozen.
signal closed
var zoom := 1.0
var pan := Vector2.ZERO
var _dragging := false
var _paper: TextureRect
var _canvas: Control
var _percent: Label
var _bar: HBoxContainer
var _help: Label
var _mouse_before: int
var _frozen_before: bool
var _hud: Array = []
var _visibility: Array = []
var _active := false

func open() -> void:
	layer = 80
	_active = true
	_mouse_before = Input.mouse_mode
	_frozen_before = Director.world.player.frozen
	Director.world.set_frozen(true)
	Input.mouse_mode = Input.MOUSE_MODE_VISIBLE
	for control in [Director.ui.objective_label, Director.ui.crosshair, Director.ui.hint_box, Director.ui.keys, Director.ui.day_label, Director.ui.room_label, Director.ui.checklist_box, Director.ui.progress_label]:
		_hud.append(control)
		_visibility.append(control.visible)
		control.hide()
	var shade := ColorRect.new()
	shade.color = Color(0.025, 0.023, 0.02, 0.96)
	shade.set_anchors_and_offsets_preset(Control.PRESET_FULL_RECT)
	add_child(shade)
	_canvas = Control.new()
	_canvas.set_anchors_and_offsets_preset(Control.PRESET_FULL_RECT)
	_canvas.offset_bottom = -120
	_canvas.mouse_filter = Control.MOUSE_FILTER_IGNORE
	_canvas.clip_contents = true
	add_child(_canvas)
	_paper = TextureRect.new()
	_paper.texture = load("res://art/footage/ded_table_blueprint.png")
	_paper.expand_mode = TextureRect.EXPAND_IGNORE_SIZE
	_paper.mouse_filter = Control.MOUSE_FILTER_IGNORE
	_canvas.add_child(_paper)
	var bar := HBoxContainer.new()
	_bar = bar
	bar.add_theme_constant_override("separation", 16)
	add_child(bar)
	for spec in [["− 缩小", -1], ["＋ 放大", 1], ["适合窗口", 0], ["Esc 收起", 2]]:
		var button := Button.new()
		button.text = spec[0]
		button.custom_minimum_size = Vector2(130, 44)
		var action: int = spec[1]
		button.pressed.connect(func():
			if action == 2: close()
			elif action == 0:
				zoom = 1.0
				pan = Vector2.ZERO
				_layout()
			else: set_zoom(zoom * pow(1.25, action)))
		bar.add_child(button)
	_percent = Label.new()
	bar.add_child(_percent)
	var help := Label.new()
	_help = help
	help.text = "滚轮 / 手柄扳机 缩放 · 放大后拖动 / 右摇杆 移动 · 图纸会一直保留，直到收起"
	help.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER
	add_child(help)
	get_viewport().size_changed.connect(_layout)
	_layout()
	_layout.call_deferred()

func set_zoom(value: float) -> void:
	var next := clampf(value, 1.0, 3.0)
	pan *= next / zoom
	zoom = next
	_layout()

func _layout() -> void:
	if not _active: return
	var viewport := get_viewport().get_visible_rect().size
	_bar.position = Vector2((viewport.x - _bar.size.x) * 0.5, viewport.y - 95)
	_help.position = Vector2(0, viewport.y - 36)
	_help.size = Vector2(viewport.x, 28)
	var available := viewport - Vector2(64, 180)
	var fit := minf(available.x / 2400.0, available.y / 1800.0)
	_paper.size = Vector2(2400, 1800) * fit * zoom
	var limit := (_paper.size - available).max(Vector2.ZERO) * 0.5
	pan = pan.clamp(-limit, limit)
	_paper.position = (viewport - _paper.size) * 0.5 - Vector2(0, 44) + pan
	_percent.text = "%d%%" % roundi(zoom * 100)

func _input(event: InputEvent) -> void:
	if not _active: return
	if event is InputEventKey and event.pressed and not event.echo:
		match event.physical_keycode:
			KEY_ESCAPE: close()
			KEY_EQUAL, KEY_KP_ADD: set_zoom(zoom * 1.25)
			KEY_MINUS, KEY_KP_SUBTRACT: set_zoom(zoom / 1.25)
			KEY_R:
				zoom = 1.0
				pan = Vector2.ZERO
				_layout()
		get_viewport().set_input_as_handled()
	elif event is InputEventJoypadButton and event.pressed:
		if event.is_action_pressed("ui_cancel"): close()
		get_viewport().set_input_as_handled()
	elif event is InputEventMouseButton:
		if event.button_index in [MOUSE_BUTTON_WHEEL_UP, MOUSE_BUTTON_WHEEL_DOWN]:
			if event.pressed: set_zoom(zoom * (1.15 if event.button_index == MOUSE_BUTTON_WHEEL_UP else 1.0 / 1.15))
			get_viewport().set_input_as_handled()
		elif event.button_index == MOUSE_BUTTON_LEFT:
			_dragging = event.pressed and event.position.y < get_viewport().get_visible_rect().size.y - 95
	elif event is InputEventMouseMotion and _dragging:
		pan += event.relative
		_layout()
		get_viewport().set_input_as_handled()

func _process(dt: float) -> void:
	if not _active: return
	var axis := Input.get_axis("inspect_zoom_out", "inspect_zoom_in")
	if absf(axis) > 0.1: set_zoom(zoom * exp(axis * dt))
	var stick := Vector2(Input.get_joy_axis(0, JOY_AXIS_RIGHT_X), Input.get_joy_axis(0, JOY_AXIS_RIGHT_Y))
	if stick.length() > 0.2:
		pan -= stick * 650 * dt
		_layout()

func close() -> void:
	if not _active: return
	_active = false
	Director.world.set_frozen(_frozen_before)
	Input.mouse_mode = _mouse_before
	for i in _hud.size(): _hud[i].visible = _visibility[i]
	hide()
	closed.emit()
	queue_free()
