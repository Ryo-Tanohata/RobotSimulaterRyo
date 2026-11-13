#!/usr/bin/env python3
"""川辺の村の年報 (1 年に 1 枚の HTML)。本人にスマホで見てもらう、やさしい日本語のページを作る。

使い方:
  python3.13 sim/society/tools/year_report.py --data sim/society/data --year 119 [--tokens 6123456] [--decide "決めてほしいこと"] \
      --out sim/society/reports/year119.html

  --data    state.json と records/ のあるフォルダ (読むだけ。何も書かない)
  --year    年 (Y年 = 通しの日 Y*120 〜 Y*120+119。118年120日目 = 14279 日目)
  --tokens  この 1 年に使ったトークンの数 (あれば見出しに出す)
  --decide  本人に決めてほしいこと (なければ「なし」と出す)
  --no-tech テクノロジーの節を作らない (テクノロジーツリーの計算に 20 秒ほどかかるので、急ぐとき)
  --out     書く HTML のファイル。sim/society/data/ の下には書かない

読むもの: data/state.json (しまった年の出来事は data/archive/ から)・data/records/ (season_village.jsonl・people.json・laws.json・snapshots/)・
  techtree/ (tools/build_tech_tree.py の build をそのまま使う)。G9・G10・G11 の条件の数え方は g9.py・g10.py・g11.py の決まり (目標の数) をそのまま使う。
出すもの: 1 つの HTML (CSS も図も中に入れる。外のファイルを読まない)。
出さないもの: 村の会計・貸借対照表・持ち物の差 (ジニ係数)・接地度・答えた人の数・よその便りの札の番号と史実の出どころなど、【シ】の帳簿の数。
  (ダッシュボードとちがい、本人むけの報告なので、人の名前・年齢・人数・条件の物差しは出す。)
"""
import argparse
import html
import json
import os
import re
import sys
import time
from pathlib import Path

HERE = os.path.dirname(os.path.abspath(__file__))
SOC = os.path.dirname(HERE)
sys.path.insert(0, SOC)
sys.path.insert(0, HERE)
import archive  # noqa: E402
import era2  # noqa: E402
import g9 as G9  # noqa: E402
import g10 as G10  # noqa: E402
import g11 as G11  # noqa: E402
import g12 as G12  # noqa: E402  (読むのは数の決まりだけ。state は変えない)
import g13 as G13  # noqa: E402  (読むのは数の決まりだけ。state は変えない)
import records  # noqa: E402

YEAR = era2.YEAR
PROTECTED = os.path.realpath(os.path.join(SOC, "data"))
SEASONS = ("夏", "秋", "冬", "春")
DEATH_WORD = {"病": "病気で", "子": "小さいうちに", "年": "年をとって", "ザガ": "ザガ (村をおそう獣) におそわれて", "飢え": "飢えて"}
yd = records.day_label  # 通しの日 → 「118年120日目」


# ---------------------------------------------------------------- 読む

