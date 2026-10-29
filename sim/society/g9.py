"""G9「遠くとの商い」(第 5 部「王と青銅」の終わりの G。2026-10-29 本人の決め。docs/society_phase/G9_design.md)

- G9 に入るのは step.py next_part だけ (G8 を本人の決めで閉じてから。g7.start_g9)。G8 までは、このファイルを読みこみもしない
  (g7・hints・era2 は state の g7.g9 があるときだけ、関数の中で読みこむ)。だから G1〜G8 は、お題・state・出来事・乱数が前と 1 バイトも変わらない
- 条件 (どれも国を要らない。【村が決めた】):
  c1 赤い金属 (青銅) の道具を使う: G9 に入ってから、1 年 (暦の年) に、村の人が赤い金属の道具で仕事 (夕方の刈り入れ) をした日が 30 人日以上
  c2 商人の家: この 1 年に、家の人が交換に行った日が 60 日 (1 年の半分。yardstick.MERCHANT_DAYS) をこえる家が 1 つ以上
  c3 遠くとの約束を書く: 遠くの町の運ぶ人との約束 (いつ・何を・どれだけ替える) を、粘土の板に書いて残した
- F: F1 赤い金属の道具を新しく手に入れる / F2 商人の家 (= c2) / F3 遠くとの約束を書く (= c3) / F4 遠くの相手と、2 回目の約束を守り合う
- G7 の国の物差し (条件 3 つ・F1〜F6) は「ならべて測る」: yardstick がいつもどおり数えて g7.reached・出来事「目盛り」に残すが、G9 は進めない
- 足した仕組み (小さく 4 つ): 遠くの町の運ぶ人 (hints.LAM_FAR = 0.1。2026-10-29 本人の決め「交換しなくても来る」: 前の年に村が交換をしなくても来る。
  約束の流れは 1 つだけ: 約束が続いているあいだに来た別の運ぶ人とは、その場で替えるか替えないかだけ (once))・赤い金属の道具の使い道 (刈り入れ)・
  約束を粘土の板に書く・まわりの集落の同盟を、村が知っていれば出来事に残す (g7._region_after)
- 乱数: 約束を書かなかったときの覚えのずれだけ。ほかの列 (塩) にはさわらない (約束ごとに seed から作る)
- 数はみな【仮定】。村の人に見せる文には「青銅」を書かない (hints.FORBIDDEN)。村の中の呼び名は「赤い金属」
"""
import math
import random

import era2
import hints
import yardstick
from world import log, season

YEAR, SEASON_DAYS = era2.YEAR, era2.SEASON_DAYS
FAR, FAR_WORD = hints.FAR, hints.FAR_WORD
TOOL = "赤い金属の鎌"  # 遠くの町の運ぶ人が出す道具 (錫の青銅の鎌)【仮定】
BRONZE_THINGS = ("赤い金属の刃", TOOL)  # 村が持つ赤い金属の道具 (67年の刃は H8-01 の「もの」。g7.hints.things)
FAR_TOOLS = 2  # 運ぶ人が 1 回に出す道具の数【仮定】
FAR_PRICE = 800  # 道具 1 つの値 (草の種のつかみ)。石の鎌 (75) の 10 倍ほど【仮定】
BRONZE_REAP = 2.5  # 赤い金属の道具で刈ると、刈る量は 2.5 倍 (石の鎌は 2 倍)【仮定】「少し速く」
BRONZE_LIFE = 600  # 使った人日がこれだけになると、すり減って使えなくなる (石の鎌は 1 季節に 5% 割れる)【仮定】「こわれにくい」
C1_DAYS = 30  # c1: 1 年に、赤い金属の道具で仕事をした人日
MERCHANT_DAYS = yardstick.MERCHANT_DAYS  # c2: 1 年に交換に行った日がこれをこえる家 (60 日)
FAR_SPREAD = 0.3  # 約束を書かなかったとき、覚えのずれ (運ぶ人は 1〜1.3 倍、村は 0.7〜1 倍に覚える)【仮定】
FAR_BLAME = era2.BLAME  # 運ぶ人の覚えが、村の覚えの 1.25 倍をこえると、言い争いになって替えない (貸し借りの覚えと同じ目安)
USE_CHOICES = ("使う", "しまう")
FAR_CHOICES = ("約束する", "受けない", "受ける")  # 読む順 (「受けない」を「受ける」より先に見る)
WRITE_CHOICES = ("書かない", "書く")
FS = {"F1": "赤い金属の道具を新しく手に入れる", "F2": "商人の家", "F3": "遠くとの約束を書く", "F4": "遠くの相手と、2 回目の約束を守り合う"}
CS = {"c1": "赤い金属の道具を使う", "c2": "商人の家", "c3": "遠くとの約束を書く"}


