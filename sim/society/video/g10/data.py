"""G10「鉄と広い国」の動画の数を、村の記録から読む (読むだけ。data には書かない)。
   python3 data.py <出力 facts.json>
   読むもの: sim/society/data/records/ (season_village・people・year_names・laws・disputes)、
   data/archive/events_0118〜.jsonl と state.json の events (しまう前の出来事)、state.json の era2.g7.g10・closed10・g9・region.log、
   sim/society/reports/year119〜150.html (年報。トークンと「字で比べた回数」)。
   lines.json の文に書いた数は、下の CHECK で記録と合うか確かめる (合わないと止まる)。
   G10 は 118年120日目 (14279) に入り 150年120日目 (18119) に閉じたので、その間だけを読む。年は 年 = 日 // 120 (年報と同じ。150年 = 18000〜18119 日目)。"""
import collections
import json
import math
import re
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
SOC = HERE.parent.parent
DATA = SOC / "data"
REC = DATA / "records"
START, END = 14279, 18119
Y = lambda d: d // 120  # noqa: E731
YD = lambda d: f"{d // 120}年{d % 120 + 1}日目"  # noqa: E731
YE = lambda y: 120 * y + 119  # noqa: E731  その年の終わりの日
YS = list(range(119, 151))
out = Path(sys.argv[1])

sv_all = [json.loads(l) for l in open(REC / "season_village.jsonl", encoding="utf-8")]
by_day = {x["season_end_day"]: x for x in sv_all}
sv = [x for x in sv_all if START < x["season_end_day"] <= END]
st = json.load(open(DATA / "state.json", encoding="utf-8"))
g7 = st["era2"]["g7"]
g10, c10 = g7["g10"], g7["closed10"]
P = {p["name"]: p for p in json.load(open(REC / "people.json", encoding="utf-8"))}

ev, seen = [], set()
for y in range(Y(START), Y(END) + 1):
    f = DATA / "archive" / f"events_{y:04d}.jsonl"
    if f.exists():
        for e in (json.loads(l) for l in open(f, encoding="utf-8")):
            if START <= e["day"] <= END and e["id"] not in seen:
                seen.add(e["id"]); ev.append(e)
for e in st["events"]:
    if START <= e["day"] <= END and e["id"] not in seen:
        seen.add(e["id"]); ev.append(e)
T = lambda ty, *ws: [e for e in ev if e["type"] == ty and all(w in e["text"] for w in ws)]  # noqa: E731

# 季節ごとの人 (図)
seasons = [{"day": x["season_end_day"], "pop": x["population"], "store_days": x["store_days"]} for x in [by_day[START]] + sv]
fs, ls = by_day[START], by_day[END]

# 刈り入れの人日 (黒い金属・赤い金属・ほか)
reap = {int(k): v for k, v in c10["reap"].items()}
share = {y: reap[y]["iron"] / reap[y]["all"] for y in YS}
# 黒い金属の鎌 (年ごと) と作った人
made = collections.Counter(Y(m["day"]) for m in g10["made"] if m["day"] <= END)
smith_y = collections.defaultdict(set)
for e in ev:
    if e["type"] == "黒い金属を作る":
        smith_y[Y(e["day"])].add(e["who"])
smith_y = {y: sorted(v) for y, v in smith_y.items()}
forge_days = sum(1 for e in ev if e["type"] == "黒い金属を作る")
# 読み書きできる大人 (年の終わり)
dead = lambda n, d: P[n]["died_day"] is not None and P[n]["died_day"] <= d  # noqa: E731
readers = {y: sum(1 for n, d in g10["readers"].items() if d <= YE(y) and not dead(n, YE(y))) for y in YS}
learn146 = sorted(n for n, d in g10["readers"].items() if Y(d) == 146)
ages146 = [Y(g10["readers"][n] - P[n]["born_day"]) for n in learn146]
# いちばん大きなまとまり (年の終わりの「段」の記録)
lg = g7["region"]["log"]
polity = {}
for y in [118] + YS:
    lv = [x for x in lg if x["kind"] == "段" and x["day"] == YE(y)][0]["levels"]
    top = max(lv, key=lambda v: (v["D"], v["n"]))
    n_all = by_day[YE(y)]["g7"]["settlements"] + 1  # 村もふくむ
    polity[y] = {"top": top["top"], "D": top["D"], "n": top["n"], "need": math.ceil(n_all / 2), "all": n_all,
                 "n83": next((v["n"] for v in lv if v["top"] == "N83"), 0)}
