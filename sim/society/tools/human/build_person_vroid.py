"""川辺の五人を VRoid の CC0 サンプルから作る (中間の作風: 線はアニメ、面は写実の光)。

使いかた (README.md の「VRoid の素体から作る道」):
    BLENDER_USER_RESOURCES=/dev/shm/sena/userres PYTHONPATH=/dev/shm/bpy \
        python3.11 -u run.py build_person_vroid.py -- --person ruo [--quick] [--only sheet,face,expr,lineup] > log 2>&1

- 人ごとの数値は people.py の VROID[<名前>]。どのサンプルの顔・髪・体を使うかもそこに書く。
- 体と骨組み: VRoid サンプル「HairSample_Female」(女) / 「HairSample_Male」(男) (CC0)。
  服の下まで肌がある素体の体を使う。骨の名前はどれも同じ (J_Bip_*)。
- 顔・髪: 人ごとに別の CC0 サンプルから (千駄ヶ谷 篠、桜田 フミリヤ、Victoria Rubin など)。
- 高さの数値は「女の素体 (HairSample_Female) の高さ」で書き、Frame.z() で
  その人の体 (腰・首・頭の骨の高さ) に写す。セナはそのまま (写しても同じ)。
- 出力: PNG を sim/society/out/human/、.glb を /dev/shm/sena/<名前>_vroid.glb に書く。
"""
import argparse
import json
import math
import os
import shutil
import struct
import sys
import time

import bpy
import bmesh
import numpy as np
from mathutils import Vector
from mathutils.bvhtree import BVHTree

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
from people import VROID  # noqa: E402
from build_sena import srgb, camera, render, compose, OUT_PNG, OUT_GLB  # noqa: E402

VRM_DIR = os.environ.get("VROID_DIR", "/dev/shm/heads/src/vrmsamples/vroid/beta")
WORK = os.environ.get("VROID_WORK", "/dev/shm/sena/vroid")


def lin(h):
    return srgb(h)[:3]


def smooth(x, a, b):
    t = np.clip((x - a) / (b - a), 0.0, 1.0)
    return t * t * (3 - 2 * t)


# 女の素体 (HairSample_Female) の骨の高さ。people.py の高さの数値はこの体の上で書いてある
REF = {"hips": 0.944, "neck": 1.35, "head": 1.422, "arm": 0.108}


class Frame:
    """いまの骨組みの目じるし (腰・首・頭の高さ、肩の横の位置)。"""

    def __init__(self, rig):
        b = rig.data.bones
        self.hips = b["J_Bip_C_Hips"].head_local.z
        self.neck = b["J_Bip_C_Neck"].head_local.z
        self.head = b["J_Bip_C_Head"].head_local.z
        self.arm = abs(b["J_Bip_L_UpperArm"].head_local.x)
        self.hb = np.array(b["J_Bip_C_Head"].head_local)
        self.w = self.arm / REF["arm"]

    def z(self, z):
        """女の素体の高さ z を、この体の高さへ (腰・首・頭のあいだは直線、頭より上はずらすだけ)。"""
        xs = [0.0, REF["hips"], REF["neck"], REF["head"], REF["head"] + 1.0]
        ys = [0.0, self.hips, self.neck, self.head, self.head + 1.0]
        return np.interp(z, xs, ys)


def mesh_co(ob):
    me = ob.data
    co = np.empty(len(me.vertices) * 3, np.float32)
    if me.shape_keys:
        me.shape_keys.key_blocks[0].data.foreach_get("co", co)
    else:
        me.vertices.foreach_get("co", co)
    return co.reshape(-1, 3).astype(np.float64)


def map_mesh(ob, fn):
    """メッシュの全頂点 (表情キーもすべて) を fn((N,3)) で動かす。"""
    me = ob.data
    n = len(me.vertices)
    if n == 0:
        return
    blocks = me.shape_keys.key_blocks if me.shape_keys else [None]
    for kb in blocks:
        co = np.empty(n * 3, np.float32)
        (kb.data if kb else me.vertices).foreach_get("co", co)
        q = fn(co.reshape(-1, 3).astype(np.float64))
        (kb.data if kb else me.vertices).foreach_set("co", q.astype(np.float32).ravel())
    if blocks[0] is not None:
        me.vertices.foreach_set("co", mesh_co(ob).astype(np.float32).ravel())
    me.update()


def map_bones(rig, fn, skip=()):
    bpy.context.view_layer.objects.active = rig
    bpy.ops.object.mode_set(mode='EDIT')
    for eb in rig.data.edit_bones:
        if any(k in eb.name for k in skip):
            continue
        for attr in ("head", "tail"):
            v = np.array(getattr(eb, attr))[None]
            setattr(eb, attr, Vector(fn(v)[0]))
    bpy.ops.object.mode_set(mode='OBJECT')


# ---------------------------------------------------------------- 読みこみ
def vrm_json(path):
    with open(path, "rb") as f:
        head = f.read(20)
        n = struct.unpack("<I", head[12:16])[0]
        return json.loads(f.read(n))


def import_vrm(fname, prefix):
    """.vrm を .glb として読み、オブジェクト名に prefix をつける。"""
    src = os.path.join(VRM_DIR, fname)
    os.makedirs(WORK, exist_ok=True)
    glb = os.path.join(WORK, prefix + "src.glb")
    shutil.copy(src, glb)
    before = set(bpy.data.objects)
    bpy.ops.import_scene.gltf(filepath=glb)
    objs = {}
    for o in set(bpy.data.objects) - before:
        nm = o.name.split(".")[0]
        o.name = prefix + nm
        objs[nm] = o
    js = vrm_json(src)
    meta = js["extensions"]["VRM"]["meta"]
    print("VRM", fname, "title", meta.get("title"), "license", meta.get("licenseName"), flush=True)
    return objs, js


def delete_faces(ob, keep):
    """keep(material_name) が偽の面を消す。"""
    names = [m.name if m else "" for m in ob.data.materials]
    bm = bmesh.new()
    bm.from_mesh(ob.data)
    bmesh.ops.delete(bm, geom=[f for f in bm.faces if not keep(names[f.material_index])], context='FACES')
    bmesh.ops.delete(bm, geom=[v for v in bm.verts if not v.link_faces], context='VERTS')
    bm.to_mesh(ob.data)
    bm.free()
    # 使わなくなった材質のスロットを消す
    used = {p.material_index for p in ob.data.polygons}
    for i in reversed(range(len(ob.data.materials))):
        if i not in used:
            ob.data.materials.pop(index=i)


def retarget(ob, rig, delta, rigid=False):
    """別の骨組みへつなぎかえる。骨組みにない頂点グループは頭の骨へまとめる。"""
    mw = ob.matrix_world.copy()
    ob.parent = rig
    ob.matrix_world = mw
    for m in ob.modifiers:
        if m.type == 'ARMATURE':
            m.object = rig
    me = ob.data
    if me.shape_keys:
        for kb in me.shape_keys.key_blocks:
            co = np.empty(len(me.vertices) * 3, np.float32)
            kb.data.foreach_get("co", co)
            kb.data.foreach_set("co", (co.reshape(-1, 3) + delta).ravel())
    else:
        co = np.empty(len(me.vertices) * 3, np.float32)
        me.vertices.foreach_get("co", co)
        me.vertices.foreach_set("co", (co.reshape(-1, 3) + delta).ravel())
    me.update()
    bones = set(rig.data.bones.keys())
    head = ob.vertex_groups.get("J_Bip_C_Head") or ob.vertex_groups.new(name="J_Bip_C_Head")
    moved = [g for g in ob.vertex_groups if g.name != "J_Bip_C_Head" and (rigid or g.name not in bones)]
    if moved:
        gi = {g.index: g for g in moved}
        for v in me.vertices:
            w = sum(e.weight for e in v.groups if e.group in gi)
            if w > 0:
                head.add([v.index], w, 'ADD')
        for g in moved:
            ob.vertex_groups.remove(g)


def drop_parts(ob, rule, hb):
    """髪のばらばらの束 (つながった部分) のうち、rule に合うものを消す。
    rule: {"x_lt": m, "x_gt": m, "z_gt": m} (頭の骨からの位置、束の重心で判定)。"""
    bm = bmesh.new()
    bm.from_mesh(ob.data)
    bm.verts.ensure_lookup_table()
    seen, dele = set(), []
    for v in bm.verts:
        if v.index in seen:
            continue
        st, comp = [v], []
        seen.add(v.index)
        while st:
            u = st.pop()
            comp.append(u)
            for e in u.link_edges:
                w = e.other_vert(u)
                if w.index not in seen:
                    seen.add(w.index)
                    st.append(w)
        c = np.mean([u.co[:] for u in comp], axis=0) - hb
        hit = all([("x_lt" not in rule or c[0] < rule["x_lt"]), ("x_gt" not in rule or c[0] > rule["x_gt"]),
                   ("z_gt" not in rule or c[2] > rule["z_gt"])])
        if hit:
            dele += comp
    bmesh.ops.delete(bm, geom=dele, context='VERTS')
    bm.to_mesh(ob.data)
    bm.free()
    print("drop_parts", ob.name, len(dele), "verts", "head", hb.round(3), flush=True)


