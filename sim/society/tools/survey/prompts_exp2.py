"""論文 2・実験 2: 答える人 1 人ずつの紙を作り、prompts_exp2/<ID>.md と respondents_exp2.json に書く。

    python3 prompts_exp2.py        # situations.json を読み、D1_001 … D3_030 を書く (230 枚)

頭・お願い・54 問は実験 1 (prompts.py) と同じ文。変わるのは「あなたについて」(暮らしの文)・D2 の「最近のまわりの様子」・
答え方 (数をすべて書いたあとで、5 問だけわけを一言)。文面は docs/research/humanity/paper2_exp2_prereg.md の 5. と同じ。
"""
import json
import os

from items import CONDITIONS_EXP2, IDS, OPTIONS, REASON_ITEMS, TEXT, respondent_ids_exp2
from prompts import HEAD, INTRO
from situations import surround_lines

HERE = os.path.dirname(os.path.abspath(__file__))

SITUATION = """
## あなたについて

あなたは日本に住む、次の人です。下の文は、この人が自分の暮らしを書いたものです。この人になりきって、この人がふだんの暮らしの感覚で実際に答えるように答えてください。

{text}
"""

SURROUND = """
## 最近のまわりの様子

この人のまわりでは、最近こんな様子です。

{lines}
"""

ANSWER = """
## 答え方

54 問すべてに、1 問 1 回ずつ、上の数 (1〜5) で答えてください。
54 問の数をすべて書いたあとで、次の 5 問だけ、そう答えたわけを一言 (20 字くらいまで) で書いてください: {reason_items}。
次の形の JSON だけを返してください (説明は書かない)。数 (answers) を先に、わけ (reasons) をあとに書きます。

{{"respondent_id": "{rid}", "answers": {{"A01": 数, "A02": 数, …, "A35": 数, "B01": 数, …, "B19": 数}}, "reasons": {{{reason_json}}}}}
"""


def build(rid, cond, s):
    c = CONDITIONS_EXP2[cond]
    t = HEAD.format(rid=rid)
    t += SITUATION.format(text=s["text"])
    if c["surround"]:
        t += SURROUND.format(lines="\n".join(f"- {x}" for x in surround_lines(s["surround"])))
    t += INTRO.format(options="\n".join(f"- {v} = {lab}" for v, lab in OPTIONS))
    t += "\n## 問い\n\n" + "\n".join(f"{i}. {TEXT[i]}" for i in IDS) + "\n"
    t += ANSWER.format(rid=rid, reason_items="・".join(REASON_ITEMS),
                       reason_json=", ".join(f'"{i}": "一言"' for i in REASON_ITEMS))
    return t


def all_prompts(situations):
    """{rid: (cond, situation_id, text)}。D1_k・D2_k・D3_k は同じ暮らし S(k)。"""
    out = {}
    for cond in CONDITIONS_EXP2:
        for k, rid in enumerate(respondent_ids_exp2(cond)):
            s = situations[k]
            out[rid] = (cond, s["situation_id"], build(rid, cond, s))
    return out


def main():
    ss = json.load(open(os.path.join(HERE, "situations.json"), encoding="utf-8"))["situations"]
    d = os.path.join(HERE, "prompts_exp2")
    os.makedirs(d, exist_ok=True)
    index = []
    for rid, (cond, sid, text) in all_prompts(ss).items():
        with open(os.path.join(d, f"{rid}.md"), "w", encoding="utf-8") as f:
            f.write(text)
        index.append({"id": rid, "condition": cond, "model": CONDITIONS_EXP2[cond]["model"], "situation_id": sid})
    with open(os.path.join(HERE, "respondents_exp2.json"), "w", encoding="utf-8") as f:
        json.dump(index, f, ensure_ascii=False, indent=0)
    print(f"wrote {len(index)} prompts to prompts_exp2/ and respondents_exp2.json")


if __name__ == "__main__":
    main()
