"""Society 4.0 フェーズ 1「読み書きと知らせ板」(2026-11-21。docs/society_phase/I4_design.md・I4_check.md)

- 印 state.era2.g7.i4 があるときだけ働く。印を書くのは step.py resume --i4 "<本人の言葉>" だけ
  (S4 のあと、26999 日目 (224年の終わり) から。S4 の相談で止まっているときか、止まりがないとき。1 回だけ)。
  印がなければ、このファイルは読みこみもしない (g7・g15・era2・step.py は「i4」の鍵があるときだけ、関数の中で読みこむ)。
  だから前の歩は、お題・state・出来事・乱数が 1 バイトも変わらない
- 印を書くと g7.s4.closed も書く (S4 の止まり・S4 のお題の節・S4 の答えの欄を止める。S4 の年の行は数えつづける。町の家・掘り場・町の市の決まりはそのまま)
- 時代 (state.era) は G15 のまま。G15・S3・S4 の世界の仕組みはそのまま動き、その上に 2 つの部分を足す:
  a 知らせ板: 答える人は、答えの欄 notice に 60 字までの知らせを書ける (家に読める大人がいるとき。1 家 1 季節 1 枚)。
    板にのるのは新しいほうから 12 枚で、1 枚は 4 季節 (1 年) で消える。書いた家の読める大人 1 人 (名の順でいちばん前) が、その季節のはじめの 1 日を「知らせを書く」にする。
    中身が読めるのは、読める人と、家に読める大人がいる人だけ。ほかの人には枚数だけ出る
  b 手習い: 読める大人は仕事「字を教える」を選べる。その日、キャンプにいる 10〜14 歳の子を 6 人まで教える (その人の家の子が先、のこりは村の子を教わった日の多い順)。
    子は教わった日が 30 日で読み書きできる (15 歳で大人になると、そのまま読める大人に数える)。
    大人が「字を習う」日に、その日「字を教える」人がいれば 2 日分進む (教える人 1 人につき大人 2 人まで)
- 乱数は使わない。後押しはしない。印・本人の言葉・「作る側」・物差しのことは、村の人のお題にも出来事にも書かない
- 物差し (I4_design.md 4.): i1 読める大人が大人の 25% 以上・i2 この年の知らせ 6 枚以上で 4 家以上・i3 字の仕事の人日が働いた人日の 4% 以上・
  i4 暮らしを守る (ききんなし・蓄え 120 日分・人は印のときの 95%)。入口は i1 と i2 と i3 が同じ 2 年つづき、その 2 年に i4 を割らない。
  止めて相談: i4 を割った年・字の道を選んだ人が 2 年 0 人・5 年ごと・読める大人が 1 人以下 (G15 の READERS_STOP のまま)
"""
import copy
import math

import era2
import g10
import g14
import g15
from world import log, season

YEAR, SEASON_DAYS = era2.YEAR, era2.SEASON_DAYS
I4_FROM = 26999  # 本物の村が S4 を閉じた日 (224年の終わり)。これより前には印を書けない
I4_DATE = "2026-11-21"
I4_NAME = "Society 4.0 フェーズ 1 (読み書きと知らせ板)"
PARTS = {"a": "知らせ板 (書いたことが、読める人みなに同じ形で届く)", "b": "手習い (読める大人が子に字を教える)"}
ACT_TEACH, ACT_WRITE = "字を教える", "知らせを書く"  # 新しい仕事 (world.ACTS7 の後ろに足した。印のあとだけ。「知らせを書く」は選ぶ仕事でなく、書いた家の読める大人の 1 日)
ACTS = (ACT_TEACH, ACT_WRITE)
# a 知らせ板【仮定】
NOTICE_MAX = 60  # 1 枚の字の数
BOARD_MAX = 12  # 板にのる枚数 (新しいほうから)
BOARD_LIFE = YEAR  # 1 枚が板にのっている日数 (4 季節)
SECTION = "## 村の知らせ板"  # お題の節の見出し (tools/prompt_check.py --words i4 が読む)
FACT_HEADS = ()
# b 手習い【仮定】
KID_AGE = (10, 14)
KIDS_PER_DAY = 6
KID_DAYS = g10.LEARN_DAYS  # 30 日
ADULTS_PER_TEACHER = 2
# 物差し【仮定】(I4_design.md 4.)
LETTER_ACTS = (g10.ACT_LEARN, ACT_TEACH, ACT_WRITE, "帳をつける", era2.ACT_RECORD)
I1_SHARE = 0.25
I2_NOTES, I2_HOUSES = 6, 4
I3_SHARE = 0.04
I4_STORE, I4_POP = 120, 0.95
I_YEARS = 2
PATH_YEARS = 2
LATER_YEARS = 5
USE_CHARS = 6  # 知らせの文と、この字の数だけ同じ並びがあれば「使った」に数える
IS = {"i1": "読める大人", "i2": "知らせ板", "i3": "字の仕事", "i4": "暮らしを守る"}
# 村の人に見せる文 (知らせ板の節と、短い節の字の行) に書かない言葉 (tools/prompt_check.py --words i4・T_I4 で確かめる)
WORDS = ("作る側", "後押し", "反実仮想", "印", "物差し", "入口", "Society", "本人", "I4", "S4", "i1", "i2", "i3")


