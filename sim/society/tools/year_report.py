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
  techtree/ (tools/build_tech_tree.py の build をそのまま使う)。G9・G10 の条件の数え方は g9.py・g10.py の決まり (目標の数) をそのまま使う。
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
        g = _g7(st).get("g10") or {}
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
    else:
        out["extra"] = [f"この年のフェーズ {phase} の条件の棒は、まだ作っていない。条件: {(st.get('era_info') or {}).get('next', '-')}"]
    return out


def path_line(C, y):
    p = C.get("path")
    if not p:
        return None
    r = p["row"]
    if not r:
        return f"道の見張り: この年 ({y}年) は、まだ村の集まりがなかった (数える年は {(p['start'] + 1) // YEAR}年から)"
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
