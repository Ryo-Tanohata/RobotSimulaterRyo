"""川辺の五人のひとり「セナ」(1日目・29歳の女性) を、クラウドで 3D 人物にする。

使いかた (README.md を参照):
    BLENDER_USER_RESOURCES=/dev/shm/sena/userres PYTHONPATH=/dev/shm/bpy \
        python3.11 run.py build_sena.py [--quick] [--person sena]

- 体は MakeHuman の基本メッシュ (CC0) を MPFB2 で読み、年齢・体重・筋肉などを
  プロフィールに合わせて変形する。
- 髪・貫頭衣・帯・眉・傷はこのスクリプトが手続き的に作る。
- 出力: PNG を sim/society/out/human/ に、.glb を /dev/shm/sena/ に書く。
"""
import argparse
import importlib
import math
import os
import sys
import time

import bpy
import addon_utils
import bmesh
import numpy as np
from mathutils import Vector, Matrix, Euler
from mathutils.bvhtree import BVHTree

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.abspath(os.path.join(HERE, "..", "..", "..", ".."))
ASSETS = os.environ.get("HUMAN_ASSETS", "/dev/shm/sena/assets")
OUT_PNG = os.path.join(REPO, "sim", "society", "out", "human")
OUT_GLB = os.environ.get("HUMAN_GLB_DIR", "/dev/shm/sena")

sys.path.insert(0, HERE)
from people import PEOPLE, STYLES  # noqa: E402
import copy  # noqa: E402


def srgb(h):
    """'#rrggbb' -> 線形 RGBA"""
    h = h.lstrip("#")
    c = [int(h[i:i + 2], 16) / 255.0 for i in (0, 2, 4)]
    lin = [x / 12.92 if x <= 0.04045 else ((x + 0.055) / 1.055) ** 2.4 for x in c]
    return (*lin, 1.0)


# ---------------------------------------------------------------- MPFB
def setup_mpfb():
    prefs = bpy.context.preferences
    if "mh" not in [r.module for r in prefs.extensions.repos]:
        prefs.extensions.repos.new(name="mh", module="mh",
                                   custom_directory=os.path.join(ASSETS, "ext"), source='USER')
    addon_utils.enable("bl_ext.mh.mpfb", default_set=True)
    m = lambda n: importlib.import_module("bl_ext.mh.mpfb.services." + n)  # noqa: E731
    return (m("humanservice").HumanService, m("targetservice").TargetService)


def make_body(P, HS, TS):
    body = HS.create_human(macro_detail_dict=P["macro"], mask_helpers=True)
    body.name = P["name"] + "_body"
    for tname, w in P["targets"].items():
        path = TS.target_full_path(tname)
        if path is None:
            print("target not found:", tname)
            continue
        TS.load_target(body, path, weight=w)
    # 足を地面に合わせなおす
    dg = bpy.context.evaluated_depsgraph_get()
    me = body.evaluated_get(dg).to_mesh()
    zmin = min(v.co.z for v in me.vertices)
    body.evaluated_get(dg).to_mesh_clear()
    body.location.z -= zmin
    bpy.context.view_layer.update()
    return body


def bake_shape(obj):
    """形 (シェイプキー) を焼きこみ、ふつうのメッシュにする。"""
    if obj.data.shape_keys is None:
        return
    mix = obj.shape_key_add(name="mix", from_mix=True)
    co = np.empty(len(obj.data.vertices) * 3, dtype=np.float32)
    mix.data.foreach_get("co", co)
    obj.shape_key_clear()
    obj.data.vertices.foreach_set("co", co)
    obj.data.update()


def apply_location(obj):
    obj.data.transform(Matrix.Translation(obj.location))
    obj.location = (0, 0, 0)


def group_verts(obj, name):
    gi = obj.vertex_groups[name].index
    return [v.index for v in obj.data.vertices
            if any(g.group == gi and g.weight > 0.5 for g in v.groups)]


def split_copy(src, keep_idx, name):
    """src の頂点のうち keep_idx だけを残した複製を作る (重みも残る)。"""
    me = src.data.copy()
    ob = bpy.data.objects.new(name, me)
    bpy.context.collection.objects.link(ob)
    for g in src.vertex_groups:
        ob.vertex_groups.new(name=g.name)
    # 4.x では重みはメッシュ側にあるので、名前をそろえればよい
    keep = np.zeros(len(me.vertices), bool)
    keep[list(keep_idx)] = True
    bm = bmesh.new()
    bm.from_mesh(me)
    bm.verts.ensure_lookup_table()
    bmesh.ops.delete(bm, geom=[v for v in bm.verts if not keep[v.index]], context='VERTS')
    bm.to_mesh(me)
    bm.free()
    ob.matrix_world = src.matrix_world.copy()
    return ob


# ---------------------------------------------------------------- 材質
def mat_basic(name, color, rough=0.6, sss=0.0, sheen=0.0, attr_mix=None):
    """Principled BSDF の材質。attr_mix=[(属性名, 色), ...] で色を塗り分ける。"""
    m = bpy.data.materials.new(name)
    m.use_nodes = True
    nt = m.node_tree
    bsdf = nt.nodes["Principled BSDF"]
    bsdf.inputs["Roughness"].default_value = rough
    bsdf.inputs["Specular IOR Level"].default_value = 0.25
    if sss:
        bsdf.inputs["Subsurface Weight"].default_value = sss
        bsdf.inputs["Subsurface Radius"].default_value = (0.5, 0.25, 0.15)
        bsdf.inputs["Subsurface Scale"].default_value = 0.01
    if sheen:
        bsdf.inputs["Sheen Weight"].default_value = sheen
    col_socket = bsdf.inputs["Base Color"]
    prev = None
    rgb = nt.nodes.new("ShaderNodeRGB")
    rgb.outputs[0].default_value = color
    prev = rgb.outputs[0]
    for aname, acol in (attr_mix or []):
        at = nt.nodes.new("ShaderNodeAttribute")
        at.attribute_name = aname
        mx = nt.nodes.new("ShaderNodeMix")
        mx.data_type = 'RGBA'
        nt.links.new(at.outputs["Fac"], mx.inputs["Factor"])
        nt.links.new(prev, mx.inputs[6])
        mx.inputs[7].default_value = acol
        prev = mx.outputs[2]
    nt.links.new(prev, col_socket)
    return m


