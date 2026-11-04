"""facts.json から動画の図 (PNG) を作る。python3 charts.py <facts.json> <出力フォルダ>
   形: 軸は 1 つ・色は少なく (青 = 主な数、だいだい = くらべる数、灰 = 背景)。字は IPA ゴシック。"""
import json
import sys
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
from matplotlib import font_manager  # noqa: E402

for f in ("/usr/share/fonts/opentype/ipafont-gothic/ipagp.ttf", "/usr/share/fonts/opentype/ipafont-gothic/ipag.ttf"):
    if Path(f).exists():
        font_manager.fontManager.addfont(f)
plt.rcParams.update({"font.family": ["IPAPGothic", "IPAGothic", "sans-serif"], "font.size": 15,
                     "axes.edgecolor": "#b8b6b0", "axes.labelcolor": "#52514e", "xtick.color": "#52514e",
                     "ytick.color": "#52514e", "axes.spines.top": False, "axes.spines.right": False,
                     "figure.facecolor": "#fcfcfb", "axes.facecolor": "#fcfcfb", "axes.grid": True,
                     "grid.color": "#e6e4df", "grid.linewidth": 0.8, "axes.axisbelow": True})
BLUE, ORANGE, GRAY, INK, INK2 = "#2a78d6", "#eb6834", "#a9a7a0", "#0b0b0b", "#52514e"

F = json.load(open(sys.argv[1], encoding="utf-8"))
OUT = Path(sys.argv[2]); OUT.mkdir(parents=True, exist_ok=True)
S = F["seasons"]
iy = lambda d: {int(k): v for k, v in d.items()}  # noqa: E731
x_of = lambda s: (s["day"] + 1) / 120  # noqa: E731  季節の終わりを、年の小数で


def fig(title):
    f, ax = plt.subplots(figsize=(9.4, 4.7), dpi=150)
    ax.set_title(title, loc="left", fontsize=17, color=INK, pad=12)
    return f, ax


def save(f, name):
    f.tight_layout()
    f.savefig(OUT / f"{name}.png")
    plt.close(f)


def yearly(key, y0, y1):
    ys = list(range(y0, y1 + 1))
    v = [sum(s[key] for s in S if s["year"] == y) / max(1, sum(1 for s in S if s["year"] == y)) for y in ys]
    return ys, v


# 人の数と、技術が来た年
f, ax = fig("村の人の数 (季節ごと)")
ax.plot([x_of(s) for s in S], [s["pop"] for s in S], color=BLUE, lw=2)
for x, lab, h in [(4, "畑・ヤギ", 120), (13, "土器・鎌・家", 150), (44, "粘土の板", 175), (67.9, "赤い金属の刃を得る", 30), (104.9, "刃を使う", 190)]:
    ax.axvline(x, color=GRAY, lw=1, ls="--")
    ax.text(x + 0.8, h, lab, color=INK2, fontsize=13)
ax.set_xlabel("村の年"); ax.set_ylabel("人"); ax.set_xlim(0, 116); ax.set_ylim(0, 205)
save(f, "c_pop")

# 食べたもの: 畑の草の種と木の実
ys, g = yearly("grain", 4, 114)
_, n = yearly("nut", 4, 114)
f, ax = fig("食べた物のうち、何の割合か (1 年の平均)")
ax.plot(ys, [v * 100 for v in n], color=BLUE, lw=2, label="木の実 (育てた木)")
ax.plot(ys, [v * 100 for v in g], color=ORANGE, lw=2, label="畑の草の種")
ax.text(5, 96, "木の実", color=INK, fontsize=14); ax.text(100, 94, "畑の草の種", color=INK, fontsize=14)
ax.axvline(48.5, color=GRAY, lw=1, ls="--"); ax.text(49.5, 4, "49年から", color=INK2, fontsize=13)
ax.set_ylim(0, 105); ax.set_xlim(0, 116); ax.set_ylabel("%"); ax.set_xlabel("村の年")
ax.legend(loc="center left", frameon=False, fontsize=13, bbox_to_anchor=(0.0, 0.62))
save(f, "c_farm")