def assemble(P):
    """体と骨組み (body_src)、顔 (face_src)、髪の部品 (hair の parts) を、それぞれのサンプルから集める。"""
    srcs = {}

    def get(fname):
        if fname not in srcs:
            srcs[fname] = import_vrm(fname, "s%d_" % len(srcs))
        return srcs[fname]

    bobjs, _ = get(P["body_src"])
    rig = bobjs["Armature"]
    rig.name = P["name"] + "_rig"
    rhead = np.array(rig.data.bones["J_Bip_C_Head"].head_local)

    def delta_of(objs):
        return rhead - np.array(objs["Armature"].data.bones["J_Bip_C_Head"].head_local)

    def dup(o, name):
        c = o.copy()
        c.data = o.data.copy()
        bpy.context.scene.collection.objects.link(c)
        c.name = name
        return c

    keep = {rig}
    # 髪の部品: Hair001 (前・横・後ろの髪) と、体のメッシュにのっている HairBack (地肌に近い後ろ髪)
    hairs = []
    for k, part in enumerate(P["hair"]["parts"]):
        objs, _ = get(part["src"])
        d = delta_of(objs)
        if part["part"] == "Hair001":
            ob = dup(objs["Hair001"], "hair%d" % k)
        else:
            ob = dup(objs["Body"], "hair%d" % k)
            delete_faces(ob, lambda n: "HairBack" in n)
        if part.get("drop"):
            delete_faces(ob, lambda n, dr=part["drop"]: not any(x in n for x in dr))
        if len(ob.data.vertices) == 0:
            bpy.data.objects.remove(ob)
            continue
        hb = np.array(objs["Armature"].data.bones["J_Bip_C_Head"].head_local)
        for rule in part.get("drop_parts", []):
            drop_parts(ob, rule, hb)
        retarget(ob, rig, d, rigid=True)
        print("hair part", part["src"], part["part"], len(ob.data.vertices), "verts, delta", d.round(4), flush=True)
        hairs.append(ob)
        keep.add(ob)

    fobjs, js = get(P["face_src"])
    face = dup(fobjs["Face"], "face")
    # 表情キーに VRoid の名前をつける (target_N -> Fcl_...)
    m0 = js["meshes"][[m["name"] for m in js["meshes"]].index("Face.baked")] \
        if any(m["name"] == "Face.baked" for m in js["meshes"]) else js["meshes"][0]
    names = m0["extras"]["targetNames"] if "extras" in m0 else m0["primitives"][0]["extras"]["targetNames"]
    for i, n in enumerate(names):
        kb = face.data.shape_keys.key_blocks.get("target_%d" % i)
        if kb:
            kb.name = n.split(".M_F00_000_00_")[-1].split(".M_")[-1]
    retarget(face, rig, delta_of(fobjs))
    keep.add(face)

    body = dup(bobjs["Body"], "body")
    delete_faces(body, lambda n: "SKIN" in n)          # 服と靴を消す
    keep.add(body)

    # いらないものを消す (読みこんだもののうち使わないもの)
    for objs, _ in srcs.values():
        for o in objs.values():
            if o not in keep and o.name in bpy.data.objects:
                bpy.data.objects.remove(o)
    for ob in [body, face] + hairs:
        for p in ob.data.polygons:
            p.use_smooth = True
    return rig, body, face, hairs


# ---------------------------------------------------------------- 体つき
def limb_field(ob, rig, limbs):
    """腕・脚を骨の軸から外へ太らせる量 (頂点ごと、重みで混ぜる)。"""
    me = ob.data
    n = len(me.vertices)
    co = np.empty(n * 3, np.float32)
    me.vertices.foreach_get("co", co)
    co = co.reshape(-1, 3)
    disp = np.zeros_like(co)
    gname = {g.index: g.name for g in ob.vertex_groups}
    W = {}
    for v in me.vertices:
        for e in v.groups:
            W.setdefault(gname[e.group], []).append((v.index, e.weight))
    for bname, b in rig.data.bones.items():
        k = next((s for key, s in limbs.items() if bname.endswith("_" + key)), None)
        if k is None or bname not in W:
            continue
        idx = np.array([i for i, _ in W[bname]])
        w = np.array([x for _, x in W[bname]])
        h, t = np.array(b.head_local), np.array(b.tail_local)
        ax = t - h
        L = ax @ ax
        p = co[idx]
        s = np.clip(((p - h) @ ax) / L, 0, 1)
        c = h + s[:, None] * ax
        disp[idx] += (w * k)[:, None] * (p - c)
    return disp


def body_field(p, B, F):
    """体つきを変える変形 (休みの姿勢の座標で)。p: (N,3)。値が負なら細く。
    高さは女の素体で書き、F.z() でこの体へ写す。"""
    x, y, z = p[:, 0], p[:, 1], p[:, 2]
    q = p.copy()
    ax = np.abs(x)
    sg = np.sign(x)
    Z = F.z
    # 肩幅: 首から外の上半身と腕を横へずらす
    band = smooth(z, Z(1.10), Z(1.25)) * (1 - smooth(z, Z(1.355), Z(1.395)))
    q[:, 0] += sg * B["shoulder"] * smooth(ax, 0.035 * F.w, 0.12 * F.w) * band
    # 腰: 骨盤のあたりを横に広げる
    hip = smooth(z, Z(0.80), Z(0.90)) * (1 - smooth(z, Z(0.97), Z(1.07))) * (ax < 0.25)
    q[:, 0] *= 1 + B["hips"] * hip
    # 胴まわり: くびれを弱く (負なら細く)
    wst = np.exp(-((z - Z(1.04)) / (0.07 * (Z(1.35) - Z(0.944)) / 0.406)) ** 2) * (ax < 0.2)
    q[:, 0] *= 1 + B["waist"] * wst
    q[:, 1] = y + (y - 0.01) * 0.5 * B["waist"] * wst
    # 胸まわり (男の胸板など)
    if B.get("chest"):
        ch = np.exp(-((z - Z(1.22)) / 0.08) ** 2) * (ax < 0.17)
        q[:, 1] = q[:, 1] + (y - 0.01) * B["chest"] * ch
    return q


def sturdy(rig, body, others, B, F):
    me = body.data
    co = mesh_co(body)
    co = co + limb_field(body, rig, B["limbs"])
    me.vertices.foreach_set("co", body_field(co, B, F).astype(np.float32).ravel())
    me.update()
    # 髪など、体の近くのもの (顔より下だけ変わる)
    for ob in others:
        map_mesh(ob, lambda c: body_field(c, B, F))
    # 骨も同じだけ動かす (腕の骨が腕の中に残るように)
    map_bones(rig, lambda v: body_field(v, B, F), skip=("Leg", "Foot", "Toe"))


def proportions(rig, objs, P, F):
    """背の高さ (scale)、脚の長さ (legs)、腕の長さ (arms) を、すべてのメッシュと骨に同じ写像で。"""
    s, kl, ka = P.get("scale", 1.0), P.get("legs", 1.0), P.get("arms", 1.0)
    if s == 1.0 and kl == 1.0 and ka == 1.0:
        return
    hz, xs = F.hips, F.arm + 0.02

    def fn(p):
        q = p.copy()
        z = q[:, 2]
        q[:, 2] = np.where(z < hz, z * kl, z + hz * (kl - 1))
        ax = np.abs(q[:, 0])
        q[:, 0] = np.where(ax > xs, np.sign(q[:, 0]) * (xs + (ax - xs) * ka), q[:, 0])
        return q * s
    for ob in objs:
        map_mesh(ob, fn)
    map_bones(rig, fn)
    print("proportions scale", s, "legs", kl, "arms", ka, flush=True)


def round_face(face, R, F):
    """ほおとあごを少し横に広げて丸顔に (負ならこけた頬)。首とのつなぎ目と目のまわりは動かさない。"""
    if not R:
        return
    me = face.data
    bm = bmesh.new()
    bm.from_mesh(me)
    bnd = np.array([v.co[:] for v in bm.verts if v.is_boundary])
    bm.free()
    base = mesh_co(face)
    # 境目 (首) からの距離
    from mathutils.kdtree import KDTree
    kd = KDTree(len(bnd))
    for i, b in enumerate(bnd):
        kd.insert(b, i)
    kd.balance()
    dist = np.array([kd.find(Vector(p))[2] for p in base])
    z = base[:, 2]
    Z = F.z
    w = smooth(dist, 0.006, 0.025) * smooth(z, Z(1.385), Z(1.415)) * (1 - smooth(z, Z(1.445), Z(1.462)))
    w *= smooth(np.abs(base[:, 0]), 0.0, 0.03)

    def fn(co):
        co[:, 0] *= 1 + R * w
        return co
    map_mesh(face, fn)


