"""村の会計 (【シ】の測る列。記録から計算するだけで、世界の進み方・お題・ダッシュボードには使わない)

2026-10-14 の経済の調べ (国の会計 SNA・部門ごとの出し入れ・制約つき最適化の点検表) から。本人が「お任せします」で決めた 3 つのうちの 1 つ目。
名前の注意: この中の「KKT」は 2 つある。会計・経済・投資理論 (アクチュアリー試験の科目。略して KKT。本人の言う KKT) と、
カルーシュ・キューン・タッカー条件 (制約つき最適化の決まり。略して KKT 条件。経済の中の道具の 1 つで、binding の読み方にだけ使う)。下では略さずに書く。
帳簿 (ledger.jsonl) の 1 季節分の行と、季節の行 (season_village・season_person) だけから計算する。単位は kcal (草の種 1 つかみ = 80 kcal)。

  食べ物: 作った (採った・木から取った・狩った・乳・刈った 2 つ・ヤギをつぶした) − 種 (まいた・埋めた) − 損 (腐った・虫やネズミ・雨・干した目減り)
  ヤギ: 1 頭 = GOAT_WORTH 3 万 kcal (生まれた・捕まえた と、いなくなった・つぶした)。値うちが大きく動くので、食べ物とは分けて出す
        草の上限 (K) は 4409 日目の季節から (36年60日目 = 4379 日目のあとにコードを変えた。世界の中の出来事ではない)
  土器・鎌: 交換の値うち VALUE (40・75 つかみ)。VALUE は G6 からなので、G6 の季節 (3569 日目の季節) から数える。それより前は null。
        季節そのものの時期で決める。G5 から G6 に変わった 3539 日目の季節は null で、季節の終わりで値うちをつける balance とは 1 季節ずれる
  住まい: 住まいを建てる日数 × DAY_FOOD 2,400 (建てた手間で数える。帳簿の残りにはないので、部門の表には入れない)
  恒等式: 純生産 = 食べた・祭り + 残りの増え (住まいをふくむ) + よその村へ出した差 + 持って出た分 − 記録にない差
  部門: 村 (村の蓄え + 大人の手元。帳簿と同じ) / 家 (家の倉と家のヤギ。だれもいなくなった家の倉もふくむ) / よその村 / 自然・暮らし
        村を出た人・家が持って出た分も自然・暮らしへ数える (G6 では村を出た家はほかの村になるが、交換・貸しとは分ける。2026-10-14 までの帳簿では 0 行)

  貸借対照表 (balance): 季節の終わりの村と家の持ち物・借り (いつも 0)・純資産と、土器・鎌の傷み。会計・経済・投資理論 (アクチュアリー試験の科目。略して KKT) の会計の見方。
        帳簿と季節の行のほかに、控えの大人の手元と、貸し借りの出来事・state の g6.debts も読む (下の Books)

足し算はみな math.fsum (Python の版で値が変わらないように)。乱数も時刻も使わないので、同じ記録からは同じ値になる。
夕方に木から取る・夕方に刈るのは、働いた日に数えない (世界の決まり)。日数あたりの得を読むときは気をつける。
"""
import math
import re

import era2

