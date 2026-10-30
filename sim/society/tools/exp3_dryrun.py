"""論文 2・実験 3 の決まりの村での試し (トークン 0。docs/research/humanity/paper2_exp3_prereg.md の 8.)

  PYTHONUTF8=1 python3.13 sim/society/tools/exp3_dryrun.py --state /tmp/e3/s12599.json --years 3 [--arms off,A0,A1,A2]

- はじめの state (読むだけ。本物の 12599 日目なら `git show 726c5340:sim/society/data/state.json > /tmp/e3/s12599.json`) から、組ごとに
  同じ決まりの答え (tools/lab_village.py の束 B0「今の LLM に近い」) で years 年回す。lab_village と同じ回し方
  (集まりの歩は g7.apply_year、ない歩は g7.apply_plan → era2.simulate_season → g7.after_season → era2.check。止まるわけは消して続ける)。
- 集まりの歩ごとに、答える人みんなのお題を step.py と同じ道 (g7.year_prompt / era2.season_prompt → exp3.apply) で作り、確かめる:
  組なし・A0 のお題は 1 字も足さない / A1・A2 は節が「覚えていること」の前に 1 つずつ / 足した節を除くと、組なしのお題と同じ /
  足した節に禁じた言葉 (exp3.FORBIDDEN) がない / A1 の家の行の「村の蓄え 約 N 日分」が era2.store_days と同じ。
- 終わりに、組ごとの state の sha256 (g7.exp3 の鍵を除いて) をくらべる。答えが同じなら世界も同じ (お題のほかは何も変えない) はず。
- 写しの中だけ。ファイルは書かない (表示だけ)。
"""
import argparse
import copy
import hashlib
import json
import sys
import time
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path[:0] = [str(HERE.parent), str(HERE)]
import lab_village as L  # noqa: E402  (era2._feed・world._near の速さの差しかえも入る。どの組も同じ)
import era2  # noqa: E402
import exp3  # noqa: E402
import g7  # noqa: E402


def prompts(state):
    """step.write_prompts の季節のお題と同じ文 (名前: 文)。組を外したお題も返す"""
    first = g7.since(state)
    out = {}
    for n in era2.answerers(state):
        p = next(q for q in state["people"] if q["name"] == n)
        t = g7.year_prompt(state, p, first) if state["era2"]["g7"]["ask"] == "年" else era2.season_prompt(state, p, first)
        out[n] = (t, exp3.apply(state, p, t))
    return out


def check(state, arm, errs):
    ps = prompts(state)
    for n, (base, t) in ps.items():
        if arm in (None, "A0"):
            if t != base:
                errs.append(f"{state['day']} {n}: 組 {arm} なのにお題が変わった")
            continue
        heads = [h for h, part in ((exp3.LIFE_HEAD, "life"), (exp3.AROUND_HEAD, "around")) if part in exp3.ARMS[arm]]
        for h in heads:
            if t.count(h) != 1 or t.index(h) > t.index(exp3.ANCHOR):
                errs.append(f"{state['day']} {n}: 節「{h}」の数か場所がちがう")
        if exp3.strip(t) != base:
            errs.append(f"{state['day']} {n}: 足した節のほかが変わった")
        sec = t[base.index(exp3.ANCHOR):t.index(exp3.ANCHOR)]  # 足した節 (その前のお題は同じなので、そこから「覚えていること」まで)
        bad = [w for w in exp3.FORBIDDEN if w in sec]
        if bad:
            errs.append(f"{state['day']} {n}: 禁じた言葉 {bad}")
        if "life" in exp3.ARMS[arm] and f"約 {era2.store_days(state)} 日分" not in sec:
            errs.append(f"{state['day']} {n}: 村の蓄えの日数が合わない")
    return len(ps)


def run(state0, arm, years):
    state = copy.deepcopy(state0)
    if arm:
        exp3.set_arm(state, arm, "決まりの村の試し")
    g = state["era2"]["g7"]
    end_day = ((state["day"] + 1) // era2.YEAR + years) * era2.YEAR - 1
    rt, errs, n_prompts, meets = {}, [], 0, 0
    pol = L.BUNDLES["B0"]
    while state["day"] < end_day and any(p["alive"] for p in state["people"]):
        ask = g.get("ask")
        if ask:
            meets += 1
            n_prompts += check(state, arm, errs)
            g7.apply_year(state, L.make_answers(state, pol, rt), {})
        else:
            g7.apply_plan(state)
        first = era2.simulate_season(state)
        state["era2"]["last_first"] = first
        g7.after_season(state, first, bool(ask))
        r = era2.check(state)
        if r or state.get("hold"):
            state["hold"] = False
            g["hold"] = None
        if (state["day"] + 1) % era2.YEAR == 0:
            L.trim(state)
    st = copy.deepcopy(state)
    st["era2"]["g7"].pop("exp3", None)
    h = hashlib.sha256(json.dumps(st, ensure_ascii=False, separators=(",", ":"), sort_keys=True).encode()).hexdigest()
    return {"arm": arm or "off", "end_day": state["day"], "meetings": meets, "prompts": n_prompts, "errors": errs, "sha": h,
            "store_days": era2.store_days(state), "people": sum(p["alive"] for p in state["people"])}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--state", required=True)
    ap.add_argument("--years", type=int, default=3)
    ap.add_argument("--arms", default="off,A0,A1,A2")
    a = ap.parse_args()
    s0 = json.loads(Path(a.state).read_text(encoding="utf-8"))
    L.trim(s0)
    res = []
    for arm in a.arms.split(","):
        t0 = time.time()
        r = run(s0, None if arm == "off" else arm, a.years)
        r["secs"] = round(time.time() - t0)
        res.append(r)
        print(f"{r['arm']}: {r['end_day']} 日目まで・集まり {r['meetings']}・お題 {r['prompts']} 通・まちがい {len(r['errors'])}・人 {r['people']}・"
              f"蓄え {r['store_days']} 日分・state {r['sha'][:16]}… ({r['secs']} 秒)", flush=True)
        for e in r["errors"][:10]:
            print("   ", e)
    same = len({r["sha"] for r in res}) == 1
    print("どの組も、世界 (state。g7.exp3 の鍵のほか) は 1 バイトも同じ" if same else "組で世界がちがう (まちがい)")
    sys.exit(0 if same and not any(r["errors"] for r in res) else 1)


if __name__ == "__main__":
    main()
