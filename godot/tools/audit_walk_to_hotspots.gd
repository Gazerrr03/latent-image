extends SceneTree
## Walk the actual player from each room spawn; no teleporting to object poses.
## Planning reads current collider geometry; actual player collision stays active. Doors open through E.
var failures:=0
var records:Array=[]
var opened_doors:Array=[]
var cycled_doors:={}
var walked_total:=0.0
var ticks_total:=0
func _initialize():call_deferred("run")
func key(code:Key):
	var e:=InputEventKey.new();e.keycode=code;e.physical_keycode=code;e.pressed=true;root.push_input(e,true)
	e=e.duplicate();e.pressed=false;root.push_input(e,true)
func stop():
	for action in ["move_left","move_right","move_forward","move_back"]:Input.action_release(action)
func aim(player,point:Vector3):
	var d:Vector3=point-player.cam.global_position
	player.rotation.y=atan2(-d.x,-d.z);player._pitch=atan2(d.y,Vector2(d.x,d.z).length());player.cam.look_at(point)
func focus(target:Node3D)->Vector3:
	for shape in target.get_children():
		if shape is CollisionShape3D and shape.shape!=null:return shape.global_transform*preload("res://world/interaction_targeting.gd")._bounds(shape.shape).get_center()
	return target.global_position
func group(director,ids):await director._inspect(ids,"walk")
func route(guide,from:Vector3,to:Vector3)->PackedVector3Array:
	var a:int=guide._poly_at(from);var b:int=guide._poly_at(to)
	if a<0 or b<0:return PackedVector3Array()
	var open:Array=[a];var came:={};var portals:={};var cost:={a:0.0};var closed:={}
	while not open.is_empty():
		var cur:int=open[0]
		for n in open:
			if cost[n]+guide._centers[n].distance_to(to)<cost[cur]+guide._centers[cur].distance_to(to):cur=n
		if cur==b:break
		open.erase(cur);closed[cur]=true
		for edge in guide._adj[cur]:
			var n:int=edge[0]
			if closed.has(n):continue
			var score:float=cost[cur]+guide._centers[cur].distance_to(guide._centers[n])
			if not cost.has(n) or score<cost[n]:
				cost[n]=score;came[n]=cur;portals[n]=edge[1]
				if not open.has(n):open.append(n)
	if a!=b and not came.has(b):return PackedVector3Array()
	var out:Array=[to];var at:int=b
	while at!=a:
		out.push_front(guide._centers[at]);out.push_front(portals[at]);at=came[at]
	out.push_front(guide._centers[a]);out.push_front(from)
	return PackedVector3Array(out)
func bake_current(guide,host):
	# Read collider geometry directly. Never mutate a collider or its visibility.
	# Closed operable doors are planning links; actual movement still hits them and must press E.
	var nm:=NavigationMesh.new();nm.agent_radius=.3;nm.agent_height=1.75
	nm.agent_max_climb=.3;nm.agent_max_slope=40;nm.cell_size=.0125;nm.cell_height=.025;nm.detail_sample_distance=9.0
	var src:=NavigationMeshSourceGeometryData3D.new()
	nm.filter_baking_aabb=guide.get_meta("walk_bake_bounds",AABB(Vector3(-6,-1,-22),Vector3(36,10,34)))
	var shapes:=0
	for body in host._walk(host.room):
		if not body is StaticBody3D or not body.is_visible_in_tree() or (body.collision_layer&1)==0:continue
		if host.doors.has(body) and not host.door_is_open(body):continue
		for shape in body.get_children():
			if not shape is CollisionShape3D or shape.disabled or shape.shape==null:continue
			var points:=PackedVector3Array()
			if shape.shape is ConcavePolygonShape3D:points=shape.shape.get_faces()
			elif shape.shape is BoxShape3D:
				var box:=BoxMesh.new();box.size=shape.shape.size;points=box.get_faces()
			elif shape.shape is CylinderShape3D:
				var cylinder:=CylinderMesh.new();cylinder.top_radius=shape.shape.radius;cylinder.bottom_radius=shape.shape.radius;cylinder.height=shape.shape.height;points=cylinder.get_faces()
			elif shape.shape is SphereShape3D:
				var sphere:=SphereMesh.new();sphere.radius=shape.shape.radius;sphere.height=shape.shape.radius*2;points=sphere.get_faces()
			elif shape.shape is CapsuleShape3D:
				var capsule:=CapsuleMesh.new();capsule.radius=shape.shape.radius;capsule.height=shape.shape.height;points=capsule.get_faces()
			else:printerr("UNSUPPORTED_WALK_SHAPE ",shape.get_path()," ",shape.shape.get_class());continue
			src.add_faces(points,shape.global_transform);shapes+=1
	NavigationServer3D.bake_from_source_geometry_data(nm,src);guide._index(nm)
	print("WALK_PLAN shapes=",shapes," polygons=",nm.get_polygon_count())

