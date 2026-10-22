extends CanvasLayer
## 界面层：轻量字幕、人物气泡、选项、提示、宽银幕黑边、冲洗底片。
## 之后会逐步换成场景中的实物 UI（纸、打字机、证据板），但 Director 调用的接口保持不变：
## show_text / choose / cancel / toast / set_objective / set_progress / set_cinematic / wait_seconds

signal _resolved(value: int)

const PAPER := Color("#efe6d2")
const INK := Color("#1f1a14")
const EvidenceBoard := preload("res://ui/evidence_board.gd")
const MediaFx := preload("res://ui/media_fx.gd")
const Menus := preload("res://ui/menus.gd")
const H := preload("res://ui/hud_text.gd")
const HudKeys := preload("res://ui/hud_keys.gd")
const ItemInspector := preload("res://ui/item_inspector.gd")
var inspector: CanvasLayer

var font: SystemFont
var _cinematic := false
var _bar_amount := 0.0
var _bars_tween: Tween
var _text_epoch := 0
var bubble: PanelContainer
var bubble_text: RichTextLabel
var bubble_more: Label
var _speaker_node: Node3D
var _speaker_height := 1.75
var _reading_label: RichTextLabel
var _reading_more: Label
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
## 左下角的笔记本、回想两枚图标
var keys: HBoxContainer
var _keys_poll := 0.0
## 眼睑（睡下、醒来）：在 3D 画面之上、所有界面之下
var lids: ColorRect
var _lid_tween: Tween


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

	text_panel = PanelContainer.new()
	text_panel.add_theme_stylebox_override("panel", StyleBoxEmpty.new())
	text_panel.mouse_filter = Control.MOUSE_FILTER_IGNORE
	root.add_child(text_panel)
	var v := VBoxContainer.new()
	text_panel.add_child(v)
	text_label = _subtitle_label(24)
	v.add_child(text_label)
	more_label = _continue_label()
	v.add_child(more_label)
	text_panel.hide()

	bubble = PanelContainer.new()
	bubble.mouse_filter = Control.MOUSE_FILTER_IGNORE
	var speech_style := StyleBoxFlat.new()
	speech_style.bg_color = Color(0.055, 0.05, 0.045, 0.88)
	speech_style.set_corner_radius_all(8)
	speech_style.content_margin_left = 18
	speech_style.content_margin_right = 18
	speech_style.content_margin_top = 12
	speech_style.content_margin_bottom = 10
	bubble.add_theme_stylebox_override("panel", speech_style)
	var speech_box := VBoxContainer.new()
	bubble.add_child(speech_box)
	bubble_text = _subtitle_label(24)
	speech_box.add_child(bubble_text)
	bubble_more = _continue_label()
	speech_box.add_child(bubble_more)
	root.add_child(bubble)
	bubble.hide()

	choice_panel = _paper_panel()
	choice_panel.set_anchors_preset(Control.PRESET_CENTER)
	choice_panel.anchor_left = 0.3
	choice_panel.anchor_right = 0.7
	choice_panel.anchor_top = 0.3
	choice_panel.anchor_bottom = 0.3
	choice_box = VBoxContainer.new()
	choice_box.add_theme_constant_override("separation", 10)
	choice_panel.add_child(choice_box)
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

	keys = HudKeys.new()
	keys.set_anchors_preset(Control.PRESET_BOTTOM_LEFT)
	keys.grow_vertical = Control.GROW_DIRECTION_BEGIN
	keys.offset_left = 26
	keys.offset_bottom = -22
	keys.pressed.connect(_on_key_icon)
	root.add_child(keys)
	keys.hide()
	var lid_layer := CanvasLayer.new()
	lid_layer.layer = 5
	add_child(lid_layer)
	lids = ColorRect.new()
	lids.set_anchors_preset(Control.PRESET_FULL_RECT)
	lids.mouse_filter = Control.MOUSE_FILTER_IGNORE
	var sm := ShaderMaterial.new()
	sm.shader = load("res://shaders/eyelids.gdshader")
	lids.material = sm
	lid_layer.add_child(lids)
	eyelids_set(1.0)

	_build_interlude(root)
	menus = Menus.new()
	menus.font = font
	add_child(menus)
	inspector = ItemInspector.new()
	add_child(inspector)
	GameState.changed.connect(_refresh)
	Director.shot_started.connect(_on_shot)
	Director.inspected.connect(_on_event)
	_refresh()