def thick_brows(face, k):
    """眉 (FaceBrow の面) を縦に k 倍 (太く)。左右それぞれの中心から。"""
    if not k or k == 1.0:
        return
    me = face.data
    mi = [i for i, m in enumerate(me.materials) if "FaceBrow" in m.name]
    idx = sorted({v for p in me.polygons if p.material_index in mi for v in p.vertices})
    if not idx:
        return
    idx = np.array(idx)
    base = mesh_co(face)[idx]
    cz = {s: base[np.sign(base[:, 0]) == s, 2].mean() for s in (-1, 1)}

    def fn(co):
        p = co[idx]
        c = np.where(p[:, 0] < 0, cz[-1], cz[1])
        p[:, 2] = c + (p[:, 2] - c) * k
        co[idx] = p
        return co
    map_mesh(face, fn)


# ---------------------------------------------------------------- 髪を低い位置で結ぶ
def tie_hair(hairs, body, rig, H, F):
    """後ろの髪を、うなじで 1 本にまとめて背中に沿わせる (形を寄せるだけ)。
    前で顔の横に下がる束は残し、肩の高さまで短くする。結び紐の輪も作る。"""
    hb = F.hb
    zt, zs, tw = F.z(H["tie_z"]), F.z(H["gather_from"]), H["tail_width"]
    # 背中の線 (体の真ん中付近で一番うしろの y、1 cm ごと)
    bc = np.array([v.co[:] for v in body.data.vertices])
    bc = bc[np.abs(bc[:, 0]) < 0.06]
    zb = np.arange(F.z(0.9), F.z(1.7), 0.01)
    back_y = np.array([bc[np.abs(bc[:, 2] - z) < 0.008, 1].min() if np.any(np.abs(bc[:, 2] - z) < 0.008)
                       else np.nan for z in zb])
    ok = ~np.isnan(back_y)
    back_of = lambda z: np.interp(z, zb[ok], back_y[ok])  # noqa: E731
    pts = []
    for ob in hairs:
        me = ob.data
        co = np.empty(len(me.vertices) * 3, np.float32)
        me.vertices.foreach_get("co", co)
        pts.append(co.reshape(-1, 3).astype(np.float64))
    allp = np.vstack(pts)
    behind_all = allp[:, 1] < hb[1] + 0.01
    # 高さごとの、後ろ髪のいちばん内側 (体に近い) の y
    inner = np.array([allp[behind_all & (np.abs(allp[:, 2] - z) < 0.01), 1].max()
                      if np.any(behind_all & (np.abs(allp[:, 2] - z) < 0.01)) else np.nan for z in zb])
    ok2 = ~np.isnan(inner)
    inner_of = lambda z: np.interp(z, zb[ok2], inner[ok2])  # noqa: E731
    xmax = np.abs(allp[behind_all & (allp[:, 2] < zt), 0]).max()
    ring = []
    for ob, p in zip(hairs, pts):
        x, y, z = p[:, 0], p[:, 1], p[:, 2]
        behind = 1 - smooth(y, hb[1] - 0.005, hb[1] + 0.03)
        f = 1 - smooth(z, zt, zs)
        hw = tw * (1 + 0.7 * np.clip((zt - z) / 0.25, 0, 1))
        xt = x * hw / xmax
        bk = back_of(z)
        yt = bk - 0.016 + (y - inner_of(z)) * 0.3
        k = f * behind
        nx = x + (xt - x) * k
        ny = y + (yt - y) * k
        ny = np.where((behind > 0.5) & (z < zs), np.minimum(ny, bk - 0.012 - 0.012 * smooth(zt - z, 0.0, 0.06)), ny)
        # 前の束: 肩の高さまで短く
        zc = F.z(H["front_from"])
        front = 1 - behind
        nz = np.where(z < zc, z + ((zc - (zc - z) * H["front_keep"]) - z) * front, z)
        q = np.stack([nx, ny, nz], 1)
        ob.data.vertices.foreach_set("co", q.astype(np.float32).ravel())
        ob.data.update()
        sel = (behind > 0.9) & (np.abs(z - zt) < 0.012)
        ring.append(q[sel])
    ring = np.vstack(ring)
    c = np.array([0.0, (ring[:, 1].min() + ring[:, 1].max()) / 2, zt])
    ax = np.abs(ring[:, 0]).max() + 0.004
    ay = (ring[:, 1].max() - ring[:, 1].min()) / 2 + 0.004
    print("tie", c.round(3), "half", round(ax, 3), round(ay, 3), flush=True)
    # 結び紐 (楕円の輪の管)
    bm = bmesh.new()
    nu, nv, r = 32, 8, 0.0045
    vs = []
    for i in range(nu):
        t = 2 * math.pi * i / nu
        cen = Vector((c[0] + ax * math.cos(t), c[1] + ay * math.sin(t), c[2]))
        out = Vector((math.cos(t) / ax, math.sin(t) / ay, 0)).normalized()
        for j in range(nv):
            u = 2 * math.pi * j / nv
            vs.append(bm.verts.new(cen + out * (r * math.cos(u)) + Vector((0, 0, r * 1.6 * math.sin(u)))))
    for i in range(nu):
        for j in range(nv):
            a = i * nv + j
            b = ((i + 1) % nu) * nv + j
            bm.faces.new((vs[a], vs[b], vs[b - j + (j + 1) % nv], vs[a - j + (j + 1) % nv]))
    me = bpy.data.meshes.new("hair_tie")
    bm.to_mesh(me)
    bm.free()
    ob = bpy.data.objects.new("hair_tie", me)
    bpy.context.scene.collection.objects.link(ob)
    for pl in me.polygons:
        pl.use_smooth = True
    m = bpy.data.materials.new("hair_tie")
    m.use_nodes = True
    m.node_tree.nodes["Principled BSDF"].inputs["Base Color"].default_value = srgb(H["tie_color"])
    m.node_tree.nodes["Principled BSDF"].inputs["Roughness"].default_value = 0.8
    me.materials.append(m)
    g = ob.vertex_groups.new(name="J_Bip_C_Head")
    g.add(list(range(len(me.vertices))), 1.0, 'REPLACE')
    ob.parent = rig
    am = ob.modifiers.new("arm", 'ARMATURE')
    am.object = rig
    return {"tie": ob, "c": c, "ax": ax, "ay": ay, "back_of": back_of}


# ---------------------------------------------------------------- 髪を短く刈る・編む
def crop_hair(hairs, face, body, F, C):
    """髪を頭の表面へ寄せて短くする。表面からのはなれを k 倍、
    z_front / z_back (頭の骨からの高さ) より下にたれる毛先は、そこからの長さを k_len 倍。
    頭の表面 = 顔の肌 (前) + 体のメッシュの首より上 (後頭部は体のメッシュにある)。"""
    verts, polys = [], []
    for ob, key in ((face, "Face_00_SKIN"), (body, "Body_00_SKIN")):
        me = ob.data
        base = mesh_co(ob)
        mi = [i for i, m in enumerate(me.materials) if key in m.name]
        off = len(verts)
        verts += [Vector(v) for v in base]
        for p in me.polygons:
            if p.material_index in mi and (ob is face or base[list(p.vertices), 2].min() > F.neck):
                polys.append([off + i for i in p.vertices])
    tree = BVHTree.FromPolygons(verts, polys)
    hb = F.hb
    for ob in hairs:
        p = mesh_co(ob)
        out = np.empty_like(p)
        front = smooth(p[:, 1], hb[1] + 0.0, hb[1] + 0.05)
        zc = hb[2] + C["z_back"] + (C["z_front"] - C["z_back"]) * front
        for i, v in enumerate(p):
            q = v.copy()
            if q[2] < zc[i]:
                q[2] = zc[i] - (zc[i] - q[2]) * C["k_len"]
            loc, nrm, _, _ = tree.find_nearest(Vector(q))
            loc = np.array(loc)
            off = q - loc
            q = loc + off * C["k"]
            loc, nrm, _, _ = tree.find_nearest(Vector(q))
            loc, nrm = np.array(loc), np.array(nrm)
            d = (q - loc) @ nrm
            if d < C["gap"]:
                q = q + nrm * (C["gap"] - d)
            out[i] = q
        map_mesh(ob, lambda c, o=out: o)
    print("crop_hair", C, flush=True)


def tube(bm, pts, radii, nv=8, flat=1.0):
    """点の列 pts にそって、半径 radii の管を bm に足す。"""
    pts = [Vector(p) for p in pts]
    rings = []
    ref = Vector((0, 1, 0))
    for i, p in enumerate(pts):
        t = (pts[min(i + 1, len(pts) - 1)] - pts[max(i - 1, 0)]).normalized()
        u = t.cross(ref).normalized()
        w = t.cross(u).normalized()
        ring = []
        for j in range(nv):
            a = 2 * math.pi * j / nv
            ring.append(bm.verts.new(p + (u * math.cos(a) + w * math.sin(a) * flat) * radii[i]))
        rings.append(ring)
    for i in range(len(rings) - 1):
        for j in range(nv):
            a, b = rings[i][j], rings[i][(j + 1) % nv]
            c, d = rings[i + 1][(j + 1) % nv], rings[i + 1][j]
            bm.faces.new((a, b, c, d))
    bm.faces.new(rings[-1][::-1])
    return rings


