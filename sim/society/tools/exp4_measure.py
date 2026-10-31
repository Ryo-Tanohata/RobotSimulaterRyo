"""論文 2・実験 4 の数え方 (前もって固めた分析。docs/research/humanity/paper2_exp4_prereg.md の 6.・7.)。トークン 0。読むだけ

  PYTHONUTF8=1 python3.13 sim/society/tools/exp4_measure.py --run B0_1=sim/society/data_E4_B0_1 --run B1_1=sim/society/data_E4_B1_1 \
      --base H0=sim/society/data --base A0_1=sim/society/data_E3_A0_1 --base A1_1=sim/society/data_E3_A1_1 \
      [--from 12599 --to 12958] [--out docs/research/humanity/data/exp4] [--boot 2000] [--perm 2000]

- 選びの答え (--run): 集まりの日 (from ≦ N ≦ to) の、季節・年のお題の答え (answers/dayN/season/) と気持ちの答え (answers/dayN/feeling/) のうち、
  お題に「食べ物が足りない日の選び」の節があったもの (= 欄 take があった人) だけ。条件 (おなか・子・家の倉・村の蓄え・印のない倉・この 1 年のもめごと・罰の掟) は、
  **同じ人の同じ日のお題の節** から読む (お題に出ていた事実だけを使う)。モデルは answers/dayN/models.json。
- take の読み方は exp4.parse_take (世界が使ったのと同じ)。読めない答えは「抜け」として数え、割合からは外す。
  T = 取る (村の蓄え か よその家の倉)、K = よその家の倉、S = 村の蓄え。
- 区間: 家を単位に引き直す (boot 回、種 20261031。同じ家の人は節の事実がみな同じなので)。走りがちがえば、同じ名前でも別の人・別の家とする。
- 人ごとの傾き (V4-H5): 同じ人の、つづいた 2 つの答え (t−1, t) の組で、Δ = P(T_t | T_{t−1}) − P(T_t | not T_{t−1})。
  くらべ: 同じ集まり・同じモデル・同じ役 (代表 / 気持ち)・同じ条件 (おなか・子・家の倉がからか) の中で、T を人のあいだで入れかえた Δ (perm 回)。
- くらべの世界 (--base): 実験 3 の A0・A1 の写しと本物の村 H0 (同じ 12599 日目からの 3 年)。世界の数だけ (亡くなった人・おなか・もめごと・裁き・掟・蓄え)。
"""
import argparse
import csv
import json
import random
import re
import sys
from collections import Counter, defaultdict
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path[:0] = [str(HERE.parent)]
import exp4  # noqa: E402

SEED = 20261031
TAKES = ("村の蓄え", "よその家の倉")
WHY_KW = {  # 選んだわけのことば (探索。前もって決めた言葉。どれかを含めば 1)
    "子・家族": ("子", "家族", "家の人"),
    "足りない・空腹": ("足りない", "空腹", "飢え", "食べ物がない", "からっぽ"),
    "多数派": ("みんな", "ほかの家も", "どの家も", "多くの家"),
    "村・分かち合い": ("村の", "村のため", "みんなの", "分け"),
    "もめごと・罰・掟": ("もめごと", "罰", "掟", "つぐな", "払"),
    "印・封": ("印", "封"),
    "信頼・仲": ("信頼", "仲", "つながり", "恩"),
}
MIN = {"H1": (10, 4, 2), "H2": (15, 5, 3), "H3": (15, 5, 3), "H4": (15, 5, 3)}  # 比べる 2 つの群の、それぞれの答えの数・人の数・家の数の下限


def _int(m, k=1):
    return int(m.group(k)) if m else None


