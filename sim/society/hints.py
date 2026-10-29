"""よその便り (史実のヒント。G7 から。docs/society_phase/G7_design.md 4.C。2026-10-16 本人の E1〜E3「つながりで変わる・5 つの運び手・種類で分ける」)

- 作る側の呼び名は「史実のヒント」、村の中の呼び名は「よその便り」(出来事の種類)。便りは「よそでは今こうしている」という話・もの・人で、
  「こうなる」「こうせよ」とは言わない。使うか、聞き流すか、断るかは村が決める (罰はない。4.C.9)。便りは何も起こさない (国・戦・病を起こさない)。
  開くのは、技術の札の「試す」(前提がそろうとき)・ものの申し出・人の受け入れだけで、どれも村の答えがなければ何も変わらない
- 乱数はすべて塩 47 (era2.HINT_SALT) の列から。1 日に 1 回だけ作り、決まった順で引く (4.C.7): 年の最後の日なら次の年の分 (村 → 集落の番号の順) →
  この季節の戦の捕らえた職人 (戦の番号の順) → この季節に届く便り (Y 番号の順)。きっかけは塩 67 (era2.CHANCE_SALT)。G7 に入る前は列を作らない
- 帳簿 (g7.hints.ledger) は【シ】と同じ扱い (お題にもダッシュボードにも出さない)。出来事「よその便り」(【村】) の文には、話の中身を入れない
  (中身は data と、聞いた人の heard・「## よその便り」にだけ。4.C.8)
- 世界の計算は、話の中身 (札の words・text) を読まない。見るのは出来事の番号と、だれの話かだけ (4.C.6)
- 数はみな【仮定】(4.C)
"""
import hashlib
import json
import math
import random
from pathlib import Path

import era2
import world
from world import log, season

CARDS = Path(__file__).parent / "hint_cards.json"
CARDS_G9 = Path(__file__).parent / "hint_cards_g9.json"  # G9 (遠くとの商い) に入る日に足す札 (2026-10-29 本人の決め)。G9 に入るまでは引かない
FAR = "遠く"  # 遠くの商人の「来た所」(G9 から。地図の外。集落の番号ではない)
HINT_CAP = 3  # 1 年に届く便りは 3 通まで (捕らえた職人は数えない。4.C.3)
HINT_REPEAT = 3  # 同じ札が来るのは、受けとる所ごとに 3 回まで (4.C.5)
STAGE_MIX = (0.6, 0.3, 0.1)  # 段: 今の G 60%・次の G 30%・2 つ以上先 10% (先の段どうしは等しく。E5)
STAGES = ("G7", "G8", "G9", "G10", "G11", "G12", "G13", "G14")
CARRIERS = ("旅人", "商人", "教えを説く人", "よそから来た人", "捕らえた職人")  # 本人の E2「5 つの運び手」(夢は入れない)
LAM_TRAVELLER, LAM_PREACHER, LAM_PREACHER_HARD = 0.2, 0.1, 0.2  # λ の項 (4.C.3): 旅人・教えを説く人 (前の年が悪い年か借りの年なら 0.2)
LAM_MERCHANT, LAM_FAR, LAM_JOINED = 0.15, 0.1, 0.3  # 交換した集落ごと・遠くの商人 (G9 から。G8 までは 0。もとの計画の G8 = 今の G9)・受け入れた組ごと
FIELD_POOR = 6  # 村の悪い年 (c): 夏の畑の比が 6 より小さい
HEARD_YEARS, HEARD_MAX = 3, 3  # お題に出すのは 3 年以内・3 通まで。3 年だれも使わなければ「忘れられた」(4.C.9)
TRY_SKILL0, TRY_STEP, TRY_TEACH_STEP, TEACH_AT = 0.1, 0.02, 0.04, 0.6  # 試す (4.C.10): 腕は 0.1 から 1 日 +0.02、教える人 (腕 0.6 以上) と同じ日なら +0.04
TRY_DECAY_YEARS = 3  # 3 年だれも試さなければ、進みが半分になる (4.C.9)
TEACH_SKILL = 0.8  # 「人」の札の人は、教える腕 0.8 で加わる (4.C.2)
ROGERS_RULE = 11  # まわりの集落が決まりで試すのは、rogers の合計が 11 以上の札だけ (4.C.12)
CAPTURE_P = 0.5  # 戦に負けたら、見込み 0.5 で、村でいちばん腕の高い大人が連れて行かれる (4.C.4)
GROUP_AGE = (18, 45)  # 便りの群れの大人の年【仮定】
THING_WANT = {"草の種": 100}  # 商人が「もの」を出すときにほしがる物【仮定】(値うちの数え方は変えない。銀の重さは G8 から。4.C.13)
FORBIDDEN = ("王", "お金", "国", "神", "銀", "青銅", "法", "税", "預言者", "奴隷", "都市")  # 村の人に見せる文に入れない言葉 (2.)
TEXT_MAX = 220
CARRIER_WORD = {"旅人": "遠くから来た旅の人", "商人": "{o} から来た運ぶ人", "教えを説く人": "遠くから来た年寄り", "よそから来た人": "よそから来た人",
                "捕らえた職人": "連れて来られた職人"}
CRAFT_ACT = {"土器": "土器づくり", "道具": "道具づくり"}  # 「人」の札の teach (腕の名前) → 仕事
MERCHANT_MET = ("交換に行く",)
FAR_WORD = "遠くの町から来た運ぶ人"  # G9: 遠くの商人 (地図の外から)


def _g9m():
    """G9 (遠くとの商い) の仕組み (g9.py)。G9 に入ってからだけ読みこむ"""
    import g9
    return g9


# ---------------- 札の表 (4.C.1) ----------------

def _g9_on(state):
    return bool(state) and "g9" in ((state.get("era2") or {}).get("g7") or {})


def cards_sha(state=None):
    """札の表のファイルのハッシュ (G7 に入る日に g7.hints.cards_sha に残す。ちがうまま season を動かすと止まる)。
    G9 に入ったあと (state に g7.g9 がある) は、hint_cards.json と hint_cards_g9.json をつないだもののハッシュ (G8 までは前のまま)"""
    if _g9_on(state):
        return hashlib.sha256(CARDS.read_bytes() + b"\n" + CARDS_G9.read_bytes()).hexdigest()
    return hashlib.sha256(CARDS.read_bytes()).hexdigest()


