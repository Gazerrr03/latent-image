extends SceneTree
## 主工程地下室实际窗口抽样，不代表全程性能。
func _initialize() -> void: call_deferred("run")
func run() -> void:
	root.get_node("GameState").persist = false
	root.add_child(load("res://main.tscn").instantiate())
	await process_frame
	var d = root.get_node("Director")
	d.ui.menus.hide()
	d.world.show_scene("gh_cellar")
	d.world.set_mode("walk", "")
	await create_timer(2).timeout
	var start := Time.get_ticks_msec()
	var frames := 0
	while Time.get_ticks_msec() - start < 8000:
		await process_frame
		frames += 1
	var fps: float = frames * 1000.0 / (Time.get_ticks_msec() - start)
	print("CELLAR_FPS resolution=1280x720 duration=8s mean=", fps)
	quit(0 if fps >= 45 else 1)
