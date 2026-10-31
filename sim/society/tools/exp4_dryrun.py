"""論文 2・実験 4 の決まりの村での試し (トークン 0。docs/research/humanity/paper2_exp4_prereg.md の 8.)

  PYTHONUTF8=1 python3.13 sim/society/tools/exp4_dryrun.py --state /tmp/e4/s12599.json --years 3 [--runs off,B0:none,B0:rule,B1:rule]

- はじめの state (読むだけ。本物の 12599 日目なら `git show 726c5340:sim/society/data/state.json > /tmp/e4/s12599.json`) から、
  実験 3 の exp3_dryrun.py と同じ回し方で years 年回す (答えは tools/lab_village.py の束 B0「今の LLM に近い」)。
- 走り (--runs) は「組:選びの決まり」。組は off (組なし) / B0 / B1。選びの決まり:
  none = みな「取らない」(組を入れても、だれも取らなければ、世界は組なしと 1 バイトも同じか (g7.exp4 の鍵のほか) を見る)
  rule = 決まりの選び (乱数なし。名前の数で決める): 家の倉がからっぽで村の蓄えが 60 日分より少ない → 村の蓄え /
         印のない、食べ物のあるよその家の倉があり、名前の数 (fnv) を 3 で割った余りが 0 → よその家の倉 / ほか → 取らない。
         取る道 (村の蓄え・よその家の倉・広げる・もめごと) がみな動くかを見るための決まりで、LLM の答えの見込みではない。
- 集まりの歩ごとに、答える人と気持ちの人のお題を step.py と同じ道で作り、確かめる: 組なしと同じ (足した節と欄を除いて) / 節は足りない家の人だけ /
  足した節に禁じた言葉 (exp3.FORBIDDEN) がない / 欄 take・take_why が答えの形にある / B1 は暮らしの節もある。
- 終わりに、走りごとの出来事の数 (選び・取った量・もめごと・裁き・亡くなった人・蓄え) と、state の sha256 (g7.exp4 の鍵を除いて) を出す。
- 写しの中だけ。ファイルは書かない (表示だけ)。
"""
import argparse
import copy
import hashlib
import json
import math
import sys
import time
from collections import Counter
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path[:0] = [str(HERE.parent), str(HERE)]
import lab_village as L  # noqa: E402  (era2._feed・world._near の速さの差しかえも入る。どの走りも同じ)
import era2  # noqa: E402
import exp3  # noqa: E402
import exp4  # noqa: E402
import g7  # noqa: E402


def fnv(s):
    x = 2166136261
    for ch in s:
        x = ((x ^ ord(ch)) * 16777619) & 0xFFFFFFFF
    return x


def rule_take(state, p):
    h = p["household"]
    if exp3._house_kcal(state, h) <= 0 and era2.store_days(state) < 60:
        return "村の蓄え"
    _, open_ = exp4._open_stores(state, h)
    if open_ and fnv(p["name"]) % 3 == 0:
        return "よその家の倉"
    return "取らない"


