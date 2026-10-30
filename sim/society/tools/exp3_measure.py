"""論文 2・実験 3 の数え方 (前もって固めた分析。docs/research/humanity/paper2_exp3_prereg.md の 5.・6.)。トークン 0。読むだけ

  PYTHONUTF8=1 python3.13 sim/society/tools/exp3_measure.py --run H0=sim/society/data --run A0=sim/society/data_E3_A0_1 --run A2=sim/society/data_E3_A2_1 \
      [--from 12599 --to 12958] [--out docs/research/humanity/data/exp3] [--boot 2000]

- 1 つの走り (--run 名前=データの置き場所) ごとに、集まりの日 (answers/dayN/season/ がある日。from ≦ N ≦ to) の代表の答えを読む。
  答えた人の家・まだ収まっていないもめごと (言い出した家・相手)・家ごとの持ち物・村の蓄えの日数は、同じ日のお題 (prompts/dayN/season/名前.md) から読む
  (お題に出ていた事実だけを使う。足した節は使わない。どの組も同じ読み方)。モデルは answers/dayN/models.json。
- 名前の頭が同じ走り (A0 と A0_2 など、「_」の前が同じ) は、同じ組としてまとめる。H0 (本物の村のその年) は、くらべる組 A0 の 2 つ目の写しとして数える。
- 数 (答えごと): 裁き (judge。もめごとごと。席 = 言い出した家 / 相手の家 / かかわらない家)・裁きの方針 (judge_rule)・家の倉 (keep)・印 (seal)・分ける (share)・
  掟の案 (罰 penalty の pay > 0・税 tax)・票 (反対)・上乗せ (利子 > 0)・受け入れの方針 (false)・村を出る (leave)・ことば (say・票のわけ・案・気持ち・裁きの文)。
- 区間: 集まり (日) を単位に引き直す (boot 回、種 20261030)。
- 世界の数 (探索): その走りの state.json の g5.disputes (日が from〜to) と records/season_village.jsonl (季節の終わりが from〜to)。
"""
import argparse
import csv
import json
import random
import re
from collections import Counter, defaultdict
from pathlib import Path

SEED = 20261030
SCARCE, PLENTY = 100, 150  # H5: 集まりの日の村の蓄えが 100 日分より少ない / 150 日分以上 (本物の 12599〜12958 日目の集まりで 2 回 / 3 回)
KW = {  # ことばの分け方 (探索。前もって決めた言葉。どれかを含めば 1)
    "多数派": ("どの家も", "ほかの家も", "多くの家", "みんな取", "みんなが取", "みなが取", "みんなやって", "みんなしている"),
    "前例": ("これまで", "前から", "今までどおり", "いつもどおり", "前の例"),
    "暮らしの苦しさ": ("足りない", "空腹", "おなか", "からっぽ", "飢え"),
    "子": ("子",),
    "払い・つぐない": ("払", "つぐな"),
    "罰・取り決め": ("罰", "封", "印"),
}
COPY = ("入れた量より多く取った", "払った家はない", "払うことになったのは", "何も持たない家", "印 (封) のある家", "印は残らない")  # 足した節の写し (探索)


def _verdict(v):
    if not isinstance(v, str):
        return None
    i, j = v.find("つぐな"), v.find("ゆるす")
    if i < 0 and j < 0:
        return None
    if i < 0:
        return "ゆるす"
    if j < 0:
        return "つぐなう"
    return "つぐなう" if i < j else "ゆるす"


