"""G9「遠くとの商い」の動画の数を、村の記録から読む (読むだけ。data には書かない)。
   python3 data.py <出力 facts.json>
   読むもの: sim/society/data/records/ (season_village・disputes・year_names・polity・laws)、
   data/archive/events_0104〜0119.jsonl (しまった出来事)、state.json の era2.g7.g9・closed9・hints、
   answers/day*/ (季節の答えと models.json)。
   lines.json の文に書いた数は、下の CHECK で記録と合うか確かめる (合わないと止まる)。
   G9 は 104年120日目 (12599) に入り 118年120日目 (14279) に閉じたので、その間だけを読む。"""
import collections
import json
import os
import re
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
SOC = HERE.parent.parent
DATA = SOC / "data"
REC = DATA / "records"
START, END = 12599, 14279
Y = lambda d: d // 120  # noqa: E731  村の年 (1 年 120 日。d = 120*年 + 日目-1)
out = Path(sys.argv[1])

sv_all = [json.loads(l) for l in open(REC / "season_village.jsonl", encoding="utf-8")]
by_day = {x["season_end_day"]: x for x in sv_all}
sv = [x for x in sv_all if START < x["season_end_day"] <= END]  # G9 の 56 季節
ev = []
for y in range(Y(START), Y(END) + 2):
    f = DATA / "archive" / f"events_{y:04d}.jsonl"
    if f.exists():
        ev += [e for e in (json.loads(l) for l in open(f, encoding="utf-8")) if START <= e["day"] <= END]
st = json.load(open(DATA / "state.json", encoding="utf-8"))
g7 = st["era2"]["g7"]
g9, c9 = g7["g9"], g7["closed9"]
visits = [v for v in g9["visits"] if v["day"] <= END]
offers = {o["id"]: o for o in g9["offer_log"]}
tools = [t for t in g9["tools"] if t["day"] <= END]
used = {int(k): v for k, v in c9["used"].items()}
tools_end = {y: sum(1 for t in tools if t["day"] <= 120 * y + 119 and (t.get("gone") is None or t["gone"] > 120 * y + 119))
             for y in range(105, 119)}

# 季節ごとの列 (図に使う)
seasons = [{"day": x["season_end_day"], "year": x["year"], "label": x["label"], "pop": x["population"],
            "store_days": x["store_days"], "harvested": x["fields"]["harvested"] or 0, "fallen": x["fields"]["fallen"] or 0}
           for x in [by_day[START]] + sv]
harvest = collections.Counter(); fallen = collections.Counter()
for s in seasons[1:]:
    harvest[s["year"]] += s["harvested"]; fallen[s["year"]] += s["fallen"]

# 出来事
T = lambda ty, *ws: [e for e in ev if e["type"] == ty and all(w in e["text"] for w in ws)]  # noqa: E731
far_offer = T("よその村", "遠くの町から来た運ぶ人は")
trades = T("交換", "遠くの町から来た運ぶ人の申し出")
near_offers = [e for e in T("よその村", "また村に来た", "ヤギ") if "がほしいと言った" in e["text"]]
near_ids = [re.search(r"\[(T\d+)\]", e["text"]).group(1) for e in near_offers]
near_no = [e for e in T("よその村", "は受けなかった") if any(f"[{i}]" in e["text"] for i in near_ids)]
shie = T("よその村", "シエ12の村", "交換できる物がなく")
zaga = T("死", "ザガ")
lend = T("貸し借り", "草の種 2300 つかみ を貸した")
back = T("覚え", "2058 つかみ")
left = T("分かれる", "シエ12の家")
go_trade = T("交換に行く")

# 運ぶ人の 9 回 (表)
rows = []
for v in visits:
    o = offers[v["offer"]]
    vote = next((e["text"] for e in ev if f"[{v['offer']}]" in e["text"] and ("受け、" in e["text"] or "受けなかった" in e["text"])), "")
    rows.append({"day": v["day"], "date": f"{Y(v['day'])}年{v['day'] % 120 + 1}日目", "id": v["offer"],
                 "end": f"{Y(o['end'][0])}年{o['end'][0] % 120 + 1}日目", "answer": o["end"][1],
                 "votes": vote[vote.rfind("(") + 1:vote.rfind(")")] if vote else ""})

# 代表の季節の答え
n_ans = collections.Counter(); far = collections.Counter(); metal = collections.Counter(); prop = 0
for d in os.listdir(DATA / "answers"):
    day = int(d[3:])
    sd = DATA / "answers" / d / "season"
    if not (START <= day <= END) or not sd.is_dir():
        continue
    m = json.load(open(DATA / "answers" / d / "models.json", encoding="utf-8"))["season"]
    for f in os.listdir(sd):
        a = json.load(open(sd / f, encoding="utf-8")); mod = m[f[:-5]]
        n_ans[mod] += 1
        for x in (a.get("far") or {}).values():
            far[x] += 1
        if a.get("metal"):
            metal[str(a["metal"])] += 1
        prop += bool(a.get("proposal"))
