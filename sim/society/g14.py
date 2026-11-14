"""G14「町と商業」(第 7 部「帝国のあとと町」の終わりの G。2026-11-14 本人の言葉「質問しないであなたのおすすめで進めて下さい」に従い、下書きのおすすめどおり。
docs/society_phase/G14_design.md)

- G14 に入るのは step.py next_part だけ (G13 の 3 つの条件がそろって HOLD wait で止まったところから。g7.close_g13 → g7.enter_next → g7.start_g14)。
  G13 までは、このファイルを読みこみもしない (g7・era2・hints・yardstick は state の g7.g14 があるときだけ、関数の中で読みこむ)。
  だから G1〜G13 は、お題・state・出来事・乱数が前と 1 バイトも変わらない
- 計画の 3 本 (町に住む人・書いた契約・組合) を、この村の形「町と市と仲間」で測る。条件 (3 つとも【村が決めた】。数えるのは G14 に入った次の暦の年 (179年) から。
  3 つそろうと G14 の終わり = 第 7 部の終わり。コードが HOLD part_end で止める):
  c1 町の家: 年の終わりに、家の大人の働いた日の半分以上が食べ物でない仕事だった家 (町の家) に住む人 (子もふくむ) が、地域の人 (村 + 人のいる集落) の 1 割以上の年が 2 年つづく
  c2 書きつけ: 暦の 1 年に、書きつけのとおり草の種を村に払った集落が 3 つ以上の年が 2 回 (つづかなくてよい。G12 の倉の約束は数えない)
  c3 仲間: 年の終わりに、結んでいる仲間 (3 人以上・2 家以上・仲間の人がその仕事を 1 年 90 人日以上) がある年が 2 年つづく
- F: F1 はじめて市へ運んだ / F2 はじめての書きつけ / F3 はじめての仲間 / F4 はじめての町の家
- 足す仕組み (乱数なし): 仕事「市へ運ぶ」(1 人ずつ。村の倉の土器と鎌を、ほしがっている集落に運んで草の種を受ける)・欄 note (書きつけ。読み書きできる人が書く)・
  欄 guild (仲間。ちがう家の答える人 2 人以上で結ぶ)・札 H13-03 (病の話。入る日に札の表に足す。何も開かない)・町と市と仲間の帳簿
- 決め方: 仕事は今のまま 1 人ずつ。note は集落ごとに答えた人のいちばん多い中身 (G12 の pact と同じ)。guild はちがう家の答える人 2 人以上。相手の答えは決まりの手
- G10〜G13 の仕組みと直しは動きつづける。G13 の条件は「ならべて測る」
- 暦の年: 帳簿は日 ÷ 120 (g12・g13 と同じ)。道の見張りの行だけ (日 + 1) ÷ 120
- 村の人に見せる文には WORDS を書かない (試しで確かめる)。呼び名は「町の家」「市へ運ぶ」「書きつけ」「仲間」
"""
import json

import era2
import g10
import g12
import g13
import hints
from world import log

YEAR, SEASON_DAYS = era2.YEAR, era2.SEASON_DAYS
ACT_MARKET = "市へ運ぶ"  # 新しい仕事 (world.ACTS7 に足した。G14 で、大人ならだれでも)
CARD_GUILD, CARD_BILL, CARD_PLAGUE = "H13-02", "H13-01", "H13-03"  # 札「職人の誓い」・「紙を渡すと別の町で払われる」・「遠くの病と足りない手」(入る日に足す)
GRAIN, POT, SICKLE = "草の種", "土器", "鎌"
GOODS = (POT, SICKLE)  # 市へ運ぶ・書きつけで渡す物 (村の倉の土器と鎌。黒い金属の鎌は道具として使っているので運ばない)
# 食べ物でない仕事 (問い 4 のおすすめ。記録をつける (G6 の帳) と交換に行く (G6 の商い) も、帳・市へ運ぶと同じ側に数える)。ほかの仕事は食べ物の側 (水の道を掘るも)
NONFOOD = ("土器づくり", "道具づくり", "黒い金属を作る", "印のかたまりを作る", "住まいを建てる", "水の輪を建てる", "帳をつける", "記録をつける", "試す", "字を習う",
           ACT_MARKET, "交換に行く")
REST = ("休む", "休む (けが)")  # 働いた日に数えない
GUILD_JOBS = ("土器づくり", "道具づくり", "黒い金属を作る", ACT_MARKET)  # 仲間を結べる仕事
GOOD_OF_JOB = {"土器づくり": POT, "道具づくり": SICKLE}  # 仲間のねうちが効く品
TOWN_HALF = 0.5  # 町の家: 家の大人の働いた日の半分以上が食べ物でない仕事【仮定】
C1_SHARE, C1_YEARS = 0.1, 2  # c1: 町の家に住む人が地域の人の 1 割以上の年が 2 年つづく【仮定】
C2_PLACES, C2_TIMES = 3, 2  # c2: 書きつけのとおり払った集落が 3 つ以上の年が 2 回【仮定】
C3_PEOPLE, C3_HOUSES, C3_DAYS, C3_YEARS = 3, 2, 90, 2  # c3: 3 人以上・2 家以上・1 年 90 人日以上の仲間がある年が 2 年つづく【仮定】
GUILD_MIN_DAYS = 20  # 仲間に入れる人: 前の 1 年にその仕事を 20 日以上した大人【仮定】
RATE_MIN, RATE_MAX = 0.8, 1.25  # 仲間のねうち・書きつけの受ける幅【仮定】
APPRENTICE = 1.5  # 弟子: 仲間の人と同じ日に with に名前を書いて同じ仕事をすると、腕の上がる量が 1.5 倍【仮定】
GUILD_REST_END = 2  # 仲間: 2 年つづけて休むと終わる
GUILD_SOLO = True  # 前に決めておいた直し (下書き 7.1・問い 9。決まりの村の B1S0 で仲間が 1 度も結ばれなかったので入れた。G14_check.md 2.): 1 人 (1 家) の答えでも、2 家以上の仕事の人を名前で書けば結ぶ
MARKET_SHARE, MARKET_TRUST = 0.2, 0.3  # 市へ運ぶ: 集落が 1 年に払えるのは、その集落の草の種の 2 割まで・信頼 0.3 より低い集落には渡せない【仮定】
NOTE_TRUST, NOTE_GRAIN_SHARE, NOTE_MAX = 0.5, 0.3, 2000  # 書きつけ: 信頼 0.5 以上・take は相手の草の種の 3 割まで・1 つの give は 2,000 つかみ分まで【仮定】
NOTE_LATE = 1  # 苦しい年は 1 年おくれる。もう 1 年払えなければ破れる
PATH_YEARS = 2  # 道の見張り: 選べる答える人が 2 年つづけて 0 人なら止めて相談
IDLE_YEARS = 3  # 選べた人はいるのに、だれも選ばなかった年がつづいたら報告 (止めない)
FAIL_REPORT = 3  # 1 年に「選んだのにできなかった」がこれだけあれば、報告に書く
LATER_YEARS = 5  # 5 年ごとの相談 (G14 に入った日から)
WORDS = ("商業", "組合", "ギルド", "手形", "為替", "自治", "市場", "お金", "領主", "国", "税", "帝国", "都") + g12.WORDS + g13.WORDS  # 村の人に見せる G14 の文に書かない言葉
FS = {"F1": "はじめて市へ運んだ", "F2": "はじめての書きつけ", "F3": "はじめての仲間", "F4": "はじめての町の家"}
CS = {"c1": "町の家", "c2": "書きつけ", "c3": "仲間"}
BLOCK_HEAD = "町と市と仲間・続けること: この集まりで、あなたができること (どれも、しなくてもよい。書かなければ今のまま)"
NONFOOD_WORDS = "土器・道具・黒い金属・住まい・水の輪・帳・市へ運ぶ"
# 2026-11-14 G14 のお題の直し (G14_design.md 12。G12_design.md 12. と同じ形): 179年・180年の年の集まり (21479・21599 日目) で、答える人 22〜23 人のだれも
# 市へ運ぶ・note・guild を選ばなかった。答えの形 (JSON) に note と guild の欄がなく (pact・help はある)、仲間の例の名前が「…」で、だれを書けば結ぶか分からず、
# 市へ運ぶの例と、運ぶと何が村に入るかが短い節になかった。G14_PROMPT_FROM (180年120日目 = 181年の年の集まり) から、お題だけを直す (決まり・数・決め方は変えない)。
# その日 (お題は前のコードで出ていた) は、step.py refresh_prompts が g7.g14.prompt_fix を書いたあとだけ。だから、その日までの歩をやり直しても 1 バイトも同じ
G14_PROMPT_FROM = 21719


def on(state):
    return "g14" in ((state.get("era2") or {}).get("g7") or {})


def _g(state):
    return state["era2"]["g7"]["g14"]


def prompt_fixed(state):
    """G14 のお題の直し (G14_PROMPT_FROM) が効くか: その日より後はいつも。その日は refresh_prompts の印 (g7.g14.prompt_fix) のあとだけ"""
    return on(state) and (state["day"] > G14_PROMPT_FROM or (state["day"] == G14_PROMPT_FROM and "prompt_fix" in _g(state)))


def mark_prompt_fix(state, why):
    """refresh_prompts から: G14_PROMPT_FROM の日に、お題の直しを今の歩から入れたことを g7.g14.prompt_fix に残す (その日より前なら何もしない)"""
    if on(state) and state["day"] >= G14_PROMPT_FROM and "prompt_fix" not in _g(state):
        _g(state)["prompt_fix"] = {"day": state["day"], "why": why}


def _y(state):
    return state["day"] // YEAR


def _others(state):
    import g7
    return g7._others(state)


def _other(state, oid):
    return next((o for o in _others(state) if o["id"] == oid), None)


def _js(x):
    return json.dumps(x, ensure_ascii=False)


def _gw(goods):
    return "・".join(f"{k} {n}" + ("本" if k == SICKLE else "個" if k == POT else " つかみ" if k == GRAIN else "") for k, n in goods.items() if n)


def bad_words(s):
    return [w for w in WORDS if w in s]


# ---------------- G14 に入る (g7.start_g14 から) ----------------