func physical_grid_path(guide,host,target,camera:Camera3D,candidates:Array)->PackedVector3Array:
	# A navmesh uses a full-height cylinder. The real player has a raised capsule and step ray.
	# Search actual capsule sweeps when that approximation cannot find a reachable viewing position.
	var capsule_node:CollisionShape3D
	for child in host.player.get_children():
		if child is CollisionShape3D and child.shape is CapsuleShape3D:capsule_node=child;break
	if capsule_node==null:return PackedVector3Array()
	var origin:Vector3=host.player.global_position;var area:AABB=guide.get_meta("walk_bake_bounds")
	var cache:={Vector2i.ZERO:origin};var came:={};var queue:Array[Vector2i]=[Vector2i.ZERO];var cursor:=0
	var space:PhysicsDirectSpaceState3D=host.get_world_3d().direct_space_state
	var found:=false;var end:=Vector2i.ZERO;var nearest:=INF;var nearest_feet:=origin
	while cursor<queue.size() and cursor<80000:
		var cell:Vector2i=queue[cursor];cursor+=1
		var feet:Vector3=cache[cell]
		var target_distance:float=(feet+Vector3.UP*1.6).distance_to(focus(target))
		if target_distance<nearest:nearest=target_distance;nearest_feet=feet
		if Vector2(feet.x-focus(target).x,feet.z-focus(target).z).length()<3.0:
			camera.global_position=feet+Vector3.UP*1.6;camera.look_at(focus(target))
			if preload("res://world/interaction_targeting.gd").pick(camera,candidates,null,[host.player.get_rid()])==target:found=true;end=cell;break
		for direction in [Vector2i.LEFT,Vector2i.RIGHT,Vector2i.UP,Vector2i.DOWN]:
			var next:Vector2i=cell+direction
			if cache.has(next):continue
			cache[next]=null
			var point:Vector3=origin+Vector3(next.x*.025,0,next.y*.025)
			if point.x<area.position.x or point.x>area.end.x or point.z<area.position.z or point.z>area.end.z:continue
			var floor_query:=PhysicsRayQueryParameters3D.create(point+Vector3.UP*.35,point-Vector3.UP*.4,1);floor_query.exclude=[host.player.get_rid()]
			var ground:Dictionary=space.intersect_ray(floor_query)
			if ground.is_empty() or ground.normal.y<.8:continue
			point=ground.position+Vector3.UP*.001
			if absf(point.y-feet.y)>.3:continue
			var query:=PhysicsShapeQueryParameters3D.new();query.shape=capsule_node.shape;query.transform=Transform3D(Basis.IDENTITY,point)*capsule_node.transform;query.collision_mask=1;query.exclude=[host.player.get_rid()];query.margin=host.player.safe_margin
			if not space.intersect_shape(query,1).is_empty():continue
			query.transform=Transform3D(Basis.IDENTITY,feet)*capsule_node.transform;query.motion=point-feet
			var sweep:PackedFloat32Array=space.cast_motion(query)
			if sweep.is_empty() or sweep[0]<.999:
				cache.erase(next) # An edge can be blocked while another approach to this cell is valid.
				continue
			cache[next]=point;came[next]=cell;queue.append(next)
	if not found:
		print("PHYSICAL_GRID no_viewing_route visited=",cursor," nearest_center_m=",nearest," feet=",nearest_feet);return PackedVector3Array()
	var path:Array=[cache[end]];var at:Vector2i=end
	while at!=Vector2i.ZERO:at=came[at];path.push_front(cache[at])
	guide.set_meta("walk_grid_path",true)
	print("PHYSICAL_GRID found visited=",cursor," steps=",path.size())
	return PackedVector3Array(path)

