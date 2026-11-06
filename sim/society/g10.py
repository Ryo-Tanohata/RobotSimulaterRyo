"""G10「鉄と広い国」(第 6 部「鉄とお金の帝国」のはじめの G。2026-11-04 本人の決め「お任せします」。docs/society_phase/G10_design.md)

- G10 に入るのは step.py next_part --closed-by-decision だけ (G9 を本人の決めで閉じてから。g7.start_g10)。G9 までは、このファイルを読みこみもしない
  (g7・g9・hints・era2・yardstick は state の g7.g10 があるときだけ、関数の中で読みこむ)。だから G1〜G9 は、お題・state・出来事・乱数が前と 1 バイトも変わらない
- 条件 (3 つともそろうと G10 の終わり。部の終わりではない):
  c1 黒い金属の道具を使う【村が決めた】: 暦の 1 年に、夕方の刈り入れの人日 (道具があってもなくても、刈った人日のすべて) のうち、村で作った黒い金属の道具で
     刈った人日が半分以上 (少なくとも 1 年 100 人日)
  c2 字を読み書きできる人【村が決めた】: 読み書きできる大人のうち、この 1 年に「記録をつける」をした人の家 (書記の家) の外の人が 2 人以上
  c3 広いまとまり【地域で生まれた】: 決める段 (v2) が 4 以上の中心があり、そのまとまり (中心と、直接・間に入って払う集落) が地域の集落 (村をふくむ) の半分以上。
     中心は村でも、よその集落でもよい
- F: F1 黒い金属を村で作った / F2 音の字ができた / F3 広いまとまり (= c3) / F4 黒い金属の道具が 1 年に 30 人日
- G9 の物差し (c1〜c3・F) と G7 の国の物差しは「ならべて測る」(届けば記録するが、G10 は進めない)
- 足した仕組み (小さく 4 つ): 黒い金属を作る (札 H9-01 を入る日に開く・仕事「黒い金属を作る」・道具は G9 の道具の一覧に足す)・音の字と読み書き (札 H9-02・
  仕事「字を習う」・読み書きできる大人のいる家は、貸し借り・遠くとの約束・もめごとの量を覚えでなく字で比べる)・燃料と力の帳簿 (記録だけ)・
  広いまとまりの物差し (記録だけ)。札 1 枚 (H9-03 村ごと人を移す長。hint_cards_g10.json)
- 道の見張り (G9 から学んだこと): 1 年ごとに、条件 1・2 の道 (試せる札・作る仕事・習う仕事) がお題に出た集まりの数を数え、2 年つづけて 0 なら止めて相談
- 乱数は使わない。数はみな【仮定】。村の人に見せる文には「鉄」「国」「帝国」「アルファベット」と hints.FORBIDDEN の言葉を書かない (WORDS。試しで確かめる)
"""
import era2
import hints
from world import log, season

YEAR, SEASON_DAYS = era2.YEAR, era2.SEASON_DAYS
IRON = "黒い金属の鎌"  # 村で作る道具 (村の人に見せる呼び名)
CARD_IRON, CARD_ALPHA = "H9-01", "H9-02"  # 赤土からとる黒い金属・音 1 つに字 1 つ
ACT_MAKE, ACT_LEARN = "黒い金属を作る", "字を習う"  # 新しい仕事 (world.ACTS7 に足した。G10 で使えるときだけ選べる)
IRON_DAYS = 20  # 黒い金属の鎌 1 本に要る働き (人日。赤土を掘る・炭を焼く・焼く・たたくをまとめた日数)【仮定】
IRON_CHAR_KG = 14  # 鎌 1 本 (約 1 kg) に要る炭 (kg。10〜18 kg のまん中【未確認】)。燃料と力の帳簿に書くだけ (森は減らさない)
LEARN_DAYS = 30  # 字を習う日がこれだけになると、読み書きできる人【仮定】
C1_SHARE, C1_MIN = 0.5, 100  # c1: 刈る人日の半分以上・少なくとも 1 年 100 人日
C2_READERS = 2  # c2: 書記の家の外の、読み書きできる大人
C3_D, C3_SHARE = 4, 0.5  # c3: 決める段 4 以上・地域の集落の半分以上
F4_DAYS = 30  # F4: 黒い金属の道具で 1 年に 30 人日
PATH_YEARS = 2  # 道の見張り: 条件の道が 2 年つづけてお題に出なければ止めて相談
WORDS = ("鉄", "国", "帝国", "アルファベット") + hints.FORBIDDEN  # 村の人に見せる G10 の文に書かない言葉
FS = {"F1": "黒い金属を村で作った", "F2": "音の字ができた", "F3": "広いまとまり", "F4": "黒い金属の道具が 1 年に 30 人日"}
CS = {"c1": "黒い金属の道具を使う", "c2": "字を読み書きできる人", "c3": "広いまとまり"}
# 2026-11-05 本人の決め「直して 5 年続ける」(docs/society_phase/G10_stall.md 7.): この日 (134年の年の集まり) からの直し 4 つ。前の日は 1 バイトも同じ
#   ① お題: 便りを知っている人に「あなたは試せる (try に番号)」、作れる人に「あなたは作れる」を出し、節に知っている人・作れる人の名前と一緒に覚える道を書く
#   ② 試す・黒い金属を作る・字を習うが選べず「休む」にしたとき、わけを出来事に残す (g7.job → g7.count_day。お題の自分のことに出る)
#   ③ 作れる人・試している人の家を、ふつうの見本の家に足す (g7.choose・g7.g10_sample_add)
#   ④ 道の見張りは、お題に答える人 (代表) が選べる道だけを数える (paths)
G10_FIX_FROM = 16079


