"""論文 2・実験 2: 答える人 (LLM) に持たせる「暮らし・立場・損得」をくじで作る。種が決めてあるので、何度動かしても同じ。

    python3 situations.py          # situations.json を書く (S001〜S100。D1・D2・D3 で同じ番号は同じ暮らし)

決め (くわしくは docs/research/humanity/paper2_exp2_prereg.md の 4.):
- 性格の言葉 (ビッグファイブ) と、人柄のよし悪しの言葉 (まじめ・正直 など) は、いっさい使わない。
- 年齢・立場 (学生 / 正社員 / パート など)・暮らし向き・家族・ネットの慣れ・音楽の聞き方・身近な人との間柄と、
  修士論文の「はみ出しにくい時」(作った人にお金が入らないと暮らせないのを身近に知っている / しっかりした決まり /
  作った人を買って応援している) を、くじで引き、本人が書いたような短い文 (一人称) にする。
- 分布はみな【仮定】(日本の大人のおおよその姿を Claude が決めた。統計の数を写したものではない)。
- D2 だけに見せる「最近のまわりの様子」(修士論文の「はみ出しやすい時」4 つ) は、1 つずつ 50 人 / 50 人に分ける
  (16 通りの組を同じ数ずつ。4 つの間の相関はほぼ 0)。D1・D3 の紙には出さない。
"""
import json
import os

import numpy as np

from items import SURROUND
from personas import PREF_POP

SEED = 20261029
N_SITUATIONS = 100

# 年代の重み【仮定】: 学生と働く人をくらべる (H9) ため、18〜29 歳を実験 1 より厚くした
AGE_BANDS = [((18, 22), 0.15), ((23, 29), 0.15), ((30, 39), 0.18), ((40, 49), 0.20), ((50, 59), 0.17), ((60, 69), 0.15)]
SEXES = ["男性", "女性"]
POSITIONS = ["student", "regular", "nonregular", "self", "home", "nowork"]
POS_JA = {"student": "学生", "regular": "会社員 (正社員)", "nonregular": "パート・アルバイト・派遣", "self": "自営業・フリーランス",
          "home": "家事が中心", "nowork": "仕事をしていない (退職・求職中)"}
# 年代ごとの立場の重み【仮定】(並びは POSITIONS)
POS_W = {
    (18, 22): [0.75, 0.08, 0.15, 0.00, 0.00, 0.02],
    (23, 29): [0.08, 0.62, 0.20, 0.03, 0.04, 0.03],
    (30, 39): [0.02, 0.58, 0.20, 0.07, 0.10, 0.03],
    (40, 49): [0.02, 0.55, 0.22, 0.09, 0.09, 0.03],
    (50, 59): [0.02, 0.50, 0.22, 0.12, 0.09, 0.05],
    (60, 69): [0.02, 0.15, 0.28, 0.15, 0.12, 0.28],
}
MONEY = ["tight", "normal", "comfortable"]
MONEY_JA = {"tight": "苦しい", "normal": "ふつう", "comfortable": "ゆとりがある"}
MONEY_W = {"student": [0.45, 0.45, 0.10], "regular": [0.15, 0.60, 0.25], "nonregular": [0.40, 0.50, 0.10],
           "self": [0.30, 0.45, 0.25], "home": [0.20, 0.60, 0.20], "nowork": [0.35, 0.45, 0.20]}
DIGITAL = ["high", "mid", "low"]
DIGITAL_JA = {"high": "くわしい", "mid": "ふつう", "low": "苦手"}
DIGITAL_W = {(18, 22): [0.45, 0.50, 0.05], (23, 29): [0.45, 0.50, 0.05], (30, 39): [0.35, 0.55, 0.10],
             (40, 49): [0.25, 0.60, 0.15], (50, 59): [0.15, 0.60, 0.25], (60, 69): [0.10, 0.50, 0.40]}
MUSIC = ["subscription", "buy", "free_video", "little"]
MUSIC_W = {"young": [0.50, 0.10, 0.35, 0.05], "middle": [0.35, 0.25, 0.30, 0.10], "older": [0.15, 0.35, 0.25, 0.25]}
HOUSE = ["alone", "parents", "spouse", "spouse_kids", "single_parent", "kids_family"]
HOUSE_W = {(18, 22): [0.45, 0.55, 0, 0, 0, 0], (23, 29): [0.45, 0.30, 0.15, 0.10, 0, 0],
           (30, 39): [0.15, 0.10, 0.15, 0.55, 0.05, 0], (40, 49): [0.15, 0.10, 0.15, 0.55, 0.05, 0],
           (50, 59): [0.15, 0.05, 0.30, 0.45, 0.05, 0], (60, 69): [0.20, 0, 0.55, 0.20, 0, 0.05]}