func _subtitle_label(size: int) -> RichTextLabel:
	var label := RichTextLabel.new()
	label.fit_content = true
	label.scroll_active = false
	label.mouse_filter = Control.MOUSE_FILTER_IGNORE
	label.add_theme_font_size_override("normal_font_size", size)
	label.add_theme_color_override("default_color", Color("#f4efdf"))
	label.add_theme_color_override("font_outline_color", Color(0, 0, 0, 0.85))
	label.add_theme_constant_override("outline_size", 3)
	label.add_theme_constant_override("line_separation", 0)
	return label


func _continue_label() -> Label:
	var label := Label.new()
	label.horizontal_alignment = HORIZONTAL_ALIGNMENT_RIGHT
	label.add_theme_font_size_override("font_size", 12)
	label.add_theme_color_override("font_color", Color("#d1cbbf"))
	label.add_theme_color_override("font_outline_color", Color.BLACK)
	label.add_theme_constant_override("outline_size", 2)
	label.mouse_filter = Control.MOUSE_FILTER_IGNORE
	return label


func _bar(root: Control, _top: bool) -> ColorRect:
	var r := ColorRect.new()
	r.color = Color.BLACK
	r.mouse_filter = Control.MOUSE_FILTER_IGNORE
	root.add_child(r)
	return r


func _layout_subtitles() -> void:
	var vp := get_viewport().get_visible_rect().size
	var bar_height := maxf(0.0, (vp.y - vp.x / 2.39) / 2.0) * _bar_amount
	bar_top.position = Vector2.ZERO
	bar_top.size = Vector2(vp.x, bar_height)
	bar_bottom.position = Vector2(0, vp.y - bar_height)
	bar_bottom.size = Vector2(vp.x, bar_height)
	var width := minf(960.0, vp.x * 0.76)
	text_panel.position.x = (vp.x - width) / 2.0
	text_panel.size.x = width
	text_label.custom_minimum_size.x = width
	# 演出字幕居于下黑边；探索字幕保持底部安全距离。
	text_panel.position.y = vp.y - (bar_height + text_panel.size.y) / 2.0 if _cinematic and bar_height >= text_panel.size.y else vp.y - text_panel.size.y - 34


func _position_speech() -> void:
	if not is_instance_valid(_speaker_node):
		bubble.hide()
		return
	var cam := get_viewport().get_camera_3d()
	if cam == null or not _speaker_node.is_visible_in_tree():
		bubble.hide()
		return
	var head := _speaker_node.global_position + Vector3.UP * _speaker_height
	if cam.is_position_behind(head):
		bubble.hide()
		return
	# 检查到脸前的位置，避免把气泡当作穿墙人物标记。
	var face := head - Vector3.UP * 0.2
	var query := PhysicsRayQueryParameters3D.create(cam.global_position, face, 1 | 4)
	if Director.world.player:
		query.exclude = [Director.world.player.get_rid()]
	var hit := cam.get_world_3d().direct_space_state.intersect_ray(query)
	if not hit.is_empty() and not _speaker_node.is_ancestor_of(hit["collider"]) and hit["position"].distance_to(face) > 0.1:
		bubble.hide()
		return
	var vp := get_viewport().get_visible_rect().size
	var point := cam.unproject_position(head)
	if not Rect2(Vector2.ZERO, vp).has_point(point):
		bubble.hide()
		return
	bubble.show()
	bubble.position = Vector2(clampf(point.x - bubble.size.x / 2, 18, maxf(18, vp.x - bubble.size.x - 18)), maxf(18, point.y - bubble.size.y - 16))


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
func _process(dt: float) -> void:
	_layout_subtitles()
	_position_speech()
	_update_keys(dt)
	hint_key.text = "A / ×" if Controls.gamepad else H.t("key_hint")
	keys.set_gamepad(Controls.gamepad)
	room_label.visible = _hud_on and not _cinematic and not menus.visible and not text_panel.visible and not inspector.active
	day_label.visible = _hud_on and not _cinematic and day_label.text != "" and not (footage and footage.active) \
		and not interlude_layer.visible and not develop_layer.visible and not board.visible and not menus.visible and not inspector.active


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