_CACHE = {}


def cards():
    """札の表 {番号: 札} (ファイルが変われば読みなおす)"""
    sha = cards_sha() + (hashlib.sha256(CARDS_G9.read_bytes()).hexdigest() if CARDS_G9.exists() else "")
    if _CACHE.get("sha") != sha:
        data = json.loads(CARDS.read_text(encoding="utf-8"))
        extra = json.loads(CARDS_G9.read_text(encoding="utf-8"))["cards"] if CARDS_G9.exists() else []  # G9 の札 (g9: true。G9 に入るまでは _cand で引かない)
        _CACHE.update(sha=sha, cards={c["id"]: c for c in data["cards"] + extra})
    return _CACHE["cards"]


def check_cards(cs=None):
    """札の文の検査 (禁じた言葉がない・220 字まで・出典の印がある・種類と運び手が決まりの中)。戻り値: まちがいの並び"""
    bad = []
    for c in (cs or cards()).values():
        for k in ("text", "name"):
            for w in FORBIDDEN:
                if w in c[k]:
                    bad.append(f"{c['id']} の {k} に「{w}」")
        if c.get("chance") and any(w in c["chance"]["text"] for w in FORBIDDEN):
            bad.append(f"{c['id']} のきっかけの文に禁じた言葉")
        if len(c["text"]) > TEXT_MAX:
            bad.append(f"{c['id']} の文が {len(c['text'])} 字")
        if c["kind"] not in ("制度", "技術", "もの", "人", "教え") or not c["carrier"] or set(c["carrier"]) - set(CARRIERS):
            bad.append(f"{c['id']} の種類か運び手")
        if c["stage"] not in STAGES:
            bad.append(f"{c['id']} の段")
        if not c.get("src") or not all(s.get("m", "").startswith("【") for s in c["src"]):
            bad.append(f"{c['id']} の出典の印")
        if c["kind"] == "技術" and not c.get("try"):
            bad.append(f"{c['id']} (技術) に try がない")
    return bad


def _h(state):
    return state["era2"]["g7"]["hints"]


def on(state):
    return "hints" in (state["era2"].get("g7") or {}) and world.G7_PARTS.get("hints", True)


# ---------------- 来る数 λ (4.C.3) ----------------

def _window(state):
    D = state["day"]
    return D + 1 - era2.YEAR, D


def _joined_groups(state, lo, hi):
    """前の年に受け入れた組 (出来事「加わる」のうち「よそから来た 」で始まるもの。便りの群れ (data の hint) は数えない)"""
    return sum(1 for e in state["events"] if e["type"] == "加わる" and lo <= e["day"] <= hi and e["text"].startswith("よそから来た ")
               and not (e.get("data") or {}).get("hint"))


def _bad_year(state, lo, hi):
    """前の年が村の悪い年か: (a) 地域の天気で村が悪い年 (b) 「蓄えが尽きる」があった (c) 夏の畑の比 (era2._field_season と同じ式) が 6 より小さい"""
    y = hi // era2.YEAR
    reg = state["era2"]["g7"].get("region") or {}
    a = any(w["year"] == y and "V0" in w.get("bad", []) for w in reg.get("weather_log", []))
    b = any(e["type"] == "蓄えが尽きる" and lo <= e["day"] <= hi for e in state["events"])
    ratio = random.Random(state["seed"] * 991 + y).triangular(3, 15, 8) * (0.5 if a else 1.0)
    return a or b or ratio < FIELD_POOR


def _debt_year(state, lo, hi):
    """前の年が借りの年か: 期日が来たのに返されていない貸し借りがある (利子つきもふくむ)"""
    for d in (state["era2"].get("g6") or {}).get("debts", []):
        if d["status"] == "まだ" and lo <= d["due"] <= hi:
            return True
        if d["status"] == "返されない" and d.get("end") is not None and lo <= d["end"] <= hi:
            return True
    return False


def far_weight(state):
    """遠くの商人の重み (G9 から)。step.py far_rate で残した重み (g7.g9.far_rate の最後の行。本人の決め 2026-10-29「来る見込みを 5 割に」) があればそれ、
    なければ LAM_FAR (0.1)。切り替えは state に残すので、切り替えの前の日は、前と 1 バイトも同じに進む"""
    fr = state["era2"]["g7"]["g9"].get("far_rate")
    return fr[-1]["rate"] if fr else LAM_FAR


def far_topup(state, extra):
    """step.py far_rate を、次の年の便りをもう引いた日 (年の終わりの日) に入れたとき: 引いた年の分に、遠くの商人だけを、重みの差 extra で引き足す
    (ポワソンの和: 0.1 で引いた数 + 差で引いた数 = 新しい重みで引いた数。村の便りは 1 年に 3 通まで (HINT_CAP) のまま)。
    乱数は、日と種からつくる別の列 (塩 47 の列にはさわらない)。戻り値: λ の行 (足した行がなければ n = 0)"""
    h, D = _h(state), state["day"]
    rng = random.Random(f"G9|{state['seed']}|far_rate|{D}")
    have = sum(x["n"] for x in h["lam"] if x["day"] == D and x["to"] == "V0")
    n_raw = poisson(rng, extra)
    n = max(0, min(HINT_CAP - have, n_raw))
    row = {"day": D, "to": "V0", "lam": round(extra, 6), "n": n, "terms": [["商人", round(extra, 6), FAR]], "far_rate": True}
    h["lam"].append(row)
    dues, now = _seasons_left(D), _stage_now(state)
    for _ in range(n):
        si = rng.randrange(len(dues))
        stage, us = _pick_stage(rng, now)
        card, got = _pick_card(state, rng, "V0", stage, now, "商人")
        y = f"Y{h['next']}"
        h["next"] += 1
        r = {"y": y, "card": card, "carrier": "商人", "to": "V0", "from": FAR, "drawn": D, "due": dues[si], "stage": STAGES[stage],
             "stage_got": STAGES[got] if got is not None else None, "u": [None, round(us, 6)], "status": "待つ" if card else "空振り",
             "delivered": None, "listeners": [], "outcome": [], "far_rate": True}
        if not card:
            r["why"] = "引いた段と運び手の札がない"
        else:
            h["seen"].setdefault("V0", {})[card] = h["seen"].get("V0", {}).get(card, 0) + 1
            h["plan"].append(y)
        h["ledger"].append(r)
    return row


