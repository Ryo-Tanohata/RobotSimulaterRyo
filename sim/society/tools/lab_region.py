"""実験 A1: 地域だけの要因の掃き出し (docs/research/state_emergence_plan.md 3.1。トークンは使わない。数はみな【シ】)

  SOC_DATA=/tmp/…/data PYTHONUTF8=1 python3.13 sim/society/tools/lab_region.py run --seeds 100 --procs 2 --csv /tmp/…/runs.csv
  PYTHONUTF8=1 python3.13 sim/society/tools/lab_region.py summary --csv /tmp/…/runs.csv [--out FILE]
  PYTHONUTF8=1 python3.13 sim/society/tools/lab_region.py check --data /tmp/…/data   (region_sweep.py と同じ数になるかの確かめ)
  PYTHONUTF8=1 python3.13 sim/society/tools/lab_region.py anatomy --data /tmp/…/data --csv /tmp/…/runs.csv   (c1 に届いた回の中身を見る)

- 土台は tools/region_sweep.py (G7_sweep.md の掃き出し)。region.py の 1 年の決まりをそのまま使い、川辺の村は「決まりで動く集落」(V0)。
  世界 (era2・world) は動かさない。state.json は読むだけ (写しを指すこと)
- 要因は、このプロセスの中だけで region の数・関数を差しかえて作る (region.py・g7.py・era2.py は 1 字も変えない)。1 回ごとに、はじめに全部もとに戻してから当てる
- 7 つの要因 (計画 3.1 の表):
    fill   まわりの埋まり: 10 (K の 10%。G7) / 30
    str    まわりの強さ: base (今のまま) / big (大きい隣 1 つ。村の 2 倍の人。村から 2 ますの川ぞい (5,3)。村と同じく K で減らず、分かれない) / x2 (はじめのまわりの人数を 2 倍)
    circ   囲み: open (今のまま) / desert (草原を砂地に。K=0 で住めない。置く人数は今の地図の K の割合のまま) / nofl (砂地 + 逃げる手なし)
    vdem   村の求め: never (求めない) / r15 (まわりと同じ決まり: 1 年 0.3 の見込みで動き、1.5 倍強いときだけ) / always (毎年、1.2 倍。region_sweep の「いつも求める」)
    split  分かれた家と親村: none (つながりなし。G7) / trib (村を出た家の集落が親村に貢ぐ。G7.md 5. の案 d)
    irr    水路の代わり: none / irr (川ぞいの余りは、段 1 以上の集落だけ満額。段 0 なら雨で育つ畑と同じ 70)
    dr     日照り: 0.20 (今) / 0.35 (地域が悪い年になる見込み)
- 村の家が出ていく見込みは、どの組も 1 年 0.25 (5 人)。G7 で村を出た家は 22 年で 27 人 (1 年 約 1.2 人) なので、それに合わせた【仮定】
- 乱数の列は region_sweep.py と同じ文字の種 ("sweep|…|種|年") を使う (組どうしで同じ種は同じ列 = くらべやすい)。足した乱数は "lab|…"
"""
import argparse
import csv
import gzip
import itertools
import json
import math
import os
import random
import statistics
import sys
import time
from multiprocessing import Pool
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent))
sys.path.insert(0, str(HERE))
import region  # noqa: E402
import region_sweep as rs  # noqa: E402