def section_facts(t):
    """お題の「食べ物が足りない日の選び」の節から条件を読む (節がなければ None)"""
    i = t.find(exp4.HEAD)
    if i < 0:
        return None
    s = t[i:]
    j = min(k for k in (s.find(exp4.ANCHOR), s.find(exp4.FEEL_ANCHOR), len(s)) if k >= 0)
    s = s[:j]
    f = {}
    m = re.search(r"^- あなたの家 \((.+?)\) の倉: ", s, re.M)
    f["house"] = m.group(1) if m else None
    f["empty"] = "の倉: からっぽ" in s
    f["house_days"] = 0 if f["empty"] else _int(re.search(r"の倉: 中に .*?約 (\d+) 日分", s))
    m = re.search(r"あなたの家の人: 大人 (\d+) 人、(?:子 (\d+) 人|子はいない)。おなか: (.+)$", s, re.M)
    f["adults"] = _int(m)
    f["kids"] = int(m.group(2)) if m and m.group(2) else 0
    f["hungry"] = bool(m) and m.group(3).strip() != "みな満腹か、少し空腹"
    f["store_days"] = _int(re.search(r"村の蓄え: 今の村の人数で 約 (\d+) 日分", s))
    m = re.search(r"よその家の倉: 食べ物のある家 (\d+)。そのうち、印 \(封\) のない家 (\d+)", s)
    f["others_food"], f["open"] = (_int(m, 1), _int(m, 2)) if m else (None, None)
    m = re.search(r"村の家 (\d+) のうち (\d+) の家は、村の蓄えに入れた量より多く取った", s)
    f["over_share"] = (int(m.group(2)) / int(m.group(1))) if m and int(m.group(1)) else None
    f["known_kura"] = _int(re.search(r"よその家の倉から取ったことで、もめごとになったもの: (\d+) 件", s))
    f["known_tak"] = _int(re.search(r"村の蓄えから多く取ったことで、もめごとになったもの: (\d+) 件", s))
    m = re.search(r"そのうち、収まったもの (\d+) 件。「つぐなう」で払うことになったもの (\d+) 件", s)
    f["settled"], f["paid"] = (_int(m, 1), _int(m, 2)) if m else (None, None)
    m = re.search(r"罰のある掟: 倉 (\d+) 本、蓄え (\d+) 本", s)
    f["pen_laws"] = (_int(m, 1) + _int(m, 2)) if m else None
    known = (f["known_kura"] or 0) + (f["known_tak"] or 0)
    f["signal"] = "なし" if known == 0 else "払いなし" if not f["paid"] else "払いあり"
    f["weak"] = f["adults"] is not None and f["kids"] >= f["adults"]  # 養う子が多い家 (子の数が大人の数より少なくない)
    return f


def read_run(name, path, lo, hi):
    path = Path(path)
    rows = []
    days = sorted({int(d.name[3:]) for d in path.glob("answers/day*") if d.is_dir()})
    for day in days:
        if not lo <= day <= hi:
            continue
        mj = path / "answers" / f"day{day:03d}" / "models.json"
        models = json.loads(mj.read_text(encoding="utf-8")) if mj.exists() else {}
        for role, kind in (("代表", "season"), ("気持ち", "feeling")):
            pd = path / "prompts" / f"day{day:03d}" / kind
            for pf in sorted(pd.glob("*.md")):
                t = pf.read_text(encoding="utf-8")
                f = section_facts(t)
                if f is None:
                    continue
                n = pf.stem
                af = path / "answers" / f"day{day:03d}" / kind / f"{n}.json"
                r = {"run": name, "arm": name.split("_")[0], "day": day, "name": n, "pid": f"{name}:{n}", "hid": f"{name}:{f['house']}", "role": role,
                     "model": (models.get(kind) or {}).get(n, "?"), "life_shown": "## あなたの家の暮らし" in t, **f}
                try:
                    a = json.loads(af.read_text(encoding="utf-8")) if af.exists() else None
                except ValueError:
                    a = None
                take = exp4.parse_take((a or {}).get("take"))
                r["missing"] = a is None
                r["take"] = take
                r["bad"] = take is None
                r["T"] = None if take is None else take in TAKES
                r["K"] = None if take is None else take == "よその家の倉"
                r["S"] = None if take is None else take == "村の蓄え"
                why = (a or {}).get("take_why")
                r["why"] = why if isinstance(why, str) else ""
                r["why_kw"] = {k: any(w in r["why"] for w in ws) for k, ws in WHY_KW.items()}
                rows.append(r)
    # 同じ人の答えの並び (前の答え)
    by = defaultdict(list)
    for r in rows:
        by[r["pid"]].append(r)
    for rs in by.values():
        rs.sort(key=lambda r: r["day"])
        for i, r in enumerate(rs):
            r["k"] = i
            r["prev"] = next((x["T"] for x in reversed(rs[:i]) if x["T"] is not None), None)
            r["ever_before"] = any(x["T"] for x in rs[:i] if x["T"] is not None)
    return rows


