#!/usr/bin/env python3
"""川辺の村の統計のページ (国の統計の形) を作る。sim/society/app/stats.html (1 つのファイル。CSS・JS・データを中に入れる。外のものを読まない)。

設計: docs/society_phase/dashboard_official_design.md。計算: tools/stats_calc.py (年報のダッシュボードと同じ)。数の定義: tools/stats_indicators.json。
data/ は読むだけ (何も書かない)。年に 1 回、年報を作るときに作り直す (本人の決め「年報だけ、年に 1 回」)。

使い方:
  python3 sim/society/tools/build_stats.py [--data sim/society/data] [--out sim/society/app/stats.html] [--no-scan]
    --no-scan  よその村の申し出の文 (archive/events_*.jsonl。約 0.8 GB) を読まない (交換の割合の読みとりを作らない)

記憶: state.json は 1 回だけ読み、統計に使う行だけ残して手放す (stats_calc.Ctx.slim)。archive の出来事は 1 行ずつ文字で探す。
テクノロジーの数は、季節ごとに作り直している app/tech_tree.html に埋めてある中身を読む (btt.build は大きいので呼ばない)。
"""
import argparse
import collections
import gc
import json
import os
import re
import resource
import subprocess
import sys
import time
from pathlib import Path

HERE = os.path.dirname(os.path.abspath(__file__))
SOC = os.path.dirname(HERE)
sys.path.insert(0, SOC)
sys.path.insert(0, HERE)
import stats_calc as SC  # noqa: E402

PROTECTED = os.path.realpath(os.path.join(SOC, "data"))
YEAR = SC.YEAR
TEMPLATE = os.path.join(HERE, "stats_page.html")
OFFER = re.compile(r"(?:が、|が)(?:また)?村に来た。(.+?) を出すので、(.+?) がほしい")
ITEM = re.compile(r"(\S+?) ([\d,]+) (\S+)")


def _items(s):
    out = []
    for part in s.split("・"):
        m = ITEM.match(part.strip())
        if m:
            out.append([m.group(1), int(m.group(2).replace(",", "")), m.group(3)])
    return out


