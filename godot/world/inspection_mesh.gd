extends RefCounted
## 将合并家具中已命名的物件材质面原位拆开；不改顶点、摆放或实体碰撞。
## 场景与笔记本使用同一份导入网格，避免拿起整件衣柜。
static func part(source: MeshInstance3D, material_name: String, asset := "", native_size := false) -> MeshInstance3D:
	if material_name == "":
		return source
	for child in source.get_children():
		if child is MeshInstance3D and child.get_meta("inspection_part", "") == material_name:
			return child
	var selected := ArrayMesh.new()
	var remainder := ArrayMesh.new()
	for index in source.mesh.get_surface_count():
		var material := source.get_active_material(index)
		var original := source.mesh.surface_get_material(index)
<<<<<<< HEAD
		var matches := original != null and original.resource_name in material_name.split("|", false)
=======
		var matches := original != null and original.resource_name == material_name
>>>>>>> codex/snapshot-source-20261022-1
		var output := selected if matches else remainder
		output.add_surface_from_arrays(source.mesh.surface_get_primitive_type(index), source.mesh.surface_get_arrays(index))
		output.surface_set_material(output.get_surface_count() - 1, material)
	if selected.get_surface_count() == 0:
		return null
	# 清除旧表面编号上的覆盖材质，材质随各自真实几何一起保留。
	for index in source.mesh.get_surface_count():
		source.set_surface_override_material(index, null)
	source.material_override = null
	source.mesh = remainder
	var object := MeshInstance3D.new()
	object.name = "检视实物"
	object.mesh = _fit_asset(asset, selected.get_aabb(), native_size) if asset != "" else selected
	object.set_meta("inspection_part", material_name)
	source.add_child(object)
	return object


static func replace(source: MeshInstance3D, asset: String) -> void:
	if source.get_meta("inspection_replacement", "") == asset:
		return
	var bounds := source.mesh.get_aabb()
	for surface in source.mesh.get_surface_count():
		source.set_surface_override_material(surface, null)
	source.material_override = null
	source.mesh = _fit_asset(asset, bounds)
	source.set_meta("inspection_replacement", asset)


static func _fit_asset(path: String, bounds: AABB, native_size := false) -> ArrayMesh:
	var model: Node3D = load(path).instantiate()
	var meshes: Array = []
	_collect(model, Transform3D.IDENTITY, meshes)
	var native_bounds := AABB()
	var first := true
	for item in meshes:
		var box: AABB = item[1] * item[0].mesh.get_aabb()
		native_bounds = box if first else native_bounds.merge(box)
		first = false
	var scale := bounds.size / native_bounds.size.max(Vector3.ONE * 0.0001)
	var center := bounds.get_center()
	if native_size:
		# 物理线索不能被旧占位范围拉伸；保留水平中心和承托底面。
		scale = Vector3.ONE
		center.y = bounds.position.y + native_bounds.size.y * 0.5
	var output := ArrayMesh.new()
	for item in meshes:
		var source: MeshInstance3D = item[0]
		var transform: Transform3D = item[1]
		var basis := Basis.from_scale(scale) * transform.basis
		for surface in source.mesh.get_surface_count():
			var arrays := source.mesh.surface_get_arrays(surface)
			var vertices: PackedVector3Array = arrays[Mesh.ARRAY_VERTEX]
			for i in vertices.size():
				vertices[i] = center + (transform * vertices[i] - native_bounds.get_center()) * scale
			arrays[Mesh.ARRAY_VERTEX] = vertices
			var normals: PackedVector3Array = arrays[Mesh.ARRAY_NORMAL]
			for i in normals.size():
				normals[i] = (basis.inverse().transposed() * normals[i]).normalized()
			arrays[Mesh.ARRAY_NORMAL] = normals
			if arrays[Mesh.ARRAY_TANGENT] != null:
				var tangents: PackedFloat32Array = arrays[Mesh.ARRAY_TANGENT]
				for i in range(0, tangents.size(), 4):
					var tangent := (basis * Vector3(tangents[i], tangents[i + 1], tangents[i + 2])).normalized()
					tangents[i] = tangent.x
					tangents[i + 1] = tangent.y
					tangents[i + 2] = tangent.z
				arrays[Mesh.ARRAY_TANGENT] = tangents
			output.add_surface_from_arrays(source.mesh.surface_get_primitive_type(surface), arrays)
			output.surface_set_material(output.get_surface_count() - 1, source.get_active_material(surface))
	model.free()
	return output


static func _collect(node: Node3D, parent: Transform3D, meshes: Array) -> void:
	var transform := parent * node.transform
	if node is MeshInstance3D:
		meshes.append([node, transform])
	for child in node.get_children():
		if child is Node3D:
			_collect(child, transform, meshes)