def start(state):
    """G14 の state を作る: G13 の物差し (条件・F・道の見張り・帳簿の要点) を g7.before.G13.g13 に写し、条件と道の見張りは数え直す
    (F は村に起きたことなので消さない。G13 のときと同じ)。病の札 H13-03 を札の表に足す (hints.cards_sha が hint_cards_g14.json もつなぐ)"""
    g7s, D = state["era2"]["g7"], state["day"]
    t = g7s["g13"]
    g7s.setdefault("before", {}).setdefault("G13", {})["g13"] = {
        "reached": dict(t["reached"]), "c": dict(t["c"]), "c2_years": list(t["c2_years"]), "c3_years": list(t["c3_years"]),
        "path": {k: dict(v) for k, v in t["path"].items()}, "mills": len(t["mill"]["mills"]), "canal_cap": t["canal"]["cap"]}
    t["c"], t["path"] = {}, {}
    g = g7s["g14"] = {"start": D, "town": {}, "c1_years": [],
                      "market": {"trips": {}, "dest": {}, "year": {}, "paid": {}, "next": 1, "log": []},
                      "notes": {"list": [], "next": 1, "year": {}}, "c2_years": [],
                      "guilds": {"list": [], "next": 1, "offers": []}, "c3_years": [], "guild_year": {},
                      "reached": {}, "c": {}, "fails": [], "path": {}, "ledger": []}
    h = g7s.get("hints") or {}
    if h:
        sha = hints.cards_sha(state)
        h["cards_sha"] = sha
        h.setdefault("cards_log", []).append({"day": D, "sha": sha, "note": f"G14 に入った日: 遠くの病の札 1 枚 ({CARD_PLAGUE})"})
        log(state, "区切り", None, "よその便りの札の表に 1 枚を足した (G14 に入った日)", cards=sha)
    log(state, "町と市", None, "G14 から、主な仕事を「市へ運ぶ」にすると、村の倉の土器と鎌を、ほしがっている村に運んで草の種を受けられる。"
        "字を書ける人は「書きつけ」を書け、同じ仕事の人は「仲間」を結べる", g14=True)
    return g


# ---------------- 町の家 (年の終わり。数えるだけ) ----------------

def house_days(state):
    """前の 1 年 (g7.past) の、家ごとの大人の働いた日 {家: [食べ物でない日, 働いた日]}。休んだ日は数えない。家は今の家"""
    ads = {p["name"]: p for p in era2.adults(state)}
    out = {}
    for s in state["era2"]["g7"].get("past", []):
        for n, acts in s["days"].items():
            p = ads.get(n)
            h = p.get("household") if p else None
            if not h:
                continue
            row = out.setdefault(h, [0, 0])
            for a, d in acts.items():
                if a in REST:
                    continue
                row[1] += d
                if a in NONFOOD:
                    row[0] += d
    return out


def house_people(state):
    out = {}
    for p in state["people"]:
        if p["alive"] and p.get("household"):
            out[p["household"]] = out.get(p["household"], 0) + 1
    return out


def region_people(state):
    """地域の人 (村 + 人のいる集落)"""
    return len([p for p in state["people"] if p["alive"]]) + sum(o.get("people", 0) for o in g13.settlements(state))


def town_now(state):
    """いま (前の 1 年) の町の家: (町の家の並び, 町の家に住む人, 地域の人, 家ごとの [食べ物でない日, 働いた日])"""
    hd, hp = house_days(state), house_people(state)
    town = sorted(h for h, (nf, w) in hd.items() if w > 0 and nf >= TOWN_HALF * w and hp.get(h))
    return town, sum(hp.get(h, 0) for h in town), region_people(state), hd