GOAT = era2.GOAT_WORTH  # ヤギ 1 頭 (kcal)
GOODS = {"土器": era2.VALUE["土器"] * era2.GRAIN, "鎌": era2.VALUE["鎌"] * era2.GRAIN}  # 交換の値うち (kcal)。G6 から
PASTURE_FROM = 4409  # 草の上限 (era2.pasture_cap) が効いた最初の季節の終わりの日 (2026-10-10 本人が決めた)
CRAFT_FROM = "G3"  # 土器 (虫やネズミ) と鎌の決まりは G3 から
VALUE_FROM = "G6"  # 交換の値うち (VALUE) は G6 から
BUILD = "住まいを建てる"
REST, INJURED = "休む", "休む (けが)"
DIFF = "記録にない差"
START, END = "季節のはじめの残り", "季節の終わりの残り"  # build_records と同じ
SECTORS = ("村", "家", "よその村", "自然・暮らし")
ROWS = ("production", "seed", "consumption", "losses", "transfers", "external", "residual")
# 帳簿の理由 → 行。build_records.FLOWS の理由は、メモ (村の蓄えに入れた・取った) のほかは全部ここにある (試しで確かめる)
KIND = {
    "採った": "production", "木から取った": "production", "狩った": "production", "乳をしぼった": "production",
    "刈った (村の蓄えに入った)": "production", "刈った (自分の家の畑)": "production", "ヤギをつぶした": "production",
    "生まれた": "production", "捕まえた": "production", "作った": "production",
    "まいた (畑)": "seed", "種として埋めた": "seed",
    "食べた": "consumption", "祭り": "consumption",
    "腐った": "losses", "虫やネズミ": "losses", "雨で傷んだ": "losses", "干した": "losses",  # 干した: 干すと 2 割へる (ほかの物 − と干し肉 + の差)
    "いなくなった (世話が足りない)": "losses", "いなくなった (草が足りない)": "losses", "つぶした": "losses", "割れた": "losses",
    "家にだれもいなくなり、村のものになった": "transfers", "だれもいなくなり、村のものになった": "transfers",
    "持ち主がいなくなり村のものになった": "transfers", "家の倉から食べた": "transfers", "家の倉から食べた (子)": "transfers",
    "家の人が食べた": "transfers", "子が食べた": "transfers", "よその家の倉から取った": "transfers", "よその家の人に取られた": "transfers",
    "罰・つぐないで受け取った": "transfers", "罰・つぐないで払った": "transfers",
    "亡くなった人の手元": "transfers", "村を出た人の手元": "transfers", "村を出て持っていった": "transfers",
    "ほかの村へ出した": "external", "ほかの村から入った": "external",
    DIFF: "residual",
}
# 移ったもののまとめ: (出した側の部門, 理由)
GONE = ("亡くなった人の手元", "村を出た人の手元", "村を出て持っていった")  # 村から出ていった (自然・暮らしへ。村を出た家も、よその村ではなくここ)
TRANSFER_KINDS = {"家にだれもいない": (("家",), ("だれもいなくなり、村のものになった", "持ち主がいなくなり村のものになった")),
                  "家の倉から食べた": (("家",), ("家の人が食べた", "子が食べた", "よその家の人に取られた")),
                  "罰・つぐない": (("家",), ("罰・つぐないで払った",)), "持って出た": (("村", "家"), GONE)}


def r2(x):
    return None if x is None else round(x, 2) + 0.0


def at_least(era, e):
    return era in era2.ORDER2 and era2.ORDER2.index(era) >= era2.ORDER2.index(e)


def fix_from(state):
    """G7 の史実のずれの直し (docs/society_phase/G7_design.md 4.E.4) が効いた最初の日。G7 に入るまでは None。
    PASTURE_FROM のように決め打ちにせず、state (e2.g7.fix_from) から読む"""
    return (((state or {}).get("era2") or {}).get("g7") or {}).get("fix_from")


def valued(era):
    """この季節の土器・鎌に値うちをつけるか (VALUE のある G6 から)"""
    return at_least(era, VALUE_FROM)


def part(item):
    return "goats" if item == "ヤギ" else "goods" if item in GOODS else "food"


def worth(row, goods):
    """帳簿の 1 行の値うち (kcal)。食べ物は kcal、ヤギは頭数 × GOAT、土器・鎌は数 × VALUE (G6 から)。数えない行は None"""
    item, n = row["item"], row["amount"]
    if row["kind"] == "メモ":
        return None
    if item == "ヤギ":
        return None if n is None else n * GOAT
    if item in GOODS:
        return None if n is None or not goods else n * GOODS[item]
    return row["kcal"] if "kcal" in row else None


