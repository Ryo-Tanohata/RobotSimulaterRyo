#!/usr/bin/env python3
"""ダッシュボード「村の跡と記録」の小さな JSON を作る (読むだけ。標準ライブラリだけ)。

設計: docs/dashboard_design.md (4. 作り方)。
入力: <data>/state.json と <data>/records/ (どちらも読むだけ)。
出力: 村が残すもの (掘ってわかる跡・G6 からは村の記録) だけを、季節の行にした JSON。
      名前・人と家の番号・本当の人数・気持ち・正確な年齢や日は入れない (年の名の中の名前だけは出す)。

使い方:
  py -3 -X utf8 sim/society/tools/build_dashboard.py [--data DIR] [--out JSON] [--embed HTML] [--allow-data] [--check]

  --data   state.json と records/ のあるフォルダ (はじめは sim/society/data)
  --out    JSON を書く場所 (はじめは sim/society/app/dashboard_data.json)。sim/society/data/ の下は --allow-data がないと断る
  --embed  html の <!--DASH-DATA--> と <!--/DASH-DATA--> のあいだだけを書きかえる (改行の形はそのまま)
  --check  書かずに作りなおして、--out (と --embed) の中身と 1 バイトでもちがえば知らせる (0 でない終わり方)

同じ入力なら同じ出力 (キーを並べる・時刻を入れない)。
"""
import argparse
import bisect
import collections
import json
import math
import os
import re
import sys
import time

HERE = os.path.dirname(os.path.abspath(__file__))
SOC = os.path.dirname(HERE)
DEFAULT_DATA = os.path.join(SOC, "data")
DEFAULT_OUT = os.path.join(SOC, "app", "dashboard_data.json")
PROTECTED = os.path.join(SOC, "data")

SEAS = "夏秋冬春"
YEAR, SEASON = 120, 30
CELL_M = 25  # 1 マス = 25 m
F_LAST = 489  # F 層の最後の日 (G1 に進んだ日)
AGE = [("乳飲み子", 0, 2), ("子", 3, 11), ("手伝える子", 12, 14), ("大人", 15, 54), ("年寄り", 55, 999)]
AGE_ORDER = [a[0] for a in AGE]
DIRS = ["北", "北東", "東", "南東", "南", "南西", "西", "北西"]
PLANT_W = {"木の実": 1.0, "草の種": 0.5, "芋": 0.05}  # 焼けて残りやすさ【仮定】
MEAT = ("肉", "ルクの肉", "魚", "ピク", "ピクの肉", "干し肉", "ヤギ")
CERT = ("高い", "中くらい", "低い")

LAYER_REAL = {
    "F": ("ナトゥーフ期", "約1.5万〜1.17万年前"),
    "G1": ("PPNA (先土器新石器 A)", "前9700〜8800年ごろ"),
    "G2": ("PPNB (先土器新石器 B)", "前8800〜6900年ごろ"),
    "G3": ("土器新石器のはじめ", "前7000年ごろ〜"),
    "G4": ("土器新石器〜ハラフ期", "前6500〜5300年ごろ"),
    "G5": ("ウバイド期", "北で前5300〜4300年ごろ"),
    "G6": ("テル・ブラク LC2 → ウルク期", "前4200〜3800年ごろ → 原楔形文字 前3350〜3200年"),
}
LAYER_IDS = ["F", "G1", "G2", "G3", "G4", "G5", "G6"]

# 跡を残した技と、本物 (西アジア) でいちばん古い例 (動かない表。docs/dashboard_design.md 2.5・K22・6.4)
# 年代と場所は docs/research/archaeological_evidence.md と app/tech_tree_demo.html (どちらも出典つき) にそろえた
TECH = [
    {"id": "grain", "trace": "焼けた草の種の粒 (野生の形)", "tech": "野生の草の種を食べる", "real": "約2.3万年前",
     "real_place": "オハロー II (焼けた野生の麦)", "also": "育てはじめは約1.16万〜1.07万年前【議論あり】。畑はこの村の跡では見えない",
     "years": 23000, "badge": "【仮定】", "cert": "低い"},
    {"id": "dwell", "trace": "柱の穴の輪", "tech": "村の住まい (柱を立てた小屋)", "real": "約1.43万年前",
     "real_place": "アイン・マラハ (ナトゥーフ期の村。丸い半地下の家)",
     "also": "村でないキャンプの枝の小屋 (床の跡) は、オハロー II 約2.3万年前", "years": 14300, "badge": None, "cert": "高い"},
    {"id": "goat", "trace": "ヤギの糞とひづめの跡", "tech": "ヤギを村に置く", "real": "約1.04万年前から",
     "real_place": "アシュクル・ホユク (おしっこの塩の層。ヒツジとヤギ。人と動物の分は分けられない)",
     "also": "ガンジ・ダレ 約1万年前 (れんがのひづめの跡・飼った群れの骨)", "years": 10450, "badge": None, "cert": "中くらい"},
    {"id": "hearth", "trace": "炉 (灰・炭・焼けた石)", "tech": "火", "real": "約79万年前",
     "real_place": "ゲシャー・ベノット・ヤアコブ (焼けた石器と種のまとまり。石で組んだ炉ではない)",
     "also": "いつも火を使った跡は、ケセム洞窟 42万〜20万年前", "years": 790000, "badge": None, "cert": "高い"},
    {"id": "blade", "trace": "つやの出た石の刃", "tech": "鎌 (草を刈る)", "real": "約2.3万年前",
     "real_place": "オハロー II", "also": None, "years": 23000, "badge": None, "cert": "中くらい"},
    {"id": "sherd", "trace": "土器のかけら", "tech": "土器", "real": "前7000〜6600年ごろ",
     "real_place": "上メソポタミアの最初の土器 (サビ・アビヤド 前7000〜6800年ごろ・テル・セケル・アル・アヘイマル 前6900〜6600年ごろ)",
     "also": "東アジアはもっと早い: 中国の仙人洞 約2万年前、日本の大平山元 I 約1.65万年前 (約1.5万年前とも)", "years": 9000, "badge": None, "cert": "高い"},
    {"id": "house", "trace": "四角い家", "tech": "家族の住まい", "real": "前8800年ごろから広がる",
     "real_place": "PPNB の村 (アイン・ガザルなど。四角い何部屋もの家)",
     "also": "その前の PPNA にも、丸い家と同じ層に四角い家がある", "years": 10800, "badge": None, "cert": "高い"},
    {"id": "bin", "trace": "家の中の食べ物をためた所", "tech": "家の倉", "real": "前8800年ごろから",
     "real_place": "PPNB の家 (アイン・ガザルの倉の部屋など)", "also": "村の共同の倉はドゥラー 約1.13万年前 (床を浮かせた丸い倉)",
     "years": 10800, "badge": None, "cert": "中くらい"},
    {"id": "hunt", "trace": "獣と魚の骨", "tech": "狩りと漁", "real": "まだ調べていない",
     "real_place": None, "also": None, "years": None, "badge": "【未確認】", "cert": "中くらい"},
]
# 村の記録の道具 (本人と決めた順) と、本物でいちばん古い例 (docs/research/historical_records.md 2.1・2.2、app/records_demo.html)
G6_LADDER = [("印", "前7千年紀ごろから (サビ・アビヤドの封泥 前6000年ごろ。いちばん古い印の年代ははっきりしない)"),
             ("数え札", "前8000年ごろから (いちばん古い例はムレイベトの前9000年ごろ。本物では印より前。数える道具だったかは【議論あり】)"),
             ("封筒", "前3500〜3300年ごろ (スーサ・ウルクなどの粘土の玉)"),
             ("粘土の板", "前3400〜3300年ごろ (数と物のしるしの板。数だけの板は前3500年ごろから)"),
             ("文字", "前3350〜3200年ごろ (原楔形文字・ウルク IV 期)")]
G6_TOOL_KEY = {"印": "印", "数え札": "数え札", "封筒": "封筒", "粘土の板": "板", "文字": "文字"}
G6_WHAT = {"村の蓄えへの家ごとの出し入れ": "蓄え", "ほかの村との交換と貸し借り": "交換", "よその家の畑で刈った量": "刈る"}
G6_WHAT_SHOW = {"蓄え": "村の蓄えの出し入れ", "交換": "ほかの村との交換", "刈る": "よその家の畑で刈った量"}
G6_TOKEN = {"草の種": 100, "干し肉": 16, "ヤギ": 1, "土器": 10, "鎌": 10, "黒曜石": 10, "日": 10}
G6_WORK = ("記録をつける", "交換に行く", "土器づくり", "道具づくり")
GLYPHS = ["sd%d" % i for i in range(9)]
FRAMES = ["丸", "四角", "六角"]

