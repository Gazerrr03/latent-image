extends RefCounted
## 餐桌关卡的餐具工厂（ded_table 专用）。
##
## 设计目标：不再用 BoxMesh / CylinderMesh 直接堆色块，而是
##   1) 用车削（lathe）与挤出（extrude）生成带厚度、带卷边的实体网格；
##   2) 用 Image 在引擎内画贴图（釉面、碎花、织物经纬、绣字、锡面锤纹、纸卡字迹），
##      包成 ImageTexture，不落盘、不产生 .import、不依赖 Python / Pillow / ImageMagick。
##
## 约定：所有物品的原点在底部中心，正视朝向 -Z；摆放时的朝向与缩放由 ded_table.gd 处理。
## 尺寸按设计稿：成人盘直径 0.22 m、艾瑞斯盘 0.17 m、卢西恩盘 0.19 m、
## 锡杯高 0.09 m、柄长 0.16 m。

const PLATE_SIZE := 512
const CLOTH_SIZE := 256
const TIN_SIZE := 256
const PAPER_SIZE := 256
const CUP_SIZE := 256

# 边带颜色（几何环，不用贴图，保证"实体色带"而不是贴纸感）
const RIM_COLOR := {
	"cobalt": Color("#2f4f8f"),
	"gold": Color("#f2cd74"),
	"brown": Color("#5a2f16"),
	"blue_thin": Color("#5c7f9c"),
	"rose": Color("#b0837a"),
}

static var _tex_cache := {}
static var _mat_cache := {}


# ─────────────────────────── 对外接口 ───────────────────────────

static func build_item(id: String) -> Node3D:
	var root := Node3D.new()
	root.name = "item_" + id
	root.set_meta("item_id", id)
	match id:
		"ambrose":
			_set_ambrose(root)
		"constance":
			_set_constance(root)
		"iris":
			_set_iris(root)
		"gideon":
			_set_gideon(root)
		"lucien":
			_set_lucien(root)
		"decoy_guest":
			_set_guest(root)
		"decoy_plate":
			_set_plain_plate(root)
		"decoy_cup":
			_set_wrong_tin(root)
		"decoy_napkin_i":
			_set_napkin_i(root)
		"decoy_card_penrose":
			_set_penrose_card(root)
		_:
			_set_plain_plate(root)
	return root


static func build_bell() -> Node3D:
	var root := Node3D.new()
	root.name = "table_bell"
	var brass := _mat_color(Color("#c39a52"), 0.32, 0.62)
	# 底座
	var base_prof := _ccw(PackedVector2Array([
		Vector2(0.0, 0.0), Vector2(0.075, 0.0), Vector2(0.078, 0.006),
		Vector2(0.070, 0.014), Vector2(0.030, 0.020), Vector2(0.0, 0.020),
	]))
	_add_mesh(root, _lathe(base_prof, 48, "flat", 0.078), brass)
	# 铃身：喇叭口 + 收颈
	var bell_prof := _ccw(PackedVector2Array([
		Vector2(0.0, 0.016), Vector2(0.062, 0.016), Vector2(0.064, 0.020),
		Vector2(0.058, 0.034), Vector2(0.044, 0.062), Vector2(0.030, 0.080),
		Vector2(0.020, 0.090), Vector2(0.014, 0.094), Vector2(0.0, 0.096),
	]))
	_add_mesh(root, _lathe(bell_prof, 48, "flat", 0.064), brass)
	# 顶钮
	var knob := MeshInstance3D.new()
	var sph := SphereMesh.new()
	sph.radius = 0.012
	sph.height = 0.020
	knob.mesh = sph
	knob.position = Vector3(0, 0.104, 0)
	knob.material_override = brass
	root.add_child(knob)
	return root


# ─────────────────────────── 五套正确餐具 ───────────────────────────

static func _place_card(root: Node3D, pos: Vector3, letter: String) -> void:
	# 图纸上每个位置有一张写着首字母的小卡片；用 Label3D 保证远看也读得出来
	var paper := _mat_color(Color("#f2ead8"), 0.72, 0.0)
	var card_mesh := BoxMesh.new()
	card_mesh.size = Vector3(0.046, 0.034, 0.0035)
	var card := _add_mesh(root, card_mesh, paper, Vector3(pos.x, 0.018, pos.z))
	card.rotation.x = deg_to_rad(-10)
	var label := Label3D.new()
	var f := SystemFont.new()
	f.font_names = PackedStringArray(["Microsoft YaHei", "SimHei", "Noto Sans SC"])
	label.font = f
	label.font_size = 48
	label.pixel_size = 0.00055
	label.text = letter + "."
	label.modulate = Color("#8b2f24")
	label.billboard = BaseMaterial3D.BILLBOARD_ENABLED
	label.position = Vector3(pos.x, 0.021, pos.z + 0.004)
	root.add_child(label)


## 一段裂纹/补钉：从 a 连到 b 的细条
static func _bar(root: Node3D, a: Vector3, b: Vector3, width: float, thick: float, mat: Material) -> void:
	var d := b - a
	var mesh := BoxMesh.new()
	mesh.size = Vector3(width, thick, d.length())
	var mi := _add_mesh(root, mesh, mat, (a + b) * 0.5)
	mi.rotation.y = atan2(d.x, d.z)


static func _set_ambrose(root: Node3D) -> void:
	_plate(root, 0.110, "cobalt", 0.009, _tex("plate_plain"))
	_glass_cup(root, Vector3(0.150, 0.0, 0.040), 0.032, 0.092)
	_cutlery(root, "knife", Vector3(0.152, 0.0, -0.030), 0.0, 0.160)
	_cutlery(root, "fork", Vector3(-0.146, 0.0, -0.020), 0.0, 0.160, 4)
	_napkin(root, Vector3(-0.140, 0.0, 0.150), 0.112, 0.092, _tex("cloth_white"), true)
	_place_card(root, Vector3(0.100, 0.0, 0.150), "A")


static func _set_constance(root: Node3D) -> void:
	_plate(root, 0.110, "gold", 0.007, _tex("plate_plain"))
	# 茶碟：图纸上茶杯下面有一只金边小碟
	_plate(root, 0.060, "gold", 0.004, _tex("plate_plain"), {}, Vector3(0.162, 0.0, 0.040))
	_teacup(root, Vector3(0.162, 0.0, 0.040), 0.046, 0.058, _tex("cup_floral"), true)
	# 茶杯口也描一圈金边，和盘子成套
	var cup_rim := TorusMesh.new()
	cup_rim.inner_radius = 0.0438
	cup_rim.outer_radius = 0.0462
	cup_rim.rings = 32
	cup_rim.ring_segments = 6
	_add_mesh(root, cup_rim, _mat_color(Color("#d9ad4a"), 0.28, 0.22), Vector3(0.162, 0.058, 0.040))
	_cutlery(root, "knife", Vector3(0.152, 0.0, -0.030), 0.0, 0.160)
	_cutlery(root, "fork", Vector3(-0.146, 0.0, -0.020), 0.0, 0.160, 4)
	_napkin(root, Vector3(-0.140, 0.0, 0.150), 0.112, 0.092, _tex("cloth_white"), true)
	_place_card(root, Vector3(-0.168, 0.0, 0.145), "C")


static func _set_iris(root: Node3D) -> void:
	_plate(root, 0.085, "rose", 0.003, _tex("plate_floral"))
	# 图纸上是散落在盘面的小粉点，不是盘沿一圈凸起
	var dot := _mat_color(Color("#b06a72"), 0.62, 0.0)
	var spots := [
		Vector2(-0.030, 0.018), Vector2(0.022, 0.030), Vector2(-0.006, -0.022),
		Vector2(0.040, -0.008), Vector2(-0.042, -0.016), Vector2(0.010, 0.004),
		Vector2(-0.020, 0.042), Vector2(0.030, 0.042), Vector2(0.002, -0.042),
		Vector2(0.050, 0.012),
	]
	for p2 in spots:
		var disc := CylinderMesh.new()
		disc.top_radius = 0.0048
		disc.bottom_radius = 0.0048
		disc.height = 0.0008
		_add_mesh(root, disc, dot, Vector3(p2.x, 0.018, p2.y))
	# 茶杯带茶碟
	_plate(root, 0.052, "rose", 0.003, _tex("plate_plain"), {}, Vector3(0.140, 0.0, 0.030))
	_teacup(root, Vector3(0.140, 0.0, 0.030), 0.048, 0.044, _tex("cup_plain"), false)
	_cutlery(root, "fork", Vector3(-0.108, 0.0, -0.012), 0.0, 0.128, 3)
	_napkin(root, Vector3(-0.120, 0.0, 0.120), 0.098, 0.078, _tex("cloth_i"), true)
	_place_card(root, Vector3(0.010, 0.0, 0.160), "I")


