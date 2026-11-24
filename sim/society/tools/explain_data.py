#!/usr/bin/env python3
"""解説の係 (年報のダッシュボードと統計のページを、本人にやさしく説明する係) のための道具。

2 つの使い方:
  1) 数を集める (係が読む小さな JSON)
     python3.13 sim/society/tools/explain_data.py --year 250 [--out /tmp/explain_data_250.json]
       年報のダッシュボードと統計のページの数 (tools/stats_calc.py と tools/year_report.py と同じ計算) を 1 つの JSON にまとめる。
       中身: 見出しの数・その年と去年の数・12 年のうつりかわり・季節ごとの種まきと蓄え・D1 と T5 の行・はじめて届いた技術・大きな出来事・
       図の一覧 (どの係の図か・図の決まりの印 sig・去年の「図の見かた」)・大きな年か (動画を作る年か)・案内役の名前。
       既定の出力は /tmp/explain_data_<年>.json。記憶は 1 GB ほど (state.json を 1 回読む)。

  2) 出す (事実の確かめのあと)
     python3.13 sim/society/tools/explain_data.py --year 250 --publish /tmp/explain_draft_250.json
       係の文 (下書き) の形を確かめ、文の中の数がみな、集めた数 (1) にあるかを確かめる。
       ない数があれば書かずに止まる (終わりの値 1。どの文のどの数かを出す)。そろえば sim/society/reports/explain/year<年>.json を書く。
       「図の見かた」は、図の決まり (sig) が去年と同じなら、去年の文をそのまま使う (図が変わったときだけ変わる)。

ワークフロー: sim/society/tools/explainer_workflow.js (4 つの分野の係 → まとめ役 → 事実の確かめ)。HANDOFF.md の「解説の係」。
data/ は読むだけ (何も書かない)。
"""
import argparse
import hashlib
import json
import os
import re
import resource
import sys
from pathlib import Path

HERE = os.path.dirname(os.path.abspath(__file__))
SOC = os.path.dirname(HERE)
sys.path.insert(0, SOC)
sys.path.insert(0, HERE)

EXPLAIN_DIR = os.path.join(SOC, "reports", "explain")
GUIDE_DIR = os.path.join(SOC, "app", "guide")
PROTECTED = os.path.realpath(os.path.join(SOC, "data"))
EXPRS = ("neutral", "smile", "concern", "surprise")
TEAMS = {"pop": "人口の係", "life": "くらし・食べ物の係", "know": "知恵・技術の係", "out": "よその村・町の係"}
PLACEHOLDER_NAME = "案内の村人 (仮)"

