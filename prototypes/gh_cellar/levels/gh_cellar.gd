extends Node3D
## 密室：空间 + 相机双视觉 + 1920 完整流程 + 1922/1924/1926 骨架。
const LAYOUT_PATH := "res://art/levels/gh_cellar/cellar_layout.json"
const CONTENT_PATH := "res://data/cellar_content.json"
const ANCHORS_PATH := "res://data/cellar_anchors.json"
const STATE_SCRIPT := preload("res://systems/cellar_state.gd")
const FRAME_SHADER := preload("res://shaders/frame_view.gdshader")

@onready var player: CharacterBody3D = $Player
@onready var collision: StaticBody3D = $Collision
@onready var lighting: Node3D = $Lighting
@onready var cellar_model: Node3D = $Art/CellarModel
@onready var ui: CanvasLayer = $CellarUI
@onready var interactables_root: Node3D = $Interactables
@onready var camera_only: Node3D = $CameraOnly
@onready var frame_labels: Node3D = $FrameLabels

var layout: Dictionary = {}
var content: Dictionary = {}
var anchors: Dictionary = {}
var state: RefCounted
var frame_views: Dictionary = {}
var interactables: Dictionary = {}
var camera_only_areas: Array[Area3D] = []
var current_id := ""
var current_kind := ""
var current_year := 0
var tag_prop: Node3D
var key_prop: Node3D
var plate_1926_prop: Node3D
var key_ghost_sprite: Sprite3D
var _sfx: AudioStreamPlayer
var _ambience: AudioStreamPlayer
var _red_hum: AudioStreamPlayer


func _ready() -> void:
	layout = _read_json(LAYOUT_PATH)
	content = _read_json(CONTENT_PATH)
	anchors = _read_json(ANCHORS_PATH)
	if layout.is_empty() or content.is_empty():
		push_error("CELLAR: missing layout/content json")
		return
	state = STATE_SCRIPT.new(content)
	_build_collision()
	_build_lights()
	_place_player()
	_configure_frames()
	_build_frame_labels()
	_build_interactables()
	_build_camera_only()
	_build_tag_prop()
	_build_key_prop()
	_build_plate_1926_prop()
	_build_audio()
	_connect_all()
	_refresh_all()
	ui.set_status("相机：尚未拿起")
	ui.set_plate("干版：—")
	ui.set_key(false)
	ui.say("一间旧地窖。桌上压着一本摊开的记录本。", 4.0)
	print("CELLAR READY meshes=", _count_meshes(cellar_model),
		" collision=", collision.get_child_count(),
		" lights=", lighting.get_child_count(),
		" frames=", frame_views.size(),
		" interactables=", interactables.size())


# ---------------------------------------------------------------------------
# load / build space
# ---------------------------------------------------------------------------

func _read_json(path: String) -> Dictionary:
	if not FileAccess.file_exists(path):
		return {}
	var data = JSON.parse_string(FileAccess.get_file_as_string(path))
	return data if typeof(data) == TYPE_DICTIONARY else {}


func _build_collision() -> void:
	for entry in layout.get("collision", []):
		var cs := CollisionShape3D.new()
		var box := BoxShape3D.new()
		var s: Array = entry.get("size", [1, 1, 1])
		box.size = Vector3(float(s[0]), float(s[1]), float(s[2]))
		cs.shape = box
		var c: Array = entry.get("center", [0, 0, 0])
		cs.position = Vector3(float(c[0]), float(c[1]), float(c[2]))
		cs.name = String(entry.get("name", "box"))
		collision.add_child(cs)


func _build_lights() -> void:
	for e in layout.get("lights", []):
		var kind := String(e.get("type", "omni"))
		var light: Light3D
		if kind == "spot":
			var spot := SpotLight3D.new()
			spot.spot_angle = deg_to_rad(float(e.get("spot_angle", 45.0)))
			spot.spot_range = float(e.get("range", 6.0))
			spot.rotation_degrees.x = -90.0
			light = spot
		else:
			var omni := OmniLight3D.new()
			omni.omni_range = float(e.get("range", 5.0))
			light = omni
		light.name = String(e.get("name", "light"))
		light.light_color = Color.from_string(String(e.get("color", "#ffffff")), Color.WHITE)
		light.light_energy = float(e.get("energy", 1.0))
		light.shadow_enabled = bool(e.get("shadow", false))
		var p: Array = e.get("position", [0, 2, 0])
		var pos := Vector3(float(p[0]), float(p[1]), float(p[2]))
		if kind == "spot":
			pos.y = minf(pos.y, 2.52)
		light.position = pos
		lighting.add_child(light)


