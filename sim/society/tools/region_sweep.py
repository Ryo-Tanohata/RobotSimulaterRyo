"""地域の決まりだけの掃き出し (docs/society_phase/G7_design.md 6.3。トークンは使わない。【シ】)

  SOC_DATA=/tmp/…/data PYTHONUTF8=1 python3.13 sim/society/tools/region_sweep.py [--seeds 200] [--years 60] [--out FILE]

- region.py の決まり (4.B.3) だけを、川辺の村を「決まりで動く集落」(V0) にして回す。世界 (era2・world) は動かさない。state.json は読むだけ
  (はじめの人数・まわりの村・村の蓄え。$SOC_DATA か --data。本物の data を書きかえることはない。写しを指すのがよい)
- 変えるもの: はじめの集落 (地域の人数 (村を除く) を K の合計の 3.4% (今のまま、置かない)・10%・30%・50% にする。塩 79 の置き方 (4.B.1) と同じ
  region.fill_cells を、種ごとの列で) と、案 (c) (置かずに、地図の端に 1 年 0.1 の見込みで新しい集落が来る)。
  村の動き方: 求めない (求められたら決まりの手) / いつも求める (毎年いちばん弱い相手に、構え「求める」で) / いつも払う。家が出ていく: 1 年 0・0.02・0.05・0.15
- 出すもの: 決める段 3 (4.D.2 の数え方) のまとまりに村がいる (条件 1) に届いた割合と年の真ん中、地域のどこかに段 3 ができた割合、
  いちばん上の集落、戦・逃げた回数・崩れ (つながりが切れた)・なくなった集落、囲まれていた決定の割合 (逃げ場がなかった求めへの答えの割合)、
  分かれた回数と出ていった人、B の数え方 (つながりの深さ + 中心の役) との差、条件 1 が 8 年・16 年進まなかった回の割合と年の真ん中
- 便り (4.C) はまだ作っていないので、この表はみな「便りなし」。便りあり・なしのくらべは、便りを作ったあとに足す
- 乱数は種ごとの文字の種 (random.Random("sweep|…")) で、同じ引数なら同じ表になる (PYTHONHASHSEED によらない)
- 本物の村の病 (子と大人の死が 3 倍になる季節) は世界の側の決まりなので、ここでは村 (V0) の病は数えない。まわりの集落の病は数える
"""
import argparse
import json
import math
import os
import random
import statistics
import sys
from multiprocessing import Pool
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent))
import region  # noqa: E402

FILLS = (("3.4% (今のまま)", 0.0, False), ("10%", 0.10, False), ("30%", 0.30, False), ("50%", 0.50, False), ("案 c (端に 1 年 0.1)", 0.0, True))
POLICIES = (("求めない・出ていく 0", None, None, 0.0), ("求めない・出ていく 0.02", None, None, 0.02), ("求めない・出ていく 0.05", None, None, 0.05),
            ("求めない・出ていく 0.15", None, None, 0.15), ("いつも求める・出ていく 0", "いつも", None, 0.0), ("いつも払う・出ていく 0", None, "払う", 0.0))
EDGE_P = 0.1  # 案 c: 地図の端に新しい集落が来る見込み (1 年)
LEAVE_N = 5  # 村を出る家の人数【仮定】(5 人未満の集落はすぐなくなる (11) ので、出た家は 5 人とみる)
GRAIN = 3200  # 草の種 1 つかみの kcal (world.UNITS の草の種と同じ。村の蓄えを、つかみに直すためだけ)


def load(data):
    st = json.loads((Path(data) / "state.json").read_text(encoding="utf-8"))
    e2 = st.get("era2") or {}
    others = (e2.get("g6") or {}).get("others", [])
    pop = sum(1 for p in st["people"] if p["alive"])
    store = sum(f["kcal"] for f in st.get("store", []))
    goats = sum(1 for g in e2.get("goats", []) if g.get("owner") is None)
    leader = (e2.get("g5") or {}).get("leader")
    return {"day": st["day"], "pop": pop, "grain": round(store / GRAIN), "goats": goats, "leader": bool(leader),
            "others": [{k: o[k] for k in ("id", "name", "dir", "days", "people", "goats", "grain", "known")} for o in others if not o.get("gone")]}