def tally(ledger_rows, goods):
    """1 季節の帳簿 → 動き {(部門, 物の種類, 行): [kcal]}・理由ごと {(部門, 理由): [kcal]}・残り {部門: (はじめ, 終わり)} (分からなければ None)"""
    fl, why, s0, s1, unknown = {}, {}, {}, {}, set()
    for r in ledger_rows:
        if r["kind"] == "メモ" or (r["item"] in GOODS and not goods):
            continue
        sec = "村" if r["holder"] == "村" else "家"
        v = worth(r, goods)
        if r["kind"] == "残り":
            if v is None:
                unknown.add(sec)
            else:
                (s0 if r["reason"] == START else s1).setdefault(sec, []).append(v)
            continue
        if v is None:
            unknown.add(sec)
            continue
        fl.setdefault((sec, part(r["item"]), KIND.get(r["reason"], "?")), []).append(v)
        why.setdefault((sec, r["reason"]), []).append(v)
    stock = {s: (None if s in unknown else (math.fsum(s0.get(s, [])), math.fsum(s1.get(s, [])))) for s in ("村", "家")}
    return fl, why, stock


def _sum(d, secs=("村", "家"), parts=("food", "goats", "goods"), rows=ROWS):
    return math.fsum(v for (s, p, k), xs in d.items() if s in secs and p in parts and k in rows for v in xs)


def _why(d, reasons, secs=("村", "家")):
    return math.fsum(v for (s, r), xs in d.items() if s in secs and r in reasons for v in xs)


def need(person_rows):
    """季節の必要な量 (kcal): いた日数 × 1 日分 (大人 DAY_FOOD、子は CHILD_EAT。store_days と同じ決まり)"""
    return math.fsum((r["present_to"] - r["present_from"] + 1) * day_need(r) for r in person_rows)


def day_need(r):
    if not r.get("child"):
        return era2.DAY_FOOD
    return next((k for a, k in era2.CHILD_EAT if (r.get("age") or 0) < a), era2.CHILD_EAT[-1][1])


def accounts(ledger_rows, person_rows, goods):
    """1 季節の村の会計 (kcal): 食べ物の生産と使い道・ヤギ・土器と鎌・住まい・恒等式の確かめ"""
    fl, why, stock = tally(ledger_rows, goods)
    gross = _sum(fl, parts=("food",), rows=("production",))
    seed = -_sum(fl, parts=("food",), rows=("seed",))
    loss = -_sum(fl, parts=("food",), rows=("losses",))
    net = gross - seed - loss
    nd = need(person_rows)
    g_in, g_out = _sum(fl, parts=("goats",), rows=("production",)), -_sum(fl, parts=("goats",), rows=("losses",))
    m_in, m_out = _sum(fl, parts=("goods",), rows=("production",)), -_sum(fl, parts=("goods",), rows=("losses",))
    homes = math.fsum(r["days_by_activity"].get(BUILD, 0) for r in person_rows) * era2.DAY_FOOD
    eaten, feast = -_why(why, ("食べた",)), -_why(why, ("祭り",))
    product = math.fsum((net, g_in - g_out, m_in - m_out, homes))
    ds = None if None in stock.values() else math.fsum([stock["村"][1], -stock["村"][0], stock["家"][1], -stock["家"][0], homes])
    nx, tr, res = -_sum(fl, rows=("external",)), -_sum(fl, rows=("transfers",)), _sum(fl, rows=("residual",))
    other = _sum(fl, rows=("?",))  # 行の決まっていない理由 (あれば恒等式が合わなくなる)
    ident = {"net_product": r2(product), "consumption": r2(eaten + feast), "stock_change": r2(ds), "net_exports": r2(nx),
             "transfers": r2(tr), "residual": r2(res),
             "gap": None if ds is None else r2(product - math.fsum((eaten, feast, ds, nx, tr, -res)))}
    if other:
        ident["unclassified"] = r2(other)
    return {"need": r2(nd), "food_gross": r2(gross), "seed": r2(seed), "food_loss": r2(loss), "food_net": r2(net),
            "food_net_to_need": round(net / nd, 3) if nd else None, "eaten": r2(eaten), "feast": r2(feast),
            "evening_share": round(_why(why, ("木から取った",)) / gross, 3) if gross else None,
            "goats": {"gained": r2(g_in), "lost": r2(g_out), "net": r2(g_in - g_out)},
            "goods": {"made": r2(m_in), "broken": r2(m_out), "net": r2(m_in - m_out)} if goods else None,
            "homes": r2(homes), "identity": ident}


