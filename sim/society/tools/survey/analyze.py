"""論文 2・実験 1: answers/*.json を読み、事前登録 (docs/research/humanity/paper2_exp1_prereg.md の 7.・8.) のとおりに数える。

    python3 analyze.py [--answers DIR] [--out DIR] [--boot 1000]

書くもの (out/ 。図は英語と日本語の両方の見出し):
- summary.md            仮説ごとの数と、決めた線で「支持 / 支持しない」
- items.csv             問いごとの 平均・SD・いちばん多い答えの割合 (条件ごと) と規範の数
- eigen.csv             条件ごとの固有値・寄与率・累積 (と人間の表 3・ノイズの基準)
- loadings_<cond>.csv   主成分 1〜10 の固有ベクトル
- match.csv             人間の 5 つの主成分 × LLM の一致の点 (H5)
- fig_item_means.png / fig_item_sd.png / fig_scree.png / fig_gray_shift.png
numpy と matplotlib だけを使う。
"""
import argparse
import csv
import glob
import json
import os

import numpy as np

from items import (CONDITIONS, GRAY, HUMAN_CUM_FROM_EIG, HUMAN_CUM_PRINTED, HUMAN_EIG, HUMAN_N, HUMAN_PCS, IDS, NORM,
                   TEXT)

HERE = os.path.dirname(os.path.abspath(__file__))
P = len(IDS)
KMAX = 10          # H5: LLM の主成分 1〜10 から、いちばん合うものを探す
SEED = 20261029
# 決めの線 (prereg 8.)
H1_SD = 0.5        # H1a: 問いの SD の平均がこれより小さければ「そろいすぎ」
H1_PC1 = HUMAN_EIG[0] / P   # 0.268 (固有値から。印刷の 0.36 は参考)
H2_MAE = 0.5       # H2: 規範との差 (絶対値) の平均がこれより小さければ「規範に近い」
H4_D = -0.2        # H4: グレーゾーンの平均の差 (C2 − C1) がこれ以下で、CI の上が 0 未満
H5_OVL = 3         # H5: 上位 5 問のうち 3 問以上が重なり、偶然の p < 0.05 なら「再現」
COLORS = {"C0": "#2a78d6", "C1": "#eb6834", "C2": "#1baf7a", "C3": "#eda100", "C4": "#e87ba4", "pooled": "#6250d6"}
INK, MUTED = "#0b0b0b", "#52514e"


# ---------- 読む ----------
def load(answers_dir):
    data = {c: {"ids": [], "X": [], "honne": []} for c in CONDITIONS}
    for fn in sorted(glob.glob(os.path.join(answers_dir, "*.json"))):
        r = json.load(open(fn, encoding="utf-8"))
        c = r["condition"]
        data[c]["ids"].append(r["id"])
        data[c]["X"].append([r["answers"][i] for i in IDS])
        data[c]["honne"].append(r.get("honne"))
    for c in data:
        data[c]["X"] = np.array(data[c]["X"], float).reshape(-1, P)
    return data


# ---------- 数える ----------
def item_stats(X):
    if len(X) < 2:
        return np.full(P, np.nan), np.full(P, np.nan), np.full(P, np.nan)
    modal = np.array([np.bincount(X[:, j].astype(int), minlength=6).max() / len(X) for j in range(P)])
    return X.mean(0), X.std(0, ddof=1), modal


def pca(X):
    """R の prcomp(X, scale.=TRUE) と同じ: 問いを標準化 (SD は n−1) して、相関行列の固有値・固有ベクトル。
    SD が 0 の問いは標準化できないので除く (除いた数を返す)。返す固有値の割合は「使った問いの数」で割る。"""
    sd = X.std(0, ddof=1)
    used = np.where(sd > 0)[0]
    Z = (X[:, used] - X[:, used].mean(0)) / sd[used]
    C = Z.T @ Z / (len(X) - 1)
    w, V = np.linalg.eigh(C)
    o = np.argsort(w)[::-1]
    w, V = np.clip(w[o], 0, None), V[:, o]
    full = np.zeros((P, V.shape[1]))
    full[used] = V
    return w, full, used


def n_to_reach(w, p, frac):
    cum = np.cumsum(w) / p
    k = np.searchsorted(cum, frac - 1e-12) + 1
    return int(k) if k <= len(w) else None


