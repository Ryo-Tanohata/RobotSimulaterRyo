#!/usr/bin/env python3
"""研究ダッシュボード (sim/society/app/research.html) を作る。【シ】/研究の見え方。

読むだけ (村も記録も変えない)。LLM なし。
  python3.13 sim/society/tools/build_research_dashboard.py          # 作り直す
  python3.13 sim/society/tools/build_research_dashboard.py --check  # 作り直して、ページの数が元の文書にあるか確かめる

材料:
  - 手で書いた文: sim/society/tools/research_dashboard_content.json (どの文にも src がある)
  - 機械で読む数: sim/society/data/records/season_village.jsonl (人・蓄え)、
    sim/society/app/tech_tree.html の tt-data (フェーズ・テクノロジーツリーの数)、
    sim/society/tools/survey/out/summary.md・out_exp2/summary.md (第 1 主成分・H8)、
    docs/research/humanity/data/exp3/summary.md (実験 3 の組ごとの数)、
    paper/paper*/README.md (ページ数・本人の TODO の数)、docs/youtube_upload.md (上げた動画)
ダッシュボード (dashboard.html) のデータには入れない (【シ】の決まり)。
"""
import html
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
CONTENT = Path(__file__).with_name("research_dashboard_content.json")
OUT = ROOT / "sim/society/app/research.html"

SRC_SEASON = "sim/society/data/records/season_village.jsonl"
SRC_TT = "sim/society/app/tech_tree.html"
SRC_EXP1 = "sim/society/tools/survey/out/summary.md"
SRC_EXP2 = "sim/society/tools/survey/out_exp2/summary.md"
SRC_EXP3 = "docs/research/humanity/data/exp3/summary.md"
SRC_YT = "docs/youtube_upload.md"
SRC_HANDOFF = "sim/society/HANDOFF.md"


def rd(rel):
    return (ROOT / rel).read_text(encoding="utf-8")


def esc(s):
    return html.escape(str(s), quote=True)


# ---------------------------------------------------------------- 機械で読む数

def load_seasons():
    rows = []
    for line in rd(SRC_SEASON).splitlines():
        if line.strip():
            r = json.loads(line)
            rows.append({
                "x": round(r["season_end_day"] / 120, 3),
                "label": r["label"], "day": r["season_end_day"], "era": r["era"],
                "pop": r["population"], "store": r["store_days"],
            })
    return rows


def load_tt():
    h = rd(SRC_TT)
    m = re.search(r'<script type="application/json" id="tt-data">(.*?)</script>', h, re.S)
    return json.loads(m.group(1))


def parse_pc1():
    """第 1 主成分の割合 (95% CI)。人間 0.268 は修士論文の表 3 (固有値から)。"""
    out = {}
    t1 = rd(SRC_EXP1)
    m = re.search(r"第 1 主成分の割合 ([0-9.]+) \(印刷では", t1)
    out["human"] = float(m.group(1))
    for name, text in (("C1", t1), ("C2", t1)):
        m = re.search(r"^\| %s \| (\d+) \| \d+ \| [^|]+\| ([0-9.]+) \[([0-9.]+), ([0-9.]+)\]" % name, text, re.M)
        out[name] = (float(m.group(2)), float(m.group(3)), float(m.group(4)), int(m.group(1)))
    t2 = rd(SRC_EXP2)
    for name in ("D1", "D2"):
        m = re.search(r"^\| %s \| (\d+) \| \d+ \| [^|]+\| ([0-9.]+) \[([0-9.]+), ([0-9.]+)\]" % name, t2, re.M)
        out[name] = (float(m.group(2)), float(m.group(3)), float(m.group(4)), int(m.group(1)))
    return out


def parse_h8():
    t = rd(SRC_EXP2)
    sec = t.split("## H8")[1].split("## H9")[0]
    rows = []
    for m in re.finditer(r"^\| ([^|]+?) \| ([-+]?[0-9.]+) \[([-+]?[0-9.]+), ([-+]?[0-9.]+)\] \| ([^|]+?) \|", sec, re.M):
        rows.append({"name": m.group(1).strip(), "est": float(m.group(2)), "lo": float(m.group(3)),
                     "hi": float(m.group(4)), "verdict": m.group(5).strip(),
                     "raw": "%s [%s, %s]" % (m.group(2), m.group(3), m.group(4))})
    return rows


def parse_exp3():
    t = rd(SRC_EXP3)
    meas = {}
    for m in re.finditer(r"^\| (M\d[^|]*?|T [^|]*?) \| ([^|]+)\| ([^|]+)\| ([^|]+)\| ([^|]+)\|$", t, re.M):
        meas[m.group(1).strip()] = [c.strip() for c in m.group(2, 3, 4, 5)]
    world_sec = t.split("## 世界の数")[1]
    lines = [l for l in world_sec.splitlines() if l.startswith("|")]
    head = [c.strip() for c in lines[0].strip("|").split("|")]
    world = {}
    for l in lines[2:]:
        cells = [c.strip() for c in l.strip("|").split("|")]
        world[cells[0]] = dict(zip(head, cells))
    return meas, world


def parse_paper(rel):
    t = rd(rel)
    pages = int(re.search(r"Built draft \((\d+) pages\)", t).group(1))
    todo = t.split("## TODO for the author")[1]
    n = len(re.findall(r"^\d+\. ", todo, re.M))
    return pages, n


def count_youtube():
    t = rd(SRC_YT)
    rows = [l for l in t.splitlines() if l.startswith("| ") and re.match(r"\| \d\d ", l)]
    up = [l for l in rows if "youtu.be/" in l]
    return len(rows), len(up)


# ---------------------------------------------------------------- 図 (SVG)

def fmt_tok(man):
    """万トークン → 「約 6 億 4,510 万」の形。"""
    oku, rest = divmod(int(man), 10000)
    if oku and rest:
        return "約 %d 億 %s 万" % (oku, format(rest, ","))
    if oku:
        return "約 %d 億" % oku
    return "約 %s 万" % format(rest, ",")


