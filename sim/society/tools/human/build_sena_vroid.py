"""セナを VRoid の CC0 サンプルから作る (中間の作風: 線はアニメ、面は写実の光)。

使いかた (README.md の「VRoid の素体から作る道」):
    BLENDER_USER_RESOURCES=/dev/shm/sena/userres PYTHONPATH=/dev/shm/bpy \
        python3.11 -u run.py build_sena_vroid.py -- [--quick] [--only sheet,face,expr] > log 2>&1

- 顔と髪: VRoid サンプル「千駄ヶ谷 篠」(CC0)。
- 体と骨組み: VRoid サンプル「HairSample_Female」(CC0)。篠の体は制服の下の肌が
  切りとられているため、服の下まで肌がある素体の体を使う。骨の名前は同じ (J_Bip_*)。
- 出力: PNG を sim/society/out/human/、.glb を /dev/shm/sena/sena_vroid.glb に書く。
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


def assemble(P):
    hs, _ = import_vrm(P["body_src"], "hs_")
    sh, js = import_vrm(P["face_src"], "sh_")
    rig = hs["Armature"]
    rig.name = "sena_rig"
    delta = np.array(rig.data.bones["J_Bip_C_Head"].head_local) - \
        np.array(sh["Armature"].data.bones["J_Bip_C_Head"].head_local)
    print("head delta", delta.round(4), flush=True)

    body = hs["Body"]
    body.name = "body"
    delete_faces(body, lambda n: "SKIN" in n)          # 服と靴を消す

    face = sh["Face"]
    face.name = "face"
    # 表情キーに VRoid の名前をつける (target_N -> Fcl_...)
    names = js["meshes"][0]["extras"]["targetNames"] if "extras" in js["meshes"][0] else \
        js["meshes"][0]["primitives"][0]["extras"]["targetNames"]
    for i, n in enumerate(names):
        kb = face.data.shape_keys.key_blocks.get("target_%d" % i)
        if kb:
            kb.name = n.split(".M_F00_000_00_")[-1].split(".M_")[-1]
    retarget(face, rig, delta)

    # 髪: 前と横の髪 (Hair001) と、体についている後ろ髪 (HairBack)
    hair = sh["Hair001"]
    hair.name = "hair"
    if P["hair"].get("remove_clip"):
        delete_faces(hair, lambda n: "HAIR_02" not in n)   # 髪どめ (青い×)
    back = sh["Body"].copy()
    back.data = sh["Body"].data.copy()
    bpy.context.scene.collection.objects.link(back)
    back.name = "hair_back"
    delete_faces(back, lambda n: "HairBack" in n)
    retarget(hair, rig, delta, rigid=True)
    retarget(back, rig, delta, rigid=True)

    # いらないものを消す
    for k in ("Armature", "Body", "Icosphere", "Hairs", "secondary"):
        o = sh.get(k)
        if o:
            bpy.data.objects.remove(o)
    for k in ("Face", "Hair001", "Icosphere", "Hairs", "secondary"):
        o = hs.get(k)
        if o:
            bpy.data.objects.remove(o)
    for ob in (body, face, hair, back):
        for p in ob.data.polygons:
            p.use_smooth = True
    return rig, body, face, hair, back


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


def body_field(p, B):
    """がっしりさせる変形 (休みの姿勢の座標で)。p: (N,3)。"""
    x, y, z = p[:, 0], p[:, 1], p[:, 2]
    q = p.copy()
    ax = np.abs(x)
    sg = np.sign(x)
    # 肩幅: 首から外の上半身と腕を横へずらす
    band = smooth(z, 1.10, 1.25) * (1 - smooth(z, 1.355, 1.395))
    q[:, 0] += sg * B["shoulder"] * smooth(ax, 0.035, 0.12) * band
    # 腰: 骨盤のあたりを横に広げる
    hip = smooth(z, 0.80, 0.90) * (1 - smooth(z, 0.97, 1.07)) * (ax < 0.25)
    q[:, 0] *= 1 + B["hips"] * hip
    # 胴まわり: くびれを弱く
    wst = np.exp(-((z - 1.04) / 0.07) ** 2) * (ax < 0.2)
    q[:, 0] *= 1 + B["waist"] * wst
    q[:, 1] = y + (y - 0.01) * 0.5 * B["waist"] * wst
    return q


def sturdy(rig, body, others, B):
    me = body.data
    co = np.empty(len(me.vertices) * 3, np.float32)
    me.vertices.foreach_get("co", co)
    co = co.reshape(-1, 3)
    co = co + limb_field(body, rig, B["limbs"])
    me.vertices.foreach_set("co", body_field(co, B).ravel())
    me.update()
    # 髪など、体の近くのもの (顔より下だけ変わる)
    for ob in others:
        me = ob.data
        co = np.empty(len(me.vertices) * 3, np.float32)
        me.vertices.foreach_get("co", co)
        me.vertices.foreach_set("co", body_field(co.reshape(-1, 3), B).ravel())
        me.update()
    # 骨も同じだけ動かす (腕の骨が腕の中に残るように)
    bpy.context.view_layer.objects.active = rig
    bpy.ops.object.mode_set(mode='EDIT')
    for eb in rig.data.edit_bones:
        for attr in ("head", "tail"):
            v = np.array(getattr(eb, attr))[None]
            if "Leg" in eb.name or "Foot" in eb.name or "Toe" in eb.name:
                continue
            setattr(eb, attr, Vector(body_field(v, B)[0]))
    bpy.ops.object.mode_set(mode='OBJECT')


def round_face(face, R):
    """ほおとあごを少し横に広げて丸顔に。首とのつなぎ目と目のまわりは動かさない。"""
    me = face.data
    n = len(me.vertices)
    bm = bmesh.new()
    bm.from_mesh(me)
    bnd = np.array([v.co[:] for v in bm.verts if v.is_boundary])
    bm.free()
    base = np.empty(n * 3, np.float32)
    me.shape_keys.key_blocks[0].data.foreach_get("co", base)
    base = base.reshape(-1, 3)
    # 境目 (首) からの距離
    from mathutils.kdtree import KDTree
    kd = KDTree(len(bnd))
    for i, b in enumerate(bnd):
        kd.insert(b, i)
    kd.balance()
    dist = np.array([kd.find(Vector(p))[2] for p in base])
    z = base[:, 2]
    w = smooth(dist, 0.006, 0.025) * smooth(z, 1.385, 1.415) * (1 - smooth(z, 1.445, 1.462))
    w *= smooth(np.abs(base[:, 0]), 0.0, 0.03)
    for kb in me.shape_keys.key_blocks:
        co = np.empty(n * 3, np.float32)
        kb.data.foreach_get("co", co)
        co = co.reshape(-1, 3)
        co[:, 0] *= 1 + R * w
        kb.data.foreach_set("co", co.ravel())
    me.update()


# ---------------------------------------------------------------- 髪を低い位置で結ぶ
def tie_hair(hair, back, body, rig, H):
    """後ろの髪を、うなじで 1 本にまとめて背中に沿わせる (形を寄せるだけ)。
    前で顔の横に下がる束は残し、肩の高さまで短くする。結び紐の輪も作る。"""
    hb = np.array(rig.data.bones["J_Bip_C_Head"].head_local)
    zt, zs, tw = H["tie_z"], H["gather_from"], H["tail_width"]
    # 背中の線 (体の真ん中付近で一番うしろの y、1 cm ごと)
    bc = np.array([v.co[:] for v in body.data.vertices])
    bc = bc[np.abs(bc[:, 0]) < 0.06]
    zb = np.arange(0.9, 1.7, 0.01)
    back_y = np.array([bc[np.abs(bc[:, 2] - z) < 0.008, 1].min() if np.any(np.abs(bc[:, 2] - z) < 0.008)
                       else np.nan for z in zb])
    ok = ~np.isnan(back_y)
    back_of = lambda z: np.interp(z, zb[ok], back_y[ok])  # noqa: E731
    pts = []
    for ob in (hair, back):
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
    for ob, p in zip((hair, back), pts):
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
        zc = H["front_from"]
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


def tan_image(img, target, skin_mask=None):
    """テクスチャの肌の中央値が target (線形) になるように掛け算する。"""
    a = img_array(img)
    rgb = to_lin(a[..., :3])
    sel = (a[..., 3] > 0.5) & (rgb.sum(-1) > 0.3)
    if skin_mask is not None:
        sel &= skin_mask
    med = np.median(rgb[sel], axis=0)
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


def skin_textures(P, body, face, rig):
    S = P["skin"]
    tan = lin(S["tan"])
    fm = next(m for m in face.data.materials if "Face_00_SKIN" in m.name)
    bmat = next(m for m in body.data.materials if "Body_00_SKIN" in m.name)
    fimg, bimg = tex_of(fm), tex_of(bmat)
    fa = tan_image(fimg, tan)
    ba = tan_image(bimg, tan)
    # ほお・鼻先の赤み (顔のテクスチャ)
    pf = UVPainter(face, "Face_00_SKIN")
    me = face.data
    base = np.array([v.co[:] for v in me.vertices])
    hb = np.array(rig.data.bones["J_Bip_C_Head"].head_local)
    pts, al = [], []
    rng = np.random.default_rng(29)
    for sx in (-1, 1):
        c = np.array([sx * 0.034, hb[1] + 0.085, 1.447])
        for _ in range(260):
            d = rng.normal(0, 0.009, 3)
            d[1] = 0
            q = c + d
            pts.append(q + np.array([0, 0.03, 0]))
            al.append(S["blush_alpha"] * math.exp(-(np.linalg.norm(d) / 0.012) ** 2))
    # 鼻先
    nose = base[np.argmax(base[:, 1] * (np.abs(base[:, 0]) < 0.004) * (base[:, 2] < 1.46) * (base[:, 2] > 1.43))]
    for _ in range(40):
        d = rng.normal(0, 0.003, 3)
        pts.append(nose + d)
        al.append(S["blush_alpha"] * 0.6 * math.exp(-(np.linalg.norm(d) / 0.004) ** 2))
    # 最も近い表面点へ (前から当てる)
    pf.paint(fa, pts, lin(S["blush"]), al, 7.0)
    # 左の前腕の外側 (上を向いた面) に古い傷
    pb = UVPainter(body, "Body_00_SKIN")
    la = rig.data.bones["J_Bip_L_LowerArm"]
    h, t = np.array(la.head_local), np.array(la.tail_local)
    pts, al = [], []
    for k in range(70):
        s = 0.35 + 0.22 * k / 69
        c = h + (t - h) * s
        c = c + np.array([0, (k / 69 - 0.5) * 0.022, 0.06])   # 少し斜め、上から当てる
        pts.append(c)
        al.append(S["scar_alpha"] * (1 - abs(k / 69 - 0.5) * 1.4))
    pb.paint(ba, pts, lin(S["scar"]), al, 2.2)
    fimg2 = save_image(fimg, fa, "sena_face_skin")
    bimg2 = save_image(bimg, ba, "sena_body_skin")
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
            elif "HAIR" in nm:
                def hair_col(nt, src, dst):
                    tex = next(n for n in nt.nodes if n.type == 'TEX_IMAGE')
                    bw = nt.nodes.new("ShaderNodeRGBToBW")
                    nt.links.new(tex.outputs["Color"], bw.inputs[0])
                    ramp = nt.nodes.new("ShaderNodeValToRGB")
                    ramp.color_ramp.elements[0].color = srgb(Hh["dark"])
                    ramp.color_ramp.elements[0].position = Hh.get("ramp_lo", 0.35)
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
def make_band(body, z0, z1, name, mat, push, bridge=False):
    bm = bmesh.new()
    bm.from_mesh(body.data)
    for z, keep_above in ((z0, True), (z1, False)):
        geom = bm.verts[:] + bm.edges[:] + bm.faces[:]
        r = bmesh.ops.bisect_plane(bm, geom=geom, plane_co=(0, 0, z), plane_no=(0, 0, 1))
        dele = [v for v in bm.verts if (v.co.z < z - 1e-5 if keep_above else v.co.z > z + 1e-5)]
        bmesh.ops.delete(bm, geom=dele, context='VERTS')
    # 腕を除く (胴の幅より外)
    dele = [f for f in bm.faces if abs(f.calc_center_median().x) > 0.165]
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


def outfit(P, body, rig):
    O = P["outfit"]
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
    top = make_band(body, *O["top"], "top", m, 0.0035, bridge=True)
    shorts = make_band(body, *O["shorts"], "shorts", m, 0.003)
    for ob in (top, shorts):
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
    return top, shorts


# ---------------------------------------------------------------- 表情
def set_expr(face, expr):
    for kb in face.data.shape_keys.key_blocks[1:]:
        kb.value = expr.get(kb.name, 0.0)


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
    ap.add_argument("--only", default="", help="sheet,face,expr をカンマで (none なら書き出しだけ)")
    ap.add_argument("--no-tie", action="store_true")
    args = ap.parse_args(sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else sys.argv[1:])
    P = VROID[args.person]
    t0 = time.time()
    bpy.ops.wm.read_factory_settings(use_empty=True)
    rig, body, face, hair, back = assemble(P)
    sturdy(rig, body, [hair, back], P["body"])
    round_face(face, P["face"]["round"])
    if P["hair"].get("tie") and not args.no_tie:
        tie_hair(hair, back, body, rig, P["hair"])
    skin_imgs = skin_textures(P, body, face, rig)
    materials(P, [body, face, hair, back], skin_imgs)
    outfit(P, body, rig)
    set_expr(face, P["smile"])
    print(f"build: {time.time() - t0:.1f}s", flush=True)

    # 書き出し (.glb): 骨組み・重み・表情キーつき
    os.makedirs(OUT_GLB, exist_ok=True)
    glb = os.path.join(OUT_GLB, P["name"] + "_vroid.glb")
    for o in bpy.data.objects:
        o.select_set(o.type in ('MESH', 'ARMATURE'))
    bpy.ops.export_scene.gltf(filepath=glb, export_format='GLB', use_selection=True, export_apply=False,
                              export_yup=True, export_skins=True, export_morph=True)
    print("glb", glb, os.path.getsize(glb) // 1024, "KB", flush=True)

    only = set(args.only.split(",")) if args.only else {"sheet", "face", "expr"}
    os.makedirs(OUT_PNG, exist_ok=True)
    setup_scene(args.quick, args.samples)
    times = {}
    hgt = 1.64
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
    hb = rig.data.bones["J_Bip_C_Head"].head_local
    fz = hb.z + 0.05
    if "face" in only:
        cam = camera("face", (-0.13, 0.95, fz + 0.03), (0, 0, fz), lens=100)
        times["face"] = render(cam, os.path.join(OUT_PNG, f"{name}_face.png"), 900, 900)
    if "expr" in only:
        tmp = []
        for k, ex in enumerate([{}, P["smile"]]):
            set_expr(face, ex)
            cam = camera("e%d" % k, (-0.13, 0.95, fz + 0.03), (0, 0, fz), lens=100)
            p = os.path.join(OUT_PNG, f"_vtmp_e{k}.png")
            times[f"expr{k}"] = render(cam, p, 560, 560)
            tmp.append(p)
        compose(tmp, os.path.join(OUT_PNG, f"{name}_expr.png"))
        set_expr(face, P["smile"])
    print("TIMES", {k: round(v, 1) for k, v in times.items()}, "total", round(time.time() - t0, 1), flush=True)


if __name__ == "__main__":
    main()
