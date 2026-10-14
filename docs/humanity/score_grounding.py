# 接地度（grounding）を計算して tech_tree.json に書き込む
#
# 接地度 = 高さ（構造） + 手綱（姿勢）
#   高さ：距離 + 身体 + 意味（それぞれ 0〜-1、合計 0〜-3）
#     距離 = -min(段階数,4)/4
#     身体 = -(1-身体比率)
#     意味 = 誰にでも 0 / 身近な人まで -0.5 / 同業者だけ -1
#   手綱：理由を言える かつ 理念から選んでいる とき「握っている」
#     握っている → エージェントの段階を距離から引く（道具が身体の延長になる）
#                  意味を1段よくする（何のために使うかを説明できる）
#     波及 = 周りの接地への影響 -1〜+1（他者を接地させれば＋、意味を奪えば−）
#   身体の軸は手綱で打ち消さない（D07）
import json, pathlib
here = pathlib.Path(__file__).parent
p = here/'tech_tree.json'
d = json.loads(p.read_text(encoding='utf-8'))

LEVELS = ["誰にでも", "身近な人まで", "同業者だけ"]
MSCORE = {"誰にでも": 0.0, "身近な人まで": -0.5, "同業者だけ": -1.0}

def score(steps, chain, ratio, meaning, agent_steps=0, reason=False, principle=False, spread=0.0):
    held = reason and principle
    eff_steps = steps - agent_steps if held else steps
    eff_meaning = LEVELS[max(0, LEVELS.index(meaning)-1)] if held else meaning
    ds = round(-min(eff_steps, 4)/4, 2)
    bs = round(-(1-ratio), 2)
    ms = MSCORE[eff_meaning]
    height = round(ds+bs+ms, 2)
    out = {
      "components": {
        "distance": {"steps": steps, "counted_steps": eff_steps, "chain": chain, "score": ds},
        "body": {"ratio": ratio, "score": bs},
        "meaning": {"level": meaning, "counted_level": eff_meaning, "score": ms},
      },
      "height": height,
      "value": round(height+spread, 2),
    }
    if agent_steps or reason or principle or spread:
        out["reins"] = {"reason": reason, "principle": principle, "held": held,
                        "agent_steps": agent_steps, "spread": spread}
    return out

# 代表者・段階の鎖・身体比率・意味の範囲（いずれも推定）
S = {
 "N01": ("狩猟採集民", score(0, "獲る→食べる", 0.9, "誰にでも")),
 "N02": ("集団で狩る者", score(1, "獲る→分け合う→食べる", 0.9, "誰にでも")),
 "N03": ("農民", score(2, "育てる→蓄える→食べる・納める", 0.9, "誰にでも")),
 "N04": ("職人", score(2, "作る→交換する→食べる", 0.8, "誰にでも")),
 "N05": ("書記", score(3, "記録する→行政→徴税→食べる", 0.3, "身近な人まで")),
 "N06": ("印刷工", score(3, "組む→刷る→流通→読まれる", 0.6, "誰にでも")),
 "N07": ("工場労働者", score(4, "部品→製品→市場→賃金→食べる", 0.8, "身近な人まで")),
 "N08": ("管理職", score(4, "指示→部下の作業→製品・サービス→賃金→食べる", 0.2, "身近な人まで")),
 "N09": ("エージェントと働く知識労働者（無自覚に使う）",
         score(4, "指示→エージェント→成果物→顧客→賃金→食べる", 0.1, "同業者だけ", agent_steps=1)),
}
N09_CHAIN = "指示→エージェント→成果物→顧客→賃金→食べる"
VARIANTS = {
 "N07": [("事務職", score(4, "書類→承認→組織→製品→賃金→食べる", 0.2, "同業者だけ"))],
 "N09": [
   ("理念を持って使う", score(4, N09_CHAIN, 0.1, "同業者だけ", agent_steps=1, reason=True, principle=True)),
   ("理念を持ち、誰でも使える仕組みを作る（使う人の理解を残す）",
    score(4, N09_CHAIN, 0.1, "同業者だけ", agent_steps=1, reason=True, principle=True, spread=1.0)),
   ("仕組みを作るが、中身を隠して使う人の意味を奪う",
    score(4, N09_CHAIN, 0.1, "同業者だけ", agent_steps=1, reason=True, principle=False, spread=-1.0)),
 ],
}
AIR = "指示→エージェント→生命維持系→暮らす"
N10_SCENARIOS = [
 ("再接地：生命維持を自分たちで営む", score(1, "育てる・直す→暮らす", 0.7, "誰にでも")),
 ("再接地し、技能を周りに伝える", score(1, "育てる・直す→暮らす", 0.7, "誰にでも", spread=0.5)),
 ("空中：すべてを無自覚にエージェントに任せる", score(4, AIR, 0.0, "同業者だけ", agent_steps=1)),
 ("空中だが、理念を持ってエージェントに任せる", score(4, AIR, 0.0, "同業者だけ", agent_steps=1, reason=True, principle=True)),
 ("空中だが、理念を持って任せ、他者も接地させる", score(4, AIR, 0.0, "同業者だけ", agent_steps=1, reason=True, principle=True, spread=1.0)),
]

