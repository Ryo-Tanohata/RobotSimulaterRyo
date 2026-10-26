"""実験 A2: 村ごと (era2 の世界 + 地域) を、決まりの答えで回す (docs/research/state_emergence_plan.md 3.2。トークンは使わない。数はみな【シ】)

  PYTHONUTF8=1 python3.13 sim/society/tools/lab_village.py run --data /tmp/…/g6real --out /tmp/…/runs --seeds 4 --years 30 --procs 2
  PYTHONUTF8=1 python3.13 sim/society/tools/lab_village.py one --data /tmp/…/g6real --world W0 --bundle B0 --seed 1 --years 2   (1 回だけ。時間を見る)
  PYTHONUTF8=1 python3.13 sim/society/tools/lab_village.py csv --out /tmp/…/runs --csv docs/research/data/A2_runs.csv
  (G8 の重い押しの確かめ 2026-10-25: --data sim/society/data (本物の 10919 日目。読むだけ) --worlds W8H,W8R --years 10、csv に --years-csv で年ごとの行)

- はじめの state は G6 の 5849 日目 (e436dfc の 1 つ前のコミットの data の写し)。メモリの中で g7.close_g6 → g7.enter (G7 に入る。本物と同じ道) してから回す。
  写しの state.json は読むだけ。何も書かない (書くのは --out の結果のファイルだけ)
- 1 季節: 集まりの歩 (g7.ask がある) なら決まりの答えを作って g7.apply_year、ない歩は g7.apply_plan → era2.simulate_season → g7.after_season → era2.check
  (止まるわけ (相談・待ち) は、写しの中では止まらずに消して続ける)。step.py の記録・お題・書き出しはしない (速さのため)。気持ちの答えは作らない
- 古い出来事は、写しの中で archive.move と同じ決まりで捨てる (年のファイルには書かない。世界の仕組みが読む種類 archive.KEEP_TYPES は残す)
- 世界 (要因) は、このプロセスの中だけで region の数・関数を差しかえて作る (region.py・g7.py・era2.py は 1 字も変えない。tools/lab_region.py と同じ差しかえ方)
- 種: state["seed"] (era2._rng・地域の天気・戦の列のもと) を 7 (本物) から種ごとに変える。種 0 は本物と同じ列
- 方針の束 (計画 3.2 の表のつまみ。1 回の中では変えない) と世界は BUNDLES・WORLDS
"""
import argparse
import csv
import json
import math
import os
import pickle
import sys
import time
from multiprocessing import Pool
from pathlib import Path

import numpy as np

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent))
import archive  # noqa: E402
import era2  # noqa: E402
import g7  # noqa: E402
import region  # noqa: E402
import world  # noqa: E402

YEAR, SEASON_DAYS = era2.YEAR, era2.SEASON_DAYS
SEASONS = g7.SEASONS  # 夏・秋・冬・春

# ---------------- 世界 (計画 3.1 の要因のうち、A1 の途中の結果で効いていたもの) ----------------
WORLDS = {
    "W0": {"name": "G7 のまま", "fill": 0.1, "str": "base", "circ": "open", "dr": 0.2},
    "W1": {"name": "中間 (K の 30%・草原を砂地)", "fill": 0.3, "str": "base", "circ": "desert", "dr": 0.2},
    "W2": {"name": "国ができやすい (K の 30%・まわり 2 倍・砂地で逃げ場なし)", "fill": 0.3, "str": "x2", "circ": "nofl", "dr": 0.2},
    # 実験 C の世界 (2026-10-24): 本物の道の選び (g7.world = 砂地・逃げ場なし) と段の数え方 v2 を g7.enter に渡す (region の差しかえはしない)
    "WC": {"name": "C の世界 (G7 のまま + 草原を砂地 + 逃げ場なし。段は v2)", "fill": 0.1, "str": "base", "circ": "open", "dr": 0.2,
           "real": {"desert": True, "no_flee": True}, "count": "v2"},
    # G8 の世界 (2026-10-25): 本物の村の 8519 日目 (G7 を閉じたところ) から、step.py next_part --closed-by-decision と同じ道で G8 に入る
    "W8": {"name": "G8 (外からの押し: 強い集落・悪い年 0.35・砂地・逃げ場なし・段 v2)", "fill": 0.0, "str": "base", "circ": "open", "dr": 0.2, "g8": True},
    # G8 の続き「重い押し」(2026-10-25): 本物の村の G8 の state (10919 日目。年の集まりの歩で、まだ答えがない) から、そのまま回す (G に入りなおさない)。
    # W8H は step.py heavy on と同じ道 (g7.heavy_on) で重い押しを入れてから。W8R は入れない (くらべるため)
    "W8H": {"name": "G8 の重い押し (去年の刈り入れの 2 割。本物の 10919 日目から)", "fill": 0.0, "str": "base", "circ": "open", "dr": 0.2, "from_g8": True,
            "heavy": 0.2},
    "W8H10": {"name": "G8 の重い押し (去年の刈り入れの 10 割。本物の 10919 日目から。2026-10-26 本人の決め)", "fill": 0.0, "str": "base", "circ": "open",
              "dr": 0.2, "from_g8": True, "heavy": 1.0},
    "W8R": {"name": "G8 のまま (本物の 10919 日目から。重い押しなし)", "fill": 0.0, "str": "base", "circ": "open", "dr": 0.2, "from_g8": True},
}
ORIG = {"K": dict(region.K), "WEATHER_BAD": region.WEATHER_BAD, "cells": region.cells, "refuge": region.refuge, "k_total": region.k_total}


