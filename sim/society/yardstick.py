"""G7 の物差し (docs/society_phase/G7_design.md 4.D): 進む条件 3 つ・F1〜F6・決める段・取り立ての記録の年・条件ごとの止まり・marks・先に届いた目盛り

- state を読むだけで、乱数を引かない (新しい塩はいらない)。季節の終わりの最後 (4.G.1 の 13) に g7.season_end から呼ぶ
- 測った数はみな【シ】(作る側の数)。お題にもダッシュボードにも出さない。出来事「目盛り」も【シ】(YEAR_EVENTS・MEETING_EVENTS に入れない)
- F に届いた日は g7.reached に残し、era2.check_substeps が出来事「区切り」に残す (今までの F と同じ)
- 通説は物差しで、村がたどる道ではない (本人の答え 2)。「まちがい」とは書かない
"""
import math

import era2
import region
from world import log, season

YEAR, SEASON_DAYS = era2.YEAR, era2.SEASON_DAYS
ROLE_ACTS = ("記録をつける", "取り立てる", "守る", "戦に出る")  # 役の仕事 (試すは入れない。4.F の 1)
F6_DAYS, F6_SHARE, F6_RUN = 20, 0.10, 4  # F6 役所: 季節の役の人 (その季節に役の仕事を 20 日以上) が大人の 1 割以上の季節が 4 つ続いた (G6 の KEEPER_DAYS・NONFOOD と同じ)
MERCHANT_DAYS = YEAR // 2  # 先の目盛り G8 F2「商人の家」: 交換に行った日が 1 年の半分をこえる家 (4.D.7)
STALL_ASK, STALL_STOP = 8, 16  # 条件ごとの止まり (4.E.2)


def _g(state):
    return state["era2"]["g7"]


# ---------------- 決める段 (4.D.2) ----------------

def officials(state):
    """村の役の人 (決める人): この 1 年に、取り立てた物を村の蓄えに入れた記録 (出来事「取り立て」の moves) がある人。下は村の葉 (V0)。
    村の中の税は、払う人でない人が 2 つ以上の家から集めたときだけ数える (4.D.3)"""
    D = state["day"]
    out = {}
    for e in state["events"]:
        if e["type"] != "取り立て" or e["day"] <= D - YEAR or not e.get("who"):
            continue
        d = e.get("data") or {}
        if len([h for h in d.get("homes", []) if h != _home(state, e["who"])]) >= 2 and d.get("moves"):
            out.setdefault(e["who"], ["V0"])
    return out


def _home(state, name):
    return next((p.get("household") for p in state["people"] if p["name"] == name), None)


def levels(state):
    """決める段 (4.D.2): 集落と役の両方で数え、どの段も 2 つ以上を下にもつ。村の蓄えに入れた物は、村の長 (まとめ役。いなければ村の集まり) に渡したとみなす"""
    import g7
    if not g7.region_on(state):
        return []
    return region.levels(g7._setts(state), g7._paid_ties(state), state["day"], officials=officials(state),
                         **({"village_rules": True} if g7.count_v2(state) else {}))  # 2026-10-24: 数え方 "v2" は、村もまわりと同じに数える


def village_group(lv):
    return next((x for x in lv if x["village"] != "外"), None)


# ---------------- 取り立ての記録 (4.D.3) ----------------

def _coll_season(state):
    """この季節の取り立て (村の中の税と、村が出す・受ける貢ぎ) を、記録できたかと一緒に残す。g7.coll は記録 (era2._g6_records) が読んだあと空にする"""
    g, D = _g(state), state["day"]
    coll = g.get("coll") or []
    if coll:
        cover = (era2._g6(state).get("cover") or {})
        full = "取り立て" in cover
        g.setdefault("coll_seasons", []).append({"day": D, "full": full, "how": cover.get("取り立て"), "n": len(coll)})
        g.setdefault("tribute_log", []).extend([dict(c, recorded=cover.get("取り立て")) for c in coll])
        g["tribute_log"] = g["tribute_log"][-200:]
        g["coll_seasons"] = g["coll_seasons"][-40:]
    g["coll"] = []