def to_town(nf, w):
    """町の家になるのに、あと何人日を食べ物でない仕事にすればよいか (働いた日はそのまま)"""
    return max(0, -(-(int(TOWN_HALF * 2 * w) - 2 * nf) // 2)) if w else 0


def _answer_houses(state):
    return {p.get("household") for p in era2.adults(state) if p["name"] in set(era2.answerers(state)) and p.get("household")}


def _town_year(state):
    """年の終わり: 町の家を数え、c1・F4 を見る。答えた家と、写って動いた家 (見本でない家) を分けて残す"""
    g, D = _g(state), state["day"]
    y = D // YEAR
    town, ppl, reg, hd = town_now(state)
    ans = _answer_houses(state)
    share = ppl / reg if reg else 0.0
    g["town"][str(y)] = {"houses": len(town), "people": ppl, "region": reg, "share": round(share, 4),
                         "answered": [h for h in town if h in ans], "copied": [h for h in town if h not in ans],
                         "top": sorted(([h, round(nf / w, 3)] for h, (nf, w) in hd.items() if w), key=lambda x: (-x[1], x[0]))[:6],
                         "nonfood": sum(v[0] for v in hd.values()), "worked": sum(v[1] for v in hd.values())}
    if y <= g["start"] // YEAR:
        return
    if town:
        _reach(state, "F4", D, f"{'・'.join(town[:4])} の大人が、{y}年に働いた日の半分以上を、食べ物でない仕事にした")
    if reg and share >= C1_SHARE and y not in g["c1_years"]:
        g["c1_years"].append(y)
        log(state, "目盛り", None, f"目盛り: G14 の条件 1 の年 ({y}年。町の家 {len(town)} に {ppl} 人。地域の {round(share * 100, 1)}%)", g="G14", c1_year=y)
    if all((y - i) in g["c1_years"] for i in range(C1_YEARS)):
        _cond(state, "c1", D, f"町の家に住む人が地域の人の 1 割以上の年が {C1_YEARS} 年つづいた ({'・'.join(str(y - i) for i in reversed(range(C1_YEARS)))}年)")


# ---------------- 市へ運ぶ (仕事。g7.role_day から) ----------------

def known(o):
    return g12.known(o)


def wants(state, o, going=False):
    """その集落が、この季節にまだほしがっている土器と鎌 (era2._g6_wants。交換・申し出・市へ運ぶ・書きつけで渡した分は引いてある)。
    going なら、ほかの村の人がいまその集落へ運んでいる途中の分も引く (出かける日に、村の人は、だれがどこへ運んでいるかを知っている)"""
    w = era2._g6_wants(state, o)
    out = {k: w.get(k, 0) for k in GOODS}
    if going:
        for tr in _g(state)["market"]["trips"].values():
            if tr["state"] == "行く" and not tr["arrived"] and tr["to"] == o["id"]:
                for k, n in tr["took"].items():
                    out[k] = max(0, out.get(k, 0) - n)
    return out


def _pay_left(state, o, going=False):
    """この暦の年に、その集落が市へ運んだ品に、まだ払える草の種 (その集落の草の種の 2 割まで)。going なら、運んでいる途中の分のねうちも引く"""
    g = _g(state)
    paid = (g["market"]["paid"].get(str(_y(state))) or {}).get(o["id"], 0)
    left = max(0, int(MARKET_SHARE * (o.get("grain", 0) + paid)) - paid)
    if going:
        for tr in g["market"]["trips"].values():
            if tr["state"] == "行く" and not tr["arrived"] and tr["to"] == o["id"]:
                left -= value(state, tr["took"], tr["who"])
    return max(0, left)


def market_why(state, o, going=True):
    """その集落へ市へ運べないわけ (運べるなら None)。going: ほかの村の人が運んでいる途中の分も数える (出かける日)"""
    if not known(o):
        return "もうない村か、まだよく知らない村なので"
    if o.get("trust", 0.5) < MARKET_TRUST:
        return f"{o['name']} は村をまだ信じきれていないので"
    if not any(wants(state, o, going).values()):
        return f"{o['name']} は、この季節の分の土器と鎌をもう受けたか、ほかの村の人が運んでいるので"
    if _pay_left(state, o, going) < min(era2.VALUE[POT], era2.VALUE[SICKLE]):
        return f"{o['name']} は、この年に払える草の種をもう払ったので"
    if going and not _carry(state, o, None):
        w = [k for k, n in wants(state, o, True).items() if n > 0]
        if not any(era2._g6_have(state, "村", k) for k in w):
            return f"村の倉に、{o['name']} がほしがっている{'・'.join(w)}がないので"
        return f"{o['name']} がこの年にまだ払える草の種では、ほしがっている{'・'.join(w)} 1 つ分に足りないので"
    return None


def market_places(state):
    """いま市へ運べる集落 (近い順・番号の順)"""
    return sorted((o for o in _others(state) if market_why(state, o) is None), key=lambda o: (o["days"], int(o["id"][1:])))


def guild_rate(state, good, who=None):
    """その品のねうちの倍 (その品の仕事の仲間があれば、そのねうち。なければ、運ぶ人が「市へ運ぶ」の仲間の人なら、そのねうち。どちらもなければ 1)"""
    for gd in active_guilds(state):
        if GOOD_OF_JOB.get(gd["job"]) == good:
            return gd["rate"]
    if who:
        for gd in active_guilds(state):
            if gd["job"] == ACT_MARKET and who in gd["people"]:
                return gd["rate"]
    return 1.0


def value(state, goods, who=None):
    return int(sum(era2.VALUE[k] * n * guild_rate(state, k, who) for k, n in goods.items()))


def set_dest(state, name, j):
    """季節のはじめ (g7.job): 「市へ運ぶ」の行き先 (to か place に書いた集落)。書いていなければ None (出かける日に、いちばん近いほしがっている村へ)"""
    oid = g12._oid(state, (j or {}).get("to")) or g12._oid(state, (j or {}).get("place"))
    _g(state)["market"]["dest"][name] = oid


def _carry(state, o, who):
    """持って行く土器と鎌 (1 人が運べる量・相手のほしい量・村の倉・相手が払える草の種まで)"""
    w = wants(state, o, True)
    left = _pay_left(state, o, True)
    have = {k: era2._g6_have(state, "村", k) for k in GOODS}
    pots = min(w[POT], era2.LOAD[POT], have[POT], int(left // (era2.VALUE[POT] * guild_rate(state, POT, who))))
    room = 1 - pots / era2.LOAD[POT]
    left -= pots * era2.VALUE[POT] * guild_rate(state, POT, who)
    sick = min(w[SICKLE], int(room * era2.LOAD[SICKLE] + 1e-9), have[SICKLE], int(max(0, left) // (era2.VALUE[SICKLE] * guild_rate(state, SICKLE, who))))
    return {k: n for k, n in ((POT, pots), (SICKLE, sick)) if n > 0}


def _fail_once(state, name, what, why):
    g, D = _g(state), state["day"]
    if not any(f["who"] == name and f["what"] == what and f["day"] // SEASON_DAYS == D // SEASON_DAYS for f in g["fails"]):
        _fail(state, name, what, why, log_it=False)


def _depart(state, p, t):
    g, D = _g(state), state["day"]
    name = p["name"]
    m = g["market"]
    want = _other(state, m["dest"].get(name)) if m["dest"].get(name) else None
    why0 = market_why(state, want) if want else None
    o = want if want and why0 is None else None
    note = ""
    if o is None:
        alt = market_places(state)
        if not alt:
            why = (f"{name} は、{why0}、市へ運べず、休んだ (いま土器と鎌をほしがっていて、払える村がない)" if want else
                   f"{name} は、いま土器と鎌をほしがっていて払える村がないので、市へ運べず、休んだ")
            t.setdefault("events", []).append(log(state, "休む", name, why, rest_why=ACT_MARKET))
            _fail_once(state, name, ACT_MARKET, why)
            return None
        o = alt[0]
        note = (f" ({why0}、行き先を {o['name']} にした)" if want else f" (行き先が書かれていなかったので、いちばん近いほしがっている {o['name']} へ)")
    carry = _carry(state, o, name)
    if not carry:
        why = f"{name} は、{o['name']} がほしがっている品を、払える草の種の分だけ運ぶことができず (仲間のねうちのため)、市へ運べず、休んだ"
        t.setdefault("events", []).append(log(state, "休む", name, why, rest_why=ACT_MARKET))
        _fail_once(state, name, ACT_MARKET, why)
        return None
    took = era2._g6_take(state, "村", carry)
    tr = m["trips"][name] = {"id": f"M{m['next']}", "who": name, "house": p.get("household"), "to": o["id"], "start": D, "days": o["days"],
                             "took": took, "got": 0, "back": {}, "gave": {}, "arrived": False, "state": "行く"}
    m["next"] += 1
    t.setdefault("events", []).append(log(state, ACT_MARKET, name, f"{name} が、村の倉の {_gw(took)} を持って、{o['name']} へ市に運びに出た{note}",
                                          other=o["id"], trip=tr["id"], moves=[era2._mv("村", -1, took)]))
    return tr


def _arrive(state, p, t, tr):
    g, D = _g(state), state["day"]
    name = p["name"]
    o = _other(state, tr["to"])
    tr["arrived"] = True
    why = market_why(state, o, False) if o else "もうない村なので"
    give = {}
    if why is None:
        w, left = wants(state, o), _pay_left(state, o)
        for k in GOODS:
            r = era2.VALUE[k] * guild_rate(state, k, name)
            n = min(tr["took"].get(k, 0), w[k], int(left // r))
            if n > 0:
                give[k] = n
                left -= n * r
    if not give:
        why = why or f"{o['name']} は、この季節の分をもう受けていたので"
        tr["back"] = dict(tr["took"])
        txt = f"{name} は {o['name'] if o else tr['to']} に {_gw(tr['took'])} を運んだが、{why}、渡せずに持ち帰る"
        t.setdefault("events", []).append(log(state, ACT_MARKET, name, txt, other=tr["to"], trip=tr["id"]))
        _fail(state, name, ACT_MARKET, txt, log_it=False)
        return
    pay = min(value(state, give, name), int(o.get("grain", 0)))
    era2._node_add(o, give, 1)
    o["grain"] = max(0, o["grain"] - pay)
    tk = era2._g6(state)["taken"].setdefault(o["id"], {})
    for k, n in give.items():
        tk[k] = tk.get(k, 0) + n
    y = str(_y(state))
    pd = g["market"]["paid"].setdefault(y, {})
    pd[o["id"]] = pd.get(o["id"], 0) + pay
    tr["gave"], tr["got"] = give, pay
    tr["back"] = {k: n - give.get(k, 0) for k, n in tr["took"].items() if n - give.get(k, 0) > 0}
    row = _market_row(state)
    row["trips"] += 1
    row["grain"] += pay
    for k, n in give.items():
        row[k] = row.get(k, 0) + n
    to = row["to"].setdefault(o["id"], {"trips": 0, "grain": 0})
    to["trips"] += 1
    to["grain"] += pay
    for k, n in give.items():
        to[k] = to.get(k, 0) + n
    row["by"][name] = row["by"].get(name, 0) + 1
    if tr.get("house"):
        row["houses"][tr["house"]] = row["houses"].get(tr["house"], 0) + pay
    t.setdefault("events", []).append(log(state, ACT_MARKET, name, f"{name} は {o['name']} で、{_gw(give)} を渡し、草の種 {pay} つかみを受けた"
                                          + (f" (受けてもらえなかった {_gw(tr['back'])} は持ち帰る)" if tr["back"] else ""), other=o["id"], trip=tr["id"]))
    _reach(state, "F1", D, f"{name} が {o['name']} に {_gw(give)} を運び、草の種 {pay} つかみを受けた")


def _market_row(state):
    return _g(state)["market"]["year"].setdefault(str(_y(state)), {"trips": 0, "days": 0, "grain": 0, "to": {}, "by": {}, "houses": {}})


def _home(state, p, t, tr, why=None):
    """帰る: 受けた草の種と、持ち帰った品を村の倉へ"""
    got = {GRAIN: tr["got"]} if tr["got"] else {}
    if got:
        era2._g6_put(state, "村", got)
    if tr["back"]:
        era2._g6_put(state, "村", tr["back"])
    if not tr["arrived"]:
        era2._g6_put(state, "村", tr["took"])
    tr["state"] = "帰った"
    tr["end"] = state["day"]
    m = _g(state)["market"]
    m["log"] = (m["log"] + [{k: tr[k] for k in ("id", "who", "house", "to", "start", "end", "gave", "got")}])[-60:]
    o = _other(state, tr["to"])
    back = got if tr["arrived"] else {}
    txt = (f"{tr['who']} が {o['name'] if o else tr['to']} から帰った ("
           + ("草の種 " + str(tr["got"]) + " つかみを村の倉に入れた" if tr["got"] else "何も受けずに")
           + (f"。持ち帰った {_gw(tr['back'] if tr['arrived'] else tr['took'])}" if (tr["back"] if tr["arrived"] else tr["took"]) else "") + ")" + (why or ""))
    ev = log(state, ACT_MARKET, tr["who"], txt, other=tr["to"], trip=tr["id"],
             moves=[era2._mv("村", 1, dict(back, **(tr["back"] if tr["arrived"] else tr["took"])))])
    if t is not None:
        t.setdefault("events", []).append(ev)


def market_day(state, p, t):
    """1 日の「市へ運ぶ」: 出かける (行き先・持って行く物) → 歩く → 向こうで渡して草の種を受ける → 歩く → 帰る (行って帰る日数は、歩く日 × 2 + 1)。乱数なし"""
    g, D = _g(state), state["day"]
    tr = g["market"]["trips"].get(p["name"])
    if tr is None or tr["state"] != "行く":
        tr = _depart(state, p, t)
        if tr is None:
            return
    t["away"] = True
    _market_row(state)["days"] += 1
    k = D - tr["start"]
    if k >= tr["days"] and not tr["arrived"]:
        _arrive(state, p, t, tr)
    elif k >= 2 * tr["days"] and tr["arrived"]:
        _home(state, p, t, tr)


def _trips_end(state):
    """季節の終わり: 出かけている人は帰る (季節をまたいで出かけない)"""
    m = _g(state)["market"]
    for name in sorted(m["trips"]):
        tr = m["trips"][name]
        if tr["state"] == "行く":
            _home(state, None, None, tr, "。季節が変わるので帰った")
    m["trips"] = {}


# ---------------- 書きつけ (欄 note。集まりの答えから) ----------------

def _house_of(state, name):
    p = next((q for q in era2.adults(state) if q["name"] == name), None)
    return p.get("household") if p else None


def house_readers(state, name):
    return g12._house_readers(state, name)


def _goods(v, allowed):
    out = {}
    for k, n in (v.items() if isinstance(v, dict) else []):
        k = POT if "土器" in str(k) else SICKLE if "鎌" in str(k) else GRAIN if ("草" in str(k) or "種" in str(k)) else None
        n = era2._num(n)
        if k in allowed and n and n >= 1:
            out[k] = min(int(n), 100000)
    return out


def note_why(state, o, give, take, rate=1.0):
    """相手が書きつけを受けないわけ (受けるなら None)。受ける決まり 1〜5 と上限"""
    g = _g(state)
    if not known(o):
        return "もうない村か、まだよく知らない村なので"
    if not give or GRAIN not in take:
        return "渡す品 (土器か鎌) と、あとで払ってもらう草の種が書かれていなかったので"
    w = wants(state, o)
    over = [k for k, n in give.items() if n > w.get(k, 0)]
    if over:
        return f"{o['name']} は、いま {'・'.join(over)} をそれほどほしがっていないので (ほしいのは {_gw(w) or 'なし'})"
    if o.get("trust", 0.5) < NOTE_TRUST:
        return f"{o['name']} は村をまだ信じきれていないので"
    v = sum(era2.VALUE[k] * n for k, n in give.items()) * rate
    if v > NOTE_MAX:
        return f"1 つの書きつけで渡せるのは 草の種 {NOTE_MAX} つかみ分までなので"
    if not RATE_MIN * v <= take[GRAIN] <= RATE_MAX * v:
        return f"草の種 {take[GRAIN]} つかみは、品のねうち (約 {int(v)} つかみ) に合わないので ({int(RATE_MIN * v)}〜{int(RATE_MAX * v)} つかみなら受ける)"
    if take[GRAIN] > NOTE_GRAIN_SHARE * o.get("grain", 0):
        return f"{o['name']} の草の種 ({o.get('grain', 0)} つかみ) の 3 割より多くは払えないので"
    if any(n["to"] == o["id"] and n["status"] in ("待つ", "おくれ") for n in g["notes"]["list"]):
        return f"{o['name']} とは、まだ払っていない書きつけがあるので"
    if any(era2._g6_have(state, "村", k) < n for k, n in give.items()):
        return "村の倉に、書いた土器か鎌が足りないので"
    return None


def _note_votes(state, real):
    """答えた人ごとの書きつけ {集落: (中身の文, 書いた人)}。書くのは読み書きできる人 (答える人か、その家の人)。字を書ける人がいない家は、わけを残す"""
    out, nowrite = {}, []
    for n, a in real.items():
        if not isinstance(a, dict):
            continue
        rows = g12._rows(a.get("note"))[:12]
        if not rows:
            continue
        rd = house_readers(state, n)
        for r in rows:
            oid = g12._oid(state, r.get("to"))
            if not oid:
                continue
            give, take = _goods(r.get("give"), GOODS), _goods(r.get("take"), (GRAIN,))
            if not (give or take):
                continue
            by = str(r.get("by") or "").strip()
            if not rd:
                nowrite.append((n, oid))
                continue
            by = by if by in rd else (n if n in rd else rd[0])
            out.setdefault(oid, {})[n] = (json.dumps({"give": give, "take": take}, ensure_ascii=False, sort_keys=True), by)
    return out, nowrite


def apply_notes(state, real):
    """集まりの答えの note: 集落ごとに、答えた人の中でいちばん多い中身 (g7._tally。1 人でも決まる) → 相手の答え (決まりの手) → 受ければ、いま品を渡す"""
    import g7
    g, D = _g(state), state["day"]
    votes, nowrite = _note_votes(state, real)
    for n, oid in nowrite:
        o = _other(state, oid)
        why = f"{n} の家には字を書ける人がいないので、{o['name'] if o else oid} への書きつけにできなかった"
        _fail(state, n, "書きつけ", why)
    w = g7._vote_weights(state, real)
    for oid in sorted(votes, key=lambda x: int(x[1:])):
        vs = {n: v[0] for n, v in votes[oid].items()}
        ch, txt = g7._tally(state, vs, w)
        if not ch:
            continue
        who = sorted(n for n, v in vs.items() if v == ch)
        by = votes[oid][who[0]][1]
        terms = json.loads(ch)
        o = _other(state, oid)
        give, take = terms["give"], terms["take"]
        rate = value(state, give, by) / max(1, sum(era2.VALUE[k] * n for k, n in give.items())) if give else 1.0
        why = note_why(state, o, give, take, rate) if o else "もうない村なので"
        row = _note_year(state)
        row["written"] += 1
        if why:
            row["refused"] += 1
            _fail(state, by, "書きつけ", f"{o['name'] if o else oid} は、{by} の書いた書きつけ ({_gw(give)} を渡し、草の種 {take.get(GRAIN, 0)} つかみを"
                  f"あとで払う) を受けなかった ({why}。答えた人 {'・'.join(who)})")
            continue
        got = era2._g6_take(state, "村", give)
        era2._node_add(o, got, 1)
        tk = era2._g6(state)["taken"].setdefault(oid, {})
        for k, n in got.items():
            tk[k] = tk.get(k, 0) + n
        x = {"id": f"W{g['notes']['next']}", "to": oid, "give": got, "take": take, "by": by, "who": who, "day": D, "due": D // YEAR,
             "status": "待つ", "late": 0, "paid": None}
        g["notes"]["next"] += 1
        g["notes"]["list"].append(x)
        g["notes"]["list"] = g["notes"]["list"][-80:]
        row["accepted"] += 1
        row["by"][by] = row["by"].get(by, 0) + 1
        log(state, "書きつけ", by, f"{by} が、{o['name']} との書きつけを字で書いた [{x['id']}]: いま村の倉の {_gw(got)} を渡し、{o['name']} は次の年の終わりまでに"
            f"草の種 {take[GRAIN]} つかみを村に払う (答えた人 {'・'.join(who)}。{g7_vote(txt)})", other=oid, note=x["id"], moves=[era2._mv("村", -1, got)])
        _reach(state, "F2", D, f"{o['name']} が、{by} の書いた書きつけを受けた")


def g7_vote(txt):
    return f"票 {txt}" if txt else ""


def _note_year(state):
    return _g(state)["notes"]["year"].setdefault(str(_y(state)), {"written": 0, "accepted": 0, "refused": 0, "paid": [], "late": [], "broken": [], "by": {},
                                                                    "grain": 0})


def _settle_notes(state):
    """年の終わり: 払う日の来た書きつけを払う。苦しい年 (g12.struggling) か草の種が足りなければ 1 年おくれ、もう 1 年払えなければ破れる (信頼が少し下がる)"""
    g, D = _g(state), state["day"]
    y = D // YEAR
    row = _note_year(state)
    for x in g["notes"]["list"]:
        if x["status"] not in ("待つ", "おくれ") or x["due"] > y:
            continue
        o = _other(state, x["to"])
        n = x["take"][GRAIN]
        if o and known(o) and not g12.struggling(o) and o.get("grain", 0) >= n:
            o["grain"] -= n
            era2._g6_put(state, "村", {GRAIN: n})
            x["status"], x["paid"] = "払った", D
            o["trust"] = min(1.0, round(o["trust"] + g12.TRUST_KEEP, 2))
            row["paid"].append(x["to"])
            row["grain"] += n
            log(state, "書きつけ", None, f"{o['name']} が、書きつけ [{x['id']}] のとおり、草の種 {n} つかみを村に払った", other=x["to"], note=x["id"],
                moves=[era2._mv("村", 1, {GRAIN: n})])
            continue
        why = ("もうない村なので" if not (o and known(o)) else f"{o['name']} は苦しい年なので" if g12.struggling(o) else f"{o['name']} の草の種が足りないので")
        if x["status"] == "待つ" and o and known(o):
            x["status"], x["due"], x["late"] = "おくれ", y + NOTE_LATE, x["late"] + 1
            row["late"].append(x["to"])
            _fail(state, None, "書きつけ", f"書きつけ [{x['id']}] は、{why}、払いが 1 年おくれた (次の年の終わりに払えなければ、書きつけは破れる)")
            continue
        x["status"] = "破れた"
        row["broken"].append(x["to"])
        if o:
            o["trust"] = max(0.0, round(o["trust"] - g12.TRUST_MISS, 2))
        _fail(state, None, "書きつけ", f"書きつけ [{x['id']}] は、{why}、払われずに破れた" + (f" ({o['name']} は村を前ほど信じなくなった)" if o else ""))
    places = sorted(set(row["paid"]), key=lambda k: int(k[1:]))
    if y > g["start"] // YEAR and len(places) >= C2_PLACES and y not in g["c2_years"]:
        g["c2_years"].append(y)
        log(state, "目盛り", None, f"目盛り: G14 の条件 2 の年 ({y}年。書きつけのとおり村に払った集落 {len(places)}: {'・'.join(places)})", g="G14", c2_year=y)
        if len(g["c2_years"]) >= C2_TIMES:
            _cond(state, "c2", D, f"書きつけのとおり村に払った集落が {C2_PLACES} つ以上の年が {len(g['c2_years'])} 回 ({'・'.join(map(str, g['c2_years']))}年)")


# ---------------- 仲間 (欄 guild。集まりの答えから) ----------------

def job_days(state):
    """前の 1 年 (g7.past) の、生きている大人の仕事ごとの日数 {名前: {仕事: 日}}"""
    ads = {p["name"] for p in era2.adults(state)}
    out = {}
    for s in state["era2"]["g7"].get("past", []):
        for n, acts in s["days"].items():
            if n in ads:
                for a, d in acts.items():
                    if a in GUILD_JOBS:
                        out.setdefault(n, {})[a] = out.setdefault(n, {}).get(a, 0) + d
    return out


def eligible(state, job, jd=None):
    """その仕事の仲間に入れる人 (前の 1 年にその仕事を 20 日以上した、生きている大人。名前の順)"""
    jd = job_days(state) if jd is None else jd
    return sorted(n for n, r in jd.items() if r.get(job, 0) >= GUILD_MIN_DAYS)


def _houses(state, names):
    hs = {p["name"]: p.get("household") for p in era2.adults(state)}
    return sorted({hs[n] for n in names if hs.get(n)})


def open_jobs(state):
    """仲間を結べる仕事 (仲間に入れる人が 3 人以上・2 家以上): {仕事: 人}"""
    jd = job_days(state)
    out = {}
    for j in GUILD_JOBS:
        e = eligible(state, j, jd)
        if len(e) >= C3_PEOPLE and len(_houses(state, e)) >= C3_HOUSES:
            out[j] = e
    return out


def active_guilds(state):
    return [x for x in _g(state)["guilds"]["list"] if x["status"] != "終わった"]


def _job_of(v):
    s = str(v or "")
    if "土器" in s:
        return "土器づくり"
    if "鎌" in s or "道具" in s:
        return "道具づくり"
    if "黒い金属" in s:
        return "黒い金属を作る"
    if "市" in s or "運ぶ" in s:
        return ACT_MARKET
    return None


def _guild_votes(state, real):
    """答えた人ごとの仲間の答え {仕事: {名前: (ねうち, 弟子, 書いた人の並び)}}"""
    out = {}
    for n, a in real.items():
        if not isinstance(a, dict):
            continue
        rows = a.get("guild")
        rows = [rows] if isinstance(rows, dict) else rows if isinstance(rows, list) else []
        for r in rows[:4]:
            if not isinstance(r, dict):
                continue
            job = _job_of(r.get("仕事") or r.get("job"))
            if not job:
                continue
            rate = era2._num(r.get("ねうち") if r.get("ねうち") is not None else r.get("rate"))
            rate = round(min(RATE_MAX, max(RATE_MIN, rate)), 2) if rate else 1.0
            ap = r.get("弟子") if "弟子" in r else r.get("apprentice")
            ppl = r.get("人") or r.get("people") or []
            ppl = [str(x).strip() for x in (ppl if isinstance(ppl, list) else [ppl])][:30]
            out.setdefault(job, {})[n] = (rate, bool(era2._yes(ap)) if ap is not None else False, ppl)
    return out


def apply_guilds(state, real):
    """集まりの答えの guild: 同じ集まりで、ちがう家の答える人 2 人以上が同じ仕事の仲間を書けば結ぶ (人は書かれた人のうち入れる人を合わせる)。
    1 家だけなら「仲間の申し出」として残し、次の集まりでほかの家の答える人が同じ仕事を書けば結ぶ。ねうちと弟子は書いた人の中でいちばん多い中身"""
    import g7
    g, D = _g(state), state["day"]
    gs = g["guilds"]
    votes = _guild_votes(state, real)
    w = g7._vote_weights(state, real)
    jd = job_days(state)
    gs["offers"] = [x for x in gs["offers"] if D - x["day"] <= YEAR]
    for job in sorted(votes, key=GUILD_JOBS.index):
        vs = votes[job]
        writers = sorted(vs)
        hs = {n: _house_of(state, n) for n in writers}
        off = next((x for x in gs["offers"] if x["job"] == job), None)
        houses = sorted({h for h in hs.values() if h} | set(off["houses"] if off else []))
        el = set(eligible(state, job, jd))
        named = sorted({m for v in vs.values() for m in v[2] if m in el} | (set(off["people"]) & el if off else set()))
        cur = next((x for x in active_guilds(state) if x["job"] == job), None)
        ch, txt = g7._tally(state, {n: _js([v[0], v[1]]) for n, v in vs.items()}, w)
        rate, ap = json.loads(ch)
        if cur:
            add = [m for m in named if m not in cur["people"]]
            cur["people"] = sorted(set(cur["people"]) | set(add))
            if len({h for h in hs.values() if h}) >= C3_HOUSES:
                cur["rate"], cur["apprentice"] = rate, ap
            if add:
                log(state, "仲間", None, f"{'・'.join(add)} が {job} の仲間に入った (書いた人 {'・'.join(writers)})", guild=cur["id"])
            continue
        solo = GUILD_SOLO and len(houses) < C3_HOUSES and len(named) >= C3_PEOPLE and len(_houses(state, named)) >= C3_HOUSES
        if len(houses) < C3_HOUSES and not solo:
            why = (f"{job} の仲間は、ちがう家の答える人 2 人以上が書くと結ぶ。いまは {'・'.join(writers)} の家だけなので、「仲間の申し出」として次の集まりに出す")
            if off:
                off["people"] = sorted(set(off["people"]) | set(named))
                off["by"] = sorted(set(off["by"]) | set(writers))
            else:
                gs["offers"].append({"job": job, "people": named, "by": writers, "houses": houses, "day": D, "rate": rate, "apprentice": ap})
            log(state, "仲間", writers[0], why, guild_offer=job)
            continue
        if len(named) < C3_PEOPLE or len(_houses(state, named)) < C3_HOUSES:
            why = (f"{job} の仲間を結べなかった (書かれた人のうち、前の 1 年にその仕事を {GUILD_MIN_DAYS} 日以上した大人が {len(named)} 人・"
                   f"{len(_houses(state, named))} 家で、{C3_PEOPLE} 人・{C3_HOUSES} 家に足りない。書いた人 {'・'.join(writers)})")
            _fail(state, writers[0], "仲間", why)
            continue
        x = {"id": f"K{gs['next']}", "job": job, "people": named, "houses": _houses(state, named), "rate": rate, "apprentice": ap,
             "by": sorted(set(writers) | set(off["by"] if off else [])), "day": D, "status": "結んだ", "rest": 0}
        gs["next"] += 1
        gs["list"].append(x)
        gs["offers"] = [o for o in gs["offers"] if o["job"] != job]
        log(state, "仲間", None, f"{job} をする {len(named)} 人 ({'・'.join(named[:8])}{' ほか' if len(named) > 8 else ''}) が、誓って仲間を結んだ [{x['id']}]。"
            f"品のねうちは {rate} 倍・弟子を{'とる' if ap else 'とらない'} (書いた人 {'・'.join(x['by'])}"
            + ("。1 つの家の答えだが、2 つ以上の家の人を名前で書いたので結んだ" if solo else "") + f"。{g7_vote(txt)})", guild=x["id"], solo=solo)
        _reach(state, "F3", D, f"{job} をする {len(named)} 人が、誓って仲間を結んだ")


def apprentice(state, p, act):
    """弟子の腕の上がり方の倍 (g7.craft_step から): 仲間 (弟子をとる) の人でない人が、with に仲間の人の名前を書き、その人と同じ日に同じ仕事をすると 1.5 倍"""
    for gd in active_guilds(state):
        if gd["job"] != act or not gd["apprentice"] or p["name"] in gd["people"]:
            continue
        wi = set(((p.get("plan") or {}).get("with")) or [])
        if any(q["name"] in wi and q["name"] in gd["people"] and (q.get("today") or {}).get("activity") == act for q in era2.adults(state)):
            return APPRENTICE
    return 1.0


def _guild_year(state):
    """年の終わり: 仲間ごとに、仲間の人のその仕事の人日 (前の 1 年)。90 人日に足りなければ「休んでいる」、2 年つづけば終わる。人が 3 人より少なくなっても終わる。c3"""
    g, D = _g(state), state["day"]
    y = D // YEAR
    alive = {p["name"] for p in era2.adults(state)}
    jd = job_days(state)
    ok = []
    rows = {}
    for x in active_guilds(state):
        x["people"] = [n for n in x["people"] if n in alive]
        days = sum(jd.get(n, {}).get(x["job"], 0) for n in x["people"])
        hs = _houses(state, x["people"])
        rows[x["id"]] = {"job": x["job"], "people": len(x["people"]), "houses": len(hs), "days": days, "rate": x["rate"], "apprentice": x["apprentice"]}
        if len(x["people"]) < C3_PEOPLE or len(hs) < C3_HOUSES:
            x["status"] = "終わった"
            _fail(state, None, "仲間", f"{x['job']} の仲間 [{x['id']}] は、仲間の人が {len(x['people'])} 人・{len(hs)} 家になったので終わった")
            continue
        if days < C3_DAYS:
            x["rest"] += 1
            x["status"] = "休んでいる"
            if x["rest"] >= GUILD_REST_END:
                x["status"] = "終わった"
                _fail(state, None, "仲間", f"{x['job']} の仲間 [{x['id']}] は、{GUILD_REST_END} 年つづけて仲間の人がその仕事を {C3_DAYS} 人日しなかったので終わった")
            else:
                _fail(state, None, "仲間", f"{x['job']} の仲間 [{x['id']}] は、{y}年に仲間の人がその仕事を {days} 人日しかしなかったので休んでいる "
                      f"(1 年 {C3_DAYS} 人日に足りない。もう 1 年足りなければ終わる)")
            continue
        x["rest"], x["status"] = 0, "結んだ"
        ok.append(x["id"])
    g["guild_year"][str(y)] = {"ok": ok, "rows": rows}
    if y <= g["start"] // YEAR:
        return
    if ok and y not in g["c3_years"]:
        g["c3_years"].append(y)
        log(state, "目盛り", None, f"目盛り: G14 の条件 3 の年 ({y}年。続いている仲間 {'・'.join(ok)})", g="G14", c3_year=y)
    if all((y - i) in g["c3_years"] for i in range(C3_YEARS)):
        _cond(state, "c3", D, f"3 人以上・2 家以上で 1 年 {C3_DAYS} 人日以上の仲間がある年が {C3_YEARS} 年つづいた")


# ---------------- 目盛り・季節の終わり ----------------

def _reach(state, f, day, why):
    g = _g(state)
    if f in g["reached"] or day is None:
        return
    g["reached"][f] = day
    log(state, "目盛り", None, f"目盛り: G14 の {f}「{FS[f]}」に届いた ({why})", g="G14", f=f)


def _cond(state, c, day, why):
    g = _g(state)
    if c not in g["c"]:
        g["c"][c] = day
        log(state, "目盛り", None, f"目盛り: G14 の条件 {c[1:]}「{CS[c]}」に届いた ({why})", g="G14", c=c)


def _fail(state, who, what, why, log_it=True):
    """選んだのにできなかったこと・受けなかった・おくれた・破れた・休んだ。帳簿に残し、log_it なら出来事「町と市」にも (お題の節に出す)"""
    g, D = _g(state), state["day"]
    g["fails"].append({"day": D, "year": D // YEAR, "who": who, "what": what, "why": why})
    g["fails"] = g["fails"][-80:]
    row = g["path"].get(str((D + 1) // YEAR))
    if row is not None:
        row["failed"] = row.get("failed", 0) + 1
    if log_it:
        log(state, "町と市", who, why, g14_fail=what)


def season_end(state):
    """G14 の季節の終わり (g7.season_end。G13 の季節の終わりのあと): 出かけている人が帰る → 年の終わりなら書きつけの払い (c2)・町の家 (c1)・仲間 (c3)・帳簿"""
    D = state["day"]
    if (D + 1) % SEASON_DAYS:
        return
    _trips_end(state)
    if (D + 1) % YEAR == 0:
        _settle_notes(state)
        _town_year(state)
        _guild_year(state)
        _ledger(state)


def _ledger(state):
    g, D = _g(state), state["day"]
    y = D // YEAR
    ys = str(y)
    tw = g["town"].get(ys) or {}
    mk = g["market"]["year"].get(ys) or {}
    nt = g["notes"]["year"].get(ys) or {}
    gy = g["guild_year"].get(ys) or {}
    s13 = state["era2"]["g7"]["g13"]
    m13 = s13["mill"]
    c13 = s13["canal"]
    g["ledger"].append({"year": y, "day": D, "town_houses": tw.get("houses", 0), "town_people": tw.get("people", 0), "region": tw.get("region", 0),
                        "town_share": tw.get("share", 0.0), "town_answered": len(tw.get("answered") or []), "town_copied": len(tw.get("copied") or []),
                        "nonfood_days": tw.get("nonfood", 0), "worked_days": tw.get("worked", 0),
                        "market_trips": mk.get("trips", 0), "market_days": mk.get("days", 0), "market_grain": mk.get("grain", 0),
                        "market_pots": mk.get(POT, 0), "market_sickles": mk.get(SICKLE, 0), "market_to": {k: dict(v) for k, v in (mk.get("to") or {}).items()},
                        "market_houses": dict(mk.get("houses") or {}),
                        "notes_written": nt.get("written", 0), "notes_accepted": nt.get("accepted", 0), "notes_refused": nt.get("refused", 0),
                        "notes_paid": len(set(nt.get("paid") or [])), "notes_late": len(nt.get("late") or []), "notes_broken": len(nt.get("broken") or []),
                        "notes_grain": nt.get("grain", 0), "notes_by": dict(nt.get("by") or {}),
                        "guilds": {k: dict(v) for k, v in (gy.get("rows") or {}).items()}, "guilds_ok": list(gy.get("ok") or []),
                        "mills": len(m13["mills"]), "mills_running": len(g13.mills_running(state)), "mill_repair": m13["repair"].get(ys, 0.0),
                        "canal_cap": c13["cap"], "canal_dug": c13["dug"].get(ys, 0), "canal_lost": sum(x["lost"] for x in c13["lost"] if x["year"] == y),
                        "readers": len(g10.readers(state)), "pots": era2._g6_have(state, "村", POT), "sickles": era2._g6_have(state, "村", SICKLE),
                        "store": era2._g6_have(state, "村", GRAIN), "store_days": era2.store_days(state),
                        "fails": sum(1 for f in g["fails"] if f["year"] == y), "town_store": town_store(state)})
    g["ledger"] = g["ledger"][-40:]


def town_store(state):
    """村の中の差 (ならべて測る): 町の家と、そうでない家の、家の倉の草の種 (家の倉がなければ 0) [町の家, そうでない家]"""
    town = set(town_now(state)[0])
    a = b = 0
    for h in era2._homes(state):
        v = era2._g6_have(state, h, GRAIN)
        if h in town:
            a += v
        else:
            b += v
    return [a, b]


def reached(state, f):
    return bool(on(state) and _g(state)["reached"].get(f))


def done(state):
    return {c: c in _g(state)["c"] for c in CS}


def progress(state):
    """条件ごとの進み (段 × 1000 + 数。yardstick._stall が年の終わりに読む。G14_design.md 2.3):
    c1: 町の家に住む人 ÷ 地域の人 (‰ の 10 分の 1、100 まで) × 10 + つづいた年 × 1000 + 町の家の数 × 10
    c2: 段 (0 / 1 F2) × 1000 + その年 (なければ前の年) に書きつけどおり払った集落の数 × 100 + 3 集落以上の年の回数 × 1000
    c3: 段 (0 / 1 F3) × 1000 + その年の仲間の人日 (90 に対して、100 まで) + つづいた年 × 1000"""
    g = _g(state)
    y = _y(state)
    tw = g["town"].get(str(y)) or g["town"].get(str(y - 1)) or {}
    run = 0
    yy = max((int(k) for k in g["town"]), default=y)
    while (yy - run) in g["c1_years"]:
        run += 1
    c1 = min(100, round(1000 * tw.get("share", 0) / 10)) * 10 + run * 1000 + tw.get("houses", 0) * 10
    nt = g["notes"]["year"].get(str(y)) or g["notes"]["year"].get(str(y - 1)) or {}
    c2 = (1 if "F2" in g["reached"] else 0) * 1000 + len(set(nt.get("paid") or [])) * 100 + len(g["c2_years"]) * 1000
    gy = g["guild_year"].get(str(y)) or g["guild_year"].get(str(y - 1)) or {}
    best = max((r["days"] for r in (gy.get("rows") or {}).values()), default=0)
    run3 = 0
    yy = max((int(k) for k in g["guild_year"]), default=y)
    while (yy - run3) in g["c3_years"]:
        run3 += 1
    c3 = (1 if "F3" in g["reached"] else 0) * 1000 + min(100, round(100 * best / C3_DAYS)) + run3 * 1000
    return {"c1": c1, "c2": c2, "c3": c3}


# ---------------- 道の見張り (答える人のうち、その道を自分で選べる人で数える。G14_design.md 6.) ----------------

def knowers_alive(state, card=CARD_GUILD):
    alive = {p["name"] for p in era2.adults(state)}
    return sorted(n for n in (((state["era2"]["g7"].get("hints") or {}).get("knowers") or {}).get(card) or []) if n in alive)


def key_houses(state):
    """見本の家に必ず足す家: 読み書きできる人の家 (書きつけ)・札 H13-02 を知っている人の家・仲間の人の家"""
    names = set(g10.readers(state)) | set(knowers_alive(state)) | {n for x in active_guilds(state) for n in x["people"]}
    return sorted({p.get("household") for p in era2.adults(state) if p["name"] in names and p.get("household")})


def paths(state):
    """いまのお題に答える人のうち、まだ届いていない条件ごとに、その道を自分で選べる人の名前。
    c1: 答える人みな (家の大人の仕事を決められる)。
    c2: 読み書きできる人のいる家の答える人 (書きつけを受けてくれそうな集落が 1 つ以上あるとき)。読める人が 0 人なら 0。
    c3: 仲間を結べる仕事 (入れる人 3 人・2 家) があれば、その人たちの家の答える人と、札 H13-02 を知る人の家の答える人。結んだ仲間があれば、その人たちの家の答える人も。
        どちらもなければ 0"""
    g = _g(state)
    ans = era2.answerers(state)
    hs = {p["name"]: p.get("household") for p in era2.adults(state)}
    c2 = [n for n in ans if house_readers(state, n)] if note_places(state) else []
    oj = open_jobs(state)
    names = {m for e in oj.values() for m in e} | ({m for x in active_guilds(state) for m in x["people"]})
    if oj:
        names |= set(knowers_alive(state))
    gh = {hs.get(m) for m in names if hs.get(m)}
    c3 = [n for n in ans if hs.get(n) in gh]
    out = {"c1": list(ans), "c2": c2, "c3": c3}
    return {k: v for k, v in out.items() if k not in g["c"]}


def note_places(state):
    """書きつけを受けてくれそうな集落 (よく知っている・信頼 0.5 以上・いま土器か鎌をほしがっている・払っていない書きつけがない。近い順)"""
    g = _g(state)
    busy = {n["to"] for n in g["notes"]["list"] if n["status"] in ("待つ", "おくれ")}
    return sorted((o for o in _others(state) if known(o) and o.get("trust", 0.5) >= NOTE_TRUST and any(wants(state, o).values()) and o["id"] not in busy
                   and not g12.struggling(o)), key=lambda o: (o["days"], int(o["id"][1:])))


def _chose(state, real):
    """この集まりで、道を実際に選んだ答える人の数 (市へ運ぶを自分か家の人に割り振った・家の大人の仕事の半分以上を食べ物でない仕事にした・note・guild を書いた)"""
    k = 0
    for n, a in real.items():
        if not isinstance(a, dict):
            continue
        txt = json.dumps({x: a.get(x) for x in ("year", "job", "family")}, ensure_ascii=False)
        if ACT_MARKET in txt or g12._rows(a.get("note")) or a.get("guild") or _half_nonfood(a):
            k += 1
    return k


def _half_nonfood(a):
    """答えの中の仕事 (job と family。年の答えなら季節ごと) の半分以上が食べ物でない仕事か"""
    acts = []

    def add(part):
        if not isinstance(part, dict):
            return
        for j in [part.get("job")] + list((part.get("family") or {}).values() if isinstance(part.get("family"), dict) else []):
            act = j.get("activity") if isinstance(j, dict) else j if isinstance(j, str) else None
            if act:
                acts.append(act)
    if isinstance(a.get("year"), dict):
        for v in a["year"].values():
            add(v)
    else:
        add(a)
    return bool(acts) and sum(1 for x in acts if x in NONFOOD) * 2 >= len(acts) and sum(1 for x in acts if x in NONFOOD) > 0


def count_paths(state, real):
    """集まりの答えを当てはめるとき (g7.apply_year から。答えを当てはめる前の state で): この集まりの、道を選べた人・選んだ人を、その年 ((日 + 1) ÷ 120) に足す"""
    g = _g(state)
    y = str((state["day"] + 1) // YEAR)
    row = g["path"].setdefault(y, {"meetings": 0, "c1": 0, "c2": 0, "c3": 0, "chose": 0, "failed": 0, "readers": 0, "who": {}})
    row["meetings"] += 1
    row["readers"] = max(row.get("readers", 0), len(g10.readers(state)))
    for k, names in paths(state).items():
        row[k] += len(names)
        if names:
            row["who"][k] = sorted(set(row["who"].get(k, [])) | set(names))[:12]
    row["chose"] += _chose(state, real)


def apply_answers(state, real):
    """集まりの答え (g7.apply_year から。G12 の pact・help のあと): 書きつけ (note) → 仲間 (guild)"""
    apply_notes(state, real)
    apply_guilds(state, real)


def fails_year(state, y):
    return [f for f in _g(state)["fails"] if f["year"] == y]


def path_consult(state, done_list):
    """年の終わり: まだ届いていない条件の道を、自分で選べる答える人が、G14 に入ってからのまる 2 年つづけて 0 人なら止めて相談。一度ずつ。
    そのほか、G14 に入った日から 5 年ごとに止めて相談 (6,000 万トークンの目安はワークフローの側で見る)"""
    g, D = _g(state), state["day"]
    y = (D + 1) // YEAR - 1
    y0 = (g["start"] + 1) // YEAR
    for k in ("c1", "c2", "c3"):
        if k in g["c"]:
            continue
        ys = [y - i for i in range(PATH_YEARS)]
        if ys[-1] < y0:
            continue
        if all(((g["path"].get(str(x)) or {}).get(k, 0) == 0) for x in ys):
            if not any(c["why"] == f"g14_path_{k}" and c.get("year") == y for c in done_list):
                return {"why": f"g14_path_{k}", "year": y, "day": D,
                        "text": f"G14 の条件 {k[1:]} ({CS[k]}) の道を、自分で選べる答える人が {PATH_YEARS} 年つづけていなかった (仕組みのまちがいとして相談)"}
    return years_consult(state, done_list)


def years_consult(state, done_list):
    """G14 に入った日 (178年60日目) から 5 年ごとに止めて相談 (183年60日目 = 22019 日目・188年60日目 …。季節の終わりに g7.consult_why が見る)"""
    g, D = _g(state), state["day"]
    if D > g["start"] and (D - g["start"]) % (LATER_YEARS * YEAR) == 0:
        why = f"g14_years_{D}"
        if not any(c["why"] == why for c in done_list):
            return {"why": why, "day": D, "text": f"G14: G14 に入って {(D - g['start']) // YEAR} 年たった (5 年ごとの相談)"}
    return None


def report_lines(state):
    """報告に書くこと (止めない): できなかったことが 1 年に 3 回以上・読める大人が 1 人だけ / 0 人・選べた人はいるのに、だれも選ばなかった年が 3 年つづいた・
    畑の世話が要る手間を下回った年・水の輪が止まった・水の道がへった"""
    g, out = _g(state), []
    y = _y(state)
    f = fails_year(state, y)
    if len(f) >= FAIL_REPORT:
        out.append(f"この年に、選んだのにできなかったこと {len(f)} 回: " + " / ".join(x["why"][:60] for x in f[-5:]))
    if "c2" not in g["c"]:
        rd = g10.readers(state)
        if not rd:
            out.append("読み書きできる大人が 0 人 (書きつけの道は閉じている。字を習う道だけ)")
        elif len(rd) == 1:
            out.append(f"読み書きできる大人は {rd[0]} だけ")
    py = (state["day"] + 1) // YEAR
    if str(py) not in g["path"]:  # 年の終わりの日 (次の年の集まりの前) は、まだその年の行がないので、前の年から数える
        py -= 1
    rows = [g["path"].get(str(py - i)) for i in range(IDLE_YEARS)]
    if all(r and r.get("meetings") and (r["c1"] + r["c2"] + r["c3"]) > 0 and r.get("chose", 0) == 0 for r in rows):
        out.append(f"選べた答える人はいるのに、町の家・市へ運ぶ・書きつけ・仲間を、だれも選ばなかった年が {IDLE_YEARS} 年つづいた")
    short = g13.field_short(state)
    if short:
        out.append(short)
    s13 = state["era2"]["g7"]["g13"]
    st = [x["id"] for x in s13["mill"]["mills"] if x.get("stopped")]
    if st:
        out.append(f"止まっている水の輪: {'・'.join(st)} (直す手がなかった)")
    lost = [x for x in s13["canal"]["lost"] if x["year"] >= y - 1 and x["year"] >= g["start"] // YEAR]
    if lost:
        out.append(f"水の道がへった: {'・'.join(str(x['year']) + '年 ' + str(x['lost']) + ' つかみ分' for x in lost)} (手入れが足りなかった)")
    return out


def indicators(state):
    """G14 の目安 (era2.indicators に足す。【シ】)"""
    g = _g(state)
    y = str(_y(state))
    tw = g["town"].get(y) or g["town"].get(str(int(y) - 1)) or {}
    mk = g["market"]["year"].get(y) or {}
    nt = g["notes"]["year"].get(y) or {}
    return {"g14_c1_day": g["c"].get("c1"), "g14_c2_day": g["c"].get("c2"), "g14_c3_day": g["c"].get("c3"),
            "g14_town_houses": tw.get("houses", 0), "g14_town_people": tw.get("people", 0), "g14_town_share": tw.get("share", 0.0),
            "g14_c1_years": len(g["c1_years"]), "g14_market_trips": mk.get("trips", 0), "g14_market_grain": mk.get("grain", 0),
            "g14_notes": sum(1 for n in g["notes"]["list"] if n["status"] in ("待つ", "おくれ")), "g14_notes_paid": len(set(nt.get("paid") or [])),
            "g14_c2_years": len(g["c2_years"]), "g14_guilds": len(active_guilds(state)), "g14_c3_years": len(g["c3_years"]),
            "g14_readers": len(g10.readers(state)), "g14_fails": len(fails_year(state, int(y)))}


# ---------------- お題 ----------------

def facts(state):
    """お題の決まりの文 (G14 から)。条件の名前と判定の文は書かない (5.3)"""
    return (f"町の家: 年の終わりに、家の大人が働いた日の半分以上が、食べ物でない仕事 ({NONFOOD_WORDS}) だった家を「町の家」と呼ぶ。町の家も村の倉から食べる。\n"
            f"市へ運ぶ: 主な仕事を「{ACT_MARKET}」(to に村の番号) にすると、村の倉の土器 (1 人 {era2.LOAD[POT]} 個) か鎌 (1 人 {era2.LOAD[SICKLE]} 本) を、"
            f"ほしがっている村に運んで、草の種を受けて帰る (土器 1 個 = 草の種 {era2.VALUE[POT]} つかみ・鎌 1 本 = {era2.VALUE[SICKLE]} つかみ)。"
            "行って帰る日数は、歩く日の 2 倍と 1 日。1 つの村が 1 年に払えるのは、その村の草の種の 2 割まで。\n"
            "書きつけ: 字が書ける人が書くと、いま品を渡して、相手の次の年の終わりに草の種で払ってもらえる。相手が苦しい年は 1 年おくれる。2 年払えなければ破れる。"
            "字のない「あとで払う」はできない。\n"
            f"仲間: 同じ仕事を {GUILD_MIN_DAYS} 日以上した大人 {C3_PEOPLE} 人以上 (2 つ以上の家) が、誓って仲間を結べる。仲間は、その品のねうち ({RATE_MIN}〜{RATE_MAX} 倍) と"
            f"弟子を決める。2 つ以上の家の人を名前で書けば、1 人の答えでも結べる。1 年 {C3_DAYS} 人日その仕事をしないと休み、2 年休むと終わる。\n")


def _want_text(state, k=3):
    rows = []
    for o in market_places(state)[:k]:
        rows.append(f"{o['id']} {o['name']} ({_gw(wants(state, o))}。歩いて {o['days']} 日)")
    return "・".join(rows) or "いまはない"


def note_example(state, name):
    """書きつけの例 (受ける決まりに合う形)。受けてくれそうな集落のうち近いほうから。なければ None"""
    rd = house_readers(state, name)
    if not rd:
        return None
    by = name if name in rd else rd[0]
    for o in note_places(state):
        w = wants(state, o)
        give = {}
        for k in GOODS:
            n = min(w[k], era2._g6_have(state, "村", k))
            if n > 0:
                give[k] = n
        while give and value(state, give, by) > NOTE_MAX:
            k = max(give, key=lambda x: (give[x], x))
            give[k] -= 1
            if not give[k]:
                give.pop(k)
        if not give:
            continue
        v = value(state, give, by)
        take = {GRAIN: min(v, int(NOTE_GRAIN_SHARE * o.get("grain", 0)))}
        rate = v / max(1, sum(era2.VALUE[k] * n for k, n in give.items()))
        if note_why(state, o, give, take, rate) is None:
            return {"to": o["id"], "give": give, "take": take, "by": by}
    return None


def prompt_block(state, p):
    """「## いま」の答えの並びのすぐ前に置く短い節 (G14 に入る日から。G12_design.md 12. の学び)。G13 の節は「続けること」の 1 行に、G12 の節も同じ行にまとめる。
    その人がこの集まりでできること (町の家・市へ運ぶ・書きつけ・仲間)・続けること・3 つの進み。せかす言葉は書かない"""
    if not p:
        return ""
    g = _g(state)
    name = p["name"]
    rows = [BLOCK_HEAD.replace("あなたが", f"あなた ({name}) が", 1)]
    h = p.get("household")
    town, ppl, reg, hd = town_now(state)
    nf, w = hd.get(h, [0, 0])
    sh = round(10 * nf / w) if w else 0
    rows.append(f"- 町の家: あなたの家 ({h}) の大人が前の 1 年に働いた日のうち、食べ物でない仕事 ({NONFOOD_WORDS}) は {sh} 割"
                + (f" (半分にはあと 約 {to_town(nf, w)} 人日)" if w and nf * 2 < w else "") + "。半分をこえると「町の家」になる。家の大人の仕事は family で決める")
    if prompt_fixed(state):
        rows.append(market_line(state))
    else:
        rows.append(f"- 市へ運ぶ: 主な仕事を「{ACT_MARKET}」(to に村の番号) にすると、村の倉の土器と鎌を、ほしがっている村に運んで、草の種を受けて帰る。"
                    f"いまほしがっている村: {_want_text(state)}")
    rd = house_readers(state, name)
    allr = g10.readers(state)
    if prompt_fixed(state):
        rows.append(note_line(state, name, rd, allr))
    elif rd:
        ex = note_example(state, name)
        who = "あなたは" if name in rd else f"あなたの家の {'・'.join(rd)} は"
        rows.append(f"- 書きつけ: {who}字が書けるので、「いま渡して、次の年の終わりに草の種で払ってもらう」書きつけを書ける (note。1 つの村に 1 つ)。"
                    + (f"例: \"note\": [{_js(ex)}]" if ex else "いま受けてくれそうな村はない"))
    else:
        rows.append(f"- 書きつけ: 書けるのは字を書ける {'・'.join(allr) or '人 (いまいない)'}" + (" (その家の代表が書く)" if allr else ""))
    oj = open_jobs(state)
    if prompt_fixed(state):
        rows.append(guild_line(state, name, oj))
        rows.append(keep_line(state, p))
        rows.append("- note・pact・help・guild は答えた人の中でいちばん多い中身に決まる (1 人の答えでも決まる)。書かないなら \"note\": []・\"guild\": null")
        rows.append("いまの進み (町と市と仲間):")
        rows += progress_lines(state)
        return "\n".join(rows) + "\n"
    pot = eligible(state, "土器づくり")
    kn = knowers_alive(state)
    ln = f"- 仲間: 同じ仕事の人が誓って「仲間」を結ぶと、その品のねうち ({RATE_MIN}〜{RATE_MAX} 倍) と弟子 (一緒に働くと腕が早く上がる) を決められる。"
    if name in kn:
        ln += "あなたは、川下の町の職人の誓いの話を知っている。"
    ln += (f"前の 1 年に {GUILD_MIN_DAYS} 日以上土器を作った人は {len(pot)} 人 ({len(_houses(state, pot))} 家)。" if pot else "")
    ln += ("いま結べる仕事: " + "・".join(f"{j} ({len(e)} 人)" for j, e in oj.items()) + "。" if oj else "いま結べる仕事はない (3 人・2 家が要る)。")
    ag = active_guilds(state)
    if ag:
        ln += "結んだ仲間: " + "・".join(f"{x['job']} {len(x['people'])} 人 ({x['status']})" for x in ag) + "。"
    offs = g["guilds"]["offers"]
    if offs:
        ln += "仲間の申し出: " + "・".join(f"{x['job']} ({'・'.join(x['by'][:3])} が書いた)" for x in offs) + "。"
    ln += ("ちがう家の答える人が 2 人以上同じ仲間を書くか、1 人でも 2 つ以上の家の人を名前で書くと結ぶ。例: \"guild\": {\"仕事\": \"土器づくり\", \"人\": [\"…\", \"…\", \"…\"], \"ねうち\": 1.1, \"弟子\": true}"
           if oj or ag or offs else "")
    rows.append(ln)
    rows.append(keep_line(state, p))
    rows.append("- note・pact・help・guild は答えた人の中でいちばん多い中身に決まる (1 人の答えでも決まる。仲間は 2 つ以上の家の人が要る)")
    rows.append("いまの進み (町と市と仲間):")
    rows += progress_lines(state)
    return "\n".join(rows) + "\n"


def _trip(state, o):
    """o へ 1 人が 1 回運ぶと受ける草の種 (いま持って行く品のねうち) と、行って帰る日数"""
    return value(state, _carry(state, o, None)), 2 * o["days"] + 1


def market_line(state):
    """直しのあとの「市へ運ぶ」の行 (G14_PROMPT_FROM から): 仕事の書き方の例・ほしがっている村・1 回で受ける草の種・運べる村みなを合わせた量 (この季節)。
    数は今の決まりのまま、いまの state から (ふやして見せない)"""
    mp = market_places(state)
    if not mp:
        return (f"- 市へ運ぶ: 主な仕事を「{ACT_MARKET}」にすると、村の倉の土器と鎌を、ほしがっている村に運んで、草の種を受けて帰る。"
                "いまは、土器と鎌をほしがっていて払える村がない (運んでも休むことになる)")
    o = mp[0]
    got, days = _trip(state, o)
    tot = sum(min(value(state, wants(state, x)), _pay_left(state, x)) for x in mp)
    return (f"- 市へ運ぶ: 季節ごとの job か family に {_js({'activity': ACT_MARKET, 'place': 'camp', 'to': o['id']})} のように書く (1 季節だけでもよい)。"
            f"村の倉の土器と鎌を運び、受けた草の種は村の倉に入る。運んだ日は食べ物でない仕事に数える。"
            f"いまほしがっている村: {_want_text(state)}。{o['id']} へ 1 回運ぶと、行って帰って {days} 日で 草の種 約 {got} つかみ。"
            f"いま運べる村 {len(mp)} を合わせても、この季節に受けられるのは 草の種 約 {tot} つかみ分 (村の倉の草の種は いま {g12._grain_have(state)} つかみ)")


def note_examples(state, name, k=3):
    """書きつけの例 (受ける形。受けてくれそうな集落の近いほうから k まで。ちがう村ごとに 1 つ)"""
    rd = house_readers(state, name)
    if not rd:
        return []
    by = name if name in rd else rd[0]
    out = []
    for o in note_places(state):
        w = wants(state, o)
        give = {}
        for kk in GOODS:
            n = min(w[kk], era2._g6_have(state, "村", kk))
            if n > 0:
                give[kk] = n
        while give and value(state, give, by) > NOTE_MAX:
            kk = max(give, key=lambda x: (give[x], x))
            give[kk] -= 1
            if not give[kk]:
                give.pop(kk)
        if not give:
            continue
        v = value(state, give, by)
        take = {GRAIN: min(v, int(NOTE_GRAIN_SHARE * o.get("grain", 0)))}
        rate = v / max(1, sum(era2.VALUE[kk] * n for kk, n in give.items()))
        if note_why(state, o, give, take, rate) is None:
            out.append({"to": o["id"], "give": give, "take": take, "by": by})
            if len(out) >= k:
                break
    return out


def note_line(state, name, rd, allr):
    """直しのあとの「書きつけ」の行: 書ける家には、受ける形の例 (ちがう村 3 つまで) と、受けると村に何が入るか。書けない家には、そのことと書ける人"""
    if not rd:
        return (f"- 書きつけ (note): あなたの家には字を書ける人がいないので、あなたの答えの note は書きつけにならない。書けるのは字を書ける "
                + ("・".join(allr) + " のいる家の答え" if allr else "人 (いまいない)"))
    who = "あなたは" if name in rd else f"あなたの家の {'・'.join(rd)} は"
    ex = note_examples(state, name)
    if not ex:
        return f"- 書きつけ (note): {who}字が書けるので、書きつけを書ける。いま受けてくれそうな村はない"
    return (f"- 書きつけ (note): {who}字が書けるので、書きつけを書ける (村ごとに 1 つ。いくつの村にも書ける)。"
            f"受けると、いま村の倉から品を渡し、相手は年の終わり (次の年の集まりの前) に草の種を村の倉に払う。"
            f"受ける形の例: \"note\": {_js(ex)} (合わせて 草の種 {sum(x['take'][GRAIN] for x in ex)} つかみ)")


def guild_example(state, name, job, el):
    """仲間の例の人 (入れる人 3 人・2 家。答える人が入れるなら自分、次に家の人、ほかは前の 1 年にその仕事を多くした人の順)"""
    jd = job_days(state)
    hs = {p["name"]: p.get("household") for p in era2.adults(state)}
    me = hs.get(name)
    order = sorted(el, key=lambda n: (n != name, hs.get(n) != me, -jd.get(n, {}).get(job, 0), n))
    pick = order[:C3_PEOPLE]
    if len({hs.get(n) for n in pick}) < C3_HOUSES:
        other = next((n for n in order if hs.get(n) != hs.get(pick[0])), None)
        if other:
            pick = pick[:C3_PEOPLE - 1] + [other]
    return pick


def guild_line(state, name, oj):
    """直しのあとの「仲間」の行: 入れる人の名前 (多い順)・1 人でも結べる決まり・名前の入った例・ねうちで村に何が入るか"""
    g = _g(state)
    ln = f"- 仲間 (guild): 同じ仕事の人が誓って「仲間」を結ぶと、その品のねうち ({RATE_MIN}〜{RATE_MAX} 倍) と弟子 (一緒に働くと腕が早く上がる) を決められる。"
    if name in knowers_alive(state):
        ln += "あなたは、川下の町の職人の誓いの話を知っている。"
    ag = active_guilds(state)
    if ag:
        ln += "結んだ仲間: " + "・".join(f"{x['job']} {len(x['people'])} 人 ({x['status']})" for x in ag) + "。"
    offs = g["guilds"]["offers"]
    if offs:
        ln += "仲間の申し出: " + "・".join(f"{x['job']} ({'・'.join(x['by'][:3])} が書いた)" for x in offs) + "。"
    if not oj:
        return ln + f"いま結べる仕事はない (前の 1 年にその仕事を {GUILD_MIN_DAYS} 日以上した人が {C3_PEOPLE} 人・{C3_HOUSES} 家要る)"
    job = "土器づくり" if "土器づくり" in oj else next(iter(oj))
    el = oj[job]
    jd = job_days(state)
    top = sorted(el, key=lambda n: (-jd.get(n, {}).get(job, 0), n))
    ln += ("いま結べる仕事: " + "・".join(f"{j} ({len(e)} 人)" for j, e in oj.items()) + "。"
           f"前の 1 年に {GUILD_MIN_DAYS} 日以上{job}をした人 (多い順): {'・'.join(top[:6])}" + (f" ほか {len(el) - 6} 人" if len(el) > 6 else "") + "。"
           f"\"人\" に名前を書いた人のうち、この人たちが仲間になる (自分も入るなら自分の名前も書く)。"
           f"あなた 1 人の答えでも、2 つ以上の家の {C3_PEOPLE} 人以上を書けば結ぶ。")
    ex = {"仕事": job, "人": guild_example(state, name, job, el), "ねうち": 1.1, "弟子": True}
    good = GOOD_OF_JOB.get(job)
    return (ln + f"例: \"guild\": {_js(ex)}"
            + (f" (ねうち 1.1 なら、市へ運ぶ・書きつけで {good} 1 つ = 草の種 {round(era2.VALUE[good] * 1.1)} つかみ。いまは {era2.VALUE[good]})" if good else ""))


def fields_json(state):
    """答えの形 (JSON) の欄 (直しのあとだけ。pact・help の後ろ)"""
    return ' "note": [], "guild": null,' if prompt_fixed(state) else ""


def keep_line(state, p):
    """続けること (G13 の水の輪と水の道の手入れ・G12 の倉の約束と助けと帳) の 1 行"""
    s12 = state["era2"]["g7"]["g12"]
    s13 = state["era2"]["g7"]["g13"]
    y = _y(state)
    due = round(g13._mill_due(state))
    st = [x for x in s13["mill"]["mills"] if x.get("stopped")]
    c = s13["canal"]
    need = max(0, round(c["cap"] / g13.CANAL_PER_DAY * g13.CANAL_KEEP - c["dug"].get(str(y), 0)))
    act = sum(1 for x in s12["pacts"].values() if g12._active(x))
    nd = g12.needy(state)
    fam = house_readers(state, p["name"])
    return (f"- 続けること: 水の輪の直し あと {due} 人日" + (f" (止まっている輪 {len(st)})" if st else "") + f" (主な仕事「{g13.ACT_MILL}」)・"
            f"水の道の手入れ あと {need} 人日 (「{g13.ACT_CANAL}」)。倉の約束 {act}・いま苦しい村 {'・'.join(o['id'] for o in nd) or 'なし'}・"
            f"帳は読める人が「{g12.ACT_CENSUS}」" + (f" ({'・'.join(fam)})" if fam else ""))


def progress_lines(state):
    """3 つの進み (1 行ずつ。村の人が見て分かる数だけ)"""
    g, y = _g(state), _y(state)
    out = []
    if "c1" in g["c"]:
        out.append(f"- 町の家: 届いた ({g['c']['c1']} 日目)")
    else:
        town, ppl, reg, _ = town_now(state)
        out.append(f"- 町の家: いま {len(town)} 家・{ppl} 人 (地域の人 約 {reg} 人。1 割 約 {round(reg * C1_SHARE)} 人をこえる年が {C1_YEARS} 年つづくと届く)")
    if "c2" in g["c"]:
        out.append(f"- 書きつけ: 届いた ({g['c']['c2']} 日目)")
    else:
        nt = g["notes"]["year"].get(str(y)) or g["notes"]["year"].get(str(y - 1)) or {}
        out.append(f"- 書きつけ: 書いたとおり払った村は、{'この年 ' + str(len(set(nt.get('paid') or []))) if nt else 'G14 に入ってからまだ 0'}"
                   f" (1 年に {C2_PLACES} つ以上の村が払った年が {C2_TIMES} 回で届く。いま {len(g['c2_years'])} 回)")
    if "c3" in g["c"]:
        out.append(f"- 仲間: 届いた ({g['c']['c3']} 日目)")
    else:
        ag = active_guilds(state)
        out.append(f"- 仲間: いま {len(ag)} ({C3_PEOPLE} 人・{C3_HOUSES} 家以上で 1 年 {C3_DAYS} 人日以上の仲間が {C3_YEARS} 年つづくと届く)")
    return out


def text(state, p):
    """お題の節「## 町と市と仲間」(長い節。短い節と重なる行は書かない)"""
    g, y = _g(state), _y(state)
    rows = []
    town, ppl, reg, hd = town_now(state)
    top = sorted(((h, nf / w) for h, (nf, w) in hd.items() if w), key=lambda x: (-x[1], x[0]))[:4]
    rows.append("- 町の家 (前の 1 年): " + (f"{len(town)} 家・{ppl} 人。" if town else "まだない。")
                + "食べ物でない仕事の割合の多い家: " + ("・".join(f"{h} {round(10 * s)} 割" for h, s in top) or "なし"))
    mk = g["market"]["year"].get(str(y)) or g["market"]["year"].get(str(y - 1)) or {}
    if mk.get("trips"):
        rows.append(f"- 市へ運んだ ({max((k for k in g['market']['year']), key=int)}年): {mk['trips']} 回・草の種 {mk['grain']} つかみを受けた ("
                    + "・".join(f"{k} {v['trips']} 回" for k, v in sorted(mk["to"].items(), key=lambda kv: int(kv[0][1:]))[:6]) + ")")
    nts = [x for x in g["notes"]["list"] if x["status"] in ("待つ", "おくれ")]
    if nts:
        rows.append("- まだ払われていない書きつけ: " + "・".join(f"[{x['id']}] {x['to']} 草の種 {x['take'][GRAIN]} つかみ ({x['status']})" for x in nts[:6]))
    done_n = [x for x in g["notes"]["list"] if x["status"] in ("払った", "破れた") and x.get("paid", x["day"]) is not None][-4:]
    if done_n:
        rows.append("- 終わった書きつけ: " + "・".join(f"[{x['id']}] {x['to']} {x['status']}" for x in done_n))
    for x in active_guilds(state):
        rows.append(f"- 仲間 [{x['id']}] {x['job']}: {'・'.join(x['people'][:8])}{' ほか' if len(x['people']) > 8 else ''} (ねうち {x['rate']} 倍・弟子を"
                    f"{'とる' if x['apprentice'] else 'とらない'}・{x['status']})")
    f = [x for x in g["fails"] if x["year"] >= y - 1][-4:]
    if f:
        rows.append("- 町と市と仲間で、できなかったこと: " + " / ".join(x["why"] for x in f))
    return "\n## 町と市と仲間\n" + "\n".join(rows) + "\n"


def feel_note(state, p):
    """気持ちだけのお題の行 (代表でない人は仕事を決めないので、代表に伝えられることだけ)"""
    out = []
    if p["name"] in g10.readers(state):
        out.append("- あなたは字が書けるので、家の代表と一緒に、よその村との書きつけを書ける")
    out.append("- 町の家・市へ運ぶ・仲間のことを、家の代表に伝えられる")
    return "\n" + "\n".join(out)


def field_rows(state, year=False):
    """答えの欄の説明 (g7._field_rows に足す)"""
    return [f"   市へ運ぶ: 主な仕事を「{ACT_MARKET}」にできる (大人ならだれでも。to に村の番号。例 {{\"activity\": \"{ACT_MARKET}\", \"place\": \"camp\", \"to\": \"N13\"}})",
            '   note: 書きつけ (字を書ける人が書く。1 つの村に 1 つ)。例 [{"to": "N13", "give": {"土器": 8}, "take": {"草の種": 320}, "by": "名前"}]',
            '   guild: 仲間 (同じ仕事の人)。例 {"仕事": "土器づくり", "人": ["名前", "名前", "名前"], "ねうち": 1.1, "弟子": true}']