def on(state):
    return "g9" in ((state.get("era2") or {}).get("g7") or {})


def _g(state):
    return state["era2"]["g7"]["g9"]


def _gw(goods):
    return "・".join(f"{k} {n} {'本' if k in BRONZE_THINGS else era2.UNIT.get(k, '')}".rstrip() for k, n in goods.items())


# ---------------- G9 に入る (g7.start_g9 から) ----------------

def start(state):
    """G9 の state を作る。村がもう持っている赤い金属の道具 (67年の刃) を道具の一覧に入れ、札の表のハッシュを新しくする (G9 の 2 枚。出来事「区切り」)"""
    g7s, D = state["era2"]["g7"], state["day"]
    h = g7s.get("hints") or {}
    g = g7s["g9"] = {"start": D, "tools": [], "next_tool": 1, "use": {"choice": "しまう", "day": None, "votes": ""}, "used": {},
                     "offers": [], "next_offer": 1, "promises": [], "next_promise": 1, "deals": [], "visits": [],
                     "reached": {}, "c": {}, "seen_things": 0, "merchant": {}, "kept": 0, "offer_log": []}
    _sync_things(state, new=False)
    if h:
        sha = hints.cards_sha(state)
        h["cards_sha"] = sha
        h.setdefault("cards_log", []).append({"day": D, "sha": sha, "note": "G9 に入った日: 遠くの商人の札 2 枚 (H8-04・H8-05)"})
        log(state, "区切り", None, "よその便りの札の表に 2 枚を足した (G9 に入った日)", cards=sha)
    return g


def _sync_things(state, new=True):
    """よその便りの商人から受けとった「もの」(g7.hints.things) のうち、赤い金属の道具を道具の一覧に入れる"""
    g = _g(state)
    things = ((state["era2"]["g7"].get("hints") or {}).get("things") or [])
    for t in things[g["seen_things"]:]:
        if t.get("thing") in BRONZE_THINGS:
            _add_tool(state, t["thing"], t["day"], t.get("from"), t.get("side", "村"), new)
    g["seen_things"] = len(things)


def _add_tool(state, name, day, frm, side, new):
    g = _g(state)
    tid = f"B{g['next_tool']}"
    g["next_tool"] += 1
    g["tools"].append({"id": tid, "name": name, "day": day, "from": frm, "side": side, "uses": 0, "gone": None, "new": bool(new)})
    if new and day >= g["start"]:
        _reach(state, "F1", day, f"{name} を手に入れた [{tid}]")
    return tid


def tools(state):
    """使える赤い金属の道具 (すり減っていないもの)"""
    return [t for t in _g(state)["tools"] if t["gone"] is None]


# ---------------- 遠くの町の運ぶ人の来る見込み (本人の決め 2026-10-29「来る見込みを 5 割に」。step.py far_rate) ----------------

FAR_RATE_MAX = 1.0  # step.py far_rate で書ける重みの上 (0 より大きく、これ以下)


def far_rate_refusal(state, rate):
    """step.py far_rate ができないわけ (できるなら None)"""
    if not on(state) or state.get("era") != "G9":
        return f"遠くの町の運ぶ人の見込みは G9 のときだけ (今は {state.get('era')})"
    if state["phase"] != "season":
        return f"段階が season でない (今は {state['phase']})"
    if not (0 < rate <= FAR_RATE_MAX):
        return f"重みは 0 より大きく {FAR_RATE_MAX} 以下 ({rate} とは書けない)"
    return None


