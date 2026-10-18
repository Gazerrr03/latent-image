extends CanvasLayer
## 标题页、暂停页、设置、操作说明（docs/01 第 11 节“界面”）。界面是纸：档案卡上的打字稿，不做现代游戏面板。
## 键盘：↑↓ / W S 移动，回车 / 空格 / E 确认，←→ / A D 调设置，Esc 返回；
## 鼠标：指向、点击，◂ ▸ 调设置，滚轮也能调。文字都在界面文字表 content/visual/ui.csv。

const H := preload("res://ui/hud_text.gd")
const PAPER := Color("#efe6d2")
const INK := Color("#1f1a14")
const RED := Color("#7a1f12")
const CREAM := Color("#e8dcc0")
## 档案卡上的横格线
const RULE := Color(0.45, 0.55, 0.68, 0.35)

var font: Font
var page := ""
## 暂停页是从游戏里打开的；标题页不是
var in_game := false
var _root: Control
var _bg: TextureRect
var _bg_tween: Tween
var _shade: ColorRect
var _rain: ColorRect
var _dim: ColorRect
var _title_block: VBoxContainer
var _holder: Control
var _card: Control
## 设置、操作说明按“返回”回到哪一页
var _back: Callable
var _sound := ""

const RAIN_SHADER := """shader_type canvas_item;
float h(vec2 p) { return fract(sin(dot(p, vec2(12.9898, 78.233))) * 43758.5453); }
void fragment() {
	vec2 uv = UV * vec2(160.0, 1.0);
	uv.x += UV.y * 18.0;
	float col = floor(uv.x);
	float speed = 0.9 + h(vec2(col, 1.0)) * 0.8;
	float y = fract(UV.y * 1.6 - TIME * speed + h(vec2(col, 2.0)));
	float streak = smoothstep(0.0, 0.03, y) * smoothstep(0.16, 0.03, y);
	float lane = smoothstep(0.5, 0.0, abs(fract(uv.x) - 0.5) * 6.0);
	float on = step(0.55, h(vec2(col, floor(TIME * 0.3 + h(vec2(col, 3.0))))));
	COLOR = vec4(vec3(0.75, 0.78, 0.85), streak * lane * on * 0.22);
}
"""


func _ready() -> void:
	layer = 15
	visible = false
	_root = Control.new()
	_root.set_anchors_preset(Control.PRESET_FULL_RECT)
	_root.mouse_filter = Control.MOUSE_FILTER_STOP
	_root.theme = Theme.new()
	_root.theme.default_font = font
	_root.theme.default_font_size = 22
	add_child(_root)

	_bg = TextureRect.new()
	_bg.set_anchors_preset(Control.PRESET_FULL_RECT)
	_bg.expand_mode = TextureRect.EXPAND_IGNORE_SIZE
	_bg.stretch_mode = TextureRect.STRETCH_KEEP_ASPECT_COVERED
	_bg.mouse_filter = Control.MOUSE_FILTER_IGNORE
	var path := "res://art/" + H.t("title_image")
	if ResourceLoader.exists(path):
		_bg.texture = load(path)
	_root.add_child(_bg)
	# 斜斜落下的雨丝
	_rain = ColorRect.new()
	_rain.set_anchors_preset(Control.PRESET_FULL_RECT)
	_rain.mouse_filter = Control.MOUSE_FILTER_IGNORE
	var rm := ShaderMaterial.new()
	rm.shader = Shader.new()
	rm.shader.code = RAIN_SHADER
	_rain.material = rm
	_root.add_child(_rain)
	# 左边压暗，标题与档案卡落在暗处
	_shade = ColorRect.new()
	_shade.set_anchors_preset(Control.PRESET_FULL_RECT)
	_shade.mouse_filter = Control.MOUSE_FILTER_IGNORE
	var sm := ShaderMaterial.new()
	sm.shader = Shader.new()
	sm.shader.code = "shader_type canvas_item;\nvoid fragment() { float a = mix(0.82, 0.12, smoothstep(0.0, 0.75, UV.x)); a = max(a, smoothstep(0.55, 1.0, UV.y) * 0.6); COLOR = vec4(0.02, 0.02, 0.03, a); }"
	_shade.material = sm
	_root.add_child(_shade)
	_dim = ColorRect.new()
	_dim.set_anchors_preset(Control.PRESET_FULL_RECT)
	_dim.color = Color(0, 0, 0, 0.62)
	_dim.mouse_filter = Control.MOUSE_FILTER_IGNORE
	_root.add_child(_dim)

	_title_block = VBoxContainer.new()
	_title_block.position = Vector2(140, 170)
	_title_block.add_theme_constant_override("separation", 6)
	_title_block.mouse_filter = Control.MOUSE_FILTER_IGNORE
	_root.add_child(_title_block)
	var tl := _label(H.t("title"), 76, CREAM)
	tl.add_theme_constant_override("shadow_offset_x", 2)
	tl.add_theme_constant_override("shadow_offset_y", 3)
	tl.add_theme_color_override("font_shadow_color", Color(0, 0, 0, 0.8))
	_title_block.add_child(tl)
	var sub := _label(H.t("title_sub"), 20, CREAM.darkened(0.25))
	_title_block.add_child(sub)

	_holder = Control.new()
	_holder.set_anchors_preset(Control.PRESET_FULL_RECT)
	_holder.mouse_filter = Control.MOUSE_FILTER_IGNORE
	_root.add_child(_holder)
	# 调试面板（F1）跳镜号时，标题页或暂停页自己收起来
	Director.shot_started.connect(func(_r):
		if visible and in_game:
			_resume()
		elif visible:
			_leave_title())


