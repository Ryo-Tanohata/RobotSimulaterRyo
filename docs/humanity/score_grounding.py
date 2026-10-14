# 接地度（grounding）を計算して tech_tree.json と design_note.md の表に書き込む（v0.7、D10）
#
# 接地度は「身体や現場にどれだけ根ざして働いているか」の記述（0〜1、大きいほど深い）。良い・悪いの判定はしない（判定は陪審団、D08）。
#   意味 M = (技能多様性・タスク完結性・タスク重要性 の平均 − 1) / 6      … 職務特性モデルの「意味を感じる」（R28）
#   結果 F = (仕事からのフィードバック − 1) / 6                          … 同「結果が分かる」（R28）
#   身体 B = O*NET の「一般的な身体活動」の重要度 / 100                  … 職業の実データ（R27）。近い職業がないときは推定
#   接地度 G = (M + F + B) / 3
# 手綱の余地（自律性）と波及は、接地度に足さずに別に出す。
#   自律性 A = (自律性 − 1) / 6                                          … 同「責任を感じる」。O*NET の「決める自由」を参考に並べる
#   波及 = 周りの接地への影響（−1〜+1）。符号は陪審団が決める（D07・D08）
# JDS の 1〜7 の評定は、陪審団 12 人の平均（jury/results.json の jury_ratings。D08・D10）。
# 下の S・VARIANTS・N10_SCENARIOS の数は作り手（Claude）が先に付けた評定で、陪審団の評定がない仕事にだけ使う。理由（作り手が書いたもの）を "why" に書く。
import json, pathlib, re
here = pathlib.Path(__file__).parent
p = here/'tech_tree.json'
d = json.loads(p.read_text(encoding='utf-8'))

# O*NET の「一般的な身体活動」の重要度と「決める自由」の分布（2026-10-14 に O*NET OnLine で確かめた）
ONET = {
  "45-2092.00": ("農作業員（作物）", 76, {"かなり": 24, "いくらか": 17, "限られる": 18, "ほとんどない": 21, "ない": 20}),
  "45-2093.00": ("農作業員（家畜）", 75, {"かなり": 54, "いくらか": 17, "限られる": 14, "ない": 14}),
  "47-2061.00": ("建設作業員", 68, {"いくらか": 50, "限られる": 34, "ほとんどない": 16}),
  "51-8091.00": ("化学プラントの運転員", 68, {"かなり": 26, "いくらか": 39, "限られる": 12, "ない": 24}),
  "51-7011.00": ("家具職人", 64, None),
  "51-5112.00": ("印刷機の運転員", 63, {"かなり": 52, "いくらか": 26, "ほとんどない": 16}),
  "51-2092.00": ("組立工", 62, {"かなり": 27, "いくらか": 50, "限られる": 23}),
  "51-6064.00": ("繊維機械の運転員", 51, {"いくらか": 32, "限られる": 26, "ほとんどない": 37}),
  "43-9061.00": ("一般事務員", 29, {"かなり": 14, "いくらか": 34, "限られる": 24, "ほとんどない": 25}),
  "11-1021.00": ("経営・管理職", 28, {"かなり": 86, "いくらか": 11}),
  "15-1252.00": ("ソフトウェア開発者", 17, {"かなり": 41, "いくらか": 46, "限られる": 13}),
  "43-3031.00": ("簿記・会計の事務員", 16, {"かなり": 27, "いくらか": 33, "限られる": 34}),
}
FREEDOM_W = {"かなり": 1.0, "いくらか": 0.75, "限られる": 0.5, "ほとんどない": 0.25, "ない": 0.0}

def onet_freedom(code):
    dist = ONET[code][2]
    if not dist:
        return None
    tot = sum(dist.values())
    return round(sum(FREEDOM_W[k]*v for k, v in dist.items())/tot, 2)

def body(code=None, est=None, note=None):
    if code:
        name, gpa, _ = ONET[code]
        return {"value": round(gpa/100, 2), "source": f"O*NET {code} {name}（一般的な身体活動 {gpa}）", "status": "実データ", "refs": ["R27"]}
    return {"value": est, "source": note, "status": "推定", "refs": ["R19"] if "狩猟" in (note or "") else []}

def score(sv, ti, ts, fb, au, b, why, spread=0.0, onet=None):
    m = round(((sv+ti+ts)/3 - 1)/6, 3)
    f = round((fb-1)/6, 3)
    g = round((m + f + b["value"])/3, 3)
    out = {
      "components": {
        "meaning": {"skill_variety": sv, "task_identity": ti, "task_significance": ts, "score": m},
        "feedback": {"feedback": fb, "score": f},
        "body": {**b, "score": b["value"]},
      },
      "value": g,
      "autonomy": {"rating": au, "score": round((au-1)/6, 3), "onet_freedom": onet_freedom(onet) if onet else None},
      "spread": spread,
      "why": why,
    }
    return out

