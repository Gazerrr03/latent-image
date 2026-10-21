import bpy
import bmesh
import math
import os
import random
from mathutils import Vector, Euler
import scene_lib as L
from scene_lib import RNG, MAT

# -----------------------------------------------------------------------------
# central workbench and hero camera
# -----------------------------------------------------------------------------

def build_workbench(coll):
    cx, cy = 0.05, 0.72
    top_z = 0.82
    # table top: six uneven old boards
    board_w = 0.205
    y0 = cy - 0.62
    bench_mats = [MAT['wood_bench'], MAT['wood_bench_2'], MAT['wood_bench_3']]
    for i in range(6):
        w = board_w + RNG.uniform(-0.012, 0.012)
        L.box(f"Bench top board {i}", (3.45 + RNG.uniform(-0.04, 0.04), w, 0.062),
              (cx + RNG.uniform(-0.015, 0.015), y0 + board_w*(i+0.5), top_z - 0.031),
              bench_mats[i % 3], coll, rot=(0, 0, RNG.uniform(-0.002, 0.002)),
              bevel=0.006)
        # dark seam between boards
        if i < 5:
            L.box(f"Bench seam {i}", (3.4, 0.008, 0.004),
                  (cx, y0 + board_w*(i+1), top_z - 0.003),
                  MAT['iron_dark'], coll, bevel=0.001)
    # breadboard ends
    L.box("Bench end left", (0.075, 1.28, 0.085), (cx-1.75, cy, top_z-0.03),
          MAT['wood_dark'], coll, bevel=0.008)
    L.box("Bench end right", (0.075, 1.28, 0.085), (cx+1.75, cy, top_z-0.03),
          MAT['wood_dark'], coll, bevel=0.008)
    # legs and stretchers
    for sx in (-1, 1):
        for sy in (-1, 1):
            x = cx + sx*1.53
            y = cy + sy*0.47
            L.box(f"Bench leg {sx}{sy}", (0.12, 0.12, 0.78),
                  (x, y, 0.39), MAT['wood_bench'], coll, bevel=0.008)
            L.box(f"Bench foot {sx}{sy}", (0.18, 0.18, 0.06),
                  (x, y, 0.03), MAT['wood_dark'], coll, bevel=0.006)
        L.box(f"Bench long apron {sx}{sy}", (3.3, 0.075, 0.14),
              (cx, cy + sy*0.47, 0.69), MAT['wood_bench'], coll, bevel=0.007)
    for sx in (-1, 1):
        L.box(f"Bench end apron {sx}", (0.07, 1.0, 0.13),
              (cx + sx*1.52, cy, 0.69), MAT['wood_bench'], coll, bevel=0.007)
    L.box("Bench stretcher", (2.85, 0.075, 0.10), (cx, cy, 0.25),
          MAT['wood_dark'], coll, bevel=0.006)
    # rough shelf under bench, with a crate and paper package
    L.box("Bench under shelf", (2.6, 0.72, 0.045), (cx, cy, 0.30),
          MAT['wood_dark'], coll, bevel=0.005)
    L.box("Under bench crate", (0.58, 0.42, 0.30), (0.78, cy, 0.49),
          MAT['wood_crate'], coll, rot=(0, 0, 0.05), bevel=0.007)
    L.box("Under bench package", (0.48, 0.35, 0.12), (-0.72, cy, 0.36),
          MAT['card'], coll, rot=(0, 0, -0.08), bevel=0.004)
    # a couple of nails / stains on the top
    L.curve_tube("Bench crack 1", [(cx-1.1, cy-0.45, top_z+0.002),
                                   (cx-0.7, cy-0.32, top_z+0.002),
                                   (cx-0.2, cy-0.36, top_z+0.002)],
                 0.0022, MAT['grout'], coll)
    L.curve_tube("Bench crack 2", [(cx+0.7, cy+0.5, top_z+0.002),
                                   (cx+0.95, cy+0.36, top_z+0.002),
                                   (cx+1.4, cy+0.3, top_z+0.002)],
                 0.0018, MAT['grout'], coll)
    for i in range(7):
        L.sphere(f"Bench nail {i}", 0.008,
                 (cx + RNG.uniform(-1.55, 1.55), cy + RNG.uniform(-0.5, 0.5), top_z+0.002),
                 MAT['iron_dark'], coll, scale=(1, 1, 0.3), segments=10, rings=6)
    # cup rings, chemical stains and old scratches on the working top
    L.torus("Cup ring stain", 0.078, 0.0032, (1.12, cy + 0.30, top_z + 0.003),
            MAT['grout'], coll, major_seg=40, minor_seg=6)
    L.torus("Cup ring stain 2", 0.062, 0.002, (-0.96, cy - 0.33, top_z + 0.003),
            MAT['grout'], coll, major_seg=36, minor_seg=6)
    _table_stain("Chemical spill", 0.55, cy - 0.30, 0.52, 0.30, MAT['grime'], coll, 201)
    _table_stain("Chemical spill 2", 1.35, cy + 0.05, 0.38, 0.24, MAT['grime'], coll, 202)
    for i, pts in enumerate([
        [(-1.3, cy-0.2, top_z+0.003), (-0.6, cy-0.12, top_z+0.003), (0.1, cy-0.18, top_z+0.003)],
        [(0.7, cy+0.2, top_z+0.003), (1.0, cy+0.08, top_z+0.003), (1.4, cy+0.12, top_z+0.003)],
        [(-0.2, cy+0.45, top_z+0.003), (0.2, cy+0.38, top_z+0.003), (0.5, cy+0.42, top_z+0.003)],
    ]):
        L.curve_tube(f"Table scratch {i}", pts, 0.0018, MAT['grout'], coll)
    # worn front edge, knots and paint flecks
    L.box("Bench worn front edge", (3.42, 0.018, 0.014),
          (cx, cy - 0.618, top_z - 0.004), MAT['wood_light'], coll, bevel=0.003)
    L.box("Bench worn back edge", (3.42, 0.014, 0.010),
          (cx, cy + 0.618, top_z - 0.003), MAT['wood_light'], coll, bevel=0.002)
    for i, (x, y) in enumerate([(-1.25, cy+0.10), (0.35, cy-0.43), (1.15, cy+0.36)]):
        L.sphere(f"Bench knot {i}", 0.024, (x, y, top_z + 0.001),
                 MAT['wood_dark'], coll, scale=(1.4, 0.8, 0.10),
                 segments=16, rings=8)
    for i in range(22):
        x = RNG.uniform(-1.62, 1.62)
        y = RNG.uniform(-0.58, 0.58) + cy
        L.sphere(f"Paint fleck {i}", RNG.uniform(0.002, 0.006),
                 (x, y, top_z + 0.002), MAT['grout'] if i % 3 else MAT['moss'],
                 coll, scale=(1.5, 1.0, 0.12), segments=8, rings=5)


def _table_stain(name, cx, cy, w, h, mat, coll, seed):
    rng = random.Random(seed)
    n = 18
    verts = []
    for i in range(n):
        a = 2*math.pi*i/n
        rr = 0.55 + rng.random()*0.45
        verts.append((cx + math.cos(a)*w*0.5*rr,
                      cy + math.sin(a)*h*0.5*rr,
                      0.825))
    me = bpy.data.meshes.new(name)
    me.from_pydata(verts, [], [tuple(range(n))])
    me.update()
    me.materials.append(mat)
    obj = bpy.data.objects.new(name, me)
    coll.objects.link(obj)
    return obj


def make_bellows(name, cx, body_z, front_y, rear_y, w_front, h_front,
                 w_rear, h_rear, coll):
    """A single tapered concertina mesh with alternating pleat peaks. This
    reads as leather bellows rather than a stack of boxes."""
    n = 21
    rings = []
    for i in range(n):
        t = i / (n - 1)
        y = front_y + (rear_y - front_y) * t
        w = w_front + (w_rear - w_front) * t
        h = h_front + (h_rear - h_front) * t
        if i % 2:
            w *= 0.76
            h *= 0.74
        y += (0.004 if i % 2 else -0.004)
        rings.append((y, w, h))
    verts = []
    for y, w, h in rings:
        verts.extend([
            (cx - w/2, y, body_z + h/2),
            (cx + w/2, y, body_z + h/2),
            (cx + w/2, y, body_z - h/2),
            (cx - w/2, y, body_z - h/2),
        ])
    faces = []
    fmats = []
    for i in range(n - 1):
        a = i * 4
        b = (i + 1) * 4
        quads = [(a+0, a+1, b+1, b+0),
                 (a+1, a+2, b+2, b+1),
                 (a+2, a+3, b+3, b+2),
                 (a+3, a+0, b+0, b+3)]
        for q in quads:
            faces.append(q)
            fmats.append(0)
    me = bpy.data.meshes.new(name)
    me.from_pydata(verts, [], faces)
    me.update()
    me.materials.append(MAT['bellows'])
    for p in me.polygons:
        p.material_index = 0
    obj = bpy.data.objects.new(name, me)
    coll.objects.link(obj)
    return obj