static func _set_gideon(root: Node3D) -> void:
	_plate(root, 0.110, "brown", 0.014, _tex("plate_rustic"))
	_tin_mug(root, Vector3(0.152, 0.0, 0.038), 0.038, 0.092, true, -1.0, false)
	_cutlery(root, "knife", Vector3(0.150, 0.0, -0.030), 0.0, 0.160)
	_napkin(root, Vector3(-0.145, 0.0, 0.152), 0.110, 0.090, _tex("cloth_coarse"), false)
	_place_card(root, Vector3(0.105, 0.0, 0.150), "G")


static func _set_lucien(root: Node3D) -> void:
	# 旧盘：略小、釉面发黄、盘沿有缺口和补钉；图纸上盘沿是深棕细边
	_plate(root, 0.095, "brown", 0.010, _tex("plate_aged"), {"center": 0.0, "width": 30.0, "depth": 0.008, "drop": 0.004, "min_r": 0.065})
	# 补钉：跨过缺口的两枚金属小钉，平贴在盘沿上（长边顺着半径方向）
	var steel := _mat_color(Color("#a8a293"), 0.30, 0.55)
	for k in 2:
		var staple := _add_mesh(root, _extrude(PackedVector2Array([
			Vector2(-0.005, -0.012), Vector2(0.005, -0.012),
			Vector2(0.005, 0.012), Vector2(-0.005, 0.012),
		]), 0.0022), steel)
		var ang := deg_to_rad(0.0 + (float(k) - 0.5) * 5.5)
		staple.position = Vector3(cos(ang) * 0.089, 0.0172, sin(ang) * 0.089)
		staple.rotation.y = deg_to_rad(90.0) - ang
	# 缺口旁的一道深色裂纹，远看也能认出“修补过”
	var crack_mat := _mat_color(Color("#4a3a26"), 0.92, 0.0)
	_bar(root, Vector3(0.078, 0.0176, 0.0), Vector3(0.020, 0.0176, 0.028), 0.0018, 0.0011, crack_mat)
	_bar(root, Vector3(0.020, 0.0176, 0.028), Vector3(0.006, 0.0176, 0.060), 0.0018, 0.0011, crack_mat)
	_bar(root, Vector3(0.006, 0.0176, 0.060), Vector3(-0.024, 0.0176, 0.070), 0.0018, 0.0011, crack_mat)
	# 盘沿上的金属修补夹
	_bar(root, Vector3(0.088, 0.0190, 0.0), Vector3(0.064, 0.0190, 0.0), 0.006, 0.0020, steel)
	_bar(root, Vector3(0.064, 0.0190, 0.0), Vector3(0.064, 0.0190, 0.014), 0.0020, 0.0020, steel)
	# 缺角锡杯：缺口在右后
	_tin_mug(root, Vector3(0.135, 0.0, 0.040), 0.031, 0.076, false, 118.0, true)
	_cutlery(root, "fork", Vector3(-0.118, 0.0, -0.014), 0.0, 0.128, 3)
	_napkin(root, Vector3(-0.128, 0.0, 0.130), 0.098, 0.078, _tex("cloth_l"), true)
	# 餐巾上再用深色线绣一个明显的 L.，避免只靠贴图看不清
	var thread := _mat_color(Color("#2e2722"), 0.92, 0.0)
	var lv_mesh := BoxMesh.new()
	lv_mesh.size = Vector3(0.0026, 0.0012, 0.024)
	_add_mesh(root, lv_mesh, thread, Vector3(-0.142, 0.0105, 0.128))
	var lh_mesh := BoxMesh.new()
	lh_mesh.size = Vector3(0.015, 0.0012, 0.0026)
	_add_mesh(root, lh_mesh, thread, Vector3(-0.135, 0.0105, 0.139))
	_place_card(root, Vector3(-0.160, 0.0, 0.150), "L")


# ─────────────────────────── 干扰物 ───────────────────────────

static func _set_guest(root: Node3D) -> void:
	# 客人备用套：蓝边细一点、成套餐具（多一只面包碟）、餐巾光洁无绣字
	_plate(root, 0.110, "blue_thin", 0.005, _tex("plate_guest"))
	_glass_cup(root, Vector3(0.150, 0.0, 0.040), 0.030, 0.086)
	_plate(root, 0.050, "blue_thin", 0.003, _tex("plate_guest"), {}, Vector3(-0.168, 0.0, -0.015))
	_cutlery(root, "knife", Vector3(0.152, 0.0, -0.045), 0.0, 0.158)
	_cutlery(root, "fork", Vector3(-0.146, 0.0, -0.045), 0.0, 0.158, 4)
	_napkin(root, Vector3(-0.142, 0.0, 0.150), 0.108, 0.090, _tex("cloth_white"), true)


static func _set_plain_plate(root: Node3D) -> void:
	# 普通小盘：无花纹、无描边、无配套
	_plate(root, 0.085, "", 0.0, _tex("plate_plain"))


static func _set_wrong_tin(root: Node3D) -> void:
	# 错锡杯：缺口在左前，杯底没有 L. 刻痕
	_tin_mug(root, Vector3(0.0, 0.0, 0.0), 0.031, 0.080, false, -62.0, true)


static func _set_napkin_i(root: Node3D) -> void:
	# 一块单独绣 I. 的餐巾（属艾瑞斯），平摊、比成套里的更亮
	_napkin(root, Vector3.ZERO, 0.114, 0.094, _tex("cloth_i"), false)


static func _set_penrose_card(root: Node3D) -> void:
	# 彭罗斯旧地点卡：薄纸卡 + 折角，只可阅读，不能摆上桌
	var paper := _mat_cloth(_tex("paper_card"))
	var card := _extrude(PackedVector2Array([
		Vector2(-0.043, -0.062), Vector2(0.043, -0.062),
		Vector2(0.043, 0.062), Vector2(-0.043, 0.062),
	]), 0.0018)
	var mi := _add_mesh(root, card, paper)
	mi.rotation.x = deg_to_rad(-4)
	# 折角（一小片翻起来的纸角）
	var corner := _extrude(PackedVector2Array([
		Vector2(0.0, 0.0), Vector2(0.026, 0.0), Vector2(0.0, -0.026),
	]), 0.0012)
	var c := _add_mesh(root, corner, paper)
	c.position = Vector3(0.043, 0.002, 0.062)
	c.rotation.y = deg_to_rad(-18)


# ─────────────────────────── 零件 ───────────────────────────

static func _plate(root: Node3D, rad: float, rim: String, rim_w: float, tex: ImageTexture, chip := {}, at := Vector3.ZERO) -> void:
	# 传进来的是半径（成人盘 0.110 = 直径 0.22），不要再折半
	var r := rad
	# 剖面：外沿立起 → 一圈平盘沿（色带贴在这圈上）→ 斜下收进盘心
	var prof := _ccw(PackedVector2Array([
		Vector2(0.0, 0.0),
		Vector2(r * 0.55, 0.0),
		Vector2(r * 0.88, 0.0015),
		Vector2(r * 0.965, 0.0060),
		Vector2(r, 0.0110),
		Vector2(r * 0.992, 0.0160),
		Vector2(r * 0.865, 0.0160),
		Vector2(r * 0.790, 0.0095),
		Vector2(r * 0.620, 0.0055),
		Vector2(0.0, 0.0055),
	]))
	var mat := _mat_ceramic(tex)
	var body := _add_mesh(root, _lathe(prof, 72, "planar", r, chip), mat)
	body.position = at
	if rim != "" and rim_w > 0.0:
		var r_out := r * 0.985
		var r_in := maxf(r * 0.865, r_out - rim_w)
		var band := _ccw(PackedVector2Array([
			Vector2(r_in, 0.0155),
			Vector2(r_out, 0.0155),
			Vector2(r_out, 0.0192),
			Vector2(r_in, 0.0192),
		]))
		# 金边不做高金属度：没有反射探针时会发黑，改成偏暖的低金属度漆金
		var rim_mat := _mat_color(Color("#d9ad4a"), 0.28, 0.22) if rim == "gold" else _mat_color(RIM_COLOR[rim], 0.32, 0.04)
		var band_mi := _add_mesh(root, _lathe(band, 72, "planar", r), rim_mat)
		band_mi.position = at
		# 图纸上每只盘子盘沿内侧还有两道细色线
		for k in 2:
			var rr := r * (0.845 - 0.045 * float(k))
			var ring := TorusMesh.new()
			ring.inner_radius = rr - 0.0007
			ring.outer_radius = rr + 0.0007
			ring.rings = 48
			ring.ring_segments = 6
			_add_mesh(root, ring, rim_mat, Vector3(at.x, 0.0068, at.z))


