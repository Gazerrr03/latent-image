extends CanvasLayer
## 影像档案播放器：参考用户提供的伪纪录片 PV（docs/04 第 10 节）。
## 开场动画与“录像带 / 胶片 / 照片”类线索的检视共用它。内容全部来自影像片段表 content/visual/footage.csv。
##
## 四种画面样式：
##   警告卡  黑底，中英双语的告示（片头）
##   档案卡  黑白 4:3 小窗，左上时间码，右下文件名与编号（胶片档案）
##   摄像机  取景器界面：REC、电池、对焦框、AUTO/AWB、日期时间
##   雪花    满屏雪花噪点（转场、信号中断）
## 两种用法：
##   play_clip(片段)  按表格逐行播放图片 / 卡片 / 字幕（可以点击跳到下一行）
##   set_live(样式…)  把取景器界面直接叠在实时 3D 画面上（开场镜头用）
## 渗漏等级越高，取景器上的文字越容易被乱码替换（参考视频后段的崩坏）。

signal _advance

const TABLE := "res://content/visual/footage.csv"
const ART := "res://art/footage/"
const OSD := Color(0.94, 0.94, 0.9)
const REC_RED := Color("#d9302c")
const MODES := ["警告卡", "档案卡", "摄像机", "雪花"]
## 每种样式默认使用的滤镜预设（content/visual/fx.csv）
const MODE_FX := {"警告卡": "档案卡", "档案卡": "档案卡", "摄像机": "录像带线索", "雪花": "录像带线索"}

var fx: CanvasLayer
var clips := {}
var active := false
var mode := ""
var playing := false

var _font := SystemFont.new()
var _img_layer := CanvasLayer.new()
var _image := TextureRect.new()
var _placeholder := Label.new()
var _card := Control.new()
var _card_title := Label.new()
var _card_text := Label.new()
var _card_foot := Label.new()
var _static := ColorRect.new()
var _osd := Control.new()
var _archive := Control.new()
var _bars: Array = []
var _labels := {}
var _subtitle := PanelContainer.new()
var _subtitle_text := Label.new()
var _stream_active := false
var _ts_base := 0
var _ts_has := false
var _t0 := 0.0
var _prev_fx := ""
var _return_mode := ""
var _garble_t := 0.0
var _row_token := 0


func _ready() -> void:
	layer = 8
	_font.font_names = PackedStringArray(["Menlo", "Monaco", "Courier New", "PingFang SC", "Songti SC"])
	_img_layer.layer = 4
	add_child(_img_layer)
	var img_root := _full(Control.new())
	_img_layer.add_child(img_root)
	var black := _full(ColorRect.new())
	black.color = Color.BLACK
	black.name = "black"
	img_root.add_child(black)
	_full(_image)
	_image.expand_mode = TextureRect.EXPAND_IGNORE_SIZE
	_image.stretch_mode = TextureRect.STRETCH_KEEP_ASPECT_COVERED
	img_root.add_child(_image)
	_placeholder.set_anchors_and_offsets_preset(Control.PRESET_CENTER)
	_placeholder.grow_horizontal = Control.GROW_DIRECTION_BOTH
	_placeholder.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER
	_placeholder.add_theme_color_override("font_color", Color(0.55, 0.55, 0.5))
	_placeholder.add_theme_font_override("font", _font)
	img_root.add_child(_placeholder)
	_build_card(img_root)
	_full(_static)
	var sm := ShaderMaterial.new()
	sm.shader = load("res://shaders/static_noise.gdshader")
	_static.material = sm
	img_root.add_child(_static)
	img_root.visible = false
	img_root.name = "img_root"

	var top := _full(Control.new())
	add_child(top)
	_build_archive(top)
	_build_osd(top)
	_build_subtitle(top)
	_set_mode("")


func _full(c: Control) -> Control:
	c.set_anchors_and_offsets_preset(Control.PRESET_FULL_RECT)
	c.mouse_filter = Control.MOUSE_FILTER_IGNORE
	return c