FACTORS = {
    "fill": ("10", "30"),
    "str": ("base", "big", "x2"),
    "circ": ("open", "desert", "nofl"),
    "vdem": ("never", "r15", "always"),
    "split": ("none", "trib"),
    "irr": ("none", "irr"),
    "dr": ("0.20", "0.35"),
}
FLABEL = {"fill": "まわりの埋まり", "str": "まわりの強さ", "circ": "囲み", "vdem": "村の求め", "split": "分かれた家と親村", "irr": "水路の代わり", "dr": "日照り"}
LABEL = {
    "10": "K の 10% (G7)", "30": "K の 30%", "base": "今のまま", "big": "大きい隣 1 つ (村の 2 倍)", "x2": "まわりの人数 2 倍",
    "open": "今のまま (草原に空き)", "desert": "草原を砂地 (住めない)", "nofl": "砂地 + 逃げる手なし",
    "never": "求めない", "r15": "1.5 倍強いときだけ (まわりと同じ)", "always": "いつも (1.2 倍)",
    "none": "なし", "trib": "親村に貢ぐ (案 d)", "irr": "段 1 以上で川ぞい満額", "0.20": "悪い年 0.2 (今)", "0.35": "悪い年 0.35",
}
LEAVE_P = 0.25  # 村の家が出ていく見込み (1 年)。G7 の 22 年で 27 人に合わせた【仮定】
BIG_CELL = (5, 3)  # 大きい隣のます (村から 2 ます北の川ぞい。G6 からの南の村 (5,7) の向かい)
BIG_ID = "B1"
COLS = ["fill", "str", "circ", "vdem", "split", "irr", "dr", "seed", "reach", "reach_yr", "any3", "any3_yr", "maxD", "vmaxD", "wars", "flee", "breaks",
        "gone", "dec", "boxed", "dem", "v_dem_out", "v_dem_in", "v_trib_end", "kids_trib_paid", "setts_end", "people_end", "v0_end", "secs"]

# ---------------- 差しかえ (このプロセスの中だけ) ----------------
ORIG = {"K": dict(region.K), "WEATHER_BAD": region.WEATHER_BAD, "DEMAND_RATIO": dict(region.DEMAND_RATIO), "cells": region.cells,
        "refuge": region.refuge, "surplus_pp": region.surplus_pp}
K_TOTAL0 = region.k_total()  # 今の地図の K の合計 (村のますを除く) = 5,000


def _cells_desert():
    return [c for c in ORIG["cells"]() if region.land(c) != "s"]


def _no_refuge(setts, s, a):
    return None


def _surplus_irr(s, bad=None):
    v = ORIG["surplus_pp"](s, bad)
    if s["land"] == "r" and s.get("org", 0) < 1:
        v *= region.SURPLUS["a"] / region.SURPLUS["r"]
    return v


def apply_world(lv):
    """要因の水準を region に当てる (はじめに、みなもとに戻す)"""
    region.K = dict(ORIG["K"])
    region.WEATHER_BAD = float(lv["dr"])
    region.DEMAND_RATIO = dict(ORIG["DEMAND_RATIO"])
    region.cells = ORIG["cells"]
    region.refuge = ORIG["refuge"]
    region.surplus_pp = ORIG["surplus_pp"]
    if lv["circ"] in ("desert", "nofl"):
        region.K["s"] = 0
        region.cells = _cells_desert
    if lv["circ"] == "nofl":
        region.refuge = _no_refuge
    if lv["vdem"] == "r15":
        region.DEMAND_RATIO["求める"] = region.DEMAND_RATIO["ふつう"]  # 村の求めの構えを、まわりと同じ 1.5 倍にする (まわりの集落は掃き出しでは構え「ふつう」のまま)
    if lv["irr"] == "irr":
        region.surplus_pp = _surplus_irr


def fill_cells(used, people_now, target, rng):
    """region.fill_cells と同じ決まり (同じ乱数の引き方)。ちがいは、目標の人数を外から渡すこと (砂地の世界でも、今の地図の K の割合で置く)"""
    used = set(used)
    out, total = [], people_now
    while total < target:
        free = [c for c in region.cells() if c not in used and region.dist(c, region.VILLAGE) > region.FILL_NEAR]
        if not free:
            break
        w = sum(region.cap(c) for c in free)
        u = rng.random() * w
        pick = free[-1]
        for c in free:
            u -= region.cap(c)
            if u < 0:
                pick = c
                break
        n = max(1, round(region.cap(pick) * rng.uniform(*region.FILL_SHARE)))
        used.add(pick)
        out.append((pick, n))
        total += n
    return out


