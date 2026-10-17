extends CanvasLayer
## 临时界面层（灰盒阶段）：文字框、选项、提示、宽银幕黑边、冲洗底片。
## 之后会逐步换成场景中的实物 UI（纸、打字机、证据板），但 Director 调用的接口保持不变：
## show_text / choose / cancel / toast / set_objective / set_progress / set_cinematic / wait_seconds

signal _resolved(value: int)

const PAPER := Color("#efe6d2")
const INK := Color("#1f1a14")
const BAR_RATIO := 0.128  # 16:9 画面上加 2.39:1 黑边
const EvidenceBoard := preload("res://ui/evidence_board.gd")
const MediaFx := preload("res://ui/media_fx.gd")

var font: SystemFont
var _waiting := false
var _typing: Tween
var _prev_mouse := Input.MOUSE_MODE_VISIBLE

var bar_top: ColorRect
var bar_bottom: ColorRect
var text_panel: PanelContainer
var text_label: RichTextLabel
var more_label: Label
var choice_panel: PanelContainer
var choice_box: VBoxContainer
var choice_title: Label
var objective_label: Label
var toast_label: Label
var hint_label: Label
var progress_label: Label
var checklist_box: VBoxContainer
var crosshair: Label
var board: Control
var develop_layer: ColorRect
var develop_image: TextureRect
var develop_label: Label
var fx: CanvasLayer
var footage: CanvasLayer
var interlude_layer: ColorRect
var interlude_box: VBoxContainer
var interlude_more: Label


func _ready() -> void:
	layer = 10
	font = SystemFont.new()
	font.font_names = PackedStringArray(["Songti SC", "STSong", "Noto Serif CJK SC", "Source Han Serif SC", "SimSun", "PingFang SC"])
	var root := Control.new()
	root.set_anchors_preset(Control.PRESET_FULL_RECT)
	root.mouse_filter = Control.MOUSE_FILTER_IGNORE
	root.theme = Theme.new()
	root.theme.default_font = font
	root.theme.default_font_size = 22
	add_child(root)

	bar_top = _bar(root, true)
	bar_bottom = _bar(root, false)

	# 证据板盖在黑边之上、文字框之下
	board = EvidenceBoard.new()
	root.add_child(board)
	_build_develop(root)

	text_panel = _paper_panel()
	text_panel.set_anchors_preset(Control.PRESET_CENTER_BOTTOM)
	text_panel.anchor_left = 0.18
	text_panel.anchor_right = 0.82
	text_panel.anchor_top = 0.66
	text_panel.anchor_bottom = 0.95
	var v := VBoxContainer.new()
	text_panel.add_child(v)
	text_label = RichTextLabel.new()
	text_label.fit_content = true
	text_label.bbcode_enabled = false
	text_label.add_theme_color_override("default_color", INK)
	text_label.size_flags_vertical = Control.SIZE_EXPAND_FILL
	v.add_child(text_label)
	more_label = Label.new()
	more_label.text = "▸"
	more_label.horizontal_alignment = HORIZONTAL_ALIGNMENT_RIGHT
	more_label.add_theme_color_override("font_color", INK)
	v.add_child(more_label)
	root.add_child(text_panel)
	text_panel.hide()

	choice_panel = _paper_panel()
	choice_panel.set_anchors_preset(Control.PRESET_CENTER)
	choice_panel.anchor_left = 0.3
	choice_panel.anchor_right = 0.7
	choice_panel.anchor_top = 0.3
	choice_panel.anchor_bottom = 0.3
	choice_box = VBoxContainer.new()
	choice_box.add_theme_constant_override("separation", 10)
	choice_panel.add_child(choice_box)
	choice_title = Label.new()
	choice_title.add_theme_color_override("font_color", INK.lightened(0.3))
	choice_title.add_theme_font_size_override("font_size", 18)
	root.add_child(choice_panel)
	choice_panel.hide()

	objective_label = _label(root, Control.PRESET_CENTER_TOP, 20)
	objective_label.offset_top = 70
	toast_label = _label(root, Control.PRESET_CENTER_TOP, 18)
	toast_label.offset_top = 110
	hint_label = _label(root, Control.PRESET_CENTER, 18)
	hint_label.offset_top = 40
	progress_label = _label(root, Control.PRESET_TOP_LEFT, 18)
	progress_label.offset_left = 24
	progress_label.offset_top = 24
	# 自由检查时的观察清单：这一轮要看的每样东西，一句带方向的问题；看过的变暗、打勾
	checklist_box = VBoxContainer.new()
	checklist_box.position = Vector2(24, 54)
	checklist_box.add_theme_constant_override("separation", 6)
	checklist_box.mouse_filter = Control.MOUSE_FILTER_IGNORE
	root.add_child(checklist_box)
	crosshair = _label(root, Control.PRESET_CENTER, 18)
	crosshair.text = "·"

	_build_interlude(root)
	GameState.changed.connect(_refresh)
	_refresh()


