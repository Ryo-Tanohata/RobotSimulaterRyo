"""時期ごとの仕事一覧と、一人ずつの職務経歴書 (見るだけ。2026-11-21 本人「履歴書・職務経歴書的なもの」「その時期の仕事一覧」)

data/records/season_person/*.jsonl (季節ごと・人ごとの記録) と people.json・households.json・year_names.json を読み、
app/work_data.json を書く。村の動き・state.json には一切さわらない。

使い方: cd sim/society && python3.13 tools/build_work.py
"""
import glob
import json
import os
import sys
from collections import Counter, defaultdict

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, ROOT)
import world  # noqa: E402

REC = os.path.join(ROOT, "data", "records")
OUT = os.path.join(ROOT, "app", "work_data.json")
YEAR = 4 * world.SEASON_DAYS
WHY_MAX = 90
CHANGES_MAX = 60
# 量を数える出来高 (outputs の中で、数で足せるもの)
OUTS = {"harvested": "刈った草の種 (つかみ)", "sown": "まいた草の種 (つかみ)", "planted": "植えた芋", "pots": "土器 (個)",
        "sickles": "鎌 (本)", "goats_caught": "つかまえたヤギ (頭)", "house_work_days": "家づくり (人日)", "milk": "乳",
        "tree_picked": "木から取った実"}
REST_PREFIX = "休む"


def load_json(name, default):
    p = os.path.join(REC, name)
    if not os.path.exists(p):
        return default
    with open(p, encoding="utf-8") as f:
        return json.load(f)


def short(t):
    t = (t or "").strip().replace("\n", " ")
    return t if len(t) <= WHY_MAX else t[:WHY_MAX] + "…"


