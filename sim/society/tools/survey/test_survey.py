"""論文 2・実験 1 の道具の試し (LLM は使わない)。  python3 test_survey.py

1. items.py の問いと予想が、docs の md の表と同じか
2. personas.py が同じ種で同じ人格を作るか、prompts.py の紙が 54 問を順に持つか
3. 作った答え (人工のデータ) で save_answers.py → analyze.py が最後まで動き、仕込んだ形を見つけるか
4. 実験 2: situations.py・prompts_exp2.py が同じものを作るか (性格・人柄の言葉がないか)、
   人工の答え (はみ出しやすい時 3 つと、学生・苦しい人のダウンロードに効き目を仕込む) で、仕込んだ効き目を見つけ、
   仕込まない 1 つ (簡単にできる) は見つけないか
5. 実験 2b: E1 の様子の行に性格・人柄の言葉とネット・ダウンロードの言葉がないか、E1 の 0/1 の組が D2 と同じか、
   E1 の紙は D2 の紙と様子の 3 行 (と ID) だけが違うか、D2r の紙・agent への指示が D2 と 1 バイトも同じか、
   人工の答え (E1 に所有意識の形と借りた物の効き目、D2r に権利意識の形を仕込む) で H12〜H15 を見つけるか
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
import analyze_exp2b  # noqa: E402
import prompts_exp2b  # noqa: E402
import save_answers  # noqa: E402
import situations  # noqa: E402
from items import BORROW, CONDITIONS, CONDITIONS_EXP2, CONDITIONS_EXP2B, DOWNLOAD, GRAY, HUMAN_PCS, IDS, ITEMS, NORM, REASON_ITEMS, SURROUND  # noqa: E402

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


# 実験 2b の E1 の様子に出てはいけない言葉 (ダウンロード・コピー・ネットの場面。D2 との違いを「中身」だけにするため)
BANNED_ONLINE = ["ダウンロード", "コピー", "ネット", "オンライン", "スマホ", "パソコン", "動画", "音楽", "配信", "保存", "写し",
                 "写真", "載せ", "アップ", "SNS", "無料", "ただで", "ボタン", "データ", "サイト", "著作"]


def test_exp2b_prompts():
    ss = situations.make()
    lines = situations.OWN_SURROUND_LINES
    assert [k for k in lines] == [k for k, _ in SURROUND]
    assert lines["weak"] == situations.SURROUND_LINES["weak"]   # 弱い立場は D2 と同じ文 (くらべの土台)
    for k, pair in lines.items():
        assert len(pair) == 2 and pair[0] != pair[1]
        for t in pair:
            for w in BANNED:
                assert w not in t, (k, w)
            if k != "weak":
                for w in BANNED_ONLINE:
                    assert w not in t, (k, w)
                # 長さは D2 の文とおよそ同じ (半分〜1.5 倍)
                d2 = situations.SURROUND_LINES[k][pair.index(t)]
                assert 0.5 * len(d2) <= len(t) <= 1.5 * len(d2), (k, len(t), len(d2))
    allp = prompts_exp2b.all_prompts(ss)
    assert len(allp) == sum(c["n"] for c in CONDITIONS_EXP2B.values()) == 200
    idx = json.load(open(os.path.join(HERE, "respondents_exp2b.json"), encoding="utf-8"))
    assert [r["id"] for r in idx] == list(allp)
    d2 = {rid: v for rid, v in prompts_exp2.all_prompts(ss).items() if v[0] == "D2"}
    for rid, (cond, sid, pid, text) in allp.items():
        k = rid.split("_")[1]
        assert sid == f"S{int(k):03d}"
        pos = [text.index(f"\n{i}. ") for i in IDS]
        assert pos == sorted(pos), rid
        head = text.split("## お願い")[0]
        for w in BANNED:
            assert w not in head, (rid, w)
        d2text = open(os.path.join(HERE, "prompts_exp2", f"D2_{k}.md"), encoding="utf-8").read()
        assert d2text == d2[f"D2_{k}"][2]
        if cond == "D2r":
            # D2r: 紙は D2 の紙そのもの (ファイルも中身も)。新しい紙は作らない
            assert pid == f"D2_{k}" and text == d2text
            assert not os.path.exists(os.path.join(HERE, "prompts_exp2b", f"{rid}.md"))
        else:
            on_disk = open(os.path.join(HERE, "prompts_exp2b", f"{rid}.md"), encoding="utf-8").read()
            assert on_disk == text, f"prompts_exp2b/{rid}.md is stale: run prompts_exp2b.py"
            # E1_k と D2_k の違いは、ID と、様子の行のうち weak 以外の 3 行だけ。0/1 は D2_k と同じ
            a, b = text.replace(rid, "ID").splitlines(), d2text.replace(f"D2_{k}", "ID").splitlines()
            assert len(a) == len(b)
            diff = [(x, y) for x, y in zip(a, b) if x != y]
            assert len(diff) == 3, (rid, diff)
            flags = ss[int(k) - 1]["surround"]
            want_e1 = [f"- {x}" for x in situations.surround_lines(flags, lines)]
            want_d2 = [f"- {x}" for x in situations.surround_lines(flags)]
            assert all(x in want_e1 and y in want_d2 for x, y in diff)
            for key, _ in SURROUND:
                assert lines[key][0 if flags[key] else 1] in text
    # agent への指示の文: 実験 2b の台本の prompt() は、D2r では実験 2 と 1 字も同じになる
    js2 = open(os.path.join(HERE, "survey_workflow_exp2.js"), encoding="utf-8").read()
    js2b = open(os.path.join(HERE, "survey_workflow_exp2b.js"), encoding="utf-8").read()
    body = lambda js: js.split("function prompt(")[1].split("\n}\n")[0].split("{", 1)[1]
    assert body(js2b).replace("${DIR}/${dir}/${id}.md", "${DIR}/prompts_exp2/${id}.md") == body(js2)
    assert "D2r: { n: 100, model: 'sonnet', file: 'prompts_exp2', src: 'D2' }" in js2b
    assert "E1: { n: 100, model: 'sonnet', file: 'prompts_exp2b', src: 'E1' }" in js2b
    # survey_workflow_exp2b.js の他の部分 (スキーマ・聞き直し) は実験 2 と同じ
    assert js2.split("const ITEMS = []")[1].split("function prompt(")[0] == js2b.split("const ITEMS = []")[1].split("// 実験 2 の prompt() と同じ文")[0]


def synthetic_exp2b(rng, ss):
    """人工の答え。D1 (実験 2 の形): 人間の 5 つの主成分の形を弱く。E1: 同じ人に、所有意識 (pc2) の形を強く + 借りた物の 5 問に
    みんながやっている・捕まった人を聞かない で −0.6。D2r: 権利意識 (pc1) の形を強く。"""
    load = np.zeros((54, 5))
    for k, (_, _, _, top) in enumerate(HUMAN_PCS):
        for i, v in top:
            load[IDS.index(i), k] = np.sign(v) * 1.0
    norm = np.array([NORM[i] for i in IDS])
    bi = [IDS.index(i) for i in BORROW]
    out = []
    for cond, amp in (("D1", None), ("E1", 1), ("D2r", 0)):
        for k in range(100):
            s = ss[k]
            f = np.random.default_rng(3000 + k).standard_normal(5)
            sc = np.full(5, 0.4)
            if amp is not None:
                sc[amp] = 1.6
            x = norm + load @ (sc * f) + 0.5 * rng.standard_normal(54)
            if cond == "E1":
                x[bi] -= 0.6 * (s["surround"]["everyone"] + s["surround"]["no_arrest"])
            x = np.clip(np.rint(x), 1, 5).astype(int)
            rid = f"{cond}_{k + 1:03d}"
            out.append({"respondent_id": rid, "answers": {i: int(v) for i, v in zip(IDS, x)},
                        "reasons": {i: "みんな返さないので" for i in REASON_ITEMS}})
    return out


def test_pipeline_exp2b():
    rng = np.random.default_rng(2)
    ss = situations.make()
    objs = synthetic_exp2b(rng, ss)
    d1 = [o for o in objs if o["respondent_id"].startswith("D1_")]
    rest = [o for o in objs if not o["respondent_id"].startswith("D1_")]
    with tempfile.TemporaryDirectory() as td:
        old = save_answers.HERE
        save_answers.HERE = td
        try:
            # D1 (くらべの相手) は実験 2 としてしまう
            p1 = os.path.join(td, "d1.json")
            json.dump({"results": [{"id": o["respondent_id"], "result": json.dumps(o, ensure_ascii=False)} for o in d1]},
                      open(p1, "w", encoding="utf-8"), ensure_ascii=False)
            save_answers.main([p1], exp=2)
            # 実験 2b: E1 は生の答え、D2r は台本が包んだ形 (id = respondent_id = D2r_k、prompt_id = D2_k) と生の形 (D2_k) が journal にまざる
            p2 = os.path.join(td, "journal.jsonl")
            with open(p2, "w", encoding="utf-8") as f:
                for o in rest:
                    rid = o["respondent_id"]
                    if rid.startswith("D2r_"):
                        raw = dict(o, respondent_id="D2_" + rid.split("_")[1])
                        f.write(json.dumps({"agent_result": raw}, ensure_ascii=False) + "\n")
                wrapped = [dict(o, id=o["respondent_id"], ok=True, condition=o["respondent_id"].split("_")[0]) for o in rest]
                f.write(json.dumps({"return": {"results": wrapped}}, ensure_ascii=False) + "\n")
            save_answers.main([p2], exp="2b")
            # 包んだ答えがないとき: D2_k の生の答えを D2r_k として読む
            p3 = os.path.join(td, "raw.json")
            json.dump([dict(o, respondent_id="D2_" + o["respondent_id"].split("_")[1]) for o in rest if o["respondent_id"].startswith("D2r_")][:3],
                      open(p3, "w", encoding="utf-8"), ensure_ascii=False)
            save_answers.main([p3], exp="2b", sub="answers_exp2b_raw")
        finally:
            save_answers.HERE = old
        d = os.path.join(td, "answers_exp2b")
        assert len(os.listdir(d)) == 200, len(os.listdir(d))
        assert sorted(os.listdir(os.path.join(td, "answers_exp2b_raw"))) == ["D2r_001.json", "D2r_002.json", "D2r_003.json"]
        r = json.load(open(os.path.join(d, "D2r_005.json"), encoding="utf-8"))
        assert r["condition"] == "D2r" and set(r["reasons"]) == set(REASON_ITEMS)
        L = analyze_exp2b.run(d, os.path.join(td, "out"), B=200, exp2_answers=os.path.join(td, "answers_exp2"))
        text = "\n".join(L)
        for f in ["summary.md", "items.csv", "eigen.csv", "match.csv", "match_k2.csv", "h14_coef.csv", "reasons.csv",
                  "reasons_coded.csv", "loadings_E1.csv", "loadings_D2r.csv", "fig_scree.png", "fig_item_means.png", "fig_h14_coef.png"]:
            assert os.path.exists(os.path.join(td, "out", f)), f
        assert re.search(r"\*\*H12 \(E1\):\*\*[^\n]*→ 支持", text), text
        assert re.search(r"\*\*H13 \(E1\):\*\*[^\n]*→ 支持", text), text
        assert "**H14 みんながやっている:** 支持" in text and "**H14 その行為で捕まった人を聞いたことがない:** 支持" in text, text
        assert re.search(r"\*\*H15 \(D2r\):\*\*[^\n]*→ 支持", text), text
        row = [x for x in L if x.startswith("| 自分が弱い立場にいる |")][0]
        assert "(探索。判定しない)" in row
    print("\n".join(L[:12]))


if __name__ == "__main__":
    test_items_match_md()
    test_personas_prompts()
    test_pipeline()
    test_exp2_situations_prompts()
    test_pipeline_exp2()
    test_exp2b_prompts()
    test_pipeline_exp2b()
    print("ok")