def mat_leather(name, color):
    m = mat_basic(name, color, rough=0.75)
    nt = m.node_tree
    bsdf = nt.nodes["Principled BSDF"]
    # まだらな革の色むら
    noise = nt.nodes.new("ShaderNodeTexNoise")
    noise.inputs["Scale"].default_value = 18.0
    noise.inputs["Detail"].default_value = 6.0
    ramp = nt.nodes.new("ShaderNodeValToRGB")
    ramp.color_ramp.elements[0].position = 0.35
    ramp.color_ramp.elements[0].color = tuple(c * 0.7 for c in color[:3]) + (1,)
    ramp.color_ramp.elements[1].position = 0.7
    ramp.color_ramp.elements[1].color = tuple(min(1, c * 1.15) for c in color[:3]) + (1,)
    nt.links.new(noise.outputs["Fac"], ramp.inputs["Fac"])
    nt.links.new(ramp.outputs["Color"], bsdf.inputs["Base Color"])
    bump = nt.nodes.new("ShaderNodeBump")
    bump.inputs["Strength"].default_value = 0.15
    noise2 = nt.nodes.new("ShaderNodeTexNoise")
    noise2.inputs["Scale"].default_value = 120.0
    nt.links.new(noise2.outputs["Fac"], bump.inputs["Height"])
    nt.links.new(bump.outputs["Normal"], bsdf.inputs["Normal"])
    # つやのむら (使いこんだ所は少し光る)
    rr = nt.nodes.new("ShaderNodeMapRange")
    rr.inputs["To Min"].default_value = 0.55
    rr.inputs["To Max"].default_value = 0.9
    nt.links.new(noise.outputs["Fac"], rr.inputs["Value"])
    nt.links.new(rr.outputs["Result"], bsdf.inputs["Roughness"])
    return m


def mat_hair(name, color, H):
    """髪: 中間の作風では、毛すじの模様と異方性 (毛の向きにのびるつや) をつける。"""
    m = mat_basic(name, color, rough=0.42)
    if not H.get("strand_tex"):
        return m
    nt = m.node_tree
    bsdf = nt.nodes["Principled BSDF"]
    tc = nt.nodes.new("ShaderNodeTexCoord")
    mp = nt.nodes.new("ShaderNodeMapping")
    mp.inputs["Scale"].default_value = (900.0, 900.0, 6.0)  # 縦にのびた細いすじ
    nz = nt.nodes.new("ShaderNodeTexNoise")
    nz.inputs["Scale"].default_value = 1.0
    nz.inputs["Detail"].default_value = 4.0
    nt.links.new(tc.outputs["Object"], mp.inputs["Vector"])
    nt.links.new(mp.outputs["Vector"], nz.inputs["Vector"])
    ramp = nt.nodes.new("ShaderNodeValToRGB")
    ramp.color_ramp.elements[0].position = 0.3
    ramp.color_ramp.elements[0].color = tuple(c * 0.55 for c in color[:3]) + (1,)
    ramp.color_ramp.elements[1].position = 0.75
    ramp.color_ramp.elements[1].color = tuple(min(1, c * 1.8 + 0.004) for c in color[:3]) + (1,)
    nt.links.new(nz.outputs["Fac"], ramp.inputs["Fac"])
    nt.links.new(ramp.outputs["Color"], bsdf.inputs["Base Color"])
    rr = nt.nodes.new("ShaderNodeMapRange")
    rr.inputs["To Min"].default_value = 0.42
    rr.inputs["To Max"].default_value = 0.6
    nt.links.new(nz.outputs["Fac"], rr.inputs["Value"])
    nt.links.new(rr.outputs["Result"], bsdf.inputs["Roughness"])
    bsdf.inputs["Anisotropic"].default_value = H.get("aniso", 0.7)
    tg = nt.nodes.new("ShaderNodeTangent")
    tg.direction_type = 'RADIAL'
    tg.axis = 'X'  # 頭の横軸のまわり = たれた髪では、ほぼ毛の向き
    nt.links.new(tg.outputs["Tangent"], bsdf.inputs["Tangent"])
    bsdf.inputs["Specular IOR Level"].default_value = 0.2
    bump = nt.nodes.new("ShaderNodeBump")
    bump.inputs["Strength"].default_value = 0.25
    nt.links.new(nz.outputs["Fac"], bump.inputs["Height"])
    nt.links.new(bump.outputs["Normal"], bsdf.inputs["Normal"])
    return m


def mat_eye(name, iris_png):
    m = bpy.data.materials.new(name)
    m.use_nodes = True
    nt = m.node_tree
    bsdf = nt.nodes["Principled BSDF"]
    tex = nt.nodes.new("ShaderNodeTexImage")
    tex.image = bpy.data.images.load(iris_png)
    nt.links.new(tex.outputs["Color"], bsdf.inputs["Base Color"])
    bsdf.inputs["Roughness"].default_value = 0.08
    bsdf.inputs["Coat Weight"].default_value = 0.6
    return m


def vgroup_to_attr(obj, group, attr, scale=1.0):
    """頂点グループの重みを、材質で使える色属性 (FLOAT) にする。"""
    gi = obj.vertex_groups[group].index
    a = obj.data.attributes.new(attr, 'FLOAT', 'POINT')
    vals = [0.0] * len(obj.data.vertices)
    for v in obj.data.vertices:
        for g in v.groups:
            if g.group == gi:
                vals[v.index] = g.weight
    a.data.foreach_set("value", [x * scale for x in vals])


# ---------------------------------------------------------------- 表面に沿う道具
class Surface:
    def __init__(self, obj):
        dg = bpy.context.evaluated_depsgraph_get()
        ev = obj.evaluated_get(dg)
        me = ev.to_mesh()
        mw = obj.matrix_world
        verts = [mw @ v.co for v in me.vertices]
        polys = [tuple(p.vertices) for p in me.polygons]
        self.bvh = BVHTree.FromPolygons(verts, polys)
        ev.to_mesh_clear()

    def hit(self, origin, direction, dist=2.0):
        loc, nor, idx, d = self.bvh.ray_cast(Vector(origin), Vector(direction).normalized(), dist)
        return loc, nor

    def toward(self, center, d, off):
        """center から方向 d の表面の点 (外へ off 浮かす)。"""
        d = Vector(d).normalized()
        loc, nor = self.hit(Vector(center) + d * 0.5, -d)
        if loc is None:
            return Vector(center) + d * 0.1
        return loc + d * off


def sph(az, el):
    """az: 0=前 (-Y), 90=左 (+X), 180=後ろ。el: 上向きの角度。度で。"""
    a, e = math.radians(az), math.radians(el)
    return Vector((math.sin(a) * math.cos(e), -math.cos(a) * math.cos(e), math.sin(e)))


def curve_obj(name, splines, bevel, mat, resolution=3):
    """splines: [(points[Vector], radii[float])]"""
    cu = bpy.data.curves.new(name, 'CURVE')
    cu.dimensions = '3D'
    cu.bevel_depth = bevel
    cu.bevel_resolution = resolution
    cu.use_fill_caps = True
    cu.twist_mode = 'MINIMUM'
    for pts, radii in splines:
        radii = list(radii) + [radii[-1]] * max(0, len(pts) - len(radii))
        sp = cu.splines.new('NURBS')
        sp.points.add(len(pts) - 1)
        for p, co, r in zip(sp.points, pts, radii):
            p.co = (co.x, co.y, co.z, 1.0)
            p.radius = r
        sp.order_u = 4
        sp.use_endpoint_u = True
        sp.resolution_u = 6
    ob = bpy.data.objects.new(name, cu)
    bpy.context.collection.objects.link(ob)
    ob.data.materials.append(mat)
    return ob


