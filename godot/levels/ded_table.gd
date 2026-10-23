extends Node3D
## 餐桌复原关卡（第一人称）：在餐厅里走动，从餐边柜拿起餐具，摆到桌上的五个位置，摇铃确认。
## 空间与光照来自 ded_table.tscn；餐具造型与贴图由 ded_table_props.gd 提供（车削网格 + 引擎内程序化贴图）。
## 由镜头表的 level(ded_table) 进入时接管主流程的玩家；单独运行时自己建一个玩家。

const PROPS := preload("res://levels/ded_table_props.gd")
const PlayerScene := preload("res://world/player.gd")

## 关卡结束：收起成功卡后发出，scene_host.enter_level 等这个信号收场
signal finished

## scene_host.enter_level 在把玩家收起来之前会读这个：这一关要自己用玩家走动
var takes_over_player := true

const ITEM_ORDER := [
	"ambrose", "constance", "iris", "gideon", "lucien",
	"decoy_guest", "decoy_plate", "decoy_cup", "decoy_napkin_i", "decoy_card_penrose",
]
const CORRECT := {
	"slot_north": "ambrose",
	"slot_east_1": "constance",
	"slot_east_2": "iris",
	"slot_west": "gideon",
	"slot_south": "lucien",
	"slot_toast": "toast_rack",
	"slot_fruit": "fruit_bowl",
	"slot_sugar": "sugar_bowl",
	"slot_small": "small_bowl",
}
const SLOT_LABELS := {
	"slot_north": "北端",
	"slot_east_1": "东一",
	"slot_east_2": "东二",
	"slot_west": "西侧",
	"slot_south": "南端",
	"slot_toast": "烤面包架",
	"slot_fruit": "水果盘",
	"slot_sugar": "糖罐",
	"slot_small": "小碗",
}
const ITEM_LABELS := {
	"ambrose": "蓝边大盘",
	"constance": "金边盘",
	"iris": "碎花小盘",
	"gideon": "棕边厚盘",
	"lucien": "南端那副旧餐具",
	"toast_rack": "烤面包架",
	"fruit_bowl": "水果盘",
	"sugar_bowl": "糖罐",
	"small_bowl": "小碗",
	"decoy_guest": "客人备用套",
	"decoy_plate": "普通小盘",
	"decoy_cup": "错锡杯",
	"decoy_napkin_i": "绣 I. 的餐巾",
	"decoy_card_penrose": "彭罗斯旧卡",
}
const SHARED := ["toast_rack", "fruit_bowl", "sugar_bowl", "small_bowl"]
## 检查顺序：先五套，再四件公用件
const CHECK_ORDER := [
	"slot_north", "slot_east_1", "slot_east_2", "slot_west", "slot_south",
	"slot_toast", "slot_fruit", "slot_sugar", "slot_small",
]
## 给格雷的独白用：南端不出现“卢西恩”这个名字
const SLOT_OWNER := {
	"slot_north": "安布罗斯",
	"slot_east_1": "康斯坦斯",
	"slot_east_2": "艾瑞斯",
	"slot_west": "吉迪恩",
	"slot_south": "南端那副旧餐具",
}
const SLOT_POS := {
	"slot_north": Vector3(15.75, 0.79, -3.73),
	"slot_east_1": Vector3(16.05, 0.79, -2.55),
	"slot_east_2": Vector3(16.05, 0.79, -3.20),
	"slot_west": Vector3(15.45, 0.79, -2.55),
	"slot_south": Vector3(15.75, 0.79, -1.45),
	"slot_toast": Vector3(15.75, 0.79, -2.95),
	"slot_fruit": Vector3(15.75, 0.79, -2.69),
	"slot_sugar": Vector3(15.75, 0.79, -2.43),
	"slot_small": Vector3(15.75, 0.79, -2.17),
}
## 每个槽位坐的人面朝哪儿：默认餐具朝 -Z，东侧座椅转 -90°（朝 +X 的桌心），西侧 +90°。
const SLOT_FACING := {
	"slot_north": 0.0,
	"slot_east_1": -90.0,
	"slot_east_2": -90.0,
	"slot_west": 90.0,
	"slot_south": 180.0,
	"slot_toast": 0.0,
	"slot_fruit": 0.0,
	"slot_sugar": 0.0,
	"slot_small": 0.0,
}
## 柜内陈列时缩小一点，免得十套东西在层板上互相压住。
const CABINET_SCALE := 0.78
## 只能翻看、不能摆上桌的物品。
const READ_ONLY := ["decoy_card_penrose"]
## 准星能碰到东西的距离（米）
const REACH := 2.6
const MEMORY := preload("res://levels/ded_table_memory.gd")

