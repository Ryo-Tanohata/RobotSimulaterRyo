"""PPO で学習する (GPU)。途中経過は評価のたびに保存され、止まっても続きから再開できる。
  ~/mjx/venv/bin/python sim/bipedal/train.py 名前 [--s 1.0] [--steps 20000000] [--envs 2048] [--hands-off] [--resume]
結果: sim/bipedal/runs/名前/ (checkpoints/ と log.csv)
"""
import argparse
import functools
import time
from pathlib import Path

import jax
import jax.numpy as jnp

# brax が使っている古い JAX の関数 (JAX 0.11 で削除) の代わり。GPU 1 枚なので、先頭に「装置の数」の軸を足すだけ
def _put_replicated(x, devices):
    return jax.tree.map(lambda v: jax.device_put(jnp.stack([v] * len(devices))), x)


def _put_sharded(xs, devices):
    return jax.tree.map(lambda *v: jax.device_put(jnp.stack(v)), *xs)


for _name, _fn in (("device_put_replicated", _put_replicated), ("device_put_sharded", _put_sharded)):
    try:
        getattr(jax, _name)
    except AttributeError:
        setattr(jax, _name, _fn)

from brax.training.agents.ppo import networks as ppo_networks
from brax.training.agents.ppo import train as ppo
from mujoco_playground import wrapper

from env import ApeWalk, default_config

ap = argparse.ArgumentParser()
ap.add_argument("name")
ap.add_argument("--s", type=float, default=1.0)
ap.add_argument("--speed", type=float, default=1.0)
ap.add_argument("--steps", type=int, default=20_000_000)
ap.add_argument("--envs", type=int, default=2048)
ap.add_argument("--evals", type=int, default=10)
ap.add_argument("--hands-off", action="store_true")
ap.add_argument("--resume", action="store_true")
ap.add_argument("--imitate", action="store_true", help="お手本 (reference.py) を土台にする")
ap.add_argument("--gait", default="biped", choices=["biped", "quad", "human2"], help="お手本の歩き方 (human2 = 人間らしい歩き方、速さを変えられる)")
ap.add_argument("--alive", type=float, default=None)
ap.add_argument("--seed", type=int, default=1)
ap.add_argument("--exp2", action="store_true", help="実験 2: お手本を体に合わせる + 足首のばね")
ap.add_argument("--froude", type=float, default=None, help="目標の速さを脚の長さに合わせる (フルード数 v^2/(g×脚の長さ))。--speed より優先")
ap.add_argument("--torque-weight", type=float, default=None)
ap.add_argument("--fall-penalty", type=float, default=None)
a = ap.parse_args()

out = Path(__file__).parent / "runs" / a.name
ckpt = (out / "checkpoints").resolve()
ckpt.mkdir(parents=True, exist_ok=True)
cfg = default_config()
cfg.s, cfg.target_speed, cfg.hands_off, cfg.imitate = a.s, a.speed, a.hands_off, a.imitate
cfg.gait = a.gait
cfg.exp2 = a.exp2
if a.froude is not None:
    from body import shape
    sh = shape(a.s)
    cfg.target_speed = float((a.froude * 9.81 * (sh.thigh + sh.shank)) ** 0.5)
    print("目標の速さ", round(cfg.target_speed, 3), "m/s")
if a.torque_weight is not None:
    cfg.torque_weight = a.torque_weight
if a.alive is not None:
    cfg.alive = a.alive
if a.fall_penalty is not None:
    cfg.fall_penalty = a.fall_penalty
(out / "config.json").write_text(cfg.to_json_best_effort(indent=1))  # render.py が同じ設定で動かすため
env = ApeWalk(cfg)
log = open(out / "log.csv", "a")
if log.tell() == 0:
    log.write("time,steps,reward,speed,biped,energy\n")
t0 = time.time()


def progress(steps, m):
    r = m.get("eval/episode_reward", float("nan"))
    line = (f"{time.time() - t0:.0f},{steps},{r:.2f},{m.get('eval/episode_speed', 0):.3f},"
            f"{m.get('eval/episode_biped', 0):.3f},{m.get('eval/episode_energy', 0):.1f}")
    log.write(line + "\n")
    log.flush()
    print(line, flush=True)


restore = None
if a.resume:
    done = sorted((p for p in ckpt.iterdir() if p.name.isdigit()), key=lambda p: int(p.name))
    restore = done[-1] if done else None
    print("再開:", restore)

ppo.train(
    environment=env, eval_env=ApeWalk(cfg), wrap_env_fn=wrapper.wrap_for_brax_training,
    num_timesteps=a.steps, num_evals=a.evals, episode_length=cfg.episode_length,
    num_envs=a.envs, batch_size=256, num_minibatches=32, num_updates_per_batch=4, unroll_length=20,
    learning_rate=3e-4, entropy_cost=5e-3, discounting=0.97, reward_scaling=1.0, clipping_epsilon=0.2,
    normalize_observations=True, max_grad_norm=1.0,
    network_factory=functools.partial(ppo_networks.make_ppo_networks,
                                      policy_hidden_layer_sizes=(256, 256, 128), value_hidden_layer_sizes=(256, 256, 256)),
    progress_fn=progress, save_checkpoint_path=str(ckpt),
    restore_checkpoint_path=str(restore) if restore else None, seed=a.seed,
)
print("完了", out)
