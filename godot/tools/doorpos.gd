extends SceneTree
func _initialize() -> void:
    call_deferred("_run")
func _run() -> void:
    var s: Node3D = load("res://levels/ded_house.tscn").instantiate()
    root.add_child(s)
    for n in s.find_children("门*", "MeshInstance3D", true, false):
        var a: AABB = n.get_aabb()
        print(n.name, " | worldAABB P=", a.position, " S=", a.size)
    quit()