var items := {}
var item_home := {}
var item_areas := {}
var slot_nodes := {}
var slot_rings := {}
var slot_items := {}
var drawer_root: Node3D
var drawer_paper: Node3D
var drawer_paper_area: Area3D
var drawer_open := false
var drawer_moving := false
var _plan_viewer: CanvasLayer
var diagram_taken := false
var table_body: StaticBody3D

var player
var player_own := false

var hover := {}
var held := ""
var fail_count := 0
var solved := false
var blueprint_open := false
var _finished := false
var cancelled := false

var table_bell: Node3D
var bell_fx: Node3D
var bell_seq := false
var chat_open := false
var _last_wrong_sig := ""
var _idle_seconds := 0.0
var _idle_hint_shown := false


func _ready() -> void:
	_hide_existing_dining_parts()
	_build_open_sideboard()
	_build_table_body()
	_build_items()
	_build_slots()
	_build_bell()
	_build_ui()
	if DisplayServer.get_name() != "headless":
		_setup_player()


func _process(dt: float) -> void:
	if player == null or player.frozen or solved or blueprint_open or chat_open or bell_seq:
		return
	_update_hover()
	_update_ring_visibility()
	# 八个位置摆满、手里没东西、又没在操作：只提示“还空一个”，不判断对错
	if slot_items.size() == CORRECT.size() - 1 and held == "":
		_idle_seconds += dt
		if _idle_seconds >= 5.0 and not _idle_hint_shown:
			_idle_hint_shown = true
			_status("桌上还空着一个位置。")
	else:
		_idle_seconds = 0.0
		_idle_hint_shown = false


# ───────────── 玩家 ─────────────

## 主线里复用主流程的玩家（SceneHost.player），单独运行时自己建一个；两种都走第一人称。
func _setup_player() -> void:
	var host = Director.world.player if Director.world else null
	if host and is_instance_valid(host) and host.is_inside_tree():
		player = host
	else:
		player = PlayerScene.new()
		add_child(player)
		player_own = true
	var pcam = player.get("cam")
	if Director.world:
		Director.world.highlight_hotspots([])
	var sp := _find_node(self, "spawn")
	var pos := Vector3(14.7, 0.02, -4.15)
	var yaw := 180.0
	if sp is Node3D:
		pos = sp.global_position
		yaw = sp.global_rotation_degrees.y
	player.place(pos, yaw)
	player.frozen = false
	player.activate()


func _teardown_player() -> void:
	# 手上有餐具 / 镜头前的图纸都是玩家的孩子，收场前先收回关卡，免得跟着宿主玩家进下一关
	if held != "":
		_return_item(held)
	if player == null:
		return
	player.frozen = true
	var pcam = player.get("cam")
	player.deactivate()


# ───────────── 现有餐厅里补出的开放柜 ─────────────

func _hide_existing_dining_parts() -> void:
	# 原有餐边柜是闭合的一整块网格；本关用自己搭的开放柜替换。
	# 两条餐桌状态层也会被隐藏，保证复原桌是空的。
	# 注意：隐藏网格不会关掉它挂着的 StaticBody3D（闭合柜门仍会挡住射线与走动），要一并静音。
	for n in _all_nodes(self):
		var nm := String(n.name)
		if nm.begins_with("层·") or nm.contains("餐边柜") or nm.contains("桌上烛台") or nm.contains("桌花"):
			n.visible = false
			_mute_collision(n)


## 把节点及其子节点里的碰撞体从世界碰撞里拿掉（原有餐边柜的实体碰撞）
func _mute_collision(n: Node) -> void:
	if n is CollisionObject3D:
		n.collision_layer = 0
		n.collision_mask = 0
	for c in n.get_children():
		_mute_collision(c)


func _all_nodes(root: Node) -> Array:
	var out: Array = [root]
	for c in root.get_children():
		out.append_array(_all_nodes(c))
	return out


func _find_node(root: Node, target: String) -> Node:
	if String(root.name) == target:
		return root
	for c in root.get_children():
		var r := _find_node(c, target)
		if r != null:
			return r
	return null


