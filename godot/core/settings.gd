extends Node
## 设置：音量、鼠标、文字速度、亮度、窗口。存在 user://settings.cfg，标题页与暂停页共用（docs/06 第 8 节）。
## 音量分三条总线：Master、Music（res://audio/music/ 下的配乐）、SFX（其余声音）；
## 声音节点加进场景树时按它的文件自动分到对应总线，播放声音的代码不用改。

signal changed

const PATH := "user://settings.cfg"
## 档位都是 0—10；灵敏度与亮度 5 档 = 原样
const STEPS := 10

var master := 10
var music := 10
var sfx := 10
var sens := 5
var invert_y := false
## 文字速度：false = 逐字，true = 直接显示
var text_instant := false
var brightness := 5
var fullscreen := false


func _ready() -> void:
	for b in ["Music", "SFX"]:
		if AudioServer.get_bus_index(b) < 0:
			AudioServer.add_bus()
			AudioServer.set_bus_name(AudioServer.bus_count - 1, b)
			AudioServer.set_bus_send(AudioServer.bus_count - 1, "Master")
	get_tree().node_added.connect(_on_node_added)
	load_cfg()
	apply()


func load_cfg() -> void:
	var c := ConfigFile.new()
	if c.load(PATH) != OK:
		return
	master = int(c.get_value("audio", "master", master))
	music = int(c.get_value("audio", "music", music))
	sfx = int(c.get_value("audio", "sfx", sfx))
	sens = int(c.get_value("input", "sens", sens))
	invert_y = bool(c.get_value("input", "invert_y", invert_y))
	text_instant = bool(c.get_value("text", "instant", text_instant))
	brightness = int(c.get_value("video", "brightness", brightness))
	fullscreen = bool(c.get_value("video", "fullscreen", fullscreen))


func save_cfg() -> void:
	var c := ConfigFile.new()
	c.set_value("audio", "master", master)
	c.set_value("audio", "music", music)
	c.set_value("audio", "sfx", sfx)
	c.set_value("input", "sens", sens)
	c.set_value("input", "invert_y", invert_y)
	c.set_value("text", "instant", text_instant)
	c.set_value("video", "brightness", brightness)
	c.set_value("video", "fullscreen", fullscreen)
	c.save(PATH)


## 改一项：限定范围、立刻生效、写盘
func set_value(key: String, v) -> void:
	if typeof(get(key)) == TYPE_INT:
		v = clampi(int(v), 1 if key in ["sens", "brightness"] else 0, STEPS)
	set(key, v)
	apply()
	save_cfg()


func apply() -> void:
	_set_bus("Master", master)
	_set_bus("Music", music)
	_set_bus("SFX", sfx)
	# 截图、自动测试、无界面时不动窗口
	var args: Array = Array(OS.get_cmdline_user_args())
	if DisplayServer.get_name() != "headless" and not args.has("--autoplay") and not args.any(func(a): return a.begins_with("--capture=")):
		var want := DisplayServer.WINDOW_MODE_FULLSCREEN if fullscreen else DisplayServer.WINDOW_MODE_WINDOWED
		if DisplayServer.window_get_mode() != want:
			DisplayServer.window_set_mode(want)
	changed.emit()


## 鼠标转动的倍数：0.2—2.0
func mouse_scale() -> float:
	return sens / 5.0


## 亮度：画面的 gamma，0.68—1.4
func gamma() -> float:
	return 0.6 + brightness * 0.08


func _set_bus(bus: String, v: int) -> void:
	var i := AudioServer.get_bus_index(bus)
	if i < 0:
		return
	AudioServer.set_bus_mute(i, v <= 0)
	AudioServer.set_bus_volume_db(i, linear_to_db(v / float(STEPS)) if v > 0 else -80.0)


func _on_node_added(n: Node) -> void:
	if n is AudioStreamPlayer and n.bus == "Master":
		var s: AudioStream = n.stream
		n.bus = "Music" if s and s.resource_path.contains("/audio/music/") else "SFX"
