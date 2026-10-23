extends Node3D
## 温室地下暗房：空间 + 相机双重视角 + 对焦与快门 + 显影与历史记录复原

signal session_finished
const Rules := preload("res://levels/cellar_state.gd")
var rules = Rules.new()
var texts := {}
var _interaction_busy := false
var _session_completed := false
var _table_camera_nodes: Array = []
var _cabinet_parts := {}
var _key_ghost: Sprite3D
var _key_prop: MeshInstance3D

const FRAME_SHADER := preload("res://shaders/frame_view.gdshader")
const FOCUS_RING_SCRIPT := preload("res://ui/focus_ring.gd")

var player: Node3D
var player_cam: Camera3D
var viewmodel: Node3D

var camera_overlay: CanvasLayer
var focus_ring: Control
var viewfinder_rect: TextureRect
var camera_hud_label: Label
var aim_target_label: Label
var flash_rect: ColorRect

var guide_pill_layer: CanvasLayer
var guide_pill_panel: PanelContainer
var guide_pill_label: Label

var has_camera: bool:
	get: return rules.data.has_camera
	set(value): rules.data.has_camera = value
var camera_raised := false
var focus := 0.0
var _aim_toast_timer := 0.0
var plate_state: String:
	get: return rules.data.plate
	set(value): rules.data.plate = value
var exposed_year: int:
	get: return rules.data.year
	set(value): rules.data.year = value
var cleared_years: Dictionary:
	get:
		var years := {}
		for year in rules.data.cleared: years[int(year)] = true
		return years
var _gameplay_active := false
var _rest_fov := 70.0

var frame_mats := {}
var frame_years := [1919, 1920, 1921, 1922, 1923, 1924, 1925, 1926]
var frame_info := {
	1919: {"haunted": false, "name": "", "line": "这一年，队伍很整齐。没有多出来的人。"},
	1920: {"haunted": true, "name": "彭罗斯先生", "line": "取景框里，队伍边上多站着一个年轻男人（彭罗斯先生）。他在看镜头。"},
	1921: {"haunted": false, "name": "", "line": "这一年，没有多出来的人。"},
	1922: {"haunted": true, "name": "系围裙的女人", "line": "多出一个系着围裙的胖女人，手垂在身侧。"},
	1923: {"haunted": false, "name": "", "line": "空年份。取景框里只有原本的四个人。"},
	1924: {"haunted": true, "name": "低着头的少年", "line": "一个少年低着头站在最边上，像在躲避镜头。"},
	1925: {"haunted": false, "name": "", "line": "这一年，没有多出来的人。"},
	1926: {"haunted": true, "name": "戴面纱的女人", "line": "一个戴面纱的女人站在队伍边上。今年轮到她。"}
}

var current_aim_year := 0
var camera_only_node: Node3D
var frame_labels_node: Node3D

var _sfx: AudioStreamPlayer
var _red_hum: AudioStreamPlayer


func _ready() -> void:
	rules.restore(GameState.cellar)
	for row in ContentDB.load_table("res://content/story/cellar.csv"):
		texts[row.id] = row
	_init_audio()
	_configure_frame_materials()
	_build_frame_labels()
	_build_camera_only_traces()
	_build_camera_overlay()
	_build_camera_guide_hud()
	_find_table_camera()
	_build_archive_props()

	# 延迟一帧绑定玩家组件，确保 Player 已在场景树中就位
	call_deferred("_bind_player")
	var d := _dir()
	if d and not d.inspected.is_connected(_on_director_inspected):
		d.inspected.connect(_on_director_inspected)


func _dir() -> Node:
	if not is_inside_tree():
		return null
	return get_node_or_null("/root/Director")


func _toast(msg: String) -> void:
	var d := _dir()
	if d and d.ui:
		d.ui.toast(msg)
	if camera_raised and is_instance_valid(aim_target_label):
		_aim_toast_timer = 2.4
		aim_target_label.text = msg
		aim_target_label.modulate = Color(1.0, 0.45, 0.35)


func _hint(msg: String) -> void:
	var d := _dir()
	if d and d.ui:
		d.ui.set_hint(msg)


func _set_cinematic(on: bool) -> void:
	var d := _dir()
	if d and d.ui:
		d.ui.set_cinematic(on)


func _set_objective(text: String) -> void:
	var d := _dir()
	if d and d.ui:
		d.ui.set_objective(text)


func _set_checklist(items: Array) -> void:
	var d := _dir()
	if d and d.ui:
		d.ui.set_checklist(items)


func _exit_tree() -> void:
	if _gameplay_active: _finish(false)
	var d := _dir()
	if d and d.inspected.is_connected(_on_director_inspected):
		d.inspected.disconnect(_on_director_inspected)
	if is_instance_valid(viewmodel):
		viewmodel.queue_free()
	if is_instance_valid(camera_overlay):
		camera_overlay.queue_free()
	if is_instance_valid(guide_pill_layer):
		guide_pill_layer.queue_free()
	if is_instance_valid(player_cam):
		player_cam.fov = _rest_fov
	if camera_raised:
		_set_cinematic(false)


