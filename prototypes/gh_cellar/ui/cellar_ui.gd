extends CanvasLayer
## 密室 UI：HUD、取景框、对焦环、记录本、最终选择、结局。

signal notebook_closed
signal notebook_page_shown(page_id: String)
signal choice_made(index: int)
signal restart_requested

const FOCUS_RING := preload("res://ui/focus_ring.gd")

var font: Font
var _root: Control
var _crosshair: ColorRect
var _controls: Label
var _title: Label
var _subtitle: Label
var _prompt: Label
var _narration: Label
var _toast: Label
var _status: Label
var _plate: Label
var _key: Label

var _camera_overlay: Control
var _viewfinder: TextureRect
var _focus_ring: Control
var _year_label: Label
var _focus_label: Label
var _camera_hint: Label
var _owner: TextureRect
var _flash: ColorRect

var _notebook: Control
var _notebook_title: Label
var _notebook_text: RichTextLabel
var _notebook_page_label: Label
var _notebook_pages: Array = []
var _notebook_index := 0

var _choice: Control
var _choice_title: Label
var _choice_text: Label
var _choice_buttons: Array[Button] = []

var _ending: Control
var _ending_text: Label

var _say_tween: Tween
var _owner_tween: Tween
var _notebook_open := false
var _choice_open := false
var _ending_open := false


func _ready() -> void:
	font = load("res://art/fonts/simhei.ttf")
	_build_hud()
	_build_camera()
	_build_notebook()
	_build_choice()
	_build_ending()


func _label(text: String, size: int, color: Color) -> Label:
	var l := Label.new()
	l.text = text
	l.add_theme_font_override("font", font)
	l.add_theme_font_size_override("font_size", size)
	l.add_theme_color_override("font_color", color)
	l.mouse_filter = Control.MOUSE_FILTER_IGNORE
	return l


func _full_rect(n: Control) -> void:
	n.set_anchors_and_offsets_preset(Control.PRESET_FULL_RECT)
	n.mouse_filter = Control.MOUSE_FILTER_IGNORE


func _build_hud() -> void:
	_root = Control.new()
	_full_rect(_root)
	add_child(_root)

	_crosshair = ColorRect.new()
	_crosshair.color = Color(0.92, 0.86, 0.72, 0.72)
	_crosshair.anchor_left = 0.5
	_crosshair.anchor_top = 0.5
	_crosshair.anchor_right = 0.5
	_crosshair.anchor_bottom = 0.5
	_crosshair.offset_left = -2.5
	_crosshair.offset_top = -2.5
	_crosshair.offset_right = 2.5
	_crosshair.offset_bottom = 2.5
	_crosshair.mouse_filter = Control.MOUSE_FILTER_IGNORE
	_root.add_child(_crosshair)

	_controls = _label("WASD 移动  ·  鼠标 视角  ·  E 检查  ·  F 举镜  ·  Tab 记录本  ·  Esc 释放鼠标",
		16, Color(0.88, 0.84, 0.74, 0.86))
	_controls.position = Vector2(26, 20)
	_root.add_child(_controls)

	_title = _label("密室 · GH CELLAR", 24, Color(0.93, 0.86, 0.72, 0.72))
	_title.position = Vector2(26, 52)
	_root.add_child(_title)

	_subtitle = _label("空间漫游原型  /  10 × 8 × 2.6 m", 13, Color(0.72, 0.68, 0.60, 0.58))
	_subtitle.position = Vector2(26, 86)
	_root.add_child(_subtitle)

	_status = _label("", 15, Color(0.9, 0.78, 0.58, 0.82))
	_status.anchor_left = 1.0
	_status.anchor_right = 1.0
	_status.offset_left = -360
	_status.offset_right = -26
	_status.offset_top = 24
	_status.offset_bottom = 48
	_status.horizontal_alignment = HORIZONTAL_ALIGNMENT_RIGHT
	_root.add_child(_status)

	_plate = _label("", 15, Color(0.82, 0.76, 0.62, 0.72))
	_plate.anchor_left = 1.0
	_plate.anchor_right = 1.0
	_plate.offset_left = -360
	_plate.offset_right = -26
	_plate.offset_top = 50
	_plate.offset_bottom = 74
	_plate.horizontal_alignment = HORIZONTAL_ALIGNMENT_RIGHT
	_root.add_child(_plate)

	_key = _label("钥匙：—", 15, Color(0.85, 0.68, 0.32, 0.72))
	_key.anchor_left = 1.0
	_key.anchor_right = 1.0
	_key.offset_left = -360
	_key.offset_right = -26
	_key.offset_top = 76
	_key.offset_bottom = 100
	_key.horizontal_alignment = HORIZONTAL_ALIGNMENT_RIGHT
	_root.add_child(_key)

	_prompt = _label("", 18, Color(0.95, 0.86, 0.66, 0.96))
	_prompt.anchor_left = 0.5
	_prompt.anchor_right = 0.5
	_prompt.anchor_top = 1.0
	_prompt.anchor_bottom = 1.0
	_prompt.offset_left = -460
	_prompt.offset_right = 460
	_prompt.offset_top = -122
	_prompt.offset_bottom = -92
	_prompt.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER
	_root.add_child(_prompt)

	_narration = _label("", 19, Color(0.93, 0.88, 0.76, 0.96))
	_narration.anchor_left = 0.5
	_narration.anchor_right = 0.5
	_narration.anchor_top = 1.0
	_narration.anchor_bottom = 1.0
	_narration.offset_left = -520
	_narration.offset_right = 520
	_narration.offset_top = -238
	_narration.offset_bottom = -130
	_narration.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER
	_narration.vertical_alignment = VERTICAL_ALIGNMENT_BOTTOM
	_narration.autowrap_mode = TextServer.AUTOWRAP_WORD_SMART
	_narration.modulate.a = 0.0
	_root.add_child(_narration)

	_toast = _label("", 17, Color(0.95, 0.78, 0.42, 0.95))
	_toast.anchor_left = 0.5
	_toast.anchor_right = 0.5
	_toast.offset_left = -400
	_toast.offset_right = 400
	_toast.offset_top = 78
	_toast.offset_bottom = 106
	_toast.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER
	_toast.modulate.a = 0.0
	_root.add_child(_toast)