NOTES = {
    "clock": "この世界の時計 (考古学ではこの細かさは分からない)",
    "year_len": "この世界の1年は120日 (30日の季節が4つ)。本物の1年とはちがう",
    "not_preserved": "掟・もめごと・まとめ役を選んだこと・話したこと・気持ち・名前・村の外でいなくなったヤギ・腐った食べ物・乳は、跡に残らない",
    "feast": "人が集まって食べた跡は見つからない",
    "living": "生きている人は跡を残しません。人数は家の跡から幅で見積もるだけです (村のタブ)。名前・気持ち・言葉はアプリの「履歴書」にあります (墓とはつなげていません)",
    "houses_unknown": "どの家族が住んだかは跡からは分からない。家を建てなかった家族は跡を残さない",
    "renumber": "新しい建物が見つかると番号が変わることがある (「小屋から北へ125m」のような場所は変わらない)",
    "village_wide": "土器のかけら・石の刃は村ぜんぶで数えている (どの建物で割れたかは記録にない)",
    "dna": "DNAや歯の成分は残らないこともある",
    "kin_limit": ("この世界の記録には父親がないので、父方のつながりは出していない (本物の古代DNAなら、父と子も分かる)。"
                  "よそから来た人の親族は村の墓にいないので分からない。「血縁なし」とは言えない"),
    "kin_degree": "祖母と孫は、2つの母と子のつながりと年ごろから推しはかる【解釈】 (DNAだけでは、祖母と孫・おばとめい・父ちがいのきょうだいは見分けにくい)",
    "iso": "歯の成分で分かるのは、歯ができた子どものころに育った土地の地質が村とちがうことだけ。よその土地は地質がちがうとした【仮定】。近くの同じ地質の土地から来た人は見分けられない。いつ村に来たかは分からない",
    "infant": "乳飲み子の骨はもろく、本物の発掘では見落とされやすい (ここでは全部見つかったとした)",
    "season_len": "1季節 (30日) は、昔のメソポタミアの役所が帳簿で使った1か月 (いつも30日として数えた) と同じ長さ",
    "ruk_season": "歯で分かるのは、狩られた獣が死んだ季節だけ。ほかの季節に村に人がいなかったとは言えない",
    "writing": "この世界の G6 の「文字」は、物のしるしと数のしるしを分けた粘土の板の記録で、量を確かめたこと (文字の入口。ウルク IV 期の書き方)。名前を音で書くのはその先 (本物では前3200年ごろから)",
    "tokens_shape": "【再現の案】数え札の形は Schmandt-Besserat の読み【議論あり】による: 草の種 = 円すい (▲)・ヤギ = 円柱・働いた日 = 四面体 (◆)。土器・鎌・黒曜石の確かな形は見つかっていないので、字で書く",
    "chronicle": "言い伝え。形には残らない。跡とは別。このページで名前が出るのはここだけ",
    "chronicle_mismatch": "言い伝えと跡が合わないこともある (たとえば祭りの年の名があっても、人が集まって食べた跡は見つからない)",
    "g6_empty": "まだ記録はない。この村は、まだ印も数え札も使っていない。村が残したのは、口で伝える年の名だけ (村のタブのいちばん下)",
    "ubaid": "本物のウバイド期 (G5にあたる) には、もう数え札も粘土の封もあった",
    "order": "本物の順は 数え札 (前8000年ごろから) → 印 (前7千年紀ごろから) → 封筒 (前3500〜3300年ごろ) → 数の粘土板 (前3500年ごろから) → 原楔形文字 (前3350〜3200年ごろ)。この村は印から始める (本人と決めた順)",
    "seal_g6": "家の印は G6 から。家の印が見つかると、印A・印B…ごとの封のかけらの数と、数え札・粘土の板の家ごとの記録が並ぶ。印と建物はつなげない (封のかけらがどこに捨てられたかは記録にない)",
    "people_g6": "村の記録は家ごと (家の印) で、人の名前は記録に出てこない。亡くなった人は墓に",
    "report": "この報告は、シミュレーションの記録から、考古学者に見えるものだけを計算で取り出したもの",
    "order_known": "順番が分かる数少ない例: 床下の墓は、その家より後に入った。広げた壁は、もとの壁より後",
    "tech_rest": "ほかの技 (知識・掟・干し肉・槍・入れ物など) は跡が残らないので、技術の木 (アプリと tech_tree_demo.html) へ",
    "plants_always": "穂の軸は自然に落ちる形 (野生の形)。畑の跡そのものは見つからない",
    "pop_always": "家がはなれて建つ村では、広がりからの見積もりは大きく出すぎる。本当の人数は跡からは分からない",
    "ages": "年ごろは本人の区分 (乳飲み子 0〜2・子 3〜11・手伝える子 12〜14・大人 15〜54・年寄り 55〜)。骨で言える限りの注をつける",
    "certainty": "確かさ: ●●● 高い / ●●○ 中くらい / ●○○ 低い (いつも字といっしょ)",
}

BONE_NOTE = {
    "乳飲み子": ("歯で月の単位まで分かる", "高い"),
    "子": ("歯で1年ほどの幅まで分かる", "高い"),
    "手伝える子": ("大人との境目は±2〜3年", "中くらい"),
    "大人": ("1人の幅は10年以上", "中くらい"),
    "年寄り": ("骨では「50くらいより上」としか言えない (55の境目は骨では引けない)", "低い"),
}


