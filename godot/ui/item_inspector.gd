extends CanvasLayer
## 共用检视器。只复制登记的真实网格，不把热区方块当成物品。
## fixed 通过原相机看现场；portable 用独立透明 3D 视口，背景模糊不会影响物品。
signal closed

var active := false
var reading := false
var page := 0
var pages: Array = []
var _mouse_before := Input.MOUSE_MODE_VISIBLE
var _frozen_before := false
var _camera: Camera3D
var _camera_before: Transform3D
var _fov_before := 70.0
var _focus_fov := 42.0
var _sources: Array = []
var _source_visibility: Array = []
var _inspection_light: SpotLight3D
var _overlays: Array = []
var _overlay_materials: Array = []
var _hud: Array = []
var _hud_visibility: Array = []
var _transition: Tween
var _closing := false
var _close_serial := 0
var _portable := false
var _scene_view := false
var _put_down_button: Button
var _dragging := false
var _zoom := 1.0
var _home_basis := Basis.IDENTITY
var _pad_hint := false
var _spin := Vector2.ZERO
var _root: Control
var _background: ColorRect
var _stage: SubViewportContainer
var _viewport: SubViewport
var _pivot: Node3D
var _read_panel: PanelContainer
var _text: RichTextLabel
var _title: Label
var _hint: Label
var _page_label: Label
var _read_button: Button
var _previous_button: Button
var _next_button: Button
var _reset_button: Button
var _flip_button: Button
var _notes_button: Button
var _controls: HBoxContainer
var _record := false
var _from_notebook := false
var _visuals: Array = []
var _data := {}
var _model: Node3D
var _entry_position := Vector3.ZERO
var _entry_scale := 1.0
var _entry_basis := Basis.IDENTITY
var _flipped := false
var _page_tween: Tween
var _page_turn := 0.0
var _flip_tween: Tween
var _object_yaw := 0.0
var _focus := Vector3.ZERO
var _notes_mode := false