func _build_camera() -> void:
	_camera_overlay = Control.new()
	_full_rect(_camera_overlay)
	_camera_overlay.visible = false
	_root.add_child(_camera_overlay)

	var dark := ColorRect.new()
	_full_rect(dark)
	dark.color = Color(0.0, 0.0, 0.0, 0.16)
	_camera_overlay.add_child(dark)

	_viewfinder = TextureRect.new()
	_full_rect(_viewfinder)
	_viewfinder.texture = load("res://art/ui/viewfinder.png")
	_viewfinder.expand_mode = TextureRect.EXPAND_IGNORE_SIZE
	_viewfinder.stretch_mode = TextureRect.STRETCH_KEEP_ASPECT_COVERED
	_camera_overlay.add_child(_viewfinder)

	_focus_ring = FOCUS_RING.new()
	_full_rect(_focus_ring)
	_camera_overlay.add_child(_focus_ring)

	_year_label = _label("", 26, Color(1.0, 0.86, 0.58, 0.95))
	_year_label.anchor_left = 0.5
	_year_label.anchor_right = 0.5
	_year_label.offset_left = -300
	_year_label.offset_right = 300
	_year_label.offset_top = 96
	_year_label.offset_bottom = 132
	_year_label.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER
	_camera_overlay.add_child(_year_label)

	_focus_label = _label("", 15, Color(0.92, 0.82, 0.62, 0.85))
	_focus_label.anchor_left = 0.5
	_focus_label.anchor_right = 0.5
	_focus_label.offset_left = -220
	_focus_label.offset_right = 220
	_focus_label.offset_top = 556
	_focus_label.offset_bottom = 584
	_focus_label.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER
	_camera_overlay.add_child(_focus_label)

	_camera_hint = _label("F 放下相机  ·  滚轮对焦  ·  左键快门  ·  R 二次曝光",
		15, Color(0.86, 0.8, 0.68, 0.75))
	_camera_hint.anchor_left = 0.5
	_camera_hint.anchor_right = 0.5
	_camera_hint.anchor_top = 1.0
	_camera_hint.anchor_bottom = 1.0
	_camera_hint.offset_left = -400
	_camera_hint.offset_right = 400
	_camera_hint.offset_top = -62
	_camera_hint.offset_bottom = -36
	_camera_hint.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER
	_camera_overlay.add_child(_camera_hint)

	_owner = TextureRect.new()
	_owner.texture = load("res://art/ui/owner_reflection.png")
	_owner.expand_mode = TextureRect.EXPAND_IGNORE_SIZE
	_owner.stretch_mode = TextureRect.STRETCH_KEEP_ASPECT_CENTERED
	_owner.anchor_left = 1.0
	_owner.anchor_top = 0.10
	_owner.anchor_right = 1.0
	_owner.anchor_bottom = 0.92
	_owner.offset_left = -460
	_owner.offset_right = -120
	_owner.mouse_filter = Control.MOUSE_FILTER_IGNORE
	_owner.modulate.a = 0.0
	_owner.visible = false
	_camera_overlay.add_child(_owner)

	_flash = ColorRect.new()
	_full_rect(_flash)
	_flash.color = Color(1.0, 0.95, 0.82, 0.0)
	_flash.mouse_filter = Control.MOUSE_FILTER_IGNORE
	_camera_overlay.add_child(_flash)