def start(base, fill, seed):
    """はじめの地域 (掃き出しの写し): 村 V0・G6 からある集落・はじめの集落 (fill > 0)"""
    v0 = {"id": "V0", "name": "川辺の村", "village": True, "people": base["pop"], "cell": list(region.VILLAGE), "land": "r", "org": 1 if base["leader"] else 0,
          "grain": base["grain"], "goats": base["goats"], "tech": 1, "commit": {}, "stance": "ふつう", "walls": None, "known": 0,
          "kcap": 10 ** 6}  # 村の暮らせる人数は地図の K でなく世界が決める (ここでは K で減らさない)
    setts, used = [v0], {region.VILLAGE}
    nxt = 1
    for o in sorted(base["others"], key=lambda o: region.num(o["id"])):
        c = region.place_known(o["dir"], o["days"], used)
        used.add(c)
        setts.append(new(o["id"], c, o["people"], o["name"], grain=o["grain"], goats=o["goats"], known=o["known"]))
        nxt = max(nxt, region.num(o["id"]) + 1)
    if fill > 0:
        have = sum(s["people"] for s in setts[1:])
        for c, n in region.fill_cells(used, have, fill, random.Random(f"sweep|fill|{seed}")):
            setts.append(new(f"N{nxt}", c, n))
            nxt += 1
    return setts, nxt


def new(sid, c, n, name=None, grain=None, goats=None, known=None):
    return {"id": sid, "name": name or sid, "people": n, "cell": list(c), "land": region.land(c), "org": 0, "commit": {}, "stance": "ふつう",
            "walls": None, "tech": 1, "head_age": 0, "cattle_f": n / region.CATTLE_PER, "grain": n * 100 if grain is None else grain,
            "goats": round(n * 0.4) if goats is None else goats, "bad": None, "parent": None,
            "known": known if known is not None else (0 if region.dist(c, region.VILLAGE) <= region.KNOWN_NEAR else None)}


