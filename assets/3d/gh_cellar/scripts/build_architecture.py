import bpy
import bmesh
import math
import os
import random
from mathutils import Vector, Euler
import scene_lib as L
from scene_lib import RNG, MAT

# -----------------------------------------------------------------------------
# architectural shell
# -----------------------------------------------------------------------------

ROOM_W = 10.0
ROOM_D = 8.0
ROOM_H = 2.6
WALL_T = 0.22

C_ARCH = None
C_DETAIL = None


def build_floor(coll):
    # structural slab
    L.box("Floor slab", (ROOM_W + 0.6, ROOM_D + 0.6, 0.22),
          (0, 0, -0.16), MAT['grout'], coll, bevel=0.012)
    # irregular flagstones, laid in slightly uneven courses
    y = -ROOM_D / 2
    row = 0
    while y < ROOM_D / 2 - 0.04:
        h = RNG.uniform(0.52, 0.68)
        if y + h > ROOM_D / 2:
            h = ROOM_D / 2 - y
        x = -ROOM_W / 2
        stones = []
        while x < ROOM_W / 2 - 0.03:
            w = RNG.uniform(0.62, 1.16)
            if x + w > ROOM_W / 2:
                w = ROOM_W / 2 - x
            gap = RNG.uniform(0.012, 0.027)
            cx = x + w / 2
            cy = y + h / 2
            if w > 0.1 and h > 0.1:
                mat = MAT[f'stone_{RNG.randrange(5)}']
                obj = L.box(f"Flagstone {row:02d}.{len(stones):02d}",
                            (w - gap, h - gap, RNG.uniform(0.035, 0.065)),
                            (cx + RNG.uniform(-0.012, 0.012),
                             cy + RNG.uniform(-0.012, 0.012),
                             -0.025 + RNG.uniform(-0.006, 0.005)),
                            mat, coll, rot=(0, 0, RNG.uniform(-0.012, 0.012)),
                            bevel=0.006, segments=3)
                if RNG.random() < 0.28:
                    # a hairline crack
                    p0 = (cx - w*0.25, cy - h*0.2, 0.008)
                    p1 = (cx + w*0.16, cy + h*0.25, 0.009)
                    L.curve_tube(f"Crack {row:02d}.{len(stones):02d}", [p0, p1],
                                 0.0022, MAT['grout'], coll)
                stones.append(obj)
            x += w
        y += h
        row += 1
    # a couple of missing / sunken stones at the edges
    L.box("Sunken stone hole", (0.65, 0.42, 0.02), (-3.55, -2.1, -0.08),
          MAT['grout'], coll, bevel=0.01)

    # irregular damp / soot stains in the flagstones
    stains = [
        (-1.15, 0.15, 2.4, 1.9, 1), (0.90, -0.65, 1.6, 1.3, 2),
        (-3.65, -2.3, 1.25, 1.0, 3), (3.05, 1.5, 1.5, 1.25, 4),
        (2.45, -2.45, 1.15, 0.9, 5), (-4.15, 2.25, 1.05, 0.85, 6),
    ]
    for i, (x, y, w, h, seed) in enumerate(stains):
        _floor_stain(f"Floor grime {i}", x, y, w, h, MAT['grime'], coll, seed)
    # shallow, reflective damp patches
    for i, (x, y, w, h, seed) in enumerate([
        (-1.55, -2.10, 0.85, 0.55, 11),
        (2.45, -0.35, 0.70, 0.48, 12),
        (-3.40, 1.65, 0.55, 0.35, 13),
    ]):
        _floor_stain(f"Floor damp patch {i}", x, y, w, h, MAT['water'], coll, seed)


def _floor_stain(name, cx, cy, w, h, mat, coll, seed):
    rng = random.Random(seed)
    n = 22
    verts = []
    for i in range(n):
        a = 2*math.pi*i/n
        rr = 0.5 + rng.random()*0.5
        verts.append((cx + math.cos(a)*w*0.5*rr,
                      cy + math.sin(a)*h*0.5*rr,
                      0.006 + rng.random()*0.002))
    me = bpy.data.meshes.new(name)
    me.from_pydata(verts, [], [tuple(range(n))])
    me.update()
    me.materials.append(mat)
    obj = bpy.data.objects.new(name, me)
    coll.objects.link(obj)
    return obj


