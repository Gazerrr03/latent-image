shader_type spatial;
render_mode unshaded, cull_disabled;

uniform sampler2D panorama : source_color, filter_linear_mipmap, repeat_disable;
uniform float visible_fraction : hint_range(0.01, 1.0) = 0.4377;
uniform float scroll_progress : hint_range(0.0, 1.0) = 0.0;
uniform float paper_brightness : hint_range(0.1, 1.5) = 0.72;

void fragment() {
	float fraction = clamp(visible_fraction, 0.01, 1.0);
	float offset = clamp(scroll_progress, 0.0, 1.0) * (1.0 - fraction);
	vec2 panorama_uv = vec2(UV.x * fraction + offset, UV.y);
	ALBEDO = texture(panorama, panorama_uv).rgb * paper_brightness;
}
