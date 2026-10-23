extends CanvasLayer
## 作弊/调试控制台（按 “~” 键随时随地触发）
## 主要是为了帮助团队更方便地测试、跳转关卡、修改状态。

const CHAPTER_MAP := {
	"0": "C0-01",
	"c0": "C0-01",
	"序章": "C0-01",
	"1": "C1-01",
	"c1": "C1-01",
	"第一章": "C1-01",
	"2": "C2-00",
	"c2": "C2-00",
	"第二章": "C2-00",
	"3": "C3-01",
	"c3": "C3-01",
	"第三章": "C3-01",
	"4": "C4-01",
	"c4": "C4-01",
	"第四章": "C4-01",
	"5": "C5-01",
	"c5": "C5-01",
	"第五章": "C5-01",
	"6": "C6-01",
	"c6": "C6-01",
	"第六章": "C6-01",
	"7": "C7-01",
	"c7": "C7-01",
	"第七章": "C7-01",
	"8": "EP-01",
	"ep": "EP-01",
	"尾声": "EP-01",
}

var _is_open := false
var _prev_mouse_mode := Input.MOUSE_MODE_VISIBLE
var _prev_player_frozen := false

## 供外部 UI 系统快速查询作弊控制台是否正打开（用于全局覆盖交互拦截）
static func is_console_open() -> bool:
	var tree := Engine.get_main_loop() as SceneTree
	if tree and tree.root and tree.root.has_node("CheatConsole"):
		var node = tree.root.get_node("CheatConsole")
		if node and node.has_method("is_open"):
			return node.is_open()
	return false

func is_open() -> bool:
	return _is_open

var _panel: PanelContainer
var _log_view: RichTextLabel
var _line_edit: LineEdit
var _status_lbl: Label

var _history: Array[String] = []
var _history_idx := -1

var _director: Node:
	get:
		return get_node_or_null("/root/Director")

var _game_state: Node:
	get:
		return get_node_or_null("/root/GameState")

var _content_db: Node:
	get:
		return get_node_or_null("/root/ContentDB")


func _ready() -> void:
	layer = 128
	process_mode = Node.PROCESS_MODE_ALWAYS
	_build_ui()
	visible = false
	log_info("控制台已就绪。按 [color=#e8dcc0]~[/color] 键随时开关，输入 [color=#e8dcc0]help[/color] 查看指令。")


func _build_ui() -> void:
	_panel = PanelContainer.new()
	_panel.anchor_left = 0.0
	_panel.anchor_top = 0.0
	_panel.anchor_right = 1.0
	_panel.anchor_bottom = 0.0
	_panel.offset_bottom = 320.0

	var sb := StyleBoxFlat.new()
	sb.bg_color = Color(0.06, 0.06, 0.08, 0.94)
	sb.border_width_bottom = 2
	sb.border_color = Color(0.65, 0.55, 0.38, 0.7) # 暗金色边缘
	sb.set_content_margin_all(10)
	_panel.add_theme_stylebox_override("panel", sb)
	add_child(_panel)

	var root_vbox := VBoxContainer.new()
	root_vbox.add_theme_constant_override("separation", 6)
	_panel.add_child(root_vbox)

	# 顶部标题栏
	var header := HBoxContainer.new()
	root_vbox.add_child(header)

	var title := Label.new()
	title.text = "【调试控制台】 按 ~ 开关 | 输入 help 查看指令"
	title.add_theme_color_override("font_color", Color(0.85, 0.78, 0.65))
	title.add_theme_font_size_override("font_size", 14)
	header.add_child(title)

	var spacer := Control.new()
	spacer.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	header.add_child(spacer)

	_status_lbl = Label.new()
	_status_lbl.add_theme_color_override("font_color", Color(0.7, 0.7, 0.7))
	_status_lbl.add_theme_font_size_override("font_size", 13)
	header.add_child(_status_lbl)

	# 日志区
	_log_view = RichTextLabel.new()
	_log_view.bbcode_enabled = true
	_log_view.scroll_following = true
	_log_view.size_flags_vertical = Control.SIZE_EXPAND_FILL
	_log_view.selection_enabled = true
	_log_view.add_theme_font_size_override("normal_font_size", 14)
	root_vbox.add_child(_log_view)

	# 底部输入栏
	var input_hbox := HBoxContainer.new()
	input_hbox.add_theme_constant_override("separation", 6)
	root_vbox.add_child(input_hbox)

	var prompt := Label.new()
	prompt.text = ">"
	prompt.add_theme_color_override("font_color", Color(0.9, 0.7, 0.2))
	prompt.add_theme_font_size_override("font_size", 16)
	input_hbox.add_child(prompt)

	_line_edit = LineEdit.new()
	_line_edit.placeholder_text = "在此输入作弊/测试指令，如 goto 0, goto 1, speed 2, help..."
	_line_edit.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	_line_edit.text_submitted.connect(_on_command_submitted)
	_line_edit.gui_input.connect(_on_line_edit_gui_input)
	input_hbox.add_child(_line_edit)


