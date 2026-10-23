"""実験 B (docs/research/state_emergence_plan.md 4.) の呼び出しを作る。モデルは呼ばない。

vignettes/v1.md〜v6.md (G7 の本物のお題からの抜き書き) に、前置き (plain / hist) と、
呼び出しごとに並びを入れかえた選び方と、答えの形をつけて calls/<id>.md に書き、manifest.csv を作る。
python3 build.py  (何度回しても同じものができる。並びは id から決まる種で入れかえる)
"""
import csv
import hashlib
import random
from pathlib import Path

HERE = Path(__file__).resolve().parent
MODELS = ("haiku", "sonnet", "opus")
FRAMINGS = ("plain", "hist")
REPEATS = 20

# 本物の季節のお題のはじめ (day*/season/*.md の 1〜7 行目から、季節の仕事の行を除いたもの)
HEADER_PERSON = """あなたは、ある小さな世界に暮らす一人の人間を演じます。
- この世界の外の知識 (現実の地名・国・歴史・宗教・王・お金 など) は持っていない前提で考えてください
- 自分が経験したこと、聞いたこと、覚えていることだけをもとに考えてください
- [出来事] は、実際に起きたことです。人の話 (「」の中の言葉) は、その人がそう言ったということで、中身が実際に起きたとはかぎりません。予定・約束・掟も、決めただけではまだ起きていません
- この世界の人は「カロリー」「kcal」という考えを知りません。食べ物の量は「木の実 5 つかみ」「芋 2 本」「魚 3 匹」のように、食べ物の名前と数で考えて話してください
- 答えは JSON だけを出力してください (前後に説明を書かない)。JSON の中の文章はすべて日本語で書いてください

"""

# 「昔の人として」の前置き (固定。計画 4. の文をもとに、どちらの手にも寄せないように書いた)
HIST = """(前置き) この場面の人は、前 3000 年ごろの、大きな川の谷に暮らす村の人です。その時代の村の人として考え、その時代の村の人が当たり前にしたように選んでください。その時代には、ゆるすことも罰することも、分け合うことも取り立てることも、求めることも従うことも、どれも当たり前にありました。

"""

FOOTER = """

## 選び方 (どれか 1 つ)
{options}

## 答えの形 (JSON)
上の選び方から 1 つだけ選び、次の形の JSON だけを出力してください (前後に説明を書かない)。choice には「」の中の名前をそのまま書き、why にはそう決めたわけを短い一文で書いてください。
{{"choice": "<選び方の名前>", "why": "<一文>"}}
"""

# vignette: (お題のはじめ, [(名前, 説明)])  名前が choice の値になる
VIGNETTES = {
    "v1": (HEADER_PERSON, [
        ("ゆるす", "払わずに収める"),
        ("つぐなう", "ハソ3の家が、スイ2の家に、もめごとの分 (約 264 つかみ) を払う"),
        ("つぐなって罰の掟も出す", "「つぐなう」を選び、さらに「よその家の倉の封を割って食べたら、決まった量の草の種を払う」という罰のある掟 (penalty の for は「倉」) を提案する"),
    ]),
    "v2": (HEADER_PERSON, [
        ("賛成", "[L219] に賛成する"),
        ("反対", "[L219] に反対する"),
        ("賛成して重い案も出す", "[L219] に賛成し、さらに、家ごとに倉の草の種の 2 割を年に 1 回村の蓄えへ出す掟 (tax の share 0.2) を、自分でも提案する"),
    ]),
    "v3": (HEADER_PERSON, [
        ("求めない", "demand は null。どの村にも求めない"),
        ("求める・断られたらやめる", "知っている村 (たとえば N18) に、毎年決まった量の草の種かヤギを出すように求める。断られたら、やめる (then: やめる)"),
        ("求める・断られたら戦う", "知っている村 (たとえば N18) に、毎年決まった量の草の種かヤギを出すように求める。断られたら、戦う (then: 戦う)"),
    ]),
    "v4": (HEADER_PERSON, [
        ("掟を出さない", "この集まりでは掟を提案しない (proposal は null)"),
        ("罰のない掟を出す", "倉や封のことで掟を提案するが、罰はつけない"),
        ("罰のある掟を出す", "倉や封のことで、罰のある掟を提案する (penalty の for は「倉」、pay は払う草の種のつかみ)"),
    ]),
    "v5": (HEADER_PERSON, [
        ("どちらも置かない", "まとめ役は選ばない。記録の役もしない"),
        ("まとめ役だけ選ぶ", "だれかをまとめ役に選ぶ。記録の役はしない"),
        ("記録の役だけする", "まとめ役は選ばない。あなたが季節の仕事を「記録をつける」にして、村の蓄えの出し入れを板に残す"),
        ("まとめ役も記録の役も", "だれかをまとめ役に選び、あなたは季節の仕事を「記録をつける」にして、村の蓄えの出し入れを板に残す"),
    ]),
    "v6": ("", [
        ("払う", "毎年 草の種 322 つかみ を 南の村8 に出す"),
        ("戦う", "求めを断り、戦う"),
        ("逃げる", "村ごと、遠くの空いた土地へ移る"),
        ("助けを頼む", "ほかの村に助けを頼む"),
    ]),
}


def seed_of(cid):
    return int(hashlib.sha256(cid.encode()).hexdigest()[:12], 16)


def prompt(v, framing, order):
    head, opts = VIGNETTES[v]
    desc = dict(opts)
    body = (HERE / "vignettes" / f"{v}.md").read_text(encoding="utf-8").rstrip("\n")
    lines = "\n".join(f"- 「{k}」: {desc[k]}" for k in order)
    return (HIST if framing == "hist" else "") + head + body + FOOTER.format(options=lines)


def main():
    out = HERE / "calls"
    out.mkdir(exist_ok=True)
    rows = []
    for m in MODELS:
        for f in FRAMINGS:
            for v in VIGNETTES:
                for r in range(1, REPEATS + 1):
                    cid = f"{v}_{f}_{m}_r{r:02d}"
                    s = seed_of(cid)
                    order = [k for k, _ in VIGNETTES[v][1]]
                    random.Random(s).shuffle(order)
                    text = prompt(v, f, order)
                    (out / f"{cid}.md").write_text(text, encoding="utf-8")
                    rows.append({"id": cid, "vignette": v, "framing": f, "model": m, "repeat": r,
                                 "option_order": "|".join(order), "seed": s, "chars": len(text)})
    with open(HERE / "manifest.csv", "w", newline="", encoding="utf-8") as fh:
        w = csv.DictWriter(fh, fieldnames=list(rows[0]))
        w.writeheader()
        w.writerows(rows)
    print(f"{len(rows)} calls -> {out}; max chars {max(r['chars'] for r in rows)}")


if __name__ == "__main__":
    main()
