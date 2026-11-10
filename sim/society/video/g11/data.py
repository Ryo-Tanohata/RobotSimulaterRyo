"""G11「お金と市場」の動画の数を、村の記録から読む (読むだけ。data には書かない)。
   python3 data.py <出力 facts.json>
   読むもの: sim/society/data/records/ (season_village・year_names・laws・disputes)、
   data/archive/events_0150〜.jsonl と state.json の events (しまう前の出来事)、state.json の era2.g7.g11・closed10・g10・hold・consulted・region.log・feel_cap、
   data/prompts・answers の 19559〜19799 日目のファイルの数、sim/society/reports/year151〜164.html (年報。トークンと G11 の行)。
   lines.json の文と図に出す数は、下の CHECK で記録と合うか確かめる (合わないと止まる)。
   G11 は 150年120日目 (18119) に入り、164年120日目 (19799。165年の年の集まり) で止めている。その間だけを読む。
   年は 年 = 日 // 120 (年報と同じ。164年 = 19680〜19799 日目)。"""
import collections
import json
import math
import re
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
SOC = HERE.parent.parent
DATA = SOC / "data"
REC = DATA / "records"
START, END = 18119, 19799
Y = lambda d: d // 120  # noqa: E731
YD = lambda d: f"{d // 120}年{d % 120 + 1}日目"  # noqa: E731
YE = lambda y: 120 * y + 119  # noqa: E731  その年の終わりの日
YS = list(range(151, 165))
out = Path(sys.argv[1])

sv_all = [json.loads(l) for l in open(REC / "season_village.jsonl", encoding="utf-8")]
by_day = {x["season_end_day"]: x for x in sv_all}
sv = [x for x in sv_all if START < x["season_end_day"] <= END]
st = json.load(open(DATA / "state.json", encoding="utf-8"))
g7 = st["era2"]["g7"]
g11, g10, c10 = g7["g11"], g7["g10"], g7["closed10"]


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

# 季節ごとの人 (図)
seasons = [{"day": x["season_end_day"], "pop": x["population"], "store_days": x["store_days"]} for x in [fs] + sv]

# 印のかたまり・払い方・引きかえ・市の日
led = {r["year"]: r for r in g11["ledger"]}
mark, pay, redeem = g11["mark"], g11["pay"], g11["redeem"]
mark_ev = T("印", "川と草の穂")

# 申し出 (T の番号ごと) と、受けなかった票
offer_re = re.compile(r"\[(T\d+)\]")
offers, decide = {}, {}
for e in sorted(ev, key=lambda e: e["day"]):
    if e["type"] != "よその村" or e["day"] <= START:
        continue
    m = offer_re.search(e["text"])
    if not m:
        continue
    if "また村に来た" in e["text"]:
        offers[m.group(1)] = {"day": e["day"], "loan": "貸してほしい" in e["text"], "text": e["text"]}
    elif "は受けなかった" in e["text"] or "を受けた" in e["text"]:
        v = re.search(r"村 (\d+)・家 (\d+)・受けない (\d+) / 大人 (\d+)", e["text"])
        decide[m.group(1)] = {"ok": "は受けなかった" not in e["text"], "village": int(v.group(1)), "no": int(v.group(3)), "adults": int(v.group(4))}
off_y = collections.Counter(Y(o["day"]) for o in offers.values())
TRUST_DAY = g11["trust_fix"]["day"]
before = sorted(t for t, o in offers.items() if o["day"] <= TRUST_DAY)
after = sorted((t for t, o in offers.items() if o["day"] > TRUST_DAY), key=lambda t: int(t[1:]))
kind_after = collections.Counter("貸して" if offers[t]["loan"] else "交換" for t in after)
loan_amt = [int(re.search(r"草の種 (\d+) つかみ を貸して", offers[t]["text"]).group(1)) for t in after if offers[t]["loan"]]
shape = collections.Counter(
    "決めない" if decide[t]["village"] == 0 and decide[t]["no"] == 0 else
    "受けないが多い" if decide[t]["no"] > decide[t]["village"] else "村が多いが半分に届かない" for t in after)
no_half = [t for t in after if decide[t]["no"] * 2 > decide[t]["adults"]]
no_deal = [e for e in ev if e["type"] in ("交換", "貸し借り", "市")]

# 138年のあとの出し入れ (村とよその村)
old = events(16590, START - 1)
last_loan = max(e["day"] for e in events(16000, START - 1) if e["type"] == "貸し借り")
last_ret = max(e["day"] for e in old if e["type"] == "確かめる" and "を返しに来た" in e["text"])

# 道の見張り・相談の止まり
path = {int(y): p for y, p in g11["path"].items()}
cons = [c for c in g7["consulted"] if c["why"] == "g11_path_c1"]
hold = g7["hold"]

