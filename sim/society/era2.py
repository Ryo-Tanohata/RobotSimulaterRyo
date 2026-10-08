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
        knowledge.vote(state, p, a.get("votes"))
        fam = family(state, name) if e2.get("rep_mode") else [p]  # 代表の答えは、家族の大人みんなの答え
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
                                     "eat_goat": max(0, min(5, _int(a.get("eat_goat")))) if q is p else 0,
                                     "harvest": max(0, min(60, _int(a.get("harvest"))))}
        p["feeling"] = str(a.get("feeling", ""))[:120]
        for v, ok in (a.get("accept").items() if isinstance(a.get("accept"), dict) else []):
            for q in fam:
                accept.setdefault(v, []).append((q["name"], ok is True or ok in ("true", "はい", "賛成")))
    for t in talk:  # 話は聞き手に届く
        for n, q in alive.items():
            if n != t["from"] and (t["to"] == "みんな" or t["to"] == n):
                q["heard"].append({k: t[k] for k in ("day", "from", "text", "event")})
                q["heard"] = q["heard"][-30:]
    for msg in knowledge.settle_meeting(state):  # 季節ごとに集まる
        log(state, "掟", None, msg)
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
            _move_food(p["food"], state["store"], None, have - keep)
        elif have < keep:
            _move_food(state["store"], p["food"], None, keep - have)
    ate = {"total": 0, "sown": 0, "by": {}}
    for c in children(state):
        need = next(k for a, k in CHILD_EAT if c["age"] < a)
        got_items = []
        by = _move_food(state["store"], got_items, None, need)
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
    grain = sum(f["kcal"] for f in state["store"] if f["kind"] == "草の種") / UNITS["草の種"][1]
    safe = min(grain, e2.get("pots", 0) * POT_HOLD)
    lost = int((grain - safe) * PEST_LOSS * frac)
    if lost > 0:
        _move_food(state["store"], [], "草の種", lost * UNITS["草の種"][1])
        log(state, "虫", None, f"蓄えの草の種 約 {lost} つかみ が、虫やネズミに食べられた" + (f" (土器に入れていた 約 {int(safe)} つかみ は無事)" if safe else ""), amount=lost)
    for key, rate, what in (("pots", POT_BREAK, "土器"), ("sickles", SICKLE_BREAK, "鎌")):
        broke = sum(1 for _ in range(e2.get(key, 0)) if rng.random() < rate * frac)
        if broke:
            e2[key] -= broke
            log(state, "道具", None, f"村の{what}が {broke} {'個' if key == 'pots' else '本'} 割れた (残り {e2[key]})")