def scan_offers(data, upto, now_events):
    """よその村の申し出の文 (読みとり)。年 → [[出す物], [ほしい物]] の数と、よくある形"""
    by = collections.defaultdict(list)
    files = sorted(Path(data, "archive").glob("events_*.jsonl"))
    for p in files:
        try:
            r = subprocess.run(["grep", "-h", "がほしい", str(p)], capture_output=True, text=True, timeout=120)
        except (OSError, subprocess.TimeoutExpired):
            continue
        for line in r.stdout.splitlines():
            try:
                x = json.loads(line)
            except json.JSONDecodeError:
                continue
            m = OFFER.search(x.get("text") or "")
            if m:
                by[x["day"] // YEAR].append((_items(m.group(1)), _items(m.group(2))))
    for x in now_events:
        m = OFFER.search(x.get("text") or "")
        if m and (upto is None or x["day"] // YEAR > upto):
            by[x["day"] // YEAR].append((_items(m.group(1)), _items(m.group(2))))
    out = {}
    for y, L in sorted(by.items()):
        goat = []  # ヤギだけを出す申し出: ヤギ 1 頭あたりに求めた物
        for give, want in L:
            if len(give) == 1 and give[0][0] == "ヤギ" and give[0][1] > 0:
                n = give[0][1]
                goat.append({w[0]: round(w[1] / n, 1) for w in want})
        keys = collections.Counter(k for g in goat for k in g)
        avg = {k: round(sum(g.get(k, 0) for g in goat) / len(goat), 1) for k in keys} if goat else None
        ex = collections.Counter(json.dumps([g, w], ensure_ascii=False) for g, w in L).most_common(1)[0][0]
        out[y] = {"n": len(L), "goat_n": len(goat), "per_goat": avg, "example": json.loads(ex)}
    return out


def tech_data(rows):
    """テクノロジーの節: tech_tree.html の中身 + 「あとで届いた」 + Society 3.0 の列 (記録の数から)"""
    p = Path(SOC) / "app" / "tech_tree.html"
    m = re.search(r'<script type="application/json" id="tt-data">(.*?)</script>', p.read_text(encoding="utf-8"), re.S)
    tt = json.loads(m.group(1).replace("<\\/", "</"))
    ys = sorted(rows)

    def first(fn):
        return next((y for y in ys if fn(rows[y])), None)

    later = {  # 木では「届かなかった」(G の窓の中だけで見る) が、あとで記録の数に出たもの
        "灌漑": (first(lambda r: (r.get("canal_days") or 0) > 0), "水の道を掘った人日が出た年"),
        "文字": (first(lambda r: (r.get("readers") or 0) > 0), "読める大人を数えた年 (読める人がいる)"),
        "教え": (first(lambda r: (r.get("kids_taught") or 0) > 0), "手習いの子が出た年 (学校ではない)"),
    }
    techs = []
    for t in tt["techs"]:
        st = t["status"]
        lt = later.get(t["name"])
        d = {"id": t["id"], "name": t["name"], "tree": t["tree"], "era": t.get("era"), "status": st, "does": t.get("does"),
             "first_day": (t.get("first") or {}).get("day"), "timing": t.get("timing"), "emerged": bool(t.get("emerged"))}
        if st == "届かなかった" and lt and lt[0] is not None:
            d["status"] = "あとで届いた"
            d["later_year"], d["later_why"] = lt
        techs.append(d)
    s3 = [  # Society 3.0 の列 (予定の木にまだない列。記録の数から)
        ("水の作業場の持ち場", "社会制度", "posts", "持ち場 (のこ番など) についた人が出た年", lambda r: (r.get("posts") or 0) > 0),
        ("燃える石の掘り場", "テクノロジー", "coal_dug", "燃える石を掘った年", lambda r: (r.get("coal_dug") or 0) > 0),
        ("読み書きと知らせ板", "テクノロジー", "literacy", "i4 の行で読める大人を数えた年", lambda r: r.get("literacy_src") == "i4"),
        ("手習い", "社会制度", "kids_taught", "手習いの子が出た年", lambda r: (r.get("kids_taught") or 0) > 0),
        ("頼み書き", "社会制度", "for_others", "頼み書きを果たした年 (p4 の行の done)。フェーズ 4 は 0 件のまま閉じた", lambda r: (r.get("p4_done") or 0) > 0),
        ("町の鎌 (町の頼み)", "テクノロジー", "town_done", "町の頼みを果たした年", lambda r: (r.get("town_done") or 0) > 0),
    ]
    col = []
    for name, tree, ind, why, fn in s3:
        y = next((yy for yy in ys if yy >= SC.S3_FIRST and fn(rows[yy])), None)
        col.append({"name": name, "tree": tree, "indicator": ind, "status": "届いた" if y else ("届かなかった" if name == "頼み書き" else "まだ"), "year": y, "why": why})
    firsts = collections.Counter(f["day"] // YEAR for f in tt["firsts"])
    return {"asof": tt["asof"], "counts": tt["counts"], "techs": techs, "s3": col, "firsts_by_year": dict(firsts),
            "emerged": [{"name": x["name"], "day": x["day"], "kind": x.get("kind"), "tech": x.get("tech")} for x in tt["emerged"]],
            "eras": [{"id": x["id"], "name": x["name"], "start": x["start"], "end": x.get("end")} for x in tt["eras"]]}


def hunger_by_year(data, years):
    """season_person/ を 1 年ずつ読み、季節の終わりに空腹だった人の割合 (4 季節の平均)"""
    out = {}
    for y in years:
        p = Path(data, "records", "season_person", f"season_person_{y:04d}.jsonl")
        if not p.exists():
            continue
        n = collections.Counter()
        h = collections.Counter()
        with open(p, encoding="utf-8") as fh:
            for line in fh:
                try:
                    r = json.loads(line)
                except json.JSONDecodeError:
                    continue
                if r.get("status_at_end") != "生きている":
                    continue
                n[r["season_end_day"]] += 1
                if (r.get("hunger") or 0) > 0:
                    h[r["season_end_day"]] += 1
        sh = [h[d] / n[d] for d in n if n[d]]
        if sh:
            out[y] = sum(sh) / len(sh)
    return out


# ---------------------------------------------------------------- 構成比の中の中身 (2026-11-22 本人の言葉: 切れを押すと、その種類のうつりかわりと、その中身の円)
# 円の 1 切れ (仕事の「物を作る」・食べ物の「そのほか」・死因の「病」など) の中身を、ここで前もって作る (ページでは計算しない)。
# tree[key][part] = {"kind": nominal|ordinal, "kids": [中身の名前 (235 年を通して大きい順。順のあるものは順のまま)]}
# 年ごとの量は years[y]["ck"][key][part] = [kids と同じ順の量]
AGE_KIDS = {"0〜14 歳": [("0〜4 歳", 0, 1), ("5〜9 歳", 1, 2), ("10〜14 歳", 2, 3)],
            "15〜54 歳": [("15〜24 歳", 3, 5), ("25〜34 歳", 5, 7), ("35〜44 歳", 7, 9), ("45〜54 歳", 9, 11)],
            "55 歳〜": [("55〜64 歳", 11, 13), ("65〜74 歳", 13, 15), ("75 歳〜", 15, 17)]}
HH_KIDS = {"3〜4 人": [("3 人", 3, 3), ("4 人", 4, 4)], "5〜9 人": [(f"{k} 人", k, k) for k in range(5, 10)],
           "10 人〜": [("10〜14 人", 10, 14), ("15〜19 人", 15, 19), ("20〜29 人", 20, 29), ("30〜49 人", 30, 49), ("50 人〜", 50, 10 ** 6)]}
DEATH_AGES = [("0〜4 歳", 0, 4), ("5〜14 歳", 5, 14), ("15〜29 歳", 15, 29), ("30〜44 歳", 30, 44), ("45 歳〜", 45, 10 ** 6)]  # 死んだときの歳 (村の年)


def compo_kids(ctx, y, r):
    """1 年の、切れの中身の量。{key: {part: {中身: 量}}} (順はあとで tree で決める)"""
    out = collections.defaultdict(dict)
    py = r.get("pyramid")
    if py:
        for part, L in AGE_KIDS.items():
            out["age"][part] = {n: sum(c[i] for c in py.values() for i in range(a, b)) for n, a, b in L}
    hs = {int(k): v for k, v in (r.get("hh_sizes") or {}).items()}
    if hs:
        for part, L in HH_KIDS.items():
            out["hh"][part] = {n: sum(v for k, v in hs.items() if a <= k <= b) for n, a, b in L}
    J = r.get("jobs") or {}
    if J:
        for k, v in J.items():
            if k in SC.REST:
                continue
            part = SC.WORK_GROUP.get(k) or ("物を作る" if k in SC.MAKE_JOBS else "そのほか")
            out["work"].setdefault(part, {})[k] = v
    for k, v in (r.get("food_items") or {}).items():
        out["food"].setdefault(SC.FOOD_GROUP.get(k, "そのほか"), {})[k] = v
    deaths = [d for s in ctx.srows(y) for d in (s.get("deaths") or [])]
    if deaths:
        for d in deaths:
            c = d.get("cause") or "その他"
            if c in ("子", "病"):
                p = ctx.people.get(d.get("id")) or {}
                age = p.get("age_at_death")
                if age is None and p.get("born_day") is not None and p.get("died_day") is not None:
                    age = (p["died_day"] - p["born_day"]) // YEAR
                n = next((n for n, a, b in DEATH_AGES if age is not None and a <= age <= b), "歳が分からない")
                out["causes"].setdefault(c, collections.Counter())[n] += 1
            else:
                out["causes"].setdefault("年・そのほか", collections.Counter())[c] += 1
    return out


def compo_tree(kids_by_year):
    """中身の順と種類 (ordinal は順のまま、nominal は 235 年の合計の大きい順)"""
    order = {"age": {p: [n for n, _, _ in L] for p, L in AGE_KIDS.items()}, "hh": {p: [n for n, _, _ in L] for p, L in HH_KIDS.items()},
             "causes": {"子": [n for n, _, _ in DEATH_AGES] + ["歳が分からない"], "病": [n for n, _, _ in DEATH_AGES] + ["歳が分からない"]}}
    tot = collections.defaultdict(collections.Counter)
    for ck in kids_by_year.values():
        for key, parts in ck.items():
            for part, d in parts.items():
                for n, v in d.items():
                    tot[(key, part)][n] += v
    tree = collections.defaultdict(dict)
    for (key, part), c in tot.items():
        if key in order and part in order[key]:
            kids = [n for n in order[key][part] if c.get(n)]
            tree[key][part] = {"kind": "ordinal", "kids": kids}
        else:
            kids = [n for n, _ in sorted(c.items(), key=lambda t: (t[0] in ("その他", "そのほか"), -t[1], t[0])) if c[n]]
            tree[key][part] = {"kind": "nominal", "kids": kids}
    return tree


def _r(v):
    if isinstance(v, float):
        return round(v, 4)
    if isinstance(v, dict):
        return {k: _r(x) for k, x in v.items()}
    if isinstance(v, list):
        return [_r(x) for x in v]
    return v


def build(data, scan=True):
    t0 = time.time()
    ctx = SC.Ctx(data)
    ctx.slim()  # state.json を読み、統計の行だけ残して手放す
    gc.collect()
    upto = ctx._cache.get("archive_upto")
    era_log = ctx._cache.get("era_log")
    now = ctx.now
    last = now // YEAR if now % YEAR == YEAR - 1 else now // YEAR - 1  # 終わった年まで
    years = list(range(SC.S2_FIRST, last + 1))
    rows = {}
    for y in years:
        rows[y] = SC.year_row(ctx, y)
    hun = hunger_by_year(data, years)
    for y, v in hun.items():
        rows[y]["hunger"] = v
    for y in years:  # 平均の線 (5 年)
        win = [rows[yy] for yy in range(ctx.win0(y), y + 1) if yy in rows]  # 2026-11-22: 区切り (stats_calc.BREAKS) の前の年と混ぜない
        b = sum(r.get("births") or 0 for r in win)
        d = sum(r.get("deaths") or 0 for r in win)
        p = sum(r.get("pop") or 0 for r in win)
        rows[y]["cbr5"] = 1000 * b / p if p else None
        rows[y]["cdr5"] = 1000 * d / p if p else None
    kids = {y: compo_kids(ctx, y, rows[y]) for y in years}  # 円の切れの中身 (押すと出る)
    tree = compo_tree(kids)
    for y in years:
        rows[y]["ck"] = {key: {part: [d.get(n, 0) for n in tree[key][part]["kids"]] for part, d in parts.items() if part in tree[key]}
                         for key, parts in kids[y].items()}
    s1 = SC.s1_rows(ctx)
    seasons = [[r["season_end_day"], r.get("population"), r.get("store_days"),
                round(((r.get("accounts") or {}).get("identity") or {}).get("net_product", 0) / SC.UNIT, 2) if r.get("accounts") else None]
               for y in sorted(ctx.seasons) for r in ctx.srows(y)]
    bad, n, mine = SC.check(ctx, os.path.join(SOC, "reports"))
    offers = scan_offers(data, upto, ctx._cache.get("live_offers") or []) if scan else {}
    tech = tech_data(rows)
    reports = sorted(int(re.findall(r"\d+", p.name)[0]) for p in Path(SOC, "reports").glob("year*.html"))
    defs = SC.defs()
    marks = {"d1"} if ctx.breaks() else set()  # 2026-11-22: 印のある区切りだけ図に点線を出す (breaks の "when")
    defs["breaks"] = [b for b in defs.get("breaks", []) if b.get("when") is None or b["when"] in marks]
    D = {"asof": {"day": now, "label": f"{now // YEAR}年{now % YEAR + 1}日目", "last_year": last, "built": time.strftime("%Y-%m-%d")},
         "defs": defs, "compo": SC.COMPO, "compo_tree": tree, "years": {str(y): _r(r) for y, r in rows.items()}, "s1": _r(s1), "seasons": seasons, "era_log": era_log,
         "tech": tech, "offers": {str(k): v for k, v in offers.items()}, "check": {"n": n, "bad": _r(bad), "ref_calc": _r(mine)}, "reports": reports}
    print(f"統計: {years[0]}〜{last}年 {len(years)} 年・Society 1.0 の季節 {len(s1)}・照らし合わせ {n} (ちがう {len(bad)})・{time.time() - t0:.0f} 秒・"
          f"記憶のいちばん多い所 {resource.getrusage(resource.RUSAGE_SELF).ru_maxrss // 1024} MB", file=sys.stderr)
    return D


def page(D):
    tpl = Path(TEMPLATE).read_text(encoding="utf-8")
    js = json.dumps(D, ensure_ascii=False, separators=(",", ":")).replace("</", "<\\/")
    assert tpl.count("/*DATA*/") == 1
    return tpl.replace("/*DATA*/", js)


def main(argv=None):
    ap = argparse.ArgumentParser(description="村の統計のページを作る (読むだけ)")
    ap.add_argument("--data", default=os.path.join(SOC, "data"))
    ap.add_argument("--out", default=os.path.join(SOC, "app", "stats.html"))
    ap.add_argument("--json", help="データだけを JSON で書く (試し用)")
    ap.add_argument("--no-scan", action="store_true")
    a = ap.parse_args(argv)
    for p in (a.out, a.json):
        if p and (os.path.realpath(p) == PROTECTED or os.path.realpath(p).startswith(PROTECTED + os.sep)):
            sys.exit("sim/society/data/ の下には書かない")
    D = build(a.data, scan=not a.no_scan)
    if a.json:
        Path(a.json).write_text(json.dumps(D, ensure_ascii=False), encoding="utf-8")
    html = page(D)
    Path(a.out).write_text(html, encoding="utf-8")
    print(f"{a.out} を書いた ({len(html.encode('utf-8')) // 1024} KB)")


if __name__ == "__main__":
    main()
