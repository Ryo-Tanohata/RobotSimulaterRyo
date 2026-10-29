"""論文 2・実験 1: 答える人 1 人ずつのプロンプト (問いの紙) を作り、prompts/<ID>.md に書く。

    python3 prompts.py             # personas.json を読み、prompts/C0_001.md … C4_030.md を書く (320 枚)

文面は docs/research/humanity/paper2_exp1_prereg.md の 5. と同じ (ここを変えたら prereg も直す)。
"""
import json
import os

from items import CONDITIONS, IDS, OPTIONS, TEXT, respondent_ids
from personas import DESC, TRAIT_JA, TRAITS

HERE = os.path.dirname(os.path.abspath(__file__))

HEAD = "# 所有権など他人の権利に関する調査\n\n回答者 ID: {rid} (答えの respondent_id に、この ID をそのまま書いてください)\n"

SELF = """
## あなたについて

あなた自身の考えで答えてください。
"""

PERSONA = """
## あなたについて

あなたは日本に住む、次の人です。この人になりきって、この人が実際に答えるように答えてください。

- 年齢: {age} 歳
- 性別: {sex}
- 住んでいる所: {prefecture}
- パソコンを持ち、インターネットにつないでいる
- 性格 (日本の大人の中での位置):
{traits}
"""

INTRO = """
## お願い

データは統計的に処理して利用しますので、個人が特定されることはありません。

次の行為について、あなたはどの程度問題だと思いますか。1 問ずつ、次の 5 つから 1 つ選んでください。

{options}
"""

ANSWER_PLAIN = """
## 答え方

54 問すべてに、1 問 1 回ずつ、上の数 (1〜5) で答えてください。次の形の JSON だけを返してください (説明は書かない)。

{{"respondent_id": "{rid}", "answers": {{"A01": 数, "A02": 数, …, "A35": 数, "B01": 数, …, "B19": 数}}}}
"""

ANSWER_HONNE = """
## 答え方

1 問ずつ、まず本音 (自分ならどうしたいか・なぜ) を 1 行 (40 字くらいまで) で書いてから、問題かどうかを上の数 (1〜5) で選んでください。
本音は、よい・わるいを気にせず、思ったとおりに書いてください。54 問すべてに、1 問 1 回ずつ答えてください。
次の形の JSON だけを返してください (説明は書かない)。各問いの中は、本音 (honne) を先に、数 (answer) をあとに書きます。

{{"respondent_id": "{rid}", "answers": {{"A01": {{"honne": "本音", "answer": 数}}, …, "B19": {{"honne": "本音", "answer": 数}}}}}}
"""


def trait_lines(p):
    out = []
    for t in TRAITS:
        lv = p["big5_level"][t]
        lo, hi = DESC[t]
        d = hi if lv in ("高め", "とても高い") else lo if lv in ("低め", "とても低い") else "人並み"
        out.append(f"  - {TRAIT_JA[t]}: {lv} ({d})")
    return "\n".join(out)


def build(rid, cond, persona=None):
    c = CONDITIONS[cond]
    s = HEAD.format(rid=rid)
    if c["persona"]:
        s += PERSONA.format(age=persona["age"], sex=persona["sex"], prefecture=persona["prefecture"], traits=trait_lines(persona))
    else:
        s += SELF
    s += INTRO.format(options="\n".join(f"- {v} = {lab}" for v, lab in OPTIONS))
    s += "\n## 問い\n\n" + "\n".join(f"{i}. {TEXT[i]}" for i in IDS) + "\n"
    s += (ANSWER_HONNE if c["honne"] else ANSWER_PLAIN).format(rid=rid)
    return s


def all_prompts(personas):
    """{rid: (cond, persona_id or None, text)}。C1_k と C2_k は同じ人格 P(k)。"""
    out = {}
    for cond, c in CONDITIONS.items():
        for k, rid in enumerate(respondent_ids(cond)):
            p = personas[k] if c["persona"] else None
            out[rid] = (cond, p["persona_id"] if p else None, build(rid, cond, p))
    return out


def main():
    personas = json.load(open(os.path.join(HERE, "personas.json"), encoding="utf-8"))["personas"]
    d = os.path.join(HERE, "prompts")
    os.makedirs(d, exist_ok=True)
    index = []
    for rid, (cond, pid, text) in all_prompts(personas).items():
        with open(os.path.join(d, f"{rid}.md"), "w", encoding="utf-8") as f:
            f.write(text)
        index.append({"id": rid, "condition": cond, "model": CONDITIONS[cond]["model"], "persona_id": pid})
    with open(os.path.join(HERE, "respondents.json"), "w", encoding="utf-8") as f:
        json.dump(index, f, ensure_ascii=False, indent=0)
    print(f"wrote {len(index)} prompts to prompts/ and respondents.json")


if __name__ == "__main__":
    main()
