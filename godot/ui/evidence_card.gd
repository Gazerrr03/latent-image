extends Control
## 证据板上的一张卡片。证据表的 kind 列决定它长什么样：
##   文件：带横线的旧纸，打字机字；照片：白边相片，胶带贴着；证词：索引卡，手写；
##   物件 / 痕迹：牛皮纸证物签，穿着线；推论：浅蓝色索引卡。
## 证据表的 image 列给了图片（res://art/evidence/ 下）就画在照片框里，没给时画一块暗房里冲出来的灰影。
## 同一个脚本也用在检视画面里的大卡片（big = true）。

const SIZE := Vector2(230, 150)
const RED := Color("#a3201a")
const INK := Color("#1f1a14")

static var _fonts := {}

var id := ""
var kind := ""
var selected := false:
	set(v):
		selected = v
		queue_redraw()
var big := false
var _image: Texture2D
var _lift := 0.0:
	set(v):
		_lift = v
		queue_redraw()


static func font(style: String) -> Font:
	if _fonts.has(style):
		return _fonts[style]
	var f := SystemFont.new()
	match style:
		"type":
			f.font_names = PackedStringArray(["American Typewriter", "Courier New", "Courier", "Songti SC", "STSong"])
		"hand":
			f.font_names = PackedStringArray(["Kaiti SC", "STKaiti", "KaiTi", "Songti SC"])
		_:
			f.font_names = PackedStringArray(["Songti SC", "STSong", "Noto Serif CJK SC", "Source Han Serif SC", "SimSun"])
	_fonts[style] = f
	return f


func setup(evidence_id: String, as_big := false) -> void:
	id = evidence_id
	big = as_big
	var e: Dictionary = ContentDB.evidence.get(id, {})
	kind = e.get("kind", "")
	if kind == "":
		kind = "推论" if id.begins_with("ev_inf_") else "文件"
	var img: String = e.get("image", "")
	if img != "" and ResourceLoader.exists("res://art/evidence/" + img):
		_image = load("res://art/evidence/" + img)
	size = SIZE
	custom_minimum_size = SIZE
	pivot_offset = SIZE / 2
	mouse_filter = Control.MOUSE_FILTER_IGNORE if big else Control.MOUSE_FILTER_STOP
	mouse_default_cursor_shape = Control.CURSOR_POINTING_HAND
	_build_text(e)
	if not big:
		mouse_entered.connect(func(): _hover(true))
		mouse_exited.connect(func(): _hover(false))


func _hover(on: bool) -> void:
	var t := create_tween()
	t.tween_property(self, "_lift", 1.0 if on else 0.0, 0.12)
	t.parallel().tween_property(self, "scale", Vector2.ONE * (1.06 if on else 1.0) * _base_scale(), 0.12)


func _base_scale() -> float:
	return float(get_meta("base_scale", 1.0))