func is_open() -> bool:
	return visible


# ───────────── 标题页 ─────────────

## 进入标题页。有存档（GameState.shot 不为空）时第一项是“继续调查”
func show_title() -> void:
	in_game = false
	page = "title"
	visible = true
	_bg.show()
	_rain.show()
	_shade.show()
	_dim.hide()
	_title_block.show()
	Input.mouse_mode = Input.MOUSE_MODE_VISIBLE
	if _bg_tween:
		_bg_tween.kill()
	_bg.pivot_offset = _root.size / 2
	_bg.scale = Vector2.ONE
	_bg_tween = create_tween().set_loops()
	_bg_tween.tween_property(_bg, "scale", Vector2.ONE * 1.06, 40.0).set_trans(Tween.TRANS_SINE)
	_bg_tween.tween_property(_bg, "scale", Vector2.ONE, 40.0).set_trans(Tween.TRANS_SINE)
	_sound = H.t("title_sound")
	if _sound != "" and Director.world and not Director.autoplay:
		Director.world.play_sound(_sound)
	_page_title()


func _page_title() -> void:
	page = "title"
	_title_block.show()
	var v := _new_card("", Vector2(140, 400), 440, -1.2)
	if _has_save():
		_item(v, H.t("menu_continue"), _continue, H.day_line(GameState.shot, true))
	_item(v, H.t("menu_new"), _new_game)
	_item(v, H.t("menu_settings"), func(): _page_settings(_page_title))
	_item(v, H.t("menu_quit"), func(): get_tree().quit())
	_focus_first(v)


func _page_confirm() -> void:
	page = "confirm"
	_title_block.show()
	var v := _new_card("", Vector2(140, 400), 440, -1.2)
	var l := _label(H.t("confirm_new"), 20, INK)
	l.autowrap_mode = TextServer.AUTOWRAP_WORD_SMART
	l.custom_minimum_size.x = 380
	v.add_child(l)
	_rule(v)
	_item(v, H.t("confirm_no"), _page_title)
	_item(v, H.t("confirm_yes"), _start_new)
	_focus_first(v)


func _has_save() -> bool:
	return GameState.shot != "" and ContentDB.shots.has(GameState.shot)


func _continue() -> void:
	_leave_title()
	Director.start(GameState.shot)


func _new_game() -> void:
	if _has_save():
		_page_confirm()
	else:
		_start_new()


func _start_new() -> void:
	_leave_title()
	GameState.reset()
	Director.start()


func _leave_title() -> void:
	if _sound != "" and Director.world:
		Director.world.stop_loop(_sound)
	if _bg_tween:
		_bg_tween.kill()
	_close()


# ───────────── 暂停页 ─────────────

## 自由行走时按 Esc：玩家停住、放开鼠标
func open_pause() -> void:
	in_game = true
	visible = true
	_bg.hide()
	_rain.hide()
	_shade.hide()
	_dim.show()
	_title_block.hide()
	Director.world.set_frozen(true)
	Input.mouse_mode = Input.MOUSE_MODE_VISIBLE
	Director.world.play_sound(H.t("sound_pause"))
	_page_pause()


