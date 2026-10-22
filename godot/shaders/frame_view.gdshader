shader_type spatial;
render_mode cull_disabled;

uniform sampler2D normal_tex : source_color;
uniform sampler2D lens_blur_tex : source_color;
uniform sampler2D lens_sharp_tex : source_color;
uniform sampler2D empty_tex : source_color;
uniform float camera_mix : hint_range(0.0, 1.0) = 0.0;
uniform float focus : hint_range(0.0, 1.0) = 0.0;
uniform float state : hint_range(0.0, 1.0) = 0.0;

float hash(vec2 p) {
	return fract(sin(dot(p, vec2(127.1, 311.7))) * 43758.5453);
}

void fragment() {
	vec3 n = texture(normal_tex, UV).rgb;
	vec3 b = texture(lens_blur_tex, UV).rgb;
	vec3 s = texture(lens_sharp_tex, UV).rgb;
	vec3 e = texture(empty_tex, UV).rgb;
	float sharp = smoothstep(0.18, 0.94, focus);
	vec3 lens = mix(b, s, sharp);
	vec3 col = mix(n, lens, camera_mix);
	col = mix(col, e, state);
	// slight silver-gelatin grain, stronger inside the lens
	float grain = hash(UV * vec2(1920.0, 1080.0)) - 0.5;
	col += grain * (0.018 + 0.02 * camera_mix);
	// soft photographic vignette
	vec2 d = UV - vec2(0.5);
	col *= 1.0 - 0.18 * dot(d, d);
	ALBEDO = col;
	ROUGHNESS = mix(0.46, 0.32, camera_mix);
	SPECULAR = 0.22;
}
