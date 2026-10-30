#!/usr/bin/env python3
"""出典の一覧を作る。読むだけ (研究ノートは変えない)。LLM なし。

  python3.13 sim/society/tools/build_references.py          # references.json の notes と docs/research/references.md を作り直す
  python3.13 sim/society/tools/build_references.py --check  # 作り直して、文書に出てくる「名前 年」がみな一覧にあるか確かめる

材料:
  - sim/society/tools/references.json の entries (手で書く。本人の研究・論文や本・ゲームや道具や声・使った AI)
  - 研究ノートの文献の欄 (SECTIONS) の 1 行ずつ → notes (機械で集める。文はそのまま写す。書き足さない)
  - 研究ノートの本文に出てくる「名前 年」(例: Johnson 1982) → どの文書で使ったか (used_in)。文献の欄にない名前は「名前と年だけ」の notes
"""
import glob
import hashlib
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
REG = Path(__file__).with_name("references.json")
MD = ROOT / "docs/research/references.md"

# 文献の欄: (ファイル, 見出し, どう入ったか)
SECTIONS = [
    ("docs/research/archaeological_evidence.md", "## 8. 出典",
     "Claude がウェブ検索で調べた (2026-10-09。同じ日に別の目で確かめなおした)。論文の多くは開けず、要旨・目録・大学の発表・報道で読んだ"),
    ("docs/research/historical_records.md", "## 7. 出典",
     "Claude がウェブ検索で調べた (2026-10-09)。元の本や論文の多くは開けず、紹介文・目録・まとめから書いた"),
    ("docs/research/economic_lenses.md", "## 8. 参考文献",
     "Claude がウェブ検索で調べた (2026-10-14)。多くは要旨か紹介で読んだ"),
    ("docs/research/modern_records.md", "### 8.2 出典一覧",
     "Claude がウェブ検索で調べた (2026-10-09)。「(一般知識)」とあるものは確かめなおしていない"),
    ("docs/research/society2_periodization.md", "## 6. 主な出典",
     "Claude がウェブ検索で調べた (2026-10-08)。検索の上限のため、いくつかは記憶だけ"),
    ("docs/research/civilization_tech_tree.md", "## 6. 参考",
     "Claude がウェブ検索で調べた (2026-10-07)。ページは開けず、検索結果の要約を使った"),
    ("docs/society_phase/G6_design.md", "## 23. Literature",
     "Claude がウェブ検索で調べた (2026-10-09)。全文の多くは開けず、要旨・出版社の記録・書評で照らした"),
    ("docs/society_phase/G7_design.md", "## 9. 参考文献",
     "Claude の調べ (2026-10-16)。計画書 docs/society2_extension_plan.md の文献から。紹介だけ読んだものは【記憶】"),
    ("docs/tech_tree_design_draft.md", "## 出典 (主なもの)",
     "Claude がウェブ検索で調べた (2026-10-09)"),
]

# 本文の「名前 年」を探す文書
SCAN = sorted(set(glob.glob(str(ROOT / "docs/research/**/*.md"), recursive=True)
                  + glob.glob(str(ROOT / "docs/society_phase/*.md"))
                  + glob.glob(str(ROOT / "docs/tech_tree*.md"))))
SCAN = [str(Path(p).relative_to(ROOT)) for p in SCAN if not p.endswith("references.md")]
SCAN += ["sim/society/techtree/plan.json", "sim/society/tools/research_dashboard_content.json"]

SUR = r"(?:(?:van der |Van |de |De |Le |Al|Mc|Mac|O')?[A-Z][a-zà-öø-ÿ'’\-]+(?:-[A-Z][a-zà-öø-ÿ\-]+)?)"
PAT = re.compile(r"(%s)((?:,? (?:&|and) %s|, %s)*)(?: (?:ほか|et al\.?|ら))?,? \(?((?:1[4-9]|20)\d\d)[a-z]?(?:/\d\d)?(?![\d\-–])" % (SUR, SUR, SUR))
# 名前に見えるが人の名前ではないもの (雑誌・場所・言葉)
STOP = set("""Claude Income Society Science Nature Antiquity Paléorient Journal Current Civ Civilization January February March April
May June July August September October November December Version Python Haiku Sonnet Opus Table Figure Season Year Day Phase Step Part
Chapter Volume Vol Section Appendix Model Plan Note The In On At By From With Mind Total Run Game Zenodo Before After Since Around About
Late Early Middle Uruk Ubaid Halaf Neolithic Bronze Iron Holocene Pleistocene Younger Seshat Our World Data Bank Wikipedia Oxford
Cambridge Harvard Chicago Yale Press University Review Quarterly American Proceedings Annual Trends Political Psychological Behavioral
Economic Population Human Animal Quaternary Vegetation Levant Iraq Syria Turkey Israel Jordan Iran Egypt China Japan Europe Anatolia
Mesopotamia Sumer Akkad Kish Lagash Susa Jericho Gawra Brak Arslantepe Eridu Nippur Mari Ebla Babylon Assyria England Reconstitution
Gazette Diseases Methods Brief Index Stat Gs Tepe Fails Weingarten's Crae Kerrell Boer Qahtani Kuhn West Brun Mahon Gopher Dixon Cann
Report Census Atlas Survey Act Law Code Statute Domesday Register Registers Office National Parish Global Burden Health Life""".split())
FIX = {"Crae": "McCrae", "Kerrell": "McKerrell", "Mahon": "McMahon", "Boer": "DeBoer", "Qahtani": "AlQahtani"}


