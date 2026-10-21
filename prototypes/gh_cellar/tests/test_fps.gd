extends SceneTree
## 粗略性能测试：加载关卡，关闭垂直同步，统计 4 秒平均帧率与 draw call。

func _initialize() -> void:
	_run.call_deferred()


func _run() -> void:
	var level: Node3D = (load("res://levels/gh_cellar.tscn") as PackedScene).instantiate()
	root.add_child(level)
	await process_frame
	await physics_frame
	DisplayServer.window_set_vsync_mode(DisplayServer.VSYNC_DISABLED)
	for i in 60:
		await process_frame
	var frames := 0
	var t0 := Time.get_ticks_usec()
	while Time.get_ticks_usec() - t0 < 4_000_000:
		await process_frame
		frames += 1
	var secs := float(Time.get_ticks_usec() - t0) / 1_000_000.0
	var fps := float(frames) / maxf(secs, 0.001)
	print("FPS_AVG %.1f  frames=%d  draw_calls=%d" % [
		fps, frames,
		int(Performance.get_monitor(Performance.RENDER_TOTAL_DRAW_CALLS_IN_FRAME))])
	quit(0)
