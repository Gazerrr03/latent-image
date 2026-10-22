extends SceneTree
## 门槛、可选年份、两种1926观察路径及存档恢复的局部规则回归。
const Rules = preload("res://levels/cellar_state.gd")
var failures := 0
func check(label: String, ok: bool) -> void:
	print("PASS " if ok else "FAIL ", label)
	if not ok: failures += 1
func _initialize() -> void:
	call_deferred("run")
func roundtrip(s) -> void:
	var state = root.get_node("GameState")
	state.cellar = s.snapshot()
	state.active_quest = "c4_cellar"
	state.explore_shot = "C4-01"
	var restored = JSON.parse_string(JSON.stringify(state.to_dict()))
	state.reset()
	state.from_dict(restored)
	var copy = Rules.new()
	copy.restore(state.cellar)
	check("存档往返保留操作状态与探索返回点", copy.snapshot() == s.snapshot() and state.active_quest == "c4_cellar" and state.explore_shot == "C4-01")
func clear_year(s, year: int) -> void:
	if s.data.plate == "NONE": s.holder()
	check("%d首曝" % year, s.shutter(year, true) == "first_shutter")
	s.develop()
	check("首次显影开放操作页", s.page_ids().has("reload"))
	roundtrip(s)
	s.read_page("reload")
	check("实体装回后仍需拨杆", s.holder() == "reloaded" and s.shutter(year, true) == "plate_busy")
	s.arm()
	check("不允许隔年二曝", s.shutter(1924 if year != 1924 else 1922, true) == "wrong_year")
	check("同年二曝", s.shutter(year, true) == "second_shutter")
	check("第二次显影才确认历史", s.develop() == "history_revealed")
func run() -> void:
	root.get_node("GameState").persist = false
	for choice in ["keep", "observe"]:
		var s = Rules.new()
		check("锁住未开放夹层", s.read_page("key") == "locked")
		check("锁柜不直接给钥匙", s.cabinet(false) == "cabinet_locked")
		s.pickup()
		check("普通1926快门锁住", s.shutter(1926, true) == "final_locked")
		check("模糊/空年份无曝光", s.shutter(1920, false) == "focus" and s.shutter(1921, true) == "quiet_year")
		s.shutter(1920, true); s.develop()
		check("没读说明不能重装", s.holder() == "need_reload_page" and s.arm() == "need_holder")
		s.read_page("reload"); s.holder(); s.arm(); s.shutter(1920, true); s.develop()
		clear_year(s, 1922); clear_year(s, 1924)
		check("举镜只发现钥匙线索", s.cabinet(true) == "key_seen" and not s.data.has_key)
		check("读夹层才取钥匙", s.read_page("key") == "key_taken")
		roundtrip(s)
		check("钥匙打开盒子", s.cabinet(false) == "box_opened")
		check("先看今年影像才能拿原片", s.take_final() == "raise_final")
		s.observe_final(true); s.take_final(); roundtrip(s)
		if choice == "keep": s.cabinet(false)
		else:
			s.holder(); s.shutter(1926, true); roundtrip(s); s.shutter(1926, true)
		check("两条路径都不提前结束调查", s.data.final_choice == choice and not s.data.complete)
		s.read_page("history")
		for doc in ["notes", "clip", "relics"]: s.read_document(doc)
		check("完整资料读到才调查完成", s.data.complete)
		roundtrip(s)
	print("CH4_RULES failures=", failures)
	quit(0 if failures == 0 else 1)
