"""Society 3.0 フェーズ 4「頼み書きと町」(2026-11-21。docs/society_phase/P4_design.md・P4_check.md)

- 印 state.era2.g7.p4 があるときだけ働く。印を書くのは step.py resume --p4 "<本人の言葉>" だけ
  (i4 のあと、27839 日目 (231年の終わり) から。i4 の相談で止まっているときか、止まりがないとき。1 回だけ)。
  印がなければ、このファイルは読みこみもしない (g7・step.py・tools/year_report.py は「p4」の鍵があるときだけ、関数の中で読みこむ)。
  だから前の歩は、お題・state・出来事・乱数が 1 バイトも変わらない
- 印を書くと g7.i4.closed も書く (i4 の入口・相談を止める。知らせ板・手習い・i4 の年の行・読める大人が 1 人以下の止まりはそのまま)
- 時代 (state.era) は G15 のまま。G15・S3・S4・i4 の世界の仕組みはそのまま動き、その上に 2 つの部分を足す:
  a 頼み書き: 家に読める大人がいる家は、知らせ板に「燃える石 N kg (か 板 N 束) がほしい。かわりに 〇〇」と書ける (答えの欄 order)。
    かわりの物は、書いたときに家の倉から預けに分ける。手間 (人日) のかわりは、家の大人の数 × 10 日まで。
  b 約束の帳: ほかの家 (家に読める大人がいる家) が受ける (答えの欄 take)。家の倉にあれば受けた日に渡す。足りない分は、名を書いた大人 (4 人まで) が、
    季節のはじめから 1 人 1 季節 10 日まで、頼みの仕事 (燃える石を掘る・水の作業場で働く) をして、できた物は頼んだ家の倉に入る。
    期限は受けた季節と次の季節。果たしたら預けは受けた家へ、手間なら頼んだ家の大人が、次の季節のはじめから、受けた家の人のいつもの食べ物の仕事をする
- 乱数は使わない。後押しはしない。印・本人の言葉・「作る側」・物差しのことは、村の人のお題にも出来事にも書かない
- 物差し (P4_design.md 4.): p1 果たした頼み 4 件以上 (頼んだ家 2・受けた家 2)・p2 よその家の頼みで 30 人日以上働いた家 2 以上・
  p3 食べ物でない仕事 22% 以上 (守り)・p4 暮らしを守る (ききんなし・蓄え 120 日分・人は印のときの 95%・読める大人 15%)。
  入口は p1 と p2 が 2 年つづき、その 2 年に p3 と p4 を割らない。止めて相談: p4 を割った年・頼みを書いた家と受けた家が 2 年 0・3 年ごと
"""
import copy
import json
import math

import era2
import g10
import g15
from world import log, season

YEAR, SEASON_DAYS = era2.YEAR, era2.SEASON_DAYS
P4_FROM = 27839  # 本物の村が 231年を終えた日。これより前には印を書けない
P4_DATE = "2026-11-21"
P4_NAME = "Society 3.0 フェーズ 4 (頼み書きと町)"
PARTS = {"a": "頼み書き (燃える石か板がほしい家が、知らせ板に書く。かわりの物は預けに分ける)",
         "b": "約束の帳 (ほかの家が受けて、季節の数日だけ働き、できた物を渡す。手間返し)"}
SRC = "頼みの仕事"  # 記録の呼び名 (帳と年報。g7.src には書かない。P4_check.md 5.)
EV = "頼み書き"  # 出来事の種類
# a 頼み書き【仮定】
WANTS = {"燃える石": (500, 10000, "kg"), "板": (10, 200, "束")}
PAYS = ("手間", "草の種", "燃える石", "板")
PAY_UNIT = {"手間": "人日", "草の種": "つかみ", "燃える石": "kg", "板": "束"}
TEMA_PER_ADULT = 10
OPEN_MAX = 2  # まだ受けられていない頼みは 1 家 2 枚まで
BOARD_MAX = 8  # 板にのる頼みの枚数 (新しいほうから)
LIFE = YEAR  # 受けられないまま 4 季節たつと消える
# b 約束の帳【仮定】
DAYS_MAX = 10  # 1 人 1 季節の頼みの仕事の日
WORKERS_MAX = 4
DUE_SEASONS = 2  # 受けた季節と次の季節
STORE_STOP = 120  # 村の蓄えがこの日数を切った季節は、頼みの仕事をしない
FOOD_JOBS = ("畑仕事", "ヤギの世話", "水の道を掘る")  # 手間返しでかわりにする「いつもの食べ物の仕事」(キャンプでできる仕事だけ)
FOOD_LAST = "畑仕事"
# 物差し【仮定】(P4_design.md 4.)
P1_DONE, P1_HOUSES = 4, 2
P2_DAYS, P2_HOUSES = 30, 2
P3_SHARE = 0.22
P4_STORE, P4_POP, P4_READERS = 120, 0.95, 0.15
P_YEARS = 2
ZERO_YEARS = 2
LATER_YEARS = 3
PS = {"p1": "果たした頼み", "p2": "よその家のために働く家", "p3": "食べ物でない仕事 (守り)", "p4": "暮らしを守る"}
FS = {"F1": "はじめての頼み書き", "F2": "はじめて頼みを受けた", "F3": "はじめて果たした", "F4": "はじめて 30 人日の家"}
SECTION = "## 村の知らせ板"  # お題の節の見出し (tools/prompt_check.py --words p4 が読む。i4 の節の中に足す)
FACT_HEADS = ()
# 村の人に見せる文 (知らせ板の節) に書かない言葉 (tools/prompt_check.py --words p4・T_P4 で確かめる)
WORDS = ("作る側", "後押し", "反実仮想", "印", "物差し", "入口", "Society", "本人", "P4", "I4", "S4", "p1", "p2", "p3", "p4", "分業", "町の芽")


def on(state):
    return "day" in (((state.get("era2") or {}).get("g7") or {}).get("p4") or {})


def _g(state):
    return state["era2"]["g7"]["p4"]


def _i4():
    import i4
    return i4


def _s3():
    import s3
    return s3


def _s4():
    import s4
    return s4


def _yd(day):
    return f"{day // YEAR}年{day % YEAR + 1}日目"


def _sl(day):
    return f"{day // YEAR}年{season(day)}"