def to_mesh(ob):
    if os.environ.get("HUMAN_DEBUG") and ob.type == 'CURVE':
        for i, sp in enumerate(ob.data.splines):
            bad = [tuple(round(x, 3) for x in p.co) for p in sp.points if Vector(p.co[:3]).length < 0.2]
            if bad:
                print("BADSPLINE", ob.name, i, len(sp.points), bad[:3])
    bpy.ops.object.select_all(action='DESELECT')
    ob.select_set(True)
    bpy.context.view_layer.objects.active = ob
    bpy.ops.object.convert(target='MESH')
    return bpy.context.view_layer.objects.active


def join(objs, name):
    bpy.ops.object.select_all(action='DESELECT')
    for o in objs:
        o.select_set(True)
    bpy.context.view_layer.objects.active = objs[0]
    bpy.ops.object.join()
    ob = bpy.context.view_layer.objects.active
    ob.name = name
    return ob


def parent_to_bone(ob, arm, bone):
    mw = ob.matrix_world.copy()
    ob.parent = arm
    ob.parent_type = 'BONE'
    ob.parent_bone = bone
    bpy.context.view_layer.update()  # 骨の位置を反映してから、元の場所へもどす
    ob.matrix_world = mw
    bpy.context.view_layer.update()


def shade_smooth(ob):
    for p in ob.data.polygons:
        p.use_smooth = True


# ---------------------------------------------------------------- 髪
def build_hair(P, surf, head_c, head_r, mats):
    H = P["hair"]
    hair_m = mats["hair"]
    parts = []
    # (1) 頭をおおう「帽子」: 方向の格子を頭の表面へ投げる
    def hairline(az):
        a = abs(((az + 180) % 360) - 180)  # 0..180
        # 前は額の上、横は耳の上、後ろはうなじまで
        pts = [(0, H["line_front"]), (55, H["line_temple"]), (95, H["line_ear"]),
               (130, H["line_ear"] - 18), (180, H["line_nape"])]
        for (a0, e0), (a1, e1) in zip(pts, pts[1:]):
            if a <= a1:
                t = (a - a0) / (a1 - a0)
                return e0 + (e1 - e0) * (0.5 - 0.5 * math.cos(math.pi * t))
        return pts[-1][1]

    naz, nel = 72, 22
    if os.environ.get("HUMAN_DEBUG"):
        for az in (60, 90, 120, 150):
            print("CAPDBG", az, round(hairline(az), 1), [(el, tuple(round(x, 3) for x in surf.toward(head_c, sph(az, el), 0)))
                                                         for el in (0, 15, 30, 45)])
        print("HEADC", head_c)
    bm = bmesh.new()
    grid = []
    for i in range(naz):
        az = -180 + 360 * i / naz
        lo = hairline(az)
        row = []
        for j in range(nel):
            t = j / (nel - 1)
            el = lo + (88 - lo) * (t ** 0.8)
            off = H["cap_off"] + 0.004 * (1 - t)
            row.append(bm.verts.new(surf.toward(head_c, sph(az, el), off)))
        grid.append(row)
    for i in range(naz):
        a, b = grid[i], grid[(i + 1) % naz]
        for j in range(nel - 1):
            bm.faces.new((a[j], b[j], b[j + 1], a[j + 1]))
    top = bm.verts.new(surf.toward(head_c, Vector((0, 0, 1)), H["cap_off"]))
    for i in range(naz):
        bm.faces.new((grid[i][-1], grid[(i + 1) % naz][-1], top))
    bm.normal_update()
    for f in bm.faces:  # 面の向きを外向きにそろえる
        if f.normal.dot(f.calc_center_median() - head_c) < 0:
            f.normal_flip()
    me = bpy.data.meshes.new("hair_cap")
    bm.to_mesh(me)
    bm.free()
    cap = bpy.data.objects.new("hair_cap", me)
    bpy.context.collection.objects.link(cap)
    cap.data.materials.append(mat_basic("dbg", (1, 0, 0, 1)) if os.environ.get("HUMAN_DEBUG") else hair_m)
    if os.environ.get("HUMAN_DEBUG"):
        zs = [v.co.z for v in cap.data.vertices]
        print("CAPZ", len(zs), min(zs), max(zs))
    shade_smooth(cap)
    sol = cap.modifiers.new("solid", 'SOLIDIFY')
    sol.thickness = 0.004
    sol.offset = 1
    parts.append(cap)

    rng = np.random.default_rng(P["seed"])

    def strand_on_head(path, off0, off1, n=14):
        """(az, el) の列にそって頭の表面をはう点の列。"""
        pts = []
        for k in range(n):
            t = k / (n - 1)
            f = t * (len(path) - 1)
            i = min(int(f), len(path) - 2)
            u = f - i
            az = path[i][0] * (1 - u) + path[i + 1][0] * u
            el = path[i][1] * (1 - u) + path[i + 1][1] * u
            pts.append(surf.toward(head_c, sph(az, el), off0 + (off1 - off0) * t))
        return pts

    clumps = []
    w = H["clump"]
    # (2) 前髪: 頭頂から額へ、まっすぐ切りそろえる
    for az in np.arange(-H["bang_span"], H["bang_span"] + 0.1, H["bang_step"]):
        az = float(az + rng.normal(0, 1.5))
        end_el = H["bang_end"] + rng.normal(0, 1.2) + 0.03 * abs(az)
        path = [(az * 0.25, 80), (az * 0.7, 45), (az, 25), (az * 1.02, end_el)]
        pts = strand_on_head(path, 0.006, 0.012, 16)
        radii = [1.0] * 11 + [0.95, 0.9, 0.8, 0.65, 0.45]
        clumps.append((pts, radii))
    # (3) 横の髪: 耳の前を通って、あごの線まで (顔をふちどる)
    for side in (-1, 1):
        for k, az0 in enumerate(H["side_az"]):
            az = side * (az0 + rng.normal(0, 2))
            path = [(side * 40, 80), (side * (az0 - 10), 50), (az, 15), (az, -5), (az, H["side_end"])]
            pts = strand_on_head(path, 0.007, 0.016, 18)
            radii = [1.0] * 11 + [0.9, 0.8, 0.7, 0.55, 0.4, 0.28, 0.15]
            clumps.append((pts, radii))
    # (4) 後ろの髪: みな、うなじの結び目へ集まる
    tie = surf.toward(head_c, sph(180, H["tie_el"]), H["tie_off"])
    for az0 in np.arange(-170, 171, H["back_step"]):
        if abs(az0) < 95:
            continue
        az = float(az0 + rng.normal(0, 2))
        path = [(az * 0.5, 82), (az, 55), (az, 20), ((az + 180 * np.sign(az)) / 2 * 0 + np.sign(az) * 170, H["tie_el"] + 8)]
        pts = strand_on_head(path, 0.008, 0.014, 14)
        pts.append(tie + (pts[-1] - tie) * 0.3)
        pts.append(tie)
        radii = [1.0] * 12 + [0.9, 0.8, 0.7, 0.6]
        clumps.append((pts, radii))
    # (5) 低い位置で結んだ髪の束: 背中にそって下がる
    tail = []
    for k in range(H["tail_clumps"]):
        dx = (k - (H["tail_clumps"] - 1) / 2) * H["tail_width"] / max(1, H["tail_clumps"] - 1)
        pts, radii = [], []
        n = 16
        for i in range(n):
            t = i / (n - 1)
            z = tie.z - t * H["tail_len"]
            x = dx * (0.5 + 0.6 * math.sin(math.pi * min(1, t * 1.2))) * (1 - 0.5 * t) + rng.normal(0, 0.0015)
            loc, nor = surf.hit((x, 0.6, z), (0, -1, 0))
            back_y = loc.y + H["tail_gap"] if loc is not None else tie.y
            y = max(tie.y + 0.01 * t, back_y) + 0.008 * math.cos(k * 2.1)  # 束を前後にもずらす
            pts.append(Vector((x, y, z)))
            # 結び目のすぐ下でふくらみ、先は細く
            radii.append(0.65 + 0.6 * math.sin(math.pi * min(1, 0.15 + t * 0.95)) * (1 - 0.65 * t ** 2))
        tail.append((pts, radii))
    clumps += tail
    hair_c = curve_obj("hair_clumps", clumps, w, hair_m)
    # 束を少しひらたく (横 1 : 厚み 0.6)
    parts.append(hair_c)
    # (6) 結び紐
    bpy.ops.mesh.primitive_torus_add(major_radius=H["tail_width"] * 0.32 + w, minor_radius=0.0045,
                                     major_segments=24, minor_segments=8,
                                     location=tie + Vector((0, 0.006, -0.022)), rotation=(0, 0, 0))
    band = bpy.context.object
    band.name = "hair_tie"
    band.data.materials.append(mats["cord"])
    parts.append(band)
    return parts, tie