def sectors(ledger_rows, goods):
    """1 季節の部門ごとの出し入れ (kcal。入るは +)。どの行も足すと 0、村と家の列の合計は残りの増え (住まいは入れない)"""
    fl, why, stock = tally(ledger_rows, goods)
    rows = {}
    for k in ROWS:
        v, h = r2(_sum(fl, ("村",), rows=(k,))), r2(_sum(fl, ("家",), rows=(k,)))
        o = r2(-math.fsum((v, h))) if k == "external" else 0.0
        rows[k] = dict(zip(SECTORS, (v, h, o, r2(-math.fsum((v, h, o))))))
    by = {name: r2(-_why(why, rs, secs)) for name, (secs, rs) in TRANSFER_KINDS.items()}
    return {"rows": rows, "stock_change": {s: None if stock[s] is None else r2(stock[s][1] - stock[s][0]) for s in ("村", "家")},
            "transfers_by_kind": by}


FATE = {"採った": "produced", "刈った (村の蓄えに入った)": "produced", "刈った (自分の家の畑)": "produced", "ほかの村から入った": "imported",
        "食べた": "eaten", "まいた (畑)": "sown", "虫やネズミ": "pests", "祭り": "feast", "ほかの村へ出した": "exported",
        "腐った": "rotted", "雨で傷んだ": "rotted"}
FATE_KEYS = ("start", "produced", "imported", "eaten", "sown", "pests", "feast", "exported", "rotted", "other")


def grain_fate(prev, ledger_rows, alive):
    """草の種の行方 (はじめからの合計、つかみ)。prev = 前の季節の値 (はじめの季節は None)。alive = 季節の終わりに人のいる家の番号。
    村の残りは村の蓄え + 大人の手元 (帳簿と同じ)。家の残りは、だれもいなくなった家の倉 (orphaned) もふくむ。
    はじめ + 作った + 入った = 食べた + まいた + 虫やネズミ + 祭り + 出した + 腐った + そのほか (亡くなった人の手元・記録にない差など) + 残り"""
    out = dict(prev or {k: 0.0 for k in FATE_KEYS})
    add = {k: [] for k in FATE_KEYS}
    stored = {"village": [], "households": [], "orphaned": []}
    known = True
    for r in ledger_rows:
        if r["item"] != "草の種" or r["kind"] == "メモ":
            continue
        n = r["amount"]
        if r["kind"] == "残り":
            if n is None:
                known = False
            elif r["reason"] == START:
                if prev is None:
                    add["start"].append(n)
            elif r["holder"] == "村":
                stored["village"].append(n)
            else:
                stored["households"].append(n)
                if r["holder"] not in alive:
                    stored["orphaned"].append(n)
            continue
        if KIND.get(r["reason"]) == "transfers" and r["reason"] not in GONE:  # 村と家のあいだ・家どうし (合わせると 0)
            continue
        k = FATE.get(r["reason"], "other")
        add[k].append(n if k in ("produced", "imported") else -n)  # 使った・へった分は + で数える
    for k in FATE_KEYS:
        out[k] = r2(math.fsum([out[k]] + add[k]))
    return dict(out, stored={k: r2(math.fsum(v)) for k, v in stored.items()} if known else None)


def store_days_all(store_kcal, ledger_rows, day_need_kcal):
    """村の蓄え + 家の倉 (だれもいなくなった家の倉もふくむ) の食べ物が、store_days と同じ人数の何日分か (era2.store_days と同じく切り捨て)"""
    if store_kcal is None or not day_need_kcal:
        return None
    hs = [r["kcal"] for r in ledger_rows if r["holder"] != "村" and r["kind"] == "残り" and r["reason"] == END
          and r["item"] not in ("ヤギ",) + tuple(GOODS)]
    if None in hs:
        return None
    return int(math.fsum([store_kcal] + hs) / day_need_kcal)


