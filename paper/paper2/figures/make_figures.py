"""Regenerate the English figures of paper 2 from the analysis outputs (read-only):

    sim/society/tools/survey/out/          (experiment 1: items.csv, eigen.csv, summary.md)
    sim/society/tools/survey/out_exp2/     (experiment 2: items.csv, eigen.csv, h8_coef.csv, reasons_coded.csv, summary.md)

    python3 paper/paper2/figures/make_figures.py          # English figures (used in main.tex)
    python3 paper/paper2/figures/make_figures.py --ja     # Japanese figures (PNG) -> paper/paper2/figures_ja/

Point estimates are read from the CSV files. Bootstrap CIs that the analysis scripts only printed to summary.md
are copied below (CI dict) with the line they come from, so that the figures match the pre-registered analysis exactly.
"""
import csv
import os
import sys

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, "..", "..", ".."))
S1 = os.path.join(ROOT, "sim/society/tools/survey/out")
S2 = os.path.join(ROOT, "sim/society/tools/survey/out_exp2")

INK, MUTED, GRID = "#0b0b0b", "#52514e", "#e6e5e0"
BLUE, ORANGE, AQUA, GRAY = "#2a78d6", "#eb6834", "#1baf7a", "#c3c2b7"
JA = "--ja" in sys.argv
OUT = os.path.join(HERE, "..", "figures_ja") if JA else HERE


def t(en, ja):
    return ja if JA else en


plt.rcParams.update({"font.family": "IPAPGothic" if JA else "DejaVu Sans", "font.size": 9, "axes.edgecolor": MUTED, "axes.labelcolor": INK,
                     "xtick.color": MUTED, "ytick.color": MUTED, "axes.spines.top": False, "axes.spines.right": False,
                     "axes.grid": True, "grid.color": GRID, "grid.linewidth": 0.6, "axes.axisbelow": True})


def rows(path):
    return list(csv.DictReader(open(path, encoding="utf-8")))


def save(fig, name):
    fig.tight_layout()
    os.makedirs(OUT, exist_ok=True)
    for ext in (("png",) if JA else ("pdf", "png")):
        fig.savefig(os.path.join(OUT, f"{name}.{ext}"), dpi=200)
    plt.close(fig)


# 95% CIs printed in summary.md (out/summary.md: "SD の平均 (95% CI)"; out_exp2/summary.md: same table)
SD_CI = {"C0": (0.148, 0.183), "C3": (0.331, 0.377), "C4": (0.109, 0.145), "C1": (0.377, 0.430), "C2": (0.425, 0.465),
         "D1": (0.290, 0.344), "D2": (0.296, 0.340), "D3": (0.271, 0.344)}
# out/summary.md and out_exp2/summary.md, PCA tables ("第 1 の割合 (95% CI, n=84 に引き直し)", "厳しさの割合")
PC1 = {"C1": (0.392, 0.336, 0.455), "C2": (0.386, 0.340, 0.438), "D1": (0.228, 0.195, 0.312), "D2": (0.250, 0.216, 0.311)}
STRICT = {"C1": (0.391, 0.342, 0.447), "D1": (0.223, 0.185, 0.297), "D2": (0.243, 0.207, 0.298)}


def fig_sd():
    i1 = rows(os.path.join(S1, "items.csv"))
    i2 = rows(os.path.join(S2, "items.csv"))
    mean_sd = {c: sum(float(r[f"{c}_sd"]) for r in i1) / len(i1) for c in ["C0", "C3", "C4", "C1", "C2"]}
    mean_sd.update({c: sum(float(r[f"{c}_sd"]) for r in i2) / len(i2) for c in ["D1", "D2", "D3"]})
    labels = [("C0", t("Exp 1 C0: no persona, Sonnet (n=30)", "実験1 C0: 人格なし sonnet (30人)")),
              ("C3", t("Exp 1 C3: no persona, Haiku (n=30)", "実験1 C3: 人格なし haiku (30人)")),
              ("C4", t("Exp 1 C4: no persona, Opus (n=30)", "実験1 C4: 人格なし opus (30人)")),
              ("C1", t("Exp 1 C1: Big Five words, Sonnet (n=100)", "実験1 C1: ビッグファイブの言葉 sonnet (100人)")),
              ("C2", t("Exp 1 C2: Big Five + honne first, Sonnet (n=100)", "実験1 C2: ビッグファイブ + 本音を先に sonnet (100人)")),
              ("D1", t("Exp 2 D1: life circumstances, Sonnet (n=100)", "実験2 D1: 暮らし sonnet (100人)")),
              ("D2", t("Exp 2 D2: circumstances + surroundings, Sonnet (n=100)", "実験2 D2: 暮らし + まわりの様子 sonnet (100人)")),
              ("D3", t("Exp 2 D3: life circumstances, Opus (n=30)", "実験2 D3: 暮らし opus (30人)"))]
    fig, ax = plt.subplots(figsize=(6.4, 3.4))
    for k, (c, lab) in enumerate(labels):
        y = len(labels) - 1 - k
        lo, hi = SD_CI[c]
        ax.plot([lo, hi], [y, y], color=BLUE, lw=2)
        ax.plot(mean_sd[c], y, "o", ms=6, color=BLUE, mec="white", mew=1.2)
        ax.text(hi + 0.012, y, f"{mean_sd[c]:.2f}", va="center", fontsize=8, color=INK)
    ax.axvline(0.5, color=MUTED, ls="--", lw=1)
    ax.text(0.495, len(labels) - 0.6, t("H1a threshold 0.5", "そろいすぎの線 0.5 (H1a)"), fontsize=7.5, color=MUTED, va="bottom", ha="right")
    ax.set_yticks(range(len(labels)))
    ax.set_yticklabels([lab for _, lab in labels][::-1], fontsize=8)
    ax.set_xlim(0, 0.62)
    ax.set_ylim(-0.6, len(labels) - 0.1)
    ax.set_xlabel(t("mean item SD over 54 items (95% bootstrap CI)", "54 問の答えのばらつき (標準偏差) の平均 (95% 信頼区間)"))
    ax.grid(axis="y", visible=False)
    save(fig, "fig_sd")


