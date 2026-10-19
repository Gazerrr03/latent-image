// 庄园的天空：一张全景照片（远处的山、树林和云），白天、夜里、雨天共用同一张，只改亮度和色调。
// 参数由 content/visual/look.csv 提供（world/look.gd）。
shader_type sky;

uniform sampler2D panorama : filter_linear, repeat_enable;
uniform vec3 tint = vec3(1.0);
uniform float energy = 1.0;

void sky() {
	COLOR = texture(panorama, SKY_COORDS).rgb * tint * energy;
}
