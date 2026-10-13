extends CanvasLayer
## 调试面板（F1 开关）：跳到任意镜号、切换分支线、设置渗漏等级、重载内容表、重置存档。
## 也是演示现场的保险。

var panel: PanelContainer
var info: Label
var shot_edit: LineEdit


func _ready() -> void:
	layer = 20
	panel = PanelContainer.new()
	panel.position = Vector2(16, 60)
	var sb := StyleBoxFlat.new()
	sb.bg_color = Color(0.05, 0.05, 0.06, 0.92)
	sb.set_content_margin_all(12)
	panel.add_theme_stylebox_override("panel", sb)
	add_child(panel)
	var v := VBoxContainer.new()
	panel.add_child(v)

	var title := Label.new()
	title.text = "调试面板（F1）"
	v.add_child(title)
	info = Label.new()
	v.add_child(info)

	var h := HBoxContainer.new()
	shot_edit = LineEdit.new()
	shot_edit.placeholder_text = "镜号，如 N3-A-01"
	shot_edit.custom_minimum_size.x = 180
	shot_edit.text_submitted.connect(func(t): _jump(t))
	h.add_child(shot_edit)
	h.add_child(_btn("跳转", func(): _jump(shot_edit.text)))
	v.add_child(h)

	var nodes := HBoxContainer.new()
	var seen := {}
	for r in ContentDB.shot_order:
		var n: String = r["node"]
		if not seen.has(n) and r.get("line", "*") in ["*", "", "A"]:
			seen[n] = true
			var id: String = r["shot_id"]
			nodes.add_child(_btn(n, func(): _jump(id)))
	v.add_child(nodes)

	var lines := HBoxContainer.new()
	lines.add_child(_label("分支线"))
	for who in ContentDB.suspects():
		var w: String = who
		lines.add_child(_btn(ContentDB.line_of(w), func(): _force_line(w)))
	v.add_child(lines)

	var leak := HBoxContainer.new()
	leak.add_child(_label("渗漏"))
	for i in 5:
		var lv := i
		leak.add_child(_btn("L%d" % lv, func():
			GameState.set_leak(lv)
			Director.world.apply_leak(lv)))
	v.add_child(leak)

	var misc := HBoxContainer.new()
	misc.add_child(_btn("重载内容表", func(): ContentDB.reload()))
	misc.add_child(_btn("从头开始", func():
		GameState.reset()
		GameState.delete_save()
		Director.jump(ContentDB.shot_order[0]["shot_id"])))
	v.add_child(misc)

	panel.visible = false
	GameState.changed.connect(_refresh)
	Director.shot_started.connect(func(_r): _refresh())


func _btn(text: String, cb: Callable) -> Button:
	var b := Button.new()
	b.text = text
	b.pressed.connect(cb)
	return b


func _label(t: String) -> Label:
	var l := Label.new()
	l.text = t
	return l


func _jump(id: String) -> void:
	Director.jump(id.strip_edges().to_upper())


## 让后续分支按某条线走：把此人记为第一次指认的对象
func _force_line(who: String) -> void:
	GameState.accused = [who]
	GameState.line = ContentDB.line_of(who)
	GameState.changed.emit()


func _refresh() -> void:
	info.text = "镜号 %s ｜ 线 %s ｜ 指认 %s\n渗漏 L%d ｜ 电报纸 %d ｜ 证据 %d ｜ 连线 %s" % [
		GameState.shot, GameState.line if GameState.line != "" else "-",
		"、".join(PackedStringArray(GameState.accused)) if not GameState.accused.is_empty() else "-",
		GameState.leak_level, GameState.telegrams_left, GameState.evidence.size(),
		",".join(PackedStringArray(GameState.links_done)),
	]


func _unhandled_input(event: InputEvent) -> void:
	if event is InputEventKey and event.pressed and event.keycode == KEY_F1:
		panel.visible = not panel.visible
		if panel.visible:
			Input.mouse_mode = Input.MOUSE_MODE_VISIBLE
