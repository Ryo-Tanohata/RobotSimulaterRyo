"""年報の動画の絵 (1 文に 1 枚、1280x720 の PNG)。
   python3.13 charts.py <explain_data.json> <作業フォルダ (script.json がある)> <voices.json>
   → <作業>/charts/<図>.png (図だけ、1280x560)・<作業>/<id>.png (1 文の絵)・<作業>/s99.png (クレジット)

1 文の絵: 上 = 図 (年報のダッシュボードと統計のページの図を、動画の大きさで描きなおしたもの)、
下の帯 = 話す人の顔 (その文の顔つき) と名前の札、字幕。
図の形と色は年報と同じ考え (青 = 主な数、だいだい = めやすの線、灰の点線 = 決まりを直した区切りの年 242年)。字は IPA ゴシック。
図の id は tools/explain_data.py の CHARTS (t_* 線・k_* 数のタイル・c_* 円・phase 物差し・f_* 統計のページの分野) と title・title_end。
"""
import json
import sys
import textwrap
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
from matplotlib import font_manager  # noqa: E402
from PIL import Image, ImageDraw, ImageFont  # noqa: E402

FONTS = [f for f in ("/usr/share/fonts/opentype/ipafont-gothic/ipagp.ttf", "/usr/share/fonts/opentype/ipafont-gothic/ipag.ttf") if Path(f).exists()]
for f in FONTS:
    font_manager.fontManager.addfont(f)
plt.rcParams.update({"font.family": ["IPAPGothic", "IPAGothic", "sans-serif"], "font.size": 16, "axes.edgecolor": "#b8b6b0",
                     "axes.labelcolor": "#52514e", "xtick.color": "#52514e", "ytick.color": "#52514e", "axes.spines.top": False,
                     "axes.spines.right": False, "figure.facecolor": "#fcfcfb", "axes.facecolor": "#fcfcfb", "axes.grid": True,
                     "grid.color": "#e6e4df", "axes.axisbelow": True})
BLUE, ORANGE, INK, INK2, GRID = "#2a78d6", "#eb6834", "#0b0b0b", "#52514e", "#b8b6b0"
PAL = ["#2a78d6", "#eb6834", "#1baf7a", "#eda100", "#e87ba4", "#008300", "#6250d6"]
W, H, CH = 1280, 720, 560   # 絵の大きさと、図の高さ (下の 160 は顔と字幕の帯)
FIX_YEAR = 242               # 決まりを直した区切りの年 (年報の図の縦の点線)

D = json.load(open(sys.argv[1], encoding="utf-8"))
WORK = Path(sys.argv[2])
V = json.load(open(sys.argv[3], encoding="utf-8"))
S = json.load(open(WORK / "script.json", encoding="utf-8"))
ROOT = Path(__file__).resolve().parents[4]
GUIDE = ROOT / "sim/society/app/guide"
BIG = ROOT / "sim/society/out/human"
Y = D["year"]
T, L = D["this_year"], D["last_year"]
(WORK / "charts").mkdir(parents=True, exist_ok=True)

LINE = {"t_pop": ("pop", 1, "人 (年の終わり)", None, "人"), "t_gdp": ("gdp", 1, "村の生産 (大人 1 年分の食べ物に直して)", None, ""),
        "t_store": ("store_min", 1, "蓄え (1 年でいちばん少ない日)", D["goals"]["store_days"], "日分"),
        "t_lit": ("literacy", 100, "字が読める大人の割合", D["goals"]["literacy_pct"], "%"),
        "t_nonfood": ("nonfood", 100, "食べ物でない仕事の割合", D["goals"]["nonfood_pct"], "%")}
# 数のタイル: (見出し, this_year のキー, 掛ける数, 単位, 12 年の線のキー)
TILE = {"k_pop": ("人口 (年の終わり)", "pop", 1, "人", "pop"), "k_gdp": ("村の生産", "gdp", 1, "", "gdp"),
        "k_store": ("蓄え (いちばん少ない日)", "store_min", 1, "日分", "store_min"), "k_nonfood": ("食べ物でない仕事", "nonfood", 100, "%", "nonfood"),
        "k_lit": ("字が読める大人", "literacy", 100, "%", "literacy"), "k_imr": ("乳児死亡率 (5 年の平均・出生千あたり)", "imr5", 1, "", "imr5"),
        "k_famine": ("ききん", "famine", 1, "回", "famine")}