def build_hero_camera(coll):
    cx, cy = 0.36, 0.64
    base_z = 0.888
    # wooden camera bed and brass tracks
    L.box("Camera bed", (0.70, 0.88, 0.075), (cx, cy, base_z),
          MAT['wood_mahogany'], coll, bevel=0.012)
    for sx in (-1, 1):
        L.box("Camera bed rail", (0.024, 0.84, 0.018),
              (cx + sx*0.26, cy, base_z + 0.046), MAT['brass_dark'], coll, bevel=0.003)
    L.box("Camera bed front lip", (0.72, 0.045, 0.045),
          (cx, cy - 0.43, base_z + 0.035), MAT['wood_mahogany'], coll, bevel=0.006)
    L.box("Camera bed rear lip", (0.72, 0.045, 0.045),
          (cx, cy + 0.43, base_z + 0.035), MAT['wood_mahogany'], coll, bevel=0.006)
    # rear standard / body
    rear_y = cy + 0.25
    body_z = base_z + 0.27
    L.box("Camera rear body", (0.40, 0.19, 0.43), (cx, rear_y, body_z),
          MAT['wood_mahogany'], coll, bevel=0.014)
    L.box("Camera rear frame top", (0.44, 0.05, 0.055),
          (cx, rear_y - 0.01, body_z + 0.225), MAT['wood_mahogany'], coll, bevel=0.008)
    L.box("Camera rear frame bottom", (0.44, 0.05, 0.055),
          (cx, rear_y - 0.01, body_z - 0.225), MAT['wood_mahogany'], coll, bevel=0.008)
    for sx in (-1, 1):
        L.box("Camera rear frame side", (0.045, 0.05, 0.45),
              (cx + sx*0.20, rear_y - 0.01, body_z), MAT['wood_mahogany'], coll, bevel=0.008)
    # ground glass
    L.box("Camera ground glass", (0.31, 0.012, 0.36),
          (cx, rear_y + 0.095, body_z), MAT['glass'], coll, bevel=0.002)
    L.box("Camera ground glass back", (0.34, 0.018, 0.39),
          (cx, rear_y + 0.108, body_z), MAT['wood_dark'], coll, bevel=0.004)
    # front standard
    front_y = cy - 0.27
    L.box("Camera front standard", (0.34, 0.05, 0.34), (cx, front_y, body_z),
          MAT['wood_mahogany'], coll, bevel=0.009)
    L.box("Camera front standard lip", (0.37, 0.035, 0.06),
          (cx, front_y - 0.035, body_z + 0.16), MAT['brass_dark'], coll, bevel=0.004)
    # bellows: tightly overlapping pleat sections, tapering toward the front
    n = 14
    y_start, y_end = front_y + 0.03, rear_y - 0.09
    for i in range(n):
        t = i / (n - 1)
        y = y_start + (y_end - y_start) * t
        w = 0.275 + 0.065 * t
        h = 0.300 + 0.085 * t
        if i % 2:
            w *= 0.970
            h *= 0.970
        L.box(f"Camera bellows pleat {i}", (w, 0.088, h),
              (cx, y, body_z), MAT['bellows'], coll, bevel=0.003)
    # brass corner fittings
    for sx in (-1, 1):
        for sz in (-1, 1):
            L.box("Camera body corner", (0.036, 0.20, 0.036),
                  (cx + sx*0.205, rear_y, body_z + sz*0.205), MAT['brass_dark'], coll, bevel=0.004)
            L.sphere("Camera knob", 0.025,
                     (cx + sx*0.235, rear_y + 0.02, body_z + sz*0.065),
                     MAT['brass'], coll, scale=(0.8, 0.8, 0.5), segments=16, rings=10)
    # lens assembly, axis along Y
    lens_y = front_y - 0.10
    L.cylinder("Lens mount", 0.128, 0.055, (cx, lens_y + 0.04, body_z),
               MAT['brass_dark'], coll, rot=(math.pi/2, 0, 0), verts=48, bevel=0.006)
    L.cylinder("Lens barrel", 0.098, 0.115, (cx, lens_y - 0.02, body_z),
               MAT['brass_dark'], coll, rot=(math.pi/2, 0, 0), verts=48)
    L.cylinder("Lens front ring", 0.105, 0.025, (cx, lens_y - 0.082, body_z),
               MAT['brass'], coll, rot=(math.pi/2, 0, 0), verts=48, bevel=0.004)
    L.cylinder("Lens inner barrel", 0.077, 0.035, (cx, lens_y - 0.102, body_z),
               MAT['iron_dark'], coll, rot=(math.pi/2, 0, 0), verts=48)
    L.cylinder("Lens glass", 0.069, 0.015, (cx, lens_y - 0.112, body_z),
               MAT['lens_glass'], coll, rot=(math.pi/2, 0, 0), verts=48)
    L.torus("Lens rim", 0.091, 0.007, (cx, lens_y - 0.092, body_z),
            MAT['brass'], coll, rot=(math.pi/2, 0, 0), major_seg=48, minor_seg=10)
    # small red safelight on camera right
    L.cylinder("Camera safelight housing", 0.038, 0.075,
               (cx + 0.31, front_y + 0.10, body_z + 0.02),
               MAT['iron_dark'], coll, rot=(0, math.pi/2, 0), verts=24, bevel=0.004)
    L.sphere("Camera safelight glow", 0.033,
             (cx + 0.352, front_y + 0.10, body_z + 0.02),
             MAT['red_bulb'], coll, scale=(0.5, 1, 1), segments=20, rings=12)
    # dark cloth: a large hanging tail behind the ground glass
    tail = L.grid_cloth("Camera dark cloth tail", 0.74, 0.76,
                        (cx - 0.01, rear_y + 0.19, body_z - 0.06), MAT['cloth_dark'], coll,
                        rot=(math.radians(5), math.radians(-2), math.radians(1)),
                        nx=24, nz=30, amp=0.06, freq=(3.2, 3.8),
                        thickness=0.004, seed=72)
    # a few film holders leaning on the table
    for i, (x, y, rz) in enumerate([(0.82, cy - 0.18, 0.18), (0.90, cy - 0.05, 0.08),
                                    (-0.15, cy + 0.41, -0.12)]):
        h = L.box(f"Film holder {i}", (0.24, 0.035, 0.27), (x, y, base_z + 0.15),
                  MAT['wood_dark'], coll, rot=(0.16, 0, rz), bevel=0.006)
        L.box(f"Film holder dark slide {i}", (0.20, 0.004, 0.22),
              (x, y - 0.021, base_z + 0.15), MAT['leather_dark'], coll,
              rot=(0.16, 0, rz), bevel=0.001)
        L.box(f"Film holder handle {i}", (0.06, 0.012, 0.025),
              (x + 0.10, y - 0.021, base_z + 0.28), MAT['brass_dark'], coll,
              rot=(0.16, 0, rz), bevel=0.002)
    # engraved brass nameplate on the front standard
    if 'label_camera' in MAT:
        L.plane("Camera nameplate", 0.19, 0.06,
                (cx, front_y - 0.058, body_z - 0.095), MAT['label_camera'], coll,
                rot=(math.pi/2, 0, 0))
    # cable release
    L.curve_tube("Cable release",
                 [(cx + 0.14, front_y - 0.02, body_z - 0.15),
                  (cx + 0.28, front_y + 0.08, body_z - 0.22),
                  (cx + 0.35, front_y + 0.30, body_z - 0.35),
                  (cx + 0.42, front_y + 0.52, base_z + 0.05)],
                 0.006, MAT['leather_dark'], coll)


