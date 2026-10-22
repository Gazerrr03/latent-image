extends SceneTree
const Targeting:=preload("res://world/interaction_targeting.gd")
var failures:=0
var emitted:Array=[]
var room_events:Array=[]
func _initialize():call_deferred("run")
func check(label:String,ok:bool):
	print("PASS " if ok else "FAIL ",label)
	if not ok:failures+=1
func key():
	var e:=InputEventKey.new();e.keycode=KEY_E;e.physical_keycode=KEY_E;e.pressed=true;root.push_input(e,true)
	e=e.duplicate();e.pressed=false;root.push_input(e,true)
func run():
	root.get_node("GameState").persist=false
	var main=load("res://main.tscn").instantiate();root.add_child(main);await process_frame
	create_timer(60).timeout.connect(func():printerr("MOVING_DOOR timeout");quit(2))
	root.get_node("GameState").reset()
	var director=root.get_node("Director");var host=director.world;var ui=director.ui
	director.inspected.connect(func(id):
		if id.begins_with("enter:"):room_events.append(id)
		else:emitted.append(id))
	ui.menus.hide();ui.eyelids_set(1.0);ui.set_cinematic(false)
	host.show_scene("darkroom");host.apply_room_states("C1-05");host.set_mode("walk","")
	host.highlight_hotspots(["hs_camera"]);host.player.frozen=true
	var door:Node
	for body in host.doors:
		if String(host.doors[body]["leaf"].name)=="暗房·温室侧门":door=body
	check("采用原侧门真实门板",door!=null)
	if door==null:quit(1);return
	if host.door_is_open(door):host.toggle_door(door,host.doors[door]["leaf"].global_position+Vector3.RIGHT);await create_timer(.9).timeout
	var samples=JSON.parse_string(FileAccess.get_file_as_string("res://../docs/验证/2026-10-20-物品检视/逐对象判定.json"))
	for row in samples:
		if row.id=="hs_camera":host.player.place(Vector3(row.feet[0],row.feet[1],row.feet[2]),0)
	await physics_frame;await physics_frame
	var target:Node3D=host.hotspot_nodes["hs_camera"]
	host.player.cam.look_at(target.global_position);host.player._update_hover()
	check("侧门未挡住旧站位时相机可选",host.player._hover=="hs_camera")
	var before=host.player.cam.global_transform
	host.toggle_door(door,host.doors[door]["leaf"].global_position+Vector3.RIGHT)
	await create_timer(.9).timeout
	check("正常开门后门扇进入视线",host.door_is_open(door) and Targeting.pick(host.player.cam,[target],target,[host.player.get_rid()])==null)
	host.player.frozen=false;key()
	check("旧相机提示不能穿过新遮挡执行",emitted.is_empty() and host.player._hover!="hs_camera")
	host.player.frozen=true;host.player.cam.global_transform=before
	host.toggle_door(door,host.doors[door]["leaf"].global_position+Vector3.RIGHT)
	await create_timer(.9).timeout
	host.player._update_hover();host.player.frozen=false
	check("关闭侧门移开遮挡后相机重新可选",host.player._hover=="hs_camera")
	key();check("新提示后E只操作相机",emitted==["hs_camera"])
	print("ROOM_ENTRY_EVENTS ",room_events)
	print("MOVING_DOOR failures=",failures)
	main.queue_free();await process_frame;quit(0 if failures==0 else 1)
