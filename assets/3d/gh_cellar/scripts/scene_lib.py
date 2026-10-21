import bpy
import bmesh
import math
import random
import os
from mathutils import Vector, Euler, Quaternion

ROOT = os.path.dirname(os.path.abspath(__file__))
TEX = os.path.join(ROOT, "textures")
RNG = random.Random(19261031)

# -----------------------------------------------------------------------------
# collections / basic object utilities
# -----------------------------------------------------------------------------

def clear_scene():
    bpy.ops.wm.read_factory_settings(use_empty=True)
    for block in (bpy.data.meshes, bpy.data.materials, bpy.data.curves,
                  bpy.data.cameras, bpy.data.lights, bpy.data.images):
        for b in list(block):
            try:
                block.remove(b)
            except Exception:
                pass
    RNG.seed(19261031)


def collection(name, parent=None):
    c = bpy.data.collections.get(name)
    if c is None:
        c = bpy.data.collections.new(name)
        (parent or bpy.context.scene.collection).children.link(c)
    return c


def _finish(name, bm, mat, coll, loc=(0, 0, 0), rot=(0, 0, 0),
            smooth=False, bevel_mod=0.0, bevel_segments=2):
    me = bpy.data.meshes.new(name)
    bm.to_mesh(me)
    bm.free()
    me.update()
    obj = bpy.data.objects.new(name, me)
    coll.objects.link(obj)
    obj.location = loc
    obj.rotation_euler = Euler(rot, 'XYZ')
    if mat is not None:
        mats = mat if isinstance(mat, (list, tuple)) else [mat]
        for m in mats:
            me.materials.append(m)
    if smooth:
        me.shade_smooth()
    if bevel_mod > 0:
        md = obj.modifiers.new("micro_bevel", 'BEVEL')
        md.width = bevel_mod
        md.segments = bevel_segments
        md.limit_method = 'ANGLE'
        md.angle_limit = math.radians(50)
    return obj


def _bevel_bm(bm, width, segments=2):
    if width <= 0:
        return
    try:
        bmesh.ops.bevel(bm, geom=list(bm.edges), offset=width,
                        offset_type='OFFSET', segments=segments,
                        profile=0.5, affect='EDGES', clamp_overlap=True)
    except Exception:
        pass


def box(name, dims, loc, mat, coll, rot=(0, 0, 0), bevel=0.0,
        segments=2, smooth=False):
    dx, dy, dz = dims
    bm = bmesh.new()
    bmesh.ops.create_cube(bm, size=1.0)
    for v in bm.verts:
        v.co.x *= dx
        v.co.y *= dy
        v.co.z *= dz
    _bevel_bm(bm, min(bevel, min(dims) * 0.22), segments)
    bmesh.ops.recalc_face_normals(bm, faces=list(bm.faces))
    return _finish(name, bm, mat, coll, loc, rot, smooth=smooth)


def cylinder(name, radius, depth, loc, mat, coll, rot=(0, 0, 0),
             verts=40, bevel=0.0, smooth=True, radius2=None):
    bm = bmesh.new()
    bmesh.ops.create_cone(bm, cap_ends=True, cap_tris=False, segments=verts,
                          radius1=radius, radius2=(radius if radius2 is None else radius2),
                          depth=depth)
    _bevel_bm(bm, min(bevel, min(radius, depth) * 0.2), 2)
    bmesh.ops.recalc_face_normals(bm, faces=list(bm.faces))
    return _finish(name, bm, mat, coll, loc, rot, smooth=smooth)


def sphere(name, radius, loc, mat, coll, scale=(1, 1, 1), rot=(0, 0, 0),
           segments=32, rings=20, smooth=True):
    bm = bmesh.new()
    bmesh.ops.create_uvsphere(bm, u_segments=segments, v_segments=rings, radius=radius)
    for v in bm.verts:
        v.co.x *= scale[0]
        v.co.y *= scale[1]
        v.co.z *= scale[2]
    bmesh.ops.recalc_face_normals(bm, faces=list(bm.faces))
    return _finish(name, bm, mat, coll, loc, rot, smooth=smooth)


def torus(name, major_r, minor_r, loc, mat, coll, rot=(0, 0, 0),
          major_seg=48, minor_seg=12, smooth=True):
    verts = []
    faces = []
    for i in range(major_seg):
        a = 2 * math.pi * i / major_seg
        ca, sa = math.cos(a), math.sin(a)
        for j in range(minor_seg):
            b = 2 * math.pi * j / minor_seg
            cb, sb = math.cos(b), math.sin(b)
            r = major_r + minor_r * cb
            verts.append((r * ca, r * sa, minor_r * sb))
    for i in range(major_seg):
        for j in range(minor_seg):
            i2 = (i + 1) % major_seg
            j2 = (j + 1) % minor_seg
            faces.append((i * minor_seg + j, i2 * minor_seg + j,
                          i2 * minor_seg + j2, i * minor_seg + j2))
    me = bpy.data.meshes.new(name)
    me.from_pydata(verts, [], faces)
    me.update()
    me.materials.append(mat)
    me.shade_smooth()
    obj = bpy.data.objects.new(name, me)
    coll.objects.link(obj)
    obj.location = loc
    obj.rotation_euler = Euler(rot, 'XYZ')
    return obj