func _input(event: InputEvent) -> void:
	if event is InputEventKey and event.pressed and not event.echo:
		if _is_toggle_key(event):
			toggle_console()
			get_viewport().set_input_as_handled()
			return
		if _is_open and event.keycode == KEY_ESCAPE:
			toggle_console(false)
			get_viewport().set_input_as_handled()
			return


func _is_toggle_key(event: InputEventKey) -> bool:
	if event.keycode == KEY_QUOTELEFT or event.keycode == KEY_ASCIITILDE or event.keycode == KEY_SECTION:
		return true
	if event.physical_keycode == KEY_QUOTELEFT or event.physical_keycode == KEY_SECTION:
		return true
	if event.unicode == 96 or event.unicode == 126: # ` or ~
		return true
	return false


func toggle_console(force_state = null) -> void:
	if force_state != null:
		_is_open = force_state
	else:
		_is_open = not _is_open

	visible = _is_open
	if _is_open:
		_prev_mouse_mode = Input.mouse_mode
		Input.mouse_mode = Input.MOUSE_MODE_VISIBLE
		if _director and _director.world and _director.world.player:
			_prev_player_frozen = _director.world.player.frozen
			_director.world.player.frozen = true
		_refresh_status()
		_line_edit.grab_focus()
		call_deferred("_clean_input_line")
	else:
		if _director and _director.world and _director.world.player:
			if not _prev_player_frozen and not _is_menu_or_inspector_open():
				_director.world.player.frozen = false
		if _prev_mouse_mode == Input.MOUSE_MODE_CAPTURED and not _is_menu_or_inspector_open():
			Input.mouse_mode = Input.MOUSE_MODE_CAPTURED
		_line_edit.release_focus()


func _clean_input_line() -> void:
	_line_edit.text = ""
	_line_edit.caret_column = 0


func _is_menu_or_inspector_open() -> bool:
	if _director and _director.ui:
		if _director.ui.menus and _director.ui.menus.is_open():
			return true
		if _director.ui.inspector and _director.ui.inspector.active:
			return true
		if _director.ui.board and _director.ui.board.visible:
			return true
	return false


func _refresh_status() -> void:
	var shot: String = _game_state.shot if _game_state and _game_state.shot != "" else "未开始"
	var leak: int = _game_state.leak_level if _game_state else 0
	var ev_count: int = _game_state.evidence.size() if _game_state else 0
	var is_run: bool = _director.running if _director else false
	_status_lbl.text = "镜头: %s | 渗漏: L%d | 证据: %d | 运行中: %s" % [
		shot, leak, ev_count, "是" if is_run else "否"
	]


func _on_line_edit_gui_input(event: InputEvent) -> void:
	if event is InputEventKey and event.pressed:
		if event.keycode == KEY_UP:
			_nav_history(-1)
			get_viewport().set_input_as_handled()
		elif event.keycode == KEY_DOWN:
			_nav_history(1)
			get_viewport().set_input_as_handled()


func _nav_history(delta: int) -> void:
	if _history.is_empty():
		return
	_history_idx = clamp(_history_idx + delta, 0, _history.size() - 1)
	_line_edit.text = _history[_history_idx]
	_line_edit.caret_column = _line_edit.text.length()


func _on_command_submitted(raw_text: String) -> void:
	var text := raw_text.strip_edges()
	_line_edit.text = ""
	if text == "":
		return

	if _history.is_empty() or _history.back() != text:
		_history.append(text)
	_history_idx = _history.size()

	log_cmd(text)
	_execute_command(text)


