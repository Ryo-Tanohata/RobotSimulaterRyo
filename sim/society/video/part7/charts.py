"""facts.json から第 7 部の動画の図 (PNG) を作る。python3.13 charts.py <facts.json> <出力フォルダ>
   形は g12/charts.py と同じ (軸 1 つ・青 = 主な数、だいだい = くらべる数、灰 = 背景。字は IPA ゴシック)。
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


def fig(title):
    f, ax = plt.subplots(figsize=(11.2, 5.0), dpi=150)
    ax.set_title(title, loc="left", fontsize=17, color=INK, pad=12)
    return f, ax


def save(f, name):
    f.tight_layout()
    f.savefig(OUT / f"{name}.png")
    plt.close(f)


def mark(ax, x, top, text, dx=0.12):
    ax.axvline(x, color=GRAY, lw=1, ls="--")
    ax.text(x + dx, top, text, color=INK2, fontsize=12, va="top")


def years(ax, ys, step=1):
    ax.set_xticks(ys[::step], [str(y) for y in ys[::step]]); ax.set_xlim(ys[0] - 0.6, ys[-1] + 0.6); ax.set_xlabel("村の年", labelpad=6)


# G13: 秋にまいた草の種のうち、水の来る畑の割合
wet = iy(F["wet"]); YS = list(range(173, 179))
f, ax = fig("秋にまいた草の種のうち、水の来る畑の割合 (G13)")
ax.bar(YS, [wet[y] for y in YS], width=0.55, color=BLUE)
for y in YS:
    ax.text(y, wet[y] + 2, f"{wet[y]}%", ha="center", color=INK, fontsize=14)
ax.axhline(50, color=ORANGE, lw=1.3, ls="--")
ax.text(172.45, 53, "条件 2: 半分以上の年が 2 年つづく", color=ORANGE, fontsize=12.5)
ax.set_ylim(0, 112); ax.set_ylabel("%", labelpad=10); years(ax, YS)
ax.set_xticks(YS, ["173", "174", "175", "176", "177", "178\n(60日目まで)"])
save(f, "c_wet")

# 手でひいた粉ひき (人日)
gr = iy(F["grind"]); YS = list(range(173, 193))
f, ax = fig("手で粉をひいた手間 (1 年の人日。6 時間働く大人で)")
ax.bar(YS, [gr[y] for y in YS], width=0.6, color=BLUE)
for y in YS:
    if gr[y]:
        ax.text(y, gr[y] + 30, f"{gr[y]:,}", ha="center", color=INK, fontsize=11.5)
ax.text(181, 380, "水の輪が粉をひいたので 0", color=INK2, fontsize=13, ha="center")
ax.annotate("184年の終わりに\n水の輪がみな止まった", xy=(185.32, gr[185] * 0.6), xytext=(187.3, 1250), color=ORANGE, fontsize=12.5,
            arrowprops=dict(arrowstyle="->", color=ORANGE, lw=1.2))
mark(ax, 178.42, 2080, "178年60日目\nG14 へ")
ax.set_ylim(0, 2150); ax.set_ylabel("人日", labelpad=10); years(ax, YS, 1)
ax.tick_params(axis="x", labelsize=11.5)
save(f, "c_grind")

# 水の輪の数 (年の終わり): 建っている輪と回っている輪
mi, ru = iy(F["mills"]), iy(F["running"])
f, ax = fig("水の輪の数 (年の終わり。みな村のもの)")
ax.bar(YS, [mi[y] for y in YS], width=0.62, color=GRAY, label="建っている輪")
ax.bar(YS, [ru[y] for y in YS], width=0.36, color=BLUE, label="そのうち回っている輪")
for y in YS:
    if mi[y]:
        ax.text(y, mi[y] + 0.5, str(mi[y]), ha="center", color=INK, fontsize=11.5)
ax.annotate("184年: 回っている 0", xy=(184, 0.3), xytext=(180.2, 12.5), color=ORANGE, fontsize=12.5,
            arrowprops=dict(arrowstyle="->", color=ORANGE, lw=1.2))
ax.annotate("191年: 22 のうち\n回っている 3", xy=(191, 3.3), xytext=(187.6, 27), color=ORANGE, fontsize=12.5,
            arrowprops=dict(arrowstyle="->", color=ORANGE, lw=1.2))
ax.axhline(2, color=INK2, lw=1.2, ls=":")
ax.text(172.5, 9.5, "点線: 村の人の粉には 2 つで足りる\n(1 つで 約 250 人分)", color=INK2, fontsize=12)
mark(ax, 185.5, 31.5, "185年の終わり\nお題の直し", dx=-0.1)
ax.set_ylim(0, 32); ax.set_ylabel("つ", labelpad=10); years(ax, YS, 1)
ax.tick_params(axis="x", labelsize=11.5)
ax.legend(loc="upper left", frameon=False, fontsize=12.5)
save(f, "c_mills")

# G14: 道の見張り (選んだ人)
ch = iy(F["chose14"]); YS = list(range(179, 194))
f, ax = fig("G14 の道を実際に選んだ人 (1 年の集まり 2 回、のべ)")
ax.bar(YS, [ch[y] for y in YS], width=0.6, color=BLUE)
for y in YS:
    ax.text(y, ch[y] + 0.3, str(ch[y]), ha="center", color=INK, fontsize=13)
mark(ax, 180.5, 16.6, "180年の終わり\nお題の直し")
mark(ax, 185.5, 16.6, "185年の終わり\n続けることの直し")
ax.set_ylim(0, 17); ax.set_yticks(range(0, 17, 4)); ax.set_ylabel("人", labelpad=10); years(ax, YS)
ax.set_xticks(YS, [str(y) if y < 193 else "193\n(60日目まで)" for y in YS])
save(f, "c_path")

# 町の家に住む人の割合
tw = iy(F["town"]); YS = list(range(178, 193))
f, ax = fig("町の家に住む人の割合 (地域の人のうち。年の終わり)")
ax.bar(YS, [100 * tw[y] for y in YS], width=0.6, color=BLUE)
for y in YS:
    ax.text(y, 100 * tw[y] + 0.2, f"{100 * tw[y]:.1f}", ha="center", color=INK, fontsize=11.5)
ax.axhline(10, color=ORANGE, lw=1.3, ls="--")
ax.text(177.5, 10.25, "条件 1: 1 割以上の年が 2 年つづく", color=ORANGE, fontsize=12.5)
ax.set_ylim(0, 11.5); ax.set_ylabel("%", labelpad=10); years(ax, YS)
ax.set_xticks(YS, [str(y) if y > 178 else "178\n(G13 の年)" for y in YS])
save(f, "c_town")

# 市へ運んで受けた草の種
mk = iy(F["market"]); YS = list(range(179, 193))
f, ax = fig("市へ運んで受けた草の種 (1 年。つかみ)")
ax.bar(YS, [mk[y] for y in YS], width=0.6, color=BLUE)
for y in YS:
    ax.text(y, mk[y] + 150, f"{mk[y]:,}" if mk[y] else "0", ha="center", color=INK if mk[y] else GRAY, fontsize=12)
ax.text(178.6, 9600, f"15 年で合わせて {sum(mk.values()):,} つかみ。村の倉 (約 300万〜500万つかみ) の 1% にもならない", color=INK2, fontsize=13)
ax.set_ylim(0, 10500); ax.set_ylabel("つかみ", labelpad=10); years(ax, YS)
save(f, "c_market")

# 人の数
S = F["seasons"]; x_of = lambda s: s["day"] / 120  # noqa: E731
f, ax = fig("村の人の数 (季節ごと)")
ax.plot([x_of(s) for s in S], [s["pop"] for s in S], color=BLUE, lw=2.4)
ax.text(x_of(S[0]) + 0.05, S[0]["pop"] + 22, f"{S[0]['pop']} 人", color=INK, fontsize=14)
ax.text(x_of(S[-1]) - 0.1, S[-1]["pop"] + 18, f"{S[-1]['pop']} 人", color=INK, fontsize=14, ha="right")
low = min(S[:8], key=lambda s: s["pop"])
ax.annotate(f"173年の終わり: 家が 1 つ村を出て {low['pop']} 人", xy=(x_of(low), low["pop"]), xytext=(x_of(low) + 1.0, 180), color=INK2, fontsize=12.5,
            arrowprops=dict(arrowstyle="->", color=GRAY, lw=1.2))
mark(ax, F["mid"] / 120, 520, "178年60日目\nG14 へ")
ax.set_xlim(172.6, 194); ax.set_ylim(0, 540); ax.set_ylabel("人"); ax.set_xlabel("村の年")
ax.set_xticks(range(173, 195, 2))
save(f, "c_pop")

# トークン (年報)
tk = iy(F["tok"]); YS = list(range(173, 194))
f, ax = fig("1 年に使ったトークン (年報。万)")
ax.bar(YS, [tk[y] / 1e4 for y in YS], color=BLUE, width=0.6)
ax.axhline(1500, color=INK2, lw=1.3, ls="--")
ax.text(172.5, 1530, "点線 = 1 年の上限 1,500 万", color=INK2, fontsize=12.5)
ax.text(172.5, 1720, f"21 の年報で 約 {sum(tk.values()) / 1e8:.2f} 億 (176年と180年は 1,200 万ちょうど。176年は見込みの数)", color=INK, fontsize=14)
ax.text(193, tk[193] / 1e4 + 25, "60日目\nまで", ha="center", color=INK2, fontsize=10.5)
mark(ax, 178.5, 1420, "G14 へ", dx=0.12)
ax.set_ylim(0, 1850); ax.set_ylabel("万", labelpad=10); years(ax, YS, 2)
save(f, "c_tokens")
print("charts:", sorted(p.name for p in OUT.glob("*.png")))
