extends Node
## 第三章绘画检视：绘画集 → 单幅画 → 小屋。
signal selected(id: String)
const HOUSE := "hs_trial_house_painting"
const GROUP := "hs_trial_drawing_collection"
const DRAWINGS := ["hs_draw_path", "hs_draw_wall", "hs_draw_family", "hs_draw_boxes", "hs_draw_train"]
var host: Node
var trial: Node
var reviewed: Array = []
var overview := false
var inspecting := false
var transitioning := false
var camera: Camera3D
var panel: Control
var _buttons := {}
var _bounds := {}
var _title: Label
var _house: Button
var _hidden: Array = []
var _camera_start: Transform3D
var cancelled := false
var _collection: Area3D

func run(owner_trial: Node) -> void:
	trial = owner_trial
	host = Director.world
	for id in DRAWINGS:
		var area: Node3D = host.hotspot_nodes.get(id)
		if not is_instance_valid(area):
			push_error("Drawing collection missing target: " + id)
			return
		for child in area.get_children():
			if child is CollisionShape3D and child.shape is BoxShape3D:
				_bounds[id] = child.global_transform * AABB(-child.shape.size * 0.5, child.shape.size)
		if GameState.inspected.has(id) and GameState.evidence.has(ContentDB.hotspots[id].get("evidence", "")):
			reviewed.append(id)
	if _bounds.size() != DRAWINGS.size():
		push_error("Drawing collection needs all five authored bounds")
		return
	_add_house_painting()
	var wall := _wall_bounds()
	ContentDB.hotspots[GROUP] = {"id": GROUP, "scene": "child_room", "label": "墙上的绘画集", "verb": "查看"}
	host._hotspot(host.room, GROUP, wall.get_center() + Vector3(0, 0, -0.045), Vector3(wall.size.x + 0.16, wall.size.y + 0.16, 0.08), true)
	_collection = host.hotspot_nodes[GROUP]
	# Papers face the interior (-Z). This group follows the same authored wall.
	_collection.set_meta("interaction_normal", Vector3.FORWARD)
	_collection.set_meta("interaction_min_dot", 0.0)
	_hide_individual_targets(true)
	host.highlight_hotspots([GROUP])
	Director.ui.set_checklist([{ "text": "墙上的绘画集：靠近后按 E，正面查看。", "head": true, "done": false }])
	var house_finished := false
	while not house_finished:
		var id: String = await Director.inspected
		if id == Director.CANCEL:
			break
		if id != GROUP:
			continue
		await _open_overview()
		if cancelled or Director._interrupted():
			await _close_overview()
			break
		while overview and not cancelled:
			var choice: String = await selected
			if cancelled:
				await _close_overview()
				house_finished = true
				break
			if choice == "close":
				await _close_overview()
			elif choice == HOUSE and reviewed.size() == DRAWINGS.size():
				await _focus_house_painting()
				if cancelled or Director._interrupted():
					await _close_overview()
					house_finished = true
					break
				await _close_overview(true)
				if cancelled or Director._interrupted():
					house_finished = true
					break
				await trial.enter_house()
				house_finished = true
				break
			elif DRAWINGS.has(choice):
				inspecting = true
				panel.hide()
				host.hotspot_nodes[choice].visible = true
				await Director._show_hotspot(choice)
				host.hotspot_nodes[choice].visible = false
				if not reviewed.has(choice):
					reviewed.append(choice)
				inspecting = false
				if Director._interrupted():
					await _close_overview()
					house_finished = true
					break
				camera.current = true
				Input.mouse_mode = Input.MOUSE_MODE_VISIBLE
				panel.show()
				_refresh()
				_buttons[choice].grab_focus()
	_hide_individual_targets(false)
	host.highlight_hotspots([])
	host.hotspot_nodes.erase(GROUP)
	ContentDB.hotspots.erase(GROUP)
	ContentDB.hotspots.erase(HOUSE)
	_collection.queue_free()
	Director.ui.set_checklist([])
	Director.ui.set_progress(0, 0)

