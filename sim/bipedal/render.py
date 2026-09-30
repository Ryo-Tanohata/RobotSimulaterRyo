"""学習した脳で 1 体を動かし、棒人間の動画 (mp4) にする。
  MUJOCO_GL=egl ~/mjx/venv/bin/python sim/bipedal/render.py 名前 out.mp4 [--s 1.0] [--seconds 8]
"""
import argparse
from pathlib import Path

import jax
import mediapy
import mujoco
import numpy as np
from brax.training.acme import running_statistics
from brax.training.agents.ppo import checkpoint
from brax.training.agents.ppo import networks as ppo_networks

from env import ApeWalk, default_config

ap = argparse.ArgumentParser()
ap.add_argument("name")
ap.add_argument("out")
ap.add_argument("--s", type=float, default=1.0)
ap.add_argument("--seconds", type=float, default=8)
a = ap.parse_args()

ckdir = Path(__file__).parent / "runs" / a.name / "checkpoints"
last = sorted((p for p in ckdir.iterdir() if p.name.isdigit()), key=lambda p: int(p.name))[-1]
print("脳:", last)
cfg = default_config()
cfg.s = a.s
env = ApeWalk(cfg)
# brax の load_policy は今の版では設定の読み込みで失敗するので、train.py と同じ形の脳を作って重みだけ読み込む
params = checkpoint.load(str(last.resolve()))
net = ppo_networks.make_ppo_networks(env.observation_size, env.action_size,
                                     preprocess_observations_fn=running_statistics.normalize,
                                     policy_hidden_layer_sizes=(256, 256, 128), value_hidden_layer_sizes=(256, 256, 256))
policy = jax.jit(ppo_networks.make_inference_fn(net)(params, deterministic=True))
reset, step = jax.jit(env.reset), jax.jit(env.step)
state = reset(jax.random.PRNGKey(0))
rng = jax.random.PRNGKey(1)
qs, fell_at = [], None
for i in range(int(a.seconds / env.dt)):
    rng, k = jax.random.split(rng)
    act, _ = policy(state.obs, k)
    state = step(state, act)
    qs.append(np.array(state.data.qpos))
    if state.done and fell_at is None:
        fell_at = i * env.dt
        break

m = env.mj_model
d = mujoco.MjData(m)
r = mujoco.Renderer(m, 480, 854)
cam = mujoco.MjvCamera()
cam.distance, cam.azimuth, cam.elevation = 3.5, 110, -12
frames = []
for q in qs:
    d.qpos[:] = q
    mujoco.mj_forward(m, d)
    cam.lookat[:] = (q[0], q[1], 0.7)
    r.update_scene(d, cam)
    frames.append(r.render())
mediapy.write_video(a.out, frames, fps=round(1 / env.dt))
dist = qs[-1][0] - qs[0][0]
print(f"{len(qs) * env.dt:.1f} 秒, 前へ {dist:.2f} m, {'転倒 ' + format(fell_at, '.1f') + ' 秒' if fell_at is not None else '転ばず'} → {a.out}")
