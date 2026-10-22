shader_type spatial;
// Static patina: no moving noise or accidental readable face before C7-04.
uniform bool fixed_image = false;
float hash(vec2 p) { return fract(sin(dot(p, vec2(127.1,311.7))) * 43758.5453); }
float noise(vec2 p) {
 vec2 i=floor(p), f=fract(p); f=f*f*(3.0-2.0*f);
 return mix(mix(hash(i),hash(i+vec2(1,0)),f.x),mix(hash(i+vec2(0,1)),hash(i+vec2(1)),f.x),f.y);
}
void fragment() {
 float stain = noise(UV*18.0)*0.65 + noise(UV*61.0)*0.35;
 float edge = smoothstep(0.26,0.47,max(abs(UV.x-0.5),abs(UV.y-0.5)));
 float corrosion = smoothstep(0.37,0.67,stain+edge*0.24);
 ALBEDO = fixed_image ? vec3(0.60,0.66,0.68) : mix(vec3(0.19,0.18,0.13),vec3(0.07,0.055,0.033),corrosion);
 METALLIC = fixed_image ? 0.82 : 0.28;
 ROUGHNESS = fixed_image ? 0.035 : 0.88;
}
