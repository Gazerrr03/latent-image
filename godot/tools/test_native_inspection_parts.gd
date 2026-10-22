extends SceneTree
## 真实导入家具材质面拆分与场景/笔记本一致性；不写玩家存档。
var Catalog: GDScript
var failures := 0
func _initialize(): call_deferred("run")
func check(label: String, ok: bool):
	print("PASS " if ok else "FAIL ", label)
	if not ok: failures += 1
func inspect_group(director, id := "hs_con_sweater"):
	await director._inspect([id], "walk")
func wait_for_inspector(director):
	for frame in 180:
		if director.ui.inspector.active:
			await create_timer(0.3).timeout
			return
		await process_frame
func measure_performance(id: String):
	await create_timer(2.0).timeout
	var frames: Array[float] = []
	var start := Time.get_ticks_usec()
	var last := start
	while Time.get_ticks_usec() - start < 5000000:
		await process_frame
		var now := Time.get_ticks_usec()
		frames.append((now - last) / 1000.0)
		last = now
	frames.sort()
	var fps := frames.size() * 1000000.0 / (last - start)
	print("NATIVE_INSPECTION_PERF ", JSON.stringify({"gpu":RenderingServer.get_video_adapter_name(),"viewport":str(root.size),"object":id,"fps":fps,"p99_ms":frames[int(frames.size()*.99)],"samples":frames.size()}))
	check(id + " 检视短时均值达到45帧",fps >= 45.0)