static func _teacup(root: Node3D, pos: Vector3, r: float, h: float, tex: ImageTexture, handle: bool) -> void:
	var prof := _cup_profile(r, h, 0.0035)
	var mat := _mat_ceramic(tex)
	var mi := _add_mesh(root, _lathe(prof, 48, "cyl", r, {}, h), mat)
	mi.position = pos
	if handle:
		_handle(root, pos, r, h)


static func _glass_cup(root: Node3D, pos: Vector3, r: float, h: float) -> void:
	var prof := PackedVector2Array([
		Vector2(0.0, 0.004),
		Vector2(r * 0.90, 0.004),
		Vector2(r * 0.94, 0.010),
		Vector2(r, 0.020),
		Vector2(r, h),
		Vector2(r * 0.94, h),
		Vector2(r * 0.90, 0.014),
		Vector2(0.0, 0.010),
	])
	var glass := _mat_color(Color(0.70, 0.86, 0.92, 0.42), 0.05, 0.0)
	glass.transparency = BaseMaterial3D.TRANSPARENCY_ALPHA
	glass.cull_mode = BaseMaterial3D.CULL_DISABLED
	glass.metallic_specular = 0.9
	var mi := _add_mesh(root, _lathe(prof, 32, "cyl", r, {}, h), glass)
	mi.position = pos
	# 切面水晶杯：竖向棱 + 横向刻线，远看不是一只普通透明杯
	var rib_mat := _mat_color(Color(0.86, 0.95, 1.0, 0.52), 0.08, 0.0)
	rib_mat.transparency = BaseMaterial3D.TRANSPARENCY_ALPHA
	for i in 10:
		var a := TAU * float(i) / 10.0
		var rib := CylinderMesh.new()
		rib.top_radius = 0.0013
		rib.bottom_radius = 0.0013
		rib.height = h * 0.86
		_add_mesh(root, rib, rib_mat, pos + Vector3(cos(a) * r * 0.985, h * 0.46, sin(a) * r * 0.985))
	for k in 3:
		var ring := TorusMesh.new()
		ring.inner_radius = r * 0.985 - 0.0007
		ring.outer_radius = r * 0.985 + 0.0007
		ring.rings = 32
		ring.ring_segments = 6
		_add_mesh(root, ring, rib_mat, pos + Vector3(0, h * (0.28 + 0.22 * float(k)), 0))
	# 杯口一圈亮边，让透明玻璃有轮廓
	var lip := _ccw(PackedVector2Array([
		Vector2(r * 0.96, h - 0.002), Vector2(r * 1.005, h - 0.002),
		Vector2(r * 1.005, h + 0.001), Vector2(r * 0.96, h + 0.001),
	]))
	var lip_mat := _mat_color(Color(0.88, 0.95, 0.95, 0.55), 0.08, 0.0)
	lip_mat.transparency = BaseMaterial3D.TRANSPARENCY_ALPHA
	var lip_mi := _add_mesh(root, _lathe(lip, 40, "planar", r * 1.005), lip_mat)
	lip_mi.position = pos


static func _tin_mug(root: Node3D, pos: Vector3, r: float, h: float, handle: bool, chip_deg: float, chipped: bool) -> void:
	var prof := _cup_profile(r, h, 0.0028)
	var chip := {}
	if chipped:
		chip = {"center": chip_deg, "width": 22.0, "depth": 0.0055, "drop": 0.010, "min_r": r * 0.72}
	var mat := _mat_metal_tex(_tex("tin"), 0.78, 0.16)
	var mi := _add_mesh(root, _lathe(prof, 40, "cyl", r, chip, h), mat)
	mi.position = pos
	if handle:
		_handle(root, pos, r, h, _tex("tin"))


static func _handle(root: Node3D, pos: Vector3, r: float, h: float, tex: ImageTexture = null) -> void:
	# 杯把：贴着杯壁的一圈 C 形，两端落在杯身上
	var pts := []
	for i in 13:
		var t := float(i) / 12.0
		var ang := deg_to_rad(lerpf(-104.0, 104.0, t))
		pts.append(Vector3(r * 1.02 + cos(ang) * r * 0.62, h * 0.54 + sin(ang) * r * 0.62, 0.0))
	var mat := _mat_metal_tex(tex, 0.34, 0.55) if tex != null else _mat_ceramic(_tex("cup_plain"))
	var mi := _add_mesh(root, _tube(pts, 0.0042, 10), mat)
	mi.position = pos


static func _cutlery(root: Node3D, kind: String, pos: Vector3, rot_y: float, length: float, tines := 4) -> void:
	var silver := _mat_color(Color("#c4c3ba"), 0.34, 0.32)
	if kind == "knife":
		var blade := length - 0.082
		var outline := PackedVector2Array([
			Vector2(-0.0065, 0.0), Vector2(0.0065, 0.0),
			Vector2(0.0090, length * 0.42), Vector2(0.0115, length * 0.52),
			Vector2(0.0080, length * 0.985), Vector2(0.0, length),
			Vector2(-0.0080, length * 0.985), Vector2(-0.0105, length * 0.55),
			Vector2(-0.0085, length * 0.40),
		])
		var mi := _add_mesh(root, _extrude(outline, 0.0032), silver)
		mi.position = pos
		mi.rotation.y = rot_y
		# 刀柄深色包片
		var grip := _add_mesh(root, _extrude(PackedVector2Array([
			Vector2(-0.0062, 0.004), Vector2(0.0062, 0.004),
			Vector2(0.0062, 0.058), Vector2(-0.0062, 0.058),
		]), 0.0040), _mat_color(Color("#4a3527"), 0.55, 0.05))
		grip.position = pos + Vector3(0.0, 0.0006, 0.0)
		grip.rotation.y = rot_y
	elif kind == "fork":
		var mi := _add_mesh(root, _extrude(PackedVector2Array([
			Vector2(-0.0070, 0.0), Vector2(0.0070, 0.0),
			Vector2(0.0075, length * 0.62), Vector2(-0.0075, length * 0.62),
		]), 0.0030), silver)
		mi.position = pos
		mi.rotation.y = rot_y
		# 叉头
		var head := _add_mesh(root, _extrude(PackedVector2Array([
			Vector2(-0.0135, length * 0.60), Vector2(0.0135, length * 0.60),
			Vector2(0.0125, length * 0.72), Vector2(-0.0125, length * 0.72),
		]), 0.0026), silver)
		head.position = pos
		head.rotation.y = rot_y
		for i in tines:
			var x0 := lerpf(-0.0105, 0.0105, float(i) / float(tines - 1))
			var tine := _add_mesh(root, _extrude(PackedVector2Array([
				Vector2(x0 - 0.0016, length * 0.70), Vector2(x0 + 0.0016, length * 0.70),
				Vector2(x0 + 0.0016, length * 0.985), Vector2(x0 - 0.0016, length * 0.985),
			]), 0.0022), silver)
			tine.position = pos
			tine.rotation.y = rot_y
	else:
		# 餐刀（吉迪恩，只有刀）
		_cutlery(root, "knife", pos, rot_y, length)


static func _napkin(root: Node3D, pos: Vector3, w: float, d: float, tex: ImageTexture, folded: bool) -> void:
	var cloth := _mat_cloth(tex)
	var base := _extrude(PackedVector2Array([
		Vector2(-w * 0.5, -d * 0.5), Vector2(w * 0.5, -d * 0.5),
		Vector2(w * 0.5, d * 0.5), Vector2(-w * 0.5, d * 0.5),
	]), 0.0045)
	var mi := _add_mesh(root, base, cloth)
	mi.position = pos
	if folded:
		var flap := _extrude(PackedVector2Array([
			Vector2(-w * 0.24, -d * 0.23), Vector2(w * 0.24, -d * 0.23),
			Vector2(w * 0.24, d * 0.23), Vector2(-w * 0.24, d * 0.23),
		]), 0.0032)
		var f := _add_mesh(root, flap, _mat_cloth(_tex("cloth_fold")))
		f.position = pos + Vector3(0.0, 0.0042, 0.0)
		f.rotation.y = deg_to_rad(7)


# ─────────────────────────── 网格工具 ───────────────────────────