def fig_pc1():
    fig, ax = plt.subplots(figsize=(6.4, 2.7))
    items = [(t("Exp 1 C1 (Big Five words)", "実験1 C1 (ビッグファイブの言葉)"), "C1"),
             (t("Exp 1 C2 (Big Five + honne)", "実験1 C2 (ビッグファイブ + 本音)"), "C2"),
             (t("Exp 2 D1 (life circumstances)", "実験2 D1 (暮らし)"), "D1"),
             (t("Exp 2 D2 (+ surroundings)", "実験2 D2 (暮らし + まわりの様子)"), "D2")]
    for k, (lab, c) in enumerate(items):
        y = len(items) - 1 - k
        p, lo, hi = PC1[c]
        ax.plot([lo, hi], [y + 0.12, y + 0.12], color=BLUE, lw=2)
        ax.plot(p, y + 0.12, "o", ms=6, color=BLUE, mec="white", mew=1.2, label=t("PC1 share", "第1主成分の割合") if k == 0 else None)
        if c in STRICT:
            p2, lo2, hi2 = STRICT[c]
            ax.plot([lo2, hi2], [y - 0.12, y - 0.12], color=ORANGE, lw=2)
            ax.plot(p2, y - 0.12, "s", ms=5.5, color=ORANGE, mec="white", mew=1.2,
                    label=t("strictness share (H10)", "「厳しさ」1本の割合 (H10)") if k == 0 else None)
    ax.axvline(0.268, color=INK, lw=1.2)
    ax.text(0.270, len(items) - 0.45, t("human PC1 share 0.268\n(from published eigenvalue)", "人間の第1主成分の割合 0.268\n(修士論文の固有値 14.47 ÷ 54)"), fontsize=7.5, color=INK, va="bottom")
    ax.set_yticks(range(len(items)))
    ax.set_yticklabels([lab for lab, _ in items][::-1], fontsize=8)
    ax.set_xlim(0.15, 0.5)
    ax.set_ylim(-0.6, len(items) + 0.35)
    ax.set_xlabel(t("share of standardized variance (95% CI, resampled to n = 84)", "ばらつき全体のうち説明できる割合 (95% 信頼区間。84 人に引き直し)"))
    ax.grid(axis="y", visible=False)
    ax.legend(fontsize=7.5, frameon=False, loc="lower right")
    save(fig, "fig_pc1")


def fig_scree():
    e1 = rows(os.path.join(S1, "eigen.csv"))
    e2 = rows(os.path.join(S2, "eigen.csv"))
    get = lambda E, s: [float(r["eigenvalue"]) for r in E if r["set"] == s]
    fig, ax = plt.subplots(figsize=(5.6, 3.4))
    K = 12
    series = [(get(e1, "C1")[:K], ORANGE, "o", t("Exp 1 C1 (Big Five words, n=100)", "実験1 C1 (ビッグファイブの言葉、100人)")),
              (get(e2, "D1")[:K], BLUE, "o", t("Exp 2 D1 (life circumstances, n=100)", "実験2 D1 (暮らし、100人)")),
              (get(e2, "human_printed"), INK, "s", t("Human (thesis Table 3, n=84; first 5 only)", "人間 (修士論文の表3、84人。5つまで)")),
              (get(e2, "noise_n84")[:K], MUTED, None, t("Random answers, n=84 (parallel analysis)", "でたらめな答え 84人 (くらべの線)"))]
    for w, col, mk, lab in series:
        x = range(1, len(w) + 1)
        if mk:
            ax.plot(x, w, "-" + mk, color=col, ms=4.5, lw=1.8, label=lab)
        else:
            ax.plot(x, w, "--", color=col, lw=1.4, label=lab)
    ax.set_xlabel(t("component", "主成分 (大きい順)"))
    ax.set_ylabel(t("eigenvalue (54 standardized items)", "固有値 (54 問。合計は 54)"))
    ax.set_xticks(range(1, K + 1))
    ax.legend(fontsize=7.5, frameon=False)
    save(fig, "fig_scree")


