"""論文 2・実験 2c: answers_exp2c/*.json (F1・F2) を読み、事前登録 (docs/research/humanity/paper2_exp2c_prereg.md の 7.・8.) のとおりに数える。

    python3 analyze_exp2c.py [--answers DIR] [--exp2 DIR] [--exp2b DIR] [--out DIR] [--boot 1000]

部品 (主成分分析・一致の点・ブートストラップ・図) は analyze.py と analyze_exp2.py のものをそのまま使う。
くらべる相手: 人間 (修士論文 表 3) と、実験 2 の D1 (同じ暮らし・出来事なし。F1_k・F2_k は D1_k と同じ暮らし S(k)) が主。
実験 2 の D2・実験 2b の E1・D2r は、第 1 主成分の割合などをならべるだけ (参考)。
書くもの (out_exp2c/):
- summary.md   仮説 H16〜H19 と、効き目の確かめの数と判定 (決めた線のとおり)、探索の数
- items.csv / eigen.csv / loadings_<組>.csv / match.csv / share_diff.csv / manip_coef.csv / reasons.csv / reasons_coded.csv
- fig_scree.png / fig_pc1_share.png / fig_manip_coef.png
"""
import csv
import json
import os

import numpy as np

import analyze as A
import analyze_exp2 as E2
import reasons_codebook as RC
from experiences import DKEYS, DOMAINS
from items import (CONDITIONS_EXP2, CONDITIONS_EXP2B, CONDITIONS_EXP2C, DOMAIN_ITEMS, DOMAIN_REST, HUMAN_CUM_FROM_EIG, HUMAN_EIG,
                   HUMAN_N, HUMAN_PCS, IDS, NORM, REASON_ITEMS, TEXT)

HERE = os.path.dirname(os.path.abspath(__file__))
P = len(IDS)
SEED = 20261102
# 決めの線 (prereg 8.)
H16_D = -0.03      # H16: 第 1 主成分の割合の対の差 (F2 − D1) がこれ以下で、対のブートストラップの CI の上が 0 未満
H17_R = 0.95       # H17: F2 の |r(厳しさ, 第 1 主成分の点)| がこれ未満で、
H17_HI = 0.97      #      ブートストラップの CI の上がこれ未満
H18_N = 2          # H18: 人間の 5 つの主成分のうち、F2 で再現 (実験 2 の H7 と同じ決まり) がこの数以上
MANIP_N = 3        # 効き目の確かめ: 5 つの領域のうち、自分の領域の係数の CI の下が 0 より上の領域がこの数以上
HUMAN_PC1 = HUMAN_EIG[0] / P
DJA = dict(DOMAINS)
DOMAIN_OF = {i: d for d, v in DOMAIN_ITEMS.items() for i in v}
REASON_DOMAIN = {i: DOMAIN_OF.get(i) for i in REASON_ITEMS}
A.COLORS.setdefault("F1", "#6250d6")
A.COLORS.setdefault("F2", "#d03b3b")
NAME = {"F1": "F1 (出来事 3 つ)", "F2": "F2 (出来事 6 つ)", "D1": "実験 2 D1 (暮らしだけ)", "D2": "実験 2 D2 (暮らし + ダウンロードの様子)",
        "E1": "実験 2b E1 (暮らし + 借りた物の様子)", "D2r": "実験 2b D2r (D2 のくり返し)"}


def pairs(a, b):
    """同じ暮らしの対: (番号の list, a の行, b の行)。"""
    ia = {r.split("_")[1]: k for k, r in enumerate(a["ids"])}
    ib = {r.split("_")[1]: k for k, r in enumerate(b["ids"])}
    both = sorted(set(ia) & set(ib))
    return both, a["X"][[ia[x] for x in both]], b["X"][[ib[x] for x in both]]


def top5(V, k):
    return [IDS[j] for j in np.argsort(-np.abs(V[:, k]))[:5]]


def tag(i):
    d = DOMAIN_OF.get(i)
    return f"{i}[{DJA[d]}]" if d else i


def pc1_vec(X):
    return A.pca(X)[1][:, 0]


