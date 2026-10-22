extends SceneTree
## All visible manor door/switch controls: real physical stand, real E dispatch, original collision.
const Targeting=preload("res://world/interaction_targeting.gd")
var host:Node
var records:Array=[]
var failures:=0
func _initialize():call_deferred("run")
func key(echo:=false):
	var event:=InputEventKey.new();event.keycode=KEY_E;event.physical_keycode=KEY_E;event.pressed=true;event.echo=echo;root.push_input(event,true)
	if not echo:event=event.duplicate();event.pressed=false;root.push_input(event,true)
func center(body:Node3D)->Vector3:
	for child in body.get_children():
		if child is CollisionShape3D and child.shape!=null:return child.global_transform*Targeting._bounds(child.shape).get_center()
	return body.global_position
func candidates()->Array:
	var out:Array=host.doors.keys()
	for body in get_nodes_in_group("light_switch"):
		if not out.has(body):out.append(body)
	for body in get_nodes_in_group("door_line"):
		if not out.has(body) and host.door_line(body)!="":out.append(body)
	return out
func pose(target:Node3D,camera:Camera3D)->Variant:
	var ancestor:Node=target;var floor_y:float=3.6 if center(target).y>3 else 0.0
	while ancestor!=null:
		if String(ancestor.name)!=host.MAP_ID and host._room_spawn.has(String(ancestor.name)):
			floor_y=host._room_spawn[String(ancestor.name)][0].y;break
		ancestor=ancestor.get_parent()
	var point:=center(target);var space:PhysicsDirectSpaceState3D=host.get_world_3d().direct_space_state
	for radius in [.9,1.25,1.65,2.0,2.2]:
		for step in 48:
			var angle:=TAU*step/48.0;var sample:=point+Vector3(sin(angle)*radius,0,cos(angle)*radius)
			var ray:=PhysicsRayQueryParameters3D.create(Vector3(sample.x,floor_y+.35,sample.z),Vector3(sample.x,floor_y-.45,sample.z),1);ray.exclude=[host.player.get_rid()]
			var floor_hit:Dictionary=space.intersect_ray(ray)
			if floor_hit.is_empty() or floor_hit.normal.y<.8:continue
			var feet:Vector3=floor_hit.position+Vector3.UP*.03
			var capsule:=CapsuleShape3D.new();capsule.radius=.3;capsule.height=1.75
			var query:=PhysicsShapeQueryParameters3D.new();query.shape=capsule;query.transform=Transform3D(Basis.IDENTITY,feet+Vector3.UP*.875);query.collision_mask=1;query.exclude=[host.player.get_rid()]
			if not space.intersect_shape(query,1).is_empty():continue
			camera.global_position=feet+Vector3.UP*1.6;camera.look_at(point)
			if Targeting.pick(camera,candidates(),null,[host.player.get_rid()])==target:return feet
	return null
func states()->Dictionary:
	var out:={}
	for body in host.doors:out[str(body.get_path())]=host.door_is_open(body)
	for body in get_nodes_in_group("light_switch"):out[str(body.get_path())]=host.switch_is_on(body)
	return out
func audit_control(target:Node3D,shot:String,camera:Camera3D):
	var director=root.get_node("Director")
	var is_door:bool=host.doors.has(target);var is_switch:bool=target.has_meta("switch")
	var label:String=String(host.doors[target]["leaf"].name) if is_door else String(target.get_meta("switch")) if is_switch else String(target.get_meta("door_line"))
	var record:={"path":str(target.get_path()),"name":label,"shot":shot,"kind":"door" if is_door else "switch" if is_switch else "sealed_door","stand":false,"hint":false,"action":false,"echo":false,"isolated":false,"restored":false}
	var feet=pose(target,camera)
	if feet!=null:
		record.stand=true;record.feet=str(feet)
		host.player.place(feet,0);host.player.frozen=true;await physics_frame;await physics_frame
		host.player.cam.look_at(center(target));host.player._update_hover()
		record.hint=host.player._target==target
		var before:=states();var path:=str(target.get_path());var locked:bool=not is_switch and host.door_line(target)!="" and (not is_door or not host.door_is_open(target))
		record.locked=locked
		director.ui.toast_label.text=""
		host.player.frozen=false;key();host.player.frozen=true;await create_timer(.9 if is_door else .05).timeout
		var after:=states()
		record.action=after==before and director.ui.toast_label.text==host.door_line(target) if locked else after[path]!=before[path]
		record.isolated=true
		for other in before:
			if other!=path and before[other]!=after[other]:record.isolated=false
		host.player.frozen=false;key(true);host.player.frozen=true;await create_timer(.05).timeout
		record.echo=states()==after
		if not locked:
			# Moving leaves must be reacquired from a floor-supported, unobstructed pose.
			feet=pose(target,camera)
			if feet!=null:
				host.player.place(feet,0);host.player.frozen=true;await physics_frame;await physics_frame
				host.player.cam.look_at(center(target));host.player._update_hover();host.player.frozen=false;key();host.player.frozen=true;await create_timer(.9 if is_door else .05).timeout
		record.restored=states()==before
	record.ok=record.stand and record.hint and record.action and record.echo and record.isolated and record.restored
	if not record.ok:failures+=1
	records.append(record);print("CONTROL ",JSON.stringify(record))
func run():
	root.get_node("GameState").persist=false
	var main=load("res://main.tscn").instantiate();root.add_child(main);await process_frame
	create_timer(180).timeout.connect(func():printerr("CONTROL_INPUT timeout");quit(2))
	var director=root.get_node("Director");host=director.world
	root.get_node("GameState").reset()
	director.ui.menus.hide();director.ui.eyelids_set(1.0);director.ui.set_cinematic(false)
	host.show_scene("guest_room");host.set_mode("walk","");host.highlight_hotspots([]);host.player.frozen=true
	var camera:=Camera3D.new();host.add_child(camera)
	for shot in ["C1-05","C0-11","C0-13"]:
		root.get_node("GameState").shot=shot;host.apply_room_states(shot);await physics_frame;await physics_frame
		for target in candidates():
			if not target.is_visible_in_tree():continue
			if shot!="C1-05" and host.door_line(target)=="":continue
			await audit_control(target,shot,camera)
	var file:=FileAccess.open("/tmp/dm-door-switch-inputs.json",FileAccess.WRITE);file.store_string(JSON.stringify({"controls":records,"failures":failures},"\t"))
	print("DOOR_SWITCH_INPUTS controls=",records.size()," failures=",failures)
	main.queue_free();await process_frame;quit(0 if failures==0 else 1)