# 図の一覧。id → (どこ, 係, 統計のページの分野, 図の名前, 図の決まり (変わったら sig が変わり、「図の見かた」を書き直す))
# where: report = 年報のダッシュボード / stats = 統計のページの分野のカード / tile = 年報の数のタイル (「図の見かた」はつけない。吹き出しだけ)
CHARTS = {
    "k_pop": ("tile", "pop", "pop", "人口 (年の終わり) のタイル", "年の終わりの人数と去年からの差"),
    "k_gdp": ("tile", "life", "econ", "村の生産のタイル", "大人 1 年分の食べ物に直した村の生産と去年からの %"),
    "k_store": ("tile", "life", "food", "蓄え (いちばん少ない日) のタイル", "1 年でいちばん少なかった日の蓄え (日分)"),
    "k_nonfood": ("tile", "life", "work", "食べ物でない仕事のタイル", "働いた日のうち畑・ヤギ以外の割合 (ポイント差)"),
    "k_lit": ("tile", "know", "edu", "読める大人のタイル", "大人のうち字が読める人の割合"),
    "k_imr": ("tile", "pop", "health", "乳児死亡率のタイル", "出生千あたりの 1 歳前の死亡 (5 年の平均)"),
    "k_famine": ("tile", "life", "food", "ききんのタイル", "村の蓄えが尽きた回数"),
    "t_pop": ("report", "pop", "pop", "人 (うつりかわり)", "12 年の線。年の終わりの人数。下は 0 から始まらない。めやすは横の実線、縦の点線は決まりを直した区切りの年 (242年)"),
    "t_gdp": ("report", "life", "econ", "村の生産 (うつりかわり)", "12 年の線。大人 1 年分。食べ物・土器と鎌・ヤギ・住まいの合計。種と損と割れた分を引く。下は 0 から始まらない。めやすは横の実線、縦の点線は決まりを直した区切りの年 (242年)"),
    "t_store": ("report", "life", "food", "蓄え (うつりかわり)", "12 年の線。1 年でいちばん少なかった日 (日分)。めやすの線 120 日分。めやすは横の実線、縦の点線は決まりを直した区切りの年 (242年)"),
    "t_lit": ("report", "know", "edu", "読める大人 (うつりかわり)", "12 年の線。大人のうち字が読める人 (%)。めやすの線 25%。めやすは横の実線、縦の点線は決まりを直した区切りの年 (242年)"),
    "t_nonfood": ("report", "life", "work", "食べ物でない仕事 (うつりかわり)", "12 年の線。燃える石・板・字など (%)。めやすの線 22%。めやすは横の実線、縦の点線は決まりを直した区切りの年 (242年)"),
    "c_age": ("report", "pop", "pop", "年齢 3 区分の人口 (円と帯)", "円: 0〜14 歳・15〜54 歳・55 歳〜 の割合 (年の終わり)。下の帯: 12 年の割合のうつりかわり"),
    "c_work": ("report", "life", "work", "仕事の種類別の人日 (円と帯)", "円: 畑仕事・狩り・採集・物を作る・水の道を掘る・ヤギの世話・そのほか の人日の割合 (休む日はのぞく)。下の帯: 12 年"),
    "c_food": ("report", "life", "food", "食べ物の生産 (円と帯)", "円: 草の種・木の実・乳・肉と魚・そのほか の熱量の割合。下の帯: 12 年"),
    "phase": ("report", None, None, "いまのフェーズの物差し", None),  # 係と中身はその年のフェーズで決まる (phase_chart)
    "f_pop": ("stats", "pop", "pop", "人口と世帯 (統計のページ)", "総人口・世帯・村の帳の人数のタイルと、総人口の線・年齢の円"),
    "f_vital": ("stats", "pop", "vital", "出生と死亡 (統計のページ)", "出生・死亡・平均寿命 (5 年)・合計特殊出生率 (5 年) と死因の円"),
    "f_health": ("stats", "pop", "health", "健康 (統計のページ)", "乳児死亡率・5 歳までの死亡率・病で亡くなった人・手当てが届いた子"),
    "f_econ": ("stats", "life", "econ", "経済 (統計のページ)", "村の生産・1 人あたり・成長率と、生産面と支出面の棒"),
    "f_work": ("stats", "life", "work", "仕事 (統計のページ)", "働いた人日・食べ物の仕事の割合・休んだ日と、仕事の円"),
    "f_food": ("stats", "life", "food", "農業と食べ物 (統計のページ)", "刈った草の種・1 人 1 日食べた熱量・蓄えと、食べ物の円・食料需給表"),
    "f_living": ("stats", "life", "living", "暮らしと差 (統計のページ)", "持ち物の差 (ジニ係数)・倉を持つ家の差・雨の夜に外にいた人"),
    "f_rules": ("stats", "life", "rules", "村の決まり (統計のページ)", "生きている掟・新しいもめごと"),
    "f_edu": ("stats", "know", "edu", "教育 (統計のページ)", "読める大人・手習いの子と、読める大人の帯"),
    "f_env": ("stats", "know", "env", "環境とエネルギー (統計のページ)", "燃やした燃える石・水の道を掘った人日"),
    "f_ext": ("stats", "out", "ext", "外とのつながり (統計のページ)", "よそから入った草の種・相手の村・果たした町の頼みと、出し入れ"),
    "f_price": ("stats", "out", "price", "物の値うち (統計のページ)", "よその村の申し出の文から読みとった交換の割合"),
}
PHASE_TEAM = {"d1": "pop", "t5": "out", "p4": "out", "i4": "know"}
PHASE_SPEC = {"d1": ("人口の決まりの直し (案 A) の物差し", "d1 平均寿命・d2 15 歳の平均余命・d3 自然増加・d4 合計特殊出生率 (線の中なら ○)・d5 蓄え (守り)。下に数の札"),
              "t5": ("フェーズ 5 (川下の町と鉄の道具) の物差し", "t1 果たした町の頼み・t2 よそのために働いた家・t3 食べ物でない仕事・t4 暮らしを守る (・h1 手当てが届いた子)。棒はめやすまでどこまで来たか"),
              "p4": ("フェーズ 4 (頼み書きと町) の物差し", "p1 果たした頼み・p2 よその家のために働いた家・p3 食べ物でない仕事・p4 暮らしを守る"),
              "i4": ("フェーズ 3 (読み書きと知らせ板) の物差し", "i1 読める大人・i2 知らせ板・i3 字の仕事・i4 暮らしを守る")}