DONUT = {"c_age": ("age", "年齢 3 区分の人口"), "c_work": ("work", "仕事の種類別の人日"), "c_food": ("food", "食べ物の生産 (熱量)")}
# 統計のページの分野のカード: (見出し, [(名前, キー, 掛ける数, 単位, 小数)])
CARD = {"f_pop": ("人口と世帯", [("総人口", "pop", 1, "人", 0), ("世帯", "households", 1, "", 0), ("村の帳の人数", "count_people", 1, "人", 0)]),
        "f_vital": ("出生と死亡", [("生まれた子", "births", 1, "人", 0), ("亡くなった人", "deaths", 1, "人", 0), ("平均寿命", "e0", 1, "歳", 1), ("合計特殊出生率", "tfr", 1, "", 2)]),
        "f_health": ("健康", [("1 歳前に亡くなった子", "infant_deaths", 1, "人", 0), ("乳児死亡率 (出生千あたり)", "imr", 1, "", 0),
                              ("病で亡くなった人", "sick_deaths", 1, "人", 0), ("手当てが届いた子", "care_kids", 1, "人", 0)]),
        "f_econ": ("経済", [("村の生産", "gdp", 1, "", 0), ("1 人あたり", "gdp_pc", 1, "", 2), ("去年からの伸び", "gdp_growth", 100, "%", 0)]),
        "f_work": ("仕事", [("働いた人日", "work_days", 1, "", 0), ("食べ物の仕事", "work_food", 100, "%", 1), ("休んだ日", "rest_share", 100, "%", 1)]),
        "f_food": ("農業と食べ物", [("刈った草の種", "harvest", 1, "つかみ", 0), ("1 人 1 日の熱量", "kcal_pc", 1, "", 0), ("蓄え (いちばん少ない日)", "store_min", 1, "日分", 0)]),
        "f_living": ("暮らしと差", [("持ち物の差 (ジニ係数)", "wealth_gini", 1, "", 2), ("倉を持つ家の差", "house_gini", 1, "", 2), ("雨の夜に外にいた人", "rain_out", 1, "人", 0)]),
        "f_rules": ("村の決まり", [("生きている掟", "laws", 1, "", 0), ("新しいもめごと", "disputes", 1, "", 0)]),
        "f_edu": ("教育", [("字が読める大人", "readers", 1, "人", 0), ("読める割合", "literacy", 100, "%", 1), ("字を覚えた子", "kids_taught", 1, "人", 0)]),
        "f_env": ("環境とエネルギー", [("燃やした燃える石", "coal_burned", 1, "kg", 0), ("水の道を掘った人日", "canal_days", 1, "", 0)]),
        "f_ext": ("外とのつながり", [("よそから入った草の種", "trade_in", 1, "つかみ", 0), ("相手の村", "partners", 1, "", 0), ("果たした町の頼み", "town_done", 1, "", 0)])}
# 子の手当て (よその村・町の係。町の払いの子の薬と手当ての書きつけ)。去年の数がないものは「去年」を書かない
CARE = ("子の手当て", [("手当てが届いた子", "care_kids", "人"), ("子の薬を使った", "meds_used", "包み"), ("5 歳までに亡くなった子", "u5_dead", "人"),
                      ("家にある子の薬", "meds_now", "包み")])
COLOR = {"sona85": "#8a5a2b", "kio85": "#b84f72", "nei75": "#3f7d3a", "kese98": "#2a5fa8", "nase110": "#c0661a"}


def fig():
    return plt.figure(figsize=(W / 100, CH / 100), dpi=100)


def fmt(v, nd=0):
    if v is None:
        return "—"
    return f"{v:,.{nd}f}"


def line_chart(cid):
    k, m, title, goal, unit = LINE[cid]
    s = D["series_12y"].get(k) or {}
    ys = sorted(int(y) for y in s)
    f = fig()
    ax = f.add_axes([0.07, 0.11, 0.88, 0.74])
    f.text(0.07, 0.92, f"{title}  {ys[0] if ys else ''}〜{Y}年", fontsize=24, color=INK)
    if ys:
        v = [s[str(y)] * m for y in ys]
        ax.plot(ys, v, color=BLUE, lw=3.5, marker="o", ms=7, zorder=3)
        ax.plot([ys[-1]], [v[-1]], "o", color=BLUE, ms=13, zorder=4)
        ax.annotate(f"{fmt(v[-1], 1 if m == 100 else 0)}{unit}", (ys[-1], v[-1]), textcoords="offset points", xytext=(-12, 14), ha="right", fontsize=22, color=INK)
        ax.set_xticks(ys)
        ax.set_xticklabels([f"{y}" for y in ys])
        if ys[0] <= FIX_YEAR <= ys[-1]:
            ax.axvline(FIX_YEAR, color=GRID, lw=1.5, ls=":")
    if goal is not None:
        ax.axhline(goal, color=ORANGE, lw=2)
        ax.text(ax.get_xlim()[0], goal, f" めやす {goal}{unit}", color=ORANGE, va="bottom", fontsize=16)
    return f


