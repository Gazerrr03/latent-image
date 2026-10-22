extends SceneTree
## Contract check for the oxidation/fixing boundary and authored model placement.
const Mirror := preload("res://world/guest_mirror.gd")
func _initialize() -> void:
	call_deferred("run")
func run() -> void:
	var room: Node3D = load("res://levels/guest_room.tscn").instantiate()
	root.add_child(room)
	var marker: Node3D = room.find_child("chr_镜中的格雷", true, false)
	var model: Node3D = load("res://art/characters/char_grey_mirror.glb").instantiate()
	marker.add_child(model)
	Mirror.prepare(room)
	var count := 0
	for n in room.find_children("*", "MeshInstance3D", true, false):
		if n.has_meta("mirror_surface"):
			count += 1
	assert(count == 1, "Exactly one guest mirror surface must be staged")
	for fixed in [false, true, false]:
		Mirror.apply(room, fixed)
		for n in room.find_children("*", "MeshInstance3D", true, false):
			if n.has_meta("mirror_surface"):
				assert(n.get_surface_override_material(n.get_meta("mirror_surface")).get_shader_parameter("fixed_image") == fixed)
		for n in marker.find_children("*", "MeshInstance3D", true, false):
			if n.get_parent().name != "可见虎口疤痕":
				assert((n.material_override == null) == fixed)
	var camera := room.find_child("cam_mirror", true, false) as Camera3D
	var toward_camera: Vector3 = camera.global_position - marker.global_position
	toward_camera.y = 0.0
	toward_camera = toward_camera.normalized()
	assert(marker.global_basis.z.dot(toward_camera) > 0.85, "Reflection must face the mirror camera")
	print("GUEST_MIRROR PASS: one surface; oxidized/fixed/replay reset; face toward camera")
	if "--mirror-render" in OS.get_cmdline_user_args():
		Mirror.apply(room, true)
		marker.visible = true
		camera.make_current()
		await process_frame
		await RenderingServer.frame_post_draw
		root.get_texture().get_image().save_png("res://../docs/验证/2026-10-22-C6-C7/guest-mirror-fixed.png")
		Mirror.apply(room, false)
		await process_frame
		await RenderingServer.frame_post_draw
		root.get_texture().get_image().save_png("res://../docs/验证/2026-10-22-C6-C7/guest-mirror-oxidized.png")
	room.free()
	quit()
