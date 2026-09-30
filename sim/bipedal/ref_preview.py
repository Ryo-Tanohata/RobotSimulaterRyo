"""お手本 (reference.py) を物理なしで再生した動画と、1 周期の連続写真を作る (関節の向きの確認用)。
  MUJOCO_GL=egl ~/mjx/venv/bin/python sim/bipedal/ref_preview.py out.mp4 [--s 1.0]
"""
import argparse

import mediapy
import mujoco
import numpy as np

from body import actuated_joints, model_xml
from reference import FREQ, reference

ap = argparse.ArgumentParser()
ap.add_argument("out")
ap.add_argument("--s", type=float, default=1.0)
ap.add_argument("--speed", type=float, default=0.8)
a = ap.parse_args()

m = mujoco.MjModel.from_xml_string(model_xml([(a.s, "", (0, 0, 0))], with_actuators=False))
d = mujoco.MjData(m)
qadr = [m.jnt_qposadr[m.joint(n).id] for n in actuated_joints()]
feet = [m.geom(f"{s}_foot").id for s in "lr"]
r = mujoco.Renderer(m, 480, 854)
cam = mujoco.MjvCamera()
cam.distance, cam.azimuth, cam.elevation = 3.2, 90, -8  # 真横から
fps, frames = 30, []
for i in range(int(3 * fps)):
    t = i / fps
    d.qpos[:] = 0
    d.qpos[3] = 1  # 向き (四元数) はそのまま
    d.qpos[qadr] = np.array(reference((FREQ * t) % 1.0))
    d.qpos[2] = 2.0
    mujoco.mj_forward(m, d)
    d.qpos[2] -= min(d.geom_xpos[k][2] - m.geom_size[k][2] for k in feet)  # 低いほうの足を床に
    d.qpos[0] = a.speed * t
    mujoco.mj_forward(m, d)
    cam.lookat[:] = (d.qpos[0], 0, 0.6)
    r.update_scene(d, cam)
    frames.append(r.render())
mediapy.write_video(a.out, frames, fps=fps)
print("→", a.out)
