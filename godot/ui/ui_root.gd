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
const Menus := preload("res://ui/menus.gd")
const H := preload("res://ui/hud_text.gd")

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
## 准星下面的提示：“［E］检查 · 药柜”
var hint_box: HBoxContainer
var hint_key: Label
## 自由行走时走进新房间，屏幕下方淡入淡出房间名
var room_label: Label
var _room_tween: Tween
var _room_last := ""
var _room_last_t := -100.0
## 右下角常驻的日期角标：“十月十八日 星期一 · 第二章 · 离开庭还有五天”
var day_label: Label
var _hud_on := true
## 标题页、暂停页、设置、操作说明
var menus: CanvasLayer
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
var _lift: Tween
var diary_page: PanelContainer
var diary_date: Label
var diary_weather: Label
var diary_title: Label
var diary_notes: VBoxContainer


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
	_build_hint(root)
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

	room_label = _label(root, Control.PRESET_CENTER_BOTTOM, 30)
	room_label.offset_top = -190
	room_label.offset_bottom = -150
	room_label.add_theme_constant_override("shadow_offset_x", 2)
	room_label.add_theme_constant_override("shadow_offset_y", 2)
	room_label.modulate.a = 0.0
	day_label = _label(root, Control.PRESET_BOTTOM_RIGHT, 16)
	day_label.grow_horizontal = Control.GROW_DIRECTION_BEGIN
	day_label.grow_vertical = Control.GROW_DIRECTION_BEGIN
	day_label.horizontal_alignment = HORIZONTAL_ALIGNMENT_RIGHT
	day_label.offset_right = -28
	day_label.offset_bottom = -22
	day_label.add_theme_color_override("font_color", Color("#cfc3a6"))
	day_label.add_theme_constant_override("shadow_offset_x", 1)
	day_label.add_theme_constant_override("shadow_offset_y", 1)

	_build_interlude(root)
	menus = Menus.new()
	menus.font = font
	add_child(menus)
	GameState.changed.connect(_refresh)
	Director.shot_started.connect(_on_shot)
	Director.inspected.connect(_on_event)
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
	day_label.text = H.day_line(GameState.shot)


## 准星提示：按键印成一枚小小的打字机键帽，后面是“动作 · 对象”
func _build_hint(root: Control) -> void:
	hint_box = HBoxContainer.new()
	hint_box.set_anchors_preset(Control.PRESET_CENTER)
	hint_box.grow_horizontal = Control.GROW_DIRECTION_BOTH
	hint_box.offset_top = 34
	hint_box.alignment = BoxContainer.ALIGNMENT_CENTER
	hint_box.add_theme_constant_override("separation", 10)
	hint_box.mouse_filter = Control.MOUSE_FILTER_IGNORE
	root.add_child(hint_box)
	hint_key = Label.new()
	hint_key.text = H.t("key_hint")
	hint_key.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER
	hint_key.custom_minimum_size = Vector2(26, 26)
	hint_key.add_theme_font_size_override("font_size", 15)
	hint_key.add_theme_color_override("font_color", INK)
	var cap := StyleBoxFlat.new()
	cap.bg_color = Color("#e8dcc0")
	cap.set_corner_radius_all(13)
	cap.set_border_width_all(2)
	cap.border_color = Color("#3a3128")
	cap.content_margin_left = 4
	cap.content_margin_right = 4
	hint_key.add_theme_stylebox_override("normal", cap)
	hint_box.add_child(hint_key)
	hint_label = Label.new()
	hint_label.add_theme_font_size_override("font_size", 18)
	hint_label.add_theme_color_override("font_color", Color("#e8dcc0"))
	hint_label.add_theme_color_override("font_shadow_color", Color.BLACK)
	hint_label.add_theme_constant_override("shadow_offset_x", 1)
	hint_label.add_theme_constant_override("shadow_offset_y", 1)
	hint_box.add_child(hint_label)
	hint_box.hide()


func _on_shot(_row: Dictionary) -> void:
	_refresh()
	# 进入一个镜头（交谈、走进房间触发的镜头），房间名立刻收起，别和文字框叠在一起
	if _room_tween:
		_room_tween.kill()
	room_label.modulate.a = 0.0