# ヤギ
thin = iy(F["thin"])
f, ax = fig("ヤギの数 (季節ごと) と、草が足りずやせていなくなったヤギ (1 年)")
ax.bar(list(thin), list(thin.values()), color=ORANGE, width=0.8, label="やせていなくなった (1 年)")
ax.plot([x_of(s) for s in S], [s["goats"] for s in S], color=BLUE, lw=1.6, label="ヤギの数")
ax.plot([36, 116], [140, 140], color=INK, lw=1.2, ls="--")
ax.text(115, 400, "点線 = 草で養える数 約 140 頭 (36年から)", color=INK, fontsize=13, ha="right")
ax.set_xlim(0, 116); ax.set_ylim(0, 640); ax.set_ylabel("頭"); ax.set_xlabel("村の年")
ax.legend(loc="upper left", frameon=False, fontsize=13)
save(f, "c_goat")

# 土器と虫
lab = ["12年の春", "13年の夏", "13年の秋", "13年の冬", "13年の春", "14年の夏", "14年の秋", "14年の冬"]  # 虫と雨の列は 12年の春 (1529 日目) から
by = {s["label"]: s for s in S}
f, ax = fig("虫やネズミに食べられた草の種 (季節ごと)")
bars = ax.bar(range(len(lab)), [by[l]["pests"] for l in lab], color=BLUE, width=0.7)
for i, l in enumerate(lab):
    p = by[l]["pests"]
    ax.text(i, p + 150, f"{p:,}", ha="center", color=INK, fontsize=13)
ax.set_xticks(range(len(lab)), [l.replace("年の", "年\n") + f"\n土器 {by[l]['pots']:,}" for l in lab], fontsize=12)
ax.set_ylabel("つかみ"); ax.set_ylim(0, 8900)
save(f, "c_pot")

# 家と雨
lab = ["12年の春", "13年の夏", "13年の秋", "13年の冬", "13年の春", "14年の夏", "14年の秋", "14年の冬"]  # 虫と雨の列は 12年の春 (1529 日目) から
f, ax = fig("雨の夜に外で寝た、のべの夜 (季節ごと)")
ax.bar(range(len(lab)), [by[l]["rain_out"] for l in lab], color=BLUE, width=0.7)
for i, l in enumerate(lab):
    ax.text(i, by[l]["rain_out"] + 1.5, str(by[l]["rain_out"]), ha="center", color=INK, fontsize=13)
ax.set_xticks(range(len(lab)), [l.replace("年の", "年\n") + f"\n家 {by[l]['homes']} 軒" for l in lab], fontsize=12)
ax.set_ylabel("人・夜"); ax.set_ylim(0, 90)
save(f, "c_house")

# 持ち物の差
G = [s for s in S if s["gini"] is not None]
f, ax = fig("家ごとの持ち物 (家の倉 + ヤギ) の差")
ax.plot([x_of(s) for s in G], [s["gini"] for s in G], color=BLUE, lw=2)
ax.annotate("14年の夏 0.843\n(家の倉に中身が入った)", xy=(14.5, 0.843), xytext=(20, 0.25), color=INK, fontsize=13,
            arrowprops=dict(arrowstyle="-", color=INK2, lw=0.8))
ax.annotate(f"今 {G[-1]['gini']}", xy=(x_of(G[-1]), G[-1]["gini"]), xytext=(98, 0.6), color=INK, fontsize=13,
            arrowprops=dict(arrowstyle="-", color=INK2, lw=0.8))
ax.text(14.3, 0.03, "13年 0", color=INK2, fontsize=13)
ax.set_ylim(0, 1.05); ax.set_xlim(0, 116); ax.set_xlabel("村の年"); ax.set_ylabel("ジニ係数")
ax.text(60, 0.12, "0 = どの家も同じ、1 = 1 つの家が全部持つ", color=INK2, fontsize=13)
save(f, "c_gini")

# 記録をつけた日
rec = iy(F["rec_days"])
f, ax = fig("粘土の板などに記録をつけた日 (1 年の、のべの日)")
ax.bar(list(rec), list(rec.values()), color=BLUE, width=0.8)
for x, t, h in [(29.5, "29年 家の印", 200), (44, "44年 初めて板に記す", 360), (60, "55年のあと 0", 60)]:
    ax.text(x, h, t, color=INK, fontsize=13)