def start(base, lv, seed):
    """はじめの地域: rs.start と同じ並べ方に、大きい隣・人数 2 倍・砂地を足す"""
    v0 = {"id": "V0", "name": "川辺の村", "village": True, "people": base["pop"], "cell": list(region.VILLAGE), "land": "r", "org": 1 if base["leader"] else 0,
          "grain": base["grain"], "goats": base["goats"], "tech": 1, "commit": {}, "stance": "ふつう", "walls": None, "known": 0, "kcap": 10 ** 6}
    mul = 2 if lv["str"] == "x2" else 1
    setts, used = [v0], {region.VILLAGE}
    nxt = 1
    for o in sorted(base["others"], key=lambda o: region.num(o["id"])):
        c = region.place_known(o["dir"], o["days"], used)
        used.add(c)
        setts.append(rs.new(o["id"], c, o["people"] * mul, o["name"], grain=o["grain"] * mul, goats=o["goats"] * mul, known=o["known"]))
        nxt = max(nxt, region.num(o["id"]) + 1)
    if lv["str"] == "big":
        n = 2 * base["pop"]
        b = rs.new(BIG_ID, BIG_CELL, n, "大きい隣", known=0)
        b["kcap"] = 10 ** 6  # 村と同じく、地図の K で減らさない
        used.add(BIG_CELL)
        setts.append(b)
    have = sum(s["people"] for s in setts[1:] if s["id"] != BIG_ID)
    for c, n in fill_cells(used, have, round(K_TOTAL0 * int(lv["fill"]) / 100), random.Random(f"sweep|fill|{seed}")):
        setts.append(rs.new(f"N{nxt}", c, n * mul))
        nxt += 1
    return setts, nxt