## 地点线索与便携物品共用入口，物品资源和呈现类型来自内容表。
func inspect_hotspot(id: String) -> void:
	var hotspot: Dictionary = ContentDB.hotspots.get(id, {})
	if Director.autoplay:
		return
	var data := preload("res://ui/inspection_catalog.gd").hotspot(id, Director.world)
	var source: Node3D = Director.world.hotspot_nodes.get(id)
	if not is_instance_valid(source):
		# 摄影机模式的物品列表也进入同一检视器；不把缺失热区伪装成现场特写。
		var camera := get_viewport().get_camera_3d()
		data["from_menu"] = true
		if data.get("asset", "") == "" and data.get("visuals", []).is_empty():
			data["mode"] = "record"
		inspector.open(data, [], camera.global_position - camera.global_basis.z, [objective_label, checklist_box, progress_label, crosshair, hint_box, day_label, room_label, keys])
		await inspector.closed
		return
	data["focus_fov"] = source.get_meta("inspect_fov", 42.0)
	data["detail_light"] = source.get_meta("inspect_light", false)
	data["detail_light_energy"] = source.get_meta("inspect_light_energy", 1.2)
	var focus: Vector3 = source.global_position + source.global_basis * source.get_meta("inspection_focus", Vector3.ZERO)
	inspector.open(data, data["sources"], focus, [objective_label, checklist_box, progress_label, crosshair, hint_box, day_label, room_label, keys])
	await inspector.closed


func inspect_evidence(id: String, where: String, derived: String) -> void:
	if inspector.active:
		return
	var data := preload("res://ui/inspection_catalog.gd").evidence(id, Director.world, where, derived)
	inspector.open(data, [], Vector3.ZERO)
	await inspector.closed


## 用实际字体宽度分页，最多两行，优先在后半段的标点处分段。
func subtitle_pages(text: String, width: float, font_size: int) -> Array[String]:
	var pages: Array[String] = []
	var rest := text.strip_edges()
	while not rest.is_empty():
		var line := 1
		var used := 0.0
		var limit := 0
		var punctuation := 0
		for i in rest.length():
			var ch := rest.substr(i, 1)
			var advance := font.get_string_size(ch, HORIZONTAL_ALIGNMENT_LEFT, -1, font_size).x
			if ch == "\n" or used + advance > width:
				line += 1
				used = 0.0
			if line > 2:
				break
			used += advance if ch != "\n" else 0.0
			limit = i + 1
			if ch in "。！？；，、.!?;":
				punctuation = limit
		limit = maxi(limit, 1)
		if limit < rest.length() and punctuation > limit / 2:
			limit = punctuation
		pages.append(rest.left(limit).strip_edges())
		rest = rest.substr(limit).strip_edges()
	return pages


func show_text(text: String) -> void:
	if footage and footage.active:
		# 档案字幕仍由原播放器处理输入与媒介层。
		for page in subtitle_pages(text, minf(960, get_viewport().get_visible_rect().size.x * 0.76), 24):
			var epoch := _text_epoch
			await footage.subtitle(page)
			if epoch != _text_epoch:
				break
		return
	await _read_subtitle(text, false)


func show_speech(speaker: String, text: String) -> void:
	_speaker_node = null
	var room_id: String = Director.conversation.get_slice("@", 1)
	for c in Director.world._chr_nodes:
		if c["room"] == room_id and (String(c["who"]) == speaker or String(c["who"]).begins_with(speaker)):
			_speaker_node = c["node"]
			break
	if not is_instance_valid(_speaker_node):
		await show_text(speaker + "：" + text)
		return
	_speaker_height = 1.75
	for c in ContentDB.characters:
		if String(c["name"]).begins_with(speaker):
			_speaker_height = float(c.get("height", "1.75"))
			break
	await _read_subtitle(text, true)
	_speaker_node = null
	bubble.hide()