def build_lantern(coll):
    x, y = -1.18, 0.62
    z0 = 0.852
    # brass base
    L.lathe("Lantern base", [(0.0, 0.0), (0.11, 0.0), (0.12, 0.018), (0.10, 0.035),
                             (0.085, 0.045), (0.08, 0.075), (0.095, 0.09),
                             (0.075, 0.105), (0.045, 0.12), (0.035, 0.14),
                             (0.0, 0.14)],
            (x, y, z0), MAT['brass'], coll, segments=48)
    # glass chimney
    L.lathe("Lantern chimney", [(0.065, 0.12), (0.09, 0.16), (0.10, 0.22),
                                 (0.102, 0.30), (0.095, 0.36), (0.065, 0.405),
                                 (0.055, 0.415), (0.055, 0.425)],
            (x, y, z0), MAT['glass'], coll, segments=48)
    # flame
    L.sphere("Lantern flame", 0.018, (x, y, z0 + 0.235), MAT['flame'], coll,
             scale=(1.0, 1.0, 2.2), segments=16, rings=12)
    L.lathe("Lantern wick", [(0.012, 0.0), (0.012, 0.055), (0.0, 0.06)],
            (x, y, z0 + 0.135), MAT['iron_dark'], coll, segments=16)
    # top cap and wire guard
    L.lathe("Lantern cap", [(0.0, 0.0), (0.075, 0.0), (0.095, 0.02),
                             (0.08, 0.05), (0.055, 0.07), (0.0, 0.07)],
            (x, y, z0 + 0.428), MAT['brass'], coll, segments=40)
    L.torus("Lantern guard top", 0.072, 0.005, (x, y, z0 + 0.47),
            MAT['brass_dark'], coll, major_seg=36, minor_seg=8)
    L.torus("Lantern guard bottom", 0.108, 0.006, (x, y, z0 + 0.115),
            MAT['brass_dark'], coll, major_seg=40, minor_seg=8)
    for i in range(3):
        a = 2*math.pi*i/3 + 0.2
        L.curve_tube(f"Lantern guard wire {i}",
                     [(x + 0.108*math.cos(a), y + 0.108*math.sin(a), z0+0.12),
                      (x + 0.084*math.cos(a), y + 0.084*math.sin(a), z0+0.31),
                      (x + 0.072*math.cos(a), y + 0.072*math.sin(a), z0+0.47)],
                     0.004, MAT['brass_dark'], coll)
    # curved handle
    L.curve_tube("Lantern handle",
                 [(x-0.10, y, z0+0.44), (x-0.17, y-0.02, z0+0.53),
                  (x, y-0.02, z0+0.57), (x+0.17, y-0.02, z0+0.53),
                  (x+0.10, y, z0+0.44)], 0.006, MAT['brass'], coll)
    # warm halo light source
    data = bpy.data.lights.new("Lantern warm light", 'POINT')
    data.energy = 38.0
    data.color = (1.0, 0.36, 0.085)
    data.shadow_soft_size = 0.06
    obj = bpy.data.objects.new("Lantern warm light", data)
    coll.objects.link(obj)
    obj.location = (x, y, z0 + 0.24)
    return obj


def build_tabletop(coll):
    # worn felt pad under the hero camera
    L.grid_cloth("Table felt runner", 1.18, 0.98, (0.38, 0.70, 0.828),
                 MAT['table_felt'], coll,
                 rot=(math.radians(-90), 0, math.radians(3)),
                 nx=24, nz=20, amp=0.006, freq=(3.0, 2.2),
                 thickness=0.003, seed=61)
    # an open ledger at the working edge
    make_open_book("Table open ledger", (-0.82, 0.06, 0.833), (0.36, 0.27),
                   (0, 0, math.radians(-14)), coll)
    # enamel bowl with developer
    bx, by = -0.40, 0.16
    bz = 0.852
    L.lathe("Enamel bowl", [(0.0, 0.0), (0.062, 0.002), (0.122, 0.012),
                            (0.160, 0.044), (0.170, 0.085), (0.159, 0.086),
                            (0.146, 0.058), (0.110, 0.029), (0.052, 0.018),
                            (0.0, 0.017)],
            (bx, by, bz), MAT['enamel'], coll, segments=64)
    L.torus("Enamel bowl rim", 0.166, 0.005, (bx, by, bz+0.085),
            MAT['enamel_blue'], coll, major_seg=64, minor_seg=10)
    L.cylinder("Developer surface", 0.136, 0.003, (bx, by, bz+0.058),
               MAT['liquid'], coll, verts=48)
    # developing tongs resting on bowl
    L.curve_tube("Developing tongs",
                 [(bx-0.24, by+0.045, bz+0.085), (bx-0.10, by+0.018, bz+0.10),
                  (bx+0.08, by-0.018, bz+0.075), (bx+0.23, by-0.035, bz+0.045)],
                 0.006, MAT['iron_dark'], coll)
    L.sphere("Tongs pivot", 0.012, (bx+0.08, by-0.018, bz+0.075),
             MAT['brass_dark'], coll, segments=14, rings=8)

    # stack of books and open ledger
    make_closed_book("Book stack 1", (-0.93, 0.43, 0.867), (0.33, 0.24, 0.055),
                     (0, 0, 0.11), MAT['leather'], MAT['paper'], coll)
    make_closed_book("Book stack 2", (-0.91, 0.44, 0.917), (0.31, 0.22, 0.045),
                     (0, 0, 0.03), MAT['leather_dark'], MAT['paper_dark'], coll)
    make_closed_book("Book stack 3", (-0.95, 0.42, 0.961), (0.27, 0.20, 0.035),
                     (0, 0, -0.08), MAT['wood_dark'], MAT['paper'], coll)
    make_open_book("Open ledger", (0.82, 0.32, 0.867), (0.57, 0.40),
                   (0, 0, math.radians(-13)), coll)
    # piled glass plate boxes
    for i in range(4):
        L.box(f"Plate box {i}", (0.42, 0.30, 0.045 + i*0.004),
              (1.15, 0.74 + i*0.018, 0.867 + i*0.045),
              MAT['wood_dark'] if i % 2 else MAT['card'], coll,
              rot=(0, 0, 0.05*(i-1)), bevel=0.004)
    # loose photographic prints
    for i, (x, y, rz, mat) in enumerate([
        (0.02, -0.12, 0.4, 'portrait_02'), (-0.10, -0.18, -0.2, 'portrait_05'),
        (0.55, -0.15, 0.7, 'portrait_08'), (1.40, 0.25, -0.4, 'portrait_11')]):
        L.plane(f"Loose print {i}", 0.16, 0.21, (x, y, 0.855), MAT[mat], coll,
                rot=(0, 0, rz))
        L.plane(f"Loose print backing {i}", 0.17, 0.22, (x, y, 0.852),
                MAT['paper'], coll, rot=(0, 0, rz))
    # small boxes, lens, keys
    L.box("Table wooden box", (0.20, 0.14, 0.11), (0.20, 0.16, 0.895),
          MAT['wood_mahogany'], coll, rot=(0, 0, 0.12), bevel=0.006)
    L.box("Table wooden box lid", (0.21, 0.15, 0.018), (0.20, 0.16, 0.957),
          MAT['wood_dark'], coll, rot=(0, 0, 0.12), bevel=0.004)
    L.cylinder("Loose lens barrel", 0.075, 0.10, (1.46, 0.55, 0.915),
               MAT['brass_dark'], coll, rot=(math.pi/2, 0, 0.2), verts=36)
    L.cylinder("Loose lens glass", 0.062, 0.012, (1.46, 0.49, 0.915),
               MAT['lens_glass'], coll, rot=(math.pi/2, 0, 0.2), verts=36)
    # keys and small tools
    for i, (x, y, rz) in enumerate([(1.06, 0.02, 0.3), (1.16, -0.02, 0.9), (1.25, 0.08, 1.4)]):
        L.torus(f"Key ring {i}", 0.022, 0.004, (x, y, 0.858), MAT['brass_dark'], coll,
                rot=(math.pi/2, 0, rz), major_seg=24, minor_seg=6)
        L.box(f"Key shaft {i}", (0.075, 0.008, 0.012), (x+0.04, y, 0.858),
              MAT['brass_dark'], coll, rot=(0, 0, rz), bevel=0.002)
    L.curve_tube("Loose wire", [(1.32, 0.38, 0.856), (1.15, 0.47, 0.86),
                                (1.0, 0.39, 0.856), (1.12, 0.30, 0.858)],
                 0.003, MAT['copper'], coll)
    # a brass magnifying glass, a small enamel cup, an ink bottle and scissors
    L.torus("Magnifier rim", 0.056, 0.007, (1.02, 0.02, 0.872),
            MAT['brass_dark'], coll, major_seg=32, minor_seg=8)
    L.cylinder("Magnifier lens", 0.050, 0.006, (1.02, 0.02, 0.872),
               MAT['glass'], coll, verts=32)
    L.cylinder("Magnifier handle", 0.011, 0.16, (1.16, 0.02, 0.872),
               MAT['brass_dark'], coll, rot=(0, math.pi/2, 0), verts=16)
    L.lathe("Enamel cup", [(0.0, 0.0), (0.035, 0.0), (0.052, 0.018),
                            (0.050, 0.085), (0.043, 0.086), (0.042, 0.02),
                            (0.0, 0.018)], (-1.33, 0.05, 0.858),
            MAT['enamel'], coll, segments=32)
    L.cylinder("Cup coffee", 0.040, 0.003, (-1.33, 0.05, 0.914),
               MAT['liquid'], coll, verts=28)
    L.cylinder("Ink bottle", 0.030, 0.09, (-0.18, 0.46, 0.906),
               MAT['glass'], coll, verts=24)
    L.cylinder("Ink bottle neck", 0.013, 0.04, (-0.18, 0.46, 0.968),
               MAT['glass'], coll, verts=16)
    L.cylinder("Ink bottle cap", 0.016, 0.022, (-0.18, 0.46, 0.995),
               MAT['brass_dark'], coll, verts=16)
    L.box("Scissors blade a", (0.20, 0.010, 0.008), (0.56, 0.02, 0.862),
          MAT['iron'], coll, rot=(0, 0, 0.22), bevel=0.002)
    L.box("Scissors blade b", (0.20, 0.010, 0.008), (0.56, 0.02, 0.866),
          MAT['iron'], coll, rot=(0, 0, -0.20), bevel=0.002)
    for sx in (-1, 1):
        L.torus("Scissors finger ring", 0.031, 0.005, (0.69, 0.02 + sx*0.035, 0.864),
                MAT['iron_dark'], coll, rot=(math.pi/2, 0, 0), major_seg=20, minor_seg=6)
    # stack of glass plate negatives in paper sleeves
    for i in range(3):
        L.box(f"Table glass plate {i}", (0.22, 0.17, 0.008),
              (-0.72 + i*0.012, 0.20 + i*0.012, 0.858 + i*0.012),
              MAT['glass'], coll, rot=(0, 0, 0.08), bevel=0.001)
        L.box(f"Table plate sleeve {i}", (0.24, 0.19, 0.004),
              (-0.73 + i*0.012, 0.19 + i*0.012, 0.854 + i*0.012),
              MAT['paper_dark'], coll, rot=(0, 0, 0.08), bevel=0.001)
    # pencil
    L.cylinder("Pencil", 0.006, 0.19, (1.28, 0.30, 0.862),
               MAT['wood_light'], coll, rot=(0, math.pi/2, 0.6), verts=8)
    # a scatter of dust / paper scraps
    for i in range(12):
        x = RNG.uniform(-1.5, 1.55)
        y = RNG.uniform(-0.55, 0.55)
        L.plane(f"Paper scrap {i}", RNG.uniform(0.03, 0.09), RNG.uniform(0.03, 0.08),
                (x, y, 0.854), MAT['paper_dark'], coll,
                rot=(0, 0, RNG.uniform(0, 6.28)))