# ---------------------------------------------------------------------------
# 外部流程驱动（Director cellar_gameplay 动作）
# ---------------------------------------------------------------------------

func await_cellar_cleared() -> bool:
	_gameplay_active = true
	rules.data.entrance_open = true
	_save_progress()
	_sync()
	await session_finished
	return _session_completed

func _text(id: String) -> String:
	return texts.get(id, {}).get("text", id)

func _save_progress() -> void:
	GameState.cellar = rules.snapshot()
	GameState.save()

func refresh_from_saved() -> void:
	rules.restore(GameState.cellar)
	_sync()

func _apply(result: String) -> void:
	_save_progress()
	_toast(_text(result))
	_sync()

func _sync() -> void:
	for year in frame_mats:
		frame_mats[year].set_shader_parameter("state", 1.0 if rules.data.cleared.has(str(year)) else 0.0)
	for mesh in _table_camera_nodes:
		mesh.visible = not has_camera
	var hinge := Vector3(-4.30, 0, 3.23)
	var turn := Transform3D(Basis(Vector3.UP, -PI / 2.0), hinge) * Transform3D(Basis.IDENTITY, -hinge)
	for mesh in _cabinet_parts:
		mesh.transform = turn * _cabinet_parts[mesh] if rules.data.box_open else _cabinet_parts[mesh]
	if _key_ghost:
		_key_ghost.visible = camera_raised and rules.data.cleared.has("1920") and not rules.data.has_key
	if _key_prop: _key_prop.visible = rules.data.has_key
	var plate := get_node_or_null("接口/hs_cellar_plate/原片")
	if plate: plate.visible = rules.data.final_seen and not rules.data.final_taken
	_update_camera_guide_hud()
	var d := _dir()
	if not _gameplay_active or not d or d.world.room != self: return
	d.world.highlight_hotspots(rules.target_ids())
	var step: String = _text("step_" + rules.next_step())
	_set_objective(step)
	var docs_done: bool = rules.data.book_opened and ["notes", "clip", "relics"].all(func(id): return rules.data.documents.has(id))
	_set_checklist([
		{"text": texts.get("milestone_camera", {}).get("text", ""), "done": has_camera},
		{"text": texts.get("milestone_history", {}).get("text", ""), "done": rules.data.cleared.has("1920")},
		{"text": texts.get("milestone_key", {}).get("text", ""), "done": rules.data.box_open},
		{"text": texts.get("milestone_final", {}).get("text", ""), "done": rules.data.final_choice != ""},
		{"text": texts.get("milestone_documents", {}).get("text", ""), "done": docs_done or rules.data.complete}
	])

func _finish(completed: bool) -> void:
	if not _gameplay_active: return
	_gameplay_active = false
	_session_completed = completed
	if camera_raised: _toggle_camera_raise()
	_save_progress()
	session_finished.emit()

func _build_archive_props() -> void:
	_key_ghost = Sprite3D.new()
	_key_ghost.texture = load("res://art/levels/gh_cellar/ui/key_ghost.png")
	_key_ghost.billboard = BaseMaterial3D.BILLBOARD_ENABLED
	_key_ghost.pixel_size = 0.002
	_key_ghost.position = Vector3(-4.48, 1.45, 2.9)
	_key_ghost.visible = false
	add_child(_key_ghost)
	_key_prop = MeshInstance3D.new()
	var shape := BoxMesh.new()
	shape.size = Vector3(0.065, 0.008, 0.018)
	_key_prop.mesh = shape
	var brass := StandardMaterial3D.new()
	brass.albedo_color = Color(0.65, 0.45, 0.16)
	brass.metallic = 0.8
	_key_prop.material_override = brass
	_key_prop.position = Vector3(0.82, 0.824, -0.32)
	add_child(_key_prop)

func autoplay_cellar() -> void:
	# 只验证章节连接，真实输入另测；走同一套局部规则，不直接写完成标记。
	if not rules.data.complete:
		rules.pickup()
		rules.shutter(1920, true)
		rules.develop()
		rules.read_page("reload")
		rules.holder()
		rules.arm()
		rules.shutter(1920, true)
		rules.develop()
		rules.read_page("history")
		rules.cabinet(true)
		rules.read_page("key")
		rules.cabinet(false)
		rules.observe_final(true)
		rules.take_final()
		rules.cabinet(false)
		for doc in ["notes", "clip", "relics"]: rules.read_document(doc)
	_save_progress()
	for id in ["ev_cellar_book", "ev_cellar_notes", "ev_cellar_clip", "ev_cellar_relics"]: _dir()._collect(id)
	_sync()


# ---------------------------------------------------------------------------
# 音频
# ---------------------------------------------------------------------------

func _init_audio() -> void:
	_sfx = AudioStreamPlayer.new()
	_sfx.name = "CellarSFX"
	add_child(_sfx)
	_red_hum = AudioStreamPlayer.new()
	_red_hum.name = "CellarRedHum"
	add_child(_red_hum)
	var red_path := "res://audio/sfx/red_hum.ogg"
	if ResourceLoader.exists(red_path):
		var stream = load(red_path)
		if stream is AudioStreamOggVorbis:
			stream.loop = true
		_red_hum.stream = stream
		_red_hum.volume_db = -18.0
		_red_hum.play()


