"""Society 4.0「分業と町」(2026-11-20。docs/society_phase/S4_design.md・S4_check.md)

- 印 state.era2.g7.s4 があるときだけ働く。印を書くのは step.py resume --s4 "<本人の言葉>" だけ
  (S3 のあと、25919 日目 (215年の終わり) から。S3 の相談・入口で止まっているときか、止まりがないとき。1 回だけ)。
  印がなければ、このファイルは読みこみもしない (g7・g15・s3・step.py は「s4」の鍵があるときだけ、関数の中で読みこむ)。
  だから前の歩は、お題・state・出来事・乱数が 1 バイトも変わらない
- 時代 (state.era) は G15 のまま。G15 と S3 の仕組み (作業場・燃える石・持ち場・見習い・交換) はそのまま動き、その上に 3 つの部分を足す:
  a 町の家: 家の大人を、1 年じゅう 1 つの町の仕事 (燃える石を掘る・水の作業場で働く) に出す (欄 town。やめると答えるまで続く)。
    その仕事の 1 人日ごとに、村の倉から草の種 10 つかみを家の倉に受ける (受け分。村の蓄えが 120 日分を切った季節はなし)。帳面に残す
  b 掘り場: 集まりで決めると (欄 pit)、村の倉の板 300 束を使い、掘る 80 人日で北の丘に板で支えた掘り場ができる。
    できたあとは掘る 1 人日で燃える石 500 kg (前は 200 kg。作るあいだは 100 kg)。掘る 20 人日ごとに板 1 束 (板がなければ 200 kg)
  c 川下の町の市: 板を草の種か燃える石に、燃える石を草の種に替える (欄 sell に「もらう」。値と今年の残りをお題に出す)
- 乱数は使わない。後押しはしない。印・本人の言葉・「作る側」のことは、村の人のお題にも出来事にも書かない
- 物差し (S4_design.md 4.): f1 食べ物でない仕事が大人の働いた日の 22% 以上・f2 新しい燃える石 (掘った・替えた) が火と力の半分以上・
  f3 町の家 (町の仕事 180 人日以上の家) が 5 つ以上・f4 交換で受けた物が草の種 3 万つかみ分以上・f5 暮らしを守る (ききんなし・蓄え 120 日分・人ははじめの 95%)。
  入口は f1 と f2 と (f3 か f4) が同じ 2 年つづき、その 2 年に f5 を割らない。止めて相談: f5 を割った年・道を選ぶ答える人が 2 年 0 人・5 年ごと
"""
import math

import era2
import g13
import g14
import g15
from world import log

YEAR, SEASON_DAYS = era2.YEAR, era2.SEASON_DAYS
S4_FROM = 25919  # 本物の村が S3 を終えて止めた日 (215年の終わり)。これより前には印を書けない
S4_DATE = "2026-11-20"
S4_NAME = "Society 4.0 (分業と町)"
# 2026-11-20 (s4-c): 人が読む所 (年報・設計の文) での呼び名。日本の枠組みでは Society 3.0 が工業・4.0 が情報の社会なので、これは「工業の続き」。
# S4_NAME は印の why (state) に入っているので変えない (前の歩の state を変えない)
S4_LABEL = "Society 3.0 フェーズ 2 (分業と町)"
PARTS = {"a": "町の家 (1 年じゅうの町の仕事と受け分)", "b": "掘り場 (板で支えた掘り場)", "c": "川下の町の市 (板と燃える石を草の種と燃える石に)"}
# a 町の家【仮定】
TOWN_SRC = "町の家の仕事"  # g7.src の値 (写しの記録では post に分ける)
JOBS = (g15.ACT_DIG, g15.ACT_WS_WORK)
TOWN_PER_HOUSE = 8  # 1 つの家から町の仕事に出せる大人
TOWN_MAX = 15  # 町の家の数の上限
RATION = 10  # 町の仕事の 1 人日ごとの受け分 (草の種のつかみ)
RATION_STOP = 120  # 村の蓄えがこの日数を切った季節は、受け分を出さない
EAT_DAY = 30  # 大人 1 人 1 日の食べ物 (草の種のつかみ。2,400 kcal ÷ 80)。帳面の「食べた」の見つもり
# b 掘り場【仮定】
PIT_PLANKS = 300
PIT_DAYS = 80
PIT_BUILD_KG = 100
PIT_KG = 500
PIT_WEAR = 20  # 掘る 20 人日ごとに板 1 束
# c 川下の町の市【仮定】((物, もらう物): (1 回の単位, もらう数), 1 年に町が受ける物の数)
TOWN = "町"
TOWN_NAME = "川下の町"
PRICE = {("板", "草の種"): (1, 30), ("板", "燃える石"): (1, 50), ("燃える石", "草の種"): (100, 30)}
CAP = {("板", "草の種"): 3000, ("板", "燃える石"): 1500, ("燃える石", "草の種"): 40000}
VALUE = {"草の種": 1.0, "燃える石": 0.3, "ヤギ": 300.0}  # 交換で受けた物のねうち (草の種のつかみ)
SELL_MAX = 6
# 物差し【仮定】(S4_design.md 4.)
NONFOOD = tuple(g14.NONFOOD) + tuple(g15.ACTS15)
F1_SHARE = 0.22
F2_SHARE = 0.5
# 2026-11-20 (220年の終わりの相談): 火と力の合わせに食べ物の熱と水の輪が入るので、新しい燃える石の分は 51% ほどが天井。
# 同じ測り方のまま、221年から線を 45% にする (S4_check.md 7.)。それより前の年は 50% のまま
F2_SHARE2, F2_FROM = 0.45, 221
F3_HOUSES, F3_DAYS = 5, 180
F4_VALUE = 30000
F5_STORE, F5_POP = 120, 0.95
F_YEARS = 2
PATH_YEARS = 2
LATER_YEARS = 5
FR = {"F1": "はじめて掘り場を作ると決めた", "F2": "はじめての掘り場", "F3": "はじめて川下の町の市で替えた", "F4": "はじめての町の家"}
FS = {"f1": "食べ物でない仕事", "f2": "新しい燃える石", "f3": "町の家", "f4": "交換", "f5": "暮らしを守る"}
HIDE = ("後押し", "反実仮想", "作る側", "Society", "S3", "S4", "案 A", "本人", "分業")
# 2026-11-20 (ブランチ s4-b): 町の家を選ばないわけを調べた直し (S4_check.md 7.)。FIX_DAY より後の日 (221年から) か、
# resume --s4fix の印 (g7.s4.fix。26519 日目の相談のお題から) があるときだけ。前の歩は 1 バイトも変わらない。
# 中身は事実だけ (後押しはしない): 1 年の畑の草取りが要る分の何倍か・水の道の手入れの決まり・板の出入り・町の市の値での町の仕事の返り・
# 年の終わりに数える「町の家」との区別・持ち場の人と止まっている作業場の書き方・はねた town の答えを「できなかったこと」に
FIX_DAY = 26519


def fixed(state):
    return state["day"] > FIX_DAY or bool(_g(state).get("fix"))


