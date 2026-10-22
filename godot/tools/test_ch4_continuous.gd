extends SceneTree
## 验证从 C4-01 开始的完整第四章连续体验：
## 1. C4-01 醒来进入自由探索
## 2. 温室与吉迪恩对话 (C4-02, C4-03)
## 3. 温室活板门下地窖 (C4-09)
## 4. 地下暗房：4 项物证 -> 拿起相机 -> 举镜对焦快门显影收人 -> 爬梯返回温室
## 5. 返回温室继续探索花园百叶风口 (C4-04)
## 6. 回客房 (c4_return) -> 书桌连线 (C4-05, d4) -> 听话 (C4-06) -> 打字 (C4-07) -> 睡下 (C4-08) -> 进 C5-01

var failures := 0

func _initialize() -> void:
	call_deferred("run")

func check(label: String, ok: bool) -> void:
	print("PASS " if ok else "FAIL ", label)
	if not ok:
		failures += 1

func run() -> void:
	root.get_node("GameState").persist = false
	var main: Node = load("res://main.tscn").instantiate()
	root.add_child(main)
	await process_frame
	root.get_node("GameState").reset()

	var director := root.get_node("Director")
	var host: Node = director.world
	director.ui.menus.hide()
	director.autoplay = true

	# 从 C4-01 启动
	var state: Node = root.get_node("GameState")
	print(">>> 启动第四章 C4-01")
	director.start("C4-01")
	await process_frame

	# 等待探索与关卡推进
	var max_ticks := 300
	while max_ticks > 0 and director._running:
		await process_frame
		max_ticks -= 1
		# 如果已经进入了第 5 章，说明第 4 章已完整连续跑通
		if state.shot.begins_with("C5"):
			break

	print(">>> 最终停留在镜号：", state.shot)
	print(">>> 已完成任务：", state.quests_done)
	print(">>> 已获得证据：", state.evidence.size(), "件")
	print(">>> 已完成连线：", state.links_done)

	check("成功完成 c4_gideon 任务", state.quests_done.has("c4_gideon"))
	check("成功完成 c4_cellar 密室任务", state.quests_done.has("c4_cellar"))
	check("成功完成 c4_vent 花园风口任务", state.quests_done.has("c4_vent"))
	check("成功完成 c4_return 回客房任务", state.quests_done.has("c4_return"))
	check("成功完成 D4 推论连线", state.links_done.has("d4"))
	check("第四章已顺利闭环流转至第五章", state.shot.begins_with("C5"))

	print("\n=== 第四章完整连续体验测试结果：失败数 = %d ===" % failures)
	quit(0 if failures == 0 else 1)
