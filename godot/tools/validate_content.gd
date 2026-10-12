extends SceneTree
## 内容检查：在不打开编辑器的情况下检查所有表格是否互相对得上。
## 用法：Godot --headless --path godot --script res://tools/validate_content.gd
## 退出码：0 = 无错误（可能有警告），1 = 有错误。

const DB := preload("res://core/content_db.gd")
const Actions := preload("res://core/actions.gd")
const Greybox := preload("res://world/greybox_specs.gd")
const STORY := "res://content/story/"

var errors: Array = []
var warnings: Array = []


func _init() -> void:
	var shots := DB.load_table(STORY + "shots.csv")
	var hotspots := DB.index_by(DB.load_table(STORY + "hotspots.csv"), "id")
	var evidence := DB.index_by(DB.load_table(STORY + "evidence.csv"), "id")
	var links := DB.group_by(DB.load_table(STORY + "links.csv"), "group")
	var ann := DB.group_by(DB.load_table(STORY + "annotations.csv"), "set_id")
	var lines := DB.group_by(DB.load_table(STORY + "lines.csv"), "set_id")
	var scenes := DB.index_by(DB.load_table(STORY + "scenes.csv"), "id")

	_check_import_files()

	var ids := {}
	for r in shots:
		var id: String = r.get("shot_id", "")
		if id == "":
			errors.append("shots.csv 有一行没有 shot_id")
		elif ids.has(id):
			errors.append("镜号重复：" + id)
		ids[id] = r

	for i in shots.size():
		var r: Dictionary = shots[i]
		var id: String = r["shot_id"]
		var sc: String = r.get("scene", "")
		if sc != "" and not scenes.has(sc):
			errors.append("%s：场景 %s 不在 scenes.csv 中" % [id, sc])
		if not r.get("mode", "") in ["", "camera", "walk"]:
			errors.append("%s：mode 只能是 camera 或 walk" % id)
		# next
		var n: String = r.get("next", "").strip_edges()
		var targets: Array = []
		if n == "":
			if i + 1 < shots.size():
				var nxt: Dictionary = shots[i + 1]
				if r.get("line", "*") not in ["", "*"] and nxt.get("line", "*") != r.get("line", "*"):
					warnings.append("%s：next 留空，表格下一行 %s 属于另一条线，可能走错" % [id, nxt["shot_id"]])
		elif n.contains(">"):
			for opt in n.split("|", false):
				targets.append(opt.split(">")[-1].strip_edges())
		else:
			targets.append(n)
		for t in targets:
			if t != "END" and not ids.has(t):
				warnings.append("%s：next 指向尚未编写的镜头 %s" % [id, t])
		# actions
		for a in Actions.parse(r.get("actions", "")):
			var nm: String = a["name"]
			var args: Array = a["args"]
			if not Actions.ACTIONS.has(nm):
				errors.append("%s：动作 %s 不在白名单中（%s）" % [id, nm, ", ".join(PackedStringArray(Actions.ACTIONS))])
				continue
			match nm:
				"inspect":
					for h in args:
						if not hotspots.has(h):
							errors.append("%s：热区 %s 不在 hotspots.csv 中" % [id, h])
				"collect":
					for e in args:
						if not evidence.has(e):
							errors.append("%s：证据 %s 不在 evidence.csv 中" % [id, e])
				"annotate", "inquire", "accuse", "ending_choice":
					if args.size() > 0 and args[0] != "" and not ann.has(args[0]):
						errors.append("%s：预设组 %s 不在 annotations.csv 中" % [id, args[0]])
				"link":
					if args.is_empty() or not links.has(args[0]):
						errors.append("%s：连线组 %s 不在 links.csv 中" % [id, args])
				"say":
					if args.is_empty() or not lines.has(args[0]):
						errors.append("%s：台词组 %s 不在 lines.csv 中" % [id, args])
				"leak":
					if args.is_empty() or not args[0].is_valid_int() or int(args[0]) < 0 or int(args[0]) > 4:
						errors.append("%s：leak 的参数必须是 0—4" % id)

	for h in hotspots.values():
		var e: String = h.get("evidence", "")
		if e != "" and not evidence.has(e):
			errors.append("热区 %s：证据 %s 不在 evidence.csv 中" % [h["id"], e])
	for g in links:
		for p in links[g]:
			for k in ["a", "b"]:
				if not evidence.has(p.get(k, "")):
					errors.append("连线组 %s：证据 %s 不在 evidence.csv 中" % [g, p.get(k, "")])
	for s in scenes.values():
		var m: String = s.get("model", "")
		var has_model := m != "" and FileAccess.file_exists(m)
		if m != "" and not has_model:
			warnings.append("场景 %s：美术模型 %s 尚未到位，使用灰盒" % [s["id"], m])
		if not has_model and Greybox.get_spec(s["id"]).is_empty():
			errors.append("场景 %s 既没有美术模型，也没有灰盒规格（world/greybox_specs.gd）" % s["id"])

	print("内容检查：%d 个镜头，%d 个热区，%d 件证据" % [shots.size(), hotspots.size(), evidence.size()])
	for w in warnings:
		print("  警告  ", w)
	for e in errors:
		print("  错误  ", e)
	print("结果：%s（%d 个错误，%d 个警告）" % ["通过" if errors.is_empty() else "未通过", errors.size(), warnings.size()])
	quit(0 if errors.is_empty() else 1)


## 每个 CSV 都要有 importer="keep" 的 .import 文件，否则 Godot 会把它当成翻译表导入
func _check_import_files() -> void:
	var dir := DirAccess.open("res://content")
	if dir == null:
		return
	for path in _list("res://content"):
		if path.ends_with(".csv"):
			var imp: String = path + ".import"
			if not FileAccess.file_exists(imp) or not FileAccess.get_file_as_string(imp).contains("\"keep\""):
				var f := FileAccess.open(imp, FileAccess.WRITE)
				f.store_string("[remap]\n\nimporter=\"keep\"\n")
				warnings.append("已为 %s 补上 .import（keep）" % path)


func _list(root: String) -> Array:
	var out: Array = []
	var d := DirAccess.open(root)
	if d == null:
		return out
	for f in d.get_files():
		out.append(root.path_join(f))
	for sub in d.get_directories():
		out.append_array(_list(root.path_join(sub)))
	return out