func _place_player() -> void:
	var spawn: Dictionary = layout.get("spawn", {})
	var p: Array = spawn.get("position", [2.15, 0.05, -3.2])
	player.place(Vector3(float(p[0]), float(p[1]), float(p[2])), float(spawn.get("yaw", 0.0)))


func _count_meshes(root: Node) -> int:
	var n := 0
	for c in root.find_children("*", "MeshInstance3D", true, false):
		n += 1
	return n


# ---------------------------------------------------------------------------
# frames / materials
# ---------------------------------------------------------------------------

func _configure_frames() -> void:
	for i in 8:
		var year := 1919 + i
		var mesh := cellar_model.find_child("Portrait frame %d portrait" % i, true, false) as MeshInstance3D
		if mesh == null:
			push_warning("CELLAR: missing photo mesh for %d" % year)
			continue
		var mat := ShaderMaterial.new()
		mat.shader = FRAME_SHADER
		var base := "res://art/levels/gh_cellar/textures/frames/"
		mat.set_shader_parameter("normal_tex", load(base + "%d_normal.png" % year))
		mat.set_shader_parameter("lens_blur_tex", load(base + "%d_lens_blur.png" % year))
		mat.set_shader_parameter("lens_sharp_tex", load(base + "%d_lens_sharp.png" % year))
		mat.set_shader_parameter("empty_tex", load(base + "%d_empty.png" % year))
		mat.set_shader_parameter("camera_mix", 0.0)
		mat.set_shader_parameter("focus", 0.0)
		mat.set_shader_parameter("state", 0.0)
		mesh.material_override = mat
		frame_views[year] = {"mesh": mesh, "mat": mat}


func _build_frame_labels() -> void:
	var f = load("res://art/fonts/simhei.ttf")
	for fdata in layout.get("frames", []):
		var raw_year = fdata.get("year", 0)
		if raw_year == null:
			continue
		var year := int(raw_year)
		if year < 1919 or year > 1926:
			continue
		var label := Label3D.new()
		label.text = str(year)
		label.font = f
		label.font_size = 42
		label.pixel_size = 0.0026
		label.outline_size = 6
		label.modulate = Color(0.9, 0.82, 0.65, 0.78)
		label.outline_modulate = Color(0.04, 0.03, 0.02, 0.9)
		var p: Array = fdata.get("label_position", [0, 1.6, -3.9])
		label.position = Vector3(float(p[0]), float(p[1]), float(p[2]) + 0.01)
		label.billboard = BaseMaterial3D.BILLBOARD_DISABLED
		frame_labels.add_child(label)


# ---------------------------------------------------------------------------
# interactables / traces / pickup
# ---------------------------------------------------------------------------

func _area(id: String, pos: Vector3, size: Vector3, kind: String, year := 0, camera_only := false) -> Area3D:
	var a := Area3D.new()
	a.name = id
	a.position = pos
	a.collision_layer = 2 if not camera_only else 0
	a.collision_mask = 0
	a.monitoring = true
	a.monitorable = true
	a.set_meta("id", id)
	a.set_meta("kind", kind)
	a.set_meta("year", year)
	a.set_meta("camera_only", camera_only)
	var cs := CollisionShape3D.new()
	var box := BoxShape3D.new()
	box.size = size
	cs.shape = box
	a.add_child(cs)
	interactables_root.add_child(a)
	interactables[id] = a
	if camera_only:
		camera_only_areas.append(a)
	return a


