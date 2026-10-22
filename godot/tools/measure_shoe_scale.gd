extends SceneTree
func _initialize():call_deferred("run")
func run():
	root.get_node("GameState").persist=false
	var main=load("res://main.tscn").instantiate();root.add_child(main);await process_frame
	var host=root.get_node("Director").world
	host.show_scene("guest_room")
	var data=load("res://ui/inspection_catalog.gd").hotspot("hs_shoes",host)
	var shoe: MeshInstance3D=data.sources[0]
	print("SHOE_SCALE ",JSON.stringify({"local_bounds":str(shoe.mesh.get_aabb()),"basis_scale":str(shoe.global_basis.get_scale()),"world_bounds":str(shoe.global_transform*shoe.mesh.get_aabb())}))
	main.queue_free();await process_frame;quit()
