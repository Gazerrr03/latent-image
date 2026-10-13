extends Control
## 证据板（参考 Ghost in the SQL Data）：软木板上钉着证据卡片，点一张、再点另一张拉红线。
## 连对：红线留在板上；连错：红线抖一下弹回，不惩罚（docs/01 第 4.2 节）。

signal _picked(pair: Array)

const CARD_SIZE := Vector2(230, 128)
const RED := Color("#a3201a")
const PAPER := Color("#efe6d2")
const INK := Color("#1f1a14")

var font: Font
var title_label: Label
var hint_label: Label
var cards := {}
var _first := ""
var _strings: Node2D


func _ready() -> void:
	set_anchors_and_offsets_preset(Control.PRESET_FULL_RECT)
	mouse_filter = Control.MOUSE_FILTER_STOP
	var bg := ColorRect.new()
	bg.set_anchors_and_offsets_preset(Control.PRESET_FULL_RECT)
	bg.mouse_filter = Control.MOUSE_FILTER_IGNORE
	var mat := ShaderMaterial.new()
	mat.shader = load("res://shaders/cork.gdshader")
	bg.material = mat
	add_child(bg)
	title_label = Label.new()
	title_label.position = Vector2(48, 28)
	title_label.add_theme_font_size_override("font_size", 26)
	title_label.add_theme_color_override("font_color", Color("#f3ead6"))
	title_label.add_theme_color_override("font_shadow_color", Color(0, 0, 0, 0.7))
	add_child(title_label)
	hint_label = Label.new()
	hint_label.set_anchors_and_offsets_preset(Control.PRESET_BOTTOM_LEFT)
	hint_label.position = Vector2(48, -60)
	hint_label.add_theme_font_size_override("font_size", 18)
	hint_label.add_theme_color_override("font_color", Color("#f3ead6"))
	hint_label.add_theme_color_override("font_shadow_color", Color(0, 0, 0, 0.7))
	add_child(hint_label)
	_strings = Node2D.new()
	_strings.z_index = 5
	add_child(_strings)
	hide()


## 打开证据板，等玩家依次点两张卡片。返回 [证据a, 证据b]；被打断时返回 []
func pick_pair(title: String) -> Array:
	open(title)
	hint_label.text = "点一张卡片拉起红线，再点另一张。"
	var pair: Array = await _picked
	return pair


func open(title: String) -> void:
	title_label.text = title
	_rebuild()
	show()


func close() -> void:
	hide()


func cancel() -> void:
	_picked.emit([])


## 播放连线结果
func show_result(a: String, b: String, ok: bool) -> void:
	if not cards.has(a) or not cards.has(b):
		return
	var line := _make_string(a, b)
	_strings.add_child(line)
	if ok:
		hint_label.text = ""
		var t := create_tween()
		t.tween_property(line, "width", 4.0, 0.25).from(1.0)
		await t.finished
		return
	hint_label.text = "红线抖了一下，弹回原处。"
	var t2 := create_tween()
	for i in 4:
		t2.tween_property(line, "position", Vector2(0, 6 if i % 2 == 0 else -6), 0.05)
	t2.tween_property(line, "modulate:a", 0.0, 0.25)
	await t2.finished
	line.queue_free()
	_set_selected(_first, false)
	_first = ""


func _rebuild() -> void:
	for c in cards.values():
		c.queue_free()
	cards.clear()
	for s in _strings.get_children():
		s.queue_free()
	_first = ""
	var ids: Array = GameState.evidence
	# 卡片多时增加列数并缩小卡片，保证全部留在板上
	var n := ids.size()
	var cols := clampi(int(ceil(sqrt(n * 1.8))), 4, 6)
	var rows := maxi(1, int(ceil(float(n) / cols)))
	var vp := get_viewport_rect().size
	var cell := CARD_SIZE + Vector2(40, 46)
	var k := minf(1.0, minf((vp.x - 120) / (cols * cell.x), (vp.y - 200) / (rows * cell.y)))
	var origin := Vector2((vp.x - cols * cell.x * k) / 2.0 + 20 * k, 110)
	for i in ids.size():
		var id: String = ids[i]
		var card := _make_card(id)
		var pos := Vector2(i % cols, i / cols)
		var jitter := Vector2(float(hash(id) % 31) - 15, float(hash(id + "y") % 25) - 12) * k
		card.position = origin + pos * cell * k + jitter
		card.scale = Vector2(k, k)
		card.rotation_degrees = float(hash(id + "r") % 7) - 3.0
		add_child(card)
		cards[id] = card
	move_child(_strings, get_child_count() - 1)
	for p in GameState.link_pairs:
		if cards.has(p[0]) and cards.has(p[1]):
			var l := _make_string(p[0], p[1])
			l.width = 4.0
			_strings.add_child(l)


