extends SceneTree
var failures := 0
var host: Node
var corridor: Node
var ui: Node
func _initialize():call_deferred("run")
func check(label: String,ok: bool):
	print("PASS " if ok else "FAIL ",label)
	if not ok:failures+=1
func key():
	var event:=InputEventKey.new();event.keycode=KEY_E;event.physical_keycode=KEY_E;event.pressed=true
	root.push_input(event,true);event=event.duplicate();event.pressed=false;root.push_input(event,true)
func aim(id: String,offset: Vector3):
	var target: Node3D=host.hotspot_nodes[id]
	var feet: Vector3=target.global_position+offset;feet.y=corridor.global_position.y+.03
	var capsule:=CapsuleShape3D.new();capsule.radius=.3;capsule.height=1.75
	var space: PhysicsDirectSpaceState3D=host.player.get_world_3d().direct_space_state
	var shape_query:=PhysicsShapeQueryParameters3D.new();shape_query.shape=capsule
	shape_query.transform=Transform3D(Basis.IDENTITY,feet+Vector3.UP*.875)
	shape_query.collision_mask=1;shape_query.exclude=[host.player.get_rid()]
	var floor_query:=PhysicsRayQueryParameters3D.create(feet+Vector3.UP*.1,feet-Vector3.UP*.2,1)
	floor_query.exclude=[host.player.get_rid()]
	check(id+"站位有地面且角色放得下",space.intersect_shape(shape_query,1).is_empty() and not space.intersect_ray(floor_query).is_empty())
	host.player.place(feet,0)
	await physics_frame;await physics_frame
	await create_timer(.3).timeout
	var direction: Vector3=target.global_position-host.player.cam.global_position
	host.player.rotation.y=atan2(-direction.x,-direction.z)
	host.player._pitch=atan2(direction.y,Vector2(direction.x,direction.z).length())
	host.player.cam.look_at(target.global_position)
	host.player._update_hover()
	check(id+"正常站位提示一致",host.player._hover==id)
	check(id+"提示动词对应实际动作",host.target_label(id).begins_with(root.get_node("ContentDB").hotspots[id]["verb"]+"："))
	if DisplayServer.get_name()!="headless":
		await RenderingServer.frame_post_draw
		check(id+"显示玩家相机且目标在画面中央",root.get_camera_3d()==host.player.cam and host.player.cam.unproject_position(target.global_position).distance_to(root.get_visible_rect().size*.5)<8)
		print("CORRIDOR_CAMERA ",host.player.cam.global_position," looking=",-host.player.cam.global_basis.z," target=",target.global_position)
		root.get_texture().get_image().save_png("/tmp/dm-corridor-"+id+".png")
