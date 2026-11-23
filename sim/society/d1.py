"""人口の決まりの直し 1 (案 A「大人の死を昔の村に近づける」。2026-11-22。docs/society_phase/A_design.md・A_projection.md・A_check.md)

- 印 state.era2.g7.d1 があるときだけ働く。印を書くのは step.py resume --d1 "<本人の言葉>" [--d1scen S2|S1] だけ
  (29039 日目 (241年の終わり) から。T5 の相談 (HOLD consult で what が「T5:」) で止まっているときだけ。1 回だけ)。
  印がなければ、このファイルは読みこみもしない (era2・g7・step.py・tools/year_report.py は「d1」の鍵があるときだけ読みこむ)。
  だから前の歩は、お題・state・出来事・乱数が 1 バイトも変わらない
- 印を書く日に g7.t5.closed も書く (フェーズ 5 の入口と相談を state の上で閉じる。川下の町の頼み・子の手当て・知らせ板・手習いは続く)
- 世界で変わるのは era2._season_end の 3 か所の見込み (p) だけ。くじを引く回数と順は同じ:
    子が生まれる 0.08 → birth (S2 0.045・S1 0.08) / 55 歳からの年寄りの死 × old (0.35) /
    病の死 15〜39 歳 0.0075 → a (0.0017)・40〜54 歳 0.0125 → b (0.0042)。子の死・病の季節の 3 倍・飢えなどは変えない
- 乱数は使わない。村の人のお題にも出来事にも、この直しのことは何も書かない (印・本人の言葉・作る側・物差し・昔の村の記録)
- 物差し (A_design.md 6.。前もって書いた線。途中で動かさない): d1 平均寿命 28〜40 歳・d2 15 歳の平均余命 38〜52 年・
  d3 自然増加 (5 年平均) S2 −0.5〜2.0%/年 [S1 1.0〜3.5]・d4 合計特殊出生率 S2 3.5〜5.0 [S1 6.0〜7.6]・d5 (守り) 年の終わりの蓄え 200 日分以上・ききん 0・
  d6 (見るだけ) ボズラップの目印。5 年まとめは区切りの年 (start_year) からの年だけで作る (5 年たつまでは短い)
  数え方: 季節の終わりごとに、生きている人 (この季節に生まれた子をのぞく) とこの季節に亡くなった人を年齢ごとに 1/4 年ずつ数え、
  出来事「死」「生まれる」から亡くなった人と母の年齢ごとの出生を数える (tools/projection_a.py と同じ形。統計のページの数は records の日ごとの数)
- 止めて相談 (A_design.md 7.): d5 を割った年・人が印のときの 95% を切った年・d1 か d4 が 2 年つづけて線の外・3 年ごと (区切りの年から数える)。
  読める大人が 1 人以下の止まり (i4) はそのまま
- 相談の直し 1 (2026-11-23。A_check.md 9.): 印 g7.d1.fix1 (step.py resume --d1fix "<本人の言葉>" だけが書く。29399 日目 (244年の終わり) の D1 の相談から。1 回だけ) の
  あとだけ、「d1 か d4 が 2 年つづけて線の外」の相談を 5 年まとめがそろう年 (区切りの年 + 4 = 246年の終わり) から見る (それより前の年は、この相談では止めない)。
  線・世界の見込み・数え方・ほかの相談 (蓄え・ききん・人 95%・3 年ごと) は変えない。印がなければ前と 1 バイトも同じ
- 蓄えの知らせ 1 (2026-11-23。A_check.md 10.): 印 g7.d1.info1 (step.py resume --d1info "<本人の言葉>" だけが書く。29879 日目 (248年の終わり) の D1 の相談から。1 回だけ) の
  あとだけ、お題の「## 村のようす」の「村の蓄え」の次に 1 行 (store_info) を足す: 年の終わりの蓄えのうつりかわり (日分) と、夏の刈り入れ (前の秋にまいた種の何倍か)。
  村の帳にある数だけ (知らせるだけ。すすめる言葉・作る側・印のことは書かない)。世界の決まり・乱数・相談は変えない。印がなければお題も前と 1 バイトも同じ
"""
import math

import era2
import g14
import g15

