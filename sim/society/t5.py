"""Society 3.0 フェーズ 5「川下の町と鉄の道具」(2026-11-22。docs/society_phase/T5_design.md・T5_check.md)

- 印 state.era2.g7.t5 があるときだけ働く。印を書くのは step.py resume --t5 "<本人の言葉>" だけ
  (p4 のあと、28319 日目 (235年の終わり) から。P4 の相談で止まっているときか、止まりがないとき。1 回だけ)。
  印がなければ、このファイルは読みこみもしない (g7・era2・p4・step.py・tools/year_report.py は「t5」の鍵か、町の頼み (o["town"]) があるときだけ読みこむ)。
  だから前の歩は、お題・state・出来事・乱数が 1 バイトも変わらない
- 印を書くと g7.p4.closed も書く (P4 の入口・相談を止める。頼み書き・約束の帳・知らせ板・手習いはそのまま)
- フェーズ 4 の頼み書きと約束の帳 (p4.py) の上に、頼む側「川下の町」を足す:
  a 町の頼み: 季節の終わりに、板の上の町の頼みが 3 枚になるまで「燃える石 2500 kg ← 鉄の鎌 1 本」「板 8 束 ← 1 本」「燃える石 5000 kg ← 2 本」を順に出す
    (町が 1 年に出す鎌は 12 本まで)。受け方は p4 の take のまま (家に読める大人がいる家・家の大人 4 人まで・1 人 1 季節 10 日まで・家の倉にあればすぐそろう)
  b 運ぶ: 物がそろったら、はじめに名を書いた人が川を下って町へ運ぶ (1 日。頼みの仕事の日に数える)。運んだ日に、鉄の鎌は受けた家のもの
  c 鉄の鎌: 持つ家の大人が昼の「畑仕事」で実った畑を刈る日、1 人 1 本 (古い鎌から) 使うと、刈る量が 1.3 倍 (150 → 195 つかみ)。刈る日に 60 日使うと傷んで使えない
- 乱数は使わない。後押しはしない。印・本人の言葉・「作る側」・物差しのことは、村の人のお題にも出来事にも書かない
- 物差し (T5_design.md 4.): t1 果たした町の頼み 4 件以上・受けた家 2 以上・t2 町かよその家の頼みで 30 人日以上働いた家 2 以上・
  t3 食べ物でない仕事 22% 以上 (守り)・t4 暮らしを守る (ききんなし・蓄え 120 日分・人は印のときの 95%・読める大人 15%)。
  入口は t1 と t2 が 2 年つづき、その 2 年に t3 と t4 を割らない。止めて相談: t4 を割った年・果たした町の頼みが 2 年 0・3 年ごと (236年から数える)
"""
import math

import era2
import g10
import g15
import p4
from world import log

YEAR, SEASON_DAYS = era2.YEAR, era2.SEASON_DAYS
T5_FROM = 28319  # 本物の村が 235年を終えて P4 の相談で止まった日。これより前には印を書けない
T5_DATE = "2026-11-22"
T5_NAME = "Society 3.0 フェーズ 5 (川下の町と鉄の道具)"
PARTS = {"a": "町の頼み (川下の町が知らせ板に燃える石と板の頼みを出す。払いは鉄の鎌)",
         "b": "運ぶ (物がそろったら、受けた家の 1 人が川を下って町へ運ぶ。鎌は受けた家のもの)",
         "c": "鉄の鎌 (持つ家の大人の昼の刈り入れが 1.3 倍。刈る日 60 日で傷む)"}