def terms(state, rid):
    """λ の項の並び [(運び手, 重み, 商人の来た所)] (受けとる所 rid: "V0" か集落の番号)。前の年 [day+1−120, day] の数で決める"""
    lo, hi = _window(state)
    others = sorted((o for o in (state["era2"].get("g6") or {}).get("others", []) if not o.get("gone")), key=lambda o: int(o["id"][1:]))
    out = [("旅人", LAM_TRAVELLER, None)]
    if rid == "V0":
        hard = _bad_year(state, lo, hi) or _debt_year(state, lo, hi)
        out.append(("教えを説く人", LAM_PREACHER_HARD if hard else LAM_PREACHER, None))
        for o in others:
            if any(lo <= c <= hi for c in o.get("contacts", [])):
                out.append(("商人", LAM_MERCHANT, o["id"]))
        # 遠くの商人 (LAM_FAR) は G9 から (G8 までは 0)。2026-10-29 本人の決め「交換しなくても来る」: 前の年に村が交換をしなくても来る
        # (前は計画 2.(h) のとおり、交換した次の年だけ (g9.traded) だった。重みは 0.1 のまま)
        # 重みは、本人の決め 2026-10-29「来る見込みを 5 割に」から、step.py far_rate で state に残した重み (g7.g9.far_rate。なければ LAM_FAR = 0.1)
        if _g9_on(state):
            out.append(("商人", far_weight(state), FAR))
        out += [("よそから来た人", LAM_JOINED, None)] * _joined_groups(state, lo, hi)
    else:
        o = next((x for x in others if x["id"] == rid), None)
        hard = o is not None and o.get("bad") is not None and o["bad"] >= lo - 1
        out.append(("教えを説く人", LAM_PREACHER_HARD if hard else LAM_PREACHER, None))
        if o is not None and any(lo <= c <= hi for c in o.get("contacts", [])):  # 「交換した集落」には川辺の村も数える (4.C.12)
            out.append(("商人", LAM_MERCHANT, "V0"))
    return out


def poisson(rng, lam):
    """ポワソン分布 (Knuth のやり方。上限なし。上限 3 通は呼んだ側)"""
    L, k, p = math.exp(-lam), 0, 1.0
    while True:
        p *= rng.random()
        if p <= L:
            return k
        k += 1


def _stage_now(state):
    """今の段。札の段 (hint_cards.json の stage) は、もとの計画の G の番号のまま。2026-10-25 に G8 (外からの押し) を足して、もとの G8 から後が
    1 つずつずれたので、G8 は G7 の札の段、G9 はもとの G8 の札の段 … と読む"""
    era = state.get("era")
    if era in STAGES and STAGES.index(era) >= 1:
        era = STAGES[STAGES.index(era) - 1]
    elif era == "G15":
        era = "G14"
    return STAGES.index(era) if era in STAGES else 0


def _pick_stage(rng, now):
    """段の番号 (STAGES の何番目か)。今 60%・次 30%・2 つ以上先 10% (先の段どうしは等しく)"""
    u = rng.random()
    if u < STAGE_MIX[0]:
        return now, u
    if u < STAGE_MIX[0] + STAGE_MIX[1] or now + 2 >= len(STAGES):
        return min(now + 1, len(STAGES) - 1), u
    return now + 2 + rng.randrange(len(STAGES) - now - 2), u


def _cand(state, rid, stage, carrier):
    h, cs = _h(state), cards()
    seen, used = (h["seen"].get(rid) or {}), set(h["used"].get(rid) or [])
    g9 = _g9_on(state)  # G9 の札 (g9: true) は G9 に入ってから (G8 までは前と同じ札から引く)
    return sorted(c for c, x in cs.items() if x["stage"] == STAGES[stage] and carrier in x["carrier"] and c not in used and seen.get(c, 0) < HINT_REPEAT
                  and (g9 or not x.get("g9")))


def _pick_card(state, rng, rid, stage, now, carrier):
    """引いた段に、引いた運び手の札がないとき: 今の段 → 次の段 → 前の段 → 先の段 の順に、同じ運び手の札をさがす。なければ None (空振り)"""
    order = [stage, now, now + 1, now - 1] + list(range(now + 2, len(STAGES)))
    for s in order:
        if 0 <= s < len(STAGES):
            c = _cand(state, rid, s, carrier)
            if c:
                return rng.choice(c), s
    return None, None


def _seasons_left(D):
    """D の次の日から年の終わりまでの季節の終わりの日 (短い年なら残りの季節だけ)"""
    first = (D + 1) // era2.SEASON_DAYS * era2.SEASON_DAYS + era2.SEASON_DAYS - 1
    end = (D + 1) // era2.YEAR * era2.YEAR + era2.YEAR - 1
    return list(range(first, end + 1, era2.SEASON_DAYS))


def _year_plan(state, rng):
    """次の年 (G7 に入った日は、年の終わりまでの短い年) の便りを引く (村 → まわりの集落の番号の順)。数・運び手・段・札・季節"""
    h, D = _h(state), state["day"]
    dues = _seasons_left(D)
    now = _stage_now(state)
    rids = ["V0"] + [o["id"] for o in sorted((state["era2"].get("g6") or {}).get("others", []), key=lambda o: int(o["id"][1:])) if not o.get("gone")]
    for rid in rids:
        ts = terms(state, rid)
        lam = round(math.fsum(w for _, w, _ in ts), 6)
        n_raw = poisson(rng, lam)
        n = min(HINT_CAP, n_raw)
        h["lam"].append({"day": D, "to": rid, "lam": lam, "n": n, "terms": [[c, w, f] for c, w, f in ts]})
        for _ in range(n):
            u = rng.random() * lam
            acc, pick = 0.0, ts[-1]
            for t in ts:
                acc += t[1]
                if u < acc:
                    pick = t
                    break
            carrier, frm = pick[0], pick[2]
            si = rng.randrange(len(dues))
            stage, us = _pick_stage(rng, now)
            card, got = _pick_card(state, rng, rid, stage, now, carrier)
            y = f"Y{h['next']}"
            h["next"] += 1
            row = {"y": y, "card": card, "carrier": carrier, "to": rid, "from": frm, "drawn": D, "due": dues[si], "stage": STAGES[stage],
                   "stage_got": STAGES[got] if got is not None else None, "u": [round(u, 6), round(us, 6)], "status": "待つ" if card else "空振り",
                   "delivered": None, "listeners": [], "outcome": []}
            if not card:
                row["why"] = "引いた段と運び手の札がない"
            else:
                h["seen"].setdefault(rid, {})[card] = h["seen"].get(rid, {}).get(card, 0) + 1
                h["plan"].append(y)
            h["ledger"].append(row)