func _read_subtitle(text: String, speech: bool) -> void:
	if Director.autoplay:
		print("  │ ", text)
		return
	var epoch := _text_epoch
	var in_conversation: bool = Director.conversation != ""
	if not in_conversation:
		_release_mouse()
	_reading_label = bubble_text if speech else text_label
	_reading_more = bubble_more if speech else more_label
	var panel: PanelContainer = bubble if speech else text_panel
	var width := minf(480, get_viewport().get_visible_rect().size.x * 0.6) if speech else minf(960, get_viewport().get_visible_rect().size.x * 0.76)
	_reading_label.custom_minimum_size.x = width
	panel.size = Vector2.ZERO
	var pages := subtitle_pages(text, width - 12, 24)
	for i in pages.size():
		_reading_label.text = pages[i]
		_reading_label.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER
		_reading_label.visible_ratio = 0.0
		_reading_more.text = ("A / ×" if Controls.gamepad else "空格 / 点击") + " 继续" + ("  %d/%d" % [i + 1, pages.size()] if pages.size() > 1 else "")
		_reading_more.modulate.a = 0.0
		panel.show()
		if Settings.text_instant:
			_reading_label.visible_ratio = 1.0
			_reading_more.modulate.a = 1.0
			_typing = null
		else:
			_typing = create_tween()
			_typing.tween_property(_reading_label, "visible_ratio", 1.0, clampf(pages[i].length() * 0.03, 0.3, 2.5))
			_typing.tween_property(_reading_more, "modulate:a", 1.0, 0.2)
		_waiting = true
		var result: int = await _resolved
		_waiting = false
		if _typing:
			_typing.kill()
		if result < 0 or epoch != _text_epoch:
			break
	panel.hide()
	if not in_conversation:
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
	if options.size() > 0:
		choice_box.get_child(1).grab_focus()
	var k: int = await _resolved
	choice_panel.hide()
	_restore_mouse()
	return k


func cancel() -> void:
	_text_epoch += 1
	_speaker_node = null
	bubble.hide()
	if inspector.active:
		inspector.close(true)
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
		eyelids_set(1.0)
		return
	interlude_layer.modulate.a = 0.0
	interlude_layer.show()
	var t := create_tween()
	t.tween_property(interlude_layer, "modulate:a", 1.0, 1.4)
	await t.finished
	await wait_seconds(0.5)
	eyelids_set(1.0)


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
	eyelids_set(1.0)
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
		l.text = String(it["text"]) if it.get("head", false) else ("✓  " if it["done"] else "·  ") + String(it["text"])
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
	hint_box.visible = _hud_on and not _cinematic and Director.conversation == ""


## 播放影像档案、冲洗底片时隐藏目标、提示等界面
func set_hud(on: bool) -> void:
	_hud_on = on
	for n in [objective_label, progress_label, checklist_box, toast_label, crosshair, room_label]:
		n.visible = on and not _cinematic
	hint_box.visible = on and not _cinematic and hint_label.text != ""
	if on:
		_refresh()


func set_cinematic(on: bool) -> void:
	if fx:
		fx.set_exploring(not on)
	for n in [objective_label, progress_label, checklist_box, toast_label, crosshair]:
		n.visible = _hud_on and not on
	crosshair.visible = _hud_on and not on and Director.conversation == ""
	hint_box.visible = _hud_on and not on and hint_label.text != ""
	if _cinematic == on:
		return
	_cinematic = on
	if _bars_tween:
		_bars_tween.kill()
	_bars_tween = create_tween().set_trans(Tween.TRANS_SINE).set_ease(Tween.EASE_IN_OUT)
	_bars_tween.tween_property(self, "_bar_amount", 1.0 if on else 0.0, 0.6)


# ───────────── 输入 ─────────────

## Tab：随时翻开证据板，一张一张拿起来看；Esc：自由行走时打开暂停页。
## 问话、选项、读字、黑场、冲洗、影像档案、证据板上都不响应
func _unhandled_input(event: InputEvent) -> void:
	if Director.world and is_instance_valid(Director.world.player.interaction_owner):
		# 图纸/读字期间由关卡或阅读器处理；Q 留给图纸，Tab 仍可翻现有证据板。
		if Director.world.player.frozen or event.is_action_pressed("recall"):
			return
	if not event.is_pressed() or event.is_echo():
		return
	var tab: bool = event.is_action_pressed("notebook")
	var esc: bool = event.is_action_pressed("pause") or event.is_action_pressed("ui_cancel")
	if event.is_action_pressed("recall") and not _busy():
		var pl: Node = Director.world.player if Director.world else null
		if pl and pl.active and not pl.frozen:
			get_viewport().set_input_as_handled()
			recall()
		return
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
	return Director.conversation != "" or inspector.active or board.visible or _waiting or choice_panel.visible or develop_layer.visible or interlude_layer.visible \
		or Director.autoplay or menus.visible or (footage and footage.active)


