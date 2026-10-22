extends SceneTree
var failures:=0
func _initialize():call_deferred("run")
func check(label: String,ok: bool):
	print("PASS " if ok else "FAIL ",label)
	if not ok:failures+=1
func key(code: Key):
	var event:=InputEventKey.new();event.keycode=code;event.physical_keycode=code;event.pressed=true
	root.push_input(event,true);event=event.duplicate();event.pressed=false;root.push_input(event,true)
func wheel():
	var event:=InputEventMouseButton.new();event.button_index=MOUSE_BUTTON_WHEEL_UP;event.pressed=true;event.position=Vector2(600,300)
	root.push_input(event,true)
func drag():
	var event:=InputEventMouseButton.new();event.button_index=MOUSE_BUTTON_LEFT;event.pressed=true;event.position=Vector2(600,300)
	root.push_input(event,true)
	var motion:=InputEventMouseMotion.new();motion.relative=Vector2(40,15);motion.position=Vector2(640,315)
	root.push_input(motion,true);event.pressed=false;root.push_input(event,true)
func run():
	root.get_node("GameState").persist=false
	var main=load("res://main.tscn").instantiate();root.add_child(main);await process_frame
	create_timer(120).timeout.connect(func():printerr("FIXED_NOTEBOOK timeout");quit(2))
	var state=root.get_node("GameState");state.reset()
	var director=root.get_node("Director");var host=director.world;var ui=director.ui;var viewer=ui.inspector
	ui.menus.hide();ui.set_cinematic(false);ui.eyelids_set(1.0)
<<<<<<< HEAD
	var assets={"ev_tray_crystal":"tray_crystals.glb","ev_bottle_moved":"cabinet_clue.glb","ev_vent_cloth":"garden_vent_review.glb","ev_vent_print":"garden_print_review.glb","ev_doorframe_l":"doorframe_review.glb","ev_latch_thread":"latch_review.tscn","ev_corridor_hook":"corridor_hook_review.glb","ev_corridor_circle":"corridor_circle_review.glb","ev_corridor_window":"corridor_window_review.glb"}
=======
	var assets={"ev_tray_crystal":"tray_crystals.glb","ev_bottle_moved":"cabinet_clue.glb","ev_vent_cloth":"garden_vent_review.glb","ev_vent_print":"garden_print_review.glb","ev_doorframe_l":"doorframe_review.glb","ev_latch_thread":"latch_review.tscn"}
>>>>>>> codex/snapshot-source-20261022-1
	for id in assets:state.add_evidence(id)
	host.show_scene("guest_room");host.set_mode("walk","")
	var before=host.player.cam.global_transform
	var before_fov=host.player.cam.fov
	ui.browse_board();await process_frame
	for id in assets:
		ui.board.examine(id)
		for i in 180:
			if viewer.active:break
			await process_frame
		await create_timer(.35).timeout
		check(id+"笔记本打开真实现场复查",viewer.active and viewer._scene_view and viewer._portable and not viewer.reading and viewer._model!=null)
		if not viewer.active:quit(1);return
		check(id+"读取原派生网格而非通用卡片",viewer._model.scene_file_path.ends_with(assets[id]) and viewer._sources.is_empty())
		check(id+"明确返回笔记本而不是放下固定物",viewer._put_down_button.text=="返回" and viewer._hint.text.contains("返回笔记本"))
		if DisplayServer.get_name()!="headless":
			await RenderingServer.frame_post_draw
			root.get_texture().get_image().save_png("/tmp/dm-notebook-"+id+".png")
		wheel();drag();await process_frame
		var rotation: Basis=viewer._pivot.basis;var zoom: float=viewer._zoom
		check(id+"真实输入可旋转和缩放现场",zoom>1.0 and viewer._spin.length()>0.1)
		key(KEY_F);await process_frame
		check(id+"F阅读既有观察记录",viewer.reading and not viewer._text.text.is_empty())
		key(KEY_ESCAPE);await process_frame
		check(id+"Esc从阅读回现场保留观察状态",viewer.active and not viewer.reading and viewer._pivot.basis.is_equal_approx(rotation) and is_equal_approx(viewer._zoom,zoom))
		key(KEY_R);await process_frame
		check(id+"R复位默认构图",is_equal_approx(viewer._zoom,1.0) and viewer._spin.is_zero_approx())
		key(KEY_ESCAPE)
		for i in 180:
			if not viewer.active:break
			await process_frame
		check(id+"关闭返回原笔记本且角色仍冻结",not viewer.active and ui.board.visible and host.player.frozen)
	check("复查不增加收集记录或移动当前房间",state.evidence.size()==assets.size() and state.inspected.is_empty() and host.player.cam.global_transform.is_equal_approx(before) and is_equal_approx(host.player.cam.fov,before_fov))
	ui.board.close();await process_frame
	check("合上笔记本恢复行动",not ui.board.visible and not host.player.frozen)
	host.show_scene("darkroom");host.apply_room_states("C1-05");host.set_mode("walk", "")
	var native: MeshInstance3D
	for node in host._walk(host.room):
		if node is MeshInstance3D and String(node.name)=="暗房·药品柜":native=node
	ui.inspect_evidence("ev_bottle_moved","", "")
	await create_timer(.35).timeout
	check("同房间复查也不隐藏或拿走真实药柜",viewer.active and viewer._scene_view and native!=null and native.is_visible_in_tree() and viewer._sources.is_empty())
	viewer.close(true)
	check("重复复查保持原收集数",state.evidence.size()==assets.size() and state.inspected.is_empty())
	print("FIXED_NOTEBOOK failures=",failures)
	main.queue_free();await process_frame;quit(0 if failures==0 else 1)