nase = json.load(open(DATA / "answers" / "day12599" / "season" / "ナセ20.json", encoding="utf-8"))

# よその便り (運ぶ人が話していった札)
cards = {}
for f in ("hint_cards.json", "hint_cards_g9.json"):
    d = json.load(open(SOC / f, encoding="utf-8"))
    for c in (d if isinstance(d, list) else d.get("cards", [])):
        if isinstance(c, dict):
            cards[c["id"]] = c["name"]
hint_ids = {v["hint"] for v in visits}
hints = [dict(r, name=cards.get(r["card"])) for r in g7["hints"]["ledger"] if r["y"] in hint_ids]

# 人・もめごと・掟・年の名前・北の大きな村
deaths = collections.Counter(d["cause"] for x in sv for d in x["deaths"])
disp = [r for r in json.load(open(REC / "disputes.json", encoding="utf-8")) if START < r["day"] <= END]
laws = json.load(open(REC / "laws.json", encoding="utf-8"))
props_g9 = [l for l in laws if l.get("proposed_day") and START <= l["proposed_day"] <= END]
names = {r["year"]: r["name"] for r in json.load(open(REC / "year_names.json", encoding="utf-8")) if 105 <= r["year"] <= 118}
pol = {p["season_end_day"]: p for p in (json.loads(l) for l in open(REC / "polity.jsonl", encoding="utf-8"))}
n83 = lambda d: next(s["people"] for s in pol[d]["settlements"] if s["id"] == "N83")  # noqa: E731
fs = by_day[START]; ls = by_day[END]

F = {"seasons": seasons, "used": used, "tools_end": tools_end, "harvest": harvest, "fallen": fallen, "rows": rows,
     "names": names, "hints": [{"date": f"{Y(h['delivered'])}年{h['delivered'] % 120 + 1}日目", "name": h["name"], "status": h["status"],
                                                                                               "kept": [o[2] for o in h["outcome"] if o[0] == "覚えた"]} for h in hints]}