func _build_interactables() -> void:
	for fdata in layout.get("frames", []):
		var raw_year = fdata.get("year", 0)
		if raw_year == null:
			continue
		var year := int(raw_year)
		if year < 1919 or year > 1926:
			continue
		var p: Array = fdata.get("position", [0, 1.9, -3.9])
		var n: Array = fdata.get("normal", [0, 0, 1])
		var pos := Vector3(float(p[0]), float(p[1]), float(p[2]))
		pos += Vector3(float(n[0]), float(n[1]), float(n[2])) * 0.055
		_area("frame_%d" % year, pos, Vector3(0.48, 0.62, 0.24), "frame", year)

	for id in ["pickup", "notebook", "tray", "holder", "cabinet", "plate_1926", "relics", "crate_plates", "ladder_print"]:
		var a: Dictionary = anchors.get(id, {})
		if a.is_empty():
			continue
		var p: Array = a.get("position", [0, 1, 0])
		var s: Array = a.get("size", [0.4, 0.4, 0.4])
		_area(id, Vector3(float(p[0]), float(p[1]), float(p[2])),
			Vector3(float(s[0]), float(s[1]), float(s[2])),
			String(a.get("kind", "misc")), 0, bool(a.get("required_camera", false)))


func _build_camera_only() -> void:
	camera_only.visible = false
	# relics: two faint silhouettes near the sink shelf
	for i in 2:
		var s := Sprite3D.new()
		s.texture = load("res://art/ui/silhouette.png")
		s.billboard = BaseMaterial3D.BILLBOARD_ENABLED
		s.pixel_size = 0.0055
		s.modulate = Color(1, 1, 1, 0.45 if i == 0 else 0.28)
		s.position = Vector3(-4.25 + i*0.25, 1.18, -1.95 - i*0.18)
		camera_only.add_child(s)
	# dry plates on the crate
	for i in 5:
		var plate := MeshInstance3D.new()
		var bm := BoxMesh.new()
		bm.size = Vector3(0.24, 0.008, 0.18)
		plate.mesh = bm
		var m := StandardMaterial3D.new()
		m.albedo_color = Color(0.55, 0.65, 0.62, 0.4)
		m.transparency = BaseMaterial3D.TRANSPARENCY_ALPHA
		m.emission_enabled = true
		m.emission = Color(0.45, 0.64, 0.62)
		m.emission_energy_multiplier = 1.5
		plate.material_override = m
		plate.position = Vector3(3.18, 0.78 + i*0.018, -1.73)
		plate.rotation_degrees.y = 14.0
		camera_only.add_child(plate)
	# footprint on the ladder
	var fp := Sprite3D.new()
	fp.texture = load("res://art/ui/footprint.png")
	fp.billboard = BaseMaterial3D.BILLBOARD_ENABLED
	fp.pixel_size = 0.0045
	fp.modulate = Color(1, 1, 1, 0.55)
	fp.position = Vector3(3.72, 0.92, -2.25)
	camera_only.add_child(fp)
	# white crystals in the developing tray
	for i in 9:
		var c := MeshInstance3D.new()
		var sm := SphereMesh.new()
		sm.radius = 0.012
		sm.height = 0.03
		c.mesh = sm
		var m := StandardMaterial3D.new()
		m.albedo_color = Color(0.8, 0.82, 0.74)
		m.emission_enabled = true
		m.emission = Color(0.6, 0.7, 0.66)
		m.emission_energy_multiplier = 2.2
		c.material_override = m
		var ang := TAU * i / 9.0
		c.position = Vector3(-4.50 + cos(ang)*0.15, 1.0, -0.90 + sin(ang)*0.12)
		camera_only.add_child(c)
	# key ghost at the film cabinet
	var key := Sprite3D.new()
	key.texture = load("res://art/ui/key_ghost.png")
	key.billboard = BaseMaterial3D.BILLBOARD_ENABLED
	key.pixel_size = 0.0028
	key.modulate = Color(1, 1, 1, 0.6)
	key.position = Vector3(-4.55, 0.95, 2.95)
	camera_only.add_child(key)
	key_ghost_sprite = key


