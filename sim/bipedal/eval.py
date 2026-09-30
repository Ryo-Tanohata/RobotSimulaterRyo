"""学習結果の評価: 1 つの脳につき、始め方 (歩き出す瞬間・小さなゆらぎ) を変えた 16 回を 15 秒ずつ動かして平均する。
  ~/mjx/venv/bin/python sim/bipedal/eval.py 名前 [名前 ...]      → runs/名前/eval.json
  ~/mjx/venv/bin/python sim/bipedal/eval.py --summary 名前 ...    → 条件ごと (名前の _seed 以降を除いたもの) の平均とばらつき、
                                                                 docs/media/bipedal_study.png と docs/bipedal_study.md
測るもの (どちらも体重 1 kg・1 m あたり。小さいほど省エネ):
- 仕事のコスト: Σ|関節の力 × 角速度| の時間積分 [J/kg/m]
- 支える力のコスト: Σ|関節の力| の時間積分 [N·m·s/kg/m]。止まった姿勢を支えるだけでも筋肉は疲れる、の近似
"""
import argparse
import json
import re
from pathlib import Path

import numpy as np

HERE = Path(__file__).parent
ROOT = HERE.parent.parent
LABEL = {"s0_quad": "チンパンジー型 4足", "s0_biped": "チンパンジー型 2足", "s0.5_quad": "ルーシー型 4足",
         "s0.5_biped": "ルーシー型 2足", "s1_quad": "人型 4足", "s1_biped": "人型 2足"}


def evaluate(name, episodes=16, seconds=15.0):
    import jax
    import jax.numpy as jp
    from brax.training.acme import running_statistics
    from brax.training.agents.ppo import checkpoint
    from brax.training.agents.ppo import networks as ppo_networks

    from env import ApeWalk, default_config

    run = HERE / "runs" / name
    cfg = default_config()
    for k, v in json.loads((run / "config.json").read_text()).items():
        if k in cfg:
            cfg[k] = v
    env = ApeWalk(cfg)
    params = None
    for p in sorted((p for p in (run / "checkpoints").iterdir() if p.name.isdigit()), key=lambda p: int(p.name), reverse=True):
        try:
            params = checkpoint.load(str(p.resolve()))
            break
        except Exception:  # noqa: BLE001  時間切れで止めたときの途中の保存は飛ばす
            continue
    net = ppo_networks.make_ppo_networks(env.observation_size, env.action_size,
                                         preprocess_observations_fn=running_statistics.normalize,
                                         policy_hidden_layer_sizes=(256, 256, 128), value_hidden_layer_sizes=(256, 256, 256))
    policy = jax.jit(jax.vmap(ppo_networks.make_inference_fn(net)(params, deterministic=True)))
    reset, step = jax.jit(jax.vmap(env.reset)), jax.jit(jax.vmap(env.step))
    state = reset(jax.random.split(jax.random.PRNGKey(123), episodes))
    x0 = np.array(state.data.qpos[:, 0])
    alive = jp.ones(episodes)
    work = torque = t_alive = hands_up = jp.zeros(episodes)
    x_end = state.data.qpos[:, 0]
    keys = jax.random.split(jax.random.PRNGKey(7), episodes)
    for _ in range(int(seconds / env.dt)):
        act, _ = policy(state.obs, keys)
        state = step(state, act)
        work += alive * state.metrics["energy"] * env.dt
        torque += alive * state.metrics["torque"] * env.dt
        hands_up += alive * state.metrics["biped"]
        t_alive += alive * env.dt
        x_end = jp.where(alive > 0, state.data.qpos[:, 0], x_end)
        alive = alive * (1 - state.done)
    mass = float(env.mj_model.body_subtreemass[1])
    dist = np.maximum(np.array(x_end) - x0, 1e-3)
    res = {
        "name": name, "episodes": episodes, "seconds": seconds,
        "fell": float(np.mean(np.array(alive) == 0)),
        "distance": float(np.mean(dist)),
        "cot_work": float(np.mean(np.array(work) / (mass * dist))),
        "cot_torque": float(np.mean(np.array(torque) / (mass * dist))),
        "hands_up": float(np.mean(np.array(hands_up) / np.maximum(np.array(t_alive) / env.dt, 1))),
    }
    (run / "eval.json").write_text(json.dumps(res, ensure_ascii=False, indent=1))
    print(json.dumps(res, ensure_ascii=False))
    return res


