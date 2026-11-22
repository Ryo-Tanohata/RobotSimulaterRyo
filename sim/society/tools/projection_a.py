#!/usr/bin/env python3
"""案 A (大人の死を昔の村に近づける) の見通し: トークン 0 の決まりの村で 30 年先を 3 通り (docs/society_phase/A_projection.md)

  PYTHONUTF8=1 python3.13 sim/society/tools/projection_a.py --data sim/society/data --seeds 20 --years 30 --out /tmp/pa/proj.json
  PYTHONUTF8=1 python3.13 sim/society/tools/projection_a.py --html /tmp/pa/proj.json --to sim/society/reports/A_projection.html
  PYTHONUTF8=1 python3.13 sim/society/tools/projection_a.py --data sim/society/data --calib      (S2 の生まれる見込みを探すだけ)

- data/ は読むだけ (state.json を 1 回・records/season_village.jsonl・records/people.json)。何も書かない。LLM は呼ばない。
- やり方: 本物の村の 29039 日目 (241年の終わり) の生きている人 (性・生まれた日・前に子を産んだ日) から始めて、
  era2._season_end と同じ順・同じ決まりの数で、1 季節ずつ 1 人ずつ乱数を引く (人ごとのくわしい模型。マイクロシミュレーション):
    年をとる (120 日で 1 歳・15 歳で大人) → 子が生まれる (15〜40 歳の女・男 15〜59 歳がいる・前の子から 120 日・空腹 0.5 未満。1 季節 p) →
    子の死 (0 歳 0.06・1〜4 歳 0.015・5〜14 歳 0.004 / 季節。病の季節は 3 倍。空腹 0.9 以上は 0.3。この季節に生まれた子は次から) →
    年寄りの死 (55 歳から 0.02 × (1 + (年 − 55)/10)) → 大人の病の死 (15〜39 歳 a・40〜54 歳 b / 季節。病の季節は 3 倍)。
  病の年: 1 年 15% (region.sick の上限 0.15。村は 784 人なので上限に当たる)。はやる季節は 4 つから 1 つ。
  子の手当て (T5 の直し 1) は 3 年で救えた見込み 0.61 人と小さいので入れない (入れると 1 年 0.2 人ほど子の死が減る)。
- 村に来る人: 232〜241年の記録で 1 年 平均 3.5 人 (よそから来た)。どの筋も同じに 1 年ポアソン 3.5 人、年は era2 と同じ (はじめ 2 人は 16〜35 歳・ほかは 2〜12 歳)。
- 食べ物 (村の人の決めは「去年までのやり方をくり返す」の決まりの答え):
    秋にまく草の種 = 働き手 1 人あたり s_w (232〜241年の秋の平均) × 働き手 (15〜59 歳 + 12〜14 歳の半分)。
    夏の刈り入れ = まいた種 × 種と実りの比 (230〜241年の本物の比 12 個から 1 年ごとに 1 つ引く。悪い年・草取りも入っている)。
    虫やネズミ = 刈り入れの 10.3% (230〜241年の平均)。食べる草の種 = 要る量 (大人 2,400・子 800/1,300/1,800 kcal/日) × g (237〜241年の平均。残りは乳・肉など)。
    蓄えの日数 = 村の蓄え / 1 日に要る量 (era2.store_days と同じ)。年の終わり (春の終わり) の値。
    畑の広さ = まいた種 / 6,000 つかみ (G13 の【仮定】1 ha に種 約 6,000 つかみ)。土地のかぎり = 草原と丘 276 ha − ヤギ 36 頭の草 (1 ha に 0.5 頭) 72 ha = 204 ha。
    (本物の村の決まりでは、畑の広さにかぎりはない。ここでは物差しとしてだけ数える)
    蓄えが尽きた季節: 子は空腹 1.0 (死の見込み 0.3)・母は空腹で産まない・大人は 2 季節つづくと 2 割が飢えで亡くなる【この見通しの仮定】。
- 数 (5 年まとめ): 平均寿命 e0・5 歳未満の死・合計特殊出生率は tools/stats_calc.py の life_table・tfr と同じ計算 (年齢は村の年、0 歳の a = 0.3)。
  乳児死亡率 = 1 歳前の死 / 生まれた子 (千あたり)。
"""
import argparse
import collections
import json
import math
import random
import statistics
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import stats_calc as SC  # noqa: E402

YEAR, SEASON = 120, 30
START_DAY = 29039
SEASONS = ("夏", "秋", "冬", "春")  # 1 年は夏から (day % 120 // 30)
SICK_YEAR_P, SICK_MULT = 0.15, 3
SEED_PER_HA, LAND_HA, GOAT_HA = 6000, 276.0, 72.0
GRAIN = 80
IMMIG_PER_YEAR = 3.5