# ---------------------------------------------------------------- 小さな道具
def dlab(d):
    return "%d年%d日目" % (d // YEAR, d % YEAR + 1)


def slab(d):
    return "%d年の%s" % (d // YEAR, SEAS[(d % YEAR) // SEASON])


def se(d):
    return d + SEASON - 1 - d % SEASON


def age_class(a):
    return next(n for n, lo, hi in AGE if lo <= a <= hi)


def rnd(x):
    """人数の丸め方: 100 より小さい数はそのまま (四捨五入)、100 以上は 10 の位で四捨五入"""
    if x is None:
        return None
    return int(x + 0.5) if x < 100 else int(x / 10 + 0.5) * 10


def fmt(n):
    return "{:,}".format(n)


def hull_area(pts):
    """凸包の広さ (点が 3 つより少ない・一直線なら None)"""
    P = sorted(set(pts))
    if len(P) < 3:
        return None

    def cr(o, a, b):
        return (a[0] - o[0]) * (b[1] - o[1]) - (a[1] - o[1]) * (b[0] - o[0])
    lo, up = [], []
    for p in P:
        while len(lo) >= 2 and cr(lo[-2], lo[-1], p) <= 0:
            lo.pop()
        lo.append(p)
    for p in reversed(P):
        while len(up) >= 2 and cr(up[-2], up[-1], p) <= 0:
            up.pop()
        up.append(p)
    h = lo[:-1] + up[:-1]
    if len(h) < 3:
        return None
    return abs(sum(h[i][0] * h[(i + 1) % len(h)][1] - h[(i + 1) % len(h)][0] * h[i][1] for i in range(len(h)))) / 2


def hull_pts(pts):
    P = sorted(set(pts))
    if len(P) < 3:
        return []

    def cr(o, a, b):
        return (a[0] - o[0]) * (b[1] - o[1]) - (a[1] - o[1]) * (b[0] - o[0])
    lo, up = [], []
    for p in P:
        while len(lo) >= 2 and cr(lo[-2], lo[-1], p) <= 0:
            lo.pop()
        lo.append(p)
    for p in reversed(P):
        while len(up) >= 2 and cr(up[-2], up[-1], p) <= 0:
            up.pop()
        up.append(p)
    return lo[:-1] + up[:-1]


def plant_words(c):
    vis = {k: c.get(k, 0) * w for k, w in PLANT_W.items()}
    top = max(vis.values()) if vis else 0
    out = {}
    for k, v in vis.items():
        if v <= 0:
            out[k] = "見つからない"
        elif v == top:
            out[k] = "いちばん多い"
        elif v >= 0.1 * top:
            out[k] = "少し"
        else:
            out[k] = "ほとんど見つからない"
    return out


# ---------------------------------------------------------------- 読む
class GateError(Exception):
    pass


def _read_json(path):
    with open(path, encoding="utf-8") as f:
        return json.load(f)


def _read_jsonl(path):
    with open(path, encoding="utf-8") as f:
        return [json.loads(l) for l in f if l.strip()]


def load(data_dir, tries=3, wait=2.0):
    """state.json と records/ を読む。meta の日と state の日が合わない・書きかけで読めないときは、少し待ってやりなおす"""
    R = os.path.join(data_dir, "records")
    last = None
    for i in range(tries + 1):
        try:
            meta = _read_json(os.path.join(R, "meta.json"))
            st = _read_json(os.path.join(data_dir, "state.json"))
            if meta.get("state_day") != st.get("day") or meta.get("state_next_event") != st.get("next_event"):
                raise GateError("records/meta.json (%s日目・%s) と state.json (%s日目・%s) が合わない"
                                % (meta.get("state_day"), meta.get("state_next_event"), st.get("day"), st.get("next_event")))
            rec = {"meta": meta}
            for f in ("people", "households", "membership", "year_names"):
                rec[f] = _read_json(os.path.join(R, f + ".json"))
            for f in ("season_village", "season_household"):
                rec[f] = _read_jsonl(os.path.join(R, f + ".jsonl"))
            rec["ledger_goats"] = []
            with open(os.path.join(R, "ledger.jsonl"), encoding="utf-8") as fh:
                for l in fh:
                    if '"item":"ヤギ"' in l and "つぶした" in l:
                        rec["ledger_goats"].append(json.loads(l))
            sp = os.path.join(R, "season_person.jsonl")
            rec["work_days"] = {}
            if any(r.get("era") == "G6" for r in rec["season_village"]):
                for r in _read_jsonl(sp):
                    dba = r.get("days_by_activity") or {}
                    n = sum(v for k, v in dba.items() if k in G6_WORK)
                    if n:
                        key = (r["season_end_day"], r.get("household_id"))
                        rec["work_days"][key] = rec["work_days"].get(key, 0) + n
            meta2 = _read_json(os.path.join(R, "meta.json"))
            if meta2 != meta:
                raise GateError("読んでいるあいだに records/ が書きかわった")
            return st, rec
        except (GateError, ValueError, OSError) as e:  # ValueError = 書きかけの JSON
            last = e
            if i < tries:
                time.sleep(wait)
    raise GateError("読めなかった (%d 回やりなおした): %s" % (tries, last))


# ---------------------------------------------------------------- 作る
def build(st, rec):
    DAY = st["day"]
    meta, people, hh, mem = rec["meta"], rec["people"], rec["households"], rec["membership"]
    sv, sh = rec["season_village"], rec["season_household"]
    events = st["events"]
    e2 = st.get("era2") or {}
    camp = st["camp"]
    cx, cy = camp["x"], camp["y"]
    hut_day = camp.get("dwelling_day")

    # 層: フェーズが進んだ日の次の日から (F1〜F6 はまとめて F)
    adv = []
    for x in st.get("era_log", []):
        if x["era"].startswith("G") and x["era"] in LAYER_IDS:
            adv.append((x["day"], x["era"]))
    adv.sort()

    def layer(d):
        cur = "F"
        for day, era in adv:
            if d > day:
                cur = era
        return cur

    # ---- 季節の行 (F 層は state から 30 日ずつ、あとは記録の行)
    rows = []
    first_rec = sv[0]["season_start_day"] if sv else DAY + 1
    for s in range(0, min(first_rec, F_LAST + 1), SEASON):
        rows.append({"s": s, "d": min(s + SEASON - 1, F_LAST, DAY), "rec": None})
    for r in sv:
        rows.append({"s": r["season_start_day"], "d": r["season_end_day"], "rec": r})
    starts = [r["s"] for r in rows]
    D = [r["d"] for r in rows]
    nrow = len(rows)

    def row_of_day(day):
        if day is None or day < 0 or day > D[-1]:
            return None
        i = bisect.bisect_right(starts, day) - 1
        return i if i >= 0 and rows[i]["s"] <= day <= rows[i]["d"] else None

    # 出来事 → 行 (記録の行は、その行の集まりの最初の出来事から次の行の前まで。F 層は日で)
    rng = []
    for i, r in enumerate(rows):
        for rd in (r["rec"] or {}).get("rounds") or []:
            lo, hi = rd.get("meeting_first"), rd.get("event_end")
            if lo is None:
                lo = rd.get("event_first")
            if lo is not None and hi is not None:
                rng.append((lo, hi, i))
    rng.sort()
    rlo = [x[0] for x in rng]

    def row_of_event(e):
        k = bisect.bisect_right(rlo, e["id"]) - 1
        if k >= 0 and rng[k][0] <= e["id"] < rng[k][1]:
            return rng[k][2]
        return row_of_day(e["day"])

    ev_by_type = collections.defaultdict(list)
    for e in events:
        ev_by_type[e["type"]].append(e)

    # ---- 建物 (小屋のまわり、北から時計まわり。同じ角度なら近い方が先)
    homes = e2.get("homes") or {}
    name2id = {h["name"]: h["id"] for h in hh}
    hid = {h["id"]: h for h in hh}

    def ang(x_m, y_m):
        return math.degrees(math.atan2(x_m, -y_m)) % 360

    blist = []
    for n, v in homes.items():
        if v.get("start") is None or v["start"] > DAY:
            continue
        x_m, y_m = (v["x"] - cx) * CELL_M, (v["y"] - cy) * CELL_M
        blist.append({"name": n, "hid": name2id.get(n), "v": v, "x_m": round(x_m, 1), "y_m": round(y_m, 1),
                      "ang": ang(x_m, y_m), "dist": math.hypot(x_m, y_m)})
    blist.sort(key=lambda b: (round(b["ang"], 1), round(b["dist"], 3), b["name"]))
    for i, b in enumerate(blist, 1):
        b["no"] = i
    b_by_hid = {b["hid"]: b for b in blist if b["hid"]}

    # 家の中の食べ物をためた所: 家が建っていて、その家の倉に物が入った最初の季節
    bin_row = {}
    for r in sh:
        hm = r.get("home") or {}
        h = r.get("household_id")
        if h in bin_row or h not in b_by_hid:
            continue
        if hm.get("built_day") is not None and hm["built_day"] <= r["season_end_day"] and any((v or 0) > 0 for v in (r.get("store") or {}).values()):
            bin_row[h] = row_of_day(r["season_end_day"])

    for b in blist:
        v = b["v"]
        b["start_i"] = row_of_day(v["start"])
        b["built_i"] = row_of_day(v["built"]) if v.get("built") is not None and v["built"] <= DAY else None
        sizes = [(d, z) for d, z in (v.get("sizes") or []) if d <= DAY]
        b["floor"] = [[D[row_of_day(d)], z] for d, z in sizes]
        b["ext_i"] = [row_of_day(d) for d, z in sizes[1:]]
        b["bin_i"] = bin_row.get(b["hid"])
        b["graves"] = []

    # ---- 墓 (亡くなった人 1 人 = 墓 1 つ。亡くなった日と人の順。番号は変えない)
    pid = {p["id"]: p for p in people}
    dead = sorted([p for p in people if p.get("died_day") is not None and p["died_day"] <= DAY],
                  key=lambda p: (p["died_day"], p["id"]))
    gno = {p["id"]: i for i, p in enumerate(dead, 1)}
    mem_by = collections.defaultdict(list)
    for m in mem:
        mem_by[m["person_id"]].append(m)

    def house_at(p):
        dd = p["died_day"]
        for m in mem_by.get(p["id"], []):
            if m["from_day"] <= dd and (m.get("to_day") is None or m["to_day"] >= dd):
                return m["household_id"]
        return p.get("household_id")

    def kin_of(p):
        out = []
        for q in dead:
            if q["id"] == p["id"]:
                continue
            if q.get("mother_id") == p["id"] or p.get("mother_id") == q["id"]:
                out.append([gno[q["id"]], "母と子"])
            elif p.get("mother_id") and q.get("mother_id") == p["mother_id"]:
                out.append([gno[q["id"]], "きょうだい (母が同じ)"])
            else:
                pm = pid.get(p.get("mother_id")) if p.get("mother_id") else None
                qm = pid.get(q.get("mother_id")) if q.get("mother_id") else None
                if (pm and pm.get("mother_id") == q["id"]) or (qm and qm.get("mother_id") == p["id"]):
                    out.append([gno[q["id"]], "祖母と孫"])
        return sorted(out)

    def grew_up_away(p):
        """歯の成分 (R12'): よそから来た人で、村に来たとき 3 歳以上 (いちばん早くできる永久歯の冠ができたあと)。
        もっと小さいときに来た人は、歯の成分が村の分とまざるので「村の外で育った」とは言わない"""
        if p.get("origin") != "よそから来た":
            return False
        cd, bd = p.get("came_day"), p.get("born_day")
        return cd is None or bd is None or (cd - bd) >= 3 * YEAR

    graves = []
    for p in dead:
        a = p.get("age_at_death") or 0
        c = age_class(a)
        h = house_at(p)
        hb = (hid.get(h) or {}).get("home_built_day")
        b = b_by_hid.get(h)
        under = hb is not None and hb <= p["died_day"] and b is not None
        note, cert = BONE_NOTE[c]
        if c == "大人":
            sub = ("大人になりかけ (15〜19くらい。骨の端がくっつききっていない)" if a <= 19 else
                   "若い大人 (20〜35くらい)" if a <= 34 else
                   "中くらいの大人 (35〜50くらい)" if a <= 49 else "年をとった大人 (50くらいより上)")
            note = sub + "。" + note
        g = {"no": gno[p["id"]], "i": row_of_day(p["died_day"]), "age_class": c, "bone_note": note, "age_cert": cert,
             "sex": ("たぶん" + p["sex"]) if a >= 15 and p.get("sex") in ("男", "女") else "骨の形では分からない",
             "mark": "獣の歯のあと" if p.get("death_cause") == "ザガ" else None,
             "cause_text": ("骨に獣の歯のあと (殺されたのか、死んだあとにかじられたのかは分からない)" if p.get("death_cause") == "ザガ"
                            else "死因は分からない (病の多くは骨に残らない)"),
             "modern": {"iso": grew_up_away(p),
                        "dna_sex": p.get("sex") if a < 15 and p.get("sex") in ("男", "女") else None,
                        "kin": kin_of(p)},
             "place": {"building": b["no"]} if under else {"centre": True}}
        if under:
            b["graves"].append(g["no"])
        graves.append(g)
    g_by_row = collections.defaultdict(list)
    for g in graves:
        g_by_row[g["i"]].append(g)

    # ---- 出来事から: 炉の灰・獣と魚の骨・ヤギの骨
    ash = collections.Counter()
    for e in ev_by_type.get("火", []):
        t = e.get("text") or ""
        if "おこした" in t and "できなかった" not in t:
            i = row_of_event(e)
            if i is not None:
                ash[i] += 1
    bones = collections.defaultdict(lambda: [0, 0, 0])
    ruk_season = collections.Counter()
    ruk_rows = []  # [行, 死んだ季節] (ページで、選んだ季節までのルクだけを数えるため)
    for e in ev_by_type.get("狩り", []):
        dd = e.get("data") or {}
        if dd.get("killer"):
            k, n = 0, 1
            ruk_season[SEAS[(e["day"] % YEAR) // SEASON]] += 1
        else:
            m = re.search(r"\((ピクの肉|魚) (\d+) 匹\)", e.get("text") or "")
            if not m:
                continue
            k, n = (1 if m.group(1) == "ピクの肉" else 2), int(m.group(2))
        i = row_of_event(e)
        if i is not None:
            bones[i][k] += n
            if k == 0:
                ruk_rows.append([i, SEAS[(e["day"] % YEAR) // SEASON]])
    goat_born = None
    goat_bones = collections.defaultdict(list)
    for r in rec["ledger_goats"]:
        if r.get("item") != "ヤギ" or r.get("reason") != "つぶした":
            continue
        i = row_of_day(r["season_end_day"])
        ids = ((r.get("detail") or {}).get("goats")) or []
        n = abs(int(r.get("amount") or 0))
        for j in range(max(n, len(ids))):
            gid = ids[j] if j < len(ids) else None
            info = None
            if gid is not None:
                if goat_born is None:
                    goat_born = _goat_index(os.path.join(rec.get("_dir", ""), "records", "snapshots.jsonl"))
                info = goat_born.get(gid)
            if info and info.get("born") is not None:
                ga = (rows[i]["d"] - info["born"]) // YEAR
                gcls = "子ヤギ (1歳より下)" if ga < 1 else "若いヤギ (1〜2歳)" if ga < 3 else "大人のヤギ (3歳から)"
                gsex = {"メス": "たぶんメス", "オス": "たぶんオス"}.get(info.get("sex"), "分からない") if ga >= 1 else "骨では分からない"
            else:
                gcls, gsex = "分からない", "分からない"
            goat_bones[i].append({"age_class": gcls, "sex": gsex})

    # ---- 植物 (食べた物に焼けて残りやすさをかける)【仮定】
    eat_by_row = collections.defaultdict(collections.Counter)
    for s in st.get("stats", []):
        i = row_of_day(s.get("day"))
        if i is None:
            continue
        for k, v in (s.get("eaten_by_kind") or {}).items():
            if k in PLANT_W:
                eat_by_row[i][k] += v or 0

    # ---- 季節ごと
    seasons = []
    cum = dict(hut=0, houses=0, footings=0, ext=0, bins=0, ash_rows=0, sherds=0, blades=0, bones=[0, 0, 0],
               dung_rows=0, mice_rows=0, goat_bones=0, graves=0, graves_floor=0, graves_centre=0)
    plants_cum = collections.Counter()
    plants_layer = collections.defaultdict(collections.Counter)
    pl_partial = []
    prev_dung = 0
    layer_of_row = []
    sum_check = collections.Counter()
    for i, r in enumerate(rows):
        s, d, rv = r["s"], r["d"], r["rec"]
        L = layer(d)
        layer_of_row.append(L)
        add = {}
        add["hut"] = 1 if hut_day is not None and s <= hut_day <= d else 0
        add["houses"] = sorted(b["no"] for b in blist if b["built_i"] == i)
        add["footings"] = sorted(b["no"] for b in blist if b["start_i"] == i and (b["built_i"] is None or b["built_i"] > i))
        add["ext"] = sorted(b["no"] for b in blist if i in b["ext_i"])
        add["bins"] = sorted(b["no"] for b in blist if b["bin_i"] == i)
        add["ash"] = 1 if ash.get(i) else 0
        if rv is None:
            add["sherds"], add["blades"] = 0, 0
        else:
            add["sherds"], add["blades"] = rv.get("pots_broken"), rv.get("sickles_broken")
        add["bones"] = list(bones[i]) if i in bones else [0, 0, 0]
        dung = 1 if rv is not None and ((rv.get("goats") or {}).get("count") or 0) > 0 else 0
        add["dung"] = dung
        add["goat_bones"] = goat_bones.get(i, [])
        add["mice"] = 1 if rv is not None and (rv.get("pests") or 0) > 0 else 0
        feast = ((rv or {}).get("g5") or {}).get("feast") or {}
        meat = sum(v for k, v in (feast.get("cost") or {}).items() if k in MEAT) if feast.get("held") else 0
        add["feast_bones"] = 1 if meat else 0
        gs = g_by_row.get(i, [])
        add["graves"] = [g["no"] for g in gs]

        cum["hut"] += add["hut"]
        cum["houses"] = sum(1 for b in blist if b["built_i"] is not None and b["built_i"] <= i)
        cum["footings"] = sum(1 for b in blist if b["start_i"] is not None and b["start_i"] <= i and (b["built_i"] is None or b["built_i"] > i))
        cum["ext"] += len(add["ext"])
        cum["bins"] += len(add["bins"])
        cum["ash_rows"] += add["ash"]
        cum["sherds"] += add["sherds"] or 0
        cum["blades"] += add["blades"] or 0
        cum["bones"] = [a + b for a, b in zip(cum["bones"], add["bones"])]
        cum["dung_rows"] += dung
        cum["mice_rows"] += add["mice"]
        cum["goat_bones"] += len(add["goat_bones"])
        cum["graves"] += len(gs)
        cum["graves_floor"] += sum(1 for g in gs if "building" in g["place"])
        cum["graves_centre"] += sum(1 for g in gs if "centre" in g["place"])
        sum_check["houses"] += len(add["houses"])

        # 人数の見積もり (R13)
        built = [b for b in blist if b["built_i"] is not None and b["built_i"] <= i]
        floor = 0
        for b in built:
            z = 0
            for fd, fz in b["floor"]:
                if fd <= d:
                    z = fz
            floor += z
        hut_on = hut_day is not None and hut_day <= d
        nb = len(built) + (1 if hut_on else 0)
        pts = [(b["x_m"], b["y_m"]) for b in built] + ([(0.0, 0.0)] if hut_on else [])
        a = hull_area(pts)
        ha = a / 10000 if a else None
        est = []
        if floor:
            est.append(floor / 10)
        if nb:
            est.append(nb * 5)
        if ha:
            est += [ha * 120, ha * 200]
        pop = None
        if est:
            lo, hi = min(est), max(est)
            pop = {"floor_m2": floor or None, "by_floor": rnd(floor / 10) if floor else None, "bldg": nb or None,
                   "by_bldg": nb * 5 if nb else None, "ha": round(ha, 2) if ha else None,
                   "area": [rnd(ha * 120), rnd(ha * 200)] if ha else None,
                   "lo": rnd(lo), "hi": rnd(hi), "lo_raw": round(lo, 1), "hi_raw": round(hi, 1),
                   "ratio": int(hi / lo + 0.5) if lo else None}

        plants_cum.update(eat_by_row.get(i, {}))
        plants_layer[L].update(eat_by_row.get(i, {}))

        # この季節に土に入ったもの (文は Python で作る。祭り・乳・掟・もめごと・まとめ役は書かない)
        text = []
        if add["hut"]:
            text.append("柱の穴の輪と床の跡が1つ (柱を立てた小屋。屋根と壁は腐って残らない)")
        if add["houses"]:
            text.append("四角い家の跡が%d軒ふえた (%s)" % (len(add["houses"]), "建物" + "・".join(map(str, add["houses"]))))
        if add["footings"]:
            text.append("壁の土台だけのものが%dつ (%s)" % (len(add["footings"]), "建物" + "・".join(map(str, add["footings"]))))
        for no in add["ext"]:
            text.append("建物%dには壁を足して広げた跡" % no)
        if add["bins"]:
            text.append("%sの中に食べ物をためた所 (しきった所) の跡" % ("建物" + "・".join(map(str, add["bins"]))))
        if add["ash"]:
            text.append("炉の跡ができた (小屋のそば。灰・炭・焼けた石)" if cum["ash_rows"] == 1 else "炉の灰がたまった (小屋のそば)")
        if add["feast_bones"]:
            text.append("1回でまとめて捨てた獣の骨のまとまり")
        if rv is not None and add["sherds"] is None:
            text.append("土器のかけら: 記録なし")
        elif add["sherds"]:
            text.append("土器のかけら %s個分" % fmt(add["sherds"]))
        if rv is not None and add["blades"] is None:
            text.append("石の刃: 記録なし")
        elif add["blades"]:
            text.append("石の刃 %s本分" % fmt(add["blades"]))
        bp = []
        if add["bones"][0]:
            bp.append("ルク (大きな獣) %d頭分" % add["bones"][0])
        if add["bones"][1]:
            bp.append("ピク (小さな獣) %d匹分" % add["bones"][1])
        if add["bones"][2]:
            bp.append("魚 %d匹分" % add["bones"][2])
        if bp:
            text.append("獣と魚の骨: " + "・".join(bp))
        if dung and not prev_dung:
            text.append("ヤギの糞とひづめの跡が出はじめた")
        if prev_dung and not dung:
            text.append("ヤギの糞がとぎれた")
        if add["goat_bones"]:
            text.append("ヤギの骨 %d頭分" % len(add["goat_bones"]))
        if add["mice"]:
            text.append("家ネズミの骨")
        if gs:
            parts = []
            for g in gs:
                pl = ("建物%dの床下" % g["place"]["building"]) if "building" in g["place"] else "村のまん中"
                parts.append("墓%d: %s・%s" % (g["no"], pl, g["age_class"]))
            text.append("墓が%d基 (%s)" % (len(gs), "、".join(parts)))
        if not text:
            text.append("新しい跡はない")
        prev_dung = dung

        y0, y1 = s // YEAR, d // YEAR
        span = ("%d年%d〜%d日目" % (y0, s % YEAR + 1, d % YEAR + 1)) if y0 == y1 else "%s〜%s" % (dlab(s), dlab(d))
        part = None
        if (d - s + 1) < SEASON:  # 短い行 (4年の夏の F 層と G1 層)。日目は年の中の日 (「10年31日目」の形とそろえる)
            part = "%d〜%d日目" % (s % YEAR + 1, d % YEAR + 1)
        seasons.append({"d": d, "s": s, "label": slab(s), "span": span, "part": part, "layer": L,
                        "add": add, "cum": json.loads(json.dumps(cum)), "pop": pop,
                        "plants": plant_words(plants_cum), "text": text})
        pl_partial.append(plant_words(plants_layer[L]))  # その層の、この季節までの言葉 (下で、層ぜんぶの言葉とちがう行だけ残す)
    pl_final = {L: plant_words(c) for L, c in plants_layer.items()}
    for i, w in enumerate(pl_partial):
        if w != pl_final[layer_of_row[i]]:
            seasons[i]["pl_layer"] = w  # 選んだ季節がこの行のとき、その層の植物の言葉はこちら (層の途中まで)

    # ---- 層
    layers = []
    for lid in LAYER_IDS:
        idx = [i for i, L in enumerate(layer_of_row) if L == lid]
        real, real_years = LAYER_REAL[lid]
        ramp = 6 - LAYER_IDS.index(lid)
        if idx:
            f, l = rows[idx[0]]["s"], rows[idx[-1]]["d"]
            layers.append({"id": lid, "first": f, "last": l, "last_row": rows[idx[-1]]["d"], "first_date": dlab(f), "last_date": dlab(l),
                           "days": l - f + 1, "real": real, "real_years": real_years, "rows": len(idx), "entered": True, "ramp": ramp})
        else:
            layers.append({"id": lid, "first": None, "last": None, "last_row": None, "first_date": None, "last_date": None, "days": 0,
                           "real": real, "real_years": real_years, "rows": 0, "entered": False, "ramp": ramp})

    # ---- 建物 (外に出す形)
    buildings = []
    for b in blist:
        buildings.append({"no": b["no"], "dir": DIRS[int(((b["ang"] + 22.5) % 360) // 45)], "m": int(b["dist"] / 5 + 0.5) * 5,
                          "x_m": b["x_m"], "y_m": b["y_m"],
                          "start_row": D[b["start_i"]] if b["start_i"] is not None else None,
                          "found_row": D[b["built_i"]] if b["built_i"] is not None else None,
                          "found_layer": layer_of_row[b["built_i"]] if b["built_i"] is not None else None,
                          "start_layer": layer_of_row[b["start_i"]] if b["start_i"] is not None else None,
                          "floor": b["floor"], "ext_rows": [D[i] for i in b["ext_i"]],
                          "bin_row": D[b["bin_i"]] if b["bin_i"] is not None else None,
                          "graves": sorted(b["graves"])})

    hut_i = row_of_day(hut_day) if hut_day is not None and hut_day <= DAY else None
    hut = {"x_m": 0, "y_m": 0, "row": D[hut_i] if hut_i is not None else None,
           "hearth_rows": [D[i] for i in sorted(ash)]}

    graves_out = []
    for g in graves:
        i = g["i"]
        graves_out.append({"no": g["no"], "row": D[i], "label": seasons[i]["label"], "layer": layer_of_row[i],
                           "place": g["place"], "age_class": g["age_class"], "bone_note": g["bone_note"], "age_cert": g["age_cert"],
                           "sex": g["sex"], "mark": g["mark"], "cause_text": g["cause_text"], "modern": g["modern"]})

    bones_layer = collections.OrderedDict()
    for i, L in enumerate(layer_of_row):
        bl = bones_layer.setdefault(L, [0, 0, 0])
        for k in range(3):
            bl[k] += seasons[i]["add"]["bones"][k]

    # ---- 技 (最初の跡が土に入った季節)
    def first_row(f):
        for sz in seasons:
            if f(sz):
                return sz
        return None
    firsts = {
        "grain": first_row(lambda sz: False),
        "dwell": first_row(lambda sz: sz["add"]["hut"]),
        "goat": first_row(lambda sz: sz["add"]["dung"]),
        "hearth": first_row(lambda sz: sz["add"]["ash"]),
        "blade": first_row(lambda sz: (sz["add"]["blades"] or 0) > 0),
        "sherd": first_row(lambda sz: (sz["add"]["sherds"] or 0) > 0),
        "house": first_row(lambda sz: sz["add"]["houses"]),
        "bin": first_row(lambda sz: sz["add"]["bins"]),
        "hunt": first_row(lambda sz: any(sz["add"]["bones"])),
    }
    gi = next((i for i in range(nrow) if eat_by_row.get(i, {}).get("草の種", 0) > 0), None)
    firsts["grain"] = seasons[gi] if gi is not None else None
    ranked = sorted({t["years"] for t in TECH if t["years"]}, reverse=True)
    tech = []
    for t in TECH:
        fr = firsts.get(t["id"])
        tech.append({"id": t["id"], "trace": t["trace"], "tech": t["tech"], "first_row": fr["d"] if fr else None,
                     "first_label": fr["label"] if fr else None, "layer": fr["layer"] if fr else None,
                     "real": t["real"], "real_place": t["real_place"], "also": t["also"],
                     "real_rank": ranked.index(t["years"]) + 1 if t["years"] else None, "badge": t["badge"], "cert": t["cert"]})

    # ---- 年の名 (口で伝える年代記)【村】
    yn = {y["year"]: y for y in rec["year_names"]}
    cur_year = DAY // YEAR
    chronicle = []
    if yn:
        for y in range(min(yn), cur_year + 1):
            r = yn.get(y) or {}
            name = r.get("name")
            if name:
                state = "named"
            elif y == cur_year or (r.get("last_day") is not None and r["last_day"] >= DAY) or r.get("asked"):
                state = "pending"
            else:
                state = "before"
            dec = None
            if name:
                eid = r.get("event_id")
                di = row_of_event(events[eid]) if isinstance(eid, int) and 0 <= eid < len(events) else row_of_day(r.get("decided_day"))
                dec = D[di] if di is not None else None
            chronicle.append({"year": y, "first": y * YEAR, "last": y * YEAR + YEAR - 1, "name": name, "state": state,
                              "decided_row": dec})

    # ---- G6 (村の記録)。G6 の前は空
    g6 = build_g6(st, rec, rows, seasons, layer_of_row, row_of_event, ev_by_type, adv)

    last = seasons[-1]
    lc = last["cum"]
    built_now = [b for b in buildings if b["found_row"] is not None]
    floors_now = collections.Counter(b["floor"][-1][1] for b in built_now if b["floor"])
    fl_txt = "・".join("%dm²が%d軒" % (z, n) for z, n in sorted(floors_now.items()))
    pl = last["pop"] or {}
    # 割れた土器の合計を、作った数 − いまの数 とくらべる (合うときだけ「確かめた」と書く。G6 ではほかの村との出し入れで合わなくなることがある)
    pots_ok = bool(sv) and (sum((r.get("pots_made") or 0) for r in sv) - sum((r.get("pots_broken") or 0) for r in sv)) == (sv[-1].get("pots") or 0)

    def f_(x):
        return fmt(x) if isinstance(x, int) else x
    how = {
        "houses": {"src": "家族の住まいの記録 (建てはじめた日・建った日・床の広さ・場所) と、村の住まい (小屋) の記録", "rule": "R1",
                   "calc": "建った家 %d軒 (%s)。建てかけ %d = 壁の土台。小屋 %d = 柱の穴の輪" % (lc["houses"], fl_txt or "なし", lc["footings"], lc["hut"]),
                   "reading": "床の広さは考古学でもよく分かる。屋根と壁の作りは推しはかるだけ。建てなおした跡はない (層は1つ)。くらべる: ハラフの丸い家 7〜38m²、チャタルヒュユクの居間 約25m²【未確認】", "cert": "高い"},
        "sherds": {"src": "季節ごとの「割れた土器」の数", "rule": "R4",
                   "calc": "季節ごとの「割れた土器」を足して %s個分%s。使っている土器は入れない" % (fmt(lc["sherds"]), " (作った数 − いまの数 とも合うことを確かめた)" if pots_ok else ""),
                   "reading": "考古学者は縁のかけらから「少なくとも何個」と数えるので、これより少なく出る。大きなつぼ (1個 約14〜18リットル) → 穀物をためた【解釈】",
                   "cert": "高い"},
        "blades": {"src": "季節ごとの「割れた鎌」の数", "rule": "R5", "calc": "割れた鎌の合計 %s本分。1本に刃が何枚かは記録にないので「本分」" % fmt(lc["blades"]),
                   "reading": "つやのきめは、穂が落ちる前の半分熟れた草を刈ったときのもの → 野生の草の種を刈った。柄は木なので残らない", "cert": "中くらい"},
        "graves": {"src": "亡くなった人の記録 (亡くなった日・年齢・男女・家族・来かた)", "rule": "R12",
                   "calc": "亡くなった人 %d人 = 墓 %d基。亡くなった日に家族の家が建っていれば床下 (%d)、なければ村のまん中 (%d)" % (lc["graves"], lc["graves"], lc["graves_floor"], lc["graves_centre"]),
                   "reading": "人の跡は墓だけ。村を出て行った人の墓はない", "cert": "中くらい"},
        "pop": {"src": "建物の跡 (床の広さ・数・村の広がり)", "rule": "R13",
                "calc": ("床の広さ: %sm² ÷ 1人10m² (Naroll 1962) = 約%s人。建物の数: %s × 1軒5人 (チャタルヒュユクの見積もりの数) = 約%s人。村の広がり: %sha × 1haに120〜200人 (西アジアの村の目安【未確認】) = 約%s〜%s人。いちばん少ない〜いちばん多い見積もり、何倍ちがうかは丸める前の数で" %
                         (f_(pl.get("floor_m2")), f_(pl.get("by_floor")), f_(pl.get("bldg")), f_(pl.get("by_bldg")), pl.get("ha"),
                          f_((pl.get("area") or [None, None])[0]), f_((pl.get("area") or [None, None])[1]))) if pl else "見積もれない",
                "reading": NOTES["pop_always"], "cert": "低い"},
        "bones": {"src": "狩りの出来事 (しとめたルク・ピクの肉・魚)", "rule": "R7",
                  "calc": "ルク %d頭分・ピク %d匹分・魚 %d匹分。3つは単位がちがうので足さない" % tuple(lc["bones"]),
                  "reading": "どれも野生の獣。「少なくとも何頭」と数えると本当より少なく出る。魚の骨は細かいふるいで見つかる。" + NOTES["ruk_season"], "cert": "中くらい"},
        "dung": {"src": "季節の終わりに村にいたヤギの数 (あるかないかだけ使う)", "rule": "R8",
                 "calc": "ヤギがいた季節 %d。頭数は出さない。ヤギの骨 (村でつぶしたヤギ) %d頭分" % (lc["dung_rows"], lc["goat_bones"]),
                 "reading": "糞とひづめの跡 → ヤギが村の中にいた。骨がなければ、飼っていたか、何頭いたかは言えない", "cert": "中くらい"},
        "hearth": {"src": "出来事「火」(おこせたものだけ。失敗は残らない)", "rule": "R2", "calc": "火をおこせた季節 %d" % lc["ash_rows"],
                   "reading": "小屋のそばに炉が1つ。四角い家の中には炉の跡がない", "cert": "高い"},
        "bins": {"src": "家ごとの倉の中身 (あるかないかだけ使う) と家が建った日", "rule": "R3",
                 "calc": "家が建っていて、倉に物が入った最初の季節から。いま %d軒" % lc["bins"],
                 "reading": "しきった所の跡。何をためたかは、焼けていないので分からない", "cert": "中くらい"},
        "mice": {"src": "季節ごとの虫やネズミの害", "rule": "R10", "calc": "害のあった季節 %d" % lc["mice_rows"],
                 "reading": "家ネズミの骨 → 1年じゅう住んでいた (定住)", "cert": "中くらい"},
        "plants": {"src": "毎日食べた物の種類と量", "rule": "R6",
                   "calc": "層ごとに足し、焼けて残りやすさの重み (木の実の殻 1.0・草の種 0.5・芋 0.05) をかけた。いちばん大きいもの = いちばん多い、その10分の1以上 = 少し、0より大きい = ほとんど見つからない、0 = 見つからない。割合や量は出さない",
                   "reading": NOTES["plants_always"], "cert": "低い"},
        "layers": {"src": "フェーズが進んだ日", "rule": "層 = フェーズ",
                   "calc": "フェーズが進んだ日の次の日から新しい層。F1〜F6 はまとめて F 層。本物の時代はおおよその見立て",
                   "reading": "放射性炭素の年代では、この村の全部が1つの年代の幅に入る", "cert": "低い"},
        "numbering": {"src": "建物の場所 (1マス25m)", "rule": "番号のつけ方",
                      "calc": "建物: 小屋を中心に北から時計まわりの角度の順、同じ角度なら近い方が先 (作るたびにつけなおす)。墓: 土に入った季節の順 (変えない)",
                      "reading": NOTES["renumber"], "cert": "高い"},
        "ages": {"src": "亡くなった人の年齢", "rule": "R12 (問4)", "calc": NOTES["ages"],
                 "reading": "乳飲み子・子は歯でよく分かる。手伝える子と大人の境目は±2〜3年。大人は1人の幅が10年以上。年寄りは骨では「50くらいより上」まで", "cert": "中くらい"},
        "sex": {"src": "亡くなった人の男女", "rule": "R12 (問4)",
                "calc": "大人と年寄りは骨盤の形で「たぶん」つき (骨盤があれば約95%)。子どもは骨の形では決めない",
                "reading": "【今の調べ方】DNA があれば子どもの男女も分かる", "cert": "中くらい"},
        "modern": {"src": "来かた (よそから来た)・村に来た日と生まれた日・母", "rule": "R12'",
                   "calc": "歯の成分: よそから来た人で、村に来たとき3歳以上 → 子どものころ村の外 (地質のちがう土地) で育った。DNA: 子どもの男女、墓にいる人どうしの母方の血縁 (母と子・きょうだい (母が同じ)・祖母と孫)",
                   "reading": NOTES["dna"] + "。" + NOTES["iso"] + "。" + NOTES["kin_limit"] + "。" + NOTES["kin_degree"], "cert": "中くらい"},
        "tech": {"src": "跡が最初に土に入った季節", "rule": "技術の木 問2 (a)",
                 "calc": "技が出るのは最初の跡が土に入った季節 (技を知った日ではない)。くらべるのは順番で、年数ではない。本物は西アジアでいちばん古い例",
                 "reading": NOTES["tech_rest"], "cert": "中くらい"},
    }

    yrs = DAY // YEAR
    notes = dict(NOTES)
    notes["c14"] = ("放射性炭素の年代では、この村の%d年 (本物のこよみでは約%d年) は1つの年代の幅 (この時代はふつう100〜200年ほど【未確認】) にすっぽり入る。本当は層は1つ" %
                    (yrs, int(DAY / 365 + 0.5)))

    out = {
        "v": 1,
        "built": {"state_day": DAY, "next_event": st.get("next_event"), "record_seasons": meta.get("seasons", len(sv)),
                  "date": dlab(DAY), "season": seasons[-1]["label"], "layer": seasons[-1]["layer"]},
        "notes": notes,
        "layers": layers,
        "seasons": seasons,
        "hut": hut,
        "buildings": buildings,
        "graves": graves_out,
        "bones": {"by_layer": {k: v for k, v in bones_layer.items() if any(v)},
                  "ruk_death_season": {k: ruk_season.get(k, 0) for k in SEAS},
                  "ruk_rows": [[D[i], k] for i, k in ruk_rows]},
        "plants": {"weights": PLANT_W, "rule": how["plants"]["calc"],
                   "by_layer": {L: plant_words(c) for L, c in plants_layer.items()},
                   "all": plant_words(plants_cum)},
        "tech": tech,
        "chronicle": chronicle,
        "how": how,
        "g6": g6,
    }
    return out


def _goat_index(path):
    idx = {}
    try:
        with open(path, encoding="utf-8") as f:
            for l in f:
                if not l.strip():
                    continue
                for g in (json.loads(l).get("goats") or []):
                    if isinstance(g, dict) and "id" in g:
                        idx.setdefault(g["id"], {"born": g.get("born"), "sex": g.get("sex")})
    except OSError:
        pass
    return idx


def build_g6(st, rec, rows, seasons, layer_of_row, row_of_event, ev_by_type, adv):
    """G6 の村の記録 (印 → 数え札 → 封筒 → 粘土の板 → 文字)。G6 に入るまでは空"""
    entered = any(era == "G6" for _, era in adv) or any(r.get("era") == "G6" for r in rec["season_village"])
    ladder = [{"tool": t, "row": None, "label": None, "real": real} for t, real in G6_LADDER]
    out = {"entered": entered, "ladder": ladder, "seals": [], "rows": [], "town": None,
           "token_units": {k: v for k, v in G6_TOKEN.items()}}
    if not entered:
        return out
    D = [r["d"] for r in rows]
    # 印 (家ごとに最初に作った順に 印A・印B…)。家の名前と番号は外に出さない
    seal_of = {}
    for e in ev_by_type.get("印", []):
        h = (e.get("data") or {}).get("household")
        if h and h not in seal_of:
            k = len(seal_of)
            letter = _seal_letter(k)
            glyph = GLYPHS[k % len(GLYPHS)] if k < len(GLYPHS) else "%s-%s" % (FRAMES[(k // len(GLYPHS) - 1) % len(FRAMES)], GLYPHS[k % len(GLYPHS)])
            i = row_of_event(e)
            seal_of[h] = letter
            out["seals"].append({"k": letter, "glyph": glyph, "first_row": D[i] if i is not None else None})
    first_tool = {}
    for e in ev_by_type.get("印", []):
        i = row_of_event(e)
        if i is not None:
            first_tool.setdefault("印", i)
    for e in ev_by_type.get("記録", []):
        t = (e.get("data") or {}).get("tool")
        i = row_of_event(e)
        if t and i is not None:
            first_tool.setdefault(t, i)
    # 文字 (文字の入口): 物のしるしと数のしるしを分けた粘土の板の記録で、量を確かめた最初の季節 (G6 の記録の条件 F4)
    for e in ev_by_type.get("確かめる", []):
        i = row_of_event(e)
        if i is not None and "板の記録" in (e.get("text") or ""):
            first_tool.setdefault("文字", i)
    for l in ladder:
        i = first_tool.get(G6_TOOL_KEY[l["tool"]])
        if i is not None:
            l["row"], l["label"] = D[i], seasons[i]["label"]
    # 季節ごと
    per = collections.defaultdict(lambda: {"sealings": collections.Counter(), "kinds": [], "checked": []})
    name2id = {h["name"]: h["id"] for h in rec["households"]}
    for e in ev_by_type.get("封", []):
        t = e.get("text") or ""
        if "封のかけら" not in t:
            continue
        i = row_of_event(e)
        if i is None:
            continue
        for h, n in re.findall(r"([^\s:：、]+?)の印 (\d+) 回", t):
            per[i]["sealings"][seal_of.get(h, "none")] += int(n)
        for n in re.findall(r"印のない封 (\d+) 回", t):
            per[i]["sealings"]["none"] += int(n)
    for e in ev_by_type.get("記録", []):
        if (e.get("data") or {}).get("tool"):
            continue
        i = row_of_event(e)
        if i is None:
            continue
        how = (e.get("data") or {}).get("how")
        for what, state, done, need in re.findall(r"(村の蓄えへの家ごとの出し入れ|ほかの村との交換と貸し借り|よその家の畑で刈った量) \((全部残せた|途中まで)。(\d+) / (\d+) 個分\)", e.get("text") or ""):
            k = G6_WHAT[what]
            per[i]["kinds"].append({"what": G6_WHAT_SHOW[k], "key": k, "how": how, "done": int(done), "need": int(need), "full": state == "全部残せた"})
    for e in ev_by_type.get("確かめる", []):
        i = row_of_event(e)
        if i is None:
            continue
        m = re.search(r"草の種にして (\d+) つかみ 分", e.get("text") or "")
        if m:
            per[i]["checked"].append({"what": "もめごとの量", "amount": int(m.group(1)), "unit": "つかみ"})
        else:
            per[i]["checked"].append({"what": "返された量", "amount": None, "unit": None})
    sv_by_d = {r["season_end_day"]: r for r in rec["season_village"]}
    sh_by = collections.defaultdict(list)
    for r in rec["season_household"]:
        sh_by[r["season_end_day"]].append(r)
    hh_name = {h["id"]: h["name"] for h in rec["households"]}
    for i, L in enumerate(layer_of_row):
        if L != "G6":
            continue
        d = D[i]
        p = per.get(i) or {"sealings": collections.Counter(), "kinds": [], "checked": []}
        row = {"d": d, "sealings": dict(sorted(p["sealings"].items())), "kinds": p["kinds"], "checked": p["checked"], "tablet": None, "trade": None}
        store = next((k for k in p["kinds"] if k["key"] == "蓄え"), None)
        if store and store["full"]:
            # 村の記録の need = 切り上げ (家ごとの 入れた + 取った (家の畑にまいた村の草の種をふくむ) の合計 ÷ 100 つかみ)
            #                  + 切り上げ (働いた日の合計 ÷ 10 日)  (era2._g6_records と同じ数え方)。
            # village_flow の out は、まいた分をもうふくむ (g5.last_flow)。fields.sown は畑の枚数なので使わない
            fl, wk, keys = [], [], []
            nonce = 0
            for r in sorted(sh_by.get(d, []), key=lambda r: r["household_id"]):
                vf = r.get("village_flow") or {}
                work = rec["work_days"].get((d, r["household_id"]), 0)
                if not (vf.get("in") or vf.get("out") or work):
                    continue
                nm = hh_name.get(r["household_id"])
                k = seal_of.get(nm)
                if k is None:
                    nonce += 1
                    k = "none%d" % nonce
                keys.append(k)
                fl += [(vf.get("in") or 0) / 100, (vf.get("out") or 0) / 100]
                wk.append(work / 10)
            fneed = math.ceil(round(sum(fl), 6)) if fl else 0
            ftok, wtok = _largest_remainder(fl, fneed), _largest_remainder(wk, store["need"] - fneed)
            if keys and ftok is not None and wtok is not None:
                row["tablet"] = [{"seal": k, "in": ftok[2 * j], "out": ftok[2 * j + 1], "work": wtok[j]} for j, k in enumerate(keys)]
        trade = next((k for k in p["kinds"] if k["key"] == "交換"), None)
        moved = ((sv_by_d.get(d) or {}).get("g6") or {}).get("moved") or {}
        if trade and trade["full"] and moved:
            # 記録に残るのは数え札の数だけ (1 個 = 草の種 100 つかみ・ヤギ 1 頭・土器 10 個…。端は 1 個に切り上げ)。本当の量は出さない
            def tok(k, n):
                return -(-int(n) // G6_TOKEN.get(k, 100))
            row["trade"] = {"out": {k: tok(k, v["out"]) for k, v in moved.items() if v.get("out")},
                            "in": {k: tok(k, v["in"]) for k, v in moved.items() if v.get("in")}}
        out["rows"].append(row)
    for e in ev_by_type.get("町", []):
        if "倍をこえた" in (e.get("text") or ""):
            i = row_of_event(e)
            if i is not None:
                out["town"] = {"row": D[i], "label": seasons[i]["label"], "ha": (seasons[i]["pop"] or {}).get("ha")}
            break
    _ = name2id
    return out


def _seal_letter(k):
    A = "ABCDEFGHIJKLMNOPQRSTUVWXYZ"
    return A[k] if k < 26 else A[k // 26 - 1] + A[k % 26]


def _largest_remainder(flat, need):
    """数え札の数 (大きい余りから配って、合計を need に合わせる)。合わせられなければ None。flat が空で need が 0 なら []"""
    base = [int(v) for v in flat]
    rem = need - sum(base)
    if rem < 0 or rem > len(flat):
        return None
    order = sorted(range(len(flat)), key=lambda j: (-(flat[j] - base[j]), j))
    for j in order[:rem]:
        base[j] += 1
    return base


# ---------------------------------------------------------------- 確かめ
FORBIDDEN_KEYS = {"population", "adults", "children", "by_age_class", "by_sex", "kcal", "eaten", "eaten_share", "store",
                  "store_kcal", "wealth", "wealth_kcal", "house_gini", "wealth_gini", "farm_share", "fields", "goats", "pots",
                  "sickles", "died_day", "born_day", "came_day", "age", "age_at_death", "death_cause", "mother_id",
                  "household_id", "person_id", "laws", "disputes", "feeling", "feelings", "said", "shown", "leader_id",
                  "injuries", "votes", "who", "members"}
ALLOW_TERMS = ["テル・セケル・アル・アヘイマル", "ケセム洞窟"]  # 本物の地名 (人の名前と字がかさなる。ケセム洞窟は 31年の子「ケセ」とかさなる)


def _walk(o, path, fn):
    if isinstance(o, dict):
        for k, v in o.items():
            fn(path, k, None)
            _walk(v, path + [k], fn)
    elif isinstance(o, list):
        for j, v in enumerate(o):
            _walk(v, path + [j], fn)
    elif isinstance(o, str):
        fn(path, None, o)


def checks(out, st, rec, prev=None):
    errs, warns = [], []
    names = sorted({p["name"] for p in rec["people"]} | {h["name"] for h in rec["households"]}, key=len, reverse=True)
    idpat = re.compile(r"\b[PH]\d{2,3}\b")

    def scan(path, key, s):
        if key is not None:
            if key in FORBIDDEN_KEYS:
                errs.append("出してはいけないキー: %s (%s)" % (key, "/".join(map(str, path))))
            if key == "name" and not (len(path) >= 2 and path[0] == "chronicle"):
                errs.append("名前のキー: %s" % "/".join(map(str, path)))
            return
        if len(path) >= 3 and path[0] == "chronicle" and path[-1] == "name":
            return
        t = s
        for a in ALLOW_TERMS:
            t = t.replace(a, "")
        # 技術の表の「現実の年代・遺跡」の欄は、こちらで決めた変わらない文 (村の人の名前は入らない)。遺跡の名前に子の名前がかさなる
        # (ケセム洞窟とケセ、ゲシャー・ベノット・ヤアコブとアコ) ので、名前の確かめはしない (2026-10-10)
        static = len(path) >= 3 and path[0] == "tech" and path[-1] in ("real", "real_place", "also")
        for n in ([] if static else names):
            if n in t:
                errs.append("名前がもれている: %s (%s)" % (n, "/".join(map(str, path))))
                break
        if idpat.search(t):
            errs.append("番号がもれている: %s" % "/".join(map(str, path)))
        if "kcal" in t or "持ち主の印" in t:
            errs.append("出してはいけない言葉: %s" % "/".join(map(str, path)))
        if path and path[0] in ("seasons", "graves", "buildings", "tech"):
            t2 = t.replace("乳飲み子", "")
            if "祭り" in t2 or "乳" in t2:
                errs.append("祭り・乳が跡の文に出ている: %s" % "/".join(map(str, path)))
    _walk(out, [], scan)

    S = out["seasons"]
    last = S[-1]["cum"]
    tot = collections.Counter()
    for sz in S:
        a = sz["add"]
        tot["sherds"] += a["sherds"] or 0
        tot["blades"] += a["blades"] or 0
        tot["graves"] += len(a["graves"])
        tot["houses"] += len(a["houses"])
        tot["hut"] += a["hut"]
        for k in range(3):
            tot["b%d" % k] += a["bones"][k]
    for k in ("sherds", "blades", "graves", "houses", "hut"):
        if tot[k] != last[k]:
            errs.append("合計が合わない: %s (足した数 %s・たまった数 %s)" % (k, tot[k], last[k]))
    if [tot["b0"], tot["b1"], tot["b2"]] != last["bones"]:
        errs.append("骨の合計が合わない")
    sv = rec["season_village"]
    pb = sum((r.get("pots_broken") or 0) for r in sv)
    if pb != last["sherds"]:
        errs.append("土器のかけら %s と割れた土器の合計 %s が合わない" % (last["sherds"], pb))
    if not out["g6"]["entered"] and sv:
        made = sum((r.get("pots_made") or 0) for r in sv)
        if made - pb != (sv[-1].get("pots") or 0):
            warns.append("土器: 作った %s − 割れた %s が いまの数 %s と合わない" % (made, pb, sv[-1].get("pots")))
        smade = sum((r.get("sickles_made") or 0) for r in sv)
        sb = sum((r.get("sickles_broken") or 0) for r in sv)
        if smade - sb != (sv[-1].get("sickles") or 0):
            warns.append("鎌: 作った %s − 割れた %s が いまの数 %s と合わない" % (smade, sb, sv[-1].get("sickles")))
    ndead = sum(1 for p in rec["people"] if p.get("died_day") is not None and p["died_day"] <= st["day"])
    G = out["graves"]
    if len(G) != ndead:
        errs.append("墓の数 %d と亡くなった人 %d が合わない" % (len(G), ndead))
    if last["graves_floor"] + last["graves_centre"] != last["graves"]:
        errs.append("床下 + まん中 が墓の数と合わない")
    if any(("building" in g["place"]) == ("centre" in g["place"]) for g in G):
        errs.append("場所の決まらない墓がある")
    if [g["no"] for g in G] != list(range(1, len(G) + 1)):
        errs.append("墓の番号が 1 から続いていない")
    for sz, r in zip(S[-len(sv):] if sv else [], sv):
        f = ((r.get("g5") or {}).get("feast") or {})
        if f.get("held") and not any(k in MEAT for k in (f.get("cost") or {})) and sz["add"]["feast_bones"]:
            errs.append("肉のない祭りで跡が出ている: %s" % sz["label"])
    if out["g6"]["entered"]:
        g6v = (sv[-1].get("g6") or {}) if sv else {}
        if g6v.get("seals") is not None and isinstance(g6v.get("seals"), int) and g6v["seals"] != len(out["g6"]["seals"]):
            errs.append("印の数が合わない (出来事 %d・記録 %s)" % (len(out["g6"]["seals"]), g6v.get("seals")))
        tot_seal = sum(sum(r["sealings"].values()) for r in out["g6"]["rows"])
        if isinstance(g6v.get("sealings_total"), int) and g6v["sealings_total"] != tot_seal:
            warns.append("封のかけらの合計が合わない (出来事 %d・記録 %s)" % (tot_seal, g6v.get("sealings_total")))
    if prev:
        def norm(a):  # 建物の番号はつけなおすことがあるので、数だけくらべる
            return {k: (len(v) if isinstance(v, list) and k != "bones" else v) for k, v in (a or {}).items()}
        old = {sz["d"]: sz for sz in prev.get("seasons", [])}
        changed = [sz["label"] for sz in S[:-1] if sz["d"] in old and norm(old[sz["d"]].get("add")) != norm(sz["add"])]
        if changed:
            warns.append("前に作ったときと、古い季節の行がちがう: %s" % "・".join(changed[:6]))
    return errs, warns


def dump(out):
    return json.dumps(out, ensure_ascii=False, sort_keys=True, separators=(",", ":")) + "\n"


MARK_A, MARK_B = "<!--DASH-DATA-->", "<!--/DASH-DATA-->"


def embed_text(html, js):
    a, b = html.find(MARK_A), html.find(MARK_B)
    if a < 0 or b < a:
        raise ValueError("html に %s と %s がない" % (MARK_A, MARK_B))
    nl = "\r\n" if "\r\n" in html else "\n"
    body = js.rstrip("\n").replace("</", "<\\/")
    block = MARK_A + nl + '<script type="application/json" id="dash-data">' + body + "</script>" + nl
    return html[:a] + block + html[b:]


def _under(path, root):
    p, r = os.path.normcase(os.path.realpath(path)), os.path.normcase(os.path.realpath(root))
    return p == r or p.startswith(r + os.sep)


def main(argv=None):
    ap = argparse.ArgumentParser(description="ダッシュボード「村の跡と記録」の JSON を作る (読むだけ)")
    ap.add_argument("--data", default=DEFAULT_DATA)
    ap.add_argument("--out", default=DEFAULT_OUT)
    ap.add_argument("--embed", default=None)
    ap.add_argument("--allow-data", action="store_true")
    ap.add_argument("--check", action="store_true")
    a = ap.parse_args(argv)
    t0 = time.time()
    if a.out and _under(a.out, PROTECTED) and not a.allow_data:
        print("止めた: %s は sim/society/data/ の下 (--allow-data がないと書かない)" % a.out, file=sys.stderr)
        return 2
    if a.embed and _under(a.embed, PROTECTED) and not a.allow_data:
        print("止めた: %s は sim/society/data/ の下" % a.embed, file=sys.stderr)
        return 2
    try:
        st, rec = load(a.data)
    except GateError as e:
        print("止めた: %s" % e, file=sys.stderr)
        return 3
    rec["_dir"] = a.data
    out = build(st, rec)
    prev = None
    if a.out and os.path.exists(a.out):
        try:
            prev = _read_json(a.out)
        except (ValueError, OSError):
            prev = None
    errs, warns = checks(out, st, rec, prev)
    js = dump(out)
    size = len(js.encode("utf-8"))
    if size > 300 * 1024:
        errs.append("大きすぎる: %d バイト (300 KB まで)" % size)
    elif size > 150 * 1024:
        warns.append("大きい: %d バイト (150 KB をこえた)" % size)
    for w in warns:
        print("知らせ: " + w, file=sys.stderr)
    if errs:
        for e in errs:
            print("だめ: " + e, file=sys.stderr)
        return 1
    S = out["seasons"]
    c = S[-1]["cum"]
    p = S[-1]["pop"] or {}
    summary = ("%s (%s・%s層) まで %d 季節 | 建物 %d (家 %d・土台 %d) + 小屋 %d | かけら %s・刃 %s | 墓 %d (床下 %d・まん中 %d) | 人数 %s〜%s (丸める前 %s〜%s) | %d バイト | %.1f 秒"
               % (out["built"]["date"], out["built"]["season"], out["built"]["layer"], len(S), len(out["buildings"]), c["houses"], c["footings"],
                  c["hut"], fmt(c["sherds"]), fmt(c["blades"]), c["graves"], c["graves_floor"], c["graves_centre"], p.get("lo"), p.get("hi"),
                  p.get("lo_raw"), p.get("hi_raw"), size, time.time() - t0))
    if a.check:
        bad = False
        if a.out:
            try:
                with open(a.out, encoding="utf-8", newline="") as f:
                    old = f.read()
            except OSError:
                old = None
            if old != js:
                print("ちがう: %s は作りなおした JSON とちがう" % a.out, file=sys.stderr)
                bad = True
        if a.embed:
            with open(a.embed, encoding="utf-8", newline="") as f:
                html = f.read()
            if embed_text(html, js) != html:
                print("ちがう: %s に埋めた JSON は作りなおしたものとちがう" % a.embed, file=sys.stderr)
                bad = True
        print(("確かめ: ちがいあり | " if bad else "確かめ: 同じ | ") + summary)
        return 4 if bad else 0
    if a.out:
        os.makedirs(os.path.dirname(os.path.abspath(a.out)), exist_ok=True)
        with open(a.out, "w", encoding="utf-8", newline="") as f:
            f.write(js)
    if a.embed:
        with open(a.embed, encoding="utf-8", newline="") as f:
            html = f.read()
        new = embed_text(html, js)
        if new != html:
            with open(a.embed, "w", encoding="utf-8", newline="") as f:
                f.write(new)
    print(summary)
    return 0


if __name__ == "__main__":
    sys.exit(main())
