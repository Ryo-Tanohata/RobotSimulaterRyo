"""フェーズの判定 (docs/society_phase_plan.md 2 章・4 章)。毎晩、7 日間の様子から次のフェーズに進んだかを決める。

フェーズは state["era"] に記録する ("F1" から始まる)。state["phase"] は 1 日の段階 (day / evening / night) なので別のもの。
判定の数字は Claude が決めた仮の基準。フェーズが進んだら、step.py がシミュレーションを一時停止して評価を待つ。
"""
from world import food_words

ERAS = {
    "F1": "移動する採集民", "F2": "食べ物の幅を広げる", "F3": "蓄える",
    "F4": "定住する", "F5": "野生植物を育てる", "F6": "農耕に頼る (Society 2.0)",
}
ORDER = list(ERAS)
WINDOW = 7          # 何日間の様子で判定するか
MIN_DAYS = 7        # 1 つのフェーズは最低この日数続ける
BROAD_FOODS = ("魚", "ピク", "草の種")  # 広範囲革命で増えたとされる種類の食べ物 (小さな動物・魚・草の種)


def indicators(state):
    """直近 7 日間の指標"""
    last = state["stats"][-WINDOW:]
    eaten, days_by_kind = {}, {}
    for s in last:
        for k, v in (s.get("eaten_by_kind") or {}).items():
            eaten[k] = eaten.get(k, 0) + v
            if v > 0:
                days_by_kind[k] = days_by_kind.get(k, 0) + 1
    main = sorted((k for k, v in eaten.items() if v >= 1500), key=lambda k: -eaten[k])
    total = sum(eaten.values()) or 1
    sown_food = 0  # 育てた植物から食べた量 (F5・F6 用。まだ記録していない)
    return {
        "days": len(last),
        "eaten": food_words(eaten),
        "main_foods": main,                                   # 7 日間に 1,500 kcal 以上食べた食べ物
        "broad_foods": [k for k in main if k in BROAD_FOODS and days_by_kind.get(k, 0) >= 3],  # 小さな動物・魚・草の種を 3 日以上
        "stored_acts": sum(s.get("stored_acts", 0) for s in last),  # 蓄えに入れた・干した回数
        "animal_broad": [k for k in ("魚", "ピク") if days_by_kind.get(k, 0) >= 3],  # 小さな動物・魚を 3 日以上
        "from_store_share": round(sum(s.get("took", 0) for s in last) / total, 2),  # 食べた量のうち蓄えから取った割合
        "lasting_store_days": round((last[-1].get("store_lasting", 0) if last else 0) / 9000, 1),  # 腐りにくい蓄えが 5 人の何日分か
        "store": food_words(_store_kinds(state)),
        "camp_moves": state.get("camp_moves", 0),
        "camp_days": state["day"] - state.get("camp_since", 0),  # 今のキャンプに何日いるか
        "dwelling": round(state["camp"].get("dwelling", 0), 2),  # 住まいのでき具合 (1 で完成)
        "dwelling_days": (state["day"] - state["camp"]["dwelling_day"]) if state["camp"].get("dwelling_day") is not None else 0,  # 住まいができてから何日暮らしたか
        "sown_trees": sum(1 for q in state["plants"] if q.get("sown")),
        "sown_share": round(sown_food / total, 2),
    }


def _store_kinds(state):
    out = {}
    for f in state.get("store", []):
        out[f["kind"]] = out.get(f["kind"], 0) + f["kcal"]
    return out


def criteria(era, ind):
    """次のフェーズへの条件。(説明, 満たしたか)"""
    if era == "F1":
        return ("7 日間に 3 種類以上の食べ物をよく食べ (各 1,500 kcal 以上)、そのうち 1 つは小さな動物・魚・草の種で、3 日以上食べている",
                len(ind["main_foods"]) >= 3 and len(ind["broad_foods"]) >= 1)
    if era == "F2":
        # F1 の評価 (2026-10-01) で、蓄える行動は F1 のうちに始まっていたため、回数ではなく中身で決める
        return ("小さな動物か魚を 7 日間に 3 日以上食べ、腐りにくい食べ物 (草の種・干し肉) の蓄えが 5 人の 3 日分以上あり、食べた量の 3 割以上を蓄えから取っている",
                len(ind["animal_broad"]) >= 1 and ind["lasting_store_days"] >= 3 and ind["from_store_share"] >= 0.3)
    if era == "F3":
        # F2 の評価のあと (2026-10-01) に住まいの仕組みを加えた。キャンプを移すと住まいは置いていくので、同じ場所に住み続けた日数になる
        return ("キャンプに住まいを建て、そのキャンプで 30 日以上暮らす (キャンプを移すと住まいは置いていく)",
                ind["dwelling_days"] >= 30)
    if era == "F4":
        return ("キャンプの近くに種をまき、育った実を 2 回以上収穫する (記録はまだない)", False)
    if era == "F5":
        return ("7 日間に食べた量の半分以上が、育てた植物から", ind["sown_share"] >= 0.5)
    return ("(最後のフェーズ)", False)


def check(state):
    """今夜の判定。フェーズが進んだら state を更新して True を返す"""
    era = state.setdefault("era", "F1")
    state.setdefault("era_log", [{"era": "F1", "day": 0}])
    ind = indicators(state)
    desc, met = criteria(era, ind)
    since = state["day"] - state["era_log"][-1]["day"]
    state["era_info"] = {"era": era, "name": ERAS[era], "next": desc, "met": met, "since": since, "indicators": ind}
    if met and since >= MIN_DAYS and era != ORDER[-1]:
        nxt = ORDER[ORDER.index(era) + 1]
        state["era"] = nxt
        state["era_log"].append({"era": nxt, "day": state["day"], "indicators": ind})
        state["era_info"] = {"era": nxt, "name": ERAS[nxt], "next": criteria(nxt, ind)[0], "met": False, "since": 0, "indicators": ind}
        return True
    return False