def _tribute_year(state):
    """年の終わり: その年に取り立てが 1 回以上あり、その年の取り立ての記録をみな「全部残せた」か。2 年続けば条件 2 (4.D.3)"""
    g, D = _g(state), state["day"]
    y = D // YEAR
    rows = [c for c in g.get("coll_seasons", []) if c["day"] // YEAR == y]
    ok = bool(rows) and all(c["full"] for c in rows)
    ys = g.setdefault("tribute_years", [])
    ys.append({"year": y, "coll": len(rows), "ok": ok})
    g["tribute_years"] = ys[-20:]
    if ok and len(ys) >= 2 and ys[-2]["ok"] and ys[-2]["year"] == y - 1 and not g.get("tribute2_day"):
        g["tribute2_day"] = D
        _mark(state, "条件 2", "決まった取り立てを、粘土の板の記録 (か数え札) で 2 年続けて全部残した")


def _tax_years(state):
    """村の中の税を集めた年 (F2 の「村の中の税を 2 年続けて集めた」)"""
    return sorted({c["day"] // YEAR for c in _g(state).get("tribute_log", []) if c["kind"] == "税" and len(c.get("from", [])) >= 2})


# ---------------- F (4.D.5) ----------------

def _first_plough(state):
    return next((e["day"] for e in state["events"] if e["type"] == "畑" and (e.get("data") or {}).get("plough")), None)


def _f2_day(state):
    D = state["day"]
    for t in (_g(state).get("region") or {}).get("ties", []):
        if "V0" in (t["payer"], t["payee"]) and t.get("fixed") is not None:
            return t["fixed"]
    ys = _tax_years(state)
    if any(b - a == 1 for a, b in zip(ys, ys[1:])):
        return D
    return None


def _f5_day(state):
    for d in (state["era2"].get("g6") or {}).get("debts", []):
        if (d.get("rate") or 0) > 0 and d.get("proof"):
            return state["day"]
    return None


def _role_share(state, frac):
    """季節の役の人 (その季節に役の仕事を合わせて 20 日以上。区切られた季節は日数の割合で) と大人の数"""
    days = _g(state).get("season_days") or {}
    ads = era2.adults(state)
    n = sum(1 for p in ads if sum((days.get(p["name"]) or {}).get(a, 0) for a in ROLE_ACTS) >= F6_DAYS * frac)
    return n, len(ads)


def _reach(state, f, day, why):
    r = _g(state).setdefault("reached", {})
    if f not in r and day is not None:
        r[f] = day
        _mark(state, f, why)


# ---------------- 先に届いた目盛り (4.D.7) ----------------

def _ahead(state):
    """G8 の F2「商人の家」: この 1 年に、家の人が交換に行った日が 1 年の半分をこえる家 (G6 の旅の記録で測る)"""
    e2, D = state["era2"], state["day"]
    if any(a["g"] == "G8" and a["f"] == "F2" for a in e2.get("ahead", [])):
        return
    days = {}
    for tr in (e2.get("g6") or {}).get("trip_log", []):
        if tr.get("start") is not None and tr["start"] > D - YEAR:
            h = _home(state, tr["who"])
            if h:
                days[h] = days.get(h, 0) + ((tr.get("end") or tr["start"]) - tr["start"] + 1)
    hit = sorted(h for h, n in days.items() if n > MERCHANT_DAYS)
    if hit:
        e2.setdefault("ahead", []).append({"g": "G8", "f": "F2", "name": "商人の家", "day": D, "households": hit})
        log(state, "目盛り", None, f"先の目盛り: G8 の F2「商人の家」に届いた ({'・'.join(hit)})", g="G8", f="F2")


# ---------------- 条件ごとの止まり (4.E.2) ----------------

def _progress(state, lv):
    """条件ごとの進み (それまでのいちばん高い値で見る)。c1 は村のいるまとまりの決める段 D (村が外なら 0)。
    2026-10-23: 前は地域のいちばん高い段も入れていたので、村の進みより大きく見えていた"""
    g = _g(state)
    vg = village_group(lv)
    c1 = vg["D"] if vg else 0
    c2 = 3 if g.get("tribute2_day") else 2 if any(y["ok"] for y in g.get("tribute_years", [])) else \
        1 if (g.get("tribute_log") or any(t.get("fixed") for t in (g.get("region") or {}).get("ties", []) if "V0" in (t["payer"], t["payee"]))) else 0
    laws = [l for l in state.get("laws", []) if l.get("penalty") or l.get("rate")]
    c3 = 3 if g.get("judged") else 2 if any(l.get("written") for l in laws) else 1 if any(l["status"] == "採用" for l in laws) else 0
    return {"c1": c1, "c2": c2, "c3": c3}


def _stall(state, lv):
    """年の終わり: 条件ごとに「進み」を見る。8 年進まなければ報告で相談 (ask)、16 年で止めて相談 (g7.consult_why が読む)"""
    g, D = _g(state), state["day"]
    y = (D + 1) // YEAR
    done = {"c1": bool((g.get("reached") or {}).get("F3")), "c2": bool(g.get("tribute2_day")), "c3": bool((g.get("reached") or {}).get("F4"))}
    st = g.setdefault("stall", {})
    s1 = st.get("c1")
    seen = (g.get("level_seen") or {}).get("village", 0)
    if s1 and not s1.get("done") and s1["best"] > seen:
        # 前の数え方 (地域のいちばん高い段) で残った best を、村の段 (level_seen.village = 村のいた段のいちばん高い値) に直す。
        # 村が一度も段に届いていなければ、進んだ年は G7 の最初の年の終わり (止まりを数え始めた年) にする。届いていれば since はそのまま
        y0 = -(-(g["start"] + 1) // YEAR)
        s1.update(best=seen, since=y0 if seen == 0 else s1["since"], ask=None)
    for k, v in _progress(state, lv).items():
        s = st.setdefault(k, {"best": v, "since": y, "done": False, "ask": None})
        if done[k]:
            s["done"] = True
            continue
        if v > s["best"]:
            s.update(best=v, since=y, ask=None)
        elif y - s["since"] >= STALL_ASK and s.get("ask") is None:
            s["ask"] = y


# ---------------- marks (4.D.8) ----------------

def _mark(state, what, why):
    """F か条件に届いた日の、そのときの条件 (【シ】)"""
    import g7
    g, D, e2 = _g(state), state["day"], state["era2"]
    reg = g.get("region") or {}
    lv = levels(state)
    vg = village_group(lv)
    hint_led = (g.get("hints") or {}).get("ledger", [])
    lo = D - 2 * YEAR
    g.setdefault("marks", []).append({
        "day": D, "what": what, "why": why, "era": state.get("era"),
        "people": sum(1 for p in state["people"] if p["alive"]), "region_people": sum(o["people"] for o in g7._others(state)),
        "households": len(era2._homes(state)), "store_days": round(era2.store_days(state), 1),
        "partners": sorted(g7._partners(state)) if g7.region_on(state) else [],
        "ties": [{k: t.get(k) for k in ("id", "payer", "payee", "status", "fixed", "end")} for t in reg.get("ties", []) if "V0" in (t["payer"], t["payee"])],
        "wars": [w["id"] for w in reg.get("wars", []) if w.get("done") is not None and w["done"] > lo],
        "bad": [w["year"] for w in reg.get("weather_log", []) if w["year"] * YEAR > lo and "V0" in w["bad"]],
        "free_cells": sum(1 for c in region.cells() if c not in region.occupied(g7._setts(state))) if g7.region_on(state) else None,
        "leader": era2._leader(state), "rule_laws": sum(1 for l in state.get("laws", []) if l["status"] == "採用" and (l.get("penalty") or l.get("rate"))),
        "levels": {"D": vg["D"], "T": vg["T"], "office": vg["office"], "top": vg["top"], "village": vg["village"]} if vg else None,
        "hints_before": [{"y": r["y"], "card": r["card"], "carrier": r["carrier"], "listeners": r.get("listeners"), "ago": D - r["delivered"]}
                         for r in hint_led if r["to"] == "V0" and r.get("event") is not None and r["delivered"] <= D][-8:],
        "source": _source(state, what), "offered": dict(g.get("offered") or {})})


def _source(state, what):
    """出どころ: ヒントのあと / きっかけから / 村の答え (掟のラベル。「知識の再現の疑い」をふくむ)"""
    g = _g(state)
    tech = ((g.get("hints") or {}).get("tech") or {})
    if what == "F1":
        t = tech.get("H7-06") or {}
        return "きっかけから" if t.get("source") == "きっかけ" else "ヒントのあと" if t.get("source") else "村の答え"
    led = [r for r in (g.get("hints") or {}).get("ledger", []) if r["to"] == "V0" and r.get("event") is not None]
    rel = {"F2": ("H7-01", "H7-02"), "F4": ("H7-03",), "F5": ("H7-04",), "F6": ("H7-02", "H7-08"), "条件 2": ("H7-01", "H7-02"), "F3": ("H7-01", "H7-07")}
    if any(r["card"] in rel.get(what, ()) for r in led):
        return "ヒントのあと"
    labels = sorted({l.get("label") for l in state.get("laws", []) if l["status"] == "採用" and (l.get("tax") or l.get("rate") or l.get("penalty"))} - {None})
    return "村の答え" + (f" ({'・'.join(labels)})" if labels else "")


# ---------------- 季節の終わり (4.G.1 の 13) ----------------

def season_end(state, frac):
    """物差し (季節の終わりの最後。乱数なし)"""
    g, D = _g(state), state["day"]
    _coll_season(state)
    lv = levels(state)
    vg = village_group(lv)
    top = max((x["D"] for x in lv), default=0)
    seen = g.setdefault("level_seen", {"village": 0, "region3": None})
    if vg and vg["D"] > seen["village"]:
        for k in range(seen["village"] + 1, min(vg["D"], 2) + 1):
            log(state, "目盛り", None, f"目盛り: 村のいるまとまりの決める段が {k} に届いた (いちばん上 {vg['top']})", levels=vg["D"], top=vg["top"])
        seen["village"] = vg["D"]
    if top >= 3 and seen.get("region3") is None and not (vg and vg["D"] >= 3):
        seen["region3"] = D
        x = max(lv, key=lambda x: x["D"])
        log(state, "目盛り", None, f"目盛り: 地域に決める段 3 のまとまりができた (いちばん上 {x['top']})。村は外", levels=x["D"], top=x["top"])
    if vg and vg["D"] >= 3:
        _reach(state, "F3", D, f"決める段 {vg['D']} のまとまりに村がいる ({vg['village']}。いちばん上 {vg['top']})")
    _reach(state, "F1", _first_plough(state), "牛 2 頭に犂を引かせて耕した")
    _reach(state, "F2", _f2_day(state), "決まった取り立て (村が出すか受ける貢ぎが期日に 2 回続けて払われた、か村の中の税を 2 年続けて集めた)")
    j = g.get("judged") or []
    _reach(state, "F4", j[0]["day"] if j else None, "板に書いた決まりで裁き、払わせた")
    _reach(state, "F5", _f5_day(state), "上乗せ (利子) のある貸し借りを、記録に残した")
    n, ads = _role_share(state, frac)
    ok = ads > 0 and n >= F6_SHARE * ads
    g["f6_run"] = g.get("f6_run", 0) + 1 if ok else 0
    g.setdefault("role_log", []).append({"day": D, "role": n, "adults": ads})
    g["role_log"] = g["role_log"][-40:]
    if g["f6_run"] >= F6_RUN:
        _reach(state, "F6", D, f"季節の役の人が大人の 1 割以上の季節が {F6_RUN} つ続いた")
    g["levels_now"] = {"D": vg["D"] if vg else 0, "T": vg["T"] if vg else 0, "office": vg["office"] if vg else 0, "village": vg["village"] if vg else "外",
                       "top": vg["top"] if vg else None, "members": len(vg["members"]) if vg else 0, "region_max": top}
    if (D + 1) % YEAR == 0:
        _tribute_year(state)
        _stall(state, lv)
    _ahead(state)


def indicators(state):
    """G7 の目安 (era2.indicators に足す。【シ】)"""
    g = _g(state)
    lv = g.get("levels_now") or {}
    ties = [t for t in (g.get("region") or {}).get("ties", []) if t["status"] == "続く"]
    return {"g7_levels": lv.get("D", 0), "g7_tiers": lv.get("T", 0), "g7_office_levels": lv.get("office", 0), "g7_centre": lv.get("top"),
            "g7_village": lv.get("village", "外"), "g7_ties": len(ties), "g7_tribute_years": sum(1 for y in g.get("tribute_years", []) if y["ok"]),
            "g7_tribute2_day": g.get("tribute2_day"), "g7_written_laws": sum(1 for l in state.get("laws", []) if l.get("written")),
            "g7_law_judged": len(g.get("judged") or []),
            "g7_interest": sum(1 for d in (state["era2"].get("g6") or {}).get("debts", []) if (d.get("rate") or 0) > 0),
            "g7_role_share": round(g["role_log"][-1]["role"] / max(1, g["role_log"][-1]["adults"]), 3) if g.get("role_log") else 0.0}
