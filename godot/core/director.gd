extends Node
## 分镜播放器：按 shots.csv 一行一行地播放。
## 每个镜头：切场景与机位 → 显示文字 → 依次执行 actions → 决定下一个镜头。
## 动作白名单见 core/actions.gd；表格只能调用这些动作（docs/06-技术方案.md 2.2）。

signal shot_started(row: Dictionary)
signal inspected(id: String)
signal finished
signal corridor_done

const Actions := preload("res://core/actions.gd")
const CANCEL := "__cancel__"
## 在镜头文字出现之前执行的动作
var _footage_handoff := false
## 客房的一站（station）、醒来（wake）也在文字之前：玩家先走过去、按 E，或先睁开眼，文字才出现；
## 目标（objective）也提前写出来，玩家走过去之前就知道去哪
const STAGING := ["reveal", "conceal", "music", "objective", "wake", "station"]
## 客房的三站：按 E 以后镜头坐到哪个机位（床由 world.lie_down 处理）
const STATION_CAM := {"hs_desk_board": "board", "hs_typewriter": "typewriter_close"}

var ui: Node
var world: Node
## 命令行带 -- --autoplay 时自动选第一个选项、跳过等待，用于无界面回归测试
var autoplay := false
## 截图时用 --skip-text：文字不等点击，直接进入后面的动作
var skip_text := false
var running := false
var _jump_to := ""
## 回到标题：停下来，不发 finished
var _stopping := false
var _played := 0
var _train_present := false
var _before_train_fx := ""
## 正在进行的自由探索（任务表的一组）；空 = 不在探索
var _explore_group := ""
## 正在进行的行走检查（inspect）里还没看的物件
var _inspect_pending: Array = []
## 这一组“回客房”已经出现过（只在第一次出现时响一声）
var _end_announced := {}


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
	ui.eyelids_set(1.0)
	if running:
		_jump_to = shot_id
		ui.cancel()
		inspected.emit(CANCEL)
	else:
		_run(shot_id)


func _interrupted() -> bool:
	return _jump_to != ""


## 回到标题页：打断正在播放的镜头，等它停下（不发 finished，不改存档）
func stop() -> void:
	if not running:
		return
	_stopping = true
	_jump_to = "END"
	ui.cancel()
	inspected.emit(CANCEL)
	for i in 120:
		if not running:
			break
		await get_tree().process_frame
	_stopping = false


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
	if _stopping:
		return
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
	var acts := Actions.parse(row.get("actions", ""))
	var names: Array = acts.map(func(a): return a["name"])
	# 眼睛只在“睡下 → 醒来”之间闭着；跳镜、读档时不该还闭着
	if not names.has("wake") and not names.has("sleep"):
		ui.eyelids_set(1.0)
	world.set_mode(mode, row.get("camera", ""))
	ui.set_cinematic(mode == "camera")
	# 客房的一站：声音（敲门、钟声）等玩家按了 E、躺下以后才响
	var late_sound: bool = names.has("station")
	if not late_sound:
		world.play_sounds(row.get("sound", ""))
	# 火车的当下画面：在文字出现前退出片头录像样式；其他关卡保持原顺序。
	var staging: Array = STAGING.duplicate()
	if row.get("scene", "") == "train":
		staging.append_array(["fx", "osd", "leak"])
	# 布景动作（显示 / 隐藏场景里的东西）先于文字执行：玩家读文字时，画面已经摆好
	for a in acts:
		if a["name"] in staging:
			await _do(a["name"], a["args"], mode)
			if _interrupted():
				return
	if late_sound:
		world.play_sounds(row.get("sound", ""))
	if row.get("text", "") != "" and not skip_text:
		# 行走镜头里读字时人站住（文字框要点击翻页，不该边读边走）
		var hold: bool = world.player != null and world.player.active
		if hold:
			world.set_frozen(true)
		await ui.show_text(fill(row["text"]))
		if hold:
			world.set_frozen(false)
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
			# footage(片段,接日记)：放完先不撤影像层，等紧接着的日记黑场盖住后再撤，免得露出底下的场景
			var handoff: bool = args.size() > 1 and args[1] == "接日记"
			await ui.footage.play_clip(args[0], handoff)
			_footage_handoff = handoff and not _interrupted()
		"recap":
			await _recap(args[0] if args.size() > 0 else "")
		"diary":
			await _diary(args[0] if args.size() > 0 else "")
		"explore":
			# explore(组)：放进庄园大地图自由探索，按任务表给提示、等玩家触发（docs/06 2.2）
			await _explore(args[0] if args.size() > 0 else "")
		"station":
			# station(物件)：客房的一站（桌面 / 打字机 / 床）。只有这一站描边，玩家走过去按 E；回客房后不能再出门（docs/01 第 4 节）
			await _station(args[0] if args.size() > 0 else "")
		"wake":
			# wake()：在客房的床上睁眼、坐起、站到床边，把控制权交给玩家
			if not autoplay:
				world.unlock_room()
				await world.wake_up()
		"sleep":
			# sleep()：眼睑合上，结束这一天；sleep(睁眼) = 这一夜没有睡，眼睛不合上（第 6 章）
			if not autoplay:
				world.unlock_room()
				if not (args.size() > 0 and args[0] == "睁眼"):
					await ui.eyelids_close()
		"corridor":
			# corridor()：进入第 5 章的回廊，走完（或退化为跳过）继续下一镜
			await _corridor()
		"osd":
			# osd(样式,文件名,编号,时间)；osd() 关闭
			ui.footage.set_live(args[0] if args.size() > 0 else "", args[1] if args.size() > 1 else "", args[2] if args.size() > 2 else "", args[3] if args.size() > 3 else "")
		_:
			push_warning("未知动作，已跳过：" + name)