func _page_pause() -> void:
	page = "pause"
	var v := _new_card(H.t("pause_head"), Vector2.ZERO, 440, 0.8, H.day_line(GameState.shot))
	_item(v, H.t("pause_resume"), _resume)
	_item(v, H.t("pause_board"), _board)
	_item(v, H.t("pause_settings"), func(): _page_settings(_page_pause))
	_item(v, H.t("pause_controls"), func(): _page_controls(_page_pause))
	_item(v, H.t("pause_title"), _to_title)
	_focus_first(v)


func _resume() -> void:
	_close()
	Director.world.set_frozen(false)
	if Director.world.player and Director.world.player.active:
		Input.mouse_mode = Input.MOUSE_MODE_CAPTURED


## 证据板：盖在暂停页下面一层，所以先把暂停页收起来，看完再回来
func _board() -> void:
	visible = false
	await Director.ui.browse_board(false)
	visible = true
	Input.mouse_mode = Input.MOUSE_MODE_VISIBLE
	_page_pause()


## 回到标题：先存档，停下正在播放的分镜
func _to_title() -> void:
	GameState.save()
	_close()
	Director.world.set_frozen(false)
	await Director.stop()
	if Director.world.player:
		Director.world.player.deactivate()
	Director.world.stop_loops()
	Director.world.stop_music(0.0)
	show_title()


# ───────────── 设置与操作说明 ─────────────

func _page_settings(back: Callable) -> void:
	page = "settings"
	_back = back
	_title_block.hide()
	var v := _new_card(H.t("settings_head"), Vector2.ZERO, 620, 0.5)
	var on_off := func(b): return H.t("val_on") if b else H.t("val_off")
	_slider(v, "set_master", "master")
	_slider(v, "set_music", "music")
	_slider(v, "set_sfx", "sfx")
	_slider(v, "set_sens", "sens")
	_toggle(v, "set_invert", "invert_y", on_off)
	_toggle(v, "set_text", "text_instant", func(b): return H.t("val_instant") if b else H.t("val_typed"))
	_slider(v, "set_brightness", "brightness")
	_toggle(v, "set_window", "fullscreen", func(b): return H.t("val_fullscreen") if b else H.t("val_windowed"))
	_rule(v)
	_item(v, H.t("back"), func(): _back.call())
	_focus_first(v)


func _page_controls(back: Callable) -> void:
	page = "controls"
	_back = back
	_title_block.hide()
	var v := _new_card(H.t("controls_head"), Vector2.ZERO, 620, -0.6)
	for line in H.t("controls").split("\n", false):
		var row := HBoxContainer.new()
		row.add_theme_constant_override("separation", 18)
		var k := _label(line.get_slice("｜", 0), 20, INK)
		k.custom_minimum_size.x = 250
		row.add_child(k)
		row.add_child(_label(line.get_slice("｜", 1), 20, INK.lightened(0.15)))
		v.add_child(row)
		_rule(v)
	_item(v, H.t("back"), func(): _back.call())
	_focus_first(v)


## 0—10 档：“◂ 十个小方格 ▸”，填墨的格数就是档位
func _slider(v: VBoxContainer, label_id: String, key: String) -> void:
	var value := func() -> int: return int(Settings.get(key))
	var step := func(d: int) -> void: Settings.set_value(key, int(Settings.get(key)) + d)
	_setting_row(v, label_id, value, step, Callable())


func _toggle(v: VBoxContainer, label_id: String, key: String, show: Callable) -> void:
	var value := func() -> String: return show.call(bool(Settings.get(key)))
	var flip := func() -> void: Settings.set_value(key, not bool(Settings.get(key)))
	var step := func(_d: int) -> void: flip.call()
	_setting_row(v, label_id, value, step, flip)