def check(state, arm, errs):
    """お題の確かめ。戻り値: (答える人のお題の数, 気持ちのお題の数, 節を足した数)"""
    first = g7.since(state)
    n_s = n_f = added = 0
    for n in era2.answerers(state):
        p = next(q for q in state["people"] if q["name"] == n)
        base = g7.year_prompt(state, p, first) if state["era2"]["g7"]["ask"] == "年" else era2.season_prompt(state, p, first)
        t = exp4.apply(state, p, base)
        n_s += 1
        if arm is None:
            if t != base:
                errs.append(f"{state['day']} {n}: 組なしなのにお題が変わった")
            continue
        if exp4.strip(t) != base:
            errs.append(f"{state['day']} {n}: 足した節と欄のほかが変わった")
        ask = exp4.asked(state, p)
        if ask != (exp4.HEAD in t) or ask != ('"take": "..."' in t):
            errs.append(f"{state['day']} {n}: 節と欄が、足りない家の人だけにない")
        if (arm == "B1") != (exp3.LIFE_HEAD in t):
            errs.append(f"{state['day']} {n}: 暮らしの節の有無がちがう")
        added += t != base
        sec = t[base.index(exp3.ANCHOR):t.index(exp3.ANCHOR)] if t != base else ""
        bad = [w for w in exp3.FORBIDDEN if w in sec]
        if bad:
            errs.append(f"{state['day']} {n}: 禁じた言葉 {bad}")
        if ask and f"約 {era2.store_days(state)} 日分" not in sec:
            errs.append(f"{state['day']} {n}: 村の蓄えの日数が合わない")
    for n in era2.feelers(state):
        p = next(q for q in state["people"] if q["name"] == n)
        base = era2.feeling_prompt(state, p, first)
        t = exp4.apply_feeling(state, p, base)
        n_f += 1
        if exp4.strip(t) != base:
            errs.append(f"{state['day']} {n} (気持ち): 足した節と欄のほかが変わった")
        if exp4.asked(state, p) != (exp4.HEAD in t):
            errs.append(f"{state['day']} {n} (気持ち): 節が、足りない家の人だけにない")
        added += t != base
        bad = [w for w in exp3.FORBIDDEN if w in t[t.find(exp4.HEAD):t.find(exp4.FEEL_ANCHOR)]] if t != base else []
        if bad:
            errs.append(f"{state['day']} {n} (気持ち): 禁じた言葉 {bad}")
    return n_s, n_f, added