# 身体の比率の裏付け
EVIDENCE = {
 "N01": ("裏付けあり（方向）", ["R19"]), "N02": ("裏付けあり（方向）", ["R19"]), "N03": ("裏付けあり（方向）", ["R19"]),
 "N04": ("推定のみ", []), "N05": ("推定のみ", []), "N06": ("推定のみ", []),
 "N07": ("裏付けあり（方向）", ["R20"]), "N08": ("裏付けあり（方向）", ["R20"]), "N09": ("推定のみ", []),
}

for n in d["nodes"]:
    nid = n["id"]
    if nid in S:
        who, g = S[nid]
        n["grounding"] = {"representative": who, **g, "status": "推定", "refs": ["D03", "D06"]}
        ev, r = EVIDENCE[nid]
        n["grounding"]["components"]["body"].update({"evidence": ev, "refs": r})
        if nid in VARIANTS:
            n["grounding"]["variants"] = [{"representative": w, **v} for w, v in VARIANTS[nid]]
        if nid == "N09":
            n["grounding"]["refs"] = ["D03", "D06", "D07"]
    elif nid == "N10":
        n["grounding"] = {"representative": "宇宙居住者", "value": None, "status": "未決",
                          "scenarios": [{"label": w, **v} for w, v in N10_SCENARIOS],
                          "refs": ["D03", "D06", "D07"]}

d["meta"]["version"] = "0.3.0"
d["meta"]["grounding_formula"] = {
  "target": "そのノードで新しく生まれた仕事の担い手",
  "total": "接地度 = 高さ（距離+身体+意味、0〜-3） + 波及（-1〜+1）。範囲は -4〜+1",
  "distance": "成果までの段階数 n → -min(n,4)/4。手綱を握っていればエージェントの段階を n から引く",
  "body": "身体・物に触れる時間の比率 r → -(1-r)。手綱では打ち消さない",
  "meaning": "仕事を説明できる相手：誰にでも 0 / 身近な人まで -0.5 / 同業者だけ -1。手綱を握っていれば1段よくする",
  "reins": "理由を言える かつ 理念から選んでいる とき握っている。波及は周りの接地への影響",
  "refs": ["D03", "D06", "D07"]
}