def lathe(name, profile, loc, mat, coll, rot=(0, 0, 0), segments=64,
          smooth=True, cap=True):
    """Revolve a profile of (radius, z) pairs around Z. Profile may include
    interior surface points; faces are generated between consecutive points."""
    verts = []
    for r, z in profile:
        if abs(r) < 1e-7:
            verts.append((0.0, 0.0, z))
        else:
            for i in range(segments):
                a = 2 * math.pi * i / segments
                verts.append((r * math.cos(a), r * math.sin(a), z))
    faces = []
    # map profile index to vertex ring start
    ring = []
    cursor = 0
    for r, z in profile:
        if abs(r) < 1e-7:
            ring.append(cursor)
            cursor += 1
        else:
            ring.append(cursor)
            cursor += segments
    for k in range(len(profile) - 1):
        r0, _ = profile[k]
        r1, _ = profile[k + 1]
        if abs(r0) < 1e-7 and abs(r1) < 1e-7:
            continue
        if abs(r0) < 1e-7:
            a = ring[k]
            b = ring[k + 1]
            for i in range(segments):
                i2 = (i + 1) % segments
                faces.append((a, b + i, b + i2))
        elif abs(r1) < 1e-7:
            a = ring[k]
            b = ring[k + 1]
            for i in range(segments):
                i2 = (i + 1) % segments
                faces.append((a + i, b, a + i2))
        else:
            a = ring[k]
            b = ring[k + 1]
            for i in range(segments):
                i2 = (i + 1) % segments
                faces.append((a + i, b + i, b + i2, a + i2))
    me = bpy.data.meshes.new(name)
    me.from_pydata(verts, [], faces)
    me.update()
    me.materials.append(mat)
    if smooth:
        me.shade_smooth()
    obj = bpy.data.objects.new(name, me)
    coll.objects.link(obj)
    obj.location = loc
    obj.rotation_euler = Euler(rot, 'XYZ')
    return obj


def beam_between(name, a, b, width, height, mat, coll, bevel=0.0):
    a = Vector(a)
    b = Vector(b)
    d = b - a
    length = d.length
    obj = box(name, (width, height, length), (0, 0, 0), mat, coll,
              bevel=bevel)
    obj.rotation_mode = 'QUATERNION'
    obj.rotation_quaternion = d.to_track_quat('Z', 'Y')
    obj.location = (a + b) * 0.5
    return obj


def tube_between(name, a, b, radius, mat, coll, verts=16):
    a = Vector(a)
    b = Vector(b)
    d = b - a
    obj = cylinder(name, radius, d.length, (0, 0, 0), mat, coll,
                   verts=verts)
    obj.rotation_mode = 'QUATERNION'
    obj.rotation_quaternion = d.to_track_quat('Z', 'Y')
    obj.location = (a + b) * 0.5
    return obj


def curve_tube(name, points, radius, mat, coll, resolution=2):
    cu = bpy.data.curves.new(name, 'CURVE')
    cu.dimensions = '3D'
    cu.resolution_u = resolution
    cu.bevel_depth = radius
    cu.bevel_resolution = 3
    cu.use_fill_caps = True
    sp = cu.splines.new('POLY')
    sp.points.add(len(points) - 1)
    for p, co in zip(sp.points, points):
        p.co = (*co, 1.0)
    obj = bpy.data.objects.new(name, cu)
    coll.objects.link(obj)
    cu.materials.append(mat)
    return obj


def grid_cloth(name, width, height, loc, mat, coll, rot=(0, 0, 0),
               nx=18, nz=30, amp=0.025, freq=(3.0, 2.0), thickness=0.003,
               seed=0):
    rng = random.Random(seed or RNG.randint(0, 999999))
    verts = []
    faces = []
    phase = rng.random() * 6.0
    for j in range(nz + 1):
        z = -height / 2 + height * j / nz
        for i in range(nx + 1):
            x = -width / 2 + width * i / nx
            u = i / nx
            v = j / nz
            y = amp * (
                math.sin(u * math.pi * freq[0] + phase) * 0.6 +
                math.sin(v * math.pi * freq[1] + phase * 1.7) * 0.5 +
                math.sin((u + v) * math.pi * 2.4 + phase) * 0.25
            )
            y += rng.uniform(-0.003, 0.003)
            verts.append((x, y, z))
    for j in range(nz):
        for i in range(nx):
            a = j * (nx + 1) + i
            faces.append((a, a + 1, a + nx + 2, a + nx + 1))
    me = bpy.data.meshes.new(name)
    me.from_pydata(verts, [], faces)
    me.update()
    me.materials.append(mat)
    me.shade_smooth()
    obj = bpy.data.objects.new(name, me)
    coll.objects.link(obj)
    obj.location = loc
    obj.rotation_euler = Euler(rot, 'XYZ')
    if thickness:
        sol = obj.modifiers.new("cloth_thickness", 'SOLIDIFY')
        sol.thickness = thickness
        sol.offset = 0.0
    return obj


