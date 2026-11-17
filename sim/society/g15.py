"""G15「近世の農業と農村の手仕事」(第 8 部「工業の入口」のただ 1 つの G。2026-11-15 本人の言葉「お任せします」に従い、下書きのおすすめどおり。
docs/society_phase/G15_design.md)

- G15 に入るのは step.py next_part --decided "<本人の言葉>" だけ (G14 を閉じて第 7 部が終わった HOLD part_end から。g7.enter_next → g7.start_g15)。
  G14 までは、このファイルを読みこみもしない (g7・era2・hints・yardstick・world は state の g7.g15 があるときだけ、関数の中で読みこむ)。
  だから G1〜G14 は、お題・state・出来事・乱数が前と 1 バイトも変わらない
- 計画の入口の 5 つ (計画 3.2) と「3 つ以上・そのうち 1 つが e1 か e3」の決まりはそのまま。測り方をこの村の帳簿の形にした (数えるのは G15 に入った次の暦の年 (194年) から):
  e1 燃える石: 暦の 1 年の火と力の帳簿で、燃える石の熱が合わせの半分以上の年が 2 年つづく (燃える石を置いた世界だけ)
  e2 食べ物の仕事が地域の働いた日の半分未満の年 (まわりの集落の大人はみな食べ物の仕事と数える)
  e3 水の作業場: 1 つの作業場で、3 家以上の大人 8 人以上が同じ日に働いた日が、暦の 1 年に 30 日。それが 2 年つづく
  e4 作ったもの: 村の 1 人あたりの作ったもの (刈り入れ・ヤギの子・使ったか出した品・燃やした燃える石) の 3 年の平均が、3 回つづけて上がる
  e5 火と力の合わせが 1 人 1 日 3 万 kcal をこえる年
  入口に着くと、コードが HOLD entrance で止める (era2.ENTRANCE = "G15")。e1 と e3 がそろって入口の手前なら、一度だけ止めて相談
- F: F1 はじめての水の作業場 / F2 はじめての燃える石 / F3 はじめての作業場の年 / F4 読める大人が 1 割
- 足す仕組み (乱数なし。入る日に作る人が新しい人を 1 人入れるところだけ、その日の名前の乱数を使う):
  欄 workshop (回っている水の輪のうち、粉ひきに要る数を残して 1 つを作業場に作りかえる。いちばん多い中身)・仕事「水の作業場を作る」(60 人日)・
  「水の作業場で働く」(水ののこ = 板 / 水の槌 = 黒い金属をたたく。腕のある人がいる日だけ)・「燃える石を掘る」(北の丘。置いた世界だけ)・
  「かまどを作りかえる」(家のかまどを石のかまどに。10 人日)・板 (直し・建てる・作業場・かまど・住まいの仕事が倍はかどる)・火と力の帳簿 (kcal)・村の作ったものの帳簿・
  札 3 枚 (H14-03〜05。話だけ。hint_cards_g15.json)・作る人が入れた新しい人 (本人の希望 2026-11-15。newcomer)
- G10〜G14 の仕組みと直しは動きつづける。G14 の条件は「ならべて測る」。第 8 部の前の方法の直し (g7.fix8) は g7.g15 があるので効く
- 暦の年: 帳簿は日 ÷ 120。道の見張りの行と、お題の「年」は (日 + 1) ÷ 120 (g7.plan_year)
- 村の人に見せる文には WORDS を書かない (試しで確かめる)。呼び名は「水の作業場」「水の槌」「水ののこ」「燃える石」「石のかまど」。「黒い石」とは書かない (黒曜石と読まれる)
"""
import json
import math
import random

import era2
import g10
import g12
import g13
import g14
import hints
from world import log

YEAR, SEASON_DAYS = era2.YEAR, era2.SEASON_DAYS
ACT_WS_BUILD = "水の作業場を作る"
ACT_WS_WORK = "水の作業場で働く"
ACT_DIG = "燃える石を掘る"
ACT_STOVE = "かまどを作りかえる"
ACTS15 = (ACT_WS_BUILD, ACT_WS_WORK, ACT_DIG, ACT_STOVE)  # G15 の仕事 (world.ACTS7 の後ろに足した。G15 で選べるときだけ)
SAW, HAMMER = "水ののこ", "水の槌"
TOOLS = (SAW, HAMMER)
WS_DAYS = 60  # 水の輪を作業場に作りかえる人日【仮定】(屋根と軸と道具。水の輪を建てる 80 人日より少し少ない)
WS_MAX, WS_PER_MEET = 3, 1  # 作業場は合わせて 3 つまで・1 回の集まりで 1 つ【仮定】
WS_CAP = 20  # 1 つの作業場で 1 日に働けるのは 20 人まで【仮定】
PLANK_PER_DAY = 1  # 水ののこ: 1 人日で板 1 束【仮定】
PLANK_BOOST = 2.0  # 板を 1 束使うと、その 1 人日が 2 人日分はかどる【仮定】
HAMMER_DAYS = 8  # 水の槌: 黒い金属の鎌 1 本が 20 人日 → 8 人日【仮定】(炭は今のまま 1 本 14 kg)
COAL_PLACE = "北丘12"  # 燃える石の層を置いた所 (村のまわりの地図の北の丘。キャンプから約 400 m)【与えた土地・仮定】
COAL_LABEL = "北の丘 (キャンプから約 400 m。燃える石の層がある)"
COAL_WHY = "作る側が置いた土地 (G15 の設計 3.3。本物のハブールのあたりに石炭はない)"
COAL_KG_DAY = 200  # 1 人日で燃える石 200 kg を掘って運ぶ【仮定】
STOVE_DAYS = 10  # かまどを石のかまどに作りかえる人日 (家ごと)【仮定】
# 火と力の帳簿の表 (G15_design.md 3.5。入る前に決めて変えない【仮定】)
KCAL_FOOD = 2000  # 人の食べ物 1 人 1 日
WOOD_KG = 1.5  # まきのかまど 1 人 1 日のまき (kg)
WOOD_KCAL = 3600  # まき 1 kg
COAL_KG = 0.75  # 石のかまど 1 人 1 日の燃える石 (kg。まきの 2 倍の熱)
COAL_KCAL = 7200  # 燃える石 1 kg
KILN_WOOD = 2  # 土器 1 個を焼くまき (kg)
CHAR_KCAL = 7000  # 黒い金属の炭 1 kg (炭は g10.IRON_CHAR_KG = 14 kg / 本)
MILL_KCAL = 30000  # 回った水の輪 1 つ 1 日
WOOD_ALT = (1.0, 1.5, 2.0)  # 評価でくらべる、まきの表 (1 人 1 日 kg)。決まりの数は WOOD_KG のまま
# 村の作ったもの (e4。草の種のつかみ)【仮定】
OUT_VALUE = {"鎌": 75, "黒い金属の鎌": 150, "土器": 40, "板": 60}
GOAT_KID = 375
WOOD_GRAIN = 1  # 燃やした燃える石は、置きかえたまき 1 kg = 草の種 1 つかみ
E1_SHARE, E1_YEARS = 0.5, 2
E2_SHARE = 0.5
E3_PEOPLE, E3_HOUSES, E3_DAYS, E3_YEARS = 8, 3, 30, 2
E4_WIN, E4_RISES = 3, 3
E5_KCAL = 30000
F4_SHARE = 0.1
PATH_YEARS = 2  # 道の見張り: 選べる答える人が 2 年つづけて 0 人なら止めて相談
IDLE_YEARS = 3  # 選べた人はいるのに、だれも選ばなかった年がつづいたら報告 (止めない)
FAIL_REPORT = 3
LATER_YEARS = 5  # 5 年ごとの相談 (G15 に入った日から)
READERS_REPORT, READERS_STOP = 2, 1  # 読める大人が 2 人以下で報告・1 人以下で止めて相談 (一度ずつ)
STORE_REPORT = 300  # 蓄えが 300 日分を切ったら報告
WORDS = ("工場", "工業", "石炭", "蒸気", "機械", "産業", "革命", "賃金", "問屋", "鉱山", "エネルギー", "カロリー", "黒い石") + g12.WORDS + g13.WORDS + g14.WORDS
ES = {"e1": "燃える石", "e2": "食べ物でない仕事が地域の半分", "e3": "水の作業場", "e4": "作ったもの", "e5": "1 人 1 日 3 万 kcal"}
FS = {"F1": "はじめての水の作業場", "F2": "はじめての燃える石", "F3": "はじめての作業場の年", "F4": "読める大人が 1 割"}
BLOCK_HEAD = "水の作業場と燃える石・続けること: この集まりで、あなたができること (どれも、しなくてもよい。書かなければ今のまま)"
# 作る側が入れた新しい人 (本人の希望 2026-11-15「超優秀な人」)。体と働く速さはほかの人と同じ。読み書きができ、札「川の力で粉をひく輪」[H12-01] を知っている。
# 役はない (まとめ役・長老・教える人・作業場の頭ではない)。自分の新しい家を立て、その家の答える人。ほかの人のお題では、ふつうのよそから来た人と同じに見える
NEWCOMER_AGE = 30
NEWCOMER_WHY = "作った人が入れた人 (本人の希望 2026-11-15)"
NEWCOMER_MODEL = "fable"  # 答えを書くモデル (ワークフローの args.fable にこの人の名前を入れる。記録だけ。シミュレーションの中では使わない)
NEWCOMER_ON = True  # 決まりの村の「新しい人なし」の束だけ False にする (本物ではいつも True)
COAL_ON = True  # 決まりの村の W15N (燃える石なし) だけ False にする (本物ではいつも True。本人の決め: 置く)


def on(state):
    return "start" in (((state.get("era2") or {}).get("g7") or {}).get("g15") or {})


def _g(state):
    return state["era2"]["g7"]["g15"]


def _y(state):
    return state["day"] // YEAR


def _js(x):
    return json.dumps(x, ensure_ascii=False)


def bad_words(s):
    return [w for w in WORDS if w in s]


def coal_on(state):
    return bool(_g(state)["coal"].get("placed"))


def _people(state):
    return [p for p in state["people"] if p["alive"]]


def _house_of(state, name):
    p = next((q for q in era2.adults(state) if q["name"] == name), None)
    return p.get("household") if p else None


def _num(mid):
    try:
        return int(str(mid)[1:])
    except ValueError:
        return 10 ** 6


# ---------------- G15 に入る (g7.start_g15 から) ----------------

def start(state, decided=None):
    """G15 の state を作る: G14 の物差し (条件・F・道の見張り・帳簿の要点) を g7.before.G14.g14 に写し、条件と道の見張りは数え直す
    (F は村に起きたことなので消さない)。燃える石の層を北の丘に置く (COAL_ON。作る側が置いた土地と記録)。札 3 枚 (H14-03〜05) を札の表に足す。
    作る側が入れた新しい人 (NEWCOMER_ON) を、その人の新しい家と一緒に村に入れる"""
    g7s, D = state["era2"]["g7"], state["day"]
    t = g7s["g14"]
    g7s.setdefault("before", {}).setdefault("G14", {})["g14"] = {
        "reached": dict(t["reached"]), "c": dict(t["c"]), "c1_years": list(t["c1_years"]), "c2_years": list(t["c2_years"]),
        "c3_years": list(t["c3_years"]), "path": {k: {x: v for x, v in r.items() if x != "who"} for k, r in t["path"].items()}}
    t["path"] = {}
    g = g7s["g15"] = {"start": D, "decided": decided, "coal": {"placed": bool(COAL_ON), "place": COAL_PLACE if COAL_ON else None,
                                                               "why": COAL_WHY if COAL_ON else "燃える石を置かない世界 (決まりの村の W15N)",
                                                               "stock": 0.0, "dug": {}, "burned": {}, "by": {}},
                      "stoves": {}, "ws": {}, "wsday": {}, "wsyear": {}, "planks": {"stock": 0, "made": {}, "used": {}},
                      "energy": {}, "base": {}, "out": {}, "ledger": [], "e1_years": [], "e3_years": [], "e4_rises": [], "e": {}, "reached": {},
                      "fails": [], "path": {}, "examples": {}, "newcomer": None, "dest": {}}
    _base(state)
    if COAL_ON:
        pl = next((x for x in state["places"] if x["id"] == COAL_PLACE), None)
        if pl is not None:
            pl["label"] = COAL_LABEL
        log(state, "燃える石", None, "北の丘の崖に、火をつけると長く燃える黒い筋がある (燃える石の層)。掘ると 1 人 1 日 約 200 kg。"
            "家のかまどを石のかまどに作りかえると、まきのかわりに燃やせる", coal=COAL_PLACE, placed_by=COAL_WHY)
    h = g7s.get("hints") or {}
    if h:
        sha = hints.cards_sha(state)
        h["cards_sha"] = sha
        h.setdefault("cards_log", []).append({"day": D, "sha": sha, "note": "G15 に入った日: 話の札 3 枚 (H14-03〜05)"})
        log(state, "区切り", None, "よその便りの札の表に 3 枚を足した (G15 に入った日)", cards=sha)
    if NEWCOMER_ON:
        add_newcomer(state)
    log(state, "水の作業場", None, "G15 から、回っている水の輪のうち、粉ひきに要る数を残して、1 つを「水の作業場」に作りかえられる (水ののこ・水の槌)", g15=True)
    return g


