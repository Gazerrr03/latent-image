extends SceneTree
## 实际药柜：原柜几何、自然站位、真实 E、原位特写和退出恢复。
var failures := 0
func _initialize():call_deferred("run")
func check(label: String,ok: bool):
	print("PASS " if ok else "FAIL ",label)
	if not ok:failures+=1
func group(director):await director._inspect(["hs_bottles"],"walk")
func triangle(points: PackedVector3Array,index: int) -> String:
	var keys: Array[String] = []
	for i in 3:
		var p: Vector3 = points[index+i]
		keys.append(str(Vector3i(roundi(p.x*10000),roundi(p.y*10000),roundi(p.z*10000))))
	keys.sort()
	return "|".join(keys)
func run():
	root.get_node("GameState").persist=false
	var main=load("res://main.tscn").instantiate()
	root.add_child(main)
	await process_frame
	root.get_node("GameState").reset()
	create_timer(120).timeout.connect(func():printerr("CABINET timeout");quit(2))
	var director=root.get_node("Director")
	var host=director.world
	var ui=director.ui
	ui.menus.hide();ui.eyelids_set(1.0);ui.set_cinematic(false)
	host.show_scene("darkroom");host.set_mode("walk","")
	var cabinet: MeshInstance3D
	for node in host._walk(host.room):
		if node is MeshInstance3D and String(node.name)=="暗房·药品柜":cabinet=node
	check("原柜子接入局部替换资源",cabinet!=null and cabinet.has_meta("inspection_replacement") and cabinet.mesh.get_surface_count()==11)
	if cabinet==null:quit(1);return
	var original=load("res://art/levels/manor/room_darkroom.gltf").instantiate()
	var raw: MeshInstance3D
	for node in host._walk(original):
		if node is MeshInstance3D and String(node.name)=="暗房·药品柜":raw=node
	for surface in cabinet.mesh.get_surface_count():
		var material=cabinet.mesh.surface_get_material(surface)
		if material.resource_name.contains("薄玻璃") or material.resource_name.contains("药液"):
			print("CABINET_MATERIAL ",material.resource_name," ",material.albedo_color," alpha=",material.transparency)
	var actual=cabinet.mesh.get_faces()
	var available={}
	for i in range(0,actual.size(),3):available[triangle(actual,i)]=true
	var old=raw.mesh.get_faces()
	var kept:=0
	var missing:=0
	for i in range(0,old.size(),3):
		var edited:=true
		for j in 3:
			var p: Vector3=old[i+j]
			edited=edited and p.x>=-.0351 and p.x<=.0267 and p.y>=1.1978 and p.y<=1.459 and p.z>=-.0364 and p.z<=.0256
		if not edited:
			kept+=1
			if not available.has(triangle(old,i)):missing+=1
	check("柜体搁板及其余瓶子真实三角面原位保留",kept>6000 and missing==0)
	print("CABINET_GEOMETRY ",JSON.stringify({"verified_triangles":kept,"missing":missing}))
	original.free()
	var samples=JSON.parse_string(FileAccess.get_file_as_string("res://../docs/验证/2026-10-20-物品检视/逐对象判定.json"))
	for row in samples:
		if row.id=="hs_bottles":
			var feet=row.feet
			host.player.place(Vector3(feet[0],feet[1],feet[2]),0)
	await physics_frame;await physics_frame
	group(director)
	host.player.cam.look_at(host.hotspot_nodes["hs_bottles"].global_position)
	host.player._update_hover()
	check("自然正面站位提示药柜",host.player._hover=="hs_bottles")
	var before=host.player.cam.global_transform
	var fov=host.player.cam.fov
	var event=InputEventKey.new();event.keycode=KEY_E;event.physical_keycode=KEY_E;event.pressed=true
	root.push_input(event,true);event=event.duplicate();event.pressed=false;root.push_input(event,true)
	for i in 180:
		if ui.inspector.active:break
		await process_frame
	await create_timer(.35).timeout
	check("真实E打开保留现场关系的固定特写",ui.inspector.active and not ui.inspector._portable and cabinet.visible)
	check("小瓶和原灰圈有局部照明与细节焦点",is_instance_valid(ui.inspector._inspection_light) and is_equal_approx(host.player.cam.fov,18.0) and ui.inspector._focus.y<4.95)
	if DisplayServer.get_name()!="headless":
		await RenderingServer.frame_post_draw
		root.get_texture().get_image().save_png("/tmp/dm-cabinet-inspection.png")
	ui.inspector.close(true)
	check("退出恢复现场视角与行动并只收集一次",not host.player.frozen and host.player.cam.global_transform.is_equal_approx(before) and is_equal_approx(host.player.cam.fov,fov) and root.get_node("GameState").inspected.count("hs_bottles")==1)
	print("CABINET_INSPECTION failures=",failures)
	main.queue_free();await process_frame;await process_frame
	quit(0 if failures==0 else 1)
