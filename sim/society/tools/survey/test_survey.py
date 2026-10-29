"""論文 2・実験 1 の道具の試し (LLM は使わない)。  python3 test_survey.py

1. items.py の問いと予想が、docs の md の表と同じか
2. personas.py が同じ種で同じ人格を作るか、prompts.py の紙が 54 問を順に持つか
3. 作った答え (人工のデータ) で save_answers.py → analyze.py が最後まで動き、仕込んだ形を見つけるか
4. 実験 2: situations.py・prompts_exp2.py が同じものを作るか (性格・人柄の言葉がないか)、
   人工の答え (はみ出しやすい時 3 つと、学生・苦しい人のダウンロードに効き目を仕込む) で、仕込んだ効き目を見つけ、
   仕込まない 1 つ (簡単にできる) は見つけないか
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
import analyze_exp2  # noqa: E402
import prompts_exp2  # noqa: E402
import save_answers  # noqa: E402
import situations  # noqa: E402
from items import CONDITIONS, CONDITIONS_EXP2, DOWNLOAD, GRAY, HUMAN_PCS, IDS, ITEMS, NORM, REASON_ITEMS, SURROUND  # noqa: E402

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


# 性格 (ビッグファイブ) と人柄のよし悪しの言葉。実験 2 の紙の「あなたについて」「最近のまわりの様子」に出てはいけない
BANNED = ["性格", "外向", "協調", "誠実", "神経", "開放", "まじめ", "真面目", "正直", "良心", "道徳", "倫理", "几帳面", "ルーズ",
          "いい加減", "責任感", "やさしい", "優しい", "思いやり", "規則を守る", "決まりを守る", "MBTI"]


def test_exp2_situations_prompts():
    a, b = situations.make(), situations.make()
    assert a == b and len(a) == 100
    ss = json.load(open(os.path.join(HERE, "situations.json"), encoding="utf-8"))["situations"]
    assert ss == json.loads(json.dumps(a, ensure_ascii=False)), "situations.json is stale: run situations.py"
    F = np.array([[s["surround"][k] for k, _ in SURROUND] for s in a])
    assert list(F.sum(0)) == [50, 50, 50, 50]
    assert np.max(np.abs(np.corrcoef(F.T) - np.eye(4))) < 0.1
    allp = prompts_exp2.all_prompts(a)
    assert len(allp) == sum(c["n"] for c in CONDITIONS_EXP2.values())
    for rid, (cond, sid, text) in allp.items():
        pos = [text.index(f"\n{i}. ") for i in IDS]
        assert pos == sorted(pos), rid
        head = text.split("## お願い")[0]
        for w in BANNED:
            assert w not in head, (rid, w)
        assert ("## 最近のまわりの様子" in text) == CONDITIONS_EXP2[cond]["surround"]
        assert "本音" not in text and "この人になりきって" in text
        assert a[int(rid[3:]) - 1]["text"] in text and sid == f"S{int(rid[3:]):03d}"
        on_disk = open(os.path.join(HERE, "prompts_exp2", f"{rid}.md"), encoding="utf-8").read()
        assert on_disk == text, f"prompts_exp2/{rid}.md is stale: run prompts_exp2.py"
    # 実験 1 と同じ問い・選択肢・お願いの文
    e1 = prompts.build("X", "C1", personas.make()[0])
    assert e1.split("## お願い")[1].split("## 答え方")[0] == allp["D1_001"][2].split("## お願い")[1].split("## 答え方")[0]


PLANT = {"everyone": -0.5, "no_arrest": -0.5, "weak": -0.5, "easy": 0.0}   # 仕込む効き目 (グレーゾーンの問い)


def synthetic_exp2(rng, ss):
    """人工の答え: 人間の 5 つの主成分の形 (上位 5 問に因子) + 暮らしの効き目 (学生か苦しい人はダウンロード 5 問を 0.8 下げる)。
    D2 は同じ人 (同じ因子) に、はみ出しやすい時の効き目 PLANT をグレーゾーンの問いに足す。D3 は小さめのばらつき。"""
    load = np.zeros((54, 5))
    for k, (_, _, _, top) in enumerate(HUMAN_PCS):
        for i, v in top:
            load[IDS.index(i), k] = np.sign(v) * 1.0
    norm = np.array([NORM[i] for i in IDS])
    dl = [IDS.index(i) for i in DOWNLOAD]
    g = [IDS.index(i) for i in GRAY]
    out = []
    for cond, c in CONDITIONS_EXP2.items():
        for k in range(c["n"]):
            s = ss[k]
            f = np.random.default_rng(2000 + k).standard_normal(5)
            x = norm + (0.5 if cond == "D3" else 1.0) * (load @ f) + 0.5 * rng.standard_normal(54)
            if s["student"] or s["money"] == "tight":
                x[dl] -= 0.8
            if c["surround"]:
                x[g] += sum(PLANT[key] * s["surround"][key] for key, _ in SURROUND)
            x = np.clip(np.rint(x), 1, 5).astype(int)
            out.append({"respondent_id": f"{cond}_{k + 1:03d}", "answers": {i: int(v) for i, v in zip(IDS, x)},
                        "reasons": {i: "みんなやっている" for i in REASON_ITEMS}})
    return out


def test_pipeline_exp2():
    rng = np.random.default_rng(1)
    ss = situations.make()
    objs = synthetic_exp2(rng, ss)
    objs.append({"respondent_id": "C1_001", "answers": {i: 3 for i in IDS}})   # 実験 1 の ID は実験 2 にしまわない
    objs.append({"respondent_id": "D9_001", "answers": {i: 3 for i in IDS}})
    with tempfile.TemporaryDirectory() as td:
        res = os.path.join(td, "result.json")
        json.dump({"results": [{"id": o["respondent_id"], "result": json.dumps(o, ensure_ascii=False)} for o in objs]},
                  open(res, "w", encoding="utf-8"), ensure_ascii=False)
        old = save_answers.HERE
        save_answers.HERE = td
        try:
            save_answers.main([res], exp=2)
        finally:
            save_answers.HERE = old
        d = os.path.join(td, "answers_exp2")
        assert len(os.listdir(d)) == 230 and not os.path.exists(os.path.join(d, "C1_001.json"))
        r = json.load(open(os.path.join(d, "D2_005.json"), encoding="utf-8"))
        assert set(r["reasons"]) == set(REASON_ITEMS) and "honne" not in r
        L = analyze_exp2.run(d, os.path.join(td, "out_exp2"), B=200, exp1_answers=os.path.join(HERE, "answers"))
        text = "\n".join(L)
        for f in ["summary.md", "items.csv", "eigen.csv", "match.csv", "h8_coef.csv", "reasons.csv", "loadings_D1.csv",
                  "fig_scree.png", "fig_item_sd.png", "fig_item_means.png", "fig_h8_coef.png", "fig_h9_download.png"]:
            assert os.path.exists(os.path.join(td, "out_exp2", f)), f
        for _, ja in SURROUND:
            row = [x for x in L if x.startswith(f"| {ja} |")][0]
            assert ("| 支持 (CI の上 < 0) |" in row) == (PLANT[[k for k, j in SURROUND if j == ja][0]] < 0), row
        assert "**H8:** 4 つのうち 3 つが支持" in text
        assert "**H9 (D1):** 支持" in text, text
        assert re.search(r"\*\*H7 D1 \(主\):\*\* 再現 [2345]/5", text), text
        assert "**H6 D1 (主):**" in text and re.search(r"\*\*H6 D1 \(主\):\*\*[^\n]*→ 支持", text)
        assert re.search(r"\*\*H10 D1 \(主\):\*\*[^\n]*→ 支持", text)
        assert "**H11:**" in text
    print("\n".join(L[-40:]))


if __name__ == "__main__":
    test_items_match_md()
    test_personas_prompts()
    test_pipeline()
    test_exp2_situations_prompts()
    test_pipeline_exp2()
    print("ok")