func _osd_label(parent: Control, key: String, text: String, size: int, anchor: Vector2, pos: Vector2, align := HORIZONTAL_ALIGNMENT_LEFT) -> Label:
	var l := Label.new()
	l.text = text
	l.anchor_left = anchor.x
	l.anchor_right = anchor.x
	l.anchor_top = anchor.y
	l.anchor_bottom = anchor.y
	l.position = pos
	l.horizontal_alignment = align
	l.add_theme_font_override("font", _font)
	l.add_theme_font_size_override("font_size", size)
	l.add_theme_color_override("font_color", OSD)
	l.add_theme_color_override("font_shadow_color", Color(0, 0, 0, 0.6))
	l.mouse_filter = Control.MOUSE_FILTER_IGNORE
	parent.add_child(l)
	if key != "":
		_labels[key] = [l, text]
	return l


# ───────────── 搭建界面 ─────────────

func _build_card(root: Control) -> void:
	_full(_card)
	root.add_child(_card)
	var v := VBoxContainer.new()
	v.set_anchors_and_offsets_preset(Control.PRESET_CENTER)
	v.grow_horizontal = Control.GROW_DIRECTION_BOTH
	v.grow_vertical = Control.GROW_DIRECTION_BOTH
	v.custom_minimum_size = Vector2(980, 0)
	v.add_theme_constant_override("separation", 22)
	_card.add_child(v)
	for l in [_card_title, _card_text, _card_foot]:
		l.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER
		l.autowrap_mode = TextServer.AUTOWRAP_WORD_SMART
		l.add_theme_color_override("font_color", Color(0.86, 0.86, 0.82))
		v.add_child(l)
	_card_title.add_theme_font_size_override("font_size", 30)
	_card_text.add_theme_font_size_override("font_size", 17)
	_card_foot.add_theme_font_size_override("font_size", 13)
	_card_foot.add_theme_color_override("font_color", Color(0.6, 0.6, 0.56))


func _build_archive(root: Control) -> void:
	_full(_archive)
	root.add_child(_archive)
	for side in [0, 1]:
		var b := ColorRect.new()
		b.color = Color.BLACK
		b.mouse_filter = Control.MOUSE_FILTER_IGNORE
		_archive.add_child(b)
		_bars.append(b)
	_osd_label(_archive, "a_time", "", 22, Vector2.ZERO, Vector2.ZERO)
	_osd_label(_archive, "a_file", "", 34, Vector2.ZERO, Vector2.ZERO, HORIZONTAL_ALIGNMENT_RIGHT)
	_osd_label(_archive, "a_count", "", 22, Vector2.ZERO, Vector2.ZERO, HORIZONTAL_ALIGNMENT_RIGHT)


func _build_osd(root: Control) -> void:
	_full(_osd)
	root.add_child(_osd)
	var br := Brackets.new()
	_full(br)
	_osd.add_child(br)
	# 左上
	_osd_label(_osd, "rec_dot", "●", 26, Vector2(0.06, 0.17), Vector2(0, -4)).add_theme_color_override("font_color", REC_RED)
	_osd_label(_osd, "rec", "REC", 28, Vector2(0.06, 0.17), Vector2(26, -6)).add_theme_color_override("font_color", REC_RED)
	_osd_label(_osd, "tape", "▭", 20, Vector2(0.06, 0.25), Vector2.ZERO)
	_osd_label(_osd, "afc", "AF-C", 16, Vector2(0.06, 0.32), Vector2.ZERO)
	_osd_label(_osd, "light", "OFF", 16, Vector2(0.06, 0.45), Vector2.ZERO)
	_osd_label(_osd, "nd", "OFF", 16, Vector2(0.06, 0.55), Vector2.ZERO)
	# 上中
	_osd_label(_osd, "enc", "·ENC", 18, Vector2(0.5, 0.17), Vector2(-24, -2))
	# 右上
	_osd_label(_osd, "batt", "96% ▮▮▮▮", 20, Vector2(0.94, 0.17), Vector2(-150, -2))
	_osd_label(_osd, "min", "102MIN", 16, Vector2(0.94, 0.22), Vector2(-90, 0))
	# 右中
	_osd_label(_osd, "auto", "AUTO", 16, Vector2(0.94, 0.42), Vector2(-60, 0))
	_osd_label(_osd, "awb", "AWB", 20, Vector2(0.94, 0.5), Vector2(-56, 0))
	# 左下
	_osd_label(_osd, "sens", "SENS  SHUTTER  IRIS", 16, Vector2(0.06, 0.76), Vector2.ZERO)
	_osd_label(_osd, "autos", "AUTO  AUTO     AUTO", 16, Vector2(0.06, 0.79), Vector2.ZERO)
	# 右下：日期时间
	_osd_label(_osd, "date", "", 22, Vector2(0.94, 0.75), Vector2(-190, 0), HORIZONTAL_ALIGNMENT_RIGHT)
	_osd_label(_osd, "time", "", 22, Vector2(0.94, 0.79), Vector2(-190, 0), HORIZONTAL_ALIGNMENT_RIGHT)