ax.axvline(29.5, color=GRAY, lw=1, ls="--")
ax.set_xlim(25, 116); ax.set_ylim(0, 380); ax.set_xlabel("村の年"); ax.set_ylabel("日")
save(f, "c_rec")

# 交換
ok, no = iy(F["ex_ok"]), iy(F["ex_no"])
f, ax = fig("よその村との交換: 受けた・自分から行った回と、受けなかった申し出")
ys = range(28, 115)
ax.bar([y - 0.2 for y in ys], [ok.get(y, 0) for y in ys], width=0.45, color=BLUE, label="交換した")
ax.bar([y + 0.25 for y in ys], [no.get(y, 0) for y in ys], width=0.45, color=GRAY, label="申し出を受けなかった")
ax.text(29.5, 6.3, "29年 初めての交換", color=INK, fontsize=13)
ax.text(108.5, 6.3, "110年〜\n遠くの町", color=INK, fontsize=13, ha="center")
ax.set_xlim(27, 116); ax.set_ylim(0, 7.8); ax.set_xlabel("村の年"); ax.set_ylabel("回")
ax.legend(loc="upper center", frameon=False, fontsize=13, ncol=2)
save(f, "c_trade")

# もめごとの収まり方
v = F["verdicts"]
items = [("ゆるす", v["ゆるす"]), ("つぐなう", v["つぐなう"]), ("仲直り (祭り)", v["仲直り"]), ("収まらない\n(去った・なくなった)", v["収まらない"])]
f, ax = fig(f"もめごと {F['disputes']} 件は、どう収まったか")
ax.barh(range(len(items))[::-1], [n for _, n in items], color=[BLUE, GRAY, GRAY, GRAY], height=0.6)
for i, (k, n) in enumerate(items):
    ax.text(n + 5, len(items) - 1 - i, f"{n}", va="center", color=INK, fontsize=15)
ax.set_yticks(range(len(items))[::-1], [k for k, _ in items], fontsize=14)
ax.set_xlim(0, 400); ax.set_xlabel("件"); ax.grid(axis="y", visible=False)
save(f, "c_disp")

# 貢ぎ
paid, stop = iy(F["paid"]), iy(F["stop"])
f, ax = fig("北の大きな村に出した草の種 (1 年)")
ys = range(70, 105)
ax.bar(list(ys), [paid.get(y, 0) / 10000 for y in ys], color=BLUE, width=0.75)
for y in stop:
    ax.text(y, 3, "×", ha="center", color=ORANGE, fontsize=20, fontweight="bold")
ax.text(92, 66, "× = 払うのをやめた年 (92・95・101・103年)", color=INK, fontsize=13, ha="center")
ax.text(80, 8, "71〜89年: 毎年 2,340 つかみ\n(小さくて棒が見えない)", color=INK, fontsize=13, ha="center")
ax.set_xlim(69.5, 104.5); ax.set_ylim(0, 72); ax.set_xlabel("村の年"); ax.set_ylabel("万つかみ")
save(f, "c_trib")

# 赤い金属
u = iy(F["bronze_used"])
f, ax = fig("赤い金属の道具で仕事をした人日 (1 年)")
ax.bar(list(u), list(u.values()), color=BLUE, width=0.7)
for y, n in u.items():
    ax.text(y, n + 6, str(n), ha="center", color=INK, fontsize=14)
for y in (110, 111, 113, 114):
    ax.text(y, -42, "+鎌", ha="center", color=ORANGE, fontsize=13)
ax.text(104.6, 290, "+鎌 = 遠くの町の運ぶ人から、赤い金属の鎌を 2 本ずつ得た年 (113年は 2 回)", color=INK2, fontsize=12)
ax.set_xticks(list(u), [f"{y}年" for y in u], fontsize=12)
ax.set_ylim(-55, 310); ax.set_ylabel("人日"); ax.axhline(0, color="#b8b6b0", lw=1)
save(f, "c_bronze")
print("charts:", OUT)