YEAR, SEASON_DAYS = era2.YEAR, era2.SEASON_DAYS
D1_FROM = 29039  # 本物の村が 241年を終えて T5 の相談 (3 年ごと) で止まった日。これより前には印を書けない
D1_DATE = "2026-11-22"
D1_NAME = "人口の決まりの直し 1 (案 A: 大人の死と生まれる見込みを昔の村に近づける)"
WHY_TAIL = "大人の死と生まれる見込みを、江戸時代の村の記録 (虎岩村・今浦など) に合わせた。A_projection.md"
# 筋 (tools/projection_a.py の SCEN と同じ数)。線 (d3・d4) は筋ごと
BASE = {"a": 0.0075, "b": 0.0125, "old": 1.0, "birth": 0.08}  # 今の決まり (era2._season_end。G7 の直し 7 のあと)
SCEN = {
    "S2": {"name": "大人の死と生まれる見込みを直す", "a": 0.0017, "b": 0.0042, "old": 0.35, "birth": 0.045, "d3": (-0.5, 2.0), "d4": (3.5, 5.0)},
    "S1": {"name": "大人の死を直す", "a": 0.0017, "b": 0.0042, "old": 0.35, "birth": 0.08, "d3": (1.0, 3.5), "d4": (6.0, 7.6)},
}
D1_E0 = (28.0, 40.0)  # d1 平均寿命 (見通しの S2 の 10〜90%。江戸の村は 33〜38 年)
D2_E15 = (38.0, 52.0)  # d2 15 歳の平均余命 (虎岩村 44〜45 年)
D5_STORE = 200  # d5 年の終わりの蓄え (日分) 以上・ききん 0
POP_KEEP = 0.95  # 人が印のときの 95% を切った年は止める
OUT_YEARS = 2  # d1 か d4 が 2 年つづけて線の外
LATER_YEARS = 3  # 3 年ごとの相談
# 相談の直し 1 (印 g7.d1.fix1 のあとだけ。A_check.md 9.)
FIX1_FROM = 29399  # 本物の村が 244年を終えて D1 の相談 (d1・d4 が 2 年つづけて線の外) で止まった日。これより前には印を書けない
FIX1_DATE = "2026-11-23"
FIX1_NAME = "人口の決まりの相談の直し 1 (d1・d4 の「2 年つづけて線の外」は 5 年まとめがそろってから見る)"
# 蓄えの知らせ 1 (印 g7.d1.info1 のあとだけ。A_check.md 10.)
INFO1_FROM = 29879  # 本物の村が 248年を終えて D1 の相談 (蓄えが 200 日分を切った) で止まった日。これより前には印を書けない
INFO1_DATE = "2026-11-23"
INFO1_NAME = "蓄えの知らせ 1 (お題の村のようすに、蓄えのうつりかわりと刈り入れの倍を 1 行)"
INFO_YEARS = 4  # 年の終わりの蓄え・夏の刈り入れを見せる年の数
WIN = 5  # 5 年まとめ
OLD_AGE = 55
AGE_GROUPS = [(0, 1), (1, 5)] + [(a, a + 5) for a in range(5, 60, 5)] + [(60, None)]  # tools/stats_calc.py の AGE_GROUPS と同じ
MOTHER = [(a, a + 5) for a in range(15, 50, 5)]  # 合計特殊出生率 (15〜49 歳の 5 歳きざみ)
DS = {"d1": "平均寿命", "d2": "15 歳の平均余命", "d3": "自然増加 (5 年平均)", "d4": "合計特殊出生率", "d5": "蓄え (守り)", "d6": "ボズラップの目印 (見るだけ)"}
# 書かない言葉 (tools/prompt_check.py --words d1。この直しには村の人に見せる節がないので、お題ぜんたい (FACT_HEADS の "" はどの行にも合う) で見る)。
# お題にもとからある言葉 (印のかたまりの「印」・「相談」・「本人」など) は入れない。それは「印のないお題とくらべてふえない」で見る (A_check.md)
SECTION = None
FACT_HEADS = ("",)
WORDS = ("作る側", "後押し", "反実仮想", "物差し", "Society", "D1", "d1", "案 A", "人口の決まり", "生まれる見込み", "昔の村", "江戸", "虎岩", "今浦", "二本松",
         "平均寿命", "平均余命", "合計特殊出生率", "生命表", "決まりを変え", "決まりを直", "ボズラップ")


def on(state):
    return "day" in ((((state.get("era2") or {}).get("g7") or {}).get("d1")) or {})


def _g(state):
    return state["era2"]["g7"]["d1"]


def _t5():
    import t5
    return t5


def _yd(day):
    return f"{day // YEAR}年{day % YEAR + 1}日目"