func _build_subtitle(root: Control) -> void:
	_subtitle.anchor_left = 0.5
	_subtitle.anchor_right = 0.5
	_subtitle.anchor_top = 0.8
	_subtitle.anchor_bottom = 0.8
	_subtitle.grow_horizontal = Control.GROW_DIRECTION_BOTH
	_subtitle.mouse_filter = Control.MOUSE_FILTER_IGNORE
	var sb := StyleBoxFlat.new()
	sb.bg_color = Color.TRANSPARENT
	sb.content_margin_left = 14
	sb.content_margin_right = 14
	sb.content_margin_top = 4
	sb.content_margin_bottom = 4
	_subtitle.add_theme_stylebox_override("panel", sb)
	_subtitle_text.add_theme_color_override("font_color", Color.WHITE)
	_subtitle_text.add_theme_font_size_override("font_size", 24)
	_subtitle_text.add_theme_color_override("font_outline_color", Color.BLACK)
	_subtitle_text.add_theme_constant_override("outline_size", 3)
	_subtitle_text.autowrap_mode = TextServer.AUTOWRAP_WORD_SMART
	_subtitle_text.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER
	_subtitle.add_child(_subtitle_text)
	root.add_child(_subtitle)
	_subtitle.visible = false


# ───────────── 对外接口 ─────────────

func reload() -> void:
	clips.clear()
	for row in ContentDB.load_table(TABLE):
		var id: String = row.get("clip", "")
		if not clips.has(id):
			clips[id] = []
		clips[id].append(row)
	for id in clips:
		clips[id].sort_custom(func(a, b): return int(a.get("seq", "0")) < int(b.get("seq", "0")))


## 实时叠加：osd(档案卡,ROYD_REEL_01,001/007,1926/10/04 21:39)；osd() 关闭
func set_live(m: String, file := "", count := "", stamp := "") -> void:
	if m == "":
		_set_mode("")
		_restore_fx()
		return
	_remember_fx()
	_set_mode(m)
	_set_labels(file, count, stamp)
	_apply_fx(MODE_FX.get(m, ""))


## 字幕：等玩家点击后返回
func subtitle(text: String) -> void:
	if Director.autoplay:
		print("  ▍", text.replace("\n", " "))
		return
	_subtitle_text.text = text
	_subtitle.visible = true
	if Settings.text_instant:
		_subtitle_text.visible_characters = -1
	else:
		_stream_active = true
		_subtitle_text.visible_characters = 0
		var n := text.length()
		for k in range(1, n + 1):
			if not _stream_active or not _subtitle.visible:
				break
			_subtitle_text.visible_characters = k
			var ch := text.substr(k - 1, 1)
			if Director.ui:
				Director.ui._play_typewriter_click()
			var delay := 0.034
			if ch in "。！？":
				delay += 0.16
			elif ch in "；，、：":
				delay += 0.08
			elif ch in "——……":
				delay += 0.10
			await get_tree().create_timer(delay).timeout
		_subtitle_text.visible_characters = -1
		_stream_active = false
	await _advance
	_subtitle.visible = false


