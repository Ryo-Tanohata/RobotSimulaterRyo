"""論文 2・実験 2c: F1 (出来事 3 つ) と F2 (出来事 6 つ) の紙を作る。

    python3 prompts_exp2c.py       # situations.json と experiences_exp2c.json を読み、prompts_exp2c/F1_001 … F2_100.md と respondents_exp2c.json を書く

- F1_k・F2_k: D1_k と同じ紙の作り (prompts_exp2.build と同じ順・同じ文)。ちがうのは ID と、
  「あなたについて」のすぐあとに入る節「## これまでにあったこと」だけ (test_survey.py が確かめる)。
- 暮らしの文は D1_k と同じ S(k)。出来事は experiences_exp2c.json の F1・F2 (F2 は F1 の 3 つをふくむ)。
- situations.json・prompts_exp2/・prompts_exp2b/ には書かない。
文面は docs/research/humanity/paper2_exp2c_prereg.md の 5. と同じ。
"""
import json
import os

import prompts_exp2
from experiences import lines
from items import CONDITIONS_EXP2C, respondent_ids_exp2c

HERE = os.path.dirname(os.path.abspath(__file__))

HISTORY = """
## これまでにあったこと

この人には、これまでに次のようなことがありました。

{lines}
"""


def build(rid, s, exps):
    """D1 の紙 (prompts_exp2.build) と同じ順・同じ文。「あなたについて」と「お願い」の間に HISTORY を入れる。"""
    t = prompts_exp2.HEAD.format(rid=rid)
    t += prompts_exp2.SITUATION.format(text=s["text"])
    t += HISTORY.format(lines="\n".join(f"- {x}" for x in lines(exps)))
    t += prompts_exp2.INTRO.format(options="\n".join(f"- {v} = {lab}" for v, lab in prompts_exp2.OPTIONS))
    t += "\n## 問い\n\n" + "\n".join(f"{i}. {prompts_exp2.TEXT[i]}" for i in prompts_exp2.IDS) + "\n"
    t += prompts_exp2.ANSWER.format(rid=rid, reason_items="・".join(prompts_exp2.REASON_ITEMS),
                                    reason_json=", ".join(f'"{i}": "一言"' for i in prompts_exp2.REASON_ITEMS))
    return t


def all_prompts(situations, assignments):
    """{rid: (cond, situation_id, 出来事の ID の列, text)}。F1_k・F2_k は D1_k と同じ暮らし S(k)。"""
    out = {}
    for cond in CONDITIONS_EXP2C:
        for k, rid in enumerate(respondent_ids_exp2c(cond)):
            s, a = situations[k], assignments[k]
            assert a["situation_id"] == s["situation_id"]
            out[rid] = (cond, s["situation_id"], a[cond], build(rid, s, a[cond]))
    return out


def main():
    ss = json.load(open(os.path.join(HERE, "situations.json"), encoding="utf-8"))["situations"]
    asg = json.load(open(os.path.join(HERE, "experiences_exp2c.json"), encoding="utf-8"))["assignments"]
    d = os.path.join(HERE, "prompts_exp2c")
    os.makedirs(d, exist_ok=True)
    index = []
    for rid, (cond, sid, exps, text) in all_prompts(ss, asg).items():
        with open(os.path.join(d, f"{rid}.md"), "w", encoding="utf-8") as f:
            f.write(text)
        index.append({"id": rid, "condition": cond, "model": CONDITIONS_EXP2C[cond]["model"], "situation_id": sid, "experiences": exps})
    with open(os.path.join(HERE, "respondents_exp2c.json"), "w", encoding="utf-8") as f:
        json.dump(index, f, ensure_ascii=False, indent=0)
    print(f"wrote {len(index)} prompts to prompts_exp2c/ and respondents_exp2c.json")


if __name__ == "__main__":
    main()