# 2026-11-20 (ブランチ s4-c): 年の集まりで、家ごとに町の家を聞く (S4_check.md 8.)。お題の終わり近くの町の行は読まれていなかったので、
# 年の集まりのお題の上のほう (その人のようすのすぐあと) に、短い 1 節で聞く。事実だけで、すすめない。答えは今までの欄 town (と sell の相手「町」)。
# ASK_DAY より後の日か、resume --s4ask の印 (g7.s4.ask。26639 日目の相談のお題から) があるときだけ、はじまりの年の集まりから ASK_YEARS 回。
# 前の歩は 1 バイトも変わらない。聞いている年は「選ぶ人 2 年 0 人」の相談で止めず、終わりの年の終わりに止めて相談する
ASK_DAY = 26639  # 221年の終わり
ASK_YEARS = 3
ASK_HEAD = "## 今年の集まりで、家ごとに聞くこと (町の家)"
ASK_NO = ("出さない", "出さず", "いない", "なし", "false", "no")


def ask_start(state):
    a = _g(state).get("ask")
    return a["day"] if a else ASK_DAY + YEAR


def ask_window(state):
    """聞く年のあいだ (はじまりの年の集まりの日から ASK_YEARS 年)"""
    D, s = state["day"], ask_start(state)
    return (bool(_g(state).get("ask")) or D > ASK_DAY) and s <= D < s + ASK_YEARS * YEAR


def ask_on(state):
    """この歩が、聞く年の年の集まりか"""
    return on(state) and state["era2"]["g7"].get("ask") == "年" and ask_window(state)


def _running_ws(state):
    return [m for m in g15.workshops(state, done=True) if not (g15._mill(state, m) or {}).get("stopped")]


def ask_block(state, p):
    """年の集まりのお題の、その人のようすのすぐあとの短い節 (聞く年だけ。ほかは空)"""
    if not ask_on(state):
        return ""
    g, g15g = _g(state), g15._g(state)
    name, h = p["name"], p.get("household")
    if not h:
        return ""
    n_ad = len([q for q in era2.adults(state) if q.get("household") == h])
    run = _running_ws(state)
    post = _s3()._g(state)["posts"].get(name)
    jobs = ([f"「{g15.ACT_DIG}」"] if g15.coal_on(state) else []) + ([f"「{g15.ACT_WS_WORK}」(いま回っている作業場 {'・'.join(run)})"] if run else [])
    if not jobs:
        return ""
    kg = PIT_KG if (g.get("pit") or {}).get("done") is not None else g15.COAL_KG_DAY
    crew, r3 = _s3().CREW[0][0], _s3().CREW[0][2]
    val = (f"掘る 1 人日 (燃える石 {kg} kg) = 草の種 {round(kg * PRICE[('燃える石', '草の種')][1] / 100)} つかみ・"
           f"{crew} 人そろった水ののこの 1 人日 (板 {r3} 束) = 草の種 {r3 * PRICE[('板', '草の種')][1]} つかみ")
    now = []
    w = weed_times(state)
    if w and w[0] > 0:
        now.append(f"畑の草取りは要る時間の 約 {round(w[1], 1)} 倍 (要る分をこえても実りは増えない)")
    cap = ((state["era2"]["g7"].get("g13") or {}).get("canal") or {}).get("cap", 0)
    if cap:
        per = round(g13.CANAL_PER_DAY / g13.CANAL_KEEP)
        now.append(f"水の道の手入れに要るのは 1 年 約 {round(cap / per)} 人日 (水の来る畑 {per} つかみ分ごとに 1 人日。掘るほどふえる)")
    now.append(f"村の倉の燃える石 {round(g15g['coal']['stock'])} kg・板 {g15g['planks']['stock']} 束")
    if post and post["mill"] in run:
        ex = f"{{\"人\": [\"{name}\"], \"仕事\": \"{g15.ACT_WS_WORK}\", \"輪\": \"{post['mill']}\"}}"
    elif g15.coal_on(state):
        ex = f"{{\"人\": [\"{name}\"], \"仕事\": \"{g15.ACT_DIG}\"}}"
    else:
        ex = f"{{\"人\": [\"{name}\"], \"仕事\": \"{g15.ACT_WS_WORK}\", \"輪\": \"{run[0]}\"}}"
    mine = g["town"].get(h)
    cur = (f"あなたの家はいま町の家 ({'・'.join(mine['people'])} が「{mine['job']}」)。やめるなら \"town\": {{\"やめる\": true}}。" if mine else "")
    return (f"\n{ASK_HEAD}\n"
            f"あなたの家 ({h}。大人 {n_ad} 人) から、大人を町の家の仕事に出すか。出しても出さなくてもよい。\n"
            f"- 町の家の仕事: {' か '.join(jobs)}。出した人は 1 年じゅうその仕事をし、畑・ヤギ・水の道には出ない。"
            f"その 1 人日ごとに、村の倉から草の種 {RATION} つかみが家の倉に入る。食べ物は今までどおり村の倉から\n"
            f"- {TOWN_NAME}の市の値で: {val} (町が受ける量まで)\n"
            f"- いま: {'・'.join(now)}\n"
            f"- 答え: 出すなら \"town\": {ex} (あなたの家の大人だけ。{TOWN_PER_HOUSE} 人まで。持ち場の人は、その作業場の「{g15.ACT_WS_WORK}」だけ)。"
            f"出さないなら \"town\": \"出さない\"。{cur}村の倉の板・燃える石を町と替えるなら \"sell\" (相手 \"{TOWN}\")\n")


def _ask_no(v):
    return v is False or (isinstance(v, str) and any(w in v.strip().lower() for w in ASK_NO))


