extends SceneTree
## 自动化测试：第四章温室地下室摄影机完整玩法循环
## 1. 拿起大画幅相机 (hs_cellar_camera)
## 2. 举镜切换 (F 键 / _toggle_camera_raise)
## 3. 虚影与双重视角检查
## 4. 滚轮调焦 (focus >= 0.82)
## 5. 首次曝光快门 (EXPOSED)
## 6. 水槽显影盘首次显影 (DEVELOPED)
## 7. 二次曝光拨杆上膛 (ARMED)
## 8. 二次快门收人 (EXPOSED2)
## 9. 最终显影清除幽灵 (CLEARED, cleared_years 记录)

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

	# 加载温室地下室场景
	host.show_scene("gh_cellar")
	host.set_mode("walk", "")
	await process_frame

	var cellar_node: Node3D = host.room as Node3D
	check("成功载入 gh_cellar 场景", cellar_node != null and cellar_node.name == "gh_cellar")
	if cellar_node == null:
		print("无法获取 cellar_node，终止测试")
		quit(1)
		return

	# 1. 检查初始状态
	check("初始未持有相机", cellar_node.get("has_camera") == false)
	check("初始相机未举起", cellar_node.get("camera_raised") == false)
	var guide_panel: PanelContainer = cellar_node.get("guide_pill_panel")
	var guide_lbl: Label = cellar_node.get("guide_pill_label")
	check("未持有相机时底部提示药丸隐藏", guide_panel != null and guide_panel.visible == false)

	# 1.5 验证通关前梯子无法离开
	cellar_node.call("_on_director_inspected", "hs_cellar_ladder")
	await process_frame
	check("通关前爬梯仍留在 gh_cellar", host.current_id == "gh_cellar")

	# 2. 交互拿起相机
	director.inspected.emit("hs_cellar_camera")
	await process_frame
	check("拿起相机后 has_camera 为 true", cellar_node.get("has_camera") == true)
	check("拿起相机后底部提示药丸显示", guide_panel != null and guide_panel.visible == true)
	check("底部提示包含按 F 举起相机", guide_lbl != null and guide_lbl.text.contains("按 [F] 举起"))

	# 3. 举镜切换
	cellar_node.call("_toggle_camera_raise")
	await process_frame
	check("举镜后 camera_raised 为 true", cellar_node.get("camera_raised") == true)
	check("举镜后提示药丸包含滚轮与快门", guide_lbl != null and guide_lbl.text.contains("滚轮") and guide_lbl.text.contains("快门"))
	var cam_only: Node3D = cellar_node.get("camera_only_node")
	check("相机双重视角节点可见", cam_only != null and cam_only.visible == true)
	var overlay: CanvasLayer = cellar_node.get("camera_overlay")
	check("取景器 UI 层可见", overlay != null and overlay.visible == true)

	# 4. 滚轮调焦
	cellar_node.call("_step_focus", 0.88)
	var cur_focus: float = cellar_node.get("focus")
	check("对焦值更新成功 (focus >= 0.82)", cur_focus >= 0.82)

	# 5. 对准 1920 年（有幽灵照片）进行首次曝光
	cellar_node.set("current_aim_year", 1920)
	cellar_node.call("_trigger_shutter")
	await process_frame
	check("首次曝光后 plate_state 为 EXPOSED", cellar_node.get("plate_state") == "EXPOSED")
	check("曝光年份记录为 1920", cellar_node.get("exposed_year") == 1920)

	# 6. 水槽显影盘首次显影
	cellar_node.call("_handle_tray_interaction")
	await process_frame
	check("水槽显影后 plate_state 为 DEVELOPED", cellar_node.get("plate_state") == "DEVELOPED")

	# 7. 拨动拨杆设定二次曝光 (R 键)
	cellar_node.call("_handle_arm_second_exposure")
	await process_frame
	check("拨动拨杆后 plate_state 为 ARMED", cellar_node.get("plate_state") == "ARMED")

	# 8. 二次曝光快门
	cellar_node.set("current_aim_year", 1920)
	cellar_node.call("_trigger_shutter")
	await process_frame
	check("二次曝光后 plate_state 为 EXPOSED2", cellar_node.get("plate_state") == "EXPOSED2")

	# 9. 最终显影收人
	cellar_node.call("_handle_tray_interaction")
	await process_frame
	check("最终显影后 plate_state 为 CLEARED", cellar_node.get("plate_state") == "CLEARED")
	var cleared_dict: Dictionary = cellar_node.get("cleared_years")
	check("1920 年已记录在 cleared_years 中", cleared_dict.has(1920))

	# 10. 放下相机
	cellar_node.call("_toggle_camera_raise")
	await process_frame
	check("放下相机后 camera_raised 为 false", cellar_node.get("camera_raised") == false)
	check("取景器 UI 层已隐藏", overlay != null and overlay.visible == false)
	check("相机双重视角节点已隐藏", cam_only != null and cam_only.visible == false)

	# 11. 木梯交互不抢先释放关卡；正常返回由镜头表执行，见真实输入测试。
	cellar_node.call("_on_director_inspected", "hs_cellar_ladder")
	await process_frame
	check("木梯事件不在检视完成前释放关卡", host.current_id == "gh_cellar")

	print("\n=== 相机玩法循环自动化校验结果：失败数 = %d ===" % failures)
	quit(0 if failures == 0 else 1)
