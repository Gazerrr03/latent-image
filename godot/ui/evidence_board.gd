extends Control
## 证据板（参考 Ghost in the SQL Data）：软木板上钉着证据卡片，点一张、再点另一张拉红线。
## 连对：红线留在板上；连错：红线抖一下弹回，不惩罚（docs/01 第 4.2 节）。
## 每张卡片都能单独拿起来看（检视）：右键卡片；或在平时按 Tab 打开证据板，左键点卡片（docs/01 第 5 节“记事本”）。

signal _picked(pair: Array)
signal closed

const Card := preload("res://ui/evidence_card.gd")
const CARD_SIZE := Card.SIZE
const RED := Color("#a3201a")
const PAPER := Color("#efe6d2")
const INK := Color("#1f1a14")
const HINT_LINK := "点一张卡片拉起红线，再点另一张。右键：拿起来仔细看。"
const HINT_BROWSE := "点一张卡片，拿起来仔细看。Tab 或 Esc 合上。"

var title_label: Label
var hint_label: Label
var cards := {}
## 浏览模式：不连线，只看（Tab 打开）
var browsing := false
var _first := ""
var _strings: Node2D
var _exam: Control
var _exam_card: Control
var _exam_text: VBoxContainer


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
	_build_examine()
	hide()


## 打开证据板，等玩家依次点两张卡片。返回 [证据a, 证据b]；被打断时返回 []
func pick_pair(title: String) -> Array:
	browsing = false
	open(title)
	hint_label.text = HINT_LINK
	var pair: Array = await _picked
	return pair


## 平时翻看证据板（Tab）：只看不连
func browse() -> void:
	browsing = true
	open("证据板")
	hint_label.text = HINT_BROWSE if not GameState.evidence.is_empty() else "证据板上还什么都没有。"
	await closed


func open(title: String) -> void:
	title_label.text = title
	_exam.hide()
	_rebuild()
	show()


func close() -> void:
	_exam.hide()
	hide()
	browsing = false
	closed.emit()


func cancel() -> void:
	_picked.emit([])
	if browsing:
		close()


## 在 GUI 焦点导航前接收 Tab，卡片有焦点时也能合上。
func _input(event: InputEvent) -> void:
	if not visible:
		return
	var esc: bool = event.is_action_pressed("ui_cancel")
	var tab: bool = event is InputEventKey and event.pressed and not event.echo and event.physical_keycode == KEY_TAB
	if _exam.visible and (esc or tab):
		_exam.hide()
		get_viewport().set_input_as_handled()
	elif browsing and (esc or tab):
		close()
		get_viewport().set_input_as_handled()


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
		var card := Card.new()
		card.setup(id)
		var pos := Vector2(i % cols, i / cols)
		var jitter := Vector2(float(hash(id) % 31) - 15, float(hash(id + "y") % 25) - 12) * k
		card.position = origin + pos * cell * k + jitter
		card.pivot_offset = Vector2.ZERO
		card.set_meta("base_scale", k)
		card.scale = Vector2(k, k)
		card.rotation_degrees = float(hash(id + "r") % 7) - 3.0
		card.focus_mode = Control.FOCUS_ALL
		card.gui_input.connect(func(ev):
			if _exam.visible: return
			if ev.is_action_pressed("ui_accept"):
				card.accept_event()
				if browsing: examine(id)
				else: _on_card(id)
			else: _on_card_input(id, ev))
		add_child(card)
		cards[id] = card
	move_child(_strings, get_child_count() - 1)
	move_child(_exam, get_child_count() - 1)
	for p in GameState.link_pairs:
		if cards.has(p[0]) and cards.has(p[1]):
			var l := _make_string(p[0], p[1])
			l.width = 4.0
			_strings.add_child(l)


func _on_card_input(id: String, ev: InputEvent) -> void:
	if not (ev is InputEventMouseButton and ev.pressed):
		return
	if ev.button_index == MOUSE_BUTTON_RIGHT or (browsing and ev.button_index == MOUSE_BUTTON_LEFT) or (ev.button_index == MOUSE_BUTTON_LEFT and ev.double_click):
		examine(id)
	elif ev.button_index == MOUSE_BUTTON_LEFT:
		_on_card(id)


func _on_card(id: String) -> void:
	if _first == "":
		_first = id
		_set_selected(id, true)
		hint_label.text = "红线的另一端连到哪里？（再点一次取消）"
	elif _first == id:
		_set_selected(id, false)
		_first = ""
		hint_label.text = HINT_LINK
	else:
		var a := _first
		_picked.emit([a, id])


func _set_selected(id: String, on: bool) -> void:
	if cards.has(id):
		cards[id].selected = on


func _make_string(a: String, b: String) -> Line2D:
	var l := Line2D.new()
	l.default_color = RED
	l.width = 3.0
	var pa: Vector2 = cards[a].position + Vector2(CARD_SIZE.x / 2, 4) * cards[a].scale
	var pb: Vector2 = cards[b].position + Vector2(CARD_SIZE.x / 2, 4) * cards[b].scale
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


# ───────────── 检视：把一张卡片拿起来看 ─────────────

