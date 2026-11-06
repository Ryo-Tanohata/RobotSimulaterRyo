"""G11「お金と市場」(第 6 部「鉄とお金の帝国」のまん中の G。2026-11-05 本人の決め「お任せします」。docs/society_phase/G11_design.md)

- G11 に入るのは step.py next_part --closed-by-decision だけ (G10 を本人の決めで閉じてから。g7.start_g11)。G10 までは、このファイルを読みこみもしない
  (g7・era2・yardstick は state の g7.g11 があるときだけ、関数の中で読みこむ)。だから G1〜G10 は、お題・state・出来事・乱数が前と 1 バイトも変わらない
- 条件 (3 つとも【村が決めた】。3 つともそろうと G11 の終わり。部の終わりではない):
  c1 印のかたまりで払う: 暦の 1 年に、村 (と家) とよその集落の出し入れ (申し出を受ける・貸す・返される・市で替える・交換に行く・引きかえ) のうち、
     印のかたまりで払ったか受けた回が半分以上で、4 回以上
  c2 市の日: 掟で市の日が決まっていて、暦の 1 年に、よその集落の人が来て 1 つ以上替えた市が 2 回以上。これが 2 年つづく
  c3 印のかたまりで貸し、字で書く: 暦の 1 年に、よその村への貸し・返しを印のかたまりでした回が 1 回以上あり、そのとき村に読み書きできる大人がいた
     (量を字で書いた)。これが 2 年つづく (税を印のかたまりで、は家が印のかたまりを持たないので、いまの仕組みでは起きない。G11_design.md 3.)
- F: F1 印のかたまりができた / F2 市が立った / F3 印のかたまりで払った / F4 印のかたまりの貸しを字で書いた
- G10 の物差し (c1〜c3) は「ならべて測る」(数えて記録するが、G11 は進めない)。G10 の仕組み (黒い金属・字・直し ①〜④) は動きつづける
- 足した仕組み (小さく 3 つ + 帳簿 1 つ): 印のかたまりを作る (仕事「印のかたまりを作る」・集まりの欄 mark)・印のかたまりで払う
  (集まりの欄 pay・redeem。よその村が受けとる決まり・引きかえ)・市の日 (掟の market_day・年の方針の market)・印と市の帳簿
- G10 から学んだこと (入る日から): 作れる人の家は答える家に足す (key_houses)・選べる人に名前で知らせる (_mine・feel_note)・
  休む / 物で払うに変わったわけを出来事に残す (rest_why・_fail)・道の見張りは答える人のうち選べる人で数える (paths)・進みは段と数をつなげる (progress)
- 乱数は使わない。数はみな【仮定】。村の人に見せる文には「お金」「硬貨」「貨幣」「通貨」「市場」「銀行」と g10.WORDS を書かない (WORDS。試しで確かめる)
"""
import json
import math

import era2
import g10
import hints
from world import log

YEAR, SEASON_DAYS = era2.YEAR, era2.SEASON_DAYS
COIN = "印のかたまり"  # 村の人に見せる呼び名
ACT_COIN = "印のかたまりを作る"  # 新しい仕事 (world.ACTS7 に足した。G11 で作れる人がいるときだけ選べる)
CARD_COIN = "H10-01"  # 印のある金属のかたまり (札はもうある。hint_cards.json)
COIN_PER_DAY = 10  # 1 人 1 日に作れる数【仮定】(1 個 約 5 g。鎌 1 本 = 200 個の目安)
COIN_VALUE = 10  # 掟で決まるまでの、1 個のねうち (草の種のつかみ)【仮定】
COIN_CHAR_KG = g10.IRON_CHAR_KG / 200  # 1 個に要る炭 (帳簿に書くだけ)
C1_SHARE, C1_MIN = 0.5, 4  # c1: 出し入れの半分以上・1 年 4 回以上
C2_MARKETS, C2_YEARS = 2, 2  # c2: 来て替えた市が 1 年 2 回以上・2 年つづく
C3_YEARS = 2  # c3: 印の貸し・返しを字で書いた年が 2 年つづく
MARKET_WALK = 2  # 市に来る集落: 歩いて 2 日以内で、行き来のあるところ
REFUSE_YEARS = 2  # 村が引きかえを断ると、2 年は受けとらない
PATH_YEARS = 2  # 道の見張り: 選べる答える人が 2 年つづけて 0 人なら止めて相談
RATE_MAX = 10 ** 4  # ねうち (草の種のつかみ) の上限 (掟の rate と同じ)
# 2026-11-06 本人の決め「②③を直して続ける」(docs/society_phase/G11_stall_diag.md 7. の 1〜3。「した直し」): G11_FIX_FROM (158年の年の集まり) からの直し 3 つ
#   ① 市の日 (market_day) とねうち (coin_rate) を、年の集まりの村の欄にする (mark・pay と同じ g7._tally。掟の道も残す。新しく決めたほうを使う)
#   ② 道の見張り: 条件 1 は、前の 1 年によその集落との出し入れが 0 回なら 0 と数える (報告にも 1 行)。条件 2 は ① の欄で選べる人を数える
#   ③ お題だけの行: 印のかたまりで村が何をできるか・申し出に来なくなった村・決めない (null) と申し出は受けない・市の日に来る村
G11_FIX_FROM = 18959
FAIL_REPORT = 3  # 1 年に「選んだのにできなかった」がこれだけあれば、報告に書く
MARK_MAX = 30  # 村の印の言葉の長さ
WORDS = ("お金", "硬貨", "貨幣", "通貨", "市場", "銀行") + g10.WORDS  # 村の人に見せる G11 の文に書かない言葉
PAY_CHOICES = ("物", "印")
REDEEM_CHOICES = ("引きかえない", "引きかえる")
MARKET_GIVE = ("草の種", "鎌", "土器", "印")  # 市で村が出してよい物
MARKET_TAKE = ("ヤギ", "黒曜石", "土器", "草の種")  # 市で村が受けてよい物
FS = {"F1": "印のかたまりができた", "F2": "市が立った", "F3": "印のかたまりで払った", "F4": "印のかたまりの貸しを字で書いた"}
CS = {"c1": "印のかたまりで払う", "c2": "市の日", "c3": "印のかたまりで貸し、字で書く"}


def on(state):
    return "g11" in ((state.get("era2") or {}).get("g7") or {})


def _g(state):
    return state["era2"]["g7"]["g11"]


def fixed(state):
    """2026-11-06 の直し (①〜③) が効くか: G11_FIX_FROM より後の日はいつも。G11_FIX_FROM の日 (お題は前のコードで出ていた) は、
    step.py refresh_prompts が g7.g11.fix を書いたあとだけ (だから、その日までの歩をやり直しても、state もお題も前と 1 バイトも同じ。g10.fixed と同じ形)"""
    return on(state) and (state["day"] > G11_FIX_FROM or (state["day"] == G11_FIX_FROM and "fix" in _g(state)))


def mark_fix(state, why):
    """refresh_prompts から: G11_FIX_FROM の日に、直しを今の歩から入れたことを g7.g11.fix に残す (その日より前なら何もしない)"""
    if on(state) and state["day"] >= G11_FIX_FROM and "fix" not in _g(state):
        _g(state)["fix"] = {"day": state["day"], "why": why}


def trust_fixed(state):
    """信頼の直し (era2.TRUST_FIX_FROM。G11_stall_diag.md「した直し 2」) のお題の行を出すか: その日より後はいつも。その日 (お題は前のコードで出ていた) は、
    step.py refresh_prompts が g7.g11.trust_fix を書いたあとだけ (fixed と同じ形。世界の決まりのほうは era2.trust_fixed が歩の日で決める)"""
    return on(state) and (state["day"] > era2.TRUST_FIX_FROM or (state["day"] == era2.TRUST_FIX_FROM and "trust_fix" in _g(state)))