func _play_sfx(sound_name: String) -> void:
	if _sfx == null:
		return
	var path := "res://audio/sfx/%s.ogg" % sound_name
	if ResourceLoader.exists(path):
		_sfx.stream = load(path)
		_sfx.volume_db = -6.0
		_sfx.play()


# ---------------------------------------------------------------------------
# 相框材质与对焦
# ---------------------------------------------------------------------------

func _configure_frame_materials() -> void:
	var model := get_node_or_null("model")
	if model == null:
		return
	var base_tex := "res://art/levels/gh_cellar/textures/frames/"
	for i in 8:
		var year := 1919 + i
		var mesh := model.find_child("Portrait frame %d portrait" % i, true, false) as MeshInstance3D
		if mesh == null:
			continue
		var mat := ShaderMaterial.new()
		mat.shader = FRAME_SHADER
		var norm := base_tex + "%d_normal.png" % year
		var blur := base_tex + "%d_lens_blur.png" % year
		var sharp := base_tex + "%d_lens_sharp.png" % year
		var empty := base_tex + "%d_empty.png" % year
		if ResourceLoader.exists(norm):
			mat.set_shader_parameter("normal_tex", load(norm))
		if ResourceLoader.exists(blur):
			mat.set_shader_parameter("lens_blur_tex", load(blur))
		if ResourceLoader.exists(sharp):
			mat.set_shader_parameter("lens_sharp_tex", load(sharp))
		if ResourceLoader.exists(empty):
			mat.set_shader_parameter("empty_tex", load(empty))
		mat.set_shader_parameter("camera_mix", 0.0)
		mat.set_shader_parameter("focus", 0.0)
		mat.set_shader_parameter("state", 0.0)
		mesh.material_override = mat
		frame_mats[year] = mat


func _build_frame_labels() -> void:
	frame_labels_node = Node3D.new()
	frame_labels_node.name = "FrameLabels"
	add_child(frame_labels_node)
	var coords := {
		1919: Vector3(-2.45, 1.65, -3.91),
		1920: Vector3(-1.82, 1.65, -3.91),
		1921: Vector3(-1.18, 1.66, -3.91),
		1922: Vector3(-0.55, 1.62, -3.91),
		1923: Vector3(0.1, 1.63, -3.91),
		1924: Vector3(0.74, 1.65, -3.91),
		1925: Vector3(1.38, 1.63, -3.91),
		1926: Vector3(2.02, 1.63, -3.91)
	}
	var f: Font = load("res://art/fonts/simhei.ttf") if ResourceLoader.exists("res://art/fonts/simhei.ttf") else null
	for y in coords:
		var l := Label3D.new()
		l.text = str(y)
		if f:
			l.font = f
		l.font_size = 38
		l.pixel_size = 0.0028
		l.outline_size = 5
		l.modulate = Color(0.92, 0.84, 0.68, 0.85)
		l.outline_modulate = Color(0.05, 0.04, 0.02, 0.95)
		l.position = coords[y]
		frame_labels_node.add_child(l)


func _build_camera_only_traces() -> void:
	camera_only_node = Node3D.new()
	camera_only_node.name = "CameraOnlyTraces"
	camera_only_node.visible = false
	add_child(camera_only_node)

	# 1. 西侧旧物旁虚影
	var sil_path := "res://art/levels/gh_cellar/ui/silhouette.png"
	if ResourceLoader.exists(sil_path):
		var tex = load(sil_path)
		for i in 2:
			var s := Sprite3D.new()
			s.texture = tex
			s.billboard = BaseMaterial3D.BILLBOARD_ENABLED
			s.pixel_size = 0.0055
			s.modulate = Color(1, 1, 1, 0.42 if i == 0 else 0.25)
			s.position = Vector3(-4.25 + i * 0.25, 1.18, -1.95 - i * 0.18)
			camera_only_node.add_child(s)

	# 2. 木箱上的未冲洗干版微光
	for i in 4:
		var plate := MeshInstance3D.new()
		var bm := BoxMesh.new()
		bm.size = Vector3(0.24, 0.008, 0.18)
		plate.mesh = bm
		var m := StandardMaterial3D.new()
		m.albedo_color = Color(0.55, 0.65, 0.62, 0.4)
		m.transparency = BaseMaterial3D.TRANSPARENCY_ALPHA
		m.emission_enabled = true
		m.emission = Color(0.45, 0.64, 0.62)
		m.emission_energy_multiplier = 1.8
		plate.material_override = m
		plate.position = Vector3(3.18, 0.78 + i * 0.018, -1.73)
		plate.rotation_degrees.y = 14.0
		camera_only_node.add_child(plate)

	# 3. 木梯上的虚影鞋印
	var fp_path := "res://art/levels/gh_cellar/ui/footprint.png"
	if ResourceLoader.exists(fp_path):
		var fp := Sprite3D.new()
		fp.texture = load(fp_path)
		fp.billboard = BaseMaterial3D.BILLBOARD_ENABLED
		fp.pixel_size = 0.0045
		fp.modulate = Color(1, 1, 1, 0.55)
		fp.position = Vector3(3.72, 0.92, -2.25)
		camera_only_node.add_child(fp)

	# 4. 显影盘底部的白色晶体
	for i in 8:
		var c := MeshInstance3D.new()
		var sm := SphereMesh.new()
		sm.radius = 0.012
		sm.height = 0.028
		c.mesh = sm
		var m := StandardMaterial3D.new()
		m.albedo_color = Color(0.85, 0.88, 0.82)
		m.emission_enabled = true
		m.emission = Color(0.65, 0.75, 0.7)
		m.emission_energy_multiplier = 2.0
		c.material_override = m
		var ang := TAU * i / 8.0
		c.position = Vector3(-4.50 + cos(ang) * 0.14, 1.0, -0.90 + sin(ang) * 0.11)
		camera_only_node.add_child(c)


