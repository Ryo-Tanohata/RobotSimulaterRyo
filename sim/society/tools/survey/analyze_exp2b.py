"""論文 2・実験 2b: answers_exp2b/*.json (E1・D2r) を読み、事前登録 (docs/research/humanity/paper2_exp2b_prereg.md の 7.・8.) のとおりに数える。

    python3 analyze_exp2b.py [--answers DIR] [--exp2 DIR] [--out DIR] [--boot 1000]

部品 (主成分分析・一致の点・ブートストラップ・図) は analyze.py と analyze_exp2.py のものをそのまま使う。
くらべる相手: 人間 (修士論文 表 3) と、実験 2 の答え (answers_exp2/ の D1・D2。E1_k・D2r_k は D1_k・D2_k と同じ暮らし)。
書くもの (out_exp2b/):
- summary.md   仮説 H12〜H15 の数と判定 (決めた線のとおり)、探索の数
- items.csv / eigen.csv / loadings_<組>.csv / match.csv / match_k2.csv / h14_coef.csv / reasons.csv / reasons_coded.csv
- fig_scree.png / fig_item_means.png / fig_h14_coef.png
"""
import csv
import os

import numpy as np

import analyze as A
import analyze_exp2 as E2
import reasons_codebook as RC
from items import (BORROW, CONDITIONS_EXP2, CONDITIONS_EXP2B, DOWNLOAD, GRAY, HUMAN_CUM_FROM_EIG, HUMAN_N, HUMAN_PCS, IDS, NORM,
                   REASON_ITEMS, SURROUND, TEXT)

HERE = os.path.dirname(os.path.abspath(__file__))
P = len(IDS)
SEED = 20261031
# 決めの線 (prereg 8.)
H12_K = 2          # H12: 人間の pc2 (所有意識) を、LLM の主成分 1〜2 の中だけで探す (偶然の基準も 1〜2 で作る)
H13_MAX = 1        # H13: E1 の pc1 の上位 5 問と、人間の pc1 (権利意識) の上位 5 問の重なりがこれ以下
H14_COEF = -0.1    # H14: 借りた物の 5 問の対の差 (E1 − D1) の係数がこれ以下で、CI の上が 0 未満
H14_FACTORS = ["everyone", "no_arrest"]   # H14 で判定する様子 (weak・easy は探索)
HUMAN_PC1_ITEMS = [i for i, _ in HUMAN_PCS[0][3]]
SURROUND_JA = dict(SURROUND)


def pairs(a, b):
    """同じ暮らしの対: (番号の list, a の行, b の行)。"""
    ia = {r.split("_")[1]: k for k, r in enumerate(a["ids"])}
    ib = {r.split("_")[1]: k for k, r in enumerate(b["ids"])}
    both = sorted(set(ia) & set(ib))
    return both, a["X"][[ia[x] for x in both]], b["X"][[ib[x] for x in both]]


def top5(V, k):
    return [IDS[j] for j in np.argsort(-np.abs(V[:, k]))[:5]]