FIELD_OF_STATS = {v[2]: k for k, v in CHARTS.items() if v[0] == "stats"}


def sig_of(title, spec):
    return hashlib.sha1(f"{title}|{spec}".encode("utf-8")).hexdigest()[:10]


def chart_list(phase_key):
    out = {}
    for cid, (where, team, field, title, spec) in CHARTS.items():
        if cid == "phase":
            if not phase_key:
                continue
            title, spec = PHASE_SPEC[phase_key]
            team, field = PHASE_TEAM[phase_key], {"d1": "vital", "t5": "ext", "p4": "ext", "i4": "edu"}[phase_key]
        out[cid] = {"where": where, "team": team, "field": field, "title": title, "spec": spec,
                    "sig": sig_of(title, spec) if where != "tile" else None}
    return out


def guide_info():
    """案内役 (いまの村の人) の名前と絵。app/guide/README.md の「名前:」と「絵:」(ファイル名の頭) で決める。
    絵は app/guide/<絵>_<顔>.png (または guide_<絵>_<顔>.png)。なければ仮の名前と仮の絵。
    app/guide には分野の係の絵 (年報の動画の顔) もあるので、「絵:」がないときは guide_ のついた絵だけを案内役とみなす"""
    g = Path(GUIDE_DIR)
    imgs = {}
    name = stem = None
    if g.is_dir():
        for doc in (g / "README.md", Path(SOC).parents[1] / "docs" / "society_phase" / "guide_character.md"):
            if doc.exists():
                txt = doc.read_text(encoding="utf-8")
                m = re.search(r"(?:名前|name)\s*[:：]\s*\**\s*([^\s*（(、。]+)", txt)
                if m:
                    name = m.group(1)
                    m2 = re.search(r"(?:^|\n)\s*-?\s*絵\s*[:：]\s*`?([A-Za-z0-9_-]+)", txt)
                    stem = m2.group(1) if m2 else None
                    break
        for p in sorted(g.iterdir()):
            m = re.match(r"(guide_)?(.+)_(neutral|smile|concern|surprise)\.(png|webp|jpg|jpeg|svg)$", p.name)
            if not m or (stem and m.group(2) != stem) or (not stem and not m.group(1)):
                continue
            stem = stem or m.group(2)
            if m.group(2) == stem and (m.group(3) not in imgs or p.suffix == ".png"):
                imgs[m.group(3)] = str(p)
    return {"name": name or stem or PLACEHOLDER_NAME, "placeholder": not imgs, "imgs": imgs}


# ---------------------------------------------------------------- 集める

ROW_KEYS = ("pop", "adults", "female", "male", "households", "hh_size", "pop_growth", "births", "deaths", "natural", "joined", "left", "cbr", "cdr",
            "causes", "infant_deaths", "imr", "imr5", "u5mr", "e0", "tfr", "sick_deaths", "injured", "age_young", "age_work", "age_old",
            "gdp", "gdp_parts", "gdp_pc", "gdp_growth", "gdp_full_year", "exp_cons", "exp_stock", "exp_net", "store_min", "store_all", "famine",
            "harvest", "seed", "yield", "goats", "kcal_pc", "self_suff", "supply", "work_days", "rest_share", "work_food", "work_make", "work_other",
            "nonfood", "canal_days", "try_days", "wealth_gini", "house_gini", "store_gini", "store_houses", "homes", "rain_out", "laws", "laws_new",
            "laws_gone", "disputes", "settled", "literacy", "readers", "lit_adults", "kids_taught", "teach_days", "posts", "trade_in", "trade_out_pots",
            "moved", "partners", "known", "debts", "tribute", "town_done", "for_others", "care_kids", "care_saved", "coal_burned", "coal_dug",
            "house_coal", "count_people", "count_ratio")


