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
- 直し 1 (2026-11-22。T5_design.md 7.): 印 g7.t5.fix1 (step.py resume --t5fix "<本人の言葉>" だけが書く。28679 日目 (238年の終わり) の T5 の相談から) のあとだけ、
  町の払いを鎌から「子の病の手当て」に変える。新しい町の頼みの払いは 子の薬 (包み。0〜4 歳の子 1 人の 1 季節分。その季節の死の見込み × 0.7) と、
  手当ての書きつけ (果たした家に 1 枚。家に読める大人がいるあいだ、家の 0〜4 歳の子みなの死の見込み × 0.85)。板の上の町の頼みも、印の日に払いを書きかえる。
  家にある鎌はそのまま使える。お題に去年亡くなった 0〜4 歳の子 (村と家) を出す。物差しに h1 (手当てが届いた子) を足す。相談は 239年から数えなおす。
  印がなければ前と 1 バイトも同じ (era2 の子の死は、印 fix1 があるときだけ t5.care を呼ぶ。乱数を引く回数は同じ)
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
# 直し 1【仮定】(印 g7.t5.fix1 のあとだけ。T5_design.md 7.)
FIX1_FROM = 28679  # 本物の村が 238年を終えて T5 の相談「2 年 0」で止まった日。これより前には印を書けない
FIX1_DATE = "2026-11-22"
FIX1_NAME = "町の払いの直し 1 (鎌から子の病の手当て (子の薬と手当ての書きつけ) に)"
MED, MED_UNIT = "子の薬", "包み"  # 川下の町の薬師が干した草の根と葉で作る包み (家のもの)
SHEET = "手当ての書きつけ"  # 町が、頼みを果たした家に 1 枚渡す書きつけ (家のもの。家に読める大人がいるあいだ効く)
MED_KINDS = (("燃える石", 2500, 4), ("板", 8, 4), ("燃える石", 5000, 8))  # (ほしい物, 数, 払う包み)。鎌 1 本 = 4 包み
MED_PER_TOOL = 4  # 印の日に板の上の町の頼みを書きかえるとき: 鎌 1 本 → 4 包み
MED_YEAR = 48  # 町が 1 年に頼みに書く包みの上 (鎌 12 本の 4 倍)
MED_MULT = 0.7  # 薬: 0〜4 歳の子 1 人の、その季節の死の見込み × 0.7 (1 包み = 1 人 1 季節。家のいちばん小さい子から)
SHEET_MULT = 0.85  # 書きつけ: 家に読める大人がいるあいだ、家の 0〜4 歳の子みな × 0.85 (薬とあわせて × 0.595)
CARE_AGE = 5  # 0〜4 歳
AVG_YEARS = 5  # お題の「ならした数」: 去年までの 5 年 (記録のある年だけ) の 1 年あたり (1 年ごとの数は大きくゆれるので)
H1_CS, H1_HOUSES = 40, 2  # h1: 手当て (薬か書きつけ) が届いた 0〜4 歳の子 (子 × 季節) 40 以上・家 2 以上
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


# ---------------- 直し 1 (step.py resume --t5fix。T5_design.md 7.) ----------------

def fixed(state):
    """直し 1 の印 g7.t5.fix1 があるか"""
    return on(state) and "fix1" in _g(state)


def fix1_year(state):
    return _g(state)["fix1"]["start_year"] if fixed(state) else None


def fix1_why(words):
    return f"{FIX1_NAME} (本人の言葉 {FIX1_DATE} 「{words}」)"


def fix1_refusal(state, words):
    """resume --t5fix ができないわけ (できるなら None)"""
    if not (words or "").strip():
        return "--t5fix には本人の言葉が要る"
    if not on(state):
        return "T5 の印がないので、直し 1 はつけられない"
    if "fix1" in _g(state):
        return "直し 1 はもうつけてある"
    if state["day"] < FIX1_FROM:
        return f"直し 1 は {FIX1_FROM} 日目 (238年の終わり) からだけ"
    h = (state["era2"]["g7"].get("hold") or {})
    if not (h.get("why") == "consult" and str(h.get("what", "")).startswith("T5:")):
        return "直し 1 は、T5 の相談 (HOLD consult) で止まっているときだけつける"
    if g15.push_on(state):
        return "後押しが動いている"
    return None