def binding(v, person_rows, ledger_rows, cap):
    """制約の点検表 (制約つき最適化のカルーシュ・キューン・タッカー条件 (KKT 条件。アクチュアリー試験の KKT とは別) の相補性のように読む。
    最適化はしない): 上限に届いているか (at_limit) と、その数。土器と鎌は G3 の季節 (1559 日目の季節) から (季節そのものの時期で決める)。
    草: 飼っているヤギと K (草の上限のある季節だけ)。土器: 土器に入る草の種と、守る草の種 (村の蓄え + 家の倉)。
    鎌: 鎌と、刈った大人。働く日: 大人の日のうち休んだ日。働く日には限りの印をつけない (at_limit はいつも None):
    大人は毎日なにかの仕事を選ぶので、休んだ日が 0 なのがふつうで、限りに届いた印にならない。夕方の仕事は日数にない"""
    g = (v.get("goats") or {}).get("count")
    pasture = {"goats": g, "K": cap, "ratio": round(g / cap, 3) if cap and g is not None else None,
               "at_limit": (g >= cap) if cap and g is not None else None}
    craft = at_least(v.get("era"), CRAFT_FROM)
    pots = None
    if craft and v.get("pots") is not None and v.get("store") is not None:
        hg = [r["amount"] for r in ledger_rows if r["holder"] != "村" and r["item"] == "草の種" and r["reason"] == END]
        if None not in hg:
            grain = r2(math.fsum([v["store"].get("草の種", 0)] + hg))
            hold = v["pots"] * era2.POT_HOLD
            pots = {"pots": v["pots"], "hold": hold, "grain": grain, "at_limit": grain > hold}
    ads = [r for r in person_rows if not r.get("child")]
    sickles = None
    if craft and v.get("sickles") is not None:
        n = sum(1 for r in ads if (r.get("outputs") or {}).get("harvested"))
        sickles = {"sickles": v["sickles"], "harvesters": n, "at_limit": n > v["sickles"]}
    days = sum(n for r in ads for n in r["days_by_activity"].values())
    rest = sum(r["days_by_activity"].get(REST, 0) for r in ads)
    hurt = sum(r["days_by_activity"].get(INJURED, 0) for r in ads)
    labour = {"adult_days": days, "rest_days": rest, "injured_days": hurt, "rest_share": round(rest / days, 3) if days else None,
              "at_limit": None}
    return {"pasture": pasture, "pots": pots, "sickles": sickles, "labour": labour}


# ---------------- 貸借対照表 (2026-10-14 本人「お任せします」: 会計・経済・投資理論 (アクチュアリー試験の科目。略して KKT) の会計の見方。測るだけ) ----------------
# 季節の終わりの持ち物 (資産) と借り (負債) と、その差 (純資産 = 資産 − 負債) を、村と家 (家をみな合わせて) に分けて出す。値うちは accounts と同じ kcal:
#   食べ物は kcal、ヤギは GOAT_WORTH (4409 日目の季節から草の上限。コードの変更なので前と後は分けて読む)、土器・鎌は VALUE で G6 の季節の終わり (3539 日目) から (accounts の goods より 1 季節早い)、
#   家族の住まいは建てた手間 (住まいを建てる日数 × DAY_FOOD。帳簿の残りにはないので、season_person の日数を季節をまたいで足す。減らさない)、
#   よその村への貸しは VALUE のつかみ × 80 kcal (ヤギ 375 つかみ = GOAT_WORTH)。
#   村の住まい (キャンプのまん中) は 153 日目、記録のはじまり (489 日目) より前にできたので、建てた手間は分からない (数だけ)。黒曜石は帳簿にない (2026-10-14 まで 0 個)
# 借り: 村も家も持たない (コードにその道がない)。よその村とは貸すだけ (貸して も 交換で足りない分 も、返すのは向こう)。罰・つぐないはその場で払い、
#   払えなければ消える。配給の記録 (g6 の credit) は「入れた」に数えるだけで、払う約束ではない
# 歴史: 「はじめの残り + 入り − 出 = 終わりの残り」の帳簿は、メソポタミアの粘土板 (ウルク期の配給・家畜の帳簿、ウル第三王朝の釣り合った帳簿 (足りない分を次へ
#   持ち越す。Englund 1991)) にある。複式簿記は中世イタリア (13〜15 世紀)、貸借対照表などの財務諸表は近代の道具。ここでは外から見る人の物差しとしてだけ使う
LENT, SHORT = "貸して", "交換で足りない分"  # よその村への貸し: 集まりで決めて貸した (貸し借り) / 交換に行った先で、向こうが払いきれなかった分 (交換)
DEBT_RE = re.compile(r"\[(D\d+)\]")


