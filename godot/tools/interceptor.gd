extends Node
var le: LineEdit

func _input(event: InputEvent) -> void:
	if event is InputEventKey:
		print("interceptor 收到事件, 转发给 le 并 set_input_as_handled")
		# 尝试转发
		# 或者通过其他机制？
		# 让我们测试