func reachable_view_path(guide,host,target,fallback:Vector3)->PackedVector3Array:
	var original:=route(guide,host.player.global_position,fallback)
	if not original.is_empty():return original
	var candidates:Array=[]
	for id in host.active_hotspots+root.get_node("GameState").inspected:
		var body:Node=host.hotspot_nodes.get(id)
		if body!=null and not candidates.has(body):candidates.append(body)
	for body in host.doors:
		if not candidates.has(body):candidates.append(body)
	for body in get_nodes_in_group("light_switch"):
		if not candidates.has(body):candidates.append(body)
	var camera:=Camera3D.new();host.add_child(camera);camera.fov=host.player.cam.fov
	var best:=PackedVector3Array();var best_length:=INF
	var vantage_points:Array=guide._centers.duplicate()
	for i in guide._polys.size():
		var poly:PackedInt32Array=guide._polys[i];var center:Vector3=guide._centers[i]
		for j in poly.size():
			vantage_points.append(center.lerp(guide._verts[poly[j]],.95))
			vantage_points.append(center.lerp((guide._verts[poly[j]]+guide._verts[poly[(j+1)%poly.size()]])*.5,.95))
	for center in vantage_points:
		if absf(center.y-host.player.global_position.y)>.4 or Vector2(center.x-target.global_position.x,center.z-target.global_position.z).length()>2.8:continue
		var q:=PhysicsRayQueryParameters3D.create(center+Vector3.UP*.25,center-Vector3.UP*.5,1);q.exclude=[host.player.get_rid()]
		var floor_hit:Dictionary=camera.get_world_3d().direct_space_state.intersect_ray(q)
		if floor_hit.is_empty() or floor_hit.normal.y<.8:continue
		var feet:Vector3=floor_hit.position+Vector3.UP*.03
		var capsule:=CapsuleShape3D.new();capsule.radius=.3;capsule.height=1.75
		var space:=PhysicsShapeQueryParameters3D.new();space.shape=capsule;space.transform=Transform3D(Basis.IDENTITY,feet+Vector3.UP*.875);space.collision_mask=1;space.exclude=[host.player.get_rid()]
		if not camera.get_world_3d().direct_space_state.intersect_shape(space,1).is_empty():continue
		camera.global_position=feet+Vector3.UP*1.6;camera.look_at(focus(target))
		if preload("res://world/interaction_targeting.gd").pick(camera,candidates,null,[host.player.get_rid()])!=target:continue
		var path:=route(guide,host.player.global_position,feet)
		if path.is_empty():continue
		var length:=0.0
		for i in range(1,path.size()):length+=path[i-1].distance_to(path[i])
		if length<best_length:best_length=length;best=path
	if best.is_empty():best=physical_grid_path(guide,host,target,camera,candidates)
	camera.queue_free()
	return best

func cycle_near_open_door(guide,host)->bool:
	# Ordinary close/open actions can move an initially inward-opening leaf out of the passage.
	for body in host.doors:
		if cycled_doors.has(body) or not host.door_is_open(body) or host.doors[body].get("container",false) or body.global_position.distance_to(host.player.global_position)>4.0:continue
		var center:Vector3=body.global_position
		for shape in body.get_children():
			if shape is CollisionShape3D and shape.shape!=null:center=shape.global_transform*preload("res://world/interaction_targeting.gd")._bounds(shape.shape).get_center();break
		if host.player.cam.global_position.distance_to(center)<.75:continue
		stop();aim(host.player,center);host.player._update_hover()
		print("DOOR_CYCLE_TRY ",host.doors[body]["leaf"].name," selected=",host.player._target," center=",center)
		cycled_doors[body]=true
		if host.player._door!=body:
			var approach:Dictionary=await travel(guide,host,body,Vector3(center.x,host.player.global_position.y,center.z),host.player.global_position.y,8)
			print("DOOR_APPROACH ",JSON.stringify(approach))
			if not approach.reached:continue
			aim(host.player,center);host.player._update_hover()
			if host.player._door!=body:continue
		key(KEY_E);await create_timer(.9).timeout
		if host.door_is_open(body):continue
		for shape in body.get_children():
			if shape is CollisionShape3D and shape.shape!=null:center=shape.global_transform*preload("res://world/interaction_targeting.gd")._bounds(shape.shape).get_center();break
		aim(host.player,center);host.player._update_hover()
		if host.player._door!=body:
			bake_current(guide,host)
			var approach_closed:Dictionary=await travel(guide,host,body,Vector3(center.x,host.player.global_position.y,center.z),host.player.global_position.y,8)
			print("CLOSED_DOOR_APPROACH ",JSON.stringify(approach_closed))
			if not approach_closed.reached:continue
			aim(host.player,center);host.player._update_hover()
			if host.player._door!=body:continue
		key(KEY_E);await create_timer(.9).timeout
		if host.door_is_open(body):
			opened_doors.append("close/open: "+String(host.doors[body]["leaf"].name));return true
	return false