func _build_tag_prop() -> void:
	tag_prop = Node3D.new()
	tag_prop.name = "CameraTag"
	tag_prop.position = Vector3(0.64, 1.34, -0.55)
	tag_prop.rotation_degrees = Vector3(0, 0, 0)
	add_child(tag_prop)
	var paper := MeshInstance3D.new()
	var bm := BoxMesh.new()
	bm.size = Vector3(0.32, 0.20, 0.012)
	paper.mesh = bm
	var pm := StandardMaterial3D.new()
	pm.albedo_color = Color(0.62, 0.54, 0.38)
	pm.roughness = 0.95
	paper.material_override = pm
	tag_prop.add_child(paper)
	var label := Label3D.new()
	label.text = "别相信照片\n先看本子"
	label.font = load("res://art/fonts/simhei.ttf")
	label.font_size = 30
	label.pixel_size = 0.004
	label.outline_size = 5
	label.outline_modulate = Color(0.15, 0.1, 0.05, 0.9)
	label.modulate = Color(0.18, 0.12, 0.06, 1)
	label.position = Vector3(0, 0, 0.008)
	label.billboard = BaseMaterial3D.BILLBOARD_ENABLED
	tag_prop.add_child(label)


func _build_key_prop() -> void:
	key_prop = Node3D.new()
	key_prop.name = "KeyProp"
	key_prop.position = Vector3(0.90, 0.94, -0.24)
	key_prop.rotation_degrees = Vector3(0, 22, 0)
	key_prop.visible = false
	add_child(key_prop)
	var mat := StandardMaterial3D.new()
	mat.albedo_color = Color(0.62, 0.44, 0.12)
	mat.metallic = 0.85
	mat.roughness = 0.3
	var shaft := MeshInstance3D.new()
	var sm := BoxMesh.new()
	sm.size = Vector3(0.14, 0.012, 0.018)
	shaft.mesh = sm
	shaft.material_override = mat
	key_prop.add_child(shaft)
	var head := MeshInstance3D.new()
	var hm := BoxMesh.new()
	hm.size = Vector3(0.04, 0.012, 0.05)
	head.mesh = hm
	head.position = Vector3(-0.08, 0, 0)
	head.material_override = mat
	key_prop.add_child(head)
	var tooth := MeshInstance3D.new()
	var tm := BoxMesh.new()
	tm.size = Vector3(0.025, 0.012, 0.035)
	tooth.mesh = tm
	tooth.position = Vector3(0.055, 0, 0.02)
	tooth.material_override = mat
	key_prop.add_child(tooth)


func _build_plate_1926_prop() -> void:
	var a: Dictionary = anchors.get("plate_1926", {})
	if a.is_empty():
		return
	var p: Array = a.get("position", [-4.15, 1.02, 2.85])
	plate_1926_prop = Node3D.new()
	plate_1926_prop.name = "Plate1926"
	plate_1926_prop.position = Vector3(float(p[0]), float(p[1]), float(p[2]))
	plate_1926_prop.visible = false
	add_child(plate_1926_prop)
	var plate := MeshInstance3D.new()
	var bm := BoxMesh.new()
	bm.size = Vector3(0.22, 0.012, 0.16)
	plate.mesh = bm
	var pm := StandardMaterial3D.new()
	pm.albedo_color = Color(0.12, 0.13, 0.12)
	pm.roughness = 0.45
	plate.material_override = pm
	plate_1926_prop.add_child(plate)
	var sleeve := MeshInstance3D.new()
	var sm := BoxMesh.new()
	sm.size = Vector3(0.24, 0.006, 0.18)
	sleeve.mesh = sm
	sleeve.position.y = 0.012
	var smat := StandardMaterial3D.new()
	smat.albedo_color = Color(0.55, 0.47, 0.32)
	smat.roughness = 0.9
	sleeve.material_override = smat
	plate_1926_prop.add_child(sleeve)


func _hide_table_camera() -> void:
	var anchor := Vector3(0.36, 1.15, -0.64)
	for n in cellar_model.find_children("Camera *", "MeshInstance3D", true, false):
		if n.global_position.distance_to(anchor) < 1.0:
			n.visible = false
	for n in cellar_model.find_children("Lens *", "MeshInstance3D", true, false):
		if n.global_position.distance_to(anchor) < 1.0:
			n.visible = false
	var safe := lighting.get_node_or_null("safelight")
	if safe:
		safe.visible = false