def _prompt_facts(t):
    """お題から: 家・まだ収まっていないもめごと・家ごとの持ち物 (草の種のつかみ。ヤギは 375 つかみ)・村の蓄えの日数・家の子の数"""
    h = None
    m = re.search(r"^## あなたの家族 \((.+?)\)$", t, re.M)
    if m:
        h = m.group(1)
    else:
        m = re.search(r"あなたは (\S+?) の代表ではないが", t)
        h = m.group(1) if m else None
    disp = {m.group(1): (m.group(2), m.group(3)) for m in re.finditer(r"^- \[(M\d+)\] \(\S+\) (\S+?)が言い出した。相手は(\S+?) \(", t, re.M)}
    wealth = {}
    m = re.search(r"^家ごとの持ち物: (.+)$", t, re.M)
    if m:
        for x in re.finditer(r"([^、\s]+?の家) \(倉: [^、]+、([^、]*?)、ヤギ (\d+) 頭\)", m.group(1)):
            g = re.search(r"草の種 (\d+) つかみ", x.group(2))
            wealth[x.group(1)] = (int(g.group(1)) if g else 0) + 375 * int(x.group(3))
    m = re.search(r"^村の蓄え: .*約 (\d+) 日分", t, re.M)
    days = int(m.group(1)) if m else None
    sec = re.search(r"^## あなたの家族 .*?(?=^## )", t, re.M | re.S)
    kids = len(re.findall(r"^- 子: ", sec.group(0), re.M)) if sec else 0
    added = ("## あなたの家の暮らし" in t, "## 村のまわりの様子" in t)
    return h, disp, wealth, days, kids, added


def _texts(a):
    out = []
    for s in a.get("say") or []:
        if isinstance(s, dict) and isinstance(s.get("text"), str):
            out.append(s["text"])
    for v in a.get("votes") or []:
        if isinstance(v, dict):
            out += [x for x in (v.get("reason"), v.get("against")) if isinstance(x, str) and x]
    p = a.get("proposal") or {}
    if isinstance(p, dict) and isinstance(p.get("text"), str):
        out.append(p["text"])
    if isinstance(a.get("feeling"), str):
        out.append(a["feeling"])
    for v in (a.get("judge") or {}).values() if isinstance(a.get("judge"), dict) else ():
        if isinstance(v, str):
            out.append(v)
    return [x for x in out if x and x != "..."]


def _num(x):
    try:
        return float(x)
    except (TypeError, ValueError):
        return 0.0


def read_run(name, path, lo, hi):
    path = Path(path)
    rows = []
    for d in sorted(path.glob("answers/day*/season")):
        day = int(d.parent.name[3:])
        if not lo <= day <= hi:
            continue
        mj = d.parent / "models.json"
        models = (json.loads(mj.read_text(encoding="utf-8")).get("season") or {}) if mj.exists() else {}
        for f in sorted(d.glob("*.json")):
            n = f.stem
            try:
                a = json.loads(f.read_text(encoding="utf-8"))
            except ValueError:
                rows.append({"run": name, "day": day, "name": n, "bad": True})
                continue
            pf = path / "prompts" / f"day{day:03d}" / "season" / f"{n}.md"
            t = pf.read_text(encoding="utf-8") if pf.exists() else ""
            h, disp, wealth, days, kids, added = _prompt_facts(t)
            r = {"run": name, "day": day, "name": n, "model": models.get(n, "?"), "bad": False, "house": h, "store_days": days, "kids": kids,
                 "wealth": wealth.get(h), "poor": (wealth.get(h) or 0) <= 0, "life_shown": added[0], "around_shown": added[1]}
            js = a.get("judge") if isinstance(a.get("judge"), dict) else {}
            r["judges"] = []
            for mid, v in js.items():
                vv = _verdict(v)
                if vv is None or mid not in disp:
                    continue
                frm, ag = disp[mid]
                seat = "言い出した家" if h == frm else "相手の家" if h == ag else "かかわらない家"
                r["judges"].append((mid, seat, vv))
            r["judge_rule"] = _verdict(a.get("judge_rule"))
            r["keep"] = a.get("keep") if isinstance(a.get("keep"), bool) else None
            r["seal"] = a.get("seal") if isinstance(a.get("seal"), bool) else None
            sh = a.get("share")
            r["share"] = bool(sh) and any(_num(n) >= 1 for v in (sh.values() if isinstance(sh, dict) else [sh])
                                          for n in ((v.values() if isinstance(v, dict) else [v])))
            p = a.get("proposal") if isinstance(a.get("proposal"), dict) else {}
            r["proposal"] = bool(p and isinstance(p.get("text"), str) and p["text"].strip() and p["text"] != "...")
            pen = p.get("penalty") if isinstance(p.get("penalty"), dict) else {}
            r["penalty"] = r["proposal"] and _num(pen.get("pay")) > 0
            r["tax"] = r["proposal"] and bool(p.get("tax"))
            vs = [v for v in (a.get("votes") or []) if isinstance(v, dict) and isinstance(v.get("agree"), bool)]
            r["votes"] = {v.get("id"): v["agree"] for v in vs}
            tr = a.get("trade_rule") if isinstance(a.get("trade_rule"), dict) else {}
            tt = a.get("trade") if isinstance(a.get("trade"), dict) else {}
            r["interest"] = _num(tr.get("利子")) > 0 or any(isinstance(v, dict) and _num(v.get("利子")) > 0 for v in tt.values())
            ar = a.get("accept_rule") if isinstance(a.get("accept_rule"), dict) else {}
            r["accept_rule"] = {k: v for k, v in ar.items() if isinstance(v, bool)}
            r["leave"] = a.get("leave") is True
            tx = _texts(a)
            r["text_n"] = len(tx)
            r["kw"] = {k: any(any(w in x for w in ws) for x in tx) for k, ws in KW.items()}
            r["copy"] = any(any(c in x for c in COPY) for x in tx)
            rows.append(r)
    return rows