def plane(name, w, h, loc, mat, coll, rot=(0, 0, 0), subdiv=0):
    me = bpy.data.meshes.new(name)
    if subdiv:
        verts = []
        faces = []
        for j in range(subdiv + 1):
            for i in range(subdiv + 1):
                verts.append((-w/2 + w*i/subdiv, -h/2 + h*j/subdiv, 0))
        for j in range(subdiv):
            for i in range(subdiv):
                a = j*(subdiv+1)+i
                faces.append((a, a+1, a+subdiv+2, a+subdiv+1))
        me.from_pydata(verts, [], faces)
    else:
        me.from_pydata([(-w/2, -h/2, 0), (w/2, -h/2, 0),
                        (w/2, h/2, 0), (-w/2, h/2, 0)], [],
                       [(0, 1, 2, 3)])
    me.update()
    # image textures (portraits, labels) need a proper UV layer
    uvl = me.uv_layers.new(name="UVMap")
    for poly in me.polygons:
        for li in poly.loop_indices:
            v = me.vertices[me.loops[li].vertex_index].co
            uvl.data[li].uv = ((v.x + w/2) / w, (v.y + h/2) / h)
    me.materials.append(mat)
    obj = bpy.data.objects.new(name, me)
    coll.objects.link(obj)
    obj.location = loc
    obj.rotation_euler = Euler(rot, 'XYZ')
    return obj


# -----------------------------------------------------------------------------
# materials
# -----------------------------------------------------------------------------

MAT = {}


def _principled(mat):
    mat.use_nodes = True
    nt = mat.node_tree
    bsdf = nt.nodes.get("Principled BSDF")
    if bsdf is None:
        bsdf = nt.nodes.new("ShaderNodeBsdfPrincipled")
        out = nt.nodes.get("Material Output")
        if out is None:
            out = nt.nodes.new("ShaderNodeOutputMaterial")
        nt.links.new(bsdf.outputs[0], out.inputs[0])
        bsdf.inputs['Roughness'].default_value = 0.6
        bsdf.inputs['Specular IOR Level'].default_value = 0.5
    return nt, bsdf


def _ramp(nt, fac, colors, positions=None, loc=(0, 0)):
    n = nt.nodes.new("ShaderNodeValToRGB")
    n.location = loc
    cr = n.color_ramp
    while len(cr.elements) < len(colors):
        cr.elements.new(0.5)
    for idx, col in enumerate(colors):
        e = cr.elements[idx]
        e.color = (*col, 1.0) if len(col) == 3 else col
        if positions:
            e.position = positions[idx]
    nt.links.new(fac, n.inputs['Fac'])
    return n


def _noise(nt, coord, scale, detail=6, rough=0.55, distortion=0.0, loc=(0, 0)):
    n = nt.nodes.new("ShaderNodeTexNoise")
    n.location = loc
    n.inputs['Scale'].default_value = scale
    n.inputs['Detail'].default_value = detail
    n.inputs['Roughness'].default_value = rough
    if distortion:
        n.inputs['Distortion'].default_value = distortion
    nt.links.new(coord, n.inputs['Vector'])
    return n


def _bump(nt, height, bsdf, strength=0.12, distance=0.03, loc=(0, 0)):
    b = nt.nodes.new("ShaderNodeBump")
    b.location = loc
    b.inputs['Strength'].default_value = strength
    b.inputs['Distance'].default_value = distance
    nt.links.new(height, b.inputs['Height'])
    nt.links.new(b.outputs['Normal'], bsdf.inputs['Normal'])
    return b


def simple_mat(name, color, rough=0.6, metal=0.0, spec=0.5,
               coat=0.0, coat_rough=0.3, emission=None, emission_strength=0.0,
               alpha=1.0, ior=1.45, transmission=0.0):
    m = bpy.data.materials.get(name) or bpy.data.materials.new(name)
    nt, bsdf = _principled(m)
    bsdf.inputs['Base Color'].default_value = (*color, 1.0)
    bsdf.inputs['Roughness'].default_value = rough
    bsdf.inputs['Metallic'].default_value = metal
    bsdf.inputs['Specular IOR Level'].default_value = spec
    bsdf.inputs['Coat Weight'].default_value = coat
    bsdf.inputs['Coat Roughness'].default_value = coat_rough
    bsdf.inputs['IOR'].default_value = ior
    if transmission:
        bsdf.inputs['Transmission Weight'].default_value = transmission
    if emission:
        bsdf.inputs['Emission Color'].default_value = (*emission, 1.0)
        bsdf.inputs['Emission Strength'].default_value = emission_strength
    if alpha < 1.0:
        bsdf.inputs['Alpha'].default_value = alpha
        m.surface_render_method = 'DITHERED'
        m.use_transparent_shadow = True
    return m


def image_mat(name, path, rough=0.4, metallic=0.0, tint=(1, 1, 1),
              emission_strength=0.0):
    m = bpy.data.materials.get(name) or bpy.data.materials.new(name)
    nt, bsdf = _principled(m)
    img = bpy.data.images.load(path, check_existing=True)
    img.colorspace_settings.name = 'sRGB'
    tex = nt.nodes.new("ShaderNodeTexImage")
    tex.image = img
    tex.interpolation = 'Linear'
    tex.extension = 'EXTEND'
    mix = nt.nodes.new("ShaderNodeMixRGB")
    mix.blend_type = 'MULTIPLY'
    mix.inputs['Fac'].default_value = 0.14 if tint != (1, 1, 1) else 0.0
    mix.inputs['Color2'].default_value = (*tint, 1)
    nt.links.new(tex.outputs['Color'], mix.inputs['Color1'])
    nt.links.new(mix.outputs['Color'], bsdf.inputs['Base Color'])
    bsdf.inputs['Roughness'].default_value = rough
    bsdf.inputs['Metallic'].default_value = metallic
    bsdf.inputs['Specular IOR Level'].default_value = 0.45
    if emission_strength:
        bsdf.inputs['Emission Color'].default_value = (*tint, 1)
        bsdf.inputs['Emission Strength'].default_value = emission_strength
    # subtle paper / glass micro-surface
    coord = nt.nodes.new("ShaderNodeTexCoord")
    n = _noise(nt, coord.outputs['Object'], 85, detail=2, rough=0.5)
    _bump(nt, n.outputs['Fac'], bsdf, 0.035, 0.01)
    return m


