"""facts.json から G9 の動画の図 (PNG) を作る。python3 charts.py <facts.json> <出力フォルダ>
   形は tech_life/charts.py と同じ (軸 1 つ・青 = 主な数、だいだい = くらべる数、灰 = 背景。字は IPA ゴシック)。"""
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
YS = list(range(105, 119))


def fig(title):
    f, ax = plt.subplots(figsize=(11.2, 5.0), dpi=150)
    ax.set_title(title, loc="left", fontsize=17, color=INK, pad=12)
    return f, ax


def save(f, name):
    f.tight_layout()
    f.savefig(OUT / f"{name}.png")
    plt.close(f)


def marks(ax, top, low):
    for x, lab, h in [(109, "108年の終わり\n運ぶ人の見込みを上げた", 1.0), (111, "110年の終わり\nはじめて替えた", low)]:
        ax.axvline(x, color=GRAY, lw=1, ls="--")
        ax.text(x + 0.12, top * h, lab, color=INK2, fontsize=12, va="top")


# 赤い金属の道具を使った人日と、道具の数
used, tools = iy(F["used"]), iy(F["tools_end"])
f, ax = fig("赤い金属の道具で働いた人日 (1 年) と、年の終わりの道具の数")
ax.bar(YS, [used[y] for y in YS], color=BLUE, width=0.7)
for y in YS:
    ax.text(y, used[y] + 6, str(used[y]), ha="center", color=INK, fontsize=13)
ax.axhline(30, color=ORANGE, lw=1.4, ls="--")
ax.text(104.6, 62, "点線 = 1つめの条件 (1 年に 30 人日)", color=ORANGE, fontsize=13)
ax.set_xticks(YS, [f"{y}年\n道具 {tools[y]}" for y in YS], fontsize=11.5)
ax.set_ylim(0, 420); ax.set_ylabel("人日")
save(f, "c_bronze")

# 人の数
f, ax = fig("村の人の数 (季節ごと)")
ax.plot([x_of(s) for s in S], [s["pop"] for s in S], color=BLUE, lw=2.4)
ax.text(x_of(S[0]) + 0.1, S[0]["pop"] - 16, f"{S[0]['pop']} 人", color=INK, fontsize=14)
ax.text(x_of(S[-1]) - 0.1, S[-1]["pop"] + 4, f"{S[-1]['pop']} 人", color=INK, fontsize=14, ha="right")
ax.set_xlim(104.8, 119.2); ax.set_ylim(0, 215); ax.set_ylabel("人"); ax.set_xlabel("村の年")
marks(ax, 110, 0.55)
save(f, "c_pop")

# 刈り入れと、刈らずに落ちた草の種
hv, fl = iy(F["harvest"]), iy(F["fallen"])
f, ax = fig("1 年の刈り入れと、刈らずに落ちた草の種 (万つかみ)")
ax.bar([y - 0.2 for y in YS], [hv.get(y, 0) / 1e4 for y in YS], width=0.4, color=BLUE, label="刈り入れ")
ax.bar([y + 0.2 for y in YS], [fl.get(y, 0) / 1e4 for y in YS], width=0.4, color=ORANGE, label="刈らずに落ちた")
for y in YS:
    ax.text(y - 0.2, hv[y] / 1e4 + 1.2, f"{hv[y] / 1e4:.1f}", ha="center", color=INK, fontsize=10.5)
    if fl.get(y, 0) > 0:
        ax.text(y + 0.2, fl[y] / 1e4 + 1.2, f"{fl[y] / 1e4:.1f}", ha="center", color=ORANGE, fontsize=10.5)
ax.set_xticks(YS, [f"{y}" for y in YS]); ax.set_xlabel("村の年"); ax.set_ylim(0, 88); ax.set_ylabel("万つかみ")
ax.legend(loc="upper left", frameon=False, fontsize=13, ncol=2)
save(f, "c_harvest")

# 蓄え (何日分)
f, ax = fig("村の蓄えは何日分か (季節の終わり。1 年は 120 日)")
ax.plot([x_of(s) for s in S], [s["store_days"] for s in S], color=BLUE, lw=2.4)
ax.text(x_of(S[0]) + 0.15, S[0]["store_days"] + 8, f"{S[0]['store_days']} 日分", color=INK, fontsize=14)
ax.text(x_of(S[-1]) - 0.1, S[-1]["store_days"] - 60, f"{S[-1]['store_days']} 日分", color=INK, fontsize=14, ha="right")
ax.set_xlim(104.8, 119.2); ax.set_ylim(0, 620); ax.set_ylabel("日分"); ax.set_xlabel("村の年")
marks(ax, 600, 0.88)
save(f, "c_store")
print("charts:", sorted(p.name for p in OUT.glob("*.png")))
