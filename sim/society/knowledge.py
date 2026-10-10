"""学び: 知識と掟の保存・更新・ラベル付け (docs/society_plan.md 5 章・6 章)。

ラベル (模倣と創発の見分け方):
- 最初の知識: 最初に与えたもの (模倣の基準)
- 創発: 世界で起きた出来事 (話す以外) をきっかけに生まれたもの
- 伝承: 他人の話だけをきっかけにしたもの (元をたどれるように、誰から聞いたかを残す)
- 知識の再現の疑い: きっかけの出来事がないもの (Claude が元々持つ人類の知識から来た可能性)
"""
import archive  # 古い出来事は年ごとのファイルにしまう (2026-10-10)。しまった番号も「ある」と数え、種類は「話す以外」(話すは残している)

INITIAL = [
    "食べると空腹が減る。川の水を飲むと、のどの渇きが減る",
    "夜はザガ (捕食者) が出る",
    "仲間は名前で呼び合える",
]
MEETING_EVERY = 7  # 掟の集まり (日ごと)
MAX_ITEMS = 30


def init(state):
    kid = 0
    for p in state["people"]:
        p["knowledge"] = []
        for text in INITIAL:
            p["knowledge"].append({"id": f"k{kid}", "text": text, "confidence": 1.0, "label": "最初の知識",
                                   "because": [], "from": None, "day": 0, "updated": 0})
            kid += 1
    state["next_knowledge"] = kid
    state["laws"] = []       # {"id","text","proposer","day","status": 提案|採用|廃止, "votes": {name: bool}, "because": [...]}
    state["next_law"] = 0
    state["knowledge_log"] = []  # 変化の履歴 {"day","who","op","id","text","label"}


def _label(state, because):
    ev = archive.Events(state)  # しまう前の {番号: 出来事} と同じ答え (archive.py)
    kinds = [ev.type(i) for i in because if i in ev]
    if any(k != "話す" for k in kinds):
        return "創発"
    if kinds:
        return "伝承"
    return "知識の再現の疑い"


def apply_updates(state, person, updates):
    """夜の振り返りの答え (knowledge の配列) を反映する"""
    day = state["day"]
    known = {k["id"]: k for k in person["knowledge"]}
    valid_events = archive.Events(state)  # しまった番号も入る (しまう前と同じ)
    for u in updates or []:
        op = u.get("op")
        if op == "add" and u.get("text"):
            raw = u.get("because") or []
            raw = raw if isinstance(raw, list) else [raw]  # 番号 1 つだけ (リストでない) の答えも読む
            because = [i for i in raw if isinstance(i, int) and i in valid_events]
            label = _label(state, because)
            src = None
            if label == "伝承":
                src = valid_events.who(because[0])  # 伝承のきっかけは話すだけ (話すは state.json に残している)
            k = {"id": f"k{state['next_knowledge']}", "text": str(u["text"])[:200],
                 "confidence": float(max(0, min(1, u.get("confidence", 0.6)))), "label": label,
                 "because": because, "from": src, "day": day, "updated": day}
            state["next_knowledge"] += 1
            person["knowledge"].append(k)
            state["knowledge_log"].append({"day": day, "who": person["name"], "op": "追加", "id": k["id"], "text": k["text"], "label": label})
        elif op == "update" and u.get("id") in known:
            k = known[u["id"]]
            if "confidence" in u:
                k["confidence"] = float(max(0, min(1, u["confidence"])))
            if u.get("text") and k["label"] != "最初の知識":
                k["text"] = str(u["text"])[:200]
            k["updated"] = day
            state["knowledge_log"].append({"day": day, "who": person["name"], "op": "修正", "id": k["id"], "text": k["text"], "label": k["label"]})
        elif op == "remove" and u.get("id") in known and known[u["id"]]["label"] != "最初の知識":
            k = known[u["id"]]
            person["knowledge"].remove(k)
            state["knowledge_log"].append({"day": day, "who": person["name"], "op": "忘れる", "id": k["id"], "text": k["text"], "label": k["label"]})
    # 多すぎたら確信度の低いものから忘れる
    extra = [k for k in person["knowledge"] if k["label"] != "最初の知識"]
    while len(extra) > MAX_ITEMS:
        k = min(extra, key=lambda k: (k["confidence"], k["updated"]))
        person["knowledge"].remove(k)
        extra.remove(k)


def propose(state, person, text, because):
    if not text:
        return
    valid = archive.Events(state)  # しまった番号も入る (しまう前と同じ)
    because = [i for i in (because or []) if isinstance(i, int) and i in valid]
    law = {"id": f"L{state['next_law']}", "text": str(text)[:200], "proposer": person["name"], "day": state["day"],
           "status": "提案", "votes": {}, "because": because, "label": _label(state, because), "changed": state["day"]}
    state["next_law"] += 1
    state["laws"].append(law)


def vote(state, person, votes):
    laws = {l["id"]: l for l in state["laws"]}
    for v in votes or []:
        l = laws.get(v.get("id"))
        if l and l["status"] in ("提案", "採用"):
            l["votes"][person["name"]] = bool(v.get("agree"))
            l.setdefault("vote_log", []).append({"day": state["day"], "who": person["name"], "agree": bool(v.get("agree")),
                                                 "reason": str(v.get("reason", ""))[:120],
                                                 "against": str(v.get("against", ""))[:120]})


def is_meeting(day):
    return day > 0 and day % MEETING_EVERY == 0


def settle_meeting(state):
    """集まりの日: 過半数の賛成で採用、採用済みの掟は過半数の反対で廃止"""
    alive = [p["name"] for p in state["people"] if p["alive"] and not p.get("child")]  # 子 (Society 2.0) は投票しない
    out = []
    for l in state["laws"]:
        yes = sum(1 for n in alive if l["votes"].get(n) is True)
        no = sum(1 for n in alive if l["votes"].get(n) is False)
        if l["status"] == "提案" and yes * 2 > len(alive):
            l["status"], l["changed"] = "採用", state["day"]
            out.append(f"掟「{l['text']}」が採用された (賛成 {yes} / {len(alive)})")
        elif l["status"] == "採用" and no * 2 > len(alive):
            l["status"], l["changed"] = "廃止", state["day"]
            out.append(f"掟「{l['text']}」が廃止された (反対 {no} / {len(alive)})")
        l["votes"] = {}
    return out