static func _ccw(profile: PackedVector2Array) -> PackedVector2Array:
	var area := 0.0
	var n := profile.size()
	for i in n:
		var a := profile[i]
		var b := profile[(i + 1) % n]
		area += a.x * b.y - b.x * a.y
	if area >= 0.0:
		return profile
	var out := PackedVector2Array()
	for i in range(n - 1, -1, -1):
		out.append(profile[i])
	return out


static func _cup_profile(r: float, h: float, wall: float) -> PackedVector2Array:
	var ri := r - wall
	return _ccw(PackedVector2Array([
		Vector2(0.0, wall),
		Vector2(ri, wall),
		Vector2(ri, h - wall * 0.5),
		Vector2(r, h),
		Vector2(r, h * 0.10),
		Vector2(r * 0.965, 0.004),
		Vector2(0.0, 0.0),
	]))


static func _chip_dent(angle: float, chip: Dictionary) -> float:
	var center := deg_to_rad(float(chip.get("center", 0.0)))
	var half := deg_to_rad(float(chip.get("width", 20.0))) * 0.5
	var d := absf(wrapf(angle - center, -PI, PI))
	if d >= half:
		return 0.0
	var t := 0.5 - 0.5 * cos(PI * (1.0 - d / half))
	return t


static func _lathe(profile_in: PackedVector2Array, segs: int, uv_mode: String, uv_ref: float, chip := {}, height := 0.0) -> ArrayMesh:
	var profile := _ccw(profile_in)
	var n := profile.size()
	var pnorm := PackedVector2Array()
	for j in n:
		var a := profile[maxi(j - 1, 0)]
		var b := profile[mini(j + 1, n - 1)]
		var t := b - a
		if t.length_squared() < 1e-12:
			t = Vector2(0.0, 1.0)
		t = t.normalized()
		pnorm.append(Vector2(t.y, -t.x))

	var verts := []
	var norms := []
	for j in n:
		var row := []
		var row_n := []
		var pr := profile[j].x
		var py := profile[j].y
		for i in segs + 1:
			var ang := TAU * float(i) / float(segs)
			var rr := pr
			var yy := py
			if not chip.is_empty():
				var k := _chip_dent(ang, chip)
				if k > 0.0 and pr >= float(chip.get("min_r", 0.0)):
					rr = maxf(pr - k * float(chip.get("depth", 0.006)), 0.0)
					yy -= k * float(chip.get("drop", 0.003))
			row.append(Vector3(rr * cos(ang), yy, rr * sin(ang)))
			var nv := Vector3(pnorm[j].x * cos(ang), pnorm[j].y, pnorm[j].x * sin(ang))
			row_n.append(nv.normalized())
		verts.append(row)
		norms.append(row_n)

	var st := SurfaceTool.new()
	st.begin(Mesh.PRIMITIVE_TRIANGLES)
	for j in n - 1:
		for i in segs:
			var p1: Vector3 = verts[j][i]
			var p2: Vector3 = verts[j][i + 1]
			var p3: Vector3 = verts[j + 1][i + 1]
			var p4: Vector3 = verts[j + 1][i]
			var n1: Vector3 = norms[j][i]
			var n2: Vector3 = norms[j][i + 1]
			var n3: Vector3 = norms[j + 1][i + 1]
			var n4: Vector3 = norms[j + 1][i]
			var u1 := _uv_of(p1, uv_mode, uv_ref, height)
			var u2 := _uv_of(p2, uv_mode, uv_ref, height)
			var u3 := _uv_of(p3, uv_mode, uv_ref, height)
			var u4 := _uv_of(p4, uv_mode, uv_ref, height)
			if p1.distance_squared_to(p2) > 1e-12 and p2.distance_squared_to(p3) > 1e-12:
				_tri(st, p1, p2, p3, n1, n2, n3, u1, u2, u3)
			if p1.distance_squared_to(p3) > 1e-12 and p3.distance_squared_to(p4) > 1e-12:
				_tri(st, p1, p3, p4, n1, n3, n4, u1, u3, u4)
	return st.commit()


static func _uv_of(p: Vector3, mode: String, ref: float, height: float) -> Vector2:
	if mode == "cyl":
		var ang := atan2(p.z, p.x)
		var u := fposmod(ang, TAU) / TAU
		var v := clampf(p.y / maxf(height, 0.0001), 0.0, 1.0)
		return Vector2(u, v)
	var r2 := maxf(ref * 2.0, 0.0001)
	return Vector2(0.5 + p.x / r2, 0.5 - p.z / r2)


static func _extrude(outline: PackedVector2Array, thickness: float) -> ArrayMesh:
	var pts := outline
	var minx := INF
	var maxx := -INF
	var minz := INF
	var maxz := -INF
	for p in pts:
		minx = minf(minx, p.x)
		maxx = maxf(maxx, p.x)
		minz = minf(minz, p.y)
		maxz = maxf(maxz, p.y)
	var w := maxf(maxx - minx, 0.0001)
	var d := maxf(maxz - minz, 0.0001)
	var up := Vector3.UP
	var down := Vector3.DOWN
	var st := SurfaceTool.new()
	st.begin(Mesh.PRIMITIVE_TRIANGLES)
	# 顶面 / 底面：扇形三角化（轮廓均为星形，质心可见全部顶点）
	var c := Vector2.ZERO
	for p in pts:
		c += p
	c /= float(pts.size())
	var cy := thickness * 0.5
	var uv_c := Vector2((c.x - minx) / w, (c.y - minz) / d)
	for i in pts.size():
		var a := pts[i]
		var b := pts[(i + 1) % pts.size()]
		var ua := Vector2((a.x - minx) / w, (a.y - minz) / d)
		var ub := Vector2((b.x - minx) / w, (b.y - minz) / d)
		_tri(st, Vector3(c.x, cy, c.y), Vector3(a.x, cy, a.y), Vector3(b.x, cy, b.y), up, up, up, uv_c, ua, ub)
		_tri(st, Vector3(c.x, -cy, c.y), Vector3(a.x, -cy, a.y), Vector3(b.x, -cy, b.y), down, down, down, uv_c, ua, ub)
	# 侧壁
	for i in pts.size():
		var a := pts[i]
		var b := pts[(i + 1) % pts.size()]
		var e := (b - a).normalized()
		var nrm := Vector3(e.y, 0.0, -e.x).normalized()
		var ua := Vector2((a.x - minx) / w, (a.y - minz) / d)
		var ub := Vector2((b.x - minx) / w, (b.y - minz) / d)
		var a0 := Vector3(a.x, -cy, a.y)
		var b0 := Vector3(b.x, -cy, b.y)
		var a1 := Vector3(a.x, cy, a.y)
		var b1 := Vector3(b.x, cy, b.y)
		_tri(st, a0, b0, b1, nrm, nrm, nrm, ua, ub, ub)
		_tri(st, a0, b1, a1, nrm, nrm, nrm, ua, ub, ua)
	return st.commit()


static func _tube(points: Array, radius: float, segs := 10) -> ArrayMesh:
	var st := SurfaceTool.new()
	st.begin(Mesh.PRIMITIVE_TRIANGLES)
	var rings := []
	var ring_n := []
	for i in points.size():
		var p: Vector3 = points[i]
		var prev: Vector3 = points[maxi(i - 1, 0)]
		var next: Vector3 = points[mini(i + 1, points.size() - 1)]
		var t := (next - prev).normalized()
		var ref := Vector3.UP if absf(t.dot(Vector3.UP)) < 0.9 else Vector3.RIGHT
		var b1 := t.cross(ref).normalized()
		var b2 := t.cross(b1).normalized()
		var ring := []
		var ring_norm := []
		for k in segs + 1:
			var ang := TAU * float(k) / float(segs)
			var dir := b1 * cos(ang) + b2 * sin(ang)
			ring.append(p + dir * radius)
			ring_norm.append(dir)
		rings.append(ring)
		ring_n.append(ring_norm)
	for i in points.size() - 1:
		for k in segs:
			var p1: Vector3 = rings[i][k]
			var p2: Vector3 = rings[i][k + 1]
			var p3: Vector3 = rings[i + 1][k + 1]
			var p4: Vector3 = rings[i + 1][k]
			var n1: Vector3 = ring_n[i][k]
			var n2: Vector3 = ring_n[i][k + 1]
			var n3: Vector3 = ring_n[i + 1][k + 1]
			var n4: Vector3 = ring_n[i + 1][k]
			_tri(st, p1, p2, p3, n1, n2, n3, Vector2.ZERO, Vector2.ZERO, Vector2.ZERO)
			_tri(st, p1, p3, p4, n1, n3, n4, Vector2.ZERO, Vector2.ZERO, Vector2.ZERO)
	return st.commit()