def noise_eig(n, reps=200, seed=SEED):
    """同じ n・54 問で、答えが互いに無関係 (正規乱数) なときの固有値の平均 (平行分析の基準)。"""
    rng = np.random.default_rng(seed)
    acc = np.zeros(min(n - 1, P))
    for _ in range(reps):
        w, _, _ = pca(rng.standard_normal((n, P)))
        acc += w[:len(acc)]
    return acc / reps


def match_one(V, items, signs, kmax=KMAX):
    """人間の主成分 1 つ (上位 5 問と符号) と、LLM の主成分 1〜kmax のうち符号をそろえた和 |Σ s_i v_ji| がいちばん大きいもの。
    返す: (何番目, 重なった問いの数 (LLM のその主成分の |v| の上位 5 問との), 符号の合った割合)"""
    idx = [IDS.index(i) for i in items]
    s = np.array(signs, float)
    k = min(kmax, V.shape[1])
    sums = np.array([np.sum(s * V[idx, j]) for j in range(k)])
    j = int(np.argmax(np.abs(sums)))
    orient = 1.0 if sums[j] >= 0 else -1.0
    top = set(np.argsort(-np.abs(V[:, j]))[:5])
    ovl = len(top & set(idx))
    agree = float(np.mean(np.sign(orient * V[idx, j]) == np.sign(s)))
    return j + 1, ovl, agree


def match_all(V, rng, n_null=2000):
    rows = []
    null = []
    for _ in range(n_null):  # 偶然の基準: でたらめな 5 問・でたらめな符号で同じ手順
        items = list(rng.choice(IDS, 5, replace=False))
        null.append(match_one(V, items, rng.choice([-1, 1], 5))[1])
    null = np.array(null)
    for pc, ja, en, top in HUMAN_PCS:
        j, ovl, agree = match_one(V, [i for i, _ in top], [np.sign(v) for _, v in top])
        p = float(np.mean(null >= ovl))
        rows.append({"human_pc": pc, "name_ja": ja, "name_en": en, "llm_pc": j, "overlap": ovl, "sign_agree": round(agree, 2),
                     "p_null": round(p, 4), "reproduced": bool(ovl >= H5_OVL and p < 0.05)})
    return rows, float(null.mean())


def boot(X, f, B, rng):
    vals = []
    for _ in range(B):
        v = f(X[rng.integers(0, len(X), len(X))])
        if v is not None and np.all(np.isfinite(v)):
            vals.append(v)
    return np.percentile(np.array(vals), [2.5, 97.5], axis=0) if vals else (np.nan, np.nan)


def pc1_share(X):
    w, _, used = pca(X)
    return w[0] / len(used)


# ---------- 図 ----------
def setup_mpl():
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    from matplotlib import font_manager
    for name in ["IPAGothic", "IPAexGothic", "Noto Sans CJK JP", "Yu Gothic", "Hiragino Sans", "MS Gothic"]:
        if any(f.name == name for f in font_manager.fontManager.ttflist):
            plt.rcParams["font.family"] = name
            break
    plt.rcParams.update({"axes.edgecolor": MUTED, "axes.labelcolor": INK, "xtick.color": MUTED, "ytick.color": MUTED,
                         "axes.spines.top": False, "axes.spines.right": False, "axes.grid": True, "grid.color": "#e6e5e0",
                         "grid.linewidth": 0.6, "lines.linewidth": 2})
    return plt


def fig_items(plt, stats, conds, key, ylabel, title, out, norm=False):
    fig, ax = plt.subplots(figsize=(16, 4.8))
    x = np.arange(P)
    off = np.linspace(-0.3, 0.3, max(len(conds), 1))
    for k, c in enumerate(conds):
        ax.plot(x + off[k], stats[c][key], "o", ms=4, color=COLORS[c], label=f"{c} ({CONDITIONS[c]['model']}, n={stats[c]['n']})")
    if norm:
        ax.plot(x, [NORM[i] for i in IDS], "_", ms=12, mew=2, color=MUTED, label="norm (thesis expected) / 規範 (論文の予想)")
        ax.set_ylim(0.8, 5.2)
    ax.set_xticks(x)
    ax.set_xticklabels(IDS, rotation=90, fontsize=7)
    for g in GRAY:
        ax.axvspan(IDS.index(g) - 0.45, IDS.index(g) + 0.45, color="#f2f1ec", zorder=0)
    ax.set_ylabel(ylabel)
    ax.set_title(title + "  (shaded = gray-zone items / 灰色 = グレーゾーンの問い)", fontsize=10, color=INK, loc="left")
    ax.legend(fontsize=8, ncol=6, frameon=False, loc="upper center", bbox_to_anchor=(0.5, -0.16))
    fig.tight_layout()
    fig.savefig(out, dpi=130)
    plt.close(fig)


