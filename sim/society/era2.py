"""Society 2.0 (農耕社会): 1 回 = 1 季節 (30 日) で進める。計画は docs/society2_phase_plan.md、文献は docs/society2_research.md

- 季節のはじめに、大人 (15 歳以上) だけがお題に答える (この季節の仕事・話・掟・覚えること・受け入れ など)
- 世界は 30 日を 1 日ずつ自動で計算する (world.simulate_day と world.evening を使う)。食べ物は「その日に食べる分を手元に残し、
  残りは蓄えに入れ、足りなければ蓄えから取る」を自動で行う (【仮定】Society 2.0 では日々の出し入れは村の決まりとして自動)
- 子は答えない。世界の仕組みで蓄えから食べて育ち、15 歳で大人になる
- 年: 1 年 = 4 季節 = 120 日。体の速さ (年齢・子が生まれる間隔・死亡) は縮めない
(2026-10-07 追加。本人の了承「おすすめの通りでお願いします」)
"""
import math
import random
import re

import characters
import knowledge
import world
from world import (BASE_KCAL, FRUIT_KCAL, H, SEASON_DAYS, UNITS, W, _move_food, food_words, holdings, log, season)

YEAR = 4 * SEASON_DAYS
ADULT = 15
# 現実の言葉と重ならないように作った名前 (子とよそから来る人)
NAMES = ["ナギ", "ソル", "ミラ", "ケト", "ハユ", "リオ", "トワ", "サエ", "ユノ", "カイ", "ネム", "ラタ", "フウ", "モエ", "シノ",
         "テオ", "アル", "ヨナ", "クラ", "ニイ", "エマ", "オト", "セキ", "ホノ", "ルネ", "ヤエ", "マロ", "コハ", "スイ", "ノア"]
ACTS2 = ["採集", "狩り", "探索", "休む", "道具づくり", "火おこし", "種まき", "住まいを建てる", "畑仕事", "ヤギの世話", "ヤギを捕まえる"]
ACTS_G3 = ["土器づくり"]  # G3 (余りと分業) から
CRAFTS = ("土器づくり", "道具づくり")


def era_at_least(state, era):
    e = state.get("era", "G1")
    return e in ORDER2 and ORDER2.index(e) >= ORDER2.index(era)


def acts2(state):
    return ACTS2 + (ACTS_G3 if era_at_least(state, "G3") else [])
CHILD_EAT = [(3, 800), (10, 1300), (15, 1800)]  # 【仮定】子が 1 日に食べる量 (年齢まで, kcal)
UNITS.setdefault("乳", ("杯", 150))              # 【仮定】ヤギの乳 1 杯
world.FOOD_NAME.setdefault("乳", "ヤギの乳")
world.SPOIL.setdefault("乳", 1)                  # 【仮定】乳はその日のうちに飲む
GOAT_MEAT = 20                                   # 【仮定】ヤギ 1 頭の肉 (ルクの肉の切れ、600 kcal)


# ---------------- はじまり ----------------

def start(state):
    """Society 1.0 (F6) の世界を引きついで、Society 2.0 (G1) を始める"""
    if state.get("era2"):
        return
    day = state["day"]
    for p in state["people"]:
        if p["alive"]:
            p["age"] += day // YEAR  # 489 日 ≒ 4 年たった
        p.setdefault("born_day", day - p["age"] * YEAR)
    hill = next(pl for pl in state["places"] if "丘" in pl["label"])
    state["era2"] = {"start_day": day, "fields": [], "goats": [], "wild_goats": {"place": hill["id"], "count": 15},
                     "visitors": [], "joined": [], "births": 0, "next_name": 0, "seasons": 0, "jobs": {}, "next_goat": 0, "kid_year": -1,
                     "harvest_years": [], "sown_years": [], "talk": []}
    state["era"] = "G1"
    state["era_log"].append({"era": "G1", "day": day})
    state["hold"] = False
    log(state, "フェーズ", None, "Society 2.0 を始めた: フェーズ G1 (村ができる)")
    state["phase"] = "season"


def _rng(state, salt):
    return random.Random(state["seed"] * 7349 + state["day"] * 31 + salt)


def adults(state):
    return [p for p in state["people"] if p["alive"] and not p.get("child")]


def children(state):
    return [p for p in state["people"] if p["alive"] and p.get("child")]