# ---------------------------------------------------------------- 服
def build_tunic(P, body, joints, mats):
    T = P["tunic"]
    co = np.array([v.co for v in body.data.vertices])
    tights = set(group_verts(body, "helper-tights"))
    skirt = set(group_verts(body, "helper-skirt"))
    sh_x = joints["joint-l-shoulder"][0]
    neck_z = joints["joint-neck"][2]
    knee_z = joints["joint-l-knee"][2]
    waist_z = joints["joint-spine-3"][2]
    keep_t = [i for i in tights
              if co[i, 2] > waist_z - 0.09 and co[i, 2] < neck_z - T["neck_drop"]
              and abs(co[i, 0]) < sh_x + T["sleeve"]]
    keep_s = [i for i in skirt if co[i, 2] > knee_z + T["hem_above_knee"]]
    top = split_copy(body, keep_t, "tunic_top")
    low = split_copy(body, keep_s, "tunic_skirt")
    for ob, push in ((top, T["push_top"]), (low, T["push_skirt"])):
        bm = bmesh.new()
        bm.from_mesh(ob.data)
        bm.normal_update()
        for v in bm.verts:
            v.co += v.normal * push
        bm.to_mesh(ob.data)
        bm.free()
    # 裾をすこし広げる
    for v in low.data.vertices:
        t = max(0.0, (waist_z - 0.05 - v.co.z) / (waist_z - knee_z))
        v.co.x *= 1 + T["flare"] * t
        v.co.y = (v.co.y - joints["joint-pelvis"][1]) * (1 + T["flare"] * 0.7 * t) + joints["joint-pelvis"][1]
    tunic = join([top, low], "tunic")
    tunic.data.materials.clear()
    tunic.data.materials.append(mats["leather"])
    for mod in list(tunic.modifiers):
        tunic.modifiers.remove(mod)
    sol = tunic.modifiers.new("solid", 'SOLIDIFY')
    sol.thickness = 0.003
    sol.offset = 1
    shade_smooth(tunic)
    return tunic


def loft_rings(surf, centers, n=64, off=0.003, clamp=9.0):
    """centers: [中心 Vector]。中から外へ光線を出して体の表面を拾い、輪を重ねた筒を作る。
    布が小さなでっぱりをまたぐよう、距離をならしてから使う。"""
    R = np.zeros((len(centers), n))
    D = [Vector((math.sin(2 * math.pi * i / n), -math.cos(2 * math.pi * i / n), 0)) for i in range(n)]
    for j, c in enumerate(centers):
        for i, d in enumerate(D):
            loc, nor = surf.hit(c, d, 0.4)
            R[j, i] = (loc - c).length if loc is not None else 0.1
    # 遠すぎる当たり (となりの脚・腰の奥) は切る
    med = np.median(R, axis=1, keepdims=True)
    R = np.minimum(R, med * clamp)
    # 角度方向: となりとの最大 -> 平均 (でっぱりをまたぐ)、たて方向: 平均
    R = np.maximum.reduce([np.roll(R, k, axis=1) for k in (-2, -1, 0, 1, 2)])
    R = np.mean([np.roll(R, k, axis=1) for k in (-2, -1, 0, 1, 2)], axis=0)
    if len(centers) > 2:
        R[1:-1] = (R[:-2] + R[1:-1] * 2 + R[2:]) / 4
    bm = bmesh.new()
    vs = [[bm.verts.new(c + D[i] * (R[j, i] + off)) for i in range(n)] for j, c in enumerate(centers)]
    for r0, r1 in zip(vs, vs[1:]):
        for i in range(n):
            bm.faces.new((r0[i], r0[(i + 1) % n], r1[(i + 1) % n], r1[i]))
    bm.normal_update()
    return bm


def copy_weights(dst, src):
    """dst の各頂点に、src のいちばん近い頂点の骨の重みを写す。"""
    from mathutils.kdtree import KDTree
    kd = KDTree(len(src.data.vertices))
    for v in src.data.vertices:
        kd.insert(v.co, v.index)
    kd.balance()
    names = [g.name for g in src.vertex_groups]
    for nme in names:
        if nme not in dst.vertex_groups:
            dst.vertex_groups.new(name=nme)
    for v in dst.data.vertices:
        _, idx, _ = kd.find(v.co)
        for g in src.data.vertices[idx].groups:
            dst.vertex_groups[names[g.group]].add([v.index], g.weight, 'REPLACE')