## 播放一个影像片段（若干行），返回时恢复原来的画面
## handoff 为真时，放完后不撤掉影像层，由接下来的黑场（日记）盖住后调用 finish_handoff()
func play_clip(id: String, handoff := false) -> void:
	if clips.is_empty():
		reload()
	var rows: Array = clips.get(id, [])
	if rows.is_empty():
		push_warning("影像片段表里没有：" + id)
		return
	if Director.autoplay:
		for r in rows:
			if r.get("subtitle", "") != "":
				print("  ▍", r["subtitle"])
		return
	playing = true
	_return_mode = mode
	_remember_fx()
	_img_layer.get_node("img_root").visible = true
	Director.ui.set_hud(false)
	for i in rows.size():
		if not playing:
			break
		await _play_row(rows[i])
		if i < rows.size() - 1:
			await _flash_static(0.22)
	if handoff and playing:
		playing = false
		return
	finish_handoff()


func finish_handoff() -> void:
	_img_layer.get_node("img_root").visible = false
	_subtitle.visible = false
	Director.ui.set_hud(true)
	playing = false
	_set_mode(_return_mode)
	_restore_fx()


func cancel() -> void:
	playing = false
	_stream_active = false
	_subtitle_text.visible_characters = -1
	_subtitle.visible = false
	_advance.emit()


# ───────────── 内部 ─────────────

func _play_row(row: Dictionary) -> void:
	var m: String = row.get("mode", "摄像机")
	_set_mode(m)
	var fxp: String = row.get("fx", "")
	_apply_fx(fxp if fxp != "" else MODE_FX.get(m, ""))
	_set_labels(row.get("file", ""), row.get("count", ""), row.get("stamp", ""))
	_card.visible = m == "警告卡"
	_card_title.text = row.get("title", "")
	_card_text.text = row.get("text", "")
	_card_foot.text = row.get("foot", "")
	if m == "警告卡":
		var red: bool = row.get("title", "") == row.get("title", "").to_upper() and row.get("title", "") != ""
		_card_title.add_theme_color_override("font_color", REC_RED if red else Color(0.9, 0.9, 0.86))
		_card_title.add_theme_font_size_override("font_size", 64 if red else 30)
	_static.visible = m == "雪花"
	_show_image(row.get("image", ""), m)
	var dur: float = float(row.get("duration", "3")) if str(row.get("duration", "")).is_valid_float() else 3.0
	_ken_burns(row, dur)
	var sub: String = row.get("subtitle", "")
	_subtitle_text.text = sub
	_subtitle.visible = sub != ""
	# 停留 duration 秒；玩家点击可以提前跳到下一行（计时器只对本行有效）
	_row_token += 1
	var token := _row_token
	get_tree().create_timer(dur).timeout.connect(func():
		if token == _row_token:
			_advance.emit())
	await _advance


func _show_image(file: String, m: String) -> void:
	_placeholder.text = ""
	_image.texture = null
	if file == "":
		# 没有图片：摄像机 / 档案卡样式下透出实时 3D 画面
		_img_layer.get_node("img_root/black").visible = m in ["警告卡", "雪花"]
		return
	_img_layer.get_node("img_root/black").visible = true
	var tex := _load_texture(ART + file)
	if tex:
		_image.texture = tex
	else:
		_placeholder.text = "（待交付：art/footage/%s）" % file


static func _load_texture(path: String) -> Texture2D:
	if ResourceLoader.exists(path):
		return load(path)
	if FileAccess.file_exists(path):
		var img := Image.load_from_file(ProjectSettings.globalize_path(path))
		if img:
			return ImageTexture.create_from_image(img)
	return null


