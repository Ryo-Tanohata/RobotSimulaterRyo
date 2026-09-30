"""学習した歩き方 (人型 human2) から、1 周期ぶんの関節角を書き出す (3D 再生の棒人間を動かすため)。
  ~/mjx/venv/bin/python sim/bipedal/export_walk.py h2_s1 ../society/app/walk_cycle.json [--cmd 1.0]
書き出すもの: 各コマの関節角 (rad、MuJoCo の向き)、骨盤の高さの上下、骨盤の前後の傾き。
"""
import argparse
import json
import math
from pathlib import Path

import jax
import numpy as np
from brax.training.acme import running_statistics
from brax.training.agents.ppo import checkpoint
from brax.training.agents.ppo import networks as ppo_networks

from body import actuated_joints
from env import ApeWalk, default_config
from reference import human2_freq

ap = argparse.ArgumentParser()
ap.add_argument("name")
ap.add_argument("out")
ap.add_argument("--cmd", type=float, default=1.0)
a = ap.parse_args()

run = Path(__file__).parent / "runs" / a.name
cfg = default_config()
for k, v in json.loads((run / "config.json").read_text()).items():
    if k in cfg:
        cfg[k] = v
cfg.speed_lo = cfg.speed_hi = a.cmd
env = ApeWalk(cfg)
last = sorted((p for p in (run / "checkpoints").iterdir() if p.name.isdigit()), key=lambda p: int(p.name))[-1]
params = checkpoint.load(str(last.resolve()))
net = ppo_networks.make_ppo_networks(env.observation_size, env.action_size, preprocess_observations_fn=running_statistics.normalize,
                                     policy_hidden_layer_sizes=(256, 256, 128), value_hidden_layer_sizes=(256, 256, 256))
policy = jax.jit(ppo_networks.make_inference_fn(net)(params, deterministic=True))
reset, step = jax.jit(env.reset), jax.jit(env.step)
state = reset(jax.random.PRNGKey(0))
key = jax.random.PRNGKey(1)
frames = []
for i in range(int(6 / env.dt)):
    act, _ = policy(state.obs, key)
    state = step(state, act)
    frames.append((float(state.info["phase"]), np.array(state.data.qpos)))

# 最後の 1 周期 (位相が 0 をまたいでから次に 0 をまたぐまで)
period = 1 / float(human2_freq(a.cmd))
n = round(period / env.dt)
cyc = frames[-n:]
m = env.mj_model
names = actuated_joints()
qadr = [int(m.jnt_qposadr[m.joint(j).id]) for j in names]
z0 = float(np.mean([q[2] for _, q in cyc]))
out = {"names": names, "dt": env.dt, "speed": a.cmd, "period": period, "frames": []}
for ph, q in cyc:
    w, x, y, z = q[3:7]
    pitch = math.asin(max(-1, min(1, 2 * (w * y - z * x))))  # 前へ倒れると +
    out["frames"].append({"q": [round(float(q[i]), 4) for i in qadr], "bob": round(float(q[2]) - z0, 4), "pitch": round(pitch, 4)})
Path(a.out).write_text(json.dumps(out, separators=(",", ":")), encoding="utf-8")
print(f"{len(out['frames'])} コマ (1 周期 {period:.2f} 秒) → {a.out}")
