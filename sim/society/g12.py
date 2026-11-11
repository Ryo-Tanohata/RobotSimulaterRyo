"""G12「大きな都と帝国」(第 6 部「鉄とお金の帝国」の終わりの G。2026-11-10 本人の決め「おすすめどおりで進める」(お任せ)。docs/society_phase/G12_design.md)

- G12 に入るのは step.py next_part --closed-by-decision だけ (G11 を本人の決めで閉じてから。g7.start_g12)。G11 までは、このファイルを読みこみもしない
  (g7・era2・yardstick は state の g7.g12 があるときだけ、関数の中で読みこむ)。だから G1〜G11 は、お題・state・出来事・乱数が前と 1 バイトも変わらない
- 「お金の帝国」ではなく「倉と帳の帝国」として測る (集める・養う・数える)。条件 (3 つとも【村が決めた】。3 つともそろうと G12 の終わり = 第 6 部の終わり):
  c1 倉の約束の輪: 暦の 1 年に、村と倉の約束を結んでいて、その年の分を約束どおり村に出した集落が 5 つ以上。そういう年が 2 回 (つづかなくてよい)
  c2 倉から地域を養う: 暦の 1 年に、村の倉から 3 つ以上のよその集落へ (約束の助け・助けに渡す・貸す)、合わせて草の種 3 万つかみ (ねうちで) 以上。1 回でよい
  c3 人と倉の帳: 暦の 1 年に、読み書きできる人が、大人のいる家みなの人の数・村の倉の量・倉の約束 (あれば) を字で書いた (帳がそろった)。これが 2 年つづく
- F: F1 はじめての倉の約束 / F2 はじめて倉から助けを出した / F3 はじめての帳 / F4 約束の分が、はじめて村に届いた (刈り手が来た日もふくむ)
- 決め方は、欄 pact・help とも「いちばん多い手」(g7._tally。1 人の答えでも決まる)。だから倉から出す量には上限 (1 年に倉の 1 割・300 日分を切らない) を置く
- 相手の村は決まりで答える (乱数なし)。受けない・減らした・切れた・休んだには、いつもわけを残す (出来事と次のお題。_fail)
- G11 までの仕組み (黒い金属・字・印のかたまり・市の日・直し) は動きつづける。G11 の条件は「ならべて測る」(g7.before.G11 に写して数え直す)
- 暦の年: 帳 (c3) と帳簿は日 ÷ 120 (g10・g11 の帳簿と年報と同じ)。年の終わりの日 (年の集まりの日) のことは、終わる年に入れる。
  道の見張りの行だけは (日 + 1) ÷ 120 (g11.count_paths と同じ。年の集まりの答えは、始まる年に数える)
- 村の人に見せる文には「都」「帝国」「国」「税」「戸籍」と g11.WORDS を書かない (WORDS。試しで確かめる)。村の中の呼び名は「倉の約束」「倉から助ける」「帳」「刈り手」
"""
import json
import re

import era2
import g10
import g11
from world import log

YEAR, SEASON_DAYS = era2.YEAR, era2.SEASON_DAYS
ACT_CENSUS = "帳をつける"  # 新しい仕事 (world.ACTS7 に足した。G12 で読み書きできる人がいるときだけ選べる)
GRAIN, GOAT, IRON, OBS, HANDS = "草の種", "ヤギ", g10.IRON, "黒曜石", "刈り手"
GIVE_GOODS = (GRAIN, GOAT, IRON)  # 苦しい年に村が出す物・助けに渡す物
TAKE_GOODS = (GRAIN, OBS, HANDS)  # ふだんの年に相手が村に出す物
C1_MIN, C1_TIMES = 5, 2  # c1: 約束どおり出した集落が 1 年に 5 つ以上の年が 2 回【仮定】
C2_SETTLEMENTS, C2_AMOUNT = 3, 30000  # c2: 1 年に 3 集落以上へ、合わせて 3 万つかみ (ねうち) 以上【仮定】
C3_YEARS = 2  # c3: 帳がそろった年が 2 年つづく【仮定】
PACT_WALK = 3  # 約束を受ける村: 歩いて 3 日以内
TAKE_GRAIN_PER = 10  # 相手が 1 年に出せる草の種: その村の人 × 10 つかみまで【仮定】
TAKE_HANDS_SHARE, TAKE_HANDS_DAYS = 0.2, 20  # 刈り手: その村の人の 2 割 (1 人から) × 20 日まで【仮定】(よその村は大人の数を持たないので、人の数で見る)
TAKE_OBS_SHARE = 0.5  # 黒曜石: その村の持つ分の半分まで【仮定】
GIVE_RATIO = 5  # 相手は、give のねうちが take の 5 倍以上のとき受ける【仮定】
LOW_GRAIN = 100  # 苦しい村: 地域の天気が悪い年か、蓄えが 1 人 100 つかみより少ない (g11._redeem と同じ)
CAP_SHARE, CAP_DAYS = 0.1, 300  # 倉から出すのは 1 年に年のはじめの倉の 1 割まで・出したあと今の人数で 300 日分を切らない【仮定】
HOUSES_PER_DAY = 2  # 帳: 1 人 1 日に 2 家 (家を書き終えたら、倉、そのあと約束。どれも 1 つで 1 家分)【仮定】
MISS_LIMIT = 2  # 苦しくない年に 2 年つづけて出せなければ切れる (地域の貢ぎは 1 回で切れる。決まりの村の B1W だけ 1 にする)
BAD_EXEMPT = True  # 苦しい年は出さなくてよい (決まりの村の B1W だけ False: 地域の貢ぎと同じく、苦しい年に出せないのも「出せなかった」)
TRUST_KEEP, TRUST_MISS, TRUST_BROKE = 0.1, 0.1, 0.2  # 約束どおり・助け +0.1 / 相手が出せずに切れた −0.1 / 村が約束を破った −0.2
HAND_REAP = 150  # 刈り手 1 人 1 日に刈る量 (村の人の畑仕事と同じ。era2._field_work)
HAND_EAT = 30  # 刈り手 1 人 1 日に食べる量 (草の種のつかみ。大人 1 人の 1 日分のおよそ。村の蓄えから)【仮定】
HAND_VALUE = round(150 * 0.1)  # 刈り手 1 人日のねうち (刈る量の 1 割。era2 の「刈り手の取り分は 1 割」と同じ)【仮定】
IRON_VALUE = 2 * era2.VALUE["鎌"]  # 黒い金属の鎌 1 本のねうち (石の鎌の 2 倍刈れる)【仮定】
PATH_YEARS = 2  # 道の見張り: 選べる答える人が 2 年つづけて 0 人なら止めて相談
IDLE_YEARS = 3  # 選べた人はいるのに、だれも選ばなかった年がつづいたら報告 (止めない)
FAIL_REPORT = 3  # 1 年に「選んだのにできなかった」がこれだけあれば、報告に書く
PART6_LIMIT_DAY = 20279  # 第 6 部の 50 年 (168年120日目)。G12 の最初の相談 (g7.consult_why の部の年数)。そのあとは 5 年ごと (path_consult)
LATER_YEARS = 5
WORDS = ("都", "帝国", "国", "税", "戸籍") + g11.WORDS  # 村の人に見せる G12 の文に書かない言葉
FS = {"F1": "はじめての倉の約束", "F2": "はじめて倉から助けを出した", "F3": "はじめての帳", "F4": "約束の分が、はじめて村に届いた"}
CS = {"c1": "倉の約束の輪", "c2": "倉から地域を養う", "c3": "人と倉の帳"}
FALLEN_RE = re.compile(r"刈らずに残った草の種 約 (\d+) つかみ")
# 2026-11-11 本人の決め「お題を直して 5 年見る」(G12_design.md 12.): G12 の 4 年、答える人は pact・help・仕事「帳をつける」をほとんど選ばなかった
# (168年は 0)。お題が 255 KB あり、節「## 倉と約束と帳」は 900 行目ほどに埋もれていた。G12_PROMPT_FROM (168年120日目。第 6 部の 50 年の相談の日) から、
# 「## いま」の答えの並びのすぐ前に、その人がこの集まりでできること (pact・help・帳) と、3 つの進みを短く書く (prompt_block)。決まりと数は変えない。
# その日 (お題は前のコードで出ていた) は、step.py refresh_prompts が g7.g12.prompt_fix を書いたあとだけ (g11.trust_fixed・g7.feel_capped と同じ形)。
# だから、その日までの歩をやり直しても、state もお題も前と 1 バイトも同じ
G12_PROMPT_FROM = 20279
BLOCK_HEAD = "倉と約束と帳: この集まりで、あなたができること (どれも、しなくてもよい。書かなければ今のまま)"


def on(state):
    return "g12" in ((state.get("era2") or {}).get("g7") or {})


def _g(state):
    return state["era2"]["g7"]["g12"]


