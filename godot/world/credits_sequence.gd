extends Node3D
## 庄园建筑实景摄影制作名单与致谢（Credits Sequence）
## 在 Godot 3D 空间内使用电影级摄像机拍摄奥瑞尔庄园全貌，
## 字幕/制作名单卡片跟随庄园建筑的 3D 锚点进行空间投射、排布与视差运动。

signal finished

const FONT_SERIF_NAMES := ["Songti SC", "STSong", "Noto Serif CJK SC", "Source Han Serif SC", "SimSun", "PingFang SC"]
const FONT_MONO_NAMES := ["American Typewriter", "Courier New", "Menlo", "Courier"]

const COLOR_BG := Color(0.03, 0.03, 0.04, 0.76)
const COLOR_BORDER := Color(0.85, 0.78, 0.65, 0.28)
const COLOR_GOLD := Color(0.93, 0.86, 0.72)
const COLOR_AMBER := Color(0.86, 0.74, 0.52)
const COLOR_IVORY := Color(0.96, 0.94, 0.90)
const COLOR_MUTED := Color(0.68, 0.64, 0.58)
const COLOR_RED_ACCENT := Color(0.88, 0.22, 0.16)

var _font_serif: SystemFont
var _font_mono: SystemFont

var _manor_instance: Node3D
var _owns_manor := false
var _cam: Camera3D
var _env_node: WorldEnvironment
var _lights_holder: Node3D

var _audio_music: AudioStreamPlayer
var _audio_rain: AudioStreamPlayer

var _canvas: CanvasLayer
var _letterbox_top: ColorRect
var _letterbox_bottom: ColorRect
var _vignette: ColorRect
var _rain_rect: ColorRect
var _card: PanelContainer
var _card_vbox: VBoxContainer
var _prompt_lbl: Label
var _transition_black: ColorRect

var _cur_shot_idx := 0
var _shot_elapsed := 0.0
var _shot_duration := 9.0
var _transitioning := false
var _is_running := false

const RAIN_SHADER := """shader_type canvas_item;
float h(vec2 p) { return fract(sin(dot(p, vec2(12.9898, 78.233))) * 43758.5453); }
void fragment() {
	vec2 uv = UV * vec2(140.0, 1.0);
	uv.x += UV.y * 16.0;
	float col = floor(uv.x);
	float speed = 0.9 + h(vec2(col, 1.0)) * 0.8;
	float y = fract(UV.y * 1.6 - TIME * speed + h(vec2(col, 2.0)));
	float streak = smoothstep(0.0, 0.03, y) * smoothstep(0.16, 0.03, y);
	float lane = smoothstep(0.5, 0.0, abs(fract(uv.x) - 0.5) * 6.0);
	float on = step(0.55, h(vec2(col, floor(TIME * 0.3 + h(vec2(col, 3.0))))));
	COLOR = vec4(vec3(0.72, 0.76, 0.85), streak * lane * on * 0.18);
}
"""

const VIGNETTE_SHADER := """shader_type canvas_item;
void fragment() {
	vec2 uv = UV - vec2(0.5);
	float dist = length(uv);
	float vig = smoothstep(0.28, 0.72, dist);
	COLOR = vec4(0.01, 0.01, 0.02, vig * 0.55);
}
"""