def _add_box_arrays(verts, faces, fmats, center, dims, mat_index, jitter=0.0):
    cx, cy, cz = center
    dx, dy, dz = dims
    x0, x1 = cx - dx/2, cx + dx/2
    y0, y1 = cy - dy/2, cy + dy/2
    z0, z1 = cz - dz/2, cz + dz/2
    i = len(verts)
    # slight local irregularity on the exposed face
    verts.extend([
        (x0, y0, z0), (x1, y0, z0), (x1, y1, z0), (x0, y1, z0),
        (x0, y0, z1), (x1, y0, z1), (x1, y1, z1), (x0, y1, z1)])
    quads = [(0, 3, 2, 1), (4, 5, 6, 7), (0, 1, 5, 4),
             (1, 2, 6, 5), (2, 3, 7, 6), (3, 0, 4, 7)]
    for q in quads:
        faces.append(tuple(i + k for k in q))
        fmats.append(mat_index)


def _brick_wall_mesh(name, axis, fixed, u0, u1, z0, z1, coll, skip=()):
    brick_l = 0.226
    brick_h = 0.069
    gap = 0.0105
    depth = 0.085
    step = brick_l + gap
    row_h = brick_h + gap
    rows = max(1, int((z1 - z0) / row_h))
    verts, faces, fmats = [], [], []
    mats = MAT['brick_list']
    outward = 1.0 if fixed > 0 else -1.0
    for row in range(rows):
        zc = z0 + row_h * (row + 0.5) + RNG.uniform(-0.0015, 0.0015)
        offset = (step * 0.5) if (row % 2) else 0.0
        u = u0 - offset - RNG.uniform(0.0, 0.01)
        while u < u1 - 0.02:
            uc = u + brick_l * 0.5
            if uc > u0 - 0.03 and uc < u1 + 0.03:
                skipped = False
                for su0, su1, sz0, sz1 in skip:
                    if su0 - 0.01 < uc < su1 + 0.01 and sz0 - 0.01 < zc < sz1 + 0.01:
                        skipped = True
                        break
                if not skipped and RNG.random() > 0.008:
                    bl = min(brick_l, u1 - u + 0.01)
                    if bl > 0.08:
                        dz = depth + RNG.uniform(-0.006, 0.004)
                        jitter = RNG.uniform(-0.0018, 0.0018)
                        if axis == 'x':
                            center = (uc + jitter, fixed + outward * dz * 0.5,
                                      zc + RNG.uniform(-0.0015, 0.0015))
                            dims = (bl, dz, brick_h)
                        else:
                            center = (fixed + outward * dz * 0.5,
                                      uc + jitter, zc + RNG.uniform(-0.0015, 0.0015))
                            dims = (dz, bl, brick_h)
                        _add_box_arrays(verts, faces, fmats, center, dims,
                                        RNG.randrange(len(mats)))
            u += step
    me = bpy.data.meshes.new(name)
    me.from_pydata(verts, [], faces)
    me.update()
    for m in mats:
        me.materials.append(m)
    for p, mi in zip(me.polygons, fmats):
        p.material_index = mi
    obj = bpy.data.objects.new(name, me)
    coll.objects.link(obj)
    bevel = obj.modifiers.new("brick_edge_bevel", 'BEVEL')
    bevel.width = 0.004
    bevel.segments = 2
    bevel.limit_method = 'ANGLE'
    bevel.angle_limit = math.radians(40)
    return obj


