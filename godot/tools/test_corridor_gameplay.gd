extends SceneTree
## 玩法验收：从 C5-04 降灵会，经真实 C5-06 入口，用玩家输入走六圈、进支线、按 E，再回到 C5-07。
## --fixed-fps 60 可加速无界面运行；不使用 autoplay（该模式会跳过回廊）。
var failures := 0
var checks := 0
var host: Node
var corridor: Node
var ui: Node
var state: Node
var director: Node
var output := ""
var report: Array = []
var skip_rooms := false
func _initialize(): call_deferred("run")
func check(label: String, ok: bool):
	checks += 1
	print("PASS " if ok else "FAIL ", label)
	report.append({"check":label,"pass":ok})
	if not ok: failures += 1
func key(code := KEY_E):
	var e := InputEventKey.new(); e.keycode=code; e.physical_keycode=code; e.pressed=true
	root.push_input(e,true); e=e.duplicate(); e.pressed=false; root.push_input(e,true)
func accept_text():
	var e := InputEventKey.new();e.keycode=KEY_ENTER;e.physical_keycode=KEY_ENTER;e.pressed=true
	root.push_input(e,true);e=e.duplicate();e.pressed=false;root.push_input(e,true)
func settle(frames := 3):
	for i in frames: await physics_frame
func local_pos() -> Vector3: return host.player.global_position-corridor.global_position
func look_at_point(point: Vector3):
	var d: Vector3 = point-host.player.cam.global_position
	host.player.rotation.y=atan2(-d.x,-d.z)
	host.player._pitch=atan2(d.y,Vector2(d.x,d.z).length())
	host.player.cam.rotation=Vector3(host.player._pitch,0,0)
	host.player._update_hover()
func go(point: Vector3, label: String, tolerance := 0.09):
	# Input 与真实玩家物理帧走动；没有传送、没有直接调用换层。
	var start := local_pos()
	var limit := int(start.distance_to(point)/1.4*60)+240
	var min_y := start.y
	for i in limit:
		var p := local_pos()
		if Vector2(p.x,p.z).distance_to(Vector2(point.x,point.z))<tolerance: break
		look_at_point(corridor.global_position+Vector3(point.x,p.y+1.6,point.z))
		Input.action_press("move_forward")
		await physics_frame
		min_y=minf(min_y,local_pos().y)
	Input.action_release("move_forward")
	await settle()
	var p := local_pos()
	check(label+"可真实行走到达且不掉落",Vector2(p.x,p.z).distance_to(Vector2(point.x,point.z))<tolerance+0.04 and min_y>-0.25)
	print("WALK ",label," end=",p)
func aim(id: String, label: String):
	var target: Node3D=host.hotspot_nodes[id]
	look_at_point(target.global_position)
	await settle()
	check(label+"准星能选中且动词正确",host.player._hover==id and host.target_label(id).begins_with(root.get_node("ContentDB").hotspots[id].verb+"："))
	# 使用玩家胶囊的实际高度和台阶留量测站位（不把地毯当成穿模）。
	var query := PhysicsShapeQueryParameters3D.new()
	var capsule := CapsuleShape3D.new(); capsule.radius=.29; capsule.height=1.43
	query.shape=capsule; query.collision_mask=1
	query.transform=Transform3D(Basis.IDENTITY,host.player.global_position+Vector3.UP*1.035)
	query.exclude=[host.player.get_rid()]
	check(label+"交互站位没有实体穿插",host.player.get_world_3d().direct_space_state.intersect_shape(query,1).is_empty())
	if output!="" and DisplayServer.get_name()!="headless":
		await RenderingServer.frame_post_draw
		root.get_texture().get_image().save_png(output+"/"+label+".png")
	# 稍微偏离中心仍能拾取；测试后回正，按键必须走真实分发链。
	var yaw: float=host.player.rotation.y
	for offset in [-0.02,0.02]:
		host.player.rotation.y=yaw+offset; host.player._update_hover()
		check(label+"准星边缘可操作 "+str(offset),host.player._hover==id)
	host.player.rotation.y=yaw; host.player._update_hover()
func exit_layer(n: int):
	await go(Vector3(0,0,-8),"第%d圈转角"%(n+1))
	await go(Vector3(-corridor._seg_b+1.0,0,-8),"第%d圈出口"%(n+1))
	await aim("hs_doorway","圈%d-尽头门"%(n+1))
	key(); await settle()
	check("第%d圈按E才换到下一圈"%(n+1),corridor.layer==n+1)