def line_chart(cid, rows, key, title, unit, eras, ymax=None, W=1000, H=260, yrstep=10, minlab=30, cls="only-desk"):
    L, R, T, B = (74, 14, 34, 40) if W > 600 else (46, 10, 30, 32)
    xs = [r["x"] for r in rows]
    x0, x1 = 0, max(xs)
    vals = [r[key] for r in rows]
    top = ymax or max(vals)
    step = 50 if top <= 250 else (250 if top <= 1500 else 500)
    top = (int(top / step) + 1) * step if ymax is None else ymax
    sx = lambda x: L + (x - x0) / (x1 - x0) * (W - L - R)
    sy = lambda y: T + (1 - y / top) * (H - T - B)
    g = []
    # フェーズの帯 (1 つおきにうすく)
    for i, (era, a, b) in enumerate(eras):
        if i % 2 == 1:
            g.append('<rect x="%.1f" y="%d" width="%.1f" height="%d" class="band"/>' % (sx(a), T, sx(b) - sx(a), H - T - B))
        if sx(b) - sx(a) > minlab:
            g.append('<text x="%.1f" y="%d" class="eral">%s</text>' % ((sx(a) + sx(b)) / 2, T - 8, era))
    if W > 600:
        g.append('<text x="%.1f" y="%d" class="eral">G2–G4</text>' % (sx(12), T - 8))
    # y の目盛り
    for k in range(0, int(top) + 1, step):
        y = sy(k)
        g.append('<line x1="%d" x2="%d" y1="%.1f" y2="%.1f" class="grid"/>' % (L, W - R, y, y))
        g.append('<text x="%d" y="%.1f" class="tick" text-anchor="end">%s</text>' % (L - 6, y + 4, format(k, ",")))
    for yr in range(0, int(x1) + 1, yrstep):
        g.append('<text x="%.1f" y="%d" class="tick" text-anchor="middle">%d年</text>' % (sx(yr), H - 8, yr))
    g.append('<line x1="%d" x2="%d" y1="%.1f" y2="%.1f" class="axis"/>' % (L, W - R, sy(0), sy(0)))
    pts = " ".join("%.1f,%.1f" % (sx(r["x"]), sy(min(r[key], top))) for r in rows)
    g.append('<polyline points="%s" class="ln"/>' % pts)
    last = rows[-1]
    g.append('<circle cx="%.1f" cy="%.1f" r="4" class="dot"/>' % (sx(last["x"]), sy(last[key])))
    g.append('<line class="xh" x1="0" x2="0" y1="%d" y2="%d" visibility="hidden"/>' % (T, H - B))
    g.append('<circle class="xd" r="5" cx="0" cy="0" visibility="hidden"/>')
    data = [[round(sx(r["x"]), 1), round(sy(min(r[key], top)), 1), r["label"], r["day"], r["era"], r[key]] for r in rows]
    return ('<div class="chart %s" data-unit="%s"><svg id="%s" viewBox="0 0 %d %d" role="img" aria-label="%s">%s</svg><div class="tip" hidden></div>'
            '<script type="application/json" class="pts">%s</script></div>') % (
        cls, esc(unit), cid, W, H, esc(title), "".join(g), json.dumps(data, ensure_ascii=False))


def ci_chart(rows, lo, hi, ticks, ref=None, ref_label="", zero=False, aria="", W=1000, vis="only-desk"):
    """横向きの点 + 95% 区間。名前は行の上に書く (スマホでも切れない)。rows: (label, est, lo, hi, cls, shape, tip)"""
    PADL, PADR = (14, 110) if W > 600 else (8, 66)
    rowh = 64 if W > 600 else 56
    top = 40
    H = top + rowh * len(rows) + 34
    sx = lambda v: PADL + (v - lo) / (hi - lo) * (W - PADL - PADR)
    g = []
    for t in ticks:
        g.append('<line x1="%.1f" x2="%.1f" y1="%d" y2="%d" class="grid"/>' % (sx(t), sx(t), top - 6, H - 30))
        g.append('<text x="%.1f" y="%d" class="tick" text-anchor="middle">%s</text>' % (sx(t), H - 6, ("%+.1f" % t if zero and t else ("0" if zero else "%.1f" % t))))
    if zero:
        g.append('<line x1="%.1f" x2="%.1f" y1="%d" y2="%d" class="axis"/>' % (sx(0), sx(0), top - 10, H - 30))
        g.append('<text x="%.1f" y="%d" class="tick" text-anchor="middle">0 = 動かない</text>' % (sx(0), top - 16))
    if ref is not None:
        g.append('<line x1="%.1f" x2="%.1f" y1="%d" y2="%d" class="ref"/>' % (sx(ref), sx(ref), top - 10, H - 30))
        g.append('<text x="%.1f" y="%d" class="lab" text-anchor="middle">%s</text>' % (sx(ref), top - 16, esc(ref_label)))
    for i, (label, est, a, b, cls, shape, tip) in enumerate(rows):
        y0 = top + rowh * i
        y = y0 + rowh * 0.68
        g.append('<g class="hit" tabindex="0"><title>%s</title>' % esc(tip))
        g.append('<rect x="0" y="%.1f" width="%d" height="%d" class="hitbox"/>' % (y0, W, rowh))
        g.append('<text x="%d" y="%.1f" class="rl">%s</text>' % (PADL, y0 + rowh * 0.36, esc(label)))
        if a is not None:
            g.append('<line x1="%.1f" x2="%.1f" y1="%.1f" y2="%.1f" class="ci %s"/>' % (sx(a), sx(b), y, y, cls))
            for v in (a, b):
                g.append('<line x1="%.1f" x2="%.1f" y1="%.1f" y2="%.1f" class="ci %s"/>' % (sx(v), sx(v), y - 7, y + 7, cls))
        if shape == "diamond":
            g.append('<path d="M%.1f %.1f l8 8 l-8 8 l-8 -8 z" class="pt %s"/>' % (sx(est), y - 8, cls))
        else:
            g.append('<circle cx="%.1f" cy="%.1f" r="7" class="pt %s"/>' % (sx(est), y, cls))
        g.append('<text x="%.1f" y="%.1f" class="val">%s</text>' % ((sx(b) if b is not None else sx(est)) + 14, y + 6, esc(("%+.3f" % est) if zero else "%.3f" % est)))
        g.append('</g>')
    return '<svg viewBox="0 0 %d %d" role="img" aria-label="%s" class="cichart %s">%s</svg>' % (W, H, esc(aria), vis, "".join(g))


