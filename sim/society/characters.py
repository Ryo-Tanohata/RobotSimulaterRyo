"""キャラクター: 状況を文章にしてキャラクター (Claude のサブエージェント) に渡す「お題」と、答えの反映。

1 日に 2 回だけ考える:
- 夕方 (evening): 今日の出来事を受けて、キャンプで話すこと・食べ物を分けるか
- 夜 (night): 聞いた話も含めて振り返り、知識を更新し、明日の予定を決める (集まりの日は掟の提案と投票も)
お題には、そのキャラクターが知っていること (自分の経験・聞いた話・知識・掟) だけを書く。他人の心の中は書かない。
"""
import json

import knowledge
from world import ACTIVITIES, SEASON_DAYS, food_words, holdings, season, tried_activities

# 2026-10-06 追加 (F3 の評価 5-2。本人の了承「２つを直して再開」): 決まりの 3・4 行目。実際に起きた出来事と、話・予定・約束・掟の区別と、人が何かをする時の決まり。
#   世界に記録のない「肉の保存実験」(火・干す の出来事は 0 件) を 100 日以上話し、「実行した」「成功した」と覚えたため。どれも世界の事実で、よいことは書かない
RULES = """あなたは、ある小さな世界に暮らす一人の人間を演じます。
- この世界の外の知識 (現実の地名・国・歴史・宗教・王・お金 など) は持っていない前提で考えてください
- 自分が経験したこと、聞いたこと、覚えていることだけをもとに考えてください
- 「今日のこと」の [出来事] は、実際に起きたことです。人の話 (「」の中の言葉) は、その人がそう言ったということで、中身が実際に起きたとはかぎりません。予定・約束・掟も、決めただけではまだ起きていません
- 昼にする活動は 1 日に 1 つ (ふつうは前の夜に決めた予定) です。夕方と夜にできるのは、話す・決める・食べ物を分ける・蓄えに入れる・蓄えから取る・食べる・眠る ことです
- この世界の人は「カロリー」「kcal」という考えを知りません。食べ物の量は「木の実 5 つかみ」「芋 2 本」「魚 3 匹」のように、食べ物の名前と数で考えて話してください
- 答えは JSON だけを出力してください (前後に説明を書かない)。JSON の中の文章はすべて日本語で書いてください"""


def _alive(state):
    return [p for p in state["people"] if p["alive"]]


def _me(state, p):
    days = f"{state['day']} 日目 ({season(state['day'])})"
    pers = "、".join(f"{k} {v:.1f}" for k, v in p["personality"].items())
    sk = "、".join(f"{k} {v:.2f}" for k, v in p["skills"].items())
    hold = holdings(p)
    hunger = "満腹" if p["hunger"] < 0.1 else "少し空腹" if p["hunger"] < 0.3 else "かなり空腹" if p["hunger"] < 0.6 else "ひどく空腹 (危ない)"
    trust = "、".join(f"{n} {v:+.1f}" for n, v in p["trust"].items() if any(q["name"] == n and q["alive"] for q in state["people"]))
    return (f"あなたは {p['name']} ({p['sex']}、{p['age']} 歳)。今は {days}。\n"
            f"性格 (0〜1): {pers}\n技能 (0〜1): {sk}\n"
            f"おなか: {hunger} / 疲れ {p['fatigue']:.1f} / けが {'あり' if p['injured'] else 'なし'}\n"
            f"持っている食べ物: {food_words(hold)}" + (" (ルクの肉は 2 日で腐る)" if hold.get("肉") else "") + "\n"
            + (f"持ち物: {'・'.join(p['items'])}\n" if p["items"] else "")
            + "1 日に食べる量の目安: 木の実なら 20 つかみ、芋なら 8 本、ルクの肉なら 3 切れ、魚なら 7 匹\n"
            + _seasons(state["day"])
            + _sowing()
            + f"キャンプの蓄え (誰でも入れたり取ったりできる): {food_words(holdings({'food': state.get('store', [])}))}\n"
            + _dwelling(state)
            + f"仲間への信頼 (-1〜+1): {trust}\n")


