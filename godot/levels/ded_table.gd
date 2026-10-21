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
var diagram_taken := false
var table_body: StaticBody3D

var player
var player_own := false
var env: Environment
var camera: Camera3D

var hover := {}
var held := ""
var fail_count := 0
var solved := false
var blueprint_open := false
var _finished := false

var ui_root: Control
var hud_root: Control
var font: SystemFont
var prompt_panel: PanelContainer
var prompt_label: Label
var held_panel: PanelContainer
var held_label: Label
var status_label: Label
var objective_label: Label
var q_line: Label
var blueprint_hint_panel: PanelContainer
var blueprint_hint_label: Label
var crosshair: Control
## 3D 图纸：按 Q 时像端在手里一样出现在镜头前（不是全屏 UI）
var blueprint_3d: Node3D
var blueprint_held_hidden := false
var clue_layer: ColorRect
var table_bell: Node3D
var bell_fx: Node3D
var bell_seq := false
var chat_open := false
var chat_panel: PanelContainer
var chat_label: Label
var chat_hint: Label
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
	var cam := _find_node(self, "cam_dining_mid")
	if cam is Camera3D:
		camera = cam
	if DisplayServer.get_name() != "headless":
		_setup_player()
	if OS.get_cmdline_user_args().has("--capture-ded"):
		_capture_and_quit()
	if OS.get_cmdline_user_args().has("--capture-hud"):
		_capture_hud()
	if OS.get_cmdline_user_args().has("--self-test"):
		_self_test()
	if OS.get_cmdline_user_args().has("--chat-test"):
		_chat_test()
	if OS.get_cmdline_user_args().has("--bell-test"):
		_bell_test()
	if OS.get_cmdline_user_args().has("--idle-test"):
		_idle_test()
	if OS.get_cmdline_user_args().has("--memory-test"):
		_memory_test()
	if OS.get_cmdline_user_args().has("--memory-capture"):
		_memory_capture()
	if OS.get_cmdline_user_args().has("--memory-close-capture"):
		_memory_close_capture()
	if OS.get_cmdline_user_args().has("--memory-skip-test"):
		_memory_skip_test()
	if OS.get_cmdline_user_args().has("--memory-line2-capture"):
		_memory_line2_capture()
	if OS.get_cmdline_user_args().has("--ring-capture"):
		_ring_capture()
	if OS.get_cmdline_user_args().has("--auto-solve") or Director.autoplay:
		# 无界面回归（--autoplay）时也要能走完这一关，不能卡在等点击
		_auto_solve()


func _process(dt: float) -> void:
	if player == null or solved or blueprint_open or clue_layer.visible or chat_open or bell_seq:
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
	var cam := _find_node(self, "cam_dining_mid")
	var pcam = player.get("cam")
	if cam is Camera3D and cam.environment and pcam is Camera3D:
		env = cam.environment
		pcam.environment = env
	# 3D 图纸挂在玩家镜头前，像端在手里
	if blueprint_3d and pcam is Node3D:
		blueprint_3d.reparent(pcam, false)
		blueprint_3d.position = Vector3(-0.01, -0.07, -0.58)
		blueprint_3d.rotation = Vector3(deg_to_rad(-7), 0, deg_to_rad(2))
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
	if blueprint_3d and is_instance_valid(blueprint_3d):
		blueprint_3d.queue_free()
		blueprint_3d = null
	if player == null:
		return
	player.frozen = true
	var pcam = player.get("cam")
	if env != null and pcam is Camera3D:
		pcam.environment = null
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
	for y in [0.25, 0.55, 0.85]:
		_box(root, "柜层板", Vector3(12.92, y, -1.11), Vector3(0.50, 0.024, 1.16), shelf)

	# 两扇门向外敞开到底（贴着柜体两端），免得挡住柜内陈列
	var left_door := _box(root, "柜门左", Vector3(13.45, 0.46, -1.70), Vector3(0.028, 0.86, 0.54), wood)
	left_door.rotation.y = deg_to_rad(94)
	var right_door := _box(root, "柜门右", Vector3(13.45, 0.46, -0.52), Vector3(0.028, 0.86, 0.54), wood)
	right_door.rotation.y = deg_to_rad(94)

	# 抽屉：里面折着 1924 年的餐桌图，是这一关的入口
	drawer_root = Node3D.new()
	drawer_root.name = "餐边柜抽屉"
	drawer_root.position = Vector3(13.47, 0.14, -1.10)
	root.add_child(drawer_root)
	_box(drawer_root, "抽屉底", Vector3(-0.18, -0.045, 0), Vector3(0.36, 0.02, 0.80), shelf)
	_box(drawer_root, "抽屉面板", Vector3(0.0, 0.0, 0), Vector3(0.03, 0.12, 0.82), wood)
	_box(drawer_root, "抽屉左侧", Vector3(-0.18, 0.0, -0.40), Vector3(0.36, 0.12, 0.02), wood)
	_box(drawer_root, "抽屉右侧", Vector3(-0.18, 0.0, 0.40), Vector3(0.36, 0.12, 0.02), wood)
	_box(drawer_root, "抽屉后板", Vector3(-0.36, 0.0, 0), Vector3(0.02, 0.12, 0.80), wood)
	var knob := _box(drawer_root, "抽屉拉手", Vector3(0.03, 0.0, 0.0), Vector3(0.02, 0.025, 0.06), Color("#c39a52"), 0.6, 0.35)
	knob.rotation.x = 0.0
	_hit_area(drawer_root, "drawer", true, Vector3(0.10, 0.16, 0.86), Vector3.ZERO)

	drawer_paper = Node3D.new()
	drawer_paper.name = "折起的餐桌图"
	drawer_paper.position = Vector3(-0.16, 0.025, 0.0)
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
	if prompt_panel == null:
		return
	prompt_panel.visible = text != ""
	prompt_label.text = text


