"""Society 2.0 の途中経過のグラフ (5 季節ごとの報告用。2026-10-08 本人と決めた「5 季節ごとに文とグラフ 1 枚」)

  python3 sim/society/tools/progress_chart.py [state.json] [出力.png] [最初の日 (既定 489 = Society 2.0 の始まり)]

4 つの小さなグラフ (目盛りは 1 つずつ。2 つの量を 1 つのグラフに重ねない):
  1. 人数 (大人・子)  2. 村の蓄え (今の人数で何日分。お題と同じ数え方)  3. 1 季節に食べたものの内訳 (割合)  4. 家族の住まいの数
日付は「10年31日目」で表す (2026-10-09 本人の希望。daily_run.md の冒頭。年は過ぎた年の数で、最初の年は 0年。この世界の 1 年は 120 日 = 季節 30 日 × 4)。
すべて state.json の記録 (人の生まれた日・加わった日・亡くなった日・村を出た日、毎日の stats、era2 の家族の住まい) から数える。
色は dataviz の手引きの決まった順 (validate_palette.js で確かめた: 青・橙・水色・黄)。水色と黄は背景との濃さの差が小さいので、凡例と文字を必ずつける。
"""
import json
import sys
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
import matplotlib.ticker  # noqa: E402,F401
from matplotlib import font_manager  # noqa: E402

SEASON, YEAR, ADULT = 30, 120, 15
BASE_KCAL = 1900  # world.py と同じ (大人は 1 日 BASE_KCAL + 500)
CHILD_EAT = [(3, 800), (10, 1300), (15, 1800)]  # era2.py と同じ (子が 1 日に食べる量)
SURFACE, INK, INK2, MUTED, GRID, AXIS = "#fcfcfb", "#0b0b0b", "#52514e", "#898781", "#e1e0d9", "#c3c2b7"
S1, S2, S3, S4 = "#2a78d6", "#eb6834", "#1baf7a", "#eda100"  # 決まった順 (並べかえない)


def year_label(d):
    """通しの日 → 「10年31日目」(app/replay3d.js の dayLabel と同じ。年は過ぎた年の数で、最初の年は 0年)"""
    return f"{d // YEAR}年{d % YEAR + 1}日目"


def _font():
    for name in ("IPAGothic", "IPAPGothic", "Noto Sans CJK JP", "WenQuanYi Zen Hei", "Yu Gothic", "Meiryo", "MS Gothic"):  # 後ろの 3 つは Windows
        if any(f.name == name for f in font_manager.fontManager.ttflist):
            return name
    return None


def _joined(state, name):
    return next((e["day"] for e in state["events"] if e["type"] == "加わる" and name in e["text"]), None)


def series(state, start):
    """季節の終わりの日ごとの、人数・蓄え・食べたもの・家族の住まい"""
    people = state["people"]
    death = {e["who"]: e["day"] for e in state["events"] if e["type"] == "死" and e.get("who")}
    stats = {s["day"]: s for s in state["stats"]}
    end = state["day"]
    days = [d for d in range(start, end + 1) if (d + 1) % SEASON == 0 or d == end]
    rows = []
    homes = (state.get("era2") or {}).get("homes", {})
    for d in days:
        ad = ch = 0
        need = 0  # その日の人数で 1 日に要る量 (era2.store_days と同じ数え方。お題の「今の人数で 約 N 日分」とそろえる)
        for p in people:
            born = p.get("born_day", -10 ** 6)
            came = born if p.get("origin") == "生まれた" else (_joined(state, p["name"]) or 0) if p.get("origin") == "よそから来た" else 0
            gone = min(x for x in (death.get(p["name"]), p.get("left"), 10 ** 9) if x is not None)
            if came <= d < gone or (came <= d and gone == d):
                age = (d - born) / YEAR
                if age >= ADULT:
                    ad += 1
                    need += BASE_KCAL + 500
                else:
                    ch += 1
                    need += next(k for a, k in CHILD_EAT if age < a)
        win = [stats[x] for x in range(d - SEASON + 1, d + 1) if x in stats]
        eaten = sum(s.get("eaten", 0) for s in win)
        by = {}
        for s in win:
            for k, v in (s.get("eaten_by_kind") or {}).items():
                by[k] = by.get(k, 0) + v
        store = stats[d]["store"] if d in stats else None
        rows.append({"day": d, "adults": ad, "children": ch, "store_days": (store / need) if store is not None and need else None,
                     "by": by, "eaten": eaten,
                     "houses": sum(1 for v in homes.values() if v.get("built") is not None and v["built"] <= d)})
    return rows