var SHOTS: Array[Dictionary] = [
	{
		"id": "gate_approach",
		"name": "前院铁门与深秋冷雨",
		"duration": 9.2,
		"cam_start_pos": Vector3(9.6, 2.8, 31.0),
		"cam_start_look": Vector3(9.6, 3.2, 0.0),
		"cam_start_fov": 50.0,
		"cam_end_pos": Vector3(11.2, 2.1, 21.0),
		"cam_end_look": Vector3(9.6, 3.5, 0.0),
		"cam_end_fov": 54.0,
		"anchor_3d": Vector3(6.5, 2.0, 23.0),
		"align": "left",
		"offset": Vector2(60, -130),
		"tag": "CORE DEVELOPMENT TEAM",
		"title": "《潜影》开发团队",
		"subtitle": "",
		"items": [
			{"label": "", "val": "Gazerrr · TTTanya · aqsed123 · cong · Rainy-bit22"}
		]
	},
	{
		"id": "facade_development",
		"name": "主楼立面与主创阵容",
		"duration": 9.8,
		"cam_start_pos": Vector3(4.2, 1.8, 14.5),
		"cam_start_look": Vector3(9.6, 3.4, 0.0),
		"cam_start_fov": 55.0,
		"cam_end_pos": Vector3(14.5, 2.5, 11.5),
		"cam_end_look": Vector3(9.6, 3.6, 0.0),
		"cam_end_fov": 58.0,
		"anchor_3d": Vector3(4.2, 3.4, 3.5),
		"align": "left",
		"offset": Vector2(50, -170),
		"tag": "LATENT IMAGE · AURIEL MANOR · 1926",
		"title": "《 潜 影 》",
		"subtitle": "奥 瑞 尔 庄 园 · 一 九 二 六",
		"items": [
			{"label": "作品定位", "val": "第一人称 3D 推理叙事 / 空间取证交互"},
			{"label": "开发平台与引擎", "val": "Godot Engine 4.7 Forward+ / PC 桌面端"}
		]
	},
	{
		"id": "west_garden_literature",
		"name": "西侧花径与文学哲学灵感",
		"duration": 9.2,
		"cam_start_pos": Vector3(-2.2, 2.0, 5.0),
		"cam_start_look": Vector3(-0.5, 4.0, -8.0),
		"cam_start_fov": 56.0,
		"cam_end_pos": Vector3(-1.2, 3.6, -4.5),
		"cam_end_look": Vector3(1.5, 4.8, -14.0),
		"cam_end_fov": 60.0,
		"anchor_3d": Vector3(-1.8, 3.2, -1.0),
		"align": "left",
		"offset": Vector2(60, -150),
		"tag": "LITERARY & PHILOSOPHICAL INSPIRATIONS",
		"title": "文 学 与 哲 学 灵 感 致 敬",
		"subtitle": "时间的迷宫与记忆的接缝",
		"items": [
			{"label": "Jorge Luis Borges", "val": ""},
			{"label": "灵感源泉", "val": "《分岔小径的花园》·《双重人》·《沙之书》"},
			{"label": "核心哲思", "val": "“时间永远分岔，通向无数的将来。”"},
			{"label": "", "val": ""},
			{"label": "Agatha Christie", "val": ""},
			{"label": "叙事启发", "val": "古典英伦暴风雪山庄模式与叙事诡计的永恒先驱"}
		]
	},
	{
		"id": "greenhouse_photography",
		"name": "玻璃花房与摄影史先驱",
		"duration": 9.5,
		"cam_start_pos": Vector3(25.0, 5.5, -20.0),
		"cam_start_look": Vector3(18.0, 5.0, -11.0),
		"cam_start_fov": 55.0,
		"cam_end_pos": Vector3(19.5, 5.0, -14.5),
		"cam_end_look": Vector3(15.0, 5.2, -9.0),
		"cam_end_fov": 58.0,
		"anchor_3d": Vector3(22.0, 5.5, -14.5),
		"align": "right",
		"offset": Vector2(-520, -150),
		"tag": "PIONEERS OF PHOTOGRAPHY",
		"title": "摄 影 史 与 银 盐 工 艺 先 驱",
		"subtitle": "光的留存与显影的具身体验",
		"items": [
			{"label": "William Henry Fox Talbot", "val": ""},
			{"label": "技术先驱", "val": "拉考克修道院 (Lacock Abbey) · 负片摄影与银盐显影术发明者"},
			{"label": "历史文献", "val": "《自然的画笔》(The Pencil of Nature, 1844)"},
			{"label": "", "val": ""},
			{"label": "Spirit Photography (灵异摄影先驱)", "val": ""},
			{"label": "艺术隐喻", "val": "“相纸不仅记录光线，更记录下不可见的记忆与执念。”"}
		]
	},
	{
		"id": "darkroom_gameplay",
		"name": "暗房后墙通风口与游戏设计致敬",
		"duration": 9.8,
		"cam_start_pos": Vector3(17.8, 5.6, -17.5),
		"cam_start_look": Vector3(16.5, 4.8, -10.0),
		"cam_start_fov": 54.0,
		"cam_end_pos": Vector3(16.6, 4.7, -12.8),
		"cam_end_look": Vector3(16.2, 5.1, -8.5),
		"cam_end_fov": 56.0,
		"anchor_3d": Vector3(18.2, 5.2, -11.0),
		"align": "left",
		"offset": Vector2(60, -170),
		"tag": "SPATIAL NARRATIVE & GAME DESIGN HOMAGE",
		"title": "经 典 游 戏 与 空 间 探 索 致 敬",
		"subtitle": "叙事机制与心理沉浸的灯塔",
		"items": [
			{"label": "《P.T.》 (Hideo Kojima)", "val": "有限循环空间中的心理压迫感与环境叙事标杆"},
			{"label": "《奥伯拉丁的回归》 (Lucas Pope)", "val": "三维空间物证与定格瞬间的纯粹推理艺术"},
			{"label": "《金偶像之谜》 (Color Gray Games)", "val": "线索填空还原案情与因果闭环逻辑"},
			{"label": "《极乐迪斯科》 (ZA/UM)", "val": "分裂人格的内在自省、对话与创伤面对"}
		]
	},
	{
		"id": "aerial_finale",
		"name": "苍穹大远景与终局致谢",
		"duration": 14.0,
		"cam_start_pos": Vector3(9.6, 6.5, 16.0),
		"cam_start_look": Vector3(9.6, 3.8, 0.0),
		"cam_start_fov": 52.0,
		"cam_end_pos": Vector3(13.5, 23.0, 44.0),
		"cam_end_look": Vector3(10.0, 4.0, -3.0),
		"cam_end_fov": 46.0,
		"anchor_3d": Vector3(9.6, 7.5, 4.0),
		"align": "center",
		"offset": Vector2(-280, -180),
		"tag": "SPECIAL THANKS & DEDICATION",
		"title": "特 别 鸣 谢",
		"subtitle": "致每一位见证真相的探寻者",
		"items": [
			{"label": "2026 第十四届全国大学生数字媒体科技作品及创意竞赛", "val": ""},
			{"label": "全体参与作品盲测并提供宝贵反馈的体验者", "val": ""},
			{"label": "Godot Engine 全球开源社区与贡献者", "val": ""},
			{"label": "", "val": ""},
			{"label": "“这一次，他自己冲洗了那张底片。”", "val": ""},
			{"label": "", "val": ""},
			{"label": "献给每一个勇于直面真实自我的人。", "val": ""}
		]
	}
]