def _r(v):
    if isinstance(v, float):
        return round(v, 4)
    if isinstance(v, dict):
        return {k: _r(x) for k, x in v.items()}
    if isinstance(v, list):
        return [_r(x) for x in v]
    return v


def _pick(o, keys):
    return {k: _r(o.get(k)) for k in keys if o.get(k) is not None}


def collect(data, y):
    import stats_calc as SC
    import year_report as YR
    D = YR.load(data, y)
    st = D["state"]
    if y * SC.YEAR > st["day"]:
        sys.exit(f"{y}年はまだ始まっていない")
    ctx = YR._sc_ctx(D)
    row = SC.year_row(ctx, y)
    prev = SC.year_row(ctx, y - 1)
    series = YR.dash_series(D, y)
    ser = {k: {str(r["year"]): _r(r.get(k)) for r in series if r.get(k) is not None}
           for k in ("pop", "gdp", "store_min", "literacy", "nonfood", "births", "deaths", "imr5", "famine")}
    ser["gdp"] = {str(r["year"]): _r(r["gdp"]) for r in series if r.get("gdp") is not None and r.get("gdp_full_year")}
    compo = {k: {"this": [[n, _r(v)] for n, v in (row.get("compo") or {}).get(k, [])], "last": [[n, _r(v)] for n, v in (prev.get("compo") or {}).get(k, [])]}
             for k in ("age", "work", "food", "causes", "product", "lit")}
    seasons = [{"season": r.get("season"), "end_day": r["season_end_day"], "pop": r.get("population"), "store_days": r.get("store_days"),
                "seed": (r.get("fields") or {}).get("seed"), "harvested": (r.get("fields") or {}).get("harvested")} for r in ctx.srows(y)]
    g7 = YR._g7(st)
    phase_key = next((k for k in ("d1", "t5", "p4", "i4") if ((g7.get(k) or {}).get("rows") or {}).get(str(y))), None)

    def rows_of(key, keep=None, n=3):
        rr = (g7.get(key) or {}).get("rows") or {}
        ks = [k for k in sorted(rr, key=int) if int(k) <= y][-n:]
        return [{a: _r(b) for a, b in rr[k].items() if not isinstance(b, (list, dict)) and (keep is None or a in keep)} for k in ks]
    d1 = rows_of("d1")
    t5 = rows_of("t5")
    i4 = rows_of("i4", n=2)
    try:
        T = YR.tech_part(data, y)
    except Exception as ex:  # noqa: BLE001  (テクノロジーの中身が作れないときも、ほかの数は出す)
        T = {"nodes": [], "techs": [], "firsts": [], "emerged": [], "total": None, "error": str(ex)[:120]}
    tech = {"big_techs": [n for _, n in T["techs"]], "nodes": [[n, YR.clean(d, 50)] for _, n, d in T["nodes"]],
            "firsts": [[c, n, t] for _, c, n, t in T["firsts"]], "emerged": [[n, k] for _, n, k, _ in T["emerged"]], "reached_total": T.get("total")}
    ev, ev_n = YR.pick_events(D, y, limit=10)
    phase = YR.phase_of_year(D, y)
    lo, hi = y * SC.YEAR, y * SC.YEAR + SC.YEAR - 1
    nxt = next((x["era"] for x in st.get("era_log") or [] if lo < x["day"] <= hi + 1 and x["era"] != phase), None)
    care = None
    if t5 and "care_cs" in t5[-1]:
        care = {k: t5[-1].get(k) for k in ("posted_meds", "paid_meds", "meds_used", "care_cs", "care_house_n", "saved", "saved_sum", "u5_dead", "u5_rate", "u5_rate_avg", "meds_now")}
    # 大きな年か (動画を作る年): はじめての大きな技術・ききん・フェーズが変わった・人が 1 年で 10% 以上動いた・蓄えが 30 日分を切った
    big = []
    if tech["big_techs"]:
        big.append("はじめて届いた技術: " + "・".join(tech["big_techs"]))
    if (row.get("famine") or 0) > 0:
        big.append(f"ききん {row['famine']} 回")
    if nxt:
        big.append(f"フェーズが変わった ({phase} → {nxt})")
    if row.get("pop_growth") is not None and abs(row["pop_growth"]) >= 0.10:
        big.append(f"人が 1 年で {row['pop_growth'] * 100:+.0f}%")
    if row.get("store_min") is not None and row["store_min"] < 30:
        big.append(f"蓄えが {row['store_min']} 日分まで減った")
    charts = chart_list(phase_key)
    pe = load_explain(y - 1)
    for cid, c in charts.items():
        old = ((pe or {}).get("notes") or {}).get(cid)
        if old and c["sig"] and old.get("sig") == c["sig"]:
            c["keep_note"] = old["text"]  # 図が去年と同じ: この文をそのまま使う
    gi = guide_info()
    out = {"year": y, "asof_day": st["day"], "complete": row.get("complete"), "phase": phase, "phase_name": YR.era2.NAMES2.get(phase, phase),
           "phase_next": nxt, "phase_panel": phase_key, "year_name": YR.year_name(st, y) if hasattr(YR, "year_name") else None,
           "this_year": _pick(row, ROW_KEYS), "last_year": _pick(prev, ROW_KEYS),
           "series_12y": ser, "compo": compo, "seasons": seasons,
           "d1_rows": d1, "t5_rows": t5, "i4_rows": i4, "child_care": care, "tech": tech,
           "events": [[d, t] for d, t in ev], "events_total": ev_n,
           "goals": {"store_days": 120, "literacy_pct": 25, "nonfood_pct": 22},
           "big_event": {"qualifies": bool(big), "reasons": big},
           "charts": charts, "teams": TEAMS, "guide": {"name": gi["name"], "placeholder": gi["placeholder"], "expressions": list(EXPRS)}}
    return out


