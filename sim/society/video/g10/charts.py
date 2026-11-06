"""facts.json から G10 の動画の図 (PNG) を作る。python3 charts.py <facts.json> <出力フォルダ>
   形は g9/charts.py と同じ (軸 1 つ・青 = 主な数、だいだい = くらべる数、灰 = 背景。字は IPA ゴシック)。"""
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
YS = list(range(119, 151))
XT = list(range(120, 151, 5))


def fig(title):
    f, ax = plt.subplots(figsize=(11.2, 5.0), dpi=150)
    ax.set_title(title, loc="left", fontsize=17, color=INK, pad=12)
    return f, ax


def save(f, name):
    f.tight_layout()
    f.savefig(OUT / f"{name}.png")
    plt.close(f)


def fix_line(ax, top, text="133年の終わり\n仕組みを直した", x=133.5, dx=0.25):
    ax.axvline(x, color=GRAY, lw=1, ls="--")
    ax.text(x + dx, top, text, color=INK2, fontsize=12, va="top")


# 黒い金属の鎌 (1 年に何本) と、作った人
made = iy(F["made"]); sm = iy(F["smith_y"])
f, ax = fig("村で作った黒い金属の鎌 (1 年の本数)")
ax.bar(YS, [made.get(y, 0) for y in YS], color=BLUE, width=0.7)
for y in YS:
    if made.get(y, 0):
        ax.text(y, made[y] + 0.3, str(made[y]), ha="center", color=INK, fontsize=11)
ax.axvspan(127.6, 133.4, color="#eeede9", zorder=0)
ax.text(130.5, 15.2, "6 年 0 本", ha="center", color=INK2, fontsize=13)
fix_line(ax, 18.6)
for x0, x1, lab in [(127, 134.4, "ケセ19"), (134.6, 143.4, "ケセ19 + タユ25"), (143.6, 150.4, "ケセ19 + ロワ33")]:
    ax.annotate("", xy=(x0, 13.3), xytext=(x1, 13.3), arrowprops=dict(arrowstyle="<->", color=ORANGE, lw=1.3))
    ax.text((x0 + x1) / 2, 13.7, lab, ha="center", color=ORANGE, fontsize=12.5)
ax.text(119, 18.6, "合わせて 138 本", color=INK, fontsize=15, va="top")
ax.set_xticks(XT, [f"{y}年" for y in XT]); ax.set_xlim(118.4, 150.6); ax.set_ylim(0, 19.5); ax.set_ylabel("本", labelpad=10)
ax.set_yticks(range(0, 20, 5))
save(f, "c_made")

# 刈り入れの人日のうち、黒い金属・赤い金属の割合
rp = iy(F["reap"])
f, ax = fig("刈り入れの人日のうち、どの道具で刈ったか (%)")
ir = [100 * rp[y]["iron"] / rp[y]["all"] for y in YS]
br = [100 * rp[y]["bronze"] / rp[y]["all"] for y in YS]
ax.bar(YS, ir, color=BLUE, width=0.7, label="村で作った黒い金属")
ax.bar(YS, br, bottom=ir, color=ORANGE, width=0.7, label="赤い金属 (G9 で買った)")
ax.axhline(50, color=INK2, lw=1.3, ls="--")
ax.text(119, 52.5, "点線 = 1つめの条件 (半分)", color=INK2, fontsize=12.5)
v150 = 100 * rp[150]["iron"] / rp[150]["all"]
ax.text(150, v150 + 2, f"{v150:.0f}%", ha="center", color=BLUE, fontsize=13)
v142 = 100 * rp[142]["iron"] / rp[142]["all"]
ax.annotate(f"142年30日目\n条件 1 に届いた ({v142:.0f}%)", xy=(141.6, v142 - 4), xytext=(131.5, 80), color=INK, fontsize=12.5,
            arrowprops=dict(arrowstyle="->", color=INK2))