func _ready() -> void:
	_init_fonts()
	_setup_3d_environment()
	_setup_lights()
	_setup_ui()
	_setup_audio()


func start_sequence() -> void:
	_is_running = true
	_cur_shot_idx = 0
	_shot_elapsed = 0.0
	_apply_shot(_cur_shot_idx, true)
	_transition_black.color.a = 1.0
	var transition := create_tween()
	transition.tween_interval(0.55)
	transition.tween_property(_transition_black, "color:a", 0.0, 1.0)


func _init_fonts() -> void:
	_font_serif = SystemFont.new()
	_font_serif.font_names = PackedStringArray(FONT_SERIF_NAMES)
	_font_mono = SystemFont.new()
	_font_mono.font_names = PackedStringArray(FONT_MONO_NAMES)


func _logo_font() -> SystemFont:
	var font := SystemFont.new()
	font.font_names = PackedStringArray(["Apple Chancery", "Snell Roundhand", "Baskerville"])
	return font


func _setup_3d_environment() -> void:
	# 检查是否已包含庄园
	if not _manor_instance:
		var scene: PackedScene = load("res://levels/manor.tscn")
		if scene:
			_manor_instance = scene.instantiate()
			add_child(_manor_instance)
			_owns_manor = true

	# 电影级摄像机
	_cam = Camera3D.new()
	_cam.name = "CreditsCinematicCamera"
	_cam.current = true
	_cam.far = 600.0
	_cam.near = 0.05
	add_child(_cam)

	# 电影级夜景环境
	_env_node = WorldEnvironment.new()
	var env := Environment.new()
	env.background_mode = Environment.BG_SKY

	var sky := Sky.new()
	var sm := ProceduralSkyMaterial.new()
	sm.sky_top_color = Color(0.04, 0.06, 0.12)
	sm.sky_horizon_color = Color(0.10, 0.14, 0.22)
	sm.ground_horizon_color = Color(0.06, 0.08, 0.12)
	sm.ground_bottom_color = Color(0.02, 0.02, 0.04)
	sky.sky_material = sm
	env.sky = sky

	env.ambient_light_source = Environment.AMBIENT_SOURCE_SKY
	env.ambient_light_energy = 0.42
	env.reflected_light_source = Environment.REFLECTION_SOURCE_SKY
	env.tonemap_mode = Environment.TONE_MAPPER_AGX if "TONE_MAPPER_AGX" in Environment else Environment.TONE_MAPPER_FILMIC

	env.fog_enabled = true
	env.fog_mode = Environment.FOG_MODE_EXPONENTIAL
	env.fog_density = 0.0032
	env.fog_light_color = Color(0.12, 0.16, 0.24)

	env.glow_enabled = true
	env.glow_intensity = 0.55
	env.glow_bloom = 0.15

	env.ssao_enabled = true
	env.ssao_radius = 1.4
	env.ssao_intensity = 1.8

	_env_node.environment = env
	add_child(_env_node)


