extends SceneTree
## 导入完整性测试：加载密室场景，检查模型、碰撞、灯光、玩家、清单与字体。

var _ok := true


func _initialize() -> void:
	_run.call_deferred()


func _check(cond: bool, label: String) -> void:
	if cond:
		print("PASS  ", label)
	else:
		_ok = false
		push_error("FAIL  " + label)


func _run() -> void:
	var scene: Node3D = (load("res://levels/gh_cellar.tscn") as PackedScene).instantiate()
	root.add_child(scene)
	await process_frame
	await process_frame
	await physics_frame

	var model := scene.get_node_or_null("Art/CellarModel")
	_check(model != null, "Art/CellarModel exists")
	var meshes := scene.find_children("*", "MeshInstance3D", true, false)
	_check(meshes.size() > 1000, "mesh count > 1000 (got %d)" % meshes.size())
	var collision := scene.get_node_or_null("Collision")
	_check(collision != null and collision.get_child_count() >= 10,
		"collision shapes >= 10 (got %d)" % (collision.get_child_count() if collision else 0))
	var lighting := scene.get_node_or_null("Lighting")
	_check(lighting != null and lighting.get_child_count() >= 4,
		"lights >= 4 (got %d)" % (lighting.get_child_count() if lighting else 0))
	var player := scene.get_node_or_null("Player")
	_check(player != null, "Player exists")
	if player:
		var cam := player.get_node_or_null("Camera3D")
		_check(cam != null and cam.current, "player camera is current")
		_check(player.global_position.y > -0.2, "player spawn is above floor")

	var path := "res://art/levels/gh_cellar/cellar_layout.json"
	_check(FileAccess.file_exists(path), "layout json exists")
	if FileAccess.file_exists(path):
		var data = JSON.parse_string(FileAccess.get_file_as_string(path))
		_check(typeof(data) == TYPE_DICTIONARY, "layout json parses")
		if typeof(data) == TYPE_DICTIONARY:
			_check(data.get("frames", []).size() == 9, "9 frame anchors")
			_check(data.get("collision", []).size() == 12, "12 collision entries")
			_check(data.get("spawn", {}).has("position"), "spawn entry exists")
	_check(FileAccess.file_exists("res://art/levels/gh_cellar/gh_cellar.glb"), "glb exists")
	_check(FileAccess.file_exists("res://art/fonts/simhei.ttf"), "CJK font exists")

	print("TEST_IMPORT ", "PASS" if _ok else "FAIL")
	quit(0 if _ok else 1)