def braid(rig, tie, H, F):
    """結んだところから下へ、三つ編みの束を作る (3 本の管が 8 の字にからむ)。"""
    B = H["braid"]
    c, back_of = tie["c"], tie["back_of"]
    L, A, r0 = B["len"], B["width"] / 2, B["strand_r"]
    period = B["period"]
    n = int(L / 0.003)
    bm = bmesh.new()
    z0 = c[2] - 0.006
    for k in range(3):
        ph = 2 * math.pi * k / 3
        pts, rad = [], []
        for i in range(n + 1):
            t = i / n
            z = z0 - L * t
            taper = 1 - B["taper"] * t
            th = 2 * math.pi * (L * t) / period + ph
            x = A * taper * math.sin(th)
            yb = back_of(z) - r0 * 1.6 - 0.004
            y = yb - 0.5 * A * taper * math.sin(2 * th)
            pts.append((x, y, z))
            rad.append(r0 * taper * (1 - 0.6 * smooth(np.array(t), 0.97, 1.0)))
        tube(bm, pts, rad, nv=10, flat=0.8)
    # 毛先の房 (細い円すい) と、下の結び紐
    zb = z0 - L
    yb = back_of(zb) - r0 * 1.6 - 0.004
    for k in range(7):
        a = 2 * math.pi * k / 7
        dx, dy = math.cos(a) * A * 0.5 * (1 - B["taper"]), math.sin(a) * A * 0.3
        tip = (dx * 2.2, yb + dy * 1.5, zb - B["tuft"])
        pts = [(dx, yb + dy, zb + 0.01), (dx * 1.6, yb + dy * 1.3, zb - B["tuft"] * 0.5), tip]
        tube(bm, pts, [r0 * 0.7, r0 * 0.45, 0.0005], nv=6)
    me = bpy.data.meshes.new("braid")
    bm.to_mesh(me)
    bm.free()
    ob = bpy.data.objects.new("braid", me)
    bpy.context.scene.collection.objects.link(ob)
    for pl in me.polygons:
        pl.use_smooth = True
    m = bpy.data.materials.new("braid_HAIR")
    m.use_nodes = True
    nt = m.node_tree
    pb = nt.nodes["Principled BSDF"]
    # 毛すじ: 縦にのばしたノイズで明るさのむら
    tc = nt.nodes.new("ShaderNodeTexCoord")
    mp = nt.nodes.new("ShaderNodeMapping")
    mp.inputs["Scale"].default_value = (90, 90, 8)
    nz = nt.nodes.new("ShaderNodeTexNoise")
    nz.inputs["Scale"].default_value = 6
    nz.inputs["Detail"].default_value = 4
    ramp = nt.nodes.new("ShaderNodeValToRGB")
    ramp.color_ramp.elements[0].color = srgb(H["dark"])
    ramp.color_ramp.elements[0].position = 0.3
    ramp.color_ramp.elements[1].color = srgb(H["light"])
    ramp.color_ramp.elements[1].position = 0.75
    nt.links.new(tc.outputs["Object"], mp.inputs["Vector"])
    nt.links.new(mp.outputs[0], nz.inputs["Vector"])
    nt.links.new(nz.outputs["Fac"], ramp.inputs[0])
    nt.links.new(ramp.outputs[0], pb.inputs["Base Color"])
    pb.inputs["Roughness"].default_value = H["rough"]
    pb.inputs["Specular IOR Level"].default_value = 0.2
    me.materials.append(m)
    bone = "J_Bip_C_UpperChest" if "J_Bip_C_UpperChest" in rig.data.bones else "J_Bip_C_Chest"
    g = ob.vertex_groups.new(name=bone)
    g.add(list(range(len(me.vertices))), 1.0, 'REPLACE')
    ob.parent = rig
    am = ob.modifiers.new("arm", 'ARMATURE')
    am.object = rig
    # 下の結び紐
    ring = bmesh.new()
    nu, nv, rr = 24, 6, 0.003
    vs = []
    for i in range(nu):
        t = 2 * math.pi * i / nu
        cen = Vector((A * 0.75 * math.cos(t), yb + A * 0.55 * math.sin(t), zb + 0.004))
        out = Vector((math.cos(t), math.sin(t), 0))
        for j in range(nv):
            u = 2 * math.pi * j / nv
            vs.append(ring.verts.new(cen + out * (rr * math.cos(u)) + Vector((0, 0, rr * 1.4 * math.sin(u)))))
    for i in range(nu):
        for j in range(nv):
            a = i * nv + j
            b = ((i + 1) % nu) * nv + j
            ring.faces.new((vs[a], vs[b], vs[b - j + (j + 1) % nv], vs[a - j + (j + 1) % nv]))
    tme = bpy.data.meshes.new("braid_tie")
    ring.to_mesh(tme)
    ring.free()
    tob = bpy.data.objects.new("braid_tie", tme)
    bpy.context.scene.collection.objects.link(tob)
    tme.materials.append(tie["tie"].data.materials[0])
    g = tob.vertex_groups.new(name=bone)
    g.add(list(range(len(tme.vertices))), 1.0, 'REPLACE')
    tob.parent = rig
    am = tob.modifiers.new("arm", 'ARMATURE')
    am.object = rig
    print("braid", len(me.vertices), "verts, len", L, flush=True)
    return ob


# ---------------------------------------------------------------- テクスチャに描く
def img_array(img):
    a = np.empty(img.size[0] * img.size[1] * 4, np.float32)
    img.pixels.foreach_get(a)
    return a.reshape(img.size[1], img.size[0], 4)


def to_lin(c):
    return np.where(c <= 0.04045, c / 12.92, ((c + 0.055) / 1.055) ** 2.4)


def to_srgb(c):
    c = np.clip(c, 0, 1)
    return np.where(c <= 0.0031308, c * 12.92, 1.055 * c ** (1 / 2.4) - 0.055)


class UVPainter:
    """3D の点を、材質 mat の面の UV へ写して、テクスチャに色をのせる。"""

    def __init__(self, ob, mat_name):
        self.bm = bmesh.new()
        self.bm.from_mesh(ob.data)
        names = [m.name for m in ob.data.materials]
        bmesh.ops.delete(self.bm, geom=[f for f in self.bm.faces if mat_name not in names[f.material_index]],
                         context='FACES')
        bmesh.ops.triangulate(self.bm, faces=self.bm.faces[:])
        self.bm.faces.ensure_lookup_table()
        self.uv = self.bm.loops.layers.uv.active
        self.tree = BVHTree.FromBMesh(self.bm)

    def uv_of(self, p):
        loc, nrm, i, d = self.tree.find_nearest(Vector(p))
        if loc is None:
            return None
        f = self.bm.faces[i]
        a, b, c = [l.vert.co for l in f.loops]
        from mathutils.geometry import barycentric_transform
        uvs = [l[self.uv].uv for l in f.loops]
        r = barycentric_transform(loc, a, b, c, Vector((*uvs[0], 0)), Vector((*uvs[1], 0)), Vector((*uvs[2], 0)))
        return r.x, r.y

    def paint(self, arr, pts, color, alphas, radius_px):
        """pts の各点に、やわらかい丸を色 color (線形) で塗る。最大値で重ねる。"""
        H, W = arr.shape[:2]
        mask = np.zeros((H, W), np.float32)
        r = int(math.ceil(radius_px * 2))
        yy, xx = np.mgrid[-r:r + 1, -r:r + 1]
        for p, a in zip(pts, alphas):
            uv = self.uv_of(p)
            if uv is None:
                continue
            cx, cy = uv[0] * W, uv[1] * H
            ix, iy = int(cx), int(cy)
            dd = np.sqrt((xx + ix - cx) ** 2 + (yy + iy - cy) ** 2)
            k = a * np.exp(-(dd / radius_px) ** 2)
            y0, y1, x0, x1 = iy - r, iy + r + 1, ix - r, ix + r + 1
            if y0 < 0 or x0 < 0 or y1 > H or x1 > W:
                continue
            mask[y0:y1, x0:x1] = np.maximum(mask[y0:y1, x0:x1], k)
        m = mask[..., None]
        rgb = to_lin(arr[..., :3])
        rgb = rgb * (1 - m) + np.array(color)[None, None] * m
        arr[..., :3] = to_srgb(rgb)
        return mask


def tex_of(mat):
    for n in mat.node_tree.nodes:
        if n.type == 'TEX_IMAGE' and n.image:
            return n.image
    return None


