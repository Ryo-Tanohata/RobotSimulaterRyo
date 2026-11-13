"""G13「帝国のあとの農業社会」(第 7 部「帝国のあとと町」のはじめの G。2026-11-12 本人の決め「おすすめどおりで進める」。docs/society_phase/G13_design.md)

- G13 に入るのは step.py next_part だけ (G12 の 3 つの条件がそろって第 6 部が終わり、HOLD part_end で止まったところから。g7.close_g12 → g7.enter_next → g7.start_g13)。
  G12 までは、このファイルを読みこみもしない (g7・era2・hints・yardstick・g12 は state の g7.g13 があるときだけ、関数の中で読みこむ)。
  だから G1〜G12 は、お題・state・出来事・乱数が前と 1 バイトも変わらない
- 計画の 3 本 (水か家畜の力の粉ひき・畑の回し方・土地を持つ家への義務) を、この村の形「水と畑と務め」で測る。条件 (3 つとも【村が決めた】。3 つそろうと G13 の終わり。
  第 7 部は G14 まで続くので、G14 のコードがなければ HOLD wait):
  c1 水の力の粉ひき: 暦の 1 年に、村の水の輪が 90 日以上回り、村の粉ひきの半分以上を引き受けた。1 回でよい
  c2 水の来る畑: 秋にまいた草の種のうち、水の来る畑にまいた分が半分以上の年が 2 年つづく
  c3 務め: 暦の 1 年に、なくなっていない地域の集落の半分以上が、村に約束の分 (草の種・黒曜石) か働き手を出した年が 2 回 (つづかなくてよい。G13 に入ってからの年だけ)
- F: F1 はじめて水の道を掘った / F2 水の輪を試しはじめた / F3 水の輪が回った / F4 よその集落の働き手が、はじめて村で働いた
- 足す仕組み (乱数なし): 粉ひきの手間 (史実のずれの直し。1 人 1 日 0.25 時間を、家の大人の次の日の働く時間から引く。水の輪がひいた分は引かない)・
  仕事「水の道を掘る」(1 人日で秋にまく草の種 60 つかみ分の畑に水が来る。水の来る畑は村の悪い年でも半分にならない。1 年に手入れ 1 割)・
  札 H12-01 の前提を G13 から「そろっている」と読む (hints.NEEDS_G13。入る日に開く)・仕事「水の輪を建てる」(できるようになったあと 80 人日で 1 つ。1 つで 250 人分。1 年 10 人日直す)・
  倉の約束の take の「働き手」(g12.WORKERS。刈り入れの季節は刈り、ほかの日は水の道を掘る)
- 決め方: 仕事は今のまま 1 人ずつ (その人か家の代表)。働き手は G12 の pact (いちばん多い手。1 人でも決まる)。水の輪は村のもの (建てた人と家は記録する)
- G12 までの仕組み (黒い金属・字・印のかたまり・市の日・倉の約束・倉から助ける・帳・刈り手・直し) は動きつづける。G12 の条件は「ならべて測る」
- 暦の年: 帳簿は日 ÷ 120 (g12 と同じ)。道の見張りの行だけ (日 + 1) ÷ 120 (g12.count_paths と同じ)
- 村の人に見せる文には「領主」「荘園」「封建」「農奴」「国」「税」「帝国」「都」と g12.WORDS を書かない (WORDS。試しで確かめる)。
  呼び名は「水の輪」「水の道」「水の来る畑」「粉ひき」「約束の分」「働き手」
"""
import json

import era2
import g10
import g12
import hints
from world import log

YEAR, SEASON_DAYS = era2.YEAR, era2.SEASON_DAYS
CARD = "H12-01"  # 札「川の力で粉をひく輪」
ACT_CANAL, ACT_MILL = "水の道を掘る", "水の輪を建てる"  # 新しい仕事 (world.ACTS7 に足した)
WORKERS = g12.WORKERS
GRIND_H = 0.25  # 1 人 1 日の分の粉をひく時間 (回す石臼として)【仮定】
GRIND_ON = True  # 粉ひきの手間 (決まりの村の B1G だけ False にする。本物ではいつも True)
CANAL_PER_DAY = 60  # 水の道: 1 人日で、秋にまく草の種 60 つかみ分の畑に水が来る (1 ha に 100 人日・1 ha に種 約 6,000 つかみ)【仮定】
CANAL_KEEP, CANAL_LOSS = 0.1, 0.2  # 手入れ: 1 年に、掘った人日の合わせた量 (cap ÷ 60) の 1 割を掘らなければ、cap が 2 割へる【仮定】
MILL_DAYS, MILL_KNOW = 80, 1.5  # 水の輪: 80 人日で 1 つ。札を知っている人 (か試した人) は 1.5 倍はかどる【仮定】
MILL_PEOPLE = 250  # 水の輪 1 つが 1 日にひく分 (村の人 250 人分。ドゥームズデイの「家 46〜50 に水車 1 つ」から)【二次・仮定】
MILL_REPAIR = 10  # 水の輪 1 つを 1 年に直す人日。足りなければ次の年は止まり、止まった輪は 10 人日で動き直す【仮定】
C1_DAYS, C1_SHARE = 90, 0.5  # c1: 1 年に 90 日以上回り、粉ひきの半分以上【仮定】
C2_SHARE, C2_YEARS = 0.5, 2  # c2: 秋のまきつけの半分以上が水の来る畑の年が 2 年つづく【仮定】
C3_SHARE, C3_TIMES = 0.5, 2  # c3: 地域の集落の半分以上が出した年が 2 回【仮定】
PATH_YEARS = 2  # 道の見張り: 選べる答える人が 2 年つづけて 0 人なら止めて相談
IDLE_YEARS = 3  # 選べた人はいるのに、だれも選ばなかった年がつづいたら報告 (止めない)
FAIL_REPORT = 3  # 1 年に「選んだのにできなかった」がこれだけあれば、報告に書く
LATER_YEARS = 5  # 5 年ごとの相談 (G13 に入った日から)
WORDS = ("領主", "荘園", "封建", "農奴", "国", "税", "帝国", "都") + g12.WORDS  # 村の人に見せる G13 の文に書かない言葉
FS = {"F1": "はじめて水の道を掘った", "F2": "水の輪を試しはじめた", "F3": "水の輪が回った", "F4": "よその集落の働き手が、はじめて村で働いた"}
CS = {"c1": "水の力の粉ひき", "c2": "水の来る畑", "c3": "務め"}
BLOCK_HEAD = "水と畑と務め・倉と約束と帳: この集まりで、あなたができること (どれも、しなくてもよい。書かなければ今のまま)"
BAD_LAST = 167  # 入る前の、いちばん新しい村の悪い年 (お題の例。G13_design.md 0.1)


def on(state):
    return "g13" in ((state.get("era2") or {}).get("g7") or {})


def _g(state):
    return state["era2"]["g7"]["g13"]


def _y(state):
    return state["day"] // YEAR


def _others(state):
    import g7
    return g7._others(state)