func _build_open_sideboard() -> void:
	var root := Node3D.new()
	root.name = "ded_open_sideboard"
	add_child(root)
	var wood := Color("#4b2f20")
	var edge := Color("#2f1c12")
	var shelf := Color("#68462e")

	# 柜体：背面、顶底、两侧，正面留空；坐标沿用餐厅西墙餐边柜位置。
	_box(root, "柜背", Vector3(12.68, 0.46, -1.11), Vector3(0.035, 0.90, 1.24), edge)
	_box(root, "柜底", Vector3(12.92, 0.035, -1.11), Vector3(0.55, 0.05, 1.24), wood)
	_box(root, "柜顶", Vector3(12.92, 0.90, -1.11), Vector3(0.55, 0.05, 1.24), wood)
	_box(root, "柜左侧", Vector3(12.92, 0.46, -1.72), Vector3(0.55, 0.90, 0.035), wood)
	_box(root, "柜右侧", Vector3(12.92, 0.46, -0.50), Vector3(0.55, 0.90, 0.035), wood)
	for y in [0.25, 0.55]:
		_box(root, "柜层板", Vector3(12.92, y, -1.11), Vector3(0.50, 0.024, 1.16), shelf)

	# 上部浅抽屉嵌入柜体，下部开放层架；门铰在柜体前沿两端。
	for spec in [["左", -1.70, 1.0], ["右", -0.52, -1.0]]:
		var hinge := Node3D.new()
		hinge.position = Vector3(13.195, 0.37, spec[1])
		hinge.rotation.y = deg_to_rad(100.0 * spec[2])
		root.add_child(hinge)
		_box(hinge, "柜门" + spec[0], Vector3(0, 0, 0.285 * spec[2]), Vector3(0.03, 0.60, 0.57), wood)
	_box(root, "抽屉下隔板", Vector3(12.92, 0.68, -1.11), Vector3(0.50, 0.024, 1.16), shelf)
	for z in [-1.66, -0.56]:
		_box(root, "木滑轨", Vector3(12.96, 0.73, z), Vector3(0.43, 0.025, 0.025), shelf)
	# 面板闭合时贴合柜体前沿，打开 30cm，抽屉后部仍留在滑轨上。
	drawer_root = Node3D.new()
	drawer_root.name = "餐边柜抽屉"
	drawer_root.position = Vector3(13.20, 0.78, -1.11)
	root.add_child(drawer_root)
	_box(drawer_root, "抽屉底", Vector3(-0.21, -0.065, 0), Vector3(0.42, 0.018, 1.08), shelf)
	_box(drawer_root, "抽屉面板", Vector3.ZERO, Vector3(0.035, 0.18, 1.14), wood)
	for z in [-0.53, 0.53]:
		_box(drawer_root, "抽屉侧板", Vector3(-0.21, -0.015, z), Vector3(0.42, 0.11, 0.02), wood)
	_box(drawer_root, "抽屉后板", Vector3(-0.41, -0.015, 0), Vector3(0.02, 0.11, 1.08), wood)
	_box(drawer_root, "黄铜拉手", Vector3(0.05, 0, 0), Vector3(0.035, 0.025, 0.14), Color("#c39a52"), 0.6, 0.35)
	_hit_area(drawer_root, "drawer", true, Vector3(0.08, 0.18, 1.14), Vector3(0.035, 0, 0))

	drawer_paper = Node3D.new()
	drawer_paper.name = "折起的餐桌图"
	drawer_paper.position = Vector3(-0.18, -0.048, 0.0)
	drawer_paper.rotation.y = deg_to_rad(8)
	drawer_paper.visible = false
	drawer_root.add_child(drawer_paper)
	_box(drawer_paper, "图纸", Vector3.ZERO, Vector3(0.16, 0.010, 0.11), Color("#d8c3a0"))
	var crease := _box(drawer_paper, "折痕", Vector3(0.0, 0.006, 0.0), Vector3(0.155, 0.002, 0.006), Color("#a8906c"))
	crease.rotation.y = deg_to_rad(4)
	drawer_paper_area = _hit_area(drawer_paper, "diagram", true, Vector3(0.20, 0.08, 0.16), Vector3(0, 0.01, 0))
	drawer_paper_area.collision_layer = 0
	for i in 3:
		var c := _box(root, "旧地点卡%d" % i, Vector3(13.06, 0.86, -1.55 + i * 0.11), Vector3(0.14, 0.008, 0.09), Color("#e6d2b6"))
		c.rotation.y = deg_to_rad(8 - i * 7)
	var bundle := _box(root, "包着的旧餐具", Vector3(13.10, 0.88, -0.68), Vector3(0.16, 0.07, 0.24), Color("#b7aa91"))
	bundle.rotation.x = deg_to_rad(-8)

	# 柜体后一半的碰撞：玩家可以走到柜前，但不会整个人钻进层板里
	var body := StaticBody3D.new()
	body.name = "柜体碰撞"
	body.position = Vector3(12.84, 0.45, -1.11)
	var body_cs := CollisionShape3D.new()
	var body_box := BoxShape3D.new()
	body_box.size = Vector3(0.28, 0.90, 1.24)
	body_cs.shape = body_box
	body.add_child(body_cs)
	root.add_child(body)