func _setup_lights() -> void:
	_lights_holder = Node3D.new()
	_lights_holder.name = "CreditsAccentLights"
	add_child(_lights_holder)

	# 正门暖色马车灯两盏
	_add_point_light(Vector3(8.03, 2.15, 0.45), Color(1.0, 0.75, 0.42), 12.0, 8.0)
	_add_point_light(Vector3(11.17, 2.15, 0.45), Color(1.0, 0.75, 0.42), 12.0, 8.0)

	# 门厅与正立面窗格暖光
	_add_point_light(Vector3(9.6, 2.2, 1.2), Color(1.0, 0.72, 0.38), 24.0, 14.0)

	# 客厅与餐厅窗景微光
	_add_point_light(Vector3(3.5, 2.0, 1.2), Color(1.0, 0.68, 0.35), 14.0, 10.0)
	_add_point_light(Vector3(16.5, 2.0, 1.2), Color(1.0, 0.68, 0.35), 14.0, 10.0)

	# 温室玻璃花房内暖光
	_add_point_light(Vector3(22.0, 5.5, -12.0), Color(1.0, 0.70, 0.40), 28.0, 16.0)

	# 暗房猩红安全灯渗透光晕（点题）
	_add_point_light(Vector3(17.2, 4.6, -11.5), Color(0.98, 0.15, 0.10), 16.0, 9.0)


func _add_point_light(pos: Vector3, col: Color, energy: float, radius: float) -> Light3D:
	var l := OmniLight3D.new()
	l.position = pos
	l.light_color = col
	l.light_energy = energy
	l.omni_range = radius
	l.shadow_enabled = true
	_lights_holder.add_child(l)
	return l


func _setup_audio() -> void:
	_audio_music = AudioStreamPlayer.new()
	_audio_music.stream = load("res://audio/music/ending.ogg")
	_audio_music.volume_db = -80.0
	add_child(_audio_music)

	_audio_rain = AudioStreamPlayer.new()
	_audio_rain.stream = load("res://audio/sfx/rain_night.ogg")
	_audio_rain.volume_db = -80.0
	add_child(_audio_rain)

	_audio_music.play()
	_audio_rain.play()

	var t := create_tween().set_parallel(true)
	t.tween_property(_audio_music, "volume_db", 0.0, 2.5)
	t.tween_property(_audio_rain, "volume_db", -9.0, 2.0)


