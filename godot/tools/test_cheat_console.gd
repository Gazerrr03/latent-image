extends SceneTree

func _initialize() -> void:
	call_deferred("_run_tests")

func _run_tests() -> void:
	print("── 开始测试 CheatConsole ──")
	var gs = root.get_node_or_null("GameState")
	var db = root.get_node_or_null("ContentDB")
	var console = preload("res://ui/cheat_console.gd").new()
	root.add_child(console)

	# 1. 验证解析章节
	assert(console._resolve_shot("0") == "C0-01", "0 应映射到 C0-01")
	assert(console._resolve_shot("c0") == "C0-01", "c0 应映射到 C0-01")
	assert(console._resolve_shot("1") == "C1-01", "1 应映射到 C1-01")
	assert(console._resolve_shot("c1") == "C1-01", "c1 应映射到 C1-01")
	assert(console._resolve_shot("2") == "C2-00", "2 应映射到 C2-00")
	assert(console._resolve_shot("3") == "C3-01", "3 应映射到 C3-01")
	assert(console._resolve_shot("4") == "C4-01", "4 应映射到 C4-01")
	assert(console._resolve_shot("5") == "C5-01", "5 应映射到 C5-01")
	assert(console._resolve_shot("6") == "C6-01", "6 应映射到 C6-01")
	assert(console._resolve_shot("7") == "C7-01", "7 应映射到 C7-01")
	assert(console._resolve_shot("8") == "EP-01", "8 应映射到 EP-01")
	assert(console._resolve_shot("ep") == "EP-01", "ep 应映射到 EP-01")
	assert(console._resolve_shot("C0-05") == "C0-05", "具体镜头 ID 应能直接解析")
	print("✔ 章节与镜头解析测试通过")

	# 2. 验证 speed 指令
	console._execute_command("speed 2.5")
	assert(is_equal_approx(Engine.time_scale, 2.5), "speed 2.5 应生效")
	console._execute_command("speed 1.0")
	assert(is_equal_approx(Engine.time_scale, 1.0), "speed 1.0 应生效")
	print("✔ speed 指令测试通过")

	# 3. 验证 leak 指令
	if gs:
		console._execute_command("leak 3")
		assert(gs.leak_level == 3, "leak 3 应生效")
		console._execute_command("leak 0")
		assert(gs.leak_level == 0, "leak 0 应生效")
		print("✔ leak 指令测试通过")

	# 4. 验证 giveall 指令
	if gs and db:
		console._execute_command("giveall")
		assert(gs.evidence.size() == db.evidence.size(), "giveall 应该发满所有证据")
		print("✔ giveall 指令测试通过")

	# 5. 验证控制台开关状态及全局覆盖交互标志
	assert(not console.visible, "初始应为不可见")
	assert(not console.is_open(), "初始 is_open 应为 false")
	console.toggle_console(true)
	assert(console.visible, "打开后应为可见")
	assert(console.is_open(), "打开后 is_open 应为 true")
	console.toggle_console(false)
	assert(not console.visible, "关闭后应为不可见")
	assert(not console.is_open(), "关闭后 is_open 应为 false")
	print("✔ 控制台开关状态与全局覆盖标志测试通过")

	# 6. 验证按键匹配
	var key_event := InputEventKey.new()
	key_event.pressed = true
	key_event.keycode = KEY_QUOTELEFT
	assert(console._is_toggle_key(key_event), "KEY_QUOTELEFT 应该是有效开关按键")

	var tilde_event := InputEventKey.new()
	tilde_event.pressed = true
	tilde_event.unicode = 126
	assert(console._is_toggle_key(tilde_event), "unicode 126 (~) 应该是有效开关按键")
	print("✔ 按键匹配测试通过")

	print("── 全部测试通过！──")
	quit(0)