def tan_image(img, target, fill_dark=0.0):
    """テクスチャの肌の中央値が target (線形) になるように掛け算する。
    fill_dark > 0 なら、それより暗いところ (素体に描かれた下着や靴下) を肌の色でうめる。"""
    a = img_array(img)
    rgb = to_lin(a[..., :3])
    sel = (a[..., 3] > 0.5) & (rgb.sum(-1) > 0.3)
    med = np.median(rgb[sel], axis=0)
    if fill_dark:
        # 肌の中央値に比べて暗いところ (明るさの比が fill_dark より下) をうめる
        r = rgb.sum(-1) / med.sum()
        k = (1 - smooth(r, fill_dark * 0.6, fill_dark))[..., None]
        rgb = rgb * (1 - k) + med[None, None] * k
        print("fill_dark", img.name, "pixels", int((k[..., 0] > 0.5).sum()), flush=True)
    ratio = np.array(target) / med
    print("tan", img.name, "median sRGB", to_srgb(med).round(3), "ratio", ratio.round(3), flush=True)
    a[..., :3] = to_srgb(rgb * ratio)
    return a


def save_image(img, a, name):
    os.makedirs(os.path.join(WORK, "tex"), exist_ok=True)
    out = bpy.data.images.new(name, img.size[0], img.size[1], alpha=True)
    out.pixels.foreach_set(a.ravel())
    out.filepath_raw = os.path.join(WORK, "tex", name + ".png")
    out.file_format = 'PNG'
    out.save()
    return out


def bone_line(rig, D):
    """傷などの線: 骨 D["bone"] の上の s0..s1 の区間に沿って点を並べ、off だけずらす。"""
    bn = rig.data.bones[D["bone"]]
    h, t = np.array(bn.head_local), np.array(bn.tail_local)
    n = D.get("n", 70)
    pts, al = [], []
    for k in range(n):
        u = k / (n - 1)
        s = D["s"][0] + (D["s"][1] - D["s"][0]) * u
        c = h + (t - h) * s + np.array(D.get("slant", (0, 0, 0))) * (u - 0.5) + np.array(D["off"])
        pts.append(c)
        al.append(D["alpha"] * (1 - abs(u - 0.5) * 1.4))
    return pts, al


def bone_patch(rig, D, rng):
    """煤などのしみ: 骨のまわり (s0..s1、半径 spread) に散らした点。"""
    bn = rig.data.bones[D["bone"]]
    h, t = np.array(bn.head_local), np.array(bn.tail_local)
    pts, al = [], []
    for _ in range(D.get("n", 120)):
        s = rng.uniform(*D["s"])
        c = h + (t - h) * s + rng.normal(0, D["spread"], 3) + np.array(D.get("off", (0, 0, 0)))
        pts.append(c)
        al.append(D["alpha"] * rng.uniform(0.4, 1.0))
    return pts, al


def skin_textures(P, body, face, rig, F):
    S = P["skin"]
    tan = lin(S["tan"])
    fm = next(m for m in face.data.materials if "Face_00_SKIN" in m.name)
    bmat = next(m for m in body.data.materials if "Body_00_SKIN" in m.name)
    fimg, bimg = tex_of(fm), tex_of(bmat)
    fa = tan_image(fimg, lin(S.get("tan_face", S["tan"])))
    ba = tan_image(bimg, tan, S.get("fill_dark", 0.0))
    rng = np.random.default_rng(P.get("seed", 29))
    # ほお・鼻先の赤み (顔のテクスチャ)
    if S.get("blush_alpha", 0) > 0:
        pf = UVPainter(face, "Face_00_SKIN")
        base = mesh_co(face)
        hb = F.hb
        pts, al = [], []
        for sx in (-1, 1):
            c = np.array([sx * 0.034, hb[1] + 0.085, F.z(1.447)])
            for _ in range(260):
                d = rng.normal(0, 0.009, 3)
                d[1] = 0
                q = c + d
                pts.append(q + np.array([0, 0.03, 0]))
                al.append(S["blush_alpha"] * math.exp(-(np.linalg.norm(d) / 0.012) ** 2))
        # 鼻先
        nose = base[np.argmax(base[:, 1] * (np.abs(base[:, 0]) < 0.004) *
                              (base[:, 2] < F.z(1.46)) * (base[:, 2] > F.z(1.43)))]
        for _ in range(40):
            d = rng.normal(0, 0.003, 3)
            pts.append(nose + d)
            al.append(S["blush_alpha"] * 0.6 * math.exp(-(np.linalg.norm(d) / 0.004) ** 2))
        # 最も近い表面点へ (前から当てる)
        pf.paint(fa, pts, lin(S["blush"]), al, 7.0)
    # 顔のしわ (年寄り): 頭の骨からの (x, z) の線を、前から光線を当てて顔の表面に描く
    if S.get("face_lines"):
        pf = UVPainter(face, "Face_00_SKIN")
        hb = F.hb
        for D in S["face_lines"]:
            pts, al = [], []
            for sx in ((-1, 1) if D.get("mirror", True) else (1,)):
                (x0, z0), (x1, z1) = D["a"], D["b"]
                n = D.get("n", 40)
                for k in range(n):
                    u = k / (n - 1)
                    x = sx * (x0 + (x1 - x0) * u)
                    z = hb[2] + z0 + (z1 - z0) * u + D.get("bow", 0.0) * math.sin(math.pi * u)
                    hit = pf.tree.ray_cast(Vector((x, hb[1] + 0.4, z)), Vector((0, -1, 0)))
                    if hit[0] is None:
                        continue
                    pts.append(np.array(hit[0]))
                    al.append(D["alpha"] * (1 - abs(u - 0.5) * D.get("fade", 1.2)))
            pf.paint(fa, pts, lin(D["color"]), al, D.get("width", 1.6))
    # 体: 古い傷 (線) と、煤など (しみ)
    pb = UVPainter(body, "Body_00_SKIN")
    for D in S.get("scars", []):
        pts, al = bone_line(rig, D)
        pb.paint(ba, pts, lin(D["color"]), al, D.get("width", 2.2))
    for D in S.get("patches", []):
        pts, al = bone_patch(rig, D, rng)
        pb.paint(ba, pts, lin(D["color"]), al, D.get("radius", 6.0))
    nm = P["name"]
    fimg2 = save_image(fimg, fa, nm + "_face_skin")
    bimg2 = save_image(bimg, ba, nm + "_body_skin")
    return {fm.name: fimg2, bmat.name: bimg2}


# ---------------------------------------------------------------- 材質
def principled_from(m, base_socket_fn, **kw):
    """読みこんだ VRoid 材質 (光の影響なし) の Emission を Principled BSDF におきかえる。
    透明の切り抜き (アルファ) の仕組みはそのまま残す。"""
    nt = m.node_tree
    em = next(n for n in nt.nodes if n.type == 'EMISSION')
    pb = nt.nodes.new("ShaderNodeBsdfPrincipled")
    base_socket_fn(nt, em.inputs["Color"], pb.inputs["Base Color"])
    for k, v in kw.items():
        pb.inputs[k].default_value = v
    for l in list(em.outputs[0].links):
        nt.links.new(pb.outputs[0], l.to_socket)
    # Light Path の切りかえ (カメラだけ見える等) を外す: 本当の光で描くため
    for mx in [n for n in nt.nodes if n.type == 'MIX_SHADER']:
        fac = mx.inputs[0]
        if fac.is_linked and fac.links[0].from_node.type == 'LIGHT_PATH':
            nt.links.remove(fac.links[0])
            fac.default_value = 1.0 if mx.inputs[2].is_linked and mx.inputs[2].links[0].from_node == pb else 0.0
    return pb


def link_same(nt, src_in, dst_in):
    if src_in.is_linked:
        nt.links.new(src_in.links[0].from_socket, dst_in)
    else:
        dst_in.default_value = src_in.default_value


def set_factor(m, color):
    for n in m.node_tree.nodes:
        if n.type == 'MIX' and n.label == 'Color Factor' or n.name == 'Color Factor':
            for s in n.inputs:
                if s.type == 'RGBA' and not s.is_linked:
                    s.default_value = (*color, 1)