def _wall_backing(name, axis, fixed, coll):
    outward = 1.0 if fixed > 0 else -1.0
    # core sits behind the brickwork; a thin mortar bed fills the joints
    core_offset = 0.125
    if axis == 'x':
        L.box(name, (ROOM_W + WALL_T, WALL_T, ROOM_H + 0.1),
              (0, fixed + outward * (core_offset + WALL_T * 0.5), ROOM_H * 0.5),
              MAT['brick_mortar'], coll, bevel=0.0)
        L.box(name + " mortar bed", (ROOM_W + WALL_T, 0.024, ROOM_H + 0.05),
              (0, fixed + outward * 0.013, ROOM_H * 0.5),
              MAT['brick_mortar'], coll, bevel=0.0)
    else:
        L.box(name, (WALL_T, ROOM_D + WALL_T, ROOM_H + 0.1),
              (fixed + outward * (core_offset + WALL_T * 0.5), 0, ROOM_H * 0.5),
              MAT['brick_mortar'], coll, bevel=0.0)
        L.box(name + " mortar bed", (0.024, ROOM_D + WALL_T, ROOM_H + 0.05),
              (fixed + outward * 0.013, 0, ROOM_H * 0.5),
              MAT['brick_mortar'], coll, bevel=0.0)


def build_walls(coll):
    _wall_backing("North wall core", 'x', ROOM_D/2, coll)
    _wall_backing("South wall core", 'x', -ROOM_D/2, coll)
    _wall_backing("West wall core", 'y', -ROOM_W/2, coll)
    _wall_backing("East wall core", 'y', ROOM_W/2, coll)

    _brick_wall_mesh("North brick wall", 'x', ROOM_D/2, -ROOM_W/2, ROOM_W/2,
                     0.0, ROOM_H, coll)
    _brick_wall_mesh("South brick wall", 'x', -ROOM_D/2, -ROOM_W/2, ROOM_W/2,
                     0.0, ROOM_H, coll,
                     skip=[(1.15, 2.65, 0.0, 2.18)])
    _brick_wall_mesh("West brick wall", 'y', -ROOM_W/2, -ROOM_D/2, ROOM_D/2,
                     0.0, ROOM_H, coll)
    _brick_wall_mesh("East brick wall", 'y', ROOM_W/2, -ROOM_D/2, ROOM_D/2,
                     0.0, ROOM_H, coll)

    # corner posts and a few structural braces
    for sx in (-1, 1):
        for sy in (-1, 1):
            x = sx * (ROOM_W/2 - 0.11)
            y = sy * (ROOM_D/2 - 0.11)
            L.box(f"Corner post {sx}{sy}", (0.20, 0.20, ROOM_H + 0.04),
                  (x, y, ROOM_H/2), MAT['wood_beam'], coll, bevel=0.012)
            # iron strap and bolts near the top
            L.box(f"Corner strap {sx}{sy}", (0.205, 0.036, 0.16),
                  (x, y, 2.23), MAT['iron_dark'], coll, bevel=0.004)
            for t in (-0.045, 0.045):
                L.sphere(f"Strap bolt {sx}{sy}{t}", 0.013,
                         (x + t, y - 0.021, 2.23), MAT['iron'], coll,
                         scale=(1, 0.35, 1), segments=12, rings=8)

    # ceiling-line wall plate on north and west (reads as old timber frame)
    L.box("North wall plate", (ROOM_W, 0.15, 0.18),
          (0, ROOM_D/2 - 0.10, ROOM_H - 0.09), MAT['wood_beam'], coll, bevel=0.012)
    L.box("West wall plate", (0.15, ROOM_D, 0.18),
          (-ROOM_W/2 + 0.10, 0, ROOM_H - 0.09), MAT['wood_beam'], coll, bevel=0.012)


def _wall_point(axis, fixed, u, z, out=0.0):
    outward = 1.0 if fixed > 0 else -1.0
    if axis == 'x':
        return (u, fixed + outward * out, z)
    return (fixed + outward * out, u, z)