def _cyr(state, y):
    """直し 1 の年の帳 (g7.t5.care.yr。印のない行 (_yr) には足さない)"""
    return _g(state)["care"]["yr"].setdefault(str(y), {"posted_meds": 0, "paid_meds": 0, "sheets_given": 0, "used": 0, "med_cs": 0, "sheet_cs": 0, "care_cs": 0,
                                                       "u5_cs": 0, "saved": 0.0, "care_dead": 0, "care_houses": [], "dead": {}, "births": None})


def _u5_dead_of(state, y):
    """y 年の出来事から、亡くなった 0〜4 歳の子 (家 → 名) と生まれた子の数を読む (印の日に、去年の分を 1 回だけ)"""
    hh = {p["name"]: p.get("household") for p in state["people"]}
    dead, births = {}, 0
    for e in state["events"]:
        if e["day"] // YEAR != y:
            continue
        if e["type"] == "生まれる":
            births += 1
        elif e["type"] == "死" and e.get("who") and e["text"].startswith(f"{e['who']} (") and e["text"].endswith(" 歳) が亡くなった"):
            a = e["text"][len(e["who"]) + 2:-len(" 歳) が亡くなった")]
            if a.isdigit() and int(a) < CARE_AGE:
                dead.setdefault(hh.get(e["who"]) or "-", []).append(e["who"])
    return dead, births