# 地域のまとまり (G10 の条件 3 を、ならべて測る)
lg = g7["region"]["log"]
polity = {}
for y in [150] + YS:
    lv = [x for x in lg if x["kind"] == "段" and x["day"] == YE(y)][0]["levels"]
    top = max(lv, key=lambda v: (v["D"], v["n"]))
    n_all = by_day[YE(y)]["g7"]["settlements"] + 1  # 村もふくむ
    polity[y] = {"top": top["top"], "D": top["D"], "n": top["n"], "need": math.ceil(n_all / 2), "all": n_all, "village": top["village"]}
dem = [x for x in lg if x["kind"] == "求め" and START <= x["day"] <= END]

# 人・村の中
deaths = collections.Counter(d["cause"] for x in sv for d in x["deaths"])
names = {r["year"]: r["name"] for r in json.load(open(REC / "year_names.json", encoding="utf-8")) if 151 <= r["year"] <= 164 and r["name"]}
laws = json.load(open(REC / "laws.json", encoding="utf-8"))
props = [l for l in laws if l.get("proposed_day") and START <= l["proposed_day"] < END]  # END の日の集まりは閉じたあとのもの
adopted = [l for l in laws if l.get("adopted_day") and START <= l["adopted_day"] <= END]
last_adopt = max(l["adopted_day"] for l in laws if l.get("adopted_day"))
disp = [r for r in json.load(open(REC / "disputes.json", encoding="utf-8")) if START < r["day"] <= END]
sick = collections.Counter(Y(m["day"]) for m in g10["made"] if START < m["day"] <= END)
come = T("加わる"); gone = T("去る", "受け入れられず")
come = [e for e in come if e["day"] > START]

# トークン (年報)
tok, rep = {}, {}
for y in YS:
    t = (SOC / "reports" / f"year{y}.html").read_text(encoding="utf-8")
    tok[y] = int(re.search(r"使ったトークン: 約 [^(]*\(([\d,]+)\)", t).group(1).replace(",", ""))
    rep[y] = re.sub(r"\s+", " ", re.sub(r"<[^>]+>", " ", t))
# 回す道具のまちがいと、相談の止まりを解いた日 (git の記録の文。data のほかに読むのはここだけ)
LOG = subprocess.run(["git", "-C", str(SOC), "log", "--format=%s"], capture_output=True, text=True, check=True).stdout
nfile = lambda p: len(list(p.iterdir())) if p.is_dir() else None  # noqa: E731

F = {"seasons": seasons, "start": START, "end": END, "names": names, "tok": tok, "polity": polity,
     "offers_y": {y: off_y.get(y, 0) for y in YS}, "trust_year": Y(TRUST_DAY), "path": path,
     "goals": [["条件 1", "出し入れの半分以上 (1 年 4 回以上) を印のかたまりで", f"出し入れ {sum(led[y]['flows']['all'] for y in YS)} 回"],
               ["条件 2", "市の日に、よその人が来て替える市 1 年 2 回 × 2 年", "市の日は決まらなかった"],
               ["条件 3", "印のかたまりで貸し、量を字で書く年が 2 年", "印の貸し 0 回"],
               ["F1", "村の印を打った印のかたまりができた", f"作った数 {sum(led[y]['made'] for y in YS)} 個"],
               ["F2", "市が立った", "0 回"],
               ["F3", "印のかたまりで払った", "0 回"],
               ["F4", "印のかたまりの貸しを字で書いた", "0 回"]]}

