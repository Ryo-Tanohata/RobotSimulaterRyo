"""接地度 (grounding) を記録から計算する (段階 0: 記録だけ。世界の進み方には使わない)

設計は docs/humanity/design_note.md (D03・D06・D09・D10)、データは docs/humanity/tech_tree.json (v0.5)。
接地度は「身体や現場にどれだけ根ざして働いているか」の記述 (0〜1、大きいほど深い)。良い・悪いの判定ではない。

  意味 = (技能多様性・タスク完結性・タスク重要性 の平均 − 1) / 6   職務特性モデル (Hackman & Oldham 1975) の「意味を感じる」
  結果 = (仕事からのフィードバック − 1) / 6                        同「結果が分かる」
  身体 = O*NET の「一般的な身体活動」の重要度 / 100                 近い現代の職業の実データ。近い職業がなければ推定
  接地度 = (意味 + 結果 + 身体) / 3
  自律性 = (自律性 − 1) / 6                                         手綱の余地。接地度には足さず別に出す

人ごとの値は、その季節に働いた日数で仕事ごとの値を重みづけした平均。休んだ日は数えない。
1〜7 の評定は、陪審団 12 人 (Claude の 3 つのモデルが演じた人物。docs/humanity/jury/) が独立に付けた値の平均 (D10)。
作り手 (Claude) の評定は docs/humanity/jury/creator_ratings.json に残してある。理由は作り手が書いたもの。身体の値の出どころも表に書いた。
乱数も時刻も使わないので、同じ記録からは同じ値になる。
"""

# 仕事: (技能多様性, タスク完結性, タスク重要性, フィードバック, 自律性, 身体, 身体の出どころ, 理由)。評定は陪審団の平均
ACTS = {
    "採集": (3.58, 4.08, 4.42, 5.25, 5.08, 0.80, "推定 (狩猟採集。docs/humanity の N01 と同じ)", "探して採り、持ち帰って食べるまで自分で関わり、量がすぐ分かる"),
    "狩り": (4.83, 5.08, 5.5, 5.83, 3.67, 0.80, "推定 (狩猟採集)", "仲間と追い込み、しとめたかどうかがその場で分かる"),
    "探索": (4.17, 3.42, 5, 4.17, 6.08, 0.75, "推定 (歩いて見て回る)", "見つけた場所が役立つかは、あとで採りに行くまで分からない"),
    "道具づくり": (5.25, 6.33, 4.75, 6.5, 5.33, 0.64, "O*NET 51-7011.00 家具職人 64", "材料から道具まで一人で作り、使えば出来が分かる"),
    "火おこし": (2.42, 3.92, 6.08, 5.67, 3.42, 0.50, "推定 (座って手を動かす)", "技能はせまいが、ついたかどうかがすぐ分かる"),
    "住まいを建てる": (5.75, 6.58, 5.67, 6.33, 4.58, 0.68, "O*NET 47-2061.00 建設作業員 68", "材料を集めて建て、住めば出来が分かる"),
    "種まき": (2.17, 2.83, 4.25, 2.58, 4.58, 0.76, "O*NET 45-2092.00 農作業員 (作物) 76", "埋めてから木になるまで長く、結果がなかなか分からない"),
    "畑仕事": (4.5, 5.67, 5.83, 5.17, 3.83, 0.76, "O*NET 45-2092.00 農作業員 (作物) 76", "まく・草取り・刈るまで関わるが、実りは季節の終わりに分かる (docs/humanity の N03 と同じ)"),
    "ヤギの世話": (3.83, 3.92, 4.58, 5.08, 4.08, 0.75, "O*NET 45-2093.00 農作業員 (家畜) 75", "毎日世話をし、乳やヤギの様子で結果が分かる"),
    "ヤギを捕まえる": (4.25, 4.5, 4.42, 5.42, 3.25, 0.80, "推定 (狩りに近い)", "捕まえられたかがその場で分かる"),
    "土器づくり": (5.17, 6.33, 4.5, 6.08, 5, 0.64, "O*NET 51-7011.00 家具職人 64 (手仕事の職人として)", "こねて形を作り焼くまで一人で関わり、割れたかで出来が分かる"),
    "交換に行く": (4.42, 4.67, 4.75, 4.33, 5.42, 0.60, "推定 (運んで歩く)", "ほかの村まで運んで交換し、持ち帰るまで関わる"),
    "記録をつける": (2.42, 2.92, 4.42, 2.67, 2.67, 0.16, "O*NET 43-3031.00 簿記・会計の事務員 16", "決まった印や数え札で量を残す。記録がどう使われるかは見えにくい"),
}
REST = ("休む", "休む (けが)")  # 働いた日に数えない


def act_scores(act):
    """1 つの仕事の (意味, 結果, 身体, 自律性)。知らない仕事は None"""
    a = ACTS.get(act)
    if a is None:
        return None
    sv, ti, ts, fb, au, body = a[:6]
    return (((sv + ti + ts) / 3 - 1) / 6, (fb - 1) / 6, body, (au - 1) / 6)


def person(days_by_activity):
    """季節の 1 人分: 仕事ごとの日数 → 接地度 (働いた日がなければ None)"""
    tot = [0.0, 0.0, 0.0, 0.0]
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
        for i in range(4):
            tot[i] += s[i] * n
    if not work:
        return None
    m, f, b, au = (round(x / work, 3) for x in tot)
    out = {"meaning": m, "feedback": f, "body": b, "value": round((m + f + b) / 3, 3), "autonomy": au, "work_days": work}
    if unscored:
        out["unscored_days"] = unscored
    return out


def village(person_rows):
    """季節の村: 大人 (子でない人) のうち、接地度のある人の平均・いちばん低い・いちばん高い"""
    vals = [r["grounding"] for r in person_rows if not r.get("child") and r.get("grounding")]
    if not vals:
        return None
    n = len(vals)
    mean = {k: round(sum(v[k] for v in vals) / n, 3) for k in ("meaning", "feedback", "body", "value", "autonomy")}
    vs = [v["value"] for v in vals]
    return mean | {"people": n, "min": min(vs), "max": max(vs)}


# ---- 段階 1: 仕事の理由 (docs/humanity の D09。2026-10-14) ----
# 季節のお題の job.why を、Claude を使わずに機械的に読む。「理由があるか」と「習慣で選んだ言い方か」だけを見る。
# 言葉の一覧は【仮定】。あいまいなものは段階 2 の陪審団が読む (理由・理念の判定はここではしない)
HABIT_WORDS = ("いつも", "前と同じ", "同じように", "同じ仕事", "変わらず", "慣れ", "引き続き", "そのまま", "決まり", "言われた")


def read_reason(text):
    """仕事の理由の一言 → {"stated": 理由が書いてあるか, "habit": 習慣・言われたからの言い方か}。書いていなければ None"""
    t = (text or "").strip() if isinstance(text, str) else ""
    if not t or t in ("...", "…"):
        return None
    return {"stated": True, "habit": any(w in t for w in HABIT_WORDS)}


def village_reasons(person_rows):
    """季節の村: 仕事を決めた大人のうち、理由を書いた人と、習慣の言い方の人の数 (理由がだれにもなければ None)"""
    rows = [r for r in person_rows if not r.get("child") and r.get("decided_by") in ("自分", "代表と同じ仕事", "代表が割り振った")]
    read = [r["why_read"] for r in rows if r.get("why_read")]
    if not read:
        return None
    return {"deciders": len(rows), "with_reason": len(read), "habit": sum(1 for x in read if x["habit"])}