func _box(parent: Node3D, n: String, pos: Vector3, size: Vector3, color: Color, metallic := 0.0, rough := 0.8) -> MeshInstance3D:
	var mi := MeshInstance3D.new()
	mi.name = n
	mi.position = pos
	var bm := BoxMesh.new()
	bm.size = size
	mi.mesh = bm
	var m := StandardMaterial3D.new()
	m.albedo_color = color
	m.metallic = metallic
	m.roughness = rough
	mi.material_override = m
	parent.add_child(mi)
	return mi


## 桌体碰撞：第一人称不能穿过长桌；桌面在 0.78 米。
func _build_table_body() -> void:
	table_body = StaticBody3D.new()
	table_body.name = "桌体碰撞"
	table_body.position = Vector3(15.75, 0.39, -2.59)
	var cs := CollisionShape3D.new()
	var box := BoxShape3D.new()
	box.size = Vector3(0.82, 0.78, 2.40)
	cs.shape = box
	table_body.add_child(cs)
	add_child(table_body)


# ───────────── 五套正确餐具 + 干扰物 ─────────────

func _build_items() -> void:
	# 五套正确餐具在中层（0.562）；图纸中间的公用件在下层（0.262）；
	# 干扰物在柜顶，仍然可以翻看，但不参与判定。
	for i in 5:
		_make_item(ITEM_ORDER[i], Vector3(13.06, 0.562, -1.60 + i * 0.245))
	for i in SHARED.size():
		_make_item(SHARED[i], Vector3(13.06, 0.262, -1.40 + i * 0.22))
	for i in 5:
		_make_item(ITEM_ORDER[5 + i], Vector3(13.06, 0.93, -1.55 + i * 0.24))
	# 茶壶按图纸“固定”，开场就在桌上，不用拿
	var pot: Node3D = PROPS.build_shared("teapot")
	pot.name = "fixed_teapot"
	pot.position = Vector3(15.75, 0.79, -3.35)
	add_child(pot)


func _make_item(id: String, pos: Vector3) -> void:
	var n: Node3D
	if id in SHARED:
		n = PROPS.build_shared(id)
	else:
		n = PROPS.build_item(id)
	n.name = "item_" + id
	n.position = pos
	n.scale = Vector3.ONE * CABINET_SCALE
	# 柜内斜放 38°，玩家站在柜前能看到盘沿、杯口、餐巾上的首字母，而不是只看侧面
	n.rotation.y = deg_to_rad(-38.0)
	add_child(n)
	items[id] = n
	item_home[id] = pos
	var size := Vector3(0.22, 0.18, 0.22)
	match id:
		"decoy_card_penrose":
			size = Vector3(0.30, 0.22, 0.10)
		"toast_rack":
			size = Vector3(0.22, 0.16, 0.18)
		"fruit_bowl", "sugar_bowl":
			size = Vector3(0.20, 0.16, 0.20)
		"small_bowl":
			size = Vector3(0.16, 0.12, 0.16)
	item_areas[id] = _hit_area(n, "item_id", id, size, Vector3(0, 0.09, 0))


# ───────────── 桌面槽位与服务铃 ─────────────

