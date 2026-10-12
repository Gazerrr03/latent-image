extends CanvasLayer
## 临时界面层（灰盒阶段）：文字框、选项、提示、电报纸计数、宽银幕黑边。
## 之后会逐步换成场景中的实物 UI（纸、打字机、证据板），但 Director 调用的接口保持不变：
## show_text / choose / cancel / toast / set_objective / set_progress / set_cinematic / wait_seconds

signal _resolved(value: int)

const PAPER := Color("#efe6d2")
const INK := Color("#1f1a14")
const BAR_RATIO := 0.128  # 16:9 画面上加 2.39:1 黑边
const EvidenceBoard := preload("res://ui/evidence_board.gd")
const RegisterView := preload("res://ui/register_view.gd")

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
var telegram_label: Label
var toast_label: Label
var hint_label: Label
var progress_label: Label
var crosshair: Label
var board: Control
var register: Control
var telegrams: HBoxContainer
var telegram_note: Label


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

	# 证据板与访客簿盖在黑边之上、文字框之下
	board = EvidenceBoard.new()
	root.add_child(board)
	register = RegisterView.new()
	root.add_child(register)

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
	telegram_label = _label(root, Control.PRESET_TOP_RIGHT, 18)
	telegram_label.visible = false
	# 七张电报纸：每个节点撕下一张（节点预算，docs/01 第 4 节）
	telegrams = HBoxContainer.new()
	telegrams.set_anchors_preset(Control.PRESET_TOP_RIGHT)
	telegrams.position = Vector2(-24 - 7 * 30, 22)
	telegrams.add_theme_constant_override("separation", -10)
	telegrams.mouse_filter = Control.MOUSE_FILTER_IGNORE
	root.add_child(telegrams)
	for i in GameState.TELEGRAMS:
		var slip := Panel.new()
		slip.custom_minimum_size = Vector2(38, 52)
		var ssb := StyleBoxFlat.new()
		ssb.bg_color = Color("#e9dfc6")
		ssb.border_color = Color("#9a8a68")
		ssb.set_border_width_all(1)
		ssb.shadow_color = Color(0, 0, 0, 0.5)
		ssb.shadow_size = 3
		slip.add_theme_stylebox_override("panel", ssb)
		slip.rotation_degrees = float(i % 3) - 1.0
		slip.mouse_filter = Control.MOUSE_FILTER_IGNORE
		telegrams.add_child(slip)
	telegram_note = _label(root, Control.PRESET_TOP_RIGHT, 13)
	telegram_note.position = Vector2(-150, 80)
	telegram_note.text = "已读 21:40"
	toast_label = _label(root, Control.PRESET_CENTER_TOP, 18)
	toast_label.offset_top = 110
	hint_label = _label(root, Control.PRESET_CENTER, 18)
	hint_label.offset_top = 40
	progress_label = _label(root, Control.PRESET_TOP_LEFT, 18)
	progress_label.offset_left = 24
	progress_label.offset_top = 24
	crosshair = _label(root, Control.PRESET_CENTER, 18)
	crosshair.text = "·"

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
	var slips := telegrams.get_children()
	for i in slips.size():
		var keep := i < GameState.telegrams_left
		if slips[i].visible and not keep and not Director.autoplay:
			# 撕下一张：向上飘走
			var t := create_tween().set_parallel()
			t.tween_property(slips[i], "position:y", -40.0, 0.5)
			t.tween_property(slips[i], "modulate:a", 0.0, 0.5)
			t.chain().tween_callback(func(): slips[i].visible = false)
		elif keep:
			slips[i].visible = true
			slips[i].modulate.a = 1.0
			slips[i].position.y = 0
	# 渗漏 L2 起，电报纸边缘出现“已读 21:40”
	telegram_note.visible = GameState.leak_level >= 2


# ───────────── Director 调用的接口 ─────────────

func show_text(text: String) -> void:
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
	register.cancel()


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


func register_pick(title: String, alive: Array) -> int:
	_release_mouse()
	var k: int = await register.pick(title, alive)
	_restore_mouse()
	return k


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


func set_hint(text: String) -> void:
	hint_label.text = text


func set_cinematic(on: bool) -> void:
	crosshair.visible = not on
	var t := create_tween().set_parallel()
	t.tween_property(bar_top, "modulate:a", 1.0 if on else 0.0, 0.6)
	t.tween_property(bar_bottom, "modulate:a", 1.0 if on else 0.0, 0.6)


# ───────────── 输入 ─────────────

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
