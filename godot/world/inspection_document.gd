extends Node3D
## 实物纸张：正反面使用各自的原文纹理，翻页更换真实纸面。
## 文稿在 inspection_pages.csv；纸张纹理由 assets/3d/inspection/scripts/build_documents.py 生成。
@export var object_id := ""
@export var paper_size := Vector2(0.21, 0.29)
@export var binding := false
@export var initial_page := 0
var front: MeshInstance3D
var back: MeshInstance3D
var page := 0
var back_label: Label3D

func _ready() -> void:
	var edge := MeshInstance3D.new()
	var mesh := BoxMesh.new()
	mesh.size = Vector3(paper_size.x, paper_size.y, 0.012 if binding else 0.0007)
	edge.mesh = mesh
	var material := StandardMaterial3D.new()
	material.albedo_color = Color("#d2c5a7")
	material.roughness = 0.95
	edge.material_override = material
	add_child(edge)
	for reverse in [false, true]:
		var face := MeshInstance3D.new()
		var plane := QuadMesh.new()
		plane.size = paper_size
		face.mesh = plane
		face.position.z = (-1 if reverse else 1) * (0.0061 if binding else 0.00045)
		if reverse:
			face.rotation.y = PI
		face.material_override = StandardMaterial3D.new()
		face.material_override.roughness = 0.95
		add_child(face)
		if reverse:
			back = face
		else:
			front = face
	if binding:
		var spine := MeshInstance3D.new()
		var box := BoxMesh.new()
		box.size = Vector3(0.008, paper_size.y + 0.005, 0.015)
		spine.mesh = box
		spine.position.x = -paper_size.x * 0.5
		var leather := StandardMaterial3D.new()
		leather.albedo_color = Color("#33271d")
		leather.roughness = 0.8
		spine.material_override = leather
		add_child(spine)
	set_page(initial_page)

func _ensure_back_label() -> void:
	if is_instance_valid(back_label):
		return
	back_label = Label3D.new()
	back_label.name = "实物背面印字"
	var modern := SystemFont.new()
	modern.font_names = PackedStringArray(["Helvetica Neue", "Arial", "Liberation Sans", "DejaVu Sans"])
	back_label.font = modern
	back_label.font_size = 48
	back_label.outline_size = 0
	back_label.modulate = Color("#282726")
	back_label.position.z = 0.00016
	back.add_child(back_label)

func set_page(index: int) -> void:
	page = index
	front.material_override.albedo_texture = load("res://art/props/inspection/%s_%d_front.png" % [object_id, page])
	back.material_override.albedo_texture = load("res://art/props/inspection/%s_%d_back.png" % [object_id, page])

	var rows: Array = get_node("/root/ContentDB").load_table("res://content/visual/inspection_pages.csv")
	if is_instance_valid(back_label):
		back_label.hide()
	for row in rows:
		if row.get("object", "") == object_id and int(row.get("page", "0")) == index and row.get("dynamic_back", "") == "1":
			_ensure_back_label()
			back_label.text = get_node("/root/Director").fill(row.get("back", ""))
			var width := back_label.font.get_string_size(back_label.text, HORIZONTAL_ALIGNMENT_LEFT, -1, back_label.font_size).x
			back_label.pixel_size = paper_size.x * 0.28 / maxf(1.0, width)
			back_label.show()