def on(state):
    return "g10" in ((state.get("era2") or {}).get("g7") or {})


def _g(state):
    return state["era2"]["g7"]["g10"]


def _g9(state):
    return state["era2"]["g7"]["g9"]


def _tech(state, card):
    return ((state["era2"]["g7"].get("hints") or {}).get("tech") or {}).get(card) or {}


def _alive_adults(state):
    return era2.adults(state)


def fixed(state):
    """2026-11-05 の直し が効くか: G10_FIX_FROM より後の日はいつも。G10_FIX_FROM の日 (お題はもう出ていた) は、
    step.py refresh_prompts が g7.g10.fix を書いたあとだけ (だから、その日までの歩をやり直しても、state もお題も前と 1 バイトも同じ)"""
    return on(state) and (state["day"] > G10_FIX_FROM or (state["day"] == G10_FIX_FROM and "fix" in _g(state)))


def mark_fix(state, why):
    """refresh_prompts から: G10_FIX_FROM の日に、直しを今の歩から入れたことを g7.g10.fix に残す (その日より前なら何もしない)"""
    if on(state) and state["day"] >= G10_FIX_FROM and "fix" not in _g(state):
        _g(state)["fix"] = {"day": state["day"], "why": why}


def tryable(state):
    """いま試せる G10 の札 (開いていて、まだできていない) の並び"""
    return [c for c in (CARD_IRON, CARD_ALPHA) if _tech(state, c).get("open") is not None and not _tech(state, c).get("done")]


def knowers(state, card):
    """札を知っている (hints の knowers に入っている)、生きている大人 (名前の順)。便りが 3 年より前でも「忘れられた」でも、知っている人のまま"""
    return sorted(p["name"] for p in era2.adults(state) if hints.knows(state, p["name"], card))


def smiths_now(state):
    """黒い金属を作れる、生きている大人 (名前の順。札ができていなければ空)"""
    return sorted(p["name"] for p in era2.adults(state) if smith(state, p["name"])) if iron_ready(state) else []


def key_houses(state):
    """③ 見本の家に必ず足す家: 黒い金属を作れる人 (と、札 H9-01 がまだ試せるならそれを知っている人) と、
    試せる G10 の札をもう試しはじめている人 (試すの腕が 0 より大きい) のいる家 (名前の順)"""
    names = set(smiths_now(state))
    if CARD_IRON in tryable(state):
        names |= set(knowers(state, CARD_IRON))
    for card in tryable(state):
        if _tech(state, card).get("first") is not None:
            names |= {p["name"] for p in era2.adults(state) if p["skills"].get(f"試す:{card}", 0) > 0}
    return sorted({p.get("household") for p in era2.adults(state) if p["name"] in names and p.get("household")})


def rest_why(state, name, act, j, with_):
    """② 試す・黒い金属を作る・字を習うを「休む」に変えたわけ (村の人に見せる短い文)。G10_FIX_FROM より前は None"""
    if not fixed(state):
        return None
    if act == "試す":
        card = str((j or {}).get("try") or "").strip().upper()
        cs = hints.cards()
        if card not in cs:
            return f"{name} は、試す便りの番号 (try) が分からず、休んだ"
        nm = f"「{cs[card]['name']}」[{card}]"
        if card not in hints.open_techs(state):
            return f"{name} は、{nm} を試そうとしたが、いまは村で試せないので、休んだ"
        return f"{name} は、{nm} の便りを知らないので、試せず、休んだ (知っている人と一緒に試すなら、with にその人の名前を書く)"
    if act == ACT_MAKE:
        if not iron_ready(state):
            return f"{name} は、村でまだ黒い金属が作れないので、休んだ"
        return f"{name} は、黒い金属の作り方を知らないので、休んだ (作れる人と一緒に作るなら、with にその人の名前を書く)"
    if act == ACT_LEARN:
        if name in _g(state)["readers"]:
            return f"{name} は、もう字を読み書きできるので、字を習わず、休んだ"
        return f"{name} は、村に字を教えられる人がいないので、字を習えず、休んだ"
    return None