def handfuls(goods):
    """物と数 → 草の種のつかみ (交換の値うち VALUE)"""
    return math.fsum(era2.VALUE[k] * n for k, n in goods.items())


def _tot(*xs):
    return None if any(x is None for x in xs) else math.fsum(xs)


class Loans:
    """よその村への貸しを、出来事の順にたどる (state.era2.g6.debts は今の値なので、出来事の番号で季節の終わりの値にもどす)。
    貸した: 貸し借りの出来事の moves の −1 (貸して) か、交換の出来事の文の [D..] (交換で足りない分)。返した: debt のある出来事の moves の +1。
    閉じた: 「返した」の貸しは最後の返し、「返されない」は moves のない貸し借りの出来事 (返されないまま 1 年たった)。
    残り = はじめの量 − 閉じる前の返し。閉じたときに残っていた分 (記録がなく覚えで決めた・わずかなので返さなくてよい・返されない) は lost"""

    def __init__(self, debts, events):
        self.d = {d["id"]: d for d in debts}
        self.made, self.kind, self.back, off = {}, {}, {}, {}
        for e in events:
            x = e.get("data") or {}
            i, mv = x.get("debt"), x.get("moves") or []
            if i is None:
                m = DEBT_RE.search(e["text"]) if e["type"] == "交換" else None
                if m and m.group(1) in self.d and m.group(1) not in self.made:
                    self.made[m.group(1)], self.kind[m.group(1)] = e["id"], SHORT
                continue
            if i not in self.d:
                continue
            if any(m[1] < 0 for m in mv):
                if i not in self.made:
                    self.made[i], self.kind[i] = e["id"], LENT
            elif mv:
                got = {}
                for m in mv:
                    for k, n in m[2].items():
                        got[k] = got.get(k, 0) + n
                self.back.setdefault(i, []).append((e["id"], got))
            elif e["type"] == "貸し借り":
                off.setdefault(i, e["id"])
        self.close, self.orig, self.part = {}, {}, {}
        for i, d in self.d.items():
            bs = self.back.get(i, [])
            if d["status"] == "返した" and bs:
                self.close[i], part = bs[-1][0], bs[:-1]
            else:
                self.close[i], part = (off.get(i) if d["status"] == "返されない" else None), bs
            g = dict(d["goods"])  # 閉じた貸しは、閉じる前の残りのまま (era2._g6_repay は閉じるときに goods を変えない)
            for _, b in part:
                for k, n in b.items():
                    g[k] = g.get(k, 0) + n
            self.orig[i], self.part[i] = g, {j for j, _ in part}

    def owed(self, i, end):
        """出来事 end より前までで、貸し i の残り (物と数)。まだ貸していない・もう閉じたなら None"""
        made, close = self.made.get(i), self.close.get(i)
        if made is None or made >= end or (close is not None and close < end):
            return None
        g = dict(self.orig[i])
        for j, b in self.back.get(i, []):
            if j < end and j in self.part[i]:
                for k, n in b.items():
                    g[k] = g.get(k, 0) - n
        return g

    def season(self, lo, end, D):
        """季節の終わり D (出来事 end の前まで。この季節の出来事は lo から): 貸した側 (「村」か家の名前) → まだの貸し・新しい貸し・返った・失った (つかみ)"""
        out = {}

        def side(i):
            return out.setdefault(self.d[i]["lender"], {"open": [], "new": [], "returned": [], "lost": []})
        for i, d in self.d.items():
            g = self.owed(i, end)
            if g is not None:
                side(i)["open"].append({"id": i, "kind": self.kind[i], "other": d["other"], "handfuls": r2(handfuls(g)),
                                        "overdue_days": max(0, D - d["due"])})
            if self.made.get(i) is not None and lo <= self.made[i] < end:
                side(i)["new"].append(handfuls(self.orig[i]))
            for j, b in self.back.get(i, []):
                if lo <= j < end:
                    side(i)["returned"].append(handfuls(b))
            c = self.close.get(i)
            if c is not None and lo <= c < end:
                last = handfuls(self.back[i][-1][1]) if d["status"] == "返した" else 0.0
                side(i)["lost"].append(handfuls(self.owed(i, c)) - last)
        return out