func _find_table_camera() -> void:
	var model := get_node_or_null("model")
	if model:
		_table_camera_nodes = model.find_children("Camera*", "MeshInstance3D", true, false)
		_table_camera_nodes.append_array(model.find_children("Lens*", "MeshInstance3D", true, false))
		for mesh in model.find_children("Film cabinet*", "MeshInstance3D", true, false):
			if mesh.name in ["Film cabinet door", "Film cabinet inset", "Film cabinet label", "Film cabinet latch", "Film cabinet padlock"]:
				_cabinet_parts[mesh] = mesh.transform
		_align_table_props(model)


func _align_table_props(model: Node) -> void:
	# 桌面表面高度 Y ≈ 0.824，木桌前端边缘在 Z ≈ -0.102，后端在 Z ≈ -1.338
	# 1. 展开手记往北平移收回桌面上，贴合桌面高度
	for mesh in model.find_children("Table open ledger*", "MeshInstance3D", true, false):
		mesh.position.z -= 0.26
		mesh.position.y = 0.824
	# 2. 剪刀整体向北收进桌沿，贴合桌面高度
	for mesh in model.find_children("Scissors*", "MeshInstance3D", true, false):
		mesh.position.z -= 0.26
		mesh.position.y = 0.824
	# 3. 散落照片（Loose print* 与 backing*）原本在 Z = +0.12~+0.18 完全悬空，向北平移收回桌面
	for mesh in model.find_children("Loose print*", "MeshInstance3D", true, false):
		if mesh.position.z > -0.10:
			mesh.position.z -= 0.45
		mesh.position.y = 0.824
	# 4. 放大镜收回桌面
	for mesh in model.find_children("Magnifier*", "MeshInstance3D", true, false):
		if mesh.position.z > -0.10:
			mesh.position.z -= 0.25
		mesh.position.y = 0.824
	# 5. 钥匙串收回桌面
	for mesh in model.find_children("Key ring*", "MeshInstance3D", true, false):
		if mesh.position.z > -0.10:
			mesh.position.z -= 0.25
		mesh.position.y = 0.824
	for mesh in model.find_children("Key shaft*", "MeshInstance3D", true, false):
		if mesh.position.z > -0.10:
			mesh.position.z -= 0.25
		mesh.position.y = 0.824
	# 6. 搪瓷杯与咖啡杯收回桌面
	for mesh in model.find_children("*", "MeshInstance3D", true, false):
		if "cup" in mesh.name.to_lower() and mesh.position.z > -0.10:
			mesh.position.z -= 0.25
	# 7. 散落纸片：超前桌沿（Z > -0.15）的碎纸平移收进桌面，并确保所有纸片落在木桌表面
	for mesh in model.find_children("Paper scrap*", "MeshInstance3D", true, false):
		if mesh.position.z > -0.15:
			mesh.position.z -= 0.52
		mesh.position.y = 0.824


# ---------------------------------------------------------------------------
# 玩家与手持 Viewmodel
# ---------------------------------------------------------------------------

func _bind_player() -> void:
	var d := _dir()
	player = d.world.player if d and d.world else null
	if player and player.cam:
		player_cam = player.cam
		_build_viewmodel()
		_sync()