# ---------------- G10 に入る (g7.start_g10 から) ----------------

def start(state):
    """G10 の state を作る: G9 の物差し (条件・F・守り合った数) を g7.before.G9.g9 に写して数え直す (G9 の仕組みは、そのまま動く)・
    札の表のハッシュ (3 つのファイル)・待っている札で、要るものがそろったものを、入る日に開く (出来事「試す」)"""
    g7s, D = state["era2"]["g7"], state["day"]
    g9 = g7s["g9"]
    g7s.setdefault("before", {}).setdefault("G9", {})["g9"] = {"reached": dict(g9["reached"]), "c": dict(g9["c"]), "kept": g9["kept"],
                                                               "merchant": dict(g9.get("merchant") or {}), "used": dict(g9["used"])}
    g9["reached"], g9["c"], g9["kept"] = {}, {}, 0
    g = g7s["g10"] = {"start": D, "made": [], "forge": 0.0, "smiths": [], "pending_smiths": [], "readers": {}, "learn": {}, "reap": {},
                      "reached": {}, "c": {}, "path": {}, "fuel": [], "region": {}, "c3_log": [], "letters": 0, "opened": []}
    h = g7s.get("hints") or {}
    if h:
        sha = hints.cards_sha(state)
        h["cards_sha"] = sha
        h.setdefault("cards_log", []).append({"day": D, "sha": sha, "note": "G10 に入った日: 村ごと人を移す長の札 1 枚 (H9-03)"})
        log(state, "区切り", None, "よその便りの札の表に 1 枚を足した (G10 に入った日)", cards=sha)
        cs = hints.cards()
        for card, t in sorted(h.get("tech", {}).items()):  # 入る日に開く (今の決まりでは季節の終わりに開くので、1 季節おくれる。G10_design.md 3.1)
            if t.get("open") is None and t.get("wait") is not None and hints.needs_ok(state, cs[card].get("needs")):
                t["open"] = D
                g["opened"].append(card)
                log(state, "試す", None, f"よその便りで聞いた「{cs[card]['name']}」に要るものが村にそろい、試せるようになった", card=card)
    return g


# ---------------- 黒い金属を作る (仕事「黒い金属を作る」。g7.role_day から) ----------------

def iron_ready(state):
    """札 H9-01 の「試す」が終わって、村で黒い金属が作れるか"""
    return bool(_tech(state, CARD_IRON).get("done"))


def smith(state, name):
    """腕のある人: 札を試した人 (試すの腕が 0 より大きい) と、腕のある人と一緒に作って覚えた人"""
    p = next((q for q in state["people"] if q["name"] == name), None)
    return bool(p) and (p["skills"].get(f"試す:{CARD_IRON}", 0) > 0 or name in _g(state)["smiths"])


def can_make(state, name, with_=()):
    """「黒い金属を作る」を選べるか: 村で作れて、腕のある人か、腕のある人と一緒に (with) 作る人"""
    return iron_ready(state) and (smith(state, name) or any(smith(state, w) for w in with_ or ()))


def make_day(state, p, t):
    """仕事「黒い金属を作る」の 1 日: 働きをためる。IRON_DAYS 人日たまると鎌 1 本 (G9 の道具の一覧に足す。村のもの)。
    腕のない人が、腕のある人と同じ日に一緒に作ると、次の季節から腕のある人"""
    g, D = _g(state), state["day"]
    mates = [q for q in era2.adults(state) if q is not p and (q.get("today") or {}).get("activity") == ACT_MAKE]
    helped = [q for q in mates if q["name"] in ((p.get("plan") or {}).get("with") or []) and smith(state, q["name"])]
    if not iron_ready(state) or not (smith(state, p["name"]) or helped):
        t.setdefault("events", []).append(log(state, "休む", p["name"], f"{p['name']} は、黒い金属の作り方が分からず、休んだ"))
        return
    if not smith(state, p["name"]) and p["name"] not in g["pending_smiths"]:
        g["pending_smiths"].append(p["name"])
    g["forge"] = round(g["forge"] + 1.0, 3)
    t.setdefault("events", []).append(log(state, ACT_MAKE, p["name"], f"{p['name']} が、丘の赤い土を掘って炭と焼き、黒い金属をたたいた"
                                          + (f" ({'・'.join(q['name'] for q in helped)} に教わりながら)" if helped and not smith(state, p["name"]) else "")))
    while g["forge"] >= IRON_DAYS:
        g["forge"] = round(g["forge"] - IRON_DAYS, 3)
        _make_tool(state)