# ---------------- 世界の見込み (era2._season_end から。印のあとだけ) ----------------

def birth(state):
    """子が生まれる見込み (1 季節。era2 の BIRTH_P7 のかわり)"""
    return _g(state)["birth"]


def old(state):
    """55 歳からの年寄りの死の見込みに掛ける数"""
    return _g(state)["old"]


def adult(state, age):
    """15〜54 歳の病の死の見込み (1 季節。病の季節の 3 倍と frac は era2 で掛ける)"""
    g = _g(state)
    return g["a"] if age < 40 else g["b"]


# ---------------- 印 (step.py resume --d1) ----------------

def why_text(words):
    return f"作る側が変えた (本人の言葉 {D1_DATE} 「{words}」)。{WHY_TAIL}"


def refusal(state, words, scen="S2"):
    """resume --d1 ができないわけ (できるなら None)"""
    if not (words or "").strip():
        return "--d1 には本人の言葉が要る"
    if scen not in SCEN:
        return f"--d1scen は {'・'.join(SCEN)} のどれか"
    g7s = ((state.get("era2") or {}).get("g7") or {})
    if "d1" in g7s:
        return "人口の決まりの直し 1 はもうつけてある"
    if "t5" not in g7s or not _t5().on(state):
        return "T5 の印がないので、人口の決まりの直し 1 はつけられない"
    if state["day"] < D1_FROM:
        return f"人口の決まりの直し 1 は {D1_FROM} 日目 (241年の終わり) からだけ"
    h = g7s.get("hold") or {}
    if not (h.get("why") == "consult" and str(h.get("what", "")).startswith("T5:")):
        return "人口の決まりの直し 1 は、T5 の相談 (HOLD consult) で止まっているときだけつける"
    if g15.push_on(state):
        return "後押しが動いている"
    return None


def mark(state, words, scen="S2"):
    """resume --d1 から: 印 g7.d1 を書き、g7.t5.closed を書く (村の出来事には残さない。乱数は使わない)"""
    words = words.strip()
    D = state["day"]
    s = SCEN[scen]
    _t5()._g(state)["closed"] = D
    g = state["era2"]["g7"]["d1"] = {
        "day": D, "words": words, "why": why_text(words), "scen": scen, "a": s["a"], "b": s["b"], "old": s["old"], "birth": s["birth"],
        "start_year": D // YEAR + 1, "rows": {}, "f": {},
        "pop0": len([p for p in state["people"] if p["alive"]]), "tally_day": D, "demo": {}, "store_min": {}, "sow": {}}
    return g


# ---------------- 相談の直し 1 (step.py resume --d1fix。A_check.md 9.) ----------------

def fixed(state):
    """相談の直し 1 の印 g7.d1.fix1 があるか"""
    return on(state) and "fix1" in _g(state)


def fix1_why(words):
    return f"作る側が変えた (本人の言葉 {FIX1_DATE} 「{words}」)。{FIX1_NAME}。1〜3 年のまとめはゆれが大きく、線は 5 年まとめの幅なので。A_check.md 9."


def fix1_refusal(state, words):
    """resume --d1fix ができないわけ (できるなら None)"""
    if not (words or "").strip():
        return "--d1fix には本人の言葉が要る"
    if not on(state):
        return "人口の決まりの直し 1 の印 (g7.d1) がないので、相談の直し 1 はつけられない"
    if "fix1" in _g(state):
        return "相談の直し 1 はもうつけてある"
    if state["day"] < FIX1_FROM:
        return f"相談の直し 1 は {FIX1_FROM} 日目 (244年の終わり) からだけ"
    h = state["era2"]["g7"].get("hold") or {}
    if not (h.get("why") == "consult" and str(h.get("what", "")).startswith("D1:")):
        return "相談の直し 1 は、D1 の相談 (HOLD consult) で止まっているときだけつける"
    if g15.push_on(state):
        return "後押しが動いている"
    return None


def mark_fix1(state, words):
    """resume --d1fix から: 印 g7.d1.fix1 を書く (村の出来事には残さない。乱数は使わない。世界の見込みは変えない)"""
    words = words.strip()
    g = _g(state)
    f = g["fix1"] = {"day": state["day"], "words": words, "why": fix1_why(words), "out_from": g["start_year"] + WIN - 1}
    return f


# ---------------- 蓄えの知らせ 1 (step.py resume --d1info。A_check.md 10.) ----------------