## 自由行走时走进一个房间（scene_host 发出 enter:<房间>）：屏幕下方淡入淡出房间名
func _on_event(id: String) -> void:
	if not id.begins_with("enter:") or Director.autoplay:
		return
	var rid := id.trim_prefix("enter:")
	var now := Time.get_ticks_msec() / 1000.0
	# 在门口来回跨的时候不要一遍遍出现
	if rid == _room_last and now - _room_last_t < 6.0:
		_room_last_t = now
		return
	_room_last = rid
	_room_last_t = now
	var n := H.room_name(rid)
	if n == "":
		return
	room_label.text = n
	if _room_tween:
		_room_tween.kill()
	_room_tween = create_tween()
	_room_tween.tween_property(room_label, "modulate:a", 1.0, 0.9).set_trans(Tween.TRANS_SINE)
	_room_tween.tween_interval(2.2)
	_room_tween.tween_property(room_label, "modulate:a", 0.0, 1.4).set_trans(Tween.TRANS_SINE)


## 日期角标在影像档案、黑场、冲洗、证据板、菜单上面不出现；房间名在菜单上面不出现
func _process(_dt: float) -> void:
	room_label.visible = _hud_on and not menus.visible
	day_label.visible = _hud_on and day_label.text != "" and not (footage and footage.active) \
		and not interlude_layer.visible and not develop_layer.visible and not board.visible and not menus.visible


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


## 章节之间的黑场：盖在所有界面之上。前半段是梦（上一章的复盘），后半段是日记本的一页（新一章的开头）
const DREAM_BG := Color("#05060a")
const DREAM_INK := Color("#b9bccb")

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
	interlude_box.add_theme_constant_override("separation", 20)
	center.add_child(interlude_box)

	# 日记本的一页：左上日期，右上天气，中间标题，下面一两行小字
	var dc := CenterContainer.new()
	dc.set_anchors_preset(Control.PRESET_FULL_RECT)
	dc.mouse_filter = Control.MOUSE_FILTER_IGNORE
	interlude_layer.add_child(dc)
	diary_page = _paper_panel()
	diary_page.custom_minimum_size = Vector2(640, 400)
	(diary_page.get_theme_stylebox("panel") as StyleBoxFlat).set_content_margin_all(44)
	dc.add_child(diary_page)
	var v := VBoxContainer.new()
	v.add_theme_constant_override("separation", 0)
	diary_page.add_child(v)
	var head := HBoxContainer.new()
	v.add_child(head)
	diary_date = _diary_label(20, HORIZONTAL_ALIGNMENT_LEFT)
	diary_date.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	head.add_child(diary_date)
	diary_weather = _diary_label(20, HORIZONTAL_ALIGNMENT_RIGHT)
	head.add_child(diary_weather)
	var rule := ColorRect.new()
	rule.color = Color(INK, 0.35)
	rule.custom_minimum_size.y = 1
	v.add_child(rule)
	var gap := Control.new()
	gap.size_flags_vertical = Control.SIZE_EXPAND_FILL
	v.add_child(gap)
	diary_title = _diary_label(36, HORIZONTAL_ALIGNMENT_CENTER)
	diary_title.autowrap_mode = TextServer.AUTOWRAP_WORD_SMART
	v.add_child(diary_title)
	var gap2 := Control.new()
	gap2.size_flags_vertical = Control.SIZE_EXPAND_FILL
	v.add_child(gap2)
	diary_notes = VBoxContainer.new()
	diary_notes.add_theme_constant_override("separation", 8)
	v.add_child(diary_notes)
	diary_page.hide()

	interlude_more = Label.new()
	interlude_more.text = "▸"
	interlude_more.set_anchors_preset(Control.PRESET_BOTTOM_RIGHT)
	interlude_more.position = Vector2(-90, -80)
	interlude_more.add_theme_color_override("font_color", Color("#8a8070"))
	interlude_layer.add_child(interlude_more)
	interlude_layer.hide()


func _diary_label(size: int, align: int) -> Label:
	var l := Label.new()
	l.horizontal_alignment = align
	l.add_theme_font_size_override("font_size", size)
	l.add_theme_color_override("font_color", INK)
	return l


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
	if Settings.text_instant:
		# 设置：文字直接显示
		text_label.visible_ratio = 1.0
		more_label.modulate.a = 1.0
		_typing = null
	else:
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
	interlude_layer.color = Color.BLACK
	interlude_box.modulate.a = 1.0
	diary_page.hide()
	if footage:
		footage.cancel()


# ───────────── 实物 UI ─────────────

func board_pick_pair(title: String) -> Array:
	_release_mouse()
	objective_label.visible = false
	var pair: Array = await board.pick_pair(title)
	return pair