def add_newcomer(state):
    """作る側が入れた新しい人 (本人の希望 2026-11-15): よそから来た大人 1 人 (30 才)。自分の新しい家を立て、その家の答える人になる。
    作り方はふつうのよそから来た人と同じ (era2._new_person。体と腕の数の決め方も同じ)。読み書きができ、札 H12-01 を知っている (試した腕 1.0)。
    名前と体の乱数は、この日だけの乱数 (村の乱数の列には足さない)。state には作る側が入れたことを、そのまま残す"""
    e2, g7s, D = state["era2"], state["era2"]["g7"], state["day"]
    rng = random.Random(f"g15-newcomer-{D}")
    sex = rng.choice(("女", "男"))
    p = era2._new_person(state, rng, sex, NEWCOMER_AGE, origin="よそから来た")
    name = p["name"]
    p["household"] = f"{name}の家"
    p["plan"] = {"activity": "畑仕事", "place": "camp", "with": []}
    e2.setdefault("joined", []).append(name)
    g10._g(state)["readers"][name] = D  # 読み書きができる (字を習う決まりは変えない。読める人として数える)
    card = g13.CARD
    p["skills"][f"試す:{card}"] = 1.0  # 札「川の力で粉をひく輪」を知っていて、輪を組める (試した人と同じ腕)
    hints._add_knowers(state, card, [name])
    tc = (g7s.get("hints") or {}).get("tech", {}).get(card)
    back = False
    if tc is not None and not tc.get("done"):
        tc["done"] = D
        tc["progress"] = max(tc.get("progress", 0.0), float((hints.cards()[card].get("try") or {}).get("days", 0)))
        back = True
    log(state, "加わる", None, f"よそから来た {name} が、村に加わった (遠くから、ひとりで来て、{name}の家を立てた)", newcomer=True)
    if back:
        log(state, "試す", name, f"村で「{hints.cards()[card]['name']}」がまたできるようになった ({name} が輪の組み方を知っていた)", card=card)
    _g(state)["newcomer"] = {"name": name, "day": D, "household": p["household"], "sex": sex, "age": NEWCOMER_AGE, "why": NEWCOMER_WHY,
                             "model": NEWCOMER_MODEL, "reads": True, "card": card, "mill_back": back, "answers": {}, "years": {}}
    return p


def newcomer(state):
    return (_g(state).get("newcomer") or None) if on(state) else None


# ---------------- 板 (村の倉。直し・建てる・作業場・かまど・住まいの仕事が倍はかどる) ----------------

def plank_rate(state):
    """板が村の倉にあれば 1 束使って 2 (その 1 人日が 2 人日分)。なければ 1"""
    pk = _g(state)["planks"]
    if pk["stock"] >= 1:
        pk["stock"] -= 1
        y = str(_y(state))
        pk["used"][y] = pk["used"].get(y, 0) + 1
        return PLANK_BOOST
    return 1.0


# ---------------- 水の作業場 ----------------

def grind_need(state):
    """粉ひきに残す水の輪の数 (村の人 ÷ 250 を切り上げ)"""
    return max(1, math.ceil(len(_people(state)) / g13.MILL_PEOPLE))


def workshops(state, done=None):
    """作業場 (作りかえると決めた輪)。done=True なら作りかえ終えたもの、False なら作っている途中のもの"""
    ws = _g(state)["ws"]
    return sorted((k for k, v in ws.items() if done is None or bool(v.get("done") is not None) == done), key=_num)


def _mill(state, mid):
    return next((m for m in state["era2"]["g7"]["g13"]["mill"]["mills"] if m["id"] == mid), None)


def grind_mills(state):
    """粉をひいている輪 (回っていて、作業場に作りかえ終えていない輪)"""
    return [m for m in g13.mills_running(state) if not m.get("ws")]


def candidates(state):
    """作業場にできる輪 (回っていて、作業場でも作っている途中でもない輪)。番号の小さいほうから粉ひきに残す数を除いたもの"""
    ws = _g(state)["ws"]
    free = sorted((m["id"] for m in g13.mills_running(state) if m["id"] not in ws), key=_num)
    return free[grind_need(state):] if len(ws) < WS_MAX else []


def ws_why(state, mid, tool):
    """欄 workshop の中身が通らないわけ (通るなら None)"""
    ws = _g(state)["ws"]
    m = _mill(state, mid)
    if tool not in TOOLS:
        return f"道具は {SAW} か {HAMMER} だけ"
    if m is None:
        return f"{mid} という水の輪はない"
    if mid in ws:
        return f"{mid} はもう作業場にすると決めてある"
    if len(ws) >= WS_MAX:
        return f"作業場はもう {WS_MAX} つ (これより多くはできない)"
    if m.get("stopped"):
        return f"{mid} は止まっている (先に直す)"
    free = [x for x in g13.mills_running(state) if x["id"] not in ws]
    if len(free) - 1 < grind_need(state):
        return f"粉をひく輪が足りなくなるので ({grind_need(state)} つは残す)"
    return None


def _ws_rows(v):
    if isinstance(v, dict):
        v = [v]
    if not isinstance(v, list):
        return []
    out = []
    for r in v[:6]:
        if not isinstance(r, dict):
            continue
        mid = str(r.get("輪") or r.get("mill") or r.get("to") or "").strip().upper()
        tool = str(r.get("道具") or r.get("tool") or "").strip()
        if mid:
            out.append((mid, tool))
    return out


def apply_workshop(state, real):
    """集まりの答えの workshop: 答えた人の中でいちばん多い中身 (g7._tally。1 人でも決まる)。1 回の集まりで 1 つまで。通らなければ、わけを残す"""
    import g7
    g, D = _g(state), state["day"]
    votes = {}
    for n, a in real.items():
        if not isinstance(a, dict):
            continue
        rows = _ws_rows(a.get("workshop"))
        if rows:
            votes[n] = _js({"輪": rows[0][0], "道具": rows[0][1]})
    if not votes:
        return None
    w = g7._vote_weights(state, real)
    ch, txt = g7._tally(state, votes, w)
    if not ch:
        return None
    who = sorted(n for n, v in votes.items() if v == ch)
    r = json.loads(ch)
    why = ws_why(state, r["輪"], r["道具"])
    if why:
        _fail(state, who[0], "workshop", f"{r['輪']} を {r['道具'] or '(道具なし)'} の作業場に作りかえられなかった ({why}。答えた人 {'・'.join(who)})")
        return None
    g["ws"][r["輪"]] = {"tool": r["道具"], "day": D, "by": who, "votes": txt, "work": 0.0, "done": None, "builders": {}}
    log(state, "水の作業場", who[0], f"水の輪 {r['輪']} を「{r['道具']}」の作業場に作りかえると決めた (あと {WS_DAYS} 人日。主な仕事「{ACT_WS_BUILD}」。"
        f"答えた人 {'・'.join(who)}。票 {txt})", mill=r["輪"], tool=r["道具"])
    return r["輪"]


def set_dest(state, name, j):
    """仕事「水の作業場を作る」「水の作業場で働く」の輪 (place か 輪 か to)。なければ決まりの手 (季節のはじめの日に選ぶ)"""
    v = str((j or {}).get("輪") or (j or {}).get("place") or (j or {}).get("to") or "").strip().upper()
    d = _g(state)["dest"]
    if v.startswith("M") and v in _g(state)["ws"]:
        d[name] = v
    else:
        d.pop(name, None)


def _pick_ws(state, name, act):
    g = _g(state)
    want = g["dest"].get(name)
    if act == ACT_WS_BUILD:
        cand = workshops(state, done=False)
    else:
        cand = workshops(state, done=True)
    if want in cand:
        return want
    return cand[0] if cand else None


