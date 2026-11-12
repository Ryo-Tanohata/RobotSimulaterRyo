"""G12「大きな都と帝国」の動画の数を、村の記録から読む (読むだけ。data には書かない)。
   python3 data.py <出力 facts.json>
   読むもの: sim/society/data/records/ (season_village・year_names)、data/archive/events_0164〜.jsonl と state.json の events (しまう前の出来事)、
   state.json の era2.g7.g12・hold・ends、data/prompts (19799・20159・20279 日目のお題)・answers (20279 日目)、
   sim/society/reports/year165〜172.html (年報。トークンと G12 の行)、techtree/plan.json (第 6 部のフェーズ)、sim/society/HANDOFF.md と git log の文。
   lines.json の文と図に出す数は、下の CHECK で記録と合うか確かめる (合わないと止まる)。
   G12 は 164年120日目 (19799。165年の年の集まり) に入り、172年120日目 (20759) で条件がそろって第 6 部が終わった。その間だけを読む。
   年は 年 = 日 // 120 (年報と同じ。172年 = 20640〜20759 日目)。"""
import collections
import json
import re
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
SOC = HERE.parent.parent
DATA = SOC / "data"
REC = DATA / "records"
START, END, FIX = 19799, 20759, 20279
Y = lambda d: d // 120  # noqa: E731
YD = lambda d: f"{d // 120}年{d % 120 + 1}日目"  # noqa: E731
YS = list(range(165, 173))
out = Path(sys.argv[1])

sv_all = [json.loads(l) for l in open(REC / "season_village.jsonl", encoding="utf-8")]
by_day = {x["season_end_day"]: x for x in sv_all}
sv = [x for x in sv_all if START < x["season_end_day"] <= END]
st = json.load(open(DATA / "state.json", encoding="utf-8"))
g7 = st["era2"]["g7"]
g12 = g7["g12"]


def events(lo, hi):
    out_, seen = [], set()
    for y in range(Y(lo), Y(hi) + 1):
        f = DATA / "archive" / f"events_{y:04d}.jsonl"
        if f.exists():
            for e in (json.loads(l) for l in open(f, encoding="utf-8")):
                if lo <= e["day"] <= hi and e["id"] not in seen:
                    seen.add(e["id"]); out_.append(e)
    for e in st["events"]:
        if lo <= e["day"] <= hi and e["id"] not in seen:
            seen.add(e["id"]); out_.append(e)
    return out_


ev = events(START, END)
T = lambda ty, *ws: [e for e in ev if e["type"] == ty and all(w in e["text"] for w in ws)]  # noqa: E731
fs, ls = by_day[START], by_day[END]

# 年報 (165〜172年)
rep, tok = {}, {}
for y in YS:
    t = (SOC / "reports" / f"year{y}.html").read_text(encoding="utf-8")
    t = re.sub(r"\s+", " ", re.sub(r"<[^>]+>", " ", re.sub(r"<(script|style).*?</\1>", "", t, flags=re.S)))
    rep[y] = t
    tok[y] = int(re.search(r"使ったトークン: 約 [^(]*\(([\d,]+)\)", t).group(1).replace(",", ""))
rnum = lambda y, pat: int(re.search(pat, rep[y]).group(1))  # noqa: E731
r_pacts = {y: rnum(y, r"倉の約束: 年の終わりに (\d+) 村") for y in YS}
r_c1 = {y: rnum(y, r"条件 1 倉の約束の輪 \(約束どおり出した村\) (?:✓ 届いた )?(\d+)") for y in YS}
r_help = {y: (0 if "倉から出した: この年はなかった" in rep[y] else rnum(y, r"倉から出した: \d+ 回・\d+ 集落・草の種 (\d+) つかみ")) for y in YS}
r_help_n = {y: (0 if "倉から出した: この年はなかった" in rep[y] else rnum(y, r"倉から出した: \d+ 回・(\d+) 集落")) for y in YS}
r_last = {y: rnum(y, r"\(草の種のつかみにしたねうち。去年 (\d+)\)") for y in YS}
r_census = {y: (0 if "この年はだれも帳をつけなかった" in rep[y] else rnum(y, r"帳: (\d+) 家を書いた")) for y in YS}
r_census_by = {y: (re.search(r"書いた人 ([^)]*)\)", rep[y]).group(1) if r_census[y] else "") for y in YS}
r_chose = {y: rnum(y, r"実際に選んだ人は (\d+) 人") for y in YS}
r_pop = {y: tuple(map(int, re.search(r"人数 \(年のはじめ → 終わり\) (\d+) → (\d+) 人", rep[y]).groups())) for y in YS}