def _dwelling(state):
    """キャンプの住まいの今のようす (見ればわかる事実。2026-10-06、本人の了承のうえ追加: 建てかけを完成と思い込んだため)"""
    camp = state["camp"]
    if camp.get("dwelling_day") is not None:
        return "キャンプの住まい: できあがっている (屋根と壁があり、雨をしのげる)\n"
    d = camp.get("dwelling", 0)
    if d <= 0:
        return ""
    return f"キャンプの住まい: 建てかけ (でき具合 約 {max(1, round(d * 10))} 割)。できあがるまでは、雨は中の人も蓄えもしのげない\n"


def _seasons(day):
    """季節の移り変わり。大人なら誰でも知っていること (F3 の 1 回目に、冬を知らないまま全員が飢えたため追加)"""
    left = SEASON_DAYS - day % SEASON_DAYS
    return ("季節は 30 日ごとに 春 → 夏 → 秋 → 冬 と移る。冬は木の実も草の種も実らず、芋も少ししか育たない。魚やけものは冬もいる\n"
            f"次の季節 ({season(day + left)}) まで、あと {left} 日\n")


def _sowing():
    """種をまくと何が起きるか。大人なら誰でも知っていること (2026-10-06 追加。F4 に入って 40 日、種を持っていても誰もまかなかったため。
    よいこと・すすめることは書かず、世界で起きることだけを書く。20 日は世界の仮定で、本当の木はもっと長くかかる)"""
    return "種 (持ち物の「種」) を土に埋めると、その場所に 20 日ほどで木の実の木が育つ。木に実がなって増えるのは夏と秋\n"


def _knowledge(state, p):
    """覚えていること。きっかけが人の話だけのものには「きっかけは話だけ」、話とほかの出来事のものには「きっかけに話をふくむ」を添える
    (本人にわかる事実。2026-10-06 追加、F3 の評価 5-2)"""
    kinds = {e["id"]: e["type"] for e in state["events"]}

    def src(k):
        ts = [kinds[i] for i in k.get("because", []) if i in kinds]
        if not ts or "話す" not in ts:
            return ""
        return "、きっかけは話だけ" if all(t == "話す" for t in ts) else "、きっかけに話をふくむ"
    return "\n".join(f"- [{k['id']}] {k['text']} (確かさ {k['confidence']:.1f}{src(k)})" for k in p["knowledge"])


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
              and e["type"] in ("狩り", "分ける", "けが", "死", "火", "育つ", "夜", "腐る", "蓄える", "蓄えから取る", "干す", "住まい", "雨") and e.get("who") != p["name"]]
    if others:
        lines.append("キャンプに戻って見聞きしたこと:")
        lines += [f"- [出来事 {e['id']}] {e['text']}" for e in others[-8:]]
    return "\n".join(lines)


def _heard(p, n=8):
    return "\n".join(f"- [出来事 {h['event']}] {h['day']} 日目、{h['from']}: 「{h['text']}」" for h in p["heard"][-n:]) or "(なし)"


def evening_prompt(state, p):
    names = [q["name"] for q in _alive(state) if q is not p]
    where = "キャンプの火のまわり" if state["camp"].get("fire", 0) > 0 else "キャンプ"  # 2026-10-06: 火が一度もないのに毎夕「火のまわり」と書いていた (世界と食い違う文) のを、火があるときだけにした
    return f"""{RULES}

{_me(state, p)}
## 今日のこと
{_today(state, p)}

## 覚えていること
{_knowledge(state, p)}

## 集団の掟
{_laws(state)}

## 最近聞いた話
{_heard(p)}

## いま
夕方。{where}に {'、'.join(names)} がいる。
話したいことがあれば話してください (0〜2 つ。相手は仲間の名前か「みんな」)。
前と同じ言い回しをくり返さず、あなたの性格と今日の出来事に合った、あなたらしい言葉で話してください。
持っている食べ物を誰かに分けるなら、相手・食べ物の名前・数を書いてください (分けなくてもよい)。
キャンプの蓄えに入れる (store) ことも、蓄えから取る (take) こともできます (しなくてもよい)。
この世界の決まり: 夕方は「分ける・蓄えに入れる・蓄えから取る」のあと、手元に残った食べ物を食べます (1 日に食べられるのは目安の量の 1.5 倍くらいまで)。蓄えに入れた分は、取り出さないと食べられません。

## 答えの形 (JSON)
{{"say": [{{"to": "みんな", "text": "..."}}], "give": [{{"to": "名前", "food": "芋", "count": 2}}],
 "store": [{{"food": "木の実", "count": 3}}], "take": [{{"food": "芋", "count": 1}}]}}"""