# ---------------------------------------------------------------- 部品

CHIP = {
    "yes": ("✓", "支持", "c-yes"),
    "part": ("◐", "一部", "c-part"),
    "no": ("✕", "支持しない", "c-no"),
    "rev": ("⇄", "逆", "c-rev"),
    "hit": ("✓", "当たった", "c-yes"),
    "miss": ("✕", "外れた", "c-no"),
}


def chip(s):
    ic, lb, cl = CHIP[s]
    return '<span class="chip %s"><span aria-hidden="true">%s</span> %s</span>' % (cl, ic, lb)


def srcline(srcs):
    if isinstance(srcs, str):
        srcs = [srcs]
    return '<p class="src">出どころ: %s</p>' % "・".join("<code>%s</code>" % esc(s) for s in srcs)


def card(title, body, srcs, cls="", hid=None):
    hid = hid or "h-" + str(abs(hash(title)) % 10**8)
    return '<section class="box %s" aria-labelledby="%s"><h2 id="%s">%s</h2>%s%s</section>' % (
        cls, hid, hid, esc(title), body, srcline(srcs))


# ---------------------------------------------------------------- ページ

def build():
    C = json.loads(CONTENT.read_text(encoding="utf-8"))
    seasons = load_seasons()
    tt = load_tt()
    pc1 = parse_pc1()
    h8 = parse_h8()
    meas, world = parse_exp3()
    p1_pages, p1_todo = parse_paper("paper/paper1/README.md")
    p2_pages, p2_todo = parse_paper("paper/paper2/README.md")
    yt_all, yt_up = count_youtube()
    handoff = rd(SRC_HANDOFF)
    last = seasons[-1]
    asof = tt["asof"]
    assert asof["day"] == last["day"], (asof, last)
    assert "108年120日目 (13079 日目)" in handoff
    assert p1_todo == len(C["status"]["paper1_todo"]["items"]), (p1_todo, "paper1 の TODO の数が content と合わない")
    assert p2_todo == len(C["status"]["paper2_todo"]["items"]), (p2_todo, "paper2 の TODO の数が content と合わない")

    # 仮説の数
    hyp = {"yes": 0, "part": 0, "no": 0, "rev": 0}
    for e in C["experiments"]:
        for r in e["rows"]:
            hyp[r["s"]] += 1
    n_hyp = sum(hyp.values())
    n_exp = len(C["experiments"]) + len(C["state_experiments"]["rows"])
    tok_known = [t for t in C["tokens"] if t["man"] is not None]
    tok_sum = sum(t["man"] for t in tok_known)
    tok_unknown = [t for t in C["tokens"] if t["man"] is None]

    # フェーズの帯 (季節の記録の era から)
    eras = []
    for r in seasons:
        if not eras or eras[-1][0] != r["era"]:
            eras.append([r["era"], r["x"] - 0.25, r["x"]])
        eras[-1][2] = r["x"]
    years_run = last["x"]

    parts = []
    A = parts.append

    # 1. 見出し
    A('<header><div class="top-row"><div>'
      '<h1>%s<span class="tag" title="シミュレーションと研究の記録から">【シ】研究</span></h1>'
      '<p class="lead">%s</p></div>'
      '<button class="btn" id="theme" type="button" aria-label="明るい表示と暗い表示を切りかえる">◐</button></div>'
      '<nav class="links" aria-label="ほかのページ"><a href="index.html">アプリへ</a>'
      '<a href="tech_tree.html">テクノロジーツリー</a><a href="dashboard.html">村の跡と記録</a></nav>'
      '<div class="datebox">まとめた日: <b>%s</b>。村の記録は <b class="d">%s</b> (%s 日目) まで。%s</div></header>'
      % (esc(C["title"]), esc(C["purpose"]["text"]), esc(C["asof"]), esc(asof["date"]), asof["day"],
         srcline([C["purpose"]["src"][0], SRC_TT])))

    # 2. 数のタイル
    tiles = [
        ("村の日", asof["date"], "%s 日目・%s 人・%s %s (止まっている)" % (asof["day"], last["pop"], asof["era"], asof["era_name"]),
         [SRC_TT, SRC_SEASON, SRC_HANDOFF]),
        ("走らせた年数", "108 年", "0年1日目 → %s。季節の記録 %d" % (asof["date"], len(seasons)), [SRC_SEASON, "paper/paper1/要約_ja.md"]),
        ("実験", "%d" % n_exp, "国の研究 %d (A1・A2・B・C) + 論文 2 の実験 %d" % (len(C["state_experiments"]["rows"]), len(C["experiments"])),
         ["docs/research/state_emergence_*.md", "docs/research/humanity/paper2_exp*_results.md"]),
        ("前もって決めた仮説", "%d" % n_hyp, "✓支持 %d・◐一部 %d・✕支持しない %d・⇄逆 %d" % (hyp["yes"], hyp["part"], hyp["no"], hyp["rev"]),
         ["docs/research/humanity/paper2_exp*_results.md"]),
        ("論文", "2 本", "どちらも下書き。%d ページ・%d ページ。本人の TODO %d・%d" % (p1_pages, p2_pages, p1_todo, p2_todo),
         ["paper/paper1/README.md", "paper/paper2/README.md"]),
        ("使ったトークン (分かる分)", fmt_tok(tok_sum), "%d 件を足した。%d 件は記録なし" % (len(tok_known), len(tok_unknown)),
         ["下の「使ったトークン」の表"]),
    ]
    A('<section class="tiles" aria-label="数のまとめ">' + "".join(
        '<div class="tile"><div class="k">%s</div><div class="v">%s</div><div class="s">%s</div>%s</div>' % (
            esc(k), esc(v), esc(s), srcline(src)) for k, v, s, src in tiles) + '</section>')

    # 3. いまの状態と、本人に決めてほしいこと
    st = C["status"]
    b = ['<div class="cols2"><div><h3>いま</h3><ul class="plain">']
    b += ['<li>%s <span class="src">(%s)</span></li>' % (esc(i["text"]), esc("・".join(i["src"]))) for i in st["running"]]
    b.append('</ul><h3>研究で決めてほしいこと</h3><ul class="checks">')
    b += ['<li><span class="box-ic" aria-hidden="true">☐</span><span>%s <span class="src">(%s)</span></span></li>' % (esc(i["text"]), esc("・".join(i["src"]))) for i in st["decide"]]
    b.append('</ul></div><div>')
    for key, name in (("paper1_todo", "論文 1"), ("paper2_todo", "論文 2")):
        t = st[key]
        b.append('<h3>%s で本人がすること (%d)</h3><ul class="checks">' % (name, len(t["items"])))
        b += ['<li><span class="box-ic" aria-hidden="true">☐</span>%s</li>' % esc(x) for x in t["items"]]
        b.append('</ul><p class="src">出どころ: <code>%s</code> の「TODO for the author」</p>' % esc(t["src"][0]))
    b.append('</div></div>')
    A(card("いまの状態と、ご本人に決めてほしいこと", "".join(b), [SRC_HANDOFF], "status", "h-status"))

    # 4. 研究の流れ
    ph = {p["id"]: p for p in tt["phases"]}
    b = ['<div class="cols2"><div><h3>村の歩み (村の中の日付)</h3><ol class="tl">']
    for it in C["timeline_village"]:
        p = ph.get(it["id"])
        rng = it.get("range") or "%s〜%s" % (p["start_text"], p["end_text"] or "今")
        name = it.get("name") or "%s %s" % (it["id"], p["name"])
        now = ' <span class="now">今</span>' if it["id"] == "G9" else ""
        b.append('<li><div class="tl-d">%s</div><div class="tl-n">%s%s</div><div class="tl-t">%s</div>'
                 '<div class="src">%s</div></li>' % (esc(rng), esc(name), now, esc(it["text"]), esc("・".join(it["src"]))))
    b.append('</ol></div><div><h3>研究の歩み (本当の日付)</h3><ol class="tl">')
    for it in C["timeline_research"]:
        b.append('<li><div class="tl-d">%s</div><div class="tl-n">%s</div><div class="tl-t">%s</div>'
                 '<div class="src">%s</div></li>' % (esc(it["date"]), esc(it["name"]), esc(it["text"]), esc("・".join(it["src"]))))
    b.append('</ol></div></div>')
    A(card("研究の流れ", "".join(b), [SRC_TT + " (フェーズの日)", "各行の文書"], "", "h-flow"))

    # 5. わかったこと
    b = ['<div class="cols3">']
    for f in C["findings"]:
        b.append('<div class="fcol"><h3>%s</h3><ul class="plain">%s</ul>%s</div>' % (
            esc(f["title"]), "".join("<li>%s</li>" % esc(x) for x in f["items"]), srcline(f["src"])))
    b.append('</div>')
    A(card("わかったこと", "".join(b), ["docs/research/humanity/part1_same_and_different.md・part2_technology.md・part3_humanness.md (くわしく)"], "", "h-find"))

    # 6. 実験の結果表
    b = ['<p class="note">しるし: %s %s %s %s (色だけでなく、形と言葉で分けた)</p>' % (chip("yes"), chip("part"), chip("no"), chip("rev"))]
    for e in C["experiments"]:
        b.append('<h3>%s</h3><div class="tw"><table class="res"><thead><tr><th>仮説</th><th>見たこと</th><th>結果</th><th>判定</th></tr></thead><tbody>' % esc(e["title"]))
        for r in e["rows"]:
            b.append('<tr><td data-l="仮説"><b>%s</b></td><td data-l="見たこと">%s</td><td data-l="結果">%s</td><td data-l="判定">%s</td></tr>' % (
                esc(r["h"]), esc(r["q"]), esc(r["r"]), chip(r["s"])))
        b.append('</tbody></table></div>' + srcline(e["src"]))
    se = C["state_experiments"]
    b.append('<h3>%s</h3><div class="tw"><table class="res"><thead><tr><th>実験</th><th>大きさ</th><th>おもな結果</th></tr></thead><tbody>' % esc(se["src_note"]))
    for r in se["rows"]:
        b.append('<tr><td data-l="実験"><b>%s</b></td><td data-l="大きさ">%s</td><td data-l="おもな結果">%s<div class="src">%s</div></td></tr>' % (
            esc(r["name"]), esc(r["size"]), esc(r["r"]), esc("・".join(r["src"]))))
    b.append('</tbody></table></div>')
    cp = se["c_predictions"]
    b.append('<h3>実験 C: 前もっての見込み 4 つ</h3><div class="tw"><table class="res"><tbody>')
    for r in cp["rows"]:
        b.append('<tr><td data-l="見込み">%s%s</td><td data-l="結果">%s</td></tr>' % (
            esc(r["q"]), (' <span class="note">%s</span>' % esc(r["note"])) if r.get("note") else "", chip(r["s"])))
    b.append('</tbody></table></div>' + srcline(cp["src"]))
    A(card("実験の結果表", "".join(b), ["各表の下"], "", "h-res"))

    # 7. 図
    b = ['<h3>村の人の数 (季節の終わり)</h3><p class="note">うすい帯はフェーズ (G1〜G9)。線にさわると、その季節の数が出ます。いま (%s): <b>%s 人</b>。</p>' % (esc(last["label"]), last["pop"]),
         line_chart("c-pop", seasons, "pop", "村の人の数", " 人", eras), line_chart("c-pop-m", seasons, "pop", "村の人の数", " 人", eras, W=420, H=300, yrstep=20, minlab=22, cls="only-phone"), srcline(SRC_SEASON),
         '<h3>村の蓄え (何日分。季節の終わり)</h3><p class="note">村の蓄えだけ (家の倉は入らない)。103年の冬と春は 0。いま (%s): <b>%s 日分</b>。</p>' % (esc(last["label"]), last["store"]),
         line_chart("c-store", seasons, "store", "村の蓄え (日分)", " 日分", eras), line_chart("c-store-m", seasons, "store", "村の蓄え (日分)", " 日分", eras, W=420, H=300, yrstep=20, minlab=22, cls="only-phone"), srcline(SRC_SEASON)]
    rows = [("人間 (修士論文 表 3、84 人)", pc1["human"], None, None, "s-h", "diamond", "人間 %.3f (固有値から。区間なし)" % pc1["human"])]
    for k, lab, cls in (("C1", "実験 1 C1 人格の言葉", "s-1"), ("C2", "実験 1 C2 人格 + 本音を先に", "s-1"),
                        ("D1", "実験 2 D1 暮らし・立場", "s-2"), ("D2", "実験 2 D2 暮らし + まわりの様子", "s-2")):
        v = pc1[k]
        rows.append(("%s (%d 人)" % (lab, v[3]), v[0], v[1], v[2], cls, "dot", "%s: %.3f [%.3f, %.3f]" % (lab, v[0], v[1], v[2])))
    b += ['<h3>ばらつきの形: 第 1 主成分の割合 (点と 95% 区間)</h3>',
          '<p class="note">1 本の軸 (全体に厳しいか、ゆるいか) にまとまるほど大きい。点線が人間の 0.268。</p>',
          '<ul class="legend"><li><span class="lg s-h">◆</span>人間</li><li><span class="lg s-1">●</span>実験 1 (人格の言葉)</li>'
          '<li><span class="lg s-2">●</span>実験 2 (暮らし・立場)</li></ul>',
          ci_chart(rows, 0.15, 0.5, [0.2, 0.3, 0.4, 0.5], ref=pc1["human"], ref_label="人間 %.3f" % pc1["human"],
                   aria="第 1 主成分の割合。人間と実験 1・実験 2"),
          ci_chart(rows, 0.15, 0.5, [0.2, 0.3, 0.4, 0.5], ref=pc1["human"], ref_label="人間 %.3f" % pc1["human"],
                   aria="第 1 主成分の割合。人間と実験 1・実験 2", W=420, vis="only-phone"),
          srcline([SRC_EXP1, SRC_EXP2])]
    hr = []
    for r in h8:
        ok = r["verdict"].startswith("支持 ")
        hr.append(("%s %s" % ("✓" if ok else "✕", r["name"]), r["est"], r["lo"], r["hi"], "s-2", "dot",
                   "%s: %s。%s" % (r["name"], r["raw"], r["verdict"])))
    b += ['<h3>実験 2 の H8: はみ出しやすい時 4 つの効き目 (グレーゾーン 14 問)</h3>',
          '<p class="note">左ほど「問題でない」へ動いた。区間が 0 をまたがなければ「効いた」(✓)。</p>',
          ci_chart(hr, -0.3, 0.1, [-0.3, -0.2, -0.1, 0.0, 0.1], zero=True, aria="H8 の係数と 95% 区間"),
          ci_chart(hr, -0.3, 0.1, [-0.3, -0.2, -0.1, 0.0, 0.1], zero=True, aria="H8 の係数と 95% 区間", W=420, vis="only-phone"),
          srcline(SRC_EXP2)]
    pick = [("M1 つぐなう (裁きの答え)", "つぐなう (裁き)"), ("M2 つぐなう: 言い出した家の席", "つぐなう (言い出した家)"),
            ("M4 家の倉を持つ (keep true)", "家の倉を持つ"), ("M6 罰のある案", "罰のある案"), ("M6 税のある案", "税のある案"),
            ("M6 掟の案", "掟の案"), ("M7 票の反対", "票の反対"), ("M9 答えのそろい (H4)", "答えのそろい")]
    b.append('<h3>実験 3: 組ごとの数 (12599〜12958 日目)</h3><p class="note">A0 いまのお題 / A1 暮らしを足す / A2 暮らし + まわりの様子 / L = A1 と A2 をまとめたもの。かっこは答えの数。</p>'
             '<div class="tw"><table class="num"><thead><tr><th>数</th><th>A0</th><th>A1</th><th>A2</th><th>L</th></tr></thead><tbody>')
    for key, lab in pick:
        v = meas[key]
        b.append('<tr><td data-l="数">%s</td>%s</tr>' % (esc(lab), "".join('<td data-l="%s">%s</td>' % (c, esc(x)) for c, x in zip(("A0", "A1", "A2", "L"), v))))
    b.append('</tbody></table></div><div class="tw"><table class="num"><thead><tr><th>世界の数 (3 年)</th><th>A0</th><th>A1</th><th>A2</th><th>H0 本物</th></tr></thead><tbody>')
    for key, lab in (("deaths", "亡くなった人"), ("births", "生まれた人"), ("pop_end", "おわりの人の数"), ("store_days_end", "おわりの蓄え (日分)"), ("つぐなう", "つぐなう (払った)")):
        b.append('<tr><td data-l="数">%s</td>%s</tr>' % (esc(lab), "".join('<td data-l="%s">%s</td>' % (c, esc(world[k][key])) for c, k in (("A0", "A0_1"), ("A1", "A1_1"), ("A2", "A2_1"), ("H0", "H0")))))
    b.append('</tbody></table></div>' + srcline(SRC_EXP3))
    b.append('<h3>文書の図</h3><div class="figs">')
    for f in C["figures"]:
        b.append('<figure><a href="../../../%s"><img src="../../../%s" alt="%s"></a><figcaption>%s<br><code>%s</code></figcaption></figure>' % (
            esc(f["file"]), esc(f["file"]), esc(f["cap"]), esc(f["cap"]), esc(f["file"])))
    b.append('</div>')
    A(card("おもな図", "".join(b), ["各図の下"], "", "h-charts"))

    # 8. 論文
    b = ['<div class="cols2">']
    for p, pages, ntodo in ((C["papers"][0], p1_pages, p1_todo), (C["papers"][1], p2_pages, p2_todo)):
        b.append('<div class="paper"><h3>%s</h3><p class="en">%s</p><p>%s</p><ul class="plain"><li>いま: %s</li><li>%d ページ</li><li>本人の TODO: %d</li></ul>'
                 '<p class="plinks"><a href="%s">PDF を開く</a><a href="%s">日本語の要約</a></p>%s</div>' % (
                     "論文 1" if p["id"] == "paper1" else "論文 2", esc(p["title_en"]), esc(p["title_ja"]), esc(p["state"]),
                     pages, ntodo, esc(p["pdf"]), esc(p["summary"]), srcline(p["src"])))
    b.append('</div>')
    A(card("論文", "".join(b), ["paper/paper1/・paper/paper2/"], "", "h-paper"))

    # 9. 次の一手
    b = ['<div class="tw"><table class="res"><thead><tr><th>案</th><th>中身</th><th>費用</th></tr></thead><tbody>']
    for n in C["next"]:
        b.append('<tr><td data-l="案"><b>%s</b></td><td data-l="中身">%s<div class="src">%s</div></td><td data-l="費用">%s</td></tr>' % (
            esc(n["name"]), esc(n["text"]), esc("・".join(n["src"])), esc(n["cost"])))
    b.append('</tbody></table></div><p class="note">どれをするかは、ご本人が決めます。</p>')
    A(card("次の一手 (案と費用)", "".join(b), ["各行の文書"], "", "h-next"))

    # トークン
    b = ['<div class="tw"><table class="num tok"><thead><tr><th>何に</th><th>トークン</th><th>出どころ</th></tr></thead><tbody>']
    for t in C["tokens"]:
        b.append('<tr><td data-l="何に">%s</td><td data-l="トークン">%s</td><td data-l="出どころ"><code>%s</code></td></tr>' % (
            esc(t["label"]), esc(t["text"]), esc(t["src"])))
    b.append('<tr class="sum"><td data-l="何に"><b>分かる分の合計 (このページで足した)</b></td><td data-l="トークン"><b>%s</b></td><td data-l="出どころ">上の %d 行</td></tr>' % (fmt_tok(tok_sum), len(tok_known)))
    b.append('</tbody></table></div><p class="note">試しの回 (実験 1 の 44 万・実験 2 の 26 万) は入れていない。「記録なし」は文書に数がないもの (論文 1 の TODO 4)。</p>')
    A(card("使ったトークン", "".join(b), ["各行の文書"], "", "h-tok"))

    # ほかの数
    tc = tt["counts"]
    b = ['<ul class="plain"><li>テクノロジーツリー: 項目 %d のうち届いた %d、要素 %d、創発 %d</li>' % (tc["techs"], tc["techs_reached"], tc["nodes"], tc["emerged"]),
         '<li>YouTube: 一覧 %d 本のうち、URL があるもの %d 本</li></ul>' % (yt_all, yt_up)]
    A(card("ほかの数", "".join(b), [SRC_TT, SRC_YT], "", "h-other"))

    # 10. 足もと
    A('<footer class="box"><h2>出どころと作り直し方</h2><ul class="plain">'
      '<li>まとめ: <code>docs/research/humanity/README.md</code> (くわしくは part1〜3)</li>'
      '<li>論文 2 の実験: <code>docs/research/humanity/paper2_exp1〜3_*.md</code>・<code>sim/society/tools/survey/out*/summary.md</code>・<code>docs/research/humanity/data/exp3/summary.md</code></li>'
      '<li>国の研究: <code>docs/research/state_emergence_A1・A2・B・C.md</code></li>'
      '<li>村のフェーズ: <code>docs/society_phase/G7.md・G8.md・G8_heavy.md・G9_design.md・G9_check.md</code>・<code>sim/society/HANDOFF.md</code></li>'
      '<li>村の数: <code>sim/society/data/records/season_village.jsonl</code>・テクノロジーツリー <code>sim/society/app/tech_tree.html</code></li>'
      '<li>論文: <code>paper/paper1/</code>・<code>paper/paper2/</code>。動画: <code>docs/youtube_upload.md</code></li>'
      '<li>手で書いた文: <code>sim/society/tools/research_dashboard_content.json</code></li>'
      '<li>作り直し: <code>python3.13 sim/society/tools/build_research_dashboard.py</code> (LLM なし・読むだけ)。'
      '数の確かめ: <code>--check</code></li></ul>'
      '<p class="note">このページは【シ】/研究の見え方です。村の跡のダッシュボード (dashboard.html) のデータには入れていません。</p></footer>')

    page = TEMPLATE.replace("%%TITLE%%", esc(C["title"])).replace("%%BODY%%", "\n".join(parts))
    OUT.write_text(page, encoding="utf-8")
    print("wrote", OUT.relative_to(ROOT), len(page), "bytes")
    return C


