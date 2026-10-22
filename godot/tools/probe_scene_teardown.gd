extends SceneTree
## 对照：加载与切换相同房间，但从不打开检视器，比较退出时的渲染资源警告。
func _initialize() -> void:
	call_deferred("run")

func run() -> void:
	root.get_node("GameState").persist = false
	var main: Node = load("res://main.tscn").instantiate()
	root.add_child(main)
	await process_frame
	root.get_node("GameState").reset()
	var director := root.get_node("Director")
	director.ui.menus.hide()
	for room in ["guest_room", "darkroom"]:
		director.world.show_scene(room)
		director.world.set_mode("walk", "")
		await create_timer(0.3).timeout
		await RenderingServer.frame_post_draw
	assert(not director.ui.inspector.active)
	print("TEARDOWN_BASELINE: no inspection opened")
	main.queue_free()
	await process_frame
	await process_frame
	await RenderingServer.frame_post_draw
	quit()