P_CLOSE = 0.55          # 気軽に貸し借り・頼みごとをし合える相手が近くにいる
P_CREATOR = 0.15        # 作った物で暮らす人が身近にいる (はみ出しにくい時: 製作者にお金が入らず生活できない)
P_FAN = 0.40            # 好きな作り手の作品を買って応援している (はみ出しにくい時: 作った人への敬意)
RULES_W = {"regular": 0.65, "student": 0.45, "nonregular": 0.35, "self": 0.30, "home": 0.10, "nowork": 0.10}  # しっかりした決まり

JOBS_REG = ["事務", "営業", "工場での製造", "IT (システム開発)", "店の販売", "介護", "建設現場の管理", "物流"]
JOBS_NONREG = [("スーパー", "パート"), ("飲食店", "アルバイト"), ("倉庫", "派遣"), ("コールセンター", "派遣"),
               ("会社の事務", "パート"), ("コンビニ", "アルバイト")]
JOBS_SELF = ["小さな飲食店", "農業", "フリーランスのデザインの仕事", "大工", "小さな商店", "個人の塾"]
CREATOR_LINES = ["家族に音楽の仕事をしている人がいて、作品が売れないと暮らしが苦しくなるのを身近に見ている。",
                 "友人に本やイラストを描いて暮らしている人がいて、作品が売れないと暮らしが苦しくなるのを身近に見ている。",
                 "自分も副業で写真やイラストを売っていて、作った物にお金が払われないと困ることを知っている。"]
FAN_LINES = ["好きな歌手がいて、新しい曲が出ると買って応援している。", "好きな作家がいて、新しい本が出ると買って応援している。",
             "好きな漫画家がいて、新しい巻が出ると買って応援している。", "好きなゲームの作り手がいて、新しい作品が出ると買って応援している。"]
RULES_LINES = {"regular": "会社では、情報の扱いや著作権について研修があり、決まりがはっきりしている。",
               "student": "学校の授業で、著作権や情報の扱いの決まりを教わった。",
               "nonregular": "職場では、お客さんの情報の扱いについて決まりがはっきりしている。",
               "self": "仕事で、契約や著作権の決まりを確かめることが多い。",
               "home": "地域の講座で、ネットの使い方の決まりを教わったことがある。",
               "nowork": "地域の講座で、ネットの使い方の決まりを教わったことがある。"}

# D2 の「最近のまわりの様子」。(はみ出しやすい側 = 1, 反対側 = 0)。並びは items.SURROUND と同じ
SURROUND_LINES = {
    "everyone": ("友人や同僚の間では、音楽や動画をただで手に入れたり、人の写真や文章を気軽に載せ合ったりするのが、ふつうになっている。",
                 "友人や同僚の多くは、音楽や動画はお金を払って手に入れ、人の写真や文章を載せるときは一言ことわっている。"),
    "no_arrest": ("ネットでのコピーや無断の利用で、捕まったり注意されたりした人の話は、まわりで聞いたことがない。",
                  "最近、ネットでのコピーや無断の利用で、捕まったり職場や学校で注意されたりした人の話を、身近で聞いた。"),
    "weak": ("このところ、自分は弱い立場にいると感じることが多い。急な出費で手元のお金が足りず、まわりにも言いたいことが言いにくい。",
             "このところ、お金にも人間関係にも余裕があり、自分が弱い立場だとは感じない。"),
    "easy": ("スマホやパソコンで、音楽や動画の保存、写真の共有、人の文章の写しなどが、ボタン一つで簡単にできるようになった。やり方も知っている。",
             "音楽や動画の保存や写真の共有などは、やり方がよく分からず、手間がかかると感じている。"),
}

