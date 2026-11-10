"""facts.json から G11 の動画の図 (PNG) を作る。python3 charts.py <facts.json> <出力フォルダ>
   形は g10/charts.py と同じ (軸 1 つ・青 = 主な数、だいだい = くらべる数、灰 = 背景。字は IPA ゴシック)。"""
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
YS = list(range(151, 165))
XT = list(range(151, 165))


def fig(title):
    f, ax = plt.subplots(figsize=(11.2, 5.0), dpi=150)
    ax.set_title(title, loc="left", fontsize=17, color=INK, pad=12)
    return f, ax


def save(f, name):
    f.tight_layout()
    f.savefig(OUT / f"{name}.png")
    plt.close(f)


def fix_line(ax, x, top, text, dx=0.12):
    ax.axvline(x, color=GRAY, lw=1, ls="--")
    ax.text(x + dx, top, text, color=INK2, fontsize=12, va="top")


def years(ax, lo=150.4, hi=164.6):
    ax.set_xticks(XT, [f"{y}" for y in XT]); ax.set_xlim(lo, hi); ax.set_xlabel("村の年", labelpad=6)


# 道の見張り: 選べた人と選んだ人 (年の集まりと秋の集まり、のべ)
pa = iy(F["path"])
f, ax = fig("道の見張り: 自分で選べた答える人と、選んだ人 (1 年の集まり 2 回、のべ)")
w = 0.36
ax.bar([y - w / 2 for y in YS], [pa[y]["c2"] for y in YS], width=w, color=BLUE, label="市の日を決められた人 (条件 2)")
ax.bar([y + w / 2 for y in YS], [pa[y]["c1"] for y in YS], width=w, color=GRAY, label="印で払う道を選べた人 (条件 1)")
ax.plot(YS, [pa[y]["chose"] for y in YS], color=ORANGE, lw=2.4, marker="o", ms=5, label="実際に選んだ人")
for y in YS:
    ax.text(y - w / 2, pa[y]["c2"] + 0.8, str(pa[y]["c2"]), ha="center", color=INK, fontsize=10.5)
    if pa[y]["c1"]:
        ax.text(y + w / 2, pa[y]["c1"] + 0.8, str(pa[y]["c1"]), ha="center", color=INK2, fontsize=10.5)
fix_line(ax, 157.5, 52, "157年の終わり\n直し 1")
fix_line(ax, 159.5, 52, "159年の終わり\n直し 2 (信頼)")
ax.set_ylim(0, 54); ax.set_ylabel("人", labelpad=10); years(ax)
ax.legend(loc="upper right", bbox_to_anchor=(1.0, 0.80), frameon=False, fontsize=12.5)
save(f, "c_path")

# 申し出 (1 年に来た数)
of = iy(F["offers_y"]); ty = F["trust_year"]
f, ax = fig("よその村の申し出 (1 年に来た数)。みな受けなかった")
ax.bar(YS, [of[y] for y in YS], color=[BLUE if y > ty else GRAY for y in YS], width=0.62)
for y in YS:
    if of[y]:
        ax.text(y, of[y] + 0.07, str(of[y]), ha="center", color=INK, fontsize=12)
fix_line(ax, ty + 0.5, 3.35, f"{ty}年の終わり\n信頼の決まりを直した")
b = sum(of[y] for y in YS if y <= ty); a = sum(of[y] for y in YS if y > ty)
ax.text(152.6, 2.75, f"151〜{ty}年: {b} 回", color=INK2, fontsize=14)
ax.text(161.9, 2.75, f"{ty + 1}〜164年: {a} 回", color=BLUE, fontsize=14, ha="center")
ax.text(161.9, 2.45, "受けた 0 回", color=ORANGE, fontsize=14, ha="center")
ax.set_ylim(0, 3.4); ax.set_yticks([0, 1, 2, 3]); ax.set_ylabel("回", labelpad=10); years(ax)
save(f, "c_offers")

# 地域のまとまり (北の大きな村) の段と集落の数 (G10 の条件 3 をならべて測る)
po = iy(F["polity"]); ys = [150] + YS
f, ax = fig("北の大きな村のまとまり (年の終わり)。G10 の条件 3 をならべて測る")
ax.plot(ys, [po[y]["n"] for y in ys], color=BLUE, lw=2.6, marker="o", ms=5, label="まとまりに入る集落")
ax.step(ys, [po[y]["need"] for y in ys], where="mid", color=ORANGE, lw=1.6, ls="--", label="要る数 (地域の半分)")
for y in ys:
    ax.text(y, 2.2, f"段 {po[y]['D']}", ha="center", fontsize=11, color=BLUE if po[y]["D"] >= 4 else INK2)
ax.text(150.0, po[150]["need"] + 0.35, f"{po[150]['need']}", color=ORANGE, fontsize=12, ha="center")
ax.text(164.0, po[164]["need"] + 0.35, f"{po[164]['need']}", color=ORANGE, fontsize=12, ha="center")
ax.text(150.6, 4.3, "段 4 になった年は青 (条件 3 は段 4 以上で、半分以上の集落)", color=INK2, fontsize=12)
ax.set_ylim(0, 13.5); ax.set_ylabel("集落", labelpad=10); years(ax, 149.4, 164.6)
ax.set_xticks(ys, [f"{y}" for y in ys])
ax.legend(loc="upper left", frameon=False, fontsize=13, ncol=2)
save(f, "c_polity")

# 人の数
S = F["seasons"]; x_of = lambda s: s["day"] / 120  # noqa: E731
f, ax = fig("村の人の数 (季節ごと)")
ax.plot([x_of(s) for s in S], [s["pop"] for s in S], color=BLUE, lw=2.4)
ax.text(x_of(S[0]) + 0.15, S[0]["pop"] - 30, f"{S[0]['pop']} 人", color=INK, fontsize=14)
ax.text(x_of(S[-1]) - 0.1, S[-1]["pop"] + 12, f"{S[-1]['pop']} 人", color=INK, fontsize=14, ha="right")
ax.set_xlim(150.8, 165.4); ax.set_ylim(0, 400); ax.set_ylabel("人"); ax.set_xlabel("村の年")
ax.set_xticks(range(151, 166, 2))
save(f, "c_pop")

# トークン (年報)
tk = iy(F["tok"])
f, ax = fig("1 年に使ったトークン (年報。万)")
ax.bar(YS, [tk[y] / 1e4 for y in YS], color=[ORANGE if tk[y] > 15e6 else BLUE for y in YS], width=0.62)
for y in YS:
    ax.text(y, tk[y] / 1e4 + 25, f"{tk[y] / 1e4:,.0f}", ha="center", color=INK, fontsize=10.5)
ax.axhline(1500, color=INK2, lw=1.3, ls="--")
ax.text(154.4, 1530, "点線 = 1 年の上限 1,500 万", color=INK2, fontsize=12.5)
ax.text(150.6, 2020, f"14 年で 約 {sum(tk.values()) / 1e8:.2f} 億", color=INK, fontsize=15)
ax.set_ylim(0, 2150); ax.set_ylabel("万", labelpad=10); years(ax)
save(f, "c_tokens")
print("charts:", sorted(p.name for p in OUT.glob("*.png")))
