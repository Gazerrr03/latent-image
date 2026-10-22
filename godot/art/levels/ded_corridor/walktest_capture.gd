extends SceneTree
## 回廊模型实机截图（临时验收用，不是关卡场景）：载入 ded_corridor_walktest.tscn，在每盏壁灯、房间吊灯处放暖色点光，
## 按几个机位截图到 /tmp/dc_godot_<名>.png。正式的灯光组 layer_1—6 由关卡场景 ded_corridor.tscn（D1）做。
##   godot --path godot --resolution 1280x720 --script res://art/levels/ded_corridor/walktest_capture.gd
const CAMS := {   # 名字: [位置, 看向]（Godot 坐标）
	"layer1": [Vector3(0, 1.55, 0), Vector3(0, 1.35, -8)],
	"darkroom": [Vector3(0, 1.55, -5.6), Vector3(0, 0.9, -8.8)],
	"turn": [Vector3(-0.1, 1.55, -7.7), Vector3(0.1, 1.25, 0.6)],
	"segB": [Vector3(0, 1.55, -8), Vector3(-6, 1.2, -8)],
	"cloakroom": [Vector3(-1.2, 1.55, -6.15), Vector3(-4.1, 1.15, -5.75)],
	"stair_window": [Vector3(0, 2.45, 1.42), Vector3(0, 1.25, -8.8)],
	"greenhouse": [Vector3(30.15, 1.55, 0.95), Vector3(29.95, 1.2, -4.6)],
}
func _initialize() -> void:
	var scene: Node3D = load("res://art/levels/ded_corridor/ded_corridor_walktest.tscn").instantiate()
	root.add_child(scene)
	await process_frame
	for n in scene.find_children("*", "", true, false):          # 第 1 圈的样子：藏起第 4、5、6 圈的东西和墙补片
		var nm0: String = n.name
		if n is Node3D and (nm0.begins_with("prop_chair") or nm0.begins_with("prop_print") or nm0 == "photo_wall" or nm0.begins_with("wall_")):
			(n as Node3D).visible = false
	var env := WorldEnvironment.new(); var e := Environment.new()
	e.background_mode = Environment.BG_COLOR; e.background_color = Color(0.01, 0.01, 0.015)
	e.ambient_light_source = Environment.AMBIENT_SOURCE_COLOR; e.ambient_light_color = Color(0.25, 0.22, 0.2); e.ambient_light_energy = 0.15
	e.tonemap_mode = Environment.TONE_MAPPER_AGX
	env.environment = e; scene.add_child(env)
	for n in scene.find_children("*", "", true, false):
		if not (n is Node3D): continue
		var nm: String = n.name
		var light_at := Vector3.INF
		if nm.begins_with("回廊·壁灯"):
			light_at = (n as Node3D).global_transform * Vector3(0, 0.05, 0.17)    # Blender (0,-0.17,0.05) → Godot
		elif nm.contains("吊灯"):
			light_at = (n as Node3D).global_position + Vector3(0, -0.45, 0)
		if light_at != Vector3.INF:
			var l := OmniLight3D.new(); l.light_color = Color(1.0, 0.72, 0.45); l.light_energy = 1.6; l.omni_range = 5.0; l.shadow_enabled = true
			scene.add_child(l); l.global_position = light_at
	var red := OmniLight3D.new(); red.light_color = Color(1, 0.05, 0.02); red.light_energy = 1.2; red.omni_range = 1.5; scene.add_child(red); red.global_position = Vector3(0, 0.05, -8.95)
	var warm := OmniLight3D.new(); warm.light_color = Color(1, 0.62, 0.3); warm.light_energy = 3.0; warm.omni_range = 4.0; scene.add_child(warm); warm.global_position = Vector3(28.6, 1.9, -3.35)
	var moon := DirectionalLight3D.new(); moon.light_color = Color(0.55, 0.65, 0.9); moon.light_energy = 0.25; scene.add_child(moon); moon.rotation_degrees = Vector3(-55, 30, 0)
	var cam := Camera3D.new(); cam.fov = 60.0; scene.add_child(cam); cam.current = true
	for k in CAMS:
		cam.global_position = CAMS[k][0]; cam.look_at(CAMS[k][1])
		for i in 8: await process_frame
		await RenderingServer.frame_post_draw
		root.get_viewport().get_texture().get_image().save_png("/tmp/dc_godot_%s.png" % k)
		print("captured ", k)
	quit()
