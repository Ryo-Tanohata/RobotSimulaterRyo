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
import unicodedata

import archive
import characters
import knowledge
import world
from world import (BASE_KCAL, FRUIT_KCAL, H, SEASON_DAYS, UNITS, W, _move_food, food_words, holdings, log, season)

YEAR = 4 * SEASON_DAYS
ADULT = 15
# 現実の言葉と重ならないように作った名前 (子とよそから来る人)
NAMES = ["ナギ", "ソル", "ミラ", "ケト", "ハユ", "リオ", "トワ", "サエ", "ユノ", "カイ", "ネム", "ラタ", "フウ", "モエ", "シノ",
         "テオ", "アル", "ヨナ", "クラ", "ニイ", "エマ", "オト", "セキ", "ホノ", "ルネ", "ヤエ", "マロ", "コハ", "スイ", "ノア"]
# G6 から使う名前 (2026-10-09 本人と決めた: 上の 30 個は使い切って「ソル2」のような名前が続くので、G6 から新しく作った 30 個を使う。G5 のあいだは変えない)。
#   上と同じく、現実のよくある言葉と重ならないように作った (前からいる人の名前とも重ならない)
NAMES_G6 = ["ラキ", "ソナ", "ケナ", "トナ", "ハソ", "オセ", "キサ", "セヤ", "リセ", "タユ", "ヒセ", "ロワ", "ヌオ", "キオ", "テナ",
            "ラニ", "ケセ", "シエ", "ナセ", "ホタ", "ムイ", "セオ", "ルタ", "アコ", "オネ", "ワユ", "ネイ", "ソワ", "ユエ", "ホミ"]
ACTS2 = ["採集", "狩り", "探索", "休む", "道具づくり", "火おこし", "種まき", "住まいを建てる", "畑仕事", "ヤギの世話", "ヤギを捕まえる"]
ACTS_G3 = ["土器づくり"]  # G3 (余りと分業) から
CRAFTS = ("土器づくり", "道具づくり")


def era_at_least(state, era):
    e = state.get("era", "G1")
    return e in ORDER2 and ORDER2.index(e) >= ORDER2.index(era)


def acts2(state):
    return (ACTS2 + (ACTS_G3 if era_at_least(state, "G3") else []) + (ACTS_G6 if era_at_least(state, "G6") else [])
            + ([ACT_RECORD] if era_at_least(state, "G6") and ((state["era2"].get("g6") or {}).get("open") or {}).get("数え札") else []))
CHILD_EAT = [(3, 800), (10, 1300), (15, 1800)]  # 【仮定】子が 1 日に食べる量 (年齢まで, kcal)
UNITS.setdefault("乳", ("杯", 150))              # 【仮定】ヤギの乳 1 杯
world.FOOD_NAME.setdefault("乳", "ヤギの乳")
world.SPOIL.setdefault("乳", 1)                  # 【仮定】乳はその日のうちに飲む
GOAT_MEAT = 20                                   # 【仮定】ヤギ 1 頭の肉 (ルクの肉の切れ、600 kcal)
# 草の量でヤギの数に上限をつける (2026-10-10 本人と決めた「草の量で上限をつける」。計画 5 の G2「草が足りないと弱る」を、ここで入れた。
#   それまでは数を止めるものがなく、G6 に入った 3539 日目の 45 頭が、4289 日目に 711 頭になった)
#   【文献】草地 1 ha が 1 年に養える頭数 (1 年じゅう放牧して、草地をこわさない数):
#   シリアの草原 (雨 年 200 mm ほど) で雌ヒツジ 1 頭に 4.5 ha (約 0.2 頭/ha。ひどい日照りや寒さのときだけ足しのえさ。van der Veen 1967, FAO の放牧の試し)。
#   イスラエル南の草原 (雨 年 250 mm。一年草) でヒツジ 1 頭に 0.6〜1.0 ha (約 1〜1.7 頭/ha。足しのえさなし。Tadmor ほか 1974)。
#   ギリシャの低い木の林で、ヤギ 1 ha に 1 頭が「ほどほど」、4 頭は草が減りヤギがやせた (Tsiouvaras ほか 1999)。
#   草は春に多く、夏から秋のはじめに少ない (ヨルダンの草原。Louhaichi・Gamoun ほか 2021)。1 年の頭数は、それをならした数なので、季節では変えない
#   【仮定】この世界 (冬に雨が降り、野生の麦が育つ川ぞいの草原と丘) は、その間の 1 ha に 0.5 頭 (日照りの年にも養える側。
#   干し草や足しのえさはなく、野生のヤギやけものも同じ草を食べる)。ヤギとヒツジ、子ヤギと大人は同じ 1 頭と数える。
#   広さは地図 (1 マス 25 m、80 × 80 マス = 2 km 四方) の草原と丘のマスだけで数え、群れは地図の外へは行かない
#   (林と川は数えない。畑は小さいので引かない)。10 頭単位に丸める (今の地図は 276 ha で、養える頭数 K = 約 140 頭)。
#   【仮定】飼っている頭数 N が K より多い季節は、多すぎる分 (N − K) の 3 分の 1 がやせていなくなり (持ち主ごとの頭数に比べて分ける)、
#   春に子を産む母ヤギは K/N の見込みに減る。世話が足りないといなくなる決まりは前のまま。N が K 以下の季節は何も変えない (乱数も引かない)
#   (春に子が生まれると K をこえ、夏から冬に減るので、群れは K の 1〜2 倍のあいだを上下する。4379 日目の写しを 8 季節進めると、
#   だれもつぶさなくても 608 → 264 → 春に 307 → 189 頭になった)
#   【文献】初めのヤギ飼いは、若いオスを先に食べ、メスを残した (Zeder & Hesse 2000, Science 287)。つぶすかどうかは、村の人が決める
PASTURE_PER_HA = 0.5
PASTURE_LOSS = 1 / 3
PASTURE_SALT = 43  # 草が足りないときだけ引く乱数 (43 を 31 で割った余り 12 は、前からの塩の余り 3・7・11・23・29・0・6・10 と重ならない)


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


