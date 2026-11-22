"""案 A (d1) の確かめ: 印を書いた写しの state を、決まりの答え (lab_village の束 S4B0) で 1 年回す (トークン 0。data にはさわらない)
  PYTHONUTF8=1 python3.13 sim/society/tools/lab_d1.py <state.json のあるフォルダ> <種> <out.json>
"""
import json
import sys
import time
from pathlib import Path

SOC = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(SOC))
sys.path.insert(0, str(SOC / "tools"))
import archive  # noqa: E402
import era2  # noqa: E402
import g7  # noqa: E402
import lab_village as LV  # noqa: E402

data, seed, out = sys.argv[1], int(sys.argv[2]), sys.argv[3]
t0 = time.time()
w, pol = LV.WORLDS["S3R"], LV.BUNDLES["S4B0"]
LV.apply_world(w)
state = json.loads((Path(data) / "state.json").read_text(encoding="utf-8"))
marked = "d1" in state["era2"]["g7"]
state["seed"] = state["seed"] + 1000 * seed
LV.enter_g7(state, w)
LV.trim(state)
y0 = (state["day"] + 1) // era2.YEAR
end_day = (y0 + 1) * era2.YEAR - 1
g = state["era2"]["g7"]
rt = {}
acc = {"births": 0, "kid_deaths": 0, "adult_deaths": 0, "old_deaths": 0, "sick_deaths": 0, "famine": 0}
seen = state["next_event"]
holds = []
while state["day"] < end_day:
    ask = g.get("ask")
    if ask:
        g7.apply_year(state, LV.make_answers(state, pol, rt), {})
    else:
        g7.apply_plan(state)
    first = era2.simulate_season(state)
    state["era2"]["last_first"] = first
    g7.after_season(state, first, bool(ask))
    r = era2.check(state)
    if r or state.get("hold"):
        holds.append((state["day"], (g.get("hold") or {}).get("what")))
        state["hold"] = False
        g["hold"] = None
    byname = {p["name"]: p for p in state["people"]}
    for e in archive.events_from(state, seen):
        t = e["type"]
        if t == "死":
            p = byname.get(e.get("who"))
            a = p["age"] if p else 0
            acc["kid_deaths" if a < 15 else "old_deaths" if a >= 55 else "adult_deaths"] += 1
            acc["sick_deaths"] += "病で" in e["text"]
        elif t == "生まれる":
            acc["births"] += 1
        elif t == "蓄えが尽きる":
            acc["famine"] += 1
    seen = state["next_event"]
    if (state["day"] + 1) % era2.YEAR == 0:
        LV.trim(state)
alive = [p for p in state["people"] if p["alive"]]
res = {"seed": seed, "marked": marked, "day": state["day"], "pop": len(alive), "old55": sum(1 for p in alive if p["age"] >= 55), **acc,
       "store_days": round(era2.store_days(state), 1), "holds": holds, "secs": round(time.time() - t0),
       "d1_rows": (g.get("d1") or {}).get("rows"), "consulted": [c for c in g.get("consulted", []) if str(c.get("why", "")).startswith("d1_")]}
Path(out).write_text(json.dumps(res, ensure_ascii=False, indent=1), encoding="utf-8")
print(json.dumps({k: v for k, v in res.items() if k != "d1_rows"}, ensure_ascii=False))