def build_underwear(P, body, joints, mats):
    """胸の帯と短いパンツ (無地・濃い色)。VRoid の素体の下着に合わせた、控えめな服。
    体の表面を輪切りに拾って筒にするので、ふちがまっすぐになる。"""
    skin = split_copy(body, group_verts(body, "body"), "_skin_tmp")
    for m in list(skin.modifiers):
        skin.modifiers.remove(m)
    surf = Surface(skin)
    # 胸の帯用: 腕を除いた胴だけの表面 (光線が腕に当たらないように)
    sh_x = joints["joint-l-shoulder"][0]
    trunk_idx = [v.index for v in skin.data.vertices if abs(v.co.x) < sh_x - 0.005]
    trunk = split_copy(skin, trunk_idx, "_trunk_tmp")
    tsurf = Surface(trunk)
    bpy.data.objects.remove(trunk)
    cy = joints["joint-spine-1"][1]
    chest = joints["joint-spine-1"][2]
    leg = joints["joint-l-upper-leg"][2]
    pel_y = joints["joint-pelvis"][1]
    bms = []
    # 胸の帯
    zs = np.linspace(chest - 0.105, chest - 0.005, 9)
    bms.append(loft_rings(tsurf, [Vector((0, cy + 0.01, z)) for z in zs], off=0.004))
    # パンツの腰まわり
    zs = np.linspace(leg - 0.045, leg + 0.075, 10)
    bms.append(loft_rings(surf, [Vector((0, pel_y, z)) for z in zs], clamp=1.45))
    # パンツの脚の部分 (左右)
    for side in (-1, 1):
        a = Vector(joints["joint-l-upper-leg"]) * Vector((side, 1, 1))
        k = Vector(joints["joint-l-knee"]) * Vector((side, 1, 1))
        cs = []
        for z in np.linspace(leg - 0.095, leg - 0.03, 6):
            t = (a.z - z) / (a.z - k.z)
            c = a.lerp(k, t)
            c.x += side * 0.01
            cs.append(Vector((c.x, c.y, z)))
        bms.append(loft_rings(surf, cs, n=40, clamp=1.25))
    # 股の部分: 前と後ろから表面を拾った小さな当て布
    for sgn in (-1, 1):
        bm = bmesh.new()
        xs = np.linspace(-0.045, 0.045, 9)
        zs2 = np.linspace(leg - 0.085, leg - 0.035, 6)
        grid = []
        for z in zs2:
            row = []
            for x in xs:
                loc, nor = surf.hit((x, pel_y + sgn * 0.5, z), (0, -sgn, 0), 1.0)
                if loc is None:
                    loc, nor = Vector((x, pel_y, z)), Vector((0, sgn, 0))
                row.append(loc + Vector((0, sgn, 0)) * 0.004)
            grid.append(row)
        # 横にならす
        for row in grid:
            ys = [p.y for p in row]
            for i in range(1, len(row) - 1):
                row[i].y = (ys[i - 1] + 2 * ys[i] + ys[i + 1]) / 4
        vs = [[bm.verts.new(p) for p in row] for row in grid]
        for r0, r1 in zip(vs, vs[1:]):
            for i in range(len(xs) - 1):
                bm.faces.new((r0[i], r0[i + 1], r1[i + 1], r1[i]))
        bms.append(bm)
    me = bpy.data.meshes.new("underwear")
    bm = bmesh.new()
    for b in bms:
        tmp = bpy.data.meshes.new("t")
        b.to_mesh(tmp)
        b.free()
        bm.from_mesh(tmp)
        bpy.data.meshes.remove(tmp)
    bm.to_mesh(me)
    bm.free()
    uw = bpy.data.objects.new("underwear", me)
    bpy.context.collection.objects.link(uw)
    copy_weights(uw, skin)
    bpy.data.objects.remove(skin)
    uw.data.materials.append(mats["underwear"])
    sol = uw.modifiers.new("solid", 'SOLIDIFY')
    sol.thickness = 0.0025
    sol.offset = 1
    shade_smooth(uw)
    return uw


def build_belt(P, tunic_surf, joints, mats):
    z = joints["joint-spine-3"][2] - 0.035
    cy = joints["joint-pelvis"][1]
    pts = []
    n = 48
    for i in range(n):
        a = 2 * math.pi * i / n
        d = Vector((math.sin(a), -math.cos(a), 0))
        loc, nor = tunic_surf.hit(Vector((0, cy, z)) + d * 0.5, -d)
        p = (loc if loc is not None else Vector((0, cy, z)) + d * 0.15) + d * 0.004
        pts.append(p)
    cu = bpy.data.curves.new("belt", 'CURVE')
    cu.dimensions = '3D'
    cu.bevel_depth = 0.0045
    cu.bevel_resolution = 3
    sp = cu.splines.new('NURBS')
    sp.points.add(len(pts) - 1)
    for p, co in zip(sp.points, pts):
        p.co = (*co, 1)
    sp.use_cyclic_u = True
    sp.order_u = 4
    belt = bpy.data.objects.new("belt", cu)
    bpy.context.collection.objects.link(belt)
    belt.data.materials.append(mats["cord"])
    # 結び目とたれた紐 (左前)
    k = pts[int(n * 0.06)]
    knot_ends = []
    for s, ln in ((-1, 0.17), (1, 0.13)):
        q = [k + Vector((0.0, -0.006, 0)),
             k + Vector((s * 0.012, -0.012, -0.03)),
             k + Vector((s * 0.018, -0.014, -ln * 0.6)),
             k + Vector((s * 0.02, -0.013, -ln))]
        knot_ends.append((q, [1, 1, 0.9, 0.8]))
    ends = curve_obj("belt_ends", knot_ends, 0.004, mats["cord"])
    bpy.ops.mesh.primitive_uv_sphere_add(radius=0.011, location=k + Vector((0, -0.004, 0)),
                                         segments=12, ring_count=8)
    knot = bpy.context.object
    knot.scale = (1.2, 0.8, 1.0)
    knot.data.materials.append(mats["cord"])
    return [belt, ends, knot]


# ---------------------------------------------------------------- 顔の小物
def build_brows(P, surf, joints, mats):
    out = []
    eye_z = joints["joint-l-eye"][2]
    for side in (-1, 1):
        ex = joints["joint-l-eye"][0] * side
        pts, radii = [], []
        for t in np.linspace(0, 1, 7):
            x = ex + side * (-0.017 + 0.036 * t)
            z = eye_z + P["face"]["brow_h"] + 0.006 * math.sin(math.pi * min(1, t * 1.15)) - 0.004 * t
            loc, nor = surf.hit((x, -0.5, z), (0, 1, 0))
            pts.append(loc + nor * 0.0012)
            radii.append(1.0 - 0.55 * t if t > 0.3 else 0.7 + t)
        out.append(curve_obj("brow", [(pts, radii)], 0.0016, mats["brow"], resolution=1))
    return out


