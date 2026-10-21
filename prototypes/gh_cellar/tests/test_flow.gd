extends SceneTree
## 纯状态流程测试：第 4 页装片门槛、第 7 页钥匙、1926 实体底片双结局。

const STATE := preload("res://systems/cellar_state.gd")

var ok := true


func _initialize() -> void:
	var text := FileAccess.get_file_as_string("res://data/cellar_content.json")
	var data = JSON.parse_string(text)
	var s = STATE.new(data)
	_check(s.has_camera == false, "starts without camera")
	_check(not s.raise_camera(), "cannot raise before pickup")
	_check(s.pickup_camera(), "pick camera")
	s.raise_camera()
	s.set_target("frame_1920", "frame", 1920)
	for i in 12:
		s.focus_step(1.0)
	_check(s.focus > 0.88, "focus reaches clear")
	_check(s.shutter() == "first", "first shutter")
	_check(s.plate_state == "EXPOSED", "plate exposed")
	s.lower_camera()
	_check(s.develop() == "first", "first development")
	_check(s.plate_state == "DEVELOPED", "plate developed")
	_check(not s.page4_read, "page 4 not read yet")
	_check(s.inspect_holder(false) == "need_notebook", "holder stuck before page 4")
	_check(not s.reload_plate(), "cannot reload before page 4")
	_check(not s.arm_second(), "cannot arm before page 4")
	s.mark_notebook_opened()
	_check(s.mark_page_read("second"), "page 4 read")
	_check(s.page4_read, "page 4 flag")
	_check(s.reload_plate(), "reload after page 4")
	_check(s.arm_second(), "arm after page 4")
	s.raise_camera()
	s.set_target("frame_1920", "frame", 1920)
	for i in 12:
		s.focus_step(1.0)
	_check(s.shutter() == "second", "second shutter")
	s.lower_camera()
	_check(s.develop() == "second", "second development")
	_check(s.cleared.has("1920"), "1920 cleared")

	s.raise_camera()
	s.set_target("", "", 0)
	_check(s.inspect_cabinet(true) == "key", "key ghost after 1920")
	_check(not s.has_key, "ghost does not give key")
	s.lower_camera()
	_check(s.inspect_cabinet(false) == "locked", "cabinet locked without key")
	s.mark_page_read("key")
	_check(s.has_key, "page 7 gives key")
	_check(s.inspect_cabinet(false) == "open", "key opens cabinet")
	_check(s.inspect_frame(1926, true) == "owner", "owner reflection")
	_check(s.take_1926_plate(), "take 1926 plate")
	_check(s.return_1926_plate(), "return 1926 plate")
	_check(s.final_choice == "keep", "keep ending")
	_check(s.is_ending(), "keep ending recorded")

	# fresh state for the shoot ending
	var s2 = STATE.new(data)
	s2.pickup_camera()
	s2.cleared["1920"] = true
	s2.camera_raised = true
	s2.inspect_cabinet(true)
	s2.mark_page_read("key")
	s2.inspect_cabinet(false)
	s2.inspect_frame(1926, true)
	_check(s2.take_1926_plate(), "take plate for shoot")
	_check(s2.load_1926_plate(), "load plate into camera")
	s2.set_target("frame_1926", "frame", 1926)
	_check(s2.final_shutter() == "first", "final first shutter")
	_check(s2.final_shutter() == "second", "final second shutter")
	_check(s2.final_choice == "shoot", "shoot ending")

	print("TEST_FLOW ", "PASS" if ok else "FAIL")
	quit(0 if ok else 1)


func _check(cond: bool, label: String) -> void:
	print(("PASS  " if cond else "FAIL  ") + label)
	if not cond:
		ok = false
