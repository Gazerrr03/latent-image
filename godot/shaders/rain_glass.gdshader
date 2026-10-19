// 窗玻璃上的雨：雨天挂在窗玻璃上的叠加材质（world/rain.gd）。
// 一层不动的小水珠，加几列往下滑、拖着水痕的水滴。按世界坐标铺，窗玻璃的 UV 怎么展都不影响。
shader_type spatial;
render_mode blend_mix, cull_disabled, depth_draw_never, shadows_disabled;

uniform float amount = 1.0;

varying vec3 wpos;

float hash(vec2 p) {
	return fract(sin(dot(p, vec2(127.1, 311.7))) * 43758.5453);
}

void vertex() {
	wpos = (MODEL_MATRIX * vec4(VERTEX, 1.0)).xyz;
}

void fragment() {
	// 沿窗面的横向坐标：x 与 z 都算上，东西、南北朝向的窗都能用
	vec2 p = vec2(wpos.x + wpos.z, wpos.y);
	// 不动的小水珠
	vec2 g = p * vec2(28.0, 22.0);
	vec2 cell = floor(g);
	float r = hash(cell);
	vec2 c = cell + 0.5 + (vec2(hash(cell + 3.1), hash(cell + 7.7)) - 0.5) * 0.6;
	float d = length((g - c) * vec2(1.0, 0.85));
	float beads = smoothstep(0.22, 0.12, d) * step(0.55, r);
	// 往下滑的水滴与水痕
	float col = floor(p.x * 9.0);
	float speed = 0.25 + hash(vec2(col, 1.0)) * 0.5;
	vec2 q = vec2(fract(p.x * 9.0) - 0.5, p.y * 1.4 + TIME * speed + hash(vec2(col, 2.0)) * 10.0);
	float lane = floor(q.y);
	float fy = fract(q.y);
	float on = step(0.72, hash(vec2(col, lane)));
	float head = smoothstep(0.16, 0.07, length(vec2(q.x * 2.4, (fy - 0.15) * 1.6)));
	float trail = smoothstep(0.05, 0.0, abs(q.x)) * smoothstep(0.15, 1.0, fy) * 0.45;
	float wet = clamp(beads * 0.7 + (head + trail) * on, 0.0, 1.0) * amount;
	ALBEDO = vec3(0.72, 0.76, 0.8);
	ROUGHNESS = 0.08;
	SPECULAR = 0.9;
	ALPHA = wet * 0.4;
}