## 设置的一行：整行可以获得焦点（键盘 ←→ / A D 调），两头的 ◂ ▸ 给鼠标点，滚轮也能调
## value 返回字符串（开 / 关之类）或 0—10 的档位
func _setting_row(v: VBoxContainer, label_id: String, value: Callable, step: Callable, press: Callable) -> void:
	var row := Button.new()
	_plain(row)
	row.custom_minimum_size = Vector2(540, 40)
	var h := HBoxContainer.new()
	h.set_anchors_preset(Control.PRESET_FULL_RECT)
	h.mouse_filter = Control.MOUSE_FILTER_PASS
	row.add_child(h)
	var name_l := _label("　" + H.t(label_id), 22, INK)
	name_l.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	h.add_child(name_l)
	var val := HBoxContainer.new()
	val.custom_minimum_size.x = 210
	val.alignment = BoxContainer.ALIGNMENT_CENTER
	val.add_theme_constant_override("separation", 4)
	val.mouse_filter = Control.MOUSE_FILTER_IGNORE
	var cells: Array = []
	var text := _label("", 18, INK)
	if value.call() is int:
		for i in Settings.STEPS:
			var c := Panel.new()
			c.custom_minimum_size = Vector2(13, 13)
			c.size_flags_vertical = Control.SIZE_SHRINK_CENTER
			c.mouse_filter = Control.MOUSE_FILTER_IGNORE
			val.add_child(c)
			cells.append(c)
	else:
		val.add_child(text)
	var refresh := func():
		var x = value.call()
		if x is int:
			for i in cells.size():
				cells[i].add_theme_stylebox_override("panel", _cell(i < x))
		else:
			text.text = x
	var dec := _arrow("◂", func(): step.call(-1); refresh.call())
	var inc := _arrow("▸", func(): step.call(1); refresh.call())
	h.add_child(dec)
	h.add_child(val)
	h.add_child(inc)
	refresh.call()
	row.gui_input.connect(func(e: InputEvent):
		var d := 0
		if e.is_action_pressed("ui_left") or (e is InputEventKey and e.pressed and e.physical_keycode == KEY_A):
			d = -1
		elif e.is_action_pressed("ui_right") or (e is InputEventKey and e.pressed and e.physical_keycode == KEY_D):
			d = 1
		elif e is InputEventMouseButton and e.pressed and e.button_index == MOUSE_BUTTON_WHEEL_UP:
			d = 1
		elif e is InputEventMouseButton and e.pressed and e.button_index == MOUSE_BUTTON_WHEEL_DOWN:
			d = -1
		if d != 0:
			step.call(d)
			refresh.call()
			row.accept_event())
	if press.is_valid():
		row.pressed.connect(func(): press.call(); refresh.call())
	row.focus_entered.connect(func():
		name_l.text = "▸ " + H.t(label_id)
		name_l.add_theme_color_override("font_color", RED))
	row.focus_exited.connect(func():
		name_l.text = "　" + H.t(label_id)
		name_l.add_theme_color_override("font_color", INK))
	row.mouse_entered.connect(row.grab_focus)
	v.add_child(row)
	_rule(v)


func _cell(filled: bool) -> StyleBoxFlat:
	var sb := StyleBoxFlat.new()
	sb.bg_color = INK if filled else Color(INK, 0.0)
	sb.set_border_width_all(1)
	sb.border_color = Color(INK, 0.7)
	return sb


func _arrow(text: String, f: Callable) -> Button:
	var b := Button.new()
	_plain(b)
	b.text = text
	b.focus_mode = Control.FOCUS_NONE
	b.custom_minimum_size.x = 30
	b.add_theme_color_override("font_color", INK.lightened(0.3))
	b.add_theme_color_override("font_hover_color", RED)
	b.pressed.connect(f)
	return b


# ───────────── 纸 ─────────────

## 一张档案卡：抬头（可空）、一道红线、下面一行行打字稿。pos 为零时放在屏幕正中
func _new_card(head: String, pos: Vector2, width: float, tilt_deg: float, sub := "") -> VBoxContainer:
	if _card:
		_card.queue_free()
	var p := PanelContainer.new()
	var sb := StyleBoxFlat.new()
	sb.bg_color = PAPER
	sb.content_margin_left = 40
	sb.content_margin_right = 40
	sb.content_margin_top = 30
	sb.content_margin_bottom = 30
	sb.shadow_color = Color(0, 0, 0, 0.55)
	sb.shadow_size = 14
	sb.shadow_offset = Vector2(4, 6)
	p.add_theme_stylebox_override("panel", sb)
	p.custom_minimum_size.x = width
	p.rotation_degrees = tilt_deg
	_holder.add_child(p)
	_card = p
	var v := VBoxContainer.new()
	v.add_theme_constant_override("separation", 4)
	p.add_child(v)
	if head != "":
		var hl := _label(head, 28, INK)
		v.add_child(hl)
		if sub != "":
			v.add_child(_label(sub, 17, INK.lightened(0.35)))
		var red := ColorRect.new()
		red.color = Color(RED, 0.75)
		red.custom_minimum_size.y = 2
		v.add_child(red)
		var gap := Control.new()
		gap.custom_minimum_size.y = 6
		v.add_child(gap)
	else:
		# 没有抬头的卡（标题页）：顶上只留那道红线
		var red := ColorRect.new()
		red.color = Color(RED, 0.75)
		red.custom_minimum_size.y = 2
		v.add_child(red)
	# 放好位置：pos 为零时，容器算出尺寸以后放到正中
	if pos == Vector2.ZERO:
		p.resized.connect(func():
			p.pivot_offset = p.size / 2
			p.position = (_root.size - p.size) / 2)
	else:
		p.position = pos
	return v