def wall_patch(name, axis, fixed, uc, zc, w, h, mat, coll, seed=1):
    rng = random.Random(seed)
    n = 18
    verts = []
    for i in range(n):
        a = 2 * math.pi * i / n
        rr = 0.65 + rng.random() * 0.45
        u = uc + math.cos(a) * w * 0.5 * rr
        z = zc + math.sin(a) * h * 0.5 * rr
        verts.append(_wall_point(axis, fixed, u, z, 0.008 + rng.random() * 0.006))
    me = bpy.data.meshes.new(name)
    me.from_pydata(verts, [], [tuple(range(n))])
    me.update()
    me.materials.append(mat)
    obj = bpy.data.objects.new(name, me)
    coll.objects.link(obj)
    sol = obj.modifiers.new("patch_thickness", 'SOLIDIFY')
    sol.thickness = 0.008
    sol.offset = 0.0
    # give the patch a faint beveled edge
    bev = obj.modifiers.new("patch_edge", 'BEVEL')
    bev.width = 0.003
    bev.segments = 2
    return obj


def soot_streak(name, axis, fixed, uc, zc, w, h, coll, seed=1):
    rng = random.Random(seed)
    # tapered, wavy polygon running downward
    n = 9
    left = []
    right = []
    for i in range(n):
        t = i / (n - 1)
        z = zc + h * (0.5 - t)
        ww = w * (1.0 - 0.55 * t) * (0.7 + 0.3 * math.sin(t * 8 + seed))
        left.append(_wall_point(axis, fixed, uc - ww * 0.5 + math.sin(t*7+seed)*0.012, z, 0.012))
        right.append(_wall_point(axis, fixed, uc + ww * 0.5 + math.sin(t*6+seed)*0.010, z, 0.012))
    verts = left + list(reversed(right))
    me = bpy.data.meshes.new(name)
    me.from_pydata(verts, [], [tuple(range(len(verts)))])
    me.update()
    me.materials.append(MAT['soot'])
    obj = bpy.data.objects.new(name, me)
    coll.objects.link(obj)
    sol = obj.modifiers.new("stain_thickness", 'SOLIDIFY')
    sol.thickness = 0.001
    return obj


def build_wall_patina(coll):
    # peeling plaster fields, arranged asymmetrically
    patches = [
        ('x', ROOM_D/2, -4.10, 2.16, 0.88, 0.48, MAT['plaster'], 11),
        ('x', ROOM_D/2, -2.25, 2.32, 1.05, 0.46, MAT['plaster'], 12),
        ('x', ROOM_D/2, 1.55, 2.36, 1.45, 0.38, MAT['plaster_grey'], 13),
        ('x', ROOM_D/2, 3.70, 2.18, 0.90, 0.44, MAT['plaster'], 14),
        ('x', -ROOM_D/2, -4.30, 2.10, 1.15, 0.50, MAT['plaster_grey'], 15),
        ('y', -ROOM_W/2, -3.55, 2.30, 1.15, 0.42, MAT['plaster'], 16),
        ('y', -ROOM_W/2, -1.65, 2.25, 0.82, 0.42, MAT['plaster_ochre'], 17),
        ('y', -ROOM_W/2, 2.55, 2.26, 1.05, 0.44, MAT['plaster_grey'], 18),
        ('y', ROOM_W/2, -3.45, 2.32, 0.95, 0.36, MAT['plaster'], 19),
        ('y', ROOM_W/2, -0.60, 2.24, 0.88, 0.38, MAT['plaster_ochre'], 20),
        ('y', ROOM_W/2, 2.55, 2.32, 1.00, 0.40, MAT['plaster_grey'], 21),
    ]
    for i, (axis, fixed, uc, zc, w, h, mat, seed) in enumerate(patches):
        wall_patch(f"Peeling plaster {i:02d}", axis, fixed, uc, zc, w, h, mat, coll, seed)

    # soot runs down from the ceiling
    streaks = [
        ('x', ROOM_D/2, -3.8, 2.25, 0.55, 0.70, 31),
        ('x', ROOM_D/2, -0.4, 2.38, 0.42, 0.55, 32),
        ('x', ROOM_D/2, 2.4, 2.30, 0.50, 0.66, 33),
        ('x', -ROOM_D/2, 0.2, 2.35, 0.42, 0.56, 34),
        ('y', -ROOM_W/2, -2.4, 2.33, 0.42, 0.58, 35),
        ('y', -ROOM_W/2, 1.1, 2.36, 0.36, 0.52, 36),
        ('y', ROOM_W/2, -1.8, 2.35, 0.38, 0.56, 37),
        ('y', ROOM_W/2, 2.9, 2.32, 0.44, 0.50, 38),
    ]
    for i, (axis, fixed, uc, zc, w, h, seed) in enumerate(streaks):
        soot_streak(f"Soot streak {i:02d}", axis, fixed, uc, zc, w, h, coll, seed)

    # lime bloom / salt streaks
    for i, (axis, fixed, uc, zc, w, h, seed) in enumerate([
        ('x', ROOM_D/2, 2.9, 1.55, 0.30, 0.58, 41),
        ('y', -ROOM_W/2, 0.1, 1.30, 0.26, 0.70, 42),
        ('y', ROOM_W/2, 0.7, 1.20, 0.24, 0.62, 43),
    ]):
        wall_patch(f"Lime bloom {i:02d}", axis, fixed, uc, zc, w, h,
                   MAT['plaster_grey'], coll, seed)


