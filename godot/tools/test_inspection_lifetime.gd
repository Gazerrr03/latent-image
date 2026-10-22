extends SceneTree
## Repeated real notebook openings: compare settled node/orphan counts after every return.
var failures:=0
func _initialize():call_deferred("run")
func run():
	root.get_node("GameState").persist=false
	var main=load("res://main.tscn").instantiate();root.add_child(main);await process_frame
	create_timer(150).timeout.connect(func():printerr("LIFETIME timeout");quit(2))
	var state=root.get_node("GameState");state.reset()
	var director=root.get_node("Director");var host=director.world;var ui=director.ui;var viewer=ui.inspector
	ui.menus.hide();ui.set_cinematic(false);ui.eyelids_set(1.0);host.show_scene("guest_room");host.set_mode("walk","")
	var ids=["ev_corridor_hook","ev_corridor_circle","ev_corridor_window","ev_shoe_mud","ev_letter_p2","ev_bottle_moved"]
	for id in ids:
		assert(root.get_node("ContentDB").evidence.has(id), "Unknown evidence: "+id)
		state.add_evidence(id)
	ui.browse_board();await process_frame
	var baseline_nodes:=-1;var baseline_orphans:=-1;var max_nodes:=0;var max_orphans:=0
	for cycle in 66:
		var id:String=ids[cycle%ids.size()];ui.board.examine(id)
		for frame in 180:
			if viewer.active:break
			await process_frame
		await create_timer(.25).timeout
		if not viewer.active or viewer._record:failures+=1;printerr("FAIL not a real object ",id);break
		viewer.toggle_reading();viewer.toggle_reading();viewer.close(true)
		await create_timer(.08).timeout
		var nodes:=int(Performance.get_monitor(Performance.OBJECT_NODE_COUNT));var orphans:=int(Performance.get_monitor(Performance.OBJECT_ORPHAN_NODE_COUNT))
		if cycle==5:baseline_nodes=nodes;baseline_orphans=orphans
		if cycle>=6:
			max_nodes=maxi(max_nodes,nodes);max_orphans=maxi(max_orphans,orphans)
			if nodes>baseline_nodes or orphans>baseline_orphans:
				failures+=1;printerr("FAIL settled counts grew cycle=",cycle," nodes=",nodes," orphans=",orphans)
		if not ui.board.visible or not host.player.frozen or viewer._pivot.get_child_count()!=0 or viewer.active:failures+=1
	print("LIFETIME_RESULT ",JSON.stringify({"warmup":6,"checked_cycles":60,"baseline_nodes":baseline_nodes,"maximum_nodes":max_nodes,"baseline_orphans":baseline_orphans,"maximum_orphans":max_orphans,"evidence_count":state.evidence.size(),"inspected_count":state.inspected.size(),"failures":failures}))
	ui.board.close();await process_frame
	if host.player.frozen or state.evidence.size()!=ids.size() or not state.inspected.is_empty():failures+=1
	print("INSPECTION_LIFETIME failures=",failures)
	main.queue_free();await process_frame;quit(0 if failures==0 else 1)
