"""論文 2・実験 2: answers_exp2/*.json を読み、事前登録 (docs/research/humanity/paper2_exp2_prereg.md の 7.・8.) のとおりに数える。

    python3 analyze.py --experiment 2 [--answers DIR] [--out DIR] [--boot 1000]
    (python3 analyze_exp2.py でも同じ)

数え方の部品 (主成分分析・一致の点・ブートストラップ・図) は analyze.py のものをそのまま使う (実験 1 と同じ手順でくらべるため)。
くらべる相手: 人間 (修士論文 表 3) と、実験 1 の答え (answers/ の C1・C4。あれば)。
書くもの (out_exp2/):
- summary.md   仮説 H6〜H11 の数と判定 (決めた線のとおり)、探索の数
- items.csv / eigen.csv / loadings_<組>.csv / match.csv / h8_coef.csv / reasons.csv
- fig_item_sd.png / fig_item_means.png / fig_scree.png / fig_h8_coef.png / fig_h9_download.png
"""
import csv
import json
import os

import numpy as np

import analyze as A
from items import (CONDITIONS, CONDITIONS_EXP2, DOWNLOAD, GRAY, HUMAN_CUM_FROM_EIG, HUMAN_EIG, HUMAN_N, HUMAN_PCS, IDS, NORM,
                   REASON_ITEMS, SURROUND, TEXT)

HERE = os.path.dirname(os.path.abspath(__file__))
P = len(IDS)
SEED = 20261030
# 決めの線 (prereg 8.)。実験 1 の数は out/summary.md (実験 1 の答え) から写した
EXP1_C1_PC1 = 0.392      # H6: 実験 1 C1 の第 1 主成分の割合 (点)
EXP1_C1_STRICT = 0.391   # H10: 実験 1 C1 の「厳しさの割合」(点。下の strict_share で計算)
EXP1_C4_SD = 0.137       # H11: 実験 1 C4 (opus・人格なし) の問いの SD の平均
H7_N = 2                 # H7: 人間の 5 つの主成分のうち、再現 (analyze.match_all と同じ決まり) がこの数以上
H9_D = -0.2              # H9: ダウンロードの 5 問の平均の差 (弱い側 − 働いてゆとり側) がこれ以下で、CI の上が 0 未満
H9_MIN_N = 15            # H9: どちらかの組がこれより少なければ「判定できない」
HUMAN_PC1 = HUMAN_EIG[0] / P


def strict_share(X):
    """「厳しさ」(人ごとの 54 問の平均) が、標準化した問いのばらつきのうち、どれだけを説明するか
    = 問いごとの corr(問い, 人ごとの平均)^2 の平均 (SD が 0 の問いは除く)。1 本の合成の点が説明できる割合なので、
    第 1 主成分の割合を超えない。人間はこの値が 0.268 (人間の第 1 主成分の割合) 以下。"""
    m = X.mean(1)
    sd = X.std(0, ddof=1)
    used = np.where(sd > 0)[0]
    if m.std() == 0 or len(used) == 0:
        return None
    r = np.array([np.corrcoef(X[:, j], m)[0, 1] for j in used])
    return float(np.mean(r ** 2))


def strict_pc1_r(X):
    """人ごとの平均 (厳しさ) と、第 1 主成分の点 (標準化した問い × 固有ベクトル) の相関の絶対値。"""
    w, V, used = A.pca(X)
    sd = X.std(0, ddof=1)
    Z = (X[:, used] - X[:, used].mean(0)) / sd[used]
    return float(abs(np.corrcoef(X.mean(1), Z @ V[used, 0])[0, 1]))


def ols(y, F):
    M = np.column_stack([np.ones(len(y)), F])
    return np.linalg.lstsq(M, y, rcond=None)[0]


def boot_ols(y, F, B, rng):
    bs = []
    for _ in range(B):
        s = rng.integers(0, len(y), len(y))
        if np.linalg.matrix_rank(np.column_stack([np.ones(len(s)), F[s]])) < F.shape[1] + 1:
            continue
        bs.append(ols(y[s], F[s]))
    return np.percentile(np.array(bs), [2.5, 97.5], axis=0)


