extends Node
## 分镜播放器：按 shots.csv 一行一行地播放。
## 每个镜头：切场景与机位 → 显示文字 → 依次执行 actions → 决定下一个镜头。
## 动作白名单见 core/actions.gd；表格只能调用这些动作（docs/06-技术方案.md 2.2）。

signal shot_started(row: Dictionary)
signal inspected(id: String)
signal finished

const Actions := preload("res://core/actions.gd")
const CANCEL := "__cancel__"

var ui: Node
var world: Node
## 命令行带 -- --autoplay 时自动选第一个选项、跳过等待，用于无界面回归测试
var autoplay := false
var running := false
var _jump_to := ""
var _played := 0


func _ready() -> void:
	autoplay = OS.get_cmdline_user_args().has("--autoplay")


func start(from_shot := "") -> void:
	var first: String = from_shot
	if first == "" and ContentDB.shot_order.size() > 0:
		first = ContentDB.shot_order[0]["shot_id"]
	_run(first)


## 调试面板：跳到任意镜号
func jump(shot_id: String) -> void:
	if not ContentDB.shots.has(shot_id):
		push_warning("没有这个镜号：" + shot_id)
		return
	if running:
		_jump_to = shot_id
		ui.cancel()
		inspected.emit(CANCEL)
	else:
		_run(shot_id)


func _interrupted() -> bool:
	return _jump_to != ""


func _run(first: String) -> void:
	running = true
	var cur := first
	while cur != "" and cur != "END":
		if not ContentDB.shots.has(cur):
			push_error("镜号不存在：" + cur)
			if not autoplay:
				await ui.show_text("（镜头 %s 尚未编写。按 F1 打开调试面板可以跳回其他镜头。）" % cur)
			break
		var row: Dictionary = ContentDB.shots[cur]
		GameState.shot = cur
		GameState.save()
		_played += 1
		await _play(row)
		if _interrupted():
			cur = _jump_to
			_jump_to = ""
			continue
		cur = resolve_next(row)
	running = false
	finished.emit()


func _play(row: Dictionary) -> void:
	shot_started.emit(row)
	var mode: String = row.get("mode", "")
	if mode == "":
		mode = "camera"
	if row.get("scene", "") != "":
		world.show_scene(row["scene"])
	world.set_mode(mode, row.get("camera", ""))
	ui.set_cinematic(mode == "camera")
	for s in str(row.get("sound", "")).split(";", false):
		world.play_sound(s.strip_edges())
	if row.get("text", "") != "":
		await ui.show_text(row["text"])
		if _interrupted():
			return
	var acts := Actions.parse(row.get("actions", ""))
	for a in acts:
		await _do(a["name"], a["args"], mode)
		if _interrupted():
			return
	if row.get("text", "") == "" and acts.is_empty():
		await _wait(1.5)


## next 列：空 = 表格中的下一行；"N2-A-01" = 指定；
## "line=A>N2-A-01|line=B>N2-B-01|>N9" = 按条件，最后一个可以是无条件的默认值
func resolve_next(row: Dictionary) -> String:
	var n: String = row.get("next", "").strip_edges()
	if n == "":
		return ContentDB.next_in_order(row["shot_id"])
	if not n.contains(">"):
		return n
	var v := GameState.vars()
	for opt in n.split("|", false):
		var kv := opt.split(">")
		if kv.size() == 2 and ContentDB.condition_matches(kv[0], v):
			return kv[1].strip_edges()
	push_error("%s 的 next 没有匹配的条件：%s" % [row["shot_id"], n])
	return "END"


func _wait(sec: float) -> void:
	if autoplay:
		return
	await ui.wait_seconds(sec)


# ───────────── 动作 ─────────────

func _do(name: String, args: Array, mode: String) -> void:
	match name:
		"wait":
			await _wait(float(args[0]) if args.size() > 0 else 1.0)
		"leak":
			GameState.set_leak(int(args[0]) if args.size() > 0 else 0)
			world.apply_leak(GameState.leak_level)
		"use_telegram":
			GameState.use_telegram()
			ui.toast("用掉一张电报纸（剩 %d 张）" % GameState.telegrams_left)
		"objective":
			GameState.objective = ",".join(PackedStringArray(args))
			ui.set_objective(GameState.objective)
		"collect":
			for id in args:
				_collect(id)
		"inspect":
			await _inspect(args, mode)
		"annotate":
			await _choose_from_set(args[0], "annotate", "手记")
		"inquire":
			await _choose_from_set(args[0], "inquire", "追问")
		"accuse":
			await _accuse(args[0] if args.size() > 0 else "")
		"link":
			await _link(args[0])
		"say":
			await _say(args[0])
		"ending_choice":
			var picked: String = await _choose_from_set(args[0] if args.size() > 0 else "ending", "ending", "")
			GameState.ending = picked
		"confession":
			await ui.show_text(build_confession())
		"goto":
			world.show_scene(args[0])
		"fx":
			ui.fx.set_override(args[0] if args.size() > 0 else "")
		_:
			push_warning("未知动作，已跳过：" + name)


func _collect(id: String) -> void:
	if not ContentDB.evidence.has(id):
		push_warning("证据表中没有：" + id)
		return
	if not GameState.evidence.has(id):
		GameState.add_evidence(id)
		ui.toast("收入证据板：" + ContentDB.evidence[id]["name"])


