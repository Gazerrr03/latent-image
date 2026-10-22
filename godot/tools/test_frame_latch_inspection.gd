extends SceneTree
var failures:=0
func _initialize():call_deferred("run")
func check(label:String,ok:bool):
	print("PASS " if ok else "FAIL ",label)
	if not ok:failures+=1
func key(code:Key):
	var e:=InputEventKey.new();e.keycode=code;e.physical_keycode=code;e.pressed=true
	root.push_input(e,true);e=e.duplicate();e.pressed=false;root.push_input(e,true)
func group(director,id):await director._inspect([id],"walk")
func mesh_named(host,base,name:String):
	for n in host._walk(base):
		if n is MeshInstance3D and String(n.name)==name:return n
	return null
func point_key(p:Vector3)->String:return str(Vector3i(roundi(p.x*10000),roundi(p.y*10000),roundi(p.z*10000)))
func faces(node:MeshInstance3D)->Dictionary:
	var out:={};var points:PackedVector3Array=node.mesh.get_faces()
	for i in range(0,points.size(),3):
		var keys:Array[String]=[]
		for j in 3:keys.append(point_key(node.global_transform*points[i+j]))
		keys.sort();out["|".join(keys)]=true
	return out
func run():
	root.get_node("GameState").persist=false
	var main=load("res://main.tscn").instantiate();root.add_child(main);await process_frame
	create_timer(120).timeout.connect(func():printerr("FRAME_LATCH timeout");quit(2))
	var state=root.get_node("GameState");state.reset()
	var director=root.get_node("Director");var host=director.world;var ui=director.ui;var viewer=ui.inspector
	ui.menus.hide();ui.eyelids_set(1.0);ui.set_cinematic(false)
	var samples=JSON.parse_string(FileAccess.get_file_as_string("res://../docs/验证/2026-10-20-物品检视/逐对象判定.json"))
	for item in [["archive","C2-05","hs_doorframe","二楼·储物间门框上的身高刻痕（L_）","doorframe_review.glb"],["greenhouse","C4-03","hs_gh_latch","暗房·侧门插销扣","latch_review.tscn"]]:
		var rid:String=item[0];var shot:String=item[1];var id:String=item[2];var name:String=item[3];var asset:String=item[4]
		host.show_scene(rid);host.apply_room_states(shot);host.set_mode("walk","")
		var source=mesh_named(host,host.room,name)
		var review=load("res://art/props/inspection/"+asset).instantiate();root.add_child(review)
		var duplicate=mesh_named(host,review,name)
		check(id+"复查保留真实痕迹网格",source!=null and duplicate!=null)
		if source==null or duplicate==null:
			for base in [host.room,review]:
				for n in host._walk(base):
					if n is MeshInstance3D and ("刻痕" in n.name or "插销" in n.name):print("MESH_NAME ",n.name)
			quit(1);return
		var expected=faces(source);var actual=faces(duplicate)
		check(id+"原痕迹三角面坐标全部保留",expected.size()>0 and expected.keys().all(func(k):return actual.has(k)))
		print("FRAME_LATCH_GEOMETRY ",id," verified=",expected.size())
		if id=="hs_gh_latch":
			var fiber: MeshInstance3D
			for n in host._walk(host.room):
				if n.get_script()==preload("res://world/inspection_fiber.gd"):fiber=n.get_child(0)
			var copy=review.get_node("现场同源呢子线头").get_child(0)
			var ink=faces(fiber);var ink_copy=faces(copy)
			check("现场与复查线头所有真实三角面相同",ink.size()>0 and ink.size()==ink_copy.size() and ink.keys().all(func(k):return ink_copy.has(k)))
		review.queue_free();await process_frame
		for row in samples:
			if row.id==id:host.player.place(Vector3(row.feet[0],row.feet[1],row.feet[2]),0)
		await physics_frame;await physics_frame
		group(director,id)
		host.player.cam.look_at(host.hotspot_nodes[id].global_position);host.player._update_hover()
		if id=="hs_gh_latch" and host.player._door!=null:
			key(KEY_E);await create_timer(.9).timeout
			host.player.cam.look_at(host.hotspot_nodes[id].global_position);host.player._update_hover()
		check(id+"自然站位提示一致",host.player._hover==id)
		var before:Transform3D=host.player.cam.global_transform
		key(KEY_E)
		for i in 180:
			if viewer.active:break
			await process_frame
		await create_timer(.35).timeout
		check(id+"真实E打开原位固定特写",viewer.active and not viewer._portable and source.is_visible_in_tree())
		if not viewer.active:quit(1);return
		check(id+"细节照明开启",is_instance_valid(viewer._inspection_light))
		if DisplayServer.get_name()!="headless":
			await RenderingServer.frame_post_draw
			root.get_texture().get_image().save_png("/tmp/dm-frame-latch-"+id+".png")
		key(KEY_ESCAPE)
		for i in 180:
			if not viewer.active:break
			await process_frame
		check(id+"退出恢复原相机和行动且只记一次",not host.player.frozen and host.player.cam.global_transform.is_equal_approx(before) and state.inspected.count(id)==1)
	print("FRAME_LATCH failures=",failures)
	main.queue_free();await process_frame;quit(0 if failures==0 else 1)