func _execute_command(text: String) -> void:
	var parts := text.split(" ", false)
	if parts.is_empty():
		return

	var cmd := parts[0].to_lower()
	var args := parts.slice(1)

	match cmd:
		"goto", "jump", "ch", "chapter":
			_cmd_goto(args)
		"help", "?":
			_cmd_help()
		"speed":
			_cmd_speed(args)
		"leak":
			_cmd_leak(args)
		"giveall", "grantall", "grant_all":
			_cmd_grant_all()
		"credits", "ending", "片尾", "制作名单":
			_cmd_credits()
		"status":
			_cmd_status()
		"reload":
			_cmd_reload()
		"restart":
			_cmd_restart()
		"clear", "cls":
			_log_view.clear()
		"quit", "exit":
			get_tree().quit()
		_:
			log_err("未知指令: '%s'。输入 [color=#e8dcc0]help[/color] 查看支持的指令列表。" % cmd)


# ───────────── 作弊指令实现 ─────────────

func _cmd_goto(args: Array) -> void:
	if args.is_empty():
		log_warn("用法: goto <章节号 或 镜号>")
		log_info("  goto 0  -> 跳到序章开头 (C0-01)")
		log_info("  goto 1  -> 跳到第一章开头 (C1-01)")
		log_info("  goto 2  -> 跳到第二章开头 (C2-00)")
		log_info("  goto 3~7-> 跳到对应章节 (C3~C7)")
		log_info("  goto ep -> 跳到尾声 (EP-01)")
		log_info("  goto <ID> -> 跳到具体镜头，例如 goto C1-05")
		return

	var target_shot := _resolve_shot(args[0])
	if target_shot == "":
		log_err("未找到匹配的章节或镜头: '%s'" % args[0])
		return

	log_ok("正在跳转至目标镜头: [b]%s[/b]..." % target_shot)

	# 1. 恢复可能存在的场景暂停
	if get_tree().paused:
		get_tree().paused = false

	# 2. 如果跳序章，重置进度提供纯净体验（除非指定 keep）
	var is_ch0: bool = (args[0] in ["0", "c0", "序章"])
	var keep_state: bool = (args.size() > 1 and args[1].to_lower() == "keep")
	if is_ch0 and not keep_state and _game_state:
		_game_state.reset()
		_game_state.delete_save()
		log_info("已重置游戏状态 (纯净序章体验)。若要保留状态请使用: goto 0 keep")

	# 3. 关闭控制台
	toggle_console(false)

	# 4. 打断正在进行的前台交互
	if _director and _director.ui:
		_director.ui.cancel()
	if _director and _director.world:
		_director.world.cancel_level()

	# 5. 执行导演跳转
	if _director:
		if not _director.running:
			_director.start(target_shot)
		else:
			_director.jump(target_shot)


func _resolve_shot(key: String) -> String:
	var clean := key.strip_edges().to_lower()
	if CHAPTER_MAP.has(clean):
		return CHAPTER_MAP[clean]

	if not _content_db:
		return ""

	var upper := clean.to_upper()
	if _content_db.shots.has(upper):
		return upper

	# 尝试遍历镜头表中的 node 匹配
	for r in _content_db.shot_order:
		if r["node"].to_upper() == upper or r["node"].to_lower() == clean:
			return r["shot_id"]

	return ""


func _cmd_speed(args: Array) -> void:
	if args.is_empty():
		log_info("当前游戏运行速度: %.1fx" % Engine.time_scale)
		log_info("用法: speed <倍率>，例如 speed 2.0 (双倍速), speed 1.0 (原速)")
		return
	var val := float(args[0])
	if val <= 0.0 or val > 10.0:
		log_err("速度倍率请设置在 0.1 ~ 10.0 之间")
		return
	Engine.time_scale = val
	log_ok("游戏运行速度已调整为: %.1fx" % val)


func _cmd_leak(args: Array) -> void:
	if args.is_empty():
		var cur_leak: int = _game_state.leak_level if _game_state else 0
		log_info("当前渗漏等级: L%d (范围 0~4)" % cur_leak)
		log_info("用法: leak <0~4>")
		return
	var lv := int(args[0])
	if lv < 0 or lv > 4:
		log_err("渗漏等级只能在 0 到 4 之间")
		return
	if _game_state:
		_game_state.set_leak(lv)
	if _director and _director.world:
		_director.world.apply_leak(lv)
	log_ok("渗漏等级已设置为: L%d" % lv)