def run(answers_dir, out_dir, B=1000, exp2_answers=None, exp2b_answers=None, figures=True, experiences_path=None):
    rng = np.random.default_rng(SEED)
    os.makedirs(out_dir, exist_ok=True)
    asg = json.load(open(experiences_path or os.path.join(HERE, "experiences_exp2c.json"), encoding="utf-8"))["assignments"]
    data = A.load(answers_dir, CONDITIONS_EXP2C)
    for path, conds_ in ((exp2_answers, CONDITIONS_EXP2), (exp2b_answers, CONDITIONS_EXP2B)):
        if path and os.path.isdir(path):
            other = A.load(path, conds_)
            for c in ("D1", "D2", "E1", "D2r"):
                if c in other and len(other[c]["X"]) >= 2:
                    data[c] = other[c]
    conds = [c for c in ("F1", "F2", "D1", "D2", "E1", "D2r") if c in data and len(data[c]["X"]) >= 2]
    meta = {**CONDITIONS_EXP2, **CONDITIONS_EXP2B, **CONDITIONS_EXP2C}
    L = ["# 実験 2c の結果 (analyze_exp2c.py が書いた)", "",
         "答えの数: " + ", ".join(f"{c} {len(data[c]['X']) if c in data else 0}/{CONDITIONS_EXP2C[c]['n']}" for c in CONDITIONS_EXP2C)
         + "。くらべる答え: " + (", ".join(f"{c} {len(data[c]['X'])}" for c in ("D1", "D2", "E1", "D2r") if c in conds) or "なし"), ""]
    res = {}

    # ---------- 問いごと ----------
    stats = {}
    for c in conds:
        m, s, mo = A.item_stats(data[c]["X"])
        stats[c] = {"mean": m, "sd": s, "modal": mo, "n": len(data[c]["X"])}
    with open(os.path.join(out_dir, "items.csv"), "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["item", "text", "norm", "domain"] + [f"{c}_{k}" for c in conds for k in ("mean", "sd", "modal")])
        for j, i in enumerate(IDS):
            w.writerow([i, TEXT[i], NORM[i], DOMAIN_OF.get(i, "")] +
                       [round(float(stats[c][k][j]), 3) for c in conds for k in ("mean", "sd", "modal")])
    norm = np.array([NORM[i] for i in IDS])
    di = {d: [IDS.index(i) for i in DOMAIN_ITEMS[d]] for d in DKEYS}
    ri = [IDS.index(i) for i in DOMAIN_REST]
    L += ["## 問いごとの数", "",
          "| 組 | n | SD の平均 (95% CI) | SD が 0 の問い | 規範との差 (符号つき, + = 厳しい) | 人ごとの平均点の SD | "
          + " | ".join(f"{DJA[d]} {len(DOMAIN_ITEMS[d])} 問" for d in DKEYS) + f" | ほか {len(DOMAIN_REST)} 問 |",
          "|---|---|---|---|---|---|" + "---|" * (len(DKEYS) + 1)]
    for c in conds:
        X = data[c]["X"]
        L.append(f"| {NAME[c]} ({meta[c]['model']}) | {len(X)} | {A.fmt(float(np.mean(stats[c]['sd'])))} "
                 f"{A.ci(A.boot(X, lambda Y: np.mean(Y.std(0, ddof=1)), B, rng))} | {int(np.sum(stats[c]['sd'] == 0))} | "
                 f"{float(np.mean(stats[c]['mean'] - norm)):+.2f} | {A.fmt(float(X.mean(1).std(ddof=1)))} | "
                 + " | ".join(f"{X[:, di[d]].mean():.2f}" for d in DKEYS) + f" | {X[:, ri].mean():.2f} |")
    L += ["", "領域の問い (prereg 4.): " + "; ".join(f"{DJA[d]} {' '.join(DOMAIN_ITEMS[d])}" for d in DKEYS) + "。", ""]

    # ---------- 主成分分析 ----------
    sets = {c: data[c]["X"] for c in conds if len(data[c]["X"]) >= 10}
    noise84 = A.noise_eig(HUMAN_N)
    noise_n = {}
    eig, Vs, match_rows, tops, rinfo = {}, {}, [], [], {}
    L += ["## 主成分分析", "",
          f"人間 (修士論文 表 3): 第 1 主成分の割合 {HUMAN_PC1:.3f}。平行分析の線 = でたらめな答え (同じ n・54 問) の固有値の平均。",
          "",
          "| 組 | n | 使った問い | 固有値 1〜5 | 第 1 の割合 | 第 1 の割合 (95% CI, n=84 に引き直し) | 厳しさの割合 (95% CI) | "
          "|r(厳しさ, 第 1 主成分の点)| (95% CI) | 平行分析の線をこえる数 | 50.3% に届く数 |",
          "|---|---|---|---|---|---|---|---|---|---|"]
    with open(os.path.join(out_dir, "eigen.csv"), "w", newline="", encoding="utf-8") as fe:
        we = csv.writer(fe)
        we.writerow(["set", "k", "eigenvalue", "share", "cumulative"])
        for k in range(5):
            we.writerow(["human_printed", k + 1, HUMAN_EIG[k], round(HUMAN_EIG[k] / P, 4), round(HUMAN_CUM_FROM_EIG[k], 4)])
        for c, X in sets.items():
            wv, V, used = A.pca(X)
            eig[c], Vs[c] = wv, V
            p = len(used)
            cum = np.cumsum(wv) / p
            for k in range(min(15, len(wv))):
                we.writerow([c, k + 1, round(float(wv[k]), 4), round(float(wv[k] / p), 4), round(float(cum[k]), 4)])
            if len(X) not in noise_n:
                noise_n[len(X)] = A.noise_eig(len(X))
            m_ = min(len(wv), len(noise_n[len(X)]))   # SD が 0 の問いを除くと、固有値は 54 より少ない (線は 54 問で作ったまま)
            above = wv[:m_] > noise_n[len(X)][:m_]
            npa = int(len(above) if above.all() else np.argmin(above))     # 前から続けて線をこえる数
            share_ci = A.boot(X, lambda Y: A.pc1_share(Y[:HUMAN_N]), B, rng)
            st, st_ci = E2.strict_share(X), A.boot(X, E2.strict_share, B, rng)
            r, r_ci = E2.strict_pc1_r(X), A.boot(X, E2.strict_pc1_r, B, rng)
            rinfo[c] = (r, r_ci, wv[0] / p, share_ci, npa)
            L.append(f"| {c} | {len(X)} | {p} | {', '.join(f'{v:.2f}' for v in wv[:5])} | {wv[0] / p:.3f} | {A.ci(share_ci)} | "
                     f"{A.fmt(st)} {A.ci(st_ci)} | {r:.3f} {A.ci(r_ci)} | {npa} | {A.n_to_reach(wv, p, HUMAN_CUM_FROM_EIG[4])} |")
            with open(os.path.join(out_dir, f"loadings_{c}.csv"), "w", newline="", encoding="utf-8") as fl:
                wl = csv.writer(fl)
                wl.writerow(["item"] + [f"pc{k + 1}" for k in range(A.KMAX)])
                for j, i in enumerate(IDS):
                    wl.writerow([i] + [round(float(V[j, k]), 4) for k in range(min(A.KMAX, V.shape[1]))])
            tops.append(f"- {c}: " + "; ".join(f"pc{k + 1}: " + " ".join(tag(i) for i in top5(V, k)) for k in range(5)))
            if c in ("F1", "F2", "D1"):
                rows, null_mean = A.match_all(V, rng)
                bo = []
                for _ in range(min(B, 300)):
                    _, Vb, _ = A.pca(X[rng.integers(0, len(X), len(X))])
                    bo.append([A.match_one(Vb, [i for i, _ in t], [np.sign(v) for _, v in t])[1] for _, _, _, t in HUMAN_PCS])
                lo, hi = np.percentile(np.array(bo), [2.5, 97.5], axis=0)
                for rr, a, b, (_, _, _, t) in zip(rows, lo, hi, HUMAN_PCS):
                    ov = [i for i in top5(V, rr["llm_pc"] - 1) if i in [x for x, _ in t]]
                    groups = {DOMAIN_OF.get(i, "rest") for i in ov}
                    rr.update({"set": c, "overlap_ci": f"[{a:.0f}, {b:.0f}]", "null_mean_overlap": round(null_mean, 2),
                               "overlap_items": " ".join(ov), "overlap_domains": " ".join(sorted(groups)),
                               "crosses_domains": bool(len(groups) >= 2)})
                    match_rows.append(rr)
    L += [""]
    L.append("- 平行分析の線をこえる数 = 第 1 主成分から続けて、固有値がでたらめな答えの線より大きい数。"
             "第 1 主成分の向きのそろい方 (D1 との |cos|) は、下の「探索: 第 1 主成分の向きのそろい方」。")
    L += ["", "### 主成分 1〜5 の上位 5 問 (|固有ベクトル|。[ ] は領域。領域のない問いは印なし)", ""] + tops + [""]
    keys = ["set", "human_pc", "name_ja", "name_en", "llm_pc", "overlap", "overlap_ci", "sign_agree", "p_null", "null_mean_overlap",
            "reproduced", "overlap_items", "overlap_domains", "crosses_domains"]
    if match_rows:
        with open(os.path.join(out_dir, "match.csv"), "w", newline="", encoding="utf-8") as fm:
            wm = csv.DictWriter(fm, fieldnames=keys)
            wm.writeheader()
            wm.writerows(match_rows)

    # ---------- H16・H19: 第 1 主成分の割合の対の差 ----------
    diff_rows, raw = [], {}
    L += ["## H16・H19: 第 1 主成分の割合は、出来事で下がるか (同じ暮らしの対の差)", "",
          "差 = 第 1 主成分の割合 (使った問いの数で割る。人数はそのまま) の差。CI は同じ暮らしの対を 1 組として引き直す。", "",
          "| くらべ | 対の数 | 割合 (前) | 割合 (後) | 差 (95% CI) |", "|---|---|---|---|---|"]
    for a, b in (("F2", "D1"), ("F1", "D1"), ("F2", "F1")):
        if a in conds and b in conds:
            both, Xa, Xb = pairs(data[a], data[b])
            if len(both) < 10:
                continue
            d0 = A.pc1_share(Xa) - A.pc1_share(Xb)
            bs = []
            for _ in range(B):
                s = rng.integers(0, len(both), len(both))
                bs.append(A.pc1_share(Xa[s]) - A.pc1_share(Xb[s]))
            lo, hi = np.percentile(bs, [2.5, 97.5])
            raw[(a, b)] = (d0, lo, hi)
            diff_rows.append({"a": a, "b": b, "n_pairs": len(both), "share_a": round(float(A.pc1_share(Xa)), 4),
                              "share_b": round(float(A.pc1_share(Xb)), 4), "diff": round(float(d0), 4), "ci_lo": round(float(lo), 4),
                              "ci_hi": round(float(hi), 4)})
            L.append(f"| {a} − {b} | {len(both)} | {A.pc1_share(Xb):.3f} ({b}) | {A.pc1_share(Xa):.3f} ({a}) | {d0:+.3f} [{lo:+.3f}, {hi:+.3f}] |")
    L.append("")
    if diff_rows:
        with open(os.path.join(out_dir, "share_diff.csv"), "w", newline="", encoding="utf-8") as fd:
            wd = csv.DictWriter(fd, fieldnames=list(diff_rows[0]))
            wd.writeheader()
            wd.writerows(diff_rows)
    dr = {k: {"diff": v[0], "ci_lo": v[1], "ci_hi": v[2]} for k, v in raw.items()}
    if ("F2", "D1") in dr:
        r = dr[("F2", "D1")]
        res["H16"] = bool(r["diff"] <= H16_D and r["ci_hi"] < 0)
        L.append(f"- **H16 (主):** F2 − D1 = {r['diff']:+.3f} [{r['ci_lo']:+.3f}, {r['ci_hi']:+.3f}] → "
                 + (f"支持 (差 ≤ {H16_D} で CI の上 < 0)" if res["H16"] else f"支持しない (差 ≤ {H16_D} で CI の上 < 0 にならない)"))
    if ("F2", "F1") in dr:
        r = dr[("F2", "F1")]
        res["H19"] = r["diff"] < 0
        L.append(f"- **H19:** F2 − F1 = {r['diff']:+.3f} [{r['ci_lo']:+.3f}, {r['ci_hi']:+.3f}] → "
                 + ("支持 (差 < 0。向きだけ。H16 と組で読む)" if res["H19"] else "支持しない (差 ≥ 0)"))
    if ("F1", "D1") in dr:
        r = dr[("F1", "D1")]
        L.append(f"- 探索 F1 − D1 = {r['diff']:+.3f} [{r['ci_lo']:+.3f}, {r['ci_hi']:+.3f}]")
    L.append("")

    # ---------- H17: 第 1 主成分は「厳しさ」か ----------
    L += ["## H17: 第 1 主成分は、まだ「厳しさ」(54 問の平均) そのものか", ""]
    for c in ("F2", "F1", "D1"):
        if c in rinfo:
            r, r_ci, _, _, _ = rinfo[c]
            L.append(f"- {c}: |r| = {r:.3f} {A.ci(r_ci)}")
    if "F2" in rinfo:
        r, r_ci, _, _, _ = rinfo["F2"]
        res["H17"] = r < H17_R and r_ci[1] < H17_HI
        L.append(f"- **H17:** F2 の |r| {r:.3f} {A.ci(r_ci)} → "
                 + (f"支持 (|r| < {H17_R} で CI の上 < {H17_HI})" if res["H17"] else f"支持しない (|r| < {H17_R} かつ CI の上 < {H17_HI} にならない)"))
    L.append("")

    # ---------- H18: 人間の 5 つの主成分 ----------
    if match_rows:
        L += ["## H18: 人間の 5 つの主成分が、いくつ出るか (実験 2 の H7 と同じ決まり: LLM の主成分 1〜10、重なり 3 以上・偶然の p < 0.05)", "",
              "「領域をまたぐ」= 重なった問いが、2 つ以上の領域 (領域のない問いは「ほか」として 1 つに数える) にわたる。"
              "1 つの領域の問いだけで重なったときは、入れた出来事の領域がそのまま出た見込みがある (prereg 8.・11.)。", "",
              "| 組 | 人間の主成分 | いちばん合う主成分 | 重なり (0〜5) (95% CI) | 符号の合う割合 | 偶然の p | 再現 | 重なった問い | 領域をまたぐ |",
              "|---|---|---|---|---|---|---|---|---|"]
        for rr in match_rows:
            L.append(f"| {rr['set']} | {rr['human_pc']} {rr['name_ja']} | pc{rr['llm_pc']} | {rr['overlap']} {rr['overlap_ci']} | "
                     f"{rr['sign_agree']} | {rr['p_null']} | {'はい' if rr['reproduced'] else 'いいえ'} | "
                     f"{' '.join(tag(i) for i in rr['overlap_items'].split()) or '—'} | {'はい' if rr['crosses_domains'] else 'いいえ'} |")
        L.append("")
        for c in ("F2", "F1", "D1"):
            rows = [rr for rr in match_rows if rr["set"] == c]
            if not rows:
                continue
            rep = [rr for rr in rows if rr["reproduced"]]
            cross = [rr for rr in rep if rr["crosses_domains"]]
            line = (f"再現 {len(rep)}/5 (" + ", ".join(rr["name_ja"] for rr in rep) + f")。そのうち領域をまたぐもの {len(cross)}")
            if c == "F2":
                res["H18"] = len(rep) >= H18_N
                L.append(f"- **H18 (F2):** {line} → " + (f"支持 ({H18_N} つ以上)" if res["H18"] else "支持しない"))
            else:
                L.append(f"- 参考 {c}: {line}")
        L.append("")

    # ---------- 効き目の確かめ: 出来事の向きは、その領域の問いを動かすか ----------
    manip_rows = []
    code = {c: np.array([[a[f"code_{c}"][d] for d in DKEYS] for a in asg], float) for c in ("F1", "F2")}

    def manip(a, b, F_of):
        both, Xa, Xb = pairs(data[a], data[b])
        if len(both) < 12:
            return None
        F = F_of(np.array([int(x) - 1 for x in both]))
        Y = np.column_stack([Xa[:, di[d]].mean(1) - Xb[:, di[d]].mean(1) for d in DKEYS]
                            + [Xa[:, ri].mean(1) - Xb[:, ri].mean(1), Xa.mean(1) - Xb.mean(1)])
        est = np.array([E2.ols(Y[:, q], F) for q in range(Y.shape[1])])          # (outcome, 1 + 5)
        bs, offd = [], []
        for _ in range(B):
            s = rng.integers(0, len(both), len(both))
            if np.linalg.matrix_rank(np.column_stack([np.ones(len(s)), F[s]])) < F.shape[1] + 1:
                continue
            e = np.array([E2.ols(Y[s, q], F[s]) for q in range(Y.shape[1])])
            bs.append(e)
            M = e[:5, 1:]
            offd.append([np.mean(np.diag(M)), (M.sum() - np.trace(M)) / 20])
        bs = np.array(bs)
        lo, hi = np.percentile(bs, [2.5, 97.5], axis=0)
        M = est[:5, 1:]
        diag_off = (float(np.mean(np.diag(M))), float((M.sum() - np.trace(M)) / 20))
        doff_ci = np.percentile(np.array(offd), [2.5, 97.5], axis=0)
        outs = DKEYS + ["rest", "all"]
        for q, o in enumerate(outs):
            for j, f in enumerate(["intercept"] + DKEYS):
                manip_rows.append({"pair": f"{a}-{b}", "outcome": o, "factor": f, "coef": round(float(est[q, j]), 4),
                                   "ci_lo": round(float(lo[q, j]), 4), "ci_hi": round(float(hi[q, j]), 4)})
        return len(both), est, lo, hi, diag_off, doff_ci

    specs = (("F1", "D1", lambda k: code["F1"][k], "F1 の出来事 (−1 / 0 / +1)"),
             ("F2", "D1", lambda k: code["F2"][k], "F2 の出来事 (−2〜+2)"),
             ("F2", "F1", lambda k: code["F2"][k] - code["F1"][k], "F2 で足した出来事 (F2 − F1 の数)"))
    mres = {}
    for a, b, fn, lab in specs:
        if a in conds and b in conds:
            m = manip(a, b, fn)
            if m:
                mres[(a, b)] = (m, lab)
    if mres:
        L += ["## 効き目の確かめ: 出来事の向きは、その領域の問いを動かすか (同じ暮らしの対の差)", "",
              "y = 領域ごとの問いの平均の差 (後 − 前)。説明の数 = 5 つの領域ごとの出来事の数 (困った・された・注意された = +1、"
              "困らなかった・助かった = −1、ない = 0。F2 は 2 つあれば ±2)。y を 5 つの数に回帰 (切片つきの最小二乗)。"
              "+ = 厳しくなる (5 = 重大な問題)。CI は対を引き直す。行 = y の領域、列 = 出来事の領域。対角 (太字) が自分の領域。", ""]
        for (a, b), ((n, est, lo, hi, (dg, of), dci), lab) in mres.items():
            judged = (a, b) == ("F1", "D1")
            L += [f"### {a} − {b} ({lab}、対 {n}){' — 判定するのはこの表の対角' if judged else ' — 探索'}", "",
                  "| y \\ 出来事 | " + " | ".join(DJA[d] for d in DKEYS) + " | 切片 |", "|---|" + "---|" * (len(DKEYS) + 1)]
            for q, o in enumerate(DKEYS + ["rest", "all"]):
                name = DJA[o] if o in DJA else ("ほかの 17 問" if o == "rest" else "54 問すべて")
                cells = []
                for j, d in enumerate(DKEYS):
                    t = f"{est[q, j + 1]:+.2f} [{lo[q, j + 1]:+.2f}, {hi[q, j + 1]:+.2f}]"
                    cells.append(f"**{t}**" if o == d else t)
                L.append(f"| {name} | " + " | ".join(cells) + f" | {est[q, 0]:+.2f} |")
            L += ["", f"- 対角の平均 {dg:+.3f} [{dci[0][0]:+.3f}, {dci[1][0]:+.3f}]・対角でないものの平均 (広がり) {of:+.3f} "
                      f"[{dci[0][1]:+.3f}, {dci[1][1]:+.3f}]" + (f"・広がり / 対角 = {of / dg:.2f}" if abs(dg) > 1e-9 else "")]
            if judged:
                ok = [d for j, d in enumerate(DKEYS) if lo[j, j + 1] > 0]
                res["MANIP"] = len(ok) >= MANIP_N
                L.append(f"- **効き目の確かめ (F1 − D1):** 自分の領域の係数の CI の下が 0 より上: {len(ok)}/5 ("
                         + ", ".join(DJA[d] for d in ok) + ") → " + (f"効いた ({MANIP_N} つ以上)" if res["MANIP"] else f"効いたとは言えない ({MANIP_N} つ未満)"))
            L.append("")
        with open(os.path.join(out_dir, "manip_coef.csv"), "w", newline="", encoding="utf-8") as fc:
            wc = csv.DictWriter(fc, fieldnames=list(manip_rows[0]))
            wc.writeheader()
            wc.writerows(manip_rows)

    # ---------- 探索: pc1 の向きのそろい方 ----------
    have = [c for c in ("F1", "F2", "D1", "D2", "E1", "D2r") if c in Vs]
    if len(have) >= 2:
        L += ["## 探索: 第 1 主成分の向きのそろい方 (固有ベクトルの |cos|)", "",
              "| | " + " | ".join(have) + " |", "|---|" + "---|" * len(have)]
        for c in have:
            L.append(f"| {c} | " + " | ".join(f"{abs(float(Vs[c][:, 0] @ Vs[e][:, 0])):.2f}" for e in have) + " |")
        L.append("")

    # ---------- わけ (探索。reasons_codebook.py の辞書で分ける) ----------
    rrows = []
    for c in ("F1", "F2", "D1"):
        if c not in conds:
            continue
        for rid, rs, x in zip(data[c]["ids"], data[c]["reasons"], data[c]["X"]):
            a = asg[int(rid.split("_")[1]) - 1]
            for i in REASON_ITEMS:
                d = REASON_DOMAIN[i]
                cv = a[f"code_{c}"][d] if c in ("F1", "F2") and d else 0
                rrows.append({"id": rid, "condition": c, "situation_id": a["situation_id"], "item": i, "item_domain": d or "",
                              "answer": int(x[IDS.index(i)]), "reason": (rs or {}).get(i, ""),
                              "own_domain_exp": "unfav" if cv > 0 else "fav" if cv < 0 else "none"})
    if rrows:
        with open(os.path.join(out_dir, "reasons.csv"), "w", newline="", encoding="utf-8") as fr:
            wr = csv.DictWriter(fr, fieldnames=list(rrows[0]))
            wr.writeheader()
            wr.writerows(rrows)
        for r in rrows:
            r["codes"] = RC.code(str(r["reason"]))
            r["family"] = RC.family(r["codes"])
        with open(os.path.join(out_dir, "reasons_coded.csv"), "w", newline="", encoding="utf-8") as fr:
            wr = csv.writer(fr)
            wr.writerow(["id", "condition", "item", "item_domain", "answer", "reason", "codes", "family", "own_domain_exp"])
            for r in rrows:
                wr.writerow([r["id"], r["condition"], r["item"], r["item_domain"], r["answer"], r["reason"], ";".join(r["codes"]),
                             r["family"], r["own_domain_exp"]])
        groups = [(c, [r for r in rrows if r["condition"] == c]) for c in ("D1", "F1", "F2")]
        groups += [(f"F1 その問いの領域の出来事 = {v}", [r for r in rrows if r["condition"] == "F1" and r["own_domain_exp"] == v])
                   for v in ("fav", "none", "unfav")]
        groups = [(g, rs) for g, rs in groups if rs]
        empty = sum(1 for r in rrows if not str(r["reason"]).strip())
        L += ["## 探索: わけ (5 問 × 人。reasons_codebook.py の辞書で分けた。辞書は実験 2 の答えを読んで作ったもの)", "",
              f"件数 {len(rrows)}、空 {empty}。わけを聞く 5 問の領域: " + ", ".join(f"{i} {DJA[d]}" for i, d in REASON_DOMAIN.items() if d)
              + "。fav = 困らなかった・助かった、unfav = 困った・された・注意された、none = その領域の出来事なし。", "", RC.table(groups, None), ""]

    # ---------- 判定のまとめ ----------
    verdict = lambda k: "—" if k not in res else ("支持" if res[k] else "支持しない")
    L[4:4] = ["## 判定のまとめ (決めた線のとおり)", "",
              f"- H16 (主。F2 の第 1 主成分の割合が D1 より下がる): {verdict('H16')}",
              f"- H17 (F2 の第 1 主成分が、厳しさそのものでなくなる): {verdict('H17')}",
              f"- H18 (F2 で人間の主成分が 2 つ以上出る): {verdict('H18')}",
              f"- H19 (F2 の割合が F1 より下): {verdict('H19')}",
              "- 効き目の確かめ (F1 − D1、3 つ以上の領域): " + ("—" if "MANIP" not in res else ("効いた" if res["MANIP"] else "効いたとは言えない")), ""]

    if figures and conds:
        plt = A.setup_mpl()
        if eig:
            A.fig_scree(plt, {c: eig[c] for c in ("F1", "F2", "D1", "D2", "E1") if c in eig}, noise84, os.path.join(out_dir, "fig_scree.png"),
                        labels={"F1": "F1 situation + 3 experiences / 暮らし + 出来事 3", "F2": "F2 situation + 6 experiences / 暮らし + 出来事 6",
                                "D1": "D1 situation / 暮らし", "D2": "D2 + download surroundings / ダウンロードの様子",
                                "E1": "E1 + borrowing surroundings / 借りた物の様子"})
        if rinfo:
            fig_share(plt, rinfo, os.path.join(out_dir, "fig_pc1_share.png"))
        if mres:
            fig_manip(plt, mres, os.path.join(out_dir, "fig_manip_coef.png"))
    with open(os.path.join(out_dir, "summary.md"), "w", encoding="utf-8") as f:
        f.write("\n".join(L) + "\n")
    return L


def fig_share(plt, rinfo, out):
    order = [c for c in ("D1", "D2", "E1", "D2r", "F1", "F2") if c in rinfo]
    fig, ax = plt.subplots(figsize=(7.5, 4.2))
    for k, c in enumerate(order):
        _, _, s, ci_, _ = rinfo[c]
        ax.plot([k, k], [ci_[0], ci_[1]], "-", color=A.COLORS[c], lw=2)
        ax.plot(k, s, "o", ms=8, color=A.COLORS[c])
    ax.axhline(HUMAN_PC1, color=A.INK, lw=1.2, ls="--")
    ax.text(len(order) - 0.6, HUMAN_PC1, f" human {HUMAN_PC1:.3f}\n 人間", va="center", fontsize=8, color=A.INK)
    ax.set_xticks(range(len(order)))
    ax.set_xticklabels([{"D1": "D1\n暮らし", "D2": "D2\n+DL の様子", "E1": "E1\n+借りた物の様子", "D2r": "D2r\nD2 再",
                         "F1": "F1\n+出来事 3", "F2": "F2\n+出来事 6"}[c] for c in order], fontsize=8)
    ax.set_xlim(-0.5, len(order) + 0.3)
    ax.set_ylabel("PC1 share / 第 1 主成分の割合")
    ax.set_title("PC1 share (95% CI, resampled to n=84) / 第 1 主成分の割合", fontsize=10, color=A.INK, loc="left")
    fig.tight_layout()
    fig.savefig(out, dpi=130)
    plt.close(fig)


def fig_manip(plt, mres, out):
    fig, ax = plt.subplots(figsize=(8.5, 4.8))
    cols = {("F1", "D1"): "#6250d6", ("F2", "D1"): "#d03b3b", ("F2", "F1"): "#eda100"}
    for q, (key, ((n, est, lo, hi, _, _), lab)) in enumerate(mres.items()):
        for j, d in enumerate(DKEYS):
            y = j - 0.25 + 0.25 * q
            ax.plot([lo[j, j + 1], hi[j, j + 1]], [y, y], "-", color=cols[key], lw=2)
            ax.plot(est[j, j + 1], y, "o", ms=6, color=cols[key], label=f"{key[0]} − {key[1]}" if j == 0 else None)
            off = [est[j, i + 1] for i in range(5) if i != j]
            ax.plot(off, [y] * 4, "x", ms=5, color=cols[key], alpha=0.5)
    ax.axvline(0, color=A.MUTED, lw=1)
    ax.set_yticks(range(len(DKEYS)))
    ax.set_yticklabels([f"{d}\n{DJA[d]}" for d in DKEYS], fontsize=8)
    ax.invert_yaxis()
    ax.set_xlabel("effect of +1 unfavorable experience on its domain items (o) and other domains (x) / 出来事 1 つの効き目 (o 自分の領域, x ほかの領域)",
                  fontsize=8)
    ax.set_title("Manipulation check: experiences move their own domain? / 出来事は自分の領域の問いを動かすか", fontsize=10, color=A.INK, loc="left")
    ax.legend(fontsize=8, frameon=False, loc="upper center", bbox_to_anchor=(0.5, -0.18), ncol=3)
    fig.tight_layout()
    fig.savefig(out, dpi=130, bbox_inches="tight")
    plt.close(fig)


if __name__ == "__main__":
    import argparse
    ap = argparse.ArgumentParser()
    ap.add_argument("--answers", default=os.path.join(HERE, "answers_exp2c"))
    ap.add_argument("--exp2", default=os.path.join(HERE, "answers_exp2"))
    ap.add_argument("--exp2b", default=os.path.join(HERE, "answers_exp2b"))
    ap.add_argument("--out", default=os.path.join(HERE, "out_exp2c"))
    ap.add_argument("--boot", type=int, default=1000)
    a = ap.parse_args()
    print("\n".join(run(a.answers, a.out, a.boot, exp2_answers=a.exp2, exp2b_answers=a.exp2b)))