def make_closed_book(name, loc, dims, rot, cover_mat, page_mat, coll):
    x, y, z = loc
    w, d, h = dims
    L.box(name + " pages", (w*0.92, d*0.94, h*0.7), (x, y, z),
          page_mat, coll, rot=rot, bevel=0.002)
    L.box(name + " cover", (w, d, h*0.14), (x, y, z + h*0.43),
          cover_mat, coll, rot=rot, bevel=0.003)
    L.box(name + " cover bottom", (w, d, h*0.14), (x, y, z - h*0.43),
          cover_mat, coll, rot=rot, bevel=0.003)
    L.box(name + " spine", (w*0.09, d*0.96, h*0.9),
          (x - w*0.47*math.cos(rot[2]), y - w*0.47*math.sin(rot[2]), z),
          cover_mat, coll, rot=rot, bevel=0.003)
    for k, t in enumerate((-0.25, 0.0, 0.25)):
        L.box(name + f" gold band {k}", (w*0.025, d*0.97, 0.007),
              (x - w*0.48*math.cos(rot[2]) + k*0.012, y - w*0.48*math.sin(rot[2]), z + t*h*0.45),
              MAT['brass_dark'], coll, rot=rot, bevel=0.001)


def make_open_book(name, loc, size, rot, coll):
    x, y, z = loc
    w, d = size
    L.box(name + " cover", (w, d, 0.018), (x, y, z), MAT['leather_dark'], coll,
          rot=rot, bevel=0.003)
    # two page panels, very slightly lifted at the centre
    for side, sx in enumerate((-1, 1)):
        px = x + sx*w*0.24*math.cos(rot[2])
        py = y + sx*w*0.24*math.sin(rot[2])
        pg = L.plane(name + f" page {side}", w*0.46, d*0.88,
                     (px, py, z+0.015), MAT['paper'], coll,
                     rot=(0, sx*math.radians(4), rot[2]))
        # a few lines of handwriting
        for line in range(7):
            ly = -d*0.34 + line*d*0.1
            L.curve_tube(name + f" ink {side}.{line}",
                         [(px - w*0.17*math.cos(rot[2]) - ly*math.sin(rot[2]),
                           py - w*0.17*math.sin(rot[2]) + ly*math.cos(rot[2]), z+0.018),
                          (px + w*0.12*math.cos(rot[2]) - ly*math.sin(rot[2]),
                           py + w*0.12*math.sin(rot[2]) + ly*math.cos(rot[2]), z+0.018)],
                         0.0012, MAT['grout'], coll)


# -----------------------------------------------------------------------------
# portrait wall
# -----------------------------------------------------------------------------

def make_frame(name, x, z, w, h, portrait_key, coll, style=0, tilt=0.0):
    y = 3.952
    bar = 0.044
    depth = 0.055
    frame_mat = MAT['wood_frames'] if style < 2 else MAT['brass_dark']
    # four bars
    L.box(name + " top", (w, depth, bar), (x, y, z + h/2 - bar/2),
          frame_mat, coll, rot=(0, 0, tilt), bevel=0.006)
    L.box(name + " bottom", (w, depth, bar), (x, y, z - h/2 + bar/2),
          frame_mat, coll, rot=(0, 0, tilt), bevel=0.006)
    L.box(name + " left", (bar, depth, h - bar*1.8), (x - w/2 + bar/2, y, z),
          frame_mat, coll, rot=(0, 0, tilt), bevel=0.006)
    L.box(name + " right", (bar, depth, h - bar*1.8), (x + w/2 - bar/2, y, z),
          frame_mat, coll, rot=(0, 0, tilt), bevel=0.006)
    # inner gilt bead
    bead = 0.010
    L.box(name + " bead top", (w - bar*2.2, 0.018, bead),
          (x, y - 0.038, z + h/2 - bar*1.55), MAT['brass_dark'], coll,
          rot=(0, 0, tilt), bevel=0.002)
    L.box(name + " bead bottom", (w - bar*2.2, 0.018, bead),
          (x, y - 0.038, z - h/2 + bar*1.55), MAT['brass_dark'], coll,
          rot=(0, 0, tilt), bevel=0.002)
    # backing
    L.box(name + " backing", (w - bar*1.8, 0.018, h - bar*1.8),
          (x, y + 0.030, z), MAT['paper_dark'], coll,
          rot=(0, 0, tilt), bevel=0.002)
    # photographic print
    L.plane(name + " portrait", w - bar*2.0, h - bar*2.0,
            (x, y - 0.030, z), MAT[portrait_key], coll,
            rot=(math.pi/2, 0, tilt))
    # glass sheen
    L.plane(name + " glass", w - bar*2.0, h - bar*2.0,
            (x, y - 0.040, z), MAT['glass_sheen'], coll,
            rot=(math.pi/2, 0, tilt))
    # hanging wire on the wall (a small detail)
    L.curve_tube(name + " wire",
                 [(x - w*0.35, y - 0.005, z + h*0.36),
                  (x, y - 0.006, z + h*0.47),
                  (x + w*0.35, y - 0.005, z + h*0.36)],
                 0.0018, MAT['iron_dark'], coll)


def build_portrait_wall(coll):
    # long picture ledge with corbels
    L.box("Picture ledge", (6.9, 0.24, 0.07), (0.0, 3.80, 1.54),
          MAT['wood_frames'], coll, bevel=0.009)
    L.box("Picture ledge lip", (6.9, 0.035, 0.035), (0.0, 3.685, 1.58),
          MAT['wood_dark'], coll, bevel=0.004)
    for x in (-3.15, -1.6, 0.0, 1.6, 3.15):
        L.box("Ledge corbel", (0.09, 0.28, 0.16), (x, 3.78, 1.46),
              MAT['wood_frames'], coll, rot=(0, 0, 0), bevel=0.006)
        L.beam_between("Ledge brace", (x, 3.63, 1.39), (x, 3.83, 1.49),
                       0.045, 0.055, MAT['wood_frames'], coll, bevel=0.003)
    # nine portraits in a deliberately uneven row
    xs = [-2.45, -1.82, -1.18, -0.55, 0.1, 0.74, 1.38, 2.02, 2.66]
    portrait_cycle = [1, 2, 3, 6, 7, 8, 9, 12, 2]
    for i, x in enumerate(xs):
        w = 0.37 + RNG.uniform(-0.02, 0.02)
        h = 0.48 + RNG.uniform(-0.02, 0.02)
        z = 1.94 + RNG.uniform(-0.025, 0.025)
        make_frame(f"Portrait frame {i}", x, z, w, h,
                   f'portrait_{portrait_cycle[i]:02d}', coll,
                   style=i % 3, tilt=RNG.uniform(-0.018, 0.018))
    # small still-life objects on the ledge
    L.box("Ledge plate box", (0.26, 0.17, 0.05), (-2.98, 3.77, 1.61),
          MAT['wood_dark'], coll, rot=(0, 0, 0.08), bevel=0.004)
    L.box("Ledge plate box 2", (0.21, 0.15, 0.06), (-2.74, 3.78, 1.62),
          MAT['card'], coll, rot=(0, 0, -0.04), bevel=0.003)
    L.cylinder("Ledge bottle", 0.04, 0.18, (3.12, 3.78, 1.67),
               MAT['glass'], coll, verts=24)
    L.cylinder("Ledge bottle neck", 0.016, 0.08, (3.12, 3.78, 1.79),
               MAT['glass'], coll, verts=16)
    # a big empty frame leaning at the left end of the ledge
    L.box("Leaning empty frame", (0.52, 0.035, 0.66), (-3.58, 3.82, 1.42),
          MAT['wood_frames'], coll, rot=(0, 0, 0.02), bevel=0.007)
    L.box("Leaning frame inner", (0.42, 0.04, 0.56), (-3.58, 3.805, 1.42),
          MAT['plaster_grey'], coll, rot=(0, 0, 0.02), bevel=0.002)
    # a little shelf above the left end, with papers and a hat
    L.box("North wall small shelf", (1.06, 0.28, 0.045), (-3.35, 3.82, 1.78),
          MAT['wood_dark'], coll, bevel=0.005)
    for x in (-3.82, -2.88):
        L.box("Small shelf bracket", (0.04, 0.24, 0.14), (x, 3.83, 1.70),
              MAT['iron_dark'], coll, bevel=0.003)
    L.grid_cloth("Shelf papers", 0.42, 0.28, (-3.48, 3.74, 1.81),
                 MAT['paper'], coll, rot=(math.radians(88), 0, math.radians(4)),
                 nx=10, nz=8, amp=0.012, freq=(2.0, 2.0), thickness=0.002, seed=55)
    L.sphere("Shelf cap", 0.14, (-3.12, 3.78, 1.89), MAT['felt'], coll,
             scale=(1.0, 1.25, 0.45), segments=24, rings=14)
    L.cylinder("Shelf cap brim", 0.20, 0.018, (-3.12, 3.75, 1.85),
               MAT['felt'], coll, rot=(0.06, 0, 0), verts=32)