pol_end = next(r for r in (json.loads(l) for l in open(REC / "polity.jsonl", encoding="utf-8")) if r["season_end_day"] == END)
dem = [x for x in lg if x["kind"] == "求め" and START <= x["day"] <= END]
# 遠くの運ぶ人
visits = [v for v in g7["g9"]["visits"] if START < v["day"] <= END]
offers = {o["id"]: o for o in g7["g9"]["offer_log"]}
bronze = [t for t in g7["g9"]["tools"] if not t.get("iron")]
# 貸し借り
loans = T("貸し借り", "季節の集まりで、村は、村の物で")
loans_int = [e for e in loans if "上乗せ" in e["text"]]
checks = sorted((e for e in ev if "字で" in e["text"] and e["type"] in ("確かめる", "もめごと")), key=lambda e: e["day"])
# 人・村の中
deaths = collections.Counter(d["cause"] for x in sv for d in x["deaths"])
left = T("分かれる", "ワユ3の家")
names = {r["year"]: r["name"] for r in json.load(open(REC / "year_names.json", encoding="utf-8")) if 119 <= r["year"] <= 150 and r["name"]}
iron_names = {y: n for y, n in names.items() if "黒い" in n}
laws = json.load(open(REC / "laws.json", encoding="utf-8"))
props = [l for l in laws if l.get("proposed_day") and START <= l["proposed_day"] < END]  # END の日の集まりは G11 のもの
adopted = [l for l in laws if l.get("adopted_day") and START <= l["adopted_day"] < END]
disp = [r for r in json.load(open(REC / "disputes.json", encoding="utf-8")) if START < r["day"] <= END]
mark = {e["text"].split("「")[1].split("」")[0] if "「" in e["text"] else e["text"]: e["day"] for e in T("目盛り", "G10")}
tok = {}
for y in YS:
    t = (SOC / "reports" / f"year{y}.html").read_text(encoding="utf-8")
    tok[y] = int(re.search(r"使ったトークン: 約 [^(]*\(([\d,]+)\)", t).group(1).replace(",", ""))
rep150 = re.sub(r"<[^>]+>", " ", (SOC / "reports" / "year150.html").read_text(encoding="utf-8"))
phase = [e["text"] for e in T("フェーズ") if e["day"] == END]

F = {"seasons": seasons, "reap": reap, "share": share, "made": made, "smith_y": smith_y, "readers": readers, "polity": polity,
     "iron_names": iron_names, "names": names, "start": START, "end": END,
     "goals": [["条件 1", "黒い金属の道具で、刈り入れの半分以上", YD(c10["c"]["c1"]), f"150年 {round(100 * share[150])}%"],
               ["条件 2", "記録の家の外に、読める大人 2 人以上", YD(c10["c"]["c2"]), f"閉じた日 読める大人 {len(c10['readers_alive'])} 人"],
               ["条件 3", "段 4 以上・地域の集落の半分以上", None, f"段 {polity[150]['D']}・{polity[150]['n']} / {polity[150]['need']} 集落"],
               ["F1", "黒い金属を村で作った", YD(c10["reached"]["F1"]), f"鎌 {c10['made']} 本"],
               ["F2", "音の字ができた", YD(c10["reached"]["F2"]), ""],
               ["F3", "広いまとまり (= 条件 3)", None, ""],
               ["F4", "黒い金属の道具が 1 年に 30 人日", YD(c10["reached"]["F4"]), ""]]}