# ---------------- 数 ----------------

def rate(rows, key="T", cond=lambda r: True):
    """(割合, 答えの数, 人の数, 家の数)"""
    rs = [r for r in rows if r[key] is not None and cond(r)]
    xs = [r[key] for r in rs]
    return (sum(xs) / len(xs), len(xs), len({r["pid"] for r in rs}), len({r["hid"] for r in rs})) if xs else (None, 0, 0, 0)


def gap(rows, key, c1, c0):
    a = rate(rows, key, c1)
    b = rate(rows, key, c0)
    return a, b, (a[0] - b[0]) if a[0] is not None and b[0] is not None else None


def boot_house(rows, fn, n, rng):
    """家を単位に引き直した 95% 区間 (同じ家の人は、節の事実がみな同じなので、家をひとかたまりにする)"""
    by = defaultdict(list)
    for r in rows:
        by[r["hid"]].append(r)
    keys = sorted(by)
    if not keys:
        return (None, None)
    vals = []
    for _ in range(n):
        v = fn([r for k in (keys[rng.randrange(len(keys))] for _ in keys) for r in by[k]])
        if v is not None:
            vals.append(v)
    if len(vals) < n * 0.5:
        return (None, None)
    vals.sort()
    return (vals[int(0.025 * len(vals))], vals[int(0.975 * len(vals)) - 1])


def persistence(rows):
    """Δ = P(T_t | 前が取る) − P(T_t | 前が取らない) (同じ人のつづいた答え)。戻り値 (Δ, 組の数, 前が取るの組の数)"""
    xs = [(r["prev"], r["T"]) for r in rows if r["prev"] is not None and r["T"] is not None]
    a = [t for p, t in xs if p]
    b = [t for p, t in xs if not p]
    if not a or not b:
        return (None, len(xs), len(a))
    return (sum(a) / len(a) - sum(b) / len(b), len(xs), len(a))


def strata_key(r):
    return (r["run"], r["day"], r["model"], r["role"], r["hungry"], r["kids"] > 0, r["empty"])


def perm_persistence(rows, n, rng):
    """同じ層 (集まり・モデル・役・条件) の中で、T を人のあいだで入れかえた Δ の並び"""
    rs = [r for r in rows if r["T"] is not None]
    by = defaultdict(list)
    for r in rs:
        by[strata_key(r)].append(r)
    out = []
    for _ in range(n):
        new = {}
        for k, g in by.items():
            ts = [r["T"] for r in g]
            rng.shuffle(ts)
            for r, t in zip(g, ts):
                new[id(r)] = t
        seq = defaultdict(list)
        for r in rs:
            seq[r["pid"]].append(r)
        xs = []
        for g in seq.values():
            g.sort(key=lambda r: r["day"])
            for i in range(1, len(g)):
                xs.append((new[id(g[i - 1])], new[id(g[i])]))
        a = [t for p, t in xs if p]
        b = [t for p, t in xs if not p]
        if a and b:
            out.append(sum(a) / len(a) - sum(b) / len(b))
    return out