func _build_viewmodel() -> void:
	if viewmodel or player_cam == null:
		return
	viewmodel = Node3D.new()
	viewmodel.name = "CameraViewmodel"
	viewmodel.position = Vector3(0.25, -0.20, -0.55)
	viewmodel.rotation_degrees = Vector3(-3, -15, 0)
	viewmodel.visible = false
	player_cam.add_child(viewmodel)

	var wood := StandardMaterial3D.new()
	wood.albedo_color = Color(0.20, 0.10, 0.048)
	wood.roughness = 0.5
	wood.metallic = 0.02

	var brass := StandardMaterial3D.new()
	brass.albedo_color = Color(0.58, 0.38, 0.12)
	brass.metallic = 0.85
	brass.roughness = 0.32

	var leather := StandardMaterial3D.new()
	leather.albedo_color = Color(0.045, 0.028, 0.018)
	leather.roughness = 0.8

	# 机身主体
	var body := MeshInstance3D.new()
	var bm := BoxMesh.new()
	bm.size = Vector3(0.16, 0.095, 0.12)
	body.mesh = bm
	body.material_override = wood
	viewmodel.add_child(body)

	# 皮腔
	var bellows := MeshInstance3D.new()
	var bm2 := BoxMesh.new()
	bm2.size = Vector3(0.09, 0.075, 0.08)
	bellows.mesh = bm2
	bellows.position = Vector3(-0.025, 0, 0.065)
	bellows.material_override = leather
	viewmodel.add_child(bellows)

	# 黄铜镜头
	var lens := MeshInstance3D.new()
	var cm := CylinderMesh.new()
	cm.top_radius = 0.035
	cm.bottom_radius = 0.042
	cm.height = 0.08
	lens.mesh = cm
	lens.rotation_degrees.x = 90.0
	lens.position = Vector3(-0.015, 0.0, -0.10)
	lens.material_override = brass
	viewmodel.add_child(lens)


# ---------------------------------------------------------------------------
# 取景器 UI
# ---------------------------------------------------------------------------

func _build_camera_overlay() -> void:
	camera_overlay = CanvasLayer.new()
	camera_overlay.layer = 15
	camera_overlay.visible = false
	add_child(camera_overlay)

	var f: Font = load("res://art/fonts/simhei.ttf") if ResourceLoader.exists("res://art/fonts/simhei.ttf") else null

	# 取景框暗角
	viewfinder_rect = TextureRect.new()
	viewfinder_rect.set_anchors_preset(Control.PRESET_FULL_RECT)
	viewfinder_rect.mouse_filter = Control.MOUSE_FILTER_IGNORE
	viewfinder_rect.expand_mode = TextureRect.EXPAND_IGNORE_SIZE
	viewfinder_rect.stretch_mode = TextureRect.STRETCH_SCALE
	var vf_path := "res://art/levels/gh_cellar/ui/viewfinder.png"
	if ResourceLoader.exists(vf_path):
		viewfinder_rect.texture = load(vf_path)
	camera_overlay.add_child(viewfinder_rect)

	# 中央对焦环
	focus_ring = FOCUS_RING_SCRIPT.new()
	focus_ring.set_anchors_preset(Control.PRESET_FULL_RECT)
	focus_ring.mouse_filter = Control.MOUSE_FILTER_IGNORE
	camera_overlay.add_child(focus_ring)

	# 顶部目标信息
	aim_target_label = Label.new()
	aim_target_label.set_anchors_preset(Control.PRESET_TOP_WIDE)
	aim_target_label.position.y = 48
	aim_target_label.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER
	if f:
		aim_target_label.add_theme_font_override("font", f)
	aim_target_label.add_theme_font_size_override("font_size", 20)
	aim_target_label.add_theme_color_override("font_color", Color(1.0, 0.88, 0.65))
	aim_target_label.text = ""
	camera_overlay.add_child(aim_target_label)

	# 底部操作提示与状态
	camera_hud_label = Label.new()
	camera_hud_label.set_anchors_preset(Control.PRESET_BOTTOM_WIDE)
	camera_hud_label.position.y = -64
	camera_hud_label.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER
	if f:
		camera_hud_label.add_theme_font_override("font", f)
	camera_hud_label.add_theme_font_size_override("font_size", 16)
	camera_hud_label.add_theme_color_override("font_color", Color(0.9, 0.85, 0.75, 0.9))
	camera_hud_label.text = "[举镜中] 滚轮：调焦 · 左键：快门 · R：二次曝光 · F：放下相机"
	camera_overlay.add_child(camera_hud_label)

	# 快门闪光遮罩
	flash_rect = ColorRect.new()
	flash_rect.set_anchors_preset(Control.PRESET_FULL_RECT)
	flash_rect.mouse_filter = Control.MOUSE_FILTER_IGNORE
	flash_rect.color = Color(1.0, 0.95, 0.85, 0.0)
	camera_overlay.add_child(flash_rect)