func _add_house_painting() -> void:
	var wall := _wall_bounds()
	var paper := host.room.get_node_or_null("TrialHousePainting") as MeshInstance3D
	if paper == null:
		paper = MeshInstance3D.new()
		paper.name = "TrialHousePainting"
		var quad := QuadMesh.new()
		quad.size = Vector2(0.42, 0.315)
		paper.mesh = quad
		var material := StandardMaterial3D.new()
		material.albedo_texture = load("res://art/levels/child_room/painting_underbed.png")
		material.roughness = 0.95
		paper.material_override = material
		host.room.add_child(paper)
		paper.global_position = Vector3(wall.get_center().x, wall.end.y + 0.11, wall.position.z - 0.015)
		paper.rotation.y = PI
	_bounds[HOUSE] = paper.global_transform * paper.get_aabb()
	ContentDB.hotspots[HOUSE] = {"id": HOUSE, "label": "眼睛小屋"}

func _focus_house_painting() -> void:
	transitioning = true
	panel.hide()
	var center: Vector3 = _bounds[HOUSE].get_center()
	var destination := Transform3D(Basis.IDENTITY, center + Vector3(0, 0, -0.7)).looking_at(center, Vector3.UP)
	var tween := create_tween().set_parallel(true).set_trans(Tween.TRANS_SINE).set_ease(Tween.EASE_IN_OUT)
	tween.tween_property(camera, "global_transform", destination, 0.65)
	if camera.projection == Camera3D.PROJECTION_ORTHOGONAL:
		tween.tween_property(camera, "size", 0.38, 0.65)
	await tween.finished

func _wall_bounds() -> AABB:
	var wall: AABB = _bounds[DRAWINGS[0]]
	for id in _bounds:
		wall = wall.merge(_bounds[id])
	return wall

func _hide_individual_targets(hide_targets: bool) -> void:
	for id in DRAWINGS:
		host.hotspot_nodes[id].visible = not hide_targets

func _open_overview() -> void:
	overview = true
	transitioning = true
	_camera_start = host.player.cam.global_transform
	camera = Camera3D.new()
	camera.fov = host.player.cam.fov
	camera.near = 0.03
	add_child(camera)
	camera.global_transform = _camera_start
	host.player.deactivate()
	host.set_frozen(true)
	camera.current = true
	_hidden = []
	for control in [Director.ui.objective_label, Director.ui.checklist_box, Director.ui.progress_label, Director.ui.crosshair, Director.ui.hint_box, Director.ui.day_label, Director.ui.room_label, Director.ui.keys]:
		_hidden.append([control, control.visible])
		control.hide()
	var wall := _wall_bounds()
	var center := wall.get_center()
	var target := Vector3(1.28, center.y - 0.02, -6.91)
	var destination := Transform3D(Basis.IDENTITY, Vector3(1.65, center.y - 0.02, -8.8)).looking_at(target, Vector3.UP)
	var tween := create_tween().set_parallel(true).set_trans(Tween.TRANS_SINE).set_ease(Tween.EASE_IN_OUT)
	tween.tween_property(camera, "global_transform", destination, 0.55)
	tween.tween_property(camera, "fov", 50.0, 0.55)
	await tween.finished
	_build_panel()
	Input.mouse_mode = Input.MOUSE_MODE_VISIBLE
	transitioning = false
	_refresh()
	_buttons[DRAWINGS[0]].grab_focus()
	print("CHAPTER3_DRAWINGS overview ready: fov=", camera.fov, " reviewed=", reviewed.size(), " house_locked=", _house.disabled)

func _close_overview(entering := false) -> void:
	transitioning = true
	panel.queue_free()
	panel = null
	_buttons.clear()
	if not entering:
		var tween := create_tween().set_parallel(true).set_trans(Tween.TRANS_SINE).set_ease(Tween.EASE_IN_OUT)
		tween.tween_property(camera, "global_transform", _camera_start, 0.4)
		tween.tween_property(camera, "fov", host.player.cam.fov, 0.4)
		await tween.finished
	for item in _hidden:
		item[0].visible = item[1]
	host.player.activate()
	host.set_frozen(false)
	camera.queue_free()
	camera = null
	overview = false
	transitioning = false

