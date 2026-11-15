"""お題を読む確かめ (第 8 部の前の方法の直し 4。docs/society_phase/method_fixes_part8.md。トークン 0・読むだけ)

  PYTHONUTF8=1 python3.13 sim/society/tools/prompt_check.py sim/society/data/prompts/day23159 [day22559 ...] [--quiet]

第 7 部の学び 7: 決まりの村はお題を読まないので、「答えの形に欄がない」「例の名前が …」のような、お題の形のまちがいは見つけられない。
そこで、本物のお題のフォルダ (prompts/dayN) を読んで、答える人ごとに次を出す:
- 短い節: G の短い節 (「…: この集まりで、あなた (名前) ができること」) が「## いま」のあと、答えの並び (「1. 」) のすぐ前にあるか
  (OK / なし / 位置ちがい)。G12〜G14 のどの節でも見る (見出しの形で探す)
- 欄: G の答えの欄 (g9〜g14 と、これから足す G の ANSWER_FIELDS の名前) のうち、お題の本文 (答えの形より前) で名前が出ているものが、
  「## 答えの形 (JSON)」にみなあるか。ないものの名前
- 大きさ: お題のバイト数
- 「…」: 本文の例に、名前や中身の代わりの「…」 ("…"・「…」・[…]・"...") があるか (答えの形の "..." は書き方の決まりなので数えない。
  例の中でも、自由に書く文の欄 (why・text・reason・feeling・for・against) の "..." は数えない)
まとめの行と、答える人ごとの行を出す。どこかに問題があれば 1 で終わる (なければ 0)。
"""
import argparse
import importlib
import re
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
SOC = HERE.parent
sys.path.insert(0, str(SOC))

FORM = "## 答えの形 (JSON)"
NOW = "## いま"
BLOCK = re.compile(r"^[^\n#]*: この集まりで、あなた \([^)]*\) ができること", re.M)
PLACEHOLDER = re.compile(r'"…"|「…」|\[…\]|(?<!"why": )(?<!"text": )(?<!"reason": )(?<!"feeling": )(?<!"for": )(?<!"against": )"\.\.\."')
# 書けと言っている欄: 「## いま」より後の、"欄":・(欄。・(欄)・欄 に・欄 を・欄 は の形 (決まりの文の中の名前や、「年の集まりの答え (market_day・…) で決める」は数えない)
TOLD = r'(?:"{k}":|\({k}[。)]|(?<![A-Za-z_]){k} ?[にをは])'


def declared_fields():
    """G の答えの欄の名前 (各 G の ANSWER_FIELDS を読む。これから足す G もファイルがあれば)"""
    import g7
    out = []
    for name in ("g9", "g11", "g12", "g14") + tuple(g7.LATER_GS):
        try:
            m = importlib.import_module(name)
        except ImportError:
            continue
        for k in getattr(m, "ANSWER_FIELDS", {}) or {}:
            if k not in out:
                out.append(k)
    return out


def check_text(text, fields):
    """1 通のお題を見る。戻り値: {block, missing, size, placeholders}"""
    import g7
    i_form = text.rfind(FORM)
    body = text[:i_form] if i_form >= 0 else text
    i_now = body.rfind(NOW)
    block = "なし"
    m = None
    for mm in BLOCK.finditer(body):
        m = mm
    if m:
        first = re.search(r"^1\. ", body[m.start():], re.M)
        between = body[m.start(): m.start() + first.start()] if first else ""
        block = "OK" if (i_now >= 0 and m.start() > i_now and first and "\n## " not in between) else "位置ちがい"
    after = body[i_now:] if i_now >= 0 else body
    named = [k for k in fields if re.search(TOLD.format(k=re.escape(k)), after)]
    missing = g7.answer_form_missing(text, named)
    ph = PLACEHOLDER.findall(body)
    return {"block": block, "missing": missing, "named": named, "size": len(text.encode("utf-8")), "placeholders": ph}


def check_dir(d, fields):
    d = Path(d)
    sd = d / "season" if (d / "season").is_dir() else d
    rows = {}
    for f in sorted(sd.glob("*.md")):
        rows[f.stem] = check_text(f.read_text(encoding="utf-8"), fields)
    return rows


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("dirs", nargs="+", help="お題のフォルダ (prompts/dayN か prompts/dayN/season)")
    ap.add_argument("--quiet", action="store_true", help="まとめの行だけ")
    a = ap.parse_args()
    fields = declared_fields()
    bad = 0
    for d in a.dirs:
        rows = check_dir(d, fields)
        if not rows:
            print(f"{d}: お題がない")
            continue
        n = len(rows)
        blk = {k: sum(1 for r in rows.values() if r["block"] == k) for k in ("OK", "なし", "位置ちがい")}
        miss = sorted({k for r in rows.values() for k in r["missing"]})
        ph = sum(1 for r in rows.values() if r["placeholders"])
        sizes = [r["size"] for r in rows.values()]
        problem = bool(miss or ph or blk["位置ちがい"] or (blk["なし"] and blk["OK"]))
        bad += problem
        print(f"## {d}: 答える人 {n} / 短い節 OK {blk['OK']}・なし {blk['なし']}・位置ちがい {blk['位置ちがい']} / "
              f"答えの形にない欄 {'・'.join(miss) or 'なし'} / 例の「…」のあるお題 {ph} / 大きさ 平均 {sum(sizes) // n:,} バイト (最小 {min(sizes):,}・最大 {max(sizes):,})"
              + (" → 見直す" if problem else " → OK"))
        if not a.quiet:
            for name, r in rows.items():
                print(f"  {name}: 短い節 {r['block']} / 欄 {'ない ' + '・'.join(r['missing']) if r['missing'] else 'そろう (' + ('・'.join(r['named']) or '名前の出た欄なし') + ')'} / "
                      f"{r['size']:,} バイト / 「…」 {len(r['placeholders'])}" + (f" ({' '.join(sorted(set(r['placeholders'])))})" if r["placeholders"] else ""))
    sys.exit(1 if bad else 0)


if __name__ == "__main__":
    main()