def informed(state):
    """蓄えの知らせ 1 の印 g7.d1.info1 があるか"""
    return on(state) and "info1" in _g(state)


def info1_why(words):
    return (f"作る側が変えた (本人の言葉 {INFO1_DATE} 「{words}」)。{INFO1_NAME}。蓄えは 3 か所に今の日分だけが出ていて、うつりかわりと刈り入れの倍は出ていなかった。"
            "知らせるだけで、村の人の決めはそのまま。A_check.md 10.")


def info1_refusal(state, words):
    """resume --d1info ができないわけ (できるなら None)"""
    if not (words or "").strip():
        return "--d1info には本人の言葉が要る"
    if not on(state):
        return "人口の決まりの直し 1 の印 (g7.d1) がないので、蓄えの知らせ 1 はつけられない"
    if "info1" in _g(state):
        return "蓄えの知らせ 1 はもうつけてある"
    if state["day"] < INFO1_FROM:
        return f"蓄えの知らせ 1 は {INFO1_FROM} 日目 (248年の終わり) からだけ"
    h = state["era2"]["g7"].get("hold") or {}
    if not (h.get("why") == "consult" and str(h.get("what", "")).startswith("D1:")):
        return "蓄えの知らせ 1 は、D1 の相談 (HOLD consult) で止まっているときだけつける"
    if g15.push_on(state):
        return "後押しが動いている"
    return None


def mark_info1(state, words):
    """resume --d1info から: 印 g7.d1.info1 を書く (村の出来事には残さない。乱数は使わない。世界の決まりと相談は変えない)"""
    words = words.strip()
    f = _g(state)["info1"] = {"day": state["day"], "words": words, "why": info1_why(words)}
    return f


def _harvests(state):
    """夏の刈り入れ {年: (前の秋にまいた種, 刈れる量)}。秋にまいた畑 (実った・刈った) を、実る夏の年ごとに足す (era2._field_season の実り。落ちた分もふくむ)"""
    out = {}
    for f in state["era2"]["fields"]:
        if f["state"] in ("実った", "刈った") and era2.season(f["day"]) == "秋" and "yield" in f:
            y = f["day"] // YEAR + 1
            s, n = out.get(y, (0, 0))
            out[y] = (s + f["seed"], n + f["yield"])
    return out