def run(args):
    """1 つの種で、決まりだけの地域を years 年回す"""
    base, fill, edge, pol, seed, years = args
    _, vdem, vans, leave = pol
    setts, nxt = start(base, fill, seed)
    R = {"ties": [], "demands": [], "wars": [], "pending": [], "gone": [], "log": [], "next_war": 1}
    day0 = (base["day"] + 1) // region.YEAR_DAYS * region.YEAR_DAYS - 1  # 年の終わりの日にそろえる
    m = {"reach": None, "any3": None, "top": None, "wars": 0, "flee": 0, "breaks": 0, "gone": 0, "decisions": 0, "boxed": 0,
         "splits": 0, "moved": 0, "left": 0, "b_gap": [], "stall8": None, "stall16": None, "maxD": 0}
    best, since = 0, 0
    counter = {"n": nxt}

    def make(parent, c, n, kind):
        o = new(f"N{counter['n']}", c, n, f"{parent.get('name', parent['id'])}の子")
        o["grain"], o["goats"], o["cattle_f"] = 0, 0, 0.0
        counter["n"] += 1
        setts.append(o)
        return o
    sick_prev = set()
    for k in range(years):
        day = day0 + k * region.YEAR_DAYS  # 年の最後の日
        y = (day + 1) // region.YEAR_DAYS
        live = region._live(setts)
        # 1. 地域の天気 (塩 53 にあたる列)
        z, rbad, bad = region.weather(random.Random(f"sweep|weather|{seed}|{y}"), [(s["id"], region.cell_of(s)) for s in live])
        for s in live:
            s["bad"] = day if s["id"] in bad else None
        # 案 c: 地図の端に新しい集落
        er = random.Random(f"sweep|edge|{seed}|{y}")
        if edge and er.random() < EDGE_P:
            occ = region.occupied(setts)
            ed = [c for c in region.cells() if c not in occ and (c[0] in (0, region.SIZE - 1) or c[1] in (0, region.SIZE - 1))]
            if ed:
                c = er.choice(ed)
                setts.append(new(f"N{counter['n']}", c, max(1, round(region.cap(c) * er.uniform(*region.FILL_SHARE)))))
                counter["n"] += 1
        out = []
        region.year_end(R, setts, random.Random(f"sweep|year|{seed}|{y}"), y, day, grow_village=True, village_demand=vdem, out=out)
        # 病 (まわりの集落だけ)
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
                m["decisions"] += 1
                m["boxed"] += not p["refuge"]
        # 次の年のはじめ (夏の集まりの日)
        d1 = day + 1
        vill = {q["id"]: vans for q in region.open_demands(R) if q["to"] == "V0"} if vans else {}
        v0 = next(s for s in setts if s["id"] == "V0")
        lr = random.Random(f"sweep|leave|{seed}|{y}")
        if leave and lr.random() < leave and v0["people"] > 2 * LEAVE_N:  # 村の家が出ていく (分かれた家の集落)
            c = region.near_cell(setts, region.VILLAGE)
            if c:
                o = make(v0, c, LEAVE_N, "分かれた家")
                o["parent"], o["known"] = "V0", d1
                region.commit_add(o, "V0", region.COMMIT_NEW)
                region.commit_add(v0, o["id"], region.COMMIT_NEW)
                v0["people"] -= LEAVE_N
                m["left"] += 1
        region.decide(R, setts, d1, village=vill, make=make, out=out)
        region.pay_ties(R, setts, d1, out=out)
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
            elif e["kind"] == "集落" and e["data"].get("new"):
                m["splits" if "分かれた" in e["text"] else "moved"] += 1
        # 決める段 (この 1 年に払った記録のあるつながり)
        paid = [t for t in region.ties_on(R) if t["paid"] and t["paid"][-1] > d1 - region.YEAR_DAYS]
        lv = region.levels(setts, paid, d1, village_rules=True)  # 村も決まりで動く集落なので、段 2 なら「集める役」がいるとみる
        vg = next((g for g in lv if "V0" in g["members"]), None)
        dv = vg["D"] if vg else 0
        m["maxD"] = max(m["maxD"], max((g["D"] for g in lv), default=0))
        if any(g["D"] >= 3 for g in lv) and m["any3"] is None:
            m["any3"] = k + 1
        if vg:
            m["b_gap"].append(vg["B"] - vg["D"])
        if dv >= 3 and m["reach"] is None:
            m["reach"], m["top"] = k + 1, vg["top"]
        if m["reach"] is None:
            if dv > best:
                best, since = dv, k + 1
            stall = k + 1 - since
            if stall >= 8 and m["stall8"] is None:
                m["stall8"] = k + 1
            if stall >= 16 and m["stall16"] is None:
                m["stall16"] = k + 1
    m["b_gap"] = statistics.mean(m["b_gap"]) if m["b_gap"] else 0.0
    m["people_end"] = sum(s["people"] for s in region._live(setts) if not s.get("village"))
    m["setts_end"] = sum(1 for s in region._live(setts) if not s.get("village"))
    return m


def _med(xs):
    return statistics.median(xs) if xs else None