TOWN = "川下の町"
TOOL = "町の鎌"  # 鉄の鎌 (村の人に見せる呼び名は「町の鎌」。G10 から村の人のお題に「鉄」は書かない (g10.WORDS)。村の言葉では黒い金属)
# a 町の頼み【仮定】(ほしい物, 数, 払う鎌の本数)。順にくり返す
KINDS = (("燃える石", 2500, 1), ("板", 8, 1), ("燃える石", 5000, 2))
TOWN_OPEN = 3  # 板の上の町の頼み (受けられていないもの) の数
TOOLS_YEAR = 12  # 町が 1 年に頼みに書く鎌の本数の上
# c 鉄の鎌【仮定】
BASE_REAP = 150  # 昼の畑仕事の刈る量 (era2._field_work の 1 日 150 つかみ。働く時間で変わる)
REAP_MULT = 1.3
LIFE = 60  # 刈る日にこれだけ使うと傷んで使えない
# 物差し【仮定】(T5_design.md 4.)
T1_DONE, T1_HOUSES = 4, 2
T2_DAYS, T2_HOUSES = 30, 2
T3_SHARE = 0.22
T4_STORE, T4_POP, T4_READERS = 120, 0.95, 0.15
T_YEARS = 2
ZERO_YEARS = 2
LATER_YEARS = 3
TS = {"t1": "果たした町の頼み", "t2": "町かよその家のために働く家", "t3": "食べ物でない仕事 (守り)", "t4": "暮らしを守る"}
FS = {"F1": "はじめて町の頼みを受けた", "F2": "はじめて町へ運んで鉄の鎌を受けた", "F3": "はじめて鉄の鎌で刈った", "F4": "はじめて鉄の鎌が傷んだ"}
SECTION = "## 村の知らせ板"  # お題の節の見出し (tools/prompt_check.py --words t5 が読む。i4 の節の中、p4 の頼み書きの行のあと)
FACT_HEADS = ()
# 村の人に見せる文 (知らせ板の節) に書かない言葉 (tools/prompt_check.py --words t5・T_T5 で確かめる)
WORDS = ("作る側", "後押し", "反実仮想", "印", "物差し", "入口", "Society", "本人", "T5", "P4", "I4", "S4", "t1", "t2", "t3", "t4", "分業", "町の芽",
         "フェーズ", "相談", "おすすめ", "鉄")


def on(state):
    return "day" in (((state.get("era2") or {}).get("g7") or {}).get("t5") or {})


def _g(state):
    return state["era2"]["g7"]["t5"]


def _p4g(state):
    return p4._g(state)


def _i4():
    import i4
    return i4


def _s4():
    import s4
    return s4


def _s3():
    import s3
    return s3


def _yd(day):
    return f"{day // YEAR}年{day % YEAR + 1}日目"


def _yr(state, y):
    return _g(state)["yr"].setdefault(str(y), {"posted": 0, "posted_tools": 0, "done": 0, "carry": 0, "pd": {}, "coal": 0.0, "planks": 0.0,
                                               "paid": 0, "worn": 0, "reap_uses": 0, "reap_extra": 0, "reap_house": {}})


def _reach(state, f, why):
    g = _g(state)
    if f not in g["f"]:
        g["f"][f] = state["day"]
        g.setdefault("f_why", {})[f] = why


def unit(k):
    return p4.WANTS[k][2]


# ---------------- 印 (step.py resume --t5) ----------------

def why_text(words):
    return f"{T5_NAME} (本人の言葉 {T5_DATE} 「{words}」)"


def refusal(state, words):
    """resume --t5 ができないわけ (できるなら None)"""
    if not (words or "").strip():
        return "--t5 には本人の言葉が要る"
    g7s = ((state.get("era2") or {}).get("g7") or {})
    if "p4" not in g7s or not p4.on(state):
        return "p4 の印がないので、T5 は始められない"
    if "t5" in g7s:
        return "T5 はもう始めてある"
    if state["day"] < T5_FROM:
        return f"T5 は {T5_FROM} 日目 (235年の終わり) からだけ"
    h = g7s.get("hold") or {}
    if state.get("hold") or h:
        if not (h.get("why") == "consult" and str(h.get("what", "")).startswith("P4:")):
            return "T5 は、P4 の相談で止まっているときか、止まりのないときだけ始める"
    if g15.push_on(state):
        return "後押しが動いている"
    return None


