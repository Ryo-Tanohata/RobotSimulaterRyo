"""G7 (王と役所) から働く仕組み (docs/society_phase/G7_design.md。2026-10-16 本人が「すべておすすめで」決めた)

- G7 に入るのは step.py next_part だけ (第 4 部の終わりで止まり、まとめのあと本人が「進めて」と言ってから)。
  G6 までは、このファイルを読みこみもしない (era2 は state["era2"] に "g7" があるときだけ、関数の中で読みこむ)。
  だから G1〜G6 は、お題・state・出来事・乱数が前と 1 バイトも変わらない (tools/test_g7.py で確かめる)
- ここにあるもの (土台): G7 の state の形 (4.H)・G7 に入る (4.E.1)・止まるわけ (4.E.2)・史実のずれの直し (4.E.4。束 A・6〜8・9.1。
  どれも G7 に入った日から)・まわりの集落の土台 (地図・はじめの集落・地域の天気。region.py)・役の仕事の日数 (4.F の 1)
- 年 1 回の答えと見本の家 (4.A): 年の集まり (年の最後の日の終わりにお題を書き、夏のはじめに集まる)・寄る季節・集まり直し・見本の家と手本の家・
  答えのない季節 (年の予定と方針を当てはめる)・年のお題・お題に出す決まりの文 (4.F の 8) と、欄が初めてお題に出た日
- 地域の 1 年 (4.B)・よその便り (4.C)・物差し (4.D)・つなぎ目のほかのもの (4.F) は、このあとで足す。
  季節の終わりの順 (4.G.1) は season_end に、次の歩のはじめの順は begin に、その順で足していく
- 乱数の塩 (4.G.2) は era2 の頭 (HINT_SALT など)。ここで使うのは 53 (地域の天気)・61 (見本の家)・79 (はじめの集落。G7 に入る日だけ)
"""
import json
import math
from pathlib import Path

import characters
import era2
import hints
import knowledge  # noqa: F401  (年の集まりの掟と知識は era2.apply_answers のまま)
import region
import world
import yardstick
from world import UNITS, log, season

SEASON_DAYS, YEAR = era2.SEASON_DAYS, era2.YEAR
ACTS7 = world.ACTS7  # 守る・取り立てる・戦に出る・試す (4.F の 1)
ROLE_ACTS = ("記録をつける", "取り立てる", "守る", "戦に出る")  # 役の仕事 (試すは入れない。4.F の 1)
ROLE_DAYS = 20  # 役の人 (1 年): 前の 1 年 (4 季節) に、役の仕事を合わせて 20 日以上 (4.F の 1 の表)
CARDS = Path(__file__).parent / "hint_cards.json"  # よその便りの札の表 (4.C.1。まだなければ、読めるかだけを見る)
# 史実のずれの直し (4.E.4。数は【仮定】。docs/society_phase/fidelity_checklist.md)
TREE_PER_H, REAP_PER_H, EVE_TIRE = 20, 30, 0.05  # A1a: 夕方の 1 時間で、木から 20 つかみ・刈る 30 つかみ。疲れは 1 時間に 0.05
MILK_PER = 3  # A4: 母ヤギ 1 頭から 1 日 3 杯 (その日に世話をした人で分ける)
KID_AGE, KID_ACTS = (12, 14), ("畑仕事", "ヤギの世話")  # 6: 12〜14 歳の子の手伝い
KID_H = (world.DAY_END - world.DAY_START - 1) / 2  # 6: 働きは大人の半分 (キャンプで働く大人の 12 時間の半分)
FIELD_BAD, PASTURE_BAD = 0.5, 0.8  # 8: 村が悪い年は、その夏の畑の比 ×0.5・草で養えるヤギの数 K ×0.8
POT_NORM, SICKLE_NORM = 2, 0.5  # 9.1: 働いた日の帳簿の目安 (1 日に土器 2 個・鎌は 2 日に 1 本)
LEDGER_KEEP = 8  # 9.1: 帳簿は新しい 8 季節分を state に残す (記録は data/records/ に)
LEDGER_ROWS = 15  # 9.1: お題に出す帳簿の行 (1 つの帳簿に 15 行まで。のこりは数だけ)
# 止まるわけ (4.E.2)
PART_YEARS = {5: 60}  # 部の年数の「止めて相談する目安」(計画 2.(c)。第 5 部は 60 年)
STALL_ASK, STALL_STOP = 8, 16  # 条件ごとの止まり: 8 年進まなければ報告で相談、16 年で止めて相談 (g7.stall は物差しの部分が数える)
# 出来事 → その日の仕事 (step.py・tools/build_records.py の ACT_BY_EVENT と同じ読み方。G7 の役の仕事も)
ACT_OF_EVENT = {"採集": "採集", "探索": "探索", "休む": "休む", "道具": "道具づくり", "火": "火おこし", "種まき": "種まき",
                "畑仕事": "畑仕事", "ヤギの世話": "ヤギの世話", "ヤギを捕まえる": "ヤギを捕まえる", "土器": "土器づくり", "住まい": "住まいを建てる",
                "交換に行く": "交換に行く", "記録をつける": "記録をつける", "守る": "守る", "取り立てる": "取り立てる", "戦に出る": "戦に出る", "試す": "試す"}
ROLE_TEXT = {"守る": "{n} がキャンプで見張りをした", "取り立てる": "{n} が、取り立てに回る支度をした",
             "戦に出る": "{n} がキャンプで戦の支度をした", "試す": "{n} がキャンプで、よその便りで聞いたことを試した"}
# お題に出す決まりの文 (era2.FACTS_G7) を出すとき (4.F の 8 の「出すとき」)。下の FACTS_ON (年 1 回の答えの節) で決める


def _g(state):
    return state["era2"]["g7"]


def fix(state):
    return era2._fix(state)


def _no(o):
    """集落の番号 (N12 → 12)。集落の番号の順に並べるため"""
    return int(o["id"][1:])


def _others(state):
    return sorted((state["era2"].get("g6") or {}).get("others", []), key=_no)


# ---------------- G7 に入る (step.py next_part。4.E.1) ----------------

def can_enter(state):
    """G7 に入れるかを確かめる (state と地図と札の表だけ。答えのフォルダは step.py が見る)。入れないときは、わけの文"""
    try:
        if region.SIZE != 11 or any(len(r) != region.SIZE or set(r) - set(region.K) for r in region.GRID):
            return "地図 (region.REGION_MAP) の形がおかしい"
    except Exception as ex:  # 読めない地図では入らない
        return f"地図 (region.REGION_MAP) が読めない ({type(ex).__name__})"
    if CARDS.exists():
        try:
            json.loads(CARDS.read_text(encoding="utf-8"))
        except (OSError, ValueError) as ex:
            return f"札の表 ({CARDS.name}) が読めない ({type(ex).__name__})"
    if "g7" in state["era2"]:
        return "G7 にはもう入っている"
    return None