func _ready() -> void:
	layer = 18
	_root = Control.new()
	_root.set_anchors_and_offsets_preset(Control.PRESET_FULL_RECT)
	_root.mouse_filter = Control.MOUSE_FILTER_STOP
	_root.theme = Theme.new()
	_root.theme.default_font = preload("res://ui/evidence_card.gd").font("serif")
	_root.theme.default_font_size = 18
	add_child(_root)
	_background = ColorRect.new()
	_background.set_anchors_and_offsets_preset(Control.PRESET_FULL_RECT)
	_background.mouse_filter = Control.MOUSE_FILTER_IGNORE
	var material := ShaderMaterial.new()
	material.shader = preload("res://shaders/inspect_background.gdshader")
	_background.material = material
	_root.add_child(_background)
	_stage = SubViewportContainer.new()
	_stage.set_anchors_and_offsets_preset(Control.PRESET_FULL_RECT)
	_stage.stretch = true
	_stage.mouse_filter = Control.MOUSE_FILTER_IGNORE
	_viewport = SubViewport.new()
	_viewport.transparent_bg = true
	_viewport.own_world_3d = true
	_viewport.render_target_update_mode = SubViewport.UPDATE_DISABLED
	_stage.add_child(_viewport)
	_root.add_child(_stage)
	var camera := Camera3D.new()
	camera.position.z = 2.6
	camera.fov = 40
	_viewport.add_child(camera)
	var environment := WorldEnvironment.new()
	environment.environment = Environment.new()
	environment.environment.background_mode = Environment.BG_CLEAR_COLOR
	environment.environment.ambient_light_source = Environment.AMBIENT_SOURCE_COLOR
	environment.environment.ambient_light_color = Color("#e5ddce")
	environment.environment.ambient_light_energy = 0.65
	_viewport.add_child(environment)
	for side in [-1, 1]:
		var light := DirectionalLight3D.new()
		light.rotation_degrees = Vector3(-30, side * 35, 0)
		light.light_energy = 0.8 if side == -1 else 0.35
		_viewport.add_child(light)
	_pivot = Node3D.new()
	_viewport.add_child(_pivot)
	_title = Label.new()
	_title.set_anchors_and_offsets_preset(Control.PRESET_TOP_WIDE)
	_title.offset_top = 35
	_title.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER
	_title.add_theme_font_size_override("font_size", 26)
	_title.add_theme_color_override("font_outline_color", Color(0.02, 0.018, 0.015, 0.9))
	_title.add_theme_constant_override("outline_size", 4)
	_root.add_child(_title)
	_read_panel = PanelContainer.new()
	_read_panel.anchor_left = 0.19
	_read_panel.anchor_right = 0.81
	_read_panel.anchor_top = 0.17
	_read_panel.anchor_bottom = 0.79
	var style := StyleBoxFlat.new()
	style.bg_color = Color(0.035, 0.03, 0.025, 0.94)
	style.set_content_margin_all(32)
	_read_panel.add_theme_stylebox_override("panel", style)
	_text = RichTextLabel.new()
	_text.add_theme_font_size_override("normal_font_size", 23)
	_text.add_theme_color_override("default_color", Color("#eee5d4"))
	_read_panel.add_child(_text)
	_root.add_child(_read_panel)
	var controls := HBoxContainer.new()
	_controls = controls
	controls.set_anchors_and_offsets_preset(Control.PRESET_CENTER_BOTTOM)
	controls.grow_horizontal = Control.GROW_DIRECTION_BOTH
	controls.offset_top = -115
	controls.offset_bottom = -73
	controls.alignment = BoxContainer.ALIGNMENT_CENTER
	controls.add_theme_constant_override("separation", 20)
	_root.add_child(controls)
	for spec in [["A 上一页", -1], ["D 下一页", 1]]:
		var button := Button.new()
		button.text = spec[0]
		button.focus_mode = Control.FOCUS_NONE
		var direction: int = spec[1]
		button.pressed.connect(func(): turn_page(direction))
		controls.add_child(button)
		if direction < 0:
			_previous_button = button
		else:
			_next_button = button
	_page_label = Label.new()
	controls.add_child(_page_label)
	_read_button = Button.new()
	_read_button.focus_mode = Control.FOCUS_NONE
	_read_button.pressed.connect(toggle_reading)
	controls.add_child(_read_button)
	_notes_button = Button.new()
	_notes_button.text = "N 记录"
	_notes_button.focus_mode = Control.FOCUS_NONE
	_notes_button.pressed.connect(show_notes)
	controls.add_child(_notes_button)
	_flip_button = Button.new()
	_flip_button.text = "V 翻面"
	_flip_button.focus_mode = Control.FOCUS_NONE
	_flip_button.pressed.connect(flip)
	controls.add_child(_flip_button)
	var reset := Button.new()
	_reset_button = reset
	reset.text = "R 复位"
	reset.focus_mode = Control.FOCUS_NONE
	reset.pressed.connect(reset_view)
	controls.add_child(reset)
	var put_down := Button.new()
	_put_down_button = put_down
	put_down.text = "放下"
	put_down.focus_mode = Control.FOCUS_NONE
	put_down.pressed.connect(close)
	controls.add_child(put_down)
	_hint = Label.new()
	_hint.set_anchors_and_offsets_preset(Control.PRESET_BOTTOM_WIDE)
	_hint.offset_top = -54
	_hint.offset_bottom = -20
	_hint.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER
	_hint.add_theme_color_override("font_outline_color", Color(0.02, 0.018, 0.015, 0.9))
	_hint.add_theme_constant_override("outline_size", 4)
	_root.add_child(_hint)
	_root.hide()


