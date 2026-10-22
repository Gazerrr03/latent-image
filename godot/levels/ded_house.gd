extends Node3D
## 迷宫入口 / 出口门的碰撞：glb 里每个门扇旁边有一块「·碰撞」参考几何，
## 但 Godot 的 glTF 导入不会把它变成门扇的子节点，宿主就认不出这扇门。
## 这里给两扇门扇各补一个 StaticBody3D，宿主 _adopt_level() 随后会登记成可开关的门。

const DOORS := ["门入口", "门出口"]

func _ready() -> void:
	for nm in DOORS:
		var leaf := find_child(nm, true, false) as MeshInstance3D
		if leaf == null:
			push_warning("门缺失：" + nm)
			continue
		var has_body := false
		for c in leaf.get_children():
			if c is StaticBody3D:
				has_body = true
		if has_body:
			continue
		var aabb := leaf.get_aabb()
		var body := StaticBody3D.new()
		body.name = "碰撞"
		body.set_meta("door", true)
		var cs := CollisionShape3D.new()
		var box := BoxShape3D.new()
		box.size = aabb.size
		cs.shape = box
		cs.position = aabb.get_center()
		body.add_child(cs)
		leaf.add_child(body)