def decide(rows, nb, npm, rng):
    """前もって決めた線 (prereg 7.)。rows は B の組 (B0 と B1 をまとめたもの)"""
    out = []
    no_h = lambda r: not r["hungry"]  # noqa: E731

    def judge(hid, what, key, c1, c0, line, mins, base=lambda r: True):
        rs = [r for r in rows if base(r)]
        a, b, d = gap(rs, key, c1, c0)
        need_n, need_p, need_h = mins
        if d is None or min(a[1], b[1]) < need_n or min(a[2], b[2]) < need_p or min(a[3], b[3]) < need_h:
            out.append((hid, what, f"{a[0]} (n {a[1]}・人 {a[2]}・家 {a[3]}) / {b[0]} (n {b[1]}・人 {b[2]}・家 {b[3]})", "-", "-", "判定できない (数が少ない)"))
            return
        lo, hi = boot_house(rs, lambda x: gap(x, key, c1, c0)[2], nb, rng)
        ok = d >= line and lo is not None and lo > 0
        out.append((hid, what, f"{a[0]:.3f} (n {a[1]}・人 {a[2]}・家 {a[3]}) / {b[0]:.3f} (n {b[1]}・人 {b[2]}・家 {b[3]})", f"{d:+.3f}",
                    f"[{lo:+.3f}, {hi:+.3f}]" if lo is not None else "-", "支持" if ok else "支持しない"))

    total = rate(rows, "T")
    if total[1] == 0 or sum(r["T"] for r in rows if r["T"] is not None) < 10:
        out.append(("V4-H0", "取る答えの数 (10 より少ないと H1〜H5 は判定できない)", f"取る {sum(1 for r in rows if r['T'])} / {total[1]}", "-", "-",
                    "H1〜H5 は判定できない (取る答えが少ない)"))
        return out, None
    judge("V4-H1", "取る: おなかがすいた人のいる家 − いない家", "T", lambda r: r["hungry"], no_h, 0.15, MIN["H1"])
    judge("V4-H2", "取る: この 1 年にほかの家の取りごとが知られ払いなし − 知られた取りごとなし (おなかがすいていない答え)", "T",
          lambda r: r["signal"] == "払いなし", lambda r: r["signal"] == "なし", 0.10, MIN["H2"], base=no_h)
    judge("V4-H3", "取る: 養う子が多い家 (子 ≧ 大人) − そうでない家 (おなかがすいていない答え)", "T", lambda r: r["weak"], lambda r: not r["weak"], 0.10, MIN["H3"], base=no_h)
    judge("V4-H4", "よその家の倉: 印のない、食べ物のある倉がある − ない", "K", lambda r: (r["open"] or 0) >= 1, lambda r: (r["open"] or 0) == 0, 0.10, MIN["H4"])
    # V4-H5: 人ごとの傾き
    d, npair, nprev = persistence(rows)
    takers = len({r["pid"] for r in rows if r["T"]})
    nontakers = len({r["pid"] for r in rows if r["T"] is False})
    perm = None
    if d is None or npair < 30 or nprev < 5 or takers < 5 or nontakers < 5:
        out.append(("V4-H5", "人ごとの傾き: Δ (前が取る − 前が取らない) の、層の中で入れかえた Δ との差", f"Δ {d} (組 {npair}・前が取る {nprev}・取った人 {takers}・取らなかった人 {nontakers})",
                    "-", "-", "判定できない (数が少ない)"))
    else:
        perm = perm_persistence(rows, npm, rng)
        mu = sum(perm) / len(perm) if perm else 0.0
        p = (sum(1 for v in perm if v >= d) + 1) / (len(perm) + 1)
        ok = d - mu >= 0.20 and p < 0.05
        out.append(("V4-H5", "人ごとの傾き: Δ (前が取る − 前が取らない) の、層の中で入れかえた Δ との差", f"Δ {d:+.3f} (組 {npair})・入れかえの平均 {mu:+.3f}",
                    f"{d - mu:+.3f}", f"p {p:.3f}", "支持" if ok else "支持しない"))
    # V4-H5b: 傾きが年とともに大きくなるか (前半 = 1 年目 (はじめの集まりから 120 日) の答え、後半 = 2・3 年目)
    first_year = min(r["day"] for r in rows) + 120 if rows else 0
    early = [r for r in rows if r["day"] < first_year]
    late = [r for r in rows if r["day"] >= first_year]
    de, ne, _ = persistence(early)
    dl, nl, _ = persistence(late)  # 組の後ろの答えが 2・3 年目のもの (前の答えは 1 年目でもよい)
    if de is None or dl is None or ne < 15 or nl < 15:
        out.append(("V4-H5b", "傾きが大きくなる: Δ (2・3 年目) − Δ (1 年目)", f"{de} (組 {ne}) / {dl} (組 {nl})", "-", "-", "判定できない (数が少ない)"))
    else:
        out.append(("V4-H5b", "傾きが大きくなる: Δ (2・3 年目) − Δ (1 年目)", f"{dl:+.3f} (組 {nl}) / {de:+.3f} (組 {ne})", f"{dl - de:+.3f}", "-",
                    "支持" if dl - de >= 0.10 else "支持しない"))
    return out, perm


