"""第 7 部「帝国のあとと町」(G13・G14) の動画の数を、村の記録から読む (読むだけ。data には書かない)。
   python3.13 data.py <出力 facts.json>
   読むもの: sim/society/data/records/ (season_village・year_names)、data/archive/events_0172〜.jsonl と state.json の events (しまう前の出来事)、
   state.json の era2.g7 (g13・g14・closed13・closed14・hold・ends・consulted)、sim/society/reports/year173〜193.html (年報)、
   docs/society_phase/G13.md・G14_design.md、sim/society/HANDOFF.md と git log の文。
   lines.json の文と図に出す数は、下の CHECK で記録と合うか確かめる (合わないと止まる)。
   第 7 部は 172年120日目 (20759) に G13 に入り、178年60日目 (21419) に G14 に入り、193年60日目 (23219) に G14 を閉じて終わった。その間だけを読む。
   年は 年 = 日 // 120 (年報と同じ)。道の見張りの年だけは「年の集まり」の年 = (日 + 1) // 120 (G13.md と同じ)。"""
import collections
import json
import re
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
SOC = HERE.parent.parent
ROOT = SOC.parent.parent
DATA = SOC / "data"
REC = DATA / "records"
START, MID, END = 20759, 21419, 23219
Y = lambda d: d // 120  # noqa: E731
YD = lambda d: f"{d // 120}年{d % 120 + 1}日目"  # noqa: E731
YS = list(range(173, 194))      # 年報のある年 (193年は 60日目まで)
out = Path(sys.argv[1])

sv_all = [json.loads(l) for l in open(REC / "season_village.jsonl", encoding="utf-8")]
by_day = {x["season_end_day"]: x for x in sv_all}
sv = [x for x in sv_all if START < x["season_end_day"] <= END]
sv13 = [x for x in sv if x["season_end_day"] <= MID]
sv14 = [x for x in sv if x["season_end_day"] > MID]
st = json.load(open(DATA / "state.json", encoding="utf-8"))
g7 = st["era2"]["g7"]
g13, g14, cl13, cl14 = g7["g13"], g7["g14"], g7["closed13"], g7["closed14"]


def events(lo, hi):
    got = {}
    for y in range(Y(lo), Y(hi) + 1):
        f = DATA / "archive" / f"events_{y:04d}.jsonl"
        if f.exists():
            for e in (json.loads(l) for l in open(f, encoding="utf-8")):
                if lo <= e["day"] <= hi:
                    got[e["id"]] = e
    for e in st["events"]:
        if lo <= e["day"] <= hi:
            got[e["id"]] = e
    return sorted(got.values(), key=lambda e: (e["day"], e["id"]))


ev = events(START, END)
T = lambda ty, *ws: [e for e in ev if e["type"] == ty and all(w in e["text"] for w in ws)]  # noqa: E731

# 年報 (173〜193年)
rep, tok = {}, {}
for y in YS:
    t = (SOC / "reports" / f"year{y}.html").read_text(encoding="utf-8")
    t = re.sub(r"\s+", " ", re.sub(r"<[^>]+>", " ", re.sub(r"<(script|style).*?</\1>", "", t, flags=re.S)))
    rep[y] = t
    tok[y] = int(re.search(r"使ったトークン: 約 [^(]*\(([\d,]+)\)", t).group(1).replace(",", ""))
r_pop = {y: tuple(map(int, re.search(r"人数 \(年のはじめ → 終わり\) (\d+) → (\d+) 人", rep[y]).groups())) for y in YS}