def run(job):
    """1 つの組・1 つの種で years 年回す (rs.run と同じ順。足したのは 村の求めの水準・村の家が出ていく・案 d・大きい隣は分かれない)"""
    base, lv, seed, years, leave = job
    t0 = time.process_time()
    apply_world(lv)
    setts, nxt = start(base, lv, seed)
    R = {"ties": [], "demands": [], "wars": [], "pending": [], "gone": [], "log": [], "next_war": 1}
    day0 = (base["day"] + 1) // region.YEAR_DAYS * region.YEAR_DAYS - 1
    m = {"reach": 0, "reach_yr": None, "any3": 0, "any3_yr": None, "maxD": 0, "vmaxD": 0, "wars": 0, "flee": 0, "breaks": 0, "gone": 0,
         "dec": 0, "boxed": 0, "kids_trib_paid": 0}
    counter = {"n": nxt}

    def make(parent, c, n, kind):
        o = rs.new(f"N{counter['n']}", c, n, f"{parent.get('name', parent['id'])}の子")
        o["grain"], o["goats"], o["cattle_f"] = 0, 0, 0.0
        counter["n"] += 1
        setts.append(o)
        return o
    sick_prev = set()
    for k in range(years):
        day = day0 + k * region.YEAR_DAYS
        y = (day + 1) // region.YEAR_DAYS
        live = region._live(setts)
        z, rbad, bad = region.weather(random.Random(f"sweep|weather|{seed}|{y}"), [(s["id"], region.cell_of(s)) for s in live])
        for s in live:
            s["bad"] = day if s["id"] in bad else None
        if lv["vdem"] == "always":
            vd = "いつも"
        elif lv["vdem"] == "r15":  # まわりと同じ: 1 年 0.3 の見込みで動く集落に入る
            vd = "いつも" if random.Random(f"lab|vdem|{seed}|{y}").random() < region.ACT_SHARE else None
        else:
            vd = None
        out = []
        region.year_end(R, setts, random.Random(f"sweep|year|{seed}|{y}"), y, day, grow_village=True, village_demand=vd, out=out)
        if lv["str"] == "big":  # 大きい隣は村と同じく、決まりで分かれず出ていかない (人の多い「町」のまま残す)
            R["pending"] = [p for p in R["pending"] if not (p["who"] == BIG_ID and p["kind"] in ("分かれる", "出ていく"))]
        sr = random.Random(f"sweep|sick|{seed}|{y}")
        now_sick = set()
        for s in region._live(setts):
            if s.get("village"):
                continue
            links = sum(1 for t in region.ties_on(R) if s["id"] in (t["payer"], t["payee"]))
            hit, _ = region.sick(sr, s, links, any(t["payer"] in sick_prev or t["payee"] in sick_prev for t in region.ties_on(R) if s["id"] in (t["payer"], t["payee"])))
            if hit:
                s["people"] -= round(s["people"] * sr.uniform(*region.SICK_DEATH))
                now_sick.add(s["id"])
        sick_prev = now_sick
        for p in R["pending"]:
            if p["kind"] == "求めへの答え":
                m["dec"] += 1
                m["boxed"] += not p["refuge"]
        d1 = day + 1
        v0 = next(s for s in setts if s["id"] == "V0")
        lr = random.Random(f"sweep|leave|{seed}|{y}")
        kid = None
        if leave and lr.random() < leave and v0["people"] > 2 * rs.LEAVE_N:
            c = region.near_cell(setts, region.VILLAGE)
            if c:
                kid = make(v0, c, rs.LEAVE_N, "分かれた家")
                kid["parent"], kid["known"] = "V0", d1
                region.commit_add(kid, "V0", region.COMMIT_NEW)
                region.commit_add(v0, kid["id"], region.COMMIT_NEW)
                v0["people"] -= rs.LEAVE_N
        region.decide(R, setts, d1, village={}, make=make, out=out)
        region.pay_ties(R, setts, d1, out=out)
        if kid is not None and lv["split"] == "trib" and not kid.get("gone"):
            # 案 d: 村を出た家の集落は、親村に貢ぐ (量は求めと同じ、相手の余りの 2 割。払うのは次の夏から。払い続けるかは決まりのまま)
            R["next_tie"] = R.get("next_tie", 1)
            R["ties"].append({"id": f"K{R['next_tie']}", "payer": kid["id"], "payee": "V0", "goods": {"草の種": region.amount_of(kid)}, "since": d1,
                              "due": "夏の集まりの日", "paid": [], "missed": 0, "status": "続く", "end": None, "fixed": None, "demand": None, "kin": True})
            R["next_tie"] += 1
        for w in sorted((w for w in R["wars"] if not w.get("done")), key=lambda w: (w["day"], int(w["id"][1:]))):
            by = region._by(setts)
            if by.get(w["att"], {}).get("gone") or by.get(w["def"], {}).get("gone") or w["att"] not in by or w["def"] not in by:
                w["done"] = w["day"]
                continue
            region.fight(R, setts, w, region.war_rng(f"sweep{seed}", int(w["id"][1:])), w["day"], out=out)
            m["wars"] += 1
        for e in out:
            if e["kind"] == "逃げる":
                m["flee"] += 1
            elif e["kind"] == "崩れ":
                m["breaks"] += 1
            elif e["kind"] == "集落" and e["data"].get("gone"):
                m["gone"] += 1
        paid = [t for t in region.ties_on(R) if t["paid"] and t["paid"][-1] > d1 - region.YEAR_DAYS]
        m["kids_trib_paid"] = max(m["kids_trib_paid"], sum(1 for t in paid if t.get("kin")))
        lv_ = region.levels(setts, paid, d1, village_rules=True)
        vg = next((g for g in lv_ if "V0" in g["members"]), None)
        dv = vg["D"] if vg else 0
        m["vmaxD"] = max(m["vmaxD"], dv)
        m["maxD"] = max(m["maxD"], max((g["D"] for g in lv_), default=0))
        if not m["any3"] and any(g["D"] >= 3 for g in lv_):
            m["any3"], m["any3_yr"] = 1, k + 1
        if not m["reach"] and dv >= 3:
            m["reach"], m["reach_yr"] = 1, k + 1
    live = region._live(setts)
    m["dem"] = len(R["demands"])
    m["v_dem_out"] = sum(1 for q in R["demands"] if q["from"] == "V0")
    m["v_dem_in"] = sum(1 for q in R["demands"] if q["to"] == "V0")
    m["v_trib_end"] = len(region.payers(R, "V0"))
    m["setts_end"] = sum(1 for s in live if not s.get("village"))
    m["people_end"] = sum(s["people"] for s in live if not s.get("village"))
    m["v0_end"] = next(s for s in setts if s["id"] == "V0")["people"]
    m["secs"] = round(time.process_time() - t0, 3)
    row = dict(lv, seed=seed, **m)
    return {c: row[c] for c in COLS}