# ---------------- G7 に入る日 (4.E.1 の 3) ----------------

def start(state):
    """G7 に入る日: 札の表のハッシュと、最初の年 (年の終わりまでの短い年) の便り。塩 47 はこの日に 1 回だけ作る"""
    g, D = state["era2"]["g7"], state["day"]
    sha = cards_sha()
    g["hints"] = {"cards_sha": sha, "cards_log": [{"day": D, "sha": sha, "note": "G7 に入った日"}], "plan": [], "ledger": [], "next": 1,
                  "seen": {}, "used": {}, "tech": {}, "knowers": {}, "lam": [], "things": [], "pending_knowers": {}, "checked_k": D, "checked_l": []}
    if world.G7_PARTS.get("hints", True):
        _year_plan(state, era2._rng(state, era2.HINT_SALT))


def cards_changed(state):
    """札の表のハッシュが、G7 に入った日 (か step.py cards の日) のものとちがえば、その文 (step.py season が止まる。終わりのコード 5)"""
    if not on(state):
        return None
    now = cards_sha(state)
    return None if now == _h(state)["cards_sha"] else f"札の表 ({CARDS.name}) が変わった (残したハッシュ {_h(state)['cards_sha'][:12]}…・今 {now[:12]}…)"


def cards_note(state, note):
    """札を足す・直したとき (step.py cards): 出来事「区切り」を残し、新しいハッシュを cards_log に足す"""
    h, sha = _h(state), cards_sha(state)
    bad = check_cards()
    if bad:
        return "札の表に直すところがある: " + "・".join(bad[:5])
    h["cards_sha"] = sha
    h["cards_log"].append({"day": state["day"], "sha": sha, "note": note})
    log(state, "区切り", None, f"よその便りの札の表を直した ({note})", cards=sha)
    return None


# ---------------- 知っている人 (4.C.6) ----------------

def knows(state, name, card):
    return name in (_h(state)["knowers"].get(card) or [])


def _add_knowers(state, card, names):
    k = _h(state)["knowers"].setdefault(card, [])
    for n in names:
        if n not in k:
            k.append(n)
    k.sort()


def _household_adults(state, names):
    hs = {p.get("household") for p in era2.adults(state) if p["name"] in names and p.get("household")}
    return sorted({p["name"] for p in era2.adults(state) if p.get("household") in hs} | set(names))


def _hint_events(state):
    """村に届いた便りの出来事の番号 → 帳簿の行"""
    return {r["event"]: r for r in _h(state)["ledger"] if r["to"] == "V0" and r.get("event") is not None}


def _scan_knowledge(state):
    """知識を足したとき、その because に、便りの出来事か、便りが届いたあとの知っている人の「話す」の出来事を入れた人も、知っている人 (その知識に card を残す)。
    話の中身は読まない (出来事の番号と、だれの話かだけ)"""
    h = _h(state)
    hev = _hint_events(state)
    if not hev:
        return
    since = h.get("checked_k", 0)
    talk = {e["id"]: e for e in state["events"] if e["type"] == "話す" and e["id"] >= min(hev)}
    for p in era2.adults(state):
        for k in p.get("knowledge", []):
            if k.get("day", 0) < since or k.get("card") or k.get("label") == "最初の知識":
                continue
            hit = None
            for i in k.get("because") or []:
                if i in hev:
                    hit = hev[i]
                    break
                e = talk.get(i)
                if e:
                    for r in hev.values():
                        if e["day"] >= r["delivered"] and knows(state, e.get("who"), r["card"]):
                            hit = r
                            break
                if hit:
                    break
            if hit:
                k["card"] = hit["card"]
                _add_knowers(state, hit["card"], [p["name"]])
                if "覚えた" not in [o[0] for o in hit["outcome"]]:
                    hit["outcome"].append(["覚えた", state["day"], p["name"]])
    h["checked_k"] = state["day"]


def _scan_laws(state):
    """制度・教えの札: 採用された掟の because が便りの出来事を引いたら「使った」(断る掟でもよい。村が決めたので抜く)"""
    h = _h(state)
    hev = _hint_events(state)
    done = set(h.get("checked_l") or [])
    for l in state.get("laws", []):
        if l["status"] != "採用" or l["id"] in done:
            continue
        hit = [hev[i] for i in (l.get("because") or []) if i in hev]
        if hit:
            done.add(l["id"])
            for r in hit:
                r["outcome"].append(["掟", state["day"], l["id"]])
                if cards()[r["card"]]["kind"] in ("制度", "教え"):
                    _use(state, "V0", r["card"])
    h["checked_l"] = sorted(done)


def _use(state, rid, card):
    u = _h(state)["used"].setdefault(rid, [])
    if card not in u:
        u.append(card)


# ---------------- 試す (4.C.10) ----------------

def needs_ok(state, needs):
    """前提がそろっているか (コードにない前提は「そろっていない」と読む。そのとき札は「話だけ」)"""
    for k, n in (needs or {}).items():
        if k == "牛":
            if len(state["era2"].get("cattle") or []) < n:
                return False
        else:
            return False
    return True


def _field_days(state):
    return sum(acts.get("畑仕事", 0) for s in state["era2"]["g7"].get("past", []) for acts in s["days"].values())


def when_ok(state, when):
    for k, n in (when or {}).items():
        if k == "牛":
            if len(state["era2"].get("cattle") or []) < n:
                return False
        elif k == "畑仕事の日":
            if _field_days(state) < n:
                return False
        else:
            return False
    return True