func open(data: Dictionary, source_nodes: Array, focus: Vector3, hud: Array = []) -> void:
	if active:
		return
	active = true
	_data = data
	_focus = focus
	_closing = false
	_record = data.get("mode", "fixed") == "record"
	_scene_view = data.get("mode", "fixed") == "scene"
	_from_notebook = data.get("from_notebook", false)
	reading = _record
	_notes_mode = false
	_flipped = _data.get("start_back", false)
	_object_yaw = PI if _flipped else 0.0
	page = 0
	pages = data.get("pages", [data.get("text", "")])
	if pages.is_empty():
		pages = [""]
	_title.text = data.get("title", "") + (" · 现场复查" if _scene_view else "")
	_camera = get_viewport().get_camera_3d()
	_mouse_before = Input.mouse_mode
	_frozen_before = Director.world.player.frozen if Director.world.player else false
	Director.world.set_frozen(true)
	Input.mouse_mode = Input.MOUSE_MODE_VISIBLE
	_hud = hud
	_hud_visibility.clear()
	for control in _hud:
		_hud_visibility.append(control.visible)
		control.hide()
	_overlays.clear()
	_overlay_materials.clear()
	for mesh in Director.world._walk(Director.world.room):
		if mesh is MeshInstance3D and mesh.material_overlay != null:
			_overlays.append(mesh)
			_overlay_materials.append(mesh.material_overlay)
			mesh.material_overlay = null
	_camera_before = _camera.global_transform
	_fov_before = _camera.fov
	_focus_fov = minf(_fov_before, data.get("focus_fov", 42.0))
	_visuals = data.get("visuals", []).duplicate()
	_portable = data.get("mode", "fixed") in ["portable", "scene"] and (not source_nodes.is_empty() or not _visuals.is_empty() or (data.get("asset", "") != "" and ResourceLoader.exists(data["asset"])))
	_sources = source_nodes.duplicate() if _portable else []
	_source_visibility.clear()
	for source in _sources:
		_source_visibility.append(source.visible)
	_stage.visible = _portable
	_stage.modulate = Color.WHITE
	_background.material.set_shader_parameter("keep_center", not _portable and not _record)
	_background.material.set_shader_parameter("amount", 0.0)
	_root.show()
	_transition = create_tween().set_parallel(true)
	_transition.tween_method(_set_blur, 0.0, 1.0, 0.22)
	if _portable:
		_build_object()
		var uv := Vector2(0.5, 0.56) if _from_notebook or _data.get("from_menu", false) else _camera.unproject_position(_focus) / get_viewport().get_visible_rect().size
		var height := 2.0 * 2.6 * tan(deg_to_rad(40.0) * 0.5)
		var aspect := get_viewport().get_visible_rect().size.aspect()
		_entry_position = Vector3((uv.x - 0.5) * height * aspect, (0.5 - uv.y) * height, 0)
		_pivot.position = _entry_position
		_pivot.basis = _entry_basis
		_pivot.scale = Vector3.ONE * _entry_scale
		_transition.tween_property(_pivot, "position", Vector3.ZERO, 0.22).set_trans(Tween.TRANS_CUBIC).set_ease(Tween.EASE_OUT)
		_transition.tween_property(_pivot, "basis", Basis(Vector3.UP, _object_yaw) * _home_basis, 0.22)
		_transition.tween_property(_pivot, "scale", Vector3.ONE, 0.22)
		_viewport.render_target_update_mode = SubViewport.UPDATE_ALWAYS
	elif not _record:
		if data.get("detail_light", false):
			_inspection_light = SpotLight3D.new()
			_inspection_light.light_color = Color("#e5ddce")
			_inspection_light.light_energy = data.get("detail_light_energy", 1.2)
			_inspection_light.spot_range = 2.8
			_inspection_light.spot_angle = 30.0
			_inspection_light.shadow_enabled = true
			_camera.add_child(_inspection_light)
		var aim := _camera.global_transform.looking_at(focus, Vector3.UP)
		_transition.tween_property(_camera, "global_transform", aim, 0.22)
		_transition.tween_property(_camera, "fov", _focus_fov, 0.22)
	_zoom = 1.0
	_spin = Vector2.ZERO
	_refresh()


