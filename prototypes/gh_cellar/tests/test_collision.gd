extends SceneTree
## 碰撞与行走测试：
## 1. 在房间网格上向下打射线，确认每个点都有地面/家具承接；
## 2. 用玩家胶囊从出生点朝 8 个方向走 3 秒，确认不会掉出房间。

const PLAYER_SCENE := preload("res://player/cellar_player.tscn")
const DIRS := 8
const STEPS := 180

var _ok := true


func _initialize() -> void:
	_run.call_deferred()


func _check(cond: bool, label: String) -> void:
	print(("PASS  " if cond else "FAIL  ") + label)
	if not cond:
		_ok = false


func _run() -> void:
	var level: Node3D = (load("res://levels/gh_cellar.tscn") as PackedScene).instantiate()
	root.add_child(level)
	await process_frame
	await physics_frame
	await physics_frame

	var space := level.get_world_3d().direct_space_state
	var missing := 0
	var total := 0
	for xi in range(-4, 5):
		for zi in range(-3, 4):
			total += 1
			var q := PhysicsRayQueryParameters3D.create(
				Vector3(float(xi), 3.0, float(zi)),
				Vector3(float(xi), -1.0, float(zi)))
			var hit := space.intersect_ray(q)
			if hit.is_empty():
				missing += 1
				print("  no floor at ", xi, ",", zi)
	_check(missing == 0, "floor ray grid %d/%d hits" % [total - missing, total])

	var spawn_player := level.get_node_or_null("Player")
	var spawn: Vector3 = spawn_player.global_position if spawn_player else Vector3(2.15, 0.05, -3.2)
	if spawn_player:
		spawn_player.queue_free()
		await process_frame

	for i in DIRS:
		var yaw := TAU * float(i) / float(DIRS)
		var p: CharacterBody3D = PLAYER_SCENE.instantiate()
		level.add_child(p)
		p.place(spawn, rad_to_deg(yaw))
		await physics_frame
		var dir := Vector3(sin(yaw), 0.0, cos(yaw))
		var min_y := p.global_position.y
		var max_r := 0.0
		for s in STEPS:
			p.walk(dir, 1.0 / 60.0)
			await physics_frame
			min_y = minf(min_y, p.global_position.y)
			max_r = maxf(max_r, Vector2(p.global_position.x, p.global_position.z).length())
		var in_room := absf(p.global_position.x) < 5.2 and absf(p.global_position.z) < 4.2
		_check(min_y > spawn.y - 0.5 and in_room,
			"walk %3d°  end=%s  min_y=%.2f  in_room=%s" %
			[int(rad_to_deg(yaw)), str(p.global_position.snapped(Vector3.ONE * 0.01)), min_y, str(in_room)])
		p.queue_free()
		await process_frame

	print("TEST_COLLISION ", "PASS" if _ok else "FAIL")
	quit(0 if _ok else 1)
