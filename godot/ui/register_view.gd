extends Control
## 访客簿（名册）：指认就是落笔划去一个名字（docs/01 第 4 节）。
## 已被划去的名字带着划痕，旁边是打字印与回执用语；渗漏等级越高，回执用语越现代。

signal _picked(index: int)

const PAGE := Color("#ece2c9")
const INK := Color("#1f1a14")
const RULE := Color("#b9a98a")

var page: PanelContainer
var list: VBoxContainer
var title_label: Label


func _ready() -> void:
	set_anchors_and_offsets_preset(Control.PRESET_FULL_RECT)
	mouse_filter = Control.MOUSE_FILTER_STOP
	var dim := ColorRect.new()
	dim.set_anchors_and_offsets_preset(Control.PRESET_FULL_RECT)
	dim.color = Color(0, 0, 0, 0.55)
	dim.mouse_filter = Control.MOUSE_FILTER_IGNORE
	add_child(dim)
	page = PanelContainer.new()
	page.anchor_left = 0.3
	page.anchor_right = 0.7
	page.anchor_top = 0.16
	page.anchor_bottom = 0.84
	page.offset_left = 0
	page.offset_right = 0
	page.offset_top = 0
	page.offset_bottom = 0
	var sb := StyleBoxFlat.new()
	sb.bg_color = PAGE
	sb.set_content_margin_all(36)
	sb.shadow_color = Color(0, 0, 0, 0.6)
	sb.shadow_size = 16
	page.add_theme_stylebox_override("panel", sb)
	add_child(page)
	var v := VBoxContainer.new()
	v.add_theme_constant_override("separation", 6)
	page.add_child(v)
	title_label = Label.new()
	title_label.add_theme_color_override("font_color", INK.lightened(0.35))
	title_label.add_theme_font_size_override("font_size", 18)
	v.add_child(title_label)
	var head := Label.new()
	head.text = "访客簿　·　十月三日"
	head.add_theme_color_override("font_color", INK)
	head.add_theme_font_size_override("font_size", 26)
	v.add_child(head)
	list = VBoxContainer.new()
	list.add_theme_constant_override("separation", 0)
	v.add_child(list)
	hide()


## 列出名册；alive 中的名字可以点。返回 alive 中的序号；被打断时返回 -1
func pick(title: String, alive: Array) -> int:
	title_label.text = title
	for c in list.get_children():
		c.queue_free()
	_add_row("罗伊德先生", true, -1)
	for who in GameState.SUSPECTS:
		var idx := alive.find(who)
		_add_row(who, idx < 0, idx)
	show()
	var k: int = await _picked
	if k >= 0:
		await _strike(alive[k])
	hide()
	return k


func cancel() -> void:
	_picked.emit(-1)


func _receipt_word() -> String:
	return "ACK" if GameState.leak_level >= 4 else ("已确认" if GameState.leak_level >= 3 else "已收悉")


func _add_row(who: String, struck: bool, idx: int) -> void:
	var row := Control.new()
	row.custom_minimum_size = Vector2(0, 58)
	row.name = who
	var l := Label.new()
	l.text = who
	l.position = Vector2(8, 10)
	l.add_theme_font_size_override("font_size", 28)
	l.add_theme_color_override("font_color", INK.lightened(0.45) if struck else INK)
	row.add_child(l)
	var rule := ColorRect.new()
	rule.color = RULE
	rule.anchor_right = 1.0
	rule.position.y = 56
	rule.size.y = 1
	row.add_child(rule)
	list.add_child(row)
	if struck:
		_add_strike(row, l, 1.0)
	else:
		row.mouse_filter = Control.MOUSE_FILTER_STOP
		row.mouse_default_cursor_shape = Control.CURSOR_POINTING_HAND
		row.mouse_entered.connect(func(): l.add_theme_color_override("font_color", Color("#7a1f12")))
		row.mouse_exited.connect(func(): l.add_theme_color_override("font_color", INK))
		row.gui_input.connect(func(ev):
			if ev is InputEventMouseButton and ev.pressed and ev.button_index == MOUSE_BUTTON_LEFT:
				_picked.emit(idx))


func _add_strike(row: Control, l: Label, ratio: float) -> ColorRect:
	var s := ColorRect.new()
	s.name = "strike"
	s.color = INK
	s.position = Vector2(2, 30)
	s.size = Vector2((l.get_minimum_size().x + 12) * ratio, 3)
	row.add_child(s)
	var mark := Label.new()
	mark.text = "e　" + _receipt_word()
	mark.position = Vector2(l.get_minimum_size().x + 30, 18)
	mark.add_theme_font_size_override("font_size", 14)
	mark.add_theme_color_override("font_color", INK.lightened(0.25))
	mark.modulate.a = ratio
	mark.name = "mark"
	row.add_child(mark)
	return s


## 落笔：一道划痕从左到右划过名字，然后浮现打字印与回执
func _strike(who: String) -> void:
	var row := list.get_node_or_null(who)
	if row == null:
		return
	var l: Label = row.get_child(0)
	var s := _add_strike(row, l, 0.0)
	var mark: Label = row.get_node("mark")
	var t := create_tween()
	t.tween_property(s, "size:x", l.get_minimum_size().x + 12, 0.45).set_ease(Tween.EASE_OUT)
	t.tween_interval(0.3)
	t.tween_property(mark, "modulate:a", 1.0, 0.6)
	t.tween_interval(0.6)
	await t.finished
