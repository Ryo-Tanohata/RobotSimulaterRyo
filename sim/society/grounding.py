"""接地度 (grounding) を記録から計算する (段階 0: 記録だけ。世界の進み方には使わない)

設計は docs/humanity/design_note.md (D03・D06・D09)、データは docs/humanity/tech_tree.json。
接地度は「身体や現場からどれだけ離れて働いているか」を表す数で、0 が密着、マイナスほど離れる。
ここでは 3 つの軸の合計 (高さ) だけを出す。手綱 (理由・理念・波及) は段階 1・2 で足す (まだ作っていない)。

  距離 = -min(段階数, 4) / 4      働いてから食べるまでに、いくつの段階があるか
  身体 = -(1 - 身体の比率)        体を使い物に触れている時間の割合
  意味 = 0 / -0.5 / -1             仕事を説明できる相手 (誰にでも / 身近な人まで / 同業者だけ)
  高さ = 距離 + 身体 + 意味        0 〜 -3

人ごとの値は、その季節に働いた日数で仕事ごとの値を重みづけした平均。休んだ日は数えない。
仕事ごとの値はすべて【仮定】(docs/humanity/design_note.md の「接地度の採点表」と同じ考え方で、村の仕事に当てはめた)。
乱数も時刻も使わないので、同じ記録からは同じ値になる。
"""

# 仕事: (段階数, 段階の流れ, 身体の比率, 説明できる相手)
ACTS = {
    "採集": (0, "採る→食べる", 0.9, "誰にでも"),
    "狩り": (1, "狩る→分け合う→食べる", 0.9, "誰にでも"),
    "探索": (2, "見つける→仲間に伝える→採る→食べる", 0.9, "誰にでも"),
    "道具づくり": (1, "作る→使って採る→食べる", 0.9, "誰にでも"),
    "火おこし": (1, "おこす→料理する→食べる", 0.9, "誰にでも"),
    "住まいを建てる": (0, "建てる→住む", 0.9, "誰にでも"),
    "種まき": (2, "埋める→木が育つ→採る→食べる", 0.9, "誰にでも"),
    "畑仕事": (2, "育てる→刈る→蓄える→食べる", 0.9, "誰にでも"),
    "ヤギの世話": (1, "世話する→乳をしぼる→食べる", 0.9, "誰にでも"),
    "ヤギを捕まえる": (2, "捕まえる→飼う→乳をしぼる→食べる", 0.9, "誰にでも"),
    "土器づくり": (2, "作る→種を守る→蓄える→食べる", 0.9, "誰にでも"),
    "交換に行く": (2, "運ぶ→交換する→持ち帰る→食べる", 0.8, "誰にでも"),
    "記録をつける": (2, "記録する→量を確かめる→分け合う→食べる", 0.3, "身近な人まで"),
}
REST = ("休む", "休む (けが)")  # 働いた日に数えない
MEANING = {"誰にでも": 0.0, "身近な人まで": -0.5, "同業者だけ": -1.0}
MAX_STEPS = 4


def act_scores(act):
    """1 つの仕事の 3 軸の値 (知らない仕事は None)"""
    a = ACTS.get(act)
    if a is None:
        return None
    steps, _, body, meaning = a
    return (-min(steps, MAX_STEPS) / MAX_STEPS, -(1 - body), MEANING[meaning])


def person(days_by_activity):
    """季節の 1 人分: 仕事ごとの日数 → 接地度 (働いた日がなければ None)"""
    tot = [0.0, 0.0, 0.0]
    work, unscored = 0, {}
    for act in sorted(days_by_activity or {}):
        n = days_by_activity[act]
        if act in REST or not n:
            continue
        s = act_scores(act)
        if s is None:
            unscored[act] = n
            continue
        work += n
        for i in range(3):
            tot[i] += s[i] * n
    if not work:
        return None
    d, b, m = (round(x / work, 3) for x in tot)
    out = {"distance": d, "body": b, "meaning": m, "height": round(d + b + m, 3), "work_days": work}
    if unscored:
        out["unscored_days"] = unscored
    return out


def village(person_rows):
    """季節の村: 大人 (子でない人) のうち、接地度のある人の平均・いちばん低い・いちばん高い"""
    vals = [r["grounding"] for r in person_rows if not r.get("child") and r.get("grounding")]
    if not vals:
        return None
    n = len(vals)
    mean = {k: round(sum(v[k] for v in vals) / n, 3) for k in ("distance", "body", "meaning", "height")}
    hs = [v["height"] for v in vals]
    return mean | {"people": n, "min": min(hs), "max": max(hs)}