# ---------------------------------------------------------------- 確かめ

NUM = re.compile(r"\d[\d,]*(?:\.\d+)?")


def check(C):
    """手で書いた文の数が、その src の文書にあるか。ないものを書き出す。"""
    bad = 0
    total = 0

    def srctext(srcs):
        if isinstance(srcs, str):
            srcs = [srcs]
        t = ""
        for s in srcs:
            p = ROOT / s
            if p.exists():
                t += p.read_text(encoding="utf-8")
            else:
                print("  src がない:", s)
        return t

    def one(text, srcs, where):
        nonlocal bad, total
        st = srctext(srcs)
        for n in NUM.findall(text):
            total += 1
            if n not in st:
                bad += 1
                print("  見つからない: %s  「%s」 (%s)" % (n, text[:60], where))

    one(C["purpose"]["text"], C["purpose"]["src"], "purpose")
    for k in ("running", "decide"):
        for i in C["status"][k]:
            one(i["text"], i["src"], k)
    for it in C["timeline_village"] + C["timeline_research"]:
        one(it["text"], it["src"], it.get("id") or it["name"])
        if it.get("date", "").startswith("2026"):
            one(it["date"], it["src"], it["name"])
    for f in C["findings"]:
        for x in f["items"]:
            one(x, f["src"], f["title"])
    for e in C["experiments"]:
        for r in e["rows"]:
            one(r["r"].replace("−", "-"), e["src"], e["id"] + r["h"])
    for r in C["state_experiments"]["rows"]:
        one(r["r"] + " " + r["size"], r["src"], r["name"])
    for t in C["tokens"]:
        one(t["text"], t["src"], t["label"])
    for n in C["next"]:
        one(n["text"] + " " + n["cost"], n["src"], n["name"])
    for p in C["papers"]:
        one(p["title_ja"], p["src"], p["id"])
    print("確かめた数 %d、見つからない %d" % (total, bad))
    return bad