func _build_camera_guide_hud() -> void:
	guide_pill_layer = CanvasLayer.new()
	guide_pill_layer.layer = 12
	add_child(guide_pill_layer)

	var root_ctrl := Control.new()
	root_ctrl.set_anchors_preset(Control.PRESET_FULL_RECT)
	root_ctrl.mouse_filter = Control.MOUSE_FILTER_IGNORE
	guide_pill_layer.add_child(root_ctrl)

	guide_pill_panel = PanelContainer.new()
	guide_pill_panel.mouse_filter = Control.MOUSE_FILTER_IGNORE
	guide_pill_panel.set_anchors_preset(Control.PRESET_BOTTOM_WIDE)
	guide_pill_panel.offset_left = 260
	guide_pill_panel.offset_right = -260
	guide_pill_panel.offset_top = -68
	guide_pill_panel.offset_bottom = -24

	var sb := StyleBoxFlat.new()
	sb.bg_color = Color(0.08, 0.07, 0.05, 0.88)
	sb.border_color = Color(0.85, 0.72, 0.45, 0.85)
	sb.set_border_width_all(2)
	sb.set_corner_radius_all(6)
	sb.content_margin_left = 16
	sb.content_margin_right = 16
	sb.content_margin_top = 8
	sb.content_margin_bottom = 8
	guide_pill_panel.add_theme_stylebox_override("panel", sb)
	root_ctrl.add_child(guide_pill_panel)

	guide_pill_label = Label.new()
	guide_pill_label.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER
	guide_pill_label.vertical_alignment = VERTICAL_ALIGNMENT_CENTER
	var f: Font = load("res://art/fonts/simhei.ttf") if ResourceLoader.exists("res://art/fonts/simhei.ttf") else null
	if f:
		guide_pill_label.add_theme_font_override("font", f)
	guide_pill_label.add_theme_font_size_override("font_size", 16)
	guide_pill_label.add_theme_color_override("font_color", Color(0.96, 0.90, 0.76))
	guide_pill_panel.add_child(guide_pill_label)

	_update_camera_guide_hud()


func _update_camera_guide_hud() -> void:
	if guide_pill_panel == null or guide_pill_label == null:
		return
	if not has_camera:
		guide_pill_panel.visible = false
		return
	guide_pill_panel.visible = true
	if not camera_raised:
		guide_pill_label.text = "📷  按 [F] 举起大画幅相机取景（对准肖像点左键亦可举起）"
	else:
		match rules.data.plate:
			"LOADED2":
				guide_pill_label.text = "📷  按 [F] 放下相机  ·  [R] 二次曝光拨杆  ·  [触控板/滚轮/↑↓] 调焦  ·  [左键/空格] 快门拍摄"
			"ARMED":
				guide_pill_label.text = "📷  按 [F] 放下相机  ·  已拨杆就绪  ·  [触控板/滚轮/↑↓] 调焦  ·  [左键/空格] 二次曝光拍摄"
			"EXPOSED", "EXPOSED2":
				guide_pill_label.text = "📷  底片已曝光  ·  按 [F] 放下相机，前往显影盘显影"
			"DEVELOPED":
				guide_pill_label.text = "📷  底片已显影  ·  按 [F] 放下相机，回记录本与片夹重装"
			_:
				guide_pill_label.text = "📷  按 [F] 放下相机  ·  [触控板/滚轮/↑↓] 调焦  ·  [左键/空格] 快门拍摄"
	_update_camera_hud_label()


func _update_camera_hud_label() -> void:
	if camera_hud_label == null:
		return
	match rules.data.plate:
		"LOADED2":
			camera_hud_label.text = "[举镜中] 触控板/滚轮/↑↓：调焦 · 左键/空格：快门 · R：二次曝光拨杆 · F：放下相机"
		"ARMED":
			camera_hud_label.text = "[举镜中] 拨杆已就位 · 触控板/滚轮/↑↓：调焦 · 左键/空格：二次曝光快门 · F：放下相机"
		"EXPOSED", "EXPOSED2":
			camera_hud_label.text = "[举镜中] 底片已曝光 · 请按 F 放下相机去显影盘显影"
		"DEVELOPED":
			camera_hud_label.text = "[举镜中] 底片已显影 · 请按 F 放下相机查看装片说明"
		_:
			camera_hud_label.text = "[举镜中] 触控板/滚轮/↑↓：调焦 · 左键/空格：快门 · F：放下相机"


# ---------------------------------------------------------------------------
# 输入与玩法循环
# ---------------------------------------------------------------------------

func _input(event: InputEvent) -> void:
	var d := _dir()
	if not d or d.world.room != self or not is_instance_valid(player) or not player.active or player.frozen or d.ui._busy():
		return
	# 先于玩家的普通左键检查处理快门；阅读/暂停交由原UI处理。
	if (event is InputEventKey or event is InputEventJoypadButton) and event.is_pressed() and not event.is_echo():
		if event.is_action_pressed("cellar_raise"):
			_toggle_camera_raise()
			get_viewport().set_input_as_handled()
		elif event.is_action_pressed("cellar_arm") and has_camera and _gameplay_active:
			_handle_arm_second_exposure()
			get_viewport().set_input_as_handled()
		elif event.is_action_pressed("cellar_shutter") and camera_raised:
			_update_aim_detection()
			_trigger_shutter()
			get_viewport().set_input_as_handled()
		elif (event.is_action_pressed("cellar_focus_up") or (camera_raised and event is InputEventKey and event.keycode == KEY_UP)) and camera_raised:
			_step_focus(0.08)
			get_viewport().set_input_as_handled()
		elif (event.is_action_pressed("cellar_focus_down") or (camera_raised and event is InputEventKey and event.keycode == KEY_DOWN)) and camera_raised:
			_step_focus(-0.08)
			get_viewport().set_input_as_handled()
	elif event is InputEventPanGesture and camera_raised:
		_step_focus(-event.delta.y * 0.12)
		get_viewport().set_input_as_handled()
	elif event is InputEventMagnifyGesture and camera_raised:
		_step_focus((event.factor - 1.0) * 0.8)
		get_viewport().set_input_as_handled()
	elif event is InputEventMouseButton and event.pressed:
		if camera_raised:
			_update_aim_detection()
			match event.button_index:
				MOUSE_BUTTON_WHEEL_UP:
					_step_focus(0.08)
					get_viewport().set_input_as_handled()
				MOUSE_BUTTON_WHEEL_DOWN:
					_step_focus(-0.08)
					get_viewport().set_input_as_handled()
				MOUSE_BUTTON_LEFT:
					_trigger_shutter()
					get_viewport().set_input_as_handled()
		elif has_camera and event.button_index == MOUSE_BUTTON_LEFT:
			if is_instance_valid(player) and player._hover == "hs_cellar_portraits":
				_toggle_camera_raise()
				get_viewport().set_input_as_handled()