led = {r["year"]: r for r in g12["ledger"]}
path = {int(y): p for y, p in g12["path"].items()}
given = {int(y): v for y, v in g12["given"].items()}
census = {int(y): c for y, c in g12["census"].items()}
pacts = g12["pacts"]
plog = g12["pact_log"]
paid_ok = {y: sum(1 for v in g12["paid"].get(str(y), {}).values() if v == "出した") for y in YS}

# 入った日のお題 (答える人のお題の 1 通): 村の倉・いま苦しい村・受けてくれそうな村
p0 = sorted((DATA / "prompts/day19799/season").glob("*.md"))[0].read_text(encoding="utf-8")
m_store = re.search(r"- 村の倉: 草の種 (\d+) つかみ \(いまの人数で 約 (\d+) 日分\)。この年に倉から出せるのは、あと 草の種 (\d+) つかみ", p0)
hard0 = re.findall(r"\[N\d+\]", re.search(r"- いま苦しい村 \([^)]*\): (.*)", p0).group(1))
like0 = re.findall(r"\[N\d+\]", re.search(r"- 倉の約束を受けてくれそうな村 \([^)]*\): (.*)", p0).group(1))

# お題の直し: ヒセ42 のお題で、節の行の場所 (直す前 = 168年の年の集まり 20159、直したあと = 20279)
def where(day):
    f = DATA / f"prompts/day{day}/season/ヒセ42.md"
    t = f.read_text(encoding="utf-8").split("\n")
    find = lambda s: next(i + 1 for i, l in enumerate(t) if l.startswith(s))  # noqa: E731
    blk = [i + 1 for i, l in enumerate(t) if l.startswith("倉と約束と帳: この集まりで")]
    return {"bytes": f.stat().st_size, "lines": len(t) - 1, "sec": find("## 倉と約束と帳"), "now": find("## いま"), "blk": blk}
pw0, pw1 = where(20159), where(FIX)
nblk = lambda d: sum(1 for f in (DATA / f"prompts/day{d}/season").glob("*.md") if "倉と約束と帳: この集まりで" in f.read_text(encoding="utf-8"))  # noqa: E731
nseason = lambda d: len(list((DATA / f"prompts/day{d}/season").glob("*.md")))  # noqa: E731
hise = json.load(open(DATA / f"answers/day{FIX}/season/ヒセ42.json", encoding="utf-8"))

# 倉から助けた出来事 (書いた人)
help_ev = T("倉", "集まりで、村の倉から、いま苦しい")
writer = lambda e: re.search(r"書いたのは ([^)]*)\)", e["text"]).group(1)  # noqa: E731
help_after = [e for e in help_ev if e["day"] >= FIX]
fix_day_help = [e for e in help_ev if e["day"] == FIX]
fix_day_pact = [x for x in plog if x["day"] == FIX]
amt = lambda e: int(re.search(r"草の種 (\d+) つかみ を渡した", e["text"]).group(1))  # noqa: E731

# 届いた日
reached, cc = g12["reached"], g12["c"]
c2_ev = T("目盛り", "条件 2「倉から地域を養う」に届いた")
c1_ev = T("目盛り", "条件 1「倉の約束の輪」に届いた")
end_ev = [e for e in T("フェーズ") if e["day"] == END]