## 圆环只在端着餐具时出现，放好/空手时隐藏，避免桌面上一直浮着一圈金环
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
	drawer_open = not drawer_open
	var target := 13.72 if drawer_open else 13.47
	var tw := create_tween().set_trans(Tween.TRANS_SINE).set_ease(Tween.EASE_OUT)
	tw.tween_property(drawer_root, "position:x", target, 0.45)
	if not diagram_taken:
		drawer_paper.visible = drawer_open
		drawer_paper_area.collision_layer = 1 if drawer_open else 0
	if drawer_open and not diagram_taken:
		_status("按 E 拿起那张纸，看看它记的是哪一年。")
	elif not diagram_taken:
		_status("把抽屉推回去了。")
	else:
		_status("抽屉空了。")


func _take_diagram() -> void:
	if diagram_taken or not drawer_open:
		return
	diagram_taken = true
	drawer_paper.visible = false
	drawer_paper_area.collision_layer = 0
	if objective_label:
		objective_label.text = "按这张图，把 1924 年的餐桌复原出来。"
	if q_line:
		q_line.visible = true
	if blueprint_hint_panel:
		blueprint_hint_panel.visible = true
	_status("按这张图，把餐具摆回桌上。滚轮缩放图纸，Q / Esc 收起。")
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
	if chat_panel == null:
		return
	chat_open = true
	_update_ring_visibility()
	chat_label.text = text
	chat_panel.visible = true
	_idle_seconds = 0.0
	_idle_hint_shown = false
	_set_prompt("")
	_set_crosshair(false)
	if player:
		player.frozen = true


func _close_chat() -> void:
	if not chat_open:
		return
	chat_open = false
	_update_ring_visibility()
	if chat_panel:
		chat_panel.visible = false
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
	if hud_root:
		hud_root.visible = false
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


## 记忆演出的转场占位：先黑场、两句独白，再回到证据卡。
## 3D 的 1924 剪影/倒茶/时钟下一步替换这里，不影响前面判定与铃声。
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
	blueprint_open = false
	_update_ring_visibility()
	if blueprint_3d:
		blueprint_3d.visible = false
	if blueprint_held_hidden and held != "" and items.has(held):
		items[held].visible = true
	blueprint_held_hidden = false
	if clue_layer:
		clue_layer.visible = true
	if hud_root:
		hud_root.visible = false
	_set_prompt("")
	_update_held()
	_set_crosshair(false)
	if player:
		player.frozen = true
		Input.mouse_mode = Input.MOUSE_MODE_VISIBLE
	if Director.autoplay or OS.get_cmdline_user_args().has("--auto-solve"):
		_finish()


## 收场：收起成功卡，把控制权交回 scene_host（镜头表的 level(...) 动作继续往下走）
func _finish() -> void:
	if _finished:
		return
	_finished = true
	if clue_layer:
		clue_layer.visible = false
	if blueprint_3d:
		blueprint_3d.visible = false
	if hud_root:
		hud_root.visible = true
	_teardown_player()
	finished.emit()


# ───────────── UI ─────────────