def _json(p, tries=5):
    """読むだけ。ワークフローが書いている最中なら少し待って読み直す"""
    for i in range(tries):
        try:
            return json.loads(Path(p).read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            if i == tries - 1:
                raise
            time.sleep(2)


def _jsonl(p):
    if not Path(p).exists():
        return []
    with open(p, encoding="utf-8") as fh:
        return [json.loads(x) for x in fh if x.strip()]


def year_list(state, data, kind, y):
    """その年の events / knowledge_log。しまった年は data/archive/ のファイル (その年が全部そろう) から読む"""
    up = (state.get("archive") or {}).get("upto")
    if up is not None and y <= up:
        return archive._read(archive.path(data, kind, y))
    lo, hi = y * YEAR, y * YEAR + YEAR - 1
    return [x for x in state.get(kind, []) if lo <= x.get("day", -1) <= hi]


def snap_end(data, y):
    """その年の最後の季節の終わりの控え (なければ None)"""
    rows = _jsonl(records.snap_path(data, y * YEAR + YEAR - 1))
    rows = [r for r in rows if r.get("day", -1) // YEAR == y]
    return max(rows, key=lambda r: r["day"]) if rows else None


def load(data, y):
    data = Path(data)
    st = _json(data / "state.json")
    sv = _jsonl(data / "records" / "season_village.jsonl")
    by_year = {}
    for r in sv:
        by_year.setdefault(r["year"], []).append(r)
    people = {p["id"]: p for p in _json(data / "records" / "people.json")}
    laws = _json(data / "records" / "laws.json")
    return {"state": st, "data": data, "seasons": by_year, "people": people, "laws": laws,
            "events": year_list(st, data, "events", y), "knowledge": year_list(st, data, "knowledge_log", y),
            "snap": snap_end(data, y), "snap_prev": snap_end(data, y - 1)}


# ---------------------------------------------------------------- 数える

def phase_of_year(D, y):
    rows = D["seasons"].get(y, [])
    eras = [r.get("era_end") or r.get("era") for r in rows if r.get("era_end") or r.get("era")]  # era は季節のはじめ、era_end は季節の終わりのフェーズ
    if eras:
        return max(set(eras), key=lambda e: (eras.count(e), eras.index(e)))
    log = D["state"].get("era_log") or []
    lo = y * YEAR
    cur = None
    for x in log:
        if x["day"] <= lo:
            cur = x["era"]
    return cur or D["state"].get("era")


def people_part(D, y):
    rows = sorted(D["seasons"].get(y, []), key=lambda r: r["season_end_day"])
    prev = sorted(D["seasons"].get(y - 1, []), key=lambda r: r["season_end_day"])
    P = D["people"]
    births, deaths, joined, left = [], [], [], []
    for r in rows:
        births += r.get("births") or []
        deaths += [d["id"] for d in r.get("deaths") or []]
        joined += r.get("joined") or []
        left += r.get("left") or []
    end, start = (rows[-1] if rows else None), (prev[-1] if prev else None)
    dl = []
    for pid in deaths:
        p = P.get(pid) or {}
        dl.append({"name": p.get("name", pid), "age": p.get("age_at_death"), "cause": p.get("death_cause"), "day": p.get("died_day")})
    harvest = sum((r.get("fields") or {}).get("harvested") or 0 for r in rows)
    sown = sum((r.get("fields") or {}).get("seed") or 0 for r in rows)
    return {"rows": rows, "start": start, "end": end, "births": births, "deaths": dl, "joined": joined, "left": left,
            "harvest": harvest, "sown": sown, "complete": len(rows) == 4 and rows[-1]["season_end_day"] == y * YEAR + YEAR - 1}


def pop_history(D, y, n=10):
    out = []
    for yy in range(y - n, y + 1):
        rows = sorted(D["seasons"].get(yy, []), key=lambda r: r["season_end_day"])
        if rows:
            out.append({"year": yy, "adults": rows[-1]["adults"], "children": rows[-1]["children"], "population": rows[-1]["population"]})
    return out


def ind(snap):
    return ((snap or {}).get("era_info") or {}).get("indicators") or {}


def _g7(st):
    return (st.get("era2") or {}).get("g7") or {}


def g9_data(st):
    """G9 の帳簿: G9 のあいだは g7.g9、G10 に入ったあとは閉じたときの写し (g7.closed9) と g7.before.G9.g9"""
    g7 = _g7(st)
    live = g7.get("g9") or {}
    closed = g7.get("closed9") or {}
    before = ((g7.get("before") or {}).get("G9") or {}).get("g9") or {}
    used = dict(live.get("used") or {})
    used.update(closed.get("used") or {})
    # G10 に入ったあとも G9 の物差しは「ならべて測る」ので、g7.g9 の c・reached は入った日に空にしてから数え直している。
    # G9 のあいだの値は、閉じたときの写しから読む (なければ、いまの値)
    c = dict(before.get("c") or {}) or dict(closed.get("c") or {}) or dict(live.get("c") or {})
    reached = dict(before.get("reached") or {}) or dict(closed.get("reached") or {}) or dict(live.get("reached") or {})
    return {"used": used, "c": c, "reached": reached, "closed": closed}


def g10_data(st):
    """G10 の帳簿: G11 に入ったあとは g7.g10 の c・path を入った日に空にして数え直している (ならべて測る) ので、
    G10 のあいだの c・reached・道の見張りは、入った日の写し (g7.before.G10.g10) から読む (なければ、いまの値)"""
    live = _g7(st).get("g10") or {}
    before = ((_g7(st).get("before") or {}).get("G10") or {}).get("g10")
    if not before:
        return live
    g = dict(live)
    g["c"], g["reached"] = dict(before.get("c") or {}), dict(before.get("reached") or {})
    g["path"] = {**(live.get("path") or {}), **(before.get("path") or {})}
    return g


def _g11_law(st, key, end):
    """その年の終わりまでに決まっていた掟 (key のあるもの) のうち、いちばん新しいもの"""
    return next((l for l in reversed(st.get("laws", [])) if l.get("status") == "採用" and l.get(key) and (l.get("day") or 0) <= end), None)


def _g11_year(g, st, y):
    """y 年の G11 の数 (g11.season_end・g11.progress と同じ数え方を、その年の帳簿から)"""
    end = y * YEAR + YEAR - 1
    on = (lambda d: d is not None and d <= end)
    ys = str(y)
    row = (g.get("flows") or {}).get(ys) or {"all": 0, "coin": 0}
    mk = (g.get("markets") or {}).get(ys) or []
    deals = sum(1 for r in mk if r["deals"] > 0)  # g11.markets_with_deals
    run = 0
    while ((g.get("credit") or {}).get(str(y - run)) or {}).get("written", 0) >= 1:
        run += 1
    rch = g.get("reached") or {}
    mark = g.get("mark") if g.get("mark") and on(g["mark"].get("day")) else None
    md = _g11_law(st, "market_day", end)
    vf = g.get("market_day")  # 2026-11-06 直し ① (g11.G11_FIX_FROM から): 年の集まりで決めた市の日 (掟より新しければ、こちら。g11.market_day と同じ)
    if vf and vf["day"] <= end and (not md or vf["day"] >= (md.get("changed") or md.get("day") or 0)):
        md = {"market_day": vf["n"]}
    begun = g.get("start") is not None and g["start"] <= end
    s1 = 4 if on(rch.get("F3")) else 3 if on(rch.get("F1")) else 2 if mark else 1 if begun else 0
    s2 = 2 if on(rch.get("F2")) else 1 if md else 0
    s3 = 2 if on(rch.get("F4")) else 1 if on(rch.get("F3")) else 0
    return {"row": row, "mk": mk, "deals": deals, "run": run, "mark": mark, "md": md["market_day"] if md else None,
            "prog": {"c1": (s1, round(1000 * row["coin"] / row["all"]) if row["all"] else 0), "c2": (s2, deals), "c3": (s3, run)}}


def _bar(label, value, goal, unit, done_day, note="", y_end=None):
    hit = done_day is not None and (y_end is None or done_day <= y_end)
    return {"label": label, "value": value, "goal": goal, "unit": unit, "done": hit, "done_day": done_day if hit else None, "note": note}


def conditions(D, y, phase):
    """条件ごとの進み (棒) と F の目盛りと、去年からの動き (+1 近づいた / 0 同じ / -1 遠のいた)"""
    st, I, Ip = D["state"], ind(D["snap"]), ind(D["snap_prev"])
    end = y * YEAR + YEAR - 1
    out = {"phase": phase, "bars": [], "fs": [], "moves": {}, "extra": [], "path": None}
    if phase == "G9":
        g = g9_data(st)
        u, up = g["used"].get(str(y), I.get("g9_used_year", 0)), g["used"].get(str(y - 1), 0)
        tm, tmp = I.get("g9_trip_days_max", 0), Ip.get("g9_trip_days_max", 0)
        wr, wrp = I.get("g9_written", 0), Ip.get("g9_written", 0)
        out["bars"] = [
            _bar("条件 1 赤い金属 (青銅) の道具を使う", u, G9.C1_DAYS, "人日", g["c"].get("c1"),
                 f"この年に赤い金属の道具で刈った、のべの日数。目標は 1 年に {G9.C1_DAYS} 人日", end),
            _bar("条件 2 商人の家", tm, G9.MERCHANT_DAYS + 1, "日", g["c"].get("c2"),
                 f"1 年に交換に出かけた日がいちばん多い家の日数。目標は {G9.MERCHANT_DAYS} 日をこえる家が 1 つ", end),
            _bar("条件 3 遠くとの約束を書く", wr, 1, "回", g["c"].get("c3"), "遠くの町の運ぶ人との約束を粘土の板に書いた回数", end)]
        out["moves"] = {"c1": (u > up) - (u < up), "c2": (tm > tmp) - (tm < tmp), "c3": (wr > wrp) - (wr < wrp)}
        out["fs"] = [(k, v, g["reached"].get(k) if (g["reached"].get(k) or end + 1) <= end else None) for k, v in G9.FS.items()]
        out["extra"] = [f"赤い金属の道具: {I.get('g9_tools', '?')} 本 / 遠くの町の運ぶ人が来た回数 (はじめから): {I.get('g9_far_visits', '?')} 回 / "
                        f"約束: {I.get('g9_promises', 0)} 回 (書いたのは {wr} 回)"]
        if (g["closed"] or {}).get("day") is not None and g["closed"]["day"] <= end and g["closed"]["day"] >= y * YEAR:
            out["extra"].append(f"G9 は {yd(g['closed']['day'])} に、本人の決めで閉じた (条件 2・3 は届かないまま)")
    elif phase == "G10":
        g = g10_data(st)
        row = (g.get("reap") or {}).get(str(y)) or {"all": I.get("g10_reap_all", 0), "iron": I.get("g10_reap_iron", 0), "bronze": I.get("g10_reap_bronze", 0)}
        rowp = (g.get("reap") or {}).get(str(y - 1)) or {"all": 0, "iron": 0}
        goal1 = max(G10.C1_MIN, -(-row["all"] * G10.C1_SHARE // 1))
        share = (row["iron"] / row["all"]) if row["all"] else 0
        orr, orp = I.get("g10_outside_readers", 0), Ip.get("g10_outside_readers", 0)
        md, mem = I.get("g10_region_maxD", 0), I.get("g10_region_members", 0)
        mdp, memp = Ip.get("g10_region_maxD", 0), Ip.get("g10_region_members", 0)
        reg = g.get("region") or {}
        n = reg.get("settlements") if reg.get("day") == end else None
        if n is None:
            last = (D["seasons"].get(y) or [{}])[-1]
            k = (last.get("g7") or {}).get("settlements")  # 記録の数は、よその集落だけ。g10 は村もふくめて数える (g7._setts)
            n = (k + 1) if k is not None else (reg.get("settlements") or 0)
        made_y = sum(1 for m in g.get("made") or [] if m["day"] // YEAR == y)
        cs = g.get("c") or {}
        out["bars"] = [
            _bar("条件 1 黒い金属の道具を使う", row["iron"], int(goal1), "人日", cs.get("c1"),
                 f"刈った人日 {row['all']} のうち、村で作った黒い金属の鎌で刈ったのは {row['iron']} ({round(share * 100)}%)。"
                 f"目標は半分以上で、少なくとも {G10.C1_MIN} 人日", end),
            _bar("条件 2 字を読み書きできる人", orr, G10.C2_READERS, "人", cs.get("c2"),
                 f"記録をつける家の外で、字を読み書きできる大人の数 (読み書きできる大人はぜんぶで {I.get('g10_readers', 0)} 人)", end),
            _bar("条件 3 広いまとまり (段)", md, G10.C3_D, "段", cs.get("c3"),
                 f"地域でいちばん深いまとまりの決める段。目標は {G10.C3_D} 段以上", end),
            _bar("条件 3 広いまとまり (集落の数)", mem, max(1, int(-(-n * G10.C3_SHARE // 1))) if n else 1, "集落", cs.get("c3"),
                 f"そのまとまりに入る集落の数。目標は地域の集落 {n} (村もふくむ) の半分以上。段と集落の数の両方がそろうと届く", end)]
        out["moves"] = {"c1": (row["iron"] > rowp["iron"]) - (row["iron"] < rowp["iron"]), "c2": (orr > orp) - (orr < orp),
                        "c3": ((md, mem) > (mdp, memp)) - ((md, mem) < (mdp, memp))}
        rch = g.get("reached") or {}
        out["fs"] = [(k, v, rch.get(k) if (rch.get(k) or end + 1) <= end else None) for k, v in G10.FS.items()]
        out["extra"] = [f"村で作った黒い金属の鎌: この年 {made_y} 本 (はじめから {I.get('g10_iron_made', len(g.get('made') or []))} 本・いま使えるのは {I.get('g10_iron_tools', 0)} 本)"
                        + (f" / 字で書いて量を比べた回数 (はじめから): {I.get('g10_letters')} 回" if I.get("g10_letters") else "")]
        p = (g.get("path") or {}).get(str(y))
        cons = [c for c in (_g7(st).get("consulted") or []) if str(c.get("why", "")).startswith("path_") and c.get("year") == y]
        out["path"] = {"row": p, "consult": cons, "start": g.get("start")}
    elif phase == "G11":
        g = _g7(st).get("g11") or {}
        Y, P = _g11_year(g, st, y), _g11_year(g, st, y - 1)
        row, cs = Y["row"], g.get("c") or {}
        goal1 = max(G11.C1_MIN, int(-(-row["all"] * G11.C1_SHARE // 1)))
        cr = (g.get("credit") or {}).get(str(y)) or {"coin": 0, "written": 0}
        out["bars"] = [
            _bar("条件 1 印のかたまりで払う", row["coin"], goal1, "回", cs.get("c1"),
                 f"この年の、よその集落との出し入れ {row['all']} 回のうち、印のかたまりで払ったか受けたのは {row['coin']} 回。"
                 f"目標は半分以上で、少なくとも {G11.C1_MIN} 回", end),
            _bar("条件 2 市の日", Y["deals"], G11.C2_MARKETS, "回", cs.get("c2"),
                 (f"掟の市の日 (季節ごとの {Y['md']} 日目) に、よその集落の人が来て替えた市の数" if Y["md"] else "市の日はまだ掟で決まっていない")
                 + f" (去年 {P['deals']} 回)。目標は 1 年 {G11.C2_MARKETS} 回以上を {G11.C2_YEARS} 年つづける", end),
            _bar("条件 3 印のかたまりで貸し、字で書く", Y["run"], G11.C3_YEARS, "年", cs.get("c3"),
                 f"よその村への貸し・返しを印のかたまりでして、量を字で書いた年が、つづいた数 (この年: 印でした貸し・返し {cr.get('coin', 0)} 回、"
                 f"字で書いたのは {cr.get('written', 0)} 回)。目標は {G11.C3_YEARS} 年つづける", end)]
        out["moves"] = {k: (Y["prog"][k] > P["prog"][k]) - (Y["prog"][k] < P["prog"][k]) for k in ("c1", "c2", "c3")}
        rch = g.get("reached") or {}
        out["fs"] = [(k, v, rch.get(k) if (rch.get(k) or end + 1) <= end else None) for k, v in G11.FS.items()]
        out["g11"] = g11_lines(g, st, y, Y)
        p = (g.get("path") or {}).get(str(y))
        cons = [c for c in (_g7(st).get("consulted") or []) if str(c.get("why", "")).startswith("g11_path_") and c.get("year") == y]
        out["path"] = {"row": p, "consult": cons, "start": g.get("start"), "g": "G11"}
    elif phase == "G12":
        g = _g7(st).get("g12") or {}
        ys, ysp = str(y), str(y - 1)
        cs = g.get("c") or {}
        paid = (g.get("paid") or {}).get(ys) or {}
        n_paid = sum(1 for v in paid.values() if v == "出した")
        c1y = [x for x in g.get("c1_years") or [] if x <= y]
        rel, relp = (g.get("relief") or {}).get(ys) or {}, (g.get("relief") or {}).get(ysp) or {}
        cen = (g.get("census") or {}).get(ys) or {}
        run = 0
        while ((g.get("census") or {}).get(str(y - run)) or {}).get("done"):
            run += 1
        led = next((r for r in g.get("ledger") or [] if r.get("year") == y), {})
        out["bars"] = [
            _bar("条件 1 倉の約束の輪 (約束どおり出した村)", n_paid, G12.C1_MIN, "村", cs.get("c1"),
                 f"この年の終わりに、倉の約束どおり村に出した集落の数 (約束 {led.get('pacts', '?')})。目標は {G12.C1_MIN} つ以上の年が {G12.C1_TIMES} 回 "
                 f"(届いた年: {'・'.join(map(str, c1y)) or 'まだ'})", end),
            _bar("条件 2 倉から地域を養う (集落)", len(rel), G12.C2_SETTLEMENTS, "集落", cs.get("c2"),
                 f"この年に村の倉から出した先の集落の数 (去年 {len(relp)})。目標は 1 年に {G12.C2_SETTLEMENTS} 集落以上で、合わせて {G12.C2_AMOUNT} つかみ以上", end),
            _bar("条件 2 倉から地域を養う (量)", sum(rel.values()), G12.C2_AMOUNT, "つかみ", cs.get("c2"),
                 f"この年に村の倉から出した量 (草の種のつかみにしたねうち。去年 {sum(relp.values())})", end),
            _bar("条件 3 人と倉の帳", run, G12.C3_YEARS, "年", cs.get("c3"),
                 f"家の人の数・村の倉・倉の約束を字で書いた帳がそろった年が、つづいた数 (この年 {len(cen.get('houses', []))} 家を書いた"
                 + ("・そろった" if cen.get("done") else "") + f")。目標は {G12.C3_YEARS} 年つづける", end)]
        pv = sum(1 for v in ((g.get("paid") or {}).get(ysp) or {}).values() if v == "出した")
        out["moves"] = {"c1": (n_paid > pv) - (n_paid < pv), "c2": (sum(rel.values()) > sum(relp.values())) - (sum(rel.values()) < sum(relp.values())),
                        "c3": (bool(cen.get("done")) - bool(((g.get("census") or {}).get(ysp) or {}).get("done")))}
        rch = g.get("reached") or {}
        out["fs"] = [(k, v, rch.get(k) if (rch.get(k) or end + 1) <= end else None) for k, v in G12.FS.items()]
        out["g12"] = g12_lines(g, st, y, led)
        p = (g.get("path") or {}).get(str(y))
        cons = [c for c in (_g7(st).get("consulted") or []) if str(c.get("why", "")).startswith("g12_path_") and c.get("year") == y]
        out["path"] = {"row": p, "consult": cons, "start": g.get("start"), "g": "G12"}
    elif phase == "G13":
        g = _g7(st).get("g13") or {}
        ys, ysp = str(y), str(y - 1)
        cs = g.get("c") or {}
        my, myp = (g.get("mill") or {}).get("year", {}).get(ys) or {}, (g.get("mill") or {}).get("year", {}).get(ysp) or {}
        share = (my.get("milled", 0) / my["need"]) if my.get("need") else 0
        wa, wap = (g.get("water") or {}).get(ys) or {}, (g.get("water") or {}).get(ysp) or {}
        wf = round(100 * wa.get("water", 0) / wa["sown"]) if wa.get("sown") else 0
        wfp = round(100 * wap.get("water", 0) / wap["sown"]) if wap.get("sown") else 0
        run = 0
        while (y - run) in (g.get("c2_years") or []):
            run += 1
        c3 = (g.get("c3_rows") or {}).get(ys) or {}
        c3p = (g.get("c3_rows") or {}).get(ysp) or {}
        c3y = [x for x in g.get("c3_years") or [] if x <= y]
        led = next((r for r in g.get("ledger") or [] if r.get("year") == y), {})
        out["bars"] = [
            _bar("条件 1 水の力の粉ひき (回った日)", my.get("days", 0), G13.C1_DAYS, "日", cs.get("c1"),
                 f"この年に村の水の輪が回った日 (水の輪 {led.get('mills', '?')}・回っている {led.get('mills_running', '?')})。"
                 f"目標は 1 年に {G13.C1_DAYS} 日以上回り、村の粉ひきの半分以上を引き受ける", end),
            _bar("条件 1 水の力の粉ひき (粉の割合)", round(100 * share), round(100 * G13.C1_SHARE), "%", cs.get("c1"),
                 f"この年に村の人が食べた粉のうち、水の輪がひいた割合 (去年 {round(100 * myp['milled'] / myp['need']) if myp.get('need') else 0}%)", end),
            _bar("条件 2 水の来る畑", wf, round(100 * G13.C2_SHARE), "%", cs.get("c2"),
                 f"この年の秋にまいた草の種 {wa.get('sown', 0)} つかみのうち、水の来る畑にまいた割合 (去年 {wfp}%。半分以上の年が、いま {run} 年つづいている)。"
                 f"目標は半分以上の年が {G13.C2_YEARS} 年つづく", end),
            _bar("条件 3 務め (出した集落)", c3.get("paid", 0), max(1, -(-c3.get("settlements", 0) * 1 // 2)) if c3 else 1, "集落", cs.get("c3"),
                 f"この年の終わりに、村に約束の分か働き手を出した集落 (地域の集落 {c3.get('settlements', '?')})。目標は半分以上の年が {G13.C3_TIMES} 回 "
                 f"(届いた年: {'・'.join(map(str, c3y)) or 'まだ'})", end)]
        out["moves"] = {"c1": (my.get("days", 0) > myp.get("days", 0)) - (my.get("days", 0) < myp.get("days", 0)), "c2": (wf > wfp) - (wf < wfp),
                        "c3": (c3.get("paid", 0) > c3p.get("paid", 0)) - (c3.get("paid", 0) < c3p.get("paid", 0))}
        rch = g.get("reached") or {}
        out["fs"] = [(k, v, rch.get(k) if (rch.get(k) or end + 1) <= end else None) for k, v in G13.FS.items()]
        out["g13"] = g13_lines(g, st, y, led)
        p = (g.get("path") or {}).get(str(y))
        cons = [c for c in (_g7(st).get("consulted") or []) if str(c.get("why", "")).startswith("g13_path_") and c.get("year") == y]
        out["path"] = {"row": p, "consult": cons, "start": g.get("start"), "g": "G13"}
    else:
        out["extra"] = [f"この年のフェーズ {phase} の条件の棒は、まだ作っていない。条件: {(st.get('era_info') or {}).get('next', '-')}"]
    return out


def g11_lines(g, st, y, Y):
    """G11 のこの年のようす (やさしい日本語の箇条)"""
    lo, end = y * YEAR, y * YEAR + YEAR - 1
    out = []
    m = Y["mark"]
    out.append(f"村の印: 「{m['text']}」 ({yd(m['day'])}に、集まりで決めた)" if m else "村の印: まだ決まっていない (決まるまでの印のかたまりは、払いに使えない)")
    pay, red = g.get("pay") or {}, g.get("redeem") or {}
    pc = pay.get("choice", "物") if (pay.get("day") or 0) <= end else "物"
    rc = red.get("choice", "引きかえる") if (red.get("day") or 0) <= end else "引きかえる"
    out.append(f"払い方: 村の物で払うときは「{pc}」で払う" + (" (まだ印のかたまりで払うとは決めていない)" if pc == "物" else "")
               + f"。よその村が持って来た印のかたまりは「{rc}」と決めている")
    led = next((r for r in g.get("ledger") or [] if r.get("year") == y), None)
    made_y = sum(r["n"] for r in g.get("made") or [] if lo <= r["day"] <= end)
    made_all = sum(r["n"] for r in g.get("made") or [] if r["day"] <= end)
    if led:
        have = f"年の終わりに村に {led['village']} 個" + (f" (印のないもの {led['unmarked']} 個)" if led.get("unmarked") else "") + \
               f"・よその村に {sum((led.get('others') or {}).values())} 個。作れる人 {led.get('smiths', 0)} 人"
    else:
        c = g.get("coins") or {}
        have = f"いま村に {c.get('village', 0)} 個・よその村に {sum((c.get('others') or {}).values())} 個"
    out.append(f"印のかたまりを作った数: この年 {made_y} 個 (はじめから {made_all} 個)。{have}")
    mk = Y["mk"]
    if Y["md"]:
        came = sum(1 for r in mk if r["came"])
        out.append(f"市: 季節ごとの {Y['md']} 日目が市の日。この年の市 {len(mk)} 回 (よその人が来た {came} 回・替えた {Y['deals']} 回)"
                   + ("" if g.get("market") else "。市の方針 (何を出し、何を受けるか) はまだない"))
    else:
        out.append("市: 市の日はまだ掟で決まっていないので、この年は市が立たなかった")
    fl = [f for f in g.get("flow_log") or [] if lo <= f["day"] <= end]
    row = Y["row"]
    t = f"よその集落との出し入れ: この年 {row['all']} 回 (印のかたまりで {row['coin']} 回・物で {row['all'] - row['coin']} 回)"
    if fl:
        kinds = {}
        for f in fl:
            k = kinds.setdefault(f["kind"], [0, 0])
            k[0] += 1
            k[1] += f["coin"]
        t += "。" + "・".join(f"{k} {a} 回" + (f" (印 {n} 個)" if n else "") for k, (a, n) in kinds.items())
    out.append(t)
    cr = (g.get("credit") or {}).get(str(y)) or {}
    out.append(f"印のかたまりの貸し・返し: この年 {cr.get('coin', 0)} 回 (字で書いたのは {cr.get('written', 0)} 回)" if cr.get("coin") else
               "印のかたまりの貸し・返し: この年はなかった")
    ref = [d for d in g.get("refused") or [] if lo <= d <= end]
    fa = [f for f in g.get("fails") or [] if f.get("year") == y]  # g11.fails_year
    if ref or fa:
        t = (f"引きかえを断った・できなかった: {len(ref)} 回。" if ref else "") + (f"選んだのにできなかったこと {len(fa)} 回: " + " / ".join(clean(f["why"], 60) for f in fa[:3]) if fa else "")
        out.append(t)
    else:
        out.append("断ったこと・選んだのにできなかったこと: なかった")
    return out


def g12_lines(g, st, y, led):
    """G12 のこの年のようす (やさしい日本語の箇条)"""
    lo, end = y * YEAR, y * YEAR + YEAR - 1
    out = []
    pacts = g.get("pacts") or {}
    made = [p for p in pacts.values() if lo <= p["day"] <= end]
    ended = [p for p in pacts.values() if p.get("end") is not None and lo <= p["end"] <= end]
    alive = [p for p in pacts.values() if p["day"] <= end and (p.get("end") is None or p["end"] > end)]
    out.append(f"倉の約束: 年の終わりに {len(alive)} 村 (この年に結んだ {len(made)}・切れた {len(ended)})"
               + ("。切れたわけ: " + " / ".join(clean(p.get("why") or "", 60) for p in ended[:3]) if ended else ""))
    paid = (g.get("paid") or {}).get(str(y)) or {}
    if paid:
        kinds = {}
        for v in paid.values():
            kinds[v] = kinds.get(v, 0) + 1
        out.append("年の終わりの約束の出し入れ: " + "・".join(f"{k} {n} 村" for k, n in kinds.items()))
    rl = [r for r in g.get("relief_log") or [] if lo <= r["day"] <= end]
    if rl:
        gr = sum(r["goods"].get("草の種", 0) for r in rl)
        out.append(f"倉から出した: {len(rl)} 回・{len({r['other'] for r in rl})} 集落・草の種 {gr} つかみ"
                   + (f"・ヤギ {sum(r['goods'].get('ヤギ', 0) for r in rl)} 頭" if any(r['goods'].get('ヤギ') for r in rl) else "")
                   + (f"・黒い金属の鎌 {sum(r['goods'].get(G12.IRON, 0) for r in rl)} 本" if any(r['goods'].get(G12.IRON) for r in rl) else ""))
    else:
        out.append("倉から出した: この年はなかった")
    hd = (g.get("hands") or {}).get(str(y)) or {}
    if hd:
        out.append(f"刈り手: のべ {hd.get('days', 0)} 人日が来て、草の種 {hd.get('grain', 0)} つかみを刈った (村の蓄えから {hd.get('ate', 0)} つかみを食べた)")
    cen = (g.get("census") or {}).get(str(y)) or {}
    out.append(f"帳: {len(cen.get('houses', []))} 家を書いた (のべ {cen.get('days', 0)} 日。書いた人 {'・'.join(sorted(cen.get('by') or {})) or 'いない'})"
               + ("。この年の帳はそろった" if cen.get("done") else "") if cen else "帳: この年はだれも帳をつけなかった")
    if led:
        out.append(f"ならべて測るもの: 都の大きさ (村の人 ÷ 地域の人) {round(100 * led.get('city', 0))}% / 虫やネズミに食べられた 約 {led.get('pests', 0)} つかみ / "
                   f"刈らずに落ちた 約 {led.get('fallen', 0)} つかみ / ヤギ {led.get('goats', '?')} 頭 / 読める大人 {led.get('readers', '?')} 人")
    fa = [f for f in g.get("fails") or [] if f.get("year") == y]
    out.append(f"受けなかった・減らした・切れた・休んだ: {len(fa)} 回" + (": " + " / ".join(clean(f["why"], 60) for f in fa[:3]) if fa else ""))
    return out


def g13_lines(g, st, y, led):
    """G13 のこの年のようす (やさしい日本語の箇条)"""
    out = []
    gr = (g.get("grind") or {}).get(str(y)) or {}
    if led:
        out.append(f"粉ひき: 手でひいたのは のべ 約 {led.get('grind_days', 0)} 人日 (6 時間働く大人で)・水の輪がひいた分は 約 {led.get('water_days', 0)} 人日分"
                   f" (人でない力の割合 {round(100 * led.get('water_share', 0))}%)")
    elif gr:
        out.append(f"粉ひき: 手でひいたのは のべ 約 {round(gr.get('hours', 0) / 6)} 人日")
    m = g.get("mill") or {}
    built = [x for x in m.get("mills") or [] if x["day"] // YEAR == y]
    out.append(f"水の輪: 建った輪 {len(m.get('mills') or [])} (この年に建った {len(built)})" + (f"・試す進み {led.get('try')}" if led and not led.get("try_done") else "")
               + (f"・この年に直した {led.get('mill_repair', 0)} 人日" if led else ""))
    c = g.get("canal") or {}
    out.append(f"水の道: この年に掘った {c.get('dug', {}).get(str(y), 0)} 人日・水の来る畑は 秋にまく草の種 {led.get('canal_cap', c.get('cap', 0))} つかみ分"
               + (f"・泥でうまってへった {sum(x['lost'] for x in c.get('lost') or [] if x['year'] == y)} つかみ分" if any(x["year"] == y for x in c.get("lost") or []) else ""))
    pr = (g.get("protected") or {}).get(str(y))
    if pr:
        out.append(f"村の悪い年に、水の来る畑が守った刈り入れ: 約 {pr} つかみ")
    wk = (g.get("workers") or {}).get(str(y)) or {}
    if wk:
        out.append(f"約束の働き手: 刈った {wk.get('reap', 0)} 人日・水の道を掘った {wk.get('dig', 0)} 人日 ({'・'.join(sorted(wk.get('from') or {}))})")
    fa = [f for f in g.get("fails") or [] if f.get("year") == y]
    out.append(f"休んだ・へった・止まった: {len(fa)} 回" + (": " + " / ".join(clean(f["why"], 60) for f in fa[:3]) if fa else ""))
    return out


def path_line(C, y):
    p = C.get("path")
    if not p:
        return None
    r = p["row"]
    if not r:
        return f"道の見張り: この年 ({y}年) は、まだ村の集まりがなかった (数える年は {(p['start'] + 1) // YEAR}年から)"
    if p.get("g") == "G13":
        t = (f"道の見張り: この年の村の集まり {r['meetings']} 回で、答える人のうち、その道を自分で選べた人は、のべで条件 1 (水の輪を試す・建てる) {r['c1']} 人、"
             f"条件 2 (水の道を掘る) {r['c2']} 人、条件 3 (約束の分・働き手) {r['c3']} 人。実際に選んだ人は {r.get('chose', 0)} 人"
             f" (札を知っている大人 {r.get('knowers', 0)} 人)。{G13.PATH_YEARS} 年つづけて 0 人なら、止めて相談する")
        return t + ("。この年の終わりに、止めて相談することになった" if p["consult"] else "")
    if p.get("g") == "G12":
        t = (f"道の見張り: この年の村の集まり {r['meetings']} 回で、答える人のうち、その道を自分で選べた人は、のべで条件 1 (倉の約束) {r['c1']} 人、"
             f"条件 2 (倉から助ける) {r['c2']} 人" + ("" if r.get("need2", True) else " (苦しい村がなかった)") + f"、条件 3 (帳をつける) {r['c3']} 人。"
             f"実際に選んだ人は {r.get('chose', 0)} 人。{G12.PATH_YEARS} 年つづけて 0 人なら、止めて相談する")
        return t + ("。この年の終わりに、止めて相談することになった" if p["consult"] else "")
    if p.get("g") == "G11":
        t = (f"道の見張り: この年の村の集まり {r['meetings']} 回で、答える人のうち、その道を自分で選べた人は、のべで条件 1 (印を決める・作る・印で払う) {r['c1']} 人、"
             f"条件 2 (市の日を決める) {r['c2']} 人、条件 3 (字の読める村で印で貸す) {r['c3']} 人。実際に選んだ人は {r.get('chose', 0)} 人。"
             f"{G11.PATH_YEARS} 年つづけて 0 人なら、止めて相談する")
        return t + ("。この年の終わりに、止めて相談することになった" if p["consult"] else "")
    t = (f"道の見張り: この年の村の集まり {r['meetings']} 回のうち、条件 1 の道 (黒い金属を試す・作る) がお題に出たのは {r['c1']} 回、"
         f"条件 2 の道 (音の字を試す・習う) は {r['c2']} 回。{G10.PATH_YEARS} 年つづけて 0 回なら、止めて相談する")
    if p["consult"]:
        t += "。この年の終わりに、止めて相談することになった"
    return t


def laws_part(D, y):
    lo, hi = y * YEAR, y * YEAR + YEAR - 1
    ad = [l for l in D["laws"] if l.get("adopted_day") is not None and lo <= l["adopted_day"] <= hi]
    pr = [l for l in D["laws"] if lo <= (l.get("proposed_day") or -1) <= hi]
    ab = [l for l in D["laws"] if l.get("abolished_day") is not None and lo <= l["abolished_day"] <= hi]
    return ad, pr, ab


def year_name(st, y):
    return next((x["name"] for x in (st.get("era2") or {}).get("year_names") or [] if x.get("year") == y), None)


# ---------------------------------------------------------------- 出来事を選ぶ

_TAG = re.compile(r"\s*\[[A-Z]{1,2}\d+\]")
_VOTE = re.compile(r"\s*\([^()]*(?:/ 大人 \d+|賛成 \d+ / \d+)[^()]*\)")


def clean(t, n=80):
    t = re.sub(r"\[D\d+\] の分として", "前に借りた分として", t or "")
    t = _VOTE.sub("", _TAG.sub("", t)).strip()
    return t if len(t) <= n else t[:n - 1] + "…"


def pick_events(D, y, limit=15):
    """大事な出来事を選ぶ (点の高いものから limit まで。並びは日の順)。生まれた・亡くなったは「人と暮らし」に出すので、ここには入れない"""
    cand = []
    pests = sum((e.get("data") or {}).get("amount", 0) for e in D["events"] if e["type"] == "虫")
    disputes = [e for e in D["events"] if e["type"] == "もめごと"]
    goats_lost = 0
    for e in D["events"]:
        t, tx, dt = e["type"], e.get("text") or "", e.get("data") or {}
        s = 0
        if t == "フェーズ":
            s = 10
        elif t == "目盛り":
            s = 9
        elif t in ("年の名前", "試す", "分かれる"):
            s = 8
        elif t == "交換" or (t == "よその村" and dt.get("far")):
            s = 7
        elif t == "道具" and ("金属" in tx or dt.get("tool") or dt.get("iron")):
            s = 7
        elif t in ("加わる", "貸し借り", "覚え", "祭り", "まとめ役", "裁き"):
            s = 6
        elif t == "字を習う" and dt.get("reader"):
            s = 6
        elif t == "よその便り":
            s = 5
        elif t in ("訪れる", "去る") and "受け入れられず" in tx:
            s = 4
        elif t == "ヤギ" and "いなくなった" in tx:
            m = re.search(r"ヤギ (\d+) 頭", tx)
            goats_lost += int(m.group(1)) if m else 0
        elif t == "けが" and "ザガ" in tx:
            s = 2
        if s:
            cand.append((s, e["day"], e["id"], clean(tx)))
    ad, _, ab = laws_part(D, y)
    for l in ad:
        cand.append((7, l["adopted_day"], 0, "掟が決まった: " + clean(l["text"], 70)))
    for l in ab:
        cand.append((5, l["abolished_day"], 0, "掟をやめた: " + clean(l["text"], 70)))
    kn = [k for k in D["knowledge"] if k.get("label") == "創発" and k.get("op") == "追加"]
    if kn:  # 村の人が自分で書いた知恵は多いので、数と、はじめの 1 つだけ
        k = kn[0]
        cand.append((5, k["day"], 0, f"村の人が自分で見つけた知恵 (創発) が {len(kn)} つ。たとえば: {clean(k['text'], 50)} ({k.get('who') or '?'})"))
    if disputes:
        cand.append((4, disputes[0]["day"], disputes[0]["id"], f"もめごとが {len(disputes)} 件あった"))
    if goats_lost:
        cand.append((3, y * YEAR + YEAR - 1, 10 ** 9 - 1, f"飼っていたヤギが、草や世話が足りず、1 年にのべ {goats_lost} 頭いなくなった"))
    if pests:
        cand.append((1, y * YEAR + YEAR - 1, 10 ** 9, f"蓄えの草の種が、虫やネズミで約 {round(pests):,} つかみ傷んだ (1 年分)"))
    seen, uniq = set(), []
    for c in sorted(cand, key=lambda c: (-c[0], c[1], c[2])):
        key = c[3][:30]
        if key in seen:
            continue
        seen.add(key)
        uniq.append(c)
    top = sorted(uniq[:limit], key=lambda c: (c[1], c[2]))
    return [(yd(c[1]), c[3]) for c in top], len(uniq)


# ---------------------------------------------------------------- テクノロジー

def tech_part(data, y):
    import build_tech_tree as btt
    out, _ = btt.build(str(data), quiet=True)
    lo, hi = y * YEAR, y * YEAR + YEAR - 1
    nodes = [(n["first"]["day"], n["name"], n.get("does") or "") for n in out["nodes"]
             if n.get("status") == "届いた" and lo <= ((n.get("first") or {}).get("day") or -1) <= hi]
    techs = [(x["first"]["day"], x["name"]) for x in out["techs"] if x.get("status") == "届いた" and lo <= ((x.get("first") or {}).get("day") or -1) <= hi]
    firsts = [(f["day"], f["cat"], f["name"], clean(f.get("text"), 70)) for f in out["firsts"]
              if lo <= f["day"] <= hi and f["cat"] != "よその便り (札)"]  # 札の番号 (どの史実の札か) は【シ】なので出さない
    emerged = [(e["day"], e["name"], e.get("kind"), e.get("what") or "") for e in out["emerged"] if lo <= e["day"] <= hi]
    c = out["counts"]
    return {"nodes": sorted(nodes), "techs": sorted(techs), "firsts": sorted(firsts), "emerged": sorted(emerged),
            "total": (c["届いた"], c["nodes"])}


# ---------------------------------------------------------------- 文を作る

def headline(PP, C, phase):
    """ひとことで言うと (1〜2 文): 条件ごとに近づいた / 同じ / 遠のいた と、村が大丈夫か"""
    w = {1: "近づいた", 0: "同じ", -1: "遠のいた"}
    parts = []
    for i, k in enumerate(("c1", "c2", "c3"), 1):
        if k in C["moves"]:
            bar = next((b for b in C["bars"] if b["label"].startswith(f"条件 {i}")), None)
            parts.append(f"条件 {i} は{'届いている' if bar and bar['done'] else w[C['moves'][k]]}")
    s1 = (f"今年、{phase} の目標には、" + "・".join(parts) + "。") if parts else ""
    a, b = PP["start"]["population"] if PP["start"] else None, PP["end"]["population"] if PP["end"] else None
    starve = any(d["cause"] == "飢え" for d in PP["deaths"])
    low = PP["end"] and (PP["end"].get("store_days") or 0) < 60
    if a is not None and b is not None:
        trend = "ふえた" if b > a else "へった" if b < a else "変わらない"
        s2 = f"人は {a} 人から {b} 人に{trend if trend == '変わらない' else trend}。" + \
             ("飢えた人がいた。" if starve else "飢えはなかった。") + ("蓄えが少ないので注意。" if low else "村は大丈夫。" if not starve else "")
    else:
        s2 = ""
    return s1 + s2


def highlights(y, PP, C, ad, emer_k, T, far, phase_change, yname):
    hs = []
    if PP["start"] and PP["end"]:
        hs.append(f"人は {PP['start']['population']} 人 → {PP['end']['population']} 人 (生まれた子 {len(PP['births'])} 人・亡くなった人 {len(PP['deaths'])} 人)")
    for b in C["bars"]:
        if b["done_day"] is not None and b["done_day"] >= y * YEAR:
            hs.append(f"{b['label']} に届いた ({yd(b['done_day'])})")
    for k, v, d in C["fs"]:
        if d is not None and d >= y * YEAR:
            hs.append(f"目盛り {k}「{v}」に届いた")
    if phase_change:
        hs.append(phase_change)
    if T and (T["nodes"] or T["techs"]):
        hs.append("新しく届いた技術: " + "・".join([n[1] for n in T["techs"]] + [n[1] for n in T["nodes"]][:4]))
    if ad:
        hs.append(f"新しい掟が {len(ad)} つ決まった")
    if far:
        hs.append(far)
    if emer_k:
        hs.append(f"村の人が自分で見つけた知恵 (創発) が {emer_k} つ")
    if yname:
        hs.append(f"村の人は、この年を「{yname}」と呼んだ")
    return hs[:5]


def next_lines(C, y, phase_next, nxt_era=None):
    out = []
    if phase_next:
        out.append(phase_next)
    if nxt_era == "G10":  # 年の終わりに G10 に入った: 新しい条件の、はじめの一歩を見る
        out += ["黒い金属の鎌を、村で作れるようになるか (作り方を試せるようになった)",
                "音の字 (音 1 つに字 1 つ) ができて、字を読み書きできる人が出るか"]
        return out[:3]
    if nxt_era:
        return out[:3]
    if C["phase"] == "G10":
        b = {i: x for i, x in enumerate(C["bars"], 1)}
        rch = dict((k, d) for k, _, d in C["fs"])
        if not b[1]["done"]:
            out.append("黒い金属の鎌が村で作れるか (作り方を試す人が出るか)" if not rch.get("F1") else
                       f"黒い金属の鎌で刈る日が、刈る日の半分をこえるか (今年 {b[1]['value']} / 目標 {b[1]['goal']} 人日)")
        if not b[2]["done"]:
            out.append("音の字 (音 1 つに字 1 つ) ができるか" if not rch.get("F2") else
                       f"記録の家の外で、字を読める大人が {G10.C2_READERS} 人になるか (いま {b[2]['value']} 人)")
        if not b[3]["done"]:
            out.append(f"まわりの集落とのまとまりが深くなるか (いま {b[3]['value']} 段・{b[4]['value']} 集落。目標は {G10.C3_D} 段で半分以上)")
        p = (C.get("path") or {}).get("row")
        zero = [k[1:] for k in ("c1", "c2") if p and p[k] == 0 and not b[int(k[1:])]["done"]]
        if zero:  # 止めて相談になるかもしれないので、いちばん上に出す
            out.insert(1 if phase_next else 0,
                       f"道の見張り: 今年、条件 {'・'.join(zero)} の道がお題に出なかった。来年も 0 回なら、止めて相談になる")
    elif C["phase"] == "G13":
        b = {i: x for i, x in enumerate(C["bars"], 1)}
        rch = dict((k, d) for k, _, d in C["fs"])
        if not b[1]["done"]:
            out.append("札を知っている人が水の輪を試すか (仕事「試す」)" if not rch.get("F2") else
                       "水の輪を建てて、1 年に 90 日回すか" if not rch.get("F3") else f"水の輪が村の粉の半分以上をひく年が来るか (今年 {b[2]['value']}%)")
        if not b[3]["done"]:
            out.append("だれかが「水の道を掘る」を選ぶか" if not rch.get("F1") else f"秋のまきつけの半分以上に水が来る年が 2 年つづくか (今年 {b[3]['value']}%)")
        if not b[4]["done"]:
            out.append(f"地域の集落の半分以上が、約束の分か働き手を出す年が 2 回来るか (今年 {b[4]['value']} 集落)")
    elif C["phase"] == "G12":
        b = {i: x for i, x in enumerate(C["bars"], 1)}
        rch = dict((k, d) for k, _, d in C["fs"])
        if not b[1]["done"]:
            out.append("近くの村と倉の約束を結ぶか (答えの pact)" if not rch.get("F1") else
                       f"倉の約束どおり出す村が {G12.C1_MIN} つ以上の年が来るか (今年 {b[1]['value']} 村)")
        if not b[2]["done"]:
            out.append("いま苦しい村に、村の倉から助けを出すか (答えの help)" if not rch.get("F2") else
                       f"1 年に {G12.C2_SETTLEMENTS} 集落・{G12.C2_AMOUNT} つかみまで倉から出すか (今年 {b[2]['value']} 集落・{b[3]['value']} つかみ)")
        if not b[4]["done"]:
            out.append("字を読める人が「帳をつける」を選ぶか" if not rch.get("F3") else "家と倉と約束を書いた帳が 2 年つづくか")
    elif C["phase"] == "G11":
        b = {i: x for i, x in enumerate(C["bars"], 1)}
        rch = dict((k, d) for k, _, d in C["fs"])
        if not b[1]["done"]:
            out.append("村の印を打った印のかたまりができるか (作れる人が「印のかたまりを作る」を選ぶか)" if not rch.get("F1") else
                       "村が印のかたまりで払うと決めて (pay)、よその集落との出し入れの半分以上を印のかたまりでするか" if not rch.get("F3") else
                       f"よその集落との出し入れの半分以上を印のかたまりでするか (今年 {b[1]['value']} / 目標 {b[1]['goal']} 回)")
        if not b[2]["done"]:
            out.append("掟で市の日が決まり、よその集落の人が来て替える市が立つか" if not rch.get("F2") else
                       f"よその人が来て替える市が、1 年 {G11.C2_MARKETS} 回以上つづくか (今年 {b[2]['value']} 回)")
        if not b[3]["done"]:
            out.append("よその村への貸し・返しを印のかたまりでして、その量を字で書くか")
    elif C["phase"] == "G9":
        for i, x in enumerate(C["bars"], 1):
            if not x["done"]:
                out.append(f"{x['label']}: いま {x['value']} {x['unit']} (目標 {x['goal']} {x['unit']})")
    return out[:3]


# ---------------------------------------------------------------- 図 (SVG。1 つの図に 1 つの目盛り)

INK, INK2, MUTED, GRID, S1, S2, GOOD = "#0b0b0b", "#52514e", "#898781", "#e1e0d9", "#2a78d6", "#eb6834", "#1a8f5a"


def _nice(v):
    for s in (5, 10, 20, 25, 50, 100, 200, 250, 500, 1000):
        if v / s <= 5:
            return s
    return 10 ** len(str(int(v)))


def svg_pop(hist):
    if not hist:
        return ""
    W, H, L, R, T, B = 360, 190, 34, 60, 12, 26
    top = max(max(h["adults"], h["children"]) for h in hist)
    step = _nice(top)
    ymax = step * (-(-top // step))
    n = len(hist)
    x = lambda i: L + (W - L - R) * (i / max(1, n - 1))
    yv = lambda v: T + (H - T - B) * (1 - v / ymax)
    s = [f'<svg viewBox="0 0 {W} {H}" role="img" aria-label="人数のうつりかわり (大人と子)">']
    v = 0
    while v <= ymax:
        s.append(f'<line x1="{L}" x2="{W - R}" y1="{yv(v):.1f}" y2="{yv(v):.1f}" stroke="{GRID}" stroke-width="1"/>'
                 f'<text x="{L - 4}" y="{yv(v) + 4:.1f}" text-anchor="end" font-size="10" fill="{MUTED}">{v}</text>')
        v += step
    for i, h in enumerate(hist):
        if i % 2 == (n - 1) % 2:
            s.append(f'<text x="{x(i):.1f}" y="{H - 8}" text-anchor="middle" font-size="10" fill="{MUTED}">{h["year"]}年</text>')
    ly = {k: yv(hist[-1][k]) + 4 for k in ("adults", "children")}
    if abs(ly["adults"] - ly["children"]) < 13:  # 端の名前が重ならないように、上下に離す
        hi_k, lo_k = ("adults", "children") if hist[-1]["adults"] >= hist[-1]["children"] else ("children", "adults")
        mid = (ly["adults"] + ly["children"]) / 2
        ly[hi_k], ly[lo_k] = mid - 6.5, mid + 6.5
    for key, col, lab in (("adults", S1, "大人"), ("children", S2, "子ども")):
        pts = " ".join(f"{x(i):.1f},{yv(h[key]):.1f}" for i, h in enumerate(hist))
        s.append(f'<polyline points="{pts}" fill="none" stroke="{col}" stroke-width="2" stroke-linejoin="round"/>')
        for i, h in enumerate(hist):
            s.append(f'<circle cx="{x(i):.1f}" cy="{yv(h[key]):.1f}" r="3" fill="{col}" stroke="#fff" stroke-width="1.5">'
                     f'<title>{h["year"]}年の終わり: {lab} {h[key]} 人</title></circle>')
        s.append(f'<text x="{x(n - 1) + 6:.1f}" y="{ly[key]:.1f}" font-size="11" fill="{INK2}">{lab} {hist[-1][key]}</text>')
    s.append("</svg>")
    return "".join(s)


def svg_store(rows):
    if not rows:
        return ""
    W, H, L, R, T, B = 360, 160, 34, 10, 18, 24
    vals = [r.get("store_days") or 0 for r in rows]
    step = _nice(max(vals) or 1)
    ymax = step * (-(-max(vals) // step)) or 1
    yv = lambda v: T + (H - T - B) * (1 - v / ymax)
    bw = (W - L - R) / 4
    s = [f'<svg viewBox="0 0 {W} {H}" role="img" aria-label="季節の終わりの村の蓄え (いまの人数で何日分)">']
    v = 0
    while v <= ymax:
        s.append(f'<line x1="{L}" x2="{W - R}" y1="{yv(v):.1f}" y2="{yv(v):.1f}" stroke="{GRID}"/>'
                 f'<text x="{L - 4}" y="{yv(v) + 4:.1f}" text-anchor="end" font-size="10" fill="{MUTED}">{v}</text>')
        v += step
    for i, r in enumerate(rows):
        v = vals[i]
        x0 = L + bw * i + bw * 0.22
        w = bw * 0.56
        y0 = yv(v)
        hgt = max(0.0, yv(0) - y0)
        s.append(f'<path d="M{x0:.1f},{yv(0):.1f} V{y0 + 4:.1f} Q{x0:.1f},{y0:.1f} {x0 + 4:.1f},{y0:.1f} H{x0 + w - 4:.1f} '
                 f'Q{x0 + w:.1f},{y0:.1f} {x0 + w:.1f},{y0 + 4:.1f} V{yv(0):.1f} Z" fill="{S1}">'
                 f'<title>{r["label"]}の終わり: 蓄え {v} 日分</title></path>' if hgt > 4 else
                 f'<rect x="{x0:.1f}" y="{y0:.1f}" width="{w:.1f}" height="{hgt:.1f}" fill="{S1}"/>')
        s.append(f'<text x="{x0 + w / 2:.1f}" y="{y0 - 4:.1f}" text-anchor="middle" font-size="10" fill="{INK2}">{v}</text>'
                 f'<text x="{x0 + w / 2:.1f}" y="{H - 8}" text-anchor="middle" font-size="11" fill="{MUTED}">{r.get("season", "")}</text>')
    s.append("</svg>")
    return "".join(s)


# ---------------------------------------------------------------- HTML

CSS = """
*{box-sizing:border-box}
body{margin:0;background:#f7f6f2;color:#1b1b1a;font-family:-apple-system,"Hiragino Sans","Hiragino Kaku Gothic ProN","Noto Sans JP","IPAGothic",sans-serif;
 font-size:16px;line-height:1.7;-webkit-text-size-adjust:100%}
main{max-width:520px;margin:0 auto;padding:14px 14px 40px}
h1{font-size:22px;line-height:1.35;margin:6px 0 4px}
h2{font-size:17px;margin:0 0 8px;padding-bottom:4px;border-bottom:2px solid #e1e0d9}
.sub{color:#52514e;font-size:14px}
.card{background:#fff;border:1px solid #e6e4dc;border-radius:12px;padding:12px 14px;margin:12px 0}
.decide{border:2px solid #eb6834;background:#fff8f3}
.decide h2{border-color:#f6c9b2}
.lead{font-size:16.5px}
ul{margin:4px 0;padding-left:1.2em}
li{margin:3px 0}
details summary{cursor:pointer;font-weight:600}
details ol{margin:6px 0 0;padding-left:1.4em}
.bar{margin:10px 0 12px}
.bar .t{display:flex;justify-content:space-between;gap:8px;font-size:14.5px;font-weight:600}
.bar .t span:last-child{white-space:nowrap;font-weight:500;color:#52514e}
.track{height:12px;background:#ecebe5;border-radius:6px;overflow:hidden;margin:4px 0 2px}
.fill{height:100%;background:#2a78d6;border-radius:6px}
.fill.ok{background:#1a8f5a}
.note{font-size:13px;color:#52514e}
.ok-tag{color:#1a8f5a;font-weight:700}
.fs{display:flex;flex-wrap:wrap;gap:6px;margin:6px 0}
.fs span{font-size:13px;border:1px solid #d8d6cc;border-radius:999px;padding:2px 9px;background:#faf9f6}
.fs span.on{border-color:#1a8f5a;color:#14663f;background:#eef8f2;font-weight:600}
table{border-collapse:collapse;width:100%;font-size:14.5px}
td{padding:4px 2px;border-bottom:1px solid #efede6;vertical-align:top}
td:last-child{text-align:right;white-space:nowrap}
.ev li{font-size:14.5px}
.ev .d{color:#898781;font-size:12.5px;display:block;line-height:1.3}
svg{width:100%;height:auto;display:block;margin:4px 0}
.legend{font-size:13px;color:#52514e}
.legend i{display:inline-block;width:10px;height:10px;border-radius:2px;margin:0 4px 0 10px;vertical-align:-1px}
.foot{font-size:12px;color:#898781;margin-top:18px}
"""


def e(t):
    return html.escape(str(t), quote=False)


def fmt_tokens(n):
    if n >= 10 ** 4:
        return f"約 {n / 10 ** 4:,.0f} 万 ({n:,})"
    return f"{n:,}"


def render(y, D, PP, C, ev, ev_total, T, tokens, decide):
    st = D["state"]
    phase = C["phase"]
    pname = era2.NAMES2.get(phase, phase)
    lo, hi = y * YEAR, y * YEAR + YEAR - 1
    ad, pr, ab = laws_part(D, y)
    emer_k = sum(1 for k in D["knowledge"] if k.get("label") == "創発" and k.get("op") == "追加")
    far_tr = [x for x in D["events"] if x["type"] == "交換" and (x.get("data") or {}).get("far")]
    far = f"遠くの町の運ぶ人と {len(far_tr)} 回取り替えた" if far_tr else ""
    ph_ev = [x for x in D["events"] if x["type"] == "フェーズ"]
    nxt_era = next((x["era"] for x in st.get("era_log") or [] if lo < x["day"] <= hi + 1 and x["era"] != phase), None)
    phase_change = (f"年の終わりに {phase} を閉じて、{nxt_era}「{era2.NAMES2.get(nxt_era, '')}」に入った" if nxt_era else
                    ("フェーズの区切り: " + clean(ph_ev[-1]["text"], 50)) if ph_ev else "")
    phase_next = (f"次の年から {nxt_era}「{era2.NAMES2.get(nxt_era, '')}」の条件で測る (新しい条件の棒は来年の年報から)" if nxt_era else "")
    yname = year_name(st, y)
    hs = highlights(y, PP, C, ad, emer_k, T, far, phase_change, yname)
    nl = next_lines(C, y, phase_next, nxt_era)
    H = []
    w = H.append
    w('<!doctype html><html lang="ja"><head><meta charset="utf-8">'
      '<meta name="viewport" content="width=device-width,initial-scale=1">'
      f"<title>川辺の村 {y}年の年報</title><style>{CSS}</style></head><body><main>")
    # 見出し
    w(f"<h1>川辺の村 {y}年の年報</h1>")
    # あなたが決めること
    w('<section class="card decide"><h2>あなたが決めること</h2>'
      + (f"<p>{e(decide)}</p>" if decide else "<p>なし (読むだけで大丈夫です)</p>") + "</section>")
    # ひとことで言うと
    w(f'<section class="card"><h2>ひとことで言うと</h2><p class="lead">{e(headline(PP, C, phase))}</p>')
    w('<details><summary>この年報の見かた</summary><ol>'
      "<li>この村は、AI の村人が、人の歴史と同じように技術やくらしのしくみを生み出すかを試す村です。</li>"
      "<li>フェーズごとに、歴史で起きたことを目標 (条件) にしています。</li>"
      "<li>見るのは 3 つ: ① 条件の棒が進んだか ② 村が無事か (人数・食べ物) ③ 何かおかしなことがないか。</li></ol></details></section>")
    w(f'<section class="card"><h2>この年報について</h2><div class="sub">フェーズ {e(phase)}「{e(pname)}」<br>{e(yd(lo))} 〜 {e(yd(hi))} (通しの日 {lo}〜{hi})'
      + (f"<br>この 1 年に使ったトークン: {e(fmt_tokens(tokens))}" if tokens is not None else "")
      + (f"<br>村の人の呼び名: 「{e(yname)}」" if yname else "") + "</div></section>")
    if not PP["complete"]:
        w('<div class="card"><b>この年はまだ終わっていない</b> (記録のある季節だけで数えた)</div>')
    # ひとことで (箇条)
    w('<section class="card"><h2>今年の大事なこと</h2><ul>' + "".join(f"<li>{e(h)}</li>" for h in hs) + "</ul></section>")
    # 条件
    w(f'<section class="card"><h2>{e(phase)} の条件の進み</h2>')
    for b in C["bars"]:
        pct = 100 if b["done"] else min(100, round(100 * (b["value"] or 0) / b["goal"])) if b["goal"] else 0
        tag = f'<span class="ok-tag">届いた ({e(yd(b["done_day"]))})</span>' if b["done"] else f"{b['value']} / {b['goal']} {e(b['unit'])}"
        if b["done"]:
            tag = f'<span class="ok-tag">✓ 届いた</span> {b["value"]} {e(b["unit"])}'
        w(f'<div class="bar"><div class="t"><span>{e(b["label"])}</span><span>{tag}</span></div>'
          f'<div class="track"><div class="fill{" ok" if b["done"] else ""}" style="width:{max(pct, 1)}%"></div></div>'
          f'<div class="note">{e(b["note"])}' + (f"。届いた日: {e(yd(b['done_day']))}" if b["done"] else "") + "</div></div>")
    if C["fs"]:
        w('<div class="note">小さな目盛り (F):</div><div class="fs">'
          + "".join(f'<span class="{"on" if d is not None else ""}">{"✓ " if d is not None else ""}{e(k)} {e(v)}</span>' for k, v, d in C["fs"]) + "</div>")
    pl = path_line(C, y)
    if C.get("g13"):
        w('<p style="margin:10px 0 2px"><b>水と畑と務め (この年)</b></p><ul class="note">' + "".join(f"<li>{e(x)}</li>" for x in C["g13"]) + "</ul>")
    if C.get("g12"):
        w('<p style="margin:10px 0 2px"><b>倉と約束と帳 (この年)</b></p><ul class="note">' + "".join(f"<li>{e(x)}</li>" for x in C["g12"]) + "</ul>")
    if C.get("g11"):
        w('<p style="margin:10px 0 2px"><b>印のかたまりと市 (この年)</b></p><ul class="note">' + "".join(f"<li>{e(x)}</li>" for x in C["g11"]) + "</ul>")
    for x in C["extra"] + ([pl] if pl else []):
        w(f'<p class="note">{e(x)}</p>')
    w("</section>")
    # 人と暮らし
    S, E = PP["start"] or {}, PP["end"] or {}
    w('<section class="card"><h2>人と暮らし</h2><table>')
    w(f"<tr><td>人数 (年のはじめ → 終わり)</td><td>{S.get('population', '?')} → <b>{E.get('population', '?')}</b> 人</td></tr>")
    w(f"<tr><td>　大人</td><td>{S.get('adults', '?')} → {E.get('adults', '?')} 人</td></tr>")
    w(f"<tr><td>　子ども</td><td>{S.get('children', '?')} → {E.get('children', '?')} 人</td></tr>")
    w(f"<tr><td>生まれた子</td><td>{len(PP['births'])} 人</td></tr>")
    w(f"<tr><td>よそから加わった人 / 村を出た人</td><td>{len(PP['joined'])} 人 / {len(PP['left'])} 人</td></tr>")
    w(f"<tr><td>刈り入れ (草の種)</td><td>{PP['harvest']:,.0f} つかみ</td></tr>")
    st_end = (E.get("store") or {}).get("草の種")
    w(f"<tr><td>年の終わりの村の蓄え</td><td>{(st_end or 0):,.0f} つかみ<br><span class='note'>いまの人数で {E.get('store_days', '?')} 日分</span></td></tr>")
    w(f"<tr><td>ヤギ (年の終わり)</td><td>{(E.get('goats') or {}).get('count', '?')} 頭</td></tr></table>")
    if PP["deaths"]:
        w(f'<p style="margin:10px 0 2px"><b>亡くなった人 ({len(PP["deaths"])} 人)</b></p><ul>'
          + "".join(f"<li>{e(d['name'])} ({d['age']} 歳) — {e(DEATH_WORD.get(d['cause'], '亡くなった'))}"
                    f"<span class='note'> {e(yd(d['day']))}</span></li>" for d in sorted(PP["deaths"], key=lambda d: d["day"] or 0)) + "</ul>")
    else:
        w("<p>亡くなった人はいなかった。</p>")
    hist = pop_history(D, y)
    w(f'<p style="margin:12px 0 0"><b>人数のうつりかわり ({hist[0]["year"] if hist else y}〜{y}年の終わり)</b></p>'
      f'<div class="legend"><i style="background:{S1}"></i>大人<i style="background:{S2}"></i>子ども</div>' + svg_pop(hist))
    w('<p style="margin:12px 0 0"><b>この年の食べ物: 季節の終わりの蓄え</b> <span class="note">(いまの人数で何日分)</span></p>' + svg_store(PP["rows"]))
    w("</section>")
    # 起きたこと
    w('<section class="card ev"><h2>起きたこと</h2>')
    if ev:
        w("<ul>" + "".join(f'<li><span class="d">{e(d)}</span>{e(t)}</li>' for d, t in ev) + "</ul>")
        if ev_total > len(ev):
            w(f'<p class="note">ほかに {ev_total - len(ev)} 件 (小さいものは省いた)</p>')
    else:
        w("<p>大きな出来事はなかった。</p>")
    if pr:
        w(f'<p class="note">掟の案が {len(pr)} つ出た (決まったのは {len(ad)} つ)。</p>')
    w("</section>")
    # テクノロジー
    w('<section class="card"><h2>テクノロジー</h2>')
    if T is None:
        w('<p class="note">(この年報では作らなかった)</p>')
    else:
        items = [f"<li><b>{e(n)}</b> (大きな技術)</li>" for _, n in T["techs"]]
        items += [f"<li><b>{e(n)}</b> — {e(clean(d, 50))}</li>" for _, n, d in T["nodes"]]
        items += [f"<li>はじめての{e(c)}: 「{e(n)}」 — {e(t)}</li>" for _, c, n, t in T["firsts"]]
        items += [f"<li>創発 ({e(k)}): {e(n)} — {e(clean(wh, 60))}</li>" for _, n, k, wh in T["emerged"]]
        w(("<ul>" + "".join(items) + "</ul>") if items else "<p>この年に新しく届いた技術はなかった。</p>")
        w(f'<p class="note">テクノロジーツリーで届いた要素: ぜんぶで {T["total"][0]} / {T["total"][1]}</p>')
    w("</section>")
    # 次の年に見ること
    w('<section class="card"><h2>次の年に見ること</h2><ul>' + "".join(f"<li>{e(x)}</li>" for x in nl) + "</ul></section>")
    w(f'<div class="foot">作った日: 記録の {e(yd(st["day"]))} まで。tools/year_report.py</div></main></body></html>')
    return "\n".join(H)


def main(argv=None):
    ap = argparse.ArgumentParser(description="川辺の村の年報 (1 枚の HTML)")
    ap.add_argument("--data", default=os.path.join(SOC, "data"))
    ap.add_argument("--year", type=int, required=True)
    ap.add_argument("--tokens", type=int)
    ap.add_argument("--decide")
    ap.add_argument("--no-tech", action="store_true")
    ap.add_argument("--out", required=True)
    a = ap.parse_args(argv)
    out = os.path.realpath(a.out)
    if out == PROTECTED or out.startswith(PROTECTED + os.sep):
        sys.exit("sim/society/data/ の下には書かない (--out を変える)")
    y = a.year
    D = load(a.data, y)
    if y * YEAR > D["state"]["day"]:
        sys.exit(f"{y}年はまだ始まっていない (いまは {yd(D['state']['day'])})")
    PP = people_part(D, y)
    phase = phase_of_year(D, y)
    C = conditions(D, y, phase)
    ev, n = pick_events(D, y)
    T = None if a.no_tech else tech_part(a.data, y)
    page = render(y, D, PP, C, ev, n, T, a.tokens, a.decide)
    Path(out).parent.mkdir(parents=True, exist_ok=True)
    Path(out).write_text(page, encoding="utf-8")
    print(f"{out} を書いた ({y}年・{phase}・{len(page) // 1024} KB)")


if __name__ == "__main__":
    main()
