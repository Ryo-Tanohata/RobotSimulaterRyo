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
6. 実験 2c: 出来事 20 個に性格・人柄の言葉・まわりの様子の言葉がないか、54 問の文を写していないか (同じ 8 字以上の続きがない)、
   長さ (25〜60 字)、割り当ての釣り合い (領域 60 人・向き 30 / 30)、F2 ⊃ F1、食い違う組がないか、
   F1・F2 の紙は D1 の紙と ID と「これまでにあったこと」の節だけが違うか、agent への指示が実験 2 と同じか、
   人工の答え (D1 は 1 本の厳しさ、F2 は人間の形 + 領域の効き目) で H16〜H19・効き目の確かめを見つけるか
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
import analyze_exp2c  # noqa: E402
import experiences  # noqa: E402
import prompts_exp2c  # noqa: E402
import save_answers  # noqa: E402
import situations  # noqa: E402
from items import (BORROW, CONDITIONS, CONDITIONS_EXP2, CONDITIONS_EXP2B, CONDITIONS_EXP2C, DOMAIN_ITEMS, DOMAIN_REST, DOWNLOAD,  # noqa: E402
                   GRAY, HUMAN_PCS, IDS, ITEMS, NORM, REASON_ITEMS, SURROUND, TEXT)

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


# 実験 2c の出来事に出てはいけない言葉: まわりの様子 (実験 2・2b で変えたもの) と、答えの物差しの言葉
BANNED_HISTORY = ["みんな", "皆", "ふつう", "誰もが", "だれもが", "まわり", "周り", "問題", "違法", "犯罪"]


def longest_common(a, b):
    best = 0
    for i in range(len(a)):
        for j in range(i + best + 1, len(a) + 1):
            if a[i:j] in b:
                best = j - i
            else:
                break
    return best


def test_exp2c_experiences():
    pool = experiences.pool()
    assert len(pool) == 20 and len({e["id"] for e in pool}) == 20 and len({e["text"] for e in pool}) == 20
    for d, _ in experiences.DOMAINS:
        for r, _ in experiences.DIRECTIONS:
            assert sum(e["domain"] == d and e["direction"] == r for e in pool) == 2
    for e in pool:
        t = e["text"]
        assert 25 <= len(t) <= 60, (e["id"], len(t))
        assert t.endswith("。") and t.count("。") == 1, e["id"]          # 1 文
        assert t.startswith("前に" if e["variant"] == 0 else "以前"), e["id"]   # 言い出しは向きによらない
        for w in BANNED + BANNED_HISTORY:
            assert w not in t, (e["id"], w)
        for i in IDS:   # 54 問の文を写さない
            assert longest_common(t, TEXT[i]) < 8, (e["id"], i)
    a, b = experiences.make(), experiences.make()
    assert a == b and len(a) == 100
    on_disk = json.load(open(os.path.join(HERE, "experiences_exp2c.json"), encoding="utf-8"))
    assert on_disk["assignments"] == json.loads(json.dumps(a, ensure_ascii=False)), "experiences_exp2c.json is stale: run experiences.py"
    assert on_disk["pool"] == json.loads(json.dumps(pool, ensure_ascii=False))
    D = experiences.DKEYS
    dom = lambda x: x.split("_")[0]
    for k, x in enumerate(a):
        assert x["situation_id"] == f"S{k + 1:03d}"
        f1, f2 = x["F1"], x["F2"]
        assert len(f1) == 3 and len({dom(e) for e in f1}) == 3                      # 3 つの違う領域
        assert len(f2) == 6 and len(set(f2)) == 6 and set(f1) <= set(f2)            # F2 ⊃ F1
        assert {dom(e) for e in f2} == set(D)                                        # F2 は 5 つの領域すべて
        for d in D:
            ex = [e for e in f2 if dom(e) == d]
            assert len(ex) <= 2 and len({e.split("_")[1] for e in ex}) == 1, (k, ex)   # 2 つなら同じ向き (食い違わない)
        assert x["code_F1"] == experiences.codes(f1) and x["code_F2"] == experiences.codes(f2)
    C1 = np.array([[x["code_F1"][d] for d in D] for x in a])
    C2 = np.array([[x["code_F2"][d] for d in D] for x in a])
    assert list((C1 != 0).sum(0)) == [60] * 5 and list((C1 == 1).sum(0)) == [30] * 5 and list((C1 == -1).sum(0)) == [30] * 5
    assert list((np.abs(C2) == 2).sum(0)) == [20] * 5 and list((C2 == 2).sum(0)) == [10] * 5 and list((C2 > 0).sum(0)) == [50] * 5
    assert np.max(np.abs(np.corrcoef(C1.T) - np.eye(5))) < 0.15 and np.max(np.abs(np.corrcoef(C2.T) - np.eye(5))) < 0.15
    from collections import Counter
    assert set(Counter(e for x in a for e in x["F1"]).values()) == {15}   # どの出来事も F1 で 15 人
    # 領域の問い: 重ならず、37 + 17 = 54
    allv = sum(DOMAIN_ITEMS.values(), [])
    assert len(allv) == len(set(allv)) == 37 and len(DOMAIN_REST) == 17 and set(allv) | set(DOMAIN_REST) == set(IDS)