def _make_tool(state):
    """黒い金属の鎌 1 本を、G9 の道具の一覧に足す (iron: True。使う・しまうの決め (metal)・すり減りは赤い金属と同じ)"""
    g, g9, D = _g(state), _g9(state), state["day"]
    tid = f"B{g9['next_tool']}"
    g9["next_tool"] += 1
    g9["tools"].append({"id": tid, "name": IRON, "day": D, "from": "村", "side": "村", "uses": 0, "gone": None, "new": True, "iron": True})
    g["made"].append({"day": D, "id": tid})
    log(state, "道具", None, f"村で黒い金属の鎌ができた [{tid}] (村で作った黒い金属の鎌は {len(g['made'])} 本目)", tool=tid, iron=True)
    if len(g["made"]) == 1:
        _reach(state, "F1", D, f"村ではじめて黒い金属の鎌を作った [{tid}]")


def iron_tools(state):
    return [t for t in _g9(state)["tools"] if t.get("iron") and t["gone"] is None]


# ---------------- 刈る人日を数える (era2._day の夕方の刈り入れ・g9.reap から) ----------------

def reap_row(state):
    """この暦の年の刈る人日の行 {all: すべて, bronze: 赤い金属, iron: 黒い金属}"""
    return _g(state)["reap"].setdefault(str(state["day"] // YEAR), {"all": 0, "bronze": 0, "iron": 0})


def count_tool(state, tool):
    reap_row(state)["iron" if tool.get("iron") else "bronze"] += 1


# ---------------- 音の字と読み書き (仕事「字を習う」。g7.role_day から) ----------------

def alpha_ready(state):
    return bool(_g(state)["reached"].get("F2"))


def readers(state):
    """生きている大人のうち、読み書きできる人 (名前の順)"""
    rd = _g(state)["readers"]
    return sorted(p["name"] for p in era2.adults(state) if p["name"] in rd)


def can_learn(state, name):
    """「字を習う」を選べるか: 音の字ができていて、まだ読み書きできない大人で、村に読み書きできる人がいる"""
    return alpha_ready(state) and name not in _g(state)["readers"] and any(n != name for n in readers(state))


def learn_day(state, p, t):
    """仕事「字を習う」の 1 日: その日にキャンプにいる (出かけていない) 読み書きできる人がいれば、習った日を 1 日足す。LEARN_DAYS 日で読み書きできる人"""
    g, D = _g(state), state["day"]
    teach = [q["name"] for q in era2.adults(state) if q is not p and q["name"] in g["readers"] and not (q.get("today") or {}).get("away")]
    if not alpha_ready(state) or p["name"] in g["readers"] or not teach:
        t.setdefault("events", []).append(log(state, "休む", p["name"], f"{p['name']} は、字を教わる人がいなくて、休んだ"))
        return
    n = g["learn"][p["name"]] = g["learn"].get(p["name"], 0) + 1
    t.setdefault("events", []).append(log(state, ACT_LEARN, p["name"], f"{p['name']} が、粘土の板に音の字を書いて習った"))
    if n >= LEARN_DAYS:
        g["readers"][p["name"]] = D
        log(state, ACT_LEARN, p["name"], f"{p['name']} は、音の字を読み書きできるようになった", reader=True)


def _house_readers(state, h):
    return [p["name"] for p in era2.adults(state) if p["name"] in _g(state)["readers"] and p.get("household") == h]


def letters(state, side):
    """読み書きできる大人のいる家 (side が家の名) か、村 (side が「村」で、村に読み書きできる大人がいる) は、量を覚えでなく字で書いて比べる (G10 から)"""
    if not on(state):
        return False
    if side == "村":
        return bool(readers(state))
    return bool(_house_readers(state, side))


def letters_used(state):
    _g(state)["letters"] += 1


def scribe_houses(state):
    """書記の家: この 1 年 (g7.past の季節) に「記録をつける」をした人がいる家 (今の家で数える)"""
    names = {n for s in state["era2"]["g7"].get("past", []) for n, acts in s["days"].items() if acts.get(era2.ACT_RECORD)}
    return sorted({p.get("household") for p in state["people"] if p["name"] in names and p.get("household")})


def outside_readers(state):
    sh = set(scribe_houses(state))
    return [p["name"] for p in era2.adults(state) if p["name"] in _g(state)["readers"] and p.get("household") not in sh]


# ---------------- 物差し (乱数なし) ----------------

def _reach(state, f, day, why):
    g = _g(state)
    if f in g["reached"] or day is None:
        return
    g["reached"][f] = day
    if not state["era2"]["g7"].get("closed10"):  # G10 を閉じたあと (G11) は、出来事に出さない (数えて記録するだけ)
        log(state, "目盛り", None, f"目盛り: G10 の {f}「{FS[f]}」に届いた ({why})", g="G10", f=f)
    if f == "F3":
        _cond(state, "c3", day, why)


def _cond(state, c, day, why):
    g = _g(state)
    if c not in g["c"]:
        g["c"][c] = day
        if not state["era2"]["g7"].get("closed10"):  # G10 を閉じたあと (G11 で数え直すとき) は、出来事に出さない (G9 の 2026-11-05 の直しと同じ)
            log(state, "目盛り", None, f"目盛り: G10 の条件 {c[1:]}「{CS[c]}」に届いた ({why})", g="G10", c=c)


def region_now(state):
    """広いまとまり (c3) の物差し: 決める段 (yardstick.levels。v2) で、いちばん深いまとまりと、D 4 以上で地域の半分以上のまとまり (なければ None)"""
    import g7
    import yardstick
    lv = yardstick.levels(state)
    n = len(g7._setts(state)) if g7.region_on(state) else 0
    best = max(lv, key=lambda x: (x["D"], len(x["members"]), -region_num(x["top"])), default=None)
    hit = [x for x in lv if x["D"] >= C3_D and len(x["members"]) >= C3_SHARE * n]
    return lv, n, best, (max(hit, key=lambda x: (len(x["members"]), x["D"])) if hit else None)


def region_num(sid):
    return int(sid[1:]) if sid and sid[1:].isdigit() else 0


def _c3(state):
    import g7
    g, D = _g(state), state["day"]
    lv, n, best, hit = region_now(state)
    g["region"] = {"day": D, "settlements": n, "maxD": best["D"] if best else 0, "top": best["top"] if best else None,
                   "members": len(best["members"]) if best else 0}
    if hit and "F3" not in g["reached"]:
        reg = (state["era2"]["g7"].get("region") or {})
        dem = [[q["id"], q["day"], q.get("answer"), q.get("result")] for q in reg.get("demands", []) if q.get("from") == hit["top"] and q.get("to") == "V0"]
        g["c3_log"].append({"day": D, "top": hit["top"], "D": hit["D"], "members": len(hit["members"]), "settlements": n, "village": hit["village"],
                            "demands_to_village": dem})
        o = next((x for x in g7._others(state) if x["id"] == hit["top"]), None)
        _reach(state, "F3", D, f"決める段 {hit['D']} のまとまり ({o['name'] if o else '川辺の村'} {hit['top']} が中心。{len(hit['members'])} / {n} 集落。村は{hit['village']})")


def _fuel_year(state):
    """燃料と力の帳簿 (記録だけ。年の終わり): 人の働き (仕事の組ごとの人日)・黒い金属の鎌の炭・ヤギ・牛。世界は変えない。お題に出さない"""
    import g7
    g, D = _g(state), state["day"]
    y = D // YEAR
    work = {}
    for s in state["era2"]["g7"].get("past", []):
        for n, acts in s["days"].items():
            for a, k in acts.items():
                w = g7._work_of(a)
                work[w] = work.get(w, 0) + k
    made = sum(1 for m in g["made"] if m["day"] // YEAR == y)
    g["fuel"].append({"year": y, "day": D, "labour": dict(sorted(work.items())), "iron_made": made, "char_kg": made * IRON_CHAR_KG,
                      "goats": len(state["era2"].get("goats") or []), "cattle": len(state["era2"].get("cattle") or [])})
    g["fuel"] = g["fuel"][-40:]


def season_end(state):
    """G10 の季節の終わり (g7.season_end の、G9 の季節の終わりのあと・物差しの前): 腕・読み書きできる人 → c1・F4 → F2・c2 → c3 → 年の終わりの帳簿"""
    g, D = _g(state), state["day"]
    for n in g["pending_smiths"]:
        if n not in g["smiths"]:
            g["smiths"].append(n)
    g["smiths"].sort()
    g["pending_smiths"] = []
    row = reap_row(state)
    if row["iron"] >= F4_DAYS:
        _reach(state, "F4", D, f"この年に、黒い金属の道具で刈った人日が {row['iron']}")
    if row["iron"] >= max(C1_MIN, C1_SHARE * row["all"]) and row["iron"] > 0:
        _cond(state, "c1", D, f"この年に、刈った人日 {row['all']} のうち、黒い金属の道具で {row['iron']}")
    ta = _tech(state, CARD_ALPHA)
    if ta.get("done") and "F2" not in g["reached"]:
        who = sorted(p["name"] for p in era2.adults(state) if p["skills"].get(f"試す:{CARD_ALPHA}", 0) > 0)
        for n in who:
            g["readers"].setdefault(n, D)
        _reach(state, "F2", D, f"音 1 つに字 1 つの書き方ができた。試した人 {'・'.join(who[:6])}{' ほか' if len(who) > 6 else ''} は読み書きできる")
    out = outside_readers(state)
    if len(out) >= C2_READERS:
        _cond(state, "c2", D, f"記録をつける家の外に、読み書きできる大人が {len(out)} 人 ({'・'.join(out[:6])})")
    _c3(state)
    if (D + 1) % YEAR == 0:
        _fuel_year(state)


def reached(state, f):
    return bool(on(state) and _g(state)["reached"].get(f))


def done(state):
    return {c: c in _g(state)["c"] for c in CS}


def progress(state):
    """条件ごとの進み (止まりを数える。yardstick._stall が G10 で読む。G10_design.md 2.3)。
    c1: 0 札が試せない / 1 試せる / 2 だれかが試した / 3 作った (F1) / 4 1 年 30 人日 (F4)。
    c2: 0 試せない / 1 試せる / 2 だれかが試した / 3 音の字ができた (F2) / 4 書記の家の外に読める人が 1 人。
    c3: いちばん深いまとまりの段 × 100 + その集落の数"""
    g = _g(state)
    ti, ta = _tech(state, CARD_IRON), _tech(state, CARD_ALPHA)
    c1 = 4 if "F4" in g["reached"] else 3 if "F1" in g["reached"] else 2 if ti.get("first") is not None else 1 if ti.get("open") is not None else 0
    c2 = 4 if outside_readers(state) else 3 if "F2" in g["reached"] else 2 if ta.get("first") is not None else 1 if ta.get("open") is not None else 0
    r = g.get("region") or {}
    return {"c1": c1, "c2": c2, "c3": r.get("maxD", 0) * 100 + r.get("members", 0)}


# ---------------- 道の見張り (G10_design.md 2.4。集まりの答えのとき数え、年の終わりに見る) ----------------

def paths(state):
    """いまのお題に、条件 1・2 の道 (試せる札・作る仕事・習う仕事) が出ているか。
    ④ G10_FIX_FROM から: お題に答える人 (代表) のだれかが、その道を自分で選べるときだけ数える
    (条件 1: 札 H9-01 を知っている人か、黒い金属を作れる人が答える人にいる。条件 2: 札 H9-02 を知っている人か、字を習える人が答える人にいる)"""
    ti, ta = _tech(state, CARD_IRON), _tech(state, CARD_ALPHA)
    if fixed(state):
        ans = era2.answerers(state)
        c1 = (CARD_IRON in tryable(state) and any(hints.knows(state, n, CARD_IRON) for n in ans)) or any(n in smiths_now(state) for n in ans)
        c2 = (CARD_ALPHA in tryable(state) and any(hints.knows(state, n, CARD_ALPHA) for n in ans)) or any(can_learn(state, n) for n in ans)
        return {"c1": bool(c1), "c2": bool(c2)}
    c1 = (ti.get("open") is not None and not ti.get("done")) or (iron_ready(state) and any(smith(state, p["name"]) for p in era2.adults(state)))
    c2 = (ta.get("open") is not None and not ta.get("done")) or (alpha_ready(state) and bool(readers(state)) and len(readers(state)) < len(era2.adults(state)))
    return {"c1": bool(c1), "c2": bool(c2)}


def count_paths(state):
    """集まりの答えを当てはめるとき (g7.apply_year から): この集まりのお題に道が出ていたら、その年 (この歩の季節の年) に 1 を足す"""
    g = _g(state)
    y = str((state["day"] + 1) // YEAR)
    row = g["path"].setdefault(y, {"meetings": 0, "c1": 0, "c2": 0})
    row["meetings"] += 1
    for k, v in paths(state).items():
        row[k] += int(v)


def path_consult(state, done_list):
    """年の終わり: まだ届いていない条件 1・2 の道が、G10 に入ってからのまる 2 年つづけて、お題に 0 回なら止めて相談 (仕組みのまちがい)。一度ずつ"""
    g, D = _g(state), state["day"]
    y = (D + 1) // YEAR - 1  # いま終わった年
    y0 = (g["start"] + 1) // YEAR  # G10 に入った日の次の歩の年 (まる 1 年目)
    for k in ("c1", "c2"):
        if k in g["c"]:
            continue
        ys = [y - i for i in range(PATH_YEARS)]
        if ys[-1] < y0:
            continue
        if all((g["path"].get(str(x)) or {}).get(k, 0) == 0 for x in ys):
            if not any(c["why"] == f"path_{k}" and c.get("year") == y for c in done_list):
                return {"why": f"path_{k}", "year": y, "day": D,
                        "text": f"G10 の条件 {k[1:]} ({CS[k]}) の道が {PATH_YEARS} 年つづけてお題に出なかった (仕組みのまちがいとして相談)"}
    return None


def indicators(state):
    """G10 の目安 (era2.indicators に足す。【シ】)"""
    g = _g(state)
    row = g["reap"].get(str(state["day"] // YEAR)) or {"all": 0, "bronze": 0, "iron": 0}
    r = g.get("region") or {}
    return {"g10_c1_day": g["c"].get("c1"), "g10_c2_day": g["c"].get("c2"), "g10_c3_day": g["c"].get("c3"),
            "g10_iron_made": len(g["made"]), "g10_iron_tools": len(iron_tools(state)), "g10_reap_all": row["all"], "g10_reap_iron": row["iron"],
            "g10_reap_bronze": row["bronze"], "g10_readers": len(readers(state)), "g10_outside_readers": len(outside_readers(state)),
            "g10_letters": g["letters"], "g10_region_maxD": r.get("maxD", 0), "g10_region_top": r.get("top"), "g10_region_members": r.get("members", 0)}


# ---------------- お題 ----------------

def facts(state):
    """お題の決まりの文 (G10 から。札が開いてから)。数 (進み・2.5 倍・600 人日) は書かない (G10_design.md 7. の 5)"""
    ti, ta = _tech(state, CARD_IRON), _tech(state, CARD_ALPHA)
    out = ""
    if ti.get("open") is not None or ti.get("done"):
        out += ("黒い金属: よその便りで聞いた「赤土からとる黒い金属」は、村で試せる (丘の赤い土と、土器を焼く強い火がある)。試すのが終わると、試した人は、"
                "主な仕事「黒い金属を作る」で黒い金属の鎌を作れる (何日も働くと 1 本できる。作り方を知る人と一緒に作った人も、次の季節から作れる)。"
                "黒い金属の鎌は、赤い金属の鎌と同じくらい刈れて、同じくらいすり減りにくい。村の道具として、赤い金属の道具と同じ「使う」か「しまう」(metal) で使う\n")
    if ta.get("open") is not None or ta.get("done"):
        out += ("音の字: よその便りで聞いた「音 1 つに字 1 つ」は、村で試せる (粘土の板がある)。試すのが終わると、試した人は字を読み書きできる。"
                "読み書きできない大人は、主な仕事「字を習う」で、読み書きできる人が村にいる日に少しずつ覚える (何十日か習うと読み書きできる)。"
                "読み書きできる大人のいる家は、貸し借り・約束・もめごとの量を、覚えでなく字で書いて比べられる (覚えちがいの言い争いにならない)\n")
    return out


def text(state, p):
    """お題の節「## 黒い金属と音の字」(G10 から。札が開いてから)"""
    g = _g(state)
    ti, ta = _tech(state, CARD_IRON), _tech(state, CARD_ALPHA)
    rows = []
    for card, t, name in ((CARD_IRON, ti, "赤土からとる黒い金属"), (CARD_ALPHA, ta, "音 1 つに字 1 つ")):
        if t.get("open") is None and not t.get("done"):
            continue
        who = sorted(q["name"] for q in era2.adults(state) if q["skills"].get(f"試す:{card}", 0) > 0)
        if t.get("done"):
            rows.append(f"- 「{name}」[{card}]: 村でできるようになった ({t['done']} 日目)")
        elif t.get("first") is not None:
            rows.append(f"- 「{name}」[{card}]: 試している ({t['first']} 日目から。試した人 {'・'.join(who[:8])}{' ほか' if len(who) > 8 else ''})。まだできていない")
        elif fixed(state):  # ① 2026-11-05: 知っている人の名前と、試し方
            kn = knowers(state, card)
            rows.append(f"- 「{name}」[{card}]: 試せる (まだだれも試していない)。試せるのは、この便りを知っている人 ({'・'.join(kn) or 'いない'}) と、"
                        f"その人と同じ季節に「試す」をして with にその人の名前を書く人 (job の try に \"{card}\")")
        else:
            rows.append(f"- 「{name}」[{card}]: 試せる (まだだれも試していない。試せるのは、この便りを知っている人と、その人と一緒に試す人)")
        if fixed(state) and t.get("first") is not None and not t.get("done"):
            kn = knowers(state, card)
            rows.append(f"  この便りを知っている人: {'・'.join(kn) or 'いない'} (知らない人は、知っている人と同じ季節に「試す」をして with にその人の名前を書けば一緒に試せる)")
    if g["made"] or iron_ready(state):
        it = iron_tools(state)
        gone = sum(1 for t in _g9(state)["tools"] if t.get("iron") and t["gone"] is not None)
        row = g["reap"].get(str(state["day"] // YEAR)) or {"iron": 0}
        sm = sorted(q["name"] for q in era2.adults(state) if smith(state, q["name"]))
        rows.append(f"- 黒い金属の鎌: 村で作ったのは {len(g['made'])} 本 (いま使えるのは {len(it)} 本" + (f"、すり減ったのは {gone} 本" if gone else "") + ")。"
                    f"この年に黒い金属の鎌で刈った日は のべ {row['iron']} 日。作れる人: {'・'.join(sm[:10])}{' ほか' if len(sm) > 10 else ''}")
        if fixed(state) and sm:  # ① 2026-11-05: 作り方を覚える道
            rows.append(f"  作り方を知らない人も、作れる人 ({'・'.join(sm[:10])}) と同じ季節に「{ACT_MAKE}」をして、with にその人の名前を書けば、"
                        "一緒に作って、次の季節から作れる")
    if g["readers"] or alpha_ready(state):
        rd = readers(state)
        ln = sorted(n for n in g["learn"] if n not in g["readers"] and any(q["name"] == n for q in era2.adults(state)))
        rows.append(f"- 字を読み書きできる人: {'・'.join(rd) or 'いない'}" + (f"。字を習っている人: {'・'.join(ln)}" if ln else "")
                    + (f"。字で書いて量を比べたのは {g['letters']} 回" if g["letters"] else ""))
    if not rows:
        return ""
    rows += _mine(state, p)
    return "\n## 黒い金属と音の字\n" + "\n".join(rows) + "\n"


def _mine(state, p):
    """① お題の人ごとの行 (G10_FIX_FROM から): あなたが知っている試せる札・あなたが作れること・あなたの家で知っている人と作れる人"""
    if not fixed(state) or not p:
        return []
    out, cs = [], hints.cards()
    for card in tryable(state):
        if hints.knows(state, p["name"], card):
            out.append(f"- あなた ({p['name']}) は、便り「{cs[card]['name']}」[{card}] を知っている。あなたは、主な仕事を「試す」にして、"
                       f"job の try に \"{card}\" と書けば試せる。知らない人も、あなたと同じ季節に「試す」をして with にあなたの名前を書けば、一緒に試せる")
    if p["name"] in smiths_now(state):
        out.append(f"- あなた ({p['name']}) は、黒い金属の作り方を知っている。あなたは、主な仕事を「{ACT_MAKE}」にできる。"
                   f"ほかの人も、あなたと同じ季節に「{ACT_MAKE}」をして with にあなたの名前を書けば、一緒に作って作り方を覚えられる")
    h = p.get("household")
    fam = [q["name"] for q in era2.adults(state) if h and q.get("household") == h and q is not p]
    for card in tryable(state):
        kn = [n for n in fam if hints.knows(state, n, card)]
        if kn:
            out.append(f"- あなたの家で、便り [{card}] を知っている人: {'・'.join(kn)} (家族の仕事 family で「試す」・try に \"{card}\" にできる)")
    sm = [n for n in fam if n in smiths_now(state)]
    if sm:
        out.append(f"- あなたの家で、黒い金属を作れる人: {'・'.join(sm)} (家族の仕事 family で「{ACT_MAKE}」にできる)")
    return out


def feel_note(state, p):
    """① 気持ちだけのお題の行 (G10_FIX_FROM から。代表でない人は仕事を決めないので、代表に伝えられることだけ)"""
    if not fixed(state):
        return ""
    cs, out = hints.cards(), []
    for card in tryable(state):
        if hints.knows(state, p["name"], card):
            out.append(f"- あなたは、便り「{cs[card]['name']}」[{card}] を知っている。家の代表が、あなたの仕事を「試す」(try に \"{card}\") にすれば、あなたは試せる")
    if p["name"] in smiths_now(state):
        out.append(f"- あなたは、黒い金属の作り方を知っている。家の代表が、あなたの仕事を「{ACT_MAKE}」にすれば、あなたは作れる")
    return ("\n" + "\n".join(out)) if out else ""


def field_rows(state):
    """答えの欄の説明 (g7._field_rows に足す)"""
    rows = []
    if iron_ready(state):
        rows.append(f'   黒い金属: 主な仕事を「{ACT_MAKE}」にできるのは、作り方を知る人と、その人と一緒に (with) 作る人')
    if alpha_ready(state):
        rows.append(f'   字: 読み書きできない大人は、主な仕事を「{ACT_LEARN}」にできる (読み書きできる人が村にいる日に習う)')
    return rows


def acts(state):
    """いま選べる G10 の仕事 (g7.acts に足す)"""
    out = []
    if iron_ready(state) and any(smith(state, p["name"]) for p in era2.adults(state)):
        out.append(ACT_MAKE)
    if alpha_ready(state) and readers(state) and len(readers(state)) < len(era2.adults(state)):
        out.append(ACT_LEARN)
    return out


def bad_words(s):
    """村の人に見せる文に、書かない言葉があれば並べる (試しで使う)"""
    return [w for w in WORDS if w in s]
