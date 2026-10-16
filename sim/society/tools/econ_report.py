"""G6 の評価の下書き (G6.md) に入れる「測った数」の節を、記録から作る (【シ】。読むだけで、世界・お題・ダッシュボードには使わない)

  PYTHONUTF8=1 python3.13 sim/society/tools/econ_report.py [--data DIR] [--out FILE]

本人が 2026-10-14 に「お任せします」で決めた 3 つのうちの 2 つ目 (人の生き死に・蓄えが尽きる見込み・貸しの帳簿) と、
同じ日に「お任せします」で決めた「会計・経済・投資理論」(日本アクチュアリー会の 1 次試験の科目。略して KKT) の見方 (8.)。
本人の言う KKT はこの科目のこと。2026-10-14 の調べは、KKT をカルーシュ・キューン・タッカー条件 (制約つき最適化の決まり。これも略すと KKT) と
取りちがえて調べた。カルーシュ・キューン・タッカー条件は、経済の中の道具の 1 つとして、6. の限りの表にだけ使う。
調べは 2026-10-14 の経済の調べ (アクチュアリーの方法・MMT と貸し借り・制約つき最適化の点検表と、その批評)。批評が直したところは批評に従った。
読むもの (3 つとも要る): records/ の people.json・season_village.jsonl・season_household.jsonl・season_person.jsonl・ledger.jsonl、
state.json (era2.g6 の貸し借りと記録の道具・era2.fields の畑)、しまった出来事 data/archive/events_*.jsonl (貸し借り・覚え・交換・畑の実りの倍率)。
死・生まれる・よそから来るの見込みは era2._season_end の文から、畑の実りの決まりは era2._field_season の文から読む (数を写さない)。
節: 1. 生命表 2. 記録と決めごとの死亡率 3. 子の生まれ方 4. 蓄えが尽きる見込み 5. 貸しの帳簿 6. 限りの表 7. 村の会計
    8. 会計・経済・投資理論 (貸借対照表・減価償却・貸倒引当金・蓄えに回した割合・みんなの倉・記録の手間・投資の戻り・天気と蓄え・分散投資) 9. 前の調べの数とのちがい
6.〜8. は build_records.py が accounts.py で作った記録の列 (binding・accounts・sectors・grain_fate・store_days_all・balance) を読む。
列がなければ 6. は accounts.py で数え、7. と、8. のうち列を使うところは書かない。
ブートストラップは random.Random(SEED) で、足し算は math.fsum、並びは決まった順なので、何度動かしても、python3.11 と 3.13 でも同じ文になる。
--data: データの置き場所 (ふだんは $SOC_DATA か sim/society/data)
--out: 書き出すファイル (なければ画面に出す)。G6 の下書きは docs/society_phase/G6_measures.md
"""
import argparse
import inspect
import json
import math
import os
import random
import re
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent))
import accounts  # noqa: E402
import archive  # noqa: E402
import era2  # noqa: E402
import world  # noqa: E402

YEAR, SD, ADULT = era2.YEAR, world.SEASON_DAYS, era2.ADULT
SEED, REPS, RUNS, HORIZON = 20261014, 4000, 20000, 25  # ブートストラップの種・生命表のくり返し・蓄えのくり返し・何年先まで
BANDS = ((0, 1, "0 歳 (乳飲み子)"), (1, 5, "1〜4 歳"), (5, 15, "5〜14 歳"), (15, 40, "15〜39 歳"), (40, 55, "40〜54 歳"), (55, None, "55 歳から"))
FERT = tuple(range(15, 45, 5))  # 母の年齢の 5 歳ごとの区分 (15〜19 … 40〜44)
CODE_CAUSES = ("子", "病", "年")  # era2._season_end が決める死 (ザガと飢えは world.py)
DROP = (("病", "病"), ("子", "子の死"), ("ザガ", "ザガ"))  # 死因を除いた表
LOW = 75  # 蓄えが少ないときの例 (日分。前の調べと同じ)
LEVELS = ("印", "数え札", "封筒", "板")
END = accounts.END
CUT = ("刈った (村の蓄えに入った)", "刈った (自分の家の畑)")  # 刈り入れ (帳簿の理由)
ROWS_JA = (("production", "作った"), ("seed", "種"), ("consumption", "食べた・祭り"), ("losses", "損 (ヤギがいなくなった・土器や鎌が割れたもふくむ)"),
           ("transfers", "移った"), ("external", "よその村と"), ("residual", "記録にない差"))  # 部門の表の行 (accounts.ROWS)
FOODS = ("草の種", "木の実", "芋", "干し肉", "肉", "魚", "ピク", "乳")
WROTE = "2026-10-14"
FLAT = (0.9, 1.1)  # 食べた・祭り ÷ 必要な量が、どの時期もこの幅なら「必要な量とほぼ同じ」と読む (7. と 8.4)
GRAIN_MOST = 0.8  # 村の蓄えと家の倉の食べ物の kcal のうち、草の種がこの割合から上なら「ほとんど草の種」と読む (8.1 と 8.4)
WEAK = 0.3  # 相関の絶対値がどれもこれより小さければ「ほとんど関係がない」と読む (8.8)
# 食べ物の出どころ (8. の分散投資の見方)。肉 = ルクの肉・ピク・ヤギの干し肉
SRC = (("木の実", ("木の実",)), ("草の種", ("草の種",)), ("乳", ("乳",)), ("肉", ("肉", "ピク", "干し肉")), ("芋", ("芋",)), ("魚", ("魚",)))
PREV_YEARS = (14, 39)  # 前の調べ (2026-10-14) が、天気と蓄えの相関に使った年
OUT, IN = "ほかの村へ出した", "ほかの村から入った"  # 帳簿の、よその村との出し入れの理由
POT_WORK, GATHER, KEEP = "土器づくり", "採集", "記録をつける"  # season_person の仕事の名前
# era2._season_end の文から読む見込み (書き方が変わって読めなければ止まる。数をここに写さない)
CODE_RE = {
    "child": r'p_die = ([\d.]+) if c\["age"\] < (\d+) else ([\d.]+) if c\["age"\] < (\d+) else ([\d.]+)',
    "hungry": r'c\["hunger"\] >= ([\d.]+):\s+p_die = max\(p_die, ([\d.]+)\)',
    "old": r'p\["age"\] >= (\d+) and rng\.random\(\) < ([\d.]+) \* frac \* \(1 \+ \(p\["age"\] - \d+\) / (\d+)\)',
    "adult": r'era_at_least\(state, "(G\d)"\) and p\["age"\] < \d+ and rng\.random\(\) < \(([\d.]+) if p\["age"\] < (\d+) else ([\d.]+)\) \* frac',
    "mothers": r'p\["sex"\] == "女" and (\d+) <= p\["age"\] <= (\d+)',
    "fed": r'w\["hunger"\] >= ([\d.]+) or day - w\.get\("last_birth", [^)]+\) < YEAR',
    "birth": r'if rng\.random\(\) < ([\d.]+) \* frac:\s+c = _new_person',
    "come": r'\(([\d.]+) \+ min\(([\d.]+), store_days\(state\) / (\d+)\)\) \* frac',
}
# era2._field_season の文から読む畑の実りの決まり (三角分布の 下・上・いちばん多い値、草取りに要る時間、草取りの効き方)
FIELD_RE = {
    "tri": r'triangular\(([\d.]+), ([\d.]+), ([\d.]+)\)',
    "need": r'need = f\["seed"\] \* ([\d.]+) \+ ([\d.]+)',
    "weed": r'min\(1\.0, ([\d.]+) \+ ([\d.]+) \* f\["work"\] / need\)',
}


# ---------------- 小さな道具 ----------------

def jsonl(f):
    with open(f, encoding="utf-8") as fh:
        return [json.loads(x) for x in fh if x.strip()]


def dl(d):
    """通しの日 → 「40年30日目 (4829 日目)」(年は過ぎた年の数。1 年 = 120 日)"""
    return f"{d // YEAR}年{d % YEAR + 1}日目 ({d} 日目)"


def n0(x):
    return f"{x:,.0f}"


def pc(x, nd=0):
    return f"{x * 100:.{nd}f}%"


def pr(x):
    """見込みの割合 (0.1% まで。ちょうど 0 と 1 のほかは、0%・100% と書かない)"""
    return "0%" if x == 0 else "100%" if x == 1 else "0.1% より下" if x < 0.0005 else "99.9% より上" if x > 0.9995 else pc(x, 1)


def rng_of(*key):
    """くり返しごとの乱数 (種は整数だけ。どの順に呼んでも同じ)"""
    return random.Random(SEED * 1000 + int("".join(str(k) for k in key)))


def mid95(xs):
    v = sorted(xs)
    return v[round(0.025 * (len(v) - 1))], v[round(0.975 * (len(v) - 1))]


def mean_sd(xs):
    m = math.fsum(xs) / len(xs)
    return m, math.sqrt(math.fsum((x - m) ** 2 for x in xs) / (len(xs) - 1)) if len(xs) > 1 else 0.0


def runs(xs, step):
    """続いた値をまとめる: [1, 2, 3, 5] → [[1, 3], [5, 5]]"""
    out = []
    for x in xs:
        if out and x - out[-1][1] == step:
            out[-1][1] = x
        else:
            out.append([x, x])
    return out


def runs_ja(xs, step, unit=""):
    return "、".join(f"{a}〜{b}{unit}" if a != b else f"{a}{unit}" for a, b in runs(xs, step))


def pois95(lam):
    """ポアソン分布 (平均 lam) の数の 95% の幅 (2.5% と 97.5% の点)"""
    k, p = 0, math.exp(-lam)
    c, lo = p, None
    while True:
        if lo is None and c >= 0.025:
            lo = k
        if c >= 0.975:
            return lo, k
        k += 1
        p *= lam / k
        c += p


def worth(goods):
    """物 → 草の種にした値うち (つかみ。era2.VALUE。よその村と動く物は、みな VALUE にある)"""
    return math.fsum(era2.VALUE[k] * n for k, n in goods.items())


# ---------------- コードの見込み ----------------

def code_rates():
    src = inspect.getsource(era2._season_end)
    m = {}
    for k, pat in CODE_RE.items():
        x = re.search(pat, src)
        if not x:
            raise SystemExit(f"era2._season_end の書き方が変わった ({k} が読めない)。econ_report.py の CODE_RE を直す")
        m[k] = x.groups()
    c = m["child"]
    return {"child": ((int(c[1]), float(c[0])), (int(c[3]), float(c[2])), (ADULT, float(c[4]))),
            "hungry": tuple(float(x) for x in m["hungry"]), "old": (int(m["old"][0]), float(m["old"][1]), int(m["old"][2])),
            "adult": (m["adult"][0], float(m["adult"][1]), int(m["adult"][2]), float(m["adult"][3])),
            "mothers": tuple(int(x) for x in m["mothers"]), "fed": float(m["fed"][0]), "birth": float(m["birth"][0]),
            "come": tuple(float(x) for x in m["come"])}


def p_season(R, age):
    """コードの、季節の終わりに亡くなる見込み (飢えていない人。若い大人の病は R["adult"][0] から)"""
    if age < ADULT:
        return next(p for a, p in R["child"] if age < a)
    o, base, div = R["old"]
    if age >= o:
        return min(1.0, base * (1 + (age - o) / div))
    return R["adult"][1] if age < R["adult"][2] else R["adult"][3]