# G13 の帳簿 (年ごと。G14 の間も「ならべて測る」で続いている)
l13 = {r["year"]: r for r in g13["ledger"]}
l14 = {r["year"]: r for r in g14["ledger"]}
water = {int(y): w for y, w in cl13["water"].items()}
wet = {y: round(100 * water[y]["water"] / water[y]["sown"]) for y in range(173, 179)}
grind = {y: round(l13[y]["grind_days"]) for y in range(173, 193)}
mills = {y: l13[y]["mills"] for y in range(173, 193)}
running = {y: l13[y]["mills_running"] for y in range(173, 193)}
repair = {y: round(l13[y]["mill_repair"]) for y in range(173, 193)}
water_ev = [e for e in ev if e["type"] == "水"]
built = collections.Counter(Y(e["day"]) for e in water_ev if "建った" in e["text"] and "水の輪" in e["text"])
stopped = collections.Counter(e["day"] for e in water_ev if "羽と軸がいたんで止まった" in e["text"])
restarted = collections.Counter(Y(e["day"]) for e in water_ev if "直って、また回りはじめた" in e["text"])
fix185 = sorted({e["text"].split(" が、")[0] for e in T("水の輪を建てる", "止まっている水の輪を直した") if Y(e["day"]) == 185})
mill_talk = [e for e in T("話す", "ヒセ42 → みんな", "水の輪が七つとも止まったままだ。粉ひきに毎日") if e["day"] == 22199]

# G14
path14 = {int(y): p for y, p in cl14["path"].items()}
chose14 = {y: path14[y]["chose"] for y in range(179, 194)}
town = {y: l14[y]["town_share"] for y in range(178, 193)}
mkt = {y: l14[y]["market_grain"] for y in range(178, 193)}
readers14 = {y: l14[y]["readers"] for y in range(178, 193)}
notes = g14["notes"]["list"]
guild = g14["guilds"]["list"]
reached14, c14 = g14["reached"], g14["c"]
store_all = [l14[y]["store"] for y in range(178, 193)]

# 人
def people(svs):
    dc = collections.Counter(d["cause"] for x in svs for d in x["deaths"])
    return {"births": sum(len(x["births"]) for x in svs), "deaths": sum(dc.values()), "dc": dc,
            "joined": sum(len(x["joined"]) for x in svs), "left": sum(len(x["left"]) for x in svs)}
P13, P14, P7 = people(sv13), people(sv14), people(sv)
seasons = [{"day": x["season_end_day"], "pop": x["population"], "store_days": x["store_days"]} for x in [by_day[START]] + sv]
yn = json.load(open(REC / "year_names.json", encoding="utf-8"))
names = {r["year"]: r["name"] for r in yn if 173 <= r["year"] <= 192 and r["name"]}
props = {r["year"]: [p["name"] for p in r["proposals"]] for r in yn if 173 <= r["year"] <= 192}
plan = json.load(open(SOC / "techtree/plan.json", encoding="utf-8"))
part7 = [e for e in plan["eras"] if e["name"] == "帝国のあとと町"][0]
LOG = subprocess.run(["git", "-C", str(SOC), "log", "--format=%s"], capture_output=True, text=True, check=True).stdout
HO = (SOC / "HANDOFF.md").read_text(encoding="utf-8")
G13MD = (ROOT / "docs/society_phase/G13.md").read_text(encoding="utf-8")
G14D = (ROOT / "docs/society_phase/G14_design.md").read_text(encoding="utf-8")