func _setup_ui() -> void:
	_canvas = CanvasLayer.new()
	_canvas.layer = 20
	add_child(_canvas)

	var root := Control.new()
	root.set_anchors_preset(Control.PRESET_FULL_RECT)
	root.mouse_filter = Control.MOUSE_FILTER_IGNORE
	_canvas.add_child(root)

	_transition_black = ColorRect.new()
	_transition_black.color = Color.BLACK
	_transition_black.set_anchors_preset(Control.PRESET_FULL_RECT)
	_transition_black.mouse_filter = Control.MOUSE_FILTER_IGNORE
	_transition_black.z_index = 100
	root.add_child(_transition_black)

	# 2.39:1 宽银幕黑边遮幅（Letterbox）
	_letterbox_top = ColorRect.new()
	_letterbox_top.color = Color(0, 0, 0, 1.0)
	_letterbox_top.set_anchors_preset(Control.PRESET_TOP_WIDE)
	_letterbox_top.anchor_bottom = 0.115
	_letterbox_top.mouse_filter = Control.MOUSE_FILTER_IGNORE
	root.add_child(_letterbox_top)

	var line_top := ColorRect.new()
	line_top.color = Color(0.85, 0.78, 0.65, 0.15)
	line_top.set_anchors_preset(Control.PRESET_BOTTOM_WIDE)
	line_top.anchor_top = 1.0
	line_top.custom_minimum_size.y = 1
	_letterbox_top.add_child(line_top)

	_letterbox_bottom = ColorRect.new()
	_letterbox_bottom.color = Color(0, 0, 0, 1.0)
	_letterbox_bottom.set_anchors_preset(Control.PRESET_BOTTOM_WIDE)
	_letterbox_bottom.anchor_top = 0.885
	_letterbox_bottom.mouse_filter = Control.MOUSE_FILTER_IGNORE
	root.add_child(_letterbox_bottom)

	var line_bot := ColorRect.new()
	line_bot.color = Color(0.85, 0.78, 0.65, 0.15)
	line_bot.set_anchors_preset(Control.PRESET_TOP_WIDE)
	line_bot.custom_minimum_size.y = 1
	_letterbox_bottom.add_child(line_bot)

	# 胶片暗角 Vignette
	_vignette = ColorRect.new()
	_vignette.set_anchors_preset(Control.PRESET_FULL_RECT)
	_vignette.mouse_filter = Control.MOUSE_FILTER_IGNORE
	var vm := ShaderMaterial.new()
	vm.shader = Shader.new()
	vm.shader.code = VIGNETTE_SHADER
	_vignette.material = vm
	root.add_child(_vignette)

	# 细密雨丝层
	_rain_rect = ColorRect.new()
	_rain_rect.set_anchors_preset(Control.PRESET_FULL_RECT)
	_rain_rect.mouse_filter = Control.MOUSE_FILTER_IGNORE
	var rm := ShaderMaterial.new()
	rm.shader = Shader.new()
	rm.shader.code = RAIN_SHADER
	_rain_rect.material = rm
	root.add_child(_rain_rect)

	# 跟随建筑运动的半透明文字卡片
	_card = PanelContainer.new()
	_card.mouse_filter = Control.MOUSE_FILTER_IGNORE

	var style := StyleBoxFlat.new()
	style.bg_color = COLOR_BG
	style.border_color = COLOR_BORDER
	style.set_border_width_all(1)
	style.set_corner_radius_all(3)
	style.content_margin_left = 32
	style.content_margin_right = 32
	style.content_margin_top = 26
	style.content_margin_bottom = 26
	style.shadow_color = Color(0, 0, 0, 0.55)
	style.shadow_size = 10
	_card.add_theme_stylebox_override("panel", style)
	root.add_child(_card)

	_card_vbox = VBoxContainer.new()
	_card_vbox.mouse_filter = Control.MOUSE_FILTER_IGNORE
	_card_vbox.add_theme_constant_override("separation", 10)
	_card.add_child(_card_vbox)

	# 底部跳过提示
	_prompt_lbl = Label.new()
	_prompt_lbl.text = " [ 空格 / 鼠标点击: 下一段 · ESC: 跳过 ] "
	_prompt_lbl.add_theme_font_override("font", _font_mono)
	_prompt_lbl.add_theme_font_size_override("font_size", 12)
	_prompt_lbl.add_theme_color_override("font_color", Color(0.58, 0.54, 0.48, 0.75))
	_prompt_lbl.set_anchors_preset(Control.PRESET_BOTTOM_RIGHT)
	_prompt_lbl.anchor_left = 1.0
	_prompt_lbl.anchor_top = 1.0
	_prompt_lbl.grow_horizontal = Control.GROW_DIRECTION_BEGIN
	_prompt_lbl.grow_vertical = Control.GROW_DIRECTION_BEGIN
	_prompt_lbl.position = Vector2(-260, -32)
	_letterbox_bottom.add_child(_prompt_lbl)