def summary(names, tag=""):
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    from matplotlib import font_manager

    for f in ("/mnt/c/Windows/Fonts/meiryo.ttc", "/mnt/c/Windows/Fonts/YuGothM.ttc"):
        if Path(f).exists():
            font_manager.fontManager.addfont(f)
            plt.rcParams["font.family"] = font_manager.FontProperties(fname=f).get_name()
            break
    groups = {}
    for n in names:
        e = json.loads((HERE / "runs" / n / "eval.json").read_text())
        groups.setdefault(re.sub(r"_seed\d+$", "", n), []).append(e)
    order = sorted(groups, key=lambda k: (0 if "quad" in k else 1, k))  # 4 足 → 2 足、それぞれ s の順
    rows = []
    for k in order:
        g = groups[k]
        base = re.sub(r"^e\d+_", "", k)  # 実験 2 以降は名前の先頭に e2_ などが付く
        row = {"cond": k, "label": LABEL.get(base, base), "n": len(g)}
        mm = re.match(r"s([\d.]+)_(quad|biped)", base)
        row["s"], row["gait"] = (float(mm.group(1)), mm.group(2)) if mm else (0.0, base)
        for m in ("cot_work", "cot_torque", "distance", "fell", "hands_up"):
            v = np.array([e[m] for e in g])
            row[m], row[m + "_sd"] = float(v.mean()), float(v.std(ddof=1)) if len(v) > 1 else 0.0
        rows.append(row)

    fig, axes = plt.subplots(1, 2, figsize=(11, 4.2))
    if len({r["s"] for r in rows}) > 1 and tag:
        # 横軸 = 体の形 s、4 足と 2 足を線で (交わるかどうかを見る)
        for ax, m, title in ((axes[0], "cot_work", "仕事のコスト [J/kg/m]"), (axes[1], "cot_torque", "支える力のコスト [N·m·s/kg/m]")):
            for gait, col, lab in (("quad", "#8a5a3c", "4 足"), ("biped", "#3c7a8a", "2 足")):
                rs = sorted((r for r in rows if r["gait"] == gait), key=lambda r: r["s"])
                if not rs:
                    continue
                ax.errorbar([r["s"] for r in rs], [r[m] for r in rs], yerr=[r[m + "_sd"] for r in rs], color=col, marker="o", capsize=4, label=lab)
                for r in rs:
                    vals = [e[m] for e in groups[r["cond"]]]
                    ax.scatter([r["s"]] * len(vals), vals, color=col, s=10, alpha=0.5)
            ax.set_xticks([0, 0.5, 1], ["チンパンジー型\n(s=0)", "ルーシー型\n(s=0.5)", "人型\n(s=1)"])
            ax.set_title(title + "  (小さいほど省エネ)")
            ax.legend()
            ax.spines[["top", "right"]].set_visible(False)
        fig.suptitle("体の形ごとの移動のコスト: 4 足と 2 足 (各条件 3 回の学習の平均 ± 標準偏差、薄い点は各回)")
        fig.tight_layout()
        fig.savefig(ROOT / "docs" / "media" / f"bipedal_study{tag}.png", dpi=120)
        axes = None
    colors = ["#8a5a3c" if "quad" in r["cond"] else "#3c7a8a" for r in rows]
    for ax, m, title in (() if axes is None else ((axes[0], "cot_work", "仕事のコスト [J/kg/m]"), (axes[1], "cot_torque", "支える力のコスト [N·m·s/kg/m]"))):
        x = np.arange(len(rows))
        ax.bar(x, [r[m] for r in rows], yerr=[r[m + "_sd"] for r in rows], color=colors, capsize=5)
        for i, r in enumerate(rows):  # 各回の値も点で示す
            vals = [e[m] for e in groups[r["cond"]]]
            ax.scatter([i] * len(vals), vals, color="black", s=12, zorder=3)
        ax.set_xticks(x, [r["label"].replace(" ", "\n", 1) for r in rows])
        ax.set_title(title + "  (小さいほど省エネ)")
        ax.spines[["top", "right"]].set_visible(False)
    if axes is not None:
        fig.suptitle("体の形と歩き方ごとの移動のコスト (各条件 3 回の学習の平均 ± 標準偏差、点は各回)")
        fig.tight_layout()
        fig.savefig(ROOT / "docs" / "media" / f"bipedal_study{tag}.png", dpi=120)

    lines = [f"# 2 足・4 足の比較{' (実験 ' + tag + ')' if tag else ''} (お手本あり、学習量をそろえ各条件 3 回)", "",
             "自動で作った表です (`sim/bipedal/eval.py --summary`)。各回 16 通りの始め方 × 15 秒の平均を、さらに学習 3 回で平均しています。", "",
             "| 条件 | 回数 | 仕事のコスト (J/kg/m) | 支える力のコスト (N·m·s/kg/m) | 15 秒で進んだ距離 (m) | 転んだ割合 | 両手が浮いている割合 |",
             "|---|---|---|---|---|---|---|"]
    for r in rows:
        lines.append(f"| {r['label']} | {r['n']} | {r['cot_work']:.2f} ± {r['cot_work_sd']:.2f} | {r['cot_torque']:.2f} ± {r['cot_torque_sd']:.2f} | "
                     f"{r['distance']:.1f} ± {r['distance_sd']:.1f} | {100 * r['fell']:.0f}% | {100 * r['hands_up']:.0f}% |")
    lines += ["", f"![比較のグラフ](media/bipedal_study{tag}.png)", "",
              "注意: 歩き方の型 (お手本) は人が与えている。コストは関節の力から計算した近似で、筋肉の消費エネルギーそのものではない。"]
    (ROOT / "docs" / f"bipedal_study{tag}.md").write_text("\n".join(lines) + "\n", encoding="utf-8")
    print("\n".join(lines))


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("names", nargs="+")
    ap.add_argument("--summary", action="store_true")
    ap.add_argument("--tag", default="", help="表とグラフのファイル名に付ける (例: 2 → bipedal_study2.md)")
    a = ap.parse_args()
    if a.summary:
        summary(a.names, a.tag)
    else:
        for n in a.names:
            evaluate(n)