# 筋 (a: 15〜39 歳・b: 40〜54 歳の 1 季節の病の死。old: 55 歳からの年寄りの死の倍率。birth: 1 季節の生まれる見込み)
#   a・b: 虎岩村 1812〜15年の生命表 (小林 1956 Table 5・6) の男女の 5 年の死亡確率 5q の平均を 1 年にし、病の季節 (1 年平均 × 1.075) で割って 1 季節に。
#     15〜39 歳: 5q の男女平均 0.0362 → 1 年 0.735% → 1 季節 0.0017。40〜54 歳: 5q 平均 0.087 → 1 年 1.80% → 1 季節 0.0042。
#   old: 15〜54 歳だけ直すと平均寿命は 約 30 歳で、江戸の村 (33〜38 年) に届かない (S1a)。年寄りの死 (今は 55 歳で 1 年 約 8%) も虎岩村
#     (55〜59 歳の 5q 男女とも 0.134 → 1 年 2.8%) に合わせて 0.35 倍 (55 歳で 1 年 2.8%)。15 歳の平均余命は 約 45 年 (虎岩村 男 43.9・女 45.0)。
#   S2 の birth: 合計特殊出生率 約 4.0 (今浦の平均 4.50 と二本松藩の農村 2.61〜3.38 の間)・自然増加 約 0.6%/年 (今浦 0.65%) になる所 (--calib)。
SCEN = {
    "S0": {"name": "今のまま", "a": 0.0075, "b": 0.0125, "old": 1.0, "birth": 0.08},
    "S1": {"name": "大人の死を直す", "a": 0.0017, "b": 0.0042, "old": 0.35, "birth": 0.08},
    "S2": {"name": "大人の死と生まれる見込みを直す", "a": 0.0017, "b": 0.0042, "old": 0.35, "birth": 0.045},
    "S1a": {"name": "(感度) 15〜54 歳の病の死だけ直す", "a": 0.0017, "b": 0.0042, "old": 1.0, "birth": 0.08},
}
OLD = 1.0  # 年寄りの死の倍率 (どの筋も 1.0 = 今の決まり。--old で感度だけ見る)


def load(data):
    """本物の 29039 日目の人と蓄え (state.json は 1 回だけ読み、要る所だけ残して捨てる)"""
    st = json.loads((Path(data) / "state.json").read_text(encoding="utf-8"))
    assert st["day"] == START_DAY, st["day"]
    people = [{"sex": p["sex"], "born": p["born_day"], "last": p.get("last_birth", -10 ** 6), "hunger": p.get("hunger", 0),
               "imm": p.get("origin") == "よそから来た"} for p in st["people"] if p["alive"]]
    store = sum(f["kcal"] for f in st["store"])
    harvest0 = sum(f["yield"] - f["harvested"] for f in st["era2"]["fields"] if f["state"] == "実った")  # 242年の夏の刈り入れ (実りは本物の村でもう決まっている)
    del st
    rows = {}
    with open(Path(data) / "records" / "season_village.jsonl", encoding="utf-8") as f:
        for line in f:
            r = json.loads(line)
            if r.get("year", 0) >= 229:
                rows[(r["year"], r["season"])] = r
    cum = lambda y, k: rows[(y, "春")]["grain_fate"][k]  # noqa: E731 (年の終わりまでの累計)
    ratios, pests, gshare, sw = [], [], [], []
    for y in range(230, 242):
        prod = cum(y, "produced") - cum(y - 1, "produced")
        ratios.append(prod / rows[(y - 1, "秋")]["fields"]["seed"])
        pests.append((cum(y, "pests") - cum(y - 1, "pests")) / prod)
        if y >= 237:
            need = sum(rows[(y, s)]["accounts"]["need"] for s in SEASONS)
            gshare.append((cum(y, "eaten") - cum(y - 1, "eaten")) * GRAIN / need)
        if y >= 232:
            a = rows[(y, "秋")]["by_age_class"]
            sw.append(rows[(y, "秋")]["fields"]["seed"] / (a["大人"] + 0.5 * a["手伝える子"]))
    last = rows[(241, "春")]
    cal = {"ratios": [round(x, 3) for x in ratios], "pest": statistics.mean(pests), "gshare": statistics.mean(gshare), "seed_w": statistics.mean(sw),
           "pots_hold": last["binding"]["pots"]["hold"], "pots_net": last["pots_made"] - last["pots_broken"], "store": store, "harvest0": harvest0,
           "store_days0": last["store_days"], "goats": last["goats"]["count"]}
    return people, cal