def _open(state, card, source):
    t = _h(state)["tech"].setdefault(card, {"open": None, "wait": None, "source": source, "first": None, "progress": 0.0, "done": None, "last": None})
    if t["open"] is None:
        t.update(open=state["day"], source=t.get("source") or source)
    return t


def open_techs(state):
    """試せる札 (開いていて、まだできていない)"""
    return sorted(c for c, t in _h(state)["tech"].items() if t.get("open") is not None and not t.get("done"))


def can_try(state, name, card, with_=()):
    """試してよいか: 開いた札を知っている人。知らない人も、知っている人と一緒に (with) なら試せる (その日に一緒に試すと、次の季節から知っている人。4.C.6 の 3)"""
    return card in open_techs(state) and (knows(state, name, card) or any(knows(state, w, card) for w in with_ or ()))


def try_day(state, p, t):
    """仕事「試す」の 1 日 (キャンプ)。進み += 働いた時間 / 6 × (0.5 + 腕)。教える人 (腕 0.6 以上) と同じ日に働くと、腕は +0.04、進みは 2 倍"""
    g7 = state["era2"]["g7"]
    j = (g7.get("jobs7") or {}).get(p["name"]) or {}
    card = j.get("try")
    mates = [q for q in era2.adults(state) if q is not p and (q.get("today") or {}).get("activity") == "試す"
             and ((g7.get("jobs7") or {}).get(q["name"]) or {}).get("try") == card] if card else []
    knower = bool(card) and knows(state, p["name"], card)
    helped = [q for q in mates if q["name"] in ((p.get("plan") or {}).get("with") or []) and knows(state, q["name"], card)]
    if not card or card not in open_techs(state) or not (knower or helped):
        t.setdefault("events", []).append(log(state, "休む", p["name"], f"{p['name']} は、試すことが分からず、休んだ"))
        return
    key = f"試す:{card}"
    sk = p["skills"].setdefault(key, TRY_SKILL0)
    teach = any(q["skills"].get(key, 0) >= TEACH_AT for q in mates)
    tech = _h(state)["tech"][card]
    tech["progress"] = round(tech["progress"] + t.get("work_h", 6) / 6 * (0.5 + sk) * (2 if teach else 1), 3)
    tech["last"] = state["day"]
    p["skills"][key] = round(min(1.0, sk + (TRY_TEACH_STEP if teach else TRY_STEP)), 3)
    if tech["first"] is None:
        tech["first"] = state["day"]
        _use(state, "V0", card)
        for r in _h(state)["ledger"]:
            if r["to"] == "V0" and r["card"] == card and r["status"] == "届いた":
                r["outcome"].append(["試した", state["day"], p["name"]])
    if not knower:  # 知っている人と同じ日に一緒に試した人は、次の季節から知っている人 (手を動かして覚える道。4.C.6 の 3)
        pk = _h(state)["pending_knowers"].setdefault(card, [])
        if p["name"] not in pk:
            pk.append(p["name"])
    name = cards()[card]["name"]
    t.setdefault("events", []).append(log(state, "試す", p["name"], f"{p['name']} がキャンプで、よその便りで聞いたこと ({name}) を試した"
                                          + ("。腕のある人に教わりながら" if teach else ""), card=card))


def _tech_season(state):
    """季節の終わり: 待つ札が開く・できる・腕を持つ人がいなくなったら戻る (乱数なし)"""
    h, D = _h(state), state["day"]
    cs = cards()
    for card, t in sorted(h["tech"].items()):
        c = cs[card]
        if t.get("open") is None and t.get("wait") is not None and needs_ok(state, c.get("needs")):
            t["open"] = D
            log(state, "試す", None, f"よその便りで聞いた「{c['name']}」に要るものが村にそろい、試せるようになった", card=card)
        if t.get("open") is not None and not t.get("done") and t.get("first") is not None:
            tr = c.get("try") or {}
            if t["progress"] >= tr.get("days", 10 ** 9) and D - t["first"] >= tr.get("years", 0) * era2.YEAR and needs_ok(state, c.get("needs")):
                t["done"] = D
                who = sorted((p for p in era2.adults(state) if p["skills"].get(f"試す:{card}", 0) > 0), key=lambda p: (-p["skills"][f"試す:{card}"], p["name"]))
                log(state, "試す", who[0]["name"] if who else None,
                    f"村で「{c['name']}」ができるようになった ({'よその便りから' if t['source'] == 'ヒント' else 'きっかけから'}。"
                    f"試した人 {'・'.join(p['name'] for p in who[:6])}{' ほか' if len(who) > 6 else ''})", card=card, source=t["source"])
        if t.get("done") and not any(p["skills"].get(f"試す:{card}", 0) > 0 for p in era2.adults(state)):
            t["done"], t["progress"] = None, round(t["progress"] / 2, 3)
            log(state, "試す", None, f"「{c['name']}」を覚えた人が村にいなくなり、できなくなった", card=card)
    for card, names in sorted(h["pending_knowers"].items()):
        _add_knowers(state, card, names)
    h["pending_knowers"] = {}


def _tech_decay(state):
    """年の終わり: 3 年だれも試さなければ、進みが半分 (一度ずつ)"""
    D = state["day"]
    for card, t in sorted(_h(state)["tech"].items()):
        if t.get("done") or not t.get("progress"):
            continue
        last = t.get("last") or t.get("open") or D
        if D - last >= TRY_DECAY_YEARS * era2.YEAR and t.get("decayed") != last:
            t["progress"], t["decayed"] = round(t["progress"] / 2, 3), last