def set_far_rate(state, rate, note):
    """遠くの町の運ぶ人の重み (1 年の見込み) を、今日から rate にする (step.py far_rate から。乱数は世界の列にはさわらない)。
    g7.g9.far_rate に {日・重み・前の重み・本人の決め} を残し、出来事「目盛り」(【シ】。村の人には見せない) を書く。
    次の年の便りは年の終わりの日に引く (hints._year_plan)。今日がその日で、村の分をもう前の重みで引いていれば、重みの差だけ遠くの商人を引き足す
    (hints.far_topup)。ほかの日なら、次の年の終わりに引くときから新しい重み。戻り値: 残した行 (同じ重みなら None = 何も変えない)"""
    g, D = _g(state), state["day"]
    was = hints.far_weight(state)
    if rate == was:
        return None
    row = {"day": D, "rate": rate, "was": was, "by": "本人の決め", "note": note}
    lam = [x for x in state["era2"]["g7"]["hints"]["lam"] if x["day"] == D and x["to"] == "V0"]
    base = [w for x in lam if not x.get("far_rate") for c, w, f in x["terms"] if f == FAR]
    if base:  # 今日、次の年の村の分をもう引いた: 引いた遠くの商人の重み (前に引き足した分もふくむ) との差だけ引き足す (下げるときは引き足さない)
        extra = round(rate - base[0] - sum(x["lam"] for x in lam if x.get("far_rate")), 6)
        if extra > 0:
            t = hints.far_topup(state, extra)
            ys = [r["y"] for r in state["era2"]["g7"]["hints"]["ledger"] if r.get("far_rate") and r["drawn"] == D]
            row["topup"] = {"lam": t["lam"], "n": t["n"], "rows": ys[len(ys) - t["n"]:]}
    g.setdefault("far_rate", []).append(row)
    log(state, "目盛り", None, f"作る側: 遠くの町の運ぶ人の 1 年の見込み (重み) を {was} から {rate} にした ({note})"
        + (f"。この日に引いた次の年の分に、差 {row['topup']['lam']} で遠くの商人を引き足した ({row['topup']['n']} 人)" if row.get("topup") else ""),
        far_rate=rate, was=was)
    return row


# ---------------- 赤い金属の道具を使う (era2._day の夕方の刈り入れ) ----------------

def tools_for_day(state):
    """その日に夕方の刈り入れで使う道具 (村が「使う」と決めているときだけ。番号の順)。G8 までは呼ばない"""
    if _g(state)["use"]["choice"] != "使う":
        return []
    return tools(state)