def observed(data):
    """本物の村の数 (records/people.json。stats_calc と同じ計算)"""
    P = {p["id"]: p for p in json.loads((Path(data) / "records" / "people.json").read_text(encoding="utf-8"))}
    dm = SC._demography(P, START_DAY)
    out = {}
    for y0, y1 in ((232, 236), (237, 241)):
        e0, u5 = SC.life_table(dm, y0, y1)
        b = sum(sum(dm["B"][Y].values()) for Y in range(y0, y1 + 1))
        inf = sum(dm["inf"][Y] for Y in range(y0, y1 + 1))
        out[f"{y0}-{y1}"] = {"e0": e0, "u5": u5, "tfr": SC.tfr(dm, y0, y1), "imr": round(1000 * inf / b) if b else None}
    pop = {}
    for Y in range(231, 242):
        pop[Y] = sum(1 for p in P.values() if p.get("born_day") is not None and (p.get("came_day") or 0) <= Y * YEAR + YEAR - 1
                     and p["born_day"] <= Y * YEAR + YEAR - 1 and not any(x is not None and x <= Y * YEAR + YEAR - 1 for x in (p.get("died_day"), p.get("left_day"))))
    out["pop"] = pop
    out["growth_237_241"] = round(100 * ((pop[241] / pop[236]) ** (1 / 5) - 1), 2)
    return out


def child_eat(age):
    return 800 if age < 3 else 1300 if age < 10 else 1800 if age < 15 else 2400


