extends SceneTree
## Real scenes and actual input dispatch; capture the emitted object ID without starting a story group.
var failures:=0
var emitted:Array=[]
func _initialize():call_deferred("run")
func check(label:String,ok:bool):
	print("PASS " if ok else "FAIL ",label)
	if not ok:failures+=1
func key(echo:=false):
	var e:=InputEventKey.new();e.keycode=KEY_E;e.physical_keycode=KEY_E;e.pressed=true;e.echo=echo
	root.push_input(e,true)
	if not echo:e=e.duplicate();e.pressed=false;root.push_input(e,true)
func run():
	root.get_node("GameState").persist=false
	var main=load("res://main.tscn").instantiate();root.add_child(main);await process_frame
	create_timer(120).timeout.connect(func():printerr("ROUTING timeout");quit(2))
	var state=root.get_node("GameState");state.reset()
	var director=root.get_node("Director");var host=director.world;var ui=director.ui
	director.inspected.connect(func(id):emitted.append(id))
	ui.menus.hide();ui.eyelids_set(1.0);ui.set_cinematic(false)
	var saved=JSON.parse_string(FileAccess.get_file_as_string("res://../docs/验证/2026-10-20-物品检视/逐对象判定.json"))
	for item in [["guest_room","C0-11","hs_notebook"],["amb_room","C1-05","hs_amb_notes"],["con_room","C2-04","hs_con_ledger"]]:
		var room:String=item[0];var shot:String=item[1];var id:String=item[2]
		host.show_scene(room);host.apply_room_states(shot);host.set_mode("walk","")
		host.highlight_hotspots([id])
		for row in saved:
			if row.id==id:host.player.place(Vector3(row.feet[0],row.feet[1],row.feet[2]),0)
		await physics_frame;await physics_frame
		var target:Node3D=host.hotspot_nodes[id]
		host.player.cam.look_at(target.global_position);host.player._update_hover()
		check(id+"当前提示是实际目标",host.player._hover==id)
		emitted.clear();key()
		check(id+"E只发出已提示的目标",emitted==[id])
		for i in 8:key(true)
		check(id+"按住E的回声不重复执行",emitted==[id])
		emitted.clear();target.hide();key()
		check(id+"同帧隐藏后E不执行旧目标",emitted.is_empty() and host.player._hover!=id)
		target.show();key()
		check(id+"同帧重现仅刷新提示",emitted.is_empty() and host.player._hover==id)
		key();check(id+"确认新提示后才执行",emitted==[id])
		if id=="hs_notebook":
			var neighbor:Node3D=host.hotspot_nodes["hs_typewriter"]
			host.highlight_hotspots([id,"hs_typewriter"])
			host.player.cam.look_at(target.global_position);host.player._update_hover();emitted.clear()
			host.player.cam.look_at(neighbor.global_position);key()
			check("瞄向邻物同帧按E只刷新不误执行",emitted.is_empty() and host.player._hover=="hs_typewriter")
			key();check("下一次E执行新提示的打字机",emitted==["hs_typewriter"])
	check("路由检查没有伪造证据或已检视记录",state.evidence.is_empty() and state.inspected.is_empty())
	print("INTERACTION_ROUTING failures=",failures)
	main.queue_free();await process_frame;quit(0 if failures==0 else 1)