TEMPLATE = r"""<!doctype html>
<html lang="ja">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>%%TITLE%% — 川辺の村</title>
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Zen+Kaku+Gothic+New:wght@400;500;700&display=swap" media="print" onload="this.media='all'">
<style>
/* 研究ダッシュボード (【シ】/研究の見え方)。このファイルは sim/society/tools/build_research_dashboard.py が書く。手で直さない */
:root{
 color-scheme:light;
 --page:#f6f6f3;--surface:#fcfcfb;--ink:#0b0b0b;--ink2:#52514e;--muted:#6f6d68;--grid:#e1e0d9;--axis:#c3c2b7;--band:#efeee9;
 --s1:#eb6834;--s2:#2a78d6;--sh:#0b0b0b;--border:rgba(11,11,11,.12);
 --good:#0ca30c;--warn:#fab219;--crit:#d03b3b;--neutral:#898781;
}
@media (prefers-color-scheme:dark){
 :root:where(:not([data-theme="light"])){
  color-scheme:dark;
  --page:#0d0d0d;--surface:#1a1a19;--ink:#f0efec;--ink2:#c3c2b7;--muted:#9a988f;--grid:#2c2c2a;--axis:#45443f;--band:#232321;
  --s1:#d95926;--s2:#3987e5;--sh:#f0efec;--border:rgba(255,255,255,.12);
 }
}
:root[data-theme="dark"]{
  color-scheme:dark;
  --page:#0d0d0d;--surface:#1a1a19;--ink:#f0efec;--ink2:#c3c2b7;--muted:#9a988f;--grid:#2c2c2a;--axis:#45443f;--band:#232321;
  --s1:#d95926;--s2:#3987e5;--sh:#f0efec;--border:rgba(255,255,255,.12);
}
*{box-sizing:border-box}
html{-webkit-text-size-adjust:100%}
body{margin:0;background:var(--page);color:var(--ink);font-family:"Zen Kaku Gothic New","Hiragino Sans","Hiragino Kaku Gothic ProN","Yu Gothic","Noto Sans CJK JP","Noto Sans JP",system-ui,sans-serif;font-size:15px;line-height:1.7}
.wrap{max-width:1240px;margin:0 auto;padding:18px 14px 90px}
h1{font-size:clamp(22px,4.6vw,32px);line-height:1.3;margin:2px 0 4px}
h2{font-size:19px;margin:0 0 8px;line-height:1.45}
h3{font-size:16px;margin:16px 0 6px}
p{margin:8px 0}
a{color:var(--s2)}
code{font-size:12px;overflow-wrap:anywhere}
.lead{margin:2px 0;font-size:15px}
.note{font-size:13px;color:var(--ink2)}
.src{font-size:11.5px;color:var(--muted);margin:6px 0 0;overflow-wrap:anywhere}
.src code{font-size:11.5px}
.tag{display:inline-block;font-size:12px;font-weight:700;border:1.5px solid var(--ink2);border-radius:6px;padding:0 6px;margin-left:8px;vertical-align:4px;color:var(--ink2)}
.top-row{display:flex;justify-content:space-between;gap:10px;align-items:flex-start}
.btn{font:inherit;font-size:13px;border:1px solid var(--axis);background:var(--surface);color:var(--ink);border-radius:8px;padding:4px 10px;cursor:pointer}
.btn:focus-visible,.hit:focus-visible{outline:3px solid var(--s2);outline-offset:2px}
nav.links{display:flex;flex-wrap:wrap;gap:6px 16px;font-size:14px;margin:6px 0 2px}
.datebox{background:var(--surface);border:1px solid var(--border);border-left:4px solid var(--s2);border-radius:8px;padding:10px 14px;margin:12px 0;font-size:14px}
.datebox b.d{font-size:17px}
section.box,footer.box{background:var(--surface);border:1px solid var(--border);border-radius:12px;padding:14px 16px;margin-top:16px;min-width:0}
.tiles{display:grid;grid-template-columns:repeat(auto-fill,minmax(180px,1fr));gap:8px;margin-top:8px}
.tile{background:var(--surface);border:1px solid var(--border);border-radius:10px;padding:10px 12px;min-width:0}
.tile .k{font-size:12.5px;color:var(--ink2)}
.tile .v{font-size:24px;font-weight:700;line-height:1.25;font-variant-numeric:tabular-nums;overflow-wrap:anywhere}
.tile .s{font-size:12.5px;color:var(--ink2);line-height:1.5}
.tile .src{font-size:10.5px}
.cols2{display:grid;grid-template-columns:repeat(auto-fit,minmax(min(100%,420px),1fr));gap:4px 28px}
.cols3{display:grid;grid-template-columns:repeat(auto-fit,minmax(min(100%,300px),1fr));gap:12px 22px}
.fcol{border-top:3px solid var(--axis);padding-top:4px}
ul.plain{margin:6px 0;padding-left:1.2em}
ul.plain li{margin:4px 0}
ul.checks{list-style:none;margin:6px 0;padding:0}
ul.checks li{display:flex;gap:8px;margin:5px 0;align-items:flex-start}
.box-ic{flex:none;font-size:17px;line-height:1.4;color:var(--ink2)}
.status{border-left:4px solid var(--warn)}
ol.tl{list-style:none;margin:6px 0;padding:0 0 0 14px;border-left:2px solid var(--axis)}
ol.tl li{position:relative;margin:0 0 12px;padding-left:6px}
ol.tl li::before{content:"";position:absolute;left:-21px;top:8px;width:10px;height:10px;border-radius:50%;background:var(--surface);border:2px solid var(--s2)}
.tl-d{font-size:12.5px;color:var(--ink2);font-variant-numeric:tabular-nums}
.tl-n{font-weight:700}
.tl-t{font-size:14px}
.tl .src{margin:0}
.now{display:inline-block;font-size:11.5px;border:1.5px solid var(--s2);color:var(--ink);border-radius:5px;padding:0 5px;margin-left:4px}
.chip{display:inline-flex;align-items:center;gap:4px;white-space:nowrap;font-size:12.5px;font-weight:700;border-radius:999px;padding:1px 9px;border:2px solid;color:var(--ink);background:var(--surface)}
.c-yes{border-color:var(--good)}
.c-part{border-color:var(--warn);border-style:dashed}
.c-no{border-color:var(--neutral)}
.c-rev{border-color:var(--crit);border-style:double;border-width:3px}
.tw{overflow-x:auto}
table{border-collapse:collapse;width:100%;font-size:14px}
th,td{border-bottom:1px solid var(--grid);padding:6px 8px;text-align:left;vertical-align:top}
th{font-size:12.5px;color:var(--ink2);font-weight:700;border-bottom:1px solid var(--axis)}
table.num td{font-variant-numeric:tabular-nums}
tr.sum td{border-top:2px solid var(--axis)}
.chart{position:relative;margin:4px 0}
.chart svg{width:100%;height:auto;display:block}
.chart .tip{position:absolute;pointer-events:none;background:var(--surface);border:1px solid var(--axis);border-radius:8px;padding:4px 8px;font-size:12.5px;white-space:nowrap;box-shadow:0 2px 8px rgba(0,0,0,.12)}
svg text{font-family:inherit}
svg .band{fill:var(--band)}
svg .grid{stroke:var(--grid);stroke-width:1}
svg .axis{stroke:var(--axis);stroke-width:1.5}
svg .ref{stroke:var(--sh);stroke-width:1.5;stroke-dasharray:5 4}
svg .tick{fill:var(--muted);font-size:12px}
svg .eral{fill:var(--ink2);font-size:12px;text-anchor:middle}
svg .lab{fill:var(--ink);font-size:13px;font-weight:700}
svg .ln{fill:none;stroke:var(--s2);stroke-width:2;vector-effect:non-scaling-stroke;stroke-linejoin:round}
svg .dot{fill:var(--s2);stroke:var(--surface);stroke-width:2}
svg .xh{stroke:var(--ink2);stroke-width:1;vector-effect:non-scaling-stroke}
svg .xd{fill:var(--s2);stroke:var(--surface);stroke-width:2}
.cichart{width:100%;max-width:860px;height:auto;display:block;margin:4px 0}
.cichart .rl{fill:var(--ink);font-size:17px}
.cichart .val{fill:var(--ink2);font-size:16px}
.cichart .ci{stroke-width:2}
.cichart .ci.s-1{stroke:var(--s1)} .cichart .ci.s-2{stroke:var(--s2)}
.cichart .pt{stroke:var(--surface);stroke-width:2}
.cichart .pt.s-1{fill:var(--s1)} .cichart .pt.s-2{fill:var(--s2)} .cichart .pt.s-h{fill:var(--sh)}
.cichart .hitbox{fill:transparent}
.cichart .hit:hover .hitbox,.cichart .hit:focus .hitbox{fill:var(--band)}
ul.legend{display:flex;flex-wrap:wrap;gap:4px 18px;list-style:none;padding:0;margin:4px 0;font-size:13px}
.lg{margin-right:5px}
.lg.s-1{color:var(--s1)} .lg.s-2{color:var(--s2)} .lg.s-h{color:var(--sh)}
.figs{display:grid;grid-template-columns:repeat(auto-fill,minmax(min(100%,260px),1fr));gap:12px}
.figs figure{margin:0}
.figs img{width:100%;height:auto;border:1px solid var(--border);border-radius:8px;background:#fff}
.figs figcaption{font-size:12.5px;color:var(--ink2)}
.paper .en{font-style:italic;margin:2px 0;font-size:14px}
.plinks{display:flex;gap:16px;flex-wrap:wrap}
@media (max-width:640px){
 table.res thead{display:none}
 table.res tr{display:block;border-bottom:1px solid var(--axis);padding:4px 0}
 table.res td{display:block;position:relative;border:0;padding:2px 2px 2px 5.4em;min-height:1.6em}
 table.res td::before{content:attr(data-l);position:absolute;left:2px;top:3px;color:var(--ink2);font-size:12px}
 table.num{font-size:12.5px} table.num th,table.num td{padding:5px 4px}
 .tiles{grid-template-columns:repeat(2,minmax(0,1fr))}
 .tile .v{font-size:20px}
 .only-desk{display:none !important}
}
@media (min-width:641px){
 .only-phone{display:none !important}
}
</style>
</head>
<body>
<div class="wrap">
%%BODY%%
</div>
<script>
(function(){
 var root=document.documentElement,btn=document.getElementById('theme');
 try{var s=localStorage.getItem('research-theme');if(s)root.setAttribute('data-theme',s);}catch(e){}
 btn.addEventListener('click',function(){
  var cur=root.getAttribute('data-theme')||(matchMedia('(prefers-color-scheme: dark)').matches?'dark':'light');
  var nx=cur==='dark'?'light':'dark';root.setAttribute('data-theme',nx);
  try{localStorage.setItem('research-theme',nx);}catch(e){}
 });
 document.querySelectorAll('.chart').forEach(function(ch){
  var svg=ch.querySelector('svg'),tip=ch.querySelector('.tip'),pts=JSON.parse(ch.querySelector('.pts').textContent);
  var xh=svg.querySelector('.xh'),xd=svg.querySelector('.xd'),unit=ch.dataset.unit,vb=svg.viewBox.baseVal;
  function show(ev){
   var r=svg.getBoundingClientRect(),x=(ev.clientX-r.left)/r.width*vb.width;
   var best=pts[0];for(var i=1;i<pts.length;i++){if(Math.abs(pts[i][0]-x)<Math.abs(best[0]-x))best=pts[i];}
   xh.setAttribute('x1',best[0]);xh.setAttribute('x2',best[0]);xh.setAttribute('visibility','visible');
   xd.setAttribute('cx',best[0]);xd.setAttribute('cy',best[1]);xd.setAttribute('visibility','visible');
   tip.hidden=false;tip.textContent=best[2]+' ('+best[3]+' 日目・'+best[4]+')  '+best[5].toLocaleString()+unit;
   var px=best[0]/vb.width*r.width,py=best[1]/vb.height*r.height;
   var left=Math.min(Math.max(px-tip.offsetWidth/2,0),r.width-tip.offsetWidth);
   tip.style.left=left+'px';tip.style.top=Math.max(py-tip.offsetHeight-12,0)+'px';
  }
  function hide(){tip.hidden=true;xh.setAttribute('visibility','hidden');xd.setAttribute('visibility','hidden');}
  svg.addEventListener('pointermove',show);svg.addEventListener('pointerleave',hide);
 });
})();
</script>
</body>
</html>
"""

if __name__ == "__main__":
    C = build()
    if "--check" in sys.argv:
        sys.exit(1 if check(C) else 0)
