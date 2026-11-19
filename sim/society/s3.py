"""Society 3.0 案 A「見える仕事・持ち場・見習い・交換」(2026-11-17 本人の OK。docs/society_phase/S3_design.md・S3_check.md)

- 印 state.era2.g7.s3 があるときだけ働く。印を書くのは step.py resume --s3 "<本人の言葉>" [--parts a,b,c,d] だけ
  (G15 の後押しなしの確かめが終わって HOLD consult で止まっている村から。1 回だけ)。印がなければ、このファイルは読みこみもしない
  (g7・g15・era2・step.py は「s3」の鍵があるときだけ、関数の中で読みこむ)。だから前の歩は、お題・state・出来事・乱数が 1 バイトも変わらない
- 時代 (state.era) は G15 のまま。G15 の仕組み (水の作業場・燃える石・かまど・板) はそのまま動き、その上に 4 つの部分を足す:
  a まき集めを数える (秋と冬。まきのかまどの人 1 人 1 日 0.4 時間 = 家の大人の次の日の働く時間から引く)・掘った燃える石の 2 割を掘った人の家の倉に
    (その家は自分の倉の石を先に燃やす)・お題に倉が尽きる日
  b 作業場の持ち場 (のこ番・槌番・帳面番 (読める大人)・頭 (集まりで選ぶ))。持ち場の人は「やめる」と書くまで、季節ごとに作業場で働く。
    のこ番の板の 2 割は家の板になる
  c 見習い: 帳面番か読める大人か腕のある人と同じ日に作業場で 20 日働くと、見習いを終えて持ち場 (のこ番・槌番) につく
  d 交換: 板と燃える石を、近い集落 3 つと川下の町に替える (値と今年の残りをお題に出す)
- 乱数は使わない。後押しはしない (g15.push は終わったまま)。印・本人の言葉・「作る側」のことは、村の人のお題にも出来事にも書かない
- 物差し (S3_design.md 5.): e1 掘った石で燃やす・e2 作業場が続く・e3 自分で選ぶ・e4 教えて広がる・e5 暮らしを守る。年の終わりに行を残す
  (2026-11-17 の直し: e3 は持ち場・掘る仕事を続けている答える人も数える・e4 は 1 年じゅう持ち場の人 10 人と見習いを終えた人 1 人・
   e5 の人は印の日の人の 95% 以上・持ち場の上限 16 → 24)
  (2026-11-18 の直し。FIX_DAY より後だけ: e1 は S3 に入ってから掘ってためた石で数える・お題の持ち場の人の去年の日と石のかまどの家の数)
  (2026-11-18 の 2 つめの直し「得が出るようにする」。RETURN_DAY より後だけ: 水ののこは同じ日の人が多いほど 1 人日の板がふえる (crew_rate)・
   板は水の道の手入れにも使える (canal_rate)・家の板は家の住まいとかまどに先に使う (house_plank)・60 日働いたのこ番も見習いを教えられる・
   お題に板の返りと残っている手入れの行 (plank_lines))
  (2026-11-19 の直し。COAL_DAY より後だけ: お題の村の倉の尽きる日は村の倉から燃やす分だけで出す・秋の集まりでも去年のまき集めの人日を出す)
- 止まり: 入口 (e1・e2 と e3 か e4。そのあいだ e5 を割らない) で HOLD entrance。e5 を割った・道を選ぶ人が 2 年 0 人・村の倉の石が尽きて
  だれも掘らない・5 年ごとで HOLD consult (G15 の相談はかわりに止める)
"""
import json
import math

import era2
import g10
import g13
import g15
from world import log, season

YEAR, SEASON_DAYS = era2.YEAR, era2.SEASON_DAYS
S3_FROM = 24479  # 本物の村が後押しなしの確かめを終えて止まった日 (203年120日目)。これより前には印を書けない
S3_DATE = "2026-11-17"
S3_NAME = "Society 3.0 (案 A)"
PARTS = {"a": "まき集めを数える・掘った石の 2 割を家の倉に・倉が尽きる日",
         "b": "作業場の持ち場 (のこ番・槌番・帳面番・頭)",
         "c": "見習い (20 日で持ち場)",
         "d": "板と燃える石の交換"}
PART_ORDER = ("a", "b", "c", "d")
# a まき集め【仮定】
PD_H = 6  # 1 人日 = 6 時間 (g13 の粉ひきと同じ数え方)
FIRE_H = 0.4  # まきのかまどの人 1 人 1 日のまき集め (時間。約 0.07 人日。4 人の家で 1 日 約 0.3 人日)
FIRE_SEASONS = ("秋", "冬")
HOUSE_SHARE = 0.2  # 掘った燃える石のうち、掘った人の家の倉に入る分
# b 持ち場【仮定】
SAW_K, HAM_K, LEDGER_K, HEAD_K = "のこ番", "槌番", "帳面番", "頭"
POSTS = (SAW_K, HAM_K, LEDGER_K, HEAD_K)
POST_CAP = 24  # 1 つの作業場の持ち場の人 (2026-11-17 の直しで 16 → 24。見習いを終えた人が持ち場につけるように。1 日に働けるのは g15.WS_CAP の 20 人まで)
LEDGER_CAP = 2
PLANK_HOME = 0.2  # のこの持ち場の人がひいた板のうち、家の板になる分
POST_SRC = "持ち場を続ける"  # g7.src の値 (写しの記録では post に分ける)
# c 見習い【仮定】
APPR_DAYS = 20
# d 交換【仮定】(町は川下の町。作る側が置いた相手。値は作る側が決めた)
TOWN = "町"
TOWN_NAME = "川下の町"
PARTNERS_N = 3
PRICE_TOWN = {"板": (1, {"草の種": 35}), "燃える石": (100, {"草の種": 30})}  # (1 回の単位, もらう物)
PRICE_SETT = {"板": (10, {"ヤギ": 1}), "燃える石": (100, {"草の種": 25})}
PRICE_SETT_NOGOAT = {"板": (10, {"草の種": 300})}
CAP_TOWN = {"板": 300, "燃える石": 20000}  # 1 年に買う量
CAP_SETT = {"板": 2, "燃える石": 30}  # 集落の人 1 人あたり、1 年に買う量
SELL_MAX = 6
# 物差し【仮定】(S3_design.md 5.)
E1_DUG, E1_SHARE, E1_YEARS = 0.8, 0.5, 2
E2_PEOPLE, E2_HOUSES, E2_DAYS, E2_YEARS = 8, 3, 30, 2
E3_SHARE, E3_YEARS = 0.2, 2
E4_N, E4_NEW, E4_YEARS = 10, 1, 2  # 2026-11-17 の直し: 1 年じゅう持ち場の人 10 人以上と、その年に見習いを終えた人 1 人以上 (読める人が教えた割合は見ない)
E5_STORE = 120
E5_POP = 0.95  # 2026-11-17 の直し: 年の終わりの人が、印を書いた日の人 (pop0) の 95% 以上 (前の年より減らない、をやめた)
LATER_YEARS = 5
# 2026-11-18 の直し (S3_check.md 6.・7.): 本物の村が 5 年の相談で止まった日 (208年の終わり) より後の年の終わりとお題だけ。
# この日までの歩 (やり直し) は、state・お題・出来事が 1 バイトも変わらない
FIX_DAY = 25079
PATH_YEARS = 2
# 2026-11-18 の 2 つめの直し (本人の「得が出るようにする」。S3_design.md 2.5・S3_check.md 8.)【仮定】: 作業場の返り。
# 本物の村が止まっている日 (25079) より後の日だけ。それまでの歩は 1 バイトも変わらない
RETURN_DAY = 25079
# 2026-11-18: 入口の e5 は「ずっと割らない」でなく「数えた 2 年 (いちばん新しい年とその前の年) に割らない」。
# 205年に一度割ると入口に二度と着けなかったため。この日より後だけ (前の歩は入口がなりたたないので同じ)
ENTRANCE_DAY = 25439
# 2026-11-19: 燃える石の行の 2 つのまちがいの直し (S3_check.md 11.)。本物の村が止まっている日 (25799。214年の終わり) より後のお題だけ。
# (1) 村の倉の尽きる日は、村の倉から燃やす分だけで出す (前は、その家しか燃やさない家の倉の石も足して、村じゅうで割っていた)。
# (2) まき集めの人日は、家ごとのまき集めがある年を出す (前は、秋の集まりで今年の数がまだなく、行が出なかった)
COAL_DAY = 25799
CREW = ((8, 3, 3), (4, 1, 2))  # (同じ日・同じ作業場の人, 家, 1 人日の板)。上から先に当てる。どれにも当たらなければ g15.PLANK_PER_DAY (1)
TEACH_SAW_DAYS = 60  # のこ番は、その作業場で合わせて 60 日働くと見習いを教えられる
ES = {"e1": "掘った燃える石で燃やす", "e2": "作業場が続く", "e3": "自分で選ぶ", "e4": "教えて広がる", "e5": "暮らしを守る"}
FS = {"F1": "はじめて持ち場についた人", "F2": "はじめて村の人が掘った燃える石", "F3": "はじめての見習いの終わり", "F4": "はじめて板か燃える石を交換した"}
# 村の人に見せない言葉 (お題と出来事。試しで確かめる)
HIDE = ("後押し", "反実仮想", "作る側", "Society", "S3", "案 A", "本人")
CHOSE_ACTS = (g15.ACT_WS_WORK, g15.ACT_WS_BUILD, g15.ACT_DIG)