func _bar(root: Control, top: bool) -> ColorRect:
	var r := ColorRect.new()
	r.color = Color.BLACK
	r.mouse_filter = Control.MOUSE_FILTER_IGNORE
	r.anchor_left = 0
	r.anchor_right = 1
	r.anchor_top = 0.0 if top else 1.0 - BAR_RATIO
	r.anchor_bottom = BAR_RATIO if top else 1.0
	root.add_child(r)
	return r


func _paper_panel() -> PanelContainer:
	var p := PanelContainer.new()
	var sb := StyleBoxFlat.new()
	sb.bg_color = PAPER
	sb.set_content_margin_all(24)
	sb.shadow_color = Color(0, 0, 0, 0.5)
	sb.shadow_size = 12
	p.add_theme_stylebox_override("panel", sb)
	p.grow_horizontal = Control.GROW_DIRECTION_BOTH
	p.grow_vertical = Control.GROW_DIRECTION_BOTH
	return p


func _label(root: Control, preset: int, size: int) -> Label:
	var l := Label.new()
	l.set_anchors_preset(preset)
	l.grow_horizontal = Control.GROW_DIRECTION_BOTH
	l.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER
	l.add_theme_font_size_override("font_size", size)
	l.add_theme_color_override("font_color", Color("#e8dcc0"))
	l.add_theme_color_override("font_shadow_color", Color.BLACK)
	l.mouse_filter = Control.MOUSE_FILTER_IGNORE
	root.add_child(l)
	return l


func _refresh() -> void:
	pass


## 暗房：红灯下的显影盘。相纸先是一片白，随着显影慢慢浮出影像
func _build_develop(root: Control) -> void:
	develop_layer = ColorRect.new()
	develop_layer.set_anchors_preset(Control.PRESET_FULL_RECT)
	develop_layer.color = Color("#1a0503")
	develop_layer.mouse_filter = Control.MOUSE_FILTER_STOP
	root.add_child(develop_layer)
	var tray := ColorRect.new()
	tray.color = Color("#2a0a06")
	tray.anchor_left = 0.3
	tray.anchor_right = 0.7
	tray.anchor_top = 0.14
	tray.anchor_bottom = 0.78
	develop_layer.add_child(tray)
	var paper := ColorRect.new()
	paper.color = Color("#f2e8e0")
	paper.set_anchors_preset(Control.PRESET_FULL_RECT)
	paper.offset_left = 24
	paper.offset_top = 24
	paper.offset_right = -24
	paper.offset_bottom = -24
	tray.add_child(paper)
	develop_image = TextureRect.new()
	develop_image.set_anchors_preset(Control.PRESET_FULL_RECT)
	develop_image.expand_mode = TextureRect.EXPAND_IGNORE_SIZE
	develop_image.stretch_mode = TextureRect.STRETCH_KEEP_ASPECT_CENTERED
	paper.add_child(develop_image)
	develop_label = Label.new()
	develop_label.set_anchors_preset(Control.PRESET_FULL_RECT)
	develop_label.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER
	develop_label.vertical_alignment = VERTICAL_ALIGNMENT_CENTER
	develop_label.add_theme_font_size_override("font_size", 26)
	develop_label.add_theme_color_override("font_color", Color("#2a1a14"))
	paper.add_child(develop_label)
	develop_layer.hide()


## 章末黑场：盖在所有界面之上，中间一列字幕
func _build_interlude(root: Control) -> void:
	interlude_layer = ColorRect.new()
	interlude_layer.set_anchors_preset(Control.PRESET_FULL_RECT)
	interlude_layer.color = Color.BLACK
	interlude_layer.mouse_filter = Control.MOUSE_FILTER_STOP
	root.add_child(interlude_layer)
	var center := CenterContainer.new()
	center.set_anchors_preset(Control.PRESET_FULL_RECT)
	center.mouse_filter = Control.MOUSE_FILTER_IGNORE
	interlude_layer.add_child(center)
	interlude_box = VBoxContainer.new()
	interlude_box.custom_minimum_size.x = 760
	interlude_box.add_theme_constant_override("separation", 18)
	center.add_child(interlude_box)
	interlude_more = Label.new()
	interlude_more.text = "▸"
	interlude_more.set_anchors_preset(Control.PRESET_BOTTOM_RIGHT)
	interlude_more.position = Vector2(-90, -80)
	interlude_more.add_theme_color_override("font_color", Color("#8a8070"))
	interlude_layer.add_child(interlude_more)
	interlude_layer.hide()


# ───────────── Director 调用的接口 ─────────────

