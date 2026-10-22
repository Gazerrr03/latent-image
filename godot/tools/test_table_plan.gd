extends SceneTree
var failures := 0
func _initialize() -> void: call_deferred("run")
func check(label: String, ok: bool) -> void:
	print("PASS " if ok else "FAIL ", label)
	if not ok: failures += 1
func frame(count := 3) -> void:
	for i in count: await process_frame
func run() -> void:
	create_timer(45).timeout.connect(func(): quit(2))
	root.get_node("GameState").persist = false
	var main = load("res://main.tscn").instantiate()
	root.add_child(main)
	await frame()
	var director = root.get_node("Director")
	director.ui.menus.hide()
	director.world.show_scene("dining")
	director.world.set_mode("walk", "")
	director.world.enter_level("ded_table")
	await frame()
	var level = director.world._sublevel
	level.player = director.world.player
	check("抽屉闭合面板贴柜体且离地 78cm", level.drawer_root.position.is_equal_approx(Vector3(13.20, 0.78, -1.11)))
	level._toggle_drawer()
	level._toggle_drawer()
	check("动画中重复按键不会反转 / 提前拿纸", level.drawer_open and level.drawer_moving and level.drawer_paper_area.collision_layer == 0)
	await create_timer(0.55).timeout
	check("拉开 30cm 后可取图", is_equal_approx(level.drawer_root.position.x, 13.50) and level.drawer_paper_area.collision_layer == 1)
	level._toggle_drawer()
	await create_timer(0.55).timeout
	check("抽屉推回原位、纸张不能隔柜拾取", is_equal_approx(level.drawer_root.position.x, 13.20) and level.drawer_paper_area.collision_layer == 0)
	level._toggle_drawer()
	await create_timer(0.55).timeout
	await physics_frame
	var ray := PhysicsRayQueryParameters3D.create(Vector3(13.9, 1.6, -1.11), level.drawer_paper.global_position)
	ray.collide_with_areas = true
	var hit = level.get_world_3d().direct_space_state.intersect_ray(ray)
	check("玩家站在柜前能直接选中纸张", not hit.is_empty() and hit.collider == level.drawer_paper_area)
	director.world.player.frozen = false
	level._take_diagram()
	await frame()
	var viewer = level._plan_viewer
	check("拿图后持续打开、冻结走动", level.blueprint_open and director.world.player.frozen)
	await create_timer(1.0).timeout
	check("等待后仍保留图纸", level.blueprint_open and is_instance_valid(viewer))
	if DisplayServer.get_name() != "headless":
		await RenderingServer.frame_post_draw
		root.get_texture().get_image().save_png("/tmp/table-plan-fit.png")
	var wheel := InputEventMouseButton.new()
	wheel.button_index = MOUSE_BUTTON_WHEEL_UP
	wheel.pressed = true
	root.push_input(wheel, true)
	check("滚轮输入实际放大", viewer.zoom > 1.0)
	viewer.set_zoom(2.0)
	check("可放大到 200%", is_equal_approx(viewer.zoom, 2.0))
	viewer.pan = Vector2(100000, 100000)
	viewer._layout()
	check("平移有边界，不会丢失整张图", viewer.pan.length() < 5000)
	if DisplayServer.get_name() != "headless":
		await RenderingServer.frame_post_draw
		root.get_texture().get_image().save_png("/tmp/table-plan-zoom.png")
	var close_key := InputEventKey.new()
	close_key.physical_keycode = KEY_Q
	close_key.pressed = true
	root.push_input(close_key, true)
	await frame()
	check("收起恢复玩家、可再次 Q 重看", not level.blueprint_open and not director.world.player.frozen)
	level._open_blueprint()
	await frame()
	check("再次打开回到完整图", level.blueprint_open and is_equal_approx(level._plan_viewer.zoom, 1.0))
	level._plan_viewer.close()
	await frame()
	if DisplayServer.get_name() != "headless":
		var review_camera := Camera3D.new()
		level.add_child(review_camera)
		review_camera.global_position = Vector3(14.2, 1.35, -2.8)
		review_camera.look_at(Vector3(13.0, 0.48, -1.11))
		review_camera.current = true
		await frame(4)
		await RenderingServer.frame_post_draw
		root.get_texture().get_image().save_png("/tmp/table-cabinet.png")
	level._open_blueprint()
	await frame()
	level._finish()
	await frame()
	check("看图中退出关卡也会关闭图纸并归还玩家", director.world._sublevel == null and director.world.player.interaction_owner == null and not director.world.player.frozen)
	print("TABLE_PLAN failures=", failures)
	quit(1 if failures else 0)
