extends SceneTree
## 使用真实物理世界验证边缘容错、稳定性和遮挡，不依赖截图或模拟命中结果。
const Targeting := preload("res://world/interaction_targeting.gd")
var failures := 0
var stage: Node3D
var camera: Camera3D

func _initialize() -> void:
	call_deferred("run")

func box(pos: Vector3, size: Vector3, solid := false) -> CollisionObject3D:
	var body: CollisionObject3D = StaticBody3D.new() if solid else Area3D.new()
	body.collision_layer = 1 if solid else 2
	var collision := CollisionShape3D.new()
	var shape := BoxShape3D.new()
	shape.size = size
	collision.shape = shape
	body.add_child(collision)
	stage.add_child(body)
	body.position = pos
	return body

func check(label: String, actual: Node, expected: Node) -> void:
	var passed := actual == expected
	print("PASS " if passed else "FAIL ", label)
	if not passed:
		failures += 1

func run() -> void:
	stage = Node3D.new()
	root.add_child(stage)
	camera = Camera3D.new()
	camera.fov = 70
	stage.add_child(camera)
	camera.current = true
	root.size = Vector2i(1280, 720)
	var paper := box(Vector3(0.07, 0, -1.5), Vector3(0.08, 0.12, 0.002))
	await physics_frame
	await physics_frame
	check("薄纸边缘偏离准星仍可选", Targeting.pick(camera, [paper]), paper)
	check("已选目标不会凭空保留", Targeting.pick(camera, [], paper), null)
	paper.position.x = 0.4
	check("明显移开立即失效", Targeting.pick(camera, [paper], paper), null)
	paper.position = Vector3(0, 0, -2.6)
	check("超距立即失效", Targeting.pick(camera, [paper], paper), null)
	paper.set_meta("interaction_reach", 2.65)
	check("指定物件允许略远的可见表面", Targeting.pick(camera, [paper]), paper)
	paper.position.z = -2.75
	check("指定物件超过自身距离仍失效", Targeting.pick(camera, [paper], paper), null)
	paper.set_meta("interaction_reach", 99.0)
	check("配置距离有上限", Targeting.pick(camera, [paper], paper), null)
	paper.remove_meta("interaction_reach")
	paper.position = Vector3(0, 0, 1)
	check("镜头后方不可选", Targeting.pick(camera, [paper]), null)
	paper.position = Vector3(0, 0, -1.5)
	paper.hide()
	check("隐藏物品不可选", Targeting.pick(camera, [paper]), null)
	paper.show()
	var neighbor := box(Vector3(0.07, 0, -1), Vector3(0.04, 0.1, 0.04))
	check("正对物品优先于旁边更近的物品", Targeting.pick(camera, [neighbor, paper], neighbor), paper)
	var left := box(Vector3(-0.05, 0, -1.2), Vector3(0.04, 0.1, 0.04))
	var right := box(Vector3(0.051, 0, -1.2), Vector3(0.04, 0.1, 0.04))
	check("邻近目标小幅偏差不抢选", Targeting.pick(camera, [left, right], right), right)
	var large := box(Vector3(0, 0, -3), Vector3(1, 1, 2))
	check("按表面距离而不是中心距离", Targeting.pick(camera, [large]), large)
	var wall := box(Vector3(0, 0, -0.7), Vector3(2, 2, 0.1), true)
	await physics_frame
	await physics_frame
	check("墙体遮挡立即取消已有目标", Targeting.pick(camera, [paper], paper), null)
	check("容错范围不能绕过遮挡", Targeting.pick(camera, [neighbor], neighbor), null)
	wall.position.x = 4
	await physics_frame
	await physics_frame
	check("移开遮挡后可选", Targeting.pick(camera, [paper]), paper)
	var door := box(Vector3(0, 0, -0.7), Vector3(0.8, 2, 0.05), true)
	await physics_frame
	await physics_frame
	check("关闭柜门阻止选中柜内物品", Targeting.pick(camera, [paper]), null)
	check("门本身可操作", Targeting.pick(camera, [door, paper]), door)
	door.position.x = 4
	await physics_frame
	await physics_frame
	check("开门后可选柜内物品", Targeting.pick(camera, [paper]), paper)
	paper.set_meta("interaction_normal", Vector3.BACK)
	check("单面线索正面可见", Targeting.pick(camera, [paper]), paper)
	paper.set_meta("interaction_normal", Vector3.FORWARD)
	check("单面线索背面立即失效", Targeting.pick(camera, [paper], paper), null)
	paper.remove_meta("interaction_normal")
	var prop := box(Vector3(0, 0, -0.8), Vector3(0.3, 0.3, 0.1), true)
	prop.collision_layer = 4
	await physics_frame
	await physics_frame
	check("渲染道具的交互遮挡层也挡住线索", Targeting.pick(camera, [paper]), null)

	prop.position.x = 4
	await physics_frame;await physics_frame
	var tie_a := box(Vector3(0,0,-1.3),Vector3(.08,.12,.01))
	var tie_b := box(Vector3(0,0,-1.3),Vector3(.08,.12,.01))
	tie_a.name="TieA";tie_b.name="TieB"
	check("同表面重叠时候选顺序不改变选择",Targeting.pick(camera,[tie_b,tie_a]),Targeting.pick(camera,[tie_a,tie_b]))
	check("同表面重叠时保留已提示对象",Targeting.pick(camera,[tie_a,tie_b],tie_b),tie_b)
	tie_a.position=Vector3(-.07,0,-1.3);tie_b.position=Vector3(.07,0,-1.3)
	check("等分边缘候选不因遍历顺序抢选",Targeting.pick(camera,[tie_b,tie_a]),Targeting.pick(camera,[tie_a,tie_b]))
	check("等分边缘候选保留已有提示",Targeting.pick(camera,[tie_a,tie_b],tie_b),tie_b)
	tie_a.position=Vector3(0,0,-1.3);tie_b.position=Vector3(0,0,-1.1)
	check("更近直接命中优先于旧提示",Targeting.pick(camera,[tie_a,tie_b],tie_a),tie_b)
	var thin_wall := box(Vector3(0,0,-1.485),Vector3(.4,.4,.01),true)
	await physics_frame;await physics_frame
	check("贴近薄墙背后的纸张仍不可穿墙选择",Targeting.pick(camera,[paper],paper),null)
	paper.set_meta("hotspot_id","test_paper")
	thin_wall.set_meta("inspection_surface_for","test_paper")
	check("物件自身表面小幅装配误差保留可检视",Targeting.pick(camera,[paper]),paper)
	thin_wall.set_meta("inspection_surface_for","other_object")
	check("其他物件不能借用自身表面余量",Targeting.pick(camera,[paper]),null)
	print("TARGETING failures=", failures)
	quit(0 if failures == 0 else 1)