# ---------------------------------------------------------------------------
# audio
# ---------------------------------------------------------------------------

func _build_audio() -> void:
	if OS.has_feature("headless"):
		return
	_sfx = AudioStreamPlayer.new()
	_sfx.name = "SFX"
	add_child(_sfx)
	_ambience = AudioStreamPlayer.new()
	_ambience.name = "Ambience"
	add_child(_ambience)
	_red_hum = AudioStreamPlayer.new()
	_red_hum.name = "RedHum"
	add_child(_red_hum)
	_play_loop(_ambience, "res://audio/room_hum.ogg", -18.0)
	_play_loop(_red_hum, "res://audio/red_hum.ogg", -24.0)
	_red_hum.stream_paused = true


func _play_loop(p: AudioStreamPlayer, path: String, db: float) -> void:
	if not ResourceLoader.exists(path):
		return
	var s = load(path)
	if s is AudioStreamOggVorbis:
		s.loop = true
	p.stream = s
	p.volume_db = db
	p.play()


func _play_sfx(name: String) -> void:
	if _sfx == null:
		return
	var p := "res://audio/%s.ogg" % name
	if not ResourceLoader.exists(p):
		return
	_sfx.stream = load(p)
	_sfx.volume_db = -8.0
	_sfx.play()


# ---------------------------------------------------------------------------
# wiring
# ---------------------------------------------------------------------------

func _connect_all() -> void:
	state.narrate.connect(_on_narrate)
	state.frame_changed.connect(_on_frame_changed)
	state.notebook_unlocked.connect(_on_notebook_unlocked)
	state.ending_reached.connect(_on_ending)
	state.changed.connect(_on_state_changed)

	player.camera_toggle_requested.connect(_on_camera_toggle)
	player.interact_pressed.connect(_on_interact)
	player.shutter_pressed.connect(_on_shutter)
	player.focus_step_requested.connect(_on_focus_step)
	player.second_exposure_requested.connect(_on_second)
	player.notebook_requested.connect(_on_notebook)

	ui.notebook_closed.connect(_on_notebook_closed)
	ui.notebook_page_shown.connect(_on_notebook_page_shown)
	ui.restart_requested.connect(func(): get_tree().reload_current_scene())


func _on_state_changed() -> void:
	if state.has_camera and interactables.has("pickup"):
		interactables["pickup"].collision_layer = 0
	if tag_prop:
		tag_prop.visible = not state.has_camera
	if key_prop:
		key_prop.visible = state.key_taken
	if plate_1926_prop:
		var can_show_plate: bool = (state.box_open and state.owner_seen
			and not state.plate_1926_taken and not state.final_returned)
		plate_1926_prop.visible = can_show_plate
		if interactables.has("plate_1926"):
			interactables["plate_1926"].collision_layer = 2 if can_show_plate else 0
	if key_ghost_sprite:
		key_ghost_sprite.visible = (state.camera_raised and state.cleared.has("1920")
			and not state.key_taken)
	ui.set_key(state.has_key)
	_update_plate()
	_update_camera_materials()
	_update_target_ui()


func _on_narrate(text: String) -> void:
	ui.say(text, 5.0)


func _on_frame_changed(year: int, visual: String) -> void:
	var view = frame_views.get(year)
	if view:
		view.mat.set_shader_parameter("state", 1.0 if visual == "empty" else 0.0)
	ui.toast("相框空了。" if visual == "empty" else "")


func _on_notebook_unlocked(page_id: String) -> void:
	ui.toast("记录本有新的一页 · 回桌上翻")


func _on_notebook_page_shown(page_id: String) -> void:
	var just_read: bool = state.mark_page_read(page_id)
	if just_read:
		if page_id == "second":
			ui.toast("你看懂了装片和二次曝光")
			_update_target_ui()
		elif page_id == "key":
			ui.toast("钥匙从本子里滑出来")
			ui.set_key(true)
			if key_prop:
				key_prop.visible = true
			if key_ghost_sprite:
				key_ghost_sprite.visible = false
			_update_target_ui()