# 代表者（JDS の評定: 技能多様性・完結性・重要性・フィードバック・自律性）
S = {
 "N01": ("狩猟採集民", score(6, 7, 6, 7, 6, body(est=0.80, note="狩猟採集。近い職業がないので推定（農作業員 0.76 より歩く・運ぶが多い）"),
         "獲物を探して獲り、分けて食べるまで全部に関わり、うまくいったかがすぐ分かる")),
 "N02": ("集団で狩る者", score(6, 6, 6, 6, 5, body(est=0.80, note="集団の狩猟。推定（N01 と同じ）"),
         "分担はあるが分配まで見える。合図や段取りで技能が増える")),
 "N03": ("農民", score(5, 6, 5, 5, 5, body("45-2092.00"),
         "種まきから刈り入れまで関わるが、結果は季節の終わりまで分からない", onet="45-2092.00")),
 "N04": ("職人", score(6, 7, 5, 6, 6, body("51-7011.00"),
         "材料から完成品まで一人で作り、出来ばえが手で分かる")),
 "N05": ("書記", score(3, 3, 5, 3, 3, body("43-3031.00"),
         "決まった形式で記録する。記録が何に使われたかは見えにくいが、行政への影響は大きい", onet="43-3031.00")),
 "N06": ("印刷工", score(5, 5, 5, 6, 4, body("51-5112.00"),
         "組版から刷り上がりまで関わり、刷り上がりで出来が分かる（ブラウナーの職人型）", onet="51-5112.00")),
 "N07": ("工場労働者（組立ライン）", score(1, 1, 3, 3, 1, body("51-2092.00"),
         "流れ作業の一工程だけ。ペースは機械が決め、製品の全体は見えない（ブラウナーの組立ライン）", onet="51-2092.00")),
 "N08": ("管理職", score(6, 4, 6, 3, 6, body("11-1021.00"),
         "仕事は多様で影響も大きいが、成果は部下を通してしか見えない", onet="11-1021.00")),
 "N09": ("エージェントと働く知識労働者（無自覚に使う）", score(3, 2, 3, 2, 4, body("15-1252.00"),
         "出力をそのまま流すだけで、何がなぜできたかが分からない", onet="15-1252.00")),
}
VARIANTS = {
 "N07": [
   ("事務職", score(3, 2, 3, 2, 2, body("43-9061.00"), "書類の一部を処理し、その先は見えない", onet="43-9061.00")),
   ("繊維機械の運転員（ブラウナーの機械番）", score(2, 2, 3, 4, 2, body("51-6064.00"),
     "多くの機械を見回るだけ。不具合はすぐ分かるが、作業は単調", onet="51-6064.00")),
 ],
 "N08": [
   ("化学プラントの運転員（ブラウナーの自動化）", score(4, 5, 5, 5, 4, body("51-8091.00"),
     "工程の全体を見張り、計器で結果が分かる。責任の範囲が広い", onet="51-8091.00")),
 ],
 "N09": [
   ("理念を持って使う", score(6, 6, 5, 5, 6, body("15-1252.00"),
     "目的を自分で決め、エージェントを手の延長として使う。全体を組み立て、結果を確かめる", onet="15-1252.00")),
   ("理念を持ち、誰でも使える仕組みを作る（理解を残す）", score(6, 6, 7, 5, 6, body("15-1252.00"),
     "上に加え、多くの人の暮らしに届く", spread=1.0, onet="15-1252.00")),
   ("仕組みを作るが、中身を隠して使う人の意味を奪う", score(5, 5, 5, 4, 6, body("15-1252.00"),
     "作る人の仕事は豊かだが、使う人を空中に置く", spread=-1.0, onet="15-1252.00")),
 ],
}
N10_SCENARIOS = [
 ("再接地：生命維持を自分たちで営む", score(6, 6, 6, 6, 6, body(est=0.60, note="閉鎖生態系の世話・修理。推定（建設・農作業より少し低い）"),
   "育てる・直すを自分たちで行い、結果が暮らしにすぐ表れる")),
 ("再接地し、技能を周りに伝える", score(6, 6, 7, 6, 6, body(est=0.60, note="同上"), "上に加え、周りの人も接地させる", spread=0.5)),
 ("空中：すべてを無自覚にエージェントに任せる", score(2, 1, 2, 1, 2, body(est=0.05, note="体を使う仕事がほぼない。推定"),
   "何も作らず、何が起きているかも分からない")),
 ("空中だが、理念を持ってエージェントに任せる", score(5, 5, 5, 4, 6, body(est=0.05, note="同上"),
   "体は使わないが、目的を決めて全体を組み立てる")),
 ("空中だが、理念を持って任せ、他者も接地させる", score(5, 5, 7, 4, 6, body(est=0.05, note="同上"),
   "上に加え、周りの人の暮らしを支える", spread=1.0)),
]

# 陪審団の平均を正式な評定として使う（D10。作り手の評定は jury/creator_ratings.json に残す）
JURY = {}
jr = here/'jury'/'results.json'
if jr.exists():
    JURY = {k: v["jury_ratings"] for k, v in json.loads(jr.read_text(encoding='utf-8'))["per_job"].items()}