static func _tri(st: SurfaceTool, p1: Vector3, p2: Vector3, p3: Vector3,
		n1: Vector3, n2: Vector3, n3: Vector3,
		u1: Vector2, u2: Vector2, u3: Vector2) -> void:
	# Godot 的正面是「顺时针绕序」：从法线一侧看过去，顶点要按顺时针排。
	# 右手定则下 (p2-p1)×(p3-p1) 与法线同向 = 逆时针 = 背面，所以这里要反着翻。
	var fn := (p2 - p1).cross(p3 - p1)
	var ref := (n1 + n2 + n3)
	if fn.dot(ref) > 0.0:
		var tp := p2
		p2 = p3
		p3 = tp
		var tn := n2
		n2 = n3
		n3 = tn
		var tu := u2
		u2 = u3
		u3 = tu
	st.set_normal(n1)
	st.set_uv(u1)
	st.add_vertex(p1)
	st.set_normal(n2)
	st.set_uv(u2)
	st.add_vertex(p2)
	st.set_normal(n3)
	st.set_uv(u3)
	st.add_vertex(p3)


static func _add_mesh(parent: Node3D, mesh: Mesh, mat: Material, pos := Vector3.ZERO) -> MeshInstance3D:
	var mi := MeshInstance3D.new()
	mi.mesh = mesh
	mi.material_override = mat
	mi.position = pos
	parent.add_child(mi)
	return mi


# ─────────────────────────── 材质 ───────────────────────────

static func _mat_color(c: Color, rough: float, metal: float) -> StandardMaterial3D:
	var key := "c_%s_%.2f_%.2f" % [c.to_html(), rough, metal]
	if _mat_cache.has(key):
		return _mat_cache[key]
	var m := StandardMaterial3D.new()
	m.albedo_color = c
	m.roughness = rough
	m.metallic = metal
	m.texture_filter = BaseMaterial3D.TEXTURE_FILTER_LINEAR_WITH_MIPMAPS_ANISOTROPIC
	_mat_cache[key] = m
	return m


static func _mat_ceramic(tex: ImageTexture) -> StandardMaterial3D:
	var key := "cer_" + str(tex.get_instance_id())
	if _mat_cache.has(key):
		return _mat_cache[key]
	var m := StandardMaterial3D.new()
	m.albedo_texture = tex
	m.albedo_color = Color(1, 1, 1)
	m.roughness = 0.42
	m.metallic = 0.0
	m.metallic_specular = 0.5
	m.texture_filter = BaseMaterial3D.TEXTURE_FILTER_LINEAR_WITH_MIPMAPS_ANISOTROPIC
	_mat_cache[key] = m
	return m


static func _mat_metal_tex(tex: ImageTexture, rough: float, metal: float) -> StandardMaterial3D:
	var key := "metal_%s_%.2f_%.2f" % [str(tex.get_instance_id()), rough, metal]
	if _mat_cache.has(key):
		return _mat_cache[key]
	var m := StandardMaterial3D.new()
	m.albedo_texture = tex
	m.roughness = rough
	m.metallic = metal
	m.metallic_specular = 0.7
	m.texture_filter = BaseMaterial3D.TEXTURE_FILTER_LINEAR_WITH_MIPMAPS_ANISOTROPIC
	_mat_cache[key] = m
	return m


static func _mat_cloth(tex: ImageTexture) -> StandardMaterial3D:
	var key := "cloth_" + str(tex.get_instance_id())
	if _mat_cache.has(key):
		return _mat_cache[key]
	var m := StandardMaterial3D.new()
	m.albedo_texture = tex
	m.roughness = 0.94
	m.metallic = 0.0
	m.texture_filter = BaseMaterial3D.TEXTURE_FILTER_LINEAR_WITH_MIPMAPS_ANISOTROPIC
	_mat_cache[key] = m
	return m


# ─────────────────────────── 贴图 ───────────────────────────

static func _tex(key: String) -> ImageTexture:
	if _tex_cache.has(key):
		return _tex_cache[key]
	var img: Image
	match key:
		"plate_plain":
			img = _img_plate(Color("#e9e0ca"), 0.25, 0.0, false)
		"plate_guest":
			img = _img_plate(Color("#efeade"), 0.05, 0.0, false)
		"plate_rustic":
			img = _img_plate(Color("#dbc9a8"), 0.75, 0.0, false)
		"plate_floral":
			img = _img_plate(Color("#eee5d3"), 0.30, 0.85, false)
		"plate_aged":
			img = _img_plate(Color("#d9c9a4"), 0.95, 0.0, true)
		"cup_floral":
			img = _img_cup(Color("#f3ece0"), true)
		"cup_plain":
			img = _img_cup(Color("#f5efe4"), false)
		"tin":
			img = _img_tin()
		"cloth_white":
			img = _img_cloth(Color("#f2ece0"), "", 0.0)
		"cloth_fold":
			img = _img_cloth(Color("#efe8da"), "", 0.0)
		"cloth_i":
			img = _img_cloth(Color("#f6f1e6"), "I", 0.0)
		"cloth_l":
			img = _img_cloth(Color("#efe7d6"), "L", 0.18)
		"cloth_coarse":
			img = _img_cloth(Color("#ddd2bb"), "", 0.0)
		"paper_card":
			img = _img_paper()
		_:
			img = _img_plate(Color("#f4eddd"), 0.2, 0.0, false)
	img.generate_mipmaps()
	var t := ImageTexture.create_from_image(img)
	_tex_cache[key] = t
	return t


static func _img_new(size: int, c: Color) -> Image:
	var img := Image.create_empty(size, size, false, Image.FORMAT_RGBA8)
	img.fill(c)
	return img


static func _blend(img: Image, x: int, y: int, c: Color) -> void:
	if x < 0 or y < 0 or x >= img.get_width() or y >= img.get_height():
		return
	if c.a >= 0.995:
		img.set_pixel(x, y, c)
		return
	var d := img.get_pixel(x, y)
	img.set_pixel(x, y, Color(
		d.r + (c.r - d.r) * c.a,
		d.g + (c.g - d.g) * c.a,
		d.b + (c.b - d.b) * c.a,
		1.0))


static func _disc(img: Image, cx: float, cy: float, r: float, c: Color) -> void:
	var x0 := int(floor(cx - r))
	var x1 := int(ceil(cx + r))
	var y0 := int(floor(cy - r))
	var y1 := int(ceil(cy + r))
	for y in range(y0, y1 + 1):
		for x in range(x0, x1 + 1):
			var dx := x - cx
			var dy := y - cy
			if dx * dx + dy * dy <= r * r:
				_blend(img, x, y, c)


static func _line(img: Image, a: Vector2, b: Vector2, c: Color, width: float, dashed := false) -> void:
	var len := a.distance_to(b)
	if len < 0.001:
		return
	var steps := int(len * 2.0) + 1
	for i in steps + 1:
		var t := float(i) / float(steps)
		if dashed and fposmod(t * len, 5.0) > 3.2:
			continue
		var p := a.lerp(b, t)
		_disc(img, p.x, p.y, width * 0.5, c)