# -----------------------------------------------------------------------------
# west wall: sink, cupboards, shelves, aprons
# -----------------------------------------------------------------------------

def build_west_side(coll):
    # base cupboard with slate top
    cx = -4.48
    y0, y1 = 0.55, 3.28
    L.box("West cupboard carcass", (0.74, y1-y0, 0.82),
          (cx, (y0+y1)/2, 0.43), MAT['wood_dark'], coll, bevel=0.009)
    L.box("West cupboard top", (0.82, y1-y0+0.08, 0.06),
          (cx-0.01, (y0+y1)/2, 0.86), MAT['slate'], coll, bevel=0.005)
    # doors on the room-facing side (+X)
    for i, y in enumerate((1.08, 1.86, 2.64)):
        L.box(f"West cupboard door {i}", (0.04, 0.70, 0.66),
              (cx + 0.385, y, 0.48), MAT['wood_door'], coll, bevel=0.006)
        L.box(f"West cupboard door inset {i}", (0.018, 0.52, 0.48),
              (cx + 0.410, y, 0.48), MAT['wood_dark'], coll, bevel=0.003)
        L.sphere(f"West cupboard knob {i}", 0.022,
                 (cx + 0.418, y + 0.27, 0.52), MAT['brass_dark'], coll,
                 scale=(0.55, 1, 1), segments=14, rings=8)
        L.box(f"West cupboard hinge {i}", (0.015, 0.10, 0.035),
              (cx + 0.412, y - 0.31, 0.70), MAT['iron_dark'], coll, bevel=0.002)
    # one door ajar
    L.box("West cupboard open door", (0.035, 0.62, 0.64),
          (cx + 0.67, 3.10, 0.49), MAT['wood_door'], coll,
          rot=(0, 0, math.radians(56)), bevel=0.005)
    # enamel basin set on the slate top (reads better than a black hole)
    sx, sy = cx - 0.02, 2.55
    sink_z = 0.955
    for ax, ay, w, d in [(-1, 0, 0.06, 0.62), (1, 0, 0.06, 0.62),
                         (0, -1, 0.56, 0.06), (0, 1, 0.56, 0.06)]:
        dims = (0.06, 0.62, 0.13) if ax else (0.56, 0.06, 0.13)
        L.box("Sink wall", dims,
              (sx + ax*0.25, sy + ay*0.28, sink_z), MAT['enamel'], coll,
              bevel=0.006)
    L.box("Sink bottom", (0.50, 0.50, 0.035), (sx, sy, 0.925),
          MAT['enamel'], coll, bevel=0.004)
    L.cylinder("Sink water", 0.235, 0.006, (sx, sy, 0.945),
               MAT['water'], coll, verts=48)
    L.cylinder("Sink drain", 0.028, 0.012, (sx, sy, 0.949),
               MAT['iron_dark'], coll, verts=20)
    # blue rim around the basin
    for ax, ay, w, d in [(-1, 0, 0.04, 0.62), (1, 0, 0.04, 0.62),
                         (0, -1, 0.56, 0.04), (0, 1, 0.56, 0.04)]:
        dims = (0.04, 0.62, 0.02) if ax else (0.56, 0.04, 0.02)
        L.box("Sink rim", dims,
              (sx + ax*0.25, sy + ay*0.28, 1.025), MAT['enamel_blue'], coll,
              bevel=0.003)
    # towel over the front edge
    L.grid_cloth("Sink towel", 0.48, 0.52, (sx + 0.27, sy - 0.10, 0.80),
                 MAT['canvas_apron'], coll, rot=(0, 0, math.radians(90)),
                 nx=14, nz=18, amp=0.045, freq=(2.8, 2.2),
                 thickness=0.004, seed=141)
    # brass wall faucet
    L.tube_between("Faucet pipe", (-4.92, sy, 1.63), (-4.72, sy, 1.63),
                   0.018, MAT['brass'], coll)
    L.curve_tube("Faucet neck",
                 [(-4.72, sy, 1.63), (-4.60, sy, 1.67), (-4.55, sy, 1.45),
                  (-4.55, sy, 1.19), (-4.55, sy, 1.08)],
                 0.017, MAT['brass'], coll)
    L.cylinder("Faucet spout", 0.024, 0.06, (-4.55, sy, 1.05),
               MAT['brass'], coll, bevel=0.003, verts=20)
    L.torus("Faucet valve", 0.045, 0.011, (-4.78, sy, 1.55),
            MAT['brass_dark'], coll, rot=(0, math.pi/2, 0), major_seg=28, minor_seg=8)
    L.cylinder("Faucet valve stem", 0.013, 0.10, (-4.78, sy, 1.55),
               MAT['brass'], coll, rot=(0, math.pi/2, 0), verts=12)
    # enamel trays, bottles, jars on the slate
    L.box("Developing tray", (0.53, 0.40, 0.075), (cx-0.06, 0.90, 0.945),
          MAT['enamel'], coll, rot=(0, 0, 0.04), bevel=0.008)
    L.box("Developing tray inner", (0.45, 0.32, 0.05), (cx-0.06, 0.90, 0.965),
          MAT['liquid'], coll, rot=(0, 0, 0.04), bevel=0.004)
    for i, (y, r, h, mat) in enumerate([(1.43, 0.055, 0.23, 'glass'),
                                         (1.58, 0.045, 0.18, 'glass'),
                                         (1.72, 0.06, 0.25, 'ceramic')]):
        L.cylinder(f"West bottle {i}", r, h, (cx-0.17, y, 0.98 + h/2),
                   MAT[mat], coll, verts=24, bevel=0.003)
        L.cylinder(f"West bottle neck {i}", r*0.35, 0.07,
                   (cx-0.17, y, 0.98 + h + 0.025), MAT[mat], coll, verts=16)
        L.cylinder(f"West bottle cork {i}", r*0.34, 0.025,
                   (cx-0.17, y, 0.98 + h + 0.07), MAT['wax'], coll, verts=16)
    # wall cupboard above sink, doors open
    L.box("West wall cupboard", (0.34, 1.30, 0.82), (-4.80, 2.30, 1.95),
          MAT['wood_dark'], coll, bevel=0.008)
    L.box("West wall cupboard back", (0.05, 1.22, 0.72), (-4.64, 2.30, 1.95),
          MAT['wood_frames'], coll, bevel=0.003)
    for z in (1.76, 2.10):
        L.box("West cupboard shelf", (0.30, 1.22, 0.035), (-4.79, 2.30, z),
              MAT['wood_light'], coll, bevel=0.003)
    for i, y in enumerate((2.74, 3.02)):
        L.box(f"West upper door {i}", (0.035, 0.50, 0.72),
              (-4.60, y, 1.95), MAT['wood_door'], coll, bevel=0.005)
        L.box(f"West upper inset {i}", (0.018, 0.37, 0.55),
              (-4.582, y, 1.95), MAT['wood_dark'], coll, bevel=0.003)
    # jars / plates inside the upper cupboard
    for i in range(6):
        y = 1.84 + i*0.15
        L.cylinder(f"Upper shelf jar {i}", 0.038, 0.13,
                   (-4.77, y, 1.835 + (i % 2)*0.33), MAT['glass'], coll, verts=20)
        L.cylinder(f"Upper shelf jar lid {i}", 0.042, 0.022,
                   (-4.77, y, 1.91 + (i % 2)*0.33), MAT['brass_dark'], coll, verts=20)
    # hanging apron with neck loop and ties
    apron = L.grid_cloth("Hanging apron", 0.58, 0.92, (-4.77, 0.12, 1.20),
                         MAT['canvas_apron'], coll,
                         rot=(0, 0, math.radians(90)),
                         nx=18, nz=28, amp=0.035, freq=(2.4, 3.2),
                         thickness=0.005, seed=81)
    L.curve_tube("Apron neck loop",
                 [(-4.80, 0.02, 1.66), (-4.80, -0.20, 1.72),
                  (-4.80, 0.02, 1.66), (-4.80, 0.24, 1.72)],
                 0.008, MAT['rope'], coll)
    L.curve_tube("Apron tie",
                 [(-4.80, -0.18, 1.35), (-4.75, -0.28, 1.26),
                  (-4.78, -0.12, 1.18)], 0.007, MAT['rope'], coll)
    # peg rail above apron
    L.box("Apron peg rail", (0.06, 1.2, 0.075), (-4.88, 0.1, 1.72),
          MAT['wood_dark'], coll, bevel=0.004)
    for y in (-0.25, 0.0, 0.25, 0.5):
        L.cylinder("Apron peg", 0.018, 0.11, (-4.82, y, 1.70),
                   MAT['wood_dark'], coll, rot=(0, math.pi/2, 0), verts=12)
    # shelf at y ~0.3 with papers, small boxes
    L.box("West high shelf", (0.42, 1.18, 0.045), (-4.72, -0.12, 1.66),
          MAT['wood_dark'], coll, bevel=0.004)
    for y in (-0.62, 0.38):
        L.box("West shelf bracket", (0.30, 0.045, 0.14), (-4.70, y, 1.58),
              MAT['iron_dark'], coll, bevel=0.003)
    L.grid_cloth("West shelf papers", 0.40, 0.32, (-4.72, -0.05, 1.69),
                 MAT['paper'], coll, rot=(math.radians(86), 0, math.radians(8)),
                 nx=10, nz=8, amp=0.012, freq=(2.2, 2.2), thickness=0.002, seed=91)
    L.box("West shelf box", (0.22, 0.18, 0.12), (-4.70, 0.28, 1.75),
          MAT['wood_dark'], coll, rot=(0, 0, 0.09), bevel=0.004)
    # film box against the south end of the west wall
    fbx, fby = -4.59, -2.95
    L.box("Film cabinet", (0.52, 0.70, 1.12), (fbx, fby, 0.58),
          MAT['wood_dark'], coll, bevel=0.008)
    L.box("Film cabinet door", (0.035, 0.60, 0.94), (fbx+0.275, fby, 0.58),
          MAT['wood_door'], coll, bevel=0.005)
    L.box("Film cabinet inset", (0.018, 0.46, 0.78), (fbx+0.295, fby, 0.58),
          MAT['wood_dark'], coll, bevel=0.003)
    L.box("Film cabinet top", (0.58, 0.76, 0.045), (fbx, fby, 1.16),
          MAT['slate'], coll, bevel=0.004)
    L.box("Film cabinet latch", (0.025, 0.07, 0.16), (fbx+0.30, fby+0.18, 0.66),
          MAT['brass_dark'], coll, bevel=0.003)
    L.torus("Film cabinet padlock", 0.038, 0.009, (fbx+0.33, fby+0.18, 0.55),
            MAT['brass'], coll, rot=(0, math.pi/2, 0), major_seg=20, minor_seg=8)
    if 'label_film' in MAT:
        L.plane("Film cabinet label", 0.30, 0.14, (fbx+0.302, fby-0.12, 0.92),
                MAT['label_film'], coll, rot=(math.pi/2, 0, math.pi/2))
    # a low stack of plate boxes and a canvas roll near the foreground corner
    for i in range(4):
        L.box(f"Foreground plate box {i}", (0.48, 0.38, 0.08),
              (-4.22, -1.34, 0.05 + i*0.085), MAT['wood_dark'], coll,
              rot=(0, 0, 0.06*(i-1)), bevel=0.004)
    L.box("Foreground plate box label", (0.30, 0.02, 0.16),
          (-4.22, -1.535, 0.29), MAT['card'], coll, rot=(0, 0, 0.02), bevel=0.002)
    L.cylinder("Canvas roll", 0.16, 1.28, (-3.76, -3.10, 0.17),
               MAT['cloth_burlap'], coll, rot=(0, math.pi/2, 0), verts=32, bevel=0.006)
    # loose leaning boards
    L.box("Leaning board 1", (0.06, 0.42, 1.9), (-4.58, -1.74, 0.95),
          MAT['wood_light'], coll, rot=(0, -0.22, 0.08), bevel=0.005)
    L.box("Leaning board 2", (0.045, 0.38, 1.7), (-4.48, -1.58, 0.85),
          MAT['wood_light'], coll, rot=(0, -0.16, -0.06), bevel=0.004)

    # a work coat hanging on the west wall, around the foreground corner
    coat = L.grid_cloth("Hanging work coat", 0.62, 1.02, (-4.80, -0.82, 1.28),
                        MAT['cloth_olive'], coll,
                        rot=(0, 0, math.radians(90)),
                        nx=20, nz=28, amp=0.045, freq=(2.6, 2.2),
                        thickness=0.006, seed=108)
    L.curve_tube("Coat hook",
                 [(-4.90, -0.82, 1.80), (-4.82, -0.82, 1.83),
                  (-4.80, -0.82, 1.76)], 0.012, MAT['iron_dark'], coll)
    L.sphere("Coat collar", 0.13, (-4.80, -1.03, 1.73), MAT['cloth_olive'], coll,
             scale=(0.35, 1.0, 0.5), segments=20, rings=10)
    # a drying line with three small prints, pegged to the wall
    L.curve_tube("Print drying line",
                 [(-4.86, -2.35, 1.88), (-4.86, -1.85, 1.80),
                  (-4.86, -1.35, 1.84)], 0.003, MAT['rope'], coll)
    for i, (y, z, key) in enumerate([(-2.10, 1.67, 'portrait_04'),
                                      (-1.78, 1.63, 'portrait_09'),
                                      (-1.47, 1.68, 'portrait_12')]):
        L.plane(f"Drying print {i}", 0.16, 0.21, (-4.845, y, z), MAT[key], coll,
                rot=(math.pi/2, 0, math.pi/2))
        L.box(f"Drying print clip {i}", (0.012, 0.035, 0.03),
              (-4.835, y, z + 0.10), MAT['wood_dark'], coll, bevel=0.001)