def ask_count(state, real, made, failed):
    """聞く年の年の集まりの答え: 出した・出さないと答えた・書かなかった (帳面 g7.s4.asked。お題には出さない)"""
    D = state["day"]
    y = str((D + 1) // YEAR)
    yes = sorted(made)
    no = sorted(n for n, a in real.items() if isinstance(a, dict) and _ask_no(a.get("town")))
    fail = sorted(failed)
    quiet = len([n for n in real if n not in set(yes) | set(no) | set(fail)])
    _g(state).setdefault("asked", {})[y] = {"day": D, "answerers": len(real), "yes": yes, "no": no, "failed": fail, "quiet": quiet,
                                           "town": len(_g(state)["town"]), "town_people": sum(len(r["people"]) for r in _g(state)["town"].values())}


def on(state):
    return "day" in (((state.get("era2") or {}).get("g7") or {}).get("s4") or {})


def _g(state):
    return state["era2"]["g7"]["s4"]


def _y(state):
    return state["day"] // YEAR


def _yd(day):
    return f"{day // YEAR}年{day % YEAR + 1}日目"


def _s3():
    import s3
    return s3


def _adult(state, name):
    return next((p for p in era2.adults(state) if p["name"] == name), None)


def _house_of(state, name):
    p = _adult(state, name)
    return p.get("household") if p else None


# ---------------- 印 (step.py resume --s4) ----------------

def why_text(words):
    return f"{S4_NAME} (本人の言葉 {S4_DATE} 「{words}」)"


def refusal(state, words):
    """resume --s4 ができないわけ (できるなら None)"""
    if not (words or "").strip():
        return "--s4 には本人の言葉が要る"
    g7s = ((state.get("era2") or {}).get("g7") or {})
    if "s3" not in g7s or not _s3().on(state):
        return "Society 3.0 の印がないので、Society 4.0 は始められない"
    if "s4" in g7s:
        return "Society 4.0 はもう始めてある"
    if state["day"] < S4_FROM:
        return f"Society 4.0 は {S4_FROM} 日目 (215年の終わり) からだけ"
    h = g7s.get("hold") or {}
    if state.get("hold") or h:
        if not (h.get("why") in ("consult", "entrance") and str(h.get("what", "")).startswith("S3:")):
            return "Society 4.0 は、S3 の相談・入口で止まっているときか、止まりのないときだけ始める"
    if g15.push_on(state):
        return "後押しが動いている"
    return None


def mark(state, words):
    """resume --s4 から: 印 g7.s4 を書く (村の出来事には残さない)"""
    words = words.strip()
    D = state["day"]
    s3g = _s3()._g(state)
    g = state["era2"]["g7"]["s4"] = {
        "day": D, "words": words, "why": why_text(words), "parts": list(PARTS), "start_year": D // YEAR + 1,
        "pop0": len([p for p in state["people"] if p["alive"]]),
        "old": {"v": round(g15._g(state)["coal"]["stock"], 2), "h": round(sum(s3g["hcoal"].values()), 2)},
        "town": {}, "quit": [], "pit": None, "sold": {}, "sales": [], "bought": {}, "led": {}, "mk": {},
        "chose": {}, "rows": {}, "f": {}, "f_years": {k: [] for k in ("f1", "f2", "f3", "f4")}, "f5_broken": [], "store_min": {}, "reached": {}}
    return g


def _reach(state, f, why):
    g = _g(state)
    if f not in g["reached"]:
        g["reached"][f] = {"day": state["day"], "why": why}


# ---------------- a 町の家 ----------------

def town_why(state, h, names, job, mid):
    """町の家の仕事につけないわけ (つけるなら None)。names: その家の大人"""
    g, s3g = _g(state), _s3()._g(state)
    if job not in JOBS:
        return f"町の仕事は {'・'.join(JOBS)} だけ"
    if job == g15.ACT_DIG and not g15.coal_on(state):
        return "燃える石のある所を知らない"
    if job == g15.ACT_WS_WORK and mid not in g15.workshops(state, done=True):
        return f"{mid} は使える作業場でない"
    if job == g15.ACT_WS_WORK and ask_on(state) and mid not in _running_ws(state):  # 聞く年 (s4-c): 回っている作業場だけ
        return f"{mid} はいま止まっている"
    if not names:
        return "人がいない"
    if len(names) > TOWN_PER_HOUSE:
        return f"1 つの家から {TOWN_PER_HOUSE} 人まで"
    for n in names:
        if _house_of(state, n) != h:
            return f"{n} は{h}の大人でない"
        r = s3g["posts"].get(n)
        if r and not (job == g15.ACT_WS_WORK and r["mill"] == mid):
            return f"{n} は {r['mill']} の{r['post']}"
    if h not in g["town"] and len(g["town"]) >= TOWN_MAX:
        return f"町の家はもう {TOWN_MAX}"
    return None


def _town_rows(v):
    if not isinstance(v, dict):
        return None
    ns = v.get("人") or v.get("people") or []
    if isinstance(ns, str):
        ns = [ns]
    ns = [str(x).strip() for x in ns if str(x).strip()] if isinstance(ns, list) else []
    job = str(v.get("仕事") or v.get("job") or "").strip()
    mid = str(v.get("輪") or v.get("mill") or "").strip().upper() or None
    q = v.get("やめる")
    q = q is True or str(q).strip().lower() in ("true", "はい", "やめる", "1")
    return ns, job, mid, q


def quit_town(state, h, names, why):
    g = _g(state)
    r = g["town"].get(h)
    if not r:
        return
    gone = [n for n in r["people"] if not names or n in names]
    r["people"] = [n for n in r["people"] if n not in gone]
    if not r["people"]:
        g["town"].pop(h)
    g["quit"] = (g["quit"] + [{"house": h, "people": gone, "day": state["day"], "why": why}])[-40:]
    if why != "亡くなった・村を出た" and gone:
        log(state, "町の家", gone[0], f"{h}の {'・'.join(gone)} が、町の家の仕事 ({r['job']}) をやめた ({why})", household=h, quit=True)


def _prune(state):
    g = _g(state)
    alive = {p["name"]: p.get("household") for p in era2.adults(state)}
    for h in sorted(g["town"]):
        r = g["town"][h]
        gone = [n for n in r["people"] if alive.get(n) != h]
        if gone:
            quit_town(state, h, gone, "亡くなった・村を出た")


def season_start(state):
    """季節のはじめ (g7._apply の終わり。S3 の持ち場のあと): 町の家の大人は、町の仕事をする (作業場の輪が止まっていれば直す)。
    集まり直し (ききん) の季節は、その季節の答えのまま"""
    g = _g(state)
    _prune(state)
    if state["era2"]["g7"].get("ask") == "集まり直し":
        return
    src = state["era2"]["g7"].setdefault("src", {})
    for h in sorted(g["town"]):
        r = g["town"][h]
        for n in r["people"]:
            p = _adult(state, n)
            if p is None:
                continue
            if r["job"] == g15.ACT_DIG:
                p["plan"] = {"activity": g15.ACT_DIG, "place": g15.COAL_PLACE, "with": []}
                g15._g(state)["dest"].pop(n, None)
            else:
                m = g15._mill(state, r["mill"])
                if m is not None and m.get("stopped") and g13.can_do(state, g13.ACT_MILL_FIX):
                    p["plan"] = {"activity": g13.ACT_MILL_FIX, "place": "camp", "with": []}
                    g15._g(state)["dest"].pop(n, None)
                else:
                    p["plan"] = {"activity": g15.ACT_WS_WORK, "place": "camp", "with": []}
                    g15._g(state)["dest"][n] = r["mill"]
            src[n] = TOWN_SRC


def _led(state, y, h):
    return _g(state)["led"].setdefault(str(y), {}).setdefault(h, {"days": 0, "pay": 0, "unpaid": 0, "ate": 0, "coal": 0.0, "ws": 0, "planks": 0.0, "people": 0})


def _ration(state):
    """季節の終わり: 町の家の、この季節の町の仕事の人日 (g7.past のいちばん新しい季節) と受け分 (村の倉 → 家の倉)。作業場の板の見つもり"""
    g, D = _g(state), state["day"]
    y = D // YEAR
    past = (state["era2"]["g7"].get("past") or [None])[-1]
    if not past or past.get("day") != D:
        return
    days = past["days"]
    pk = g15._g(state)["planks"]
    made = pk["made"].get(str(y), 0)
    mk = g["mk"]
    delta = made - (mk.get("made", 0) if mk.get("y") == y else 0)
    g["mk"] = {"y": y, "made": made}
    ws_all = sum(a.get(g15.ACT_WS_WORK, 0) for a in days.values())
    per = delta / ws_all if ws_all else 0.0
    ok = era2.store_days(state) >= RATION_STOP
    total = 0
    for h in sorted(g["town"]):
        r = g["town"][h]
        acts = (r["job"], g13.ACT_MILL_FIX) if r["job"] == g15.ACT_WS_WORK else (r["job"],)
        n = sum((days.get(x) or {}).get(a, 0) for x in r["people"] for a in acts)
        ws = sum((days.get(x) or {}).get(g15.ACT_WS_WORK, 0) for x in r["people"])
        row = _led(state, y, h)
        row["days"] += n
        row["ws"] += ws
        row["planks"] = round(row["planks"] + ws * per, 1)
        row["ate"] += len(r["people"]) * SEASON_DAYS * EAT_DAY
        row["people"] = max(row["people"], len(r["people"]))
        pay = n * RATION
        if not pay:
            continue
        if ok:
            got = era2._g6_take(state, "村", {"草の種": pay}).get("草の種", 0)
            if got:
                era2._g6_put(state, h, {"草の種": got})
            row["pay"] += got
            row["unpaid"] += pay - got
            total += got
        else:
            row["unpaid"] += pay
    if total:
        log(state, "受け分", None, f"町の家 {len(g['town'])} 家が、町の仕事の受け分として、村の倉から草の種 {total} つかみを家の倉に受けた", paid=total)


# ---------------- b 掘り場 ----------------

def dig_kg_now(state):
    """いま掘る 1 人日の燃える石 (kg): 掘り場ができて板があれば 500・作っているあいだは 100・なければ 200"""
    pit = _g(state).get("pit")
    if not pit:
        return g15.COAL_KG_DAY
    if pit.get("done") is None:
        return PIT_BUILD_KG
    return PIT_KG if pit["wear"] < 1 or g15._g(state)["planks"]["stock"] >= 1 else g15.COAL_KG_DAY


def dig_day(state, p, t):
    """g15._dig のかわり (印のあと): 掘り場の決まりで掘る。2 割は掘った人の家の倉 (S3 の a)"""
    g, g15g, D = _g(state), g15._g(state), state["day"]
    name, h = p["name"], p.get("household")
    y = str(_y(state))
    pit = g.get("pit")
    kg, note = g15.COAL_KG_DAY, ""
    if pit and pit.get("done") is None:
        kg = PIT_BUILD_KG
        pit["work"] += 1
        pit["by"][name] = pit["by"].get(name, 0) + 1
        note = f"掘り場を板で支えながら (あと 約 {max(0, PIT_DAYS - pit['work'])} 人日)"
        if pit["work"] >= PIT_DAYS:
            pit["done"] = D
            b = sorted(pit["by"], key=lambda k: (-pit["by"][k], k))
            log(state, "掘り場", None, f"北の丘の掘り場ができた (作ったのは {'・'.join(b[:6])}{' ほか' if len(b) > 6 else ''})。掘る 1 人日で燃える石 約 {PIT_KG} kg")
            _reach(state, "F2", "掘り場ができた")
    elif pit:
        if pit["wear"] >= 1 and g15g["planks"]["stock"] >= 1:
            g15g["planks"]["stock"] -= 1
            g15g["planks"]["used"][y] = g15g["planks"]["used"].get(y, 0) + 1
            pit["wear"] = round(pit["wear"] - 1, 3)
            pit["planks_used"][y] = pit["planks_used"].get(y, 0) + 1
        if pit["wear"] < 1:
            kg = PIT_KG
            pit["wear"] = round(pit["wear"] + 1 / PIT_WEAR, 3)
            note = "掘り場で"
        else:
            note = "掘り場を支える板がないので、浅い所で"
    s3 = _s3()
    vk = s3.dig(state, p, kg)
    c = g15g["coal"]
    c["stock"] = round(c["stock"] + vk, 1)
    c["dug"][y] = c["dug"].get(y, 0) + kg
    c["by"][name] = c["by"].get(name, 0) + 1
    if h and h in g["town"] and name in g["town"][h]["people"]:
        row = _led(state, _y(state), h)
        row["coal"] = round(row["coal"] + kg, 1)
    t.setdefault("events", []).append(log(state, g15.ACT_DIG, name, f"{name} が、北の丘で{note}燃える石を {kg} kg 掘って、{round(vk)} kg を村の倉に"
                                          + (f"、{round(kg - vk)} kg を家の倉に" if kg - vk >= 1 else "") + f"運んだ (村の倉の燃える石 {round(c['stock'])} kg)", coal=kg))


def _pit_vote(state, real):
    import g7
    g = _g(state)
    if g.get("pit") or not g15.coal_on(state):
        return
    votes = {n: "作る" if a.get("pit") is True or str(a.get("pit")).strip().lower() in ("true", "作る", "はい") else "作らない"
             for n, a in sorted(real.items()) if isinstance(a, dict) and a.get("pit") is not None}
    if not votes:
        return
    ch, txt = g7._tally(state, votes, g7._vote_weights(state, real))
    if ch != "作る":
        return
    pk = g15._g(state)["planks"]
    if pk["stock"] < PIT_PLANKS:
        log(state, "掘り場", None, f"集まりで、北の丘に掘り場を作ると決めたが、村の倉の板が {PIT_PLANKS} 束に足りないので、まだ作れない (票 {txt})")
        return
    pk["stock"] -= PIT_PLANKS
    y = str(_y(state))
    pk["used"][y] = pk["used"].get(y, 0) + PIT_PLANKS
    g["pit"] = {"day": state["day"], "votes": txt, "work": 0, "done": None, "by": {}, "wear": 0.0, "planks_used": {y: PIT_PLANKS}}
    log(state, "掘り場", None, f"集まりで、北の丘に板で支えた掘り場を作ると決めた。村の倉の板 {PIT_PLANKS} 束を使う。掘る {PIT_DAYS} 人日でできる (票 {txt})")
    _reach(state, "F1", "掘り場を作ると決めた")


# ---------------- c 川下の町の市 ----------------

def _sell_rows(v):
    if isinstance(v, dict):
        v = [v]
    if not isinstance(v, list):
        return []
    out = []
    for r in v[:SELL_MAX]:
        if not isinstance(r, dict):
            continue
        what = str(r.get("物") or r.get("what") or "").strip()
        to = str(r.get("相手") or r.get("to") or "").strip()
        side = str(r.get("から") or r.get("from") or "家").strip()
        get = str(r.get("もらう") or r.get("get") or "草の種").strip()
        try:
            n = int(float(r.get("数") or r.get("n") or 0))
        except (TypeError, ValueError):
            n = 0
        if what in ("板", "燃える石") and to and n > 0:
            out.append((what, n, to.upper() if to.upper().startswith("N") else to, "村" if side == "村" else "家", get))
    return out


def _is_town(to):
    return to in (TOWN, TOWN_NAME)


def left(state, key):
    y = str((state["day"] + 1) // YEAR)
    return max(0, CAP[key] - ((_g(state)["sold"].get(y) or {}).get("→".join(key), 0)))


def sell_town(state, who, side, what, n, get):
    """川下の町との 1 つの交換 (乱数なし)。side は「村」か家の名前。戻り値: (もらった物, できないわけ)"""
    g, g15g, s3g = _g(state), g15._g(state), _s3()._g(state)
    key = (what, get)
    if key not in PRICE:
        return None, f"町は{what}を{get}には替えない"
    unit, rate = PRICE[key]
    n = min(n, _s3()._have(state, side, what), left(state, key))
    k = n // unit
    if k <= 0:
        return None, f"{TOWN_NAME}と{what}を替えられなかった (物が足りないか、町が今年はもう要らない)"
    q, got = k * unit, k * rate
    if side == "村":
        if what == "板":
            g15g["planks"]["stock"] -= q
        else:
            g15g["coal"]["stock"] = round(g15g["coal"]["stock"] - q, 2)
    else:
        kk = "hplanks" if what == "板" else "hcoal"
        s3g[kk][side] = round(s3g[kk].get(side, 0) - q, 2)
    if get == "草の種":
        era2._g6_put(state, side, {"草の種": got})
    elif side == "村":
        g15g["coal"]["stock"] = round(g15g["coal"]["stock"] + got, 2)
    else:
        s3g["hcoal"][side] = round(s3g["hcoal"].get(side, 0) + got, 2)
    y = str((state["day"] + 1) // YEAR)
    row = g["sold"].setdefault(y, {})
    row["→".join(key)] = row.get("→".join(key), 0) + q
    row["got_" + get] = row.get("got_" + get, 0) + got
    if get == "燃える石":
        g["bought"][y] = g["bought"].get(y, 0) + got
    g["sales"] = (g["sales"] + [{"day": state["day"], "who": who, "side": side, "what": what, "n": q, "get": get, "got": got}])[-60:]
    uw = "束" if what == "板" else "kg"
    gw = f"{get} {got} {'つかみ' if get == '草の種' else 'kg'}"
    log(state, "交換", who, f"{who} が、{'村' if side == '村' else side}の{what} {q} {uw}を {TOWN_NAME} に渡して、{gw} を受けた", to=TOWN, what=what, n=q, got={get: got})
    _reach(state, "F3", f"{what} {q} {uw}を {TOWN_NAME} で{get}に替えた")
    return {get: got}, None


def apply_sell(state, real, hs):
    """s3.apply_answers の d のかわり (印のあと): 近い集落とは S3 のまま、川下の町とは市の値で。村の倉の物は、物・相手・もらう物ごとに、答えた人の中でいちばん多い中身"""
    import g7
    s3 = _s3()
    vill = {}
    for name, a in sorted(real.items()):
        if not isinstance(a, dict):
            continue
        for what, n, to, side, get in _sell_rows(a.get("sell")):
            if side == "村":
                vill.setdefault((what, TOWN if _is_town(to) else to, get), {})[name] = n
            elif hs.get(name):
                if _is_town(to):
                    sell_town(state, name, hs[name], what, n, get)
                else:
                    s3.sell(state, name, hs[name], what, n, to)
    for (what, to, get), vs in sorted(vill.items()):
        ch, _ = g7._tally(state, {k: str(v) for k, v in vs.items()}, g7._vote_weights(state, real))
        if not ch:
            continue
        who = sorted(k for k, v in vs.items() if str(v) == ch)[0]
        if _is_town(to):
            sell_town(state, who, "村", what, int(ch), get)
        else:
            s3.sell(state, who, "村", what, int(ch), to)


# ---------------- 集まりの答え (g7.apply_year から。S3 の post・head・sell のあと) ----------------

def count_chose(state, real):
    """答える人のうち、town・pit・sell を書いた人と、自分か家の大人が町の家の仕事をしている人 (道の見張り)"""
    g = _g(state)
    y = str((state["day"] + 1) // YEAR)
    row = g["chose"].setdefault(y, {"meetings": 0, "answerers": 0, "chose": 0, "wrote": 0, "who": []})
    row["meetings"] += 1
    row["answerers"] = max(row["answerers"], len(real))
    n = w = 0
    for name, a in sorted(real.items()):
        if not isinstance(a, dict):
            continue
        wrote = isinstance(a.get("town"), dict) or a.get("pit") is True or bool(_sell_rows(a.get("sell")))
        w += wrote
        h = _house_of(state, name)
        if wrote or (h and h in g["town"]):
            n += 1
            if name not in row["who"]:
                row["who"] = (row["who"] + [name])[:30]
    row["chose"] = max(row["chose"], n)
    row["wrote"] = max(row["wrote"], w)


def apply_answers(state, real):
    """集まりの答え: town (町の家。自分の家)・pit (掘り場。答えた人の中でいちばん多い中身)。sell は s3.apply_answers から apply_sell"""
    g = _g(state)
    _prune(state)
    count_chose(state, real)
    asking = ask_on(state)
    made, failed = [], []
    for name, a in sorted(real.items()):
        if not isinstance(a, dict):
            continue
        tr = _town_rows(a.get("town"))
        h = _house_of(state, name)
        if asking and not tr and a.get("town") is not None and not _ask_no(a.get("town")):  # 聞く年 (s4-c): 読めない town も「できなかったこと」に
            failed.append(name)
            g15._fail(state, name, "町の家", f"{name} の答えの町の家は、書き方が分からず、できなかった (書き方 {{\"人\": [名前], \"仕事\": 仕事}})")
            continue
        if not tr or not h:
            continue
        ns, job, mid, q = tr
        if q:
            quit_town(state, h, ns, f"{name} の答え")
            continue
        if job == g15.ACT_WS_WORK and not mid:
            mid = next(iter(g15.workshops(state, done=True)), None)
        ns = sorted(dict.fromkeys(ns))
        why = town_why(state, h, ns, job, mid)
        if why is not None:
            if fixed(state):  # 直し (s4-b): はねた答えを「水の作業場と燃える石で、できなかったこと」に出す (前は黙ってはねた)
                g15._fail(state, name, "町の家", f"{name} の答えの町の家 ({'・'.join(ns) or '人なし'}・{job or '仕事なし'}) は、できなかった ({why})")
            failed.append(name)
            continue
        made.append(name)
        old = g["town"].get(h)
        g["town"][h] = {"job": job, "mill": mid if job == g15.ACT_WS_WORK else None, "people": ns, "day": state["day"], "by": name}
        if old and old["job"] == job and old["people"] == ns and old.get("mill") == g["town"][h]["mill"]:
            g["town"][h]["day"] = old["day"]
            continue
        where = f" ({mid})" if job == g15.ACT_WS_WORK else ""
        log(state, "町の家", name, f"{h}の {'・'.join(ns)} が、町の家の仕事として、1 年じゅう「{job}」{where}をすることにした (やめると答えるまで。"
            f"受け分は 1 人日 草の種 {RATION} つかみ)", household=h, job=job, people=ns)
        _reach(state, "F4", f"{h}が町の家になった")
    if asking:
        ask_count(state, real, made, failed)
    _pit_vote(state, real)
    if not _s3().part(state, "d"):  # S3 の d (交換) がない村では、川下の町の市だけここで
        apply_sell(state, {n: {"sell": [r for r in (a.get("sell") or []) if isinstance(r, dict) and _is_town(str(r.get("相手") or r.get("to") or ""))]}
                           for n, a in real.items() if isinstance(a, dict) and isinstance(a.get("sell"), list)},
                   {p["name"]: p.get("household") for p in era2.adults(state)})


# ---------------- 季節の終わり・年の終わり: 帳面と物差し ----------------

def season_end(state):
    """季節の終わり (g7.season_end。S3 の季節の終わりのあと): 受け分 → 蓄えのいちばん少ない日数 → 年の終わりなら行と物差し"""
    D = state["day"]
    if (D + 1) % SEASON_DAYS:
        return
    _prune(state)
    _ration(state)
    g = _g(state)
    y = str(D // YEAR)
    sd = era2.store_days(state)
    g["store_min"][y] = min(g["store_min"].get(y, sd), sd)
    if (D + 1) % YEAR == 0:
        year_end(state)


def work_days(state):
    """前の 1 年 (g7.past) の大人の働いた日と、食べ物でない仕事の日 (休んだ日は数えない)"""
    w = nf = 0
    for s in state["era2"]["g7"].get("past", []):
        for acts in s["days"].values():
            for a, d in acts.items():
                if a in g14.REST:
                    continue
                w += d
                if a in NONFOOD:
                    nf += d
    return w, nf


def food_rate(state, y):
    """y 年の刈り入れを、前の 1 年の畑仕事と水の道を掘る人日で割ったもの (お題のくらべ。見つもり)"""
    pd = 0
    for s in state["era2"]["g7"].get("past", []):
        for acts in s["days"].values():
            pd += acts.get("畑仕事", 0) + acts.get(g13.ACT_CANAL, 0)
    hv = __import__("g7").harvest_year(state, y * YEAR)
    return round(hv / pd) if pd else 0


def trade_value(state, y):
    """y 年に交換で受けた物のねうち (草の種のつかみ): 川下の町 (印のあと) と近い集落 (S3 の交換)"""
    s = (_g(state)["sold"].get(str(y)) or {})
    v = sum(VALUE[k[4:]] * n for k, n in s.items() if k.startswith("got_") and k[4:] in VALUE)
    for pid, r in ((_s3()._g(state)["sold"].get(str(y)) or {}).items()):
        if pid == _s3().TOWN:
            continue
        v += sum(VALUE[k[4:]] * n for k, n in r.items() if k.startswith("got_") and k[4:] in VALUE)
    return round(v)


def row_of(state, y):
    g, g15g, s3g = _g(state), g15._g(state), _s3()._g(state)
    ys = str(y)
    lr = next((r for r in g15g["ledger"] if r["year"] == y), None) or {}
    en = lr.get("energy") or {}
    w, nf = work_days(state)
    f1 = round(nf / w, 4) if w else 0.0
    burned = lr.get("coal_burned", 0)
    hk = ((s3g["fire"].get(ys) or {}).get("house_kg", 0))
    old = g.setdefault("old_left", dict(g["old"]))
    used_h = min(old["h"], hk)
    used_v = min(old["v"], max(0.0, burned - hk))
    own = round((burned - used_h - used_v) / burned, 4) if burned else 0.0
    f2 = round(en.get("coal_share", 0.0) * own, 4)
    led = g["led"].get(ys) or {}
    town_ok = sorted(h for h, r in led.items() if r["days"] >= F3_DAYS)
    tv = trade_value(state, y)
    ev = [e for e in state["events"] if e["day"] // YEAR == y]
    famine = sum(1 for e in ev if e["type"] == "蓄えが尽きる")
    pop = len([p for p in state["people"] if p["alive"]])
    smin = g["store_min"].get(ys, era2.store_days(state))
    ch = g["chose"].get(ys) or {}
    pit = g.get("pit") or {}
    sold = g["sold"].get(ys) or {}
    return {"year": y, "worked": w, "nonfood": nf, "f1_share": f1, "coal_share": en.get("coal_share", 0.0), "coal_burned": round(burned),
            "old_used": round(used_h + used_v), "own_share": own, "f2_share": f2, "coal_dug": lr.get("coal_dug", 0), "coal_bought": round(g["bought"].get(ys, 0)),
            "coal_stock": round(g15g["coal"]["stock"]), "house_coal": round(sum(s3g["hcoal"].values())), "stoves": len(lr.get("stoves") or []),
            "fire_pd": round(((s3g["fire"].get(ys) or {}).get("hours", 0)) / _s3().PD_H),
            "town": len(g["town"]), "town_people": sum(len(r["people"]) for r in g["town"].values()), "town_ok": len(town_ok),
            "town_days": sum(r["days"] for r in led.values()), "town_pay": sum(r["pay"] for r in led.values()), "town_unpaid": sum(r["unpaid"] for r in led.values()),
            "town_ate": sum(r["ate"] for r in led.values()), "town_coal": round(sum(r["coal"] for r in led.values())), "town_planks": round(sum(r["planks"] for r in led.values())),
            "pit": "ある" if pit.get("done") is not None else ("作っている" if pit else "ない"), "pit_planks": (pit.get("planks_used") or {}).get(ys, 0),
            "sold": dict(sold), "trade_value": tv, "planks": g15g["planks"]["stock"], "planks_made": g15g["planks"]["made"].get(ys, 0),
            "answerers": ch.get("answerers", 0), "chose": ch.get("chose", 0), "wrote": ch.get("wrote", 0),
            "store_min": smin, "store_end": era2.store_days(state), "famine": famine, "pop": pop, "pop0": g["pop0"], "harvest": lr.get("harvest", 0),
            "f1_like": f1 >= F1_SHARE, "f2_like": f2 >= (F2_SHARE2 if y >= F2_FROM else F2_SHARE), "f3_like": len(town_ok) >= F3_HOUSES, "f4_like": tv >= F4_VALUE,
            "f5_ok": famine == 0 and smin >= F5_STORE and pop >= F5_POP * g["pop0"]}


def year_end(state):
    g, D = _g(state), state["day"]
    y = D // YEAR
    if y < g["start_year"] or str(y) in g["rows"]:
        return
    r = row_of(state, y)
    old = g["old_left"]
    old["h"] = round(old["h"] - min(old["h"], ((_s3()._g(state)["fire"].get(str(y)) or {}).get("house_kg", 0))), 2)
    old["v"] = round(max(0.0, old["v"] - max(0.0, r["coal_burned"] - ((_s3()._g(state)["fire"].get(str(y)) or {}).get("house_kg", 0)))), 2)
    g["rows"][str(y)] = r
    for k in ("f1", "f2", "f3", "f4"):
        if r[f"{k}_like"] and y not in g["f_years"][k]:
            g["f_years"][k].append(y)
        if k not in g["f"] and all((y - i) in g["f_years"][k] for i in range(F_YEARS)):
            g["f"][k] = D
    if not r["f5_ok"] and y not in g["f5_broken"]:
        g["f5_broken"].append(y)


def entrance(state):
    """入口: いちばん新しい 2 年に、f1 と f2 と (f3 か f4) がつづき、その 2 年に f5 を割らない"""
    g = _g(state)
    if not g["rows"]:
        return False
    y = max(int(k) for k in g["rows"])
    ys = [g["rows"].get(str(y - i)) for i in range(F_YEARS)]
    if not all(ys):
        return False
    both = lambda k: all(r[f"{k}_like"] for r in ys)  # noqa: E731
    return both("f1") and both("f2") and (both("f3") or both("f4")) and all(r["f5_ok"] for r in ys)


def check(state, done):
    """g7.check から (年の終わりだけ): 止まるわけ (なければ None)。S3・G15 の相談のかわり"""
    g, D = _g(state), state["day"]
    if (D + 1) % YEAR:
        return None
    y = D // YEAR
    if y < g["start_year"]:
        return None
    r = g["rows"].get(str(y)) or {}
    if entrance(state) and not any(c["why"] == "s4_entrance" for c in done):
        return {"why": "s4_entrance", "year": y, "day": D, "text": f"S4: 入口に着いた ({y - 1}年と{y}年に f1・f2・{'f3' if r.get('f3_like') else 'f4'}。その 2 年に f5 を割らなかった)"}
    if r and not r["f5_ok"] and not any(c["why"] == "s4_f5" and c.get("year") == y for c in done):
        return {"why": "s4_f5", "year": y, "day": D, "text": f"S4: {y}年に f5 (暮らしを守る) を割った (ききん {r['famine']}・蓄えのいちばん少ない日 {r['store_min']} 日分・"
                f"人 {r['pop']} (はじめ {r['pop0']} の {round(F5_POP * 100)}% は {math.ceil(F5_POP * r['pop0'])}))"}
    if (g.get("ask") or D > ASK_DAY) and D == ask_start(state) + ASK_YEARS * YEAR and not any(c["why"] == "s4_ask" for c in done):  # 聞く年 (s4-c) の終わり
        a = g.get("asked") or {}
        return {"why": "s4_ask", "year": y, "day": D, "text": f"S4: 年の集まりで町の家を聞いた {ASK_YEARS} 年が終わった (出した答え "
                + "・".join(f"{k}年 {len(v['yes'])}" for k, v in sorted(a.items())) + f"。いまの町の家 {len(g['town'])})"}
    ys = [g["rows"].get(str(y - i)) for i in range(PATH_YEARS)]
    if ask_window(state) and D > ASK_DAY:  # 聞く年 (s4-c) のあいだは「選ぶ人 2 年 0 人」で止めない (終わりの年に止めて相談する)
        ys = [None]
    if all(x and x["chose"] == 0 for x in ys) and not any(c["why"] == "s4_path" and c.get("year") == y for c in done):
        return {"why": "s4_path", "year": y, "day": D, "text": f"S4: 町の家・掘り場・交換を選ぶ答える人が {PATH_YEARS} 年つづけて 0 人"}
    n = y - g["start_year"] + 1
    if n > 0 and n % LATER_YEARS == 0 and not any(c["why"] == f"s4_years_{y}" for c in done):
        return {"why": f"s4_years_{y}", "year": y, "day": D, "text": f"S4: Society 4.0 に入って {n} 年たった (5 年ごとの相談)"}
    return None


# ---------------- お題 (g15.prompt_block の中。短く) ----------------

def dig_saves_pd(kg):
    return round(kg / g15.COAL_KG * _s3().FIRE_H / _s3().PD_H, 1)


def block_lines(state, p):
    """町の家・掘り場・川下の町の市の行 (答える人ごと)。短く"""
    g, g15g = _g(state), g15._g(state)
    name, h = p["name"], p.get("household")
    ly = (state["day"] + 1) // YEAR - 1  # 終わった年
    rows = []
    tp = sum(len(r["people"]) for r in g["town"].values())
    rows.append(f"- 町の家 (town): 家の大人を、1 年じゅう 1 つの町の仕事 ({'・'.join(JOBS)}) に出す家。その人は畑・ヤギ・水の道には出ない。食べ物は今までどおり村の倉から。"
                f"町の仕事の 1 人日ごとに、村の倉から草の種 {RATION} つかみを家の倉に受ける (受け分。村の蓄えが {RATION_STOP} 日分を切った季節はなし)。")
    led = g["led"].get(str(ly)) or {}
    t = f"  いまの町の家 {len(g['town'])} 家 (大人 {tp} 人)"
    if led:
        t += (f"。{ly}年の町の家の帳面: 町の仕事 {sum(r['days'] for r in led.values())} 人日・食べた 約 {sum(r['ate'] for r in led.values())} つかみ・"
              f"受け分 {sum(r['pay'] for r in led.values())} つかみ / 掘った燃える石 {round(sum(r['coal'] for r in led.values()))} kg・作業場 {sum(r['ws'] for r in led.values())} 人日 "
              f"(板 約 {round(sum(r['planks'] for r in led.values()))} 束)")
    rows.append(t + "。")
    mine = g["town"].get(h) if h else None
    n_ad = len([q for q in era2.adults(state) if h and q.get("household") == h])
    ws = g15.workshops(state, done=True)
    ex_ws = sorted(ws, key=lambda m: (len(_s3().posts_of(state, m)), m))[0] if ws else None
    if fixed(state):  # 直し (s4-b): 書き方の例を、その答える人が書ける形に (持ち場の人は、その作業場だけ)・止まっている作業場はそう書く
        rows[0] += "名前で出すこの町の家は、年の終わりに数える「町の家」(働いた日の半分以上が食べ物でない仕事の家) とは別。"
        post = _s3()._g(state)["posts"].get(name)
        ex = f"{{\"人\": [\"{name}\"], \"仕事\": \"{g15.ACT_DIG}\"}}"
        if post:
            ex_ws = post["mill"]
        if ex_ws:
            m = g15._mill(state, ex_ws)
            stop = " (いまは止まっている。町の家の人が先に「水の輪を直す」)" if m is not None and m.get("stopped") else ""
            ex_w = f"{{\"人\": [\"{name}\"], \"仕事\": \"{g15.ACT_WS_WORK}\", \"輪\": \"{ex_ws}\"}}{stop}"
            ex = ex_w if post else f"{ex} か {ex_w}"
        rows.append(f"  あなたの家 ({h}。大人 {n_ad} 人) は" + (f"町の家 ({'・'.join(mine['people'])} が「{mine['job']}」{(' ' + mine['mill']) if mine.get('mill') else ''})。" if mine else "町の家でない。")
                    + f"書き方 \"town\": {ex}・やめるは {{\"やめる\": true}} (あなたの家の大人だけ。1 家 {TOWN_PER_HOUSE} 人まで"
                    + (f"。{name} は {post['mill']} の{post['post']}なので、町の仕事は {post['mill']} の「{g15.ACT_WS_WORK}」だけ)" if post
                       else f"。持ち場の人は、その作業場の「{g15.ACT_WS_WORK}」だけ)"))
    else:
        rows.append(f"  あなたの家 ({h}。大人 {n_ad} 人) は" + (f"町の家 ({'・'.join(mine['people'])} が「{mine['job']}」{(' ' + mine['mill']) if mine.get('mill') else ''})。" if mine else "町の家でない。")
                    + f"書き方 \"town\": {{\"人\": [\"{name}\"], \"仕事\": \"{g15.ACT_DIG}\"}}" + (f" か {{\"人\": [\"{name}\"], \"仕事\": \"{g15.ACT_WS_WORK}\", \"輪\": \"{ex_ws}\"}}" if ex_ws else "")
                    + f"・やめるは {{\"やめる\": true}} (あなたの家の大人だけ。1 家 {TOWN_PER_HOUSE} 人まで)")
    if g15.coal_on(state):
        pit = g.get("pit")
        now = ("まだない。作るなら \"pit\": true (答えた人の中でいちばん多い中身)" if not pit else
               f"作っている (あと 約 {max(0, PIT_DAYS - pit['work'])} 人日)" if pit.get("done") is None else
               f"ある ({_yd(pit['done'])}にできた)")
        rows.append(f"- 掘り場 (pit): 北の丘に板で支えた掘り場を作ると、掘る 1 人日で燃える石 {PIT_KG} kg (いまは {g15.COAL_KG_DAY} kg)。作るには村の倉の板 {PIT_PLANKS} 束と、"
                    f"掘る {PIT_DAYS} 人日 (そのあいだは 1 人日 {PIT_BUILD_KG} kg)。できたあとは掘る {PIT_WEAR} 人日ごとに板 1 束。"
                    f"{PIT_KG} kg を秋と冬に燃やすと、まき集め 約 {dig_saves_pd(PIT_KG)} 人日が浮く。いま: {now}")
    pr = []
    for (what, get), (unit, rate) in PRICE.items():
        uw = "束" if what == "板" else "kg"
        pr.append(f"{what} {unit} {uw} = {get} {rate} {'つかみ' if get == '草の種' else 'kg'} (今年あと {left(state, (what, get))} {uw})")
    rows.append(f"- {TOWN_NAME}の市 (sell の相手 \"{TOWN}\"): " + "・".join(pr) + "。"
                f"町からもらう物は \"もらう\" に書く (書かなければ草の種)。例 \"sell\": [{{\"物\": \"板\", \"数\": 500, \"相手\": \"{TOWN}\", \"から\": \"村\", \"もらう\": \"燃える石\"}}]")
    fr = food_rate(state, ly)
    if fixed(state):  # 直し (s4-b): くらべの数の中身と、手の使いみちの事実 (後押しはしない)
        pk = g15g["planks"]
        kg = PIT_KG if (g.get("pit") or {}).get("done") is not None else g15.COAL_KG_DAY
        r3 = _s3().CREW[0][2]
        (_, c_rate), (_, p_rate) = PRICE[("燃える石", "草の種")], PRICE[("板", "草の種")]
        rows.append(f"  くらべ: {ly}年は、畑仕事と水の道の 1 人日あたり 刈り入れ 約 {fr} つかみ (その年の刈り入れを、畑仕事と水の道の人日みなで割った数)。"
                    f"町の市の値では、掘る 1 人日 (燃える石 {kg} kg) は草の種 {round(kg * c_rate / 100)} つかみ、{_s3().CREW[0][0]} 人そろった水ののこの 1 人日 (板 {r3} 束) は草の種 {r3 * p_rate} つかみ (町が受ける量まで)。"
                    f"村の倉の板 {pk['stock']} 束 ({ly}年にひいた {pk['made'].get(str(ly), 0)} 束・使った {pk['used'].get(str(ly), 0)} 束)・燃える石 {round(g15g['coal']['stock'])} kg。"
                    f"村の蓄え 約 {era2.store_days(state)} 日分")
        rows += hands_lines(state)
    else:
        rows.append(f"  くらべ: {ly}年は、畑仕事と水の道の 1 人日あたり 刈り入れ 約 {fr} つかみ。村の倉の板 {g15g['planks']['stock']} 束・燃える石 {round(g15g['coal']['stock'])} kg。"
                    f"村の蓄え 約 {era2.store_days(state)} 日分")
    return rows


WEED_NEED = (0.15, 10)  # era2._field_season の草取りに要る時間 (まいた種 × 0.15 + 10)


def weed_times(state):
    """いちばん新しい、育ち終えた秋の畑の (まいた種, した草取り ÷ 要る草取り)。なければ None"""
    fs = [f for f in state["era2"]["fields"] if f["state"] != "育つ" and era2.season(f["day"]) == "秋"]
    if not fs:
        return None
    d = max(f["day"] for f in fs)
    xs = [f for f in fs if f["day"] == d]
    need = sum(f["seed"] * WEED_NEED[0] + WEED_NEED[1] for f in xs)
    return sum(f["seed"] for f in xs), (sum(f["work"] for f in xs) / need if need else 0.0)


def hands_lines(state):
    """直し (s4-b): 畑の草取りと水の道の手入れの事実 (どちらも決まりのとおり。すすめない)"""
    out = []
    w = weed_times(state)
    if w and w[0] > 0:
        out.append(f"  畑の草取り: いちばん新しく実った畑 (秋にまいた {w[0]} つかみ) にした草取りは、要る時間の 約 {round(w[1], 1)} 倍 "
                   f"(要る時間の分までで実りは 10 割。それより多くしても増えない)")
    g13g = state["era2"]["g7"].get("g13") or {}
    cap = (g13g.get("canal") or {}).get("cap", 0)
    if cap:
        sown, _ = g13._water_now(state)
        per = round(g13.CANAL_PER_DAY / g13.CANAL_KEEP)
        out.append(f"  水の道: いま水が来る畑は、秋にまく草の種 {cap} つかみ分で、去年の秋にまいた量の 約 {round(cap / sown) if sown else '-'} 倍。"
                   f"掘る 1 人日で {g13.CANAL_PER_DAY} つかみ分ふえ、手入れに要る人日も、水の来る畑 {per} つかみ分ごとに 1 年 1 人日ふえる "
                   f"(いま 約 {round(cap / per)} 人日。足りない年は、水の来る畑が {round(g13.CANAL_LOSS * 10)} 割へる)")
    return out


def field_rows(state, year=False):
    return ["   town: 町の家 (あなたの家の大人を、1 年じゅう町の仕事に)。例 {\"人\": [名前], \"仕事\": \"燃える石を掘る\"}。やめるは {\"やめる\": true}",
            "   pit: 北の丘の掘り場を作るなら true。sell の \"もらう\": 川下の町からもらう物 (草の種 か 燃える石)"]


ANSWER_FIELDS = {"town": "null", "pit": "null"}


def answer_fields(state):
    return ["town"] + (["pit"] if not _g(state).get("pit") and g15.coal_on(state) else [])


# ---------------- step.py status・決まりの村の行 (村の人のお題には出さない) ----------------

def row_text(r):
    sold = "・".join(f"{k} {v}" for k, v in r["sold"].items()) or "なし"
    return (f"{r['year']}年: 食べ物でない仕事 {r['nonfood']}/{r['worked']} 人日 ({round(r['f1_share'] * 100, 1)}%) / 燃える石 火と力の {round(r['coal_share'] * 100, 1)}% "
            f"(新しい石の分 {round(r['own_share'] * 100)}% → {round(r['f2_share'] * 100, 1)}%)・掘った {round(r['coal_dug'])} kg・替えた {r['coal_bought']} kg・村の倉 {r['coal_stock']} kg・まき集め {r['fire_pd']} 人日 / "
            f"町の家 {r['town']} (大人 {r['town_people']}・180 人日以上 {r['town_ok']})・町の仕事 {r['town_days']} 人日・受け分 {r['town_pay']}・掘り場 {r['pit']} / "
            f"交換 {sold} (ねうち {r['trade_value']}) / 板 {r['planks']} / 選んだ答える人 {r['chose']} (書いた {r['wrote']}) / {r['answerers']} / "
            f"蓄え いちばん少ない {r['store_min']} 日分・ききん {r['famine']}・人 {r['pop']} (はじめ {r['pop0']}) / "
            + " ".join(f"{k} {'○' if r[f'{k}_like'] else '×'}" for k in ("f1", "f2", "f3", "f4")) + f" f5 {'○' if r['f5_ok'] else '×'}")


def lines(state):
    if not on(state):
        return []
    g = _g(state)
    out = [f"{g['why']}。{g['day']} 日目から ({g['start_year']}年から数える)。町の家 {len(g['town'])}・掘り場 {'ある' if (g.get('pit') or {}).get('done') is not None else ('作っている' if g.get('pit') else 'ない')}"
           + " / " + " / ".join(f"{k} {FS[k]} {_yd(g['f'][k]) if k in g['f'] else 'まだ'}" for k in ("f1", "f2", "f3", "f4"))
           + f" / f5 を割った年 {'・'.join(map(str, g['f5_broken'])) or 'なし'} / 入口 {'○' if entrance(state) else 'まだ'}"]
    for y in sorted(g["rows"], key=int)[-3:]:
        out.append(row_text(g["rows"][y]))
    for y, r in sorted((g.get("asked") or {}).items()):  # 聞く年 (s4-c)
        out.append(f"{y}年の集まりで町の家を聞いた: 答える人 {r['answerers']} のうち、出した {len(r['yes'])} ({'・'.join(r['yes']) or 'なし'})・"
                   f"出さない {len(r['no'])}・できなかった {len(r['failed'])}・書かなかった {r['quiet']} / 町の家 {r['town']} (大人 {r['town_people']})")
    return out