static func _img_plate(base: Color, wear: float, floral: float, cracked: bool) -> Image:
	var size := PLATE_SIZE
	var img := _img_new(size, base)
	var rng := RandomNumberGenerator.new()
	rng.seed = int(wear * 977.0 + floral * 131.0 + (10.0 if cracked else 0.0))
	var mid := float(size) * 0.5
	# 釉面深浅：几十个同心半透明圆，形成轻微聚釉感
	for i in 26:
		var rr := mid * (0.10 + 0.036 * float(i))
		_disc_outline(img, mid, mid, rr, 2.0, Color(1, 1, 1, 0.035 if i % 2 == 0 else 0.0))
	# 边缘积釉：外圈略深
	for i in 12:
		_disc_outline(img, mid, mid, mid * (0.985 - 0.006 * float(i)), 2.4, Color(0.55, 0.45, 0.32, 0.022))
	# 釉面小斑点
	for i in int(900.0 + wear * 900.0):
		var ang := rng.randf() * TAU
		var rad := sqrt(rng.randf()) * mid * 0.985
		var p := Vector2(mid + cos(ang) * rad, mid + sin(ang) * rad)
		var s := rng.randf_range(0.6, 1.9)
		_disc(img, p.x, p.y, s, Color(0.62, 0.52, 0.40, rng.randf_range(0.05, 0.18)))
	if floral > 0.0:
		for i in 30:
			var ang := rng.randf() * TAU
			var rad := rng.randf_range(mid * 0.26, mid * 0.86)
			var p := Vector2(mid + cos(ang) * rad, mid + sin(ang) * rad)
			var r := rng.randf_range(9.0, 17.0)
			# 细枝：从花心朝盘心方向带一小段
			var inward := (Vector2(mid, mid) - p).normalized()
			_line(img, p, p + inward * r * 1.5, Color(0.40, 0.46, 0.34, 0.32 * floral), 1.2)
			_flower(img, p.x, p.y, r, rng, floral)
	if wear > 0.5:
		# 使用痕迹：盘沿发暗 + 细划痕
		for i in 26:
			var ang := rng.randf() * TAU
			var rad := rng.randf_range(mid * 0.55, mid * 0.99)
			var p0 := Vector2(mid + cos(ang) * rad, mid + sin(ang) * rad)
			var p1 := p0 + Vector2(rng.randf_range(-26, 26), rng.randf_range(-26, 26))
			_line(img, p0, p1, Color(0.55, 0.46, 0.34, 0.12), rng.randf_range(0.7, 1.4))
	if cracked:
		for i in 5:
			var a0 := rng.randf() * TAU
			var p := Vector2(mid + cos(a0) * mid * 0.86, mid + sin(a0) * mid * 0.86)
			for k in 9:
				var p2 := p + Vector2(rng.randf_range(-14, 14), rng.randf_range(-14, 14))
				_line(img, p, p2, Color(0.36, 0.28, 0.18, 0.42), 0.9)
				p = p2
		# 陈年污渍
		for i in 9:
			var ang := rng.randf() * TAU
			var rad := rng.randf_range(mid * 0.5, mid * 0.95)
			_disc(img, mid + cos(ang) * rad, mid + sin(ang) * rad, rng.randf_range(6, 18), Color(0.55, 0.44, 0.26, 0.07))
	return img


static func _disc_outline(img: Image, cx: float, cy: float, r: float, w: float, c: Color) -> void:
	if c.a <= 0.0:
		return
	var steps := int(TAU * r / 1.6) + 8
	for i in steps:
		var ang := TAU * float(i) / float(steps)
		_disc(img, cx + cos(ang) * r, cy + sin(ang) * r, w * 0.5, c)


static func _flower(img: Image, cx: float, cy: float, r: float, rng: RandomNumberGenerator, strength: float) -> void:
	var petal := Color(0.66, 0.28, 0.33, 0.9 * strength)
	var petal2 := Color(0.32, 0.42, 0.62, 0.75 * strength)
	var n := 5
	for i in n:
		var ang := TAU * float(i) / float(n) + rng.randf_range(-0.2, 0.2)
		var d := r * 0.55
		_disc(img, cx + cos(ang) * d, cy + sin(ang) * d, r * 0.44, petal if i % 2 == 0 else petal2)
	# 花瓣上的重色描边，远看才有"花"的轮廓
	_disc_outline(img, cx, cy, r * 0.62, maxf(1.0, r * 0.10), Color(0.52, 0.22, 0.26, 0.45 * strength))
	_disc(img, cx, cy, r * 0.24, Color(0.85, 0.70, 0.30, 0.95 * strength))
	# 叶子
	_disc(img, cx + r * 0.9, cy + r * 0.7, r * 0.26, Color(0.34, 0.44, 0.32, 0.72 * strength))
	_disc(img, cx - r * 0.85, cy - r * 0.6, r * 0.20, Color(0.36, 0.47, 0.34, 0.6 * strength))


static func _img_cup(base: Color, floral: bool) -> Image:
	var size := CUP_SIZE
	var img := _img_new(size, base)
	var rng := RandomNumberGenerator.new()
	rng.seed = 771 if floral else 553
	for i in 380:
		var x := rng.randf() * size
		var y := rng.randf() * size
		_disc(img, x, y, rng.randf_range(0.6, 1.6), Color(0.62, 0.52, 0.40, rng.randf_range(0.04, 0.14)))
	if floral:
		# 杯身中段的花带（柱面 UV：v 为高度）
		for i in 16:
			var x := (float(i) / 16.0) * size + rng.randf_range(-4, 4)
			var y := size * 0.46 + rng.randf_range(-8, 8)
			_flower(img, x, y, rng.randf_range(7.0, 11.0), rng, 1.0)
		for i in 2:
			var y := size * (0.40 + 0.12 * float(i))
			_line(img, Vector2(0, y), Vector2(size, y), Color(0.76, 0.62, 0.28, 0.55), 1.4)
	# 杯口内壁的阴影带
	_line(img, Vector2(0, 2), Vector2(size, 2), Color(0.55, 0.47, 0.36, 0.20), 5.0)
	return img


static func _img_tin() -> Image:
	var size := TIN_SIZE
	var img := _img_new(size, Color("#b3b2a7"))
	var rng := RandomNumberGenerator.new()
	rng.seed = 1924
	# 锤纹：一圈圈浅浅的凹面
	for i in 300:
		var x := rng.randf() * size
		var y := rng.randf() * size
		var r := rng.randf_range(4.0, 11.0)
		_disc(img, x, y, r, Color(0.60, 0.61, 0.57, 0.22) if i % 2 == 0 else Color(0.76, 0.76, 0.71, 0.24))
		_disc_outline(img, x, y, r, 1.2, Color(0.44, 0.45, 0.41, 0.30))
	# 竖向拉丝
	for i in 90:
		var x := rng.randf() * size
		_line(img, Vector2(x, 0), Vector2(x + rng.randf_range(-3, 3), size), Color(1, 1, 1, 0.05), 1.0)
	# 上下暗角：锡杯口与杯底积灰
	for i in 6:
		_line(img, Vector2(0, size * (0.03 + 0.015 * float(i))), Vector2(size, size * (0.03 + 0.015 * float(i))), Color(0.42, 0.43, 0.40, 0.10), 5.0)
		_line(img, Vector2(0, size * (0.97 - 0.015 * float(i))), Vector2(size, size * (0.97 - 0.015 * float(i))), Color(0.42, 0.43, 0.40, 0.10), 5.0)
	return img


static func _img_cloth(base: Color, mono: String, stain: float) -> Image:
	var size := CLOTH_SIZE
	var img := _img_new(size, base)
	var rng := RandomNumberGenerator.new()
	rng.seed = 31 + (mono.unicode_at(0) if mono != "" else 7)
	# 经纬：横竖细线
	for y in range(0, size, 3):
		_line(img, Vector2(0, y), Vector2(size, y), Color(1, 1, 1, 0.05), 0.9)
	for x in range(0, size, 3):
		_line(img, Vector2(x, 0), Vector2(x, size), Color(0.55, 0.50, 0.42, 0.045), 0.9)
	# 纤维噪点
	for i in 900:
		var x := rng.randf() * size
		var y := rng.randf() * size
		_disc(img, x, y, rng.randf_range(0.5, 1.3), Color(0.62, 0.56, 0.46, rng.randf_range(0.03, 0.10)))
	if stain > 0.0:
		for i in 7:
			_disc(img, rng.randf() * size, rng.randf() * size, rng.randf_range(10, 26), Color(0.60, 0.48, 0.28, stain * 0.18))
	# 折痕
	_line(img, Vector2(0, size * 0.34), Vector2(size, size * 0.30), Color(0.62, 0.56, 0.46, 0.16), 1.6)
	_line(img, Vector2(size * 0.52, 0), Vector2(size * 0.48, size), Color(0.62, 0.56, 0.46, 0.14), 1.6)
	# 餐巾四周的锁边线，让织物感更明确
	var edge := Color(0.55, 0.48, 0.38, 0.35)
	_line(img, Vector2(10, 10), Vector2(size - 10, 10), edge, 1.4, true)
	_line(img, Vector2(size - 10, 10), Vector2(size - 10, size - 10), edge, 1.4, true)
	_line(img, Vector2(size - 10, size - 10), Vector2(10, size - 10), edge, 1.4, true)
	_line(img, Vector2(10, size - 10), Vector2(10, 10), edge, 1.4, true)
	if mono != "":
		_stitch_monogram(img, mono, Vector2(size * 0.80, size * 0.78), size * 0.26)
	return img


