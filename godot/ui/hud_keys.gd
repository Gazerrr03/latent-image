extends HBoxContainer
## 屏幕左下角两枚纸质小图标：笔记本（Tab）、回想（Q），下面印着快捷键（docs/01 第 4 节，10-20）。
## 只在自由行走时出现；收进新线索时笔记本跳一下；没有可指的路时回想变灰。点图标与按键一样。

signal pressed(which: String)

const PAPER := Color("#e8dcc0")
const INK := Color("#2a221a")

var _cards := {}
var _dim := {}


func _ready() -> void:
	mouse_filter = Control.MOUSE_FILTER_IGNORE
	add_theme_constant_override("separation", 14)
	_card("notebook", "Tab", "笔记本")
	_card("guide", "Q", "回想")


func _card(which: String, key: String, caption: String) -> void:
	var v := VBoxContainer.new()
	v.add_theme_constant_override("separation", 3)
	v.mouse_filter = Control.MOUSE_FILTER_IGNORE
	var icon := Icon.new()
	icon.kind = which
	icon.custom_minimum_size = Vector2(52, 52)
	icon.mouse_filter = Control.MOUSE_FILTER_STOP
	icon.gui_input.connect(func(e):
		if e is InputEventMouseButton and e.pressed and e.button_index == MOUSE_BUTTON_LEFT:
			pressed.emit(which))
	v.add_child(icon)
	var k := Label.new()
	k.text = key
	k.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER
	k.add_theme_font_size_override("font_size", 14)
	k.add_theme_color_override("font_color", INK)
	var cap := StyleBoxFlat.new()
	cap.bg_color = PAPER
	cap.set_corner_radius_all(4)
	cap.set_border_width_all(1)
	cap.border_color = Color("#3a3128")
	cap.content_margin_left = 6
	cap.content_margin_right = 6
	k.add_theme_stylebox_override("normal", cap)
	k.size_flags_horizontal = Control.SIZE_SHRINK_CENTER
	v.add_child(k)
	var c := Label.new()
	c.text = caption
	c.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER
	c.add_theme_font_size_override("font_size", 13)
	c.add_theme_color_override("font_color", Color("#e8dcc0"))
	c.add_theme_color_override("font_shadow_color", Color.BLACK)
	c.add_theme_constant_override("shadow_offset_x", 1)
	c.add_theme_constant_override("shadow_offset_y", 1)
	v.add_child(c)
	add_child(v)
	_cards[which] = v
	_dim[which] = false


func set_gamepad(on: bool) -> void:
	_cards["notebook"].get_child(1).text = "Y / △" if on else "Tab"
	_cards["guide"].get_child(1).text = "X / □" if on else "Q"


func set_dim(which: String, on: bool) -> void:
	if _dim.get(which) == on:
		return
	_dim[which] = on
	_cards[which].modulate = Color(1, 1, 1, 0.35) if on else Color.WHITE


## 跳一下：笔记本收进新线索、按下按键时
func ping(which: String) -> void:
	var icon: Control = _cards[which].get_child(0)
	icon.pivot_offset = icon.size / 2
	var t := create_tween().set_trans(Tween.TRANS_BACK).set_ease(Tween.EASE_OUT)
	t.tween_property(icon, "scale", Vector2(1.18, 1.18), 0.12)
	t.tween_property(icon, "scale", Vector2.ONE, 0.3)


## 图标本身：纸卡上一笔一笔画出来（打字稿质感，不用扁平图标）
class Icon extends Control:
	var kind := "notebook"

	func _draw() -> void:
		var r := Rect2(Vector2.ZERO, size)
		draw_rect(r.grow(-1), Color("#e8dcc0"))
		draw_rect(r.grow(-1), Color("#3a3128"), false, 1.5)
		var ink := Color("#2a221a")
		var c := size / 2
		if kind == "notebook":
			# 合着的笔记本：封面、左边一排线圈、两行字
			var b := Rect2(c + Vector2(-13, -17), Vector2(28, 34))
			draw_rect(b, Color("#5a4632"))
			draw_rect(b, ink, false, 1.5)
			for i in 5:
				var y := b.position.y + 5 + i * 6
				draw_arc(Vector2(b.position.x, y), 2.6, 0, TAU, 10, Color("#c8bba0"), 1.2)
			draw_line(b.position + Vector2(8, 11), b.position + Vector2(23, 11), Color("#e8dcc0"), 1.4)
			draw_line(b.position + Vector2(8, 16), b.position + Vector2(20, 16), Color("#e8dcc0"), 1.4)
		else:
			# 一左一右两只鞋印，一前一后
			_shoe(c + Vector2(-7, 5), ink)
			_shoe(c + Vector2(7, -7), ink)

	func _shoe(at: Vector2, ink: Color) -> void:
		var sole := PackedVector2Array()
		for i in 24:
			var a := TAU * i / 24.0
			sole.append(at + Vector2(cos(a) * 5.0, sin(a) * 7.0 - 3.0))
		draw_colored_polygon(sole, ink)
		var heel := PackedVector2Array()
		for i in 16:
			var a := TAU * i / 16.0
			heel.append(at + Vector2(cos(a) * 4.0, sin(a) * 3.0 + 8.0))
		draw_colored_polygon(heel, ink)