def wood_mat(name, dark, light, rough=0.52, grain=16.0, coat=0.0,
             bump=0.08, warm=1.0):
    m = bpy.data.materials.get(name) or bpy.data.materials.new(name)
    nt, bsdf = _principled(m)
    coord = nt.nodes.new("ShaderNodeTexCoord")
    objinfo = nt.nodes.new("ShaderNodeObjectInfo")
    # unique offset per object so repeated planks do not share the same grain
    mx = nt.nodes.new("ShaderNodeMath")
    mx.operation = 'MULTIPLY'
    mx.inputs[1].default_value = 0.37
    my = nt.nodes.new("ShaderNodeMath")
    my.operation = 'MULTIPLY'
    my.inputs[1].default_value = 1.31
    nt.links.new(objinfo.outputs['Random'], mx.inputs[0])
    nt.links.new(objinfo.outputs['Random'], my.inputs[0])
    comb = nt.nodes.new("ShaderNodeCombineXYZ")
    nt.links.new(mx.outputs['Value'], comb.inputs['X'])
    nt.links.new(my.outputs['Value'], comb.inputs['Y'])
    mapping = nt.nodes.new("ShaderNodeMapping")
    mapping.vector_type = 'POINT'
    mapping.inputs['Scale'].default_value = (0.24, 1.55, 1.0)
    nt.links.new(coord.outputs['Object'], mapping.inputs['Vector'])
    nt.links.new(comb.outputs['Vector'], mapping.inputs['Location'])
    tex = nt.nodes.new("ShaderNodeTexImage")
    tex.image = bpy.data.images.load(os.path.join(TEX, "wood_grain.png"), check_existing=True)
    tex.image.colorspace_settings.name = 'Non-Color'
    tex.interpolation = 'Linear'
    tex.extension = 'REPEAT'
    nt.links.new(mapping.outputs['Vector'], tex.inputs['Vector'])
    mid = tuple(d*0.34 + l*0.66 for d, l in zip(dark, light))
    mid2 = tuple(d*0.62 + l*0.38 for d, l in zip(dark, light))
    ramp = _ramp(nt, tex.outputs['Color'], [dark, mid, light, mid2],
                 [0.10, 0.38, 0.63, 0.92])
    # large-scale patina / colour drift
    n2 = _noise(nt, coord.outputs['Object'], 1.2, detail=4, rough=0.6)
    ramp2 = _ramp(nt, n2.outputs['Fac'],
                  [(dark[0]*0.55, dark[1]*0.55, dark[2]*0.55),
                   (min(1, light[0]*1.12), min(1, light[1]*1.12), min(1, light[2]*1.12))],
                  [0.18, 0.8])
    mix = nt.nodes.new("ShaderNodeMixRGB")
    mix.blend_type = 'MULTIPLY'
    mix.inputs['Fac'].default_value = 0.30
    nt.links.new(ramp.outputs['Color'], mix.inputs['Color1'])
    nt.links.new(ramp2.outputs['Color'], mix.inputs['Color2'])
    nt.links.new(mix.outputs['Color'], bsdf.inputs['Base Color'])
    # rough, slightly varied surface
    mr = nt.nodes.new("ShaderNodeMapRange")
    mr.inputs['To Min'].default_value = max(0.25, rough - 0.08)
    mr.inputs['To Max'].default_value = min(0.95, rough + 0.12)
    nt.links.new(n2.outputs['Fac'], mr.inputs['Value'])
    nt.links.new(mr.outputs['Result'], bsdf.inputs['Roughness'])
    bsdf.inputs['Specular IOR Level'].default_value = 0.42
    bsdf.inputs['Coat Weight'].default_value = coat
    bsdf.inputs['Coat Roughness'].default_value = 0.35
    b = nt.nodes.new("ShaderNodeBump")
    b.inputs['Strength'].default_value = max(0.12, bump * 2.2)
    b.inputs['Distance'].default_value = 0.012
    nt.links.new(tex.outputs['Color'], b.inputs['Height'])
    nt.links.new(b.outputs['Normal'], bsdf.inputs['Normal'])
    return m