def mark_fix1(state, words):
    """resume --t5fix から: 印 g7.t5.fix1 を書き、板の上の町の頼みの払いを子の薬に書きかえ、去年亡くなった 0〜4 歳の子を帳に写す (村の出来事には残さない)"""
    words = words.strip()
    g, D = _g(state), state["day"]
    f = g["fix1"] = {"day": D, "words": words, "why": fix1_why(words), "start_year": D // YEAR + 1}
    g["care"] = {"meds": {}, "sheets": {}, "kind": 0, "yr": {}}
    for o in town_open(state):
        if o.get("pay") == TOOL:
            o["was"] = {"pay": o["pay"], "pn": o["pn"]}
            o["pay"], o["pn"] = MED, int(o["pn"]) * MED_PER_TOOL
            if o["year"] >= f["start_year"]:
                _yr(state, o["year"])["posted_tools"] -= o["was"]["pn"]
                _cyr(state, o["year"])["posted_meds"] += o["pn"]
    y = D // YEAR
    for yy in range(y - AVG_YEARS + 1, y + 1):  # 去年までの 5 年 (state の出来事に残っている年だけ。古い年はしまってあるので、本物の村では 236〜238年)
        dead, births = _u5_dead_of(state, yy)
        if births or dead or yy == y:
            c = _cyr(state, yy)
            c["dead"], c["births"] = dead, births
    return f


# ---------------- 直し 1: 子の手当て (era2 の季節の終わりの子の死から。g7.t5_care) ----------------

def _base_p(c):
    return 0.06 if c["age"] < 1 else 0.015  # era2 の子の死 (0 歳 1 季節 0.06・1〜4 歳 0.015) と同じ数


def care(state, kids, sick, frac):
    """子の死の見込みを引く前に: 0〜4 歳の子ごとの手当ての掛け目 {名: 掛け目}。薬は家のいちばん小さい子から 1 人 1 包み使う (乱数は使わない)"""
    g, D = _g(state), state["day"]
    cg = g["care"]
    c = _cyr(state, D // YEAR)
    i4 = _i4()
    by = {}
    for k in kids:
        if k["age"] < CARE_AGE:
            by.setdefault(k.get("household") or "-", []).append(k)
    out = {}
    for h in sorted(by):
        ks = sorted(by[h], key=lambda k: (-k["born_day"], k["name"]))
        sheet = h in cg["sheets"] and bool(i4.house_readers(state, h))
        meds = cg["meds"].get(h, 0)
        for k in ks:
            m = 1.0
            if meds > 0:
                m *= MED_MULT
                meds -= 1
                c["used"] += 1
                c["med_cs"] += 1
            if sheet:
                m *= SHEET_MULT
                c["sheet_cs"] += 1
            c["u5_cs"] += 1
            if m < 1:
                out[k["name"]] = m
                c["care_cs"] += 1
                if h not in c["care_houses"]:
                    c["care_houses"].append(h)
                if k["hunger"] < 0.9:
                    c["saved"] = round(c["saved"] + _base_p(k) * sick * (1 - m) * frac, 4)
        if meds:
            cg["meds"][h] = meds
        else:
            cg["meds"].pop(h, None)
    return out


def care_after(state, plan, kids):
    """子の死の見込みを引いたあと: 亡くなった 0〜4 歳の子を家ごとに帳へ (お題の「去年亡くなった子」)"""
    c = _cyr(state, state["day"] // YEAR)
    for k in kids:
        if k["age"] < CARE_AGE and not k["alive"]:
            c["dead"].setdefault(k.get("household") or "-", []).append(k["name"])
            if k["name"] in plan:
                c["care_dead"] += 1


def meds_of(state, h):
    return int(_g(state)["care"]["meds"].get(h, 0)) if h and fixed(state) else 0


def u5_of(state, h):
    return sorted((p for p in era2.children(state) if p.get("household") == h and p["age"] < CARE_AGE), key=lambda k: (-k["born_day"], k["name"])) if h else []


def _rate_avg(cg, y):
    """0〜4 歳の死 (子 千人・年あたり) を、y 年までの 5 年 (手当ての帳のある年だけ) でならした数"""
    cs = [cg["yr"][str(x)] for x in range(y - AVG_YEARS + 1, y + 1) if (cg["yr"].get(str(x)) or {}).get("u5_cs")]
    n = sum(c["u5_cs"] for c in cs)
    return round(1000 * sum(sum(len(v) for v in c["dead"].values()) for c in cs) / (n / 4), 1) if n else None


def care_row(state, y):
    """直し 1 の年の行 (h1 と、子の手当ての記録)"""
    cg = _g(state)["care"]
    c = cg["yr"].get(str(y)) or _cyr(state, y)
    dead = sum(len(v) for v in c["dead"].values())
    ch = sorted(c["care_houses"])
    u5 = [p for p in era2.children(state) if p["age"] < CARE_AGE]
    i4 = _i4()
    sh = sorted(h for h in cg["sheets"] if i4.house_readers(state, h))
    return {"posted_meds": c["posted_meds"], "paid_meds": c["paid_meds"], "sheets_given": c["sheets_given"], "meds_used": c["used"],
            "med_cs": c["med_cs"], "sheet_cs": c["sheet_cs"], "care_cs": c["care_cs"], "u5_cs": c["u5_cs"], "care_houses": ch, "care_house_n": len(ch),
            "saved": round(c["saved"], 2), "u5_dead": dead, "care_dead": c["care_dead"], "births": c["births"],
            "u5_rate": round(1000 * dead / (c["u5_cs"] / 4), 1) if c["u5_cs"] else None, "u5_now": len(u5),
            "u5_rate_avg": _rate_avg(cg, y), "saved_sum": round(sum((cg["yr"].get(str(x)) or {}).get("saved", 0.0) for x in range(fix1_year(state), y + 1)), 2),
            "meds_now": sum(cg["meds"].values()), "med_houses": len(cg["meds"]), "sheet_houses": len(sh), "sheet_all": len(cg["sheets"]),
            "h1_like": c["care_cs"] >= H1_CS and len(ch) >= H1_HOUSES}


# ---------------- a 町の頼み ----------------

def town_open(state):
    return [o for o in _p4g(state)["orders"] if o.get("town")]


def post(state):
    """板の上の町の頼みが TOWN_OPEN 枚になるまで、次の種類の頼みを出す (その季節が入る暦の年に、町が書く鎌は TOOLS_YEAR 本まで)"""
    g, g4, D = _g(state), _p4g(state), state["day"]
    y = (D + 1) // YEAR
    yr = _yr(state, y)
    out = []
    fix = fixed(state)
    while len(town_open(state)) < TOWN_OPEN:
        if fix:  # 直し 1: 払いは子の薬 (と書きつけ)。1 年に 48 包みまで
            cg, c = g["care"], _cyr(state, y)
            want, n, pn = MED_KINDS[cg["kind"] % len(MED_KINDS)]
            if c["posted_meds"] + pn > MED_YEAR:
                break
            cg["kind"] += 1
            c["posted_meds"] += pn
        else:
            want, n, pn = KINDS[g["kind"] % len(KINDS)]
            if yr["posted_tools"] + pn > TOOLS_YEAR:
                break
            g["kind"] += 1
        r = {"id": g4["next_id"], "day": D, "year": y, "season": p4._sl(D + 1), "house": TOWN, "by": TOWN, "writer": None, "want": want, "n": n,
             "pay": MED if fix else TOOL, "pn": pn, "escrow": 0, "status": "板", "town": True}
        g4["next_id"] += 1
        g4["orders"].append(r)
        while len(g4["orders"]) > p4.BOARD_MAX:
            p4._drop(state, g4["orders"][0], "板がいっぱいで、古い頼みから消えた")
        yr["posted"] += 1
        if not fix:
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
    if o.get("pay") == MED:  # 直し 1: 子の薬 (と、はじめての家には書きつけ)
        got = f"{MED}を {o['pn']} {MED_UNIT}" + ("" if o["taker"] in _g(state)["care"]["sheets"] else f"と、{SHEET}を") + "受けた"
    else:
        got = f"{TOOL}を {o['pn']} 本受けた"
    t.setdefault("events", []).append(log(state, p4.EV, name, f"{name} が、{o['taker']}の{o['want']} {o['n']} {unit(o['want'])} を背負って川を下り、{TOWN}に渡して、"
                                                               + got, order=o["id"], household=o["taker"], town=True))
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
    if o.get("pay") == MED:  # 直し 1: 子の薬を受けた家に。書きつけは、まだない家に 1 枚
        cg, c = g["care"], _cyr(state, D // YEAR)
        h = o["taker"]
        cg["meds"][h] = cg["meds"].get(h, 0) + int(o["pn"])
        c["paid_meds"] += int(o["pn"])
        if h not in cg["sheets"]:
            cg["sheets"][h] = D
            c["sheets_given"] += 1
        _yr(state, D // YEAR)["done"] += 1
        _reach(state, "F5", f"{h}が {TOWN}の頼み {o['id']} を運んで、{MED}を {o['pn']} {MED_UNIT}受けた")
        return
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
            "t3_ok": t3 >= T3_SHARE, "t4_ok": famine == 0 and smin >= T4_STORE and pop >= T4_POP * g["pop0"] and rshare >= T4_READERS,
            **(care_row(state, y) if fixed(state) and y >= fix1_year(state) else {})}


def year_end(state):
    g, D = _g(state), state["day"]
    y = D // YEAR
    if y < g["start_year"] or str(y) in g["rows"]:
        return
    if fixed(state) and y >= fix1_year(state):  # 直し 1: 生まれた子の数 (この年の出来事から)
        _cyr(state, y)["births"] = sum(1 for e in state["events"] if e["day"] // YEAR == y and e["type"] == "生まれる")
    r = g["rows"][str(y)] = row_of(state, y)
    for k in ("t1", "t2") + (("h1",) if "h1_like" in r else ()):
        if r[f"{k}_like"] and y not in g["f_years"].setdefault(k, []):
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
    if fixed(state):  # 直し 1: 入口は直しの年から数え、h1 (手当てが届いた子) もそろう 2 年
        return all(r["year"] >= fix1_year(state) and r.get("h1_like") and r["t1_like"] and r["t2_like"] and r["t3_ok"] and r["t4_ok"] for r in ys)
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
    fix = fixed(state)
    if entrance(state) and not any(c["why"] == "t5_entrance" for c in done):
        return {"why": "t5_entrance", "year": y, "day": D, "text": f"T5: 入口に着いた ({y - 1}年と{y}年に t1・t2{'・h1' if fix else ''}。その 2 年に t3・t4 を割らなかった)"}
    if r and not r["t4_ok"] and not any(c["why"] == "t5_safe" and c.get("year") == y for c in done):
        return {"why": "t5_safe", "year": y, "day": D, "text": f"T5: {y}年に t4 (暮らしを守る) を割った (ききん {r['famine']}・蓄えのいちばん少ない日 {r['store_min']} 日分・"
                f"人 {r['pop']} (はじめ {r['pop0']} の {round(T4_POP * 100)}% は {math.ceil(T4_POP * r['pop0'])})・読める大人 {round(r['r_share'] * 100, 1)}%)"}
    ys = [g["rows"].get(str(y - i)) for i in range(ZERO_YEARS)]
    if fix:  # 直し 1: 「2 年 0」は直しの年 (239年) から数える
        ys = [x if x and x["year"] >= fix1_year(state) else None for x in ys]
    if all(x and x["done"] == 0 for x in ys) and not any(c["why"] == "t5_zero" and c.get("year") == y for c in done):
        return {"why": "t5_zero", "year": y, "day": D, "text": f"T5: 果たした川下の町の頼みが {ZERO_YEARS} 年つづけて 0" + (f" ({fix1_year(state)}年の直し 1 のあと)" if fix else "")}
    if fix:  # 直し 1: 3 年ごとの相談は直しの年から数える (239・240・241年 → 241年の終わり)
        n = y - fix1_year(state) + 1
        if n > 0 and n % LATER_YEARS == 0 and not any(c["why"] == f"t5_years_{y}" for c in done):
            return {"why": f"t5_years_{y}", "year": y, "day": D, "text": f"T5: 町の払いを子の手当てにして {n} 年たった (3 年ごとの相談)"}
        return None
    n = y - g["start_year"] + 1
    if n > 0 and n % LATER_YEARS == 0 and not any(c["why"] == f"t5_years_{y}" for c in done):
        return {"why": f"t5_years_{y}", "year": y, "day": D, "text": f"T5: 川下の町と鉄の道具に入って {n} 年たった (3 年ごとの相談)"}
    return None


# ---------------- お題 (知らせ板の節の中、p4 の頼み書きの行のあと) ----------------

def _per(p):
    """1 年 (4 季節) に亡くなる見込み → 「約 N 人に 1 人」"""
    q = 1 - (1 - p) ** 4
    return f"約 {round(1 / q)} 人に 1 人"


def care_rows(state, p, answer=True):
    """直し 1 のお題の行 (町の頼みの払いは子の薬と手当ての書きつけ)"""
    i4 = _i4()
    g, D = _g(state), state["day"]
    name, h = p["name"], p.get("household")
    me, fam = i4.can_read(state, p)
    ly = (D + 1) // YEAR - 1
    c = g["care"]["yr"].get(str(ly)) or {}
    dd = c.get("dead") or {}
    mine = dd.get(h) or []
    dead = f"- 去年 ({ly}年)、村で亡くなった 0〜4 歳の子 {sum(len(v) for v in dd.values())} 人" + (f" (生まれた子 {c['births']} 人)" if c.get("births") is not None else "") \
        + "。あなたの家では " + (f"{len(mine)} 人 ({'・'.join(mine[:3])}{' ほか' if len(mine) > 3 else ''})" if mine else "0 人")
    ys = [x for x in range(ly - AVG_YEARS + 1, ly + 1) if (g["care"]["yr"].get(str(x)) or {}).get("births") is not None]
    if len(ys) >= 2:  # ならした数 (1 年ごとの数は大きくゆれる)
        cs = [g["care"]["yr"][str(x)] for x in ys]
        nd, nb = sum(sum(len(v) for v in c["dead"].values()) for c in cs), sum(c["births"] for c in cs)
        dead += f"。ならすと {ys[0]}〜{ys[-1]}年の {len(ys)} 年で 1 年 {round(nd / len(ys))} 人 (生まれた子 1 年 {round(nb / len(ys))} 人)"
    if not (me or fam):
        return [f"- {TOWN}が、燃える石と板を{MED}と{SHEET}で払う頼みを出していると聞いた (家に読める大人がいないので、受けられない)", dead]
    rows = [f"{TOWN}の頼み (町の人が板に書く。払いは{MED}と{SHEET}):",
            f"- {MED} (町の薬師が、干した草の根と葉で作る包み。家のもの): 1 包みで 0〜4 歳の子 1 人の 1 季節分。季節の終わりに家のいちばん小さい子から使い、"
            f"その季節に病で亡くなる見込みが 10 のうち {round((1 - MED_MULT) * 10)} へる",
            f"- {SHEET} (町の頼みを果たした家に 1 枚。家のもの): 家の読める大人が読んで、わかして冷ました水・塩を少し入れた薄いかゆ・体を冷やさない、を小さい子にする。"
            f"家に読める大人がいるあいだ、家の 0〜4 歳の子みな、病で亡くなる見込みが 10 のうち {round((1 - SHEET_MULT) * 10, 1)} へる (薬とあわせて 約 {round((1 - MED_MULT * SHEET_MULT) * 10)})",
            f"- 小さい子が 1 年に病で亡くなるのは、0 歳で{_per(0.06)}・1〜4 歳で{_per(0.015)} (病がはやる季節は 3 倍)",
            dead]
    ks = u5_of(state, h)
    sh = h in g["care"]["sheets"]
    rows.append(f"- あなたの家の 0〜4 歳の子 {len(ks)} 人・{MED} {meds_of(state, h)} {MED_UNIT}・{SHEET} " + ("あり" if sh else "なし")
                + (" (家に読める大人がいないので、いまは使えない)" if sh and not i4.house_readers(state, h) else ""))
    tl = tools_of(state, h)
    if tl:
        rows.append(f"- あなたの家の{TOOL} {len(tl)} 本 (刈る日 のこり {sum(LIFE - x['uses'] for x in tl)} 日分。昼の刈り入れ 1 人 1 日 {BASE_REAP} → {int(BASE_REAP * REAP_MULT)} つかみ)。町はもう鎌では払わない")
    if not answer:
        return rows
    rows.append(f"- 受け方は \"take\" のまま。物がそろったら、はじめに名を書いた人が町へ運ぶ (川を下って 1 日)。運んだ日に、薬と書きつけは受けた家のもの")
    tw = [o for o in p4.board_now(state) if o.get("town")]
    if tw:
        o = tw[-1]  # いちばん前から板にある町の頼み
        if o["want"] == "燃える石":
            kg = _s4().dig_kg_now(state)
            tail = f"燃える石 {o['n']} kg = 掘り場で掘る {math.ceil(o['n'] / max(1, kg))} 人日"
        else:
            tail = f"板 {o['n']} 束 = 水の作業場で働いてひく"
        rows.append(f"- 例: \"take\": {{\"頼み\": {o['id']}, \"人\": [\"{name}\"]}} ({tail}。{o['pay']} {o['pn']} {p4.PAY_UNIT.get(o['pay'], '')})")
    return rows


def town_rows(state, p, answer=True):
    if fixed(state):  # 直し 1
        return care_rows(state, p, answer)
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
            + f"t1 {'○' if r['t1_like'] else '×'} t2 {'○' if r['t2_like'] else '×'} t3 {'○' if r['t3_ok'] else '×'} t4 {'○' if r['t4_ok'] else '×'}"
            + (care_text(r) if "h1_like" in r else ""))


def care_text(r):
    """直し 1 の年の行の足し (h1 と子の手当て)"""
    return (f" h1 {'○' if r['h1_like'] else '×'} / 子の手当て: 手当てが届いた子 {r['care_cs']} 人・季節 ({r['care_house_n']} 家。薬 {r['med_cs']}・書きつけ {r['sheet_cs']}) / "
            f"子の薬 町が書いた {r['posted_meds']}・払った {r['paid_meds']}・使った {r['meds_used']}・いま {r['meds_now']} 包み ({r['med_houses']} 家)・書きつけ 渡した {r['sheets_given']} (読める家 {r['sheet_houses']}) / "
            f"亡くなった 0〜4 歳 {r['u5_dead']} 人 (手当てのあった子 {r['care_dead']})・生まれた子 {r['births']}・0〜4 歳 千人・年あたり {r['u5_rate']} (5 年でならして {r['u5_rate_avg']})・見込みで救えた子 {r['saved']} 人 (直しから {r['saved_sum']})")


def lines(state):
    if not on(state):
        return []
    g = _g(state)
    tb = _town_book(state)
    out = [f"{g['why']}。{g['day']} 日目から ({g['start_year']}年から数える。P4 の入口と相談は閉じた)。板の町の頼み {len(town_open(state))}・"
           f"受けている町の頼み {len([o for o in tb if o['status'] in p4.ACTIVE])}・家にある{TOOL} {sum(len(v) for v in g['tools'].values())} 本"
           + " / " + " / ".join(f"{k} {FS[k]} {_yd(g['f'][k]) if k in g['f'] else 'まだ'}" for k in FS)
           + f" / t4 を割った年 {'・'.join(map(str, g['t4_broken'])) or 'なし'} / 入口 {'○' if entrance(state) else 'まだ'}"]
    if fixed(state):
        f, cg = g["fix1"], g["care"]
        out.append(f"直し 1: {f['why']}。{f['day']} 日目から ({f['start_year']}年から数える。「2 年 0」と 3 年ごとの相談も)。家にある{MED} {sum(cg['meds'].values())} {MED_UNIT} ({len(cg['meds'])} 家)・"
                   f"{SHEET}のある家 {len(cg['sheets'])} / F5 はじめて{MED}を受けた {_yd(g['f']['F5']) if 'F5' in g['f'] else 'まだ'}")
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
