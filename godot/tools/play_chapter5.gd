extends SceneTree
## 独立试玩第 5 章回廊。默认直接进入；--intro 从降灵会仪式开始。
## Godot --path godot --script res://tools/play_chapter5.gd [-- --intro]
## 不自动操作、不截图退出、不写正式存档；通关后正常衔接 C5-07。

func _initialize() -> void:
	call_deferred("_play")


func _play() -> void:
	var state := root.get_node("GameState")
	state.persist = false
	var main: Node = load("res://main.tscn").instantiate()
	root.add_child(main)
	await process_frame
	state.reset()
	state.set_leak(2)
	var director := root.get_node("Director")
	director.ui.menus.hide()
	director.ui.eyelids_set(1.0)
	var first := "C5-04" if OS.get_cmdline_user_args().has("--intro") else "C5-06"
	director.start(first)
	print("CHAPTER5_PLAY start=", first, " persist=", state.persist, " autoplay=", director.autoplay)
