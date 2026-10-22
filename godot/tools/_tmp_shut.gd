extends SceneTree
func _initialize():
	call_deferred("run")
func run():
	var main = load("res://main.tscn").instantiate()
	root.add_child(main)
	await create_timer(7.0).timeout
	var host = root.get_node("Director").world
	var pl = host.player
	print("GROUP ", get_nodes_in_group("door_line").map(func(b): return b.get_meta("door_line")))
	for spot in [["正门", Vector3(9.6, 0.02, -1.2), 180.0, 5.0], ["暗房门", Vector3(17.15, 3.62, -6.5), 0.0, -5.0], ["后门", Vector3(11.95, 3.62, -10.2), 0.0, -5.0], ["温室北门", Vector3(22.2, 3.6, -14.6), 180.0, -5.0]]:
		pl.place(spot[1], spot[2])
		pl._pitch = deg_to_rad(spot[3]); pl.cam.rotation.x = pl._pitch
		await create_timer(0.6).timeout
		pl._update_hover()
		var shut = pl._shut
		print("SPOT ", spot[0], " shut=", shut != null, " door=", pl._door != null, " hint=", root.get_node("Director").ui.hint_label.text, " line=", host.door_line(shut) if shut else "")
		if shut:
			root.get_node("Director").ui.toast(host.door_line(shut))
		await create_timer(0.8).timeout
		root.get_viewport().get_texture().get_image().save_png("/tmp/perf/shut_%s.png" % spot[0])
	quit()