def materials(P, objs, skin_imgs):
    S, Hh, Ls = P["skin"], P["hair"], P["lines"]
    seen = set()
    for ob in objs:
        for m in ob.data.materials:
            if not m or m.name in seen:
                continue
            seen.add(m.name)
            nm = m.name
            if nm in skin_imgs:
                for n in m.node_tree.nodes:
                    if n.type == 'TEX_IMAGE':
                        n.image = skin_imgs[nm]
                principled_from(m, link_same, **{
                    "Roughness": S["rough"], "Subsurface Weight": S["sss"],
                    "Subsurface Radius": (1.0, 0.38, 0.22), "Subsurface Scale": 0.012,
                    "Specular IOR Level": 0.38})
            elif "HAIR" in nm and "braid" not in nm:
                lo, hi = Hh.get("ramp_lo", 0.35), Hh.get("ramp_hi", 1.0)
                for key, rr in Hh.get("ramp_mat", {}).items():
                    if key in nm:
                        lo, hi = rr

                def hair_col(nt, src, dst, lo=lo, hi=hi):
                    tex = next(n for n in nt.nodes if n.type == 'TEX_IMAGE')
                    bw = nt.nodes.new("ShaderNodeRGBToBW")
                    nt.links.new(tex.outputs["Color"], bw.inputs[0])
                    ramp = nt.nodes.new("ShaderNodeValToRGB")
                    ramp.color_ramp.elements[0].color = srgb(Hh["dark"])
                    ramp.color_ramp.elements[0].position = lo
                    ramp.color_ramp.elements[1].position = hi
                    ramp.color_ramp.elements[1].color = srgb(Hh["light"])
                    nt.links.new(bw.outputs[0], ramp.inputs[0])
                    nt.links.new(ramp.outputs[0], dst)
                principled_from(m, hair_col, **{"Roughness": Hh["rough"], "Specular IOR Level": 0.2})
            elif "EyeIris" in nm:
                def iris_col(nt, src, dst):
                    hsv = nt.nodes.new("ShaderNodeHueSaturation")
                    link_same(nt, src, hsv.inputs["Color"])
                    hsv.inputs["Hue"].default_value = 0.5 + P["iris"]["hue"]
                    hsv.inputs["Saturation"].default_value = P["iris"]["sat"]
                    hsv.inputs["Value"].default_value = P["iris"]["val"]
                    mul = nt.nodes.new("ShaderNodeMix")
                    mul.data_type = 'RGBA'
                    mul.blend_type = 'MULTIPLY'
                    mul.inputs[0].default_value = 1.0
                    nt.links.new(hsv.outputs[0], mul.inputs[6])
                    mul.inputs[7].default_value = srgb(P["iris"]["tint"])
                    nt.links.new(mul.outputs[2], dst)
                    return hsv
                pb = principled_from(m, iris_col, **{"Roughness": 0.5, "Specular IOR Level": 0.0, "Coat Weight": 0.3,
                                                     "Coat Roughness": 0.02, "Emission Strength": 0.6})
                m.node_tree.links.new(pb.inputs["Base Color"].links[0].from_socket, pb.inputs["Emission Color"])
            elif "EyeWhite" in nm:
                def white_col(nt, src, dst):
                    mx = nt.nodes.new("ShaderNodeMix")
                    mx.data_type = 'RGBA'
                    mx.blend_type = 'MULTIPLY'
                    mx.inputs[0].default_value = 1.0
                    link_same(nt, src, mx.inputs[6])
                    mx.inputs[7].default_value = srgb("#e8dcd8")
                    nt.links.new(mx.outputs[2], dst)
                pb = principled_from(m, white_col, **{"Roughness": 0.4, "Coat Weight": 0.3,
                                                      "Coat Roughness": 0.05, "Emission Strength": 0.15})
                m.node_tree.links.new(pb.inputs["Base Color"].links[0].from_socket, pb.inputs["Emission Color"])
            elif "FaceMouth" in nm:
                principled_from(m, link_same, **{"Roughness": 0.45, "Specular IOR Level": 0.4})
            elif "FaceBrow" in nm:
                set_factor(m, lin(Ls["brow"]))
            elif "FaceEyeline" in nm:
                set_factor(m, lin(Ls["eyeline"]))
            elif "FaceEyelash" in nm:
                set_factor(m, lin(Ls["lash"]))
            elif "EyeHighlight" in nm:
                # 絵としてのハイライト。光の影響なしのまま (tip 2)。篠のものは大きいので弱める
                for n in m.node_tree.nodes:
                    if n.type == 'EMISSION':
                        n.inputs["Strength"].default_value = P["iris"]["highlight"]
    # 表情用の特別な目 (星など) は使わない
    for ob in objs:
        if ob.name == "face":
            names = [m.name for m in ob.data.materials]
            if any("EyeExtra" in n for n in names):
                delete_faces(ob, lambda n: "EyeExtra" not in n)


# ---------------------------------------------------------------- 服 (無地の胸の帯と短パン)
def make_band(body, z0, z1, name, mat, push, bridge=False, xcut=0.165):
    bm = bmesh.new()
    bm.from_mesh(body.data)
    for z, keep_above in ((z0, True), (z1, False)):
        geom = bm.verts[:] + bm.edges[:] + bm.faces[:]
        r = bmesh.ops.bisect_plane(bm, geom=geom, plane_co=(0, 0, z), plane_no=(0, 0, 1))
        dele = [v for v in bm.verts if (v.co.z < z - 1e-5 if keep_above else v.co.z > z + 1e-5)]
        bmesh.ops.delete(bm, geom=dele, context='VERTS')
    # 腕を除く (胴の幅より外)
    dele = [f for f in bm.faces if abs(f.calc_center_median().x) > xcut]
    bmesh.ops.delete(bm, geom=dele, context='FACES')
    bmesh.ops.delete(bm, geom=[v for v in bm.verts if not v.link_faces], context='VERTS')
    bm.normal_update()
    for v in bm.verts:
        v.co += v.normal * push
    if bridge:
        # 胸のあいだのくぼみを、ふくらみの頂点どうしでまっすぐにつなぐ
        for v in bm.verts:
            if v.co.y < 0.0:
                continue
            ring = [u for u in bm.verts if abs(u.co.z - v.co.z) < 0.004 and u.co.y > 0]
            pk = max(ring, key=lambda u: u.co.y)
            if abs(v.co.x) < abs(pk.co.x):
                v.co.y = max(v.co.y, pk.co.y)
    ob_me = bpy.data.meshes.new(name)
    bm.to_mesh(ob_me)
    bm.free()
    ob = bpy.data.objects.new(name, ob_me)
    bpy.context.scene.collection.objects.link(ob)
    ob.matrix_world = body.matrix_world
    ob.data.materials.clear()
    ob.data.materials.append(mat)
    for p in ob.data.polygons:
        p.use_smooth = True
    sol = ob.modifiers.new("thick", 'SOLIDIFY')
    sol.thickness = 0.002
    sol.offset = 1.0
    # 骨の重み (体からそのまま写る: 頂点グループは bmesh で引きつがれる)
    for g in body.vertex_groups:
        if g.name not in ob.vertex_groups:
            ob.vertex_groups.new(name=g.name)
    return ob


def leather_mat(name, color, rough=0.62, seed=0.0):
    """なめした革 (ヤギの皮): 色むら・しわの凹凸・つやのむら。"""
    m = bpy.data.materials.new(name)
    m.use_nodes = True
    nt = m.node_tree
    b = nt.nodes["Principled BSDF"]
    b.inputs["Roughness"].default_value = rough
    b.inputs["Specular IOR Level"].default_value = 0.3
    nz = nt.nodes.new("ShaderNodeTexNoise")
    nz.inputs["Scale"].default_value = 18
    nz.inputs["Detail"].default_value = 6
    nz.noise_dimensions = '4D'
    nz.inputs["W"].default_value = seed
    ramp = nt.nodes.new("ShaderNodeValToRGB")
    c = srgb(color)
    ramp.color_ramp.elements[0].position = 0.35
    ramp.color_ramp.elements[0].color = (c[0] * 0.72, c[1] * 0.72, c[2] * 0.72, 1)
    ramp.color_ramp.elements[1].position = 0.7
    ramp.color_ramp.elements[1].color = (min(1, c[0] * 1.18), min(1, c[1] * 1.18), min(1, c[2] * 1.18), 1)
    nt.links.new(nz.outputs["Fac"], ramp.inputs["Fac"])
    nt.links.new(ramp.outputs["Color"], b.inputs["Base Color"])
    nz2 = nt.nodes.new("ShaderNodeTexNoise")
    nz2.inputs["Scale"].default_value = 260
    nz2.inputs["Detail"].default_value = 3
    bp = nt.nodes.new("ShaderNodeBump")
    bp.inputs["Strength"].default_value = 0.12
    nt.links.new(nz2.outputs[0], bp.inputs["Height"])
    nt.links.new(bp.outputs[0], b.inputs["Normal"])
    return m


