extends RefCounted
## 第四章局部规则。曝光改变的是对旧记录的观察，不改变人物与历史。
const VERSION := 1
var data := {
	"entrance_open": false, "version": VERSION, "has_camera": false, "plate": "NONE", "year": 0,
	"cleared": {}, "pages_read": [], "documents": [], "book_opened": false,
	"key_seen": false, "has_key": false, "box_open": false,
	"final_seen": false, "final_taken": false, "final_loaded": false,
	"final_shots": 0, "final_choice": "", "complete": false
}

func restore(saved: Dictionary) -> void:
	for key in data:
		if saved.has(key) and data[key] is int and (saved[key] is float or saved[key] is int):
			data[key] = int(saved[key])
		elif saved.has(key) and typeof(saved[key]) == typeof(data[key]):
			data[key] = saved[key].duplicate(true) if saved[key] is Array or saved[key] is Dictionary else saved[key]
	data.version = VERSION
	_update_complete()

func snapshot() -> Dictionary:
	return data.duplicate(true)

func page_ids() -> Array:
	var ids: Array = ["intro"]
	if data.has_camera: ids.append("lens")
	if data.plate in ["DEVELOPED", "LOADED2", "ARMED", "EXPOSED2"] or not data.cleared.is_empty():
		ids.append_array(["first_record", "reload"])
	if not data.cleared.is_empty():
		ids.append("history")
		for year in [1920, 1922, 1924]:
			if data.cleared.has(str(year)): ids.append("record_%d" % year)
	if data.key_seen: ids.append("key")
	if data.box_open: ids.append("box")
	if data.final_seen: ids.append("final")
	return ids

func read_page(id: String) -> String:
	if not page_ids().has(id): return "locked"
	if not data.pages_read.has(id): data.pages_read.append(id)
	if id == "key" and data.key_seen and not data.has_key:
		data.has_key = true
		return "key_taken"
	_update_complete()
	return "read"

func read_document(id: String) -> void:
	if not data.documents.has(id): data.documents.append(id)
	_update_complete()

func _update_complete() -> void:
	data.complete = data.final_choice != "" and data.pages_read.has("history") and ["notes", "clip", "relics"].all(func(id): return data.documents.has(id))

func pickup() -> String:
	if data.has_camera: return "camera_already"
	data.has_camera = true
	data.plate = "LOADED"
	return "camera_taken"

func shutter(year: int, focused: bool) -> String:
	if not data.has_camera: return "need_camera"
	if year == 0: return "aim"
	if year == 1926:
		if not data.final_loaded: return "final_locked"
		if not focused: return "focus"
		data.final_shots += 1
		if data.final_shots == 1: return "final_first"
		data.final_choice = "observe"
		data.final_loaded = false
		data.plate = "NONE"
		_update_complete()
		return "final_observed"
	if not focused: return "focus"
	if year not in [1920, 1922, 1924]: return "quiet_year"
	if data.plate == "ARMED" and data.year != year: return "wrong_year"
	if data.cleared.has(str(year)): return "already_clear"
	if data.plate == "LOADED":
		data.plate = "EXPOSED"
		data.year = year
		return "first_shutter"
	if data.plate == "ARMED":
		if data.year != year: return "wrong_year"
		data.plate = "EXPOSED2"
		return "second_shutter"
	return "plate_busy"

func develop() -> String:
	if data.plate == "EXPOSED":
		data.plate = "DEVELOPED"
		return "first_developed"
	if data.plate == "EXPOSED2":
		data.cleared[str(data.year)] = true
		data.plate = "NONE"
		return "history_revealed"
	return "tray_empty"

func holder() -> String:
	if data.final_taken and data.final_choice == "":
		data.final_loaded = true
		data.plate = "FINAL"
		return "final_loaded"
	if data.plate == "DEVELOPED":
		if not data.pages_read.has("reload"): return "need_reload_page"
		data.plate = "LOADED2"
		return "reloaded"
	if data.plate == "NONE":
		data.plate = "LOADED"
		return "new_plate"
	return "holder_busy"

func arm() -> String:
	if data.plate != "LOADED2": return "need_holder"
	data.plate = "ARMED"
	return "armed"

func cabinet(raised: bool) -> String:
	if raised:
		if not data.cleared.has("1920"): return "need_1920"
		if not data.key_seen:
			data.key_seen = true
			return "key_seen"
		return "key_hint"
	if not data.has_key: return "cabinet_locked"
	if not data.box_open:
		data.box_open = true
		return "box_opened"
	if data.final_taken and not data.final_loaded and data.final_choice == "":
		data.final_choice = "keep"
		data.plate = "NONE"
		_update_complete()
		return "final_kept"
	return "box_already"

func observe_final(raised: bool) -> String:
	if not raised: return "raise_final"
	if not data.box_open: return "final_locked"
	data.final_seen = true
	return "final_seen"

func take_final() -> String:
	if not data.box_open or not data.final_seen: return "raise_final"
	if data.final_taken: return "plate_already"
	data.final_taken = true
	return "final_taken"

func target_ids() -> Array:
	var ids: Array = ["hs_cellar_camera", "hs_cellar_portraits", "hs_cellar_relics", "hs_cellar_clip", "hs_cellar_cabinet", "hs_cellar_ladder"]
	if data.has_camera:
		ids.erase("hs_cellar_camera")
		ids.append_array(["hs_cellar_book", "hs_cellar_tray", "hs_cellar_holder"])
	if data.box_open: ids.append("hs_cellar_notes")
	if data.final_seen and not data.final_taken: ids.append("hs_cellar_plate")
	return ids

func next_step() -> String:
	if data.complete: return "leave"
	if not data.has_camera: return "pickup"
	match data.plate:
		"EXPOSED", "EXPOSED2": return "tray"
		"DEVELOPED": return "read_reload" if not data.pages_read.has("reload") else "holder"
		"LOADED2": return "arm"
		"ARMED": return "second"
		"FINAL": return "final_shoot"
	if not data.cleared.has("1920"): return "first"
	if not data.key_seen: return "find_key"
	if not data.has_key: return "read_key"
	if not data.box_open: return "open_box"
	if not data.final_seen: return "view_final"
	if not data.final_taken: return "take_final"
	if data.final_choice == "": return "choose_final"
	if not data.pages_read.has("history"): return "read_history"
	for doc in ["notes", "clip", "relics"]:
		if not data.documents.has(doc): return "read_" + doc
	return "leave"