func board_result(a: String, b: String, ok: bool) -> void:
	Director.world.play_sound("ui_link_ok" if ok else "ui_link_wrong")
	await board.show_result(a, b, ok)


func board_open(title: String) -> void:
	_release_mouse()
	Director.world.play_sound("ui_board_open")
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


## 进入黑场：已经是黑的（梦接着日记）就停下正在退去的黑场，不再重新变暗
func _interlude_enter() -> void:
	_release_mouse()
	set_hud(false)
	if _lift and _lift.is_valid():
		_lift.kill()
	interlude_more.modulate.a = 0.0
	if interlude_layer.visible and interlude_layer.modulate.a > 0.5:
		interlude_layer.modulate.a = 1.0
		return
	interlude_layer.modulate.a = 0.0
	interlude_layer.show()
	var t := create_tween()
	t.tween_property(interlude_layer, "modulate:a", 1.0, 1.4)
	await t.finished
	await wait_seconds(0.5)


## 等玩家点击，再让当前这一段淡去
func _interlude_hold(part: CanvasItem) -> void:
	create_tween().tween_property(interlude_more, "modulate:a", 1.0, 0.4)
	_typing = null
	_waiting = true
	await _resolved
	_waiting = false
	interlude_more.modulate.a = 0.0
	var out := create_tween()
	out.tween_property(part, "modulate:a", 0.0, 0.8)
	await out.finished


## 离开黑场：黑场在下一镜开始以后才退去，画面从黑里慢慢亮起来。
## 紧接着还有下一段（梦之后的日记）时，_interlude_enter 会停下这次退去。
func _interlude_exit() -> void:
	set_hud(true)
	_restore_mouse()
	_lift = create_tween()
	_lift.tween_interval(0.4)
	_lift.tween_property(interlude_layer, "modulate:a", 0.0, 2.0)
	_lift.tween_callback(func():
		interlude_layer.hide()
		interlude_layer.color = Color.BLACK
		interlude_box.modulate.a = 1.0
		diary_page.hide())


## 梦：一章结束、睡下以后，上一章的事在梦里过一遍（复盘）。
## clip 不为空时先放这段影像片段（独立的梦境动画），再浮出字幕；lines：[{text}]
## 字幕一行一行从下面浮上来，新的一行出现时，前面的几行慢慢暗下去，像梦里记不住的东西。
func dream(lines: Array, clip := "") -> void:
	if Director.autoplay:
		if clip != "":
			print("  ☾ （梦境片段：%s）" % clip)
		for l in lines:
			print("  ☾ ", String(l["text"]).replace("\n", "\n  ☾ "))
		return
	await _interlude_enter()
	if clip != "":
		# 影像片段画在黑场下面一层，放的时候把黑场让开
		interlude_layer.hide()
		await footage.play_clip(clip)
		interlude_layer.show()
		interlude_layer.modulate.a = 1.0
	if lines.is_empty():
		_interlude_exit()
		return
	interlude_layer.color = DREAM_BG
	diary_page.hide()
	for c in interlude_box.get_children():
		c.queue_free()
	interlude_box.modulate.a = 1.0
	interlude_box.show()
	var shown: Array = []
	for l in lines:
		var lb := Label.new()
		lb.text = l["text"]
		lb.autowrap_mode = TextServer.AUTOWRAP_WORD_SMART
		lb.custom_minimum_size.x = 760
		lb.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER
		lb.add_theme_font_size_override("font_size", 23)
		lb.add_theme_color_override("font_color", DREAM_INK)
		lb.modulate.a = 0.0
		interlude_box.add_child(lb)
		await get_tree().process_frame
		var y := lb.position.y
		lb.position.y = y + 14
		var f := create_tween().set_parallel()
		f.tween_property(lb, "modulate:a", 1.0, 1.6).set_trans(Tween.TRANS_SINE)
		f.tween_property(lb, "position:y", y, 2.2).set_trans(Tween.TRANS_SINE).set_ease(Tween.EASE_OUT)
		for i in shown.size():
			var dim := maxf(0.22, 0.75 - 0.18 * (shown.size() - 1 - i))
			f.tween_property(shown[i], "modulate:a", dim, 1.6)
		shown.append(lb)
		await f.finished
		if not interlude_layer.visible:
			return
		await wait_seconds(0.9)
	# 最后一行（睡前相信的那件事）停住；前面的都暗下去
	await _interlude_hold(interlude_box)
	interlude_layer.color = Color.BLACK
	_interlude_exit()