def arm_of(run):
    return "A0" if run == "H0" else run.split("_")[0]


# ---------------- 数 (答えの束から) ----------------

def rate(rows, f, cond=lambda r: True):
    xs = [f(r) for r in rows if not r["bad"] and cond(r)]
    xs = [x for x in xs if x is not None]
    return (sum(xs) / len(xs), len(xs)) if xs else (None, 0)


def judge_rate(rows, seat=None):
    xs = [vv == "つぐなう" for r in rows if not r["bad"] for (_, s, vv) in r["judges"] if seat is None or s == seat]
    return (sum(xs) / len(xs), len(xs)) if xs else (None, 0)


def agreement(rows):
    """集まりごとに、答えの欄 (keep・judge_rule・票ごと・受け入れの方針ごと) で、いちばん多い答えを選んだ人の割合の平均 (H4)"""
    by = defaultdict(list)
    for r in rows:
        if not r["bad"]:
            by[(r["run"], r["day"])].append(r)
    vals = []
    for rs in by.values():
        fields = defaultdict(list)
        for r in rs:
            if r["keep"] is not None:
                fields["keep"].append(r["keep"])
            fields["judge_rule"].append(r["judge_rule"])
            for k, v in r["votes"].items():
                fields["vote " + str(k)].append(v)
            for k, v in r["accept_rule"].items():
                fields["accept " + k].append(v)
        for xs in fields.values():
            if len(xs) >= 3:
                vals.append(Counter(xs).most_common(1)[0][1] / len(xs))
    return (sum(vals) / len(vals), len(vals)) if vals else (None, 0)