# -----------------------------------------------------------------------------
# east side: ladder, crates, plate camera on tripod
# -----------------------------------------------------------------------------

def build_east_side(coll):
    # long leaning ladder under the ceiling hatch
    xa, xb = 3.56, 4.26
    base_y, top_y = -3.08, -1.04
    base_z, top_z = 0.02, 2.63
    for x in (xa, xb):
        L.beam_between(f"Ladder rail {x}", (x, base_y, base_z),
                       (x, top_y, top_z), 0.075, 0.11,
                       MAT['wood_ladder'], coll, bevel=0.007)
    for i in range(11):
        t = 0.06 + i*0.086
        y = base_y + (top_y-base_y)*t
        z = base_z + (top_z-base_z)*t
        L.box(f"Ladder rung {i}", (xb-xa+0.10, 0.065, 0.07),
              ((xa+xb)/2, y, z), MAT['wood_ladder'], coll,
              bevel=0.006)
        # iron strap / nails
        if i % 3 == 0:
            for x in (xa, xb):
                L.sphere("Ladder nail", 0.012, (x, y-0.028, z+0.02),
                         MAT['iron_dark'], coll, scale=(1, 0.5, 1),
                         segments=10, rings=6)
    # top hook plates
    for x in (xa, xb):
        L.box("Ladder top hook", (0.14, 0.06, 0.24), (x, top_y-0.02, top_z-0.06),
              MAT['iron_dark'], coll, rot=(0.35, 0, 0), bevel=0.004)
    # a big dusty cobweb across the ladder
    L.curve_tube("Ladder cobweb",
                 [(3.55, -2.75, 2.13), (4.28, -2.20, 1.78),
                  (3.85, -2.55, 1.45)], 0.0018, MAT['dust'], coll)

    # crates: foreground stack, a pile beneath the ladder, and back-right
    crates = [
        ((3.58, -3.42, 0.28), (0.68, 0.52, 0.46), 0.05, 'label_plates', 0),
        ((4.27, -3.53, 0.25), (0.62, 0.50, 0.42), -0.03, 'label_fragile', 1),
        ((3.64, -3.40, 0.73), (0.58, 0.45, 0.38), 0.11, 'label_london', 2),
        ((4.60, -2.84, 0.27), (0.50, 0.44, 0.48), 0.16, 'label_film', 3),
        ((2.88, -3.56, 0.24), (0.55, 0.40, 0.38), -0.13, None, 4),
        ((3.18, -1.73, 0.29), (0.64, 0.48, 0.50), 0.04, 'label_1926', 5),
        ((3.22, -1.70, 0.78), (0.52, 0.42, 0.36), -0.08, 'label_fragile', 6),
        ((4.58, -1.62, 0.28), (0.46, 0.42, 0.46), 0.12, 'label_film', 7),
        ((4.20, 2.63, 0.30), (0.72, 0.55, 0.52), 0.06, 'label_chemicals', 8),
        ((4.26, 2.61, 0.82), (0.60, 0.45, 0.38), -0.09, 'label_1926', 9),
        ((3.66, 2.72, 0.26), (0.50, 0.42, 0.44), 0.20, None, 10),
        ((4.53, 1.87, 0.28), (0.48, 0.40, 0.46), -0.15, 'label_darkroom', 11),
    ]
    for loc, dims, rz, label, idx in crates:
        build_crate(f"Crate {idx}", loc, dims, rz, coll, label)

    # plate camera on a tripod at the back-right
    build_tripod_camera(coll, (4.02, 2.92, 0.0))

    # stack of glass plate boxes, jars and a step stool near the back wall
    for i in range(4):
        L.box(f"East plate box {i}", (0.52, 0.38, 0.075),
              (4.64, 1.34, 0.05 + i*0.08), MAT['wood_dark'], coll,
              rot=(0, 0, 0.04*(i-1)), bevel=0.004)
    L.cylinder("East jar", 0.09, 0.22, (4.68, 0.95, 0.13),
               MAT['ceramic'], coll, verts=24, bevel=0.005)
    L.cylinder("East jar lid", 0.095, 0.03, (4.68, 0.95, 0.255),
               MAT['brass_dark'], coll, verts=24)
    # small step ladder leaning on east wall
    for i, y in enumerate((1.05, 1.50)):
        L.box(f"Step ladder stile {i}", (0.06, 0.08, 1.85),
              (4.80, y, 0.93), MAT['wood_ladder'], coll,
              rot=(0, -0.16, 0), bevel=0.004)
    for k, z in enumerate((0.35, 0.78, 1.21, 1.62)):
        L.box(f"Step ladder tread {k}", (0.20, 0.50, 0.045),
              (4.78, 1.275, z), MAT['wood_ladder'], coll,
              rot=(0, -0.16, 0), bevel=0.004)

    # east wall shelf with chemical bottles
    L.box("East wall shelf", (0.34, 1.16, 0.045), (4.80, 0.25, 1.55),
          MAT['wood_dark'], coll, bevel=0.004)
    for y in (-0.2, 0.68):
        L.box("East shelf bracket", (0.26, 0.045, 0.12), (4.79, y, 1.47),
              MAT['iron_dark'], coll, bevel=0.003)
    for i, (y, r, h, mat) in enumerate([(0.02, 0.055, 0.21, 'glass'),
                                         (0.19, 0.045, 0.16, 'glass'),
                                         (0.36, 0.06, 0.24, 'ceramic')]):
        L.cylinder(f"East bottle {i}", r, h, (4.79, y, 1.58+h/2),
                   MAT[mat], coll, verts=20)
        L.cylinder(f"East bottle neck {i}", r*0.35, 0.07, (4.79, y, 1.58+h+0.03),
                   MAT[mat], coll, verts=12)
        if 'chemicals' in MAT:
            pass
    # a wall-mounted rail with a few hanging darkroom tools
    L.box("East tool rail", (0.045, 1.12, 0.075), (4.92, -0.55, 1.79),
          MAT['iron_dark'], coll, bevel=0.005)
    for i, (y, z) in enumerate([(-0.92, 1.74), (-0.58, 1.74), (-0.24, 1.74)]):
        L.cylinder(f"Tool peg {i}", 0.012, 0.10, (4.88, y, z),
                   MAT['iron_dark'], coll, rot=(0, math.pi/2, 0), verts=12)
    # long tongs
    L.curve_tube("Hanging tongs",
                 [(4.86, -0.92, 1.72), (4.84, -0.94, 1.38), (4.83, -0.89, 1.18)],
                 0.007, MAT['iron_dark'], coll)
    L.curve_tube("Hanging tongs 2",
                 [(4.86, -0.91, 1.72), (4.84, -0.86, 1.38), (4.83, -0.80, 1.18)],
                 0.007, MAT['iron_dark'], coll)
    # scissors
    L.box("Hanging scissors blade", (0.012, 0.013, 0.34), (4.85, -0.58, 1.51),
          MAT['iron'], coll, rot=(0.0, 0.28, 0.0), bevel=0.002)
    L.box("Hanging scissors blade 2", (0.012, 0.013, 0.34), (4.85, -0.55, 1.51),
          MAT['iron'], coll, rot=(0.0, -0.28, 0.0), bevel=0.002)
    L.torus("Hanging scissors ring", 0.035, 0.005, (4.84, -0.52, 1.72),
            MAT['brass_dark'], coll, rot=(0, math.pi/2, 0), major_seg=20, minor_seg=6)
    # a couple of small clips and a hanging negative strip
    L.curve_tube("Hanging negative strip",
                 [(4.86, -0.24, 1.74), (4.86, -0.22, 1.43), (4.86, -0.28, 1.24)],
                 0.018, MAT['leather_dark'], coll)


