"""「Society 3.0 これまで」(200年120日目〜232年の終わり) の動画の数を、村の記録から読む (読むだけ。data には書かない)。
   python3.13 data.py <出力 facts.json>
   読むもの: sim/society/data/records/ (season_village・year_names)、state.json の era2.g7 (g15 の push・after、s3・s4・i4・p4、consulted)、
   sim/society/reports/year200〜232.html (年報)、docs/society_phase/ (G15_push・S3_check・S4_check・I4_design・I4_check・P4_design)、
   sim/society/HANDOFF.md と git log の文。
   lines.json の文と図に出す数は、下の CHECK で記録と合うか確かめる (合わないと止まる)。
   Society 3.0 は 200年120日目 (24119) に後押しを止めたところから数え、232年の終わり (27959) までを読む。
   村は動いている (state.json は先へ進む) ので、年ごとの行は 232年までだけを使い、233年より後は見ない。
   年は 年 = 日 // 120 (年報と同じ)。コードと state の文には前の呼び名 (Society 4.0 …) が残るが、図と字幕には今の呼び名 (Society 3.0 フェーズ N) だけを出す。"""
import collections
import json
import re
import subprocess
import sys
import time
from pathlib import Path

HERE = Path(__file__).resolve().parent
SOC = HERE.parent.parent
ROOT = SOC.parent.parent
DATA = SOC / "data"
REC = DATA / "records"
DOC = ROOT / "docs/society_phase"
START, END = 24119, 27959
YD = lambda d: f"{d // 120}年{d % 120 + 1}日目"  # noqa: E731
YS = list(range(201, 233))      # Society 3.0 の年 (年報 201〜232)
out = Path(sys.argv[1])