def _cells_desert():
    return [c for c in ORIG["cells"]() if region.land(c) != "s"]


def _no_refuge(setts, s, a):
    return None


def apply_world(w):
    """要因を region に当てる (はじめに、みなもとに戻す)。はじめに置く人数は、今の地図の K の割合のまま (lab_region.py と同じ)"""
    region.K = dict(ORIG["K"])
    region.WEATHER_BAD = float(w["dr"])
    region.cells = ORIG["cells"]
    region.refuge = ORIG["refuge"]
    region.k_total = ORIG["k_total"]
    if w["circ"] in ("desert", "nofl"):
        region.K["s"] = 0
        region.cells = _cells_desert
    if w["circ"] == "nofl":
        region.refuge = _no_refuge


def enter_g7(state, w):
    """G6 を閉じて G7 に入る (step.py next_part --closed-by-decision … --fill と同じ道)。まわり 2 倍は入ったあとに人と物を 2 倍"""
    k0 = ORIG["k_total"]()
    if w.get("from_g8"):  # もう G8 にいる state (本物の 10919 日目): 入りなおさない。重い押しは step.py heavy on と同じ関数で
        assert state.get("era") == "G8", state.get("era")
        if w.get("heavy"):
            g7.heavy_on(state, w["heavy"], answered=False)
        return
    if w.get("g8"):
        g7.close_g7(state, "G7 を閉じる (試し)")
        g7.enter_next(state)
        state["era_log"][-1]["g7_closed"] = state["day"]
        return
    g7.close_g6(state, "町は生まれなかったとして G6 を閉じる")
    if w.get("real") or w.get("count"):  # 本物の道 (step.py next_part --world … --count v2 と同じ)
        g7.enter(state, w["fill"], w.get("real"), w.get("count"))
        state["era_log"][-1]["g6_closed"] = state["day"]
        return
    region.k_total = lambda skip=(region.VILLAGE,): k0 if skip == (region.VILLAGE,) else ORIG["k_total"](skip)  # 置く人数は今の地図の K で
    try:
        g7.enter(state, w["fill"])
    finally:
        region.k_total = ORIG["k_total"]
    state["era_log"][-1]["g6_closed"] = state["day"]
    if w["str"] == "x2":
        for o in g7._others(state):
            for k in ("people", "goats", "grain", "pots", "sickles"):
                if isinstance(o.get(k), (int, float)):
                    o[k] = o[k] * 2


# ---------------- 方針の束 (計画 3.2) ----------------
# tax: none / famine (ききんのときだけ倉の 1 割。62年の案 L219 の形) / yearly (毎年 5%)
# rec: 記録の人 (季節ごとの人数。0 なら置かない)。what は残す種類の順
# judge: もめごとの収め方。pen: 罰 (倉・蓄え) と換算の掟を出して、みな賛成し、記録の人が板に書く
# dem: 村が求める (never / r15 = 1.5 倍強いときだけ / always = いつも。断られたら戦う)。ans: 求められたら (rule = 決まりの損のくらべ / pay = いつも払う)
# lead: まとめ役を選び、役の人 (守る) を大人の 1 割をこえるまで置く。loan: 「貸して」に村の物で 1 割の上乗せで答える (記録の人が残す)
BASE = {"tax": "none", "rec": 0, "what": [], "judge": "ゆるす", "pen": False, "dem": "never", "ans": "rule", "lead": False, "loan": False}
BUNDLES = {
    "B0": {"name": "G7 の LLM に近い", **BASE},
    "B1": {"name": "全部を国に寄せた", **BASE, "tax": "yearly", "rec": 2, "what": ["取り立て", "掟", "交換", "蓄え"], "judge": "つぐなう", "pen": True,
           "dem": "always", "ans": "pay", "lead": True, "loan": True},
    "B2": {"name": "税 + 記録", **BASE, "tax": "yearly", "rec": 2, "what": ["取り立て", "掟", "交換", "蓄え"]},
    "B3": {"name": "罰 + つぐなう", **BASE, "rec": 1, "what": ["掟"], "judge": "つぐなう", "pen": True},
    "B4": {"name": "求める", **BASE, "dem": "always"},
    "B5": {"name": "まとめ役と役の人", **BASE, "lead": True},
}
CKPT_YEARS = 3  # とちゅうの写しを書く間 (年)
POTTERS = 3  # どの束も、季節ごとに 3 人が土器づくり (草の種を虫から守る土器。63〜70年の答えに多かった形)
TAX_SHARE = {"famine": 0.1, "yearly": 0.05}
FAMINE_DAYS = 30  # ききんの税: 集まりの日に、村の蓄えと家の倉を合わせて 30 日分より少ないとき (G7 の Z4 と同じ数え方)
ROLE_SHARE = 0.12  # まとめ役の束: 役の人を大人の 12% (F6 の 1 割を少しこえる)
FIGHT_SHARE = 0.25  # 求めて断られたときに戦に出る人 (region.FIGHT_SHARE と同じ割合)
LAW_TEXT = {"tax": "家ごとに、年に 1 回、家の倉の草の種の一部を村の蓄えに出す", "倉": "よその家の倉から取って食べたら、その家に草の種を払う",
            "蓄え": "村の蓄えから、入れた量よりずっと多く取った家は、草の種を払う", "rate": "もめごとの払いでは、ヤギ 1 頭を草の種 300 つかみとみなす"}


def _job(act, **kw):
    return {"activity": act, "place": "camp", "with": [], **kw}


