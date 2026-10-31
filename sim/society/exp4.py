"""論文 2・実験 4「村の人が、自分の物でない食べ物を取るかを選ぶ」(2026-10-31。docs/research/humanity/paper2_exp4_prereg.md)

- 写しの村 (sim/society/data_E4_*) だけで使う。本物の村 (sim/society/data) では step.py exp4 が断る。
- 切り替え: state["era2"]["g7"]["exp4"] = {"arm": "B0" | "B1", "day": 入れた日, "note": わけ, "choice": {…}, "now": {…}, "acts": […], "log": […]}。
  1 回の走りの中では組を変えない。鍵がなければ、世界もお題も今のまま (1 バイトも同じ。どの関数も、はじめに on() を見て何もしない)。
- 入れると、世界の決まりが 1 つ変わる: ひどく空腹の人が、よその家の倉から自動で取る決まり (era2._steal) を止め、かわりに **村の人の答え** で取る。
  - 答える人: 集まりの歩で答える大人 (見本の家の代表・まとめ役 = 季節か年のお題、見本の家の代表でない大人 = 気持ちのお題)。
    そのうち、お題を作るときに **家の倉が、家の人の 30 日分 (TARGET_DAYS) より少ない家** の人だけに、節と欄 take・take_why を足す。
  - 選び (take): 「取らない」/「村の蓄え」(その日に食べる分のほかに、村の蓄えから大人 1 人の 1 日分を取って家の倉に入れる) /
    「よその家の倉」(印 (封) のないよその家の倉から、大人 1 人の 1 日分を、だまって取って家の倉に入れる。印のある倉からは取れない)。
  - 選びは次の集まりの歩まで使う。毎日、家の倉が 30 日分より少ない日に、選んだ人ひとりにつき 1 日分 (DAY_FOOD) を動かす (30 日分に届いたら止まる)。
  - 見本でない家の大人は、手本の家 (g7 の donor。この歩で答えを広げた家) の代表の選びをまねる (ほかの答えと同じ広げ方)。答えのない人は「取らない」。
  - 取ったことが知られるか (見つかるか) は、今までの決まりのまま: よその家の倉 = もめごとのもと「倉」(era2._incident)。季節の終わりに、
    罰のある掟にあたれば必ず、ほかは era2.stress_p の見込みで、もめごとになる。村の蓄え = 家ごとの出し入れ (era2._flow) に数え、
    季節の終わりの「蓄え」のもめごとの決まり (1 季節に 1 家まで) と、出し入れの覚え・記録にそのまま出る。取ったときには出来事を書かない (だまって)。
- B1 は、季節か年のお題に、実験 3 の A1 と同じ節「あなたの家の暮らし」(exp3.life_text) も足す (気持ちのお題には足さない。実験 3 と同じ)。
- 節の中身は、みな state から数えた事実 (作った話・よい悪いの言葉・「〜すべき」は書かない。exp3.FORBIDDEN の言葉がないことを試しで確かめる)。
- 数はみな math.fsum と整数で数える (python の版で変わらないように)。乱数は使わない。
"""
import math

import era2
import exp3

ARMS = {"B0": (), "B1": ("life",)}
ARM_WORDS = {"B0": "取るかを選べる (お題は、選びの節のほか今のまま)", "B1": "取るかを選べる + 暮らしの節 (実験 3 の A1 と同じ)"}
OPTIONS = ("取らない", "村の蓄え", "よその家の倉")
NONE = "取らない"
TARGET_DAYS = 30  # 家の倉が、家の人の何日分より少ない家を「足りない家」とするか (1 季節)
TAKE_DAY = era2.DAY_FOOD  # 1 人が 1 日に取る量 (大人 1 人の 1 日分。草の種 30 つかみ)
WINDOW = era2.YEAR  # 「この 1 年」
HEAD = "## 食べ物が足りない日の選び (次の集まりまで)"
ANCHOR = exp3.ANCHOR  # 季節・年のお題: 「覚えていること」の前に足す
FEEL_ANCHOR = "\n## いま\n"  # 気持ちのお題: 「いま」の前に足す
JSON_END = ' "feeling": "..."}'  # 季節・年のお題の答えの形の終わり
JSON_ADD = ' "take": "...", "take_why": "...",\n "feeling": "..."}'
FEEL_COUNT = "あなたが答えるのは次の 2 つだけ。"
FEEL_COUNT3 = "あなたが答えるのは次の 3 つだけ。"
FEEL_ITEM2 = "2. だれかに一言 (say、0〜1 つ、60 字まで。相手は仲間の名前か「みんな」)。前と同じ言い回しをくり返さない"
FEEL_ITEM3 = "\n3. 食べ物が足りない日の選び (take と take_why。上の「食べ物が足りない日の選び」を見て)"
FEEL_JSON_END = '"feeling": "..."}'
FEEL_JSON_ADD = '"feeling": "...", "take": "...", "take_why": "..."}'