def _other(state, oid):
    return next((o for o in _others(state) if o["id"] == oid), None)


def _tech(state):
    return ((state["era2"]["g7"].get("hints") or {}).get("tech") or {}).get(CARD) or {}


def _card_name():
    return hints.cards()[CARD]["name"]


# ---------------- G13 に入る (g7.start_g13 から) ----------------

def start(state):
    """G13 の state を作る: G12 の物差し (条件・F・道の見張り・帳簿) を g7.before.G12.g12 に写し、条件と道の見張りは数え直す
    (F は村に起きたことなので消さない。G12 のときと同じ)。札 H12-01 の前提がそろうので、待っていれば入る日に開く (出来事「試す」)。
    粉ひき・水の道・水の輪・働き手は入る日から"""
    g7s, D = state["era2"]["g7"], state["day"]
    t = g7s["g12"]
    g7s.setdefault("before", {}).setdefault("G12", {})["g12"] = {
        "reached": dict(t["reached"]), "c": dict(t["c"]), "c1_years": list(t["c1_years"]), "path": {k: dict(v) for k, v in t["path"].items()},
        "prompt_fix": t.get("prompt_fix"), "city_half": t.get("city_half")}
    t["c"], t["path"] = {}, {}
    g = g7s["g13"] = {"start": D, "grind": {}, "mill": {"mills": [], "work": 0.0, "repair": {}, "year": {}, "by": {}},
                      "canal": {"cap": 0, "dug": {}, "by": {}, "lost": []}, "water": {}, "protected": {}, "workers": {},
                      "c2_years": [], "c3_years": [], "c3_rows": {}, "reached": {}, "c": {}, "fails": [], "path": {}, "ledger": [], "opened": None}
    h = g7s.get("hints") or {}
    tc = (h.get("tech") or {}).get(CARD)
    if tc and tc.get("open") is None and hints.needs_ok(state, hints.cards()[CARD].get("needs")):  # 入る日に開く (G10 の札と同じ。季節の終わりを待つと 1 季節おくれる)
        tc["open"] = D
        g["opened"] = D
        log(state, "試す", None, f"よその便りで聞いた「{_card_name()}」に要るもの (粉をひく・木を組む) が村にそろい、試せるようになった", card=CARD)
    log(state, "水", None, f"G13 から、草の種は粉にしてから食べる (1 人 1 日の分をひくのに 約 {round(GRIND_H * 60)} 分。家の大人の働く時間から引かれる)。"
        "前の世界では、この手間を数えていなかった", grind=GRIND_H)
    return g


# ---------------- 粉ひき (era2._day の夕方から。毎日) ----------------

def mills_running(state):
    return [m for m in _g(state)["mill"]["mills"] if not m.get("stopped")]