def _base(sea, famine=False):
    """季節ごとのふつうの仕事と、夕方の量 (63〜70年の答えの形: 夏は畑で刈り、秋は採集して 1 人 1,000 つかみまき、冬と春は草取り)"""
    if famine:  # 集まり直し (蓄えが尽きた): 食べ物を採る
        return _job("採集"), {"pick": 40, "plant": 0, "harvest": 60, "eat_goat": 0}
    if sea == "夏":
        return _job("畑仕事"), {"pick": 40, "plant": 0, "harvest": 60, "eat_goat": 0}
    if sea == "秋":
        return _job("採集"), {"pick": 40, "plant": 0, "harvest": 60, "eat_goat": 0, "sow": 1000}
    return _job("畑仕事"), {"pick": 0, "plant": 0, "harvest": 0, "eat_goat": 0}


def _our_laws(state):
    """この試しが出した掟 ({種類: 掟})。種類: tax・倉・蓄え・rate"""
    out = {}
    for l in state["laws"]:
        if l["status"] not in ("提案", "採用"):
            continue
        for k, t in LAW_TEXT.items():
            if l["text"].startswith(t):
                out.setdefault(k, l)
    return out


def _want_laws(pol):
    return (["tax"] if pol["tax"] != "none" else []) + (["倉", "蓄え", "rate"] if pol["pen"] else [])


def _proposal(kind, pol):
    p = {"text": LAW_TEXT[kind], "because": []}
    if kind == "tax":
        p["tax"] = {"what": "草の種", "share": TAX_SHARE[pol["tax"]]}
    elif kind in ("倉", "蓄え"):
        p["penalty"] = {"for": kind, "pay": 50}
    else:
        p["rate"] = {"ヤギ": 300}
    return p


def _people(state, names):
    """答える人ごとの家族 (年の順。代表でない答える人は自分だけ)"""
    reps = set(g7._rep_of(state).values())
    rep_mode = bool(state["era2"].get("rep_mode"))
    return {n: [q["name"] for q in era2.family(state, n)] if rep_mode and n in reps else [n] for n in names}


def _roles(state, pol, sea, rt, ask):
    """この季節の役の割り振り [(仕事, 人数, くわしい答え)]"""
    A = len(era2.adults(state))
    homes = era2._homes(state)
    out = [("土器づくり", POTTERS, {})]
    laws = _our_laws(state)
    if pol["rec"]:
        unwritten = [l["id"] for k, l in laws.items() if l["status"] == "採用" and not l.get("written") and k != "tax"]
        out.append(("記録をつける", pol["rec"], {"what": list(pol["what"]), "how": "板", **({"laws": unwritten} if unwritten else {})}))
    if "tax" in laws:  # 提案中でも (この集まりで、みな賛成して採用される)
        famine = g7._store_days_all(state) < FAMINE_DAYS
        if (pol["tax"] == "yearly" and sea == "夏") or (pol["tax"] == "famine" and famine and ask in ("集まり直し", "寄る", "秋", "年") and sea == season_now(state)):
            out.append(("取り立てる", math.ceil(len(homes) / 25), {}))
            rt["tax_seasons"] = rt.get("tax_seasons", 0) + 1
    if sea == "秋" and _war_pending(state):
        out.append(("戦に出る", math.ceil(FIGHT_SHARE * A), {}))
    if pol["lead"]:
        have = sum(n for a, n, _ in out if a in g7.ROLE_ACTS)
        need = math.ceil(ROLE_SHARE * A) - have
        if need > 0:
            out.append(("守る", need, {}))
    return out


def season_now(state):
    return world.season(state["day"] + 1)


def _war_pending(state):
    reg = (state["era2"]["g7"].get("region") or {})
    return any(w.get("att") == "V0" and not w.get("done") for w in reg.get("wars", []))


def _assign(fams, roles):
    """役を、答える家の家族に割り振る (代表でない大人から、家の順に。足りなければ代表も)。戻り値 {名前: 仕事}"""
    pool = [m for n, ms in fams.items() for m in ms[1:]] + [n for n in fams]
    out, i = {}, 0
    for act, k, extra in roles:
        for _ in range(k):
            if i >= len(pool):
                return out
            out[pool[i]] = _job(act, **extra)
            i += 1
    return out


def _season_part(state, pol, rt, n, ms, sea, roles, famine=False):
    job, extra = _base(sea, famine)
    fam = {m: dict(roles.get(m) or job) for m in ms[1:]}
    return {"job": dict(roles.get(n) or job), "family": fam, **extra}


def _demand(state, pol):
    """村が求める相手と量 (知っている村のうち、いちばん人の少ない村。r15 は村の人が 1.5 倍以上のときだけ)"""
    if pol["dem"] == "never":
        return None
    reg = state["era2"]["g7"].get("region") or {}
    busy = {t["payer"] for t in reg.get("ties", []) if t["payee"] == "V0" and t["status"] == "続く"}
    busy |= {d["to"] for d in reg.get("demands", []) if d.get("from") == "V0" and not d.get("end")}
    setts = {s["id"]: s for s in g7._setts(state)}
    v0 = setts.get("V0")
    cands = [o for o in g7._others(state) if o.get("known") is not None and o["id"] in setts and not setts[o["id"]].get("gone")
             and setts[o["id"]]["people"] > 0 and o["id"] not in busy]
    if not cands or not v0:
        return None
    t = min(cands, key=lambda o: (setts[o["id"]]["people"], region.num(o["id"])))
    s = setts[t["id"]]
    if pol["dem"] == "r15" and v0["people"] < 1.5 * s["people"]:
        return None
    amt = max(1, round(region.DEMAND_SHARE * region.surplus_pp(s) * s["people"]))
    return {"to": int(t["id"][1:]), "what": {"草の種": amt}, "then": "戦う"}


