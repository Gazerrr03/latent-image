// 雪花屏：录像带信号中断时的噪点，带横向条纹。
shader_type canvas_item;

float hash(vec2 p) {
	return fract(sin(dot(p, vec2(12.9898, 78.233))) * 43758.5453);
}

void fragment() {
	float t = floor(TIME * 30.0);
	vec2 px = floor(FRAGCOORD.xy / vec2(2.0, 1.0));
	float n = hash(px + t);
	float band = step(0.92, hash(vec2(floor(FRAGCOORD.y / 3.0), t)));
	float v = mix(n * 0.55, 0.9, band * n);
	vec3 col = vec3(v) * vec3(0.95, 0.97, 1.0);
	col.r += (hash(px + t + 3.0) - 0.5) * 0.15;
	col.b += (hash(px + t + 7.0) - 0.5) * 0.15;
	COLOR = vec4(col, 1.0);
}