# 人・暮らし
deaths = collections.Counter(d["cause"] for x in sv for d in x["deaths"])
names = {r["year"]: r["name"] for r in json.load(open(REC / "year_names.json", encoding="utf-8")) if 165 <= r["year"] <= 172 and r["name"]}
props = {r["year"]: [p["name"] for p in r["proposals"]] for r in json.load(open(REC / "year_names.json", encoding="utf-8")) if 165 <= r["year"] <= 172}
yak = sorted({n for y in props for n in props[y] if "約束" in n})
seasons = [{"day": x["season_end_day"], "pop": x["population"], "store_days": x["store_days"]} for x in [fs] + sv]
plan = json.load(open(SOC / "techtree/plan.json", encoding="utf-8"))
part6 = [e for e in plan["eras"] if e["name"] == "鉄とお金の帝国"][0]
part7 = [e for e in plan["eras"] if e["name"] == "帝国のあとと町"][0]
LOG = subprocess.run(["git", "-C", str(SOC), "log", "--format=%s"], capture_output=True, text=True, check=True).stdout
HO = (SOC / "HANDOFF.md").read_text(encoding="utf-8")

F = {"start": START, "end": END, "seasons": seasons, "tok": tok, "names": names, "path": path,
     "pacts_y": r_pacts, "c1_y": r_c1, "help_y": r_help, "given_y": {y: given.get(y, 0) for y in YS}, "fix_year": Y(FIX),
     "goals": [["条件 1", "倉の約束どおり村に出した集落が 5 つ以上の年が 2 回", YD(cc["c1"]), "170年 9 集落・172年 10 集落"],
               ["条件 2", "1 年に 3 集落以上へ、合わせて草の種 30000 つかみ以上を倉から", YD(cc["c2"]), "9 集落・32000 つかみ"],
               ["条件 3", "家の人の数・倉・約束を字で書いた帳がそろう年が 2 年つづく", YD(cc["c3"]), "169・170年 41 家"],
               ["F1", "はじめての倉の約束", YD(reached["F1"]), "南の村"],
               ["F2", "はじめて倉から助けを出した", YD(reached["F2"]), "南の村に 2000 つかみ"],
               ["F3", "はじめての帳", YD(reached["F3"]), "ヒセ42"],
               ["F4", "約束の分が、はじめて村に届いた", YD(reached["F4"]), "南の村から 50 つかみ"]]}