func _build_card_content(shot: Dictionary) -> void:
	for c in _card_vbox.get_children():
		_card_vbox.remove_child(c)
		c.queue_free()

	# 顶部英文小标题 (Mono)
	if shot.has("tag") and shot["tag"] != "":
		var tag_lbl := Label.new()
		tag_lbl.text = shot["tag"]
		tag_lbl.add_theme_font_override("font", _font_mono)
		tag_lbl.add_theme_font_size_override("font_size", 11)
		tag_lbl.add_theme_color_override("font_color", COLOR_MUTED)
		_card_vbox.add_child(tag_lbl)

	if shot.get("id", "") == "gate_approach":
		var logo := Label.new()
		logo.text = "latent image"
		logo.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER
		logo.custom_minimum_size = Vector2(360, 56)
		logo.add_theme_font_override("font", _logo_font())
		logo.add_theme_font_size_override("font_size", 42)
		logo.add_theme_color_override("font_color", COLOR_GOLD)
		_card_vbox.add_child(logo)
		var logo_rule := Label.new()
		logo_rule.text = "──────  AURIEL MANOR · 1926  ──────"
		logo_rule.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER
		logo_rule.add_theme_font_override("font", _font_mono)
		logo_rule.add_theme_font_size_override("font_size", 10)
		logo_rule.add_theme_color_override("font_color", COLOR_AMBER)
		_card_vbox.add_child(logo_rule)

	# 中文主标题 (Serif)
	if shot.has("title") and shot["title"] != "":
		var title_lbl := Label.new()
		title_lbl.text = shot["title"]
		title_lbl.add_theme_font_override("font", _font_serif)
		title_lbl.add_theme_font_size_override("font_size", 24)
		title_lbl.add_theme_color_override("font_color", COLOR_GOLD)
		_card_vbox.add_child(title_lbl)

	# 副标题 (Serif)
	if shot.has("subtitle") and shot["subtitle"] != "":
		var sub_lbl := Label.new()
		sub_lbl.text = shot["subtitle"]
		sub_lbl.add_theme_font_override("font", _font_serif)
		sub_lbl.add_theme_font_size_override("font_size", 15)
		sub_lbl.add_theme_color_override("font_color", COLOR_AMBER)
		_card_vbox.add_child(sub_lbl)

	# 优雅横线分割线
	var div := ColorRect.new()
	div.custom_minimum_size = Vector2(0, 1)
	div.color = Color(0.85, 0.78, 0.65, 0.22)
	_card_vbox.add_child(div)

	# 核心引言（如有）
	if shot.has("quote") and shot["quote"] != "":
		var q_lbl := Label.new()
		q_lbl.text = shot["quote"]
		q_lbl.add_theme_font_override("font", _font_serif)
		q_lbl.add_theme_font_size_override("font_size", 14)
		q_lbl.add_theme_color_override("font_color", COLOR_AMBER)
		q_lbl.autowrap_mode = TextServer.AUTOWRAP_WORD_SMART
		_card_vbox.add_child(q_lbl)

	# 列表项（角色名单 / 致敬内容）
	if shot.has("items"):
		var grid := VBoxContainer.new()
		grid.add_theme_constant_override("separation", 6)
		_card_vbox.add_child(grid)

		for it in shot["items"]:
			var label_text: String = it.get("label", "")
			var val_text: String = it.get("val", "")

			if label_text == "" and val_text == "":
				var spacer := Control.new()
				spacer.custom_minimum_size.y = 4
				grid.add_child(spacer)
				continue

			var row := HBoxContainer.new()
			row.add_theme_constant_override("separation", 16)
			grid.add_child(row)

			if label_text == "":
				var v_only := Label.new()
				v_only.text = val_text
				v_only.add_theme_font_override("font", _font_serif)
				v_only.add_theme_font_size_override("font_size", 15)
				v_only.add_theme_color_override("font_color", COLOR_IVORY)
				row.add_child(v_only)
			elif val_text == "":
				# 单行整行显示（如书名、致敬人名、题记）
				var l := Label.new()
				l.text = label_text
				l.add_theme_font_override("font", _font_serif)
				l.add_theme_font_size_override("font_size", 15)
				if label_text.begins_with("“") or label_text.begins_with("献给"):
					l.add_theme_color_override("font_color", COLOR_AMBER)
				else:
					l.add_theme_color_override("font_color", COLOR_GOLD)
				row.add_child(l)
			else:
				# 左侧角色/标签，右侧名字/值
				var l_lbl := Label.new()
				l_lbl.text = label_text
				l_lbl.custom_minimum_size.x = 160
				l_lbl.add_theme_font_override("font", _font_serif)
				l_lbl.add_theme_font_size_override("font_size", 14)
				l_lbl.add_theme_color_override("font_color", COLOR_MUTED)
				row.add_child(l_lbl)

				var v_lbl := Label.new()
				v_lbl.text = val_text
				v_lbl.add_theme_font_override("font", _font_serif)
				v_lbl.add_theme_font_size_override("font_size", 15)
				v_lbl.add_theme_color_override("font_color", COLOR_IVORY)
				row.add_child(v_lbl)