func _cmd_grant_all() -> void:
	if not _game_state or not _content_db:
		log_err("系统尚未完全就绪")
		return
	var count := 0
	for id in _content_db.evidence:
		if not _game_state.evidence.has(id):
			_game_state.add_evidence(id)
			count += 1
	log_ok("已补齐全部证据！新增 %d 件，当前共持有 %d 件证据。" % [count, _game_state.evidence.size()])


func _cmd_status() -> void:
	if not _game_state:
		log_err("GameState 尚未初始化")
		return
	_refresh_status()
	log_info("──────── 游戏状态 ────────")
	log_info("当前镜号: %s" % (_game_state.shot if _game_state.shot != "" else "（未开始）"))
	log_info("现实渗漏: L%d" % _game_state.leak_level)
	log_info("持有证据: %d 件 (%s)" % [_game_state.evidence.size(), ", ".join(PackedStringArray(_game_state.evidence))])
	log_info("已成推论: %s" % (", ".join(PackedStringArray(_game_state.links_done)) if not _game_state.links_done.is_empty() else "无"))
	log_info("当前讲法/终局: %s" % (_game_state.ending if _game_state.ending != "" else "未决"))
	log_info("时间倍率: %.1fx" % Engine.time_scale)
	log_info("─────────────────────────")


func _cmd_credits() -> void:
	log_ok("正在启动庄园实景电影级制作名单与致谢巡礼...")
	toggle_console(false)
	if _director and _director.ui:
		_director.ui.cancel()
	var credits_cls := preload("res://world/credits_sequence.gd")
	var seq = credits_cls.new()
	get_tree().root.add_child(seq)
	seq.start_sequence()


func _cmd_reload() -> void:
	if _content_db:
		_content_db.reload()
	if _director and _director.ui and _director.ui.fx:
		_director.ui.fx.reload()
	if _director and _director.ui and _director.ui.footage:
		_director.ui.footage.reload()
	log_ok("内容表已完成热重载！包含 shots.csv, evidence.csv, links.csv 等。")


func _cmd_restart() -> void:
	log_ok("正在从头重置游戏...")
	if _game_state:
		_game_state.reset()
		_game_state.delete_save()
	toggle_console(false)
	if _director and _director.ui:
		_director.ui.cancel()
	if _director and _director.world:
		_director.world.cancel_level()
	if _content_db and _content_db.shot_order.size() > 0 and _director:
		_director.jump(_content_db.shot_order[0]["shot_id"])


func _cmd_help() -> void:
	log_info("[color=#ffd700]==== 可用指令列表 ====[/color]")
	log_info("[color=#a6e22e]goto <0~7|ep|镜号>[/color] : 章节或镜号瞬间传送 (如 goto 0, goto 1, goto C1-05)")
	log_info("[color=#a6e22e]speed <倍率>[/color]       : 调整演播与游戏速度 (如 speed 2.0 加速, speed 1.0 恢复)")
	log_info("[color=#a6e22e]leak <0~4>[/color]        : 设置现实渗漏等级 (L0~L4)")
	log_info("[color=#a6e22e]giveall[/color]           : 一键获得全部证据（便于测试客房连线）")
	log_info("[color=#a6e22e]reload[/color]            : 热重载表格数据 (无需重启游戏)")
	log_info("[color=#a6e22e]status[/color]            : 查看当前镜头、证据、推论进度")
	log_info("[color=#a6e22e]restart[/color]           : 彻底从头重置游戏")
	log_info("[color=#a6e22e]clear[/color]             : 清屏")
	log_info("[color=#a6e22e]quit[/color]              : 退出游戏")


# ───────────── 日志输出辅助 ─────────────

func log_cmd(text: String) -> void:
	_log_view.append_text("[color=#888888]> %s[/color]\n" % text)


func log_ok(text: String) -> void:
	_log_view.append_text("[color=#a6e22e]%s[/color]\n" % text)


func log_info(text: String) -> void:
	_log_view.append_text("[color=#f8f8f2]%s[/color]\n" % text)


func log_warn(text: String) -> void:
	_log_view.append_text("[color=#e6db74]%s[/color]\n" % text)


func log_err(text: String) -> void:
	_log_view.append_text("[color=#f92672]%s[/color]\n" % text)