func show_text(text: String) -> void:
	# 取景器 / 档案卡叠加时，文字以纪录片字幕的形式出现
	if footage and footage.active:
		await footage.subtitle(text)
		return
	if Director.autoplay:
		print("  │ ", text.replace("\n", "\n  │ "))
		return
	_release_mouse()
	text_label.text = text
	text_label.visible_ratio = 0.0
	more_label.modulate.a = 0.0
	text_panel.show()
	_typing = create_tween()
	_typing.tween_property(text_label, "visible_ratio", 1.0, clampf(text.length() * 0.03, 0.3, 2.5))
	_typing.tween_property(more_label, "modulate:a", 1.0, 0.3)
	_waiting = true
	await _resolved
	_waiting = false
	text_panel.hide()
	_restore_mouse()


## 返回所选序号；被 cancel() 打断时返回 -1
func choose(title: String, options: Array) -> int:
	if Director.autoplay:
		return 0
	_release_mouse()
	for c in choice_box.get_children():
		choice_box.remove_child(c)
		c.queue_free()
	choice_title = Label.new()
	choice_title.text = title
	choice_title.add_theme_color_override("font_color", INK.lightened(0.35))
	choice_title.add_theme_font_size_override("font_size", 18)
	choice_box.add_child(choice_title)
	for i in options.size():
		var b := Button.new()
		b.text = str(options[i])
		b.flat = true
		b.alignment = HORIZONTAL_ALIGNMENT_LEFT
		b.add_theme_color_override("font_color", INK)
		b.add_theme_color_override("font_hover_color", Color("#7a1f12"))
		b.pressed.connect(func(): _resolved.emit(i))
		choice_box.add_child(b)
	choice_panel.show()
	var k: int = await _resolved
	choice_panel.hide()
	_restore_mouse()
	return k


func cancel() -> void:
	_resolved.emit(-1)
	board.cancel()
	develop_layer.hide()
	interlude_layer.hide()
	interlude_box.modulate.a = 1.0
	if footage:
		footage.cancel()


# ───────────── 实物 UI ─────────────

func board_pick_pair(title: String) -> Array:
	_release_mouse()
	objective_label.visible = false
	var pair: Array = await board.pick_pair(title)
	return pair


func board_result(a: String, b: String, ok: bool) -> void:
	await board.show_result(a, b, ok)


func board_open(title: String) -> void:
	_release_mouse()
	board.open(title)


func board_close() -> void:
	board.close()
	objective_label.visible = true
	_restore_mouse()


## 第 6 章：亲手冲洗底片。显影（影像从白纸上慢慢浮出）→ 定影。
## image 是 art/footage/ 下的图片；还没交付时显示占位文字
func develop(image: String) -> void:
	var tex: Texture2D = null
	var path := "res://art/footage/" + image
	if image != "" and ResourceLoader.exists(path):
		tex = load(path)
	develop_image.texture = tex
	develop_label.text = "" if tex else "（叠印：一张清晰的脸）\n图片待美术交付：art/footage/%s" % image
	if Director.autoplay:
		print("  ◐ 显影：", image)
		return
	develop_image.modulate.a = 0.0
	develop_label.modulate.a = 0.0
	set_hud(false)
	develop_layer.show()
	# 选项框移到显影盘下方，别挡住正在浮出来的脸
	choice_panel.anchor_top = 0.84
	choice_panel.anchor_bottom = 0.84
	await choose("暗房", ["把底片放进显影液"])
	var t := create_tween().set_parallel()
	t.tween_property(develop_image, "modulate:a", 1.0, 6.0).set_ease(Tween.EASE_IN)
	t.tween_property(develop_label, "modulate:a", 1.0, 6.0).set_ease(Tween.EASE_IN)
	await t.finished
	await choose("暗房", ["放进定影液"])
	choice_panel.anchor_top = 0.3
	choice_panel.anchor_bottom = 0.3
	develop_layer.hide()
	set_hud(true)


