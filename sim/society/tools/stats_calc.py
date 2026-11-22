#!/usr/bin/env python3
"""川辺の村の統計 (国の統計の形) の計算。年報 (tools/year_report.py) と統計のページ (tools/build_stats.py) が同じこれを使う。

設計: docs/society_phase/dashboard_official_design.md。数の定義: tools/stats_indicators.json (1 つの数に 1 行)。
data/ は読むだけ (何も書かない)。書いている最中の JSON は少し待って読み直す。

使い方 (照らし合わせ):
  python3 sim/society/tools/stats_calc.py --data sim/society/data --check
    年報 (reports/yearN.html) に書いた数と、設計に書いた 236年の数とくらべ、ちがう所を出す。

おもな関数:
  Ctx(data, state=None, seasons=None, people=None)  読むもの (読んだものを渡せば読み直さない。ほかは要るときに読む)
  year_row(ctx, y, full=True)  1 年の数 (dict。キーは stats_indicators.json の id。ない数は None)
  headline(ctx, y)              見出しの数だけ (年報のいちばん上)
"""
import argparse
import collections
import json
import os
import re
import sys
import time
from pathlib import Path

HERE = os.path.dirname(os.path.abspath(__file__))
SOC = os.path.dirname(HERE)
YEAR = 120
UNIT = 288000.0  # 大人 1 年分 = 2,400 kcal × 120 日
S2_FIRST, S3_FIRST = 4, 201  # Society 2.0 は 489 日目 (4年) から、Society 3.0 は 24120 日目 (201年) から
DEFS_PATH = os.path.join(HERE, "stats_indicators.json")

REST = ("休む", "休む (けが)")
FOOD_JOBS = ("畑仕事", "ヤギの世話", "採集", "狩り", "水の道を掘る", "種まき", "探索", "ヤギを捕まえる")
MAKE_JOBS = ("土器づくり", "道具づくり", "黒い金属を作る", "印のかたまりを作る", "住まいを建てる", "水の輪を建てる", "水の輪を直す",
             "水の作業場を作る", "水の作業場で働く", "燃える石を掘る", "かまどを作りかえる", "火おこし")
# のこりは「そのほか」(字を教える・習う・知らせを書く・帳・記録・市へ運ぶ・交換に行く・試す)
FOOD_ITEMS_SKIP = ("ヤギ", "土器", "鎌")  # 帳簿の食べ物の表に入れない物 (kcal が 0 か、食べ物でない)
PROD_REASONS = ("刈った (村の蓄えに入った)", "刈った (自分の家の畑)", "採った", "木から取った", "狩った", "乳をしぼった", "ヤギをつぶした", "捕まえた", "つぶした")
SEED_REASONS = ("まいた (畑)", "種として埋めた")
LOSS_REASONS = ("虫やネズミ", "腐った")


def defs():
    return json.loads(Path(DEFS_PATH).read_text(encoding="utf-8"))


# ---------------------------------------------------------------- 読む

