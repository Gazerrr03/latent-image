extends SceneTree

var failures := 0

func _initialize():
	call_deferred("run")

func check(label: String, ok: bool):
	print("PASS " if ok else "FAIL ", label)
	if not ok:
		failures += 1

func run():
	root.get_node("GameState").persist = false
	var main = load("res://main.tscn").instantiate()
	root.add_child(main)
	await process_frame
	create_timer(40).timeout.connect(func():
		printerr("TEST timeout")
		quit(2))
	var director = root.get_node("Director")
	var ui = director.ui
	director.autoplay = false

	# 1. 初始状态：眼睑全睁开，特效不可见
	ui.eyelids_set(1.0)
	check("初始眼睑 open 为 1.0", is_equal_approx(ui._lid_value(), 1.0))
	check("初始眼睑 lids 不可见", not ui.lids.visible)

	# 2. 执行 eyelids_close()
	print("--- 测试 eyelids_close() ---")
	await ui.eyelids_close()
	check("闭眼完成且黑屏后，interlude_layer 显示且不透明", ui.interlude_layer.visible and ui.interlude_layer.modulate.a >= 0.99)
	check("闭眼完成且黑屏后，眼睑 open 为 1.0", is_equal_approx(ui._lid_value(), 1.0))
	check("闭眼完成且黑屏后，眼睑 lids 已移除（不可见）", not ui.lids.visible)

	# 3. 梦境播放片段：测试 dream 流程中片段展示时眼睑不遮挡
	print("--- 测试 dream 播放梦境片段 ---")
	var run_dream := func():
		await ui.dream([], "梦_r0")
	run_dream.call()

	for i in 60:
		if ui.footage.playing:
			break
		await process_frame
	check("梦境片段开始播放", ui.footage.playing)
	check("放照片时黑场已让开（隐藏）", not ui.interlude_layer.visible)
	check("放照片时眼睑特效已被移除（不可见）", not ui.lids.visible)
	check("放照片时图片根节点可见", ui.footage._img_layer.get_node("img_root").visible)

	# 取消片段播放
	ui.footage.cancel()
	await create_timer(0.5).timeout

	# 4. 醒来流程：wake_up 重新设置 eyelids_set(0.0) 并执行 eyelids_open
	print("--- 测试 wake_up 流程 ---")
	director.world.show_scene("guest_room")
	var run_wake := func():
		await director.world.wake_up()
	run_wake.call()
	await process_frame
	check("wake_up 启动时眼睑关闭 (0.0) 且可见", is_equal_approx(ui._lid_value(), 0.0) and ui.lids.visible)
	await director.world.wake_up() # 直接等待执行完成
	check("wake_up 完成后眼睑全睁 (1.0) 且不可见", is_equal_approx(ui._lid_value(), 1.0) and not ui.lids.visible)

	print("测试完成，失败数: ", failures)
	quit(1 if failures > 0 else 0)