func _build_object() -> void:
	for node in _pivot.get_children():
		node.free()
	_model = null
	var visuals := _visuals.duplicate()
	for source in _sources:
		visuals.append(preload("res://ui/inspection_catalog.gd")._visual(source, source.global_transform))
	var asset: String = _data.get("asset", "")
	if asset != "" and ResourceLoader.exists(asset):
		_model = load(asset).instantiate()
		_pivot.add_child(_model)
		visuals = []
		_collect_model(_model, visuals)
	var bounds := AABB()
	var first := true
	for visual in visuals:
		var b: AABB = visual["transform"] * visual["mesh"].get_aabb()
		bounds = b if first else bounds.merge(b)
		first = false
	var factor := 1.35 / maxf(0.01, _data.get("view_span", bounds.size.length()))
	var center: Vector3 = _data.get("view_center", bounds.get_center())
	var inverse_view := Basis.IDENTITY if _from_notebook or _model else _camera.global_basis.inverse().orthonormalized()
	if _model:
		_model.position = -center * factor
		_model.scale = Vector3.ONE * factor
	for visual in visuals if not _model else []:
		var clone := MeshInstance3D.new()
		clone.mesh = visual["mesh"]
		clone.material_override = visual["material"]
		for surface in clone.mesh.get_surface_count():
			clone.set_surface_override_material(surface, visual["materials"][surface])
		_pivot.add_child(clone)
		clone.basis = inverse_view * visual["transform"].basis * factor
		clone.position = inverse_view * (visual["transform"].origin - center) * factor
	for source in _sources:
		source.hide()
	_pivot.basis = Basis.IDENTITY
	_home_basis = Basis.from_euler((_data.get("rotation", Vector3.ZERO) as Vector3) * PI / 180.0)
	if _scene_view:
		var angles: Vector3 = (_data.get("rotation", Vector3.ZERO) as Vector3) * PI / 180.0
		_home_basis = Basis(Vector3.RIGHT, angles.x) * Basis(Vector3.UP, angles.y) * Basis(Vector3.BACK, angles.z)
	if not _from_notebook and not _model:
		_home_basis = _home_basis * _camera.global_basis.orthonormalized()
	_entry_basis = Basis.IDENTITY
	var original_ratio := 1.0
	if _model and not _from_notebook and not _sources.is_empty():
		var original_bounds: AABB = _sources[0].global_transform * _sources[0].mesh.get_aabb()
		for source in _sources.slice(1):
			original_bounds = original_bounds.merge(source.global_transform * source.mesh.get_aabb())
		_focus = original_bounds.get_center()
		original_ratio = original_bounds.size.length() / maxf(0.01, bounds.size.length())
		_entry_basis = _camera.global_basis.inverse().orthonormalized() * _sources[0].global_basis.orthonormalized()
	var distance := maxf(0.15, (_camera.global_basis.inverse() * ((_focus if _model else bounds.get_center()) - _camera.global_position)).z * -1.0)
	_entry_scale = 0.8 if _from_notebook else clampf(2.6 * tan(deg_to_rad(40.0) * 0.5) / (distance * tan(deg_to_rad(_fov_before) * 0.5) * factor) * original_ratio, 0.01, 4.0)


func _collect_model(node: Node3D, out: Array) -> void:
	if node is MeshInstance3D:
		out.append(preload("res://ui/inspection_catalog.gd")._visual(node, _pivot.global_transform.affine_inverse() * node.global_transform))
	for child in node.get_children():
		if child is Node3D:
			_collect_model(child, out)


func _set_blur(value: float) -> void:
	_background.material.set_shader_parameter("amount", value)


func _refresh() -> void:
	_put_down_button.text = "返回" if _from_notebook or not _portable else "放下"
	var read_label: String = _data.get("back_read_label", _data.get("read_label", "阅读")) if _flipped else _data.get("read_label", "阅读")
	_read_panel.visible = reading
	_text.text = str(_data.get("back_pages", pages)[page] if _flipped else pages[page])
	if _text.text == "" and _flipped:
		_text.text = "背面没有文字。"
	if _notes_mode:
		_text.text = _data.get("notes", "")
	_page_label.text = "%d / %d" % [page + 1, pages.size()]
	_read_button.text = ("F 返回现场复查" if _scene_view else "F 返回物品") if reading else "F " + read_label
	_read_button.visible = not _record
	_notes_button.visible = not _record and _data.get("notes", "") != "" and not _notes_mode
	_flip_button.visible = _portable and _data.get("can_flip", false) and not reading
	_reset_button.visible = not reading
	_previous_button.visible = pages.size() > 1 and not _notes_mode
	_next_button.visible = pages.size() > 1 and not _notes_mode
	_page_label.visible = pages.size() > 1 and not _notes_mode
	_previous_button.disabled = page == 0
	_next_button.disabled = page == pages.size() - 1
	if _record:
		_hint.text = "滚轮阅读　·　Esc 返回" + ("笔记本" if _from_notebook else "现场")
	if not _record:
		if reading:
			_hint.text = ("Esc 返回现场复查" if _scene_view else "Esc 返回物品") + ("　·　A / D 翻页" if pages.size() > 1 and not _notes_mode else "")
		elif _portable:
			_hint.text = ("拖动旋转现场" if _scene_view else "拖动旋转") + "　·　滚轮缩放　·　R 复位　·　F " + read_label + ("　·　Esc 返回笔记本" if _from_notebook else "　·　Esc 放下")
			if _data.get("can_flip", false):
				_hint.text += "　·　V 翻面"
		else:
			_hint.text = "滚轮查看细节　·　R 复位　·　F 观察记录　·　Esc 返回现场"
	_stage.modulate.a = 0.18 if reading else 1.0


func toggle_reading() -> void:
	if not active or _closing or _record:
		return
	_finish_page_turn()
	reading = not reading
	_notes_mode = false
	_dragging = false
	_refresh()


