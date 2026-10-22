extends SceneTree
## Four authentic sources can be opened/read/flipped from the notebook.
var failures := 0
func _initialize():call_deferred("run")
func check(label: String, ok: bool):
	print("PASS " if ok else "FAIL ",label)
	if not ok:failures+=1
func key(code: Key):
	var e:=InputEventKey.new();e.keycode=code;e.physical_keycode=code;e.pressed=true
	root.push_input(e,true);e=e.duplicate();e.pressed=false;root.push_input(e,true)
func run():
	root.get_node("GameState").persist=false
	var main=load("res://main.tscn").instantiate();root.add_child(main);await process_frame
	create_timer(120).timeout.connect(func():printerr("HANDWRITING timeout");quit(2))
	var state=root.get_node("GameState");state.reset()
	var director=root.get_node("Director");var host=director.world;var ui=director.ui;var viewer=ui.inspector
	ui.menus.hide();ui.eyelids_set(1.0);ui.set_cinematic(false)
	host.show_scene("guest_room");host.set_mode("walk","")
	var originals={"ev_receipt":"药房签收单","ev_con_ledger":"1920 年 5 月","ev_seance_cards":"彭罗斯","ev_amb_notes":"星期六，格雷来。"}
	for id in originals:state.add_evidence(id)
	ui.browse_board();await process_frame
	for id in originals:
		ui.board.examine(id)
		for i in 180:
			if viewer.active:break
			await process_frame
		await create_timer(.35).timeout
		check(id+"打开真实可翻面纸张",viewer.active and viewer._portable and not viewer.reading and viewer._model!=null and viewer._model.object_id==id)
		if not viewer.active:quit(1);return
		if id=="ev_seance_cards":
			key(KEY_D);await create_timer(.3).timeout
			check("第二张卡片真实换页",viewer._model.page==1)
		if DisplayServer.get_name()!="headless":
			await RenderingServer.frame_post_draw
			root.get_texture().get_image().save_png("/tmp/dm-handwriting-"+id+".png")
		key(KEY_F);await process_frame
		var expected: String="索尔特" if id=="ev_seance_cards" else originals[id]
		check(id+"英文实物与中文阅读分离",viewer.reading and viewer._text.text.contains(expected))
		if id=="ev_receipt":
			check("签收单中文列出用户授权的四项品名瓶数",viewer._text.text.contains("显影液　2 瓶") and viewer._text.text.contains("停显液　1 瓶") and viewer._text.text.contains("定影液　1 瓶") and viewer._text.text.contains("专用调色液　1 瓶"))
		key(KEY_ESCAPE);await process_frame
		check(id+"关闭阅读仍保留实物",viewer.active and not viewer.reading)
		key(KEY_ESCAPE)
		for i in 180:
			if not viewer.active:break
			await process_frame
		check(id+"返回笔记本",not viewer.active and ui.board.visible)
	check("复查不重复收集或触发现场",state.evidence.size()==4 and state.inspected.is_empty())
	print("HANDWRITING failures=",failures)
	main.queue_free();await process_frame;quit(0 if failures==0 else 1)