func _build_notebook() -> void:
	_notebook = Control.new()
	_full_rect(_notebook)
	_notebook.visible = false
	_notebook.mouse_filter = Control.MOUSE_FILTER_STOP
	_root.add_child(_notebook)

	var dim := ColorRect.new()
	_full_rect(dim)
	dim.color = Color(0.015, 0.013, 0.010, 0.72)
	_notebook.add_child(dim)

	var paper := TextureRect.new()
	paper.texture = load("res://art/ui/notebook_bg.png")
	paper.anchor_left = 0.5
	paper.anchor_top = 0.5
	paper.anchor_right = 0.5
	paper.anchor_bottom = 0.5
	paper.offset_left = -450
	paper.offset_top = -340
	paper.offset_right = 450
	paper.offset_bottom = 340
	paper.expand_mode = TextureRect.EXPAND_IGNORE_SIZE
	paper.stretch_mode = TextureRect.STRETCH_KEEP_ASPECT_COVERED
	paper.mouse_filter = Control.MOUSE_FILTER_IGNORE
	_notebook.add_child(paper)

	_notebook_title = _label("记录本", 26, Color(0.22, 0.16, 0.10, 0.95))
	_notebook_title.position = Vector2(392, 146)
	_notebook.add_child(_notebook_title)

	_notebook_text = RichTextLabel.new()
	_notebook_text.bbcode_enabled = true
	_notebook_text.fit_content = false
	_notebook_text.scroll_active = false
	_notebook_text.anchor_left = 0.5
	_notebook_text.anchor_top = 0.5
	_notebook_text.anchor_right = 0.5
	_notebook_text.anchor_bottom = 0.5
	_notebook_text.offset_left = -400
	_notebook_text.offset_top = -210
	_notebook_text.offset_right = 400
	_notebook_text.offset_bottom = 280
	_notebook_text.add_theme_font_override("normal_font", font)
	_notebook_text.add_theme_font_override("bold_font", font)
	_notebook_text.add_theme_font_size_override("normal_font_size", 18)
	_notebook_text.add_theme_font_size_override("bold_font_size", 23)
	_notebook_text.add_theme_color_override("default_color", Color(0.24, 0.18, 0.11, 0.96))
	_notebook.add_child(_notebook_text)

	_notebook_page_label = _label("第 1 / 1 页  ·  A / D 翻页", 14, Color(0.28, 0.21, 0.13, 0.66))
	_notebook_page_label.anchor_left = 0.5
	_notebook_page_label.anchor_right = 0.5
	_notebook_page_label.anchor_top = 0.5
	_notebook_page_label.anchor_bottom = 0.5
	_notebook_page_label.offset_left = -400
	_notebook_page_label.offset_top = 300
	_notebook_page_label.offset_right = 0
	_notebook_page_label.offset_bottom = 326
	_notebook.add_child(_notebook_page_label)

	var close_hint := _label("Tab / Esc 合上", 14, Color(0.28, 0.21, 0.13, 0.62))
	close_hint.anchor_left = 0.5
	close_hint.anchor_right = 0.5
	close_hint.anchor_top = 0.5
	close_hint.anchor_bottom = 0.5
	close_hint.offset_left = 230
	close_hint.offset_top = 302
	close_hint.offset_right = 430
	close_hint.offset_bottom = 326
	close_hint.horizontal_alignment = HORIZONTAL_ALIGNMENT_RIGHT
	_notebook.add_child(close_hint)


