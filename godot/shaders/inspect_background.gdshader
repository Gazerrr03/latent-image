shader_type canvas_item;
uniform sampler2D screen_texture : hint_screen_texture, filter_linear_mipmap;
uniform float amount : hint_range(0.0, 1.0) = 0.0;
uniform bool keep_center = false;
void fragment() {
	vec2 p = (SCREEN_UV - vec2(0.5)) / vec2(0.33, 0.37);
	float mask = keep_center ? smoothstep(0.65, 1.0, length(p)) : 1.0;
	vec3 sharp = textureLod(screen_texture, SCREEN_UV, 0.0).rgb;
	vec3 blurred = textureLod(screen_texture, SCREEN_UV, 3.0 * amount).rgb;
	COLOR = vec4(mix(sharp, blurred * 0.62, mask * amount), 1.0);
}
