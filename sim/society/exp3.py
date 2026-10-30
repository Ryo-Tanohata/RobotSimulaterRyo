"""論文 2・実験 3「村の中で、暮らし・立場・まわりの様子を持たせる」のお題の節 (2026-10-30。docs/research/humanity/paper2_exp3_prereg.md)

- 写しの村 (sim/society/data_E3_*) だけで使う。本物の村 (sim/society/data) では step.py exp3 が断る。
- 切り替え: state["era2"]["g7"]["exp3"] = {"arm": "A0" | "A1" | "A2" (| "A3"), "day": 入れた日, "note": わけ}。1 回の走りの中では変えない。
  arm がない・A0 のときは、お題は今のまま (1 バイトも同じ。apply がそのまま返す)。
- 変えるのは、季節の集まりのお題 (代表とまとめ役が答えるもの) だけ。「覚えていること」の節のすぐ前に、節を 1 つか 2 つ足す。
  気持ちのお題・まわりの集落の集まりのお題・答えの形・世界の決まり・乱数・出来事は変えない (同じ答えなら同じ世界)。
- 節の中身は、みな state から数えた事実 (作った話・よい悪いの言葉・「〜すべき」は書かない)。
  A1「あなたの家の暮らし」(実験 2 の D1 にあたる: 家の人・おなか・家の倉・村の蓄え・持ち物の順位・村の蓄えへの出し入れ・親類・もめごと・役)
  A2 = A1 + 「村のまわりの様子」(実験 2 の D2 にあたる: 修士論文の「はみ出しやすい時」のうち、村で数えられる 3 つ。
     みんながやっている = 入れたより多く取った家の数・ほかの家の倉から取ったもめごとの数 /
     捕まった人を聞いたことがない = つぐなうで払わせた数・最後に払った年・罰のある掟 /
     簡単にできる = 村の蓄えの封・家の倉の印の封)。
  A3 = 「村のまわりの様子」だけ (登録はしたが、今の計画では使わない)。
- 数はみな math.fsum と整数で数える (python の版で変わらないように)。
"""
import math

import era2
from world import food_words, holdings

ARMS = {"A0": (), "A1": ("life",), "A2": ("life", "around"), "A3": ("around",)}
ARM_WORDS = {"A0": "今のお題のまま (くらべる組)", "A1": "暮らし (自分の家の暮らし・立場・損得)", "A2": "暮らし + まわりの様子",
             "A3": "まわりの様子だけ (計画では使わない)"}
ANCHOR = "\n## 覚えていること\n"  # この見出しの前に足す (季節の集まりのお題にも、年の集まりのお題にも 1 つだけある)
WINDOW_YEARS = 10  # 「この 10 年」
LIFE_HEAD = "## あなたの家の暮らし (いまの様子)"
AROUND_HEAD = "## 村のまわりの様子 (この 10 年ほど)"
# お題の節に書かない言葉 (よい・悪いを決める言葉と、性格の言葉。test_exp3.py が確かめる)
FORBIDDEN = ("盗", "悪い", "悪く", "ずる", "正直", "まじめ", "良心", "道徳", "責任", "罪", "恥", "いけない", "べき", "許されない", "ゆるされない",
             "思いやり", "やさしい", "わがまま", "身勝手", "性格", "協力的", "誠実", "外向", "神経", "開放", "みんながやっている", "捕ま")


def arm(state):
    """今の組 (なければ None)"""
    x = (((state.get("era2") or {}).get("g7") or {}).get("exp3") or {})
    return x.get("arm")


def parts(state):
    return ARMS.get(arm(state) or "A0", ())


def refusal(state, arm_, data_dir, real_dir):
    """step.py exp3 ができないわけ (できるなら None)"""
    if arm_ not in ARMS:
        return f"組は {' / '.join(ARMS)} のどれか ({arm_} とは書けない)"
    try:
        same = data_dir.resolve() == real_dir.resolve()
    except OSError:
        same = False
    if same:
        return "本物の村 (sim/society/data) には入れない (写しの村 SOC_DATA=… だけ)"
    if not ((state.get("era2") or {}).get("g7")):
        return f"G7 より前の村には入れない (今は {state.get('era')})"
    if state.get("phase") != "season":
        return f"段階が season でない (今は {state.get('phase')})"
    cur = arm(state)
    if cur is not None and cur != arm_:
        return f"もう組 {cur} で走っている ({state['era2']['g7']['exp3']['day']} 日目から)。1 回の走りの中では変えない"
    return None


