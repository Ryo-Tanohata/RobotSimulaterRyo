"""体のモデルの確認: 5 段階それぞれ、関節を今の角度に保つ力だけで 2 秒間物理を進め、壊れない (値が発散しない) かを見る。
  ~/mjx/venv/bin/python sim/bipedal/check_body.py
"""
import mujoco
import numpy as np

from body import model_xml

for s in (0, 0.25, 0.5, 0.75, 1):
    m = mujoco.MjModel.from_xml_string(model_xml([(s, "", (0, 0, 1.2))]))
    d = mujoco.MjData(m)
    mass = m.body_subtreemass[1]
    for _ in range(int(2 / m.opt.timestep)):
        mujoco.mj_step(m, d)
    ok = np.all(np.isfinite(d.qpos))
    print(f"s={s:4.2f}  体重 {mass:.1f} kg  関節 {m.nu}  2 秒後の骨盤の高さ {d.qpos[2]:.2f} m  {'OK' if ok else '発散'}")