func run():
	root.get_node("GameState").persist=false
	var main=load("res://main.tscn").instantiate();root.add_child(main);await process_frame
	root.get_node("GameState").reset()
	create_timer(90).timeout.connect(func():printerr("CORRIDOR timeout");quit(2))
	host=root.get_node("Director").world;ui=root.get_node("Director").ui
	ui.menus.hide();ui.set_cinematic(false);ui.eyelids_set(1.0)
	host.show_scene("seance")
	host.start_corridor()
	for i in 180:
		await process_frame
		if host.corridor!=null and host.corridor.running:break
	corridor=host.corridor
	check("第一层只有出口可操作",host.active_hotspots==["hs_doorway"])
	await aim("hs_doorway",Vector3(1.1,0,0))
	key();await process_frame
	check("真实E推门进入下一层",corridor.layer==1 and host.active_hotspots.has("hs_darkroom_door"))
	await aim("hs_darkroom_door",Vector3(0,0,1.1))
	key();await process_frame
	check("第二层真实E触发敲门且保持可行走",corridor._knocked and not host.player.frozen and not ui.inspector.active)
	key();await process_frame
	check("重复E不重复推进层级",corridor.layer==1)
	corridor._enter(2);await physics_frame
	check("第三层不泄漏暗房门热区",not host.active_hotspots.has("hs_darkroom_door") and not host.hotspot_nodes["hs_darkroom_door"].visible)
	corridor._enter(3);await physics_frame
	await aim("hs_darkroom_door",Vector3(0,0,1.1))
	key();await process_frame
	check("第四层E保持本层且显示无回应",corridor.layer==3 and ui.toast_label.text.contains("没有声音"))
	corridor._enter(4);await physics_frame
	check("第五层声音未齐时第四椅不可选",not host.active_hotspots.has("hs_chair4") and not host.hotspot_nodes["hs_chair4"].visible)
	for source in corridor._sources:
		host.player.place(corridor.global_position+source.chair+Vector3(.7,.03,0),0)
		for frame in 30:
			await process_frame
			if source.found:break
		print("CORRIDOR_SOURCE ",source.id," found=",source.found," layer=",corridor.layer," pos=",host.player.global_position-corridor.global_position)
	check("靠近三处声源后第四椅出现",corridor._sources.all(func(source):return source.found) and host.active_hotspots.has("hs_chair4") and host.hotspot_nodes["hs_chair4"].visible)
	await aim("hs_chair4",Vector3(1.0,0,0))
	key();await process_frame
	check("第四椅真实E进入照片圈并保持可行走",corridor.layer==5 and not host.player.frozen and not ui.inspector.active)
	check("第六层无旧热区且没有便携收集",corridor.layer==5 and host.active_hotspots.is_empty() and not root.get_node("GameState").inspected.has("hs_chair4"))
	# 独立失败路径：用真实 E / 转身打破规矩，确认只重置本圈且恢复移动。
	corridor._enter(1);await physics_frame
	await aim("hs_darkroom_door",Vector3(0,0,1.1))
	key();await process_frame;await process_frame
	host.player.rotation.y=PI
	await create_timer(.15).timeout
	check("铃响回头触发跳针且冻结期间不重复触发",corridor._resetting and host.player.frozen)
	await create_timer(.8).timeout
	check("跳针只回本圈并恢复输入",corridor.layer==1 and not corridor._resetting and not host.player.frozen and (host.player.global_position-corridor.global_position).length()<.3)
	await create_timer(1.0).timeout
	check("跳针后没有遗留重置协程",not corridor._resetting and corridor._layer_t>.8)
	corridor._enter(2);await physics_frame
	host.player.place(corridor.global_position+Vector3(0,.03,-5),0)
	await create_timer(.2).timeout
	host.player._update_hover();key();await create_timer(.15).timeout
	check("第三圈真实E回答触发规矩失败",corridor._resetting and host.player.frozen)
	await create_timer(.8).timeout
	check("回答后重置本圈且可以继续玩",corridor.layer==2 and not host.player.frozen and not corridor._answered)
	# 已启用目标与相邻房间隔一面墙，距离在交互范围内，仍不可穿墙选择。
	corridor._enter(1);await physics_frame
	host.player.place(corridor.global_position+Vector3(-3,.03,-4.35),0)
	await create_timer(.1).timeout
	var target: Node3D=host.hotspot_nodes["hs_room_1"]
	host.player.cam.look_at(target.global_position)
	host.player._update_hover()
	check("遮挡反例确实在交互距离内",host.player.cam.global_position.distance_to(target.global_position)<2.4)
	check("房间隔墙阻止选中真实目标",host.player._hover!="hs_room_1")
	for i in 6:
		corridor._enter(i);await physics_frame
		for n in range(1,4):
			var wall: Node3D=corridor._part("wall_%d"%n)
			var solid: CollisionObject3D=wall.get_node("StaticBody3D")
			check("圈%d门%d墙补片显隐与实体同步"%[i+1,n],wall.visible==(i>n) and (solid.collision_layer!=0)==wall.visible)
	if DisplayServer.get_name()!="headless":
		await RenderingServer.frame_post_draw
		root.get_texture().get_image().save_png("/tmp/dm-corridor-interaction.png")
	corridor.running=false
	print("CORRIDOR_INTERACTION failures=",failures)
	main.queue_free();await process_frame;quit(0 if failures==0 else 1)