def make_answers(state, pol, rt):
    """集まりの歩の、答える人みんなの決まりの答え ({名前: JSON の文})"""
    g = state["era2"]["g7"]
    ask = g.get("ask")
    names = era2.answerers(state)
    if not names:
        return {}
    fams = _people(state, names)
    now = season_now(state)
    e2 = state["era2"]
    g5 = e2.get("g5") or {}
    open_d = [d["id"] for d in g5.get("disputes", []) if d["status"] == era2.OPEN]
    laws = _our_laws(state)
    pending = [l["id"] for l in laws.values() if l["status"] == "提案"]
    to_propose = [k for k in _want_laws(pol) if k not in laws]
    lead = None
    if pol["lead"]:
        cur = g5.get("leader")
        ads = era2.adults(state)
        lead = cur if any(p["name"] == cur for p in ads) else max(ads, key=lambda p: p["age"])["name"]
    dem = _demand(state, pol) if ask == "年" else None
    if dem:
        rt["demands"] = rt.get("demands", 0) + 1
    qs = [d["id"] for d in (g.get("region") or {}).get("demands", []) if d.get("to") == "V0" and not d.get("end")]
    common = {"judge": {d: pol["judge"] for d in open_d}, "judge_rule": pol["judge"],
              "votes": [{"id": i, "agree": True} for i in pending], "accept_rule": {"よその群れ": True, "ほかの村から": True},
              "accept": {v["name"]: True for v in e2.get("visitors", [])},
              "trade_rule": {"交換": None, "貸して": "村" if pol["loan"] else None, "max": None, "not": [], "利子": 0.1 if pol["loan"] else 0},
              "feast": [], "seal_store": []}
    if pol["loan"]:
        common["trade"] = {o["id"]: {"side": "村", "利子": 0.1} for o in (e2.get("g6") or {}).get("offers", []) if o["kind"] == "貸して"}
    if pol["ans"] == "pay" and qs:
        common["answer_demand"] = {q: "払う" for q in qs}
    if lead:
        common["leader"] = lead
    out = {}
    if ask == "年":
        seas = SEASONS[SEASONS.index(now):]
        plans = {s: _assign(fams, _roles(state, pol, s, rt, ask)) for s in seas}
        for i, n in enumerate(names):
            a = {"say": [], "year": {s: _season_part(state, pol, rt, n, fams[n], s, plans[s]) for s in seas}, **common}
            if i < len(to_propose):
                a["proposal"] = _proposal(to_propose[i], pol)
            if dem:
                a["demand"] = dem
            out[n] = json.dumps(a, ensure_ascii=False)
    else:
        famine = ask == "集まり直し"
        roles = _assign(fams, _roles(state, pol, now, rt, ask))
        for i, n in enumerate(names):
            a = {"say": [], **_season_part(state, pol, rt, n, fams[n], now, roles, famine), **common}
            if i < len(to_propose):
                a["proposal"] = _proposal(to_propose[i], pol)
            out[n] = json.dumps(a, ensure_ascii=False)
    return out


# ---------------- 速さのため: 蓄えの切れをまとめる (写しの中だけ) ----------------
# 時間の 9 割は、子と大人が 1 人ずつ村の蓄え (1 万 2 千切れ) を腐る日の順に並べなおす所 (world._move_food)。物・採った日・印 (sown・dry) が同じ切れは
# 腐る日も同じなので、1 つにまとめても量は同じ (5849 日目の写しで 12,365 切れ → 362)。食べる順が変わるのは、腐る日が同じで印だけちがう切れのあいだだけ
# (草の種の sown は「食べた量のうち育てたもの」の数にだけ効く)。毎日、食べる前 (era2._feed の前) にまとめる

def merge(store):
    if len(store) < 2:
        return
    out, at = [], {}
    for f in store:
        k = (f["kind"], f["day"], bool(f.get("sown")), bool(f.get("dry")))
        i = at.get(k)
        if i is None:
            at[k] = len(out)
            out.append(dict(f))
        else:
            out[i]["kcal"] += f["kcal"]
    store[:] = out


_FEED = era2._feed


def _feed_merged(state, rng):
    merge(state["store"])
    for h in (state["era2"].get("house") or {}).values():
        merge(h["store"])
    return _FEED(state, rng)


era2._feed = _feed_merged


# 速さのため (2): 植えた木 (state["plants"]。1 万 8 千本。ふえるだけで、動かず、消えない) から近くを探す world._near を、numpy の配列で引く。
# 返すもの・並び (plants の並びの順) は前と同じ。動くもの (群れ・けもの) と短い並びは前のまま
_NEAR, _ARR = world._near, {}


def _near_np(items, x, y, r):
    if len(items) < 2000:
        return _NEAR(items, x, y, r)
    c = _ARR.get(id(items))
    n = len(items)
    if c is None or c["items"] is not items or n < c["n"] or items[c["n"] - 1] is not c["last"]:
        c = _ARR[id(items)] = {"items": items, "n": 0, "last": None, "x": np.zeros(0, dtype=np.int64), "y": np.zeros(0, dtype=np.int64)}
    if n > c["n"]:
        new = items[c["n"]:]
        c["x"] = np.concatenate([c["x"], np.fromiter((i["x"] for i in new), dtype=np.int64, count=len(new))])
        c["y"] = np.concatenate([c["y"], np.fromiter((i["y"] for i in new), dtype=np.int64, count=len(new))])
        c["n"], c["last"] = n, items[-1]
    dx, dy = c["x"] - x, c["y"] - y
    idx = np.flatnonzero((dx >= -r) & (dx <= r) & (dy >= -r) & (dy <= r))
    return [items[i] for i in idx.tolist()]