def test_exp2c_prompts():
    ss = situations.make()
    asg = experiences.make()
    allp = prompts_exp2c.all_prompts(ss, asg)
    assert len(allp) == sum(c["n"] for c in CONDITIONS_EXP2C.values()) == 200
    idx = json.load(open(os.path.join(HERE, "respondents_exp2c.json"), encoding="utf-8"))
    assert [r["id"] for r in idx] == list(allp) and all(r["experiences"] == allp[r["id"]][2] for r in idx)
    d1 = {rid: v for rid, v in prompts_exp2.all_prompts(ss).items() if v[0] == "D1"}
    for rid, (cond, sid, exps, text) in allp.items():
        k = rid.split("_")[1]
        assert sid == f"S{int(k):03d}"
        on_disk = open(os.path.join(HERE, "prompts_exp2c", f"{rid}.md"), encoding="utf-8").read()
        assert on_disk == text, f"prompts_exp2c/{rid}.md is stale: run prompts_exp2c.py"
        head = text.split("## お願い")[0]
        for w in BANNED:
            assert w not in head, (rid, w)
        assert "## 最近のまわりの様子" not in text and "## これまでにあったこと" in text
        # D1_k との違いは、ID と「これまでにあったこと」の節だけ (D1 の紙は 1 バイトも変わっていない)
        d1text = open(os.path.join(HERE, "prompts_exp2", f"D1_{k}.md"), encoding="utf-8").read()
        assert d1text == d1[f"D1_{k}"][2]
        sec = prompts_exp2c.HISTORY.format(lines="\n".join(f"- {x}" for x in experiences.lines(exps)))
        assert text.count(sec) == 1
        assert text.replace(sec, "").replace(rid, "ID") == d1text.replace(f"D1_{k}", "ID"), rid
        assert len(exps) == CONDITIONS_EXP2C[cond]["history"]
        assert exps == asg[int(k) - 1][cond]
    # agent への指示の文: 実験 2 と同じ (紙のディレクトリだけが違う)。スキーマ・聞き直しの部分は実験 2b と同じ
    js2 = open(os.path.join(HERE, "survey_workflow_exp2.js"), encoding="utf-8").read()
    js2b = open(os.path.join(HERE, "survey_workflow_exp2b.js"), encoding="utf-8").read()
    js2c = open(os.path.join(HERE, "survey_workflow_exp2c.js"), encoding="utf-8").read()
    body = lambda js: js.split("function prompt(")[1].split("\n}\n")[0].split("{", 1)[1]
    assert body(js2c).replace("${DIR}/${dir}/${id}.md", "${DIR}/prompts_exp2/${id}.md") == body(js2)
    assert "F1: { n: 100, model: 'sonnet', file: 'prompts_exp2c', src: 'F1' }" in js2c
    assert "F2: { n: 100, model: 'sonnet', file: 'prompts_exp2c', src: 'F2' }" in js2c
    assert js2b.split("const ITEMS = []")[1].split("\nfunction prompt(")[0].split("\n// ")[0] == \
        js2c.split("const ITEMS = []")[1].split("\nfunction prompt(")[0].split("\n// ")[0]
    assert js2b.split("\nfunction prompt(")[1] == js2c.split("\nfunction prompt(")[1]


def synthetic_exp2c(rng, asg):
    """人工の答え。D1: 54 問がみな同じ重さの 1 本の厳しさ (強く) + 人間の形 (弱く)。
    F1: 厳しさを少し弱め、人間の形を中くらい + 領域の効き目 (出来事 1 つで、その領域の問いを 0.5)。
    F2: 厳しさを弱く、人間の形を強く + 同じ効き目。だから H16〜H19 と効き目の確かめは、みな見つかるはず。"""
    load = np.zeros((54, 5))
    for k, (_, _, _, top) in enumerate(HUMAN_PCS):
        for i, v in top:
            load[IDS.index(i), k] = np.sign(v) * 1.0
    norm = np.array([NORM[i] for i in IDS])
    D = experiences.DKEYS
    dmask = {d: np.array([i in DOMAIN_ITEMS[d] for i in IDS], float) for d in D}
    out = []
    for cond, g_amp, h_amp in (("D1", 0.9, 0.2), ("F1", 0.6, 0.8), ("F2", 0.25, 1.4)):
        for k in range(100):
            f = np.random.default_rng(4000 + k).standard_normal(6)
            x = norm + g_amp * f[0] + h_amp * (load @ f[1:]) + 0.5 * rng.standard_normal(54)
            if cond != "D1":
                x += sum(0.5 * asg[k][f"code_{cond}"][d] * dmask[d] for d in D)
            x = np.clip(np.rint(x), 1, 5).astype(int)
            out.append({"respondent_id": f"{cond}_{k + 1:03d}", "answers": {i: int(v) for i, v in zip(IDS, x)},
                        "reasons": {i: "前に困ったので" for i in REASON_ITEMS}})
    return out


