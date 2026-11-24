"""大きな年の解説動画の絵 (1 文に 1 枚。1920x1080 の PNG)。python3.13 charts.py <explain_data.json> <reports/explain/yearY.json> <出力フォルダ>
   絵の中身は文の chart (図の id。tools/explain_data.py の CHARTS) で決める: 線の図 (t_*・k_*)・円 (c_*)・それ以外は文字の札。下に字幕。
   形と色は video/s3/charts.py と同じ (青 = 主な数、だいだい = めやすの線。字は IPA ゴシック)。出力: <出力>/<id>.png・lines.json (synth.py 用)・s99.png"""
import json
import sys
import textwrap
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
from matplotlib import font_manager  # noqa: E402

for f in ("/usr/share/fonts/opentype/ipafont-gothic/ipagp.ttf", "/usr/share/fonts/opentype/ipafont-gothic/ipag.ttf"):
    if Path(f).exists():
        font_manager.fontManager.addfont(f)
plt.rcParams.update({"font.family": ["IPAPGothic", "IPAGothic", "sans-serif"], "font.size": 18, "axes.edgecolor": "#b8b6b0",
                     "axes.labelcolor": "#52514e", "xtick.color": "#52514e", "ytick.color": "#52514e", "axes.spines.top": False,
                     "axes.spines.right": False, "figure.facecolor": "#fcfcfb", "axes.facecolor": "#fcfcfb", "axes.grid": True,
                     "grid.color": "#e6e4df", "axes.axisbelow": True})
BLUE, ORANGE, INK, INK2 = "#2a78d6", "#eb6834", "#0b0b0b", "#52514e"
PAL = ["#2a78d6", "#eb6834", "#1baf7a", "#eda100", "#e87ba4", "#008300", "#6250d6"]

D = json.load(open(sys.argv[1], encoding="utf-8"))
X = json.load(open(sys.argv[2], encoding="utf-8"))
OUT = Path(sys.argv[3]); OUT.mkdir(parents=True, exist_ok=True)
Y = D["year"]
LINE = {"t_pop": ("pop", 1, "人 (年の終わり)", None), "k_pop": ("pop", 1, "人 (年の終わり)", None),
        "t_gdp": ("gdp", 1, "村の生産 (大人 1 年分)", None), "k_gdp": ("gdp", 1, "村の生産 (大人 1 年分)", None),
        "t_store": ("store_min", 1, "蓄え (いちばん少ない日・日分)", 120), "k_store": ("store_min", 1, "蓄え (いちばん少ない日・日分)", 120),
        "t_lit": ("literacy", 100, "読める大人 (%)", 25), "k_lit": ("literacy", 100, "読める大人 (%)", 25),
        "t_nonfood": ("nonfood", 100, "食べ物でない仕事 (%)", 22), "k_nonfood": ("nonfood", 100, "食べ物でない仕事 (%)", 22),
        "k_imr": ("imr5", 1, "乳児死亡率 (5 年・出生千あたり)", None), "k_famine": ("famine", 1, "ききん (回)", None)}
DONUT = {"c_age": ("age", "年齢 3 区分の人口"), "c_work": ("work", "仕事の種類別の人日"), "c_food": ("food", "食べ物の生産 (熱量)")}


def frame():
    f = plt.figure(figsize=(12.8, 7.2), dpi=150)
    return f


def caption(f, text):
    f.text(0.5, 0.045, "\n".join(textwrap.wrap(text, 34)), ha="center", va="bottom", fontsize=24, color=INK,
           bbox={"boxstyle": "round,pad=0.5", "fc": "#ffffff", "ec": "#d8d6cf"})


def draw(line):
    cid = line.get("chart") or ""
    f = frame()
    if cid in LINE:
        k, m, title, goal = LINE[cid]
        s = D["series_12y"].get(k) or {}
        ys = sorted(int(y) for y in s)
        ax = f.add_axes([0.08, 0.30, 0.86, 0.58])
        ax.set_title(f"{title}  {ys[0] if ys else ''}〜{Y}年", loc="left", fontsize=24, color=INK, pad=14)
        if ys:
            v = [s[str(y)] * m for y in ys]
            ax.plot(ys, v, color=BLUE, lw=3.5, marker="o", ms=7)
            ax.annotate(f"{v[-1]:,.1f}" if m == 100 else f"{v[-1]:,.0f}", (ys[-1], v[-1]), textcoords="offset points", xytext=(8, 8), fontsize=20, color=INK)
            ax.set_xticks(ys[::2] + ([ys[-1]] if (len(ys) - 1) % 2 else []))
        if goal is not None:
            ax.axhline(goal, color=ORANGE, lw=2, ls="--")
            ax.text(ax.get_xlim()[0], goal, f" めやす {goal}", color=ORANGE, va="bottom", fontsize=17)
    elif cid in DONUT:
        k, title = DONUT[cid]
        rows = [(n, v) for n, v in (D["compo"].get(k) or {}).get("this") or [] if v > 0]
        ax = f.add_axes([0.25, 0.27, 0.5, 0.63])
        ax.set_title(f"{title}  ({Y}年)", fontsize=24, color=INK)
        if rows:
            ax.pie([v for _, v in rows], labels=[f"{n} {v / sum(x for _, x in rows) * 100:.0f}%" for n, v in rows], colors=PAL[:len(rows)],
                   startangle=90, counterclock=False, wedgeprops={"width": 0.38, "edgecolor": "#fcfcfb", "linewidth": 2}, textprops={"fontsize": 18})
    else:
        f.text(0.5, 0.66, f"川辺の村 {Y}年", ha="center", fontsize=46, color=INK)
        f.text(0.5, 0.54, "・".join(D["big_event"]["reasons"]) or "この年の大きなこと", ha="center", fontsize=26, color=INK2)
    caption(f, line["text"])
    f.savefig(OUT / f"{line['id']}.png")
    plt.close(f)


lines = (X.get("video") or {}).get("lines") or []
if not lines:
    sys.exit("動画の文がない (大きな年ではないか、解説の JSON に video.lines がない)")
for ln in lines:
    draw(ln)
f = frame()
f.text(0.5, 0.55, f"川辺の村 {Y}年 (解説の係)", ha="center", fontsize=40, color=INK)
f.text(0.5, 0.42, "声: VOICEVOX:ずんだもん", ha="center", fontsize=24, color=INK2)
f.savefig(OUT / "s99.png"); plt.close(f)
(OUT / "lines.json").write_text(json.dumps([{"id": x["id"], "text": x["text"], "say": x.get("say") or x["text"]} for x in lines], ensure_ascii=False, indent=1), encoding="utf-8")
print(f"絵 {len(lines) + 1} 枚と lines.json を {OUT} に書いた")