func _on_ending(choice: String) -> void:
	player.set_ui_locked(true)
	player.set_camera_mode(false)
	ui.set_camera_mode(false)
	var text := String(content.get("endings", {}).get(choice, ""))
	ui.show_ending(text)
	_play_sfx("page_turn")


# ---------------------------------------------------------------------------
# camera mode / focus / visuals
# ---------------------------------------------------------------------------

func _on_camera_toggle() -> void:
	if ui.is_overlay_open():
		return
	if not state.has_camera:
		ui.say(state.prompt("no_camera"), 2.5)
		return
	if state.camera_raised:
		state.lower_camera()
		player.set_camera_mode(false)
		ui.set_camera_mode(false)
		_set_camera_world(false)
		_play_sfx("cloth_rustle")
	else:
		state.raise_camera()
		player.set_camera_mode(true)
		ui.set_camera_mode(true)
		_set_camera_world(true)
		_play_sfx("cloth_rustle")
		ui.say("取景框边缘刻着：看清楚了，就得拍。", 3.2)
	_on_state_changed()


func _set_camera_world(on: bool) -> void:
	camera_only.visible = on
	for a in camera_only_areas:
		a.collision_layer = 2 if on else 0
	for year in frame_views:
		frame_views[year].mat.set_shader_parameter("camera_mix", 1.0 if on else 0.0)
	if _red_hum:
		_red_hum.stream_paused = not on


func _update_camera_materials() -> void:
	var mix := 1.0 if state.camera_raised else 0.0
	for year in frame_views:
		var view = frame_views[year]
		view.mat.set_shader_parameter("camera_mix", mix)
		view.mat.set_shader_parameter("focus", state.focus if year == current_year else 0.0)
	ui.set_focus(state.focus, state.camera_raised and current_kind == "frame")


func _on_focus_step(direction: float) -> void:
	if not state.camera_raised or current_kind != "frame":
		return
	state.focus_step(direction)


func _on_shutter() -> void:
	if ui.is_overlay_open():
		return
	if state.final_loaded:
		var final_result: String = state.final_shutter()
		if final_result == "first":
			_play_sfx("shutter_old")
			ui.flash(Color(1.0, 0.9, 0.72, 0.5))
		elif final_result == "second":
			_play_sfx("shutter_old")
			ui.flash(Color(0.0, 0.0, 0.0, 0.9))
		_on_state_changed()
		return
	var result: String = state.shutter()
	if result == "first" or result == "second":
		_play_sfx("shutter_old")
		ui.flash(Color(1.0, 0.9, 0.72, 0.5))
	_on_state_changed()


func _on_second() -> void:
	if ui.is_overlay_open():
		return
	if state.arm_second():
		_play_sfx("bolt_slide")
	_on_state_changed()


# ---------------------------------------------------------------------------
# interaction
# ---------------------------------------------------------------------------