def build_ceiling(coll):
    holes = [
        (-0.82, 0.82, 0.04, 1.27),      # skylight
        (3.42, 4.56, -1.86, -0.84),     # attic hatch
    ]
    board_w = 0.185
    y = -ROOM_D/2
    while y < ROOM_D/2 - 0.02:
        w = min(board_w, ROOM_D/2 - y)
        y0, y1 = y, y + w
        intervals = [(-ROOM_W/2, ROOM_W/2)]
        for hx0, hx1, hy0, hy1 in holes:
            if y1 > hy0 and y0 < hy1:
                new = []
                for a, b in intervals:
                    if hx1 <= a or hx0 >= b:
                        new.append((a, b))
                    else:
                        if hx0 > a:
                            new.append((a, hx0))
                        if hx1 < b:
                            new.append((hx1, b))
                intervals = new
        for k, (a, b) in enumerate(intervals):
            if b - a > 0.1:
                L.box(f"Ceiling board {y:+.2f}.{k}", (b-a-0.005, w-0.008, 0.045),
                      ((a+b)/2, (y0+y1)/2, 2.655 + RNG.uniform(-0.002, 0.002)),
                      MAT['wood_floor'], coll, bevel=0.002)
        y += w

    # primary joists, positioned to frame the two openings
    joist_ys = [-3.55, -2.72, -1.94, -0.56, 0.02, 1.34, 2.12, 2.92, 3.62]
    for i, jy in enumerate(joist_ys):
        L.box(f"Ceiling joist {i:02d}", (ROOM_W, 0.155, 0.225),
              (0, jy, 2.48), MAT['wood_beam'], coll, bevel=0.014)
        # rough iron joist straps
        if i in (1, 4, 7):
            for sx in (-3.1, 3.0):
                L.box(f"Joist strap {i}.{sx}", (0.08, 0.17, 0.24),
                      (sx, jy, 2.48), MAT['iron_dark'], coll, bevel=0.004)

    # big binding beams over the room
    for i, bx in enumerate([-2.82, 2.38]):
        L.box(f"Binding beam {i}", (0.24, ROOM_D, 0.30),
              (bx, 0, 2.39), MAT['wood_beam'], coll, bevel=0.016)
        for sy in (-3.0, -1.2, 1.2, 3.0):
            L.box(f"Beam strap {i}.{sy}", (0.27, 0.08, 0.32),
                  (bx, sy, 2.39), MAT['iron_dark'], coll, bevel=0.005)

    # headers around openings
    for hx0, hx1, hy0, hy1 in holes:
        width = 0.16
        L.box("Skylight header", (hx1-hx0+0.4, width, 0.24),
              ((hx0+hx1)/2, hy0 - 0.06, 2.46), MAT['wood_beam'], coll, bevel=0.012)
        L.box("Skylight header", (hx1-hx0+0.4, width, 0.24),
              ((hx0+hx1)/2, hy1 + 0.06, 2.46), MAT['wood_beam'], coll, bevel=0.012)
        L.box("Skylight header", (width, hy1-hy0, 0.24),
              (hx0 - 0.06, (hy0+hy1)/2, 2.46), MAT['wood_beam'], coll, bevel=0.012)
        L.box("Skylight header", (width, hy1-hy0, 0.24),
              (hx1 + 0.06, (hy0+hy1)/2, 2.46), MAT['wood_beam'], coll, bevel=0.012)

    # skylight shaft: plastered reveal, timber curb, old glazing
    hx0, hx1, hy0, hy1 = holes[0]
    for sx in (-1, 1):
        L.box("Skylight reveal", (0.10, hy1-hy0+0.3, 0.66),
              ((hx0 if sx < 0 else hx1) + sx*0.01, (hy0+hy1)/2, 2.94),
              MAT['plaster_grey'], coll, bevel=0.004)
    for sy in (-1, 1):
        L.box("Skylight reveal", (hx1-hx0+0.3, 0.10, 0.66),
              ((hx0+hx1)/2, (hy0 if sy < 0 else hy1) + sy*0.01, 2.94),
              MAT['plaster_grey'], coll, bevel=0.004)
    L.box("Skylight curb north", (hx1-hx0+0.34, 0.12, 0.12),
          ((hx0+hx1)/2, hy1+0.04, 2.64), MAT['wood_beam'], coll, bevel=0.008)
    L.box("Skylight curb south", (hx1-hx0+0.34, 0.12, 0.12),
          ((hx0+hx1)/2, hy0-0.04, 2.64), MAT['wood_beam'], coll, bevel=0.008)
    # glass at 3.26, 2 x 2 panes
    gz = 3.26
    for i in range(2):
        for j in range(2):
            cw = (hx1-hx0)/2
            ch = (hy1-hy0)/2
            cx = hx0 + cw*(i+0.5)
            cy = hy0 + ch*(j+0.5)
            L.plane(f"Skylight glass {i}{j}", cw*0.94, ch*0.94,
                    (cx, cy, gz), MAT['glass_window'], coll,
                    rot=(0, 0, 0))
    # glazing bars
    for i in (0, 1, 2):
        x = hx0 + (hx1-hx0)*i/2
        L.box(f"Skylight muntin x{i}", (0.035, hy1-hy0, 0.045),
              (x, (hy0+hy1)/2, gz), MAT['iron_dark'], coll, bevel=0.003)
        y = hy0 + (hy1-hy0)*i/2
        L.box(f"Skylight muntin y{i}", (hx1-hx0, 0.035, 0.045),
              ((hx0+hx1)/2, y, gz), MAT['iron_dark'], coll, bevel=0.003)

    # hatch shaft and open lid
    hx0, hx1, hy0, hy1 = holes[1]
    for sx in (-1, 1):
        L.box("Hatch reveal", (0.12, hy1-hy0+0.25, 0.45),
              ((hx0 if sx < 0 else hx1) + sx*0.01, (hy0+hy1)/2, 2.82),
              MAT['wood_beam'], coll, bevel=0.006)
    for sy in (-1, 1):
        L.box("Hatch reveal", (hx1-hx0+0.25, 0.12, 0.45),
              ((hx0+hx1)/2, (hy0 if sy < 0 else hy1) + sy*0.01, 2.82),
              MAT['wood_beam'], coll, bevel=0.006)
    # hatch door swung up and to the side
    hinge = Vector((hx1 + 0.05, hy1 + 0.04, 3.02))
    hd = L.box("Open hatch lid", (hx1-hx0, hy1-hy0, 0.055),
               (0, 0, 0), MAT['wood_floor'], coll, bevel=0.008)
    hd.rotation_euler = (math.radians(-58), 0, math.radians(-8))
    hd.location = hinge + Vector((-0.02, 0.42, 0.48))
    # simple iron hatch hinges
    for t in (-0.3, 0.3):
        L.box("Hatch hinge", (0.20, 0.03, 0.05),
              (hx1 - 0.12, hy1 + 0.04 + t*0.4, 3.02), MAT['iron'], coll, bevel=0.003)

    # a few cobweb strands in the ceiling corners
    for i, (start, end, r) in enumerate([
        ((-4.82, 3.82, 2.5), (-4.1, 3.82, 2.2), 0.003),
        ((-4.82, 3.82, 2.5), (-4.82, 3.05, 2.2), 0.0025),
        ((4.82, 3.82, 2.5), (4.2, 3.82, 2.25), 0.0025),
        ((4.82, -3.82, 2.5), (4.25, -3.82, 2.22), 0.0025),
    ]):
        L.curve_tube(f"Cobweb {i}", [start, end], r, MAT['dust'], coll)