def fixed(state):
    """2026-11-18 の直し (e1 を掘りためた石で数える・お題の 2 つの数のまちがい) が働くか: FIX_DAY より後の日だけ"""
    return state["day"] > FIX_DAY


def coal_fixed(state):
    """2026-11-19 の直し (燃える石の行: 村の倉の尽きる日・まき集めの年) が働くか: COAL_DAY より後の日だけ"""
    return state["day"] > COAL_DAY


def ret(state):
    """2026-11-18 の 2 つめの直し (作業場の返り) が働くか: 印があって、RETURN_DAY より後の日だけ"""
    return on(state) and state["day"] > RETURN_DAY


def on(state):
    return "day" in (((state.get("era2") or {}).get("g7") or {}).get("s3") or {})


def _g(state):
    return state["era2"]["g7"]["s3"]


def part(state, k):
    return on(state) and k in _g(state)["parts"]


def _y(state):
    return state["day"] // YEAR


def _yd(day):
    return f"{day // YEAR}年{day % YEAR + 1}日目"


def _adult(state, name):
    return next((p for p in era2.adults(state) if p["name"] == name), None)


# ---------------- 印 (step.py resume --s3) ----------------

def why_text(words):
    return f"{S3_NAME} (本人の言葉 {S3_DATE} 「{words}」)"


def parse_parts(text):
    """--parts の文 → 部分の並び。書かなければみな。知らない名前があれば ValueError"""
    if text is None or not str(text).strip():
        return list(PART_ORDER)
    xs = [x.strip() for x in str(text).replace("・", ",").split(",") if x.strip()]
    bad = [x for x in xs if x not in PARTS]
    if bad:
        raise ValueError(f"知らない部分: {'・'.join(bad)} (選べるのは {','.join(PART_ORDER)})")
    return [x for x in PART_ORDER if x in xs]


def refusal(state, words):
    """resume --s3 ができないわけ (できるなら None)"""
    if not (words or "").strip():
        return "--s3 には本人の言葉が要る"
    if not g15.on(state) or state.get("era") != "G15":
        return "G15 でないので、Society 3.0 は始められない"
    g7s = state["era2"]["g7"]
    if "s3" in g7s:
        return "Society 3.0 はもう始めてある"
    if state["day"] < S3_FROM:
        return f"Society 3.0 は {S3_FROM} 日目 (後押しなしの確かめの終わり) からだけ"
    a = g15._g(state).get("after") or {}
    if a.get("end") is None:
        return "後押しなしの確かめが終わっていない"
    if not (state.get("hold") and (g7s.get("hold") or {}).get("why") == "consult"):
        return "Society 3.0 は、相談 (HOLD consult) で止まっているときに resume と一緒にだけ始める"
    if g15.push_on(state):
        return "後押しが動いている"
    return None


def mark(state, words, parts=None):
    """resume --s3 から: 印 g7.s3 を書く (村の出来事には残さない)。parts: 部分の並び (なければみな。決まりの村は 1 つずつも)"""
    words = words.strip()
    D = state["day"]
    ps = list(PART_ORDER) if parts is None else [x for x in PART_ORDER if x in parts]
    g = state["era2"]["g7"]["s3"] = {
        "day": D, "words": words, "why": why_text(words), "parts": ps, "start_year": D // YEAR + 1,
        "hcoal": {}, "hplanks": {}, "fire": {}, "dug": {}, "posts": {}, "quit": [], "head": {}, "appr": {}, "appr_done": [],
        "sales": [], "sold": {}, "chose": {}, "rows": {}, "e": {}, "e_years": {k: [] for k in ("e1", "e2", "e3", "e4")}, "e5_broken": [],
        "reached": {}, "store_min": {}, "pop0": len([p for p in state["people"] if p["alive"]])}
    return g


# ---------------- a 燃える石とまき集め ----------------

def dig(state, p, kg):
    """g15._dig から: 掘った石の 2 割を掘った人の家の倉に (a のときだけ)。戻り値: 村の倉に入る kg"""
    g, y = _g(state), str(_y(state))
    name, h = p["name"], p.get("household")
    d = g["dug"].setdefault(y, {})
    d[name] = d.get(name, 0) + kg
    if "F2" not in g["reached"]:
        _reach(state, "F2", f"{name} が北の丘で燃える石を掘った")
    if not part(state, "a") or not h:
        return kg
    mine = round(kg * HOUSE_SHARE, 1)
    g["hcoal"][h] = round(g["hcoal"].get(h, 0) + mine, 1)
    return kg - mine


def evening(state, en, y):
    """g15.evening のかわり (印のあと): 石のかまどの家は、家の倉の石を先に燃やし、足りなければ村の倉から。
    a のときは、秋と冬に、まきのかまどの人 1 人につき FIRE_H 時間を、その家の大人の次の日の働く時間から引く。戻り値: 燃える石の人日"""
    g15g, g = g15._g(state), _g(state)
    alive = [p for p in state["people"] if p["alive"]]
    homes = {}
    for p in alive:
        h = p.get("household")
        if h:
            homes.setdefault(h, []).append(p)
    covered = set()
    coal_pd = 0
    if g15.coal_on(state) and g15g["stoves"]:
        c = g15g["coal"]
        for h in sorted(homes):
            if not g15.stove_done(state, h):
                continue
            need = round(len(homes[h]) * g15.COAL_KG, 2)
            own = g["hcoal"].get(h, 0)
            if own + c["stock"] < need:
                continue
            take = min(own, need)
            if take:
                g["hcoal"][h] = round(own - take, 2)
                f = g["fire"].setdefault(y, {})
                f["house_kg"] = round(f.get("house_kg", 0) + take, 2)
            rest = round(need - take, 2)
            if rest:
                c["stock"] = round(c["stock"] - rest, 2)
            c["burned"][y] = round(c["burned"].get(y, 0) + need, 2)
            en["coal_kg"] = round(en["coal_kg"] + need, 2)
            coal_pd += len(homes[h])
            covered.add(h)
            if "F2" not in g15g["reached"]:
                g15._reach(state, "F2", state["day"], f"{h}の石のかまどで、北の丘から掘った燃える石を燃やした")
    if part(state, "a") and season(state["day"]) in FIRE_SEASONS:
        f = g["fire"].setdefault(y, {})
        hrs_all, pd_all, saved = 0.0, 0, 0
        for h in sorted(homes):
            ps = homes[h]
            if h in covered:
                saved += len(ps)
                continue
            ads = [p for p in ps if not p.get("child")]
            pd_all += len(ps)
            if not ads:
                f["no_adult"] = f.get("no_adult", 0) + len(ps)
                continue
            hrs = round(FIRE_H * len(ps) / len(ads), 3)
            for p in ads:
                p["eve_h"] = round(p.get("eve_h", 0) + hrs, 3)
            hrs_all += hrs * len(ads)
            fh = f.setdefault("house", {})
            fh[h] = round(fh.get(h, 0) + FIRE_H * len(ps) / PD_H, 3)
        f["wood_pd"] = f.get("wood_pd", 0) + pd_all
        f["hours"] = round(f.get("hours", 0) + hrs_all, 2)
        f["saved_pd"] = f.get("saved_pd", 0) + saved
    return coal_pd