def tile_chart(cid):
    title, key, m, unit, sk = TILE[cid]
    v, lv = (T.get(key) or 0) * m, (L.get(key) or 0) * m
    nd = 1 if m == 100 else 0
    f = fig()
    f.text(0.07, 0.86, f"{title}  ({Y}年)", fontsize=26, color=INK)
    f.text(0.07, 0.48, f"{fmt(v, nd)}", fontsize=96, color=BLUE)
    f.text(0.07, 0.36, unit, fontsize=26, color=INK2)
    d = v - lv
    f.text(0.07, 0.2, f"去年 {fmt(lv, nd)}{unit}  ({'+' if d >= 0 else '−'}{fmt(abs(d), nd)})", fontsize=24, color=INK2)
    s = D["series_12y"].get(sk) or {}
    if s:
        ys = sorted(int(y) for y in s)
        ax = f.add_axes([0.5, 0.18, 0.44, 0.58])
        ax.plot(ys, [s[str(y)] * m for y in ys], color=BLUE, lw=3, marker="o", ms=5)
        ax.set_title("12 年のうつりかわり", fontsize=16, color=INK2, loc="left")
        ax.set_xticks(ys[::3] + ([ys[-1]] if (len(ys) - 1) % 3 else []))
    return f


def donut_chart(cid):
    """円 (今年) と、右に中身の表 (今年と去年の割合)。小さなかけらには円の上に字を書かない"""
    k, title = DONUT[cid]
    f = fig()
    f.text(0.07, 0.9, f"{title}  ({Y}年)", fontsize=24, color=INK)
    c = D["compo"].get(k) or {}
    last = dict(c.get("last") or [])
    rows0 = [(n, v) for n, v in c.get("this") or [] if v > 0]
    if not rows0:
        return f
    tot = sum(v for _, v in rows0)
    ltot = sum(v for v in last.values() if v > 0) or 1
    # 3% より小さいかけらは「そのほか」にまとめる (円の上も表も重ならないように。本人の直し 2026-11-24)
    big = [(n, v) for n, v in rows0 if v / tot >= 0.03 and n != "そのほか"]
    small = [n for n, v in rows0 if (n, v) not in big]
    rows = big + ([("そのほか", sum(v for n, v in rows0 if n in small))] if small else [])
    last = {**{n: last.get(n, 0) for n, _ in big}, "そのほか": sum(v for n, v in last.items() if n in small or n not in dict(big))}
    ax = f.add_axes([0.05, 0.04, 0.42, 0.8])
    ax.pie([v for _, v in rows], colors=PAL[:len(rows)], startangle=90, counterclock=False,
           wedgeprops={"width": 0.38, "edgecolor": "#fcfcfb", "linewidth": 2})
    ax.text(0, 0, f"{Y}年", ha="center", va="center", fontsize=20, color=INK2)
    if small:
        f.text(0.53, 0.66 - len(rows) * 0.085 - 0.02, "そのほか: " + "・".join(small), fontsize=15, color=INK2)
    f.text(0.74, 0.76, f"{Y}年", fontsize=18, color=INK2, ha="right")
    f.text(0.9, 0.76, f"{Y - 1}年", fontsize=18, color=INK2, ha="right")
    for i, (n, v) in enumerate(rows):
        y = 0.66 - i * 0.085
        f.patches.append(plt.Rectangle((0.5, y), 0.018, 0.04, transform=f.transFigure, fc=PAL[i % len(PAL)], ec="none"))
        f.text(0.53, y, n, fontsize=20, color=INK)
        f.text(0.74, y, f"{v / tot * 100:.1f}%", fontsize=20, color=INK, ha="right")
        f.text(0.9, y, f"{last.get(n, 0) / ltot * 100:.1f}%", fontsize=20, color=INK2, ha="right")
    return f


