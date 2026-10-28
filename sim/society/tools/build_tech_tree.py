#!/usr/bin/env python3
"""技術の木のページ (sim/society/app/tech_tree.html) のデータを作る (読むだけ。標準ライブラリだけ。LLM は使わない)。

説明: docs/tech_tree.md。【シ】(シミュレーションだから分かること) の見え方なので、ダッシュボード (dashboard.html) には入れない。
入力 (どれも読むだけ):
  sim/society/techtree/plan.json     予定の木 (手で書く。フェーズ・技術・前提・本物の年代)
  sim/society/techtree/emerged.json  創発の一覧 (Claude がフェーズの区切りごとに選んで手で書く)
  <data>/state.json (しまった古い年の出来事 <data>/archive/ も戻して)
出力: tech_tree.html の <!--TT-DATA--> と <!--/TT-DATA--> のあいだの JSON だけを書きかえる。--out を渡すと JSON も書く。

使い方:
  python3.13 sim/society/tools/build_tech_tree.py [--data DIR] [--embed HTML] [--out JSON] [--check] [--quiet]
  (本人の PC は py -3 -X utf8)

同じ入力なら同じ出力 (キーを並べる・時刻を入れない)。state.json にも data/ の下にも書かない。
"""
import argparse
import json
import os
import re
import sys
import time

HERE = os.path.dirname(os.path.abspath(__file__))
SOC = os.path.dirname(HERE)
sys.path.insert(0, SOC)
import archive  # noqa: E402  (しまった古い年の出来事を戻す)

DEFAULT_DATA = os.environ.get("SOC_DATA") or os.path.join(SOC, "data")
TT = os.path.join(SOC, "techtree")
DEFAULT_EMBED = os.path.join(SOC, "app", "tech_tree.html")
PROTECTED = os.path.join(SOC, "data")
YEAR = 120
KINDS = ("仕事", "もの", "やり方", "しくみ")
EKINDS = ("予定にない", "予定より早い", "予定と違う形")
SOURCES = ("村", "場は作る側", "よその便り")

# 掟の中身の種類 (初めて出た案と、初めて採用された日を見る)。言葉で結ぶので、まちがいがありうる【仮定】
LAW_TOPICS = [
    ("夜とザガ", "ザガ|夜は"), ("食べ物を分ける", "分け合|分けよう|分ける"), ("蓄え", "蓄え"), ("雨と屋根", "屋根|雨"), ("火", "火を|火で|火の"),
    ("種まき・畑", "畑|種をまく|種まき|種を埋め"), ("ヤギ", "ヤギ"), ("干し肉", "干し肉|燻"), ("子と年寄り", "小さな子|子ども|子が|子に|年寄り"),
    ("当番・交代", "当番|交代|番の人"), ("よそから来た人", "よそから|受け入れ"), ("祭り", "祭り"),
    ("もめごと", "もめごと|ゆるす|つぐな"), ("まとめ役・長老", "まとめ役|長老"), ("印と封", "封を|封は|印を"),
    ("数え札", "数え札"), ("板に刻む", "板に|板で"), ("ほかの村との交換", "交換"), ("ほかの村との貸し借り", "貸そう|借り|返す"),
    ("黒曜石", "黒曜石"), ("病", "病"), ("家の倉", "家の倉|倉を|倉の"), ("鎌と土器", "鎌|土器"), ("貢ぎと求め", "貢|求め"),
    ("壁と戦", "村のまわりの壁|土の壁|戦う|攻め"), ("金属", "金属"), ("取り立て・税", "取り立て|税"), ("利子・上乗せ", "上乗せ|利子"),
]


