extends SceneTree
## End-to-end comparison: chapter gate, actual five sources, E, and notebook replay.
var failures := 0
func _initialize():call_deferred("run")
func check(label: String, ok: bool):
	print("PASS " if ok else "FAIL ",label)
	if not ok:failures+=1
func key(code: Key):
	var e:=InputEventKey.new();e.keycode=code;e.physical_keycode=code;e.pressed=true
	root.push_input(e,true);e=e.duplicate();e.pressed=false;root.push_input(e,true)
func group(director):await director._inspect(["hs_handwriting"],"walk")
func run():
	root.get_node("GameState").persist=false
	var main=load("res://main.tscn").instantiate();root.add_child(main);await process_frame
	create_timer(120).timeout.connect(func():printerr("SPREAD timeout");quit(2))
	var state=root.get_node("GameState");state.reset()
	var director=root.get_node("Director");var host=director.world;var ui=director.ui;var viewer=ui.inspector
	ui.menus.hide();ui.eyelids_set(1.0);ui.set_cinematic(false)
	host.show_scene("guest_room");host.set_mode("walk","")
	var spread: Node3D=host.named.get("层·笔迹比对")
	if spread==null:spread=host.named.get("guest_room/层·笔迹比对")
	check("在原客房书桌接入五份实物",spread!=null and spread.get_child_count()==5)
	if spread==null:quit(1);return
	host.apply_room_states("C0-11")
	check("早期探索不提前显示晚期比对",not spread.is_visible_in_tree())
	host.apply_room_states("C5-14")
	check("第五章去客房之前仍未摊字",not spread.is_visible_in_tree())
	host.apply_room_states("C5-08")
	check("摊字镜号才显示原位实物",spread.is_visible_in_tree())
	check("直接复用已检视过的四份纸张和自己的笔记",spread.get_node("ledger").object_id=="ev_con_ledger" and spread.get_node("receipt").object_id=="ev_receipt" and spread.get_node("card").object_id=="ev_seance_cards" and spread.get_node("ambrose").object_id=="ev_amb_notes" and spread.get_node("grey").object_id=="prop_grey_notebook")
	check("五份纸张朝上平放在桌上",spread.get_children().all(func(p): return p.front.global_basis.z.dot(Vector3.UP)>.99))
	check("降灵卡片展示真正含小写t的Salter页",spread.get_node("card").page==1)
	var samples=JSON.parse_string(FileAccess.get_file_as_string("res://../docs/验证/2026-10-20-物品检视/逐对象判定.json"))
	for row in samples:
		if row.id=="hs_handwriting":host.player.place(Vector3(row.feet[0],row.feet[1],row.feet[2]),0)
	await physics_frame;await physics_frame
	group(director)
	host.player.cam.look_at(host.hotspot_nodes["hs_handwriting"].global_position);host.player._update_hover()
	check("原可站立位置提示摊开的字",host.player._hover=="hs_handwriting")
	var before: Transform3D=host.player.cam.global_transform
	key(KEY_E)
	for i in 180:
		if viewer.active:break
		await process_frame
	await create_timer(.35).timeout
	check("真实E保留原位五源关系的特写",viewer.active and not viewer._portable and spread.is_visible_in_tree())
	if not viewer.active:quit(1);return
	if DisplayServer.get_name()!="headless":
		await RenderingServer.frame_post_draw
		root.get_texture().get_image().save_png("/tmp/dm-handwriting-spread-onsite.png")
	for i in 8:
		var wheel:=InputEventMouseButton.new();wheel.button_index=MOUSE_BUTTON_WHEEL_UP;wheel.pressed=true;root.push_input(wheel,true)
	await process_frame
	check("现场可进一步放大笔迹",viewer._zoom>1.5)
	if DisplayServer.get_name()!="headless":
		await RenderingServer.frame_post_draw
		root.get_texture().get_image().save_png("/tmp/dm-handwriting-spread-onsite-zoom.png")
	key(KEY_R);key(KEY_F);await process_frame
	check("观察记录仍是既有五源推论",viewer.reading and viewer._text.text.contains("我自己的") and viewer._text.text.contains("康斯坦斯") and viewer._text.text.contains("吉迪恩") and viewer._text.text.contains("拉坦特") and viewer._text.text.contains("安布罗斯") and viewer._text.text.contains("竖画"))
	key(KEY_ESCAPE);key(KEY_ESCAPE)
	for i in 180:
		if not viewer.active:break
		await process_frame
	check("退出恢复相机与行走且只记录一次",not viewer.active and not host.player.frozen and host.player.cam.global_transform.is_equal_approx(before) and state.inspected.count("hs_handwriting")==1 and state.evidence.count("ev_t_cross")==1)
	host.show_scene("hall");host.set_mode("walk","");ui.browse_board();await process_frame
	ui.board.examine("ev_t_cross")
	for i in 180:
		if viewer.active:break
		await process_frame
	await create_timer(.35).timeout
	check("异地笔记本仍展示同一五份实物",viewer.active and viewer._scene_view and viewer._model!=null and viewer._model.get_child_count()==5)
	check("复查卡片保持含t的第二页",viewer._model.get_node("card").page==1)
	if DisplayServer.get_name()!="headless":
		await RenderingServer.frame_post_draw
		root.get_texture().get_image().save_png("/tmp/dm-handwriting-spread-notebook.png")
	for i in 8:
		var wheel:=InputEventMouseButton.new();wheel.button_index=MOUSE_BUTTON_WHEEL_UP;wheel.pressed=true;root.push_input(wheel,true)
	await process_frame
	check("复查可放大同组笔迹",viewer._zoom>1.5)
	if DisplayServer.get_name()!="headless":
		await RenderingServer.frame_post_draw
		root.get_texture().get_image().save_png("/tmp/dm-handwriting-spread-notebook-zoom.png")
	viewer.close(true)
	check("笔记本复查不重记或增发五份证据",state.inspected.count("hs_handwriting")==1 and state.evidence.size()==1 and ui.board.visible)
	print("HANDWRITING_SPREAD failures=",failures)
	main.queue_free();await process_frame;quit(0 if failures==0 else 1)