world._near = _near_np


# ---------------- 写しの中で古い記録を捨てる (archive.move と同じ切り方。ファイルには書かない) ----------------

def trim(state):
    a = state.get("archive")
    a = json.loads(json.dumps(a)) if a else {"v": archive.V, "upto": -1, "event": 0, "n": {k: 0 for k in archive.KINDS}}
    upto, base, last = a["upto"], a["event"], archive.last_year(state)
    if last <= upto:
        return
    cut = (last + 1) * YEAR
    ev = state["events"]
    kept = [e for e in ev if e["id"] < base]
    rest = [e for e in ev if e["id"] >= base]
    i = archive._head(rest, cut)
    moved, rest = rest[:i], rest[i:]
    state["events"] = kept + [e for e in moved if e["type"] in archive.KEEP_TYPES] + rest
    for k in archive.LISTS:
        xs = state.get(k)
        if xs:
            state[k] = xs[archive._head(xs, cut):]
    for law in state.get("laws", []):
        vl = law.get("vote_log")
        if vl:
            law["vote_log"] = vl[archive._head(vl, cut):]
    a["upto"], a["event"] = last, base + len(moved)
    state["archive"] = a


# ---------------- 1 回 ----------------

def _year_row(state, y0, acc):
    g, e2, D = state["era2"]["g7"], state["era2"], state["day"]
    alive = [p for p in state["people"] if p["alive"]]
    lv = g.get("levels_now") or {}
    w = era2.wealth(state)
    laws = _our_laws(state)
    reg = g.get("region") or {}
    return {"year": (D + 1) // YEAR - y0, "day": D, "pop": len(alive), "adults": sum(1 for p in alive if not p.get("child")),
            "homes": len(era2._homes(state)), "store_days": round(era2.store_days(state), 1), "store_all_days": round(g7._store_days_all(state), 1),
            "gini": round(era2.gini(list(w.values())), 3) if w else None, "vD": lv.get("D", 0), "region_max": lv.get("region_max", 0),
            "village": lv.get("village"), "reached": dict(g.get("reached") or {}), "tribute2_day": g.get("tribute2_day"),
            "tribute_ok": sum(1 for t in g.get("tribute_years", []) if t["ok"]), "judged": len(g.get("judged") or []),
            "role_share": (g.get("role_log") or [{}])[-1].get("role", 0) / max(1, (g.get("role_log") or [{}])[-1].get("adults", 1)),
            "f6_run": g.get("f6_run", 0), "laws": {k: {"status": l["status"], "written": bool(l.get("written"))} for k, l in laws.items()},
            "leader": (e2.get("g5") or {}).get("leader"), "ties_in": sum(1 for t in reg.get("ties", []) if t["payee"] == "V0" and t["status"] == "続く"),
            "ties_out": sum(1 for t in reg.get("ties", []) if t["payer"] == "V0" and t["status"] == "続く"),
            "region3": (g.get("level_seen") or {}).get("region3"),
            # 村に来た求めの答え (払う・戦う・助けを頼む・まだ) と、村がかかわった戦 (G8 の確かめ)
            "dem_in_ans": _count(str(d.get("answer") or "まだ") + ("" if d.get("from") != g.get("strong") else "@強") for d in reg.get("demands", []) if d.get("to") == "V0"),
            "dem_in_strong": sum(1 for d in reg.get("demands", []) if d.get("to") == "V0" and d.get("from") == g.get("strong")),
            "wars_v0": sum(1 for x in reg.get("wars", []) if "V0" in (x.get("att"), x.get("def")) and x.get("done") is not None and not x.get("called_off")),
            "strong_people": next((o["people"] for o in g7._others(state) if o["id"] == g.get("strong")), None),
            **_heavy_cols(state),
            **{k: acc[k] for k in sorted(acc)}}


def _heavy_cols(state):
    """重い押しの確かめ (2026-10-25) の年ごとの列: 村の蓄え (村の土器) と家の倉 (日数と草の種)・その年の刈り入れ・強い集落への貢ぎの量・強い集落からの求めの答え"""
    g, e2 = state["era2"]["g7"], state["era2"]
    reg = g.get("region") or {}
    need = max(1, era2._need(state))
    v_kc = math.fsum(f["kcal"] for f in state["store"])
    h_kc = math.fsum(f["kcal"] for h in sorted(e2.get("house", {})) for f in e2["house"][h].get("store", []))
    tie = next((t for t in reg.get("ties", []) if t["payer"] == "V0" and t["payee"] == g.get("strong") and t["status"] == "続く"), None)
    return {"v_days": round(v_kc / need, 1), "h_days": round(h_kc / need, 1), "v_grain": era2._g6_have(state, "村", "草の種"),
            "h_grain": sum(era2._g6_have(state, h, "草の種") for h in sorted(era2._homes(state))), "harvest": g7.harvest_year(state),
            "tie_strong": tie["goods"].get("草の種", 0) if tie else 0, "tie_heavy": bool(tie and tie.get("heavy")),
            "strong_dem": [[d["id"], d["day"], d["what"].get("草の種"), d.get("answer"), d.get("how"), d.get("result"), bool(d.get("raise"))]
                           for d in reg.get("demands", []) if d.get("to") == "V0" and d.get("from") == g.get("strong")],
            "wars_list": [[x["id"], x["att"], x["def"], x.get("done"), x.get("att_win"), (x.get("dead") or {}).get("V0")]
                          for x in reg.get("wars", []) if "V0" in (x.get("att"), x.get("def"))]}