func run():
	root.get_node("GameState").persist = false
	var main = load("res://main.tscn").instantiate()
	root.add_child(main)
	await process_frame
	root.get_node("GameState").reset()
	Catalog = load("res://ui/inspection_catalog.gd")
	var director = root.get_node("Director")
	director.ui.menus.hide()
	var host = director.world
	host.show_scene("con_room")
	host.set_mode("walk", "")
	var data = Catalog.hotspot("hs_con_sweater",host)
	check("少年毛衣为真实便携网格",data.mode == "portable" and data.sources.size() == 1)
	if data.sources.size() != 1:
		quit(1)
		return
	var source: MeshInstance3D = data.sources[0]
	check("毛衣没有连衣柜一起复制",source.mesh.get_surface_count() == 2 and source.mesh.get_aabb().size.length() < 0.7 and source.mesh.get_faces().size() > 3000)
	var parent: MeshInstance3D = source.get_parent()
	check("衣柜原位保留其余四种材料",parent.mesh.get_surface_count() == 4 and source.transform == Transform3D.IDENTITY)
	var path = source.mesh.get_faces()
	director.ui.eyelids_set(1.0)
	director.ui.set_cinematic(false)
	for door in host.doors:
		if host.doors[door].get("container", false):
			host.toggle_door(door,Vector3(5.8,3.62,-7.25))
			await create_timer(0.9).timeout
	var samples = JSON.parse_string(FileAccess.get_file_as_string("res://../docs/验证/2026-10-20-物品检视/逐对象判定.json"))
	for row in samples:
		if row.id == "hs_con_sweater":
			var feet = row.feet
			host.player.place(Vector3(feet[0],feet[1],feet[2]),0)
	inspect_group(director)
	host.player.cam.look_at(host.hotspot_nodes["hs_con_sweater"].global_position)
	host.player._update_hover()
	check("真实开柜后提示毛衣",host.player._hover == "hs_con_sweater")
	print("NATIVE_INPUT before ",JSON.stringify({"active":host.player.active,"frozen":host.player.frozen,"busy":director.ui._busy(),"menus":director.ui.menus.visible,"pending":director._inspect_pending,"jump":director._jump_to}))
	var key = InputEventKey.new()
	key.physical_keycode = KEY_E
	key.keycode = KEY_E
	key.pressed = true
	root.push_input(key,true)
	key = key.duplicate()
	key.pressed = false
	root.push_input(key,true)
	await wait_for_inspector(director)
	print("NATIVE_INPUT after ",JSON.stringify({"inspector":director.ui.inspector.active,"menus":director.ui.menus.visible,"frozen":host.player.frozen,"inspected":root.get_node("GameState").inspected,"jump":director._jump_to}))
	check("毛衣从原件方向浮出",director.ui.inspector._entry_basis.is_equal_approx(host.player.cam.global_basis.inverse().orthonormalized() * source.global_basis.orthonormalized()))
	check("拿起只隐藏毛衣且衣柜仍在",director.ui.inspector._portable and not source.visible and parent.visible)
	if OS.get_cmdline_user_args().has("--performance"):
		await measure_performance("ev_sweater")
	if DisplayServer.get_name() != "headless":
		await RenderingServer.frame_post_draw
		root.get_texture().get_image().save_png("/tmp/dm-native-sweater.png")
	director.ui.inspector.close(true)
	check("放下恢复毛衣",source.visible and parent.visible)
	check("真实E路径收集毛衣一次",root.get_node("GameState").evidence.has("ev_sweater") and root.get_node("GameState").inspected.count("hs_con_sweater") == 1)
	host.show_scene("guest_room")
	var notebook = Catalog.evidence("ev_sweater",host,"","")
	check("跨房间笔记本读取同一毛衣几何",notebook.mode == "portable" and notebook.visuals.size() == 1 and notebook.visuals[0].mesh.get_faces() == path)
	var shoes = Catalog.hotspot("hs_shoes",host)
	check("皮鞋为独立实物而非整个衣柜",shoes.mode == "portable" and shoes.sources.size() == 1 and shoes.sources[0].mesh.get_surface_count() == 4)
	if shoes.sources.is_empty():
		quit(1)
		return
	var shoe_source: MeshInstance3D = shoes.sources[0]
	var shoe_parent: MeshInstance3D = shoe_source.get_parent()
	check("衣柜保留大衣和帽盒",shoe_parent.mesh.get_surface_count() == 4 and shoe_parent.visible)
	for row in samples:
		if row.id == "hs_shoes":
			var feet = row.feet
			host.player.place(Vector3(feet[0],feet[1],feet[2]),0)
	inspect_group(director,"hs_shoes")
	host.player.cam.look_at(host.hotspot_nodes["hs_shoes"].global_position)
	host.player._update_hover()
	check("真实站位提示皮鞋",host.player._hover == "hs_shoes")
	key = InputEventKey.new()
	key.physical_keycode = KEY_E
	key.keycode = KEY_E
	key.pressed = true
	root.push_input(key,true)
	key = key.duplicate()
	key.pressed = false
	root.push_input(key,true)
	await wait_for_inspector(director)
	check("皮鞋从原件方向浮出",director.ui.inspector._entry_basis.is_equal_approx(host.player.cam.global_basis.inverse().orthonormalized() * shoe_source.global_basis.orthonormalized()))
	check("真实E拿起皮鞋且原衣柜仍在",director.ui.inspector._portable and not shoe_source.visible and shoe_parent.visible)
	if OS.get_cmdline_user_args().has("--performance"):
		await measure_performance("ev_shoes")
	if DisplayServer.get_name() != "headless":
		await RenderingServer.frame_post_draw
		root.get_texture().get_image().save_png("/tmp/dm-native-shoes-front.png")
	var has_mud := false
	for node in director.ui.inspector._model.find_children("*","MeshInstance3D",true,false):
		for surface in node.mesh.get_surface_count():
			var mat: Material = node.get_active_material(surface)
			if mat.resource_name == "鞋底干泥":has_mud = true
	check("鞋底有独立真实干泥材质与几何",has_mud)
	director.ui.inspector._spin.y = PI
	director.ui.inspector._apply_rotation()
	if DisplayServer.get_name() != "headless":
		await RenderingServer.frame_post_draw
		root.get_texture().get_image().save_png("/tmp/dm-native-shoes-sole.png")
	director.ui.inspector.close(true)
	check("放下皮鞋恢复且只记录一次",shoe_source.visible and root.get_node("GameState").inspected.count("hs_shoes") == 1)
	var shoe_faces = shoe_source.mesh.get_faces()
	host.show_scene("darkroom")
	var shoe_notebook = Catalog.evidence("ev_shoe_mud",host,"","")
	check("异地笔记本皮鞋几何一致",shoe_notebook.visuals.size() == 1 and shoe_notebook.visuals[0].mesh.get_faces() == shoe_faces)
	print("NATIVE_PARTS failures=",failures)
	main.queue_free()
	await process_frame
	await process_frame
	quit(0 if failures == 0 else 1)