## 推拉镜头：zoom 从 zoom_from 缓慢变到 zoom_to，同时向 (pan_x, pan_y) 平移（像素）
func _ken_burns(row: Dictionary, dur: float) -> void:
	var z0: float = float(row.get("zoom_from", "1")) if str(row.get("zoom_from", "")).is_valid_float() else 1.0
	var z1: float = float(row.get("zoom_to", "1.08")) if str(row.get("zoom_to", "")).is_valid_float() else 1.08
	var px: float = float(row.get("pan_x", "0")) if str(row.get("pan_x", "")).is_valid_float() else 0.0
	var py: float = float(row.get("pan_y", "0")) if str(row.get("pan_y", "")).is_valid_float() else 0.0
	var vp := _image.get_viewport_rect().size
	_image.pivot_offset = vp / 2
	_image.scale = Vector2(z0, z0)
	_image.position = Vector2.ZERO
	var t := create_tween().set_parallel()
	t.tween_property(_image, "scale", Vector2(z1, z1), dur).set_trans(Tween.TRANS_SINE)
	t.tween_property(_image, "position", Vector2(px, py), dur).set_trans(Tween.TRANS_SINE)


func _flash_static(sec: float) -> void:
	var was := _static.visible
	_static.visible = true
	await get_tree().create_timer(sec).timeout
	_static.visible = was


func _set_mode(m: String) -> void:
	mode = m
	active = m != ""
	_osd.visible = m == "摄像机"
	_archive.visible = m == "档案卡"
	if m == "":
		_subtitle.visible = false
	_t0 = Time.get_ticks_msec() / 1000.0
	_layout_archive()


func _set_labels(file: String, count: String, stamp: String) -> void:
	_labels["a_file"][1] = file
	_labels["a_count"][1] = ("[ %s ]" % count) if count != "" else ""
	_ts_has = false
	var re := RegEx.create_from_string("(\\d+)[/-](\\d+)[/-](\\d+)\\s+(\\d+):(\\d+)(?::(\\d+))?")
	var m := re.search(stamp)
	if m:
		_ts_has = true
		_labels["date"][1] = "%s/%s/%s" % [m.get_string(1), m.get_string(2), m.get_string(3)]
		var s := int(m.get_string(6)) if m.get_string(6) != "" else 0
		_ts_base = int(m.get_string(4)) * 3600 + int(m.get_string(5)) * 60 + s
	else:
		_labels["date"][1] = stamp
	_refresh_labels(true)


## 档案卡：两侧黑边留出 4:3 小窗；左上时间码，右下文件名与编号（每帧按窗口大小重新摆放）
func _layout_archive() -> void:
	if not is_inside_tree():
		return
	var vp := get_viewport().get_visible_rect().size
	var w := vp.y * 4.0 / 3.0
	var side := maxf(0.0, (vp.x - w) / 2.0)
	_bars[0].position = Vector2.ZERO
	_bars[0].size = Vector2(side, vp.y)
	_bars[1].position = Vector2(vp.x - side, 0)
	_bars[1].size = Vector2(side, vp.y)
	_labels["a_time"][0].position = Vector2(side + w * 0.07, vp.y * 0.17)
	for key in ["a_file", "a_count"]:
		var l: Label = _labels[key][0]
		l.size.x = w * 0.8
	_labels["a_file"][0].position = Vector2(side + w * 0.13, vp.y * 0.71)
	_labels["a_count"][0].position = Vector2(side + w * 0.13, vp.y * 0.765)


func _process(dt: float) -> void:
	if not active:
		return
	var vp := get_viewport().get_visible_rect().size
	var width := minf(960, vp.x * 0.76)
	_subtitle.set_anchors_preset(Control.PRESET_TOP_LEFT)
	_subtitle_text.custom_minimum_size.x = width
	_subtitle.size.x = width + 28
	var bar_height: float = Director.ui.bar_bottom.size.y if Director.ui else 0.0
	_subtitle.position = Vector2((vp.x - _subtitle.size.x) / 2, vp.y - (bar_height + _subtitle.size.y) / 2 if bar_height > _subtitle.size.y + 12 else vp.y - _subtitle.size.y - 34)
	if _archive.visible:
		_layout_archive()
	_garble_t += dt
	_refresh_labels(_garble_t > 0.35)
	if _garble_t > 0.35:
		_garble_t = 0.0
	_labels["rec_dot"][0].visible = fmod(Time.get_ticks_msec() / 1000.0, 1.0) < 0.6