F = {"start": START, "mid": MID, "end": END, "seasons": seasons, "tok": tok, "names": names,
     "wet": wet, "grind": grind, "mills": mills, "running": running, "chose14": chose14, "town": town, "market": mkt,
     "goals13": [["条件 1", "水の力の粉ひき: 水の輪が 1 年に 90 日回り、粉の半分以上", YD(cl13["c"]["c1"]), "177年 120 日・粉の 88%"],
                 ["条件 2", "水の来る畑: 秋の畑の半分以上が水の来る畑の年が 2 年つづく", YD(cl13["c"]["c2"]), "177年 91%・178年 100%"],
                 ["条件 3", "務め: 地域の集落の半分以上が約束の分を出した年が 2 回", YD(cl13["c"]["c3"]), "173・174年 11 集落"],
                 ["F1", "はじめて水の道を掘った", YD(cl13["reached"]["F1"]), ""],
                 ["F2", "水の輪を試しはじめた", YD(cl13["reached"]["F2"]), ""],
                 ["F3", "水の輪が回った", YD(cl13["reached"]["F3"]), "M1"],
                 ["F4", "よその集落の働き手が村で働いた", "届かなかった", "働き手を書いた答え 0"]],
     "goals14": [["条件 1", "町の家: 町の家に住む人が地域の 1 割以上の年が 2 年つづく", "届かなかった", "いちばん多い年 約 4% (181年)"],
                 ["条件 2", "書きつけ: 書きつけどおり払った集落が 3 つ以上の年が 2 回", "届かなかった", "185年の 1 回だけ"],
                 ["条件 3", "仲間: 3 人・2 家以上・1 年 90 人日の仲間が 2 年つづく", YD(c14["c3"]), "186・187年 土器づくり"],
                 ["F1", "はじめて市へ運んだ", YD(reached14["F1"]), "土器 1 個 → 草の種 40"],
                 ["F2", "はじめての書きつけ", YD(reached14["F2"]), "南の村"],
                 ["F3", "はじめての仲間", YD(reached14["F3"]), "土器づくり 4 人"],
                 ["F4", "はじめての町の家", YD(reached14["F4"]), "2 家"]]}

