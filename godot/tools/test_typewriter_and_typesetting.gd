extends SceneTree

const CLOSE_PUNCT := "。！？；，、：”’）》］｝』〕〉…,.!?;:)]}\"'"
const OPEN_PUNCT := "“‘（《［｛『〔〈([{"

func _initialize() -> void:
	call_deferred("run")

func run() -> void:
	print("==================================================")
	print("== 验证：字幕排版优化（避孤行/孤字）与打字机流式输出 ==")
	print("==================================================")
	
	root.get_node("GameState").persist = false
	var main = load("res://main.tscn").instantiate()
	root.add_child(main)
	await process_frame
	
	var director = root.get_node("Director")
	var ui = director.ui
	var db = root.get_node("ContentDB")
	var font = ui.font
	
	var failures := 0
	
	# 1. 遍历游戏所有文本在多种宽度下的排版检查
	print("\n[测试 1] 游戏全量文本排版查验（lines, shots, hotspots）...")
	var widths = [
		{"name": "对话气泡 (480px)", "w": 468.0, "size": 24},
		{"name": "默认下黑边 (960px)", "w": 948.0, "size": 24},
		{"name": "1280x720 (76%)", "w": 1280.0 * 0.76 - 12.0, "size": 24},
		{"name": "1600x900 (76%)", "w": 1600.0 * 0.76 - 12.0, "size": 24}
	]
	
	var texts: Array[Dictionary] = []
	for set_id in db.lines:
		for row in db.lines[set_id]:
			var t = str(row.get("text", "")).strip_edges()
			if t != "":
				texts.append({"source": "lines:" + set_id, "text": t})
	for row in db.shots.values():
		var t = str(row.get("subtitle", "")).strip_edges()
		if t != "":
			texts.append({"source": "shots:" + str(row.get("id", "")), "text": t})
	for row in db.hotspots.values():
		var t = str(row.get("desc", "")).strip_edges()
		if t != "":
			texts.append({"source": "hotspots:" + str(row.get("id", "")), "text": t})
			
	var orphan_pages := 0
	var orphan_lines := 0
	var kinsoku_errors := 0
	
	for item in texts:
		var t: String = item.text
		for cfg in widths:
			var max_w: float = cfg.w
			var fsize: int = cfg.size
			var pages: Array[String] = ui.subtitle_pages(t, max_w, fsize)
			
			for p_idx in pages.size():
				var page := pages[p_idx]
				var lines := page.split("\n")
				
				# 检查孤字孤页（整页少于或等于3个字符）
				var clean_page := page.replace("\n", "").strip_edges()
				if clean_page.length() <= 3 and pages.size() > 1:
					print("  [ERROR 孤页] %s (%d 字) [%s]: '%s'" % [item.source, clean_page.length(), cfg.name, clean_page])
					orphan_pages += 1
					
				# 检查行尾孤字（第二行少于4个字符）
				if lines.size() > 1:
					var l2 := lines[-1].strip_edges()
					if l2.length() <= 3:
						print("  [ERROR 孤行] %s (%d 字) [%s]: 行2='%s' (全文: '%s')" % [item.source, l2.length(), cfg.name, l2, page.replace("\n", " ")])
						orphan_lines += 1
						
				# 检查避头尾（禁则处理）
				for line in lines:
					var l_clean := line.strip_edges()
					if l_clean.length() > 0:
						var first_ch := l_clean.substr(0, 1)
						if first_ch in "。！？；，、：”’）》］｝』〕〉…":
							print("  [ERROR 行首避头] %s [%s]: '%s'" % [item.source, cfg.name, l_clean])
							kinsoku_errors += 1
						var last_ch := l_clean.substr(l_clean.length() - 1, 1)
						if last_ch in "“‘（《［｛『〔〈":
							print("  [ERROR 行尾避尾] %s [%s]: '%s'" % [item.source, cfg.name, l_clean])
							kinsoku_errors += 1

	print("全量排版查验完成：待测文本 %d 条" % texts.size())
	print("  孤页数: %d" % orphan_pages)
	print("  孤行数: %d" % orphan_lines)
	print("  避头尾违规: %d" % kinsoku_errors)
	if orphan_pages > 0 or orphan_lines > 0 or kinsoku_errors > 0:
		failures += 1
		print("FAIL 排版查验未通过")
	else:
		print("PASS 全量文本排版查验完美通过（0 孤页、0 孤行、0 避头尾违规）")

	# 2. 打字机流式输出与 UI 光标、按键跳过验证
	print("\n[测试 2] 打字机流式输出与 UI 交互查验...")
	root.get_node("Settings").text_instant = false
	var dialogue_task = (func():
		await ui.show_text("那一夜，便携打字机的金属击锤在客房里咬碎了死寂。我们在黑暗中等待着最后的显影。")
	)
	var timer := create_timer(0.0)
	timer.timeout.connect(dialogue_task)
	
	# 等待 0.25 秒，正在打字流式吐字中
	await create_timer(0.25).timeout
	var mid_active: bool = ui._typing_active
	var mid_chars: int = ui._reading_label.visible_characters
	var mid_caret_visible: bool = ui.text_caret.visible
	var mid_caret_pos: Vector2 = ui.text_caret.position
	print("  吐字中状态：_typing_active=%s, visible_characters=%d, caret_visible=%s, caret_pos=%s" % [
		mid_active, mid_chars, mid_caret_visible, mid_caret_pos
	])
	
	if mid_active and mid_chars > 0 and mid_caret_visible and mid_caret_pos.x > 0:
		print("PASS 打字机流式进行中：字数步进推进，击锤光标实时跟进")
	else:
		print("FAIL 打字机流式状态异常")
		failures += 1
		
	# 按空格跳过流式打字
	var ev := InputEventKey.new()
	ev.keycode = KEY_SPACE
	ev.pressed = true
	root.push_input(ev, true)
	ev = ev.duplicate()
	ev.pressed = false
	root.push_input(ev, true)
	await process_frame
	
	var skip_active: bool = ui._typing_active
	var skip_chars: int = ui._reading_label.visible_characters
	var skip_caret_visible: bool = ui.text_caret.visible
	print("  按键跳过后状态：_typing_active=%s, visible_characters=%d, caret_visible=%s" % [
		skip_active, skip_chars, skip_caret_visible
	])
	
	if not skip_active and skip_chars == -1 and not skip_caret_visible:
		print("PASS 跳过机制生效：立即显现整页文本，光标自然收起，等待翻页")
	else:
		print("FAIL 跳过机制未生效")
		failures += 1
		
	# 再次按空格翻页
	root.push_input(ev, true)
	await process_frame
	ui.cancel()
	await process_frame
	
	# 3. 档案字幕播放器（FootagePlayer）打字机流式验证
	print("\n[测试 3] 档案播放器（FootagePlayer）打字机流式查验...")
	ui.footage.set_live("档案卡", "DEMO", "001/001", "1926/10/16 21:00")
	var foot_timer := create_timer(0.0)
	foot_timer.timeout.connect(func(): await ui.footage.subtitle("这是一段档案影像的专属打字机流式字幕。"))
	await create_timer(0.15).timeout
	var foot_active: bool = ui.footage._stream_active
	var foot_chars: int = ui.footage._subtitle_text.visible_characters
	print("  档案字幕流式状态：_stream_active=%s, visible_characters=%d" % [foot_active, foot_chars])
	if foot_active and foot_chars > 0:
		print("PASS 档案字幕打字机流式生效")
	else:
		print("FAIL 档案字幕打字机流式未生效")
		failures += 1
		
	# 跳过并结束
	root.push_input(ev, true)
	await process_frame
	root.push_input(ev, true)
	await process_frame
	ui.footage.cancel()
	await process_frame
	
	print("\n==================================================")
	print("== 测试总结：全部用例执行完成，总失败数: %d ==" % failures)
	print("==================================================")
	main.queue_free()
	await process_frame
	quit(0 if failures == 0 else 1)