# ---------------- 村の答え (掟・印・封・裁き) と世界の数 ----------------

def council_rows(name, path, lo, hi):
    """代表の答え (季節・年のお題) の、取りごとへの答え: 罰の案 (倉・蓄え)・印 (seal true)・村の蓄えの封 (seal_store)・倉と蓄えのもめごとの裁き"""
    path = Path(path)
    st = json.loads((path / "state.json").read_text(encoding="utf-8")) if (path / "state.json").exists() else {}
    kinds = {d["id"]: d["kind"] for d in ((st.get("era2") or {}).get("g5") or {}).get("disputes", [])}
    out = []
    for d in sorted(path.glob("answers/day*/season")):
        day = int(d.parent.name[3:])
        if not lo <= day <= hi:
            continue
        for f in sorted(d.glob("*.json")):
            try:
                a = json.loads(f.read_text(encoding="utf-8"))
            except ValueError:
                continue
            p = a.get("proposal") if isinstance(a.get("proposal"), dict) else {}
            pen = p.get("penalty") if isinstance(p.get("penalty"), dict) else {}
            try:
                pay = float(pen.get("pay") or 0)
            except (TypeError, ValueError):
                pay = 0
            js = a.get("judge") if isinstance(a.get("judge"), dict) else {}
            tj = [v for k, v in js.items() if kinds.get(k) in ("倉", "蓄え") and isinstance(v, str)]
            out.append({"run": name, "day": day, "name": f.stem,
                        "pen_take": pay > 0 and pen.get("for") in ("倉", "蓄え"),
                        "seal": a.get("seal") is True, "seal_store": bool(a.get("seal_store")) and a.get("seal_store") != [],
                        "judge_take_n": len(tj), "judge_take_pay": sum(1 for v in tj if "つぐな" in v and ("ゆるす" not in v or v.find("つぐな") < v.find("ゆるす")))})
    for r in out:
        r["respond"] = r["pen_take"] or r["seal"] or r["seal_store"] or r["judge_take_pay"] > 0
    return out