def run(people0, cal, sc, seed, years):
    """1 つの筋・1 つの種。戻り値: 年ごとの行と、人口学の帳 (stats_calc の形)"""
    rng = random.Random(seed * 7919)  # 人の乱数 (筋をまたいで同じ種。くり返せる)
    yr = random.Random(seed * 991)  # 天気 (種と実りの比) と病の年は、どの筋でも同じ列 (筋のちがいだけを見る)
    ppl = [dict(p, alive=True, child=(START_DAY - p["born"]) // YEAR < 15) for p in people0]
    store, seed_next, pots_hold = cal["store"], 0.0, cal["pots_hold"]
    dm = {"E": collections.defaultdict(collections.Counter), "Ef": collections.defaultdict(collections.Counter),
          "D": collections.defaultdict(collections.Counter), "B": collections.defaultdict(collections.Counter), "inf": collections.Counter()}
    rows, hungry_run, famine_seasons = [], 0, 0
    day = START_DAY
    y_first = (START_DAY + 1) // YEAR  # 242
    for y in range(y_first, y_first + years):
        sick_sea = yr.randrange(4) if yr.random() < SICK_YEAR_P else None
        ratio = yr.choice(cal["ratios"])
        imm_n = 0
        lam, k, pr = IMMIG_PER_YEAR, 0, 1.0  # ポアソン (乱数は rng から)
        L = math.exp(-lam)
        while True:
            pr *= rng.random()
            if pr <= L:
                break
            k += 1
        imm_n = k
        births = deaths = kid_deaths = adult_deaths = starved = 0
        sown = 0
        famine_this_year = False
        min_days = 10 ** 9
        for si in range(4):
            start = day + 1
            day += SEASON
            alive = [p for p in ppl if p["alive"]]
            # 食べ物 (季節のはじめの人で要る量)
            need_day = sum(child_eat((start - p["born"]) // YEAR) for p in alive)
            if si == 0:  # 夏: 秋にまいた畑が実る
                got = cal["harvest0"] if y == y_first else seed_next * ratio
                store += got * (1 - cal["pest"]) * GRAIN
                store = min(store, pots_hold * GRAIN + 0.0)  # つぼに入らない分は残らない (いまは入る量の 4 割ほど)
                seed_next = 0
            if si == 1:  # 秋: まく
                w = sum(1 for p in alive if 15 <= (start - p["born"]) // YEAR < 60) + 0.5 * sum(1 for p in alive if 12 <= (start - p["born"]) // YEAR < 15)
                want = cal["seed_w"] * w
                seed_next = max(0.0, min(want, store / GRAIN))
                store -= seed_next * GRAIN
                sown = seed_next
            eat = need_day * SEASON * cal["gshare"]
            short = eat > store
            store = max(0.0, store - eat)
            pots_hold += cal["pots_net"] / 4
            if short:
                famine_seasons += 1
                famine_this_year = True
                hungry_run += 1
            else:
                hungry_run = 0
            for p in alive:
                p["hunger"] = 1.0 if short else 0.0
            # 人口学の帳 (この季節にいた人: 0.25 年)
            for p in alive:
                a = (start - p["born"]) // YEAR
                dm["E"][y][a] += 0.25
                if p["sex"] == "女":
                    dm["Ef"][y][a] += 0.25
            # 季節の終わり (era2._season_end と同じ順)
            for p in alive:
                a = (day - p["born"]) // YEAR
                if p["child"] and a >= 15:
                    p["child"] = False
            sick = SICK_MULT if sick_sea == si else 1
            adults = [p for p in alive if not p["child"]]
            men = any(p["sex"] == "男" and (day - p["born"]) // YEAR < 60 for p in adults)
            new = []
            if men:
                for wmn in [p for p in adults if p["sex"] == "女" and 15 <= (day - p["born"]) // YEAR <= 40]:
                    if wmn["hunger"] >= 0.5 or day - wmn["last"] < YEAR:
                        continue
                    if rng.random() < sc["birth"]:
                        sex = "女" if rng.random() < 0.5 else "男"
                        new.append({"sex": sex, "born": day, "last": -10 ** 6, "hunger": 0, "imm": False, "alive": True, "child": True})
                        wmn["last"] = day
                        births += 1
                        dm["B"][y][(day - wmn["born"]) // YEAR] += 1
            for c in [p for p in alive if p["child"] and p["born"] < start]:
                a = (day - c["born"]) // YEAR
                pd = (0.06 if a < 1 else 0.015 if a < 5 else 0.004) * sick
                if c["hunger"] >= 0.9:
                    pd = max(pd, 0.3)
                if rng.random() < pd:
                    c["alive"] = False
                    kid_deaths += 1
                    dm["D"][y][a] += 1
                    if day - c["born"] < YEAR:
                        dm["inf"][y] += 1
            for p in adults:
                a = (day - p["born"]) // YEAR
                if a >= 55:
                    die = rng.random() < 0.02 * sc.get("old", 1.0) * OLD * (1 + (a - 55) / 10)
                else:
                    die = rng.random() < (sc["a"] if a < 40 else sc["b"]) * sick
                if not die and hungry_run >= 2 and rng.random() < 0.2:
                    die = True
                    starved += 1
                if die:
                    p["alive"] = False
                    adult_deaths += 1
                    dm["D"][y][a] += 1
            ppl.extend(new)
            if si == 3:  # 1 年に 1 回、来る人を入れる (春の終わり)
                for i in range(imm_n):
                    age = rng.randint(16, 35) if i % 3 < 2 else rng.randint(2, 12)
                    ppl.append({"sex": "女" if rng.random() < 0.5 else "男", "born": day - age * YEAR - rng.randrange(YEAR), "last": -10 ** 6,
                                "hunger": 0, "imm": True, "alive": True, "child": age < 15})
            if si == 3:
                ppl = [p for p in ppl if p["alive"]]
            alive_now = [p for p in ppl if p["alive"]]
            nd = sum(child_eat((day - p["born"]) // YEAR) for p in alive_now) or 1
            min_days = min(min_days, store / nd)
        alive = [p for p in ppl if p["alive"]]
        ages = [(day - p["born"]) // YEAR for p in alive]
        nd = sum(child_eat(a) for a in ages) or 1
        workers = sum(1 for a in ages if 15 <= a < 60) + 0.5 * sum(1 for a in ages if 12 <= a < 15)
        rows.append({"year": y, "pop": len(alive), "adults": sum(1 for a in ages if a >= 15), "old": sum(1 for a in ages if a >= 55), "workers_per_pop": round(workers / max(1, len(alive)), 3),
                     "store_days": round(store / nd), "min_days": round(min_days), "famine": famine_this_year, "below200": store / nd < 200,
                     "field_ha": round(sown / SEED_PER_HA, 1), "births": births, "kid_deaths": kid_deaths, "adult_deaths": adult_deaths,
                     "starved": starved, "imm": imm_n, "ratio": round(cal["harvest0"] / 297400 if y == y_first else ratio, 2), "sick": sick_sea is not None,
                     "need_vs_prod": round((sown * statistics.mean(cal["ratios"]) * (1 - cal["pest"]) * GRAIN) / (nd * YEAR * cal["gshare"]), 3)})
        if not alive:
            break
    return rows, dm


def window_stats(dm, y0, y1):
    e0, u5 = SC.life_table(dm, y0, y1)
    b = sum(sum(dm["B"][Y].values()) for Y in range(y0, y1 + 1))
    inf = sum(dm["inf"][Y] for Y in range(y0, y1 + 1))
    # 15 歳の平均余命 (同じ生命表の作り方で、15 歳から)
    return {"e0": e0, "u5": u5, "tfr": SC.tfr(dm, y0, y1), "imr": round(1000 * inf / b) if b else None, "e15": e15(dm, y0, y1)}


def e15(dm, y0, y1):
    groups = SC.AGE_GROUPS
    Eg, Dg = [0.0] * len(groups), [0] * len(groups)
    for Y in range(y0, y1 + 1):
        for a, v in dm["E"].get(Y, {}).items():
            Eg[SC._gi(a)] += v
        for a, v in dm["D"].get(Y, {}).items():
            Dg[SC._gi(a)] += v
    l, T = 1.0, 0.0
    for i, (lo, hi) in enumerate(groups):
        if lo < 15:
            continue
        m = Dg[i] / Eg[i] if Eg[i] > 0 else 0.0
        if hi is None:
            T += l / m if m > 0 else l * 10
            break
        n = hi - lo
        q = min(1.0, n * m / (1 + (n / 2) * m))
        d = l * q
        T += n * (l - d) + n / 2 * d
        l -= d
    return round(T, 1)


def pct(xs, q):
    xs = sorted(x for x in xs if x is not None)
    if not xs:
        return None
    k = (len(xs) - 1) * q
    f, c = math.floor(k), math.ceil(k)
    return xs[f] + (xs[c] - xs[f]) * (k - f)


def summarize(runs, years):
    """種ごとの行 → 年ごとの中央値と 10〜90% の幅"""
    y_first = (START_DAY + 1) // YEAR
    out = {"by_year": [], "marks": {}}
    for t in range(1, years + 1):
        Y = y_first + t - 1
        rec = {"t": t, "year": Y}
        for key in ("pop", "adults", "old", "workers_per_pop", "store_days", "min_days", "field_ha", "need_vs_prod"):
            vals = [r["rows"][t - 1][key] for r in runs if len(r["rows"]) >= t]
            rec[key] = [pct(vals, 0.1), pct(vals, 0.5), pct(vals, 0.9)]
        rec["famine_share"] = sum(1 for r in runs if any(x["famine"] for x in r["rows"][:t])) / len(runs)
        rec["below200_share"] = sum(1 for r in runs if any(x["below200"] for x in r["rows"][:t])) / len(runs)
        out["by_year"].append(rec)
    for t in (5, 10, 20, 30):
        if t > years:
            continue
        Y1 = y_first + t - 1
        Y0 = Y1 - 4
        st = [window_stats(r["dm"], Y0, Y1) for r in runs]
        g = []
        for r in runs:
            rows = r["rows"]
            p1 = rows[t - 1]["pop"]
            p0 = rows[t - 6]["pop"] if t >= 6 else 784
            g.append(100 * ((p1 / p0) ** (1 / 5) - 1) if p0 else None)
        nat = []
        for r in runs:
            rr = r["rows"][t - 5:t]
            popm = statistics.mean(x["pop"] for x in rr)
            nat.append(100 * sum(x["births"] - x["kid_deaths"] - x["adult_deaths"] for x in rr) / 5 / popm)
        m = {k: [pct([s[k] for s in st], q) for q in (0.1, 0.5, 0.9)] for k in ("e0", "e15", "tfr", "imr", "u5")}
        m["growth"] = [pct(g, q) for q in (0.1, 0.5, 0.9)]
        m["natural"] = [pct(nat, q) for q in (0.1, 0.5, 0.9)]
        m["window"] = f"{Y0}-{Y1}"
        out["marks"][t] = m
    return out


def project(data, seeds, years, scen_keys):
    people, cal = load(data)
    obs = observed(data)
    res = {"start_day": START_DAY, "people0": len(people), "cal": cal, "observed": obs, "seeds": seeds, "years": years, "scen": {}}
    for k in scen_keys:
        sc = SCEN[k]
        runs = []
        for s in range(seeds):
            rows, dm = run(people, cal, sc, s, years)
            runs.append({"rows": rows, "dm": dm})
        res["scen"][k] = {"def": sc, **summarize(runs, years)}
        mk = res["scen"][k]["marks"]
        print(k, sc["name"], {t: {kk: (round(v[1], 2) if v[1] is not None else None) for kk, v in m.items() if kk != "window"} for t, m in mk.items()}, flush=True)
        by = res["scen"][k]["by_year"]
        print("   pop", [round(b["pop"][1]) for b in by[4::5]], "store", [round(b["store_days"][1]) for b in by[4::5]],
              "ha", [b["field_ha"][1] for b in by[4::5]], "famine", by[-1]["famine_share"], "below200", by[-1]["below200_share"], flush=True)
    return res


def calib(data, seeds=10, years=30):
    """S2 の生まれる見込みを探す (年 21〜30 の合計特殊出生率と自然増加)"""
    people, cal = load(data)
    for b in (0.035, 0.040, 0.045, 0.050):
        sc = dict(SCEN["S1"], birth=b, name=f"b{b}")
        tf, gr = [], []
        for s in range(seeds):
            rows, dm = run(people, cal, sc, s, years)
            tf.append(SC.tfr(dm, 262, 271))
            gr.append(100 * sum(r["births"] - r["kid_deaths"] - r["adult_deaths"] for r in rows[-10:]) / 10 / statistics.mean(r["pop"] for r in rows[-10:]))
        print(b, "TFR", round(statistics.median(tf), 2), "natural %/yr", round(statistics.median(gr), 2))


# ---------------- スマホ用の HTML (1 ファイル。SVG の線グラフ) ----------------

CSS_COL = {"S0": "var(--s1)", "S1": "var(--s2)", "S2": "var(--s3)"}  # 分類の色は決まった順 (1 青・2 だいだい・3 水色)


def svg_lines(res, key, title, unit, ref=None, fmt="{:.0f}", cid="c"):
    """線グラフ 1 枚 (中央値の線 + 10〜90% の帯)。右はしに名前 (文字は文字の色、色は線の印だけ)。ゆびで触ると、その年の 3 つの数"""
    W, H, l, r, t, b = 340, 210, 44, 78, 26, 30
    ser = {k: v["by_year"] for k, v in res["scen"].items()}
    allv = [x for s in ser.values() for row in s for x in row[key] if x is not None]
    if ref:
        allv += [ref[0]]
    raw = max(allv) * 1.05 / 4
    mag = 10 ** math.floor(math.log10(raw))
    step = next(m * mag for m in (1, 2, 2.5, 5, 10) if m * mag >= raw)  # 目もりはきりのよい数
    lo, hi = 0.0, step * 4
    years = len(next(iter(ser.values())))
    X = lambda i: l + (W - l - r) * i / max(1, years)  # noqa: E731
    Y = lambda v: t + (H - t - b) * (1 - (v - lo) / (hi - lo))  # noqa: E731
    out = [f'<svg id="{cid}" viewBox="0 0 {W} {H}" role="img" aria-label="{title}"><title>{title}</title>']
    for k in range(5):
        v = lo + step * k
        out.append(f'<line x1="{l}" x2="{W - r}" y1="{Y(v):.1f}" y2="{Y(v):.1f}" class="grid"/>'
                   f'<text x="{l - 4}" y="{Y(v) + 3:.1f}" class="ax" text-anchor="end">{fmt.format(v)}</text>')
    for i in (0, 10, 20, 30):
        if i <= years:
            out.append(f'<text x="{X(i):.1f}" y="{H - b + 14}" class="ax" text-anchor="middle">{i} 年後</text>')
    if ref:
        out.append(f'<line x1="{l}" x2="{W - r}" y1="{Y(ref[0]):.1f}" y2="{Y(ref[0]):.1f}" class="ref"/>'
                   f'<text x="{l + 4}" y="{Y(ref[0]) - 4:.1f}" class="ax">{ref[1]}</text>')
    ends = []
    for k, rows in ser.items():
        band = [(X(i + 1), Y(row[key][0])) for i, row in enumerate(rows)] + [(X(i + 1), Y(row[key][2])) for i, row in reversed(list(enumerate(rows)))]
        out.append('<polygon points="' + " ".join(f"{x:.1f},{y:.1f}" for x, y in band) + f'" style="fill:{CSS_COL[k]}" opacity="0.13"/>')
        pts = [(X(i + 1), Y(row[key][1])) for i, row in enumerate(rows)]
        out.append('<polyline points="' + " ".join(f"{x:.1f},{y:.1f}" for x, y in pts) + f'" fill="none" style="stroke:{CSS_COL[k]}" stroke-width="2"/>')
        ends.append([pts[-1][1], k, rows[-1][key][1]])
    ends.sort()
    for i in range(1, len(ends)):  # 終わりのラベルが重ならないように
        if ends[i][0] - ends[i - 1][0] < 12:
            ends[i][0] = ends[i - 1][0] + 12
    for y, k, v in ends:
        out.append(f'<rect x="{W - r + 3}" y="{y - 1:.1f}" width="8" height="3" rx="1" style="fill:{CSS_COL[k]}"/>'
                   f'<text x="{W - r + 14}" y="{y + 3:.1f}" class="lab">{k} {fmt.format(v)}</text>')
    out.append(f'<line class="xh" x1="0" x2="0" y1="{t}" y2="{H - b}" visibility="hidden"/>'
               f'<rect class="hit" x="{l}" y="{t}" width="{W - l - r}" height="{H - t - b}" fill="transparent"/>')
    out.append(f'<text x="{l}" y="14" class="ttl">{title}{(" (" + unit + ")") if unit else ""}</text></svg>')
    data = {k: [row[key][1] for row in rows] for k, rows in ser.items()}
    meta = {"l": l, "w": W - l - r, "n": years, "fmt": 2 if "{:.2f}" == fmt else 0, "unit": unit}
    return "".join(out), cid, data, meta


def html(res):
    import html as H
    S = res["scen"]
    obs = res["observed"]

    def cell(v, f="{:.1f}"):
        return "―" if v is None or v[1] is None else f.format(v[1]) + f' <span class="band">({f.format(v[0])}〜{f.format(v[2])})</span>'

    def by(k, t):
        return S[k]["by_year"][t - 1]
    rows = []
    for t in (5, 10, 20, 30):
        for k in S:
            m, b = S[k]["marks"][str(t)], by(k, t)
            rows.append(f"<tr><td>{t} 年後<br><span class=band>{241 + t}年</span></td><td><i class=sw style='background:{CSS_COL[k]}'></i><b>{k}</b></td>"
                        f"<td>{cell(b['pop'], '{:.0f}')}</td><td>{cell(b['adults'], '{:.0f}')}</td><td>{cell(b['workers_per_pop'], '{:.2f}')}</td>"
                        f"<td>{cell(b['store_days'], '{:.0f}')}</td><td>{round(100 * b['famine_share'])}% / {round(100 * b['below200_share'])}%</td>"
                        f"<td>{cell(b['field_ha'], '{:.0f}')}</td>"
                        f"<td>{cell(m['e0'])}</td><td>{cell(m['e15'])}</td><td>{cell(m['tfr'], '{:.2f}')}</td><td>{cell(m['imr'], '{:.0f}')}</td>"
                        f"<td>{cell(m['growth'], '{:.2f}')}</td><td>{cell(m['natural'], '{:.2f}')}</td></tr>")
    legend = "".join(f'<span class="key"><i style="background:{CSS_COL[k]}"></i>{k} {H.escape(S[k]["def"]["name"])}</span>' for k in S)
    made = [svg_lines(res, "pop", "人の数", "人", cid="c1"),
            svg_lines(res, "store_days", "年の終わりの蓄え", "日分", ref=(200, "相談の線 200 日分"), cid="c2"),
            svg_lines(res, "field_ha", "畑の広さの見積り", "ha", ref=(204, "土地のかぎり 204 ha (見積り)"), cid="c3"),
            svg_lines(res, "workers_per_pop", "働き手 ÷ 人", "", fmt="{:.2f}", cid="c4")]
    charts = "".join(f'<div class="card">{m[0]}</div>' for m in made)
    js_data = json.dumps({m[1]: {"d": m[2], "m": m[3]} for m in made}, ensure_ascii=False)
    o = obs["237-241"]
    defs = "".join(f"<li><b>{k}</b> {H.escape(S[k]['def']['name'])}: 15〜39 歳 {S[k]['def']['a']}・40〜54 歳 {S[k]['def']['b']} (1 季節)・"
                   f"55 歳から × {S[k]['def'].get('old', 1.0)}・生まれる見込み {S[k]['def']['birth']} (1 季節)</li>" for k in S)
    return f"""<!doctype html><html lang="ja"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>案 A の見通し (30 年先・3 通り)</title><style>
:root{{--bg:#fcfcfb;--fg:#0b0b0b;--mute:#52514e;--grid:#e8e7e3;--card:#f4f3f0;--s1:#2a78d6;--s2:#eb6834;--s3:#1baf7a}}
@media (prefers-color-scheme:dark){{:root{{--bg:#1a1a19;--fg:#f0efec;--mute:#c3c2b7;--grid:#383835;--card:#232322;--s1:#3987e5;--s2:#d95926;--s3:#199e70}}}}
body{{margin:0;font:15px/1.65 system-ui,-apple-system,"Hiragino Sans",sans-serif;background:var(--bg);color:var(--fg)}}
main{{max-width:760px;margin:auto;padding:14px}} h1{{font-size:20px;line-height:1.4}} h2{{font-size:17px;margin-top:26px}}
.card{{background:var(--card);border-radius:10px;padding:8px;margin:10px 0;position:relative}} svg{{width:100%;height:auto;touch-action:pan-y}}
.grid{{stroke:var(--grid)}} .ref{{stroke:var(--mute);stroke-dasharray:4 3}} .xh{{stroke:var(--mute);stroke-width:1}}
.ax{{font-size:10px;fill:var(--mute)}} .ttl{{font-size:12px;fill:var(--fg);font-weight:600}} .lab{{font-size:10.5px;fill:var(--fg)}}
.key{{display:inline-block;margin-right:12px;font-size:13px}} .key i,.sw{{display:inline-block;width:12px;height:3px;margin-right:4px;vertical-align:middle;border-radius:1px}}
table{{border-collapse:collapse;font-size:12px;min-width:1000px}} td,th{{border-bottom:1px solid var(--grid);padding:4px 6px;text-align:right;vertical-align:top}}
th{{color:var(--mute);font-weight:500}} .wrap{{overflow-x:auto}} .band{{color:var(--mute);font-size:10px}}
.box{{border-left:3px solid var(--mute);padding:6px 10px;background:var(--card)}}
.tip{{position:absolute;pointer-events:none;background:var(--bg);color:var(--fg);border:1px solid var(--grid);border-radius:6px;padding:4px 8px;font-size:12px;display:none;white-space:nowrap}}
</style></head><body><main>
<h1>案 A「大人の死を昔の村に近づける」の見通し</h1>
<p>241年の終わり (29039 日目) の本物の村から、30 年先を 3 通り。決まりの村 (トークン 0)・乱数の種 {res['seeds']} 本の中央値と、10〜90% の幅 (うすい帯)。本物の村は止めたまま。data には何も書いていない。</p>
<p>{legend}</p>
<div class="box"><b>ひとことで</b><br>{res.get('lead', '')}</div>
<h2>グラフ (指でなぞると、その年の数)</h2>{charts}
<h2>数の表 (中央値・かっこは 10〜90%)</h2>
<div class="wrap"><table><tr><th></th><th></th><th>人</th><th>大人 (15 歳から)</th><th>働き手 ÷ 人</th><th>蓄え (日分)</th><th>ききん / 200 日分を切った (それまでに 1 回でも。種の割合)</th><th>畑 ha (かぎり 204)</th><th>平均寿命</th><th>15 歳の平均余命</th><th>合計特殊出生率</th><th>乳児死亡率</th><th>人のふえ方 %/年</th><th>うち自然増加 %/年</th></tr>
{''.join(rows)}</table></div>
<p class="band">平均寿命・15 歳の平均余命・合計特殊出生率・乳児死亡率は、その年までの 5 年まとめ。人のふえ方は 5 年の年平均 (村に来る人 1 年 3.5 人をふくむ)。
いまの村 (237〜241年): 平均寿命 {o['e0']} 歳・合計特殊出生率 {o['tfr']}・乳児死亡率 {o['imr']}・人のふえ方 {obs['growth_237_241']}%/年。</p>
<h2>3 つの筋の決まりの数</h2><ul>{defs}</ul>
<h2>くらべる昔の村 (開いた資料)</h2>
<ul><li>信濃国 虎岩村 1812〜15年: 平均寿命 男 36.8・女 36.5 年、15 歳の平均余命 男 43.9・女 45.0 年、人のふえ方 1 年 0.44% (小林 1956)。</li>
<li>野母村・仁井田村・西条村: 平均寿命 33.4〜37.7 年 (中島 2018)。</li>
<li>石見国 今浦 1798〜1841年: 合計出生率 平均 4.50 (2.98〜5.74)、自然増加 0.65%・人口増加 0.33% (廣嶋 2023)。</li>
<li>陸奥国 二本松藩の農村: 合計特殊出生率 2.61〜3.38 (高橋 2007 の表 1)。</li></ul>
<p class="band">くわしい書きつけ: docs/society_phase/A_projection.md・作りの下書き: docs/society_phase/A_design.md・道具: sim/society/tools/projection_a.py</p>
</main>
<script>
const D={js_data};
const NAMES={json.dumps({k: S[k]["def"]["name"] for k in S}, ensure_ascii=False)};
for(const [id,o] of Object.entries(D)){{
  const svg=document.getElementById(id),card=svg.parentNode,tip=document.createElement('div');tip.className='tip';card.appendChild(tip);
  const xh=svg.querySelector('.xh'),hit=svg.querySelector('.hit');
  const move=e=>{{const r=svg.getBoundingClientRect(),vb=svg.viewBox.baseVal,sx=vb.width/r.width;
    const x=(e.clientX-r.left)*sx;let i=Math.round((x-o.m.l)/o.m.w*o.m.n);i=Math.max(1,Math.min(o.m.n,i));
    const X=o.m.l+o.m.w*i/o.m.n;xh.setAttribute('x1',X);xh.setAttribute('x2',X);xh.setAttribute('visibility','visible');
    tip.textContent='';const h=document.createElement('div');h.textContent=i+' 年後 ('+(241+i)+'年)';tip.appendChild(h);
    for(const [k,v] of Object.entries(o.d)){{const d=document.createElement('div');d.textContent=k+' '+NAMES[k]+': '+(v[i-1]==null?'―':v[i-1].toFixed(o.m.fmt))+(o.m.unit?' '+o.m.unit:'');tip.appendChild(d);}}
    tip.style.display='block';const px=X/sx;tip.style.left=Math.min(px+12,r.width-tip.offsetWidth)+'px';tip.style.top='28px';}};
  const out=()=>{{tip.style.display='none';xh.setAttribute('visibility','hidden');}};
  hit.addEventListener('pointermove',move);hit.addEventListener('pointerdown',move);hit.addEventListener('pointerleave',out);
}}
</script></body></html>"""


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--data", default=str(HERE.parent / "data"))
    ap.add_argument("--seeds", type=int, default=20)
    ap.add_argument("--years", type=int, default=30)
    ap.add_argument("--scen", default="S0,S1,S2")
    ap.add_argument("--out")
    ap.add_argument("--calib", action="store_true")
    ap.add_argument("--old", type=float, default=1.0, help="年寄りの死の倍率 (感度だけ)")
    ap.add_argument("--html")
    ap.add_argument("--to")
    ap.add_argument("--lead", default="")
    a = ap.parse_args()
    global OLD
    OLD = a.old
    if a.html:
        res = json.loads(Path(a.html).read_text(encoding="utf-8"))
        if a.lead:
            res["lead"] = a.lead
        Path(a.to).write_text(html(res), encoding="utf-8")
        return
    if a.calib:
        calib(a.data)
        return
    res = project(a.data, a.seeds, a.years, a.scen.split(","))
    if a.out:
        out = Path(a.out).resolve()
        assert "sim/society/data" not in str(out), "data の下には書かない"
        out.write_text(json.dumps(res, ensure_ascii=False), encoding="utf-8")


if __name__ == "__main__":
    main()