func _build_slots() -> void:
	for id in SLOT_POS:
		var is_shared := String(id).begins_with("slot_") and not String(id).contains("north") and not String(id).contains("east") and not String(id).contains("west") and not String(id).contains("south")
		# 桌上的公用件槽位更小：它们沿桌子中线排得很密
		var area_size := Vector3(0.18, 0.14, 0.18) if is_shared else Vector3(0.30, 0.16, 0.30)
		var a := _hit_area(self, "slot_id", id, area_size, Vector3.ZERO)
		a.name = id
		a.position = SLOT_POS[id] + Vector3(0, 0.08, 0)
		slot_nodes[id] = a
		var ring := MeshInstance3D.new()
		var torus := TorusMesh.new()
		# 细黄铜嵌线，不是发光粗环；只在端着餐具时出现
		torus.inner_radius = 0.070 if is_shared else 0.146
		torus.outer_radius = 0.074 if is_shared else 0.152
		torus.rings = 40
		torus.ring_segments = 6
		ring.mesh = torus
		ring.position = SLOT_POS[id] + Vector3(0, 0.003, 0)
		var m := StandardMaterial3D.new()
		m.albedo_color = Color(0.58, 0.46, 0.28, 0.42)
		m.transparency = BaseMaterial3D.TRANSPARENCY_ALPHA
		m.metallic = 0.25
		m.roughness = 0.55
		m.emission_enabled = false
		m.shading_mode = BaseMaterial3D.SHADING_MODE_UNSHADED
		ring.material_override = m
		ring.cast_shadow = GeometryInstance3D.SHADOW_CASTING_SETTING_OFF
		ring.visible = false
		add_child(ring)
		slot_rings[id] = ring


func _build_bell() -> void:
	var bell: Node3D = PROPS.build_bell()
	bell.name = "bell"
	bell.position = Vector3(15.98, 0.79, -1.95)
	add_child(bell)
	table_bell = bell
	# 铃不再可交互：只有九件全对时，格雷才会自动拿起它


func _hit_area(parent: Node3D, key: String, value, size: Vector3, center: Vector3) -> Area3D:
	var a := Area3D.new()
	a.collision_layer = 1
	a.collision_mask = 0
	a.set_meta(key, value)
	var cs := CollisionShape3D.new()
	var box := BoxShape3D.new()
	box.size = size
	cs.shape = box
	cs.position = center
	a.add_child(cs)
	parent.add_child(a)
	return a


# ───────────── 准星与交互 ─────────────

func _update_hover() -> void:
	hover = {}
	var pcam = player.get("cam")
	if not (pcam is Camera3D):
		_refresh_prompt()
		return
	var cam: Camera3D = pcam
	var from := cam.global_position
	var dir := -cam.global_transform.basis.z
	var q := PhysicsRayQueryParameters3D.create(from, from + dir * REACH)
	q.collide_with_areas = true
	q.collide_with_bodies = true
	q.collision_mask = 1
	q.exclude = [player.get_rid()]
	var hit := get_world_3d().direct_space_state.intersect_ray(q)
	if not hit.is_empty():
		var c = hit.get("collider")
		if c != null:
			if c.has_meta("slot_id"):
				hover = {"kind": "slot", "id": String(c.get_meta("slot_id"))}
			elif c.has_meta("item_id"):
				hover = {"kind": "item", "id": String(c.get_meta("item_id"))}
			elif c.has_meta("drawer"):
				hover = {"kind": "drawer", "id": ""}
			elif c.has_meta("diagram"):
				hover = {"kind": "diagram", "id": ""}
	_refresh_prompt()


func _refresh_prompt() -> void:
	var text := ""
	var kind: String = hover.get("kind", "")
	var id: String = hover.get("id", "")
	if kind == "":
		text = ""
	elif held != "":
		match kind:
			"slot":
				text = ""
			"bell":
				text = ""
			"drawer", "diagram":
				text = "先放下手里的餐具"
			"item":
				text = "手上已有餐具"
	else:
		match kind:
			"item":
				if not diagram_taken:
					text = "先拉开抽屉看看那张旧餐桌图"
				elif id in READ_ONLY:
					text = "E　翻看：%s" % ITEM_LABELS[id]
				else:
					text = "E　拿起：%s" % ITEM_LABELS[id]
			"slot":
				text = ""
			"drawer":
				text = "E　关上抽屉" if drawer_open else "E　拉开抽屉"
			"diagram":
				if drawer_open and not diagram_taken:
					text = "E　拿起：1924 年餐桌图"
	_set_prompt(text)


func _set_prompt(text: String) -> void:
	var hand := "手上：%s · R 放回　" % ITEM_LABELS[held] if held != "" else ""
	Director.ui.set_hint(hand + text if text != "" or hand != "" else "")


func _update_ring_visibility() -> void:
	var show := held != "" and not solved and not chat_open and not blueprint_open and not bell_seq
	for slot in slot_rings:
		slot_rings[slot].visible = show and not slot_items.has(slot)