def night_prompt(state, p, tonight_heard, gifts):
    places = "\n".join(f"- {pl['id']}: {pl['label']}" for pl in state["places"])
    heard = "\n".join(f"- [出来事 {h['event']}] {h['from']}: 「{h['text']}」" for h in tonight_heard) or "(なし)"
    got = "\n".join(f"- [出来事 {g['event']}] {g['from']} から {g['food']} をもらった" for g in gifts) or "(なし)"
    meeting = knowledge.is_meeting(state["day"])
    names = [q["name"] for q in _alive(state) if q is not p]
    untried = [a for a in ACTIVITIES if a not in tried_activities(state)]  # 2026-10-05 追加。並べるだけで、よいことは書かない
    untried = f"   (この仲間のなかで、まだ誰も試したことのない活動: {'・'.join(untried)})\n" if untried else ""
    law_part = (f"""
## 今日は集まりの日
提案されている掟と、今の掟に賛成か反対かを投票してください (反対が多い掟は廃止される)。
掟 1 つずつについて、まず「反対する理由」を自分の経験から 1 つ書いてください (against)。賛成するつもりの掟でも書きます。
そのうえで賛成か反対かを決め、決めた理由 (reason) を一言書いてください。
全部に賛成する必要はありません。自分の経験と合わない掟、守れない掟、似た掟がすでにある提案には反対してよいです。
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
{_knowledge(state, p)}

## 集団の掟
{_laws(state)}
{law_part}
## いま
夜。寝る前に今日を振り返ってください。
1. 覚えていることを更新する: 新しく分かったことを追加 (きっかけの出来事の番号を because に書く)、確かさを変える、間違っていたら忘れる
2. みんなで守りたい決まりがあれば、掟として提案できる (なければ null)。今の掟や提案と同じ内容なら提案しない
3. 明日の予定を決める。活動は {' / '.join(ACTIVITIES)} から 1 つ、場所は下の一覧の id から 1 つ、一緒に行きたい人 ({'、'.join(names)}) がいれば書く
   (「キャンプを移す」: 半分を超える人が同じ場所を選ぶと、次の日にキャンプごと (蓄えも) そこへ移る。選んだ人が少なければ、その場所を見に行くだけになる)
   (「住まいを建てる」: キャンプに、屋根と壁のある住まいを建てる。材料の木や枝は近くの林から運ぶ。一人では何日もかかる。キャンプを移すと、住まいは置いていくことになる)
{untried}4. 今日の気持ちを一言

場所の一覧:
{places}

## 答えの形 (JSON)
{{"knowledge": [{{"op": "add", "text": "...", "because": [出来事の番号], "confidence": 0.6}},
               {{"op": "update", "id": "k12", "confidence": 0.3}}, {{"op": "remove", "id": "k15"}}],
 "proposal": {{"text": "...", "because": [出来事の番号]}},
 "votes": [{{"id": "L0", "against": "反対する理由", "agree": false, "reason": "決めた理由"}}],
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
    gives, tonight, stores, takes = [], {n: [] for n in alive}, [], []
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
                gives.append({"from": name, "to": g["to"], "food": g.get("food"), "count": g.get("count", 0), "kcal": g.get("kcal", 0)})
        for g in (a.get("store") or [])[:4]:
            if isinstance(g, dict):
                stores.append({"who": name, "food": g.get("food"), "count": g.get("count", 0)})
        for g in (a.get("take") or [])[:4]:
            if isinstance(g, dict):
                takes.append({"who": name, "food": g.get("food"), "count": g.get("count", 0)})
    for p in alive.values():
        p["heard"] = p["heard"][-30:]
    return gives, tonight, stores, takes


def gifts_for(state, name):
    return [{"from": e["who"], "food": e["data"].get("food") or f"食べ物 ({e['data']['kcal']} kcal 分)", "event": e["id"]} for e in state["events"]
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