func _build_choice() -> void:
	_choice = Control.new()
	_full_rect(_choice)
	_choice.visible = false
	_choice.mouse_filter = Control.MOUSE_FILTER_STOP
	_root.add_child(_choice)

	var dim := ColorRect.new()
	_full_rect(dim)
	dim.color = Color(0.01, 0.008, 0.006, 0.82)
	_choice.add_child(dim)

	_choice_title = _label("", 28, Color(0.94, 0.84, 0.64, 0.98))
	_choice_title.anchor_left = 0.5
	_choice_title.anchor_right = 0.5
	_choice_title.offset_left = -420
	_choice_title.offset_right = 420
	_choice_title.offset_top = 260
	_choice_title.offset_bottom = 306
	_choice_title.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER
	_choice.add_child(_choice_title)

	_choice_text = _label("", 18, Color(0.86, 0.81, 0.70, 0.9))
	_choice_text.anchor_left = 0.5
	_choice_text.anchor_right = 0.5
	_choice_text.offset_left = -430
	_choice_text.offset_right = 430
	_choice_text.offset_top = 320
	_choice_text.offset_bottom = 420
	_choice_text.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER
	_choice_text.autowrap_mode = TextServer.AUTOWRAP_WORD_SMART
	_choice.add_child(_choice_text)

	for i in 2:
		var b := Button.new()
		b.add_theme_font_override("font", font)
		b.add_theme_font_size_override("font_size", 18)
		b.anchor_left = 0.5
		b.anchor_right = 0.5
		b.offset_left = -260
		b.offset_right = 260
		b.offset_top = 450 + i * 62
		b.offset_bottom = 496 + i * 62
		b.pressed.connect(_on_choice_pressed.bind(i))
		_choice.add_child(b)
		_choice_buttons.append(b)


func _build_ending() -> void:
	_ending = Control.new()
	_full_rect(_ending)
	_ending.visible = false
	_ending.mouse_filter = Control.MOUSE_FILTER_STOP
	_root.add_child(_ending)

	var bg := ColorRect.new()
	_full_rect(bg)
	bg.color = Color(0.006, 0.006, 0.007, 1.0)
	_ending.add_child(bg)

	_ending_text = _label("", 25, Color(0.92, 0.84, 0.68, 0.96))
	_ending_text.anchor_left = 0.5
	_ending_text.anchor_top = 0.5
	_ending_text.anchor_right = 0.5
	_ending_text.anchor_bottom = 0.5
	_ending_text.offset_left = -500
	_ending_text.offset_right = 500
	_ending_text.offset_top = -120
	_ending_text.offset_bottom = 120
	_ending_text.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER
	_ending_text.vertical_alignment = VERTICAL_ALIGNMENT_CENTER
	_ending_text.autowrap_mode = TextServer.AUTOWRAP_WORD_SMART
	_ending.add_child(_ending_text)

	var again := Button.new()
	again.text = "重新开始"
	again.add_theme_font_override("font", font)
	again.add_theme_font_size_override("font_size", 18)
	again.anchor_left = 0.5
	again.anchor_top = 0.5
	again.anchor_right = 0.5
	again.anchor_bottom = 0.5
	again.offset_left = -130
	again.offset_top = 160
	again.offset_right = 130
	again.offset_bottom = 206
	again.pressed.connect(func(): restart_requested.emit())
	_ending.add_child(again)


func set_camera_mode(on: bool) -> void:
	_camera_overlay.visible = on
	_crosshair.visible = not on
	_controls.visible = not on
	_title.visible = not on
	_subtitle.visible = not on
	_controls.text = ("F 放下相机  ·  滚轮对焦  ·  左键快门  ·  E 检查  ·  R 二次曝光" if on
		else "WASD 移动  ·  鼠标 视角  ·  E 检查  ·  F 举镜  ·  Tab 记录本  ·  Esc 释放鼠标")
	if not on:
		_owner.visible = false
		_owner.modulate.a = 0.0


func set_focus(value: float, active: bool) -> void:
	_focus_ring.set_focus(value, active)
	_focus_label.text = "对焦  %d%%" % int(round(value * 100.0)) if active else ""
	_focus_label.add_theme_color_override("font_color",
		Color(0.45, 0.92, 0.62, 0.95) if value >= 0.88 else Color(0.92, 0.78, 0.56, 0.85))


func set_target(year: int, name_text: String) -> void:
	if year <= 0:
		_year_label.text = ""
	else:
		_year_label.text = "%d  ·  %s" % [year, name_text] if name_text != "" else str(year)


func set_prompt(text: String) -> void:
	_prompt.text = text


func set_status(text: String) -> void:
	_status.text = text


func set_plate(text: String) -> void:
	_plate.text = text