def build_crate(name, loc, dims, rz, coll, label=None):
    x, y, z = loc
    w, d, h = dims
    # dark interior / mass
    L.box(name + " mass", (w*0.92, d*0.92, h*0.92), (x, y, z),
          MAT['wood_dark'], coll, rot=(0, 0, rz), bevel=0.006)
    # corner posts
    for sx in (-1, 1):
        for sy in (-1, 1):
            L.box(name + " corner", (0.055, 0.055, h),
                  (x + sx*(w/2-0.03), y + sy*(d/2-0.03), z),
                  MAT['wood_crate'], coll, rot=(0, 0, rz), bevel=0.003)
    # horizontal slats on four sides
    for side, (nx, ny, sw, sd) in enumerate([(0, -1, w, 0.026), (0, 1, w, 0.026),
                                             (-1, 0, 0.026, d), (1, 0, 0.026, d)]):
        for k, zz in enumerate((-h*0.32, 0.0, h*0.32)):
            if nx:
                L.box(name + f" slat {side}.{k}", (sw, sd, h*0.22),
                      (x + nx*w/2, y, z+zz), MAT['wood_crate'], coll,
                      rot=(0, 0, rz), bevel=0.003)
            else:
                L.box(name + f" slat {side}.{k}", (sw, sd, h*0.22),
                      (x, y + ny*d/2, z+zz), MAT['wood_crate'], coll,
                      rot=(0, 0, rz), bevel=0.003)
    # lid boards
    for k in range(3):
        L.box(name + f" lid {k}", (w*0.92, d*0.30, 0.032),
              (x, y + (k-1)*d*0.30, z+h/2+0.018),
              MAT['wood_light'], coll, rot=(0, 0, rz), bevel=0.003)
    # label on the front (-Y) face
    if label and label in MAT:
        L.plane(name + " label", w*0.48, h*0.24, (x, y-d/2-0.002, z+h*0.04),
                MAT[label], coll, rot=(math.pi/2, 0, rz))
    # a few rusted nails
    for sx in (-1, 1):
        for sz in (-1, 1):
            L.sphere(name + " nail", 0.008,
                     (x + sx*w*0.40, y-d/2-0.001, z + sz*h*0.35),
                     MAT['iron_dark'], coll, scale=(1, 0.35, 1),
                     segments=8, rings=6)