func _corridor() -> void:
	if autoplay:
		# 无界面回归：不真的走，直接按表把每层该收的线索收掉
		for r in ContentDB.corridor:
			_collect(String(r.get("collect", "")))
		return
	world.start_corridor()
	await corridor_done
	# 走完：把每层该收的线索收进证据板
	for r in ContentDB.corridor:
		_collect(String(r.get("collect", "")))
	GameState.record("corridor", "回廊")


func _collect(id: String) -> void:
	if not ContentDB.evidence.has(id):
		push_warning("证据表中没有：" + id)
		return
	if not GameState.evidence.has(id):
		GameState.add_evidence(id)
		world.play_sound("ui_collect")
		ui.toast("收入笔记本：" + ContentDB.evidence[id]["name"])
		ui.notebook_ping()


func _show_hotspot(id: String) -> void:
	var h: Dictionary = ContentDB.hotspots.get(id, {})
	if not GameState.inspected.has(id):
		GameState.inspected.append(id)
	world.set_frozen(true)
	world.play_sounds(h.get("sound", ""))
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
		_inspect_pending = pending
		while not pending.is_empty():
			var id: String = await inspected
			if id == CANCEL:
				_inspect_pending = []
				world.highlight_hotspots([])
				ui.set_checklist([])
				return
			if not pending.has(id):
				continue  # 走进别的房间（enter:）之类的探索事件，这里不管
			await _show_hotspot(id)
			pending.erase(id)
			ui.set_progress(ids.size() - pending.size(), ids.size())
			_checklist(ids, pending)
		_inspect_pending = []
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


# ───────────── 自由探索（任务表） ─────────────