def _count(xs):
    out = {}
    for x in xs:
        out[x] = out.get(x, 0) + 1
    return out


def _boot():
    try:
        return Path("/proc/sys/kernel/random/boot_id").read_text().strip()
    except OSError:
        return "?"


def _lock(dst):
    """同じ回を 2 つの掃き出しが回さないための札 (入れ物が止まって残った札は、boot_id か pid がちがえば古いとみなす)"""
    lk = dst.with_suffix(".lock")
    me = f"{_boot()} {os.getpid()}"
    for _ in range(2):
        try:
            fd = os.open(lk, os.O_CREAT | os.O_EXCL | os.O_WRONLY)
        except FileExistsError:
            try:
                boot, pid = lk.read_text().split()
                alive = boot == _boot() and Path(f"/proc/{pid}").exists()
            except (OSError, ValueError):
                alive = False
            if alive:
                return False
            lk.unlink(missing_ok=True)
            continue
        os.write(fd, me.encode())
        os.close(fd)
        return True
    return False


def run_one(job):
    wid, bid, seed, years, data, out = job
    dst = Path(out) / f"{wid}_{bid}_s{seed}.json"
    if dst.exists() or not _lock(dst):
        return str(dst) + (" (済み)" if dst.exists() else " (ほかの組が回している)")
    t0 = time.time()
    w, pol = WORLDS[wid], BUNDLES[bid]
    apply_world(w)
    ck = dst.with_suffix(".ckpt.pkl")  # とちゅうの写し (入れ物が止まっても、ここから続ける。終わったら消す)
    if ck.exists():
        with open(ck, "rb") as f:
            state, rows, acc, rt, seen_events, fis0, y0, end_day, spent = pickle.load(f)
        t0 -= spent
    else:
        state = json.loads((Path(data) / "state.json").read_text(encoding="utf-8"))
        state["seed"] = state["seed"] + 1000 * seed
        enter_g7(state, w)
        trim(state)
        y0 = (state["day"] + 1) // YEAR  # 入った年 (短い年。この年の終わりが 0 年目の終わり)
        end_day = (y0 + years) * YEAR - 1
        rt, rows = {}, []
        acc = {k: 0 for k in ("kid_deaths", "adult_deaths", "births", "left_people", "fissions", "famine_events", "famine_seasons", "meetings", "remeet",
                              "wars", "demands_in", "tax_coll", "shares", "paid_out", "famine_all_seasons")}
        seen_events = state["next_event"]
        fis0 = len((state["era2"].get("g5") or {}).get("fissions", []))
    g = state["era2"]["g7"]
    while state["day"] < end_day:
        if not any(p["alive"] for p in state["people"]):
            break
        ask = g.get("ask")
        if ask:
            acc["meetings"] += 1
            acc["remeet"] += ask == "集まり直し"
            g7.apply_year(state, make_answers(state, pol, rt), {})
        else:
            g7.apply_plan(state)
        first = era2.simulate_season(state)
        state["era2"]["last_first"] = first
        g7.after_season(state, first, bool(ask))
        r = era2.check(state)
        if r or state.get("hold"):  # 写しの中では止まらない (相談・待ちを消して続ける)
            state["hold"] = False
            g["hold"] = None
        byname = {p["name"]: p for p in state["people"]}
        for e in archive.events_from(state, seen_events):
            t = e["type"]
            if t == "死":
                p = byname.get(e.get("who"))
                acc["kid_deaths" if p and p.get("child") else "adult_deaths"] += 1
            elif t == "生まれる":
                acc["births"] += 1
            elif t == "去る":
                acc["left_people"] += 1
            elif t == "蓄えが尽きる":
                acc["famine_events"] += 1
            elif t == "戦":
                acc["wars"] += 1
            elif t == "取り立て":
                acc["tax_coll"] += 1
            elif t == "貢ぎ" and (e.get("data") or {}).get("amount") and str(e.get("text", "")).startswith(g7.V0_NAME + " が "):
                acc["paid_out"] = acc.get("paid_out", 0) + e["data"]["amount"]
            elif t == "求め" and "V0" in str((e.get("data") or {}).get("who", "")):
                pass
        seen_events = state["next_event"]
        if era2.store_days(state) < 1:
            acc["famine_seasons"] += 1
        if g7._store_days_all(state) < 1:  # 家の倉もふくめて 1 日分を切った季節 (重い押しの確かめ)
            acc["famine_all_seasons"] = acc.get("famine_all_seasons", 0) + 1
        acc["fissions"] = len((state["era2"].get("g5") or {}).get("fissions", [])) - fis0
        acc["demands_in"] = sum(1 for d in (g.get("region") or {}).get("demands", []) if d.get("to") == "V0")
        if (state["day"] + 1) % YEAR == 0:
            rows.append(_year_row(state, y0, acc))
            trim(state)
            if len(rows) % CKPT_YEARS == 0 and state["day"] < end_day:
                tmp = ck.with_suffix(".tmp")
                with open(tmp, "wb") as f:
                    pickle.dump((state, rows, acc, rt, seen_events, fis0, y0, end_day, time.time() - t0), f, protocol=pickle.HIGHEST_PROTOCOL)
                os.replace(tmp, ck)
    res = {"world": wid, "bundle": bid, "seed": seed, "years": years, "secs": round(time.time() - t0, 1), "rt": rt, "y0": y0, "start": g["start"],
           "full_first": bool(w.get("from_g8")),  # 1 行目から まる 1 年 (入った短い年がない)
           "rows": rows, "end_day": state["day"], "all_dead": not any(p["alive"] for p in state["people"])}
    tmp = dst.with_suffix(".tmp")
    tmp.write_text(json.dumps(res, ensure_ascii=False), encoding="utf-8")
    os.replace(tmp, dst)
    ck.unlink(missing_ok=True)
    dst.with_suffix(".lock").unlink(missing_ok=True)
    return str(dst)