# ---------------------------------------------------------------- 数の確かめ

NUM = re.compile(r"(約|およそ|ほぼ|ほど)?\s*([+\-−▲▼]?)(\d[\d,]*(?:\.\d+)?)")


def _nums(o, acc):
    if isinstance(o, bool) or o is None:
        return
    if isinstance(o, (int, float)):
        acc.append(float(o))
    elif isinstance(o, dict):
        for k, v in o.items():
            if isinstance(k, str) and re.fullmatch(r"\d+", k):
                acc.append(float(k))
            _nums(v, acc)
    elif isinstance(o, (list, tuple)):
        for v in o:
            _nums(v, acc)
    elif isinstance(o, str):
        for m in NUM.finditer(o):
            acc.append(float(m.group(3).replace(",", "")))


def number_bag(data):
    """集めた数から、文に出てよい数の集まり (そのまま・% に直した数・去年との差と比・12 年の中の差・円の % )"""
    base = []
    _nums({k: v for k, v in data.items() if k not in ("charts", "teams", "guide")}, base)
    bag = set()
    for v in base:
        bag.add(v)
        if 0 < abs(v) <= 1.5:
            bag.add(v * 100)  # 割合 → %
        if abs(v) >= 10000:
            bag.add(v / 10000)  # 万
    ty, ly = data.get("this_year", {}), data.get("last_year", {})
    for k, v in ty.items():
        w = ly.get(k)
        if isinstance(v, (int, float)) and isinstance(w, (int, float)) and not isinstance(v, bool):
            bag.add(abs(v - w))
            if 0 < abs(v) <= 1.5 and 0 < abs(w) <= 1.5:
                bag.add(abs(v - w) * 100)  # ポイント
            if w:
                bag.add(v / w)
                bag.add(abs(v - w) / abs(w) * 100)
    for k, s in (data.get("series_12y") or {}).items():
        ys = sorted(s, key=int)
        vals = [s[y] for y in ys]
        for i in range(len(vals)):
            for j in range(i + 1, len(vals)):
                a, b = vals[i], vals[j]
                bag.add(abs(b - a))
                if 0 < abs(a) <= 1.5 and 0 < abs(b) <= 1.5:
                    bag.add(abs(b - a) * 100)
                if a:
                    bag.add(b / a)
                    bag.add(abs(b - a) / abs(a) * 100)
                if b:
                    bag.add(a / b)
        if vals:
            bag.add(max(vals))
            bag.add(min(vals))
    for k, c in (data.get("compo") or {}).items():
        for part in ("this", "last"):
            rows = c.get(part) or []
            tot = sum(v for _, v in rows if isinstance(v, (int, float)))
            if tot:
                bag.add(tot)
                for _, v in rows:
                    bag.add(v / tot * 100)
        a = {n: v for n, v in c.get("this") or []}
        b = {n: v for n, v in c.get("last") or []}
        ta, tb = sum(a.values()), sum(b.values())
        if ta and tb:
            for n in a:
                if n in b:
                    bag.add(abs(a[n] / ta - b[n] / tb) * 100)
    for r in data.get("seasons") or []:
        pass
    ss = [r.get("seed") or 0 for r in data.get("seasons") or []]
    hs = [r.get("harvested") or 0 for r in data.get("seasons") or []]
    bag.update([sum(ss), sum(hs)])
    return sorted(bag)


