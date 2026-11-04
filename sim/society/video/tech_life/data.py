"""テクノロジーが暮らしにどう出たかの動画 (tech_life) の数を、村の記録から読む (読むだけ。data には書かない)。
   python3 data.py <出力 facts.json>
   読むもの: sim/society/data/records/ (season_village・disputes・year_names)、archive.load_state で戻した出来事、
   state.json の era2.g7.g9 (赤い金属の道具を使った人日)。
   lines.json の文に書いた数は、下の CHECK で記録と合うか確かめる (合わないと止まる。記録が進んだら文を直す)。"""
import collections
import json
import re
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
SOC = HERE.parent.parent
DATA = SOC / "data"
REC = DATA / "records"
sys.path.insert(0, str(SOC))
import archive  # noqa: E402

out = Path(sys.argv[1])
ASOF = int(sys.argv[2]) if len(sys.argv) > 2 else 13799  # 文の数はこの日 (114年120日目) までの記録。村が進んでも同じ数になるように、これより後は読まない
Y = lambda d: d // 120  # noqa: E731  村の年 (1 年 120 日。d = 120*年 + 日目-1)
sv = [x for x in (json.loads(l) for l in open(REC / "season_village.jsonl", encoding="utf-8")) if x["season_end_day"] <= ASOF]
st = archive.load_state(str(DATA))
ev = [e for e in st["events"] if e["day"] <= ASOF]

# 季節ごとの列
seasons = [{"day": x["season_end_day"], "year": x["year"], "label": x["label"], "pop": x["population"],
            "grain": (x.get("eaten_share") or {}).get("草の種", 0) or 0,
            "nut": (x.get("eaten_share") or {}).get("木の実", 0) or 0,
            "goats": (x.get("goats") or {}).get("count", 0), "pests": x.get("pests") or 0,
            "pots": x.get("pots") or 0, "gini": x.get("wealth_gini"), "no_wealth": x.get("no_wealth"),
            "hh": x.get("households_with_members"), "homes": x.get("homes_built") or 0,
            "rain_out": x.get("rain_outside_person_nights") or 0, "rain_people": x.get("rain_outside_people") or 0}
           for x in sv]

# 出来事から年ごとに数える
thin, ex_ok, ex_no, rec_days, paid, stop = (collections.Counter() for _ in range(6))
first_seal = None
for e in ev:
    t, ty, y = e["text"], e["type"], Y(e["day"])
    if ty == "ヤギ" and "やせていなくなった" in t:
        thin[y] += int(re.search(r"ヤギ (\d+) 頭", t).group(1))
    elif ty == "交換":
        ex_ok[y] += 1
    elif ty == "よその村" and "受けなかった" in t:
        ex_no[y] += 1
    elif ty == "記録をつける":
        rec_days[y] += 1
    elif ty == "貢ぎ" and re.search(r"が 北の大きな村 に 草の種 \d+ つかみ を出した", t):
        paid[y] += int(re.search(r"草の種 (\d+) つかみ", t).group(1))
    elif ty == "崩れ" and "貢ぐのをやめた" in t:
        stop[y] += 1
    elif ty == "印" and first_seal is None:
        first_seal = e["day"]

g9 = st["era2"]["g7"]["g9"]
bronze_used = {int(k): v for k, v in g9["used"].items() if int(k) <= Y(ASOF)}
g9 = dict(g9, tools=[t for t in g9["tools"] if t["day"] <= ASOF], visits=[v for v in g9["visits"] if v["day"] <= ASOF],
          deals=[x for x in g9["deals"] if x <= ASOF])
d = [r for r in json.load(open(REC / "disputes.json", encoding="utf-8")) if r["day"] <= ASOF]
verdicts = collections.Counter(r["verdict"] or "収まらない" for r in d)
names = {r["year"]: r["name"] for r in json.load(open(REC / "year_names.json", encoding="utf-8")) if r.get("name") and r["decided_day"] <= ASOF}
last = sv[-1]

F = {"asof_day": last["season_end_day"], "asof": f"{Y(last['season_end_day'])}年{last['season_end_day'] % 120 + 1}日目",
     "seasons": seasons, "thin": thin, "ex_ok": ex_ok, "ex_no": ex_no, "rec_days": rec_days,
     "paid": paid, "stop": stop, "bronze_used": bronze_used,
     "bronze_tools": len(g9["tools"]), "verdicts": verdicts, "disputes": len(d), "year_names": names, "first_seal": first_seal}