## 一章结束：画面暗下去，字幕一行一行浮出来（当天的复盘），点击后黑场慢慢退去，进入下一镜。
## lines：[{text, title}]，title = true 的一行是顶上的日期
func interlude(lines: Array) -> void:
	if Director.autoplay:
		for l in lines:
			print("  ▬ ", String(l["text"]).replace("\n", "\n  ▬ "))
		return
	_release_mouse()
	set_hud(false)
	for c in interlude_box.get_children():
		c.queue_free()
	interlude_more.modulate.a = 0.0
	interlude_layer.modulate.a = 0.0
	interlude_layer.show()
	var t := create_tween()
	t.tween_property(interlude_layer, "modulate:a", 1.0, 1.4)
	await t.finished
	await wait_seconds(0.5)
	for l in lines:
		var lb := Label.new()
		lb.text = l["text"]
		lb.autowrap_mode = TextServer.AUTOWRAP_WORD_SMART
		lb.custom_minimum_size.x = 760
		if l.get("title", false):
			lb.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER
			lb.add_theme_font_size_override("font_size", 20)
			lb.add_theme_color_override("font_color", Color("#9c917c"))
		else:
			lb.add_theme_font_size_override("font_size", 23)
			lb.add_theme_color_override("font_color", Color("#e8dcc0"))
		lb.modulate.a = 0.0
		interlude_box.add_child(lb)
		var f := create_tween()
		f.tween_property(lb, "modulate:a", 1.0, 1.0)
		await f.finished
		if not interlude_layer.visible:
			return
		await wait_seconds(0.6 if l.get("title", false) else 0.9)
	create_tween().tween_property(interlude_more, "modulate:a", 1.0, 0.4)
	_typing = null
	_waiting = true
	await _resolved
	_waiting = false
	var out := create_tween()
	out.tween_property(interlude_box, "modulate:a", 0.0, 0.8)
	await out.finished
	set_hud(true)
	_restore_mouse()
	# 黑场在下一镜开始以后才退去：早晨的画面从黑里慢慢亮起来
	var lift := create_tween()
	lift.tween_interval(0.4)
	lift.tween_property(interlude_layer, "modulate:a", 0.0, 2.0)
	lift.tween_callback(func():
		interlude_layer.hide()
		interlude_box.modulate.a = 1.0)


func wait_seconds(sec: float) -> void:
	await get_tree().create_timer(sec).timeout


func toast(text: String) -> void:
	if Director.autoplay:
		print("  ※ ", text)
		return
	toast_label.text = text
	toast_label.modulate.a = 1.0
	var t := create_tween()
	t.tween_interval(2.0)
	t.tween_property(toast_label, "modulate:a", 0.0, 0.8)


func set_objective(text: String) -> void:
	objective_label.text = text


func set_progress(done: int, total: int) -> void:
	progress_label.text = "" if total == 0 else "手记 %d / %d" % [done, total]


## items：[{text, done}]；空数组清掉清单
func set_checklist(items: Array) -> void:
	for c in checklist_box.get_children():
		c.queue_free()
	for it in items:
		var l := Label.new()
		l.text = ("✓  " if it["done"] else "·  ") + String(it["text"])
		l.add_theme_font_size_override("font_size", 17)
		l.add_theme_color_override("font_color", Color("#8f8778") if it["done"] else Color("#efe3c6"))
		l.add_theme_color_override("font_shadow_color", Color.BLACK)
		l.add_theme_constant_override("shadow_offset_x", 1)
		l.add_theme_constant_override("shadow_offset_y", 1)
		checklist_box.add_child(l)


func set_hint(text: String) -> void:
	hint_label.text = text


## 播放影像档案、冲洗底片时隐藏目标、提示等界面
func set_hud(on: bool) -> void:
	for n in [objective_label, hint_label, progress_label, checklist_box, toast_label, crosshair]:
		n.visible = on
	if on:
		_refresh()


func set_cinematic(on: bool) -> void:
	crosshair.visible = not on
	var t := create_tween().set_parallel()
	t.tween_property(bar_top, "modulate:a", 1.0 if on else 0.0, 0.6)
	t.tween_property(bar_bottom, "modulate:a", 1.0 if on else 0.0, 0.6)


# ───────────── 输入 ─────────────

## Tab：随时翻开证据板，一张一张拿起来看（不在问话、选项、读字的时候）
func _unhandled_input(event: InputEvent) -> void:
	if not (event is InputEventKey and event.pressed and not event.echo and event.physical_keycode == KEY_TAB):
		return
	if board.visible or _waiting or choice_panel.visible or develop_layer.visible or interlude_layer.visible or Director.autoplay:
		return
	if footage and footage.active:
		return
	get_viewport().set_input_as_handled()
	_release_mouse()
	objective_label.visible = false
	Director.world.set_frozen(true)
	await board.browse()
	Director.world.set_frozen(false)
	objective_label.visible = true
	_restore_mouse()


func _input(event: InputEvent) -> void:
	if not _waiting:
		return
	var click: bool = event is InputEventMouseButton and event.pressed and event.button_index == MOUSE_BUTTON_LEFT
	var key: bool = event.is_action_pressed("ui_accept")
	if not (click or key):
		return
	get_viewport().set_input_as_handled()
	if _typing and _typing.is_running():
		_typing.kill()
		text_label.visible_ratio = 1.0
		more_label.modulate.a = 1.0
		return
	_resolved.emit(0)


func _release_mouse() -> void:
	_prev_mouse = Input.mouse_mode
	Input.mouse_mode = Input.MOUSE_MODE_VISIBLE


func _restore_mouse() -> void:
	Input.mouse_mode = _prev_mouse