func _on_interact() -> void:
	if ui.is_overlay_open():
		return
	var a: Area3D = player.get_target_area()
	if a == null:
		return
	var id := String(a.get_meta("id", ""))
	var kind := String(a.get_meta("kind", ""))
	var year := int(a.get_meta("year", 0))

	match kind:
		"pickup":
			if state.pickup_camera():
				player.set_has_camera(true)
				_hide_table_camera()
				if tag_prop:
					tag_prop.visible = false
				a.collision_layer = 0
				_play_sfx("camera_case")
				ui.toast("拿起相机。记录本就在下面。")
		"notebook":
			_open_notebook(true)
		"frame":
			var res: String = state.inspect_frame(year, state.camera_raised)
			if res == "owner":
				ui.set_owner_visible(true)
		"tray":
			var res2: String = state.inspect_tray(state.camera_raised)
			if res2 == "first" or res2 == "second":
				_play_sfx("liquid")
				ui.flash(Color(0.3, 0.1, 0.05, 0.25))
			elif res2 == "crystals":
				ui.toast("取景框里，盘底亮了")
			elif res2 == "need_lower":
				ui.toast("先放下相机")
		"holder":
			if state.plate_1926_taken and not state.final_loaded:
				if state.camera_raised:
					ui.toast("先放下相机")
				elif state.load_1926_plate():
					_play_sfx("drawer")
					ui.toast("1926 底片装进相机。F 举镜拍两次。")
			elif state.final_loaded:
				ui.toast("按 F 举镜，对准 1926 拍两次")
			elif state.plate_state == "DEVELOPED" and not state.camera_raised:
				if not state.page4_read:
					state.inspect_holder(false)
					ui.toast("卡住了。先翻记录本第四页")
				elif state.reload_plate():
					_play_sfx("drawer")
					ui.toast("干版已装回。按 R 拨二次曝光。")
			elif state.plate_state == "NONE" and state.cleared.size() > 0 and not state.camera_raised:
				if state.reload_plate():
					_play_sfx("drawer")
					ui.toast("换了一张新的干版。")
			else:
				state.inspect_holder(state.camera_raised)
				_play_sfx("drawer")
		"cabinet":
			if state.plate_1926_taken and not state.final_loaded and not state.final_returned:
				if state.camera_raised:
					ui.toast("先放下相机")
				elif state.return_1926_plate():
					_play_sfx("drawer")
			else:
				var res3: String = state.inspect_cabinet(state.camera_raised)
				if res3 == "key":
					ui.toast("记录本有新的一页。先翻第七页。")
				elif res3 == "open":
					_play_sfx("drawer")
					ui.toast("盒底有一张 1926 底片。")
				elif res3 == "locked":
					_play_sfx("door_knock")
		"plate":
			if state.camera_raised:
				ui.toast("先放下相机")
			elif state.take_1926_plate():
				_play_sfx("drawer")
				if plate_1926_prop:
					plate_1926_prop.visible = false
				ui.toast("拿到 1926 底片")
			elif not state.owner_seen:
				ui.toast("先举镜看她一眼")
		"trace":
			state.inspect_trace(_trace_key(id))
		_:
			pass
	_on_state_changed()


func _trace_key(id: String) -> String:
	match id:
		"relics":
			return "relics"
		"crate_plates":
			return "crate_plates"
		"ladder_print":
			return "ladder_print"
		"tray":
			return "crystals"
	return id


# ---------------------------------------------------------------------------
# notebook / final / ending
# ---------------------------------------------------------------------------

func _on_notebook() -> void:
	if ui.is_overlay_open():
		return
	if not state.notebook_opened_once:
		ui.say("先到桌上翻记录本。", 2.6)
		return
	_open_notebook(false)


func _open_notebook(first_read: bool) -> void:
	var pages: Array = state.notebook_pages()
	if pages.is_empty():
		return
	var start := 0 if first_read else pages.size() - 1
	ui.open_notebook(pages, start)
	player.set_ui_locked(true)
	if first_read:
		state.mark_notebook_opened()
	_play_sfx("page_turn")


func _on_notebook_closed() -> void:
	player.set_ui_locked(false)


func _input(event: InputEvent) -> void:
	if not (ui and ui.notebook_is_open()):
		return
	if event is InputEventKey and event.pressed and not event.echo:
		match event.keycode:
			KEY_TAB, KEY_ESCAPE:
				ui.close_notebook()
				get_viewport().set_input_as_handled()
			KEY_D, KEY_RIGHT, KEY_PAGEDOWN:
				ui.notebook_next()
				get_viewport().set_input_as_handled()
			KEY_A, KEY_LEFT, KEY_PAGEUP:
				ui.notebook_prev()
				get_viewport().set_input_as_handled()
	elif event is InputEventMouseButton and event.pressed:
		if event.button_index == MOUSE_BUTTON_WHEEL_DOWN:
			ui.notebook_next()
			get_viewport().set_input_as_handled()
		elif event.button_index == MOUSE_BUTTON_WHEEL_UP:
			ui.notebook_prev()
			get_viewport().set_input_as_handled()


func _unhandled_input(event: InputEvent) -> void:
	if ui.notebook_is_open() and event is InputEventKey and event.pressed and not event.echo:
		if event.keycode == KEY_TAB or event.keycode == KEY_ESCAPE:
			ui.close_notebook()
			get_viewport().set_input_as_handled()