def design():
    keys = list(FACTORS)
    return [dict(zip(keys, v)) for v in itertools.product(*(FACTORS[k] for k in keys))]


def key_of(r):
    return tuple(str(r[k]) for k in list(FACTORS) + ["seed"])


def cmd_run(a):
    base = rs.load(a.data)
    done = set()
    path = Path(a.csv)
    if path.exists():
        with path.open(encoding="utf-8") as f:
            done = {key_of(r) for r in csv.DictReader(f)}
    jobs = [(base, lv, s, a.years, LEAVE_P) for s in range(a.seed0, a.seed0 + a.seeds) for lv in design()]
    jobs = [j for j in jobs if key_of(dict(j[1], seed=j[2])) not in done]
    print(f"のこり {len(jobs)} 回 (済み {len(done)})", file=sys.stderr)
    new = not path.exists()
    t0 = time.time()
    with path.open("a", encoding="utf-8", newline="") as f, Pool(a.procs) as pool:
        w = csv.DictWriter(f, fieldnames=COLS)
        if new:
            w.writeheader()
        for i, row in enumerate(pool.imap_unordered(run, jobs, chunksize=4), 1):
            w.writerow(row)
            if i % 432 == 0:
                f.flush()
                el = time.time() - t0
                print(f"  {i}/{len(jobs)}  {el / 60:.1f} 分  のこり見込み {el / i * (len(jobs) - i) / 60:.0f} 分", file=sys.stderr, flush=True)


def cmd_check(a):
    """足した要因を「今のまま」にし、村の家の出ていく見込みを rs と同じにすると、region_sweep.run と同じ数になるか"""
    base = rs.load(a.data)
    lv = {"fill": "10", "str": "base", "circ": "open", "vdem": "never", "split": "none", "irr": "none", "dr": "0.20"}
    bad = 0
    for vdem, pol in (("never", rs.POLICIES[0]), ("always", rs.POLICIES[4]), ("never", rs.POLICIES[3])):
        for fill in ("10", "30"):
            for seed in range(4):
                mine = run((base, dict(lv, vdem=vdem, fill=fill), seed, 60, pol[3]))
                ref = rs.run((base, int(fill) / 100, False, pol, seed, 60))
                same = all(mine[k] == ref[k] for k in ("wars", "flee", "breaks", "gone", "maxD")) and \
                    mine["reach_yr"] == ref["reach"] and mine["any3_yr"] == ref["any3"] and mine["people_end"] == ref["people_end"]
                bad += not same
                print(vdem, pol[0], fill, seed, "同じ" if same else f"ちがう {mine} {ref}")
    apply_world(lv)
    print("ちがい", bad)


# ---------------- まとめ ----------------

def wilson(k, n, z=1.96):
    if n == 0:
        return (float("nan"),) * 3
    p = k / n
    d = 1 + z * z / n
    c = (p + z * z / (2 * n)) / d
    h = z * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n)) / d
    return p, max(0.0, c - h), min(1.0, c + h)