func _build_text(e: Dictionary) -> void:
	var name_text: String = e.get("name", id)
	var note: String = Director.fill(String(e.get("note", "")).strip_edges())
	var box := VBoxContainer.new()
	box.mouse_filter = Control.MOUSE_FILTER_IGNORE
	box.add_theme_constant_override("separation", 4)
	add_child(box)
	var title := Label.new()
	var body := Label.new()
	for l in [title, body]:
		l.mouse_filter = Control.MOUSE_FILTER_IGNORE
		l.autowrap_mode = TextServer.AUTOWRAP_ARBITRARY
		l.add_theme_color_override("font_color", INK)
		box.add_child(l)
	title.text = name_text
	body.text = note
	body.add_theme_color_override("font_color", INK.lightened(0.28))
	match kind:
		"照片":
			# 照片：上面是相片，下面白边上手写一行字
			box.position = Vector2(14, SIZE.y - 42)
			box.size = Vector2(SIZE.x - 28, 36)
			title.add_theme_font_override("font", font("hand"))
			title.add_theme_font_size_override("font_size", 17)
			title.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER
			body.visible = false
		"证词":
			box.position = Vector2(14, 12)
			box.size = Vector2(SIZE.x - 28, SIZE.y - 20)
			title.add_theme_font_override("font", font("serif"))
			title.add_theme_font_size_override("font_size", 17)
			body.add_theme_font_override("font", font("hand"))
			body.add_theme_font_size_override("font_size", 17)
			body.text = note
			body.add_theme_color_override("font_color", Color("#24304a"))
		"物件", "痕迹":
			box.position = Vector2(40, 14)
			box.size = Vector2(SIZE.x - 54, SIZE.y - 24)
			title.add_theme_font_override("font", font("serif"))
			title.add_theme_font_size_override("font_size", 18)
			body.add_theme_font_override("font", font("hand"))
			body.add_theme_font_size_override("font_size", 15)
		"推论":
			box.position = Vector2(16, 14)
			box.size = Vector2(SIZE.x - 32, SIZE.y - 24)
			title.add_theme_font_override("font", font("serif"))
			title.add_theme_font_size_override("font_size", 20)
			body.add_theme_font_override("font", font("hand"))
			body.add_theme_font_size_override("font_size", 16)
		_:
			box.position = Vector2(16, 12)
			box.size = Vector2(SIZE.x - 40, SIZE.y - 20)
			title.add_theme_font_override("font", font("type"))
			title.add_theme_font_size_override("font_size", 17)
			body.add_theme_font_override("font", font("type"))
			body.add_theme_font_size_override("font_size", 14)
	title.custom_minimum_size.x = box.size.x
	body.custom_minimum_size.x = box.size.x
	body.max_lines_visible = 3 if kind != "证词" else 4


func _draw() -> void:
	var r := Rect2(Vector2.ZERO, SIZE)
	# 投影：拿起来的卡片影子更远
	var sh := Vector2(4, 5) + Vector2(4, 6) * _lift
	match kind:
		"物件", "痕迹":
			_draw_tag(r, sh)
		_:
			draw_rect(Rect2(r.position + sh, r.size), Color(0, 0, 0, 0.42))
			match kind:
				"照片":
					_draw_photo(r)
				"证词":
					_draw_index(r, Color("#f6f1e6"), true)
				"推论":
					_draw_index(r, Color("#dfe7ee"), false)
				_:
					_draw_paper(r)
	if selected:
		draw_rect(r.grow(3), RED, false, 3.0)


func _draw_paper(r: Rect2) -> void:
	draw_rect(r, Color("#ece2c9"))
	var y := 40.0
	while y < r.size.y - 6:
		draw_line(Vector2(10, y), Vector2(r.size.x - 10, y), Color(0.55, 0.47, 0.33, 0.22), 1.0)
		y += 19.0
	# 右上角折过的一角
	var c := r.size.x
	draw_colored_polygon(PackedVector2Array([Vector2(c - 22, 0), Vector2(c, 0), Vector2(c, 22)]), Color("#1b120c", 0.55))
	draw_colored_polygon(PackedVector2Array([Vector2(c - 22, 0), Vector2(c, 22), Vector2(c - 22, 22)]), Color("#d4c7a8"))
	_draw_pin()


func _draw_index(r: Rect2, bg: Color, testimony: bool) -> void:
	draw_rect(r, bg)
	draw_line(Vector2(0, 36), Vector2(r.size.x, 36), Color(0.75, 0.25, 0.22, 0.6), 1.5)
	var y := 56.0
	while y < r.size.y - 4:
		draw_line(Vector2(0, y), Vector2(r.size.x, y), Color(0.35, 0.5, 0.75, 0.22), 1.0)
		y += 20.0
	if testimony:
		draw_string(font("serif"), Vector2(r.size.x - 34, r.size.y - 8), "“", HORIZONTAL_ALIGNMENT_LEFT, -1, 48, Color(0.2, 0.25, 0.4, 0.18))
	else:
		_stamp(Vector2(r.size.x - 60, r.size.y - 16), "推论")
	_draw_pin()