def build_scar(P, surf, arm_obj, mats):
    """左の前腕の外側に、ななめの古い傷。"""
    eb = arm_obj.data.bones["lowerarm01.L"]
    mw = arm_obj.matrix_world
    a, b = mw @ eb.head_local, mw @ arm_obj.data.bones["lowerarm02.L"].tail_local
    axis = (b - a).normalized()
    out_dir = axis.cross(Vector((0, 1, 0))).normalized()  # 腕の上側
    if out_dir.z < 0:
        out_dir = -out_dir
    side = axis.cross(out_dir).normalized()
    c = a + (b - a) * 0.3
    pts = []
    for t in np.linspace(-1, 1, 7):
        q = c + axis * (0.022 * t) + side * (0.011 * t)
        loc, nor = surf.hit(q + out_dir * 0.2, -out_dir)
        pts.append(loc + nor * 0.0006)
    radii = [0.4, 0.8, 1, 1, 1, 0.8, 0.4]
    return curve_obj("scar", [(pts, radii)], 0.0018, mats["scar"], resolution=1)


# ---------------------------------------------------------------- 外の頭 (差しかえ口)
def replace_head(path, body, arm, joints, hide=(), cut_above=0.025):
    """頭と顔を、外の 3D 素材 (.glb/.gltf/.obj/.fbx) に差しかえる。

    いまの顔はまだ「こわい」と言われているので、よい頭の素材が見つかったら、
    `--head-asset <file>` で差しこめるようにしておく口。
    - 体の首より上 (首の関節 + cut_above より上) をマスクで隠す
    - 素材を 1 つにまとめ、隠した頭と同じ高さ・位置に合わせて拡大縮小する
    - head の骨につなぐ (姿勢を変えても頭が付いてくる)
    hide: 一緒に隠す物 (元の目・まつ毛・眉など)
    素材の向きは「前が -Y、上が +Z」を前提にする (glTF の読みこみはこの向きになる)。
    """
    before = set(bpy.data.objects)
    ext = os.path.splitext(path)[1].lower()
    if ext in (".glb", ".gltf"):
        bpy.ops.import_scene.gltf(filepath=path)
    elif ext == ".obj":
        bpy.ops.wm.obj_import(filepath=path)
    elif ext == ".fbx":
        bpy.ops.import_scene.fbx(filepath=path)
    else:
        raise ValueError("head asset: unknown format " + ext)
    new = [o for o in bpy.data.objects if o not in before]
    for o in new:
        if o.type != 'MESH':
            bpy.data.objects.remove(o)
    meshes = [o for o in bpy.data.objects if o not in before and o.type == 'MESH']
    for o in meshes:  # 親を外して、見た目の位置のまま固定
        mw = o.matrix_world.copy()
        o.parent = None
        o.matrix_world = mw
        o.data.transform(o.matrix_world)
        o.matrix_world = Matrix()
    head = join(meshes, "head_asset") if len(meshes) > 1 else meshes[0]
    head.name = "head_asset"
    # 隠す頭の範囲
    cut_z = joints["joint-neck"][2] + cut_above
    gi = body.vertex_groups.new(name="_head_cut")
    idx = [v.index for v in body.data.vertices if v.co.z > cut_z]
    gi.add(idx, 1.0, 'REPLACE')
    mk = body.modifiers.new("hide_head", 'MASK')
    mk.vertex_group = "_head_cut"
    mk.invert_vertex_group = True
    co = np.array([body.data.vertices[i].co for i in idx])
    lo, hi = co.min(0), co.max(0)
    hc = np.array([v.co for v in head.data.vertices])
    hlo, hhi = hc.min(0), hc.max(0)
    k = (hi[2] - lo[2]) / max(1e-6, hhi[2] - hlo[2])
    off = Vector(((lo[0] + hi[0]) / 2, (lo[1] + hi[1]) / 2, lo[2])) - \
        Vector(((hlo[0] + hhi[0]) / 2, (hlo[1] + hhi[1]) / 2, hlo[2])) * k
    head.data.transform(Matrix.Translation(off) @ Matrix.Scale(k, 4))
    parent_to_bone(head, arm, "head")
    for o in hide:
        if o is not None:
            o.hide_render = True
            o.hide_viewport = True
    print(f"head asset: {path} scale {k:.3f}", flush=True)
    return head


# ---------------------------------------------------------------- 姿勢
def set_pose(arm, pose):
    for pb in arm.pose.bones:
        pb.rotation_mode = 'XYZ'
        pb.rotation_euler = (0, 0, 0)
        pb.location = (0, 0, 0)
    arm.location.z = 0
    for bone, rot in pose.get("rot", {}).items():
        if bone in arm.pose.bones:
            arm.pose.bones[bone].rotation_euler = tuple(math.radians(r) for r in rot)
    bpy.context.view_layer.update()


def ground(arm, objs):
    """一番低い点が地面に来るよう、全体を上下させる。"""
    dg = bpy.context.evaluated_depsgraph_get()
    zmin = 9
    for o in objs:
        ev = o.evaluated_get(dg)
        me = ev.to_mesh()
        mw = o.matrix_world
        for v in me.vertices:
            zmin = min(zmin, (mw @ v.co).z)
        ev.to_mesh_clear()
    arm.location.z -= zmin
    bpy.context.view_layer.update()