func travel(guide,host,target,goal:Vector3,floor_y:float,depth:=0)->Dictionary:
	guide.set_meta("walk_grid_path",false)
	var path:=reachable_view_path(guide,host,target,goal)
	var waypoint_precision:float=.015 if guide.get_meta("walk_grid_path",false) else .1
	var reached:=false;var reason:="";var meters:=0.0;var ticks:=0;var min_y:float=host.player.global_position.y
	if path.is_empty():
		if depth<8 and await cycle_near_open_door(guide,host):
			bake_current(guide,host)
			return await travel(guide,host,target,goal,floor_y,depth+1)
		reason="no_planned_route"
	for point_index in path.size():
		var point:Vector3=path[point_index]
		var idle:=0;var previous_distance:=INF
		while Vector2(point.x-host.player.global_position.x,point.z-host.player.global_position.z).length()>(.015 if guide.get_meta("walk_grid_path",false) else .025 if point_index==path.size()-1 else waypoint_precision):
			stop();aim(host.player,focus(target));host.player._update_hover()
			if host.player._target==target:reached=true;break
			var door:Node=host.player._door
			var delta:Vector3=point-host.player.global_position;delta.y=0
			if door==null or host.door_is_open(door):
				aim(host.player,host.player.cam.global_position+delta.normalized());host.player._update_hover();door=host.player._door
			if door!=null and not host.door_is_open(door):
				if depth>=8:reason="door_replan_limit";break
				key(KEY_E);await create_timer(.9).timeout
				if not host.door_is_open(door):reason="door_did_not_open";break
				opened_doors.append(String(host.doors[door]["leaf"].name))
				bake_current(guide,host)
				var continued:Dictionary=await travel(guide,host,target,goal,floor_y,depth+1)
				continued.walked_m+=meters;continued.ticks+=ticks;continued.minimum_y=minf(min_y,continued.minimum_y)
				return continued
			var before:Vector3=host.player.global_position
			Input.action_press("move_forward");await physics_frame;stop()
			meters+=before.distance_to(host.player.global_position);walked_total+=before.distance_to(host.player.global_position);ticks+=1;ticks_total+=1;min_y=minf(min_y,host.player.global_position.y)
			var distance:float=Vector2(point.x-host.player.global_position.x,point.z-host.player.global_position.z).length()
			idle=idle+1 if distance>previous_distance-.001 else 0;previous_distance=distance
			if idle>90 or ticks>3600:
				reason="blocked_on_route"
				var hits:Array=[]
				for k in host.player.get_slide_collision_count():
					var hit:KinematicCollision3D=host.player.get_slide_collision(k)
					hits.append({"body":str(hit.get_collider().get_path()),"normal":str(hit.get_normal()),"at":str(hit.get_position())})
				print("WALK_BLOCK ",target.get_meta("hotspot_id",str(target.get_path()))," point=",point," collisions=",JSON.stringify(hits));break
			if host.player.global_position.y<floor_y-.5:reason="fell_below_floor";break
		if reached or reason!="":break
	stop();aim(host.player,focus(target));host.player._update_hover()
	reached=reached or host.player._target==target
	if not reached and reason=="":reason="arrived_without_target"
	return {"reached":reached,"reason":reason,"walked_m":meters,"ticks":ticks,"minimum_y":min_y,"waypoints":path.size()}

