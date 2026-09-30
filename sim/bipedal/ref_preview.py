"""お手本 (reference.py) を物理なしで再生した動画と、1 周期の連続写真を作る (関節の向きの確認用)。
  MUJOCO_GL=egl ~/mjx/venv/bin/python sim/bipedal/ref_preview.py out.mp4 [--s 1.0]
"""
import argparse

import mediapy
import mujoco
import numpy as np

from body import actuated_joints, model_xml
from env import _lowest
from reference import make

ap = argparse.ArgumentParser()
ap.add_argument("out")
ap.add_argument("--s", type=float, default=1.0)
ap.add_argument("--speed", type=float, default=0.8)
ap.add_argument("--gait", default="biped", choices=["biped", "quad"])
ap.add_argument("--exp2", action="store_true", help="実験 2 のお手本 (体に合わせる)")
a = ap.parse_args()

m = mujoco.MjModel.from_xml_string(model_xml([(a.s, "", (0, 0, 0))], with_actuators=False))
d = mujoco.MjData(m)
qadr = [m.jnt_qposadr[m.joint(n).id] for n in actuated_joints()]
ref, freq, pitch = make(a.gait, a.s, scaled=a.exp2)
contacts = [m.geom(f"{x}_{y}").id for x in "lr" for y in ("foot", "hand")]
jids = [m.joint(n).id for n in actuated_joints()]
r = mujoco.Renderer(m, 480, 854)
cam = mujoco.MjvCamera()
cam.distance, cam.azimuth, cam.elevation = 3.2, 90, -8  # 真横から
fps, frames = 30, []
for i in range(int(3 * fps)):
    t = i / fps
    d.qpos[:] = 0
    d.qpos[3:7] = (np.cos(np.radians(pitch) / 2), 0, np.sin(np.radians(pitch) / 2), 0)  # 胴体を前へ倒す (4 足)
    d.qpos[qadr] = np.clip(np.array(ref((freq * t) % 1.0)), m.jnt_range[jids, 0], m.jnt_range[jids, 1])
    d.qpos[2] = 2.0
    mujoco.mj_forward(m, d)
    d.qpos[2] -= min(_lowest(m, d, g) for g in contacts)  # 一番低い手足を床に
    d.qpos[0] = a.speed * t
    mujoco.mj_forward(m, d)
    cam.lookat[:] = (d.qpos[0], 0, 0.6)
    r.update_scene(d, cam)
    frames.append(r.render())
mediapy.write_video(a.out, frames, fps=fps)
print("→", a.out)