def brick_mat(name, dark, light, rough=0.78, seed=0, soot=0.55):
    m = bpy.data.materials.get(name) or bpy.data.materials.new(name)
    nt, bsdf = _principled(m)
    coord = nt.nodes.new("ShaderNodeTexCoord")
    n = _noise(nt, coord.outputs['Object'], 22, detail=8, rough=0.7, distortion=0.4)
    ramp = _ramp(nt, n.outputs['Fac'], [dark, light], [0.24, 0.78])
    # darkening toward ceiling / soot
    sep = nt.nodes.new("ShaderNodeSeparateXYZ")
    nt.links.new(coord.outputs['Object'], sep.inputs['Vector'])
    mr = nt.nodes.new("ShaderNodeMapRange")
    mr.inputs['From Min'].default_value = 1.2
    mr.inputs['From Max'].default_value = 2.65
    mr.inputs['To Min'].default_value = 1.0
    mr.inputs['To Max'].default_value = 1.0 - soot
    nt.links.new(sep.outputs['Z'], mr.inputs['Value'])
    # break the gradient with noise
    n2 = _noise(nt, coord.outputs['Object'], 4.5, detail=5, rough=0.7)
    mixf = nt.nodes.new("ShaderNodeMixRGB")
    mixf.blend_type = 'MULTIPLY'
    mixf.inputs['Fac'].default_value = 0.35
    nt.links.new(mr.outputs['Result'], mixf.inputs['Color1'])
    nt.links.new(n2.outputs['Color'], mixf.inputs['Color2'])
    dark_mix = nt.nodes.new("ShaderNodeMixRGB")
    dark_mix.blend_type = 'MULTIPLY'
    dark_mix.inputs['Fac'].default_value = 0.52
    dark_mix.inputs['Color2'].default_value = (0.30, 0.19, 0.13, 1)
    nt.links.new(ramp.outputs['Color'], dark_mix.inputs['Color1'])
    nt.links.new(mixf.outputs['Color'], dark_mix.inputs['Fac'])
    nt.links.new(dark_mix.outputs['Color'], bsdf.inputs['Base Color'])
    bsdf.inputs['Roughness'].default_value = rough
    bsdf.inputs['Specular IOR Level'].default_value = 0.32
    n3 = _noise(nt, coord.outputs['Object'], 55, detail=5, rough=0.75)
    _bump(nt, n3.outputs['Fac'], bsdf, 0.18, 0.015)
    return m


def stone_mat(name, dark, light, rough=0.7, scale=9.0):
    m = bpy.data.materials.get(name) or bpy.data.materials.new(name)
    nt, bsdf = _principled(m)
    coord = nt.nodes.new("ShaderNodeTexCoord")
    n = _noise(nt, coord.outputs['Object'], scale, detail=7, rough=0.65)
    ramp = _ramp(nt, n.outputs['Fac'], [dark, light], [0.2, 0.8])
    # worn bevels
    geo = nt.nodes.new("ShaderNodeNewGeometry")
    pr = _ramp(nt, geo.outputs['Pointiness'],
               [(dark[0]*0.55, dark[1]*0.55, dark[2]*0.55), light],
               [0.35, 0.65])
    mix = nt.nodes.new("ShaderNodeMixRGB")
    mix.blend_type = 'SCREEN'
    mix.inputs['Fac'].default_value = 0.16
    nt.links.new(ramp.outputs['Color'], mix.inputs['Color1'])
    nt.links.new(pr.outputs['Color'], mix.inputs['Color2'])
    nt.links.new(mix.outputs['Color'], bsdf.inputs['Base Color'])
    bsdf.inputs['Roughness'].default_value = rough
    bsdf.inputs['Specular IOR Level'].default_value = 0.3
    n2 = _noise(nt, coord.outputs['Object'], 80, detail=6, rough=0.8)
    _bump(nt, n2.outputs['Fac'], bsdf, 0.32, 0.02)
    return m


def plaster_mat(name, base, rough=0.9, cracks=0.4):
    m = bpy.data.materials.get(name) or bpy.data.materials.new(name)
    nt, bsdf = _principled(m)
    coord = nt.nodes.new("ShaderNodeTexCoord")
    n = _noise(nt, coord.outputs['Object'], 8, detail=9, rough=0.7)
    ramp = _ramp(nt, n.outputs['Fac'],
                 [(base[0]*0.55, base[1]*0.55, base[2]*0.55),
                  (min(1, base[0]*1.18), min(1, base[1]*1.18), min(1, base[2]*1.18))],
                 [0.2, 0.8])
    vor = nt.nodes.new("ShaderNodeTexVoronoi")
    vor.feature = 'DISTANCE_TO_EDGE'
    vor.inputs['Scale'].default_value = 7.0
    nt.links.new(coord.outputs['Object'], vor.inputs['Vector'])
    vr = _ramp(nt, vor.outputs['Distance'], [(0.03, 0.025, 0.02), (base[0]*0.82, base[1]*0.82, base[2]*0.82)],
               [0.0, 0.075])
    mix = nt.nodes.new("ShaderNodeMixRGB")
    mix.blend_type = 'MULTIPLY'
    mix.inputs['Fac'].default_value = cracks
    nt.links.new(ramp.outputs['Color'], mix.inputs['Color1'])
    nt.links.new(vr.outputs['Color'], mix.inputs['Color2'])
    nt.links.new(mix.outputs['Color'], bsdf.inputs['Base Color'])
    bsdf.inputs['Roughness'].default_value = rough
    bsdf.inputs['Specular IOR Level'].default_value = 0.22
    n2 = _noise(nt, coord.outputs['Object'], 45, detail=6, rough=0.7)
    _bump(nt, n2.outputs['Fac'], bsdf, 0.22, 0.035)
    return m