CHECK = [
    ("第 7 部: G13 172年120日目〜178年60日目 (5 年半・22 季節)・G14 178年60日目〜193年60日目 (15 年・60 季節)",
     YD(START) == "172年120日目" and YD(MID) == "178年60日目" and YD(END) == "193年60日目" and len(sv13) == 22 and len(sv14) == 60
     and g13["start"] == START and g14["start"] == MID and st["day"] == END and part7["phases"] == ["G13", "G14"]),
    ("いまは HOLD part_end (193年60日目)・G14 は本人の決め (Claude のおすすめ) で閉じた・第 7 部の終わり",
     g7["hold"] == {"why": "part_end", "era": "G14", "day": END} and g7["ends"]["G14"]["by"] == "本人の決め" and cl14["part_end"] == 7
     and cl14["by"].startswith("Claude のおすすめで閉じた (本人の指示「質問しないであなたのおすすめで進めて下さい」による")
     and [e["text"] for e in T("フェーズ") if e["day"] == END] == ["G14 (町と商業): 3 つの条件はそろわないまま、ここで閉じた。第 7 部「帝国のあとと町」も、ここで終わった"]),
    ("入った日 378 人・蓄え 379 日分・札を知る大人 2・読める大人 6 → 178年 4 → 193年 2",
     by_day[START]["population"] == 378 and by_day[START]["store_days"] == 379 and "知っている大人 2 人 (ヌオ29・リセ32)。読める大人 6 人" in G13MD
     and len(cl13["readers"]) == 4 and cl14["readers"] == ["オネ54", "ロワ53"]),
    ("173年: ヌオ29 が 60日目に年で亡くなり、札を知る大人は リセ32 1 人・ヒセ5の家の 33 人が村を出た",
     "ヌオ29 (56 歳) — 年をとって 173年60日目" in rep[173] and "村を出た人 0 人 / 33 人" in rep[173] and P13["left"] == 33
     and "ヒセ5の家の 33 人 (大人 16・子 17) が村を出た" in G13MD),
    ("175年60日目に村で水の輪が作れるように (リセ32 が 3 人に教えた)・176年85日目 M1 = F3・リセ32 は 176年120日目に病で",
     "**村で水の輪ができるようになった** (試した人 シエ37・ソワ32・ラニ37・リセ32)" in G13MD and YD(cl13["reached"]["F3"]) == "176年85日目"
     and "リセ32 (53 歳) — 病気で 176年120日目" in rep[176]),
    ("手でひいた粉ひき (人日): 173年 1870・174年 1746・175年 1795・176年 1461・177年 217・178〜184年 0・185年 519",
     [grind[y] for y in range(173, 178)] == [1870, 1746, 1795, 1460, 217] and all(grind[y] == 0 for y in range(178, 185)) and grind[185] == 519),
    ("水の来る畑 (秋): 11・35・32・37・91・100%", [wet[y] for y in range(173, 179)] == [11, 35, 32, 37, 91, 100]),
    ("悪い年に水の来る畑が守った: 176年 133,571・177年 200,238 つかみ", g13["protected"]["176"] == 133571 and g13["protected"]["177"] == 200238),
    ("G13 の届いた日: c3 174年120日目・c1 177年120日目・c2 178年60日目・F1 F2 173年31日目・F4 届かず",
     [YD(cl13["c"][k]) for k in ("c3", "c1", "c2")] == ["174年120日目", "177年120日目", "178年60日目"]
     and YD(cl13["reached"]["F1"]) == YD(cl13["reached"]["F2"]) == "173年31日目" and cl13["reached"]["F4"] is None
     and cl13["mills"] == 5),
    ("c3 は G12 の倉の約束 11 だけで届き、pact を書いた答えは 0・働き手 0",
     "G13 の 5 年半で、pact を書いた答えそのものが 0" in G13MD and "**働き手を書いた答えは 0**" in G13MD and cl13["pacts"] == 11 and cl13["workers"] == {}),
    ("G13 で選んだ人は 1 年に 4〜6 人・水の輪 5 つはほとんどホミ34 1 人の答え・水の道 26 回のうち 14 回は ヒセ42・ホミ34",
     sorted({p["chose"] for p in cl13["path"].values()}) == [4, 5, 6] and "**水の輪 5 つは、ほとんどホミ34 1 人の答えから**" in G13MD
     and "そのうちヒセ42 とホミ34 の 2 人で 26 回のうち 14 回" in G13MD),
    ("G13 のトークン 約 7,251 万 (176年は見込み 12,000,000)", "合わせて **約 72,510,961**" in G13MD and tok[176] == 12_000_000),
    ("179・180年: 答える人 22〜23 人のだれも 市へ運ぶ・note・guild を書かなかった (わけ: 答えの形に欄がない・仲間の名前が「…」・市の例がない)",
     "答える人 22〜23 人のだれも 市へ運ぶ・note・guild を書かなかった" in HO and "**答えの形 (JSON) に note と guild の欄がなかった**" in G14D
     and "**仲間の例の名前が「…」だった**" in G14D and all(mkt[y] == 0 for y in (178, 179, 180)) and l14[180]["notes_written"] == 0),
    ("お題の直し 180年120日目 (21719)・お題だけ・決まりと数は変えない",
     g14["prompt_fix"]["day"] == 21719 and YD(21719) == "180年120日目" and "社会シミュレーション: G14 のお題を直した (180年120日目)" in LOG
     and "**お題だけ** を直した (決まり・数・決め方は変えない" in HO),
    ("直したあと: F2 181年30日目 (ヒセ42)・F4 181年120日目・F1 183年62日目 (ロワ33 が土器 1 個で草の種 40)・183年の名前「はじめて市へ運んだ年」",
     YD(reached14["F2"]) == "181年30日目" and YD(reached14["F4"]) == "181年120日目" and YD(reached14["F1"]) == "183年62日目"
     and any("ロワ33 が 南の村 に 土器 1個 を運び、草の種 40 つかみを受けた" in e["text"] for e in T("目盛り")) and names[183] == "はじめて市へ運んだ年"),
    ("選んだ人 (のべ) 179年 2・180年 5 → 181年 8・187年 14 (いちばん多い)・192・193年 5",
     [chose14[y] for y in (179, 180, 181)] == [2, 5, 8] and max(chose14.values()) == 14 and chose14[187] == 14 and chose14[192] == chose14[193] == 5),
    ("書きつけ 9 はみな ヒセ42・185年に 3 村 (南の村・南東の村・北の大きな村) が払った = c2 の 1 回・186年の 3 つは 187年に破れた",
     len(notes) == 9 and all(n["by"] == "ヒセ42" for n in notes) and g14["c2_years"] == [185]
     and [n["to"] for n in notes if n["paid"] == 22319] == ["N1", "N4", "N83"]
     and [n["status"] for n in notes[-3:]] == ["破れた"] * 3 and all(n["day"] == 22319 for n in notes[-3:]) and cl14["notes"] == {"払った": 6, "破れた": 3}),
    ("ヒセ42 は 186年60日目に病で亡くなった。そのあと書きつけを書いた人は 0",
     "ヒセ42 (50 歳) — 病気で 186年60日目" in rep[186] and max(n["day"] for n in notes) < 22379
     and all(l14[y]["notes_written"] == 0 for y in range(186, 193))),
    ("市へ運んだ: 合わせて 125 回・草の種 24,870 つかみ (183年 6,460・186年 6,720・190年 8,950・191年 2,740)・村の倉は 約 300〜500 万",
     cl14["market"] == {"trips": 125, "grain": 24870} and sum(mkt.values()) == 24870
     and {y: v for y, v in mkt.items() if v} == {183: 6460, 186: 6720, 190: 8950, 191: 2740}
     and 2_700_000 < min(store_all) and max(store_all) < 5_100_000),
    ("仲間 K1 (土器づくり): 186年30日目、ホタ56 1 人の答えで 4 人を名前で書いて結んだ・186・187年 90 人日 → 条件 3 187年120日目・188・189年 30 人日で終わった",
     len(guild) == 1 and guild[0]["job"] == "土器づくり" and guild[0]["by"] == ["ホタ56"] and YD(guild[0]["day"]) == "186年30日目"
     and guild[0]["status"] == "終わった" and YD(c14["c3"]) == "187年120日目" and g14["c3_years"] == [186, 187]
     and [l14[y]["guilds"].get("K1", {}).get("days") for y in (186, 187, 188, 189)] == [90, 90, 30, 30]
     and len(T("町と市", "2 年つづけて仲間の人がその仕事を 90 人日しなかったので終わった")) == 1),
    ("町の家: いちばん多い年 181年 約 4% (目安 1 割)・192年 0.3%",
     max(town.values()) == town[181] and round(100 * town[181]) == 4 and round(100 * town[192], 1) == 0.3 and g14["c1_years"] == []),
    ("水の輪の直しの年のまちがい: 年の集まりのお題はいつも「あと 0 人日」→ 184年の終わり (22199) に 7 つみな止まった",
     stopped[22199] == 7 and running[184] == 0 and "年の集まりのお題ではいつも「水の輪の直し あと 0 人日」「水の道の手入れ あと 0 人日」" in HO),
    ("ヒセ42 の言葉 (184年120日目)", len(mill_talk) == 1),
    ("185年の秋の集まりのあと 18 人で 7 つを直し (185年31〜34日目)、そのまま新しく 9 つ建てた",
     len(fix185) == 18 and restarted[185] == 7 and built[185] == 9 and mills[185] == 16),
    ("続けることの年の直し 185年120日目 (22319)・お題だけ", g14["keep_fix"]["day"] == 22319 and YD(22319) == "185年120日目"
     and "社会シミュレーション: 続けることの年の直し (185年120日目)" in LOG),
    ("水の輪: 183年 7 → 185年 16 → 186年 21 → 187年 22 → 192年 25 (みな村のもの)・1 つ 250 人分・村には 2 つで足りる",
     [mills[y] for y in (182, 183, 185, 186, 187, 191, 192)] == [5, 7, 16, 21, 22, 22, 25] and cl14["mills"] == 25
     and "1 日に村の 約 250 人分の粉をひける" in T("水", "(M8) が建った")[0]["text"] and max(x["population"] for x in sv) <= 500),
    ("直す手: 1 年 1 つ 10 人日。192年は 220 人日・止まった輪 188年の終わり 7・191年の終わり 19 (22 のうち回っていたのは 3)",
     repair[192] == 220 and stopped[22679] == 7 and stopped[23039] == 19 and running[191] == 3 and mills[191] == 22),
    ("相談: 183年60日目・188年60日目 (どちらも変えずに続ける)・193年60日目 (15 年。閉じた)",
     [c["day"] for c in g7["consulted"] if str(c.get("why", "")).startswith("g14_years")] == [22019, 22619, 23219]
     and "G14 の 5 年の相談 (183年60日目)" in LOG and "G14 の 10 年の相談 (188年60日目)" in LOG and "G14 を閉じて第 7 部を終えた (193年60日目" in LOG),
    ("閉じたわけ: 15 年で届いたのは仲間だけ・町の家 0.3%・書きつけ 3 村の年が 1 回・読める大人 2 人・202年までに届く見込みは低い",
     "15 年で届いたのは仲間 (c3) だけ。町の家は地域の 0.3%、書きつけは 3 村の年が 1 回で、読める大人は 2 人にへった。202年までに届く見込みは低い" in cl14["by"]
     and "第 7 部の目安 202年120日目 (24359 日目" in HO),
    ("G14 の F: F2 181年30日目・F4 181年120日目・F1 183年62日目・F3 186年30日目",
     [YD(reached14[k]) for k in ("F2", "F4", "F1", "F3")] == ["181年30日目", "181年120日目", "183年62日目", "186年30日目"]),
    ("人 378 → 455・生まれ 432・亡くなり 351 (小さいうち 185・病 132・年 33・ザガ 1)・加わり 29・出た 33",
     seasons[0]["pop"] == 378 and seasons[-1]["pop"] == 455 and by_day[MID]["population"] == 378
     and P7["births"] == 432 and P7["deaths"] == 351 and P7["dc"] == {"子": 185, "病": 132, "年": 33, "ザガ": 1} and P7["joined"] == 29 and P7["left"] == 33
     and r_pop[173][0] == 378 and r_pop[193][1] == 455),
    ("ききん 0・季節の終わりの蓄え いちばん少ない 296 日分 (192年の終わり)・193年60日目 297 日分",
     all("飢えはなかった" in rep[y] for y in YS) and min(s["store_days"] for s in seasons) == 296 and by_day[23159]["store_days"] == 296
     and by_day[END]["store_days"] == 297),
    ("年の名前 173〜192年: 刈り入れ・実りが多い。水・輪の名前は 0 (176年の案に「水の輪が回った年」)・新しいことは 183年「はじめて市へ運んだ年」だけ・ほかは病や亡くした人",
     sorted(names) == list(range(173, 193)) and not any("水" in n or "輪" in n for n in names.values()) and "水の輪が回った年" in props[176]
     and sum(1 for n in names.values() if "刈" in n or "実" in n) == 15),
    ("トークン: 21 の年報で 約 2 億 5,723 万・どの年も 1,500 万の下・176年と 180年は 12,000,000 ちょうど",
     round(sum(tok.values()) / 1e4) == 25723 and all(v < 15_000_000 for v in tok.values()) and tok[176] == tok[180] == 12_000_000
     and min(tok.values()) == 11878025 and max(tok.values()) == 12662003),
    ("185年の直しは 31〜34日目の 4 日・悪い年に守った分 176・177年で 33 万つかみあまり・水の来る畑は 178〜192年も毎年 100%",
     sorted({e["day"] % 120 + 1 for e in T("水の輪を建てる", "止まっている水の輪を直した") if Y(e["day"]) == 185}) == [31, 32, 33, 34]
     and 330_000 < g13["protected"]["176"] + g13["protected"]["177"] < 340_000 and all(l13[y]["water_frac"] == 1.0 for y in range(178, 193))),
]
bad = [n for n, ok in CHECK if not ok]
for n, ok in CHECK:
    print(("OK  " if ok else "NG  ") + n)
if bad:
    sys.exit("記録と合わない文がある: " + " / ".join(bad))
out.write_text(json.dumps(F, ensure_ascii=False), encoding="utf-8")
print("facts:", out)
