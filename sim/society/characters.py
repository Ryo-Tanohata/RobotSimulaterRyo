"""キャラクター: 状況を文章にしてキャラクター (Claude のサブエージェント) に渡す「お題」と、答えの反映。

1 日に 2 回だけ考える:
- 夕方 (evening): 今日の出来事を受けて、キャンプで話すこと・食べ物を分けるか
- 夜 (night): 聞いた話も含めて振り返り、知識を更新し、明日の予定を決める (集まりの日は掟の提案と投票も)
お題には、そのキャラクターが知っていること (自分の経験・聞いた話・知識・掟) だけを書く。他人の心の中は書かない。
"""
import json

import knowledge
from world import ACTIVITIES, season

RULES = """あなたは、ある小さな世界に暮らす一人の人間を演じます。
- この世界の外の知識 (現実の地名・国・歴史・宗教・王・お金 など) は持っていない前提で考えてください
- 自分が経験したこと、聞いたこと、覚えていることだけをもとに考えてください
- 答えは JSON だけを出力してください (前後に説明を書かない)。JSON の中の文章はすべて日本語で書いてください"""


def _alive(state):
    return [p for p in state["people"] if p["alive"]]


def _me(state, p):
    days = f"{state['day']} 日目 ({season(state['day'])})"
    pers = "、".join(f"{k} {v:.1f}" for k, v in p["personality"].items())
    sk = "、".join(f"{k} {v:.2f}" for k, v in p["skills"].items())
    food = sum(f["kcal"] for f in p["food"])
    meat = [f for f in p["food"] if f["kind"] == "肉"]
    trust = "、".join(f"{n} {v:+.1f}" for n, v in p["trust"].items() if any(q["name"] == n and q["alive"] for q in state["people"]))
    return (f"あなたは {p['name']} ({p['sex']}、{p['age']} 歳)。今は {days}。\n"
            f"性格 (0〜1): {pers}\n技能 (0〜1): {sk}\n"
            f"空腹 {p['hunger']:.1f} (0 = 満腹、1 = 限界) / 疲れ {p['fatigue']:.1f} / けが {'あり' if p['injured'] else 'なし'}\n"
            f"持ち物: 食べ物 {food} kcal" + (f" (うち肉 {sum(f['kcal'] for f in meat)} kcal。肉は 2 日で腐る)" if meat else "")
            + (f"、{'・'.join(p['items'])}" if p["items"] else "") + "\n"
            f"仲間への信頼 (-1〜+1): {trust}\n")


def _knowledge(p):
    return "\n".join(f"- [{k['id']}] {k['text']} (確かさ {k['confidence']:.1f})" for k in p["knowledge"])


def _laws(state, with_pending=False):
    rows = [f"- [{l['id']}] {l['text']} ({l['status']}、{l['proposer']} が提案)" for l in state["laws"]
            if l["status"] == "採用" or (with_pending and l["status"] == "提案")]
    return "\n".join(rows) or "(まだない)"


def _today(state, p):
    ev = {e["id"]: e for e in state["events"]}
    t = p["today"]
    if not t:
        return "この世界での最初の夜。まだ何もしていない。キャンプは川のそばにある。"
    lines = [f"今日は「{t.get('activity', '休む')}」で {t.get('place', 'キャンプ')} へ行った (歩いた距離 約 {t.get('walked_m', 0)} m)。"]
    for i in t.get("events", []):
        if i in ev:
            lines.append(f"- [出来事 {i}] {ev[i]['text']}")
    others = [e for e in state["events"] if e["day"] == state["day"] and e["id"] not in t.get("events", [])
              and e["type"] in ("狩り", "分ける", "けが", "死", "火", "育つ", "夜", "腐る") and e.get("who") != p["name"]]
    if others:
        lines.append("キャンプに戻って見聞きしたこと:")
        lines += [f"- [出来事 {e['id']}] {e['text']}" for e in others[-8:]]
    return "\n".join(lines)


def _heard(p, n=8):
    return "\n".join(f"- [出来事 {h['event']}] {h['day']} 日目、{h['from']}: 「{h['text']}」" for h in p["heard"][-n:]) or "(なし)"


def evening_prompt(state, p):
    names = [q["name"] for q in _alive(state) if q is not p]
    return f"""{RULES}

{_me(state, p)}
## 今日のこと
{_today(state, p)}

## 覚えていること
{_knowledge(p)}

## 集団の掟
{_laws(state)}

## 最近聞いた話
{_heard(p)}

## いま
夕方。キャンプの火のまわりに {'、'.join(names)} がいる。
話したいことがあれば話してください (0〜2 つ。相手は仲間の名前か「みんな」)。
持っている食べ物を誰かに分けるなら、相手と量 (kcal) を書いてください (分けなくてもよい)。

## 答えの形 (JSON)
{{"say": [{{"to": "みんな", "text": "..."}}], "give": [{{"to": "名前", "kcal": 1000}}]}}"""