def mark(state, words):
    """resume --t5 から: 印 g7.t5 を書き、g7.p4.closed を書き、町の頼みを板に出す (村の出来事には残さない)"""
    words = words.strip()
    D = state["day"]
    _p4g(state)["closed"] = D
    g = state["era2"]["g7"]["t5"] = {
        "day": D, "words": words, "why": why_text(words), "parts": list(PARTS), "start_year": D // YEAR + 1,
        "pop0": len([p for p in state["people"] if p["alive"]]), "adults0": len(era2.adults(state)),
        "kind": 0, "tools": {}, "next_tool": 1, "worn": [], "reap_day": {}, "yr": {}, "rows": {}, "f": {},
        "f_years": {"t1": [], "t2": []}, "t4_broken": [], "store_min": {}}
    post(state)
    return g


# ---------------- a 町の頼み ----------------

def town_open(state):
    return [o for o in _p4g(state)["orders"] if o.get("town")]


def post(state):
    """板の上の町の頼みが TOWN_OPEN 枚になるまで、次の種類の頼みを出す (その季節が入る暦の年に、町が書く鎌は TOOLS_YEAR 本まで)"""
    g, g4, D = _g(state), _p4g(state), state["day"]
    y = (D + 1) // YEAR
    yr = _yr(state, y)
    out = []
    while len(town_open(state)) < TOWN_OPEN:
        want, n, pn = KINDS[g["kind"] % len(KINDS)]
        if yr["posted_tools"] + pn > TOOLS_YEAR:
            break
        g["kind"] += 1
        r = {"id": g4["next_id"], "day": D, "year": y, "season": p4._sl(D + 1), "house": TOWN, "by": TOWN, "writer": None, "want": want, "n": n,
             "pay": TOOL, "pn": pn, "escrow": 0, "status": "板", "town": True}
        g4["next_id"] += 1
        g4["orders"].append(r)
        while len(g4["orders"]) > p4.BOARD_MAX:
            p4._drop(state, g4["orders"][0], "板がいっぱいで、古い頼みから消えた")
        yr["posted"] += 1
        yr["posted_tools"] += pn
        out.append(r)
    return out


# ---------------- b 運ぶ (p4 の約束の帳から) ----------------

def ready(state, o):
    """町の頼みの物がそろった (p4._deliver から): 受けた家の人が町へ運ぶのを待つ"""
    o["status"], o["ready"] = "運ぶ", state["day"]


def after_ready(state, name, w, o):
    """そろえた人 (p4.work_day から): ほかの人はもとの仕事にもどる。そろえた人は、10 日のうちなら次の日に運ぶ (10 日目なら次の季節のはじめに、ほかの人が)"""
    g4 = _p4g(state)
    for n, x in list(g4["work"].items()):
        if x["id"] == o["id"] and n != name:
            p4._restore(state, n, x)
            g4["work"].pop(n)
    if w["days"] < p4.DAYS_MAX:
        w["carry"] = True


def carrier(state, o, src, busy):
    """季節のはじめ (p4.season_start から): そろった町の頼みを運ぶ人を 1 人決める (はじめに名を書いた人 → 受けた答えの人 → 家の大人の名の順)"""
    g4 = _p4g(state)
    ads = p4._house_adults(state, o["taker"])
    cand = [n for n in list(o.get("workers") or []) + [o.get("taker_by")] + ads if n in ads and n not in g4["work"] and n not in busy]
    if not cand:
        return None
    n = cand[0]
    p = p4._adult(state, n)
    w = {"id": o["id"], "days": 0, "act": g15.ACT_DIG, "carry": True}
    w["plan"] = p4._set_plan(state, p, {"activity": g15.ACT_DIG, "place": "camp", "with": []})
    w["from"] = src.get(n)
    g4["work"][n] = w
    busy.add(n)
    return n