def burn_per_day(state, h=None):
    """石のかまどの家 (h があればその家) の 1 日の燃える石 (kg)"""
    n = 0
    for p in state["people"]:
        if p["alive"] and p.get("household") and g15.stove_done(state, p["household"]) and (h is None or p["household"] == h):
            n += 1
    return n * g15.COAL_KG


def runout(state, kg, per_day):
    """倉が尽きる日 (通しの日。燃やさないなら None)"""
    if per_day <= 0:
        return None
    return state["day"] + int(kg // per_day)


def vill_draw(state):
    """村の倉から 1 日に燃やす燃える石 (kg) と、その家の数: 石のかまどの家のうち、家の倉の石が 1 日分にとどかない家 (evening と同じ順: 家の倉が先)"""
    need = {}
    for p in state["people"]:
        h = p.get("household")
        if p["alive"] and h and g15.stove_done(state, h):
            need[h] = need.get(h, 0) + g15.COAL_KG
    hc = _g(state)["hcoal"]
    hs = [h for h in need if hc.get(h, 0) < need[h]]
    return sum(need[h] - hc.get(h, 0) for h in hs), len(hs)


def dig_saves_pd():
    """燃える石 1 人日分 (200 kg) を秋と冬に燃やすと浮くまき集めの人日"""
    return round(g15.COAL_KG_DAY / g15.COAL_KG * FIRE_H / PD_H, 1)


# ---------------- 作業場の返り (2026-11-18 の 2 つめの直し。ret のときだけ) ----------------

def crew_rate(n, houses):
    """同じ日・同じ作業場 (水ののこ) に n 人 (houses 家) いるときの、1 人日の板"""
    for k, hh, r in CREW:
        if n >= k and houses >= hh:
            return r
    return g15.PLANK_PER_DAY


def saw_planks(state, names):
    """g15.work_day から: names (その日その作業場で働いた人。いま来た人が最後) の、いま来た人の分の板。
    その日の板の合わせ (人 × crew_rate) が、1 人ふえてどれだけふえたか (日の終わりには、人 × crew_rate になる)"""
    if not ret(state):
        return g15.PLANK_PER_DAY
    hs = {p["name"]: p.get("household") for p in state["people"] if p["alive"]}

    def tot(ns):
        return len(ns) * crew_rate(len(ns), len({hs.get(n) or n for n in ns})) if ns else 0
    k = tot(names) - tot(names[:-1])
    y = str(_y(state))
    c = _g(state).setdefault("crew", {}).setdefault(y, {})
    c["extra"] = c.get("extra", 0) + k - g15.PLANK_PER_DAY
    return k


def canal_left(state, y=None):
    """y 年 (なければ今の年) の水の道の手入れの残り (人日。g13 の年の終わりの決まりと同じ数え方。読むだけ)"""
    c = state["era2"]["g7"]["g13"]["canal"]
    y = _y(state) if y is None else y
    return max(0.0, c["cap"] / g13.CANAL_PER_DAY * g13.CANAL_KEEP - c["dug"].get(str(y), 0))


def canal_rate(state):
    """g13.work_day (水の道を掘る) から: この年の手入れが残っていて、村の倉に板があれば 1 束使って 2 人日分 (ret のときだけ)"""
    if not ret(state) or canal_left(state) <= 0:
        return 1
    return int(g15.plank_rate(state))


def house_plank(state, h):
    """g15.plank_rate から (住まい・かまど): 家の板が 1 束以上あれば 1 束使う (ret のときだけ)。戻り値: 使ったか"""
    g = _g(state)
    if not ret(state) or not h or g["hplanks"].get(h, 0) < 1:
        return False
    g["hplanks"][h] = round(g["hplanks"][h] - 1, 2)
    y = str(_y(state))
    g.setdefault("hused", {})[y] = g.get("hused", {}).get(y, 0) + 1
    return True


def plank_lines(state, p):
    """お題の板の返りの行 (ret で、使える水ののこの作業場があるとき)。短く"""
    g15g = g15._g(state)
    if not ret(state) or not any(g15g["ws"][m]["tool"] == g15.SAW for m in g15.workshops(state, done=True)):
        return []
    import g14
    y = g14.plan_year(state)
    due = round(g13.mill_due(state, y) + g13.restart_left(state))
    cl = round(canal_left(state, y))
    (n3, h3, r3), (n2, _, r2) = CREW
    h = p.get("household")
    hp = int(_g(state)["hplanks"].get(h, 0)) if h else 0
    return [f"- 板の返り: 水ののこは、同じ作業場で同じ日に {h3} 家から {n3} 人そろうと 1 人日で板 {r3} 束 ({n2} 人からは {r2} 束・{n2 - 1} 人までは "
            f"{g15.PLANK_PER_DAY} 束)。板 1 束で、水の輪の直し・水の道の手入れ・住まい・かまどの作りかえの 1 人日が {round(g15.PLANK_BOOST)} 人日分になり、"
            f"手入れ 1 人日が浮く ({n3} 人そろった日は、のこの 1 人日で 約 {r3 * round(g15.PLANK_BOOST - 1)} 人日が浮く)。",
            f"  いま残っている手入れ: 水の輪の直し あと {due} 人日・水の道の手入れ あと {cl} 人日 (板があれば、その分の人日が半分ですむ)。"
            f"村の倉の板 {g15g['planks']['stock']} 束" + (f"・あなたの家の板 {hp} 束 (家の住まいとかまどに先に使う)" if hp else "")]


# ---------------- b 持ち場・c 見習い ----------------

def posts_of(state, mid=None, kind=None):
    g = _g(state)
    return sorted(n for n, r in g["posts"].items() if (mid is None or r["mill"] == mid) and (kind is None or r["post"] == kind))


def post_why(state, name, kind, mid):
    """持ち場につけないわけ (つけるなら None)"""
    g = _g(state)
    p = _adult(state, name)
    if p is None:
        return f"{name} という大人はいない"
    if kind not in (SAW_K, HAM_K, LEDGER_K):
        return f"持ち場は {SAW_K}・{HAM_K}・{LEDGER_K} だけ (頭は集まりで選ぶ)"
    w = g15._g(state)["ws"].get(mid)
    if not w or w.get("done") is None:
        return f"{mid} は使える作業場でない"
    if name in g["posts"]:
        r = g["posts"][name]
        return f"{name} はもう {r['mill']} の{r['post']}"
    if kind == SAW_K and w["tool"] != g15.SAW:
        return f"{mid} は{w['tool']}の作業場なので、{SAW_K}はない"
    if kind == HAM_K and w["tool"] != g15.HAMMER:
        return f"{mid} は{w['tool']}の作業場なので、{HAM_K}はない"
    if kind == HAM_K and not (g10.smith(state, name) or any(x["name"] == name for x in g["appr_done"])):
        return f"{name} は黒い金属の腕がない ({HAM_K}は腕のある人か、見習いを終えた人)"
    if kind == LEDGER_K and name not in set(g10.readers(state)):
        return f"{name} は読み書きできない ({LEDGER_K}は読める大人)"
    if kind == LEDGER_K and len(posts_of(state, mid, LEDGER_K)) >= LEDGER_CAP:
        return f"{mid} の{LEDGER_K}はもう {LEDGER_CAP} 人"
    if len(posts_of(state, mid)) >= POST_CAP:
        return f"{mid} の持ち場はもう {POST_CAP} 人"
    return None


def _take_post(state, name, kind, mid, via, by=None):
    g, D = _g(state), state["day"]
    g["posts"][name] = {"post": kind, "mill": mid, "day": D, "via": via, "by": by, "days": {}, "planks": 0.0}
    p = _adult(state, name)
    log(state, "持ち場", name, f"{name} が、作業場 {mid} の{kind}になった (やめると答えるまで、季節ごとに作業場で働く)", mill=mid, post=kind, via=via)
    _reach(state, "F1", f"{name} が {mid} の{kind}になった")
    return p


def quit_post(state, name, why):
    g = _g(state)
    r = g["posts"].pop(name, None)
    if not r:
        return
    g["quit"].append({"name": name, "post": r["post"], "mill": r["mill"], "day": state["day"], "why": why})
    g["quit"] = g["quit"][-40:]
    for mid, hd in list(g["head"].items()):
        if hd.get("name") == name:
            g["head"].pop(mid)
    if why != "亡くなった・村を出た":
        log(state, "持ち場", name, f"{name} が、作業場 {r['mill']} の{r['post']}をやめた ({why})", mill=r["mill"], post=r["post"], quit=True)


def _prune(state):
    """亡くなった・村を出た人の持ち場と見習いを外す (出来事にはしない)"""
    g = _g(state)
    alive = {p["name"] for p in era2.adults(state)}
    for n in sorted(g["posts"]):
        if n not in alive:
            quit_post(state, n, "亡くなった・村を出た")
    for n in sorted(g["appr"]):
        if n not in alive:
            g["appr"].pop(n)
    for mid, hd in list(g["head"].items()):
        if hd.get("name") not in alive:
            g["head"].pop(mid)


def season_start(state):
    """季節のはじめ (g7._apply の終わり。その季節の仕事が決まったあと): 持ち場の人は、作業場で働く (止まった輪なら直す)。
    集まり直し (ききん) の季節は、持ち場の人もその季節の答えのまま"""
    g = _g(state)
    _prune(state)
    if not (part(state, "b") or part(state, "c")):
        return
    if state["era2"]["g7"].get("ask") == "集まり直し":
        return
    src = state["era2"]["g7"].setdefault("src", {})
    for n in sorted(g["posts"]):
        p = _adult(state, n)
        r = g["posts"][n]
        if p is None:
            continue
        m = g15._mill(state, r["mill"])
        if m is not None and m.get("stopped") and g13.can_do(state, g13.ACT_MILL_FIX):
            p["plan"] = {"activity": g13.ACT_MILL_FIX, "place": "camp", "with": []}
            g15._g(state)["dest"].pop(n, None)
        else:
            p["plan"] = {"activity": g15.ACT_WS_WORK, "place": "camp", "with": []}
            g15._g(state)["dest"][n] = r["mill"]
        src[n] = POST_SRC


def sawyer(state, n, mid):
    """その作業場で合わせて TEACH_SAW_DAYS 日以上働いたのこ番か (2026-11-18 の 2 つめの直し。ret のときだけ教えられる)"""
    r = _g(state)["posts"].get(n) or {}
    return r.get("post") == SAW_K and r.get("mill") == mid and sum(r.get("days", {}).values()) >= TEACH_SAW_DAYS


def teachers(state, mid, names):
    """その日、作業場で教えられる人: その作業場の帳面番・読める大人 (c)・黒い金属の腕のある人。ret のあとは、60 日働いたのこ番も"""
    rd = set(g10.readers(state))
    g = _g(state)
    sw = ret(state)
    return [n for n in names if (g["posts"].get(n) or {}).get("post") == LEDGER_K and g["posts"][n]["mill"] == mid
            or n in rd or g10.smith(state, n) or (sw and sawyer(state, n, mid))]


def ws_season(state):
    """季節の終わり (g15.season_end から、g15._ws_season の前): 持ち場の人の日・のこの板の 2 割を家の板に (b)・見習いの日を数えて、20 日で持ち場 (c)"""
    g, g15g = _g(state), g15._g(state)
    hs = {p["name"]: p.get("household") for p in era2.adults(state)}
    for mid, days in sorted(g15g["wsday"].items()):
        w = g15g["ws"].get(mid) or {}
        for ds, names in sorted(days.items(), key=lambda kv: int(kv[0])):
            y = str(int(ds) // YEAR)
            for n in names:
                r = g["posts"].get(n)
                if r and r["mill"] == mid:
                    r["days"][y] = r["days"].get(y, 0) + 1
                    if part(state, "b") and w.get("tool") == g15.SAW and hs.get(n) and g15g["planks"]["stock"] >= 1:
                        r["planks"] = round(r["planks"] + PLANK_HOME, 2)
                        h = hs[n]
                        before = int(g["hplanks"].get(h, 0))
                        g["hplanks"][h] = round(g["hplanks"].get(h, 0) + PLANK_HOME, 2)
                        if int(g["hplanks"][h]) > before:
                            g15g["planks"]["stock"] -= 1  # 家の板 1 束になった分を、村の倉から家に移す
            if not part(state, "c"):
                continue
            tc = teachers(state, mid, names)
            if not tc:
                continue
            for n in names:
                if n in tc or n in g["posts"] or n not in hs:
                    continue
                a = g["appr"].setdefault(n, {"mill": mid, "days": 0, "start": int(ds), "by": {}})
                a["days"] += 1
                a["mill"] = mid
                t = tc[0] if tc[0] != n else tc[-1]
                a["by"][t] = a["by"].get(t, 0) + 1
                if a["days"] >= APPR_DAYS:
                    _finish(state, n, a, mid, w.get("tool"), int(ds))


def _finish(state, n, a, mid, tool, day):
    g = _g(state)
    t = max(a["by"], key=lambda k: (a["by"][k], k))
    rd = t in set(g10.readers(state))
    g["appr"].pop(n, None)
    g["appr_done"].append({"name": n, "mill": mid, "teacher": t, "reader": rd, "day": day, "year": day // YEAR})
    g["appr_done"] = g["appr_done"][-200:]
    kind = HAM_K if tool == g15.HAMMER else SAW_K
    log(state, "見習い", n, f"{n} が、作業場 {mid} で {t} に教わって、見習い ({APPR_DAYS} 日) を終えた", mill=mid, teacher=t)
    _reach(state, "F3", f"{n} が {t} に教わって見習いを終えた")
    if n not in g["posts"] and post_why(state, n, kind, mid) is None:
        _take_post(state, n, kind, mid, "見習い", t)


# ---------------- d 交換 ----------------

def partners(state):
    """交換の相手: 近い集落 3 つ (人のいる集落。近い順) と川下の町 (d のときだけ)"""
    setts = sorted(g13.settlements(state), key=lambda o: (o.get("days", 99), int(o["id"][1:])))[:PARTNERS_N]
    out = []
    for o in setts:
        pr = dict(PRICE_SETT)
        if o.get("goats", 0) < 3:
            pr.update(PRICE_SETT_NOGOAT)
        out.append({"id": o["id"], "name": o["name"], "price": pr, "cap": {k: v * o.get("people", 0) for k, v in CAP_SETT.items()}, "o": o})
    out.append({"id": TOWN, "name": TOWN_NAME, "price": dict(PRICE_TOWN), "cap": dict(CAP_TOWN), "o": None})
    return out


def left(state, pt, what):
    y = str((state["day"] + 1) // YEAR)
    sold = ((_g(state)["sold"].get(y) or {}).get(pt["id"]) or {}).get(what, 0)
    return max(0, pt["cap"].get(what, 0) - sold)


def _have(state, side, what):
    g, g15g = _g(state), g15._g(state)
    if side == "村":
        return int(g15g["planks"]["stock"]) if what == "板" else int(g15g["coal"]["stock"])
    return int(g["hplanks"].get(side, 0)) if what == "板" else int(g["hcoal"].get(side, 0))


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
        try:
            n = int(float(r.get("数") or r.get("n") or 0))
        except (TypeError, ValueError):
            n = 0
        if what in ("板", "燃える石") and to and n > 0:
            out.append((what, n, to.upper() if to.upper().startswith("N") else to, "村" if side == "村" else "家"))
    return out


def sell(state, who, side, what, n, to):
    """1 つの交換 (乱数なし)。side は「村」か家の名前。戻り値: もらった物 (できなければ None とわけ)"""
    g, g15g = _g(state), g15._g(state)
    pt = next((x for x in partners(state) if x["id"] == to or x["name"] == to), None)
    if pt is None:
        return None, f"{to} という交換の相手はいない"
    unit, gets = pt["price"][what]
    n = min(n, _have(state, side, what), left(state, pt, what))
    k = n // unit
    if pt["o"] is not None and "ヤギ" in gets:
        k = min(k, max(0, pt["o"].get("goats", 0) - 2))
    if pt["o"] is not None and "草の種" in gets:
        k = min(k, int(pt["o"].get("grain", 0) * 0.5) // gets["草の種"])
    if k <= 0:
        return None, f"{pt['name']} と{what}を替えられなかった (物が足りないか、相手が今年はもう要らない)"
    q = k * unit
    got = {kk: vv * k for kk, vv in gets.items()}
    if side == "村":
        if what == "板":
            g15g["planks"]["stock"] -= q
        else:
            g15g["coal"]["stock"] = round(g15g["coal"]["stock"] - q, 2)
    else:
        key = "hplanks" if what == "板" else "hcoal"
        g[key][side] = round(g[key].get(side, 0) - q, 2)
    if pt["o"] is not None:
        if "ヤギ" in got:
            pt["o"]["goats"] -= got["ヤギ"]
        if "草の種" in got:
            pt["o"]["grain"] -= got["草の種"]
    era2._g6_put(state, side, got)
    y = str((state["day"] + 1) // YEAR)
    row = g["sold"].setdefault(y, {}).setdefault(pt["id"], {})
    row[what] = row.get(what, 0) + q
    for kk, vv in got.items():
        row["got_" + kk] = row.get("got_" + kk, 0) + vv
    g["sales"].append({"day": state["day"], "who": who, "side": side, "what": what, "n": q, "to": pt["id"], "got": got})
    g["sales"] = g["sales"][-60:]
    unit_w = "束" if what == "板" else "kg"
    gw = "・".join(f"{kk} {vv}{' 頭' if kk == 'ヤギ' else ' つかみ'}" for kk, vv in got.items())
    log(state, "交換", who, f"{who} が、{'村' if side == '村' else side}の{what} {q} {unit_w}を {pt['name']} に渡して、{gw} を受けた", to=pt["id"], what=what, n=q, got=got)
    _reach(state, "F4", f"{what} {q} {unit_w}を {pt['name']} と替えた")
    return got, None


# ---------------- 集まりの答え (g7.apply_year から。G15 の workshop のあと) ----------------

def _post_rows(v):
    if isinstance(v, dict):
        v = [v]
    if not isinstance(v, list):
        return []
    out = []
    for r in v[:8]:
        if not isinstance(r, dict):
            continue
        n = str(r.get("人") or r.get("name") or "").strip()
        kind = str(r.get("持ち場") or r.get("post") or "").strip()
        mid = str(r.get("輪") or r.get("mill") or "").strip().upper()
        q = era2._yes(r.get("やめる")) if hasattr(era2, "_yes") else bool(r.get("やめる"))
        if n:
            out.append((n, kind, mid, bool(q)))
    return out


def held(state, name):
    """答える人が、いま道を続けているか (e3。2026-11-17 の直し): 自分か家の大人が、持ち場についている・いまの季節の仕事が燃える石を掘る
    (持ち場も掘る仕事も、答えに書きなおさなくても続く)"""
    g = _g(state)
    h = _house_of(state, name)
    fam = [q for q in era2.adults(state) if q["name"] == name or (h and q.get("household") == h)]
    return any(q["name"] in g["posts"] or (q.get("plan") or {}).get("activity") == g15.ACT_DIG for q in fam)


def count_chose(state, real):
    """答えを当てはめる前 (g15.count_paths のあと): 作業場か掘る仕事を、自分か家の人に割り振った答える人と、
    いま自分か家の大人が持ち場・掘る仕事を続けている答える人 (e3。2026-11-17 の直しで、続けている人も数える)"""
    g = _g(state)
    y = str((state["day"] + 1) // YEAR)
    row = g["chose"].setdefault(y, {"meetings": 0, "answerers": 0, "chose": 0, "who": []})
    row["meetings"] += 1
    row["answerers"] = max(row["answerers"], len(real))
    n = w = 0
    for name, a in sorted(real.items()):
        if not isinstance(a, dict):
            continue
        txt = json.dumps({x: a.get(x) for x in ("year", "job", "family")}, ensure_ascii=False)
        wrote = any(x in txt for x in CHOSE_ACTS) or bool(_post_rows(a.get("post")))
        w += wrote
        if wrote or held(state, name):
            n += 1
            if name not in row["who"]:
                row["who"] = (row["who"] + [name])[:30]
    row["chose"] = max(row["chose"], n)
    row["wrote"] = max(row.get("wrote", 0), w)


def apply_answers(state, real):
    """集まりの答え: post (持ち場につく・やめる。自分か家の大人)・head (作業場の頭。答えた人の中でいちばん多い中身)・sell (交換)"""
    import g7
    g = _g(state)
    _prune(state)
    count_chose(state, real)
    hs = {p["name"]: p.get("household") for p in era2.adults(state)}
    if part(state, "b"):
        for name, a in sorted(real.items()):
            if not isinstance(a, dict):
                continue
            for n, kind, mid, q in _post_rows(a.get("post")):
                if hs.get(n) is None or hs.get(n) != hs.get(name):
                    continue  # 自分か家の大人だけ
                if q:
                    if n in g["posts"]:
                        quit_post(state, n, f"{name} の答え")
                    continue
                why = post_why(state, n, kind, mid)
                if why is None:
                    _take_post(state, n, kind, mid, "答え", name)
        votes = {}
        for name, a in real.items():
            if not isinstance(a, dict) or not isinstance(a.get("head"), dict):
                continue
            mid = str(a["head"].get("輪") or a["head"].get("mill") or "").strip().upper()
            who = str(a["head"].get("人") or a["head"].get("name") or "").strip()
            if mid and who:
                votes[name] = json.dumps({"輪": mid, "人": who}, ensure_ascii=False)
        if votes:
            ch, txt = g7._tally(state, votes, g7._vote_weights(state, real))
            if ch:
                r = json.loads(ch)
                w = g15._g(state)["ws"].get(r["輪"])
                if w and w.get("done") is not None and _adult(state, r["人"]) and (g["head"].get(r["輪"]) or {}).get("name") != r["人"]:
                    if r["人"] in g["posts"] and g["posts"][r["人"]]["mill"] != r["輪"]:
                        quit_post(state, r["人"], f"{r['輪']} の頭になった")
                    old = (g["head"].get(r["輪"]) or {}).get("name")
                    g["head"][r["輪"]] = {"name": r["人"], "day": state["day"], "votes": txt}
                    if r["人"] not in g["posts"]:
                        g["posts"][r["人"]] = {"post": HEAD_K, "mill": r["輪"], "day": state["day"], "via": "集まり", "by": None, "days": {}, "planks": 0.0}
                    else:
                        g["posts"][r["人"]]["post"] = HEAD_K
                    if old and old in g["posts"] and g["posts"][old]["post"] == HEAD_K:
                        g["posts"][old]["post"] = SAW_K if w["tool"] == g15.SAW else HAM_K
                    log(state, "持ち場", r["人"], f"集まりで、{r['人']} を作業場 {r['輪']} の頭に選んだ (票 {txt})", mill=r["輪"], post=HEAD_K)
                    _reach(state, "F1", f"{r['人']} が {r['輪']} の頭になった")
    if part(state, "d"):
        vill = {}
        for name, a in sorted(real.items()):
            if not isinstance(a, dict):
                continue
            for what, n, to, side in _sell_rows(a.get("sell")):
                if side == "村":
                    vill[name] = json.dumps([what, n, to], ensure_ascii=False)
                elif hs.get(name):
                    sell(state, name, hs[name], what, n, to)
        if vill:
            ch, _ = g7._tally(state, vill, g7._vote_weights(state, real))
            if ch:
                what, n, to = json.loads(ch)
                who = sorted(k for k, v in vill.items() if v == ch)[0]
                sell(state, who, "村", what, n, to)


# ---------------- 年の終わり: 物差し ----------------

def season_end(state):
    """季節の終わり (g7.season_end。G15 の季節の終わりのあと): 蓄えのいちばん少ない日数 → 年の終わりなら行と物差し"""
    D = state["day"]
    if (D + 1) % SEASON_DAYS:
        return
    g = _g(state)
    y = str(D // YEAR)
    sd = era2.store_days(state)
    g["store_min"][y] = min(g["store_min"].get(y, sd), sd)
    if (D + 1) % YEAR == 0:
        year_end(state)


def row_of(state, y):
    g, g15g = _g(state), g15._g(state)
    ys = str(y)
    lr = next((r for r in g15g["ledger"] if r["year"] == y), None) or {}
    en = lr.get("energy") or {}
    dug = lr.get("coal_dug", 0)
    burned = lr.get("coal_burned", 0)
    ws = {}
    for mid, r in sorted((lr.get("ws") or {}).items()):
        ws[mid] = {"big": r.get("big", 0), "days": r.get("days", 0), "houses": len(r.get("houses") or {})}
    big = max((w["big"] for w in ws.values()), default=0)
    ch = g["chose"].get(ys) or {}
    share3 = round(ch.get("chose", 0) / ch["answerers"], 3) if ch.get("answerers") else 0.0
    done = [x for x in g["appr_done"] if x["year"] == y]
    rd = sum(1 for x in done if x["reader"])
    whole = sum(1 for r in g["posts"].values() if r["day"] < y * YEAR)  # 1 年じゅう持ち場の人 (この年のはじめより前についた・今もついている)
    ev = [e for e in state["events"] if e["day"] // YEAR == y]
    famine = sum(1 for e in ev if e["type"] == "蓄えが尽きる")
    pop = len([p for p in state["people"] if p["alive"]])
    prev = g["rows"].get(str(y - 1))
    pop_prev = prev["pop"] if prev else g["pop0"]
    smin = g["store_min"].get(ys, era2.store_days(state))
    f = g["fire"].get(ys) or {}
    sold = g["sold"].get(str(y)) or {}
    return {"year": y, "coal_dug": dug, "coal_burned": burned, "dug_share": round(min(1.0, dug / burned), 3) if burned else 0.0,
            "coal_share": en.get("coal_share", 0.0), "coal_stock": round(g15g["coal"]["stock"]), "house_coal": round(sum(g["hcoal"].values())),
            "house_burn": round(f.get("house_kg", 0)), "diggers": len((g["dug"].get(ys) or {})),
            "fire_pd": round(f.get("hours", 0) / PD_H), "saved_pd": round(f.get("saved_pd", 0) * FIRE_H / PD_H),
            "stoves": len(lr.get("stoves") or []), "ws": ws, "big": big,
            "posts": len(g["posts"]), "posts_by": {k: len([1 for r in g["posts"].values() if r["post"] == k]) for k in POSTS},
            "quit": sum(1 for q in g["quit"] if q["day"] // YEAR == y), "appr": len(g["appr"]), "appr_done": len(done), "appr_reader": rd,
            "answerers": ch.get("answerers", 0), "chose": ch.get("chose", 0), "wrote": ch.get("wrote", 0), "chose_share": share3, "posts_year": whole,
            "sold": {k: dict(v) for k, v in sold.items()}, "house_planks": round(sum(g["hplanks"].values()), 1), "planks": g15g["planks"]["stock"],
            "store_min": smin, "store_end": era2.store_days(state), "famine": famine, "pop": pop, "pop_prev": pop_prev, "pop0": g["pop0"],
            "readers": len(g10.readers(state)), "harvest": lr.get("harvest", 0),
            "e1_like": bool(burned and dug >= E1_DUG * burned and en.get("coal_share", 0) >= E1_SHARE),
            "e2_like": big >= E2_DAYS, "e3_like": share3 >= E3_SHARE,
            "e4_like": whole >= E4_N and len(done) >= E4_NEW,
            "e5_ok": famine == 0 and smin >= E5_STORE and pop >= E5_POP * g["pop0"]}


def _old0(state):
    """e1 の直し (2026-11-18): S3 に入る前からあった燃える石 (後押しの年までに掘った石) の kg。
    数えはじめの年の前の年の終わりの村の倉 (G15 の帳簿) から、印のあとその年に村の人が掘った分を引く (家の倉は印の日に 0)"""
    g = _g(state)
    p = g.get("e1pool") or {}
    if "old0" in p:
        return p["old0"]
    y0 = g["start_year"] - 1
    lr = next((r for r in g15._g(state)["ledger"] if r["year"] == y0), None) or {}
    return round(max(0.0, lr.get("coal_stock", 0) - sum((g["dug"].get(str(y0)) or {}).values())), 2)


def e1_pool(state, upto, last=None):
    """e1 の直し (2026-11-18): 年ごとに、燃やした石のうち、S3 に入ってから村の人が掘った石 (前の年に掘ってためた石も数える) の割合。
    前からあった石を先に出す (燃やした石、つぎに替えた石)。last: upto 年の行 (まだ rows にないとき)。
    戻り値: [{year, old_start, old_used, own_share, coal_share, like}] (state は変えない。前の年の数えなおしにも使う)"""
    g = _g(state)
    old, out = _old0(state), []
    for y in range(g["start_year"], upto + 1):
        r = last if (y == upto and last is not None) else g["rows"].get(str(y))
        if not r:
            continue
        burned = r.get("coal_burned", 0)
        sold = sum(v.get("燃える石", 0) for v in (r.get("sold") or {}).values())
        used = min(old, burned)
        own = round((burned - used) / burned, 3) if burned else 0.0
        out.append({"year": y, "old_start": round(old), "old_used": round(used), "own_share": own, "coal_share": r.get("coal_share", 0.0),
                    "like": bool(burned and own >= E1_DUG and r.get("coal_share", 0) >= E1_SHARE)})
        old = max(0.0, old - used - sold)
    return out


def year_end(state):
    g, D = _g(state), state["day"]
    y = D // YEAR
    if y < g["start_year"]:
        return
    r = row_of(state, y)
    if fixed(state):  # e1 の直し (2026-11-18): その年に掘った石でなく、S3 に入ってから掘ってためた石で燃やしたか (前の年の行と e_years は変えない)
        g.setdefault("e1pool", {"old0": _old0(state)})
        e = e1_pool(state, y, r)[-1]
        r["own_share"], r["e1_like"] = e["own_share"], e["like"]
    if ret(state):  # 作業場の返りの直し (2026-11-18 の 2 つめ): 板と手入れの数 (記録だけ。物差しは変えない)
        pk, ys = g15._g(state)["planks"], str(y)
        c13 = state["era2"]["g7"]["g13"]
        r.update({"planks_made": pk["made"].get(ys, 0), "planks_used": pk["used"].get(ys, 0), "planks_house_used": g.get("hused", {}).get(ys, 0),
                  "crew_extra": (g.get("crew", {}).get(ys) or {}).get("extra", 0),
                  "canal_dug": c13["canal"]["dug"].get(ys, 0), "canal_left": round(canal_left(state, y)), "mill_repair": c13["mill"]["repair"].get(ys, 0.0)})
    g["rows"][str(y)] = r
    for k in ("e1", "e2", "e3", "e4"):
        if r[f"{k}_like"] and y not in g["e_years"][k]:
            g["e_years"][k].append(y)
        if k not in g["e"] and all((y - i) in g["e_years"][k] for i in range(2)):
            g["e"][k] = D
    if not r["e5_ok"] and y not in g["e5_broken"]:
        g["e5_broken"].append(y)


def entrance(state):
    g = _g(state)
    e = g["e"]
    if not ("e1" in e and "e2" in e and ("e3" in e or "e4" in e)):
        return False
    if state["day"] >= ENTRANCE_DAY and g.get("rows"):
        ymax = max(int(k) for k in g["rows"])
        return not any(b >= ymax - PATH_YEARS + 1 for b in g["e5_broken"])
    return not g["e5_broken"]


def more_refusal(state, words, years):
    """resume --s3more ができないわけ (できるなら None)"""
    if not on(state):
        return "Society 3.0 の印がない"
    h = state["era2"]["g7"].get("hold") or {}
    if h.get("why") != "entrance" or not str(h.get("what", "")).startswith("S3:"):
        return "S3 の入口 (HOLD entrance) で止まっていない"
    if _g(state).get("more"):
        return "もう一度つけた (1 回だけ)"
    if not str(words).strip():
        return "本人の言葉がない"
    if not (1 <= years <= 10):
        return "年の数は 1〜10"
    return None


def mark_more(state, words, years):
    """S3 の入口から、そのまま years 年確かめる印 (g7.s3.more)。止めるのは until_day の年の終わり"""
    D = state["day"]
    y0 = D // YEAR  # いまいる年 (季節の途中なら、その年も数える)
    m = {"day": D, "words": words, "why": f"そのまま確かめる (本人の言葉 2026-11-18 「{words}」)", "years": years, "from_year": y0, "to_year": y0 + years - 1,
         "until_day": (y0 + years) * YEAR - 1}
    _g(state)["more"] = m
    return m


def check(state, done):
    """g7.check から (年の終わりと季節の終わり): 止まるわけ (なければ None)。G15 の相談のかわり"""
    g, D = _g(state), state["day"]
    if (D + 1) % SEASON_DAYS:
        return None
    mo = g.get("more")
    if mo and D >= mo["until_day"] and not any(c["why"] == "s3_more_end" for c in done):
        return {"why": "s3_more_end", "day": D, "text": f"S3: 入口のあと、そのまま確かめた {mo['years']} 年 ({mo['from_year']}年〜{mo['to_year']}年) が終わった。この先を本人と相談する"}
    if (D + 1) % YEAR:
        if D > ENTRANCE_DAY and entrance(state) and not any(c["why"] == "s3_entrance" for c in done):
            return {"why": "s3_entrance", "day": D, "text": f"S3: 入口に着いた ({'・'.join(f'{k} {_yd(v)}' for k, v in sorted(g['e'].items()))}。数えた 2 年に e5 を割らなかった)"}
        rd = g10.readers(state)
        if len(rd) <= g15.READERS_STOP and not any(c["why"] == f"s3_readers_{len(rd)}" for c in done):
            return {"why": f"s3_readers_{len(rd)}", "day": D, "text": f"S3: 読める大人が {len(rd)} 人になった"}
        return None
    y = D // YEAR
    if y < g["start_year"]:
        return None
    r = g["rows"].get(str(y)) or {}
    if entrance(state) and not any(c["why"] == "s3_entrance" for c in done):
        return {"why": "s3_entrance", "day": D, "text": f"S3: 入口に着いた ({'・'.join(f'{k} {_yd(v)}' for k, v in sorted(g['e'].items()))}。そのあいだ e5 を割らなかった)"}
    if r and not r["e5_ok"] and not any(c["why"] == "s3_e5" and c.get("year") == y for c in done):
        return {"why": "s3_e5", "year": y, "day": D, "text": f"S3: {y}年に e5 (暮らしを守る) を割った (ききん {r['famine']}・蓄えのいちばん少ない日 {r['store_min']} 日分・人 {r['pop']} (はじめ {r['pop0']} の {round(E5_POP * 100)}% は {math.ceil(E5_POP * r['pop0'])}))"}
    ys = [g["rows"].get(str(y - i)) for i in range(PATH_YEARS)]
    if all(x and x["chose"] == 0 for x in ys) and not any(c["why"] == "s3_path" and c.get("year") == y for c in done):
        return {"why": "s3_path", "year": y, "day": D, "text": f"S3: 作業場か掘る仕事を選ぶ答える人が {PATH_YEARS} 年つづけて 0 人"}
    if r and g15._g(state)["coal"]["stock"] < 1 and r["coal_dug"] == 0 and not any(c["why"] == "s3_coal" for c in done):
        return {"why": "s3_coal", "year": y, "day": D, "text": f"S3: 村の倉の燃える石が尽きて、{y}年はだれも掘らなかった"}
    n = y - g["start_year"] + 1
    if n > 0 and n % LATER_YEARS == 0 and not any(c["why"] == f"s3_years_{y}" for c in done):
        return {"why": f"s3_years_{y}", "day": D, "text": f"S3: Society 3.0 に入って {n} 年たった (5 年ごとの相談)"}
    return None


def _reach(state, f, why):
    g = _g(state)
    if f in g["reached"]:
        return
    g["reached"][f] = state["day"]


# ---------------- お題 (g15.prompt_block の中。短く) ----------------

def coal_lines(state, p):
    """g15.coal_line のかわり (a のとき)"""
    g, g15g = _g(state), g15._g(state)
    h = p.get("household")
    n = len([x for x in g15g["stoves"] if g15.stove_done(state, x)])
    if fixed(state):  # 直し (2026-11-18): 今いる家だけを数える (なくなった家の石のかまどを数えない)。まきのかまどの家の数も出す
        hs = era2._homes(state)
        n = len([x for x in hs if g15.stove_done(state, x)])
        nw = len(hs) - n
    mine = "石のかまど" if h and g15.stove_done(state, h) else (f"石のかまどに作りかえている途中" if h in g15g["stoves"] else "まきのかまど")
    vill = g15g["coal"]["stock"]
    per = burn_per_day(state)
    end = runout(state, vill + sum(g["hcoal"].values()), per)
    if coal_fixed(state):  # 直し (2026-11-19): 村の倉は、村の倉から燃やす分だけで尽きる日を出す (家の倉の石は、その家しか燃やさない)
        per, nv = vill_draw(state)
        end = runout(state, vill, per)
    rows = [f"- 燃える石: 北の丘で掘ると 1 人 1 日 約 {g15.COAL_KG_DAY} kg (主な仕事「{g15.ACT_DIG}」)。そのうち {round(g15.COAL_KG_DAY * HOUSE_SHARE)} kg は掘った人の家の倉に入り、"
            f"その家が先に燃やす。かまどを石のかまどに作りかえるのは「{g15.ACT_STOVE}」(家の大人で {g15.STOVE_DAYS} 人日)。",
            f"  まき集め: 秋と冬は、まきで火をたく人 1 人につき 1 日 約 {FIRE_H} 時間、家の大人の働く時間がへる。"
            f"燃える石 {g15.COAL_KG_DAY} kg (掘る 1 人日) を秋と冬に燃やすと、まき集め 約 {dig_saves_pd()} 人日が浮く。"]
    ys = str(_y(state) - 1) if str(_y(state)) not in g["fire"] else str(_y(state))
    if coal_fixed(state):  # 直し (2026-11-19): 今年の家ごとのまき集めがまだなければ (秋の集まり)、去年の数
        ys = str(_y(state)) if "house" in (g["fire"].get(str(_y(state))) or {}) else str(_y(state) - 1)
    fh = ((g["fire"].get(ys) or {}).get("house") or {}).get(h)
    hc = g["hcoal"].get(h, 0)
    hend = runout(state, hc, burn_per_day(state, h)) if h and g15.stove_done(state, h) else None
    t = (f"  あなたの家 ({h}) は{mine}" + (f"。{ys}年のまき集め 約 {round(fh)} 人日" if fh else "")
         + f"。家の倉の燃える石 {round(hc)} kg" + (f" ({_yd(hend)}ごろまで)" if hend and hc else "") + "。")
    if coal_fixed(state) and per > 0 and vill < per:  # 直し (2026-11-19): もう尽きているときは、まきをたく石のかまどの家の数
        t += f"村の倉 {round(vill)} kg (もう尽きた。家の倉に石のない石のかまどの家 {nv} は、まきをたく)"
    else:
        t += f"村の倉 {round(vill)} kg" + (f" (このままなら {_yd(end)}ごろに尽きる)" if end else "")
    t += f"・石のかまどの家 {n}" + (f" (まきのかまどの家 {nw})" if fixed(state) else "")
    dg = g["dug"].get(str(_y(state))) or g["dug"].get(str(_y(state) - 1)) or {}
    if dg:
        top = sorted(dg, key=lambda k: (-dg[k], k))[:4]
        t += f"・近ごろ掘った人 {'・'.join(top)}"
    rows.append(t)
    return rows


def block_lines(state, p):
    """持ち場・見習い・交換の行 (b・c・d のとき)。短く"""
    g, g15g = _g(state), g15._g(state)
    name, h = p["name"], p.get("household")
    rows = plank_lines(state, p)
    done = [m for m in g15.workshops(state, done=True)]
    if (part(state, "b") or part(state, "c")) and done:
        ps = "・".join(f"{m} ({g15g['ws'][m]['tool']}): 持ち場 {len(posts_of(state, m))} 人" + (f"・頭 {g['head'][m]['name']}" if g["head"].get(m) else "")
                      + (f"・帳面番 {'・'.join(posts_of(state, m, LEDGER_K))}" if posts_of(state, m, LEDGER_K) else "") for m in done)
        rows.append(f"- 作業場の持ち場: {ps}。持ち場の人は、やめると答えるまで、季節ごとに作業場で働く (のこ番がひいた板の 2 割は家の板になる)。"
                    if part(state, "b") else f"- 作業場の持ち場: {ps}。持ち場の人は、やめると答えるまで、季節ごとに作業場で働く。")
        r = g["posts"].get(name)
        if r:
            y = str((state["day"] + 1) // YEAR - 1) if fixed(state) else str(_y(state) - 1)  # 直し (2026-11-18): 年の集まり (年の終わりの日) でも、終わった年の日を出す
            rows.append(f"  あなたは {r['mill']} の{r['post']}。{y}年に {r['days'].get(y, 0)} 日働いた" + (f"・家にもどった板 {int(r['planks'])} 束" if r["planks"] >= 1 else ""))
        fam = [q["name"] for q in era2.adults(state) if h and q.get("household") == h and q["name"] in g["posts"] and q["name"] != name]
        if fam:
            rows.append(f"  あなたの家の持ち場: " + "・".join(f"{n} ({g['posts'][n]['mill']} の{g['posts'][n]['post']})" for n in fam[:4]))
        if part(state, "b"):
            rd = [n for n in g10.readers(state) if _house_of(state, n) == h]
            ex = {"人": name, "持ち場": SAW_K if g15g["ws"][done[0]]["tool"] == g15.SAW else HAM_K, "輪": done[0]}
            rows.append(f"  持ち場につく・やめる (post。自分か家の大人): 例 [{json.dumps(ex, ensure_ascii=False)}]・やめるは [{{\"人\": \"{name}\", \"やめる\": true}}]。"
                        f"{LEDGER_K}は読める大人" + (f" (あなたの家の {'・'.join(rd[:3])})" if rd else "") + f"。頭は集まりで選ぶ (head: {{\"輪\": \"{done[0]}\", \"人\": 名前}})")
    if part(state, "c") and done:
        a = g["appr"].get(name)
        sw = [n for m in done for n in posts_of(state, m, SAW_K) if sawyer(state, n, m)] if ret(state) else []
        who = "帳面番か読める大人か黒い金属の腕のある人" + (f"か、{TEACH_SAW_DAYS} 日以上働いたのこ番" if ret(state) else "")
        rows.append(f"- 見習い: 作業場で、{who}と同じ日に {APPR_DAYS} 日働くと、見習いを終えて持ち場 (のこ番・槌番) につく"
                    + (f" (いま教えられるのこ番: {'・'.join(sw[:4])})" if sw else "")
                    + (f"。あなたは見習い {a['days']} 日目 ({a['mill']})" if a else ""))
    if part(state, "d"):
        pts = partners(state)
        pr = []
        for pt in pts:
            xs = []
            for what in ("板", "燃える石"):
                unit, gets = pt["price"][what]
                gw = "・".join(f"{k} {v}{' 頭' if k == 'ヤギ' else ' つかみ'}" for k, v in gets.items())
                xs.append(f"{what} {unit}{' 束' if what == '板' else ' kg'} = {gw} (今年あと {left(state, pt, what)})")
            pr.append(f"{pt['name']} ({pt['id']}) " + "・".join(xs))
        rows.append("- 交換 (sell): 板と燃える石を替えられる。" + " / ".join(pr))
        rows.append(f"  あなたの家の板 {int(g['hplanks'].get(h, 0))} 束・燃える石 {int(g['hcoal'].get(h, 0))} kg。村の倉の板 {g15g['planks']['stock']} 束。"
                    f"書き方 \"sell\": [{{\"物\": \"板\", \"数\": 10, \"相手\": \"{pts[0]['id']}\", \"から\": \"家\"}}] (村の倉の物は \"から\": \"村\"。答えた人のいちばん多い中身)")
    return rows


def _house_of(state, name):
    p = _adult(state, name)
    return p.get("household") if p else None


def field_rows(state, year=False):
    out = []
    if part(state, "b"):
        out.append("   post: 持ち場につく・やめる (自分か家の大人)。例 [{\"人\": 名前, \"持ち場\": \"のこ番\", \"輪\": \"M6\"}]。head: 作業場の頭 {\"輪\", \"人\"}")
    if part(state, "d"):
        out.append("   sell: 板と燃える石の交換。例 [{\"物\": \"板\", \"数\": 10, \"相手\": \"町\", \"から\": \"家\"}]")
    return out


ANSWER_FIELDS = {"post": "[]", "head": "null", "sell": "[]"}


def answer_fields(state):
    out = []
    if part(state, "b"):
        out += ["post", "head"]
    if part(state, "d"):
        out.append("sell")
    return out


# ---------------- step.py status・決まりの村の行 (村の人のお題には出さない) ----------------

def row_text(r):
    ws = "・".join(f"{m} {w['big']} 日" for m, w in r["ws"].items()) or "なし"
    sold = "・".join(f"{k} " + "・".join(f"{kk} {vv}" for kk, vv in v.items()) for k, v in r["sold"].items()) or "なし"
    return (f"{r['year']}年: 掘った {round(r['coal_dug'])} kg ({r['diggers']} 人)・燃やした {round(r['coal_burned'])} kg (掘った分 {round(r['dug_share'] * 100)}%)・"
            f"火と力の {round(r['coal_share'] * 100, 1)}%・村の倉 {r['coal_stock']} kg・家の倉 {r['house_coal']} kg / まき集め {r['fire_pd']} 人日 (浮いた {r['saved_pd']}) / "
            f"作業場の 8 人の日 {ws} / 持ち場 {r['posts']} (1 年じゅう {r.get('posts_year', '-')}・やめた {r['quit']})・見習い 終えた {r['appr_done']} (読める人が教えた {r['appr_reader']})・途中 {r['appr']} / "
            + (f"S3 からの石の分 {round(r['own_share'] * 100)}% / " if "own_share" in r else "") +
            (f"板 ひいた {r['planks_made']} (人の多い日の足し {r['crew_extra']})・使った {r['planks_used']} (家の板 {r['planks_house_used']})・水の道 掘った {r['canal_dug']} 人日 (手入れの残り {r['canal_left']}) / " if "planks_made" in r else "") +
            f"選んだ答える人 {r['chose']} (書いた {r.get('wrote', '-')}) / {r['answerers']} / 交換 {sold} / 蓄え いちばん少ない {r['store_min']} 日分・ききん {r['famine']}・人 {r['pop_prev']} → {r['pop']} (はじめ {r.get('pop0', '-')}) / "
            + " ".join(f"{k} {'○' if r[f'{k}_like'] else '×'}" for k in ("e1", "e2", "e3", "e4")) + f" e5 {'○' if r['e5_ok'] else '×'}")


def lines(state):
    if not on(state):
        return []
    g = _g(state)
    out = [f"{g['why']}。{g['day']} 日目から ({g['start_year']}年から数える)。部分: " + "・".join(f"{k} {PARTS[k]}" for k in g["parts"])
           + f"。入口 " + " / ".join(f"{k} {ES[k]} {_yd(g['e'][k]) if k in g['e'] else 'まだ'}" for k in ("e1", "e2", "e3", "e4"))
           + f" / e5 を割った年 {'・'.join(map(str, g['e5_broken'])) or 'なし'} / F {'・'.join(sorted(g['reached'])) or 'まだ'}"]
    for y in sorted(g["rows"], key=int)[-3:]:
        out.append(row_text(g["rows"][y]))
    return out