# ---------------- 結果の表 ----------------
FS = ("F1", "F2", "F3", "F4", "F5", "F6")
COLS = ["world", "bundle", "seed", "years_run", "c1_year", "c2_year", "c3_year"] + [f"{f}_year" for f in FS] + \
    ["region3_year", "vD_max", "region_max", "pop_end", "adults_end", "homes_end", "kid_deaths", "adult_deaths", "births", "left_people", "fissions",
     "famine_seasons", "famine_events", "remeet", "wars", "demands_out", "demands_in", "ties_in_end", "ties_out_end", "tax_coll", "tax_seasons",
     "tribute_ok_years", "judged", "laws_adopted", "laws_written", "leader_end", "role_share_max", "gini_end", "store_all_days_end", "all_dead", "truncated_from", "secs"]


def row_of(res):
    rows = res["rows"]
    last = rows[-1] if rows else {}
    y0 = res["y0"]

    def yr(day):
        return None if day is None else day // YEAR - y0 + 1  # 入った年 (短い年) を 0 年目として、その日が何年目か (0 年目 = 1 未満は 0)

    re = last.get("reached") or {}
    laws = last.get("laws") or {}
    out = {"world": res["world"], "bundle": res["bundle"], "seed": res["seed"], "years_run": (len(rows) - (0 if res.get("full_first") else 1)) if rows else 0,
           "c1_year": yr(re.get("F3")), "c2_year": yr(last.get("tribute2_day")), "c3_year": yr(re.get("F4")),
           **{f"{f}_year": yr(re.get(f)) for f in FS}, "region3_year": yr(last.get("region3")),
           "vD_max": max((r["vD"] for r in rows), default=0), "region_max": max((r["region_max"] for r in rows), default=0),
           "pop_end": last.get("pop"), "adults_end": last.get("adults"), "homes_end": last.get("homes"),
           **{k: last.get(k) for k in ("kid_deaths", "adult_deaths", "births", "left_people", "fissions", "famine_seasons", "famine_events", "remeet",
                                       "wars", "demands_in", "tax_coll")},
           # rt は回の合計 (年ごとでない)。30 年で回して 15 年に切った回 (truncated_from) は数えられないので空
           "demands_out": res["rt"].get("demands", 0) if res.get("rt") is not None else None,
           "tax_seasons": res["rt"].get("tax_seasons", 0) if res.get("rt") is not None else None,
           "ties_in_end": last.get("ties_in"), "ties_out_end": last.get("ties_out"), "tribute_ok_years": last.get("tribute_ok"), "judged": last.get("judged"),
           "laws_adopted": sum(1 for v in laws.values() if v["status"] == "採用"), "laws_written": sum(1 for v in laws.values() if v["written"]),
           "leader_end": bool(last.get("leader")), "role_share_max": round(max((r["role_share"] for r in rows), default=0), 3),
           "gini_end": last.get("gini"), "store_all_days_end": last.get("store_all_days"), "all_dead": res["all_dead"], "truncated_from": res.get("truncated_from"), "secs": res["secs"]}
    for f in ("c1_year", "c2_year", "c3_year", "region3_year") + tuple(f"{f}_year" for f in FS):
        if out[f] is not None:
            out[f] = max(0, out[f])
    return out


YEAR_COLS = ["world", "bundle", "seed", "year", "day", "pop", "adults", "homes", "harvest", "tie_strong", "tie_heavy", "paid_out_year", "v_grain", "h_grain",
             "v_days", "h_days", "store_all_days", "famine_seasons_year", "famine_all_seasons_year", "kid_deaths_year", "adult_deaths_year", "births_year",
             "fissions_year", "left_people_year", "wars_v0", "dem_strong", "vD", "gini"]


def write_years_csv(out_dir, path):
    """年ごとの行 (重い押しの確かめ。2026-10-25): 1 回 × 1 年 = 1 行。_year の列は、その年の分 (前の年の行との差)"""
    out = []
    for f in sorted(Path(out_dir).glob("*.json")):
        res = json.loads(f.read_text(encoding="utf-8"))
        prev = {}
        for r in res["rows"]:
            d = {k: r.get(k, 0) - prev.get(k, 0) for k in ("paid_out", "famine_seasons", "famine_all_seasons", "kid_deaths", "adult_deaths", "births",
                                                          "fissions", "left_people")}
            prev = r
            out.append({"world": res["world"], "bundle": res["bundle"], "seed": res["seed"], **{k: r.get(k) for k in YEAR_COLS if k in r},
                        **{f"{k}_year": v for k, v in d.items()}, "dem_strong": ";".join("/".join(str(x) for x in q) for q in r.get("strong_dem", []))})
    out.sort(key=lambda r: (r["world"], r["bundle"], r["seed"], r["year"]))
    with open(path, "w", encoding="utf-8", newline="") as fh:
        wr = csv.DictWriter(fh, fieldnames=YEAR_COLS, extrasaction="ignore")
        wr.writeheader()
        for r in out:
            wr.writerow(r)
    return out


