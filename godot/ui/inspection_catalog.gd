extends RefCounted
## 实物与阅读内容只在内容表登记；场景和笔记本从这里取同一份数据。
## 笔记本可从原关卡资源读取实物，不依赖玩家此刻所在的房间，也不加载那间房进入游戏。

static func hotspot(id: String, host: Node, notebook := false) -> Dictionary:
	var h: Dictionary = ContentDB.hotspots.get(id, {})
	var entry: Dictionary = {}
	for row in ContentDB.load_table("res://content/visual/inspections.csv"):
		if row.get("hotspot", "") == id:
			entry = row
			break
	var text: String = entry.get("pages", "")
	if text == "":
		text = h.get("text", "")
	var data := {"title": h.get("label", id), "text": Director.fill(text),
		"pages": Array(Director.fill(text).split("\\f", false)),
		"mode": entry.get("mode", "fixed"), "from_notebook": notebook,
		"sources": [], "visuals": [], "asset": entry.get("asset", ""),
		"rotation": _vector(entry.get("rotation", "0,0,0")), "hotspot": id,
		"read_label": "观察记录", "start_back": entry.get("start_back", "") == "1"}
	data["notes"] = Director.fill(h.get("text", ""))
	var wanted: String = entry.get("mesh", "")
	if wanted != "" and is_instance_valid(host.room):
		for node in host._walk(host.room):
			if node is Node3D and String(node.name) == wanted and node.is_visible_in_tree():
				if node is MeshInstance3D and entry.get("part_material", "") != "":
					node = preload("res://world/inspection_mesh.gd").part(node, entry["part_material"], "" if entry.get("world_document", "") == "1" else entry.get("asset", ""), entry.get("asset_fit", "") == "native")
				if not is_instance_valid(node):
					continue
				if node is MeshInstance3D and node.has_meta("inspection_document"):
					for child in host._walk(node.get_meta("inspection_document")):
						if child is MeshInstance3D:
							data["sources"].append(child)
				elif node is MeshInstance3D:
					data["sources"].append(node)
				else:
					for child in host._walk(node):
						if child is MeshInstance3D and child.is_visible_in_tree():
							data["sources"].append(child)
	if notebook and data["mode"] == "portable":
		var sources: Array = data["sources"]
		for source in sources:
			data["visuals"].append(_visual(source, source.global_transform))
		data["sources"] = []
		if data["visuals"].is_empty() and wanted != "":
			var path := ContentDB.level_path(h.get("scene", ""))
			if ResourceLoader.exists(path):
				var model: Node = load(path).instantiate()
				_gather(model, Transform3D.IDENTITY, wanted, data["visuals"], entry.get("part_material", ""), "" if entry.get("world_document", "") == "1" else entry.get("asset", ""), entry.get("asset_fit", "") == "native")
				model.free()
	if notebook and entry.get("notebook_asset", "") != "":
		# 固定痕迹复查保留同一组真实网格关系，独立视口不移动当前房间。
		data["mode"] = "scene"
		data["asset"] = entry["notebook_asset"]
		data["sources"] = []
		data["visuals"] = []
		data["view_center"] = _vector(entry.get("notebook_center", "0,0,0"))
		data["view_span"] = float(entry.get("notebook_span", "1"))
		data["rotation"] = _vector(entry.get("notebook_rotation", "0,0,0"))
		data["read_label"] = "观察记录"
	_document(data, entry.get("object", h.get("evidence", "")))
	if id == "hs_cellar_book": _cellar_book(data)
	return data