def pct(k, n):
    p, lo, hi = wilson(k, n)
    return f"{p:.1%} ({lo:.1%}–{hi:.1%})"


def read_rows(path):
    op = gzip.open if str(path).endswith(".gz") else open
    with op(path, "rt", encoding="utf-8") as f:
        rows = list(csv.DictReader(f))
    for r in rows:
        for c in ("reach", "any3", "maxD", "vmaxD", "wars", "flee", "breaks", "gone", "dec", "boxed", "dem", "v_dem_out", "v_dem_in", "v_trib_end",
                  "kids_trib_paid", "setts_end", "people_end", "v0_end", "seed"):
            r[c] = int(r[c])
        r["secs"] = float(r["secs"])
    return rows


def _mean(rs_, c):
    return statistics.mean(r[c] for r in rs_) if rs_ else float("nan")


def group_line(name, rows_):
    n = len(rows_)
    k1, k3 = sum(r["reach"] for r in rows_), sum(r["any3"] for r in rows_)
    yrs = [int(r["reach_yr"]) for r in rows_ if r["reach"]]
    dec = sum(r["dec"] for r in rows_)
    return (f"| {name} | {n} | {pct(k1, n)} | {statistics.median(yrs) if yrs else '-'} | {pct(k3, n)} | {_mean(rows_, 'maxD'):.2f} | {_mean(rows_, 'vmaxD'):.2f} | "
            f"{_mean(rows_, 'wars'):.2f} | {_mean(rows_, 'flee'):.1f} | {_mean(rows_, 'breaks'):.1f} | {_mean(rows_, 'gone'):.1f} | "
            f"{(sum(r['boxed'] for r in rows_) / dec if dec else 0):.0%} | {_mean(rows_, 'v_dem_in'):.2f} | {_mean(rows_, 'v_trib_end'):.2f} | "
            f"{_mean(rows_, 'people_end'):.0f} | {_mean(rows_, 'v0_end'):.0f} |")


HEAD = ("| 水準 | 回 | c1 (村が段 3) (95% の幅) | c1 の年 (真ん中) | 地域のどこかに段 3 (95% の幅) | 段の最大 | 村の段の最大 | 戦 | 逃げた | 崩れ | なくなった | "
        "囲まれていた答え | 村への求め | 60 年後に村へ貢ぐ集落 | 60 年後のまわりの人 | 60 年後の村の人 |\n|" + "---|" * 16)


