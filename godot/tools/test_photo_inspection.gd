extends SceneTree
## 原位小样、真实动态印字、键盘翻面/阅读，以及十二个容器号的笔记本一致性。
var failures := 0
func _initialize(): call_deferred("run")
func check(label: String, ok: bool):
	print("PASS " if ok else "FAIL ",label)
	if not ok: failures += 1
func key(code: Key):
	var event := InputEventKey.new()
	event.keycode = code
	event.physical_keycode = code
	event.pressed = true
	root.push_input(event,true)
	event = event.duplicate()
	event.pressed = false
	root.push_input(event,true)
func group(director): await director._inspect(["hs_se_photo"],"walk")
func run():
	root.get_node("GameState").persist = false
	var main = load("res://main.tscn").instantiate()
	root.add_child(main)
	await process_frame
	var state = root.get_node("GameState")
	create_timer(120.0).timeout.connect(func():
		printerr("PHOTO_INSPECTION timeout")
		quit(2))
	state.reset()
	state.container = "03"
	state.shot = "C5-03"
	var director = root.get_node("Director")
	var host = director.world
	var ui = director.ui
	var inspector = ui.inspector
	ui.menus.hide()
	ui.eyelids_set(1.0)
	ui.set_cinematic(false)
	host.show_scene("seance")
	host.apply_room_states("C5-03")
	host.set_mode("walk","")
	var native: MeshInstance3D
	for node in host._walk(host.room):
		if String(node.name) == "客厅·合影小样（背面朝上） hs_se_photo":native = node
	check("小样回接原模型与状态层",native != null and native.has_meta("inspection_document") and native.layers == 0)
	if native == null or not native.has_meta("inspection_document"):
		quit(1)
		return
	var document: Node3D = native.get_meta("inspection_document")
	check("原位背面向上且现代印字跟随本局",document.back.global_basis.z.dot(Vector3.UP)>.99 and document.back_label.text == "#03 / 12  SYNC" and document.back_label.is_visible_in_tree())
	var rows = JSON.parse_string(FileAccess.get_file_as_string("res://../docs/验证/2026-10-20-物品检视/逐对象判定.json"))
	for row in rows:
		if row.id == "hs_se_photo":
			var feet = row.feet
			host.player.place(Vector3(feet[0],feet[1],feet[2]),0)
	await physics_frame
	await physics_frame
	group(director)
	host.player.cam.look_at(host.hotspot_nodes["hs_se_photo"].global_position)
	host.player._update_hover()
	check("现场E提示小样",host.player._hover == "hs_se_photo")
	key(KEY_E)
	for frame in 180:
		if inspector.active:break
		await process_frame
	await create_timer(.3).timeout
	check("E拿起真实小样且默认仍观察背面",inspector.active and inspector._portable and inspector._flipped and inspector._model != null)
	if not inspector.active:
		quit(1)
		return
	check("背面操作提示为阅读",inspector._read_button.text.contains("阅读"))
	check("拿起后原位印字随背面一起隐藏",not document.back_label.is_visible_in_tree())
	check("预览实物背面印字不是固定模板",inspector._model.back_label.text == "#03 / 12  SYNC" and inspector._model.back_label.visible)
	if DisplayServer.get_name() != "headless":
		await RenderingServer.frame_post_draw
		root.get_texture().get_image().save_png("/tmp/dm-photo-back.png")
	key(KEY_F)
	await process_frame
	check("背面清晰阅读与物理印字相同",inspector.reading and inspector._text.text == inspector._model.back_label.text)
	key(KEY_ESCAPE)
	key(KEY_V)
	await create_timer(.3).timeout
	if inspector._model.front.material_override.albedo_texture == null:
		check("正面贴图可加载", false)
		quit(1)
		return
	check("翻面展示真实照片正面",not inspector._flipped and is_zero_approx(inspector._object_yaw) and inspector._model.front.material_override.albedo_texture.resource_path.contains("ev_photo_back_0_front"))
	check("正面操作提示为描述",inspector._read_button.text.contains("描述"))
	if DisplayServer.get_name() != "headless":
		await RenderingServer.frame_post_draw
		root.get_texture().get_image().save_png("/tmp/dm-photo-front.png")
	key(KEY_R)
	await process_frame
	check("复位回到默认背面",inspector._flipped and is_equal_approx(inspector._object_yaw,PI))
	inspector.close(true)
	check("放下原位印字恢复并只收入一次",document.back_label.is_visible_in_tree() and state.evidence.has("ev_photo_back") and state.inspected.count("hs_se_photo") == 1)
	host.show_scene("guest_room")
	for number in range(1,13):
		state.container = "%02d" % number
		ui.inspect_evidence("ev_photo_back","","")
		await process_frame
		var expected = "#%02d / 12  SYNC" % number
		check("异地笔记本动态编号 " + str(number),inspector._portable and inspector._flipped and inspector._model.back_label.text == expected and inspector._data.back_pages[0] == expected)
		inspector.close(true)
	print("PHOTO_INSPECTION failures=",failures)
	main.queue_free()
	await process_frame
	await process_frame
	quit(0 if failures == 0 else 1)