## 一轮自由探索：玩家在庄园里走，左上角列出提示；走到人面前交谈、走进房间、推开某扇门，就播放对应的镜头，
## 播完回到原地继续走。写了 require 的任务（回客房）完成后，这一轮结束，回到镜头表的下一镜。
func _explore(group: String) -> void:
	var qs: Array = ContentDB.quests.get(group, [])
	if qs.is_empty():
		push_warning("任务表里没有这一组：" + group)
		return
	_explore_group = group
	var present: Array = []
	for q in qs:
		var t: String = q.get("trigger", "")
		if t.begins_with("talk:"):
			present.append(t.get_slice("@", 1) + "/" + t.trim_prefix("talk:").get_slice("@", 0))
	while true:
		var open: Array = qs.filter(func(q): return not GameState.quests_done.has(q["id"]) and quest_ready(q))
		if open.is_empty():
			break
		var pick: Dictionary = {}
		if autoplay:
			for q in open:
				if q.get("require", "") == "":
					pick = q
					break
			if pick.is_empty():
				pick = open[0]
		else:
			if world.current_id != "manor":
				world.show_scene("guest_room")
			ui.set_cinematic(false)
			# 先进入探索状态再交给玩家：从单独加载的房间（主卧）回到大地图时，玩家站回原处，不被送回客房
			world.set_explore(open.map(func(q): return q["trigger"]), present)
			world.set_mode("walk", "")
			_explore_checklist(qs)
			var id: String = await inspected
			if id == CANCEL:
				_explore_group = ""
				world.end_explore()
				ui.set_checklist([])
				return
			for q in open:
				if q["trigger"] == id:
					pick = q
			if pick.is_empty():
				continue
		world.end_explore()
		ui.set_checklist([])
		GameState.quests_done.append(pick["id"])
		GameState.save()
		if pick.get("shot", "") != "":
			await _play_range(pick["shot"], pick.get("until", ""))
			if _interrupted():
				_explore_group = ""
				return
		if pick.get("require", "") != "":
			break
	_explore_group = ""
	world.end_explore()
	ui.set_checklist([])


## require 列：a|b|2:c,d,e（a、b 都完成，且 c、d、e 里至少两个）；
## “全部” = 这一组里能拿到线索的任务都做完了（这一章的线索收齐，docs/01 第 4 节）
static func quest_ready(q: Dictionary) -> bool:
	for part in String(q.get("require", "")).split("|", false):
		var p := part.strip_edges()
		if p == "全部":
			for o in ContentDB.quests.get(q.get("group", ""), []):
				if o["id"] != q["id"] and o.get("require", "") == "" and not quest_evidence(o).is_empty() \
						and not GameState.quests_done.has(o["id"]):
					return false
			continue
		if p.contains(":"):
			var need := int(p.get_slice(":", 0))
			var n := 0
			for id in p.get_slice(":", 1).split(",", false):
				if GameState.quests_done.has(id.strip_edges()):
					n += 1
			if n < need:
				return false
		elif not GameState.quests_done.has(p):
			return false
	return true


func _explore_checklist(qs: Array) -> void:
	var items: Array = []
	# 线索计数：这一组任务能拿到的线索，已经收进笔记本的有几条
	var all: Array = group_evidence(qs[0].get("group", "")) if not qs.is_empty() else []
	if not all.is_empty():
		var got: int = all.filter(func(e): return GameState.evidence.has(e)).size()
		items.append({"text": "线索 %d / %d" % [got, all.size()], "done": false, "head": true})
	for q in qs:
		var done: bool = GameState.quests_done.has(q["id"])
		if done or quest_ready(q):
			items.append({"text": fill(q.get("hint", "")), "done": done})
			# 收尾任务（回客房）第一次出现：打字机“叮”一声，告诉玩家这一天可以结束了
			if not done and q.get("require", "") != "" and not _end_announced.has(q["id"]):
				_end_announced[q["id"]] = true
				if not all.is_empty():
					world.play_sound("typewriter_return")
					ui.toast("今天的线索收齐了。")
	ui.set_checklist(items)


## 一条任务能拿到的线索：它的镜头里 collect(...) 的，加上 inspect(...) 检查的物件给出的
static func quest_evidence(q: Dictionary) -> Array:
	var out: Array = []
	var cur: String = q.get("shot", "")
	var last: String = q.get("until", "")
	var guard := 0
	while cur != "" and ContentDB.shots.has(cur) and guard < 64:
		guard += 1
		var row: Dictionary = ContentDB.shots[cur]
		for a in Actions.parse(row.get("actions", "")):
			if a["name"] == "collect":
				out.append_array(a["args"])
			elif a["name"] == "inspect":
				for h in a["args"]:
					var e: String = ContentDB.hotspots.get(h, {}).get("evidence", "")
					if e != "":
						out.append(e)
		if last == "" or cur == last:
			break
		var n: String = row.get("next", "").strip_edges()
		cur = ContentDB.next_in_order(cur) if n == "" else n
	return out


