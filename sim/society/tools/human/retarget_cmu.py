"""CMU のモーションキャプチャー (BVH) を、VRoid の五人 (<名前>_vroid.glb) に移して、動き 12 個つきの glb と json を作る。

動画 D1V (1 日目をクラウドで人のモデルで撮る、2026-11-23) のため。本人の PC の D1P (human-model/scripts/export_people_glb.py、Blender)
と同じ 12 個の動きを、クラウドの CPU だけで、numpy で作る (Blender は使わない。glb の中の形・重み・表情キー・材質はそのまま残し、
動きのデータ (animations) を書き足すだけ。メモリは 1 人 0.3 GB ほど)。

    python3 retarget_cmu.py --bvh /dev/shm/cmu/una/data --src /dev/shm/sena --out /dev/shm/people_glb [--only sena] [--tex 1024]
    python3 retarget_cmu.py --bvh /dev/shm/cmu/una/data --analyze 18_08     # 区間を選ぶための下見 (0.5 秒ごとの腰の高さ・速さなど)

出力: <out>/<ファイル名>.glb (動き 12 個) と <ファイル名>.json ({"clips": {名前: {"sec": 長さ秒, "speed": 進む速さ m/秒}}})。
名前とファイルの対応は app/replay3d_people.js の FILES (ルオ ruo・セナ sena・タヒ tahi・ウィロ wiro・イサ isa)。

移し方 (どの動きも同じ):
- BVH の 1 コマ目は T ポーズ (cgspeed の変換の決まり)。VRoid の素の姿勢も T ポーズなので、骨ごとに「T ポーズからの世界での回り方」を写す
  (骨の向きの決め方がちがっても合う)。指は動かさず、少し曲げた形にする。
- その場で動く形: 腰の前後左右の移動を消す。向きは、動きの最初の向き (歩くものは進む向き) を前にそろえる。
- 足で地面の高さをそろえる: コマごとに、足・つま先 (横になるときは腰・頭・肘なども) のいちばん低いところが地面に来るように腰の高さを決める。
- 120 コマ/秒を 30 コマ/秒に間引く。
- glb の向き: VRoid の glb は -z を向いているので、いちばん上の節を y のまわりに 180° 回して +z を向かせる (replay3d_people.js の決め)。
- 材質: three r128 で重くならないよう、clearcoat・sheen・specular の拡張をはずす (ふつうの MeshStandardMaterial になる)。
  目の線・まつ毛・眉・ハイライトは光の影響なし (unlit) のまま。画像は --tex の大きさ (既定 1024) まで縮める。

動きのデータ: CMU Graphics Lab Motion Capture Database (mocap.cs.cmu.edu)。BVH は B. Hahne (cgspeed) の変換を
https://github.com/una-dinosauria/cmu-mocap (commit 09a07f54f3bbb58797325f009282d0b2048a2871) から取る。
条件 (READMEFIRST.txt にある CMU の言葉): "This data is free for use in research and commercial projects worldwide."
"""
import argparse
import io
import json
import math
import os
import struct

import numpy as np

FILES = {"ルオ": "ruo", "セナ": "sena", "タヒ": "tahi", "ウィロ": "wiro", "イサ": "isa",
         "ナギ": "nagi", "ソル": "sol"}  # ナギ・ソル: 2026-11-25 (G1 からの村の人。動画 G1F2V・G1F3V)
FPS_IN, STEP = 120, 4          # BVH は 120 コマ/秒。4 コマごとに取って 30 コマ/秒
FPS = FPS_IN / STEP