def mark_trust_fix(state, why):
    """refresh_prompts から: era2.TRUST_FIX_FROM の日に、信頼の直しのお題の行を今の歩から入れたことを g7.g11.trust_fix に残す (その日より前なら何もしない)"""
    if on(state) and state["day"] >= era2.TRUST_FIX_FROM and "trust_fix" not in _g(state):
        _g(state)["trust_fix"] = {"day": state["day"], "why": why}


def _y(state):
    return str(state["day"] // YEAR)


def _gw(goods):
    return era2._gw(goods)


# ---------------- G11 に入る (g7.start_g11 から) ----------------

def start(state):
    """G11 の state を作る: G10 の物差し (条件・刈る人日・道の見張り・字で比べた回) を g7.before.G10.g10 に写し、条件と道の見張りは数え直す
    (F は村に起きたことなので消さない。字を習う道は F2 を見る)。印のかたまりは入る日に作れるようになる (出来事「試す」)"""
    g7s, D = state["era2"]["g7"], state["day"]
    t = g7s["g10"]
    g7s.setdefault("before", {}).setdefault("G10", {})["g10"] = {
        "reached": dict(t["reached"]), "c": dict(t["c"]), "reap": {k: dict(v) for k, v in t["reap"].items()}, "path": {k: dict(v) for k, v in t["path"].items()},
        "letters": t["letters"], "made": len(t["made"]), "region": dict(t.get("region") or {}), "fix": t.get("fix")}
    t["c"], t["path"] = {}, {}
    g = g7s["g11"] = {"start": D, "mark": None, "value": None, "coins": {"village": 0, "unmarked": 0, "others": {}}, "made": [],
                      "pay": {"choice": "物", "day": None, "votes": ""}, "redeem": {"choice": "引きかえる", "day": None, "votes": ""},
                      "market": None, "market_used": {}, "markets": {}, "flows": {}, "flow_log": [], "credit": {}, "refused": [],
                      "fails": [], "path": {}, "ledger": [], "reached": {}, "c": {}}
    log(state, "試す", None, f"よその便りで聞いた「印のある金属のかたまり」を、村の黒い金属で作れるようになった (作れる人: {'・'.join(g10.smiths_now(state)) or 'いない'})",
        card=CARD_COIN, coin=True)
    return g


# ---------------- 印のかたまりを作る (仕事「印のかたまりを作る」。g7.role_day から) ----------------

def smiths(state):
    return g10.smiths_now(state)


def can_make(state, name, with_=()):
    """「印のかたまりを作る」を選べるか: 黒い金属を作れる人か、その人と一緒に (with) 作る人"""
    return g10.iron_ready(state) and (g10.smith(state, name) or any(g10.smith(state, w) for w in with_ or ()))


def acts(state):
    return [ACT_COIN] if smiths(state) else []


def make_day(state, p, t):
    """1 日: 作れる人 (と、同じ日に一緒に作る、with に書いた作れる人のいる人) が 10 個作る。一緒に作った人は、次の季節から作れる人 (g10 の腕)"""
    g, D = _g(state), state["day"]
    mates = [q for q in era2.adults(state) if q is not p and (q.get("today") or {}).get("activity") in (ACT_COIN, g10.ACT_MAKE)]
    helped = [q for q in mates if q["name"] in ((p.get("plan") or {}).get("with") or []) and g10.smith(state, q["name"])]
    if not g10.iron_ready(state) or not (g10.smith(state, p["name"]) or helped):
        why = rest_why(state, p["name"], ACT_COIN, None, (p.get("plan") or {}).get("with"), today=True)
        t.setdefault("events", []).append(log(state, "休む", p["name"], why, rest_why=ACT_COIN))
        if not any(f["who"] == p["name"] and f["what"] == ACT_COIN and f["day"] // SEASON_DAYS == D // SEASON_DAYS for f in g["fails"]):
            _fail(state, p["name"], ACT_COIN, why, log_it=False)  # 帳簿には 1 季節に 1 回
        return
    t10 = state["era2"]["g7"]["g10"]
    if not g10.smith(state, p["name"]) and p["name"] not in t10["pending_smiths"]:
        t10["pending_smiths"].append(p["name"])
    c = g["coins"]
    marked = g["mark"] is not None
    c["village" if marked else "unmarked"] += COIN_PER_DAY
    row = g["made"][-1] if g["made"] and g["made"][-1]["day"] == D else None
    if row is None:
        row = {"day": D, "n": 0, "by": []}
        g["made"].append(row)
    row["n"] += COIN_PER_DAY
    row["by"].append(p["name"])
    t.setdefault("events", []).append(log(state, ACT_COIN, p["name"], f"{p['name']} が、黒い金属を小さくたたいて、{'村の印を打った' if marked else 'まだ印のない'}かたまりを "
                                          f"{COIN_PER_DAY} 個作った" + (f" ({'・'.join(q['name'] for q in helped)} に教わりながら)" if helped and not g10.smith(state, p["name"]) else ""),
                                          coins=COIN_PER_DAY, marked=marked))
    if marked:
        _reach(state, "F1", D, f"{p['name']} が村の印を打った印のかたまりを作った")


def made_total(state):
    return sum(r["n"] for r in _g(state)["made"])


def rest_why(state, name, act, j, with_, today=False):
    """「印のかたまりを作る」を「休む」に変えたわけ (村の人に見せる短い文)。G11 では入る日からいつも残す"""
    if act != ACT_COIN:
        return None
    if not g10.iron_ready(state) or not smiths(state):
        return f"{name} は、村にいま黒い金属を作れる人がいないので、印のかたまりを作れず、休んだ"
    if today:
        return f"{name} は、印のかたまりの作り方を知らず、その日に一緒に作る作れる人もいなかったので、休んだ (作れる人と同じ季節に、with にその人の名前を書く)"
    return f"{name} は、印のかたまりの作り方を知らないので、休んだ (作れる人と一緒に作るなら、with にその人の名前を書く)"


def key_houses(state):
    """見本の家に必ず足す家 (G10 の直し ③ を広げる): 印のかたまりを作れる人 (黒い金属を作れる人) のいる家"""
    sm = set(smiths(state))
    return sorted({p.get("household") for p in era2.adults(state) if p["name"] in sm and p.get("household")})


# ---------------- 集まりの答え (g7.apply_year から。era2.apply_answers の前) ----------------

def _mark_text(v):
    s = str(v or "").strip().strip("「」『』\"'。 ")
    if not s or s.lower() in ("...", "null", "none", "なし", "false") or not s.isprintable():
        return ""
    return s[:MARK_MAX]


def _choice(v, choices, yes=None, no=None):
    if v is True and yes:
        return yes
    if v is False and no:
        return no
    s = str(v or "").strip()
    return next((c for c in choices if s and c in s), None)


def _market(v):
    """年の方針の market → {"give": {物: 1 年の上限}, "take": [物], "pay": bool}。読めなければ None"""
    if not isinstance(v, dict):
        return None
    give = {}
    gv = v.get("give") if isinstance(v.get("give"), dict) else {}
    for k, n in gv.items():
        good = "印" if "印" in str(k) else era2._g6_good(k)
        n = era2._num(n)
        if good in MARKET_GIVE and n and n > 0:
            give[good] = give.get(good, 0) + int(n)
    tk = v.get("take")
    tk = [tk] if isinstance(tk, str) else tk if isinstance(tk, list) else []
    take = []
    for x in tk:
        good = era2._g6_good(x)
        if good in MARKET_TAKE and good not in take:
            take.append(good)
    pay = v.get("pay") is True or "印" in str(v.get("pay") or "")
    if not give and not take:
        return None
    return {"give": dict(sorted(give.items())), "take": take, "pay": pay}


def apply_answers(state, real):
    """集まりの歩の答え: 村の印 (mark。まだ決まっていなければ)・払い方 (pay)・引きかえ (redeem)・市の方針 (market。年の集まりだけ)"""
    import g7
    g, D = _g(state), state["day"]
    at = "季節の集まりで"
    w = g7._vote_weights(state, real)
    if g["mark"] is None:
        votes = {n: _mark_text(a.get("mark")) for n, a in real.items()}
        votes = {n: v for n, v in votes.items() if v}
        ch, txt = g7._tally(state, votes, w)
        if ch:
            g["mark"] = {"text": ch, "day": D, "votes": txt}
            c = g["coins"]
            moved, c["unmarked"] = c["unmarked"], 0
            c["village"] += moved
            log(state, "印", None, f"{at}、村の印のかたまりに打つ印を「{ch}」に決めた ({txt})"
                + (f"。いままでに作った {moved} 個にも、この印を打った" if moved else ""), coin_mark=ch)
            if c["village"] > 0:
                _reach(state, "F1", D, f"村の印「{ch}」を打った印のかたまり {c['village']} 個")
    for key, choices, yes, no, slot in (("pay", PAY_CHOICES, "印", "物", "pay"), ("redeem", REDEEM_CHOICES, "引きかえる", "引きかえない", "redeem")):
        votes = {n: _choice(a.get(key), choices, yes, no) for n, a in real.items()}
        votes = {n: v for n, v in votes.items() if v}
        ch, txt = g7._tally(state, votes, w)
        if ch:
            if ch != g[slot]["choice"]:
                word = {"印": "村の物で払うときは、印のかたまりで払うことにした", "物": "村の物で払うときは、物で払うことにした",
                        "引きかえる": "よその村が持って来た印のかたまりは、約束どおり草の種と引きかえることにした",
                        "引きかえない": "よその村が持って来た印のかたまりを、草の種と引きかえないことにした"}[ch]
                log(state, "印", None, f"{at}、{word} ({txt})", coin_rule=key, choice=ch)
            g[slot] = {"choice": ch, "day": D, "votes": txt}
    if (state["era2"]["g7"].get("ask") or "") == "年":
        votes = {}
        for n, a in real.items():
            m = _market(a.get("market"))
            if m:
                votes[n] = json.dumps(m, ensure_ascii=False, sort_keys=True)
        ch, txt = g7._tally(state, votes, w)
        if ch:
            m = json.loads(ch)
            if m != {k: v for k, v in (g["market"] or {}).items() if k in ("give", "take", "pay")}:
                log(state, "印", None, f"{at}、市の日の方針を決めた: {_market_text(m)} ({txt})", market=m)
            g["market"] = dict(m, day=D, votes=txt)
        if fixed(state):  # 直し ①: 市の日とねうちも村の欄 (いちばん多い手。決めない人は数えない)
            _apply_day_rate(state, real, w, at)


def _day_of(v):
    n = era2._num(v)
    return int(n) if n and n == int(n) and 1 <= n <= SEASON_DAYS else None


def _rate_of(v):
    if isinstance(v, dict):
        v = next((x for k, x in v.items() if "印" in str(k)), None)
    n = era2._num(v)
    return min(int(n), RATE_MAX) if n and n >= 1 else None


def _apply_day_rate(state, real, w, at):
    """直し ① (G11_FIX_FROM から。年の集まりだけ): 答えの market_day (季節の何日目か) と coin_rate (印のかたまり 1 個 = 草の種何つかみ) を g7._tally で決める。
    決めた値は g7.g11.market_day・g7.g11.value に残す ({"n", "day", "votes"})。掟で決めた値より新しければ、こちらを使う (market_day()・value())"""
    import g7
    g, D = _g(state), state["day"]
    for key, slot, read in (("market_day", "market_day", _day_of), ("coin_rate", "value", _rate_of)):
        votes = {n: read(a.get(key)) for n, a in real.items() if isinstance(a, dict)}
        votes = {n: v for n, v in votes.items() if v}
        ch, txt = g7._tally(state, votes, w)
        if not ch:
            continue
        if ch != (g.get(slot) or {}).get("n"):
            word = f"市の日を、季節ごとの {ch} 日目に決めた" if slot == "market_day" else f"印のかたまり 1 個のねうちを、草の種 {ch} つかみに決めた"
            log(state, "印", None, f"{at}、{word} ({txt})", coin_rule=key, choice=ch)
        g[slot] = {"n": ch, "day": D, "votes": txt}


def _market_text(m):
    give = "・".join(f"{k} {n} {'個' if k == '印' else era2.UNIT.get(k, '')}まで" for k, n in m["give"].items()) or "出さない"
    return f"出してよい物 {give} / 受ける物 {'・'.join(m['take']) or 'なし'} / 印のかたまりで払う・受ける {'はい' if m['pay'] else 'いいえ'}"


# ---------------- 掟 (g7.law_extra から): 市の日・印のかたまりのねうち ----------------

def law_extra(state, law, prop):
    md = era2._num(prop.get("market_day"))
    if md and 1 <= md <= SEASON_DAYS:
        law["market_day"] = int(md)
        law["text"] += f" (市の日: 季節ごとの {int(md)} 日目)"
    rate = prop.get("rate")
    if isinstance(rate, dict):
        n = era2._num(next((v for k, v in rate.items() if "印" in str(k)), None))
        if n and n > 0:
            law["coin_rate"] = min(int(n), 10 ** 4)
            law["text"] += f" (印のかたまり 1 個 = 草の種 {law['coin_rate']} つかみ)"


def _law_key(state, key):
    return next((l for l in reversed(state.get("laws", [])) if l.get("status") == "採用" and l.get(key)), None)


def _newer(field, law):
    """直し ①: 村の欄 (g7.g11 の {"n", "day"}) と掟のうち、新しく決めたほう (同じ日なら村の欄)。直しの前は村の欄がない (value は None) ので、掟のまま"""
    if isinstance(field, dict) and (not law or field["day"] >= (law.get("changed") or law.get("day") or 0)):
        return field["n"]
    return None


def market_day(state):
    """市の日 (季節の何日目か。1〜30): 掟で決まったもの、か (直し ① から) 年の集まりで決めたもの。なければ None"""
    l = _law_key(state, "market_day")
    n = _newer(_g(state).get("market_day"), l)
    return n if n is not None else l["market_day"] if l else None


def value(state):
    """印のかたまり 1 個のねうち (草の種のつかみ)。掟で決まっていればその数。直し ① から、年の集まりで決めたほうが新しければその数"""
    l = _law_key(state, "coin_rate")
    n = _newer(_g(state).get("value"), l)
    return n if n is not None else l["coin_rate"] if l else COIN_VALUE


# ---------------- 受けとる決まりと払い ----------------

def others_total(state):
    return sum(_g(state)["coins"]["others"].values())


def refused_recent(state):
    D = state["day"]
    return [d for d in _g(state)["refused"] if D - d < REFUSE_YEARS * YEAR]


def accept_why(state, n):
    """よその村が、村の印のかたまり n 個を受けとらないわけ (受けとるなら None)。乱数なし"""
    g = _g(state)
    if g["mark"] is None:
        return "村の印がまだ決まっていないので、印のかたまりは払いに使えない"
    if g["coins"]["village"] < n:
        return f"村の印のかたまりが {g['coins']['village']} 個で、{n} 個に足りない"
    r = refused_recent(state)
    if r:
        return f"村が {r[-1]} 日目に引きかえを断ったので、よその村は 2 年のあいだ印のかたまりを受けとらない"
    need = (others_total(state) + n) * value(state)
    if era2._g6_have(state, "村", "草の種") < need:
        return "村の蓄えの草の種が、よその村にある印のかたまりをみな引きかえられるほどないので、受けとらない"
    return None


def _fail(state, who, what, why, log_it=True):
    """選んだのにできなかったこと (休む・物で払った・よそが受けとらない)。帳簿に残し、log_it なら出来事にも (お題の節に出す)"""
    g, D = _g(state), state["day"]
    g["fails"].append({"day": D, "year": D // YEAR, "who": who, "what": what, "why": why})
    g["fails"] = g["fails"][-60:]
    if log_it:
        log(state, "印のかたまり", who, why, coin_fail=what)


def flow(state, o, kind, coin=False, n=0):
    """出し入れ 1 回を数える (c1)。coin: 印のかたまりで払ったか受けた。F3 も"""
    g, D = _g(state), state["day"]
    row = g["flows"].setdefault(_y(state), {"all": 0, "coin": 0})
    row["all"] += 1
    row["coin"] += int(bool(coin))
    g["flow_log"].append({"day": D, "other": o["id"] if o else None, "kind": kind, "coin": n if coin else 0})
    g["flow_log"] = g["flow_log"][-80:]
    if coin:
        _reach(state, "F3", D, f"{o['name'] if o else 'よその村'} と、{kind}で印のかたまり {n} 個")


def _credit(state, o, kind, n):
    """印のかたまりでした貸し・返し (c3)。村に読み書きできる大人がいれば、量を字で書いた"""
    g, D = _g(state), state["day"]
    rd = g10.readers(state)
    row = g["credit"].setdefault(_y(state), {"coin": 0, "written": 0})
    row["coin"] += 1
    if rd:
        row["written"] += 1
        _reach(state, "F4", D, f"{o['name']} への{kind}の印のかたまり {n} 個を、{rd[0]} が字で書いた")
    return rd


def pay_choice(state):
    return _g(state)["pay"]["choice"]


def pay_coins(state, off, o, at):
    """申し出を村の物で受けるとき (era2._g6_decide から): 村が「印で払う」と決めていれば、払う印のかたまりの数。受けとらなければ 0 (わけを残す)。
    印で払わないなら None"""
    if pay_choice(state) != "印":
        return None
    val = sum(era2.VALUE.get(k, 0) * m for k, m in off["want"].items())
    if val <= 0:
        return None
    n = math.ceil(val / value(state))
    why = accept_why(state, n)
    if why:
        _fail(state, None, "払う", f"{at}、村は {o['name']} の申し出 [{off['id']}] に印のかたまりで払おうとしたが、{why}。物で払う")
        return 0
    return n


def decide_with_coins(state, c6, off, o, n, lead, at, votes):
    """申し出 (交換・貸して) を、村の印のかたまりで受ける (era2._g6_decide の村の物の道と同じ順。貸し借りは草の種のつかみで残す)"""
    import g7
    g6, g, D = era2._g6(state), _g(state), state["day"]
    c = g["coins"]
    if off["kind"] == "貸して":
        rate = g7.loan_rate(state, c6, off, lead)
        if g7.loan_refused(o, rate):
            log(state, "よその村", None, f"{at}、村は {o['name']} の申し出 [{off['id']}] に上乗せ {round(rate * 10, 1):g} 割をつけて答えたが、{o['name']} は借りなかった ({votes})",
                other=o["id"], offer=off["id"], rate=rate)
            return
        c["village"] -= n
        c["others"][o["id"]] = c["others"].get(o["id"], 0) + n
        goods = dict(off["want"])
        d = {"id": f"D{g6['next_debt']}", "other": o["id"], "lender": "村", "goods": goods, "day": D, "due": D + YEAR,
             "proof": None, "mem": off["mem"], "status": "まだ", "end": None, "coin": n}
        if rate:
            d["rate"] = rate
        g6["next_debt"] += 1
        g6["debts"].append(d)
        era2._g6_contact(state, o)
        rd = _credit(state, o, "貸し", n)
        back = f"1 年のうちに、上乗せ {round(rate * 10, 1):g} 割をつけて {_gw(g7.owed(d))} を返すと言った" if rate else f"1 年のうちに {_gw(goods)} を返すと言った"
        log(state, "貸し借り", None, f"{at}、村は {o['name']} に、草の種 {goods.get('草の種', 0)} つかみのかわりに、印のかたまり {n} 個を貸した [{d['id']}] ({back}"
            + (f"。貸した量は {rd[0]} が字で書いた" if rd else "") + f"。{votes})", other=o["id"], debt=d["id"], coins=n, **({"rate": rate} if rate else {}))
        flow(state, o, "貸し", True, n)
        return
    era2._node_add(o, off["give"], -1)
    in_ids = []
    to = era2._g6_put(state, "村", off["give"], off["goats_in"], in_ids)
    c["village"] -= n
    c["others"][o["id"]] = c["others"].get(o["id"], 0) + n
    era2._g6_note(state, o, {}, (off["give"],))
    era2._g6_contact(state, o)
    sx = (" (" + "・".join(f"{x['sex']} {x['age']} 歳" for x in off["goats_in"]) + ")") if off["goats_in"] else ""
    log(state, "交換", None, f"{at}、村は {o['name']} の申し出 [{off['id']}] を受け、{_gw(off['want'])} のかわりに印のかたまり {n} 個を払って、{_gw(off['give'])}{sx} を受けとった ({votes})",
        other=o["id"], offer=off["id"], coins=n, moves=[era2._mv(to, 1, off["give"], in_ids)])
    flow(state, o, "交換", True, n)


def repay_coins(state, o, d, bring):
    """よその村が貸し借りを返しに来た (era2._g6_repay から): 村の印のかたまりを持っていれば、それで先に返す (草の種の貸しだけ)。
    戻り値: (物で持って来る分, 印で返した分の草の種のつかみ {"草の種": n})"""
    c = _g(state)["coins"]
    have = c["others"].get(o["id"], 0)
    if d.get("lender") != "村" or have <= 0 or "草の種" not in bring:
        return bring, {}
    v = value(state)
    k = min(have, bring["草の種"] // v)
    if k <= 0:
        return bring, {}
    c["others"][o["id"]] = have - k
    c["village"] += k
    out = dict(bring)
    out["草の種"] -= k * v
    if out["草の種"] <= 0:
        out.pop("草の種")
    rd = _credit(state, o, "返し", k)
    log(state, "印のかたまり", None, f"{o['name']} の人は、[{d['id']}] の分の一部を、村の印のかたまり {k} 個 (草の種 {k * v} つかみ分) で返した"
        + (f"。{rd[0]} が字で書いておいた量と読み合わせた" if rd else ""), other=o["id"], debt=d["id"], coins=k)
    _g(state)["repaid_coin"] = k
    return out, {"草の種": k * v}


def repay_flow(state, o):
    """返しを 1 回数える (repay_coins のあと)"""
    k = _g(state).pop("repaid_coin", 0)
    flow(state, o, "返し", bool(k), k)


# ---------------- 市 (g7.region_day から、毎日) ----------------

def visitors(state):
    """市に来る集落: 知っていて、行き来があり (交換・貸し借りをしたことがある)、歩いて 2 日以内で、なくなっていない集落 (番号の順)"""
    import g7
    return [o for o in g7._others(state) if o.get("known") is not None and o.get("contacts") and o.get("days", 9) <= MARKET_WALK
            and not o.get("gone") and o.get("people", 0) > 0]


def _used(state, good):
    return _g(state)["market_used"].get(_y(state), {}).get(good, 0)


def _use(state, good, n):
    row = _g(state)["market_used"].setdefault(_y(state), {})
    row[good] = row.get(good, 0) + n


def _left(state, m, good):
    if good == "印" and good not in m["give"]:  # 印で払うと決めて、印の上限を書いていなければ、村にある分まで
        return _g(state)["coins"]["village"]
    return max(0, m["give"].get(good, 0) - _used(state, good))


def market(state):
    """市の日 (掟の market_day が、季節の何日目か) に、近くの集落の人が来る。村の方針 (market) のとおりに替える (答えはいらない)。乱数なし"""
    md = market_day(state)
    D = state["day"]
    if not md or D % SEASON_DAYS + 1 != md:
        return
    g = _g(state)
    came = visitors(state)
    mrow = {"day": D, "came": [o["id"] for o in came], "deals": 0}
    g["markets"].setdefault(_y(state), []).append(mrow)
    if not came:
        log(state, "市", None, "市の日だったが、よその村の人はだれも来なかった", market=True)
        return
    m = g["market"]
    names = "・".join(o["name"] for o in came)
    if not m:
        log(state, "市", None, f"市の日に、{names} の人が来たが、村は市の方針 (market) を決めていないので、見て帰った", market=True, came=mrow["came"])
        return
    for o in came:
        r = _deal(state, o, m)
        if r:
            mrow["deals"] += 1
    if mrow["deals"]:
        _reach(state, "F2", D, f"市の日に {names} の人が来て、{mrow['deals']} つの集落と替えた")
    else:
        log(state, "市", None, f"市の日に、{names} の人が来たが、替えられる物がなく、見て帰った", market=True, came=mrow["came"])


def _deal(state, o, m):
    """1 つの集落と市で替える。(1) 集落の出す物を村が受けるなら、印 (方針で印で払うなら) か、村が出してよい物で払う。
    (2) 集落が村の印のかたまりを持っていれば、それで村が出してよい物を買う。どちらか 1 つ (1) が先"""
    g, c = _g(state), _g(state)["coins"]
    v = value(state)
    sup, wants = era2._g6_supply(o), era2._g6_wants(state, o)
    good = next((k for k in m["take"] if sup.get(k, 0) >= (5 if k == "黒曜石" else 300 if k == "草の種" else 1)), None)
    if good:
        k = 5 if good == "黒曜石" else 300 if good == "草の種" else 1
        val = era2.VALUE[good] * k
        n = math.ceil(val / v)
        if m["pay"]:
            why = accept_why(state, n) if _left(state, m, "印") >= n else f"市の方針の印のかたまりの上限 ({m['give'].get('印', 0)} 個) をこえる"
            if not why:
                era2._node_add(o, {good: k}, -1)
                ids = []
                to = era2._g6_put(state, "村", {good: k}, ({"sex": "メス", "age": 2},) * k if good == "ヤギ" else (), ids)
                c["village"] -= n
                c["others"][o["id"]] = c["others"].get(o["id"], 0) + n
                _use(state, "印", n)
                era2._g6_note(state, o, {}, ({good: k},))
                era2._g6_contact(state, o)
                log(state, "市", None, f"市の日に、{o['name']} の人が {_gw({good: k})} を出し、村は印のかたまり {n} 個で受けとった", market=True, other=o["id"], coins=n,
                    moves=[era2._mv(to, 1, {good: k}, ids)])
                flow(state, o, "市", True, n)
                return True
            _fail(state, None, "市", f"市の日に、村は {o['name']} に印のかたまりで払おうとしたが、{why}。物で替える")
        pay, left = {}, val
        for w in ("鎌", "土器", "草の種"):
            if w == good:
                continue
            q = min(wants.get(w, 0), _left(state, m, w), era2._g6_have(state, "村", w), int(left // era2.VALUE[w]))
            if q > 0:
                pay[w], left = q, left - q * era2.VALUE[w]
        if pay and left * 2 <= val:
            out_ids = []
            gave = era2._g6_take(state, "村", pay, out_ids)
            for w, q in gave.items():
                _use(state, w, q)
            era2._node_add(o, gave, 1)
            era2._node_add(o, {good: k}, -1)
            ids = []
            to = era2._g6_put(state, "村", {good: k}, ({"sex": "メス", "age": 2},) * k if good == "ヤギ" else (), ids)
            era2._g6_note(state, o, gave, ({good: k},))
            era2._g6_contact(state, o)
            log(state, "市", None, f"市の日に、{o['name']} の人が {_gw({good: k})} を出し、村は {_gw(gave)} で替えた", market=True, other=o["id"],
                moves=[era2._mv("村", -1, gave, out_ids), era2._mv(to, 1, {good: k}, ids)])
            flow(state, o, "市")
            return True
    have = c["others"].get(o["id"], 0)
    if have > 0:
        buy, spent = {}, 0
        for w in ("草の種", "鎌", "土器"):
            q = min(wants.get(w, 0), _left(state, m, w), era2._g6_have(state, "村", w), int((have - spent) * v // era2.VALUE[w]))
            if q > 0:
                buy[w] = q
                spent += math.ceil(q * era2.VALUE[w] / v)
        spent = min(spent, have)
        if buy and spent > 0:
            out_ids = []
            gave = era2._g6_take(state, "村", buy, out_ids)
            for w, q in gave.items():
                _use(state, w, q)
            era2._node_add(o, gave, 1)
            c["others"][o["id"]] = have - spent
            c["village"] += spent
            era2._g6_note(state, o, gave)
            era2._g6_contact(state, o)
            log(state, "市", None, f"市の日に、{o['name']} の人が、村の印のかたまり {spent} 個で {_gw(gave)} を買っていった", market=True, other=o["id"], coins=spent,
                moves=[era2._mv("村", -1, gave, out_ids)])
            flow(state, o, "市", True, spent)
            return True
    return False


# ---------------- 季節の終わり (g7.season_end。G10 の季節の終わりのあと) ----------------

def _redeem(state):
    """よその村が、持っている村の印のかたまりを草の種と引きかえる (その村が苦しい年か、蓄えが 1 人 100 つかみより少ないとき)。
    村が「引きかえない」と決めていれば断る (そのあと 2 年、よその村は受けとらない)。乱数なし"""
    import g7
    g, D = _g(state), state["day"]
    c, v = g["coins"], value(state)
    for o in g7._others(state):
        have = c["others"].get(o["id"], 0)
        if have <= 0 or o.get("gone") or not (o["bad"] is not None or o["grain"] < o["people"] * 100):
            continue
        if g["redeem"]["choice"] == "引きかえない":
            g["refused"].append(D)
            _fail(state, None, "引きかえ", f"{o['name']} の人が、村の印のかたまり {have} 個を草の種と引きかえに来たが、村は引きかえないと決めていたので、断った。"
                  "よその村は、これから 2 年、村の印のかたまりを受けとらない")
            continue
        k = min(have, era2._g6_have(state, "村", "草の種") // v)
        if k > 0:
            ids = []
            got = era2._g6_take(state, "村", {"草の種": k * v}, ids)
            era2._node_add(o, got, 1)
            c["others"][o["id"]] = have - k
            c["village"] += k
            log(state, "印のかたまり", None, f"{o['name']} の人が、村の印のかたまり {k} 個を持って来て、約束どおり草の種 {k * v} つかみと引きかえた",
                other=o["id"], coins=k, moves=[era2._mv("村", -1, got, ids)])
            flow(state, o, "引きかえ", True, k)
        if k < have:
            g["refused"].append(D)
            _fail(state, None, "引きかえ", f"{o['name']} の人が、村の印のかたまり {have - k} 個を引きかえに来たが、村の蓄えに草の種が足りず、引きかえられなかった。"
                  "よその村は、これから 2 年、村の印のかたまりを受けとらない")


def _reach(state, f, day, why):
    g = _g(state)
    if f in g["reached"] or day is None:
        return
    g["reached"][f] = day
    log(state, "目盛り", None, f"目盛り: G11 の {f}「{FS[f]}」に届いた ({why})", g="G11", f=f)


def _cond(state, c, day, why):
    g = _g(state)
    if c not in g["c"]:
        g["c"][c] = day
        log(state, "目盛り", None, f"目盛り: G11 の条件 {c[1:]}「{CS[c]}」に届いた ({why})", g="G11", c=c)


def markets_with_deals(state, y):
    return sum(1 for r in _g(state)["markets"].get(str(y), []) if r["deals"] > 0)


def season_end(state):
    """G11 の季節の終わり: 引きかえ → c1 (この年の出し入れ) → c2 (市) → c3 (字で書いた印の貸し) → 年の終わりの帳簿"""
    g, D = _g(state), state["day"]
    _redeem(state)
    y = D // YEAR
    row = g["flows"].get(str(y)) or {"all": 0, "coin": 0}
    if row["coin"] >= C1_MIN and row["coin"] >= C1_SHARE * row["all"]:
        _cond(state, "c1", D, f"この年の出し入れ {row['all']} 回のうち、印のかたまりで {row['coin']} 回")
    if market_day(state) and all(markets_with_deals(state, y - i) >= C2_MARKETS for i in range(C2_YEARS)):
        _cond(state, "c2", D, f"市の日に、よその村の人が来て替えた市が、{C2_YEARS} 年つづけて 1 年 {C2_MARKETS} 回以上 (この年 {markets_with_deals(state, y)} 回)")
    if all(((g["credit"].get(str(y - i)) or {}).get("written", 0) >= 1) for i in range(C3_YEARS)):
        _cond(state, "c3", D, f"印のかたまりの貸し・返しを字で書いた年が {C3_YEARS} 年つづいた")
    if (D + 1) % YEAR == 0:
        made = sum(r["n"] for r in g["made"] if r["day"] // YEAR == y)
        g["ledger"].append({"year": y, "day": D, "made": made, "char_kg": round(made * COIN_CHAR_KG, 2), "village": g["coins"]["village"],
                            "unmarked": g["coins"]["unmarked"], "others": dict(sorted(g["coins"]["others"].items())), "flows": dict(row),
                            "markets": len(g["markets"].get(str(y), [])), "markets_deals": markets_with_deals(state, y),
                            "credit": dict(g["credit"].get(str(y)) or {}), "fails": sum(1 for f in g["fails"] if f["year"] == y),
                            "readers": len(g10.readers(state)), "smiths": len(smiths(state)), "value": value(state)})
        g["ledger"] = g["ledger"][-40:]


def reached(state, f):
    return bool(on(state) and _g(state)["reached"].get(f))


def done(state):
    return {c: c in _g(state)["c"] for c in CS}


def progress(state):
    """条件ごとの進み (段 × 1000 + 数。大きいほど進んだ。yardstick._stall が年の終わりに読む):
    c1: 段 (0 作れない / 1 作れる / 2 印が決まった / 3 F1 / 4 F3) × 1000 + この年の、印で払った割合 (‰)
    c2: 段 (0 市の日がない / 1 市の日が決まった / 2 F2) × 1000 + この年の、来て替えた市の数 × 100
    c3: 段 (0 なし / 1 印で払った (F3) / 2 F4) × 1000 + 字で書いた年がつづいた数 × 100"""
    g = _g(state)
    y = state["day"] // YEAR
    re_ = g["reached"]
    s1 = 4 if "F3" in re_ else 3 if "F1" in re_ else 2 if g["mark"] else 1 if smiths(state) else 0
    row = g["flows"].get(str(y)) or {"all": 0, "coin": 0}
    c1 = s1 * 1000 + (round(1000 * row["coin"] / row["all"]) if row["all"] else 0)
    s2 = 2 if "F2" in re_ else 1 if market_day(state) else 0
    c2 = s2 * 1000 + markets_with_deals(state, y) * 100
    run = 0
    while (g["credit"].get(str(y - run)) or {}).get("written", 0) >= 1:
        run += 1
    s3 = 2 if "F4" in re_ else 1 if "F3" in re_ else 0
    return {"c1": c1, "c2": c2, "c3": s3 * 1000 + run * 100}


# ---------------- 道の見張り (答える人のうち、その道を自分で選べる人で数える。G11_design.md 6.) ----------------

def _house_smiths(state, name):
    p = next((q for q in era2.adults(state) if q["name"] == name), None)
    h = p.get("household") if p else None
    return [n for n in smiths(state) if h and any(q["name"] == n and q.get("household") == h for q in era2.adults(state))]


def paths(state):
    """いまのお題に答える人 (era2.answerers) のうち、まだ届いていない条件ごとに、その道を自分で選べる人の名前。
    c1: 村の印が決まっていなければ、だれでも (mark) / 作れる人と、作れる人のいる家の代表 / 村に印のかたまりがあり印が決まっていれば、だれでも (pay)。
    c2: 年の集まりなら、だれでも (掟の market_day・方針の market)。ほかの集まりは、市の日と方針が決まっていれば、だれでも (pay)。
    c3: 村に読み書きできる大人がいて、c1 の道を選べる人 (印で貸すには、印のかたまりと pay が要る)。読める人がいなければ 0。
    直し ② (G11_FIX_FROM から): 前の 1 年によその集落との出し入れが 0 回なら、c1 (と c3) は 0 (印のかたまりで払う場がない)。
    c2 は、年の集まりなら答えの market_day (直し ①。村の欄) で、だれでも選べる (直しの前の年の集まりは、掟の道だけだった)"""
    g = _g(state)
    ans = era2.answerers(state)
    year = (state["era2"]["g7"].get("ask") or "") == "年"
    sm = set(smiths(state))
    coins = g["coins"]["village"] + g["coins"]["unmarked"]
    place = not fixed(state) or flows_recent(state) > 0

    def c1_ok(n):
        return place and (g["mark"] is None or n in sm or bool(_house_smiths(state, n)) or (coins > 0 and g["mark"] is not None))
    out = {"c1": [n for n in ans if c1_ok(n)],
           "c2": [n for n in ans if year or (market_day(state) and g["market"])],
           "c3": [n for n in ans if c1_ok(n)] if g10.readers(state) else []}
    return {k: v for k, v in out.items() if k not in g["c"]}


def flows_recent(state):
    """直し ②: 前の 1 年 (この日までの 120 日) の、村 (と家) とよその集落の出し入れの回数 (flow_log から)"""
    D = state["day"]
    return sum(1 for f in _g(state)["flow_log"] if D - YEAR < f["day"] <= D)


def _chose(state, real):
    """この集まりで、道を実際に選んだ答える人の数 (作る・印を出す・市の日を出す・方針・印で払う)"""
    k = 0
    for n, a in real.items():
        if not isinstance(a, dict):
            continue
        txt = json.dumps({x: a.get(x) for x in ("year", "job", "family")}, ensure_ascii=False)
        prop = a.get("proposal") if isinstance(a.get("proposal"), dict) else {}
        if ACT_COIN in txt or _mark_text(a.get("mark")) or _choice(a.get("pay"), PAY_CHOICES, "印", "物") == "印" or _market(a.get("market")) \
                or era2._num(prop.get("market_day")) or (fixed(state) and (_day_of(a.get("market_day")) or _rate_of(a.get("coin_rate")))):
            k += 1
    return k


def count_paths(state, real):
    """集まりの答えを当てはめるとき (g7.apply_year から): この集まりの、道を選べた人・選んだ人をその年 (この歩の季節の年) に足す"""
    g = _g(state)
    y = str((state["day"] + 1) // YEAR)
    row = g["path"].setdefault(y, {"meetings": 0, "c1": 0, "c2": 0, "c3": 0, "chose": 0, "who": {}})
    row["meetings"] += 1
    for k, names in paths(state).items():
        row[k] += len(names)
        if names:
            row["who"][k] = sorted(set(row["who"].get(k, [])) | set(names))[:12]
    row["chose"] += _chose(state, real)


def fails_year(state, y):
    return [f for f in _g(state)["fails"] if f["year"] == y]


def path_consult(state, done_list):
    """年の終わり: まだ届いていない条件の道を、自分で選べる答える人が、G11 に入ってからのまる 2 年つづけて 0 人なら止めて相談 (仕組みのまちがい)。一度ずつ"""
    g, D = _g(state), state["day"]
    y = (D + 1) // YEAR - 1
    y0 = (g["start"] + 1) // YEAR
    for k in ("c1", "c2", "c3"):
        if k in g["c"]:
            continue
        ys = [y - i for i in range(PATH_YEARS)]
        if ys[-1] < y0:
            continue
        if all((g["path"].get(str(x)) or {}).get(k, 0) == 0 for x in ys):
            if not any(c["why"] == f"g11_path_{k}" and c.get("year") == y for c in done_list):
                return {"why": f"g11_path_{k}", "year": y, "day": D,
                        "text": f"G11 の条件 {k[1:]} ({CS[k]}) の道を、自分で選べる答える人が {PATH_YEARS} 年つづけていなかった (仕組みのまちがいとして相談)"}
    return None


def report_lines(state):
    """報告に書くこと (止めない): この年の「選んだのにできなかった」が 3 回以上・読める人が 0 人・作れる人が 1 つの家だけ"""
    out = []
    y = state["day"] // YEAR
    f = fails_year(state, y)
    if len(f) >= FAIL_REPORT:
        out.append(f"この年に、選んだのにできなかったこと {len(f)} 回: " + " / ".join(x["why"][:60] for x in f[-5:]))
    if not g10.readers(state):
        out.append("字を読み書きできる大人が 0 人 (条件 3 の道が閉じている。字を習う道は、読める人がいないと使えない)")
    kh = key_houses(state)
    if len(kh) == 1:
        out.append(f"印のかたまりを作れる人がいる家は {kh[0]} だけ")
    if fixed(state):  # 直し ②
        if not (_g(state)["flows"].get(str(y)) or {}).get("all"):
            out.append(f"この年 ({y}年) の、よその集落との出し入れが 0 回 (印のかたまりで払う場がない。前の 1 年に出し入れがなければ、条件 1・3 の道は 0 と数える)")
    return out


def indicators(state):
    """G11 の目安 (era2.indicators に足す。【シ】)"""
    g = _g(state)
    y = state["day"] // YEAR
    row = g["flows"].get(str(y)) or {"all": 0, "coin": 0}
    return {"g11_c1_day": g["c"].get("c1"), "g11_c2_day": g["c"].get("c2"), "g11_c3_day": g["c"].get("c3"),
            "g11_coins_village": g["coins"]["village"], "g11_coins_unmarked": g["coins"]["unmarked"], "g11_coins_others": others_total(state),
            "g11_made": made_total(state), "g11_mark": (g["mark"] or {}).get("text"), "g11_market_day": market_day(state),
            "g11_flows_all": row["all"], "g11_flows_coin": row["coin"], "g11_markets": markets_with_deals(state, y),
            "g11_fails": len(fails_year(state, y)), "g11_readers": len(g10.readers(state)), "g11_value": value(state)}


# ---------------- お題 ----------------

# 直し ③ (G11_FIX_FROM から。お題だけ。state は変えない): 印のかたまりで村が何をできるか (今の仕組みでできることだけ)
GAIN_TEXT = ("印のかたまりがあると、村はこんなことができる: 市の日に、村の物を運び出さずに、よその村の人が持って来たヤギ・黒曜石・土器・草の種を、印のかたまりで受けとれる "
             "(村の草の種は、その村が苦しい年に引きかえに来るまで減らない)。苦しい村が「貸して」と来たとき、草の種のかわりに印のかたまりを貸せる (その村は、印のかたまりで先に返す)。"
             "印のかたまりを持っているよその村は、市の日に、それで村の物を買いに来る。印のかたまりは、草の種のように、蓄えておくあいだにへることがない。\n")

def facts(state):
    """お題の決まりの文 (G11 から)。数 (半分・4 回・2 回・2 年・5 g・受けとる決まりの中の計算) は書かない"""
    v = value(state)
    fx = fixed(state)
    return ("印のかたまり: 黒い金属を作れる人は、主な仕事を「印のかたまりを作る」にすると、1 日に 10 個ほど、村の印を打った小さな黒い金属のかたまりを作れる。"
            "作れる人と同じ季節に、with にその人の名前を書いて作れば、次の季節から作れる。\n"
            "村の印は、集まりで決める (答えの mark に、印の形をことばで書く)。印が決まるまでのかたまりは、払いに使えない。\n"
            f"村は、印のかたまりを、いつでも決めたねうち ({'年の集まりの答えの coin_rate か、掟で決める' if fx else '掟で決める'}。いまは 1 個 = 草の種 {v} つかみ) の草の種と引きかえると約束している。"
            "よその村は、村がこの約束を守り、引きかえられるだけの草の種が村にあれば、印のかたまりを受けとる。村が引きかえを断ると、よその村はしばらく受けとらない。\n"
            "印のかたまりは、虫やネズミに食べられず、割れない。\n"
            + (GAIN_TEXT if fx else "") +
            "集まりの答えの pay を \"印\" にすると、村の物で申し出を受ける・貸すときに、印のかたまりで払う (\"物\" なら今までどおり物で)。"
            "よその村は、村の印のかたまりを持っていれば、返しに来たとき、それで先に返す。\n"
            + ("市の日: 年の集まりの答えの market_day か掟で、市の日 (季節の何日目か) を決めると、その日に" if fx else "市の日: 掟で市の日 (季節の何日目か) を決めると、その日に")
            + "、行き来のある近くの村の人が、物か印のかたまりを持って来る。市で村の物から何を出し、何を受けるかは、"
            "年の方針の「市」(market) で決める (市の日は集まらない。方針のとおりに替える)\n")


def text(state, p):
    """お題の節「## 印のかたまりと市」"""
    g = _g(state)
    c = g["coins"]
    y = state["day"] // YEAR
    sm = smiths(state)
    kh = key_houses(state)
    rows = [f"- 村の印: {g['mark']['text'] + ' (' + str(g['mark']['day']) + ' 日目に決めた)' if g['mark'] else '(まだ決まっていない)'}",
            f"- 印のかたまり: 村に {c['village']} 個" + (f" (印のないもの {c['unmarked']} 個)" if c["unmarked"] else "") + f" / よその村に {others_total(state)} 個。"
            f"作れる人: {'・'.join(sm) or 'いない'}" + (f" ({'・'.join(kh)})" if kh else "")
            + (f"。作り方を知らない人も、作れる人と同じ季節に「{ACT_COIN}」をして、with にその人の名前を書けば、一緒に作って、次の季節から作れる" if sm else "")]
    paid = [f for f in g["flow_log"] if f["coin"] and f["day"] // YEAR == y]
    if paid:
        on_ = {}
        for f in paid:
            on_[f["kind"]] = on_.get(f["kind"], 0) + f["coin"]
        rows.append("- この年に印のかたまりで払った・受けたこと: " + "・".join(f"{k} {n} 個" for k, n in on_.items()) + f" ({len(paid)} 回)")
    else:
        rows.append("- この年に印のかたまりで払った・受けたこと: なし")
    rows.append(f"- 払い方: 村の物で払うときは「{g['pay']['choice']}」で払う (pay)。よその村の印のかたまりは「{g['redeem']['choice']}」(redeem)")
    md = market_day(state)
    if md:
        m = g["market"]
        mk = g["markets"].get(str(y), [])
        rows.append(f"- 市の日: 季節ごとの {md} 日目。" + (f"市の方針: {_market_text(m)}" if m else "市の方針はまだない (来た人は見て帰る)")
                    + (f"。この年の市 {len(mk)} 回 (替えた市 {sum(1 for r in mk if r['deals'])} 回)" if mk else ""))
    elif fixed(state):
        rows.append("- 市の日: (まだ決まっていない。年の集まりの答えの market_day (季節の何日目か) に書くと決まる。掟の提案に market_day をつけてもよい)")
    else:
        rows.append('- 市の日: (まだ決まっていない。掟の提案に market_day (季節の何日目か) をつけて決める)')
    if fixed(state):  # 直し ③: 市の日に来る村・申し出に来なくなった村・決めないと申し出は受けない
        rows += _others_rows(state)
    rd = g10.readers(state)
    rows.append(f"- 字を読み書きできる人: {'・'.join(rd) or 'いない'}" + (" (字で書いておけば、印のかたまりで貸した量を読み合わせられる)" if rd else
                                                                     " (字を書ける人がいないと、印のかたまりで貸した量を字で書けない)"))
    f = [x for x in g["fails"] if x["year"] >= y - 1][-4:]
    if f:
        rows.append("- 印のかたまりと市で、できなかったこと: " + " / ".join(x["why"] for x in f))
    rows += _mine(state, p)
    return "\n## 印のかたまりと市\n" + "\n".join(rows) + "\n"


def _others_rows(state):
    """直し ③ (お題だけ): 市の日に来る村 (信頼に関係なく来る。visitors)・知っている村のうち、申し出に来なくなった村 (信頼 0。数は出さない)・
    申し出を決めない (null) と、受けないことになる"""
    import g7
    vis = visitors(state)
    out = ["- 市の日を決めると来る村: " + ("・".join(f"[{o['id']}] {o['name']}" for o in vis) + " (申し出に来なくなった村も、市の日には来る)" if vis
                                       else "いまはない (行き来したことがあり、歩いて 2 日以内の村だけが来る)")]
    tf = trust_fixed(state)  # 信頼の直しのあと: 信頼が低い村 (era2.TRUST_FLOOR より下) を書き、もどる道も書く (数は出さない)
    for o in g7._others(state):
        if o.get("known") is not None and not o.get("gone") and o.get("people", 0) > 0 and (o.get("trust", 0.5) < era2.TRUST_FLOOR if tf else o.get("trust", 0.5) <= 0):
            out.append(f"- [{o['id']}] {o['name']}: 村に申し出や、ここで暮らしたい人を何度も受けてもらえなかったので、"
                       + ("申し出にはあまり来ない。村と争わない年がつづけば少しずつまた来るようになり、来た申し出を村が受ければもっと来る" if tf else "もう申し出に来ない")
                       + ("。市の日には来る" if o in vis else ""))
    out.append("- 申し出 (trade・年の方針の trade_rule) を決めない (null) 人が多いと、村の物で受ける人 (\"村\") が大人の半分に届かず、"
               + ("まとめ役も \"村\" と答えなければ、" if era2._leader(state) else "") + "その申し出は受けないことになる")
    return out


def _mine(state, p):
    """その人だけの行 (入る日から。G10 の学び): 作れる人・作れる人のいる家の代表・印の話を知っている人・読める人"""
    if not p:
        return []
    g, out = _g(state), []
    sm = smiths(state)
    if p["name"] in sm:
        out.append(f"- あなた ({p['name']}) は黒い金属を作れるので、主な仕事を「{ACT_COIN}」にできる。ほかの人も、あなたと同じ季節に「{ACT_COIN}」をして "
                   "with にあなたの名前を書けば、一緒に作って作り方を覚えられる")
    fam = [n for n in _house_smiths(state, p["name"]) if n != p["name"]]
    if fam:
        out.append(f"- あなたの家の {'・'.join(fam)} は印のかたまりを作れる (家族の仕事 family で「{ACT_COIN}」にできる)")
    if g["mark"] is None and hints.knows(state, p["name"], CARD_COIN):
        out.append("- あなたは、印を押した金属のかたまりの話を知っている。村の印を決めるなら、集まりの mark に書ける")
    elif g["mark"] is None:
        out.append("- 村の印はまだ決まっていない。あなたも、集まりの mark に印の形を書ける")
    if p["name"] in g10.readers(state):
        out.append(f"- あなた ({p['name']}) は字を読み書きできる。村が印のかたまりで貸したり、返されたりした量を、字で書いておける")
    return out


def feel_note(state, p):
    """気持ちだけのお題の行 (代表でない人は仕事を決めないので、代表に伝えられることだけ)"""
    out = []
    if p["name"] in smiths(state):
        out.append(f"- あなたは黒い金属を作れる。家の代表が、あなたの仕事を「{ACT_COIN}」にすれば、あなたは印のかたまりを作れる")
    if _g(state)["mark"] is None and hints.knows(state, p["name"], CARD_COIN):
        out.append("- あなたは、印を押した金属のかたまりの話を知っている。村の印をどうするか、家の代表に伝えられる")
    if fixed(state):  # 直し ③
        out.append("- 村に印のかたまりがあれば、市の日に村の物を運び出さずによその村の物を受けとれ、苦しい村に草の種のかわりに貸せる (市の日をどうするか、家の代表に伝えられる)")
    return ("\n" + "\n".join(out)) if out else ""


def field_rows(state, year=False):
    """答えの欄の説明 (g7._field_rows に足す)"""
    g = _g(state)
    rows = []
    if smiths(state):
        rows.append(f'   印のかたまり: 主な仕事を「{ACT_COIN}」にできるのは、黒い金属を作れる人と、その人と一緒に (with) 作る人')
    if g["mark"] is None:
        rows.append("   村の印: 印のかたまりに打つ村の印を、ことばで書く (mark。例「川と麦の穂」。決めないなら null)")
    rows.append('   払い方: 村の物で申し出を受ける・貸すとき、印のかたまりで払うなら "印"、物で払うなら "物" (pay。決めないなら null)')
    rows.append('   引きかえ: よその村が持って来た印のかたまりを、約束どおり草の種と "引きかえる" か "引きかえない" (redeem。決めないなら null)')
    if fixed(state) and year:  # 直し ①: 年の集まりの村の欄 (掟の道も残す)
        rows.append('   市の日: 市を開く日を、季節の何日目か (1 から 30) で書く (market_day。決めないなら null)。印のかたまり 1 個のねうちを、草の種何つかみか で書く '
                    '(coin_rate。決めないなら null)。どちらも、答えのいちばん多いものに決まる。掟の提案に market_day・rate をつけて決めることもできる')
    elif fixed(state):
        rows.append('   市の日: 市の日とねうちは、年の集まりの答え (market_day・coin_rate) か、掟の提案 (market_day・rate に {"印のかたまり": つかみ}) で決める')
    else:
        rows.append('   市の日: 掟の提案に market_day (季節の何日目か。1 から 30) をつけると、市の日を決める掟になる。印のかたまりのねうちは rate に {"印のかたまり": つかみ}')
    if year:
        rows.append('   市の方針: 市の日に村が出してよい物と 1 年の上限 (give: {"草の種": つかみ, "鎌": 本, "土器": 個, "印": 個})、受ける物 (take: ["ヤギ", ...])、'
                    '印のかたまりで払う・受けるか (pay: true か false) を書く (market。決めないなら null)')
    return rows


def fields_json(state):
    g = _g(state)
    year = (state["era2"]["g7"].get("ask") or "") == "年"
    return ((' "mark": null,' if g["mark"] is None else "") + ' "pay": null, "redeem": null,'
            + (' "market": {"give": {}, "take": [], "pay": null},' if year else "")
            + (' "market_day": null, "coin_rate": null,' if year and fixed(state) else ""))


def bad_words(s):
    return [w for w in WORDS if w in s]
