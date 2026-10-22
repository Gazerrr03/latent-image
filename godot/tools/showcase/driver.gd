extends RefCounted
## 玩法录屏的自动驾驶：用真正的玩家节点与真正的按键事件，按“剧本”走路、转头、按 E、点击文字。
## 剧本是分号隔开的步骤（shots.csv 的 drive 列）：
##   walk <热区id> [距离]   朝着热区走，到距离（默认 1.2 米）内停下，视线跟着它
##   face <热区id> [秒]     只转头看向它（默认 1 秒）
##   e                      按一下 E（对着准星下的东西）
##   click [次数] [间隔]    点击文字往下走（默认 1 次，间隔 1.2 秒）
##   pick <序号>            选择第几个选项
##   card <证据id>          在证据板上点一张卡
##   examine <证据id>       证据板上拿起一张卡检视
##   wait <秒>
##   key <键名>             按一下某个键（Escape、Tab、Q……）

static func _hotspot(id: String) -> Node3D:
	return Director.world.hotspot_nodes.get(id)


static func _aim(player: Node, target: Vector3, dt: float, rate := 6.0) -> void:
	var from: Vector3 = player.cam.global_position
	var d := target - from
	var yaw := atan2(-d.x, -d.z)
	var pitch := atan2(d.y, Vector2(d.x, d.z).length())
	var k := 1.0 - exp(-rate * dt)
	player.rotation.y = lerp_angle(player.rotation.y, yaw, k)
	player._pitch = lerpf(player._pitch, clampf(pitch, -1.2, 1.2), k)
	player.cam.rotation.x = player._pitch


static func _press(action: String) -> void:
	var ev := InputEventAction.new()
	ev.action = action
	ev.pressed = true
	Input.parse_input_event(ev)
	var up := InputEventAction.new()
	up.action = action
	up.pressed = false
	Input.parse_input_event(up)


static func run(tree: SceneTree, script: String) -> void:
	var player: Node = Director.world.player
	for raw in script.split(";", false):
		var p := raw.strip_edges().split(" ", false)
		if p.is_empty():
			continue
		match p[0]:
			"wait":
				await tree.create_timer(float(p[1])).timeout
			"e":
				_press("interact")
				await tree.create_timer(0.2).timeout
			"key":
				# 真按键（Escape、Tab、Q……），界面层是按键事件收的
				for down in [true, false]:
					var ke := InputEventKey.new()
					ke.keycode = OS.find_keycode_from_string(p[1])
					ke.physical_keycode = ke.keycode
					ke.pressed = down
					Input.parse_input_event(ke)
				await tree.create_timer(0.3).timeout
			"click":
				var n := int(p[1]) if p.size() > 1 else 1
				var gap := float(p[2]) if p.size() > 2 else 1.2
				for i in n:
					Director.ui._resolved.emit(0)
					await tree.create_timer(gap).timeout
			"pick":
				Director.ui._resolved.emit(int(p[1]))
				await tree.create_timer(0.3).timeout
			"card":
				Director.ui.board._on_card(p[1])
				await tree.create_timer(0.8).timeout
			"examine":
				Director.ui.board.examine(p[1])      # 翻开证据板后，把一张卡拿起来看
				await tree.create_timer(0.8).timeout
			"face":
				var secs := float(p[2]) if p.size() > 2 else 1.0
				var node := _hotspot(p[1])
				var t := 0.0
				while t < secs and is_instance_valid(node):
					var dt := 1.0 / 30.0
					_aim(player, node.global_position, dt)
					t += dt
					await tree.process_frame
			"walk":
				var node := _hotspot(p[1])
				var stop := float(p[2]) if p.size() > 2 else 1.2
				var t := 0.0
				while t < 12.0 and is_instance_valid(node):
					var dt := 1.0 / 30.0
					_aim(player, node.global_position, dt)
					var flat := Vector2(node.global_position.x - player.global_position.x, node.global_position.z - player.global_position.z).length()
					if flat <= stop:
						break
					Input.action_press("move_forward")
					t += dt
					await tree.process_frame
				Input.action_release("move_forward")