def phase_chart():
    """いまのフェーズの物差し (D1 のときは d1〜d5 の表)"""
    f = fig()
    rows = D.get("d1_rows") or []
    f.text(0.07, 0.88, f"村のようすの物差し  ({Y}年)", fontsize=24, color=INK)
    f.text(0.93, 0.88, "○ 記録どおりの幅  × まだ", fontsize=16, color=INK2, ha="right")
    if D.get("phase_panel") != "d1" or not rows:
        f.text(0.07, 0.5, D.get("phase_name") or "", fontsize=28, color=INK2)
        return f
    r = rows[-1]
    # 中の呼び名 (d1 など) は出さない。○ は記録の幅に入っている、× はまだ
    items = [("寿命 (平均寿命)", f"{r['e0']:.1f} 歳", r["d1_ok"]), ("15 歳からの寿命", f"{r['e15']:.1f} 年", r["d2_ok"]),
             ("人のふえかた (1 年)", f"{r['nat']:.2f} %", r["d3_ok"]), ("生まれる子の数 (女の人 1 人)", f"{r['tfr']:.2f} 人", r["d4_ok"]),
             ("蓄えの守り", f"年の終わり {r['store_end']} 日分", r["d5_ok"])]
    for i, (a, b, ok) in enumerate(items):
        y = 0.72 - i * 0.14
        f.text(0.1, y, a, fontsize=24, color=INK)
        f.text(0.52, y, b, fontsize=24, color=INK2)
        f.text(0.82, y - 0.01, "○" if ok else "×", fontsize=36, color=BLUE if ok else ORANGE)
    return f


def card_chart(cid):
    title, items = CARD[cid]
    f = fig()
    f.text(0.07, 0.88, f"{title}  ({Y}年・統計のページ)", fontsize=24, color=INK)
    n = len(items)
    w = 0.86 / n
    for i, (lab, key, m, unit, nd) in enumerate(items):
        x = 0.07 + i * w
        v, lv = T.get(key), L.get(key)
        f.patches.append(plt.Rectangle((x, 0.14), w - 0.02, 0.62, transform=f.transFigure, fc="#ffffff", ec="#d8d6cf", lw=1.5))
        f.text(x + 0.015, 0.66, "\n".join(textwrap.wrap(lab.replace(" ", "\u00a0"), 9)), fontsize=18, color=INK2, va="top")
        f.text(x + 0.015, 0.36, f"{fmt(v * m if v is not None else None, nd)}", fontsize=46 if n > 3 else 54, color=BLUE)
        f.text(x + 0.015, 0.28, unit, fontsize=18, color=INK2)
        f.text(x + 0.015, 0.18, f"去年 {fmt(lv * m if lv is not None else None, nd)}{unit}", fontsize=17, color=INK2)
    return f


def care_chart():
    title, items = CARE
    cc = D.get("child_care") or {}
    f = fig()
    f.text(0.07, 0.88, f"{title}  ({Y}年)", fontsize=24, color=INK)
    w = 0.86 / len(items)
    for i, (lab, key, unit) in enumerate(items):
        x = 0.07 + i * w
        v = T.get(key) if key in T else cc.get(key)
        lv = L.get(key) if key in L else None
        f.patches.append(plt.Rectangle((x, 0.14), w - 0.02, 0.62, transform=f.transFigure, fc="#ffffff", ec="#d8d6cf", lw=1.5))
        f.text(x + 0.015, 0.66, "\n".join(textwrap.wrap(lab.replace(" ", "\u00a0"), 9)), fontsize=18, color=INK2, va="top")
        f.text(x + 0.015, 0.36, fmt(v), fontsize=46, color=BLUE)
        f.text(x + 0.015, 0.28, unit, fontsize=18, color=INK2)
        if lv is not None:
            f.text(x + 0.015, 0.18, f"去年 {fmt(lv)}{unit}", fontsize=17, color=INK2)
    return f


def title_chart(end=False):
    f = fig()
    f.text(0.5, 0.62, f"川辺の村 {Y}年", ha="center", fontsize=60, color=INK)
    if D.get("year_name"):
        f.text(0.5, 0.45, f"「{D['year_name']}」", ha="center", fontsize=32, color=INK2)
    f.text(0.5, 0.27, "年報の動画 — 村の係がお話しします" if not end else "また来年", ha="center", fontsize=24, color=INK2)
    return f


def chart(cid):
    p = WORK / "charts" / f"{cid}.png"
    if p.exists():
        return p
    if cid in LINE:
        f = line_chart(cid)
    elif cid in TILE:
        f = tile_chart(cid)
    elif cid in DONUT:
        f = donut_chart(cid)
    elif cid == "phase":
        f = phase_chart()
    elif cid in CARD:
        f = card_chart(cid)
    elif cid == "x_care":
        f = care_chart()
    else:
        f = title_chart(cid == "title_end")
    f.savefig(p)
    plt.close(f)
    return p


def font(sz):
    return ImageFont.truetype(FONTS[0], sz)  # IPA P ゴシック (字の幅が自然)