func _build_ui() -> void:
	font = SystemFont.new()
	font.font_names = PackedStringArray(["Microsoft YaHei", "SimHei", "Noto Sans SC"])
	var layer := CanvasLayer.new()
	layer.layer = 20
	add_child(layer)
	ui_root = Control.new()
	ui_root.set_anchors_preset(Control.PRESET_FULL_RECT)
	ui_root.mouse_filter = Control.MOUSE_FILTER_IGNORE
	ui_root.theme = _theme()
	layer.add_child(ui_root)

	# 常驻 HUD 单独一层：打开图纸 / 成功卡时整层让位，免得纸面板透在下面
	hud_root = Control.new()
	hud_root.set_anchors_preset(Control.PRESET_FULL_RECT)
	hud_root.mouse_filter = Control.MOUSE_FILTER_IGNORE
	ui_root.add_child(hud_root)

	var obj := PanelContainer.new()
	obj.position = Vector2(24, 20)
	obj.custom_minimum_size = Vector2(560, 96)
	obj.add_theme_stylebox_override("panel", _paper_style())
	hud_root.add_child(obj)
	var ov := VBoxContainer.new()
	ov.add_theme_constant_override("separation", 2)
	obj.add_child(ov)
	ov.add_child(_label("CHAPTER 02 · 餐厅 · 女主人", 12, Color("#8a3f32")))
	objective_label = _label("餐边柜里有一张旧餐桌图。它记的是哪一年？", 20, Color("#35271d"))
	ov.add_child(objective_label)
	q_line = _label("Q　查看 1924 年图纸（也可以对着柜里的纸按 E）", 13, Color("#6b4a32"))
	q_line.visible = false
	ov.add_child(q_line)

	# 右上角常驻的键位提示：不靠底部那行小字，玩家一眼能看到
	var bp_hint := PanelContainer.new()
	bp_hint.set_anchors_preset(Control.PRESET_TOP_RIGHT)
	bp_hint.offset_left = -300
	bp_hint.offset_right = -24
	bp_hint.offset_top = 20
	bp_hint.offset_bottom = 64
	bp_hint.add_theme_stylebox_override("panel", _paper_style())
	bp_hint.visible = false
	hud_root.add_child(bp_hint)
	blueprint_hint_panel = bp_hint
	blueprint_hint_label = _label("Q　查看 1924 年图纸", 18, Color("#8a3f32"))
	blueprint_hint_label.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER
	bp_hint.add_child(blueprint_hint_label)

	status_label = _label("", 16, Color("#ffe3b0"))
	status_label.position = Vector2(26, 124)
	status_label.custom_minimum_size = Vector2(700, 24)
	status_label.autowrap_mode = TextServer.AUTOWRAP_WORD_SMART
	status_label.add_theme_color_override("font_outline_color", Color(0.03, 0.02, 0.01, 0.92))
	status_label.add_theme_constant_override("outline_size", 5)
	status_label.visible = false
	hud_root.add_child(status_label)

	# 格雷的内心独白：屏幕下方的纸质聊天框，一次最多两行
	chat_panel = PanelContainer.new()
	chat_panel.set_anchors_preset(Control.PRESET_CENTER_BOTTOM)
	chat_panel.offset_left = -380
	chat_panel.offset_right = 380
	chat_panel.offset_top = -164
	chat_panel.offset_bottom = -24
	chat_panel.add_theme_stylebox_override("panel", _paper_style())
	chat_panel.visible = false
	hud_root.add_child(chat_panel)
	var cv := VBoxContainer.new()
	cv.add_theme_constant_override("separation", 4)
	chat_panel.add_child(cv)
	var who := _label("格雷", 14, Color("#8a3f32"))
	cv.add_child(who)
	chat_label = _label("", 17, Color("#35271d"))
	chat_label.autowrap_mode = TextServer.AUTOWRAP_WORD_SMART
	chat_label.max_lines_visible = 2
	chat_label.custom_minimum_size = Vector2(720, 0)
	cv.add_child(chat_label)
	chat_hint = _label("E　继续", 12, Color("#7a5c3e"))
	chat_hint.horizontal_alignment = HORIZONTAL_ALIGNMENT_RIGHT
	cv.add_child(chat_hint)

	# 准星（不用主界面的准星，这一关单独运行也要有）
	var center := CenterContainer.new()
	center.set_anchors_preset(Control.PRESET_FULL_RECT)
	center.mouse_filter = Control.MOUSE_FILTER_IGNORE
	hud_root.add_child(center)
	crosshair = ColorRect.new()
	crosshair.custom_minimum_size = Vector2(10, 10)
	crosshair.color = Color(0, 0, 0, 0.35)
	crosshair.mouse_filter = Control.MOUSE_FILTER_IGNORE
	center.add_child(crosshair)
	var dot := ColorRect.new()
	dot.custom_minimum_size = Vector2(6, 6)
	dot.color = Color(1, 1, 1, 0.85)
	dot.mouse_filter = Control.MOUSE_FILTER_IGNORE
	center.add_child(dot)

	# 手上拿着什么
	held_panel = PanelContainer.new()
	held_panel.set_anchors_preset(Control.PRESET_CENTER_TOP)
	held_panel.offset_left = -230
	held_panel.offset_right = 230
	held_panel.offset_top = 16
	held_panel.offset_bottom = 54
	held_panel.add_theme_stylebox_override("panel", _pill_style())
	held_panel.visible = false
	hud_root.add_child(held_panel)
	held_label = _label("", 16, Color("#f4e7cf"))
	held_label.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER
	held_panel.add_child(held_label)

	# 准星下面的交互提示
	prompt_panel = PanelContainer.new()
	prompt_panel.set_anchors_preset(Control.PRESET_CENTER_BOTTOM)
	prompt_panel.offset_left = -250
	prompt_panel.offset_right = 250
	prompt_panel.offset_top = -136
	prompt_panel.offset_bottom = -92
	prompt_panel.add_theme_stylebox_override("panel", _pill_style())
	prompt_panel.visible = false
	hud_root.add_child(prompt_panel)
	prompt_label = _label("", 17, Color("#f4e7cf"))
	prompt_label.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER
	prompt_panel.add_child(prompt_label)

	var controls := _label("WASD 移动 · 鼠标看 · E 交互 · Q 图纸 · R 放回", 12, Color("#d8c8b0"))
	controls.set_anchors_preset(Control.PRESET_BOTTOM_RIGHT)
	controls.offset_left = -460
	controls.offset_right = -24
	controls.offset_top = -34
	controls.offset_bottom = -12
	controls.horizontal_alignment = HORIZONTAL_ALIGNMENT_RIGHT
	controls.add_theme_color_override("font_outline_color", Color(0.03, 0.02, 0.01, 0.85))
	controls.add_theme_constant_override("outline_size", 4)
	hud_root.add_child(controls)

	_build_blueprint_3d()
	_build_clue_overlay()
	_set_crosshair(true)
	_update_held()
	_status("先走到右手边的餐边柜，拉开抽屉看看里面有什么。")


