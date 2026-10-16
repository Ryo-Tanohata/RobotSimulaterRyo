"""G7 (王と役所) から働く仕組み (docs/society_phase/G7_design.md。2026-10-16 本人が「すべておすすめで」決めた)

- G7 に入るのは step.py next_part だけ (第 4 部の終わりで止まり、まとめのあと本人が「進めて」と言ってから)。
  G6 までは、このファイルを読みこみもしない (era2 は state["era2"] に "g7" があるときだけ、関数の中で読みこむ)。
  だから G1〜G6 は、お題・state・出来事・乱数が前と 1 バイトも変わらない (tools/test_g7.py で確かめる)
- ここにあるもの (土台): G7 の state の形 (4.H)・G7 に入る (4.E.1)・止まるわけ (4.E.2)・史実のずれの直し (4.E.4。束 A・6〜8・9.1。
  どれも G7 に入った日から)・まわりの集落の土台 (地図・はじめの集落・地域の天気。region.py)・役の仕事の日数 (4.F の 1)
- 年 1 回の答えと見本の家 (4.A)・地域の 1 年 (4.B)・よその便り (4.C)・物差し (4.D)・つなぎ目のほかのもの (4.F) は、このあとで足す。
  季節の終わりの順 (4.G.1) は season_end に、その順で足していく
- 乱数の塩 (4.G.2) は era2 の頭 (HINT_SALT など)。ここで使うのは 53 (地域の天気) と 79 (はじめの集落。G7 に入る日だけ)
"""
import json
import math
from pathlib import Path

import era2
import region
import world
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
# お題に出す決まりの文 (era2.FACTS_G7) のうち、今使えるもの (4.F の 8)。仕組みを入れた部分が、ここに足していく
FACTS_ON = {"guard": lambda state: True}


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
        # 年 1 回の答え (4.A): 入った季節にすぐ年の集まりをする。飢えで区切った日に入ったなら、寄る年の集まり
        "ask": "年" if (D + 1) % SEASON_DAYS == 0 else "寄る", "answer_day": D,
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
    ind = era2.indicators(state)
    state["era_log"].append({"era": "G7", "day": D, "indicators": ind, "how": "next_part", "fix_from": D + 1})
    state["era_info"] = {"era": "G7", "name": era2.NAMES2["G7"], "next": era2.CRITERIA["G7"][0], "met": False, "since": 0, "indicators": ind}
    state["hold"] = False
    # 「フェーズが…に進んだ」の形にはしない (ワークフローが止まらないように。start2 と同じ形)
    log(state, "フェーズ", None, f"第 5 部「{era2.PARTS[5]}」を始めた: フェーズ G7 ({era2.NAMES2['G7']})")
    _offer(state)
    return g


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
    if any(t.get("open") and not t.get("done") for t in ((g.get("hints") or {}).get("tech") or {}).values()):
        on.add("試す")
    return [a for a in ACTS7 if a in on]


def new_season(state):
    """季節のはじめ (答えを当てはめる前): この季節の仕事の日数・子の手伝い・季節のはじめのヤギの数を空にする"""
    g = _g(state)
    g["season_days"], g["kid_jobs"], g["herd0"] = {}, {}, _herd(state)


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
    """G7 の役の仕事の 1 日 (守るは見張るだけで、何も作らない。取り立てる・戦に出る・試すは、それぞれの仕組みの部分が働きを足す)"""
    t.setdefault("events", []).append(log(state, act, p["name"], ROLE_TEXT[act].format(n=p["name"])))


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
    """era2.pasture_cap から: 村が悪い年 (その日の年) は、草で養えるヤギの数 K を ×0.8 (10 頭単位)"""
    if not (fix(state) and world.G7_PARTS["weather"]) or not _bad_year(state, state["day"] // YEAR):
        return cap
    return int(round(cap * PASTURE_BAD / 10)) * 10


# ---------------- 記録 (直し 9.1: 配給・働いた日・家畜の帳簿) ----------------

def whats(state):
    """G7 で足す記録の種類 (粘土の板が使えるとき)"""
    if fix(state) and ((state["era2"].get("g6") or {}).get("open") or {}).get("板"):
        return ("配給", "働いた日", "家畜")
    return ()


def _workdays(state):
    """この季節の、人ごとの働いた日 (休むは数えない)"""
    return {n: {a: d for a, d in acts.items() if a != "休む"} for n, acts in sorted(_g(state).get("season_days", {}).items())}


def ledger_need(state, flow, ws):
    """帳簿に要る数え札の数 (era2.TOKEN と同じ数え方: 草の種 100 つかみ・働いた日 10 日・ヤギ 1 頭に 1 個)"""
    need = {}
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
    """お題の欄 (と決まりの文) が初めてお題に出た日を残す (4.F の 8)。お題は保存のあとに書くので、季節の終わり (と G7 に入る日) に、次のお題に出るものを数える"""
    off = _g(state).setdefault("offered", {})
    for k in era2.FACTS_G7:
        if k in FACTS_ON and FACTS_ON[k](state):
            off.setdefault(k, state["day"])


def text(state, p):
    """G7 のお題の節 (season_prompt の「ほかの村・印・記録」のあと)"""
    return _ledger_text(state)


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


def fix_text(state, text_):
    """季節と気持ちのお題を、直しのあとの決まりの文にする"""
    if not fix(state):
        return text_
    for a, b in FIX_TEXT:
        text_ = text_.replace(a, b)
    return text_


# ---------------- 季節の終わり (era2._season_end から。G6 の季節の終わりのあと。4.G.1) ----------------

def season_end(state, frac):
    """G7 の季節の終わり。順は 4.G.1 (8 地域の 1 年 → 9 病 → 10 見本の家 → 11 便り → 12 きっかけ → 13 物差しと次の歩の ask) を、
    それぞれの部分を入れるときに、ここに足す。今は、前の 1 年の仕事の日数と、お題に出る欄の日を残すだけ (乱数なし)"""
    g, D = _g(state), state["day"]
    homes = {p["name"]: p.get("household") for p in state["people"]}
    days = g.get("season_days") or {}
    g["past"] = [s for s in g.get("past", []) if s["day"] > D - YEAR] + [  # 前の 1 年 (120 日) の季節だけ (途中で区切った季節も 1 つ)
        {"day": D, "season": season(D), "days": days, "home": {n: homes.get(n) for n in sorted(days)}}]
    _derive(g)
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
            "g7_region_people": sum(o["people"] for o in _others(state))}