# ---- 文に書いた数を確かめる ----
by = {s["label"]: s for s in seasons}
yr = lambda y, k: sum(s[k] for s in seasons if s["year"] == y) / max(1, sum(1 for s in seasons if s["year"] == y))  # noqa: E731
CHECK = [
    ("人は今 173 人", last["population"] == 173),
    ("12年の春 虫 5410・13年の夏 7727 (土器 0)", by["12年の春"]["pests"] == 5410 and by["13年の夏"]["pests"] == 7727 and by["13年の夏"]["pots"] == 0),
    ("14年の夏 虫 62・土器 340", by["14年の夏"]["pests"] == 62 and by["14年の夏"]["pots"] == 340),
    ("今の土器 15101", last["pots"] == 15101),
    ("13年の夏 雨の夜に外 11 人・のべ 66 夜 → 14年 0", by["13年の夏"]["rain_people"] == 11 and by["13年の夏"]["rain_out"] == 66 and by["14年の夏"]["rain_out"] == 0),
    ("家族の住まい 64 軒", seasons[-1]["homes"] == 64),
    ("ジニ 14年の夏 0.843・今 0.963", by["14年の夏"]["gini"] == 0.843 and last["wealth_gini"] == 0.963),
    ("持ち物のない家 27 / 31", last["no_wealth"] == 27 and last["households_with_members"] == 31),
    ("記録の日: 44〜46年に 870 日、55年のあと 0", rec_days[44] + rec_days[45] + rec_days[46] == 870 and max(rec_days) == 55),
    ("ききんの年 (53〜62年) の倉のもめごと 180 回", sum(1 for r in d if r["kind"] == "倉" and 53 <= Y(r["day"]) <= 62) == 180),
    ("もめごと 459・ゆるす 344・つぐなう 46・仲直り 18", len(d) == 459 and verdicts["ゆるす"] == 344 and verdicts["つぐなう"] == 46 and verdicts["仲直り"] == 18),
    ("貢ぎ 71〜89年 毎年 2340", all(paid[y] == 2340 for y in range(71, 90))),
    ("90年 456460 を払った", paid[90] == 456460),
    ("やめた年 92・95・101・103", sorted(stop) == [92, 95, 101, 103]),
    ("赤い金属 111年 84・112年 150・114年 270", bronze_used[111] == 84 and bronze_used[112] == 150 and bronze_used[114] == 270 and bronze_used[105] == 30),
    ("赤い金属の道具 11", len(g9["tools"]) == 11),
    ("遠くの運ぶ人 6 回・受けた 5", len(g9["visits"]) == 6 and len(g9["deals"]) == 5),
    ("ヤギ: 36年に 265 頭やせた", thin[36] == 265),
    ("年の名前 108・109・112 ヤギがやせた", "やせ" in names[108] and "やせ" in names[109] and "やせ" in names[112]),
    ("草の種 114年 9 割以上", yr(114, "grain") > 0.9),
    ("48年まで草の種は多くても 3 割ほど (0.34 未満)", all(yr(y, "grain") < 0.34 for y in range(4, 49))),
    ("49年から草の種が半分をこえる年が多い", sum(yr(y, "grain") > 0.5 for y in range(49, 115)) > 50),
    ("交換を受けなかった 36年から", min(ex_no) == 36),
    ("家の印 29年60日目", first_seal == 3539),
    ("108〜112年のうち 4 つの年の名前に「やせ」", sum("やせ" in names.get(y, "") for y in range(108, 113)) == 4),
    ("36年からよその村の申し出を受けなかった 147 回", sum(ex_no.values()) == 147),
    ("黒曜石を取りに北の村へ 5 回 (41〜44年)", sorted(Y(e["day"]) for e in ev if e["type"] == "交換に行く" and "交換に行った" in e["text"]) == [41, 41, 43, 43, 44]),
    ("罰のある掟は 34年にでき 35年になくなった (L162)", any(l["id"] == "L162" for l in st["laws"])),
]
bad = [n for n, ok in CHECK if not ok]
for n, ok in CHECK:
    print(("OK  " if ok else "NG  ") + n)
if bad:
    sys.exit("記録と合わない文がある: " + " / ".join(bad))
out.write_text(json.dumps(F, ensure_ascii=False), encoding="utf-8")
print("facts:", out, F["asof"])
