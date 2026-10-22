## 动作白名单与解析（纯函数，不依赖任何自动加载，校验工具也用它）。
## 镜头表只能调用这些动作，见 docs/06-技术方案.md 2.2。

const ACTIONS := [
	"wait", "leak", "objective", "collect", "inspect",
	"annotate", "inquire", "link", "say", "telling", "develop",
	"goto", "fx", "footage", "osd", "reveal", "conceal", "recap", "diary", "anim",
	"music", "explore", "corridor", "station", "wake", "sleep", "cellar_gameplay",
]


## 声音列（镜头表、台词表、可检查物件表的 sound 列）：
## "door_knock;door_bang@3.2;-projector" -> [{id, delay, stop}]
## 编号 = 立刻播放；编号@秒 = 延迟播放；-编号 = 停掉这个循环声
static func parse_sounds(s: String) -> Array:
	var out: Array = []
	for raw in s.split(";", false):
		var t := raw.strip_edges()
		if t == "":
			continue
		var stop := t.begins_with("-")
		if stop:
			t = t.substr(1).strip_edges()
		var delay := 0.0
		var at := t.find("@")
		if at >= 0:
			delay = float(t.substr(at + 1)) if t.substr(at + 1).is_valid_float() else -1.0
			t = t.substr(0, at).strip_edges()
		out.append({"id": t, "delay": delay, "stop": stop})
	return out


## "leak(1);inspect(hs_a,hs_b)" -> [{name, args}]
static func parse(s: String) -> Array:
	var out: Array = []
	var depth := 0
	var buf := ""
	for ch in s + ";":
		if ch == "(":
			depth += 1
		elif ch == ")":
			depth -= 1
		if ch == ";" and depth == 0:
			var t := buf.strip_edges()
			buf = ""
			if t == "":
				continue
			var p := t.find("(")
			if p < 0:
				out.append({"name": t, "args": []})
			else:
				var inner := t.substr(p + 1, t.rfind(")") - p - 1)
				var args: Array = []
				for x in inner.split(",", false):
					args.append(x.strip_edges())
				out.append({"name": t.substr(0, p).strip_edges(), "args": args})
		else:
			buf += ch
	return out
