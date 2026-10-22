extends SceneTree
var failures:=0
func _initialize():call_deferred("run")
func check(label: String,ok: bool):
	print("PASS " if ok else "FAIL ",label)
	if not ok:failures+=1
func key():
	var e:=InputEventKey.new();e.keycode=KEY_E;e.physical_keycode=KEY_E;e.pressed=true
	root.push_input(e,true);e=e.duplicate();e.pressed=false;root.push_input(e,true)
func group(director,id):await director._inspect([id],"walk")
func run():
	root.get_node("GameState").persist=false
	var main=load("res://main.tscn").instantiate();root.add_child(main);await process_frame
	create_timer(120).timeout.connect(func():printerr("GARDEN_INSPECTION timeout");quit(2))
	var state=root.get_node("GameState");state.reset();state.shot="C4-03"
	var director=root.get_node("Director");var host=director.world;var ui=director.ui
	ui.menus.hide();ui.set_cinematic(false);ui.eyelids_set(1.0)
	host.show_scene("garden");host.apply_room_states("C4-03");host.set_mode("walk","")
	var samples=JSON.parse_string(FileAccess.get_file_as_string("res://../docs/验证/2026-10-20-物品检视/逐对象判定.json"))
	for id in ["hs_vent_print","hs_vent_louver"]:
		for row in samples:
			if row.id==id:host.player.place(Vector3(row.feet[0],row.feet[1],row.feet[2]),0)
		await physics_frame;await physics_frame
		group(director,id)
		host.player.cam.look_at(host.hotspot_nodes[id].global_position);host.player._update_hover()
		check(id+"自然站位提示一致",host.player._hover==id)
		var native_name="花园·泥地鞋印" if id=="hs_vent_print" else "花园·遮光布（堵着通风口）"
		var source: MeshInstance3D
		for node in host._walk(host.room):
			if node is MeshInstance3D and String(node.name)==native_name:source=node
		check(id+"原位实物存在并按章节显示",source!=null and source.is_visible_in_tree())
		if id=="hs_vent_louver":
			var original=load("res://art/levels/manor/room_garden__遮光布.gltf").instantiate()
			var native: MeshInstance3D=original.get_child(0) if original.get_child_count()>0 else null
			for node in host._walk(original):
				if node is MeshInstance3D:native=node
			check("遮光布补厚度和压边但保留原范围",source.has_meta("inspection_replacement") and source.mesh.get_faces().size()>30000 and source.mesh.get_aabb().is_equal_approx(native.mesh.get_aabb()))
			original.free()
		var before=host.player.cam.global_transform;var fov=host.player.cam.fov
		key()
		for i in 180:
			if ui.inspector.active:break
			await process_frame
		await create_timer(.35).timeout
		check(id+"真实E保留原件及现场关系",ui.inspector.active and not ui.inspector._portable and source.is_visible_in_tree())
		if DisplayServer.get_name()!="headless":
			await RenderingServer.frame_post_draw
			root.get_texture().get_image().save_png("/tmp/dm-garden-"+id+".png")
		ui.inspector.close(true)
		check(id+"退出恢复相机与输入",host.player.cam.global_transform.is_equal_approx(before) and is_equal_approx(host.player.cam.fov,fov) and not host.player.frozen)
		check(id+"只记一次并可重复入口",state.inspected.count(id)==1 and source.is_visible_in_tree())
	check("现场收集两条原有证据",state.evidence.has("ev_vent_print") and state.evidence.has("ev_vent_cloth"))
	print("GARDEN_INSPECTION failures=",failures)
	main.queue_free();await process_frame;quit(0 if failures==0 else 1)