# ---------------------------------------------------------------------------
# target / UI loop
# ---------------------------------------------------------------------------

func _process(_dt: float) -> void:
	if state == null or not is_instance_valid(player):
		return
	if ui.is_overlay_open():
		return
	var a: Area3D = player.get_target_area()
	var id := ""
	var kind := ""
	var year := 0
	if a:
		id = String(a.get_meta("id", ""))
		kind = String(a.get_meta("kind", ""))
		year = int(a.get_meta("year", 0))
	if id == "pickup" and state.has_camera:
		id = ""
		kind = ""
		year = 0
	if id != current_id:
		current_id = id
		current_kind = kind
		current_year = year
		if id == "":
			state.clear_target()
		else:
			state.set_target(id, kind, year)
	_update_prompt()
	_update_target_ui()
	if state.camera_raised and year == 1926 and state.box_open:
		ui.set_owner_visible(true)
		if not state.owner_seen:
			state.inspect_frame(1926, true)
	else:
		ui.set_owner_visible(false)


func _update_prompt() -> void:
	if current_id == "":
		ui.set_prompt("")
		return
	var txt := ""
	match current_kind:
		"pickup":
			txt = state.prompt("pickup")
		"notebook":
			txt = "E　翻记录本"
		"frame":
			txt = "滚轮对焦  ·  左键快门" if state.camera_raised else "E　查看相框"
		"tray":
			if state.camera_raised:
				txt = "E　看显影盘底" if not state.crystals_seen else "先放下相机"
			else:
				txt = "E　显影"
		"holder":
			if state.plate_1926_taken and not state.final_loaded:
				txt = "E　装上 1926 底片"
			elif state.final_loaded:
				txt = "F　举镜，拍两次"
			elif state.plate_state == "DEVELOPED" and not state.camera_raised:
				txt = "E　装回干版" if state.page4_read else "E　片夹卡住了"
			elif state.plate_state == "NONE" and state.cleared.size() > 0 and not state.camera_raised:
				txt = "E　换一张干版"
			elif state.camera_raised:
				txt = "E　看片夹凹槽"
			else:
				txt = "E　推片夹"
		"cabinet":
			if state.plate_1926_taken and not state.final_loaded and not state.final_returned:
				txt = "E　放回 1926 底片"
			elif state.box_open:
				txt = "E　看底片盒"
			elif state.has_key:
				txt = "E　开底片盒"
			else:
				txt = "E　看柜子"
		"plate":
				txt = "E　拿 1926 底片"
		"trace":
			txt = "E　细看"
	ui.set_prompt(txt)


func _update_target_ui() -> void:
	if current_kind == "frame" and state.camera_raised:
		ui.set_target(current_year, state.year_name(current_year))
	else:
		ui.set_target(0, "")
	ui.set_plate(_plate_text())
	ui.set_key(state.has_key)
	if state.camera_raised:
		ui.set_status("取景模式")
	else:
		ui.set_status("相机：" + ("已拿起" if state.has_camera else "尚未拿起"))
	ui.set_focus(state.focus, state.camera_raised and current_kind == "frame")


func _update_plate() -> void:
	if ui == null:
		return
	ui.set_plate(_plate_text())


func _plate_text() -> String:
	if state.final_loaded:
		return "1926 底片：已装"
	if state.plate_1926_taken:
		return "1926 底片：在手上"
	match state.plate_state:
		"LOADED": return "干版：已装"
		"EXPOSED": return "干版：第一次曝光"
		"DEVELOPED": return "干版：已显影"
		"LOADED2": return "干版：已装回"
		"ARMED": return "二次曝光：待拍"
		"EXPOSED2": return "干版：第二次曝光"
		"FINAL": return "1926 底片：已装"
		"NONE": return "干版：—"
	return ""


func _refresh_all() -> void:
	_update_camera_materials()
	_update_plate()
	_update_target_ui()
	for year in frame_views:
		frame_views[year].mat.set_shader_parameter("state", 1.0 if state.cleared.has(str(year)) else 0.0)
	_on_state_changed()