func _process(delta: float) -> void:
	if not _is_running:
		return

	var cur_shot: Dictionary = SHOTS[_cur_shot_idx]
	_shot_elapsed += delta
	var duration: float = cur_shot.get("duration", 9.0)
	var progress := clampf(_shot_elapsed / duration, 0.0, 1.0)

	# 平滑缓动 (Hermite / Smoothstep)
	var t := smoothstep(0.0, 1.0, progress)

	# 摄像机在 3D 庄园空间内运动
	var start_pos: Vector3 = cur_shot["cam_start_pos"]
	var end_pos: Vector3 = cur_shot["cam_end_pos"]
	_cam.global_position = start_pos.lerp(end_pos, t)

	var start_look: Vector3 = cur_shot["cam_start_look"]
	var end_look: Vector3 = cur_shot["cam_end_look"]
	var cur_look := start_look.lerp(end_look, t)
	_cam.look_at(cur_look, Vector3.UP)

	var start_fov: float = cur_shot.get("cam_start_fov", 55.0)
	var end_fov: float = cur_shot.get("cam_end_fov", 55.0)
	_cam.fov = lerp(start_fov, end_fov, t)

	# 空间投影与建筑贴合排布
	if cur_shot.has("anchor_3d"):
		var anchor_3d: Vector3 = cur_shot["anchor_3d"]
		# 判断锚点是否在摄像机前方
		var cam_forward := -_cam.global_transform.basis.z
		var to_anchor := (anchor_3d - _cam.global_position).normalized()

		if cam_forward.dot(to_anchor) > 0.05:
			var screen_pos := _cam.unproject_position(anchor_3d)
			var offset: Vector2 = cur_shot.get("offset", Vector2.ZERO)
			var target_pos: Vector2 = screen_pos + offset

			# 约束在宽银幕画幅安全区内
			var vp_size := get_viewport().get_visible_rect().size
			var top_limit := vp_size.y * 0.125 + 16.0
			var bot_limit := vp_size.y * 0.875 - _card.size.y - 16.0

			target_pos.x = clampf(target_pos.x, 60.0, max(60.0, vp_size.x - _card.size.x - 60.0))
			target_pos.y = clampf(target_pos.y, top_limit, max(top_limit, bot_limit))

			_card.position = _card.position.lerp(target_pos, delta * 6.5)

	# 字幕淡入淡出曲线
	var is_last_shot := (_cur_shot_idx == SHOTS.size() - 1)
	var alpha := 1.0
	var fade_time := 0.75

	if _shot_elapsed < fade_time:
		alpha = smoothstep(0.0, 1.0, _shot_elapsed / fade_time)
	elif not is_last_shot and _shot_elapsed > (duration - fade_time):
		alpha = smoothstep(1.0, 0.0, (_shot_elapsed - (duration - fade_time)) / fade_time)

	_card.modulate.a = alpha

	# 检查镜头时间结束
	if _shot_elapsed >= duration and not is_last_shot and not _transitioning:
		_advance_shot()
	elif is_last_shot and _shot_elapsed >= duration and (Director.autoplay or DisplayServer.get_name() == "headless" or OS.has_feature("movie") or OS.get_cmdline_user_args().has("--record-credits")):
		_finish_credits()