def run(answers_dir, out_dir, B=1000, exp2_answers=None, figures=True, situations_path=None):
    import json
    rng = np.random.default_rng(SEED)
    os.makedirs(out_dir, exist_ok=True)
    ss = json.load(open(situations_path or os.path.join(HERE, "situations.json"), encoding="utf-8"))["situations"]
    data = A.load(answers_dir, CONDITIONS_EXP2B)
    e2 = A.load(exp2_answers, CONDITIONS_EXP2) if exp2_answers and os.path.isdir(exp2_answers) else None
    for c in ("D1", "D2"):
        if e2 is not None and len(e2[c]["X"]) >= 2:
            data[c] = e2[c]
    conds = [c for c in ("E1", "D2r", "D1", "D2") if c in data and len(data[c]["X"]) >= 2]
    meta = {**CONDITIONS_EXP2, **CONDITIONS_EXP2B}
    name = {"E1": "E1 (所有の様子)", "D2r": "D2r (D2 のくり返し)", "D1": "実験 2 D1 (暮らしだけ)", "D2": "実験 2 D2 (暮らし + ダウンロードの様子)"}

    L = ["# 実験 2b の結果 (analyze_exp2b.py が書いた)", "",
         "答えの数: " + ", ".join(f"{c} {len(data[c]['X']) if c in data else 0}/{CONDITIONS_EXP2B[c]['n']}" for c in CONDITIONS_EXP2B)
         + ("。くらべる実験 2: " + ", ".join(f"{c} {len(data[c]['X'])}" for c in ("D1", "D2") if c in conds) if e2 is not None else "。実験 2 の答えなし"), ""]

    # ---------- 問いごと ----------
    stats = {}
    for c in conds:
        m, s, mo = A.item_stats(data[c]["X"])
        stats[c] = {"mean": m, "sd": s, "modal": mo, "n": len(data[c]["X"])}
    with open(os.path.join(out_dir, "items.csv"), "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["item", "text", "norm", "gray", "download", "borrow"] + [f"{c}_{k}" for c in conds for k in ("mean", "sd", "modal")])
        for j, i in enumerate(IDS):
            w.writerow([i, TEXT[i], NORM[i], int(i in GRAY), int(i in DOWNLOAD), int(i in BORROW)] +
                       [round(float(stats[c][k][j]), 3) for c in conds for k in ("mean", "sd", "modal")])
    norm = np.array([NORM[i] for i in IDS])
    gi, di, bi = ([IDS.index(i) for i in g] for g in (GRAY, DOWNLOAD, BORROW))
    L += ["## 問いごとの数", "",
          "| 組 | n | SD の平均 (95% CI) | SD が 0 の問い | 規範との差 (符号つき, + = 厳しい) | 人ごとの平均点の SD | グレーゾーン 14 問の平均 | ダウンロード 5 問 | 借りた物 5 問 |",
          "|---|---|---|---|---|---|---|---|---|"]
    for c in conds:
        X = data[c]["X"]
        L.append(f"| {name[c]} ({meta[c]['model']}) | {len(X)} | {A.fmt(float(np.mean(stats[c]['sd'])))} "
                 f"{A.ci(A.boot(X, lambda Y: np.mean(Y.std(0, ddof=1)), B, rng))} | {int(np.sum(stats[c]['sd'] == 0))} | "
                 f"{float(np.mean(stats[c]['mean'] - norm)):+.2f} | {A.fmt(float(X.mean(1).std(ddof=1)))} | "
                 f"{X[:, gi].mean():.2f} | {X[:, di].mean():.2f} | {X[:, bi].mean():.2f} |")
    L += ["", f"借りた物の 5 問 (H14): {' '.join(BORROW)}。ダウンロードの 5 問: {' '.join(DOWNLOAD)}。", ""]

    # ---------- 主成分分析 ----------
    sets = {c: data[c]["X"] for c in conds if len(data[c]["X"]) >= 10}
    noise84 = A.noise_eig(HUMAN_N)
    eig, Vs, match_rows, match_k2, tops, share_lines = {}, {}, [], [], [], []
    L += ["## 主成分分析", "",
          "| 組 | n | 使った問い | 固有値 1〜5 | 第 1 の割合 (95% CI, n=84 に引き直し) | 厳しさの割合 (95% CI) | |r(厳しさ, 第 1 主成分の点)| | 50.3% に届く数 |",
          "|---|---|---|---|---|---|---|---|"]
    with open(os.path.join(out_dir, "eigen.csv"), "w", newline="", encoding="utf-8") as fe:
        we = csv.writer(fe)
        we.writerow(["set", "k", "eigenvalue", "share", "cumulative"])
        for c, X in sets.items():
            wv, V, used = A.pca(X)
            eig[c], Vs[c] = wv, V
            p = len(used)
            cum = np.cumsum(wv) / p
            for k in range(min(15, len(wv))):
                we.writerow([c, k + 1, round(float(wv[k]), 4), round(float(wv[k] / p), 4), round(float(cum[k]), 4)])
            share_ci = A.boot(X, lambda Y: A.pc1_share(Y[:HUMAN_N]), B, rng)
            st, st_ci = E2.strict_share(X), A.boot(X, E2.strict_share, B, rng)
            L.append(f"| {c} | {len(X)} | {p} | {', '.join(f'{v:.2f}' for v in wv[:5])} | {wv[0] / p:.3f} {A.ci(share_ci)} | "
                     f"{A.fmt(st)} {A.ci(st_ci)} | {E2.strict_pc1_r(X):.3f} | {A.n_to_reach(wv, p, HUMAN_CUM_FROM_EIG[4])} |")
            with open(os.path.join(out_dir, f"loadings_{c}.csv"), "w", newline="", encoding="utf-8") as fl:
                wl = csv.writer(fl)
                wl.writerow(["item"] + [f"pc{k + 1}" for k in range(A.KMAX)])
                for j, i in enumerate(IDS):
                    wl.writerow([i] + [round(float(V[j, k]), 4) for k in range(min(A.KMAX, V.shape[1]))])
            tops.append(f"- {c} の上位 5 問 (|固有ベクトル|): " + ", ".join(f"pc{k + 1}: " + " ".join(top5(V, k)) for k in range(3)))
            # 実験 2 の H7 と同じ決まり (LLM の主成分 1〜10)
            rows, null_mean = A.match_all(V, rng)
            # H12 の決まり (LLM の主成分 1〜2 だけ。偶然の基準も 1〜2)
            rows2, null_mean2 = A.match_all(V, rng, kmax=H12_K)
            bo, bo2 = [], []
            for _ in range(min(B, 300)):
                _, Vb, _ = A.pca(X[rng.integers(0, len(X), len(X))])
                bo.append([A.match_one(Vb, [i for i, _ in t], [np.sign(v) for _, v in t])[1] for _, _, _, t in HUMAN_PCS])
                bo2.append([A.match_one(Vb, [i for i, _ in t], [np.sign(v) for _, v in t], H12_K)[1] for _, _, _, t in HUMAN_PCS])
            for rs, bb, nm, out in ((rows, bo, null_mean, match_rows), (rows2, bo2, null_mean2, match_k2)):
                lo, hi = np.percentile(np.array(bb), [2.5, 97.5], axis=0)
                for rr, a, b in zip(rs, lo, hi):
                    rr.update({"set": c, "overlap_ci": f"[{a:.0f}, {b:.0f}]", "null_mean_overlap": round(nm, 2)})
                    out.append(rr)
            if c == "E1":
                share_lines.append(f"- 探索 E1: 第 1 主成分の割合 {wv[0] / p:.3f} {A.ci(share_ci)}、厳しさの割合 {A.fmt(st)} {A.ci(st_ci)} "
                                   f"(実験 2 D2 は 0.250・0.243、D1 は 0.228・0.223。人間の第 1 主成分の割合 0.268)")
    L += [""] + share_lines + [""] + tops + [""]
    keys = ["set", "human_pc", "name_ja", "name_en", "llm_pc", "overlap", "overlap_ci", "sign_agree", "p_null", "null_mean_overlap", "reproduced"]
    for fn, rows in (("match.csv", match_rows), ("match_k2.csv", match_k2)):
        if rows:
            with open(os.path.join(out_dir, fn), "w", newline="", encoding="utf-8") as fm:
                wm = csv.DictWriter(fm, fieldnames=keys)
                wm.writeheader()
                wm.writerows(rows)

    def row_of(rows, s, pc):
        x = [r for r in rows if r["set"] == s and r["human_pc"] == pc]
        return x[0] if x else None

    # ---------- H12・H13・H15 ----------
    L += ["## H12・H13・H15: どの主成分が、人間のどの意識と合うか", ""]
    if match_k2:
        L += ["### LLM の主成分 1〜2 だけで探したとき (H12 の決まり。偶然の基準も 1〜2)", "",
              "| 組 | 人間の主成分 | いちばん合う主成分 | 重なり (0〜5) (95% CI) | 符号の合う割合 | 偶然の p | 再現 |", "|---|---|---|---|---|---|---|"]
        for rr in match_k2:
            L.append(f"| {rr['set']} | {rr['human_pc']} {rr['name_ja']} | pc{rr['llm_pc']} | {rr['overlap']} {rr['overlap_ci']} | "
                     f"{rr['sign_agree']} | {rr['p_null']} | {'はい' if rr['reproduced'] else 'いいえ'} |")
        L.append("")
    if match_rows:
        L += ["### LLM の主成分 1〜10 から探したとき (実験 2 の H7 と同じ決まり。H15 はこちら)", "",
              "| 組 | 人間の主成分 | いちばん合う主成分 | 重なり (0〜5) (95% CI) | 符号の合う割合 | 偶然の p | 再現 |", "|---|---|---|---|---|---|---|"]
        for rr in match_rows:
            L.append(f"| {rr['set']} | {rr['human_pc']} {rr['name_ja']} | pc{rr['llm_pc']} | {rr['overlap']} {rr['overlap_ci']} | "
                     f"{rr['sign_agree']} | {rr['p_null']} | {'はい' if rr['reproduced'] else 'いいえ'} |")
        L.append("")
    L += ["### 第 1 主成分の上位 5 問と、人間の pc1 (権利意識: " + " ".join(HUMAN_PC1_ITEMS) + ") の重なり (H13)", "",
          "| 組 | 第 1 主成分の上位 5 問 | 重なった問い | 重なりの数 |", "|---|---|---|---|"]
    for c in Vs:
        t = top5(Vs[c], 0)
        ov = [i for i in t if i in HUMAN_PC1_ITEMS]
        L.append(f"| {c} | {' '.join(t)} | {' '.join(ov) or '—'} | {len(ov)} |")
    L.append("")
    res = {}
    r12 = row_of(match_k2, "E1", "pc2")
    if r12:
        res["H12"] = r12["reproduced"]
        L.append(f"- **H12 (E1):** 人間の pc2 (所有意識) に、E1 の pc{r12['llm_pc']} がいちばん合う (1〜2 の中で)。重なり {r12['overlap']} "
                 f"{r12['overlap_ci']}、偶然の p {r12['p_null']} → " + ("支持 (重なり 3 以上で p < 0.05)" if r12["reproduced"] else "支持しない"))
    if "E1" in Vs:
        ov = len([i for i in top5(Vs["E1"], 0) if i in HUMAN_PC1_ITEMS])
        res["H13"] = ov <= H13_MAX
        L.append(f"- **H13 (E1):** E1 の pc1 の上位 5 問と人間の pc1 の重なり {ov} → "
                 + (f"支持 ({H13_MAX} 以下。第 1 の軸はダウンロード・Wi-Fi から離れた)" if ov <= H13_MAX else f"支持しない ({H13_MAX} をこえる)"))
    r15 = row_of(match_rows, "D2r", "pc1")
    if r15:
        ok = r15["reproduced"] and r15["llm_pc"] == 1
        res["H15"] = ok
        L.append(f"- **H15 (D2r):** 人間の pc1 (権利意識) にいちばん合うのは D2r の pc{r15['llm_pc']}。重なり {r15['overlap']} {r15['overlap_ci']}、"
                 f"偶然の p {r15['p_null']} → " + ("支持 (pc1 で、重なり 3 以上・p < 0.05。D2 と同じ)" if ok else
                                                 "支持しない" + (" (再現したが pc1 ではない)" if r15["reproduced"] else "")))
    r2 = row_of(match_rows, "D2", "pc1")
    if r2:
        L.append(f"- 参考 (同じ手順で数え直した実験 2 D2): 人間の pc1 に pc{r2['llm_pc']}、重なり {r2['overlap']}、p {r2['p_null']}、"
                 f"再現 {'はい' if r2['reproduced'] else 'いいえ'} (実験 2 の summary は pc1・3・0.015。p は偶然の基準のくじで少しゆれる)")
    L.append("")

    # ---------- H14: 借りた物の様子 (E1 − D1、同じ暮らしの対) ----------
    coef_rows = []

    def paired_reg(a, b, label):
        both, Xa, Xb = pairs(data[a], data[b])
        if len(both) < 8:
            return None
        F = np.array([[ss[int(x) - 1]["surround"][k] for k, _ in SURROUND] for x in both], float)
        other = [j for j in range(P) if j not in set(gi) | set(bi) | set(di)]
        outs = {"borrow": Xa[:, bi].mean(1) - Xb[:, bi].mean(1), "gray": Xa[:, gi].mean(1) - Xb[:, gi].mean(1),
                "download": Xa[:, di].mean(1) - Xb[:, di].mean(1), "other": Xa[:, other].mean(1) - Xb[:, other].mean(1)}
        est = {k: E2.ols(y, F) for k, y in outs.items()}
        cis = {k: E2.boot_ols(y, F, B, rng) for k, y in outs.items()}
        for key in outs:
            for j, (k, ja) in enumerate(SURROUND):
                coef_rows.append({"pair": label, "outcome": key, "factor": k, "factor_ja": ja, "coef": round(float(est[key][j + 1]), 4),
                                  "ci_lo": round(float(cis[key][0][j + 1]), 4), "ci_hi": round(float(cis[key][1][j + 1]), 4)})
            coef_rows.append({"pair": label, "outcome": key, "factor": "intercept", "factor_ja": "切片", "coef": round(float(est[key][0]), 4),
                              "ci_lo": round(float(cis[key][0][0]), 4), "ci_hi": round(float(cis[key][1][0]), 4)})
        return len(both), est, cis

    L += ["## H14: 借りた物の様子は、借りた物の 5 問を「問題でない」へ動かすか (E1 − D1、同じ暮らしの対)", "",
          f"y = 借りた物 5 問 ({' '.join(BORROW)}) の平均の差 (E1 − D1)。y を 4 つの様子 (1 = はみ出しやすい側) に回帰 (切片つきの最小二乗)。"
          "CI は対を引き直す。判定するのは「みんながやっている」「捕まった人を聞いたことがない」の 2 つ (1 つずつ)。ほかは探索。", ""]
    reg = {}
    for a, b, label in (("E1", "D1", "E1-D1"), ("D2", "D1", "D2-D1"), ("D2r", "D1", "D2r-D1"), ("E1", "D2", "E1-D2")):
        if a in conds and b in conds:
            r = paired_reg(a, b, label)
            if r:
                reg[label] = r
    if "E1-D1" in reg:
        n, est, cis = reg["E1-D1"]
        cell = lambda key, j: f"{est[key][j]:+.3f} [{cis[key][0][j]:+.3f}, {cis[key][1][j]:+.3f}]"
        L += [f"対の数 {n}。", "", "| 様子 | 借りた物 5 問 (主) 係数 (95% CI) | 判定 | グレーゾーン 14 問 (探索) | ダウンロード 5 問 (探索。動かない見込み) | ほかの問い (探索) |",
              "|---|---|---|---|---|---|"]
        for j, (k, ja) in enumerate(SURROUND):
            b, hi = est["borrow"][j + 1], cis["borrow"][1][j + 1]
            if k in H14_FACTORS:
                sup = b <= H14_COEF and hi < 0
                res[f"H14_{k}"] = sup
                verdict = "支持 (係数 ≤ −0.1 で CI の上 < 0)" if sup else "支持しない"
            else:
                verdict = "(探索。判定しない)"
            L.append(f"| {ja} | {cell('borrow', j + 1)} | {verdict} | {cell('gray', j + 1)} | {cell('download', j + 1)} | {cell('other', j + 1)} |")
        L += ["", f"- 切片 (4 つともはみ出しにくい側): 借りた物 {cell('borrow', 0)}・ダウンロード {cell('download', 0)}"]
        for k in H14_FACTORS:
            L.append(f"- **H14 {SURROUND_JA[k]}:** " + ("支持" if res[f"H14_{k}"] else "支持しない"))
        L.append("")
    what = {"D2-D1": "ダウンロードの様子", "D2r-D1": "ダウンロードの様子・2 回目",
            "E1-D2": "同じ 0/1 で中身だけが違う。負 = 借りた物の様子のほうがゆるい"}
    for label in ("D2-D1", "D2r-D1", "E1-D2"):
        if label in reg:
            n, est, cis = reg[label]
            L.append(f"- 探索 {label} ({what[label]}、対 {n}): " + "; ".join(
                f"{ja}: 借りた物 {est['borrow'][j + 1]:+.2f} [{cis['borrow'][0][j + 1]:+.2f}, {cis['borrow'][1][j + 1]:+.2f}]・"
                f"ダウンロード {est['download'][j + 1]:+.2f} [{cis['download'][0][j + 1]:+.2f}, {cis['download'][1][j + 1]:+.2f}]・"
                f"グレーゾーン {est['gray'][j + 1]:+.2f} [{cis['gray'][0][j + 1]:+.2f}, {cis['gray'][1][j + 1]:+.2f}]"
                for j, (k, ja) in enumerate(SURROUND)))
    if coef_rows:
        with open(os.path.join(out_dir, "h14_coef.csv"), "w", newline="", encoding="utf-8") as fc:
            wc = csv.DictWriter(fc, fieldnames=list(coef_rows[0]))
            wc.writeheader()
            wc.writerows(coef_rows)
    L.append("")

    # ---------- 探索: グレーゾーン・ダウンロード・借りた物の問いごと ----------
    show = [c for c in ("D1", "D2", "D2r", "E1") if c in conds]
    if show:
        L += ["## 探索: グレーゾーン 14 問・ダウンロード 5 問・借りた物 5 問の平均 (問いごと)", "",
              "| 問い | 規範 | " + " | ".join(show) + " |", "|---|---|" + "---|" * len(show)]
        for i in sorted(set(GRAY) | set(DOWNLOAD) | set(BORROW), key=IDS.index):
            j = IDS.index(i)
            tag = ("G" if i in GRAY else "") + ("D" if i in DOWNLOAD else "") + ("B" if i in BORROW else "")
            L.append(f"| {i} ({tag}) | {NORM[i]} | " + " | ".join(f"{stats[c]['mean'][j]:.2f}" for c in show) + " |")
        L += ["", "G = グレーゾーン、D = ダウンロード、B = 借りた物。", ""]

    # ---------- 探索: D2 と D2r (同じ紙の 2 回目) のそろい方 ----------
    if "D2" in conds and "D2r" in conds:
        both, X2, Xr = pairs(data["D2"], data["D2r"])
        if len(both) >= 5:
            m2, mr = X2.mean(1), Xr.mean(1)
            rr = float(np.corrcoef(m2, mr)[0, 1]) if m2.std() > 0 and mr.std() > 0 else float("nan")
            same = float(np.mean(X2 == Xr))
            im = float(np.corrcoef(X2.mean(0), Xr.mean(0))[0, 1])
            L += ["## 探索: D2 と D2r (同じ紙をもう 1 回) のそろい方", "",
                  f"- 対 {len(both)}。同じ人・同じ問いで同じ数を答えた割合 {same:.2f}。人ごとの厳しさ (54 問の平均) の相関 {rr:+.2f}。"
                  f"問いごとの平均の相関 {im:+.2f}、平均の差の |平均| {float(np.mean(np.abs(X2.mean(0) - Xr.mean(0)))):.3f}"]
            if "D2" in Vs and "D2r" in Vs:
                cos = [abs(float(Vs["D2"][:, k] @ Vs["D2r"][:, k])) for k in range(3)]
                L.append("- 固有ベクトルの |cos| (D2 と D2r、同じ番号どうし): " + ", ".join(f"pc{k + 1} {v:.2f}" for k, v in enumerate(cos)))
            L.append("")

    # ---------- わけ (探索。reasons_codebook.py の辞書で分ける) ----------
    rrows = []
    for c in ("E1", "D2r"):
        if c not in conds:
            continue
        for rid, rs, x in zip(data[c]["ids"], data[c]["reasons"], data[c]["X"]):
            s = ss[int(rid.split("_")[1]) - 1]
            for i in REASON_ITEMS:
                rrows.append({"id": rid, "condition": c, "situation_id": s["situation_id"], "item": i,
                              "answer": int(x[IDS.index(i)]), "reason": (rs or {}).get(i, ""),
                              **{f"s_{k}": s["surround"][k] for k, _ in SURROUND}})
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
            wr.writerow(["id", "condition", "item", "answer", "reason", "codes", "family"] + [f"s_{k}" for k, _ in SURROUND])
            for r in rrows:
                wr.writerow([r["id"], r["condition"], r["item"], r["answer"], r["reason"], ";".join(r["codes"]), r["family"]]
                            + [r[f"s_{k}"] for k, _ in SURROUND])
        groups = [(c, [r for r in rrows if r["condition"] == c]) for c in ("E1", "D2r")]
        groups += [(f"E1 {SURROUND_JA['everyone']} = {v}", [r for r in rrows if r["condition"] == "E1" and r["s_everyone"] == v]) for v in (0, 1)]
        groups = [(g, rs) for g, rs in groups if rs]
        empty = sum(1 for r in rrows if not str(r["reason"]).strip())
        L += ["## 探索: わけ (5 問 × 人。reasons_codebook.py の辞書で分けた。辞書は実験 2 の答えを読んで作ったもの)", "",
              f"件数 {len(rrows)}、空 {empty}。実験 2 の数は out_exp2/reasons_summary.md。", "", RC.table(groups, None), ""]

    # ---------- 判定のまとめ ----------
    verdict = lambda k: "—" if k not in res else ("支持" if res[k] else "支持しない")
    L[4:4] = ["## 判定のまとめ (決めた線のとおり)", "",
              f"- H12 (E1 の pc1〜pc2 に所有意識): {verdict('H12')}", f"- H13 (E1 の pc1 が権利意識でない): {verdict('H13')}",
              f"- H14 みんながやっている: {verdict('H14_everyone')}", f"- H14 捕まった人を聞いたことがない: {verdict('H14_no_arrest')}",
              f"- H15 (D2r の pc1 に権利意識): {verdict('H15')}", ""]

    if figures and conds:
        plt = A.setup_mpl()
        A.fig_items(plt, stats, conds, "mean", "mean / 平均 (5 = serious … 1 = none)",
                    "Exp 2b item means vs norm / 実験 2b の問いごとの平均と規範", os.path.join(out_dir, "fig_item_means.png"), norm=True, meta=meta)
        if eig:
            A.fig_scree(plt, eig, noise84, os.path.join(out_dir, "fig_scree.png"),
                        labels={"E1": "E1 situation + borrowing surroundings / 暮らし + 借りた物の様子",
                                "D2r": "D2r = D2 again / D2 のくり返し", "D1": "D1 situation / 暮らし",
                                "D2": "D2 situation + download surroundings / 暮らし + ダウンロードの様子"})
        if any(r["pair"] == "E1-D1" for r in coef_rows):
            fig_h14(plt, [r for r in coef_rows if r["pair"] == "E1-D1"], os.path.join(out_dir, "fig_h14_coef.png"))
    with open(os.path.join(out_dir, "summary.md"), "w", encoding="utf-8") as f:
        f.write("\n".join(L) + "\n")
    return L


def fig_h14(plt, rows, out):
    fig, ax = plt.subplots(figsize=(8.5, 4.8))
    keys = [("borrow", "borrowing 5 items / 借りた物 (主)", "#eda100"), ("gray", "gray-zone 14 / グレーゾーン", "#2a78d6"),
            ("download", "download 5 / ダウンロード", "#eb6834")]
    for j, (k, ja) in enumerate(SURROUND):
        for q, (key, lab, col) in enumerate(keys):
            r = [x for x in rows if x["outcome"] == key and x["factor"] == k][0]
            y = j - 0.22 + 0.22 * q
            ax.plot([r["ci_lo"], r["ci_hi"]], [y, y], "-", color=col, lw=2)
            ax.plot(r["coef"], y, "o", ms=6, color=col, label=lab if j == 0 else None)
    ax.axvline(0, color=A.MUTED, lw=1)
    ax.set_yticks(range(len(SURROUND)))
    ax.set_yticklabels([f"{k}\n{ja}" for k, ja in SURROUND], fontsize=8)
    ax.invert_yaxis()
    ax.set_xlabel("effect on mean (E1 − D1), < 0 = less problematic / 平均の動き (負 = 問題でない側)", fontsize=9)
    ax.set_title("H14: borrowing surroundings (E1) / 借りた物の様子", fontsize=10, color=A.INK, loc="left")
    ax.legend(fontsize=8, frameon=False, loc="upper center", bbox_to_anchor=(0.5, -0.16), ncol=3)
    fig.tight_layout()
    fig.savefig(out, dpi=130, bbox_inches="tight")
    plt.close(fig)


if __name__ == "__main__":
    import argparse
    ap = argparse.ArgumentParser()
    ap.add_argument("--answers", default=os.path.join(HERE, "answers_exp2b"))
    ap.add_argument("--exp2", default=os.path.join(HERE, "answers_exp2"))
    ap.add_argument("--out", default=os.path.join(HERE, "out_exp2b"))
    ap.add_argument("--boot", type=int, default=1000)
    a = ap.parse_args()
    print("\n".join(run(a.answers, a.out, a.boot, exp2_answers=a.exp2)))