def _json(p, tries=6):
    """読むだけ。ワークフローが書いている最中なら少し待って読み直す"""
    for i in range(tries):
        try:
            return json.loads(Path(p).read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            if i == tries - 1:
                raise
            time.sleep(2)


def _jsonl(p):
    """1 行 1 つ。書きかけの最後の行は飛ばす"""
    out = []
    if not Path(p).exists():
        return out
    with open(p, encoding="utf-8") as fh:
        for x in fh:
            if x.strip():
                try:
                    out.append(json.loads(x))
                except json.JSONDecodeError:
                    pass
    return out


class Ctx:
    """読むもの。year_report.py は読んだ state・季節の行・人を渡す (読み直さない)。ほかは要るときに 1 回だけ読む"""

    def __init__(self, data, state=None, seasons=None, people=None):
        self.data = Path(data)
        self.rec = self.data / "records"
        self._state = state
        self._seasons = seasons
        self._people = people
        self._cache = {}

    # state.json から使うのは小さな部分だけ。build_stats は state を読んで、要る所だけ残して手放す
    @property
    def state(self):
        if self._state is None:
            self._state = _json(self.data / "state.json")
        return self._state

    def g7rows(self, key):
        if ("g7", key) not in self._cache:
            g7 = ((self.state.get("era2") or {}).get("g7")) or {}
            self._cache[("g7", key)] = (g7.get(key) or {}).get("rows") or {}
        return self._cache[("g7", key)]

    def slim(self):
        """state のうち、統計に使う所だけを残して、大きな state を手放す (build_stats の大きさをおさえる)"""
        st = self.state
        for k in ("s3", "s4", "i4", "p4", "t5"):
            self.g7rows(k)
        lo = (st.get("archive") or {}).get("upto")
        self._cache["live_famine"] = collections.Counter(x["day"] // YEAR for x in st.get("events", []) if x.get("type") == "蓄えが尽きる")
        self._cache["archive_upto"] = lo
        self._cache["now"] = st["day"]
        self._cache["era_log"] = st.get("era_log") or []
        self._state = {"day": st["day"], "archive": st.get("archive"), "era_log": st.get("era_log"), "era2": {"g7": {}}, "events": []}

    @property
    def now(self):
        return self._cache.get("now", self.state["day"])

    @property
    def seasons(self):
        if self._seasons is None:
            by = {}
            for r in _jsonl(self.rec / "season_village.jsonl"):
                by.setdefault(r["year"], []).append(r)
            self._seasons = by
        return self._seasons

    def srows(self, y):
        return sorted(self.seasons.get(y, []), key=lambda r: r["season_end_day"])

    @property
    def people(self):
        if self._people is None:
            self._people = {p["id"]: p for p in _json(self.rec / "people.json")}
        return self._people

    def _lazy(self, key, fn):
        if key not in self._cache:
            self._cache[key] = fn()
        return self._cache[key]

    @property
    def households(self):
        return self._lazy("households", lambda: _json(self.rec / "households.json"))

    @property
    def granary(self):
        def f():
            by = collections.defaultdict(list)
            for r in _jsonl(self.rec / "granary.jsonl"):
                by[(r["year"], r["kind"])].append(r)
            return by
        return self._lazy("granary", f)

    @property
    def tribute(self):
        return self._lazy("tribute", lambda: collections.Counter(
            (r.get("season_end_day") or r.get("day", 0)) // YEAR for r in _jsonl(self.rec / "tribute.jsonl") if r.get("kind") == "貢ぎ出す"))

    @property
    def hh(self):
        """season_household.jsonl を 1 回読み、年ごとの仕事の人日と、年の終わりの家の倉 (つかみ) だけ残す"""
        def f():
            jobs = collections.defaultdict(collections.Counter)
            stores = collections.defaultdict(dict)
            with open(self.rec / "season_household.jsonl", encoding="utf-8") as fh:
                for x in fh:
                    try:
                        r = json.loads(x)
                    except json.JSONDecodeError:
                        continue
                    d = r["season_end_day"]
                    y = d // YEAR
                    jobs[y].update(r.get("jobs") or {})
                    if d % YEAR == YEAR - 1 and r.get("status") == "村にいる":
                        stores[y][r["household_id"]] = sum((r.get("store") or {}).values())
            return {"jobs": jobs, "stores": stores}
        return self._lazy("hh", f)

    @property
    def ledger(self):
        """ledger.jsonl を 1 回読み、年 × 理由の食べ物の kcal と、季節のはじめ・終わりの残り (食べ物) だけ残す"""
        def f():
            mv = collections.defaultdict(collections.Counter)
            with open(self.rec / "ledger.jsonl", encoding="utf-8") as fh:
                for x in fh:
                    try:
                        r = json.loads(x)
                    except json.JSONDecodeError:
                        continue
                    if r.get("item") in FOOD_ITEMS_SKIP or r.get("kind") == "メモ":
                        continue
                    y = r["season_end_day"] // YEAR
                    k = r["reason"] if r["kind"] == "動き" else ("start" if "はじめ" in r["reason"] else "end")
                    mv[y][k] += r.get("kcal") or 0.0
            return mv
        return self._lazy("ledger", f)

    def famine(self, y):
        """その年の出来事「蓄えが尽きる」の数。しまった年は archive/events_NNNN.jsonl を文字で数える"""
        fc = self._cache.setdefault("famine", {})
        if y in fc:
            return fc[y]
        upto = self._cache.get("archive_upto", (self.state.get("archive") or {}).get("upto"))
        if upto is not None and y <= upto:
            p = self.data / "archive" / f"events_{y:04d}.jsonl"
            n = None
            if p.exists():
                t = p.read_text(encoding="utf-8")
                n = len(re.findall(r'"type":\s*"蓄えが尽きる"', t))
        else:
            live = self._cache.get("live_famine")
            if live is None:
                live = collections.Counter(x["day"] // YEAR for x in self.state.get("events", []) if x.get("type") == "蓄えが尽きる")
                self._cache["live_famine"] = live
            n = live.get(y, 0)
        fc[y] = n
        return n

    # 人の出入り (生命表のもと)。1 回だけ作る
    @property
    def demo(self):
        return self._lazy("demo", lambda: _demography(self.people, self.now))


# ---------------------------------------------------------------- 人口 (生命表・合計特殊出生率)

AGE_GROUPS = [(0, 1), (1, 5)] + [(a, a + 5) for a in range(5, 60, 5)] + [(60, None)]


def _gi(age):
    for i, (lo, hi) in enumerate(AGE_GROUPS):
        if age >= lo and (hi is None or age < hi):
            return i
    return 0


def _demography(people, now):
    """年 × 年齢 (村の年) の、いた人年 (E・女 Ef)・死亡 (D)・母の年齢ごとの出生 (B)"""
    E = collections.defaultdict(collections.Counter)
    Ef = collections.defaultdict(collections.Counter)
    D = collections.defaultdict(collections.Counter)
    B = collections.defaultdict(collections.Counter)
    inf = collections.Counter()  # 年 → 1 歳 (120 日) 前の死亡
    for p in people.values():
        born = p.get("born_day")
        if born is None:
            continue
        s = max(p.get("came_day") or 0, born)
        ends = [x for x in (p.get("died_day"), p.get("left_day")) if x is not None]
        e = min(ends) if ends else now + 1
        t = s
        while t < e:
            Y = t // YEAR
            a = (t - born) // YEAR
            nx = min(e, (Y + 1) * YEAR, born + (a + 1) * YEAR)
            E[Y][a] += (nx - t) / YEAR
            if p.get("sex") == "女":
                Ef[Y][a] += (nx - t) / YEAR
            t = nx
        dd = p.get("died_day")
        if dd is not None and (p.get("left_day") is None or dd <= p["left_day"]) and dd >= s:
            D[dd // YEAR][(dd - born) // YEAR] += 1
            if dd - born < YEAR:
                inf[dd // YEAR] += 1
        m = people.get(p.get("mother_id")) if p.get("mother_id") else None
        if m and m.get("born_day") is not None and born >= 0 and p.get("origin") == "生まれた":
            B[born // YEAR][(born - m["born_day"]) // YEAR] += 1
    return {"E": E, "Ef": Ef, "D": D, "B": B, "inf": inf}


def life_table(dm, y0, y1):
    """y0〜y1 年の生命表 → (平均寿命, 5 歳未満児死亡率 (千あたり))。人年が少なすぎれば None"""
    n_g = len(AGE_GROUPS)
    Eg, Dg = [0.0] * n_g, [0] * n_g
    for Y in range(y0, y1 + 1):
        for a, v in dm["E"].get(Y, {}).items():
            Eg[_gi(a)] += v
        for a, v in dm["D"].get(Y, {}).items():
            Dg[_gi(a)] += v
    if sum(Eg) < 50:
        return None, None
    l, T, Ls = 1.0, 0.0, []
    l5 = None
    for i, (lo, hi) in enumerate(AGE_GROUPS):
        m = Dg[i] / Eg[i] if Eg[i] > 0 else 0.0
        if hi is None:
            Ls.append(l / m if m > 0 else l * 10)
            break
        n = hi - lo
        a = 0.3 if lo == 0 else n / 2
        q = min(1.0, n * m / (1 + (n - a) * m))
        d = l * q
        Ls.append(n * (l - d) + a * d)
        l -= d
        if hi == 5:
            l5 = l
    T = sum(Ls)
    return round(T, 1), (round((1 - l5) * 1000) if l5 is not None else None)


def tfr(dm, y0, y1):
    """y0〜y1 年。15〜49 歳の女の人の、5 歳きざみの出生率 × 5 の合計"""
    tot = 0.0
    for lo in range(15, 50, 5):
        ex = sum(v for Y in range(y0, y1 + 1) for a, v in dm["Ef"].get(Y, {}).items() if lo <= a < lo + 5)
        b = sum(v for Y in range(y0, y1 + 1) for a, v in dm["B"].get(Y, {}).items() if lo <= a < lo + 5)
        if ex > 0:
            tot += 5 * b / ex
    return round(tot, 2) if tot else None


def age_counts(people, day):
    """その日にいた人の、男女 × 5 歳きざみ (村の年)。人口ピラミッドと年齢の割合のもと"""
    out = {"女": collections.Counter(), "男": collections.Counter()}
    for p in people.values():
        b = p.get("born_day")
        if b is None or b > day or (p.get("came_day") or 0) > day:
            continue
        if p.get("died_day") is not None and p["died_day"] <= day:
            continue
        if p.get("left_day") is not None and p["left_day"] <= day:
            continue
        out.setdefault(p.get("sex"), collections.Counter())[min(16, (day - b) // YEAR // 5)] += 1
    return out


# ---------------------------------------------------------------- 1 年の数

def gini(xs):
    xs = sorted(x for x in xs if x is not None)
    n = len(xs)
    s = sum(xs)
    if n < 2 or s <= 0:
        return None
    cum = sum((i + 1) * x for i, x in enumerate(xs))
    return round((2 * cum) / (n * s) - (n + 1) / n, 3)


def _phase_row(ctx, y, keys=("t5", "p4", "i4", "s4", "s3")):
    r = {}
    for k in reversed(keys):  # 新しいフェーズの行を上に重ねる
        r.update(ctx.g7rows(k).get(str(y)) or {})
    return r


def nonfood_of(r):
    for k in ("t3_share", "p3_share", "f1_share"):
        if r.get(k) is not None:
            return r[k]
    return None


def literacy_of(ctx, y, end_adults):
    r = ctx.g7rows("i4").get(str(y))
    if r and r.get("adults"):
        return r["readers"], r["adults"], "i4"
    g = ctx.granary.get((y, "町と市と仲間"))
    if g and g[-1]["data"].get("readers") is not None and end_adults:
        return g[-1]["data"]["readers"], end_adults, "granary"
    return None, None, None


def headline(ctx, y):
    """年報のいちばん上と統計のページの見出し。季節の行・人・フェーズの行・出来事だけで出す (帳簿や家の行は読まない)"""
    rows = ctx.srows(y)
    pr = _phase_row(ctx, y)
    out = {"year": y, "complete": len(rows) == 4 and rows[-1]["season_end_day"] == y * YEAR + YEAR - 1, "seasons": len(rows)}
    end = rows[-1] if rows else None
    out["pop"] = end["population"] if end else pr.get("pop")
    out["adults"] = end.get("adults") if end else None
    # 村の生産 (accounts)
    acc = [r.get("accounts") for r in rows if r.get("accounts")]
    if acc:
        idn = lambda k: sum(((a.get("identity") or {}).get(k) or 0.0) for a in acc)  # noqa: E731
        goods = [a.get("goods") for a in acc]
        out["gdp_kcal"] = idn("net_product")
        out["gdp"] = out["gdp_kcal"] / UNIT
        out["gdp_parts"] = {"food": sum(a.get("food_net") or 0.0 for a in acc) / UNIT,
                            "goods": sum((g or {}).get("net") or 0.0 for g in goods) / UNIT,
                            "goats": sum(((a.get("goats") or {}).get("net") or 0.0) for a in acc) / UNIT,
                            "homes": sum(a.get("homes") or 0.0 for a in acc) / UNIT}
        out["gdp_food_only"] = any(g is None for g in goods)
        out["gdp_full_year"] = len(acc) == 4
        out["exp_cons"] = idn("consumption") / UNIT
        out["exp_stock"] = idn("stock_change") / UNIT
        out["exp_net"] = idn("net_exports") / UNIT
        out["exp_other"] = (idn("transfers") + idn("residual")) / UNIT
        out["gdp_pc"] = out["gdp"] / out["pop"] if out["pop"] else None
    else:
        out["gdp"] = None
    # 蓄え
    sd = [r["store_days"] for r in rows if r.get("store_days") is not None]
    out["store_min"] = pr.get("store_min", min(sd) if sd else None)
    out["store_min_src"] = "row" if "store_min" in pr else "season"
    out["nonfood"] = nonfood_of(pr)
    rd, ad, src = literacy_of(ctx, y, out["adults"])
    out["readers"], out["lit_adults"] = rd, ad
    out["literacy"] = rd / ad if rd is not None and ad else None
    out["literacy_src"] = src
    # 出生と死亡
    out["births"] = sum(len(r.get("births") or []) for r in rows) if rows else None
    out["deaths"] = sum(len(r.get("deaths") or []) for r in rows) if rows else None
    dm = ctx.demo
    out["infant_deaths"] = dm["inf"].get(y, 0)
    out["imr"] = 1000 * out["infant_deaths"] / out["births"] if out["births"] else None
    b5 = sum(sum(len(r.get("births") or []) for r in ctx.srows(yy)) for yy in range(y - 4, y + 1))
    i5 = sum(dm["inf"].get(yy, 0) for yy in range(y - 4, y + 1))
    out["imr5"] = 1000 * i5 / b5 if b5 else None
    fam = pr.get("famine")
    out["famine"] = fam if fam is not None else ctx.famine(y)
    out["wealth_gini"] = end.get("wealth_gini") if end else None
    return out


def year_row(ctx, y, full=True):
    """1 年の数ぜんぶ (キーは stats_indicators.json の id)。full=False なら見出しと季節の行だけ"""
    h = headline(ctx, y)
    rows = ctx.srows(y)
    end = rows[-1] if rows else {}
    pr = _phase_row(ctx, y)
    o = dict(h)
    P = o["pop"]
    o["female"] = (end.get("by_sex") or {}).get("女")
    o["male"] = (end.get("by_sex") or {}).get("男")
    o["households"] = end.get("households_with_members")
    o["hh_size"] = P / o["households"] if P and o["households"] else None
    prev = ctx.srows(y - 1)
    p0 = prev[-1]["population"] if prev else None
    o["pop_growth"] = (P - p0) / p0 if P is not None and p0 else None
    o["joined"] = sum(len(r.get("joined") or []) for r in rows)
    o["left"] = sum(len(r.get("left") or []) for r in rows)
    o["natural"] = (o["births"] or 0) - (o["deaths"] or 0) if rows else None
    o["cbr"] = 1000 * o["births"] / P if P and o["births"] is not None else None
    o["cdr"] = 1000 * o["deaths"] / P if P and o["deaths"] is not None else None
    cz = collections.Counter(d.get("cause") or "その他" for r in rows for d in (r.get("deaths") or []))
    o["causes"] = dict(cz)
    o["sick_deaths"] = cz.get("病", 0) if rows else None
    o["injured"] = sum(((r.get("binding") or {}).get("labour") or {}).get("injured_days") or 0 for r in rows) if any(r.get("binding") for r in rows) else None
    o["harvest"] = sum((r.get("fields") or {}).get("harvested") or 0 for r in rows) if rows else None
    seed = sum((r.get("fields") or {}).get("seed") or 0 for r in rows)
    o["seed"] = seed
    o["yield"] = o["harvest"] / seed if seed and o["harvest"] else None
    o["goats"] = (end.get("goats") or {}).get("count")
    eaten = sum(r.get("eaten_kcal") or 0 for r in rows)
    o["kcal_pc"] = eaten / P / YEAR if P and rows else None
    o["store_all"] = end.get("store_days_all")
    o["house_gini"] = end.get("house_gini")
    o["homes"] = end.get("homes_built")
    o["rain_out"] = max((r.get("rain_outside_people") or 0 for r in rows), default=None) if rows else None
    lw = end.get("laws") or {}
    o["laws"] = lw.get("in_force")
    o["laws_new"] = sum(len((r.get("laws") or {}).get("adopted") or []) for r in rows)
    o["laws_gone"] = sum(len((r.get("laws") or {}).get("abolished") or []) for r in rows)
    has_g5 = any(r.get("g5") for r in rows)
    o["disputes"] = sum(len((r.get("g5") or {}).get("disputes_new") or []) for r in rows) if has_g5 else None
    o["settled"] = sum(len((r.get("g5") or {}).get("disputes_settled") or []) for r in rows) if has_g5 else None
    g6s = [r.get("g6") for r in rows if r.get("g6")]
    if g6s:
        mv = collections.defaultdict(lambda: [0, 0])
        for g in g6s:
            for it, io in (g.get("moved") or {}).items():
                mv[it][0] += io.get("in", 0)
                mv[it][1] += io.get("out", 0)
        o["moved"] = {k: {"in": v[0], "out": v[1]} for k, v in mv.items()}
        o["trade_in"] = mv["草の種"][0] if "草の種" in mv else 0
        o["trade_out_pots"] = mv["土器"][1] if "土器" in mv else 0
        o["partners"] = g6s[-1].get("partners_last4")
        o["known"] = g6s[-1].get("known_villages")
        o["debts"] = g6s[-1].get("debts_open")
    bal = end.get("balance") or {}
    o["bal_village"] = (bal.get("村") or {}).get("assets") / UNIT if (bal.get("村") or {}).get("assets") is not None else None
    o["bal_house"] = (bal.get("家") or {}).get("assets") / UNIT if (bal.get("家") or {}).get("assets") is not None else None
    acc = [r.get("accounts") for r in rows if r.get("accounts")]
    o["gfcf"] = sum((a.get("homes") or 0) + ((a.get("goods") or {}).get("made") or 0) for a in acc) / UNIT if acc else None
    py = ctx.srows(y - 1)
    if o.get("gdp") is not None and py:
        hp = headline(ctx, y - 1) if (y - 1) >= S2_FIRST else {}
        o["gdp_prev"] = hp.get("gdp")
        o["gdp_growth"] = (o["gdp"] - hp["gdp"]) / abs(hp["gdp"]) if hp.get("gdp") and o.get("gdp_full_year") and hp.get("gdp_full_year") else None
    # フェーズの行
    o["posts"] = pr.get("posts")
    o["kids_taught"] = (ctx.g7rows("i4").get(str(y)) or {}).get("kids_taught")
    o["teach_days"] = (ctx.g7rows("i4").get(str(y)) or {}).get("teach_days")
    t5r, p4r = ctx.g7rows("t5").get(str(y)), ctx.g7rows("p4").get(str(y))
    o["for_others"] = ((t5r or {}).get("town_pd") or 0) + ((p4r or {}).get("pd") or 0) if (t5r or p4r) else None
    o["town_done"] = t5r.get("done") if t5r else None
    o["p4_done"] = p4r.get("done") if p4r else None
    s3r = ctx.g7rows("s3").get(str(y)) or {}
    for k in ("coal_burned", "coal_dug", "house_coal"):
        o[k] = s3r.get(k)
    # 数えもれ (村の帳)
    led = ctx.granary.get((y, "帳"))
    if led and P:
        d = led[-1]["data"]
        o["count_people"], o["count_houses"] = d.get("people"), d.get("houses")
        o["count_ratio"] = d["people"] / P if d.get("people") is not None else None
    # 年齢
    ac = age_counts(ctx.people, y * YEAR + YEAR - 1 if h["complete"] else (rows[-1]["season_end_day"] if rows else y * YEAR))
    tot = sum(sum(c.values()) for c in ac.values())
    if tot:
        bins = collections.Counter()
        for c in ac.values():
            bins.update(c)
        o["age_young"] = sum(v for b, v in bins.items() if b < 3) / tot
        o["age_work"] = sum(v for b, v in bins.items() if 3 <= b < 11) / tot
        o["age_old"] = sum(v for b, v in bins.items() if b >= 11) / tot
        o["pyramid"] = {s: [c.get(i, 0) for i in range(17)] for s, c in ac.items() if s in ("女", "男")}
        o["pyramid_total"] = tot
    dm = ctx.demo
    o["e0"], o["u5mr"] = life_table(dm, y - 4, y)
    o["tfr"] = tfr(dm, y - 4, y)
    if not full:
        return o
    # 家の行 (仕事・倉)
    J = ctx.hh["jobs"].get(y) or collections.Counter()
    wd = sum(J.values())
    if wd:
        work = sum(v for k, v in J.items() if k not in REST)
        o["work_days"] = wd
        o["jobs"] = dict(J.most_common())
        o["rest_share"] = (wd - work) / wd
        if work:
            o["work_food"] = sum(J.get(k, 0) for k in FOOD_JOBS) / work
            o["work_make"] = sum(J.get(k, 0) for k in MAKE_JOBS) / work
            o["work_other"] = 1 - o["work_food"] - o["work_make"]
        o["canal_days"] = J.get("水の道を掘る", 0)
        o["try_days"] = J.get("試す", 0)
    stores = ctx.hh["stores"].get(y)
    if stores:
        o["store_gini"] = gini([v for v in stores.values() if v > 0])
        o["store_houses"] = sum(1 for v in stores.values() if v > 0)
    # 帳簿 (食料需給表)
    L = ctx.ledger.get(y)
    if L:
        prod = sum(L.get(k, 0) for k in PROD_REASONS)
        imp = L.get("ほかの村から入った", 0)
        exp = -(L.get("ほかの村へ出した", 0) + L.get("貢ぎで出した", 0))
        dstock = L.get("end", 0) - L.get("start", 0)
        sup = prod + imp - exp - dstock
        o["fbs"] = {"prod": prod / UNIT, "imp": imp / UNIT, "exp": exp / UNIT, "dstock": dstock / UNIT, "supply": sup / UNIT,
                    "seed": -sum(L.get(k, 0) for k in SEED_REASONS) / UNIT, "loss": -sum(L.get(k, 0) for k in LOSS_REASONS) / UNIT,
                    "feast": -L.get("祭り", 0) / UNIT, "eaten": -L.get("食べた", 0) / UNIT}
        o["supply"] = sup / UNIT
        o["self_suff"] = prod / sup if sup > 0 else None
    o["tribute"] = ctx.tribute.get(y, 0) if y * YEAR >= 5849 else None
    return o


# ---------------------------------------------------------------- Society 1.0 (0〜488 日目。季節 = 30 日)

def s1_rows(ctx):
    """日ごとの archive/stats_NNNN.jsonl と archive/days_NNNN.json から、30 日ごとの行"""
    stats, days = [], {}
    for y in range(0, 5):
        stats += _jsonl(ctx.data / "archive" / f"stats_{y:04d}.jsonl")
        p = ctx.data / "archive" / f"days_{y:04d}.json"
        if p.exists():
            days.update({int(k): v for k, v in (_json(p).get("days") or {}).items()})
    stats = [s for s in stats if s["day"] <= 488]
    people = ctx.people
    laws = _json(ctx.rec / "laws.json")
    out = []
    for lo in range(0, 489, 30):
        hi = min(lo + 29, 488)
        ss = [s for s in stats if lo <= s["day"] <= hi]
        if not ss:
            continue
        act = collections.Counter(a["activity"] for d in range(lo, hi + 1) for a in days.get(d, []))
        wd = sum(act.values())
        work = sum(v for k, v in act.items() if k not in REST)
        births = [p for p in people.values() if p.get("origin") == "生まれた" and p.get("born_day") is not None and lo <= p["born_day"] <= hi]
        deaths = [p for p in people.values() if p.get("died_day") is not None and lo <= p["died_day"] <= hi]
        eaten = sum(s.get("eaten") or 0 for s in ss)
        alive = [s["alive"] for s in ss]
        out.append({"from": lo, "to": hi, "label": f"{lo // YEAR}年 {lo % YEAR + 1}〜{hi % YEAR + 1}日目", "days": len(ss),
                    "pop": alive[-1], "pop_max": max(alive), "births": len(births), "deaths": len(deaths),
                    "causes": dict(collections.Counter(p.get("death_cause") or "その他" for p in deaths)),
                    "kcal_pc": eaten / sum(alive) if sum(alive) else None,
                    "store_end_kcal": ss[-1].get("store"), "store_days": (ss[-1].get("store") or 0) / (2400 * alive[-1]) if alive[-1] else None,
                    "fire_days": sum(1 for s in ss if s.get("fire")), "housed_days": sum(1 for s in ss if s.get("housed")),
                    "rain_days": sum(1 for s in ss if s.get("rain")),
                    "eaten_by_kind": dict(sum((collections.Counter(s.get("eaten_by_kind") or {}) for s in ss), collections.Counter())),
                    "work_days": wd, "jobs": dict(act.most_common()), "rest_share": (wd - work) / wd if wd else None,
                    "work_food": sum(act.get(k, 0) for k in FOOD_JOBS) / work if work else None,
                    "laws": sum(1 for x in laws if x.get("adopted_day") is not None and x["adopted_day"] <= hi and (x.get("abolished_day") is None or x["abolished_day"] > hi)),
                    "laws_new": sum(1 for x in laws if x.get("adopted_day") is not None and lo <= x["adopted_day"] <= hi)})
    return out


# ---------------------------------------------------------------- 照らし合わせ

def _report_numbers(path):
    """年報 HTML から、照らし合わせに使う数を読む (書いた形が年でちがうので、見つかった物だけ)"""
    t = Path(path).read_text(encoding="utf-8")
    t = re.sub(r"<style.*?</style>|<svg.*?</svg>|<script.*?</script>", "", t, flags=re.S)
    txt = re.sub(r"\s+", " ", re.sub(r"<[^>]+>", " ", t))
    out = {}
    m = re.search(r"作った日: 記録の (\d+)年(\d+)日目 まで", txt)
    if m and int(m.group(2)) < YEAR:
        out["_partial"] = f"{m.group(1)}年{m.group(2)}日目"
    m = re.search(r"人は (\d[\d,]*) 人 → (\d[\d,]*) 人 \(生まれた子 (\d+) 人・亡くなった人 (\d+) 人", txt)
    if m:
        out["pop"] = int(m.group(2).replace(",", ""))
        out["births"], out["deaths"] = int(m.group(3)), int(m.group(4))
    for key, lab in (("pop", r"人 \(年の終わり\)"), ("store_min", r"蓄え \(いちばん少ない日\)"), ("literacy", "読める大人"),
                     ("nonfood", "食べ物でない仕事"), ("famine", "ききん")):
        m = re.search(r'title="' + lab + r': ([\d,.]+)', t)
        if m:
            v = float(m.group(1).replace(",", ""))
            out[key] = v / 100 if key in ("literacy", "nonfood") else v
    return out


def check(ctx, report_dir, years=None):
    """年報に書いた数と、設計の 236年の数とくらべる。(ちがい の list, くらべた数, 236年の計算の数)"""
    bad, n = [], 0
    rd = Path(report_dir)
    for p in sorted(rd.glob("year*.html")):
        y = int(re.findall(r"\d+", p.name)[0])
        if years and y not in years:
            continue
        got = _report_numbers(p)
        part = got.pop("_partial", None)
        if not got:
            continue
        h = headline(ctx, y)
        for k, v in got.items():
            mine = h.get(k)
            n += 1
            tol = 0.0006 if k in ("literacy", "nonfood") else 0.5
            if mine is None or abs(mine - v) > tol:
                bad.append({"src": p.name, "year": y, "key": k, "report": v, "calc": mine,
                            "why": f"年報を年の途中 ({part}) で作った" if part and int(part.split("年")[0]) == y else ""})
    R = defs()["reference_236"]
    y = R["year"]
    o = year_row(ctx, y)
    J = o.get("jobs") or {}
    wd = o.get("work_days") or 1
    mine = {"pop": o["pop"], "female": o["female"], "male": o["male"], "households": o["households"], "births": o["births"], "deaths": o["deaths"],
            "imr": o["imr"], "gdp_kcal": o.get("gdp_kcal"), "gdp": o.get("gdp"), "gdp_food_kcal": (o.get("gdp_parts") or {}).get("food", 0) * UNIT,
            "exp_cons_kcal": o.get("exp_cons", 0) * UNIT, "exp_stock_kcal": o.get("exp_stock", 0) * UNIT, "exp_net_kcal": o.get("exp_net", 0) * UNIT,
            "gdp_pc": o.get("gdp_pc"), "work_days": o.get("work_days"), "share_farm": J.get("畑仕事", 0) / wd, "share_canal": J.get("水の道を掘る", 0) / wd,
            "share_ws": J.get("水の作業場で働く", 0) / wd, "share_rest": sum(J.get(k, 0) for k in REST) / wd, "harvest": o["harvest"], "yield": o["yield"],
            "goats": o["goats"], "store_min": o["store_min"], "readers": o["readers"], "adults": o["lit_adults"], "literacy": o["literacy"],
            "nonfood": o["nonfood"], "kcal_pc": o["kcal_pc"], "wealth_gini": o["wealth_gini"], "house_gini": o["house_gini"], "homes": o["homes"],
            "bal_village_kcal": (o.get("bal_village") or 0) * UNIT, "bal_house_kcal": (o.get("bal_house") or 0) * UNIT, "e0_5y": o["e0"], "tfr_5y": o["tfr"],
            "laws": o["laws"], "known": o.get("known"), "partners": o.get("partners"), "canal_days": o.get("canal_days"), "town_done": o.get("town_done")}
    rough = {"gdp_kcal", "gdp_food_kcal", "exp_cons_kcal", "exp_stock_kcal", "exp_net_kcal", "work_days", "harvest", "bal_village_kcal", "bal_house_kcal", "kcal_pc"}
    for k, v in R["values"].items():
        m = mine.get(k)
        n += 1
        if m is None:
            bad.append({"src": "設計の 236年", "year": y, "key": k, "report": v, "calc": None})
            continue
        if k in rough:
            ok = abs(m - v) <= max(abs(v) * 0.02, 10000 if "kcal" in k else 50)
        elif isinstance(v, float) and v < 1:
            ok = abs(m - v) < 0.006
        elif k in ("yield", "e0_5y", "tfr_5y", "imr"):
            ok = abs(m - v) <= max(0.5, abs(v) * 0.05)
        else:
            ok = abs(m - v) < 0.5
        if not ok:
            bad.append({"src": "設計の 236年", "year": y, "key": k, "report": v, "calc": round(m, 4) if isinstance(m, float) else m})
    return bad, n, mine


def main(argv=None):
    ap = argparse.ArgumentParser(description="村の統計の計算 (照らし合わせ)")
    ap.add_argument("--data", default=os.path.join(SOC, "data"))
    ap.add_argument("--reports", default=os.path.join(SOC, "reports"))
    ap.add_argument("--check", action="store_true")
    ap.add_argument("--year", type=int)
    a = ap.parse_args(argv)
    ctx = Ctx(a.data)
    ctx.slim()
    if a.year is not None:
        o = year_row(ctx, a.year)
        o.pop("pyramid", None)
        print(json.dumps(o, ensure_ascii=False, indent=1, default=str))
    if a.check:
        bad, n, _ = check(ctx, a.reports)
        print(f"くらべた数 {n}・ちがう {len(bad)}")
        for b in bad:
            print(f"  {b['src']} {b['year']}年 {b['key']}: 書いた数 {b['report']} / 計算 {b['calc']}" + (f" ({b['why']})" if b.get("why") else ""))


if __name__ == "__main__":
    main()
