extends RefCounted
## 密室流程状态机。只做规则，不碰节点、不碰 UI，方便 headless 测试。

signal changed
signal narrate(text)
signal frame_changed(year, visual_state)
signal notebook_unlocked(page_id)
signal ending_reached(choice)

var content: Dictionary
var years: Dictionary = {}
var pages: Dictionary = {}
var unlocked: Array[String] = ["intro"]

var has_camera := false
var camera_raised := false
var plate_state := "NONE"          # NONE / LOADED / EXPOSED / DEVELOPED / LOADED2 / ARMED / EXPOSED2 / FINAL
var exposed_year := 0
var focus := 0.0
var target_id := ""
var target_kind := ""
var target_year := 0
var cleared: Dictionary = {}
var holder_seen := false
var key_seen := false
var key_taken := false
var has_key := false
var box_open := false
var crystals_seen := false
var owner_seen := false
var final_choice := ""
var trace_seen: Dictionary = {}

# 记录本 / 实体底片
var notebook_opened_once := false
var page4_read := false
var final_page_read := false
var plate_1926_taken := false
var final_loaded := false
var final_returned := false
var final_shots := 0


func _init(data: Dictionary) -> void:
	content = data
	for y in data.get("years", []):
		years[int(y.get("year", 0))] = y
	for p in data.get("notebook", []):
		pages[String(p.get("id", ""))] = p


func prompt(key: String) -> String:
	return String(content.get("prompts", {}).get(key, ""))


func year_data(year: int) -> Dictionary:
	return years.get(year, {})


func year_name(year: int) -> String:
	return String(year_data(year).get("name", ""))


func is_haunted(year: int) -> bool:
	return bool(year_data(year).get("haunted", false))


func is_clearable(year: int) -> bool:
	return is_haunted(year) and year != 1926


func visual_state(year: int) -> String:
	return "empty" if cleared.has(str(year)) else "normal"


func set_target(id: String, kind: String, year: int) -> void:
	if id == target_id and kind == target_kind and year == target_year:
		return
	target_id = id
	target_kind = kind
	target_year = year
	focus = 0.0
	changed.emit()


func clear_target() -> void:
	if target_id == "":
		return
	target_id = ""
	target_kind = ""
	target_year = 0
	focus = 0.0
	changed.emit()


func pickup_camera() -> bool:
	if has_camera:
		return false
	has_camera = true
	plate_state = "LOADED"
	unlock("camera")
	narrate.emit("相机移开了。下面压着一本摊开的记录本。")
	changed.emit()
	return true


func raise_camera() -> bool:
	if not has_camera or camera_raised:
		return false
	camera_raised = true
	changed.emit()
	return true


func lower_camera() -> bool:
	if not camera_raised:
		return false
	camera_raised = false
	focus = 0.0
	changed.emit()
	return true


func focus_step(direction: float) -> void:
	if not camera_raised or target_kind != "frame" or not is_haunted(target_year):
		return
	var step := 0.12 * pow(maxf(0.0, 1.0 - focus), 0.8) + 0.01
	focus = clampf(focus + step * signf(direction), 0.0, 1.0)
	changed.emit()


func focus_ok() -> bool:
	return focus >= 0.88


func shutter() -> String:
	if final_loaded:
		return final_shutter()
	if not has_camera:
		narrate.emit(prompt("no_camera"))
		return "no_camera"
	if not camera_raised:
		narrate.emit(prompt("raise"))
		return "raise"
	if target_kind != "frame":
		narrate.emit("先对准一张照片。")
		return "aim"
	if not focus_ok():
		narrate.emit(prompt("focus_low"))
		return "focus"

	if plate_state == "ARMED":
		if target_year != exposed_year:
			narrate.emit("不是同一张。第二次必须拍同一张。")
			return "wrong_year"
		if target_year == 1926:
			narrate.emit("这一张，先想清楚。")
			return "final_locked"
		plate_state = "EXPOSED2"
		narrate.emit(prompt("shutter_second"))
		changed.emit()
		return "second"

	if plate_state == "LOADED":
		if not is_haunted(target_year):
			narrate.emit(String(year_data(target_year).get("line", prompt("already"))))
			return "quiet"
		if target_year == 1926:
			narrate.emit("快门按不下去。先看看盒子里有什么。")
			return "final_locked"
		plate_state = "EXPOSED"
		exposed_year = target_year
		narrate.emit(prompt("shutter_first"))
		changed.emit()
		return "first"

	if plate_state == "DEVELOPED" or plate_state == "LOADED2":
		narrate.emit(prompt("reload"))
		return "reload"
	if plate_state == "NONE":
		narrate.emit("相机里没有干版。")
		return "no_plate"
	return "busy"


func develop() -> String:
	if plate_state == "EXPOSED":
		plate_state = "DEVELOPED"
		unlock("first")
		unlock("second")       # 第 4 页：装片与 R 的写法
		narrate.emit(prompt("develop_first"))
		changed.emit()
		return "first"
	if plate_state == "EXPOSED2":
		var yr := exposed_year
		plate_state = "NONE"
		cleared[str(yr)] = true
		frame_changed.emit(yr, "empty")
		unlock("cleared")
		unlock("clear_%d" % yr)
		var y := year_data(yr)
		var line := String(y.get("clear", ""))
		narrate.emit((line + "\n" if line != "" else "") + prompt("develop_second"))
		changed.emit()
		return "second"
	narrate.emit("显影盘里没有需要显影的干版。")
	return "nothing"