def use_jury(jid, e):
    r = JURY.get(jid)
    if not r:
        e["rating_source"] = "作り手（Claude）の評定"
        return e
    b = e["components"]["body"]
    new = score(r["sv"], r["ti"], r["ts"], r["fb"], r["au"], {k: v for k, v in b.items() if k != "score"}, e["why"], spread=e.get("spread", 0.0))
    new["autonomy"]["onet_freedom"] = e["autonomy"]["onet_freedom"]
    new["rating_source"] = "陪審団 12 人の平均"
    return new

for nid in list(S):
    S[nid] = (S[nid][0], use_jury(nid, S[nid][1]))
for nid in VARIANTS:
    VARIANTS[nid] = [(w, use_jury(nid + "abc"[k], v)) for k, (w, v) in enumerate(VARIANTS[nid])]
N10_SCENARIOS = [(w, use_jury("N10" + "abcde"[k], v)) for k, (w, v) in enumerate(N10_SCENARIOS)]

for n in d["nodes"]:
    nid = n["id"]
    if nid in S:
        who, g = S[nid]
        n["grounding"] = {"representative": who, **g, "status": "陪審団の評定＋実データ", "refs": ["D03", "D06", "D10"]}
        if nid in VARIANTS:
            n["grounding"]["variants"] = [{"representative": w, **v} for w, v in VARIANTS[nid]]
        if nid == "N09":
            n["grounding"]["refs"] = ["D03", "D06", "D07", "D10"]
    elif nid == "N10":
        n["grounding"] = {"representative": "宇宙居住者", "value": None, "status": "未決",
                          "scenarios": [{"label": w, **v} for w, v in N10_SCENARIOS],
                          "refs": ["D03", "D06", "D07", "D10"]}

d["meta"]["version"] = "0.7.0"
d["meta"]["design_note"] = "テックツリー設計ノート（参照ID R00〜R31 と D01〜D10 はノートの「参考文献」「設計判断」に対応）"
d["meta"]["grounding_formula"] = {
  "target": "そのノードで新しく生まれた仕事の担い手",
  "direction": "0〜1。大きいほど身体や現場に根ざしている。記述であって、良い・悪いではない",
  "meaning": "職務特性モデルの技能多様性・タスク完結性・タスク重要性（1〜7。陪審団 12 人の平均）の平均 → (x−1)/6",
  "feedback": "職務特性モデルの仕事からのフィードバック（1〜7） → (x−1)/6",
  "body": "O*NET の一般的な身体活動の重要度 / 100（近い職業がないときは推定）",
  "total": "接地度 = (意味 + 結果 + 身体) / 3",
  "separate": "自律性（手綱の余地）と波及は接地度に足さず、別に出す",
  "refs": ["D06", "D10", "R27", "R28", "R29", "R31"]
}
d["reins_rubric"]["refs"] = ["D07", "D10", "R05", "R28"]

p.write_text(json.dumps(d, ensure_ascii=False, indent=2), encoding='utf-8')

# ---- ノートの表を書き換える（印のあいだだけ） ----
def row(nid, who, g):
    c = g["components"]
    m = c["meaning"]
    sp = g.get("spread") or 0
    return (f"| {nid} | {who} | {m['skill_variety']:.1f}・{m['task_identity']:.1f}・{m['task_significance']:.1f} | {c['meaning']['score']:.2f} | "
            f"{c['feedback']['feedback']:.1f} | {c['feedback']['score']:.2f} | {c['body']['score']:.2f}（{c['body']['status']}） | **{g['value']:.2f}** | "
            f"{g['autonomy']['rating']:.1f} | {'' if not sp else ('+' if sp > 0 else '−') + str(abs(sp))} |")

lines = ["| ID | 代表者 | 多様性・完結性・重要性 | 意味 | フィードバック | 結果 | 身体 | 接地度 | 自律性 | 波及 |",
         "|---|---|---|---|---|---|---|---|---|---|"]
for n in d["nodes"]:
    g = n["grounding"]
    if "components" in g:
        lines.append(row(n["id"], g["representative"], g))
    for v in g.get("variants", []):
        lines.append(row(n["id"], "（別例）" + v["representative"], v))
    for s in g.get("scenarios", []):
        lines.append(row(n["id"], s["label"], s))
table = "\n".join(lines)
notep = here/'design_note.md'
note = notep.read_text(encoding='utf-8')
note = re.sub(r"(<!-- grounding-table:start -->\n)(?:.*?\n)?(<!-- grounding-table:end -->)", lambda mm: mm.group(1)+table+"\n"+mm.group(2), note, flags=re.S)
notep.write_text(note, encoding='utf-8')

for n in d["nodes"]:
    g = n["grounding"]
    print(n["id"], g.get("representative"), g["value"])
    for v in g.get("variants", []) + g.get("scenarios", []):
        print("   ", v.get("representative") or v.get("label"), v["value"], "波及", v["spread"])