def prompt_fixed(state):
    """お題の直し (G12_PROMPT_FROM) が効くか: その日より後はいつも。その日は refresh_prompts の印 (g7.g12.prompt_fix) のあとだけ"""
    return on(state) and (state["day"] > G12_PROMPT_FROM or (state["day"] == G12_PROMPT_FROM and "prompt_fix" in _g(state)))


def mark_prompt_fix(state, why):
    """refresh_prompts から: G12_PROMPT_FROM の日に、お題の直しを今の歩から入れたことを g7.g12.prompt_fix に残す (その日より前なら何もしない)"""
    if on(state) and state["day"] >= G12_PROMPT_FROM and "prompt_fix" not in _g(state):
        _g(state)["prompt_fix"] = {"day": state["day"], "why": why}


def _y(state):
    return state["day"] // YEAR


def _others():
    import g7
    return g7._others


def _other(state, oid):
    import g7
    return next((o for o in g7._others(state) if o["id"] == oid), None)


def _grain_have(state):
    return era2._g6_have(state, "村", GRAIN)


# ---------------- G12 に入る (g7.start_g12 から) ----------------

def start(state):
    """G12 の state を作る: G11 の物差し (条件・F・道の見張り・出し入れ) を g7.before.G11.g11 に写し、条件と道の見張りは数え直す
    (F は村に起きたことなので消さない。G10 のときと同じ)。倉の約束・助け・帳は入る日から"""
    g7s, D = state["era2"]["g7"], state["day"]
    t = g7s["g11"]
    g7s.setdefault("before", {}).setdefault("G11", {})["g11"] = {
        "reached": dict(t["reached"]), "c": dict(t["c"]), "path": {k: dict(v) for k, v in t["path"].items()},
        "flows": {k: dict(v) for k, v in t["flows"].items()}, "made": g11.made_total(state), "mark": t.get("mark"),
        "fix": t.get("fix"), "trust_fix": t.get("trust_fix")}
    t["c"], t["path"] = {}, {}
    y = _y(state)
    g = g7s["g12"] = {"start": D, "pacts": {}, "pact_log": [], "relief": {}, "relief_log": [], "given": {},
                      "year_store": {str(y): _grain_have(state), str(y + 1): _grain_have(state)}, "paid": {}, "c1_years": [],
                      "hands_due": {}, "hands": {}, "census": {}, "pests": {}, "fallen": {}, "ev_seen": state["next_event"],
                      "fails": [], "path": {}, "ledger": [], "reached": {}, "c": {}, "city_half": None}
    return g


# ---------------- 苦しい村・受ける決まり・上限 ----------------

def struggling(o):
    """苦しい村: 地域の天気が悪い年か、蓄えが 1 人 100 つかみより少ない (g11._redeem と同じ)"""
    return o.get("bad") is not None or o.get("grain", 0) < o.get("people", 0) * LOW_GRAIN


def known(o):
    return o is not None and o.get("known") is not None and not o.get("gone") and o.get("people", 0) > 0


def hostile(state, o):
    D = state["day"]
    return era2._trust_hostile(state, o["id"], D - YEAR + 1, D)


def near_why(state, o):
    """約束を受けてくれそうな村か (受ける決まりの 1〜3)。受けそうなら None、ちがえばわけ"""
    if not known(o):
        return "村がまだよく知らない村なので" if o is not None and not o.get("gone") and o.get("people", 0) > 0 else "もうない村なので"
    if o.get("days", 9) > PACT_WALK:
        return f"歩いて {o['days']} 日と遠いので"
    if o.get("trust", 0.5) < era2.TRUST_FLOOR:
        return "村をまだ信じきれていないので"
    if hostile(state, o):
        return "この 1 年に村と争い (戦・求め・返されない貸し借り) があったので"
    return None


def candidates(state):
    """倉の約束を受けてくれそうな村 (受ける決まりの 1〜3 に合い、まだ約束のない村。番号の順)"""
    g = _g(state)
    return [o for o in _others()(state) if near_why(state, o) is None and not _active(g.get("pacts", {}).get(o["id"]))]


def needy(state):
    """いま苦しい、知っている村 (番号の順)"""
    return [o for o in _others()(state) if known(o) and struggling(o)]


def take_max(o):
    """相手が 1 年に出せる分の上限 (受ける決まりの 4)"""
    return {GRAIN: o["people"] * TAKE_GRAIN_PER, HANDS: [max(1, int(o["people"] * TAKE_HANDS_SHARE)), TAKE_HANDS_DAYS],
            OBS: int(o.get("obsidian", 0) * TAKE_OBS_SHARE)}


def value(goods):
    v = 0
    for k, n in goods.items():
        if k == HANDS:
            v += n[0] * n[1] * HAND_VALUE
        elif k == IRON:
            v += n * IRON_VALUE
        else:
            v += n * era2.VALUE.get(k, 0)
    return v


def accept_why(state, o, terms):
    """相手の村が倉の約束を受けないわけ (受けるなら None)。乱数なし。文は「<村> は、<わけ>、倉の約束を受けなかった」の形"""
    why = near_why(state, o)
    if why:
        return why
    give, take = terms.get("give") or {}, terms.get("take") or {}
    if not give:
        return "苦しい年に村が出す物 (give) が書いてなかったので"
    if not take:
        return "ふだんの年に出す物 (take) が書いてなかったので"
    mx = take_max(o)
    if GRAIN in take and take[GRAIN] > mx[GRAIN]:
        return f"1 年に草の種 {mx[GRAIN]} つかみより多くは出せないので"
    if HANDS in take and (take[HANDS][0] > mx[HANDS][0] or take[HANDS][1] > mx[HANDS][1]):
        return f"刈り手は {mx[HANDS][0]} 人が {mx[HANDS][1]} 日までしか出せないので"
    if OBS in take and take[OBS] > mx[OBS]:
        return "黒曜石をそれほど持っていないので" if mx[OBS] <= 0 else f"黒曜石は {mx[OBS]} 個までしか出せないので"
    if value(give) < GIVE_RATIO * value(take):
        return "苦しい年に村が出す分 (give) が、ふだんの年に出す分にくらべて少なく、得がないので"
    return None