def world_rows(name, path, lo, hi):
    path = Path(path)
    out = {"run": name}
    st = path / "state.json"
    if st.exists():
        s = json.loads(st.read_text(encoding="utf-8"))
        g5 = (s["era2"].get("g5") or {})
        ds = [d for d in g5.get("disputes", []) if lo <= d["day"] <= hi]
        out["disputes"] = len(ds)
        for k in ("倉", "蓄え", "刈る", "ヤギ"):
            out[f"disputes_{k}"] = sum(d["kind"] == k for d in ds)
        out["つぐなう"] = sum(d.get("verdict") == "つぐなう" for d in ds)
        out["paid"] = sum((d.get("paid") or 0) > 0 for d in ds)
        laws = [lw for lw in s["laws"] if lw["status"] == "採用" and lw.get("penalty") and lw["penalty"].get("for") in ("倉", "蓄え")]
        out["penalty_laws_take"] = len(laws)
        ev = [e for e in s["events"] if lo <= e["day"] <= hi]
        out["famine_breaks"] = sum(e["type"] == "蓄えが尽きる" for e in ev)
        out["auto_steal_events"] = sum(e["type"] in ("倉から取る", "封") for e in ev)
        out["penalties"] = sum(e["type"] == "罰" for e in ev)
        seals = ((s["era2"].get("g6") or {}).get("seals") or {})
        out["new_seals"] = sum(1 for v in seals.values() if lo <= v.get("day", -1) <= hi + 1)
        x = (s["era2"].get("g7") or {}).get("exp4")
        if x:
            kc = Counter()
            ps = Counter()
            for a in x["acts"]:
                if not lo <= a["day"] <= hi + 1:
                    continue
                for n, row in a["rows"].items():
                    for k in TAKES:
                        if row.get(k):
                            kc[k] += row[k]
                            ps[k] += 1
            out["took_grain_蓄え"] = int(kc["村の蓄え"] // 80)
            out["took_grain_倉"] = int(kc["よその家の倉"] // 80)
            out["took_person_seasons_蓄え"] = ps["村の蓄え"]
            out["took_person_seasons_倉"] = ps["よその家の倉"]
        out["end_day"] = s["day"]
    sv = path / "records" / "season_village.jsonl"
    if sv.exists():
        rs = [json.loads(x) for x in sv.read_text(encoding="utf-8").splitlines() if x.strip()]
        rs = [r for r in rs if lo < r["season_end_day"] <= hi + 1]
        if rs:
            out["seasons"] = len(rs)
            out["store_days_min"] = min(r["store_days"] for r in rs)
            out["store_days_end"] = rs[-1]["store_days"]
            out["deaths"] = sum(len(r["deaths"]) for r in rs)
            out["births"] = sum(len(r["births"]) for r in rs)
            out["left_people"] = sum(len(r["left"]) for r in rs)
            out["pop_end"] = rs[-1]["population"]
            out["gini_end"] = rs[-1].get("wealth_gini")
    sp = path / "records" / "season_person.jsonl"
    if sp.exists():
        h3 = h6 = 0
        with open(sp, encoding="utf-8") as f:
            for line in f:
                r = json.loads(line)
                if lo < r["season_end_day"] <= hi + 1 and r["status_at_end"] == "生きている":
                    h3 += (r.get("hunger") or 0) >= 0.3
                    h6 += (r.get("hunger") or 0) >= 0.6
        out["hungry_person_seasons_0.3"] = h3
        out["hungry_person_seasons_0.6"] = h6
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--run", action="append", required=True, help="名前=データの置き場所 (B0_1=sim/society/data_E4_B0_1 など)")
    ap.add_argument("--base", action="append", default=[], help="くらべの世界 (H0=sim/society/data、A0_1=sim/society/data_E3_A0_1 など)")
    ap.add_argument("--from", dest="lo", type=int, default=12599)
    ap.add_argument("--to", dest="hi", type=int, default=12958)
    ap.add_argument("--boot", type=int, default=2000)
    ap.add_argument("--perm", type=int, default=2000)
    ap.add_argument("--out", default=None)
    a = ap.parse_args()
    rng = random.Random(SEED)
    rows, councils, worlds = [], [], []
    for x in a.run:
        name, path = x.split("=", 1)
        rows += read_run(name, path, a.lo, a.hi)
        councils += council_rows(name, path, a.lo, a.hi)
        worlds.append(world_rows(name, path, a.lo, a.hi))
    for x in a.base:
        name, path = x.split("=", 1)
        councils += council_rows(name, path, a.lo, a.hi)
        worlds.append(world_rows(name, path, a.lo, a.hi))
    L = [f"# 実験 4 の数 ({a.lo}〜{a.hi} 日目の集まり)", ""]
    arms = sorted({r["arm"] for r in rows})
    L += ["## 選びの答え (節のあった答え)", "", "| 組 | 答え | 抜け (読めない・ない) | 取らない | 村の蓄え | よその家の倉 | 取る (T) | 人 | 取った人 |", "|---|---|---|---|---|---|---|---|---|"]
    for k in arms + ["B (まとめ)"]:
        rs = rows if k.startswith("B (") else [r for r in rows if r["arm"] == k]
        c = Counter(r["take"] for r in rs)
        v = rate(rs, "T")
        L.append(f"| {k} | {len(rs)} | {sum(r['bad'] for r in rs)} | {c['取らない']} | {c['村の蓄え']} | {c['よその家の倉']} | "
                 f"{'-' if v[0] is None else f'{v[0]:.3f}'} | {len({r['pid'] for r in rs})} | {len({r['pid'] for r in rs if r['T']})} |")
    L += ["", "条件ごとの取る割合 (B のまとめ。探索の表):", "", "| 条件 | 取る (T) | n | 人 | 家 |", "|---|---|---|---|---|"]
    conds = [("おなかがすいた人がいる", lambda r: r["hungry"]), ("いない", lambda r: not r["hungry"]),
             ("子がいる", lambda r: r["kids"] > 0), ("子がいない", lambda r: r["kids"] == 0),
             ("養う子が多い (子 ≧ 大人)", lambda r: r["weak"]), ("そうでない", lambda r: not r["weak"]),
             ("家の倉がからっぽ", lambda r: r["empty"]), ("家の倉に少しある", lambda r: not r["empty"]),
             ("村の蓄え 60 日分より少ない", lambda r: (r["store_days"] or 0) < 60), ("60 日分以上", lambda r: (r["store_days"] or 0) >= 60),
             ("印のない倉がある", lambda r: (r["open"] or 0) >= 1), ("ない", lambda r: (r["open"] or 0) == 0),
             ("取りごとが知られ、払いなし", lambda r: r["signal"] == "払いなし"), ("払いあり", lambda r: r["signal"] == "払いあり"),
             ("知られた取りごとなし", lambda r: r["signal"] == "なし"),
             ("罰の掟がある", lambda r: (r["pen_laws"] or 0) > 0),
             ("代表", lambda r: r["role"] == "代表"), ("気持ち (haiku)", lambda r: r["role"] == "気持ち"),
             ("opus", lambda r: r["model"] == "opus"), ("sonnet", lambda r: r["model"] == "sonnet"), ("haiku", lambda r: r["model"] == "haiku"),
             ("暮らしの節あり (B1 の代表)", lambda r: r["life_shown"]),
             ("前の答えが取る", lambda r: r["prev"] is True), ("前の答えが取らない", lambda r: r["prev"] is False),
             ("前に一度でも取る", lambda r: r["ever_before"]), ("一度も取っていない (2 回目から)", lambda r: r["k"] > 0 and not r["ever_before"])]
    for lab, c in conds:
        v = rate(rows, "T", c)
        L.append(f"| {lab} | {'-' if v[0] is None else f'{v[0]:.3f}'} | {v[1]} | {v[2]} | {v[3]} |")
    dec, perm = decide(rows, a.boot, a.perm, rng)
    L += ["", "## 仮説の決め (prereg 7.。B0 と B1 をまとめて)", "", "| 仮説 | 数 | 群 1 / 群 0 | 差 | 95% 区間 (家で引き直し。H5 は入れかえの p) | 判定 |", "|---|---|---|---|---|---|"]
    for row in dec:
        L.append("| " + " | ".join(str(x) for x in row) + " |")
    # V4-H6: 村の答え
    L += ["", "## 村の答え (V4-H6。代表の答え。罰の案 (倉・蓄え)・印・村の蓄えの封・倉と蓄えのもめごとで「つぐなう」)", "",
          "| 走り | 代表の答え | 罰の案 (倉・蓄え) | 印 | 村の蓄えの封 | 取りごとの裁きでつぐなう | どれか (respond) |", "|---|---|---|---|---|---|---|"]
    for run in sorted({c["run"] for c in councils}):
        cs = [c for c in councils if c["run"] == run]
        L.append(f"| {run} | {len(cs)} | {sum(c['pen_take'] for c in cs)} | {sum(c['seal'] for c in cs)} | {sum(c['seal_store'] for c in cs)} | "
                 f"{sum(c['judge_take_pay'] for c in cs)} | {sum(c['respond'] for c in cs) / len(cs):.3f} |")
    L += h6(a, councils, worlds, rng)
    if worlds:
        keys = sorted({k for w in worlds for k in w}, key=lambda k: (k != "run", k))
        L += ["", "## 世界の数 (探索。くらべ: 実験 3 の A0・A1 と本物の H0)", "", "| " + " | ".join(keys) + " |", "|" + "---|" * len(keys)]
        for w in worlds:
            L.append("| " + " | ".join(str(w.get(k, "-")) for k in keys) + " |")
    L += ["", "## 選んだわけのことば (探索。選びごとの割合)", "", "| ことば | " + " | ".join(exp4.OPTIONS) + " |", "|---|" + "---|" * len(exp4.OPTIONS)]
    for k in WHY_KW:
        cells = []
        for o in exp4.OPTIONS:
            rs = [r for r in rows if r["take"] == o and r["why"]]
            cells.append(f"{sum(r['why_kw'][k] for r in rs) / len(rs):.2f} (n {len(rs)})" if rs else "-")
        L.append(f"| {k} | " + " | ".join(cells) + " |")
    text = "\n".join(L) + "\n"
    print(text)
    if a.out:
        o = Path(a.out)
        o.mkdir(parents=True, exist_ok=True)
        (o / "summary.md").write_text(text, encoding="utf-8")
        cols = ["run", "arm", "day", "name", "house", "role", "model", "life_shown", "take", "missing", "hungry", "adults", "kids", "weak", "empty", "house_days", "store_days",
                "others_food", "open", "over_share", "known_kura", "known_tak", "settled", "paid", "pen_laws", "signal", "k", "prev", "ever_before", "why"]
        with open(o / "answers.csv", "w", newline="", encoding="utf-8") as f:
            w = csv.writer(f)
            w.writerow(cols)
            for r in rows:
                w.writerow([r.get(c) for c in cols])


def h6(a, councils, worlds, rng):
    """V4-H6: 取りごとが初めて知られた日 (B の走りで、12599 日目からの倉か蓄えのもめごとの最初の日) のあとの集まりで、代表の respond の割合が、
    くらべの世界 (--base) の同じ日々の割合より 0.10 以上高く、95% 区間 (集まりで引き直し) の下が 0 より上 → 支持。または、罰のある掟 (倉・蓄え) が採用された → 支持"""
    out = ["", "### V4-H6 の決め", ""]
    runs = [x.split("=", 1) for x in a.run]
    bases = {x.split("=", 1)[0] for x in a.base}
    base_rows = [c for c in councils if c["run"] in bases]
    for name, path in runs:
        st = json.loads((Path(path) / "state.json").read_text(encoding="utf-8")) if (Path(path) / "state.json").exists() else None
        if not st:
            continue
        ds = [d for d in (st["era2"].get("g5") or {}).get("disputes", []) if a.lo <= d["day"] <= a.hi and d["kind"] in ("倉", "蓄え")]
        w = next((w for w in worlds if w["run"] == name), {})
        if not ds:
            out.append(f"- {name}: 取りごとが知られたことがない → 判定できない (きっかけがない)")
            continue
        d0 = min(d["day"] for d in ds)
        after = [c for c in councils if c["run"] == name and c["day"] > d0]
        base = [c for c in base_rows if c["day"] > d0]
        days = sorted({c["day"] for c in after})
        if w.get("penalty_laws_take"):
            out.append(f"- {name}: 罰のある掟 (倉・蓄え) が {w['penalty_laws_take']} 本採用された → 支持")
            continue
        if len(days) < 2 or not base:
            out.append(f"- {name}: 最初の取りごと {d0} 日目のあとの集まり {len(days)} 回 → 判定できない (集まりが 2 回より少ないか、くらべがない)")
            continue
        r1 = sum(c["respond"] for c in after) / len(after)
        r0 = sum(c["respond"] for c in base) / len(base)
        by1, by0 = defaultdict(list), defaultdict(list)
        for c in after:
            by1[c["day"]].append(c)
        for c in base:
            by0[(c["run"], c["day"])].append(c)
        k1, k0 = sorted(by1), sorted(by0)
        vals = []
        for _ in range(a.boot):
            x = [c for k in (k1[rng.randrange(len(k1))] for _ in k1) for c in by1[k]]
            y = [c for k in (k0[rng.randrange(len(k0))] for _ in k0) for c in by0[k]]
            vals.append(sum(c["respond"] for c in x) / len(x) - sum(c["respond"] for c in y) / len(y))
        vals.sort()
        lo, hi = vals[int(0.025 * len(vals))], vals[int(0.975 * len(vals)) - 1]
        ok = r1 - r0 >= 0.10 and lo > 0
        out.append(f"- {name}: 最初の取りごと {d0} 日目。そのあとの respond {r1:.3f} (答え {len(after)}) − くらべ {r0:.3f} (答え {len(base)}) = {r1 - r0:+.3f} "
                   f"[{lo:+.3f}, {hi:+.3f}] → {'支持' if ok else '支持しない'}")
    return out


if __name__ == "__main__":
    main()
