"""論文 2・実験 2c: 答える人に持たせる「これまでにあったこと」(過去の出来事) を、くじで割り当てる。種が決めてあるので、何度動かしても同じ。

    python3 experiences.py         # experiences_exp2c.json を書く (出来事 20 個と、S001〜S100 の割り当て)

決め (くわしくは docs/research/humanity/paper2_exp2c_prereg.md の 4.):
- 出来事は 20 個 = 5 つの領域 (修士論文の 5 つの意識に合わせた: 権利・所有・情報・プライバシー・自己責任)
  × 2 つの向き (fav = はみ出しても困らなかった・助かった・喜ばれた / unfav = 困った・自分がされた・注意された) × 2 つの言い方。
- 一人称・過去・具体的な 1 文。性格・人柄の言葉は使わない。54 問の文を写さない (同じ 8 字以上の続きを持たない。test_survey.py が確かめる)。
  「みんながやっている」など、まわりの様子の言葉も使わない (それは実験 2・2b で変えたもの。ここでは本人の出来事だけ)。
- 言い出し「前に、」「以前、」は、向きによらず、言い方 0 = 「前に」、1 = 「以前」にそろえた (言い出しが向きと重ならないように)。
- F1 (100 人): 3 つの出来事。3 つとも違う領域。5 つから 3 つの組 10 通りを 10 人ずつ (どの領域も 60 人)。
  向きは、領域ごとに 30 人 / 30 人。組ごとに 8 通りの向きの並び + 1 通りとその裏返し (どの領域も組の中で 5 / 5)。
- F2 (100 人): F1 の 3 つ + 3 つ。足す 3 つは、F1 になかった 2 つの領域に 1 つずつ (向きは領域ごとに 20 / 20) と、
  F1 にあった領域のうち 1 つに、同じ向きのもう一つの言い方 (どの領域・向きも 10 人ずつ)。
  だから F2 では、だれもが 5 つの領域の出来事を持ち、1 つの領域だけ 2 つ (同じ向き。食い違う組はない)。
- 紙の上の並びは、人ごとにくじ (F1 も F2 も)。
"""
import json
import os
from itertools import combinations

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
SEED = 20261101
N = 100

DOMAINS = [("rights", "権利"), ("own", "所有"), ("info", "情報"), ("privacy", "プライバシー"), ("self", "自己責任")]
DIRECTIONS = [("fav", "はみ出しても困らなかった・助かった"), ("unfav", "困った・自分がされた・注意された")]

# (領域, 向き) → [言い方 0 (「前に」), 言い方 1 (「以前」)]
POOL = {
    ("rights", "fav"): ["前に、友人の家の Wi-Fi を断らずに使わせてもらったが、何も言われず、とても助かった。",
                        "以前、おもしろかった雑誌の記事を撮って友人に送ったら、読みたかったと喜ばれた。"],
    ("rights", "unfav"): ["前に、ただで手に入れた音楽のファイルのせいで、パソコンがウイルスに感染して困った。",
                          "以前、自分が描いた絵を、知らない人のページに勝手に使われて、いやな思いをした。"],
    ("own", "fav"): ["前に、友人に借りた本を半年ほど持ったままだったが、相手は少しも気にしていなかった。",
                     "以前、借りた傘を返しそびれていたら、相手から「そのまま使って」と言ってもらえた。"],
    ("own", "unfav"): ["前に、友人に貸した本が何か月も返ってこず、最後にはなくされてしまった。",
                       "以前、借りた道具を返すのが遅れて、貸してくれた人と気まずくなった。"],
    ("info", "fav"): ["前に、家族のアカウントで代わりにログインして手続きを済ませたら、とても感謝された。",
                      "以前学校で、本や記事の文章をつなぎ合わせて出したレポートが、よい点をもらえた。"],
    ("info", "unfav"): ["前に、知人に自分のアカウントを勝手に使われて、覚えのない買い物をされた。",
                        "以前学校で、人の書いた文章をほぼそのまま使ってレポートを出し、先生に注意された。"],
    ("privacy", "fav"): ["前に、友人の住所を共通の知り合いに教えたら、お祝いが届いたと友人に喜ばれた。",
                         "以前、旅行で友人を写した一枚を断らずに SNS に出したが、友人は気にしなかった。"],
    ("privacy", "unfav"): ["前に、自分の電話番号を知らないうちに人に教えられ、知らない人から何度も電話が来た。",
                           "以前、自分が写った写真を勝手にネットに出されて、知り合いに見られていやな思いをした。"],
    ("self", "fav"): ["前に、宛名の書かれた封筒をそのまま捨てていたが、困ったことは一度もなかった。",
                      "以前、よく調べずに入れた家計簿のアプリが便利で、毎日の記録がずっと楽になった。"],
    ("self", "unfav"): ["前に、宛名の書かれたはがきをそのまま捨てたら、近所の人に中身を読まれて気まずくなった。",
                        "以前、何にでも同じパスワードにしていて、いくつものアカウントを一度に乗っ取られた。"],
}
DKEYS = [d for d, _ in DOMAINS]


def eid(domain, direction, variant):
    return f"{domain}_{direction}_{variant}"