func _theme() -> Theme:
	var t := Theme.new()
	t.default_font = font
	t.default_font_size = 16
	return t


func _label(text: String, size: int, color: Color) -> Label:
	var l := Label.new()
	l.text = text
	l.add_theme_font_size_override("font_size", size)
	l.add_theme_color_override("font_color", color)
	return l


func _paper_style() -> StyleBoxFlat:
	var sb := StyleBoxFlat.new()
	sb.bg_color = Color(0.95, 0.90, 0.80, 0.94)
	sb.border_color = Color("#94795a")
	sb.set_border_width_all(1)
	sb.set_corner_radius_all(4)
	sb.set_content_margin_all(10)
	return sb


func _pill_style() -> StyleBoxFlat:
	var sb := StyleBoxFlat.new()
	sb.bg_color = Color(0.04, 0.03, 0.02, 0.78)
	sb.border_color = Color(0.75, 0.62, 0.42, 0.5)
	sb.set_border_width_all(1)
	sb.set_corner_radius_all(4)
	sb.set_content_margin_all(8)
	return sb


func _button(text: String, kind: String) -> Button:
	var b := Button.new()
	b.text = text
	b.custom_minimum_size = Vector2(160, 42)
	b.add_theme_font_size_override("font_size", 16)
	b.add_theme_color_override("font_color", Color("#3b2c20"))
	b.add_theme_color_override("font_hover_color", Color("#8a3f32"))
	b.add_theme_stylebox_override("normal", _paper_style())
	b.add_theme_stylebox_override("hover", _paper_style())
	b.add_theme_stylebox_override("pressed", _paper_style())
	if kind == "red":
		b.add_theme_color_override("font_color", Color("#8a3f32"))
	return b


func _set_crosshair(on: bool) -> void:
	if crosshair:
		crosshair.visible = on


func _update_held() -> void:
	if held_panel == null:
		return
	held_panel.visible = held != ""
	if held != "":
		held_label.text = "手上：%s　　E 摆放 · R 放回" % ITEM_LABELS[held]


func _status(text: String) -> void:
	if status_label == null:
		return
	status_label.text = text
	status_label.visible = text != ""


func _build_blueprint_3d() -> void:
	# 图纸是 3D 纸片：按 Q 时像端在手里一样挂在玩家镜头前，而不是全屏 UI
	blueprint_3d = Node3D.new()
	blueprint_3d.name = "蓝图纸"
	var back := MeshInstance3D.new()
	var bm := BoxMesh.new()
	bm.size = Vector3(0.64, 0.49, 0.006)
	back.mesh = bm
	var bmat := StandardMaterial3D.new()
	bmat.albedo_color = Color("#e7dcc2")
	bmat.roughness = 0.95
	back.material_override = bmat
	back.position.z = -0.005
	blueprint_3d.add_child(back)
	var quad := QuadMesh.new()
	quad.size = Vector2(0.62, 0.465)
	var face := MeshInstance3D.new()
	face.mesh = quad
	var mat := StandardMaterial3D.new()
	mat.shading_mode = BaseMaterial3D.SHADING_MODE_UNSHADED
	mat.albedo_texture = load("res://art/footage/ded_table_blueprint.png")
	mat.cull_mode = BaseMaterial3D.CULL_DISABLED
	mat.texture_filter = BaseMaterial3D.TEXTURE_FILTER_LINEAR_WITH_MIPMAPS
	face.material_override = mat
	blueprint_3d.add_child(face)
	blueprint_3d.visible = false
	add_child(blueprint_3d)


func _open_blueprint() -> void:
	if solved or blueprint_open:
		return
	if not diagram_taken:
		_status("先拉开餐边柜的抽屉，找到那张旧餐桌图。")
		return
	blueprint_open = true
	_update_ring_visibility()
	if blueprint_3d:
		blueprint_3d.position.z = -0.58
		blueprint_3d.visible = true
	# 图纸盖住视线时先把手里那件藏起来，收起图纸再还原
	if held != "" and items.has(held):
		items[held].visible = false
		blueprint_held_hidden = true
	_set_prompt("滚轮　缩放 · Q / Esc 收起图纸")
	if blueprint_hint_label:
		blueprint_hint_label.text = "Q / Esc 收起 · 滚轮缩放"
	_set_crosshair(false)


