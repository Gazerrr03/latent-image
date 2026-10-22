"""阶段 F（Blender 侧可做的那一半）：胶囊通行体检。

    uv run --with numpy python scripts/07_walk_check.py

做法：把可行走区域按 Ø0.60 m 胶囊半径（0.30 m）腐蚀一遍，再在腐蚀后的区域里
从 S 门到北出口做 BFS。BFS 通 = 玩家贴不贴墙都能过去；返回腐蚀后的路径长度。
输出 review/walk_check.json。
"""
import json, math, sys
from collections import deque
from pathlib import Path
import numpy as np

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
import layout as LY

occ, d0, pts = LY.solve()
RES, ORIGIN = LY.RES, LY.ORIGIN
H, W = occ.shape
CAP_R = 0.30

# 腐蚀：一个格子可通过，当且仅当 0.30 m 圆周上 16 个采样点全在可行走区域内
free0 = ~occ.copy()
wide = free0.copy()
angles = [2 * math.pi * k / 16 for k in range(16)]
for r in (CAP_R, CAP_R * 0.5):
    for a in angles:
        di = int(round(math.cos(a) * r / RES))
        dj = int(round(math.sin(a) * r / RES))
        shifted = np.zeros_like(free0)
        si0, si1 = max(0, -di), min(W, W - di)
        sj0, sj1 = max(0, -dj), min(H, H - dj)
        shifted[sj0:sj1, si0:si1] = free0[sj0 + dj:sj1 + dj, si0 + di:si1 + di]
        wide &= shifted

def idx(x, y):
    return int(round((x - ORIGIN) / RES)), int(round((y - ORIGIN) / RES))

sx, sy = idx(*LY.DOORS['S'])
while not wide[sy, sx] and sy < H - 1:
    sy += 1
ex, ey = idx(*LY.DOORS['N'])
while not wide[ey, ex] and ey > 0:
    ey -= 1

dist = np.full((H, W), -1, np.int32)
if wide[sy, sx]:
    dist[sy, sx] = 0
    q = deque([(sx, sy)])
    while q:
        x, y = q.popleft()
        for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
            nx, ny = x + dx, y + dy
            if 0 <= nx < W and 0 <= ny < H and wide[ny, nx] and dist[ny, nx] < 0:
                dist[ny, nx] = dist[y, x] + 1
                q.append((nx, ny))

passable = bool(dist[ey, ex] >= 0)
route_len = float(dist[ey, ex]) * RES if passable else None
res = dict(capsule_diameter_m=0.60, capsule_radius_m=CAP_R,
           passable=passable, eroded_route_length_m=round(route_len, 2) if route_len else None,
           note='腐蚀后通行 = 贴墙 0.30 m 也能走通；原始最短路（贴角走）另见 layout.solve()')
out = ROOT / 'review' / 'walk_check.json'
json.dump(res, open(out, 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
print('WALK', res)
