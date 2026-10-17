extends Node
## 分镜播放器：按 shots.csv 一行一行地播放。
## 每个镜头：切场景与机位 → 显示文字 → 依次执行 actions → 决定下一个镜头。
## 动作白名单见 core/actions.gd；表格只能调用这些动作（docs/06-技术方案.md 2.2）。

signal shot_started(row: Dictionary)
signal inspected(id: String)
signal finished

const Actions := preload("res://core/actions.gd")
const CANCEL := "__cancel__"
## 在镜头文字出现之前执行的动作
const STAGING := ["reveal", "conceal", "music"]

var ui: Node
var world: Node
## 命令行带 -- --autoplay 时自动选第一个选项、跳过等待，用于无界面回归测试
var autoplay := false
## 截图时用 --skip-text：文字不等点击，直接进入后面的动作
var skip_text := false
var running := false
var _jump_to := ""
var _played := 0
var _train_present := false
var _before_train_fx := ""


func _ready() -> void:
	autoplay = OS.get_cmdline_user_args().has("--autoplay")
	skip_text = OS.get_cmdline_user_args().has("--skip-text")


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
	var scene_id: String = row.get("scene", "")
	if scene_id == "train" and not _train_present:
		_before_train_fx = ui.fx.get_override()
		_train_present = true
	elif scene_id != "" and scene_id != "train" and _train_present:
		ui.fx.set_override(_before_train_fx)
		_train_present = false
	var mode: String = row.get("mode", "")
	if mode == "":
		mode = "camera"
	if row.get("scene", "") != "":
		world.show_scene(row["scene"])
	world.apply_room_states(row.get("shot_id", ""))
	world.set_mode(mode, row.get("camera", ""))
	ui.set_cinematic(mode == "camera")
	for s in str(row.get("sound", "")).split(";", false):
		world.play_sound(s.strip_edges())
	var acts := Actions.parse(row.get("actions", ""))
	# 火车的当下画面：在文字出现前退出片头录像样式；其他关卡保持原顺序。
	var staging: Array = STAGING.duplicate()
	if row.get("scene", "") == "train":
		staging.append_array(["fx", "osd", "leak"])
	# 布景动作（显示 / 隐藏场景里的东西）先于文字执行：玩家读文字时，画面已经摆好
	for a in acts:
		if a["name"] in staging:
			await _do(a["name"], a["args"], mode)
	if row.get("text", "") != "" and not skip_text:
		await ui.show_text(fill(row["text"]))
		if _interrupted():
			return
	for a in acts:
		if a["name"] in staging:
			continue
		await _do(a["name"], a["args"], mode)
		if _interrupted():
			return
	if row.get("text", "") == "" and acts.is_empty():
		await _wait(1.5)


## next 列：空 = 表格中的下一行；"N2-A-01" = 指定；
## "view=保护>C7-02|>C7-03" = 按条件，最后一个可以是无条件的默认值
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
		"link":
			await _link(args[0])
		"say":
			await _say(args[0])
		"telling":
			await _telling(args[0])
		"develop":
			# 第 6 章：玩家亲手冲洗底片（docs/02 第 9 节）
			await ui.develop(args[0] if args.size() > 0 else "")
			GameState.record("develop", args[0] if args.size() > 0 else "")
		"goto":
			world.show_scene(args[0])
		"fx":
			ui.fx.set_override(args[0] if args.size() > 0 else "")
		"music":
			# music(曲名[,淡入秒])；music(关闭[,淡出秒])，淡出秒填 0 = 直接切断
			var fade := float(args[1]) if args.size() > 1 and args[1].is_valid_float() else 1.5
			world.play_music(args[0] if args.size() > 0 else "关闭", fade)
		"anim":
			# anim(人物, 动作)：idle / walk / talk / tap / sit
			if args.size() >= 2:
				world.figure_anim(args[0], args[1])
		"reveal":
			for id in args:
				world.set_shown(id, true)
		"conceal":
			for id in args:
				world.set_shown(id, false)
		"footage":
			await ui.footage.play_clip(args[0])
		"recap":
			await _recap(args[0] if args.size() > 0 else "")
		"osd":
			# osd(样式,文件名,编号,时间)；osd() 关闭
			ui.footage.set_live(args[0] if args.size() > 0 else "", args[1] if args.size() > 1 else "", args[2] if args.size() > 2 else "", args[3] if args.size() > 3 else "")
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
	if h.get("footage", "") != "":
		await ui.footage.play_clip(h["footage"])
	if h.get("text", "") != "":
		await ui.show_text(fill(h["text"]))
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
		_checklist(ids, pending)
		while not pending.is_empty():
			var id: String = await inspected
			if id == CANCEL:
				world.highlight_hotspots([])
				ui.set_checklist([])
				return
			await _show_hotspot(id)
			pending.erase(id)
			ui.set_progress(ids.size() - pending.size(), ids.size())
			_checklist(ids, pending)
		world.highlight_hotspots([])
		ui.set_progress(0, 0)
		ui.set_checklist([])
		return
	while not pending.is_empty():
		var labels: Array = pending.map(func(i): return ContentDB.hotspots.get(i, {}).get("label", i))
		var k: int = await ui.choose("仔细看看", labels)
		if k < 0:
			return
		var id: String = pending[k]
		await _show_hotspot(id)
		pending.erase(id)