CHECK = [
    ("期間 118年120日目〜150年120日目・32 年・128 季節", YD(START) == "118年120日目" and YD(END) == "150年120日目" and len(sv) == 128
     and int(g10["start"]) == START and any("第 6 部「鉄とお金の帝国」を始めた: フェーズ G10" in e["text"] for e in T("フェーズ"))),
    ("閉じた: 本人の決め・閉じる文・c1 17069 (142年30日目)・c2 16619 (138年60日目)",
     c10["day"] == END and c10["by"] == "本人の決め" and "鉄と広い国を 150年120日目で閉じた。c1・c2 は届き、c3 は 32 年届かなかった" in c10["note"]
     and c10["c"] == {"c2": 16619, "c1": 17069} and YD(17069) == "142年30日目" and YD(16619) == "138年60日目"
     and any("G10 (鉄と広い国): 3 つの条件はそろわないまま" in t for t in phase)),
    ("F1 127年50日目・F4 128年30日目・F2 138年60日目・F3 なし", c10["reached"] == {"F1": 15289, "F4": 15389, "F2": 16619}
     and YD(15289) == "127年50日目" and YD(15389) == "128年30日目"),
    ("入った日 194 人・蓄え 201 万つかみ = 457 日分・赤い金属の道具 13", fs["population"] == 194 and round(fs["store"]["草の種"] / 1e4) == 201
     and fs["store_days"] == 457 and len(bronze) == 13),
    ("ケセ19 が 119・125・126年に試し、126年90日目に作れるようになった",
     sorted({Y(e["day"]) for e in T("試す", "ケセ19", "黒い金属") if "を試した" in e["text"]}) == [119, 125, 126]
     and [YD(e["day"]) for e in T("試す", "赤土からとる黒い金属」ができるようになった")] == ["126年90日目"]),
    ("127年に鎌 3 本・128〜133年は 0 本", made[127] == 3 and all(made[y] == 0 for y in range(128, 134))),
    ("止まりの直し 133年120日目 (16079)", [YD(e["day"]) for e in T("区切り", "お題を書き直した")] == ["133年120日目"]),
    ("鎌は 138 本 (作る 2760 人日 = 20 人日で 1 本)", len(g10["made"]) == 138 == c10["made"] and forge_days == 2760 == 20 * 138),
    ("作った人: 127・134年 ケセ19 / 135〜143年 + タユ25 / 144〜150年 + ロワ33",
     smith_y[127] == ["ケセ19"] and smith_y[134] == ["ケセ19"] and all(smith_y[y] == ["ケセ19", "タユ25"] for y in range(135, 144))
     and all(smith_y[y] == ["ケセ19", "ロワ33"] for y in range(144, 151)) and Y(P["タユ25"]["died_day"]) == 143),
    ("142年 刈った 1914 人日のうち 黒い金属 1298", reap[142]["all"] == 1914 and reap[142]["iron"] == 1298),
    ("150年 2520 のうち 2277 (90%)・いちばん高い年", reap[150] == {"all": 2520, "bronze": 0, "iron": 2277} and round(100 * share[150]) == 90
     and max(share, key=share.get) == 150 and abs(c10["iron_share_best"] - share[150]) < 1e-3),
    ("141年まで半分に届かない", all(share[y] < 0.5 for y in range(119, 142)) and share[142] >= 0.5),
    ("赤い金属の道具 13 は 145年までにみなすり減った・146年から赤い金属で刈った人日 0",
     all(t.get("gone") and Y(t["gone"]) <= 145 for t in bronze) and all(reap[y]["bronze"] == 0 for y in range(146, 151))),
    ("遠くの運ぶ人 9 回・みな受けない", len(visits) == 9 and all(offers[v["offer"]]["end"][1] == "受けない" for v in visits) and not T("交換")),
    ("年の名前: 黒い金属・黒い鎌 6 つ (126・134・137・138・141・143)", sorted(iron_names) == [126, 134, 137, 138, 141, 143]),
    ("音の字: ムイ21 が 136年に試し始め、138年60日目に 5 人", min(Y(e["day"]) for e in T("試す", "音 1 つに字 1 つ") if "を試した" in e["text"]) == 136
     and T("試す", "ムイ21", "音 1 つに字 1 つ")[0]["day"] // 120 == 136 and sum(1 for d in g10["readers"].values() if d == 16619) == 5
     and readers[138] == 5),
    ("読める大人: 141年 3・145年 2・146年 12・閉じた日 9 (亡くなった 6)", readers[141] == 3 and readers[145] == 2 and readers[146] == 12
     and readers[150] == 9 == len(c10["readers_alive"]) and len(c10["readers_dead"]) == 6),
    ("146年 若い人 10 人が字を習って読めるようになった (16〜29 歳)", len(learn146) == 10 and min(ages146) == 16 and max(ages146) == 29 and len(T("字を習う")) == 310),
    ("字で量を比べた 10 回 (返しの確かめ 7・もめごと 3)", len(checks) == 10 == c10["letters"] and "字で書いて量を比べた回数 (はじめから): 10 回" in rep150
     and sum(e["type"] == "確かめる" for e in checks) == 7),
    ("貸し: 上乗せ (1〜2 割) をつけたのは 133〜138年の 7 回、最初は 133年30日目",
     len(loans_int) == 7 and YD(loans_int[0]["day"]) == "133年30日目" and Y(loans_int[-1]["day"]) == 138
     and sum("上乗せ 2 割" in e["text"] for e in loans_int) == 1 and len(loans) == 15 and Y(loans[0]["day"]) == 121),
    ("124年 ワユ3の家 36 人が村を出た", len(left) == 1 and Y(left[0]["day"]) == 124 and len(by_day[left[0]["day"]]["left"]) == 36
     and sum(len(x["left"]) for x in sv) == 36),
    ("c3: いちばん大きなまとまりは 32 年ずっと段 3 以下", all(polity[y]["D"] <= 3 for y in YS) and polity[150]["D"] == 3),
    ("N83 は 119〜131年 13〜16 集落 (要るのは 12) → 閉じた日 8 / 11", all(13 <= polity[y]["n83"] <= 16 and polity[y]["need"] == 12 for y in range(119, 132))
     and polity[150]["top"] == "N83" and polity[150]["n"] == 8 == c10["region"]["members"] and polity[150]["need"] == 11
     and polity[150]["all"] == 21 == c10["region"]["settlements"]),
    ("N83 は 137〜140年ごろ 5〜6 集落にちぢんだ", min(polity[y]["n83"] for y in YS) == 5),
    ("130〜135年 地域の悪い年 6 年続き、貢ぎが 25 切れた (払えなかった)", all(w["region_bad"] for w in g7["region"]["weather_log"] if Y(w["day"]) in range(130, 136))
     and sum(1 for x in lg if x["kind"] == "崩れ" and Y(x["day"]) in range(130, 136) and START <= x["day"] <= END) == 25),
    ("閉じた日、村は地域でいちばん大きい", all(s["people"] < ls["population"] for s in pol_end["settlements"] if s["id"] != "V0")),
    ("138年60日目 ワユ3の村の返し「字で書いておいた量を読み合わせて、貸した数 (草の種 3300 つかみ) を確かめ」",
     YD(checks[0]["day"]) == "138年60日目" and "ワユ3の村" in checks[0]["text"] and "字で書いておいた量を読み合わせて、貸した数 (草の種 3300 つかみ) を確かめ" in checks[0]["text"]),
    ("年の名前 126年「黒い金属の年」", names[126] == "黒い金属の年"),
    ("村がまわりに求めた回 0", not any("V0" in x["who"] for x in dem) and len(dem) > 0),
    ("人 194 → 312・生まれ 404・亡くなり 313・加わり 63・出た 36・ききん 0", ls["population"] == 312
     and sum(len(x["births"]) for x in sv) == 404 and sum(deaths.values()) == 313 and sum(len(x["joined"]) for x in sv) == 63
     and min(x["store_days"] for x in sv) == 440),
    ("蓄え 457 → 573 日分 (409 万つかみ)", ls["store_days"] == 573 and round(ls["store"]["草の種"] / 1e4) == 409),
    ("案 66・採用 0・もめごと 21 のうち ゆるす 20", len(props) == 66 and not adopted and len(disp) == 21 and sum(r["verdict"] == "ゆるす" for r in disp) == 20),
    ("トークン 32 年で 約 2.6 億", round(sum(tok.values()) / 1e7) == 26),
]
bad = [n for n, ok in CHECK if not ok]
for n, ok in CHECK:
    print(("OK  " if ok else "NG  ") + n)
if bad:
    sys.exit("記録と合わない文がある: " + " / ".join(bad))
out.write_text(json.dumps(F, ensure_ascii=False), encoding="utf-8")
print("facts:", out)