func reload_plate() -> bool:
	if plate_state == "DEVELOPED":
		if not page4_read:
			narrate.emit("卡住了。本子上也许有写法。")
			return false
		plate_state = "LOADED2"
		unlock("second")
		narrate.emit(prompt("reload"))
		changed.emit()
		return true
	if plate_state == "NONE" and cleared.size() > 0:
		plate_state = "LOADED"
		narrate.emit("换了一张新的干版。")
		changed.emit()
		return true
	return false


func arm_second() -> bool:
	if not page4_read:
		narrate.emit("先翻记录本，看看二次曝光怎么拨。")
		return false
	if plate_state != "LOADED2":
		narrate.emit("先装回已经显影的干版。")
		return false
	plate_state = "ARMED"
	unlock("second")
	narrate.emit(prompt("arm"))
	changed.emit()
	return true


func inspect_holder(camera: bool) -> String:
	if camera:
		holder_seen = true
		unlock("holder")
		narrate.emit(prompt("holder_camera"))
		changed.emit()
		return "camera"
	if plate_state == "DEVELOPED" and not page4_read:
		narrate.emit("卡住了。本子上也许有写法。")
		return "need_notebook"
	narrate.emit(prompt("holder_hand"))
	return "hand"


func inspect_cabinet(camera: bool) -> String:
	if camera and not cleared.has("1920"):
		narrate.emit("柜子上什么也没有。先处理完 1920。")
		return "empty"
	if camera and not key_seen:
		key_seen = true
		unlock("key")
		narrate.emit(prompt("key"))
		changed.emit()
		return "key"
	if not has_key:
		narrate.emit(prompt("box_locked"))
		return "locked"
	if not box_open:
		box_open = true
		unlock("box")
		narrate.emit(prompt("box_open"))
		changed.emit()
		return "open"
	if not plate_1926_taken:
		return "plate_available"
	if plate_1926_taken and not final_loaded and not final_returned:
		return "plate_in_hand"
	narrate.emit("盒子已经开着。")
	return "already"


func inspect_tray(camera: bool) -> String:
	if camera:
		if not crystals_seen:
			crystals_seen = true
			narrate.emit(String(content.get("traces", {}).get("crystals", {}).get("text", "")))
			changed.emit()
			return "crystals"
		narrate.emit("先放下相机。")
		return "need_lower"
	return develop()


func inspect_trace(id: String) -> String:
	var traces: Dictionary = content.get("traces", {})
	if not traces.has(id):
		return "none"
	trace_seen[id] = true
	narrate.emit(String(traces[id].get("text", "")))
	changed.emit()
	return id


func inspect_frame(year: int, camera: bool) -> String:
	if camera:
		if year == 1926 and box_open:
			unlock("final")
			if not owner_seen:
				owner_seen = true
				narrate.emit(prompt("owner"))
				changed.emit()
				return "owner"
			narrate.emit(prompt("owner"))
			return "owner"
		var y := year_data(year)
		narrate.emit(String(y.get("line", "")))
		return "lens"
	var y := year_data(year)
	var line := String(y.get("line", ""))
	if cleared.has(str(year)) and String(y.get("clear", "")) != "":
		line = String(y.get("clear", ""))
	narrate.emit(line)
	return "eye"


func take_1926_plate() -> bool:
	if not box_open or plate_1926_taken:
		return false
	if not owner_seen:
		narrate.emit("先举镜看她一眼。")
		return false
	plate_1926_taken = true
	narrate.emit("盒底有一张 1926 的底片。你把它拿在手里。")
	changed.emit()
	return true


func return_1926_plate() -> bool:
	if not plate_1926_taken or final_loaded or final_returned or is_ending():
		return false
	final_returned = true
	choose_final("keep")
	return true


func load_1926_plate() -> bool:
	if not plate_1926_taken or final_returned or final_loaded or is_ending():
		return false
	final_loaded = true
	plate_state = "FINAL"
	narrate.emit("1926 底片装进相机。按 F 举镜，拍两次。")
	changed.emit()
	return true


func final_shutter() -> String:
	if not final_loaded:
		return "no_plate"
	if not camera_raised:
		narrate.emit("先举镜。")
		return "raise"
	if target_kind != "frame" or target_year != 1926:
		narrate.emit("对准 1926。")
		return "aim"
	final_shots += 1
	if final_shots == 1:
		narrate.emit("第一次快门。她看着镜头。")
		changed.emit()
		return "first"
	if final_shots >= 2:
		choose_final("shoot")
		return "second"
	return "busy"


func mark_notebook_opened() -> void:
	notebook_opened_once = true


func mark_page_read(page_id: String) -> bool:
	if page_id == "second" and not page4_read:
		page4_read = true
		narrate.emit("你看懂了：片夹要装回，拨杆在右边。")
		changed.emit()
		return true
	if page_id == "key" and key_seen and not key_taken:
		key_taken = true
		has_key = true
		narrate.emit("钥匙从本子夹层里滑出来。")
		changed.emit()
		return true
	if page_id == "final":
		final_page_read = true
	return false


func choose_final(choice: String) -> bool:
	if not box_open:
		return false
	final_choice = choice
	narrate.emit(String(content.get("endings", {}).get(choice, "")))
	ending_reached.emit(choice)
	changed.emit()
	return true


func is_ending() -> bool:
	return final_choice != ""


func notebook_pages() -> Array:
	var out: Array = []
	for p in content.get("notebook", []):
		if unlocked.has(String(p.get("id", ""))):
			out.append(p)
	return out


func unlock(page_id: String) -> void:
	if page_id == "" or unlocked.has(page_id) or not pages.has(page_id):
		return
	unlocked.append(page_id)
	notebook_unlocked.emit(page_id)
	changed.emit()