static func _stitch_monogram(img: Image, letter: String, at: Vector2, h: float) -> void:
	# 线绣：够粗才在近景里读得出来（h 约 66px，线宽按字高比例给）
	var thread := Color(0.44, 0.16, 0.13)
	var shadow := Color(0.30, 0.20, 0.16, 0.35)
	var w := maxf(2.6, h * 0.085)
	var top := at.y - h * 0.5
	var bot := at.y + h * 0.5
	if letter == "L":
		_line(img, Vector2(at.x + w * 0.5, top + w * 0.5), Vector2(at.x + w * 0.5, bot + w * 0.5), shadow, w, false)
		_line(img, Vector2(at.x, top), Vector2(at.x, bot), thread, w, false)
		_line(img, Vector2(at.x - w * 0.4, bot), Vector2(at.x + h * 0.46, bot), thread, w, false)
	elif letter == "I":
		_line(img, Vector2(at.x + w * 0.5, top + w * 0.5), Vector2(at.x + w * 0.5, bot + w * 0.5), shadow, w, false)
		_line(img, Vector2(at.x, top), Vector2(at.x, bot), thread, w, false)
		_line(img, Vector2(at.x - h * 0.22, top), Vector2(at.x + h * 0.22, top), thread, w, false)
		_line(img, Vector2(at.x - h * 0.22, bot), Vector2(at.x + h * 0.22, bot), thread, w, false)
	_disc(img, at.x + h * 0.46, bot - w * 0.7, w * 0.85, thread)


static func _img_paper() -> Image:
	var size := PAPER_SIZE
	var img := _img_new(size, Color("#e9dcc2"))
	var rng := RandomNumberGenerator.new()
	rng.seed = 1921
	# 纤维与斑点
	for i in 1200:
		var x := rng.randf() * size
		var y := rng.randf() * size
		_disc(img, x, y, rng.randf_range(0.5, 1.5), Color(0.52, 0.42, 0.28, rng.randf_range(0.02, 0.10)))
	# 四边压暗
	for i in 8:
		_line(img, Vector2(0, size * (0.02 + 0.006 * float(i))), Vector2(size, size * (0.02 + 0.006 * float(i))), Color(0.55, 0.42, 0.24, 0.05), 4.0)
		_line(img, Vector2(0, size * (0.98 - 0.006 * float(i))), Vector2(size, size * (0.98 - 0.006 * float(i))), Color(0.55, 0.42, 0.24, 0.05), 4.0)
	# 手写字迹：几行长短不一的墨线 + 一处划掉
	var ink := Color(0.24, 0.20, 0.17, 0.75)
	for row in 3:
		var y := size * (0.26 + 0.16 * float(row))
		var x := size * 0.14
		var x_end := size * rng.randf_range(0.55, 0.86)
		while x < x_end:
			var seg := rng.randf_range(6.0, 16.0)
			var yj := y + rng.randf_range(-1.6, 1.6)
			_line(img, Vector2(x, yj), Vector2(minf(x + seg, x_end), y + rng.randf_range(-1.6, 1.6)), ink, 1.5)
			x += seg + rng.randf_range(3.0, 6.0)
	# 抬头一行更粗（像名字）
	_line(img, Vector2(size * 0.16, size * 0.16), Vector2(size * 0.62, size * 0.155), Color(0.20, 0.16, 0.13, 0.85), 2.6)
	# 划掉的一道
	_line(img, Vector2(size * 0.15, size * 0.60), Vector2(size * 0.72, size * 0.575), Color(0.38, 0.15, 0.12, 0.8), 2.2)
	return img

# ─────────────────────────── 公用件（图纸中间那组） ───────────────────────────

static func build_shared(id: String) -> Node3D:
	var root := Node3D.new()
	root.name = "item_" + id
	root.set_meta("item_id", id)
	match id:
		"toast_rack":
			_toast_rack(root)
		"fruit_bowl":
			_fruit_bowl(root)
		"sugar_bowl":
			_sugar_bowl(root)
		"small_bowl":
			_small_bowl(root)
		"teapot":
			_teapot(root)
	return root


static func _ceramic() -> StandardMaterial3D:
	return _mat_color(Color("#efe6d6"), 0.48, 0.0)


static func _mat_tex(tex: Texture2D, rough := 0.45, metal := 0.0) -> StandardMaterial3D:
	var m := StandardMaterial3D.new()
	m.albedo_texture = tex
	m.roughness = rough
	m.metallic = metal
	return m


static func _gold() -> StandardMaterial3D:
	return _mat_color(Color("#c9a24b"), 0.28, 0.78)


static func _silver() -> StandardMaterial3D:
	return _mat_color(Color("#b9b3a6"), 0.30, 0.70)


static func _rim(parent: Node3D, radius: float, y: float, thickness: float, mat: Material) -> MeshInstance3D:
	var t := TorusMesh.new()
	t.inner_radius = maxf(radius - thickness, 0.001)
	t.outer_radius = radius
	t.rings = 40
	t.ring_segments = 8
	var mi := _add_mesh(parent, t, mat, Vector3(0, y, 0))
	return mi


static func _band(parent: Node3D, radius: float, y: float, height: float, mat: Material) -> MeshInstance3D:
	var c := CylinderMesh.new()
	c.top_radius = radius
	c.bottom_radius = radius
	c.height = height
	c.cap_top = false
	c.cap_bottom = false
	return _add_mesh(parent, c, mat, Vector3(0, y, 0))


# ── 烤面包架 ──

static func _toast_rack(root: Node3D) -> void:
	var silver := _silver()
	# 底座
	var base := BoxMesh.new()
	base.size = Vector3(0.160, 0.010, 0.085)
	_add_mesh(root, base, silver, Vector3(0, 0.005, 0))
	# 四只脚
	for sx in [-1.0, 1.0]:
		for sz in [-1.0, 1.0]:
			var foot := SphereMesh.new()
			foot.radius = 0.007
			foot.height = 0.012
			_add_mesh(root, foot, silver, Vector3(sx * 0.066, 0.006, sz * 0.030))
	# 四道拱：半个环埋在底座里
	for i in 4:
		var arch := TorusMesh.new()
		arch.inner_radius = 0.026
		arch.outer_radius = 0.030
		arch.rings = 28
		arch.ring_segments = 7
		var mi := _add_mesh(root, arch, silver, Vector3(-0.060 + i * 0.040, 0.030, 0))
		mi.rotation.x = deg_to_rad(90)
	# 端头的小提手
	var handle := TorusMesh.new()
	handle.inner_radius = 0.014
	handle.outer_radius = 0.018
	handle.rings = 20
	handle.ring_segments = 6
	var hm := _add_mesh(root, handle, silver, Vector3(0.086, 0.030, 0))
	hm.rotation.x = deg_to_rad(90)
	# 两片吐司：深色面包皮 + 浅色内芯
	var crust := _mat_color(Color("#8a4f28"), 0.82, 0.0)
	var crumb := _mat_color(Color("#d8b07a"), 0.88, 0.0)
	var outline := PackedVector2Array([
		Vector2(-0.024, -0.028), Vector2(0.024, -0.028), Vector2(0.028, -0.023),
		Vector2(0.028, 0.018), Vector2(0.020, 0.030), Vector2(-0.020, 0.030),
		Vector2(-0.028, 0.018), Vector2(-0.028, -0.023),
	])
	var inner := PackedVector2Array([
		Vector2(-0.020, -0.024), Vector2(0.020, -0.024), Vector2(0.023, -0.019),
		Vector2(0.023, 0.015), Vector2(0.016, 0.025), Vector2(-0.016, 0.025),
		Vector2(-0.023, 0.015), Vector2(-0.023, -0.019),
	])
	for k in 2:
		var angle := deg_to_rad(10.0 - k * 20.0)
		var slot := _add_mesh(root, _extrude(outline, 0.010), crust, Vector3(-0.030 + k * 0.060, 0.062, 0))
		slot.rotation.x = deg_to_rad(90)
		slot.rotation.z = angle
		var face := _add_mesh(root, _extrude(inner, 0.002), crumb, Vector3(-0.030 + k * 0.060, 0.062, 0.006))
		face.rotation.x = deg_to_rad(90)
		face.rotation.z = angle


# ── 碗 ──

static func _bowl(root: Node3D, r: float, h: float, mat: StandardMaterial3D, rim_mat: Material = null, band_mat: Material = null) -> void:
	var prof := _ccw(PackedVector2Array([
		Vector2(0.0, 0.0), Vector2(r * 0.46, 0.0), Vector2(r * 0.52, h * 0.10),
		Vector2(r * 0.72, h * 0.22), Vector2(r * 0.94, h * 0.50),
		Vector2(r, h * 0.78), Vector2(r * 0.97, h), Vector2(r * 0.92, h),
		Vector2(r * 0.88, h * 0.78), Vector2(r * 0.80, h * 0.50),
		Vector2(r * 0.58, h * 0.28), Vector2(0.0, h * 0.20),
	]))
	_add_mesh(root, _lathe(prof, 40, "flat", r), mat, Vector3.ZERO)
	if band_mat != null:
		_band(root, r * 0.96, h * 0.55, h * 0.22, band_mat)
	if rim_mat != null:
		_rim(root, r * 0.965, h, maxf(r * 0.018, 0.0016), rim_mat)