## 日记：新一章开头，在日记本上写下这一天：日期、天气、标题，下面一两行小字。
## page：{date, weather, title, notes:[文字]}；字一笔一笔写出来（按字数显露）
## on_covered：黑场完全盖住画面之后调用（用来撤掉被盖住的东西）
func diary(page: Dictionary, on_covered := Callable()) -> void:
	if Director.autoplay:
		print("  ✎ %s　%s　《%s》" % [page.get("date", ""), page.get("weather", ""), page.get("title", "")])
		for n in page.get("notes", []):
			print("  ✎ ", n)
		return
	await _interlude_enter()
	if on_covered.is_valid():
		on_covered.call()
	interlude_layer.color = Color.BLACK
	interlude_box.hide()
	diary_date.text = page.get("date", "")
	diary_weather.text = page.get("weather", "")
	diary_title.text = page.get("title", "")
	for c in diary_notes.get_children():
		c.queue_free()
	var notes: Array = []
	for n in page.get("notes", []):
		var nl := _diary_label(20, HORIZONTAL_ALIGNMENT_LEFT)
		nl.text = n
		diary_notes.add_child(nl)
		notes.append(nl)
	var order: Array = [diary_date, diary_weather, diary_title]
	order.append_array(notes)
	for l in order:
		l.visible_ratio = 0.0
	diary_page.modulate.a = 0.0
	diary_page.show()
	var t := create_tween()
	t.tween_property(diary_page, "modulate:a", 1.0, 0.9)
	await t.finished
	for l in order:
		var n: int = (l as Label).text.length()
		if n == 0:
			continue
		var w := create_tween()
		w.tween_property(l, "visible_ratio", 1.0, clampf(n * (0.16 if l == diary_title else 0.07), 0.4, 2.4))
		await w.finished
		if not interlude_layer.visible:
			return
		await wait_seconds(0.9 if l == diary_title else 0.35)
	await _interlude_hold(diary_page)
	diary_page.hide()
	diary_page.modulate.a = 1.0
	_interlude_exit()


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


## 准星提示。玩家脚本传来“E　检查：药柜”“E　开门”，统一成键帽 + “检查 · 药柜”；空字符串收起
func set_hint(text: String) -> void:
	if text.strip_edges() == "":
		hint_label.text = ""
		hint_box.hide()
		return
	var p := H.hint_parts(text)
	hint_label.text = p[0] if p[1] == "" else "%s · %s" % p
	hint_box.visible = _hud_on


## 播放影像档案、冲洗底片时隐藏目标、提示等界面
func set_hud(on: bool) -> void:
	_hud_on = on
	for n in [objective_label, progress_label, checklist_box, toast_label, crosshair, room_label]:
		n.visible = on
	hint_box.visible = on and hint_label.text != ""
	if on:
		_refresh()


func set_cinematic(on: bool) -> void:
	if fx:
		fx.set_exploring(not on)
	crosshair.visible = not on
	var t := create_tween().set_parallel()
	t.tween_property(bar_top, "modulate:a", 1.0 if on else 0.0, 0.6)
	t.tween_property(bar_bottom, "modulate:a", 1.0 if on else 0.0, 0.6)


# ───────────── 输入 ─────────────

## Tab：随时翻开证据板，一张一张拿起来看；Esc：自由行走时打开暂停页。
## 问话、选项、读字、黑场、冲洗、影像档案、证据板上都不响应
func _unhandled_input(event: InputEvent) -> void:
	if not (event is InputEventKey and event.pressed and not event.echo):
		return
	var tab: bool = event.physical_keycode == KEY_TAB
	var esc: bool = event.is_action_pressed("ui_cancel")
	if not (tab or esc) or _busy():
		return
	if esc:
		var pl: Node = Director.world.player if Director.world else null
		if pl and pl.active and not pl.frozen:
			get_viewport().set_input_as_handled()
			menus.open_pause()
		return
	get_viewport().set_input_as_handled()
	browse_board()


func _busy() -> bool:
	return board.visible or _waiting or choice_panel.visible or develop_layer.visible or interlude_layer.visible \
		or Director.autoplay or menus.visible or (footage and footage.active)


## 翻开证据板浏览（Tab，或暂停页的“证据板”）；合上以后回到原来的样子
func browse_board(restore_mouse := true) -> void:
	_release_mouse()
	objective_label.visible = false
	Director.world.set_frozen(true)
	Director.world.play_sound("ui_board_open")
	await board.browse()
	objective_label.visible = true
	if restore_mouse:
		Director.world.set_frozen(false)
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