def load(p):  # 村のワークフローが書きかえている最中なら、少し待って読み直す
    for _ in range(20):
        try:
            return json.loads(p.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            time.sleep(3)
    sys.exit(f"読めない: {p}")


sv_all = []
for l in open(REC / "season_village.jsonl", encoding="utf-8"):
    try:
        sv_all.append(json.loads(l))
    except json.JSONDecodeError:
        pass  # 書きかけの最後の行
by_day = {x["season_end_day"]: x for x in sv_all}
sv = [x for x in sv_all if START < x["season_end_day"] <= END]
st = load(DATA / "state.json")
g7 = st["era2"]["g7"]
g15, s3, s4, i4, p4 = g7["g15"], g7["s3"], g7["s4"], g7["i4"], g7["p4"]
push, after = g15["push"], g15["after"]
iy = lambda d, lo=0, hi=232: {int(k): v for k, v in d.items() if lo <= int(k) <= hi}  # noqa: E731
r3, r4, ri, rp, ra = iy(s3["rows"]), iy(s4["rows"]), iy(i4["rows"]), iy(p4["rows"]), iy(after["rows"])

# 年報 (200〜232年)
rep, tok = {}, {}
for y in [200] + YS:
    t = (SOC / "reports" / f"year{y}.html").read_text(encoding="utf-8")
    t = re.sub(r"\s+", " ", re.sub(r"<[^>]+>", " ", re.sub(r"<(script|style).*?</\1>", "", t, flags=re.S)))
    rep[y] = t
    tok[y] = int(re.search(r"使ったトークン: 約 [^(]*\(([\d,]+)\)", t).group(1).replace(",", ""))
r_pop = {y: tuple(map(int, re.search(r"人数 \(年のはじめ → 終わり\) (\d+) → (\d+) 人", rep[y]).groups())) for y in YS}
tok = {y: tok[y] for y in YS}

# 年ごとの数 (201〜203年は後押しなしの確かめの行、204年からは S3 の行。S3 の行は 232年まで続いている)
coal = {y: ra[y]["coal_dug"] for y in (201, 202, 203)} | {y: r3[y]["coal_dug"] for y in range(204, 233)}
diggers = {y: r3[y]["diggers"] for y in range(204, 233)}
big = {y: ra[y]["big"] for y in (201, 202, 203)} | {y: r3[y]["big"] for y in range(204, 233)}
posts = {y: r3[y]["posts"] for y in range(204, 233)}
share = {200: after["base"]["coal_share"]} | {y: ra[y]["coal_share"] for y in (201, 202, 203)} | {y: r3[y]["coal_share"] for y in range(204, 233)}
share = {y: round(100 * v, 1) for y, v in share.items()}
fire = {y: r3[y]["fire_pd"] for y in range(204, 233)}
nonfood = {y: round(100 * r4[y]["f1_share"], 1) for y in range(216, 233)}
asked = {int(y): {"yes": len(a["yes"]), "no": len(a["no"]), "quiet": a["quiet"]} for y, a in s4["asked"].items()}
readers = {y: {"n": ri[y]["readers"], "adults": ri[y]["adults"], "pct": round(100 * ri[y]["i1_share"], 1)} for y in range(225, 233)}
notes = {y: {"n": ri[y]["notes"], "houses": ri[y]["note_houses"]} for y in range(225, 233)}
used = {y: ri[y]["used"] for y in range(225, 233)}
i3 = {y: round(100 * ri[y]["i3_share"], 2) for y in range(225, 233)}
note227 = [n for n in i4["notes"]["227"] if n["house"] == "ハソ4の家" and n["day"] == 27239][0]
seasons = [{"day": x["season_end_day"], "pop": x["population"], "store_days": x["store_days"]} for x in [by_day[START]] + sv]
dc = collections.Counter(d["cause"] for x in sv for d in x["deaths"])
P = {"births": sum(len(x["births"]) for x in sv), "deaths": sum(dc.values()), "joined": sum(len(x["joined"]) for x in sv),
     "left": sum(len(x["left"]) for x in sv)}
yn = json.load(open(REC / "year_names.json", encoding="utf-8"))
names = {r["year"]: r["name"] for r in yn if 201 <= r["year"] <= 232 and r["name"]}
work_names = sorted(y for y, n in names.items() if "のこ" in n or "板" in n)
food_names = sum(1 for n in names.values() if any(w in n for w in ("刈", "実", "みのり", "畑", "ヤギ", "採集", "種", "蓄え")))
LOG = subprocess.run(["git", "-C", str(SOC), "log", "--format=%s"], capture_output=True, text=True, check=True).stdout
HO = (SOC / "HANDOFF.md").read_text(encoding="utf-8")
G15P = (DOC / "G15_push.md").read_text(encoding="utf-8")
S3C = (DOC / "S3_check.md").read_text(encoding="utf-8")
S4C = (DOC / "S4_check.md").read_text(encoding="utf-8")
I4D = (DOC / "I4_design.md").read_text(encoding="utf-8")
I4C = (DOC / "I4_check.md").read_text(encoding="utf-8")
P4D = (DOC / "P4_design.md").read_text(encoding="utf-8")
cons = {c["why"]: c for c in g7["consulted"] if START <= c.get("day", 0) <= END}

F = {"start": START, "end": END, "seasons": seasons, "tok": tok, "names": names, "work_names": work_names,
     "coal": coal, "big": big, "posts": posts, "share": share, "nonfood": nonfood, "asked": asked,
     "readers": readers, "notes": notes, "used": used,
     "phases": [["201〜203年", "後押しなしの確かめ (村の人だけで 3 年)", "作業場 0 日・掘った石 0 kg"],
                ["204〜215年", "フェーズ 1 (案 A): 見える仕事・持ち場・見習い", f"{YD(cons['s3_entrance']['day'])} に入口"],
                ["216〜224年", "フェーズ 2: 分業と町", "町の家 0 のまま閉じた"],
                ["225〜231年", "フェーズ 3: 読み書きと知らせ板", f"読める大人 {readers[225]['pct']:.0f}% → {readers[231]['pct']:.0f}%"],
                ["232年〜", "フェーズ 4: 頼み書きと町", "続いている (232年は頼み書き 0)"]]}

CHECK = [
    ("範囲: 200年120日目 (24119)〜232年120日目 (27959)・128 季節・年報 201〜232年",
     YD(START) == "200年120日目" and YD(END) == "232年120日目" and len(sv) == 128 and all(f"通しの日 {y * 120}〜{y * 120 + 119}" in rep[y] for y in YS)),
    ("G15: 193年60日目に入った・198年60日目から作る側の後押し・200年120日目に入口 (e3・e4 199年120日目、e1 200年120日目)",
     YD(g15["start"]) == "193年60日目" and YD(push["day"]) == "198年60日目" and g7["ends"]["G15"] == {"day": START, "why": "entrance"}
     and YD(g15["e"]["e1"]) == "200年120日目" and YD(g15["e"]["e3"]) == YD(g15["e"]["e4"]) == "199年120日目"
     and "G15「水の作業場と燃える石」" in HO and "燃える石" in rep[200]),
    ("Society 3.0 は工業の社会 (日本の区分)", "3.0 工業" in S4C),
    ("後押しを 200年120日目に止め、201〜203年を村の人だけで回した: 作業場の 8 人の日 0・掘った石 0・倉の石 約 16.9 万 → 約 3.2 万 kg",
     push["ended"]["day"] == START and after["day"] == START and (after["from_year"], after["to_year"]) == (201, 203)
     and all(big[y] == 0 and coal[y] == 0 and ra[y]["chose"] == 0 for y in (201, 202, 203))
     and round(after["base"]["coal_stock"] / 1e4, 1) == 16.9 and round(ra[203]["coal_stock"] / 1e4, 1) == 3.2
     and "後押しの年にためた倉の石を燃やした" in G15P),
    ("フェーズ 1 (案 A) は 203年の終わり (24479) から・204年から数える・本人「お任せします」・部分 a〜d (家の倉に 2 割・持ち場・見習い 20 日)",
     s3["day"] == 24479 and YD(24479) == "203年120日目" and s3["start_year"] == 204 and s3["words"] == "お任せします" and s3["parts"] == ["a", "b", "c", "d"]
     and "掘った石の 2 割を家の倉に" in rep[232] and "のこ番・槌番・帳面番・頭" in rep[232] and "見習い (20 日で持ち場)" in rep[232]),
    ("石掘り: 206年 33 人 (204,000 kg)・207年 25 人 (156,000 kg)・204〜208年で 約 43 万 kg",
     diggers[206] == 33 and coal[206] == 204000 and diggers[207] == 25 and coal[207] == 156000
     and sum(coal[y] for y in range(204, 209)) == 432000),
    ("作業場の 8 人の日: 204〜208年 0 → 209年 90 → 210〜232年 毎年 120・わけは板の返り 0・本人「得が出るようにする」・持ち場 232年 48 人",
     all(big[y] == 0 for y in range(201, 209)) and big[209] == 90 and all(big[y] == 120 for y in range(210, 233))
     and "わけは「板の返りが 0」で、209年から人がそろうと板が多くひけるようにした" in S3C and "「得が出るようにする」" in LOG
     and posts[209] == 17 and posts[232] == 48 and max(posts.values()) == 48),
    ("212年30日目にフェーズ 1 の入口 (e1・e2 210年120日目・e4 211年120日目)・214・215年は燃える石が半分を切り、215年 12%",
     YD(cons["s3_entrance"]["day"]) == "212年30日目" and YD(s3["e"]["e1"]) == YD(s3["e"]["e2"]) == "210年120日目" and YD(s3["e"]["e4"]) == "211年120日目"
     and not r3[214]["e1_like"] and not r3[215]["e1_like"] and round(share[215]) == 12 and share[214] < 50 and r3[215]["coal_stock"] <= 1),
    ("フェーズ 1 の 12 年: 人 527 → 604・ききん 0・いちばん少ない蓄え 205年の 90 日分・石が尽きても水の道の手入れを先に",
     s3["pop0"] == 527 and r3[215]["pop"] == 604 and all(r3[y]["famine"] == 0 for y in range(204, 216))
     and min(r3[y]["store_min"] for y in range(204, 216)) == 90 == r3[205]["store_min"]
     and "食べ物を守る水の道の手入れ" in S3C and "返りがお題に見える仕事" in S3C),
    ("フェーズ 2 (分業と町) は 215年の終わり (25919) から・本人「次のフェーズまで進めて下さい」・町の家・掘り場・川下の町の市・目安 22%・5 家・3 万つかみ",
     s4["day"] == 25919 and YD(25919) == "215年120日目" and s4["words"] == "次のフェーズまで進めて下さい" and s4["parts"] == ["a", "b", "c"]
     and "町の家・掘り場・川下の町の市" in rep[232] and "**22% 以上**" in (DOC / "S4_design.md").read_text(encoding="utf-8")
     and "**5 つ以上**" in (DOC / "S4_design.md").read_text(encoding="utf-8") and "**3 万つかみ以上**" in (DOC / "S4_design.md").read_text(encoding="utf-8")),
    ("216〜221年: 町の家 0・町の道を選んだ答える人 のべ 3 人 (みな同じ 1 人)",
     all(r4[y]["town"] == 0 for y in range(216, 225)) and sum(s4["chose"][str(y)]["chose"] for y in range(216, 222)) == 3
     and len({w for y in range(216, 222) for w in s4["chose"][str(y)]["who"]}) == 1),
    ("222〜224年 年の集まりで町の家を聞いた (本人「年の集まりで聞く」): 出す 0・出さない 33・23・34 (のべ 90)・書かない 7・14・8",
     sorted(asked) == [222, 223, 224] and all(asked[y]["yes"] == 0 for y in asked) and [asked[y]["no"] for y in (222, 223, 224)] == [33, 23, 34]
     and [asked[y]["quiet"] for y in (222, 223, 224)] == [7, 14, 8] and "本人の選び「年の集まりで聞く」" in HO),
    ("224年の終わり (26999) に閉じた・問いを読んだうえで出さない・222〜224年の蓄え 350 日分をこえる・22% をこえたのは 223年だけ (22.1%)",
     s4["closed"] == 26999 and YD(26999) == "224年120日目" and "**問いを読んだうえで出さない**と決めた" in S4C
     and all(r3[y]["store_min"] > 350 for y in (222, 223, 224)) and [y for y in range(216, 225) if nonfood[y] >= 22] == [223] and nonfood[223] == 22.1),
    ("呼び名の直し (227年の終わり): 本人のたずね・3.0 の入口には届いていない・Society 3.0 フェーズ 3 と呼び直した",
     "いつのまに society3.0 が終わりましたか？" in I4D and "**Society 3.0 フェーズ 3 (読み書きと知らせ板)** と呼び直す" in I4D
     and "3.0 (工業の社会) の入口 (分業と町) には届いていない" in I4D and "読み書きと知らせ板の呼び名を Society 3.0 フェーズ 3 に直した" in LOG),
    ("フェーズ 3 は 224年の終わり (26999) から・225年から数える・知らせは 60 字・1 季節 1 枚・子は 1 日 6 人まで・30 日で読める・10〜14 歳",
     i4["day"] == 26999 and i4["start_year"] == 225 and "`notice` (60 字。家に読める大人がいるとき。1 家 1 季節 1 枚)" in HO
     and "キャンプの 10〜14 歳の子を 1 日 6 人まで" in HO and "子は 30 日で読める" in HO),
    ("読める大人: 225年 7% (25 人) → 231年 26% (99 人)・目安 25%・232年 28% (108 人)・10〜14 歳の子は 228年からみな読める",
     round(readers[225]["pct"]) == 7 and readers[225]["n"] == 25 and round(readers[231]["pct"]) == 26 and readers[231]["n"] == 99
     and round(readers[232]["pct"]) == 28 and readers[232]["n"] == 108 and 231 in i4["f_years"]["i1"] and "25% 以上" in I4D
     and "10〜14 歳の子は 228年からみな読める" in I4C),
    ("知らせ: 225〜231年 2・2・5・7・6・3・8 枚。231年 8 枚 4 家 (いちばん多い)・232年 5 枚 3 家",
     [notes[y]["n"] for y in range(225, 232)] == [2, 2, 5, 7, 6, 3, 8] and notes[231] == {"n": 8, "houses": 4}
     and max(notes[y]["n"] for y in notes) == 8 and notes[232] == {"n": 5, "houses": 3}),
    ("227年夏の知らせ (ハソ4の家・書いたのは ケセ96)・知らせの中身を話で使った回 227年 20・229年 28・232年 46 (いちばん多い)",
     note227["text"] == "ヤギは245頭で草の140頭を大きくこえた。よそのヤギは受けず、オスからつぶして干し肉にしよう" and note227["writer"] == "ケセ96"
     and used[227] == 20 and used[229] == 28 and used[232] == 46 and max(used.values()) == 46
     and "知らせは段取り (ヤギの数・種の量・水の道) に使われ" in I4C),
    ("字の仕事: 目安 4%・いちばん多い年 231年 1.7%・229年の相談で決まりを変えずに 231年の終わりまで",
     "4% 以上" in I4D and max(i3[y] for y in range(225, 232)) == i3[231] and round(i3[231], 1) == 1.7 and i4["f_years"]["i3"] == []
     and "**決まりを変えずに、あと 2 年 (231年の終わりまで) 続けて見る**" in I4C and cons["i4_years_229"]["day"] == 27599),
    ("230年: 掘った人 0・燃える石は火と力の 3%・まき集め 2,576 人日",
     coal[230] == 0 and diggers[230] == 0 and round(share[230]) == 3 and fire[230] == 2576 and "まき集め 2576 人日" in rep[232]),
    ("フェーズ 4 は 231年の終わり (27839) から・232年から数える・1 季節 10 日まで・村の倉の石 0 kg・23 家の倉に 45,073 kg",
     p4["day"] == 27839 and YD(27839) == "231年120日目" and p4["start_year"] == 232 and "1 人 1 季節 10 日まで頼みの仕事" in HO
     and "家の倉には 23 家に合わせて 45,073 kg の石がある" in P4D and r3[230]["house_coal"] == 45073 and r3[230]["coal_stock"] == 0
     and "村をフェーズ 4 (頼み書きと町) に切りかえた (231年の終わり)" in LOG),
    ("232年: 頼み書き 0・受けた頼み 0・果たした 0",
     rp[232]["wrote"] == 0 and rp[232]["took"] == 0 and rp[232]["done"] == 0 and "この年の頼み書き: なし" in rep[232]
     and all(x["wrote"] == [] for y, x in p4["yr"].items() if int(y) <= 232)),
    ("人 500 → 700・生まれ 1,010・亡くなり 908・加わり 98・出た 0・ききん 0 (どの年報も「飢えはなかった」)",
     seasons[0]["pop"] == 500 and seasons[-1]["pop"] == 700 and P == {"births": 1010, "deaths": 908, "joined": 98, "left": 0}
     and r_pop[201][0] == 500 and r_pop[232][1] == 700 and all("飢えはなかった" in rep[y] for y in YS)
     and min(s["store_days"] for s in seasons) == 90),
    ("年の名前 201〜232年: 食べ物 (刈り入れ・実り・畑・ヤギなど) がほとんど・のこ / 板の名前は 226・228・230年",
     sorted(names) == YS and work_names == [226, 228, 230] and names[226] == "のこ番の年" and names[230] == "板ひきの年" and food_names >= 26),
    ("トークン: 32 の年報で 約 3 億 8,560 万 (203年は途中から数えた分だけ・214年は年報の数が約 215 万と少ない)・ほかの年は 1,500 万の下",
     round(sum(tok.values()) / 1e5) == 3856 and tok[203] == 6342609 and "203年のトークンは、途中で入れ物が止まり" in G15P
     and tok[214] == 2147170 and min(tok.values()) == tok[214] and all(v < 15_000_000 for v in tok.values())),
    ("相談は 3 年ごと・1 回目は 234年の終わり", "3 年ごと。234年の終わりが 1 回目" in HO),
    ("字幕と読みに前の呼び名 (4.0) を出さない", "4.0" not in (HERE / "lines.json").read_text(encoding="utf-8")),
]
bad = [n for n, ok in CHECK if not ok]
for n, ok in CHECK:
    print(("OK  " if ok else "NG  ") + n)
F["food_names"] = food_names
F["tok_sum"] = sum(tok.values())
if bad:
    sys.exit("記録と合わない文がある: " + " / ".join(bad))
out.write_text(json.dumps(F, ensure_ascii=False), encoding="utf-8")
print("facts:", out)