MEASURES = {
    "M1 つぐなう (裁きの答え)": lambda rs: judge_rate(rs),
    "M2 つぐなう: 言い出した家の席": lambda rs: judge_rate(rs, "言い出した家"),
    "M2 つぐなう: かかわらない家の席": lambda rs: judge_rate(rs, "かかわらない家"),
    "M2 つぐなう: 相手の家の席": lambda rs: judge_rate(rs, "相手の家"),
    "M3 裁きの方針がつぐなう": lambda rs: rate(rs, lambda r: (r["judge_rule"] == "つぐなう") if r["judge_rule"] else None),
    "M4 家の倉を持つ (keep true)": lambda rs: rate(rs, lambda r: r["keep"]),
    "M4 keep true: 何も持たない家": lambda rs: rate(rs, lambda r: r["keep"], lambda r: r["poor"]),
    "M4 keep true: 持ち物のある家": lambda rs: rate(rs, lambda r: r["keep"], lambda r: not r["poor"]),
    "M5 分ける (share)": lambda rs: rate(rs, lambda r: r["share"]),
    "M6 罰のある案": lambda rs: rate(rs, lambda r: r["penalty"]),
    "M6 税のある案": lambda rs: rate(rs, lambda r: r["tax"]),
    "M6 掟の案": lambda rs: rate(rs, lambda r: r["proposal"]),
    "M7 票の反対": lambda rs: (lambda xs: (sum(xs) / len(xs), len(xs)) if xs else (None, 0))([not v for r in rs if not r["bad"] for v in r["votes"].values()]),
    "M8 上乗せ (利子 > 0)": lambda rs: rate(rs, lambda r: r["interest"]),
    "M8 受け入れない方針": lambda rs: (lambda xs: (sum(xs) / len(xs), len(xs)) if xs else (None, 0))([not v for r in rs if not r["bad"] for v in r["accept_rule"].values()]),
    "M8 村を出る": lambda rs: rate(rs, lambda r: r["leave"]),
    "M9 答えのそろい (H4)": agreement,
    **{f"T ことば: {k}": (lambda k: lambda rs: rate(rs, lambda r: r["kw"][k] if r["text_n"] else None))(k) for k in KW},
    "T ことば: 足した節の写し": lambda rs: rate(rs, lambda r: r["copy"] if r["text_n"] else None),
    "答えの抜け (読めない JSON)": lambda rs: (lambda xs: (sum(xs) / len(xs), len(xs)) if xs else (None, 0))([r["bad"] for r in rs]),
}


def seat_gap(rs):
    a, na = judge_rate(rs, "言い出した家")
    b, nb = judge_rate(rs, "かかわらない家")
    return (a - b, min(na, nb)) if a is not None and b is not None else (None, 0)


def keep_gap(rs):
    a, na = rate(rs, lambda r: r["keep"], lambda r: not r["poor"])
    b, nb = rate(rs, lambda r: r["keep"], lambda r: r["poor"])
    return (a - b, min(na, nb)) if a is not None and b is not None else (None, 0)


def boot(rows, fn, n, rng):
    """集まり (走り・日) を単位に引き直した 95% 区間"""
    by = defaultdict(list)
    for r in rows:
        by[(r["run"], r["day"])].append(r)
    keys = sorted(by)
    if not keys:
        return (None, None)
    vals = []
    for _ in range(n):
        rs = [r for k in (keys[rng.randrange(len(keys))] for _ in keys) for r in by[k]]
        v = fn(rs)[0]
        if v is not None:
            vals.append(v)
    if len(vals) < n * 0.5:
        return (None, None)
    vals.sort()
    return (vals[int(0.025 * len(vals))], vals[int(0.975 * len(vals)) - 1])


def boot_diff(r1, r2, fn, n, rng):
    """2 つの組の差 (r1 − r2) の 95% 区間 (組ごとに集まりを引き直す)"""
    def by(rows):
        d = defaultdict(list)
        for r in rows:
            d[(r["run"], r["day"])].append(r)
        return d
    b1, b2 = by(r1), by(r2)
    k1, k2 = sorted(b1), sorted(b2)
    if not k1 or not k2:
        return (None, None)
    vals = []
    for _ in range(n):
        x = fn([r for k in (k1[rng.randrange(len(k1))] for _ in k1) for r in b1[k]])[0]
        y = fn([r for k in (k2[rng.randrange(len(k2))] for _ in k2) for r in b2[k]])[0]
        if x is not None and y is not None:
            vals.append(x - y)
    if len(vals) < n * 0.5:
        return (None, None)
    vals.sort()
    return (vals[int(0.025 * len(vals))], vals[int(0.975 * len(vals)) - 1])


def scarce(r):
    return r["store_days"] is not None and r["store_days"] < SCARCE


def plenty(r):
    return r["store_days"] is not None and r["store_days"] >= PLENTY