def write_csv(out_dir, path):
    rows = [row_of(json.loads(f.read_text(encoding="utf-8"))) for f in sorted(Path(out_dir).glob("*.json"))]
    rows.sort(key=lambda r: (r["world"], r["bundle"], r["seed"]))
    Path(path).parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", encoding="utf-8", newline="") as f:
        wr = csv.DictWriter(f, fieldnames=COLS)
        wr.writeheader()
        for r in rows:
            wr.writerow(r)
    return rows


def _wilson(k, n, z=1.96):
    if n == 0:
        return None, None
    ph = k / n
    d = 1 + z * z / n
    c = (ph + z * z / (2 * n)) / d
    h = z * math.sqrt(ph * (1 - ph) / n + z * z / (4 * n * n)) / d
    return max(0.0, c - h), min(1.0, c + h)


def _med(xs):
    xs = sorted(x for x in xs if x is not None)
    if not xs:
        return None
    m = len(xs) // 2
    return xs[m] if len(xs) % 2 else (xs[m - 1] + xs[m]) / 2


def summary(rows):
    """組 (世界 × 束) ごとの表 (markdown)"""
    keys = [("c1_year", "c1"), ("c2_year", "c2"), ("c3_year", "c3")] + [(f"{f}_year", f) for f in FS] + [("region3_year", "地域に段 3")]
    out = []
    groups = {}
    for r in rows:
        groups.setdefault((r["world"], r["bundle"]), []).append(r)
    head = "| 世界 | 束 | 回 | " + " | ".join(lab for _, lab in keys) + " |"
    out += ["### 届いた回 / 回 (届いた年の真ん中。1 年目 = G7 に入った短い年 (48年の春の 1 季節)。15 年目の終わり = 62年の終わり)", "", head, "|" + "---|" * (3 + len(keys))]
    for (w, b), rs in sorted(groups.items()):
        cells = []
        for k, _ in keys:
            hit = [r[k] for r in rs if r[k] not in (None, "")]
            cells.append(f"{len(hit)}/{len(rs)}" + (f" ({_med([int(x) for x in hit]):g})" if hit else ""))
        out.append(f"| {w} | {b} {BUNDLES[b]['name']} | {len(rs)} | " + " | ".join(cells) + " |")
    out += ["", "### 続くか (15 年目の終わり。回の平均。[ ] は最小〜最大)", "",
            "| 世界 | 束 | 人 | 大人 | 家 | 亡くなった子 | 亡くなった大人 | 生まれた | 村を出た家 | 蓄えが 1 日分を切った季節 | 蓄えが尽きた | 戦 | 村が受ける貢ぎ | 村が出す貢ぎ | 取り立て | 裁いて払わせた | 持ち物のジニ | 蓄え (家の倉もふくむ日数) |",
            "|" + "---|" * 18]

    def av(rs, k, nd=0):
        xs = [float(r[k]) for r in rs if r[k] not in (None, "")]
        if not xs:
            return "-"
        m = sum(xs) / len(xs)
        return (f"{m:.{nd}f} [{min(xs):.{nd}f}〜{max(xs):.{nd}f}]")
    for (w, b), rs in sorted(groups.items()):
        out.append(f"| {w} | {b} | " + " | ".join(av(rs, k, 2 if k == "gini_end" else 0) for k in (
            "pop_end", "adults_end", "homes_end", "kid_deaths", "adult_deaths", "births", "fissions", "famine_seasons", "famine_events", "wars",
            "ties_in_end", "ties_out_end", "tax_coll", "judged", "gini_end", "store_all_days_end")) + " |")
    return "\n".join(out)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("cmd", choices=("run", "one", "csv"))
    ap.add_argument("--data")
    ap.add_argument("--out")
    ap.add_argument("--csv")
    ap.add_argument("--years-csv", dest="years_csv", help="csv で、年ごとの行も書く (重い押しの確かめ)")
    ap.add_argument("--world", default="W0")
    ap.add_argument("--bundle", default="B0")
    ap.add_argument("--worlds", default=",".join(WORLDS))
    ap.add_argument("--bundles", default=",".join(BUNDLES))
    ap.add_argument("--seed", type=int, default=1)
    ap.add_argument("--seeds", type=int, default=4)
    ap.add_argument("--years", type=int, default=15)
    ap.add_argument("--procs", type=int, default=2)
    a = ap.parse_args()
    if a.cmd == "csv":
        rows = write_csv(a.out, a.csv)
        print(f"{len(rows)} 行 → {a.csv}")
        if a.years_csv:
            print(f"{len(write_years_csv(a.out, a.years_csv))} 行 → {a.years_csv}")
        print(summary(rows))
        return
    Path(a.out).mkdir(parents=True, exist_ok=True)
    if a.cmd == "one":
        print(run_one((a.world, a.bundle, a.seed, a.years, a.data, a.out)))
        return
    jobs = [(w, b, s, a.years, a.data, a.out) for s in range(1, a.seeds + 1) for b in a.bundles.split(",") for w in a.worlds.split(",")]
    t0 = time.time()
    with Pool(a.procs, maxtasksperchild=1) as pool:
        for i, f in enumerate(pool.imap_unordered(run_one, jobs), 1):
            print(f"{i}/{len(jobs)} {Path(f).name} {(time.time() - t0) / 60:.1f} 分", flush=True)


if __name__ == "__main__":
    main()