func _toggle_camera_raise() -> void:
	if not has_camera:
		_toast("得先在桌上拿起大画幅相机。")
		return
	if not camera_raised and player_cam:
		_rest_fov = player_cam.fov
	camera_raised = not camera_raised
	_play_sfx("cloth_rustle")
	if viewmodel:
		viewmodel.visible = camera_raised
	if camera_overlay:
		camera_overlay.visible = camera_raised
	if camera_only_node:
		camera_only_node.visible = camera_raised
	if player_cam:
		player_cam.fov = 48.0 if camera_raised else _rest_fov

	for y in frame_mats:
		frame_mats[y].set_shader_parameter("camera_mix", 1.0 if camera_raised else 0.0)
	_set_cinematic(camera_raised)
	_update_camera_guide_hud()
	_sync()
	if camera_raised:
		if is_instance_valid(focus_ring):
			focus_ring.set_focus(focus, true)
		_update_aim_detection()
		_hint("举镜中 · 触控板/滚轮/↑↓调焦 · 左键/空格快门 · F 放下")
	else:
		_hint("")


func _step_focus(delta: float) -> void:
	focus = clampf(focus + delta, 0.0, 1.0)
	if is_instance_valid(focus_ring):
		focus_ring.set_focus(focus, true)
	if current_aim_year > 0 and frame_mats.has(current_aim_year):
		frame_mats[current_aim_year].set_shader_parameter("focus", focus)
	_aim_toast_timer = 0.0
	_update_aim_hud()


func _process(dt: float) -> void:
	if _aim_toast_timer > 0.0:
		_aim_toast_timer -= dt
	var d := _dir()
	var shown: bool = camera_raised and d != null and not d.ui._busy() and is_instance_valid(player) and not player.frozen
	if camera_overlay:
		camera_overlay.visible = shown
	if viewmodel:
		viewmodel.visible = shown
	if guide_pill_panel:
		guide_pill_panel.visible = has_camera and d != null and not d.ui._busy()
	if not shown or player_cam == null:
		return
	_update_aim_detection()


func _update_aim_detection() -> void:
	# 从相机射向世界，判断是否正对着北墙肖像相框
	var origin: Vector3 = player_cam.global_position
	var fwd: Vector3 = -player_cam.global_transform.basis.z
	var detected_year := 0

	# 北墙平面位于 z = -3.92 左右
	if fwd.z < -0.2:
		var t: float = (-3.92 - origin.z) / fwd.z
		if t > 0.0 and t < 8.0:
			var hit_x: float = origin.x + fwd.x * t
			var hit_y: float = origin.y + fwd.y * t
			if absf(hit_y - 1.94) < 0.75:
				var coords := {
					1919: -2.45, 1920: -1.82, 1921: -1.18, 1922: -0.55,
					1923: 0.1, 1924: 0.74, 1925: 1.38, 1926: 2.02
				}
				var best_d := 0.38
				for y in coords:
					var dx: float = absf(hit_x - coords[y])
					if dx < best_d:
						best_d = dx
						detected_year = y

	if detected_year != current_aim_year:
		current_aim_year = detected_year
		if current_aim_year > 0 and frame_mats.has(current_aim_year):
			frame_mats[current_aim_year].set_shader_parameter("focus", focus)
	_update_aim_hud()


func _update_aim_hud() -> void:
	if not camera_raised or aim_target_label == null:
		return
	if _aim_toast_timer > 0.0:
		return
	if current_aim_year == 0:
		aim_target_label.text = "对准北墙相框，或观察暗处虚影"
		aim_target_label.modulate = Color(0.8, 0.8, 0.8, 0.6)
		return

	var info: Dictionary = frame_info.get(current_aim_year, {})
	var is_sharp := focus >= 0.88
	var year_title: String = "【%d 年合影】" % current_aim_year
	if cleared_years.has(current_aim_year):
		aim_target_label.text = "%s 过去记录中的空位 · 已对照" % year_title
		aim_target_label.modulate = Color(0.6, 0.7, 0.8, 0.9)
	elif not info.get("haunted", false):
		aim_target_label.text = "%s 正常 · 无多余人影" % year_title
		aim_target_label.modulate = Color(0.8, 0.8, 0.8, 0.8)
	else:
		var name_str: String = info.get("name", "")
		var focus_pct: int = int(round(focus * 100))
		var status_str := "清晰（%d%%）· 可按左键/空格快门" % focus_pct if is_sharp else "模糊（当前%d%%/需88%%·滑触控板/滚轮/按↑↓调焦）" % focus_pct
		aim_target_label.text = "%s 发现旧影（%s） · %s" % [year_title, name_str, status_str]
		aim_target_label.modulate = Color(1.0, 0.82, 0.3) if is_sharp else Color(1.0, 0.55, 0.4)


