"""facts.json から「Society 3.0 これまで」の動画の図 (PNG) を作る。python3.13 charts.py <facts.json> <出力フォルダ>
   形は part7/charts.py と同じ (軸 1 つ・青 = 主な数、だいだい = 目安の線、灰 = 背景。字は IPA ゴシック)。
   色は dataviz の確かめ (validate_palette.js: #2a78d6・#eb6834 は明るい面でみな通る) をしてある。"""
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
PH = [(203.5, "フェーズ 1"), (215.5, "フェーズ 2"), (224.5, "フェーズ 3"), (231.5, "フェーズ 4")]


def fig(title):
    f, ax = plt.subplots(figsize=(11.2, 5.0), dpi=150)
    ax.set_title(title, loc="left", fontsize=17, color=INK, pad=12)
    return f, ax


def save(f, name):
    f.tight_layout()
    f.savefig(OUT / f"{name}.png")
    plt.close(f)


def mark(ax, x, top, text, dx=0.12, fs=12):
    ax.axvline(x, color=GRAY, lw=1, ls="--")
    ax.text(x + dx, top, text, color=INK2, fontsize=fs, va="top")


def phases(ax, top, lo=200):
    for x, t in PH:
        if x > lo:
            mark(ax, x, top, t, fs=11.5)


def years(ax, ys, step=1):
    ax.set_xticks(ys[::step], [str(y) for y in ys[::step]]); ax.set_xlim(ys[0] - 0.6, ys[-1] + 0.6); ax.set_xlabel("村の年", labelpad=6)


# 掘った燃える石 (1 年。万 kg)
co = iy(F["coal"]); YS = list(range(201, 233))
f, ax = fig("村の人が掘った燃える石 (1 年。万 kg)")
ax.bar(YS, [co[y] / 1e4 for y in YS], width=0.6, color=BLUE)
for y in YS:
    if co[y] >= 50000:
        ax.text(y, co[y] / 1e4 + 0.5, f"{co[y] / 1e4:.1f}", ha="center", color=INK, fontsize=11.5)
ax.text(200.5, 6.5, "201〜203年\n0 kg", color=INK2, fontsize=12)
phases(ax, 24)
ax.set_ylim(0, 24); ax.set_ylabel("万 kg", labelpad=10); years(ax, YS, 2)
save(f, "c_coal")

# 作業場の持ち場の人 (年の終わり)
po, bg = iy(F["posts"]), iy(F["big"]); YS = list(range(204, 233))
f, ax = fig("作業場の持ち場についている人 (年の終わり)")
ax.bar(YS, [po[y] for y in YS], width=0.6, color=BLUE)
for y in YS:
    if po[y] and (y in (209, 224, 232) or y < 209):
        ax.text(y, po[y] + 0.8, str(po[y]), ha="center", color=INK, fontsize=12)
ax.text(203.6, 44, "作業場に 8 人そろった日 (1 年):\n208年まで 0 日 → 209年 90 日 → 210〜232年 毎年 120 日", color=INK, fontsize=13, va="top")
for x, t in PH[1:]:
    mark(ax, x, 58, t, fs=11.5)
ax.set_ylim(0, 58); ax.set_ylabel("人", labelpad=10); years(ax, YS, 2)
save(f, "c_posts")

# 年の集まりで町の家を聞いた答え (222〜224年)
ak = iy(F["asked"]); YS = [222, 223, 224]
f, ax = fig("年の集まりで「町の家を出すか」を聞いた答え (答える人)")
w = 0.26
for i, (k, lab, c) in enumerate([("yes", "出す", BLUE), ("no", "出さない", ORANGE), ("quiet", "書かなかった", GRAY)]):
    xs = [y + (i - 1) * w for y in YS]
    ax.bar(xs, [ak[y][k] for y in YS], width=w * 0.92, color=c, label=lab)
    for x, y in zip(xs, YS):
        ax.text(x, ak[y][k] + 0.6, str(ak[y][k]), ha="center", color=INK, fontsize=13)
ax.text(221.55, 44, f"3 年で「出す」 0 人・「出さない」 のべ {sum(ak[y]['no'] for y in YS)} 人", color=INK, fontsize=14)
ax.set_ylim(0, 48); ax.set_ylabel("人", labelpad=10); ax.set_xticks(YS, [f"{y}年" for y in YS]); ax.set_xlim(221.5, 224.5)
ax.legend(loc="upper right", frameon=False, fontsize=12.5, ncol=3)
save(f, "c_ask")

