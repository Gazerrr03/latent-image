extends Control
## 取景框中央的对焦环。

var focus := 0.0
var active := false


func set_focus(value: float, visible_ring := true) -> void:
	focus = clampf(value, 0.0, 1.0)
	active = visible_ring
	queue_redraw()


func _draw() -> void:
	if not active:
		return
	var c := size * 0.5
	var r := minf(size.x, size.y) * 0.105
	draw_circle(c, r + 9.0, Color(0.0, 0.0, 0.0, 0.18))
	draw_arc(c, r, 0.0, TAU, 96, Color(0.85, 0.78, 0.62, 0.22), 2.0, true)
	draw_arc(c, r, -PI / 2.0, -PI / 2.0 + TAU * maxf(0.001, focus),
		96, Color(1.0, 0.66, 0.28, 0.95), 4.0, true)
	draw_circle(c, 3.5, Color(1.0, 0.82, 0.55, 0.95))
	for i in 4:
		var a := -PI / 2.0 + i * PI / 2.0
		var p0 := c + Vector2(cos(a), sin(a)) * (r + 12.0)
		var p1 := c + Vector2(cos(a), sin(a)) * (r + 20.0)
		draw_line(p0, p1, Color(0.9, 0.82, 0.65, 0.35), 2.0)