def skirt_loft(body, z_top, z_hem, flare, push, name, mat, rig, n_ang=56, n_z=26, shrink=0.0, xlim=0.24,
               bone="J_Bip_C_Hips"):
    """革の筒 (すそ・胴)。体の輪切りの外側をなぞる。flare: 下へ行くほど広げる割合。
    shrink: 下へ 1 m 行くあいだに細くなってよい量 (0 なら細くならない。胸から下へまっすぐ落ちる革)。"""
    co = mesh_co(body)
    ang = np.linspace(0, 2 * np.pi, n_ang, endpoint=False)
    zs = np.linspace(z_top, z_hem, n_z)

    def radius_at(z, cx, cy, tol=0.015):
        sel = co[(np.abs(co[:, 2] - z) < tol) & (np.abs(co[:, 0]) < xlim)]
        r = np.zeros(n_ang)
        if len(sel) == 0:
            return r
        a = np.arctan2(sel[:, 1] - cy, sel[:, 0] - cx) % (2 * np.pi)
        d = np.hypot(sel[:, 0] - cx, sel[:, 1] - cy)
        idx = (a / (2 * np.pi) * n_ang).astype(int) % n_ang
        np.maximum.at(r, idx, d)
        return r
    top = co[np.abs(co[:, 2] - z_top) < 0.01]
    cx, cy = 0.0, float(np.median(top[:, 1]))
    rings = []
    prev = None
    for k, z in enumerate(zs):
        r = radius_at(z, cx, cy)
        # 角の中で空いたところは、まわりでうめて、なめらかに
        for _ in range(8):
            r = np.maximum(r, 0.5 * (np.roll(r, 1) + np.roll(r, -1)) * 0.995)
        r = np.maximum(r, np.convolve(np.concatenate([r[-3:], r, r[:3]]), np.ones(5) / 5, mode='same')[3:-3])
        if prev is None:
            base = r.copy()
        t = k / (n_z - 1)
        want = np.maximum(r + push, base * (1 + flare * t) + push)
        if prev is not None:
            want = np.maximum(want, prev - shrink * abs(zs[1] - zs[0]))  # 上から落ちる革 (急に細くならない)
        prev = want
        rings.append(np.stack([cx + want * np.cos(ang), cy + want * np.sin(ang), np.full(n_ang, z)], 1))
    bm = bmesh.new()
    vs = [[bm.verts.new(p) for p in ring] for ring in rings]
    for k in range(n_z - 1):
        for i in range(n_ang):
            j = (i + 1) % n_ang
            bm.faces.new((vs[k][i], vs[k][j], vs[k + 1][j], vs[k + 1][i]))
    bm.normal_update()
    me = bpy.data.meshes.new(name)
    bm.to_mesh(me)
    bm.free()
    ob = bpy.data.objects.new(name, me)
    bpy.context.scene.collection.objects.link(ob)
    ob.data.materials.append(mat)
    for p in ob.data.polygons:
        p.use_smooth = True
    sol = ob.modifiers.new("thick", 'SOLIDIFY')
    sol.thickness = 0.003
    sol.offset = 1.0
    g = ob.vertex_groups.new(name=bone)
    g.add(list(range(len(me.vertices))), 1.0, 'REPLACE')
    ob.parent = rig
    am = ob.modifiers.new("arm", 'ARMATURE')
    am.object = rig
    return ob


def dress(P, body, rig, F):
    """革の長い貫頭衣 (袖なしに近い短い袖) と、すそ、帯。D の高さは女の素体の高さ。"""
    D = P["outfit"]["dress"]
    m = leather_mat("leather", D["color"], seed=0.3)
    mb = leather_mat("belt", D["belt"], rough=0.55, seed=1.7)
    parts = []
    # 肩と短い袖: 脇の少し下から首の付け根まで (腕も含める)
    parts.append(make_band(body, *F.z(np.array([D["arm"] - 0.03, D["neck"]])), "tunic_sh", m, D.get("push", 0.006) + 0.002,
                           xcut=D.get("sleeve_x", 0.26)))
    for ob in parts:
        dt = ob.modifiers.new("w", 'DATA_TRANSFER')
        dt.object = body
        dt.use_vert_data = True
        dt.data_types_verts = {'VGROUP_WEIGHTS'}
        dt.vert_mapping = 'NEAREST'
        bpy.context.view_layer.objects.active = ob
        bpy.ops.object.datalayout_transfer(modifier=dt.name)
        bpy.ops.object.modifier_apply(modifier=dt.name)
        ob.parent = rig
        am = ob.modifiers.new("arm", 'ARMATURE')
        am.object = rig
    # 胴: 脇から腰まで。胸から下はまっすぐ落ちる (体のくぼみをなぞらない)
    parts.append(skirt_loft(body, float(F.z(D["arm"])), float(F.z(D["waist"] - 0.01)), 0.0, D.get("push", 0.006),
                            "tunic", m, rig, n_z=30, shrink=0.3, xlim=0.17, bone="J_Bip_C_Spine"))
    # すそ: 腰からひざ下まで
    parts.append(skirt_loft(body, float(F.z(D["waist"])), float(F.z(D["hem"])), D.get("flare", 0.25),
                            D.get("push", 0.006) + 0.008, "skirt", m, rig))
    # 帯: 腰に細い革紐
    belt = make_band(body, *F.z(np.array([D["waist"] - 0.012, D["waist"] + 0.012])), "belt", mb, D.get("push", 0.006) + 0.012)
    belt.modifiers["thick"].thickness = 0.004
    dt = belt.modifiers.new("w", 'DATA_TRANSFER')
    dt.object = body
    dt.use_vert_data = True
    dt.data_types_verts = {'VGROUP_WEIGHTS'}
    dt.vert_mapping = 'NEAREST'
    bpy.context.view_layer.objects.active = belt
    bpy.ops.object.datalayout_transfer(modifier=dt.name)
    bpy.ops.object.modifier_apply(modifier=dt.name)
    belt.parent = rig
    am = belt.modifiers.new("arm", 'ARMATURE')
    am.object = rig
    parts.append(belt)
    return parts


def outfit(P, body, rig, F):
    O = P["outfit"]
    if O.get("dress"):
        return dress(P, body, rig, F)
    m = bpy.data.materials.new("cloth")
    m.use_nodes = True
    nt = m.node_tree
    b = nt.nodes["Principled BSDF"]
    b.inputs["Base Color"].default_value = srgb(O["color"])
    b.inputs["Roughness"].default_value = 0.85
    b.inputs["Sheen Weight"].default_value = 0.08
    b.inputs["Specular IOR Level"].default_value = 0.2
    # 布目 (細かい凹凸)
    nz = nt.nodes.new("ShaderNodeTexNoise")
    nz.inputs["Scale"].default_value = 900
    bp = nt.nodes.new("ShaderNodeBump")
    bp.inputs["Strength"].default_value = 0.08
    nt.links.new(nz.outputs[0], bp.inputs["Height"])
    nt.links.new(bp.outputs[0], b.inputs["Normal"])
    parts = []
    if O.get("top"):
        parts.append(make_band(body, *F.z(np.array(O["top"])), "top", m, 0.0035, bridge=True))
    parts.append(make_band(body, *F.z(np.array(O["shorts"])), "shorts", m, 0.003))
    for ob in parts:
        # vertex group の重みを体から写す
        dt = ob.modifiers.new("w", 'DATA_TRANSFER')
        dt.object = body
        dt.use_vert_data = True
        dt.data_types_verts = {'VGROUP_WEIGHTS'}
        dt.vert_mapping = 'NEAREST'
        bpy.context.view_layer.objects.active = ob
        bpy.ops.object.datalayout_transfer(modifier=dt.name)
        bpy.ops.object.modifier_apply(modifier=dt.name)
        ob.parent = rig
        am = ob.modifiers.new("arm", 'ARMATURE')
        am.object = rig
    return parts


# ---------------------------------------------------------------- 表情
def set_expr(face, expr):
    for kb in face.data.shape_keys.key_blocks[1:]:
        kb.value = expr.get(kb.name, 0.0)


def set_gaze(rig, down_deg):
    """目の骨 (J_Adj_*_FaceEye) を下へ向ける (伏し目)。描くときだけ。"""
    for side in ("L", "R"):
        pb = rig.pose.bones.get("J_Adj_%s_FaceEye" % side)
        if pb:
            pb.rotation_mode = 'XYZ'
            pb.rotation_euler = (-math.radians(down_deg), 0, 0)