def work_day(state, p, t, act):
    """1 日: 水の作業場を作る・水の作業場で働く・燃える石を掘る・かまどを作りかえる (g7.role_day から)"""
    name = p["name"]
    if act == ACT_DIG:
        return _dig(state, p, t)
    if act == ACT_STOVE:
        return _stove(state, p, t)
    mid = _pick_ws(state, name, act)
    g, D = _g(state), state["day"]
    if mid is None:
        why = (f"{name} は、作りかけの水の作業場がないので、休んだ (作りかえる輪は欄 workshop で決める)" if act == ACT_WS_BUILD else
               f"{name} は、使える水の作業場がまだないので、休んだ (作りかえる輪は欄 workshop で決め、「{ACT_WS_BUILD}」で作る)")
        return _rest(state, p, t, act, why)
    w = g["ws"][mid]
    m = _mill(state, mid)
    if m is None or m.get("stopped"):
        return _rest(state, p, t, act, f"{name} は、作業場の水の輪 {mid} が止まっているので、働けずに休んだ (直すのは「{g13.ACT_MILL_FIX}」)")
    if act == ACT_WS_BUILD:
        rate = plank_rate(state)
        w["work"] = round(w["work"] + rate, 2)
        w["builders"][name] = round(w["builders"].get(name, 0) + rate, 2)
        t.setdefault("events", []).append(log(state, ACT_WS_BUILD, name, f"{name} が、水の輪 {mid} に屋根と軸と{w['tool']}を組んだ (あと 約 {max(0, round(WS_DAYS - w['work']))} 人日"
                                              + ("。板を使った" if rate > 1 else "") + ")", mill=mid))
        if w["work"] >= WS_DAYS:
            w["done"] = D
            m["ws"] = w["tool"]
            b = sorted(w["builders"])
            log(state, "水の作業場", None, f"水の輪 {mid} が「{w['tool']}」の作業場になった (作ったのは {'・'.join(b[:6])}{' ほか' if len(b) > 6 else ''})。"
                "この輪は粉をひかない", mill=mid, tool=w["tool"])
            _reach(state, "F1", D, f"水の輪 {mid} を {w['tool']} の作業場に作りかえ終えた")
        return
    day = g["wsday"].setdefault(mid, {}).setdefault(str(D), [])
    if len(day) >= WS_CAP:
        return _rest(state, p, t, act, f"{name} は、作業場 {mid} がいっぱい ({WS_CAP} 人) だったので、休んだ")
    day.append(name)
    y = str(_y(state))
    row = _wsy(state, y, mid)
    row["days"] += 1
    if w["tool"] == SAW:
        g["planks"]["stock"] += PLANK_PER_DAY
        g["planks"]["made"][y] = g["planks"]["made"].get(y, 0) + PLANK_PER_DAY
        row["planks"] += PLANK_PER_DAY
        t.setdefault("events", []).append(log(state, ACT_WS_WORK, name, f"{name} が、作業場 {mid} の水ののこで木をひいて、板にした (村の倉の板 {g['planks']['stock']} 束)", mill=mid))
        return
    smiths = [q["name"] for q in era2.adults(state) if (q.get("today") or {}).get("activity") == ACT_WS_WORK and _pick_ws(state, q["name"], ACT_WS_WORK) == mid
              and g10.smith(state, q["name"])]
    if not g10.iron_ready(state) or not smiths:
        row["no_smith"] += 1
        g.setdefault("wsnosm", {}).setdefault(mid, [])
        if str(D) not in g["wsnosm"][mid]:  # 本人に聞いた点 (G15_check.md 2.3) をおすすめで決めた (2026-11-16): 何も作らない槌の日は e3 の「8 人の日」に数えない
            g["wsnosm"][mid].append(str(D))
        why = f"{name} は、作業場 {mid} で槌を回したが、黒い金属の腕のある人がいないので、黒い金属はたたけなかった"
        t.setdefault("events", []).append(log(state, ACT_WS_WORK, name, why, mill=mid, no_smith=True))
        if not any(f["who"] == name and f["what"] == act and f["day"] // SEASON_DAYS == D // SEASON_DAYS for f in g["fails"]):
            _fail(state, name, act, why, log_it=False)
        return
    s10 = g10._g(state)
    if not g10.smith(state, name) and name not in s10["pending_smiths"]:
        s10["pending_smiths"].append(name)
    s10["forge"] = round(s10["forge"] + g10.IRON_DAYS / HAMMER_DAYS, 3)
    row["iron"] += 1
    t.setdefault("events", []).append(log(state, ACT_WS_WORK, name, f"{name} が、作業場 {mid} の水の槌で黒い金属をたたいた"
                                          + (f" ({'・'.join(smiths[:2])} に教わりながら)" if name not in smiths else ""), mill=mid))
    while s10["forge"] >= g10.IRON_DAYS:
        s10["forge"] = round(s10["forge"] - g10.IRON_DAYS, 3)
        g10._make_tool(state)


def _wsy(state, y, mid):
    return _g(state)["wsyear"].setdefault(str(y), {}).setdefault(mid, {"days": 0, "big": 0, "big_noans": 0, "planks": 0, "iron": 0, "no_smith": 0, "houses": {}})


def _rest(state, p, t, act, why):
    """選んだのにできなかった: 出来事「休む」にわけを残し、帳簿に (1 季節に 1 回)"""
    g, D, name = _g(state), state["day"], p["name"]
    t.setdefault("events", []).append(log(state, "休む", name, why, rest_why=act))
    if not any(f["who"] == name and f["what"] == act and f["day"] // SEASON_DAYS == D // SEASON_DAYS for f in g["fails"]):
        _fail(state, name, act, why, log_it=False)


def _ws_season(state):
    """季節の終わり: 作業場ごとの日の人を数える (8 人以上・3 家以上の日。答えた家の人がいない日には印)"""
    import g7
    g = _g(state)
    hs = {p["name"]: p.get("household") for p in era2.adults(state)}
    src = state["era2"]["g7"].get("src") or {}
    for mid, days in sorted(g["wsday"].items()):
        for ds, names in sorted(days.items(), key=lambda kv: int(kv[0])):
            y = int(ds) // YEAR
            row = _wsy(state, y, mid)
            houses = {hs.get(n) or n for n in names}
            for h in houses:
                row["houses"][h] = row["houses"].get(h, 0) + sum(1 for n in names if (hs.get(n) or n) == h)
            if ds in (g.get("wsnosm") or {}).get(mid, []):
                continue
            if len(names) >= E3_PEOPLE and len(houses) >= E3_HOUSES:
                row["big"] += 1
                if push_on(state) and any(src.get(n) == PUSH_SRC for n in names):  # 2026-11-16: 作る側の後押しの人がいた 8 人の日 (印のあとだけ数える)
                    row["big_push"] = row.get("big_push", 0) + 1
                if not any(g7.gpath_kind(src.get(n)) == "answered" for n in names):
                    row["big_noans"] += 1
                if after_on(state):  # 2026-11-17: 後押しなしの確かめのあいだだけ、答えた家・写って動いた家の人がいたかで分ける (印のあとだけ数える)
                    ks = {g7.gpath_kind(src.get(n)) for n in names}
                    for k, hit in (("big_ans", "answered" in ks), ("big_copy", "copied" in ks), ("big_other", not ks & {"answered", "copied"})):
                        if hit:
                            row[k] = row.get(k, 0) + 1
    g["wsday"] = {}
    g["wsnosm"] = {}


# ---------------- 燃える石 ----------------

def _dig(state, p, t):
    g, name = _g(state), p["name"]
    if not coal_on(state):
        return _rest(state, p, t, ACT_DIG, f"{name} は、燃える石のある所を知らないので、休んだ")
    c = g["coal"]
    y = str(_y(state))
    c["stock"] = round(c["stock"] + COAL_KG_DAY, 1)
    c["dug"][y] = c["dug"].get(y, 0) + COAL_KG_DAY
    c["by"][name] = c["by"].get(name, 0) + 1
    t.setdefault("events", []).append(log(state, ACT_DIG, name, f"{name} が、北の丘で燃える石を {COAL_KG_DAY} kg 掘って、村の倉に運んだ (村の倉の燃える石 {round(c['stock'])} kg)",
                                          coal=COAL_KG_DAY))


def stove_done(state, h):
    return (_g(state)["stoves"].get(h) or {}).get("done") is not None


def _stove(state, p, t):
    g, D, name = _g(state), state["day"], p["name"]
    h = p.get("household")
    if g.get("push") and (g["push"].get("stove_for") or {}).get(name) and push_src(state, name):  # 2026-11-16: 後押しで、ほかの家のかまどを手伝う人
        h = g["push"]["stove_for"][name]
    if not coal_on(state):
        return _rest(state, p, t, ACT_STOVE, f"{name} は、燃える石がないので、かまどを作りかえずに休んだ")
    if not h:
        return _rest(state, p, t, ACT_STOVE, f"{name} は、家がないので、かまどを作りかえずに休んだ")
    if stove_done(state, h):
        return _rest(state, p, t, ACT_STOVE, f"{name} は、{h}のかまどはもう石のかまどなので、休んだ")
    s = g["stoves"].setdefault(h, {"work": 0.0, "done": None, "by": []})
    rate = plank_rate(state)
    s["work"] = round(s["work"] + rate, 2)
    if name not in s["by"]:
        s["by"].append(name)
    t.setdefault("events", []).append(log(state, ACT_STOVE, name, f"{name} が、{h}のかまどを石のかまどに作りかえた (あと 約 {max(0, round(STOVE_DAYS - s['work']))} 人日"
                                          + ("。板を使った" if rate > 1 else "") + ")", household=h))
    if s["work"] >= STOVE_DAYS:
        s["done"] = D
        log(state, "燃える石", None, f"{h}のかまどが石のかまどになった。村の倉に燃える石があれば、まきのかわりに燃やす", household=h)


def evening(state):
    """その日の火 (era2._day の夕方から。毎日。乱数なし): 石のかまどの家は、村の倉に燃える石があれば、家の人の分 (1 人 0.75 kg) を燃やす。
    なければ今のまま (まき)。火と力の帳簿の 1 日の数をためる"""
    g, D = _g(state), state["day"]
    alive = _people(state)
    if not alive:
        return
    y = str(D // YEAR)
    en = g["energy"].setdefault(y, {"people_days": 0, "wood_pd": 0, "coal_pd": 0, "mill_days": 0, "coal_kg": 0.0})
    en["people_days"] += len(alive)
    en["mill_days"] += len(g13.mills_running(state))
    coal_pd = 0
    if coal_on(state) and g["stoves"]:
        homes = {}
        for p in alive:
            h = p.get("household")
            if h and stove_done(state, h):
                homes[h] = homes.get(h, 0) + 1
        c = g["coal"]
        for h in sorted(homes):
            need = round(homes[h] * COAL_KG, 2)
            if c["stock"] >= need:
                c["stock"] = round(c["stock"] - need, 2)
                c["burned"][y] = round(c["burned"].get(y, 0) + need, 2)
                en["coal_kg"] = round(en["coal_kg"] + need, 2)
                coal_pd += homes[h]
                if "F2" not in g["reached"]:
                    _reach(state, "F2", D, f"{h}の石のかまどで、北の丘から掘った燃える石を燃やした")
    en["coal_pd"] += coal_pd
    en["wood_pd"] += len(alive) - coal_pd


def _base(state):
    """年のはじめの数 (作った土器・鎌・黒い金属の鎌の数え。年の終わりに引いて、その年に作った数にする)"""
    e2 = state["era2"]
    _g(state)["base"] = {"year": _y(state) + (1 if (state["day"] + 1) % YEAR == 0 else 0), "iron": len(g10._g(state)["made"])}


# ---------------- 年の終わり: 帳簿と物差し ----------------

def energy_row(state, y, wood_kg=WOOD_KG):
    """暦の年 y の火と力の帳簿 (kcal。表は頭の数のまま。wood_kg だけ評価のくらべで変えられる)"""
    g = _g(state)
    en = g["energy"].get(str(y)) or {}
    lr = next((r for r in g["ledger"] if r["year"] == y), None)
    pots = (lr or {}).get("pots_made", 0)
    iron = (lr or {}).get("iron_made", 0)
    rows = {"food": en.get("people_days", 0) * KCAL_FOOD, "wood": round(en.get("wood_pd", 0) * wood_kg * WOOD_KCAL),
            "coal": round(en.get("coal_pd", 0) * COAL_KG * COAL_KCAL), "kiln": pots * KILN_WOOD * WOOD_KCAL,
            "char": iron * g10.IRON_CHAR_KG * CHAR_KCAL, "mill": en.get("mill_days", 0) * MILL_KCAL}
    tot = sum(rows.values())
    pd = en.get("people_days", 0)
    return {**rows, "total": tot, "coal_share": round(rows["coal"] / tot, 4) if tot else 0.0, "per_day": round(tot / pd) if pd else 0}


def _ledger(state):
    """年の終わりの帳簿の行 (作業場・燃える石・板・火と力・作ったもの・字・黒い金属・水の輪・蓄え)"""
    g, D, e2 = _g(state), state["day"], state["era2"]
    y = D // YEAR
    ys = str(y)
    b = g["base"] if g["base"].get("year") == y else {"iron": len(g10._g(state)["made"])}
    made = __import__("g7")._made(state, y * YEAR)  # この年に作った土器と鎌 (出来事「土器」「道具」の数から。村の倉の数は割れたり運んだりで減るので使わない)
    wsy = g["wsyear"].get(ys) or {}
    s13 = state["era2"]["g7"]["g13"]
    hd = g14.house_days(state)
    nf, wk = sum(v[0] for v in hd.values()), sum(v[1] for v in hd.values())
    pop = len(_people(state))
    setts = sum(o.get("people", 0) for o in g13.settlements(state))
    per = wk / pop if pop else 0
    reg_w = wk + setts * per
    food_share = round(1 - nf / reg_w, 4) if reg_w else 1.0
    mk = (state["era2"]["g7"]["g14"]["market"]["year"].get(ys) or {})
    notes = [x for x in state["era2"]["g7"]["g14"]["notes"]["list"] if x["day"] // YEAR == y]
    out_pots = mk.get(g14.POT, 0) + sum(x["give"].get(g14.POT, 0) for x in notes)
    out_sickles = mk.get(g14.SICKLE, 0) + sum(x["give"].get(g14.SICKLE, 0) for x in notes)
    row = {"year": y, "day": D, "pop": pop, "adults": len(era2.adults(state)),
           "pots_made": sum(v.get("土器", 0) for v in made.values()), "sickles_made": sum(v.get("鎌", 0) for v in made.values()),
           "iron_made": len(g10._g(state)["made"]) - b["iron"],
           "ws": {k: {kk: (dict(vv) if isinstance(vv, dict) else vv) for kk, vv in v.items()} for k, v in wsy.items()},
           "ws_list": {k: {"tool": v["tool"], "done": v["done"], "work": v["work"]} for k, v in g["ws"].items()},
           "planks_made": g["planks"]["made"].get(ys, 0), "planks_used": g["planks"]["used"].get(ys, 0), "planks": g["planks"]["stock"],
           "coal_dug": g["coal"]["dug"].get(ys, 0), "coal_burned": g["coal"]["burned"].get(ys, 0), "coal_stock": g["coal"]["stock"],
           "stoves": sorted(h for h in g["stoves"] if stove_done(state, h)), "homes": len(era2._homes(state)),
           "nonfood_days": nf, "worked_days": wk, "village_food_share": round(1 - nf / wk, 4) if wk else 1.0, "region_food_share": food_share,
           "settle_people": setts, "harvest": __import__("g7").harvest_year(state),
           "kids": sum(1 for x in e2["goats"] if y * YEAR <= x["born"] < (y + 1) * YEAR),
           "out_pots": out_pots, "out_sickles": out_sickles,
           "readers": g10.readers(state), "smiths": g10.smiths_now(state), "mills": len(s13["mill"]["mills"]), "mills_running": len(g13.mills_running(state)),
           "grind_mills": len(grind_mills(state)), "mill_repair": s13["mill"]["repair"].get(ys, 0.0), "canal_cap": s13["canal"]["cap"],
           "store_days": era2.store_days(state), "fails": sum(1 for f in g["fails"] if f["year"] == y)}
    g["ledger"] = [r for r in g["ledger"] if r["year"] != y] + [row]
    en = energy_row(state, y)
    row["energy"] = en
    row["e1_alt"] = {str(k): energy_row(state, y, k)["coal_share"] for k in WOOD_ALT}
    out = (row["harvest"] + row["kids"] * GOAT_KID + row["out_pots"] * OUT_VALUE["土器"] + row["out_sickles"] * OUT_VALUE["鎌"]
           + row["iron_made"] * OUT_VALUE["黒い金属の鎌"] + row["planks_used"] * OUT_VALUE["板"]
           + round(row["coal_burned"] * (COAL_KCAL / WOOD_KCAL) * WOOD_GRAIN))
    row["output"] = out
    row["output_pc"] = round(out / pop, 2) if pop else 0.0
    g["ledger"] = g["ledger"][-40:]
    return row


def _year_end(state):
    """年の終わり: 帳簿 → e1〜e5・F3・F4 (G15 に入った次の暦の年から)・新しい人の 1 年"""
    g, D = _g(state), state["day"]
    y = D // YEAR
    row = _ledger(state)
    _newcomer_year(state, y)
    _base(state)
    if after_on(state):  # 2026-11-17: 後押しなしの確かめの年の行 (印のあとだけ)
        _g(state)["after"]["rows"][str(y)] = after_row(state, y)
    if y <= g["start"] // YEAR:
        return
    en = row["energy"]
    if coal_on(state) and en["coal_share"] >= E1_SHARE and y not in g["e1_years"]:
        g["e1_years"].append(y)
        log(state, "目盛り", None, f"目盛り: G15 の e1 の年 ({y}年。燃える石の熱が火と力の {round(en['coal_share'] * 100, 1)}%)", g="G15", e1_year=y)
    if all((y - i) in g["e1_years"] for i in range(E1_YEARS)):
        _e(state, "e1", D, f"燃える石の熱が火と力の半分以上の年が {E1_YEARS} 年つづいた")
    if row["region_food_share"] < E2_SHARE:
        _e(state, "e2", D, f"食べ物の仕事が地域の働いた日の {round(row['region_food_share'] * 100, 1)}% になった")
    big = max((r["big"] for r in (row["ws"] or {}).values()), default=0)
    if big >= E3_DAYS and y not in g["e3_years"]:
        g["e3_years"].append(y)
        best = max(row["ws"].items(), key=lambda kv: (kv[1]["big"], kv[0]))
        _reach(state, "F3", D, f"作業場 {best[0]} で、3 家以上の大人 8 人以上が同じ日に働いた日が {y}年に {best[1]['big']} 日")
        log(state, "目盛り", None, f"目盛り: G15 の e3 の年 ({y}年。作業場 {best[0]} の 8 人の日 {best[1]['big']} 日)", g="G15", e3_year=y)
    if all((y - i) in g["e3_years"] for i in range(E3_YEARS)):
        _e(state, "e3", D, f"作業場の 8 人の日が 1 年に {E3_DAYS} 日以上の年が {E3_YEARS} 年つづいた")
    g["out"][str(y)] = row["output_pc"]
    avg = output_avg(state)
    if str(y) in avg and str(y - 1) in avg and avg[str(y)] > avg[str(y - 1)] and y not in g["e4_rises"]:
        g["e4_rises"].append(y)
    run = 0
    while (y - run) in g["e4_rises"]:
        run += 1
    if run >= E4_RISES:
        _e(state, "e4", D, f"1 人あたりの作ったものの {E4_WIN} 年の平均が {E4_RISES} 回つづけて上がった")
    if en["per_day"] >= E5_KCAL:
        _e(state, "e5", D, f"火と力の合わせが 1 人 1 日 {en['per_day']} kcal になった")
    ads = len(era2.adults(state))
    if ads and len(row["readers"]) >= F4_SHARE * ads:
        _reach(state, "F4", D, f"読める大人が {len(row['readers'])} 人 (大人 {ads} 人の 1 割以上)")


def output_avg(state):
    """1 人あたりの作ったものの 3 年の平均 {年: 平均} (G15 に入った次の年から数えた年がそろうところだけ)"""
    g = _g(state)
    o = {int(k): v for k, v in g["out"].items()}
    y0 = g["start"] // YEAR + 1
    return {str(y): round(sum(o[y - i] for i in range(E4_WIN)) / E4_WIN, 2) for y in sorted(o) if all((y - i) in o and y - i >= y0 for i in range(E4_WIN))}


def _newcomer_year(state, y):
    """新しい人の 1 年 (年報が読む): その人の家が答えた G の仕事の人日・写って動いた家 (手本がその人の家) の人日 (g7.gpath から)・欄 workshop"""
    nc = _g(state).get("newcomer")
    if not nc:
        return
    g7s = state["era2"]["g7"]
    h = nc["household"]
    gp = (g7s.get("gpath") or {}).get(str(y)) or {}
    donor = g7s.get("donor") or {}
    fol = sorted(x for x, d in donor.items() if d == h)
    ans = {d: v for d, v in nc["answers"].items() if int(d) // YEAR == y or (int(d) + 1) // YEAR == y}
    if not ans:  # その人がまだ答えていない年 (入った年) の写しは、前の手本の家の予定なので、その人のものに数えない
        fol = []
    own, copied = {}, {}
    for act, r in gp.items():
        n = (r.get("answered") or {}).get(h, 0)
        if n:
            own[act] = n
        for x in fol:
            m = (r.get("copied") or {}).get(x, 0)
            if m:
                copied.setdefault(x, {})[act] = m
    alive = any(p["name"] == nc["name"] and p["alive"] for p in state["people"])
    nc["years"][str(y)] = {"alive": alive, "own": own, "followers": fol, "copied": copied, "answers": ans}
    if len(nc["years"]) > 30:
        for k in sorted(nc["years"], key=int)[:-30]:
            nc["years"].pop(k)


def season_end(state):
    """G15 の季節の終わり (g7.season_end。G14 の季節の終わりのあと): 作業場の日を数える → 年の終わりなら帳簿と物差し"""
    D = state["day"]
    if (D + 1) % SEASON_DAYS:
        return
    _ws_season(state)
    if (D + 1) % YEAR == 0:
        _year_end(state)


def _e(state, k, day, why):
    g = _g(state)
    if k not in g["e"]:
        g["e"][k] = day
        log(state, "目盛り", None, f"目盛り: G15 の入口 {k}「{ES[k]}」に届いた ({why})", g="G15", e=k)


def _reach(state, f, day, why):
    g = _g(state)
    if f in g["reached"] or day is None:
        return
    g["reached"][f] = day
    log(state, "目盛り", None, f"目盛り: G15 の {f}「{FS[f]}」に届いた ({why})", g="G15", f=f)


def _fail(state, who, what, why, log_it=True):
    g, D = _g(state), state["day"]
    g["fails"].append({"day": D, "year": D // YEAR, "who": who, "what": what, "why": why})
    g["fails"] = g["fails"][-80:]
    row = g["path"].get(str((D + 1) // YEAR))
    if row is not None:
        row["failed"] = row.get("failed", 0) + 1
    if log_it:
        log(state, "水の作業場", who, why, g15_fail=what)


def reached(state, f):
    return bool(on(state) and _g(state)["reached"].get(f))


def done(state):
    return {k: k in _g(state)["e"] for k in ("e1", "e3", "e4")}


def entrance_count(state):
    e = _g(state)["e"]
    return sum(1 for k in ES if k in e), ("e1" in e or "e3" in e)


def progress(state):
    """入口の物差しごとの進み (yardstick._stall が年の終わりに読む。G15_design.md 2.3。e2・e5 は数えない):
    e1: その年 (なければ前の年) の燃える石の割合 (‰ の 10 分の 1、50 まで) × 20 + つづいた年 × 1000 + 石のかまどの家の数 × 10
    e3: 段 (0 / 1 F1) × 1000 + その年の「8 人の日」の数 (30 に対して、100 まで) + つづいた年 × 1000
    e4: 上がった回 × 1000 + その年の 1 人あたりの作ったもの (前の 3 年の平均に対して、100 まで)"""
    g = _g(state)
    y = _y(state)
    lr = next((r for r in reversed(g["ledger"]) if r["year"] in (y, y - 1)), None) or {}
    sh = (lr.get("energy") or {}).get("coal_share", 0.0)
    run1 = 0
    while (max(g["e1_years"], default=-9) - run1) in g["e1_years"]:
        run1 += 1
    e1 = min(50, round(1000 * sh / 10)) * 20 + run1 * 1000 + len([h for h in g["stoves"] if stove_done(state, h)]) * 10
    big = max((r["big"] for r in (lr.get("ws") or {}).values()), default=0)
    run3 = 0
    while (max(g["e3_years"], default=-9) - run3) in g["e3_years"]:
        run3 += 1
    e3 = (1 if "F1" in g["reached"] else 0) * 1000 + min(100, round(100 * big / E3_DAYS)) + run3 * 1000
    avg = output_avg(state)
    prev = avg.get(str(y - 1)) or avg.get(str(y - 2))
    cur = g["out"].get(str(y)) or g["out"].get(str(y - 1)) or 0
    e4 = len(g["e4_rises"]) * 1000 + (min(100, round(100 * cur / prev)) if prev else 0)
    return {"e1": e1, "e3": e3, "e4": e4}


# ---------------- 道の見張り (答える人のうち、その道を自分で選べる人で数える。G15_design.md 6.) ----------------

def key_houses(state):
    """見本の家に必ず足す家: 読める人の家・黒い金属の腕のある人の家・作業場で働いた人の家 (前の 1 年)・新しい人の家"""
    names = set(g10.readers(state)) | set(g10.smiths_now(state))
    y = _y(state)
    hs = {p.get("household") for p in era2.adults(state) if p["name"] in names and p.get("household")}
    nc = _g(state).get("newcomer")
    if nc and any(p["name"] == nc["name"] and p["alive"] and not p.get("child") for p in state["people"]):
        hs.add(nc["household"])
    for yy in (str(y), str(y - 1)):
        for r in (_g(state)["wsyear"].get(yy) or {}).values():
            for h in sorted(r["houses"], key=lambda h: -r["houses"][h])[:3]:
                if h in set(era2._homes(state)):
                    hs.add(h)
    return sorted(hs)


def paths(state):
    """いまのお題に答える人のうち、まだ届いていない e1・e3 の道を自分で選べる人の名前。
    e3: 作業場にできる輪があるか、作業場があるか、作っている途中なら、答える人みな。e1: 燃える石を置いた世界だけ、答える人みな"""
    g = _g(state)
    ans = era2.answerers(state)
    out = {}
    if "e3" not in g["e"]:
        out["e3"] = list(ans) if (candidates(state) or g["ws"]) else []
    if "e1" not in g["e"] and coal_on(state):
        out["e1"] = list(ans)
    return out


def _acts_in(a):
    txt = json.dumps({x: a.get(x) for x in ("year", "job", "family")}, ensure_ascii=False)
    return [x for x in ACTS15 if x in txt]


def examples(state):
    """答える人ごとの workshop の例 {名前: {"輪", "道具"}} (作業場にできる輪を、大きい番号から答える人の順に回す。道具は水ののこ)。
    お題を書くときと、答えを当てはめるとき (同じ state) に同じ形になる"""
    c = list(reversed(candidates(state)))
    if not c:
        return {}
    return {n: {"輪": c[i % len(c)], "道具": SAW} for i, n in enumerate(era2.answerers(state))}


def count_paths(state, real):
    """集まりの答えを当てはめるとき (g7.apply_year から。答えを当てはめる前の state で): 道を選べた人・選んだ人・例と同じに書いた人を、その年 ((日 + 1) ÷ 120) に足す。
    出した例を g7.g15.examples に残す (第 7 部の学び 3)"""
    g, D = _g(state), state["day"]
    y = str((D + 1) // YEAR)
    row = g["path"].setdefault(y, {"meetings": 0, "e1": 0, "e3": 0, "chose": 0, "failed": 0, "same_ex": 0, "ws_written": 0,
                                   "readers": 0, "smiths": 0, "who": {}, "chose_who": []})
    row["meetings"] += 1
    row["readers"] = max(row.get("readers", 0), len(g10.readers(state)))
    row["smiths"] = max(row.get("smiths", 0), len(g10.smiths_now(state)))
    for k, names in paths(state).items():
        row[k] += len(names)
        if names:
            row["who"][k] = sorted(set(row["who"].get(k, [])) | set(names))[:12]
    ex = examples(state)
    g["examples"][str(D)] = ex
    if len(g["examples"]) > 12:
        for k in sorted(g["examples"], key=int)[:-12]:
            g["examples"].pop(k)
    nc = g.get("newcomer")
    for n, a in sorted(real.items()):
        if not isinstance(a, dict):
            continue
        rows = _ws_rows(a.get("workshop"))
        acts = _acts_in(a)
        if rows:
            row["ws_written"] += 1
            if ex.get(n) and rows[0] == (ex[n]["輪"], ex[n]["道具"]):
                row["same_ex"] += 1
        if rows or acts:
            row["chose"] += 1
            row["chose_who"] = sorted(set(row["chose_who"]) | {n})[:20]
        if nc and n == nc["name"]:
            nc["answers"][str(D)] = {"workshop": [list(r) for r in rows], "acts": acts, "jobs": _job_count(a)}


def _job_count(a):
    """答えの仕事の数 (季節ごとの job と family の仕事の名前ごとの数)"""
    out = {}

    def add(part):
        if not isinstance(part, dict):
            return
        for j in [part.get("job")] + list((part.get("family") or {}).values() if isinstance(part.get("family"), dict) else []):
            act = j.get("activity") if isinstance(j, dict) else j if isinstance(j, str) else None
            if act:
                out[str(act)[:20]] = out.get(str(act)[:20], 0) + 1
    if isinstance(a.get("year"), dict):
        for v in a["year"].values():
            add(v)
    else:
        add(a)
    return dict(sorted(out.items(), key=lambda kv: (-kv[1], kv[0]))[:8])


def apply_answers(state, real):
    """集まりの答え (g7.apply_year から。G14 の note・guild のあと): 欄 workshop"""
    apply_workshop(state, real)


def fails_year(state, y):
    return [f for f in _g(state)["fails"] if f["year"] == y]


def season_consult(state, done_list):
    """季節の終わりの相談 (g7.consult_why): 読める大人が 1 人以下 (一度ずつ)・G15 に入った日から 5 年ごと"""
    rd = g10.readers(state)
    if len(rd) <= READERS_STOP:
        why = f"g15_readers_{len(rd)}"
        if not any(c["why"] == why for c in done_list):
            return {"why": why, "day": state["day"], "text": f"G15: 読める大人が {len(rd)} 人になった ({'・'.join(rd) or 'いない'}。0 人になると字はもどらない)"}
    return years_consult(state, done_list)


def years_consult(state, done_list):
    g, D = _g(state), state["day"]
    if D > g["start"] and (D - g["start"]) % (LATER_YEARS * YEAR) == 0:
        why = f"g15_years_{D}"
        if not any(c["why"] == why for c in done_list):
            return {"why": why, "day": D, "text": f"G15: G15 に入って {(D - g['start']) // YEAR} 年たった (5 年ごとの相談)"}
    return None


def path_consult(state, done_list):
    """年の終わり: 入口の手前 (e1 と e3 がそろったのに 3 つめがない。一度だけ) → まだ届いていない e1・e3 の道を、自分で選べる答える人が、
    G15 に入ってからのまる 2 年つづけて 0 人なら止めて相談 (一度ずつ) → 季節の終わりの相談"""
    g, D = _g(state), state["day"]
    n, ok = entrance_count(state)
    if "e1" in g["e"] and "e3" in g["e"] and n < 3 and not any(c["why"] == "g15_near" for c in done_list):
        return {"why": "g15_near", "day": D, "text": "G15: 入口の手前 (燃える石と水の作業場の 2 つがそろったが、3 つめがまだ)"}
    y = (D + 1) // YEAR - 1
    y0 = (g["start"] + 1) // YEAR
    for k in ("e1", "e3"):
        if k in g["e"] or (k == "e1" and not coal_on(state)):
            continue
        ys = [y - i for i in range(PATH_YEARS)]
        if ys[-1] < y0:
            continue
        if all(((g["path"].get(str(x)) or {}).get(k, 0) == 0) for x in ys):
            if not any(c["why"] == f"g15_path_{k}" and c.get("year") == y for c in done_list):
                return {"why": f"g15_path_{k}", "year": y, "day": D,
                        "text": f"G15 の {k} ({ES[k]}) の道を、自分で選べる答える人が {PATH_YEARS} 年つづけていなかった (仕組みのまちがいとして相談)"}
    return season_consult(state, done_list)


def report_lines(state):
    """報告に書くこと (止めない)"""
    g, out = _g(state), []
    y = _y(state)
    f = fails_year(state, y)
    if len(f) >= FAIL_REPORT:
        out.append(f"この年に、選んだのにできなかったこと {len(f)} 回: " + " / ".join(x["why"][:60] for x in f[-5:]))
    rd = g10.readers(state)
    if len(rd) <= READERS_REPORT:
        out.append(f"読める大人は {len(rd)} 人 ({'・'.join(rd) or 'いない'})")
    sm = g10.smiths_now(state)
    if len(sm) <= 1:
        out.append(f"黒い金属の腕のある人は {len(sm)} 人 ({'・'.join(sm) or 'いない'})")
    py = (state["day"] + 1) // YEAR
    if str(py) not in g["path"]:
        py -= 1
    rows = [g["path"].get(str(py - i)) for i in range(IDLE_YEARS)]
    if all(r and r.get("meetings") and (r.get("e1", 0) + r.get("e3", 0)) > 0 and r.get("chose", 0) == 0 for r in rows):
        out.append(f"選べた答える人はいるのに、水の作業場・燃える石を、だれも選ばなかった年が {IDLE_YEARS} 年つづいた")
    short = g13.field_short(state)
    if short:
        out.append(short)
    sd = era2.store_days(state)
    if sd < STORE_REPORT:
        out.append(f"蓄えが {sd} 日分 ({STORE_REPORT} 日分を切った)")
    s13 = state["era2"]["g7"]["g13"]
    st = [x["id"] for x in s13["mill"]["mills"] if x.get("stopped")]
    if st:
        out.append(f"止まっている水の輪: {'・'.join(st)} (直す手がなかった)")
    lost = [x for x in s13["canal"]["lost"] if x["year"] >= y - 1 and x["year"] >= g["start"] // YEAR]
    if lost:
        out.append(f"水の道がへった: {'・'.join(str(x['year']) + '年 ' + str(x['lost']) + ' つかみ分' for x in lost)} (手入れが足りなかった)")
    lr = next((r for r in reversed(g["ledger"]) if r["year"] in (y, y - 1)), None)
    if lr:
        big = sum(r["big"] for r in lr["ws"].values())
        noans = sum(r["big_noans"] for r in lr["ws"].values())
        if big and noans * 2 > big:
            out.append(f"{lr['year']}年の作業場の 8 人の日 {big} 日のうち {noans} 日は、答えた家の人がいなかった (写って動いた家だけ)")
    n, ok = entrance_count(state)
    if "e1" in g["e"] and "e3" in g["e"] and n < 3:
        out.append("入口の手前: 燃える石と水の作業場の 2 つがそろった (3 つめがまだ)")
    return out


def indicators(state):
    """G15 の目安 (era2.indicators に足す。【シ】)"""
    g = _g(state)
    y = _y(state)
    lr = next((r for r in reversed(g["ledger"]) if r["year"] in (y, y - 1)), None) or {}
    en = lr.get("energy") or {}
    return {**{f"g15_{k}_day": g["e"].get(k) for k in ES},
            "g15_ws": len(workshops(state, done=True)), "g15_ws_building": len(workshops(state, done=False)),
            "g15_big_days": max((r["big"] for r in (lr.get("ws") or {}).values()), default=0), "g15_e3_years": len(g["e3_years"]),
            "g15_coal_share": en.get("coal_share", 0.0), "g15_e1_years": len(g["e1_years"]), "g15_stoves": len([h for h in g["stoves"] if stove_done(state, h)]),
            "g15_coal_stock": round(g["coal"]["stock"]), "g15_planks": g["planks"]["stock"], "g15_kcal_pc": en.get("per_day", 0),
            "g15_output_pc": lr.get("output_pc", 0.0), "g15_e4_rises": len(g["e4_rises"]), "g15_region_food": lr.get("region_food_share", 1.0),
            "g15_readers": len(g10.readers(state)), "g15_smiths": len(g10.smiths_now(state)), "g15_fails": len(fails_year(state, y))}


# ---------------- お題 ----------------

def facts(state):
    """お題の決まりの文 (G15 から)。入口の名前と判定の文は書かない (5.3)"""
    out = (f"水の作業場: 回っている水の輪を、粉ひきに要る数を残して、作業場に作りかえられる ({WS_DAYS} 人日)。水ののこは川の力で木をひいて板にし (1 人 1 日 1 束。だれでも)、"
           f"水の槌は川の力で黒い金属をたたく (鎌 1 本 {HAMMER_DAYS} 人日。腕のある人がいる日だけ)。作業場の輪は粉をひかない。作業場も 1 年 {g13.MILL_REPAIR} 人日直さないと止まる。\n")
    if coal_on(state):
        out += (f"燃える石: 北の丘の崖に、火をつけると長く燃える黒い筋がある。掘ると 1 人 1 日 約 {COAL_KG_DAY} kg。家のかまどを石のかまどに作りかえると ({STOVE_DAYS} 人日)、"
                "倉の燃える石をまきのかわりに燃やす (まきの倍の熱)。まきは今も足りている。\n")
    out += "板: 水ののこでひいた板を使うと、水の輪を直す・建てる・作業場を作る・かまどを作りかえる・住まいの仕事が倍はかどる。\n"
    return out


def _readers_text(rd):
    return f"{'・'.join(rd)} の {len(rd)} 人" if rd else "いない"


def ws_line(state, name):
    """作業場の行 (答える人ごとに例の輪を変える。例は決まりのとおり通る形)"""
    g = _g(state)
    need = grind_need(state)
    c = candidates(state)
    sm = g10.smiths_now(state)
    rows = []
    if c:
        ex = examples(state).get(name) or {"輪": c[-1], "道具": SAW}
        rng = f"{c[0]}〜{c[-1]}" if len(c) > 1 else c[0]
        rows.append(f"- 水の作業場: 粉ひきに要る水の輪は {need} つ。残りの {len(c)} ({rng}) のうち 1 つを、作業場にできる (workshop)。"
                    f"作りかえるには {WS_DAYS} 人日 (主な仕事「{ACT_WS_BUILD}」、place に輪の名前)。")
    elif g["ws"]:
        rows.append(f"- 水の作業場: いまは、これより多くの輪を作業場にできない ({'作業場はもう ' + str(WS_MAX) + ' つ' if len(g['ws']) >= WS_MAX else '粉をひく輪が足りなくなる'})。")
        ex = None
    else:
        rows.append(f"- 水の作業場: いまは作業場にできる輪がない (粉ひきに要る輪 {need} つを残すと、回っている輪が足りない)。")
        ex = None
    rows.append(f"  水ののこ: 川の力で木をひいて板にする。だれでも働ける。板を使うと、輪の直しや建てる仕事が倍はかどる。")
    hm = f"  水の槌: 川の力で黒い金属をたたく。鎌 1 本が {g10.IRON_DAYS} 人日から {HAMMER_DAYS} 人日になる。"
    if sm:
        hm += f"黒い金属の腕のある人 ({'・'.join(sm)}) が作業場にいる日だけ。一緒に働いた人は腕を覚える。"
        mine = [n for n in sm if _house_of(state, n) == _house_of(state, name)]
        if name in sm:
            hm += "あなたは水の槌の作業場で教えられる。"
        elif mine:
            hm += f"あなたの家の {'・'.join(mine)} は水の槌の作業場で教えられる。"
    else:
        hm += "いま黒い金属の腕のある人がいないので、黒い金属はたたけない。"
    rows.append(hm)
    for mid in workshops(state):
        w = g["ws"][mid]
        y = _y(state)
        last = sum((_g(state)["wsyear"].get(str(yy)) or {}).get(mid, {}).get("big", 0) for yy in (y - 1,))
        if w["done"] is None:
            rows.append(f"  作業場 {mid} ({w['tool']}): あと 約 {max(0, round(WS_DAYS - w['work']))} 人日で使える (主な仕事「{ACT_WS_BUILD}」、place に {mid})")
        else:
            m = _mill(state, mid)
            rows.append(f"  作業場 {mid} ({w['tool']}): 使える{'' if not (m or {}).get('stopped') else ' (いまは止まっている。直すのは「' + g13.ACT_MILL_FIX + '」)'}。"
                        f"去年 8 人の日 {last} 日 (主な仕事「{ACT_WS_WORK}」、place に {mid}。1 日 {WS_CAP} 人まで)")
    tail = f"働くのは主な仕事「{ACT_WS_WORK}」(place に輪の名前。1 日 {WS_CAP} 人まで)"
    if c or g["ws"]:  # 前に決めておいた直し (下書き 7.1。決まりの村の B1S で e3 が 4 回に 2 回以下だった。G15_check.md 6.): 作業場で働ける家の大人を名前で (数は変えない)
        h = _house_of(state, name)
        fam = [p["name"] for p in era2.adults(state) if h and p.get("household") == h][:6]
        if fam:
            tail += f"。あなたの家の大人 {'・'.join(fam)} は作業場で働ける"
    if ex:
        rows.append(f"  書き方: \"workshop\": [{_js(ex)}]。{tail}")
    else:
        rows.append(f"  {tail}")
    return rows


def coal_line(state, p):
    g = _g(state)
    h = p.get("household")
    n = len([x for x in g["stoves"] if stove_done(state, x)])
    mine = "もう石のかまど" if h and stove_done(state, h) else (f"石のかまどに作りかえている途中 (あと 約 {max(0, round(STOVE_DAYS - g['stoves'][h]['work']))} 人日)"
                                                                if h in g["stoves"] else "まだまきのかまど")
    return [f"- 燃える石: 北の丘に、火をつけると長く燃える石の層がある (主な仕事「{ACT_DIG}」。1 人 1 日 約 {COAL_KG_DAY} kg)。家のかまどを「石のかまど」に作りかえると "
            f"(主な仕事「{ACT_STOVE}」。家の大人で {STOVE_DAYS} 人日)、倉の燃える石をまきのかわりに燃やす。",
            f"  まきは足りているので、暮らしの得はない。あなたの家 ({h}) のかまどは、{mine}。いま石のかまどの家 {n}・村の倉の燃える石 {round(g['coal']['stock'])} kg"]


def read_line(state, name):
    rd = g10.readers(state)
    if not rd:
        return "- 字: いま読める人がいないので、字を習えない"
    ln = (f"- 字: 読める人は {_readers_text(rd)}。読めない大人は、主な仕事「{g10.ACT_LEARN}」を {g10.LEARN_DAYS} 日すると読めるようになる "
          f"({'どちらか' if len(rd) == 2 else 'だれか'}が村にいる日。教える人の手間は要らない)")
    mine = [n for n in rd if _house_of(state, n) == _house_of(state, name)]
    if name in rd:
        ln += "。あなたがいる日に、ほかの人が字を習える"
    elif mine:
        ln += f"。あなたの家の {'・'.join(mine)} がいる日に、ほかの人が字を習える"
    return ln


def prompt_block(state, p):
    """「## いま」の答えの並びのすぐ前に置く短い節 (G15 に入る日から。G12〜G14 の学び)。G14 の節は「続けること」の 1 行に、G12・G13 も同じ行にまとめる。
    その人がこの集まりでできること (水の作業場・燃える石・字)・続けること・いまの進み。せかす言葉は書かない"""
    if not p:
        return ""
    name = p["name"]
    rows = [BLOCK_HEAD.replace("あなたが", f"あなた ({name}) が", 1)]
    rows += ws_line(state, name)
    if coal_on(state):
        rows += coal_line(state, p)
    rows.append(read_line(state, name))
    rows.append(g14.keep_line(state, p))
    rows.append("- workshop は答えた人の中でいちばん多い中身に決まる (1 人の答えでも決まる)。書かないなら \"workshop\": []")
    rows.append("いまの進み (水の作業場と燃える石):")
    rows += progress_lines(state)
    return "\n".join(rows) + "\n"


def progress_lines(state):
    """いまの進み (村の人が見て分かる数だけ。e2・e5 は出さない)"""
    g, y = _g(state), _y(state)
    out = []
    if "e3" in g["e"]:
        out.append(f"- 水の作業場: 届いた ({g['e']['e3']} 日目)")
    else:
        lr = next((r for r in reversed(g["ledger"]) if r["year"] in (y, y - 1)), None) or {}
        big = max((r["big"] for r in (lr.get("ws") or {}).values()), default=0)
        out.append(f"- 水の作業場: いま {len(workshops(state, done=True))}{f' (去年 8 人の日 {big} 日)' if lr and g['ws'] else ''}。1 つの作業場で、3 つ以上の家の大人が 8 人以上同じ日に働いた日が、"
                   f"1 年に {E3_DAYS} 日。それが {E3_YEARS} 年つづくと届く")
    if coal_on(state):
        if "e1" in g["e"]:
            out.append(f"- 燃える石: 届いた ({g['e']['e1']} 日目)")
        else:
            lr = next((r for r in reversed(g["ledger"]) if r["year"] in (y, y - 1)), None) or {}
            sh = (lr.get("energy") or {}).get("coal_share")
            out.append(f"- 燃える石: いま {round(sh * 10) if sh else 0} 割。1 年の火と力の半分を燃える石がまかなう年が {E1_YEARS} 年つづくと届く")
    if "e4" in g["e"]:
        out.append(f"- 作ったもの: 届いた ({g['e']['e4']} 日目)")
    else:
        out.append(f"- 作ったもの: 1 人あたりの作ったもの (刈り入れと使った品) の {E4_WIN} 年の平均が、{E4_RISES} 回つづけて上がると届く (いま {len(_rises_run(state))} 回)")
    return out


def _rises_run(state):
    g = _g(state)
    if not g["e4_rises"]:
        return []
    y = max(int(k) for k in g["out"]) if g["out"] else -1
    run = []
    while (y - len(run)) in g["e4_rises"]:
        run.append(y - len(run))
    return run


def text(state, p):
    """お題の節「## 水の作業場と燃える石」(長い節。短い節と重なる行は書かない)"""
    g, y = _g(state), _y(state)
    rows = []
    for mid in workshops(state):
        w = g["ws"][mid]
        r = (g["wsyear"].get(str(y)) or {}).get(mid) or (g["wsyear"].get(str(y - 1)) or {}).get(mid) or {}
        rows.append(f"- 作業場 {mid} ({w['tool']}): " + ("作っている途中" if w["done"] is None else f"{w['done']} 日目から使える")
                    + (f"。働いた {r.get('days', 0)} 人日・8 人の日 {r.get('big', 0)} 日" if r else "")
                    + (f"・板 {r.get('planks', 0)} 束" if r.get("planks") else "") + (f"・槌の日 {r.get('iron', 0)}" if r.get("iron") else ""))
    if coal_on(state):
        c = g["coal"]
        rows.append(f"- 燃える石: 掘った {round(sum(c['dug'].values()))} kg・燃やした {round(sum(c['burned'].values()))} kg・村の倉 {round(c['stock'])} kg・"
                    f"石のかまどの家 {len([h for h in g['stoves'] if stove_done(state, h)])}")
    rows.append(f"- 村の倉の板 {g['planks']['stock']} 束・黒い金属の鎌 {len(g10.iron_tools(state))} 本")
    f = [x for x in g["fails"] if x["year"] >= y - 1][-4:]
    if f:
        rows.append("- 水の作業場と燃える石で、できなかったこと: " + " / ".join(x["why"] for x in f))
    return "\n## 水の作業場と燃える石\n" + "\n".join(rows) + "\n"


def feel_note(state, p):
    """気持ちだけのお題の行 (代表に伝えられることだけ)"""
    return "\n- 水の作業場・燃える石のことを、家の代表に伝えられる"


def field_rows(state, year=False):
    """答えの欄の説明 (g7._field_rows に足す)"""
    return [f"   水の作業場: 主な仕事を「{ACT_WS_BUILD}」「{ACT_WS_WORK}」にできる (大人ならだれでも。place に輪の名前)",
            "   workshop: 作業場にする輪と道具 (水ののこ か 水の槌)。例 [{\"輪\": \"M24\", \"道具\": \"水ののこ\"}]"]


# 答えの形 (JSON) の欄の宣言 (第 8 部の前の直し 2。g7.later_fields_json が答えの形に自動で足す。g7.answer_fields・tools/prompt_check.py が読む)
ANSWER_FIELDS = {"workshop": "[]"}


def answer_fields(state):
    return ["workshop"]


def acts(state):
    """いま選べる G15 の仕事 (燃える石の 2 つは置いた世界だけ)"""
    out = [ACT_WS_BUILD, ACT_WS_WORK]
    if coal_on(state):
        out += [ACT_DIG, ACT_STOVE]
    return out


def can_do(state, act):
    return act in acts(state)


def rest_why(state, name, act):
    if act in (ACT_DIG, ACT_STOVE) and not coal_on(state):
        return f"{name} は、燃える石のある所を知らないので、休んだ"
    return None


SECTION = "## 水の作業場と燃える石"  # 長い節の見出し (tools/prompt_check.py --words g15 が読む)
FACT_HEADS = ("水の作業場:", "燃える石:", "板:")  # 決まりの文の行の頭 (同じ)


# ---------------- 作る側の反実仮想の後押し (本人の言葉 2026-11-16「１フェーズ進めて下さい。何か問題があってもあなた方で反実仮想でよい風に進めて下さい」。
#   docs/society_phase/G15_push.md) ----------------
# 本物の村の 5 年の相談 (198年60日目 = 23819 日目) で step.py resume --push "<本人の言葉>" が印 g7.g15.push を書いた日から、作る側が季節ごとに手を足す。
# 村の人の選んだことではない。村の人のお題には出さない (出来事にも残さない。state・step.py status・年報に残す)。集まりの LLM の答えは今までどおり読み、
# その季節の仕事を当てたあと (g7._apply の終わり) に、次の手を足すだけ (決まりの村の束 G15B1 の手の配り方をもとにした):
#   - 手を回すのは、この季節の仕事が「休む」の大人と、「狩り」「採集」の大人の半分まで、草取りだけの冬と春は「畑仕事」の大人の 4 分の 1 まで。
#     答えた人本人は動かさない。休む人・写しと決まりの家の人を先に (ヤギ・水・役・作る仕事と、夏・秋の刈り入れ・まきつけからは人を取らない)
#   - 水の輪の直しと水の道の手入れ: その年に足りない人日を埋める (止まった輪を直し、水の来る畑を守る = 食べ物を守る)
#   - 水の作業場: 作業場ごとに 4 家以上から 12 人 (1 家 3 人まで。作業場の 20 人の枠の残りまで)。毎季節。e3 の「8 人・3 家・30 日」に余裕
#   - 2 つめの作業場 (水ののこ): 作る側が決めて作る (村の票ではない)。板は、休んでいる大人が自分の家の住まいを建てる・広げるのに使う (板の数だけ)。
#     e4 の帳簿は「使った板 × 60」を作ったものに数える (設計 3.6)。刈り入れがふえるわけではない (G15_push.md に正直に書く)
#   - かまど: まだ石のかまどでない家の大人 1 人が「かまどを作りかえる」(できたら、その季節の残りは燃える石を掘る)
#   - 燃える石: 石のかまどの家の 1 季節分の 1.25 倍が倉にあるように、掘る人を足す
# どれも印 (g7.g15.push) があるときだけ。印のない日 (前の日) は 1 バイトも変わらない。
PUSH_FROM = 23819  # 本物の村の G15 の 5 年の相談の日 (198年60日目)。これより前には印を書けない
PUSH_DATE = "2026-11-16"
PUSH_NAME = "作る側の反実仮想の後押し"
PUSH_SRC = "作る側の後押し"  # g7.src の値 (写しの記録 g7.gpath では push に分ける)
PUSH_WS_PEOPLE, PUSH_WS_PER_HOUSE, PUSH_WS_BUILD = 12, 3, 6
PUSH_WS_COUNT = 2  # 後押しで使う水ののこの作業場の数 (村の作業場 1 つ + 作る側が決める 1 つ)
PUSH_HOUSE_MAX = 24  # 板で住まいを建てる・広げる人 (1 季節)
PUSH_COAL_KEEP = 1.25
PUSH_KEEP = 40
# 後押しの手 (lever)。step.py resume --push "<本人の言葉>" --levers a,b,c で選ぶ (2026-11-17 本人の言葉の読み直し「いくつかの筋を並べて、いちばんよい筋で進める」。
# 筋 (写しの村) ごとにちがう組を入れて、決まりの村と LLM の年でくらべる)。state の g7.g15.push.levers に組を残す
LEVERS = {"food": "水の輪の直しと水の道の手入れ (食べ物を守る)",
          "ws": "水の作業場に 4 家以上から 12 人 (e3)",
          "coal": "かまどを石のかまどに・燃える石を掘る (e1)",
          "ws2": "2 つめの水の作業場 (水ののこ) を作る側が決めて作り、そこで働く (e4)",
          "house": "のこの板で住まいを建てる・広げる (使った板は作ったものに数える。e4)"}
LEVER_ORDER = ("food", "ws", "coal", "ws2", "house")
ACT_HOUSE = "住まいを建てる"


def push_on(state):
    """後押しが動いているか (印があり、まだ止めていない。止めた印 push.ended は step.py resume --unpush だけが書く。2026-11-17)"""
    pu = _g(state).get("push") if on(state) else None
    return bool(pu) and pu.get("ended") is None


def push_why(words):
    return f"{PUSH_NAME} (本人の言葉 {PUSH_DATE} 「{words}」)"


def parse_levers(text):
    """--levers の文 → 手の並び (LEVER_ORDER の順)。書かなければみな。知らない名前があれば ValueError"""
    if text is None or not str(text).strip():
        return list(LEVER_ORDER)
    xs = [x.strip() for x in str(text).replace("・", ",").split(",") if x.strip()]
    bad = [x for x in xs if x not in LEVERS]
    if bad:
        raise ValueError(f"知らない手: {'・'.join(bad)} (選べるのは {','.join(LEVER_ORDER)})")
    return [x for x in LEVER_ORDER if x in xs]


def push_levers(state):
    return set((_g(state).get("push") or {}).get("levers") or ())


def push_refusal(state, words):
    """resume --push ができないわけ (できるなら None)"""
    if not (words or "").strip():
        return "--push には本人の言葉が要る"
    if not on(state):
        return "G15 でないので、後押しはできない"
    if _g(state).get("push"):
        return "後押しはもう始めてある"
    if state["day"] < PUSH_FROM:
        return f"後押しは {PUSH_FROM} 日目 (G15 の 5 年の相談) からだけ"
    if ((state["era2"]["g7"].get("hold") or {}).get("why")) != "consult":
        return "後押しは、相談で止まっているときに resume と一緒にだけ始める"
    return None


def mark_push(state, words, levers=None):
    """resume --push から: 印 g7.g15.push を書く (村の出来事には残さない。村の人のお題に出さないため)。levers: 手の並び (なければみな)"""
    words = words.strip()
    lv = list(LEVER_ORDER) if levers is None else [x for x in LEVER_ORDER if x in levers]
    _g(state)["push"] = {"day": state["day"], "words": words, "why": push_why(words), "from": "決まりの村の束 G15B1 の手の配り方",
                         "levers": lv, "ws2": None, "seasons": {}}
    return _g(state)["push"]


def push_src(state, name):
    """その人のこの季節の仕事が、後押しで決まったか"""
    return (state["era2"]["g7"].get("src") or {}).get(name) == PUSH_SRC


def push_act(state, p, act):
    """g7.role_day から: 後押しで「かまどを作りかえる」になった人は、その家のかまどができていれば燃える石を掘る。
    後押しで「水の作業場を作る」になった人は、作りかけの作業場がなくなっていれば (できあがっていれば)、その作業場で働く"""
    if not (push_on(state) and push_src(state, p["name"])):
        return act
    h = (_g(state)["push"].get("stove_for") or {}).get(p["name"]) or p.get("household")
    if act == ACT_STOVE and h and stove_done(state, h) and coal_on(state):
        p["plan"]["place"] = COAL_PLACE
        return ACT_DIG
    if act == ACT_WS_BUILD and not workshops(state, done=False) and workshops(state, done=True):
        p["plan"]["activity"] = ACT_WS_WORK
        return ACT_WS_WORK
    return act


PUSH_FROM_ACTS = ("休む", "狩り", "採集", "畑仕事")  # 後押しで手を回せる仕事 (この順に。ヤギ・水・役・作る仕事からは取らない)
PUSH_HUNT_SHARE = 0.5  # 狩り・採集の人は、その季節の半分までしか回さない (食べ物を守る)
PUSH_FIELD_SHARE, PUSH_FIELD_SEASONS = 0.25, ("冬", "春")  # 畑仕事の人は、草取りだけの冬と春に、4 分の 1 までしか回さない (夏・秋の刈り入れとまきつけからは取らない)


def _push_pool(state):
    """後押しで手を回せる大人: この季節の仕事が「休む」の大人と、「狩り」「採集」の大人の半分まで、冬と春は「畑仕事」の大人の 4 分の 1 まで (答えた人本人は除く)。
    休む人を先に、写しと決まりの家の人を先に、人の並びの順"""
    import g7
    g7s = state["era2"]["g7"]
    src = g7s.get("src") or {}
    answered = set((g7s.get("step") or {}).get("answered") or [])
    order = {p["name"]: i for i, p in enumerate(state["people"])}
    ads = era2.adults(state)
    rest = [p for p in ads if (p.get("plan") or {}).get("activity") == "休む" and p["name"] not in answered]
    food = [p for p in ads if (p.get("plan") or {}).get("activity") in PUSH_FROM_ACTS[1:3]]
    food_ok = [p for p in food if p["name"] not in answered]
    field = [p for p in ads if (p.get("plan") or {}).get("activity") == PUSH_FROM_ACTS[3]] if g7.season(state["day"] + 1) in PUSH_FIELD_SEASONS else []
    field_ok = [p for p in field if p["name"] not in answered]

    def key(p):
        return (g7.gpath_kind(src.get(p["name"])) == "answered", order[p["name"]])
    return (sorted(rest, key=key) + sorted(food_ok, key=key)[:int(len(food) * PUSH_HUNT_SHARE)]
            + sorted(field_ok, key=key)[:int(len(field) * PUSH_FIELD_SHARE)])


def _push_set(state, p, act, place="camp", mill=None):
    p["plan"] = {"activity": act, "place": place, "with": []}
    state["era2"]["g7"].setdefault("src", {})[p["name"]] = PUSH_SRC
    if mill:
        _g(state)["dest"][p["name"]] = mill
    else:
        _g(state)["dest"].pop(p["name"], None)


def _push_ws2(state, pu):
    """2 つめの作業場 (水ののこ): 作業場にできる輪があれば、作る側が決める (村の票ではない。出来事にもしない。作るのは後押しの人)"""
    g = _g(state)
    if pu.get("ws2") or len(g["ws"]) >= PUSH_WS_COUNT:
        return
    c = candidates(state)
    if not c or ws_why(state, c[-1], SAW):
        return
    mid = c[-1]
    g["ws"][mid] = {"tool": SAW, "day": state["day"], "by": [PUSH_SRC], "votes": PUSH_NAME, "work": 0.0, "done": None, "builders": {}}
    pu["ws2"] = mid


def push_season(state):
    """季節のはじめ (g7._apply の終わり。その季節の仕事が決まったあと): 後押しの手を足す。乱数なし"""
    import g13
    g, pu, D = _g(state), _g(state)["push"], state["day"]
    famine = state["era2"]["g7"].get("ask") == "集まり直し"
    ads = era2.adults(state)
    pool = _push_pool(state)
    used = set()
    row = {"pool": len(pool), "ws": {}, "build": 0, "house": 0, "stove": 0, "dig": 0, "mill_fix": 0, "canal": 0, "short": []}

    def doing(*acts):
        return sum(1 for p in ads if (p.get("plan") or {}).get("activity") in acts)

    def take(n, house=None, per_house=None):
        out, cnt = [], {}
        for p in pool:
            if len(out) >= n:
                break
            h = p.get("household") or p["name"]
            if p["name"] in used or (house is not None and h != house) or (per_house and cnt.get(h, 0) >= per_house):
                continue
            out.append(p)
            cnt[h] = cnt.get(h, 0) + 1
            used.add(p["name"])
        return out

    lv = push_levers(state)
    s13 = state["era2"]["g7"].get("g13") if "food" in lv else None
    if s13 and g13.can_do(state, g13.ACT_MILL_FIX):  # 水の輪の直し: 止まった輪とこの年の直しの残り
        need = g13.repair_left(state) - doing(g13.ACT_MILL_FIX, g13.ACT_MILL) * SEASON_DAYS
        for p in take(max(0, math.ceil(need / SEASON_DAYS))):
            _push_set(state, p, g13.ACT_MILL_FIX)
            row["mill_fix"] += 1
    if s13:  # 水の道の手入れ: その年に要る人日の残り
        c = s13["canal"]
        need = c["cap"] / g13.CANAL_PER_DAY * g13.CANAL_KEEP - c["dug"].get(str(_y(state)), 0) - doing(g13.ACT_CANAL) * SEASON_DAYS
        for p in take(max(0, math.ceil(need / SEASON_DAYS))):
            _push_set(state, p, g13.ACT_CANAL)
            row["canal"] += 1
    if not famine:
        if "ws2" in lv:
            _push_ws2(state, pu)
        for mid in [m for m in workshops(state, done=False) if m == pu.get("ws2")]:  # 作りかけの作業場 (60 人日。板で倍)
            for p in take(PUSH_WS_BUILD, per_house=2):
                _push_set(state, p, ACT_WS_BUILD, mill=mid)
                row["build"] += 1
        saw = 0
        for mid in workshops(state, done=True):
            if ("ws2" if mid == pu.get("ws2") else "ws") not in lv:
                continue
            m = _mill(state, mid)
            if m is None or m.get("stopped"):
                row["short"].append(f"{mid} は止まっている")
                continue
            there = sum(1 for p in ads if (p.get("plan") or {}).get("activity") == ACT_WS_WORK and _pick_ws(state, p["name"], ACT_WS_WORK) == mid)
            ws = take(max(0, min(PUSH_WS_PEOPLE, WS_CAP - there)), per_house=PUSH_WS_PER_HOUSE)
            for p in ws:
                _push_set(state, p, ACT_WS_WORK, mill=mid)
            houses = {p.get("household") for p in ws}
            row["ws"][mid] = [len(ws), len(houses)]
            if g["ws"][mid]["tool"] == SAW:
                saw += len(ws) + there
            if len(ws) < E3_PEOPLE or len(houses) < E3_HOUSES:
                row["short"].append(f"{mid} は {len(ws)} 人・{len(houses)} 家しか回せなかった")
        if coal_on(state) and "coal" in lv:
            new_h = set()
            pu["stove_for"] = {}
            left = []
            for h in sorted({p.get("household") for p in ads if p.get("household")}):
                if stove_done(state, h):
                    continue
                got = take(1, house=h)
                for p in got:
                    _push_set(state, p, ACT_STOVE)
                    row["stove"] += 1
                    new_h.add(h)
                if not got:
                    left.append(h)
            for h in left:  # その家に回せる大人がいない家: ほかの家の大人が手伝って作りかえる (後押しのときだけ)
                for p in take(1):
                    _push_set(state, p, ACT_STOVE)
                    pu["stove_for"][p["name"]] = h
                    row["stove"] += 1
                    new_h.add(h)
            homes = sum(1 for p in _people(state) if p.get("household") and (stove_done(state, p["household"]) or p["household"] in new_h))
            need = homes * COAL_KG * SEASON_DAYS * PUSH_COAL_KEEP - g["coal"]["stock"]
            for p in take(max(0, math.ceil(need / (COAL_KG_DAY * SEASON_DAYS)))):
                _push_set(state, p, ACT_DIG, place=COAL_PLACE)
                row["dig"] += 1
        homes = state["era2"].get("homes") or {}
        n_house = 0 if "house" not in lv else min(PUSH_HOUSE_MAX, saw + g["planks"]["stock"] // SEASON_DAYS)  # 板の数だけ (のこの人 1 人 = 1 日 1 束)
        small = [p for p in pool if p["name"] not in used and p.get("household") and (homes.get(p["household"]) or {}).get("size", 0) < era2.HOUSE_MAX]
        for p in small[:n_house]:
            used.add(p["name"])
            _push_set(state, p, ACT_HOUSE)
            row["house"] += 1
    pu["seasons"][str(D)] = row
    if len(pu["seasons"]) > PUSH_KEEP:
        for k in sorted(pu["seasons"], key=int)[:-PUSH_KEEP]:
            pu["seasons"].pop(k)


def push_lines(state, y=None):
    """後押しの行 (step.py status・年報。村の人のお題には出さない): 印・季節ごとの手"""
    pu = _g(state).get("push") if on(state) else None
    if not pu:
        return []
    out = [f"{pu['why']}。{pu['day']} 日目から。村の人の選んだことではない (村の人のお題には出さない)。手: "
           + ("・".join(f"{k} {LEVERS[k]}" for k in pu.get("levers") or []) or "なし")]
    ss = [(int(d), r) for d, r in pu["seasons"].items() if y is None or (int(d) + 1) // YEAR == y]
    for d, r in sorted(ss)[-4:]:
        out.append(f"{d + 1} 日目からの季節: 休んでいた大人 {r['pool']} 人から、作業場 " + ("・".join(f"{k} {v[0]} 人 ({v[1]} 家)" for k, v in r["ws"].items()) or "なし")
                   + f"・作業場を作る {r['build']}・板で住まい {r['house']}・かまど {r['stove']}・燃える石を掘る {r['dig']}・水の輪の直し {r['mill_fix']}・水の道 {r['canal']}"
                   + (f" ({'・'.join(r['short'])})" if r["short"] else ""))
    if pu.get("ws2"):
        out.append(f"2 つめの作業場 {pu['ws2']} (水ののこ) は作る側が決めた (村の票ではない)")
    if pu.get("ended") is not None:
        out.append(f"後押しは {pu['ended']['day']} 日目に止めた ({pu['ended']['why']})。そのあとは手を回さない "
                   "(作業場・石のかまど・倉の燃える石・板・住まいは、そのまま残る)")
    return out


# ---------------- 後押しなしの確かめ (本人の言葉 2026-11-17「後押しなしで確かめる」。docs/society_phase/G15_push.md 7.) ----------------
# 入口 (HOLD entrance) に着いたあと、本人が「後押しを外して村人だけで数年回し、作業場と燃える石が続くかを見てから、Society 3.0 の設計に入る」を選んだ。
# step.py resume --unpush "<本人の言葉>" --years N だけが、後押しを止め (push.ended)、印 g7.g15.after を書き、入口の止まりを解く (G15 のまま進む。
# 入口は g7.ends に残っているので、もう一度 HOLD entrance にはならない。入口の物差しは記録のために年の終わりに見つづける)。
# 確かめの年ごとに、後押しのない物差しの行 (after.rows) を残し、最後の年の終わり (until_day) に HOLD consult で止める。
# 村の人のお題と出来事には何も出さない (印・行は state・step.py status・年報だけ)。印のない日 (前の日) は 1 バイトも変わらない。
AFTER_DATE = "2026-11-17"
AFTER_NAME = "後押しなしの確かめ"
AFTER_YEARS = (1, 10)  # --years に書ける年の数


def after_why(words):
    return f"{AFTER_NAME} (本人の言葉 {AFTER_DATE} 「{words}」)"


def after_on(state):
    """後押しなしの確かめのあいだか (印 g7.g15.after のあと・まだ止めていない・印を書いた日の次の日から)"""
    a = _g(state).get("after") if on(state) else None
    return bool(a) and a.get("end") is None and state["day"] > a["day"]


def unpush_refusal(state, words, years):
    """resume --unpush ができないわけ (できるなら None)"""
    if not (words or "").strip():
        return "--unpush には本人の言葉が要る"
    if not on(state) or state.get("era") != "G15":
        return "G15 でないので、後押しは止められない"
    pu = _g(state).get("push")
    if not pu:
        return "後押しの印がない (後押しをしていない村)"
    if pu.get("ended") is not None or _g(state).get("after"):
        return "後押しはもう止めてある (確かめは 1 回だけ)"
    h = state["era2"]["g7"].get("hold") or {}
    if not (state.get("hold") and h.get("why") == "entrance"):
        return "後押しを止めるのは、入口 (HOLD entrance) で止まっているときだけ"
    if not isinstance(years, int) or not AFTER_YEARS[0] <= years <= AFTER_YEARS[1]:
        return f"--years は {AFTER_YEARS[0]}〜{AFTER_YEARS[1]} 年"
    if (state["day"] + 1) % YEAR:
        return "後押しを止めるのは、年の終わりの日だけ"
    return None


def mark_unpush(state, words, years):
    """resume --unpush から: 後押しを止め (push.ended)、確かめの印 g7.g15.after を書く (村の出来事には残さない)。
    確かめは、印の次の日からの暦の年 years 年。終わりの日 until_day (その年の終わり) に HOLD consult で止める"""
    g, D = _g(state), state["day"]
    words = words.strip()
    why = after_why(words)
    g["push"]["ended"] = {"day": D, "words": words, "why": why}
    y0 = D // YEAR + 1
    g["after"] = {"day": D, "words": words, "why": why, "years": years, "from_year": y0, "to_year": y0 + years - 1,
                  "until_day": D + years * YEAR, "base": after_row(state, D // YEAR), "rows": {}, "end": None}
    return g["after"]


def after_row(state, y):
    """確かめの年の行 (年の終わりに。帳簿の行と道の見張りから): 作業場ごとの 8 人の日 (答えた家・写って動いた家の人がいたか)・燃える石・かまど・
    作ったもの・蓄え・ききん・読める大人・G15 の道を選んだ答える人"""
    g = _g(state)
    lr = next((r for r in g["ledger"] if r["year"] == y), None) or {}
    en = lr.get("energy") or {}
    ws = {}
    wl = lr.get("ws") or {}
    for mid in sorted(set(wl) | {m for m, v in (lr.get("ws_list") or {}).items() if v.get("done") is not None}, key=lambda m: (_num(m), m)):
        r = wl.get(mid) or {}
        big = r.get("big", 0)
        w = {"big": big, "days": r.get("days", 0), "houses": len(r.get("houses") or {})}
        if "big_ans" in r or "big_copy" in r or "big_other" in r or not r.get("big_push"):
            w.update({"ans": r.get("big_ans", 0), "copy": r.get("big_copy", 0), "other": r.get("big_other", 0)})
        if r.get("big_push"):
            w["push"] = r["big_push"]
        if "ans" not in w:
            w["ans"] = big - r.get("big_noans", 0)
        ws[mid] = w
    big = max((w["big"] for w in ws.values()), default=0)
    p = g["path"].get(str(y)) or {}
    ev = [e for e in state["events"] if e["day"] // YEAR == y]
    sh = en.get("coal_share", 0.0)
    return {"year": y, "ws": ws, "big": big, "e3_like": big >= E3_DAYS, "coal_share": sh, "e1_like": sh >= E1_SHARE,
            "stoves": len(lr.get("stoves") or []), "homes": lr.get("homes", 0), "coal_dug": lr.get("coal_dug", 0), "coal_burned": lr.get("coal_burned", 0), "coal_stock": lr.get("coal_stock", 0),
            "output_pc": lr.get("output_pc", 0.0), "store_days": lr.get("store_days", 0),
            "famine": sum(1 for e in ev if e["type"] == "蓄えが尽きる"), "starved": sum(1 for e in ev if e["type"] == "死" and "飢え" in e["text"]),
            "readers": len(lr.get("readers") or []), "pop": lr.get("pop", 0),
            "chose": p.get("chose", 0), "chose_who": list(p.get("chose_who") or []), "meetings": p.get("meetings", 0)}


def after_due(state):
    """確かめの終わりの日 (until_day の季節の終わり) か"""
    a = _g(state).get("after") if on(state) else None
    return bool(a) and a.get("end") is None and state["day"] >= a["until_day"]


def after_stop(state):
    """g7.check から、確かめの終わりの日に: 印に終わりを書き、相談の止まりの中身を返す (HOLD consult)"""
    a, D = _g(state)["after"], state["day"]
    a["end"] = D
    rows = [a["rows"].get(str(y)) for y in range(a["from_year"], a["to_year"] + 1)]
    e1 = sum(1 for r in rows if r and r["e1_like"])
    e3 = sum(1 for r in rows if r and r["e3_like"])
    return {"why": "g15_after_end", "day": D,
            "text": f"G15: 後押しなしの確かめの {a['years']} 年が終わった ({a['from_year']}年〜{a['to_year']}年。燃える石が火と力の半分以上の年 {e1}・"
                    f"作業場の 8 人の日が 30 日以上の年 {e3})。Society 3.0 に進むかを本人と相談する"}


def _yn(b):
    return "続いた" if b else "続かなかった"


def after_row_text(r, base=False):
    """確かめの年の行 (やさしい日本語。status と年報)"""
    ws = "・".join(f"{mid} {w['big']} 日 (" + (f"後押しの人がいた日 {w['push']}・" if w.get("push") else "")
                   + f"答えた家の人がいた日 {w['ans']}" + (f"・写って動いた家の人がいた日 {w['copy']}・どちらもいない日 {w['other']}" if "copy" in w else "")
                   + f"。働いた人日 {w['days']}・{w['houses']} 家)" for mid, w in r["ws"].items()) or "なし"
    head = f"{r['year']}年" + (" (後押しのあった年。くらべるため)" if base else "")
    t = (f"{head}: 作業場の 8 人・3 家の日 {ws} / 燃える石は火と力の {round(r['coal_share'] * 100, 1)}% (掘った {round(r['coal_dug'])} kg・燃やした {round(r['coal_burned'])} kg・年の終わりの倉 {round(r.get('coal_stock', 0))} kg)・"
         f"石のかまどの家 {r['stoves']} / {r['homes']} 家 / 1 人あたりの作ったもの {r['output_pc']} / 蓄え {r['store_days']} 日分・"
         + (f"ききん {r['famine']} 回" if r["famine"] else "ききんなし") + (f"・飢えて亡くなった {r['starved']} 人" if r["starved"] else "")
         + f" / 読める大人 {r['readers']} / G15 の道 (作業場・燃える石) を選んだ答える人 {r['chose']}" + (f" ({'・'.join(r['chose_who'][:6])})" if r["chose_who"] else ""))
    if base:
        return t
    return (t + f"。→ 後押しなしで、e1 のよう (燃える石が火と力の半分以上) は{_yn(r['e1_like'])}。"
            f"e3 のよう (1 つの作業場で 8 人・3 家の日が 30 日以上) は{_yn(r['e3_like'])}")


def after_lines(state, y=None):
    """後押しなしの確かめの行 (step.py status・年報。村の人のお題には出さない)。y があれば、その年の行だけ"""
    a = _g(state).get("after") if on(state) else None
    if not a:
        return []
    out = [f"{a['why']}。{a['day']} 日目に後押しを止めた。{a['from_year']}年〜{a['to_year']}年の {a['years']} 年を村の人だけで回して、"
           f"作業場と燃える石が続くかを見る。{a['until_day']} 日目 ({a['to_year']}年の終わり) で止めて相談する (HOLD consult)"
           + (f"。{a['end']} 日目に終わった" if a.get("end") is not None else "")]
    if y is None or y == a["from_year"] - 1:
        out.append(after_row_text(a["base"], base=True))
    ys = sorted(int(k) for k in a["rows"])
    for k in ys:
        if y is None or k == y:
            out.append(after_row_text(a["rows"][str(k)]))
    if y is None and not ys:
        out.append("まだ確かめの年が終わっていない (年の終わりに行を足す)")
    return out