CHECK = [
    ("期間 164年120日目〜172年120日目・8 年・32 季節", YD(START) == "164年120日目" and YD(END) == "172年120日目" and len(sv) == 32
     and g12["start"] == START and st["day"] == END and [e["text"] for e in T("フェーズ") if e["day"] == START] == [
         "G11 (お金と市場): 3 つの条件はそろわないまま、ここで閉じた", "フェーズ G12 (大きな都と帝国) を始めた"]),
    ("第 6 部「鉄とお金の帝国」は G10・G11・G12。次の第 7 部は G13・G14", part6["phases"] == ["G10", "G11", "G12"] and part7["phases"][0] == "G13"),
    ("入った日: 348 人・村の倉 4,017,423 つかみ = 478 日分・この年に出せる 401,742・いま苦しい村 13・受けてくれそうな村 17・読める大人 5",
     fs["population"] == 348 and m_store and m_store.group(1) == "4017423" and m_store.group(2) == "478" and m_store.group(3) == "401742"
     and len(hard0) == 13 and len(like0) == 17 and led[165]["readers"] == 5),
    ("165〜168年: 選んだ人 2・1・1・0 (選べた人 条件 1 は 毎年 38〜40)", [r_chose[y] for y in range(165, 169)] == [2, 1, 1, 0]
     and [path[y]["chose"] for y in YS] == [r_chose[y] for y in YS] and all(38 <= path[y]["c1"] <= 40 for y in range(165, 169))),
    ("165〜168年: 年の終わりの約束 0・帳は 165年 41 家 (ヒセ42) のあと 166〜168年 0 家",
     all(r_pacts[y] == 0 for y in range(165, 169)) and r_census[165] == 41 and r_census_by[165] == "ヒセ42"
     and all(r_census[y] == 0 for y in range(166, 169))),
    ("165〜168年の倉からの助け: 4 回 (2000・1800・2000・2000。164年120日目〜166年120日目)",
     [amt(e) for e in help_ev if e["day"] < FIX] == [2000, 1800, 2000, 2000] and max(e["day"] for e in help_ev if e["day"] < FIX) == 20039),
    ("お題 (ヒセ42、168年の年の集まり): 255 KB・1,013 行・節「## 倉と約束と帳」は 895 行目",
     round(pw0["bytes"] / 1000) == 255 and pw0["lines"] == 1013 and pw0["sec"] == 895 and pw0["blk"] == []),
    ("168年120日目 (20279) に直した: 短い節は 944 行目 (「## いま」936 行目のすぐあと、答えの並びの前)・答える人 20 通みな",
     g12["prompt_fix"]["day"] == FIX and YD(FIX) == "168年120日目" and pw1["now"] == 936 and pw1["blk"] == [944]
     and nblk(FIX) == 20 and nseason(FIX) == 20 and nblk(20159) == 0
     and [YD(e["day"]) for e in T("区切り", "お題を書き直した")] == ["168年120日目"]
     and "本人の決め 2026-11-11" in g12["prompt_fix"]["why"]),
    ("直したのはお題だけ (決まり・数は変えない)", "**お題だけ** を直した (決まり・数は変えない" in HO
     and "G12 のお題を直した (168年120日目。本人の決め 2026-11-11)" in LOG),
    ("直したあとの最初の集まり (20279): 約束 3 (南の村・北東の村14・ハソ12の村)・助け 7 集落 21,500",
     [x["other"] for x in fix_day_pact] == ["N1", "N14", "N85"] and len(fix_day_help) == 7 and sum(map(amt, fix_day_help)) == 21500
     and given[168] == 21500 and reached["F1"] == FIX),
    ("直す前の「## いま」は 927 行目", pw0["now"] == 927),
    ("帳を書いた人: 169年 ヒセ42・170年 アコ34・ヒセ42・ホミ34・171年 ハソ50・ユエ49・172年 ヒセ42",
     [r_census_by[y] for y in range(169, 173)] == ["ヒセ42", "アコ34・ヒセ42・ホミ34", "ハソ50・ユエ49", "ヒセ42"]),
    ("約束の名前の案は 3 つとも 169年", all(n in props[169] for n in yak)),
    ("ヒセ42 の言葉 (20279 日目の答え)", any(s["text"] == "倉には草の種がたっぷりある。畑が実らず苦しい近くの村に、少しずつ分けてあげよう。困ったときに助け合える仲になれる。" for s in hise["say"])),
    ("年の終わりの約束: 169年 5 → 170年 9 → 171年 10 → 172年 11", [r_pacts[y] for y in range(169, 173)] == [5, 9, 10, 11]
     and [led[y]["pacts"] for y in range(169, 173)] == [5, 9, 10, 11] and len(pacts) == 11 and all(p["status"] == "続く" for p in pacts.values())),
    ("約束どおり出した村: 169年 3・170年 9・171年 2・172年 10 (171年は 8 村が苦しく、村が出した)",
     [r_c1[y] for y in range(169, 173)] == [3, 9, 2, 10] and [paid_ok[y] for y in range(169, 173)] == [3, 9, 2, 10]
     and "苦しいので村が出した 8 村" in rep[171] and g12["c1_years"] == [170, 172]),
    ("年報の「この年に倉から出した量」: 169年 12,500・170年 30,000・171年 24,000・172年 13,000 (165〜168年は 0)",
     [r_help[y] for y in YS] == [0, 0, 0, 0, 12500, 30000, 24000, 13000] and [led[y]["relief_amount"] for y in YS] == [r_help[y] for y in YS]
     and [r_help_n[y] for y in range(169, 173)] == [4, 2, 8, 5]),
    ("年報の「去年」の欄 (年の集まりの日に決めた助けも入れた数): 21,500・21,500・30,000・60,000",
     [r_last[y] for y in range(169, 173)] == [21500, 21500, 30000, 60000] and all(r_last[y] == given.get(y - 1, 0) for y in range(166, 173))
     and given[172] == 13000),
    ("帳: 169〜172年は毎年そろった (41・41・40・41 家)", [r_census[y] for y in range(169, 173)] == [41, 41, 40, 41]
     and all("この年の帳はそろった" in rep[y] for y in range(169, 173)) and sorted(census) == [165, 169, 170, 171, 172]),
    ("届いた日: 条件 3 170年120日目・条件 2 171年120日目・条件 1 172年120日目・第 6 部の終わり",
     YD(cc["c3"]) == "170年120日目" and YD(cc["c2"]) == "171年120日目" and YD(cc["c1"]) == "172年120日目"
     and len(c2_ev) == 1 and "9 集落へ、合わせて草の種 32000 つかみ分" in c2_ev[0]["text"] and len(c1_ev) == 1 and "(170・172年)" in c1_ev[0]["text"]
     and [e["text"] for e in end_ev] == ["第 6 部の終わり (G12): G12 の条件がそろった"]
     and g7["hold"] == {"why": "part_end", "era": "G12", "day": END} and g7["ends"]["G12"]["day"] == END),
    ("F: F2 164年120日目・F3 165年31日目・F1 168年120日目・F4 169年120日目",
     [YD(reached[k]) for k in ("F2", "F3", "F1", "F4")] == ["164年120日目", "165年31日目", "168年120日目", "169年120日目"]),
    ("ほとんど一人の読み手 ヒセ42: 約束 11 のうち 10・直したあとの助け 24 回のうち 19 回・帳 5 年のうち 4 年",
     sum(1 for p in pacts.values() if p["by"] == ["ヒセ42"]) == 10 and len(help_after) == 24
     and sum(1 for e in help_after if writer(e) == "ヒセ42") == 19 and sum(1 for c in census.values() if "ヒセ42" in c["by"]) == 4),
    ("選んだ人 (のべ) 169年 5・170年 5・171年 3・172年 4", [r_chose[y] for y in range(169, 173)] == [5, 5, 3, 4]),
    ("人 348 → 378・生まれ 156・亡くなり 133 (小さいうち 72・病 45・年 14・ザガ 2)・加わり 7・出た 0",
     ls["population"] == 378 and r_pop[165][0] == 348 and r_pop[172][1] == 378 and sum(len(x["births"]) for x in sv) == 156
     and sum(deaths.values()) == 133 and deaths["子"] == 72 and deaths["病"] == 45 and deaths["年"] == 14 and deaths["ザガ"] == 2
     and sum(len(x["joined"]) for x in sv) == 7 and sum(len(x["left"]) for x in sv) == 0 and max(x["population"] for x in sv) == 383),
    ("蓄え: 季節の終わり 379〜592 日分、172年の終わり 379 日分 (G12 でいちばん少ない)・ききんなし",
     min(x["store_days"] for x in sv) == 379 and max(x["store_days"] for x in sv) == 592 and ls["store_days"] == 379
     and all("飢えはなかった" in rep[y] for y in YS)),
    ("年の名前 165〜171年: みな実り・刈り入れ・蓄え。案には「約束の種が届いた年」など 3 つ",
     sorted(names) == list(range(165, 172)) and not any("約束" in n or "倉" in n for n in names.values())
     and yak == ["病と倉の約束の年", "約束の分が届いた年", "約束の種が届いた年"]),
    ("トークン: 8 年とも 1,500 万の下 (1,204 万〜1,241 万)・8 年で 約 9,765 万",
     all(tok[y] < 15_000_000 for y in YS) and min(tok.values()) == 12036714 and max(tok.values()) == 12409699
     and round(sum(tok.values()) / 1e4) == 9765),
    ("帳を書けずに休んだ 1 回 (169年 ユエ49。字を読めない)", len(g12["fails"]) == 1 and g12["fails"][0]["who"] == "ユエ49" and g12["fails"][0]["year"] == 169),
]
bad = [n for n, ok in CHECK if not ok]
for n, ok in CHECK:
    print(("OK  " if ok else "NG  ") + n)
if bad:
    sys.exit("記録と合わない文がある: " + " / ".join(bad))
out.write_text(json.dumps(F, ensure_ascii=False), encoding="utf-8")
print("facts:", out)