# ---------------------------------------------------------------- 撮影
def setup_render(quick, ST):
    s = bpy.context.scene
    s.render.engine = 'CYCLES'
    s.cycles.device = 'CPU'
    s.cycles.samples = 24 if quick else ST["samples"]
    s.cycles.use_denoising = True
    s.cycles.max_bounces = 6
    s.render.film_transparent = False
    s.view_settings.view_transform = 'Standard'
    s.view_settings.look = 'None'
    s.view_settings.exposure = ST.get("exposure", 0.0)
    s.render.use_freestyle = ST["freestyle"]
    s.render.line_thickness_mode = 'ABSOLUTE'
    s.render.line_thickness = 1.0
    vl = s.view_layers[0]
    ls = vl.freestyle_settings.linesets[0] if vl.freestyle_settings.linesets else vl.freestyle_settings.linesets.new("lines")
    ls.select_by_visibility = True
    ls.select_silhouette = True
    ls.select_border = True
    ls.select_crease = False
    ls.linestyle.color = (0.12, 0.07, 0.05)
    ls.linestyle.thickness = 1.2
    w = bpy.data.worlds.new("w")
    s.world = w
    w.use_nodes = True
    w.node_tree.nodes["Background"].inputs[0].default_value = srgb("#aeb3bb")
    w.node_tree.nodes["Background"].inputs[1].default_value = 0.55
    # 光: 正面上の主光・反対の補助光・後ろの縁取り光
    def area(name, loc, energy, size, color=(1, 1, 1)):
        ld = bpy.data.lights.new(name, 'AREA')
        ld.energy = energy
        ld.size = size
        ld.color = color
        ob = bpy.data.objects.new(name, ld)
        s.collection.objects.link(ob)
        ob.location = loc
        d = Vector((0, 0, 1.0)) - Vector(loc)
        ob.rotation_euler = d.to_track_quat('-Z', 'Y').to_euler()
        return ob
    area("key", (1.6, -2.4, 2.6), 420, 2.0, (1.0, 0.96, 0.9))
    area("fill", (-2.2, -1.8, 1.4), 160, 3.0, (0.9, 0.95, 1.0))
    area("rim", (0.5, 2.6, 2.4), 260, 1.5)
    # 地面 (影を受ける。色は背景に近く)
    bpy.ops.mesh.primitive_plane_add(size=8, location=(0, 0, 0))
    fl = bpy.context.object
    fl.name = "floor"
    fl.data.materials.append(mat_basic("floor", srgb("#a3a8b0"), rough=0.9))
    fl.is_shadow_catcher = False
    return s


def camera(name, loc, target, ortho=None, lens=85):
    cd = bpy.data.cameras.new(name)
    if ortho:
        cd.type = 'ORTHO'
        cd.ortho_scale = ortho
    else:
        cd.lens = lens
    ob = bpy.data.objects.new(name, cd)
    bpy.context.scene.collection.objects.link(ob)
    ob.location = loc
    d = Vector(target) - Vector(loc)
    ob.rotation_euler = d.to_track_quat('-Z', 'Y').to_euler()
    return ob


def render(cam, path, rx, ry):
    s = bpy.context.scene
    s.camera = cam
    s.render.resolution_x, s.render.resolution_y = rx, ry
    s.render.resolution_percentage = 100
    s.render.filepath = path
    t = time.time()
    bpy.ops.render.render(write_still=True)
    dt = time.time() - t
    print(f"render {os.path.basename(path)} {rx}x{ry}: {dt:.1f}s", flush=True)
    return dt


def compose(paths, out, labels=None, bg=(174, 179, 187)):
    from PIL import Image, ImageDraw
    ims = [Image.open(p).convert("RGB") for p in paths]
    W = sum(i.width for i in ims)
    Hh = max(i.height for i in ims)
    sheet = Image.new("RGB", (W, Hh), bg)
    x = 0
    for im in ims:
        sheet.paste(im, (x, 0))
        x += im.width
    sheet.save(out)
    for p in paths:
        os.remove(p)