def _loans(xs):
    """貸した側のまとめ (つかみと kcal): 残り・種類ごと・この季節に新しく貸した・返った・失った・まだの貸し"""
    op = [o for x in xs for o in x["open"]]
    h = math.fsum(o["handfuls"] for o in op)
    return {"handfuls": r2(h), "kcal": r2(h * era2.GRAIN),
            "by_kind": {k: r2(math.fsum(o["handfuls"] for o in op if o["kind"] == k)) for k in (LENT, SHORT)},
            "new": r2(math.fsum(v for x in xs for v in x["new"])), "returned": r2(math.fsum(v for x in xs for v in x["returned"])),
            "lost": r2(math.fsum(v for x in xs for v in x["lost"])), "open": sorted(op, key=lambda o: int(o["id"][1:]))}


def wear(ledger_rows, item):
    """土器・鎌の傷み (村のもの。帳簿から): はじめの数・作った・割れた・割れた割合 (割れた ÷ はじめの数)・そこから読む平均の寿命 (季節。1 ÷ 割合)"""
    rows = [r for r in ledger_rows if r["holder"] == "村" and r["item"] == item]
    start = next((r["amount"] for r in rows if r["kind"] == "残り" and r["reason"] == START), 0)
    if start is None:
        return None
    made = sum(r["amount"] for r in rows if r["reason"] == "作った")
    broken = -sum(r["amount"] for r in rows if r["reason"] == "割れた")
    rate = broken / start if start else None
    return {"start": start, "made": made, "broken": broken, "rate": None if rate is None else round(rate, 4),
            "life_seasons": round(1 / rate, 1) if rate else None}


