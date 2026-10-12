## 动作白名单与解析（纯函数，不依赖任何自动加载，校验工具也用它）。
## 镜头表只能调用这些动作，见 docs/06-技术方案.md 2.2。

const ACTIONS := [
	"wait", "leak", "use_telegram", "objective", "collect", "inspect",
	"annotate", "inquire", "accuse", "link", "say", "ending_choice",
	"confession", "goto",
]


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