def fig_scree(plt, eig, noise84, out):
    fig, ax = plt.subplots(figsize=(7, 4.5))
    K = 15
    for c, w in eig.items():
        ax.plot(np.arange(1, min(K, len(w)) + 1), w[:K], "-o", ms=4, color=COLORS[c], label=f"LLM {c}")
    ax.plot(np.arange(1, 6), HUMAN_EIG, "-s", ms=6, color=INK, label=f"human (thesis, n={HUMAN_N}) / 人間 (修士論文)")
    ax.plot(np.arange(1, K + 1), noise84[:K], "--", color=MUTED, lw=1.5, label="random answers, n=84 / でたらめな答え")
    ax.set_xlabel("component / 主成分")
    ax.set_ylabel("eigenvalue / 固有値")
    ax.set_title("Scree plot (standardized 54 items) / 固有値の並び", fontsize=10, color=INK, loc="left")
    ax.legend(fontsize=8, frameon=False)
    fig.tight_layout()
    fig.savefig(out, dpi=130)
    plt.close(fig)


def fig_gray(plt, m1, m2, out):
    fig, ax = plt.subplots(figsize=(7, 5))
    y = np.arange(len(GRAY))
    gi = [IDS.index(g) for g in GRAY]
    for k, j in enumerate(gi):
        ax.plot([m1[j], m2[j]], [k, k], "-", color="#c3c2b7", lw=2, zorder=1)
    ax.plot(m1[gi], y, "o", ms=8, color=COLORS["C1"], label="C1 persona / 人格", zorder=2)
    ax.plot(m2[gi], y, "o", ms=8, color=COLORS["C2"], label="C2 persona + honne first / 人格 + 本音を先に", zorder=2)
    ax.plot([NORM[g] for g in GRAY], y, "|", ms=12, mew=2, color=MUTED, label="norm / 規範")
    ax.set_yticks(y)
    ax.set_yticklabels(GRAY)
    ax.set_xlim(0.8, 5.2)
    ax.set_xlabel("mean (5 = serious problem … 1 = no problem) / 平均")
    ax.set_title("Gray-zone items: C1 vs C2 / グレーゾーンの問い", fontsize=10, color=INK, loc="left")
    ax.legend(fontsize=8, frameon=False, loc="lower right")
    fig.tight_layout()
    fig.savefig(out, dpi=130)
    plt.close(fig)


# ---------- 本体 ----------
def fmt(v, d=3):
    return "—" if v is None or (isinstance(v, float) and not np.isfinite(v)) else (f"{v:.{d}f}" if isinstance(v, float) else str(v))


def ci(a):
    return f"[{fmt(float(a[0]))}, {fmt(float(a[1]))}]"