# 動き: 名前 → (BVH, 始まり秒, 終わり秒, 向きの決め方, ほか)。秒は T ポーズのコマのあとから数える。
#   face: "start" 最初の腰の向き / "mean" 腰の向きの平均 / "end" 最後の腰の向き / "travel" 進む向き
#   loop: 区間の中から、つながりのよい 1 周 (min〜max 秒) を探す。speed: 進む速さを json に書く
CLIPS = {
    "idle":    dict(bvh="18_08", t=(3.0, 9.5), face="mean"),             # 立って待つ (話の記録の、手を下ろしているところ)
    "walk":    dict(bvh="08_01", t=(0.3, 2.3), face="travel", loop=(0.8, 1.4), speed=True),  # 足の運び 1 回分 (つながりのよい 1 周)
    "search":  dict(bvh="77_25", t=(1.5, 5.5), face="travel", speed=True),  # 用心して歩きさがす
    "look":    dict(bvh="77_06", t=(1.5, 9.0), face="mean"),              # かがんで地面をさがす
    "pick":    dict(bvh="69_73", t=(2.4, 4.4), face="mean"),              # 身をかがめて拾う
    "probe":   dict(bvh="77_08", t=(1.2, 3.4), face="mean"),              # しゃがんで、地面のものを両手で調べる
    "reach":   dict(bvh="15_07", t=(1.2, 3.6), face="start"),             # 身をのり出して、つま先立ちで取る
    "stretch": dict(bvh="13_10", t=(0.6, 3.0), face="mean"),              # 背のびして、上のものを取る
    "talk":    dict(bvh="18_08", t=(10.0, 17.0), face="mean"),            # 手ぶりで話す
    "give":    dict(bvh="22_13", t=(0.2, 2.6), face="start"),             # 手渡す
    "eat":     dict(bvh="79_12", t=(1.0, 7.5), face="mean"),              # 立って食べる
    "lie":     dict(bvh="77_16", t=(0.5, 4.5), face="end"),               # 横になった姿勢から起き上がる (replay3d_people.js が逆に流す)
}

# 骨の対応: BVH (cgspeed の名前) → VRoid (J_Bip_*)
MAP = {
    "Hips": "J_Bip_C_Hips", "LowerBack": "J_Bip_C_Spine", "Spine": "J_Bip_C_Chest", "Spine1": "J_Bip_C_UpperChest",
    "Neck1": "J_Bip_C_Neck", "Head": "J_Bip_C_Head",
}
for s, S in (("Left", "L"), ("Right", "R")):
    MAP.update({f"{s}Shoulder": f"J_Bip_{S}_Shoulder", f"{s}Arm": f"J_Bip_{S}_UpperArm", f"{s}ForeArm": f"J_Bip_{S}_LowerArm",
                f"{s}Hand": f"J_Bip_{S}_Hand", f"{s}UpLeg": f"J_Bip_{S}_UpperLeg", f"{s}Leg": f"J_Bip_{S}_LowerLeg",
                f"{s}Foot": f"J_Bip_{S}_Foot", f"{s}ToeBase": f"J_Bip_{S}_ToeBase"})


# ---------- 回転の道具 ----------
def rot_axis(ax, deg):
    a = math.radians(deg); c, s = math.cos(a), math.sin(a)
    if ax == "X": return np.array([[1, 0, 0], [0, c, -s], [0, s, c]])
    if ax == "Y": return np.array([[c, 0, s], [0, 1, 0], [-s, 0, c]])
    return np.array([[c, -s, 0], [s, c, 0], [0, 0, 1]])


def quat_to_mat(q):
    x, y, z, w = q
    return np.array([[1 - 2 * (y * y + z * z), 2 * (x * y - z * w), 2 * (x * z + y * w)],
                     [2 * (x * y + z * w), 1 - 2 * (x * x + z * z), 2 * (y * z - x * w)],
                     [2 * (x * z - y * w), 2 * (y * z + x * w), 1 - 2 * (x * x + y * y)]])


