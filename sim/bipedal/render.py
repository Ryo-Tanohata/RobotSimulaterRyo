"""学習した脳で 1 体を動かし、棒人間の動画 (mp4) にする。
  MUJOCO_GL=egl ~/mjx/venv/bin/python sim/bipedal/render.py 名前 out.mp4 [--s 1.0] [--seconds 8]
"""
import argparse
import json
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
ap.add_argument("--cmd", type=float, default=None, help="gait=human2 の目標の速さ (m/s)。省略すると学習と同じく毎回ランダム")
ap.add_argument("--near", action="store_true", help="カメラを近づける")
a = ap.parse_args()

ckdir = Path(__file__).parent / "runs" / a.name / "checkpoints"
# 新しい順に読み込めるものを探す (時間切れで止めたとき、最後の保存が途中の場合があるため)
params = last = None
for p in sorted((p for p in ckdir.iterdir() if p.name.isdigit()), key=lambda p: int(p.name), reverse=True):
    try:
        params = checkpoint.load(str(p.resolve()))
        last = p
        break
    except Exception as e:  # noqa: BLE001
        print("読み込めない:", p.name, type(e).__name__)
print("脳:", last)
cfg = default_config()
cfg.s = a.s
cj = ckdir.parent / "config.json"
if cj.exists():  # 学習したときの設定 (お手本の有無など) に合わせる
    for k, v in json.loads(cj.read_text()).items():
        if k in cfg:
            cfg[k] = v
if a.cmd is not None:
    cfg.speed_lo = cfg.speed_hi = a.cmd
env = ApeWalk(cfg)
# brax の load_policy は今の版では設定の読み込みで失敗するので、train.py と同じ形の脳を作って重みだけ読み込む
net = ppo_networks.make_ppo_networks(env.observation_size, env.action_size,
                                     preprocess_observations_fn=running_statistics.normalize,
                                     policy_hidden_layer_sizes=(256, 256, 128), value_hidden_layer_sizes=(256, 256, 256))
policy = jax.jit(ppo_networks.make_inference_fn(net)(params, deterministic=True))
reset, step = jax.jit(env.reset), jax.jit(env.step)
state = reset(jax.random.PRNGKey(0))
rng = jax.random.PRNGKey(1)
qs, fell_at, powers, handsup = [], None, [], []
for i in range(int(a.seconds / env.dt)):
    rng, k = jax.random.split(rng)
    act, _ = policy(state.obs, k)
    state = step(state, act)
    qs.append(np.array(state.data.qpos))
    powers.append(float(state.metrics["energy"]))
    handsup.append(float(state.metrics["biped"]))
    if state.done and fell_at is None:
        fell_at = i * env.dt
        break

m = env.mj_model
d = mujoco.MjData(m)
r = mujoco.Renderer(m, 480, 854)
cam = mujoco.MjvCamera()
cam.distance, cam.azimuth, cam.elevation = (2.4, 100, -6) if a.near else (3.5, 110, -12)
frames = []
for q in qs:
    d.qpos[:] = q
    mujoco.mj_forward(m, d)
    cam.lookat[:] = (q[0], q[1], 0.7)
    r.update_scene(d, cam)
    frames.append(r.render())
mediapy.write_video(a.out, frames, fps=round(1 / env.dt))
dist = qs[-1][0] - qs[0][0]
# 移動のコスト (cost of transport) = 関節の仕事 ÷ (体重 × 進んだ距離) [J/kg/m]。筋肉の消費エネルギーではない
mass = float(m.body_subtreemass[1])
cot = sum(powers) * env.dt / (mass * max(dist, 1e-6))
print(f"平均の仕事率 {np.mean(powers):.0f} W, 移動のコスト {cot:.2f} J/kg/m, 手が浮いている時間 {100 * np.mean(handsup):.0f}%")
print(f"{len(qs) * env.dt:.1f} 秒, 前へ {dist:.2f} m, {'転倒 ' + format(fell_at, '.1f') + ' 秒' if fell_at is not None else '転ばず'} → {a.out}")
