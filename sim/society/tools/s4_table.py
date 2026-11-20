"""Society 4.0 (分業と町) の決まりの村の表 (2026-11-20。docs/society_phase/S4_check.md)

  PYTHONUTF8=1 python3.13 sim/society/tools/s4_table.py --out <lab_village.py run の --out>

lab_village.py の結果 (S4R_<束>_s<種>.json) の年ごとの s4_row から、f1〜f5 と町の家・掘り場・交換・蓄えの表 (Markdown) を書く。
"""
import argparse
import json
from pathlib import Path


def pct(x):
    return f"{round(x * 100, 1)}%"


def ok(b):
    return "○" if b else "×"


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", required=True)
    a = ap.parse_args()
    print("| 束 | 種 | 年 | f1 食べ物でない仕事 | f2 新しい燃える石 (火と力の割合 × 新しい石の分) | f3 町の家 (180 人日以上) | f4 交換のねうち | "
          "町の仕事 (人日) | 受け分 | 掘り場 | 掘った石 | 替えた石 | 村の倉の板 | 蓄えの最少 | ききん | 人 | f1 f2 f3 f4 f5 | 止まり |")
    print("|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|")
    for f in sorted(Path(a.out).glob("S4R_*.json")):
        res = json.loads(f.read_text(encoding="utf-8"))
        for row in res["rows"]:
            r = row.get("s4_row")
            if not r:
                continue
            stops = "・".join(c["why"] for c in row.get("s4_consulted", []) if c.get("year") == r["year"]) or "-"
            print(f"| {res['bundle']} | {res['seed']} | {r['year']} | {pct(r['f1_share'])} ({r['nonfood']}/{r['worked']}) | "
                  f"{pct(r['f2_share'])} ({pct(r['coal_share'])} × {pct(r['own_share'])}) | {r['town_ok']} (町の家 {r['town']}・大人 {r['town_people']}) | "
                  f"{r['trade_value']:,} | {r['town_days']:,} | {r['town_pay']:,} | {r['pit']} | {r['coal_dug']:,} kg | {r['coal_bought']:,} kg | {r['planks']:,} | "
                  f"{r['store_min']} 日 | {r['famine']} | {r['pop']} | {ok(r['f1_like'])} {ok(r['f2_like'])} {ok(r['f3_like'])} {ok(r['f4_like'])} {ok(r['f5_ok'])} | {stops} |")


if __name__ == "__main__":
    main()