def _next_name(state):
    """新しい名前 (生まれた子・よそから来る人)。G6 からは NAMES_G6 から (数は g6 の next_name。G6 の前は前のまま)"""
    e2, g = state["era2"], state["era2"].get("g6")
    if g is not None and era_at_least(state, "G6"):
        i = g.get("next_name", 0)
        g["next_name"] = i + 1
        return NAMES_G6[i % len(NAMES_G6)] + ("" if i < len(NAMES_G6) else str(i // len(NAMES_G6) + 1))
    n = _name(e2["next_name"])
    e2["next_name"] += 1
    return n


def _new_person(state, rng, sex, age, child=False, mother=None, origin="生まれた", name=None):
    e2 = state["era2"]
    if name is None:
        name = _next_name(state)
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
    g6 = era_at_least(state, "G6")  # G6 の部分は、G6 の前は何もしない
    c6 = {"trade": {}, "trade_by": {}, "house": {}, "seal": {}, "store": set(), "store_by": set()}  # G6: 季節の集まりの答え
    if g6:
        _g6_new_season(state)
    yname = [] if year_end(state) else None  # 年の名前 (年の終わりの集まりだけ読む)
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
        t = _year_name_text(a.get("year_name")) if yname is not None else ""
        if t:
            yname.append((p, t, len(fam)))  # 家族の大人の数だけ数える (ほかの答えと同じ)
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
            if g6 and act in ACTS_G6 + [ACT_RECORD]:  # 行き先・持って行く物・残すもの (e2["jobs"] には入れない)
                _g6_job(state, q, job, own)
            e2["jobs"][q["name"]] = {"sow": max(0, min(1000, _int(a.get("sow")))), "pick": max(0, min(40, _int(a.get("pick")))),
                                     "plant": max(0, min(5, _int(a.get("plant")))),
                                     "eat_goat": max(0, min(5, _int(a.get("eat_goat")))) if q is p and own else 0,
                                     "harvest": max(0, min(60, _int(a.get("harvest"))))}
        p["feeling"] = str(a.get("feeling", ""))[:120]
        p["feeling_day"] = state["day"]  # いつの気持ちか (2026-10-09 から。ダッシュボードで日付を出す)
        if era_at_least(state, "G4") and own and "keep" in a and p.get("household"):
            _house(state, p["household"])["keep"] = a.get("keep") is True or a.get("keep") in ("true", "はい")
        for v, ok in (a.get("accept").items() if isinstance(a.get("accept"), dict) else []):
            for q in fam:
                accept.setdefault(v, []).append((q["name"], ok is True or ok in ("true", "はい", "賛成")))
        if g5:
            _g5_collect(state, c5, p, a, fam)
        if g6:
            _g6_collect(state, c6, p, a, fam, own)
    for t in talk:  # 話は聞き手に届く
        for n, q in alive.items():
            if n != t["from"] and (t["to"] == "みんな" or t["to"] == n):
                q["heard"].append({k: t[k] for k in ("day", "from", "text", "event")})
                q["heard"] = q["heard"][-30:]
    for msg in knowledge.settle_meeting(state):  # 季節ごとに集まる
        log(state, "掟", None, msg)
    if g5:
        _g5_meeting(state, c5, len(alive))  # 掟を決めてから (この集まりで採用された罰の掟も、この集まりで使う)
    if g6:
        _g6_meeting(state, c6, len(alive))  # 印 → 村の蓄えの封 → 申し出 (よそから来た人の受け入れの前)
    _settle_visitors(state, accept, len(alive))
    _eat_goats(state)
    if yname:
        _year_name(state, yname, len(alive))  # 集まりの最後に (ほかの集まりの出来事の並びは変わらない)


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
        vr = random.Random(v["seed"]) if v.get("seed") is not None else rng  # G6: ほかの村から来た群れは、その群れの乱数で (前からの列に足さない)
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
            # G6: 行き先のない「交換に行く」・記録の中身のない「記録をつける」はまねない (G6 の前はだれも選べないので、前と同じ)
            plans = [q["plan"] for q in adults(state) if q["name"] in accept_answered(e2) and q["plan"]["activity"] not in ACTS_G6 + [ACT_RECORD]]
            common = max(plans, key=lambda pl: sum(1 for x in plans if x["activity"] == pl["activity"] and x["place"] == pl["place"])) if plans else {"activity": "採集", "place": "camp"}
            for m in v["members"]:
                q = _new_person(state, vr, m["sex"], m["age"], child=m["age"] < ADULT, origin="よそから来た", name=m["name"],
                                mother=guardian if m["age"] < ADULT else None)
                e2["joined"].append(q["name"])
                q["household"] = member_names[0] + "の家"
                if v.get("from"):  # G6: 来たほかの村 (家を建てる場所を、その村の方角にする)
                    q["from_village"] = v["from"]
                if not q.get("child"):
                    q["plan"] = {"activity": common["activity"], "place": common["place"], "with": []}
                    e2["jobs"][q["name"]] = {"sow": 0, "pick": 0, "plant": 0, "eat_goat": 0, "harvest": 0}
            names = "・".join(member_names)
            o = _other(state, v.get("from")) if v.get("from") else None
            log(state, "加わる", None, f"よそから来た {names} が、村に加わった ({o['name'] + 'から。' if o else ''}賛成 {yes} / {n_adults})")
        else:
            o = _other(state, v.get("from")) if v.get("from") else None
            log(state, "去る", None, f"よそから来た {v['name']} たちは、受け入れられず{'、' + o['name'] + 'へ帰って' if o else '去って'}いった (賛成 {yes} / {n_adults})")
        if v.get("from"):
            _g6_settled(state, v, yes * 2 > n_adults)
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
        elif act == ACT_RECORD and era_at_least(state, "G6"):
            _g6_keep_day(state, p, t)
        if act in CRAFTS:
            e2.setdefault("craft_days", {})[p["name"]] = e2.get("craft_days", {}).get(p["name"], 0) + 1
            if era_at_least(state, "G3"):
                _craft(state, p, t, act)
    if era_at_least(state, "G6"):
        _g6_trips_day(state)  # 交換に行く (出かけている人は、夕方に木から取らず、畑も刈らない)
    # 夕方、キャンプのそばの木から取る (季節のはじめに決めた量。world.evening の「取る」を使う)
    takes = []
    for p in adults(state):
        job = e2["jobs"].get(p["name"], {})
        if job.get("pick") and not _injured_today(p) and not (p.get("today") or {}).get("away"):
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
        if n and not _injured_today(p) and not (p.get("today") or {}).get("away"):
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
                took = sum(_move_food(_house(state, p.get("household"))["store"], p["food"], None, keep - have - got).values())
                got += took
                if took and era_at_least(state, "G6"):  # G6: 印で封をした家の倉を開けた (封のかけら)
                    _g6_opened(state, p, "倉")
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
            obs = _g6_obsidian_blades(state, n) if era_at_least(state, "G6") else 0
            extra = f" (うち {obs} 本は黒曜石の刃)" if obs else ""
            log(state, "道具", p["name"], f"{p['name']} が石の刃を木の柄にはめた鎌を {n} 本作った{extra} (村の鎌 {e2['sickles']} 本)", count=n)
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
        obs = min(e2.get(key, 0), (e2.get("g6") or {}).get("obs_sickles", 0)) if key == "sickles" and era_at_least(state, "G6") else 0
        hits = [i for i in range(e2.get(key, 0)) if rng.random() < rate * frac * (OBS_BREAK if i < obs else 1)]  # 1 つに 1 回引く (G6 の前と同じ数)
        broke = len(hits)
        if obs:
            e2["g6"]["obs_sickles"] -= sum(1 for i in hits if i < obs)
        if broke:
            e2[key] -= broke
            log(state, "道具", None, f"村の{what}が {broke} {'個' if key == 'pots' else '本'} 割れた (残り {e2[key]})")


# ---------------- 家族の住まい (2026-10-08 追加。G3 から働く。本人の希望「人数が増えて家族になっているので、シミュレーションに反映したい」) ----------------
# 【文献】Flannery 2002: 先土器新石器 B (PPNB) に、丸い家と共同の倉から、四角い家と家ごとの倉へ変わった。Kohler ほか 2017: 家の大きさで豊かさの差 (ジニ係数) を測る
# 【仮定】家族の住まい 1 軒に、のべ 400 時間の働き (大人 2 人で 3 週間ほど。広さ 約 20 m²)。そのあと 200 時間ごとに 10 m² 広くなる (80 m² まで)。
#   (2026-10-08 写しの試しで、120 時間では 4〜6 日で建ち、1 季節で 80 m² になったので、400 時間にした。
#    広げるのも 200 時間ごとでは 2 季節で 80 m² になったので、400 時間ごとに 10 m² にした (大人 2 人で 80 m² まで 半年ほど))
#   村の住まい (キャンプのまん中) で眠れるのは 12 人まで (world.DWELL_CAP)。家族の住まいのある家族は、そこで眠る
HOUSE_HOURS, HOUSE_BASE, HOUSE_STEP, HOUSE_MAX = 400, 20, 10, 80


def _homes_built(state):
    return {h for h, v in state["era2"].get("homes", {}).items() if v.get("built") is not None}


def _house_site(state, h=None):
    """家族の住まいを建てる場所: キャンプから 5〜9 マスの輪の上で、川でなく、南西の畑と村の住まいから離れ、ほかの家と重ならない所
    (G6: 11〜15 マスの輪も使う。ほかの村から来た家は、まずその村の方角の 11〜15 マスに建てる。ブラクのまわりの、来たところごとの小さな集まり)"""
    cx, cy = state["camp"]["x"], state["camp"]["y"]
    used = [(v["x"], v["y"]) for v in state["era2"].get("homes", {}).values()]

    def ok(x, y):
        ix, iy = int(x), int(y)
        if not (0 <= ix < W and 0 <= iy < H) or state["terrain"][iy][ix] == "r":
            return False
        if (x < cx - 1 and y > cy + 1) or math.hypot(x - (cx - 2.7), y - (cy - 1.7)) < 3:  # 南西は畑、北西は村の住まい
            return False
        return not any(math.hypot(x - ux, y - uy) < 2.2 for ux, uy in used)

    rings = (5, 7, 9)
    if era_at_least(state, "G6"):
        src = next((q.get("from_village") for q in state["people"] if h and q.get("household") == h and q.get("from_village")), None)
        o = _other(state, src) if src else None
        if o:
            ang = math.atan2(o["edge"][1] - cy, o["edge"][0] - cx)
            for r in (11, 13, 15):
                for k in sorted(range(24), key=lambda k: abs(math.remainder(math.radians(k * 15) - ang, 2 * math.pi))):
                    a = math.radians(k * 15)
                    if abs(math.remainder(a - ang, 2 * math.pi)) > math.radians(60):
                        continue
                    x, y = round(cx + r * math.cos(a), 1), round(cy + r * math.sin(a), 1)
                    if ok(x, y):
                        return x, y
        rings += (11, 13, 15)
    for r in rings:
        for k in range(12):
            a = math.radians(k * 30 + (15 if r in (7, 11, 15) else 0))
            x, y = round(cx + r * math.cos(a), 1), round(cy + r * math.sin(a), 1)
            if ok(x, y):
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
        x, y = _house_site(state, h)
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
        size = min(HOUSE_MAX, HOUSE_BASE + HOUSE_STEP * int((v["work"] - HOUSE_HOURS) // HOUSE_HOURS))
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
        if i == 1 and era_at_least(state, "G6"):  # G6: 印で封をした村の蓄えを開けた (封のかけら)
            _g6_opened(state, p, "蓄え")


def _incident(state, kind, frm, against, kcal, what, eid=None, sealed=False):
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
    if sealed:  # G6: 印で封をした倉の封が割れていた (必ずもめごとになる)
        x["sealed"] = True


def _steal(state, p, want):
    """G5: ひどく空腹で、村の蓄えにも自分の家の倉にも食べ物がない大人は、よその家の倉 (多い家から) から取って食べる (出来事は家の組ごとに 1 季節 1 回)"""
    hs, mine, homes = state["era2"].get("house", {}), p.get("household"), _homes(state)
    if not mine:  # 家のない人 (今はいない) は取らない。取ると、もめごとのもとにならず、毎日記録が出るため (2026-10-08 確認役の指摘)
        return
    sealed = ((state["era2"].get("g6") or {}).get("seals") or {}) if era_at_least(state, "G6") else {}  # G6: 封をした倉は、ほかの倉がからになってから
    for h in sorted([h for h in hs if h in homes and h != mine and hs[h]["store"]], key=lambda h: (h in sealed, -sum(f["kcal"] for f in hs[h]["store"]))):
        if want <= 0:
            break
        by = _move_food(hs[h]["store"], p["food"], None, want)
        want -= sum(by.values())
        new = not any((x["kind"], x["from"], x["against"]) == ("倉", h, mine) for x in _g5(state)["incidents"])
        if h in sealed:
            eid = log(state, "封", p["name"], f"{h}の倉の封が割れていた: ひどく空腹の {p['name']} ({mine}) が、封を割って食べ物を取って食べた", owner=h, home=mine) if new else None
        else:
            amt = "食べ物" if era_at_least(state, "G6") else food_words(by)  # G6: 量は記録にない
            eid = log(state, "倉から取る", p["name"], f"ひどく空腹の {p['name']} が、{h}の倉から {amt} を取って食べた", owner=h, home=mine) if new else None
        _incident(state, "倉", h, mine, sum(by.values()), f"{mine}の人が、{h}の倉から食べ物を取って食べた", eid, sealed=h in sealed)


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
    claim = _g6_claim(state, d) if era_at_least(state, "G6") else ""  # G6: 記録があれば正しい量、なければ言い出した家の覚え
    d["event"] = log(state, "もめごと", None, f"もめごと [{d['id']}] ({d['kind']}): {d['from']}が、{d['against']}のことで不満を言い出した。"
                     f"{d['what']} (草の種にして {'' if d.get('record') else '約 '}{d['harm']} つかみ 分{claim})", dispute=d["id"], about=d["kind"])


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
            what = f"{hh}の人が{o}の畑で刈った草の種 {n} つかみ は、みな{o}の倉に入った"
            if era_at_least(state, "G6") and not _g6_cover(state, "刈る"):  # G6: 記録がなければ量は分からない
                what = f"{hh}の人が{o}の畑で刈った草の種は、みな{o}の倉に入った (量は記録になく、覚えによる)"
            _incident(state, "刈る", hh, o, n * REAP_SHARE * GRAIN, what)
    # (3) 蓄え: 村の蓄えに入れた量にくらべて、ほかの家より多く取った家 (1 季節に 1 つの家まで。言い出すのは、いちばん多く入れた家)
    flow = raw = {h: v for h, v in g["flow"].items() if h in homes}
    if era_at_least(state, "G6"):
        flow = _g6_credit(state, raw)  # G6: 配給の記録 (村の蓄えの記録を全部残せた季節は、作る人などの働いた日を「入れた」に数える)
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
            what = (f"この季節、{h}の大人は、村の蓄えから草の種にして 約 {round((o + s) / GRAIN)} つかみ 分を取り"
                    + (f" (家の畑にまいた村の草の種 {round(s / GRAIN)} つかみ をふくむ)" if s else "")
                    + f"、入れたのは 約 {round(i / GRAIN)} つかみ 分だった (おもな仕事: {acts}"
                    + (f"。家の倉に {food_words(holdings({'food': hs[h]['store']}))} がある" if h in full else "")
                    + f")。{frm}は 約 {round(flow[frm][0] / GRAIN)} つかみ 分を入れた")
            if era_at_least(state, "G6") and not _g6_cover(state, "蓄え"):  # G6: 記録がなければ量は分からない
                what = f"この季節、{h}の大人は、村の蓄えに入れた量にくらべて多く取った (おもな仕事: {acts})。量は記録になく、{frm}の覚えによる"
            elif flow is not raw and (flow[h][0] != raw[h][0] or flow[frm][0] != raw[frm][0]):  # G6: 入れた量に、配給の記録の働いた日を数えた (文を事実どおりに)
                what += " (入れた量は、記録した働いた日の分をふくむ)"
            _incident(state, "蓄え", frm, h, over[h] / len(homes), what)  # 【仮定】言い出した家の損 = 取りすぎを村の家の数で割った分
    g["last_flow"] = {h: [round(v[0] / GRAIN), round((v[1] + v[2]) / GRAIN)] for h, v in sorted(raw.items())}
    g["flow"], g["reap"] = {}, {}
    # もめごとのもと → もめごと (家が多いほどなりやすい。罰のある掟にあたることは必ずなる。同じ家どうしの同じ中身で収まっていないものには重ねる)
    pen = {l["penalty"]["for"] for l in state["laws"] if l["status"] == "採用" and l.get("penalty")}
    p, new = stress_p(state), 0
    for inc in g["incidents"]:
        if inc["from"] not in homes or inc["against"] not in homes:
            continue
        old = next((d for d in g["disputes"] if d["status"] == OPEN and (d["kind"], d["from"], d["against"]) == (inc["kind"], inc["from"], inc["against"])), None)
        if old:
            add = max(1, round(inc["kcal"] / GRAIN))
            if "harm_true" in old:  # G6: 記録のないもめごとは、言い出した家の覚えで重ねる
                ratio = old["harm"] / max(1, old["harm_true"])
                old["harm_true"] += add
                add = max(1, round(add * ratio))
            old["harm"] += add
            old["because"] += inc["events"]
            log(state, "もめごと", None, f"もめごと [{old['id']}] に、また同じことが重なった: {inc['what']}", dispute=old["id"])
        elif new < MAX_NEW and (inc["kind"] in pen or inc.get("sealed") or rng.random() < p):  # sealed は G6 だけ
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
        rec = d.get("record")  # G6: 記録のあるもめごとは、記録を見て確かめる (話し合える数に数えない)
        if v:
            if rec:
                _g6_check(state, d)
            _verdict(state, d, v, "まとめ役", lead)
            continue
        if talked >= TALK_MAX and not rec:
            continue
        talked += 0 if rec else 1
        if rec:
            _g6_check(state, d)
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
    if v == "つぐなう" and not law and era_at_least(state, "G6"):  # G6: 記録のない量を覚えで払った (払った家が多く払ったと思うと、覚え違いのもと。払ったと書いたあとに)
        _g6_after_pay(state, d, round(paid / GRAIN))


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


# ---------------- G6 交易・町・記録: ほかの村・交換・貸し借り・印と封・覚え・数え札 → 封筒 → 粘土の板・町 (2026-10-09 追加。G6 に入ってから働く) ----------------
# 第 4 部「町と文字」(計画 2.1。設計書 docs/society_phase/G6_design.md。「本人に確かめること」1〜17 は、2026-10-09 にすべておすすめの通りに決まった)。
#   町と記録は別々の条件で、どちらが先でもよい (届いた日を区切り F3・F4 に残す)。両方そろうと Society 2.0 の終わり
# 考え方: 目標を上から置かない。ほかの村は、記録に残る出来事 (村を出た家・G6 で来たよその群れの来たところ・交換をもとめて来た人) からだけ生まれる。
#   記録の道具は、それが答える困りごとが起きてから使えるようになる (印 → 数え札 → 封筒 → 粘土の板。順は本人と決めた。part2.md 6.3)。使うかは人が決める
# 【文献】Renfrew, Dixon & Cann 1968・Ortega ほか 2014・Ibáñez ほか 2015: 黒曜石は 300 km ほどまで多く届き、遠くへは少しずつ (模型では、手渡しだけでは
#   300 km より遠くへ届きにくく、遠くの相手をもつ村があると説明しやすい)。Yacobi & Gopher 2023: 親族どうしの交換 (という読み)。Davidson & McKerrell 1976・1980: ハラフの土器も村から村へ動いた
# 【文献】Duistermaat 1996・Akkermans & Duistermaat 1996/97・2004: サビ・アビヤドの封泥 (前 6,300〜6,000 年ごろ。多くは焼けた村、前 6,000 年ごろ)。入れ物に封をし、開けたあとの封のかけらを
#   取っておいた。Frangipane ほか 2007: アルスランテペの宮殿 (前 3,400〜3,000 年ごろ) の 1 つの倉に 30 の印 (取り出す多くの人の印という読み)。印が「持ち主」を示したかは
#   議論がある (Duistermaat 2012・2013) ので、文は「封をした家の印」とする
# 【文献】Johnson 1978・1982・Wright & Johnson 1975・Shin ほか 2020: 扱う量と決める単位が増えると、記録の道具が要る。Englund 2011: ウルク IV の粘土板は、数のしるしと物のしるしを分けて記す
#   (原楔形文字の約 85% は帳簿)。数のしるしが押したトークンから来たことは広く認められるが、物のしるしがトークンから来たかは弱い (Zimansky 1993・Michalowski 1993・Englund 1993。
#   Kelley ほか 2024 は、一部の物のしるしは印の絵から来たとする)
# 【文献】Ur, Karsgaard & Oates 2007・Ur ほか 2011: テル・ブラク LC2 (前 4,200〜3,900/3,800 年ごろ) は約 55 ha (まん中の丘と、まわりの小さな集まり)。集まりが内へ広がり、LC3〜4 に約 130 ha。
#   よそから移り住んだ人が加わったとする調べがある (歯の形の調べ。【文献・二次】)。Childe 1950: 町には食べ物をとらない専門の人がいる
# 【仮定】数: よその村は 3 つまで (最初の G6 の季節の終わりに必ず 1 つ来る)。来る見込み: 分かれた家 0.35・よその村 0.15 (信頼で変わる)。
#   よその村の人は 10〜25 人。交換している村から住みたい人が来る見込み 1 季節 0.15。苦しい年 1 年 0.2。値うち (草の種のつかみ): ヤギ 375・鎌 75・土器 40・黒曜石 40・干し肉 6。
#   1 人が運べるのは 20 kg ほど (草の種 900 つかみ)。覚えのずれ 0.05 × (家の数 + 返されていない貸し借り)、0.5 まで。
#   数え札 1 個 = 草の種 100 つかみ・ヤギ 1 頭・土器や鎌 10 個・働いた日 10 日。1 人 1 日に数え札 10 個 (板なら 50 個分)。
#   粘土の板が使えるようになるのは、数え札で記録した季節が 4 つ以上で、1 季節に数え札が 200 個以上要る季節があったとき。
#   町: 50 人以上 (ブラク LC2 の約 1/55〜1/110)、この 4 季節は毎季節交換し、相手の村が 2 つ以上、いちばん大きい相手の 2 倍以上、食べ物をとらない人が大人の 1 割以上
# 帳簿: 物が村や家に出入りする出来事には data の moves (家か「村」・+1 か −1・物と数・ヤギの番号) をつける。記録 (tools/build_records.py) が読むだけで、世界の進み方には使わない
G6_SALT = 41  # 41 を 31 で割った余り 10 は、前からの塩 3・7・11・23・29・31・37 の余り 3・7・11・23・29・0・6 と重ならない
ACTS_G6, ACT_RECORD = ["交換に行く"], "記録をつける"
G6_EVENTS = ("よその村", "交換", "貸し借り", "覚え", "印", "封", "記録", "確かめる", "町")  # お題と step.py で見せる (毎日の「交換に行く」「記録をつける」は入れない)
DIRS = {"南": ("川にそって南へ", (39, 79)), "北": ("川にそって北へ", (49, 0)), "東": ("東へ", (79, 40)), "西": ("西へ", (0, 40))}
MAX_STRANGERS, STRANGER_P, JOIN_P, JOIN_MIN, BAD_P = 3, 0.10, 0.15, 12, 0.2
CONTACT_P = {"分かれた家": 0.35, "よその村": 0.15}
USE_OBSIDIAN, OBS_BREAK = True, 0.5
VALUE = {"草の種": 1, "干し肉": 6, "ヤギ": 375, "土器": 40, "鎌": 75, "黒曜石": 40}
LOAD = {"草の種": 900, "土器": 4, "鎌": 10}  # 1 人が運べる量。持って行けるのは、ほかの村が受けとる物 (_g6_cap と同じ 3 つ) だけ
TRIP_WALK, TRIP_LOAD, TRIP_HURT, TRIP_LOSS = 30000, 1.4, 0.005, 0.03
SPREAD, SPREAD_MAX, BLAME = 0.05, 0.5, 1.25
TOKEN = {"草の種": 100, "干し肉": 16, "ヤギ": 1, "土器": 10, "鎌": 10, "黒曜石": 10, "日": 10}
RATE = {"数え札": 10, "封筒": 10, "板": 50}
WHATS = ("蓄え", "交換", "刈る")
WHAT_WORDS = {"蓄え": "村の蓄えへの家ごとの出し入れ", "交換": "ほかの村との交換と貸し借り", "刈る": "よその家の畑で刈った量"}
TABLET_SEASONS, TABLET_TOKENS, KEEPER_DAYS = 4, 200, 20
TOWN_POP, TOWN_RUN, TOWN_PARTNERS, CENTRE, NONFOOD = 50, 4, 2, 2, 0.10
GOOD_WORDS = (("黒曜石", "黒曜石"), ("黒い石", "黒曜石"), ("干し肉", "干し肉"), ("肉", "干し肉"), ("土器", "土器"), ("つぼ", "土器"), ("壺", "土器"),
              ("器", "土器"), ("鎌", "鎌"), ("ヤギ", "ヤギ"), ("山羊", "ヤギ"), ("草の種", "草の種"), ("麦", "草の種"), ("穀", "草の種"), ("種", "草の種"))
UNIT = {"草の種": "つかみ", "干し肉": "切れ", "ヤギ": "頭", "土器": "個", "鎌": "本", "黒曜石": "個"}
FOOD_KCAL = {"草の種": GRAIN, "干し肉": UNITS["干し肉"][1]}
NODE_KEY = {"ヤギ": "goats", "草の種": "grain", "土器": "pots", "鎌": "sickles", "黒曜石": "obsidian"}


def _g6(state):
    """G6 の状態 (G6 の最初の集まりで作る。start から数えるので、G6 の前のことは G6 の条件に数えない)"""
    e2 = state["era2"]
    if "g6" not in e2:
        e2["g6"] = {"start": state["day"], "seed": _rng(state, G6_SALT).getrandbits(31), "meets": [], "meet_first": None,
                    "others": [], "next_other": 1, "offers": [], "next_offer": 1, "debts": [], "next_debt": 1, "next_trip": 1,
                    "taken": {}, "moved": {}, "seals": {}, "store_sealed": None, "season_seals": {}, "opened": {}, "sealings": {}, "seal_seasons": 0,
                    "jobs": {}, "keep_days": {}, "trips": {}, "trip_log": [], "records": [], "cover": {}, "credit": {},
                    "open": {"印": state["day"], "数え札": None, "封筒": None, "板": None}, "token_seasons": 0, "big": 0,
                    "unchecked": 0, "misremember": 0, "checked": {"数え札": 0, "封筒": 0, "板": 0},
                    "exchanges": 0, "joined": 0, "obsidian": 0, "obs_sickles": 0, "nonfood": [], "shown": None,
                    "town_seen": None, "town_low": 0, "log": [], "end": None, "next_name": 0}
    return e2["g6"]


def _g6_r(state, k):
    """集まりと 30 日のあいだの G6 の乱数 (季節の終わりに塩 41 から引いた seed から作る。前からの乱数の列には足さない)"""
    return random.Random(state["era2"]["g6"]["seed"] * 1000003 + state["day"] * 1009 + k)


def _other(state, oid):
    return next((o for o in (state["era2"].get("g6") or {}).get("others", []) if o["id"] == oid), None)


def _okey(o):
    return f"{o['name']} ({o['way']}歩いて {o['days']} 日)"


def _gw(goods):
    """{"ヤギ": 2, "土器": 18} → 「ヤギ 2 頭・土器 18 個」"""
    return "・".join(f"{k} {n} {UNIT[k]}" for k, n in goods.items() if n > 0) or "なし"


def _mv(side, sign, goods, ids=()):
    """帳簿のための物の出し入れ 1 つ (出来事の data の moves。記録が読むだけ): [家か「村」, +1 か −1, 物と数, ヤギの [番号, オスかメスか, 生まれた日]]"""
    return [side, sign, {k: n for k, n in goods.items() if n > 0}, list(ids)]


def _g6_spread(state):
    """覚えのずれ (家が多いほど、返されていない貸し借りが多いほど大きい)"""
    g = state["era2"].get("g6") or {}
    return min(SPREAD_MAX, SPREAD * (len(_homes(state)) + sum(1 for d in g.get("debts", []) if d["status"] == "まだ")))


def _g6_cover(state, what):
    """この季節の記録 (全部残せたもの) の道具。なければ None"""
    return ((state["era2"].get("g6") or {}).get("cover") or {}).get(what)


# ---- ほかの村 (地図の外。Claude は演じない。決まりで動く) ----

def _new_other(state, rng, kind, household=None, people=None, goats=0, grain=0):
    g = _g6(state)
    used = {o["dir"] for o in g["others"]}
    d = rng.choice([x for x in DIRS if x not in used] or list(DIRS))
    strangers = [o for o in g["others"] if o["kind"] == "よその村"]
    obs = USE_OBSIDIAN and kind == "よその村" and len(strangers) == 1  # 2 つ目のよその村 (歩いて 2 日) は黒曜石を持つ【仮定】
    days = 1 if kind == "分かれた家" or not strangers else 2 if obs else rng.choice([1, 2])
    name = (household[:-2] if household.endswith("の家") else household) + "の村" if kind == "分かれた家" else f"{d}の村"
    if any(o["name"] == name for o in g["others"]):
        name = f"{name}{g['next_other']}"
    n = people if people is not None else rng.randint(10, 25)
    far = kind == "よその村"
    o = {"id": f"N{g['next_other']}", "name": name, "kind": kind, "household": household, "dir": d, "way": DIRS[d][0], "days": days,
         "edge": list(DIRS[d][1]), "since": state["day"], "known": None, "people": n,
         "goats": round(n * 0.4) if far else goats, "grain": n * 100 if far else grain, "pots": n // 4 if far else 0,
         "sickles": n // 8 if far else 0, "obsidian": 20 if obs else 0, "has_obsidian": obs, "bad": None, "trust": 0.5, "contacts": []}
    g["next_other"] += 1
    g["others"].append(o)
    return o


def _g6_cap(o):
    """ほかの村が 1 季節に受けとる物の上限【仮定】(土器は 3 人に 1 個 (3 個から)、鎌は 6 人に 1 本 (1 本から)、草の種は 1 人 10 つかみ。苦しい年は 100 つかみ)"""
    return {"土器": max(3, o["people"] // 3), "鎌": max(1, o["people"] // 6), "草の種": o["people"] * (100 if o["bad"] is not None else 10)}


def _g6_wants(state, o):
    t = _g6(state)["taken"].get(o["id"], {})
    return {k: max(0, n - t.get(k, 0)) for k, n in _g6_cap(o).items()}


def _g6_supply(o):
    """ほかの村が出せる物 (ヤギは 2 頭残す。草の種は苦しい年でなく、1 人 100 つかみより多い分)"""
    return {"ヤギ": max(0, o["goats"] - 2), "黒曜石": o["obsidian"],
            "草の種": max(0, o["grain"] - o["people"] * 100) if o["bad"] is None else 0}


def _node_add(o, goods, sign):
    for k, n in goods.items():
        if NODE_KEY.get(k):
            o[NODE_KEY[k]] = max(0, o[NODE_KEY[k]] + sign * n)


def _g6_pay(o, value, want, skip=()):
    """ほかの村が value (草の種のつかみ) を払う: want の物から、なければほかの物で。戻り値: 払う物、払いきれない値うち
    (skip: 受けとったのと同じ物では払わない。2026-10-09 作るときの試しで、草の種を渡して同じ量の草の種を受けとる交換が出たため)"""
    sup, pay = _g6_supply(o), {}
    for k in [x for x in [want] + [x for x in ("ヤギ", "黒曜石", "草の種") if x != want] if x not in skip]:
        n = min(sup.get(k, 0), int(value // VALUE[k]))
        if n > 0:
            pay[k] = n
            value -= n * VALUE[k]
    return pay, value


def _g6_note(state, o, took, moved=()):
    g = _g6(state)
    t = g["taken"].setdefault(o["id"], {})
    for k, n in took.items():
        t[k] = t.get(k, 0) + n
    for goods in (took,) + tuple(moved):
        for k, n in goods.items():
            g["moved"][k] = g["moved"].get(k, 0) + n


def _g6_contact(state, o):
    """交換・貸し借り・返すが 1 つ済んだ (この季節に交換した村として数える)"""
    g, sd = _g6(state), state["era2"]["step_day"]
    if sd not in o["contacts"]:
        o["contacts"].append(sd)
    g["exchanges"] += 1
    o["trust"] = min(1.0, round(o["trust"] + 0.1, 2))


# ---- 村の物・家の物 ----

def _g6_have(state, side, k):
    e2 = state["era2"]
    if side == "村":
        if k in FOOD_KCAL:
            return int(sum(f["kcal"] for f in state["store"] if f["kind"] == k) // FOOD_KCAL[k])
        if k == "ヤギ":
            return max(0, sum(1 for x in e2["goats"] if x.get("owner") is None) - 2)  # 村のヤギは 2 頭残す
        return {"土器": e2.get("pots", 0), "鎌": e2.get("sickles", 0), "黒曜石": _g6(state)["obsidian"]}.get(k, 0)
    if k in FOOD_KCAL:
        return int(sum(f["kcal"] for f in _house(state, side)["store"] if f["kind"] == k) // FOOD_KCAL[k])
    return sum(1 for x in e2["goats"] if x.get("owner") == side) if k == "ヤギ" else 0


def _g6_take(state, side, goods, ids=None):
    """side (「村」か家の名前) の物を出す (足りなければある分だけ)。戻り値: 出した物 (ids があれば、出したヤギの [番号, オスかメスか, 生まれた日] を足す。帳簿のため)"""
    e2, out = state["era2"], {}
    for k, n in goods.items():
        n = min(n, _g6_have(state, side, k))
        if n <= 0:
            continue
        if k in FOOD_KCAL:
            _move_food(state["store"] if side == "村" else _house(state, side)["store"], [], k, n * FOOD_KCAL[k])
        elif k == "ヤギ":
            mine = [x for x in e2["goats"] if x.get("owner") == (None if side == "村" else side)]
            for x in sorted(mine, key=lambda x: (x["sex"] != "オス", x["born"]))[:n]:  # オスの、年上から
                e2["goats"].remove(x)
                if ids is not None:
                    ids.append([x["id"], x["sex"], x["born"]])
        elif k == "黒曜石":
            _g6(state)["obsidian"] -= n
        else:
            e2["pots" if k == "土器" else "sickles"] -= n
            if k == "鎌":  # 黒曜石の刃の鎌の数は、村の鎌の数をこえない
                _g6(state)["obs_sickles"] = min(_g6(state)["obs_sickles"], e2["sickles"])
        out[k] = n
    return out


def _g6_put(state, side, goods, goats_in=(), ids=None):
    """side に物を入れる (土器・鎌・黒曜石は、いつも村の物)。戻り値: 入れた先 (家がもうなければ「村」)。ids があれば、入れたヤギの [番号, オスかメスか, 生まれた日] を足す"""
    e2, day, gi = state["era2"], state["day"], list(goats_in)
    if side != "村" and side not in _homes(state):
        side = "村"  # 家がもうない (村を出た) ときは村へ
    for k, n in goods.items():
        if n <= 0:
            continue
        if k in FOOD_KCAL:
            (state["store"] if side == "村" else _house(state, side)["store"]).append({"kind": k, "kcal": n * FOOD_KCAL[k], "day": day})
        elif k == "ヤギ":
            for i in range(n):
                x = gi[i] if i < len(gi) else {"sex": "メス", "age": 2}
                e2["goats"].append({"id": e2["next_goat"], "sex": x["sex"], "born": day - x["age"] * YEAR, "owner": None if side == "村" else side})
                if ids is not None:
                    ids.append([e2["next_goat"], x["sex"], day - x["age"] * YEAR])
                e2["next_goat"] += 1
        elif k == "黒曜石":
            _g6(state)["obsidian"] += n
        else:
            key = "pots" if k == "土器" else "sickles"
            e2[key] = e2.get(key, 0) + n
    return side


# ---- 季節の終わりに、ほかの村の人が来る (申し出) ----

def _g6_offer_new(state, rng, o, first):
    g, day, s = _g6(state), state["day"], _g6_spread(state)
    head = (f"前に村を出た{o['household']}の人たちが、村に来た。いまは {_okey(o)} で暮らしているという" if first and o["kind"] == "分かれた家"
            else f"{_okey(o)} の人たちが、交換をもとめて村に来た" if first else f"{_okey(o)} の人たちが、また村に来た")
    due = next((d for d in g["debts"] if d["other"] == o["id"] and d["status"] == "まだ" and d["due"] <= day + 1), None)
    off, what = None, ""
    bring = None
    if due:
        exact = due.get("proof") in ("封筒", "板")
        bring = {k: min(n if exact else int(n * rng.uniform(1 - s, 1)), o[NODE_KEY[k]] if NODE_KEY.get(k) else n) for k, n in due["goods"].items()}
        if sum(VALUE[k] * n for k, n in bring.items()) * 2 < sum(VALUE[k] * n for k, n in due["goods"].items()):
            bring = None  # 半分も返せないときは、まだ返しに来ない
    if o["bad"] is not None and o["grain"] < o["people"] * 60:
        n = min(3000, max(100, round(o["people"] * 120, -2)))
        off = {"kind": "貸して", "give": {}, "want": {"草の種": n}}
        what = f"この年は畑が実らず苦しいので、草の種 {n} つかみ を貸してほしい、1 年のうちに同じ量を返す、と言った"
    elif bring:
        off = {"kind": "返す", "debt": due["id"], "give": bring, "want": {}}
        what = f"[{due['id']}] の分として、{_gw(bring)} を返しに来た"
    else:
        sup, wants = _g6_supply(o), _g6_wants(state, o)
        cap = sum(VALUE[k] * n for k, n in wants.items())
        # ほしい物がヤギ半頭分 (草の種 約 190 つかみ) 以上あれば、ヤギ 1 頭を出す (12 人より小さい村は、ほしい物がヤギ 1 頭分に届かないため。2026-10-09 確かめ役)
        good = "ヤギ" if sup["ヤギ"] >= 1 and cap >= VALUE["ヤギ"] / 2 else "黒曜石" if sup["黒曜石"] >= 5 and cap >= 5 * VALUE["黒曜石"] else None
        if good:
            k = max(1, min(3, sup["ヤギ"], int(cap // VALUE["ヤギ"]))) if good == "ヤギ" else min(15, sup["黒曜石"], int(cap // VALUE["黒曜石"]))
            ask, left = {}, k * VALUE[good]
            for w in ("土器", "鎌", "草の種"):
                m = min(wants.get(w, 0), int(left // VALUE[w]))
                if m > 0:
                    ask[w], left = m, left - m * VALUE[w]
            off = {"kind": "交換", "give": {good: k}, "want": ask}
            what = f"{_gw(off['give'])} を出すので、{_gw(ask)} がほしいと言った"
    if not off:
        log(state, "よその村", None, f"{head}。交換できる物がなく、帰っていった", other=o["id"])
        return
    off.update(id=f"T{g['next_offer']}", other=o["id"], day=day,
               goats_in=[{"sex": "メス" if rng.random() < 0.5 else "オス", "age": rng.randint(1, 4)} for _ in range(off["give"].get("ヤギ", 0))],
               mem={"village": round(rng.uniform(1, 1 + s), 3), "other": round(rng.uniform(1 - s, 1), 3)})
    g["next_offer"] += 1
    g["offers"].append(off)
    log(state, "よその村", None, f"{head}。{what} [{off['id']}]", other=o["id"], offer=off["id"])


# ---- 季節の集まり (G6): 答えを読む・決める ----

def _tid(k):
    m = re.search(r"\d+", str(k or ""))
    return f"T{int(m.group())}" if m else ""


def _g6_side(v):
    """申し出の答え: "村" / "家" / False (受けない) / None (読めない。お題の「...」)"""
    if v is True:
        return "村"
    if v is False:
        return False
    s = str(v or "").strip()
    if s.lower() in ("false", "no") or any(w in s for w in ("受けない", "しない", "断", "ことわ", "いらない")):
        return False
    vil, home = "村" in s, "家" in s
    return "村" if vil and not home else "家" if home and not vil else None


def _g6_good(v):
    s = str(v or "")
    return next((g for w, g in GOOD_WORDS if w in s), None)


def _g6_goods(d):
    out = {}
    for k, v in (d.items() if isinstance(d, dict) else []):
        good, n = _g6_good(k), _num(v)
        if good and n > 0:
            out[good] = out.get(good, 0) + n
    return out


def _g6_node(state, v):
    """行き先: 「N1」か、知っている村の名前 (まわりに字があってもよい)"""
    s = str(v or "")
    known = [o for o in (state["era2"].get("g6") or {}).get("others", []) if o["known"] is not None]
    m = re.search(r"[NnＮ]\s*(\d+)", s)
    if m:
        return next((o["id"] for o in known if o["id"] == f"N{int(m.group(1))}"), None)
    hit = [o for o in known if o["name"] in s]
    return max(hit, key=lambda o: len(o["name"]))["id"] if hit else None


def _g6_new_season(state):
    """季節の集まりのはじめ (G6): この季節の仕事の答えなどを空にする"""
    g = _g6(state)
    g["meets"].append(state["era2"]["step_day"])
    g["meet_first"] = state["next_event"]
    g["jobs"], g["keep_days"], g["trips"] = {}, {}, {}


def _g6_job(state, q, job, own):
    """交換に行く・記録をつける の、くわしい答え (e2["jobs"] には入れない)"""
    g = _g6(state)
    act = q["plan"]["activity"]
    if act == "交換に行く":
        then = job.get("then")
        then = then.get("activity") if isinstance(then, dict) else then
        g["jobs"][q["name"]] = {"activity": act, "to": _g6_node(state, job.get("to")), "carry": _g6_goods(job.get("carry")),
                                "want": _g6_good(job.get("want")) or "ヤギ",
                                "then": then if then in acts2(state) and then not in ACTS_G6 + [ACT_RECORD] else "休む",
                                "house": bool(own and _yes(job.get("house")))}
    elif act == ACT_RECORD:
        w = job.get("what")
        w = [w] if isinstance(w, str) else w if isinstance(w, list) else []
        what = []
        for y in w:
            what += [x for x in WHATS if x in str(y) and x not in what]
        how = next((h for h in ("板", "封筒", "数え札") if h in str(job.get("how") or "") and g["open"].get(h)), "数え札")
        g["jobs"][q["name"]] = {"activity": act, "what": what or list(WHATS), "how": how}


def _g6_collect(state, c, p, a, fam, own):
    """季節の答えから、申し出 (trade)・家の印 (seal)・村の蓄えの封 (seal_store) を集める (代表の答えは家族の大人みんなの答え)"""
    names = {q["name"] for q in fam}
    tr = a.get("trade")
    for k, v in (tr.items() if isinstance(tr, dict) else []):
        tid, side = _tid(k), _g6_side(v)
        if not tid or side is None or (side == "家" and not own):
            continue
        c["trade"].setdefault(tid, {}).setdefault(side, set()).update(names)
        c["trade_by"].setdefault(tid, {})[p["name"]] = side
        if side == "家" and p.get("household"):
            c["house"].setdefault(tid, []).append(p["household"])
    if own and p.get("household") and _yes(a.get("seal")):
        c["seal"].setdefault(p["household"], p["name"])
    if _yes(a.get("seal_store")):
        c["store"] |= names
        c["store_by"].add(p["name"])


def _g6_meeting(state, c, n):
    """季節の集まり (G6。G5 の集まりのあと、よそから来た人の受け入れの前): 家の印 → 村の蓄えの封 → 申し出"""
    e2, g = state["era2"], _g6(state)
    lead, homes = _leader(state), _homes(state)
    for h, who in sorted(c["seal"].items()):
        if h in homes and h not in g["seals"]:
            g["seals"][h] = {"day": e2["step_day"], "by": who}
            log(state, "印", who, f"{h}の代表の {who} が、家の印 (焼いた粘土に形を刻んだもの) を作った。これから{h}の倉の口は、粘土でふさいで{h}の印を押しておく",
                household=h)
    if len(c["store"]) * 2 > n or (lead and lead in c["store_by"]):
        g["store_sealed"] = e2["step_day"]
        alone = len(c["store"]) * 2 <= n
        log(state, "封", lead if alone else None, (f"まとめ役の {lead} が決めて、" if alone else "")
            + "この季節は、村の蓄えの土器の口を粘土でふさぐことになった。取るときは封を割り、取った人の家の印を押した粘土で封をし直す。割った封のかけらは取っておく")
    for off in g["offers"]:
        o = _other(state, off["other"])
        if o:
            _g6_decide(state, c, off, o, n, lead)
    g["offers"] = []


def _g6_decide(state, c, off, o, n, lead):
    g = _g6(state)
    if off["kind"] == "返す":
        _g6_repay(state, off, o)
        return
    tally = {k: len(v) for k, v in c["trade"].get(off["id"], {}).items()}
    if tally.get("村", 0) * 2 > n or (lead and c["trade_by"].get(off["id"], {}).get(lead) == "村"):
        side = "村"
    else:
        cands = [h for h in c["house"].get(off["id"], []) if all(_g6_have(state, h, k) >= m for k, m in off["want"].items())]
        side = max(sorted(cands), key=lambda h: sum(f["kcal"] for f in _house(state, h)["store"])) if cands else None
    votes = f"村 {tally.get('村', 0)}・家 {tally.get('家', 0)}・受けない {tally.get(False, 0)} / 大人 {n}"
    if side is None:
        o["trust"] = max(0.0, round(o["trust"] - 0.1, 2))
        log(state, "よその村", None, f"季節の集まりで、{o['name']} の申し出 [{off['id']}] は受けなかった ({votes})", other=o["id"], offer=off["id"])
        return
    if any(_g6_have(state, side, k) < m for k, m in off["want"].items()):
        log(state, "交換", None, f"季節の集まりで、{o['name']} の申し出 [{off['id']}] を{side}の物で受けようとしたが、{_gw(off['want'])} がなかった",
            other=o["id"], offer=off["id"])
        return
    out_ids = []
    gave = _g6_take(state, side, off["want"], out_ids)
    _node_add(o, gave, 1)
    who = "村は、村の物で" if side == "村" else f"{side}が、家の物で"
    if off["kind"] == "貸して":
        d = {"id": f"D{g['next_debt']}", "other": o["id"], "lender": side, "goods": gave, "day": state["day"], "due": state["day"] + YEAR,
             "proof": None, "mem": off["mem"], "status": "まだ", "end": None}
        g["next_debt"] += 1
        g["debts"].append(d)
        _g6_note(state, o, {}, (gave,))
        _g6_contact(state, o)
        log(state, "貸し借り", None, f"季節の集まりで、{who} {o['name']} に {_gw(gave)} を貸した [{d['id']}] (1 年のうちに同じ量を返すと言った。{votes})",
            other=o["id"], debt=d["id"], moves=[_mv(side, -1, gave, out_ids)])
        return
    _node_add(o, off["give"], -1)
    in_ids = []
    to = _g6_put(state, side, off["give"], off["goats_in"], in_ids)
    _g6_note(state, o, gave, (off["give"],))
    _g6_contact(state, o)
    sx = (" (" + "・".join(f"{x['sex']} {x['age']} 歳" for x in off["goats_in"]) + ")") if off["goats_in"] else ""
    log(state, "交換", None, f"季節の集まりで、{who} {o['name']} の申し出 [{off['id']}] を受け、{_gw(gave)} を {_gw(off['give'])}{sx} と取り替えた ({votes})",
        other=o["id"], offer=off["id"], moves=[_mv(side, -1, gave, out_ids), _mv(to, 1, off["give"], in_ids)], **({"household": side} if side != "村" else {}))


def _g6_repay(state, off, o):
    """ほかの村が貸し借りを返しに来た (集まりで決めずに受けとる)。封筒・板の記録があれば、約束した数を両方で確かめる"""
    g, day = _g6(state), state["day"]
    d = next((x for x in g["debts"] if x["id"] == off["debt"] and x["status"] == "まだ"), None)
    if not d:
        return
    bring = {k: min(n, o[NODE_KEY[k]]) if NODE_KEY.get(k) else n for k, n in off["give"].items()}
    _node_add(o, bring, -1)
    in_ids = []
    side = _g6_put(state, d["lender"], bring, (), in_ids)
    mv = [_mv(side, 1, bring, in_ids)]
    _g6_note(state, o, {}, (bring,))
    _g6_contact(state, o)
    true = d["goods"]
    short = {k: n - bring.get(k, 0) for k, n in true.items() if n - bring.get(k, 0) > 0}
    to = "村" if d["lender"] == "村" else d["lender"]
    # 足りない分が草の種 50 つかみ分より少なければ、返さなくてよいことにする (交換に行ったときの「あとで返す」と同じ目安。2026-10-09 試し回し:
    #   数え札の記録では、向こうは覚えで持って来るので、草の種 1 つかみのような残りが季節ごとに続き、最後は「返されないまま」になっていた)
    small = bool(short) and sum(VALUE[k] * n for k, n in short.items()) < 50
    if d.get("proof") in ("封筒", "板", "数え札"):
        g["checked"][d["proof"]] += 1
        if short and not small:
            d["goods"] = short
        else:
            d.update(status="返した", end=day)
        how = "封筒を割って" if d["proof"] == "封筒" else f"{d['proof']}の記録を見て"
        log(state, "確かめる", None, f"{o['name']} の人が [{d['id']}] を返しに来た。{how}、貸した数 ({_gw(true)}) を確かめ、{to}は {_gw(bring)} を受けとった"
            + (f"。足りない {_gw(short)} は、わずかなので、返さなくてよいことになった" if small
               else f"。足りない {_gw(short)} は、あとで返すことになった" if short else ""), other=o["id"], debt=d["id"], how=d["proof"], moves=mv)
        return
    g["unchecked"] += 1  # 記録のない量を、覚えで決めた
    d.update(status="返した", end=day)
    mem = {k: math.ceil(n * d["mem"]["village"]) for k, n in true.items()}
    if any(mem[k] > bring.get(k, 0) * BLAME for k in mem):
        g["misremember"] += 1
        o["trust"] = max(0.0, round(o["trust"] - 0.2, 2))
        log(state, "覚え", None, f"{o['name']} の人は、[{d['id']}] の分として {_gw(bring)} を返した。{to}の覚えでは {_gw(mem)} を貸したはずだった (記録はない)",
            other=o["id"], debt=d["id"], moves=mv)
    else:
        log(state, "貸し借り", None, f"{o['name']} の人が、[{d['id']}] の分として {_gw(bring)} を返した ({to}が受けとった。記録はなく、量は覚えで決めた)",
            other=o["id"], debt=d["id"], moves=mv)


# ---- 30 日のあいだ: 交換に行く・記録をつける・封 ----

def _g6_then(p, j):
    p["plan"] = {"activity": j["then"], "place": "camp", "with": []}


def _g6_trips_day(state):
    """交換に行く (G6。毎日、仕事の計算のあと・食べる前): 出かける → 歩く → 向こうの村で交換 → 歩く → 帰る"""
    e2, g, day = state["era2"], _g6(state), state["day"]
    for p in adults(state):
        j = g["jobs"].get(p["name"])
        if not j and (p.get("plan") or {}).get("activity") == "交換に行く":  # 答えがなく、前の季節の「交換に行く」のまま (行き先が分からない)
            j = {"activity": "交換に行く", "to": None, "carry": {}, "want": "ヤギ", "then": "休む", "house": False}
        if not j or j["activity"] != "交換に行く":
            continue
        t = p.get("today") or {}
        tr = g["trips"].get(p["name"])
        if tr is None:
            if day != e2["step_day"]:
                continue
            tr = g["trips"][p["name"]] = _g6_depart(state, p, t, j)
        if tr["state"] != "行く":
            continue
        o, k = _other(state, tr["to"]), day - tr["start"]
        t["away"] = True
        if k != tr["days"]:
            t["spent"] = round(t.get("spent", BASE_KCAL) + world._walk_kcal(p, TRIP_WALK) * TRIP_LOAD)
        if k == tr["days"]:
            _g6_barter(state, p, t, tr, o)
        elif k == 2 * tr["days"]:
            _g6_return(state, p, t, tr, o, j)
        elif k > 0:
            t.setdefault("events", []).append(log(state, "交換に行く", p["name"], f"{p['name']} が、{o['name']} {'への' if k < tr['days'] else 'からの帰り'}道を歩いた",
                                                  other=o["id"], trip=tr["id"]))


def _g6_depart(state, p, t, j):
    g = _g6(state)
    o = _other(state, j["to"]) if j.get("to") else None
    side = p["household"] if j["house"] and p.get("household") in _homes_built(state) else "村"
    carry = {k: n for k, n in j["carry"].items() if k in LOAD}  # ほかの村が受けとる物 (_g6_cap) だけを持って行く (ヤギ・干し肉・黒曜石は受けとらないので持って行かない)
    load = sum(n / LOAD[k] for k, n in carry.items())
    if load > 1:
        carry = {k: int(n / load) for k, n in carry.items()}
    ok = o is not None and t.get("activity") == "交換に行く"
    took = _g6_take(state, side, carry) if ok else {}
    why = "行き先の村が分からず" if not o else "けがをしていて" if not ok else "持って行ける物がなく" if not took else None
    if why:
        _g6_then(p, j)
        t.setdefault("events", []).append(log(state, "交換に行く", p["name"], f"{p['name']} は、{why}、交換に行かなかった"))
        return {"state": "行かなかった"}
    tr = {"id": f"R{g['next_trip']}", "who": p["name"], "to": o["id"], "start": state["day"], "days": o["days"], "side": side,
          "took": took, "want": j["want"], "got": {}, "back": {}, "goats_in": [], "debt": None, "state": "行く"}
    g["next_trip"] += 1
    t.setdefault("events", []).append(log(state, "交換に行く", p["name"], f"{p['name']} が、{'村' if side == '村' else side}の {_gw(took)} を持って、"
                                          f"{_okey(o)} へ交換に行った", other=o["id"], trip=tr["id"], moves=[_mv(side, -1, took)]))
    return tr


def _g6_barter(state, p, t, tr, o):
    """向こうの村で: ほしい分だけ受けとり、want の物 (なければほかの物) で払う。払いきれない分は、あとで返す約束"""
    g = _g6(state)
    tr["bartered"] = True  # 季節の終わりに、まだ帰っていないときの持ち帰り方を分ける
    wants = _g6_wants(state, o)
    took = {k: min(n, wants.get(k, 0)) for k, n in tr["took"].items()}
    took = {k: n for k, n in took.items() if n > 0}
    tr["back"] = {k: n - took.get(k, 0) for k, n in tr["took"].items() if n - took.get(k, 0) > 0}
    if not took:
        t.setdefault("events", []).append(log(state, "交換", p["name"], f"{p['name']} は {o['name']} で {_gw(tr['took'])} を見せたが、"
                                              "この季節はもう足りていると言われ、交換できなかった", other=o["id"], trip=tr["id"]))
        return
    pay, left = _g6_pay(o, sum(VALUE[k] * n for k, n in took.items()), tr["want"], skip=set(took))
    _node_add(o, took, 1)
    _node_add(o, pay, -1)
    r = _g6_r(state, 200 + int(tr["id"][1:]))
    tr["got"] = pay
    tr["goats_in"] = [{"sex": "メス" if r.random() < 0.5 else "オス", "age": r.randint(1, 4)} for _ in range(pay.get("ヤギ", 0))]
    owe = ""
    if left >= 50:
        # その村が出せる物でだけ約束する (ヤギは 2 頭残すので、2 頭より多く飼う村だけ。2026-10-09 試し回し: ヤギのいない分かれた家の村が、ヤギ 1 頭を返すと約束していた)
        can = (tr["want"] == "ヤギ" and o["goats"] > 2) or (tr["want"] == "黒曜石" and o["has_obsidian"])
        k = tr["want"] if can and left >= VALUE[tr["want"]] / 2 else "草の種"
        s = _g6_spread(state)
        d = {"id": f"D{g['next_debt']}", "other": o["id"], "lender": tr["side"], "goods": {k: max(1, round(left / VALUE[k]))}, "day": state["day"],
             "due": state["day"] + 2 * SEASON_DAYS, "proof": None,
             "mem": {"village": round(r.uniform(1, 1 + s), 3), "other": round(r.uniform(1 - s, 1), 3)}, "status": "まだ", "end": None}
        g["next_debt"] += 1
        g["debts"].append(d)
        tr["debt"] = d["id"]
        owe = (f"。足りない分の {_gw(d['goods'])} は、あとで返すと言った [{d['id']}]" if pay  # 何も払えなかったときは「足りない分」と書かない (2026-10-09 試し回し)
               else f"。{o['name']} は、いま払える物がなく、{_gw(d['goods'])} をあとで返すと言った [{d['id']}]")
    _g6_note(state, o, took, (pay,))
    _g6_contact(state, o)
    t.setdefault("events", []).append(log(state, "交換", p["name"], f"{p['name']} は {o['name']} で、{_gw(took)} を渡し"
                                          + (f"、{_gw(pay)} を受けとった" if pay else "た") + owe
                                          + (f" (受けとってもらえなかった {_gw(tr['back'])} は持ち帰る)" if tr["back"] else ""), other=o["id"], trip=tr["id"]))


def _g6_home(*goods):
    """持ち帰った物の文: 受けとった物と、受けとってもらえなかった物を合わせて書く (何もなければ「何も持ち帰らなかった」)
    (2026-10-09 試し回し: 受けとってもらえなかった物だけを持ち帰ったとき「なし を持ち帰った」と出ていた)"""
    both = {}
    for x in goods:
        for k, n in x.items():
            both[k] = both.get(k, 0) + n
    return f"{_gw(both)} を持ち帰った" if any(n > 0 for n in both.values()) else "何も持ち帰らなかった"


def _g6_return(state, p, t, tr, o, j):
    r = _g6_r(state, 300 + int(tr["id"][1:]))
    got, lost, hurt = dict(tr["got"]), "", ""
    if r.random() < TRIP_LOSS:
        if got.get("ヤギ"):
            got["ヤギ"] -= 1
            lost = "。帰り道でヤギ 1 頭がはぐれていなくなった"
        elif got.get("草の種"):
            m = max(1, got["草の種"] // 10)
            got["草の種"] -= m
            lost = f"。帰り道で草の種 {m} つかみ をこぼして失った"
    if r.random() < TRIP_HURT * 2 * tr["days"]:
        p["injured"] = 2
        hurt = "。帰り道でけがをした"
    ids = []
    side = _g6_put(state, tr["side"], got, tr["goats_in"], ids)
    _g6_put(state, tr["side"], tr["back"])
    tr.update(state="帰った", end=state["day"], got=got)
    _g6(state)["trip_log"].append(dict(tr))
    _g6_then(p, j)
    t.setdefault("events", []).append(log(state, "交換に行く", p["name"], f"{p['name']} が {o['name']} から帰った ({_g6_home(got, tr['back'])}{lost}{hurt})",
                                          other=o["id"], trip=tr["id"], moves=[_mv(side, 1, got, ids), _mv(side, 1, tr["back"])]))


def _g6_keep_day(state, p, t):
    """記録をつける (1 日)"""
    g = _g6(state)
    j = g["jobs"].get(p["name"]) or {"what": list(WHATS), "how": "数え札"}
    g["keep_days"][p["name"]] = g["keep_days"].get(p["name"], 0) + 1
    w = "・".join(WHAT_WORDS[x] for x in j["what"])
    txt = {"数え札": f"粘土の数え札を作り、{w} を数えた", "封筒": f"粘土の数え札を作って {w} を数え、貸し借りの分は粘土の玉 (封筒) に入れて印を押した",
           "板": f"粘土の板に、物のしるしと数のしるしを分けて押し、{w} を記した"}[j["how"]]
    t.setdefault("events", []).append(log(state, "記録をつける", p["name"], f"{p['name']} がキャンプで、{txt}"))


def _g6_opened(state, p, where):
    """封のかけら: 印で封をした村の蓄え (この季節) か家の倉を、家の人が開けた (1 つの家で 1 日 1 回まで)"""
    g, h = state["era2"].get("g6"), p.get("household")
    if not g or not h:
        return
    if where == "蓄え" and g["store_sealed"] != state["era2"].get("step_day"):
        return
    if where == "倉" and h not in g["seals"]:
        return
    if g["opened"].get(f"{where}:{h}") == state["day"]:
        return
    g["opened"][f"{where}:{h}"] = state["day"]
    key = h if h in g["seals"] else "(印なし)"
    g["season_seals"][key] = g["season_seals"].get(key, 0) + 1


def _g6_obsidian_blades(state, n):
    """道具づくり (G6): 村に黒曜石があれば、鎌に黒曜石の刃をはめる (1 本に 1 個)"""
    g = state["era2"].get("g6")
    if not g or not USE_OBSIDIAN:
        return 0
    use = min(n, g["obsidian"])
    g["obsidian"] -= use
    g["obs_sickles"] += use
    return use


# ---- もめごと (G5 の仕組みに、G6 の覚えと記録を足す) ----

def _g6_claim(state, d):
    """G6 のもめごとの量: 記録 (数え札・板を全部残せた) があれば正しい量。なければ、言い出した家の覚え (多めのことがある)"""
    how = _g6_cover(state, d["kind"]) if d["kind"] in ("蓄え", "刈る") else None
    if how:
        d["record"] = how
        return f"。{how}の記録がある"
    if d["kind"] not in ("蓄え", "刈る", "倉", "覚え"):
        return ""  # ヤギに荒らされた畑は、見ればわかる
    r, s = _g6_r(state, 1000 + int(d["id"][1:])), _g6_spread(state)
    d["harm_true"], d["mem"] = d["harm"], round(r.uniform(1 - s, 1), 3)
    d["harm"] = max(1, round(d["harm"] * r.uniform(1, 1 + s)))
    return "。言い出した家の覚えで、記録はない"


def _g6_check(state, d):
    """記録のあるもめごとを、季節の集まりで確かめた (一度だけ数える)"""
    if d.get("checked"):
        return
    g = _g6(state)
    d["checked"] = state["day"]
    g["checked"][d["record"]] += 1
    log(state, "確かめる", None, f"季節の集まりで、もめごと [{d['id']}] の量を、{d['record']}の記録で確かめた (草の種にして {d['harm']} つかみ 分)",
        dispute=d["id"], how=d["record"])


def _g6_after_pay(state, d, paid):
    """覚えで払ったあと: 払った家の覚えより多く払ったと思えば、覚え違いのもめごとのもと"""
    if d.get("record") or "harm_true" not in d or paid <= 0 or d["kind"] == "覚え":
        return
    g = _g6(state)
    g["unchecked"] += 1
    mine = d["harm_true"] * d["mem"]
    if paid > mine * BLAME:
        g["misremember"] += 1
        what = (f"{d['against']}は、もめごと [{d['id']}] で{d['from']}に草の種にして 約 {paid} つかみ 分を払ったが、"
                f"{d['against']}の覚えでは 約 {round(mine)} つかみ 分だった (記録はない)")
        eid = log(state, "覚え", None, what, dispute=d["id"])
        _incident(state, "覚え", d["against"], d["from"], (paid - mine) * GRAIN, what, eid)


def _g6_credit(state, flow):
    """配給の記録 (G6): 村の蓄えの記録を全部残せた季節は、作る・記録をつける・交換に行った日を、1 日 = 大人 1 人の 1 日分として「入れた」に数える"""
    cr = (state["era2"].get("g6") or {}).get("credit") or {}
    return {h: [v[0] + cr.get(h, 0) * DAY_FOOD, v[1], v[2]] for h, v in flow.items()}


def _g6_workdays(state):
    e2, g, days = state["era2"], _g6(state), {}
    rows = list(e2.get("craft_days", {}).items()) + list(g["keep_days"].items())
    rows += [(tr["who"], 2 * tr["days"] + 1) for tr in g["trips"].values() if tr.get("start") is not None]
    for n, d in rows:
        q = next((q for q in state["people"] if q["name"] == n), None)
        if q and q.get("household"):
            days[q["household"]] = days.get(q["household"], 0) + d
    return days


# ---- 季節の終わり (G6) ----

def _g6_records(state, frac):
    """この季節の記録 (G5 のもめごとを決める前。どの量に記録があるかを決める)"""
    e2, g, g5 = state["era2"], _g6(state), state["era2"].get("g5") or {}
    g["cover"], g["credit"] = {}, {}
    keep = {n: d for n, d in sorted(g["keep_days"].items()) if d > 0}
    if not keep:
        return
    homes = _homes(state)
    flow = {h: v for h, v in g5.get("flow", {}).items() if h in homes}
    work = _g6_workdays(state)
    sd = e2["step_day"]
    need = {"蓄え": math.ceil(sum(v[0] + v[1] + v[2] for v in flow.values()) / GRAIN / TOKEN["草の種"]) + math.ceil(sum(work.values()) / TOKEN["日"]),
            "交換": sum(math.ceil(n / TOKEN.get(k, 100)) for k, n in g["moved"].items()) + sum(1 for d in g["debts"] if d["day"] >= sd - 1),
            "刈る": math.ceil(sum(n for row in g5.get("reap", {}).values() for n in row.values()) / TOKEN["草の種"])}
    done, how, env = {w: 0 for w in WHATS}, {w: None for w in WHATS}, None
    for n, days in keep.items():
        j = g["jobs"].get(n) or {"what": list(WHATS), "how": "数え札"}
        cap = days * RATE[j["how"]]
        for w in j["what"]:
            use = min(cap, need[w] - done[w])
            if use > 0:
                done[w] += use
                cap -= use
                how[w] = "板" if "板" in (j["how"], how[w]) else "数え札"
                if w == "交換" and j["how"] in ("封筒", "板"):
                    env = "板" if j["how"] == "板" or env == "板" else "封筒"
    full = [w for w in WHATS if need[w] > 0 and done[w] >= need[w]]
    g["cover"] = {w: how[w] for w in full}
    if "交換" in full:
        for d in g["debts"]:
            if d["day"] >= sd - 1 and not d.get("proof"):
                d["proof"] = env or "数え札"
    if "蓄え" in full:
        g["credit"] = work
    tokens = sum(done.values())
    if tokens:
        g["token_seasons"] += 1
        g["big"] = max(g["big"], sum(need.values()))
    g["records"] = (g["records"] + [{"day": state["day"], "keepers": {n: [d, (g["jobs"].get(n) or {}).get("how", "数え札")] for n, d in keep.items()},
                                      "need": need, "done": done, "how": how, "complete": full, "envelope": env}])[-8:]
    who = "・".join(keep)
    parts = [f"{WHAT_WORDS[w]} ({'全部残せた' if w in full else '途中まで'}。{done[w]} / {need[w]} 個分)" for w in WHATS if need[w] and done[w]]
    log(state, "記録", list(keep)[0], f"{who} が、この季節の " + ("、".join(parts) if parts else "記録をつけようとしたが、残せたものはなかった")
        + (" を残した" if parts else ""), count=tokens, how="・".join(sorted({x for x in how.values() if x})) or "数え札")


def _g6_range(rng, x, s):
    lo, hi = x * rng.uniform(1 - s, 1), x * rng.uniform(1, 1 + s)
    return [int(lo // 100 * 100), int(-(-hi // 100) * 100)]


def _g6_ladder(state):
    """記録の道具 (困りごとが起きてから使えるようになる)。使うかは人が決める"""
    g, day = _g6(state), state["day"]
    op = g["open"]
    if not op["数え札"] and g["seal_seasons"] >= 1 and g["unchecked"] >= 1:
        op["数え札"] = day
        log(state, "記録", None, "印で封をするようになり、記録のない量を覚えで決めることも起きた。これからは、粘土の数え札で量を数えて残せる (主な仕事「記録をつける」)",
            tool="数え札")
    if op["数え札"] and not op["封筒"] and any(d["status"] == "まだ" for d in g["debts"]):
        op["封筒"] = day
        log(state, "記録", None, "ほかの村との貸し借りがある。これからは、貸し借りの数え札を粘土の玉 (封筒) に入れ、外に印を押して残せる", tool="封筒")
    if op["数え札"] and not op["板"] and g["token_seasons"] >= TABLET_SEASONS and g["big"] >= TABLET_TOKENS:
        op["板"] = day
        log(state, "記録", None, f"数え札で記録した季節が {g['token_seasons']} つになり、数え札が 1 季節に {g['big']} 個も要る季節があった。"
            "これからは、粘土の板に、物のしるしと数のしるしを分けて押して記せる", tool="板")


def _town(state):
    """町の目安 (いまの季節)。届いた日は区切り F3 に残る (あとで下回っても消さない)"""
    g = state["era2"].get("g6") or {}
    last = g.get("meets", [])[-TOWN_RUN:]
    others = g.get("others", [])
    run = len(last) == TOWN_RUN and all(any(d in o["contacts"] for o in others) for d in last)
    partners = [o for o in others if any(d in last for d in o["contacts"])]
    biggest = max((o["people"] for o in partners), default=0)
    pop = sum(1 for q in state["people"] if q["alive"])
    ads, nf = len(adults(state)), len(g.get("nonfood", []))
    ok = bool(g) and pop >= TOWN_POP and run and len(partners) >= TOWN_PARTNERS and pop >= CENTRE * biggest and nf >= NONFOOD * ads - 1e-9
    return {"ok": ok, "pop": pop, "run": run, "partners": len(partners), "biggest": biggest, "nonfood": nf, "adults": ads}


def _record_ok(state):
    """記録 (文字の入口): 物のしるしと数のしるしを分けて記した粘土の板で、量を確かめた"""
    return ((state["era2"].get("g6") or {}).get("checked") or {}).get("板", 0) >= 1


def _g6_settled(state, v, accepted):
    """ほかの村から来た群れを、受け入れた / 受け入れなかった"""
    o = _other(state, v.get("from"))
    if not o:
        return
    if accepted:
        o["trust"] = min(1.0, round(o["trust"] + 0.1, 2))
        if v.get("seed") is not None:
            o["people"] = max(0, o["people"] - len(v["members"]))
            _g6(state)["joined"] += len(v["members"])
    else:
        o["trust"] = max(0.0, round(o["trust"] - 0.1, 2))


def _g6_season_end(state, frac):
    """季節の終わり (G6。G5 の季節の終わりのあと): ほかの村ができる → 来る (申し出) → 住みたい人 → 貸し借り → 封のかけら → 出し入れの見え方 → 記録の道具 → 町"""
    e2, g, day = state["era2"], _g6(state), state["day"]
    rng = _rng(state, G6_SALT)  # この季節の終わりの G6 の乱数は、すべてこの列から (順番を変えない)
    sd, g5 = e2["step_day"], e2.get("g5") or {}
    # 0. 途中で区切った季節: まだ帰っていない人は、持ち物を持ち帰ったことにする (向こうで交換したあとなら、受けとった物と受けとってもらえなかった物。
    #    交換の前なら、持って行った物。2026-10-09 確かめ役: 前は、向こうが受けとって何も払えなかったとき、渡した物も持ち帰っていた)
    for name, tr in g["trips"].items():
        if tr.get("state") == "行く":
            ids = []
            if tr.get("bartered"):
                side = _g6_put(state, tr["side"], tr["got"], tr["goats_in"], ids)
                _g6_put(state, tr["side"], tr["back"])
                mv = [_mv(side, 1, tr["got"], ids), _mv(side, 1, tr["back"])]
                brought = {k: tr["got"].get(k, 0) + tr["back"].get(k, 0) for k in list(tr["got"]) + [k for k in tr["back"] if k not in tr["got"]]}
            else:
                side = _g6_put(state, tr["side"], tr["took"])
                mv, brought = [_mv(side, 1, tr["took"])], tr["took"]
            tr.update(state="帰った", end=day)
            g["trip_log"].append(dict(tr))
            o = _other(state, tr["to"])
            log(state, "交換に行く", name, f"季節が途中で区切られたので、{name} は {o['name'] if o else 'ほかの村'} から帰ってきた ({_g6_home(brought)})",
                other=tr["to"], trip=tr["id"], moves=mv)
    # 1. 村を出た家 (G5) は、まだだれも知らない「分かれた家の村」になる (G6 の前に出た家も。来たときに初めてお題に出る)
    for f in g5.get("fissions", []):
        if not any(o["household"] == f["household"] for o in g["others"]):
            _new_other(state, rng, "分かれた家", household=f["household"], people=len(f["people"]), goats=f["goats"], grain=round(f["store"] / GRAIN))
    # 2. この季節の終わりに来たよその群れの、来たところ (G6 に入る前に来た人の来たところは書かない)
    for v in e2["visitors"]:
        if v.get("day") == day and "from" not in v:
            st = [o for o in g["others"] if o["kind"] == "よその村"]
            o = rng.choice(st) if st and (len(st) >= MAX_STRANGERS or rng.random() < 0.5) else _new_other(state, rng, "よその村")
            v["from"] = o["id"]
            o["known"] = o["known"] or day
            log(state, "よその村", None, f"よその群れの {'・'.join(m['name'] for m in v['members'])} は、{_okey(o)} から来たと言った", other=o["id"])
    # 3. 交換をもとめて、よその村の人が来る (G6 の最初の季節の終わりは必ず。【仮定】交換は村の始まりからあったので、待たない (計画 3.))
    #    最初の季節の終わりに、2. で群れの来たところの村ができていたら、その村の人が来る (新しい村は作らない。2026-10-09 確かめ役: 前は 2. で村ができると、来ないことが多かった)
    st = [o for o in g["others"] if o["kind"] == "よその村"]
    came = set()
    if not g["log"] or (len(st) < MAX_STRANGERS and rng.random() < STRANGER_P * frac):
        o = st[0] if st and not g["log"] else _new_other(state, rng, "よその村")
        o["known"] = o["known"] or day
        _g6_offer_new(state, rng, o, True)
        came.add(o["id"])
    # 4. ほかの村の 1 季節 (【仮定】人は 1 季節 0.5% ほど増える。夏のはじめに、その年が苦しい年か決まる。ヤギは春に増える。土器・鎌は少しずつ割れる)
    nxt = season(day + 1)
    for o in g["others"]:
        if rng.random() < o["people"] * 0.005 * frac:
            o["people"] += 1
        if nxt == "夏":
            o["bad"] = day if rng.random() < BAD_P else None
            o["grain"] = min(o["grain"], o["people"] * 20) if o["bad"] is not None else min(o["people"] * 300, o["grain"] + o["people"] * 100)
        if nxt == "春":
            o["goats"] = min(max(o["people"], 2), round(o["goats"] * 1.3))
        o["pots"], o["sickles"] = int(o["pots"] * 0.97), int(o["sickles"] * 0.95)
        if o["has_obsidian"]:
            o["obsidian"] = min(40, o["obsidian"] + 8)
    # 5. ほかの村の人が来る (この季節に村の人が行った村は来ない)
    went = {tr.get("to") for tr in g["trips"].values()}
    for o in g["others"]:
        if o["id"] in came:
            continue
        due = any(d["other"] == o["id"] and d["status"] == "まだ" and d["due"] <= day + 1 for d in g["debts"])
        # 返す分のある村は、村の人が行った季節でも返しに来る (2026-10-09 試し回し: 毎季節行く村は一度も来られず、貸し借りがみな「返されないまま」になっていた)
        if o["id"] in went and not due:
            continue
        p = min(0.8, max(0.8 if due else 0.0, CONTACT_P[o["kind"]] * o["trust"] / 0.5))
        if rng.random() < p * frac:
            first = o["known"] is None
            o["known"] = o["known"] or day
            _g6_offer_new(state, rng, o, first)
    # 6. 交換している村から、ここで暮らしたい人が来る (町に人が集まる。【文献・二次】ブラクには移り住んだ人が加わったとする調べがある【仮定】見込み)
    recent = g["meets"][-TOWN_RUN:]
    for o in g["others"]:
        if o["known"] is None or o["people"] < JOIN_MIN or not any(c in recent for c in o["contacts"]):
            continue
        if rng.random() < JOIN_P * min(1.0, store_days(state) / 120) * (2 if o["bad"] is not None else 1) * frac:
            members = []
            for i in range(rng.choice([1, 2, 2, 3])):
                age = rng.randint(16, 35) if i < 2 else rng.randint(2, 12)
                members.append({"name": _next_name(state), "sex": "女" if rng.random() < 0.5 else "男", "age": age})
            e2["visitors"].append({"name": members[0]["name"], "members": members, "day": day, "from": o["id"], "seed": rng.getrandbits(31)})
            txt = "、".join(f"{m['name']} ({m['sex']}、{m['age']} 歳)" for m in members)
            log(state, "訪れる", None, f"{_okey(o)} から {txt} がやって来て、「ここで暮らしたい」と言った", other=o["id"])
    # 7. 返されないまま 1 年たった貸し借り
    for d in g["debts"]:
        if d["status"] == "まだ" and day - d["due"] >= YEAR:
            d.update(status="返されない", end=day)
            o = _other(state, d["other"])
            if o:
                o["trust"] = max(0.0, round(o["trust"] - 0.2, 2))
            log(state, "貸し借り", None, f"[{d['id']}] ({o['name'] if o else 'ほかの村'} が返すはずの {_gw(d['goods'])}) は、返されないまま 1 年たった", debt=d["id"])
    # 8. 封のかけら (この季節)
    ss = g["season_seals"]
    if ss:
        log(state, "封", None, "この季節、印で封をした倉や村の蓄えが開けられた (割った封のかけらは取っておいた): "
            + "、".join(f"{h}の印 {n} 回" if h != "(印なし)" else f"印のない封 {n} 回" for h, n in sorted(ss.items())), count=sum(ss.values()))
        for h, n in ss.items():
            g["sealings"][h] = g["sealings"].get(h, 0) + n
        if sum(1 for h in ss if h != "(印なし)") >= 2:
            g["seal_seasons"] += 1
    # 9. 前の季節の、家ごとの村の蓄えへの出し入れの見え方 (記録がなければ、みんなの覚えの幅。印で封をした家は幅が半分)
    s, how = _g6_spread(state), g["cover"].get("蓄え")
    rows = {}
    for h, (i, out) in sorted(g5.get("last_flow", {}).items()):
        sh = s / 2 if h in g["seals"] and g["store_sealed"] == sd else s
        rows[h] = [i, out] if how else [_g6_range(rng, i, sh), _g6_range(rng, out, sh)]
    g["shown"] = {"day": day, "how": how, "rows": rows}
    # 10. 食べ物をとらない人・記録の道具・町
    g["nonfood"] = sorted(set(e2.get("specialists", [])) | {n for n, x in g["keep_days"].items() if x >= KEEPER_DAYS * frac})
    _g6_ladder(state)
    t = _town(state)
    if t["ok"] and g["town_seen"] is None:
        g["town_seen"] = day
        log(state, "町", None, f"村の人は {t['pop']} 人で、交換した村のうちいちばん大きい村 (約 {t['biggest']} 人) の {CENTRE} 倍をこえた。この {TOWN_RUN} 季節は毎季節ほかの村と"
            f"交換し、相手の村は {t['partners']} つ。この季節、作ることや記録に 20 日以上を使った人は、大人 {t['adults']} 人のうち {t['nonfood']} 人")
    if g["town_seen"] is not None:
        g["town_low"] = 0 if t["ok"] else g["town_low"] + 1
        if g["town_low"] == 4:
            log(state, "町", None, f"町の目安を下回ったまま 1 年たった (村の人 {t['pop']} 人、この 4 季節に交換した村 {t['partners']} つ)")
    g["log"].append({"day": day, "pop": t["pop"], "adults": t["adults"], "households": len(_homes(state)), "known": sum(1 for o in g["others"] if o["known"]),
                     "partners": t["partners"], "biggest": t["biggest"], "run": t["run"], "exchanges": g["exchanges"], "joined": g["joined"],
                     "seals": len(g["seals"]), "sealings": sum(ss.values()), "tools": [k for k, v in g["open"].items() if v],
                     "tokens": sum(g["records"][-1]["done"].values()) if g["records"] and g["records"][-1]["day"] == day else 0,
                     "checked": dict(g["checked"]), "misremember": g["misremember"], "nonfood": t["nonfood"], "town": t["ok"]})
    g["season_seals"], g["opened"], g["taken"], g["moved"] = {}, {}, {}, {}
    g["seed"] = rng.getrandbits(31)  # 次の季節の集まりと 30 日の乱数のもと (この列の最後に引く)


def _g6_indicators(state):
    """G6 の目安 (G6 の前は鍵を足さない。だから G6 の前の state.json・app_data.json は前とまったく同じ。G6 に入って g6 を作る前は 0)"""
    if not era_at_least(state, "G6"):
        return {}
    base = {"g6_on": False, "g6_known": 0, "g6_partners": 0, "g6_biggest": 0, "g6_run": 0, "g6_exchanges": 0, "g6_debts_open": 0, "g6_joined": 0,
            "g6_seals": 0, "g6_sealings": 0, "g6_seal_seasons": 0, "g6_tools": "", "g6_records": 0, "g6_checked": 0, "g6_checked_tablet": 0,
            "g6_misremember": 0, "g6_nonfood": 0, "g6_town": False, "g6_town_day": None, "g6_record_day": None}
    g = state["era2"].get("g6")
    if not g:
        return base
    t = _town(state)
    sub = {x["f"]: x["day"] for x in state["era2"].get("substeps", []) if x["g"] == "G6"}
    run = 0
    for d in reversed(g["meets"]):
        if not any(d in o["contacts"] for o in g["others"]):
            break
        run += 1
    return base | {"g6_on": True, "g6_known": sum(1 for o in g["others"] if o["known"] is not None), "g6_partners": t["partners"], "g6_biggest": t["biggest"],
                   "g6_run": run, "g6_exchanges": g["exchanges"], "g6_debts_open": sum(1 for d in g["debts"] if d["status"] == "まだ"),
                   "g6_joined": g["joined"], "g6_seals": len(g["seals"]), "g6_sealings": sum(g["sealings"].values()), "g6_seal_seasons": g["seal_seasons"],
                   "g6_tools": "・".join(k for k, v in g["open"].items() if v), "g6_records": g["token_seasons"],
                   "g6_checked": sum(g["checked"].values()), "g6_checked_tablet": g["checked"]["板"], "g6_misremember": g["misremember"],
                   "g6_nonfood": t["nonfood"], "g6_town": t["ok"], "g6_town_day": sub.get("F3"), "g6_record_day": sub.get("F4")}


# ---- アプリ用 ----

def g6_places(state):
    """3D の再生で、ほかの村へ行く人が歩いて行く地図の端 (知っている村だけ。G6 の前は空)"""
    g = (state.get("era2") or {}).get("g6") or {}
    return [{"id": o["id"], "label": o["name"], "x": min(79, max(0, o["edge"][0])), "y": min(79, max(0, o["edge"][1])), "far": True}
            for o in g.get("others", []) if o["known"] is not None]


def g6_export(state):
    g = state["era2"]["g6"]
    return {"others": [{k: o[k] for k in ("id", "name", "kind", "household", "dir", "days", "edge", "known", "people", "contacts")} for o in g["others"]
                       if o["known"] is not None],
            "seals": g["seals"], "open": g["open"], "records": g["records"], "debts": g["debts"], "trips": g["trip_log"][-200:], "log": g["log"], "end": g["end"]}


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


def pasture_cap(state):
    """草原と丘の草で 1 年に養えるヤギの数 K (10 頭単位)。地図の草原と丘のマスの広さ × PASTURE_PER_HA"""
    ha = sum(row.count("g") + row.count("h") for row in state["terrain"]) * world.CELL ** 2 / 10000
    return int(round(ha * PASTURE_PER_HA / 10)) * 10


def _pasture_loss(state, cap, frac, rng):
    """草が足りない季節 (飼っているヤギ N が K より多い): 多すぎる分の PASTURE_LOSS がやせていなくなる。
    いなくなる数は持ち主 (村・家) ごとの頭数に比べて分け (端数の大きい順。同じなら村 → 家の名前の順)、持ち主の中では rng で選ぶ"""
    e2 = state["era2"]
    n = len(e2["goats"])
    m = round(PASTURE_LOSS * (n - cap) * frac) if n > cap else 0
    if m <= 0:
        return
    by = {}
    for g in e2["goats"]:
        by.setdefault(g.get("owner"), []).append(g)
    keys = sorted(by, key=lambda h: (h is not None, h or ""))
    share = {h: m * len(by[h]) // n for h in keys}
    for h in sorted(keys, key=lambda h: -(m * len(by[h]) % n))[:m - sum(share.values())]:
        share[h] += 1
    gone = {g["id"] for h in keys if share[h] for g in rng.sample(by[h], share[h])}
    e2["goats"][:] = [g for g in e2["goats"] if g["id"] not in gone]
    hit = [h for h in keys if share[h]]
    who = "・".join(f"{'村' if h is None else h} {share[h]} 頭" for h in hit) if hit != [None] else ""  # 村のヤギだけなら書かない
    log(state, "ヤギ", None, f"草が足りず、飼っていたヤギ {m} 頭がやせていなくなった{' (' + who + ')' if who else ''}"
        f"。草原と丘の草で養えるヤギは 約 {cap} 頭で、{n} 頭いた", cap=cap, herd=n, goat_ids=sorted(gone))


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
    # 草が足りない (ヤギが K 頭より多い) と、やせていなくなる・子が少ない (2026-10-10 本人と決めた。上の PASTURE_PER_HA)。
    #   この乱数は草が足りないときだけ引く (K 頭以下の世界は、前と同じに進む)
    cap, prng = pasture_cap(state), _rng(state, PASTURE_SALT)
    _pasture_loss(state, cap, frac, prng)
    if sea == "春" and e2.get("kid_year") != (day + 1) // YEAR:
        e2["kid_year"] = (day + 1) // YEAR
        kids, n = 0, len(e2["goats"])
        mothers = [g for g in e2["goats"] if g["sex"] == "メス" and day - g["born"] >= YEAR]
        for g in mothers:
            if n > cap and prng.random() >= cap / n:  # 草が足りないと、子を産む母ヤギが K/N に減る
                continue
            for _ in range(2 if rng.random() < 0.4 else 1):  # 【仮定】双子の見込み 4 割
                e2["goats"].append({"id": e2["next_goat"], "sex": "メス" if rng.random() < 0.5 else "オス", "born": day, "owner": g.get("owner")})
                e2["next_goat"] += 1
                kids += 1
        if n > cap and mothers:
            log(state, "ヤギ", None, f"草が足りず、子ヤギがあまり生まれなかった (飼っているヤギに、子ヤギが {kids} 頭生まれた)" if kids
                else "草が足りず、子ヤギが生まれなかった", cap=cap, herd=n)
        elif kids:
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
            members.append({"name": _next_name(state), "sex": "女" if rng.random() < 0.5 else "男", "age": age})  # 受け入れなくても名前は使い切る (同じ名前の別人を作らない)
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
    if era_at_least(state, "G6"):
        _g6_records(state, frac)  # この季節の記録 (G5 のもめごとを決める前に。どの量に記録があるかを決める)
    if era_at_least(state, "G5"):  # 家族を決めてから (この季節に生まれた子も母の家に入る)。村が分かれて大人が 12 人以下になれば、次の _note_mode で代表の方式が終わる
        _g5_season_end(state, frac)
    if era_at_least(state, "G6"):  # G5 のあと (この季節に村を出た家も、ほかの村になる)
        _g6_season_end(state, frac)
    _note_mode(state)


# ---------------- 家族と代表 (計画 4: 大人が 12 人をこえたら、家族の代表だけが答える) ----------------

REP_FROM = 12


def _sync_households(state):
    """家族 (家) を決める。【仮定】最初からいる人とその子で「川辺の家」、よそから一緒に来た群れごとに 1 つの家 (群れの最初の人の名前で呼ぶ)。
    村で生まれた子は母の家に入り、大人になっても同じ家にいる"""
    named = {}
    for e in state["events"]:  # 加わる は、古い年をしまっても state.json に残す (archive.KEEP_TYPES)
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


def feelers(state):
    """気持ちだけ答える人 (2026-10-09 本人の希望「全員が気持ちだけ答える」): 家族の代表 (と G5 のまとめ役) でない大人。
    季節のはじめに、今の気持ちとだれかへの一言だけを答える。仕事・掟の投票・受け入れは、今までどおり代表が決める (世界の進み方は変わらない)"""
    if not state["era2"].get("rep_mode"):
        return []
    who = set(answerers(state))
    return [p["name"] for p in adults(state) if p["name"] not in who]


def feeling_prompt(state, p, first):
    """代表でない大人のお題 (気持ちと一言だけ)"""
    st = dict(state, day=state["day"] + 1)
    me = characters._me(st, p).replace("(誰でも入れたり取ったりできる)", "(日々の出し入れは自動)")
    who = set(answerers(state))
    rep = next((q["name"] for q in family(state, p["name"]) if q["name"] in who), None)
    fam = [q for q in family(state, p["name"]) if q is not p]
    kids = [c for c in children(state) if c.get("household") and c.get("household") == p.get("household")]
    rows = [f"- {q['name']} ({q['sex']}、{q['age']} 歳{'。家族の代表' if q['name'] == rep else ''})" for q in fam]
    rows += [f"- 子: {c['name']} ({c['sex']}、{c['age']} 歳)" for c in kids]
    sea = season(state["day"] + 1)
    return f"""{RULES2}

{me}
## 村のようす
{_village(state)}{_year_names_text(state)}
## 前の季節のこと
{_season_digest(state, p, first)}

## 最近聞いた話
{characters._heard(p)}

## あなたの家族 ({p.get('household')})
村の大人が {REP_FROM} 人をこえたので、季節の集まりでは家族ごとに、いちばん年上の大人が代表して答える。{f'{p.get("household")} の代表は {rep}。' if rep else ''}代表が、家族の大人の仕事・掟の投票・よそから来た人の受け入れを決める。あなたは代表ではないので、仕事は決めない。
{chr(10).join(rows) if rows else '- (ほかの家族はいない)'}

## いま
{state["day"] + 1} 日目、{sea}。季節のはじめの集まり。あなたが答えるのは次の 2 つだけ。
1. 今の気持ち (feeling、120 字まで)。前の季節に起きたことと、あなた自身や家族のことから、あなたらしい言葉で
2. だれかに一言 (say、0〜1 つ、60 字まで。相手は仲間の名前か「みんな」)。前と同じ言い回しをくり返さない

## 答えの形 (JSON)
{{"say": [{{"to": "みんな", "text": "..."}}], "feeling": "..."}}"""


def apply_feelings(state, answers):
    """代表でない大人の、気持ちと一言 (2026-10-09 から)。世界のしくみには使わない。一言は話として記録し、聞き手に届く"""
    alive = {p["name"]: p for p in adults(state)}
    talk = []
    for name, raw in answers.items():
        p = alive.get(name)
        if not p:
            continue
        a = characters.parse(raw)
        f = str(a.get("feeling", "")).strip()[:120]
        if f:
            p["feeling"], p["feeling_day"] = f, state["day"]
        for s in (a.get("say") or [])[:1]:
            text = str((s or {}).get("text", ""))[:60] if isinstance(s, dict) else ""
            to = (s or {}).get("to", "みんな") if isinstance(s, dict) else "みんな"
            if text:
                eid = log(state, "話す", name, f"{name} → {to}: 「{text}」", to=to)
                talk.append({"day": state["day"], "from": name, "text": text, "event": eid, "to": to})
    for t in talk:
        for n, q in alive.items():
            if n != t["from"] and (t["to"] == "みんな" or t["to"] == n):
                q["heard"].append({k: t[k] for k in ("day", "from", "text", "event")})
                q["heard"] = q["heard"][-30:]


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
        **_g6_indicators(state),
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


# まとめ役なしの道 (2026-10-09 本人と決めた。29年30日目 = 3509 日目): 村の人は第 2 段の 55 季節のうち 47 季節、まとめ役に「なし」を選び、
#   集まり・長老・祭りでもめごとを収め続けた。【文献】Johnson 1982 は「順番の階層」(家の長の話し合いと儀礼) を、決まった役 (同時の階層) に代わる
#   規模のストレスへの答えとした (計画 2.1 の 3 つの答えの 1 つめ)。そこで、まとめ役が 2 回以上裁いた道のほかに、この道でも G5 を終える
NO_LEADER_SEASONS = 8  # 【仮定】まとめ役なしで続いた季節 (2 年)
NO_LEADER_SETTLED = 2  # 【仮定】そのあいだに、集まり・長老・祭りで収めたもめごと


def _g5_no_leader(state, g):
    """まとめ役なしの道の目安: (まとめ役のいない季節, そのあいだに集まり・長老・祭りで収めたもめごと, 収まらないまま 2 季節をこえたもめごと)"""
    day = state["day"]
    if g["leader"]:
        return 0, 0, 0
    since = (g.get("open") or {}).get("day") or g["start"]
    for e in reversed(state["events"]):  # いちばん新しい「まとめ役がいなくなった・なくなった」(まとめ役 は、古い年をしまっても state.json に残す)
        if e["day"] < since:
            break
        if e["type"] == "まとめ役" and (e["text"].endswith("村にまとめ役がいなくなった") or "はまとめ役でなくなった" in e["text"]):
            since = e["day"]
            break
    seasons = (day - since) // SEASON_DAYS
    lo = day - NO_LEADER_SEASONS * SEASON_DAYS
    settled = sum(1 for d in g["disputes"] if d["status"] == "収まった" and d.get("by") in ("集まり", "長老", "祭り") and lo < (d.get("end") or 0) <= day)
    stale = sum(1 for d in g["disputes"] if d["status"] == OPEN and d["day"] <= day - 2 * SEASON_DAYS)
    return seasons, settled, stale


def _g5_indicators(state):
    """G5 の目安 (G5 の前は 0。家族の数は G4 の 5 季節ごとの報告にも使うので、いつも数える)"""
    base = {"households": len(_homes(state)), "g5_stage": 0, "stage1": None, "leader": None, "leader_seasons": 0, "disputes": 0,
            "disputes_open": 0, "settled": 0, "judged": 0, "penalty_laws": 0, "penalties": 0, "feasts": 0, "fissions": 0,
            "left_people": 0, "joint": 0, "stress": 0.0, "no_leader_seasons": 0, "no_leader_settled": 0, "stale_open": 0, "g5_path": None}
    g = state["era2"].get("g5")
    if not era_at_least(state, "G5") or not g:
        return base
    nls, nlset, stale = _g5_no_leader(state, g)
    path = ("まとめ役" if g["leader"] and g["judged"] >= 2 else
            "まとめ役なし" if g["stage1"] and nls >= NO_LEADER_SEASONS and nlset >= NO_LEADER_SETTLED and not stale else None)
    return base | {"no_leader_seasons": nls, "no_leader_settled": nlset, "stale_open": stale, "g5_path": path,
                   "g5_stage": g["stage"], "stage1": g["stage1"], "leader": g["leader"],
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
    # 2026-10-09 本人と決めた (27年120日目 = 3359 日目): 「罰のある掟が 3 つ以上」「罰を 1 回以上払わせた」を条件から外した。
    #   第 2 段に入って 50 季節、罰のある掟は 1 本も出なかった (お題の例を罰の欄の形にしたあとの 15 季節も 0)。罰を決めた掟の記録は
    #   ウル・ナンム法典 (前 2100 年ごろ) からで、手本のウバイド期にはまとめ役はいても罰の掟の証拠はない。罰の数は記録を続け、G6 のあとの目安にする
    # 2026-10-09 本人と決めた (29年30日目 = 3509 日目): まとめ役なしの道も認める (上の NO_LEADER_SEASONS)。どちらの道かは g5_path に残る
    "G5": ("第 2 段: 家族が 6 つ以上で、(まとめ役がいて、もめごとを 2 回以上裁いた) か (第 1 段の目安に届き、まとめ役のいないまま 8 季節、"
           "集まり・長老・祭りでもめごとを 2 回以上収め、収まらないまま 2 季節をこえたもめごとがない)",
           lambda i: i["g5_stage"] >= 2 and i["households"] >= 6 and i.get("g5_path") is not None),  # 古い控えには g5_path がない
    # G6 (第 4 部「町と文字」): 町と記録は別々の条件で、どちらが先でもよい。それぞれ届いた日は区切り F3・F4。両方に一度でも届くと Society 2.0 の終わり
    #   (2026-10-09 本人と決めた: 町は 50 人、交換が 4 季節続く (相手は 2 つ以上の村)、記録は粘土の板で量を確かめた。一度届けば届いたまま)
    "G6": ("町 (村が 50 人以上で、この 4 季節は毎季節ほかの村と交換し、相手の村が 2 つ以上、村がいちばん大きい相手の村の 2 倍以上、食べ物をとらない人が大人の 1 割以上) と、"
           "記録 (物のしるしと数のしるしを分けて記した粘土の板で、量を確かめた) の両方に、一度でも届く (どちらが先でもよい)",
           lambda i: bool(i["g6_town_day"]) and bool(i["g6_record_day"])),
}
ORDER2 = ["G1", "G2", "G3", "G4", "G5", "G6"]
NAMES2 = {"G1": "村ができる", "G2": "畑と家畜", "G3": "余りと分業", "G4": "持ち物と差", "G5": "リーダーと決まり", "G6": "交易・町・記録"}


# ---------------- G の中の小さな区切り F (2026-10-08 本人の希望) ----------------
# 本人「F はある一つの変化、G は一つの大きな変化。G の中に F はあるはず。F ごとにも G ごとにも動画と記録を残す」。
# 区切りの中身は docs/research/society2_periodization.md の 4. (部の中の途中経過の目安) による。季節の終わりに見て、入った日を記録する (止まらない)。
# 書くときは「G3 の F1」(Society 1.0 の F1〜F6 とまぎれないように G をつける)
SUBSTEPS = {
    "G3": [("F1", "土器を作り始める", lambda s: s["era2"].get("pots", 0) > 0 or any(e["type"] == "土器" and (e.get("data") or {}).get("count") for e in s["events"][-3000:])),
           ("F2", "家族の住まいができる", lambda s: bool(_homes_built(s))),
           ("F3", "作る人が出る", lambda s: bool(s["era2"].get("specialists")))],
    "G4": [("F1", "家の倉に食べ物をためる", lambda s: any(h["store"] for h in s["era2"].get("house", {}).values())),
           ("F2", "受けつぎ", lambda s: s["era2"].get("inherits", 0) >= 1)],
    "G5": [("F1", "集まり・長老・祭りでまとまる", lambda s: bool((s["era2"].get("g5") or {}).get("stage1"))),
           ("F2", "まとめ役が選ばれる", lambda s: bool((s["era2"].get("g5") or {}).get("leaders"))),
           ("F3", "罰を払わせる", lambda s: (s["era2"].get("g5") or {}).get("penalties", 0) >= 1)],
    # G6 の F (2026-10-09 本人と決めた 4 つ)。数え札・封筒・粘土の板は、出来事「記録」に残す
    "G6": [("F1", "村どうしの交換", lambda s: (s["era2"].get("g6") or {}).get("exchanges", 0) >= 1),
           ("F2", "印で封をする", lambda s: (s["era2"].get("g6") or {}).get("seal_seasons", 0) >= 1),
           ("F3", "町", lambda s: _town(s)["ok"]),
           ("F4", "物と数を分けて記す", lambda s: _record_ok(s))],
}
# G1・G2 の F は、この仕組みを作る前に終わっていたので、記録 (出来事) から日を決めた (2026-10-08。G1_notes.md・G2_notes.md)
RETRO_SUBSTEPS = [
    {"g": "G1", "f": "F1", "name": "畑を始める", "day": 510, "why": "セナとウィロが初めて畑に草の種をまいた"},
    {"g": "G1", "f": "F2", "name": "よそから人が加わる", "day": 629, "why": "ナギとソルが村に加わった"},
    {"g": "G1", "f": "F3", "name": "村で子が生まれる", "day": 659, "why": "セナにミラが生まれた (2 回目の Society 2.0 で初めて)"},
    {"g": "G2", "f": "F1", "name": "家族の代表で決める", "day": 1259, "why": "大人が 12 人をこえ、家族ごとに代表が答えるようになった"},
    {"g": "G2", "f": "F2", "name": "ヤギを捕まえて飼う", "day": 1415, "why": "代表のセナが割り振り、タヒが子ヤギを捕まえた (この季節に 4 頭)"},
    {"g": "G2", "f": "F3", "name": "ヤギが増える", "day": 1529, "why": "子ヤギが 3 頭生まれて 5 頭になった"},
    # G3 は 1 季節 (1560〜1589 日目) で終わり、F を見つける仕組みを入れる前だった。起きたのは F3 だけ (F1 土器・F2 家族の住まいは起きなかった)
    {"g": "G3", "f": "F3", "name": "作る人が出る", "day": 1589, "why": "ナギとソルが 30 日、道具づくりで石の鎌を作った (39 本)"},
]


def check_substeps(state):
    """今の G の中の F に入ったかを見て、入った日を記録する (季節の終わり。フェーズが進む前に見る)"""
    era = state.get("era")
    done = state["era2"].setdefault("substeps", [])
    for f, name, fn in SUBSTEPS.get(era, []):
        if not any(x["g"] == era and x["f"] == f for x in done) and fn(state):
            done.append({"g": era, "f": f, "name": name, "day": state["day"]})
            log(state, "区切り", None, f"{era} の {f}「{name}」に入った", g=era, f=f)  # 「フェーズが…に進んだ」とは書かない (ワークフローが止まらないように)


def check(state):
    era = state["era"]
    check_substeps(state)
    ind = indicators(state)
    desc, fn = CRITERIA.get(era, ("(まだ作っていない)", lambda i: False))
    met = fn(ind)
    since = state["day"] - state["era_log"][-1]["day"]
    state["era_info"] = {"era": era, "name": NAMES2[era], "next": desc, "met": met, "since": since, "indicators": ind}
    if met and era == ORDER2[-1]:  # G6: 町と記録がそろった → Society 2.0 の終わり (一度だけ "end" を返す。フェーズは進まない。step.py は "end" を先に見る)
        g6 = state["era2"].get("g6") or {}
        if g6 and not g6.get("end"):
            t, r = ind["g6_town_day"], ind["g6_record_day"]
            g6["end"] = {"day": state["day"], "town": t, "record": r, "first": "町" if t < r else "記録" if r < t else "同じ日"}
            return "end"
        return False
    if met and era != ORDER2[-1]:
        nxt = ORDER2[ORDER2.index(era) + 1]
        state["era"] = nxt
        state["era_log"].append({"era": nxt, "day": state["day"], "indicators": ind})
        state["era_info"] = {"era": nxt, "name": NAMES2[nxt], "next": CRITERIA.get(nxt, ("(まだ作っていない)",))[0], "met": False, "since": 0, "indicators": ind}
        return True
    return False


# ---------------- 季節の集まりの出来事 (読むだけ。docs/dashboard_records_spec.md 3.4) ----------------

MEETING_EVENTS = ("話す", "掟", "もめごと", "収める", "裁き", "罰", "祭り", "まとめ役", "共同の仕事", "加わる", "去る", "ヤギを食べる", "年の名前",
                  "印", "封", "よその村", "交換", "貸し借り", "確かめる", "覚え")  # 後ろの 7 つは G6 の集まりの出来事 (G6 の前は起きない)


def _meeting_event(e):
    t, x = e["type"], e["text"]
    if t not in MEETING_EVENTS:
        return False
    if t == "封":
        return "ふさぐことになった" in x  # 季節の終わりの「封のかけら」と、30 日のあいだの「封が割れていた」は、集まりの前
    if t in ("よその村", "交換"):
        return x.startswith("季節の集まりで")  # 季節の終わりに来た人・交換に行った先での交換は、集まりの前
    if t == "貸し借り":
        return "返されないまま" not in x  # 返されないまま 1 年たったのは、季節の終わり
    if t == "もめごと":
        return "話し合ったが" in x  # 季節の終わりの「言い出した」「重なった」「言わなくなった」は、集まりの前
    if t == "去る":
        return "受け入れられず" in x  # 蓄えが尽きて出ていくのは、季節の途中
    if t == "まとめ役":
        return not x.endswith("村にまとめ役がいなくなった")  # 亡くなった・村を出たのは、季節の終わり
    return True


def meeting_first(state, day):
    """day 日の終わりの季節の集まりの、最初の出来事の id (集まりの出来事がなければ、その日の次の id)。読むだけ
    (集まりの出来事は、季節の終わりの出来事のあとに、同じ日の日付で記録される。2026-10-09 に、git に残る 51 回の集まりで、すべて合うことを確かめた)"""
    ev = state["events"]
    i = len(ev)
    while i > 0 and ev[i - 1]["day"] > day:
        i -= 1
    end = i
    while i > 0 and ev[i - 1]["day"] == day and _meeting_event(ev[i - 1]):
        i -= 1
    return ev[i]["id"] if i < end else (ev[end - 1]["id"] + 1 if end else 0)


# ---------------- 年の名前 (口で伝える年代記。2026-10-09 本人と決めた。docs/dashboard_records_spec.md 5.) ----------------
# 年の終わりの季節の集まり (年の最後の日 (day + 1) % YEAR == 0 の終わりに書くお題と、その答え) で、季節の答えをする人 (家族の代表と、まとめ役) が、
#   終わった年に、その年いちばん大きな出来事で名前をつける。決まった名前は、そのあとのお題に「村で覚えている年の名前」として出る
# 【文献】年の名前 (メソポタミア)・年の記録 (エジプト)・冬の数え (ラコタ) (docs/research/historical_records.md の ⑩)
# 決め方: 同じ名前を書いた人の、家族の大人の数 (その答えが数える大人の数) を足して、いちばん多い名前 (半分をこえなくてもよい)。
#   同じなら、その名前を書いた人でいちばん年上の人の名前 (同じ年なら人の並びで先。長老の決め方と同じ)。乱数は使わない。
#   だれも書かなければ名前はつかない (state も出来事も前と同じ)
YEAR_NAME_MAX = 20
YEAR_EVENTS = ("フェーズ", "区切り", "段階", "分かれる", "死", "生まれる", "加わる", "去る", "まとめ役", "受けつぎ", "祭り", "住まい", "もめごと",
               "収める", "裁き", "罰", "大人になる", "ヤギ", "ヤギを食べる", "虫", "蓄えが尽きる", "家族",
               "町", "記録")  # お題に見せる出来事 (前のものほど先に残す)。町・記録は G6 から (記録は、道具が使えるようになったときだけ)
YEAR_DIGEST_MAX = 15
STOP_WORDS = ("フェーズが", "Society 2.0 が終わった")  # ワークフローが止まる文と重なる名前は読まない (step.py が出来事を表示するため)


def year_end(state):
    """この集まりが、年の終わりの集まりか"""
    return (state["day"] + 1) % YEAR == 0


def _year_name_text(v):
    """答えの year_name → 名前 (読めないもの・お題の例の写しは "")"""
    s = unicodedata.normalize("NFKC", v if isinstance(v, str) else "").strip().strip("「」『』\"'“”。 ").strip()
    if not s or s.lower() in ("...", "null", "none", "なし") or not s.isprintable() or any(w in s for w in STOP_WORDS):  # 改行などのある名前も読まない
        return ""
    return s[:YEAR_NAME_MAX].strip()


def _year_digest(state):
    """年の名前のお題: この 1 年のおもな出来事 (読むだけ)"""
    y = state["day"] // YEAR
    ev = archive.events_from(state, meeting_first(state, y * YEAR - 1))  # この年の最初の季節の集まりから (古い年をしまうと、id は並びの番号でなくなる。2026-10-10)
    big = [e for e in ev if e["type"] in YEAR_EVENTS and not (e["type"] == "住まい" and "size" not in (e.get("data") or {}))
           and not (e["type"] == "ヤギ" and e.get("who"))  # 建てた日ごとの記録と、1 頭ずつ捕まえたのは入れない (下で数でまとめる)
           and not (e["type"] == "記録" and "tool" not in (e.get("data") or {}))]  # G6: 季節ごとの記録は入れない (道具が使えるようになったときだけ)
    if len(big) > YEAR_DIGEST_MAX:
        big = sorted(sorted(big, key=lambda e: (YEAR_EVENTS.index(e["type"]), e["id"]))[:YEAR_DIGEST_MAX], key=lambda e: e["id"])
    rows = [f"- [出来事 {e['id']}] {e['text']}" for e in big]
    caught = sum(1 for e in ev if e["type"] == "ヤギ" and e.get("who"))
    harv = sum((e.get("data") or {}).get("amount", 0) for e in ev if e["type"] == "収穫")
    rows += ([f"- 野生の子ヤギを {caught} 頭捕まえた"] if caught else []) + ([f"- 畑で刈った草の種: 合わせて {harv} つかみ"] if harv else [])
    return "\n".join(rows) or "- (大きな出来事はなかった)"


def _year_end_text(state):
    """年の終わりの集まりのお題の節 (ほかの集まりでは空)"""
    if not year_end(state):
        return ""
    y = state["day"] // YEAR
    count = ("家族の代表の答えは、家族の大人みんなの答えとして数える。同じ名前を書いた人の家族の大人の数を足して、いちばん多い名前に決まる"
             if state["era2"].get("rep_mode") else "同じ名前を書いた人の数が、いちばん多い名前に決まる")
    return (f"\n## 年の名前 (1 年に 1 回)\n{y * YEAR}〜{state['day']} 日目の 1 年が終わった。村では、1 年ごとに、その年いちばん大きな出来事で"
            f"年に名前をつけ、口で伝えて覚えていく。この 1 年のおもな出来事:\n{_year_digest(state)}\n"
            f"この年の名前を、あなたの言葉で 1 つ書く (year_name、{YEAR_NAME_MAX} 字まで)。{count} (同じなら、書いた人でいちばん年上の人の名前)\n")


def _year_names_text(state):
    """村で覚えている年の名前 (古い年から)。まだなければ空 (お題は前と同じ)"""
    names = state["era2"].get("year_names") or []
    if not names:
        return ""
    last = (state["day"] + 1) // YEAR - 1
    rows = [f"- {x['year'] * YEAR}〜{x['year'] * YEAR + YEAR - 1} 日目の年: 「{x['name']}」" + (" (去年)" if x["year"] == last else "") for x in names]
    return "\n## 村で覚えている年の名前\n村では、年を、その年いちばん大きな出来事の名前で呼び、口で伝えて覚えている (古い年から)。\n" + "\n".join(rows) + "\n"


def _year_name(state, props, n):
    """年の名前を決める (props: [(答えた人, 名前, 家族の大人の数)]。n: 集まりの大人の数)"""
    e2, y = state["era2"], state["day"] // YEAR
    if not props or any(x["year"] == y for x in e2.get("year_names", [])):
        return
    w, by = {}, {}
    for p, t, k in props:
        w[t] = w.get(t, 0) + k
        by.setdefault(t, []).append(p)
    top = max(w.values())
    order = {id(q): i for i, q in enumerate(state["people"])}
    best = min((t for t in w if w[t] == top), key=lambda t: min((-q["age"], order[id(q)]) for q in by[t]))  # 同じなら、書いた人でいちばん年上
    eid = log(state, "年の名前", None, f"{y}年 ({y * YEAR}〜{state['day']} 日目) は「{best}」と呼ぶことになった "
              f"(同じ名前を書いた家族の大人 {top} 人分 / 大人 {n} 人)", year=y, name=best)
    e2.setdefault("year_names", []).append({"year": y, "name": best, "day": state["day"], "event": eid, "weight": top, "adults": n,
                                            "proposals": [{"who": p["name"], "name": t, "weight": k} for p, t, k in props]})


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
    # 家族の住まいを建てた日 (毎日の記録は家族ごとにまとめる。できた・広げたは下の出来事に出る。2026-10-08)
    build = {}
    for e in ev:
        h = (e.get("data") or {}).get("household")
        if e["type"] == "住まい" and h and "size" not in (e.get("data") or {}):
            build[h] = build.get(h, 0) + 1
    if build:
        rows.append("- 家族の住まいを建てた (人と日の数): " + "、".join(f"{h} {n}" for h, n in build.items()))
    village = [e for e in ev if e["type"] in ("生まれる", "死", "加わる", "去る", "訪れる", "畑", "ヤギ", "ヤギを食べる", "大人になる", "けが", "掟", "住まい", "フェーズ", "蓄えが尽きる", "家族", "虫", "区切り")
               and not (e["type"] == "住まい" and (e.get("data") or {}).get("household") and "size" not in (e.get("data") or {}))]
    rows += [f"- [出来事 {e['id']}] {e['text']}" for e in village[-25:] if e.get("who") != p["name"]]
    rains = [e for e in ev if e["type"] == "雨"]
    if rains:
        out = [e for e in rains if (e.get("data") or {}).get("outside")]
        me_out = sum(1 for e in out if p["name"] in e["data"]["outside"])
        rows.append(f"- 雨の夜 {len(rains)} 回" + (f" (村の住まいに入りきらず、外で濡れた人がいた夜 {len(out)} 回。あなたもそのうち {me_out} 回)" if out else ""))
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
            + _pasture_text(state)
            + (f"村の土器: {e2.get('pots', 0)} 個 (草の種 {e2.get('pots', 0) * POT_HOLD} つかみ分)、村の石の鎌: {e2.get('sickles', 0)} 本\n" if era_at_least(state, "G3") else "")
            + (_houses_text(state) if era_at_least(state, "G3") else "")
            + (_houses_line(state) if era_at_least(state, "G4") else "")
            + f"{wild} のあたりに、野生のヤギの群れ (約 {e2['wild_goats']['count']} 頭) がいる\n")


def _pasture_text(state):
    """草の量 (2026-10-10): 飼っているヤギが K の 8 割をこえたときだけ書く (それより少ないときのお題は前と同じ)"""
    n, cap = len(state["era2"]["goats"]), pasture_cap(state)
    if n > cap:
        return (f"草: 草原と丘の草で養えるヤギは 約 {cap} 頭。今は {n} 頭で、草が足りない (草が足りないと、春に生まれる子ヤギが減り、"
                "季節ごとに、多すぎる分の 3 分の 1 ほどがやせていなくなる。つぶして肉にすれば、ヤギは減る"
                + ("。ほかの村からヤギを受けとると、ヤギは増える" if state["era2"].get("g6") else "") + ")\n")
    if n * 10 >= cap * 8:
        return f"草: 草原と丘の草で養えるヤギは 約 {cap} 頭 (今は {n} 頭)。それより多くなると、草が足りなくなる\n"
    return ""


def _houses_line(state):
    e2 = state["era2"]
    rows = []
    for h in sorted({p.get("household") for p in state["people"] if p["alive"] and p.get("household")}):
        hs = _house(state, h)
        goats = sum(1 for g in e2["goats"] if g.get("owner") == h)
        rows.append(f"{h} (倉: {'持つ' if hs['keep'] else '持たない'}、{food_words(world.holdings({'food': hs['store']})) or 'からっぽ'}、ヤギ {goats} 頭)")
    return "家ごとの持ち物: " + "、".join(rows) + "\n"


FACTS_HOUSE = (f"家族の住まい: 村の住まい (キャンプのまん中) で眠れるのは {world.DWELL_CAP} 人まで。家族ごとに、キャンプのそばに四角い住まいを建てられる "
               f"(住まいを建てる。家族の大人が働いて、のべ 約 {HOUSE_HOURS} 時間でできる。そのあとも {HOUSE_HOURS} 時間ごとに 10 m² 広くなる)。家族の住まいのある家族は、そこで眠る。"
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
    j = 0  # 話し合える数に数えるもめごと (G6: 記録のあるものは数えない。G6 の前は i と同じ)
    for i, d in enumerate(op):
        age = (state["day"] - d["day"]) // SEASON_DAYS
        when = ("前の季節の終わりに起きた" if age == 0 else f"{age} 季節 収まっていない。この季節の集まりでも収まらないと、季節の終わりに、"
                + (f"{d['from']}が村を出ていくことがある" if age + 1 < DROP_AGE else "だれも言わなくなる"))
        rec = d.get("record")
        talk = ("" if lead and not rec else "。この季節の集まりで、記録を見て確かめる" if rec else "。この季節の集まりで話し合う" if j < TALK_MAX
                else f"。この季節の集まりでは話し合えない (古いものから {TALK_MAX} つまで)")
        j += 0 if rec else 1
        amt = (f"草の種にして {d['harm']} つかみ 分。{rec}の記録がある" if rec else f"言い出した家の覚えでは、草の種にして 約 {d['harm']} つかみ 分。記録はない"
               if "harm_true" in d else f"草の種にして 約 {d['harm']} つかみ 分")
        rows.append(f"- [{d['id']}] ({d['kind']}) {d['from']}が言い出した。相手は{d['against']} ({when}{talk}): {d['what']}"
                    f" ({amt}) [出来事 {d['event']}]")
    ev = [e for e in state["events"] if e["id"] >= since and e["type"] in G5_EVENTS]
    if ev:
        rows += ["この前の集まりから起きたこと:"] + [f"- [出来事 {e['id']}] {e['text']}" for e in ev[-12:]]
    if g.get("last_flow") and not era_at_least(state, "G6"):  # G6 では「ほかの村・印・記録」に (記録がなければ覚えの幅で)
        rows.append("前の季節の、家ごとの村の蓄えへの出し入れ (大人の分。草の種にして): "
                    + "、".join(f"{h} 入れた 約 {i}・取った 約 {o} つかみ" for h, (i, o) in g["last_flow"].items() if h in homes))
    return "\n## 村の集まり (もめごと・祭り" + ("・まとめ役" if two else "") + ")\n" + "\n".join(rows) + "\n"


FACTS_G6 = ("ほかの村: 村の外 (地図の外。歩いて 1〜2 日) にも、人の暮らす村がある。知っている村は「ほかの村・印・記録」に出る。"
            "ほかの村の人は、季節の終わりに村に来て、申し出をすることがある (交換したい / 食べ物を貸してほしい / 前に借りた分を返す)。"
            "交換したい・貸してほしいの申し出は、次の季節の集まりで決める (trade: 申し出の番号ごとに、村の物で受けるなら \"村\"、"
            "自分の家の倉の食べ物と家のヤギで受けるなら \"家\"、受けないなら false)。"
            "大人の半分をこえる人が \"村\" と答えるか、まとめ役が \"村\" と答えると、村の蓄え・村の土器・村の鎌・村のヤギで受け、手に入れた物は村のものになる。"
            "そうでなければ、\"家\" と答えた家の代表のうち、払える家で、家の倉の食べ物がいちばん多い家が受け、手に入れた食べ物とヤギはその家のものになる "
            "(土器・鎌・黒曜石は、いつも村のもの)。返す申し出は、決めずに受けとる。"
            "交換している村から「ここで暮らしたい」と人が来ることもある (よそから来た人と同じく、受け入れるかを決める)\n"
            "交換に行く: 主な仕事を「交換に行く」(camp) にすると、季節のはじめの日に、知っているほかの村へ、ほかの村がほしがる物 (村の草の種・土器・鎌) を持って出かける "
            "(to: 村の番号、carry: 持って行く物と数、want: ほしい物、then: 帰ってからの仕事)。"
            f"1 人が持てるのは、草の種なら {LOAD['草の種']} つかみ、土器なら {LOAD['土器']} 個、鎌なら {LOAD['鎌']} 本ほど "
            "(2 つ持つときは、それぞれ半分ずつ)。"
            "歩いて 1 日の村なら、行く・交換する・帰るで 3 日、2 日の村なら 5 日かかる。歩く日はおなかが多くすく。帰り道で物をなくしたり、けがをしたりすることがある。"
            "向こうの村は、その季節にほしい分だけを受けとり、want の物 (なければほかの物) で払う。受けとらなかった物は持ち帰る。払いきれない分は、あとで返す約束 (貸し借り) になる。"
            "家の代表は、家の倉の草の種を持って行かせることもできる (house: true。家族の住まいのある家だけ。手に入れた食べ物とヤギは家のもの)\n"
            f"値うち: 交換では、草の種にして、ヤギ 1 頭 = {VALUE['ヤギ']} つかみ、鎌 1 本 = {VALUE['鎌']} つかみ、土器 1 個 = {VALUE['土器']} つかみ、"
            f"黒曜石 1 個 = {VALUE['黒曜石']} つかみ、干し肉 1 切れ = {VALUE['干し肉']} つかみ ほどとして釣り合わせる\n"
            "覚え: 記録のない量 (家ごとの村の蓄えへの出し入れ・もめごとの量・貸し借りの量) は、人の覚えにたよるので、はっきりしない。"
            "村の家が多いほど、ほかの村との貸し借りが多いほど、覚えはずれる。もめごとを言い出した家は、損を多めに覚えていることがある。"
            "覚えた量で払うと、払った家が「多く払った」と言い出すことがある (もめごとのもと (5) 覚え)\n"
            "印: 家の代表は、家の印 (焼いた粘土に形を刻んだもの) を作れる (seal)。印のある家の倉は、口を粘土でふさいで印を押しておく (封)。封は割らずには開けられない。"
            "よその家の人が開けると、封が割れているので分かり、必ずもめごとになる。"
            "大人の半分をこえる人か、まとめ役が望むと (seal_store)、この季節は村の蓄えの土器にも封をする。そのときは、取るたびに封を割り、取った人の家の印で封をし直す。"
            "割った封のかけらは取っておくので、どの家が何日開けたかが分かる (量は分からない)\n")

FACTS_TOKEN = ("数え札: 粘土を小さく丸めたり形をつけたりした札で、量を数えて残せる (草の種 100 つかみ分に 1 個、ヤギ 1 頭に 1 個、土器・鎌・黒曜石 10 個に 1 個、"
               "働いた日 10 日に 1 個)。主な仕事を「記録をつける」(camp) にすると、この季節の出し入れを残す (what: 残すもの。"
               "「蓄え」= 家ごとの村の蓄えへの出し入れと、作る人などの働いた日、「交換」= ほかの村との交換と貸し借り、「刈る」= よその家の畑で刈った量。"
               "書いた順に残す。how: \"数え札\")。"
               f"1 人が 1 日に作って数えられる数え札は {RATE['数え札']} 個ほどで、足りないと途中までしか残らない。"
               "全部残せた量ははっきり分かる。その量のもめごとは、季節の集まりで記録を見て確かめる (話し合える 2 つには数えない)。"
               "記録のある貸し借りは、返しに来たときに、正しい数が分かる (足りない分は、あとで返す約束のまま残る)。"
               "村の蓄えの出し入れを全部残せた季節は、作る人・記録をつける人・交換に行った人の働いた日を、1 日を大人 1 人の 1 日分として、その家が村の蓄えに入れた量に数える\n")

FACTS_ENVELOPE = ("封筒: 記録をつける人が how を \"封筒\" にして「交換」を残すと、その季節の貸し借りの数え札を粘土の玉に入れて閉じ、外に印を押しておく。"
                  "返しに来たときに玉を割ると、約束した数がどちらにも分かり、その数が返される\n")

FACTS_TABLET = (f"粘土の板: 数え札を 1 つずつ作るかわりに、平たい粘土の板に、物を表すしるし (草の種・ヤギ・土器 など) と、数を表すしるしを分けて押して記せる (how: \"板\")。"
                f"1 人が 1 日に、数え札 {RATE['板']} 個分ほどを記せる。板に記した量も、数え札と同じように確かめるのに使える。"
                "板で記した貸し借りは、封筒と同じく、どちらにも数が分かる\n")

FACTS_OBSIDIAN = ("黒曜石: 黒く光る石で、割ると鋭い刃になる。村に黒曜石があると、道具づくりで作る鎌に黒曜石の刃をはめる (鎌 1 本に 1 個)。"
                  "黒曜石の刃の鎌は、割れにくい (半分ほど)\n")


def _g6_facts(state):
    if not era_at_least(state, "G6"):
        return ""
    g = state["era2"].get("g6") or {}
    op = g.get("open") or {}
    obs = USE_OBSIDIAN and (g.get("obsidian") or any(o.get("has_obsidian") and o["known"] is not None for o in g.get("others", [])))
    return (FACTS_G6 + (FACTS_TOKEN if op.get("数え札") else "") + (FACTS_ENVELOPE if op.get("封筒") else "")
            + (FACTS_TABLET if op.get("板") else "") + (FACTS_OBSIDIAN if obs else ""))


def _g6_rw(x):
    return "ほとんどなし" if x[1] == 0 else f"約 {x[0]}〜{x[1]} つかみ"


def _g6_text(state):
    """G6 のお題の節 (見ればわかる事実だけ。状態は変えない)"""
    if not era_at_least(state, "G6"):
        return ""
    g = state["era2"].get("g6") or {}
    homes = _homes(state)
    rows = []
    known = [o for o in g.get("others", []) if o["known"] is not None]
    rows.append("知っているほかの村:" + ("" if known else " まだない"))
    for o in known:
        who = f"前に村を出た{o['household']}の人たちが暮らす" if o["kind"] == "分かれた家" else "よその村"
        has = "・".join(k for k, n in _g6_supply(o).items() if n > 0) or "目立つ物はない"
        last = max(o["contacts"]) if o["contacts"] else None
        rows.append(f"- [{o['id']}] {_okey(o)}: {who}。人 約 {max(5, 5 * round(o['people'] / 5))} 人。出せる物: {has}。ほしがる物: {'・'.join(_g6_cap(o))}。"
                    f"はじめて知った日 {o['known']} 日目。交換した季節 {len(o['contacts'])} 回" + (f" (最後は {last} 日目)" if last else "")
                    + ("。この年は畑が実らず苦しいと言っていた" if o["bad"] is not None else ""))
    offers = g.get("offers", [])
    if offers:
        rows.append("この季節の集まりで決める申し出 (trade。返す申し出は、決めずに受けとる):")
        for off in offers:
            o = _other(state, off["other"])
            rows.append(f"- [{off['id']}] {o['name']}: " + {"交換": f"{_gw(off['give'])} を出すので、{_gw(off['want'])} がほしい",
                                                          "貸して": f"{_gw(off['want'])} を貸してほしい (1 年のうちに同じ量を返す)",
                                                          "返す": f"[{off.get('debt')}] の分として {_gw(off['give'])} を返しに来た"}[off["kind"]])
    debts = [d for d in g.get("debts", []) if d["status"] == "まだ"]
    if debts:
        rows.append("まだ返されていない貸し借り:")
        for d in debts:
            o = _other(state, d["other"])
            amt = (f"{_gw(d['goods'])} ({d['proof']}の記録がある)" if d.get("proof")
                   else "覚えでは " + _gw({k: math.ceil(n * d["mem"]["village"]) for k, n in d["goods"].items()}) + " ほど (記録はない)")
            rows.append(f"- [{d['id']}] {o['name'] if o else 'ほかの村'} が{'村' if d['lender'] == '村' else d['lender']}に返す分: {amt}。{d['day']} 日目から")
    seals = g.get("seals", {})
    rows.append("家の印: " + ("、".join(f"{h} ({v['day']} 日目から)" for h, v in sorted(seals.items()) if h in homes) or "まだない")
                + ("。印のない家: " + ("、".join(h for h in homes if h not in seals) or "なし") if seals else ""))
    if g.get("store_sealed") is not None and g.get("store_sealed") == state["era2"].get("step_day"):
        rows.append("前の季節は、村の蓄えに封をした")
    rec = g.get("records", [])
    last = rec[-1] if rec and rec[-1]["day"] == state["day"] else None
    if last:
        rows.append("前の季節の記録 (" + "、".join(f"{n} {d} 日・{h}" for n, (d, h) in last["keepers"].items()) + "): "
                    + ("、".join(f"{WHAT_WORDS[w]} は{'全部残せた' if w in last['complete'] else '途中までしか残せなかった'}"
                                for w in WHATS if last["need"][w] and last["done"][w]) or "残せたものはなかった"))
    else:
        rows.append("前の季節の記録: なし")
    op = g.get("open") or {}
    rows.append("使える記録の道具: " + ("・".join(k for k in ("印", "数え札", "封筒", "板") if op.get(k)) or "印"))  # G6 の最初のお題 (g6 を作る前) も「印」
    if g.get("obsidian") or g.get("obs_sickles"):
        rows.append(f"村の黒曜石: {g['obsidian']} 個 (黒曜石の刃の鎌 {g['obs_sickles']} 本)")
    sh = g.get("shown")
    if sh and sh["rows"]:
        if sh["how"]:
            rows.append(f"前の季節の、家ごとの村の蓄えへの出し入れ ({sh['how']}の記録による。大人の分。草の種にして): "
                        + "、".join(f"{h} 入れた {i}・取った {o_} つかみ" for h, (i, o_) in sh["rows"].items() if h in homes))
        else:
            rows.append("前の季節の、家ごとの村の蓄えへの出し入れ (記録はない。みんなの覚えでは、だいたい。大人の分。草の種にして): "
                        + "、".join(f"{h} 入れた {_g6_rw(i)}・取った {_g6_rw(o_)}" for h, (i, o_) in sh["rows"].items() if h in homes))
    ev = [e for e in state["events"] if e["id"] >= (g.get("meet_first") or state["next_event"]) and e["type"] in G6_EVENTS]
    if ev:
        rows += ["この前の集まりから起きたこと (ほかの村・印・記録):"] + [f"- [出来事 {e['id']}] {e['text']}" for e in ev[-12:]]
    return "\n## ほかの村・印・記録\n" + "\n".join(rows) + "\n"


def _g6_now(state, p, solo, n=8):
    """お題の「いま」の G6 の項目 (n はその番号。G6 の前は空)"""
    if not era_at_least(state, "G6"):
        return ""
    g = state["era2"].get("g6") or {}
    offers = [o for o in g.get("offers", []) if o["kind"] != "返す"]
    rows = [f"{n}. ほかの村・印・記録 (上の「ほかの村・印・記録」を見て決める。どれも書かなくてもよい)"]
    if offers:
        rows.append("   申し出: 申し出の番号ごとに、村の物で受けるなら \"村\"" + ("" if solo else "、自分の家の物で受けるなら \"家\"") + "、受けないなら false (trade)")
    if not solo and p.get("household") and p["household"] not in g.get("seals", {}):
        rows.append("   印: 家の印を作るなら true (seal。家ごとに 1 回だけ)")
    rows.append("   村の蓄えの封: この季節、村の蓄えに封をするなら true、しないなら false (seal_store)")
    if any(o["known"] is not None for o in g.get("others", [])):
        rows.append('   交換に行く: 主な仕事を「交換に行く」にする人は、job か family に、to (村の番号)・carry (持って行く物と数)・want (ほしい物)・then (帰ってからの仕事) を書く。'
                    '例 {"activity": "交換に行く", "place": "camp", "to": "N1", "carry": {"土器": 4}, "want": "ヤギ", "then": "採集"}')
    op = g.get("open") or {}
    if op.get("数え札"):
        hows = " / ".join(h for h in ("数え札", "封筒", "板") if op.get(h))
        rows.append(f'   記録をつける: 主な仕事を「記録をつける」にする人は、what (残すもの: 蓄え・交換・刈る。書いた順に残す) と how ({hows}) を書く。'
                    '例 {"activity": "記録をつける", "place": "camp", "what": ["蓄え", "交換", "刈る"], "how": "数え札"}')
    return "\n".join(rows) + "\n"


def _g6_json(state, p, solo):
    if not era_at_least(state, "G6"):
        return ""
    g = state["era2"].get("g6") or {}
    offers = [o["id"] for o in g.get("offers", []) if o["kind"] != "返す"]
    return (('"trade": {' + ", ".join(f'"{i}": "..."' for i in offers) + "}, " if offers else "")
            + ('"seal": false, ' if not solo and p.get("household") and p["household"] not in g.get("seals", {}) else "")
            + '"seal_store": false, ')


def season_prompt(state, p, first):
    e2 = state["era2"]
    g5, g = era_at_least(state, "G5"), e2.get("g5") or {}  # G5 の部分は、G5 の前はみな空の文字 (お題は前と同じ)
    lead, two = g.get("leader"), g.get("stage", 1) >= 2
    solo = bool(g5 and e2.get("rep_mode") and p["name"] not in _reps(state))  # 家族の代表でないまとめ役 (自分の分だけ答える)
    g6 = era_at_least(state, "G6")  # G6 の部分は、G6 の前はみな空の文字
    places = "\n".join(f"- {pl['id']}: {pl['label']}" for pl in state["places"])
    names = [q["name"] for q in adults(state) if q is not p]
    vis = ""
    if e2["visitors"] and g6:  # G6: 群れが 2 つ以上のこともある (ほかの村から来た人)
        rows = []
        for v in e2["visitors"]:
            o = _other(state, v.get("from")) if v.get("from") else None
            rows.append("- " + "、".join(f"{m['name']} ({m['sex']}、{m['age']} 歳)" for m in v["members"]) + (f" ({o['name']} から来た)" if o else " (よその群れ)"))
        vis = ("\n## よそから来た人\n" + "\n".join(rows) + "\nそれぞれ「ここで暮らしたい」と言っている (1 行が、いっしょに来た一つの群れ)。群れごとに、村に受け入れるか決めてください "
               "(accept: 群れの最初の人の名前ごとに、受け入れるなら true、受け入れないなら false)。大人の半分をこえる賛成で、その群れの全員が村に加わる。"
               "加わった大人は、この季節は村でいちばん多い仕事をし、次の季節から自分で決める\n")
    elif e2["visitors"]:
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
    if g6 and e2["visitors"]:
        acc = '"accept": {' + ", ".join(f'"{v["name"]}": true' for v in e2["visitors"]) + "}, "
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
                   f"\n- 掟の投票と、よそから来た人の受け入れ{('、もめごとの収め方・祭り' + ('・まとめ役' if two else '') + ('・申し出 (trade)・村の蓄えの封' if g6 else '') + 'の答え') if g5 else ''}は、家族の大人みんなの答えとして数える\n")
        if fam:
            fam_json = '"family": {' + ", ".join(f'"{q["name"]}": {{"activity": "採集", "place": "camp"}}' for q in [q for q in fam if q["name"] != lead][:2]) + '}, '

    if solo:
        fam_txt = (f"\n## あなたはまとめ役\nあなたは {p.get('household')} の代表ではないが、村のまとめ役なので、季節の集まりで答える。決めるのは自分の仕事だけ "
                   "(家族の仕事・家の倉・ヤギをつぶす数は、家族の代表が決める)。掟の投票・受け入れ・もめごとの収め方・祭り・まとめ役"
                   + ("・申し出 (trade)・村の蓄えの封" if g6 else "") + "の答えは、あなた一人の答えとして数える\n")
    op = [d["id"] for d in g.get("disputes", []) if d["status"] == OPEN] if g5 else []
    me5 = g5 and lead == p["name"]
    g5_now = ("7. 村の集まり (上の「村の集まり」を見て決める。どれも書かなくてもよい)\n"
              + ("   もめごと: まだ収まっていないもめごとの収め方を、番号ごとに「つぐなう」か「ゆるす」で書く (judge)\n" if op else "")
              + "   祭り: この季節のはじめに、村の全員で祭りをするか (feast: するなら true、しないなら false)\n"
              + ("   まとめ役: まとめ役にしたい人の名前を書く (leader。まとめ役はいらないなら「なし」、決めないなら null)\n"
                 '   罰: 掟を提案するときに罰をつけるなら、proposal の penalty に {"for": "ヤギ" か "倉" か "蓄え" か "刈る", "pay": 草の種のつかみ} を書く (つけないなら null か、pay を 0 のまま)\n'
                 if two else "")
              + ("   あなたは村のまとめ役。あなたの家のものでないもめごとは、あなたの judge で決まる。次の季節にみんなでする仕事を 1 つ呼びかけられる (call: 仕事の名前。しないなら null)\n"
                 if me5 else "")) if g5 else ""
    g5_json = ("\n " + ('"judge": {' + ", ".join(f'"{i}": "..."' for i in op) + "}, " if op else "") + '"feast": false, '
               + ('"leader": "...", ' if two else "") + ('"call": null, ' if me5 else "")) if g5 else ""
    # 2026-10-09 (2909 日目、本人「お任せします」→ 案 B): 罰の例を null から欄の形に。null の例をそのまま写して、第 2 段の 30 季節で罰のある掟の提案が 0 だったため。
    #   例のまま (pay 0) は _penalty が罰なしにする。世界の仕組みは変えない (つけるかは人が決める)
    pen = ', "penalty": {"for": "...", "pay": 0}' if g5 and two else ""
    n6 = 7 + bool(g5_now)  # G6 の「ほかの村・印・記録」の番号 (G6 では 8)
    g6_now, g6_json = _g6_now(state, p, solo, n6), _g6_json(state, p, solo)  # G6 の前は空
    rec6 = g6 and ACT_RECORD in acts2(state)  # 記録をつけるは、数え札が使えるようになってから書く (使えない道具のことは書かない。2026-10-09 試し回し)
    g6_act = (f"   交換に行く{'・記録をつける' if rec6 else ''}は camp と書く (行き先・持って行く物{'・残すもの' if rec6 else ''}は {n6}. に書く)\n"
              if g6 else "")
    ye = year_end(state)  # 年の終わりの集まり: 年の名前を決める (ほかの集まりでは、お題は前と同じ)
    yname_now = f"{7 + bool(g5_now) + bool(g6_now)}. この 1 年の名前を決める (year_name。上の「年の名前」を見て)\n" if ye else ""
    yname_json = ' "year_name": "...",\n' if ye else ""

    return f"""{RULES2}

{me}{FACTS2}{(FACTS_G3 + FACTS_HOUSE) if era_at_least(state, "G3") else ""}{FACTS_G4 if era_at_least(state, "G4") else ""}{_g5_facts(state)}{_g6_facts(state)}
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
{_year_names_text(state)}{_g5_text(state)}{_g6_text(state)}{vis}{_year_end_text(state)}
## いま
{state["day"] + 1} 日目、{sea}。これから {SEASON_DAYS - (state["day"] + 1) % SEASON_DAYS} 日 (この季節の終わりまで) の仕事を決める集まり (途中で村の蓄えが尽きて、ひどく空腹の人が出たら、そこで集まり直す)。
1. 話したいことがあれば話す (0〜2 つ。相手は仲間の名前か「みんな」)。前と同じ言い回しをくり返さず、あなたらしい言葉で
2. この季節の主な仕事を決める (job)。仕事は {' / '.join(acts2(state))} から 1 つ、場所は下の一覧の id から 1 つ、一緒に行きたい人 ({'、'.join(names) or 'なし'}) がいれば書く
   畑仕事 (草取り・刈り入れ) は camp で行う
   ヤギの世話は camp で行う。ヤギを捕まえるは、野生のヤギのいる場所で行う
{g6_act}3. {(pick.strip().rstrip('。') + '。取るのはこの季節の毎夕で、1 人 40 つかみまで') if pick.strip() else 'この季節 (' + sea + ') は、キャンプのそばの木から実は取れない (実がなるのは夏と秋)'}
4. 持っている木の実 (なければ村の蓄えの木の実) を、この回の最初の日にキャンプのそばに埋める (plant、つかみ、5 まで) こともできる
   秋なら、季節のはじめに、蓄えの草の種をキャンプのそばの畑にまく量 (sow、つかみ、1000 まで) を書ける (主な仕事とは別にできる)
   実った畑があれば、毎夕いくつ刈るか (harvest、つかみ、60 まで) を書ける (主な仕事とは別にできる)
{'   飼っているヤギを、この回の最初の日に何頭つぶして肉にするか (eat_goat、頭。肉は干して蓄えに入れる。2 頭は残す' + ('。1 つの答えで 5 頭まで' if len(e2['goats']) > pasture_cap(state) else '') + ') を書ける' + chr(10) if e2['goats'] and not solo else ''}
{'   家の倉を持つか (keep: 持つなら true、持たないなら false) を決める (家の代表が決める)' + chr(10) if era_at_least(state, "G4") and not solo else ''}5. 覚えていることを更新する (新しく分かったことを追加、確かさを変える、間違っていたら忘れる)
6. 掟: みんなで守りたい決まりがあれば提案できる (なければ null)。今の掟と提案に、賛成か反対かを投票する (against に反対する理由、reason に決めた理由)
{g5_now}{g6_now}{yname_now}{7 + bool(g5_now) + bool(g6_now) + ye}. 今の気持ちを一言

場所の一覧:
{places}

## 答えの形 (JSON)
{{"say": [{{"to": "みんな", "text": "..."}}],
 "job": {{"activity": "採集", "place": "camp", "with": []}}, {sow}"pick": 0, "plant": 0, "harvest": 0, {goat}{acc}{fam_json}{keep}{g5_json}{g6_json}
 "knowledge": [{{"op": "add", "text": "...", "because": [出来事の番号], "confidence": 0.6}}],
 "proposal": {{"text": "...", "because": [出来事の番号]{pen}}},
 "votes": [{{"id": "L0", "against": "反対する理由", "agree": true, "reason": "決めた理由"}}],
{yname_json} "feeling": "..."}}"""