def carry_day(state, p, t, w, o):
    """運ぶ 1 日 (p4.work_day から): 川を下って町に物を渡し、鉄の鎌を受ける (p4._fulfil → pay)"""
    g4, D = _p4g(state), state["day"]
    name = p["name"]
    w["days"] += 1
    o["days"][name] = o["days"].get(name, 0) + 1
    o["pd"] += 1
    o["carrier"], o["carried"] = name, D
    pyr = p4._yr(state, D // YEAR)
    pyr["pd"][o["taker"]] = pyr["pd"].get(o["taker"], 0) + 1
    yr = _yr(state, D // YEAR)
    yr["carry"] += 1
    yr["pd"][o["taker"]] = yr["pd"].get(o["taker"], 0) + 1
    yr["coal" if o["want"] == "燃える石" else "planks"] = round(yr["coal" if o["want"] == "燃える石" else "planks"] + o["n"], 2)
    t.setdefault("events", []).append(log(state, p4.EV, name, f"{name} が、{o['taker']}の{o['want']} {o['n']} {unit(o['want'])} を背負って川を下り、{TOWN}に渡して、"
                                                               f"{TOOL}を {o['pn']} 本受けた", order=o["id"], household=o["taker"], town=True))
    p4._fulfil(state, o)
    if name in g4["work"]:
        p4._restore(state, name, w)
        g4["work"].pop(name)


def count_work(state, o, act, give):
    """町の頼みの仕事の 1 日 (p4.work_day から): 人日を数える"""
    yr = _yr(state, state["day"] // YEAR)
    yr["pd"][o["taker"]] = yr["pd"].get(o["taker"], 0) + 1


def pay(state, o):
    """果たした町の頼み (p4._fulfil から): 鉄の鎌を受けた家に"""
    g, D = _g(state), state["day"]
    tl = g["tools"].setdefault(o["taker"], [])
    for _ in range(int(o["pn"])):
        tl.append({"id": f"K{g['next_tool']}", "day": D, "uses": 0, "order": o["id"]})
        g["next_tool"] += 1
    yr = _yr(state, D // YEAR)
    yr["paid"] += int(o["pn"])
    yr["done"] += 1
    _reach(state, "F2", f"{o['taker']}が {TOWN}の頼み {o['id']} を運んで、{TOOL}を {o['pn']} 本受けた")


def took(state, o):
    """町の頼みを受けた (帳と年の行。p4.take_orders のあと、book から数える)"""
    _reach(state, "F1", f"{o['taker']}が {TOWN}の頼み {o['id']} を受けた")


# ---------------- c 鉄の鎌 (era2._field_work から。g7.t5_harvest) ----------------

def tools_of(state, h):
    return list(_g(state)["tools"].get(h) or []) if h else []


def harvest(state, p, n):
    """昼の畑仕事で実った畑を刈る 1 日: 家に今日まだ使っていない鉄の鎌があれば 1 本使って 1.3 倍 (古い鎌から)。戻り値: 刈った量"""
    g, D = _g(state), state["day"]
    h = p.get("household")
    if g["reap_day"].get("day") != D:
        g["reap_day"] = {"day": D, "used": []}
    used = g["reap_day"]["used"]
    tool = next((x for x in tools_of(state, h) if x["id"] not in used), None)
    if tool is None:
        return era2._harvest(state, p, n)
    got = era2._harvest(state, p, int(n * REAP_MULT))
    if got <= 0:
        return got
    used.append(tool["id"])
    tool["uses"] += 1
    extra = max(0, got - n)
    yr = _yr(state, D // YEAR)
    yr["reap_uses"] += 1
    yr["reap_extra"] += extra
    yr["reap_house"][h] = yr["reap_house"].get(h, 0) + extra
    _reach(state, "F3", f"{p['name']} ({h}) が {TOOL}で刈った")
    if tool["uses"] >= LIFE:
        g["tools"][h] = [x for x in g["tools"][h] if x["id"] != tool["id"]]
        if not g["tools"][h]:
            g["tools"].pop(h)
        g["worn"] = (g["worn"] + [dict(tool, house=h, gone=D)])[-80:]
        yr["worn"] += 1
        log(state, "道具", p["name"], f"{h}の{TOOL} [{tool['id']}] は、刈る日に {LIFE} 日使って傷み、使えなくなった", tool=tool["id"], household=h)
        _reach(state, "F4", f"{h}の{TOOL} [{tool['id']}] が傷んだ")
    return got


# ---------------- 季節の終わり・年の終わり (g7.season_end。p4 のあと) ----------------

def season_end(state):
    g, D = _g(state), state["day"]
    if (D + 1) % SEASON_DAYS:
        return
    y = str(D // YEAR)
    sd = era2.store_days(state)
    g["store_min"][y] = min(g["store_min"].get(y, sd), sd)
    if (D + 1) % YEAR == 0:
        year_end(state)
    post(state)


def _town_book(state):
    g4 = _p4g(state)
    return [o for o in g4["book"] if o.get("town")]


def row_of(state, y):
    g, g4 = _g(state), _p4g(state)
    yr = g["yr"].get(str(y)) or _yr(state, y)
    tb = _town_book(state)
    done = [o for o in tb if o["status"] == "果たした" and o.get("end_y") == y]
    failed = [o for o in tb if o["status"] == "果たせなかった" and o.get("end_y") == y]
    gone = [o for o in g4["gone"] if o.get("town") and o.get("end_y") == y]
    taken = [o for o in tb if (o.get("taken", 0) + 1) // YEAR == y]
    takers = sorted({o["taker"] for o in done})
    ppd = ((g4["yr"].get(str(y)) or {}).get("pd") or {})
    t2 = sorted((h for h, d in ppd.items() if d >= T2_DAYS), key=lambda h: (-ppd[h], h))
    w, nf = _s4().work_days(state)
    t3 = round(nf / w, 4) if w else 0.0
    ads = era2.adults(state)
    rd = g10.readers(state)
    rshare = round(len(rd) / len(ads), 4) if ads else 0.0
    famine = sum(1 for e in state["events"] if e["day"] // YEAR == y and e["type"] == "蓄えが尽きる")
    pop = len([p for p in state["people"] if p["alive"]])
    smin = g["store_min"].get(str(y), era2.store_days(state))
    s3g = (state["era2"]["g7"].get("s3") or {})
    tools_now = {h: len(v) for h, v in sorted(g["tools"].items()) if v}
    return {"year": y, "posted": yr["posted"], "posted_tools": yr["posted_tools"], "taken": len(taken), "done": len(done), "takers": takers, "taker_n": len(takers),
            "failed": len(failed), "gone": len(gone), "stock": round(sum(o.get("stock", 0) for o in done)), "town_pd": sum(yr["pd"].values()),
            "town_pd_houses": dict(sorted(yr["pd"].items())), "carry": yr["carry"], "coal": round(yr["coal"]), "planks": round(yr["planks"], 1),
            "paid": yr["paid"], "worn": yr["worn"], "tools_now": sum(tools_now.values()), "tool_houses": len(tools_now),
            "reap_uses": yr["reap_uses"], "reap_extra": yr["reap_extra"], "days_saved": round(yr["reap_extra"] / BASE_REAP, 1),
            "pd_houses": dict(sorted(ppd.items())), "t2_houses": t2, "t2_n": len(t2), "worked": w, "nonfood": nf, "t3_share": t3,
            "fire_pd": round(((s3g.get("fire") or {}).get(str(y)) or {}).get("hours", 0) / _s3().PD_H),
            "house_coal": round(sum((s3g.get("hcoal") or {}).values())), "readers": len(rd), "adults": len(ads), "r_share": rshare,
            "store_min": smin, "store_end": era2.store_days(state), "famine": famine, "pop": pop, "pop0": g["pop0"],
            "t1_like": len(done) >= T1_DONE and len(takers) >= T1_HOUSES, "t2_like": len(t2) >= T2_HOUSES,
            "t3_ok": t3 >= T3_SHARE, "t4_ok": famine == 0 and smin >= T4_STORE and pop >= T4_POP * g["pop0"] and rshare >= T4_READERS}


def year_end(state):
    g, D = _g(state), state["day"]
    y = D // YEAR
    if y < g["start_year"] or str(y) in g["rows"]:
        return
    r = g["rows"][str(y)] = row_of(state, y)
    for k in ("t1", "t2"):
        if r[f"{k}_like"] and y not in g["f_years"][k]:
            g["f_years"][k].append(y)
    if not r["t4_ok"] and y not in g["t4_broken"]:
        g["t4_broken"].append(y)


def entrance(state):
    """入口: いちばん新しい 2 年に、t1 と t2 がつづき、その 2 年に t3 と t4 を割らない"""
    g = _g(state)
    if not g["rows"]:
        return False
    y = max(int(k) for k in g["rows"])
    ys = [g["rows"].get(str(y - i)) for i in range(T_YEARS)]
    if not all(ys):
        return False
    return all(r["t1_like"] and r["t2_like"] and r["t3_ok"] and r["t4_ok"] for r in ys)


def check(state, done):
    """g7.check から (季節の終わり): 止まるわけ (なければ None)。i4 の止まりは、読める大人が 1 人以下だけ (i4 は閉じた)。P4 の入口と相談は閉じた"""
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
    if entrance(state) and not any(c["why"] == "t5_entrance" for c in done):
        return {"why": "t5_entrance", "year": y, "day": D, "text": f"T5: 入口に着いた ({y - 1}年と{y}年に t1・t2。その 2 年に t3・t4 を割らなかった)"}
    if r and not r["t4_ok"] and not any(c["why"] == "t5_safe" and c.get("year") == y for c in done):
        return {"why": "t5_safe", "year": y, "day": D, "text": f"T5: {y}年に t4 (暮らしを守る) を割った (ききん {r['famine']}・蓄えのいちばん少ない日 {r['store_min']} 日分・"
                f"人 {r['pop']} (はじめ {r['pop0']} の {round(T4_POP * 100)}% は {math.ceil(T4_POP * r['pop0'])})・読める大人 {round(r['r_share'] * 100, 1)}%)"}
    ys = [g["rows"].get(str(y - i)) for i in range(ZERO_YEARS)]
    if all(x and x["done"] == 0 for x in ys) and not any(c["why"] == "t5_zero" and c.get("year") == y for c in done):
        return {"why": "t5_zero", "year": y, "day": D, "text": f"T5: 果たした川下の町の頼みが {ZERO_YEARS} 年つづけて 0"}
    n = y - g["start_year"] + 1
    if n > 0 and n % LATER_YEARS == 0 and not any(c["why"] == f"t5_years_{y}" for c in done):
        return {"why": f"t5_years_{y}", "year": y, "day": D, "text": f"T5: 川下の町と鉄の道具に入って {n} 年たった (3 年ごとの相談)"}
    return None


# ---------------- お題 (知らせ板の節の中、p4 の頼み書きの行のあと) ----------------

def town_rows(state, p, answer=True):
    i4 = _i4()
    g, D = _g(state), state["day"]
    name, h = p["name"], p.get("household")
    me, fam = i4.can_read(state, p)
    if not (me or fam):
        return [f"- {TOWN}が、燃える石と板を{TOOL}で払う頼みを出していると聞いた (家に読める大人がいないので、受けられない)"]
    a, b = BASE_REAP, int(BASE_REAP * REAP_MULT)
    rows = [f"{TOWN}の頼み (町の人が板に書く。払いは{TOOL}):",
            f"- {TOOL} (川下の町で作った黒い金属の鎌。家のもの): 昼の畑仕事で刈る日、1 人 1 日 {a} → {b} つかみ (同じ量を 約 4 分の 3 の日数で刈れる)。刈る日に {LIFE} 日使うと傷んで使えない"]
    tl = tools_of(state, h)
    ly = (D + 1) // YEAR - 1
    ex = ((g["yr"].get(str(ly)) or {}).get("reap_house") or {}).get(h, 0)
    rows.append(f"- あなたの家の{TOOL} {len(tl)} 本" + (f" (刈る日 のこり {sum(LIFE - x['uses'] for x in tl)} 日分)" if tl else "")
                + f"・去年それで多く刈った草の種 {ex} つかみ")
    if not answer:
        return rows
    rows.append(f"- 受け方は \"take\" のまま。物がそろったら、はじめに名を書いた人が町へ運ぶ (川を下って 1 日)。運んだ日に鎌は受けた家のもの")
    tw = [o for o in p4.board_now(state) if o.get("town")]
    if tw:
        o = tw[-1]  # いちばん前から板にある町の頼み
        if o["want"] == "燃える石":
            kg = _s4().dig_kg_now(state)
            tail = f"燃える石 {o['n']} kg = 掘り場で掘る {math.ceil(o['n'] / max(1, kg))} 人日"
        else:
            tail = f"板 {o['n']} 束 = 水の作業場で働いてひく"
        rows.append(f"- 例: \"take\": {{\"頼み\": {o['id']}, \"人\": [\"{name}\"]}} ({tail})")
    return rows


def board_block(state, p, answer=True):
    """p4 の知らせ板の節 (知らせ・頼み書き) のあとに、町の頼みの行を足す"""
    base = p4.board_block(state, p, answer)
    if not base or not p:
        return base
    rows = town_rows(state, p, answer)
    return base + "\n".join(rows) + "\n" if rows else base


# ---------------- step.py status・年報 (村の人のお題には出さない) ----------------

def row_text(r):
    return (f"{r['year']}年: 果たした町の頼み {r['done']} (受けた家 {r['taker_n']}) / 出した {r['posted']} 枚 (鎌 {r['posted_tools']} 本)・受けた {r['taken']}・果たせなかった {r['failed']}・消えた {r['gone']} / "
            f"町に渡した 燃える石 {r['coal']} kg・板 {r['planks']} 束 (家の倉から {r['stock']})・町の頼みの仕事 {r['town_pd']} 人日 (運ぶ {r['carry']}) / "
            f"30 人日の家 {r['t2_n']} / 鉄の鎌 払った {r['paid']}・傷んだ {r['worn']}・いま {r['tools_now']} 本 ({r['tool_houses']} 家)・刈った日 {r['reap_uses']}・"
            f"多く刈った {r['reap_extra']} つかみ (刈る {r['days_saved']} 日分) / 食べ物でない仕事 {round(r['t3_share'] * 100, 1)}% / "
            f"蓄え いちばん少ない {r['store_min']} 日分・ききん {r['famine']}・人 {r['pop']} (はじめ {r['pop0']})・読める大人 {round(r['r_share'] * 100, 1)}% / "
            + f"t1 {'○' if r['t1_like'] else '×'} t2 {'○' if r['t2_like'] else '×'} t3 {'○' if r['t3_ok'] else '×'} t4 {'○' if r['t4_ok'] else '×'}")


def lines(state):
    if not on(state):
        return []
    g = _g(state)
    tb = _town_book(state)
    out = [f"{g['why']}。{g['day']} 日目から ({g['start_year']}年から数える。P4 の入口と相談は閉じた)。板の町の頼み {len(town_open(state))}・"
           f"受けている町の頼み {len([o for o in tb if o['status'] in p4.ACTIVE])}・家にある{TOOL} {sum(len(v) for v in g['tools'].values())} 本"
           + " / " + " / ".join(f"{k} {FS[k]} {_yd(g['f'][k]) if k in g['f'] else 'まだ'}" for k in FS)
           + f" / t4 を割った年 {'・'.join(map(str, g['t4_broken'])) or 'なし'} / 入口 {'○' if entrance(state) else 'まだ'}"]
    for y in sorted(g["rows"], key=int)[-3:]:
        out.append(row_text(g["rows"][y]))
    return out


def orders_of(state, y):
    """y 年に出した町の頼み (年報)"""
    g4 = _p4g(state)
    allo = {o["id"]: o for o in g4["gone"] + g4["book"] + g4["orders"] if o.get("town")}
    return [allo[k] for k in sorted(allo) if allo[k]["year"] == y]


def book_of(state, y):
    return [o for o in p4.book_of(state, y) if o.get("town")]