func turn_page(direction: int) -> void:
	if not active or _closing or _notes_mode or pages.size() < 2:
		return
	var target := clampi(page + direction, 0, pages.size() - 1)
	if target == page:
		return
	_finish_page_turn()
	page = target
	_dragging = false
	if _model and _model.has_method("set_page"):
		if reading:
			_model.set_page(page)
		else:
			# 纸面转至侧边时换页，再从另一侧展开；不改变玩家的旋转和缩放。
			_page_tween = create_tween()
			var edge := PI * 0.5 * signi(direction)
			_page_tween.tween_method(_set_page_turn, 0.0, edge, 0.12).set_trans(Tween.TRANS_SINE)
			_page_tween.tween_callback(func():
				_model.set_page(page)
				_set_page_turn(-edge))
			_page_tween.tween_method(_set_page_turn, -edge, 0.0, 0.12).set_trans(Tween.TRANS_SINE)
	_refresh()


func _set_page_turn(value: float) -> void:
	_page_turn = value
	if is_instance_valid(_model):
		_model.rotation.y = value


func _finish_page_turn() -> void:
	if _page_tween and _page_tween.is_valid():
		_page_tween.kill()
	_set_page_turn(0.0)
	if is_instance_valid(_model) and _model.has_method("set_page"):
		_model.set_page(page)


func show_notes() -> void:
	if not active or _closing or _data.get("notes", "") == "":
		return
	_finish_page_turn()
	reading = true
	_notes_mode = true
	_dragging = false
	_refresh()


func flip() -> void:
	if not active or _closing or reading or not _portable or not _data.get("can_flip", false):
		return
	_flipped = not _flipped
	_refresh()
	_dragging = false
	if _flip_tween and _flip_tween.is_valid():
		_flip_tween.kill()
	_flip_tween = create_tween()
	_flip_tween.tween_method(_set_yaw, _object_yaw, PI if _flipped else 0.0, 0.22).set_trans(Tween.TRANS_SINE)


func _set_yaw(value: float) -> void:
	_object_yaw = value
	_apply_rotation()


func _apply_rotation() -> void:
	_pivot.basis = Basis(Vector3.UP, _spin.x) * Basis(Vector3.RIGHT, _spin.y) * Basis(Vector3.UP, _object_yaw) * _home_basis


func reset_view() -> void:
	if reading or _closing:
		return
	_finish_page_turn()
	_spin = Vector2.ZERO
	_zoom = 1.0
	_flipped = _data.get("start_back", false)
	_object_yaw = PI if _flipped else 0.0
	if _flip_tween and _flip_tween.is_valid():
		_flip_tween.kill()
	_pivot.basis = Basis(Vector3.UP, _object_yaw) * _home_basis
	_pivot.scale = Vector3.ONE
	if not _portable and is_instance_valid(_camera):
		_camera.fov = _focus_fov
	_refresh()


func _input(event: InputEvent) -> void:
	Controls.note_event(event)
	if not active:
		return
	if event is InputEventJoypadButton and event.pressed:
		if _closing:
			get_viewport().set_input_as_handled()
			return
		get_viewport().set_input_as_handled()
		if event.is_action_pressed("ui_cancel"):
			if reading and not _record: toggle_reading()
			else: close()
		elif event.is_action_pressed("inspect_read"): toggle_reading()
		elif event.is_action_pressed("notebook"): show_notes()
		elif event.is_action_pressed("inspect_reset"): reset_view()
		elif event.is_action_pressed("inspect_flip"): flip()
		elif event.is_action_pressed("page_prev"): turn_page(-1)
		elif event.is_action_pressed("page_next"): turn_page(1)
		return
	# 鼠标按钮留给 GUI；相机和移动由 frozen 阻止。
	if event is InputEventKey and event.pressed and not event.echo:
		get_viewport().set_input_as_handled()
		if _closing:
			return
		match event.physical_keycode:
			KEY_ESCAPE:
				if reading and not _record:
					toggle_reading()
				else:
					close()
			KEY_F: toggle_reading()
			KEY_R: reset_view()
			KEY_A: turn_page(-1)
			KEY_D: turn_page(1)
			KEY_V: flip()
			KEY_N: show_notes()
	elif not _closing and not reading and event is InputEventMouseButton:
		if event.button_index == MOUSE_BUTTON_LEFT:
			_dragging = event.pressed and not _controls.get_global_rect().has_point(event.position)
		if event.pressed and event.button_index in [MOUSE_BUTTON_WHEEL_UP, MOUSE_BUTTON_WHEEL_DOWN]:
			var step := 1.1 if event.button_index == MOUSE_BUTTON_WHEEL_UP else 1.0 / 1.1
			_zoom = clampf(_zoom * step, 0.75, 1.75)
			if _portable:
				_pivot.scale = Vector3.ONE * _zoom
			else:
				_camera.fov = clampf(_focus_fov / _zoom, minf(12.0, _focus_fov), _fov_before)
	elif not _closing and not reading and _portable and _dragging and event is InputEventMouseMotion:
		_spin += event.relative * 0.008
		_apply_rotation()
		get_viewport().set_input_as_handled()