def face(img, expr, px):
    for p in (BIG / f"guide_{img}_{expr}.png", GUIDE / f"{img}_{expr}.png", BIG / f"guide_{img}_neutral.png", GUIDE / f"{img}_neutral.png"):
        if p.exists():
            im = Image.open(p).convert("RGB")
            break
    else:
        im = Image.new("RGB", (px, px), "#e6e1d8")
    w, h = im.size
    s = min(w, h)
    im = im.crop(((w - s) // 2, 0, (w - s) // 2 + s, s)).resize((px, px), Image.LANCZOS)
    mask = Image.new("L", (px * 4, px * 4), 0)
    ImageDraw.Draw(mask).ellipse((0, 0, px * 4 - 1, px * 4 - 1), fill=255)
    return im, mask.resize((px, px), Image.LANCZOS)


def wrap_px(d, text, fnt, maxw):
    """字幕を幅で折る。数や英字の途中と、句読点・閉じかっこの前では切らない"""
    def ok(a, b):
        al = lambda c: c.isascii() and (c.isalnum() or c in ".,")  # noqa: E731
        return not (al(a) and al(b)) and b not in "、。」)）％%"

    out, cur = [], ""
    for ch in text:
        if cur and d.textlength(cur + ch, font=fnt) > maxw:
            t = cur + ch
            k = len(cur)
            while k > 1 and not ok(t[k - 1], t[k]):
                k -= 1
            if k <= 1:
                k = len(cur)
            out.append(t[:k])
            cur = t[k:]
        else:
            cur += ch
    if cur:
        out.append(cur)
    return out


def frame(ln):
    p = V["people"][ln["who"]]
    im = Image.new("RGB", (W, H), "#fcfcfb")
    im.paste(Image.open(chart(ln["chart"])).convert("RGB"), (0, 0))
    d = ImageDraw.Draw(im)
    d.rectangle((0, CH, W, H), fill="#f3efe6")
    d.line((0, CH, W, CH), fill="#d8d6cf", width=2)
    col = COLOR.get(ln["who"], "#52514e")
    fc, mk = face(p["img"], ln["expr"], 132)
    d.ellipse((20, CH - 26, 20 + 140, CH - 26 + 140), fill=col)
    im.paste(fc, (24, CH - 22), mk)
    tag = f"{p['name']}  {p['role']}"
    f_tag = font(20)
    tw = d.textlength(tag, font=f_tag)
    d.rounded_rectangle((14, H - 44, 14 + tw + 24, H - 12), radius=8, fill=col)
    d.text((26, H - 41), tag, font=f_tag, fill="#ffffff")
    f_sub = font(30)
    x0 = 184
    lines = wrap_px(d, ln["text"], f_sub, W - x0 - 28)
    if len(lines) > 3:
        f_sub = font(25)
        lines = wrap_px(d, ln["text"], f_sub, W - x0 - 28)
    lh = f_sub.size + 10
    y = CH + (H - CH - lh * len(lines)) // 2 - 2
    for t in lines:
        d.text((x0, y), t, font=f_sub, fill=INK)
        y += lh
    return im


for ln in S["lines"]:
    frame(ln).save(WORK / f"{ln['id']}.png")

# クレジット
im = Image.new("RGB", (W, H), "#fcfcfb")
d = ImageDraw.Draw(im)
d.text((W // 2, 120), f"川辺の村 {Y}年  年報の動画", font=font(44), fill=INK, anchor="mm")
y = 210
d.text((W // 2, y), "話した人 (村の人) と声", font=font(26), fill=INK2, anchor="mm")
y += 50
for k, p in V["people"].items():
    fc, mk = face(p["img"], "smile", 56)
    im.paste(fc, (300, y - 28), mk)
    d.text((372, y), f"{p['name']} ({p['role']})", font=font(24), fill=INK, anchor="lm")
    d.text((760, y), p["credit"], font=font(24), fill=INK, anchor="lm")
    y += 66
y += 20
d.text((W // 2, y), V["portrait_credit"].split(" (")[0] + " (CC0)", font=font(20), fill=INK2, anchor="mm")
d.text((W // 2, y + 34), "pixiv Inc. の VRoid サンプル「HairSample_Female」「HairSample_Male」「Victoria Rubin」「千駄ヶ谷 篠」「桜田 フミリヤ」", font=font(17), fill=INK2, anchor="mm")
d.text((W // 2, y + 66), "数: 村の記録 (年報と統計のページ)", font=font(17), fill=INK2, anchor="mm")
im.save(WORK / "s99.png")
print(f"絵 {len(S['lines']) + 1} 枚 ({W}x{H}) を {WORK} に書いた")
