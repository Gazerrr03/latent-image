extends SceneTree
var Catalog:GDScript
var failures:=0
func _initialize():call_deferred("run")
func check(label:String,ok:bool):
	print("PASS " if ok else "FAIL ",label)
	if not ok:failures+=1
func key(code:Key):
	var event:=InputEventKey.new();event.physical_keycode=code;event.keycode=code;event.pressed=true;root.push_input(event,true);event=event.duplicate();event.pressed=false;root.push_input(event,true)
func find(node:Node,wanted:String)->Node:
	if String(node.name)==wanted:return node
	for child in node.get_children():
		var found=find(child,wanted)
		if found:return found
	return null
func group(director):await director._inspect(["hs_con_ringbox"],"walk")
func run():
	root.get_node("GameState").persist=false
	var main=load("res://main.tscn").instantiate();root.add_child(main);await process_frame
	create_timer(60).timeout.connect(func():printerr("RINGBOX timeout");quit(2))
	var state=root.get_node("GameState");state.reset()
	var director=root.get_node("Director");var host=director.world;var viewer=director.ui.inspector
	director.ui.menus.hide();director.ui.eyelids_set(1.0);director.ui.set_cinematic(false)
	host.show_scene("con_room");state.shot="C2-04";host.apply_room_states(state.shot);host.set_mode("walk","")
	Catalog=load("res://ui/inspection_catalog.gd")
	var data:Dictionary=Catalog.hotspot("hs_con_ringbox",host)
	check("戒指盒使用可拿起的原生几何",data.mode=="portable" and data.sources.size()==1)
	if data.sources.is_empty():quit(1);return
	var source:MeshInstance3D=data.sources[0];var parent:MeshInstance3D=source.get_parent()
	check("仅盒体与白缎内衬两材质分离",source.mesh.get_surface_count()==2)
	var native=load("res://art/levels/manor/room_con_room.gltf").instantiate()
	var original:MeshInstance3D=find(native,String(parent.name))
	var selected:=ArrayMesh.new();var remainder:=ArrayMesh.new()
	for i in original.mesh.get_surface_count():
		var material:Material=original.mesh.surface_get_material(i)
		var output:=selected if material.resource_name in ["manor_室内_藏青丝绒","manor_室内_白缎"] else remainder
		output.add_surface_from_arrays(original.mesh.surface_get_primitive_type(i),original.mesh.surface_get_arrays(i))
	check("戒指盒全部顶点与原模型逐面一致",source.mesh.get_faces()==selected.get_faces())
	check("账簿发刷香水等其余几何原样保留",parent.mesh.get_faces()==remainder.get_faces())
	check("原物件坐标和尺寸不变",source.transform==Transform3D.IDENTITY and parent.transform==original.transform and source.mesh.get_aabb()==selected.get_aabb())
	native.free()
	var source_faces:=source.mesh.get_faces();var parent_faces:=parent.mesh.get_faces();var source_pose:=source.global_transform
	host.player.place(Vector3(5.50,3.63,-8.11),0);await physics_frame;await physics_frame
	group(director);host.player.cam.look_at(host.hotspot_nodes["hs_con_ringbox"].global_position);host.player._update_hover()
	check("实际站位E提示是戒指盒",host.player._hover=="hs_con_ringbox")
	key(KEY_E);await create_timer(.3).timeout
	check("真实E浮出且只隐藏戒指盒",viewer.active and viewer._portable and not source.visible and parent.visible and parent.mesh.get_faces()==parent_faces)
	var old_basis:Basis=viewer._pivot.basis
	var click:=InputEventMouseButton.new();click.button_index=MOUSE_BUTTON_LEFT;click.pressed=true;click.position=Vector2(400,300);root.push_input(click,true)
	var motion:=InputEventMouseMotion.new();motion.relative=Vector2(50,-30);root.push_input(motion,true)
	click=click.duplicate();click.pressed=false;root.push_input(click,true)
	var wheel:=InputEventMouseButton.new();wheel.button_index=MOUSE_BUTTON_WHEEL_UP;wheel.pressed=true;root.push_input(wheel,true)
	check("原物件支持拖动旋转与滚轮放大",not viewer._pivot.basis.is_equal_approx(old_basis) and viewer._zoom>1.0)
	var viewed:Basis=viewer._pivot.basis;var zoom:float=viewer._zoom
	key(KEY_F);check("戒指盒文字阅读可打开",viewer.reading)
	key(KEY_ESCAPE);check("阅读退出保留观察角度与缩放",viewer.active and not viewer.reading and viewer._pivot.basis.is_equal_approx(viewed) and viewer._zoom==zoom)
	key(KEY_R);check("复位恢复默认观察状态",viewer._zoom==1.0 and viewer._spin==Vector2.ZERO)
	if DisplayServer.get_name()!="headless":
		await RenderingServer.frame_post_draw;root.get_texture().get_image().save_png("/tmp/dm-ringbox-inspection.png")
	key(KEY_ESCAPE);await create_timer(.25).timeout
	check("退出恢复原位物件并只记录一次",not viewer.active and source.visible and parent.visible and source.global_transform==source_pose and state.inspected.count("hs_con_ringbox")==1)
	host.player.cam.look_at(host.hotspot_nodes["hs_con_ringbox"].global_position);host.player._update_hover();key(KEY_E);await create_timer(.3).timeout
	check("同一戒指盒可重复拿起",viewer.active and viewer._data.get("hotspot","")=="hs_con_ringbox")
	key(KEY_ESCAPE);await create_timer(.25).timeout
	check("重复检视不虚构证据或重复记录",state.inspected.count("hs_con_ringbox")==1 and state.evidence.is_empty())
	host.show_scene("guest_room")
	var review:Dictionary=Catalog.hotspot("hs_con_ringbox",host,true)
	check("异地复查取同一真实两材质几何",review.mode=="portable" and review.visuals.size()==1 and review.visuals[0].mesh.get_faces()==source_faces)
	print("RINGBOX_INSPECTION failures=",failures)
	main.queue_free();await process_frame;quit(0 if failures==0 else 1)