def mat_to_quat(m):
    t = np.trace(m)
    if t > 0:
        s = math.sqrt(t + 1.0) * 2; w = 0.25 * s
        x = (m[2, 1] - m[1, 2]) / s; y = (m[0, 2] - m[2, 0]) / s; z = (m[1, 0] - m[0, 1]) / s
    elif m[0, 0] > m[1, 1] and m[0, 0] > m[2, 2]:
        s = math.sqrt(1.0 + m[0, 0] - m[1, 1] - m[2, 2]) * 2; w = (m[2, 1] - m[1, 2]) / s
        x = 0.25 * s; y = (m[0, 1] + m[1, 0]) / s; z = (m[0, 2] + m[2, 0]) / s
    elif m[1, 1] > m[2, 2]:
        s = math.sqrt(1.0 + m[1, 1] - m[0, 0] - m[2, 2]) * 2; w = (m[0, 2] - m[2, 0]) / s
        x = (m[0, 1] + m[1, 0]) / s; y = 0.25 * s; z = (m[1, 2] + m[2, 1]) / s
    else:
        s = math.sqrt(1.0 + m[2, 2] - m[0, 0] - m[1, 1]) * 2; w = (m[1, 0] - m[0, 1]) / s
        x = (m[0, 2] + m[2, 0]) / s; y = (m[1, 2] + m[2, 1]) / s; z = 0.25 * s
    q = np.array([x, y, z, w]); return q / np.linalg.norm(q)


def ortho(m):  # 拡大縮小を除いた回転だけ
    u, _, vt = np.linalg.svd(m); r = u @ vt
    if np.linalg.det(r) < 0: u[:, -1] *= -1; r = u @ vt
    return r


# ---------- BVH ----------
class BVH:
    def __init__(self, path):
        tok = open(path).read().split()
        self.names, self.parent, self.offset, self.chans = [], [], [], []
        i, stack = 0, []
        while tok[i] != "MOTION":
            t = tok[i]
            if t in ("ROOT", "JOINT"):
                self.names.append(tok[i + 1]); self.parent.append(stack[-1] if stack else -1); stack.append(len(self.names) - 1)
                self.offset.append(None); self.chans.append([]); i += 2
            elif t == "End":
                stack.append(None); i += 2
            elif t == "OFFSET":
                if stack[-1] is not None: self.offset[stack[-1]] = np.array([float(x) for x in tok[i + 1:i + 4]])
                i += 4
            elif t == "CHANNELS":
                n = int(tok[i + 1]); self.chans[stack[-1]] = tok[i + 2:i + 2 + n]; i += 2 + n
            elif t == "}":
                stack.pop(); i += 1
            else:
                i += 1
        nf = int(tok[i + 2]); self.dt = float(tok[i + 5]); vals = np.array(tok[i + 6:], dtype=float)
        self.data = vals.reshape(nf, -1)
        self.idx = {n: k for k, n in enumerate(self.names)}

    def fk(self, f):
        """コマ f の、骨ごとの世界の回転 (3x3) と位置"""
        row, c = self.data[f], 0
        R, P = [None] * len(self.names), [None] * len(self.names)
        for j, ch in enumerate(self.chans):
            pos, rot = self.offset[j].copy(), np.eye(3)
            for name in ch:
                v = row[c]; c += 1
                if name.endswith("position"): pos[{"X": 0, "Y": 1, "Z": 2}[name[0]]] += v
                else: rot = rot @ rot_axis(name[0], v)
            p = self.parent[j]
            if p < 0: R[j], P[j] = rot, pos
            else: R[j], P[j] = R[p] @ rot, P[p] + R[p] @ pos
        return R, P


# ---------- glb ----------
def read_glb(path):
    b = open(path, "rb").read()
    L = struct.unpack("<I", b[12:16])[0]; j = json.loads(b[20:20 + L])
    o = 20 + L; L2 = struct.unpack("<I", b[o:o + 4])[0]
    return j, b[o + 8:o + 8 + L2]


def write_glb(path, j, binary):
    js = json.dumps(j, ensure_ascii=False, separators=(",", ":")).encode("utf-8")
    js += b" " * ((4 - len(js) % 4) % 4); binary += b"\0" * ((4 - len(binary) % 4) % 4)
    out = struct.pack("<III", 0x46546C67, 2, 12 + 8 + len(js) + 8 + len(binary))
    out += struct.pack("<II", len(js), 0x4E4F534A) + js + struct.pack("<II", len(binary), 0x004E4942) + binary
    open(path, "wb").write(out)