def table(base, seeds, years, procs):
    rows = []
    for fname, fill, edge in FILLS:
        for pol in POLICIES:
            jobs = [(base, fill, edge, pol, s, years) for s in range(seeds)]
            with Pool(procs) as pool:
                ms = pool.map(run, jobs, chunksize=max(1, seeds // (procs * 4)))
            n = len(ms)
            r = [m["reach"] for m in ms if m["reach"]]
            a3 = [m["any3"] for m in ms if m["any3"]]
            tops = {}
            for m in ms:
                if m["top"]:
                    tops[m["top"]] = tops.get(m["top"], 0) + 1
            dec = sum(m["decisions"] for m in ms)
            s8 = [m["stall8"] for m in ms if m["stall8"]]
            s16 = [m["stall16"] for m in ms if m["stall16"]]
            rows.append({"fill": fname, "policy": pol[0], "reach": len(r) / n, "reach_med": _med(r), "any3": len(a3) / n,
                         "top": "・".join(f"{k} {v}" for k, v in sorted(tops.items(), key=lambda kv: -kv[1])[:2]) or "-",
                         "wars": statistics.mean(m["wars"] for m in ms), "flee": statistics.mean(m["flee"] for m in ms),
                         "breaks": statistics.mean(m["breaks"] for m in ms), "gone": statistics.mean(m["gone"] for m in ms),
                         "boxed": (sum(m["boxed"] for m in ms) / dec) if dec else None, "dec": dec / n,
                         "splits": statistics.mean(m["splits"] for m in ms), "moved": statistics.mean(m["moved"] for m in ms),
                         "b_gap": statistics.mean(m["b_gap"] for m in ms), "maxD": statistics.mean(m["maxD"] for m in ms),
                         "stall8": len(s8) / n, "stall8_med": _med(s8), "stall16": len(s16) / n, "stall16_med": _med(s16),
                         "people_end": statistics.mean(m["people_end"] for m in ms), "setts_end": statistics.mean(m["setts_end"] for m in ms)})
            print(f"  {fname} / {pol[0]}: 条件 1 {rows[-1]['reach']:.0%}", file=sys.stderr)
    return rows


def fmt(rows, base, seeds, years):
    def f(v, p=False, d=1):
        if v is None:
            return "-"
        if p:
            return "1% 未満" if 0 < v and f"{v:.0%}" == "0%" else "99% より上" if v < 1 and f"{v:.0%}" == "100%" else f"{v:.0%}"
        return f"{v:.{d}f}"
    out = [f"| はじめの集落 | 村の動き方 | 条件 1 (段 3 に村) | 年の真ん中 | 地域のどこかに段 3 | 段の最大 (平均) | いちばん上 | 戦 | 逃げた | 崩れ | なくなった | "
           f"求めへの答え (1 回あたり) | 囲まれていた割合 | 分かれた | 出ていった (新しい集落) | B − D | 8 年進まない | 16 年進まない | {years} 年後の集落と人 |",
           "|" + "---|" * 19]
    for r in rows:
        out.append(f"| {r['fill']} | {r['policy']} | {f(r['reach'], True)} | {f(r['reach_med'], d=0)} | {f(r['any3'], True)} | {f(r['maxD'], d=2)} | {r['top']} | "
                   f"{f(r['wars'])} | {f(r['flee'])} | {f(r['breaks'])} | {f(r['gone'])} | {f(r['dec'])} | {f(r['boxed'], True)} | {f(r['splits'])} | "
                   f"{f(r['moved'])} | {f(r['b_gap'], d=2)} | {f(r['stall8'], True)} ({f(r['stall8_med'], d=0)} 年) | "
                   f"{f(r['stall16'], True)} ({f(r['stall16_med'], d=0)} 年) | {f(r['setts_end'])}・{f(r['people_end'], d=0)} |")
    return "\n".join(out)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--data", default=os.environ.get("SOC_DATA") or str(HERE.parent / "data"))
    ap.add_argument("--seeds", type=int, default=200)
    ap.add_argument("--years", type=int, default=60)
    ap.add_argument("--procs", type=int, default=os.cpu_count() or 2)
    ap.add_argument("--out", default=None)
    a = ap.parse_args()
    base = load(a.data)
    rows = table(base, a.seeds, a.years, a.procs)
    k = region.k_total()
    head = (f"はじめの state: {base['day']} 日目 (村 {base['pop']} 人・まわり {len(base['others'])} 集落 {sum(o['people'] for o in base['others'])} 人)。"
            f"K の合計 (村のますを除く) {k} 人。種 {a.seeds} × {a.years} 年。数はみな 1 回あたりの平均 (割合は回の割合)")
    txt = head + "\n\n" + fmt(rows, base, a.seeds, a.years) + "\n"
    if a.out:
        Path(a.out).write_text(txt, encoding="utf-8")
    print(txt)


if __name__ == "__main__":
    main()
