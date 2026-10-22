extends SceneTree
## Check the existing ambient loop keeps the same player, gain, and advancing playback during inspection.
var failures:=0
func _initialize():call_deferred("run")
func check(label:String,ok:bool):
	print("PASS " if ok else "FAIL ",label)
	if not ok:failures+=1
func key(code:Key):
	var e:=InputEventKey.new();e.keycode=code;e.physical_keycode=code;e.pressed=true;root.push_input(e,true)
	e=e.duplicate();e.pressed=false;root.push_input(e,true)
func advance(from:float,to:float,length:float)->float:return fposmod(to-from,length)
func run():
	root.get_node("GameState").persist=false
	var main=load("res://main.tscn").instantiate();root.add_child(main);await process_frame
	root.get_node("GameState").reset()
	create_timer(60).timeout.connect(func():printerr("AMBIENT timeout");quit(2))
	var director=root.get_node("Director");var host=director.world;var ui=director.ui;var viewer=ui.inspector
	ui.menus.hide();ui.eyelids_set(1.0);ui.set_cinematic(false)
	host.show_scene("guest_room");host.set_mode("walk","");host.play_sound("clock_tick")
	await create_timer(.3).timeout
	var ambient:AudioStreamPlayer=host._loops.get("clock_tick")
	check("使用项目原环境循环音轨",ambient!=null and ambient.playing and ambient.stream.resource_path.ends_with("clock_tick.ogg"))
	if ambient==null:quit(1);return
	var instance:int=ambient.get_instance_id();var gain:float=ambient.volume_db;var bus:String=ambient.bus
	var muted:bool=AudioServer.is_bus_mute(AudioServer.get_bus_index(bus))
	var length:float=ambient.stream.get_length()
	for id in ["hs_notebook","hs_drawer"]:
		var before:float=ambient.get_playback_position()
		ui.inspect_hotspot(id);await create_timer(.5).timeout
		check(id+"检视冻结角色但不暂停场景",viewer.active and host.player.frozen and not paused)
		check(id+"保留同一环境播放器且未暂停",ambient.get_instance_id()==instance and ambient.playing and not ambient.stream_paused)
		check(id+"环境音播放位置继续前进",advance(before,ambient.get_playback_position(),length)>.15)
		check(id+"环境音增益和总线静音状态不被改写",is_equal_approx(ambient.volume_db,gain) and ambient.bus==bus and AudioServer.is_bus_mute(AudioServer.get_bus_index(bus))==muted)
		before=ambient.get_playback_position();key(KEY_F);await create_timer(.4).timeout
		check(id+"文字阅读期间环境音继续",viewer.reading and ambient.playing and not ambient.stream_paused and advance(before,ambient.get_playback_position(),length)>.15)
		key(KEY_ESCAPE);key(KEY_ESCAPE);await create_timer(.3).timeout
		check(id+"退出恢复行动且保留环境声",not viewer.active and not host.player.frozen and ambient.playing and not ambient.stream_paused)
	print("INSPECTION_AMBIENT failures=",failures)
	main.queue_free();await process_frame;quit(0 if failures==0 else 1)