## 翻开证据板浏览（Tab，或暂停页的“证据板”）；合上以后回到原来的样子
func browse_board(restore_mouse := true) -> void:
	keys.ping("notebook")
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
	Controls.note_event(event)
	if not _waiting:
		return
	if event.is_echo():
		return
	var click: bool = event is InputEventMouseButton and event.pressed and event.button_index == MOUSE_BUTTON_LEFT
	var key: bool = event.is_action_pressed("ui_accept")
	if not (click or key):
		return
	get_viewport().set_input_as_handled()
	if _typing and _typing.is_running():
		_typing.kill()
		_reading_label.visible_ratio = 1.0
		_reading_more.modulate.a = 1.0
		return
	_resolved.emit(0)


func _release_mouse() -> void:
	_prev_mouse = Input.mouse_mode
	Input.mouse_mode = Input.MOUSE_MODE_VISIBLE


func _restore_mouse() -> void:
	Input.mouse_mode = _prev_mouse


# ───────────── 笔记本、回想、眼睑（docs/01 第 4 节，10-20） ─────────────

## 图标只在自由行走时出现；回想没有可指的路（客房收尾、不在探索）时变灰。目标每半秒问一次
func _update_keys(dt: float) -> void:
	var pl: Node = Director.world.player if Director.world else null
	var show: bool = _hud_on and not _cinematic and Director.conversation == "" and pl != null and pl.active and not pl.frozen and not text_panel.visible and not menus.visible and not board.visible \
		and not interlude_layer.visible and not (footage and footage.active) and not Director.autoplay
	keys.visible = show
	if not show:
		return
	_keys_poll -= dt
	if _keys_poll <= 0.0:
		_keys_poll = 0.5
		keys.set_dim("guide", Director.guide_targets().is_empty())


func _on_key_icon(which: String) -> void:
	if _busy():
		return
	if which == "notebook":
		browse_board()
	elif is_instance_valid(Director.world.player.interaction_owner):
		Director.world.player.interaction_owner._open_blueprint()
	else:
		recall()


## Q：回想。地面上浮现通往下一条还没拿到的线索（收齐后是客房）的一段路
func recall() -> void:
	keys.ping("guide")
	if Director.world.room_locked() != "":
		toast("今天就到这里。")
		return
	var targets: Array = Director.guide_targets()
	if targets.is_empty():
		toast("现在没有要去的地方。")
		return
	var ok: bool = await Director.world.show_guide(targets)
	if not ok:
		toast("想不起来该往哪里走。")


func notebook_ping() -> void:
	if keys:
		keys.ping("notebook")


func eyelids_set(v: float) -> void:
	if _lid_tween:
		_lid_tween.kill()
	(lids.material as ShaderMaterial).set_shader_parameter("open", v)
	lids.visible = v < 0.999


func _lid_value() -> float:
	return float((lids.material as ShaderMaterial).get_shader_parameter("open"))


## 眼睑慢慢合到 v（0 = 全闭）
func eyelids_to(v: float, sec: float) -> void:
	if Director.autoplay:
		return
	if _lid_tween:
		_lid_tween.kill()
	lids.visible = true
	_lid_tween = create_tween().set_trans(Tween.TRANS_SINE).set_ease(Tween.EASE_IN_OUT)
	_lid_tween.tween_method(func(x): (lids.material as ShaderMaterial).set_shader_parameter("open", x), _lid_value(), v, sec)
	await _lid_tween.finished
	lids.visible = v < 0.999


## 合眼：沉下去、挣一下、再沉下去。闭眼完成后接黑屏并移除眼睑特效
func eyelids_close() -> void:
	await eyelids_to(0.12, 1.0)
	await eyelids_to(0.32, 0.5)
	await eyelids_to(0.0, 1.4)
	await wait_seconds(0.6)
	interlude_layer.color = Color.BLACK
	interlude_layer.modulate.a = 1.0
	interlude_layer.show()
	eyelids_set(1.0)


## 睁眼：先睁开一条缝，眨一下，再睁开
func eyelids_open() -> void:
	eyelids_set(0.0)
	await wait_seconds(0.5)
	await eyelids_to(0.35, 0.9)
	await eyelids_to(0.12, 0.25)
	await eyelids_to(0.7, 0.7)
	await eyelids_to(1.0, 0.6)