ax.set_xticks(XT, [f"{y}年" for y in XT]); ax.set_xlim(118.4, 150.6); ax.set_ylim(0, 100); ax.set_ylabel("%")
ax.legend(loc="upper left", bbox_to_anchor=(0, 0.92), frameon=False, fontsize=13)
save(f, "c_iron")

# 読み書きできる大人 (年の終わり)
rd = iy(F["readers"])
f, ax = fig("字を読み書きできる大人 (年の終わり)")
ax.bar(YS, [rd[y] for y in YS], color=BLUE, width=0.7)
for y in YS:
    if rd[y]:
        ax.text(y, rd[y] + 0.2, str(rd[y]), ha="center", color=INK, fontsize=11)
ax.axhline(2, color=ORANGE, lw=1.3, ls="--")
ax.text(119, 2.3, "点線 = 2 人 (2つめの条件の数)", color=ORANGE, fontsize=12.5)
ax.annotate("138年60日目\n音の字ができた (5 人)", xy=(138, 5.2), xytext=(130.2, 8.6), color=INK, fontsize=12.5,
            arrowprops=dict(arrowstyle="->", color=INK2))
ax.annotate("146年\n若い人 10 人が習った", xy=(145.6, 11.0), xytext=(138.6, 11.6), color=INK, fontsize=12.5,
            arrowprops=dict(arrowstyle="->", color=INK2))
ax.set_xticks(XT, [f"{y}年" for y in XT]); ax.set_xlim(118.4, 150.6); ax.set_ylim(0, 14); ax.set_ylabel("人")
save(f, "c_readers")

# いちばん大きなまとまり (集落の数) と、要る数
po = iy(F["polity"]); ys = [118] + YS
f, ax = fig("北の大きな村のまとまりに入る集落の数 (年の終わり。段はずっと 3)")
ax.plot(ys, [po[y]["n83"] for y in ys], color=BLUE, lw=2.6, marker="o", ms=4, label="北の大きな村のまとまり")
ax.step(ys, [po[y]["need"] for y in ys], where="mid", color=ORANGE, lw=1.6, ls="--", label="条件 3 に要る数 (地域の半分)")
ax.axvspan(129.5, 135.5, color="#eeede9", zorder=0)
ax.text(132.5, 18.2, "地域の悪い年が\n6 年続いた", ha="center", color=INK2, fontsize=12.5, va="top")
ax.text(150.2, po[150]["n83"] - 1.6, f"{po[150]['n83']}", color=INK, fontsize=14, ha="center")
ax.text(118.6, 17.6, "段 4 にも届かなかった", color=INK, fontsize=13.5)
ax.set_xticks(XT, [f"{y}年" for y in XT]); ax.set_xlim(117.6, 151); ax.set_ylim(0, 19); ax.set_ylabel("集落")
ax.legend(loc="lower left", frameon=False, fontsize=13)
save(f, "c_polity")

# 人の数
S = F["seasons"]; x_of = lambda s: s["day"] / 120  # noqa: E731
f, ax = fig("村の人の数 (季節ごと)")
ax.plot([x_of(s) for s in S], [s["pop"] for s in S], color=BLUE, lw=2.4)
ax.text(x_of(S[0]) + 0.3, S[0]["pop"] + 12, f"{S[0]['pop']} 人", color=INK, fontsize=14)
ax.text(x_of(S[-1]) - 0.2, S[-1]["pop"] + 10, f"{S[-1]['pop']} 人", color=INK, fontsize=14, ha="right")
ax.annotate("124年の終わり\nワユ3の家 36 人が出た", xy=(125, 173), xytext=(126.5, 95), color=INK, fontsize=12.5,
            arrowprops=dict(arrowstyle="->", color=INK2))
ax.set_xlim(118.4, 151.2); ax.set_ylim(0, 350); ax.set_ylabel("人"); ax.set_xlabel("村の年")
save(f, "c_pop")
print("charts:", sorted(p.name for p in OUT.glob("*.png")))