def evening(state):
    """その日の粉ひき: 水の輪が回っていれば 1 つで 250 人分をひく。残りは家ごとに、その家の人数分を、家の大人の次の日の働く時間から引く (world の eve_h)。乱数なし"""
    g, D = _g(state), state["day"]
    alive = [p for p in state["people"] if p["alive"]]
    pop = len(alive)
    if not pop:
        return
    y = str(D // YEAR)
    run = mills_running(state)
    milled = min(pop, MILL_PEOPLE * len(run))
    my = g["mill"]["year"].setdefault(y, {"days": 0, "milled": 0, "need": 0})
    my["need"] += pop
    my["milled"] += milled
    if run:
        my["days"] += 1
        if "F3" not in g["reached"]:
            _reach(state, "F3", D, f"水の輪が川の力で、村の {milled} 人分の粉をひいた")
    gr = g["grind"].setdefault(y, {"hours": 0.0, "people": 0, "milled": 0, "no_adult": 0})
    gr["people"] += pop
    gr["milled"] += milled
    if not GRIND_ON:
        return
    frac = 1 - milled / pop
    if frac <= 0:
        return
    homes = {}
    for p in alive:
        h = p.get("household")
        if h:
            r = homes.setdefault(h, [0, []])
            r[0] += 1
            if not p.get("child"):
                r[1].append(p)
    tot = 0.0
    for h in sorted(homes):
        n, ads = homes[h]
        if not ads:
            gr["no_adult"] += n
            continue
        hrs = round(GRIND_H * n * frac / len(ads), 2)
        for p in ads:
            p["eve_h"] = round(p.get("eve_h", 0) + hrs, 2)
        tot += hrs * len(ads)
    gr["hours"] = round(gr["hours"] + tot, 2)


# ---------------- 仕事: 水の道を掘る・水の輪を建てる (g7.role_day から) ----------------

def mill_ready(state):
    """札 H12-01 の「試す」が終わって、村で水の輪を建てられるか"""
    return bool(_tech(state).get("done"))


def can_do(state, act):
    if act == ACT_CANAL:
        return True
    if act == ACT_MILL:
        return mill_ready(state) or bool(_g(state)["mill"]["mills"])
    return False


def acts(state):
    return [a for a in (ACT_CANAL, ACT_MILL) if can_do(state, a)]


def rest_why(state, name, act):
    """水の仕事を「休む」に変えたわけ (村の人に見せる短い文)。入る日からいつも残す"""
    if act == ACT_MILL and not can_do(state, act):
        return (f"{name} は、村でまだ水の輪を建てられないので、休んだ (「{_card_name()}」[{CARD}] を試して、できるようになってから建てられる)")
    return None


def try_rest_why(state, name):
    """札 H12-01 の「試す」を「休む」に変えたわけ (できるようになったあと。前は g10 の「いまは村で試せない」になり、わけが分かりにくかった)"""
    if mill_ready(state):
        return f"{name} は、「{_card_name()}」[{CARD}] はもう村でできるようになったので、試さずに休んだ (主な仕事を「{ACT_MILL}」にすると、水の輪を建てられる)"
    return None


def knower(state, name):
    p = next((q for q in state["people"] if q["name"] == name), None)
    return bool(p) and (hints.knows(state, name, CARD) or p["skills"].get(f"試す:{CARD}", 0) > 0)


def dig(state, n, who):
    """水の道を n 人日掘る (村の人の仕事か、約束の働き手)"""
    g, D = _g(state), state["day"]
    c = g["canal"]
    y = str(D // YEAR)
    c["cap"] += n * CANAL_PER_DAY
    c["dug"][y] = c["dug"].get(y, 0) + n
    k = who or "働き手"
    c["by"][k] = c["by"].get(k, 0) + n
    _reach(state, "F1", D, f"{who or 'よその集落の働き手'} が、川から村の畑へ水の道を掘った")


def _mill_due(state):
    """この暦の年に、まだ直す人日 (年のはじめからあった、回っている輪 × 10 から、この年に直した分を引く)"""
    g, D = _g(state), state["day"]
    y = D // YEAR
    old = [m for m in mills_running(state) if m["day"] // YEAR < y]
    return max(0.0, MILL_REPAIR * len(old) - g["mill"]["repair"].get(str(y), 0.0))


def work_day(state, p, t, act):
    """1 日: 水の道を掘る (cap に 60 つかみ分) / 水の輪を建てる (止まった輪を動かす → この年の直し → 新しい輪)"""
    g, D = _g(state), state["day"]
    name = p["name"]
    if act == ACT_CANAL:
        dig(state, 1, name)
        t.setdefault("events", []).append(log(state, ACT_CANAL, name, f"{name} が、川から村の畑へ水の道を掘った", canal=CANAL_PER_DAY))
        return
    if not can_do(state, act):
        why = rest_why(state, name, act)
        t.setdefault("events", []).append(log(state, "休む", name, why, rest_why=act))
        if not any(f["who"] == name and f["what"] == act and f["day"] // SEASON_DAYS == D // SEASON_DAYS for f in g["fails"]):
            _fail(state, name, act, why, log_it=False)
        return
    m = g["mill"]
    rate = MILL_KNOW if knower(state, name) else 1.0
    m["by"][name] = round(m["by"].get(name, 0) + rate, 2)
    y = str(D // YEAR)
    stopped = [x for x in m["mills"] if x.get("stopped")]
    if stopped:
        x = stopped[0]
        x["fix"] = round(x.get("fix", 0) + rate, 2)
        txt = f"{name} が、止まっている水の輪を直した"
        if x["fix"] >= MILL_REPAIR:
            x["stopped"], x["fix"] = None, 0
            m["repair"][y] = round(m["repair"].get(y, 0.0) + MILL_REPAIR, 2)
            log(state, "水", None, f"止まっていた水の輪 ({x['id']}) が直って、また回りはじめた", mill=x["id"])
        t.setdefault("events", []).append(log(state, ACT_MILL, name, txt, mill=x["id"]))
        return
    if _mill_due(state) > 0 or not mill_ready(state):
        m["repair"][y] = round(m["repair"].get(y, 0.0) + rate, 2)
        t.setdefault("events", []).append(log(state, ACT_MILL, name, f"{name} が、川の水の輪の羽と軸を直した", repair=True))
        return
    m["work"] = round(m["work"] + rate, 2)
    t.setdefault("events", []).append(log(state, ACT_MILL, name, f"{name} が、川に新しい水の輪を組んだ (あと 約 {max(0, round(MILL_DAYS - m['work']))} 人日)",
                                          build=True))
    if m["work"] >= MILL_DAYS:
        m["work"] = round(m["work"] - MILL_DAYS, 2)
        builders = sorted(n for n, v in m["by"].items() if v > 0)
        x = {"id": f"M{len(m['mills']) + 1}", "day": D, "by": builders[:12],
             "houses": sorted({q.get("household") for q in state["people"] if q["name"] in builders and q.get("household")})[:12], "stopped": None, "fix": 0}
        m["mills"].append(x)
        m["by"] = {}
        log(state, "水", None, f"村の水の輪 ({x['id']}) が建った。川の力で、1 日に村の 約 {MILL_PEOPLE} 人分の粉をひける (村のもの。建てたのは {'・'.join(builders[:6])}"
            + (" ほか" if len(builders) > 6 else "") + ")", mill=x["id"])


# ---------------- 約束の働き手 (g12._workers_day から) ----------------

def workers(state, oid, n, how, got):
    g, D = _g(state), state["day"]
    y = str(D // YEAR)
    row = g["workers"].setdefault(y, {"reap": 0, "dig": 0, "grain": 0, "from": {}})
    row["reap" if how == "刈る" else "dig"] += n
    row["grain"] += got
    row["from"][oid] = row["from"].get(oid, 0) + n
    o = _other(state, oid)
    _reach(state, "F4", D, f"{o['name'] if o else oid} の働き手 {n} 人が、村で{'刈り入れをした' if how == '刈る' else '水の道を掘った'}")


# ---------------- 悪い年の畑 (era2._field_season から) ----------------

def bad_factor(f):
    """村の悪い年の比: 水の来る分は 1 (半分にしない)、水の来ない分は g7.FIELD_BAD"""
    import g7
    w = float(f.get("water") or 0)
    return w + (1 - w) * g7.FIELD_BAD


def protected(state, f):
    """悪い年に、水の来る畑が守った量 (水が来なければ実った量)"""
    import g7
    g = _g(state)
    y = str((state["day"] + 1) // YEAR)  # 夏のはじめ (次の日) の年
    base = int(f["yield"] * g7.FIELD_BAD / bad_factor(f))
    g["protected"][y] = g["protected"].get(y, 0) + (f["yield"] - base)


# ---------------- 目盛り・季節の終わり ----------------

def _reach(state, f, day, why):
    g = _g(state)
    if f in g["reached"] or day is None:
        return
    g["reached"][f] = day
    log(state, "目盛り", None, f"目盛り: G13 の {f}「{FS[f]}」に届いた ({why})", g="G13", f=f)


def _cond(state, c, day, why):
    g = _g(state)
    if c not in g["c"]:
        g["c"][c] = day
        log(state, "目盛り", None, f"目盛り: G13 の条件 {c[1:]}「{CS[c]}」に届いた ({why})", g="G13", c=c)


def _fail(state, who, what, why, log_it=True):
    """選んだのにできなかったこと・休んだ・へった・止まった。帳簿に残し、log_it なら出来事「水」にも (お題の節に出す)"""
    g, D = _g(state), state["day"]
    g["fails"].append({"day": D, "year": D // YEAR, "who": who, "what": what, "why": why})
    g["fails"] = g["fails"][-80:]
    row = g["path"].get(str((D + 1) // YEAR))
    if row is not None:
        row["failed"] = row.get("failed", 0) + 1
    if log_it:
        log(state, "水", who, why, g13_fail=what)


def _water_fields(state):
    """秋の終わり: この秋にまいた畑 (育っている) のうち、まいた順に cap までを水の来る畑にする (f["water"] は水の来る割合)。c2 を見る"""
    g, D = _g(state), state["day"]
    y = D // YEAR
    left = g["canal"]["cap"]
    sown = wat = 0
    for f in sorted((f for f in state["era2"]["fields"] if f["state"] == "育つ" and era2.season(f["day"]) == "秋" and f["day"] // YEAR == y),
                    key=lambda f: f["id"]):
        w = min(1.0, left / f["seed"]) if f["seed"] > 0 and left > 0 else 0.0
        if w > 0:
            f["water"] = round(w, 4)
            left -= f["seed"] * w
        sown += f["seed"]
        wat += f["seed"] * w
    g["water"][str(y)] = {"sown": sown, "water": int(wat), "cap": g["canal"]["cap"]}
    sh = wat / sown if sown else 0
    if sown and sh >= C2_SHARE and y not in g["c2_years"]:
        g["c2_years"].append(y)
        log(state, "目盛り", None, f"目盛り: G13 の条件 2 の年 ({y}年。秋にまいた草の種の {round(sh * 100)}% が水の来る畑)", g="G13", c2_year=y)
    if all((y - i) in g["c2_years"] for i in range(C2_YEARS)):
        _cond(state, "c2", D, f"秋にまいた草の種の半分以上が水の来る畑の年が {C2_YEARS} 年つづいた ({'・'.join(str(y - i) for i in reversed(range(C2_YEARS)))}年)")


def settlements(state):
    """なくなっていない地域の集落 (人のいる集落)"""
    return [o for o in _others(state) if not o.get("gone") and o.get("people", 0) > 0]


def _year_end(state):
    """年の終わり: 水の道の手入れ → 水の輪の直し (足りなければ止まる) → c1 → c3 → 帳簿"""
    g, D = _g(state), state["day"]
    y = D // YEAR
    ys = str(y)
    c = g["canal"]
    need = c["cap"] / CANAL_PER_DAY * CANAL_KEEP
    if c["cap"] > 0 and c["dug"].get(ys, 0) < need:
        lost = int(c["cap"] * CANAL_LOSS)
        c["cap"] -= lost
        c["lost"].append({"year": y, "lost": lost, "dug": c["dug"].get(ys, 0), "need": round(need, 1)})
        c["lost"] = c["lost"][-20:]
        _fail(state, None, ACT_CANAL, f"{y}年は水の道の手入れが足りず (掘ったのは {c['dug'].get(ys, 0)} 人日。要るのは 約 {round(need)} 人日)、"
              f"水の道が泥でうまって、水の来る畑が 秋にまく草の種 {lost} つかみ分へった")
    m = g["mill"]
    old = [x for x in mills_running(state) if x["day"] // YEAR < y]
    keep = int(m["repair"].get(ys, 0.0) // MILL_REPAIR)
    for x in old[keep:]:
        x["stopped"], x["fix"] = D, 0
        _fail(state, None, ACT_MILL, f"水の輪 ({x['id']}) は、{y}年に直す手 ({MILL_REPAIR} 人日) がなかったので、羽と軸がいたんで止まった "
              f"(主な仕事を「{ACT_MILL}」にして {MILL_REPAIR} 人日直せば、また回る)")
    my = m["year"].get(ys) or {}
    if my.get("days", 0) >= C1_DAYS and my.get("need") and my["milled"] / my["need"] >= C1_SHARE:
        _cond(state, "c1", D, f"{y}年に水の輪が {my['days']} 日回り、村の粉ひきの {round(100 * my['milled'] / my['need'])}% を引き受けた")
    paid = (state["era2"]["g7"]["g12"]["paid"].get(ys) or {})
    n = sum(1 for v in paid.values() if v == "出した")
    tot = len(settlements(state))
    g["c3_rows"][ys] = {"paid": n, "settlements": tot}
    if y > g["start"] // YEAR and tot and n >= C3_SHARE * tot and y not in g["c3_years"]:
        g["c3_years"].append(y)
        log(state, "目盛り", None, f"目盛り: G13 の条件 3 の年 ({y}年。地域の {tot} 集落のうち {n} が、村に約束の分か働き手を出した)", g="G13", c3_year=y)
        if len(g["c3_years"]) >= C3_TIMES:
            _cond(state, "c3", D, f"地域の集落の半分以上が、村に約束の分か働き手を出した年が {len(g['c3_years'])} 回 ({'・'.join(map(str, g['c3_years']))}年)")
    gr = g["grind"].get(ys) or {}
    wk = g["workers"].get(ys) or {}
    wa = g["water"].get(ys) or {}
    hand_days = round(gr.get("hours", 0) / 6, 1)
    water_days = round(gr.get("milled", 0) * GRIND_H / 6, 1)
    fuel = state["era2"]["g7"]["g10"].get("fuel") or []
    if fuel and fuel[-1].get("year") == y:  # 燃料と力の帳簿 (g10): 人でない力 (水) と粉ひきの人日を足す (G13 から。記録だけ)
        fuel[-1]["water_days"] = water_days
        fuel[-1]["grind_days"] = hand_days
    lab = (fuel[-1].get("labour") or {}) if fuel and fuel[-1].get("year") == y else {}
    allw = sum(lab.values()) + hand_days + water_days
    g["ledger"].append({"year": y, "day": D, "grind_hours": gr.get("hours", 0), "grind_days": hand_days, "water_days": water_days,
                        "water_share": round(water_days / allw, 3) if allw else 0.0,
                        "mills": len(m["mills"]), "mills_running": len(mills_running(state)), "mill_days": my.get("days", 0),
                        "mill_share": round(my["milled"] / my["need"], 3) if my.get("need") else 0.0, "mill_work": m["work"],
                        "mill_repair": m["repair"].get(ys, 0.0), "try": round(_tech(state).get("progress", 0), 1), "try_done": _tech(state).get("done"),
                        "knowers": len(knowers_alive(state)), "canal_cap": c["cap"], "canal_dug": c["dug"].get(ys, 0),
                        "water_sown": wa.get("sown", 0), "water_fields": wa.get("water", 0),
                        "water_frac": round(wa["water"] / wa["sown"], 3) if wa.get("sown") else 0.0, "protected": g["protected"].get(ys, 0),
                        "workers_reap": wk.get("reap", 0), "workers_dig": wk.get("dig", 0), "paid": n, "settlements": tot,
                        "fails": sum(1 for f in g["fails"] if f["year"] == y), "store": era2._g6_have(state, "村", g12.GRAIN),
                        "store_days": era2.store_days(state), "top3_house": top3_share(state)})
    g["ledger"] = g["ledger"][-40:]


def top3_share(state):
    """村の中の差 (ならべて測る): 家の倉の草の種のうち、上位 3 家の割合 (家の倉がなければ 0)"""
    hs = sorted((era2._g6_have(state, h, g12.GRAIN) for h in era2._homes(state)), reverse=True)
    tot = sum(hs)
    return round(sum(hs[:3]) / tot, 3) if tot else 0.0


def season_end(state):
    """G13 の季節の終わり (g7.season_end。G12 の季節の終わりのあと): 夏の終わりなら悪い年に守った量の出来事 → 秋の終わりなら水の来る畑 (c2) →
    年の終わりなら手入れ・水の輪・c1・c3・帳簿"""
    g, D = _g(state), state["day"]
    t = _tech(state)
    if t.get("first") is not None and "F2" not in g["reached"] and t["first"] >= g["start"]:
        who = sorted(q["name"] for q in era2.adults(state) if q["skills"].get(f"試す:{CARD}", 0) > 0)
        _reach(state, "F2", t["first"], f"{'・'.join(who[:4]) or '村の人'} が「{_card_name()}」を試しはじめた")
    if (D + 1) % SEASON_DAYS:
        return
    sea = era2.season(D)
    if sea == "夏":
        y = str(D // YEAR)
        if g["protected"].get(y):
            log(state, "水", None, f"村の悪い年だったが、水の来る畑は刈り入れが半分にならなかった (水が来なければ、約 {g['protected'][y]} つかみ少なかった)",
                protected=g["protected"][y])
    if sea == "秋":
        _water_fields(state)
    if (D + 1) % YEAR == 0:
        _year_end(state)


def reached(state, f):
    return bool(on(state) and _g(state)["reached"].get(f))


def done(state):
    return {c: c in _g(state)["c"] for c in CS}


def knowers_alive(state):
    alive = {p["name"] for p in era2.adults(state)}
    return sorted(n for n in (((state["era2"]["g7"].get("hints") or {}).get("knowers") or {}).get(CARD) or []) if n in alive)


def progress(state):
    """条件ごとの進み (段 × 1000 + 数。大きいほど進んだ。yardstick._stall が年の終わりに読む):
    c1: 段 (0 札が開いていない / 1 開いた / 2 F2 / 3 水の輪ができる / 4 F3) × 1000 + 試す進み (200 に対する ‰ の 10 分の 1、100 まで) + その年に回った日 (90 に対して、100 まで)
    c2: 段 (0 / 1 F1) × 1000 + その年の水の来る畑の割合 (‰ の 10 分の 1) + つづいた年 × 100
    c3: その年に出した集落の数 × 100 + 半分以上の年の回数 × 1000"""
    g = _g(state)
    y = _y(state)
    t = _tech(state)
    re_ = g["reached"]
    s1 = 4 if "F3" in re_ else 3 if mill_ready(state) else 2 if "F2" in re_ else 1 if t.get("open") is not None else 0
    days = ((hints.cards()[CARD].get("try") or {}).get("days") or 200)
    my = g["mill"]["year"].get(str(y)) or {}
    c1 = s1 * 1000 + min(100, round(1000 * t.get("progress", 0) / days / 10)) + min(100, round(100 * my.get("days", 0) / C1_DAYS))
    wa = g["water"].get(str(y)) or g["water"].get(str(y - 1)) or {}
    run = 0
    yy = max((int(k) for k in g["water"]), default=y)
    while (yy - run) in g["c2_years"]:
        run += 1
    c2 = (1 if "F1" in re_ else 0) * 1000 + min(100, round(1000 * wa.get("water", 0) / max(1, wa.get("sown", 0)) / 10)) + run * 100
    row = g["c3_rows"].get(str(y)) or g["c3_rows"].get(str(y - 1)) or {}
    c3 = row.get("paid", 0) * 100 + len(g["c3_years"]) * 1000
    return {"c1": c1, "c2": c2, "c3": c3}


# ---------------- 道の見張り (答える人のうち、その道を自分で選べる人で数える。G13_design.md 6.) ----------------

def _house_of(state, name):
    p = next((q for q in era2.adults(state) if q["name"] == name), None)
    return p.get("household") if p else None


def house_knowers(state, name):
    """name の家の、札を知っている大人 (name もふくむ)"""
    h = _house_of(state, name)
    kn = set(knowers_alive(state))
    return [q["name"] for q in era2.adults(state) if h and q.get("household") == h and q["name"] in kn]


def key_houses(state):
    """見本の家に必ず足す家: 札 H12-01 を知っている人のいる家 (水の輪を建てられるようになるまで)"""
    if mill_ready(state):
        return []
    kn = set(knowers_alive(state))
    return sorted({p.get("household") for p in era2.adults(state) if p["name"] in kn and p.get("household")})


def paths(state):
    """いまのお題に答える人 (era2.answerers) のうち、まだ届いていない条件ごとに、その道を自分で選べる人の名前。
    c1: 水の輪ができる前は、札を知っている人と、その家の代表 (札がまだ開いていなくても、知っている人がいればその人。開いていなければ 0)。知っている人が 0 人なら 0。
        できたあとは答える人みな (建てる・直す)。
    c2: 答える人みな (大人ならだれでも掘れる)。
    c3: 約束が 1 つ以上あるか、受けてくれそうな村が 1 つ以上あれば、答える人みな。どちらもなければ 0"""
    g = _g(state)
    ans = era2.answerers(state)
    if can_do(state, ACT_MILL):
        c1 = list(ans)
    elif CARD in hints.open_techs(state):
        c1 = [n for n in ans if house_knowers(state, n)]
    else:
        c1 = []
    s12 = state["era2"]["g7"]["g12"]
    has = any(g12._active(p) for p in s12["pacts"].values())
    out = {"c1": c1, "c2": list(ans), "c3": list(ans) if (has or g12.candidates(state)) else []}
    return {k: v for k, v in out.items() if k not in g["c"]}


def _chose(state, real):
    """この集まりで、道を実際に選んだ答える人の数 (試す H12-01・水の輪を建てる・水の道を掘るを自分か家の人に割り振った・take に働き手を書いた)"""
    k = 0
    for n, a in real.items():
        if not isinstance(a, dict):
            continue
        txt = json.dumps({x: a.get(x) for x in ("year", "job", "family")}, ensure_ascii=False)
        if ACT_CANAL in txt or ACT_MILL in txt or CARD in txt or WORKERS in json.dumps(a.get("pact"), ensure_ascii=False):
            k += 1
    return k


def count_paths(state, real):
    """集まりの答えを当てはめるとき (g7.apply_year から。答えを当てはめる前の、お題を書いたときの state で): この集まりの、道を選べた人・選んだ人を、
    その年 (この歩の季節の年。g12.count_paths と同じ (日 + 1) ÷ 120) に足す"""
    g = _g(state)
    y = str((state["day"] + 1) // YEAR)
    row = g["path"].setdefault(y, {"meetings": 0, "c1": 0, "c2": 0, "c3": 0, "chose": 0, "failed": 0, "knowers": 0, "who": {}})
    row["meetings"] += 1
    row["knowers"] = max(row.get("knowers", 0), len(knowers_alive(state)))
    for k, names in paths(state).items():
        row[k] += len(names)
        if names:
            row["who"][k] = sorted(set(row["who"].get(k, [])) | set(names))[:12]
    row["chose"] += _chose(state, real)


def fails_year(state, y):
    return [f for f in _g(state)["fails"] if f["year"] == y]


def path_consult(state, done_list):
    """年の終わり: まだ届いていない条件の道を、自分で選べる答える人が、G13 に入ってからのまる 2 年つづけて 0 人なら止めて相談 (仕組みのまちがい)。一度ずつ。
    そのほか、G13 に入った日から 5 年ごとに止めて相談 (本人の決め 2026-11-12 (おすすめ)。6,000 万トークンの目安はワークフローの側で見る)"""
    g, D = _g(state), state["day"]
    y = (D + 1) // YEAR - 1
    y0 = (g["start"] + 1) // YEAR
    for k in ("c1", "c2", "c3"):
        if k in g["c"]:
            continue
        ys = [y - i for i in range(PATH_YEARS)]
        if ys[-1] < y0:
            continue
        if all(((g["path"].get(str(x)) or {}).get(k, 0) == 0) for x in ys):
            if not any(c["why"] == f"g13_path_{k}" and c.get("year") == y for c in done_list):
                return {"why": f"g13_path_{k}", "year": y, "day": D,
                        "text": f"G13 の条件 {k[1:]} ({CS[k]}) の道を、自分で選べる答える人が {PATH_YEARS} 年つづけていなかった (仕組みのまちがいとして相談)"}
    if D > g["start"] and (D - g["start"]) % (LATER_YEARS * YEAR) == 0:
        why = f"g13_years_{D}"
        if not any(c["why"] == why for c in done_list):
            return {"why": why, "day": D, "text": f"G13: G13 に入って {(D - g['start']) // YEAR} 年たった (5 年ごとの相談)"}
    return None


def report_lines(state):
    """報告に書くこと (止めない): 「選んだのにできなかった」が 1 年に 3 回以上・札を知っている人が 1 人だけ / 0 人 (水の輪ができる前)・
    選べた人はいるのに、だれも選ばなかった年が 3 年つづいた・粉ひきで畑の世話が要る手間を下回った年"""
    g, out = _g(state), []
    y = _y(state)
    f = fails_year(state, y)
    if len(f) >= FAIL_REPORT:
        out.append(f"この年に、選んだのにできなかったこと {len(f)} 回: " + " / ".join(x["why"][:60] for x in f[-5:]))
    if not mill_ready(state) and not g["mill"]["mills"]:
        kn = knowers_alive(state)
        if not kn:
            out.append(f"水の輪の札 ({CARD}) を知っている大人が 0 人 (試す道は、きっかけだけ)")
        elif len(kn) == 1:
            out.append(f"水の輪の札 ({CARD}) を知っている大人は {kn[0]} だけ")
    py = (state["day"] + 1) // YEAR
    if str(py) not in g["path"]:  # 年の終わりの日 (次の年の集まりの前) は、まだその年の行がないので、前の年から数える
        py -= 1
    rows = [g["path"].get(str(py - i)) for i in range(IDLE_YEARS)]
    if all(r and r.get("meetings") and (r["c1"] + r["c2"] + r["c3"]) > 0 and r.get("chose", 0) == 0 for r in rows):
        out.append(f"選べた答える人はいるのに、水の輪・水の道・働き手を、だれも選ばなかった年が {IDLE_YEARS} 年つづいた")
    under = field_short(state)
    if under:
        out.append(under)
    return out


def field_short(state):
    """粉ひきのせいで、去年の畑の世話が、畑の要る手間 (まいた種 × 0.15 + 10 時間) を下回った畑があったか (G13_design.md 3.1 の見込みの確かめ)"""
    y = _y(state)
    short = [f for f in state["era2"]["fields"] if f["state"] in ("実った", "刈った") and f["day"] // YEAR == y - 1
             and era2.season(f["day"]) == "秋" and f["work"] < f["seed"] * 0.15 + 10]
    if short and (_g(state)["grind"].get(str(y - 1)) or {}).get("hours"):
        return f"{y - 1}年の秋にまいた畑 {len(short)} 枚で、畑の世話が要る手間を下回った (粉ひきの手間が効いたかもしれない)"
    return None


def indicators(state):
    """G13 の目安 (era2.indicators に足す。【シ】)"""
    g = _g(state)
    y = str(_y(state))
    my = g["mill"]["year"].get(y) or {}
    wa = g["water"].get(y) or {}
    row = g["c3_rows"].get(y) or {}
    return {"g13_c1_day": g["c"].get("c1"), "g13_c2_day": g["c"].get("c2"), "g13_c3_day": g["c"].get("c3"),
            "g13_mills": len(g["mill"]["mills"]), "g13_mills_running": len(mills_running(state)), "g13_mill_days": my.get("days", 0),
            "g13_mill_share": round(my["milled"] / my["need"], 3) if my.get("need") else 0.0, "g13_try": round(_tech(state).get("progress", 0), 1),
            "g13_mill_ready": mill_ready(state), "g13_knowers": len(knowers_alive(state)), "g13_canal_cap": g["canal"]["cap"],
            "g13_water_frac": round(wa["water"] / wa["sown"], 3) if wa.get("sown") else 0.0, "g13_c2_years": len(g["c2_years"]),
            "g13_paid": row.get("paid", 0), "g13_settlements": row.get("settlements", len(settlements(state))), "g13_c3_years": len(g["c3_years"]),
            "g13_fails": len(fails_year(state, int(y))), "g13_grind_hours": round((g["grind"].get(y) or {}).get("hours", 0), 1)}


# ---------------- お題 ----------------

def facts(state):
    """お題の決まりの文 (G13 から)。条件の名前と判定の文は書かない (5.3)。決まりの中の数 (60 つかみ・250 人・15 分・80 人日・10 人日) は書く"""
    return (f"粉ひき: G13 から、草の種は粉にしてから食べる。1 人 1 日の分をひくのに 約 {round(GRIND_H * 60)} 分。家の大人の働く時間から引かれる。"
            "水の輪がひいた分は、人はひかない。\n"
            f"水の道: 主な仕事を「{ACT_CANAL}」にすると、1 日で、秋にまく草の種 {CANAL_PER_DAY} つかみ分の畑に水が来る。水の来る畑は、村の悪い年でも刈り入れが半分にならない。"
            "水の道は 1 年に少し手入れしないと、泥でうまる。\n"
            f"水の輪: 「{_card_name()}」を試してできるようになると、主な仕事を「{ACT_MILL}」にして、{MILL_DAYS} 人日で 1 つ建てられる。"
            f"1 つで 約 {MILL_PEOPLE} 人分の粉をひく。1 年に {MILL_REPAIR} 人日直さないと止まる。水の輪は村のもの。\n"
            f"約束の働き手: 倉の約束の take に「{WORKERS}」を書ける。刈り入れの季節は刈り、ほかの日は村の水の道を掘る。\n")


def _water_now(state):
    """いまの水の来る畑の見込み: (秋にまく量の見込み, cap)。秋にまく量は、去年の秋にまいた量 (なければ cap)"""
    g = _g(state)
    ys = sorted(g["water"], key=int)
    last = g["water"][ys[-1]]["sown"] if ys else _sown_last(state)
    return last, g["canal"]["cap"]


def _sown_last(state):
    """いちばん新しい秋にまいた草の種 (つかみ)"""
    fs = [f for f in state["era2"]["fields"] if era2.season(f["day"]) == "秋"]
    if not fs:
        return 0
    y = max(f["day"] // YEAR for f in fs)
    return sum(f["seed"] for f in fs if f["day"] // YEAR == y)


def _bad_text(state):
    """いちばん新しい村の悪い年 (夏の畑の比が半分) の文 (地域の天気の帳簿 g7.region.weather_log の年。年の最後の日に引いて、その年の夏の畑に効く)"""
    wl = (state["era2"]["g7"].get("region") or {}).get("weather_log") or []
    y = max([w["year"] for w in wl if "V0" in w.get("bad", [])] or [BAD_LAST])
    return f"{y}年は村の悪い年で、夏の刈り入れが半分になった"


def text(state, p):
    """お題の節「## 水と畑と務め」(長い節。短い節と重なる行は 1 行にする)"""
    g, y = _g(state), _y(state)
    rows = []
    rows.append(f"- 粉ひき: いま村の粉ひきに、1 日 約 {grind_people(state)} 人分の手 (6 時間働く大人) がかかっている"
                + (f" (水の輪がひいた分は 1 日 約 {min(len([q for q in state['people'] if q['alive']]), MILL_PEOPLE * len(mills_running(state)))} 人分)" if mills_running(state) else ""))
    t = _tech(state)
    kn = knowers_alive(state)
    who = sorted(q["name"] for q in era2.adults(state) if q["skills"].get(f"試す:{CARD}", 0) > 0)
    m = g["mill"]
    if mill_ready(state) or m["mills"]:
        rows.append(f"- 水の輪: 建った輪 {len(m['mills'])} (回っている {len(mills_running(state))})"
                    + (f"。いま組んでいる輪は {round(m['work'])} / {MILL_DAYS} 人日" if m["work"] else "")
                    + f"。この年に直した {round(m['repair'].get(str(y), 0))} 人日 (回っている輪 1 つにつき 1 年 {MILL_REPAIR} 人日)")
        for x in m["mills"]:
            if x.get("stopped"):
                rows.append(f"- 止まっている水の輪 ({x['id']}): 直す手がなかったので止まった。あと {round(MILL_REPAIR - x.get('fix', 0))} 人日直せば、また回る")
    elif t.get("open") is not None:
        rows.append(f"- 水の輪: 「{_card_name()}」[{CARD}] を試している (進み {round(t.get('progress', 0))} / "
                    f"{(hints.cards()[CARD].get('try') or {}).get('days', 200)}。試した人 {'・'.join(who[:8]) or 'まだいない'})。"
                    f"この便りを知っている人: {'・'.join(kn) or 'いない'}")
    else:
        rows.append(f"- 水の輪: 「{_card_name()}」[{CARD}] は、まだ村で試せない。この便りを知っている人: {'・'.join(kn) or 'いない'}")
    sown, cap = _water_now(state)
    rows.append(f"- 水の道: いま水が来るのは、秋にまく草の種 {cap} つかみ分の畑 (去年の秋にまいたのは {sown} つかみ)。"
                f"この年に掘った {g['canal']['dug'].get(str(y), 0)} 人日 (手入れに要るのは 1 年に 約 {round(cap / CANAL_PER_DAY * CANAL_KEEP)} 人日)")
    if g["protected"]:
        yy = max(g["protected"], key=int)
        rows.append(f"- {yy}年は村の悪い年だったが、水の来る畑は刈り入れが半分にならなかった (約 {g['protected'][yy]} つかみ守った)")
    wk = g["workers"].get(str(y - 1)) or g["workers"].get(str(y)) or {}
    if wk:
        rows.append(f"- 約束の働き手: 刈った {wk.get('reap', 0)} 人日・水の道を掘った {wk.get('dig', 0)} 人日 ({'・'.join(sorted(wk.get('from') or {}))})")
    f = [x for x in g["fails"] if x["year"] >= y - 1][-4:]
    if f:
        rows.append("- 水と畑と務めで、できなかったこと: " + " / ".join(x["why"] for x in f))
    return "\n## 水と畑と務め\n" + "\n".join(rows) + "\n"


def grind_people(state):
    """いまの粉ひきの手 (6 時間働く大人で何人分)。水の輪がひく分は引く"""
    pop = len([q for q in state["people"] if q["alive"]])
    left = max(0, pop - MILL_PEOPLE * len(mills_running(state)))
    return round(left * GRIND_H / 6) if GRIND_ON else 0


def progress_lines(state):
    """3 つの進み (1 行ずつ。村の人が見て分かる数だけ)"""
    g, y = _g(state), _y(state)
    out = []
    t = _tech(state)
    if "c1" in g["c"]:
        out.append(f"- 水の輪: 届いた ({g['c']['c1']} 日目)")
    else:
        my = g["mill"]["year"].get(str(y)) or {}
        st = (f"建った輪 {len(g['mill']['mills'])}" if (mill_ready(state) or g["mill"]["mills"]) else
              f"札が{'開いた' if t.get('open') is not None else 'まだ開いていない'}・試す進み {round(t.get('progress', 0))} / {(hints.cards()[CARD].get('try') or {}).get('days', 200)}")
        out.append(f"- 水の輪: {st}。{y}年に回った日 {my.get('days', 0)} (1 年に {C1_DAYS} 日以上回り、村の粉の半分以上をひくと届く)")
    if "c2" in g["c"]:
        out.append(f"- 水の来る畑: 届いた ({g['c']['c2']} 日目)")
    else:
        sown, cap = _water_now(state)
        run = 0
        yy = max((int(k) for k in g["water"]), default=y)
        while (yy - run) in g["c2_years"]:
            run += 1
        out.append(f"- 水の来る畑: いま 秋にまく草の種 {cap} つかみ分 (去年の秋は {sown} つかみまいた)。秋のまきつけの半分以上に水が来た年が、いま {run} 年つづいている ({C2_YEARS} 年つづくと届く)")
    if "c3" in g["c"]:
        out.append(f"- 約束の分: 届いた ({g['c']['c3']} 日目)")
    else:
        ys = sorted(g["c3_rows"], key=int)
        last = g["c3_rows"][ys[-1]] if ys else None
        out.append(f"- 約束の分: " + (f"{ys[-1]}年に村に約束の分か働き手を出した村 {last['paid']} / {last['settlements']}" if last else
                                       f"約束の分を出した村は、G13 に入ってからはまだ数えていない (地域の村 {len(settlements(state))})")
                   + f"。半分以上の村が出した年: {len(g['c3_years'])} 回 ({C3_TIMES} 回で届く)")
    return out


def _js(x):
    return json.dumps(x, ensure_ascii=False)


def prompt_block(state, p):
    """「## いま」の答えの並びのすぐ前に置く短い節 (G13 に入る日から。G12_design.md 12. の学び)。G12 の短い節 (倉と約束と帳) は、ここに短くまとめる (g12.prompt_block の compact)。
    その人がこの集まりでできること (水の輪を試す・建てる / 水の道を掘る / 約束の働き手)・3 つの進み。せかす言葉は書かない"""
    if not p:
        return ""
    g = _g(state)
    rows = [BLOCK_HEAD.replace("あなたが", f"あなた ({p['name']}) が", 1)]
    name = p["name"]
    t = _tech(state)
    kn = knowers_alive(state)
    fam = house_knowers(state, name)
    gp = grind_people(state)
    if mill_ready(state) or g["mill"]["mills"]:
        st = [x for x in g["mill"]["mills"] if x.get("stopped")]
        rows.append(f"- 水の輪: 主な仕事を「{ACT_MILL}」にできる (大人ならだれでも。札を知っている人ははかどる)。"
                    + (f"止まっている輪を直す (あと {round(MILL_REPAIR - st[0].get('fix', 0))} 人日)。" if st else
                       f"新しい輪はあと 約 {max(0, round(MILL_DAYS - g['mill']['work']))} 人日で建つ。" if mill_ready(state) else "")
                    + f"回っている輪 {len(mills_running(state))} (1 つで 約 {MILL_PEOPLE} 人分。いま粉ひきに 1 日 約 {gp} 人分の手がかかっている)。"
                    f"回っている輪は 1 年に {MILL_REPAIR} 人日直さないと止まる")
    elif t.get("open") is not None and kn:
        others = [n for n in kn if n not in fam]
        if name in kn:
            rows.append(f"- 水の輪: あなたは「{_card_name()}」の話を知っている。主な仕事を「試す」(job の try に \"{CARD}\") にすると、水の輪を試せる"
                        + (f" (ほかに知っている人: {'・'.join(n for n in kn if n != name)})" if len(kn) > 1 else "") + "。")
            rows.append("  知らない人も、あなたと同じ季節に「試す」をして with にあなたの名前を書けば、一緒に試して覚えられる。"
                        "試しが進めば (2 年ほど)、村で水の輪を建てられるようになる。"
                        f"水の輪が 1 つあれば、村の 約 {MILL_PEOPLE} 人分の粉を川の力でひける (いまは粉ひきに、1 日 約 {gp} 人分の手がかかっている)")
        elif fam:
            rows.append(f"- 水の輪: あなたの家の {'・'.join(fam)} は「{_card_name()}」の話を知っている。family で「試す」(try に \"{CARD}\") にすると、水の輪を試せる"
                        f"{'・ほかに知っている人: ' + '・'.join(others) if others else ''}。"
                        f"試しが進めば (2 年ほど) 水の輪を建てられ、1 つで 約 {MILL_PEOPLE} 人分の粉をひける (いまは粉ひきに、1 日 約 {gp} 人分の手がかかっている)")
        else:
            rows.append(f"- 水の輪: 「{_card_name()}」の話を知っているのは {'・'.join(kn)}。あなたも、その人と同じ季節に「試す」(try に \"{CARD}\") をして "
                        f"with にその人の名前を書けば、一緒に試して覚えられる。水の輪が 1 つあれば、村の 約 {MILL_PEOPLE} 人分の粉を川の力でひける "
                        f"(いまは粉ひきに、1 日 約 {gp} 人分の手がかかっている)")
    elif t.get("open") is not None:
        rows.append(f"- 水の輪: 「{_card_name()}」の話を知っている人が、いま村にいないので、試せない")
    else:
        rows.append(f"- 水の輪: 「{_card_name()}」は、まだ村で試せない" + (f" (話を知っている人: {'・'.join(kn)})" if kn else ""))
    sown, cap = _water_now(state)
    half = max(0, (sown + 1) // 2 - cap)
    rows.append(f"- 水の道: 主な仕事を「{ACT_CANAL}」にできる (大人ならだれでも)。水の来る畑は、村の悪い年でも刈り入れが半分にならない ({_bad_text(state)})。"
                f"いま水の来る畑: 秋にまく草の種 {cap} つかみ分 (去年の秋にまいたのは {sown} つかみ)。"
                + (f"半分にするには あと 約 {-(-half // CANAL_PER_DAY)} 人日" if half else "去年の秋のまきつけの半分をこえている")
                + (f"。手入れに 1 年 約 {round(cap / CANAL_PER_DAY * CANAL_KEEP)} 人日" if cap else ""))
    ex = worker_example(state)
    if ex:
        rows.append(f"- 約束の働き手: 倉の約束の take に {{\"{WORKERS}\": [人, 日]}} を足すと、その村の人が、刈り入れか水の道を手伝う (その村の人の 2 割 × 20 日まで)。"
                    f"例: \"pact\": [{_js(ex)}]")
    else:
        rows.append(f"- 約束の働き手: 倉の約束の take に {{\"{WORKERS}\": [人, 日]}} を書ける (いま約束を受けてくれそうな村はない)")
    rows += g12.prompt_block(state, p, compact=True)
    rows.append("- pact・help と働き手は、答えた人の中でいちばん多い中身に決まる (1 人の答えでも決まる。書かなくてもよい)")
    rows.append("いまの進み (水と畑と務め):")
    rows += progress_lines(state)
    return "\n".join(rows) + "\n"


def worker_example(state):
    """働き手を足した約束の例 (受ける決まりに合う形)。続いている約束があれば、その中身に働き手を足し、ねうちが足りなければ give の草の種を足す。
    なければ、受けてくれそうな村への新しい約束。どちらもなければ None"""
    s12 = state["era2"]["g7"]["g12"]
    act = sorted((oid for oid, x in s12["pacts"].items() if g12._active(x) and _other(state, oid)), key=lambda k: int(k[1:]))
    cands = [(_other(state, oid), s12["pacts"][oid]) for oid in act] + [(o, None) for o in g12.candidates(state)]
    for o, x in cands:
        if g12.near_why(state, o):
            continue
        n = max(1, min(2, int(o["people"] * g12.TAKE_HANDS_SHARE)))
        take = dict(x["take"]) if x else {}
        take[WORKERS] = [n, 20]
        give = dict(x["give"]) if x else {}
        need = g12.GIVE_RATIO * g12.value(take) - g12.value({k: v for k, v in give.items() if k != g12.GRAIN})
        give[g12.GRAIN] = max(give.get(g12.GRAIN, 0), -(-need // era2.VALUE[g12.GRAIN] // 100) * 100)
        terms = {"give": {k: give[k] for k in sorted(give)}, "take": {k: take[k] for k in sorted(take)}}
        if g12.accept_why(state, o, terms) is None:
            return {"to": o["id"], **terms}
    return None


def feel_note(state, p):
    """気持ちだけのお題の行 (代表でない人は仕事を決めないので、代表に伝えられることだけ)"""
    out = []
    if p["name"] in knowers_alive(state) and not mill_ready(state):
        out.append(f"- あなたは「{_card_name()}」の話を知っている。家の代表が、あなたの仕事を「試す」(try に \"{CARD}\") にすれば、あなたは水の輪を試せる")
    out.append("- 水の輪・水の道のことを、家の代表に伝えられる")
    return "\n" + "\n".join(out)


def field_rows(state, year=False):
    """答えの欄の説明 (g7._field_rows に足す)"""
    rows = [f"   水の道: 主な仕事を「{ACT_CANAL}」にできる (大人ならだれでも)"]
    if can_do(state, ACT_MILL):
        rows.append(f"   水の輪: 主な仕事を「{ACT_MILL}」にできる (大人ならだれでも)")
    elif CARD in hints.open_techs(state):
        rows.append(f"   水の輪を試す: 主な仕事を「試す」にして try に \"{CARD}\" (話を知っている人と、その人と同じ季節に with に名前を書く人)")
    rows.append(f'   約束の働き手: pact の take に {{"{WORKERS}": [人, 日]}} も書ける (刈り入れの季節は刈り、ほかの日は水の道を掘る)')
    return rows


def bad_words(s):
    return [w for w in WORDS if w in s]