CHECK = [
    ("期間 150年120日目〜164年120日目・14 年・56 季節", YD(START) == "150年120日目" and YD(END) == "164年120日目" and len(sv) == 56
     and g11["start"] == START and st["day"] == END and [e["text"] for e in T("フェーズ") if e["day"] == START] == [
         "G10 (鉄と広い国): 3 つの条件はそろわないまま、ここで閉じた", "フェーズ G11 (お金と市場) を始めた"]),
    ("いまは 164年120日目 (19799) の年の集まりで止まっている (相談)・お題は出ていて答えは 0",
     hold["why"] == "consult" and hold["day"] == END and hold["era"] == "G11" and nfile(DATA / "prompts/day19799/season") == 16
     and nfile(DATA / "answers/day19799/season") in (None, 0) and nfile(DATA / "answers/day19799/feeling") in (None, 0)),
    ("G11 の条件も F も 1 つも届いていない", g11["reached"] == {} and g11["c"] == {} and all(f"F{i} " in rep[164] for i in range(1, 5))),
    ("入った日 312 人・蓄え 409 万つかみ = 573 日分・作れる人 2 (ケセ19・ロワ33)・読める大人 9",
     fs["population"] == 312 and round(fs["store"]["草の種"] / 1e4) == 409 and fs["store_days"] == 573
     and c10["smiths"] == ["ケセ19", "ロワ33"] and len(c10["readers_alive"]) == 9
     and [e["day"] for e in T("試す", "印のある金属のかたまり", "作れる人: ケセ19・ロワ33")] == [START]),
    ("村の印「川と草の穂」151年30日目・5 / 大人 156", mark["text"] == "川と草の穂" and YD(mark["day"]) == "151年30日目"
     and mark["votes"].startswith("川と草の穂 5 / 大人 156") and len(mark_ev) == 1 and mark_ev[0]["day"] == mark["day"]),
    ("印のかたまりは 14 年で 0 個・出し入れ 0 回・市 0 回・印の貸し 0",
     sorted(led) == YS and all(led[y]["made"] == 0 and led[y]["flows"] == {"all": 0, "coin": 0} and led[y]["markets"] == 0
                               and led[y]["credit"] == {} for y in YS)
     and g11["made"] == [] and g11["coins"]["village"] == 0 and g11["markets"] == {} and g11["flows"] == {} and not no_deal),
    ("払い方「物」156年120日目 (42 / 165)・引きかえ「引きかえる」160年120日目 (71 / 175)",
     pay["choice"] == "物" and YD(pay["day"]) == "156年120日目" and pay["votes"].startswith("物 42 / 大人 165")
     and redeem["choice"] == "引きかえる" and YD(redeem["day"]) == "160年120日目" and redeem["votes"].startswith("引きかえる 71 / 大人 175")),
    ("市の日は決まらなかった (村の欄にも掟にも)", "market_day" not in g11 and g11["market"] is None
     and not any("market_day" in json.dumps(l, ensure_ascii=False) for l in props) and "市の日はまだ" in rep[164]),
    ("よその村との出し入れ: 新しい貸しは 138年 (16589) が最後・返しは 140年 (16889) まで",
     last_loan == 16589 and Y(last_loan) == 138 and last_ret == 16889 and Y(last_ret) == 140
     and not [e for e in old if e["type"] in ("交換", "貸し借り")]),
    ("直し 1: 157年120日目 (18959)・直し 2 (信頼): 159年120日目 (19199)・気持ちの席: 162年120日目 (19559)",
     g11["fix"]["day"] == 18959 and TRUST_DAY == 19199 and g7["feel_cap"]["day"] == 19559
     and [YD(e["day"]) for e in T("区切り", "お題を書き直した")] == ["157年120日目", "159年120日目", "162年120日目"]),
    ("申し出: 151〜159年に 2 回 (T257・T258)、信頼の直しのあと 160〜164年に 10 回 (T259〜T268)",
     before == ["T257", "T258"] and after == [f"T{i}" for i in range(259, 269)]
     and sorted(Y(offers[t]["day"]) for t in after) == [160, 160, 161, 161, 162, 162, 163, 163, 164, 164]),
    ("12 回とも受けなかった (受けた 0)", set(decide) == set(offers) and not any(d["ok"] for d in decide.values())),
    ("10 回の中身: 貸して 4 (1000〜2900 つかみ)・交換 6",
     kind_after == {"貸して": 4, "交換": 6} and min(loan_amt) == 1000 and max(loan_amt) == 2900),
    ("10 回の票: 受けないが多い 5・だれも決めない 4・村が多いが半分に届かない 1・受けないが半分をこえた 1",
     shape == {"受けないが多い": 5, "決めない": 4, "村が多いが半分に届かない": 1} and no_half == ["T266"]),
    ("道の見張り: 条件 1 を選べた人 158〜164年 0・条件 2 を選べた人 毎年 17〜22・選んだ人 152年から 0",
     sorted(path) == YS and all(path[y]["c1"] == 0 for y in range(158, 165)) and all(17 <= path[y]["c2"] <= 22 for y in YS)
     and all(path[y]["chose"] == 0 for y in range(152, 165)) and path[151]["chose"] == 1),
    ("相談の止まり 159〜164年の毎年 120日目 (6 回)", [YD(c["day"]) for c in cons] == [f"{y}年120日目" for y in range(159, 165)]),
    ("地域のまとまり: 北の大きな村 (N83) が段 4 (151年・159年から)、集落は 8〜9、要る数 10 (20 集落の半分)、村は外",
     all(polity[y]["top"] == "N83" for y in [150] + YS) and polity[150]["D"] == 3 and polity[151]["D"] == 4
     and all(polity[y]["D"] == 3 for y in range(152, 159)) and all(polity[y]["D"] == 4 for y in range(159, 165))
     and max(polity[y]["n"] for y in YS) == 9 and [y for y in YS if polity[y]["n"] == 9] == [155, 159, 160, 161]
     and all(polity[y]["n"] >= 8 for y in YS) and polity[164]["need"] == 10 and polity[164]["all"] == 20
     and all(polity[y]["village"] == "外" for y in YS)),
    ("村がまわりに求めた回 0", len(dem) > 0 and not any("V0" in x["who"] for x in dem)),
    ("人 312 → 348・生まれ 211・亡くなり 182 (小さいうち 96・病 72・年 13)・加わり 7・出た 0",
     ls["population"] == 348 and max(x["population"] for x in sv) == 348 and sum(len(x["births"]) for x in sv) == 211
     and sum(deaths.values()) == 182 and deaths["子"] == 96 and deaths["病"] == 72 and deaths["年"] == 13
     and sum(len(x["joined"]) for x in sv) == 7 and sum(len(x["left"]) for x in sv) == 0),
    ("よそから来た人: 受け入れ 2 回 (158・164年)・受けなかった 8 回", [Y(e["day"]) for e in come] == [158, 164] and len(gone) == 8),
    ("蓄え 573 → 478 日分 (402 万つかみ)・季節の蓄え 468〜735 日分・ききん 0", ls["store_days"] == 478 and round(ls["store"]["草の種"] / 1e4) == 402
     and min(x["store_days"] for x in sv) == 468 and max(x["store_days"] for x in sv) == 735),
    ("黒い金属の鎌 G11 で 24 本 (合わせて 162)", sum(sick.values()) == 24 and len(g10["made"]) == 162),
    ("作れる人 2 → 1 (153年) → 3 (163年)・読める大人 10 → 5", led[151]["smiths"] == 2 and led[153]["smiths"] == 1 and led[163]["smiths"] == 3
     and led[164]["smiths"] == 3 and led[151]["readers"] == 10 and led[164]["readers"] == 5),
    ("掟の案 35・採用 0 (最後の採用は 103年)・もめごと 10 みな「ゆるす」",
     len(props) == 35 and not adopted and Y(last_adopt) == 103 and len(disp) == 10 and all(r["verdict"] == "ゆるす" for r in disp)),
    ("年の名前 151〜163年 (13): 印・市・かたまりの名前は 0", sorted(names) == list(range(151, 164))
     and not any(w in n for n in names.values() for w in ("印", "市", "かたまり"))),
    ("トークン: 162年 16,254,120・163年 17,756,756 (上限 1,500 万をこえた)・164年 12,048,638・14 年で 約 1.83 億",
     tok[162] == 16254120 and tok[163] == 17756756 and tok[164] == 12048638 and [y for y in YS if tok[y] > 15_000_000] == [162, 163]
     and round(sum(tok.values()) / 1e6) == 183),
    ("気持ちの席: 162年120日目から 気持ち 80 → 53 人・代表 17 人",
     nfile(DATA / "prompts/day19439/feeling") == 80 and nfile(DATA / "prompts/day19559/feeling") == 53
     and nfile(DATA / "answers/day19559/feeling") == 53 and nfile(DATA / "answers/day19559/season") == 17),
    ("トークンの丸め: 162年 1,625 万・163年 1,776 万・164年 1,205 万", [round(tok[y] / 1e4) for y in (162, 163, 164)] == [1625, 1776, 1205]),
    ("道具のまちがい: 18569 (154年90日目) の歩を 2 回・17879 (148年120日目、G10 のうち)・19559 (162年120日目) の読みちがいで 70 人",
     "18599 日目の歩をもどした (回す役が 18569 日目の歩を 2 回動かし" in LOG and "17879 日目に 4 集落の集まりが答えなしで決まりで選ばれた" in LOG
     and "19559 日目に読む役が一覧をまとめ、代表と気持ちの 70 人をみなやり直した" in LOG
     and YD(18569) == "154年90日目" and YD(18599) == "154年120日目" and YD(17879) == "148年120日目" and 17879 < START and YD(19559) == "162年120日目"
     and nfile(DATA / "answers/day19559/season") + nfile(DATA / "answers/day19559/feeling") == 70),
    ("相談の止まりを解いた: 19199・19319・19439・19559・19679 (159〜163年)。19799 は解いていない",
     all(f"{d} 日目に相談の止まりを解" in LOG or f"{d} 日目の相談の止まりを解いた" in LOG for d in (19199, 19319, 19439, 19559, 19679))
     and "19799 日目の相談の止まりを解" not in LOG),
]
bad = [n for n, ok in CHECK if not ok]
for n, ok in CHECK:
    print(("OK  " if ok else "NG  ") + n)
if bad:
    sys.exit("記録と合わない文がある: " + " / ".join(bad))
out.write_text(json.dumps(F, ensure_ascii=False), encoding="utf-8")
print("facts:", out)