def cap_left(state):
    """この暦の年に、村の倉からまだ出せる草の種 (つかみ) と、上限のわけ。1 年に年のはじめの倉の 1 割まで・出したあと今の人数で 300 日分を切らない"""
    g, y = _g(state), str(_y(state))
    base = g["year_store"].setdefault(y, _grain_have(state))
    a = int(base * CAP_SHARE) - g["given"].get(y, 0)
    kcal = sum(f["kcal"] for f in state["store"])
    b = int((kcal - CAP_DAYS * era2._need(state)) // era2.FOOD_KCAL[GRAIN])
    b = min(b, _grain_have(state))
    if b < a:
        return max(0, b), f"村の蓄えが、今の人数で {CAP_DAYS} 日分を切るので"
    return max(0, a), f"この年に倉から出せるのは、年のはじめの倉の 1 割 ({int(base * CAP_SHARE)} つかみ) までなので"


def _active(p):
    return bool(p) and p.get("status") == "続く"


# ---------------- 答えを読む ----------------

def _good(k):
    s = str(k)
    if "刈" in s:
        return HANDS
    if "鎌" in s:
        return IRON
    if "黒曜" in s:
        return OBS
    if "ヤギ" in s:
        return GOAT
    if "草" in s or "種" in s:
        return GRAIN
    return None


def _int(v):
    n = era2._num(v)
    return int(n) if n and n > 0 else 0


def _goods(v, allowed):
    """{物: 数} → 正しい形 (刈り手は [人, 日])。読めない物・0 は落とす"""
    if not isinstance(v, dict):
        return {}
    out = {}
    for k, n in v.items():
        good = _good(k)
        if good not in allowed:
            continue
        if good == HANDS:
            if isinstance(n, (list, tuple)) and len(n) >= 2:
                a, b = _int(n[0]), _int(n[1])
            else:
                a, b = _int(n), TAKE_HANDS_DAYS
            if a and b:
                out[HANDS] = [min(a, 1000), min(b, SEASON_DAYS)]
        else:
            m = _int(n)
            if m:
                out[good] = out.get(good, 0) + min(m, 10 ** 7)
    return {k: out[k] for k in sorted(out)}


def _oid(state, v):
    s = str(v or "").strip().strip("[]「」 ")
    if not s:
        return None
    for o in _others()(state):
        if s == o["id"] or s == o["name"] or s.upper() == o["id"]:
            return o["id"]
    n = era2._num(s)
    return f"N{int(n)}" if n and n == int(n) and _other(state, f"N{int(n)}") else None


def _float(v):
    try:
        return float(v) if v is not None and not isinstance(v, bool) else None
    except (TypeError, ValueError):
        return None


def _vtxt(txt, votes, ch):
    """票の文 (g7._tally) の中の答えの形 (JSON) を、村の人に読めることばにする"""
    for v in sorted(set(votes.values()), key=len, reverse=True):
        txt = txt.replace(v, "この中身" if v == ch else "やめる" if v == "end" else "ほかの中身")
    return txt


def _rows(v):
    if isinstance(v, dict):
        if "to" in v:
            return [v]
        return [dict(x, to=k) if isinstance(x, dict) else {"to": k, "end": x is False} for k, x in v.items()]
    return [x for x in v if isinstance(x, dict)] if isinstance(v, list) else []


def _pact_votes(state, a):
    out = {}
    for r in _rows(a.get("pact"))[:20]:
        oid = _oid(state, r.get("to"))
        if not oid:
            continue
        if r.get("end") is True or str(r.get("end")).strip() in ("やめる", "true"):
            out[oid] = "end"
            continue
        give, take = _goods(r.get("give"), GIVE_GOODS), _goods(r.get("take"), TAKE_GOODS)
        if give or take:
            out[oid] = json.dumps({"give": give, "take": take}, ensure_ascii=False, sort_keys=True)
    return out


def _help_votes(state, a):
    out = {}
    for r in _rows(a.get("help"))[:20]:
        oid = _oid(state, r.get("to"))
        if not oid:
            continue
        goods = _goods({k: v for k, v in r.items() if k not in ("to", "lend")}, GIVE_GOODS)
        if not goods:
            continue
        lend = _float(r.get("lend"))
        lend = round(min(0.5, lend), 2) if lend and lend > 0 else None
        out[oid] = json.dumps({"goods": goods, "lend": lend}, ensure_ascii=False, sort_keys=True)
    return out


def apply_answers(state, real):
    """集まりの答え (g7.apply_year から。era2.apply_answers の前): 倉の約束 (pact) → 倉から助ける (help)。相手の村ごとに、答えた人のいちばん多い手で決まる
    (g7._tally。決めない人は数えない。1 人でも決まる)。だれが決めたか (票) は出来事に残す"""
    import g7
    w = g7._vote_weights(state, real)
    pv, hv = {}, {}
    for n, a in real.items():
        if not isinstance(a, dict):
            continue
        for oid, v in _pact_votes(state, a).items():
            pv.setdefault(oid, {})[n] = v
        for oid, v in _help_votes(state, a).items():
            hv.setdefault(oid, {})[n] = v
    key = (lambda x: int(x[1:]))
    for oid in sorted(pv, key=key):
        ch, txt = g7._tally(state, pv[oid], w)
        if ch:
            by = sorted(n for n, v in pv[oid].items() if v == ch)
            _pact_answer(state, _other(state, oid), ch, _vtxt(txt, pv[oid], ch), by)
    for oid in sorted(hv, key=key):
        ch, txt = g7._tally(state, hv[oid], w)
        if ch:
            by = sorted(n for n, v in hv[oid].items() if v == ch)
            h = json.loads(ch)
            _help(state, _other(state, oid), h["goods"], h.get("lend"), _vtxt(txt, hv[oid], ch), by)


def _gw(goods):
    out = []
    for k, n in goods.items():
        if k == HANDS:
            out.append(f"刈り手 {n[0]} 人 × {n[1]} 日")
        elif k == IRON:
            out.append(f"{IRON} {n} 本")
        else:
            out.append(f"{k} {n} {era2.UNIT.get(k, 'つ')}")
    return "・".join(out) or "なし"


def _pact_answer(state, o, ch, txt, by):
    g, D = _g(state), state["day"]
    at = "集まりで"
    p = g["pacts"].get(o["id"]) if o else None
    if ch == "end":
        if _active(p):
            _end_pact(state, o, p, f"村が集まりで、{o['name']} との倉の約束をやめると決めた ({txt})", 0.0, "やめた")
        return
    terms = json.loads(ch)
    if _active(p) and p["give"] == terms["give"] and p["take"] == terms["take"]:
        return
    why = accept_why(state, o, terms)
    if why:
        _fail(state, by[0] if by else None, "約束", f"{o['name']} は、{why}、倉の約束を受けなかった (村が出す {_gw(terms['give'])} / 村に出す {_gw(terms['take'])}。{txt})")
        return
    if _active(p):
        p.update(give=terms["give"], take=terms["take"], changed=D, votes=txt, by=by)
        log(state, "倉", None, f"{at}、{o['name']} との倉の約束を変えた: {o['name']} が苦しい年に村が出す {_gw(terms['give'])} / "
            f"ふだんの年に {o['name']} が村に出す {_gw(terms['take'])} ({txt})", other=o["id"], pact=True)
    else:
        g["pacts"][o["id"]] = {"to": o["id"], "give": terms["give"], "take": terms["take"], "day": D, "votes": txt, "by": by,
                               "status": "続く", "paid": {}, "miss": 0, "end": None, "why": None, "written": None}
        log(state, "倉", None, f"{at}、{o['name']} と倉の約束を結んだ: {o['name']} が苦しい年は、村の倉から {_gw(terms['give'])} を出す。"
            f"ふだんの年は、{o['name']} が年の集まりの日に {_gw(terms['take'])} を村に出す ({txt}。書いたのは {'・'.join(by[:4])})",
            other=o["id"], pact=True)
        _reach(state, "F1", D, f"{o['name']} が倉の約束を受けた")
    g["pact_log"].append({"day": D, "other": o["id"], "what": "結ぶ", "give": terms["give"], "take": terms["take"], "votes": txt})
    g["pact_log"] = g["pact_log"][-80:]


def _end_pact(state, o, p, why, dt, how):
    g, D = _g(state), state["day"]
    p.update(status="切れた", end=D, why=why)
    if dt:
        o["trust"] = max(0.0, round(o["trust"] - dt, 2))
    log(state, "倉", None, why, other=o["id"], pact_end=how)
    g["pact_log"].append({"day": D, "other": o["id"], "what": how, "why": why})
    g["pact_log"] = g["pact_log"][-80:]


# ---------------- 倉から出す (助け・約束の助け) ----------------

def _give(state, o, goods, kind):
    """村の倉から o に出す (上限の中で)。戻り値: (出した物, 減らしたわけ (減らさなければ None))。助けとして数える (c2・F2)"""
    g, D = _g(state), state["day"]
    y = str(_y(state))
    want = dict(goods)
    cut = []
    if GRAIN in want:
        left, why = cap_left(state)
        if want[GRAIN] > left:
            cut.append(f"{why}、{o['name']} への草の種 {want[GRAIN]} つかみのうち {left} つかみだけ出した")
            want[GRAIN] = left
    if GOAT in want:
        have = era2._g6_have(state, "村", GOAT)
        if want[GOAT] > have:
            cut.append(f"村のヤギが足りず、{o['name']} へのヤギ {want[GOAT]} 頭のうち {have} 頭だけ出した")
            want[GOAT] = have
    tools = []
    if IRON in want:
        tools = g10.iron_tools(state)[-want[IRON]:] if want[IRON] > 0 else []
        if len(tools) < want[IRON]:
            cut.append(f"村の{IRON}が足りず、{o['name']} への {want[IRON]} 本のうち {len(tools)} 本だけ出した")
            want[IRON] = len(tools)
    ids = []
    gave = era2._g6_take(state, "村", {k: n for k, n in want.items() if k in (GRAIN, GOAT) and n > 0}, ids)
    era2._node_add(o, gave, 1)
    if tools:
        for t in tools:
            t["gone"], t["given"] = D, o["id"]
        gave[IRON] = len(tools)
        era2._node_add(o, {"鎌": len(tools)}, 1)
        if "sickles_f" in o:
            o["sickles_f"] = float(o["sickles_f"]) + len(tools)
    gave = {k: gave[k] for k in sorted(gave) if gave[k] > 0}
    if gave:
        g["given"][y] = g["given"].get(y, 0) + gave.get(GRAIN, 0)
        row = g["relief"].setdefault(y, {})
        row[o["id"]] = row.get(o["id"], 0) + value(gave)
        g["relief_log"].append({"day": D, "other": o["id"], "kind": kind, "goods": gave})
        g["relief_log"] = g["relief_log"][-120:]
        _reach(state, "F2", D, f"村の倉から {o['name']} に {_gw(gave)} を出した ({kind})")
        tot = sum(row.values())
        if len(row) >= C2_SETTLEMENTS and tot >= C2_AMOUNT:
            _cond(state, "c2", D, f"この年に村の倉から {len(row)} 集落へ、合わせて草の種 {tot} つかみ分を出した")
    return gave, ("。".join(cut) if cut else None), ids


def _help(state, o, goods, lend, txt, by):
    """倉から助ける (help): 苦しい村だけが受ける。上限で減らしたら、わけを残す"""
    D = state["day"]
    who = by[0] if by else None
    if not known(o):
        _fail(state, who, "助け", f"{o['name'] if o else 'その村'} は、村がよく知らない村 (かもうない村) なので、助けを受けとれなかった ({txt})")
        return
    if not struggling(o):
        _fail(state, who, "助け", f"{o['name']} は、いまは足りているので、村の倉からの助け ({_gw(goods)}) を受けなかった ({txt})")
        return
    gave, cut, ids = _give(state, o, goods, "貸し" if lend else "助け")
    if cut:
        _fail(state, who, "助け", cut)
    if not gave:
        return
    o["trust"] = min(1.0, round(o["trust"] + TRUST_KEEP, 2))
    mv = [era2._mv("村", -1, {k: n for k, n in gave.items() if k != IRON}, ids)]
    if lend and (gave.get(GRAIN) or gave.get(GOAT)):  # 貸す: 今の貸し借りの帳簿 (g6.debts) に、上乗せつきで残す (返しは今の決まりで来る)
        g6 = era2._g6(state)
        d = {"id": f"D{g6['next_debt']}", "other": o["id"], "lender": "村", "goods": {k: n for k, n in gave.items() if k in (GRAIN, GOAT)},
             "day": D, "due": D + YEAR, "proof": None, "mem": {"village": 1.0, "other": 1.0}, "status": "まだ", "end": None, "rate": lend}
        g6["next_debt"] += 1
        g6["debts"].append(d)
        log(state, "倉", None, f"集まりで、村の倉から {o['name']} に {_gw(gave)} を貸した [{d['id']}] (1 年のうちに、上乗せ {round(lend * 10, 1):g} 割をつけて返すと言った。{txt})",
            other=o["id"], debt=d["id"], help=True, moves=mv)
        if g11.on(state):
            g11.flow(state, o, "貸し")
    else:
        log(state, "倉", None, f"集まりで、村の倉から、いま苦しい {o['name']} に {_gw(gave)} を渡した ({txt}。書いたのは {'・'.join(by[:4])})",
            other=o["id"], help=True, moves=mv)


# ---------------- 年の終わり: 約束の出し入れと切れる決まり ----------------

def _settle(state):
    """年の終わり (年の集まりの日) の約束の出し入れ。乱数なし。相手が苦しければ村が give を出し (出せなければ村が約束を破った: すぐ切れる)、
    苦しくなければ相手が take を出す (出せない年が 2 年つづけば切れる)。刈り手は次の刈り入れの季節に来る"""
    g, D = _g(state), state["day"]
    y = str(_y(state))
    paid = g["paid"].setdefault(y, {})
    for oid in sorted(g["pacts"], key=lambda x: int(x[1:])):
        p = g["pacts"][oid]
        if not _active(p):
            continue
        o = _other(state, oid)
        if not known(o):
            _end_pact(state, o or {"id": oid, "name": oid, "trust": 0}, p, f"{oid} がなくなったので、倉の約束は終わった", 0.0, "なくなった")
            continue
        if struggling(o) and BAD_EXEMPT:
            gave, cut, ids = _give(state, o, p["give"], "約束")
            if cut or any(gave.get(k, 0) < n for k, n in p["give"].items()):
                paid[oid] = "村が出せなかった"
                p["paid"][y] = paid[oid]
                if gave:
                    log(state, "倉", None, f"{o['name']} が苦しい年なので、約束どおり村の倉から出そうとしたが、{_gw(gave)} だけだった",
                        other=oid, pact_give=True, moves=[era2._mv("村", -1, {k: n for k, n in gave.items() if k != IRON}, ids)])
                why = (cut or "村の倉に約束の物が足りなかったので") + f"。村が約束を破ったので、{o['name']} との倉の約束は切れ、{o['name']} は村を前ほど信じなくなった"
                _fail(state, None, "約束", why, log_it=False)
                _end_pact(state, o, p, why, TRUST_BROKE, "村が破った")
                continue
            paid[oid] = "苦しいので村が出した"
            p["paid"][y] = paid[oid]
            p["miss"] = 0
            o["trust"] = min(1.0, round(o["trust"] + TRUST_KEEP, 2))
            log(state, "倉", None, f"{o['name']} が苦しい年なので、約束どおり、村の倉から {_gw(gave)} を出した (この年は {o['name']} は出さなくてよい)",
                other=oid, pact_give=True, moves=[era2._mv("村", -1, {k: n for k, n in gave.items() if k != IRON}, ids)])
            continue
        why = None if not struggling(o) else f"{o['name']} は苦しい年で"
        if why is None:
            sup = era2._g6_supply(o)
            for k, n in p["take"].items():
                if k == GRAIN and sup.get(GRAIN, 0) < n:
                    why = f"{o['name']} の蓄えが少なく、約束の草の種 {n} つかみを出せず"
                elif k == OBS and o.get("obsidian", 0) < n:
                    why = f"{o['name']} に約束の黒曜石 {n} 個がなく"
                elif k == HANDS and o.get("people", 0) < n[0]:
                    why = f"{o['name']} に刈り手を出せる人が足りず"
                if why:
                    break
        if why:
            p["miss"] += 1
            paid[oid] = "出せなかった"
            p["paid"][y] = paid[oid]
            if p["miss"] >= MISS_LIMIT:
                txt = f"{why}、{p['miss']} 年つづけて約束の分を出せなかったので、{o['name']} との倉の約束は切れた" if MISS_LIMIT > 1 else \
                    f"{why}、約束の分を出せなかったので、{o['name']} との倉の約束は切れた"
                _fail(state, None, "約束", txt, log_it=False)
                _end_pact(state, o, p, txt, TRUST_MISS, "相手が出せなかった")
            else:
                _fail(state, None, "約束", f"{why}、この年は約束の分を出せなかった (つづけて {MISS_LIMIT} 年出せなければ、約束は切れる)")
            continue
        got = {}
        for k, n in p["take"].items():
            if k == GRAIN:
                o["grain"] = max(0, o["grain"] - n)
                era2._g6_put(state, "村", {GRAIN: n})
                got[GRAIN] = n
            elif k == OBS:
                o["obsidian"] = max(0, o["obsidian"] - n)
                era2._g6_put(state, "村", {OBS: n})
                got[OBS] = n
            elif k == HANDS:
                g["hands_due"][oid] = {"n": n[0], "left": n[1], "days": n[1], "day": D, "came": 0}
                got[HANDS] = n
        p["miss"] = 0
        paid[oid] = "出した"
        p["paid"][y] = paid[oid]
        o["trust"] = min(1.0, round(o["trust"] + TRUST_KEEP, 2))
        rest = {k: v for k, v in got.items() if k != HANDS}
        log(state, "倉", None, f"{o['name']} が、倉の約束どおり、" + (f"{_gw(rest)} を村に出した" if rest else "")
            + ("" if HANDS not in got else ("。" if rest else "") + f"刈り入れの季節に、刈り手 {got[HANDS][0]} 人が {got[HANDS][1]} 日まで来ると言った"),
            other=oid, pact_take=True, moves=[era2._mv("村", 1, rest)] if rest else [])
        if rest:
            _reach(state, "F4", D, f"{o['name']} が約束どおり {_gw(rest)} を出した")
    n = sum(1 for v in paid.values() if v == "出した")
    if n >= C1_MIN and int(y) not in g["c1_years"]:
        g["c1_years"].append(int(y))
        log(state, "目盛り", None, f"目盛り: G12 の条件 1 の年 ({y}年。倉の約束どおり村に出した集落 {n})", g="G12", c1_year=int(y))
        if len(g["c1_years"]) >= C1_TIMES:
            _cond(state, "c1", D, f"倉の約束どおり村に出した集落が {C1_MIN} つ以上の年が {len(g['c1_years'])} 回 ({'・'.join(map(str, g['c1_years']))}年)")


# ---------------- 刈り手 (era2._day の夕方のあと。刈り入れの季節だけ) ----------------

def hands_day(state):
    """刈り手: 約束の人数が来て、その日の終わりに、実ったまま刈られていない村の畑を刈る (1 人 1 日 150 つかみまで)。食べ物は村の蓄えから。
    刈り手は村の人にならない (家はない・答えない)。刈る畑がない日は来ない"""
    g = _g(state)
    if not g["hands_due"]:
        return
    e2, D = state["era2"], state["day"]
    for oid in sorted(g["hands_due"], key=lambda x: int(x[1:])):
        h = g["hands_due"][oid]
        ripe = [f for f in e2["fields"] if f["state"] == "実った" and f["yield"] > f["harvested"]]
        if h["left"] <= 0 or not ripe:
            continue
        want, got = h["n"] * HAND_REAP, 0
        for f in ripe:
            n = min(want - got, f["yield"] - f["harvested"])
            if n <= 0:
                continue
            f["harvested"] += n
            got += n
            st = era2._store_of(state, f.get("owner"))
            st.append({"kind": GRAIN, "kcal": n * era2.FOOD_KCAL[GRAIN], "day": D, "sown": True})
            if f["harvested"] >= f["yield"]:
                f["state"] = "刈った"
            if got >= want:
                break
        ate = era2._g6_take(state, "村", {GRAIN: h["n"] * HAND_EAT})
        h["left"] -= 1
        h["came"] += 1
        o = _other(state, oid)
        y = str(_y(state))
        row = g["hands"].setdefault(y, {"days": 0, "grain": 0, "ate": 0, "from": {}})
        row["days"] += h["n"]
        row["grain"] += got
        row["ate"] += ate.get(GRAIN, 0)
        row["from"][oid] = row["from"].get(oid, 0) + h["n"]
        log(state, "倉", None, f"{o['name'] if o else oid} の刈り手 {h['n']} 人が、村の畑で草の種 {got} つかみを刈った (村の蓄えから {ate.get(GRAIN, 0)} つかみを食べた)",
            other=oid, hands=h["n"], amount=got)
        _reach(state, "F4", D, f"{o['name'] if o else oid} の刈り手が来て、村の畑を刈った")


# ---------------- 帳をつける (仕事。g7.role_day から) ----------------

def acts(state):
    return [ACT_CENSUS] if g10.readers(state) else []


def can_census(state, name):
    return name in g10.readers(state)


def rest_why(state, name, act, j=None, with_=None, today=False):
    """「帳をつける」を「休む」に変えたわけ (村の人に見せる短い文)。G12 では入る日からいつも残す"""
    if act != ACT_CENSUS:
        return None
    if not g10.readers(state):
        return f"{name} は、村にいま字を読み書きできる人がいないので、帳をつけられず、休んだ"
    return (f"{name} は字を読み書きできないので、帳をつけられず、休んだ (字は、読める人のいる季節に、主な仕事を「字を習う」にすると習える。"
            f"帳をつけられるのは {'・'.join(g10.readers(state))})")


def _census_row(state, y):
    return _g(state)["census"].setdefault(str(y), {"houses": [], "people": {}, "store": None, "pacts": None, "days": 0, "by": {}, "done": None})


def census_day(state, p, t):
    """1 日: 読み書きできる人が、まだ書いていない家 (大人のいる家の名前の順) を 2 家ずつ書く。家を書き終えたら、村の倉の量、そのあと倉の約束 (あれば)。
    帳がそろった日を残す (c3 は年の終わりに見る)"""
    g, D = _g(state), state["day"]
    if not can_census(state, p["name"]):
        why = rest_why(state, p["name"], ACT_CENSUS)
        t.setdefault("events", []).append(log(state, "休む", p["name"], why, rest_why=ACT_CENSUS))
        if not any(f["who"] == p["name"] and f["what"] == ACT_CENSUS and f["day"] // SEASON_DAYS == D // SEASON_DAYS for f in g["fails"]):
            _fail(state, p["name"], ACT_CENSUS, why, log_it=False)
        return
    y = _y(state)
    row = _census_row(state, y)
    row["days"] += 1
    row["by"][p["name"]] = row["by"].get(p["name"], 0) + 1
    left, wrote = HOUSES_PER_DAY, []
    homes = era2._homes(state)
    for h in [h for h in homes if h not in row["houses"]][:left]:
        row["houses"].append(h)
        row["people"][h] = sum(1 for q in state["people"] if q["alive"] and q.get("household") == h)
        wrote.append(h)
        left -= 1
    if left and not [h for h in homes if h not in row["houses"]] and row["store"] is None:
        row["store"] = {"day": D, "grain": _grain_have(state), "days": era2.store_days(state)}
        wrote.append("村の倉")
        left -= 1
    pacts = [x for x in g["pacts"].values() if _active(x)]
    if left and row["store"] is not None and pacts and row["pacts"] is None:
        row["pacts"] = {"day": D, "n": len(pacts)}
        for x in pacts:
            x["written"] = D
        wrote.append("倉の約束")
        left -= 1
    if wrote:
        t.setdefault("events", []).append(log(state, ACT_CENSUS, p["name"], f"{p['name']} が、粘土の板に、{'・'.join(wrote)} を字で書いた"
                                              + (" (家の人の数・生まれた子・亡くなった人)" if any(w.endswith("の家") for w in wrote) else ""), census=wrote))
    else:
        t.setdefault("events", []).append(log(state, ACT_CENSUS, p["name"], f"{p['name']} が、この年の帳を読み返して確かめた", census=[]))
    _reach(state, "F3", D, f"{p['name']} が、家の人の数を字で書いた")
    if row["done"] is None and not [h for h in homes if h not in row["houses"]] and row["store"] is not None and (row["pacts"] is not None or not pacts):
        row["done"] = D
        log(state, ACT_CENSUS, None, f"この年の帳がそろった: 大人のいる家 {len(row['houses'])} の人の数・村の倉の量" + ("・倉の約束" if row["pacts"] else "")
            + f" (書いたのは {'・'.join(sorted(row['by']))}、のべ {row['days']} 日)", census_done=True)


def key_houses(state):
    """見本の家に必ず足す家 (G10 の直し ③ を広げる): 字を読み書きできる人のいる家"""
    rd = set(g10.readers(state))
    return sorted({p.get("household") for p in era2.adults(state) if p["name"] in rd and p.get("household")})


def _house_readers(state, name):
    p = next((q for q in era2.adults(state) if q["name"] == name), None)
    h = p.get("household") if p else None
    rd = set(g10.readers(state))
    return [q["name"] for q in era2.adults(state) if h and q.get("household") == h and q["name"] in rd]


# ---------------- 目盛り・季節の終わり ----------------

def _reach(state, f, day, why):
    g = _g(state)
    if f in g["reached"] or day is None:
        return
    g["reached"][f] = day
    log(state, "目盛り", None, f"目盛り: G12 の {f}「{FS[f]}」に届いた ({why})", g="G12", f=f)


def _cond(state, c, day, why):
    g = _g(state)
    if c not in g["c"]:
        g["c"][c] = day
        log(state, "目盛り", None, f"目盛り: G12 の条件 {c[1:]}「{CS[c]}」に届いた ({why})", g="G12", c=c)


def _fail(state, who, what, why, log_it=True):
    """選んだのにできなかったこと・受けなかった・減らした・切れた・休んだ。帳簿に残し、log_it なら出来事「倉」にも (お題の節に出す)"""
    g, D = _g(state), state["day"]
    g["fails"].append({"day": D, "year": D // YEAR, "who": who, "what": what, "why": why})
    g["fails"] = g["fails"][-80:]
    row = g["path"].get(str((D + 1) // YEAR))
    if row is not None:
        row["failed"] = row.get("failed", 0) + 1
    if log_it:
        log(state, "倉", who, why, g12_fail=what)


def _scan(state):
    """この季節の出来事から、虫に食べられた量と、刈らずに落ちた量を、暦の年ごとに足す (ならべて測る)"""
    g = _g(state)
    seen = g.get("ev_seen", 0)
    for e in state["events"]:
        if e["id"] < seen:
            continue
        y = str(e["day"] // YEAR)
        if e["type"] == "虫":
            g["pests"][y] = g["pests"].get(y, 0) + int((e.get("data") or {}).get("amount") or 0)
        elif e["type"] == "畑":
            m = FALLEN_RE.search(e.get("text", ""))
            if m:
                g["fallen"][y] = g["fallen"].get(y, 0) + int(m.group(1))
    g["ev_seen"] = state["next_event"]


def city_share(state):
    """都の大きさ (ならべて測る): 村の人 ÷ (村の人 + まわりの集落の人)"""
    mine = sum(1 for p in state["people"] if p["alive"])
    others = sum(o.get("people", 0) for o in _others()(state) if not o.get("gone"))
    return round(mine / max(1, mine + others), 3)


def season_end(state):
    """G12 の季節の終わり (g7.season_end。G11 の季節の終わりのあと): 虫と落ちた量を数える → 刈り入れの季節の終わりなら刈り手を帰す →
    年の終わりなら c3 (帳) → 帳簿の行 → 約束の出し入れ (c1・c2) → 次の年の倉の量を残す"""
    g, D = _g(state), state["day"]
    _scan(state)
    if era2.season(D) == "夏" and era2.season(D + 1) != "夏" and g["hands_due"]:
        for oid, h in sorted(g["hands_due"].items()):
            if h["left"] > 0:
                o = _other(state, oid)
                log(state, "倉", None, f"{o['name'] if o else oid} の刈り手は、刈る畑が残っていなかったので、{h['days']} 日のうち {h['came']} 日来て帰った",
                    other=oid, hands_end=True)
        g["hands_due"] = {}
    sh = city_share(state)
    if sh > 0.5 and g.get("city_half") is None:
        g["city_half"] = D
        log(state, "目盛り", None, f"目盛り: 村の人が、地域の人の半分をこえた ({round(sh * 100)}%。G12 の「ならべて測る」都の大きさ)", g="G12", city=sh)
    if (D + 1) % YEAR:
        return
    y = _y(state)
    if all((g["census"].get(str(y - i)) or {}).get("done") for i in range(C3_YEARS)):
        _cond(state, "c3", D, f"家の人の数と村の倉と倉の約束を字で書いた帳が、{C3_YEARS} 年つづけてそろった")
    _settle(state)
    rel = g["relief"].get(str(y)) or {}
    hd = g["hands"].get(str(y)) or {}
    g10s = state["era2"]["g7"]["g10"]
    cen = g["census"].get(str(y)) or {}
    reap = (g10s.get("reap") or {}).get(str(y)) or {}
    g["ledger"].append({"year": y, "day": D, "pacts": sum(1 for p in g["pacts"].values() if _active(p)),
                        "paid": dict(g["paid"].get(str(y)) or {}), "relief_settlements": len(rel), "relief_amount": sum(rel.values()),
                        "given_grain": g["given"].get(str(y), 0), "hands_days": hd.get("days", 0), "hands_grain": hd.get("grain", 0),
                        "reap_days": reap.get("all", 0), "census_houses": len(cen.get("houses", [])), "census_done": cen.get("done"),
                        "census_days": cen.get("days", 0), "readers": len(g10.readers(state)), "fails": sum(1 for f in g["fails"] if f["year"] == y),
                        "store": _grain_have(state), "store_days": era2.store_days(state), "pests": g["pests"].get(str(y), 0),
                        "fallen": g["fallen"].get(str(y), 0), "goats": len(state["era2"]["goats"]), "city": city_share(state),
                        "iron_given": sum(r["goods"].get(IRON, 0) for r in g["relief_log"] if r["day"] // YEAR == y),
                        "region": dict(g10s.get("region") or {}), "pact_ties": sum(1 for p in g["pacts"].values() if _active(p))})
    g["ledger"] = g["ledger"][-40:]
    g["year_store"][str(y + 1)] = _grain_have(state)
    g["year_store"] = {k: v for k, v in g["year_store"].items() if int(k) >= y - 3}


def reached(state, f):
    return bool(on(state) and _g(state)["reached"].get(f))


def done(state):
    return {c: c in _g(state)["c"] for c in CS}


def progress(state):
    """条件ごとの進み (段 × 1000 + 数。大きいほど進んだ。yardstick._stall が年の終わりに読む。G10 で「物差しが飽きる」をふさいだ形と同じ):
    c1: 段 (0 約束なし / 1 F1 / 2 F4) × 1000 + その年に約束どおり出した相手の数 × 100
    c2: 段 (0 / 1 F2) × 1000 + その年に助けた集落の数 × 100 + 出した量 (3 万に対する ‰ の 10 分の 1、100 まで)
    c3: 段 (0 / 1 F3) × 1000 + その年に書けた家の割合 (‰ の 10 分の 1) + つづいた年 × 100"""
    g = _g(state)
    y = _y(state)
    re_ = g["reached"]
    s1 = 2 if "F4" in re_ else 1 if "F1" in re_ else 0
    c1 = s1 * 1000 + sum(1 for v in (g["paid"].get(str(y)) or {}).values() if v == "出した") * 100
    rel = g["relief"].get(str(y)) or {}
    c2 = (1 if "F2" in re_ else 0) * 1000 + len(rel) * 100 + min(100, round(1000 * sum(rel.values()) / C2_AMOUNT / 10))
    cen = g["census"].get(str(y)) or {}
    homes = era2._homes(state)
    share = round(1000 * len([h for h in cen.get("houses", []) if h in homes]) / max(1, len(homes)) / 10)
    run = 0
    while (g["census"].get(str(y - run)) or {}).get("done"):
        run += 1
    c3 = (1 if "F3" in re_ else 0) * 1000 + min(100, share) + run * 100
    return {"c1": c1, "c2": c2, "c3": c3}


# ---------------- 道の見張り (答える人のうち、その道を自分で選べる人で数える。G12_design.md 6.) ----------------

def paths(state):
    """いまのお題に答える人 (era2.answerers) のうち、まだ届いていない条件ごとに、その道を自分で選べる人の名前と、c2 の道が要るか (need2)。
    c1: 受けてくれそうな村が 1 つ以上 (か、もう約束がある) なら、答える人みな (pact)。0 なら 0。
    c2: 苦しい村が 1 つ以上あり、倉からまだ出せるなら、答える人みな (help)。苦しい村がなければ need2 = False (2 年 0 の相談には数えない)。上限でもう出せなければ 0。
    c3: 答える人のうち、読み書きできる人と、読み書きできる人のいる家の代表。読める人が 0 人なら 0"""
    g = _g(state)
    ans = era2.answerers(state)
    has_pact = any(_active(p) for p in g["pacts"].values())
    nd = needy(state)
    out = {"c1": list(ans) if (candidates(state) or has_pact) else [],
           "c2": list(ans) if nd and cap_left(state)[0] > 0 else [],
           "c3": [n for n in ans if can_census(state, n) or _house_readers(state, n)] if g10.readers(state) else []}
    return {k: v for k, v in out.items() if k not in g["c"]}, bool(nd)


def _chose(state, real):
    """この集まりで、道を実際に選んだ答える人の数 (pact・help を書いた・「帳をつける」を選んだ)"""
    k = 0
    for n, a in real.items():
        if not isinstance(a, dict):
            continue
        txt = json.dumps({x: a.get(x) for x in ("year", "job", "family")}, ensure_ascii=False)
        if ACT_CENSUS in txt or _pact_votes(state, a) or _help_votes(state, a):
            k += 1
    return k


def count_paths(state, real):
    """集まりの答えを当てはめるとき (g7.apply_year から。答えを当てはめる前の、お題を書いたときの state で): この集まりの、道を選べた人・選んだ人を、
    その年 (この歩の季節の年。g11.count_paths と同じ (日 + 1) ÷ 120) に足す"""
    g = _g(state)
    y = str((state["day"] + 1) // YEAR)
    row = g["path"].setdefault(y, {"meetings": 0, "c1": 0, "c2": 0, "c3": 0, "need2": False, "no_need": 0, "chose": 0, "failed": 0, "who": {}})
    row["meetings"] += 1
    ps, need = paths(state)
    row["need2"] = row["need2"] or need
    row["no_need"] += not need
    for k, names in ps.items():
        row[k] += len(names)
        if names:
            row["who"][k] = sorted(set(row["who"].get(k, [])) | set(names))[:12]
    row["chose"] += _chose(state, real)


def fails_year(state, y):
    return [f for f in _g(state)["fails"] if f["year"] == y]


def _zero(row, k):
    if row and k == "c2" and not row.get("need2", True):
        return False  # 苦しい村のない年は、0 と別に数える (2 年 0 の相談には数えない)
    return (row or {}).get(k, 0) == 0


def path_consult(state, done_list):
    """年の終わり: まだ届いていない条件の道を、自分で選べる答える人が、G12 に入ってからのまる 2 年つづけて 0 人なら止めて相談 (仕組みのまちがい)。一度ずつ。
    第 6 部の 50 年 (168年120日目) の相談 (g7.consult_why) のあとは、5 年ごとに止めて相談 (本人の決め 2026-11-10 (お任せ))"""
    g, D = _g(state), state["day"]
    y = (D + 1) // YEAR - 1
    y0 = (g["start"] + 1) // YEAR
    for k in ("c1", "c2", "c3"):
        if k in g["c"]:
            continue
        ys = [y - i for i in range(PATH_YEARS)]
        if ys[-1] < y0:
            continue
        if all(_zero(g["path"].get(str(x)), k) for x in ys):
            if not any(c["why"] == f"g12_path_{k}" and c.get("year") == y for c in done_list):
                return {"why": f"g12_path_{k}", "year": y, "day": D,
                        "text": f"G12 の条件 {k[1:]} ({CS[k]}) の道を、自分で選べる答える人が {PATH_YEARS} 年つづけていなかった (仕組みのまちがいとして相談)"}
    if D > PART6_LIMIT_DAY and (D - PART6_LIMIT_DAY) % (LATER_YEARS * YEAR) == 0:
        why = f"g12_years_{D}"
        if not any(c["why"] == why for c in done_list):
            return {"why": why, "day": D, "text": f"G12: 第 6 部の 50 年の相談から {(D - PART6_LIMIT_DAY) // YEAR} 年たった (5 年ごとの相談)"}
    return None


def report_lines(state):
    """報告に書くこと (止めない): この年の「選んだのにできなかった」が 3 回以上・読める大人が 0 人・作れる人の家が 1 つだけ・
    選べた人はいるのに、だれも選ばなかった年が 3 年つづいた (G11 で 14 年気づかれなかった形)"""
    g, out = _g(state), []
    y = _y(state)
    f = fails_year(state, y)
    if len(f) >= FAIL_REPORT:
        out.append(f"この年に、選んだのにできなかったこと {len(f)} 回: " + " / ".join(x["why"][:60] for x in f[-5:]))
    if not g10.readers(state):
        out.append("字を読み書きできる大人が 0 人 (条件 3 の道が閉じている。帳は書けない)")
    kh = g11.key_houses(state)
    if len(kh) == 1:
        out.append(f"黒い金属を作れる人がいる家は {kh[0]} だけ")
    py = (state["day"] + 1) // YEAR
    rows = [g["path"].get(str(py - i)) for i in range(IDLE_YEARS)]
    if all(r and r.get("meetings") and (r["c1"] + r["c2"] + r["c3"]) > 0 and r.get("chose", 0) == 0 for r in rows):
        out.append(f"選べた答える人はいるのに、倉の約束・倉から助ける・帳をつけるを、だれも選ばなかった年が {IDLE_YEARS} 年つづいた")
    return out


def indicators(state):
    """G12 の目安 (era2.indicators に足す。【シ】)"""
    g = _g(state)
    y = str(_y(state))
    rel = g["relief"].get(y) or {}
    cen = g["census"].get(y) or {}
    return {"g12_c1_day": g["c"].get("c1"), "g12_c2_day": g["c"].get("c2"), "g12_c3_day": g["c"].get("c3"),
            "g12_pacts": sum(1 for p in g["pacts"].values() if _active(p)), "g12_paid": sum(1 for v in (g["paid"].get(y) or {}).values() if v == "出した"),
            "g12_c1_years": len(g["c1_years"]), "g12_relief_settlements": len(rel), "g12_relief_amount": sum(rel.values()),
            "g12_census_houses": len(cen.get("houses", [])), "g12_census_done": cen.get("done"), "g12_readers": len(g10.readers(state)),
            "g12_cap_left": cap_left(state)[0], "g12_fails": len(fails_year(state, int(y))), "g12_city": city_share(state),
            "g12_hands_days": (g["hands"].get(y) or {}).get("days", 0)}


# ---------------- お題 ----------------

def facts(state):
    """お題の決まりの文 (G12 から)。条件の数 (5 つ・3 万・2 年) と、受ける決まりの中の数 (5 倍・人 × 10 つかみ) は書かない"""
    return ("倉の約束: 年の集まりか秋の集まりの答えの pact に、近くの村と約束を書ける。give は、その村が苦しい年に村の倉から出す物 (草の種・ヤギ・黒い金属の鎌)、"
            "take は、ふだんの年にその村が村に出す物 (草の種・黒曜石・刈り手)。答えた人の中でいちばん多い中身に決まる (1 人でも決まる)。\n"
            "相手の村は、村を信じていて、出す分が小さく、苦しい年に助けてもらえる分が出す分よりずっと多いとき、約束を受ける。苦しい年は出さなくてよい。"
            "苦しくない年に 2 年つづけて出さなければ、約束は切れる。村が、相手の苦しい年に約束の物を出さなければ、約束はすぐ切れ、相手は村を信じなくなる。"
            "約束どおりの年は、相手は村を前より信じる。約束の物は、年の集まりの日に出し入れする。\n"
            "刈り手は、刈り入れの季節 (夏) に来て、その日の終わりに、実ったまま刈られていない村の畑を刈る (食べ物は村の蓄えから)。\n"
            "倉から助ける: 集まりの答えの help に、苦しい村と量を書くと、村の倉から渡す。苦しくない村は受けない。lend (上乗せ。例 0.1) を書くと、渡すかわりに貸す。\n"
            f"倉から出すのは、1 年に年のはじめの倉の 1 割まで。倉が、いまの人数で {CAP_DAYS} 日分より少なくなる分は出さない。出せなかった分は、わけと一緒に次のお題に出る。\n"
            f"帳: 字を読み書きできる人は、主な仕事を「{ACT_CENSUS}」にすると、1 日に {HOUSES_PER_DAY} 家ずつ、家の人の数を字で書ける。家を書き終えたら、倉の量と、倉の約束を書く。"
            "書いた約束の量は、覚えちがえない。帳をつけた年の次のお題には、家ごとの人の数と、1 年に虫やネズミに食べられた量が出る\n")


def _o_line(o):
    return f"[{o['id']}] {o['name']} ({o['people']} 人・歩いて {o['days']} 日)"


def text(state, p):
    """お題の節「## 倉と約束と帳」"""
    g, D = _g(state), state["day"]
    y = _y(state)
    left, _ = cap_left(state)
    rows = [f"- 村の倉: 草の種 {_grain_have(state)} つかみ (いまの人数で 約 {era2.store_days(state)} 日分)。"
            + (f"去年、虫やネズミに 約 {g['pests'][str(y - 1)]} つかみ食べられた。" if g["pests"].get(str(y - 1)) else "")
            + f"この年に倉から出せるのは、あと 草の種 {left} つかみ"]
    pf = prompt_fixed(state)
    if pf:
        rows.append("- いま苦しい村・倉の約束を受けてくれそうな村・あなたがこの集まりでできることは、下の「## いま」の答えの並びのすぐ前に書いた")
    else:
        nd = needy(state)
        rows.append("- いま苦しい村 (天気が悪いか、蓄えが少ない): " + ("・".join(f"[{o['id']}] {o['name']}" for o in nd) if nd else "いまはない"))
        cand = candidates(state)
        rows.append("- 倉の約束を受けてくれそうな村 (村を信じていて、歩いて 3 日以内、この 1 年に村と争っていない): "
                    + ("・".join(_o_line(o) + ("・いま苦しい" if struggling(o) else "") for o in cand) + " (出せる物: 草の種・刈り手。黒曜石を持つ村は黒曜石も)"
                       if cand else "いまはない"))
    act = [(oid, x) for oid, x in sorted(g["pacts"].items(), key=lambda kv: int(kv[0][1:])) if _active(x)]
    if act:
        for oid, x in act:
            o = _other(state, oid)
            last = sorted(x["paid"].items(), key=lambda kv: int(kv[0]))[-1:] if x["paid"] else []
            rows.append(f"- 倉の約束 [{oid}] {o['name'] if o else oid} ({x['day']} 日目から): 苦しい年に村が出す {_gw(x['give'])} / ふだんの年に村に出す {_gw(x['take'])}"
                        + (f"。{last[0][0]}年: {last[0][1]}" if last else "。まだ出し入れはない") + (" (帳に書いた)" if x.get("written") else ""))
    else:
        rows.append("- 倉の約束: まだない")
    ended = [x for x in g["pacts"].values() if x.get("status") == "切れた" and (x.get("end") or 0) >= D - YEAR]
    for x in ended[-3:]:
        rows.append(f"- 切れた倉の約束: {x['why']}")
    fl = g["fallen"]
    if fl:
        yy = max(fl, key=int)
        rows.append(f"- 刈らずに落ちた草の種: {yy}年に 約 {fl[yy]} つかみ (刈る手が足りなかった)")
    goats = len(state["era2"]["goats"])
    rows.append(f"- ヤギ: {goats} 頭 (村のヤギは、苦しい村に渡すこともできる)")
    rd = g10.readers(state)
    cen = g["census"].get(str(y)) or {}
    prev = g["census"].get(str(y - 1)) or {}
    rows.append(f"- 字を読み書きできる人: {'・'.join(rd) or 'いない'}" + (f" (主な仕事を「{ACT_CENSUS}」にできる)" if rd else " (帳をつけられる人がいない)")
                + (f"。帳: この年 {len(cen.get('houses', []))} / {len(era2._homes(state))} 家を書いた" + ("・そろった" if cen.get("done") else "") if cen else "。帳: この年はまだ書いていない"))
    if prev.get("done"):
        ppl = prev.get("people") or {}
        top = sorted(ppl.items(), key=lambda kv: (-kv[1], kv[0]))[:12]
        rows.append(f"- 去年の帳 ({y - 1}年): 家ごとの人の数 " + "・".join(f"{h} {n} 人" for h, n in top) + (f" ほか {len(ppl) - 12} 家" if len(ppl) > 12 else "")
                    + f" / 1 年に虫やネズミに食べられた草の種 約 {g['pests'].get(str(y - 1), 0)} つかみ")
    else:
        rows.append("- 去年の帳: ない (家ごとの人の数と、虫やネズミに食べられた量は、わからない)")
    sm = g11.smiths(state)
    if sm:
        rows.append(f"- 黒い金属の鎌を作れる人: {'・'.join(sm)} ({'・'.join(g11.key_houses(state))})")
    f = [x for x in g["fails"] if x["year"] >= y - 1][-4:]
    if f:
        rows.append("- 倉と約束と帳で、できなかったこと: " + " / ".join(x["why"] for x in f))
    if not pf:
        rows += _mine(state, p)
    return "\n## 倉と約束と帳\n" + "\n".join(rows) + "\n"


def _mine(state, p):
    """その人だけの行 (入る日から。G10・G11 の学び (a)): 読める人・読める人のいる家の代表・作れる人の家の代表・答える人みな"""
    if not p:
        return []
    out = []
    if can_census(state, p["name"]):
        out.append(f"- あなた ({p['name']}) は字を読み書きできるので、主な仕事を「{ACT_CENSUS}」にできる (1 日に {HOUSES_PER_DAY} 家)")
    fam = [n for n in _house_readers(state, p["name"]) if n != p["name"]]
    if fam:
        out.append(f"- あなたの家の {'・'.join(fam)} は帳をつけられる (family で「{ACT_CENSUS}」にできる)")
    fs = [n for n in g11._house_smiths(state, p["name"])]
    if fs:
        out.append(f"- あなたの家の {'・'.join(fs)} たちが作った黒い金属の鎌は、倉の約束や助けの品 (give・help の「黒い金属の鎌」) にできる")
    if p["name"] in era2.answerers(state):
        out.append("- あなたも pact と help に書ける。1 人の答えでも決まる")
    return out


def _pact_example(o):
    """o が受ける形の例 (受ける決まり 1〜5 に合う。数は書かずに、例の量だけ見せる)"""
    take = max(10, min(o["people"] * TAKE_GRAIN_PER, o["people"] * TAKE_GRAIN_PER // 20 * 10))
    return {"give": {GRAIN: take * 10}, "take": {GRAIN: take}}


def _js(x):
    return json.dumps(x, ensure_ascii=False)


def progress_lines(state):
    """3 つの進み (1 行ずつ。村の人が見て分かる数だけ)"""
    g, y = _g(state), _y(state)
    out = []
    if "c1" in g["c"]:
        out.append(f"- 倉の約束の輪: 届いた ({g['c']['c1']} 日目)")
    else:
        ys = sorted((k for k, v in g["paid"].items() if v), key=int)
        last = ys[-1] if ys else None
        n = sum(1 for v in (g["paid"].get(last) or {}).values() if v == "出した") if last else 0
        out.append(f"- 倉の約束の輪: 続いている倉の約束 {sum(1 for x in g['pacts'].values() if _active(x))}。"
                   + (f"{last}年に約束どおり村に出した村 {n}" if last else "約束どおり村に出した村は、まだない")
                   + f"。1 年に {C1_MIN} つ以上の村が約束どおり出した年: {len(g['c1_years'])} 回 ({C1_TIMES} 回で届く)")
    if "c2" in g["c"]:
        out.append(f"- 倉から地域を養う: 届いた ({g['c']['c2']} 日目)")
    else:
        rel = g["relief"].get(str(y)) or {}
        out.append(f"- 倉から地域を養う: {y}年に村の倉から出した村 {len(rel)}・合わせて 草の種 {sum(rel.values())} つかみ分"
                   f" (1 年に {C2_SETTLEMENTS} つ以上の村へ、合わせて 草の種 {C2_AMOUNT} つかみ分以上を出すと届く)")
    if "c3" in g["c"]:
        out.append(f"- 人と倉の帳: 届いた ({g['c']['c3']} 日目)")
    else:
        cen = g["census"].get(str(y)) or {}
        run = 0
        while (g["census"].get(str(y - run)) or {}).get("done"):
            run += 1
        out.append(f"- 人と倉の帳: {y}年の帳は {len(cen.get('houses', []))} / {len(era2._homes(state))} 家" + ("・そろった" if cen.get("done") else "")
                   + f"。帳がそろった年が、いま {run} 年つづいている ({C3_YEARS} 年つづくと届く)")
    return out


def prompt_block(state, p):
    """「## いま」の答えの並びのすぐ前に置く短い節 (G12_PROMPT_FROM から。prompt_fixed のときだけ。前は空の文字)。
    その人がこの集まりで書けること (pact・help)・その人の家で「帳をつける」にできる人と、そうするとどうなるか・3 つの進み。せかす言葉は書かない"""
    if not p or not prompt_fixed(state):
        return ""
    g = _g(state)
    left, why = cap_left(state)
    rows = [BLOCK_HEAD.replace("あなたが", f"あなた ({p['name']}) が", 1)]
    cand = candidates(state)
    if cand:
        ex = next((o for o in cand if not struggling(o)), cand[0])
        rows.append(f"- 倉の約束 (pact): いま受けてくれそうな村は {len(cand)} ("
                    + "・".join(_o_line(o) + ("・いま苦しい" if struggling(o) else "") for o in cand) + ")。"
                    "give は相手が苦しい年に村の倉から出す物、take はふだんの年に相手が村に出す物 (草の種・刈り手。黒曜石を持つ村は黒曜石も)。"
                    "相手が出す分が小さく、苦しい年に村が出す分がずっと多いと受ける。"
                    f"例: \"pact\": [{_js({'to': ex['id'], **_pact_example(ex)})}]")
    else:
        rows.append("- 倉の約束 (pact): いま受けてくれそうな村はない (村を信じていて、歩いて 3 日以内で、この 1 年に村と争っていない村が受ける)")
    act = [oid for oid, x in sorted(g["pacts"].items(), key=lambda kv: int(kv[0][1:])) if _active(x)]
    if act:
        rows.append(f"- 続いている倉の約束: {'・'.join(act)} (中身は上の「## 倉と約束と帳」。やめるなら {{\"to\": 番号, \"end\": true}})")
    nd = needy(state)
    if nd and left > 0:
        rows.append("- 倉から助ける (help): いま苦しい村は " + "・".join(f"[{o['id']}] {o['name']} ({o['people']} 人)" for o in nd)
                    + f"。この年に倉から出せるのは、あと 草の種 {left} つかみ。苦しい村だけが受ける。"
                    f"例: \"help\": [{_js({'to': nd[0]['id'], GRAIN: min(2000, left)})}] (貸すなら \"lend\": 0.1 をそえる)")
    elif nd:
        rows.append(f"- 倉から助ける (help): いま苦しい村はあるが、この年は倉からもう出せない ({why})")
    else:
        rows.append("- 倉から助ける (help): いま苦しい村はない (苦しくない村は受けない)")
    rd = g10.readers(state)
    fam = _house_readers(state, p["name"])
    homes = len(era2._homes(state))
    days = -(-(homes + 1 + (1 if act else 0)) // HOUSES_PER_DAY)
    gain = (f"1 人なら 1 日に {HOUSES_PER_DAY} 家ずつ書き、大人のいる {homes} 家と倉{'と約束' if act else ''}を、のべ 約 {days} 日で書き終える (帳がそろう)。"
            "帳がそろった年の次のお題には、家ごとの人の数と、1 年に虫やネズミに食べられた量が出る。")
    if fam:
        me, others = p["name"] in fam, [n for n in fam if n != p["name"]]
        who = (f"あなた ({p['name']})" + (f" と、あなたの家の {'・'.join(others)}" if others else "")) if me else f"あなたの家の {'・'.join(others)}"
        how = "・".join((["あなたは job"] if me else []) + ([f"{'・'.join(others)} は family"] if others else []))
        rows.append(f"- 帳: {who} は字を読み書きできるので、季節の主な仕事を「{ACT_CENSUS}」にできる ({how} に書く)。" + gain)
    elif rd:
        rows.append(f"- 帳: あなたの家には字を読み書きできる人がいない。「{ACT_CENSUS}」にできるのは {'・'.join(rd)} (その家の代表が決める)。" + gain)
    else:
        rows.append(f"- 帳: いま村に字を読み書きできる人がいないので、「{ACT_CENSUS}」にできる人はいない")
    fs = g11._house_smiths(state, p["name"])
    if fs:
        rows.append(f"- あなたの家の {'・'.join(fs)} たちが作った黒い金属の鎌は、give・help の「黒い金属の鎌」にできる")
    rows.append("- pact と help は、答えた人の中でいちばん多い中身に決まる (1 人の答えでも決まる)。書かなくてもよい (\"pact\": []・\"help\": [])")
    rows.append("いまの進み (村の倉と約束と帳):")
    rows += progress_lines(state)
    return "\n".join(rows) + "\n"


def feel_note(state, p):
    """気持ちだけのお題の行 (代表でない人は仕事を決めないので、代表に伝えられることだけ)"""
    out = []
    if can_census(state, p["name"]):
        out.append(f"- あなたは字を読み書きできる。家の代表が、あなたの仕事を「{ACT_CENSUS}」にすれば、あなたは家の人の数と倉の量を字で書ける")
    out.append("- 村の倉から苦しい村を助けることや、近くの村と倉の約束を結ぶことを、家の代表に伝えられる")
    return "\n" + "\n".join(out)


def field_rows(state, year=False):
    """答えの欄の説明 (g7._field_rows に足す)"""
    rows = []
    if g10.readers(state):
        rows.append(f"   帳: 主な仕事を「{ACT_CENSUS}」にできるのは、字を読み書きできる人")
    take = 100 if prompt_fixed(state) else 200  # 直しのあと: 前の例 (北の村13 は 18 人。1 年に出せる草の種は 180 つかみまで) は、そのまま書くと受けない形だった
    rows.append('   倉の約束: pact に [{"to": "N13", "give": {"草の種": 3000}, "take": {"草の種": ' + str(take) + '}}] のように書く (take には {"刈り手": [人, 日]}・{"黒曜石": 個} も書ける。'
                'やめるなら {"to": "N13", "end": true}。決めないなら [])')
    rows.append('   倉から助ける: help に [{"to": "N13", "草の種": 2000}] のように書く ("ヤギ"・"黒い金属の鎌" も書ける。貸すなら "lend": 0.1 をそえる。決めないなら [])')
    return rows


def fields_json(state):
    return ' "pact": [], "help": [],'


def bad_words(s):
    return [w for w in WORDS if w in s]