func run():
	root.get_node("GameState").persist=false
	var main=load("res://main.tscn").instantiate();root.add_child(main);await process_frame
	create_timer(600).timeout.connect(func():stop();printerr("WALK_INPUT timeout");quit(2))
	var state=root.get_node("GameState");state.reset()
	var director=root.get_node("Director");var host=director.world;var ui=director.ui;var viewer=ui.inspector
	ui.menus.hide();ui.eyelids_set(1.0);ui.set_cinematic(false)
	var rows=JSON.parse_string(FileAccess.get_file_as_string("res://../docs/验证/2026-10-20-物品检视/逐对象判定.json"))
	var selected:=PackedStringArray(["guest_room"])
	var out_stem:="/tmp/dm-walk-to-hotspots"
	var capture_id:=""
	for arg in OS.get_cmdline_user_args():
		if arg.begins_with("--rooms="):selected=arg.trim_prefix("--rooms=").split(",")
		if arg.begins_with("--out-stem="):out_stem=arg.trim_prefix("--out-stem=")
		if arg.begins_with("--capture-id="):capture_id=arg.trim_prefix("--capture-id=")
	for room in selected:
		stop();host.show_scene(room)
		var shot:String={"guest_room":"C6-02","darkroom":"C1-05","archive":"C2-03","con_room":"C2-04","child_room":"C3-04","greenhouse":"C4-03","seance":"C5-03"}.get(room,"C1-05")
		state.shot=shot;host.apply_room_states(shot);host.set_mode("walk","")
		var ids:Array=[]
		for row in rows:
			if row.room==room:ids.append(row.id)
		var spawn:Vector3=host._room_spawn[room][0] if host._room_spawn.has(room) else host.spawn[0]
		host.player.place(spawn,0);await create_timer(.3).timeout
		var guide=preload("res://world/guide.gd").new();guide.host=host;host.add_child(guide)
		var area:=AABB(spawn,Vector3.ZERO)
		for row in rows:
			if row.room==room:area=area.expand(Vector3(row.feet[0],spawn.y,row.feet[2]))
		area.position-=Vector3(1.5,.4,1.5);area.size+=Vector3(3,3.5,3)
		guide.set_meta("walk_bake_bounds",area)
		var layers:={}
		for body in host.doors:layers[body]=body.collision_layer
		bake_current(guide,host)
		var restored:bool=layers.keys().all(func(body):return body.collision_layer==layers[body])
		if not restored:failures+=1;printerr("FAIL door layers not restored");quit(1);return
		group(director,ids)
		for row in rows:
			if row.room!=room:continue
			var id:String=row.id;var target:Node3D=host.hotspot_nodes.get(id)
			var goal:=Vector3(row.feet[0],row.feet[1],row.feet[2])
			var previous_total:float=walked_total;var previous_ticks:int=ticks_total
			var result:Dictionary=await travel(guide,host,target,goal,spawn.y)
			result.walked_m=walked_total-previous_total;result.ticks=ticks_total-previous_ticks
			var reached:bool=result.reached
			var opened:=false
			if reached:
				key(KEY_E);await create_timer(.27).timeout
				opened=viewer.active and viewer._data.get("hotspot","")==id
				if opened and capture_id==id:
					await RenderingServer.frame_post_draw
					root.get_texture().get_image().save_png(out_stem+"-"+id+".png")
				if viewer.active:key(KEY_ESCAPE);await create_timer(.3).timeout
			var ok:bool=reached and opened and state.inspected.count(id)==1
			if not ok:failures+=1
			result.merge({"id":id,"room":room,"ok":ok,"opened":opened,"feet":str(host.player.global_position)})
			records.append(result);print("WALK_OBJECT ",JSON.stringify(result))
		stop();director.inspected.emit(director.CANCEL);guide.queue_free();await process_frame
	var file=FileAccess.open(out_stem+".json",FileAccess.WRITE);file.store_string(JSON.stringify({"objects":records,"doors_opened_by_e":opened_doors,"failures":failures},"\t"))
	print("WALK_TO_HOTSPOTS objects=",records.size()," failures=",failures)
	main.queue_free();await process_frame;quit(0 if failures==0 else 1)