func _build_examine() -> void:
	_exam = Control.new()
	_exam.set_anchors_and_offsets_preset(Control.PRESET_FULL_RECT)
	_exam.mouse_filter = Control.MOUSE_FILTER_STOP
	_exam.z_index = 10
	var dim := ColorRect.new()
	dim.set_anchors_and_offsets_preset(Control.PRESET_FULL_RECT)
	dim.color = Color(0.03, 0.02, 0.02, 0.82)
	dim.mouse_filter = Control.MOUSE_FILTER_IGNORE
	_exam.add_child(dim)
	var paper := PanelContainer.new()
	var sb := StyleBoxFlat.new()
	sb.bg_color = PAPER
	sb.set_content_margin_all(30)
	sb.shadow_color = Color(0, 0, 0, 0.55)
	sb.shadow_size = 14
	paper.add_theme_stylebox_override("panel", sb)
	paper.anchor_left = 0.5
	paper.anchor_right = 0.9
	# 纸的高度跟着字走，竖直居中
	paper.anchor_top = 0.5
	paper.anchor_bottom = 0.5
	paper.grow_vertical = Control.GROW_DIRECTION_BOTH
	paper.mouse_filter = Control.MOUSE_FILTER_IGNORE
	_exam.add_child(paper)
	_exam_text = VBoxContainer.new()
	_exam_text.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	_exam_text.add_theme_constant_override("separation", 14)
	paper.add_child(_exam_text)
	var close_hint := Label.new()
	close_hint.text = "点任意处放下"
	close_hint.set_anchors_and_offsets_preset(Control.PRESET_CENTER_BOTTOM)
	close_hint.position.y -= 46
	close_hint.add_theme_color_override("font_color", Color("#b8ab92"))
	close_hint.add_theme_font_size_override("font_size", 16)
	_exam.add_child(close_hint)
	_exam.gui_input.connect(func(ev):
		if ev is InputEventMouseButton and ev.pressed and ev.button_index in [MOUSE_BUTTON_LEFT, MOUSE_BUTTON_RIGHT]:
			_exam.hide())
	add_child(_exam)
	_exam.hide()


## 检视一张证据：左边是放大的卡片本身，右边是这条线索的全文、在哪里找到的、侦探想到的
func examine(id: String) -> void:
	var e: Dictionary = ContentDB.evidence.get(id, {})
	if _exam_card:
		_exam_card.queue_free()
	_exam_card = Card.new()
	_exam_card.setup(id, true)
	var vp := get_viewport_rect().size
	var k := minf(2.1, vp.x * 0.36 / CARD_SIZE.x)
	_exam_card.pivot_offset = Vector2.ZERO
	_exam_card.scale = Vector2(k, k)
	_exam_card.rotation_degrees = -2.0
	_exam_card.position = Vector2(vp.x * 0.27 - CARD_SIZE.x * k / 2, vp.y * 0.5 - CARD_SIZE.y * k / 2)
	_exam.add_child(_exam_card)
	for c in _exam_text.get_children():
		c.queue_free()
	_exam_line(e.get("name", id), 26, INK, Card.font("serif"))
	var where := _found_where(id)
	if where != "":
		_exam_line(where, 15, INK.lightened(0.45), Card.font("serif"))
	_exam_rule()
	var detail: String = e.get("detail", "")
	if detail == "":
		detail = e.get("note", "")
	_exam_line(Director.fill(detail), 19, INK, Card.font("type" if e.get("kind", "") == "文件" else "serif"))
	var source := _derived_from(id)
	if source != "":
		_exam_line(source, 17, Color("#7a1f12"), Card.font("serif"))
	var hint: String = e.get("hint", "")
	if hint != "":
		_exam_rule()
		_exam_line("我想：" + hint, 19, Color("#24304a"), Card.font("hand"))
	_exam.show()


func _exam_line(text: String, size: int, color: Color, f: Font) -> void:
	var l := Label.new()
	l.text = text
	l.autowrap_mode = TextServer.AUTOWRAP_WORD_SMART
	l.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	l.add_theme_font_override("font", f)
	l.add_theme_font_size_override("font_size", size)
	l.add_theme_color_override("font_color", color)
	_exam_text.add_child(l)


func _exam_rule() -> void:
	var r := ColorRect.new()
	r.custom_minimum_size = Vector2(0, 1)
	r.color = Color(0.4, 0.3, 0.2, 0.3)
	_exam_text.add_child(r)


## “第 2 章 · 花园·通风口外侧”：这条证据是在哪一章、哪个房间收进来的
func _found_where(id: String) -> String:
	var shot: String = GameState.found_at.get(id, "")
	if shot == "" or not ContentDB.shots.has(shot):
		return ""
	var node := shot.get_slice("-", 0)
	var chapter := "序章" if node == "C0" else ("第 %s 章" % node.trim_prefix("C"))
	var room: String = ContentDB.shots[shot].get("scene", "")
	var rname: String = ContentDB.scenes.get(room, {}).get("name", "")
	return chapter + ("　·　" + rname if rname != "" else "")


## 推论卡：由哪两条线索推出
func _derived_from(id: String) -> String:
	if not id.begins_with("ev_inf_"):
		return ""
	for i in GameState.links_done.size():
		var g: String = GameState.links_done[i]
		if i >= GameState.link_pairs.size():
			break
		var pairs: Array = ContentDB.links.get(g, [])
		if not pairs.is_empty() and pairs[0].get("result", "") == id:
			var p: Array = GameState.link_pairs[i]
			return "由“%s”与“%s”推出。" % [ContentDB.evidence.get(p[0], {}).get("name", p[0]), ContentDB.evidence.get(p[1], {}).get("name", p[1])]
	return ""
