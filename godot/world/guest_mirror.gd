extends RefCounted
## The mirror is a staged reflection: oxidation conceals the face until fixing.
## Keep the reveal independent of L3/L4's white-room material replacement.
static func prepare(level: Node) -> void:
	for n in level.find_children("*", "MeshInstance3D", true, false):
		if String(n.name).contains("前室·穿衣镜"):
			n.add_to_group("no_leak")
			for surface in n.mesh.get_surface_count():
				var original: Material = n.mesh.surface_get_material(surface)
				if original and original.resource_name.contains("镜面"):
					var mat := ShaderMaterial.new()
					mat.shader = preload("res://shaders/guest_mirror.gdshader")
					n.set_surface_override_material(surface, mat)
					n.set_meta("mirror_surface", surface)

static func apply(level: Node, fixed: bool) -> void:
	for n in level.find_children("*", "MeshInstance3D", true, false):
		if n.has_meta("mirror_surface"):
			var mat := n.get_surface_override_material(n.get_meta("mirror_surface")) as ShaderMaterial
			mat.set_shader_parameter("fixed_image", fixed)
	var marker := level.find_child("chr_镜中的格雷", true, false)
	if marker:
		if not marker.has_node("可见虎口疤痕"):
			var scar := Node3D.new()
			scar.name = "可见虎口疤痕"
			marker.add_child(scar)
			for i in 3:
				var stroke := MeshInstance3D.new()
				var box := BoxMesh.new()
				box.size = Vector3(0.013, 0.005, 0.002)
				stroke.mesh = box
				stroke.position = Vector3(0.266 + i * 0.009, 0.819 + sin(i * 1.4) * 0.007, 0.079)
				var skin := StandardMaterial3D.new()
				skin.albedo_color = Color("#e8c8b8")
				stroke.material_override = skin
				stroke.cast_shadow = GeometryInstance3D.SHADOW_CASTING_SETTING_OFF
				scar.add_child(stroke)
		marker.get_node("可见虎口疤痕").visible = fixed
		for n in marker.find_children("*", "MeshInstance3D", true, false):
			n.cast_shadow = GeometryInstance3D.SHADOW_CASTING_SETTING_OFF
			if n.get_parent().name == "可见虎口疤痕":
				continue
			if fixed:
				n.material_override = null
			else:
				var silhouette := StandardMaterial3D.new()
				silhouette.albedo_color = Color("#111112")
				silhouette.roughness = 1.0
				n.material_override = silhouette