def set_arm(state, arm_, note):
    """組を残す (乱数・出来事・世界にはさわらない)。もう同じ組なら None"""
    g = state["era2"]["g7"]
    if (g.get("exp3") or {}).get("arm") == arm_:
        return None
    g["exp3"] = {"arm": arm_, "day": state["day"], "note": note}
    return g["exp3"]


def apply(state, p, text):
    """季節の集まりのお題に節を足す (組がない・A0 なら、text をそのまま返す)"""
    ps = parts(state)
    if not ps:
        return text
    add = ""
    if "life" in ps:
        add += life_text(state, p)
    if "around" in ps:
        add += around_text(state, p)
    if text.count(ANCHOR) != 1:
        raise ValueError("お題に「覚えていること」の見出しが 1 つだけでない (節を足せない)")
    return text.replace(ANCHOR, add.rstrip("\n") + "\n" + ANCHOR, 1)


# ---------------- 数える (読むだけ) ----------------

def _yd(day):
    return f"{day // era2.YEAR}年"


def _grain(kcal):
    return int(kcal // era2.GRAIN)


def _need_of(adults_, kids):
    """家の人の 1 日に食べる量 (era2._need と同じ数え方)"""
    return sum(era2.BASE_KCAL + 500 for _ in adults_) + sum(next(k for a, k in era2.CHILD_EAT if c["age"] < a) for c in kids)


def _house_kcal(state, h):
    return math.fsum(f["kcal"] for f in ((state["era2"].get("house") or {}).get(h) or {}).get("store", []))


def _members(state, h):
    ads = [q for q in era2.adults(state) if q.get("household") == h]
    kids = [c for c in era2.children(state) if c.get("household") == h]
    return ads, kids


def _wealth(state):
    """家ごとの持ち物 (家の倉 + ヤギ。g7._wealth と同じ)。大人のいる家だけ"""
    hs, goats = state["era2"].get("house", {}), {}
    for x in state["era2"]["goats"]:
        goats[x.get("owner")] = goats.get(x.get("owner"), 0) + 1
    return {h: round(math.fsum(f["kcal"] for f in hs.get(h, {}).get("store", [])) + goats.get(h, 0) * era2.GOAT_WORTH) for h in era2._homes(state)}


def _shown_rows(state):
    """前の季節の、家ごとの村の蓄えへの出し入れ (お題の「ほかの村・印・記録」に出すもの。記録なら数、なければ覚えの幅)。
    戻り値: (how, {家: ((入れた下, 入れた上), (取った下, 取った上))})"""
    sh = ((state["era2"].get("g6") or {}).get("shown")) or {}
    rows = sh.get("rows") or {}
    out = {}
    for h, (i, o) in rows.items():
        i2 = tuple(i) if isinstance(i, (list, tuple)) else (i, i)
        o2 = tuple(o) if isinstance(o, (list, tuple)) else (o, o)
        out[h] = (i2, o2)
    return sh.get("how"), out


def _amount(lo_hi, how):
    lo, hi = lo_hi
    if how or lo == hi:
        return f"{lo} つかみ"
    return f"{lo}〜{hi} つかみ" if hi else "0 つかみ"


def _disputes(state, since=None):
    ds = (state["era2"].get("g5") or {}).get("disputes", [])
    return [d for d in ds if since is None or d["day"] >= since]


def _paid(d):
    return d.get("verdict") == "つぐなう" and (d.get("paid") or 0) > 0


def kin(state, p):
    """親類の家 (母の家・同じ母のきょうだいの家・子の家。自分の家は入れない) と、この家の倉から食べることがある親類の子 (g7.kin_houses)"""
    h = p.get("household")
    homes = set(era2._homes(state))
    by = {q["name"]: q for q in state["people"] if q["alive"]}
    rows = []
    m = by.get(p.get("mother"))
    if m and m.get("household") in homes and m.get("household") != h:
        rows.append(f"母 {m['name']} は{m['household']}")
    sib = sorted({q["household"] for q in era2.adults(state) if q is not p and p.get("mother") and q.get("mother") == p.get("mother")
                  and q.get("household") in homes and q.get("household") != h})
    if sib:
        rows.append("同じ母のきょうだいの家: " + "、".join(sib))
    ch = sorted({q["household"] for q in era2.adults(state) if q.get("mother") == p["name"] and q.get("household") in homes and q.get("household") != h})
    if ch:
        rows.append("大人になった子の家: " + "、".join(ch))
    eat = []
    if "g7" in state["era2"] and era2._fix(state):
        import g7  # noqa: E402  (G7 の直しのあとだけ。子が親類の家の倉から食べる)
        eat = [c["name"] for c in era2.children(state) if c.get("household") != h and h in g7.kin_houses(state, c)]
    return rows, eat


# ---------------- 節の文 ----------------

def life_text(state, p):
    """A1: あなたの家の暮らし (代表の家の事実だけ。二人称。よい悪いは書かない)"""
    e2, h = state["era2"], p.get("household")
    ads, kids = _members(state, h)
    rows = []
    kid_txt = f"子 {len(kids)} 人 (15 歳より下。いちばん下は {min(c['age'] for c in kids)} 歳)" if kids else "子はいない"
    rows.append(f"- あなたの家 ({h}) の人: 大人 {len(ads)} 人、{kid_txt}")
    hung = [q for q in ads + kids if q.get("hunger", 0) >= 0.3]
    if hung:
        rows.append("- 家の人のおなか: " + "、".join(f"{q['name']} {era2._hunger_word(q['hunger'])}" for q in hung))
    else:
        rows.append("- 家の人のおなか: みな満腹か、少し空腹")
    need = _need_of(ads, kids)
    hk = _house_kcal(state, h)
    hs = (e2.get("house") or {}).get(h) or {}
    store = food_words(holdings({"food": hs.get("store", [])})) if hk > 0 else ""
    built = h in era2._homes_built(state)
    rows.append("- 家の倉: " + ("持つ" if hs.get("keep") else "持たない") + (f"。中に {store} (家の人だけで 約 {int(hk // max(1, need))} 日分)" if store else "。中はからっぽ")
                + ("" if built else "。家族の住まいはまだない"))
    rows.append(f"- 村の蓄え: 今の村の人数で 約 {era2.store_days(state)} 日分")
    w = _wealth(state)
    if h in w:
        order = sorted(w, key=lambda x: (-w[x], x))
        zero = sum(1 for x in w if w[x] <= 0)
        top = order[0]
        rank = ("何も持たない家の一つ" if w[h] <= 0 else f"上から {order.index(h) + 1} 番目")
        rows.append(f"- 持ち物 (家の倉の食べ物とヤギ) の多さ: 村の {len(w)} 家のうち、あなたの家は {rank}。何も持たない家は {zero} 家。"
                    f"いちばん多いのは{top} (草の種にして 約 {_grain(w[top])} つかみ分)")
    how, shown = _shown_rows(state)
    if h in shown:
        (i, o) = shown[h]
        rows.append(f"- 前の季節、あなたの家 (大人の分) は、村の蓄えに {_amount(i, how)} 入れて、{_amount(o, how)} 取った"
                    + (f" ({how}の記録による)" if how else " (記録はない。みんなの覚えでは、だいたい)"))
    krows, eat = kin(state, p)
    if krows:
        rows.append("- 親類: " + "。".join(krows))
    if eat:
        rows.append(f"- 村の蓄えと自分の家の倉で足りないとき、あなたの家の倉から食べることがある親類の子: {'、'.join(eat)}")
    since = state["day"] + 1 - WINDOW_YEARS * era2.YEAR
    ds = _disputes(state, since)
    mine_from = [d for d in ds if d["from"] == h]
    mine_ag = [d for d in ds if d["against"] == h]
    rows.append(f"- この 10 年 ({_yd(max(0, since))}から) のもめごと: あなたの家が言い出したもの {len(mine_from)} 件 (払われたもの {sum(_paid(d) for d in mine_from)} 件)、"
                f"あなたの家が相手のもの {len(mine_ag)} 件 (払ったもの {sum(_paid(d) for d in mine_ag)} 件)")
    op = [d for d in ds if d["status"] == era2.OPEN and h in (d["from"], d["against"])]
    if op:
        rows.append("- まだ収まっていないもめごとのうち、あなたの家のもの: "
                    + "、".join(f"[{d['id']}] ({'あなたの家が言い出した' if d['from'] == h else 'あなたの家が相手'})" for d in op))
    lead = (e2.get("g5") or {}).get("leader")
    ads_all = era2.adults(state)
    eldest = max(ads_all, key=lambda q: q["age"])["name"] if ads_all else None
    role = []
    if lead == p["name"]:
        role.append("あなたは村のまとめ役")
    if eldest == p["name"]:
        role.append("あなたは村でいちばん年上の大人")
    if p["name"] in era2._reps(state):
        role.append("あなたは家の代表")
    if role:
        rows.append("- " + "。".join(role))
    return f"\n{LIFE_HEAD}\n" + "\n".join(rows) + "\n"


def around_text(state, p):
    """A2: 村のまわりの様子 (修士論文の「はみ出しやすい時」のうち 3 つを、村の数で。どの家のことも、よい悪いは書かない)"""
    e2 = state["era2"]
    homes = era2._homes(state)
    rows = []
    how, shown = _shown_rows(state)
    if shown:
        cnt = [hh for hh in homes if hh in shown]
        more = [hh for hh in cnt if shown[hh][1][0] > shown[hh][0][1]]
        rows.append(f"- 前の季節、村の家 {len(cnt)} のうち {len(more)} の家は、村の蓄えに入れた量より多く取った"
                    + (f" ({how}の記録による)" if how else " (みんなの覚えでは。覚えの幅で見ても、取った量のほうが多い家)"))
    since = state["day"] + 1 - WINDOW_YEARS * era2.YEAR
    ds = _disputes(state, since)
    by_kind = {}
    for d in ds:
        by_kind[d["kind"]] = by_kind.get(d["kind"], 0) + 1
    kinds = "、".join(f"{k} {by_kind[k]} 件" for k in ("倉", "蓄え", "刈る", "ヤギ", "覚え") if by_kind.get(k))
    rows.append(f"- この 10 年 ({_yd(max(0, since))}から) に言い出されたもめごと: {len(ds)} 件" + (f" ({kinds})" if kinds else ""))
    k_houses = sorted({d["against"] for d in ds if d["kind"] == "倉"})
    if k_houses:
        rows.append(f"- そのうち、よその家の倉から食べ物を取ったもめごとの相手になった家: {len(k_houses)} 家")
    done = [d for d in ds if d["status"] != era2.OPEN]
    paid = [d for d in done if _paid(d)]
    rows.append(f"- この 10 年に収まったもめごと {len(done)} 件のうち、「つぐなう」で払うことになったのは {len(paid)} 件")
    allpaid = [d for d in _disputes(state) if _paid(d)]
    if allpaid:
        last = max(allpaid, key=lambda d: d.get("end", d["day"]))
        ld = last.get("end", last["day"])
        rows.append(f"- 村で最後に、もめごとの分を払った家があったのは {_yd(ld)} ({ld} 日目)。それから {max(0, (state['day'] - ld) // era2.YEAR)} 年、払った家はない")
    else:
        rows.append("- 村で、もめごとの分を払った家は、まだない")
    pen = [lw for lw in state["laws"] if lw["status"] == "採用" and lw.get("penalty")]
    pays = len((e2.get("g5") or {}).get("penalties") or [])
    rows.append(f"- 罰のある掟: {len(pen)} 本。罰を払ったことは、これまで {pays} 回")
    g6 = e2.get("g6") or {}
    ss = g6.get("store_sealed")
    rows.append("- 村の蓄えの土器に封をしたのは " + (f"{_yd(ss)} ({ss} 日目) が最後" if ss is not None else "これまでない")
                + "。封をしていない季節は、だれがいつ村の蓄えから取ったかの印は残らない")
    seals = g6.get("seals") or {}
    have = [hh for hh in homes if _house_kcal(state, hh) > 0]
    rows.append(f"- 家の倉に食べ物のある家 {len(have)} のうち、印 (封) のある家は {sum(1 for hh in have if hh in seals)}")
    return f"\n{AROUND_HEAD}\n" + "\n".join(rows) + "\n"


def strip(text):
    """apply で足した節を取りのぞく (確かめ用: 足した節のほかは、今のお題と 1 バイトも同じか)"""
    for head in (LIFE_HEAD, AROUND_HEAD):
        i = text.find("\n\n" + head + "\n")
        if i < 0:
            continue
        j = text.find(ANCHOR, i)
        text = text[:i + 1] + text[j:]
    return text
