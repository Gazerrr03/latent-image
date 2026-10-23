extends SceneTree
## 真实衣柜：先选门，开门后再选毛衣，关门重新遮挡；不绕过实体层。
const Targeting := preload("res://world/interaction_targeting.gd")
var failures := 0
func _initialize() -> void:
	call_deferred("run")
func check(label: String, ok: bool) -> void:
	print("PASS " if ok else "FAIL ", label)
	if not ok:
		failures += 1
func run() -> void:
	root.get_node("GameState").persist = false
	var main: Node = load("res://main.tscn").instantiate()
	root.add_child(main)
	await process_frame
	root.get_node("GameState").reset()
	var director := root.get_node("Director")
	var host: Node = director.world
	director.ui.menus.hide()
	host.show_scene("con_room")
	host.set_mode("walk", "")
	host.player.frozen = true
	var camera := Camera3D.new()
	main.add_child(camera)
	camera.position = Vector3(5.8, 5.215, -7.25)
	var target: Node3D = host.hotspot_nodes["hs_con_sweater"]
	camera.look_at(target.global_position)
	var leaf: Node3D = target.get_meta("container_leaf", null)
	var door: Node
	for body in host.doors:
		if host.doors[body]["leaf"] == leaf:
			door = body
	check("衣柜门有真实门板碰撞与合页状态", door != null and leaf != null)
	if door == null:
		quit(1)
		return
	await physics_frame
	await physics_frame
	check("关闭柜门时无法选中柜内毛衣", Targeting.pick(camera, [target], null, [host.player.get_rid()]) == null)
	check("关闭柜门时优先选中门板", Targeting.pick(camera, [target, door], null, [host.player.get_rid()]) == door)
	check("提示明确操作的是衣柜", host.door_label(door) == "开门：衣柜")
	host.toggle_door(door, Vector3(5.8, 3.615, -7.25))
	await create_timer(0.9).timeout
	check("正常开门动作可打开柜门", host.door_is_open(door))
	check("开门后可选中内部物品", Targeting.pick(camera, [target, door], null, [host.player.get_rid()]) == target)
	host.toggle_door(door, Vector3(5.8, 3.615, -7.25))
	await create_timer(0.9).timeout
	check("正常关门后重新阻止检视内部物品", not host.door_is_open(door) and Targeting.pick(camera, [target], target, [host.player.get_rid()]) == null)
	host.show_scene("seance")
	host.apply_room_states("C5-03")
	for id in ["hs_se_cards", "hs_se_photo", "hs_se_gloves"]:
		check("绑定原模型末尾编号：" + id, host.hotspot_nodes.has(id) and host.hotspot_nodes[id].is_visible_in_tree())
	host.apply_room_states("C5-04")
	check("状态层隐藏后物品不可选", not host.hotspot_nodes["hs_se_cards"].is_visible_in_tree())
	print("CONTAINER_INTERACTION failures=", failures)
	quit(0 if failures == 0 else 1)