def rd(rel):
    return (ROOT / rel).read_text(encoding="utf-8")


def keys_in(text):
    out = []
    for m in PAT.finditer(text):
        a = m.group(1).strip()
        a = re.sub(r"^(?:van der |Van |de |De |Le |O')", "", a) if a.split(" ")[0] in ("van", "Van", "de", "De", "Le") else a
        if a in STOP or int(m.group(3)) > 2026:
            continue
        out.append((a, m.group(3), m.start(), m.end()))
    return out


PAT2 = re.compile(r"(?:^|[.;。・] |\*|\b)(%s), (?:[A-ZÀ-Ý][a-zà-ÿ]*\.?[- ]?){1,3}[^0-9\n]{0,160}?\(?((?:1[4-9]|20)\d\d)[a-z]?(?:/\d\d)?(?![\d\-–])" % SUR)


def keys_in_line(text):
    """文献の行の「名前 年」: 本文の形 (Johnson 1982) と、書誌の形 (Johnson, G. A. 1982) の両方。"""
    out = keys_in(text)
    for m in PAT2.finditer(text):
        a = m.group(1).strip()
        if a in STOP or int(m.group(2)) > 2026:
            continue
        out.append((a, m.group(2), m.start(1), m.end()))
    out.sort(key=lambda k: k[2])
    return out


def norm(k):
    return (k[0].lower().replace("ü", "u").replace("é", "e").replace("á", "a"), k[1])


def section_lines(rel, head):
    t = rd(rel)
    i = t.index(head)
    rest = t[i + len(head):]
    m = re.search(r"\n## ", rest)
    body = rest[:m.start()] if m else rest
    out = []
    for line in body.splitlines():
        m = re.match(r"\s*(?:[-*]|\d+\.) (.*)", line)
        if not m:
            continue
        s = m.group(1).strip()
        if len(s) < 12 or (not re.search(r"\d{4}|https?://", s)):
            continue  # 見出しだけの行
        out.append(s)
    return out