def enter(state, fill=0.0):
    """G7 に入る (step.py next_part から 1 回だけ。4.E.1 の 2〜5)。確かめるのは step.py と can_enter。
    乱数は、はじめの集落を置く塩 79 (fill > 0 のときだけ) と、この日が年の最後の日なら地域の天気の塩 53 を、この日に 1 回ずつ作る。
    (見本の家の塩 61 と最初の年の便りの塩 47 は、それぞれの部分を入れるときに、ここに足す)"""
    e2, D = state["era2"], state["day"]
    state["era"] = "G7"
    e2["g7"] = g = {
        "start": D, "fix_from": D + 1, "part": 5, "ends": {}, "hold": None,
        # 年 1 回の答え (4.A): 入った季節にすぐ年の集まりをし、年の終わりまでの「短い年」にする (4.A.8)。
        #   飢えで区切った日に入ったなら、寄る年の集まり (その年の残りも寄る。Z5)
        "ask": "年" if (D + 1) % SEASON_DAYS == 0 and world.G7_PARTS["year"] else "寄る", "answer_day": D, "since": e2.get("last_first", 0), "meet_first": None,
        "zoom": None if (D + 1) % SEASON_DAYS == 0 else {"year": (D + 1) // YEAR, "why": ["Z5"], "day": D},
        "plan": {}, "sample": {}, "weights": {}, "cells": {}, "donor": {}, "sample_hist": {}, "src": {}, "step": None, "last_plans": {},
        "region": {}, "offered": {},
        "past": [], "role_days": {}, "prev": {},  # 前の 1 年の仕事の日数 (役の人・前の年の予定。4.A.3・4.F の 1)
        "season_days": {}, "kid_jobs": {}, "herd0": _herd(state), "ledger": [], "consulted": [],
    }
    _region_start(state, fill)
    # この日が年の最後の日なら、地域の天気もこの日に引く (4.G.2)。村の夏の畑の比はもう決まっている (G6 の _field_season) ので、
    #   使うのは、まわりの悪い年と、草で養えるヤギの数 K の ×0.8 だけ
    if (D + 1) % YEAR == 0 and fix(state) and world.G7_PARTS["weather"]:
        w = _weather(state)
        for o in _others(state):
            o["bad"] = D if o["id"] in w["bad"] else None
    g["past"] = _past_from_events(state)
    _derive(g)
    if fix(state):
        vacant(state)  # 直し A3: 今ある分は、この日に 1 回だけ移す
    choose(state, era2._rng(state, era2.SAMPLE_SALT))  # 見本の家 (塩 61。この日に 1 回だけ作る。4.A.3)
    donors(state)
    hints.start(state)  # よその便り: 札の表のハッシュと、最初の年の便り (塩 47。この日に 1 回だけ作る。4.C)
    ind = era2.indicators(state)
    state["era_log"].append({"era": "G7", "day": D, "indicators": ind, "how": "next_part", "fix_from": D + 1})
    state["era_info"] = {"era": "G7", "name": era2.NAMES2["G7"], "next": era2.CRITERIA["G7"][0], "met": False, "since": 0, "indicators": ind}
    state["hold"] = False
    # 「フェーズが…に進んだ」の形にはしない (ワークフローが止まらないように。start2 と同じ形)
    log(state, "フェーズ", None, f"第 5 部「{era2.PARTS[5]}」を始めた: フェーズ G7 ({era2.NAMES2['G7']})")
    _offer(state)
    return g


def close_g6(state, note):
    """G6 を本人の決めで閉じる (町の条件がそろわないまま。2026-10-17 本人「町は生まれなかったとして G6 を閉じる」)。
    step.py next_part --closed-by-decision から、G7 に入る前に 1 回だけ。出来事「フェーズ」と g6.closed に残す (本人の言葉は data と g6.closed に。
    文は村の人の年のまとめにも出るので、作る側のことばは入れない)。乱数は使わない"""
    g6, D = era2._g6(state), state["day"]
    ind = era2.indicators(state)
    c = {"day": D, "by": "本人の決め", "note": note, "town": ind.get("g6_town_day"), "record": ind.get("g6_record_day")}
    g6["closed"] = c
    log(state, "フェーズ", None, "第 4 部の終わり (G6): 町の条件はそろわないまま、ここで閉じた"
        + (f" (記録は {c['record']} 日目にそろった)" if c["record"] is not None else ""), closed_by="本人の決め", note=note, town=c["town"], record=c["record"])
    return c


def enter_next(state):
    """次の G の待ち・部の終わりから、次の G に入る (G8 から。その G のコードを入れたあと)。G7 に入るのは enter"""
    e2, D, g = state["era2"], state["day"], _g(state)
    nxt = era2.ORDER2[era2.ORDER2.index(state["era"]) + 1]
    state["era"] = nxt
    ind = era2.indicators(state)
    state["era_log"].append({"era": nxt, "day": D, "indicators": ind, "how": "next_part"})
    state["era_info"] = {"era": nxt, "name": era2.NAMES2[nxt], "next": era2.CRITERIA.get(nxt, ("(まだ作っていない)",))[0], "met": False, "since": 0,
                         "indicators": ind}
    state["hold"] = False
    g["hold"] = None
    n = era2.PART_START.get(nxt)
    if n:
        g["part"], g["part_start"] = n, D
        log(state, "フェーズ", None, f"第 {n} 部「{era2.PARTS[n]}」を始めた: フェーズ {nxt} ({era2.NAMES2[nxt]})")
    else:
        log(state, "フェーズ", None, f"フェーズ {nxt} ({era2.NAMES2[nxt]}) を始めた")
    return nxt


def _add_keys(o, cell):
    """まわりの集落に G7 の鍵を足す (4.B.2。G6 の鍵はそのまま。牛は小数。土器と鎌も端数を残す)"""
    o.update({"cell": list(cell), "land": region.land(cell), "parent": None, "org": 0, "commit": {}, "stance": "ふつう",
              "walls": None, "tech": 1, "head_age": 0, "cattle_f": o["people"] / region.CATTLE_PER,
              "pots_f": float(o["pots"]), "sickles_f": float(o["sickles"])})


def new_other(state, o):
    """G7 に入ったあとに G6 の決まりでできた集落 (村を出た家の村など) に、地図のますと G7 の鍵を足す (era2._new_other から。乱数なし)。
    村から 2 ます以内なら、村が知っている (4.B.2)"""
    used = {tuple(x["cell"]) for x in _others(state) if x.get("cell")}
    c = region.place_known(o["dir"], o["days"], used)
    _add_keys(o, c)
    if o["kind"] == "分かれた家":
        o["parent"] = "V0"
    if o["known"] is None and region.dist(c, region.VILLAGE) <= region.KNOWN_NEAR:
        o["known"] = state["day"]


def _new_settlement(state, cell, n):
    """はじめの集落 (G6 の _new_other の形。種類「よその村」。方角は 8 方向、日数は ます数 ÷ 2 の切り上げ。2 ます以内なら村が知っている)"""
    g6, D = era2._g6(state), state["day"]
    d = region.direction(cell)
    name = f"{d}の村"
    if any(o["name"] == name for o in g6["others"]):
        name = f"{name}{g6['next_other']}"
    o = {"id": f"N{g6['next_other']}", "name": name, "kind": "よその村", "household": None, "dir": d, "way": region.DIRS8[d][0],
         "days": region.days(cell), "edge": list(region.DIRS8[d][1]), "since": D,
         "known": D if region.dist(cell, region.VILLAGE) <= region.KNOWN_NEAR else None, "people": n,
         "goats": round(n * 0.4), "grain": n * 100, "pots": n // 4, "sickles": n // 8, "obsidian": 0, "has_obsidian": False,
         "bad": None, "trust": 0.5, "contacts": []}
    g6["next_other"] += 1
    g6["others"].append(o)
    _add_keys(o, cell)
    return o


def _region_start(state, fill):
    """まわりの集落の土台 (4.B.1・4.B.2): 地図のしるし、G6 からある集落のます、はじめの集落 (fill > 0 のときだけ。塩 79)"""
    g, D = _g(state), state["day"]
    reg = g["region"] = {"map_hash": region.map_hash(), "weather": None, "weather_log": [], "ties": [], "wars": [], "demands": [],
                         "yoru": {}, "councils": {}, "gone": [], "log": [], "seed": None, "next_war": 1, "pending": [], "fill": None}
    used = set()
    for o in _others(state):
        c = region.place_known(o["dir"], o["days"], used)
        used.add(c)
        _add_keys(o, c)
    have = sum(o["people"] for o in _others(state))
    if fill > 0:
        placed = [_new_settlement(state, c, n) for c, n in region.fill_cells(used, have, fill, era2._rng(state, era2.FILL_SALT))]
        reg["fill"] = {"share": fill, "day": D, "placed": [o["id"] for o in placed], "people": sum(o["people"] for o in placed),
                       "known": [o["id"] for o in placed if o["known"] is not None]}
    reg["log"].append({"day": D, "kind": "はじめ", "k": region.k_total(), "people": sum(o["people"] for o in _others(state)), "village": _pop(state),
                       "others": [[o["id"], o["cell"], o["people"]] for o in _others(state)]})


def _pop(state):
    return sum(1 for p in state["people"] if p["alive"])


def _past_from_events(state):
    """G7 に入る日: 前の 1 年 (120 日) の、人ごとの仕事の日数を、出来事から作る (step.py の day_summaries と同じ読み方。季節ごとに 1 つ)"""
    D = state["day"]
    lo = D - YEAR + 1
    homes = {p["name"]: p.get("household") for p in state["people"]}
    by, seen = {}, set()
    for e in state["events"]:
        d = e["day"]
        if d < lo or d > D:
            continue
        t = e["type"]
        names = (e.get("data") or {}).get("hunters") if t == "狩り" else [e.get("who")]
        act = "狩り" if t == "狩り" else "交換に行く" if t == "交換" and e.get("who") else ACT_OF_EVENT.get(t)
        if not act or not names:
            continue
        end = d // SEASON_DAYS * SEASON_DAYS + SEASON_DAYS - 1
        for n in names:
            if not n or (n, d) in seen:
                continue
            seen.add((n, d))
            row = by.setdefault(end, {})
            row.setdefault(n, {})[act] = row.get(n, {}).get(act, 0) + 1
    return [{"day": end, "season": season(end), "days": by[end], "home": {n: homes.get(n) for n in sorted(by[end])}} for end in sorted(by)]


def _derive(g):
    """前の 1 年の仕事の日数から、役の人の日数 (role_days) と、家ごと季節ごとの仕事の日数 (prev) を作る"""
    role, prev = {}, {}
    for s in g["past"]:
        for n, acts in s["days"].items():
            for a, d in acts.items():
                if a in ROLE_ACTS:
                    role.setdefault(n, {})[a] = role.get(n, {}).get(a, 0) + d
                h = s["home"].get(n)
                if h:
                    row = prev.setdefault(h, {}).setdefault(s["season"], {})
                    row[a] = row.get(a, 0) + d
    g["role_days"], g["prev"] = role, prev


def role_people(state):
    """役の人 (1 年): 前の 1 年に、役の仕事を合わせて 20 日以上した、生きている大人 (4.F の 1)"""
    alive = {p["name"] for p in era2.adults(state)}
    return sorted(n for n, acts in _g(state).get("role_days", {}).items() if n in alive and sum(acts.values()) >= ROLE_DAYS)


# ---------------- 季節 ----------------

def acts(state):
    """G7 の役の仕事のうち、今選べるもの (4.F の 1)。守るはいつも。取り立てるは税の掟があるとき、戦に出るは村の戦が決まった季節、
    試すは開いた技術の札があるとき (それぞれの仕組みを入れた部分が、ここで見る state を作る)"""
    g = _g(state)
    on = {"守る"}
    if any(l.get("status") == "採用" and l.get("tax") for l in state.get("laws", [])):
        on.add("取り立てる")
    if g.get("war_season"):
        on.add("戦に出る")
    if g.get("hints") and hints.open_techs(state):
        on.add("試す")
    return [a for a in ACTS7 if a in on]


def new_season(state):
    """季節のはじめ (答えを当てはめる前): この季節の仕事の日数・子の手伝い・季節のはじめのヤギの数・G7 の仕事のくわしい答えを空にする"""
    g = _g(state)
    g["season_days"], g["kid_jobs"], g["herd0"], g["jobs7"] = {}, {}, _herd(state), {}
    sick_start(state)  # 4.F の 7: これからの季節が病の季節なら、出来事「病」


def job(state, q, j):
    """G7 の仕事のくわしい答え (era2.apply_answers から。e2["jobs"] には入れない): 試す (try。開いた札を知っている人だけ。ちがえば「休む」)・
    住まいを建てる (build: "壁")・畑仕事 (plough: true)・交換に行く (want に「牛」)"""
    g, act = _g(state), q["plan"]["activity"]
    j = j if isinstance(j, dict) else {}
    out = {}
    if act == "試す":
        card = str(j.get("try") or "").strip().upper()
        if hints.can_try(state, q["name"], card, (q.get("plan") or {}).get("with")):
            out["try"] = card
        else:
            q["plan"]["activity"] = "休む"
    elif act == "住まいを建てる" and "壁" in str(j.get("build") or ""):
        out["build"] = "壁"
    elif act == "畑仕事" and era2._yes(j.get("plough")) and _plough(state):
        out["plough"] = True
    elif act == "交換に行く" and "牛" in str(j.get("want") or ""):
        out["want"] = "牛"
    elif act == era2.ACT_RECORD and isinstance(j.get("laws"), list):
        out["laws"] = [f"L{era2._num(x)}" for x in j["laws"] if era2._num(x) or str(x).strip() in ("L0", "0")][:20]
    if out:
        g.setdefault("jobs7", {})[q["name"]] = out


def kid_age(c):
    """12〜14 歳の子か (直し 6)"""
    return bool(c.get("child")) and KID_AGE[0] <= c["age"] <= KID_AGE[1]


def _kid(state, name):
    return next((c for c in era2.children(state) if c["name"] == name and kid_age(c)), None)


def kid_jobs(state, rep, fjobs):
    """直し 6: 家の代表が family で、12〜14 歳の子に「畑仕事」か「ヤギの世話」を割り振った (書かなかった子は働かない)"""
    if not fix(state):
        return
    h = rep.get("household")
    for c in era2.children(state):
        if not h or c.get("household") != h or not kid_age(c):
            continue
        j = fjobs.get(c["name"])
        act = j.get("activity") if isinstance(j, dict) else j if isinstance(j, str) else None
        if act in KID_ACTS:
            _g(state)["kid_jobs"][c["name"]] = act


def count_day(state, name, act):
    """人ごとの、この季節の仕事の日数 (役の人・前の年の予定・働いた日の帳簿)"""
    d = _g(state).setdefault("season_days", {}).setdefault(name, {})
    d[act] = d.get(act, 0) + 1


def role_day(state, p, t, act):
    """G7 の役の仕事の 1 日 (守るは見張るだけで、何も作らない。取り立てるは季節の終わりに集める。戦に出るは戦の日に出かける。試すは hints.try_day)"""
    if act == "試す":
        hints.try_day(state, p, t)
        return
    t.setdefault("events", []).append(log(state, act, p["name"], ROLE_TEXT[act].format(n=p["name"])))


def hint_settled(state, v, accepted):
    hints.settled(state, v, accepted)


def hint_offer(state, c6, off, o, n, lead, how):
    hints.thing_offer(state, c6, off, o, n, lead, how)


def craft_step(state, p, act, base):
    return hints.craft_step(state, p, act, base) if _g(state).get("hints") else base


def milk_shares(state, sea):
    """直し A4: 1 日の乳は「3 杯 × 母ヤギ (1 歳以上のメス) の数」で、その日に世話をした人で分ける (12〜14 歳の子は大人の半分の重み)。
    整数で分け、端数は余りの大きい人から (同じなら並びの前から)。乱数なし。春と夏だけ。戻り値: {名前: 杯}"""
    if sea not in ("春", "夏"):
        return {}
    e2 = state["era2"]
    total = MILK_PER * sum(1 for g in e2["goats"] if g["sex"] == "メス" and state["day"] - g["born"] >= YEAR)
    who = [(p["name"], 2) for p in era2.adults(state) if (p.get("today") or {}).get("activity") == "ヤギの世話"]
    who += [(n, 1) for n, a in sorted(_g(state).get("kid_jobs", {}).items()) if a == "ヤギの世話" and _kid(state, n)]
    w = sum(x for _, x in who)
    if not w:
        return {}
    out = {n: total * x // w for n, x in who}
    for n, x in sorted(who, key=lambda nx: -(total * nx[1] % w))[:total - sum(out.values())]:
        out[n] += 1
    return out


def kids_day(state, sea, rng, milk):
    """直し 6: 12〜14 歳の子の手伝い (割り振られた子だけ。働きは大人の半分。world の 1 時間ずつの計算には入れない)"""
    e2 = state["era2"]
    for name, act in sorted(_g(state).get("kid_jobs", {}).items()):
        c = _kid(state, name)
        if not c:
            continue
        if act == "畑仕事":
            era2._field_work(state, c, {"activity": act, "work_h": KID_H}, {}, sea, rng)
            log(state, "畑仕事", name, f"{name} ({c['age']} 歳) がキャンプのそばの畑で手伝った", child=True)
        else:
            e2["tended_run"] = e2.get("tended_run", 0) + 0.5
            log(state, "ヤギの世話", name, f"{name} ({c['age']} 歳) がヤギの世話を手伝った", child=True)
            cups = (milk or {}).get(name, 0)
            if cups:  # 子は自分の食べ物を持たないので、しぼった乳は村の蓄えに入れる
                state["store"].append({"kind": "乳", "kcal": cups * UNITS["乳"][1], "day": state["day"], "sown": True})
                log(state, "乳", name, f"{name} がヤギの乳を {cups} 杯しぼり、村の蓄えに入れた", amount=cups, child=True)
        count_day(state, name, act)


def evening_cost(state, reaped):
    """直し A1a: 夕方の 1 時間で、木から 20 つかみ・刈る 30 つかみ。使った時間を次の日の働く時間 (world の work_h) から引き、
    疲れを 1 時間に 0.05 足す。乱数なし。木から取った量は world.evening が today の tree_got に残す"""
    for p in era2.adults(state):
        t = p.get("today") or {}
        h = t.get("tree_got", 0) / TREE_PER_H + reaped.get(p["name"], 0) / REAP_PER_H
        if h > 0:
            h = round(h, 2)
            t["eve_h"] = p["eve_h"] = h
            p["fatigue"] = round(min(1.0, p["fatigue"] + EVE_TIRE * h), 2)


def _herd(state):
    """持ち主 (家か「村」) ごとの、ヤギの数"""
    out = {}
    for g in state["era2"]["goats"]:
        k = g.get("owner") or "村"
        out[k] = out.get(k, 0) + 1
    return out


def vacant(state):
    """直し A3: 生きている人がいない家 (G5 で村を出た家は除く) の倉・ヤギ・畑を、村のものにする (季節の終わりと、G7 に入る日。乱数なし)"""
    e2 = state["era2"]
    alive = {p.get("household") for p in state["people"] if p["alive"]}
    left = {f["household"] for f in (e2.get("g5") or {}).get("fissions", [])}
    fields = [f for f in e2["fields"] if f["state"] in ("育つ", "実った")]
    homes = set(e2.get("house", {})) | {g.get("owner") for g in e2["goats"]} | {f.get("owner") for f in fields}
    for h in sorted(x for x in homes if x and x != "-" and x not in alive and x not in left):
        store = (e2.get("house", {}).get(h) or {}).get("store") or []
        goats = [g for g in e2["goats"] if g.get("owner") == h]
        mine = [f for f in fields if f.get("owner") == h]
        if not (store or goats or mine):
            continue
        what = "・".join(x for x in (("倉 (" + world.food_words(world.holdings({"food": store})) + ")") if store else "",
                                     f"ヤギ {len(goats)} 頭" if goats else "", f"畑 {len(mine)} 枚" if mine else "") if x)
        kcal = {}
        for f in store:
            kcal[f["kind"]] = kcal.get(f["kind"], 0) + f["kcal"]
        state["store"].extend(store)
        if store:
            e2["house"][h]["store"] = []
        for g in goats:
            g["owner"] = None
        for f in mine:
            f["owner"] = None
        log(state, "受けつぎ", None, f"{h}にはだれも暮らしていないので、{what}は村のものになった",
            household=h, kcal=kcal, goats=[g["id"] for g in goats], fields=[f["id"] for f in mine])


# ---------------- 地域の天気 (直し 8。4.B.3 の 1) ----------------

def _weather(state):
    """地域の天気を引く (塩 53。年の最後の日に 1 回。同じ年に 2 回は引かない)。引く順: z → 村 (V0) → 集落の番号の順"""
    reg = _g(state)["region"]
    y = (state["day"] + 1) // YEAR  # これからの年
    if reg.get("weather") and reg["weather"]["year"] == y:
        return reg["weather"]
    places = [("V0", region.VILLAGE)] + [(o["id"], tuple(o["cell"])) for o in _others(state) if o.get("cell")]
    z, rbad, bad = region.weather(era2._rng(state, era2.WEATHER_SALT), places)
    w = {"year": y, "day": state["day"], "z": round(z, 4), "region_bad": rbad, "bad": bad}
    reg["weather"] = w
    reg["weather_log"].append(dict(w))
    return w


def weather_day(state):
    """era2._field_season から (年の最後の日)。戻り値: 村が悪い年か (その夏の畑の比を半分にする)"""
    if not (fix(state) and world.G7_PARTS["weather"]):
        return False
    return "V0" in _weather(state)["bad"]


def bad_set(state):
    """era2._g6_season_end から (年の最後の日の季節の終わり): 地域の天気で悪い年になった集落の番号 (天気を止めているときは None = G6 の決まりのまま)"""
    if not (fix(state) and world.G7_PARTS["weather"]):
        return None
    w = _g(state)["region"].get("weather")
    return set(w["bad"]) if w and w["year"] == (state["day"] + 1) // YEAR else None


def _bad_year(state, year):
    return any(w["year"] == year and "V0" in w["bad"] for w in _g(state)["region"].get("weather_log", []))


def pasture(state, cap):
    """era2.pasture_cap から: 村が悪い年 (その日の年) は、草で養えるヤギの数 K を ×0.8 (10 頭単位)。牛 1 頭はヤギ 5 頭分の草を食べる (4.F の 5)"""
    if fix(state) and world.G7_PARTS["weather"] and _bad_year(state, state["day"] // YEAR):
        cap = int(round(cap * PASTURE_BAD / 10)) * 10
    return max(0, cap - CATTLE_GOATS * len(state["era2"].get("cattle") or []))


# ---------------- 記録 (直し 9.1: 配給・働いた日・家畜の帳簿) ----------------

def whats(state):
    """G7 で足す記録の種類: 取り立て (村の中の税と貢ぎの出入り。4.D.3)、粘土の板が使えるとき 掟 (板に書く。4.F の 3) と 配給・働いた日・家畜 (直し 9.1)"""
    board = bool(((state["era2"].get("g6") or {}).get("open") or {}).get("板"))
    return (("取り立て",) if joints(state) else ()) + (("掟",) if joints(state) and board else ()) + \
        (("配給", "働いた日", "家畜") if fix(state) and board else ())


def _workdays(state):
    """この季節の、人ごとの働いた日 (休むは数えない)"""
    return {n: {a: d for a, d in acts.items() if a != "休む"} for n, acts in sorted(_g(state).get("season_days", {}).items())}


def ledger_need(state, flow, ws):
    """帳簿に要る数え札の数 (era2.TOKEN と同じ数え方: 草の種 100 つかみ・働いた日 10 日・ヤギ 1 頭に 1 個)"""
    need = {}
    if "取り立て" in ws:  # この季節の取り立て (税と貢ぎの出入り): 草の種 100 つかみに 1 個・ヤギ 1 頭に 1 個 (era2.TOKEN と同じ)
        tot = {}
        for c in _g(state).get("coll") or []:
            for k, n in c["goods"].items():
                tot[k] = tot.get(k, 0) + n
        need["取り立て"] = sum(math.ceil(n / era2.TOKEN.get(k, 100)) for k, n in tot.items())
    if "掟" in ws:
        need["掟"] = 0  # 掟は数え札ではなく、記録をつけた日 1 日に 1 本 (write_laws)
    if "配給" in ws:
        need["配給"] = math.ceil(math.fsum(v[1] for v in flow.values()) / era2.GRAIN / era2.TOKEN["草の種"])
    if "働いた日" in ws:
        need["働いた日"] = math.ceil(sum(sum(a.values()) for a in _workdays(state).values()) / era2.TOKEN["日"])
    if "家畜" in ws:
        need["家畜"] = math.ceil(len(state["era2"]["goats"]) / era2.TOKEN["ヤギ"])
    return need


def _made(state, since):
    """この季節に、人ごとに作った土器と鎌 (出来事から)"""
    out = {}
    for e in reversed(state["events"]):
        if e["day"] < since:
            break
        n = (e.get("data") or {}).get("count")
        if e.get("who") and n and e["type"] in ("土器", "道具"):
            row = out.setdefault(e["who"], {})
            k = "土器" if e["type"] == "土器" else "鎌"
            row[k] = row.get(k, 0) + n
    return out


def ledger(state, full, how, flow):
    """直し 9.1: 全部残せた帳簿を、【村】の帳簿 (g7.ledger) に残す。決めた目安と、実際の量 (記録をつける人が見た量だけ。乱数なし)"""
    g, e2, D = _g(state), state["era2"], state["day"]
    sd = e2["step_day"]
    n_days = D - sd + 1
    books = []
    if "配給" in full:
        ads = {}
        for p in era2.adults(state):
            ads[p.get("household")] = ads.get(p.get("household"), 0) + 1
        rows = [{"household": h, "adults": ads.get(h, 0), "norm": ads.get(h, 0) * n_days * era2.DAY_FOOD // era2.GRAIN, "out": round(v[1] / era2.GRAIN)}
                for h, v in sorted(flow.items())]
        books.append({"what": "配給", "how": how["配給"], "days": n_days, "per_day": era2.DAY_FOOD // era2.GRAIN, "rows": rows})
    if "働いた日" in full:
        made = _made(state, sd)
        rows = []
        for n, work in _workdays(state).items():
            if not work:
                continue
            row = {"who": n, "days": work}
            if work.get("土器づくり"):
                row["pots"] = [work["土器づくり"] * POT_NORM, made.get(n, {}).get("土器", 0)]
            if work.get("道具づくり"):
                row["sickles"] = [math.floor(work["道具づくり"] * SICKLE_NORM), made.get(n, {}).get("鎌", 0)]
            rows.append(row)
        books.append({"what": "働いた日", "how": how["働いた日"], "rows": rows})
    if "家畜" in full:
        h0, now = g.get("herd0") or {}, _herd(state)
        rows = []
        for k in sorted(set(h0) | set(now), key=lambda k: (k != "村", k)):
            mine = [x for x in e2["goats"] if (x.get("owner") or "村") == k]
            mothers = sum(1 for x in mine if x["sex"] == "メス" and D - x["born"] >= YEAR)
            born = sum(1 for x in mine if sd <= x["born"] <= D)
            rows.append({"owner": k, "start": h0.get(k, 0), "now": now.get(k, 0), "mothers": mothers, "born": born,
                         "norm": mothers if season(D + 1) == "春" else 0})  # 目安: 春のはじめに、母ヤギ 1 頭に子 1 頭
        books.append({"what": "家畜", "how": how["家畜"], "rows": rows})
    if books:
        g["ledger"] = (g.get("ledger", []) + [{"day": D, "books": books}])[-LEDGER_KEEP:]


def _ledger_text(state):
    """お題の「板の帳簿」(前の季節に全部残せた帳簿だけ。【村】)"""
    led = _g(state).get("ledger") or []
    last = led[-1] if led and led[-1]["day"] == state["day"] else None
    if not last:
        return ""
    out = []
    for b in last["books"]:
        rows = b["rows"]
        if b["what"] == "配給":
            txt = [f"{r['household']} 目安 {r['norm']}・出した {r['out']} つかみ" for r in rows]
            head = f"配給 (村の蓄えから家ごとに出した食べ物。目安は大人 1 人 1 日 草の種 {b['per_day']} つかみ分 × {b['days']} 日)"
        elif b["what"] == "働いた日":
            txt = [f"{r['who']} " + "・".join(f"{a} {d} 日" for a, d in r["days"].items())
                   + (f" (土器 目安 {r['pots'][0]}・できた {r['pots'][1]} 個)" if "pots" in r else "")
                   + (f" (鎌 目安 {r['sickles'][0]}・できた {r['sickles'][1]} 本)" if "sickles" in r else "") for r in rows]
            head = "働いた日 (人ごとの働いた日。土器は 1 日 2 個、鎌は 2 日で 1 本を目安に)"
        else:
            txt = [f"{r['owner']} ヤギ {r['start']} → {r['now']} 頭 (母ヤギ {r['mothers']} 頭"
                   + (f"。生まれた子 {r['born']} 頭 / 目安 {r['norm']} 頭" if r["norm"] or r["born"] else "") + ")" for r in rows]
            head = "家畜 (村と家ごとのヤギ。子は春のはじめに、母ヤギ 1 頭に 1 頭を目安に)"
        more = f"、ほか {len(txt) - LEDGER_ROWS}" if len(txt) > LEDGER_ROWS else ""
        out.append(f"- {head} ({b['how']}): " + ("、".join(txt[:LEDGER_ROWS]) + more if txt else "なし"))
    return "\n## 板の帳簿 (前の季節に、記録をつける人が全部残したもの)\n" + "\n".join(out) + "\n"


# ---------------- お題 ----------------

def facts(state):
    """お題の決まりの文のうち、今使えるもの (era2.FACTS_G7。4.F の 8)"""
    return "".join(era2.FACTS_G7[k] for k in era2.FACTS_G7 if k in FACTS_ON and FACTS_ON[k](state))


def _offer(state):
    """お題の欄 (と決まりの文) が初めてお題に出た日を残す (4.F の 8)。お題は保存のあとに書くので、季節の終わり (と G7 に入る日) に、次のお題に出るものを数える。
    お題を書くのは集まりの歩 (ask がある) だけなので、そのときだけ数える"""
    g = _g(state)
    if not g.get("ask"):
        return
    off = g.setdefault("offered", {})
    for k in [k for k in era2.FACTS_G7 if FACTS_ON[k](state)] + fields_on(state):
        off.setdefault(k, state["day"])


def text(state, p):
    """G7 のお題の節 (season_prompt の「ほかの村・印・記録」のあと): 板の帳簿・まわりの集落"""
    return _ledger_text(state) + region_text(state) + hints.text(state, p)


# 直しで変わった決まりの、お題の文の置きかえ (G7 に入ってから。前の文が見つからなければ何もしない)
FIX_TEXT = (
    ("その場所に 20 日ほどで木の実の木が育つ", "その場所に 3 年ほどで木の実の木が育つ"),  # A1b (characters._sowing)
    ("村の蓄えの草の種を土器に入れておくと、虫やネズミに食べられない (1 個に",
     "村の蓄えの草の種を土器に入れておくと、虫やネズミにほとんど食べられない (土器の中でも、1 年に 100 分の 3 ほどは傷む。1 個に"),  # A2 (FACTS_G3)
    ("春と夏は世話をすると乳がとれる。",
     "春と夏は世話をすると乳がとれる (1 日にとれる乳は母ヤギの数で決まり、世話をする人が多くても増えない。その日に世話をした人で分ける)。"),  # A4 (FACTS2)
    ("1 人 40 つかみまで", "1 人 40 つかみまで。夕方に取った分だけ、次の日に働ける時間が減り、疲れる (20 つかみで 1 時間ほど)"),  # A1a
    ("(harvest、つかみ、60 まで) を書ける (主な仕事とは別にできる)",
     "(harvest、つかみ、60 まで) を書ける (主な仕事とは別にできる。夕方に刈った分だけ、次の日に働ける時間が減り、疲れる。30 つかみで 1 時間ほど)"),  # A1a
)


# 年 1 回の答えで変わる決まりの、お題の文の置きかえ (寄る季節のお題。4.A.4 の 8)
YEAR_TEXT = (("加わった大人は、この季節は村でいちばん多い仕事をし、次の季節から自分で決める",
              "加わった大人は、次の年の集まりまで、季節ごとに村でいちばん多い仕事をする"),)


def fix_text(state, text_):
    """季節と気持ちのお題を、直しのあとの決まりの文 (と、年 1 回の答えの文) にする"""
    if world.G7_PARTS["year"]:
        for a, b in YEAR_TEXT:
            text_ = text_.replace(a, b)
    if not fix(state):
        return text_
    for a, b in FIX_TEXT:
        text_ = text_.replace(a, b)
    return text_


# ---------------- 季節の終わり (era2._season_end から。G6 の季節の終わりのあと。4.G.1) ----------------

def season_end(state, frac):
    """G7 の季節の終わり。順は 4.G.1 (8 地域の 1 年 → 9 病 → 10 見本の家 → 11 便り → 12 きっかけ → 13 物差しと次の歩の ask)。
    8・9・11・12 と 13 の物差しは、それぞれの部分を入れるときに、ここに足す"""
    g, D = _g(state), state["day"]
    if region_on(state):
        drop_gone(state)  # 戦の日になくなった集落で、交換に行く途中の人がいた分 (G6 の季節の終わりで帰った)
    homes = {p["name"]: p.get("household") for p in state["people"]}
    days = g.get("season_days") or {}
    g["past"] = [s for s in g.get("past", []) if s["day"] > D - YEAR] + [  # 前の 1 年 (120 日) の季節だけ (途中で区切った季節も 1 つ)
        {"day": D, "season": season(D), "days": days, "home": {n: homes.get(n) for n in sorted(days)}}]
    _derive(g)
    if (D + 1) % YEAR == 0:
        region_year(state)  # 8. 地域の 1 年 (塩 59) → 9. 病 (塩 71)・寄る年の目印 region.yoru
        year_turn(state)  # 10. 寄るか → 見本の選び直し → 手本 (塩 61)
    hints.season_end(state)  # 11. よその便り (塩 47): 年の終わりなら次の年の分 → 捕らえた職人 → この季節に届く便り
    hints.chance(state)  # 12. 年の終わりだけ: きっかけ (塩 67)
    yardstick.season_end(state, frac)  # 13. 物差し (乱数なし)
    ask_next(state)  # 13. 次の歩で答えが要るか (物差しは物差しの部分)
    _offer(state)


# ---------------- 判定と止まるわけ (era2.check から。4.E.2) ----------------

def check(state, met, ind):
    """G7 からの判定: True (フェーズが進んだ) / "end" (部の終わり) / "entrance" (工業の入口) / "wait" (次の G のコードを待つ) / "consult" / False。
    部の終わり・待ち・入口は、一度だけ返す (そのあとは条件がそろっていても進まない。進むのは next_part だけ)"""
    g, era, D = _g(state), state["era"], state["day"]
    if met:
        if era in era2.PART_END:
            if era in g["ends"]:
                return False
            code = "entrance" if era == "G14" else "part_end"
            g["ends"][era] = {"day": D, "why": code}
            g["hold"] = {"why": code, "era": era, "day": D}
            return "entrance" if code == "entrance" else "end"
        i = era2.ORDER2.index(era)
        if i + 1 < len(era2.ORDER2):
            nxt = era2.ORDER2[i + 1]
            state["era"] = nxt
            state["era_log"].append({"era": nxt, "day": D, "indicators": ind})
            state["era_info"] = {"era": nxt, "name": era2.NAMES2[nxt], "next": era2.CRITERIA.get(nxt, ("(まだ作っていない)",))[0], "met": False,
                                 "since": 0, "indicators": ind}
            g["hold"] = {"why": "phase", "era": nxt, "day": D}
            return True
        if era in g["ends"]:
            return False
        g["ends"][era] = {"day": D, "why": "wait"}
        g["hold"] = {"why": "wait", "era": era, "day": D}
        return "wait"
    c = consult_why(state)
    if c:
        g.setdefault("consulted", []).append(c)
        g["hold"] = {"why": "consult", "era": era, "day": D, "what": c["text"]}
        return "consult"
    return False


def consult_why(state):
    """止めて相談するか (年の終わりだけ。一度ずつ): 部の年数が目安をこえた / どれかの条件が 16 年進まない (g7.stall。物差しの部分が数える)"""
    g, D = _g(state), state["day"]
    if (D + 1) % YEAR:
        return None
    done = g.setdefault("consulted", [])
    part = g.get("part", 5)
    start = g.get("part_start", g["start"])
    yrs = (D + 1 - start) // YEAR
    if yrs >= PART_YEARS.get(part, 10 ** 9) and not any(c["why"] == "years" and c.get("part") == part for c in done):
        return {"why": "years", "part": part, "day": D, "text": f"第 {part} 部に入って {yrs} 年たった (目安 {PART_YEARS[part]} 年)"}
    y = (D + 1) // YEAR
    for k, s in sorted((g.get("stall") or {}).items()):
        if s.get("done") or y - s["since"] < STALL_STOP:
            continue
        if not any(c["why"] == k and c.get("since") == s["since"] for c in done):
            return {"why": k, "since": s["since"], "day": D, "text": f"条件 {k[1:]} が {y - s['since']} 年進んでいない"}
    return None


def reached(state, f):
    """G7 の F に届いたか (物差しの部分が g7.reached に日を残す)"""
    return bool((_g(state).get("reached") or {}).get(f))


def indicators(state):
    """G7 の目安 (G7 に入ってから。条件の 3 つ (4.D.1) と、この部分で数えるもの)"""
    g = _g(state)
    sub = {x["f"]: x["day"] for x in state["era2"].get("substeps", []) if x["g"] == "G7"}
    return {"g7_on": True, "g7_f3_day": sub.get("F3"), "g7_tribute2_day": g.get("tribute2_day"), "g7_f4_day": sub.get("F4"),
            "g7_role_people": len(role_people(state)), "g7_others": len(_others(state)),
            "g7_region_people": sum(o["people"] for o in _others(state)), **yardstick.indicators(state)}


# ---------------- 年 1 回の答えと見本の家 (4.A) ----------------
# 答えを集めるのは、年の集まり (年の最後の日の終わりにお題を書き、夏のはじめに集まる) と、前もって決めた「寄る」季節だけ。
#   ほかの季節は、年の答えの「その季節の予定」と「1 年の方針」を当てはめる (apply_plan)。世界の計算・歩・コミット・記録の行は 1 季節ずつのまま
# 答えるのは見本の家の代表とまとめ役。見本でない家は、同じ組の手本の家の答えをまね、票はその家の大人の数で数える
#   (だから多数決は今のまま「生きている大人みんなの半分をこえるか」)。見本であることは、お題に書かない (村の中の仕組みではないため)
SAMPLE_SHARE, SAMPLE_MIN, SAMPLE_MAX, SAMPLE_YEARS, ZOOM_DAYS = 0.4, 12, 25, 3, 30  # 【仮定】4.A.3・4.A.7
SEASONS = ("夏", "秋", "冬", "春")  # 年の集まり (夏のはじめ) からの順
WEALTH = ("なし", "少し", "多い")  # 豊かさの組 (era2.wealth が 0 / 0 より多い家のうち真ん中より下 / 上)
WORK = (("集める", ("採集", "狩り", "探索", "休む", "火おこし", "種まき")),
        ("畑", ("畑仕事", "ヤギの世話", "ヤギを捕まえる", "住まいを建てる")),
        ("作る", ("土器づくり", "道具づくり", "記録をつける", "交換に行く") + ACTS7))  # 仕事の組 (作る・記録・交換・役)
WORK_TIE = ("作る", "畑", "集める")  # 日数が同じで、代表の仕事でも決まらないとき (まれな立場を先に)
COPY_IF_DONE = ("交換に行く", "記録をつける", "取り立てる", "守る", "戦に出る")  # 前の年の同じ季節に、その家がしていたときだけまねる (4.A.4 の 2)
NOT_COMMON = COPY_IF_DONE + ("試す",)  # 「いちばん多い仕事」には数えない (行き先・残すもの・札のない仕事。era2._settle_visitors と同じ考え)
DIGEST_MAX = 40  # 「前の 1 年のこと」の自分の行 (仕事の種類ごとに新しい 3 件まで。4.A.9)
ZOOM_WHY = {"Z1": "ほかの村から求めが来ている", "Z2": "前の年に、村が戦をした", "Z3": "前の年に、貢いでいた村か、貢いでくる村が崩れた",
            "Z4": f"村の蓄えと家の倉を合わせても、{ZOOM_DAYS} 日分より少ない", "Z5": "村の蓄えが尽きて、集まり直した"}
MEET_KEYS = ("say", "keep", "seal", "accept", "judge", "leader", "call", "trade", "knowledge", "proposal", "votes", "year_name", "feeling",
             "answer_demand", "ally", "demand", "leave", "captives")  # 年の集まりの季節に、その季節の答えに入れる欄 (G7 の欄は、それぞれの部分が読む)
COPY_KEYS = ("pick", "plant", "harvest", "eat_goat", "sow", "keep", "seal", "seal_store", "feast", "accept", "judge", "leader", "answer_demand")  # 手本からまねる欄 (4.A.4 の 4・5)
PLAN_G7 = ("answer_demand", "ally", "demand", "leave", "captives")  # 年の答えのうち、G7 の部分が読む欄 (g7.plan にそのまま残す)


def _rep_of(state):
    """家ごとの代表 (家でいちばん年上の大人。同じ年なら人の並びで先。era2._reps と同じ決め方)。{家: 名前}"""
    out = {}
    for p in sorted(era2.adults(state), key=lambda q: -q["age"]):
        out.setdefault(p.get("household") or p["name"], p["name"])
    return out


def _wealth(state):
    """家ごとの豊かさ (家の倉 + ヤギ。era2.wealth と同じ数え方を math.fsum で。python の版で数が変わらないように)"""
    hs, goats = state["era2"].get("house", {}), {}
    for x in state["era2"]["goats"]:
        goats[x.get("owner")] = goats.get(x.get("owner"), 0) + 1
    return {h: round(math.fsum(f["kcal"] for f in hs.get(h, {}).get("store", [])) + goats.get(h, 0) * era2.GOAT_WORTH) for h in era2._homes(state)}


def _work_of(act):
    return next((w for w, acts in WORK if act in acts), "集める")


def _cells(state):
    """家ごとの組 (豊かさ 3 × 仕事 3。4.A.3)。仕事は、家の大人の前の 1 年 (g7.past) の日数を、仕事の組ごとに足してくらべる。乱数なし"""
    homes, w = era2._homes(state), _wealth(state)
    pos = sorted((h for h in homes if w.get(h, 0) > 0), key=lambda h: (w[h], h))
    low = set(pos[:len(pos) // 2])
    ads = {p["name"]: p for p in era2.adults(state)}
    days = {}  # 名前 → {仕事の組: 日数}
    for s in _g(state).get("past", []):
        for n, acts in s["days"].items():
            if n in ads:
                for a, d in acts.items():
                    row = days.setdefault(n, {})
                    row[_work_of(a)] = row.get(_work_of(a), 0) + d
    reps, out = _rep_of(state), {}
    for h in homes:
        mine = [n for n, p in ads.items() if p.get("household") == h]
        tot = {k: sum(days.get(n, {}).get(k, 0) for n in mine) for k, _ in WORK}
        if not any(tot.values()):  # 前の 1 年の日数がない家 (加わったばかり): 今の予定で数える
            for n in mine:
                k = _work_of((ads[n].get("plan") or {}).get("activity"))
                tot[k] += 1
        top = max(tot.values())
        tie = [k for k, _ in WORK if tot[k] == top]
        if len(tie) > 1:  # 代表の仕事の組 → 作る・畑・集める の順
            rd = days.get(reps.get(h), {})
            best = max(rd.get(k, 0) for k in tie)
            tie = [k for k in tie if rd.get(k, 0) == best] if best else tie
        work = next(k for k in WORK_TIE if k in tie)
        out[h] = f"{WEALTH[0] if w.get(h, 0) <= 0 else WEALTH[1] if h in low else WEALTH[2]}×{work}"
    return out


def _cell_key(c):
    """組の並び (豊かさの低い順 × 仕事の順)"""
    a, b = c.split("×")
    return WEALTH.index(a), [k for k, _ in WORK].index(b)


def sample_size(H):
    """見本の家の数: 大人のいる家の 4 割で、12 家から 25 家まで。12 家以下なら全部 (4.A.3)"""
    return H if H <= SAMPLE_MIN else min(SAMPLE_MAX, max(SAMPLE_MIN, round(SAMPLE_SHARE * H)))


def choose(state, rng):
    """見本の家を選ぶ (G7 に入る日と、年の最後の日の季節の終わり。4.A.3)。rng は塩 61 (その日に 1 回だけ作る)。
    数は大人のいる家の 4 割 (12〜25 家。12 家以下なら全部)。まとめ役の家・2 家以下の組の家・役の人の家は必ず入れる (重み 1)。
    のこりは組の家の数に合わせて割る (いちばん大きい余りから。家が 3 つ以上あるのに 0 になった組には、いちばん多い組から 1 つ回す)。
    3 年続いた見本の家は外し、足りない分は、見本だったのがいちばん前の家から (一度もなっていない家が先。同じなら乱数)"""
    g, D = _g(state), state["day"]
    homes = era2._homes(state)
    cells = _cells(state)
    H = len(homes)
    n = sample_size(H) if world.G7_PARTS["year"] else H  # 年 1 回の答えを止めた試しでは、全部の家
    old, hist = g.get("sample") or {}, g.setdefault("sample_hist", {})
    keep = {h: v for h, v in old.items() if h in homes and D + 1 - v["since"] < SAMPLE_YEARS * YEAR}
    lead = era2._leader(state)
    by = {}
    for h in homes:
        by.setdefault(cells[h], []).append(h)
    must = {h for c, hs in by.items() if len(hs) <= 2 for h in hs} | {p.get("household") for p in era2.adults(state) if p["name"] == lead or p["name"] in role_people(state)}
    must = (set(homes) if n >= H else must) & set(homes)
    n = max(n, len(must))
    rest = {c: [h for h in hs if h not in must] for c, hs in sorted(by.items(), key=lambda kv: _cell_key(kv[0]))}
    N, R = sum(len(hs) for hs in rest.values()), n - len(must)
    quota = {c: R * len(hs) / N if N else 0 for c, hs in rest.items()}
    target = {c: math.floor(q) for c, q in quota.items()}
    for c in sorted(rest, key=lambda c: (-(quota[c] - target[c]), _cell_key(c)))[:R - sum(target.values())]:
        target[c] += 1
    for c in [c for c in rest if rest[c] and not target[c]]:  # 家があるのに見本が 0 の組 (手本がなくなる) には、いちばん多い組から 1 つ回す
        give = max((x for x in rest if target[x] > 1), key=lambda x: (target[x], -_cell_key(x)[0], -_cell_key(x)[1]), default=None)
        if give:
            target[give] -= 1
            target[c] += 1
    for h in old:
        if h not in keep and h not in must:
            hist[h] = D  # 見本でなくなった日 (3 年続いた家は、選び直しで後ろに回る)
    order = {h: (h in hist, hist.get(h, -1), rng.random()) for h in sorted(homes) if h not in must and h not in keep}  # 乱数は家の名前の順に 1 回ずつ
    new = {}
    for h in sorted(must):
        new[h] = {"since": old[h]["since"] if h in old else D, "cell": cells[h], "must": True}
    for c, hs in rest.items():
        stay = [h for h in hs if h in keep]
        for h in stay:
            new[h] = {"since": keep[h]["since"], "cell": cells[h], "must": False}
        for h in sorted((h for h in hs if h in order), key=order.get)[:max(0, target[c] - len(stay))]:
            new[h] = {"since": D, "cell": cells[h], "must": False}
    for h in [h for h in keep if h not in new and h in cells]:  # 組を移った家も 3 年のあいだは見本のまま
        new[h] = {"since": keep[h]["since"], "cell": cells[h], "must": False}
    for h in old:
        if h not in new:
            hist[h] = D  # 見本でなくなった日
    g["sample"] = {h: new[h] for h in sorted(new)}
    g["cells"] = cells
    g["weights"] = {c: round(len(hs) / k, 3) for c, hs in rest.items() for k in [sum(1 for h in hs if h in new)] if hs and k}
    return g["sample"]


def donors(state):
    """見本でない家ごとの手本の家 (同じ組の見本の家。4.A.4)。大人の数がいちばん近い家 → 豊かさが近い家 → 受け持ちの少ない家 → 名前の順。
    見本でない家は、家の名前の順に 1 つずつ決める。乱数なし"""
    g = _g(state)
    sample, cells, w = g.get("sample") or {}, g.get("cells") or {}, _wealth(state)
    n_ad = {}
    for p in era2.adults(state):
        n_ad[p.get("household")] = n_ad.get(p.get("household"), 0) + 1
    load, out = {h: 0 for h in sample}, {}
    for h in sorted(x for x in cells if x not in sample):
        cand = [s for s in sorted(sample) if cells.get(s) == cells[h]]
        if cand:
            best = min(cand, key=lambda s: (abs(n_ad.get(s, 0) - n_ad.get(h, 0)), abs(w.get(s, 0) - w.get(h, 0)), load[s], s))
            load[best] += 1
            out[h] = best
        else:
            out[h] = None
    g["donor"] = out
    return out


def _store_days_all(state):
    """村の蓄えと家の倉を合わせて、今の人数の何日分か (寄る年の目安 Z4)"""
    e2 = state["era2"]
    kc = math.fsum(f["kcal"] for f in state["store"]) + math.fsum(f["kcal"] for h in sorted(e2.get("house", {})) for f in e2["house"][h].get("store", []))
    return kc / max(1, era2._need(state))


def _zoom(state):
    """次の年を寄る年にするか (年の最後の日の季節の終わり。前の年の数だけで決める。4.A.7)。
    Z1〜Z3 は地域の 1 年が g7.region.yoru に {"year": 次の年, "Z1": …, "Z2": …, "Z3": …} の形で書く (まわりの集落の部分)。Z4 はここで数える"""
    g, D = _g(state), state["day"]
    y = (D + 1) // YEAR
    yo = (g.get("region") or {}).get("yoru") or {}
    why = [k for k in ("Z1", "Z2", "Z3") if yo.get("year") == y and yo.get(k)]
    if _store_days_all(state) < ZOOM_DAYS:
        why.append("Z4")
    return {"year": y, "why": why, "day": D} if why else None


def year_turn(state):
    """年の最後の日の季節の終わり (4.G.1 の 10): 寄るか → 見本の選び直し → 手本。出来事「年の集まり」(【村】。見本のことは書かない)"""
    g, D = _g(state), state["day"]
    y = (D + 1) // YEAR
    g["zoom"] = z = _zoom(state)
    choose(state, era2._rng(state, era2.SAMPLE_SALT))
    donors(state)
    if z:
        log(state, "年の集まり", None, f"{y}年は、季節ごとに集まって決める (わけ: {'・'.join(ZOOM_WHY[k] for k in z['why'])})", year=y, zoom=z["why"])
    else:
        log(state, "年の集まり", None, f"{y}年の村の集まりは、夏のはじめの 1 回。これから 1 年の、季節ごとの予定と方針を決める", year=y, zoom=[])


def ask_next(state):
    """次の歩で答えが要るか (季節の終わりの最後。4.A.2)。"年" (年の集まり) / "寄る" (寄る年の季節) / "集まり直し" (蓄えが尽きて区切った) / None"""
    g, D = _g(state), state["day"]
    y, z = (D + 1) // YEAR, g.get("zoom")
    if not era2.adults(state):
        g["ask"] = None
    elif (D + 1) % SEASON_DAYS:  # 季節の途中で区切った (蓄えが尽きた。Z5): すぐ集まり直し、その年の残りの季節も寄る
        if not (z and z["year"] == y):
            log(state, "年の集まり", None, "村の蓄えが尽きたので、この年の残りの季節は、季節ごとに集まって決める", year=y, zoom=["Z5"])
            z = None
        g["zoom"] = {"year": y, "why": sorted(set((z or {}).get("why", [])) | {"Z5"}), "day": D}
        g["ask"] = "集まり直し"
    elif not world.G7_PARTS["year"] or (z and z["year"] == y):  # 寄る年 (G7_PARTS["year"] は試しで止めるためだけ。止めると毎季節寄る)
        g["ask"] = "寄る"
    else:
        g["ask"] = "年" if (D + 1) % YEAR == 0 else None
    return g["ask"]


def answerers(state):
    """答える人 (era2.answerers から): 見本の家の代表とまとめ役。大人が 12 人以下なら大人みんな (見本は全部の家)"""
    ads = era2.adults(state)
    if not state["era2"].get("rep_mode"):
        return [p["name"] for p in ads]
    era2._sync_households(state)
    sample = _g(state).get("sample") or {}
    who = {n for h, n in _rep_of(state).items() if h in sample} | {era2._leader(state)}
    return [p["name"] for p in ads if p["name"] in who]


def feelers(state):
    """気持ちだけ答える人 (era2.feelers から): 見本の家の大人で、代表でない人 (4.A.8)"""
    if not state["era2"].get("rep_mode"):
        return []
    who, sample = set(answerers(state)), _g(state).get("sample") or {}
    return [p["name"] for p in era2.adults(state) if p["name"] not in who and p.get("household") in sample]


def _seasons_of(v, now):
    """季節の並び (["秋", "春"]・"秋と春" など)。true はこの季節"""
    if v is True:
        return [now]
    s = "".join(map(str, v)) if isinstance(v, list) else str(v or "")
    return [x for x in SEASONS if x in s]


def _yes_no(v):
    """true / false / None (決めない)"""
    if v is True or str(v).strip().lower() in ("true", "はい", "受け入れる", "賛成"):
        return True
    if v is False or str(v).strip().lower() in ("false", "いいえ", "受け入れない", "反対"):
        return False
    return None


def _policy(a, now):
    """年の答えの 1 年の方針 (4.A.5・4.A.6)"""
    ar = a.get("accept_rule") if isinstance(a.get("accept_rule"), dict) else {}
    tr = a.get("trade_rule") if isinstance(a.get("trade_rule"), dict) else {}
    side = {k: (lambda x: x if x in ("村", False) else None)(era2._g6_side(tr.get(k))) for k in ("交換", "貸して")}
    nots = tr.get("not") if isinstance(tr.get("not"), list) else [tr.get("not")] if tr.get("not") else []
    call = a.get("call")
    act = (call.get("activity") if isinstance(call, dict) else call) if call else None
    when = _seasons_of(call.get("when"), now) if isinstance(call, dict) else []
    return {"feast": _seasons_of(a.get("feast"), now), "seal_store": _seasons_of(a.get("seal_store"), now),
            "judge_rule": era2._do(a.get("judge_rule")), "accept_rule": {k: _yes_no(ar.get(k)) for k in ("よその群れ", "ほかの村から")},
            "trade_rule": {**side, "max": era2._num(tr.get("max")) or None, "not": sorted({f"N{era2._num(x)}" for x in nots if era2._num(x)}),
                           **({"利子": _rate(tr.get("利子"))} if _rate(tr.get("利子")) else {})},  # 4.F の 4: 「貸して」に村がつける上乗せ
            "call": {"activity": str(act)[:20], "when": when[0] if when else None} if act else None}


def _plan(a, D, now):
    """年の答え → 整えた年の予定 (季節ごとの予定と 1 年の方針)。秋でない sow は読まない"""
    y = a.get("year") if isinstance(a.get("year"), dict) else {}
    year = {}
    for s in SEASONS:
        sub = y.get(s)
        if isinstance(sub, dict):
            year[s] = {k: v for k, v in sub.items() if k != "sow" or s == "秋"}
    return {"day": D, "year": year, "policy": _policy(a, now), "g7": {k: a[k] for k in PLAN_G7 if k in a}}


def _part(state, pl, sea, meet=None):
    """整えた年の予定 → この季節の答え (era2.apply_answers の季節の形)。meet: 年の集まりの季節の答え (話す・掟・票・裁き・申し出 など)。
    答えのない季節は、方針から、今のもめごと・申し出・よそから来た群れへの答えを作る (4.A.6 の表)"""
    sub, pol = pl["year"].get(sea), pl["policy"]
    a = {k: meet[k] for k in MEET_KEYS if k in meet} if meet else {}
    if isinstance(sub, dict):
        a.update({k: sub[k] for k in ("job", "family", "pick", "plant", "harvest", "eat_goat", "sow") if k in sub})
    else:
        a["_missing"] = True  # この季節の予定がない (決まりで動く。4.A.4 の 7)
    a["feast"], a["seal_store"] = sea in pol["feast"], sea in pol["seal_store"]
    if pol.get("call") and meet:
        a["call"], a["call_when"] = pol["call"]["activity"], pol["call"]["when"]
    if meet:
        return a
    e2 = state["era2"]
    if pol["judge_rule"]:
        a["judge"] = {d["id"]: pol["judge_rule"] for d in (e2.get("g5") or {}).get("disputes", []) if d["status"] == era2.OPEN}
    tr, trade = pol["trade_rule"], {}
    for off in (e2.get("g6") or {}).get("offers", []):
        r = tr.get(off["kind"])
        if off["kind"] == "返す" or r is None:
            continue
        if off["other"] in tr["not"] or (r == "村" and tr["max"] is not None and sum(era2.VALUE.get(k, 0) * n for k, n in off["want"].items()) > tr["max"]):
            r = False
        trade[off["id"]] = {"side": "村", "利子": tr["利子"]} if r == "村" and off["kind"] == "貸して" and tr.get("利子") else r
    a["trade"] = trade
    a["accept"] = {v["name"]: r for v in e2.get("visitors", []) for r in [pol["accept_rule"]["ほかの村から" if v.get("from") else "よその群れ"]] if r is not None}
    return a


def knows(state, name, card):
    """よその便りを「知っている人」か (4.C.6。hints.py が g7.hints.knowers に {札: [名前]} を作る)"""
    return bool(_g(state).get("hints")) and hints.knows(state, name, card)


def _job(j):
    j = {"activity": j} if isinstance(j, str) else dict(j) if isinstance(j, dict) else {}
    return {k: v for k, v in j.items() if k not in ("with", "why", "house")} | {"with": []}  # 一緒に行く人・理由・家の倉の物はまねない


def _fit(state, h, name, j, sea, common):
    """手本の仕事を、その家の人に当てる (4.A.4 の 2・3)"""
    j, act = _job(j), (j.get("activity") if isinstance(j, dict) else j)
    if act in COPY_IF_DONE and not ((_g(state).get("prev") or {}).get(h, {}).get(sea, {}).get(act)):
        then = j.get("then")
        then = then.get("activity") if isinstance(then, dict) else then
        return {"activity": then, "place": "camp", "with": []} if act == "交換に行く" and then in era2.acts2(state) and then not in NOT_COMMON else dict(common)
    if act == "試す" and not knows(state, name, j.get("try")):
        return dict(common)
    return j


def _kids(state, h):
    return sorted((c for c in era2.children(state) if c.get("household") == h and kid_age(c)), key=lambda c: -c["age"])


def _copy(state, h, rep, dh, drep, da, sea, common):
    """見本でない家の答え: 手本の家の、この季節の答えをまねる (4.A.4)。話す・知識・掟の提案・理由・気持ち・家ごとに出ていく・家の物で受ける申し出は、まねない"""
    a = {k: da[k] for k in COPY_KEYS if k in da}
    if isinstance(da.get("trade"), dict):
        a["trade"] = {k: v for k, v in da["trade"].items() if era2._g6_side(v) != "家"}
    a["votes"] = [{"id": v.get("id"), "agree": v.get("agree")} for v in da.get("votes") or [] if isinstance(v, dict)]
    dj, dfam = da.get("job") or {}, da.get("family") if isinstance(da.get("family"), dict) else {}
    ranks = [dj] + [dfam.get(q["name"]) or dj for q in era2.family(state, drep)[1:]]  # 手本の家の大人の、年の順の仕事
    fam = {}
    for i, q in enumerate(era2.family(state, rep)):
        j = _fit(state, h, q["name"], ranks[i] if i < len(ranks) else dj, sea, common)
        if i:
            fam[q["name"]] = j
        else:
            a["job"] = j
    dkids = [dfam.get(c["name"]) for c in _kids(state, dh)]  # 12〜14 歳の子も年の順に (手本に子がいなければ働かない)
    for c, j in zip(_kids(state, h), dkids):
        if j:
            fam[c["name"]] = j
    a["family"] = fam
    return a


def _rule(state, n, lp, now=False):
    """決まり (答えも手本もないとき): 前の年の同じ季節の予定をくり返す。票は出さない。前の年の予定がなければ None (今の予定のまま)。
    now: 前の年の予定がない人は、今の予定のまま (この季節の予定が抜けた答え)"""
    fam = era2.family(state, n) if state["era2"].get("rep_mode") else [next(p for p in era2.adults(state) if p["name"] == n)]
    rows = {q["name"]: dict(lp[q["name"]]) if q["name"] in lp else {k: q["plan"][k] for k in ("activity", "place")} for q in fam if q["name"] in lp or now}
    if not any(q["name"] in lp for q in fam) and not now:
        return None
    me = next(q for q in fam if q["name"] == n)
    return {"job": rows.get(n) or {k: me["plan"][k] for k in ("activity", "place")}, "family": {k: v for k, v in rows.items() if k != n}}


def _common(state, own):
    """その季節の見本の答えで、いちばん多い仕事 (行き先などの要る仕事は数えない。同じなら仕事と場所の名前の順)"""
    cnt = {}
    for n, a in own.items():
        if a.get("_missing"):
            continue
        j0, fam = _job(a.get("job")), a.get("family") if isinstance(a.get("family"), dict) else {}
        for q in era2.family(state, n) if state["era2"].get("rep_mode") else [next(p for p in era2.adults(state) if p["name"] == n)]:
            j = _job(fam.get(q["name"])) if q["name"] != n and fam.get(q["name"]) else j0
            k = (j.get("activity"), j.get("place") if j.get("place") in {pl["id"] for pl in state["places"]} else "camp")
            if k[0] in era2.acts2(state) and k[0] not in NOT_COMMON:
                cnt[k] = cnt.get(k, 0) + 1
    k = min(cnt, key=lambda x: (-cnt[x], x)) if cnt else ("採集", "camp")
    return {"activity": k[0], "place": k[1], "with": []}


def _fam_of(state, n, answers, rep_mode, reps):
    """era2.apply_answers と同じ数え方の、その答えが数える大人"""
    me = next(p for p in era2.adults(state) if p["name"] == n)
    if not rep_mode:
        return [me]
    if n not in reps:
        return [me]
    return [q for q in era2.family(state, n) if q is me or q["name"] not in answers]


def _apply(state, own, kinds, real, how):
    """見本の答え (own: {答える人: 季節の形の答え}) に、見本でない家の答え (手本から)・決まり・加わった家を足し、era2.apply_answers を 1 回呼ぶ。
    kinds: {答える人: "年" (年の答えから) | "季節" (寄る季節・集まり直しの答え)}。real: この歩で実際に答えた人 (気持ちを読む人)"""
    g, e2, D = _g(state), state["era2"], state["day"]
    sea, rep_mode = season(D + 1), bool(e2.get("rep_mode"))
    reps_h = _rep_of(state)
    reps = set(reps_h.values())
    lp = (g.get("last_plans") or {}).get(sea) or {}
    answers, src_of, missing = {}, {}, []
    for n in own:
        a = dict(own[n])
        if a.pop("_missing", False):  # この季節の予定がない見本の家: 仕事は決まり、票などは答えのとおり
            a.update(_rule(state, n, lp, now=True))
            missing.append(n)
        answers[n] = a
    house = {n: next(p for p in era2.adults(state) if p["name"] == n).get("household") for n in answers}
    usable = {house[n]: n for n in answers if rep_mode and n in reps and n not in missing}  # この季節の予定がある家 → 答えた代表
    sample, cells, donor = g.get("sample") or {}, g.get("cells") or {}, g.get("donor") or {}
    used, rule_h, joined_h, common = {}, [], [], _common(state, {n: own[n] for n in usable.values()})
    w = _wealth(state)
    n_ad = {}
    for p in era2.adults(state):
        n_ad[p.get("household")] = n_ad.get(p.get("household"), 0) + 1
    for h in era2._homes(state) if rep_mode else []:
        rep = reps_h.get(h)
        if not rep or rep in answers:
            continue
        if h not in cells:  # 年の途中で加わった家: 次の年の集まりまで、その季節に村でいちばん多い仕事 (4.A.4 の 8)
            answers[rep], src_of[rep] = {"job": dict(common)}, "加わった季節"
            joined_h.append(h)
            continue
        d = donor.get(h) if h not in sample else None
        if d not in usable:  # 手本の答えがない: 同じ組のほかの見本の家 (4.A.4 の 7)
            d = min((s for s in usable if s in sample and cells.get(s) == cells[h] and h not in sample),
                    key=lambda s: (abs(n_ad.get(s, 0) - n_ad.get(h, 0)), abs(w.get(s, 0) - w.get(h, 0)), s), default=None)
        if d:
            answers[rep], src_of[rep] = _copy(state, h, rep, d, usable[d], answers[usable[d]], sea, common), "見本から広げた"
            used[h] = d
        else:
            r = _rule(state, rep, lp)
            if r:
                answers[rep], src_of[rep] = r, "決まり (前の年と同じ)"
            rule_h.append(h)
    order = {p["name"]: i for i, p in enumerate(state["people"])}  # 答えは人の並びの順に読む (step.read_answers と同じ。話・知識・掟の番号の順が G6 と同じになる)
    answers = {n: answers[n] for n in sorted(answers, key=order.get)}
    fams = {n: _fam_of(state, n, answers, rep_mode, reps) for n in answers}
    n_all = len(era2.adults(state))
    ynames = {n: era2._year_name_text(a.pop("year_name", None)) for n, a in answers.items()} if era2.year_end(state) else {}
    feel = {n: (p.get("feeling"), p.get("feeling_day")) for p in era2.adults(state) for n in [p["name"]] if n in answers and n not in real}
    joined0 = len(e2.get("joined", []))
    era2.apply_answers(state, answers, how=how)
    for p in state["people"]:  # 気持ちは、答えた人だけ (4.A.8。まねた答え・方針の答えでは変えない)
        if p["name"] in feel:
            p["feeling"], f_day = feel[p["name"]]
            if f_day is None:
                p.pop("feeling_day", None)
            else:
                p["feeling_day"] = f_day
    props = []  # 年の名前: 答えた人の家族の大人に、手本として受け持つ家の大人を足して数える (4.A.8)
    for n in sorted(ynames):
        if ynames[n] and n in real:
            k = len(fams[n]) + sum(len(fams[reps_h[h]]) for h, d in used.items() if d == house.get(n) and n in reps)
            props.append((next(p for p in state["people"] if p["name"] == n), ynames[n], k))
    if props:
        era2._year_name(state, props, n_all)
    src = {}  # だれの答えで仕事が決まったか (記録の decided_by。4.A.10)
    for n, a in answers.items():
        fj = a.get("family") if isinstance(a.get("family"), dict) else {}
        for q in fams[n]:
            if n in src_of:
                v = src_of[n]
            elif n in missing:
                v = "決まり (前の年と同じ)" if q["name"] in lp else "答えなし (前と同じ)"
            else:
                v = "自分" if q["name"] == n else "代表が割り振った" if fj.get(q["name"]) else "代表と同じ仕事"
                v = f"年の答え ({v})" if kinds.get(n) == "年" else v
            src[q["name"]] = v
    for n in e2.get("joined", [])[joined0:]:
        src[n] = "加わった季節"
    for p in era2.adults(state):
        src.setdefault(p["name"], "答えなし (前と同じ)")
    g["src"] = {k: src[k] for k in sorted(src)}
    g["step"] = {"day": D, "season": sea, "ask": g.get("ask"), "how": how, "answer_day": g.get("answer_day"),
                 "sample": sorted(h for h in sample if h in set(era2._homes(state))), "donor": {h: used[h] for h in sorted(used)},
                 "rule": sorted(rule_h), "joined": sorted(joined_h), "answered": sorted(real)}
    g.setdefault("last_plans", {})[sea] = {p["name"]: {k: p["plan"][k] for k in ("activity", "place")} for p in era2.adults(state)}


def apply_year(state, answers, councils=None):
    """集まりの歩 (年の集まり・寄る季節・集まり直し) の答えを読む (step.py season。4.A.6)。
    年の集まりは、年の答えを整えて g7.plan に残し、この季節の分を当てる。寄る季節・集まり直しは、季節の形の答えをそのまま当てる。
    順 (4.G.1・4.B.5): 家ごとに出ていく (leave) → まわりの集落の集まりの答え・待ち・続く貢ぎ (残った家で数えた、求めへの答えで) → 村の答え → 村が求める (demand)。
    councils: まわりの集落の集まりの答え {番号: 答えの文} (step.py が council/ から読む)"""
    g, e2, D = _g(state), state["era2"], state["day"]
    ask, now = g.get("ask") or "寄る", season(D + 1)
    g["meet_first"], g["answer_day"] = state["next_event"], D
    alive = {p["name"] for p in era2.adults(state)}
    real = {n: characters.parse(raw) for n, raw in answers.items() if n in alive}  # step.read_answers の順 (人の並び) のまま
    if region_on(state):
        leave_households(state, real)
        alive = {p["name"] for p in era2.adults(state)}
        real = {n: a for n, a in real.items() if n in alive}
    begin(state, {**village_answers(state, real), **tribute_answers(state, real)} if region_on(state) else None, councils)
    if joints(state):
        captives_answer(state, real)  # 戦に勝ったとき、負けた村の職人を連れて帰るか (4.C.4。答えがなければ前の答えのまま、はじめは「連れて帰らない」)
    own, kinds = {}, {}
    if ask == "年":
        reps = set(_rep_of(state).values())
        g["plan"] = {}
        for n, a in real.items():
            h = next(p for p in era2.adults(state) if p["name"] == n).get("household")
            pl = g["plan"][n] = {"household": h, "own": not e2.get("rep_mode") or n in reps, **_plan(a, D, now)}
            own[n], kinds[n] = _part(state, pl, now, a), "年"
    else:
        g["plan"] = {}  # 寄る季節の答えは、その季節だけ
        for n, a in real.items():
            own[n], kinds[n] = dict(a), "季節"
    _apply(state, own, kinds, set(real), "集まり")
    village_demand(state, real)


def apply_plan(state):
    """答えのない季節のはじめ (4.A.6): 年の答えの、この季節の予定と 1 年の方針を当てる。掟の投票はしない。
    代表が亡くなった家は、次に年上の大人 (今の代表) が、その家の予定で動く"""
    g, e2, D = _g(state), state["era2"], state["day"]
    begin(state)
    sea, rep_mode = season(D + 1), bool(e2.get("rep_mode"))
    reps_h, lead = _rep_of(state), era2._leader(state)
    alive = {p["name"] for p in era2.adults(state)}
    own = {}
    for n, pl in sorted(g.get("plan", {}).items()):
        who = reps_h.get(pl["household"]) if pl["own"] and rep_mode else n if n in alive and (pl["own"] or n == lead) else None
        if who and who in alive and who not in own:
            own[who] = _part(state, pl, sea)
    _apply(state, own, {n: "年" for n in own}, set(), "方針")


def since(state):
    """お題の「前の季節のこと」を数えはじめる出来事 (この前の集まりの歩の、30 日の最初の出来事)"""
    return _g(state).get("since", state["era2"].get("last_first", 0))


def after_season(state, first, met):
    """歩のあと (step.py season。simulate_season のあと): 集まりの歩なら、次のお題の「前の…のこと」をここから数える"""
    if met:
        _g(state)["since"] = first


def digest_head(state):
    """お題の「前の季節のこと」の見出し (この前の集まりが 1 季節より前なら、その日から)"""
    g, D = _g(state), state["day"]
    a = g.get("answer_day")
    return "前の季節のこと" if a is None or D - a <= SEASON_DAYS else f"この前の集まり ({a + 1} 日目) からのこと"


def digest(state, p, first):
    """自分のこと (era2._season_digest。1 年分になるので 40 行まで)"""
    return "\n".join(era2._season_digest(state, p, first).split("\n")[:DIGEST_MAX])


def meeting_word(state):
    return "1 年に 1 回の村の集まり" if _g(state).get("ask") == "年" else "季節のはじめの集まり"


def since_word(state):
    return "前の季節" if digest_head(state) == "前の季節のこと" else "この前の集まりから"


def zoom_line(state):
    """寄る季節・集まり直しのお題の 1 行 (わけだけ。4.A.9)"""
    g = _g(state)
    z = g.get("zoom")
    if g.get("ask") not in ("寄る", "集まり直し") or not z or not z.get("why"):
        return ""
    return f"\n今年は季節ごとに集まる (わけ: {'・'.join(ZOOM_WHY.get(k, k) for k in z['why'])})。"


# ---- お題に出す決まりの文と、G7 の欄 (4.F の 8・4.A.5)。どれも「する」と「しない」を同じ重さで。例の値は空にする ----

def _demands_to_village(state):
    """村への求め (まわりの集落の部分が g7.region.demands に {"id": "Q1", "from": "N2", "to": "V0", …, "end": None} の形で書く)"""
    return [d for d in (_g(state).get("region") or {}).get("demands", []) if d.get("to") == "V0" and not d.get("end")]


def _village_pays(state):
    return any(t.get("payer") == "V0" and t.get("status") == "続く" for t in (_g(state).get("region") or {}).get("ties", []))


def _tax_law(state):
    return any(l.get("status") == "採用" and l.get("tax") for l in state.get("laws", []))


def _tech_open(state):
    return any(t.get("open") and not t.get("done") for t in ((_g(state).get("hints") or {}).get("tech") or {}).values())


def _plough(state):
    D = state["day"]
    return bool((((_g(state).get("hints") or {}).get("tech") or {}).get("H7-06") or {}).get("done")) and \
        sum(1 for c in state["era2"].get("cattle", []) if D - c["born"] >= 2 * YEAR) >= 2


def _leave_on(state):
    return bool(_demands_to_village(state)) or _village_pays(state) or _tax_law(state)


def _war_on(state):
    """村が戦に出るか攻められる季節か、村が「断られたら戦う」と書いた求めが続いている (まわりの集落の部分が war_season と demands を書く)"""
    return bool(_g(state).get("war_season")) or any(d.get("from") == "V0" and d.get("then") == "戦う" and not d.get("end")
                                                   for d in (_g(state).get("region") or {}).get("demands", []))


FACTS_ON = {  # 決まりの文を出すとき (4.F の 8)。tax・write・loan・guard・others は G7 に入った日から (write は粘土の板が使えるとき)
    "tax": lambda state: True, "write": lambda state: bool(((state["era2"].get("g6") or {}).get("open") or {}).get("板")),
    "loan": lambda state: True, "guard": lambda state: True, "others": lambda state: True, "leave": _leave_on,
    "cattle": lambda state: any(o.get("known") is not None and int(o.get("cattle_f", 0)) >= 1 for o in _others(state)),
    "try": _tech_open, "plough": _plough}
FIELDS_ON = {  # 答えの欄を出すとき (4.A.5)
    "demand": lambda state: any(o.get("known") is not None for o in _others(state)),
    "answer_demand": lambda state: bool(_demands_to_village(state)), "ally": lambda state: bool(_demands_to_village(state)),
    "leave": _leave_on, "captives": _war_on, "tribute": _village_pays, "tax": lambda state: True, "rate": lambda state: True, "利子": lambda state: True,
    "try": _tech_open, "plough": _plough, "build": lambda state: True}


def fields_on(state):
    return [k for k in FIELDS_ON if FIELDS_ON[k](state)]


FIELDS_HEAD = "新しい仕組み (上の決まりを見て決める。どれも書かなくてもよい)"


def fields_now(state, p, solo, n, year=False):
    """寄る季節・集まり直しのお題の「いま」の、G7 の欄の項目 (n はその番号)"""
    return f"{n}. {FIELDS_HEAD}\n" + _field_rows(state, solo, year) + "\n"


def _field_rows(state, solo, year):
    on = set(fields_on(state))
    rows = []
    if "demand" in on:
        rows.append('   求める: 知っている村に、毎年決まったものを出すように求めるなら demand に {"to": 村の番号, "what": {物: 数}, "then": 断られたら "戦う" か "やめる"}、'
                    "求めないなら null" + ("。断られて戦うときは、次の季節の 10 日目に、その季節の主な仕事を「戦に出る」にした人が出かける (year の次の季節の job に書ける)"
                                         if year else ""))
    if "answer_demand" in on:
        ids = "・".join(d["id"] for d in _demands_to_village(state))
        rows.append(f"   求めへの答え: 村への求め ({ids}) ごとに、\"払う\" か \"戦う\" か \"逃げる\" か \"助けを頼む\" (answer_demand)。助けを頼むなら、頼む村の番号 (ally)")
    if "leave" in on and not solo:
        rows.append("   家ごとに村を出る: 家の人みんなで村を出るなら true、出ないなら false (leave。家の代表が決める)")
    if "captives" in on:
        rows.append('   戦に勝ったとき: 負けた村の職人を "連れて帰る" か "連れて帰らない" (captives)')
    if "tribute" in on:
        ids = "・".join(t["id"] for t in _reg(state).get("ties", []) if t["payer"] == "V0" and t["status"] == "続く")
        rows.append(f'   貢ぎ: 村がほかの村に毎年出しているもの ({ids}) ごとに、"払い続ける" か "やめる" (tribute。書かなければ払い続ける)')
    rows.append('   掟の提案には、家ごとに 1 年に 1 回、村の蓄えへ出すもの (tax: {"what": "草の種" か "ヤギ", "share": 割合}) や、ヤギ 1 頭を草の種何つかみとみなすか '
                '(rate: {"ヤギ": つかみ}) を、つけることも、つけない (null) こともできる')
    rows.append("   「貸して」の申し出には、上乗せ (利子、0 から 0.5) をつけて答えることも、つけない (0) こともできる ("
                + ('trade_rule の "利子"' if year else 'trade に {"side": "村", "利子": 上乗せ} の形') + ")")
    if "try" in on:
        rows.append("   試す: 主な仕事を「試す」にする人は、job に try (便りの番号) を書く")
    if "plough" in on:
        rows.append("   犂: 畑仕事の人は、牛に犂を引かせるなら job に plough: true を書ける")
    rows.append('   壁: 住まいを建てる人は、job に build: "壁" と書くと、村のまわりの壁を積む (書かなければ、家族の住まい)')
    return "\n".join(rows)


def fields_json(state, p, solo):
    on = set(fields_on(state))
    return ((' "demand": null,' if "demand" in on else "") + (' "answer_demand": {}, "ally": null,' if "answer_demand" in on else "")
            + (' "leave": false,' if "leave" in on and not solo else "") + (' "captives": null,' if "captives" in on else "")
            + (' "tribute": {},' if "tribute" in on else ""))


def fields_prop(state):
    return ', "tax": null, "rate": null'


# ---- 年の集まりのお題 (4.A.9) ----
RULES_Y = era2.RULES2.replace(
    "- これから季節の終わりまでの主な仕事を 1 つ決めます。毎日その仕事をします (けがの日は休む)。",
    "- これから 1 年 (夏・秋・冬・春) の、季節ごとの主な仕事を決めます。季節ごとに、毎日その仕事をします (けがの日は休む)。")
assert RULES_Y != era2.RULES2, "RULES2 の文が変わった (年の集まりの決まりの文を直す)"


def _season_notes(state, seas):
    """季節ごとに見て分かること (1 行ずつ)"""
    e2 = state["era2"]
    out = []
    for s in seas:
        if s == "夏":
            ripe = [f for f in e2["fields"] if f["state"] == "実った"]
            grow = [f for f in e2["fields"] if f["state"] == "育つ" and season(f["day"]) == "秋"]
            out.append("- 夏: " + (f"実って刈れる畑 (残り 約 {sum(f['yield'] - f['harvested'] for f in ripe)} つかみ)" if ripe else
                                   f"秋にまいた畑 (まいた種 合わせて {sum(f['seed'] for f in grow)} つかみ) が、夏のはじめに実る (まいた量の数倍。年によって違う)" if grow
                                   else "実る畑はない") + "。夏のうちに刈らないと落ちる。夏の畑仕事は刈り入れ (実った畑があるあいだ)。キャンプのそばの木に実がなる")
        elif s == "秋":
            out.append("- 秋: 秋のはじめに、sow に書いた量の蓄えの草の種が畑にまかれる (仕事の「種まき」はいらない。「種まき」は持ち物の「種」を埋めて木を育てる仕事)。"
                       "まいた畑は次の夏に実る。キャンプのそばの木に実がなる")
        elif s == "冬":
            out.append("- 冬: 木の実も草の種も実らない")
        else:
            out.append("- 春: 子ヤギが生まれる。春と夏は、世話をするとヤギの乳がとれる")
    if any(s != "夏" for s in seas):  # 実りと草取り (era2 の畑の実り: need・min(1, 0.3 + 0.7 × work / need))
        out.append("- 実りと畑仕事: まいた畑の実りは、秋・冬・春の畑仕事 (草取り) で増える。畑 1 つに要る草取りは (まいた種 つかみ × 0.15 + 10) 時間で、"
                   "草取りがなければ実りは 3 割、した時間に合わせて増え、要る時間の分まですると 10 割 (それより多くしても増えない)。"
                   "畑仕事の時間は、育っている畑みんなで分ける")
    return "\n".join(out)


def year_prompt(state, p, first):
    """年の集まりのお題 (年の最後の日の終わりに書く。G7 に入った日は、年の終わりまでの短い年)。見本であることは書かない"""
    e2, g = state["era2"], _g(state)
    g5 = e2.get("g5") or {}
    lead, two = g5.get("leader"), g5.get("stage", 1) >= 2
    rep_mode = bool(e2.get("rep_mode"))
    solo = bool(rep_mode and p["name"] not in era2._reps(state))
    ask_why = bool(e2.get("ask_why"))
    why_json = ', "why": "..."' if ask_why else ""
    D = state["day"]
    now = season(D + 1)
    seas = SEASONS[SEASONS.index(now):]
    st = dict(state, day=D + 1)
    me = characters._me(st, p).replace("(誰でも入れたり取ったりできる)", "(日々の出し入れは自動)")
    names = [q["name"] for q in era2.adults(state) if q is not p]
    places = "\n".join(f"- {pl['id']}: {pl['label']}" for pl in state["places"])
    goats = bool(e2["goats"]) and not solo
    g6 = (e2.get("g6") or {})
    vis = ""
    if e2["visitors"]:
        rows = []
        for v in e2["visitors"]:
            o = era2._other(state, v.get("from")) if v.get("from") else None
            rows.append("- " + "、".join(f"{m['name']} ({m['sex']}、{m['age']} 歳)" for m in v["members"]) + (f" ({o['name']} から来た)" if o else " (よその群れ)"))
        vis = ("\n## よそから来た人\n" + "\n".join(rows) + "\nそれぞれ「ここで暮らしたい」と言っている (1 行が、いっしょに来た一つの群れ)。群れごとに、村に受け入れるか決めてください "
               "(accept: 群れの最初の人の名前ごとに、受け入れるなら true、受け入れないなら false)。大人の半分をこえる賛成で、その群れの全員が村に加わる。"
               "加わった大人は、次の年の集まりまで、季節ごとに村でいちばん多い仕事をする\n")
    fam_txt, fam_json = "", ""
    if rep_mode and not solo:
        fam = [q for q in era2.family(state, p["name"]) if q is not p]
        kids = [c for c in era2.children(state) if c.get("household") and c.get("household") == p.get("household")]
        rows = [f"- {q['name']} ({q['sex']}、{q['age']} 歳。採集 {q['skills']['採集']:.2f}、狩り {q['skills']['狩り']:.2f}。"
                f"おなか {era2._hunger_word(q['hunger'])}{'、けが' if q.get('injured') else ''}{'。まとめ役なので、自分で答える' if q['name'] == lead else ''})" for q in fam]
        rows += [f"- 子: {c['name']} ({c['sex']}、{c['age']} 歳、母 {c.get('mother') or '-'})" for c in kids]
        fam_txt = (f"\n## あなたの家族 ({p.get('household')})\n村の大人が {era2.REP_FROM} 人をこえたので、村の集まりでは家族ごとに、いちばん年上の大人が代表して答える。"
                   f"あなたは {p.get('household')} の代表。\n" + ("\n".join(rows) if rows else "- (ほかの家族はいない)")
                   + "\n- 家族の大人の、季節ごとの主な仕事も、あなたが決める (year の季節ごとの family。書かなかった人は、その季節のあなたと同じ仕事)"
                   + ("\n- family に書いた人ごとに、その仕事にした理由も一言書く (family の why)" if ask_why else "")
                   + ("\n- 12〜14 歳の子にも、季節ごとの family で「畑仕事」か「ヤギの世話」を割り振れる (働きは大人の半分。書かなかった子は働かない)"
                      if fix(state) and any(kid_age(c) for c in kids) else "")
                   + "\n- sow・pick・plant・harvest の数は、家族の大人一人ひとりの量 (eat_goat は家族で何頭か)"
                   + "\n- 掟の投票、よそから来た人の受け入れ、もめごとの収め方・祭り" + ("・まとめ役" if two else "") + "・申し出 (trade)・村の蓄えの封の答えと、1 年の方針は、"
                   "家族の大人みんなの答えとして数える\n")
        if fam:
            fam_json = '"family": {' + ", ".join(f'"{q["name"]}": {{"activity": "採集", "place": "camp"{why_json}}}' for q in [q for q in fam if q["name"] != lead][:2]) + '}, '
    if solo:
        fam_txt = (f"\n## あなたはまとめ役\nあなたは {p.get('household')} の代表ではないが、村のまとめ役なので、村の集まりで答える。決めるのは自分の季節ごとの仕事だけ "
                   "(家族の仕事・家の倉・ヤギをつぶす数は、家族の代表が決める)。掟の投票・受け入れ・もめごとの収め方・祭り・まとめ役・申し出 (trade)・村の蓄えの封の答えと、"
                   "1 年の方針は、あなた一人の答えとして数える\n")
    op = [d["id"] for d in g5.get("disputes", []) if d["status"] == era2.OPEN]
    offers = [o["id"] for o in g6.get("offers", []) if o["kind"] != "返す"]
    rec = era2.ACT_RECORD in era2.acts2(state)
    known = any(o["known"] is not None for o in g6.get("others", []))
    acts = era2.acts2(state)
    q = ["話したいことがあれば話す (0〜2 つ。相手は仲間の名前か「みんな」)。前と同じ言い回しをくり返さず、あなたらしい言葉で",
         f"季節ごとの主な仕事を決める (year の {'・'.join(seas)} のそれぞれに job)。仕事は {' / '.join(acts)} から 1 つ、場所は下の一覧の id から 1 つ、"
         f"一緒に行きたい人 ({'、'.join(names) or 'なし'}) がいれば書く\n"
         "   畑仕事 (草取り・刈り入れ) と ヤギの世話 は camp で行う。ヤギを捕まえるは、野生のヤギのいる場所で行う"
         + ("\n   その仕事にした理由を一言で書く (why。続けている仕事なら、続ける理由を)" if ask_why else "")
         + (f"\n   交換に行く{'・記録をつける' if rec else ''}は camp と書く (行き先・持って行く物{'・残すもの' if rec else ''}は job に書く。下の「ほかの村・印・記録」)"),
         "季節ごとの量 (year の季節ごと): pick (その季節の毎夕、キャンプのそばの木から取る実。1 人 40 つかみまで。実がなるのは夏と秋)・plant (持っている木の実を、"
         "季節のはじめにキャンプのそばに埋める。つかみ、5 まで)・harvest (実った畑を毎夕刈る。つかみ、60 まで)"
         + ("・eat_goat (季節のはじめに、飼っているヤギを何頭つぶして肉にするか。肉は干して蓄えに入れる。2 頭は残す)" if goats else "")
         + ("・秋だけ sow (秋のはじめに、蓄えの草の種を畑にまく量。つかみ、1000 まで)" if "秋" in seas else "")]
    if not solo:
        q.append("家の倉を持つか (keep: 持つなら true、持たないなら false) を決める (家の代表が決める)")
    q += ["覚えていることを更新する (新しく分かったことを追加、確かさを変える、間違っていたら忘れる)",
          "掟: みんなで守りたい決まりがあれば提案できる (なければ null)。今の掟と提案に、賛成か反対かを投票する (against に反対する理由、reason に決めた理由)。"
          "掟の提案と投票は、この集まりでだけする"]
    q.append("村の集まり (上の「村の集まり」を見て決める。どれも書かなくてもよい)\n"
             + ("   もめごと: まだ収まっていないもめごとの収め方を、番号ごとに「つぐなう」か「ゆるす」で書く (judge)\n" if op else "")
             + f"   もめごとの方針: この 1 年、季節のはじめに、まだ収まっていないもめごと (古いものから {era2.TALK_MAX} つまで) を収める収め方 "
               "(judge_rule:「つぐなう」か「ゆるす」。決めないなら null)\n"
             + '   祭り: 祭りをする季節を並べる (feast。例 ["秋"]。しないなら [])。祭りは、その季節のはじめにする\n'
             + ("   まとめ役: まとめ役にしたい人の名前を書く (leader。まとめ役はいらないなら「なし」、決めないなら null)\n"
                '   罰: 掟を提案するときに罰をつけるなら、proposal の penalty に {"for": "ヤギ" か "倉" か "蓄え" か "刈る", "pay": 草の種のつかみ} を書く (つけないなら null か、pay を 0 のまま)\n'
                if two else "")
             + ("   あなたは村のまとめ役。あなたの家のものでないもめごとは、あなたの judge と judge_rule で決まる (いくつでも)。この 1 年のうちの季節を 1 つ選んで、"
                'みんなでする仕事を呼びかけられる (call: {"activity": 仕事の名前, "when": 季節}。しないなら null)\n' if lead == p["name"] else ""))
    q.append("ほかの村・印・記録 (上の「ほかの村・印・記録」を見て決める。どれも書かなくてもよい)\n"
             + ("   申し出: 申し出の番号ごとに、村の物で受けるなら \"村\"" + ("" if solo else "、自分の家の物で受けるなら \"家\"") + "、受けないなら false (trade)\n" if offers else "")
             + "   申し出の方針: この 1 年に来る申し出を、季節のはじめに決める決め方 (trade_rule:「交換」「貸して」ごとに、村の物で受けるなら \"村\"、受けないなら false、"
               "決めないなら null。max は 1 つの申し出で村が出す物の上限 (草の種にして何つかみ。決めないなら null)、not は相手にしない村の番号の並び)。返す申し出は、決めずに受けとる\n"
             + ("   印: 家の印を作るなら true (seal。家ごとに 1 回だけ)\n" if not solo and p.get("household") and p["household"] not in g6.get("seals", {}) else "")
             + '   村の蓄えの封: 村の蓄えに封をする季節を並べる (seal_store。例 ["冬"]。しないなら [])\n'
             + ('   交換に行く: 主な仕事を「交換に行く」にする季節は、その job か family に、to (村の番号)・carry (持って行く物と数)・want (ほしい物)・then (帰ってからの仕事) を書く。'
                '例 {"activity": "交換に行く", "place": "camp", "to": "N1", "carry": {"土器": 4}, "want": "ヤギ", "then": "採集"' + why_json + '}\n'
                if known else "")
             + (f'   記録をつける: 主な仕事を「記録をつける」にする季節は、what (残すもの: {"・".join(era2._whats(state))}。書いた順に残す) と how '
                f'({" / ".join(h for h in ("数え札", "封筒", "板") if (g6.get("open") or {}).get(h))}) を書く。'
                '例 {"activity": "記録をつける", "place": "camp", "what": ["蓄え", "交換", "刈る"], "how": "数え札"' + why_json + '}\n' if rec else ""))
    q.append("よそから来た人 (どれも書かなくてもよい)\n"
             + ("   今来ている群れ: 群れの最初の人の名前ごとに、受け入れるなら true、受け入れないなら false (accept)\n" if e2["visitors"] else "")
             + "   受け入れの方針: この 1 年に来る群れを、季節のはじめに決める決め方 (accept_rule:「よその群れ」「ほかの村から」ごとに、受け入れるなら true、"
               "受け入れないなら false、決めないなら null)。大人の半分をこえる賛成で、群れの全員が村に加わる\n")
    q.append(f"{FIELDS_HEAD}\n" + _field_rows(state, solo, True))
    if era2.year_end(state):
        q.append("この 1 年の名前を決める (year_name。上の「年の名前」を見て)")
    q.append("今の気持ちを一言")
    asks = "\n".join(f"{i}. {x.rstrip(chr(10))}" for i, x in enumerate(q, 1))
    sea_json = ",\n          ".join(f'"{s}": {{"job": {{"activity": "採集", "place": "camp", "with": []{why_json}}}, {fam_json}"pick": 0, "plant": 0, "harvest": 0'
                                   + (', "eat_goat": 0' if goats else "") + (', "sow": 0' if s == "秋" else "") + "}" for s in seas)
    acc = ('"accept": {' + ", ".join(f'"{v["name"]}": true' for v in e2["visitors"]) + "}, ") if e2["visitors"] else ""
    pen = ', "penalty": {"for": "...", "pay": 0}' if two else ""
    nxt = (D + 1) // YEAR * YEAR + YEAR
    village = "" if era2.year_end(state) else f"\n村のおもな出来事 (この年):\n{era2._year_digest(state)}"
    out = f"""{RULES_Y}

{me}{era2.FACTS2}{era2.FACTS_G3 + era2.FACTS_HOUSE}{era2.FACTS_G4}{era2._g5_facts(state)}{era2._g6_facts(state)}{facts(state)}
## 村のようす
{era2._village(state)}
## {digest_head(state)}
{digest(state, p, first)}{village}

## 最近聞いた話
{characters._heard(p)}
{fam_txt}
## 覚えていること
{characters._knowledge(state, p)}

## 集団の掟 (1 年に 1 回の村の集まりで、みんなで決める)
{characters._laws(state, with_pending=True, short=True)}
{era2._year_names_text(state)}{era2._g5_text(state)}{era2._g6_text(state)}{text(state, p)}{vis}{era2._year_end_text(state)}
## いま
{D + 1} 日目、{now}。1 年に 1 回の村の集まり。これから {nxt - D - 1} 日 ({'・'.join(seas)}) の、季節ごとの予定と、{'1 年' if len(seas) == 4 else '年の終わりまで'}の方針を決める (次の集まりは {nxt} 日目、夏のはじめ。途中で村の蓄えが尽きて、ひどく空腹の人が出たら、そこで集まり直す)。
季節ごとに見て分かること:
{_season_notes(state, seas)}
{asks}

場所の一覧:
{places}

## 答えの形 (JSON)
{{"say": [{{"to": "みんな", "text": "..."}}],
 "year": {{{sea_json}}},
 {'"keep": false, ' if not solo else ''}{'"seal": false, ' if not solo and p.get("household") and p["household"] not in g6.get("seals", {}) else ''}"seal_store": [],
 {acc}"accept_rule": {{"よその群れ": null, "ほかの村から": null}},
 {('"judge": {' + ", ".join(f'"{i}": "..."' for i in op) + "}, ") if op else ''}"judge_rule": null, "feast": [], {'"leader": "...", ' if two else ''}{'"call": null, ' if lead == p["name"] else ''}
 {('"trade": {' + ", ".join(f'"{i}": "..."' for i in offers) + "}, ") if offers else ''}"trade_rule": {{"交換": null, "貸して": null, "max": null, "not": [], "利子": 0}},{fields_json(state, p, solo)}
 "knowledge": [{{"op": "add", "text": "...", "because": [出来事の番号], "confidence": 0.6}}],
 "proposal": {{"text": "...", "because": [出来事の番号]{pen}{fields_prop(state)}}},
 "votes": [{{"id": "L0", "against": "反対する理由", "agree": true, "reason": "決めた理由"}}],
{' "year_name": "...",' + chr(10) if era2.year_end(state) else ''} "feeling": "..."}}"""
    return fix_text(state, out)


# ---------------- まわりの集落 (4.B。地域の決まりは region.py) ----------------
# 川辺の村は「V0」として加わる。人数・蓄え・役の段は、毎回 state から数える (_v0)。まわりの集落は g6.others の同じ辞書 (G6 の鍵はそのまま)。
# 年の終わり (4.G.1 の 8・9): 地域の 1 年 (塩 59) → 病 (塩 71) → 寄る年の目印。次の歩のはじめ (夏の集まりの日): 集まりの答え → 待ち → 続く貢ぎ。
# 戦の日は era2._day から (交換に行くのあと)。村が知らない地域のこと (遠くの戦など) は出来事にせず、g7.region.log だけに書く【シ】
V0_KCAP = 10 ** 6  # 村の暮らせる人数は地図の K でなく、世界の計算で決まる
NEAR_WAR = 2  # 1 日 (2 ます) 以内の戦は、出来事「よその村」として村に届く (交換の相手の戦も)
VILLAGE_KINDS = ("求め", "貢ぎ", "戦", "同盟", "崩れ", "集落", "逃げる")  # 村がかかわる地域の出来事の種類 (4.B.7。どれも G6 までは使っていない)
WAR_NEXT_DAY = 9  # 村が求めて断られ、then が「戦う」なら、次の季節の 10 日目に戦 (乱数なし。4.B.5)
STANCES = ("求める", "守る", "ふつう")


def _reg(state):
    return _g(state)["region"]


def region_on(state):
    """地域の決まりが働くか (G7 から。world.G7_PARTS["region"] は試しで止めるためだけの切りかえ)"""
    return "g7" in state["era2"] and world.G7_PARTS["region"]


def _v0_org(state):
    """村の役の段 (4.B.5): まとめ役がいれば 1。この 1 年に「取り立てる」か「守る」をした役の人 (役の仕事を合わせて 20 日以上) がいれば 2"""
    rd = _g(state).get("role_days") or {}
    if any(n in rd and (rd[n].get("取り立てる") or rd[n].get("守る")) for n in role_people(state)):
        return 2
    return 1 if era2._leader(state) else 0


def _v0(state):
    """川辺の村 (V0) の見た目 (地域の決まりが読むもの。毎回 state から数え、手で数を入れない)"""
    e2, reg = state["era2"], _reg(state)
    vs = reg.setdefault("v0", {"commit": {}, "conflict": None})
    w = reg.get("weather") or {}
    y = (state["day"] + 1) // YEAR
    bad = state["day"] if w.get("year") in (y, state["day"] // YEAR) and "V0" in w.get("bad", []) else None
    return {"id": "V0", "name": "川辺の村", "village": True, "people": _pop(state), "cell": list(region.VILLAGE), "land": region.land(region.VILLAGE),
            "kcap": V0_KCAP, "org": _v0_org(state), "grain": era2._g6_have(state, "村", "草の種"),
            "goats": sum(1 for x in e2["goats"] if x.get("owner") is None), "tech": 1, "walls": e2.get("walls"), "commit": vs["commit"],
            "stance": "ふつう", "known": 0, "bad": bad, "conflict": vs.get("conflict")}


def _setts(state):
    return [_v0(state)] + [o for o in _others(state) if not o.get("gone")]


def _maker(state):
    def make(parent, cell, n, kind):
        o = _new_settlement(state, cell, n)
        o.update(kind=kind, grain=0, goats=0, pots=0, sickles=0, pots_f=0.0, sickles_f=0.0, cattle_f=0.0, trust=0.5)
        return o
    return make


def _hook(state, moves):
    """続く貢ぎの、村の出し入れ (村の蓄えの草の種から。足りないときは家の倉から、倉の量に合わせて出す。4.B.5)"""
    def hook(t, n, how):
        if how == "受ける":
            era2._g6_put(state, "村", {"草の種": n})
            moves.setdefault(t["id"], []).append(era2._mv("村", 1, {"草の種": n}))
            return n
        got = era2._g6_take(state, "村", {"草の種": n}).get("草の種", 0)
        mv = [era2._mv("村", -1, {"草の種": got})] if got else []
        rest = n - got
        if rest > 0:
            have = {h: era2._g6_have(state, h, "草の種") for h in sorted(era2._homes(state))}
            tot = sum(have.values())
            for h in [h for h in have if have[h] > 0]:
                k = min(have[h], rest, math.ceil((n - got) * have[h] / tot)) if tot else 0
                if k > 0:
                    era2._g6_take(state, h, {"草の種": k})
                    mv.append(era2._mv(h, -1, {"草の種": k}))
                    rest -= k
        moves.setdefault(t["id"], []).extend(mv)
        return n - max(0, rest)
    return hook


def _partners(state):
    """この 1 年に交換した集落 (G6 の contacts)"""
    D = state["day"]
    return {o["id"] for o in _others(state) if any(c > D - YEAR for c in o.get("contacts", []))}


def _region_after(state, setts, out, moves=None):
    """地域の決まりのあと: 村の見た目を書きもどし、なくなった集落を g6.others から外し、出来事を書く。
    村がかかわる出来事 → その種類で。1 日 (2 ます) 以内か交換の相手の戦 → 「よその村」。ほかは g7.region.log だけ"""
    reg, D = _reg(state), state["day"]
    v0 = next(s for s in setts if s["id"] == "V0")
    reg["v0"]["conflict"] = v0.get("conflict")
    by = region._by(setts)
    part = _partners(state)
    for ev in out:
        who = ev["who"]
        if "V0" in who:
            for x in who:
                if x != "V0" and x in by and by[x].get("known") is None:
                    by[x]["known"] = D  # 求め・戦・貢ぎでかかわった集落は、村が知る (4.B.2)
            mv = (moves or {}).get(ev["data"].get("tie")) if ev["kind"] in ("貢ぎ", "崩れ") else None
            log(state, ev["kind"], None, ev["text"], region=True, **ev["data"], **({"moves": mv} if mv else {}))
        elif ev["kind"] == "戦" and any(x in by and by[x].get("known") is not None and
                                        (region.dist(region.cell_of(by[x]), region.VILLAGE) <= NEAR_WAR or x in part) for x in who):
            log(state, "よその村", None, ev["text"], region=True, **ev["data"])
        else:
            reg["log"].append({"day": D, "kind": ev["kind"], "text": ev["text"], "who": who, **ev["data"]})
    drop_gone(state)


def drop_gone(state):
    """なくなった集落を g6.others から外す (G6 のコードには見えなくなる。返されていない貸し借りは、1 年たつと今のまま「返されない」)。
    交換に行く途中の人の行き先は、季節の終わり (G6 の季節の終わりの 0. で帰る) まで残す。そのあいだは、村が知らない集落として扱う (来ない・申し出もない)"""
    g6 = era2._g6(state)
    going = {tr.get("to") for tr in g6.get("trips", {}).values() if tr.get("state") == "行く"}
    for o in g6["others"]:
        if o.get("gone") and o["id"] in going:
            o["known"] = None
    g6["others"] = [o for o in g6["others"] if not o.get("gone") or o["id"] in going]
    # なくなった集落の、まだ決めていない申し出も外す (2026-10-22: 残すと、お題の「ほかの村」の節 (era2._g6_text) で集落が見つからず止まっていた)。
    # 交換に行く途中の人のために残した集落も、なくなっていれば申し出はない (来ない・申し出もない)
    live = {o["id"] for o in g6["others"] if not o.get("gone")}
    if any(off.get("other") not in live for off in g6.get("offers", [])):
        g6["offers"] = [off for off in g6["offers"] if off.get("other") in live]


def region_year(state):
    """年の最後の日の季節の終わり (4.G.1 の 8・9): 地域の 1 年 (塩 59) → 病 (塩 71) → 寄る年の目印 → 決める段の記録【シ】"""
    if not region_on(state):
        return
    reg, D = _reg(state), state["day"]
    y = (D + 1) // YEAR
    setts = _setts(state)
    out = region.year_end(reg, setts, era2._rng(state, era2.REGION_SALT), y, D, out=[])
    _sick_year(state, setts, y, out)
    _region_after(state, setts, out)
    _yoru(state, y)
    _levels_log(state)


def _sick_year(state, setts, y, out):
    """病 (4.F の 7。塩 71): 村 → まわりの集落の番号の順に 1 回ずつ。村でははやる季節も引く (響きは世界の側。g7.sick に残す)"""
    reg, D, g = _reg(state), state["day"], _g(state)
    rng = era2._rng(state, era2.SICK_SALT)
    last = set(reg.get("sick_last") or [])
    part = _partners(state)
    now = []
    for s in region._live(setts):
        mine = {t["payer"] if t["payee"] == s["id"] else t["payee"] for t in region.ties_on(reg) if s["id"] in (t["payer"], t["payee"])}
        links = (part | mine) if s["id"] == "V0" else ({x for x in ("V0",) if s["id"] in part} | mine)
        hit, p = region.sick(rng, s, len(links), bool(links & last))
        if not hit:
            continue
        now.append(s["id"])
        if s["id"] == "V0":
            g["sick"] = {"year": y, "season": SEASONS[rng.randrange(4)], "p": round(p, 5), "day": D}
        else:
            k = round(s["people"] * rng.uniform(*region.SICK_DEATH))
            s["people"] -= k
            region._ev(out, "病", f"{region._name(s)} で病がはやり、{k} 人が亡くなった", [s["id"]], dead=k)
    reg["sick_last"] = now
    region.collapse(reg, setts, D, out)


def _yoru(state, y):
    """寄る年の目印 (4.A.7 の Z1〜Z3)。g7._zoom が読む"""
    reg, D = _reg(state), state["day"]
    lo = D - YEAR + 1
    reg["yoru"] = {"year": y,
                   "Z1": any(q["to"] == "V0" and not q.get("end") for q in reg.get("demands", [])),
                   "Z2": any("V0" in (w["att"], w["def"]) and w.get("done") is not None and lo <= w["done"] <= D and not w.get("called_off")
                             for w in reg.get("wars", [])),
                   "Z3": any("V0" in (t["payer"], t["payee"]) and t.get("end") is not None and lo <= t["end"] <= D for t in reg.get("ties", []))}


def _paid_ties(state):
    D = state["day"]
    return [t for t in region.ties_on(_reg(state)) if t["paid"] and t["paid"][-1] > D - YEAR]


def levels(state):
    """決める段 (4.D.2) を、今の地域で数える (村の役の人は、取り立てた物を村の蓄えに入れた人。yardstick.officials)"""
    return yardstick.levels(state)


def _levels_log(state):
    reg = _reg(state)
    lv = levels(state)
    reg["log"].append({"day": state["day"], "kind": "段", "levels": [{k: g[k] for k in ("top", "D", "T", "office", "village", "B")} | {"n": len(g["members"])}
                                                                    for g in lv if len(g["members"]) > 1 or g["top"] == "V0"]})


def begin(state, village=None, councils=None):
    """次の歩のはじめ (4.G.1。年の集まりの歩も、答えのない歩も同じ): 1 まわりの集落の集まりの答え → 2 待ち → 3 続く貢ぎの今年の分 → 4 村の答え (呼んだ側)。
    1〜3 は夏の集まりの日 (年のはじめ) だけ。village: 川辺の村の、求めへの答え ({Q 番号: 手, "ally": 番号})"""
    D = state["day"]
    if not region_on(state) or (D + 1) % YEAR:
        return None
    reg = _reg(state)
    if councils is not None:
        apply_councils(state, councils)
    setts, moves = _setts(state), {}
    out = region.decide(reg, setts, D + 1, village=village or {}, make=_maker(state), out=[])
    region.pay_ties(reg, setts, D + 1, pay_hook=_hook(state, moves), out=out)
    _coll_ties(state, moves)
    _village_wars(state)
    _region_after(state, setts, out, moves)
    return out


def _coll_ties(state, moves):
    """村が出した・受けた貢ぎを、この季節の取り立て (g7.coll。記録をつける人が「取り立て」で残す。4.D.3) に足す"""
    reg, g = _reg(state), _g(state)
    for tid, mv in sorted(moves.items()):
        t = next((x for x in reg.get("ties", []) if x["id"] == tid), None)
        n = sum(m[2].get("草の種", 0) for m in mv)
        if t and n:
            g.setdefault("coll", []).append({"day": state["day"], "kind": "貢ぎ出す" if t["payer"] == "V0" else "貢ぎ受ける", "tie": tid,
                                             "other": t["payee"] if t["payer"] == "V0" else t["payer"], "goods": {"草の種": n}})


def _village_wars(state):
    """村がかかわる戦の季節 (仕事「戦に出る」を選べる季節。4.F の 1)"""
    g, reg = _g(state), _reg(state)
    ws = sorted(w["day"] for w in reg.get("wars", []) if not w.get("done") and "V0" in (w["att"], w["def"]))
    g["war_season"] = ws[0] // SEASON_DAYS * SEASON_DAYS if ws else None


def region_day(state):
    """戦の日 (era2._day の交換に行くのあと。4.B.5): 戦ごとの種 (G7|世界の種|戦|番号)。村が攻めるときは「戦に出る」の人、
    守るときはその日キャンプにいる大人 (「守る」の人は 1、ほかの大人は 0.5) が戦う。死ぬ人は戦った人の名前の順に並べて引く"""
    if not region_on(state):
        return
    reg, D = _reg(state), state["day"]
    due = sorted((w for w in reg.get("wars", []) if not w.get("done") and w["day"] == D), key=lambda w: int(w["id"][1:]))
    if not due:
        return
    setts, out = _setts(state), []
    for w in due:
        by = region._by(setts)
        if w["att"] not in by or w["def"] not in by or by[w["att"]].get("gone") or by[w["def"]].get("gone"):
            w.update(done=D, called_off=True)
            continue
        rng = region.war_rng(state["seed"], int(w["id"][1:]))
        own, fighters = None, []
        if "V0" in (w["att"], w["def"]):
            ads = era2.adults(state)
            if w["att"] == "V0":
                fighters = [p for p in ads if (p.get("today") or {}).get("activity") == "戦に出る" and not era2._injured_today(p)]
                if not fighters:
                    w.update(done=D, called_off=True)
                    q = next((x for x in reg["demands"] if x["id"] == w.get("demand")), None)
                    if q:
                        q.update(end=D, result="戦わなかった")
                    region._ev(out, "求め", f"村から戦に出る人がいなかったので、{region._name(by[w['def']])} との戦 ([{w.get('demand')}]) はしなかった",
                               ["V0", w["def"]], demand=w.get("demand"), war=w["id"])
                    continue
                for p in fighters:
                    p["today"]["away"] = True
                own = {"S": float(len(fighters)), "n": len(fighters)}
            else:
                fighters = [p for p in ads if not (p.get("today") or {}).get("away")]
                own = {"S": sum(1.0 if (p.get("today") or {}).get("activity") == "守る" else 0.5 for p in fighters), "n": len(fighters)}
        region.fight(reg, setts, w, rng, D, own=own, out=out)
        if own is not None:
            _war_village(state, w, fighters, rng, out)
    _village_wars(state)
    _region_after(state, setts, out)


def _war_village(state, w, fighters, rng, out):
    """村の戦のあと: 死んだ人 (戦った人の名前の順に並べて、戦の列で引く)・取られた物か、取った物"""
    k = min(len(fighters), w["dead"].get("V0", 0))
    names = rng.sample(sorted(p["name"] for p in fighters), k) if k else []
    w["dead_names"] = names
    for n in names:
        p = next(q for q in state["people"] if q["name"] == n)
        p["alive"] = False
        log(state, "死", n, f"{n} ({p['age']} 歳) が戦で亡くなった", war=w["id"])
        era2._inherit(state, p)
    if names:
        era2._check_leader(state)
    lost = (w["def"] == "V0") == bool(w["att_win"])
    other = w["att"] if w["def"] == "V0" else w["def"]
    if lost:
        share = w["loot"]["share"]
        goods = {"草の種": int(era2._g6_have(state, "村", "草の種") * share), "ヤギ": int(era2._g6_have(state, "村", "ヤギ") * share)}
        ids = []
        took = era2._g6_take(state, "村", {k: n for k, n in goods.items() if n > 0}, ids)
        o = next((x for x in _others(state) if x["id"] == other), None)
        if o:
            era2._node_add(o, took, 1)
        w["village_loot"] = took
        log(state, "戦", None, f"戦に負け、村の蓄えから {era2._gw(took)} を取られた", war=w["id"], moves=[era2._mv("村", -1, took, ids)])
    else:
        got = {k: n for k, n in (("草の種", w["loot"]["草の種"]), ("ヤギ", w["loot"]["ヤギ"])) if n > 0}
        if got:
            ids = []
            era2._g6_put(state, "村", got, (), ids)
            w["village_loot"] = got
            log(state, "戦", None, f"戦に勝ち、{era2._gw(got)} を持ち帰った", war=w["id"], moves=[era2._mv("村", 1, got, ids)])


# ---- 村の答え (4.B.5): 求めへの答え・村が求める・家ごとに出ていく ----

def _vote_weights(state, real):
    """答えた人ごとの票の重み: その人が答える大人 (自分と、自分で答えない家族) と、手本として受け持つ家の大人 (4.A.4 の 5 の数え方)"""
    e2, g = state["era2"], _g(state)
    if not e2.get("rep_mode"):
        return {n: 1 for n in real}
    reps = _rep_of(state)
    n_ad = {}
    for p in era2.adults(state):
        n_ad[p.get("household")] = n_ad.get(p.get("household"), 0) + 1
    out = {}
    for n in real:
        h = next((p.get("household") for p in era2.adults(state) if p["name"] == n), None)
        if reps.get(h) == n:
            own = n_ad.get(h, 0) - sum(1 for m in real if m != n and next((p.get("household") for p in era2.adults(state) if p["name"] == m), None) == h)
            out[n] = own + sum(n_ad.get(x, 0) for x, d in (g.get("donor") or {}).items() if d == h and x not in g.get("sample", {}))
        else:
            out[n] = 1
    return out


def _tally(state, votes, weights):
    """_g6_decide と同じ形: 広げた票で大人の半分をこえればその手、なければまとめ役の答え、それもなければいちばん多い手 (同じなら手の順)。votes: {名前: 手}"""
    if not votes:
        return None, ""
    n = len(era2.adults(state))
    t = {}
    for who, v in votes.items():
        t[v] = t.get(v, 0) + weights.get(who, 1)
    lead = era2._leader(state)
    best = min(t, key=lambda k: (-t[k], str(k)))
    txt = "・".join(f"{k} {v}" for k, v in sorted(t.items(), key=lambda kv: -kv[1])) + f" / 大人 {n}"
    if t[best] * 2 > n:
        return best, txt
    if lead in votes:
        return votes[lead], txt + " (まとめ役の答え)"
    return best, txt + " (いちばん多い手)"


def _oid(v):
    m = era2._num(v)
    return f"N{m}" if m else None


def village_answers(state, real):
    """答えた人の求めへの答え (answer_demand・ally) を、広げた票で 1 つにする (4.B.5)。戻り値: region.decide の village"""
    qs = [q for q in _reg(state).get("demands", []) if q["to"] == "V0" and not q.get("end")]
    if not qs:
        return {}
    w = _vote_weights(state, real)
    out = {}
    for q in qs:
        votes = {}
        for n, a in real.items():
            ad = a.get("answer_demand") if isinstance(a.get("answer_demand"), dict) else {}
            v = next((str(x) for k, x in ad.items() if f"Q{era2._num(k)}" == q["id"]), None)
            ch = next((c for c in region.CHOICES["求められた"] if v and c in v), None)
            if ch:
                votes[n] = ch
        ch, txt = _tally(state, votes, w)
        if ch:
            out[q["id"]] = ch
            q["votes"] = txt
            if ch == "助けを頼む":
                allies = {}
                for n in votes:
                    if votes[n] == ch and _oid(real[n].get("ally")):
                        allies[_oid(real[n].get("ally"))] = allies.get(_oid(real[n].get("ally")), 0) + w.get(n, 1)
                out["ally"] = min(allies, key=lambda k: (-allies[k], region.num(k))) if allies else None
    return out


def leave_households(state, real):
    """家ごとに村を出る (4.B.5。leave: true。答えた家だけ (まねない)。出ていけるのは era2._can_leave のとき)。出た家は、次の季節の終わりに
    「分かれた家」の集落になる (G6 の決まり)。G5 の「1 年に 1 家まで」は、もめごとで出るときの決まりなので当てない"""
    if not _leave_on(state):
        return []
    why = "ほかの村の求め" if _demands_to_village(state) else "ほかの村への貢ぎ" if _village_pays(state) else "村の取り立て"
    reps, out = _rep_of(state), []
    for n, a in real.items():
        p = next((q for q in era2.adults(state) if q["name"] == n), None)
        h = p and p.get("household")
        if not h or reps.get(h) != n or a.get("leave") is not True or not era2._can_leave(state, h):
            continue
        _leave(state, h, why)
        out.append(h)
    return out


def _leave(state, h, why):
    """家の人みんな (子も) で村を出る (era2._split の形。家のヤギと家の倉の食べ物は持って行き、家の畑は村のものになる)"""
    e2, g5, day = state["era2"], era2._g5(state), state["day"]
    ppl = sorted([q for q in state["people"] if q["alive"] and q.get("household") == h], key=lambda q: -q["age"])
    names = {q["name"] for q in ppl}
    ppl += [c for c in era2.children(state) if c.get("mother") in names and c["name"] not in names]
    for q in ppl:
        q["alive"], q["left"] = False, day
    goats = [x for x in e2["goats"] if x.get("owner") == h]
    e2["goats"] = [x for x in e2["goats"] if x.get("owner") != h]
    st = era2._house(state, h)
    kcal, food = sum(f["kcal"] for f in st["store"]), world.food_words(world.holdings({"food": st["store"]}))
    st["store"] = []
    fields = [f for f in e2["fields"] if f.get("owner") == h and f["state"] in ("育つ", "実った")]
    for f in fields:
        f["owner"] = None
    for x in g5["disputes"]:
        if x["status"] == era2.OPEN and h in (x["from"], x["against"]):
            x.update(status="去った", end=day)
    g5["fissions"].append({"day": day, "household": h, "people": [q["name"] for q in ppl], "goats": len(goats), "store": round(kcal),
                           "fields": len(fields), "dispute": None, "why": why})
    took = "・".join(x for x in (f"ヤギ {len(goats)} 頭" if goats else "", f"家の倉の {food}" if kcal else "") if x)
    log(state, "分かれる", ppl[0]["name"], f"{why}から逃れて、{h}の " + "・".join(q["name"] + (" (子)" if q.get("child") else "") for q in ppl)
        + " が、家の人みんなで村を出ていった" + (f"。{took} を持って行った" if took else "") + (f"。{h}の畑 {len(fields)} 枚は村のものになった" if fields else ""),
        household=h, why=why)
    era2._check_leader(state)


def village_demand(state, real):
    """村が求める (4.B.5): demand を書いた人の票を、相手ごとに広げた票で数える。大人の半分をこえるか、まとめ役が書けば求める。
    相手の答えは、その年は決まり (8.)。断られて then が「戦う」なら、次の季節の 10 日目に戦 (乱数なし)"""
    if not region_on(state):
        return None
    reg, D = _reg(state), state["day"]
    w = _vote_weights(state, real)
    votes, what = {}, {}
    for n, a in real.items():
        d = a.get("demand")
        if not isinstance(d, dict):
            continue
        to = _oid(d.get("to"))
        o = next((x for x in _others(state) if x["id"] == to and x.get("known") is not None), None)
        goods = era2._g6_goods(d.get("what"))
        amt = sum(era2.VALUE.get(k, 0) * v for k, v in goods.items())
        if not o or amt <= 0:
            continue
        votes[n] = to
        what.setdefault(to, (n, amt, "戦う" if "戦" in str(d.get("then") or "") else "やめる"))
    to, txt = _tally(state, votes, w)
    if not to:
        return None
    lead = era2._leader(state)
    tot = sum(w.get(n, 1) for n, v in votes.items() if v == to)
    if not (tot * 2 > len(era2.adults(state)) or votes.get(lead) == to):
        return None
    n0, amt, then = what[to] if votes.get(lead) != to else (lead, *what[to][1:])
    if votes.get(lead) == to:
        d = real[lead]["demand"]
        amt = sum(era2.VALUE.get(k, 0) * v for k, v in era2._g6_goods(d.get("what")).items()) or amt
        then = "戦う" if "戦" in str(d.get("then") or "") else "やめる"
    setts = _setts(state)
    by = region._by(setts)
    out = []
    t = by[to]
    q = region.add_demand(reg, by["V0"], t, {"草の種": amt}, D, war_day=D + 1 + SEASON_DAYS + WAR_NEXT_DAY, then=then, out=out,
                          who_text=f"村の集まりで、{region._name(t)} に毎年 草の種 {amt} つかみ を出すように求めることにした ({txt})")
    q["votes"] = txt
    c, ally, ref = region.costs(reg, setts, t, by["V0"], amt)
    ch = region.pick(c)
    if ch == "戦う" and then != "戦う":
        q.update(answer="戦う", how="決まりで選んだ", end=D, result="やめた")
        region._ev(out, "求め", f"{region._name(t)} は求め [{q['id']}] を断った。村は求めをやめた", ["V0", to], demand=q["id"])
    else:
        region.answer(reg, setts, q, ch, ally, D, "決まりで選んだ", out, _maker(state))
    moves = {}
    if ch == "払う":
        tie = next(x for x in reg["ties"] if x.get("demand") == q["id"])
        region.pay_ties(reg, setts, D, pay_hook=_hook(state, moves), out=out, only={tie["id"]})
        _coll_ties(state, moves)
    _village_wars(state)
    _region_after(state, setts, out, moves)
    return q


# ---- まわりの集落の集まり (4.B.6): 分かれ目の年だけ、集落ごとに 1 体 ----

def council_prompt(state, sid):
    """まわりの集落の集まりのお題 (見て分かることだけ。勝つ見込みや【シ】の数は出さない)"""
    reg = _reg(state)
    setts = _setts(state)
    by = region._by(setts)
    s = by[sid]
    pts = (reg.get("councils") or {}).get("points", {}).get(sid, [])
    rows = []
    for x in sorted(region._live(setts), key=lambda x: (region.dist(region.cell_of(x), region.cell_of(s)), region.num(x["id"]))):
        if x["id"] == sid or region.dist(region.cell_of(x), region.cell_of(s)) > region.REACH2:
            continue
        dd = region.days(region.cell_of(x), region.cell_of(s))
        rows.append(f"- {region._name(x)}: 歩いて {dd} 日 (" + ("同じ日のうち" if dd == 0 else f"{region.direction(region.cell_of(x), region.cell_of(s))}") + f")。"
                    f"約 {round(x['people'], -1) if x['people'] >= 20 else x['people']} 人" + ("・まわりに土の壁" if x.get("walls") is not None else "")
                    + ("・長の下に、ほかの村から集める役がいる" if x.get("org", 0) >= 2 else "・長がいる" if x.get("org", 0) == 1 else ""))
    hist = []
    for t in reg.get("ties", []):
        if sid in (t["payer"], t["payee"]):
            other = by.get(t["payee"] if t["payer"] == sid else t["payer"])
            nm = region._name(other) if other else "なくなった村"
            hist.append(f"- [{t['id']}] " + (f"毎年 {nm} に {region._goods(t['goods'])} を出している" if t["payer"] == sid and t["status"] == "続く"
                                            else f"毎年 {nm} から {region._goods(t['goods'])} を受けている" if t["status"] == "続く"
                                            else f"{nm} とのあいだの貢ぎは、{t['end']} 日目に終わった"))
    for w in reg.get("wars", []):
        if sid in (w["att"], w["def"]) and w.get("done") is not None and not w.get("called_off"):
            other = by.get(w["def"] if w["att"] == sid else w["att"])
            win = (w["att"] == sid) == bool(w.get("att_win"))
            hist.append(f"- {w['done']} 日目、{region._name(other) if other else 'なくなった村'} と戦い、{'勝った' if win else '負けた'}")
    asks, form = [], {}
    for pnt in pts:
        if pnt["kind"] == "求められた":
            q = next(x for x in reg["demands"] if x["id"] == pnt["demand"])
            a = by.get(q["from"])
            asks.append(f"- [{q['id']}] {region._name(a) if a else 'ほかの村'} が、毎年 {region._goods(q['what'])} を出すように求めてきた。"
                        "払う / 戦う / 逃げる (村ごと、遠くの空いた土地へ移る) / 助けを頼む (ほかの村に。頼む村を ally に) のどれか")
            form[q["id"]] = "払う か 戦う か 逃げる か 助けを頼む"
        elif pnt["kind"] == "払い続けるか":
            t = next(x for x in reg["ties"] if x["id"] == pnt["tie"])
            a = by.get(t["payee"])
            asks.append(f"- [{t['id']}] {region._name(a) if a else 'ほかの村'} に毎年 {region._goods(t['goods'])} を出している。払い続けるか、やめるか")
            form[t["id"]] = "払い続ける か やめる"
        else:
            asks.append("- 村の人が多くなった。一部の人が近くの空いた土地に分かれて住むか、分かれずに、長の下に役を置いてまとめるか")
            form["分かれるか"] = "分かれる か とどめて役を作る"
    land_word = region.LAND[s["land"]]
    choice = ", ".join(f'"{k}": "{v}"' for k, v in form.items())
    return f"""あなたは {region._name(s)} の人たちの集まり (長と年寄りたち) です。{region._name(s)} は {land_word} の土地にある、約 {s['people']} 人の村です。
戦える人は、人のおよそ 4 分の 1 です。{'まわりに土の壁があります。' if s.get('walls') is not None else ''}村の中のことは決まりで進みますが、今年は、次のことを村の集まりで決めます。

## まわりの村 (歩いて 2 日まで)
{chr(10).join(rows) or '- (近くに村はない)'}

## これまでのこと
{chr(10).join(hist) or '- (ほかの村とのあいだに、貢ぎも戦もない)'}

## 今年決めること
{chr(10).join(asks)}
- これからの構え: ほかの村に求めることもあるか (求める) / 自分からは求めず守りを固めるか (守る) / どちらでもないか (ふつう)

## 答えの形 (JSON)
{{"choice": {{{choice}}}, "ally": null, "stance": "ふつう", "say": "集まりで出た言葉を一言", "why": "そう決めたわけを一言"}}
"""


def apply_councils(state, raw):
    """まわりの集落の集まりの答えを読む (次の歩のはじめ。村の答えより先)。答えのない集落・形のおかしい答えは決まりの手 (「決まりで選んだ」)"""
    reg = _reg(state)
    c = reg.get("councils") or {}
    ans = c.setdefault("answers", {})
    for sid in c.get("ask", []):
        a = characters.parse(raw.get(sid, "")) if raw.get(sid) else {}
        got = {}
        ch = a.get("choice") if isinstance(a.get("choice"), dict) else {}
        for pnt in c.get("points", {}).get(sid, []):
            key = pnt.get("demand") or pnt.get("tie") or "分かれるか"
            v = str(next((x for k, x in ch.items() if str(k).strip("[] ") == key), "") or "")
            opts = region.CHOICES[pnt["kind"]]
            hit = [o for o in opts if o in v]
            if len(hit) == 1 or (hit and pnt["kind"] == "払い続けるか" and v.startswith(hit[0])):
                got[key] = hit[0] if len(hit) == 1 else max(hit, key=len)
        if _oid(a.get("ally")):
            got["ally"] = _oid(a.get("ally"))
        o = next((x for x in _others(state) if x["id"] == sid), None)
        st = next((x for x in STANCES if x in str(a.get("stance") or "")), None)
        if o and st:
            o["stance"] = st
        ans[sid] = got
        reg["log"].append({"day": state["day"], "kind": "集まり", "who": [sid], "answer": got, "stance": st, "rule": not got,
                           "say": str(a.get("say") or "")[:200], "why": str(a.get("why") or "")[:200]})


def region_text(state):
    """お題の「## まわりの集落」(4.B.7): 村が知っている集落だけ (名前・方角と日数・約何人・城壁・村との貢ぎ・村への求め・村がかかわった戦と 1 日以内の戦)"""
    if not region_on(state):
        return ""
    reg, D = _reg(state), state["day"]
    known = [o for o in _others(state) if o.get("known") is not None]
    if not known:
        return ""
    rows = []
    for o in known:
        ties = [t for t in reg.get("ties", []) if t["status"] == "続く" and "V0" in (t["payer"], t["payee"]) and o["id"] in (t["payer"], t["payee"])]
        tie = "".join(f"。毎年 村が {region._goods(t['goods'])} を出している [{t['id']}]" if t["payer"] == "V0" else
                      f"。毎年 村に {region._goods(t['goods'])} を出している [{t['id']}]" for t in ties)
        rows.append(f"- {o['id']} {o['name']} ({o['way']}歩いて {o['days']} 日): 約 {round(o['people'], -1) if o['people'] >= 20 else o['people']} 人"
                    + ("・まわりに土の壁" if o.get("walls") is not None else "") + (f"・牛 {int(o['cattle_f'])} 頭ほど" if int(o.get("cattle_f", 0)) >= 1 else "") + tie)
    for q in reg.get("demands", []):
        if q["to"] == "V0" and not q.get("end"):
            a = next((o for o in known if o["id"] == q["from"]), None)
            rows.append(f"- 求め [{q['id']}]: {a['name'] if a else 'ほかの村'} が、毎年 {region._goods(q['what'])} を出すように村に求めている (answer_demand で答える)")
    for w in reg.get("wars", []):
        if w.get("done") is not None and w["done"] > D - 2 * YEAR and not w.get("called_off") and "V0" in (w["att"], w["def"]):
            o = next((x for x in _others(state) if x["id"] in (w["att"], w["def"])), None)
            win = (w["att"] == "V0") == bool(w.get("att_win"))
            rows.append(f"- {w['done']} 日目、村は {o['name'] if o else 'ほかの村'} と戦い、{'勝った' if win else '負けた'}"
                        + (f" (村で亡くなった人: {'・'.join(w.get('dead_names') or [])})" if w.get("dead_names") else ""))
    return "\n## まわりの集落 (村が知っている村)\n" + "\n".join(rows) + "\n"


# ---------------- つなぎ目 (4.F。まとめ役が足した小さな形。数はみな【仮定】) ----------------
# どれも「何度も別々に生まれた仕組み」なので、G7 に入った日から使える (牛と犂だけは、便りかきっかけのあと)。村の答えがなければ何も起きない。
# 試しで止めるための切りかえ world.G7_PARTS["joints"] (いつもは True)
TAX_MAX, LOAN_MAX, LOAN_EASY = 0.5, 0.5, 0.2  # 2: 税の割合は 5 割まで / 4: 上乗せは 5 割まで。ほかの村は、悪い年でなければ 2 割をこえる上乗せでは借りない
WALL_DAYS = 1500  # 6: 村のまわりの壁は、合わせて 1,500 人日
SICK_MULT = 3  # 7: 村に病がはやった季節は、子の死と大人の病の死の見込みが 3 倍
CATTLE_VALUE, CATTLE_GIVE_AT, CATTLE_GOATS = 1125, 3, 5  # 5: 牛の値うち (ヤギ 3 頭分)・ほかの村が牛を出すのは 3 頭以上のとき・牛 1 頭はヤギ 5 頭分の草
CATTLE_BREED_AGE, PLOUGH_AGE, PLOUGH_MULT = 3, 2, 3  # 5: 3 歳以上の母牛が 2 年に 1 頭・犂を引くのは 2 歳以上の牛 2 頭・犂の畑仕事は 3 倍
CAPTIVES = ("連れて帰る", "連れて帰らない")
TRIBUTE_CHOICES = ("払い続ける", "やめる")


def joints(state):
    return "g7" in state["era2"] and world.G7_PARTS.get("joints", True)


# ---- 2・3. 掟の取り立て (tax) と換算 (rate) ----

def _share_words(x):
    return f"{round(x * 10, 1):g} 割"


def law_extra(state, law, prop):
    """掟の提案の tax・rate を読む (era2.apply_answers から。penalty (G5) と同じ形)。採用されると、文の後ろの書き添えがお題・アプリに出る"""
    if not joints(state) or not isinstance(prop, dict):
        return
    tax = prop.get("tax")
    if isinstance(tax, dict):
        what = era2._g6_good(tax.get("what"))
        try:
            share = float(tax.get("share"))
        except (TypeError, ValueError):
            share = 0.0
        if what in ("草の種", "ヤギ") and share > 0:
            share = round(min(TAX_MAX, share), 3)
            law["tax"] = {"what": what, "share": share}
            law["text"] += f" (取り立て: 家の倉の{what}の {_share_words(share)}を、年に 1 回、村の蓄えへ)" if what == "草の種" else \
                f" (取り立て: 家のヤギの {_share_words(share)}を、年に 1 回、村へ)"
    rate = prop.get("rate")
    if isinstance(rate, dict):
        n = era2._num(next((v for k, v in rate.items() if "ヤギ" in str(k)), None))
        if n > 0:
            law["rate"] = {"ヤギ": min(n, 10 ** 4)}
            law["text"] += f" (換算: もめごとの払いで、ヤギ 1 頭 = 草の種 {law['rate']['ヤギ']} つかみ)"


def tax_law(state):
    """今効いている取り立ての掟 (採用された掟のうち、いちばん新しいもの)"""
    return next((l for l in reversed(state.get("laws", [])) if l.get("status") == "採用" and l.get("tax")), None)


def collect_tax(state, frac):
    """村の中の税を集める (era2._season_end から。家族を決めたあと、記録の前。4.G.1 の 4)。乱数なし。
    仕事「取り立てる」の人が、今年まだ払っていない家から、1 人 1 日に 1 家 (家の名前の順)。自分の家からは集めず、自分の家は季節の終わりに自分で払う。
    倉が 0 の家は払わない (罰はない)。年は夏から"""
    if not joints(state):
        return
    g, D = _g(state), state["day"]
    law = tax_law(state)
    y = D // YEAR
    paid = g.setdefault("tax_year", {"year": y, "homes": [], "visited": []})
    if paid["year"] != y:
        paid.update(year=y, homes=[], visited=[])
    days = g.get("season_days") or {}
    who = sorted(n for n, a in days.items() if a.get("取り立てる") and any(p["name"] == n for p in era2.adults(state)))
    if not law or not who:
        return
    homes = sorted(era2._homes(state))
    what, share = law["tax"]["what"], law["tax"]["share"]
    for n in who:
        p = next(q for q in era2.adults(state) if q["name"] == n)
        mine = p.get("household")
        todo = [h for h in homes if h != mine and h not in paid["visited"]][:days[n]["取り立てる"]]
        if mine in homes and mine not in paid["visited"]:
            todo.append(mine)
        got_from, total, mv = [], 0, []
        for h in todo:
            paid["visited"].append(h)
            k = math.floor(era2._g6_have(state, h, what) * share) if what == "草の種" else math.floor(sum(1 for x in state["era2"]["goats"] if x.get("owner") == h) * share)
            if k <= 0:
                continue
            ids = []
            if what == "草の種":
                got = era2._g6_take(state, h, {what: k}, ids)
                era2._g6_put(state, "村", got)
            else:  # ヤギは持ち主を村にかえる (番号は変えない)
                mine_g = sorted((x for x in state["era2"]["goats"] if x.get("owner") == h), key=lambda x: (x["sex"] != "オス", x["born"]))[:k]
                for x in mine_g:
                    x["owner"] = None
                    ids.append([x["id"], x["sex"], x["born"]])
                got = {what: len(mine_g)}
            if got.get(what):
                paid["homes"].append(h)
                got_from.append(h)
                total += got[what]
                mv += [era2._mv(h, -1, got, ids), era2._mv("村", 1, got, ids)]
        if got_from:
            g.setdefault("coll", []).append({"day": D, "kind": "税", "law": law["id"], "by": n, "from": got_from, "goods": {what: total}})
            log(state, "取り立て", n, f"[{law['id']}] にしたがい、{n} が {len(got_from)} 家から {era2._gw({what: total})} を集め、村の蓄えに入れた"
                + (" (自分の家の分もふくむ)" if mine in got_from else ""), law=law["id"], homes=got_from, goods={what: total}, moves=mv)


# ---- 3. 掟を板に書く ----

def write_laws(state, keep):
    """記録をつける人が、記録をつけた日 1 日につき 1 本、まだ書いていない採用ずみの掟を粘土の板に書く (era2._g6_records から。板のときだけ。4.F の 3)"""
    if not joints(state):
        return
    g6, D = era2._g6(state), state["day"]
    if not (g6.get("open") or {}).get("板"):
        return
    laws = {l["id"]: l for l in state.get("laws", [])}
    for n, days in sorted(keep.items()):
        j = g6["jobs"].get(n) or {}
        j7 = (_g(state).get("jobs7") or {}).get(n) or {}
        if j.get("how") != "板" or ("掟" not in j.get("what", []) and not j7.get("laws")):
            continue
        order = j7.get("laws") or sorted((l for l in laws if laws[l]["status"] == "採用"), key=lambda x: int(x[1:]))
        left = days
        for lid in order:
            l = laws.get(lid)
            if left <= 0:
                break
            if not l or l["status"] != "採用" or l.get("written"):
                continue
            l["written"] = {"day": D, "by": n, "how": "板"}
            left -= 1
            log(state, "記録", n, f"{n} が、掟 [{lid}] を粘土の板に書いた", law=lid, written=True)


# ---- 3. 換算と、書いた決まりで裁く (F4) ----

def goat_worth(state):
    """もめごとの払いでヤギ 1 頭をいくらとみなすか (kcal) と、その換算の掟。採用され、板に書かれた換算の掟があれば、その数 (いちばん新しいもの)"""
    if joints(state):
        for l in reversed(state.get("laws", [])):
            if l.get("status") == "採用" and l.get("rate") and l.get("written"):
                return l["rate"]["ヤギ"] * era2.GRAIN, l
    return era2.GOAT_WORTH, None


def judged(state, d, law, paid, by, how):
    """もめごとが収まったあと (era2._verdict から): 書いた決まり (罰か換算) で裁き、実際に払わせたら、記録に残す (4.D.4)。祭りは数えない"""
    if not law or paid <= 0 or by == "祭り" or not law.get("written") or law["written"]["day"] > state["day"]:
        return
    _g(state).setdefault("judged", []).append({"day": state["day"], "dispute": d["id"], "law": law["id"], "paid": round(paid / era2.GRAIN),
                                               "by": by, "how": how, "kind": "罰" if law.get("penalty") else "換算"})


# ---- 4. 利子 ----

def collect_rate(state, c6, p, a, fam):
    """申し出の答えの上乗せ (trade の {"side": "村", "利子": 0.2})。era2.apply_answers の G6 の集まりの答えのあと"""
    if not joints(state):
        return
    tr = a.get("trade")
    for k, v in (tr.items() if isinstance(tr, dict) else []):
        if isinstance(v, dict) and era2._g6_side(v) == "村":
            r = _rate(v.get("利子"))
            if r is not None:
                c6.setdefault("rate", {}).setdefault(era2._tid(k), {})[p["name"]] = (r, len(fam))


def _rate(v):
    try:
        x = float(v)
    except (TypeError, ValueError):
        return None
    return round(max(0.0, min(LOAN_MAX, x)), 3)


def loan_rate(state, c6, off, lead):
    """貸すときの上乗せ: まとめ役が書いていればその数、なければ、大人の数でいちばん多い数 (同じなら小さいほう)"""
    rs = (c6.get("rate") or {}).get(off["id"]) or {}
    if lead in rs:
        return rs[lead][0]
    t = {}
    for r, k in rs.values():
        t[r] = t.get(r, 0) + k
    return min(t, key=lambda r: (-t[r], r)) if t else 0.0


def loan_refused(o, rate):
    """ほかの村は、悪い年なら 5 割までの上乗せで借りる。悪い年でなければ、2 割をこえる上乗せでは借りない (決まり)"""
    return rate > LOAN_EASY and o.get("bad") is None


def owed(d):
    """返す量 (上乗せのある貸し借りは goods × (1 + rate)。切り上げ)"""
    r = d.get("rate") or 0
    return {k: math.ceil(n * (1 + r) - 1e-9) for k, n in d["goods"].items()} if r else dict(d["goods"])


# ---- 5. 牛と犂 ----

def cattle_value():
    return CATTLE_VALUE


def want_cattle(state, name):
    return joints(state) and ((_g(state).get("jobs7") or {}).get(name) or {}).get("want") == "牛"


def cattle_in(state, tr):
    """交換の旅で受けとった牛を村 (か家) に入れる (乱数なし。3 歳のメスとする【仮定】)"""
    e2, D = state["era2"], state["day"]
    side = tr["side"] if tr["side"] == "村" or tr["side"] in era2._homes(state) else "村"
    herd = e2.setdefault("cattle", [])
    for _ in range(tr.get("cattle_in", 0)):
        herd.append({"id": e2.get("next_cattle", 1), "sex": "メス", "born": D - CATTLE_BREED_AGE * YEAR, "owner": None if side == "村" else side})
        e2["next_cattle"] = e2.get("next_cattle", 1) + 1
    return side


def cattle_season(state, rng, frac, sea):
    """牛の 1 季節 (era2._season_end のヤギのあと): 世話が足りないと逃げる (塩 7 の列を、ヤギのあとで引く)。春のはじめに、3 歳以上の母牛が 2 年に 1 頭 (乱数なし)"""
    e2, day = state["era2"], state["day"]
    herd = e2.get("cattle") or []
    if not herd:
        return
    if e2.get("tended_run", 0) < 5 * frac:
        gone = [c for c in herd if rng.random() < 0.15 * frac]
        for c in gone:
            herd.remove(c)
        if gone:
            log(state, "ヤギ", None, f"世話をする人が少なく、飼っていた牛 {len(gone)} 頭がいなくなった", cattle=len(gone))
    if sea == "春" and e2.get("calf_year") != (day + 1) // YEAR:
        e2["calf_year"] = (day + 1) // YEAR
        y = (day + 1) // YEAR
        born = 0
        for c in sorted(herd, key=lambda c: c["id"]):
            if c["sex"] == "メス" and day - c["born"] >= CATTLE_BREED_AGE * YEAR and (c["born"] // YEAR) % 2 == y % 2:
                i = e2.get("next_cattle", 1)
                herd.append({"id": i, "sex": "メス" if i % 2 == 0 else "オス", "born": day, "owner": c.get("owner")})
                e2["next_cattle"] = i + 1
                born += 1
        if born:
            log(state, "ヤギ", None, f"飼っている牛に、子牛が {born} 頭生まれた", calves=born)


def plough_work(state, p, h):
    """犂 (H7-06 ができたあと。2 歳以上の牛 2 頭で 1 人): 畑仕事の 1 時間を 3 時間分に数える。その季節に初めて犂を引いた日は出来事「畑」(data の plough)"""
    g = _g(state)
    if not ((g.get("jobs7") or {}).get(p["name"]) or {}).get("plough") or not _plough(state):
        return h
    D = state["day"]
    used = g.setdefault("plough_day", {"day": None, "n": 0})
    if used["day"] != D:
        used.update(day=D, n=0)
    pairs = sum(1 for c in state["era2"].get("cattle", []) if D - c["born"] >= PLOUGH_AGE * YEAR) // 2
    if used["n"] >= pairs:
        return h
    used["n"] += 1
    seen = g.setdefault("plough_seen", {})
    if seen.get(p["name"]) != state["era2"].get("step_day"):
        seen[p["name"]] = state["era2"].get("step_day")
        log(state, "畑", p["name"], f"{p['name']} が、牛 2 頭に犂を引かせて畑を耕した", plough=True)
    return h * PLOUGH_MULT


# ---- 6. 壁 ----

def wall_job(state, p):
    return joints(state) and ((_g(state).get("jobs7") or {}).get(p["name"]) or {}).get("build") == "壁" and state["era2"].get("walls") is None


def wall_day(state, p, t):
    """住まいを建てる人が、村のまわりの壁を積む (1 日 = 1 人日。合わせて 1,500 人日でできる)"""
    g = _g(state)
    g["wall_work"] = g.get("wall_work", 0) + 1
    if g["wall_work"] >= WALL_DAYS:
        state["era2"]["walls"] = state["day"]
        t.setdefault("events", []).append(log(state, "住まい", p["name"], f"{p['name']} たちの手で、村のまわりの土の壁ができた", wall=True))
    else:
        t.setdefault("events", []).append(log(state, "住まい", p["name"], f"{p['name']} が、村のまわりの土の壁を積んだ (でき具合 約 {max(1, g['wall_work'] * 10 // WALL_DAYS)} 割)",
                                              wall=True))


# ---- 7. 病 (村) ----

def sick_now(state, day):
    """day の季節が、村に病がはやる季節か (年の終わりに塩 71 で引いた g7.sick)"""
    s = _g(state).get("sick")
    return bool(s) and day // YEAR == s["year"] and season(day) == s["season"]


def sick_mult(state):
    """季節の終わり: この季節が病の季節なら 3 (子の死と大人の病の死。乱数を引く回数は同じ)"""
    return SICK_MULT if joints(state) and sick_now(state, state["day"]) else 1


def sick_start(state):
    """季節のはじめ (答えを当てはめるとき): これからの季節が病の季節なら、出来事「病」(【村】)"""
    D = state["day"]
    s = _g(state).get("sick")
    if joints(state) and sick_now(state, D + 1) and s.get("logged") != D + 1:
        s["logged"] = D + 1
        log(state, "病", None, "この季節、村に病がはやっている")


# ---- 8. 戦に勝ったとき・貢ぎをやめる (村の答え) ----

def captives_answer(state, real):
    """captives (連れて帰る / 連れて帰らない) を広げた票で 1 つにする。答えがなければ「連れて帰らない」(7. の 8)"""
    w = _vote_weights(state, real)
    votes = {n: next((c for c in CAPTIVES if c == str(a.get("captives") or "").strip()), None) for n, a in real.items()}
    votes = {n: v for n, v in votes.items() if v}
    if not votes:
        return
    ch, txt = _tally(state, votes, w)
    _g(state)["captives"] = {"day": state["day"], "choice": ch, "votes": txt}


def tribute_answers(state, real):
    """村が出している貢ぎを、払い続けるか、やめるか (tribute: {"K1": "やめる"})。広げた票で 1 つにする。答えのないつながりは払い続ける"""
    out = {}
    if not region_on(state):
        return out
    w = _vote_weights(state, real)
    for t in [t for t in _reg(state).get("ties", []) if t["payer"] == "V0" and t["status"] == "続く"]:
        votes = {}
        for n, a in real.items():
            tr = a.get("tribute") if isinstance(a.get("tribute"), dict) else {}
            v = next((str(x) for k, x in tr.items() if f"K{era2._num(k)}" == t["id"]), None)
            ch = next((c for c in TRIBUTE_CHOICES if v and c in v), None)
            if ch:
                votes[n] = ch
        ch, txt = _tally(state, votes, w)
        if ch:
            out[t["id"]] = ch
            t.setdefault("votes", []).append({"day": state["day"], "choice": ch, "votes": txt})
    return out
