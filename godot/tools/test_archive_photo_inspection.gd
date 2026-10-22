extends SceneTree
## 年度编号与容器编号分离；原书桌只拿起照片，真实E/翻面/阅读/放回。
var failures := 0
func _initialize():call_deferred("run")
func check(label: String, ok: bool):
	print("PASS " if ok else "FAIL ",label)
	if not ok:failures += 1
func key(code: Key):
	var event := InputEventKey.new()
	event.keycode=code;event.physical_keycode=code;event.pressed=true
	root.push_input(event,true)
	event=event.duplicate();event.pressed=false;root.push_input(event,true)
func group(director):await director._inspect(["hs_photo_back"],"walk")
func run():
	root.get_node("GameState").persist=false
	var main=load("res://main.tscn").instantiate();root.add_child(main)
	await process_frame
	create_timer(120).timeout.connect(func():printerr("ARCHIVE_PHOTO timeout");quit(2))
	var state=root.get_node("GameState");state.reset();state.container="03"
	var director=root.get_node("Director");var host=director.world;var ui=director.ui
	ui.menus.hide();ui.eyelids_set(1.0);ui.set_cinematic(false)
	host.show_scene("archive");host.set_mode("walk","")
	var source: MeshInstance3D
	for node in host._walk(host.room):
		if node is MeshInstance3D and node.has_meta("inspection_document"):source=node
	check("书桌中只拆出原照片并接入双面实物",source!=null and source.get_meta("inspection_part","")=="manor_室内_照片背面")
	if source==null:quit(1);return
	var document=source.get_meta("inspection_document")
	check("放在书桌上仍是背面朝上",document.back.global_basis.z.dot(Vector3.UP)>.99)
	var rows=JSON.parse_string(FileAccess.get_file_as_string("res://../docs/验证/2026-10-20-物品检视/逐对象判定.json"))
	for row in rows:
		if row.id=="hs_photo_back":host.player.place(Vector3(row.feet[0],row.feet[1],row.feet[2]),0)
	await physics_frame;await physics_frame
	group(director)
	host.player.cam.look_at(host.hotspot_nodes["hs_photo_back"].global_position);host.player._update_hover()
	check("自然站位提示目标是档案室照片",host.player._hover=="hs_photo_back")
	key(KEY_E)
	for i in 180:
		if ui.inspector.active:break
		await process_frame
	await create_timer(.4).timeout
	var viewer=ui.inspector
	check("真实E拿起照片且默认背面",viewer.active and viewer._portable and viewer._flipped and viewer._model!=null)
	if not viewer.active:quit(1);return
	check("照片离桌而其余底片簿放大镜仍在",not document.back.is_visible_in_tree() and source.get_parent().layers!=0)
	if DisplayServer.get_name()!="headless":
		await RenderingServer.frame_post_draw
		root.get_texture().get_image().save_png("/tmp/dm-archive-photo-back.png")
	key(KEY_F);await process_frame
	check("阅读实物编号08且不跟随容器03",viewer.reading and viewer._text.text=="08")
	key(KEY_ESCAPE);key(KEY_V);await create_timer(.3).timeout
	check("翻至合影正面",not viewer._flipped and viewer._model.front.material_override.albedo_texture!=null)
	key(KEY_R);await process_frame
	check("复位回手写编号一侧",viewer._flipped)
	viewer.close(true)
	check("放回原位且不增加虚构证据",document.back.is_visible_in_tree() and state.inspected.count("hs_photo_back")==1 and not state.evidence.has("prop_photo_1926"))
	host.show_scene("guest_room")
	var data=load("res://ui/inspection_catalog.gd").hotspot("hs_photo_back",host,true)
	check("跨房间复查保持同一实物及固定编号",data.asset.ends_with("prop_photo_1926.tscn") and data.back_pages==["08"] and data.sources.is_empty())
	main.queue_free();await process_frame
	print("ARCHIVE_PHOTO failures=",failures);quit(0 if failures==0 else 1)