def _sow(state, p, want):
    e2 = state["era2"]
    by = _move_food(state["store"], [], "草の種", want * UNITS["草の種"][1])
    n = int(by.get("草の種", 0) // UNITS["草の種"][1])
    if n:
        e2["fields"].append({"id": len(e2["fields"]), "day": state["day"], "seed": n, "work": 0.0, "state": "育つ", "by": p["name"], "harvested": 0})
        e2.setdefault("sown_years", []).append(state["day"] // YEAR)
        log(state, "畑", p["name"], f"{p['name']} がキャンプのそばの畑に、草の種 {n} つかみ をまいた", seed=n)


def _harvest(state, p, want):
    e2 = state["era2"]
    day = state["day"]
    for f in [f for f in e2["fields"] if f["state"] == "実った"]:
        n = min(want, f["yield"] - f["harvested"])
        if n > 0:
            f["harvested"] += n
            want -= n
            state["store"].append({"kind": "草の種", "kcal": n * UNITS["草の種"][1], "day": day, "sown": True})
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
                f["yield"] = int(f["seed"] * ratio * min(1.0, 0.3 + 0.7 * f["work"] / need))
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
        e2["goats"].append({"id": e2["next_goat"], "sex": sex, "born": state["day"] - rng.randint(30, 90)})  # 生まれて 1〜3 か月の子ヤギ
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
                e2["goats"].append({"id": e2["next_goat"], "sex": "メス" if rng.random() < 0.5 else "オス", "born": day})
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
    for p in adults(state):
        if p["age"] >= 55 and rng.random() < 0.02 * frac * (1 + (p["age"] - 55) / 10):
            p["alive"] = False
            log(state, "死", p["name"], f"{p['name']} ({p['age']} 歳) が年をとって亡くなった")
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


def answerers(state):
    """季節のはじめに答える人"""
    ads = adults(state)
    if not state["era2"].get("rep_mode"):
        return [p["name"] for p in ads]
    _sync_households(state)
    reps = {}
    for p in sorted(ads, key=lambda q: -q["age"]):
        reps.setdefault(p.get("household") or p["name"], p["name"])
    return [p["name"] for p in ads if p["name"] in reps.values()]


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
    }


CRITERIA = {
    "G1": ("人が 10 人以上 (子をふくむ)、村で生まれて 1 歳をこえた子が 2 人以上、よそから来た人が 1 人以上",
           lambda i: i["population"] >= 10 and i["children_1y"] >= 2 and i["joined"] >= 1),
    "G2": ("畑の収穫が 2 年続く、飼うヤギが 5 頭以上、1 年に食べた量の半分以上が育てた植物と家畜から",
           lambda i: i["harvest_2y"] and i["goats"] >= 5 and i["farm_share"] >= 0.5),
    "G3": ("1 年の終わりに、その 1 年に食べた量の 2 割以上の蓄えが残る年が 2 年続く、1 季節のうち 20 日以上を作ること (土器づくり・道具づくり) に使った人が 1 人以上",
           lambda i: i["surplus_2y"] and i["specialists"] >= 1),
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
            + f"{wild} のあたりに、野生のヤギの群れ (約 {e2['wild_goats']['count']} 頭) がいる\n")


FACTS_G3 = ("土器: 土器づくりでは、キャンプで川の粘土をこねて器の形を作り、乾かして火で焼く。慣れるほど、1 日に多く作れる。"
            f"村の蓄えの草の種を土器に入れておくと、虫やネズミに食べられない (1 個に {POT_HOLD} つかみ)。"
            "土器に入らない草の種は、季節ごとに 20 分の 1 ほどが虫やネズミに食べられる。土器はときどき割れる\n"
            "石の鎌: 道具づくりでは、石の刃を木の柄にはめた鎌を作れる (1 本に 2 日ほど)。鎌を使うと、畑を刈る量が 2 倍になる (村の鎌の数の人まで)。鎌もときどき割れる\n")


FACTS2 = ("畑: 蓄えの草の種を、秋にキャンプのそばの畑にまくと、冬と春をこえて夏のはじめに実り、刈れる (まいた量の数倍。年によって違う)。"
          "ほかの季節にまくと実らない。育っているあいだに畑仕事 (草取り) をする人が少ないと、実りが減る。夏のうちに刈らないと落ちてしまう\n"
          "ヤギ: 野生の子ヤギは「ヤギを捕まえる」で連れ帰れることがある。飼っているヤギは、世話をする人がいないといなくなることがある。"
          "春に子を産み、春と夏は世話をすると乳がとれる。つぶして肉にすることもできる\n"
          "子: 村の子は、15 歳になるまで村の蓄えから食べて育つ\n")


def season_prompt(state, p, first):
    e2 = state["era2"]
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
    goat = '"eat_goat": 0, ' if e2["goats"] else ""
    acc = f'"accept": {{"{e2["visitors"][0]["name"]}": true}}, ' if e2["visitors"] else ""
    pick = characters._pick_line(st)
    me = characters._me(st, p).replace("(誰でも入れたり取ったりできる)", "(日々の出し入れは自動)")
    fam_txt, fam_json = "", ""
    if e2.get("rep_mode"):
        fam = [q for q in family(state, p["name"]) if q is not p]
        kids = [c for c in children(state) if c.get("household") and c.get("household") == p.get("household")]
        rows = [f"- {q['name']} ({q['sex']}、{q['age']} 歳。採集 {q['skills']['採集']:.2f}、狩り {q['skills']['狩り']:.2f}。"
                f"おなか {_hunger_word(q['hunger'])}{'、けが' if q.get('injured') else ''})" for q in fam]
        rows += [f"- 子: {c['name']} ({c['sex']}、{c['age']} 歳、母 {c.get('mother') or '-'})" for c in kids]
        fam_txt = (f"\n## あなたの家族 ({p.get('household')})\n村の大人が {REP_FROM} 人をこえたので、季節の集まりでは家族ごとに、いちばん年上の大人が代表して答える。"
                   f"あなたは {p.get('household')} の代表。\n" + ("\n".join(rows) if rows else "- (ほかの家族はいない)") +
                   "\n- 家族の大人の主な仕事も、あなたが決める (family。書かなかった人は、あなたと同じ仕事)"
                   "\n- sow・pick・plant・harvest の数は、家族の大人一人ひとりの量 (eat_goat は家族で何頭か)"
                   "\n- 掟の投票と、よそから来た人の受け入れは、家族の大人みんなの答えとして数える\n")
        if fam:
            fam_json = '"family": {' + ", ".join(f'"{q["name"]}": {{"activity": "採集", "place": "camp"}}' for q in fam[:2]) + '}, '

    return f"""{RULES2}

{me}{FACTS2}{FACTS_G3 if era_at_least(state, "G3") else ""}
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
{vis}
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
{'   飼っているヤギを、この回の最初の日に何頭つぶして肉にするか (eat_goat、頭。肉は干して蓄えに入れる。2 頭は残す) を書ける' + chr(10) if e2['goats'] else ''}
5. 覚えていることを更新する (新しく分かったことを追加、確かさを変える、間違っていたら忘れる)
6. 掟: みんなで守りたい決まりがあれば提案できる (なければ null)。今の掟と提案に、賛成か反対かを投票する (against に反対する理由、reason に決めた理由)
7. 今の気持ちを一言

場所の一覧:
{places}

## 答えの形 (JSON)
{{"say": [{{"to": "みんな", "text": "..."}}],
 "job": {{"activity": "採集", "place": "camp", "with": []}}, {sow}"pick": 0, "plant": 0, "harvest": 0, {goat}{acc}{fam_json}
 "knowledge": [{{"op": "add", "text": "...", "because": [出来事の番号], "confidence": 0.6}}],
 "proposal": {{"text": "...", "because": [出来事の番号]}},
 "votes": [{{"id": "L0", "against": "反対する理由", "agree": true, "reason": "決めた理由"}}],
 "feeling": "..."}}"""