func _zoom_blueprint(delta: float) -> void:
	if blueprint_3d == null:
		return
	blueprint_3d.position.z = clampf(blueprint_3d.position.z + delta, -1.10, -0.38)


func _close_blueprint() -> void:
	blueprint_open = false
	_update_ring_visibility()
	if blueprint_3d:
		blueprint_3d.visible = false
	if blueprint_held_hidden and held != "" and items.has(held):
		items[held].visible = true
	blueprint_held_hidden = false
	if blueprint_hint_label:
		blueprint_hint_label.text = "Q　查看 1924 年图纸"
	_set_prompt("")
	_set_crosshair(true)


func _build_clue_overlay() -> void:
	clue_layer = ColorRect.new()
	clue_layer.set_anchors_preset(Control.PRESET_FULL_RECT)
	clue_layer.color = Color(0.03, 0.02, 0.01, 0.88)
	clue_layer.mouse_filter = Control.MOUSE_FILTER_STOP
	clue_layer.visible = false
	ui_root.add_child(clue_layer)
	var center := CenterContainer.new()
	center.set_anchors_preset(Control.PRESET_FULL_RECT)
	clue_layer.add_child(center)
	var panel := PanelContainer.new()
	panel.custom_minimum_size = Vector2(780, 430)
	panel.add_theme_stylebox_override("panel", _paper_style())
	center.add_child(panel)
	var v := VBoxContainer.new()
	v.add_theme_constant_override("separation", 12)
	panel.add_child(v)
	v.add_child(_label("复原成功", 30, Color("#8a3f32")))
	var body := _label("1924 年的餐桌摆放图\n\n五个位置。南端是卢西恩的旧餐具：修补过缺口的旧盘、锡杯、短叉、绣着卢西恩名字的餐巾。图背写着 1924 和卢西恩的位子。\n\n图是安布罗斯留下的记录。康斯坦斯说不认识卢西恩，但每天还是摆着同一副餐具。", 17, Color("#3b2c20"))
	body.autowrap_mode = TextServer.AUTOWRAP_WORD_SMART
	body.custom_minimum_size.y = 250
	v.add_child(body)
	var close := _button("收起线索", "red")
	close.pressed.connect(_finish)
	v.add_child(close)


func _unhandled_input(event: InputEvent) -> void:
	if chat_open:
		var advance := event.is_action_pressed("interact")
		if event is InputEventKey and event.pressed and not event.echo and event.physical_keycode == KEY_E:
			advance = true
		if event is InputEventMouseButton and event.pressed and event.button_index == MOUSE_BUTTON_LEFT:
			advance = true
		if advance:
			_close_chat()
			get_viewport().set_input_as_handled()
		return
	if solved or bell_seq:
		return
	if blueprint_open:
		if event is InputEventKey and event.pressed and not event.echo:
			if event.physical_keycode == KEY_Q or event.physical_keycode == KEY_ESCAPE:
				_close_blueprint()
				get_viewport().set_input_as_handled()
		elif event is InputEventMouseButton and event.pressed:
			if event.button_index == MOUSE_BUTTON_WHEEL_UP:
				_zoom_blueprint(-0.06)
				get_viewport().set_input_as_handled()
			elif event.button_index == MOUSE_BUTTON_WHEEL_DOWN:
				_zoom_blueprint(0.06)
				get_viewport().set_input_as_handled()
			elif event.button_index == MOUSE_BUTTON_LEFT:
				_close_blueprint()
				get_viewport().set_input_as_handled()
		return
	if clue_layer.visible:
		return
	if event is InputEventKey and event.pressed and not event.echo:
		match event.physical_keycode:
			KEY_Q:
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


# ───────────── 自查：截图与自动通关 ─────────────

func _ring_capture() -> void:
	await get_tree().create_timer(0.5).timeout
	diagram_taken = true
	_pick_up("small_bowl")
	var pcam = player.get("cam")
	player.global_position = Vector3(15.75, 0.02, -4.35)
	await get_tree().physics_frame
	pcam.look_at(Vector3(15.75, 0.79, -2.55), Vector3.UP)
	await get_tree().physics_frame
	_update_hover()
	_update_ring_visibility()
	await RenderingServer.frame_post_draw
	var dir := _capture_dir()
	DirAccess.make_dir_recursive_absolute(dir)
	get_viewport().get_texture().get_image().save_png(dir.path_join("ded_table_rings.png"))
	get_tree().quit(0)