func _interact() -> void:
	if solved or blueprint_open or chat_open or bell_seq:
		return
	var kind: String = hover.get("kind", "")
	var id: String = hover.get("id", "")
	match kind:
		"item":
			if id in READ_ONLY:
				_status("旧地点卡：彭罗斯 · 1921 年。名字被划掉，背面只写了房号——这不是餐具。")
			else:
				_pick_up(id)
		"slot":
			if held != "":
				_place(id)
			elif slot_items.has(id):
				_pick_up(slot_items[id], true)
			else:
				_status("")
		"drawer":
			if held == "":
				_toggle_drawer()
			else:
				_status("先放下手里的餐具。")
		"diagram":
			if held == "":
				_take_diagram()
			else:
				_status("先放下手里的餐具。")
		_:
			_status("")


func _pick_up(id: String, from_slot := false) -> void:
	if id == "" or not items.has(id):
		return
	if held != "":
		_status("手上还有 %s，先摆上或按 R 放回。" % ITEM_LABELS[held])
		return
	if not diagram_taken:
		_status("先拉开餐边柜的抽屉，看看那张旧餐桌图。")
		return
	if id in READ_ONLY:
		_status("旧地点卡只能翻看，不能摆上桌。")
		return
	if from_slot:
		for slot in slot_items.keys():
			if slot_items[slot] == id:
				slot_items.erase(slot)
				slot_rings[slot].visible = true
	var n: Node3D = items[id]
	var cam = player.get("cam")
	if not (cam is Node3D):
		return
	n.reparent(cam, false)
	n.position = Vector3(0.17, -0.24, -0.42)
	n.rotation = Vector3(0, PI, 0)
	n.scale = Vector3.ONE * 0.55
	item_areas[id].collision_layer = 0
	held = id
	_update_held()
	if from_slot:
		_status("")
	else:
		_status("拿起了 %s。" % ITEM_LABELS[id])
	_after_table_changed()


func _place(slot: String) -> void:
	if held == "":
		return
	if slot_items.has(slot):
		_return_item(slot_items[slot])
	var id := held
	var n: Node3D = items[id]
	n.reparent(self, false)
	n.global_position = SLOT_POS[slot] + Vector3(0, 0.012, 0)
	n.rotation = Vector3(0, deg_to_rad(SLOT_FACING.get(slot, 0.0)), 0)
	n.scale = Vector3.ONE
	item_areas[id].collision_layer = 0
	slot_items[slot] = id
	slot_rings[slot].visible = false
	held = ""
	_update_held()
	_status("")
	_after_table_changed()


func _return_item(id: String) -> void:
	if not items.has(id):
		return
	for slot in slot_items.keys():
		if slot_items[slot] == id:
			slot_items.erase(slot)
			slot_rings[slot].visible = true
	var n: Node3D = items[id]
	n.reparent(self, false)
	n.visible = true
	n.global_position = item_home[id]
	n.rotation = Vector3(0, deg_to_rad(-38.0), 0)
	n.scale = Vector3.ONE * CABINET_SCALE
	item_areas[id].collision_layer = 1
	if held == id:
		held = ""
		_update_held()


func _return_all() -> void:
	for id in slot_items.values().duplicate():
		_return_item(id)
	if held != "":
		_return_item(held)
	for slot in slot_rings:
		slot_rings[slot].visible = true


func _return_held() -> void:
	if held == "":
		return
	var id := held
	_return_item(id)
	_status("放回柜子。")
	_after_table_changed()


func _toggle_drawer() -> void:
	if drawer_moving: return
	drawer_moving = true
	drawer_open = not drawer_open
	drawer_paper_area.collision_layer = 0
	if not diagram_taken: drawer_paper.visible = true
	var target := 13.50 if drawer_open else 13.20
	var tw := create_tween().set_trans(Tween.TRANS_SINE).set_ease(Tween.EASE_IN_OUT)
	tw.tween_property(drawer_root, "position:x", target, 0.45)
	await tw.finished
	drawer_moving = false
	if not diagram_taken:
		drawer_paper.visible = drawer_open
		drawer_paper_area.collision_layer = 1 if drawer_open else 0
	if drawer_open and not diagram_taken:
		_status("抽屉里有张旧图。对准纸张按 E 拿起；拿到后按 P 可随时重看。")
	else:
		_status("抽屉空了。" if diagram_taken else "把抽屉推回去了。")