func _draw_photo(r: Rect2) -> void:
	draw_rect(r, Color("#f1ece0"))
	var pic := Rect2(10, 10, r.size.x - 20, r.size.y - 52)
	if _image:
		draw_texture_rect(_image, pic, false, Color(1, 0.95, 0.85))
	else:
		# 还没有图片：一块冲得不太好的相片——中间亮、四角暗，几道竖着的银盐条纹
		draw_rect(pic, Color("#4a3e32"))
		for i in 6:
			var k := float(i) / 6.0
			draw_rect(pic.grow(-k * pic.size.y * 0.42), Color(0.62, 0.55, 0.45, 0.09))
		var rng := RandomNumberGenerator.new()
		rng.seed = hash(id)
		for i in 5:
			var x := pic.position.x + rng.randf() * pic.size.x
			draw_line(Vector2(x, pic.position.y), Vector2(x + rng.randf_range(-4, 4), pic.end.y), Color(0.9, 0.85, 0.75, 0.08), rng.randf_range(1, 3))
		# 一个模糊的人影或物件的轮廓
		var c := pic.get_center() + Vector2(rng.randf_range(-20, 20), 4)
		draw_circle(c + Vector2(0, -16), 10, Color(0.1, 0.08, 0.06, 0.35))
		draw_rect(Rect2(c + Vector2(-14, -4), Vector2(28, 26)), Color(0.1, 0.08, 0.06, 0.3))
	# 两条胶带
	for p in [Vector2(-8, -4), Vector2(r.size.x - 34, -4)]:
		draw_set_transform(p + Vector2(21, 8), deg_to_rad(-12 if p.x < 0 else 12))
		draw_rect(Rect2(-21, -8, 42, 16), Color(0.93, 0.89, 0.74, 0.7))
		draw_set_transform(Vector2.ZERO)


func _draw_tag(r: Rect2, sh: Vector2) -> void:
	var n := 18.0
	var pts := PackedVector2Array([Vector2(n, 0), Vector2(r.size.x, 0), Vector2(r.size.x, r.size.y), Vector2(n, r.size.y), Vector2(0, r.size.y - n), Vector2(0, n)])
	var shadow := PackedVector2Array()
	for p in pts:
		shadow.append(p + sh)
	draw_colored_polygon(shadow, Color(0, 0, 0, 0.42))
	draw_colored_polygon(pts, Color("#d9c08c"))
	draw_polyline(pts + PackedVector2Array([pts[0]]), Color(0.45, 0.33, 0.15, 0.45), 1.0)
	# 穿线的孔与一段线
	draw_circle(Vector2(20, r.size.y / 2), 7, Color("#efe2bf"))
	draw_arc(Vector2(20, r.size.y / 2), 7, 0, TAU, 16, Color(0.45, 0.33, 0.15, 0.7), 1.5)
	draw_circle(Vector2(20, r.size.y / 2), 3.5, Color("#2a1f14"))
	draw_line(Vector2(20, r.size.y / 2), Vector2(-14, r.size.y / 2 - 26), Color("#efe6d2"), 2.0)
	_stamp(Vector2(r.size.x - 56, r.size.y - 14), "证物" if kind == "物件" else "痕迹")


func _stamp(pos: Vector2, text: String) -> void:
	draw_set_transform(pos, deg_to_rad(-8))
	draw_rect(Rect2(-4, -18, 50, 24), Color(0.64, 0.13, 0.1, 0.55), false, 2.0)
	draw_string(font("serif"), Vector2(2, 0), text, HORIZONTAL_ALIGNMENT_LEFT, -1, 16, Color(0.64, 0.13, 0.1, 0.6))
	draw_set_transform(Vector2.ZERO)


func _draw_pin() -> void:
	var c := Vector2(SIZE.x / 2, 4)
	draw_circle(c + Vector2(2, 3), 7, Color(0, 0, 0, 0.35))
	draw_circle(c, 7, RED)
	draw_circle(c + Vector2(-2, -2), 2.5, Color(1, 0.7, 0.65, 0.8))
