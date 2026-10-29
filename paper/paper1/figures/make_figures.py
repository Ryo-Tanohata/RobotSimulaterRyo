"""Regenerate the four English-labelled figures of paper 1 from the season records.

Usage (from the repository root):
    python3 paper/paper1/figures/make_figures.py
Input : sim/society/data/records/season_village.jsonl (one row per 30-day season, days 489-13079)
Output: paper/paper1/figures/fig_{population,store,diet,inequality}.pdf/.png
Read-only: does not touch the simulation state. One y-axis per chart.
"""
import json, os
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", ".."))
SRC = os.path.join(ROOT, "sim/society/data/records/season_village.jsonl")
OUT = os.path.dirname(os.path.abspath(__file__))
rows = [json.loads(l) for l in open(SRC, encoding="utf-8")]
yr = lambda d: d / 120.0
x = [yr(r["season_end_day"]) for r in rows]

BLUE, GREEN, ORANGE, RED, GREY = "#2a5fa8", "#2e8b57", "#d4881c", "#c0392b", "#888888"
PHASES = [("G1", 489), ("G2", 1229), ("G3-5", 1529), ("G6", 3539),
          ("G7", 5849), ("G8", 8519), ("G9", 12599)]
plt.rcParams.update({"font.size": 9, "axes.spines.top": False, "axes.spines.right": False})


def base(ylabel, ylim=None):
    fig, ax = plt.subplots(figsize=(7.0, 3.3))
    ax.set_xlabel("Simulated year (1 year = 120 days)")
    ax.set_ylabel(ylabel)
    ax.grid(axis="y", color="#eeeeee", lw=0.6)
    ax.set_xlim(0, 110)
    if ylim:
        ax.set_ylim(*ylim)
    return fig, ax


def phase_ticks(ax):
    for name, d in PHASES:
        if ax.get_xlim()[0] <= yr(d):
            ax.text(yr(d) + 0.4, 1.0, name, fontsize=6.5, color=GREY, ha="left", va="bottom",
                    transform=ax.get_xaxis_transform())


def mark(ax, day, label, kind, level):
    """kind 'village' = first used by villagers (solid red); 'maker' = opened by a phase gate or code change (dashed grey)."""
    style = dict(color=RED, lw=0.8) if kind == "village" else dict(color=GREY, lw=0.8, ls="--")
    ax.axvline(yr(day), **style)
    lo, hi = ax.get_ylim()
    ax.text(yr(day) + 0.6, lo + (hi - lo) * level, label, fontsize=6.5, color="#333333")


def unit_ticks(ax):
    ax.set_yticks([0, 0.2, 0.4, 0.6, 0.8, 1.0])


def save(fig, name):
    fig.tight_layout()
    fig.savefig(os.path.join(OUT, name + ".pdf"))
    fig.savefig(os.path.join(OUT, name + ".png"), dpi=200)
    plt.close(fig)


# 1. population
fig, ax = base("Population (persons)", (0, 250))
ax.set_yticks(range(0, 175, 25))
ax.axvspan(53, 62, color=RED, alpha=0.08, lw=0)
ax.text(53.5, 6, "famine (G7)", fontsize=7, color=RED)
ax.axvspan(yr(10919), yr(12599), color=GREY, alpha=0.12, lw=0)
ax.text(yr(10919) + 0.5, 6, "heavy tribute (G8)", fontsize=7, color="#555555")
for d, lab, k, lv in [(510, "fields", "village", .93), (781, "fire", "village", .86),
                      (1560, "sickle, pottery, family houses (G3 gate)", "maker", .79),
                      (1709, "household stores (G4 gate)", "maker", .72),
                      (3539, "household seals (G6 gate)", "maker", .93),
                      (5009, "tokens first used", "village", .86), (5280, "clay tablet first used", "village", .79),
                      (8159, "bronze blade acquired", "village", .72), (12629, "bronze used", "village", .93)]:
    mark(ax, d, lab, k, lv)
ax.plot(x, [r["population"] for r in rows], color=BLUE, lw=1.5)
phase_ticks(ax)
save(fig, "fig_population")

# 2. food store in days
fig, ax = base("Food store (days of current consumption)", (0, 1900))
ax.set_yticks(range(0, 1500, 250))
for d, lab, k, lv in [(510, "fields", "village", .93), (1560, "sickle, pottery (G3)", "maker", .86),
                      (1709, "household stores (G4)", "maker", .79), (4409, "goat cap (world change)", "maker", .72),
                      (5280, "clay tablet", "village", .93), (5849, "yearly plan (G7)", "maker", .86),
                      (7439, "autumn meeting, model switch", "maker", .79), (8520, "tribute begins (G8)", "village", .72),
                      (10919, "heavy tribute", "maker", .93), (12629, "bronze used", "village", .86)]:
    mark(ax, d, lab, k, lv)
ax.plot(x, [r.get("store_days_all") for r in rows], color=BLUE, lw=1.2)
phase_ticks(ax)
save(fig, "fig_store")

# 3. diet share by year (kcal-weighted over the four seasons)
by = {}
for r in rows:
    y = r["year"]
    k = r.get("eaten_kcal") or 0
    s = r.get("eaten_share") or {}
    a = by.setdefault(y, [0.0, 0.0, 0.0])
    a[0] += k
    a[1] += k * s.get("木の実", 0)
    a[2] += k * s.get("草の種", 0)
ys = sorted(y for y in by if by[y][0] > 0)
fig, ax = base("Share of food energy eaten", (0, 1.55))
for d, lab, k, lv in [(510, "fields", "village", .95), (1560, "sickle, pottery (G3)", "maker", .88),
                      (1709, "household stores (G4)", "maker", .81), (5849, "yearly plan (G7)", "maker", .74),
                      (7439, "autumn meeting, model switch", "maker", .95), (12629, "bronze used", "village", .88)]:
    mark(ax, d, lab, k, lv)
ax.plot([y + 0.5 for y in ys], [by[y][1] / by[y][0] for y in ys], color=GREEN, lw=1.4, label="nuts (mostly from planted trees)")
ax.plot([y + 0.5 for y in ys], [by[y][2] / by[y][0] for y in ys], color=BLUE, lw=1.4, label="grass seed (field cereal)")
ax.legend(loc="upper right", bbox_to_anchor=(1.0, 0.68), frameon=False, fontsize=7.5)
phase_ticks(ax)
unit_ticks(ax)
save(fig, "fig_diet")

# 4. inequality
fig, ax = base("Gini coefficient", (0, 1.5))
for d, lab, k, lv in [(1560, "family houses (G3)", "maker", .95), (1709, "household stores (G4)", "maker", .88),
                      (3539, "household seals (G6)", "maker", .81), (5280, "clay tablet", "village", .74),
                      (6360, "famine", "village", .95), (10919, "heavy tribute", "maker", .88)]:
    mark(ax, d, lab, k, lv)
wx = [(xx, r["wealth_gini"]) for xx, r in zip(x, rows) if r.get("wealth_gini") is not None]
hx = [(xx, r["house_gini"]) for xx, r in zip(x, rows) if r.get("house_gini") is not None]
ax.plot(*zip(*wx), color=BLUE, lw=1.4, label="household wealth (store + goats)")
ax.plot(*zip(*hx), color=ORANGE, lw=1.0, label="house size")
ax.set_xlim(10, 110)
ax.legend(loc="upper center", bbox_to_anchor=(0.5, -0.2), frameon=False, fontsize=7.5, ncol=2)
phase_ticks(ax)
unit_ticks(ax)
save(fig, "fig_inequality")
print("ok")