func _memory_line2_capture() -> void:
	await get_tree().create_timer(0.5).timeout
	diagram_taken = true
	for slot in CORRECT:
		_place_direct(slot, CORRECT[slot])
	if hud_root:
		hud_root.visible = false
	var mem = MEMORY.new()
	add_child(mem)
	mem.play(self, player)
	await get_tree().create_timer(9.2).timeout
	get_tree().paused = true
	await RenderingServer.frame_post_draw
	var dir := _capture_dir()
	DirAccess.make_dir_recursive_absolute(dir)
	get_viewport().get_texture().get_image().save_png(dir.path_join("ded_table_memory_line2.png"))
	get_tree().quit(0)


func _memory_skip_test() -> void:
	await get_tree().create_timer(0.5).timeout
	diagram_taken = true
	for slot in CORRECT:
		_place_direct(slot, CORRECT[slot])
	if hud_root:
		hud_root.visible = false
	var mem = MEMORY.new()
	add_child(mem)
	mem.play(self, player)
	await get_tree().create_timer(1.2).timeout
	var ev := InputEventKey.new()
	ev.physical_keycode = KEY_E
	ev.pressed = true
	mem._unhandled_input(ev)
	await get_tree().create_timer(1.0).timeout
	print("[memory-skip] finished=", mem._finished)
	get_tree().quit(0 if mem._finished else 1)


func _memory_close_capture() -> void:
	# 暂停时间线再截特写，避免截图阻塞把演出跑过头
	await get_tree().create_timer(0.5).timeout
	diagram_taken = true
	for slot in CORRECT:
		_place_direct(slot, CORRECT[slot])
	if hud_root:
		hud_root.visible = false
	var mem = MEMORY.new()
	add_child(mem)
	mem.play(self, player)
	await get_tree().create_timer(5.7).timeout
	get_tree().paused = true
	await RenderingServer.frame_post_draw
	var dir := _capture_dir()
	DirAccess.make_dir_recursive_absolute(dir)
	get_viewport().get_texture().get_image().save_png(dir.path_join("ded_table_memory_pour.png"))
	get_tree().quit(0)


func _memory_capture() -> void:
	# 只截记忆画面，不等完整时间线（截图后直接退出）
	await get_tree().create_timer(0.5).timeout
	diagram_taken = true
	for slot in CORRECT:
		_place_direct(slot, CORRECT[slot])
	if hud_root:
		hud_root.visible = false
	var mem = MEMORY.new()
	add_child(mem)
	mem.play(self, player)
	await get_tree().create_timer(2.2).timeout
	var dir := _capture_dir()
	DirAccess.make_dir_recursive_absolute(dir)
	await RenderingServer.frame_post_draw
	get_viewport().get_texture().get_image().save_png(dir.path_join("ded_table_memory_wide.png"))
	await get_tree().create_timer(3.0).timeout
	await RenderingServer.frame_post_draw
	get_viewport().get_texture().get_image().save_png(dir.path_join("ded_table_memory_pour.png"))
	await get_tree().create_timer(3.0).timeout
	await RenderingServer.frame_post_draw
	get_viewport().get_texture().get_image().save_png(dir.path_join("ded_table_memory_line2.png"))
	get_tree().quit(0)


func _memory_test() -> void:
	await get_tree().create_timer(0.5).timeout
	diagram_taken = true
	for slot in CORRECT:
		_place_direct(slot, CORRECT[slot])
	if hud_root:
		hud_root.visible = false
	var mem = MEMORY.new()
	add_child(mem)
	mem.play(self, player)
	await get_tree().create_timer(12.0).timeout
	print("[memory-test] finished=", mem._finished)
	var ok: bool = mem._finished
	mem.queue_free()
	get_tree().quit(0 if ok else 1)

func _idle_test() -> void:
	# 八件摆满后发呆五秒，HUD 只提示还空一个位置
	await get_tree().create_timer(0.5).timeout
	diagram_taken = true
	for i in CHECK_ORDER.size() - 1:
		var slot: String = CHECK_ORDER[i]
		_place_direct(slot, CORRECT[slot])
	await get_tree().create_timer(5.3).timeout
	print("[idle-test] status=", status_label.text, " visible=", status_label.visible)
	var ok := status_label.text.contains("空着") and status_label.visible
	get_tree().quit(0 if ok else 1)


func _bell_test() -> void:
	# 摆对九件，等自动摇铃 + 记忆演出结束，最后应出成功卡
	await get_tree().create_timer(0.5).timeout
	diagram_taken = true
	for slot in CORRECT:
		_place_direct(slot, CORRECT[slot])
	_after_table_changed()
	await get_tree().create_timer(16.0).timeout
	print("[bell-test] solved=", solved, " bell_seq=", bell_seq)
	get_tree().quit(0 if solved else 1)