def metal_mat(name, base, rough=0.38, metal=0.92, rust=0.0, rust_color=(0.19, 0.055, 0.015)):
    m = bpy.data.materials.get(name) or bpy.data.materials.new(name)
    nt, bsdf = _principled(m)
    coord = nt.nodes.new("ShaderNodeTexCoord")
    bsdf.inputs['Base Color'].default_value = (*base, 1.0)
    bsdf.inputs['Metallic'].default_value = metal
    bsdf.inputs['Roughness'].default_value = rough
    bsdf.inputs['Specular IOR Level'].default_value = 0.6
    if rust:
        n = _noise(nt, coord.outputs['Object'], 11, detail=8, rough=0.7)
        ramp = _ramp(nt, n.outputs['Fac'], [base, rust_color], [0.52, 0.82])
        mix = nt.nodes.new("ShaderNodeMixRGB")
        mix.blend_type = 'MIX'
        mix.inputs['Fac'].default_value = rust
        nt.links.new(ramp.outputs['Color'], mix.inputs['Color1'])
        mix.inputs['Color2'].default_value = (*rust_color, 1)
        nt.links.new(mix.outputs['Color'], bsdf.inputs['Base Color'])
        bsdf.inputs['Metallic'].default_value = metal * (1 - rust * 0.45)
        mr = nt.nodes.new("ShaderNodeMapRange")
        mr.inputs['To Min'].default_value = rough
        mr.inputs['To Max'].default_value = 0.9
        nt.links.new(n.outputs['Fac'], mr.inputs['Value'])
        nt.links.new(mr.outputs['Result'], bsdf.inputs['Roughness'])
        n2 = _noise(nt, coord.outputs['Object'], 38, detail=5, rough=0.8)
        _bump(nt, n2.outputs['Fac'], bsdf, 0.2, 0.02)
    return m


def cloth_mat(name, base, rough=0.92, sheen=0.35, bump=0.25, scale=30, spec=0.25):
    m = bpy.data.materials.get(name) or bpy.data.materials.new(name)
    nt, bsdf = _principled(m)
    bsdf.inputs['Base Color'].default_value = (*base, 1.0)
    bsdf.inputs['Roughness'].default_value = rough
    bsdf.inputs['Specular IOR Level'].default_value = spec
    bsdf.inputs['Sheen Weight'].default_value = sheen
    bsdf.inputs['Sheen Roughness'].default_value = 0.55
    bsdf.inputs['Sheen Tint'].default_value = (0.55, 0.5, 0.4, 1)
    coord = nt.nodes.new("ShaderNodeTexCoord")
    n = _noise(nt, coord.outputs['Object'], scale, detail=5, rough=0.7)
    _bump(nt, n.outputs['Fac'], bsdf, bump, 0.02)
    return m


def leather_mat(name, base, rough=0.55, scale=90, bump=0.12):
    m = simple_mat(name, base, rough, spec=0.22, coat=0.06, coat_rough=0.4)
    nt, bsdf = _principled(m)
    coord = nt.nodes.new("ShaderNodeTexCoord")
    n = _noise(nt, coord.outputs['Object'], scale, detail=5, rough=0.65)
    _bump(nt, n.outputs['Fac'], bsdf, bump, 0.008)
    return m


