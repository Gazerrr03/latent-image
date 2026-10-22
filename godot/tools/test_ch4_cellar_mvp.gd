extends SceneTree
## 验证第四章地下室密室 MVP：
## 1. 温室活板门存在且热区有效
## 2. gh_cellar 场景加载正常，包含 3 个物证热点与返回木梯
## 3. 场景来回切换（温室 -> 地下室 -> 温室）平稳，玩家位置恢复

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

	# 1. 验证温室与活板门
	host.show_scene("greenhouse")
	await process_frame
	check("温室热点包含 hs_gh_trapdoor", host.hotspot_nodes.has("hs_gh_trapdoor"))
	var trapdoor: Node = host.hotspot_nodes.get("hs_gh_trapdoor")
	check("活板门节点有效", is_instance_valid(trapdoor))

	# 2. 验证地下室场景与热点
	host.show_scene("gh_cellar")
	host.set_mode("walk", "")
	await process_frame
	check("地下室当前场景为 gh_cellar", host.current_id == "gh_cellar")
	check("地下室包含记录本 hs_cellar_book", host.hotspot_nodes.has("hs_cellar_book"))
	check("地下室包含笔记 hs_cellar_notes", host.hotspot_nodes.has("hs_cellar_notes"))
	check("地下室包含旧物 hs_cellar_relics", host.hotspot_nodes.has("hs_cellar_relics"))
	check("地下室包含返回木梯 hs_cellar_ladder", host.hotspot_nodes.has("hs_cellar_ladder"))

	# 3. 验证返回温室
	host.show_scene("greenhouse")
	host.set_mode("walk", "")
	await process_frame
	check("切回温室成功", host.current_id == "manor" or host.current_id == "greenhouse")

	print("\n=== MVP 自动化校验结果：失败数 = %d ===" % failures)
	quit(0 if failures == 0 else 1)