def yd(d):
    return None if d is None else "%d年%d日目" % (d // YEAR, d % YEAR + 1)


def _read_json(p):
    with open(p, encoding="utf-8") as f:
        return json.load(f)


def _short(t, n=90):
    t = re.sub(r"\s+", " ", t or "")
    return t if len(t) <= n else t[: n - 1] + "…"


class Scan:
    """出来事を 1 回だけ読んで、決まりごとに最初の出来事を見つける"""

    def __init__(self, st):
        self.st = st
        self.ev = st["events"]
        self.by_type = {}   # 種類 -> [(key, regex, not_regex, data_key)]
        self.found = {}     # key -> 出来事
        self.any_good = {}  # 物 -> 最初の出来事
        self.substep = {}   # "G4/F1" -> (day, 出来事の id)
        self.cards = {}     # 札 -> 最初のよその便り
        self.firsts = []    # 自動で見つけた「初めて」
        self.phase_ev = {}  # フェーズ -> そのフェーズに進んだ出来事の id

    def want(self, key, spec):
        t = spec.get("ev")
        if t:
            self.by_type.setdefault(t, []).append((key, re.compile(spec["text"]) if spec.get("text") else None,
                                                     re.compile(spec["not"]) if spec.get("not") else None, spec.get("data")))

    def run(self):
        seen_type, seen_good, seen_tool, seen_by, seen_how = {}, {}, {}, {}, {}
        law_adopt = {}
        for e in self.ev:
            t = e["type"]
            d = e.get("data") or {}
            if t not in seen_type:
                seen_type[t] = e
            for key, rx, nrx, dk in self.by_type.get(t, ()):
                if key in self.found:
                    continue
                txt = e.get("text") or ""
                if rx and not rx.search(txt):
                    continue
                if nrx and nrx.search(txt):
                    continue
                if dk and not d.get(dk):
                    continue
                self.found[key] = e
            if d.get("thing") and d["thing"] not in seen_good:
                seen_good[d["thing"]] = e
            for mv in d.get("moves") or ():
                try:
                    goods = mv[2]
                except (IndexError, TypeError):
                    continue
                for g in goods or {}:
                    if g not in seen_good:
                        seen_good[g] = e
            if t == "記録" and d.get("tool") and d["tool"] not in seen_tool:
                seen_tool[d["tool"]] = e
            if t == "確かめる" and d.get("how") and ("確かめる:" + d["how"]) not in seen_tool:
                seen_tool["確かめる:" + d["how"]] = e
            if t in ("収める", "裁き") and d.get("by"):
                k = "%s (%s)" % ({"収める": "もめごとを収める", "裁き": "裁く"}[t], d["by"])
                if "長老" in (e.get("text") or "") and d["by"] != "長老":
                    k2 = "%s (長老の言葉)" % {"収める": "もめごとを収める", "裁き": "裁く"}[t]
                    seen_by.setdefault(k2, e)
                seen_by.setdefault(k, e)
            if t in ("貢ぎ", "崩れ") and (d.get("how") or d.get("why")):
                seen_how.setdefault("%s (%s)" % (t, d.get("why") or d.get("how")), e)
            if t == "フェーズ":
                m = re.search(r"フェーズ(?:が)? ?(F\d|G\d+) ?\(", e.get("text") or "")
                if m:
                    self.phase_ev.setdefault(m.group(1), e["id"])
            if t == "区切り" and d.get("g") and d.get("f"):
                self.substep.setdefault("%s/%s" % (d["g"], d["f"]), e)
            if t == "よその便り" and d.get("card"):
                self.cards.setdefault(d["card"], e)
            if t == "掟" and "が採用された" in (e.get("text") or ""):
                m = re.match(r"掟「(.{1,40})", e["text"])
                if m:
                    law_adopt.setdefault(m.group(1)[:30], e)
        self.any_good = seen_good
        self.law_adopt = law_adopt
        self.seen_type = seen_type
        self.seen_tool = seen_tool
        self.seen_by = seen_by
        self.seen_how = seen_how

    def adopt_event(self, law):
        return self.law_adopt.get((law.get("text") or "")[:30])


def ev_ref(e):
    if not e:
        return None
    return {"day": e["day"], "ev": e["id"], "who": e.get("who"), "text": _short(e.get("text"))}


def detect(spec, sc, st, law_by_key):
    """(day, 出来事の id, だれ, 文, わけ) か None"""
    if not spec:
        return None
    if "any" in spec:
        hits = [h for h in (detect(s, sc, st, law_by_key) for s in spec["any"]) if h]
        return min(hits, key=lambda h: (h["day"], h.get("ev") or 0)) if hits else None
    if spec.get("ev"):
        return ev_ref(sc.found.get(spec["_key"]))
    if spec.get("substep"):
        e = sc.substep.get(spec["substep"])
        if e:
            return ev_ref(e)
        g, f = spec["substep"].split("/")
        for x in (st.get("era2") or {}).get("substeps", []):
            if x["g"] == g and x["f"] == f:
                return {"day": x["day"], "ev": None, "who": None, "text": "%s の %s「%s」" % (g, f, x["name"])}
        return None
    if spec.get("day") is not None:
        return {"day": spec["day"], "ev": None, "who": None, "text": spec.get("why", ""), "at": spec.get("at")}
    if spec.get("good"):
        for g, e in sc.any_good.items():
            if spec["good"] in g:
                return ev_ref(e)
        return None
    if spec.get("law"):
        best = None
        for law in law_by_key.get(spec["law"], []):
            e = sc.adopt_event(law)
            if e and (best is None or e["id"] < best["id"]):
                best = e
        return ev_ref(best)
    if spec.get("stall_done"):
        g7 = ((st.get("era2") or {}).get("g7") or {})
        s = (g7.get("stall") or {}).get(spec["stall_done"]) or {}
        if s.get("done"):
            return {"day": st["day"], "ev": None, "who": None, "text": "物差しの条件 %s に届いた (日は記録にない。今日の日を入れた)" % spec["stall_done"]}
        return None
    return None


def build(data, quiet=False):
    t0 = time.time()
    plan = _read_json(os.path.join(TT, "plan.json"))
    emer = _read_json(os.path.join(TT, "emerged.json"))
    st = archive.load_state(data)
    t_load = time.time() - t0
    errs = []

    # ---- 決まりをそろえる
    sc = Scan(st)
    for n in plan["nodes"]:
        def reg(spec, path):
            if not spec:
                return
            if "any" in spec:
                for i, s in enumerate(spec["any"]):
                    reg(s, path + ".%d" % i)
            elif spec.get("ev"):
                spec["_key"] = path
                sc.want(path, spec)
        reg(n.get("detect"), n["id"])
    sc.run()
    law_by_key = {}
    for law in st.get("laws", []):
        for k in ("penalty", "tax", "rate"):
            if law.get(k):
                law_by_key.setdefault(k, []).append(law)

    # ---- フェーズの日
    log = st.get("era_log") or []
    starts = {}
    for x in log:
        starts.setdefault(x["era"], x["day"])
    order = [p["id"] for p in plan["phases"]]
    now = st["day"]
    era = st.get("era")
    closures = plan.get("closures") or {}
    phases = []
    for i, p in enumerate(plan["phases"]):
        s = starts.get(p["id"])
        if p["id"] == "F6" and s is None:
            s = starts.get("G1")
        e = None
        for q in order[i + 1:]:
            if q in starts:
                e = starts[q]
                break
        if p["id"] == "F6":
            e = starts.get("G1")  # F6 (農耕に頼る) に入った日 = Society 2.0 の G1 に入った日。F6 は G1 と重ねず、1 日の区切りにする
        closed = None
        if e is not None:
            closed = "次のフェーズに進んだ"
        elif p["id"] in closures and closures[p["id"]].get("day") is not None:
            e = closures[p["id"]]["day"]
            closed = closures[p["id"]].get("how")
        state = "済み" if (s is not None and e is not None) else ("今" if s is not None else "予定")
        if p["id"] == era and p["id"] in closures:
            state = "済み"
        how = next((x.get("how") for x in log if x["era"] == p["id"] and x.get("how")), None)
        phases.append(dict(p, start=s, end=e, state=state, closed=closed, how=how,
                           start_text=yd(s), end_text=yd(e)))
    ph_by = {p["id"]: p for p in phases}

    pstart_ev = {"F1": -1}
    pstart_ev.update(sc.phase_ev)
    if "F6" in pstart_ev and "G1" in pstart_ev:
        pstart_ev["F6"] = pstart_ev["G1"] - 0.5  # F6 に進んだ出来事のすぐあとに G1 を始めた。F6 は 1 日だけの区切り

    def phase_of(d, eid=None):
        """d 日目 (出来事 eid) がどのフェーズか。出来事があれば、フェーズに進んだ出来事より後かで決める (区切りの日の出来事も分けられる)。
        出来事がなければ (区切りの記録など)、区切りの日は前のフェーズに入れる (季節の終わりに見て、そのあと次に進むため)"""
        if eid is not None:
            cur = None
            for p in phases:
                se = pstart_ev.get(p["id"])
                if se is not None and se <= eid:
                    cur = p["id"]
            return cur
        for p in phases:
            if p["start"] is not None and p["start"] <= d and (p["end"] is None or d <= p["end"]):
                if p["end"] is not None and p["end"] == p["start"] and d != p["start"]:
                    continue
                return p["id"]
        return None

    # ---- 予定の木
    ids = {n["id"] for n in plan["nodes"]}
    nodes = []
    for n in plan["nodes"]:
        if n["phase"] not in ph_by:
            errs.append("技術 %s のフェーズ %s が phases にない" % (n["id"], n["phase"]))
        if n.get("kind") not in KINDS:
            errs.append("技術 %s の kind が 4 つのどれでもない" % n["id"])
        for q in n.get("prereq", []):
            if q not in ids:
                errs.append("技術 %s の前提 %s が nodes にない" % (n["id"], q))
        hit = detect(n.get("detect"), sc, st, law_by_key)
        P = ph_by.get(n["phase"]) or {}
        out = {k: v for k, v in n.items() if k != "detect"}
        out["auto"] = n.get("detect") is not None
        out["code"] = n.get("code", True)
        if hit:
            out["status"] = "届いた"
            out["first"] = hit
            out["first"]["date"] = yd(hit["day"])
            at = hit.pop("at", None) or phase_of(hit["day"], hit.get("ev"))
            out["at_phase"] = at
            if at is None or order.index(at) < order.index(n["phase"]):
                out["timing"] = "早い"
            elif order.index(at) > order.index(n["phase"]):
                out["timing"] = "遅い"
            else:
                out["timing"] = "予定どおり"
        elif P.get("state") == "済み":
            out["status"] = "届かなかった"
        else:
            out["status"] = "予定" if P.get("state") == "予定" else "まだ"
        if n.get("heard"):
            e = sc.cards.get(n["heard"])
            if e:
                out["heard_at"] = dict(ev_ref(e), date=yd(e["day"]), listeners=(e.get("data") or {}).get("listeners"))
        out["dependents"] = [m["id"] for m in plan["nodes"] if n["id"] in m.get("prereq", [])]
        nodes.append(out)

    # ---- 創発 (手で選んだもの)
    emerged = []
    for x in emer["entries"]:
        if x.get("kind") not in EKINDS:
            errs.append("創発 %s の kind が 3 つのどれでもない" % x.get("id"))
        if x.get("source") not in SOURCES:
            errs.append("創発 %s の source が 3 つのどれでもない" % x.get("id"))
        if x.get("node") is not None and x["node"] not in ids:
            errs.append("創発 %s の node %s が予定の木にない" % (x.get("id"), x["node"]))
        evs = []
        for i in x.get("evidence", []):
            if not isinstance(i, int) or i < 0 or i >= len(st["events"]) or st["events"][i]["id"] != i:
                errs.append("創発 %s の出来事 %s が state にない" % (x.get("id"), i))
                continue
            evs.append(dict(ev_ref(st["events"][i]), date=yd(st["events"][i]["day"]), type=st["events"][i]["type"]))
        laws = {l["id"]: l for l in st.get("laws", [])}
        lw = []
        for L in x.get("laws", []):
            if L not in laws:
                errs.append("創発 %s の掟 %s が state にない" % (x.get("id"), L))
                continue
            l = laws[L]
            lw.append({"id": L, "status": l.get("status"), "day": l.get("day"), "date": yd(l.get("day")),
                       "proposer": l.get("proposer"), "label": l.get("label"), "text": _short(l.get("text"), 140)})
        emerged.append(dict(x, date=yd(x["day"]), at_phase=phase_of(x["day"], (x.get("evidence") or [None])[0]), evidence_rows=evs, law_rows=lw))
    checked = [dict(c, date=yd(c.get("day"))) for c in emer.get("checked_not_emerged", [])]

    # ---- 自動で見つけた「初めて」
    firsts = []

    def add(cat, name, e, extra=None):
        if not e:
            return
        r = {"cat": cat, "name": name, "day": e["day"], "date": yd(e["day"]), "ev": e["id"], "who": e.get("who"), "text": _short(e.get("text"), 110),
             "phase": phase_of(e["day"], e["id"])}
        if extra:
            r.update(extra)
        firsts.append(r)

    for t, e in sc.seen_type.items():
        add("出来事の種類", t, e, {"person": bool(e.get("who"))})
    for g, e in sc.any_good.items():
        add("やりとりに出た物", g, e)
    for k, e in sc.seen_tool.items():
        add("記録の道具", k, e)
    for k, e in sc.seen_by.items():
        add("決め方", k, e)
    for k, e in sc.seen_how.items():
        add("決め方", k, e)
    for k, e in sc.cards.items():
        add("よその便り (札)", k, e)
    # 掟の中身: 初めての案の日 (掟の番号) と、初めて採用された日 (出来事)
    for name, pat in LAW_TOPICS:
        rx = re.compile(pat)
        first_prop, first_ad = None, None
        for law in st.get("laws", []):
            if not rx.search(law.get("text") or ""):
                continue
            if first_prop is None or law["day"] < first_prop["day"]:
                first_prop = law
            e = sc.adopt_event(law)
            if e and (first_ad is None or e["id"] < first_ad["id"]):
                first_ad = e
        if first_prop:
            r = {"cat": "掟の中身", "name": name, "day": first_prop["day"], "date": yd(first_prop["day"]), "ev": None,
                 "law": first_prop["id"], "who": first_prop.get("proposer"), "label": first_prop.get("label"),
                 "text": _short(first_prop.get("text"), 110), "phase": phase_of(first_prop["day"])}
            if first_ad:
                r["adopted"] = {"day": first_ad["day"], "date": yd(first_ad["day"]), "ev": first_ad["id"]}
            firsts.append(r)
    for k in ("penalty", "tax", "rate"):
        ls = law_by_key.get(k) or []
        if ls:
            law = min(ls, key=lambda l: l["day"])
            nm = {"penalty": "罰の欄のある掟", "tax": "取り立ての欄のある掟", "rate": "換算の欄のある掟"}[k]
            firsts.append({"cat": "掟の中身", "name": nm, "day": law["day"], "date": yd(law["day"]), "ev": None, "law": law["id"],
                           "who": law.get("proposer"), "label": law.get("label"), "text": _short(law.get("text"), 110), "phase": phase_of(law["day"])})
    firsts.sort(key=lambda r: (r["day"], r["cat"], r["name"]))

    # ---- まとめの数
    cnt = {s: sum(1 for n in nodes if n["status"] == s) for s in ("届いた", "届かなかった", "まだ", "予定")}
    cnt["早い"] = sum(1 for n in nodes if n.get("timing") == "早い")
    cnt["遅い"] = sum(1 for n in nodes if n.get("timing") == "遅い")
    cnt["nodes"] = len(nodes)
    cnt["emerged"] = len(emerged)
    cnt["emerged_by_kind"] = {k: sum(1 for x in emerged if x["kind"] == k) for k in EKINDS}
    cnt["firsts"] = len(firsts)
    alive = [p for p in st.get("people", []) if p.get("alive", True) and not p.get("dead")]
    out = {
        "v": 1,
        "asof": {"day": now, "date": yd(now), "era": era, "era_name": (ph_by.get(era) or {}).get("name"),
                 "events": len(st["events"]), "people": len(alive)},
        "phases": phases,
        "nodes": nodes,
        "emerged": emerged,
        "checked": checked,
        "firsts": firsts,
        "counts": cnt,
        "plan_updated": plan.get("updated"),
        "emerged_updated": emer.get("updated"),
    }
    if not quiet:
        print("読みこみ %.1f 秒・計算 %.1f 秒" % (t_load, time.time() - t0 - t_load), file=sys.stderr)
    return out, errs


MARK_A, MARK_B = "<!--TT-DATA-->", "<!--/TT-DATA-->"


def dump(o):
    return json.dumps(o, ensure_ascii=False, sort_keys=True, separators=(",", ":"))


def embed_text(html, js):
    if html.count(MARK_A) != 1 or html.count(MARK_B) != 1:
        raise ValueError("html に %s と %s が 1 つずつない (コメントなどに同じ文字を書かない)" % (MARK_A, MARK_B))
    a, b = html.find(MARK_A), html.find(MARK_B)
    if b < a:
        raise ValueError("html の %s が %s より前にある" % (MARK_B, MARK_A))
    nl = "\r\n" if "\r\n" in html else "\n"
    body = js.replace("</", "<\\/")
    block = MARK_A + nl + '<script type="application/json" id="tt-data">' + body + "</script>" + nl
    return html[:a] + block + html[b:]


def _under(path, root):
    p, r = os.path.normcase(os.path.realpath(path)), os.path.normcase(os.path.realpath(root))
    return p == r or p.startswith(r + os.sep)


def main(argv=None):
    ap = argparse.ArgumentParser(description="技術の木のページのデータを作る (読むだけ)")
    ap.add_argument("--data", default=DEFAULT_DATA)
    ap.add_argument("--embed", default=DEFAULT_EMBED)
    ap.add_argument("--out", default=None)
    ap.add_argument("--check", action="store_true", help="書かずに作りなおして、埋めてある中身とちがえば 4 で終わる")
    ap.add_argument("--quiet", action="store_true")
    a = ap.parse_args(argv)
    t0 = time.time()
    for p in (a.embed, a.out):
        if p and _under(p, PROTECTED):
            print("止めた: %s は sim/society/data/ の下 (技術の木は data/ に書かない)" % p, file=sys.stderr)
            return 2
    out, errs = build(a.data, quiet=a.quiet)
    for e in errs:
        print("だめ: " + e, file=sys.stderr)
    if errs:
        return 1
    js = dump(out)
    c = out["counts"]
    summary = ("技術の木: %s (%s) | 予定の技術 %d (届いた %d・届かなかった %d・まだ %d・予定 %d、早い %d・遅い %d) | 創発 %d | 自動の初めて %d | %d バイト | %.1f 秒"
               % (out["asof"]["date"], out["asof"]["era"], c["nodes"], c["届いた"], c["届かなかった"], c["まだ"], c["予定"], c["早い"], c["遅い"],
                  c["emerged"], c["firsts"], len(js.encode("utf-8")), time.time() - t0))
    if a.check:
        with open(a.embed, encoding="utf-8", newline="") as f:
            html = f.read()
        same = embed_text(html, js) == html
        print(("確かめ: 同じ | " if same else "確かめ: ちがいあり | ") + summary)
        return 0 if same else 4
    if a.out:
        with open(a.out, "w", encoding="utf-8", newline="") as f:
            f.write(js)
    if a.embed:
        with open(a.embed, encoding="utf-8", newline="") as f:
            html = f.read()
        new = embed_text(html, js)
        if new != html:
            with open(a.embed, "w", encoding="utf-8", newline="") as f:
                f.write(new)
    print(summary)
    return 0


if __name__ == "__main__":
    sys.exit(main())
