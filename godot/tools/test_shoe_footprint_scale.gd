extends SceneTree
var failures:=0
func _initialize():call_deferred("run")
func check(label: String,ok: bool):
	print("PASS " if ok else "FAIL ",label)
	if not ok:failures+=1
func find_root(parents: Array,index: int) -> int:
	while parents[index]!=index:
		parents[index]=parents[parents[index]];index=parents[index]
	return index
func components(source: MeshInstance3D, match_material: String) -> Array:
	var groups: Array=[]
	for surface in source.mesh.get_surface_count():
		if not source.get_active_material(surface).resource_name.contains(match_material):continue
		var arrays:=source.mesh.surface_get_arrays(surface)
		var vertices: PackedVector3Array=arrays[Mesh.ARRAY_VERTEX]
		var indices: PackedInt32Array=arrays[Mesh.ARRAY_INDEX]
		var points: Array[Vector3]=[];var ids:=[];var parents:=[];var keys:={}
		for vertex in vertices:
			var p: Vector3=source.global_transform*vertex
			var key:=Vector3i(roundi(p.x*10000),roundi(p.y*10000),roundi(p.z*10000))
			if not keys.has(key):keys[key]=points.size();points.append(p);parents.append(parents.size())
			ids.append(keys[key])
		if indices.is_empty():
			for i in vertices.size():indices.append(i)
		for i in range(0,indices.size(),3):
			for j in [1,2]:parents[find_root(parents,ids[indices[i+j]])]=find_root(parents,ids[indices[i]])
		var found:={}
		for i in points.size():
			var r:=find_root(parents,i)
			if not found.has(r):found[r]=[]
			found[r].append(Vector2(points[i].x,points[i].z))
		for cloud in found.values():
			var diameter:=0.0
			for a in cloud:
				for b in cloud:diameter=maxf(diameter,a.distance_to(b))
			if diameter>.04:groups.append({"points":cloud,"diameter":diameter})
	groups.sort_custom(func(a,b):return a.diameter>b.diameter)
	return groups
func widths(points: Array) -> Array[float]:
	var out: Array[float]=[]
	for degree in 180:
		var direction:=Vector2(cos(deg_to_rad(float(degree))),sin(deg_to_rad(float(degree))))
		var lo:=INF;var hi:=-INF
		for p in points:
			var dot: float=p.dot(direction);lo=minf(lo,dot);hi=maxf(hi,dot)
		out.append(hi-lo)
	return out
func compare(a: Array,b: Array) -> Dictionary:
	var wa:=widths(a);var wb:=widths(b);var best:=INF;var maximum:=INF
	for shift in 180:
		var error:=0.0;var peak:=0.0
		for i in 180:
			var delta:=absf(wa[i]-wb[(i+shift)%180]);error+=delta*delta;peak=maxf(peak,delta)
		if error<best:best=error;maximum=peak
	return {"rms_m":sqrt(best/180.0),"max_m":maximum}
func center(points: Array) -> Vector2:
	var lo:=Vector2(INF,INF);var hi:=Vector2(-INF,-INF)
	for p in points:lo=lo.min(p);hi=hi.max(p)
	return (lo+hi)*.5
func nearest_gap(fore: Array,heels: Array) -> float:
	var best:=INF
	for heel in heels:best=minf(best,center(fore).distance_to(center(heel.points)))
	return best
func run():
	root.get_node("GameState").persist=false
	var main=load("res://main.tscn").instantiate();root.add_child(main);await process_frame
	var host=root.get_node("Director").world
	host.show_scene("guest_room")
	var data=load("res://ui/inspection_catalog.gd").hotspot("hs_shoes",host)
	var shoe: MeshInstance3D=data.sources[0]
	var shoes:=components(shoe,"分开的前掌与鞋跟")
	var slot:=AABB();var has_slot:=false
	var original=load("res://art/levels/manor/room_guest_room.gltf").instantiate()
	for node in host._walk(original):
		if not node is MeshInstance3D:continue
		for surface in node.mesh.get_surface_count():
			var material: Material=node.mesh.surface_get_material(surface)
			if material==null or material.resource_name!="manor_室内_黑皮鞋":continue
			for vertex in node.mesh.surface_get_arrays(surface)[Mesh.ARRAY_VERTEX]:
				if not has_slot:slot=AABB(vertex,Vector3.ZERO);has_slot=true
				else:slot=slot.expand(vertex)
	var actual:=shoe.mesh.get_aabb()
	check("保留衣柜内水平中心和承托底面",has_slot and absf(actual.get_center().x-slot.get_center().x)<.0001 and absf(actual.get_center().z-slot.get_center().z)<.0001 and absf(actual.position.y-slot.position.y)<.0001)
	check("真实尺寸鞋仍放得进原衣柜",shoe.get_parent().mesh.get_aabb().grow(.001).encloses(actual))
	original.free()

	print("SHOE_SCALE_GEOMETRY ",shoe.mesh.get_aabb()," basis=",shoe.global_basis.get_scale()," components=",shoes.size()," sizes=",shoes.map(func(c):return [c.diameter,c.points.size()]))
	check("真实原位鞋底含两前掌两鞋跟足弓及内底",shoes.size()==8)
	host.show_scene("garden")
	var print_mesh: MeshInstance3D
	for node in host._walk(host.room):
		if node is MeshInstance3D and String(node.name)=="花园·泥地鞋印":print_mesh=node
	var prints:=components(print_mesh,"湿泥鞋印")
	check("真实现场保留原前掌和鞋跟残片",prints.size()==7)
	if shoes.size()!=8 or prints.size()!=7:quit(1);return
	for i in [0,1,4,5]:
		var best={"rms_m":INF,"max_m":INF}
		for trace in prints:
			var comparison:=compare(shoes[i].points,trace.points)
			if comparison.rms_m<best.rms_m:best=comparison
		print("SOLE_TRACE_MATCH ",JSON.stringify({"part":i,"diameter_m":shoes[i].diameter,"error":best}))
		check("实物鞋底片段%d与原鞋印实尺吻合"%i,best.rms_m<.0012 and best.max_m<.002)
	var heels: Array=prints.filter(func(trace):return trace.diameter<.15)
	var source_gap:=INF
	for trace in prints:
		if trace.diameter>.15:source_gap=minf(source_gap,nearest_gap(trace.points,heels))
	for i in [0,1]:
		var shoe_gap:=nearest_gap(shoes[i].points,[shoes[4],shoes[5]])
		print("SOLE_HEEL_SPACING ",JSON.stringify({"shoe_m":shoe_gap,"print_m":source_gap}))
		check("鞋底前掌与鞋跟相对间距%d保持实尺"%i,source_gap>.15 and absf(shoe_gap-source_gap)<.003)
	print("SHOE_FOOTPRINT_SCALE failures=",failures)
	main.queue_free();await process_frame;quit(0 if failures==0 else 1)