class Books:
    """貸借対照表を季節の順に作る (家族の住まいの建てた手間と、よその村への貸しは、季節をまたいで数える)"""

    def __init__(self, debts, events, hid, camp_day):
        self.loans = Loans(debts, events)
        self.hid = hid  # 家の名前 → 家の番号 (貸した家)
        self.camp_day = camp_day  # 村の住まいができた日 (state.camp.dwelling_day)
        self.cost = {}  # 家の番号 → 住まいを建てた手間 (kcal)
        self.lo = 0  # この季節の出来事のはじめ (前の季節の終わり)

    def season(self, v, hs, ps, lg, C, end):
        D = v["season_end_day"]
        ln = self.loans.season(self.lo, end, D)
        self.lo = end
        if at_least(v.get("era"), "G3"):  # 家族の住まいは G3 から (その前の「住まいを建てる」は村の住まいの手入れ)
            for r in ps:
                n = r["days_by_activity"].get(BUILD, 0)
                if n and r.get("household_id"):
                    self.cost[r["household_id"]] = math.fsum([self.cost.get(r["household_id"], 0.0), n * era2.DAY_FOOD])
        val = at_least(v.get("era_end") or v.get("era"), VALUE_FROM)  # 土器・鎌の値うち: 季節の終わりに G6 なら (3539 日目の季節の終わりから)
        # 村
        hands = None if C is None else math.fsum(k for sp in C["people"].values() if sp.get("alive") and not sp.get("child")
                                                 for k in (sp.get("food") or {}).values())
        gv = (v.get("goats") or {}).get("by_holder", {}).get("村", 0) if v.get("goats") else None
        goods = {}
        for item, key in (("土器", "pots"), ("鎌", "sickles")):
            n = v.get(key)
            goods[key] = {"count": n, "kcal": r2(n * GOODS[item]) if val and n is not None else None}
        vl = _loans([ln["村"]] if "村" in ln else [])
        vg = None if gv is None else gv * GOAT
        va = _tot(v.get("store_kcal"), hands, vg, goods["pots"]["kcal"] or 0.0, goods["sickles"]["kcal"] or 0.0, vl["kcal"])
        village = {"food": {"kcal": v.get("store_kcal"), "by_item": v.get("store")}, "hands_kcal": r2(hands), "goats": {"count": gv, "kcal": r2(vg)},
                   **goods, "dwellings": {"count": 1 if self.camp_day is not None and self.camp_day <= D else 0, "kcal": None},
                   "loans": vl, "assets": r2(va), "liabilities": 0.0, "equity": r2(va)}
        # 家 (家の倉と家のヤギは帳簿の季節の終わりの残りから。だれもいなくなった家の倉もふくむ)
        food, items, goats, known = {}, {}, {}, True
        for r in lg:
            if r["holder"] == "村" or r["kind"] != "残り" or r["reason"] != END:
                continue
            if r["amount"] is None:
                known = False
            elif r["item"] == "ヤギ":
                goats[r["holder"]] = goats.get(r["holder"], 0) + r["amount"]
            elif r["item"] not in GOODS:
                food.setdefault(r["holder"], []).append(r["kcal"])
                items.setdefault(r["item"], []).append(r["amount"])
        hl = {self.hid.get(k, k): x for k, x in ln.items() if k != "村"}
        living = {h["household_id"] for h in hs if h["members"]}
        built = set(v.get("home_sizes") or {})
        each = {}
        for h in set(food) | set(goats) | set(self.cost) | set(hl):
            each[h] = math.fsum([math.fsum(food.get(h, [])), goats.get(h, 0) * GOAT, self.cost.get(h, 0.0), _loans([hl[h]])["kcal"] if h in hl else 0.0])
        hk = math.fsum(math.fsum(x) for x in food.values())
        hg = sum(goats.values())
        hd = math.fsum(self.cost.values())
        hloans = _loans([hl[h] for h in sorted(hl)])
        ha = math.fsum([hk, hg * GOAT, hd, hloans["kcal"]]) if known else None
        top = max(sorted(each), key=lambda h: each[h]) if each else None
        orph = [h for h in each if h not in living and each[h] > 0]
        house = {"food": {"kcal": r2(hk) if known else None, "by_item": {k: r2(math.fsum(x)) for k, x in sorted(items.items())} if known else None},
                 "goats": {"count": hg, "kcal": r2(hg * GOAT)},
                 "dwellings": {"count": len(built), "building": sum(1 for h in self.cost if h not in built), "kcal": r2(hd)},
                 "loans": hloans, "assets": r2(ha), "liabilities": 0.0, "equity": r2(ha),
                 "living": len(living), "with_assets": sum(1 for h in living if each.get(h, 0) > 0),
                 "with_stores": sum(1 for h in living if math.fsum(food.get(h, [])) > 0 or goats.get(h, 0) > 0),
                 "orphaned": {"households": len(orph), "kcal": r2(math.fsum(each[h] for h in orph))},
                 "top": {"household": top, "share": round(each[top] / ha, 3) if top and ha else None}}
        ta = _tot(va, ha)
        return {"村": village, "家": house, "total": {"assets": r2(ta), "liabilities": 0.0, "equity": r2(ta)},
                "wear": {"pots": wear(lg, "土器"), "sickles": wear(lg, "鎌")}}