def run(answers_dir, out_dir, B=1000, figures=True):
    rng = np.random.default_rng(SEED)
    os.makedirs(out_dir, exist_ok=True)
    data = load(answers_dir)
    conds = [c for c in CONDITIONS if len(data[c]["X"]) >= 2]
    stats = {}
    for c in conds:
        m, s, mo = item_stats(data[c]["X"])
        stats[c] = {"mean": m, "sd": s, "modal": mo, "n": len(data[c]["X"])}
    L = ["# 実験 1 の結果 (analyze.py が書いた)", "",
         "答えの数: " + ", ".join(f"{c} {len(data[c]['X'])}/{CONDITIONS[c]['n']}" for c in CONDITIONS), ""]

    # items.csv
    with open(os.path.join(out_dir, "items.csv"), "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["item", "text", "norm", "gray"] + [f"{c}_{k}" for c in conds for k in ("mean", "sd", "modal")])
        for j, i in enumerate(IDS):
            w.writerow([i, TEXT[i], NORM[i], int(i in GRAY)] +
                       [round(float(stats[c][k][j]), 3) for c in conds for k in ("mean", "sd", "modal")])

    # H1a・H2・H3 (問いごとの数)
    L += ["## 問いごとの数 (H1a・H2・H3)", "",
          "| 条件 | n | SD の平均 (95% CI) | SD が 0 の問い | いちばん多い答えが 9 割以上の問い | 規範との差 |平均| (95% CI) | 規範との差 (符号つき, + = 規範より厳しい) | 人ごとの平均点の SD |",
          "|---|---|---|---|---|---|---|---|"]
    norm = np.array([NORM[i] for i in IDS])
    res = {}
    for c in conds:
        X = data[c]["X"]
        mean_sd = float(np.mean(stats[c]["sd"]))
        sd_ci = boot(X, lambda Y: np.mean(Y.std(0, ddof=1)), B, rng)
        mae = float(np.mean(np.abs(stats[c]["mean"] - norm)))
        mae_ci = boot(X, lambda Y: np.mean(np.abs(Y.mean(0) - norm)), B, rng)
        signed = float(np.mean(stats[c]["mean"] - norm))
        res[c] = {"mean_sd": mean_sd, "mae": mae}
        L.append(f"| {c} ({CONDITIONS[c]['model']}) | {len(X)} | {fmt(mean_sd)} {ci(sd_ci)} | {int(np.sum(stats[c]['sd'] == 0))} | "
                 f"{int(np.sum(stats[c]['modal'] >= 0.9))} | {fmt(mae)} {ci(mae_ci)} | {fmt(signed, 2)} | {fmt(float(X.mean(1).std(ddof=1)))} |")
    L.append("")
    for c in ("C0", "C3", "C4"):
        if c in res:
            L.append(f"- **H1a {c}:** SD の平均 {fmt(res[c]['mean_sd'])} → "
                     + ("支持 (そろいすぎ。線 < 0.5)" if res[c]["mean_sd"] < H1_SD else "支持しない (線 0.5 以上)"))
    for c in ("C0", "C3", "C4"):
        if c in res:
            L.append(f"- **H2 {c}:** 規範との差の平均 {fmt(res[c]['mae'])} → "
                     + ("支持 (規範に近い。線 < 0.5)" if res[c]["mae"] < H2_MAE else "支持しない") + " (人間の平均がないので、人との比較はできない)")
    if "C0" in conds and "C1" in conds:
        X0, X1 = data["C0"]["X"], data["C1"]["X"]
        d = []
        for _ in range(B):
            d.append(np.mean(X1[rng.integers(0, len(X1), len(X1))].std(0, ddof=1))
                     - np.mean(X0[rng.integers(0, len(X0), len(X0))].std(0, ddof=1)))
        lo, hi = np.percentile(d, [2.5, 97.5])
        diff = res["C1"]["mean_sd"] - res["C0"]["mean_sd"]
        L.append(f"- **H3:** SD の平均 C1 − C0 = {fmt(diff)} [{fmt(lo)}, {fmt(hi)}] → "
                 + ("支持 (人格でばらつきが増えた)" if lo > 0 else "支持しない"))
    if "C1" in conds and os.path.exists(os.path.join(HERE, "personas.json")):
        ps = json.load(open(os.path.join(HERE, "personas.json"), encoding="utf-8"))["personas"]
        X1 = data["C1"]["X"]
        k = [int(r.split("_")[1]) - 1 for r in data["C1"]["ids"]]
        strict = X1.mean(1)
        cors = []
        for t in ("E", "A", "C", "N", "O"):
            z = np.array([ps[q]["big5_z"][t] for q in k])
            cors.append(f"{t} {np.corrcoef(z, strict)[0, 1]:+.2f}")
        L.append("- **H3b (探索):** C1 の人ごとの平均点 (厳しさ) とビッグファイブの相関: " + ", ".join(cors))
    L.append("")

    # PCA (H1b・H5)
    pca_sets = {c: data[c]["X"] for c in ("C1", "C2") if c in conds and len(data[c]["X"]) >= 10}
    if "C1" in pca_sets and "C2" in pca_sets:
        pca_sets["pooled"] = np.vstack([pca_sets["C1"], pca_sets["C2"]])
    noise84 = noise_eig(HUMAN_N)
    eig = {}
    L += ["## 主成分分析 (H1b・H5)", "",
          f"人間 (修士論文 表 3): 固有値 {HUMAN_EIG}、累積 (印刷) {HUMAN_CUM_PRINTED}、累積 (固有値 / 54 から) {HUMAN_CUM_FROM_EIG}。"
          f"第 1 主成分の割合 {H1_PC1:.3f} (印刷では 0.36。合わない)。でたらめな答え (n=84) の第 1 固有値 {noise84[0]:.2f}。", "",
          "| 条件 | n | 使った問い | 固有値 1〜5 | 第 1 の割合 (95% CI, n=84 に引き直し) | 50.3% に届く数 | 81% に届く数 |",
          "|---|---|---|---|---|---|---|"]
    with open(os.path.join(out_dir, "eigen.csv"), "w", newline="", encoding="utf-8") as fe:
        we = csv.writer(fe)
        we.writerow(["set", "k", "eigenvalue", "share", "cumulative"])
        for k in range(5):
            we.writerow(["human_printed", k + 1, HUMAN_EIG[k], round(HUMAN_EIG[k] / P, 4), HUMAN_CUM_PRINTED[k]])
        for k in range(15):
            we.writerow(["noise_n84", k + 1, round(float(noise84[k]), 4), round(float(noise84[k]) / P, 4), ""])
        match_rows = []
        for c, X in pca_sets.items():
            w, V, used = pca(X)
            eig[c] = w
            p = len(used)
            cum = np.cumsum(w) / p
            for k in range(min(15, len(w))):
                we.writerow([c, k + 1, round(float(w[k]), 4), round(float(w[k] / p), 4), round(float(cum[k]), 4)])
            sub = lambda Y: pc1_share(Y[:HUMAN_N])  # 引き直した中から 84 人
            share_ci = boot(X, sub, B, rng)
            L.append(f"| {c} | {len(X)} | {p} | {', '.join(f'{v:.2f}' for v in w[:5])} | {w[0] / p:.3f} {ci(share_ci)} | "
                     f"{n_to_reach(w, p, HUMAN_CUM_FROM_EIG[4])} | {n_to_reach(w, p, 0.81)} |")
            verdict = "支持 (人と違う: CI が 0.268 を含まない)" if (share_ci[0] > H1_PC1 or share_ci[1] < H1_PC1) else "支持しない (CI が 0.268 を含む)"
            res.setdefault("h1b", []).append(f"- **H1b {c}:** 第 1 主成分の割合 {w[0] / p:.3f} {ci(share_ci)} → {verdict}")
            with open(os.path.join(out_dir, f"loadings_{c}.csv"), "w", newline="", encoding="utf-8") as fl:
                wl = csv.writer(fl)
                wl.writerow(["item"] + [f"pc{k + 1}" for k in range(KMAX)])
                for j, i in enumerate(IDS):
                    wl.writerow([i] + [round(float(V[j, k]), 4) for k in range(min(KMAX, V.shape[1]))])
            rows, null_mean = match_all(V, rng)
            # 一致の点の CI: 人を引き直して PCA をやり直し、同じ手順の重なりの数
            bo = []
            for _ in range(min(B, 300)):
                Y = X[rng.integers(0, len(X), len(X))]
                _, Vb, _ = pca(Y)
                bo.append([match_one(Vb, [i for i, _ in t], [np.sign(v) for _, v in t])[1] for _, _, _, t in HUMAN_PCS])
            lo, hi = np.percentile(np.array(bo), [2.5, 97.5], axis=0)
            for r, a, b in zip(rows, lo, hi):
                r.update({"set": c, "overlap_ci": f"[{a:.0f}, {b:.0f}]", "null_mean_overlap": round(null_mean, 2)})
                match_rows.append(r)
            top = ", ".join(f"pc{k + 1}: " + " ".join(IDS[j] for j in np.argsort(-np.abs(V[:, k]))[:5]) for k in range(3))
            res.setdefault("tops", []).append(f"- {c} の上位 5 問 (|固有ベクトル|): {top}")
    L.append("")
    L += res.get("h1b", []) + [""] + res.get("tops", []) + [""]
    if match_rows:
        keys = ["set", "human_pc", "name_ja", "name_en", "llm_pc", "overlap", "overlap_ci", "sign_agree", "p_null", "null_mean_overlap", "reproduced"]
        with open(os.path.join(out_dir, "match.csv"), "w", newline="", encoding="utf-8") as fm:
            wm = csv.DictWriter(fm, fieldnames=keys)
            wm.writeheader()
            wm.writerows(match_rows)
        L += ["### H5: 人間の 5 つの主成分の上位 5 問が、LLM でもいっしょに出るか (すべて書く)", "",
              "| 組 | 人間の主成分 | いちばん合う LLM の主成分 | 重なり (0〜5) (95% CI) | 符号の合う割合 | 偶然の p | 再現 |", "|---|---|---|---|---|---|---|"]
        for r in match_rows:
            L.append(f"| {r['set']} | {r['human_pc']} {r['name_ja']} | pc{r['llm_pc']} | {r['overlap']} {r['overlap_ci']} | {r['sign_agree']} | "
                     f"{r['p_null']} | {'はい' if r['reproduced'] else 'いいえ'} |")
        L.append("")
        for c in pca_sets:
            nrep = sum(r["reproduced"] for r in match_rows if r["set"] == c)
            L.append(f"- **H5 {c}:** 再現 {nrep}/5 → " + ("支持 (3 つ以上)" if nrep >= 3 else "支持しない"))
        L.append("")

    # H4
    if "C1" in conds and "C2" in conds:
        id1 = {r.split("_")[1]: k for k, r in enumerate(data["C1"]["ids"])}
        id2 = {r.split("_")[1]: k for k, r in enumerate(data["C2"]["ids"])}
        both = sorted(set(id1) & set(id2))
        X1 = data["C1"]["X"][[id1[b] for b in both]]
        X2 = data["C2"]["X"][[id2[b] for b in both]]
        g = [IDS.index(i) for i in GRAY]
        ng = [j for j in range(P) if j not in g]
        dg = X2[:, g].mean(1) - X1[:, g].mean(1)
        dn = X2[:, ng].mean(1) - X1[:, ng].mean(1)
        bg, bn, bd = [], [], []
        for _ in range(B):
            s = rng.integers(0, len(both), len(both))
            bg.append(dg[s].mean()); bn.append(dn[s].mean()); bd.append((dg[s] - dn[s]).mean())
        cg, cn, cd = (np.percentile(v, [2.5, 97.5]) for v in (bg, bn, bd))
        sup = dg.mean() <= H4_D and cg[1] < 0
        L += ["## H4: 本音を先に書くと、グレーゾーンの問いで「問題でない」へ動くか (C2 − C1、同じ人格の対)", "",
              f"- 対の数 {len(both)}。グレーゾーン {len(GRAY)} 問: {' '.join(GRAY)}",
              f"- グレーゾーンの平均の差 {dg.mean():+.3f} {ci(cg)} / ほかの問い {dn.mean():+.3f} {ci(cn)} / 差の差 {(dg - dn).mean():+.3f} {ci(cd)}",
              "- **H4:** " + ("支持 (差 ≤ −0.2 で CI の上が 0 未満)" if sup else "支持しない")
              + ("。グレーゾーンだけの動き (差の差の CI が 0 未満)" if cd[1] < 0 else "。グレーゾーンだけの動きとは言えない (差の差の CI が 0 をふくむ)"),
              ]
        empty = sum(1 for h in data["C2"]["honne"] if h for v in h.values() if not str(v).strip())
        L += [f"- 本音が空の答え: {empty} / {len(data['C2']['honne']) * P}", ""]
        if figures:
            plt = setup_mpl()
            fig_gray(plt, X1.mean(0), X2.mean(0), os.path.join(out_dir, "fig_gray_shift.png"))

    if figures and conds:
        plt = setup_mpl()
        fig_items(plt, stats, conds, "mean", "mean / 平均 (5 = serious … 1 = none)",
                  "Item means vs norm / 問いごとの平均と規範", os.path.join(out_dir, "fig_item_means.png"), norm=True)
        fig_items(plt, stats, conds, "sd", "SD / 標準偏差", "Item SD / 問いごとのばらつき", os.path.join(out_dir, "fig_item_sd.png"))
        if eig:
            fig_scree(plt, eig, noise84, os.path.join(out_dir, "fig_scree.png"))
    with open(os.path.join(out_dir, "summary.md"), "w", encoding="utf-8") as f:
        f.write("\n".join(L) + "\n")
    return L


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--answers", default=os.path.join(HERE, "answers"))
    ap.add_argument("--out", default=os.path.join(HERE, "out"))
    ap.add_argument("--boot", type=int, default=1000)
    a = ap.parse_args()
    print("\n".join(run(a.answers, a.out, a.boot)))


if __name__ == "__main__":
    main()