def reap(state, p, tool, n):
    """赤い金属の道具で刈る (1 人 1 日 1 つ): 刈る量は 2.5 倍。使った人日を数える (c1)"""
    g, y = _g(state), str(state["day"] // YEAR)
    tool["uses"] += 1
    g["used"][y] = g["used"].get(y, 0) + 1
    return n * 5 // 2


# ---------------- 遠くの町の運ぶ人 (hints._deliver_v0 から) ----------------

def traded(state, lo, hi):
    """前の年 [lo, hi] に、村が交換をしたか (2026-10-29 本人の決め「交換しなくても来る」からは、遠くの運ぶ人が来るかには使わない。試しと記録のため残す) (ほかの村との交換・貸し借り・返す (G6 の contacts) と、遠くの町の運ぶ人との取り替え)"""
    for o in (state["era2"].get("g6") or {}).get("others", []):
        if any(lo <= c <= hi for c in o.get("contacts", [])):
            return True
    return any(lo <= d <= hi for d in _g(state)["deals"])


def flow(state, skip=None):
    """いま続いている約束の流れ (2026-10-29 本人の決め: 流れは 1 つだけ)。待っている約束の番号か、守り合ったあとの次の申し出 (まだ答えていないもの) が
    約束した番号。なければ None。skip: 集まりでいま答えている申し出 (それ自身は数えない)"""
    g = _g(state)
    p = next((pr["id"] for pr in g["promises"] if pr["status"] == "待つ"), None)
    return p or next((o["after"] for o in g["offers"] if o.get("after") and o is not skip and "end" not in o), None)


def far_arrive(state, r=None, promise=None):
    """遠くの町の運ぶ人が、赤い金属の鎌との取り替えを申し出る (次の村の集まりまで待つ)。r: よその便りの帳簿の行、promise: 約束どおり来たとき。
    約束の流れが続いているあいだに来た別の運ぶ人 (promise なし) は、その場で替えるだけ (once。約束はできない。2026-10-29 本人の決め)"""
    g, D = _g(state), state["day"]
    once = flow(state) if promise is None else None
    oid = f"M{g['next_offer']}"
    g["next_offer"] += 1
    off = {"id": oid, "day": D, "give": {TOOL: FAR_TOOLS}, "want": {"草の種": FAR_TOOLS * FAR_PRICE}, "hint": (r or {}).get("y"), "after": promise}
    if once:
        off["once"] = once
    g["offers"].append(off)
    g["visits"].append({"day": D, "offer": oid, "hint": off["hint"], "promise": promise, **({"once": once} if once else {})})
    log(state, "よその村", None, f"{FAR_WORD}は、{_gw(off['give'])} を出すので、{_gw(off['want'])} がほしいと言った。"
        f"次の村の集まりまで待つという [{oid}]" + ("。村はもう、遠くの町の別の運ぶ人と約束をしているので、この運ぶ人とは、その場で替えるか替えないかだけを決める" if once else ""),
        far=True, offer=oid, **({"hint": off["hint"]} if off["hint"] else {}), **({"once": once} if once else {}))
    return off


def _votes(state, real, key, choices, per=None):
    """答えの key (per があれば、その番号の答え) を、手の言葉で読み、広げた票で 1 つにする (g7._tally)"""
    import g7
    w = g7._vote_weights(state, real)
    votes = {}
    for n, a in real.items():
        v = a.get(key)
        if per is not None:
            v = next((x for k, x in (v.items() if isinstance(v, dict) else []) if f"M{era2._num(k)}" == per), None)
        if v is True:
            v = choices[-1]
        elif v is False:
            v = choices[0] if key == "far_write" else "受けない" if key == "far" else "しまう"
        s = str(v or "").strip()
        ch = next((c for c in choices if s and c in s), None)
        if ch:
            votes[n] = ch
    return g7._tally(state, votes, w)


def apply_answers(state, real):
    """集まりの歩の答え (g7.apply_year から): 赤い金属の道具を使うか (metal)・遠くの町の運ぶ人の申し出 (far)・約束を板に書くか (far_write)"""
    g, D = _g(state), state["day"]
    at = "季節の集まりで"
    ch, txt = _votes(state, real, "metal", USE_CHOICES)
    if ch and tools(state):
        if ch != g["use"]["choice"]:
            log(state, "道具", None, f"{at}、村の赤い金属の道具を" + ("、夕方に畑を刈る人が使うことにした" if ch == "使う" else "使わず、しまっておくことにした") + f" ({txt})",
                metal=ch)
        g["use"] = {"choice": ch, "day": D, "votes": txt}
    wait = []
    for off in g["offers"]:
        ch, txt = _votes(state, real, "far", FAR_CHOICES, per=off["id"])
        if not ch:
            log(state, "よその村", None, f"{at}、{FAR_WORD}の申し出 [{off['id']}] には答えがなく、運ぶ人は帰っていった", far=True, offer=off["id"])
            off["end"] = [D, "答えなし"]
            continue
        if ch == "受けない":
            log(state, "よその村", None, f"{at}、{FAR_WORD}の申し出 [{off['id']}] は受けなかった ({txt})。運ぶ人は帰っていった", far=True, offer=off["id"])
            off["end"] = [D, "受けない"]
            continue
        if any(era2._g6_have(state, "村", k) < m for k, m in off["want"].items()):
            log(state, "よその村", None, f"{at}、{FAR_WORD}の申し出 [{off['id']}] を受けようとしたが、村の蓄えに {_gw(off['want'])} がなかった。運ぶ人は帰っていった",
                far=True, offer=off["id"])
            off["end"] = [D, "物がない"]
            continue
        once = ""
        if ch == "約束する" and (off.get("once") or flow(state, skip=off)):  # 約束の流れは 1 つだけ (2026-10-29 本人の決め): その場で替えるだけにする
            ch, once = "受ける", "。この運ぶ人とは約束しなかった (村はもう、遠くの町の別の運ぶ人と約束をしている)。その場で替えるだけにした"
        write = None
        if ch == "約束する":
            wc, wtxt = _votes(state, real, "far_write", WRITE_CHOICES)
            write = wc == "書く" and bool(((state["era2"].get("g6") or {}).get("open") or {}).get("板"))
        ids = []
        gave = era2._g6_take(state, "村", off["want"], ids)
        tids = [_add_tool(state, TOOL, D, FAR, "村", True) for _ in range(off["give"][TOOL])]
        g["deals"].append(D)
        extra = once
        pid = None
        if ch == "約束する":
            pid = _promise(state, off, write)
            extra = (f"。次に来るとき (1 年あと、{season(D + 1)}のはじめ) にも、同じように替えると約束した [{pid}]。"
                     + ("約束は粘土の板に書いて残した" if write else "約束は書かず、覚えておくことにした"))
        log(state, "交換", None, f"{at}、村は、村の物で {FAR_WORD}の申し出 [{off['id']}] を受け、{_gw(gave)} を {_gw(off['give'])} と取り替えた ({txt}){extra}",
            far=True, offer=off["id"], moves=[era2._mv("村", -1, gave, ids)], tools=tids, **({"promise": pid, "written": write} if pid else {}))
        off["end"] = [D, ch]
        if write:
            _reach(state, "F3", D, f"遠くの町の運ぶ人との約束 [{pid}] を粘土の板に書いた")
    g.setdefault("offer_log", []).extend(o for o in g["offers"] if o not in wait)
    g["offers"] = wait


def _promise(state, off, write):
    g, D = _g(state), state["day"]
    pid = f"P{g['next_promise']}"
    g["next_promise"] += 1
    rng = random.Random(state["seed"] * 7919 + D * 13 + g["next_promise"])  # 覚えのずれ (約束ごと。ほかの乱数の列にはさわらない)
    g["promises"].append({"id": pid, "offer": off["id"], "day": D, "due": D + YEAR, "give": dict(off["give"]), "want": dict(off["want"]),
                          "written": bool(write), "status": "待つ", "end": None,
                          "mem": {"village": round(rng.uniform(1 - FAR_SPREAD, 1), 3), "merchant": round(rng.uniform(1, 1 + FAR_SPREAD), 3)}})
    return pid


def _due(state):
    """約束の日が来た約束: 運ぶ人がまた来る (集まりで決めずに、約束どおり替える)。守り合えたら、また申し出る"""
    g, D = _g(state), state["day"]
    for pr in g["promises"]:
        if pr["status"] != "待つ" or pr["due"] > D:
            continue
        want = pr["want"]["草の種"]
        if pr["written"]:
            ask, mine, how = want, want, "粘土の板を読み合わせて"
        else:
            ask, mine, how = math.ceil(want * pr["mem"]["merchant"]), math.floor(want * pr["mem"]["village"]), "覚えで"
        head = f"{FAR_WORD}が、約束 [{pr['id']}] のとおり、また来た"
        if ask > mine * FAR_BLAME:
            pr.update(status="ちがっていた", end=D)
            log(state, "覚え", None, f"{head}。運ぶ人は 草の種 {ask} つかみ と覚えていたが、村の覚えでは 草の種 {mine} つかみ だった (記録はない)。"
                "言い合いになり、取り替えずに帰っていった", far=True, promise=pr["id"])
            continue
        if era2._g6_have(state, "村", "草の種") < ask:
            pr.update(status="村が守れなかった", end=D)
            log(state, "よその村", None, f"{head}。けれども村の蓄えに 草の種 {ask} つかみ がなく、約束は守れなかった。運ぶ人は帰っていった",
                far=True, promise=pr["id"])
            continue
        ids = []
        gave = era2._g6_take(state, "村", {"草の種": ask}, ids)
        tids = [_add_tool(state, TOOL, D, FAR, "村", True) for _ in range(pr["give"][TOOL])]
        g["deals"].append(D)
        pr.update(status="守られた", end=D, paid=ask)
        g["kept"] += 1
        log(state, "確かめる" if pr["written"] else "交換", None, f"{head}。{how}、{_gw(gave)} を {_gw(pr['give'])} と取り替えた",
            far=True, promise=pr["id"], moves=[era2._mv("村", -1, gave, ids)], tools=tids)
        if g["kept"] >= 2:
            _reach(state, "F4", D, f"遠くの町の運ぶ人と、約束を {g['kept']} 回守り合った")
        far_arrive(state, promise=pr["id"])


def _wear(state):
    for t in tools(state):
        if t["uses"] >= BRONZE_LIFE:
            t["gone"] = state["day"]
            log(state, "道具", None, f"村の{t['name']} [{t['id']}] は、すり減って使えなくなった", tool=t["id"])


# ---------------- 物差し (乱数なし) ----------------

def trip_days(state):
    """この 1 年に、家ごとに、家の人が交換に行った日 (G6 の旅の記録。yardstick._ahead と同じ数え方)"""
    e2, D = state["era2"], state["day"]
    days = {}
    for tr in (e2.get("g6") or {}).get("trip_log", []):
        if tr.get("start") is not None and tr["start"] > D - YEAR:
            h = yardstick._home(state, tr["who"])
            if h:
                days[h] = days.get(h, 0) + ((tr.get("end") or tr["start"]) - tr["start"] + 1)
    return days


def _reach(state, f, day, why):
    g = _g(state)
    if f in g["reached"] or day is None:
        return
    g["reached"][f] = day
    log(state, "目盛り", None, f"目盛り: G9 の {f}「{FS[f]}」に届いた ({why})", g="G9", f=f)
    for c, ff in (("c2", "F2"), ("c3", "F3")):
        if f == ff:
            _cond(state, c, day, why)


def _cond(state, c, day, why):
    g = _g(state)
    if c not in g["c"]:
        g["c"][c] = day
        log(state, "目盛り", None, f"目盛り: G9 の条件 {c[1:]}「{CS[c]}」に届いた ({why})", g="G9", c=c)


def season_end(state):
    """G9 の季節の終わり (g7.season_end の、よその便りのあと・物差しの前): もの → 約束の日 → すり減り → c1・c2"""
    g, D = _g(state), state["day"]
    _sync_things(state)
    _due(state)
    _wear(state)
    n = g["used"].get(str(D // YEAR), 0)
    if n >= C1_DAYS:
        _cond(state, "c1", D, f"この年に、赤い金属の道具で仕事をした人日が {n}")
    days = trip_days(state)
    g["merchant"] = {"day": D, "max": max(days.values(), default=0), "households": {h: n for h, n in sorted(days.items())}}
    hit = sorted(h for h, n in days.items() if n > MERCHANT_DAYS)
    if hit:
        _reach(state, "F2", D, f"交換に行った日が 1 年に {MERCHANT_DAYS} 日をこえた家: {'・'.join(hit)}")


def reached(state, f):
    return bool(on(state) and _g(state)["reached"].get(f))


def progress(state):
    """条件ごとの進み (止まりを数える。yardstick._stall が G9 で読む)。c1: 0 道具がない / 1 道具がある / 2 使った / 3 届いた。
    c2: 0 交換に行った家がない / 1 ある / 2 30 日をこえた家がある / 3 届いた。c3: 0 運ぶ人が来ていない / 1 来た / 2 約束した / 3 書いた"""
    g = _g(state)
    c1 = 3 if "c1" in g["c"] else 2 if any(g["used"].values()) else 1 if tools(state) else 0
    mx = (g.get("merchant") or {}).get("max", 0)
    c2 = 3 if "c2" in g["c"] else 2 if mx > MERCHANT_DAYS // 2 else 1 if mx > 0 else 0
    c3 = 3 if "c3" in g["c"] else 2 if g["promises"] else 1 if g["visits"] else 0
    return {"c1": c1, "c2": c2, "c3": c3}


def done(state):
    return {c: c in _g(state)["c"] for c in CS}


def indicators(state):
    """G9 の目安 (era2.indicators に足す。【シ】)"""
    g = _g(state)
    return {"g9_c1_day": g["c"].get("c1"), "g9_c2_day": g["c"].get("c2"), "g9_c3_day": g["c"].get("c3"), "g9_tools": len(tools(state)),
            "g9_use": g["use"]["choice"], "g9_used_year": g["used"].get(str(state["day"] // YEAR), 0), "g9_far_visits": len(g["visits"]),
            "g9_promises": len(g["promises"]), "g9_flow": flow(state), "g9_written": sum(1 for p in g["promises"] if p["written"]), "g9_kept": g["kept"],
            "g9_trip_days_max": (g.get("merchant") or {}).get("max", 0)}


# ---------------- お題 ----------------

def facts(state):
    """お題の決まりの文 (G9 から)"""
    tab = bool(((state["era2"].get("g6") or {}).get("open") or {}).get("板"))
    return ("遠くの町の運ぶ人: ときどき、地図の外の遠くの町から運ぶ人が来る (村がほかの村と交換をしていなくても来る)。赤い金属の鎌を出して草の種と替えたいと言い、"
            "次の村の集まりまで待つ。集まりで、受ける・受けない・約束する (いま替えて、1 年あとに、また同じように替える) を決める。約束すると、運ぶ人は 1 年あとに"
            "また来て、集まりで決めずに約束どおり替える。そのとき村の蓄えに草の種がなければ、約束は守れない。約束できるのは、1 人の運ぶ人とだけ。"
            "約束が続いているあいだに別の運ぶ人が来たら、その運ぶ人とは、その場で替えるか替えないかだけを決める"
            + ("。約束を粘土の板に書いておけば、来たときに板を読み合わせられる。書かなければ、覚えで比べる (覚えは、人によってずれる)" if tab else "") + "\n"
            "赤い金属の道具: 赤い金属の刃や鎌で畑を刈ると、刈る量が 2.5 倍になる (石の鎌は 2 倍)。石の鎌より、ずっとすり減りにくい。"
            "村の集まりで「使う」と決めると、夕方に畑を刈る人が使う (道具の数の人まで)。「しまう」と決めると使わない\n")


def text(state, p):
    """お題の節「## 遠くの町の運ぶ人・赤い金属の道具」(G9 から。申し出・約束・道具があるときだけ)"""
    g, D = _g(state), state["day"]
    rows = []
    for off in g["offers"]:
        rows.append(f"- 申し出 [{off['id']}] ({off['day']} 日目に来た): {_gw(off['give'])} を出すので、{_gw(off['want'])} がほしい"
                    + (f" (約束 [{off['after']}] を守り合ったあとの、次の申し出)" if off.get("after") else "")
                    + (" (村はもう別の運ぶ人と約束をしているので、この運ぶ人とは約束できない。受けるか受けないかだけ)" if off.get("once") else ""))
    for pr in g["promises"]:
        if pr["status"] == "待つ":
            rows.append(f"- 約束 [{pr['id']}] ({pr['day']} 日目): {pr['due']} 日目 ({season(pr['due'] + 1)}のはじめ) ごろに運ぶ人がまた来て、"
                        + (f"{_gw(pr['want'])} を {_gw(pr['give'])} と替える (粘土の板に書いてある)" if pr["written"] else
                           f"村の覚えでは 草の種 {math.floor(pr['want']['草の種'] * pr['mem']['village'])} つかみ ほどを {_gw(pr['give'])} と替える (書いていない)"))
        elif pr["end"] is not None and D - pr["end"] < YEAR:
            rows.append(f"- 約束 [{pr['id']}]: {pr['end']} 日目に{'守り合った' if pr['status'] == '守られた' else pr['status']}")
    ts = tools(state)
    if ts:
        rows.append("- 村の赤い金属の道具: " + "・".join(f"{t['name']} [{t['id']}]" for t in ts)
                    + f"。いまは「{g['use']['choice']}」と決まっている" + (f" ({g['use']['day']} 日目の集まり)" if g["use"]["day"] is not None else ""))
    if not rows:
        return ""
    return "\n## 遠くの町の運ぶ人・赤い金属の道具\n" + "\n".join(rows) + "\n"


def field_rows(state):
    """答えの欄 (g7._field_rows に足す)"""
    rows = []
    if tools(state):
        rows.append('   赤い金属の道具: 次の集まりまで、夕方に畑を刈る人が "使う" か、"しまう" か (metal)')
    g = _g(state)
    if g["offers"]:
        ids = "・".join(o["id"] for o in g["offers"])
        rows.append(f'   遠くの町の運ぶ人の申し出 ({ids}) ごとに、"受ける" か "約束する" か "受けない" (far。約束できるのは 1 人の運ぶ人とだけ)')
        if ((state["era2"].get("g6") or {}).get("open") or {}).get("板"):
            rows.append('   約束するとき、約束を粘土の板に "書く" か "書かない" か (far_write)')
    return rows


def fields_json(state):
    g = _g(state)
    return ((' "metal": null,' if tools(state) else "") + ((' "far": {' + ", ".join(f'"{o["id"]}": "..."' for o in g["offers"]) + "},") if g["offers"] else "")
            + (' "far_write": null,' if g["offers"] and ((state["era2"].get("g6") or {}).get("open") or {}).get("板") else ""))