# 実験 2b の E1 の「最近のまわりの様子」(docs/research/humanity/paper2_exp2b_prereg.md の 4.)。並び・0/1 は D2 と同じ。
# 中身だけを、ダウンロード・コピーから「借りた物・人の物」に変えた。weak は D2 と 1 字も同じ (くらべの土台)。
# ネット・ダウンロード・コピーの言葉は使わない (test_survey.py が確かめる)。
OWN_SURROUND_LINES = {
    "everyone": ("友人や同僚の間では、借りた本や服、道具や CD を返さずにいたり、共用の場所の小さな物を持ち帰ったりするのが、ふつうになっている。",
                 "友人や同僚の多くは、借りた物はすぐに返し、共用の場所の物は持ち帰らずに、元の場所にもどしている。"),
    "no_arrest": ("借りた物を返さずにいて、返すように言われたり責められたりした人の話は、まわりで聞いたことがない。",
                  "最近、借りた物を返さずにいて、相手と仲が悪くなったり、職場や学校に知らされたりした人の話を、身近で聞いた。"),
    "weak": SURROUND_LINES["weak"],
    "easy": ("借りた物や、まわりに置きっぱなしの物は、そのまま持っていても、だれにも気づかれない。だれが何を貸したかを覚えている人もいない。",
             "職場や友人の間では、だれに何を貸したかを書きとめていて、借りた物を持ったままだと、すぐに分かるようになっている。"),
}


def _pick(rng, options, w):
    w = np.array(w, float)
    return options[int(rng.choice(len(options), p=w / w.sum()))]


def describe(s):
    """暮らしの数 → 本人が書いたような一人称の文 (性格・人柄の言葉は使わない)。"""
    age, sex, pos = s["age"], s["sex"], s["position"]
    out = [f"私は {age} 歳の{sex}で、{s['prefecture']}に住んでいる。"]
    d = s["detail"]
    if pos == "student":
        out.append("働きながら、通信制の大学で学んでいる。" if age >= 23 else f"{d}に通っている。")
    elif pos == "regular":
        out.append(f"会社員 (正社員) として、{d}の仕事をしている。")
    elif pos == "nonregular":
        out.append(f"{d[0]}で{d[1]}として働いている。")
    elif pos == "self":
        out.append(f"{d}を自分でやっている。")
    elif pos == "home":
        out.append("家事が中心の毎日で、外では働いていない。")
    else:
        out.append("長く勤めた会社を退職し、いまは年金で暮らしている。" if age >= 60 else "いまは仕事を探している。")
    partner = "妻" if sex == "男性" else "夫"
    out.append({"alone": "一人暮らしだ。", "parents": "親と暮らしている。", "spouse": f"{partner}と二人で暮らしている。",
                "spouse_kids": f"{partner}と子どもと暮らしている。", "single_parent": "子どもと二人で暮らしている。",
                "kids_family": "子ども夫婦と暮らしている。"}[s["household"]])
    if s["money"] == "tight":
        out.append("仕送りとアルバイト代でやりくりしていて、月末はいつもお金が足りない。本や CD を買う余裕はほとんどない。"
                   if pos == "student" and age < 23 else "家計に余裕がなく、毎月のやりくりで精一杯だ。趣味にお金をかけることはほとんどできない。")
    elif s["money"] == "normal":
        out.append("暮らしはふつうで、ぜいたくはしないが、ほしい物をときどき買うくらいの余裕はある。")
    else:
        out.append("暮らしにはゆとりがあり、ほしい本や音楽は気にせず買える。")
    out.append({"high": "パソコンやスマホにはくわしいほうで、アプリの設定やファイルのやりとりも自分でできる。",
                "mid": "スマホで検索や SNS、動画は使うが、細かい設定やファイルのやりとりはあまりしない。",
                "low": "パソコンやスマホは苦手で、電話とメールと簡単な検索くらいしか使わない。困ったら家族に聞く。"}[s["digital"]])
    out.append({"subscription": "音楽はふだん、月ぎめの配信サービスで聞いている。",
                "buy": "音楽は、気に入ったものを CD やダウンロードで買って聞く。",
                "free_video": "音楽はふだん、無料の動画サイトで聞くことが多い。",
                "little": "音楽はあまり聞かない。"}[s["music"]])
    out.append("近くに気心の知れた友人や同僚がいて、物の貸し借りや頼みごとをよくし合う。何かあっても、あとで話せば分かり合える間柄だ。"
               if s["close"] else "気軽に頼みごとをし合える相手は少なく、知り合いとは用があるときに話すくらいだ。")
    if s["creator"] is not None:
        out.append(CREATOR_LINES[s["creator"]])
    if s["fan"] is not None:
        out.append(FAN_LINES[s["fan"]])
    if s["rules"]:
        out.append(RULES_LINES[pos])
    return "".join(out)


