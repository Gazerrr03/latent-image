// 渗漏 L3—L4：被“清除”的空间露出底层——白模 + 世界坐标网格。
// 移植自 three.js 原型（game/src/scenes/common.ts）的白模与网格线表现。
shader_type spatial;

uniform vec3 base_color : source_color = vec3(0.90, 0.89, 0.86);
uniform vec3 line_color : source_color = vec3(0.16, 0.16, 0.16);
uniform float cell = 0.5;          // 网格间距（米）
uniform float line_width = 0.012;  // 线宽（米）
uniform float line_alpha = 0.55;

varying vec3 world_pos;
varying vec3 world_normal;

void vertex() {
	world_pos = (MODEL_MATRIX * vec4(VERTEX, 1.0)).xyz;
	world_normal = normalize((MODEL_MATRIX * vec4(NORMAL, 0.0)).xyz);
}

float grid(vec2 p) {
	vec2 g = abs(fract(p / cell - 0.5) - 0.5) * cell;
	float d = min(g.x, g.y);
	return 1.0 - smoothstep(line_width * 0.5, line_width, d);
}

void fragment() {
	// 按法线方向选择投影平面，地面、墙面都能画出网格
	vec3 n = abs(world_normal);
	float l;
	if (n.y > n.x && n.y > n.z) {
		l = grid(world_pos.xz);
	} else if (n.x > n.z) {
		l = grid(world_pos.zy);
	} else {
		l = grid(world_pos.xy);
	}
	ALBEDO = mix(base_color, line_color, l * line_alpha);
	ROUGHNESS = 1.0;
}
