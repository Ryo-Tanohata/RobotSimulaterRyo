"""実験 B の答えを数える (標準ライブラリだけ)。

/tmp/B_answers/<id>.json (中身は {"choice": ..., "why": ...}。前後に文があってもよい。はじめの {...} を読む) を
manifest.csv とつなぎ、お題 × モデル × 前置き ごとに、手ごとの選んだ割合と Wilson 95% の幅を出す。
書き出し: docs/research/data/B_answers.csv。標準出力: markdown の表と、無い・読めない・手にない答えの数。
python3 analyze.py [--answers /tmp/B_answers] [--out ../B_answers.csv]
"""
import argparse
import csv
import json
import math
import re
from collections import Counter, defaultdict
from pathlib import Path

HERE = Path(__file__).resolve().parent
Z = 1.959964


def wilson(k, n):
    if n == 0:
        return (float("nan"), float("nan"))
    p = k / n
    d = 1 + Z * Z / n
    c = (p + Z * Z / (2 * n)) / d
    h = Z * math.sqrt(p * (1 - p) / n + Z * Z / (4 * n * n)) / d
    return (max(0.0, c - h), min(1.0, c + h))


def first_object(text):
    """はじめの { から、釣り合う } までを返す (文字列の中の括弧は数えない)。なければ None"""
    i = text.find("{")
    while i != -1:
        depth, in_str, esc = 0, False, False
        for j in range(i, len(text)):
            ch = text[j]
            if in_str:
                if esc:
                    esc = False
                elif ch == "\\":
                    esc = True
                elif ch == '"':
                    in_str = False
            elif ch == '"':
                in_str = True
            elif ch == "{":
                depth += 1
            elif ch == "}":
                depth -= 1
                if depth == 0:
                    try:
                        return json.loads(text[i:j + 1])
                    except json.JSONDecodeError:
                        break
        i = text.find("{", i + 1)
    return None


def norm(s):
    return re.sub(r"[\s「」『』\"'“”‘’。、.]", "", str(s))


def match(choice, labels):
    """choice を手の名前に合わせる。そのまま合えばそれ、合わなければ choice に含まれるいちばん長い名前 (1 つに決まるときだけ)"""
    c = norm(choice)
    by = {norm(l): l for l in labels}
    if c in by:
        return by[c]
    hits = [l for l in labels if norm(l) and norm(l) in c]
    if hits:
        best = max(hits, key=lambda l: len(norm(l)))
        if sum(1 for l in hits if len(norm(l)) == len(norm(best))) == 1 and all(norm(l) in norm(best) for l in hits):
            return best
    return None


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--answers", default="/tmp/B_answers")
    ap.add_argument("--manifest", default=str(HERE / "manifest.csv"))
    ap.add_argument("--out", default=str(HERE.parent / "B_answers.csv"))
    a = ap.parse_args()

    rows = list(csv.DictReader(open(a.manifest, encoding="utf-8")))
    labels = {}
    for r in rows:
        labels.setdefault(r["vignette"], sorted(r["option_order"].split("|")))
    cell = defaultdict(Counter)          # (v, model, framing) -> 手 -> 数
    bad = defaultdict(Counter)           # (v, model, framing) -> missing / malformed / invalid
    first = defaultdict(lambda: [0, 0])  # (v, model, framing) -> [はじめに出た手を選んだ数, 読めた数]
    bad_ids = defaultdict(list)
    for r in rows:
        key = (r["vignette"], r["model"], r["framing"])
        p = Path(a.answers) / f"{r['id']}.json"
        if not p.exists():
            bad[key]["missing"] += 1
            bad_ids["missing"].append(r["id"])
            continue
        obj = first_object(p.read_text(encoding="utf-8", errors="replace"))
        if not isinstance(obj, dict) or "choice" not in obj:
            bad[key]["malformed"] += 1
            bad_ids["malformed"].append(r["id"])
            continue
        lab = match(obj["choice"], labels[r["vignette"]])
        if lab is None:
            bad[key]["invalid"] += 1
            bad_ids["invalid"].append(f"{r['id']}={obj['choice']!r}")
            continue
        cell[key][lab] += 1
        first[key][1] += 1
        first[key][0] += lab == r["option_order"].split("|")[0]

    keys = sorted({(r["vignette"], r["model"], r["framing"]) for r in rows},
                  key=lambda k: (k[0], ["haiku", "sonnet", "opus"].index(k[1]) if k[1] in ("haiku", "sonnet", "opus") else 9, k[2]))
    out = []
    for k in keys:
        n = sum(cell[k].values())
        for lab in labels[k[0]]:
            x = cell[k][lab]
            lo, hi = wilson(x, n)
            out.append({"vignette": k[0], "model": k[1], "framing": k[2], "option": lab, "k": x, "n": n,
                        "rate": round(x / n, 4) if n else "", "lo95": round(lo, 4) if n else "", "hi95": round(hi, 4) if n else "",
                        "missing": bad[k]["missing"], "malformed": bad[k]["malformed"], "invalid": bad[k]["invalid"],
                        "first_listed_rate": round(first[k][0] / first[k][1], 4) if first[k][1] else ""})
    Path(a.out).parent.mkdir(parents=True, exist_ok=True)
    with open(a.out, "w", newline="", encoding="utf-8") as fh:
        w = csv.DictWriter(fh, fieldnames=list(out[0]))
        w.writeheader()
        w.writerows(out)

    print(f"# 実験 B の答え ({len(rows)} 呼び出し。答えのフォルダ {a.answers})\n")
    tot = Counter()
    for k in keys:
        tot.update(bad[k])
    print(f"読めた答え {sum(sum(c.values()) for c in cell.values())} / 無い {tot['missing']} / 読めない {tot['malformed']} / 手にない {tot['invalid']}\n")
    for v in sorted(labels):
        print(f"## {v}\n")
        print("| モデル | 前置き | n | " + " | ".join(labels[v]) + " | はじめの手 | 無/壊/外 |")
        print("|---|---|---|" + "---|" * len(labels[v]) + "---|---|")
        for k in [k for k in keys if k[0] == v]:
            n = sum(cell[k].values())
            cells = []
            for lab in labels[v]:
                x = cell[k][lab]
                if n:
                    lo, hi = wilson(x, n)
                    cells.append(f"{x / n:.0%} ({lo:.0%}–{hi:.0%})")
                else:
                    cells.append("-")
            fr = f"{first[k][0] / first[k][1]:.0%}" if first[k][1] else "-"
            print(f"| {k[1]} | {k[2]} | {n} | " + " | ".join(cells) + f" | {fr} | {bad[k]['missing']}/{bad[k]['malformed']}/{bad[k]['invalid']} |")
        print()
    for kind in ("malformed", "invalid"):
        if bad_ids[kind]:
            print(f"{kind}: " + ", ".join(bad_ids[kind][:40]) + (" ..." if len(bad_ids[kind]) > 40 else ""))
    print(f"\n書き出し: {a.out}")


if __name__ == "__main__":
    main()