func _build_panel() -> void:
	var layer := CanvasLayer.new()
	layer.layer = 45
	add_child(layer)
	panel = Control.new()
	panel.set_anchors_and_offsets_preset(Control.PRESET_FULL_RECT)
	panel.mouse_filter = Control.MOUSE_FILTER_STOP
	layer.add_child(panel)
	# Free the owning canvas too when this overview closes.
	panel.tree_exited.connect(layer.queue_free)
	_title = Label.new()
	_title.position = Vector2(32, 30)
	_title.add_theme_font_size_override("font_size", 22)
	_title.add_theme_color_override("font_shadow_color", Color.BLACK)
	_title.add_theme_constant_override("shadow_outline_size", 6)
	panel.add_child(_title)
	for id in DRAWINGS + [HOUSE]:
		var button := Button.new()
		button.flat = true
		button.mouse_default_cursor_shape = Control.CURSOR_POINTING_HAND
		var outline := StyleBoxFlat.new()
		outline.bg_color = Color(0.95, 0.86, 0.65, 0.07)
		outline.border_color = Color("#f2db9c")
		outline.set_border_width_all(2)
		outline.set_corner_radius_all(3)
		button.add_theme_stylebox_override("hover", outline)
		button.add_theme_stylebox_override("focus", outline)
		button.add_theme_stylebox_override("pressed", outline)
		button.pressed.connect(func(): selected.emit(id))
		panel.add_child(button)
		_buttons[id] = button
		var caption := Label.new()
		caption.name = "Caption"
		caption.mouse_filter = Control.MOUSE_FILTER_IGNORE
		caption.add_theme_font_size_override("font_size", 16)
		caption.add_theme_color_override("font_shadow_color", Color.BLACK)
		caption.add_theme_constant_override("shadow_outline_size", 5)
		button.add_child(caption)
	var close := Button.new()
	close.text = "返回房间  Esc / B"
	close.set_anchors_and_offsets_preset(Control.PRESET_TOP_RIGHT)
	close.position = Vector2(-250, 30)
	close.size = Vector2(220, 42)
	close.pressed.connect(func(): selected.emit("close"))
	panel.add_child(close)
	_house = _buttons[HOUSE]
	var hint := Label.new()
	hint.set_anchors_and_offsets_preset(Control.PRESET_BOTTOM_LEFT)
	hint.position = Vector2(32, -75)
	hint.text = "点击画作查看 · 方向键选择，A / Enter 确认\n先看其余五幅画，最后选择画着小屋的那幅。"
	hint.add_theme_color_override("font_shadow_color", Color.BLACK)
	hint.add_theme_constant_override("shadow_outline_size", 5)
	panel.add_child(hint)
	_position_buttons()

func _refresh() -> void:
	_title.text = "墙上的绘画集　线索画 %d / %d" % [reviewed.size(), DRAWINGS.size()]
	_house.disabled = reviewed.size() != DRAWINGS.size()
	var house_caption: Label = _house.get_node("Caption")
	house_caption.text = "眼睛小屋 · 走进画中" if not _house.disabled else "眼睛小屋 · 最后查看"
	_house.tooltip_text = "查看其余五幅画后，这幅小屋画才可进入。" if _house.disabled else "走进画里的小屋"
	for id in DRAWINGS:
		var caption: Label = _buttons[id].get_node("Caption")
		caption.text = ("✓ " if reviewed.has(id) else "") + String(ContentDB.hotspots[id].get("label", id))

func _position_buttons() -> void:
	var viewport_size := get_viewport().get_visible_rect().size
	var aspect := viewport_size.x / maxf(viewport_size.y, 1.0)
	var wall := _wall_bounds()
	if camera.projection == Camera3D.PROJECTION_ORTHOGONAL:
		camera.size = maxf((wall.size.y + 0.10) / 0.68, (wall.size.x + 0.12) / (aspect * 0.78))
	for id in _buttons:
		var bounds: AABB = _bounds[id]
		var rect := Rect2(camera.unproject_position(bounds.get_endpoint(0)), Vector2.ZERO)
		for i in range(1, 8):
			rect = rect.expand(camera.unproject_position(bounds.get_endpoint(i)))
		rect = rect.grow(8)
		_buttons[id].position = rect.position
		_buttons[id].size = rect.size
		_buttons[id].get_node("Caption").position = Vector2(0, rect.size.y + 3)

func _process(_dt: float) -> void:
	if overview and not transitioning and not inspecting and is_instance_valid(panel):
		# The normal HUD updates room/date visibility every frame.
		for item in _hidden:
			item[0].hide()
		_position_buttons()

func _input(event: InputEvent) -> void:
	if not overview or inspecting or not event.is_pressed() or event.is_echo():
		return
	if event.is_action_pressed("ui_cancel") or event.is_action_pressed("pause") or event.is_action_pressed("notebook"):
		get_viewport().set_input_as_handled()
		if not transitioning:
			selected.emit("close")

func cancel() -> void:
	cancelled = true
	if overview and not inspecting and not transitioning:
		selected.emit("close")
