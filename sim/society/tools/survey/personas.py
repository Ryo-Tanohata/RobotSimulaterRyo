"""論文 2・実験 1: 答える人 (LLM) の人格をくじで作る。乱数の種を決めてあるので、何度動かしても同じになる。

    python3 personas.py            # personas.json を書く (C1 と C2 で同じ 100 人を使う)

決め (くわしくは docs/research/humanity/paper2_exp1_prereg.md の 4.):
- ビッグファイブ 5 つ (外向性 E・協調性 A・誠実性 C・神経症傾向 N・開放性 O) を、標準正規分布の z で持たせる。
  5 つの間の相関は 0 (独立) とする。大人の相関の表 (van der Linden ほか 2010 のメタ分析) を使いたかったが、
  このセッションでは数を確かめられなかった (表の載ったページに届かなかった)。確かめた表が手に入ったら、
  CORR に入れれば同じ手順で相関のある多変量正規分布から引ける (CORR を変えると人格はみな変わる)。
- 見せるための MBTI ふうの 4 文字 + -A / -T は、z の符号から決める (人格の中身ではなく、ラベルだけ)。
  E/I ← 外向性、N/S ← 開放性、F/T ← 協調性、J/P ← 誠実性、-T/-A ← 神経症傾向。
  この対応は McCrae & Costa (1989) の、MBTI の 4 つの軸とビッグファイブの相関の向きに合わせた【記憶】。
- 年齢・性別・都道府県は【仮定】(修士論文の 84 人は知り合いで 10 代以上、ということしか分からない)。
"""
import json
import os

import numpy as np

SEED = 20261029
N_PERSONAS = 100
TRAITS = ["E", "A", "C", "N", "O"]
TRAIT_JA = {"E": "外向性", "A": "協調性", "C": "誠実性", "N": "神経症傾向", "O": "開放性"}
# 5 つの間の相関 (いまは単位行列 = 独立)。並びは TRAITS と同じ
CORR = np.eye(5)

# 年代の重み【仮定】: 10 代は 18〜19 歳だけ。知り合いを中心に集めた調査なので、20〜50 代を厚くした
AGE_BANDS = [((18, 19), 0.05), ((20, 29), 0.20), ((30, 39), 0.25), ((40, 49), 0.25), ((50, 59), 0.15), ((60, 69), 0.10)]
SEXES = [("男性", 0.5), ("女性", 0.5)]
# 都道府県は人口の重みで引く。人口は 2020 年の国勢調査のおよその数 (万人)【記憶】
PREF_POP = [
    ("北海道", 522), ("青森県", 124), ("岩手県", 121), ("宮城県", 230), ("秋田県", 96), ("山形県", 107), ("福島県", 183),
    ("茨城県", 287), ("栃木県", 193), ("群馬県", 194), ("埼玉県", 734), ("千葉県", 628), ("東京都", 1405), ("神奈川県", 924),
    ("新潟県", 220), ("富山県", 103), ("石川県", 113), ("福井県", 77), ("山梨県", 81), ("長野県", 205), ("岐阜県", 198),
    ("静岡県", 363), ("愛知県", 754), ("三重県", 177), ("滋賀県", 141), ("京都府", 258), ("大阪府", 884), ("兵庫県", 547),
    ("奈良県", 133), ("和歌山県", 92), ("鳥取県", 55), ("島根県", 67), ("岡山県", 189), ("広島県", 280), ("山口県", 134),
    ("徳島県", 72), ("香川県", 95), ("愛媛県", 133), ("高知県", 69), ("福岡県", 514), ("佐賀県", 81), ("長崎県", 131),
    ("熊本県", 174), ("大分県", 112), ("宮崎県", 107), ("鹿児島県", 159), ("沖縄県", 147),
]

# z → 5 段階の言葉 (人の中で下から 10%・30%・70%・90% の区切り)
CUTS = [-1.2816, -0.5244, 0.5244, 1.2816]
LEVELS = ["とても低い", "低め", "ふつう", "高め", "とても高い"]
# 高い / 低いときの説明 (プロンプトに書く)
DESC = {
    "E": ("ひとりで静かに過ごすのを好み、人づきあいは控えめ", "人と話すのが好きで、にぎやかな場を楽しむ"),
    "A": ("自分の考えをはっきり通し、人に合わせることは少ない", "人を思いやり、人に合わせ、争いを避ける"),
    "C": ("細かいことや決まりにこだわらず、気ままに動く", "計画的で、決まりや約束をきちんと守る"),
    "N": ("気持ちが落ち着いていて、あまり心配しない", "心配しやすく、気持ちがゆれやすい"),
    "O": ("なじんだやり方を好み、新しいものには慎重", "新しいことや考えに興味があり、型にはまらない"),
}


def level(z):
    return LEVELS[sum(z > c for c in CUTS)]


def mbti(z):
    e, a, c, n, o = (z[t] for t in TRAITS)
    return ("E" if e >= 0 else "I") + ("N" if o >= 0 else "S") + ("F" if a >= 0 else "T") + ("J" if c >= 0 else "P") + \
        ("-T" if n >= 0 else "-A")


def make(n=N_PERSONAS, seed=SEED):
    rng = np.random.default_rng(seed)
    Z = rng.multivariate_normal(np.zeros(5), CORR, size=n)
    w = np.array([p for _, p in AGE_BANDS], float)
    bands = rng.choice(len(AGE_BANDS), size=n, p=w / w.sum())
    sex = rng.choice(len(SEXES), size=n, p=[p for _, p in SEXES])
    pw = np.array([p for _, p in PREF_POP], float)
    pref = rng.choice(len(PREF_POP), size=n, p=pw / pw.sum())
    out = []
    for k in range(n):
        lo, hi = AGE_BANDS[bands[k]][0]
        age = int(rng.integers(lo, hi + 1))
        z = {t: round(float(Z[k, j]), 3) for j, t in enumerate(TRAITS)}
        out.append({
            "persona_id": f"P{k + 1:03d}",
            "age": age, "sex": SEXES[sex[k]][0], "prefecture": PREF_POP[pref[k]][0],
            "big5_z": z,
            "big5_level": {t: level(z[t]) for t in TRAITS},
            "mbti_label": mbti(z),
        })
    return out


def main():
    here = os.path.dirname(os.path.abspath(__file__))
    ps = make()
    meta = {"seed": SEED, "n": len(ps), "traits": TRAITS, "corr": CORR.tolist(),
            "note": "Big Five は独立な標準正規 (相関は確かめられた表がないので 0)。MBTI は見せるためのラベルだけ。年齢・性別・都道府県は仮定の分布 (prereg 4.)"}
    with open(os.path.join(here, "personas.json"), "w", encoding="utf-8") as f:
        json.dump({"meta": meta, "personas": ps}, f, ensure_ascii=False, indent=1)
    print(f"wrote personas.json ({len(ps)} personas)")


if __name__ == "__main__":
    main()