func _show_hotspot(id: String) -> void:
	var h: Dictionary = ContentDB.hotspots.get(id, {})
	if not GameState.inspected.has(id):
		GameState.inspected.append(id)
	world.set_frozen(true)
	if h.get("text", "") != "":
		await ui.show_text(h["text"])
	world.set_frozen(false)
	if h.get("evidence", "") != "":
		_collect(h["evidence"])


func _inspect(ids: Array, mode: String) -> void:
	var pending := ids.duplicate()
	if autoplay:
		for id in ids:
			await _show_hotspot(id)
		return
	if mode == "walk":
		world.highlight_hotspots(ids)
		while not pending.is_empty():
			var id: String = await inspected
			if id == CANCEL:
				return
			await _show_hotspot(id)
			pending.erase(id)
			ui.set_progress(ids.size() - pending.size(), ids.size())
		ui.set_progress(0, 0)
		return
	while not pending.is_empty():
		var labels: Array = pending.map(func(i): return ContentDB.hotspots.get(i, {}).get("label", i))
		var k: int = await ui.choose("仔细看看", labels)
		if k < 0:
			return
		var id: String = pending[k]
		await _show_hotspot(id)
		pending.erase(id)


## 弹出一组预设（annotations.csv），记录选择与倾向变量，显示回应；返回所选文本
func _choose_from_set(set_id: String, kind: String, title: String) -> String:
	var rows: Array = ContentDB.annotations.get(set_id, [])
	if rows.is_empty():
		push_warning("预设组不存在：" + set_id)
		return ""
	var k := 0
	if not autoplay:
		k = await ui.choose(title, rows.map(func(r): return r["text"]))
	if k < 0:
		return ""
	var r: Dictionary = rows[k]
	GameState.add_tendency(r.get("tendency", ""))
	GameState.record(kind, r["text"], {"set": set_id, "tendency": r.get("tendency", "")})
	if r.get("response", "") != "":
		await ui.show_text(r["response"])
	return r["text"]


func _accuse(reason_set: String) -> void:
	var names := GameState.remaining_suspects()
	var k := 0
	if not autoplay:
		k = await ui.register_pick("笔尖悬在名字上方。落笔即是指认。", names)
	elif GameState.accused.is_empty():
		for i in names.size():
			if "--line=" + ContentDB.line_of(names[i]) in OS.get_cmdline_user_args():
				k = i
	if k < 0:
		return
	var who: String = names[k]
	var reason := ""
	if reason_set != "":
		reason = await _choose_from_set(reason_set, "reason", "理由")
		if _interrupted():
			return
	GameState.accuse(who)
	GameState.record("accuse", who, {"reason": reason})
	world.on_accused(who)


func _link(group: String) -> void:
	var pairs: Array = ContentDB.links.get(group, [])
	if pairs.is_empty():
		push_warning("连线组不存在：" + group)
		return
	# links.csv 的 note 列写了镜号的行，是这个镜头固定要演示的画面（如 N6 汇聚），与玩家连的是哪一对无关
	var here: Array = pairs.filter(func(p): return p.get("note", "") == GameState.shot)
	var shot_demo: Dictionary = here[0] if not here.is_empty() else {}
	if GameState.links_done.has(group):
		# 之前已经连对：自动演示一遍
		await ui.show_text((shot_demo if not shot_demo.is_empty() else pairs[0]).get("response", ""))
		return
	var usable := pairs.filter(func(p): return GameState.evidence.has(p["a"]) and GameState.evidence.has(p["b"]))
	var matched: Dictionary = {}
	if usable.is_empty() or autoplay:
		if usable.is_empty():
			push_warning("连线组 %s 所需证据尚未收集（可能是调试跳转），自动完成" % group)
		matched = usable[0] if not usable.is_empty() else pairs[0]
	else:
		var title: String = GameState.objective if GameState.objective != "" else "证据板"
		while matched.is_empty():
			var pick: Array = await ui.board_pick_pair(title)
			if pick.is_empty():
				ui.board_close()
				return
			for p in pairs:
				if (p["a"] == pick[0] and p["b"] == pick[1]) or (p["a"] == pick[1] and p["b"] == pick[0]):
					matched = p
					break
			await ui.board_result(pick[0], pick[1], not matched.is_empty())
	GameState.links_done.append(group)
	GameState.link_pairs.append([matched["a"], matched["b"]])
	GameState.record("link", group)
	await ui.show_text(matched.get("response", ""))
	if not shot_demo.is_empty() and shot_demo != matched:
		await ui.show_text(shot_demo.get("response", ""))
	ui.board_close()


func _say(set_id: String) -> void:
	var v := GameState.vars()
	for r in ContentDB.lines.get(set_id, []):
		if ContentDB.condition_matches(r.get("condition", ""), v):
			var sp: String = r.get("speaker", "")
			await ui.show_text(("%s：%s" % [sp, r["text"]]) if sp != "" else r["text"])
			if _interrupted():
				return


## 案卷自述的兜底版本：标准自述 + 原样摘录玩家的批注（docs/05 第 4 节）
func build_confession() -> String:
	var parts: Array = [ContentDB.confession_fallback.strip_edges()]
	for e in GameState.journal:
		match e["kind"]:
			"annotate", "reason":
				parts.append("我写下：“%s”" % e["text"])
			"accuse":
				parts.append("我在名册上划去了%s。" % e["text"])
	return "\n".join(PackedStringArray(parts))
