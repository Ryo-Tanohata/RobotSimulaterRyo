"""Society 3.0 案 A の決まりの村の結果を表にする (2026-11-17。docs/society_phase/S3_check.md 2.)

  PYTHONUTF8=1 python3.13 sim/society/tools/s3_table.py --out /tmp/s3work/runs [--years-md 年ごとの表.md]

- lab_village.py の結果 (<世界>_<束>_s<種>.json) の年ごとの列 s3_row (s3.row_of) を読んで、まとめの表 (Markdown) を出す。
"""
import argparse
import json
from pathlib import Path

WORLDS = ("S30", "S3A", "S3B", "S3C", "S3D", "S3X")
BUNDLES = ("S3B0", "S3B1")


def load(out):
    res = []
    for f in sorted(Path(out).glob("S3*_S3B*_s*.json")):
        res.append(json.loads(f.read_text(encoding="utf-8")))
    return res


def yd(d):
    return f"{d // 120}年" if d is not None else "-"


def summary(res):
    rows = ["| 世界 | 束 | 種 | e1 | e2 | e3 | e4 | e5 を割った年 | 入口 | 掘った (年平均 kg) | 掘った分の割合 (最後の年) | 燃える石の割合 (最後の年) | 8 人の日 (年平均) | 持ち場 (終わり) | 見習いを終えた (合わせ) | まき集め (年平均 人日) | 蓄えのいちばん少ない日 | ききん | 人 (はじめ → 終わり) |",
            "|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|"]
    key = {w: i for i, w in enumerate(WORLDS)}
    for r in sorted(res, key=lambda r: (key.get(r["world"], 9), r["bundle"], r["seed"])):
        ys = [x["s3_row"] for x in r["rows"] if x.get("s3_row")]
        if not ys:
            continue
        last = r["rows"][-1]
        e = last.get("s3_e") or {}
        n = len(ys)
        rows.append(f"| {r['world']} | {r['bundle']} | {r['seed']} | " + " | ".join(yd(e.get(k)) for k in ("e1", "e2", "e3", "e4"))
                    + f" | {'・'.join(map(str, last.get('s3_e5_broken') or [])) or 'なし'} | {'ある' if last.get('s3_entrance') else 'ない'} | "
                    f"{round(sum(y['coal_dug'] for y in ys) / n):,} | {round(ys[-1]['dug_share'] * 100)}% | {round(ys[-1]['coal_share'] * 100, 1)}% | "
                    f"{round(sum(y['big'] for y in ys) / n, 1)} | {ys[-1]['posts']} | {sum(y['appr_done'] for y in ys)} | {round(sum(y['fire_pd'] for y in ys) / n):,} | "
                    f"{min(y['store_min'] for y in ys)} | {sum(y['famine'] for y in ys)} | {ys[0]['pop_prev']} → {ys[-1]['pop']} |")
    return "\n".join(rows)


def years(res, seed=0):
    rows = ["| 世界 | 束 | 年 | 掘った kg | 燃やした kg | 掘った分 | 燃える石の割合 | 村の倉 kg | 家の倉 kg | まき集め 人日 (浮いた) | 8 人の日 | 持ち場 | 見習い 終えた (読める人が教えた) | 選んだ答える人 | 交換 | 蓄え (いちばん少ない) | ききん | 人 | e1〜e4 のよう / e5 |",
            "|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|"]
    key = {w: i for i, w in enumerate(WORLDS)}
    for r in sorted(res, key=lambda r: (key.get(r["world"], 9), r["bundle"])):
        if r["seed"] != seed:
            continue
        for x in r["rows"]:
            y = x.get("s3_row")
            if not y:
                continue
            sold = sum(v.get("板", 0) for v in y["sold"].values())
            coal = sum(v.get("燃える石", 0) for v in y["sold"].values())
            rows.append(f"| {r['world']} | {r['bundle']} | {y['year']} | {round(y['coal_dug']):,} | {round(y['coal_burned']):,} | {round(y['dug_share'] * 100)}% | "
                        f"{round(y['coal_share'] * 100, 1)}% | {y['coal_stock']:,} | {y['house_coal']:,} | {y['fire_pd']:,} ({y['saved_pd']:,}) | {y['big']} | {y['posts']} | "
                        f"{y['appr_done']} ({y['appr_reader']}) | {y['chose']} / {y['answerers']} | 板 {sold}・石 {coal} kg | {y['store_min']} | {y['famine']} | {y['pop']} | "
                        + "".join("○" if y[f"{k}_like"] else "×" for k in ("e1", "e2", "e3", "e4")) + f" / {'○' if y['e5_ok'] else '×'} |")
    return "\n".join(rows)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", required=True)
    ap.add_argument("--seed", type=int, default=0, help="年ごとの表の種")
    a = ap.parse_args()
    res = load(a.out)
    print(summary(res))
    print()
    print(years(res, a.seed))


if __name__ == "__main__":
    main()
