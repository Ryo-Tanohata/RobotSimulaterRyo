"""論文 2・実験 2b: E1 (所有の様子) と D2r (D2 のくり返し) の紙を作る。

    python3 prompts_exp2b.py       # situations.json を読み、prompts_exp2b/E1_001 … E1_100.md と respondents_exp2b.json を書く

- E1_k: D2_k と同じ紙の作り (prompts_exp2.build)。ちがうのは「最近のまわりの様子」の 4 行の中身だけ
  (situations.OWN_SURROUND_LINES。0/1 の組は D2_k と同じ situations.json の surround)。
- D2r_k: D2_k の紙 (prompts_exp2/D2_k.md) を、そのまま使う。新しいファイルは作らない。紙の中の ID も D2_k のまま
  (agent に渡す指示の文も D2 と 1 字も同じにするため。survey_workflow_exp2b.js が D2r_k としてしまう)。
  ここでは、D2 の紙を作り直して、ディスクの prompts_exp2/D2_k.md と 1 バイトも同じかを確かめる (違えば止まる)。
文面は docs/research/humanity/paper2_exp2b_prereg.md の 5. と同じ。
"""
import json
import os

import prompts_exp2
from items import CONDITIONS_EXP2B, prompt_id_exp2b, respondent_ids_exp2b
from situations import OWN_SURROUND_LINES, surround_lines

HERE = os.path.dirname(os.path.abspath(__file__))


def build_e1(rid, s):
    """D2 の紙の作り (prompts_exp2.build と同じ順・同じ文) で、様子の行だけ OWN_SURROUND_LINES にする。"""
    t = prompts_exp2.HEAD.format(rid=rid)
    t += prompts_exp2.SITUATION.format(text=s["text"])
    t += prompts_exp2.SURROUND.format(lines="\n".join(f"- {x}" for x in surround_lines(s["surround"], OWN_SURROUND_LINES)))
    t += prompts_exp2.INTRO.format(options="\n".join(f"- {v} = {lab}" for v, lab in prompts_exp2.OPTIONS))
    t += "\n## 問い\n\n" + "\n".join(f"{i}. {prompts_exp2.TEXT[i]}" for i in prompts_exp2.IDS) + "\n"
    t += prompts_exp2.ANSWER.format(rid=rid, reason_items="・".join(prompts_exp2.REASON_ITEMS),
                                    reason_json=", ".join(f'"{i}": "一言"' for i in prompts_exp2.REASON_ITEMS))
    return t


def prompt_file(rid):
    """リポジトリの中の紙の場所 (sim/society/tools/survey からの相対)。"""
    pid = prompt_id_exp2b(rid)
    return f"prompts_exp2b/{rid}.md" if pid == rid else f"prompts_exp2/{pid}.md"


def all_prompts(situations):
    """{rid: (cond, situation_id, 紙に書いた ID, text)}。E1_k・D2r_k は D2_k と同じ暮らし S(k)・同じ 0/1 の組。"""
    out = {}
    for cond in CONDITIONS_EXP2B:
        for k, rid in enumerate(respondent_ids_exp2b(cond)):
            s = situations[k]
            pid = prompt_id_exp2b(rid)
            text = build_e1(rid, s) if cond == "E1" else prompts_exp2.build(pid, CONDITIONS_EXP2B[cond]["prompt_of"], s)
            out[rid] = (cond, s["situation_id"], pid, text)
    return out


def main():
    ss = json.load(open(os.path.join(HERE, "situations.json"), encoding="utf-8"))["situations"]
    d = os.path.join(HERE, "prompts_exp2b")
    os.makedirs(d, exist_ok=True)
    index = []
    for rid, (cond, sid, pid, text) in all_prompts(ss).items():
        path = os.path.join(HERE, prompt_file(rid))
        if cond == "E1":
            with open(path, "w", encoding="utf-8") as f:
                f.write(text)
        else:
            on_disk = open(path, encoding="utf-8").read()
            if on_disk != text:
                raise SystemExit(f"{prompt_file(rid)} は作り直した D2 の紙と違う。D2r は D2 と同じ紙でなければならない")
        index.append({"id": rid, "condition": cond, "model": CONDITIONS_EXP2B[cond]["model"], "situation_id": sid,
                      "prompt_id": pid, "prompt_file": prompt_file(rid)})
    with open(os.path.join(HERE, "respondents_exp2b.json"), "w", encoding="utf-8") as f:
        json.dump(index, f, ensure_ascii=False, indent=0)
    n_e1 = sum(r["condition"] == "E1" for r in index)
    print(f"wrote {n_e1} E1 prompts to prompts_exp2b/; D2r uses prompts_exp2/D2_*.md ({len(index) - n_e1}, checked identical); "
          f"respondents_exp2b.json ({len(index)})")


if __name__ == "__main__":
    main()