def build():
    people = {p["id"]: p for p in load_json("people.json", [])}
    hh = {h["id"]: h["name"] for h in load_json("households.json", [])}
    ynames = {y["year"]: y.get("name") for y in load_json("year_names.json", [])}

    # 時期ごと: 年 → 仕事 → {人日, 人}
    yd = defaultdict(Counter)
    yp = defaultdict(lambda: defaultdict(set))
    yadults = defaultdict(set)
    yseas = defaultdict(set)
    # 人ごと
    pyear = defaultdict(lambda: defaultdict(lambda: {"acts": Counter(), "dec": Counter(), "out": Counter(), "hh": None, "age": None,
                                                      "rep": False, "leader": False, "laws": 0, "know": 0}))
    last_act, changes = {}, defaultdict(list)
    first_day = {}

    files = sorted(glob.glob(os.path.join(REC, "season_person", "season_person_*.jsonl")))
    for fp in files:
        with open(fp, encoding="utf-8") as f:
            for line in f:
                if not line.strip():
                    continue
                r = json.loads(line)
                if r.get("child"):
                    continue
                pid, end = r["person_id"], r["season_end_day"]
                y = end // YEAR
                yseas[y].add(end)
                dba = r.get("days_by_activity") or {}
                for a, d in dba.items():
                    yd[y][a] += d
                    yp[y][a].add(pid)
                if dba:
                    yadults[y].add(pid)
                c = pyear[pid][y]
                c["acts"].update(dba)
                if r.get("decided_by"):
                    c["dec"][r["decided_by"]] += 1
                for k in OUTS:
                    v = (r.get("outputs") or {}).get(k)
                    if isinstance(v, (int, float)) and v:
                        c["out"][k] += v
                c["hh"], c["age"] = r.get("household_id"), r.get("age")
                c["rep"] |= bool(r.get("is_rep"))
                c["leader"] |= bool(r.get("is_leader"))
                c["laws"] += len(((r.get("laws") or {}).get("proposed")) or [])
                c["know"] += r.get("knowledge_added") or 0
                first_day.setdefault(pid, r.get("present_from", end))
                # おもな仕事 (休むをのぞいて、いちばん日の多いもの) が変わったら経歴に書く
                work = {a: d for a, d in dba.items() if not a.startswith(REST_PREFIX)}
                if work:
                    main = max(work, key=lambda a: (work[a], a))
                    if last_act.get(pid) != main:
                        changes[pid].append({"day": r.get("present_from", end), "from": last_act.get(pid), "to": main,
                                             "by": r.get("decided_by"), "why": short(r.get("why"))})
                        last_act[pid] = main

    # ---- 時期ごとの仕事一覧
    years = sorted(yd)
    first_seen, last_seen, total = {}, {}, Counter()
    for y in years:
        for a, d in yd[y].items():
            first_seen.setdefault(a, y)
            last_seen[a] = y
            total[a] += d
    periods = []
    prev = set()
    for y in years:
        now = {a for a, d in yd[y].items() if d}
        worked = sum(d for a, d in yd[y].items() if not a.startswith(REST_PREFIX))
        jobs = [{"job": a, "days": d, "people": len(yp[y][a]),
                 "share": round(d / worked, 4) if worked and not a.startswith(REST_PREFIX) else None,
                 "new": a not in prev and y != years[0], "first": first_seen[a] == y}
                for a, d in sorted(yd[y].items(), key=lambda kv: -kv[1])]
        periods.append({"year": y, "name": ynames.get(y), "seasons": len(yseas[y]), "adults": len(yadults[y]), "worked": worked, "jobs": jobs,
                        "gone": sorted(prev - now)})
        prev = now
    jobs_all = [{"job": a, "first": first_seen[a], "last": last_seen[a], "total": total[a],
                 "peak": max(years, key=lambda y: yd[y].get(a, 0))} for a in sorted(total, key=lambda a: first_seen[a])]

    # ---- 一人ずつの職務経歴書
    cvs = []
    for pid, ys in pyear.items():
        p = people.get(pid, {})
        rows, acts_all, out_all, dec_all = [], Counter(), Counter(), Counter()
        for y in sorted(ys):
            c = ys[y]
            acts_all.update(c["acts"])
            out_all.update(c["out"])
            dec_all.update(c["dec"])
            rows.append({"y": y, "age": c["age"], "hh": hh.get(c["hh"], c["hh"]), "acts": dict(c["acts"].most_common()),
                         "rep": c["rep"], "leader": c["leader"], "laws": c["laws"], "know": c["know"],
                         "out": {k: round(v) for k, v in c["out"].items()}})
        ch = changes.get(pid, [])
        cvs.append({
            "id": pid, "name": p.get("name", pid), "sex": p.get("sex"), "born": p.get("born_day"), "origin": p.get("origin"),
            "came": p.get("came_day"), "died": p.get("died_day"), "cause": p.get("death_cause"), "age_death": p.get("age_at_death"),
            "left": p.get("left_day"), "left_why": p.get("left_why"), "status": p.get("status"),
            "hh": hh.get(p.get("household_id"), p.get("household_id")),
            "years": rows, "total": dict(acts_all.most_common()), "out": {k: round(v) for k, v in out_all.items()},
            "dec": dict(dec_all.most_common()),
            "changes": ch if len(ch) <= CHANGES_MAX else ch[:10] + [{"skip": len(ch) - CHANGES_MAX}] + ch[-(CHANGES_MAX - 10):],
        })
    cvs.sort(key=lambda c: (c["status"] != "生きている", -(c["years"][-1]["y"] if c["years"] else 0), c["name"]))

    data = {"year_days": YEAR, "season_days": world.SEASON_DAYS, "seasons": list(world.SEASONS), "season_start": world.SEASON_START, "first_year": years[0] if years else None, "last_year": years[-1] if years else None,
            "out_names": OUTS, "periods": periods, "jobs": jobs_all, "people": cvs}
    with open(OUT, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, separators=(",", ":"))
    return data


if __name__ == "__main__":
    d = build()
    print(f"{OUT} を書いた ({d['first_year']}〜{d['last_year']}年・仕事 {len(d['jobs'])} 種・{len(d['people'])} 人・"
          f"{os.path.getsize(OUT) // 1024} KB)")