func side_room(n: int):
	var z: float=-corridor.DOORS[n-1]
	await go(Vector3(0,0,z),"支线%d门前"%n)
	await aim("hs_corridor_door_%d"%n,"支线%d-推门"%n)
	key(); await settle()
	check("支线%d门扇真实打开"%n,absf(corridor._part("door_%d"%n).rotation.y-corridor._door_yaws[n])>1.5)
	await go(Vector3(-1.5,0,z),"支线%d穿过门洞"%n)
	if n==1:
		await go(Vector3(-2.6,0,-6.0),"衣帽间空挂钩前")
	elif n==2:
		await go(Vector3(-1.9,0,-3.4),"空房间圆圈旁")
	else:
		await go(Vector3(-1.5,.9,1.38),"窄楼梯第一跑")
		await go(Vector3(0,.9,1.38),"楼梯内窗平台")
	await aim("hs_room_%d"%n,"支线%d-观察"%n)
	var before: int=state.journal.size()
	key(); await settle()
	check("支线%d观察E有真实反馈并保持行走"%n,state.journal.size()==before+1 and state.evidence.has(corridor.ROOM_NOTES[n-1]) and ui.toast_label.text.contains(corridor._room_observations[n-1]) and not host.player.frozen and not ui.inspector.active)
	key(); await settle()
	check("支线%d重复观察不重复记笔记"%n,state.journal.size()==before+1)
	key(KEY_TAB); await settle()
	var note_id: String=corridor.ROOM_NOTES[n-1]
	check("支线%d观察可在Tab笔记本中找到"%n,ui.board.visible and ui.board.cards.has(note_id))
	ui.board.cards[note_id].grab_focus();accept_text();await create_timer(.4).timeout
	check("支线%d笔记本记录可以打开阅读"%n,ui.inspector.active and ui.inspector._data.notes.contains(corridor._room_observations[n-1]))
	if output!="" and DisplayServer.get_name()!="headless":
		await RenderingServer.frame_post_draw
		root.get_texture().get_image().save_png(output+"/支线%d-笔记本.png"%n)
	key(KEY_ESCAPE);await create_timer(.4).timeout
	key(KEY_TAB);await create_timer(.2).timeout
	check("支线%d合上笔记本恢复现场行走"%n,not ui.inspector.active and not ui.board.visible and not host.player.frozen)
	if n==3:
		await go(Vector3(1.8,1.98,1.38),"窄楼梯第二跑近顶")
		check("窄楼梯真实爬高",local_pos().y>1.7)
		await go(Vector3(0,.9,1.38),"窄楼梯回到平台")
		await go(Vector3(-1.5,.9,1.38),"窄楼梯平台回转")
		await go(Vector3(-1.5,0,z),"窄楼梯下楼")
	else:
		await go(Vector3(-1.5,0,z),"支线%d返回门洞"%n)
	await go(Vector3(0,0,z),"支线%d回走廊"%n)
	check("支线%d离开后门关闭且旧入口失效"%n,corridor._room_left and not host.active_hotspots.has("hs_corridor_door_%d"%n))
