"""GPU で MJX の物理演算が動くかと、その速さを測る。
  ~/mjx/venv/bin/python tools/mjx/check_gpu.py [同時に動かす体の数 ...]
MuJoCo Playground の人型 (Humanoid) を N 体並べて 1000 ステップ進め、1 秒あたりのステップ数を出す。
"""
import sys
import time

import jax
import jax.numpy as jp
from mujoco_playground import registry

print("devices:", jax.devices())
env = registry.load("HumanoidWalk")
reset = jax.jit(jax.vmap(env.reset))
step = jax.jit(jax.vmap(env.step))

for n in [int(a) for a in sys.argv[1:]] or [256, 1024, 4096]:
    keys = jax.random.split(jax.random.PRNGKey(0), n)
    state = reset(keys)
    act = jp.zeros((n, env.action_size))
    state = step(state, act)  # コンパイル
    jax.block_until_ready(state.obs)
    t = time.time()
    for _ in range(1000):
        state = step(state, act)
    jax.block_until_ready(state.obs)
    dt = time.time() - t
    print(f"{n:5d} 体: {n * 1000 / dt:,.0f} ステップ/秒  (1000 ステップ {dt:.1f} 秒)")