func _take_diagram() -> void:
	if diagram_taken or not drawer_open or drawer_moving:
		return
	diagram_taken = true
	drawer_paper.visible = false
	drawer_paper_area.collision_layer = 0
	Director.ui.set_objective("按旧图复原餐桌 · P 查看图纸 · R 放回物件")
	_status("按图复原餐桌。P 随时重看；打开后滚轮放大、拖动查看，Esc 收起。")
	_open_blueprint()


func _after_table_changed() -> void:
	if solved or chat_open or bell_seq or blueprint_open or held != "":
		return
	if slot_items.size() < CORRECT.size():
		_idle_seconds = 0.0
		_idle_hint_shown = false
		return
	var wrong := _first_wrong()
	if wrong.is_empty():
		_start_bell_sequence()
		return
	var sig := _table_signature()
	if sig == _last_wrong_sig:
		return
	_last_wrong_sig = sig
	_show_chat(_wrong_chat_text(wrong))


func _first_wrong() -> Dictionary:
	for slot in CHECK_ORDER:
		if String(slot_items.get(slot, "")) != String(CORRECT[slot]):
			return {"slot": slot, "got": String(slot_items.get(slot, ""))}
	return {}


func _table_signature() -> String:
	var parts := PackedStringArray()
	for slot in CHECK_ORDER:
		parts.append(slot + "=" + String(slot_items.get(slot, "")))
	return "|".join(parts)


func _chat_item_label(id: String) -> String:
	match id:
		"ambrose":
			return "安布罗斯的玻璃杯"
		"constance":
			return "康斯坦斯的金边茶杯"
		"iris":
			return "艾瑞斯的碎花小盘"
		"gideon":
			return "吉迪恩的锡杯"
		"lucien":
			return "南端那副旧餐具"
		"toast_rack":
			return "烤面包架"
		"fruit_bowl":
			return "水果盘"
		"sugar_bowl":
			return "糖罐"
		"small_bowl":
			return "小碗"
		"decoy_guest":
			return "客人备用套"
		"decoy_plate":
			return "普通小盘"
		"decoy_cup":
			return "错锡杯"
		"decoy_napkin_i":
			return "绣 I. 的餐巾"
	return ITEM_LABELS.get(id, id)


func _wrong_chat_text(wrong: Dictionary) -> String:
	var slot := String(wrong.get("slot", ""))
	var got := String(wrong.get("got", ""))
	var slot_label: String = SLOT_LABELS.get(slot, slot)
	if got == "":
		return "%s还空着。先把最后一件摆上。" % slot_label
	var got_label := _chat_item_label(got)
	if got in SHARED:
		return "……%s摆的是%s。那是桌子中间的，不是这个位置。" % [slot_label, got_label]
	if got in ["decoy_guest", "decoy_plate", "decoy_cup", "decoy_napkin_i"]:
		return "……%s摆的是%s。那不是这九件里的东西。" % [slot_label, got_label]
	if slot in ["slot_toast", "slot_fruit", "slot_sugar", "slot_small"]:
		return "……%s不该放在桌子中间的%s位。先把它放回柜子。" % [got_label, slot_label]
	var correct_label := _chat_item_label(String(CORRECT[slot]))
	return "……%s摆的是%s。那不是%s。" % [slot_label, got_label, correct_label]


func _show_chat(text: String) -> void:
	chat_open = true
	_update_ring_visibility()
	_idle_seconds = 0.0
	_idle_hint_shown = false
	_set_prompt("")
	_set_crosshair(false)
	if player:
		player.frozen = true
	await Director.ui.show_text(text)
	_close_chat()


func _close_chat() -> void:
	chat_open = false
	_update_ring_visibility()
	if player:
		player.frozen = false
	_set_crosshair(true)
	_set_prompt("")