def on(state):
    return "day" in (((state.get("era2") or {}).get("g7") or {}).get("i4") or {})


def _g(state):
    return state["era2"]["g7"]["i4"]


def _yd(day):
    return f"{day // YEAR}年{day % YEAR + 1}日目"


def _s4():
    import s4
    return s4


def _adult(state, name):
    return next((p for p in era2.adults(state) if p["name"] == name), None)


def _house_of(state, name):
    p = next((q for q in state["people"] if q["name"] == name), None)
    return p.get("household") if p else None


def _reader_set(state):
    return g10._g(state)["readers"]


def house_readers(state, h):
    """家 h の、読み書きできる生きている大人 (名の順)"""
    rd = _reader_set(state)
    return sorted(p["name"] for p in era2.adults(state) if h and p.get("household") == h and p["name"] in rd)


def _fail(state, who, what, why, log_it=True):
    """選んだのにできなかったこと (帳面 g7.i4.fails。log_it なら出来事「字」にも。お題の短い節の「字と知らせ板で、できなかったこと」に出す)"""
    g, D = _g(state), state["day"]
    g["fails"] = (g["fails"] + [{"day": D, "year": (D + 1) // YEAR, "who": who, "what": what, "why": why}])[-40:]  # 年は集まりの答えが効く年 (年の集まりの日は次の年)
    if log_it:
        log(state, "字", who, why, i4_fail=what)


# ---------------- 印 (step.py resume --i4) ----------------

def why_text(words):
    return f"{I4_NAME} (本人の言葉 {I4_DATE} 「{words}」)"


def refusal(state, words):
    """resume --i4 ができないわけ (できるなら None)"""
    if not (words or "").strip():
        return "--i4 には本人の言葉が要る"
    g7s = ((state.get("era2") or {}).get("g7") or {})
    if "s4" not in g7s or not _s4().on(state):
        return "S4 の印がないので、I4 は始められない"
    if "i4" in g7s:
        return "I4 はもう始めてある"
    if state["day"] < I4_FROM:
        return f"I4 は {I4_FROM} 日目 (224年の終わり) からだけ"
    h = g7s.get("hold") or {}
    if state.get("hold") or h:
        if not (h.get("why") == "consult" and str(h.get("what", "")).startswith("S4:")):
            return "I4 は、S4 の相談で止まっているときか、止まりのないときだけ始める"
    if g15.push_on(state):
        return "後押しが動いている"
    return None


def mark(state, words):
    """resume --i4 から: 印 g7.i4 を書き、g7.s4.closed を書く (村の出来事には残さない)"""
    words = words.strip()
    D = state["day"]
    s4g = _s4()._g(state)
    s4g["closed"] = D
    g = state["era2"]["g7"]["i4"] = {
        "day": D, "words": words, "why": why_text(words), "parts": list(PARTS), "start_year": D // YEAR + 1,
        "pop0": len([p for p in state["people"] if p["alive"]]), "adults0": len(era2.adults(state)),
        "readers0": len(g10.readers(state)), "board": [], "notes": {}, "pending": [], "restore": {}, "kids": {}, "taught": {},
        "today": {}, "used": {}, "chose": {}, "fails": [], "rows": {}, "f": {}, "f_years": {k: [] for k in ("i1", "i2", "i3")},
        "i4_broken": [], "store_min": {}}
    return g


# ---------------- a 知らせ板 ----------------

def _season_label(day):
    return f"{day // YEAR}年{season(day)}"


def board_now(state, day=None):
    """いま板にのっている知らせ (新しい順。BOARD_MAX 枚まで・BOARD_LIFE 日より前のものは消えている)"""
    D = state["day"] if day is None else day
    return [b for b in _g(state)["board"] if D - b["day"] < BOARD_LIFE][-BOARD_MAX:][::-1]


def notice_text(v):
    """答えの notice の文 (なければ None)。60 字まで・改行はつめる"""
    if not isinstance(v, str):
        return None
    t = " ".join(v.replace("\r", "\n").split()).strip()
    if not t or t.lower() in ("null", "none", "なし"):
        return None
    return t[:NOTICE_MAX]


def can_read(state, p):
    """知らせの中身が分かるか: (自分が読める, 読んで聞かせる家の読める大人の名前 (自分が読めれば None))"""
    rd = _reader_set(state)
    if p["name"] in rd and not p.get("child"):
        return True, None
    hr = house_readers(state, p.get("household"))
    return False, (hr[0] if hr else None)


def _subs(text):
    return {text[i:i + USE_CHARS] for i in range(len(text) - USE_CHARS + 1)} if len(text) >= USE_CHARS else set()


def _texts(a):
    """答えの、話・覚えていること・掟の提案の文"""
    out = []
    for s in a.get("say") or []:
        if isinstance(s, dict) and s.get("text"):
            out.append(("話", str(s["text"])))
    for k in a.get("knowledge") or []:
        if isinstance(k, dict) and k.get("text"):
            out.append(("知識", str(k["text"])))
    pr = a.get("proposal")
    if isinstance(pr, dict) and pr.get("text") and str(pr["text"]).strip() not in ("...", "null"):
        out.append(("掟", str(pr["text"])))
    return out


def count_used(state, real, day=None):
    """知らせの中身が分かる人が、話・知識・掟で知らせの文を使ったか (同じ並びが 6 字以上。お題を書いた日の板の知らせだけ)。帳面 g7.i4.used (お題には出さない)"""
    g = _g(state)
    bd = board_now(state, day)
    if not bd:
        return
    y = str((state["day"] + 1) // YEAR)
    row = g["used"].setdefault(y, {"n": 0, "who": [], "notes": {}})
    subs = [(b, _subs(b["text"])) for b in bd]
    for name, a in sorted(real.items()):
        p = next((q for q in era2.adults(state) if q["name"] == name), None)
        if p is None or not isinstance(a, dict):
            continue
        me, fam = can_read(state, p)
        if not me and not fam:
            continue
        for kind, t in _texts(a):
            for b, ss in subs:
                if b["house"] == p.get("household") or not any(s in t for s in ss):
                    continue
                row["n"] += 1
                if name not in row["who"]:
                    row["who"] = (row["who"] + [name])[:30]
                k = f"{b['day']}:{b['house']}"
                row["notes"][k] = row["notes"].get(k, 0) + 1


def apply_answers(state, real):
    """集まりの答え (g7.apply_year から。S4 のあと): 知らせを使ったか → notice (1 家 1 季節 1 枚。家に読める大人がいるとき)"""
    g, D = _g(state), state["day"]
    count_used(state, real)
    y = (D + 1) // YEAR
    lab = _season_label(D + 1)
    done = {b["house"] for b in g["board"] if b["day"] == D}
    g["pending"] = []
    for name, a in sorted(real.items()):
        if not isinstance(a, dict):
            continue
        t = notice_text(a.get("notice"))
        if t is None:
            continue
        h = _house_of(state, name)
        hr = house_readers(state, h)
        if not hr:
            _fail(state, name, "知らせ板", f"{name} の知らせは、家に字を書ける人がいないので、板に書けなかった")
            continue
        if h in done:
            _fail(state, name, "知らせ板", f"{name} の知らせは、{h}がこの季節にもう 1 枚書いたので、書かなかった (1 家 1 季節 1 枚)")
            continue
        done.add(h)
        b = {"day": D, "year": y, "season": lab, "house": h, "by": name, "writer": hr[0], "text": t}
        g["board"] = (g["board"] + [b])[-BOARD_MAX:]
        g["notes"].setdefault(str(y), []).append({k: b[k] for k in ("day", "season", "house", "by", "writer", "text")})
        g["pending"].append({"writer": hr[0], "house": h})
        _chose(state, y, name)


def _chose(state, y, name):
    row = _g(state)["chose"].setdefault(str(y), [])
    if name not in row:
        row.append(name)


def season_start(state):
    """季節のはじめ (g7._apply の終わり。S4 の町の家のあと): 知らせを書いた家の読める大人は、季節のはじめの 1 日を「知らせを書く」にする
    (その日のあとは、もとの仕事にもどる。write_day がもどす)"""
    g = _g(state)
    g["restore"] = {}
    for r in g.get("pending") or []:
        p = _adult(state, r["writer"])
        if p is None or r["writer"] in g["restore"]:
            continue
        g["restore"][r["writer"]] = copy.deepcopy(p.get("plan") or {"activity": "休む", "place": "camp", "with": []})
        p["plan"] = {"activity": ACT_WRITE, "place": "camp", "with": []}
    g["pending"] = []


def write_day(state, p, t):
    """仕事「知らせを書く」の 1 日 (g7.role_day から): 出来事を残し、次の日からはもとの仕事にもどる"""
    g = _g(state)
    name = p["name"]
    b = next((x for x in reversed(g["board"]) if x["writer"] == name), None)
    h = b["house"] if b else p.get("household")
    t.setdefault("events", []).append(log(state, ACT_WRITE, name, f"{h}の {name} が、村の知らせ板に知らせを書いた", household=h))
    if name in g["restore"]:
        p["plan"] = g["restore"].pop(name)


# ---------------- b 手習い ----------------

def can_teach(state, name):
    """「字を教える」を選べるか: 読み書きできる大人"""
    return name in _reader_set(state) and _adult(state, name) is not None


def acts(state):
    """いま選べる i4 の仕事 (読める大人がいるときの「字を教える」だけ。「知らせを書く」は選ぶ仕事でない)"""
    return [ACT_TEACH] if g10.readers(state) else []


def rest_why(state, name, act):
    if act == ACT_TEACH and not can_teach(state, name):
        return f"{name} は、字を読み書きできないので、字を教えられず、休んだ"
    return None


# 字の仕事ができない人の仕事 (2026-11-21。I4_check.md 5.6): 代表が「字を教える」「知らせを書く」「帳をつける」にして、家の大人が同じ仕事になったとき
# (family に書かれなかった・代表と同じ仕事・見本の家の答えをまねた)、できない人は季節じゅう休まず、前の季節の仕事をする。
# 前の季節の仕事がなければ、その人の家の前の季節にいちばん多かった仕事、それもなければ畑仕事。どれもキャンプでできる仕事だけ
LETTER_JOBS = (ACT_TEACH, ACT_WRITE, "帳をつける")
REFIT_OK = ("畑仕事", "ヤギの世話", "土器づくり", "道具づくり", "水の道を掘る", "燃える石を掘る")
REFIT_LAST = "畑仕事"


def _can_letter(state, name, act):
    if act == ACT_TEACH:
        return can_teach(state, name)
    if act == "帳をつける":
        import g12
        return "g12" in state["era2"]["g7"] and g12.can_census(state, name)
    return False  # 知らせを書くは選ぶ仕事でない (書いた家の読める大人の 1 日だけ)


def _best(days, ok):
    xs = sorted(((d, a) for a, d in days.items() if a in ok and d > 0), key=lambda x: (-x[0], x[1]))
    return xs[0][1] if xs else None


def refit_job(state, q):
    """できない字の仕事のかわりの仕事: 前の季節のその人の仕事 → 家でいちばん多かった仕事 → 畑仕事"""
    ok = [a for a in REFIT_OK if a in era2.acts2(state)]
    past = (state["era2"]["g7"].get("past") or [None])[-1] or {}
    days = past.get("days") or {}
    a = _best(days.get(q["name"]) or {}, ok)
    if a:
        return a
    h = q.get("household")
    tot = {}
    for n, acts_ in days.items():
        if h and (past.get("home") or {}).get(n) == h:
            for k, d in acts_.items():
                tot[k] = tot.get(k, 0) + d
    return _best(tot, ok) or REFIT_LAST


def refit(state, q, act, j):
    """g7.job のはじめ (印のあと): 字の仕事 (「休む」になる前の答えも見る) ができない人は、かわりの仕事にする。戻り値 (仕事, くわしい答え)"""
    want = j.get("activity") if act == "休む" else act
    if want not in LETTER_JOBS or _can_letter(state, q["name"], want):
        return act, j
    new = refit_job(state, q)
    why = "字を読み書きできない" if want != ACT_WRITE else "知らせを書くのは、知らせを出した家の読める大人の 1 日だけな"
    q["plan"] = {"activity": new, "place": "camp", "with": []}
    _fail(state, q["name"], want, f"{q['name']} は、{why}ので「{want}」はできず、季節じゅう「{new}」をした", log_it=False)
    return new, {"activity": new}


def _today(state):
    g, D = _g(state), state["day"]
    if (g.get("today") or {}).get("day") != D:
        g["today"] = {"day": D, "kids": [], "adults": 0}
    return g["today"]


def _kid_ok(c):
    return bool(c.get("child")) and KID_AGE[0] <= c["age"] <= KID_AGE[1] and not (c.get("today") or {}).get("away")


def _taught(state, y):
    return _g(state)["taught"].setdefault(str(y), {"days": 0, "kid_days": 0, "kids": [], "adult_days": 0, "kid_readers": [], "teachers": []})


def teach_day(state, p, t):
    """仕事「字を教える」の 1 日 (g7.role_day から): キャンプにいる 10〜14 歳の子を 6 人まで (家の子が先、のこりは教わった日の多い順・名の順)。
    子は教わった日が 30 日で読み書きできる (g10.readers に入る)"""
    g, D = _g(state), state["day"]
    name = p["name"]
    if not can_teach(state, name):
        t.setdefault("events", []).append(log(state, "休む", name, rest_why(state, name, ACT_TEACH) or f"{name} はキャンプで休んだ"))
        return
    td = _today(state)
    rd = _reader_set(state)
    h = p.get("household")
    ks = [c for c in era2.children(state) if _kid_ok(c) and c["name"] not in rd and c["name"] not in td["kids"]]
    own = sorted((c for c in ks if h and c.get("household") == h), key=lambda c: (-g["kids"].get(c["name"], 0), c["name"]))
    rest = sorted((c for c in ks if not (h and c.get("household") == h)), key=lambda c: (-g["kids"].get(c["name"], 0), c["name"]))
    pick = (own + rest)[:KIDS_PER_DAY]
    row = _taught(state, D // YEAR)
    row["days"] += 1
    if name not in row["teachers"]:
        row["teachers"] = (row["teachers"] + [name])[:60]
    if not pick:
        t.setdefault("events", []).append(log(state, ACT_TEACH, name, f"{name} が、字を教えようとしたが、キャンプに教わる子がいなかった", kids=0))
        return
    for c in pick:
        td["kids"].append(c["name"])
        n = g["kids"][c["name"]] = g["kids"].get(c["name"], 0) + 1
        row["kid_days"] += 1
        if c["name"] not in row["kids"]:
            row["kids"] = (row["kids"] + [c["name"]])[:200]
        if n >= KID_DAYS:
            rd[c["name"]] = D
            g["kids"].pop(c["name"])
            row["kid_readers"].append(c["name"])
            log(state, g10.ACT_LEARN, c["name"], f"{c['name']} (子) は、音の字を読み書きできるようになった", reader=True, child=True)
    t.setdefault("events", []).append(log(state, ACT_TEACH, name, f"{name} が、子 {len(pick)} 人に音の字を教えた", kids=len(pick)))


def teachers_today(state):
    """その日「字を教える」をしている (キャンプにいる・読める) 大人の数"""
    rd = _reader_set(state)
    return len([q for q in era2.adults(state) if (q.get("today") or {}).get("activity") == ACT_TEACH and q["name"] in rd and not (q.get("today") or {}).get("away")])


def learn_day(state, p, t):
    """g10.learn_day のかわり (印のあと): その日「字を教える」人がいれば、習う日が 2 日分進む (教える人 1 人につき大人 2 人まで)"""
    g10g = g10._g(state)
    before = g10g["learn"].get(p["name"], 0)
    g10.learn_day(state, p, t)
    if p["name"] in g10g["readers"] or g10g["learn"].get(p["name"], 0) == before:
        return
    td = _today(state)
    if td["adults"] >= ADULTS_PER_TEACHER * teachers_today(state):
        return
    td["adults"] += 1
    n = g10g["learn"][p["name"]] = g10g["learn"][p["name"]] + 1
    _taught(state, state["day"] // YEAR)["adult_days"] += 1
    if n >= g10.LEARN_DAYS:
        g10g["readers"][p["name"]] = state["day"]
        log(state, g10.ACT_LEARN, p["name"], f"{p['name']} は、音の字を読み書きできるようになった", reader=True)


def _grown(state):
    """大人になった子の、教わった日を「字を習う」の日に移す (読めないまま 15 歳になった子は、大人として習いつづける)"""
    g = _g(state)
    ad = {p["name"] for p in era2.adults(state)}
    alive = {p["name"] for p in state["people"] if p["alive"]}
    lr = g10._g(state)["learn"]
    for n in sorted(g["kids"]):
        if n in ad:
            lr[n] = max(lr.get(n, 0), g["kids"].pop(n))
        elif n not in alive:
            g["kids"].pop(n)


# ---------------- 季節の終わり・年の終わり: 帳面と物差し ----------------

def season_end(state):
    """季節の終わり (g7.season_end。S4 のあと): 板の古い知らせを消す → 大人になった子 → 蓄えのいちばん少ない日数 → 年の終わりなら行と物差し"""
    D = state["day"]
    if (D + 1) % SEASON_DAYS:
        return
    g = _g(state)
    g["board"] = [b for b in g["board"] if D - b["day"] < BOARD_LIFE]
    _grown(state)
    y = str(D // YEAR)
    sd = era2.store_days(state)
    g["store_min"][y] = min(g["store_min"].get(y, sd), sd)
    if (D + 1) % YEAR == 0:
        year_end(state)


def work_days(state):
    """前の 1 年 (g7.past) の大人の働いた日と、字の仕事の日 (休んだ日は数えない)・字の道を選んだ人"""
    w = lt = 0
    who = set()
    for s in state["era2"]["g7"].get("past", []):
        for n, acts_ in s["days"].items():
            for a, d in acts_.items():
                if a in g14.REST:
                    continue
                w += d
                if a in LETTER_ACTS:
                    lt += d
                if a in (g10.ACT_LEARN, ACT_TEACH):
                    who.add(n)
    return w, lt, who


def row_of(state, y):
    g = _g(state)
    ys = str(y)
    ads = era2.adults(state)
    rd = g10.readers(state)
    i1 = round(len(rd) / len(ads), 4) if ads else 0.0
    notes = g["notes"].get(ys) or []
    w, lt, who = work_days(state)
    i3 = round(lt / w, 4) if w else 0.0
    ev = [e for e in state["events"] if e["day"] // YEAR == y]
    famine = sum(1 for e in ev if e["type"] == "蓄えが尽きる")
    pop = len([p for p in state["people"] if p["alive"]])
    smin = g["store_min"].get(ys, era2.store_days(state))
    tg = g["taught"].get(ys) or {}
    new_rd = sorted(n for n, d in g10._g(state)["readers"].items() if d is not None and d // YEAR == y)
    chose = sorted(set(g["chose"].get(ys) or []) | who)
    us = g["used"].get(ys) or {}
    return {"year": y, "adults": len(ads), "readers": len(rd), "i1_share": i1, "notes": len(notes), "note_houses": len({x["house"] for x in notes}),
            "worked": w, "letters": lt, "i3_share": i3, "teach_days": tg.get("days", 0), "kid_days": tg.get("kid_days", 0), "kids_taught": len(tg.get("kids") or []),
            "adult_bonus": tg.get("adult_days", 0), "kid_readers": len(tg.get("kid_readers") or []), "new_readers": len(new_rd), "learning_kids": len(g["kids"]),
            "chose": len(chose), "used": us.get("n", 0), "fails": len([f for f in g["fails"] if f["year"] == y]),
            "store_min": smin, "store_end": era2.store_days(state), "famine": famine, "pop": pop, "pop0": g["pop0"],
            "i1_like": i1 >= I1_SHARE, "i2_like": len(notes) >= I2_NOTES and len({x["house"] for x in notes}) >= I2_HOUSES, "i3_like": i3 >= I3_SHARE,
            "i4_ok": famine == 0 and smin >= I4_STORE and pop >= I4_POP * g["pop0"]}


def year_end(state):
    g, D = _g(state), state["day"]
    y = D // YEAR
    if y < g["start_year"] or str(y) in g["rows"]:
        return
    r = g["rows"][str(y)] = row_of(state, y)
    for k in ("i1", "i2", "i3"):
        if r[f"{k}_like"] and y not in g["f_years"][k]:
            g["f_years"][k].append(y)
        if k not in g["f"] and all((y - i) in g["f_years"][k] for i in range(I_YEARS)):
            g["f"][k] = D
    if not r["i4_ok"] and y not in g["i4_broken"]:
        g["i4_broken"].append(y)


def entrance(state):
    """入口: いちばん新しい 2 年に、i1 と i2 と i3 がつづき、その 2 年に i4 を割らない"""
    g = _g(state)
    if not g["rows"]:
        return False
    y = max(int(k) for k in g["rows"])
    ys = [g["rows"].get(str(y - i)) for i in range(I_YEARS)]
    if not all(ys):
        return False
    return all(r["i1_like"] and r["i2_like"] and r["i3_like"] and r["i4_ok"] for r in ys)


def check(state, done):
    """g7.check から (季節の終わり): 止まるわけ (なければ None)。S4・S3・G15 の相談のかわり"""
    g, D = _g(state), state["day"]
    if (D + 1) % SEASON_DAYS:
        return None
    rd = g10.readers(state)
    if len(rd) <= g15.READERS_STOP and not any(c["why"] == f"i4_readers_{len(rd)}" for c in done):
        return {"why": f"i4_readers_{len(rd)}", "day": D, "text": f"I4: 読める大人が {len(rd)} 人になった"}
    if (D + 1) % YEAR:
        return None
    y = D // YEAR
    if y < g["start_year"]:
        return None
    r = g["rows"].get(str(y)) or {}
    if entrance(state) and not any(c["why"] == "i4_entrance" for c in done):
        return {"why": "i4_entrance", "year": y, "day": D, "text": f"I4: 入口に着いた ({y - 1}年と{y}年に i1・i2・i3。その 2 年に i4 を割らなかった)"}
    if r and not r["i4_ok"] and not any(c["why"] == "i4_safe" and c.get("year") == y for c in done):
        return {"why": "i4_safe", "year": y, "day": D, "text": f"I4: {y}年に i4 (暮らしを守る) を割った (ききん {r['famine']}・蓄えのいちばん少ない日 {r['store_min']} 日分・"
                f"人 {r['pop']} (はじめ {r['pop0']} の {round(I4_POP * 100)}% は {math.ceil(I4_POP * r['pop0'])}))"}
    ys = [g["rows"].get(str(y - i)) for i in range(PATH_YEARS)]
    if all(x and x["chose"] == 0 for x in ys) and not any(c["why"] == "i4_path" and c.get("year") == y for c in done):
        return {"why": "i4_path", "year": y, "day": D, "text": f"I4: 知らせ板・字を教える・字を習うを選んだ人が {PATH_YEARS} 年つづけて 0 人"}
    n = y - g["start_year"] + 1
    if n > 0 and n % LATER_YEARS == 0 and not any(c["why"] == f"i4_years_{y}" for c in done):
        return {"why": f"i4_years_{y}", "year": y, "day": D, "text": f"I4: 読み書きと知らせ板に入って {n} 年たった (5 年ごとの相談)"}
    return None


# ---------------- お題 ----------------

def board_block(state, p, answer=True):
    """お題の上のほう (その人のようす・決まりの文のすぐあと) の節「## 村の知らせ板」。大人みな (答える人・気持ちだけ答える人)。
    中身が出るのは、読める人と、家に読める大人がいる人だけ。answer なら書き方の行も"""
    if not p:
        return ""
    bd = board_now(state)
    me, fam = can_read(state, p)
    rows = ["村のまん中に、粘土の知らせ板がある。字の読める人が書いた知らせは、読める人ならだれでも同じ形で見られる。"]
    if not bd:
        rows.append("- 知らせ板に知らせはない")
    elif me or fam:
        rows += [f"- {b['season']} {b['house']}: 「{b['text']}」" for b in bd]
        if not me:
            rows.append(f"(あなたは字が読めないが、家の {fam} が読んで聞かせた)")
    else:
        rows.append(f"- 知らせが {len(bd)} 枚ある。字が読めないので、中身はわからない (家に読める人がいない)")
    if answer:
        hr = house_readers(state, p.get("household"))
        if hr:
            rows.append(f"- 知らせを書くなら、答えの \"notice\" に {NOTICE_MAX} 字までの文 (書かないなら null)。1 家 1 季節 1 枚。"
                        f"あなたの家の {hr[0]} が、季節のはじめの 1 日を「{ACT_WRITE}」にして板に書く。板にのるのは新しいほうから {BOARD_MAX} 枚で、1 年で消える")
        else:
            rows.append("- あなたの家には字を書ける大人がいないので、知らせは書けない")
    return f"\n{SECTION}\n" + "\n".join(rows) + "\n"


def read_lines(state, p):
    """g15 の短い節の「- 字:」の行のかわり (印のあと): 読める大人・習っている子と大人 (あと何日)・「字を教える」・できなかったこと"""
    g = _g(state)
    name, h = p["name"], p.get("household")
    rd = g10.readers(state)
    ads = len(era2.adults(state))
    if not rd:
        out = ["- 字: いま読める大人がいないので、字を習えない"]
    else:
        out = [f"- 字: 読める大人は {len(rd)} 人 / 大人 {ads} 人 ({'・'.join(rd[:10])}{' ほか' if len(rd) > 10 else ''})。読めない大人は、主な仕事「{g10.ACT_LEARN}」を "
               f"{g10.LEARN_DAYS} 日すると読めるようになる (読める人が村にいる日。その日「{ACT_TEACH}」の人がいれば 1 日で 2 日分。教える人 1 人につき大人 {ADULTS_PER_TEACHER} 人まで)"]
    mine = house_readers(state, h)
    if name in rd or mine:
        who = "あなた" if name in rd else f"あなたの家の {'・'.join(mine[:4])}"
        how = "job" if name in rd else "family"
        out.append(f"  {who}{'' if name in rd else ' '}は字を読み書きできるので、主な仕事を「{ACT_TEACH}」にできる ({how} に書く)。その日、キャンプにいる {KID_AGE[0]}〜{KID_AGE[1]} 歳の子を "
                   f"{KIDS_PER_DAY} 人まで教える (家の子が先)。子は教わった日が {KID_DAYS} 日で読み書きできるようになる")
    lr = g10._g(state)["learn"]
    ad_l = sorted((n for n in lr if n not in g10._g(state)["readers"] and _adult(state, n)), key=lambda n: (_house_of(state, n) != h, -lr[n], n))
    kd = sorted(g["kids"], key=lambda n: (_house_of(state, n) != h, -g["kids"][n], n))
    if kd or ad_l:
        out.append("  字を習っている人 (あと何日): "
                   + (f"子 {len(kd)} 人 " + "・".join(f"{n} ({KID_DAYS - g['kids'][n]})" for n in kd[:6]) + (" ほか" if len(kd) > 6 else "") if kd else "")
                   + (" / " if kd and ad_l else "")
                   + (f"大人 {len(ad_l)} 人 " + "・".join(f"{n} ({g10.LEARN_DAYS - lr[n]})" for n in ad_l[:6]) + (" ほか" if len(ad_l) > 6 else "") if ad_l else ""))
    y = state["day"] // YEAR
    f = [x for x in g["fails"] if x["year"] >= y - 1][-3:]
    if f:
        out.append("  字と知らせ板で、できなかったこと: " + " / ".join(x["why"] for x in f))
    return out


def field_rows(state, year=False):
    return ["   notice: 村の知らせ板に書く知らせ (60 字まで。家に字の読める大人がいるとき)。例 \"冬の前に土器のふたを見なおそう\"。書かないなら null"]


ANSWER_FIELDS = {"notice": "null"}


def answer_fields(state):
    return ["notice"]


# ---------------- step.py status・年報 (村の人のお題には出さない) ----------------

def row_text(r):
    return (f"{r['year']}年: 読める大人 {r['readers']}/{r['adults']} ({round(r['i1_share'] * 100, 1)}%) / 知らせ {r['notes']} 枚 ({r['note_houses']} 家)・使った {r['used']} / "
            f"字の仕事 {r['letters']}/{r['worked']} 人日 ({round(r['i3_share'] * 100, 2)}%) / 教えた {r['teach_days']} 人日 (子 {r['kids_taught']} 人・のべ {r['kid_days']}・"
            f"大人の 2 日分 {r['adult_bonus']})・読めるようになった {r['new_readers']} (子 {r['kid_readers']})・習っている子 {r['learning_kids']} / "
            f"選んだ人 {r['chose']}・できなかった {r['fails']} / 蓄え いちばん少ない {r['store_min']} 日分・ききん {r['famine']}・人 {r['pop']} (はじめ {r['pop0']}) / "
            + " ".join(f"{k} {'○' if r[f'{k}_like'] else '×'}" for k in ("i1", "i2", "i3")) + f" i4 {'○' if r['i4_ok'] else '×'}")


def lines(state):
    if not on(state):
        return []
    g = _g(state)
    out = [f"{g['why']}。{g['day']} 日目から ({g['start_year']}年から数える)。読める大人 {len(g10.readers(state))}・板の知らせ {len(board_now(state))}・習っている子 {len(g['kids'])}"
           + " / " + " / ".join(f"{k} {IS[k]} {_yd(g['f'][k]) if k in g['f'] else 'まだ'}" for k in ("i1", "i2", "i3"))
           + f" / i4 を割った年 {'・'.join(map(str, g['i4_broken'])) or 'なし'} / 入口 {'○' if entrance(state) else 'まだ'}"]
    for y in sorted(g["rows"], key=int)[-3:]:
        out.append(row_text(g["rows"][y]))
    return out


def notes_of(state, y):
    """y 年の知らせ (年報)"""
    return list(_g(state)["notes"].get(str(y)) or [])
