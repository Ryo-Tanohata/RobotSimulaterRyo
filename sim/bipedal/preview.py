"""5 段階の体を横に並べた画像を作る (物理は進めず、立った姿勢で表示するだけ)。
  MUJOCO_GL=egl ~/mjx/venv/bin/python sim/bipedal/preview.py out.png
"""
import sys

import mujoco
import numpy as np
from PIL import Image, ImageDraw, ImageFont

from body import model_xml, shape

S = (0, 0.25, 0.5, 0.75, 1)
GAP = 0.9


def main(out):
    bodies = [(s, f"b{i}_", (0, (i - 2) * -GAP, 1.2)) for i, s in enumerate(S)]
    model = mujoco.MjModel.from_xml_string(model_xml(bodies, with_actuators=False))
    data = mujoco.MjData(model)
    # 関節は範囲の中で 0 に一番近い角度 (膝を伸ばしきれない体は少し曲がる)
    for j in range(model.njnt):
        if model.jnt_type[j] == mujoco.mjtJoint.mjJNT_HINGE:
            lo, hi = model.jnt_range[j]
            data.qpos[model.jnt_qposadr[j]] = np.clip(0, lo, hi)
    mujoco.mj_forward(model, data)
    # 足の裏が床に着く高さにそろえる
    for i in range(len(S)):
        g = [mujoco.mj_name2id(model, mujoco.mjtObj.mjOBJ_GEOM, f"b{i}_{side}_foot") for side in "lr"]
        low = min(data.geom_xpos[k][2] - model.geom_size[k][2] for k in g)
        adr = model.jnt_qposadr[mujoco.mj_name2id(model, mujoco.mjtObj.mjOBJ_JOINT, f"b{i}_root")]
        data.qpos[adr + 2] -= low
    mujoco.mj_forward(model, data)

    model.vis.global_.fovy = 18
    r = mujoco.Renderer(model, 700, 1600)
    cam = mujoco.MjvCamera()
    cam.lookat[:] = (0, 0, 0.7)
    cam.distance, cam.azimuth, cam.elevation = 13, 165, -6  # 遠くから狭い画角で (遠近で大きさが変わって見えないように)
    r.update_scene(data, cam)
    img = Image.fromarray(r.render())

    d = ImageDraw.Draw(img)
    font = ImageFont.load_default()
    for f in ("/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc", "/mnt/c/Windows/Fonts/meiryo.ttc", "/mnt/c/Windows/Fonts/YuGothM.ttc"):
        try:
            font = ImageFont.truetype(f, 26)
            break
        except OSError:
            pass
    # 各体の頭の上の画面位置に、s と腕÷脚の値を書く
    r.update_scene(data, cam)
    for i, s in enumerate(S):
        head = data.xpos[mujoco.mj_name2id(model, mujoco.mjtObj.mjOBJ_BODY, f"b{i}_head")] + (0, 0, 0.25)
        x, y = project(r, cam, model, data, head, img.size)
        d.text((x, y), f"s = {s}\n腕÷脚 {shape(s).imi:.0f}", font=font, fill=(20, 20, 20), anchor="md", align="center")
    img.save(out)
    print("→", out)


def project(r, cam, model, data, p, size):
    """3 次元の点 → 画像の座標 (カメラの位置と向きから計算)"""
    scn = r.scene
    c = scn.camera[0]
    pos = np.array(c.pos)
    fwd = np.array(c.forward)
    up = np.array(c.up)
    right = np.cross(fwd, up)
    v = np.array(p) - pos
    z = v @ fwd
    fovy = np.deg2rad(model.vis.global_.fovy)
    w, h = size
    f = (h / 2) / np.tan(fovy / 2)
    return w / 2 + f * (v @ right) / z, h / 2 - f * (v @ up) / z


if __name__ == "__main__":
    main(sys.argv[1] if len(sys.argv) > 1 else "bodies.png")
