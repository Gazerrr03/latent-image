extends SceneTree

var le: LineEdit
var handled_in_input := true

func _initialize():
	call_deferred("_setup")

func _setup():
	var layer = CanvasLayer.new()
	root.add_child(layer)

	var tester = Node.new()
	tester.set_script(load("res://tools/interceptor.gd"))
	layer.add_child(tester)

	le = LineEdit.new()
	layer.add_child(le)
	le.grab_focus()
	tester.le = le

	call_deferred("_send_key")

func _send_key():
	var ev = InputEventKey.new()
	ev.pressed = true
	ev.keycode = KEY_SPACE
	ev.unicode = 32
	root.push_input(ev)

	await process_frame
	await process_frame
	print("LineEdit 接收到的文本: '", le.text, "'")
	quit(0)
