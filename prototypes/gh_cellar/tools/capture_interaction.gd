extends SceneTree
## 新交互截图：纸签/记录本第4页/第7页钥匙/1926实体底片/放回结局。

func _initialize() -> void:
	_run.call_deferred()


func _wait(n: int) -> void:
	for i in n:
		await process_frame


func _shot(dir: String, name: String) -> void:
	var img := get_root().get_texture().get_image()
	img.save_png(dir + "/" + name + ".png")
	print("CAPTURED ", name)


func _look(player: CharacterBody3D, stand: Vector3, target: Vector3) -> void:
	player.global_position = stand
	player.camera.current = true
	player.camera.look_at(target, Vector3.UP)
	await physics_frame
	await physics_frame


func _page_index(pages: Array, id: String) -> int:
	for i in pages.size():
		if String(pages[i].get("id", "")) == id:
			return i
	return 0


func _run() -> void:
	var level: Node3D = (load("res://levels/gh_cellar.tscn") as PackedScene).instantiate()
	root.add_child(level)
	await process_frame
	await physics_frame
	var out_dir := ProjectSettings.globalize_path("res://review/gh_cellar")
	DirAccess.make_dir_recursive_absolute(out_dir)
	var player: CharacterBody3D = level.get_node("Player")

	await _look(player, Vector3(1.55, 0.0, -1.55), Vector3(0.45, 1.16, -0.45))
	await _wait(20)
	await _shot(out_dir, "20_table_tag_notebook")

	var state = level.state
	state.mark_notebook_opened()
	state.pickup_camera()
	state.plate_state = "DEVELOPED"
	state.unlock("first")
	state.unlock("second")
	var pages: Array = state.notebook_pages()
	level.ui.open_notebook(pages, _page_index(pages, "second"))
	await _wait(10)
	await _shot(out_dir, "21_notebook_page4")

	level.ui.close_notebook()
	state.key_seen = true
	state.unlock("key")
	pages = state.notebook_pages()
	level.ui.open_notebook(pages, _page_index(pages, "key"))
	await _wait(10)
	await _shot(out_dir, "22_notebook_key")
	level.ui.close_notebook()
	await _wait(5)
	await _shot(out_dir, "23_key_on_notebook")

	state.box_open = true
	state.owner_seen = true
	level._on_state_changed()
	await _look(player, Vector3(-3.1, 0.0, 2.85), Vector3(-4.15, 1.02, 2.85))
	await _wait(15)
	await _shot(out_dir, "24_plate_1926")

	state.plate_1926_taken = true
	state.return_1926_plate()
	await _wait(10)
	await _shot(out_dir, "25_ending_keep")
	quit(0)
