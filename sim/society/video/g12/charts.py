"""facts.json から G12 の動画の図 (PNG) を作る。python3 charts.py <facts.json> <出力フォルダ>
   形は g11/charts.py と同じ (軸 1 つ・青 = 主な数、だいだい = くらべる数、灰 = 背景。字は IPA ゴシック)。"""
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
iy = lambda d: {int(k): v for k, v in d.items()}  # noqa: E731
YS = list(range(165, 173))
FY = F["fix_year"]


def fig(title):
    f, ax = plt.subplots(figsize=(11.2, 5.0), dpi=150)
    ax.set_title(title, loc="left", fontsize=17, color=INK, pad=12)
    return f, ax


def save(f, name):
    f.tight_layout()
    f.savefig(OUT / f"{name}.png")
    plt.close(f)


def fix_line(ax, x, top, text, dx=0.08):
    ax.axvline(x, color=GRAY, lw=1, ls="--")
    ax.text(x + dx, top, text, color=INK2, fontsize=12, va="top")


def years(ax, lo=164.4, hi=172.6):
    ax.set_xticks(YS, [f"{y}" for y in YS]); ax.set_xlim(lo, hi); ax.set_xlabel("村の年", labelpad=6)


# 道の見張り: 選べた人と選んだ人
pa = iy(F["path"])
f, ax = fig("道の見張り: 約束・助け・帳を自分で選べた人と、選んだ人 (1 年の集まり 2 回、のべ)")
ax.bar(YS, [pa[y]["c1"] for y in YS], width=0.55, color=GRAY, label="倉の約束を選べた人")
ax.plot(YS, [pa[y]["chose"] for y in YS], color=ORANGE, lw=2.6, marker="o", ms=7, label="実際に選んだ人")
for y in YS:
    ax.text(y, pa[y]["c1"] + 1.2, str(pa[y]["c1"]), ha="center", color=INK2, fontsize=11)
    ax.text(y + 0.12, pa[y]["chose"] + 2.2, str(pa[y]["chose"]), ha="center", color=ORANGE, fontsize=14)
fix_line(ax, FY + 0.5, 56, f"{FY}年の終わり\nお題を直した")
ax.set_ylim(0, 58); ax.set_ylabel("人", labelpad=10); years(ax)
ax.legend(loc="upper left", frameon=False, fontsize=12.5)
save(f, "c_path")

# 倉の約束 (年の終わり) と、約束どおり出した村
pc, c1 = iy(F["pacts_y"]), iy(F["c1_y"])
f, ax = fig("倉の約束: 年の終わりに続いている約束と、約束どおり村に出した村")
ax.bar(YS, [pc[y] for y in YS], width=0.55, color=BLUE, label="続いている倉の約束")
ax.plot(YS, [c1[y] for y in YS], color=ORANGE, lw=2.4, marker="o", ms=7, label="約束どおり村に出した村")
for y in YS:
    if pc[y]:
        ax.text(y, pc[y] + 0.25, str(pc[y]), ha="center", color=INK, fontsize=13)
    if c1[y]:
        ax.text(y + 0.2, c1[y] - 0.9, str(c1[y]), ha="center", color=ORANGE, fontsize=13)
ax.axhline(5, color=INK2, lw=1.2, ls=":")
ax.text(164.55, 5.25, "条件 1: 5 村以上の年が 2 回", color=INK2, fontsize=12)
fix_line(ax, FY + 0.5, 12.6, f"{FY}年の終わり\nお題を直した")
ax.set_ylim(0, 13); ax.set_ylabel("村", labelpad=10); years(ax)
ax.legend(loc="upper left", bbox_to_anchor=(0.0, 0.86), frameon=False, fontsize=12.5)
save(f, "c_pacts")

# 倉から出した量
hp, gv = iy(F["help_y"]), iy(F["given_y"])
man = lambda v: f"{v / 1e4:g}万" if v >= 1e4 else f"{v:,}"  # noqa: E731
f, ax = fig("村の倉から苦しい村へ出した量 (草の種、万つかみ)")
w = 0.36
ax.bar([y - w / 2 for y in YS], [hp[y] / 1e4 for y in YS], width=w, color=BLUE, label="年報の「この年に倉から出した量」")
ax.bar([y + w / 2 for y in YS], [gv[y] / 1e4 for y in YS], width=w, color=GRAY, label="120日目の年の集まりで決めた分も入れた数")
for y in YS:
    if hp[y]:
        ax.text(y - w / 2, hp[y] / 1e4 + 0.1, man(hp[y]), ha="center", color=BLUE, fontsize=11.5)
    if gv[y]:
        ax.text(y + w / 2, gv[y] / 1e4 + 0.1, man(gv[y]), ha="center", color=INK2, fontsize=11)
ax.axhline(3, color=ORANGE, lw=1.3, ls="--")
ax.text(164.55, 3.12, "条件 2: 1 年に 30,000 つかみ (3 集落以上)", color=ORANGE, fontsize=12)
fix_line(ax, FY, 6.6, f"{FY}年120日目\nお題を直した")
ax.set_ylim(0, 6.8); ax.set_ylabel("万つかみ", labelpad=10); years(ax)
ax.legend(loc="upper left", bbox_to_anchor=(0.0, 0.84), frameon=False, fontsize=12)
save(f, "c_help")

# 人の数
S = F["seasons"]; x_of = lambda s: s["day"] / 120  # noqa: E731
f, ax = fig("村の人の数 (季節ごと)")
ax.plot([x_of(s) for s in S], [s["pop"] for s in S], color=BLUE, lw=2.4)
ax.text(x_of(S[0]) + 0.1, S[0]["pop"] - 32, f"{S[0]['pop']} 人", color=INK, fontsize=14)
ax.text(x_of(S[-1]) - 0.05, S[-1]["pop"] + 14, f"{S[-1]['pop']} 人", color=INK, fontsize=14, ha="right")
ax.set_xlim(164.8, 173.2); ax.set_ylim(0, 420); ax.set_ylabel("人"); ax.set_xlabel("村の年")
ax.set_xticks(range(165, 174))
save(f, "c_pop")

# トークン (年報)
tk = iy(F["tok"])
f, ax = fig("1 年に使ったトークン (年報。万)")
ax.bar(YS, [tk[y] / 1e4 for y in YS], color=BLUE, width=0.55)
for y in YS:
    ax.text(y, tk[y] / 1e4 + 25, f"{tk[y] / 1e4:,.0f}", ha="center", color=INK, fontsize=11)
ax.axhline(1500, color=INK2, lw=1.3, ls="--")
ax.text(164.6, 1530, "点線 = 1 年の上限 1,500 万", color=INK2, fontsize=12.5)
ax.text(164.6, 1720, f"8 年で 約 {sum(tk.values()) / 1e4:,.0f} 万", color=INK, fontsize=15)
ax.set_ylim(0, 1850); ax.set_ylabel("万", labelpad=10); years(ax)
save(f, "c_tokens")
print("charts:", sorted(p.name for p in OUT.glob("*.png")))