func _start_bell_sequence() -> void:
	if solved or bell_seq or held != "":
		return
	bell_seq = true
	_update_ring_visibility()
	_idle_seconds = 0.0
	_idle_hint_shown = false
	_set_prompt("")
	_set_crosshair(false)
	_status("")
	Director.ui.set_hud(false)
	if player:
		player.frozen = true
	# 回归测试/自动通关跳过演出，免得每次等十秒
	if OS.get_cmdline_user_args().has("--self-test") or Director.autoplay or OS.get_cmdline_user_args().has("--auto-solve"):
		_success()
		return
	var cam = player.get("cam") if player else null
	if not (cam is Node3D):
		_success()
		return
	if table_bell:
		table_bell.visible = false
	bell_fx = PROPS.build_bell()
	bell_fx.name = "bell_fx"
	bell_fx.scale = Vector3.ONE * 0.42
	cam.add_child(bell_fx)
	bell_fx.position = Vector3(0.22, -0.46, -0.52)
	bell_fx.rotation = Vector3(deg_to_rad(-16), deg_to_rad(18), 0)
	var audio := AudioStreamPlayer.new()
	audio.stream = load("res://audio/sfx/table_bell.wav")
	audio.volume_db = -6
	add_child(audio)
	var tw := create_tween().set_trans(Tween.TRANS_SINE).set_ease(Tween.EASE_OUT)
	tw.tween_property(bell_fx, "position", Vector3(0.20, -0.26, -0.46), 0.35)
	tw.tween_property(bell_fx, "rotation:z", deg_to_rad(12), 0.08)
	tw.tween_property(bell_fx, "rotation:z", deg_to_rad(-12), 0.10)
	tw.tween_property(bell_fx, "rotation:z", deg_to_rad(8), 0.10)
	tw.tween_property(bell_fx, "rotation:z", 0.0, 0.10)
	await get_tree().create_timer(0.35).timeout
	if audio.stream:
		audio.play()
	await tw.finished
	await get_tree().create_timer(1.0).timeout
	_play_memory()


## 保留 PR 的记忆场面，阅读和媒介表现使用当前公共系统。
func _play_memory() -> void:
	if table_bell:
		table_bell.visible = false
	var mem = MEMORY.new()
	add_child(mem)
	await mem.play(self, player)
	mem.queue_free()
	if bell_fx:
		bell_fx.queue_free()
		bell_fx = null
	if table_bell:
		table_bell.visible = true
	_success()

func _success() -> void:
	if solved:
		return
	solved = true
	_update_ring_visibility()
	_set_prompt("")
	_set_crosshair(false)
	if player:
		player.frozen = true
	await Director.ui.inspect_evidence("ev_table_diagram", "", "")
	_finish()


func _finish() -> void:
	if _finished:
		return
	_finished = true
	if is_instance_valid(_plan_viewer): _plan_viewer.close()
	_teardown_player()
	finished.emit()


func _build_ui() -> void:
	Director.ui.set_objective("餐边柜里有一张旧餐桌图。它记的是哪一年？")
	_status("先拉开餐边柜的抽屉。E 交互 · P 图纸 · R 放回")


func _set_crosshair(on: bool) -> void:
	Director.ui.crosshair.visible = on


func _update_held() -> void:
	_set_prompt("")


func _status(text: String) -> void:
	Director.ui.toast(text)


## 任务图纸采用持续停留的正面阅读；不旋转纸张，放大后可平移。
func _open_blueprint() -> void:
	if solved or blueprint_open or Director.ui._busy(): return
	if not diagram_taken:
		_status("先拉开餐边柜的抽屉，找到那张旧餐桌图。")
		return
	blueprint_open = true
	_update_ring_visibility()
	_plan_viewer = preload("res://ui/table_plan_viewer.gd").new()
	add_child(_plan_viewer)
	_plan_viewer.open()
	await _plan_viewer.closed
	_plan_viewer = null
	blueprint_open = false
	_update_ring_visibility()
	_set_prompt("")


func cancel_level() -> void:
	cancelled = true
	_finish()


func _unhandled_input(event: InputEvent) -> void:
	if chat_open or solved or bell_seq:
		return
	if blueprint_open or (player and player.frozen) or Director.ui._busy():
		return
	if event is InputEventJoypadButton and event.is_action_pressed("interact"):
		_interact()
		get_viewport().set_input_as_handled()
		return
	if event is InputEventKey and event.pressed and not event.echo:
		match event.physical_keycode:
			KEY_P:
				_open_blueprint()
				get_viewport().set_input_as_handled()
			KEY_R:
				_return_held()
				get_viewport().set_input_as_handled()
			KEY_E:
				_interact()
				get_viewport().set_input_as_handled()
	elif event is InputEventMouseButton and event.pressed and event.button_index == MOUSE_BUTTON_LEFT and Input.mouse_mode == Input.MOUSE_MODE_CAPTURED:
		_interact()
		get_viewport().set_input_as_handled()