def build_door(coll):
    # heavy plank door set into the south wall, slightly ajar
    x0, x1 = 1.18, 2.64
    z0, z1 = 0.02, 2.14
    L.box("Door frame left", (0.14, 0.20, z1-z0+0.10),
          (x0-0.05, -3.94, (z0+z1)/2), MAT['wood_door'], coll, bevel=0.012)
    L.box("Door frame right", (0.14, 0.20, z1-z0+0.10),
          (x1+0.05, -3.94, (z0+z1)/2), MAT['wood_door'], coll, bevel=0.012)
    L.box("Door lintel", (x1-x0+0.28, 0.22, 0.16),
          ((x0+x1)/2, -3.94, z1+0.06), MAT['wood_door'], coll, bevel=0.014)
    L.box("Door threshold", (x1-x0+0.30, 0.34, 0.10),
          ((x0+x1)/2, -3.93, 0.03), MAT['stone_0'], coll, bevel=0.008)
    # door slab is built around a pivot so it can be ajar
    door = L.box("Darkroom door", (x1-x0-0.05, 0.065, z1-z0-0.04),
                 (0, 0, 0), MAT['wood_door'], coll, bevel=0.009)
    pivot = Vector((x0 + 0.04, -3.99, (z0+z1)/2))
    door.location = pivot + Vector(((x1-x0-0.05)/2, 0.04, 0))
    door.rotation_mode = 'XYZ'
    door.rotation_euler = (0, 0, math.radians(-7.0))
    # panels / braces on the door
    for k, x in enumerate([x0+0.28, x0+0.74, x0+1.20]):
        L.box(f"Door plank seam {k}", (0.012, 0.018, z1-z0-0.15),
              (x, -3.935, (z0+z1)/2), MAT['iron_dark'], coll, bevel=0.003)
    for z in (0.48, 1.12, 1.72):
        L.box("Door strap", (x1-x0-0.16, 0.025, 0.075),
              ((x0+x1)/2, -3.925, z), MAT['iron_dark'], coll, bevel=0.004)
        for x in (x0+0.18, x1-0.18):
            L.sphere("Door rivet", 0.012, (x, -3.91, z), MAT['iron'], coll,
                     scale=(1, 0.4, 1), segments=12, rings=8)
    L.cylinder("Door handle", 0.035, 0.05, (x1-0.24, -3.89, 1.05),
               MAT['brass_dark'], coll, rot=(math.pi/2, 0, 0), verts=20)
    L.sphere("Door knob", 0.045, (x1-0.24, -3.86, 1.05), MAT['brass'], coll,
             segments=20, rings=12)
    L.box("Door lock plate", (0.09, 0.028, 0.18), (x1-0.24, -3.925, 0.92),
          MAT['brass_dark'], coll, bevel=0.006)
    # little darkroom sign
    if 'label_darkroom' in MAT:
        L.plane("Darkroom door sign", 0.52, 0.24, (1.90, -3.885, 1.63),
                MAT['label_darkroom'], coll, rot=(-math.pi/2, 0, 0))


def build_architecture():
    coll = L.collection("Architecture")
    build_floor(coll)
    build_walls(coll)
    build_wall_patina(coll)
    build_ceiling(coll)
    build_door(coll)
    return coll