static func group_evidence(group: String) -> Array:
	var out: Array = []
	for q in ContentDB.quests.get(group, []):
		if q.get("require", "") != "":
			continue  # 收尾任务自己的镜头（如降灵会）不算在“收齐”里
		for e in quest_evidence(q):
			if not out.has(e):
				out.append(e)
	return out


# ───────────── 客房的一站 ─────────────

## 一天结束时，客房里按顺序只有一站可以交互（桌面 → 打字机 → 床）。玩家走过去按 E，镜头坐到那一站；
## 走到客房门口会被挡回来（这一天不能再出门）。床：躺下，眼睑半合；之后 sleep() 合上
func _station(id: String) -> void:
	if autoplay or id == "":
		return
	if world.current_id != "manor":
		world.show_scene("guest_room")
	ui.set_cinematic(false)
	world.set_mode("walk", "")
	world.lock_room("guest_room")
	world.highlight_hotspots([id])
	while true:
		var got: String = await inspected
		if got == CANCEL:
			world.highlight_hotspots([])
			return
		if got == id:
			break
	world.highlight_hotspots([])
	ui.set_objective("")
	world.play_sounds(ContentDB.hotspots.get(id, {}).get("sound", ""))
	if id == "hs_bed":
		await world.lie_down()
		await ui.eyelids_to(0.45, 1.6)
	elif STATION_CAM.has(id):
		world.set_mode("camera", STATION_CAM[id])
		await _wait(1.0)


# ───────────── 回想（地面指引） ─────────────

## Q：指向哪里。行走检查时 = 还没看的物件；自由探索时 = 还没做的任务（先做能拿线索的，收齐后才指客房）；
## 回到客房收尾（锁着）或不在走动时 = 不指（图标变灰）
func guide_targets() -> Array:
	var out: Array = []
	if world == null or world.room_locked() != "":
		return out
	if not _inspect_pending.is_empty():
		for id in _inspect_pending:
			out.append(id)
		return out
	if _explore_group == "":
		return out
	for q in ContentDB.quests.get(_explore_group, []):
		if not GameState.quests_done.has(q["id"]) and quest_ready(q):
			out.append(q["trigger"])
	return out


## 播放一段镜头：从 first 到 last（含），按 next 列走；last 为空只播 first
func _play_range(first: String, last: String) -> void:
	var cur := first
	var guard := 0
	while cur != "" and cur != "END" and ContentDB.shots.has(cur) and guard < 64:
		guard += 1
		var row: Dictionary = ContentDB.shots[cur]
		GameState.shot = cur
		_played += 1
		await _play(row)
		if _interrupted() or last == "" or cur == last:
			return
		cur = resolve_next(row)


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


## 一章结束、睡下以后的梦：上一章的复盘（台词表的一组，逐行浮现）。
## 影像片段表里有“梦_<组名>”这个片段时（如 梦_r1），先播放它，作为这一章独立的梦境动画。
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
			out.append({"text": t})
	var clip := "梦_" + set_id
	if ui.footage.clips.is_empty():
		ui.footage.reload()
	if not ui.footage.clips.has(clip):
		clip = ""
	if out.is_empty() and clip == "":
		push_warning("复盘组为空：" + set_id)
		return
	await ui.dream(out, clip)


## 新一章开头：日记本上的一页（台词表的一组）。说话人写“日期”“天气”“标题”的行填进对应位置，
## 说话人空着的行是标题下面的小字（如“离开庭还有六天”）。
func _diary(set_id: String) -> void:
	var page := {"date": "", "weather": "", "title": "", "notes": []}
	var v := GameState.vars()
	for r in ContentDB.lines.get(set_id, []):
		if not ContentDB.condition_matches(r.get("condition", ""), v):
			continue
		var t: String = fill(r["text"])
		match r.get("speaker", ""):
			"日期": page["date"] = t
			"天气": page["weather"] = t
			"标题": page["title"] = t
			_: page["notes"].append(t)
	if page["date"] == "" and page["title"] == "":
		push_warning("日记组为空：" + set_id)
		return
	var covered := Callable()
	if _footage_handoff:
		_footage_handoff = false
		covered = func():
			ui.footage.finish_handoff()
			world.fade_loop("projector", 2.5)
	await ui.diary(page, covered)


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
			world.play_sounds(r.get("sound", ""))
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
