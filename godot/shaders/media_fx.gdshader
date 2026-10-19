// 媒介滤镜：给整个 3D 画面套上“胶片 → 录像带 → 数字故障”的质感。
// 参数由 content/visual/fx.csv 的预设提供，随渗漏等级渐变（docs/04 第 9 节）。
// 每个效果单独一个强度，0 = 关闭。
shader_type canvas_item;

uniform sampler2D screen_tex : hint_screen_texture, filter_linear;

// —— 胶片（1920 年代） ——
uniform float sepia = 0.0;       // 泛黄程度 0—1
uniform vec3 tint : source_color = vec3(1.0, 0.9, 0.74);
uniform float desat = 0.0;       // 去色 0—1
uniform float grain = 0.0;       // 颗粒 0—0.2
uniform float flicker = 0.0;     // 亮度闪烁 0—0.15
uniform float vignette = 0.0;    // 暗角 0—1
uniform float scratches = 0.0;   // 竖向划痕出现概率 0—1
uniform float dust = 0.0;        // 灰尘斑点 0—1
uniform float weave = 0.0;       // 画面整体抖动 0—0.004
uniform float fps = 18.0;        // 胶片帧率（颗粒、抖动按帧跳变）
// —— 录像带 ——
uniform float chroma = 0.0;      // 红蓝错位 0—2
uniform float scanlines = 0.0;   // 扫描线 0—1
uniform float tracking = 0.0;    // 滚动的跟踪条纹 0—1
uniform float jitter = 0.0;      // 每行横向抖动 0—1
uniform float bleed = 0.0;       // 颜色向右拖影 0—1
// —— 数字 ——
uniform float glitch = 0.0;      // 方块错位 0—1
// —— 总强度（用于淡入淡出） ——
uniform float exploration = 0.0; // 行走舒适度：颗粒保留 65%，闪烁 50%，片门抖动 35%，划痕 30%，灰尘 50%
uniform float amount = 1.0;
uniform float brightness = 1.0;  // 设置里的亮度：gamma，1 = 原样

float hash(vec2 p) {
	return fract(sin(dot(p, vec2(127.1, 311.7))) * 43758.5453);
}

float hash1(float x) {
	return fract(sin(x * 91.3458) * 47453.5453);
}

void fragment() {
	vec2 uv = SCREEN_UV;
	float t = TIME;
	float frame = floor(t * fps);

	// 胶片：整体抖动（片门晃动）
	uv += (vec2(hash1(frame), hash1(frame + 7.0)) - 0.5) * weave * amount * mix(1.0, 0.35, exploration);

	// 录像带：每行横向抖动
	float line = floor(uv.y * 240.0);
	uv.x += (hash(vec2(line, floor(t * 30.0))) - 0.5) * jitter * 0.006 * amount;

	// 录像带：一条缓慢向下滚动的跟踪条纹
	float band_pos = fract(t * 0.06);
	float band = smoothstep(0.05, 0.0, abs(uv.y - band_pos)) * tracking * amount;
	uv.x += band * (hash(vec2(line, t)) - 0.5) * 0.06;

	// 数字：方块错位
	if (glitch > 0.0) {
		vec2 block = floor(uv * vec2(18.0, 10.0));
		float g = hash(block + floor(t * 6.0));
		if (g < glitch * amount * 0.12) {
			uv.x += (hash(block + 3.1) - 0.5) * 0.1;
		}
	}

	// 取色：红蓝错位
	vec2 off = vec2(chroma * 0.003 * amount, 0.0);
	vec3 col;
	col.r = texture(screen_tex, uv + off).r;
	col.g = texture(screen_tex, uv).g;
	col.b = texture(screen_tex, uv - off).b;
	vec3 clean = texture(screen_tex, SCREEN_UV).rgb;

	// 录像带：颜色向右拖影
	if (bleed > 0.0) {
		vec3 acc = col;
		for (int i = 1; i <= 5; i++) {
			acc += texture(screen_tex, uv - vec2(float(i) * 0.002 * bleed, 0.0)).rgb;
		}
		col = mix(col, acc / 6.0, 0.65);
	}

	// 胶片：泛黄与去色
	float lum = dot(col, vec3(0.299, 0.587, 0.114));
	col = mix(col, vec3(lum) * tint * 1.1, sepia);
	col = mix(col, vec3(lum), desat);

	// 胶片：亮度闪烁
	col *= 1.0 + (hash1(frame * 1.37) - 0.5) * flicker * 2.0 * mix(1.0, 0.5, exploration);

	// 录像带：扫描线与跟踪条纹里的噪点
	col *= 1.0 - scanlines * 0.35 * (0.5 + 0.5 * sin(FRAGCOORD.y * 3.14159 * 0.5));
	col += band * hash(vec2(floor(FRAGCOORD.x * 0.5), line + floor(t * 30.0))) * 0.4;

	// 胶片：竖向划痕（每帧随机出现 0—2 条）
	for (int k = 0; k < 2; k++) {
		float fk = float(k);
		if (hash1(frame + fk * 5.3) < scratches * mix(1.0, 0.3, exploration)) {
			float x = hash1(frame * 0.37 + fk * 13.1);
			float d = abs(SCREEN_UV.x - x);
			float s = smoothstep(0.0012, 0.0, d);
			col = mix(col, k == 0 ? vec3(0.08) : vec3(0.85, 0.8, 0.7), s * 0.7);
		}
	}

	// 胶片：灰尘斑点
	float speck = step(1.0 - dust * mix(1.0, 0.5, exploration) * 0.003, hash(floor(FRAGCOORD.xy / 3.0) + frame));
	col = mix(col, vec3(0.06), speck);

	// 颗粒
	col += (hash(FRAGCOORD.xy + frame) - 0.5) * grain * mix(1.0, 0.65, exploration);

	// 暗角
	vec2 v = SCREEN_UV - 0.5;
	col *= 1.0 - dot(v, v) * vignette * 1.8;

	vec3 outc = max(mix(clean, col, amount), vec3(0.0));
	COLOR = vec4(pow(outc, vec3(1.0 / brightness)), 1.0);
}