## 观察清单：可检查物件表的 hint 列（带方向的问题）；没写 hint 的用物件名
func _checklist(ids: Array, pending: Array) -> void:
	var items: Array = []
	for id in ids:
		var h: Dictionary = ContentDB.hotspots.get(id, {})
		var t: String = h.get("hint", "")
		items.append({"text": fill(t if t != "" else h.get("label", id)), "done": not pending.has(id)})
	ui.set_checklist(items)


## 镜头文字里的占位符：{容器号} = 本局的容器编号（01—12）；{本轮陈述} = 玩家在终局选定的那句话
func fill(text: String) -> String:
	var said: String = GameState.statement if GameState.statement != "" else "……"
	return text.replace("{容器号}", GameState.container).replace("{本轮陈述}", said)


## 一章结束：黑场，字幕逐行打出当天的复盘（台词表的一组；说话人写“标题”的一行是黑场顶上的日期）。
## 可用占位符：{今日线索}（这一章收进证据板的线索）、{今日推论}（这一章得出的推论）、{今日记录}（这一章打字机上写下的那句）。
## 占位符这一章没有内容时，整行不出现。
func _recap(set_id: String) -> void:
	var chapter := GameState.shot.get_slice("-", 0)
	var clues: Array = []
	var infs: Array = []
	for id in GameState.evidence:
		if String(GameState.found_at.get(id, "")).get_slice("-", 0) != chapter:
			continue
		var nm: String = ContentDB.evidence.get(id, {}).get("name", id)
		if id.begins_with("ev_inf_"):
			infs.append(nm.trim_prefix("推论："))
		else:
			clues.append(nm)
	var note := ""
	for e in GameState.journal:
		if e.get("kind", "") == "annotate" and String(e.get("shot", "")).get_slice("-", 0) == chapter:
			note = e["text"]
	var fills := {"{今日线索}": "、".join(PackedStringArray(clues)), "{今日推论}": "；".join(PackedStringArray(infs)), "{今日记录}": note}
	var out: Array = []
	var v := GameState.vars()
	for r in ContentDB.lines.get(set_id, []):
		if not ContentDB.condition_matches(r.get("condition", ""), v):
			continue
		var t: String = fill(r["text"])
		var empty := false
		for k in fills:
			if t.contains(k):
				empty = empty or fills[k] == ""
				t = t.replace(k, fills[k])
		if not empty:
			out.append({"text": t, "title": r.get("speaker", "") == "标题"})
	if out.is_empty():
		push_warning("复盘组为空：" + set_id)
		return
	await ui.interlude(out)


## 弹出一组预设（annotations.csv），记录选择与人格属性，显示回应；返回所选文本
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