## 刷新文字；渗漏等级 L3 起，取景器上的字开始被乱码替换，L4 时大部分被替换
func _refresh_labels(reroll: bool) -> void:
	var elapsed := int(Time.get_ticks_msec() / 1000.0 - _t0)
	if _ts_has:
		var s := _ts_base + elapsed
		_labels["time"][1] = "%02d:%02d:%02d" % [(s / 3600) % 24, (s / 60) % 60, s % 60]
	else:
		_labels["time"][1] = ""
	_labels["a_time"][1] = "%s  %s" % [_labels["date"][1], _labels["time"][1]] if _ts_has else _labels["date"][1]
	var corrupt := 0.0
	if GameState.leak_level >= 4:
		corrupt = 0.6
	elif GameState.leak_level >= 3:
		corrupt = 0.15
	for key in _labels:
		var l: Label = _labels[key][0]
		var base: String = _labels[key][1]
		if key == "rec_dot":
			continue
		if corrupt > 0.0 and reroll and randf() < corrupt:
			l.text = _garble(base)
		elif reroll or corrupt == 0.0:
			l.text = base


static func _garble(s: String) -> String:
	var letters := "ABCDEFGHIJKLMNOPQRSTUVWXYZ"
	var out := ""
	for ch in s:
		if ch >= "A" and ch <= "Z":
			out += letters[randi() % 26]
		elif ch >= "0" and ch <= "9":
			out += str(randi() % 10)
		else:
			out += ch
	return out


func _remember_fx() -> void:
	if fx and _prev_fx == "":
		_prev_fx = fx.get_override() if fx.get_override() != "" else "自动"


func _restore_fx() -> void:
	if fx and _prev_fx != "":
		fx.set_override(_prev_fx)
		_prev_fx = ""


func _apply_fx(name: String) -> void:
	if fx and name != "":
		fx.set_override(name)


func _input(event: InputEvent) -> void:
	Controls.note_event(event)
	if not (_subtitle.visible or playing):
		return
	var click: bool = event is InputEventMouseButton and event.pressed and event.button_index == MOUSE_BUTTON_LEFT
	if click or event.is_action_pressed("ui_accept"):
		get_viewport().set_input_as_handled()
		if _stream_active:
			_stream_active = false
			_subtitle_text.visible_characters = -1
			return
		_advance.emit()


## 取景器四角的框线与中心对焦框
class Brackets extends Control:
	func _draw() -> void:
		var s := size
		var c := Color(0.94, 0.94, 0.9, 0.85)
		var x0 := s.x * 0.04
		var x1 := s.x * 0.96
		var y0 := s.y * 0.14
		var y1 := s.y * 0.86
		var l := 120.0
		var w := 1.5
		for p in [[Vector2(x0, y0), 1, 1], [Vector2(x1, y0), -1, 1], [Vector2(x0, y1), 1, -1], [Vector2(x1, y1), -1, -1]]:
			var o: Vector2 = p[0]
			draw_line(o, o + Vector2(l * p[1], 0), c, w)
			draw_line(o, o + Vector2(0, l * 0.9 * p[2]), c, w)
		var m := s / 2
		var b := 40.0
		for d in [Vector2(-1, -1), Vector2(1, -1), Vector2(-1, 1), Vector2(1, 1)]:
			var o2: Vector2 = m + Vector2(b * d.x, b * 0.8 * d.y)
			draw_line(o2, o2 - Vector2(14 * d.x, 0), c, w)
			draw_line(o2, o2 - Vector2(0, 14 * d.y), c, w)
		draw_circle(m, 1.5, c)
