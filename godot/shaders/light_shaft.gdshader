// 假光柱：窗口斜照进屋里的一束光（world/look.gd 的 shaft_mesh 生成形状）。
// 叠加混合、不受光、不写深度：横竖几张薄片，每张两边淡出、靠近窗口亮、往里渐淡；侧着看的薄片淡掉，
// 镜头钻进光里时也淡掉；空气里一点缓慢飘动的明暗。强度由天光表 shafts 列给。
shader_type spatial;
render_mode blend_add, unshaded, cull_disabled, depth_draw_never, shadows_disabled, fog_disabled;

uniform float amount = 0.0;
uniform vec3 tint : source_color = vec3(1.0, 0.95, 0.85);

varying vec3 wpos;

float hash(vec3 p) {
	return fract(sin(dot(p, vec3(127.1, 311.7, 74.7))) * 43758.5453);
}

float noise(vec3 p) {
	vec3 i = floor(p);
	vec3 f = fract(p);
	f = f * f * (3.0 - 2.0 * f);
	float a = mix(mix(hash(i), hash(i + vec3(1, 0, 0)), f.x), mix(hash(i + vec3(0, 1, 0)), hash(i + vec3(1, 1, 0)), f.x), f.y);
	float b = mix(mix(hash(i + vec3(0, 0, 1)), hash(i + vec3(1, 0, 1)), f.x), mix(hash(i + vec3(0, 1, 1)), hash(i + vec3(1, 1, 1)), f.x), f.y);
	return mix(a, b, f.z);
}

void vertex() {
	wpos = (MODEL_MATRIX * vec4(VERTEX, 1.0)).xyz;
}

void fragment() {
	float along = UV.x;                                    // 0 = 窗口，1 = 光落到的地方
	float fade = pow(1.0 - along, 1.6) * smoothstep(0.0, 0.06, along);
	float across = sin(UV.y * 3.14159);                     // 薄片两边淡出
	across *= across;
	float edge = abs(dot(normalize(NORMAL), normalize(VIEW)));   // 侧着看的薄片淡掉，看不出是一张片
	float near_cam = smoothstep(0.8, 2.5, -VERTEX.z);
	float air = 0.75 + 0.5 * noise(wpos * 1.3 + vec3(0.0, TIME * 0.05, TIME * 0.03));
	ALBEDO = tint * fade * across * edge * COLOR.r * near_cam * air * amount;
}