def run(state0, arm, how, years):
    state = copy.deepcopy(state0)
    if arm:
        exp4.set_arm(state, arm, "決まりの村の試し")
    g = state["era2"]["g7"]
    end_day = ((state["day"] + 1) // era2.YEAR + years) * era2.YEAR - 1
    rt, errs, meets, n_s, n_f, n_add = {}, [], 0, 0, 0, 0
    kinds = Counter()
    pol = L.BUNDLES["B0"]
    store_min = era2.store_days(state)
    hungry = 0
    d0 = len([d for d in state["era2"]["g5"]["disputes"]])
    deaths0 = sum(1 for p in state["people"] if not p["alive"] and not p.get("left"))
    while state["day"] < end_day and any(p["alive"] for p in state["people"]):
        ask = g.get("ask")
        if ask:
            meets += 1
            kinds[ask] += 1
            a, b, c = check(state, arm, errs)
            n_s, n_f, n_add = n_s + a, n_f + b, n_add + c
            ans = L.make_answers(state, pol, rt)
            feels = {}
            if arm:
                by = {p["name"]: p for p in era2.adults(state)}
                for n in list(ans):
                    if exp4.asked(state, by[n]):
                        a_ = json.loads(ans[n])
                        a_["take"] = "取らない" if how == "none" else rule_take(state, by[n])
                        a_["take_why"] = "決まりの試し"
                        ans[n] = json.dumps(a_, ensure_ascii=False)
                for n in era2.feelers(state):
                    if exp4.asked(state, by[n]):
                        feels[n] = json.dumps({"feeling": "", "take": "取らない" if how == "none" else rule_take(state, by[n])}, ensure_ascii=False)
                exp4.read_choices(state, ans, feels)
            g7.apply_year(state, ans, {})
            exp4.spread(state)
        else:
            g7.apply_plan(state)
        first = era2.simulate_season(state)
        state["era2"]["last_first"] = first
        g7.after_season(state, first, bool(ask))
        exp4.season_end(state)
        store_min = min(store_min, era2.store_days(state))
        hungry = max(hungry, sum(1 for p in era2.adults(state) if p["hunger"] >= 0.3))
        r = era2.check(state)
        if r or state.get("hold"):
            state["hold"] = False
            g["hold"] = None
        if (state["day"] + 1) % era2.YEAR == 0:
            L.trim(state)
    st = copy.deepcopy(state)
    x = st["era2"]["g7"].pop("exp4", None)
    h = hashlib.sha256(json.dumps(st, ensure_ascii=False, separators=(",", ":"), sort_keys=True).encode()).hexdigest()
    ds = state["era2"]["g5"]["disputes"][d0:]
    out = {"run": f"{arm or 'off'}:{how}", "end_day": state["day"], "meetings": meets, "prompts": n_s, "feel_prompts": n_f, "added": n_add,
           "errors": errs, "sha": h, "store_days": era2.store_days(state), "store_min": store_min, "hungry_max": hungry,
           "people": sum(p["alive"] for p in state["people"]),
           "deaths": sum(1 for p in state["people"] if not p["alive"] and not p.get("left")) - deaths0,
           "disputes": dict(Counter(d["kind"] for d in ds)), "verdicts": dict(Counter(d.get("verdict") for d in ds if d.get("verdict"))),
           "steal_events": sum(1 for e in state["events"] if e["day"] > state0["day"] and e["type"] in ("倉から取る", "封")),
           "meeting_kinds": dict(kinds), "famine_breaks": sum(1 for e in state["events"] if e["day"] > state0["day"] and e["type"] == "蓄えが尽きる"),
           "left_people": sum(1 for p in state["people"] if p.get("left")) - sum(1 for p in state0["people"] if p.get("left")),
           "split_events": [e["text"][:80] for e in state["events"] if e["day"] > state0["day"] and e["type"] in ("分かれる", "去る")][:5],
           "penalty_laws": sum(1 for lw in state["laws"] if lw["status"] == "採用" and lw.get("penalty"))}
    if x:
        lg = x["log"]
        out["answers"] = len(lg)
        out["answers_by"] = dict(Counter(r["take"] for r in lg))
        kc = Counter()
        people_took = Counter()
        for s in x["acts"]:
            for n, row in s["rows"].items():
                for k in ("村の蓄え", "よその家の倉"):
                    if row.get(k):
                        kc[k] += row[k]
                        people_took[k] += 1
        out["took_kcal"] = {k: round(v) for k, v in kc.items()}
        out["took_grain"] = {k: int(v // era2.GRAIN) for k, v in kc.items()}
        out["took_person_seasons"] = dict(people_took)
        out["spread_person_seasons"] = sum(1 for s in x["acts"] for c in s["choice"].values() if c[1] != "自分")
        out["persons_asked"] = len({r["name"] for r in lg})
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--state", required=True)
    ap.add_argument("--years", type=int, default=3)
    ap.add_argument("--runs", default="off:-,B0:none,B0:rule,B1:rule")
    a = ap.parse_args()
    s0 = json.loads(Path(a.state).read_text(encoding="utf-8"))
    L.trim(s0)
    res = []
    for r_ in a.runs.split(","):
        arm, how = r_.split(":") if ":" in r_ else (r_, "-")
        t0 = time.time()
        r = run(s0, None if arm == "off" else arm, how, a.years)
        r["secs"] = round(time.time() - t0)
        res.append(r)
        print(json.dumps({k: v for k, v in r.items() if k != "errors"}, ensure_ascii=False), flush=True)
        print(f"   まちがい {len(r['errors'])}", flush=True)
        for e in r["errors"][:10]:
            print("   ", e)
    off = [r for r in res if r["run"].startswith("off")]
    none = [r for r in res if r["run"].endswith(":none")]
    if off and none:
        same = all(r["sha"] == off[0]["sha"] for r in none)
        print("だれも取らなければ、組を入れても世界 (state。g7.exp4 の鍵のほか) は組なしと 1 バイトも同じ" if same else "だれも取らないのに、世界がちがう (まちがい)")
    else:
        same = True
    sys.exit(0 if same and not any(r["errors"] for r in res) else 1)


if __name__ == "__main__":
    main()