def pool():
    """出来事 20 個 (並びは 領域 → 向き → 言い方)。"""
    return [{"id": eid(d, r, v), "domain": d, "domain_ja": dict(DOMAINS)[d], "direction": r, "variant": v, "text": POOL[(d, r)][v]}
            for d in DKEYS for r, _ in DIRECTIONS for v in (0, 1)]


TEXT_OF = {e["id"]: e["text"] for e in pool()}


def codes(exps):
    """出来事の ID の列 → 領域ごとの数 (unfav = +1、fav = −1、ない = 0 の和)。F1 は −1/0/+1、F2 は −2〜+2 (0 はない)。"""
    c = {d: 0 for d in DKEYS}
    for x in exps:
        d, r, _ = x.split("_")
        c[d] += 1 if r == "unfav" else -1
    return c


def _assign_f1(rng):
    triples = list(combinations(range(5), 3))
    patterns = [[(c >> b) & 1 for b in range(3)] for c in range(8)]
    people = []   # (triple, dirs)
    for t in triples:
        extra = patterns[int(rng.integers(8))]
        grp = patterns + [extra, [1 - x for x in extra]]
        grp = [grp[i] for i in rng.permutation(10)]
        people += [(t, g) for g in grp]
    people = [people[i] for i in rng.permutation(N)]
    dom = [[DKEYS[j] for j in t] for t, _ in people]
    dirs = [["unfav" if x else "fav" for x in g] for _, g in people]
    # 言い方: (領域, 向き) ごとの 30 人を 15 / 15
    var = [[None] * 3 for _ in range(N)]
    for d in DKEYS:
        for r, _ in DIRECTIONS:
            who = [(k, j) for k in range(N) for j in range(3) if dom[k][j] == d and dirs[k][j] == r]
            vs = [0, 1] * (len(who) // 2) + [0] * (len(who) % 2)
            vs = [vs[i] for i in rng.permutation(len(vs))]
            for (k, j), v in zip(who, vs):
                var[k][j] = v
    return [[eid(dom[k][j], dirs[k][j], var[k][j]) for j in range(3)] for k in range(N)]


def _assign_f2_extra(rng, f1):
    """F1 になかった 2 つの領域に 1 つずつ + F1 の領域の 1 つに同じ向きのもう一つの言い方。"""
    extra = [[] for _ in range(N)]
    for d in DKEYS:
        who = [k for k in range(N) if d not in [x.split("_")[0] for x in f1[k]]]
        rs = ["fav", "unfav"] * (len(who) // 2) + ["fav"] * (len(who) % 2)
        rs = [rs[i] for i in rng.permutation(len(rs))]
        for r in ("fav", "unfav"):
            ks = [k for k, x in zip(who, rs) if x == r]
            vs = [0, 1] * (len(ks) // 2) + [0] * (len(ks) % 2)
            vs = [vs[i] for i in rng.permutation(len(vs))]
            for k, v in zip(ks, vs):
                extra[k].append(eid(d, r, v))
    # 2 つ目を足す領域: どの (領域, 向き) も 10 人ずつになるように、少ない方から選ぶ (同点はくじ)
    for _ in range(1000):
        cnt = {(d, r): 0 for d in DKEYS for r, _ in DIRECTIONS}
        pick = [None] * N
        for k in rng.permutation(N):
            cells = [tuple(x.split("_")[:2]) for x in f1[k]]
            low = min(cnt[c] for c in cells)
            c = [c for c in cells if cnt[c] == low]
            c = c[int(rng.integers(len(c)))]
            cnt[c] += 1
            pick[k] = c
        if all(v == N // 10 for v in cnt.values()):
            break
    else:
        raise SystemExit("could not balance the doubled domains")
    for k in range(N):
        d, r = pick[k]
        v = [int(x.split("_")[2]) for x in f1[k] if x.startswith(f"{d}_{r}_")][0]
        extra[k].append(eid(d, r, 1 - v))
    return extra


def make(n=N, seed=SEED):
    assert n == N
    rng = np.random.default_rng(seed)
    f1 = _assign_f1(rng)
    extra = _assign_f2_extra(rng, f1)
    out = []
    for k in range(N):
        a = [f1[k][i] for i in rng.permutation(3)]          # F1 の紙の並び
        six = f1[k] + extra[k]
        b = [six[i] for i in rng.permutation(6)]            # F2 の紙の並び
        out.append({"situation_id": f"S{k + 1:03d}", "F1": a, "F2": b, "code_F1": codes(a), "code_F2": codes(b)})
    return out


def lines(exps):
    return [TEXT_OF[x] for x in exps]


def main():
    asg = make()
    meta = {"seed": SEED, "n": len(asg), "domains": DOMAINS,
            "note": "prereg 4.。code は unfav = +1、fav = −1 の和 (領域ごと)。F1・F2 は紙の上の並び。S(k) は situations.json と同じ暮らし"}
    with open(os.path.join(HERE, "experiences_exp2c.json"), "w", encoding="utf-8") as f:
        json.dump({"meta": meta, "pool": pool(), "assignments": asg}, f, ensure_ascii=False, indent=1)
    c1 = {d: sum(a["code_F1"][d] != 0 for a in asg) for d in DKEYS}
    print(f"wrote experiences_exp2c.json ({len(asg)}); F1 per domain {c1}")


if __name__ == "__main__":
    main()