func close(immediate := false) -> void:
	if not active or (_closing and not immediate):
		return
	_finish_page_turn()
	_closing = true
	_close_serial += 1
	var serial := _close_serial
	_dragging = false
	if _flip_tween and _flip_tween.is_valid():
		_flip_tween.kill()
	if _transition and _transition.is_valid():
		_transition.kill()
	if not immediate:
		_transition = create_tween().set_parallel(true)
		_transition.tween_method(_set_blur, 1.0, 0.0, 0.16)
		if is_instance_valid(_camera):
			_transition.tween_property(_camera, "global_transform", _camera_before, 0.16)
			_transition.tween_property(_camera, "fov", _fov_before, 0.16)
		if _portable:
			_stage.modulate.a = 1.0
			_read_panel.hide()
			_transition.tween_property(_pivot, "position", _entry_position, 0.16)
			_transition.tween_property(_pivot, "basis", _entry_basis, 0.16)
			_transition.tween_property(_pivot, "scale", Vector3.ONE * _entry_scale, 0.16)
		while active and serial == _close_serial and _transition.is_valid() and _transition.is_running():
			await get_tree().process_frame
		if not active or serial != _close_serial:
			return
	if is_instance_valid(_camera):
		_camera.global_transform = _camera_before
		_camera.fov = _fov_before
	for i in _sources.size():
		if is_instance_valid(_sources[i]):
			_sources[i].visible = _source_visibility[i]
	if is_instance_valid(_inspection_light):
		_inspection_light.free()
	for i in _overlays.size():
		if is_instance_valid(_overlays[i]):
			_overlays[i].material_overlay = _overlay_materials[i]
	_overlays.clear()
	_overlay_materials.clear()
	for i in _hud.size():
		if is_instance_valid(_hud[i]):
			_hud[i].visible = _hud_visibility[i]
	_viewport.render_target_update_mode = SubViewport.UPDATE_DISABLED
	_root.hide()
	for child in _pivot.get_children():
		child.free()
	_sources.clear()
	_source_visibility.clear()
	_visuals.clear()
	_data = {}
	_model = null
	Director.world.set_frozen(_frozen_before)
	Input.mouse_mode = _mouse_before
	active = false
	_closing = false
	closed.emit()


func _process(dt: float) -> void:
	if not active or _closing: return
	if _pad_hint != Controls.gamepad:
		_pad_hint = Controls.gamepad
		_refresh()
	if Controls.gamepad:
		if _record:
			_hint.text = "左摇杆滚动　·　LB / RB 翻页　·　B / ○ 返回笔记本"
		elif reading:
			_hint.text = "左摇杆滚动　·　B / ○ 返回物品　·　LB / RB 翻页"
		else:
			_hint.text = "右摇杆旋转　·　LT / RT 缩放　·　LB / RB 翻页　·　X / □ 复位　·　A / × 阅读　·　B / ○ 放下"
			if _portable and _data.get("can_flip", false): _hint.text += "　·　按右摇杆翻面"
			if _data.get("notes", "") != "": _hint.text += "　·　Y / △ 观察记录"
	if reading:
		var scroll := _text.get_v_scroll_bar()
		scroll.value += Input.get_axis("move_forward", "move_back") * 450.0 * dt
		return
	var look := Controls.look_vector()
	if _portable and not look.is_zero_approx():
		_spin += look * 2.0 * dt
		_apply_rotation()
	var zoom_input := Input.get_axis("inspect_zoom_out", "inspect_zoom_in")
	if not is_zero_approx(zoom_input):
		_zoom = clampf(_zoom * exp(zoom_input * dt), 0.75, 1.75)
		if _portable: _pivot.scale = Vector3.ONE * _zoom
		else: _camera.fov = clampf(_focus_fov / _zoom, minf(12.0, _focus_fov), _fov_before)