def surround_lines(flags, lines=None):
    """lines: 既定は D2 の SURROUND_LINES。実験 2b の E1 は OWN_SURROUND_LINES。"""
    lines = lines or SURROUND_LINES
    return [lines[k][0 if flags[k] else 1] for k, _ in SURROUND]


def make(n=N_SITUATIONS, seed=SEED):
    rng = np.random.default_rng(seed)
    out = []
    for k in range(n):
        band = _pick(rng, [b for b, _ in AGE_BANDS], [w for _, w in AGE_BANDS])
        age = int(rng.integers(band[0], band[1] + 1))
        sex = SEXES[int(rng.integers(0, 2))]
        pw = np.array([p for _, p in PREF_POP], float)
        pref = PREF_POP[int(rng.choice(len(PREF_POP), p=pw / pw.sum()))][0]
        pos = _pick(rng, POSITIONS, POS_W[band])
        if pos == "student":
            detail = "大学" if rng.random() < 0.75 else "専門学校"
        elif pos == "regular":
            detail = JOBS_REG[int(rng.integers(len(JOBS_REG)))]
        elif pos == "nonregular":
            detail = list(JOBS_NONREG[int(rng.integers(len(JOBS_NONREG)))])
        elif pos == "self":
            detail = JOBS_SELF[int(rng.integers(len(JOBS_SELF)))]
        else:
            detail = None
        money = _pick(rng, MONEY, MONEY_W[pos])
        house = _pick(rng, HOUSE, HOUSE_W[band])
        digital = _pick(rng, DIGITAL, DIGITAL_W[band])
        music = _pick(rng, MUSIC, MUSIC_W["young" if age < 30 else "middle" if age < 50 else "older"])
        close = bool(rng.random() < P_CLOSE)
        creator = int(rng.integers(len(CREATOR_LINES))) if rng.random() < P_CREATOR else None
        fan = int(rng.integers(len(FAN_LINES))) if rng.random() < P_FAN else None
        rules = bool(rng.random() < RULES_W[pos])
        s = {"situation_id": f"S{k + 1:03d}", "age": age, "sex": sex, "prefecture": pref, "position": pos, "detail": detail,
             "money": money, "household": house, "digital": digital, "music": music, "close": close,
             "creator": creator, "fan": fan, "rules": rules}
        out.append(s)
    # D2 の「最近のまわりの様子」: 4 つの 0/1 の組 16 通りを 6 人ずつ (96 人) + 4 人 (どの列も 2 人が 1) にして、
    # 人の並びをくじで混ぜる。どの様子も 50 人 / 50 人で、4 つの間の相関はほぼ 0 (回帰で 1 つずつの効き目を分けられる)
    rng2 = np.random.default_rng(seed + 2)
    full = [[(c >> b) & 1 for b in range(4)] for c in range(16)]
    rows = [r for r in full for _ in range(n // 16)] + [[1, 1, 0, 0], [0, 0, 1, 1], [1, 0, 1, 0], [0, 1, 0, 1]][:n - 16 * (n // 16)]
    rows = [rows[i] for i in rng2.permutation(len(rows))]
    for k in range(n):
        out[k]["surround"] = {key: int(rows[k][j]) for j, (key, _) in enumerate(SURROUND)}
    for s in out:
        s["student"] = int(s["position"] == "student")
        s["text"] = describe(s)
    return out


def main():
    here = os.path.dirname(os.path.abspath(__file__))
    ss = make()
    meta = {"seed": SEED, "n": len(ss),
            "note": "分布はみな仮定 (prereg 4.)。surround は D2 だけに見せる (1 = はみ出しやすい側)。text は D1・D2・D3 の紙の「あなたについて」"}
    with open(os.path.join(here, "situations.json"), "w", encoding="utf-8") as f:
        json.dump({"meta": meta, "situations": ss}, f, ensure_ascii=False, indent=1)
    pos = {p: sum(s["position"] == p for s in ss) for p in POSITIONS}
    mon = {m: sum(s["money"] == m for s in ss) for m in MONEY}
    print(f"wrote situations.json ({len(ss)}); positions {pos}; money {mon}")


if __name__ == "__main__":
    main()
