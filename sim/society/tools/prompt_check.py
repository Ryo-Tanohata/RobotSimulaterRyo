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
G15 の確かめで足したもの (2026-11-15。docs/society_phase/G15_check.md):
- --require 欄,欄: 本文で名前が出ていなくても、答えの形にいつもあるべき欄 (G15 は workshop)
- --base <物差しのお題のフォルダ> [--grow-max バイト]: 同じ名前のお題との大きさのちがい (平均と最大)。--grow-max をこえる人がいれば問題 (G15 は 2560 = +2.5 KB)
- --words <G のモジュール> (例 g15): その G の短い節・長い節 (モジュールの SECTION)・決まりの文の行 (FACT_HEADS) に、書かない言葉 (WORDS) がないか
  (お題の全体には、前からの札の文 (「黒い石」など) が入るので、その G の文だけを見る)
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


def g_parts(text, mod):
    """その G の文 (短い節・長い節・決まりの文の行) をつないだもの (書かない言葉を見るため)"""
    out = []
    body = text[:text.rfind(FORM)] if text.rfind(FORM) >= 0 else text
    m = None
    for mm in BLOCK.finditer(body):
        m = mm
    if m:
        first = re.search(r"^1\. ", body[m.start():], re.M)
        out.append(body[m.start(): m.start() + (first.start() if first else 0)])
    sec = getattr(mod, "SECTION", None)
    if sec and sec in body:
        i = body.index(sec)
        j = body.find("\n## ", i + len(sec))
        out.append(body[i: j if j >= 0 else len(body)])
    for h in getattr(mod, "FACT_HEADS", ()):
        out += [ln for ln in body.splitlines() if ln.startswith(h)]
    return "\n".join(out)


def check_text(text, fields, require=(), words_mod=None):
    """1 通のお題を見る。戻り値: {block, missing, size, placeholders, bad_words}"""
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
    named += [k for k in require if k not in named]
    missing = g7.answer_form_missing(text, named)
    ph = PLACEHOLDER.findall(body)
    bw = [w for w in getattr(words_mod, "WORDS", ()) if w in g_parts(text, words_mod)] if words_mod else []
    return {"block": block, "missing": missing, "named": named, "size": len(text.encode("utf-8")), "placeholders": ph, "bad_words": bw}


def _season_dir(d):
    d = Path(d)
    return d / "season" if (d / "season").is_dir() else d


def check_dir(d, fields, require=(), words_mod=None):
    rows = {}
    for f in sorted(_season_dir(d).glob("*.md")):
        rows[f.stem] = check_text(f.read_text(encoding="utf-8"), fields, require, words_mod)
    return rows


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("dirs", nargs="+", help="お題のフォルダ (prompts/dayN か prompts/dayN/season)")
    ap.add_argument("--quiet", action="store_true", help="まとめの行だけ")
    ap.add_argument("--require", default="", help="答えの形にいつもあるべき欄 (, で区切る。G15 は workshop)")
    ap.add_argument("--base", default=None, help="大きさをくらべる物差しのお題のフォルダ (同じ名前のお題とくらべる)")
    ap.add_argument("--grow-max", type=int, default=None, help="--base とくらべて、ふえてよいバイト (こえる人がいれば問題)")
    ap.add_argument("--words", default=None, help="書かない言葉を見る G のモジュール (例 g15)")
    a = ap.parse_args()
    fields = declared_fields()
    require = [x.strip() for x in a.require.split(",") if x.strip()]
    words_mod = importlib.import_module(a.words) if a.words else None
    base = {f.stem: len(f.read_bytes()) for f in sorted(_season_dir(a.base).glob("*.md"))} if a.base else {}
    bad = 0
    for d in a.dirs:
        rows = check_dir(d, fields, require, words_mod)
        if not rows:
            print(f"{d}: お題がない")
            continue
        n = len(rows)
        blk = {k: sum(1 for r in rows.values() if r["block"] == k) for k in ("OK", "なし", "位置ちがい")}
        miss = sorted({k for r in rows.values() for k in r["missing"]})
        ph = sum(1 for r in rows.values() if r["placeholders"])
        sizes = [r["size"] for r in rows.values()]
        bw = sorted({w for r in rows.values() for w in r["bad_words"]})
        grow = {k: r["size"] - base[k] for k, r in rows.items() if k in base}
        over = sorted(k for k, v in grow.items() if a.grow_max is not None and v > a.grow_max)
        problem = bool(miss or ph or blk["位置ちがい"] or (blk["なし"] and blk["OK"]) or bw or over or (require and blk["OK"] < n))
        bad += problem
        print(f"## {d}: 答える人 {n} / 短い節 OK {blk['OK']}・なし {blk['なし']}・位置ちがい {blk['位置ちがい']} / "
              f"答えの形にない欄 {'・'.join(miss) or 'なし'} / 例の「…」のあるお題 {ph} / 大きさ 平均 {sum(sizes) // n:,} バイト (最小 {min(sizes):,}・最大 {max(sizes):,})"
              + (f" / 物差しとのちがい 平均 {sum(grow.values()) / len(grow):+,.0f}・最大 {max(grow.values()):+,} バイト ({len(grow)} 通"
                 + (f"。{a.grow_max:,} をこえた人 {'・'.join(over)}" if over else "") + ")" if grow else "")
              + (f" / 書かない言葉 ({a.words}) {'・'.join(bw) or 'なし'}" if words_mod else "")
              + (" → 見直す" if problem else " → OK"))
        if not a.quiet:
            for name, r in rows.items():
                print(f"  {name}: 短い節 {r['block']} / 欄 {'ない ' + '・'.join(r['missing']) if r['missing'] else 'そろう (' + ('・'.join(r['named']) or '名前の出た欄なし') + ')'} / "
                      f"{r['size']:,} バイト" + (f" ({r['size'] - base[name]:+,})" if name in base else "") + f" / 「…」 {len(r['placeholders'])}"
                      + (f" ({' '.join(sorted(set(r['placeholders'])))})" if r["placeholders"] else "")
                      + (f" / 書かない言葉 {'・'.join(r['bad_words'])}" if r["bad_words"] else ""))
    sys.exit(1 if bad else 0)


if __name__ == "__main__":
    main()