def summary(rows):
    out = []
    n = len(rows)
    seeds = sorted({r["seed"] for r in rows})
    out.append(f"回 {n} (組 {len({key_of(r)[:-1] for r in rows})} × 種 {len(seeds)}: {seeds[0]}〜{seeds[-1]})。CPU 合計 {sum(r['secs'] for r in rows) / 3600:.2f} 時間")
    out.append("\n### 全体\n\n" + HEAD + "\n" + group_line("全部", rows))
    out.append("\n### 要因ごと (ほかの要因はみな平均。主効果)\n")
    for f, lvls in FACTORS.items():
        out.append(f"\n#### {FLABEL[f]}\n\n" + HEAD)
        for l in lvls:
            out.append(group_line(LABEL[l], [r for r in rows if r[f] == l]))
    out.append("\n### 村の求め × ほかの要因 (c1 の割合 (95% の幅))\n")
    for f in [x for x in FACTORS if x != "vdem"]:
        out.append(f"\n#### 村の求め × {FLABEL[f]}\n\n| {FLABEL[f]} | " + " | ".join(LABEL[v] for v in FACTORS["vdem"]) + " |\n|" + "---|" * 4)
        for l in FACTORS[f]:
            cells_ = []
            for v in FACTORS["vdem"]:
                g = [r for r in rows if r[f] == l and r["vdem"] == v]
                cells_.append(pct(sum(r["reach"] for r in g), len(g)))
            out.append(f"| {LABEL[l]} | " + " | ".join(cells_) + " |")
    out.append("\n### 村が求めない回だけ: 分かれた家と親村 × ほかの要因 (c1 の割合 (95% の幅))\n")
    nv = [r for r in rows if r["vdem"] == "never"]
    for f in [x for x in FACTORS if x not in ("vdem", "split")]:
        out.append(f"\n#### {FLABEL[f]}\n\n| {FLABEL[f]} | " + " | ".join(LABEL[v] for v in FACTORS["split"]) + " |\n|" + "---|" * 3)
        for l in FACTORS[f]:
            cl = []
            for v in FACTORS["split"]:
                g = [r for r in nv if r[f] == l and r["split"] == v]
                cl.append(pct(sum(r["reach"] for r in g), len(g)))
            out.append(f"| {LABEL[l]} | " + " | ".join(cl) + " |")
    out.append("\n### 2 つの要因の組 (地域のどこかに段 3 の割合)\n")
    fs = list(FACTORS)
    for i, f in enumerate(fs):
        for g_ in fs[i + 1:]:
            out.append(f"\n#### {FLABEL[f]} × {FLABEL[g_]}\n\n| {FLABEL[f]} | " + " | ".join(LABEL[v] for v in FACTORS[g_]) + " |\n|" + "---|" * (len(FACTORS[g_]) + 1))
            for l in FACTORS[f]:
                cl = []
                for v in FACTORS[g_]:
                    g = [r for r in rows if r[f] == l and r[g_] == v]
                    cl.append(pct(sum(r["any3"] for r in g), len(g)))
                out.append(f"| {LABEL[l]} | " + " | ".join(cl) + " |")
    # 組ごと: c1 のいちばん高い組・村が求めないときの c1 > 0 の組
    cells_ = {}
    for r in rows:
        cells_.setdefault(key_of(r)[:-1], []).append(r)
    rank = sorted(cells_.items(), key=lambda kv: -sum(r["reach"] for r in kv[1]) / len(kv[1]))
    out.append("\n### 組ごと: 村が求めないのに c1 に届いた割合の高い 20 組\n\n| " + " | ".join(FLABEL[f] for f in FACTORS) + " | 回 | c1 | 地域に段 3 |\n|" + "---|" * 10)
    for kk, g in [kv for kv in rank if kv[0][3] == "never"][:20]:
        out.append("| " + " | ".join(LABEL[v] for v in kk) + f" | {len(g)} | {pct(sum(r['reach'] for r in g), len(g))} | {pct(sum(r['any3'] for r in g), len(g))} |")
    out.append("\n### 組ごと: 村が「1.5 倍強いときだけ」求めるのに c1 の低い 10 組\n\n| " + " | ".join(FLABEL[f] for f in FACTORS) + " | 回 | c1 | c1 の年 (真ん中) | 地域に段 3 |\n|" + "---|" * 11)
    for kk, g in [kv for kv in rank if kv[0][3] == "r15"][-10:][::-1]:
        yrs = [int(r["reach_yr"]) for r in g if r["reach"]]
        out.append("| " + " | ".join(LABEL[v] for v in kk) + f" | {len(g)} | {pct(sum(r['reach'] for r in g), len(g))} | "
                   f"{statistics.median(yrs) if yrs else '-'} | {pct(sum(r['any3'] for r in g), len(g))} |")
    g7 = cells_.get(("10", "base", "open", "never", "none", "none", "0.20"), [])
    out.append("\n### G7 にいちばん近い組 (10%・今のまま・求めない・つながりなし・水路なし・0.2)\n\n" + HEAD + "\n" + group_line("G7 に近い組", g7))
    return "\n".join(out) + "\n"


def cmd_summary(a):
    txt = summary(read_rows(a.csv))
    if a.out:
        Path(a.out).write_text(txt, encoding="utf-8")
    print(txt)