func set_key(taken: bool) -> void:
	_key.text = "钥匙：已取得" if taken else "钥匙：—"
	_key.add_theme_color_override("font_color",
		Color(0.95, 0.76, 0.35, 0.95) if taken else Color(0.6, 0.55, 0.45, 0.6))


func say(text: String, seconds := 4.0) -> void:
	if text.strip_edges() == "":
		return
	_narration.text = text
	_narration.modulate.a = 1.0
	if _say_tween and _say_tween.is_valid():
		_say_tween.kill()
	_say_tween = create_tween()
	_say_tween.tween_interval(maxf(1.0, seconds))
	_say_tween.tween_property(_narration, "modulate:a", 0.0, 0.6)


func toast(text: String) -> void:
	_toast.text = text
	_toast.modulate.a = 1.0
	var t := create_tween()
	t.tween_interval(1.8)
	t.tween_property(_toast, "modulate:a", 0.0, 0.5)


func flash(color := Color(1.0, 0.95, 0.82, 0.65)) -> void:
	_flash.color = color
	_flash.modulate.a = 0.0
	_flash.color.a = color.a
	var t := create_tween()
	t.tween_property(_flash, "modulate:a", 1.0, 0.05)
	t.tween_property(_flash, "modulate:a", 0.0, 0.35)


func show_owner() -> void:
	set_owner_visible(true)


func set_owner_visible(on: bool) -> void:
	_owner.visible = on
	_owner.modulate.a = 0.62 if on else 0.0


func open_notebook(pages: Array, start_index := 0) -> void:
	_notebook_pages = pages
	if _notebook_pages.is_empty():
		return
	_notebook_index = clampi(start_index, 0, _notebook_pages.size() - 1)
	_show_notebook_page(_notebook_index)
	_notebook.visible = true
	_notebook_open = true
	Input.mouse_mode = Input.MOUSE_MODE_VISIBLE


func _show_notebook_page(index: int) -> void:
	if _notebook_pages.is_empty():
		return
	_notebook_index = clampi(index, 0, _notebook_pages.size() - 1)
	var p: Dictionary = _notebook_pages[_notebook_index]
	_notebook_text.text = "[b]%s[/b]\n\n%s" % [
		String(p.get("title", "")), String(p.get("text", ""))]
	_notebook_page_label.text = "第 %d / %d 页  ·  A / D 翻页" % [
		_notebook_index + 1, _notebook_pages.size()]
	notebook_page_shown.emit(String(p.get("id", "")))


func notebook_next() -> void:
	if not _notebook_open:
		return
	if _notebook_index < _notebook_pages.size() - 1:
		_show_notebook_page(_notebook_index + 1)


func notebook_prev() -> void:
	if not _notebook_open:
		return
	if _notebook_index > 0:
		_show_notebook_page(_notebook_index - 1)


func notebook_current_page_id() -> String:
	if _notebook_pages.is_empty():
		return ""
	return String(_notebook_pages[_notebook_index].get("id", ""))


func close_notebook() -> void:
	_notebook.visible = false
	_notebook_open = false
	notebook_closed.emit()


func notebook_is_open() -> bool:
	return _notebook_open


func show_choice(title: String, body: String, options: Array) -> void:
	_camera_overlay.visible = false
	_owner.visible = false
	_crosshair.visible = false
	_prompt.text = ""
	_narration.text = ""
	_narration.modulate.a = 0.0
	_status.text = ""
	_plate.text = ""
	_toast.modulate.a = 0.0
	_choice_title.text = title
	_choice_text.text = body
	for i in 2:
		_choice_buttons[i].text = String(options[i]) if i < options.size() else ""
		_choice_buttons[i].visible = i < options.size()
	_choice.visible = true
	_choice_open = true
	Input.mouse_mode = Input.MOUSE_MODE_VISIBLE


func hide_choice() -> void:
	_choice.visible = false
	_choice_open = false


func choice_is_open() -> bool:
	return _choice_open


func _on_choice_pressed(index: int) -> void:
	hide_choice()
	choice_made.emit(index)


func show_ending(text: String) -> void:
	_camera_overlay.visible = false
	_notebook.visible = false
	_choice.visible = false
	_ending_text.text = text
	_ending.visible = true
	_ending_open = true
	Input.mouse_mode = Input.MOUSE_MODE_VISIBLE


func is_overlay_open() -> bool:
	return _notebook_open or _choice_open or _ending_open