def _adult(state, name):
    return next((p for p in era2.adults(state) if p["name"] == name), None)


def _house_of(state, name):
    p = next((q for q in state["people"] if q["name"] == name), None)
    return p.get("household") if p else None


def _house_adults(state, h):
    return sorted(p["name"] for p in era2.adults(state) if h and p.get("household") == h)


def _fail(state, who, what, why):
    """選んだのにできなかったこと (帳面 g7.p4.fails。お題の知らせ板の節の「頼み書きで、できなかったこと」に出す。出来事には残さない)"""
    g, D = _g(state), state["day"]
    g["fails"] = (g["fails"] + [{"day": D, "year": (D + 1) // YEAR, "who": who, "house": _house_of(state, who), "what": what, "why": why}])[-40:]


def _yr(state, y):
    return _g(state)["yr"].setdefault(str(y), {"wrote": [], "took": [], "done": 0, "failed": 0, "gone": 0, "coal_dug": 0.0, "planks_made": 0.0,
                                               "coal_moved": 0.0, "planks_moved": 0.0, "back_days": 0, "pd": {}, "used": 0, "food_first": 0})


_MEET = [False]  # 集まりの答えを読んでいるあいだ (apply_answers) は True。その日のことは次の暦の年に数える (答えが効く年。i4 の知らせと同じ)


def _ay(state):
    """帳の年: 集まりの日 (季節の最後の日) に答えで起きたことは次の年、季節の日々と季節の終わりはその日の年"""
    D = state["day"]
    return (D + 1) // YEAR if _MEET[0] else D // YEAR


def _reach(state, f, why):
    g = _g(state)
    if f not in g["f"]:
        g["f"][f] = state["day"]
        g.setdefault("f_why", {})[f] = why


# ---------------- 印 (step.py resume --p4) ----------------

def why_text(words):
    return f"{P4_NAME} (本人の言葉 {P4_DATE} 「{words}」)"


def refusal(state, words):
    """resume --p4 ができないわけ (できるなら None)"""
    if not (words or "").strip():
        return "--p4 には本人の言葉が要る"
    g7s = ((state.get("era2") or {}).get("g7") or {})
    if "i4" not in g7s or not _i4().on(state):
        return "i4 の印がないので、P4 は始められない"
    if "p4" in g7s:
        return "P4 はもう始めてある"
    if state["day"] < P4_FROM:
        return f"P4 は {P4_FROM} 日目 (231年の終わり) からだけ"
    h = g7s.get("hold") or {}
    if state.get("hold") or h:
        if not (h.get("why") == "consult" and str(h.get("what", "")).startswith("I4:")):
            return "P4 は、I4 の相談で止まっているときか、止まりのないときだけ始める"
    if g15.push_on(state):
        return "後押しが動いている"
    return None


def mark(state, words):
    """resume --p4 から: 印 g7.p4 を書き、g7.i4.closed を書く (村の出来事には残さない)"""
    words = words.strip()
    D = state["day"]
    _i4()._g(state)["closed"] = D
    ads = era2.adults(state)
    g = state["era2"]["g7"]["p4"] = {
        "day": D, "words": words, "why": why_text(words), "parts": list(PARTS), "start_year": D // YEAR + 1,
        "pop0": len([p for p in state["people"] if p["alive"]]), "adults0": len(ads), "readers0": len(g10.readers(state)),
        "orders": [], "book": [], "gone": [], "next_id": 1, "work": {}, "back_now": {}, "yr": {}, "chose": {}, "fails": [],
        "rows": {}, "f": {}, "f_years": {k: [] for k in ("p1", "p2")}, "p4_broken": [], "store_min": {}}
    return g


# ---------------- 家の倉 (燃える石・板は S3 の家の倉。草の種は家の倉の食べ物) ----------------

def have(state, h, k):
    s3g = _s3()._g(state)
    if k == "燃える石":
        return int(s3g["hcoal"].get(h, 0))
    if k == "板":
        return int(s3g["hplanks"].get(h, 0))
    if k == "草の種":
        return era2._g6_have(state, h, "草の種") if h in era2._homes(state) else 0
    return 0


def take_goods(state, h, k, n):
    """家 h の倉から k を n 出す (足りなければある分だけ)。戻り値: 出した数"""
    s3g = _s3()._g(state)
    if k in ("燃える石", "板"):
        key = "hcoal" if k == "燃える石" else "hplanks"
        n = min(n, s3g[key].get(h, 0))
        if n > 0:
            s3g[key][h] = round(s3g[key][h] - n, 2)
        return max(0, n)
    if k == "草の種":
        return era2._g6_take(state, h, {"草の種": int(n)}).get("草の種", 0)
    return 0


def put_goods(state, h, k, n):
    s3g = _s3()._g(state)
    if n <= 0:
        return
    if k in ("燃える石", "板"):
        key = "hcoal" if k == "燃える石" else "hplanks"
        s3g[key][h] = round(s3g[key].get(h, 0) + n, 2)
    elif k == "草の種":
        era2._g6_put(state, h, {"草の種": int(n)})


# ---------------- a 頼み書き ----------------

def _obj(v):
    if isinstance(v, str):
        s = v.strip()
        if not s or s.lower() in ("null", "none", "なし"):
            return None
        try:
            v = json.loads(s)
        except ValueError:
            return "bad"
    if v is None or v is False or v == {}:
        return None
    return v if isinstance(v, dict) else "bad"


def parse_order(v):
    """答えの order を読む。戻り値: None (書かない) / 文 (書けないわけ) / {want, n, pay, pn}"""
    v = _obj(v)
    if v is None:
        return None
    if v == "bad":
        return "書き方がちがう (例の形で書く)"
    want = str(v.get("ほしい") or v.get("want") or "").strip()
    if want in era2.FOOD_KCAL or want in ("食べ物", "乳", "肉", "ヤギ"):
        return "食べ物は頼めない (頼めるのは燃える石と板だけ)"
    if want not in WANTS:
        return "頼めるのは燃える石と板だけ"
    n = era2._num(v.get("数") if v.get("数") is not None else v.get("n"))
    lo, hi, unit = WANTS[want]
    if not lo <= n <= hi:
        return f"{want}は {lo}〜{hi} {unit}で書く"
    pay = v.get("かわり") if v.get("かわり") is not None else v.get("pay")
    if not isinstance(pay, dict) or len([k for k in pay if pay[k] not in (None, 0, "")]) != 1:
        return "かわりの物は 1 つだけ書く (手間・草の種・燃える石・板)"
    k = next(k for k in pay if pay[k] not in (None, 0, ""))
    if k not in PAYS:
        return "かわりの物は 手間・草の種・燃える石・板 のどれか"
    pn = era2._num(pay[k])
    if pn < 1:
        return "かわりの数がない"
    if k == want:
        return "ほしい物と同じ物はかわりにできない"
    return {"want": want, "n": n, "pay": k, "pn": pn}


def board_now(state):
    """いま板にのっている (まだ受けられていない) 頼み (新しい順。BOARD_MAX 枚まで)"""
    return list(_g(state)["orders"])[-BOARD_MAX:][::-1]


def open_of(state, h):
    return [o for o in _g(state)["orders"] if o["house"] == h]


def owed(state, h):
    """家 h が、まだ返していない手間 (人日)"""
    return sum(b["back"]["need"] - b["back"]["done"] for b in _g(state)["book"] if b["house"] == h and b.get("back") and b["back"]["done"] < b["back"]["need"])


def order_why(state, name, h, o):
    """頼みを書けないわけ (書けるなら None)"""
    i4 = _i4()
    D = state["day"]
    if not i4.house_readers(state, h):
        return "家に字を書ける人がいないので、頼み書きは書けなかった"
    if any(x["house"] == h and x.get("day") == D for x in _g(state)["orders"] + _g(state)["book"]):
        return "家がこの季節にもう 1 枚書いたので、書かなかった (1 家 1 季節 1 枚)"
    if len(open_of(state, h)) >= OPEN_MAX:
        return f"まだ受けられていない頼みが {OPEN_MAX} 枚あるので、書けなかった"
    if owed(state, h):
        return f"手間をまだ {owed(state, h)} 人日返していないので、新しい頼みは書けなかった"
    if o["pay"] == "手間":
        cap = len(_house_adults(state, h)) * TEMA_PER_ADULT
        if o["pn"] > cap:
            return f"手間は家の大人の数 × {TEMA_PER_ADULT} ({cap} 人日) までしか書けない"
    elif have(state, h, o["pay"]) < o["pn"]:
        return f"家の倉の{o['pay']}が {o['pn']} {PAY_UNIT[o['pay']]}に足りないので、預けられず、書けなかった"
    return None


def _drop(state, o, why):
    """板から頼みを消し、預けを家にもどす"""
    g = _g(state)
    g["orders"] = [x for x in g["orders"] if x["id"] != o["id"]]
    if o["pay"] != "手間" and o.get("escrow"):
        put_goods(state, o["house"], o["pay"], o["escrow"])
        o["escrow"] = 0
    o["status"], o["end"], o["end_y"], o["end_why"] = "消えた", state["day"], _ay(state), why
    g["gone"] = (g["gone"] + [o])[-40:]
    _yr(state, _ay(state))["gone"] += 1


def write_orders(state, real):
    g, D = _g(state), state["day"]
    i4 = _i4()
    y = (D + 1) // YEAR
    for name, a in sorted(real.items()):
        if not isinstance(a, dict) or a.get("order") is None:
            continue
        o = parse_order(a.get("order"))
        if o is None:
            continue
        if isinstance(o, str):
            _fail(state, name, "頼み書き", f"{name} の頼み書きは、{o}")
            continue
        h = _house_of(state, name)
        why = order_why(state, name, h, o)
        if why:
            _fail(state, name, "頼み書き", f"{name} の頼み書きは、{why}")
            continue
        esc = take_goods(state, h, o["pay"], o["pn"]) if o["pay"] != "手間" else 0
        hr = i4.house_readers(state, h)
        r = {"id": g["next_id"], "day": D, "year": y, "season": _sl(D + 1), "house": h, "by": name, "writer": hr[0], "want": o["want"], "n": o["n"],
             "pay": o["pay"], "pn": o["pn"], "escrow": esc, "status": "板"}
        g["next_id"] += 1
        g["orders"].append(r)
        while len(g["orders"]) > BOARD_MAX:
            _drop(state, g["orders"][0], "板がいっぱいで、古い頼みから消えた")
        i4._g(state).setdefault("pending", []).append({"writer": hr[0], "house": h})  # 書く日は知らせと同じ (i4 の「知らせを書く」の 1 日)
        _chose(state, y, name)
        yr = _yr(state, y)
        if h not in yr["wrote"]:
            yr["wrote"].append(h)
        _reach(state, "F1", f"{h}の {name} が、頼み {r['id']} ({o['want']} {o['n']} {WANTS[o['want']][2]}) を書いた")


def _chose(state, y, name):
    row = _g(state)["chose"].setdefault(str(y), [])
    if name not in row:
        row.append(name)


# ---------------- b 約束の帳 ----------------

def parse_take(v):
    v = _obj(v)
    if v is None:
        return None
    if v == "bad":
        return "書き方がちがう (例の形で書く)"
    oid = era2._num(v.get("頼み") if v.get("頼み") is not None else v.get("id"))
    if not oid:
        return "頼みの番号がない"
    ppl = v.get("人") if v.get("人") is not None else v.get("people")
    ppl = [ppl] if isinstance(ppl, str) else (ppl if isinstance(ppl, list) else [])
    return {"id": oid, "people": [str(x).strip() for x in ppl if str(x).strip()]}


def take_orders(state, real):
    g, D = _g(state), state["day"]
    i4 = _i4()
    y = (D + 1) // YEAR
    for name, a in sorted(real.items()):
        if not isinstance(a, dict) or a.get("take") is None:
            continue
        t = parse_take(a.get("take"))
        if t is None:
            continue
        if isinstance(t, str):
            _fail(state, name, "受ける", f"{name} の受ける答えは、{t}")
            continue
        h = _house_of(state, name)
        o = next((x for x in g["orders"] if x["id"] == t["id"]), None)
        if not i4.house_readers(state, h):
            _fail(state, name, "受ける", f"{name} は、家に字の読める人がいないので、頼み {t['id']} を受けられなかった")
            continue
        if o is None:
            done = next((x for x in g["book"] if x["id"] == t["id"]), None)
            _fail(state, name, "受ける", f"{name} が受けようとした頼み {t['id']} は、" + (f"もう{done['taker']}が受けていた" if done else "板になかった"))
            continue
        if o["house"] == h:
            _fail(state, name, "受ける", f"{name} は、自分の家の頼み {t['id']} は受けられない")
            continue
        mine = set(_house_adults(state, h))
        ws = []
        for n in t["people"]:
            if n in mine and n not in ws:
                ws.append(n)
            elif n not in mine:
                _fail(state, name, "受ける", f"{n} は {name} の家の大人でないので、頼み {t['id']} の人に入れなかった")
        ws = ws[:WORKERS_MAX]
        stock = min(have(state, h, o["want"]), o["n"])
        if not ws and stock < o["n"]:
            _fail(state, name, "受ける", f"{name} は、頼み {t['id']} の仕事をする人を書かなかったので、受けられなかった")
            continue
        g["orders"] = [x for x in g["orders"] if x["id"] != o["id"]]
        o.update({"status": "受けた", "taker": h, "taker_by": name, "workers": ws, "taken": D, "due": D + DUE_SEASONS * SEASON_DAYS,
                  "made": 0.0, "stock": 0.0, "days": {}, "pd": 0, "dug": 0.0, "food_first": []})
        g["book"].append(o)
        log(state, EV, name, f"{h}の {name} が、{o['house']}の頼み ({o['want']} {o['n']} {WANTS[o['want']][2]}) を受けた", order=o["id"], household=h)
        _chose(state, y, name)
        yr = _yr(state, y)
        if h not in yr["took"]:
            yr["took"].append(h)
        _reach(state, "F2", f"{h}の {name} が、{o['house']}の頼み {o['id']} を受けた")
        if stock > 0:
            got = take_goods(state, h, o["want"], stock)
            _deliver(state, o, got, stock=True)


def _need(o):
    return round(o["n"] - o["made"], 2)


def _deliver(state, o, n, stock=False):
    """できた物 n を頼んだ家の倉へ。頼みの分になったら果たす"""
    if n <= 0:
        return
    put_goods(state, o["house"], o["want"], n)
    o["made"] = round(o["made"] + n, 2)
    if stock:
        o["stock"] = round(o["stock"] + n, 2)
    yr = _yr(state, _ay(state))
    yr["coal_moved" if o["want"] == "燃える石" else "planks_moved"] = round(yr["coal_moved" if o["want"] == "燃える石" else "planks_moved"] + n, 2)
    if _need(o) <= 0:
        _fulfil(state, o)


def _fulfil(state, o):
    g, D = _g(state), state["day"]
    o["status"], o["end"], o["end_y"] = "果たした", D, _ay(state)
    if o["pay"] == "手間":
        o["back"] = {"need": o["pn"], "done": 0, "from": D}
    else:
        put_goods(state, o["taker"], o["pay"], o["escrow"])
    log(state, EV, o["taker_by"], f"{o['taker']}が、{o['house']}の頼み ({o['want']} {o['n']} {WANTS[o['want']][2]}) を果たした", order=o["id"], household=o["taker"])
    _yr(state, _ay(state))["done"] += 1
    _reach(state, "F3", f"{o['taker']}が {o['house']}の頼み {o['id']} を果たした")
    for n, w in list(g["work"].items()):
        if w["id"] == o["id"]:
            _restore(state, n, w)
            g["work"].pop(n)


def _failed(state, o):
    """期限までに果たせなかった: 預けは頼んだ家にもどり、できた分だけ渡る (もう倉に入っている)"""
    D = state["day"]
    o["status"], o["end"], o["end_y"] = "果たせなかった", D, _ay(state)
    if o["pay"] != "手間" and o.get("escrow"):
        put_goods(state, o["house"], o["pay"], o["escrow"])
    _yr(state, _ay(state))["failed"] += 1


# ---------------- 季節のはじめ: 頼みの仕事と手間返し ----------------

def _set_plan(state, p, plan):
    """その人の予定を plan にする。戻り値: もとの予定 (知らせを書く日を待っている人は、書いたあとの予定を入れかえる)"""
    rs = _i4()._g(state).get("restore") or {}
    if p["name"] in rs:
        old = rs[p["name"]]
        rs[p["name"]] = plan
        return old
    old = copy.deepcopy(p.get("plan") or {"activity": "休む", "place": "camp", "with": []})
    p["plan"] = plan
    return old


def _restore(state, name, w):
    p = _adult(state, name)
    d = g15._g(state)["dest"]
    if "dest" in w:
        if w["dest"] is None:
            d.pop(name, None)
        else:
            d[name] = w["dest"]
    if p is None:
        return
    rs = _i4()._g(state).get("restore") or {}
    if name in rs:
        rs[name] = w["plan"]
    else:
        p["plan"] = w["plan"]


def saw_ws(state):
    """頼みの板をひける水ののこの作業場 (できていて、輪が止まっていない。持ち場の人の少ないほう、同じなら名の順)"""
    ok = []
    for m in g15.workshops(state, done=True):
        w = g15._g(state)["ws"][m]
        mi = g15._mill(state, m)
        if w.get("tool") == g15.SAW and mi is not None and not mi.get("stopped"):
            ok.append(m)
    return min(ok, key=lambda m: (len(_s3().posts_of(state, m)), m)) if ok else None


def food_first(state):
    return state["era2"]["g7"].get("ask") == "集まり直し" or era2.store_days(state) < STORE_STOP


def usual_food(state, name, h=None):
    """その人のいつもの食べ物の仕事: 前の季節のその人の仕事 → 家でいちばん多かった仕事 → 畑仕事 (i4.refit_job と同じ順。食べ物の仕事だけ)"""
    i4 = _i4()
    ok = [a for a in FOOD_JOBS if a in era2.acts2(state)]
    past = (state["era2"]["g7"].get("past") or [None])[-1] or {}
    days = past.get("days") or {}
    a = i4._best(days.get(name) or {}, ok) if name else None
    if a:
        return a
    h = h or _house_of(state, name)
    tot = {}
    for n, acts_ in days.items():
        if h and (past.get("home") or {}).get(n) == h:
            for k, d in acts_.items():
                tot[k] = tot.get(k, 0) + d
    return i4._best(tot, ok) or FOOD_LAST


def season_start(state):
    """季節のはじめ (g7._apply の終わり。i4 の書く日のあと): 受けた頼みの人は頼みの仕事 (1 人 10 日まで)、手間を返す家の大人はかわりの仕事"""
    g, D = _g(state), state["day"]
    for n, w in list(g["work"].items()) + list(g["back_now"].items()):
        _restore(state, n, w)
    g["work"], g["back_now"] = {}, {}
    src = state["era2"]["g7"].get("src") or {}
    busy = set()
    if food_first(state):
        for o in g["book"]:
            if o["status"] == "受けた":
                o["due"] += SEASON_DAYS
                o["food_first"].append(D + 1)
                _yr(state, (D + 1) // YEAR)["food_first"] += 1
    else:
        mid = saw_ws(state)
        for o in sorted((x for x in g["book"] if x["status"] == "受けた"), key=lambda x: x["id"]):
            for n in o["workers"]:
                p = _adult(state, n)
                if p is None or p.get("household") != o["taker"] or n in g["work"]:
                    continue
                if o["want"] == "燃える石":
                    plan = {"activity": g15.ACT_DIG, "place": g15.COAL_PLACE, "with": []}
                    w = {"id": o["id"], "days": 0, "act": g15.ACT_DIG}
                else:
                    if mid is None:
                        _fail(state, n, SRC, f"{n} は、使える水ののこの作業場がないので、頼み {o['id']} の板をひけなかった")
                        continue
                    plan = {"activity": g15.ACT_WS_WORK, "place": "camp", "with": []}
                    w = {"id": o["id"], "days": 0, "act": g15.ACT_WS_WORK, "dest": g15._g(state)["dest"].get(n), "mill": mid}
                    g15._g(state)["dest"][n] = mid
                w["plan"] = _set_plan(state, p, plan)
                w["from"] = src.get(n)
                g["work"][n] = w
                busy.add(n)
    # 手間返し: 頼んだ家の大人 (名の順。読める人はあと) が、受けた家の人のいつもの食べ物の仕事を、のこりの日数だけ (1 人 1 季節 10 日まで)
    rd = set(g10._g(state)["readers"])
    for o in sorted((x for x in g["book"] if x.get("back") and x["back"]["done"] < x["back"]["need"]), key=lambda x: x["id"]):
        left = o["back"]["need"] - o["back"]["done"] - sum(b["target"] for b in g["back_now"].values() if b["id"] == o["id"])
        jobs = [usual_food(state, n, o["taker"]) for n in (o["workers"] or [None])] or [usual_food(state, None, o["taker"])]
        ads = sorted((n for n in _house_adults(state, o["house"]) if n not in busy and n not in g["back_now"]), key=lambda n: (n in rd, n))
        for i, n in enumerate(ads):
            if left <= 0:
                break
            k = min(DAYS_MAX, left)
            job = jobs[i % len(jobs)]
            p = _adult(state, n)
            b = {"id": o["id"], "days": 0, "target": k, "act": job, "for": (o["workers"] or [None])[i % max(1, len(o["workers"]))]}
            b["plan"] = _set_plan(state, p, {"activity": job, "place": "camp", "with": []})
            g["back_now"][n] = b
            left -= k


# ---------------- 1 日 (g7.role_day・g7.count_day から) ----------------

def working(state, p, act):
    w = _g(state)["work"].get(p["name"])
    return bool(w) and w["act"] == act


def _ev(state, t):
    ids = t.get("events") or []
    if ids and state["events"] and state["events"][-1]["id"] == ids[-1]:
        return state["events"][-1]
    return None


def work_day(state, p, t, act):
    """頼みの仕事の 1 日 (g7.role_day から。燃える石を掘る・水の作業場で働く): できた物を頼んだ家の倉へ (S3 の「2 割は掘った人の家」も、この日は頼んだ家へ)"""
    g, D = _g(state), state["day"]
    name, h = p["name"], p.get("household")
    w = g["work"][name]
    o = next((x for x in g["book"] if x["id"] == w["id"]), None)
    if o is None or o["status"] != "受けた":
        _restore(state, name, w)
        g["work"].pop(name)
        g15.work_day(state, p, t, act)
        return
    s3g, g15g = _s3()._g(state), g15._g(state)
    c, pk = g15g["coal"], g15g["planks"]
    ys = str(g15._y(state))
    d0, h0, k0 = c["dug"].get(ys, 0), s3g["hcoal"].get(h, 0), pk["stock"]
    if act == g15.ACT_WS_WORK:
        g15g["dest"][name] = w.get("mill") or g15g["dest"].get(name)
    g15.work_day(state, p, t, act)
    if act == g15.ACT_DIG:
        made = c["dug"].get(ys, 0) - d0  # 掘った kg (村の倉の数は 0.1 kg に丸めるので、掘った帳の数で数える)
        dh = round(s3g["hcoal"].get(h, 0) - h0, 2)
    else:
        made = round(pk["stock"] - k0, 2)
    if made <= 0:  # 働けなかった (作業場がいっぱい・止まった): 休みつづけないように、その季節はもとの仕事にもどる
        _fail(state, name, SRC, f"{name} は、頼み {o['id']} の仕事ができなかったので、もとの仕事にもどった")
        _restore(state, name, w)
        g["work"].pop(name)
        return
    give = min(made, _need(o))
    if act == g15.ACT_DIG:
        th = min(dh, give)
        if th > 0:
            s3g["hcoal"][h] = round(s3g["hcoal"][h] - th, 2)
        c["stock"] = round(max(0.0, c["stock"] - (give - th)), 1)
        o["dug"] = round(o["dug"] + made, 2)
    else:
        pk["stock"] = round(pk["stock"] - give, 2)
    w["days"] += 1
    o["days"][name] = o["days"].get(name, 0) + 1
    o["pd"] += 1
    y = D // YEAR
    yr = _yr(state, y)
    yr["pd"][o["taker"]] = yr["pd"].get(o["taker"], 0) + 1
    yr["coal_dug" if act == g15.ACT_DIG else "planks_made"] = round(yr["coal_dug" if act == g15.ACT_DIG else "planks_made"] + made, 2)
    if yr["pd"][o["taker"]] >= P2_DAYS:
        _reach(state, "F4", f"{o['taker']}が、よその家の頼みで {P2_DAYS} 人日働いた")
    e = _ev(state, t)
    if e is not None:
        u = WANTS[o["want"]][2]
        if act == g15.ACT_DIG:
            e["text"] = (f"{name} が、{o['house']}の頼みで、北の丘で燃える石を {round(made)} kg 掘って、{round(give)} kg を{o['house']}の倉に運んだ"
                         + (f" (のこり {round(made - give)} kg は村の倉と家の倉に)" if made - give >= 1 else ""))
        else:
            e["text"] = f"{name} が、{o['house']}の頼みで、作業場 {w.get('mill')} の水ののこで木をひいて、板 {round(give, 1)} {u}を{o['house']}の倉に運んだ"
        e.setdefault("data", {})["order"] = o["id"]
    _deliver(state, o, give)
    if name in g["work"] and w["days"] >= DAYS_MAX:
        _restore(state, name, w)
        g["work"].pop(name)


def count_day(state, name, act):
    """手間返しの日を数える (g7.count_day から): かわりの仕事を 1 日したら 1 人日。決めた日数になったら、もとの仕事にもどる"""
    g = _g(state)
    b = g["back_now"].get(name)
    if not b or act != b["act"]:
        return
    o = next((x for x in g["book"] if x["id"] == b["id"]), None)
    if o is None or not o.get("back"):
        return
    b["days"] += 1
    o["back"]["done"] += 1
    _yr(state, state["day"] // YEAR)["back_days"] += 1
    if b["days"] >= b["target"]:
        _restore(state, name, b)
        g["back_now"].pop(name)
    if o["back"]["done"] >= o["back"]["need"] and not o["back"].get("end"):
        o["back"]["end"] = state["day"]
        log(state, EV, name, f"{o['house']}が、{o['taker']}に手間 {o['back']['need']} 人日を返した", order=o["id"], household=o["house"])


# ---------------- 集まりの答え ----------------

def count_used(state, real):
    """中身が分かる人が、話・知識・掟で頼み書きのことを書いたか (「頼み」の字。数えるだけ。お題には出さない)"""
    if not (_g(state)["orders"] or _g(state)["book"]):
        return
    i4 = _i4()
    yr = _yr(state, (state["day"] + 1) // YEAR)
    for name, a in sorted(real.items()):
        p = _adult(state, name)
        if p is None or not isinstance(a, dict):
            continue
        me, fam = i4.can_read(state, p)
        if not me and not fam:
            continue
        yr["used"] += sum(1 for _, t in i4._texts(a) if "頼み" in t)


def apply_answers(state, real):
    """集まりの答え (g7.apply_year から。i4 の知らせのあと): 頼み書きを使ったか → 受ける (take) → 頼み書き (order)。
    受けるのは、お題を書いたときに板にあった頼みだけ (この集まりで書かれた頼みは、次の集まりから)"""
    _MEET[0] = True
    try:
        count_used(state, real)
        take_orders(state, real)
        write_orders(state, real)
    finally:
        _MEET[0] = False


# ---------------- 季節の終わり・年の終わり ----------------

def season_end(state):
    """季節の終わり (g7.season_end。i4 のあと): 頼みの仕事と手間返しの人をもとの予定にもどす → 期限と板の古い頼み → 蓄え → 年の終わりなら行と物差し"""
    g, D = _g(state), state["day"]
    for n, w in list(g["work"].items()) + list(g["back_now"].items()):
        _restore(state, n, w)
    g["work"], g["back_now"] = {}, {}
    if (D + 1) % SEASON_DAYS:
        return
    for o in list(g["book"]):
        if o["status"] == "受けた" and D >= o["due"]:
            _failed(state, o)
    for o in list(g["orders"]):
        if D - o["day"] >= LIFE:
            _drop(state, o, "受ける家がないまま 4 季節たった")
    y = str(D // YEAR)
    sd = era2.store_days(state)
    g["store_min"][y] = min(g["store_min"].get(y, sd), sd)
    if (D + 1) % YEAR == 0:
        year_end(state)


def row_of(state, y):
    g = _g(state)
    ys = str(y)
    yr = g["yr"].get(ys) or _yr(state, y)
    done = [o for o in g["book"] if o["status"] == "果たした" and o.get("end_y", o.get("end", 0) // YEAR) == y]
    req, tak = sorted({o["house"] for o in done}), sorted({o["taker"] for o in done})
    town = sorted((h for h, d in yr["pd"].items() if d >= P2_DAYS), key=lambda h: (-yr["pd"][h], h))
    w, nf = _s4().work_days(state)
    p3 = round(nf / w, 4) if w else 0.0
    ads = era2.adults(state)
    rd = g10.readers(state)
    rshare = round(len(rd) / len(ads), 4) if ads else 0.0
    ev = [e for e in state["events"] if e["day"] // YEAR == y]
    famine = sum(1 for e in ev if e["type"] == "蓄えが尽きる")
    pop = len([p for p in state["people"] if p["alive"]])
    smin = g["store_min"].get(ys, era2.store_days(state))
    fire = (_s3()._g(state)["fire"].get(ys) or {})
    owed_all = sum(b["back"]["need"] - b["back"]["done"] for b in g["book"] if b.get("back"))
    return {"year": y, "done": len(done), "req_houses": len(req), "taker_houses": len(tak), "wrote": len(yr["wrote"]), "took": len(yr["took"]),
            "town": town, "town_n": len(town), "pd": sum(yr["pd"].values()), "pd_houses": dict(sorted(yr["pd"].items())),
            "worked": w, "nonfood": nf, "p3_share": p3, "coal_dug": round(yr["coal_dug"]), "planks_made": round(yr["planks_made"], 1),
            "coal_moved": round(yr["coal_moved"]), "planks_moved": round(yr["planks_moved"], 1), "failed": yr["failed"], "gone": yr["gone"],
            "back_days": yr["back_days"], "owed": owed_all, "used": yr["used"], "food_first": yr["food_first"],
            "fire_pd": round(fire.get("hours", 0) / _s3().PD_H), "house_coal": round(sum(_s3()._g(state)["hcoal"].values())),
            "chose": len(g["chose"].get(ys) or []), "fails": len([f for f in g["fails"] if f["year"] == y]),
            "readers": len(rd), "adults": len(ads), "r_share": rshare, "store_min": smin, "store_end": era2.store_days(state), "famine": famine, "pop": pop, "pop0": g["pop0"],
            "p1_like": len(done) >= P1_DONE and len(req) >= P1_HOUSES and len(tak) >= P1_HOUSES, "p2_like": len(town) >= P2_HOUSES,
            "p3_ok": p3 >= P3_SHARE, "p4_ok": famine == 0 and smin >= P4_STORE and pop >= P4_POP * g["pop0"] and rshare >= P4_READERS}


def year_end(state):
    g, D = _g(state), state["day"]
    y = D // YEAR
    if y < g["start_year"] or str(y) in g["rows"]:
        return
    r = g["rows"][str(y)] = row_of(state, y)
    for k in ("p1", "p2"):
        if r[f"{k}_like"] and y not in g["f_years"][k]:
            g["f_years"][k].append(y)
    if not r["p4_ok"] and y not in g["p4_broken"]:
        g["p4_broken"].append(y)
    keep = (y - 2) * YEAR  # 帳は 3 年分 (受けている頼み・返していない手間は残す)
    g["book"] = [o for o in g["book"] if o["status"] == "受けた" or o.get("end", D) >= keep or (o.get("back") and o["back"]["done"] < o["back"]["need"])]


def entrance(state):
    """入口: いちばん新しい 2 年に、p1 と p2 がつづき、その 2 年に p3 と p4 を割らない"""
    g = _g(state)
    if not g["rows"]:
        return False
    y = max(int(k) for k in g["rows"])
    ys = [g["rows"].get(str(y - i)) for i in range(P_YEARS)]
    if not all(ys):
        return False
    return all(r["p1_like"] and r["p2_like"] and r["p3_ok"] and r["p4_ok"] for r in ys)


def check(state, done):
    """g7.check から (季節の終わり): 止まるわけ (なければ None)。i4 の止まりは、読める大人が 1 人以下だけ (i4 の closed)"""
    c = _i4().check(state, done)
    if c:
        return c
    g, D = _g(state), state["day"]
    if (D + 1) % YEAR:
        return None
    y = D // YEAR
    if y < g["start_year"]:
        return None
    r = g["rows"].get(str(y)) or {}
    if entrance(state) and not any(c["why"] == "p4_entrance" for c in done):
        return {"why": "p4_entrance", "year": y, "day": D, "text": f"P4: 入口に着いた ({y - 1}年と{y}年に p1・p2。その 2 年に p3・p4 を割らなかった)"}
    if r and not r["p4_ok"] and not any(c["why"] == "p4_safe" and c.get("year") == y for c in done):
        return {"why": "p4_safe", "year": y, "day": D, "text": f"P4: {y}年に p4 (暮らしを守る) を割った (ききん {r['famine']}・蓄えのいちばん少ない日 {r['store_min']} 日分・"
                f"人 {r['pop']} (はじめ {r['pop0']} の {round(P4_POP * 100)}% は {math.ceil(P4_POP * r['pop0'])})・読める大人 {round(r['r_share'] * 100, 1)}%)"}
    ys = [g["rows"].get(str(y - i)) for i in range(ZERO_YEARS)]
    if all(x and x["wrote"] == 0 and x["took"] == 0 for x in ys) and not any(c["why"] == "p4_zero" and c.get("year") == y for c in done):
        return {"why": "p4_zero", "year": y, "day": D, "text": f"P4: 頼み書きを書いた家・受けた家が {ZERO_YEARS} 年つづけて 0"}
    n = y - g["start_year"] + 1
    if n > 0 and n % LATER_YEARS == 0 and not any(c["why"] == f"p4_years_{y}" for c in done):
        return {"why": f"p4_years_{y}", "year": y, "day": D, "text": f"P4: 頼み書きと約束の帳に入って {n} 年たった (3 年ごとの相談)"}
    return None


# ---------------- お題 (知らせ板の節の中。新しい節は作らない) ----------------

def _u(k):
    return WANTS[k][2] if k in WANTS else PAY_UNIT.get(k, "")


def _pay_text(o):
    return f"{o['pay']} {o['pn']} {PAY_UNIT[o['pay']]}"


def order_lines(state, p, answer=True):
    """知らせ板の節に足す行 (知らせのあと)。読める人・家に読める大人がいる人には中身、どちらでもない人には枚数だけ"""
    i4 = _i4()
    g, D = _g(state), state["day"]
    name, h = p["name"], p.get("household")
    me, fam = i4.can_read(state, p)
    bd = board_now(state)
    act = [o for o in g["book"] if o["status"] == "受けた"]
    ly = (D + 1) // YEAR - 1
    fin = [o for o in g["book"] if o["status"] in ("果たした", "果たせなかった") and o.get("end_y", o.get("end", 0) // YEAR) >= ly]
    debt = [o for o in g["book"] if o.get("back") and o["back"]["done"] < o["back"]["need"]]
    rows = []
    if not (me or fam):
        if bd or act:
            rows.append(f"- 頼み書きが {len(bd) + len(act)} 枚ある。字が読めないので、中身はわからない (家に読める人がいない)")
        if answer:
            rows.append("- あなたの家には字を書ける大人がいないので、頼み書きは書けず、受けることもできない")
        return rows
    rows.append("頼み書き (燃える石か板がほしい家が書く。ほかの家が受けて働き、かわりの物をもらう):")
    if bd:
        rows += [f"- 頼み{o['id']} {o['house']}: {o['want']} {o['n']} {_u(o['want'])} ← {_pay_text(o)} ({_sl(o['day'] + LIFE)}に消える)" for o in bd]
    else:
        rows.append("- 板に頼みはない")
    if act or fin or debt:
        t = ["約束の帳:"]
        t += [f"頼み{o['id']} {o['taker']}が受けた ({round(o['made'])}/{o['n']} {_u(o['want'])}・{_sl(o['due'])}まで)" for o in act]
        t += [f"頼み{o['id']} {o['taker']}が{'果たした' if o['status'] == '果たした' else '果たせなかった'}" for o in fin]
        t += [f"返していない手間 {o['house']}→{o['taker']} {o['back']['need'] - o['back']['done']} 人日" for o in debt]
        rows.append("- " + t[0] + " " + " / ".join(t[1:]))
    if not me:
        rows.append(f"(頼み書きも、家の {fam} が読んで聞かせた)")
    if not answer:
        return rows
    s3g = _s3()._g(state)
    kg = _s4().dig_kg_now(state)
    rows.append(f"- 燃える石 {kg} kg = 掘り場で掘る 1 人日。秋と冬に燃やすと、まき集め 約 {round(_s4().dig_saves_pd(kg))} 人日")
    fh = ((s3g["fire"].get(str(ly)) or {}).get("house") or {}).get(h, 0)
    rows.append(f"- あなたの家の、去年のまき集め {round(fh)} 人日・家の倉の燃える石 {have(state, h, '燃える石')} kg・板 {have(state, h, '板')} 束")
    rows.append(f"- 頼みの仕事は 1 人 1 季節 {DAYS_MAX} 日まで。のこりの日はいつもの仕事。手間返しのときは、頼んだ家の人が書いた日数だけ、あなたの家の人のいつもの仕事をかわりにする")
    ads = _house_adults(state, h)
    why = (f"手間をまだ {owed(state, h)} 人日返していない" if owed(state, h) else
           f"まだ受けられていない頼みが {OPEN_MAX} 枚ある" if len(open_of(state, h)) >= OPEN_MAX else None)
    if why:
        rows.append(f"- あなたの家は{why}ので、新しい頼みは書けない")
    else:
        tema = min(6, len(ads) * TEMA_PER_ADULT)
        goods = [f"{k} {have(state, h, k)} {PAY_UNIT[k]}" for k in ("草の種", "燃える石", "板") if have(state, h, k) >= 1]
        rows.append(f"- 頼むなら \"order\": {{\"ほしい\": \"燃える石\", \"数\": 3000, \"かわり\": {{\"手間\": {tema}}}}} (燃える石 500〜10000 kg か 板 10〜200 束。"
                    f"手間は家の大人の数 × {TEMA_PER_ADULT} 人日まで"
                    + (f"。家の倉の {'・'.join(goods)} から 1 つでもよく、書いたとき預けに分ける" if goods else "") + ")。1 家 1 季節 1 枚")
    other = [o for o in bd if o["house"] != h]
    if other:
        rows.append(f"- 受けるなら \"take\": {{\"頼み\": {other[0]['id']}, \"人\": [\"{name}\"]}} (あなたの家の大人 {WORKERS_MAX} 人まで。"
                    f"燃える石は北の丘で掘る・板は水の作業場で働く。家の倉にあればすぐ渡す。期限は次の季節の終わり)")
    f = [x for x in g["fails"] if x.get("house") == h and x["year"] >= ly][-2:]
    if f:
        rows.append("- 頼み書きで、できなかったこと: " + " / ".join(x["why"] for x in f))
    return rows


def board_block(state, p, answer=True):
    """i4 の知らせ板の節に、頼み書きの行を足す (新しい節は作らない)"""
    base = _i4().board_block(state, p, answer)
    if not base or not p:
        return base
    rows = order_lines(state, p, answer)
    return base + "\n".join(rows) + "\n" if rows else base


def field_rows(state, year=False):
    return ["   order: 知らせ板に書く頼み書き (燃える石か板がほしいとき。家に字の読める大人がいるとき)。書かないなら null",
            "   take: 板の頼みを受ける {\"頼み\": 番号, \"人\": [あなたの家の大人]}。受けないなら null"]


ANSWER_FIELDS = {"order": "null", "take": "null"}


def answer_fields(state):
    return ["order", "take"]


# ---------------- step.py status・年報 (村の人のお題には出さない) ----------------

def row_text(r):
    return (f"{r['year']}年: 果たした頼み {r['done']} (頼んだ家 {r['req_houses']}・受けた家 {r['taker_houses']}) / 書いた家 {r['wrote']}・受けた家 {r['took']} / "
            f"頼みの仕事 {r['pd']} 人日・30 人日の家 {r['town_n']} / 食べ物でない仕事 {r['nonfood']}/{r['worked']} 人日 ({round(r['p3_share'] * 100, 1)}%) / "
            f"掘った石 {r['coal_dug']} kg・板 {r['planks_made']} 束・家から家へ 石 {r['coal_moved']} kg・板 {r['planks_moved']} 束 / 果たせなかった {r['failed']}・消えた {r['gone']} / "
            f"手間返し {r['back_days']} 人日 (のこり {r['owed']}) / まき集め {r['fire_pd']} 人日 / 蓄え いちばん少ない {r['store_min']} 日分・ききん {r['famine']}・人 {r['pop']} "
            f"(はじめ {r['pop0']})・読める大人 {round(r['r_share'] * 100, 1)}% / "
            + f"p1 {'○' if r['p1_like'] else '×'} p2 {'○' if r['p2_like'] else '×'} p3 {'○' if r['p3_ok'] else '×'} p4 {'○' if r['p4_ok'] else '×'}")


def lines(state):
    if not on(state):
        return []
    g = _g(state)
    out = [f"{g['why']}。{g['day']} 日目から ({g['start_year']}年から数える)。板の頼み {len(g['orders'])}・受けている頼み {len([o for o in g['book'] if o['status'] == '受けた'])}"
           + " / " + " / ".join(f"{k} {FS[k]} {_yd(g['f'][k]) if k in g['f'] else 'まだ'}" for k in FS)
           + f" / p4 を割った年 {'・'.join(map(str, g['p4_broken'])) or 'なし'} / 入口 {'○' if entrance(state) else 'まだ'}"]
    for y in sorted(g["rows"], key=int)[-3:]:
        out.append(row_text(g["rows"][y]))
    return out


def orders_of(state, y):
    """y 年に書かれた頼み (年報。板・帳・消えたもの)"""
    g = _g(state)
    allo = {o["id"]: o for o in g["gone"] + g["book"] + g["orders"]}
    return [allo[k] for k in sorted(allo) if allo[k]["year"] == y]


def book_of(state, y):
    """y 年に受けていた・果たした・果たせなかった頼み (年報)"""
    return [o for o in _g(state)["book"] if (o.get("taken", 0) + 1) // YEAR <= y and (o["status"] == "受けた" or o.get("end_y", y) >= y)]