## 菜单的一项：一行打字稿；获得焦点（键盘或鼠标指向）时前面打一个 ▸、字变红
func _item(v: VBoxContainer, text: String, f: Callable, sub := "") -> Button:
	var b := Button.new()
	_plain(b)
	b.text = "　" + text
	b.alignment = HORIZONTAL_ALIGNMENT_LEFT
	b.add_theme_font_size_override("font_size", 24)
	b.add_theme_color_override("font_color", INK)
	b.add_theme_color_override("font_hover_color", RED)
	b.add_theme_color_override("font_focus_color", RED)
	b.add_theme_color_override("font_pressed_color", RED)
	b.focus_entered.connect(func(): b.text = "▸ " + text)
	b.focus_exited.connect(func(): b.text = "　" + text)
	b.mouse_entered.connect(b.grab_focus)
	b.pressed.connect(func():
		if Director.world:
			Director.world.play_sound(H.t("sound_select"))
		f.call())
	v.add_child(b)
	if sub != "":
		var l := _label("　　" + sub, 16, INK.lightened(0.35))
		v.add_child(l)
	_rule(v)
	return b


func _plain(b: Button) -> void:
	b.flat = true
	for s in ["normal", "hover", "pressed", "focus", "hover_pressed", "disabled"]:
		b.add_theme_stylebox_override(s, StyleBoxEmpty.new())


func _rule(v: VBoxContainer) -> void:
	var r := ColorRect.new()
	r.color = RULE
	r.custom_minimum_size.y = 1
	r.mouse_filter = Control.MOUSE_FILTER_IGNORE
	v.add_child(r)


func _label(text: String, size: int, color: Color) -> Label:
	var l := Label.new()
	l.text = text
	l.add_theme_font_size_override("font_size", size)
	l.add_theme_color_override("font_color", color)
	l.mouse_filter = Control.MOUSE_FILTER_IGNORE
	return l


func _focus_first(v: VBoxContainer) -> void:
	await get_tree().process_frame
	if not is_instance_valid(v) or v.is_queued_for_deletion():
		return
	for c in v.get_children():
		if c is Button and is_instance_valid(c):
			c.grab_focus()
			return


func _close() -> void:
	visible = false
	page = ""
	if _card:
		_card.queue_free()
		_card = null


# ───────────── 输入 ─────────────

func _input(event: InputEvent) -> void:
	if not visible or not (event is InputEventKey and event.pressed and not event.echo):
		return
	var f := get_viewport().gui_get_focus_owner()
	match event.physical_keycode:
		KEY_ESCAPE:
			get_viewport().set_input_as_handled()
			match page:
				"pause":
					_resume()
				"settings", "controls":
					_back.call()
				"confirm":
					_page_title()
		KEY_W, KEY_S:
			if f:
				var n: Control = f.find_prev_valid_focus() if event.physical_keycode == KEY_W else f.find_next_valid_focus()
				if n:
					n.grab_focus()
			get_viewport().set_input_as_handled()
		KEY_E:
			if f is Button:
				f.pressed.emit()
			get_viewport().set_input_as_handled()


## 截图自查：--menu=标题|暂停|设置|操作|确认
func open_for_capture(kind: String) -> void:
	match kind:
		"标题":
			show_title()
		"确认":
			show_title()
			_page_confirm()
		"暂停":
			open_pause()
		"设置":
			open_pause()
			_page_settings(_page_pause)
		"操作":
			open_pause()
			_page_controls(_page_pause)