static func evidence(id: String, host: Node, where: String, derived: String) -> Dictionary:
	var e: Dictionary = ContentDB.evidence.get(id, {})
	var data := {"mode": "record", "from_notebook": true, "title": e.get("name", id), "sources": [], "visuals": []}
	for h in ContentDB.hotspots.values():
		if h.get("evidence", "") == id:
			data = hotspot(h["id"], host, true)
			if data["mode"] not in ["portable", "scene"]:
				data["mode"] = "record"
			break
	data["title"] = e.get("name", id)
	var detail: String = e.get("detail", "")
	if detail == "":
		detail = e.get("note", "")
	var notes := Director.fill(detail)
	if where != "":
		notes = where + "\n\n" + notes
	if derived != "":
		notes += "\n\n" + derived
	if e.get("hint", "") != "":
		notes += "\n\n我的想法\n" + Director.fill(e["hint"])
	data["notes"] = notes
	_document(data, id)
	if data["mode"] == "record":
		data["pages"] = [notes]
	if id == "ev_cellar_book": _cellar_book(data)
	if id in ["ev_cellar_notes", "ev_cellar_clip", "ev_cellar_relics"]:
		data["on_page_read"] = func(_index):
			var state = preload("res://levels/cellar_state.gd").new()
			state.restore(GameState.cellar)
			state.read_document(id.trim_prefix("ev_cellar_"))
			GameState.cellar = state.snapshot()
			GameState.save()
			if is_instance_valid(host.room) and host.room.has_method("refresh_from_saved"): host.room.refresh_from_saved()
	return data


static func _document(data: Dictionary, id: String) -> void:
	var rows: Array = ContentDB.load_table("res://content/visual/inspection_pages.csv").filter(func(row): return row.get("object", "") == id)
	if rows.is_empty():
		return
	rows.sort_custom(func(a, b): return int(a["page"]) < int(b["page"]))
	data["asset"] = "res://art/props/inspection/" + id + ".tscn"
	data["mode"] = "portable"
	data["read_label"] = "阅读"
	data["can_flip"] = true
	data["rotation"] = Vector3.ZERO
	data["pages"] = rows.map(func(row): return Director.fill(row["front"]))
	data["back_pages"] = rows.map(func(row): return Director.fill(row["back"]))
	if rows[0].get("style", "") in ["drawing", "photo"]:
		data["read_label"] = "描述"
		if rows.any(func(row): return row.get("back", "") != ""):
			data["back_read_label"] = "阅读"


static func _vector(text: String) -> Vector3:
	var values := text.split(",")
	return Vector3(float(values[0]), float(values[1]), float(values[2])) if values.size() == 3 else Vector3.ZERO


static func _gather(node: Node, parent_transform: Transform3D, wanted: String, out: Array, material_name := "", asset := "", native_size := false) -> void:
	var transform := parent_transform
	if node is Node3D:
		transform = parent_transform * node.transform
	if node is MeshInstance3D and String(node.name) == wanted:
		var part := preload("res://world/inspection_mesh.gd").part(node, material_name, asset, native_size)
		if part != null:
			out.append(_visual(part, transform * part.transform if part != node else transform))
	for child in node.get_children():
		_gather(child, transform, wanted, out, material_name, asset, native_size)


static func _visual(source: MeshInstance3D, transform: Transform3D) -> Dictionary:
	var materials: Array = []
	for i in source.mesh.get_surface_count():
		materials.append(source.get_surface_override_material(i))
	return {"mesh": source.mesh, "transform": transform, "material": source.material_override, "materials": materials}


## 主人的记录本使用同一检视/笔记本入口；翻到并阅读才记为已读。
static func _cellar_book(data: Dictionary) -> void:
	var state = preload("res://levels/cellar_state.gd").new()
	state.restore(GameState.cellar)
	var ids: Array = state.page_ids()
	var texts := {}
	for row in ContentDB.load_table("res://content/story/cellar.csv"):
		texts[row.id] = row.title + "\n\n" + row.text
	data["notes"] = ""
	data["pages"] = ids.map(func(id): return texts.get(id, id))
	data["on_page_read"] = func(index):
		var current = preload("res://levels/cellar_state.gd").new()
		current.restore(GameState.cellar)
		if index < 0 or index >= ids.size() or current.data.pages_read.has(ids[index]): return
		var result: String = current.read_page(ids[index])
		GameState.cellar = current.snapshot()
		GameState.save()
		if Director.world and is_instance_valid(Director.world.room) and Director.world.room.has_method("refresh_from_saved"):
			Director.world.room.refresh_from_saved()
		if result == "key_taken": Director.ui.toast(texts.get("key", ""))