# ---------------------------------------------------------------- 光と撮影
def setup_scene(quick, samples):
    s = bpy.context.scene
    s.render.engine = 'CYCLES'
    s.cycles.device = 'CPU'
    s.cycles.samples = 24 if quick else samples
    s.cycles.use_denoising = True
    s.cycles.max_bounces = 8
    s.cycles.transparent_max_bounces = 16
    # 色の管理: Standard (テクスチャの色をそのまま)、露出 0。白飛びしないよう光の量で合わせる
    s.view_settings.view_transform = 'Standard'
    s.view_settings.look = 'None'
    s.view_settings.exposure = 0.0
    s.view_settings.gamma = 1.0
    w = bpy.data.worlds.new("w")
    s.world = w
    w.use_nodes = True
    w.node_tree.nodes["Background"].inputs[0].default_value = srgb("#aeb3bb")
    nt = w.node_tree
    nt.nodes["Background"].inputs[1].default_value = 0.4
    bg2 = nt.nodes.new("ShaderNodeBackground")
    bg2.inputs[0].default_value = srgb("#aeb3bb")
    bg2.inputs[1].default_value = 1.0
    lp = nt.nodes.new("ShaderNodeLightPath")
    mx = nt.nodes.new("ShaderNodeMixShader")
    nt.links.new(lp.outputs["Is Camera Ray"], mx.inputs[0])
    nt.links.new(nt.nodes["Background"].outputs[0], mx.inputs[1])
    nt.links.new(bg2.outputs[0], mx.inputs[2])
    nt.links.new(mx.outputs[0], nt.nodes["World Output"].inputs[0])

    def area(name, loc, energy, size, color=(1, 1, 1), target=(0, 0, 1.0)):
        ld = bpy.data.lights.new(name, 'AREA')
        ld.energy = energy
        ld.size = size
        ld.color = color
        ob = bpy.data.objects.new(name, ld)
        s.collection.objects.link(ob)
        ob.location = loc
        ob.rotation_euler = (Vector(target) - Vector(loc)).to_track_quat('-Z', 'Y').to_euler()
        return ob
    # 正面 (+Y) を向いている。主光は右前上、補助光は左前、縁取り光は後ろの左右上 (tip 8)
    area("key", (-1.5, 2.6, 2.4), 240, 2.5, (1.0, 0.95, 0.88), (0, 0, 1.2))
    area("fill", (2.2, 2.0, 1.2), 100, 3.5, (0.88, 0.93, 1.0), (0, 0, 1.0))
    area("rimL", (-1.3, -2.2, 2.0), 130, 1.2, (1.0, 0.97, 0.92), (0, 0, 1.3))
    area("rimR", (1.4, -2.0, 1.6), 90, 1.2, (0.92, 0.96, 1.0), (0, 0, 1.2))
    bpy.ops.mesh.primitive_plane_add(size=8, location=(0, 0, 0))
    fl = bpy.context.object
    fl.name = "floor"
    fm = bpy.data.materials.new("floor")
    fm.use_nodes = True
    fm.node_tree.nodes["Principled BSDF"].inputs["Base Color"].default_value = srgb("#a3a8b0")
    fm.node_tree.nodes["Principled BSDF"].inputs["Roughness"].default_value = 0.9
    fl.data.materials.append(fm)
    return s


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--person", default="sena")
    ap.add_argument("--quick", action="store_true")
    ap.add_argument("--samples", type=int, default=96)
    ap.add_argument("--only", default="", help="sheet,face,expr,lineup,guide をカンマで (none なら書き出しだけ)")
    ap.add_argument("--no-tie", action="store_true")
    args = ap.parse_args(sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else sys.argv[1:])
    P = VROID[args.person]
    H = P["hair"]
    t0 = time.time()
    bpy.ops.wm.read_factory_settings(use_empty=True)
    rig, body, face, hairs = assemble(P)
    F = Frame(rig)
    sturdy(rig, body, hairs, P["body"], F)
    proportions(rig, [body, face] + hairs, P, F)
    F = Frame(rig)
    round_face(face, P["face"].get("round", 0.0), F)
    thick_brows(face, P["face"].get("brow_thick", 1.0))
    style = H.get("style", "keep")
    if H.get("crop"):
        crop_hair(hairs, face, body, F, H["crop"])
    if style in ("tie", "braid") and not args.no_tie:
        tie = tie_hair(hairs, body, rig, H, F)
        if style == "braid":
            braid(rig, tie, H, F)
    skin_imgs = skin_textures(P, body, face, rig, F)
    materials(P, [body, face] + hairs, skin_imgs)
    outfit(P, body, rig, F)
    set_expr(face, P["expr"])
    print(f"build: {time.time() - t0:.1f}s", flush=True)

    # 書き出し (.glb): 骨組み・重み・表情キーつき
    os.makedirs(OUT_GLB, exist_ok=True)
    glb = os.path.join(OUT_GLB, P["name"] + "_vroid.glb")
    for o in bpy.data.objects:
        o.select_set(o.type in ('MESH', 'ARMATURE'))
    bpy.ops.export_scene.gltf(filepath=glb, export_format='GLB', use_selection=True, export_apply=False,
                              export_yup=True, export_skins=True, export_morph=True)
    print("glb", glb, os.path.getsize(glb) // 1024, "KB", flush=True)
    set_gaze(rig, P.get("gaze_down", 0.0))

    only = set(args.only.split(",")) if args.only else {"sheet", "face", "expr", "lineup"}
    os.makedirs(OUT_PNG, exist_ok=True)
    s = setup_scene(args.quick, args.samples)
    times = {}
    top = max(float(mesh_co(o)[:, 2].max()) for o in bpy.data.objects if o.type == 'MESH' and o.name != "floor"
              and len(o.data.vertices))
    hgt = max(1.64, top + 0.03)
    print("top", round(top, 3), "frame", round(hgt, 3), flush=True)
    cz = hgt / 2
    name = P["name"] + "_vroid"
    if "sheet" in only:
        tmp = []
        for k, loc in enumerate([(0, 10, cz), (10, 0, cz), (0, -10, cz)]):
            cam = camera("c%d" % k, loc, (0, 0, cz), ortho=hgt * 1.1)
            p = os.path.join(OUT_PNG, f"_vtmp_{k}.png")
            times[f"sheet{k}"] = render(cam, p, 560, 1000)
            tmp.append(p)
        compose(tmp, os.path.join(OUT_PNG, f"{name}_3view.png"))
    fz = F.hb[2] + 0.05
    if "face" in only:
        cam = camera("face", (-0.13, 0.95, fz + 0.03), (0, 0, fz), lens=100)
        times["face"] = render(cam, os.path.join(OUT_PNG, f"{name}_face.png"), 900, 900)
    if "expr" in only:
        tmp = []
        for k, ex in enumerate([{}, P["expr"]]):
            set_expr(face, ex)
            cam = camera("e%d" % k, (-0.13, 0.95, fz + 0.03), (0, 0, fz), lens=100)
            p = os.path.join(OUT_PNG, f"_vtmp_e{k}.png")
            times[f"expr{k}"] = render(cam, p, 560, 560)
            tmp.append(p)
        compose(tmp, os.path.join(OUT_PNG, f"{name}_expr.png"))
        set_expr(face, P["expr"])
    if "guide" in only and P.get("guide"):
        # 案内役の吹き出し用の胸から上の絵 (正方形、無地の背景)。表情ごとに 1 枚
        G = P["guide"]
        bpy.data.objects["floor"].hide_render = True
        nt = s.world.node_tree
        for n in nt.nodes:
            if n.type == 'BACKGROUND' and n.inputs[1].default_value == 1.0:
                n.inputs[0].default_value = srgb(G.get("bg", "#e6e1d8"))
        # 腕を下ろす (T の形のままだと胸から上の絵で腕が横にのびる)
        from mathutils import Quaternion
        for side, sg in (("L", -1), ("R", 1)):
            pb = rig.pose.bones["J_Bip_%s_UpperArm" % side]
            ax = rig.data.bones[pb.name].matrix_local.to_3x3().inverted() @ Vector((0, 1, 0))
            pb.rotation_mode = 'QUATERNION'
            pb.rotation_quaternion = Quaternion(ax, sg * math.radians(G.get("arm_down", 68)))
        bpy.context.view_layer.update()
        bz = F.hb[2] + G.get("dz", -0.02)
        for ex_name, ex in G["expr"].items():
            set_expr(face, ex)
            cam = camera("g_" + ex_name, (-0.08, G.get("dist", 0.95), bz + 0.03), (0, 0, bz), lens=G.get("lens", 85))
            times["guide_" + ex_name] = render(cam, os.path.join(OUT_PNG, f"guide_{P['name']}_{ex_name}.png"),
                                               512, 512)
        set_expr(face, P["expr"])
        for side in ("L", "R"):
            rig.pose.bones["J_Bip_%s_UpperArm" % side].rotation_quaternion = (1, 0, 0, 0)
        bpy.data.objects["floor"].hide_render = False
    if "lineup" in only:
        # 5 人を並べる絵の部品: 同じ縮尺の正面 (背景は透明) と、正面の顔
        d = os.path.join(WORK, "lineup")
        os.makedirs(d, exist_ok=True)
        bpy.data.objects["floor"].hide_render = True
        s.render.film_transparent = True
        cam = camera("lu", (0, 10, 1.0), (0, 0, 1.0), ortho=2.0)
        cam.data.sensor_fit = 'VERTICAL'
        times["lineup"] = render(cam, os.path.join(d, P["name"] + "_body.png"), 1000, 1100)
        s.render.film_transparent = False
        bpy.data.objects["floor"].hide_render = False
        cam = camera("luf", (0, 0.95, fz), (0, 0, fz), lens=100)
        times["lineup_face"] = render(cam, os.path.join(d, P["name"] + "_face.png"), 600, 600)
    print("TIMES", {k: round(v, 1) for k, v in times.items()}, "total", round(time.time() - t0, 1), flush=True)


if __name__ == "__main__":
    main()
