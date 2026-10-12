## 灰盒房间规格：美术模型到位之前，用方块搭出布局、机位和热区。
## 尺寸单位为米；房间中心在原点，地面 y=0，-z 为“前方”（进门后面对的方向）。
## 布局依据 docs/03-空间与关卡设计.md；正式模型到位后由 scenes.csv 的 model 列取代。
##
## 字段：
##   size      房间内部尺寸 (宽 x, 高 y, 深 z)
##   lights    [位置, 颜色, 能量]
##   props     {name, pos(中心), size, color}
##   hotspots  id -> 位置（可检查的物件，0.3 m 方块）
##   markers   机位名 -> [机位位置, 看向的点]
##   spawn     [位置, 朝向角(度)]，行走模式的出生点

const WOOD := Color("#5b3f2a")
const DARK := Color("#2b2420")
const CLOTH := Color("#4a2a2a")
const BRASS := Color("#8a7444")
const PAPER := Color("#d8cdb4")
const STONE := Color("#6b6660")

static func get_spec(id: String) -> Dictionary:
	match id:
		"office":
			return {
				"size": Vector3(4, 3, 4),
				"lights": [[Vector3(0.4, 1.4, -1.0), Color("#ffc98a"), 3.0], [Vector3(0, 2, -2), Color("#6f86b8"), 0.6]],
				"props": [
					{"name": "书桌", "pos": Vector3(0, 0.38, -1.0), "size": Vector3(1.6, 0.76, 0.8), "color": WOOD},
					{"name": "打字机", "pos": Vector3(0, 0.86, -1.0), "size": Vector3(0.4, 0.2, 0.35), "color": DARK},
					{"name": "电报纸", "pos": Vector3(0.5, 0.78, -0.9), "size": Vector3(0.22, 0.03, 0.15), "color": PAPER},
					{"name": "委托信", "pos": Vector3(-0.5, 0.77, -0.9), "size": Vector3(0.2, 0.01, 0.28), "color": PAPER},
					{"name": "台灯", "pos": Vector3(0.6, 1.0, -1.25), "size": Vector3(0.15, 0.45, 0.15), "color": BRASS},
					{"name": "窗", "pos": Vector3(0, 1.6, -1.98), "size": Vector3(1.4, 1.2, 0.04), "color": Color("#1c2638")},
				],
				"hotspots": {},
				"markers": {
					"establish": [Vector3(0.6, 1.7, 0.4), Vector3(0, 0.85, -1.0)],
					"letter_close": [Vector3(-0.45, 1.25, -0.6), Vector3(-0.5, 0.77, -0.9)],
					"typewriter_close": [Vector3(0.1, 1.1, -0.55), Vector3(0, 0.9, -1.0)],
					"door_follow": [Vector3(0, 1.6, -0.2), Vector3(0, 1.4, 1.9)],
				},
				"spawn": [Vector3(0, 0, 1.2), 0.0],
			}
		"street":
			return {
				"size": Vector3(8, 6, 12),
				"lights": [[Vector3(2, 4, -3), Color("#ffd9a0"), 2.0]],
				"props": [
					{"name": "门廊立柱", "pos": Vector3(-1.5, 1.5, 0), "size": Vector3(0.3, 3, 0.3), "color": STONE},
					{"name": "出租车", "pos": Vector3(1.5, 0.75, -4), "size": Vector3(1.8, 1.5, 4.2), "color": Color("#1b1b1d")},
				],
				"hotspots": {},
				"markers": {"follow": [Vector3(0, 1.7, 2.5), Vector3(1.5, 1, -4)]},
				"spawn": [Vector3(0, 0, 3), 0.0],
			}
		"manor_gate":
			return {
				"size": Vector3(20, 10, 30),
				"lights": [[Vector3(0, 6, -12), Color("#ffd28a"), 4.0]],
				"props": [
					{"name": "铁门左", "pos": Vector3(-1.2, 1.5, -4), "size": Vector3(2, 3, 0.1), "color": DARK},
					{"name": "铁门右", "pos": Vector3(1.2, 1.5, -4), "size": Vector3(2, 3, 0.1), "color": DARK},
					{"name": "庄园", "pos": Vector3(0, 4, -13), "size": Vector3(16, 8, 4), "color": STONE},
				],
				"hotspots": {},
				"markers": {"wide_symmetric": [Vector3(0, 1.6, 4), Vector3(0, 3.5, -13)]},
				"spawn": [Vector3(0, 0, 5), 0.0],
			}
		"hall":
			return {
				"size": Vector3(6, 3.6, 5),
				"lights": [[Vector3(0, 2.8, 0), Color("#ffcf95"), 2.5]],
				"props": [
					{"name": "访客簿与支架", "pos": Vector3(-2.2, 1.0, -1.0), "size": Vector3(0.5, 0.1, 0.4), "color": CLOTH},
					{"name": "镜子", "pos": Vector3(2.95, 1.6, -0.5), "size": Vector3(0.04, 1.4, 0.8), "color": Color("#9fb0b8")},
					{"name": "座钟", "pos": Vector3(-2.7, 1.0, 1.5), "size": Vector3(0.45, 2.0, 0.35), "color": WOOD},
					{"name": "帽架", "pos": Vector3(2.4, 0.9, 1.8), "size": Vector3(0.3, 1.8, 0.3), "color": WOOD},
				],
				"hotspots": {},
				"markers": {"hall_mid": [Vector3(1.2, 1.65, 2.0), Vector3(-2.2, 1.0, -1.0)]},
				"spawn": [Vector3(0, 0, 2), 0.0],
			}
		"study":
			return {
				"size": Vector3(5, 3.2, 4),
				"lights": [[Vector3(0.55, 1.3, -1.25), Color("#ffc98a"), 3.0]],
				"props": [
					{"name": "书桌", "pos": Vector3(0, 0.38, -1.2), "size": Vector3(1.6, 0.76, 0.8), "color": WOOD},
					{"name": "转椅", "pos": Vector3(0, 0.45, -0.55), "size": Vector3(0.55, 0.9, 0.55), "color": CLOTH},
					{"name": "台灯", "pos": Vector3(0.55, 1.0, -1.35), "size": Vector3(0.15, 0.45, 0.15), "color": BRASS},
					{"name": "书架", "pos": Vector3(-2.3, 1.1, 0), "size": Vector3(0.35, 2.2, 2.4), "color": WOOD},
					{"name": "平面图画框", "pos": Vector3(2.47, 1.6, 0.2), "size": Vector3(0.04, 1.0, 1.4), "color": PAPER},
					{"name": "镜子", "pos": Vector3(-1.2, 1.6, 1.97), "size": Vector3(0.7, 1.2, 0.04), "color": Color("#9fb0b8")},
					{"name": "窗", "pos": Vector3(1.2, 1.6, -1.98), "size": Vector3(1.2, 1.3, 0.04), "color": Color("#1c2638")},
				],
				"hotspots": {
					"hs_latch": Vector3(0.4, 1.1, 1.95),
					"hs_window": Vector3(1.2, 1.4, -1.85),
					"hs_phone": Vector3(-0.5, 0.85, -1.15),
					"hs_receipt": Vector3(0.6, 0.79, -0.95),
					"hs_register": Vector3(0.05, 0.8, -1.05),
					"hs_journal_p1": Vector3(-0.2, 0.8, -1.0),
					"hs_mirror_study": Vector3(-1.2, 1.6, 1.85),
					"hs_lending_cards": Vector3(-2.05, 1.2, 0.5),
					"hs_floorplan": Vector3(2.35, 1.6, 0.2),
				},
				"markers": {
					"door_push": [Vector3(0, 1.6, 1.7), Vector3(0, 0.9, -1.2)],
					"desk_close": [Vector3(0.2, 1.35, -0.3), Vector3(0, 0.8, -1.1)],
					"study_mid": [Vector3(1.6, 1.6, 1.2), Vector3(-0.3, 0.9, -1.0)],
					"chair_over_shoulder": [Vector3(0.4, 1.45, 0.1), Vector3(0, 0.8, -1.2)],
					"orbit_desk": [Vector3(-1.4, 1.5, -0.2), Vector3(0, 0.8, -1.2)],
					"mirror": [Vector3(-0.4, 1.6, 0.6), Vector3(-1.2, 1.6, 1.97)],
				},
				"spawn": [Vector3(0, 0, 1.4), 0.0],
			}
		"parlor":
			return {
				"size": Vector3(7, 3.4, 6),
				"lights": [[Vector3(-2.8, 0.6, -2.4), Color("#ff9a4a"), 3.0], [Vector3(2.5, 1.4, 1.8), Color("#ffc98a"), 1.5]],
				"props": [
					{"name": "沙发", "pos": Vector3(-1.0, 0.4, -1.2), "size": Vector3(2.4, 0.8, 0.9), "color": CLOTH},
					{"name": "壁炉", "pos": Vector3(-3.2, 0.6, -2.4), "size": Vector3(0.5, 1.2, 1.4), "color": STONE},
					{"name": "虎纹挂毯", "pos": Vector3(0, 1.8, -2.97), "size": Vector3(2.0, 1.3, 0.04), "color": Color("#8a5a22")},
					{"name": "证据板", "pos": Vector3(3.47, 1.5, 1.0), "size": Vector3(0.05, 1.1, 1.6), "color": Color("#9a7a52")},
					{"name": "侦探工作台", "pos": Vector3(2.6, 0.38, 1.8), "size": Vector3(1.2, 0.76, 0.7), "color": WOOD},
					{"name": "巴洛", "pos": Vector3(-1.9, 0.85, -1.2), "size": Vector3(0.45, 1.7, 0.4), "color": DARK},
					{"name": "韦恩小姐", "pos": Vector3(-1.0, 0.8, -1.2), "size": Vector3(0.4, 1.6, 0.4), "color": Color("#3a3f55")},
					{"name": "朗斯", "pos": Vector3(-0.1, 0.85, -1.2), "size": Vector3(0.45, 1.75, 0.4), "color": Color("#4a4a3a")},
				],
				"hotspots": {
					"hs_barlow_watch": Vector3(-1.9, 1.0, -0.95),
					"hs_wynn_fingers": Vector3(-1.0, 0.95, -0.95),
					"hs_lance_window": Vector3(-0.1, 1.5, -0.95),
				},
				"markers": {
					"parlor_mid": [Vector3(1.5, 1.55, 2.0), Vector3(-1.0, 1.0, -1.2)],
					"suspects_close": [Vector3(-1.0, 1.3, 0.4), Vector3(-1.0, 1.1, -1.2)],
					"register_close": [Vector3(2.6, 1.3, 2.25), Vector3(2.6, 0.78, 1.75)],
					"board": [Vector3(2.0, 1.55, 1.0), Vector3(3.47, 1.5, 1.0)],
					"telegram_close": [Vector3(2.85, 1.15, 2.2), Vector3(2.85, 0.78, 1.8)],
					"two_shot": [Vector3(1.6, 1.5, 0.8), Vector3(-1.0, 1.0, -1.2)],
				},
				"spawn": [Vector3(1.5, 0, 2.2), 0.0],
				"suspect_props": {"巴洛": "巴洛", "韦恩小姐": "韦恩小姐", "朗斯": "朗斯"},
			}
		"butler_room":
			return {
				"size": Vector3(5, 3.0, 6),
				"lights": [[Vector3(-1.8, 1.0, -2.2), Color("#ffc98a"), 1.8], [Vector3(2.0, 1.6, -2.6), Color("#ffb070"), 1.4]],
				"props": [
					{"name": "床铺", "pos": Vector3(-1.6, 0.3, -1.8), "size": Vector3(1.0, 0.6, 2.0), "color": PAPER},
					{"name": "衣柜", "pos": Vector3(-2.2, 1.0, 1.2), "size": Vector3(0.6, 2.0, 1.2), "color": WOOD},
					{"name": "书桌", "pos": Vector3(1.2, 0.38, 1.8), "size": Vector3(1.2, 0.76, 0.6), "color": WOOD},
					{"name": "钥匙房隔墙", "pos": Vector3(1.5, 1.5, -1.5), "size": Vector3(2.0, 3.0, 0.1), "color": STONE},
					{"name": "钥匙钩板", "pos": Vector3(2.0, 1.5, -2.9), "size": Vector3(1.4, 0.6, 0.06), "color": WOOD},
					{"name": "镜子", "pos": Vector3(2.47, 1.6, 0.8), "size": Vector3(0.04, 1.2, 0.7), "color": Color("#9fb0b8")},
				],
				"hotspots": {
					"hs_key_tags": Vector3(2.0, 1.5, -2.8),
					"hs_night_log": Vector3(-1.2, 0.7, -2.6),
					"hs_receipts_drawer": Vector3(1.2, 0.6, 1.45),
					"hs_window_a": Vector3(-0.2, 1.5, -2.9),
					"hs_mirror_a": Vector3(2.35, 1.6, 0.8),
					"hs_keyring": Vector3(1.0, 0.8, 1.7),
				},
				"markers": {"door_push": [Vector3(0, 1.6, 2.6), Vector3(-0.5, 0.8, -1.5)]},
				"spawn": [Vector3(0, 0, 2.5), 0.0],
			}
		"corridor":
			return {
				"size": Vector3(1.8, 3.0, 18),
				"lights": [[Vector3(0, 1.8, -8.5), Color("#ffc98a"), 3.0]],
				"props": [],
				"hotspots": {"hs_study_door": Vector3(0, 1.2, -8.8)},
				"markers": {},
				"spawn": [Vector3(0, 0, 8.0), 0.0],
			}
		"typing_room":
			return {
				"size": Vector3(4.5, 3.0, 4),
				"lights": [[Vector3(1.8, 2.2, -1.9), Color("#ffe0b0"), 2.2], [Vector3(-1.0, 1.4, 0.5), Color("#ffc98a"), 0.8]],
				"props": [
					{"name": "打字桌左", "pos": Vector3(-0.9, 0.38, -1.0), "size": Vector3(1.1, 0.76, 0.6), "color": WOOD},
					{"name": "打字桌右", "pos": Vector3(0.9, 0.38, -1.0), "size": Vector3(1.1, 0.76, 0.6), "color": WOOD},
					{"name": "打字机左", "pos": Vector3(-0.9, 0.86, -1.0), "size": Vector3(0.4, 0.2, 0.35), "color": DARK},
					{"name": "打字机右", "pos": Vector3(0.9, 0.86, -1.0), "size": Vector3(0.4, 0.2, 0.35), "color": DARK},
					{"name": "抽屉柜", "pos": Vector3(1.9, 0.5, 1.2), "size": Vector3(0.5, 1.0, 0.8), "color": WOOD},
					{"name": "窗", "pos": Vector3(1.5, 1.7, -1.98), "size": Vector3(1.0, 1.2, 0.04), "color": Color("#1c2638")},
					{"name": "镜子", "pos": Vector3(-2.22, 1.6, 0.6), "size": Vector3(0.04, 1.1, 0.6), "color": Color("#9fb0b8")},
				],
				"hotspots": {
					"hs_platen": Vector3(-0.9, 1.0, -1.0),
					"hs_typewriter_pair": Vector3(0.9, 1.05, -0.95),
					"hs_calendar_letter": Vector3(-0.5, 0.85, -0.85),
					"hs_telegram_drafts": Vector3(1.9, 0.75, 0.75),
					"hs_window_b": Vector3(1.5, 1.6, -1.85),
					"hs_mirror_b": Vector3(-2.1, 1.6, 0.6),
				},
				"markers": {"door_push": [Vector3(0, 1.6, 1.8), Vector3(0, 0.9, -1.0)]},
				"spawn": [Vector3(0, 0, 1.6), 0.0],
			}
		"attic_stairs":
			return {
				"size": Vector3(1.6, 6.0, 6),
				"lights": [[Vector3(0, 4.6, -2.6), Color("#ffd28a"), 3.0]],
				"props": [
					{"name": "台阶1", "pos": Vector3(0, 0.1, 1.5), "size": Vector3(1.4, 0.2, 0.6), "color": WOOD},
					{"name": "台阶2", "pos": Vector3(0, 0.6, 0.9), "size": Vector3(1.4, 0.2, 0.6), "color": WOOD},
					{"name": "台阶3", "pos": Vector3(0, 1.1, 0.3), "size": Vector3(1.4, 0.2, 0.6), "color": WOOD},
					{"name": "台阶4", "pos": Vector3(0, 1.6, -0.3), "size": Vector3(1.4, 0.2, 0.6), "color": WOOD},
					{"name": "台阶5", "pos": Vector3(0, 2.1, -0.9), "size": Vector3(1.4, 0.2, 0.6), "color": WOOD},
					{"name": "台阶6", "pos": Vector3(0, 2.6, -1.5), "size": Vector3(1.4, 0.2, 0.6), "color": WOOD},
					{"name": "台阶7", "pos": Vector3(0, 3.1, -2.1), "size": Vector3(1.4, 0.2, 0.6), "color": WOOD},
					{"name": "门框光", "pos": Vector3(0, 4.3, -2.95), "size": Vector3(0.9, 2.0, 0.05), "color": Color("#ffe6b8")},
				],
				"hotspots": {},
				"markers": {"stairs_up": [Vector3(0, 0.9, 2.6), Vector3(0, 3.6, -2.6)]},
				"spawn": [Vector3(0, 0, 2.4), 0.0],
			}
		"billiard_room":
			return {
				"size": Vector3(6, 3.0, 5),
				"lights": [[Vector3(0, 2.3, 0), Color("#ffd9a0"), 3.0]],
				"props": [
					{"name": "台球桌", "pos": Vector3(0, 0.4, 0), "size": Vector3(2.6, 0.8, 1.4), "color": Color("#1f4a32")},
					{"name": "吊灯", "pos": Vector3(0, 2.5, 0), "size": Vector3(1.2, 0.15, 0.3), "color": BRASS},
					{"name": "记分黑板", "pos": Vector3(-2.97, 1.5, -1.0), "size": Vector3(0.04, 0.8, 1.0), "color": Color("#1b1d1c")},
					{"name": "边桌", "pos": Vector3(-2.4, 0.38, 0.6), "size": Vector3(0.8, 0.76, 0.6), "color": WOOD},
					{"name": "留声机", "pos": Vector3(2.5, 0.6, -1.8), "size": Vector3(0.5, 1.2, 0.5), "color": BRASS},
					{"name": "镜面墙", "pos": Vector3(0, 1.6, -2.47), "size": Vector3(3.0, 1.6, 0.04), "color": Color("#9fb0b8")},
					{"name": "窗", "pos": Vector3(2.97, 1.6, 1.0), "size": Vector3(0.04, 1.2, 1.0), "color": Color("#1c2638")},
				],
				"hotspots": {
					"hs_iou": Vector3(-2.4, 0.85, 0.6),
					"hs_morning_paper": Vector3(-2.2, 0.85, 0.9),
					"hs_gramophone": Vector3(2.5, 1.3, -1.6),
					"hs_mirror_c": Vector3(0, 1.6, -2.35),
					"hs_window_c": Vector3(2.85, 1.6, 1.0),
				},
				"markers": {"billiard_mid": [Vector3(2.0, 1.6, 2.0), Vector3(0, 0.8, 0)]},
				"spawn": [Vector3(0, 0, 2.0), 0.0],
			}
	return {}
