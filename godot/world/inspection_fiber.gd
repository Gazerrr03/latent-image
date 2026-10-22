extends Node3D
## 同一段真实呢线用于现场与笔记本：三股捻线、少量散纤维，顶端挂回原插销扣。
func _ready() -> void:
	var surface := SurfaceTool.new()
	surface.begin(Mesh.PRIMITIVE_TRIANGLES)
	var core: Array[Vector3] = [Vector3(.006, .001, 0), Vector3(.003, .0015, .001)]
	for i in 25:
		var t := float(i) / 24.0
		core.append(Vector3(.002 * sin(t * TAU), -.065 * t, .011 * sin(t * TAU * 1.25)))
	_strand(surface, core, .00048, 7)
	for ply in 3:
		var strand: Array[Vector3] = []
		for i in core.size():
			var angle := TAU * (float(i) / float(core.size()-1) * 7.0 + float(ply) / 3.0)
			strand.append(core[i] + Vector3(cos(angle),0,sin(angle)) * .0004)
		_strand(surface, strand, .0004, 6)
	for i in range(3, core.size()-1, 2):
		var outward := Vector3(cos(i*2.4), .5*sin(i), sin(i*2.4))
		var fiber: Array[Vector3] = [core[i], core[i]+outward*.0015, core[i]+outward*.0025+Vector3(0,-.001,0)]
		_strand(surface, fiber, .00010, 4)
	var mesh := MeshInstance3D.new()
	mesh.mesh = surface.commit()
	var material := StandardMaterial3D.new()
	material.albedo_color = Color("#4b4947")
	material.roughness = 1.0
	mesh.material_override = material
	add_child(mesh)

func _strand(surface: SurfaceTool, points: Array[Vector3], radius: float, sides: int) -> void:
	for i in points.size()-1:
		var direction := (points[i+1]-points[i]).normalized()
		var axis := Vector3.UP if absf(direction.dot(Vector3.RIGHT))>.95 else Vector3.RIGHT
		var side := direction.cross(axis).normalized()
		var up := direction.cross(side).normalized()
		for j in sides:
			var a := TAU*j/sides;var b := TAU*(j+1)/sides
			var n0 := side*cos(a)+up*sin(a);var n1 := side*cos(b)+up*sin(b)
			var corners := [points[i]+n0*radius,points[i]+n1*radius,points[i+1]+n1*radius,points[i+1]+n0*radius]
			for index in [0,1,2,0,2,3]:
				surface.set_normal(n0 if index in [0,3] else n1)
				surface.add_vertex(corners[index])