def build_tripod_camera(coll, origin):
    ox, oy, oz = origin
    top = Vector((ox, oy, oz + 1.14))
    legs = [(ox-0.48, oy-0.46, oz), (ox+0.46, oy-0.42, oz),
            (ox+0.02, oy+0.55, oz)]
    for i, leg in enumerate(legs):
        L.beam_between(f"Tripod leg {i}", top, leg, 0.055, 0.065,
                       MAT['wood_dark'], coll, bevel=0.004)
        L.box(f"Tripod foot {i}", (0.10, 0.10, 0.06),
              (leg[0], leg[1], 0.04), MAT['iron_dark'], coll, bevel=0.004)
    L.box("Tripod head", (0.17, 0.17, 0.08), (ox, oy, oz+1.16),
          MAT['brass_dark'], coll, bevel=0.006)
    L.box("Tripod camera base", (0.44, 0.38, 0.08), (ox, oy+0.02, oz+1.23),
          MAT['wood_mahogany'], coll, bevel=0.006)
    L.box("Tripod camera body", (0.36, 0.30, 0.36), (ox, oy+0.08, oz+1.45),
          MAT['wood_mahogany'], coll, bevel=0.008)
    # small bellows toward the front (south-west)
    for i in range(5):
        L.box(f"Tripod bellows {i}", (0.30-0.025*i, 0.045, 0.28-0.02*i),
              (ox-0.08*i, oy-0.09-0.04*i, oz+1.44),
              MAT['leather_dark'] if i % 2 else MAT['leather'], coll, bevel=0.003)
    L.cylinder("Tripod lens", 0.085, 0.08, (ox-0.19, oy-0.18, oz+1.44),
               MAT['brass_dark'], coll, rot=(math.pi/2, 0, 0.20), verts=36)
    L.cylinder("Tripod lens glass", 0.068, 0.012, (ox-0.19, oy-0.225, oz+1.44),
               MAT['lens_glass'], coll, rot=(math.pi/2, 0, 0.20), verts=36)
    # dark cloth over the back
    L.grid_cloth("Tripod camera cloth", 0.46, 0.56, (ox+0.04, oy+0.22, oz+1.36),
                 MAT['cloth_dark'], coll, rot=(math.radians(75), 0, 0.05),
                 nx=14, nz=18, amp=0.035, freq=(2.2, 2.8),
                 thickness=0.003, seed=111)


# -----------------------------------------------------------------------------
# floor clutter, dust, final dressing
# -----------------------------------------------------------------------------

def build_chair(coll):
    cx, cy = -2.00, -1.85
    ang = math.radians(18)
    ca, sa = math.cos(ang), math.sin(ang)
    def p(dx, dy):
        return (cx + dx*ca - dy*sa, cy + dx*sa + dy*ca)
    # legs
    for sx in (-1, 1):
        for sy in (-1, 1):
            x, y = p(sx*0.20, sy*0.18)
            L.box("Chair leg", (0.052, 0.052, 0.46), (x, y, 0.23),
                  MAT['wood_bench'], coll, rot=(0, 0, ang), bevel=0.004)
    x, y = p(0, 0)
    L.box("Chair seat", (0.48, 0.42, 0.05), (x, y, 0.47),
          MAT['wood_bench'], coll, rot=(0, 0, ang), bevel=0.007)
    L.box("Chair seat wear", (0.40, 0.33, 0.006), (x, y, 0.499),
          MAT['wood_dark'], coll, rot=(0, 0, ang), bevel=0.002)
    # back posts and slats
    for sx in (-1, 1):
        x, y = p(sx*0.20, 0.20)
        L.box("Chair back post", (0.05, 0.055, 0.58), (x, y, 0.78),
              MAT['wood_bench'], coll, rot=(0, 0, ang), bevel=0.004)
    for i, z in enumerate((0.72, 0.88, 1.02)):
        x, y = p(0, 0.205)
        L.box(f"Chair back slat {i}", (0.40, 0.035, 0.075), (x, y, z),
              MAT['wood_ladder'], coll, rot=(0, 0, ang), bevel=0.004)
    # a work cloth left on the chair
    L.grid_cloth("Chair cloth", 0.38, 0.45, (x-0.02, y-0.02, 0.58),
                 MAT['canvas_apron'], coll,
                 rot=(math.radians(8), 0, ang + math.radians(90)),
                 nx=12, nz=16, amp=0.03, freq=(2.5, 2.0), thickness=0.003, seed=131)


def build_floor_clutter(coll):
    # an old wooden chair, tucked in front of the bench
    build_chair(coll)
    # a zinc bucket and a broom by the sink
    L.lathe("Zinc bucket", [(0.0, 0.0), (0.14, 0.0), (0.16, 0.05),
                             (0.17, 0.28), (0.155, 0.30), (0.145, 0.29),
                             (0.135, 0.05), (0.0, 0.03)],
            (-3.80, 2.70, 0.0), MAT['iron_dark'], coll, segments=40)
    L.curve_tube("Bucket handle",
                 [(-3.96, 2.70, 0.28), (-3.90, 2.70, 0.40), (-3.80, 2.70, 0.44),
                  (-3.70, 2.70, 0.40), (-3.64, 2.70, 0.28)],
                 0.008, MAT['iron'], coll)
    L.tube_between("Broom handle", (-4.55, 3.45, 0.03),
                   (-4.34, 3.25, 1.55), 0.025, MAT['wood_light'], coll)
    L.lathe("Broom head", [(0.0, 0.0), (0.10, 0.02), (0.13, 0.20),
                            (0.08, 0.26), (0.0, 0.28)],
            (-4.55, 3.45, 0.03), MAT['straw'], coll, segments=24)
    # a newspaper bundle on the floor
    for i in range(5):
        L.box(f"Newspaper bundle {i}", (0.46, 0.32, 0.035),
              (2.22, -1.42, 0.025 + i*0.038), MAT['paper_dark'], coll,
              rot=(0, 0, 0.08*(i-2)), bevel=0.002)
    # a discarded glass plate, face up
    L.plane("Discarded glass plate", 0.30, 0.22, (-2.55, -1.65, 0.015),
            MAT['glass_window'], coll, rot=(0, 0, 0.38))
    # scattered paper / prints on the floor
    for i in range(10):
        x = RNG.uniform(-4.2, 4.2)
        y = RNG.uniform(-3.7, 3.4)
        if -2.0 < x < 2.2 and -1.2 < y < 1.9:
            continue
        L.plane(f"Floor paper {i}", RNG.uniform(0.10, 0.28), RNG.uniform(0.12, 0.32),
                (x, y, 0.012), MAT['paper_dark'] if i % 3 else MAT['paper'], coll,
                rot=(0, 0, RNG.uniform(0, 6.28)))
    # straw and grit
    for i in range(75):
        x = RNG.uniform(-4.6, 4.6)
        y = RNG.uniform(-3.7, 3.7)
        if abs(x) < 2.0 and abs(y) < 1.0:
            continue
        z = 0.015
        L.curve_tube(f"Straw {i}",
                     [(x, y, z), (x+RNG.uniform(-0.15, 0.15), y+RNG.uniform(-0.12, 0.12), z+0.004),
                      (x+RNG.uniform(-0.28, 0.28), y+RNG.uniform(-0.22, 0.22), z)],
                     RNG.uniform(0.0025, 0.005), MAT['straw'], coll)
    # small stones / debris
    for i in range(35):
        x = RNG.uniform(-4.7, 4.7)
        y = RNG.uniform(-3.7, 3.7)
        L.sphere(f"Debris {i}", RNG.uniform(0.01, 0.035), (x, y, 0.012),
                 MAT['stone_2'], coll, scale=(1.4, 1.0, 0.5),
                 segments=8, rings=6)
    # a discarded glass plate, face up
    L.plane("Discarded glass plate", 0.30, 0.22, (-2.55, -1.65, 0.015),
            MAT['glass_window'], coll, rot=(0, 0, 0.38))
    # a coil of rope on the floor
    pts = []
    for i in range(40):
        a = i / 39 * math.pi * 5.2
        r = 0.18 + 0.03 * math.sin(a*0.7)
        pts.append((1.55 + r*math.cos(a), -1.85 + r*math.sin(a), 0.025))
    L.curve_tube("Coiled rope", pts, 0.008, MAT['rope'], coll)


def build_dust(coll):
    # one mesh of tiny floating dust diamonds; catches the light shafts
    verts = []
    faces = []
    rng = random.Random(19261031)
    for i in range(430):
        if rng.random() < 0.62:
            x = rng.uniform(-1.3, 1.5)
            y = rng.uniform(-0.2, 2.2)
            z = rng.uniform(0.25, 2.45)
        else:
            x = rng.uniform(-4.6, 4.6)
            y = rng.uniform(-3.6, 3.6)
            z = rng.uniform(0.2, 2.4)
        s = rng.uniform(0.00045, 0.0015)
        j = len(verts)
        verts.extend([(x, y, z+s*1.8), (x, y, z-s*1.8),
                      (x+s, y, z), (x-s, y, z),
                      (x, y+s, z), (x, y-s, z)])
        faces.extend([(j, j+2, j+4), (j, j+4, j+3), (j, j+3, j+5),
                      (j, j+5, j+2), (j+1, j+4, j+2), (j+1, j+3, j+4),
                      (j+1, j+5, j+3), (j+1, j+2, j+5)])
    me = bpy.data.meshes.new("Dust motes")
    me.from_pydata(verts, [], faces)
    me.update()
    me.materials.append(MAT['dust'])
    obj = bpy.data.objects.new("Dust motes", me)
    coll.objects.link(obj)
    return obj


def build_props():
    coll = L.collection("Props")
    build_workbench(coll)
    build_hero_camera(coll)
    build_lantern(coll)
    build_tabletop(coll)
    build_portrait_wall(coll)
    build_west_side(coll)
    build_east_side(coll)
    build_floor_clutter(coll)
    dust_coll = L.collection("Atmosphere")
    build_dust(dust_coll)
    return coll