def test_pipeline_exp2c():
    rng = np.random.default_rng(3)
    asg = experiences.make()
    objs = synthetic_exp2c(rng, asg)
    d1 = [o for o in objs if o["respondent_id"].startswith("D1_")]
    rest = [o for o in objs if not o["respondent_id"].startswith("D1_")]
    with tempfile.TemporaryDirectory() as td:
        old = save_answers.HERE
        save_answers.HERE = td
        try:
            p1 = os.path.join(td, "d1.json")
            json.dump({"results": [{"id": o["respondent_id"], "result": json.dumps(o, ensure_ascii=False)} for o in d1]},
                      open(p1, "w", encoding="utf-8"), ensure_ascii=False)
            save_answers.main([p1], exp=2)
            # 実験 2c: 台本が包んだ形 (id = respondent_id) と、はねられた生の答え (ID 違い) が journal にまざる
            p2 = os.path.join(td, "journal.jsonl")
            with open(p2, "w", encoding="utf-8") as f:
                f.write(json.dumps({"agent_result": dict(rest[0], respondent_id="F1_999")}, ensure_ascii=False) + "\n")
                wrapped = [dict(o, id=o["respondent_id"], prompt_id=o["respondent_id"], ok=True, condition=o["respondent_id"].split("_")[0])
                           for o in rest]
                f.write(json.dumps({"return": {"results": wrapped + [{"respondent_id": "D1_001", "answers": {}}]}}, ensure_ascii=False) + "\n")
            save_answers.main([p2], exp="2c")
        finally:
            save_answers.HERE = old
        d = os.path.join(td, "answers_exp2c")
        assert sorted(os.listdir(d)) == sorted(f"{o['respondent_id']}.json" for o in rest), len(os.listdir(d))
        r = json.load(open(os.path.join(d, "F2_005.json"), encoding="utf-8"))
        assert r["condition"] == "F2" and set(r["reasons"]) == set(REASON_ITEMS)
        L = analyze_exp2c.run(d, os.path.join(td, "out"), B=200, exp2_answers=os.path.join(td, "answers_exp2"),
                              exp2b_answers=os.path.join(td, "none"))
        text = "\n".join(L)
        for f in ["summary.md", "items.csv", "eigen.csv", "match.csv", "share_diff.csv", "manip_coef.csv", "reasons.csv",
                  "reasons_coded.csv", "loadings_F1.csv", "loadings_F2.csv", "loadings_D1.csv", "fig_scree.png", "fig_pc1_share.png",
                  "fig_manip_coef.png"]:
            assert os.path.exists(os.path.join(td, "out", f)), f
        assert re.search(r"\*\*H16 \(主\):\*\*[^\n]*→ 支持", text), text
        assert re.search(r"\*\*H17:\*\*[^\n]*→ 支持", text), text
        assert re.search(r"\*\*H18 \(F2\):\*\* 再現 [2345]/5[^\n]*→ 支持", text), text
        assert re.search(r"\*\*H19:\*\*[^\n]*→ 支持", text), text
        assert re.search(r"\*\*効き目の確かめ \(F1 − D1\):\*\*[^\n]*[345]/5[^\n]*→ 効いた", text), text
        assert "- H16 (主。F2 の第 1 主成分の割合が D1 より下がる): 支持" in text
    # 仕込まないとき (F1・F2 も D1 と同じ形・効き目なし) は、H16・H17・効き目の確かめを支持しない
    flat = [dict(o) for o in d1] + [dict(o, respondent_id=c + o["respondent_id"][2:]) for o in synthetic_exp2c(np.random.default_rng(4), asg)
                                    if o["respondent_id"].startswith("D1_") for c in ("F1", "F2")]
    with tempfile.TemporaryDirectory() as td:
        old = save_answers.HERE
        save_answers.HERE = td
        try:
            p = os.path.join(td, "all.json")
            json.dump(flat, open(p, "w", encoding="utf-8"), ensure_ascii=False)
            save_answers.main([p], exp=2)
            save_answers.main([p], exp="2c")
        finally:
            save_answers.HERE = old
        L2 = analyze_exp2c.run(os.path.join(td, "answers_exp2c"), os.path.join(td, "out"), B=200,
                               exp2_answers=os.path.join(td, "answers_exp2"), figures=False)
        t2 = "\n".join(L2)
        assert re.search(r"\*\*H16 \(主\):\*\*[^\n]*→ 支持しない", t2), t2
        assert re.search(r"\*\*H17:\*\*[^\n]*→ 支持しない", t2), t2
        assert re.search(r"\*\*効き目の確かめ \(F1 − D1\):\*\*[^\n]*→ 効いたとは言えない", t2), t2
    print("\n".join(L[:14]))


if __name__ == "__main__":
    test_items_match_md()
    test_personas_prompts()
    test_pipeline()
    test_exp2_situations_prompts()
    test_pipeline_exp2()
    test_exp2b_prompts()
    test_pipeline_exp2b()
    test_exp2c_experiences()
    test_exp2c_prompts()
    test_pipeline_exp2c()
    print("ok")