func _make_card(id: String) -> Control:
	var e: Dictionary = ContentDB.evidence.get(id, {})
	var wrap := Control.new()
	wrap.size = CARD_SIZE
	wrap.pivot_offset = Vector2.ZERO
	wrap.mouse_filter = Control.MOUSE_FILTER_STOP
	wrap.mouse_default_cursor_shape = Control.CURSOR_POINTING_HAND
	var card := PanelContainer.new()
	card.custom_minimum_size = CARD_SIZE
	card.size = CARD_SIZE
	card.mouse_filter = Control.MOUSE_FILTER_IGNORE
	wrap.add_child(card)
	var sb := StyleBoxFlat.new()
	# 推论卡（连线得出的结论）用浅蓝色的索引卡，和线索区分开
	sb.bg_color = Color("#dfe7ee") if id.begins_with("ev_inf_") else PAPER
	sb.set_content_margin_all(14)
	sb.shadow_color = Color(0, 0, 0, 0.45)
	sb.shadow_size = 6
	sb.shadow_offset = Vector2(3, 4)
	card.add_theme_stylebox_override("panel", sb)
	var v := VBoxContainer.new()
	v.mouse_filter = Control.MOUSE_FILTER_IGNORE
	card.add_child(v)
	var name_l := Label.new()
	name_l.text = e.get("name", id)
	name_l.autowrap_mode = TextServer.AUTOWRAP_ARBITRARY
	name_l.custom_minimum_size.x = CARD_SIZE.x - 28
	name_l.add_theme_font_size_override("font_size", 20)
	name_l.add_theme_color_override("font_color", INK)
	v.add_child(name_l)
	var note_l := Label.new()
	note_l.text = e.get("note", "").strip_edges()
	note_l.autowrap_mode = TextServer.AUTOWRAP_WORD_SMART
	note_l.add_theme_font_size_override("font_size", 15)
	note_l.add_theme_color_override("font_color", INK.lightened(0.3))
	v.add_child(note_l)
	var pin := Panel.new()
	var psb := StyleBoxFlat.new()
	psb.bg_color = RED
	psb.set_corner_radius_all(7)
	pin.add_theme_stylebox_override("panel", psb)
	pin.size = Vector2(14, 14)
	pin.position = Vector2(CARD_SIZE.x / 2 - 7, -4)
	pin.mouse_filter = Control.MOUSE_FILTER_IGNORE
	wrap.add_child(pin)
	wrap.gui_input.connect(func(ev):
		if ev is InputEventMouseButton and ev.pressed and ev.button_index == MOUSE_BUTTON_LEFT:
			_on_card(id))
	return wrap


func _on_card(id: String) -> void:
	if _first == "":
		_first = id
		_set_selected(id, true)
		hint_label.text = "红线的另一端连到哪里？（再点一次取消）"
	elif _first == id:
		_set_selected(id, false)
		_first = ""
		hint_label.text = "点一张卡片拉起红线，再点另一张。"
	else:
		var a := _first
		_picked.emit([a, id])


func _set_selected(id: String, on: bool) -> void:
	if not cards.has(id):
		return
	var sb: StyleBoxFlat = cards[id].get_child(0).get_theme_stylebox("panel")
	sb.border_color = RED
	sb.set_border_width_all(3 if on else 0)


func _make_string(a: String, b: String) -> Line2D:
	var l := Line2D.new()
	l.default_color = RED
	l.width = 3.0
	var pa: Vector2 = cards[a].position + Vector2(CARD_SIZE.x / 2, 3) * cards[a].scale
	var pb: Vector2 = cards[b].position + Vector2(CARD_SIZE.x / 2, 3) * cards[b].scale
	l.add_point(pa)
	l.add_point((pa + pb) / 2 + Vector2(0, 18))
	l.add_point(pb)
	return l


## 提示：让几张卡片轻轻闪烁（连错三次后，指出该连的两张）
func highlight(ids: Array) -> void:
	for id in ids:
		if not cards.has(id):
			continue
		var card: Control = cards[id]
		var t := create_tween().set_loops(4)
		t.tween_property(card, "modulate", Color(1.35, 1.2, 0.8), 0.35)
		t.tween_property(card, "modulate", Color.WHITE, 0.35)
