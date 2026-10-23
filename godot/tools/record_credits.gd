extends SceneTree
## 庄园实景片尾制作名单与致谢录制脚本
## 自动运行 CreditsSequence 并通知 MovieWriter 录制完整音画，完成后退出

func _initialize() -> void:
	_run.call_deferred()

func _run() -> void:
	print(">>> 开始录制庄园实景片尾制作名单与致谢...")
	var script: GDScript = load("res://world/credits_sequence.gd")
	if not script:
		printerr("无法加载 res://world/credits_sequence.gd")
		quit(1)
		return

	var seq: Node3D = script.new()
	get_root().add_child(seq)
	seq.start_sequence()

	await seq.finished
	print(">>> 庄园实景片尾录制完成，正在保存视频...")
	# 缓冲 15 帧确保渐隐平滑
	for f in 15:
		await process_frame
	quit(0)