def _ok(n, dec, approx, bag):
    import bisect
    tol = max(0.5 * 10 ** (-dec), abs(n) * 0.03 if approx else 0)
    if not approx and dec == 0 and abs(n) >= 1000 and n % 10 == 0:
        tol = max(tol, abs(n) * 0.005)  # 「約」がなくても、千をこえる丸い数は 0.5% まで
    i = bisect.bisect_left(bag, n - tol - 1e-9)
    return i < len(bag) and bag[i] <= n + tol + 1e-9


def check_text(text, bag):
    """文の中の数のうち、集めた数にないもの"""
    bad = []
    for m in NUM.finditer(text or ""):
        s = m.group(3)
        n = float(s.replace(",", ""))
        dec = len(s.split(".")[1]) if "." in s else 0
        if dec == 0 and n <= 3:  # 「2 つ」「3 つの大事なこと」などの小さな数え
            continue
        if not _ok(n, dec, bool(m.group(1)), bag):
            bad.append(s)
    return bad


# ---------------------------------------------------------------- 出す

def load_explain(y):
    p = Path(EXPLAIN_DIR) / f"year{y}.json"
    if not p.exists():
        return None
    try:
        return json.loads(p.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return None


def publish(y, draft_path, data_path):
    data = json.loads(Path(data_path).read_text(encoding="utf-8"))
    if data.get("year") != y:
        sys.exit(f"集めた数の年 ({data.get('year')}) と --year ({y}) がちがう")
    dr = json.loads(Path(draft_path).read_text(encoding="utf-8"))
    charts = data["charts"]
    errs, warn = [], []
    bag = number_bag(data)
    notes = {}
    for cid, c in charts.items():
        if c["where"] == "tile":
            continue
        if c.get("keep_note"):
            notes[cid] = {"text": c["keep_note"], "sig": c["sig"]}  # 図が去年と同じ: 去年の文のまま
            continue
        t = ((dr.get("notes") or {}).get(cid) or "")
        t = t["text"] if isinstance(t, dict) else t
        t = t.strip()
        if not t:
            errs.append(f"図の見かた がない: {cid} ({c['title']})")
            continue
        if len(t) > 120:
            errs.append(f"図の見かた が長い ({len(t)} 字。120 字まで): {cid}")
        notes[cid] = {"text": t, "sig": c["sig"]}
    bubbles = []
    for b in dr.get("bubbles") or []:
        cid = b.get("chart")
        if cid not in charts:
            errs.append(f"吹き出しの図がない: {cid}")
            continue
        if b.get("expr") not in EXPRS:
            errs.append(f"吹き出しの顔がちがう ({b.get('expr')}): {cid}")
            continue
        t = (b.get("text") or "").strip()
        if not t or len(t) > 90:
            errs.append(f"吹き出しの文が空か長い ({len(t)} 字。90 字まで): {cid}")
            continue
        bubbles.append({"chart": cid, "field": charts[cid]["field"], "team": b.get("team") or charts[cid]["team"], "expr": b["expr"], "text": t})
    if len(bubbles) > 12:
        errs.append(f"吹き出しが多い ({len(bubbles)}。12 まで)")
    top3 = []
    for h in (dr.get("top3") or [])[:3]:
        t, ti = (h.get("text") or "").strip(), (h.get("title") or "").strip()
        if not t or not ti:
            errs.append("まとめ役の 3 つに、見出しか文がない")
            continue
        top3.append({"title": ti, "text": t, "chart": h.get("chart") if h.get("chart") in charts else None, "expr": h.get("expr") if h.get("expr") in EXPRS else "neutral"})
    video = {"qualifies": data["big_event"]["qualifies"], "reasons": data["big_event"]["reasons"]}
    vl = (dr.get("video") or {}).get("lines") or []
    if video["qualifies"]:
        if not (5 <= len(vl) <= 16):
            errs.append(f"大きな年なのに動画の文が {len(vl)} 本 (5〜16 本)")
        video["lines"] = [{"id": f"y{i + 1:02d}", "chart": x.get("chart") if x.get("chart") in charts else None, "text": (x.get("text") or "").strip(),
                           "say": (x.get("say") or x.get("text") or "").strip()} for i, x in enumerate(vl)]
    elif vl:
        warn.append("大きな年ではないので、動画の文は入れない")
    allow = {str(a.get("num")): a.get("why") for a in (dr.get("allow") or []) if a.get("num") is not None and a.get("why")}
    texts = [(f"図の見かた {k}", v["text"]) for k, v in notes.items() if not charts[k].get("keep_note")]
    texts += [(f"吹き出し {b['chart']}", b["text"]) for b in bubbles]
    texts += [(f"3 つ: {h['title']}", h["title"] + " " + h["text"]) for h in top3]
    texts += [(f"動画 {x['id']}", x["text"]) for x in video.get("lines") or []]
    nchk = 0
    for where, t in texts:
        nchk += len(NUM.findall(t))
        for s in check_text(t, bag):
            if s in allow:
                continue
            errs.append(f"数が集めた数にない: {where}: 「{s}」 — {t}")
    if errs:
        print("出さなかった (直すこと):", file=sys.stderr)
        for x in errs:
            print("  - " + x, file=sys.stderr)
        sys.exit(1)
    out = {"year": y, "asof_day": data["asof_day"], "guide": {"name": data["guide"]["name"]},
           "notes": notes, "bubbles": bubbles, "top3": top3, "video": video,
           "checked": {"numbers": nchk, "fixed": [str(x)[:160] for x in (dr.get("fixed") or [])][:20],
                       "dropped": [str(x)[:160] for x in (dr.get("dropped") or [])][:20], "allowed": [f"{k}: {v}" for k, v in allow.items()][:10]}}
    Path(EXPLAIN_DIR).mkdir(parents=True, exist_ok=True)
    p = Path(EXPLAIN_DIR) / f"year{y}.json"
    p.write_text(json.dumps(out, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
    for x in warn:
        print("注意: " + x, file=sys.stderr)
    print(f"{p} を書いた (図の見かた {len(notes)}・吹き出し {len(bubbles)}・3 つ {len(top3)}・確かめた数 {nchk}・大きな年 {'はい' if video['qualifies'] else 'いいえ'})")


def main(argv=None):
    ap = argparse.ArgumentParser(description="解説の係の数を集める / 確かめて出す")
    ap.add_argument("--data", default=os.path.join(SOC, "data"))
    ap.add_argument("--year", type=int, required=True)
    ap.add_argument("--out", help="集めた数の JSON (既定 /tmp/explain_data_<年>.json)")
    ap.add_argument("--publish", help="係の文の下書き (JSON)。確かめて reports/explain/year<年>.json に書く")
    ap.add_argument("--check-text", help="1 つの文の数を確かめるだけ (確かめの係が使う)")
    a = ap.parse_args(argv)
    dp = a.out or f"/tmp/explain_data_{a.year}.json"
    if os.path.realpath(dp).startswith(PROTECTED + os.sep):
        sys.exit("sim/society/data/ の下には書かない")
    if a.publish:
        publish(a.year, a.publish, dp)
        return
    if a.check_text is not None:
        data = json.loads(Path(dp).read_text(encoding="utf-8"))
        bad = check_text(a.check_text, number_bag(data))
        print("ない数: " + "・".join(bad) if bad else "ぜんぶある")
        return
    out = collect(a.data, a.year)
    Path(dp).write_text(json.dumps(out, ensure_ascii=False, indent=1), encoding="utf-8")
    print(f"{dp} を書いた ({len(json.dumps(out, ensure_ascii=False)) // 1024} KB・大きな年 {'はい: ' + '・'.join(out['big_event']['reasons']) if out['big_event']['qualifies'] else 'いいえ'}・"
          f"記憶 {resource.getrusage(resource.RUSAGE_SELF).ru_maxrss // 1024} MB)")


if __name__ == "__main__":
    main()