static func _fruit_bowl(root: Node3D) -> void:
	_bowl(root, 0.090, 0.052, _ceramic(), _gold())
	# 五种水果：苹果、橙、梨、柠檬、李子；带梗和叶
	var spec := [
		{"c": Color("#a63b35"), "r": 0.021, "s": Vector3(1, 0.92, 1), "pos": Vector3(-0.032, 0.064, -0.012)},
		{"c": Color("#d98a2b"), "r": 0.019, "s": Vector3(1, 1, 1), "pos": Vector3(0.030, 0.062, -0.014)},
		{"c": Color("#b8b24a"), "r": 0.018, "s": Vector3(0.92, 1.18, 0.92), "pos": Vector3(-0.006, 0.070, 0.026)},
		{"c": Color("#d9c24a"), "r": 0.015, "s": Vector3(1.25, 0.82, 0.82), "pos": Vector3(0.036, 0.058, 0.026)},
		{"c": Color("#6b3f63"), "r": 0.014, "s": Vector3(1, 1, 1), "pos": Vector3(-0.040, 0.056, 0.030)},
	]
	var leaf := _mat_color(Color("#4f6a35"), 0.8, 0.0)
	var stem := _mat_color(Color("#5a3a22"), 0.9, 0.0)
	for i in spec.size():
		var s: Dictionary = spec[i]
		var fruit := SphereMesh.new()
		fruit.radius = s["r"]
		fruit.height = s["r"] * 2.0
		var mi := _add_mesh(root, fruit, _mat_color(s["c"], 0.55, 0.0), s["pos"])
		mi.scale = s["s"]
		# 梗
		var st := CylinderMesh.new()
		st.top_radius = 0.0012
		st.bottom_radius = 0.0016
		st.height = 0.012
		_add_mesh(root, st, stem, s["pos"] + Vector3(0, s["r"] * 0.95, 0))
		# 叶
		var lf := SphereMesh.new()
		lf.radius = 0.007
		lf.height = 0.002
		var lm := _add_mesh(root, lf, leaf, s["pos"] + Vector3(0.006, s["r"] * 1.05, 0))
		lm.scale = Vector3(1.0, 0.25, 0.55)
		lm.rotation.y = deg_to_rad(20.0 + i * 37.0)


# ── 糖罐 ──

static func _sugar_bowl(root: Node3D) -> void:
	var floral := _mat_tex(_tex("cup_floral"), 0.42, 0.0)
	_bowl(root, 0.054, 0.056, _ceramic(), _gold(), floral)
	# 穹顶盖
	var lid_prof := _ccw(PackedVector2Array([
		Vector2(0.0, 0.0), Vector2(0.052, 0.0), Vector2(0.050, 0.008),
		Vector2(0.040, 0.018), Vector2(0.024, 0.026), Vector2(0.0, 0.030),
	]))
	var lid := _add_mesh(root, _lathe(lid_prof, 36, "flat", 0.052), _ceramic(), Vector3(0, 0.056, 0))
	_rim(root, 0.052, 0.058, 0.0018, _gold())
	var knob := SphereMesh.new()
	knob.radius = 0.009
	knob.height = 0.014
	_add_mesh(root, knob, _gold(), Vector3(0, 0.090, 0))
	# 两只环形把手
	for sgn in [-1.0, 1.0]:
		var h := TorusMesh.new()
		h.inner_radius = 0.010
		h.outer_radius = 0.015
		h.rings = 20
		h.ring_segments = 6
		var mi := _add_mesh(root, h, _ceramic(), Vector3(sgn * 0.055, 0.032, 0))
		mi.rotation.y = deg_to_rad(90)
	# 一把小银勺搭在盖边
	var spoon_h := CylinderMesh.new()
	spoon_h.top_radius = 0.0012
	spoon_h.bottom_radius = 0.0016
	spoon_h.height = 0.070
	var sh := _add_mesh(root, spoon_h, _silver(), Vector3(0.030, 0.071, 0.026))
	sh.rotation.z = deg_to_rad(46)
	sh.rotation.x = deg_to_rad(14)
	var spoon_b := SphereMesh.new()
	spoon_b.radius = 0.010
	spoon_b.height = 0.006
	var sb := _add_mesh(root, spoon_b, _silver(), Vector3(0.055, 0.047, 0.030))
	sb.scale = Vector3(1.0, 0.35, 0.75)


# ── 小碗 ──

static func _small_bowl(root: Node3D) -> void:
	_bowl(root, 0.062, 0.040, _ceramic(), _mat_color(Color("#2f4f8f"), 0.40, 0.15))


# ── 茶壶 ──

static func _teapot(root: Node3D) -> void:
	var mat := _ceramic()
	var cobalt := _mat_color(Color("#2f4f8f"), 0.38, 0.18)
	# 壶身：外撇的圈足、饱满的肩、收颈
	var body_prof := _ccw(PackedVector2Array([
		Vector2(0.0, 0.0), Vector2(0.046, 0.0), Vector2(0.052, 0.008),
		Vector2(0.044, 0.020), Vector2(0.052, 0.028), Vector2(0.070, 0.048),
		Vector2(0.076, 0.068), Vector2(0.068, 0.088), Vector2(0.052, 0.101),
		Vector2(0.041, 0.107), Vector2(0.045, 0.112), Vector2(0.038, 0.114),
		Vector2(0.0, 0.114),
	]))
	_add_mesh(root, _lathe(body_prof, 44, "flat", 0.076), mat, Vector3.ZERO)
	# 圈足金边
	_rim(root, 0.049, 0.006, 0.0022, _gold())
	# 壶身中段的青花花带
	_band(root, 0.0772, 0.062, 0.022, _mat_tex(_tex("cup_floral"), 0.42, 0.0))
	# 颈口金边
	_rim(root, 0.043, 0.112, 0.0022, _gold())
	# 盖子
	var lid_prof := _ccw(PackedVector2Array([
		Vector2(0.0, 0.0), Vector2(0.050, 0.0), Vector2(0.047, 0.008),
		Vector2(0.035, 0.016), Vector2(0.018, 0.021), Vector2(0.0, 0.023),
	]))
	_add_mesh(root, _lathe(lid_prof, 36, "flat", 0.050), mat, Vector3(0, 0.114, 0))
	_rim(root, 0.050, 0.116, 0.0018, _gold())
	# 盖钮：小金珠 + 小盘
	var knob_base := CylinderMesh.new()
	knob_base.top_radius = 0.012
	knob_base.bottom_radius = 0.014
	knob_base.height = 0.004
	_add_mesh(root, knob_base, _gold(), Vector3(0, 0.139, 0))
	var knob := SphereMesh.new()
	knob.radius = 0.010
	knob.height = 0.018
	_add_mesh(root, knob, _gold(), Vector3(0, 0.147, 0))
	# 弯曲壶嘴：三段渐细的管 + 金口
	var spout_spec := [
		{"pos": Vector3(0.072, 0.060, 0), "rot": -22.0, "h": 0.040, "r0": 0.017, "r1": 0.014},
		{"pos": Vector3(0.094, 0.082, 0), "rot": -48.0, "h": 0.038, "r0": 0.013, "r1": 0.011},
		{"pos": Vector3(0.110, 0.104, 0), "rot": -72.0, "h": 0.034, "r0": 0.010, "r1": 0.008},
	]
	for s in spout_spec:
		var pipe := CylinderMesh.new()
		pipe.top_radius = s["r1"]
		pipe.bottom_radius = s["r0"]
		pipe.height = s["h"]
		var pm := _add_mesh(root, pipe, mat, s["pos"])
		pm.rotation.z = deg_to_rad(s["rot"])
	var lip := TorusMesh.new()
	lip.inner_radius = 0.006
	lip.outer_radius = 0.009
	lip.rings = 16
	lip.ring_segments = 6
	var lm := _add_mesh(root, lip, _gold(), Vector3(0.124, 0.120, 0))
	lm.rotation.z = deg_to_rad(-72)
	# C 形把手
	var handle := TorusMesh.new()
	handle.inner_radius = 0.024
	handle.outer_radius = 0.031
	handle.rings = 28
	handle.ring_segments = 8
	var hm := _add_mesh(root, handle, mat, Vector3(-0.078, 0.062, 0))
	hm.rotation.y = deg_to_rad(90)
	# 把手上的一点金饰
	var hg := SphereMesh.new()
	hg.radius = 0.006
	hg.height = 0.010
	_add_mesh(root, hg, _gold(), Vector3(-0.108, 0.075, 0))