def night_prompt(state, p, tonight_heard, gifts):
    places = "\n".join(f"- {pl['id']}: {pl['label']}" for pl in state["places"])
    heard = "\n".join(f"- [出来事 {h['event']}] {h['from']}: 「{h['text']}」" for h in tonight_heard) or "(なし)"
    got = "\n".join(f"- [出来事 {g['event']}] {g['from']} から {g['kcal']} kcal もらった" for g in gifts) or "(なし)"
    meeting = knowledge.is_meeting(state["day"])
    names = [q["name"] for q in _alive(state) if q is not p]
    law_part = (f"""
## 今日は集まりの日
提案されている掟と、今の掟に賛成か反対かを投票してください (反対が多い掟は廃止される)。
{_laws(state, with_pending=True)}""" if meeting else "")
    return f"""{RULES}

{_me(state, p)}
## 今日のこと
{_today(state, p)}

## 今夜キャンプで聞いた話
{heard}

## もらった食べ物
{got}

## 覚えていること
{_knowledge(p)}

## 集団の掟
{_laws(state)}
{law_part}
## いま
夜。寝る前に今日を振り返ってください。
1. 覚えていることを更新する: 新しく分かったことを追加 (きっかけの出来事の番号を because に書く)、確かさを変える、間違っていたら忘れる
2. みんなで守りたい決まりがあれば、掟として提案できる (なければ null)
3. 明日の予定を決める。活動は {' / '.join(ACTIVITIES)} から 1 つ、場所は下の一覧の id から 1 つ、一緒に行きたい人 ({'、'.join(names)}) がいれば書く
4. 今日の気持ちを一言

場所の一覧:
{places}

## 答えの形 (JSON)
{{"knowledge": [{{"op": "add", "text": "...", "because": [出来事の番号], "confidence": 0.6}},
               {{"op": "update", "id": "k12", "confidence": 0.3}}, {{"op": "remove", "id": "k15"}}],
 "proposal": {{"text": "...", "because": [出来事の番号]}},
 "votes": [{{"id": "L0", "agree": true}}],
 "plan": {{"activity": "採集", "place": "camp", "with": []}},
 "feeling": "..."}}"""


def parse(text):
    """答えの文章から JSON を取り出す (前後に余計な文があっても読めるように)"""
    if isinstance(text, dict):
        return text
    s, e = text.find("{"), text.rfind("}")
    if s < 0 or e < 0:
        return {}
    try:
        return json.loads(text[s:e + 1])
    except json.JSONDecodeError:
        return {}


def apply_evening(state, answers):
    """夕方の答え {名前: 答え} → 話す (出来事に記録し、聞き手に届ける) と分ける (の予定)"""
    from world import log
    alive = {p["name"]: p for p in _alive(state)}
    gives, tonight = [], {n: [] for n in alive}
    for name, raw in answers.items():
        a = parse(raw)
        if name not in alive:
            continue
        for s in (a.get("say") or [])[:2]:
            text = str(s.get("text", ""))[:200]
            to = s.get("to", "みんな")
            if not text:
                continue
            eid = log(state, "話す", name, f"{name} → {to}: 「{text}」", to=to)
            for n in alive:
                if n != name and (to == "みんな" or to == n):
                    h = {"day": state["day"], "from": name, "text": text, "event": eid}
                    alive[n]["heard"].append(h)
                    tonight[n].append(h)
        for g in (a.get("give") or [])[:len(alive)]:
            if g.get("to") in alive:
                gives.append({"from": name, "to": g["to"], "kcal": g.get("kcal", 0)})
    for p in alive.values():
        p["heard"] = p["heard"][-30:]
    return gives, tonight


def gifts_for(state, name):
    return [{"from": e["who"], "kcal": e["data"]["kcal"], "event": e["id"]} for e in state["events"]
            if e["day"] == state["day"] and e["type"] == "分ける" and e.get("data", {}).get("to") == name]


def apply_night(state, answers):
    """夜の答え → 知識の更新・掟の提案と投票・明日の予定・気持ち"""
    alive = {p["name"]: p for p in _alive(state)}
    places = {pl["id"] for pl in state["places"]}
    for name, raw in answers.items():
        p = alive.get(name)
        if not p:
            continue
        a = parse(raw)
        knowledge.apply_updates(state, p, a.get("knowledge"))
        prop = a.get("proposal")
        if isinstance(prop, dict) and prop.get("text"):
            knowledge.propose(state, p, prop["text"], prop.get("because"))
        knowledge.vote(state, p, a.get("votes"))
        plan = a.get("plan") or {}
        act = plan.get("activity") if plan.get("activity") in ACTIVITIES else "休む"
        place = plan.get("place") if plan.get("place") in places else "camp"
        p["plan"] = {"activity": act, "place": place, "with": [w for w in plan.get("with", []) if w in alive]}
        p["feeling"] = str(a.get("feeling", ""))[:120]
    if knowledge.is_meeting(state["day"]):
        from world import log
        for msg in knowledge.settle_meeting(state):
            log(state, "掟", None, msg)
