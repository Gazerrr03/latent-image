shader_type canvas_item;
// 眼睑：open = 1 全睁，0 全闭。上下两片弧形的黑，边缘柔，合到一半时整体也暗下去（docs/01 第 4 节）
uniform float open : hint_range(0.0, 1.0) = 1.0;

void fragment() {
	vec2 uv = UV;
	float x = uv.x * 2.0 - 1.0;
	// 眼睑是弧形：中间张得最开，两边收拢
	float h = open * 0.75 * (1.0 - 0.25 * x * x);
	float d = abs(uv.y - 0.5);
	float soft = 0.05 + 0.1 * (1.0 - open);
	float lid = smoothstep(h - soft, h + soft * 0.3, d);
	float dim = (1.0 - open) * 0.55;
	COLOR = vec4(0.0, 0.0, 0.0, clamp(max(lid, dim), 0.0, 1.0));
}