def boot_diff(a, b, B, rng):
    d = [a[rng.integers(0, len(a), len(a))].mean() - b[rng.integers(0, len(b), len(b))].mean() for _ in range(B)]
    return np.percentile(d, [2.5, 97.5])


def situation_features(s):
    """探索 (厳しさと暮らしの数の相関) に使う 0/1 と数。"""
    return {"年齢 (歳)": s["age"], "女性": int(s["sex"] == "女性"), "学生": s["student"],
            "正社員": int(s["position"] == "regular"), "パート・派遣": int(s["position"] == "nonregular"),
            "暮らし 苦しい": int(s["money"] == "tight"), "暮らし ゆとり": int(s["money"] == "comfortable"),
            "ネットくわしい": int(s["digital"] == "high"), "ネット苦手": int(s["digital"] == "low"),
            "音楽は無料の動画": int(s["music"] == "free_video"), "近い間柄": int(s["close"]),
            "作り手が身近": int(s["creator"] is not None), "作り手を買って応援": int(s["fan"] is not None),
            "決まりがはっきり": int(s["rules"])}


def run(answers_dir, out_dir, B=1000, exp1_answers=None, figures=True, situations_path=None):
    rng = np.random.default_rng(SEED)
    os.makedirs(out_dir, exist_ok=True)
    ss = json.load(open(situations_path or os.path.join(HERE, "situations.json"), encoding="utf-8"))["situations"]
    data = A.load(answers_dir, CONDITIONS_EXP2)
    conds = [c for c in CONDITIONS_EXP2 if len(data[c]["X"]) >= 2]
    sit = {c: [ss[int(r.split("_")[1]) - 1] for r in data[c]["ids"]] for c in CONDITIONS_EXP2}
    e1 = A.load(exp1_answers, CONDITIONS) if exp1_answers and os.path.isdir(exp1_answers) else None
    e1c = [c for c in ("C1", "C4") if e1 is not None and len(e1[c]["X"]) >= 2]
    meta = {**{c: CONDITIONS[c] for c in e1c}, **CONDITIONS_EXP2}

    stats = {}
    for c in conds:
        m, s, mo = A.item_stats(data[c]["X"])
        stats[c] = {"mean": m, "sd": s, "modal": mo, "n": len(data[c]["X"])}
    for c in e1c:
        m, s, mo = A.item_stats(e1[c]["X"])
        stats[c] = {"mean": m, "sd": s, "modal": mo, "n": len(e1[c]["X"])}
    L = ["# 実験 2 の結果 (analyze_exp2.py が書いた)", "",
         "答えの数: " + ", ".join(f"{c} {len(data[c]['X'])}/{CONDITIONS_EXP2[c]['n']}" for c in CONDITIONS_EXP2)
         + ("。くらべる実験 1: " + ", ".join(f"{c} {len(e1[c]['X'])}" for c in e1c) if e1c else "。実験 1 の答えなし"), ""]

    with open(os.path.join(out_dir, "items.csv"), "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        cs = conds + [f"exp1_{c}" for c in e1c]
        keys = conds + e1c
        w.writerow(["item", "text", "norm", "gray", "download"] + [f"{c}_{k}" for c in cs for k in ("mean", "sd", "modal")])
        for j, i in enumerate(IDS):
            w.writerow([i, TEXT[i], NORM[i], int(i in GRAY), int(i in DOWNLOAD)] +
                       [round(float(stats[c][k][j]), 3) for c in keys for k in ("mean", "sd", "modal")])

    # ---------- 問いごとの数 (くらべの土台) ----------
    norm = np.array([NORM[i] for i in IDS])
    L += ["## 問いごとの数 (実験 1 とならべる)", "",
          "| 組 | n | SD の平均 (95% CI) | SD が 0 の問い | いちばん多い答えが 9 割以上の問い | 規範との差 |平均| | 規範との差 (符号つき, + = 厳しい) | 人ごとの平均点の SD |",
          "|---|---|---|---|---|---|---|---|"]
    res = {}
    rows = [(c, data[c]["X"], c) for c in conds] + [(c, e1[c]["X"], f"実験 1 {c}") for c in e1c]
    for c, X, name in rows:
        msd = float(np.mean(stats[c]["sd"]))
        res[c] = {"mean_sd": msd}
        L.append(f"| {name} ({meta[c]['model']}) | {len(X)} | {A.fmt(msd)} {A.ci(A.boot(X, lambda Y: np.mean(Y.std(0, ddof=1)), B, rng))} | "
                 f"{int(np.sum(stats[c]['sd'] == 0))} | {int(np.sum(stats[c]['modal'] >= 0.9))} | "
                 f"{A.fmt(float(np.mean(np.abs(stats[c]['mean'] - norm))))} | {A.fmt(float(np.mean(stats[c]['mean'] - norm)), 2)} | "
                 f"{A.fmt(float(X.mean(1).std(ddof=1)))} |")
    L.append("")

    # ---------- 主成分分析 (H6・H7・H10) ----------
    sets = {c: data[c]["X"] for c in ("D1", "D2") if c in conds and len(data[c]["X"]) >= 10}
    if "D1" in sets and "D2" in sets:
        sets["D1+D2"] = np.vstack([sets["D1"], sets["D2"]])
    if "C1" in e1c and len(e1["C1"]["X"]) >= 10:
        sets["exp1_C1"] = e1["C1"]["X"]
    noise84 = A.noise_eig(HUMAN_N)
    eig, match_rows, h6, h7, h10, tops = {}, [], [], [], [], []
    L += ["## 主成分分析 (H6・H7・H10)", "",
          f"人間 (修士論文 表 3): 第 1 主成分の割合 {HUMAN_PC1:.3f} (固有値から)。実験 1 C1: {EXP1_C1_PC1}。でたらめな答え (n=84) の第 1 固有値 {noise84[0]:.2f}。"
          "D1+D2 は同じ暮らしの人が 2 回ずつ入る (参考)。", "",
          "| 組 | n | 使った問い | 固有値 1〜5 | 第 1 の割合 (95% CI, n=84 に引き直し) | 厳しさの割合 (95% CI) | |r(厳しさ, 第 1 主成分の点)| | 50.3% に届く数 |",
          "|---|---|---|---|---|---|---|---|"]
    with open(os.path.join(out_dir, "eigen.csv"), "w", newline="", encoding="utf-8") as fe:
        we = csv.writer(fe)
        we.writerow(["set", "k", "eigenvalue", "share", "cumulative"])
        for k in range(5):
            we.writerow(["human_printed", k + 1, HUMAN_EIG[k], round(HUMAN_EIG[k] / P, 4), round(HUMAN_CUM_FROM_EIG[k], 4)])
        for k in range(15):
            we.writerow(["noise_n84", k + 1, round(float(noise84[k]), 4), round(float(noise84[k]) / P, 4), ""])
        for c, X in sets.items():
            w, V, used = A.pca(X)
            eig[c] = w
            p = len(used)
            cum = np.cumsum(w) / p
            for k in range(min(15, len(w))):
                we.writerow([c, k + 1, round(float(w[k]), 4), round(float(w[k] / p), 4), round(float(cum[k]), 4)])
            share_ci = A.boot(X, lambda Y: A.pc1_share(Y[:HUMAN_N]), B, rng)
            st = strict_share(X)
            st_ci = A.boot(X, strict_share, B, rng)
            r = strict_pc1_r(X)
            L.append(f"| {c} | {len(X)} | {p} | {', '.join(f'{v:.2f}' for v in w[:5])} | {w[0] / p:.3f} {A.ci(share_ci)} | "
                     f"{A.fmt(st)} {A.ci(st_ci)} | {r:.3f} | {A.n_to_reach(w, p, HUMAN_CUM_FROM_EIG[4])} |")
            if c.startswith("exp1"):
                continue
            sup6 = share_ci[1] < EXP1_C1_PC1
            h6.append(f"- **H6 {c}{' (主)' if c == 'D1' else ' (参考)'}:** 第 1 主成分の割合 {w[0] / p:.3f} {A.ci(share_ci)} → "
                      + ("支持 (CI の上が実験 1 の 0.392 より下)" if sup6 else "支持しない (CI の上が 0.392 以上)")
                      + ("。人間の 0.268 は CI の中" if share_ci[0] <= HUMAN_PC1 <= share_ci[1] else "。人間の 0.268 は CI の外"))
            sup10 = st_ci[1] < EXP1_C1_STRICT
            h10.append(f"- **H10 {c}{' (主)' if c == 'D1' else ' (参考)'}:** 厳しさの割合 {A.fmt(st)} {A.ci(st_ci)} → "
                       + ("支持 (CI の上が実験 1 の 0.391 より下)" if sup10 else "支持しない (CI の上が 0.391 以上)")
                       + f"。人間はこの値が 0.268 以下 ({'CI の上が 0.268 以下' if st_ci[1] <= HUMAN_PC1 else 'CI の上は 0.268 より上'})。"
                       + f" 第 1 主成分は「厳しさ」{'そのもの (|r| > 0.95)' if r > 0.95 else 'とは別の向きをふくむ (|r| ≤ 0.95)'}")
            with open(os.path.join(out_dir, f"loadings_{c.replace('+', '_')}.csv"), "w", newline="", encoding="utf-8") as fl:
                wl = csv.writer(fl)
                wl.writerow(["item"] + [f"pc{k + 1}" for k in range(A.KMAX)])
                for j, i in enumerate(IDS):
                    wl.writerow([i] + [round(float(V[j, k]), 4) for k in range(min(A.KMAX, V.shape[1]))])
            mrows, null_mean = A.match_all(V, rng)
            bo = []
            for _ in range(min(B, 300)):
                _, Vb, _ = A.pca(X[rng.integers(0, len(X), len(X))])
                bo.append([A.match_one(Vb, [i for i, _ in t], [np.sign(v) for _, v in t])[1] for _, _, _, t in HUMAN_PCS])
            lo, hi = np.percentile(np.array(bo), [2.5, 97.5], axis=0)
            for rr, a, b in zip(mrows, lo, hi):
                rr.update({"set": c, "overlap_ci": f"[{a:.0f}, {b:.0f}]", "null_mean_overlap": round(null_mean, 2)})
                match_rows.append(rr)
            nrep = sum(rr["reproduced"] for rr in mrows)
            h7.append(f"- **H7 {c}{' (主)' if c == 'D1' else ' (参考)'}:** 再現 {nrep}/5 ("
                      + ", ".join(rr["name_ja"] for rr in mrows if rr["reproduced"]) + f") → "
                      + (f"支持 ({H7_N} つ以上。実験 1 C1 は 1)" if nrep >= H7_N else "支持しない"))
            tops.append(f"- {c} の上位 5 問 (|固有ベクトル|): "
                        + ", ".join(f"pc{k + 1}: " + " ".join(IDS[j] for j in np.argsort(-np.abs(V[:, k]))[:5]) for k in range(3)))
    L += [""] + h6 + [""] + h10 + [""] + tops + [""]
    if match_rows:
        keys = ["set", "human_pc", "name_ja", "name_en", "llm_pc", "overlap", "overlap_ci", "sign_agree", "p_null", "null_mean_overlap", "reproduced"]
        with open(os.path.join(out_dir, "match.csv"), "w", newline="", encoding="utf-8") as fm:
            wm = csv.DictWriter(fm, fieldnames=keys)
            wm.writeheader()
            wm.writerows(match_rows)
        L += ["### H7: 人間の 5 つの主成分の上位 5 問が、いっしょに出るか (実験 1 の H5 と同じ決まり。すべて書く)", "",
              "| 組 | 人間の主成分 | いちばん合う主成分 | 重なり (0〜5) (95% CI) | 符号の合う割合 | 偶然の p | 再現 |", "|---|---|---|---|---|---|---|"]
        for rr in match_rows:
            L.append(f"| {rr['set']} | {rr['human_pc']} {rr['name_ja']} | pc{rr['llm_pc']} | {rr['overlap']} {rr['overlap_ci']} | "
                     f"{rr['sign_agree']} | {rr['p_null']} | {'はい' if rr['reproduced'] else 'いいえ'} |")
        L += [""] + h7 + [""]

    # ---------- H8: はみ出しやすい時 (D2 − D1、同じ暮らしの対) ----------
    coef_rows = []
    if "D1" in conds and "D2" in conds:
        i1 = {r.split("_")[1]: k for k, r in enumerate(data["D1"]["ids"])}
        i2 = {r.split("_")[1]: k for k, r in enumerate(data["D2"]["ids"])}
        both = sorted(set(i1) & set(i2))
        if len(both) >= 8:
            X1 = data["D1"]["X"][[i1[b] for b in both]]
            X2 = data["D2"]["X"][[i2[b] for b in both]]
            F = np.array([[ss[int(b) - 1]["surround"][k] for k, _ in SURROUND] for b in both], float)
            g = [IDS.index(i) for i in GRAY]
            ng = [j for j in range(P) if j not in g]
            dl = [IDS.index(i) for i in DOWNLOAD]
            outs = {"gray_paired": X2[:, g].mean(1) - X1[:, g].mean(1), "gray_D2only": X2[:, g].mean(1),
                    "other_paired": X2[:, ng].mean(1) - X1[:, ng].mean(1), "download_paired": X2[:, dl].mean(1) - X1[:, dl].mean(1)}
            est = {k: ols(y, F) for k, y in outs.items()}
            cis = {k: boot_ols(y, F, B, rng) for k, y in outs.items()}
            L += ["## H8: はみ出しやすい時 4 つは、グレーゾーンの問いを「問題でない」へ動かすか", "",
                  f"対の数 {len(both)}。y = グレーゾーン {len(GRAY)} 問の平均の差 (D2 − D1、同じ暮らし)。"
                  "y を 4 つの様子 (1 = はみ出しやすい側) に回帰 (切片つきの最小二乗)。CI は対を引き直す。", "",
                  "| 様子 | グレーゾーン (主) 係数 (95% CI) | 判定 | グレーゾーン D2 だけ | ほかの 40 問 (探索) | ダウンロード 5 問 (探索) |",
                  "|---|---|---|---|---|---|"]
            nsup = 0
            for j, (k, ja) in enumerate(SURROUND):
                b, (lo, hi) = est["gray_paired"][j + 1], (cis["gray_paired"][0][j + 1], cis["gray_paired"][1][j + 1])
                sup = hi < 0
                nsup += sup
                cell = lambda key: f"{est[key][j + 1]:+.3f} [{cis[key][0][j + 1]:+.3f}, {cis[key][1][j + 1]:+.3f}]"
                L.append(f"| {ja} | {cell('gray_paired')} | {'支持 (CI の上 < 0)' if sup else '支持しない'} | {cell('gray_D2only')} | "
                         f"{cell('other_paired')} | {cell('download_paired')} |")
                for key in outs:
                    coef_rows.append({"outcome": key, "factor": k, "factor_ja": ja, "coef": round(float(est[key][j + 1]), 4),
                                      "ci_lo": round(float(cis[key][0][j + 1]), 4), "ci_hi": round(float(cis[key][1][j + 1]), 4)})
            L += ["", f"- 切片 (4 つともはみ出しにくい側の様子を足したときの、グレーゾーンの動き): {est['gray_paired'][0]:+.3f} "
                      f"[{cis['gray_paired'][0][0]:+.3f}, {cis['gray_paired'][1][0]:+.3f}]",
                  f"- **H8:** 4 つのうち {nsup} つが支持 → " + ("支持 (4 つすべて)" if nsup == 4 else "一部支持" if nsup > 0 else "支持しない"), ""]
            with open(os.path.join(out_dir, "h8_coef.csv"), "w", newline="", encoding="utf-8") as fc:
                wc = csv.DictWriter(fc, fieldnames=list(coef_rows[0]))
                wc.writeheader()
                wc.writerows(coef_rows)

    # ---------- H9: 学生・お金が苦しい人は、ダウンロードの問いをゆるく見るか ----------
    dl = [IDS.index(i) for i in DOWNLOAD]
    h9plot = {}
    L += ["## H9: 学生・暮らしが苦しい人 (弱い側) と、働いていて暮らしが苦しくない人 (働いてゆとり側) のダウンロード 5 問", "",
          f"ダウンロード・コピーの問い: {' '.join(DOWNLOAD)}。弱い側 = 学生か、暮らしが「苦しい」。働いてゆとり側 = 正社員・パート・自営で、暮らしが「ふつう」か「ゆとりがある」。"
          "どちらでもない人 (家事が中心・仕事をしていない で苦しくない) は入れない。", "",
          "| 組 | 弱い側 n | 働いてゆとり側 n | 弱い側の平均 | ゆとり側の平均 | 差 (95% CI) | 判定 | 回帰 (探索): 学生 / 苦しい |", "|---|---|---|---|---|---|---|---|"]
    for c in [c for c in ("D1", "D2", "D3") if c in conds]:
        X, S = data[c]["X"], sit[c]
        y = X[:, dl].mean(1)
        wk = np.array([s["student"] == 1 or s["money"] == "tight" for s in S])
        st = np.array([s["position"] in ("regular", "nonregular", "self") and s["money"] != "tight" and not s["student"] for s in S])
        if wk.sum() < 2 or st.sum() < 2:
            L.append(f"| {c} | {int(wk.sum())} | {int(st.sum())} | — | — | — | 人数が足りない | — |")
            continue
        d = y[wk].mean() - y[st].mean()
        dci = boot_diff(y[wk], y[st], B, rng)
        h9plot[c] = (y[wk], y[st])
        if wk.sum() < H9_MIN_N or st.sum() < H9_MIN_N:
            verdict = f"判定できない (どちらかが {H9_MIN_N} 人未満)"
        else:
            verdict = "支持 (差 ≤ −0.2 で CI の上 < 0)" if (d <= H9_D and dci[1] < 0) else "支持しない"
        Fm = np.array([[s["student"], int(s["money"] == "tight")] for s in S], float)
        reg = "—"
        if np.linalg.matrix_rank(np.column_stack([np.ones(len(y)), Fm])) == 3:
            bb = ols(y, Fm)
            bc = boot_ols(y, Fm, B, rng)
            reg = f"{bb[1]:+.2f} [{bc[0][1]:+.2f}, {bc[1][1]:+.2f}] / {bb[2]:+.2f} [{bc[0][2]:+.2f}, {bc[1][2]:+.2f}]"
        L.append(f"| {c}{' (主)' if c == 'D1' else ' (参考)'} | {int(wk.sum())} | {int(st.sum())} | {y[wk].mean():.2f} | {y[st].mean():.2f} | "
                 f"{d:+.3f} {A.ci(dci)} | {verdict} | {reg} |")
        if c == "D1":
            res["h9"] = verdict
    L += ["", f"- **H9 (D1):** {res.get('h9', '答えが足りない')}", ""]

    # ---------- H11: モデルの確かめ (opus) ----------
    if "D3" in conds:
        X3 = data["D3"]["X"]
        L += ["## H11: 暮らしを持たせると、opus でも答えがばらけるか (D3 と実験 1 C4。どちらも opus・30 人)", ""]
        if "C4" in e1c:
            X4 = e1["C4"]["X"]
            dd = [np.mean(X3[rng.integers(0, len(X3), len(X3))].std(0, ddof=1)) - np.mean(X4[rng.integers(0, len(X4), len(X4))].std(0, ddof=1))
                  for _ in range(B)]
            lo, hi = np.percentile(dd, [2.5, 97.5])
            diff = float(np.mean(X3.std(0, ddof=1)) - np.mean(X4.std(0, ddof=1)))
            L.append(f"- **H11:** SD の平均 D3 − 実験 1 C4 = {diff:+.3f} [{lo:+.3f}, {hi:+.3f}] (C4 は {EXP1_C4_SD}) → "
                     + ("支持 (CI の下 > 0)" if lo > 0 else "支持しない"))
        else:
            d0 = float(np.mean(X3.std(0, ddof=1))) - EXP1_C4_SD
            L.append(f"- **H11:** 実験 1 の答えがないので、決めた数 {EXP1_C4_SD} とだけくらべる: 差 {d0:+.3f} (CI なし。判定しない)")
        if "D1" in conds:
            i1 = {r.split("_")[1]: k for k, r in enumerate(data["D1"]["ids"])}
            i3 = {r.split("_")[1]: k for k, r in enumerate(data["D3"]["ids"])}
            bb = sorted(set(i1) & set(i3))
            if len(bb) >= 5:
                m1 = data["D1"]["X"][[i1[b] for b in bb]].mean(1)
                m3 = X3[[i3[b] for b in bb]].mean(1)
                r = float(np.corrcoef(m1, m3)[0, 1])
                rs = []
                for _ in range(B):
                    s = rng.integers(0, len(bb), len(bb))
                    if m1[s].std() > 0 and m3[s].std() > 0:
                        rs.append(np.corrcoef(m1[s], m3[s])[0, 1])
                lo, hi = np.percentile(rs, [2.5, 97.5])
                L.append(f"- 探索: 同じ暮らしの人の厳しさ (54 問の平均) の相関 D1 (sonnet) × D3 (opus) = {r:+.2f} [{lo:+.2f}, {hi:+.2f}] (対 {len(bb)})。"
                         "高ければ、モデルが変わっても、暮らしが同じ向きに効いている")
        L.append("")

    # ---------- 探索: 厳しさと暮らしの数 (実験 1 の誠実性 +0.78 にあたるもの) ----------
    if "D1" in conds and len(data["D1"]["X"]) >= 10:
        X, S = data["D1"]["X"], sit["D1"]
        m = X.mean(1)
        feats = [situation_features(s) for s in S]
        names = list(feats[0])
        Fm = np.array([[f[n] for n in names] for f in feats], float)
        cors = []
        for j, n in enumerate(names):
            cors.append((n, float(np.corrcoef(Fm[:, j], m)[0, 1]) if Fm[:, j].std() > 0 else float("nan")))
        keep = [j for j in range(len(names)) if Fm[:, j].std() > 0]
        beta = ols(m, Fm[:, keep])
        fit = np.column_stack([np.ones(len(m)), Fm[:, keep]]) @ beta
        r2 = 1 - np.sum((m - fit) ** 2) / np.sum((m - m.mean()) ** 2)
        big = max(abs(v) for _, v in cors if np.isfinite(v))
        L += ["## 探索: 厳しさ (54 問の平均) と暮らしの数 (D1。決めた判定はない)", "",
              "相関: " + ", ".join(f"{n} {v:+.2f}" for n, v in cors),
              f"", f"- いちばん大きい |相関| {big:.2f} (実験 1 では誠実性の言葉が +0.78)。暮らしの数みなで説明できる割合 R² = {r2:.2f} (人数 {len(m)}・数 {len(keep)}。多めに出る)", ""]

    # ---------- わけ (探索。数えるだけ。文は reasons.csv) ----------
    rrows = []
    for c in conds:
        for rid, rs, x in zip(data[c]["ids"], data[c]["reasons"], data[c]["X"]):
            for i in REASON_ITEMS:
                rrows.append({"id": rid, "condition": c, "situation_id": f"S{int(rid.split('_')[1]):03d}", "item": i,
                              "answer": int(x[IDS.index(i)]), "reason": (rs or {}).get(i, "")})
    if rrows:
        with open(os.path.join(out_dir, "reasons.csv"), "w", newline="", encoding="utf-8") as fr:
            wr = csv.DictWriter(fr, fieldnames=list(rrows[0]))
            wr.writeheader()
            wr.writerows(rrows)
        empty = sum(1 for r in rrows if not str(r["reason"]).strip())
        L += [f"わけ (5 問 × 人): {len(rrows)} 件、空 {empty} 件 (文は reasons.csv。修士論文の 7 つの考え方での分け方は、あとで別に決める)", ""]

    if figures and conds:
        plt = A.setup_mpl()
        fconds = conds + e1c
        A.fig_items(plt, stats, fconds, "mean", "mean / 平均 (5 = serious … 1 = none)",
                    "Exp 2 item means vs norm / 実験 2 の問いごとの平均と規範", os.path.join(out_dir, "fig_item_means.png"), norm=True, meta=meta)
        A.fig_items(plt, stats, fconds, "sd", "SD / 標準偏差", "Exp 2 item SD / 実験 2 の問いごとのばらつき",
                    os.path.join(out_dir, "fig_item_sd.png"), meta=meta)
        if eig:
            A.fig_scree(plt, eig, noise84, os.path.join(out_dir, "fig_scree.png"),
                        labels={"exp1_C1": "exp1 C1 (Big Five words) / 実験 1 人格の言葉", "D1": "D1 situation / 暮らし",
                                "D2": "D2 situation + surroundings / 暮らし + まわり", "D1+D2": "D1+D2"})
        if coef_rows:
            fig_h8(plt, coef_rows, os.path.join(out_dir, "fig_h8_coef.png"))
        if h9plot:
            fig_h9(plt, h9plot, os.path.join(out_dir, "fig_h9_download.png"))
    with open(os.path.join(out_dir, "summary.md"), "w", encoding="utf-8") as f:
        f.write("\n".join(L) + "\n")
    return L


def fig_h8(plt, rows, out):
    fig, ax = plt.subplots(figsize=(8.5, 4.8))
    keys = [("gray_paired", "gray-zone, paired / グレーゾーン (主)", "#2a78d6"), ("other_paired", "other 40 items / ほかの問い", "#c3c2b7"),
            ("download_paired", "download 5 items / ダウンロード", "#eb6834")]
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
    ax.set_xlabel("effect on mean (D2 − D1), < 0 = less problematic / 平均の動き (負 = 問題でない側)", fontsize=9)
    ax.set_title("H8: 'easy to step outside the rules' conditions / はみ出しやすい時", fontsize=10, color=A.INK, loc="left")
    ax.legend(fontsize=8, frameon=False, loc="upper center", bbox_to_anchor=(0.5, -0.16), ncol=3)
    fig.tight_layout()
    fig.savefig(out, dpi=130, bbox_inches="tight")
    plt.close(fig)


def fig_h9(plt, groups, out):
    fig, ax = plt.subplots(figsize=(6.5, 4))
    for k, (c, (a, b)) in enumerate(groups.items()):
        for q, (v, col, lab) in enumerate([(a, "#eb6834", "student or money tight / 学生か苦しい"),
                                            (b, "#2a78d6", "working, not tight / 働いてゆとり")]):
            x = k + (q - 0.5) * 0.35
            ax.plot(np.full(len(v), x) + np.linspace(-0.06, 0.06, len(v)), v, "o", ms=3, color=col, alpha=0.5)
            ax.plot([x - 0.12, x + 0.12], [v.mean(), v.mean()], "-", color=col, lw=3, label=lab if k == 0 else None)
    ax.set_xticks(range(len(groups)))
    ax.set_xticklabels(list(groups))
    ax.set_ylim(0.8, 5.2)
    ax.set_ylabel("mean of 5 download items / ダウンロード 5 問の平均")
    ax.set_title("H9: download items by life situation / 暮らしとダウンロードの問い", fontsize=10, color=A.INK, loc="left")
    ax.legend(fontsize=8, frameon=False)
    fig.tight_layout()
    fig.savefig(out, dpi=130)
    plt.close(fig)


if __name__ == "__main__":
    import argparse
    ap = argparse.ArgumentParser()
    ap.add_argument("--answers", default=os.path.join(HERE, "answers_exp2"))
    ap.add_argument("--out", default=os.path.join(HERE, "out_exp2"))
    ap.add_argument("--boot", type=int, default=1000)
    a = ap.parse_args()
    print("\n".join(run(a.answers, a.out, a.boot, exp1_answers=os.path.join(HERE, "answers"))))