def fig_h8():
    h = rows(os.path.join(S2, "h8_coef.csv"))
    names = {"everyone": t("'Everyone around me does it'", "「まわりがみんなやっている」"),
             "no_arrest": t("'Never heard of anyone caught'", "「捕まった人を聞いたことがない」"),
             "weak": t("'I am in a weak position'", "「自分は弱い立場にいる」"),
             "easy": t("'It is technically easy'", "「技術的に簡単にできる」")}
    outs = [("gray_paired", BLUE, "o", t("14 gray-zone items (H8, primary)", "グレーゾーン 14 問 (H8、主な数)")),
            ("download_paired", ORANGE, "s", t("5 download/copy items (exploratory)", "ダウンロード・コピー 5 問 (探索)"))]
    fig, ax = plt.subplots(figsize=(6.4, 3.2))
    for j, (o, col, mk, lab) in enumerate(outs):
        for k, f in enumerate(names):
            r = next(r for r in h if r["outcome"] == o and r["factor"] == f)
            y = len(names) - 1 - k + (0.14 if j == 0 else -0.14)
            ax.plot([float(r["ci_lo"]), float(r["ci_hi"])], [y, y], color=col, lw=2)
            ax.plot(float(r["coef"]), y, mk, color=col, ms=6, mec="white", mew=1.2, label=lab if k == 0 else None)
    ax.axvline(0, color=INK, lw=1)
    ax.set_yticks(range(len(names)))
    ax.set_yticklabels(list(names.values())[::-1], fontsize=8)
    ax.set_xlabel(t("coefficient on paired change D2 − D1 (1–5 scale; < 0 = more lenient)", "同じ人の D1 → D2 の答えの動き (5段階。0 より左 = ゆるくなる)"))
    ax.grid(axis="y", visible=False)
    ax.legend(fontsize=7.5, frameon=False, loc="upper center", bbox_to_anchor=(0.4, -0.25), ncol=2)
    save(fig, "fig_h8")


def fig_reasons():
    R = rows(os.path.join(S2, "reasons_coded.csv"))
    fams = [("rule", BLUE, t("Rule-following only", "決まりに従う理由だけ")), ("mixed", AQUA, t("Mixed (rule + bending)", "両方")),
            ("bend", ORANGE, t("Bending only", "はみ出す理由だけ")), ("unc", GRAY, t("Uncodable", "分けられない"))]
    groups = [(t("D1\ncircumstances\n(Sonnet)", "D1\n暮らし\n(sonnet)"), [r for r in R if r["condition"] == "D1"]),
              (t("D2\n+ surroundings\n(Sonnet)", "D2\n+ まわりの様子\n(sonnet)"), [r for r in R if r["condition"] == "D2"]),
              (t("D3\ncircumstances\n(Opus)", "D3\n暮らし\n(opus)"), [r for r in R if r["condition"] == "D3"]),
              (t("D2, 'everyone\ndoes it'\n= no", "D2\n「みんなやっている」\nなし"), [r for r in R if r["condition"] == "D2" and r["s_everyone"] == "0"]),
              (t("D2, 'everyone\ndoes it'\n= yes", "D2\n「みんなやっている」\nあり"), [r for r in R if r["condition"] == "D2" and r["s_everyone"] == "1"])]
    fig, ax = plt.subplots(figsize=(6.4, 3.6))
    xs = [0, 1, 2, 3.4, 4.4]
    for x, (g, rs) in zip(xs, groups):
        b = 0
        for f, col, lab in fams:
            v = 100 * sum(r["family"] == f for r in rs) / len(rs)
            ax.bar(x, v, bottom=b, width=0.7, color=col, edgecolor="white", linewidth=1.5, label=lab if x == 0 else None)
            if v >= 6:
                ax.text(x, b + v / 2, f"{v:.0f}%", ha="center", va="center", fontsize=7.5, color="white" if f != "unc" else INK)
            b += v
        ax.text(x, 101.5, t(f"n={len(rs)}", f"{len(rs)}件"), ha="center", va="bottom", fontsize=7, color=MUTED)
    ax.axvline(2.7, color=MUTED, lw=0.8, ls=":")
    ax.set_xticks(xs)
    ax.set_xticklabels([g for g, _ in groups], fontsize=7.5)
    ax.set_ylim(0, 108)
    ax.set_ylabel(t("share of one-phrase reasons (%)", "ひとことの理由の割合 (%)"))
    ax.grid(axis="x", visible=False)
    ax.legend(fontsize=7.5, frameon=False, loc="upper center", bbox_to_anchor=(0.5, -0.3), ncol=4)
    save(fig, "fig_reasons")


if __name__ == "__main__":
    fig_sd()
    fig_pc1()
    fig_scree()
    fig_h8()
    fig_reasons()
    print("ok")