class Rig:
    """glb の骨組み (rig のいちばん上の節の中の座標。メートル)"""
    def __init__(self, j):
        self.j, N = j, j["nodes"]
        self.idx = {n.get("name"): i for i, n in enumerate(N)}
        self.parent = [-1] * len(N)
        for i, n in enumerate(N):
            for c in n.get("children", []): self.parent[c] = i
        self.root = j["scenes"][j.get("scene", 0)]["nodes"][0]
        self.order = []
        def walk(i):
            self.order.append(i)
            for c in N[i].get("children", []): walk(c)
        walk(self.root)
        self.T = {i: np.array(N[i].get("translation", [0, 0, 0]), float) for i in self.order}
        self.Rl = {i: quat_to_mat(N[i].get("rotation", [0, 0, 0, 1])) for i in self.order}
        self.S = {i: np.array(N[i].get("scale", [1, 1, 1]), float) for i in self.order}
        self.Wr, self.Wp = {}, {}
        self.fk_into(self.Rl, self.Wr, self.Wp)

    def fk_into(self, Rl, Wr, Wp, hips_t=None):
        for i in self.order:
            p = self.parent[i]
            t = hips_t if (hips_t is not None and i == self.hips) else self.T[i]
            if i == self.root: Wr[i], Wp[i] = np.eye(3), np.zeros(3)
            else: Wr[i], Wp[i] = Wr[p] @ Rl[i], Wp[p] + Wr[p] @ (t * self.Sw(p))
        return Wr, Wp

    def Sw(self, i):  # 親までの拡大縮小 (どれもほぼ 1)
        s = np.ones(3)
        while i >= 0 and i in self.S: s = s * self.S[i]; i = self.parent[i]
        return s

    @property
    def hips(self): return self.idx["J_Bip_C_Hips"]


def heading(v):  # xz 面の向き (+z が 0、+x が正)
    return math.atan2(v[0], v[2])


