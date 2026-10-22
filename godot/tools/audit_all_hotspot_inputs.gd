extends SceneTree
## Actual E/F/Esc dispatch through Director and Inspector for every ordinary hotspot.
## Headless input/state regression; rendered appearance and continuous walking need separate evidence.
var failures:=0
var records:Array=[]
var group_done:=false
func _initialize():call_deferred("run")
func check(label:String,ok:bool):
	print("PASS " if ok else "FAIL ",label)
	if not ok:failures+=1
func key(code:Key):
	var e:=InputEventKey.new();e.keycode=code;e.physical_keycode=code;e.pressed=true
	root.push_input(e,true);e=e.duplicate();e.pressed=false;root.push_input(e,true)
func group(director,id):
	group_done=false;await director._inspect([id],"walk");group_done=true
func aim(host,target):
	var delta:Vector3=target.global_position-host.player.cam.global_position
	host.player.rotation.y=atan2(-delta.x,-delta.z)
	host.player._pitch=atan2(delta.y,Vector2(delta.x,delta.z).length())
	host.player.cam.look_at(target.global_position);host.player._update_hover()
func run():
	root.get_node("GameState").persist=false
	var main=load("res://main.tscn").instantiate();root.add_child(main);await process_frame
	create_timer(180).timeout.connect(func():printerr("ALL_INPUT timeout");quit(2))
	var state=root.get_node("GameState");state.reset()
	var director=root.get_node("Director");var host=director.world;var ui=director.ui;var viewer=ui.inspector
	ui.menus.hide();ui.eyelids_set(1.0);ui.set_cinematic(false)
	var samples=JSON.parse_string(FileAccess.get_file_as_string("res://../docs/验证/2026-10-20-物品检视/逐对象判定.json"))
	var filtered:=false
	for arg in OS.get_cmdline_user_args():
		if arg.begins_with("--only="):
			filtered=true
			var selected=arg.trim_prefix("--only=").split(",")
			samples=samples.filter(func(row):return selected.has(row.id))
	var modes:={}
	for row in root.get_node("ContentDB").load_table("res://content/visual/inspections.csv"):modes[row.hotspot]=row.mode
	var rooms:Array=[]
	for row in samples:
		if not rooms.has(row.room):rooms.append(row.room)
	for room in rooms:
		host.show_scene(room)
		var shot:String={"guest_room":"C6-02","darkroom":"C1-05","archive":"C2-03","con_room":"C2-04","child_room":"C3-04","greenhouse":"C4-03","seance":"C5-03"}.get(room,"C1-05")
		state.shot=shot;host.apply_room_states(shot);host.set_mode("walk","")
		for body in host.doors:
			var info:Dictionary=host.doors[body]
			if String(info["leaf"].name)=="暗房·温室侧门":
				if host.door_is_open(body)!=(room=="greenhouse"):host.toggle_door(body,info["leaf"].global_position+Vector3.RIGHT)
			elif info.get("container",false) and not host.door_is_open(body):host.toggle_door(body,info["leaf"].global_position-Vector3.RIGHT)
		await create_timer(.9).timeout
		for row in samples:
			if row.room!=room:continue
			var id:String=row.id;var target:Node3D=host.hotspot_nodes.get(id)
			if target==null:check(id+"真实目标存在",false);continue
			host.player.place(Vector3(row.feet[0],row.feet[1],row.feet[2]),0)
			await physics_frame;await physics_frame
			group(director,id);aim(host,target)
			check(id+"实际E提示命中",host.player._hover==id)
			if host.player._hover!=id:print("HOVER_DIAGNOSTIC ",id," picked=",host.player._hover," target=",host.player._target)
			var before:Transform3D=host.player.cam.global_transform
			var before_fov:float=host.player.cam.fov
			key(KEY_E);await create_timer(.26).timeout
			var opened:bool=viewer.active and viewer._data.get("hotspot", "")==id
			check(id+"实际E打开检视并冻结移动",opened and host.player.frozen)
			if not opened:
				if viewer.active:viewer.close(true)
				director.inspected.emit(director.CANCEL);await process_frame;continue
			if DisplayServer.get_name()!="headless":
				await RenderingServer.frame_post_draw
				root.get_texture().get_image().save_png("/tmp/dm-all-input-"+id+".png")
			var returned:={}
			viewer.closed.connect(func():
				returned["camera"]=host.player.cam.global_transform
				returned["fov"]=host.player.cam.fov,CONNECT_ONE_SHOT)
			var form_ok:bool=not viewer._record and viewer._portable==(modes[id]=="portable")
			check(id+"保持登记的实物或现场形态",form_ok)
			key(KEY_F);await process_frame
			check(id+"F阅读具体内容",viewer.reading and not viewer._text.text.is_empty())
			key(KEY_ESCAPE);await process_frame
			check(id+"Esc先返回观察",viewer.active and not viewer.reading)
			key(KEY_ESCAPE);await create_timer(.30).timeout
			var evidence:String=root.get_node("ContentDB").hotspots[id].get("evidence","")
			var restored:bool=not viewer.active and not host.player.frozen and returned.has("camera") and returned["camera"].is_equal_approx(before) and is_equal_approx(returned["fov"],before_fov)
			if not restored or not group_done:print("RESTORE_DIAGNOSTIC ",id," before=",before," after=",host.player.cam.global_transform," frozen=",host.player.frozen," group_done=",group_done," inspected=",state.inspected.count(id)," evidence=",state.evidence.count(evidence))
			check(id+"退出恢复且完成单项调查",restored and group_done and state.inspected.count(id)==1 and (evidence=="" or state.evidence.count(evidence)==1))
			var count:int=state.evidence.size()
			aim(host,target);key(KEY_E);await create_timer(.26).timeout
			var reopened:bool=viewer.active and viewer._data.get("hotspot", "")==id
			check(id+"任务结束后E仍可重复检视",reopened)
			if reopened:key(KEY_ESCAPE);await create_timer(.30).timeout
			check(id+"重复检视不重复记录",state.evidence.size()==count and state.inspected.count(id)==1 and not host.player.frozen)
			records.append({"id":id,"room":room,"opened":opened,"form":form_ok,"restored":restored,"reopened":reopened,"evidence_once":state.evidence.size()==count and state.inspected.count(id)==1})
	var file=FileAccess.open("/tmp/dm-selected-hotspot-inputs.json" if filtered else "/tmp/dm-all-hotspot-inputs.json",FileAccess.WRITE);file.store_string(JSON.stringify(records,"\t"))
	check("覆盖所有普通热点",records.size()==samples.size())
	print("ALL_HOTSPOT_INPUTS objects=",records.size()," failures=",failures)
	main.queue_free();await process_frame;quit(0 if failures==0 else 1)