func run():
	for arg in OS.get_cmdline_user_args():
		if arg.begins_with("--evidence="): output=arg.trim_prefix("--evidence=")
		if arg=="--skip-rooms": skip_rooms=true
	if output!="":DirAccess.make_dir_recursive_absolute(output)
	state=root.get_node("GameState");state.persist=false
	var main=load("res://main.tscn").instantiate();root.add_child(main);await process_frame
	director=root.get_node("Director");host=director.world;ui=director.ui
	state.reset();ui.menus.hide();ui.eyelids_set(1.0)
	create_timer(600).timeout.connect(func():printerr("GAMEPLAY timeout");quit(2))
	# C5-06 的 corridor() 是正式分镜入口；autoplay 始终关闭。
	director.start("C5-04")
	for i in 1800:
		await process_frame
		if host.corridor!=null and host.corridor.running:break
		if ui._waiting and i % 12 == 0:accept_text()
	corridor=host.corridor
	check("C5-06正式入口进入Blender关卡且可以操作",corridor!=null and corridor.scene_file_path=="res://levels/ded_corridor.tscn" and corridor.running and host.player.active and not host.player.frozen and ui.crosshair.visible)
	check("模型来自Blender GLB",corridor.get_node("模型").scene_file_path.ends_with("ded_corridor.glb"))
	check("第一圈只有尽头门可操作",host.active_hotspots==["hs_doorway"])
	await go(Vector3(0,0,-8), "第一圈声音测试转角")
	await go(Vector3(-2.5,0,-8), "第一圈正走")
	check("正走唱针正放且底色持续",corridor._speed>0.12 and corridor._audio_fwd.playing and corridor._bed_fwd.playing)
	await go(Vector3(-1.2,0,-8), "第一圈倒走")
	check("倒走唱针与底色都倒放",corridor._speed<-.12 and corridor._audio_rev.playing and corridor._bed_rev.playing and corridor._bed_back)
	await create_timer(.8).timeout
	check("停步人声停止且底色仍在",not corridor._audio_fwd.playing and not corridor._audio_rev.playing and (corridor._bed_fwd.playing or corridor._bed_rev.playing))
	await exit_layer(0)
	if not skip_rooms: await side_room(1)
	await go(Vector3(0,0,-7.35),"第二圈暗房门前")
	await aim("hs_darkroom_door","圈2-暗房敲门")
	key();await settle()
	check("暗房敲门有回应且不打开检视器",corridor._knocked and ui.toast_label.text.contains("两下") and not ui.inspector.active)
	await exit_layer(1)
	check("第三圈隐藏暗房门入口",not host.active_hotspots.has("hs_darkroom_door"))
	if not skip_rooms: await side_room(2)
	# 处于相邻房间时，对准同一目标必须被墙挡住。
	await go(Vector3(0,0,-1.3),"第三圈遮挡测试走廊")
	look_at_point(host.hotspot_nodes["hs_room_2"].global_position)
	check("不能隔墙观察空房间圆圈",host.player._hover!="hs_room_2")
	await exit_layer(2)
	if not skip_rooms: await side_room(3)
	await go(Vector3(0,0,-7.35),"第四圈暗房门前")
	await aim("hs_darkroom_door","圈4-暗房无回应")
	key();await settle()
	check("第四圈暗房E反馈无回应",ui.toast_label.text.contains("没有声音"))
	await create_timer(5.2).timeout
	await exit_layer(3)
	check("第五圈三处声音未齐不能坐第四椅",not host.active_hotspots.has("hs_chair4"))
	for z in [-1.2,-3.6,-6.0]:
		await go(Vector3(0,0,z),"第五圈听声 "+str(z))
	check("沿走廊真实找到三个声音及椅子",corridor._sources.all(func(s):return s.found) and corridor._chairs.all(func(c):return c.visible))
	await go(Vector3(0,0,-8),"第五圈转角")
	await go(Vector3(-.8,0,-8),"第五圈第四椅前")
	await aim("hs_chair4","圈5-第四椅")
	key();await settle()
	check("第四椅进入第六圈并继续可行走",corridor.layer==5 and not host.player.frozen and not ui.inspector.active)
	check("第六圈门消失照片显示且旧交互清空",not corridor._part("door_end").visible and corridor._part("photo_wall").visible and host.active_hotspots.is_empty())
	await go(Vector3(0,0,-8),"第六圈转角")
	# go 的终点在照片传送阈值之前；随后用真实 W 穿入照片。
	await go(Vector3(-.85,0,-8),"第六圈照片前")
	look_at_point(corridor.global_position+Vector3(-2,1.6,-8))
	Input.action_press("move_forward")
	for i in 120:
		await physics_frame
		if corridor._in_photo:break
	Input.action_release("move_forward");await settle()
	check("真实走近照片进入温室小路",corridor._in_photo and local_pos().x>29 and not host.player.frozen)
	await go(Vector3(30,.03,-2.7),"温室小路人影身后")
	await aim("hs_corridor_figure","圈6-伸手")
	key();await settle()
	check("真实E伸手人影消失玩家站在照片位置",corridor._touching and not corridor._part("gh_figure").visible and host.player.frozen)
	await create_timer(1).timeout
	# 按真实 UI 继续输入读完最后那句话，然后正常回到 C5-07。
	for i in 120:
		accept_text();await create_timer(.05).timeout
		if state.shot=="C5-07":break
	check("回廊正常结束回到C5-07",state.shot=="C5-07" and not corridor.running)
	check("四条回廊证据全部收入",["ev_knock_twice","ev_seance_voice","ev_sync_steps","ev_fourth_chair"].all(func(id):return state.evidence.has(id)))
	check("三间支线观察都有记录",state.journal.filter(func(e):return e.kind=="observation").size()==(0 if skip_rooms else 3))
	print("CORRIDOR_GAMEPLAY checks=",checks," failures=",failures)
	if output!="":
		var file=FileAccess.open(output+"/玩法判定.json",FileAccess.WRITE)
		file.store_string(JSON.stringify({"checks":checks,"failures":failures,"results":report},"\t"))
	await director.stop();await process_frame
	main.queue_free();await process_frame;quit(0 if failures==0 else 1)