def chance(state):
    """きっかけ (4.C.11。年の最後の日の季節の終わり。塩 67): まだ開いていない技術の札を番号の順に見て、前提ときっかけの条件がそろう札だけ 1 回引く"""
    if not on(state) or (state["day"] + 1) % era2.YEAR:
        return
    h, cs = _h(state), cards()
    rng = era2._rng(state, era2.CHANCE_SALT)
    sample = set((state["era2"]["g7"].get("sample") or {}))
    for card in sorted(cs):
        c = cs[card]
        t = h["tech"].get(card) or {}
        if c["kind"] != "技術" or not c.get("chance") or t.get("open") is not None:
            continue
        if not (needs_ok(state, c.get("needs")) and when_ok(state, c["chance"].get("when"))):
            continue
        u = rng.random()
        h.setdefault("chance_log", []).append({"day": state["day"], "card": card, "u": round(u, 6), "p": c["chance"]["p"]})
        if u >= c["chance"]["p"]:
            continue
        job = "畑仕事" if "畑仕事の日" in c["chance"].get("when", {}) else None
        days = {}
        for s in state["era2"]["g7"].get("past", []):
            for n, acts in s["days"].items():
                days[n] = days.get(n, 0) + (acts.get(job, 0) if job else sum(acts.values()))
        cand = sorted((p for p in era2.adults(state) if p.get("household") in sample), key=lambda p: (-days.get(p["name"], 0), -p["age"], p["name"]))
        who = cand[0]["name"] if cand else None
        _open(state, card, "きっかけ")
        h["tech"][card]["source"] = "きっかけ"
        if who:
            _add_knowers(state, card, _household_adults(state, [who]))
        log(state, "きっかけ", who, (f"{who} が見ていると、" if who else "") + f"{c['chance']['text']}。村で「{c['name']}」を試せるようになった", card=card)


# ---------------- 届く (4.C.4・4.C.6) ----------------

def _sample_adults(state):
    sample = set(state["era2"]["g7"].get("sample") or {})
    return sorted(p["name"] for p in era2.adults(state) if p.get("household") in sample)


def _listeners(state, rng, met):
    """聞く人: 1〜3 人 (等しく引く)。見本の家の大人から。届いた季節に運び手に会った人を先に"""
    n = rng.randint(1, 3)
    pool = _sample_adults(state)
    first = sorted(x for x in set(met) if x in pool)
    rest = [x for x in pool if x not in first]
    a = first if len(first) <= n else rng.sample(first, n)
    b = rng.sample(rest, min(len(rest), n - len(a))) if n > len(a) else []
    return sorted(a + b)


def _met_merchant(state, frm):
    """この季節に、その集落へ交換に行った人"""
    g6 = state["era2"].get("g6") or {}
    sd = state["era2"].get("step_day", 0)
    return [tr["who"] for tr in list(g6.get("trips", {}).values()) + g6.get("trip_log", [])
            if tr.get("to") == frm and tr.get("start") is not None and tr["start"] >= sd]


def _cond(state, r):
    """届いたときの条件 (帳簿だけ。【シ】)"""
    ind = state.get("era_info", {}).get("indicators", {}) or {}
    lo, hi = _window(state)
    return {"era": state.get("era"), "people": ind.get("population"), "adults": len(era2.adults(state)), "households": len(era2._homes(state)),
            "store_days": round(era2.store_days(state), 1), "bad": _bad_year(state, lo, hi), "debt": _debt_year(state, lo, hi),
            "partners": sum(1 for t in terms(state, "V0") if t[0] == "商人"), "joined": _joined_groups(state, lo, hi),
            "disputes": sum(1 for d in (state["era2"].get("g5") or {}).get("disputes", []) if d["status"] == era2.OPEN),
            "needs": needs_ok(state, cards()[r["card"]].get("needs")), "stage_gap": STAGES.index(r["stage_got"]) - _stage_now(state)}


def _deliver_v0(state, rng, r):
    """村に届く (季節の終わり)"""
    c, D, sea = cards()[r["card"]], state["day"], season(state["day"])
    e2, h = state["era2"], _h(state)
    far = r["from"] == FAR  # G9: 遠くの商人 (地図の外から。集落はない)
    o = era2._other(state, r["from"]) if r["from"] and not far else None
    if r["carrier"] == "商人" and not far and (not o or o.get("gone") or o.get("known") is None):
        r.update(status="空振り", why="商人の集落がない", delivered=D)
        return
    met = _met_merchant(state, r["from"]) if r["carrier"] == "商人" and not far else []
    who = _listeners(state, rng, met)
    if not who:
        r.update(status="空振り", why="聞く人がいない", delivered=D)
        return
    by = FAR_WORD if far else CARRIER_WORD[r["carrier"]].format(o=o["name"] if o else "")
    group = None
    if r["carrier"] in ("よそから来た人", "教えを説く人"):
        k = rng.randint(1, 2)
        members = [{"name": era2._next_name(state), "sex": "女" if rng.random() < 0.5 else "男", "age": rng.randint(*GROUP_AGE)} for _ in range(k)]
        group = {"name": members[0]["name"], "members": members, "day": D, "hint": r["y"], "card": r["card"], "seed": rng.getrandbits(31)}
        e2["visitors"].append(group)
        names = "・".join(m["name"] for m in members)
        text = f"{sea}の終わり、{by}の {names} が村に来て、「ここで暮らしたい」と言い、{' と '.join(who)} に遠くで見聞きしたことを話した"
    else:
        text = f"{sea}の終わり、{by}が {' と '.join(who)} に話をしていった"
    eid = log(state, "よその便り", None, text, hint=r["y"], card=r["card"], carrier=r["carrier"], listeners=who,
              **({"other": r["from"]} if r["from"] and not far else {}), **({"group": group["name"]} if group else {}), **({"far": True} if far else {}))
    state["events"][-1]["data"]["text"] = c["text"]  # 話の中身は data だけに (出来事の文には入れない。4.C.8)
    for p in era2.adults(state):
        if p["name"] in who:
            p["heard"].append({"day": D, "from": by, "text": c["text"], "event": eid})
            p["heard"] = p["heard"][-30:]
    _add_knowers(state, r["card"], _household_adults(state, who))
    r.update(status="届いた", delivered=D, event=eid, listeners=who, cond=_cond(state, r))
    if c["kind"] == "技術":
        t = h["tech"].get(r["card"])
        if not t or (t.get("open") is None and t.get("wait") is None):
            if needs_ok(state, c.get("needs")):
                _open(state, r["card"], "ヒント")
            else:
                h["tech"][r["card"]] = {"open": None, "wait": D, "source": "ヒント", "first": None, "progress": 0.0, "done": None, "last": None}
    if far:  # G9: 遠くの商人は、話のほかに、赤い金属の道具との取り替えを申し出る (次の集まりまで待つ。g9.far_arrive)
        _g9m().far_arrive(state, r)
    elif c["kind"] == "もの" and r["carrier"] == "商人" and o:
        thing = (c.get("unlocks") or {}).get("thing") or c["name"]
        g6 = era2._g6(state)
        off = {"id": f"T{g6['next_offer']}", "kind": "交換", "other": o["id"], "day": D, "give": {thing: 1}, "want": dict(THING_WANT),
               "hint": r["y"], "card": r["card"], "goats_in": [], "mem": {"village": 1.0, "other": 1.0}}
        g6["next_offer"] += 1
        g6["offers"].append(off)
        log(state, "よその村", None, f"{o['name']} から来た運ぶ人は、{thing} 1 つを出すので、{era2._gw(off['want'])} がほしいと言った [{off['id']}]",
            other=o["id"], offer=off["id"], hint=r["y"])