def _name(i):
    return NAMES[i % len(NAMES)] + ("" if i < len(NAMES) else str(i // len(NAMES) + 1))


def _new_person(state, rng, sex, age, child=False, mother=None, origin="生まれた", name=None):
    e2 = state["era2"]
    if name is None:
        name = _name(e2["next_name"])
        e2["next_name"] += 1
    names = [q["name"] for q in state["people"]]
    p = {"name": name, "alive": True, "age": age, "sex": sex, "mass": round(rng.uniform(45, 55), 1) if not child else 10.0,
         "personality": {k: round(rng.random(), 2) for k in ("協力", "大胆", "好奇心", "社交")},
         "skills": {k: round(rng.uniform(0.1, 0.4), 2) for k in ("採集", "狩り", "道具", "火")},
         "reserve": world.RESERVE_START, "hunger": 0.0, "fatigue": 0.0, "injured": 0, "food": [], "items": [],
         "trust": {n: 0.0 for n in names}, "heard": [], "plan": {"activity": "休む", "place": "camp", "with": []},
         "today": None, "knowledge": [], "feeling": "", "born_day": state["day"] - age * YEAR, "origin": origin}
    if child:
        p["child"] = True
    if mother:
        p["mother"] = mother
    for q in state["people"]:
        q.setdefault("trust", {})[name] = 0.0
    if not child:
        _give_initial_knowledge(state, p)
    state["people"].append(p)
    return p


def _give_initial_knowledge(state, p):
    for text in knowledge.INITIAL:
        p.setdefault("knowledge", []).append({"id": f"k{state['next_knowledge']}", "text": text, "confidence": 1.0, "label": "最初の知識",
                                              "because": [], "from": None, "day": state["day"], "updated": state["day"]})
        state["next_knowledge"] += 1


# ---------------- 1 季節を進める ----------------

def apply_answers(state, answers):
    """季節のはじめの答え: 話す・仕事・畑にまく量・ヤギを食べる・受け入れ・知識・掟の提案と投票・気持ち"""
    e2 = state["era2"]
    alive = {p["name"]: p for p in adults(state)}
    places = {pl["id"] for pl in state["places"]}
    e2["jobs"], accept = {}, {}
    e2["craft_days"] = {}  # この季節に、作ること (土器づくり・道具づくり) をした日数
    e2["step_day"] = state["day"] + 1
    talk = []
    g5 = era_at_least(state, "G5")
    reps = _reps(state) if g5 and e2.get("rep_mode") else set()
    c5 = {"judge": {}, "by": {}, "feast": set(), "feast_by": set(), "leader": {}, "call": {}}  # G5: 季節の集まりの答え
    for name, raw in answers.items():
        p = alive.get(name)
        if not p:
            continue
        a = characters.parse(raw)
        for s in (a.get("say") or [])[:2]:
            text = str((s or {}).get("text", ""))[:200] if isinstance(s, dict) else ""
            to = (s or {}).get("to", "みんな") if isinstance(s, dict) else "みんな"
            if text:
                eid = log(state, "話す", name, f"{name} → {to}: 「{text}」", to=to)
                talk.append({"day": state["day"], "from": name, "text": text, "event": eid, "to": to})
        knowledge.apply_updates(state, p, a.get("knowledge"))
        prop = a.get("proposal")
        if isinstance(prop, dict) and prop.get("text"):
            knowledge.propose(state, p, prop["text"], prop.get("because"))
            if g5 and _g5(state)["stage"] >= 2:  # G5 の第 2 段から、掟に罰をつけられる
                _penalty(state["laws"][-1], prop.get("penalty"))
        knowledge.vote(state, p, a.get("votes"))
        fam = family(state, name) if e2.get("rep_mode") else [p]  # 代表の答えは、家族の大人みんなの答え
        own = not (g5 and e2.get("rep_mode")) or name in reps  # G5: 家族の代表でないまとめ役は、自分の分だけ答える
        if not own:
            fam = [p]
        elif g5 and e2.get("rep_mode"):  # 代表の答えに、自分で答えたまとめ役の分は入れない
            fam = [q for q in fam if q is p or q["name"] not in answers]
        fjobs = a.get("family") if isinstance(a.get("family"), dict) else {}
        for q in fam:
            if q is not p:
                for l in state["laws"]:
                    if name in l["votes"]:
                        l["votes"][q["name"]] = l["votes"][name]
            job = (fjobs.get(q["name"]) if q is not p else None) or a.get("job") or a.get("plan") or {}
            if not isinstance(job, dict):
                job = {"activity": job} if isinstance(job, str) else {}
            act = job.get("activity") if job.get("activity") in acts2(state) else "休む"
            place = job.get("place") if job.get("place") in places else "camp"
            with_ = job.get("with") if isinstance(job.get("with"), list) else []
            q["plan"] = {"activity": act, "place": place, "with": [w for w in with_ if isinstance(w, str) and w in alive and w != q["name"]]}
            e2["jobs"][q["name"]] = {"sow": max(0, min(1000, _int(a.get("sow")))), "pick": max(0, min(40, _int(a.get("pick")))),
                                     "plant": max(0, min(5, _int(a.get("plant")))),
                                     "eat_goat": max(0, min(5, _int(a.get("eat_goat")))) if q is p and own else 0,
                                     "harvest": max(0, min(60, _int(a.get("harvest"))))}
        p["feeling"] = str(a.get("feeling", ""))[:120]
        if era_at_least(state, "G4") and own and "keep" in a and p.get("household"):
            _house(state, p["household"])["keep"] = a.get("keep") is True or a.get("keep") in ("true", "はい")
        for v, ok in (a.get("accept").items() if isinstance(a.get("accept"), dict) else []):
            for q in fam:
                accept.setdefault(v, []).append((q["name"], ok is True or ok in ("true", "はい", "賛成")))
        if g5:
            _g5_collect(state, c5, p, a, fam)
    for t in talk:  # 話は聞き手に届く
        for n, q in alive.items():
            if n != t["from"] and (t["to"] == "みんな" or t["to"] == n):
                q["heard"].append({k: t[k] for k in ("day", "from", "text", "event")})
                q["heard"] = q["heard"][-30:]
    for msg in knowledge.settle_meeting(state):  # 季節ごとに集まる
        log(state, "掟", None, msg)
    if g5:
        _g5_meeting(state, c5, len(alive))  # 掟を決めてから (この集まりで採用された罰の掟も、この集まりで使う)
    _settle_visitors(state, accept, len(alive))
    _eat_goats(state)


def accept_answered(e2):
    return set(e2["jobs"])


def _int(v):
    try:
        return int(v)
    except (TypeError, ValueError):
        return 0


def _settle_visitors(state, accept, n_adults):
    e2 = state["era2"]
    rng = _rng(state, 11)
    for v in e2["visitors"]:
        member_names = [m["name"] for m in v["members"]]
        votes = {}  # 大人ごとの答え (群れのだれの名前で書いても同じ群れの受け入れ)
        for key, vals in accept.items():
            if key in member_names or key == v["name"]:
                for who, ok in vals:
                    votes[who] = votes.get(who, False) or ok
        yes = sum(1 for ok in votes.values() if ok)
        if yes * 2 > n_adults:
            grown = [m for m in v["members"] if m["age"] >= ADULT]
            guardian = next((m["name"] for m in grown if m["sex"] == "女"), grown[0]["name"] if grown else None)
            # 加わった大人は、この季節は村でいちばん多い仕事をする (【仮定】次の季節から自分で決める)
            plans = [q["plan"] for q in adults(state) if q["name"] in accept_answered(e2)]
            common = max(plans, key=lambda pl: sum(1 for x in plans if x["activity"] == pl["activity"] and x["place"] == pl["place"])) if plans else {"activity": "採集", "place": "camp"}
            for m in v["members"]:
                q = _new_person(state, rng, m["sex"], m["age"], child=m["age"] < ADULT, origin="よそから来た", name=m["name"],
                                mother=guardian if m["age"] < ADULT else None)
                e2["joined"].append(q["name"])
                q["household"] = member_names[0] + "の家"
                if not q.get("child"):
                    q["plan"] = {"activity": common["activity"], "place": common["place"], "with": []}
                    e2["jobs"][q["name"]] = {"sow": 0, "pick": 0, "plant": 0, "eat_goat": 0, "harvest": 0}
            names = "・".join(member_names)
            log(state, "加わる", None, f"よそから来た {names} が、村に加わった (賛成 {yes} / {n_adults})")
        else:
            log(state, "去る", None, f"よそから来た {v['name']} たちは、受け入れられず去っていった (賛成 {yes} / {n_adults})")
    e2["visitors"] = []


def _eat_goats(state):
    e2 = state["era2"]
    want = sum(j["eat_goat"] for j in e2["jobs"].values())
    n = min(want, max(0, len(e2["goats"]) - 2))  # 2 頭は残す
    if n <= 0:
        return
    males = sorted([g for g in e2["goats"] if g["sex"] == "オス"], key=lambda g: g["born"])
    others = sorted([g for g in e2["goats"] if g["sex"] != "オス"], key=lambda g: g["born"])
    for g in (males + others)[:n]:
        e2["goats"].remove(g)
        state["store"].append({"kind": "干し肉", "kcal": GOAT_MEAT * UNITS["肉"][1], "day": state["day"], "sown": True})
    log(state, "ヤギを食べる", None, f"飼っているヤギ {n} 頭をつぶして、肉を干し、蓄えに入れた (干し肉 約 {n * GOAT_MEAT * UNITS['肉'][1] // UNITS['干し肉'][1]} 切れ)")


def simulate_season(state):
    """30 日を 1 日ずつ進める。戻り値: この季節の最初の出来事の id"""
    first = state["next_event"]
    start = state["day"]
    state["era2"]["tended_run"] = 0
    for _ in range(SEASON_DAYS):
        _day(state)
        if (state["day"] + 1) % SEASON_DAYS == 0:  # 季節の終わりの日で区切る (次の回は次の季節のはじめから)
            break
        if not adults(state) and not children(state):
            break
        # 蓄えが尽きて、ひどく空腹の人が出たら、その日で区切って決め直す (30 日のあいだ誰も決め直せずに飢えないように。【仮定】)
        if (sum(f["kcal"] for f in state["store"]) < 1000 and any(p["hunger"] >= 0.6 for p in adults(state))
                and state["day"] - start >= 3):
            log(state, "蓄えが尽きる", None, "村の蓄えが尽き、ひどく空腹の人が出たので、みんなで集まって決め直すことにした")
            _famine_leave(state)
            break
    _season_end(state, (state["day"] - start) / SEASON_DAYS)
    return first


def _day(state):
    e2 = state["era2"]
    world.simulate_day(state)
    day = state["day"]
    rng = _rng(state, 3)
    sea = season(day)
    # 仕事ごとの、その日の働き
    for p in adults(state):
        t = p.get("today") or {}
        act = t.get("activity")
        job = e2["jobs"].get(p["name"], {})
        if act == "畑仕事":
            _field_work(state, p, t, job, sea, rng)
        elif act == "ヤギの世話":
            _goat_work(state, p, t, sea)
        elif act == "ヤギを捕まえる":
            _catch_goat(state, p, t, rng)
        elif act == "住まいを建てる" and era_at_least(state, "G3") and state["camp"].get("dwelling_day") is not None:
            _build_house(state, p, t)
        if act in CRAFTS:
            e2.setdefault("craft_days", {})[p["name"]] = e2.get("craft_days", {}).get(p["name"], 0) + 1
            if era_at_least(state, "G3"):
                _craft(state, p, t, act)
    # 夕方、キャンプのそばの木から取る (季節のはじめに決めた量。world.evening の「取る」を使う)
    takes = []
    for p in adults(state):
        job = e2["jobs"].get(p["name"], {})
        if job.get("pick") and not _injured_today(p):
            takes.append({"who": p["name"], "food": "木の実", "count": job["pick"], "tree": True})
        if job.get("plant") and day == e2.get("step_day"):  # この回の最初の日に、木の実を埋める
            _plant(state, p, job["plant"])
    # 秋の回の最初の日に、決めた量の草の種をキャンプのそばの畑にまく (季節の仕事とは別。2026-10-07 追加)
    if day == e2.get("step_day") and sea == "秋":
        for p in adults(state):
            n = e2["jobs"].get(p["name"], {}).get("sow", 0)
            if n:
                _sow(state, p, n)
    # 夕方、実った畑を、決めた量だけ刈る (季節の仕事とは別。2026-10-07 追加)
    sickles = e2.get("sickles", 0)
    for p in adults(state):
        n = e2["jobs"].get(p["name"], {}).get("harvest", 0)
        if n and not _injured_today(p):
            if sickles > 0 and any(f["state"] == "実った" for f in e2["fields"]):  # 鎌を使うと 2 倍刈れる (村の鎌の数の人まで)
                sickles -= 1
                n *= 2
            _harvest(state, p, n)
    kids_ate = _feed(state, rng)
    world.evening(state, [], [], takes)
    if state["stats"] and kids_ate:  # 子が食べた量も、その日の食べた量に数える
        s = state["stats"][-1]
        s["eaten"] += kids_ate["total"]
        s["eaten_sown"] = s.get("eaten_sown", 0) + kids_ate["sown"]
        for k, v in kids_ate["by"].items():
            s["eaten_by_kind"][k] = s["eaten_by_kind"].get(k, 0) + v
    _field_season(state, rng)


def _injured_today(p):
    """けがで休んだ日 (予定は休むではないのに、今日は休んだ)"""
    return (p.get("today") or {}).get("activity") == "休む" and (p.get("plan") or {}).get("activity") != "休む"


def _plant(state, p, want):
    """手元の木の実、なければ村の蓄えの木の実を、キャンプのそばに埋める (1 つかみが 1 つの種。20 日で木になる)"""
    got = []
    by = _move_food(p["food"], got, "木の実", want * FRUIT_KCAL)
    have = sum(by.values())
    if have < want * FRUIT_KCAL:
        _move_food(state["store"], got, "木の実", want * FRUIT_KCAL - have)
    n = int(sum(f["kcal"] for f in got) // FRUIT_KCAL)
    rng = _rng(state, 29)
    cx, cy = state["camp"]["x"], state["camp"]["y"]
    for _ in range(n):
        state["planted"].append({"x": min(W - 1, max(0, cx + rng.randint(-3, 3))), "y": min(H - 1, max(0, cy + rng.randint(-3, 3))),
                                 "day": state["day"], "who": p["name"]})
    if n:
        log(state, "種まき", p["name"], f"{p['name']} がキャンプのそばに 木の実 {n} つかみ を種として埋めた")


def _keep(p):
    need = (p.get("today") or {}).get("spent") or BASE_KCAL
    # その日に使った分を手元に残す。空腹のときは少し多めに (体の蓄えを取り戻す。【仮定】)
    return min(world.EAT_MAX, need + (800 if p["hunger"] > 0 else 0))


def _feed(state, rng):
    """大人: 手元に食べる分を残して残りを蓄えへ、足りなければ蓄えから取る。子: 蓄えから食べる (足りないと空腹になる)"""
    for p in adults(state):
        keep = _keep(p)
        have = sum(f["kcal"] for f in p["food"])
        if have > keep:
            _flow(state, p, 0, sum(_move_food(p["food"], state["store"], None, have - keep).values()))
        elif have < keep:
            got = sum(_move_food(state["store"], p["food"], None, keep - have).values())
            _flow(state, p, 1, got)
            if have + got < keep and era_at_least(state, "G4"):  # 村の蓄えが足りないときは、家の倉から
                got += sum(_move_food(_house(state, p.get("household"))["store"], p["food"], None, keep - have - got).values())
                if have + got < keep and p["hunger"] >= 0.6 and era_at_least(state, "G5"):  # G5: それでも足りず、ひどく空腹 (前からの 0.6) なら、よその家の倉から
                    _steal(state, p, keep - have - got)
    ate = {"total": 0, "sown": 0, "by": {}}
    for c in children(state):
        need = next(k for a, k in CHILD_EAT if c["age"] < a)
        got_items = []
        by = _move_food(state["store"], got_items, None, need)
        if sum(by.values()) < need and era_at_least(state, "G4"):
            for k, v in _move_food(_house(state, c.get("household"))["store"], got_items, None, need - sum(by.values())).items():
                by[k] = by.get(k, 0) + v
        got = sum(by.values())
        c["hunger"] = round(min(1.0, max(0.0, c["hunger"] + (0.15 if got < need * 0.5 else -0.2))), 2)
        ate["total"] += got
        ate["sown"] += sum(f["kcal"] for f in got_items if f.get("sown"))
        for k, v in by.items():
            ate["by"][k] = ate["by"].get(k, 0) + v
    return ate


def _field_work(state, p, t, job, sea, rng):
    e2 = state["era2"]
    day = state["day"]
    h = t.get("work_h", 6)
    mine = [f for f in e2["fields"] if f["state"] == "育つ"]
    ripe = [f for f in e2["fields"] if f["state"] == "実った"]
    if ripe:  # 刈る: 畑仕事の人は 1 日に 150 つかみまで【仮定】
        _harvest(state, p, int(150 * h / 6))
        return
    for f in mine:  # 草取り・水やり
        f["work"] += h / max(1, len(mine))


# ---------------- G3 余りと分業: 土器と石の鎌 (2026-10-08 追加。G3 に入ってから働く) ----------------
# 【文献】西アジアの土器は前 7000 年ごろから。民族誌の目安で、鉢 1 個の成形に数時間、乾かすのに数日〜1 週間、焼くのに 1 日 (society2_research.md)
# 【文献】ナトゥーフ期・先土器新石器時代の、石の刃を骨や木の柄にはめた鎌
# 【仮定】土器 1 個に草の種 500 つかみ (約 11 kg)。土器に入らない草の種は、1 季節に 5% が虫やネズミに食べられる。土器は 1 季節に 3%、鎌は 5% が割れる
POT_HOLD, PEST_LOSS, POT_BREAK, SICKLE_BREAK = 500, 0.05, 0.03, 0.05


def _craft(state, p, t, act):
    e2 = state["era2"]
    h = t.get("work_h", 6)
    if act == "土器づくり":
        sk = p["skills"].setdefault("土器", 0.1)
        p["pot_work"] = p.get("pot_work", 0.0) + h / 6 * (0.4 + 0.8 * sk)  # 腕が上がると、1 日に作れる数が増える (専門化の得)
        n = int(p["pot_work"])
        p["pot_work"] -= n
        p["skills"]["土器"] = round(min(1, sk + 0.02), 3)
        if n:
            e2["pots"] = e2.get("pots", 0) + n
            log(state, "土器", p["name"], f"{p['name']} がキャンプで土器を {n} 個焼き上げた (村の土器 {e2['pots']} 個)", count=n)
        else:
            log(state, "土器", p["name"], f"{p['name']} がキャンプで土器の形を作り、乾かした", count=0)
    elif act == "道具づくり":
        sk = p["skills"].get("道具", 0.1)
        p["sickle_work"] = p.get("sickle_work", 0.0) + h / 6 * (0.3 + 0.7 * sk) / 2  # 石の刃を打ち欠き、木の柄にはめる (1 本に 2 日ほど)
        n = int(p["sickle_work"])
        p["sickle_work"] -= n
        p["skills"]["道具"] = round(min(1, sk + 0.02), 3)
        if n:
            e2["sickles"] = e2.get("sickles", 0) + n
            log(state, "道具", p["name"], f"{p['name']} が石の刃を木の柄にはめた鎌を {n} 本作った (村の鎌 {e2['sickles']} 本)", count=n)
        else:
            log(state, "道具", p["name"], f"{p['name']} がキャンプで石の刃を打ち欠き、鎌の柄を削った", count=0)


def _storage_season(state, frac):
    """季節の終わり: 土器に入らない草の種の一部が、虫やネズミに食べられる。土器と鎌は少し割れる"""
    e2 = state["era2"]
    rng = _rng(state, 31)
    stores = [state["store"]] + [h["store"] for h in e2.get("house", {}).values()]
    grain = sum(f["kcal"] for st in stores for f in st if f["kind"] == "草の種") / UNITS["草の種"][1]
    safe = min(grain, e2.get("pots", 0) * POT_HOLD)
    lost = int((grain - safe) * PEST_LOSS * frac)
    if lost > 0:
        for st in stores:  # どの倉も同じ割合で (土器は村の土器を、すべての草の種に同じ割合で使う)
            g = sum(f["kcal"] for f in st if f["kind"] == "草の種") / UNITS["草の種"][1]
            if g:
                _move_food(st, [], "草の種", g / grain * lost * UNITS["草の種"][1])
        log(state, "虫", None, f"蓄えの草の種 約 {lost} つかみ が、虫やネズミに食べられた" + (f" (土器に入れていた 約 {int(safe)} つかみ は無事)" if safe else ""), amount=lost)
    for key, rate, what in (("pots", POT_BREAK, "土器"), ("sickles", SICKLE_BREAK, "鎌")):
        broke = sum(1 for _ in range(e2.get(key, 0)) if rng.random() < rate * frac)
        if broke:
            e2[key] -= broke
            log(state, "道具", None, f"村の{what}が {broke} {'個' if key == 'pots' else '本'} 割れた (残り {e2[key]})")


# ---------------- 家族の住まい (2026-10-08 追加。G3 から働く。本人の希望「人数が増えて家族になっているので、シミュレーションに反映したい」) ----------------
# 【文献】Flannery 2002: 先土器新石器 B (PPNB) に、丸い家と共同の倉から、四角い家と家ごとの倉へ変わった。Kohler ほか 2017: 家の大きさで豊かさの差 (ジニ係数) を測る
# 【仮定】家族の住まい 1 軒に、のべ 400 時間の働き (大人 2 人で 3 週間ほど。広さ 約 20 m²)。そのあと 200 時間ごとに 10 m² 広くなる (80 m² まで)。
#   (2026-10-08 写しの試しで、120 時間では 4〜6 日で建ち、1 季節で 80 m² になったので、400 時間にした)
#   村の住まい (キャンプのまん中) で眠れるのは 12 人まで (world.DWELL_CAP)。家族の住まいのある家族は、そこで眠る
HOUSE_HOURS, HOUSE_BASE, HOUSE_STEP, HOUSE_MAX = 400, 20, 10, 80


def _homes_built(state):
    return {h for h, v in state["era2"].get("homes", {}).items() if v.get("built") is not None}


def _house_site(state):
    """家族の住まいを建てる場所: キャンプから 5〜9 マスの輪の上で、川でなく、南西の畑と村の住まいから離れ、ほかの家と重ならない所"""
    cx, cy = state["camp"]["x"], state["camp"]["y"]
    used = [(v["x"], v["y"]) for v in state["era2"].get("homes", {}).values()]
    for r in (5, 7, 9):
        for k in range(12):
            a = math.radians(k * 30 + (15 if r == 7 else 0))
            x, y = round(cx + r * math.cos(a), 1), round(cy + r * math.sin(a), 1)
            ix, iy = int(x), int(y)
            if not (0 <= ix < W and 0 <= iy < H) or state["terrain"][iy][ix] == "r":
                continue
            if (x < cx - 1 and y > cy + 1) or math.hypot(x - (cx - 2.7), y - (cy - 1.7)) < 3:  # 南西は畑、北西は村の住まい
                continue
            if any(math.hypot(x - ux, y - uy) < 2.2 for ux, uy in used):
                continue
            return x, y
    return cx + 3.0, cy - 4.0


def _build_house(state, p, t):
    """家族の大人が、家族の住まいを建てる・広げる (G3 から。村の住まいができたあと)"""
    h = p.get("household")
    if not h:
        return
    homes = state["era2"].setdefault("homes", {})
    v = homes.get(h)
    if not v:
        x, y = _house_site(state)
        v = homes[h] = {"x": x, "y": y, "start": state["day"], "built": None, "size": 0, "work": 0.0, "sizes": []}
    before = v["work"]
    v["work"] = round(before + t.get("work_h", 6) * (0.6 + 0.4 * p["skills"].get("道具", 0.1)), 2)
    p["skills"]["道具"] = round(min(1, p["skills"].get("道具", 0.1) + 0.02), 3)
    if v["built"] is None:
        if v["work"] >= HOUSE_HOURS:
            v["built"], v["size"] = state["day"], HOUSE_BASE
            v["sizes"].append([state["day"], HOUSE_BASE])
            t.setdefault("events", []).append(log(state, "住まい", p["name"], f"{p['name']} たちの手で、{h}の住まいができた (四角い家。広さ 約 {HOUSE_BASE} m²)",
                                                  household=h, size=HOUSE_BASE))
        else:
            t.setdefault("events", []).append(log(state, "住まい", p["name"], f"{p['name']} が、{h}の住まいを建てた (まだ建てかけ。でき具合 約 "
                                                  f"{max(1, round(v['work'] / HOUSE_HOURS * 10))} 割)", household=h))
    else:
        size = min(HOUSE_MAX, HOUSE_BASE + HOUSE_STEP * int((v["work"] - HOUSE_HOURS) // (HOUSE_HOURS / 2)))
        if size > v["size"]:
            v["size"] = size
            v["sizes"].append([state["day"], size])
            t.setdefault("events", []).append(log(state, "住まい", p["name"], f"{p['name']} たちが、{h}の住まいを広げた (広さ 約 {size} m²)", household=h, size=size))
        else:
            t.setdefault("events", []).append(log(state, "住まい", p["name"], f"{p['name']} が、{h}の住まいを"
                                                  + ("手入れした" if v["size"] >= HOUSE_MAX else "広げている"), household=h))


def _houses_text(state):
    """お題の「村のようす」: 家族の住まい (G3 から)"""
    homes = state["era2"].get("homes", {})
    rows = []
    for h in sorted({q.get("household") for q in state["people"] if q["alive"] and q.get("household")}):
        v = homes.get(h)
        rows.append(f"{h} (" + ("まだない" if not v else f"できている、広さ 約 {v['size']} m²" if v["built"] is not None
                                else f"建てかけ、でき具合 約 {max(1, round(v['work'] / HOUSE_HOURS * 10))} 割") + ")")
    built = _homes_built(state)
    inside = sum(1 for q in state["people"] if q["alive"] and q.get("household") not in built)
    return (f"家族の住まい: {'、'.join(rows)}\n"
            f"村の住まい (キャンプのまん中) で眠るのは {inside} 人 ({world.DWELL_CAP} 人まで)\n")


# ---------------- G4 持ち物と差: 家の倉・持ち主・受けつぎ (2026-10-08 追加。G4 に入ってから働く) ----------------
# 【文献】畑・家畜・家は手間をかけた人の物になりやすく、親から子に受けつがれるので差が世代をこえて大きくなる (Borgerhoff Mulder ほか 2009)
# 【文献】家の大きさのジニ係数: 狩猟採集 約 0.17、園耕 約 0.27、農耕 約 0.35 (Kohler ほか 2017)
# 【文献】Halstead の「ふつうの余り」: 不作に備えて多めに作り、ためておく
# 【仮定】ヤギ 1 頭の値うちを 3 万 kcal (肉 20 kg ほど) として、家の倉と合わせて家の持ち物とする
GOAT_WORTH = 30000


def _house(state, h):
    hs = state["era2"].setdefault("house", {})
    return hs.setdefault(h or "-", {"store": [], "keep": False})


def _store_of(state, owner):
    """刈った草の種の入れ先: G4 からは、畑の持ち主の家が倉を持つ (keep) なら、その家の倉"""
    if era_at_least(state, "G4") and owner:
        h = _house(state, owner)
        if h["keep"] and owner in _homes_built(state):  # 家の倉は家族の住まいの中に置く (2026-10-08。住まいのない家は村の蓄えへ)
            return h["store"]
    return state["store"]


def wealth(state):
    """家ごとの持ち物 (kcal): 家の倉 + ヤギ。生きている人のいる家だけ"""
    homes = sorted({p.get("household") for p in state["people"] if p["alive"] and p.get("household")})
    hs = state["era2"].get("house", {})
    goats = {}
    for g in state["era2"]["goats"]:
        goats[g.get("owner")] = goats.get(g.get("owner"), 0) + 1
    return {h: round(sum(f["kcal"] for f in hs.get(h, {}).get("store", [])) + goats.get(h, 0) * GOAT_WORTH) for h in homes}


def gini(values):
    v = sorted(values)
    n, s = len(v), sum(v)
    if n < 2 or s <= 0:
        return 0.0
    return round(sum((2 * (i + 1) - n - 1) * x for i, x in enumerate(v)) / (n * s), 3)


def _inherit(state, dead):
    """家の代表 (いちばん年上の大人) が亡くなったら、家の倉・畑・ヤギを、家で次に年上の大人が受けつぐ"""
    e2 = state["era2"]
    h = dead.get("household")
    if not h or not era_at_least(state, "G4"):
        return
    was_head = all(q["age"] <= dead["age"] for q in adults(state) + [dead] if q.get("household") == h)
    goats = sum(1 for g in e2["goats"] if g.get("owner") == h)
    fields = sum(1 for f in e2["fields"] if f.get("owner") == h and f["state"] in ("育つ", "実った"))
    store = _house(state, h)["store"]
    if not was_head or not (goats or fields or store):
        return
    what = "・".join(x for x in (("倉 (" + food_words(world.holdings({"food": store})) + ")") if store else "",
                                 f"ヤギ {goats} 頭" if goats else "", f"畑 {fields} 枚" if fields else "") if x)
    heir = sorted([q for q in adults(state) if q.get("household") == h and q is not dead], key=lambda q: -q["age"])
    kids = sorted([c for c in children(state) if c.get("household") == h], key=lambda c: -c["age"])
    if heir or kids:
        who = (heir or kids)[0]
        e2["inherits"] = e2.get("inherits", 0) + 1
        log(state, "受けつぎ", who["name"], f"{dead['name']} が亡くなり、{h}の{what}は、{who['name']}{' (子)' if not heir else ''} が受けついだ", dead=dead["name"])
    else:  # 家にだれもいなくなった: 村のものになる
        state["store"].extend(store)
        _house(state, h)["store"] = []
        for g in e2["goats"]:
            if g.get("owner") == h:
                g["owner"] = None
        for f in e2["fields"]:
            if f.get("owner") == h:
                f["owner"] = None
        log(state, "受けつぎ", None, f"{dead['name']} が亡くなり、{h}にはだれもいなくなったので、{what}は村のものになった")


# ---------------- G5 リーダーと決まり: もめごと・集まり・長老・祭り・まとめ役・罰・村が分かれる (2026-10-08 追加。G5 に入ってから働く) ----------------
# 2 段階 (計画 2.1。2026-10-08 本人と決めた): 第 1 段 集まり・長老・祭りでもめごとを収める → 第 2 段 決まったまとめ役・罰・裁き。村が分かれるのも起きてよい結果
# 【文献】Johnson 1982 (規模のストレス): 話し合いで決める単位が 6 ほどをこえると、決めるのが急に難しくなる。答えは (1) 家の長どうしの話し合いと儀礼で
#   まとまる「順番の階層」、(2) 決まった役をおく「同時の階層」、(3) 集団が分かれる、の 3 つ。Johnson は (1) を (2) に代わる平等な仕組みとして示した。
#   (1) → (2) の順はこの計画の解釈 (docs/research/society2_periodization.md 5.)。だから第 2 段 (まとめ役を選ぶ・掟に罰をつける) は、第 1 段でまとまっても
#   (まとまり)、集まりでもめごとが収まらなくても (ゆきづまり) 選べるようになるだけで、選ぶかどうかは人が決める。まとめ役は「なし」でやめさせられる
# 【仮定】もめごとは家どうしなので、話し合いの単位は家 (大人のいる家)。家族の代表 (家でいちばん年上の大人) の集まりは、家の長の「順番の階層」にあたる
# 【文献】ヒラゾン・タクティトの祭り (約 1.2 万年前)・ギョベクリ・テペ (前 9,600〜8,200 年ごろ): 目に見えるまとめ役なしに、祭りと儀礼で人が集まった
#   (docs/research/society2_periodization.md 3 の 5)。Bandy 2004: 決まりのない村は約 300 人で分かれる (人数を 1/10 にして 30 人)
# 【文献】Flannery 2002: 共同の倉から家ごとの倉へ。Stein 1994: ウバイド期のまとめ役は儀礼のために主食を集めた。Fried: ランク社会のまとめ役は呼びかけるが、従わせる力は弱い
# 【文献の目安】話し合いのコストは単位の数の 2 乗に比例 (docs/society2_research.md 9) → もめごとになる見込みを、家どうしの組の数 H(H−1)/2 に比べて決める
# 【仮定】数: もめごとになる見込み 0.3 × H(H−1)/30 (6 家族で 0.3、8 家族で 0.56、0.9 まで。祭りの季節は半分)。新しいもめごとは 1 季節に 3 つまで。
#   集まりで話し合えるのは古いものから 2 つまで。4 季節収まらないと、だれも言わなくなる。祭り = 村の全員の 3 日分。荒らされた畑は実りの 2 割を失う。
#   取りすぎ = 大人 1 人あたり 10 日分 (家の倉に食べ物がある家は 5 日分) をこえる差。刈り手の取り分は 1 割。払うのは 1000 つかみまで。
#   収まらないまま 2 季節で、1 季節に 0.5 × (人数 / 30) の見込みで言い出した家が出ていく (1 年に 1 つの家まで。残る村に家が 3 つ・大人が 6 人より少なくなるときは出ていかない)
G5_P, G5_MAX_P, MAX_NEW, TALK_MAX, DROP_AGE = 0.3, 0.9, 3, 2, 4
FEAST_DAYS, TRAMPLE, FREE_DAYS, REAP_SHARE, MAX_PAY = 3, 0.2, 10, 0.1, 1000
LEAVE_P, BANDY, MIN_HOMES, MIN_ADULTS = 0.5, 30, 3, 6
GRAIN = UNITS["草の種"][1]
DAY_FOOD = BASE_KCAL + 500  # 大人 1 人の 1 日分 (_need と同じ)
OPEN = "収まっていない"
KINDS = {"ヤギ": "家のヤギが、よその家の畑を荒らす", "倉": "よその家の倉から取って食べる",
         "蓄え": "村の蓄えに入れた量にくらべて、ほかの家より多く村の蓄えから取る", "刈る": "よその家の畑で刈った草の種が、みな畑の持ち主の家の倉に入る"}
G5_EVENTS = ("もめごと", "収める", "裁き", "罰", "祭り", "まとめ役", "分かれる", "段階", "共同の仕事", "倉から取る")  # お題と step.py で見せる


def _g5(state):
    return state["era2"].setdefault("g5", {
        "start": state["day"], "stage": 1, "open": None, "stage1": None, "disputes": [], "next": 0, "leader": None, "leader_day": None,
        "leaders": [], "votes": None, "call": None, "settled": 0, "judged": 0, "penalties": 0, "feasts": 0, "feast_day": None, "joint": 0,
        "fissions": [], "last_fission": None, "flow": {}, "reap": {}, "incidents": [], "last_flow": {}, "meet_first": None})


def _leader(state):
    """まとめ役の名前 (いなければ None。G5 の前は状態を作らずに None)"""
    return (state["era2"].get("g5") or {}).get("leader")


def _homes(state):
    """大人のいる家 (話し合いの単位)"""
    return sorted({p["household"] for p in adults(state) if p.get("household")})


def stress_p(state):
    """季節の終わりに、もめごとのもとが、もめごとになる見込み (家が多いほど高い。祭りをした季節は半分)"""
    h, g = len(_homes(state)), state["era2"].get("g5") or {}
    p = min(G5_MAX_P, G5_P * h * (h - 1) / 30)
    return p / 2 if g.get("feast_day") is not None and g.get("feast_day") == state["era2"].get("step_day") else p


def _flow(state, p, i, kcal):
    """G5: 家ごとに、村の蓄えに入れた量 (0)・取った量 (1)・家の倉を持つ家が自分の畑にまいた村の草の種 (2) を数える (大人の分だけ。子は村の蓄えで育つ決まり)"""
    if kcal > 0 and era_at_least(state, "G5"):
        _g5(state)["flow"].setdefault(p.get("household") or "-", [0, 0, 0])[i] += kcal


def _incident(state, kind, frm, against, kcal, what, eid=None):
    """もめごとのもと (世界で起きたこと)。季節の終わりに、もめごとになるか決める。frm = 損をした家 (言い出す家)、against = 相手の家"""
    if not frm or not against or frm == against or kcal <= 0:
        return
    inc = _g5(state)["incidents"]
    x = next((x for x in inc if (x["kind"], x["from"], x["against"]) == (kind, frm, against)), None)
    if not x:
        x = {"kind": kind, "from": frm, "against": against, "kcal": 0, "what": what, "events": []}
        inc.append(x)
    x["kcal"] += kcal
    x["events"] += [eid] if eid is not None else []


def _steal(state, p, want):
    """G5: ひどく空腹で、村の蓄えにも自分の家の倉にも食べ物がない大人は、よその家の倉 (多い家から) から取って食べる (出来事は家の組ごとに 1 季節 1 回)"""
    hs, mine, homes = state["era2"].get("house", {}), p.get("household"), _homes(state)
    if not mine:  # 家のない人 (今はいない) は取らない。取ると、もめごとのもとにならず、毎日記録が出るため (2026-10-08 確認役の指摘)
        return
    for h in sorted([h for h in hs if h in homes and h != mine and hs[h]["store"]], key=lambda h: -sum(f["kcal"] for f in hs[h]["store"])):
        if want <= 0:
            break
        by = _move_food(hs[h]["store"], p["food"], None, want)
        want -= sum(by.values())
        new = not any((x["kind"], x["from"], x["against"]) == ("倉", h, mine) for x in _g5(state)["incidents"])
        eid = log(state, "倉から取る", p["name"], f"ひどく空腹の {p['name']} が、{h}の倉から {food_words(by)} を取って食べた", owner=h, home=mine) if new else None
        _incident(state, "倉", h, mine, sum(by.values()), f"{mine}の人が、{h}の倉から食べ物を取って食べた", eid)


def _g5_reap(state, p, owner, n, to_village):
    """刈った草の種 (G5): 村の蓄えに入れば、刈った人の家が入れた量。よその家の倉に入れば「刈る」のもと
    (よその家の畑を刈って、刈った人の家が損をすることはない。持ち主の倉か村の蓄えに入るため。損をするのは、取り分のない刈り手の家)"""
    if to_village:
        _flow(state, p, 0, n * GRAIN)
    elif owner and p.get("household") and owner != p["household"]:
        r = _g5(state)["reap"].setdefault(p["household"], {})
        r[owner] = r.get(owner, 0) + n


def _dispute(state, inc):
    g = _g5(state)
    d = {"id": f"M{g['next']}", "kind": inc["kind"], "from": inc["from"], "against": inc["against"], "day": state["day"],
         "harm": max(1, round(inc["kcal"] / GRAIN)), "what": inc["what"], "because": inc["events"], "status": OPEN}
    g["next"] += 1
    g["disputes"].append(d)
    # 注意: log() の引数名 kind・who・text を、データの名前に使わない (TypeError になる)
    d["event"] = log(state, "もめごと", None, f"もめごと [{d['id']}] ({d['kind']}): {d['from']}が、{d['against']}のことで不満を言い出した。"
                     f"{d['what']} (草の種にして 約 {d['harm']} つかみ 分)", dispute=d["id"], about=d["kind"])


def _g5_season_end(state, frac):
    """季節の終わり (G5。家族を決めた後): もめごとのもと → もめごと → 言われなくなる → 第 1 段・第 2 段 → 村が分かれる"""
    e2, g = state["era2"], _g5(state)
    rng = _rng(state, 37)  # G5 で足した乱数 (37 を 31 で割った余り 6 は、前からの塩 3・7・11・23・29・31 の余り 3・7・11・23・29・0 と重ならない)
    day, homes = state["day"], _homes(state)
    _check_leader(state)
    # (1) ヤギ: 世話をする人が少ない季節 (ヤギが逃げるのと同じ「世話 5 日より少ない」) は、家のヤギが、よその家の畑を荒らすことがある (【仮定】1 頭 0.1、0.6 まで)
    if e2.get("tended_run", 0) < 5 * frac:
        for h in sorted({x["owner"] for x in e2["goats"] if x.get("owner") in homes}):
            n = sum(1 for x in e2["goats"] if x.get("owner") == h)
            fl = [f for f in e2["fields"] if f["state"] in ("育つ", "実った") and f.get("owner") in homes and f["owner"] != h]
            if not fl or rng.random() >= min(0.6, 0.1 * n) * frac:
                continue
            f = rng.choice(fl)
            ripe = f["state"] == "実った"
            lost = int(((f["yield"] - f["harvested"]) if ripe else f["seed"] * 8) * TRAMPLE)
            if lost <= 0:
                continue
            if ripe:
                f["yield"] -= lost
            else:  # 育っている畑は、実るときに減る (減る量は平年の 8 倍で見積もる)
                f["lost"] = round(1 - (1 - f.get("lost", 0)) * (1 - TRAMPLE), 3)
            what = f"{h}のヤギが、{f['owner']}の畑を荒らした"
            eid = log(state, "ヤギ", None, f"世話をする人が少なく、{what} (草の種 約 {lost} つかみ 分)", owner=h, field=f["id"])
            _incident(state, "ヤギ", f["owner"], h, lost * GRAIN, what, eid)
    # (4) 刈る: よその家の畑で刈った草の種が、みな畑の持ち主の家の倉に入った (刈った人の家の取り分を 1 割とみる)
    for hh, row in sorted(g["reap"].items()):
        for o, n in sorted(row.items()):
            _incident(state, "刈る", hh, o, n * REAP_SHARE * GRAIN, f"{hh}の人が{o}の畑で刈った草の種 {n} つかみ は、みな{o}の倉に入った")
    # (3) 蓄え: 村の蓄えに入れた量にくらべて、ほかの家より多く取った家 (1 季節に 1 つの家まで。言い出すのは、いちばん多く入れた家)
    flow = {h: v for h, v in g["flow"].items() if h in homes}
    tin, tout = sum(v[0] for v in flow.values()), sum(v[1] + v[2] for v in flow.values())
    if len(flow) >= 2 and tin > 0 and tin >= 0.25 * tout:  # 【仮定】ほとんど蓄えで暮らした季節 (冬・春) は、だれの出し入れも目立たない
        r = max(1.0, tout / tin)  # 村みんなで蓄えを減らした季節は、入れた量の r 倍まで取っても多くない
        hs = e2.get("house", {})
        full = {h for h in flow if hs.get(h, {}).get("keep") and hs[h]["store"]}  # 【文献】Flannery 2002: 家の倉を持ちながら村の蓄えから取る家は目立つ
        over = {h: v[1] + v[2] - v[0] * r for h, v in flow.items()}
        need = {h: FREE_DAYS * DAY_FOOD * frac * sum(1 for q in adults(state) if q.get("household") == h) * (0.5 if h in full else 1) for h in flow}
        cand = [h for h in flow if need[h] > 0 and over[h] >= need[h]]
        frm = min(sorted(flow), key=over.get)
        if cand and over[frm] < 0:
            h = max(sorted(cand), key=lambda x: over[x] / need[x])
            i, o, s = flow[h]
            acts = "・".join(dict.fromkeys(q["plan"]["activity"] for q in adults(state) if q.get("household") == h))
            _incident(state, "蓄え", frm, h, over[h] / len(homes),  # 【仮定】言い出した家の損 = 取りすぎを村の家の数で割った分
                      f"この季節、{h}の大人は、村の蓄えから草の種にして 約 {round((o + s) / GRAIN)} つかみ 分を取り"
                      + (f" (家の畑にまいた村の草の種 {round(s / GRAIN)} つかみ をふくむ)" if s else "")
                      + f"、入れたのは 約 {round(i / GRAIN)} つかみ 分だった (おもな仕事: {acts}"
                      + (f"。家の倉に {food_words(holdings({'food': hs[h]['store']}))} がある" if h in full else "")
                      + f")。{frm}は 約 {round(flow[frm][0] / GRAIN)} つかみ 分を入れた")
    g["last_flow"] = {h: [round(v[0] / GRAIN), round((v[1] + v[2]) / GRAIN)] for h, v in sorted(flow.items())}
    g["flow"], g["reap"] = {}, {}
    # もめごとのもと → もめごと (家が多いほどなりやすい。罰のある掟にあたることは必ずなる。同じ家どうしの同じ中身で収まっていないものには重ねる)
    pen = {l["penalty"]["for"] for l in state["laws"] if l["status"] == "採用" and l.get("penalty")}
    p, new = stress_p(state), 0
    for inc in g["incidents"]:
        if inc["from"] not in homes or inc["against"] not in homes:
            continue
        old = next((d for d in g["disputes"] if d["status"] == OPEN and (d["kind"], d["from"], d["against"]) == (inc["kind"], inc["from"], inc["against"])), None)
        if old:
            old["harm"] += max(1, round(inc["kcal"] / GRAIN))
            old["because"] += inc["events"]
            log(state, "もめごと", None, f"もめごと [{old['id']}] に、また同じことが重なった: {inc['what']}", dispute=old["id"])
        elif new < MAX_NEW and (inc["kind"] in pen or rng.random() < p):
            _dispute(state, inc)
            new += 1
    g["incidents"] = []
    # 収まらないもめごと: どちらかの家に大人がいなくなった・DROP_AGE 季節たった → なくなった
    for d in [d for d in g["disputes"] if d["status"] == OPEN]:
        if d["from"] not in homes or d["against"] not in homes:
            d.update(status="なくなった", end=day)
        elif (day - d["day"]) // SEASON_DAYS >= DROP_AGE:
            d.update(status="なくなった", end=day)
            log(state, "もめごと", None, f"もめごと [{d['id']}] は、収まらないまま {DROP_AGE} 季節たち、だれも言わなくなった ({d['what']})", dispute=d["id"])
    stale = [d for d in g["disputes"] if d["status"] == OPEN and (day - d["day"]) // SEASON_DAYS >= 2]
    # 第 1 段の目安 (止まらずに記録する): 家族が 6 つ以上の村が、まとめ役なしに、G5 に入って 1 年以上、集まり・長老・祭りでもめごとを 2 回以上収めた
    H = len(homes)
    if not g["stage1"] and not g["leader"] and H >= 6 and g["settled"] >= 2 and day - g["start"] >= YEAR:
        g["stage1"] = day
        log(state, "段階", None, f"G5 の第 1 段: 家族が {H} つの村が、まとめ役なしに、集まり・長老の言葉・祭りで、もめごとを {g['settled']} 回収めてきた (祭り {g['feasts']} 回)")
        _open2(state, "まとまり", "村は、まとめ役なしに、もめごとを収めてきた")
    if stale:
        _open2(state, "ゆきづまり", f"もめごと [{stale[0]['id']}] が、集まりで収まらないまま 2 季節たった")
    # 村が分かれる: 収まらないまま 2 季節たったもめごとの、言い出した家が出ていくことがある (祭りをした季節は出ていかない。1 年に 1 つの家まで)
    pop = sum(1 for q in state["people"] if q["alive"])
    if g["feast_day"] != e2.get("step_day") and (g["last_fission"] is None or day - g["last_fission"] >= YEAR):
        for d in stale:
            if _can_leave(state, d["from"]) and rng.random() < LEAVE_P * min(1.0, pop / BANDY) * frac:
                _split(state, d)
                break


def _open2(state, how, why):
    """第 2 段: 季節の集まりで、まとめ役を選べるようになり、掟に罰をつけられるようになる (一度だけ。止まらずに記録する)"""
    g = _g5(state)
    if g["stage"] < 2:
        g["stage"], g["open"] = 2, {"day": state["day"], "how": how}
        log(state, "段階", None, f"G5 の第 2 段: {why}。これからは、季節の集まりで村のまとめ役を選べ、掟に罰をつけられる", how=how)


def _can_leave(state, h):
    """出ていけるのは大人のいる家で、残る村に家が 3 つ以上・大人が 6 人以上いるとき (【仮定】残る村が続くように)"""
    ads = adults(state)
    mine = sum(1 for q in ads if q.get("household") == h)
    return mine >= 1 and len(_homes(state)) - 1 >= MIN_HOMES and len(ads) - mine >= MIN_ADULTS


def _split(state, d):
    """村が分かれる: 言い出した家が、家の人みんな (子も、この季節に生まれた子も) で出ていく。家のヤギと家の倉の食べ物は持って行き、家の畑は村のものになる
    【文献】Johnson 1982 (分かれるのも規模のストレスへの答え)、PPNC で大きな村がばらけた (periodization 3 の 8)"""
    e2, g, h, day = state["era2"], _g5(state), d["from"], state["day"]
    ppl = sorted([q for q in state["people"] if q["alive"] and q.get("household") == h], key=lambda q: -q["age"])
    names = {q["name"] for q in ppl}
    ppl += [c for c in children(state) if c.get("mother") in names and c["name"] not in names]
    for q in ppl:
        q["alive"], q["left"] = False, day
    goats = [x for x in e2["goats"] if x.get("owner") == h]
    e2["goats"] = [x for x in e2["goats"] if x.get("owner") != h]
    st = _house(state, h)
    kcal, food = sum(f["kcal"] for f in st["store"]), food_words(holdings({"food": st["store"]}))
    st["store"] = []
    fields = [f for f in e2["fields"] if f.get("owner") == h and f["state"] in ("育つ", "実った")]
    for f in fields:
        f["owner"] = None
    for x in g["disputes"]:
        if x["status"] == OPEN and h in (x["from"], x["against"]):
            x.update(status="去った", end=day)
    g["fissions"].append({"day": day, "household": h, "people": [q["name"] for q in ppl], "goats": len(goats), "store": round(kcal),
                          "fields": len(fields), "dispute": d["id"]})
    g["last_fission"] = day
    took = "・".join(x for x in (f"ヤギ {len(goats)} 頭" if goats else "", f"家の倉の {food}" if kcal else "") if x)
    log(state, "分かれる", ppl[0]["name"], f"もめごと [{d['id']}] が収まらないまま 2 季節たち、{h}の "
        + "・".join(q["name"] + (" (子)" if q.get("child") else "") for q in ppl) + " が村を出ていった"
        + (f"。{took} を持って行った" if took else "") + (f"。{h}の畑 {len(fields)} 枚は村のものになった" if fields else ""),
        household=h, dispute=d["id"])
    _check_leader(state)


def _check_leader(state):
    """まとめ役が亡くなった・村を出たら、まとめ役はいなくなる"""
    g = _g5(state)
    q = next((q for q in state["people"] if q["name"] == g["leader"]), None) if g["leader"] else None
    if q and not q["alive"]:
        log(state, "まとめ役", q["name"], f"まとめ役の {q['name']} が{'村を出た' if q.get('left') else '亡くなった'}ので、村にまとめ役がいなくなった")
        g["leader"], g["leader_day"] = None, None


# ---- 季節の集まり (G5): 答えを読む ----

def _mid(v):
    """もめごとの番号 (「M3」「m3」「3」「[M3]」→ "M3"。番号がなければ "")"""
    m = re.search(r"\d+", str(v or ""))
    return f"M{int(m.group())}" if m else ""


def _num(v):
    """数 (「50 つかみ」のような文でも、はじめの数を読む。全角の数字も読む)"""
    m = re.search(r"\d+", str(v)) if v is not None and not isinstance(v, bool) else None
    return int(m.group()) if m else 0


def _do(v):
    """収め方: 「つぐなう」か「ゆるす」(どちらも書いたもの・どちらでもないもの (お題の「...」) は読まない)"""
    s = str(v or "")
    if any(w in s for w in ("ない", "なく", "ず", "せん")):  # 「払わなくてよい」「ゆるさない」のような打ち消しは、どちらとも読まない (2026-10-08 確認役の指摘)
        return None
    pay, free = any(w in s for w in ("つぐな", "償", "払")), any(w in s for w in ("ゆる", "許"))
    return "つぐなう" if pay and not free else "ゆるす" if free and not pay else None


def _judges(a):
    """judge: {"M3": "つぐなう"} / [{"id": "M3", "do": "ゆるす"}] / {"id": "M3", "do": ...} のどれでも読む"""
    j = a.get("judge")
    if isinstance(j, dict) and "id" in j:
        j = [j]
    if isinstance(j, list):
        j = {x.get("id"): next((x[k] for k in ("do", "judge", "verdict") if k in x), None) for x in j if isinstance(x, dict)}
    out = {}
    for k, v in (j.items() if isinstance(j, dict) else []):
        if _mid(k) and _do(v):
            out[_mid(k)] = _do(v)
    return out


def _who(state, v):
    """まとめ役に選ぶ人: 大人の名前 (まわりに字があってもよい。1 人だけのとき) か「なし」。どちらでもなければ None (null・「...」は数えない)"""
    s = v.strip() if isinstance(v, str) else ""
    names = [q["name"] for q in adults(state)]
    if s in names:
        return s
    for h in sorted({q.get("household") for q in state["people"] if q.get("household")}, key=len, reverse=True):
        s = s.replace(h, "")  # 「ソル (ナギの家)」の「ナギの家」の中の「ナギ」を数えない (2026-10-08 確認役の指摘)
    hit = [n for n in names if n in s]
    hit = [n for n in hit if not any(n != m and n in m for m in hit)]  # 「ナギ」と「ナギ2」なら「ナギ2」
    if len(hit) == 1:
        return hit[0]
    return "なし" if not hit and any(w in s for w in ("なし", "いらない", "いない")) else None


def _yes(v):
    return v is True or str(v).strip().lower() in ("true", "はい", "する", "開く")


def _penalty(law, pen):
    """掟の罰 (G5 の第 2 段): {"for": ヤギ|倉|蓄え|刈る, "pay": 草の種のつかみ}。for がなければ掟の文から読む。「刈る 40」のような文でもよい。
    種類が 1 つに決まらないもの・数が 0 のもの (お題の例の写し) は罰なし。罰の文は掟の文の後ろにつける (お題・アプリ・採用の出来事に出る)"""
    if pen is None or isinstance(pen, bool) or pen == "":
        return
    d = pen if isinstance(pen, dict) else {"for": pen, "pay": pen}
    s, pay = str(d.get("for") or "").strip(), min(MAX_PAY, _num(d.get("pay")))
    kinds = [s] if s in KINDS else [k for k in KINDS if k in s] or [k for k in KINDS if k in law["text"]]
    if len(kinds) == 1 and pay > 0:
        law["penalty"] = {"for": kinds[0], "pay": pay}
        law["text"] += f" (罰: {KINDS[kinds[0]]}と、相手の家は、言い出した家に 草の種 {pay} つかみ を払う)"


def _g5_collect(state, c, p, a, fam):
    """季節の答えから、もめごとの収め方・祭り・まとめ役・呼びかけを集める (家族の代表の答えは、家族の大人みんなの答え)"""
    names = {q["name"] for q in fam}
    c["by"][p["name"]] = mine = _judges(a)
    for mid, v in mine.items():
        c["judge"].setdefault(mid, {}).setdefault(v, set()).update(names)
    if _yes(a.get("feast")):
        c["feast"] |= names
        c["feast_by"].add(p["name"])
    who = _who(state, a.get("leader"))
    if who:
        c["leader"].setdefault(who, set()).update(names)
    act = next((x for x in sorted(acts2(state), key=len, reverse=True) if x in str(a.get("call") or "")), None)
    if act:
        c["call"][p["name"]] = act


def _g5_meeting(state, c, n):
    """季節の集まり (G5。掟を決めたあと): 呼びかけに応じたか → もめごとを収める (まとめ役 → 集まり → 長老) → 祭り → まとめ役を選ぶ → 呼びかけ"""
    e2, g = state["era2"], _g5(state)
    g["meet_first"] = state["next_event"]  # この集まりからの出来事を、次のお題に見せる (集まりの出来事は 30 日の前に起きるので、前の季節のまとめに入らない)
    _check_leader(state)
    ads = {q["name"]: q for q in adults(state)}
    lead = g["leader"]  # お題を書いたときのまとめ役 (この集まりで選ばれた人は、次の集まりから)
    # 前の集まりのまとめ役の呼びかけに、この季節、大人の何人が応じたか (大人の半分をこえると「共同の仕事」。【文献】Fried)
    cl = g["call"]
    if cl:
        m = sum(1 for q in ads.values() if q["plan"]["activity"] == cl["activity"])
        ok = m * 2 > len(ads)
        g["joint"] += 1 if ok else 0
        log(state, "共同の仕事" if ok else "まとめ役", cl["by"], f"{cl['day']} 日目の集まりでの {cl['by']} の呼びかけ (みんなで {cl['activity']}) に、"
            f"この季節、大人 {len(ads)} 人のうち {m} 人が応じた")
        g["call"] = None
    # もめごとを収める: まとめ役 (自分の家のものでないもめごと。いくつでも) → 集まり (古いものから TALK_MAX まで。大人の半分をこえる人が同じ収め方)
    #   → 長老 (もめごとの家の人でない大人のうち、いちばん年上の人。その人の収め方が、ほかの収め方より少なくなければ)
    talked = 0
    for d in [d for d in g["disputes"] if d["status"] == OPEN]:
        parties = (d["from"], d["against"])
        v = c["by"].get(lead, {}).get(d["id"]) if lead in ads and ads[lead].get("household") not in parties else None
        if v:
            _verdict(state, d, v, "まとめ役", lead)
            continue
        if talked >= TALK_MAX:
            continue
        talked += 1
        tally = {k: len(s) for k, s in c["judge"].get(d["id"], {}).items()}
        top = max(tally.values(), default=0)
        elder = max([q for q in ads.values() if q.get("household") not in parties], key=lambda q: q["age"], default=None)  # 同じ年なら人の並びで先 (家の代表の決め方と同じ。2026-10-08)
        ev = c["by"].get(elder["name"], {}).get(d["id"]) if elder else None
        if top * 2 > n:
            _verdict(state, d, max(tally, key=tally.get), "集まり", None)
        elif ev and tally.get(ev, 0) >= top:
            _verdict(state, d, ev, "長老", elder["name"])
        elif tally:
            log(state, "もめごと", None, f"季節の集まりで、もめごと [{d['id']}] を話し合ったが、まとまらなかった ("
                + "・".join(f"{k} {x} 人" for k, x in sorted(tally.items())) + f" / 大人 {n} 人)", dispute=d["id"])
    # 祭り: 大人の半分をこえる人が望むか、まとめ役が望むと (【文献】Stein 1994)。まだ収まっていないもめごとの半分 (古いものから) が仲直りで収まる
    if len(c["feast"]) * 2 > n or lead in c["feast_by"]:
        cost = FEAST_DAYS * _need(state)
        if sum(f["kcal"] for f in state["store"]) >= cost:
            by = _move_food(state["store"], [], None, cost)
            g["feasts"] += 1
            g["feast_day"] = e2["step_day"]
            op = [d for d in g["disputes"] if d["status"] == OPEN]
            calm = op[:math.ceil(len(op) / 2)]
            for d in calm:
                _verdict(state, d, "仲直り", "祭り", None)
            alone = len(c["feast"]) * 2 <= n
            log(state, "祭り", lead if alone else None, (f"まとめ役の {lead} が決めて、" if alone else "")
                + f"季節のはじめに、村の全員で祭りをした (村の蓄えから {food_words(by)} を使った)"
                + (f"。もめごと {'・'.join('[' + d['id'] + ']' for d in calm)} は、祭りの場で仲直りして収まった" if calm else ""))
        else:
            log(state, "祭り", None, "祭りをしようとしたが、村の蓄えが足りなかった")
    # まとめ役を選ぶ (第 2 段から。大人の半分をこえる人が同じ人を書くと、その人。「なし」なら、まとめ役はいなくなる)
    tally = {k: len(v) for k, v in c["leader"].items()}
    if g["stage"] >= 2 and tally:
        g["votes"] = {"day": e2["step_day"], "votes": tally, "adults": n}
        best = max(sorted(tally), key=tally.get)
        if tally[best] * 2 > n and best == "なし" and lead:
            g["leader"], g["leader_day"] = None, None
            log(state, "まとめ役", lead, f"大人の半分をこえる人が「まとめ役はいらない」と答え、{lead} はまとめ役でなくなった (「なし」 {tally[best]} / {n})")
        elif tally[best] * 2 > n and best not in ("なし", lead):
            g["leader"], g["leader_day"] = best, e2["step_day"]
            g["leaders"].append({"name": best, "day": e2["step_day"]})
            log(state, "まとめ役", best, f"{best} ({ads[best].get('household')}) が、村のまとめ役に選ばれた (賛成 {tally[best]} / {n})"
                + (f"。{lead} に代わる" if lead else ""))
    # まとめ役の呼びかけ (次の季節にみんなでする仕事。応じるかは、それぞれが決める)
    act = c["call"].get(lead) if lead and g["leader"] == lead else None
    if act:
        g["call"] = {"by": lead, "activity": act, "day": e2["step_day"]}
        log(state, "まとめ役", lead, f"まとめ役の {lead} が、「次の季節は、みんなで {act} をしよう」と呼びかけた")


def _verdict(state, d, v, by, who):
    """もめごとが収まる。「つぐなう」なら、相手の家が言い出した家に払う (罰のある掟があれば罰の量、なければもめごとの分)"""
    g = _g5(state)
    law, paid, words = None, 0, ""
    if v == "つぐなう":
        law = next((l for l in reversed(state["laws"]) if l["status"] == "採用" and (l.get("penalty") or {}).get("for") == d["kind"]), None)
        paid, words = _pay(state, d["against"], d["from"], (law["penalty"]["pay"] if law else min(d["harm"], MAX_PAY)) * GRAIN)
        if round(paid / GRAIN) <= 0:  # 半つかみより少ないものは、払ったと数えない (2026-10-08 確認役の指摘)
            paid, words = 0, ""
    d.update(status="収まった", verdict=v, by=by, judge=who, paid=round(paid / GRAIN), law=law["id"] if law else None, end=state["day"])
    if by == "まとめ役":
        g["judged"] += 1
    elif not g["leader"]:
        g["settled"] += 1  # まとめ役のいない村が、集まり・長老・祭りで収めた (第 1 段)
    if by != "祭り":
        head = {"まとめ役": f"まとめ役の {who} が裁いた", "集まり": "季節の集まりで決まった",
                "長老": f"長老 (もめごとの家の人でない大人でいちばん年上) の {who} の言葉で決まった"}[by]
        res = (f"{d['from']}は{d['against']}をゆるした (払いはない)" if v == "ゆるす" else
               f"{d['against']}が{d['from']}に {words} を払った" + (f" (掟 [{law['id']}] の罰)" if law else "") if paid
               else f"{d['against']}には、払えるものがなかった")
        log(state, "裁き" if by == "まとめ役" else "収める", who, f"もめごと [{d['id']}] ({d['what']}) は、{head}: 「{v}」。{res}", dispute=d["id"], by=by)
    if law and paid > 0:  # 罰は、実際に何か払われたときだけ数える
        g["penalties"] += 1
        log(state, "罰", None, f"{d['against']}が、掟 [{law['id']}] の罰として、{d['from']}に {words} を払った", dispute=d["id"], law=law["id"])


def _pay(state, a, b, kcal):
    """a の家が b の家の倉に払う: a の家の倉の食べ物から。足りない分は、いちばん近い頭数のヤギで払う (1 頭 = GOAT_WORTH。足りない分がヤギ半頭分より
    少なければヤギは渡さない)【仮定】。ヤギも食べ物もなければ払えない"""
    got = []
    by = _move_food(_house(state, a)["store"], got, None, kcal)
    _house(state, b)["store"].extend(got)
    paid, n = sum(by.values()), 0
    words = [food_words(by)] if food_words(by) != "なし" else []
    for x in [x for x in state["era2"]["goats"] if x.get("owner") == a]:
        if kcal - paid < GOAT_WORTH / 2:
            break
        x["owner"] = b
        paid += GOAT_WORTH
        n += 1
    if n:
        words.append(f"ヤギ {n} 頭")
    return paid, "・".join(words)


def _sow(state, p, want):
    e2 = state["era2"]
    by = _move_food(state["store"], [], "草の種", want * UNITS["草の種"][1])
    if era_at_least(state, "G5") and _house(state, p.get("household"))["keep"]:  # G5: 家の倉を持つ家が、村の草の種を自分の畑にまいた
        _flow(state, p, 2, by.get("草の種", 0))
    n = int(by.get("草の種", 0) // UNITS["草の種"][1])
    if n:
        e2["fields"].append({"id": len(e2["fields"]), "day": state["day"], "seed": n, "work": 0.0, "state": "育つ", "by": p["name"], "harvested": 0,
                             "owner": p.get("household")})
        e2.setdefault("sown_years", []).append(state["day"] // YEAR)
        log(state, "畑", p["name"], f"{p['name']} がキャンプのそばの畑に、草の種 {n} つかみ をまいた", seed=n)


def _harvest(state, p, want):
    e2 = state["era2"]
    day = state["day"]
    ripe = [f for f in e2["fields"] if f["state"] == "実った"]
    for f in ripe:  # G4 の仕組みを入れる前にまいた畑: まいた人の家のもの
        if "owner" not in f:
            f["owner"] = next((q.get("household") for q in state["people"] if q["name"] == f.get("by")), None)
    if era_at_least(state, "G4"):
        ripe.sort(key=lambda f: f.get("owner") != p.get("household"))  # 自分の家の畑から
    for f in ripe:
        n = min(want, f["yield"] - f["harvested"])
        if n > 0:
            f["harvested"] += n
            want -= n
            st = _store_of(state, f.get("owner"))
            st.append({"kind": "草の種", "kcal": n * UNITS["草の種"][1], "day": day, "sown": True})
            if era_at_least(state, "G5"):
                _g5_reap(state, p, f.get("owner"), n, st is state["store"])
            log(state, "収穫", p["name"], f"{p['name']} が畑で草の種 {n} つかみ を刈った", amount=n)
            if day // YEAR not in e2["harvest_years"]:
                e2["harvest_years"].append(day // YEAR)
        if f["harvested"] >= f["yield"]:
            f["state"] = "刈った"
        if want <= 0:
            break


def _field_season(state, rng):
    """季節の最後の日の終わりに、次の季節の畑のようすを決める。秋にまいた畑は、冬と春をこえて、夏のはじめに実る
    (2026-10-07: 前は新しい季節の最初の日の終わりに決めていて、お題が古い季節のようすを見せていた。夏のお題に実った畑が出ず、
    秋のお題に 1 日で落ちる畑が出た)"""
    e2 = state["era2"]
    day = state["day"] + 1  # 次の季節の最初の日
    if day % SEASON_DAYS != 0:
        return
    sea = season(day)
    for f in e2["fields"]:
        if f["state"] == "育つ":
            sown_sea = season(f["day"])
            if sown_sea != "秋":
                f["state"] = "実らない"
                log(state, "畑", None, f"{sown_sea}にまいた畑 (草の種 {f['seed']} つかみ) は、芽が出たが実らなかった")
            elif sea == "夏" and day - f["day"] >= 2 * SEASON_DAYS - 1:
                yr_rng = random.Random(state["seed"] * 991 + day // YEAR)
                ratio = yr_rng.triangular(3, 15, 8)  # 【文献】初期の麦の種と収量の比 1:5〜1:15 (平年 1:8 を仮定)
                need = f["seed"] * 0.15 + 10  # 【仮定】草取りに要る人手 (時間)
                f["yield"] = int(f["seed"] * ratio * min(1.0, 0.3 + 0.7 * f["work"] / need) * (1 - f.get("lost", 0)))  # lost: G5 でヤギに荒らされた分
                f["state"] = "実った"
                log(state, "畑", None, f"畑の草の種が実った (まいた {f['seed']} つかみ。刈れるのは 約 {f['yield']} つかみ)", ratio=round(ratio, 1))
        elif f["state"] == "実った" and sea == "秋":
            lost = f["yield"] - f["harvested"]
            f["state"] = "刈った"
            if lost > 0:
                log(state, "畑", None, f"刈らずに残った草の種 約 {lost} つかみ は、落ちてしまった")


def _goat_work(state, p, t, sea):
    e2 = state["era2"]
    e2["tended_run"] = e2.get("tended_run", 0) + 1
    if sea in ("春", "夏"):
        milk = sum(3 for g in e2["goats"] if g["sex"] == "メス" and state["day"] - g["born"] >= YEAR)  # 【仮定】1 頭 1 日 3 杯
        if milk:
            p["food"].append({"kind": "乳", "kcal": milk * UNITS["乳"][1], "day": state["day"], "sown": True})
            t.setdefault("events", []).append(log(state, "乳", p["name"], f"{p['name']} がヤギの乳を {milk} 杯しぼった", amount=milk))


def _catch_goat(state, p, t, rng):
    e2 = state["era2"]
    wild = e2["wild_goats"]
    if t.get("place_id") != wild["place"] or wild["count"] <= 0:
        return
    if rng.random() < 0.03 + 0.04 * p["skills"].get("狩り", 0.2):  # 【仮定】子ヤギを連れ帰れる見込み (1 日。1 季節に 1〜2 頭ほど)
        wild["count"] -= 1
        sex = "メス" if rng.random() < 0.5 else "オス"
        e2["goats"].append({"id": e2["next_goat"], "sex": sex, "born": state["day"] - rng.randint(30, 90), "owner": p.get("household")})  # 生まれて 1〜3 か月の子ヤギ
        e2["next_goat"] += 1
        log(state, "ヤギ", p["name"], f"{p['name']} が北の丘で野生の子ヤギ ({sex}) を捕まえて、キャンプに連れ帰った")


def _famine_leave(state):
    """飢饉: よそから来た大人で、ひどく空腹の人は、見込み 4 割で村を出ていく (子は母といっしょに)。
    【文献】飢饉のとき、農耕の村でも人は親族やほかの集団のもとへ移って生きのびた (村の分裂・移住)。【仮定】割合は試作の値
    (2026-10-07 追加。G1 の 2 回目の前の試しで、よそから人が次々に加わったあと、冬に村の全員が動けないまま飢えたため)"""
    rng = _rng(state, 23)
    for p in [q for q in adults(state) if q.get("origin") == "よそから来た" and q["hunger"] >= 0.6]:
        if rng.random() < 0.4:
            p["alive"], p["left"] = False, state["day"]
            kids = [c for c in children(state) if c.get("mother") == p["name"]]
            for c in kids:
                c["alive"], c["left"] = False, state["day"]
            with_kids = f" (子の {'・'.join(c['name'] for c in kids)} もいっしょに)" if kids else ""
            log(state, "去る", p["name"], f"ひどく空腹の {p['name']} が、食べ物を求めて村を出ていった{with_kids}")
    for c in [c for c in children(state) if c.get("mother") and not any(q["name"] == c["mother"] and q["alive"] for q in state["people"])
              and any(q["name"] == c["mother"] and q.get("left") for q in state["people"])]:
        c["alive"], c["left"] = False, state["day"]
        log(state, "去る", c["name"], f"{c['name']} も、村を出た {c['mother']} を追って出ていった")


def _season_end(state, frac=1.0):
    """季節の終わり (または途中で区切った日)。見込みは、進んだ日数に合わせて frac 倍にする"""
    e2 = state["era2"]
    rng = _rng(state, 7)
    day = state["day"]
    e2["seasons"] += 1
    sea = season(day + 1)
    # 年をとる
    for p in [q for q in state["people"] if q["alive"]]:
        age = (day - p["born_day"]) // YEAR
        if age > p["age"]:
            p["age"] = age
            if p.get("child") and age >= ADULT:
                p.pop("child")
                p["mass"] = round(rng.uniform(45, 55), 1)
                _give_initial_knowledge(state, p)
                log(state, "大人になる", p["name"], f"{p['name']} が {ADULT} 歳になり、大人の仲間に加わった")
    # ヤギ: 世話がなければ逃げる・弱る。春のはじめに子が生まれる
    if e2["goats"] and e2.get("tended_run", 0) < 5 * frac:  # この回に世話をした日が少ない
        gone = [g for g in e2["goats"] if rng.random() < 0.15 * frac]
        for g in gone:
            e2["goats"].remove(g)
        if gone:
            log(state, "ヤギ", None, f"世話をする人が少なく、飼っていたヤギ {len(gone)} 頭がいなくなった")
    if sea == "春" and e2.get("kid_year") != (day + 1) // YEAR:
        e2["kid_year"] = (day + 1) // YEAR
        kids = 0
        for g in [g for g in e2["goats"] if g["sex"] == "メス" and day - g["born"] >= YEAR]:
            for _ in range(2 if rng.random() < 0.4 else 1):  # 【仮定】双子の見込み 4 割
                e2["goats"].append({"id": e2["next_goat"], "sex": "メス" if rng.random() < 0.5 else "オス", "born": day, "owner": g.get("owner")})
                e2["next_goat"] += 1
                kids += 1
        if kids:
            log(state, "ヤギ", None, f"飼っているヤギに、子ヤギが {kids} 頭生まれた")
    wild = e2["wild_goats"]
    if wild["count"] < 15 and rng.random() < 0.5 * frac:
        wild["count"] += 1
    # 子が生まれる (【文献】定住した農耕民の出生間隔 2〜3 年: 1 季節 0.1 で平均 2.5 年)
    men = [p for p in adults(state) if p["sex"] == "男" and p["age"] < 60]
    if state["camp"].get("dwelling_day") is not None and men:
        for w in [p for p in adults(state) if p["sex"] == "女" and 15 <= p["age"] <= 40]:
            if w["hunger"] >= 0.5 or day - w.get("last_birth", -10 ** 6) < YEAR:
                continue
            if rng.random() < 0.10 * frac:
                c = _new_person(state, rng, "女" if rng.random() < 0.5 else "男", 0, child=True, mother=w["name"])
                w["last_birth"] = day
                e2["births"] += 1
                log(state, "生まれる", w["name"], f"{w['name']} に子が生まれた。名前は {c['name']} ({c['sex']})")
    # 子の死亡 (【文献】15 歳までに 4〜5 割。0 歳 1 季節 0.06、1〜4 歳 0.015、5〜14 歳 0.004 を仮定) と、飢え
    for c in [c for c in children(state) if c["born_day"] < e2.get("step_day", 0)]:  # この回に生まれた子は、次の回から
        p_die = 0.06 if c["age"] < 1 else 0.015 if c["age"] < 5 else 0.004
        if c["hunger"] >= 0.9:
            p_die = max(p_die, 0.3)
        if rng.random() < p_die * frac:
            c["alive"] = False
            log(state, "死", c["name"], f"{c['name']} ({c['age']} 歳) が亡くなった")
    # 年をとった大人の死 (【仮定】55 歳から 1 季節 0.02)
    # G4 から、病気やけがで若い大人も亡くなる (【文献の目安】新石器時代の 15 歳の平均余命は 20〜25 年ほど (骨の年齢推定。資料で差が大きい)。
    #   【仮定】15〜39 歳 1 季節 0.0075 (1 年 3%)、40〜54 歳 0.0125 (1 年 5%))
    for p in adults(state):
        if p["age"] >= 55 and rng.random() < 0.02 * frac * (1 + (p["age"] - 55) / 10):
            p["alive"] = False
            log(state, "死", p["name"], f"{p['name']} ({p['age']} 歳) が年をとって亡くなった")
            _inherit(state, p)
        elif era_at_least(state, "G4") and p["age"] < 55 and rng.random() < (0.0075 if p["age"] < 40 else 0.0125) * frac:
            p["alive"] = False
            log(state, "死", p["name"], f"{p['name']} ({p['age']} 歳) が病で亡くなった")
            _inherit(state, p)
    # よそから人が来る (【仮定】1 季節 0.05、村の蓄えが今の人数の何日分あるかで増え、0.25 まで。
    #   2026-10-07: 蓄えの総量で決めていたのを、1 人あたりにした。人が増えても蓄えの総量が大きいと来つづけ、冬に飢えたため)
    if rng.random() < (0.05 + min(0.20, store_days(state) / 600)) * frac:
        n = rng.choice([1, 2, 2, 3])
        members = []
        for i in range(n):
            age = rng.randint(16, 35) if i < 2 else rng.randint(2, 12)
            members.append({"name": _name(e2["next_name"]), "sex": "女" if rng.random() < 0.5 else "男", "age": age})
            e2["next_name"] += 1  # 受け入れなくても名前は使い切る (同じ名前の別人を作らない)
        e2["visitors"] = [{"name": members[0]["name"], "members": members, "day": day}]
        txt = "、".join(f"{m['name']} ({m['sex']}、{m['age']} 歳)" for m in members)
        log(state, "訪れる", None, f"よその群れから {txt} がやって来て、「ここで暮らしたい」と言った")
    # 余り (1 年の終わり = 冬の終わり): 蓄えが、この 1 年に食べた量の 2 割以上あれば「余りの年」
    if sea == "春":
        eaten = sum(s["eaten"] for s in state["stats"][-YEAR:])
        store = sum(f["kcal"] for f in state["store"])
        if eaten and store >= 0.2 * eaten and (day // YEAR) not in e2.setdefault("surplus_years", []):
            e2["surplus_years"].append(day // YEAR)
    # 作ること (土器づくり・道具づくり) に、この季節の 20 日以上を使った人
    e2["specialists"] = [n for n, d in e2.get("craft_days", {}).items() if d >= 20 * frac]
    if era_at_least(state, "G3"):
        _storage_season(state, frac)
        if e2["specialists"]:
            e2.setdefault("specialist_log", []).append({"day": day, "names": e2["specialists"]})
    _sync_households(state)
    if era_at_least(state, "G5"):  # 家族を決めてから (この季節に生まれた子も母の家に入る)。村が分かれて大人が 12 人以下になれば、次の _note_mode で代表の方式が終わる
        _g5_season_end(state, frac)
    _note_mode(state)


# ---------------- 家族と代表 (計画 4: 大人が 12 人をこえたら、家族の代表だけが答える) ----------------

REP_FROM = 12


def _sync_households(state):
    """家族 (家) を決める。【仮定】最初からいる人とその子で「川辺の家」、よそから一緒に来た群れごとに 1 つの家 (群れの最初の人の名前で呼ぶ)。
    村で生まれた子は母の家に入り、大人になっても同じ家にいる"""
    named = {}
    for e in state["events"]:
        if e["type"] == "加わる" and e["text"].startswith("よそから来た "):
            names = e["text"][len("よそから来た "):].split(" が、")[0].split("・")
            for n in names:
                named.setdefault(n, names[0] + "の家")
    for p in state["people"]:
        if p.get("household"):
            continue
        if p["name"] in named:
            p["household"] = named[p["name"]]
        elif not p.get("origin"):
            p["household"] = "川辺の家"
    for p in state["people"]:
        if not p.get("household") and p.get("mother"):
            m = next((q for q in state["people"] if q["name"] == p["mother"]), None)
            if m and m.get("household"):
                p["household"] = m["household"]


def _hunger_word(h):
    return "満腹" if h < 0.1 else "少し空腹" if h < 0.3 else "かなり空腹" if h < 0.6 else "ひどく空腹 (危ない)"


def rep_mode(state):
    return len(adults(state)) > REP_FROM


def _note_mode(state):
    e2 = state["era2"]
    on = rep_mode(state)
    if on != e2.get("rep_mode", False):
        e2["rep_mode"] = on
        log(state, "家族", None, f"村の大人が {REP_FROM} 人をこえたので、これからは季節の集まりで、家族ごとに代表 (家族でいちばん年上の大人) が答える" if on
            else f"村の大人が {REP_FROM} 人以下になったので、また大人みんなが季節の集まりで答える")


def family(state, name):
    """name と同じ家の、生きている大人 (年上から)"""
    me = next(q for q in state["people"] if q["name"] == name)
    h = me.get("household")
    return sorted([q for q in adults(state) if h and q.get("household") == h], key=lambda q: -q["age"]) or [me]


def _reps(state):
    """家族の代表 (家族でいちばん年上の大人) の名前"""
    reps = {}
    for p in sorted(adults(state), key=lambda q: -q["age"]):
        reps.setdefault(p.get("household") or p["name"], p["name"])
    return set(reps.values())


def answerers(state):
    """季節のはじめに答える人 (G5: まとめ役は、家族の代表でなくても答える。代表は家族でいちばん年上の大人のまま (計画 4))"""
    ads = adults(state)
    if not state["era2"].get("rep_mode"):
        return [p["name"] for p in ads]
    _sync_households(state)
    who = _reps(state) | {_leader(state)}
    return [p["name"] for p in ads if p["name"] in who]


# ---------------- 判定 ----------------

def indicators(state):
    e2 = state["era2"]
    day = state["day"]
    last = state["stats"][-YEAR:]
    total = sum(s["eaten"] for s in last) or 1
    sown = sum(s.get("eaten_sown", 0) for s in last)
    # 村で生まれて 1 歳をこえた人 (2026-10-08: よその群れが連れてきた子は数えない。G1 は「定住すると子が生まれて人が増える」を見るため)
    kids_1y = sum(1 for c in state["people"] if c["alive"] and c.get("origin") == "生まれた" and c["age"] >= 1)
    yrs = sorted(set(e2["harvest_years"]))
    consec = any(y + 1 in yrs for y in yrs)
    return {
        "population": sum(1 for p in state["people"] if p["alive"]),
        "adults": len(adults(state)), "children": len(children(state)), "children_1y": kids_1y,
        "joined": sum(1 for q in state["people"] if q["alive"] and q.get("origin") == "よそから来た"), "births": e2["births"],
        "harvest_years": yrs, "harvest_2y": consec, "goats": len(e2["goats"]),
        "farm_share": round(sown / total, 2), "fields": sum(1 for f in e2["fields"] if f["state"] == "育つ"),
        "store": food_words(world.holdings({"food": state["store"]})), "seasons": e2["seasons"],
        "surplus_years": sorted(e2.get("surplus_years", [])),
        "surplus_2y": any(y + 1 in e2.get("surplus_years", []) for y in e2.get("surplus_years", [])),
        "specialists": len(e2.get("specialists", [])) if era_at_least(state, "G3") else 0,
        "pots": e2.get("pots", 0), "sickles": e2.get("sickles", 0),
        **_g4_indicators(state),
        **_g5_indicators(state),
        **_house_indicators(state),
    }


def _house_indicators(state):
    """家族の住まい (G3 から): できた数と、家の大きさのジニ係数 (【文献】Kohler ほか 2017。家のない家は 0 m²)"""
    if not era_at_least(state, "G3"):
        return {"houses_built": 0, "house_gini": 0.0}
    homes = state["era2"].get("homes", {})
    hs = sorted({q.get("household") for q in adults(state) if q.get("household")})
    sizes = [homes[h]["size"] if h in homes and homes[h]["built"] is not None else 0 for h in hs]
    return {"houses_built": sum(1 for s in sizes if s > 0), "house_gini": gini(sizes)}


def _g4_indicators(state):
    if not era_at_least(state, "G4"):
        return {"owned": False, "inherits": 0, "gini": 0.0}
    w = wealth(state)
    vals = sorted(w.values())
    return {"owned": any(v > 0 for v in vals), "inherits": state["era2"].get("inherits", 0), "gini": gini(vals),
            "wealth": w, "no_wealth": sum(1 for v in vals if v <= 0)}


def _g5_indicators(state):
    """G5 の目安 (G5 の前は 0。家族の数は G4 の 5 季節ごとの報告にも使うので、いつも数える)"""
    base = {"households": len(_homes(state)), "g5_stage": 0, "stage1": None, "leader": None, "leader_seasons": 0, "disputes": 0,
            "disputes_open": 0, "settled": 0, "judged": 0, "penalty_laws": 0, "penalties": 0, "feasts": 0, "fissions": 0,
            "left_people": 0, "joint": 0, "stress": 0.0}
    g = state["era2"].get("g5")
    if not era_at_least(state, "G5") or not g:
        return base
    return base | {"g5_stage": g["stage"], "stage1": g["stage1"], "leader": g["leader"],
                   "leader_seasons": (state["day"] + 1 - g["leader_day"]) // SEASON_DAYS if g["leader"] else 0,
                   "disputes": g["next"], "disputes_open": sum(1 for d in g["disputes"] if d["status"] == OPEN),
                   "settled": g["settled"], "judged": g["judged"],
                   "penalty_laws": sum(1 for l in state["laws"] if l["status"] == "採用" and l.get("penalty")),
                   "penalties": g["penalties"], "feasts": g["feasts"], "fissions": len(g["fissions"]),
                   "left_people": sum(len(f["people"]) for f in g["fissions"]), "joint": g["joint"], "stress": round(stress_p(state), 2)}


CRITERIA = {
    "G1": ("人が 10 人以上 (子をふくむ)、村で生まれて 1 歳をこえた子が 2 人以上、よそから来た人が 1 人以上",
           lambda i: i["population"] >= 10 and i["children_1y"] >= 2 and i["joined"] >= 1),
    "G2": ("畑の収穫が 2 年続く、飼うヤギが 5 頭以上、1 年に食べた量の半分以上が育てた植物と家畜から",
           lambda i: i["harvest_2y"] and i["goats"] >= 5 and i["farm_share"] >= 0.5),
    "G3": ("1 年の終わりに、その 1 年に食べた量の 2 割以上の蓄えが残る年が 2 年続く、1 季節のうち 20 日以上を作ること (土器づくり・道具づくり) に使った人が 1 人以上",
           lambda i: i["surplus_2y"] and i["specialists"] >= 1),
    # 2026-10-08 本人と決めた: ジニ係数 0.3 以上は通説より早すぎるので条件から外し、後の部の目安にする (ジニ係数は計算して記録は続ける)
    "G4": ("家族ごとの持ち物 (家の倉かヤギ) がある、受けつぎが 1 回以上",
           lambda i: i["owned"] and i["inherits"] >= 1),
    # 2026-10-08: G5 は 2 段階 (計画 2.1)。条件は第 2 段。第 1 段 (集まり・長老・祭りでまとまる) は止まらずに記録する (出来事「段階」・指標 stage1)
    "G5": ("第 2 段: 家族が 6 つ以上で、まとめ役がいる。罰のある掟が 3 つ以上採用されている。まとめ役がもめごとを 2 回以上裁いた。罰を 1 回以上払わせた",
           lambda i: i["g5_stage"] >= 2 and i["households"] >= 6 and bool(i["leader"]) and i["penalty_laws"] >= 3
           and i["judged"] >= 2 and i["penalties"] >= 1),
}
ORDER2 = ["G1", "G2", "G3", "G4", "G5", "G6"]
NAMES2 = {"G1": "村ができる", "G2": "畑と家畜", "G3": "余りと分業", "G4": "持ち物と差", "G5": "リーダーと決まり", "G6": "交易・町・記録"}


def check(state):
    era = state["era"]
    ind = indicators(state)
    desc, fn = CRITERIA.get(era, ("(まだ作っていない)", lambda i: False))
    met = fn(ind)
    since = state["day"] - state["era_log"][-1]["day"]
    state["era_info"] = {"era": era, "name": NAMES2[era], "next": desc, "met": met, "since": since, "indicators": ind}
    if met and era != ORDER2[-1]:
        nxt = ORDER2[ORDER2.index(era) + 1]
        state["era"] = nxt
        state["era_log"].append({"era": nxt, "day": state["day"], "indicators": ind})
        state["era_info"] = {"era": nxt, "name": NAMES2[nxt], "next": CRITERIA.get(nxt, ("(まだ作っていない)",))[0], "met": False, "since": 0, "indicators": ind}
        return True
    return False


# ---------------- お題 ----------------

RULES2 = characters.RULES.replace(
    "- 昼にする活動は 1 日に 1 つ (ふつうは前の夜に決めた予定) です。夕方と夜にできるのは、話す・決める・食べ物を分ける・蓄えに入れる・蓄えから取る・食べる・眠る ことです",
    "- これから季節の終わりまでの主な仕事を 1 つ決めます。毎日その仕事をします (けがの日は休む)。食べ物は、その日に食べる分を手元に残し、残りは村の蓄えに入れ、足りなければ蓄えから取ります (村の決まりとして自動で行う)")


def _season_digest(state, p, first):
    """前の季節に起きたこと (出来事の記録から)"""
    ev = [e for e in state["events"] if e["id"] >= first]
    mine = [e for e in ev if e.get("who") == p["name"] and e["type"] not in ("話す",)]
    by = {}
    for e in mine:
        by.setdefault(e["type"], []).append(e)
    rows = []
    for t, es in by.items():
        if t == "収穫":
            continue
        if t in ("採集", "狩り"):
            ok = [e for e in es if (e.get("data") or {}).get("kcal", 0) > 0 or "とった" in e["text"] or "しとめた" in e["text"]]
            rows.append(f"- {t} {len(es)} 日 (食べ物が見つかった日 {len(ok)})。例: [出来事 {es[-1]['id']}] {es[-1]['text']}")
        else:
            for e in es[-3:]:
                rows.append(f"- [出来事 {e['id']}] {e['text']}")
    harv = {}
    for e in ev:
        if e["type"] == "収穫":
            harv[e["who"]] = harv.get(e["who"], 0) + (e.get("data") or {}).get("amount", 0)
    if harv:
        rows.append("- 畑で刈った草の種: " + "、".join(f"{n} {v} つかみ" for n, v in harv.items()))
    grew = [e for e in ev if e["type"] == "育つ"]
    if grew:
        midden = sum(1 for e in grew if "殻を捨てた所" in e["text"])
        rows.append(f"- キャンプのそばで木の実の木が {len(grew)} 本育った (種を埋めた所から {len(grew) - midden} 本・殻を捨てた所から {midden} 本)")
    village = [e for e in ev if e["type"] in ("生まれる", "死", "加わる", "去る", "訪れる", "畑", "ヤギ", "ヤギを食べる", "大人になる", "けが", "掟", "住まい", "フェーズ", "蓄えが尽きる", "家族", "虫")]
    rows += [f"- [出来事 {e['id']}] {e['text']}" for e in village[-25:] if e.get("who") != p["name"]]
    rains = sum(1 for e in ev if e["type"] == "雨")
    if rains:
        rows.append(f"- 雨の夜 {rains} 回")
    return "\n".join(rows) or "(Society 2.0 の最初の季節。まだ何もしていない)"


def _need(state):
    return sum(BASE_KCAL + 500 for _ in adults(state)) + sum(next(k for a, k in CHILD_EAT if c["age"] < a) for c in children(state))


def store_days(state):
    """村の蓄えが、今の人数で何日分か"""
    return int(sum(f["kcal"] for f in state["store"]) / max(1, _need(state)))


def _village(state):
    e2 = state["era2"]
    kids = "、".join(f"{c['name']} ({c['sex']}、{c['age']} 歳、母 {c.get('mother', '-')})" for c in children(state)) or "なし"
    ads = "、".join(f"{q['name']} ({q['sex']}、{q['age']} 歳)" for q in adults(state))
    fields = [f for f in e2["fields"] if f["state"] in ("育つ", "実った")]
    fl = "、".join(f"{'実って刈れる' if f['state'] == '実った' else '育っている'}畑 (まいた種 {f['seed']} つかみ{'、残り 約 ' + str(f['yield'] - f['harvested']) + ' つかみ' if f['state'] == '実った' else ''})" for f in fields) or "なし"
    goats = e2["goats"]
    gl = f"{len(goats)} 頭 (メス {sum(1 for g in goats if g['sex'] == 'メス')}・オス {sum(1 for g in goats if g['sex'] == 'オス')})" if goats else "なし"
    wild = state["places"][[pl["id"] for pl in state["places"]].index(e2["wild_goats"]["place"])]["label"]
    days = store_days(state)
    return (f"村の大人: {ads}\n村の子: {kids}\n村の蓄え: {food_words(world.holdings({'food': state['store']}))} (今の人数で 約 {days} 日分)\n"
            f"畑: {fl}\n飼っているヤギ: {gl}\n"
            + (f"村の土器: {e2.get('pots', 0)} 個 (草の種 {e2.get('pots', 0) * POT_HOLD} つかみ分)、村の石の鎌: {e2.get('sickles', 0)} 本\n" if era_at_least(state, "G3") else "")
            + (_houses_text(state) if era_at_least(state, "G3") else "")
            + (_houses_line(state) if era_at_least(state, "G4") else "")
            + f"{wild} のあたりに、野生のヤギの群れ (約 {e2['wild_goats']['count']} 頭) がいる\n")


def _houses_line(state):
    e2 = state["era2"]
    rows = []
    for h in sorted({p.get("household") for p in state["people"] if p["alive"] and p.get("household")}):
        hs = _house(state, h)
        goats = sum(1 for g in e2["goats"] if g.get("owner") == h)
        rows.append(f"{h} (倉: {'持つ' if hs['keep'] else '持たない'}、{food_words(world.holdings({'food': hs['store']})) or 'からっぽ'}、ヤギ {goats} 頭)")
    return "家ごとの持ち物: " + "、".join(rows) + "\n"


FACTS_HOUSE = (f"家族の住まい: 村の住まい (キャンプのまん中) で眠れるのは {world.DWELL_CAP} 人まで。家族ごとに、キャンプのそばに四角い住まいを建てられる "
               f"(住まいを建てる。家族の大人が働いて、のべ 約 {HOUSE_HOURS} 時間でできる。そのあとも働くと広くなる)。家族の住まいのある家族は、そこで眠る。"
               "雨の夜に屋根の下で眠れなかった人は、疲れがとれない\n")


FACTS_G3 = ("土器: 土器づくりでは、キャンプで川の粘土をこねて器の形を作り、乾かして火で焼く。慣れるほど、1 日に多く作れる。"
            f"村の蓄えの草の種を土器に入れておくと、虫やネズミに食べられない (1 個に {POT_HOLD} つかみ)。"
            "土器に入らない草の種は、季節ごとに 20 分の 1 ほどが虫やネズミに食べられる。土器はときどき割れる\n"
            "石の鎌: 道具づくりでは、石の刃を木の柄にはめた鎌を作れる (1 本に 2 日ほど)。鎌を使うと、畑を刈る量が 2 倍になる (村の鎌の数の人まで)。鎌もときどき割れる\n")


FACTS_G4 = ("家の倉: 家族ごとに倉を持てる (keep)。keep を true にした家では、家の人がまいた畑で刈った草の種は、村の蓄えではなく家の倉に入る。"
            "家の倉の食べ物は、村の蓄えが足りないときに、その家の人が食べる。keep が false の家の畑で刈った草の種は、村の蓄えに入る。"
            "家の倉は家族の住まいの中に置くので、家族の住まいのない家は、keep を true にしても、刈った草の種は村の蓄えに入る\n"
            "持ち主: 畑はまいた人の家のもの。ヤギは捕まえた人の家のもの (子ヤギは母ヤギの家のもの)。刈るときは自分の家の畑から刈る\n"
            "受けつぎ: 家の代表 (いちばん年上の大人) が亡くなると、家の倉・畑・ヤギは、家で次に年上の大人が受けつぐ\n")


FACTS2 = ("畑: 蓄えの草の種を、秋にキャンプのそばの畑にまくと、冬と春をこえて夏のはじめに実り、刈れる (まいた量の数倍。年によって違う)。"
          "ほかの季節にまくと実らない。育っているあいだに畑仕事 (草取り) をする人が少ないと、実りが減る。夏のうちに刈らないと落ちてしまう\n"
          "ヤギ: 野生の子ヤギは「ヤギを捕まえる」で連れ帰れることがある。飼っているヤギは、世話をする人がいないといなくなることがある。"
          "春に子を産み、春と夏は世話をすると乳がとれる。つぶして肉にすることもできる\n"
          "子: 村の子は、15 歳になるまで村の蓄えから食べて育つ\n")


FACTS_G5 = ("もめごと: 家どうしのあいだで次の (1)〜(4) のことが起きると、季節の終わりに、損をした家が言い出して、もめごとになることがある。"
            "村の家が多いほど、もめごとになりやすい。祭りをした季節は、なりにくい。"
            "(1) ヤギ: 世話をする人が少ない季節に、家のヤギが、よその家の畑を荒らす (荒らされた畑は、実りが 2 割減る) "
            "(2) 倉: ひどく空腹の人が、村の蓄えにも自分の家の倉にも食べ物がないときに、よその家の倉から取って食べる (日々の食べ物の出し入れと同じく、自動で起きる) "
            "(3) 蓄え: ある家の大人が、村の蓄えに入れた量にくらべて、ほかの家より多く村の蓄えから取る (言い出すのは、いちばん多く入れた家。1 季節に 1 つの家まで。"
            f"大人 1 人あたり {FREE_DAYS} 日分の食べ物より少ない差では、もめごとにならない。家の倉に食べ物がある家は、半分の差でなる) "
            "(4) 刈る: よその家の畑で刈った草の種が、みな畑の持ち主の家の倉に入る (言い出すのは、刈った人の家)\n"
            "収める: もめごとは、季節の集まりで収める。収め方は「つぐなう」(相手の家が、言い出した家に払う) か「ゆるす」(払わずに収める)。"
            f"集まりで話し合えるのは、古いもめごとから {TALK_MAX} つまで。大人の半分をこえる人が同じ収め方を選ぶと、それに決まる。"
            "決まらないときは、もめごとの家の人でない大人のうち、いちばん年上の人 (長老) の選んだ収め方が、ほかの収め方より少なくなければ、それに決まる。"
            f"払う量は、もめごとの分 ({MAX_PAY} つかみまで)。家の倉の食べ物で払い、足りなければ、足りない分にいちばん近い頭数のヤギで払う "
            f"(1 頭を草の種 {GOAT_WORTH // GRAIN} つかみ 分とする)。払えるものがなければ払わない\n"
            "村を出る: もめごとが収まらないまま 2 季節たつと、言い出した家が、家の人みんな (子も) で村を出ていくことがある (1 年に 1 つの家まで)。"
            f"家のヤギと家の倉の食べ物は持って行き、家の畑は村のものになる。{DROP_AGE} 季節たっても収まらないもめごとは、だれも言わなくなる\n"
            f"祭り: 大人の半分をこえる人が望むと (feast)、季節のはじめに村の全員で祭りをする。村の蓄えから、村の全員の {FEAST_DAYS} 日分の食べ物を使う。"
            "祭りでは、まだ収まっていないもめごとの半分 (古いものから) が、仲直りして収まる。祭りをした季節は、だれも村を出ていかない\n")

FACTS_G5_2 = ("まとめ役: 大人の半分をこえる人が同じ人を選ぶと (leader)、その人が村のまとめ役になる。まとめ役は、亡くなるか、村を出るか、"
              "大人の半分をこえる人がほかの人か「なし」を選ぶまで続く。まとめ役は、家族の代表でなくても、季節の集まりで答える。"
              "まとめ役は、自分の家のものでないもめごとを、一人で、いくつでも裁ける (まとめ役の judge が、集まりより先に決まる。"
              "まとめ役が裁かなかったもめごとは、集まりで話し合う)。まとめ役が祭りをすると答えると、ほかの人の答えにかかわらず祭りをする。"
              "まとめ役は、次の季節にみんなでする仕事を呼びかけられる (call)。応じるかどうかは、それぞれが決める\n"
              f"罰: 掟を提案するときに、罰をつけられる (penalty)。罰は、もめごとのもと (1)〜(4) のどれか 1 つと、払う草の種のつかみ ({MAX_PAY} まで)。"
              "罰のある掟が採用されていると、その掟にあたることが起きたときは、必ずもめごとになる。そのもめごとが「つぐなう」に決まると、"
              "もめごとの分ではなく、罰の量を払う\n")


def _g5_facts(state):
    if not era_at_least(state, "G5"):
        return ""
    return FACTS_G5 + (FACTS_G5_2 if (state["era2"].get("g5") or {}).get("stage", 1) >= 2 else "")


def _g5_text(state):
    """G5 のお題の節: 村の家・まとめ役・票・罰のある掟・呼びかけ・祭り・まだ収まっていないもめごと・この前の集まりから起きたこと・村の蓄えへの出し入れ (見ればわかる事実だけ。状態は変えない)"""
    if not era_at_least(state, "G5"):
        return ""
    g = state["era2"].get("g5") or {}
    lead, two, since = g.get("leader"), g.get("stage", 1) >= 2, g.get("meet_first") or state["next_event"]
    homes = _homes(state)
    rows = [f"村の家族: {len(homes)} つ ({'、'.join(homes)})"]
    if two:
        hh = next((q.get("household") for q in adults(state) if q["name"] == lead), "")
        rows.append(f"まとめ役: {lead} ({hh}。{g['leader_day']} 日目から)" if lead else "まとめ役: いない")
        v = g.get("votes")
        if v:
            rows.append(f"{v['day']} 日目の集まりで、まとめ役に名前があがった人: "
                        + "、".join(f"{k} (大人 {x} 人分)" for k, x in sorted(v["votes"].items(), key=lambda kv: -kv[1])) + f" (大人 {v['adults']} 人)")
        rows.append("罰のある掟: " + ("、".join(l["id"] for l in state["laws"] if l["status"] == "採用" and l.get("penalty")) or "まだない"))
    c = g.get("call")
    if c:
        rows.append(f"{c['day']} 日目の集まりで、まとめ役の {c['by']} が「次の季節は、みんなで {c['activity']} をしよう」と呼びかけた (この季節のこと)")
    if g.get("feast_day") is not None:
        rows.append(f"前に祭りをしたのは {g['feast_day']} 日目 (これまで {g['feasts']} 回)")
    op = [d for d in g.get("disputes", []) if d["status"] == OPEN]
    rows.append("まだ収まっていないもめごと:" + ("" if op else " なし"))
    for i, d in enumerate(op):
        age = (state["day"] - d["day"]) // SEASON_DAYS
        when = ("前の季節の終わりに起きた" if age == 0 else f"{age} 季節 収まっていない。この季節の集まりでも収まらないと、季節の終わりに、"
                + (f"{d['from']}が村を出ていくことがある" if age + 1 < DROP_AGE else "だれも言わなくなる"))
        talk = "" if lead else "。この季節の集まりで話し合う" if i < TALK_MAX else f"。この季節の集まりでは話し合えない (古いものから {TALK_MAX} つまで)"
        rows.append(f"- [{d['id']}] ({d['kind']}) {d['from']}が言い出した。相手は{d['against']} ({when}{talk}): {d['what']}"
                    f" (草の種にして 約 {d['harm']} つかみ 分) [出来事 {d['event']}]")
    ev = [e for e in state["events"] if e["id"] >= since and e["type"] in G5_EVENTS]
    if ev:
        rows += ["この前の集まりから起きたこと:"] + [f"- [出来事 {e['id']}] {e['text']}" for e in ev[-12:]]
    if g.get("last_flow"):
        rows.append("前の季節の、家ごとの村の蓄えへの出し入れ (大人の分。草の種にして): "
                    + "、".join(f"{h} 入れた 約 {i}・取った 約 {o} つかみ" for h, (i, o) in g["last_flow"].items() if h in homes))
    return "\n## 村の集まり (もめごと・祭り" + ("・まとめ役" if two else "") + ")\n" + "\n".join(rows) + "\n"


def season_prompt(state, p, first):
    e2 = state["era2"]
    g5, g = era_at_least(state, "G5"), e2.get("g5") or {}  # G5 の部分は、G5 の前はみな空の文字 (お題は前と同じ)
    lead, two = g.get("leader"), g.get("stage", 1) >= 2
    solo = bool(g5 and e2.get("rep_mode") and p["name"] not in _reps(state))  # 家族の代表でないまとめ役 (自分の分だけ答える)
    places = "\n".join(f"- {pl['id']}: {pl['label']}" for pl in state["places"])
    names = [q["name"] for q in adults(state) if q is not p]
    vis = ""
    if e2["visitors"]:
        v = e2["visitors"][0]
        txt = "、".join(f"{m['name']} ({m['sex']}、{m['age']} 歳)" for m in v["members"])
        vis = (f"\n## よそから来た人\n{txt} が「ここで暮らしたい」と言っている (いっしょに来た一つの群れ)。村に受け入れるか決めてください "
               f"(accept: 受け入れるなら true、受け入れないなら false)。大人の半分をこえる賛成で、群れの全員が村に加わる。"
               f"加わった大人は、この季節は村でいちばん多い仕事をし、次の季節から自分で決める\n")
    sea = season(state["day"] + 1)
    st = dict(state, day=state["day"] + 1)  # この回の最初の日のようすで書く
    sow = '"sow": 0, ' if sea == "秋" else ""
    keep = '"keep": false, ' if era_at_least(state, "G4") and not solo else ""
    goat = '"eat_goat": 0, ' if e2["goats"] and not solo else ""
    acc = f'"accept": {{"{e2["visitors"][0]["name"]}": true}}, ' if e2["visitors"] else ""
    pick = characters._pick_line(st)
    me = characters._me(st, p).replace("(誰でも入れたり取ったりできる)", "(日々の出し入れは自動)")
    fam_txt, fam_json = "", ""
    if e2.get("rep_mode") and not solo:
        fam = [q for q in family(state, p["name"]) if q is not p]
        kids = [c for c in children(state) if c.get("household") and c.get("household") == p.get("household")]
        rows = [f"- {q['name']} ({q['sex']}、{q['age']} 歳。採集 {q['skills']['採集']:.2f}、狩り {q['skills']['狩り']:.2f}。"
                f"おなか {_hunger_word(q['hunger'])}{'、けが' if q.get('injured') else ''}{'。まとめ役なので、自分で答える' if q['name'] == lead else ''})" for q in fam]
        rows += [f"- 子: {c['name']} ({c['sex']}、{c['age']} 歳、母 {c.get('mother') or '-'})" for c in kids]
        fam_txt = (f"\n## あなたの家族 ({p.get('household')})\n村の大人が {REP_FROM} 人をこえたので、季節の集まりでは家族ごとに、いちばん年上の大人が代表して答える。"
                   f"あなたは {p.get('household')} の代表。\n" + ("\n".join(rows) if rows else "- (ほかの家族はいない)") +
                   "\n- 家族の大人の主な仕事も、あなたが決める (family。書かなかった人は、あなたと同じ仕事)"
                   "\n- sow・pick・plant・harvest の数は、家族の大人一人ひとりの量 (eat_goat は家族で何頭か)"
                   f"\n- 掟の投票と、よそから来た人の受け入れ{('、もめごとの収め方・祭り' + ('・まとめ役' if two else '') + 'の答え') if g5 else ''}は、家族の大人みんなの答えとして数える\n")
        if fam:
            fam_json = '"family": {' + ", ".join(f'"{q["name"]}": {{"activity": "採集", "place": "camp"}}' for q in [q for q in fam if q["name"] != lead][:2]) + '}, '

    if solo:
        fam_txt = (f"\n## あなたはまとめ役\nあなたは {p.get('household')} の代表ではないが、村のまとめ役なので、季節の集まりで答える。決めるのは自分の仕事だけ "
                   "(家族の仕事・家の倉・ヤギをつぶす数は、家族の代表が決める)。掟の投票・受け入れ・もめごとの収め方・祭り・まとめ役の答えは、あなた一人の答えとして数える\n")
    op = [d["id"] for d in g.get("disputes", []) if d["status"] == OPEN] if g5 else []
    me5 = g5 and lead == p["name"]
    g5_now = ("7. 村の集まり (上の「村の集まり」を見て決める。どれも書かなくてもよい)\n"
              + ("   もめごと: まだ収まっていないもめごとの収め方を、番号ごとに「つぐなう」か「ゆるす」で書く (judge)\n" if op else "")
              + "   祭り: この季節のはじめに、村の全員で祭りをするか (feast: するなら true、しないなら false)\n"
              + ("   まとめ役: まとめ役にしたい人の名前を書く (leader。まとめ役はいらないなら「なし」、決めないなら null)\n"
                 '   罰: 掟を提案するときに罰をつけるなら、proposal の penalty に {"for": "ヤギ" か "倉" か "蓄え" か "刈る", "pay": 草の種のつかみ} を書く (つけないなら null)\n'
                 if two else "")
              + ("   あなたは村のまとめ役。あなたの家のものでないもめごとは、あなたの judge で決まる。次の季節にみんなでする仕事を 1 つ呼びかけられる (call: 仕事の名前。しないなら null)\n"
                 if me5 else "")) if g5 else ""
    g5_json = ("\n " + ('"judge": {' + ", ".join(f'"{i}": "..."' for i in op) + "}, " if op else "") + '"feast": false, '
               + ('"leader": "...", ' if two else "") + ('"call": null, ' if me5 else "")) if g5 else ""
    pen = ', "penalty": null' if g5 and two else ""

    return f"""{RULES2}

{me}{FACTS2}{(FACTS_G3 + FACTS_HOUSE) if era_at_least(state, "G3") else ""}{FACTS_G4 if era_at_least(state, "G4") else ""}{_g5_facts(state)}
## 村のようす
{_village(state)}
## 前の季節のこと
{_season_digest(state, p, first)}

## 最近聞いた話
{characters._heard(p)}
{fam_txt}
## 覚えていること
{characters._knowledge(state, p)}

## 集団の掟 (季節のはじめに、みんなで集まって決める)
{characters._laws(state, with_pending=True)}
{_g5_text(state)}{vis}
## いま
{state["day"] + 1} 日目、{sea}。これから {SEASON_DAYS - (state["day"] + 1) % SEASON_DAYS} 日 (この季節の終わりまで) の仕事を決める集まり (途中で村の蓄えが尽きて、ひどく空腹の人が出たら、そこで集まり直す)。
1. 話したいことがあれば話す (0〜2 つ。相手は仲間の名前か「みんな」)。前と同じ言い回しをくり返さず、あなたらしい言葉で
2. この季節の主な仕事を決める (job)。仕事は {' / '.join(acts2(state))} から 1 つ、場所は下の一覧の id から 1 つ、一緒に行きたい人 ({'、'.join(names) or 'なし'}) がいれば書く
   畑仕事 (草取り・刈り入れ) は camp で行う
   ヤギの世話は camp で行う。ヤギを捕まえるは、野生のヤギのいる場所で行う
3. {(pick.strip().rstrip('。') + '。取るのはこの季節の毎夕で、1 人 40 つかみまで') if pick.strip() else 'この季節 (' + sea + ') は、キャンプのそばの木から実は取れない (実がなるのは夏と秋)'}
4. 持っている木の実 (なければ村の蓄えの木の実) を、この回の最初の日にキャンプのそばに埋める (plant、つかみ、5 まで) こともできる
   秋なら、季節のはじめに、蓄えの草の種をキャンプのそばの畑にまく量 (sow、つかみ、1000 まで) を書ける (主な仕事とは別にできる)
   実った畑があれば、毎夕いくつ刈るか (harvest、つかみ、60 まで) を書ける (主な仕事とは別にできる)
{'   飼っているヤギを、この回の最初の日に何頭つぶして肉にするか (eat_goat、頭。肉は干して蓄えに入れる。2 頭は残す) を書ける' + chr(10) if e2['goats'] and not solo else ''}
{'   家の倉を持つか (keep: 持つなら true、持たないなら false) を決める (家の代表が決める)' + chr(10) if era_at_least(state, "G4") and not solo else ''}5. 覚えていることを更新する (新しく分かったことを追加、確かさを変える、間違っていたら忘れる)
6. 掟: みんなで守りたい決まりがあれば提案できる (なければ null)。今の掟と提案に、賛成か反対かを投票する (against に反対する理由、reason に決めた理由)
{g5_now}{8 if g5_now else 7}. 今の気持ちを一言

場所の一覧:
{places}

## 答えの形 (JSON)
{{"say": [{{"to": "みんな", "text": "..."}}],
 "job": {{"activity": "採集", "place": "camp", "with": []}}, {sow}"pick": 0, "plant": 0, "harvest": 0, {goat}{acc}{fam_json}{keep}{g5_json}
 "knowledge": [{{"op": "add", "text": "...", "because": [出来事の番号], "confidence": 0.6}}],
 "proposal": {{"text": "...", "because": [出来事の番号]{pen}}},
 "votes": [{{"id": "L0", "against": "反対する理由", "agree": true, "reason": "決めた理由"}}],
 "feeling": "..."}}"""