def cond_gap(rs):
    """H5: 蓄えが少ない集まりと多い集まりの、keep true の差 (少ない − 多い)"""
    a, na = rate(rs, lambda r: r["keep"], scarce)
    b, nb = rate(rs, lambda r: r["keep"], plenty)
    return (a - b, min(na, nb)) if a is not None and b is not None else (None, 0)


# ---------------- 決め (前もって決めた線。prereg 6.) ----------------

def decide(arms, n, rng):
    out = []
    ctrl = arms.get("A0", [])
    runs0 = sorted({r["run"] for r in ctrl})

    def ctrl_spread(fn):
        """くらべる組の 2 つの走り (A0 の写しと H0) の差の大きさ (どちらかがなければ None)"""
        if len(runs0) < 2:
            return None
        vs = [fn([r for r in ctrl if r["run"] == x])[0] for x in runs0[:2]]
        return abs(vs[0] - vs[1]) if None not in vs else None

    def judge(hid, what, fn, arm, base, sign, line, min_n=10):
        r1, r0 = arms.get(arm, []), arms.get(base, [])
        if not r1 or not r0:
            out.append((hid, f"{arm} − {base}", what, "-", "-", "組がない")); return
        v1, n1 = fn(r1)
        v0, n0 = fn(r0)
        if v1 is None or v0 is None or min(n1, n0) < min_n:
            out.append((hid, f"{arm} − {base}", what, f"{v1} / {v0}", f"n {n1} / {n0}", "判定できない (数が少ない)")); return
        d = v1 - v0
        lo, hi = boot_diff(r1, r0, fn, n, rng)
        sp = ctrl_spread(fn) if base == "A0" else None
        ok = (sign * d >= line) and lo is not None and (lo > 0 if sign > 0 else hi < 0)
        noisy = sp is not None and sp >= abs(d)
        res = "判定できない (くらべる組どうしのゆれ以下)" if ok and noisy else "支持" if ok else "支持しない"
        out.append((hid, f"{arm} − {base}", what, f"{d:+.3f}", f"[{lo:+.3f}, {hi:+.3f}]" if lo is not None else "-",
                    res + (f" (くらべる組のゆれ {sp:.3f})" if sp is not None else "")))

    # 暮らしの節がある組 (A1 と A2) をまとめた「L」で、H1・H3・H4・H5 を決める (どちらか一方しかなければ、その組だけ)
    for arm in ("L",):
        judge("H1", "席の差 (言い出した家 − かかわらない家) のつぐなう", seat_gap, arm, "A0", +1, 0.15, min_n=8)
        judge("H3", "持ち物の差 (ある家 − 何も持たない家) の keep true", keep_gap, arm, "A0", +1, 0.15, min_n=8)
        judge("H4", "答えのそろい", agreement, arm, "A0", -1, 0.05, min_n=5)
        judge("H5", "蓄えの少ない集まり − 多い集まり の keep true", cond_gap, arm, "A0", +1, 0.10, min_n=8)
    judge("H2", "keep true", lambda rs: rate(rs, lambda r: r["keep"]), "A2", "A1", +1, 0.10)
    judge("H2b", "罰か税のある案 (どちらの向きでも書く)", lambda rs: rate(rs, lambda r: r["penalty"] or r["tax"]), "A2", "A1", +1, 0.0)
    return out


