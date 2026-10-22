extends SceneTree
## Dense real-scene sweeps. Never move furniture or turn off occlusion.
const Targeting:=preload("res://world/interaction_targeting.gd")
var failures:=0
var records:Array=[]
func _initialize():call_deferred("run")
func name_of(node)->String:
	if node==null:return ""
	return str(node.get_meta("hotspot_id",node.get_path()))
func run():
	root.get_node("GameState").persist=false
	var main=load("res://main.tscn").instantiate();root.add_child(main);await process_frame
	root.get_node("GameState").reset()
	create_timer(180).timeout.connect(func():printerr("DENSE timeout");quit(2))
	var director=root.get_node("Director");var host=director.world
	director.ui.menus.hide()
	var camera:=Camera3D.new();main.add_child(camera)
	camera.fov=host.player.cam.fov
	var saved=JSON.parse_string(FileAccess.get_file_as_string("res://../docs/验证/2026-10-20-物品检视/逐对象判定.json"))
	for resolution in [Vector2i(1280,720),Vector2i(1920,1080)]:
		root.content_scale_size=resolution;root.size=resolution;await process_frame
		var rooms:Array=[]
		for row in saved:
			if not rooms.has(row.room):rooms.append(row.room)
		for room_id in rooms:
			host.show_scene(room_id)
			var shot:String={"guest_room":"C6-02","darkroom":"C1-05","archive":"C2-03","con_room":"C2-04","child_room":"C3-04","greenhouse":"C4-03","seance":"C5-03"}.get(room_id,"C1-05")
			host.apply_room_states(shot);host.set_mode("walk","");host.player.frozen=true
			# Open only existing containers/side door through their normal operation.
			for body in host.doors:
				var info:Dictionary=host.doors[body]
				if String(info["leaf"].name)=="暗房·温室侧门":
					var should_open:bool=room_id=="greenhouse"
					if host.door_is_open(body)!=should_open:host.toggle_door(body,info["leaf"].global_position+Vector3.RIGHT)
				elif info.get("container",false) and not host.door_is_open(body):
					host.toggle_door(body,info["leaf"].global_position-Vector3.RIGHT)
			await create_timer(.9).timeout;await physics_frame;await physics_frame
			var candidates:Array=[]
			for h in root.get_node("ContentDB").hotspots.values():
				if h["scene"]==room_id and host.hotspot_nodes.has(h["id"]):candidates.append(host.hotspot_nodes[h["id"]])
			for body in host.doors:
				if not candidates.has(body):candidates.append(body)
			for body in get_nodes_in_group("light_switch"):
				if not candidates.has(body):candidates.append(body)
			var reversed:=candidates.duplicate();reversed.reverse()
			for row in saved:
				if row.room!=room_id:continue
				var target:Node3D=host.hotspot_nodes.get(row.id)
				if target==null or not row.has("feet"):continue
				camera.global_position=Vector3(row.feet[0],row.feet[1],row.feet[2])+Vector3.UP*1.6
				camera.look_at(target.global_position)
				var base:Transform3D=camera.global_transform
				var center_pick=Targeting.pick(camera,candidates,null,[host.player.get_rid()])
				if center_pick!=target:failures+=1;print("CENTER_FAIL ",row.id," ",name_of(center_pick))
				var previous:Node=null
				var sequence:Array=[]
				var pixels:float=camera.get_viewport().get_visible_rect().size.y/720.0
				for axis in [Vector2.RIGHT,Vector2.DOWN]:
					for offset in range(-64,65,8):
						camera.global_transform=base
						var center:Vector2=camera.get_viewport().get_visible_rect().size*.5
						var ray:Vector3=camera.project_ray_normal(center+axis*float(offset)*pixels)
						camera.look_at(camera.global_position+ray)
						var picked=Targeting.pick(camera,candidates,previous,[host.player.get_rid()])
						var reverse_pick=Targeting.pick(camera,reversed,previous,[host.player.get_rid()])
						if picked!=reverse_pick:failures+=1
						var alone=Targeting.pick(camera,[picked],picked,[host.player.get_rid()]) if picked!=null else null
						if alone!=picked:failures+=1
						sequence.append({"axis":str(axis),"offset_720p":offset,"picked":name_of(picked),"order_stable":picked==reverse_pick,"still_eligible":alone==picked})
						previous=picked
				records.append({"resolution":str(resolution),"viewport":str(camera.get_viewport().get_visible_rect().size),"room":room_id,"id":row.id,"center_pick":name_of(center_pick),"center_matches":center_pick==target,"samples":sequence})
				print("DENSE_OBJECT ",resolution," ",row.id," samples=",sequence.size())
	var per_object:={}
	for record in records:per_object.get_or_add(record.id,[]).append(record)
	var resolution_differences:=0
	for id in per_object:
		var pair:Array=per_object[id]
		if pair.size()!=2:failures+=1;continue
		for i in pair[0].samples.size():
			if pair[0].samples[i].picked!=pair[1].samples[i].picked:resolution_differences+=1
	if per_object.size()!=saved.size():failures+=1
	failures+=resolution_differences
	print("RESOLUTION_DIFFERENCES ",resolution_differences)
	var file=FileAccess.open("/tmp/dm-dense-interaction.json",FileAccess.WRITE);file.store_string(JSON.stringify(records,"\t"))
	print("DENSE_INTERACTION targets=",records.size()," samples=",records.size()*34," failures=",failures)
	main.queue_free();await process_frame;quit(0 if failures==0 else 1)