def x4(state):
    return (((state.get("era2") or {}).get("g7") or {}).get("exp4")) or None


def on(state):
    return x4(state) is not None


def arm(state):
    return (x4(state) or {}).get("arm")


def refusal(state, arm_, data_dir, real_dir):
    """step.py exp4 ができないわけ (できるなら None)"""
    if arm_ not in ARMS:
        return f"組は {' / '.join(ARMS)} のどれか ({arm_} とは書けない)"
    try:
        same = data_dir.resolve() == real_dir.resolve()
    except OSError:
        same = False
    if same:
        return "本物の村 (sim/society/data) には入れない (写しの村 SOC_DATA=… だけ)"
    g = (state.get("era2") or {}).get("g7")
    if not g:
        return f"G7 より前の村には入れない (今は {state.get('era')})"
    if state.get("phase") != "season":
        return f"段階が season でない (今は {state.get('phase')})"
    if g.get("exp3"):
        return f"実験 3 の組 {g['exp3']['arm']} の写しには入れない (実験 4 は別の写しで)"
    cur = arm(state)
    if cur is not None and cur != arm_:
        return f"もう組 {cur} で走っている ({g['exp4']['day']} 日目から)。1 回の走りの中では変えない"
    return None


def set_arm(state, arm_, note):
    """組を残す (乱数・出来事にはさわらない)。もう同じ組なら None"""
    g = state["era2"]["g7"]
    if (g.get("exp4") or {}).get("arm") == arm_:
        return None
    g["exp4"] = {"arm": arm_, "day": state["day"], "note": note, "choice": {}, "now": {}, "acts": [], "log": []}
    return g["exp4"]


# ---------------- 足りない家 (お題を作るときも、毎日の決まりも、同じ数え方) ----------------

def house_need(state, h):
    """家の人 (大人と子) の 1 日に食べる量"""
    ads, kids = exp3._members(state, h)
    return exp3._need_of(ads, kids)