def cmd_anatomy(a):
    """c1 に届いた回の中身: 届いた年の、村のいるまとまりを、回を選んで写しなおして見る (同じ種なら同じ回になる)。
    村の求め × 分かれた家 ごとに、届いた回から a.n 回を選ぶ (乱数の種 1)"""
    base = rs.load(a.data)
    rows = [r for r in read_rows(a.csv) if r["reach"]]
    rnd = random.Random(1)
    orig = region.levels
    out = ["| 村の求め | 分かれた家と親村 | c1 に届いた回 | 見た回 | 村がいちばん上 | 村が貢ぐ側 | まとまりが村を出た家の集落だけ | 村のほかの集落の数 (真ん中) | 村のほかの人 (真ん中) |",
           "|" + "---|" * 9]
    for v in FACTORS["vdem"]:
        for sp in FACTORS["split"]:
            g = [r for r in rows if r["vdem"] == v and r["split"] == sp]
            smp = g if len(g) <= a.n else rnd.sample(g, a.n)
            top = kin = pays = 0
            ppl, mem = [], []
            for r in smp:
                hit = {}

                def lev(setts, ties, day, officials=None, village_rules=False):
                    res = orig(setts, ties, day, officials, village_rules)
                    gg = next((x for x in res if "V0" in x["members"]), None)
                    if gg and gg["D"] >= 3 and not hit:
                        by = {s["id"]: s for s in setts}
                        oth = [m for m in gg["members"] if m != "V0"]
                        hit.update(top=gg["top"] == "V0", kin=all(by[m].get("parent") == "V0" for m in oth), n=len(oth),
                                   p=sum(by[m]["people"] for m in oth), pays=any(t["payer"] == "V0" for t in ties if t["payee"] in gg["members"]))
                    return res
                region.levels = lev
                try:
                    run((base, {k: r[k] for k in FACTORS}, r["seed"], 60, LEAVE_P))
                finally:
                    region.levels = orig
                top += hit["top"]
                kin += hit["kin"]
                pays += hit["pays"]
                ppl.append(hit["p"])
                mem.append(hit["n"])
            if smp:
                out.append(f"| {LABEL[v]} | {LABEL[sp]} | {len(g)} | {len(smp)} | {top / len(smp):.0%} | {pays / len(smp):.0%} | {kin / len(smp):.0%} | "
                           f"{statistics.median(mem):.0f} | {statistics.median(ppl):.0f} |")
            print(out[-1], file=sys.stderr, flush=True)
    apply_world({"fill": "10", "str": "base", "circ": "open", "vdem": "never", "split": "none", "irr": "none", "dr": "0.20"})
    txt = "\n".join(out) + "\n"
    if a.out:
        Path(a.out).write_text(txt, encoding="utf-8")
    print(txt)


def main():
    ap = argparse.ArgumentParser()
    sub = ap.add_subparsers(dest="cmd", required=True)
    p = sub.add_parser("run")
    p.add_argument("--data", default=os.environ.get("SOC_DATA") or str(HERE.parent / "data"))
    p.add_argument("--seeds", type=int, default=100)
    p.add_argument("--seed0", type=int, default=0)
    p.add_argument("--years", type=int, default=60)
    p.add_argument("--procs", type=int, default=2)
    p.add_argument("--csv", required=True)
    p = sub.add_parser("summary")
    p.add_argument("--csv", required=True)
    p.add_argument("--out", default=None)
    p = sub.add_parser("check")
    p.add_argument("--data", default=os.environ.get("SOC_DATA") or str(HERE.parent / "data"))
    p = sub.add_parser("anatomy")
    p.add_argument("--data", default=os.environ.get("SOC_DATA") or str(HERE.parent / "data"))
    p.add_argument("--csv", required=True)
    p.add_argument("--n", type=int, default=200)
    p.add_argument("--out", default=None)
    a = ap.parse_args()
    {"run": cmd_run, "summary": cmd_summary, "check": cmd_check, "anatomy": cmd_anatomy}[a.cmd](a)


if __name__ == "__main__":
    main()