func _advance_shot() -> void:
	if _transitioning:
		return
	if _cur_shot_idx < SHOTS.size() - 1:
		_transitioning = true
		_cur_shot_idx += 1
		_shot_elapsed = 0.0
		_apply_shot(_cur_shot_idx, false)
		_transitioning = false
	else:
		_finish_credits()


func _apply_shot(idx: int, immediate: bool) -> void:
	var shot: Dictionary = SHOTS[idx]
	_build_card_content(shot)
	_card.reset_size()
	_card.visible = not shot.get("hide_card", false)

	# 初始重置位置
	var anchor_3d: Vector3 = shot.get("anchor_3d", Vector3.ZERO)
	_cam.global_position = shot["cam_start_pos"]
	_cam.look_at(shot["cam_start_look"], Vector3.UP)
	_cam.fov = shot.get("cam_start_fov", 55.0)

	var screen_pos := _cam.unproject_position(anchor_3d)
	var offset: Vector2 = shot.get("offset", Vector2.ZERO)
	var target_pos: Vector2 = screen_pos + offset
	var vp_size := get_viewport().get_visible_rect().size
	var top_limit := vp_size.y * 0.125 + 16.0
	var bot_limit := vp_size.y * 0.875 - _card.size.y - 16.0

	target_pos.x = clampf(target_pos.x, 60.0, max(60.0, vp_size.x - _card.size.x - 60.0))
	target_pos.y = clampf(target_pos.y, top_limit, max(top_limit, bot_limit))
	_card.position = target_pos
	_card.modulate.a = 0.0 if not immediate else 1.0


func _unhandled_input(event: InputEvent) -> void:
	if not _is_running:
		return

	if event.is_action_pressed("ui_cancel"):
		get_viewport().set_input_as_handled()
		_finish_credits()
	elif event.is_action_pressed("ui_accept") or (event is InputEventMouseButton and event.pressed and event.button_index == MOUSE_BUTTON_LEFT) or (event is InputEventKey and event.pressed and event.keycode in [KEY_SPACE, KEY_ENTER, KEY_E]):
		get_viewport().set_input_as_handled()
		if _cur_shot_idx < SHOTS.size() - 1:
			_advance_shot()
		else:
			_finish_credits()


func _finish_credits() -> void:
	if not _is_running:
		return
	_is_running = false

	# 淡出声音与片尾卡片，再落到全屏黑场。
	var t := create_tween().set_parallel(true)
	if _audio_music:
		t.tween_property(_audio_music, "volume_db", -80.0, 1.2)
	if _audio_rain:
		t.tween_property(_audio_rain, "volume_db", -80.0, 1.2)
	if _card:
		t.tween_property(_card, "modulate:a", 0.0, 0.8)
	t.tween_property(_transition_black, "color:a", 1.0, 1.0)

	await t.finished
	finished.emit()
	queue_free()
