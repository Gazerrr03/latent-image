extends Node
## 展示相机的“最后一道手”：优先级最大，每帧在别的脚本之后把相机摆好并夺回 current，剧情与玩家抢不过它。

var cam: Camera3D
var pose: Callable          # (帧号) -> void，摆相机
var frame := 0


func _init() -> void:
	process_priority = 100000


func _process(_dt: float) -> void:
	if cam and is_instance_valid(cam):
		pose.call(frame)
		cam.current = true