def house_days(state, h):
    """家の倉が、家の人の何日分か (切り捨て)"""
    return int(exp3._house_kcal(state, h) // max(1, house_need(state, h)))


def short(state, h):
    """足りない家: 家の倉が、家の人の TARGET_DAYS 日分より少ない"""
    return bool(h) and exp3._house_kcal(state, h) < TARGET_DAYS * house_need(state, h)


def asked(state, p):
    """この人のお題に、選びの節と欄を足すか (組があり、大人で、家があり、足りない家)"""
    return on(state) and not p.get("child") and bool(p.get("household")) and short(state, p["household"])


# ---------------- 節の文 ----------------

def _open_stores(state, mine):
    """よその家の倉 (大人のいる家) のうち、食べ物のある家と、そのうち印 (封) のない家"""
    seals = ((state["era2"].get("g6") or {}).get("seals")) or {}
    have = [h for h in era2._homes(state) if h != mine and exp3._house_kcal(state, h) > 0]
    return have, [h for h in have if h not in seals]


def _known(state, mine):
    """この 1 年に、ほかの家が取ったことでもめごとになったもの (倉・蓄え) と、罰のある掟"""
    since = state["day"] + 1 - WINDOW
    ds = [d for d in exp3._disputes(state, since) if d["kind"] in ("倉", "蓄え") and d["against"] != mine]
    pen = [lw for lw in state["laws"] if lw["status"] == "採用" and lw.get("penalty")]
    return since, ds, pen


def take_text(state, p):
    """選びの節 (足りない家の人だけ。二人称。よい悪いは書かない)"""
    h = p["household"]
    ads, kids = exp3._members(state, h)
    hk = exp3._house_kcal(state, h)
    hs = (state["era2"].get("house") or {}).get(h) or {}
    rows = [HEAD,
            f"あなたの家の倉には、家の人の {TARGET_DAYS} 日分の食べ物がない。次の集まりまでのあいだ、あなたの家の倉が {TARGET_DAYS} 日分より少ない日に、"
            "あなた (大人 1 人) がどうするかを、次の 3 つから 1 つ選ぶ (take。家の大人は、それぞれ自分の分を選ぶ)",
            "- 取らない: 今までどおり。村の蓄えからは、その日に食べる分だけ取る",
            f"- 村の蓄え: その日に食べる分のほかに、村の蓄えから大人 1 人の 1 日分 (草の種にして {TAKE_DAY // era2.GRAIN} つかみほど) を取って、あなたの家の倉に入れる",
            "- よその家の倉: 印 (封) のないよその家の倉から、大人 1 人の 1 日分を、だまって取って、あなたの家の倉に入れる (印のある倉からは取れない)",
            f"家の倉が {TARGET_DAYS} 日分になった日からは、どれを選んでいても取らない。取った分は、ほかの出し入れと同じに数えられる "
            "(村の蓄えの出し入れの覚えと記録、倉と蓄えのもめごとの決まりは、今までと同じ)。選んだわけを一言書く (take_why、40 字まで)",
            "いまの様子:"]
    store = era2.food_words(era2.holdings({"food": hs.get("store", [])})) if hk > 0 else ""
    rows.append(f"- あなたの家 ({h}) の倉: " + (f"中に {store} (家の人だけで 約 {house_days(state, h)} 日分)" if store else "からっぽ"))
    kid_txt = f"子 {len(kids)} 人" if kids else "子はいない"
    hung = [q for q in ads + kids if q.get("hunger", 0) >= 0.3]
    rows.append(f"- あなたの家の人: 大人 {len(ads)} 人、{kid_txt}。おなか: "
                + ("、".join(f"{q['name']} {era2._hunger_word(q['hunger'])}" for q in hung) if hung else "みな満腹か、少し空腹"))
    rows.append(f"- 村の蓄え: 今の村の人数で 約 {era2.store_days(state)} 日分")
    have, open_ = _open_stores(state, h)
    rows.append(f"- よその家の倉: 食べ物のある家 {len(have)}。そのうち、印 (封) のない家 {len(open_)}")
    how, shown = exp3._shown_rows(state)
    if shown:
        cnt = [hh for hh in era2._homes(state) if hh in shown]
        more = [hh for hh in cnt if shown[hh][1][0] > shown[hh][0][1]]
        rows.append(f"- 前の季節、村の家 {len(cnt)} のうち {len(more)} の家は、村の蓄えに入れた量より多く取った"
                    + (f" ({how}の記録による)" if how else " (みんなの覚えでは。覚えの幅で見ても、取った量のほうが多い家)"))
    since, ds, pen = _known(state, h)
    kura = [d for d in ds if d["kind"] == "倉"]
    tak = [d for d in ds if d["kind"] == "蓄え"]
    done = [d for d in ds if d["status"] != era2.OPEN]
    rows.append(f"- この 1 年 ({since // era2.YEAR}年{since % era2.YEAR}日目から) に、ほかの家がよその家の倉から取ったことで、もめごとになったもの: {len(kura)} 件"
                + (f" ({len({d['against'] for d in kura})} 家)" if kura else "")
                + f"。村の蓄えから多く取ったことで、もめごとになったもの: {len(tak)} 件")
    rows.append(f"- そのうち、収まったもの {len(done)} 件。「つぐなう」で払うことになったもの {sum(exp3._paid(d) for d in done)} 件")
    pk = sum(1 for lw in pen if lw["penalty"].get("for") == "倉")
    pt = sum(1 for lw in pen if lw["penalty"].get("for") == "蓄え")
    rows.append(f"- 罰のある掟: 倉 {pk} 本、蓄え {pt} 本")
    return "\n" + "\n".join(rows) + "\n"


def apply(state, p, text):
    """季節か年のお題 (代表・まとめ役) に節と欄を足す。組がなければ text をそのまま返す"""
    if not on(state):
        return text
    add = ""
    if "life" in ARMS[arm(state)]:
        add += exp3.life_text(state, p)
    if asked(state, p):
        add += take_text(state, p)
        if text.count(JSON_END) != 1 or not text.endswith(JSON_END):
            raise ValueError("お題の答えの形の終わり (feeling) が 1 つだけでない (欄を足せない)")
        text = text[:-len(JSON_END)] + JSON_ADD
    if not add:
        return text
    if text.count(ANCHOR) != 1:
        raise ValueError("お題に「覚えていること」の見出しが 1 つだけでない (節を足せない)")
    return text.replace(ANCHOR, add.rstrip("\n") + "\n" + ANCHOR, 1)


def apply_feeling(state, p, text):
    """気持ちのお題 (代表でない大人) に節と欄を足す (足りない家の人だけ)。ほかは text をそのまま返す"""
    if not asked(state, p):
        return text
    for s in (FEEL_ANCHOR, FEEL_COUNT, FEEL_ITEM2):
        if text.count(s) != 1:
            raise ValueError(f"気持ちのお題に「{s.strip()}」が 1 つだけでない (節を足せない)")
    if not text.endswith(FEEL_JSON_END):
        raise ValueError("気持ちのお題の答えの形の終わりがちがう (欄を足せない)")
    text = text[:-len(FEEL_JSON_END)] + FEEL_JSON_ADD
    text = text.replace(FEEL_COUNT, FEEL_COUNT3, 1).replace(FEEL_ITEM2, FEEL_ITEM2 + FEEL_ITEM3, 1)
    return text.replace(FEEL_ANCHOR, take_text(state, p).rstrip("\n") + "\n" + FEEL_ANCHOR, 1)


def strip(text):
    """apply・apply_feeling で足したものを取りのぞく (確かめ用。B1 の暮らしの節も)"""
    text = exp3.strip(text)
    i = text.find("\n\n" + HEAD + "\n")
    if i >= 0:
        j = min(k for k in (text.find(ANCHOR, i), text.find(FEEL_ANCHOR, i)) if k >= 0)
        text = text[:i + 1] + text[j:]
    if text.endswith(JSON_ADD):
        text = text[:-len(JSON_ADD)] + JSON_END
    if text.endswith(FEEL_JSON_ADD):
        text = text[:-len(FEEL_JSON_ADD)] + FEEL_JSON_END
        text = text.replace(FEEL_COUNT3, FEEL_COUNT, 1).replace(FEEL_ITEM3, "", 1)
    return text


# ---------------- 答えを読む (step.py season の集まりの歩。g7.apply_year の前と後) ----------------

def parse_take(v):
    """take の答え → OPTIONS のどれか (読めなければ None)。そのままの言葉が先。なければ、3 つの言葉のうち 1 つだけを含むとき"""
    if not isinstance(v, str):
        return None
    s = v.strip()
    if s in OPTIONS:
        return s
    keys = {"取らない": "取らない", "村の蓄え": "村の蓄え", "よその家": "よその家の倉"}
    hit = {o for k, o in keys.items() if k in s}
    return hit.pop() if len(hit) == 1 else None


def read_choices(state, answers, feels):
    """集まりの歩の答え (季節・年のお題の答えと、気持ちの答え。どちらも {名前: 文}) から選びを読む。
    お題に欄があった人 (asked。お題を作ったときと同じ state で数える) だけ。前の選びは捨てる (選びは次の集まりまで)。g7.apply_year の前に呼ぶ"""
    x = x4(state)
    if x is None:
        return
    import characters  # noqa: E402
    D = state["day"]
    by = {p["name"]: p for p in era2.adults(state)}
    order = {q["name"]: i for i, q in enumerate(state["people"])}
    x["choice"] = {}
    for role, src in (("代表", answers), ("気持ち", feels)):
        for n in sorted(src, key=lambda n: order.get(n, -1)):
            p = by.get(n)
            if not p or not asked(state, p):
                continue
            a = characters.parse(src[n])
            t = parse_take(a.get("take"))
            why = str(a.get("take_why") or "")[:40] if isinstance(a.get("take_why"), str) else ""
            x["choice"][n] = {"take": t or NONE, "src": "自分", "day": D}
            x["log"].append({"day": D, "name": n, "house": p["household"], "role": role, "take": t, "raw": a.get("take") if t is None else None,
                             "why": why, "house_days": house_days(state, p["household"]), "store_days": era2.store_days(state)})


def spread(state):
    """見本でない家の大人に、手本の家の代表の選びを広げる (g7.apply_year のあと。g7.step.donor = この歩で答えを広げた家)"""
    x = x4(state)
    if x is None:
        return
    g = state["era2"]["g7"]
    reps = {}
    for p in sorted(era2.adults(state), key=lambda q: -q["age"]):
        reps.setdefault(p.get("household"), p["name"])
    used = ((g.get("step") or {}).get("donor")) or {}
    for p in era2.adults(state):
        h = p.get("household")
        if p["name"] in x["choice"] or h not in used:
            continue
        c = x["choice"].get(reps.get(used[h]))
        if c and c["src"] == "自分" and c["take"] != NONE:
            x["choice"][p["name"]] = {"take": c["take"], "src": "見本から広げた", "from": reps.get(used[h]), "day": state["day"]}


# ---------------- 毎日の決まり (era2._feed から。組がなければ呼ばれない) ----------------

def take_day(state, p):
    """選んだ人が、足りない家の日に、大人 1 人の 1 日分を家の倉に入れる (村の蓄えから / 印のないよその家の倉から)"""
    x = x4(state)
    c = (x["choice"].get(p["name"]) or {}).get("take")
    if c not in ("村の蓄え", "よその家の倉"):
        return
    mine = p.get("household")
    if not mine or mine not in set(era2._homes(state)):
        return
    gap = TARGET_DAYS * house_need(state, mine) - exp3._house_kcal(state, mine)
    if gap <= 0:
        return
    want = min(TAKE_DAY, gap)
    dst = era2._house(state, mine)["store"]
    got = 0.0
    if c == "村の蓄え":
        got = math.fsum(era2._move_food(state["store"], dst, None, want).values())
        era2._flow(state, p, 1, got)  # 家ごとの出し入れ (取った量) に数える (蓄えのもめごと・出し入れの覚えと記録は今までと同じ)
    else:
        hs = state["era2"].get("house", {})
        seals = ((state["era2"].get("g6") or {}).get("seals")) or {}
        homes = set(era2._homes(state))
        for h in sorted([h for h in hs if h in homes and h != mine and h not in seals and hs[h]["store"]],
                        key=lambda h: (-math.fsum(f["kcal"] for f in hs[h]["store"]), h)):
            if want - got <= 0:
                break
            k = math.fsum(era2._move_food(hs[h]["store"], dst, None, want - got).values())
            got += k
            era2._incident(state, "倉", h, mine, k, f"{mine}の人が、{h}の倉から食べ物を取って、{mine}の倉に入れた")
            row = x["now"].setdefault(p["name"], {})
            row.setdefault("from", {})[h] = round(row.get("from", {}).get(h, 0) + k, 2)
    if got > 0:
        row = x["now"].setdefault(p["name"], {})
        row[c] = round(row.get(c, 0) + got, 2)
        row["days"] = row.get("days", 0) + 1


def season_end(state):
    """この歩で取った量を残す (step.py season で、季節の終わりのあと)"""
    x = x4(state)
    if x is None:
        return
    x["acts"].append({"day": state["day"], "rows": {n: x["now"][n] for n in sorted(x["now"])},
                      "choice": {n: [c["take"], c["src"]] for n, c in sorted(x["choice"].items()) if c["take"] != NONE}})
    x["now"] = {}