def build_materials():
    MAT.clear()
    MAT['brick_mortar'] = plaster_mat("Brick mortar", (0.11, 0.095, 0.075), 0.95, 0.35)
    MAT['brick_backing'] = simple_mat("Brick backing dark", (0.035, 0.028, 0.022), 0.95)
    MAT['brick_0'] = brick_mat("Brick 00", (0.11, 0.036, 0.022), (0.32, 0.11, 0.055), 0.82, 1, 0.5)
    MAT['brick_1'] = brick_mat("Brick 01", (0.13, 0.045, 0.028), (0.37, 0.145, 0.075), 0.8, 2, 0.45)
    MAT['brick_2'] = brick_mat("Brick 02", (0.095, 0.032, 0.023), (0.28, 0.095, 0.055), 0.85, 3, 0.6)
    MAT['brick_3'] = brick_mat("Brick 03", (0.145, 0.06, 0.037), (0.42, 0.18, 0.09), 0.78, 4, 0.42)
    MAT['brick_4'] = brick_mat("Brick 04", (0.11, 0.04, 0.028), (0.33, 0.13, 0.075), 0.82, 5, 0.5)
    MAT['brick_5'] = brick_mat("Brick 05", (0.08, 0.03, 0.022), (0.23, 0.085, 0.052), 0.88, 6, 0.65)
    MAT['brick_6'] = brick_mat("Brick 06", (0.12, 0.055, 0.043), (0.34, 0.17, 0.12), 0.8, 7, 0.55)
    MAT['brick_7'] = brick_mat("Brick 07", (0.14, 0.05, 0.03), (0.39, 0.15, 0.075), 0.79, 8, 0.4)
    MAT['brick_list'] = [MAT[f'brick_{i}'] for i in range(8)]

    MAT['wood_dark'] = wood_mat("Old dark oak", (0.017, 0.010, 0.006), (0.095, 0.055, 0.028), 0.56, 14, 0.05)
    MAT['wood_beam'] = wood_mat("Sooty beam oak", (0.013, 0.008, 0.005), (0.078, 0.047, 0.025), 0.62, 9, 0.0, 0.11)
    MAT['wood_bench'] = wood_mat("Worn bench pine", (0.035, 0.017, 0.007), (0.190, 0.100, 0.040), 0.52, 14, 0.03, 0.10)
    MAT['wood_bench_2'] = wood_mat("Worn bench pine B", (0.030, 0.016, 0.008), (0.160, 0.085, 0.040), 0.55, 14, 0.02, 0.10)
    MAT['wood_bench_3'] = wood_mat("Worn bench pine C", (0.028, 0.015, 0.008), (0.145, 0.078, 0.038), 0.58, 14, 0.01, 0.10)
    MAT['table_felt'] = cloth_mat("Table felt", (0.048, 0.035, 0.020), 0.98, 0.03, 0.10, 60, 0.04)
    MAT['wood_floor'] = wood_mat("Floor boards", (0.022, 0.014, 0.008), (0.082, 0.050, 0.024), 0.64, 12, 0.0, 0.12)
    MAT['wood_crate'] = wood_mat("Crate pine", (0.060, 0.032, 0.016), (0.210, 0.118, 0.054), 0.66, 10, 0.0, 0.12)
    MAT['wood_mahogany'] = wood_mat("Camera mahogany", (0.020, 0.006, 0.003), (0.090, 0.027, 0.011), 0.42, 16, 0.18, 0.03)
    MAT['wood_frames'] = wood_mat("Frame walnut", (0.017, 0.008, 0.004), (0.082, 0.036, 0.016), 0.42, 14, 0.12)
    MAT['wood_light'] = wood_mat("Pale worn wood", (0.080, 0.048, 0.024), (0.270, 0.160, 0.075), 0.62, 10, 0.0, 0.08)
    MAT['wood_door'] = wood_mat("Door oak", (0.020, 0.012, 0.007), (0.105, 0.058, 0.027), 0.6, 10, 0.02)
    MAT['wood_ladder'] = wood_mat("Ladder ash", (0.055, 0.033, 0.018), (0.210, 0.132, 0.066), 0.58, 11, 0.0, 0.15)

    MAT['plaster'] = plaster_mat("Aged plaster", (0.235, 0.220, 0.185), 0.92, 0.5)
    MAT['plaster_grey'] = plaster_mat("Grey plaster", (0.165, 0.170, 0.162), 0.92, 0.55)
    MAT['plaster_ochre'] = plaster_mat("Ochre plaster", (0.210, 0.175, 0.115), 0.93, 0.45)
    MAT['soot'] = simple_mat("Soot stain", (0.012, 0.010, 0.008), 0.95, alpha=0.82)
    MAT['grime'] = simple_mat("Floor grime", (0.040, 0.028, 0.016), 0.96, alpha=0.34)
    MAT['moss'] = simple_mat("Moss", (0.035, 0.045, 0.022), 0.95)

    MAT['stone_0'] = stone_mat("Flagstone 0", (0.038, 0.034, 0.028), (0.165, 0.145, 0.115), 0.68, 8)
    MAT['stone_1'] = stone_mat("Flagstone 1", (0.048, 0.042, 0.033), (0.195, 0.170, 0.132), 0.72, 6)
    MAT['stone_2'] = stone_mat("Flagstone 2", (0.032, 0.030, 0.026), (0.135, 0.125, 0.105), 0.64, 10)
    MAT['stone_3'] = stone_mat("Flagstone 3", (0.052, 0.045, 0.035), (0.215, 0.180, 0.132), 0.74, 5)
    MAT['stone_4'] = stone_mat("Flagstone 4", (0.040, 0.036, 0.029), (0.180, 0.155, 0.115), 0.70, 12)
    MAT['stone_list'] = [MAT[f'stone_{i}'] for i in range(5)]
    MAT['grout'] = simple_mat("Grout", (0.028, 0.025, 0.020), 0.95)

    MAT['iron'] = metal_mat("Blackened iron", (0.018, 0.017, 0.015), 0.52, 0.88, 0.18)
    MAT['iron_dark'] = metal_mat("Dark iron", (0.012, 0.011, 0.010), 0.66, 0.75, 0.25)
    MAT['brass'] = metal_mat("Aged brass", (0.24, 0.13, 0.032), 0.38, 0.96, 0.12, (0.20, 0.10, 0.02))
    MAT['brass_dark'] = metal_mat("Tarnished brass", (0.14, 0.075, 0.022), 0.50, 0.92, 0.22)
    MAT['silver'] = metal_mat("Silver", (0.55, 0.55, 0.52), 0.18, 1.0, 0.0)
    MAT['copper'] = metal_mat("Copper", (0.36, 0.12, 0.04), 0.32, 0.95, 0.2)
    MAT['rust'] = simple_mat("Rust", (0.17, 0.055, 0.018), 0.95)

    MAT['glass'] = simple_mat("Old glass", (0.65, 0.75, 0.68), 0.08, 0.0, 0.5, transmission=0.92, ior=1.45)
    MAT['glass_window'] = simple_mat("Dirty window glass", (0.45, 0.55, 0.50), 0.28, 0.0, 0.5, transmission=0.78, ior=1.47)
    MAT['glass_safelight'] = simple_mat("Red safelight glass", (0.32, 0.014, 0.006), 0.22, 0.0, 0.5, transmission=0.65, ior=1.5)
    MAT['glass_sheen'] = simple_mat("Glass sheen", (0.55, 0.62, 0.60), 0.05, 0.0, 0.5, alpha=0.14)
    MAT['lens_glass'] = simple_mat("Lens glass", (0.08, 0.19, 0.18), 0.03, 0.0, 1.0, transmission=0.75, ior=1.62)
    MAT['liquid'] = simple_mat("Developer liquid", (0.055, 0.038, 0.023), 0.08, 0.0, 0.7, transmission=0.25, ior=1.33)
    MAT['water'] = simple_mat("Water", (0.24, 0.28, 0.27), 0.03, 0.0, 0.7, transmission=0.9, ior=1.333)

    MAT['paper'] = simple_mat("Aged paper", (0.48, 0.40, 0.27), 0.90, 0.0, 0.28)
    MAT['paper_dark'] = simple_mat("Old paper dark", (0.28, 0.22, 0.14), 0.92, 0.0, 0.25)
    MAT['card'] = simple_mat("Card board", (0.35, 0.28, 0.18), 0.94, 0.0, 0.2)
    MAT['enamel'] = simple_mat("White enamel", (0.72, 0.70, 0.63), 0.16, 0.0, 0.6, coat=0.7, coat_rough=0.12)
    MAT['enamel_blue'] = simple_mat("Blue enamel rim", (0.055, 0.09, 0.10), 0.2, 0.0, 0.5, coat=0.5)
    MAT['ceramic'] = simple_mat("Aged ceramic", (0.48, 0.43, 0.33), 0.3, 0.0, 0.5, coat=0.3)
    MAT['slate'] = stone_mat("Dark slate", (0.025, 0.026, 0.025), (0.10, 0.105, 0.10), 0.5, 14)
    MAT['leather'] = simple_mat("Worn leather", (0.095, 0.043, 0.020), 0.54, 0.0, 0.3, coat=0.15, coat_rough=0.5)
    MAT['leather_dark'] = simple_mat("Black leather", (0.018, 0.013, 0.010), 0.5, 0.0, 0.35, coat=0.25, coat_rough=0.4)
    MAT['felt'] = cloth_mat("Felt", (0.085, 0.072, 0.050), 0.96, 0.2, 0.12, 80)
    MAT['canvas_apron'] = cloth_mat("Canvas apron", (0.33, 0.30, 0.22), 0.95, 0.25, 0.3, 42)
    MAT['cloth_dark'] = cloth_mat("Dark cloth", (0.012, 0.009, 0.007), 0.98, 0.02, 0.42, 55, 0.06)
    MAT['bellows'] = leather_mat("Bellows leather", (0.022, 0.013, 0.008), 0.54, 90, 0.10)
    MAT['cloth_olive'] = cloth_mat("Olive canvas", (0.10, 0.095, 0.062), 0.95, 0.25, 0.32, 38)
    MAT['cloth_burlap'] = cloth_mat("Burlap", (0.28, 0.23, 0.15), 0.98, 0.15, 0.4, 70)
    MAT['cloth_tarp'] = cloth_mat("Old tarpaulin", (0.095, 0.082, 0.055), 0.97, 0.2, 0.45, 46)
    MAT['straw'] = simple_mat("Straw", (0.46, 0.35, 0.16), 0.85, 0.0, 0.2)
    MAT['rope'] = simple_mat("Rope", (0.29, 0.24, 0.14), 0.92, 0.0, 0.2)
    MAT['wax'] = simple_mat("Wax", (0.64, 0.52, 0.32), 0.55, 0.0, 0.3)
    MAT['flame'] = simple_mat("Flame", (1.0, 0.52, 0.12), 0.4, emission=(1.0, 0.42, 0.08), emission_strength=9)
    MAT['red_bulb'] = simple_mat("Red bulb", (0.7, 0.02, 0.01), 0.2, emission=(1.0, 0.015, 0.004), emission_strength=8)
    MAT['photo_edge'] = simple_mat("Photo edge", (0.20, 0.17, 0.12), 0.9)
    MAT['dust'] = simple_mat("Dust motes", (0.58, 0.53, 0.44), 0.8, emission=(0.70, 0.60, 0.42), emission_strength=0.16)
    MAT['label_back'] = simple_mat("Label backing", (0.22, 0.19, 0.14), 0.9)

    # image materials for the portrait wall
    for i in range(1, 13):
        p = os.path.join(TEX, f"portrait_alt_{i:02d}.png")
        if not os.path.exists(p):
            p = os.path.join(TEX, f"portrait_{i:02d}.png")
        if os.path.exists(p):
            MAT[f'portrait_{i:02d}'] = image_mat(f"Portrait {i:02d}", p, 0.46, tint=(0.90, 0.82, 0.68))
    for key, fn in [('film', 'label_film.png'), ('plates', 'label_plates.png'),
                    ('fragile', 'label_fragile.png'), ('darkroom', 'label_darkroom.png'),
                    ('chemicals', 'label_chemicals.png'), ('london', 'label_london.png'),
                    ('1926', 'label_1926.png'), ('camera', 'label_camera.png')]:
        p = os.path.join(TEX, fn)
        if os.path.exists(p):
            MAT['label_' + key] = image_mat(f"Label {key}", p, 0.76, tint=(0.95, 0.9, 0.8))
    return MAT