def build():
    reg = json.loads(REG.read_text(encoding="utf-8"))
    entries = reg["entries"]
    ck = {}  # 手で書いた entries の「名前 年」
    for e in entries:
        for a, y in e.get("keys", []):
            ck[norm((a, y))] = e

    # 本文の「名前 年」がどの文書にあるか。【記憶】がその行にあるか
    where, memo = {}, set()
    for rel in SCAN:
        for line in rd(rel).splitlines():
            for a, y, s, e_ in keys_in(line):
                k = norm((a, y))
                where.setdefault(k, {"name": "%s %s" % (FIX.get(a, a), y), "files": []})
                if rel not in where[k]["files"]:
                    where[k]["files"].append(rel)
                if "【記憶】" in line[s:s + 160] or "(memory" in line[s:s + 160]:
                    memo.add(k)

    notes, by_key = [], {}
    for rel, head, how in SECTIONS:
        for s in section_lines(rel, head):
            ks = keys_in_line(s)
            urls = re.findall(r"https?://[^\s)）,]+", s)
            doi = re.search(r"(?:doi:|doi\.org/)(10\.[^\s)）,]+)", s)
            prim = norm(ks[0][:2]) if ks else None
            if prim and prim in ck:
                e = ck[prim]
                if rel not in e["used_in"]:
                    e["used_in"].append(rel)
                continue
            if prim and prim in by_key:
                n = by_key[prim]
                n["also"].append({"file": rel, "text": s})
                if rel not in n["used_in"]:
                    n["used_in"].append(rel)
                continue
            label = ("%s %s" % (FIX.get(ks[0][0], ks[0][0]), ks[0][1])) if ks else re.split(r"[:：（(]", s)[0].strip()[:60]
            nid = "n-" + hashlib.md5((label + s).encode()).hexdigest()[:8]
            n = {"id": nid, "label": label, "citation": s, "url": urls[0] if urls else "", "doi": doi.group(1) if doi else "",
                 "entered": how, "status": "no", "marks": [], "used_in": [rel], "also": [],
                 "keys": [list(k[:2]) for k in ks]}
            if "【未確認】" in s:
                n["marks"].append("【未確認】")
            if "【記憶】" in s or "(memory" in s:
                n["marks"].append("【記憶】")
            if "【議論あり】" in s:
                n["marks"].append("【議論あり】")
            notes.append(n)
            if prim:
                by_key[prim] = n
    # 行の中の 2 つ目からの「名前 年」も、その行の entry につなぐ
    sec = {}
    for n in notes:
        for k in n["keys"]:
            sec.setdefault(norm(tuple(k)), n)
    # 本文で使った文書を足す
    for k, w in where.items():
        tgt = ck.get(k) or by_key.get(k) or sec.get(k)
        if tgt is None:
            n = {"id": "k-" + re.sub(r"[^a-z0-9]", "", w["name"].lower()), "label": w["name"],
                 "citation": "%s (研究ノートの本文に名前と年だけが出てくる。書誌の行はない)" % w["name"],
                 "url": "", "doi": "", "entered": "Claude の研究ノートの本文 (下地の知識か、その文書の調べ)", "status": "no",
                 "marks": ["名前と年だけ"], "used_in": list(w["files"]), "also": [], "keys": [list(k)], "inline_only": True}
            notes.append(n)
            by_key[k] = n
            tgt = n
        for f in w["files"]:
            if f not in tgt["used_in"]:
                tgt["used_in"].append(f)
        if k in memo and "【記憶】" not in tgt.get("marks", []) and tgt.get("status") != "ok":
            tgt.setdefault("marks", []).append("【記憶】")
    for n in notes:
        n.pop("keys", None)
        n["used_in"].sort()
    notes.sort(key=lambda n: (n.get("inline_only", False), n["label"].lower()))
    reg["notes"] = notes
    reg["counts"] = counts(reg)
    REG.write_text(json.dumps(reg, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
    MD.write_text(markdown(reg), encoding="utf-8")
    print("wrote", REG.relative_to(ROOT), "entries", len(entries), "notes", len(notes))
    print("wrote", MD.relative_to(ROOT))
    return reg


def counts(reg):
    c = {"entries": len(reg["entries"]), "notes": len(reg["notes"]),
         "ok": 0, "no": 0, "warn": 0, "by_group": {}}
    for e in reg["entries"]:
        c[e["status"]] += 1
        g = c["by_group"].setdefault(e["group"], {"ok": 0, "no": 0, "warn": 0})
        g[e["status"]] += 1
    c["notes_no"] = sum(1 for n in reg["notes"] if n["status"] == "no")
    c["notes_name_only"] = sum(1 for n in reg["notes"] if n.get("inline_only"))
    c["notes_memory"] = sum(1 for n in reg["notes"] if "【記憶】" in n.get("marks", []))
    c["notes_unconfirmed"] = sum(1 for n in reg["notes"] if "【未確認】" in n.get("marks", []))
    return c


ST = {"ok": "✓ 確かめた", "no": "✗ 確かめていない", "warn": "⚠ 食い違い"}


def markdown(reg):
    c = reg["counts"]
    g = {x["id"]: x["name"] for x in reg["groups"]}
    L = []
    A = L.append
    A("# 参考にした研究と出典")
    A("")
    A("このプロジェクトが外から持ってきたもの (本人の修士論文・人の論文や本・ゲーム・道具・声・AI) の一覧です。"
      "このファイルは `python3.13 sim/society/tools/build_references.py` が作ります (手で直すのは "
      "`sim/society/tools/references.json` の entries だけ)。まとめた日: %s。" % reg["asof"])
    A("")
    A("## 読み方")
    A("")
    A("- **✓ 確かめた**: 書誌 (だれが・いつ・題・どこに出たか) を、本や雑誌の記録・DOI・図書館の目録と照らした。いつ、どこで照らしたかを書いた。")
    A("- **✗ 確かめていない**: まだ照らしていない。名前や中身は、Claude の記憶 (【記憶】) か、研究ノートを書いたときの調べ (要旨・紹介) のまま。")
    A("- **⚠ 食い違い**: 照らしたら、書いてあることと合わなかった。")
    A("- 書誌が分からないものは、作らずに「分かることだけ」を書いた。研究ノートの文献の行は、文のまま写した。")
    A("- ダッシュボード (`sim/society/app/research.html`) では、外から持ってきた研究に〔 〕の印をつけ、この一覧につないでいる。")
    A("")
    A("## 数")
    A("")
    A("| | 件数 | ✓ | ✗ | ⚠ |")
    A("|---|---|---|---|---|")
    for gid in ("self", "works", "tools", "ai"):
        x = c["by_group"].get(gid, {"ok": 0, "no": 0, "warn": 0})
        A("| %s | %d | %d | %d | %d |" % (g[gid], sum(x.values()), x["ok"], x["no"], x["warn"]))
    A("| **手で書いた一覧の合計** | **%d** | **%d** | **%d** | **%d** |" % (c["entries"], c["ok"], c["no"], c["warn"]))
    A("| 研究ノートの文献 (機械で集めた) | %d | 0 | %d | 0 |" % (c["notes"], c["notes_no"]))
    A("")
    A("研究ノートの文献 %d 件のうち、【未確認】の印 %d・【記憶】の印 %d・名前と年だけ (書誌の行がない) %d。"
      "これらは、ノートを書いたときに要旨や紹介で読んだものが多いが、この一覧を作るときには確かめなおしていない (✗)。"
      % (c["notes"], c["notes_unconfirmed"], c["notes_memory"], c["notes_name_only"]))
    A("")
    for gid in ("self", "works", "tools", "ai"):
        A("## %s" % g[gid])
        A("")
        for e in reg["entries"]:
            if e["group"] != gid:
                continue
            A("### %s 〔%s〕" % (ST[e["status"]], e["label"]))
            A("")
            A("- **書誌**: %s" % e["citation"])
            if e.get("doi"):
                A("- **DOI**: https://doi.org/%s" % e["doi"])
            if e.get("url"):
                A("- **URL**: %s" % e["url"])
            A("- **種類**: %s" % e["type"])
            A("- **どんなものか**: %s" % e["what"])
            A("- **何に使ったか**: %s" % e["used_for"])
            if e.get("not_used"):
                A("- **使っていないもの**: %s" % e["not_used"])
            if e.get("consent"):
                A("- **2016 年の約束**: %s" % e["consent"])
            A("- **どう入ったか**: %s" % e["entered"])
            A("- **確かめ**: %s — %s" % (ST[e["status"]], e["checked"]))
            if e.get("note"):
                A("- **注**: %s" % e["note"])
            A("- **使った所**: %s" % "・".join("`%s`" % u for u in e["used_in"]))
            A("")
    A("## 研究ノートの文献 (機械で集めた。みな ✗ 確かめていない)")
    A("")
    A("研究ノート (`docs/research/`・`docs/society_phase/`・`docs/tech_tree*.md`・`sim/society/techtree/plan.json`) が文献の欄に書いた行と、"
      "本文に名前と年だけが出てくるものです。文はノートのまま写しました。上の手で書いた一覧と同じものは、上にまとめました。")
    A("")
    A("どう入ったか (文献の欄ごと):")
    A("")
    for rel, head, how in SECTIONS:
        A("- `%s` の「%s」: %s" % (rel, head.lstrip("# "), how))
    A("- 名前と年だけのもの: 研究ノートの本文 (Claude の下地の知識か、その文書の調べ)。書誌の行がないので、書誌は書いていない")
    A("")
    A("| # | 名前 | 書誌 (ノートのまま) | 印 | 使った所 |")
    A("|---|---|---|---|---|")
    for i, n in enumerate(reg["notes"], 1):
        cit = n["citation"].replace("|", "\\|")
        if n["also"]:
            cit += " (ほかの書き方 %d)" % len(n["also"])
        A("| %d | %s | %s | ✗ %s | %s |" % (i, n["label"].replace("|", "\\|"), cit, " ".join(n["marks"]),
                                           "・".join("`%s`" % u for u in n["used_in"])))
    A("")
    return "\n".join(L) + "\n"


def check(reg):
    """研究ノートの本文に出てくる「名前 年」が、みな一覧にあるか。"""
    have = set()
    for e in reg["entries"]:
        for k in e.get("keys", []):
            have.add(norm(tuple(k)))
    for n in reg["notes"]:
        for m in keys_in_line(n["citation"] + " " + n["label"]):
            have.add(norm(m[:2]))
    bad = 0
    for rel in SCAN:
        for a, y, s, e in keys_in(rd(rel)):
            if norm((a, y)) not in have:
                bad += 1
                print("  一覧にない:", a, y, rel)
    print("一覧にない「名前 年」:", bad)
    return bad


if __name__ == "__main__":
    reg = build()
    if "--check" in sys.argv:
        sys.exit(1 if check(reg) else 0)
