extends SceneTree

var failures := 0

func _initialize():
	call_deferred("run")

func check(label: String, ok: bool):
	print("PASS " if ok else "FAIL ", label)
	if not ok:
		failures += 1

func run():
	root.get_node("GameState").persist = false
	var main = load("res://main.tscn").instantiate()
	root.add_child(main)
	await process_frame
	root.get_node("GameState").reset()

	var director = root.get_node("Director")
	var host = director.world
	host.show_scene("darkroom")

	var corpse: Node3D = host.named.get("darkroom/尸体", host.named.get("尸体"))
	check("暗房中存在尸体节点", corpse != null)

	# 1. 序章撞门前：尸体不应显示
	host.apply_room_states("C0-06")
	check("序章撞门前 (C0-06) 尸体不显示", corpse != null and not corpse.visible)

	# 2. 序章撞门后 (C0-13)：尸体应显示
	host.apply_room_states("C0-13")
	check("序章撞门后 (C0-13) 尸体显示", corpse != null and corpse.visible)

	# 3. 序章医生调查 (C0-14)：尸体应显示
	host.apply_room_states("C0-14")
	check("序章医生调查 (C0-14) 尸体显示", corpse != null and corpse.visible)

	# 4. 第一章醒来 (C1-01)：尸体应保留
	host.apply_room_states("C1-01")
	check("第一章醒来 (C1-01) 尸体保留显示", corpse != null and corpse.visible)

	# 5. 第一章调查暗房 (C1-05)：尸体应显示
	host.apply_room_states("C1-05")
	check("第一章调查暗房 (C1-05) 尸体显示", corpse != null and corpse.visible)

	# 6. 第二章开始 (C2-00)：尸体移走，不应显示
	host.apply_room_states("C2-00")
	check("第二章开始 (C2-00) 尸体移走不显示", corpse != null and not corpse.visible)

	# 7. 第二章早饭 (C2-01)：尸体不应显示
	host.apply_room_states("C2-01")
	check("第二章早饭 (C2-01) 尸体不显示", corpse != null and not corpse.visible)

	# 8. 第三章 (C3-01)：尸体不应显示
	host.apply_room_states("C3-01")
	check("第三章 (C3-01) 尸体不显示", corpse != null and not corpse.visible)

	# 9. 第四章 (C4-01)：尸体不应显示
	host.apply_room_states("C4-01")
	check("第四章 (C4-01) 尸体不显示", corpse != null and not corpse.visible)

	# 10. 第五章 (C5-01)：尸体不应显示
	host.apply_room_states("C5-01")
	check("第五章 (C5-01) 尸体不显示", corpse != null and not corpse.visible)

	# 11. 第六章暗房冲洗 (C6-03)：尸体不应显示
	host.apply_room_states("C6-03")
	check("第六章暗房冲洗 (C6-03) 尸体不显示", corpse != null and not corpse.visible)

	# 12. 第七章终局 (C7-01)：尸体不应显示
	host.apply_room_states("C7-01")
	check("第七章终局 (C7-01) 尸体不显示", corpse != null and not corpse.visible)

	print("\n测试完成，失败数: %d" % failures)
	quit(0 if failures == 0 else 1)