# 読める大人の割合
rd = iy(F["readers"]); YS = list(range(225, 233))
f, ax = fig("読める大人の割合 (大人のうち。年の終わり)")
ax.bar(YS, [rd[y]["pct"] for y in YS], width=0.6, color=BLUE)
for y in YS:
    ax.text(y, rd[y]["pct"] + 0.6, f"{rd[y]['pct']:.0f}%\n({rd[y]['n']} 人)", ha="center", color=INK, fontsize=12)
ax.axhline(25, color=ORANGE, lw=1.3, ls="--")
ax.text(224.5, 25.6, "目安 25%", color=ORANGE, fontsize=12.5)
mark(ax, 231.5, 37, "フェーズ 4", fs=11.5)
ax.set_ylim(0, 37); ax.set_ylabel("%", labelpad=10); years(ax, YS)
save(f, "c_readers")

# 知らせ板の知らせ
nt = iy(F["notes"]); YS = list(range(225, 233))
f, ax = fig("知らせ板の知らせ (1 年の枚数と、書いた家の数)")
ax.bar(YS, [nt[y]["n"] for y in YS], width=0.6, color=BLUE)
for y in YS:
    ax.text(y, nt[y]["n"] + 0.2, f"{nt[y]['n']} 枚\n({nt[y]['houses']} 家)", ha="center", color=INK, fontsize=12)
ax.axhline(6, color=ORANGE, lw=1.3, ls="--")
ax.text(224.5, 6.15, "目安 6 枚・4 家", color=ORANGE, fontsize=12.5)
mark(ax, 231.5, 10.4, "フェーズ 4", fs=11.5)
ax.set_ylim(0, 10.5); ax.set_ylabel("枚", labelpad=10); years(ax, YS)
save(f, "c_notes")

# 燃える石が火と力に占める割合
sh = iy(F["share"]); YS = list(range(200, 233))
f, ax = fig("燃える石が、火と力 (熱) に占める割合 (1 年)")
ax.plot(YS, [sh[y] for y in YS], color=BLUE, lw=2.4, marker="o", ms=4)
ax.axhline(50, color=ORANGE, lw=1.3, ls="--")
ax.text(199.6, 51.2, "半分", color=ORANGE, fontsize=12.5)
for y in (200, 215, 230, 232):
    ax.annotate(f"{sh[y]:.0f}%", (y, sh[y]), textcoords="offset points", xytext={200: (0, 9), 230: (-22, 2)}.get(y, (0, -20)), ha="center", color=INK, fontsize=12.5)
phases(ax, 74, lo=200)
ax.set_ylim(0, 75); ax.set_ylabel("%", labelpad=10); years(ax, YS, 2)
save(f, "c_share")

# 人の数
S = F["seasons"]; x_of = lambda s: s["day"] / 120  # noqa: E731
f, ax = fig("村の人の数 (季節ごと)")
ax.plot([x_of(s) for s in S], [s["pop"] for s in S], color=BLUE, lw=2.4)
ax.text(x_of(S[0]) + 0.1, S[0]["pop"] - 60, f"{S[0]['pop']} 人", color=INK, fontsize=14)
ax.text(x_of(S[-1]) - 0.1, S[-1]["pop"] + 22, f"{S[-1]['pop']} 人", color=INK, fontsize=14, ha="right")
ax.text(201, 120, "32 年で ききん 0。季節の終わりの蓄えのいちばん少ない日は 205年の 90 日分", color=INK2, fontsize=13)
phases(ax, 860, lo=200)
ax.set_xlim(200.6, 233.2); ax.set_ylim(0, 870); ax.set_ylabel("人"); ax.set_xlabel("村の年")
ax.set_xticks(range(201, 234, 2))
save(f, "c_pop")

# トークン (年報)
tk = iy(F["tok"]); YS = list(range(201, 233))
f, ax = fig("1 年に使ったトークン (年報。万)")
ax.bar(YS, [tk[y] / 1e4 for y in YS], color=BLUE, width=0.6)
ax.axhline(1500, color=INK2, lw=1.3, ls="--")
ax.text(200.5, 1530, "点線 = 1 年の上限 1,500 万", color=INK2, fontsize=12.5)
ax.text(200.5, 1720, f"32 の年報で 約 {sum(tk.values()) / 1e8:.2f} 億 (203年は途中から数えた分だけ。214年は年報の数のまま)", color=INK, fontsize=14)
ax.set_ylim(0, 1850); ax.set_ylabel("万", labelpad=10); years(ax, YS, 2)
save(f, "c_tokens")
print("charts:", sorted(p.name for p in OUT.glob("*.png")))