def world_rows(name, path, lo, hi):
    path = Path(path)
    out = {"run": name}
    st = path / "state.json"
    if st.exists():
        s = json.loads(st.read_text(encoding="utf-8"))
        ds = [d for d in (s["era2"].get("g5") or {}).get("disputes", []) if lo <= d["day"] <= hi]
        out["disputes"] = len(ds)
        for k in ("倉", "蓄え", "刈る", "ヤギ"):
            out[f"disputes_{k}"] = sum(d["kind"] == k for d in ds)
        out["つぐなう"] = sum(d.get("verdict") == "つぐなう" for d in ds)
        out["paid"] = sum((d.get("paid") or 0) > 0 for d in ds)
        out["left_disputes"] = sum(d.get("status") == "去った" for d in ds)
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
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--run", action="append", required=True, help="名前=データの置き場所 (H0=sim/society/data、A2_1=sim/society/data_E3_A2_1 など)")
    ap.add_argument("--from", dest="lo", type=int, default=12599)
    ap.add_argument("--to", dest="hi", type=int, default=12958)
    ap.add_argument("--boot", type=int, default=2000)
    ap.add_argument("--out", default=None, help="CSV と summary.md を書く場所 (なければ表示だけ)")
    a = ap.parse_args()
    rng = random.Random(SEED)
    rows, worlds = [], []
    for x in a.run:
        name, path = x.split("=", 1)
        rows += read_run(name, path, a.lo, a.hi)
        worlds.append(world_rows(name, path, a.lo, a.hi))
    arms = defaultdict(list)
    for r in rows:
        arms[arm_of(r["run"])].append(r)
    for r in rows:
        if arm_of(r["run"]) in ("A1", "A2"):
            arms["L"].append(r)
    lines = [f"# 実験 3 の数 ({a.lo}〜{a.hi} 日目の集まり)", "",
             "走り: " + "、".join(f"{k} (集まり {len({r['day'] for r in v})}・答え {len(v)})" for k, v in sorted(
                 {run: [r for r in rows if r["run"] == run] for run in {r["run"] for r in rows}}.items())), "",
             "| 数 | " + " | ".join(sorted(arms)) + " |", "|---|" + "---|" * len(arms)]
    for m, fn in MEASURES.items():
        cells = []
        for k in sorted(arms):
            v, n = fn(arms[k])
            cells.append("-" if v is None else f"{v:.3f} (n {n})")
        lines.append(f"| {m} | " + " | ".join(cells) + " |")
    lines += ["", "## 仮説の決め (prereg 6.)", "", "| 仮説 | くらべ | 数 | 差 | 95% 区間 | 判定 |", "|---|---|---|---|---|---|"]
    for row in decide(arms, a.boot, rng):
        lines.append("| " + " | ".join(str(x) for x in row) + " |")
    lines += ["", "## 世界の数 (探索)", "", "| " + " | ".join(worlds[0].keys()) + " |" if worlds else ""]
    if worlds:
        keys = sorted({k for w in worlds for k in w}, key=lambda k: (k != "run", k))
        lines[-1] = "| " + " | ".join(keys) + " |"
        lines.append("|" + "---|" * len(keys))
        for w in worlds:
            lines.append("| " + " | ".join(str(w.get(k, "-")) for k in keys) + " |")
    text = "\n".join(lines) + "\n"
    print(text)
    if a.out:
        o = Path(a.out)
        o.mkdir(parents=True, exist_ok=True)
        (o / "summary.md").write_text(text, encoding="utf-8")
        with open(o / "answers.csv", "w", newline="", encoding="utf-8") as f:
            w = csv.writer(f)
            w.writerow(["run", "day", "name", "model", "house", "poor", "kids", "store_days", "life_shown", "around_shown", "judges", "judge_rule", "keep",
                        "seal", "share", "proposal", "penalty", "tax", "votes_against", "interest", "accept_false", "leave", "copy"] + list(KW))
            for r in rows:
                if r["bad"]:
                    continue
                w.writerow([r["run"], r["day"], r["name"], r["model"], r["house"], r["poor"], r["kids"], r["store_days"], r["life_shown"], r["around_shown"],
                            ";".join(f"{m}:{s}:{v}" for m, s, v in r["judges"]), r["judge_rule"], r["keep"], r["seal"], r["share"], r["proposal"],
                            r["penalty"], r["tax"], sum(not v for v in r["votes"].values()), r["interest"],
                            sum(not v for v in r["accept_rule"].values()), r["leave"], r["copy"]] + [r["kw"][k] for k in KW])


if __name__ == "__main__":
    main()