func _trigger_shutter() -> void:
	var result: String = rules.shutter(current_aim_year, focus >= 0.88)
	if result in ["first_shutter", "second_shutter", "final_first", "final_observed"]:
		_play_sfx("shutter_old")
		_play_flash()
	else:
		_play_sfx("click_clean")
		if result == "focus":
			var pct: int = int(round(focus * 100))
			_toast("⚠️ 影像尚未调焦清晰（当前 %d%%，需 88%% 以上）！请滑动触控板/滚轮或按↑/↓调焦" % pct)
			return
		elif result == "aim":
			_toast("⚠️ 请将中央取景十字对准北墙上的相框再按快门")
			return
	_apply(result)

func _handle_arm_second_exposure() -> void:
	var result: String = rules.arm()
	if result == "armed":
		_play_sfx("bolt_slide")
	else:
		_play_sfx("cloth_rustle")
	_apply(result)


func _play_flash() -> void:
	if flash_rect == null:
		return
	flash_rect.color = Color(1.0, 0.95, 0.85, 0.85)
	var tween := create_tween()
	tween.tween_property(flash_rect, "color:a", 0.0, 0.35)


# ---------------------------------------------------------------------------
# 热点交互响应
# ---------------------------------------------------------------------------

func _on_director_inspected(id: String) -> void:
	if id == "__cancel__":
		_finish(false)
		return
	if not _gameplay_active or _interaction_busy or not rules.target_ids().has(id): return
	match id:
		"hs_cellar_camera": _apply(rules.pickup())
		"hs_cellar_holder":
			if camera_raised: _toast(_text("lower"))
			else: _apply(rules.holder())
		"hs_cellar_cabinet": _apply(rules.cabinet(camera_raised))
		"hs_cellar_plate":
			if camera_raised: _toast(_text("lower"))
			else: _apply(rules.take_final())
		"hs_cellar_tray": _handle_tray_interaction()
		"hs_cellar_portraits":
			if camera_raised and current_aim_year == 1926:
				_apply(rules.observe_final(true))
			else:
				await _show_document(id, "portraits")
		"hs_cellar_book": await _show_document(id, "book")
		"hs_cellar_notes": await _show_document(id, "notes")
		"hs_cellar_clip": await _show_document(id, "clip")
		"hs_cellar_relics": await _show_document(id, "relics")
		"hs_cellar_ladder":
			_toast(_text("leave_done" if rules.data.complete else "leave_early"))
			_finish(rules.data.complete)

func _show_document(id: String, document: String) -> void:
	if camera_raised: _toggle_camera_raise()
	_interaction_busy = true
	if document == "book":
		rules.data.book_opened = true
		_save_progress()
	var d := _dir()
	var info: Dictionary = preload("res://ui/inspection_catalog.gd").hotspot(id, d.world)
	if document != "book":
		info["pages"] = [texts[document].title + "\n\n" + _text(document)]
		info["on_page_read"] = func(_index):
			rules.read_document(document)
			_save_progress()
	var target: Node3D = d.world.hotspot_nodes[id]
	d.ui.inspector.open(info, info.sources, target.global_position, [d.ui.objective_label, d.ui.checklist_box, d.ui.progress_label, d.ui.crosshair, d.ui.hint_box, d.ui.day_label, d.ui.room_label, d.ui.keys])
	await d.ui.inspector.closed
	if not is_inside_tree(): return
	if document != "book":
		rules.read_document(document)
	if not GameState.inspected.has(id): GameState.inspected.append(id)
	var evidence: String = ContentDB.hotspots.get(id, {}).get("evidence", "")
	if evidence != "": d._collect(evidence)
	_interaction_busy = false
	_save_progress()
	_sync()

func _handle_tray_interaction() -> void:
	if camera_raised:
		_toast(_text("lower"))
		return
	var result: String = rules.develop()
	if result in ["first_developed", "history_revealed"]: _play_sfx("liquid")
	_apply(result)


func guide_targets() -> Array:
	if not _gameplay_active: return []
	var targets := {
		"pickup": "camera", "first": "portraits", "tray": "tray",
		"read_reload": "book", "holder": "holder", "arm": "holder", "second": "portraits",
		"find_key": "cabinet", "read_key": "book", "open_box": "cabinet",
		"view_final": "portraits", "take_final": "plate", "choose_final": "cabinet",
		"final_shoot": "portraits", "read_history": "book", "read_notes": "notes",
		"read_clip": "clip", "read_relics": "relics", "leave": "ladder"
	}
	return ["hs_cellar_" + targets.get(rules.next_step(), "ladder")]