func _chat_test() -> void:
	# 把九件用错位方式摆满，确认格雷的聊天框会指出第一个错，E 能继续
	await get_tree().create_timer(0.5).timeout
	diagram_taken = true
	for i in CHECK_ORDER.size():
		var slot: String = CHECK_ORDER[i]
		var wrong_slot: String = CHECK_ORDER[(i + 1) % CHECK_ORDER.size()]
		_place_direct(slot, String(CORRECT[wrong_slot]))
	_after_table_changed()
	print("[chat-test] open=", chat_open, " frozen=", player.frozen if player else "no-player", " text=", chat_label.text)
	var dir := _capture_dir()
	DirAccess.make_dir_recursive_absolute(dir)
	await RenderingServer.frame_post_draw
	get_viewport().get_texture().get_image().save_png(dir.path_join("ded_table_hud_chat.png"))
	var opened := chat_open and chat_label.text.contains("北端")
	var ev := InputEventKey.new()
	ev.physical_keycode = KEY_E
	ev.pressed = true
	_unhandled_input(ev)
	await get_tree().create_timer(0.2).timeout
	print("[chat-test] closed=", not chat_open, " frozen=", player.frozen if player else "no-player")
	if chat_open:
		_close_chat()
	get_tree().quit(0 if opened and not chat_open else 1)


func _self_test() -> void:
	await get_tree().create_timer(0.3).timeout
	var pcam = player.get("cam") if player else null
	if not (pcam is Camera3D):
		print("[self-test] 没有玩家相机")
		get_tree().quit(1)
		return
	var ok := true
	var dir := _capture_dir()
	DirAccess.make_dir_recursive_absolute(dir)
	# 先按流程拉开抽屉、拿出图，后面的拿取才会解锁
	player.global_position = Vector3(13.95, 0.02, -1.10)
	player.rotation = Vector3.ZERO
	await get_tree().physics_frame
	pcam.look_at(Vector3(13.47, 0.14, -1.10), Vector3.UP)
	await get_tree().physics_frame
	_update_hover()
	print("[self-test] 抽屉 hover=", hover)
	if String(hover.get("kind", "")) == "drawer":
		_interact()
	else:
		ok = false
	await get_tree().create_timer(0.6).timeout
	await RenderingServer.frame_post_draw
	get_viewport().get_texture().get_image().save_png(dir.path_join("ded_table_hud_drawer.png"))
	pcam.look_at(drawer_paper.global_position + Vector3(0, 0.02, 0), Vector3.UP)
	await get_tree().physics_frame
	_update_hover()
	print("[self-test] 图纸 hover=", hover)
	if String(hover.get("kind", "")) == "diagram":
		_interact()
	else:
		ok = false
	await get_tree().create_timer(0.2).timeout
	if blueprint_open:
		_close_blueprint()
	if not diagram_taken:
		ok = false
	if not ok:
		print("[self-test] 抽屉/图纸入口失败")
		get_tree().quit(1)
		return
	# 图纸：3D 纸片再看一次，留一张图（放在摆桌之前，最后一件会自动进成功流程）
	_open_blueprint()
	_zoom_blueprint(-0.08)
	print("[self-test] 图纸缩放后 z=", blueprint_3d.position.z)
	await RenderingServer.frame_post_draw
	get_viewport().get_texture().get_image().save_png(dir.path_join("ded_table_hud_blueprint.png"))
	_close_blueprint()
	for slot in CORRECT:
		var id: String = CORRECT[slot]
		player.global_position = Vector3(13.95, 0.02, -1.10)
		player.rotation = Vector3.ZERO
		await get_tree().physics_frame
		pcam.look_at(items[id].global_position + Vector3(0, 0.08, 0), Vector3.UP)
		await get_tree().physics_frame
		_update_hover()
		print("[self-test] 柜内 hover=", hover, " 想要=", id)
		if String(hover.get("id", "")) != id:
			ok = false
			break
		if id == "ambrose":
			await RenderingServer.frame_post_draw
			get_viewport().get_texture().get_image().save_png(dir.path_join("ded_table_hud_prompt.png"))
		_interact()
		if held != id:
			print("[self-test] 没拿起来：held=", held)
			ok = false
			break
		if id == "ambrose":
			await RenderingServer.frame_post_draw
			get_viewport().get_texture().get_image().save_png(dir.path_join("ded_table_hud_held.png"))
		var sp: Vector3 = SLOT_POS[slot]
		var away := Vector3(0, 0, 1.0)
		match slot:
			"slot_north":
				away = Vector3(0, 0, -1.0)
			"slot_east_1", "slot_east_2":
				away = Vector3(1.0, 0, 0)
			"slot_west":
				away = Vector3(-1.0, 0, 0)
		player.global_position = Vector3(sp.x, 0.02, sp.z) + away
		await get_tree().physics_frame
		pcam.look_at(Vector3(sp.x, sp.y + 0.10, sp.z), Vector3.UP)
		await get_tree().physics_frame
		_update_hover()
		print("[self-test] 桌面 hover=", hover, " 想要=", slot)
		if String(hover.get("id", "")) != slot:
			ok = false
			break
		_interact()
		if String(slot_items.get(slot, "")) != id:
			ok = false
			break
	print("[self-test] solved=", solved, " -> ", "PASS" if ok and solved else "FAIL")
	await get_tree().create_timer(0.3).timeout
	get_tree().quit(0 if ok and solved else 1)