def store_info(state):
    """お題の「## 村のようす」の「村の蓄え」の次の 1 行 (印 g7.d1.info1 のあとだけ。era2._village から)。村の帳にある数だけ"""
    if not informed(state):
        return ""
    g = _g(state)
    y_now = (state["day"] + 1) // YEAR  # これからの年 (年の終わりの日は、次の年)
    ends = [(int(y), r["store_end"]) for y, r in g["rows"].items() if int(y) < y_now][-INFO_YEARS:]
    ends.sort()
    hv = _harvests(state)
    ripe = {f["day"] // YEAR + 1 for f in state["era2"]["fields"] if f["state"] == "実った" and era2.season(f["day"]) == "秋"}
    ys = sorted(y for y in hv if y <= y_now)[-INFO_YEARS:]
    parts = []
    if ends:
        parts.append("年の終わりの村の蓄え " + "・".join(f"{y}年 {d} 日分" for y, d in ends) + " (1 年は 120 日)")
    if ys:
        parts.append("夏の刈り入れ " + "・".join(
            f"{y}年 {'いま実っている 約 ' if y in ripe else ''}{n} つかみ (前の秋にまいた {s} つかみの {round(n / s, 1) if s else 0} 倍)" for y, (s, n) in ((y, hv[y]) for y in ys)))
    return ("村の蓄えのうつりかわり: " + "。".join(parts) + "\n") if parts else ""


# ---------------- 数える (g7.season_end から。t5 のあと) ----------------

def _gi(age):
    for i, (lo, hi) in enumerate(AGE_GROUPS):
        if age >= lo and (hi is None or age < hi):
            return i
    return 0


def _demo(g, y):
    return g["demo"].setdefault(str(y), {"E": [0.0] * len(AGE_GROUPS), "D": [0] * len(AGE_GROUPS), "Ef": [0.0] * len(MOTHER), "B": [0] * len(MOTHER),
                                         "births": 0, "kid_dead": 0, "adult_dead": 0, "old_dead": 0, "famine": 0})


def _window_events(state, last, D):
    """出来事のうち、last より後・D までのもの (出来事は日の順に並んでいる。後ろから見る)"""
    out = []
    for e in reversed(state["events"]):
        if e["day"] <= last:
            break
        if e["day"] <= D:
            out.append(e)
    out.reverse()
    return out


def _workers(state):
    """働き手 (大人 + 12〜14 歳の子の半分。tools/projection_a.py と同じ形)"""
    return len(era2.adults(state)) + 0.5 * sum(1 for c in era2.children(state) if 12 <= c["age"] < 15)


def season_end(state):
    g, D = _g(state), state["day"]
    if (D + 1) % SEASON_DAYS:
        return
    last = g["tally_day"]
    if D <= last:
        return
    g["tally_day"] = D
    y = D // YEAR
    if y < g["start_year"]:
        return
    t = _demo(g, y)
    byname = {p["name"]: p for p in state["people"]}
    w = (D - last) / YEAR
    seen = set()
    for e in _window_events(state, last, D):
        k = e["type"]
        if k == "死" and e.get("who") in byname and e["who"] not in seen:
            p = byname[e["who"]]
            seen.add(p["name"])
            a = p["age"]
            t["D"][_gi(a)] += 1
            t["kid_dead" if a < era2.ADULT else "old_dead" if a >= OLD_AGE else "adult_dead"] += 1
            t["E"][_gi(a)] += w
            if p["sex"] == "女" and 15 <= a < 50:
                t["Ef"][(a - 15) // 5] += w
        elif k == "生まれる":
            t["births"] += 1
            m = byname.get(e.get("who"))
            if m and 15 <= m["age"] < 50:
                t["B"][(m["age"] - 15) // 5] += 1
        elif k == "蓄えが尽きる":
            t["famine"] += 1
    for p in state["people"]:
        if not p["alive"] or p["born_day"] > last:  # この季節に生まれた子は次の季節から数える
            continue
        a = p["age"]
        t["E"][_gi(a)] += w
        if p["sex"] == "女" and 15 <= a < 50:
            t["Ef"][(a - 15) // 5] += w
    sd = era2.store_days(state)
    g["store_min"][str(y)] = min(g["store_min"].get(str(y), sd), sd)
    if era2.season(D) == "秋":  # 秋の終わり: この季節にまいた種と働き手 (ボズラップの目印)
        seed = sum(f.get("seed", 0) for f in state["era2"].get("fields", []) if last < f.get("day", -1) <= D)
        g["sow"][str(y)] = {"seed": seed, "workers": _workers(state)}
    if (D + 1) % YEAR == 0:
        year_end(state)


def _sum(g, y0, y1):
    out = {"E": [0.0] * len(AGE_GROUPS), "D": [0] * len(AGE_GROUPS), "Ef": [0.0] * len(MOTHER), "B": [0] * len(MOTHER)}
    for y in range(y0, y1 + 1):
        t = g["demo"].get(str(y))
        if not t:
            continue
        for k in out:
            out[k] = [a + b for a, b in zip(out[k], t[k])]
    return out


def life(s, from_age=0):
    """生命表 (tools/stats_calc.py の life_table と同じ作り方。0 歳の a = 0.3)。from_age=15 なら 15 歳の平均余命。人年が少なすぎれば None"""
    if sum(s["E"]) < 50:
        return None
    l, T = 1.0, 0.0
    for i, (lo, hi) in enumerate(AGE_GROUPS):
        if lo < from_age:
            continue
        m = s["D"][i] / s["E"][i] if s["E"][i] > 0 else 0.0
        if hi is None:
            T += l / m if m > 0 else l * 10
            break
        n = hi - lo
        a = 0.3 if lo == 0 else n / 2
        q = min(1.0, n * m / (1 + (n - a) * m))
        d = l * q
        T += n * (l - d) + a * d
        l -= d
    return round(T, 1)


def tfr(s):
    tot = sum(5 * b / e for b, e in zip(s["B"], s["Ef"]) if e > 0)
    return round(tot, 2) if tot else None


def _in(v, band):
    return v is not None and band[0] <= v <= band[1]


def row_of(state, y):
    g = _g(state)
    s = SCEN[g["scen"]]
    t = g["demo"].get(str(y)) or _demo(g, y)
    alive = [p for p in state["people"] if p["alive"]]
    pop = len(alive)
    y0 = max(g["start_year"], y - WIN + 1)
    agg = _sum(g, y0, y)
    e0, e15, tf = life(agg), life(agg, 15), tfr(agg)
    pops = [(g["rows"].get(str(yy)) or {}).get("pop") for yy in range(y0, y)] + [pop]
    pops = [x for x in pops if x]
    nat_n = sum((g["demo"].get(str(yy)) or {}).get("births", 0) - sum((g["demo"].get(str(yy)) or {}).get(k, 0) for k in ("kid_dead", "adult_dead", "old_dead"))
                for yy in range(y0, y + 1))
    nat = round(100 * nat_n / (y - y0 + 1) / (sum(pops) / len(pops)), 2) if pops else None
    sd_end = era2.store_days(state)
    smin = g["store_min"].get(str(y), sd_end)
    sow = g["sow"].get(str(y)) or {}
    past = state["era2"]["g7"].get("past", [])
    worked = field = canal = 0
    for ss in past:
        for acts in ss["days"].values():
            for act, d in acts.items():
                if act in g14.REST:
                    continue
                worked += d
                if act in ("畑仕事", "種まき"):
                    field += d
                if act == "水の道を掘る":
                    canal += d
    t5r = (_t5()._g(state)["rows"].get(str(y)) or {}) if _t5().on(state) else {}
    deaths = t["kid_dead"] + t["adult_dead"] + t["old_dead"]
    r = {"year": y, "scen": g["scen"], "win": [y0, y], "pop": pop, "pop0": g["pop0"], "adults": len(era2.adults(state)),
         "old": sum(1 for p in alive if p["age"] >= OLD_AGE), "births": t["births"], "deaths": deaths, "kid_dead": t["kid_dead"], "adult_dead": t["adult_dead"],
         "old_dead": t["old_dead"], "store_end": sd_end, "store_min": smin, "famine": t["famine"],
         "e0": e0, "e15": e15, "nat": nat, "tfr": tf,
         "d1_ok": _in(e0, D1_E0), "d2_ok": _in(e15, D2_E15), "d3_ok": _in(nat, s["d3"]), "d4_ok": _in(tf, s["d4"]),
         "d5_ok": t["famine"] == 0 and sd_end >= D5_STORE,
         "seed": sow.get("seed"), "workers": sow.get("workers"), "seed_w": round(sow["seed"] / sow["workers"]) if sow.get("workers") else None,
         "worked": worked, "field_share": round(field / worked, 4) if worked else None, "nonfood_share": t5r.get("t3_share"),
         "canal_pd": canal, "town_takers": t5r.get("taker_n")}
    return r


def year_end(state):
    g, D = _g(state), state["day"]
    y = D // YEAR
    if y < g["start_year"] or str(y) in g["rows"]:
        return
    g["rows"][str(y)] = row_of(state, y)


# ---------------- 止まり (g7.check から。t5 のかわり) ----------------

def check(state, done):
    """季節の終わり: 止まるわけ (なければ None)。i4 の止まり (読める大人が 1 人以下) はそのまま。T5 の入口と相談は閉じた"""
    import i4
    c = i4.check(state, done)
    if c:
        return c
    g, D = _g(state), state["day"]
    if (D + 1) % YEAR:
        return None
    y = D // YEAR
    if y < g["start_year"]:
        return None
    r = g["rows"].get(str(y))
    if not r:
        return None
    did = lambda w: any(c["why"] == w and c.get("year") == y for c in done)  # noqa: E731
    if not r["d5_ok"] and not did("d1_safe"):
        head = f"{y}年にききんがあった" if r["famine"] else "蓄えが 200 日分を切った"
        return {"why": "d1_safe", "year": y, "day": D, "text": f"D1: {head} ({y}年の終わり {r['store_end']} 日分・いちばん少ない {r['store_min']} 日分・ききん {r['famine']})"}
    need = math.ceil(POP_KEEP * g["pop0"])
    if r["pop"] < need and not did("d1_pop"):
        return {"why": "d1_pop", "year": y, "day": D, "text": f"D1: 人が {r['pop']} 人になり、直したときの {g['pop0']} 人の {round(POP_KEEP * 100)}% ({need} 人) を切った"}
    rs = [g["rows"].get(str(y - i)) for i in range(OUT_YEARS)]
    late = "fix1" in g and y < g["fix1"]["out_from"]  # 相談の直し 1: 5 年まとめがそろう年 (246) より前は、この相談では止めない
    if all(rs) and not late and not did("d1_out"):
        out = [k for k in ("d1", "d4") if not any(x[f"{k}_ok"] for x in rs)]
        if out:
            s = SCEN[g["scen"]]
            txt = "・".join(f"{k} {DS[k]} ({'・'.join(str(x['e0' if k == 'd1' else 'tfr']) for x in reversed(rs))}。線 {D1_E0[0] if k == 'd1' else s['d4'][0]}〜{D1_E0[1] if k == 'd1' else s['d4'][1]})"
                           for k in out)
            return {"why": "d1_out", "year": y, "day": D, "text": f"D1: {txt} が {OUT_YEARS} 年つづけて線の外 (見通しとちがう動き)"}
    n = y - g["start_year"] + 1
    if n > 0 and n % LATER_YEARS == 0 and not any(c["why"] == f"d1_years_{y}" for c in done):
        return {"why": f"d1_years_{y}", "year": y, "day": D, "text": f"D1: 人口の決まりを直して {n} 年たった (3 年ごとの相談)"}
    return None


# ---------------- 行 (status・年報) ----------------

def win_text(r):
    y0, y1 = r["win"]
    n = y1 - y0 + 1
    return f"{y1}年だけ" if n == 1 else f"{y0}〜{y1}年" + ("" if n >= WIN else f"。{WIN} 年たつまでは短い")


def row_text(r):
    ok = lambda b: "○" if b else "×"  # noqa: E731
    return (f"{r['year']}年: 人 {r['pop']} (大人 {r['adults']}・55 歳から {r['old']}。はじめ {r['pop0']}) / 生まれた {r['births']}・亡くなった {r['deaths']} "
            f"(子 {r['kid_dead']}・大人 {r['adult_dead']}・年寄り {r['old_dead']}) / 蓄え 年の終わり {r['store_end']} 日分 (いちばん少ない {r['store_min']})・ききん {r['famine']} / "
            f"d1 平均寿命 {r['e0']} {ok(r['d1_ok'])}・d2 15 歳の平均余命 {r['e15']} {ok(r['d2_ok'])}・d3 自然増加 {r['nat']}%/年 {ok(r['d3_ok'])}・"
            f"d4 合計特殊出生率 {r['tfr']} {ok(r['d4_ok'])} ({win_text(r)}) / d5 {ok(r['d5_ok'])} / "
            f"d6 働き手 1 人あたりの秋の種まき {r['seed_w']} つかみ・畑仕事 {round((r['field_share'] or 0) * 100, 1)}%・"
            f"食べ物でない仕事 {round((r['nonfood_share'] or 0) * 100, 1)}%・水の道 {r['canal_pd']} 人日・町の頼みを受けた家 {r['town_takers']}")


def lines(state):
    if not on(state):
        return []
    g = _g(state)
    s = SCEN[g["scen"]]
    pop = len([p for p in state["people"] if p["alive"]])
    out = [f"{D1_NAME}: {g['why']}。{g['day']} 日目から ({g['start_year']}年から数える。筋 {g['scen']} {s['name']}: 15〜39 歳の病の死 {BASE['a']} → {g['a']}・"
           f"40〜54 歳 {BASE['b']} → {g['b']}・55 歳からの年寄りの死 × {g['old']}・生まれる見込み {BASE['birth']} → {g['birth']} (1 季節)。"
           f"T5 の入口と相談は {_yd(g['day'])}で閉じた)。人 {pop} (はじめ {g['pop0']})。"
           f"線: d1 {D1_E0[0]}〜{D1_E0[1]} 歳・d2 {D2_E15[0]}〜{D2_E15[1]} 年・d3 {s['d3'][0]}〜{s['d3'][1]}%/年・d4 {s['d4'][0]}〜{s['d4'][1]}・d5 {D5_STORE} 日分以上とききん 0"]
    if "fix1" in g:
        f = g["fix1"]
        out.append(f"相談の直し 1: {f['why']} {_yd(f['day'])}から。「d1 か d4 が {OUT_YEARS} 年つづけて線の外」の相談は {f['out_from']}年の終わりから "
                   f"({f['out_from'] - 1}年と {f['out_from']}年の行で見る)。線・世界の見込み・ほかの相談は変えない")
    if "info1" in g:
        f = g["info1"]
        out.append(f"蓄えの知らせ 1: {f['why']} {_yd(f['day'])}から。世界の決まり・線・相談は変えない")
    for y in sorted(g["rows"], key=int)[-3:]:
        out.append(row_text(g["rows"][y]))
    return out