def _style(ax, title):
    ax.set_facecolor(SURFACE)
    ax.set_title(title, loc="left", fontsize=12, color=INK, pad=8)
    for s in ("top", "right"):
        ax.spines[s].set_visible(False)
    for s in ("left", "bottom"):
        ax.spines[s].set_color(AXIS)
        ax.spines[s].set_linewidth(0.8)
    ax.tick_params(colors=MUTED, labelsize=9, length=0)
    ax.grid(axis="y", color=GRID, linewidth=0.8)  # 実線の細い目盛り線
    ax.set_axisbelow(True)


def phases(state, start):
    return [(x["era"], x["day"]) for x in state.get("era_log", []) if x["day"] >= start and x["era"].startswith("G")]


def draw(state, out, start=489):
    font = _font()
    if font:
        plt.rcParams["font.family"] = font
    rows = series(state, start)
    xs = [r["day"] for r in rows]
    fig, axes = plt.subplots(2, 2, figsize=(12, 7.2), dpi=130, facecolor=SURFACE)
    fig.suptitle(f"川辺の村 (Society 2.0) の移り変わり: {year_label(start)} 〜 {year_label(state['day'])} (季節の終わりごと)", x=0.01, ha="left", fontsize=14, color=INK)
    fig.text(0.01, 0.945, "※ 年は過ぎた年の数 (最初の年は 0年)。この世界の 1 年は 120 日 (夏・秋・冬・春が 30 日ずつ。現実の 1 年とは違います)", ha="left", va="top", fontsize=9, color=MUTED)
    ph = phases(state, start)

    def marks(ax):  # フェーズが進んだ日 (細い縦線と、上の小さな文字)
        top = ax.get_ylim()[1]
        for era, d in ph:
            ax.axvline(d, color=AXIS, linewidth=0.8, zorder=0)
            ax.text(d, top, f" {era}", color=MUTED, fontsize=8, va="top", ha="left")

    # 1. 人数
    ax = axes[0][0]
    _style(ax, "人数")
    ax.plot(xs, [r["adults"] for r in rows], color=S1, linewidth=2, label="大人")
    ax.plot(xs, [r["children"] for r in rows], color=S2, linewidth=2, label="子")
    ax.set_ylim(0, max(r["adults"] + 2 for r in rows))
    ax.yaxis.set_major_locator(matplotlib.ticker.MaxNLocator(integer=True))
    for key, col, name in (("adults", S1, "大人"), ("children", S2, "子")):  # 終わりの値だけ文字で
        ax.annotate(f"{name} {rows[-1][key]}", (xs[-1], rows[-1][key]), xytext=(6, 0), textcoords="offset points", color=INK2, fontsize=9, va="center")
    ax.legend(frameon=False, fontsize=9, loc="upper left", labelcolor=INK2)
    marks(ax)
    # 2. 村の蓄え
    ax = axes[0][1]
    _style(ax, "村の蓄え (今の人数で何日分か)")
    pts = [(r["day"], r["store_days"]) for r in rows if r["store_days"] is not None]
    ax.plot([p[0] for p in pts], [p[1] for p in pts], color=S1, linewidth=2)
    ax.set_ylim(0, max(p[1] for p in pts) * 1.15 if pts else 1)
    if pts:
        ax.annotate(f"{pts[-1][1]:.0f} 日分", pts[-1], xytext=(6, 0), textcoords="offset points", color=INK2, fontsize=9, va="center")
    marks(ax)
    # 3. 食べたものの内訳 (割合の積み上げ。部分のあいだに背景色の 2px のすき間)
    ax = axes[1][0]
    _style(ax, "1 季節に食べたものの内訳 (割合)")
    kinds = [("木の実", S1), ("芋", S2), ("草の種", S3)]
    other = S4
    bottom = [0.0] * len(rows)
    w = SEASON * 0.8
    for k, col in kinds + [("ほか", other)]:
        vals = []
        for r in rows:
            t = r["eaten"] or 1
            v = r["by"].get(k, 0) if k != "ほか" else sum(x for kk, x in r["by"].items() if kk not in dict(kinds))
            vals.append(v / t)
        ax.bar(xs, vals, width=w, bottom=bottom, color=col, edgecolor=SURFACE, linewidth=1.5, label=k)
        bottom = [b + v for b, v in zip(bottom, vals)]
    ax.set_ylim(0, 1.0)
    ax.yaxis.set_major_formatter(matplotlib.ticker.PercentFormatter(1.0, decimals=0))
    ax.legend(frameon=False, fontsize=9, loc="lower left", ncol=4, labelcolor=INK2, bbox_to_anchor=(0, -0.28))
    last = rows[-1]
    t = last["eaten"] or 1
    ax.annotate("終わりの季節: " + "・".join(f"{k} {last['by'].get(k, 0) / t:.0%}" for k, _ in kinds), (1, 1.02), xycoords="axes fraction",
                ha="right", va="bottom", fontsize=8, color=INK2)
    # 4. 家族の住まい
    ax = axes[1][1]
    _style(ax, "家族の住まい (できた数)")
    ax.step(xs, [r["houses"] for r in rows], where="post", color=S1, linewidth=2)
    ax.set_ylim(0, max(4, max(r["houses"] for r in rows) + 1))
    ax.yaxis.set_major_locator(matplotlib.ticker.MaxNLocator(integer=True))
    ax.annotate(f"{rows[-1]['houses']} 軒", (xs[-1], rows[-1]["houses"]), xytext=(6, 0), textcoords="offset points", color=INK2, fontsize=9, va="center")
    marks(ax)
    first, last = start // YEAR + 1, state["day"] // YEAR  # 目盛りは、その年のはじめ (グラフの中に入る年だけ)
    step = max(1, (last - first + 1) // 8)  # 目盛りは 8 つほど
    ticks = [y * YEAR for y in range(first + (-first) % step, last + 1, step)]
    for row in axes:
        for ax in row:
            ax.set_xticks(ticks)
            ax.set_xticklabels([f"{x // YEAR}年" for x in ticks])
            ax.set_xlim(start - SEASON, state["day"] + SEASON)
            ax.set_xlabel("年 (過ぎた年の数。目盛りは年のはじめ)", color=MUTED, fontsize=9, loc="right")
    fig.tight_layout(rect=(0, 0, 1, 0.92))
    fig.savefig(out, facecolor=SURFACE)
    return rows


if __name__ == "__main__":
    root = Path(__file__).resolve().parents[1]
    st = json.loads(Path(sys.argv[1] if len(sys.argv) > 1 else root / "data" / "state.json").read_text(encoding="utf-8"))
    out = sys.argv[2] if len(sys.argv) > 2 else "progress.png"
    start = int(sys.argv[3]) if len(sys.argv) > 3 else 489
    rows = draw(st, out, start)
    last = rows[-1]
    print(out, "/", year_label(last["day"]), f"({last['day']} 日目): 大人", last["adults"], "子", last["children"],
          "蓄え", round(last["store_days"] or 0), "日分 / 家族の住まい", last["houses"])