func _capture_and_quit() -> void:
	# 输出目录可通过 --capture-dir=<绝对路径> 指定，默认 assets/3d/ded_table/review/
	var dir := _capture_dir()
	DirAccess.make_dir_recursive_absolute(dir)
	await get_tree().create_timer(1.2).timeout
	# 宽景：和原来的 cam_dining_mid 一样，从南端看整张桌子
	_capture_camera(Vector3(15.75, 1.515, -4.65), Vector3(15.55, 0.82, -2.55), 59.0)
	await _save_view(dir.path_join("ded_table_wide.png"))

	# 餐边柜：正面略微俯视，能同时看到五套餐具的盘沿与杯形
	_add_capture_light(Vector3(13.60, 1.10, -1.06), 1.1, 2.2)
	_capture_camera(Vector3(13.98, 0.96, -1.11), Vector3(13.00, 0.57, -1.11), 52.0)
	await get_tree().create_timer(0.6).timeout
	await _save_view(dir.path_join("ded_table_cabinet.png"))

	_showcase_solve()
	_capture_lights()
	_capture_camera(Vector3(15.75, 1.515, -4.65), Vector3(15.55, 0.82, -2.55), 59.0)
	await get_tree().create_timer(0.5).timeout
	await _save_view(dir.path_join("ded_table_solved.png"))
	_capture_camera(Vector3(15.74, 1.20, -0.86), Vector3(15.74, 0.79, -1.47), 44.0)
	await get_tree().create_timer(0.6).timeout
	await _save_view(dir.path_join("ded_table_close.png"))
	_capture_camera(Vector3(15.78, 0.94, -1.20), Vector3(15.74, 0.80, -1.47), 38.0)
	await get_tree().create_timer(0.5).timeout
	await _save_view(dir.path_join("ded_table_macro.png"))
	_teardown_player()
	get_tree().quit()


func _capture_hud() -> void:
	# 自查：从玩家视角截图（带 HUD），用来检查出生点、准星与提示
	var dir := _capture_dir()
	DirAccess.make_dir_recursive_absolute(dir)
	await get_tree().create_timer(2.0).timeout
	await RenderingServer.frame_post_draw
	var path := dir.path_join("ded_table_hud.png")
	get_viewport().get_texture().get_image().save_png(path)
	print("[ded_table] 第一人称截图：", path)
	_teardown_player()
	get_tree().quit()


func _capture_dir() -> String:
	for a in OS.get_cmdline_user_args():
		if a.begins_with("--capture-dir="):
			return a.substr("--capture-dir=".length())
	# 截图属于中间产物：默认落到 assets/3d/ded_table/review/，不要堆在 godot/ 根目录
	return ProjectSettings.globalize_path("res://").path_join("../assets/3d/ded_table/review").simplify_path()


func _add_capture_light(pos: Vector3, energy: float, reach: float) -> void:
	var l := OmniLight3D.new()
	l.light_color = Color(1.0, 0.97, 0.92)
	l.light_energy = energy
	l.omni_range = reach
	l.omni_attenuation = 1.2
	l.position = pos
	add_child(l)


func _capture_lights() -> void:
	# 只为截图补的中性光：餐厅本身偏暖，近景看不清器物细节
	for offset in [Vector3(0.0, 1.45, 0.35), Vector3(0.0, 1.42, -0.35)]:
		_add_capture_light(Vector3(15.74, 0.79, -1.47) + offset, 1.1, 2.0)


func _capture_camera(pos: Vector3, target: Vector3, fov := 42.0) -> void:
	var cam := Camera3D.new()
	# 餐厅的天空/环境光是挂在相机上的；新相机不继承就会变成无环境光 → 器物全黑
	if camera != null and camera.environment != null:
		cam.environment = camera.environment
	cam.fov = fov
	cam.near = 0.02
	add_child(cam)
	cam.global_position = pos
	cam.look_at(target, Vector3.UP)
	cam.current = true
	camera = cam
	# 截图不想要 HUD 挡画面
	if ui_root != null:
		ui_root.visible = false


func _save_view(path: String) -> void:
	await RenderingServer.frame_post_draw
	var img := get_viewport().get_texture().get_image()
	img.save_png(path)
	print("[ded_table] 截图：", path)


func _showcase_solve() -> void:
	# 只摆放、不摇铃：避免成功面板挡住桌面
	for slot in CORRECT:
		_place_direct(slot, CORRECT[slot])


func _place_direct(slot: String, id: String) -> void:
	var n: Node3D = items[id]
	n.reparent(self, false)
	n.global_position = SLOT_POS[slot] + Vector3(0, 0.012, 0)
	n.rotation = Vector3(0, deg_to_rad(SLOT_FACING.get(slot, 0.0)), 0)
	n.scale = Vector3.ONE
	item_areas[id].collision_layer = 0
	slot_items[slot] = id
	slot_rings[slot].visible = false


func _auto_solve() -> void:
	await get_tree().create_timer(0.5).timeout
	for slot in CORRECT:
		_place_direct(slot, CORRECT[slot])
	_success()