CHECK = [
    ("期間 104年120日目〜118年120日目・56 季節", Y(START) == 104 and START % 120 + 1 == 120 and Y(END) == 118 and END % 120 + 1 == 120 and len(sv) == 56),
    ("閉じた: 本人の決め・c1 届き・F1 13319・約束 0・商人の家 0", c9["day"] == END and c9["c"] == {"c1": 12629} and c9["f1"] == 13319 and c9["promises"] == 0 and c9["merchant_max"] == 0),
    ("入った日 139 人・蓄え 7.7 万つかみ・23 日分", fs["population"] == 139 and round(fs["store"]["草の種"] / 1000) == 77 and fs["store_days"] == 23),
    ("ナセ20 (opus) 「しまってある赤い金属の刃も出して使おう」・使う", "しまってある赤い金属の刃も出して使おう" in nase["say"][0]["text"] and nase["metal"] == "使う"
     and json.load(open(DATA / "answers/day12599/models.json"))["season"]["ナセ20"] == "opus"),
    ("刃は 67年のもの 1 つ (B1)", tools[0]["id"] == "B1" and Y(tools[0]["day"]) == 67 and tools_end[105] == 1),
    ("c1 は 105年30日目、この年 30 人日", c9["c1"] == 12629 and Y(12629) == 105 and 12629 % 120 + 1 == 30 and used[105] == 30),
    ("105〜108年 運ぶ人 0・108年の刈り入れ 16.8 万", all(Y(v["day"]) > 108 for v in visits) and round(harvest[108] / 1000) == 168),
    ("見込み 0.1 → 0.5 (108年120日目、本人の決め)", g9["far_rate"][0]["day"] == 13079 and g9["far_rate"][0]["was"] == 0.1 and g9["far_rate"][0]["rate"] == 0.5
     and Y(13079) == 108 and 13079 % 120 + 1 == 120),
    ("はじめての運ぶ人 110年60日目・鎌 2 本と草の種 1600", visits[0]["day"] == 13259 and 13259 % 120 + 1 == 60 and offers["M1"]["give"] == {"赤い金属の鎌": 2}
     and offers["M1"]["want"] == {"草の種": 1600} and "次の村の集まりまで待つ" in far_offer[0]["text"]),
    ("M1 110年120日目 受ける 40・受けない 35", rows[0]["end"] == "110年120日目" and rows[0]["votes"].startswith("受ける 40・受けない 35")),
    ("運ぶ人 9 回・替え 6・受けない 3", len(visits) == 9 == c9["visits"] and len(trades) == 6 == c9["deals"] and sum(r["answer"] == "受けない" for r in rows) == 3),
    ("「約束する」0 / 104 の答え", far.get("約束する", 0) == 0 and sum(far.values()) == 104 and n_ans == {"sonnet": 300, "opus": 80}),
    ("替えた 6 回で草の種 9600・鎌 12 本、蓄えの 0.5% ほど", sum(offers[r["id"]]["want"]["草の種"] for r in rows if r["answer"] == "受ける") == 9600
     and sum(offers[r["id"]]["give"]["赤い金属の鎌"] for r in rows if r["answer"] == "受ける") == 12 and 0.004 < 9600 / ls["store"]["草の種"] < 0.006),
    ("118年 道具 13・351 人日・使うだけ (しまう 0)", tools_end[118] == 13 == c9["tools"] and used[118] == 351 and "しまう" not in metal and c9["use"] == "使う"),
    ("交換に出かけた日 0 (G9)・最後は 44年", not go_trade and c9["merchant_max"] == 0),
    ("近くの村の交換の申し出 7・みな受けない", len(near_offers) == 7 and len(near_no) == 7 and not T("交換", "[T")),
    ("よその便り: 運ぶ人 9 通、値を知らせる粘土の手紙 3 回 みな忘れ、覚えたのは配給の名簿だけ",
     len(hints) == 9 and [h["status"] for h in hints if h["name"] == "値を知らせる粘土の手紙"] == ["忘れられた"] * 3
     and [h["name"] for h in hints if h["status"] != "忘れられた"] == ["配給の名簿"]
     and [o[2] for h in hints for o in h["outcome"] if o[0] == "覚えた"] == ["ルタ24"]),
    ("113年 シエ12の家の 5 人が出た・シエ12の村 8 回", len(left) == 1 and Y(left[0]["day"]) == 113 and len(by_day[left[0]["day"]]["left"]) == 5 and len(shie) == 8),
    ("116年 南東の村に 2300 貸し、117年に 2058 返った", len(lend) == 1 and Y(lend[0]["day"]) == 116 and "南東の村" in lend[0]["text"] and len(back) == 1 and Y(back[0]["day"]) == 117),
    ("ザガ: 116年75日目 ホミ13・118年 ケナ24", [(Y(e["day"]), e["day"] % 120 + 1) for e in zaga] == [(116, 75), (118, 36)] and "ホミ13" in zaga[0]["text"] and "ケナ24" in zaga[1]["text"]),
    ("人 139 → 194・生まれ 128・亡くなり 92・加わり 24・ききん 0", ls["population"] == 194 and sum(len(x["births"]) for x in sv) == 128
     and sum(deaths.values()) == 92 and sum(len(x["joined"]) for x in sv) == 24 and min(x["store_days"] for x in sv) > 0),
    ("刈り入れ 111年から 59〜76 万", all(590000 <= harvest[y] < 770000 for y in range(111, 119)) and round(harvest[117] / 10000) == 59 and round(harvest[118] / 10000) == 76),
    ("蓄え 23 日分 → 457 日分", fs["store_days"] == 23 and ls["store_days"] == 457),
    ("刈らずに落ちた 112年・116年 約 35 万", round(fallen[112] / 10000) == 35 and round(fallen[116] / 10000) == 35 and sorted(y for y in fallen if fallen[y] > 300000) == [112, 116]),
    ("年の名前 5 つが ヤギがやせ・運ぶ人・赤い金属の名前 0", sum("ヤギが" in n and "やせ" in n for n in names.values()) == 5
     and not any(w in n for n in names.values() for w in ("運ぶ", "赤い", "金属", "ザガ"))),
    ("案 67 本 (opus)・採用 0・もめごと 38 のうち ゆるす 37", prop == 67 and len(props_g9) == 67 and not any(l.get("adopted_day") for l in props_g9)
     and len(disp) == 38 and sum(r["verdict"] == "ゆるす" for r in disp) == 37),
    ("鎌 2 本の値 1600 は、運ぶ人が来た日の蓄えの 1% より小さい", all(1600 < 0.01 * by_day[max(d for d in by_day if d <= v["day"])]["store"]["草の種"] for v in visits)),
    ("村を出た 5 人のうち子 2", left and left[0]["text"].count("(子)") == 2),
    ("北の大きな村 89 → 57 人", n83(START) == 89 and n83(END) == 57),
]
bad = [n for n, ok in CHECK if not ok]
for n, ok in CHECK:
    print(("OK  " if ok else "NG  ") + n)
if bad:
    sys.exit("記録と合わない文がある: " + " / ".join(bad))
out.write_text(json.dumps(F, ensure_ascii=False), encoding="utf-8")
print("facts:", out)