def analyze(bvh_dir, cid):
    B = BVH(os.path.join(bvh_dir, f"{int(cid.split('_')[0]):03d}", cid + ".bvh"))
    R0, P0 = B.fk(0); h = B.idx["Hips"]; hh = P0[h][1] - min(P0[B.idx["LeftToeBase"]][1], P0[B.idx["RightToeBase"]][1])
    n = len(B.data); print(f"{cid}: {n} コマ ({(n - 1) / FPS_IN:.1f} 秒)  腰の高さ (T ポーズ) {hh:.2f}")
    prev = None
    for f in range(1, n, FPS_IN // 2):
        R, P = B.fk(f)
        lo = min(P[k][1] for k in range(len(P)))
        fwd = R[h] @ np.array([0, 0, 1.0])
        sp = 0 if prev is None else np.linalg.norm((P[h] - prev)[[0, 2]]) * 2 / hh
        prev = P[h]
        hand = max(P[B.idx["LeftHand"]][1], P[B.idx["RightHand"]][1])
        print(f"  {(f - 1) / FPS_IN:5.1f}s 腰 {(P[h][1] - lo) / hh:4.2f} 速さ {sp:4.2f} 向き {math.degrees(heading(fwd)):6.0f} 手の高い方 {(hand - lo) / hh:4.2f}"
              f" 足L {(P[B.idx['LeftToeBase']][1] - lo) / hh:4.2f} R {(P[B.idx['RightToeBase']][1] - lo) / hh:4.2f}")


def bake_clip(rig, B, spec, finger_rl, src_scale):
    """1 つの動きを焼く。返り値: (コマ数 × 骨) の局所回転 (四元数)、腰の位置、長さ、速さ"""
    a, b = int(spec["t"][0] * FPS_IN) + 1, min(len(B.data) - 1, int(spec["t"][1] * FPS_IN) + 1)
    frames = list(range(a, b + 1, STEP))
    R0, _ = B.fk(0)
    src = [B.fk(f) for f in frames]
    h = B.idx["Hips"]
    hp = np.array([P[h] for _, P in src])
    if spec.get("loop"):  # つながりのよい 1 周を探す (骨の回り方の差が小さい 2 コマ)
        feat = np.array([np.concatenate([(R[B.idx[k]] @ R0[B.idx[k]].T).ravel() for k in MAP if k != "Hips"]
                                        + [(R[h] @ R0[h].T)[:, 1]]) for R, _ in src])
        lo, hi = int(spec["loop"][0] * FPS), int(spec["loop"][1] * FPS)
        best = None
        for i in range(len(src)):
            for k in range(i + lo, min(len(src), i + hi + 1)):
                d = np.sum((feat[i] - feat[k]) ** 2)
                if best is None or d < best[0]: best = (d, i, k)
        _, i, k = best
        src, hp, frames = src[i:k + 1], hp[i:k + 1], frames[i:k + 1]
    dur = (len(src) - 1) / FPS
    # 向き: 前 (+z) にそろえる角度
    fw = lambda R: heading(R[h] @ R0[h].T @ np.array([0, 0, 1.0]))
    if spec["face"] == "travel": psi = heading(hp[-1] - hp[0])
    elif spec["face"] == "start": psi = fw(src[0][0])
    elif spec["face"] == "end": psi = fw(src[-1][0])
    else: psi = math.atan2(np.mean([math.sin(fw(R)) for R, _ in src]), np.mean([math.cos(fw(R)) for R, _ in src]))
    # BVH の +z (前) を、glb の rig の前 (-z) へ: y のまわりに (180° - psi)
    Yc = rot_axis("Y", 180.0 - math.degrees(psi)); A = rot_axis("Y", 180.0)
    speed = 0.0
    if spec.get("speed"):
        speed = np.sum(np.linalg.norm(np.diff(hp[:, [0, 2]], axis=0), axis=1)) / max(dur, 1e-6) * src_scale
    # 骨ごとの局所回転
    tgt = {rig.idx[MAP[k]]: B.idx[k] for k in MAP if MAP[k] in rig.idx}
    Q, HT = [], []
    feet = [rig.idx[n] for n in rig.idx if n and (n.endswith("_Foot") or "ToeBase" in n) and n.startswith("J_Bip")]
    extra = {"J_Bip_C_Hips": 0.10, "J_Bip_C_Head": 0.10, "J_Bip_C_UpperChest": 0.10, "J_Bip_C_Chest": 0.10,
             "J_Bip_L_LowerLeg": 0.05, "J_Bip_R_LowerLeg": 0.05, "J_Bip_L_LowerArm": 0.04, "J_Bip_R_LowerArm": 0.04,
             "J_Bip_L_Hand": 0.03, "J_Bip_R_Hand": 0.03, "J_Bip_L_UpperArm": 0.05, "J_Bip_R_UpperArm": 0.05}
    pts = [(i, rig.Wp[i][1]) for i in feet]  # 足とつま先: T ポーズの高さを地面からのはなれに
    pts += [(rig.idx[n], c) for n, c in extra.items() if n in rig.idx]
    offs = []
    for R, _ in src:
        Rl, Wr, Wp = {}, {}, {}
        for i in rig.order:
            p = rig.parent[i]
            if i == rig.root: Wr[i] = np.eye(3); Rl[i] = rig.Rl[i]; continue
            if i in tgt:
                s = tgt[i]
                Dw = Yc @ (R[s] @ R0[s].T) @ A.T  # T ポーズからの世界での回り方 (BVH の素の向き +z を rig の -z へ写し、動きの向きを前に)
                W = Dw @ rig.Wr[i]
                Rl[i] = ortho(Wr[p].T @ W)
            elif i in finger_rl: Rl[i] = finger_rl[i]
            else: Rl[i] = rig.Rl[i]
            Wr[i] = Wr[p] @ Rl[i]
        rig.fk_into(Rl, Wr, Wp)
        lowest = min(Wp[i][1] - c for i, c in pts)
        offs.append(-lowest)
        Q.append({i: mat_to_quat(Rl[i]) for i in list(tgt) + list(finger_rl)})
    offs = np.array(offs)
    k = 3  # 地面の高さのゆれを少しならす
    sm = np.array([offs[max(0, f - k):f + k + 1].mean() for f in range(len(offs))])
    if spec.get("loop"): sm[:] = sm.mean() + (offs - offs.mean()) * 0.6  # 歩く 1 周: 上下のゆれを少し残す
    T0 = rig.T[rig.hips]
    for f in range(len(Q)): HT.append(T0 + np.array([0, sm[f], 0]) / rig.Sw(rig.parent[rig.hips]))
    return Q, HT, dur, speed


def finger_curl(rig, deg=22.0):
    """指を少し曲げた形 (手のひら側へ)。T ポーズの手のひらは下向き、rig は -z を向く"""
    out = {}
    for n, i in rig.idx.items():
        if not n or not n.startswith("J_Bip_") or "_end" in n: continue
        side = n.split("_")[2]
        if not any(f in n for f in ("Index", "Middle", "Ring", "Little", "Thumb")): continue
        k = int(n[-1]) if n[-1].isdigit() else 1
        ang = deg * (0.6 if "Thumb" in n else 1.0) * (1.25 if k == 2 else 1.0)
        # 左手は -x、右手は +x を指す。手のひら側 (-y) へ曲げるのは、左は z のまわりに +、右は -
        axis_deg = ang if side == "L" else -ang
        C = rot_axis("Z", axis_deg) if "Thumb" not in n else rot_axis("Y", -axis_deg * 0.8)
        Wr = rig.Wr[i]
        out[i] = rig.Rl[i] @ (Wr.T @ C @ Wr)
    return out


def _to_lin(c): c = np.asarray(c, float); return np.where(c <= 0.04045, c / 12.92, ((c + 0.055) / 1.055) ** 2.4)
def _to_srgb(c): c = np.clip(np.asarray(c, float), 0, 1); return np.where(c <= 0.0031308, c * 12.92, 1.055 * c ** (1 / 2.4) - 0.055)
def _hex(h): h = h.lstrip("#"); return np.array([int(h[i:i + 2], 16) / 255 for i in (0, 2, 4)])


def bake_colors(j, P):
    """Blender の材質の中の色の計算 (glTF に書き出せないもの) を、画像に焼きこむしかた。画像の番号 → 関数。
    アプリの絵 (replay3d_people.js) は、画像の色をそのまま出し、画像のある材質の色の係数は変換しないので、係数は 1 にして画像に入れる"""
    H, Ls, I = P["hair"], P["lines"], P["iris"]
    tex_img = lambda m: j["textures"][m["pbrMetallicRoughness"]["baseColorTexture"]["index"]]["source"]
    jobs = {}
    for m in j.get("materials", []):
        nm, pbr = m.get("name", ""), m.setdefault("pbrMetallicRoughness", {})
        has_tex = "baseColorTexture" in pbr
        if "braid" in nm:  # 三つ編み: 髪の 2 色のなか (Blender ではノイズのむら)
            pbr["baseColorFactor"] = [*map(float, _to_lin(_to_srgb(_to_lin(_hex(H["dark"])) * 0.5 + _to_lin(_hex(H["light"])) * 0.5))), 1.0]
        elif "HAIR" in nm and has_tex:  # 髪: 明るさだけを使い、dark〜light の間に
            lo, hi = H.get("ramp_lo", 0.35), H.get("ramp_hi", 1.0)
            for key, rr in H.get("ramp_mat", {}).items():
                if key in nm: lo, hi = rr
            d, l = _to_lin(_hex(H["dark"])), _to_lin(_hex(H["light"]))
            def f(rgb, lo=lo, hi=hi, d=d, l=l):
                bw = _to_lin(rgb) @ np.array([0.2126, 0.7152, 0.0722])
                t = np.clip((bw - lo) / max(hi - lo, 1e-6), 0, 1)[..., None]
                return _to_srgb(d + (l - d) * t)
            jobs[tex_img(m)] = f; pbr.pop("baseColorFactor", None)
        elif "EyeIris" in nm and has_tex:  # 虹彩: 色をうすめて (彩度・明るさ) 色を掛ける
            tint = _hex(I["tint"])
            def f(rgb, tint=tint):
                g = rgb.mean(axis=-1, keepdims=True)
                x = (g + (rgb - g) * I["sat"]) * I["val"]
                return np.clip(x * tint, 0, 1)
            jobs[tex_img(m)] = f; pbr.pop("baseColorFactor", None)
        elif "EyeWhite" in nm and has_tex:
            jobs[tex_img(m)] = lambda rgb: rgb * _hex("#e8dcd8"); pbr.pop("baseColorFactor", None)
        else:
            for key, col in (("FaceBrow", "brow"), ("FaceEyeline", "eyeline"), ("FaceEyelash", "lash")):
                if key in nm and has_tex:  # 線: 線の色そのもの (形は画像の透明度)
                    c = _hex(Ls[col]); jobs[tex_img(m)] = lambda rgb, c=c: np.broadcast_to(c, rgb.shape).copy(); pbr.pop("baseColorFactor", None)
        m.pop("emissiveFactor", None); m.pop("emissiveTexture", None)  # 目の光り (弱い) は使わない
    return jobs


def slim_materials(j, binary, tex, P=None):
    """拡張をはずし、色を画像に焼きこみ、画像を縮める。新しいバイナリと bufferViews を作り直す"""
    from PIL import Image
    jobs = bake_colors(j, P) if P else {}
    for m in j.get("materials", []):
        ex = m.get("extensions", {})
        for k in ("KHR_materials_clearcoat", "KHR_materials_sheen", "KHR_materials_specular"): ex.pop(k, None)
        if not ex: m.pop("extensions", None)
    j["extensionsUsed"] = [e for e in j.get("extensionsUsed", []) if e == "KHR_materials_unlit"]
    if not j["extensionsUsed"]: j.pop("extensionsUsed")
    j.pop("extensionsRequired", None)
    img_views = {im["bufferView"]: k for k, im in enumerate(j.get("images", [])) if "bufferView" in im}
    out = bytearray()
    for vi, bv in enumerate(j["bufferViews"]):
        o = bv.get("byteOffset", 0); data = binary[o:o + bv["byteLength"]]
        if vi in img_views:
            I = Image.open(io.BytesIO(data)); k = img_views[vi]; changed = False
            if tex and max(I.size) > tex:
                s = tex / max(I.size); I = I.resize((max(1, round(I.size[0] * s)), max(1, round(I.size[1] * s))), Image.LANCZOS); changed = True
            if k in jobs:
                I = I.convert("RGBA"); a = np.asarray(I, dtype=np.float64) / 255
                rgb = jobs[k](a[..., :3]); a = np.concatenate([rgb, a[..., 3:]], axis=-1)
                I = Image.fromarray(np.round(np.clip(a, 0, 1) * 255).astype(np.uint8), "RGBA"); changed = True
            if changed:
                buf = io.BytesIO(); I.save(buf, "PNG", optimize=True); data = buf.getvalue()
                j["images"][k]["mimeType"] = "image/png"
        while len(out) % 4: out.append(0)
        bv["byteOffset"] = len(out); bv["byteLength"] = len(data); out += data
    return out


def add_accessor(j, out, arr, typ, minmax=False):
    while len(out) % 4: out.append(0)
    arr = np.ascontiguousarray(arr, dtype=np.float32)
    j["bufferViews"].append({"buffer": 0, "byteOffset": len(out), "byteLength": arr.nbytes})
    out += arr.tobytes()
    acc = {"bufferView": len(j["bufferViews"]) - 1, "componentType": 5126, "count": int(arr.shape[0]), "type": typ}
    if minmax: acc["min"] = [float(x) for x in np.atleast_1d(arr.min(axis=0))]; acc["max"] = [float(x) for x in np.atleast_1d(arr.max(axis=0))]
    j["accessors"].append(acc)
    return len(j["accessors"]) - 1


def build_person(fname, args, clips, bvhs):
    j, binary = read_glb(os.path.join(args.src, f"{fname}_vroid.glb"))
    rig = Rig(j)
    fingers = finger_curl(rig)
    # 大きさの比: 腰の高さ (メートル) / BVH の腰の高さ
    hip_h = rig.Wp[rig.hips][1] - min(rig.Wp[rig.idx[n]][1] for n in ("J_Bip_L_ToeBase", "J_Bip_R_ToeBase"))
    import sys
    sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
    from people import VROID  # 髪・目・線の色 (build_person_vroid.py と同じ設定)
    out = slim_materials(j, binary, args.tex, VROID.get(fname))
    j["animations"] = []
    info = {}
    for name, spec in clips.items():
        B = bvhs[spec["bvh"]]
        _, P0 = B.fk(0)
        src_h = P0[B.idx["Hips"]][1] - min(P0[B.idx["LeftToeBase"]][1], P0[B.idx["RightToeBase"]][1])
        Q, HT, dur, speed = bake_clip(rig, B, spec, fingers, hip_h / src_h)
        times = np.arange(len(Q), dtype=np.float32) / FPS
        ti = add_accessor(j, out, times, "SCALAR", minmax=True)
        samplers, channels = [], []
        for node in Q[0]:
            q = np.array([Q[f][node] for f in range(len(Q))])
            for f in range(1, len(q)):  # 四元数の符号をそろえる (補間で遠回りしない)
                if np.dot(q[f], q[f - 1]) < 0: q[f] = -q[f]
            samplers.append({"input": ti, "output": add_accessor(j, out, q, "VEC4"), "interpolation": "LINEAR"})
            channels.append({"sampler": len(samplers) - 1, "target": {"node": node, "path": "rotation"}})
        samplers.append({"input": ti, "output": add_accessor(j, out, np.array(HT), "VEC3"), "interpolation": "LINEAR"})
        channels.append({"sampler": len(samplers) - 1, "target": {"node": rig.hips, "path": "translation"}})
        j["animations"].append({"name": name, "samplers": samplers, "channels": channels})
        info[name] = {"sec": round(dur, 3), "speed": round(float(speed), 3), "src": spec["bvh"], "range": [round(spec["t"][0], 2), round(spec["t"][1], 2)]}
        print(f"  {fname} {name}: {spec['bvh']} {len(Q)} コマ {dur:.2f} 秒 速さ {speed:.2f} m/秒", flush=True)
    # 指の形は、素の姿勢にも入れる (動きの外でも曲がっているように)
    for i, R in fingers.items(): j["nodes"][i]["rotation"] = [float(x) for x in mat_to_quat(R)]
    # +z を向かせる (rig のいちばん上の節を y のまわりに 180°)
    j["nodes"][rig.root]["rotation"] = [0.0, 1.0, 0.0, 0.0]
    j["buffers"] = [{"byteLength": len(out)}]
    j.setdefault("asset", {})["generator"] = "retarget_cmu.py (motion: CMU Graphics Lab Motion Capture Database, mocap.cs.cmu.edu)"
    os.makedirs(args.out, exist_ok=True)
    write_glb(os.path.join(args.out, f"{fname}.glb"), j, bytes(out))
    meta = {"clips": info, "fps": FPS, "credit": "Motion: CMU Graphics Lab Motion Capture Database (mocap.cs.cmu.edu)"}
    json.dump(meta, open(os.path.join(args.out, f"{fname}.json"), "w"), ensure_ascii=False, indent=1)
    print(f"→ {fname}.glb {os.path.getsize(os.path.join(args.out, fname + '.glb')) / 1e6:.1f} MB", flush=True)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--bvh", required=True, help="BVH の data フォルダ (<3 桁>/<id>.bvh)")
    ap.add_argument("--src", default="/dev/shm/sena")
    ap.add_argument("--out", default="/dev/shm/people_glb")
    ap.add_argument("--only", default="")
    ap.add_argument("--tex", type=int, default=1024)
    ap.add_argument("--analyze", default="")
    args = ap.parse_args()
    if args.analyze:
        for cid in args.analyze.split(","): analyze(args.bvh, cid)
        return
    clips = {k: dict(v) for k, v in CLIPS.items()}
    bvhs = {}
    for spec in clips.values():
        cid = spec["bvh"]
        if cid not in bvhs: bvhs[cid] = BVH(os.path.join(args.bvh, f"{int(cid.split('_')[0]):03d}", cid + ".bvh"))
    for name, f in FILES.items():
        if args.only and f not in args.only.split(","): continue
        if not os.path.exists(os.path.join(args.src, f + "_vroid.glb")): continue  # まだ作っていない人は飛ばす
        print(f"{name} ({f})", flush=True)
        build_person(f, args, clips, bvhs)


if __name__ == "__main__":
    main()
