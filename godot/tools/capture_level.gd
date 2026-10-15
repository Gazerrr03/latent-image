extends SceneTree
## 关卡美术预览截图：给关卡场景临时加上天空、阳光与后期（不写进关卡场景），从关卡里的各个 cam_ 机位与附加机位依次截图。
## 用法（会弹出窗口）：
##   godot --path godot --resolution 1600x900 --script res://tools/capture_level.gd -- --level=manor --out=/tmp/manor_godot [--only=客房]
## 附加机位用设计坐标（X, N, 标高），与 assets/3d/manor/scripts/13_beauty.py 的镜头一致。

const EXTRA := {
	"manor": [
		["正面草坪", Vector3(9.6, -18.5, 1.6), Vector3(9.6, 0.0, 4.6), 62.0],
		["前鸟瞰", Vector3(5.0, -40.0, 12.5), Vector3(10.0, -2.0, 3.0), 50.0],
		["正门近景", Vector3(9.6, -5.2, 1.7), Vector3(9.6, 0.0, 2.2), 45.0],
		["西侧小路", Vector3(-2.1, -3.5, 1.7), Vector3(-1.0, 12.0, 4.8), 70.0],
		["后鸟瞰", Vector3(6.0, 33.0, 13.5), Vector3(11.5, 10.0, 4.5), 55.0],
		["后花园与温室", Vector3(22.0, 19.5, 5.3), Vector3(11.0, 10.5, 5.6), 70.0],
		["客房_全景", Vector3(4.45, 2.95, 5.165), Vector3(0.4, 2.55, 4.665), 55.0],
		["客房_书桌", Vector3(1.55, 3.2, 4.965), Vector3(0.5, 3.45, 4.415), 38.0],
		["客房_床与壁炉", Vector3(1.05, 3.95, 5.115), Vector3(3.6, 1.0, 4.315), 55.0],
		["前室_镜子", Vector3(4.2, 3.75, 5.165), Vector3(6.6, 3.75, 4.815), 45.0],
		["暗房_全景", Vector3(17.35, 7.8, 5.315), Vector3(16.2, 10.9, 4.365), 60.0],
		["暗房_显影盘", Vector3(16.05, 9.95, 5.165), Vector3(15.95, 10.78, 4.495), 42.0],
		["暗房_侧门", Vector3(16.6, 9.75, 5.215), Vector3(18.9, 9.7, 4.715), 50.0],
		["温室_全景", Vector3(21.15, 8.95, 5.26), Vector3(23.9, 12.5, 4.41), 62.0],
		["温室_侧门", Vector3(21.6, 8.6, 5.16), Vector3(19.2, 9.75, 4.76), 50.0],
	],
}

func _arg(name: String, default: String) -> String:
	for a in OS.get_cmdline_user_args():
		if a.begins_with("--%s=" % name): return a.split("=", true, 1)[1]
	return default

func _g(p: Vector3) -> Vector3:
	return Vector3(p.x, p.z, -p.y)                         # 设计坐标 (X, N, 标高) → Godot (X, 标高, −N)

func _initialize() -> void:
	_run.call_deferred()

func _run() -> void:
	var level := _arg("level", "manor")
	var out := _arg("out", "/tmp/%s_godot" % level)
	DirAccess.make_dir_recursive_absolute(out)
	var root := Node3D.new(); get_root().add_child(root)
	var lv: Node3D = (load("res://levels/%s.tscn" % level) as PackedScene).instantiate(); root.add_child(lv)
	for n in lv.find_children("*", "DirectionalLight3D", true, false): n.visible = false      # 关卡自带的月光：预览用白天的太阳代替
	var env := Environment.new()
	env.background_mode = Environment.BG_SKY
	var sky := Sky.new(); var sm := ProceduralSkyMaterial.new()
	sm.sky_top_color = Color(0.33, 0.47, 0.68); sm.sky_horizon_color = Color(0.82, 0.78, 0.70)
	sm.ground_horizon_color = Color(0.6, 0.55, 0.45); sm.ground_bottom_color = Color(0.25, 0.22, 0.18)
	sm.sun_angle_max = 20.0
	sky.sky_material = sm; env.sky = sky
	env.ambient_light_source = Environment.AMBIENT_SOURCE_SKY; env.ambient_light_energy = 0.9
	env.reflected_light_source = Environment.REFLECTION_SOURCE_SKY
	env.tonemap_mode = Environment.TONE_MAPPER_AGX if "TONE_MAPPER_AGX" in Environment else Environment.TONE_MAPPER_FILMIC
	env.ssao_enabled = true; env.ssao_radius = 1.2; env.ssao_intensity = 2.0
	env.ssil_enabled = true
	env.ssr_enabled = true
	env.glow_enabled = true; env.glow_intensity = 0.4
	env.fog_enabled = true; env.fog_light_color = Color(0.75, 0.75, 0.78); env.fog_density = 0.0025; env.fog_aerial_perspective = 0.6
	var we := WorldEnvironment.new(); we.environment = env; root.add_child(we)
	var sun := DirectionalLight3D.new()
	sun.light_color = Color(1.0, 0.86, 0.68); sun.light_energy = 2.2; sun.shadow_enabled = true
	sun.directional_shadow_max_distance = 90.0; sun.light_angular_distance = 1.0
	root.add_child(sun)
	sun.look_at_from_position(Vector3.ZERO, Vector3(0.55, -0.34, -0.62), Vector3.UP)       # 午后阳光从西南方照向东北（Godot +z 为南）
	var cam := Camera3D.new(); root.add_child(cam); cam.current = true; cam.far = 600.0
	var shots: Array = []
	for c in lv.find_children("cam_*", "Camera3D", true, false):
		shots.append([String(c.name), c.global_transform, c.fov])
	for e in EXTRA.get(level, []):
		var t := Transform3D(Basis(), _g(e[1])).looking_at(_g(e[2]), Vector3.UP)
		shots.append([e[0], t, e[3]])
	var only := _arg("only", "")
	if only != "": shots = shots.filter(func(s): return only in String(s[0]))
	for s in shots:
		cam.global_transform = s[1]; cam.fov = s[2]
		for i in 24: await process_frame                      # 让阴影、SSAO、SSIL 收敛
		var img := get_root().get_texture().get_image()
		img.save_png("%s/%s.png" % [out, s[0]])
		print("captured ", s[0])
	quit(0)
