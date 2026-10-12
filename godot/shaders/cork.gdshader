// 软木板：暖棕底色 + 细碎颗粒 + 四周暗角。全部程序生成，不需要贴图。
shader_type canvas_item;

uniform vec3 base : source_color = vec3(0.55, 0.40, 0.25);

float hash(vec2 p) {
	return fract(sin(dot(p, vec2(127.1, 311.7))) * 43758.5453);
}

void fragment() {
	vec2 px = FRAGCOORD.xy;
	float g = hash(floor(px / 2.0)) * 0.5 + hash(floor(px / 7.0)) * 0.5;
	vec3 col = base * (0.82 + 0.3 * g);
	float spot = step(0.985, hash(floor(px / 3.0) + 17.0));
	col *= 1.0 - spot * 0.35;
	vec2 uv = UV - 0.5;
	col *= 1.0 - dot(uv, uv) * 1.1;
	COLOR = vec4(col, 1.0);
}