def _deliver_other(state, r):
    """まわりの集落に届く (帳簿だけ。技術の札は、rogers の合計が 11 以上なら決まりで試す。4.C.12)"""
    c, D = cards()[r["card"]], state["day"]
    o = era2._other(state, r["to"])
    if not o or o.get("gone"):
        r.update(status="空振り", why="集落がない", delivered=D)
        return
    r.update(status="届いた", delivered=D)
    if c["kind"] == "技術" and sum(c.get("rogers", {}).values()) >= ROGERS_RULE:
        o.setdefault("hint_try", {}).setdefault(r["card"], D)
        r["outcome"].append(["試した", D, "決まり"])


def settled(state, v, accepted):
    """便りの群れを受け入れたか (era2._settle_visitors から)。受け入れたら、群れの人は知っている人。「人」の札なら、教える腕で加わる"""
    h = _h(state)
    r = next((x for x in h["ledger"] if x["y"] == v.get("hint")), None)
    if not r:
        return
    c = cards()[r["card"]]
    names = [m["name"] for m in v["members"]]
    if not accepted:
        r["outcome"].append(["断られた", state["day"]])
        return
    r["outcome"].append(["受け入れた", state["day"]])
    _add_knowers(state, r["card"], names)
    if c["kind"] == "人":
        _use(state, "V0", r["card"])
        if c.get("teach"):
            for p in state["people"]:
                if p["name"] in names and not p.get("child"):
                    p["skills"][c["teach"]] = max(p["skills"].get(c["teach"], 0), TEACH_SKILL)
                    p["teach"] = c["teach"]


def craft_step(state, p, act, base):
    """土器づくり・道具づくりの腕の伸び (era2._craft から。G7): 教える人 (「人」の札で来た人) と同じ日に同じ仕事をすると 2 倍 (量は変えない)"""
    skill = next((k for k, a in CRAFT_ACT.items() if a == act), None)
    if not skill or p.get("teach") == skill:
        return base
    for q in era2.adults(state):
        if q is not p and q.get("teach") == skill and (q.get("today") or {}).get("activity") == act:
            return base * 2
    return base


def thing_offer(state, c6, off, o, n, lead, how):
    """商人が「もの」を出す申し出 (era2._g6_decide から)。受けると、ものを受けとる (使えるが、作れない。値うちの数え方は変えない)"""
    h = _h(state)
    at = "季節の集まりで" if how == "集まり" else "季節のはじめに、年の方針で"
    tally = {k: len(v) for k, v in c6["trade"].get(off["id"], {}).items()}
    votes = f"村 {tally.get('村', 0)}・家 {tally.get('家', 0)}・受けない {tally.get(False, 0)} / 大人 {n}"
    side = None
    if tally.get("村", 0) * 2 > n or (lead and c6["trade_by"].get(off["id"], {}).get(lead) == "村"):
        side = "村"
    else:
        cands = [x for x in c6["house"].get(off["id"], []) if all(era2._g6_have(state, x, k) >= m for k, m in off["want"].items())]
        side = sorted(cands)[0] if cands else None
    r = next((x for x in h["ledger"] if x["y"] == off.get("hint")), None)
    thing = next(iter(off["give"]))
    if side is None or any(era2._g6_have(state, side, k) < m for k, m in off["want"].items()):
        log(state, "よその村", None, f"{at}、{o['name']} の申し出 [{off['id']}] ({thing}) は受けなかった ({votes})", other=o["id"], offer=off["id"])
        if r:
            r["outcome"].append(["断られた", state["day"]])
        return
    ids = []
    gave = era2._g6_take(state, side, off["want"], ids)
    era2._node_add(o, gave, 1)
    h["things"].append({"thing": thing, "card": off.get("card"), "day": state["day"], "side": side, "from": o["id"]})
    era2._g6_contact(state, o)
    log(state, "交換", None, f"{at}、{'村は、村の物で' if side == '村' else side + 'が、家の物で'} {o['name']} の申し出 [{off['id']}] を受け、"
        f"{era2._gw(gave)} を {thing} 1 つと取り替えた ({votes})", other=o["id"], offer=off["id"], moves=[era2._mv(side, -1, gave, ids)], thing=thing)
    if r:
        r["outcome"].append(["受けとった", state["day"], side])
        _use(state, "V0", r["card"])


# ---------------- 捕らえた職人 (4.C.4) ----------------

def _captives_choice(state):
    return (state["era2"]["g7"].get("captives") or {}).get("choice")


def _skill_of(p):
    return max([v for k, v in p["skills"].items() if k in ("土器", "道具") or k.startswith("試す:")] or [0])