# ---------------------------------------------------------------- 本体
def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--person", default="sena")
    ap.add_argument("--quick", action="store_true")
    ap.add_argument("--style", default="mid", choices=sorted(STYLES))
    ap.add_argument("--head-asset", default="", help="頭と顔を差しかえる外の素材 (.glb/.obj/.fbx)")
    ap.add_argument("--keep-hair", action="store_true", help="頭を差しかえても、作った髪を残す")
    ap.add_argument("--only", default="", help="sheet,face,poses をカンマで")
    args = ap.parse_args(sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else sys.argv[1:])
    P = copy.deepcopy(PEOPLE[args.person])
    ST = STYLES[args.style]
    P["targets"].update(ST["targets"])
    P["hair"].update(ST["hair"])
    P["skin"].update(ST["skin"])
    if "outfit" in ST:
        P["outfit"] = ST["outfit"]
    t0 = time.time()
    for ob in list(bpy.data.objects):
        bpy.data.objects.remove(ob)
    HS, TS = setup_mpfb()

    body = make_body(P, HS, TS)
    bake_shape(body)
    apply_location(body)
    # 関節の位置 (MakeHuman の joint 立方体の中心)
    co = np.array([v.co for v in body.data.vertices])
    joints = {}
    for g in body.vertex_groups:
        if g.name.startswith("joint-"):
            idx = group_verts(body, g.name)
            if idx:
                joints[g.name] = co[idx].mean(0)

    vgroup_to_attr(body, "lips", "lips_w", P["skin"].get("lip_mix", 1.0))

    # 骨組み (MakeHuman の default リグ、重みつき)
    arm = HS.add_builtin_rig(body, "default", import_weights=True)
    arm.name = P["name"] + "_rig"

    # 目 (MakeHuman の high-poly eyes, CC0)
    eyes = HS.add_mhclo_asset(os.path.join(ASSETS, "mh_eyes", "high-poly", "high-poly.mhclo"),
                              body, asset_type="Eyes", subdiv_levels=1, material_type="MAKESKIN")
    eyes.name = "eyes"
    eyes.data.materials.clear()
    eyes.data.materials.append(mat_eye("eye", os.path.join(ASSETS, "mh_eyes", "materials", "brown_eye.png")))

    # 色
    S = P["skin"]
    mats = {
        "skin": mat_basic("skin", srgb(S["color"]), rough=S.get("rough", 0.55), sss=S.get("sss", 0.08),
                          attr_mix=[("lips_w", srgb(S["lips"]))]),
        "hair": mat_hair("hair", srgb(P["hair"]["color"]), P["hair"]),
        "leather": mat_leather("leather", srgb(P["tunic"]["color"])),
        "cord": mat_basic("cord", srgb(P["tunic"]["cord"]), rough=0.8),
        "brow": mat_basic("brow", srgb(P["hair"]["color"]), rough=0.7),
        "scar": mat_basic("scar", srgb(S["scar"]), rough=0.5),
        "lash": mat_basic("lash", srgb("#1a1210"), rough=0.7),
        "underwear": mat_basic("underwear", srgb("#141414"), rough=0.6),
    }
    # まつ毛: 基本メッシュの補助形状をそのまま使う
    lash_idx = []
    for g in ("helper-l-eyelashes-2", "helper-r-eyelashes-2"):  # 上まつ毛だけ
        if g in body.vertex_groups:
            if os.environ.get("HUMAN_DEBUG"):
                print("LASH", g, co[group_verts(body, g)].mean(0).round(4))
            lash_idx += group_verts(body, g)
    lashes = split_copy(body, lash_idx, "lashes") if lash_idx else None
    if lashes:
        for m in list(lashes.modifiers):
            if m.type != 'ARMATURE':
                lashes.modifiers.remove(m)
        lashes.data.materials.clear()
        lashes.data.materials.append(mats["lash"])

    outfit = P.get("outfit", "tunic")
    if outfit == "tunic":
        tunic = build_tunic(P, body, joints, mats)
    else:
        tunic = build_underwear(P, body, joints, mats)
    # 体から補助形状を消し、肌だけにする
    body_idx = group_verts(body, "body")
    keep = np.zeros(len(body.data.vertices), bool)
    keep[body_idx] = True
    bm = bmesh.new()
    bm.from_mesh(body.data)
    bm.verts.ensure_lookup_table()
    bmesh.ops.delete(bm, geom=[v for v in bm.verts if not keep[v.index]], context='VERTS')
    bm.to_mesh(body.data)
    bm.free()
    for m in list(body.modifiers):
        if m.type == 'MASK':
            body.modifiers.remove(m)
    body.data.materials.clear()
    body.data.materials.append(mats["skin"])
    shade_smooth(body)

    surf = Surface(body)
    head_pts = co[group_verts(body, "body")] if False else None
    hz = joints["joint-head"][2]
    top_z = joints["joint-head-2"][2]
    head_c = Vector((0, joints["joint-head"][1] + 0.015, hz + 0.045))  # 頭蓋の中心あたり
    hair_parts, tie = build_hair(P, surf, head_c, (top_z - hz) / 2, mats)
    brows = build_brows(P, surf, joints, mats)
    scar = build_scar(P, surf, arm, mats)
    belt_parts = build_belt(P, Surface(tunic), joints, mats) if outfit == "tunic" else []

    # 曲線をメッシュにし、骨につなぐ
    hair = join([to_mesh(o) for o in hair_parts], "hair")
    shade_smooth(hair)
    parent_to_bone(hair, arm, "head")
    for b in brows:
        parent_to_bone(to_mesh(b), arm, "head")
    parent_to_bone(to_mesh(scar), arm, "lowerarm01.L")
    belt = None
    if belt_parts:
        belt = join([to_mesh(o) for o in belt_parts], "belt")
        shade_smooth(belt)
        parent_to_bone(belt, arm, "spine05")

    # 服は体の重みをそのまま持っているので、骨にそって動く
    tunic.parent = arm
    am = tunic.modifiers.new("arm", 'ARMATURE')
    am.object = arm
    tunic.modifiers.move(len(tunic.modifiers) - 1, 0)
    if lashes:
        lashes.parent = arm
        if not any(m.type == 'ARMATURE' for m in lashes.modifiers):
            m = lashes.modifiers.new("arm", 'ARMATURE')
            m.object = arm
    if args.head_asset:
        hide = [eyes, lashes] + [o for o in bpy.data.objects if o.name.startswith("brow")]
        if not args.keep_hair:
            hide.append(hair)
        replace_head(args.head_asset, body, arm, joints, hide=hide)
    for ob in (body, tunic, eyes):
        sd = ob.modifiers.new("subd", 'SUBSURF')
        sd.levels = 0
        sd.render_levels = 1
    print(f"build: {time.time() - t0:.1f}s", flush=True)
    if os.environ.get("HUMAN_DEBUG"):
        dg = bpy.context.evaluated_depsgraph_get()
        for o in bpy.data.objects:
            if o.type == 'MESH':
                ev = o.evaluated_get(dg)
                me = ev.to_mesh()
                c = np.array([o.matrix_world @ v.co for v in me.vertices]) if len(me.vertices) else np.zeros((1, 3))
                if o.name == "hair":
                    import collections
                    print("HAIRMAT", [m.name for m in o.data.materials], collections.Counter(p.material_index for p in o.data.polygons))
                low = c[c[:, 2] < 0.6]
                if len(low) and o.name == "hair":
                    print("LOW", len(low), low[:5].round(3))
                print("OBJ", o.name, len(me.vertices), c.min(0).round(3), c.max(0).round(3), [m.type for m in o.modifiers])
                ev.to_mesh_clear()

    # 書き出し (.glb): 立ち姿の休み姿勢
    os.makedirs(OUT_GLB, exist_ok=True)
    glb = os.path.join(OUT_GLB, P["name"] + ("_" + args.style if args.style != "real" else "") + ".glb")
    bpy.ops.export_scene.gltf(filepath=glb, export_format='GLB', export_apply=False,
                              export_yup=True, export_skins=True, export_morph=False)
    print("glb", glb, os.path.getsize(glb) // 1024, "KB", flush=True)

    # 撮影
    os.makedirs(OUT_PNG, exist_ok=True)
    setup_render(args.quick, ST)
    figure = [o for o in (body, tunic, hair, belt, eyes, lashes) if o]
    set_pose(arm, P["poses"]["stand"])
    ground(arm, [body])
    only = set(args.only.split(",")) if args.only else {"sheet", "face", "poses"}
    times = {}
    name = P["name"] + "_" + ST["prefix"].rstrip("_") if ST["prefix"] else P["name"]
    hgt = joints["joint-head-2"][2]
    cz = hgt / 2
    if "sheet" in only:
        tmp = []
        for k, (loc) in enumerate([(0, -10, cz), (10, 0, cz), (0, 10, cz)]):
            cam = camera("c%d" % k, loc, (0, 0, cz), ortho=hgt * 1.12)
            p = os.path.join(OUT_PNG, f"_tmp_{k}.png")
            times[f"sheet{k}"] = render(cam, p, 560, 1100)
            tmp.append(p)
        compose(tmp, os.path.join(OUT_PNG, f"{name}_3view.png"))
    if "face" in only:
        fz = joints["joint-l-eye"][2] - 0.01
        cam = camera("face", (0.12, -0.95, fz + 0.03), (0, 0, fz), lens=105)
        times["face"] = render(cam, os.path.join(OUT_PNG, f"{name}_face.png"), 900, 900)
    if "sideface" in only:
        fz = joints["joint-l-eye"][2]
        cam = camera("sf", (0.9, 0.3, fz + 0.05), (0, 0, fz), lens=100)
        if os.environ.get("HUMAN_DEBUG") == "2":
            for o in bpy.data.objects:
                if o.type == 'MESH' and o.name not in ("hair",):
                    o.hide_render = True
        times["sideface"] = render(cam, os.path.join(OUT_PNG, f"_debug_side.png"), 600, 600)
    if "poses" in only:
        tmp = []
        for k, pose in enumerate(["stand", "gather"]):
            set_pose(arm, P["poses"][pose])
            ground(arm, [body])
            cam = camera("p%d" % k, (2.6, -4.6, 1.0), (0, 0, 0.72 if k == 0 else 0.5), lens=60)
            p = os.path.join(OUT_PNG, f"_tmp_p{k}.png")
            times[f"pose{k}"] = render(cam, p, 700, 1000)
            tmp.append(p)
        compose(tmp, os.path.join(OUT_PNG, f"{name}_poses.png"))
    print("TIMES", {k: round(v, 1) for k, v in times.items()}, "total", round(time.time() - t0, 1), flush=True)


if __name__ == "__main__":
    main()
    sys.stdout.flush()
    os._exit(0)