def code_life(R):
    """コードの見込みだけの生命表 (季節の終わりごと。生まれた季節の終わりは数えない、年齢は (日 − 生まれた日) // YEAR)"""
    S, s, j = [], 1.0, 0
    while s > 1e-12 and j < 200 * YEAR // SD:
        S.append(s)
        j += 1
        s *= 1 - p_season(R, j * SD // YEAR)
    f, k = SD / YEAR, ADULT * YEAR // SD
    return {"e0": f * math.fsum(S), "e15": f * math.fsum(S[k:]) / S[k - 1], "q0": 1 - S[YEAR // SD - 1], "l15": S[k - 1]}


def code_tfr(R):
    """コードで生める子の数の上限 (いつも飢えておらず、住まいと男がいて、生めるときはいつも 1 季節 R["birth"])"""
    lo, hi = R["mothers"]
    gap = -(-YEAR // SD) - 1  # 生んだあと、YEAR 日たつまでの季節の終わりの数
    free, wait, out = 1.0, [0.0] * gap, []
    for _ in range((hi - lo + 1) * YEAR // SD):
        b = free * R["birth"]
        out.append(b)
        free, wait = free - b + wait[0], wait[1:] + [b]
    return math.fsum(out)


# ---------------- 1. 生命表 ----------------

def spans(people, s, e):
    """期間 (s, e] に村にいた人: (人, いた最初の日, 最後の日)。よそから来た人は来た日から、生きている人は e で打ち切り"""
    out = []
    for p in people:
        a = max(s, p["came_day"])
        b = min(x for x in (e, p["died_day"], p["left_day"]) if x is not None)
        if b > a:
            out.append((p, a, b))
    return out


def years_by(born, a, b, cuts):
    """a〜b 日に住んだ年 (1 年 = YEAR 日) を、年齢の区切り ((下, 上), …) ごとに"""
    return [max(0, (b if hi is None else min(b, born + hi * YEAR)) - max(a, born + lo * YEAR)) / YEAR for lo, hi in cuts]


def band_of(age):
    return next(i for i, (lo, hi, _) in enumerate(BANDS) if age >= lo and (hi is None or age < hi))


def life(py, d, last=None):
    """略式の生命表 (区分の中は死亡率が一定)。55 歳からは終わりのない区分。
    last: 55 歳からに住んだ年か亡くなった人が 0 のときに使う死亡率 (ブートストラップ用。全体の値)"""
    m = [d[i] / py[i] if py[i] else 0.0 for i in range(len(BANDS))]
    if last is not None and not (py[-1] and d[-1]):
        m[-1] = last
    rows, l = [], 1.0
    for (lo, hi, _), mi in zip(BANDS, m):
        if hi is None:
            q, L = 1.0, (l / mi if mi else math.inf)
        else:
            q = 1 - math.exp(-(hi - lo) * mi)
            L = l * q / mi if mi else l * (hi - lo)
        rows.append({"m": mi, "q": q, "l": l, "L": L})
        l *= 1 - q
    for i, r in enumerate(rows):
        r["e"] = math.fsum(x["L"] for x in rows[i:]) / r["l"] if r["l"] else 0.0
    return rows


def summary(rows):
    return {"e0": rows[0]["e"], "e15": rows[3]["e"], "q0": rows[0]["q"], "l15": rows[3]["l"]}


def l_at(rows, x):
    """生命表の x 歳まで生きる割合 (区分の中は死亡率が一定)"""
    i = band_of(x)
    return rows[i]["l"] * math.exp(-rows[i]["m"] * (x - BANDS[i][0]))


def demography(people, village, R, s, e):
    sp = spans(people, s, e)
    cuts = [(lo, hi) for lo, hi, _ in BANDS]
    per = []  # 人ごと: (年齢の区分ごとの住んだ年, 亡くなった区分, 死因)
    for p, a, b in sp:
        died = p["died_day"] is not None and s < p["died_day"] <= e
        per.append((years_by(p["born_day"], a, b, cuts), band_of((p["died_day"] - p["born_day"]) // YEAR) if died else None,
                    p["death_cause"] if died else None))

    def tally(idx):
        py = [math.fsum(per[i][0][k] for i in idx) for k in range(len(BANDS))]
        ds = {c: [0] * len(BANDS) for c in ("all",) + tuple(c for c, _ in DROP)}  # 全部と、死因ごとにその死を除いた数
        for i in idx:
            _, b, cause = per[i]
            if b is not None:
                for c in ds:
                    if cause != c:
                        ds[c][b] += 1
        return py, ds

    py, ds = tally(range(len(per)))
    tables = {c: life(py, d) for c, d in ds.items()}
    boot = {c: {k: [] for k in ("e0", "e15", "q0", "l15")} for c in ds}
    rng = rng_of(9, 1)
    for _ in range(REPS):
        bpy, bds = tally([rng.randrange(len(per)) for _ in per])
        for c in ds:
            for k, v in summary(life(bpy, bds[c], tables[c][-1]["m"])).items():
                boot[c][k].append(v)
    # 2. コードからの見込み: 季節の終わりごとに、村にいた人の 1 季節の見込みを足す
    ends = [r["season_end_day"] for r in village if s < r["season_end_day"] <= e]
    exp = [[] for _ in BANDS]
    for p, a, b in sp:
        for D in ends:
            if p["born_day"] < D and p["came_day"] < D and (p["died_day"] is None or p["died_day"] >= D) and (p["left_day"] is None or p["left_day"] >= D):
                age = (D - p["born_day"]) // YEAR
                exp[band_of(age)].append(p_season(R, age))
    obs = [0] * len(BANDS)
    other = {}
    for p, a, b in sp:
        if p["died_day"] is not None and s < p["died_day"] <= e:
            if p["death_cause"] in CODE_CAUSES:
                obs[band_of((p["died_day"] - p["born_day"]) // YEAR)] += 1
            else:
                other[p["death_cause"]] = other.get(p["death_cause"], 0) + 1
    return {"spans": sp, "old": sum(1 for x in per if x[0][-1] > 0), "py": py, "ds": ds, "tables": tables, "boot": boot, "exp": [math.fsum(x) for x in exp], "obs": obs, "other": other}


# ---------------- 3. 子の生まれ方 ----------------

def fertility(people, sp, table, s, e):
    by_id = {p["id"]: p for p in people}
    births = [p for p in people if p["origin"] == "生まれた" and s < p["born_day"] <= e]
    cuts = [(x, x + 5) for x in FERT]
    at = {p["id"]: i for i, (p, a, b) in enumerate(sp)}
    per = [(years_by(p["born_day"], a, b, cuts) if p["sex"] == "女" else [0.0] * len(FERT), [0] * len(FERT)) for p, a, b in sp]  # 人ごと: 住んだ年・生んだ子
    nomom = 0
    for c in births:
        m = by_id.get(c.get("mother_id"))
        k = ((c["born_day"] - m["born_day"]) // YEAR - FERT[0]) // 5 if m else -1
        if 0 <= k < len(FERT) and m["id"] in at:
            per[at[m["id"]]][1][k] += 1
        else:
            nomom += 1

    def rates(idx):
        wy = [math.fsum(per[i][0][k] for i in idx) for k in range(len(FERT))]
        nb = [sum(per[i][1][k] for i in idx) for k in range(len(FERT))]
        return wy, nb, [nb[k] / wy[k] if wy[k] else 0.0 for k in range(len(FERT))]

    wy, nb, asfr = rates(range(len(per)))
    rng = rng_of(9, 3)
    boot = [5 * math.fsum(rates([rng.randrange(len(per)) for _ in per])[2]) for _ in range(REPS)]
    girls = sum(1 for c in births if c["sex"] == "女")
    f = girls / len(births) if births else 0.5
    step = 1 / YEAR  # 1 日ずつ足す (生命表の生きる割合 × 出生率 × 娘の割合)
    pts = [(x0 + (i + 0.5) * step, asfr[k]) for k, x0 in enumerate(FERT) for i in range(5 * YEAR)]
    surv = [(x, a * f * l_at(table, x) * step) for x, a in pts]
    nrr = math.fsum(w for _, w in surv)

    def g(r):
        return math.fsum(w * math.exp(-r * x) for x, w in surv) - 1

    lo, hi = -0.2, 0.2
    for _ in range(80):
        mid = (lo + hi) / 2
        lo, hi = (mid, hi) if g(mid) > 0 else (lo, mid)
    r = (lo + hi) / 2
    return {"births": births, "wy": wy, "nb": nb, "asfr": asfr, "tfr": 5 * math.fsum(asfr), "girls": girls, "f": f, "nrr": nrr, "r": r, "nomom": nomom, "tfr95": mid95(boot)}


# ---------------- 4. 蓄えが尽きる見込み ----------------

def drifts(village, era):
    """その時期の中の、続いた 2 つの季節の差 (はじめの季節の差は、前の時期とまたぐので入れない)。
    (a) 人数を固定: 蓄えの kcal の差 ÷ その季節の終わりの 1 日分 (= store_kcal / store_days)。(b) 人数も入れる: store_days の差"""
    rows = [r for r in village if r["era"] == era]
    a, b = [], []
    for p, r in zip(rows, rows[1:]):
        a.append((r["store_kcal"] - p["store_kcal"]) * r["store_days"] / r["store_kcal"] if r["store_kcal"] else 0.0)
        b.append(r["store_days"] - p["store_days"])
    return rows, a, b


def ruin(xs, u, key):
    """4 季節 (続いた差 4 つ) をひとかたまりに選び直して HORIZON 年並べ、u 日分から 0 以下になる割合"""
    blocks = [xs[i:i + 4] for i in range(0, len(xs) - 3, 4)]
    if not blocks:
        return None, 0
    rng, hit = rng_of(*key), 0
    for _ in range(RUNS):
        st = u
        for _ in range(HORIZON):
            for x in blocks[rng.randrange(len(blocks))]:
                st += x
                if st <= 0:
                    break
            if st <= 0:
                hit += 1
                break
    return hit / RUNS, len(blocks)




def corr(a, b):
    """相関係数 (ピアソン。年ごとの 2 つの数がいっしょに動く度合い)。3 つより少ないか、どちらかが動かなければ None"""
    n = len(a)
    if n < 3:
        return None
    ma, mb = math.fsum(a) / n, math.fsum(b) / n
    va, vb = math.fsum((x - ma) ** 2 for x in a), math.fsum((y - mb) ** 2 for y in b)
    return math.fsum((x - ma) * (y - mb) for x, y in zip(a, b)) / math.sqrt(va * vb) if va and vb else None


def cr(x):
    return "-" if x is None else f"{x + 0.0:+.2f}"


def gw(goods):
    """{"ヤギ": 2, "土器": 18} → 「ヤギ 2 頭・土器 18 個」(era2._gw と同じ形)"""
    return "・".join(f"{k} {int(n) if float(n).is_integer() else n:,} {era2.UNIT.get(k, '')}".rstrip() for k, n in goods.items() if n) or "なし"


def parse_goods(s):
    """era2._gw の文 (「草の種 2047 つかみ・ヤギ 2 頭」) → {物: 数}。物の名前が VALUE にないか、形が読めなければ None"""
    out = {}
    for part in s.split("・"):
        m = re.fullmatch(r"(\S+) (\d+) (\S+)", part.strip())
        if not m or m.group(1) not in era2.VALUE or era2.UNIT.get(m.group(1)) != m.group(3):
            return None
        out[m.group(1)] = out.get(m.group(1), 0) + int(m.group(2))
    return out


def season_of(village, day):
    """通しの日 → その日をふくむ季節の行 (なければ None)"""
    return next((r for r in village if r["season_start_day"] <= day <= r["season_end_day"]), None)


def mk(x, unit=1e6):
    """百万 kcal (unit=1e4 なら万 kcal) で小数 1 けた。-0.0 は 0.0"""
    return "-" if x is None else f"{round(x / unit, 1) + 0.0:,.1f}"


# ---------------- 5. 貸しの帳簿 ----------------

def loans(state, ledger, village, e):
    """よその村への貸し (accounts.Loans で出来事をたどる。量は VALUE で草の種のつかみ)。
    種類: 貸して (季節の集まりで決めて貸した。出来事「貸し借り」) と、交換で足りない分 (交換に行った先で向こうが払いきれず、あとで返すと言った分。
    出来事「交換」の文の [D..]。期限は 2 季節)。交換で得した分は、足りない分を除いて数える (足りない分は貸しの帳簿で数えるので、二重に数えない)"""
    g = state["era2"]["g6"]
    start = g.get("start") or 0
    ev = [x for x in state["events"] if x["day"] >= start and x["type"] in ("交換", "交換に行く", "貸し借り", "覚え", "確かめる", "記録", "よその村")]
    opened = {k: (v, None) for k, v in g["open"].items() if v is not None}
    for x in ev:
        t = (x.get("data") or {}).get("tool")
        if x["type"] == "記録" and t in opened and x["day"] == opened[t][0] and opened[t][1] is None:
            opened[t] = (x["day"], x["id"])
    L = accounts.Loans(g["debts"], ev)
    big = max((x["id"] for x in ev), default=0) + 1
    rows = []
    for d in g["debts"]:
        i = d["id"]
        orig = L.orig[i]
        lent = accounts.handfuls(orig)
        ret = math.fsum(accounts.handfuls(b) for _, b in L.back.get(i, []))
        closed = d["status"] != "まだ"
        owed = L.owed(i, big)
        said = [re.search(r"覚えでは (.+?) を貸したはずだった", x["text"]) for x in ev if x["type"] == "覚え" and (x.get("data") or {}).get("debt") == i]
        said = [parse_goods(m.group(1)) for m in said if m]
        if None in said:
            raise SystemExit(f"出来事「覚え」の文の物と数が読めない ({i})。econ_report.py の parse_goods を直す")
        mem = (math.fsum(accounts.handfuls(x) for x in said) if said
               else math.fsum(era2.VALUE[k] * math.ceil(n * d["mem"]["village"]) for k, n in d["goods"].items()))
        lid = L.made.get(i)
        level = [t for t in LEVELS if t in opened and (opened[t][0] < d["day"] or (opened[t][0] == d["day"] and (opened[t][1] is None or (lid is not None and opened[t][1] < lid))))]
        rows.append({"id": i, "kind": L.kind.get(i, "?"), "lender": d["lender"], "other": d["other"], "day": d["day"], "due": d["due"], "goods": orig,
                     "lent": lent, "ret": ret, "lost": lent - ret if closed else 0.0, "open": accounts.handfuls(owed) if owed is not None and not closed else 0.0,
                     "late": max(0, e - d["due"]) if not closed else 0, "level": level[-1] if level else "なし", "proof": d.get("proof"),
                     "mem": mem, "mem_from": "覚え" if said else "お題", "status": d["status"]})
    names = {o["id"]: o["name"] for o in g.get("others", [])}
    # よその村との出し入れ (出来事の moves。村と家の両方) と、交換で得した分
    net, items, trades, trips = 0.0, {}, [], {}
    for x in ev:
        dt = x.get("data") or {}
        mv = dt.get("moves") or []
        for m in mv:
            for k, n in m[2].items():
                items[k] = items.get(k, 0) - m[1] * n
        net -= math.fsum(m[1] * accounts.handfuls(m[2]) for m in mv)
        if dt.get("trip"):  # 交換に行った (出かけるときに持って出て、帰るときに持ち帰る。向こうの村の出来事には moves がない)
            t = trips.setdefault(dt["trip"], {"other": dt.get("other"), "day": x["day"], "net": [], "debts": []})
            t["net"] += [m[1] * accounts.handfuls(m[2]) for m in mv]
            t["debts"] += [j for j in accounts.DEBT_RE.findall(x["text"]) if L.kind.get(j) == accounts.SHORT and L.made.get(j) == x["id"]]
        elif x["type"] == "交換" and mv:  # 季節の集まりで、よその村の申し出を受けた
            gave = {k: n for m in mv if m[1] < 0 for k, n in m[2].items()}
            got = {k: n for m in mv if m[1] > 0 for k, n in m[2].items()}
            trades.append({"offer": dt.get("offer"), "day": x["day"], "gave": gave, "got": got,
                           "gain": accounts.handfuls(got) - accounts.handfuls(gave)})
    trip_rows = [{"trip": k, "other": t["other"], "day": t["day"], "debts": t["debts"],
                  "gain": math.fsum(t["net"] + [accounts.handfuls(L.orig[j]) for j in t["debts"]])} for k, t in trips.items()]
    lg = {}
    for r in ledger:
        if r["reason"] in (OUT, IN) and r["item"] in era2.VALUE:
            lg[r["item"]] = lg.get(r["item"], 0.0) - r["amount"]
    lg_net = math.fsum(era2.VALUE[k] * n for k, n in lg.items())
    return {"rows": rows, "opened": opened, "names": names, "net": net, "items": items, "trades": trades, "trips": trip_rows, "lg_net": lg_net,
            "spread": era2._g6_spread(state)}


def record_cost(rows, village, ledger):
    """貸しを記録に残す手間 (era2._g6_records の need["交換"] と同じ数え方): 貸しを記録する季節に、よその村と動いた物 (帳簿の「ほかの村へ出した・入った」を
    物ごとに足す。出たのも入ったのも数える) を TOKEN で割って切り上げた数 + その季節の新しい貸しの数。その季節の交換を全部残さないと、記録にならない。
    集まりの貸しは季節の終わりの日の集まりで決まるので、次の季節に記録する。交換で足りない分は、その日の季節"""
    moved = {}
    for r in ledger:
        if r["reason"] in (OUT, IN) and r["kind"] == "動き" and r["amount"] is not None:
            m = moved.setdefault(r["season_end_day"], {})
            m[r["item"]] = m.get(r["item"], 0) + abs(r["amount"])

    def sea(r):
        s = season_of(village, r["day"] + (1 if r["kind"] == accounts.LENT else 0))
        return s["season_end_day"] if s else None
    per = {}
    for r in rows:
        per.setdefault(sea(r), []).append(r["id"])
    out = {}
    for D, ids in per.items():
        if D is None:
            continue
        need = sum(math.ceil(n / era2.TOKEN.get(k, 100)) for k, n in sorted(moved.get(D, {}).items())) + len(ids)
        out[D] = {"ids": ids, "tokens": need, "moved": dict(sorted(moved.get(D, {}).items()))}
    return {r["id"]: sea(r) for r in rows}, out


# ---------------- 7. 村の会計 ----------------

def full_years(village):
    """4 季節がそろった年 (夏から春) → その年の季節の行"""
    by = {}
    for r in village:
        by.setdefault(r["year"], []).append(r)
    return {y: rs for y, rs in by.items() if len(rs) == 4}


def field_ratio(state):
    """年 → 畑の実りの倍率 (出来事「畑」の ratio。夏のはじめに決まり、前の年の最後の日の出来事に書かれる)"""
    return {(x["day"] + 1) // YEAR: x["data"]["ratio"] for x in state["events"] if x["type"] == "畑" and (x.get("data") or {}).get("ratio") is not None}


def fs(rows, f):
    return math.fsum(f(r) for r in rows)


def eat_ratio(village):
    """時期ごとの 食べた・祭り ÷ 必要な量 (7. の表と同じ足し方。7. と 8.4 の読みに使う)"""
    out = []
    for x in era2.ORDER2:
        rs = [r for r in village if r["era"] == x]
        if rs:
            out.append((fs(rs, lambda r: r["accounts"]["eaten"]) + fs(rs, lambda r: r["accounts"]["feast"])) / fs(rs, lambda r: r["accounts"]["need"]))
    return out


def flat_eat(xs):
    """食べた量が、どの時期も必要な量とほぼ同じか (FLAT の幅)"""
    return bool(xs) and all(FLAT[0] <= x <= FLAT[1] for x in xs)


def grain_share(v):
    """季節の終わりの、村の蓄えと家の倉 (だれもいなくなった家の倉もふくむ) の食べ物の kcal のうち、草の種の割合 (列 balance から。大人の手元は入れない)"""
    b = (v.get("balance") or {})
    if not b:
        return None
    tot = math.fsum([b["村"]["food"]["kcal"], b["家"]["food"]["kcal"]])
    g = math.fsum([(b["村"]["food"]["by_item"] or {}).get("草の種", 0), (b["家"]["food"]["by_item"] or {}).get("草の種", 0)]) * era2.GRAIN
    return g / tot if tot else None


def short_years(years, era):
    """その時期だけの年のうち、食べ物の純生産が必要な量に届かなかった年"""
    return [y for y, rs in sorted(years.items()) if all(r["era"] == era for r in rs)
            and fs(rs, lambda r: r["accounts"]["food_net"]) < fs(rs, lambda r: r["accounts"]["need"])]


def fell(r0, r1):
    """2 つの季節のあいだの蓄えの日数の減りを、蓄えの kcal の減りと、食べる人の増え (1 日分の増え) に分ける。
    文に出す割合は対数で分けたもの (ln(kcal の比) ÷ ln(日数の比))。差で分けると、1 日分をはじめの季節に
    固定するか終わりの季節に固定するかで割合が動くので、その幅もそえる。
    → (文, (対数の割合, 差で分けた割合の小さいほう, 大きいほう)。どちらかが減っていなければ None)"""
    k, d = r1["store_kcal"] / r0["store_kcal"], r1["store_days"] / r0["store_days"]
    share = None
    if d < 1 and k < 1:
        a = (1 - k) / (1 - d)  # 1 日分をはじめの季節に固定: (kcal の減り ÷ はじめの 1 日分) ÷ 日数の減り
        b = a * d / k  # 1 日分を終わりの季節に固定
        share = (math.log(k) / math.log(d), min(a, b), max(a, b))
    part = (f"。日数の減りのうち、蓄えの kcal の減りによるのは {pc(share[0])} ほど (対数で分けた割合。分け方で "
            f"{pc(share[1])}〜{pc(share[2])} と動く。残りは食べる人の増え)") if share is not None else ""
    return (f"蓄えは {n0(r0['store_kcal'] / 1e4)} → {n0(r1['store_kcal'] / 1e4)} 万 kcal、日数は {r0['store_days']} → {r1['store_days']} 日分、"
            f"人は {r0['population']} → {r1['population']} 人{part}"), share


# ---------------- 8. 会計・経済・投資理論 ----------------

def food_stock(ledger):
    """季節の終わりの日 → (食べ物の残りの増え kcal, ヤギの頭数の増え)。帳簿の「季節のはじめの残り」と「季節の終わりの残り」から (村 + 家。だれもいなくなった家の倉もふくむ)"""
    f, g = {}, {}
    for r in ledger:
        if r["kind"] != "残り":
            continue
        sign = -1 if r["reason"] == accounts.START else 1
        if accounts.part(r["item"]) == "food":
            f.setdefault(r["season_end_day"], []).append(sign * r["kcal"])
        elif r["item"] == "ヤギ":
            g.setdefault(r["season_end_day"], []).append(sign * r["amount"])
    return {D: (math.fsum(f.get(D, [])), sum(g.get(D, []))) for D in sorted(set(f) | set(g))}


def saving(rows, stock):
    """蓄えに回した割合: 食べ物だけ (食べ物の残りの増え ÷ 食べ物の純生産) と、ヤギも入れた割合 ((食べ物 + ヤギの増え) ÷ (食べ物の純生産 + ヤギの増減))"""
    df = math.fsum(stock[r["season_end_day"]][0] for r in rows)
    dg = sum(stock[r["season_end_day"]][1] for r in rows) * era2.GOAT_WORTH
    fn = fs(rows, lambda r: r["accounts"]["food_net"])
    gn = fs(rows, lambda r: r["accounts"]["goats"]["net"])
    return {"food_net": fn, "d_food": df, "food": df / fn if fn else None, "goat_net": gn, "d_goat": dg,
            "with_goats": (df + dg) / (fn + gn) if fn + gn else None}


def flows(hhs, village):
    """みんなの倉 (村の蓄え) に入れた・取った (season_household.village_flow。大人の分、草の種にしたつかみ)。年ごと・倉のある家とない家に分ける"""
    yr = {r["season_end_day"]: r["year"] for r in village}
    by, cum, seasons = {}, {}, {}
    for h in hhs:
        f = h.get("village_flow")
        if not f:
            continue
        D = h["season_end_day"]
        y = by.setdefault(yr[D], {"seasons": set(), "in": [], "out": [], "keep": [0, 0, 0], "none": [0, 0, 0]})
        y["seasons"].add(D)
        y["in"].append(f["in"])
        y["out"].append(f["out"])
        k = y["keep" if h.get("keep") else "none"]
        k[0] += f["in"]
        k[1] += f["out"]
        k[2] += h.get("adults") or 0
        c = cum.setdefault(h["household_id"], [0, 0, 0])
        c[0] += f["in"]
        c[1] += f["out"]
        c[2] += 1
        seasons[D] = True
    return by, cum, sorted(seasons)


def field_chain(state, village):
    """畑の実り (state の era2.fields。刈り終わった畑だけ): まいた 1 つかみあたり、設定の平均 → 実際に引かれた年の倍率 → 草取りのあと → ヤギに荒らされた分と切り捨てのあと → 刈った"""
    src = inspect.getsource(era2._field_season)
    m = {k: re.search(p, src) for k, p in FIELD_RE.items()}
    if not all(m.values()):
        raise SystemExit("era2._field_season の書き方が変わった (畑の実りの決まりが読めない)。econ_report.py の FIELD_RE を直す")
    lo, hi, mode = (float(x) for x in m["tri"].groups())  # random.triangular(下, 上, いちばん多い値)
    na, nb = (float(x) for x in m["need"].groups())
    w0, w1 = (float(x) for x in m["weed"].groups())
    rt = field_ratio(state)
    era_of = {(r["year"], r["season"]): r["era"] for r in village}
    by, skipped = {}, 0
    for f in state["era2"]["fields"]:
        if f["state"] != "刈った":
            continue
        y = f["day"] // YEAR + 1  # 秋にまいて、次の年の夏のはじめに実る
        if y not in rt:
            skipped += 1
            continue
        weed = min(1.0, w0 + w1 * f["work"] / (f["seed"] * na + nb))
        b = by.setdefault(y, {"seed": [], "ratio": [], "weed": [], "yield": [], "cut": []})
        b["seed"].append(f["seed"])
        b["ratio"].append(f["seed"] * rt[y])
        b["weed"].append(f["seed"] * rt[y] * weed)
        b["yield"].append(f["yield"])
        b["cut"].append(f["harvested"])
    years = {y: {k: math.fsum(v) for k, v in b.items()} for y, b in sorted(by.items())}
    for y, b in years.items():
        b["era"] = era_of.get((y, "夏"))
        b["r"] = rt[y]
    tot = {k: math.fsum(b[k] for b in years.values()) for k in ("seed", "ratio", "weed", "yield", "cut")}
    return {"tri": (lo, hi, mode), "mean": (lo + hi + mode) / 3, "need": (na, nb), "weed": (w0, w1), "years": years, "tot": tot, "skipped": skipped,
            "fields": sum(len(b["seed"]) for b in by.values())}


def weather(village, rt, chain):
    """天気 (畑の実りの倍率) と蓄え: 年ごとに、倍率と (a) 夏の終わりの store_days − その前の春の終わりの store_days、
    (b) 同じ 2 つの季節の蓄えの kcal の増え ÷ 夏の終わりの 1 日分 (人数を固定)、(c) 刈った量 ÷ まいた量 (畑)"""
    by = {(r["year"], r["season"]): r for r in village}
    out = []
    for y, x in sorted(rt.items()):
        a, b = by.get((y, "夏")), by.get((y - 1, "春"))
        if not a or not b or not a["store_kcal"]:
            continue
        c = chain["years"].get(y)
        out.append({"year": y, "ratio": x, "era": a["era"], "era_prev": b["era"], "days": a["store_days"] - b["store_days"],
                    "fixed": (a["store_kcal"] - b["store_kcal"]) * a["store_days"] / a["store_kcal"], "cut": c["cut"] / c["seed"] if c and c["seed"] else None})
    return out


def sources(ledger, persons, years):
    """食べ物の出どころごとの、年ごとの 1 人・年あたり kcal (作った量 ÷ (いた人 (子もふくむ) のいた日数 ÷ YEAR))"""
    which = {i: s for s, items in SRC for i in items}
    prod = {}
    for r in ledger:
        if r["kind"] == "動き" and accounts.KIND.get(r["reason"]) == "production" and accounts.part(r["item"]) == "food":
            prod.setdefault(r["season_end_day"], {}).setdefault(which.get(r["item"], "そのほか"), []).append(r["kcal"])
    pdays = {}
    for r in persons:
        pdays[r["season_end_day"]] = pdays.get(r["season_end_day"], 0) + r["present_to"] - r["present_from"] + 1
    out = {}
    for y, rs in sorted(years.items()):
        py = sum(pdays.get(r["season_end_day"], 0) for r in rs) / YEAR
        if py:
            out[y] = {s: math.fsum(x for r in rs for x in prod.get(r["season_end_day"], {}).get(s, [])) / py for s, _ in SRC + (("そのほか", ()),)}
    return out


def spread_stats(series, ys):
    """分散投資の見方: 出どころごとの平均・ばらつき (標準偏差)・変動係数と、合計の変動係数・出どころの変動係数を量で重みをつけた平均・相関の表"""
    names = [s for s, _ in SRC]
    cols = {s: [series[y][s] for y in ys] for s in names}
    tot = [math.fsum(series[y][s] for s in names) for y in ys]
    st = {s: mean_sd(cols[s]) for s in names}
    mt, sdt = mean_sd(tot)
    parts = math.fsum(sd for _, sd in st.values())
    return {"n": len(ys), "st": st, "mean": mt, "sd": sdt, "cv": sdt / mt if mt else None, "cv_parts": parts / mt if mt else None,
            "matrix": {a: {b: corr(cols[a], cols[b]) for b in names} for a in names}}


def pots_return(village, persons):
    """土器の戻り: 作る手間 (土器づくりの日 ÷ 作った数) と、守った草の種 (季節ごとに min(草の種, 土器 × POT_HOLD) × PEST_LOSS。おおよそ)"""
    days = {}
    for r in persons:
        n = r["days_by_activity"].get(POT_WORK, 0)
        if n:
            days[r["season_end_day"]] = days.get(r["season_end_day"], 0) + n
    out = {}
    for v in village:
        b = (v.get("binding") or {}).get("pots")
        if not b:
            continue
        x = out.setdefault(v["era"], {"seasons": 0, "made": 0, "days": 0, "pot_seasons": 0, "saved": [], "limit": 0})
        x["seasons"] += 1
        x["made"] += v.get("pots_made") or 0
        x["days"] += days.get(v["season_end_day"], 0)
        x["pot_seasons"] += b["pots"]
        x["saved"].append(min(b["grain"], b["hold"]) * era2.PEST_LOSS)
        x["limit"] += 1 if b["at_limit"] else 0
    return out


def wear_sum(village, key, eras):
    rs = [(v["balance"]["wear"] or {}).get(key) for v in village if v["era"] in eras and isinstance(v.get("balance"), dict)]
    rs = [x for x in rs if x and (x["start"] or x["made"])]
    st, mdx, br = sum(x["start"] for x in rs), sum(x["made"] for x in rs), sum(x["broken"] for x in rs)
    return {"seasons": len(rs), "start": st, "made": mdx, "broken": br, "rate": br / st if st else None, "rate2": br / (st + mdx) if st + mdx else None}



# ---------------- 文にする ----------------

def report(data):
    rec = Path(data) / "records"
    people = json.loads((rec / "people.json").read_text(encoding="utf-8"))
    village = jsonl(rec / "season_village.jsonl")
    hhs = jsonl(rec / "season_household.jsonl")
    persons = jsonl(rec / "season_person.jsonl")
    ledger = jsonl(rec / "ledger.jsonl")
    state = archive.load_state(data)
    R = code_rates()
    e = village[-1]["season_end_day"]
    s = next(r["season_start_day"] - 1 for r in village if r["era"] == "G4")
    out = []
    w = out.append
    w("# G6 の測った数 (人の生き死に・蓄え・貸し・限り・村の会計・会計/経済/投資理論の見方): 評価の下書きに入れる節")
    w("")
    w(f"書いたのは Claude ({WROTE})。G6 の評価の下書き (G6.md) に入れる、測った数の節の下書き。"
      "数は `python3.13 sim/society/tools/econ_report.py` で作り直せる (`--out docs/society_phase/G6_measures.md`)。"
      "作り直すには、records (`sim/society/data/records/`)・state.json・しまった出来事 (`data/archive/`) の 3 つがみな要る。")
    w("")
    w(f"記録の最後の日は {dl(e)}。日付の「40年30日目」は、はじめから 40 年たった年の 30 日目 (この世界の 1 年は 120 日 = 季節 30 日 × 4)。"
      "ここの数はみな【シ】(シミュレーションの中だけで分かる数。正確な年齢・本当の量を使う)。"
      "ダッシュボードにも村人のお題にも出さない (docs/dashboard_data_model.md §5)。人数が少ないので、1 つの値には幅をいっしょに書く。【読み】と書いたところは Claude の読み。")
    w("")

    # ---- 1 ----
    D = demography(people, village, R, s, e)
    T = D["tables"]["all"]
    B = D["boot"]
    cl = code_life(R)
    ds = D["ds"]
    w(f"## 1. 生命表 (G4 から後: {dl(s)} 〜 {dl(e)})")
    w("")
    w(f"- 数え方: people.json の {len(people)} 人のうち、この期間に村にいた {len(D['spans'])} 人。住んでいた年数は 1 年 = {YEAR} 日で数え、"
      f"よそから来た人は来た日から、生きている人は {e} 日目で打ち切った。年齢の区分の中では死亡率が一定とした略式の表 (qx = 1 − exp(−区分の年数 × mx))")
    w(f"- 幅: 人を選び直すブートストラップ {REPS:,} 回 (random.Random の種は決めてある) の 2.5%〜97.5%")
    w("")
    w("| 年齢 | 住んでいた年数 | 亡くなった人 | うちザガを除く | 1 年の死亡率 mx | 区分の中で亡くなる割合 qx | 区分のはじめまで生きる割合 lx | 平均余命 ex (年) |")
    w("|---|---:|---:|---:|---:|---:|---:|---:|")
    for i, (_, _, name) in enumerate(BANDS):
        r = T[i]
        w(f"| {name} | {D['py'][i]:.1f} | {ds['all'][i]} | {ds['ザガ'][i]} | {r['m']:.3f} | {r['q']:.3f} | {r['l']:.3f} | {r['e']:.1f} |")
    w(f"| 計 | {math.fsum(D['py']):.1f} | {sum(ds['all'])} | {sum(ds['ザガ'])} | | | | |")
    w("")
    sm = summary(T)

    def rg(c, k, nd=1, f=1):
        lo, hi = mid95(B[c][k])
        return f"{lo * f:.{nd}f}〜{hi * f:.{nd}f}"
    w(f"- 生まれたときの平均余命 e0: **{sm['e0']:.1f} 年** (95% の幅 {rg('all', 'e0')})。コードの決めごとだけで作った表では {cl['e0']:.1f} 年 (ザガと飢えは入らない)")
    w(f"- 15 歳の平均余命 e15: **{sm['e15']:.1f} 年** ({rg('all', 'e15')})。コード {cl['e15']:.1f} 年")
    w(f"- 1 歳までに亡くなる割合 q0: **{sm['q0']:.3f}** ({rg('all', 'q0', 3)})。コード {cl['q0']:.3f}")
    w(f"- 15 歳まで生きる割合 l15: **{sm['l15']:.3f}** ({rg('all', 'l15', 3)})。コード {cl['l15']:.3f}")
    parts = []
    for c, name in DROP:
        x = summary(D["tables"][c])
        n = sum(ds["all"]) - sum(ds[c])
        parts.append(f"{name}がなかったら ({n} 人を除く) e0 {x['e0']:.1f} 年 ({rg(c, 'e0')})・e15 {x['e15']:.1f} 年 ({rg(c, 'e15')})")
    w("- 死因を除いた表 (その死因で亡くなった人を、亡くならなかったとして数え直す。住んでいた年数はそのまま):")
    for x in parts:
        w(f"  - {x}")
    adult_d = sum(ds["all"][3:])
    w(f"- **人数が少ない**: 亡くなった人は {sum(ds['all'])} 人 (うち 15 歳から上は {adult_d} 人)。55 歳から上に住んだのは {D['old']} 人だけ "
      f"({D['py'][-1]:.1f} 年、亡くなった {ds['all'][-1]} 人) なので、55 歳からの行はほとんど当てにならない "
      "(ブートストラップで 55 歳から上の人が選ばれない・亡くならないときは、全体の死亡率を使った)。"
      "移って来た人と最初からいた人の生まれた日はおおよそ (born_day_exact = false) だが、コードもその年齢で死亡率を決めるので、中では食い違わない")
    w("")

    # ---- 2 ----
    exp, obs = D["exp"], D["obs"]
    w("## 2. 記録と決めごとの死亡率")
    w("")
    a = R["adult"]
    w(f"- コードの決めごと (era2._season_end の文から読んだ。季節の終わりごとの見込み): 0 歳 {R['child'][0][1]}、1〜4 歳 {R['child'][1][1]}、"
      f"5〜14 歳 {R['child'][2][1]} (ひどく飢えた子 (飢え {R['hungry'][0]} 以上) は {R['hungry'][1]})、15〜{a[2] - 1} 歳 {a[1]}・{a[2]}〜{R['old'][0] - 1} 歳 {a[3]} ({a[0]} から)、"
      f"{R['old'][0]} 歳から {R['old'][1]} × (1 + (年齢 − {R['old'][0]}) / {R['old'][2]})")
    w(f"- 見込みの数: 季節の終わりごとに、その日に村にいた人の 1 季節の見込みを足した (生まれたその季節の終わりは数えない。年齢は (日 − 生まれた日) ÷ {YEAR} の整数)。"
      "記録の死は、コードのこの部分が決める死 (子・病・年) だけ。")
    hungry = sum(1 for r in persons if s < r["season_end_day"] <= e and r.get("child") and (r.get("hunger") or 0) >= R["hungry"][0])
    w(f"- 季節の終わりにひどく飢えていた子は {hungry} 人・季節なので、飢えた子の見込みの引き上げは数に入れていない")
    w("")
    w("| 年齢 | 記録の死 (子・病・年) | コードからの見込み | 見込みの 95% の幅 (ポアソン) | 幅の中か |")
    w("|---|---:|---:|---:|---|")
    for i, (_, _, name) in enumerate(BANDS):
        lo, hi = pois95(exp[i])
        where = "幅の中" if lo <= obs[i] <= hi else ("幅より多い" if obs[i] > hi else "幅より少ない")
        w(f"| {name} | {obs[i]} | {exp[i]:.1f} | {lo}〜{hi} | {where} |")
    te = math.fsum(exp)
    lo, hi = pois95(te)
    w(f"| 計 | {sum(obs)} | {te:.1f} | {lo}〜{hi} | {'幅の中' if lo <= sum(obs) <= hi else '幅の外'} |")
    w("")
    oth = "・".join(f"{k} {n} 人" for k, n in sorted(D["other"].items()))
    w(f"- コードのこの部分の外の死: {oth or 'なし'} (world.py の決まり。era2 の見込みには入らない)")
    w(f"- これは確かめの報告で、試し (テスト) ではない。区分が {len(BANDS)} つあると、決めごとどおりでも、どれか 1 つが偶然 95% の幅から出る見込みは "
      f"{pc(1 - 0.95 ** len(BANDS))} ほどある。")
    w("")

    # ---- 3 ----
    F = fertility(people, D["spans"], T, s, e)
    pyt = math.fsum(D["py"])
    imm = [p for p in people if p["origin"] == "よそから来た" and s < p["came_day"] <= e]
    left = [p for p in people if p["left_day"] is not None and s < p["left_day"] <= e]
    dead = [p for p in people if p["died_day"] is not None]  # これまでに亡くなった人 (墓の割合とくらべる)
    baby = [p for p in dead if (p["died_day"] - p["born_day"]) // YEAR < 1]
    p0 = next(r["population"] for r in village if r["season_end_day"] == s)
    p1 = village[-1]["population"]
    gr = math.log(p1 / p0) / ((e - s) / YEAR)
    natural = (len(F["births"]) - sum(ds["all"])) / pyt
    w("## 3. 子の生まれ方")
    w("")
    w(f"- 期間は 1. と同じ。生まれた子 {len(F['births'])} 人 (女 {F['girls']} 人)。母の年齢は、子が生まれた日の整数の年齢 (コードと同じ数え方)"
      + (f"。母が分からない・区分の外 {F['nomom']} 人" if F["nomom"] else ""))
    w("")
    w("| 母の年齢 | 女の人が住んでいた年数 | 生まれた子 | 年齢ごとの出生率 (1 年) |")
    w("|---|---:|---:|---:|")
    for k, x in enumerate(FERT):
        w(f"| {x}〜{x + 4} 歳 | {F['wy'][k]:.1f} | {F['nb'][k]} | {F['asfr'][k]:.3f} |")
    w("")
    top = code_tfr(R)
    w(f"- 1 人の女の人が一生に生む子の数 (TFR): **{F['tfr']:.2f}** (人を選び直した 95% の幅 {F['tfr95'][0]:.2f}〜{F['tfr95'][1]:.2f})。"
      f"コードで生める上限は {top:.2f} "
      f"({R['mothers'][0]}〜{R['mothers'][1]} 歳、飢え {R['fed']} 未満、生んでから {YEAR} 日は生まない、生めるときは 1 季節 {R['birth']}。いつも飢えていないとしたとき)"
      + ("。記録が上限をこえているが、上限は幅の中なので、人数が少ないことによるばらつきで説明できる" if F["tfr"] > top and F["tfr95"][0] <= top else ""))
    w(f"- 娘の世代が何倍になるか (NRR): {F['nrr']:.2f} (生まれた子のうち女の割合 {F['f']:.3f} と、1. の表の生きる割合で)。"
      f"人口の増える速さ (ロトカの r): {pc(F['r'], 2)} / 年")
    w(f"- 1,000 人・年あたり ({pyt:.0f} 人・年): 生まれた {len(F['births']) / pyt * 1000:.0f}、亡くなった {sum(ds['all']) / pyt * 1000:.0f}、"
      f"よそから来た {len(imm) / pyt * 1000:.0f} ({len(imm)} 人)" + (f"、村を出た {len(left) / pyt * 1000:.0f} ({len(left)} 人)" if left else "。村を出た人はいない"))
    w(f"- 村の人数は {p0} 人 ({s} 日目) → {p1} 人 ({e} 日目)。1 年あたり {pc(gr, 1)}。このうち生まれた子と亡くなった人の差は 1 年 "
      f"{pc(natural, 1)}、残りはよそから来た人")
    w("- 文献とくらべるときの注意 (調べの批評に従う):")
    tfr_cmp = ("より高く" if F["tfr"] > 6.6 else "の幅の中" if F["tfr"] >= 5.6 else "より低く")
    w(f"  - TFR {F['tfr']:.2f} は、狩猟採集民 5.6〜5.7、農耕民 6.3〜6.6 という比べ (Demographic Research 49 巻 29 の引用。二次の引用で【未確認】) {tfr_cmp}"
      + ("、フッター派の約 9 (よく引かれる値。ここでは【未確認】) に近い" if abs(F["tfr"] - 9) <= 1 else "")
      + "。新石器時代の人口転換で「1 人あたり約 2 人増えた」(Bocquet-Appel 2011 の読み) は【未確認】")
    w("  - 長い目で見た新石器時代の人口の増え方は 1 年 0.041% (Zahid ほか 2016。確かめた)。"
      f"この村の増え方 (1 年 {pc(gr, 1)}) は" + ("それよりずっと速く" if gr > 10 * 0.00041 else "それに近く")
      + (f"、多くはよそから来た人による (生まれた子と亡くなった人の差は 1 年 {pc(natural, 1)} だけ)" if natural < gr / 2 else ""))
    e15, e0 = sm["e15"], sm["e0"]
    bone = ("骨からの値の幅の中にあり、民族誌の値よりずっと低い" if 20 <= e15 <= 25 else "骨からの値より高く、民族誌の値より低い" if 25 < e15 < 30
            else "民族誌の値に近い" if e15 >= 30 else "骨からの値よりも低い")
    w("  - 狩猟採集民の民族誌では、15 歳まで生きる割合 約 6 割・e15 30〜44 年 (Gurven & Kaplan 2007)。骨から推定した e15 は 20〜25 年ほど (era2 のコメントの目安。資料で差が大きい)。"
      f"どちらも抄録と引用で読んだだけで【未確認】。この村の e15 ({e15:.1f} 年) は{bone}。"
      + (f"e0 {e0:.1f} 年は Coale–Demeny のモデル生命表のいちばん低い段 (e0 20 年) の近く。" if e0 < 25 else "")
      + "テル・エル・ケルク (前 6400〜6100 年ごろの墓、258 人) では 1 歳になる前に亡くなった人が約 4 割 (抄録で確かめた。"
      f"墓の 258 人のうちの割合で、q0 とは比べられない。村は、これまでに亡くなった {len(dead)} 人のうち 1 歳になる前が {pc(len(baby) / len(dead))})")
    w("  - 骨からの値と民族誌からの値のどちらを「史実」とするかは本人が決めること。")
    w("")

    # ---- 4 ----
    acc = all(isinstance(r.get("accounts"), dict) for r in village)  # 村の会計の列 (accounts.py) があるか
    bal = all(isinstance(r.get("balance"), dict) for r in village)  # 貸借対照表の列があるか
    years = full_years(village)
    short = short_years(years, "G5") if acc else []
    u = village[-1]["store_days"]
    lowest = min((r for r in village if r.get("store_days") is not None and accounts.at_least(r["era"], "G4")), key=lambda r: r["store_days"])  # G4 から (G7 からも)
    c0, c1, c2 = R["come"]
    rt = field_ratio(state)
    chain = field_chain(state, village)
    wx = weather(village, rt, chain)

    def wcorr(sel, k):
        xs = [x for x in wx if sel(x)]
        return corr([x["ratio"] for x in xs], [x[k] for x in xs]), len(xs)
    w("## 4. 蓄えが尽きる見込み (ブートストラップ。見込みであって予想ではない)")
    w("")
    w(f"- 数え方: G5 と G6 のそれぞれで、続いた 2 つの季節の差を、時期のはじめから 4 つずつ (1 年分) のかたまりにし、かたまりを選び直して {HORIZON} 年並べた "
      f"({RUNS:,} 回)。村の蓄えが、どこかの季節の終わりに 0 日分以下になった割合")
    w("- 2 つの見方を分けて書く:")
    w("  - (a) **人数を固定した見込み**: 蓄えの kcal の差 ÷ その季節の 1 日分 (store_kcal ÷ store_days)。人数がこのままなら、の見込み")
    w("  - (b) **人数の増え方も入れた見込み**: 記録の store_days (今の人数で何日分か) の差。その時期の人の増え方も入る")
    w("")
    w(f"| 時期 | 見方 | 1 年のかたまり | 1 年の増え (日分、平均 ± ばらつき) | 減った年 | {HORIZON} 年で尽きる割合 ({u} 日分から) | ({LOW} 日分から) |")
    w("|---|---|---:|---:|---:|---:|---:|")
    rz = {}
    for k, era in enumerate(("G5", "G6")):
        rows, fa, fb = drifts(village, era)
        for j, (name, xs) in enumerate((("(a) 人数を固定", fa), ("(b) 人数の増え方も入れる", fb))):
            yrs = [math.fsum(xs[i:i + 4]) for i in range(0, len(xs) - 3, 4)]
            m, sdv = mean_sd(yrs)
            r1, nb = ruin(xs, u, (1, k, j, 1))
            r2, _ = ruin(xs, LOW, (1, k, j, 2))
            rz[(era, j)] = (m, sdv, r1, r2, yrs)
            w(f"| {era} ({dl(rows[0]['season_end_day'])} 〜 {rows[-1]['season_end_day']} 日目) | {name} | {nb} | {m:+.1f} ± {sdv:.1f} | "
              f"{sum(1 for y in yrs if y < 0)} | {pr(r1)} | {pr(r2)} |")
    w("")
    hh = [r for r in ledger if r["season_end_day"] == e and r["holder"] != "村" and r["kind"] == "残り" and r["reason"] == END and r["item"] in FOODS]
    nd = math.fsum(accounts.day_need(r) for r in persons if r["season_end_day"] == e and r.get("status_at_end") == "生きている")
    sda = village[-1].get("store_days_all")
    if sda is None and nd:
        sda = int(math.fsum([village[-1]["store_kcal"]] + [r["kcal"] for r in hh]) / nd)
    w(f"- 今の村の蓄えは {u} 日分。村の蓄えがいちばん少なかったのは G4 から後で {lowest['store_days']} 日分 ({dl(lowest['season_end_day'])})。"
      f"ここでは村の蓄えだけを見ている。家の倉 (だれもいなくなった家の倉もふくむ) を足すと 約 {sda} 日分")
    m5a, m5b = rz[("G5", 0)], rz[("G5", 1)]
    g5 = [r for r in village if r["era"] == "G5"]
    txt, share = fell(g5[0], g5[-1])
    # どの分け方でも同じ側なら「半分より多くは」と書く。分け方で入れかわるなら書かない
    why = ("" if share is None else "半分より多くは食べる人が増えたため" if share[2] < 0.5
           else "半分より多くは蓄えの kcal が減ったため" if share[1] > 0.5 else "")
    w(f"- 【読み】G5 の初めから終わりまで ({g5[0]['season_end_day']} → {g5[-1]['season_end_day']} 日目) では、"
      + (f"蓄えの日数が減ったのは、{why}: " if why else "") + f"{txt}。上の表 (季節ごとの増え減りの 1 年の平均。分け方がちがう) では、"
      f"kcal で見た増え減りは 1 年 {m5a[0]:+.1f} 日分、人数を入れると {m5b[0]:+.1f} 日分")
    if short:  # 純生産が必要な量に届かなかった年が多かったあいだ (7.)
        y0, y1 = min(short), max(short)
        met = [y for y in range(y0, y1 + 1) if y not in short]
        r0, r1 = years[y0][0], years[y1][0]
        txt, share = fell(r0, r1)
        w(f"  - ただし、純生産が必要な量に届かなかった年が多かった {y0}〜{y1} 年 (" + (f"{'・'.join(map(str, met))} 年のほかは届かなかった。" if met else "") + "7.) のうち、"
          f"{y0} 年の夏から {y1} 年の夏まで ({r0['season_end_day']} → {r1['season_end_day']} 日目) を見ると、"
          f"蓄えの kcal も {pc(1 - r1['store_kcal'] / r0['store_kcal'])} {'減った' if r1['store_kcal'] < r0['store_kcal'] else '増えた'}: {txt}")
    m6a, m6b = rz[("G6", 0)], rz[("G6", 1)]
    fa6, fb6 = sum(1 for y in m6a[4] if y < 0), sum(1 for y in m6b[4] if y < 0)
    w(f"- G6 は {len(m6a[4])} 年のかたまりのうち、減った年が (a) {fa6}・(b) {fb6}。選び直したとき {HORIZON} 年で尽きる割合は (a) {pr(m6a[2])}・(b) {pr(m6b[2])} ({u} 日分から)"
      + (f"。減った年が 1 つもないので、選び直しても減る年は出てこない (0% は「この {len(m6a[4])} 年に減った年がなかった」ということで、起きないという意味ではない)"
         if fa6 == fb6 == 0 else ""))
    g6r = [rt[y] for y, rs in sorted(years.items()) if all(r["era"] == "G6" for r in rs) and y in rt]
    g5r = min(((rt[y], y) for y, rs in years.items() if all(r["era"] == "G5" for r in rs) and y in rt), default=None)
    if g6r:
        low = f"、G5 でいちばん低かった {g5r[1]} 年の {g5r[0]} 倍ほどの年はなかった" if g5r and g5r[0] < min(g6r) else ""
        ca, na_ = wcorr(lambda x: True, "days")
        w(f"  - G6 の {len(g6r)} 年の畑の実りの倍率は {min(g6r)}〜{max(g6r)} 倍で{low}。倍率と、夏に村の蓄えが何日分増えたかの相関は、"
          f"記録のある {na_} 年で {cr(ca)} (8.8。年の範囲で値が動く)。この {len(g6r)} 年からは、まれな大きな不作は見えない")
    w(f"- **予想ではない**: よそから人が来る見込みは 1 季節 {c0} + min({c1}, 蓄えの日数 ÷ {c2:.0f}) (era2._season_end) で、蓄えの日数そのものに左右される。"
      "人の数も決まりも時期ごとに変わり続けている。村の蓄えが尽きることは、飢えることと同じではない (家の倉・木の実・乳がある)")
    w("")

    # ---- 5 ----
    L = loans(state, ledger, village, e)
    rows = L["rows"]
    op = L["opened"]
    lenders = {}
    for r in rows:
        lenders[r["lender"]] = lenders.get(r["lender"], 0) + 1
    who = ("貸したのはみな村" if set(lenders) == {"村"} else "貸した側は " + "・".join(f"{k} {n} 回" for k, n in sorted(lenders.items())))
    lent_rows = [r for r in rows if r["kind"] == accounts.LENT]
    short_rows = [r for r in rows if r["kind"] == accounts.SHORT]
    odd = [r for r in rows if r["kind"] not in (accounts.LENT, accounts.SHORT)]
    w("## 5. 貸しの帳簿")
    w("")
    w(f"- 量はみな草の種のつかみ (交換の値うち VALUE で数えた。{'・'.join(f'{k} {v}' for k, v in era2.VALUE.items())})。"
      f"{who}で、利子はない (G6 の決めごと)。貸しは {len(rows)} 回だけなので、割合を一般の値として使わない。"
      "記録の道具が使えるようになった日 (g6.open): " + "、".join(f"{t} {op[t][0]} 日目" for t in LEVELS if t in op)
      + (f"、{'・'.join(t for t in LEVELS if t not in op)} はまだ" if any(t not in op for t in LEVELS) else ""))
    w(f"- 2 つの種類を分けた: 季節の集まりで決めて貸した「{accounts.LENT}」{len(lent_rows)} 回 (期限 1 年) と、交換に行った先で向こうが払いきれず、あとで返すと言った"
      f"「{accounts.SHORT}」{len(short_rows)} 回 (期限 2 季節。出来事「交換」の文の [D..] で見分ける)" + (f"。どちらでもない {len(odd)} 回 ({'・'.join(r['id'] for r in odd)})" if odd else ""))
    w("")

    def loan_table(rs):
        w("| 貸し | 相手 | 貸した日 (通しの日) | 貸した量 | 貸した日に使えた記録 | 残した記録 | 期限 | 返った | 返らなかった | まだ | 期限をすぎた日数 | 村の覚え | 覚え ÷ 本当 |")
        w("|---|---|---|---:|---|---|---:|---:|---:|---:|---:|---:|---:|")
        for r in rs:
            w(f"| {r['id']} | {L['names'].get(r['other'], r['other'])} | {r['day']} | {n0(r['lent'])} | {r['level']} | {r['proof'] or 'なし'} | {r['due']} | "
              f"{n0(r['ret'])} | {n0(r['lost'])} | {n0(r['open'])} | {r['late'] or '-'} | {n0(r['mem'])} | {r['mem'] / r['lent']:.2f} |")
        w(f"| 計 | | | {n0(fs(rs, lambda r: r['lent']))} | | | | {n0(fs(rs, lambda r: r['ret']))} | {n0(fs(rs, lambda r: r['lost']))} | "
          f"{n0(fs(rs, lambda r: r['open']))} | | | |")
    w(f"「{accounts.LENT}」(集まりで決めて貸した):")
    w("")
    if lent_rows:
        loan_table(lent_rows)
    else:
        w("- なし")
    w("")
    w(f"「{accounts.SHORT}」(交換に行った先で、向こうが払いきれなかった分): " + ("" if short_rows else f"なし (交換に行ったのは {len(L['trips'])} 回)"))
    if short_rows:
        w("")
        loan_table(short_rows)
    w("")
    lent = fs(rows, lambda r: r["lent"])
    lost = fs(rows, lambda r: r["lost"])
    still = fs(rows, lambda r: r["open"])
    closed = [r for r in rows if r["status"] != "まだ"]
    cl_lent = fs(closed, lambda r: r["lent"])
    cl_ret = fs(closed, lambda r: r["ret"])
    w(f"- 返し終わった {len(closed)} 回: 貸した {n0(cl_lent)} のうち返った {n0(cl_ret)}、返らなかった {n0(lost)} "
      f"(返し終わった分の {pc(lost / cl_lent if cl_lent else 0)}、貸した全部の {pc(lost / lent if lent else 0)})。"
      f"まだ返っていない {n0(still)}" + "".join(f"。{r['id']} は期限を {r['late']} 日すぎた" for r in rows if r["late"]))
    mem_ev = [r for r in closed if r["mem_from"] == "覚え"]
    w(f"- 村の覚え: 返し終わった分のうち {len(mem_ev)} 回は、出来事「覚え」の文の物と数を VALUE で数えた量"
      + (f" (計 {n0(fs(mem_ev, lambda r: r['mem']))}、本当の {fs(mem_ev, lambda r: r['mem']) / fs(mem_ev, lambda r: r['lent']):.2f} 倍)" if mem_ev else "")
      + "。そのほかは、貸したときの覚えの倍率 (debts の mem.village) を掛けて切り上げた量 (まだの分は、お題の「まだ返されていない貸し借り」に出る量)。"
      f"覚えのずれはコードの【仮定】({era2.SPREAD} × (大人のいる家の数 + まだ返されていない貸し借りの数)、{era2.SPREAD_MAX} まで。era2._g6_spread) で、史実から決めた値ではない")
    late = [r for r in closed if r["level"] in LEVELS[1:]]  # 数え札から後に貸した
    early = [r for r in closed if r not in late]
    av = fs(late, lambda r: r["lost"])
    w("- 記録があれば避けられたかもしれない損 (多くて): " + ("、".join(f"{r['id']} {n0(r['lost'])} ({r['level']})" for r in late) or "なし")
      + f" = **{n0(av)} つかみ** ({n0(av * era2.GRAIN)} kcal、大人の {av * era2.GRAIN / era2.DAY_FOOD:.0f} 日分の食べ物)。"
      + ("".join(f"{r['id']} は数え札より前に貸したので、どの記録でも避けられなかった ({n0(r['lost'])})。" for r in early)))
    w(f"  - コードでは、封筒か板の記録がないと、相手は覚えで 貸した量 × {1 - era2.SPREAD_MAX:g}〜1 倍 (覚えのずれが {era2.SPREAD_MAX} のとき) を持って来る。"
      "数え札の記録があれば、足りない分が新しい借りになるだけ (あとで返れば損が消える)。封筒か板の記録があれば決めた量を持って来るが、相手の蓄えまで。"
      "だからこれは上限で、記録だけの効き目ではない (相手の蓄えにも左右される)。記録の手間とのくらべは 8.6")
    gain = fs(L["trades"], lambda t: t["gain"])
    tgain = fs(L["trips"], lambda t: t["gain"])
    calc = still + lost - gain - tgain
    w(f"- よその村との出し入れのつり合い: 村と家からよその村へ出した物の値うちの差し引きは {n0(L['net'])} "
      f"({'、'.join(f'{k} {n0(n)} (値うち {n0(era2.VALUE[k] * n)})' for k, n in L['items'].items() if n)}。帳簿 ledger.jsonl の「ほかの村へ出した・入った」でも {n0(L['lg_net'])})。"
      f"これは、まだ返っていない貸し {n0(still)} + 返らなかった分 {n0(lost)} − 交換で得した分 {n0(gain)}"
      + (f" − 交換に行って得した分 (足りない分を除く) {n0(tgain)}" if L["trips"] else "")
      + f" = {n0(calc)} と" + (" ぴったり合う。" if abs(L["net"] - calc) < 0.5 else f" {n0(L['net'] - calc)} ずれる。"))
    gains = [t for t in L["trades"] if t["gain"]]
    if L["trades"]:
        kinds = {}
        for t in gains:
            k = (gw(t["gave"]), accounts.handfuls(t["gave"]), gw(t["got"]), accounts.handfuls(t["got"]))
            kinds.setdefault(k, []).append(t["offer"])
        w(f"  - 季節の集まりの交換 {len(L['trades'])} 回のうち、値うちの差があったのは {len(gains)} 回"
          + ("" if not gains else " (" + "、".join(f"{'・'.join(o)}: {g_} (値うち {n0(gv)}) を出して {r_} (値うち {n0(rv)}) を受けとった。差 {rv - gv:+,.0f}"
                                                   for (g_, gv, r_, rv), o in kinds.items()) + ")")
          + "。差は相手の申し出の作り方による (値段ではない)")
    if L["trips"]:
        w(f"  - 交換に行った {len(L['trips'])} 回: 得した分 (足りない分の貸しは、この節の帳簿で数えるので除いた) " + "、".join(f"{t['trip']} {t['gain']:+,.0f}" for t in L["trips"]))
    shrink = closed and all(r["mem"] > r["lent"] for r in closed) and all(r["ret"] < r["lent"] for r in closed)
    if shrink:
        w(f"- 【読み】返し終わった {len(closed)} 回はどれも、村は貸した量より多く覚えていて、相手は貸した量より少なく返した。記録のない借りは、覚えのずれで減っていく。"
          "後の時代の、利子で増えていく借り (Hudson の言う帳消しの問題) とは向きが逆")
    w("")

    # ---- 6 ----
    last8 = village[-8:]
    have = all(isinstance(r.get("binding"), dict) for r in last8)
    cap = era2.pasture_cap(state)
    w("## 6. 限りの表 (どの限りが効いているか。最後の 8 季節)")
    w("")
    w("- 経済の道具の 1 つ「制約つき最適化」の読み方 (カルーシュ・キューン・タッカー条件の相補性: 余りのある限りは効いていない) で、記録を点検する。最適化の計算はしない")
    w("- 記録の列 season_village.binding を読んだ (build_records が作った【シ】の列)" if have else
      "- 記録の列 season_village.binding がまだないので、accounts.py の同じ数え方で数えた (帳簿の家の倉と季節の人の行から)")
    w(f"- 草: 飼っているヤギと、草で養える数 K (era2.pasture_cap = {cap} 頭。{accounts.PASTURE_FROM} 日目の季節から。コードを変えた日で、村の中の出来事ではない)。"
      f"土器: 土器に入る草の種 (土器 × {era2.POT_HOLD} つかみ) と、守る草の種 (村の蓄え + 家の倉。だれもいなくなった家の倉もふくむ)。"
      "鎌: 鎌の数と、刈った大人。働く日: 大人の日のうち休んだ日 (夕方の仕事は日数にない)")
    w("")
    w("| 季節の終わり | ヤギ / K | 草の種 / 土器に入る量 | 虫やネズミ | 鎌 / 刈った大人 | 休んだ日 (けが) / 大人の日 | 届いている限り |")
    w("|---|---:|---:|---:|---:|---:|---|")
    hits = {"草": 0, "土器": 0, "鎌": 0}
    rest = [0, 0]
    for v in last8:
        D_ = v["season_end_day"]
        b = v["binding"] if have else accounts.binding(v, [r for r in persons if r["season_end_day"] == D_], [r for r in ledger if r["season_end_day"] == D_],
                                                         cap if D_ >= accounts.PASTURE_FROM else None)
        pa, po, si, la = (b.get(k) or {} for k in ("pasture", "pots", "sickles", "labour"))
        hit = [n for k, n in (("pasture", "草"), ("pots", "土器"), ("sickles", "鎌")) if (b.get(k) or {}).get("at_limit")]
        for n in hit:
            hits[n] += 1
        rest[0] += la.get("rest_days") or 0
        rest[1] += la.get("adult_days") or 0
        w(f"| {dl(D_)} | {pa.get('goats')} / {pa.get('K') or '-'} | {n0(po.get('grain') or 0)} / {n0(po.get('hold') or 0)} | {n0(v.get('pests') or 0)} | "
          f"{si.get('sickles')} / {si.get('harvesters')} | {la.get('rest_days')} ({la.get('injured_days')}) / {n0(la.get('adult_days') or 0)} | {'・'.join(hit) or 'なし'} |")
    w("")
    pests = [r["season_end_day"] for r in village if (r.get("pests") or 0) > 0]
    lim = ([r["season_end_day"] for r in village if (r["binding"].get("pots") or {}).get("at_limit")]
           if all(isinstance(r.get("binding"), dict) for r in village) else None)  # 列 binding で土器の限りに届いた季節
    w(f"- 虫やネズミの害が出た季節: {runs_ja(pests, SD, ' 日目')}"
      + ("".join((f"。列 binding では、割れたあとの土器で見るので、{'・'.join(map(str, x))} 日目も限りに届いている (虫の害は 0)" if k else
                  f"。列 binding では、{'・'.join(map(str, x))} 日目は限りに届いていない (虫のあとに草の種が出ていった)")
                 for k, x in ((1, [d for d in lim if d not in pests]), (0, [d for d in pests if d not in lim])) if x) if lim is not None else ""))
    w("- 働く日には「届いている限り」の印をつけない (列でも at_limit は null)。休んだ日が 0 なのは、大人が毎日なにかの仕事を選ぶ形だからで、限りに届いた印にならない "
      "(夕方の仕事は日数にない。線形計画でも働く日の影の値段は 0。docs/research/economic_lenses.md 5.5)")
    # 冬と春の採集の 1 日あたりの得 (最後の 8 季節。帳簿の「採った」÷ 採集の日)
    low_sea = []
    for v in last8:
        if v["season"] in ("冬", "春"):
            gd = sum(r["days_by_activity"].get(GATHER, 0) for r in persons if r["season_end_day"] == v["season_end_day"])
            got = math.fsum(r["kcal"] for r in ledger if r["season_end_day"] == v["season_end_day"] and r["reason"] == "採った")
            if gd:
                low_sea.append((v["season_end_day"], got / gd, gd))
    nlast = len(last8)
    on = [n for n, c in hits.items() if c]
    off = [n for n, c in hits.items() if not c]
    w(f"- 【読み】最後の {nlast} 季節で限りに届いていたのは" + ("・".join(f"{n} ({hits[n]} 季節)" for n in on) if on else "どれもなし")
      + (f"。{'と'.join(off)}は余っている" if off else "")
      + f"。休んだ日は大人の日の {pc(rest[0] / rest[1] if rest[1] else 0, 1)}"
      + (f"。冬と春の採集は 1 日あたり {n0(min(x for _, x, _ in low_sea))}〜{n0(max(x for _, x, _ in low_sea))} kcal (大人の 1 日分 {n0(era2.DAY_FOOD)} kcal より"
         f"{'少ない' if max(x for _, x, _ in low_sea) < era2.DAY_FOOD else '多いこともある'}。{'・'.join(str(d) for d, _, _ in low_sea)} 日目の季節)" if low_sea else "")
      + ("。得の小さい日も多いので、「働く日が足りない」とは言えない" if low_sea and max(x for _, x, _ in low_sea) < era2.DAY_FOOD else ""))
    w("")

    # ---- 7 ----
    w("## 7. 村の会計 (記録の列 accounts・sectors・grain_fate・store_days_all)")
    w("")
    alive = {r["household_id"] for r in persons if r["season_end_day"] == e and r.get("status_at_end") == "生きている"}
    sda_live = int(math.fsum([village[-1]["store_kcal"]] + [r["kcal"] for r in hh if r["holder"] in alive]) / nd) if nd else None
    ev_, cut = {}, {}  # 季節ごとの、夕方に木から取った・刈った kcal (帳簿から)
    for r in ledger:
        if r["reason"] == "木から取った" or r["reason"] in CUT:
            (ev_ if r["reason"] == "木から取った" else cut).setdefault(r["season_end_day"], []).append(r["kcal"])

    def by(d, rs):
        return math.fsum(x for r in rs for x in d.get(r["season_end_day"], []))

    def sa(rs, k):
        return fs(rs, lambda r: r["accounts"][k])
    if not acc:
        w("- 記録の列 season_village.accounts がまだない (build_records.py で records を作り直すと入る)")
    else:
        idt = [r["accounts"]["identity"] for r in village]
        gaps = [abs(x["gap"]) for x in idt if x["gap"] is not None]
        res = [(x["residual"], r["season_end_day"]) for x, r in zip(idt, village)]
        big = max(res, key=lambda x: abs(x[0]))
        w("- 列は sim/society/accounts.py が、帳簿 (ledger.jsonl) と季節の行から作る (build_records.py)。単位は kcal (草の種 1 つかみ = 80 kcal)。"
          f"ヤギ (1 頭 {n0(era2.GOAT_WORTH)} kcal) と土器・鎌 (交換の値うち VALUE。G6 から) は、食べ物と分けて数えた。夕方の仕事は働いた日に数えない (世界の決まり)")
        w(f"- 恒等式 (純生産 = 食べた・祭り + 残りの増え (住まいをふくむ) + よその村へ出した差 + 持って出た分 − 記録にない差): {len(gaps)} 季節すべてで、"
          f"ずれはいちばん大きくて {max(gaps):.2f} kcal (丸めの分)。帳簿は記録にない差の行で毎季節閉じているので、これは新しい列の数え方 (符号と値うち) の確かめで、"
          f"村についての発見ではない。記録にない差は合わせて {n0(math.fsum(x for x, _ in res))} kcal、いちばん大きいのは {big[1]} 日目の {n0(big[0])} kcal")
        w("")
        w("| 時期 | 季節 | 食べ物を作った | 種 | 損 | 純生産 | 食べた・祭り | 必要な量 | 純生産 ÷ 必要な量 | 食べた・祭り ÷ 必要な量 | うち夕方に木から取った | うち刈った |")
        w("|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|")
        for name, rs in [(x, [r for r in village if r["era"] == x]) for x in era2.ORDER2] + [("計", village)]:
            if rs:
                g, need_, net = sa(rs, "food_gross"), sa(rs, "need"), sa(rs, "food_net")
                use = sa(rs, "eaten") + sa(rs, "feast")
                w(f"| {name} | {len(rs)} | {mk(g)} | {mk(sa(rs, 'seed'))} | {mk(sa(rs, 'food_loss'))} | {mk(net)} | {mk(use)} | {mk(need_)} | "
                  f"{net / need_:.2f} | {use / need_:.2f} | {pc(by(ev_, rs) / g)} | {pc(by(cut, rs) / g)} |")
        w("")
        w("- 量は百万 kcal。作った = 採った・木から取った・狩った・乳をしぼった・刈った・ヤギをつぶした (肉)。種 = まいた・埋めた。損 = 腐った・虫やネズミ・雨で傷んだ・干して減った分。"
          "必要な量 = いた日数 × 1 日分 (大人 2,400 kcal、子は年齢で。store_days と同じ決まり)")
        ratio = {y: (fs(rs, lambda r: r["accounts"]["food_net"]), fs(rs, lambda r: r["accounts"]["eaten"] + r["accounts"]["feast"]), sa(rs, "need"))
                 for y, rs in years.items()}
        eat = [u_ / n_ for _, u_, n_ in ratio.values()]
        w(f"- 年ごと (夏から春の 4 季節がそろった {len(years)} 年): 食べた・祭り ÷ 必要な量は {min(eat):.2f}〜{max(eat):.2f}"
          + (" で、ほぼ一定" if max(eat) - min(eat) <= 0.15 else ""))
        lows = [(x, short_years(years, x)) for x in era2.ORDER2]
        w("- 純生産が必要な量に届かなかった年 (1 つの時期だけの年): " + ("、".join(
            f"{x} の {runs_ja(ys, 1, ' 年')} (純生産 ÷ 必要な量 {min(ratio[y][0] / ratio[y][2] for y in ys):.2f}〜{max(ratio[y][0] / ratio[y][2] for y in ys):.2f})"
            for x, ys in lows if ys) or "なし"))
        g6y = [rs for rs in years.values() if all(r["era"] == "G6" for r in rs)]
        hs = [by(cut, rs) / sa(rs, "food_gross") for rs in g6y]
        if hs:
            w(f"- 刈り入れが作った食べ物に占める割合は、G6 の年ごとに {pc(min(hs))}〜{pc(max(hs))} ({len(hs)} 年)。これまで全部では {pc(by(cut, village) / sa(village, 'food_gross'))}")
        g6 = [r for r in village if r["era"] == "G6"]
        pre = [r for r in g6 if r["season_end_day"] < accounts.PASTURE_FROM]
        post = [r for r in village if r["season_end_day"] >= accounts.PASTURE_FROM]

        def heads(rs, k):
            return fs(rs, lambda r: r["accounts"]["goats"][k]) / era2.GOAT_WORTH
        w(f"- ヤギ (食べ物とは分けた。増えた = 生まれた・捕まえた、減った = いなくなった・つぶした。よその村との出し入れは入れない): G6 の {accounts.PASTURE_FROM} 日目の季節より前は "
          f"{n0(heads(pre, 'gained'))} 頭増えて {n0(heads(pre, 'lost'))} 頭減った。{accounts.PASTURE_FROM} 日目の季節から後は {n0(heads(post, 'gained'))} 頭増えて "
          f"{n0(heads(post, 'lost'))} 頭減った。{accounts.PASTURE_FROM} 日目は草の上限が効いた最初の季節で、コードを変えた日 (村の中の出来事ではない)。前と後は分けて読む")
        w(f"- 土器と鎌 (G6、VALUE で草の種のつかみ): 作った {n0(fs(g6, lambda r: r['accounts']['goods']['made']) / era2.GRAIN)}、"
          f"割れた {n0(fs(g6, lambda r: r['accounts']['goods']['broken']) / era2.GRAIN)}。"
          f"住まい (G6、建てた日数 × 2,400 kcal): 建てた日 {n0(sa(g6, 'homes') / era2.DAY_FOOD)} 日")
        gf = village[-1]["grain_fate"]
        made, st = gf["produced"], gf["stored"]
        w(f"- 草の種の行方 (はじめからの合計、つかみ): 作った {n0(made)} のうち、"
          + "・".join(f"{n} {pc(gf[k] / made, 1)}" for k, n in (("eaten", "食べた"), ("sown", "まいた"), ("pests", "虫やネズミ"), ("feast", "祭り"),
                                                              ("exported", "よその村へ出した"), ("rotted", "腐った"), ("other", "そのほか")))
          + f"。**まだ倉にあるのは {n0(st['village'] + st['households'])} ({pc((st['village'] + st['households']) / made, 1)})**: 村 {n0(st['village'])}、"
          f"家の倉 {n0(st['households'])} (うち、だれもいなくなった家の倉 {n0(st['orphaned'])})。記録のはじめの残り {n0(gf['start'])} と、よその村から入った {n0(gf['imported'])} を足すとつり合う")
        w(f"- 蓄えの日数 ({e} 日目): 村の蓄えだけ {u} 日分 (store_days)。家の倉を足すと {sda_live} 日分、だれもいなくなった家の倉も足すと {sda} 日分 (store_days_all)。"
          "割る 1 日分は、季節の終わりに生きている人の 1 日分の合計 (store_days と同じ決まり)")
        w("")
        w(f"部門の表 (G6 の {len(g6)} 季節の合計、万 kcal。入るは +。sectors の列): どの行も足すと 0。村と家の列の合計は、残りの増え (住まいは入れない)")
        w("")
        w("| 行 | 村 (村の蓄え + 大人の手元) | 家 (家の倉と家のヤギ。だれもいない家の倉も) | よその村 | 自然・暮らし |")
        w("|---|---:|---:|---:|---:|")
        for k, name in ROWS_JA:
            w(f"| {name} | " + " | ".join(mk(fs(g6, lambda r: r["sectors"]["rows"][k][sec]), 1e4) for sec in accounts.SECTORS) + " |")
        w(f"| 残りの増え | {mk(fs(g6, lambda r: r['sectors']['stock_change']['村']), 1e4)} | {mk(fs(g6, lambda r: r['sectors']['stock_change']['家']), 1e4)} | | |")
        w("")
        tk = {k: fs(g6, lambda r: r["sectors"]["transfers_by_kind"][k]) for k in accounts.TRANSFER_KINDS}
        nx = fs(g6, lambda r: r["sectors"]["rows"]["external"]["よその村"])  # よその村に入った分 = 村と家が出した差し引き
        w("- 移ったもの (G6、出した側で数えた、万 kcal): " + "、".join(f"{k} {mk(x, 1e4)}" for k, x in tk.items()))
        w(f"- よその村へ出した差し引き: {n0(nx)} kcal = {n0(nx / era2.GRAIN)} つかみ。5. のよその村との出し入れ ({n0(L['net'])} つかみ) と"
          + ("合う" if abs(nx / era2.GRAIN - L["net"]) < 0.5 else f"{n0(nx / era2.GRAIN - L['net'])} つかみずれる"))
        moves = math.fsum([tk["家にだれもいない"], tk["家の倉から食べた"], tk["罰・つぐない"], nx])
        made6 = fs(g6, lambda r: r["sectors"]["rows"]["production"]["村"] + r["sectors"]["rows"]["production"]["家"])
        use_era = eat_ratio(village)
        flat = flat_eat(use_era)
        w("- 【読み】" + (f"食べた量は、どの時期も必要な量とほぼ同じ (時期ごとに {min(use_era):.2f}〜{max(use_era):.2f} 倍) で、作った量の多い少ないは、ほとんどが蓄えの増え減りになった。"
                         "だから 1 人あたりの生産は、暮らしのよさの数にならない。" if flat else
                         f"食べた量 ÷ 必要な量は、時期ごとに {min(use_era):.2f}〜{max(use_era):.2f} 倍。")
          + f"部門のあいだの動き (家→村・家どうし・よその村へ) は、G6 で作った量の {pc(moves / made6, 1)}"
          + (" だけ。お金のない村なので、MMT の言う「部門ごとの差し引き」はほとんど 0 で、意味があるのは、部門ごとにためた量 (残りの増え)" if moves / made6 < 0.05 else ""))
    w("")

    # ---- 8 ----
    kkt(w, village, hhs, persons, ledger, state, L, years, chain, wx, rt, acc, bal, e)

    # ---- 9 ----
    w("## 9. 前の調べ (2026-10-14) の数とのちがい")
    w("")
    if e != 4829:
        w(f"- 前の調べは 4829 日目までの記録。この表は {e} 日目までなので、くらべない")
    else:
        compare(w, people, village, ledger, persons, state, R, D, F, T, cl, rz, rg, s, e, u, sda_live, sda, hh, alive)
    return "\n".join(out) + "\n"


# ---------------- 8. 会計・経済・投資理論 (文) ----------------

def kkt(w, village, hhs, persons, ledger, state, L, years, chain, wx, rt, acc, bal, e):
    """8. 会計・経済・投資理論 (日本アクチュアリー会の 1 次試験の科目。略して KKT) の見方。記録から測れるものだけ"""
    G, DF = era2.GRAIN, era2.DAY_FOOD
    rows = L["rows"]
    closed = [r for r in rows if r["status"] != "まだ"]
    w("## 8. 会計・経済・投資理論 (アクチュアリー試験の「KKT」)")
    w("")
    w("- **名前のこと**: 本人の言う KKT は、日本アクチュアリー会の資格試験 (1 次試験) の科目「会計・経済・投資理論」のこと (略して KKT と呼ばれる)。"
      "2026-10-14 の調べ (docs/research/economic_lenses.md の 5.) は、これを数学の「KKT 条件」(カルーシュ・キューン・タッカー条件。限りのある中でいちばんよいやり方を探す"
      "「制約つき最適化」の決まり) と取りちがえて調べた。KKT 条件は、経済の中の道具の 1 つにすぎない。6. の限りの表の読み方にだけ使い、この節では使わない")
    w("- この節では、試験の 3 つの分野 (会計・経済・投資理論) の見方で、記録から測れるものだけを測る。村の人はこの見方を知らない (【シ】)。お題とダッシュボードには出さない")
    w(f"- **仮定に左右される数** (【仮定】と書いた): 値うちのものさし (草の種 1 つかみ = {G} kcal、ヤギ 1 頭 = {n0(era2.GOAT_WORTH)} kcal (GOAT_WORTH)、"
      f"土器 {era2.VALUE['土器']}・鎌 {era2.VALUE['鎌']} つかみ (交換の値うち VALUE。G6 から))、人の 1 日の働きを大人の 1 日分の食べ物 ({n0(DF)} kcal = {DF // G} つかみ) で数えること "
      f"(住まい・土器・記録の手間)、返らない見込みの割合 (返し終わった {len(closed)} 回から)、土器が守った草の種 (季節の終わりの量から、おおよそ)。"
      "記録の数 (何つかみ・何頭・何日) そのものは仮定によらない")
    w("")

    # ---- 8.1 貸借対照表 ----
    w("### 8.1 会計: 村と家の貸借対照表")
    w("")
    w("- 貸借対照表: ある日に持っている物 (資産) と借り (負債) を並べ、その差 (純資産 = 資産 − 負債) を出す表。記録の列 season_village.balance (accounts.py) を読んだ。単位は万 kcal")
    if not bal:
        w("- 記録の列 season_village.balance がまだない (build_records.py で records を作り直すと入る)")
        w("")
    else:
        b = village[-1]["balance"]
        V, H, T_ = b["村"], b["家"], b["total"]
        pop = village[-1]["population"]
        w("")
        w(f"{dl(e)} の季節の終わり:")
        w("")
        w("| | 村 | 家 (みな合わせて) | 計 |")
        w("|---|---:|---:|---:|")
        w(f"| 食べ物 (村の蓄え・家の倉) | {mk(V['food']['kcal'], 1e4)} | {mk(H['food']['kcal'], 1e4)} | {mk(math.fsum([V['food']['kcal'], H['food']['kcal']]), 1e4)} |")
        w(f"| 大人の手元の食べ物 | {mk(V['hands_kcal'], 1e4)} | - | {mk(V['hands_kcal'], 1e4)} |")
        w(f"| ヤギ | {V['goats']['count']} 頭 {mk(V['goats']['kcal'], 1e4)} | {H['goats']['count']} 頭 {mk(H['goats']['kcal'], 1e4)} | "
          f"{mk(math.fsum([V['goats']['kcal'], H['goats']['kcal']]), 1e4)} |")
        for key, item, unit in (("pots", "土器", "個"), ("sickles", "鎌", "本")):
            x = V[key]
            w(f"| {item} | {x['count']:,} {unit} {mk(x['kcal'], 1e4)} | - | {mk(x['kcal'], 1e4)} |")
        hd = H["dwellings"]
        w(f"| 住まい | {V['dwellings']['count']} (値うちは分からない) | {hd['count']} 軒" + (f" + 建てかけ {hd['building']}" if hd["building"] else "")
          + f" {mk(hd['kcal'], 1e4)} | {mk(hd['kcal'], 1e4)} |")
        w(f"| よその村への貸し | {n0(V['loans']['handfuls'])} つかみ {mk(V['loans']['kcal'], 1e4)} | {n0(H['loans']['handfuls'])} つかみ {mk(H['loans']['kcal'], 1e4)} | "
          f"{mk(math.fsum([V['loans']['kcal'], H['loans']['kcal']]), 1e4)} |")
        w(f"| **資産の計** | **{mk(V['assets'], 1e4)}** | **{mk(H['assets'], 1e4)}** | **{mk(T_['assets'], 1e4)}** |")
        w(f"| 負債 (借り) | {mk(V['liabilities'], 1e4)} | {mk(H['liabilities'], 1e4)} | {mk(T_['liabilities'], 1e4)} |")
        w(f"| **純資産** | **{mk(V['equity'], 1e4)}** | **{mk(H['equity'], 1e4)}** | **{mk(T_['equity'], 1e4)}** |")
        w("")
        nonzero = [r["season_end_day"] for r in village if r["balance"]["村"]["liabilities"] or r["balance"]["家"]["liabilities"]]
        w(f"- 1 人あたり ({pop} 人): 資産 {mk(T_['assets'] / pop, 1e4)} 万 kcal = 大人の {T_['assets'] / pop / DF:,.0f} 日分の食べ物。"
          f"そのうち食べ物 (村の蓄え・手元・家の倉) は {pc(math.fsum([V['food']['kcal'], V['hands_kcal'], H['food']['kcal']]) / T_['assets'])}")
        w("- 負債 (借り): " + (f"{len(village)} 季節すべてで、村も家も 0。" if not nonzero else f"0 でない季節がある ({'・'.join(map(str, nonzero))} 日目)。")
          + "コードに借りる道がない (よその村とは貸すだけ。罰・つぐないはその場で払うか、払えなければ消える。配給の記録 (g6 の credit) は払う約束ではない)。"
          "だから純資産 = 資産で、この表で見えるのは「何をどれだけ持っているか」だけ")
        vg, hg_ = V["food"]["by_item"] or {}, H["food"]["by_item"] or {}
        gsh = grain_share(village[-1])
        w(f"- 村の食べ物のうち草の種は {n0(vg.get('草の種', 0))} つかみ ({pc(vg.get('草の種', 0) * G / V['food']['kcal'] if V['food']['kcal'] else 0)})。"
          f"家の倉は草の種が {n0(hg_.get('草の種', 0))} つかみ ({pc(hg_.get('草の種', 0) * G / H['food']['kcal'] if H['food']['kcal'] else 0)})"
          + (f"。村の蓄えと家の倉を合わせると、食べ物の kcal の {pc(gsh)} が草の種" if gsh is not None else "")
          + ("で、食べられる物がほとんど草の種の形でためられている" if gsh is not None and gsh >= GRAIN_MOST else ""))
        hts = H["top"]
        w(f"- 家: 人のいる家 {H['living']}、そのうち持ち物 (住まいをふくむ) のある家 {H['with_assets']}、倉かヤギのある家 {H['with_stores']}。"
          f"人のいない家に残った持ち物 {H['orphaned']['households']} 軒分 {mk(H['orphaned']['kcal'], 1e4)} 万 kcal (家の倉と住まい。だれも使えない)。"
          + (f"持ち物がいちばん多い家は {hts['household']} (家の合計の {pc(hts['share'], 1)})" if hts["household"] else ""))
        ln = V["loans"]["open"]
        if ln:
            w("- よその村への貸しの残り: " + "、".join(f"{o['id']} ({o['kind']}) {L['names'].get(o['other'], o['other'])} {n0(o['handfuls'])} つかみ"
                                                   + (f" (期限を {o['overdue_days']} 日すぎた)" if o["overdue_days"] else " (期限の前)") for o in ln)
              + "。返らないかもしれない分の見込みは 8.3")
        w("")
        # いくつかの時点
        last = {}
        for r in village:
            last[r["era"]] = r
        pts = {r["season_end_day"]: r for r in last.values()}
        i409 = next((k for k, r in enumerate(village) if r["season_end_day"] >= accounts.PASTURE_FROM), None)
        if i409:
            for r in village[i409 - 1:i409 + 1]:
                pts[r["season_end_day"]] = r
        w("いくつかの時点 (時期の最後の季節と、草の上限の前と後。万 kcal):")
        w("")
        w("| 季節の終わり | 時期 | 人 | 村の資産 | うち食べ物 (手元も) | うちヤギ (頭) | うち土器・鎌 | うち貸し | 家の資産 | うち家の倉 | うち住まい | 計 | 1 人あたり (大人の日分) |")
        w("|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|")
        for D_, r in sorted(pts.items()):
            bb = r["balance"]
            v_, h_ = bb["村"], bb["家"]
            gs = [v_["pots"]["kcal"], v_["sickles"]["kcal"]]
            w(f"| {dl(D_)} | {r['era']}{'→' + r['era_end'] if r.get('era_end') and r['era_end'] != r['era'] else ''} | {r['population']} | {mk(v_['assets'], 1e4)} | "
              f"{mk(math.fsum([v_['food']['kcal'], v_['hands_kcal'] or 0.0]), 1e4)} | {mk(v_['goats']['kcal'], 1e4)} ({v_['goats']['count']}) | "
              f"{'-' if None in gs else mk(math.fsum(gs), 1e4)} | {mk(v_['loans']['kcal'], 1e4)} | {mk(h_['assets'], 1e4)} | {mk(h_['food']['kcal'], 1e4)} | "
              f"{mk(h_['dwellings']['kcal'], 1e4)} | {mk(bb['total']['assets'], 1e4)} | {bb['total']['assets'] / r['population'] / DF:,.0f} |")
        w("")
        pv = [r for r in village if r["balance"]["村"]["pots"]["kcal"] is not None]
        first_v = pv[0]["season_end_day"] if pv else None
        hfirst = min((r["season_end_day"] for r in ledger if r["holder"] != "村"), default=None)  # 帳簿に家の行が出た最初の季節
        hhome = next((r["season_end_day"] for r in village if r["balance"]["家"]["dwellings"]["kcal"]), None)
        notes = []
        if first_v:
            fg = next((r["season_end_day"] for r in village if (r.get("accounts") or {}).get("goods") is not None), None) if acc else None
            notes.append(f"土器・鎌の値うち (VALUE) は G6 の季節の終わり ({first_v} 日目) から。それより前は「-」で資産に入れないので、{first_v} 日目で村の資産がとぶ"
                         + (f"。7. の土器と鎌の作った・割れた (列 accounts の goods) は、季節そのものの時期で決めるので {fg} 日目の季節から。"
                            f"{first_v} 日目のとびに見合う出し入れは 7. にない" if fg and fg != first_v else ""))
        if hfirst:
            notes.append(f"帳簿に家の倉の行が出るのは {hfirst} 日目の季節から。" + (f"それより前の家の資産は、建てた住まいの手間だけ ({hhome} 日目から)" if hhome and hhome < hfirst
                                                                                 else "それより前の家の資産は 0"))
        if i409:
            a_, b_ = village[i409 - 1]["balance"]["村"]["goats"], village[i409]["balance"]["村"]["goats"]
            notes.append(f"ヤギは {accounts.PASTURE_FROM} 日目の季節から草の上限 (コードの変更) が効いた。{village[i409 - 1]['season_end_day']} → {village[i409]['season_end_day']} 日目で "
                         f"村のヤギは {a_['count']} → {b_['count']} 頭、{village[-1]['season_end_day']} 日目は {village[-1]['balance']['村']['goats']['count']} 頭。"
                         "ヤギの値うちが大きく動くのはこのため (前と後は分けて読む)")
        hg = [(D_, r["balance"]["家"]["goats"]["count"]) for D_, r in sorted(pts.items()) if r["balance"]["家"]["goats"]["count"]]
        if hg:
            notes.append("家の資産には家のヤギもふくむ (表の列にはない): " + "、".join(f"{D_} 日目 {n} 頭" for D_, n in hg))
        notes.append("住まいは建てた手間 (住まいを建てる日数 × 2,400 kcal【仮定】) で数え、減らしていない。村の住まい (キャンプのまん中) は記録のはじまりより前にできたので、値うちは分からない")
        for x in notes:
            w(f"- {x}")
        w("- 歴史: 「はじめの残り + 入り − 出 = 終わりの残り」でつり合う帳簿 (今の言葉で単式の帳簿) は、メソポタミアの粘土板にある。G6 の終わり (ウルク IV 期、前 3300〜3200 年ごろ) "
          "のころに配給・家畜の帳簿が始まり、つり合いをはっきり書く帳簿はウル第三王朝 (前 2100 年ごろ。Englund 1991)。貸しと借りを 2 つの欄に同時に書く複式簿記は中世イタリア "
          "(13〜15 世紀。パチョーリ 1494 が本にした。一般知識)、貸借対照表などの財務諸表は近代の道具。ここでは外から見る人の物差しとしてだけ使う")
        w("")

    # ---- 8.2 減価償却 ----
    w("### 8.2 会計: 減価償却の見方 (土器と鎌の傷み)")
    w("")
    w("- 減価償却: 長く使う道具の値うちが、使ううちに減っていく分を、期間ごとの費用として分けて数えること。ここでは土器と鎌 (いつも村のもの) が割れる割合から、平均の寿命を読む")
    if bal:
        obs = (state["era2"].get("g6") or {}).get("obs_sickles", 0)
        w(f"- コードでは、季節の終わりに 1 つずつ、土器は {era2.POT_BREAK:.0%}・鎌は {era2.SICKLE_BREAK:.0%} の見込みで割れる (era2._storage_season。"
          f"季節の終わりの数に掛けるので、たくさん作った季節は「割れた ÷ はじめの数」が少し高く出る)。黒曜石の刃の鎌は割れる見込みが {era2.OBS_BREAK} 倍だが、今は {obs} 本")
        w("")
        w("| 道具 | 時期 | 季節 | はじめの数 (季節ごとの計) | 作った | 割れた | 割れた ÷ はじめの数 | 割れた ÷ (はじめ + 作った) | 平均の寿命 (1 ÷ 割合) |")
        w("|---|---|---:|---:|---:|---:|---:|---:|---:|")
        for key, item, rate in (("pots", "土器", era2.POT_BREAK), ("sickles", "鎌", era2.SICKLE_BREAK)):
            for era in era2.ORDER2:
                x = wear_sum(village, key, (era,))
                if not x["seasons"]:
                    continue
                life = f"{1 / x['rate']:.1f} 季節 ({1 / x['rate'] / (YEAR // SD):.1f} 年)" if x["rate"] else "-"
                w(f"| {item} | {era} | {x['seasons']} | {x['start']:,} | {x['made']:,} | {x['broken']:,} | {pc(x['rate'], 2) if x['rate'] is not None else '-'} | "
                  f"{pc(x['rate2'], 2) if x['rate2'] is not None else '-'} | {life} |")
            w(f"| {item} | コードの決まり | | | | | {rate:.0%} | | {1 / rate:.1f} 季節 ({1 / rate / (YEAR // SD):.1f} 年) |")
        w("")
        g6v = [r for r in village if r["era"] == "G6"]  # 7. と同じ G6 の季節
        dep = {k: sum((r["balance"]["wear"].get(k) or {}).get("broken", 0) for r in g6v) for k in ("pots", "sickles")}
        mad = {k: sum((r["balance"]["wear"].get(k) or {}).get("made", 0) for r in g6v) for k in ("pots", "sickles")}
        val = {"pots": accounts.GOODS["土器"], "sickles": accounts.GOODS["鎌"]}
        if g6v:
            V = village[-1]["balance"]["村"]
            w(f"- 値うちで見ると (G6 の {len(g6v)} 季節、VALUE で【仮定】): 割れた分 (減価償却費に当たる) は 土器 {dep['pots']:,} 個 {mk(dep['pots'] * val['pots'], 1e4)} 万 kcal・"
              f"鎌 {dep['sickles']:,} 本 {mk(dep['sickles'] * val['sickles'], 1e4)} 万 kcal。作った分は 土器 {mad['pots']:,} 個 {mk(mad['pots'] * val['pots'], 1e4)} 万 kcal・"
              f"鎌 {mad['sickles']:,} 本 {mk(mad['sickles'] * val['sickles'], 1e4)} 万 kcal。今の帳簿の値うちは 土器 {mk(V['pots']['kcal'], 1e4)}・鎌 {mk(V['sickles']['kcal'], 1e4)} 万 kcal")
        w("- 読み方: 残っている数の決まった割合が毎季節へる形は、会計の「定率法」(残りの値うちに決まった率を掛けて減らす) に近く、毎年同じ額を減らす「定額法」ではない。"
          "1 つ 1 つの寿命は乱数でばらばらで、平均が 1 ÷ 割合になる")
    w("")

    # ---- 8.3 貸倒引当金 ----
    w("### 8.3 会計: 貸倒引当金の見方 (返らないかもしれない貸し)")
    w("")
    w("- 貸倒引当金: 貸したもののうち返らないと見込む分を、先に損として数えておくこと。ここでは「まだの貸し × 返し終わった貸しで返らなかった割合」で見積もる")
    opn = [r for r in rows if r["status"] == "まだ"]
    still = fs(opn, lambda r: r["open"])
    cl_lent, cl_lost = fs(closed, lambda r: r["lent"]), fs(closed, lambda r: r["lost"])
    if not opn:
        w("- まだ返っていない貸しはない")
    elif not closed:
        w("- 返し終わった貸しがまだないので、割合が出せない")
    else:
        rate_all = cl_lost / cl_lent
        per = {r["id"]: r["lost"] / r["lent"] for r in closed}
        lv = {}
        for r in closed:
            lv.setdefault(r["level"], []).append(r)
        guess, how = [], []
        for r in opn:
            base = lv.get(r["level"])
            rr = fs(base, lambda x: x["lost"]) / fs(base, lambda x: x["lent"]) if base else rate_all
            guess.append(r["open"] * rr)
            how.append(f"{r['id']} {n0(r['open'])} × {pc(rr, 1)} ({r['level']}。" + (f"{'・'.join(x['id'] for x in base)} から" if base else "同じ記録の貸しがないので全部の割合") + ")")
        s_ = L["spread"]
        each = "・".join(f"{r['id']} {pc(per[r['id']], 1)}" for r in closed)
        w(f"- 返し終わった貸しは {len(closed)} 回だけ ({each})。どの見積もりも、おおまかな目安 (【仮定】)")
        w("")
        w("| 見積もり方 | 返らなかった割合 | まだの貸し (つかみ) | 返らないと見込む量 (つかみ) | kcal |")
        w("|---|---:|---:|---:|---:|")
        w(f"| 返し終わった {len(closed)} 回ぜんぶの割合 ({n0(cl_lost)} ÷ {n0(cl_lent)}) | {pc(rate_all, 1)} | {n0(still)} | {n0(still * rate_all)} | {n0(still * rate_all * G)} |")
        w(f"| 貸した日に使えた記録ごとの割合 | {pc(math.fsum(guess) / still, 1)} | {n0(still)} | {n0(math.fsum(guess))} | {n0(math.fsum(guess) * G)} |")
        lo_, hi_ = min(per.values()), max(per.values())
        w(f"| 1 回ずつの割合の幅 (いちばん低い〜高い) | {pc(lo_, 1)}〜{pc(hi_, 1)} | {n0(still)} | {n0(still * lo_)}〜{n0(still * hi_)} | {n0(still * lo_ * G)}〜{n0(still * hi_ * G)} |")
        w(f"| コードの決まり (覚えのずれ {s_:g} の半分。下の注) | {pc(s_ / 2, 1)} | {n0(still)} | {n0(still * s_ / 2)} | {n0(still * s_ / 2 * G)} |")
        w("")
        w("- 記録ごとの割合の内わけ: " + "、".join(how))
        w(f"- コードの決まりとのくらべ: 封筒か板の記録がないと、相手は 貸した量 × (1 − 覚えのずれ)〜1 倍 を持って来るので、持って来たときの損は平均で覚えのずれの半分 "
          f"(今のずれ {s_:g}。era2._g6_spread)。ただし期限から 1 年たっても返さなければ「返されない」で全部が損になる"
          + "".join(f"。{r['id']} は期限を {r['late']} 日すぎた" for r in opn if r["late"]))
        w(f"- 記録を残した貸しは {sum(1 for r in rows if r['proof'])} 回。「貸した日に使えた記録」は使えたというだけで、残したのではない")
    w("")

    # ---- 8.4 蓄えに回した割合 ----
    w("### 8.4 経済: 蓄えに回した割合")
    w("")
    w("- 貯蓄率: 作った分 (純生産) のうち、使わずに残した (蓄えが増えた) 分の割合。食べ物だけ (食べ物の残りの増え ÷ 食べ物の純生産) と、"
      f"ヤギも入れた割合 ((食べ物の残りの増え + ヤギの頭数の増え × {n0(era2.GOAT_WORTH)}) ÷ (食べ物の純生産 + ヤギの増減 × {n0(era2.GOAT_WORTH)})) の 2 つ。"
      "残りは帳簿の季節のはじめと終わりの残り (村の蓄え・大人の手元・家の倉。だれもいなくなった家の倉も)。ヤギの頭数の増えには、よその村から受けとったヤギも入る。"
      "ヤギの増減は生まれた・捕まえた − いなくなった・つぶした (7.)")
    if not acc:
        w("- 記録の列 season_village.accounts がまだない")
        w("")
    else:
        stock = food_stock(ledger)
        w("")
        w("| 時期 | 季節 | 食べ物の純生産 (百万 kcal) | 食べ物の残りの増え | 蓄えに回した割合 (食べ物) | その時期だけの年の幅 | 割合が負の年 | ヤギも入れた割合 |")
        w("|---|---:|---:|---:|---:|---:|---:|---:|")
        for era in era2.ORDER2:
            rs = [r for r in village if r["era"] == era]
            if not rs:
                continue
            x = saving(rs, stock)
            ys = [saving(v, stock) for y, v in sorted(years.items()) if all(r["era"] == era for r in v)]
            ys = [y_["food"] for y_ in ys if y_["food"] is not None]
            w(f"| {era} | {len(rs)} | {mk(x['food_net'])} | {mk(x['d_food'])} | {pc(x['food'], 1)} | "
              f"{'-' if not ys else pc(ys[0], 1) if len(ys) == 1 else pc(min(ys), 1) + '〜' + pc(max(ys), 1)} ({len(ys)} 年) | {sum(1 for y_ in ys if y_ < 0)} | "
              f"{pc(x['with_goats'], 1) if x['with_goats'] is not None else '-'} |")
        x = saving(village, stock)
        w(f"| 計 | {len(village)} | {mk(x['food_net'])} | {mk(x['d_food'])} | {pc(x['food'], 1)} | | | {pc(x['with_goats'], 1)} |")
        w("")
        g6y = [(y, v) for y, v in sorted(years.items()) if all(r["era"] == "G6" for r in v)]
        if g6y:
            brk = next((y for y, v in g6y if any(r["season_end_day"] == accounts.PASTURE_FROM for r in v)), None)
            brk_label = next((r["label"] for r in village if r["season_end_day"] == accounts.PASTURE_FROM), None)  # 草の上限が効いた最初の季節の名前 (36年の冬)
            w("- G6 の年ごと (食べ物だけ / ヤギも入れて): " + "、".join(
                f"{y} 年 {pc(saving(v, stock)['food'])} / {pc(saving(v, stock)['with_goats'])}" for y, v in g6y)
              + (f"。{brk_label} ({accounts.PASTURE_FROM} 日目の季節) から草の上限 (コードの変更) でヤギが大きく減ったので、ヤギを入れた割合は {brk} 年で区切って読む" if brk else ""))
        neg = [y for y, v in sorted(years.items()) if (saving(v, stock)["food"] or 0) < 0]
        ue = eat_ratio(village)
        gsh = grain_share(village[-1]) if bal else None
        rd = [f"食べ物を蓄えから取りくずした (割合が負の) 年は {runs_ja(neg, 1, ' 年')}" if neg else "割合が負の年はない"]
        rd.append("7. のとおり食べた量は必要な量とほぼ同じなので、作った量の増え減りが、ほとんどそのまま蓄えに回した割合の増え減りになる" if flat_eat(ue) else
                  f"食べた量 ÷ 必要な量は時期ごとに {min(ue):.2f}〜{max(ue):.2f} 倍で、どの時期も必要な量とほぼ同じ ({FLAT[0]:g}〜{FLAT[1]:g} 倍) とは言えない (7.)。"
                  "だから蓄えに回した割合の増え減りは、作った量の増え減りだけでは決まらない")
        if gsh is not None and gsh >= GRAIN_MOST:
            rd.append(f"{dl(e)} の蓄え (村の蓄えと家の倉) は、食べ物の kcal の {pc(gsh)} が草の種で、土器の中では減らない (docs/society_phase/fidelity_checklist.md の 2.)")
        w("- 【読み】" + "。".join(rd))
        w("")

    # ---- 8.5 みんなの倉 ----
    w("### 8.5 経済: みんなの倉に入れた・取った")
    w("")
    by, cum, fseas = flows(hhs, village)
    memo = {}
    for r in ledger:
        if r["kind"] == "メモ" and r["reason"].startswith("村の蓄え"):
            memo.setdefault((r["season_end_day"], r["holder"]), {})["in" if "入れた" in r["reason"] else "out"] = r["amount"]
    vf = {(h["season_end_day"], h["household_id"]): h["village_flow"] for h in hhs if h.get("village_flow")}
    diff = sum(1 for k, m in memo.items() if k in vf and (m.get("in") != vf[k]["in"] or m.get("out") != vf[k]["out"]))
    only_vf = [k for k in vf if k not in memo]
    first = {}
    for D_, h_ in sorted(vf):
        first.setdefault(h_, D_)
    newh = all(first[h_] == D_ for D_, h_ in only_vf)  # 列にだけある行が、みな家ができた最初の季節か
    w("- みんなの倉: 村の蓄えに、家の大人が入れた量と取った量 (season_household.village_flow。草の種にしたつかみ。取った量には、倉を持つ家が自分の畑にまいた村の草の種もふくむ)。"
      "子の分は数えない (子は村の蓄えで育つ決まり)。"
      f"G5 から ({fseas[0] if fseas else '-'} 日目)。帳簿のメモの行「村の蓄えに入れた・取った」と、{len(memo)} 行のうち {len(memo) - diff} 行が同じ数"
      + (f"。列にだけある {len(only_vf)} 行は" + ("、みな家ができた最初の季節 (帳簿には、その季節にその家の行がない)" if newh else "、帳簿にない") if only_vf else ""))
    w("- 「倉のある家」は、その季節に家の倉を持っていた家 (season_household.keep)。大人 1 人・季節あたりは、(入れた − 取った) ÷ その家の大人の数 (季節の終わり) の計")
    w("")
    w("| 年 | 季節 | 入れた | 取った | 差し引き (入れた − 取った) | 倉のある家 (大人 1 人・季節あたり) | 倉のない家 (大人 1 人・季節あたり) |")
    w("|---|---:|---:|---:|---:|---:|---:|")
    for y, x in sorted(by.items()):
        i_, o_ = sum(x["in"]), sum(x["out"])
        k_, n_ = x["keep"], x["none"]
        w(f"| {y} | {len(x['seasons'])} | {n0(i_)} | {n0(o_)} | {i_ - o_:+,} | {(k_[0] - k_[1]) / k_[2] if k_[2] else 0:+,.0f} ({k_[2]}) | "
          f"{(n_[0] - n_[1]) / n_[2] if n_[2] else 0:+,.0f} ({n_[2]}) |")
    w("")
    if cum:
        tot_i, tot_o = sum(c[0] for c in cum.values()), sum(c[1] for c in cum.values())
        keep_ = [sum(x["keep"][j] for x in by.values()) for j in range(3)]
        none_ = [sum(x["none"][j] for x in by.values()) for j in range(3)]
        takers = sorted((h for h, c in cum.items() if c[0] < c[1]), key=lambda h: (cum[h][0] - cum[h][1], h))
        givers = sorted(cum, key=lambda h: (-(cum[h][0] - cum[h][1]), h))
        endst = {}
        for r in ledger:
            if r["season_end_day"] == e and r["holder"] != "村" and r["kind"] == "残り" and r["reason"] == END and accounts.part(r["item"]) == "food":
                endst[r["holder"]] = endst.get(r["holder"], 0.0) + r["kcal"]
        rank = sorted((h for h in endst if endst[h] > 0), key=lambda h: (-endst[h], h))

        def where(h):
            return (f"{e} 日目の家の倉は {rank.index(h) + 1} 番目に多い ({mk(endst[h], 1e4)} 万 kcal。倉に食べ物のある {len(rank)} 家 (人のいない家もふくむ) のうち)"
                    if h in rank else f"{e} 日目に家の倉の食べ物はない")
        w(f"- ぜんぶで ({len(fseas)} 季節): 入れた {n0(tot_i)}、取った {n0(tot_o)}、差し引き {tot_i - tot_o:+,} つかみ。大人 1 人・季節あたり、倉のある家 "
          f"{(keep_[0] - keep_[1]) / keep_[2] if keep_[2] else 0:+,.0f}・倉のない家 {(none_[0] - none_[1]) / none_[2] if none_[2] else 0:+,.0f} つかみ")
        w(f"- 家ごとの、はじめからの差し引き: {len(cum)} 家のうち、取ったほうが多い家は {len(takers)}"
          + (f"。いちばん多く取ったのは {takers[0]} ({cum[takers[0]][0] - cum[takers[0]][1]:+,} つかみ、{cum[takers[0]][2]} 季節。{where(takers[0])})" if takers else "")
          + f"。いちばん多く入れたのは {givers[0]} ({cum[givers[0]][0] - cum[givers[0]][1]:+,} つかみ、{cum[givers[0]][2]} 季節。{where(givers[0])})")
        if len(takers) > 1:
            w("- 取ったほうが多い家 (差し引き・記録のある季節の数): " + "、".join(f"{h} {cum[h][0] - cum[h][1]:+,} ({cum[h][2]} 季節)" for h in takers))
        neg = [y for y, x in sorted(by.items()) if sum(x["in"]) < sum(x["out"])]
        rd = [("どの年も、入れた量が取った量より多い" if not neg else f"取った量が入れた量より多かった年は {runs_ja(neg, 1, ' 年')}だけ"),
              "コードでは、大人はその日に食べる分を手元に残し、余りを村の蓄えに入れ、足りなければ蓄えから取る (era2._feed)"]
        if tot_i > 2 * tot_o:
            rd.append(f"ぜんぶで入れた量は取った量の {tot_i / tot_o:.1f} 倍で、みんなの倉は「みんなで分けた」より「みんなで余りをためた」形に近い")
        if none_[2] and keep_[2] and (none_[0] - none_[1]) / none_[2] > (keep_[0] - keep_[1]) / keep_[2]:
            rd.append("倉のない家のほうが、大人 1 人あたり多く入れた (倉のある家の畑で刈った草の種は、その家の倉に入る決まり。era2._harvest)")
        w("- 【読み】" + "。".join(rd))
    w("")

    # ---- 8.6 記録の手間 ----
    w("### 8.6 経済: 記録の手間と、記録がなくて失った量")
    w("")
    kd = sum(r["days_by_activity"].get(KEEP, 0) for r in persons)
    tok = L["opened"].get("数え札")
    after = [r for r in rows if r["level"] in LEVELS[1:]]
    before = [r for r in rows if r not in after]
    w("- 取引の費用: 約束を守らせるための手間 (記録をつける) は、約束が守られずに失う量より小さいか。数え札が使えるようになった日 "
      f"({tok[0] if tok else '-'} 日目) から後の貸しだけをくらべる ({'・'.join(r['id'] for r in before) or 'なし'} はその前で、どの記録も使えなかった)")
    w(f"- 主な仕事「記録をつける」を選んだ大人の日は、これまで {kd} 日。記録を残した貸しは {sum(1 for r in rows if r['proof'])} 回")
    if after:
        sea, need = record_cost(rows, village, ledger)
        w(f"- 数え方 (era2._g6_records と同じ): 貸しを記録する季節に、よその村と動いた物を物ごとに足し、数え札 1 個の量 (草の種 {era2.TOKEN['草の種']} つかみ・ヤギ {era2.TOKEN['ヤギ']} 頭・"
          f"土器と鎌 {era2.TOKEN['土器']} 個) で割って切り上げ、その季節の新しい貸しの数を足す。記録をつける人は 1 日に {era2.RATE['数え札']} 個 (数え札・封筒)。"
          "その季節の交換を全部残さないと、記録にならない。1 日の手間は大人の 1 日分の食べ物で数えた (【仮定】。G6 の採集の 1 日の得はそれより少ない)")
        w("")
        w("| 貸し | 記録する季節 | その季節によその村と動いた物 | 要る数え札 | 記録をつける日 (少なくとも) | 手間 (つかみ) | 返らなかった (返し終わった) / 見込む損 (まだ、8.3 の全部の割合) |")
        w("|---|---|---|---:|---:|---:|---:|")
        rate_all = fs(closed, lambda r: r["lost"]) / fs(closed, lambda r: r["lent"]) if closed else None
        tot = {"days": 0, "cost": 0.0, "loss": 0.0, "days_c": 0, "cost_c": 0.0, "loss_c": 0.0}
        seen = set()
        for r in after:
            D_ = sea[r["id"]]
            x = need.get(D_)
            if not x:
                continue
            days = math.ceil(x["tokens"] / era2.RATE["数え札"])
            share = D_ in seen  # 同じ季節の貸しは、手間をいっしょに数える
            seen.add(D_)
            cost = 0 if share else days * DF / G
            loss = r["lost"] if r["status"] != "まだ" else (r["open"] * rate_all if rate_all is not None else 0.0)
            tag = "c" if r["status"] != "まだ" else "o"
            tot["days"] += 0 if share else days
            tot["cost"] += cost
            tot["loss"] += loss
            if tag == "c":
                tot["days_c"] += 0 if share else days
                tot["cost_c"] += cost
                tot["loss_c"] += loss
            w(f"| {r['id']} | {dl(D_)} | {gw(x['moved'])} | {x['tokens']} | {days}{' (同じ季節)' if share else ''} | {n0(days * DF / G)} | "
              f"{n0(loss)}{'' if r['status'] != 'まだ' else ' (見込み)'} |")
        w("")
        if tot["days_c"]:
            w(f"- 返し終わった貸し: 記録の手間は 記録をつける人の {tot['days_c']} 日 = {n0(tot['cost_c'])} つかみ分。記録がなくて失ったのは多くて {n0(tot['loss_c'])} つかみ "
              f"(手間の {tot['loss_c'] / tot['cost_c']:.1f} 倍)。ただし数え札だけの記録では、相手は覚えで持って来て、足りない分が新しい借りになるだけ (5.)。"
              "失った量のどこまでが記録で防げたかは、相手の蓄えにも左右される")
        w(f"- まだの貸しもふくめると: 手間 {tot['days']} 日 = {n0(tot['cost'])} つかみ分、失った量と見込む損 {n0(tot['loss'])} つかみ")
        lost_all = fs(closed, lambda r: r["lost"]) * G
        st_k = village[-1]["store_kcal"]
        if tot["days_c"] and tot["loss_c"] > tot["cost_c"]:
            w(f"- 【読み】記録の手間は、記録がなくて失った量より小さい (返し終わった貸しで {tot['loss_c'] / tot['cost_c']:.1f} 倍)。"
              + ("それでも記録をつける仕事を選んだ大人はまだいない (お題の選び方の記述で、失敗とは言えない。" if not kd else "(")
              + f"返らなかった分はぜんぶで {n0(lost_all)} kcal で、{e} 日目の村の蓄えの {pc(lost_all / st_k, 2) if st_k else '-'})")
    w("")

    # ---- 8.7 投資の戻り ----
    w("### 8.7 投資理論: 投資の戻り (種・土器・住まい)")
    w("")
    w("- 投資の戻り: 今がまんして出したもの (種・働いた日) が、あとでどれだけになって返ったか。利子もお金もないので、物と日数のままくらべる")
    tt = chain["tot"]
    lo, hi, mode = chain["tri"]
    if tt["seed"]:
        w(f"- **種 → 実り** (state の era2.fields。刈り終わった畑 {chain['fields']} 枚、{len(chain['years'])} 年分、まいた {n0(tt['seed'])} つかみ): まいた 1 つかみから")
        w(f"  - **{chain['mean']:.2f}**: 設定の平均 (era2._field_season の三角分布。いちばん少なくて {lo:g} 倍、多くて {hi:g} 倍、いちばん多いのは {mode:g} 倍。"
          "【文献】の目安 (1:5〜1:15) をもとにした【仮定】)")
        w(f"  - → **{tt['ratio'] / tt['seed']:.2f}**: 実際に引かれた年の倍率を、その年にまいた量で重みをつけて平均 ({len(chain['years'])} 年)")
        w(f"  - → **{tt['weed'] / tt['seed']:.2f}**: 草取りが足りない分を引いた (実りは min(1, {chain['weed'][0]:g} + {chain['weed'][1]:g} × 草取りの時間 ÷ 要る時間) 倍、"
          f"要る時間 = まいた量 × {chain['need'][0]:g} + {chain['need'][1]:g})")
        w(f"  - → {tt['yield'] / tt['seed']:.2f}: ヤギに荒らされた分と、整数への切り捨て (実った量。差 {tt['weed'] / tt['seed'] - tt['yield'] / tt['seed']:.3f})")
        w(f"  - → **{tt['cut'] / tt['seed']:.2f}**: 実ったのに刈らずに落ちた分を引いた (実った量の {pc(1 - tt['cut'] / tt['yield'], 1)})")
        sown = -math.fsum(r["amount"] for r in ledger if r["reason"] == "まいた (畑)")
        reap = math.fsum(r["amount"] for r in ledger if r["reason"] in CUT)
        lr = f"{reap / sown:.2f}" if sown else "-"
        w(f"  - 刈った量 ÷ まいた量 {tt['cut'] / tt['seed']:.2f} は、人の働き方 (草取りと刈り入れ) の結果で、天気の設定ではない。史実の目安とくらべられるのは設定 ({chain['mean']:.2f}) だけ。"
          f"帳簿の「刈った」÷「まいた (畑)」の合計 ({n0(reap)} ÷ {n0(sown)}) は {lr}"
          + (" で同じ" if lr == f"{tt['cut'] / tt['seed']:.2f}" else " (まだ実っていない畑の種をふくむので、少しちがう)")
          + (f"。ここに入らなかった畑 {chain['skipped']} 枚" if chain["skipped"] else ""))
        w("")
        w("| 時期 (実った年の夏) | 年 | まいた | 倍率 (重みつき) | 草取りのあと | 実った | 刈った | 刈った ÷ まいた (年ごとの幅) |")
        w("|---|---:|---:|---:|---:|---:|---:|---|")
        for era in era2.ORDER2:
            ys = {y: b for y, b in chain["years"].items() if b["era"] == era}
            if not ys:
                continue
            S_ = math.fsum(b["seed"] for b in ys.values())
            rr = [b["cut"] / b["seed"] for b in ys.values() if b["seed"]]
            w(f"| {era} | {len(ys)} | {n0(S_)} | {math.fsum(b['ratio'] for b in ys.values()) / S_:.2f} | {math.fsum(b['weed'] for b in ys.values()) / S_:.2f} | "
              f"{math.fsum(b['yield'] for b in ys.values()) / S_:.2f} | {math.fsum(b['cut'] for b in ys.values()) / S_:.2f} | {min(rr):.2f}〜{max(rr):.2f} |")
        w("")
    P = pots_return(village, persons)
    if P:
        made = sum(x["made"] for x in P.values())
        days = sum(x["days"] for x in P.values())
        per_pot = days / made if made else None
        mg = era2.POT_HOLD * era2.PEST_LOSS
        life = 1 / era2.POT_BREAK
        w(f"- **土器**: 1 個を作る手間は、{POT_WORK}の {n0(days)} 日で {n0(made)} 個 = 1 個 {per_pot:.2f} 日 = {per_pot * DF / G:.1f} つかみ分 (【仮定】1 日 = {DF // G} つかみ)。"
          f"交換の値うちは {era2.VALUE['土器']} つかみ (G6)")
        w(f"  - 土器 1 個は草の種 {era2.POT_HOLD} つかみを入れ、入らない草の種は 1 季節に {era2.PEST_LOSS:.0%} が虫やネズミに食べられる。"
          f"だから土器がもう 1 個あると、草の種が土器より多い季節だけ、1 季節に {mg:g} つかみを守る (足りている季節は 0)")
        w("")
        w("| 時期 | 季節 | 作った | 土器づくりの日 | 土器の数 (季節ごとの計) | 守った草の種 (おおよそ) | 土器 1 個・1 季節あたり | 土器が足りなかった季節 |")
        w("|---|---:|---:|---:|---:|---:|---:|---:|")
        for era in era2.ORDER2:
            x = P.get(era)
            if not x:
                continue
            sv = math.fsum(x["saved"])
            w(f"| {era} | {x['seasons']} | {x['made']:,} | {x['days']:,} | {x['pot_seasons']:,} | {n0(sv)} | "
              f"{sv / x['pot_seasons'] if x['pot_seasons'] else 0:.1f} | {x['limit']} |")
        w("")
        last8 = village[-8:]
        lim8 = sum(1 for v in last8 if ((v.get("binding") or {}).get("pots") or {}).get("at_limit"))
        w(f"  - 守った草の種 = 季節ごとに min (草の種, 土器 × {era2.POT_HOLD}) × {era2.PEST_LOSS:.0%} (季節の終わりの量から。おおよそ)。"
          f"寿命 (コード 1 ÷ {era2.POT_BREAK:.0%} = {life:.0f} 季節) のあいだずっと土器が足りなければ、1 個で {mg * life:,.0f} つかみを守り、作る手間 {per_pot * DF / G:.1f} つかみ分の "
          f"{mg * life / (per_pot * DF / G):,.0f} 倍になる。最後の 8 季節のうち土器が足りなかったのは {lim8} 季節で、"
          + ("今はもう 1 個の得はほとんど 0 (土器は余っている。6.)" if lim8 <= 1 else "まだ土器を足す得がある"))
    hd = [r["balance"]["家"]["dwellings"] for r in village[-1:]] if bal else []
    if hd:
        hd = hd[0]
        nh = hd["count"] + hd["building"]
        rn = [r for r in village if (r.get("rain_outside_person_nights") or 0) > 0]
        w(f"- **住まい** (家族の住まい): 建てた手間は {n0(hd['kcal'] / DF)} 日 = {mk(hd['kcal'], 1e4)} 万 kcal (【仮定】1 日 = {n0(DF)} kcal。減らしていない)。"
          f"できた {hd['count']} 軒" + (f" と建てかけ {hd['building']} 軒" if hd["building"] else "") + f"で、1 軒あたり {hd['kcal'] / DF / nh:.0f} 日 (広げた分もふくむ)。"
          "住まいの戻り (屋根の下で眠る・家の倉を置く) は食べ物では測れない"
          + (f"。参考: 雨の夜に外で寝た のべの夜は、{rn[-1]['season_end_day']} 日目の季節のあと 0 (そのときの住まい {rn[-1]['homes_built']} 軒。住まいだけのおかげかは、この記録では分からない)"
             if rn and rn[-1]["season_end_day"] < e else ""))
    w("")

    # ---- 8.8 天気と蓄え ----
    w("### 8.8 投資理論: 天気と蓄え (畑の実りの倍率は、蓄えに届いたか)")
    w("")
    w("- 相関: 2 つの数がいっしょに動く度合い (ピアソンの相関係数。1 はいつもいっしょ、0 は関係なし、−1 は逆)。ここでは年ごとに次の数をくらべた")
    w("  - 倍率: その年の夏のはじめに決まる畑の実りの倍率 (出来事「畑」の ratio。天気の代わり。野生の実り・木の実・乳は天気で変わらない)")
    w("  - (a) 夏に蓄えが何日分増えたか: その年の夏の季節の終わりの store_days − その前の年の春の季節の終わりの store_days (刈り入れは夏)")
    w("  - (b) 人数を固定: 同じ 2 つの季節の村の蓄えの kcal の増え ÷ 夏の季節の終わりの 1 日分 (store_kcal ÷ store_days)")
    w("  - (c) 刈った量 ÷ まいた量 (その年に実った畑。8.7)")
    w("")
    w("| 年の範囲 | 年の数 | 倍率と (a) | 倍率と (b) | 倍率と (c) |")
    w("|---|---:|---:|---:|---:|")
    sets = (("記録のある年ぜんぶ", lambda x: True), (f"前の調べの範囲 ({PREV_YEARS[0]}〜{PREV_YEARS[1]} 年)", lambda x: PREV_YEARS[0] <= x["year"] <= PREV_YEARS[1]),
            ("G5 だけの年", lambda x: x["era"] == x["era_prev"] == "G5"), ("G6 だけの年", lambda x: x["era"] == x["era_prev"] == "G6"))
    vals, cvals = [], []
    for name, f in sets:
        xs = [x for x in wx if f(x)]
        if not xs:
            continue
        ca = corr([x["ratio"] for x in xs], [x["days"] for x in xs])
        cb = corr([x["ratio"] for x in xs], [x["fixed"] for x in xs])
        cc_ = [x for x in xs if x["cut"] is not None]
        cc = corr([x["ratio"] for x in cc_], [x["cut"] for x in cc_])
        vals += [v for v in (ca, cb) if v is not None]
        cvals += [cc] if cc is not None else []
        yr_ = [x["year"] for x in xs]
        w(f"| {name}{'' if '年)' in name else f' ({min(yr_)}〜{max(yr_)} 年)'} | {len(xs)} | {cr(ca)} | {cr(cb)} | {cr(cc)} |")
    w("")
    if vals:
        weak = max(abs(v) for v in vals) < WEAK
        w(f"- 年の範囲と数え方を変えるだけで、倍率と蓄えの相関は {min(vals):+.2f}〜{max(vals):+.2f} と動く。前の調べの「0.1 前後」は {PREV_YEARS[0]}〜{PREV_YEARS[1]} 年の (a) で、"
          "記録のある年ぜんぶでは上の表のとおり"
          + ("。どの範囲でも、倍率と蓄えには「ほとんど関係がない」以上のことは言えない (年が少なく、ばらつきも大きい)" if weak else ""))
        if weak:
            w("- 【読み】倍率は" + ("「刈った ÷ まいた」とはいっしょに動くが、" if cvals and min(cvals) >= WEAK else "") + "蓄えまでは届いていない。"
              "刈り入れは作った食べ物の一部で、木の実と乳は天気で変わらず、草取りと刈り入れの働き方でも実りが変わるため (8.7)。"
              "悪い年への備え (投資理論で言うリスクへの備え) が試される年が、ほとんどない")
    w("")

    # ---- 8.9 分散投資 ----
    w("### 8.9 投資理論: 分散投資の見方 (食べ物の出どころ)")
    w("")
    w("- 分散投資: いくつかの物に分けて持つと、別々に上がり下がりするぶん、合計の上がり下がりが小さくなること (マーコウィッツ 1952 の考え。一般知識)。"
      "ここでは、食べ物の出どころごとの 1 年の量の上がり下がりと、合計の上がり下がりをくらべる")
    w("- 量: 年ごと (夏から春の 4 季節がそろった年) に、出どころごとに作った量 (帳簿の作った行。木の実 = 採った + 夕方に木から取った、草の種 = 採った + 刈った、"
      "肉 = ルクの肉・ピク・ヤギの干し肉) を、いた人 (子もふくむ) の、いた日数 ÷ 120 で割った (1 人・年あたり。1 年 = 120 日)")
    w("- 変動係数 = ばらつき (標準偏差) ÷ 平均。「出どころがみな同じ向きに動いたら」の合計の変動係数は、出どころのばらつきを足して合計の平均で割った値 "
      "(出どころの変動係数を量で重みをつけた平均と同じ)。合計の変動係数がそれより小さいほど、出どころを分けたことで食べ物の量がならされた")
    ser = sources(ledger, persons, years)
    allys = sorted(ser)
    g6ys = [y for y in allys if all(r["era"] == "G6" for r in years[y])]
    names = [s_ for s_, _ in SRC]
    other = math.fsum(ser[y]["そのほか"] for y in allys)
    w("")
    w("| 出どころ | 平均 (年ぜんぶ、kcal) | ばらつき | 変動係数 | 平均 (G6 の年) | ばらつき | 変動係数 |")
    w("|---|---:|---:|---:|---:|---:|---:|")
    SA, S6 = spread_stats(ser, allys), (spread_stats(ser, g6ys) if len(g6ys) >= 3 else None)
    for s_ in names:
        ma, sa_ = SA["st"][s_]
        line = f"| {s_} | {n0(ma)} | {n0(sa_)} | {sa_ / ma if ma else 0:.2f} |"
        if S6:
            m6, s6 = S6["st"][s_]
            line += f" {n0(m6)} | {n0(s6)} | {s6 / m6 if m6 else 0:.2f} |"
        else:
            line += " - | - | - |"
        w(line)
    w(f"| **合計** | **{n0(SA['mean'])}** | **{n0(SA['sd'])}** | **{SA['cv']:.2f}** |" + (f" **{n0(S6['mean'])}** | **{n0(S6['sd'])}** | **{S6['cv']:.2f}** |" if S6 else " - | - | - |"))
    w(f"| みな同じ向きに動いたら | | | {SA['cv_parts']:.2f} |" + (f" | | {S6['cv_parts']:.2f} |" if S6 else " | | - |"))
    w("")
    w(f"- 年ぜんぶ ({SA['n']} 年): 合計の変動係数 {SA['cv']:.2f} は、みな同じ向きに動いたときの {SA['cv_parts']:.2f} の {pc(SA['cv'] / SA['cv_parts'])}。"
      f"出どころを分けたことで、上がり下がりが {pc(1 - SA['cv'] / SA['cv_parts'])} 小さくなった"
      + (f"。G6 の {S6['n']} 年では {S6['cv']:.2f} と {S6['cv_parts']:.2f} ({pc(1 - S6['cv'] / S6['cv_parts'])} 小さく)" if S6 else "")
      + (f"。どれにも入らない出どころ {n0(other)} kcal は数えていない" if other else ""))
    for lab, Sx in (("年ぜんぶ", SA), ("G6 の年", S6)):
        if not Sx:
            continue
        w("")
        w(f"相関の表 ({lab}、{Sx['n']} 年):")
        w("")
        w("| | " + " | ".join(names) + " |")
        w("|---|" + "---:|" * len(names))
        for a_ in names:
            w(f"| {a_} | " + " | ".join("1" if a_ == b_ else cr(Sx["matrix"][a_][b_]) for b_ in names) + " |")
    w("")
    w("- 読み方の注意: 年ぜんぶのばらつきの多くは、ゆっくりした流れ (人の増え方・乳と畑が増えていったこと・決まりの変わり方) で、天気の上がり下がりではない。"
      "G6 の年のほうが上がり下がりに近い。村の人がこれをねらって出どころを分けたのではない (夕方の木の実は働いた日にならず、乳は世話をする人の数で増える決まり。"
      "docs/society_phase/fidelity_checklist.md の 1.・4.)。1 人・年あたりにしたので、人数の増え方はおおよそ除いてある")
    w("")

    # ---- 8.10 使わない理論 ----
    w("### 8.10 使わない理論")
    w("")
    w("- 利子の理論 (お金の時間の値うち・割り引いて今の値うちにする計算)、株・債券の値段の理論 (CAPM など)、オプションの理論 (ブラック・ショールズなど)、年金の数理は使わない。"
      "村には利子もお金も市場もない (G6 の決めごと: 貸しに利子はない)。草の種は土器の中で減らないので、今の 1 つかみと来年の 1 つかみの値うちもほとんど同じ")
    w("- 保険の考え (破産の見込み) は 4. で、生命表は 1. で使った。アクチュアリーの方法のうち、記録で確かめられるものだけを使っている")
    w("")


def compare(w, people, village, ledger, persons, state, R, D, F, T, cl, rz, rg, s, e, u, sda_live, sda, hh, alive):
    """9. 前の調べの数とのちがい。わけは、数え直して確かめたもの (確かめた) と、確かめられないもの (見込み・分からない) を分けて書く"""
    sm = summary(T)
    w("- 「ちがいのわけ」は、ここで数え直して同じ数が出たものだけ「確かめた」と書いた。数え直せないものは「見込み」か「分からない」")
    w("")
    w("| 数 | 前の調べ | この表 | ちがいのわけ |")
    w("|---|---|---|---|")
    same = (f"{sm['e0']:.1f}・{sm['e15']:.1f}・{sm['l15']:.3f}" == "20.6・20.8・0.519")
    w(f"| e0・e15・l15 | 20.4・20.4・0.515 (報告)、20.6・20.8・0.519 (批評) | {sm['e0']:.1f}・{sm['e15']:.1f}・{sm['l15']:.3f} | "
      + ("批評と同じ数え方 (区分の中で死亡率一定) で、批評と同じ数になった (確かめた)。" if same else "批評と同じ数え方 (区分の中で死亡率一定) だが、数はちがう。")
      + "報告の数え方は残っておらず、わけは分からない |")
    w(f"| e0 の幅 | 16.1〜26.5 | {rg('all', 'e0')} | 見込み: ブートストラップの回数と乱数の種のちがい (前の調べの回数と種は残っていない) |")
    x = summary(D["tables"]["ザガ"])
    w(f"| ザガがなかったら e0 | 21.1 | {x['e0']:.1f} | 報告の数え方は残っておらず、わけは分からない |")
    # コードの表: 15 歳ちょうどの季節の終わりで割ると
    S_, s_, j = [], 1.0, 0
    while s_ > 1e-12 and j < 200 * YEAR // SD:
        S_.append(s_)
        j += 1
        s_ *= 1 - p_season(R, j * SD // YEAR)
    k = ADULT * YEAR // SD
    alt = SD / YEAR * math.fsum(S_[k:]) / S_[k]
    w(f"| コードの表の e0・e15 | 23.3・24.3 | {cl['e0']:.1f}・{cl['e15']:.1f} | "
      + (f"15 歳ちょうどの季節の終わりまで生きた人で割ると e15 は {alt:.1f} になる (確かめた)。ここは、その 1 つ前の季節の終わりまで生きた人で割った |"
         if f"{alt:.1f}" == "24.3" else "わけは分からない |"))
    # 見込みの死: 住んでいた年数 × 1 年の死亡率 (−4 ln(1 − 季節の見込み)、1 歳ごと)
    cuts = [(a_, a_ + 1) for a_ in range(0, 120)]
    alt_e = [0.0] * len(BANDS)
    for p, a_, b_ in D["spans"]:
        for age, y in enumerate(years_by(p["born_day"], a_, b_, cuts)):
            if y:
                alt_e[band_of(age)] += y * -(YEAR // SD) * math.log(1 - p_season(R, age))
    prev = (11.7, 11.6, 4.2, 18.3, 7.1, 1.1)
    ok = [i for i in range(len(BANDS)) if f"{alt_e[i]:.1f}" == f"{prev[i]:.1f}"]
    ng = [i for i in range(len(BANDS)) if i not in ok]
    w(f"| 見込みの死 (0・1〜4・5〜14・15〜39・40〜54・55 歳から) | {'・'.join(f'{x:.1f}' for x in prev)} | {'・'.join(f'{x:.1f}' for x in D['exp'])} | "
      "ここは季節の終わりごとに、その日にいた人の見込みを足した。"
      + (f"{'・'.join(BANDS[i][2] for i in ok)} は、住んでいた年数 × 1 年の死亡率 (−4 ln(1 − 季節の見込み)、1 歳ごと) で数え直すと報告と同じ (確かめた)。" if ok else "")
      + (f"{'・'.join(BANDS[i][2] for i in ng)} は、その数え方では {'・'.join(f'{alt_e[i]:.1f}' for i in ng)} で合わず、わけは分からない |" if ng else " |"))
    w(f"| NRR・r | 1.34・1.14% | {F['nrr']:.2f}・{pc(F['r'], 2)} | 報告は数え方を書いておらず、わけは分からない。ここは生まれた子の女の割合 ({F['f']:.3f}) と記録の生命表で 1 日ずつ足した |")
    v = village[-1]
    per = v["store_kcal"] / v["store_days"]
    a1 = (v["store_kcal"] + math.fsum(r["kcal"] for r in hh if r["holder"] in alive)) / per
    a2 = (v["store_kcal"] + math.fsum(r["kcal"] for r in hh)) / per
    w(f"| 家の倉を足した蓄えの日数 | 592 (家の倉)、約 604 (だれもいなくなった家の倉も) | {sda_live}・{sda} | "
      f"1 日分を store_kcal ÷ store_days (切り捨てた日数から戻した値) で割ると {a1:.0f}・{a2:.0f} になる (確かめた)。ここは、季節の終わりに生きている人の 1 日分の合計で割った |")
    # 蓄えが尽きる割合: 報告は年を夏から区切った
    rows_, fa, _ = drifts(village, "G5")
    yrs = {}
    for r, x_ in zip(rows_[1:], fa):
        yrs.setdefault(r["year"], []).append(x_)
    full = [v_ for _, v_ in sorted(yrs.items()) if len(v_) == 4]
    m_, _ = mean_sd([math.fsum(v_) for v_ in full])
    xs = [x_ for v_ in full for x_ in v_]
    q1, _ = ruin(xs, u, (2, 0, 0, 1))
    q2, _ = ruin(xs, LOW, (2, 0, 0, 2))
    se = math.sqrt(rz[("G5", 0)][2] * (1 - rz[("G5", 0)][2]) / RUNS)
    w(f"| 蓄えが尽きる割合 (G5、{u}・{LOW} 日分から) | (a) 報告 16%・83%、批評 17%・88%、(b) 批評 90%・約 100% | "
      f"(a) {pr(rz[('G5', 0)][2])}・{pr(rz[('G5', 0)][3])}、(b) {pr(rz[('G5', 1)][2])}・{pr(rz[('G5', 1)][3])} | "
      f"報告は年を夏から区切った: そう区切ると 1 年の増え減りは {m_:+.1f}" + (" (報告と同じ。確かめた)" if f"{m_:.1f}" == "-4.1" else " (報告の −4.1 と合わない)")
      + f"、尽きる割合は {pr(q1)}・{pr(q2)} で、報告の 16%・83% との差のわけは分からない。"
      f"批評とここは G5 の中の差を、はじめから 4 つずつ区切った (1 年 {rz[('G5', 0)][0]:+.1f})。批評との差は見込み: 乱数のちがい ({RUNS:,} 回なら、{pr(rz[('G5', 0)][2])} の幅は ±{pc(2 * se, 1)} ほど) |")
    g = state["era2"]["g6"]
    raw = math.fsum(n * d["mem"]["village"] for d in g["debts"] if d["status"] != "まだ" for n in d["goods"].values())
    cl_mem = math.fsum(math.ceil(n * d["mem"]["village"]) for d in g["debts"] if d["status"] != "まだ" for n in d["goods"].values())
    w(f"| 村の覚え (返し終わった {sum(1 for d in g['debts'] if d['status'] != 'まだ')} 回) | 7,617 (批評)、7,618 (MMT の報告) | {n0(cl_mem)} | "
      f"覚えの倍率をそのまま掛けて足すと {raw:,.1f} (四捨五入で {raw:,.0f})、出来事の文の数 (コードは 1 回ずつ切り上げ) を足すと {n0(cl_mem)} (確かめた) |")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--data", default=os.environ.get("SOC_DATA") or str(HERE.parent / "data"))
    ap.add_argument("--out", default=None)
    a = ap.parse_args()
    txt = report(a.data)
    if not a.out:
        sys.stdout.write(txt)
        return
    out = Path(a.out)
    tmp = out.with_name(out.name + ".tmp")
    tmp.write_text(txt, encoding="utf-8")
    os.replace(tmp, out)
    print(f"{out} に書いた ({len(txt.splitlines())} 行)")


if __name__ == "__main__":
    main()