func _link(group: String) -> void:
	var pairs: Array = ContentDB.links.get(group, [])
	if pairs.is_empty():
		push_warning("连线组不存在：" + group)
		return
	# links.csv 的 note 列写了镜号的行，是这个镜头固定要演示的画面（如 N6 汇聚），与玩家连的是哪一对无关
	var here: Array = pairs.filter(func(p): return p.get("note", "") == GameState.shot)
	var shot_demo: Dictionary = here[0] if not here.is_empty() else {}
	if GameState.links_done.has(group):
		# 之前已经连对：自动演示一遍，并给出这个镜头对应的推论
		var demo: Dictionary = shot_demo if not shot_demo.is_empty() else pairs[0]
		await ui.show_text(demo.get("response", ""))
		_collect(demo.get("result", ""))
		return
	var usable := pairs.filter(func(p): return GameState.evidence.has(p["a"]) and GameState.evidence.has(p["b"]))
	var matched: Dictionary = {}
	if usable.is_empty() or autoplay:
		if usable.is_empty():
			push_warning("连线组 %s 所需证据尚未收集（可能是调试跳转），自动完成" % group)
		matched = usable[0] if not usable.is_empty() else pairs[0]
	else:
		var title: String = GameState.objective if GameState.objective != "" else "证据板"
		var fails := 0
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
			if matched.is_empty():
				fails += 1
				await _link_hint(group, pick, usable, fails)
	GameState.links_done.append(group)
	GameState.link_pairs.append([matched["a"], matched["b"]])
	GameState.record("link", group)
	await ui.show_text(matched.get("response", ""))
	_collect(matched.get("result", ""))
	if not shot_demo.is_empty() and shot_demo != matched:
		await ui.show_text(shot_demo.get("response", ""))
		_collect(shot_demo.get("result", ""))
	ui.board_close()


## 连不通时，侦探的自言自语，一次比一次具体（docs/13 第 6 节）：
## 第 1 次：针对玩家拿起的那条线索（证据表 hint 列）；
## 第 2 次：针对这组推理（连线规则表 hint 列）；
## 第 3 次起：证据板上该连的两张卡片亮起来。
func _link_hint(group: String, pick: Array, usable: Array, fails: int) -> void:
	var relevant := func(id: String) -> bool:
		return usable.any(func(p): return p["a"] == id or p["b"] == id)
	var line := ""
	if fails == 1:
		for id in pick:
			if relevant.call(id) and ContentDB.evidence.get(id, {}).get("hint", "") != "":
				line = ContentDB.evidence[id]["hint"]
				break
		if line == "":
			line = "这两样东西之间，看不出关系。"
	elif fails == 2:
		line = ContentDB.links.get(group, [{}])[0].get("hint", "")
		if line == "":
			line = "也许该换一条线索试试。"
	else:
		var p: Dictionary = usable[0]
		ui.board.highlight([p["a"], p["b"]])
		line = "也许该把“%s”和“%s”放在一起看。" % [ContentDB.evidence.get(p["a"], {}).get("name", p["a"]), ContentDB.evidence.get(p["b"], {}).get("name", p["b"])]
	await ui.show_text("（自言自语）" + line)


func _say(set_id: String) -> void:
	var v := GameState.vars()
	for r in ContentDB.lines.get(set_id, []):
		if ContentDB.condition_matches(r.get("condition", ""), v):
			var sp: String = r.get("speaker", "")
			var talking: bool = sp != "" and world.has_method("figure_anim") and world.figure_anim(sp, "talk")
			await ui.show_text(("%s：%s" % [sp, r["text"]]) if sp != "" else r["text"])
			if talking:
				world.figure_anim(sp, "idle")
			if _interrupted():
				return


## 终局的两种讲法（docs/02 第 9.3 节）：玩家一路写下的记录决定哪一种先出现在纸上，
## 但由玩家自己选。选定的那句话写进尾声的记录卡（{本轮陈述}）。
func _telling(set_id: String) -> void:
	var rows: Array = ContentDB.annotations.get(set_id, [])
	if rows.is_empty():
		push_warning("预设组不存在：" + set_id)
		return
	var lean := GameState.dominant()
	rows = rows.duplicate()
	rows.sort_custom(func(a, b): return a.get("tendency", "") == lean and b.get("tendency", "") != lean)
	var k := 0
	if not autoplay:
		k = await ui.choose("最后一份记录", rows.map(func(r): return r["text"]))
	if k < 0:
		return
	var r: Dictionary = rows[k]
	GameState.ending = r.get("tendency", "")
	GameState.statement = r["text"]
	GameState.record("telling", r["text"], {"tendency": GameState.ending})
	if r.get("response", "") != "":
		await ui.show_text(r["response"])