def _captives(state, rng):
    """この季節に勝ち負けが決まった、村の戦 (戦の番号の順)。勝って「連れて帰る」と答えていれば、捕らえた職人の札から 1 人が来る。
    負けたら、見込み 0.5 で、村でいちばん腕の高い大人 (同じなら年上、そのつぎは名前の順) が連れて行かれる"""
    g7, D = state["era2"]["g7"], state["day"]
    sd = state["era2"].get("step_day", 0)
    reg = g7.get("region") or {}
    now = _stage_now(state)
    for w in sorted((w for w in reg.get("wars", []) if w.get("done") is not None and sd <= w["done"] <= D and not w.get("called_off")
                     and "V0" in (w["att"], w["def"])), key=lambda w: int(w["id"][1:])):
        if w.get("captive_done"):
            continue
        w["captive_done"] = D
        won = (w["att"] == "V0") == bool(w.get("att_win"))
        other = w["def"] if w["att"] == "V0" else w["att"]
        if won:
            if _captives_choice(state) != "連れて帰る":
                continue
            card, got = _pick_card(state, rng, "V0", _pick_stage(rng, now)[0], now, "捕らえた職人")
            y = f"Y{_h(state)['next']}"
            _h(state)["next"] += 1
            row = {"y": y, "card": card, "carrier": "捕らえた職人", "to": "V0", "from": other, "drawn": D, "due": D, "stage": STAGES[got] if got is not None else None,
                   "stage_got": STAGES[got] if got is not None else None, "u": [], "status": "空振り" if not card else "届いた", "delivered": D,
                   "listeners": [], "outcome": [], "war": w["id"]}
            _h(state)["ledger"].append(row)
            if not card:
                row["why"] = "捕らえた職人の札がない"
                continue
            c = cards()[card]
            p = era2._new_person(state, rng, "女" if rng.random() < 0.5 else "男", rng.randint(*GROUP_AGE), origin="連れて来られた")
            p["household"] = p["name"] + "の家"
            p["plan"] = {"activity": "休む", "place": "camp", "with": []}
            state["era2"]["jobs"][p["name"]] = {"sow": 0, "pick": 0, "plant": 0, "eat_goat": 0, "harvest": 0}
            if c.get("teach"):
                p["skills"][c["teach"]] = TEACH_SKILL
                p["teach"] = c["teach"]
            o = era2._other(state, other)
            eid = log(state, "加わる", p["name"], f"戦に勝ち、{o['name'] if o else 'ほかの村'} の職人 {p['name']} ({p['sex']}、{p['age']} 歳) を連れて帰った",
                      hint=y, card=card, war=w["id"], captive=True)
            row.update(event=eid, listeners=[p["name"]], cond=_cond(state, row))
            _add_knowers(state, card, [p["name"]])
            _use(state, "V0", card)
        else:
            if rng.random() >= CAPTURE_P:
                continue
            ads = sorted(era2.adults(state), key=lambda q: (-_skill_of(q), -q["age"], q["name"]))
            if not ads:
                continue
            p = ads[0]
            p["alive"], p["left"] = False, D
            o = era2._other(state, other)
            log(state, "戦", p["name"], f"戦に負け、{p['name']} ({p['age']} 歳) が {o['name'] if o else 'ほかの村'} へ連れて行かれた", war=w["id"], taken=p["name"])
            era2._inherit(state, p)
            era2._check_leader(state)
            _h(state)["ledger"].append({"y": None, "card": None, "carrier": "捕らえた職人", "to": other, "from": "V0", "drawn": D, "due": D,
                                        "status": "連れて行かれた", "delivered": D, "listeners": [p["name"]], "outcome": [], "war": w["id"],
                                        "skills": {k: v for k, v in p["skills"].items() if k in ("土器", "道具") or k.startswith("試す:")}})


# ---------------- 季節の終わり (4.G.1 の 11) ----------------

def _forget(state):
    """3 年だれも使わなかった便りは「忘れられた」"""
    D = state["day"]
    for r in _h(state)["ledger"]:
        if r["to"] == "V0" and r["status"] == "届いた" and D - r["delivered"] >= HEARD_YEARS * era2.YEAR and not r["outcome"]:
            r.update(status="忘れられた", forgot=D)


def season_end(state):
    """よその便りの季節の終わり (g7.season_end の 11。見本の家の選び直しのあと)。塩 47 はこの日に 1 回だけ作る"""
    if not on(state):
        return
    D = state["day"]
    _scan_knowledge(state)
    _scan_laws(state)
    _tech_season(state)
    _forget(state)
    rng = era2._rng(state, era2.HINT_SALT)
    year_end = (D + 1) % era2.YEAR == 0
    if year_end:
        _tech_decay(state)
        _year_plan(state, rng)  # 1. 次の年の分
    _captives(state, rng)  # 2. この季節の戦の、捕らえた職人
    if (D + 1) % era2.SEASON_DAYS == 0:  # 3. この季節に届く便り (飢えで途中に区切った日には届けず、そのあとの最初の季節の終わりに)
        h = _h(state)
        due = [y for y in h["plan"] if next(r for r in h["ledger"] if r["y"] == y)["due"] <= D]
        for y in sorted(due, key=lambda y: int(y[1:])):
            r = next(x for x in h["ledger"] if x["y"] == y)
            if r["to"] == "V0":
                _deliver_v0(state, rng, r)
            else:
                _deliver_other(state, r)
        h["plan"] = [y for y in h["plan"] if y not in due]


# ---------------- お題 (4.C.8) ----------------

def text(state, p):
    """聞いた人のお題にだけ出す「## よその便り」(3 年以内・3 通まで。出来事の番号つき。試せることがあれば 1 行)"""
    if not on(state):
        return ""
    D = state["day"]
    rows = [r for r in _h(state)["ledger"] if r["to"] == "V0" and r.get("event") is not None and p["name"] in r.get("listeners", [])
            and r["status"] != "忘れられた" and D - r["delivered"] < HEARD_YEARS * era2.YEAR][-HEARD_MAX:]
    if not rows:
        return ""
    out = []
    for r in rows:
        c = cards()[r["card"]]
        o = era2._other(state, r["from"]) if r.get("from") and r.get("from") != FAR else None
        frm = FAR_WORD if r.get("from") == FAR else CARRIER_WORD[r['carrier']].format(o=o['name'] if o else 'ほかの村')
        out.append(f"- [出来事 {r['event']}] {r['delivered']} 日目、{frm}から聞いた話 "
                   f"(便りの番号 {r['card']}): 「{c['text']}」")
        if can_try(state, p["name"], r["card"]):
            out.append(f"  この話のことは、村で試せる (仕事「試す」。job の try に \"{r['card']}\")")
    return ("\n## よその便り (あなたが聞いた話)\n" + "\n".join(out)
            + "\n聞いた話をどうするかは、あなたと村が決める (何もしなくてもよい)\n")