# 状況で評価が変わる事象の判定表（行為ではなく判断の質を見る）
d["reins_rubric"] = {
  "criteria": [
    {"id": "reason", "label": "理由を言えるか", "question": "なぜ使うのか、なぜ使わないのかを説明できるか"},
    {"id": "principle", "label": "理念から選んでいるか", "question": "自分の目的から選んでいるか、惰性や恐れからか"},
    {"id": "spread", "label": "周りの接地を増やすか", "question": "その選択で、周りの人の距離・意味はどうなるか"}
  ],
  "cases": [
    {"id": "C1", "event": "AIを使うより自分でやった方が早い",
     "plus": "経験に基づく判断で、手の技能を保っている（理由あり・理念あり）",
     "minus": "試さずに避けている（理由なし・惰性）"},
    {"id": "C2", "event": "AIを学ぶ時間があるなら仕事をする",
     "plus": "手仕事が本分で、AIを入れると距離が増えるだけだと分かっている",
     "minus": "変化への恐れや惰性で学ばない"},
    {"id": "C3", "event": "みんな学ぶ時間がないので、学習コスト0の仕組みを作る",
     "plus": "使う人の理解を残したまま距離を縮める（波及＋）",
     "minus": "中身を完全に隠し、使う人を空中に置く（波及−）"}
  ],
  "refs": ["D07", "R05"]
}

d["reins_rubric"]["version"] = "2026"
d["reins_rubric"]["era_versions"] = {
  "note": "同じ一生を時代ごとの版で採点し直し、版が変わっても評価が変わらない部分を不変項の候補とする",
  "planned": ["2026"],
  "refs": ["D08"]
}

# 判定の仕組み（D08・D09）
d["meta"]["version"] = "0.4.0"
d["judgment_pipeline"] = {
  "tiers": [
    {"tier": 0, "name": "記録", "when": "毎ターン", "uses_llm": False,
     "does": "時代・仕事・成果までの段階数・身体の時間を欄に記録し、高さをスクリプトで計算する"},
    {"tier": 1, "name": "抜き出し", "when": "ライフステージの区切りごと（一生で8回）", "uses_llm": True,
     "model": "小さく安いモデル", "does": "記録から理由・理念・波及の有無を あり／なし／不明 で抜き出す。価値判断はしない",
     "output": {"reason": "あり|なし|不明", "principle": "あり|なし|不明", "spread": "-1〜+1|不明"}},
    {"tier": 2, "name": "陪審団", "when": "下の発動条件のどれかに当てはまる場面だけ", "uses_llm": True,
     "triggers": ["段階1の結果に「不明」がある", "波及が0でない", "新しいノードに切り替わった直後の選択", "品質確認の抜き取り（数%）"],
     "escalation": "まず3人で判定し、全員一致なら終了。割れたら12人に増やす",
     "output": "賛否の分布（＋の人数・−の人数）と一致度",
     "self_check": "同じ事例を言い換えて判定が変わらないか確かめる"}
  ],
  "rescoring": "判定表の版が変わったら、段階2の場面だけ採点し直す",
  "token_estimate_per_life": {"tier1": "約1.6万トークン", "tier2": "約1万〜7万トークン", "status": "概算（未計測）"},
  "refs": ["D09"]
}
d["jury_spec"] = {
  "status": "叩き台",
  "size": {"initial": 3, "max": 12},
  "attributes": [
    {"key": "era", "label": "生きた時代", "source": "テックツリーのノード（N01〜N10）"},
    {"key": "region", "label": "地域・文化圏", "source": "R26（要確認）"},
    {"key": "life_stage", "label": "年齢・ライフステージ", "source": "life_stages（S1〜S8）"},
    {"key": "work", "label": "仕事", "source": "各ノードの仕事層"},
    {"key": "values", "label": "価値観（伝統↔世俗、生存↔自己表現など）", "source": "R26 の分布から抽出（要確認）"}
  ],
  "rules": [
    "属性はClaudeの想像ではなく、調査データの分布から抽出する",
    "陪審員は判定の理由を一文で述べる",
    "陪審員どうしは相談しない（独立に判定する）"
  ],
  "caution": "言語モデルが演じる集団は多様さが平板になりやすい（R22）",
  "refs": ["D08", "R21", "R22", "R26"]
}

p.write_text(json.dumps(d, ensure_ascii=False, indent=2), encoding='utf-8')
for n in d["nodes"]:
    g = n["grounding"]
    print(n["id"], g.get("representative"), g["value"])
    for v in g.get("variants", []) + g.get("scenarios", []):
        print("   ", v.get("representative") or v.get("label"), "高さ", v["height"], "→", v["value"])
