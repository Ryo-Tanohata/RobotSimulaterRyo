"""一人ひとりの履歴書と職務経歴書 (アプリの「履歴書」タブ用)

すべて state.json の記録 (出来事・掟・知識・統計) から数えて作る。記録にないことは書かない。
(2026-10-06 追加。本人の希望「それぞれの人の履歴書・職務経歴書も見られるようにしたい」)
"""
import re
from collections import Counter, defaultdict

PLACE = re.compile(r"(\S+の(?:林|川|丘|草地|原))")
SKILL_NAME = {"採集": "採集", "狩り": "狩り", "道具": "道具づくり", "火": "火おこし"}


def _era_of(day, eras):
    cur = eras[0][0] if eras else "F1"
    for era, d in eras:
        if day > d:
            cur = era
    return cur


def _joined_day(state, name):
    return next((e["day"] for e in state["events"] if e["type"] == "加わる" and name in e["text"]), state["day"])


def build(state):
    ev = state["events"]
    eras = [(x["era"], x["day"]) for x in state.get("era_log", [])]
    names = [p["name"] for p in state["people"]]
    out = []
    for p in state["people"]:
        n = p["name"]
        mine = [e for e in ev if e.get("who") == n or n in (e.get("data") or {}).get("hunters", [])]
        last_day = max([e["day"] for e in mine] + [0])
        death = next((e for e in ev if e["type"] == "死" and e.get("who") == n), None)

        # 職務経歴: 活動ごとの回数と成果
        gather = [e for e in mine if e["type"] == "採集"]
        g_ok = [e for e in gather if (e.get("data") or {}).get("kcal", 0) > 0]
        hunts = [e for e in mine if e["type"] == "狩り"]
        kills = [e for e in hunts if (e.get("data") or {}).get("killer") == n]
        places = Counter()
        for e in gather + hunts:
            m = PLACE.search(e["text"])
            if m:
                places[m.group(1)] += 1
        counts = Counter(e["type"] for e in mine if e.get("who") == n)
        gave = [e for e in mine if e["type"] == "分ける" and e.get("who") == n]
        given = Counter((e.get("data") or {}).get("to") for e in gave)
        recv = sum(1 for e in ev if e["type"] == "分ける" and (e.get("data") or {}).get("to") == n)

        # フェーズごとの仕事
        by_era = defaultdict(Counter)
        for e in mine:
            if e.get("who") == n or e["type"] == "狩り":
                if e["type"] in ("採集", "狩り", "探索", "休む", "住まい", "種まき", "蓄える", "蓄えから取る", "木から取る", "分ける", "話す"):
                    by_era[_era_of(e["day"], eras)][e["type"]] += 1

        # 経歴 (年表): 初めてのこと・大きな出来事
        if p.get("origin") == "よそから来た":
            hist = [{"day": _joined_day(state, n), "text": "よその群れから来て、村に加わる"}]
        elif p.get("origin") == "生まれた":
            hist = [{"day": p.get("born_day", 0), "text": f"村で生まれる (母 {p.get('mother', '-')})"}]
        else:
            hist = [{"day": 0, "text": "川辺のキャンプで 5 人と暮らし始める"}]
        firsts = {"採集": "初めて採集に出る", "狩り": "初めて狩りに出る", "探索": "初めて探索に出る", "蓄える": "初めてキャンプの蓄えに食べ物を入れる",
                  "種まき": "種をまく", "住まい": "住まいを建てる"}
        seen = set()
        for e in mine:
            t = e["type"]
            if t in firsts and t not in seen and (e.get("who") == n or t == "狩り"):
                seen.add(t)
                hist.append({"day": e["day"], "text": firsts[t] + " (" + e["text"] + ")"})
            if t == "狩り" and (e.get("data") or {}).get("killer") == n and "kill" not in seen:
                seen.add("kill")
                hist.append({"day": e["day"], "text": "初めてルクをしとめる (" + e["text"] + ")"})
            if t in ("けが", "死") and e.get("who") == n:
                hist.append({"day": e["day"], "text": e["text"]})
        for e in ev:
            if e["type"] == "住まい" and "ができた" in e["text"] and n in e["text"] and not any(e["text"] in h["text"] for h in hist):
                hist.append({"day": e["day"], "text": e["text"]})
            if e["type"] == "フェーズ" and (not death or e["day"] <= death["day"]):
                hist.append({"day": e["day"], "text": e["text"]})
        laws = [l for l in state.get("laws", []) if l.get("proposer") == n]
        first_law = next((l for l in sorted(laws, key=lambda l: l["day"]) if l["status"] == "採用" or l.get("changed")), None)
        if first_law:
            hist.append({"day": first_law["day"], "text": "初めて掟を提案する (のちに採用): 「" + first_law["text"][:60] + ("…" if len(first_law["text"]) > 60 else "") + "」"})
        if death:
            hist.append({"day": death["day"], "text": "(記録ここまで)"})
        hist.sort(key=lambda h: h["day"])

        kn = p.get("knowledge", [])
        klog = [k for k in state.get("knowledge_log", []) if k.get("who") == n and k.get("op") == "追加"]
        out.append({
            "name": n, "sex": p["sex"], "age": p["age"], "mass": p["mass"], "alive": p["alive"],
            "death": {"day": death["day"], "text": death["text"]} if death else None,
            "days": (death["day"] if death else state["day"]),
            "personality": p["personality"],
            "skills": {SKILL_NAME.get(k, k): v for k, v in p["skills"].items()},
            "items": p.get("items", []),
            "trust": {k: v for k, v in (p.get("trust") or {}).items() if k in names},
            "feeling": p.get("feeling"),
            "history": hist,
            "work": {
                "gather": len(gather), "gather_ok": len(g_ok), "gather_kcal": round(sum(e["data"]["kcal"] for e in g_ok)),
                "hunt": len(hunts), "kills": len(kills),
                "explore": counts["探索"], "rest": counts["休む"], "build": counts["住まい"], "sow": counts["種まき"],
                "pick": counts["木から取る"], "store": counts["蓄える"], "take": counts["蓄えから取る"], "talk": counts["話す"],
                "gave": len(gave), "gave_to": dict(given), "received": recv,
                "places": places.most_common(6),
            },
            "by_era": {k: dict(v) for k, v in sorted(by_era.items())},
            "laws": {"proposed": len(laws), "adopted": sum(1 for l in laws if l["status"] == "採用"),
                     "examples": [{"day": l["day"], "text": l["text"], "status": l["status"]} for l in sorted(laws, key=lambda l: l["day"])[-3:]]},
            "knowledge": {"now": len(kn), "added": len(klog), "labels": dict(Counter(k.get("label") for k in klog))},
            "last_day": last_day,
        })
    return out
