"""論文 2・実験 1 の道具の試し (LLM は使わない)。  python3 test_survey.py

1. items.py の問いと予想が、docs の md の表と同じか
2. personas.py が同じ種で同じ人格を作るか、prompts.py の紙が 54 問を順に持つか
3. 作った答え (人工のデータ) で save_answers.py → analyze.py が最後まで動き、仕込んだ形を見つけるか
"""
import json
import os
import re
import sys
import tempfile

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import analyze  # noqa: E402
import personas  # noqa: E402
import prompts  # noqa: E402
import save_answers  # noqa: E402
from items import CONDITIONS, GRAY, HUMAN_PCS, IDS, ITEMS, NORM  # noqa: E402

ROOT = os.path.abspath(os.path.join(HERE, "..", "..", "..", ".."))


def test_items_match_md():
    md = open(os.path.join(ROOT, "docs/research/humanity/thesis2017_questionnaire.md"), encoding="utf-8").read()
    rows = re.findall(r"^\| ([AB]\d\d) \| (.*) \| (.*) \|$", md, re.M)
    assert [tuple(r) for r in rows] == [tuple(i) for i in ITEMS]
    assert len(IDS) == 54 and len(GRAY) == 14


def test_personas_prompts():
    a, b = personas.make(), personas.make()
    assert a == b and len(a) == 100
    ps = json.load(open(os.path.join(HERE, "personas.json"), encoding="utf-8"))["personas"]
    assert ps == json.loads(json.dumps(a, ensure_ascii=False)), "personas.json is stale: run personas.py"
    allp = prompts.all_prompts(a)
    assert len(allp) == sum(c["n"] for c in CONDITIONS.values())
    for rid, (cond, pid, text) in allp.items():
        pos = [text.index(f"\n{i}. ") for i in IDS]
        assert pos == sorted(pos), rid
        assert ("本音" in text) == CONDITIONS[cond]["honne"]
        assert ("この人になりきって" in text) == CONDITIONS[cond]["persona"]
        assert "MBTI" not in text
        on_disk = open(os.path.join(HERE, "prompts", f"{rid}.md"), encoding="utf-8").read()
        assert on_disk == text, f"prompts/{rid}.md is stale: run prompts.py"
    assert allp["C1_007"][1] == allp["C2_007"][1] == "P007"


def synthetic(rng):
    """人工の答え: C1/C2 は人間の 5 つの主成分の上位 5 問に因子を仕込む。C0/C3/C4 は規範のまわりに小さくそろえる。
    C2 はグレーゾーンの問いを 0.6 下げる。"""
    load = np.zeros((54, 5))
    for k, (_, _, _, top) in enumerate(HUMAN_PCS):
        for i, v in top:
            load[IDS.index(i), k] = np.sign(v) * 1.0
    norm = np.array([NORM[i] for i in IDS])
    out = []
    for cond, c in CONDITIONS.items():
        for k in range(c["n"]):
            rid = f"{cond}_{k + 1:03d}"
            if c["persona"]:
                f = np.random.default_rng(1000 + k).standard_normal(5)  # 同じ人格 → 同じ因子
                x = norm + load @ f + 0.5 * rng.standard_normal(54)
                if c["honne"]:
                    x[[IDS.index(g) for g in GRAY]] -= 0.6
            else:
                x = norm + 0.25 * rng.standard_normal(54)
            x = np.clip(np.rint(x), 1, 5).astype(int)
            if c["honne"]:
                ans = {i: {"honne": "そうしたい", "answer": int(v)} for i, v in zip(IDS, x)}
            else:
                ans = {i: int(v) for i, v in zip(IDS, x)}
            out.append({"respondent_id": rid, "answers": ans})
    return out


def test_pipeline():
    rng = np.random.default_rng(0)
    objs = synthetic(rng)
    objs.append({"respondent_id": "C0_001", "answers": {"A01": 9}})  # 形の悪いもの (数えるだけ)
    with tempfile.TemporaryDirectory() as td:
        res = os.path.join(td, "result.json")
        json.dump({"results": [{"id": o["respondent_id"], "result": json.dumps(o, ensure_ascii=False)} for o in objs]},
                  open(res, "w", encoding="utf-8"), ensure_ascii=False)
        old = save_answers.HERE
        save_answers.HERE = td
        try:
            save_answers.main([res])
        finally:
            save_answers.HERE = old
        assert len(os.listdir(os.path.join(td, "answers"))) == 290
        L = analyze.run(os.path.join(td, "answers"), os.path.join(td, "out"), B=50)
        text = "\n".join(L)
        for f in ["summary.md", "items.csv", "eigen.csv", "match.csv", "loadings_C1.csv", "fig_scree.png",
                  "fig_item_means.png", "fig_item_sd.png", "fig_gray_shift.png"]:
            assert os.path.exists(os.path.join(td, "out", f)), f
        assert "**H1a C0:** SD の平均" in text and "支持 (そろいすぎ" in text
        assert "**H3:**" in text and re.search(r"\*\*H3:\*\*.*支持 \(人格", text)
        assert re.search(r"\*\*H4:\*\* 支持", text)
        assert re.search(r"\*\*H5 C1:\*\* 再現 [345]/5", text), text
    print("\n".join(L[-30:]))


if __name__ == "__main__":
    test_items_match_md()
    test_personas_prompts()
    test_pipeline()
    print("ok")
